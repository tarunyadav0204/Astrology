"""
Campaign engine: audience resolution, due-campaign dispatch (cron), Cloud Tasks
fan-out, and the per-batch worker that renders dynamic copy (template
placeholders or Gemini AI framing) and delivers via the channel orchestrator.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from zoneinfo import ZoneInfo

from db import execute
from credits.credit_service import CreditService

from . import db
from .delivery import deliver_nudge
from .param_resolver import CAMPAIGN_PLACEHOLDERS, default_params, resolve_params_for_users
from .template_render import extract_placeholders, render_template_lenient

logger = logging.getLogger(__name__)
IST_TZ = ZoneInfo("Asia/Kolkata")

ALLOWED_CHANNELS = ("push", "whatsapp", "email")
ALLOWED_POLICIES = ("waterfall", "blast")
ALLOWED_AUDIENCE_TYPES = (
    "all",
    "has_device_token",
    "no_device_token",
    "active_chat_days",
    "inactive_chat_days",
    "user_ids",
    "credit_intelligence_segment",
)

REACHABILITY_CHANNELS = ("push", "whatsapp", "email")

LANDING_SCREEN_TO_CTA: Dict[str, str] = {
    "chat": "astroroshni://chat",
    "information": "astroroshni://information",
    "event_screen": "astroroshni://event",
    "past_life_karma": "astroroshni://karma",
    "career": "astroroshni://analysis",
    "marriage": "astroroshni://analysis",
    "health": "astroroshni://analysis",
    "wealth": "astroroshni://analysis",
    "progeny": "astroroshni://analysis",
    "education": "astroroshni://analysis",
}


def campaign_trigger_id(campaign_id: int) -> str:
    return f"campaign_{int(campaign_id)}"


def _chunked(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _boolish(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    raw = str(value or "").strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _normalized_text_set(values: Any) -> Set[str]:
    out: Set[str] = set()
    if isinstance(values, (list, tuple, set)):
        items = values
    else:
        items = []
    for item in items:
        text = str(item or "").strip()
        if text:
            out.add(text.lower())
    return out


def _coerce_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _users_has_column(conn, column_name: str) -> bool:
    cur = execute(
        conn,
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = %s
        LIMIT 1
        """,
        (column_name,),
    )
    return bool(cur.fetchone())


def _whatsapp_presence_sql(conn) -> str:
    if _users_has_column(conn, "whatsapp_wa_id"):
        return "COALESCE(NULLIF(TRIM(whatsapp_wa_id), ''), '') <> ''"
    return "FALSE"


# ---------------------------------------------------------------------------
# Audience
# ---------------------------------------------------------------------------

def resolve_campaign_audience(conn, audience_filter: Dict[str, Any]) -> List[int]:
    """Return target user ids for a campaign audience filter."""
    ftype = str((audience_filter or {}).get("type") or "all").strip().lower()
    base_ids: List[int]
    if ftype == "user_ids":
        base_ids = [
            int(u)
            for u in (audience_filter.get("user_ids") or [])
            if isinstance(u, int) or str(u).isdigit()
        ]
    elif ftype == "credit_intelligence_segment":
        segment_key = str(audience_filter.get("segment_key") or "").strip().lower()
        from_date = str(audience_filter.get("from_date") or "").strip()
        to_date = str(audience_filter.get("to_date") or "").strip()
        if not segment_key or not from_date or not to_date:
            raise ValueError("credit intelligence segment audience requires segment_key, from_date, and to_date")
        base_ids = CreditService().get_admin_campaign_segment_user_ids(
            segment_key,
            from_date=from_date,
            to_date=to_date,
        )
    elif ftype == "has_device_token":
        cur = execute(conn, "SELECT DISTINCT userid FROM device_tokens ORDER BY userid")
        base_ids = [int(r[0]) for r in (cur.fetchall() or [])]
    elif ftype == "no_device_token":
        cur = execute(
            conn,
            """
            SELECT u.userid
            FROM users u
            LEFT JOIN (SELECT DISTINCT userid FROM device_tokens) dt ON dt.userid = u.userid
            WHERE dt.userid IS NULL
            ORDER BY u.userid
            """,
        )
        base_ids = [int(r[0]) for r in (cur.fetchall() or [])]
    elif ftype in ("active_chat_days", "inactive_chat_days"):
        days = max(1, min(int(audience_filter.get("days") or 7), 365))
        since = datetime.utcnow() - timedelta(days=days)
        if ftype == "active_chat_days":
            cur = execute(
                conn,
                """
                SELECT DISTINCT cs.user_id
                FROM chat_messages cm
                JOIN chat_sessions cs ON cs.session_id = cm.session_id
                WHERE cm.sender = 'user' AND cm.timestamp >= %s
                ORDER BY cs.user_id
                """,
                (since,),
            )
        else:
            cur = execute(
                conn,
                """
                SELECT u.userid
                FROM users u
                WHERE u.userid NOT IN (
                    SELECT DISTINCT cs.user_id
                    FROM chat_messages cm
                    JOIN chat_sessions cs ON cs.session_id = cm.session_id
                    WHERE cm.sender = 'user' AND cm.timestamp >= %s
                )
                ORDER BY u.userid
                """,
                (since,),
            )
        base_ids = [int(r[0]) for r in (cur.fetchall() or [])]
    else:
        base_ids = db.get_all_user_ids(conn)
    return filter_campaign_audience(conn, sorted(set(base_ids)), audience_filter or {})


def filter_campaign_audience(conn, user_ids: List[int], audience_filter: Dict[str, Any]) -> List[int]:
    """Apply flexible criteria on top of a base audience list."""
    clean_ids = sorted({int(uid) for uid in user_ids if str(uid).isdigit()})
    if not clean_ids:
        return []

    criteria = dict((audience_filter or {}).get("criteria") or {})
    for key in (
        "require_self_chart",
        "has_email",
        "has_whatsapp",
        "has_device_token",
        "free_question_available",
        "min_days_since_last_chat",
        "max_days_since_last_chat",
        "min_questions_asked",
        "max_questions_asked",
        "min_credits_balance",
        "max_credits_balance",
        "sun_signs",
        "moon_signs",
        "ascendant_signs",
        "mahadashas",
        "antardashas",
        "current_dasha_contains",
        "signup_clients",
    ):
        if key in audience_filter and key not in criteria:
            criteria[key] = audience_filter.get(key)

    keep: Set[int] = set(clean_ids)

    def _apply_sql_ids(sql: str, params: tuple[Any, ...]) -> Set[int]:
        cur = execute(conn, sql, params)
        return {int(r[0]) for r in (cur.fetchall() or [])}

    require_self_chart = _boolish(criteria.get("require_self_chart"))
    if require_self_chart is True:
        keep &= _apply_sql_ids(
            """
            SELECT DISTINCT userid
            FROM birth_charts
            WHERE userid = ANY(%s) AND LOWER(COALESCE(relation, '')) = 'self'
            """,
            (clean_ids,),
        )

    whatsapp_presence_sql = _whatsapp_presence_sql(conn)

    for flag_key, sql in (
        (
            "has_email",
            """
            SELECT userid
            FROM users
            WHERE userid = ANY(%s)
              AND COALESCE(NULLIF(TRIM(email), ''), '') <> ''
            """,
        ),
        (
            "has_whatsapp",
            f"""
            SELECT userid
            FROM users
            WHERE userid = ANY(%s)
              AND {whatsapp_presence_sql}
            """,
        ),
        (
            "has_device_token",
            """
            SELECT DISTINCT userid
            FROM device_tokens
            WHERE userid = ANY(%s)
            """,
        ),
    ):
        flag = _boolish(criteria.get(flag_key))
        if flag is None:
            continue
        matched = _apply_sql_ids(sql, (clean_ids,))
        keep &= matched if flag else (set(clean_ids) - matched)

    signup_clients = _normalized_text_set(criteria.get("signup_clients"))
    if signup_clients:
        cur = execute(
            conn,
            """
            SELECT userid
            FROM users
            WHERE userid = ANY(%s)
              AND LOWER(COALESCE(signup_client, '')) = ANY(%s)
            """,
            (clean_ids, list(signup_clients)),
        )
        keep &= {int(r[0]) for r in (cur.fetchall() or [])}

    needs_param_filters = any(
        criteria.get(key) not in (None, "", [], ())
        for key in (
            "min_days_since_last_chat",
            "max_days_since_last_chat",
            "min_questions_asked",
            "max_questions_asked",
            "min_credits_balance",
            "max_credits_balance",
            "free_question_available",
            "sun_signs",
            "moon_signs",
            "ascendant_signs",
            "mahadashas",
            "antardashas",
            "current_dasha_contains",
        )
    )
    if not needs_param_filters:
        return sorted(keep)

    needed_params: Set[str] = set()
    numeric_param_map = {
        "min_days_since_last_chat": "days_since_last_chat",
        "max_days_since_last_chat": "days_since_last_chat",
        "min_questions_asked": "questions_asked",
        "max_questions_asked": "questions_asked",
        "min_credits_balance": "credits_balance",
        "max_credits_balance": "credits_balance",
    }
    for key, placeholder in numeric_param_map.items():
        if criteria.get(key) not in (None, ""):
            needed_params.add(placeholder)
    if criteria.get("free_question_available") not in (None, ""):
        needed_params.add("free_question_available")
    sign_filters = {
        "sun_signs": "sun_sign",
        "moon_signs": "moon_sign",
        "ascendant_signs": "ascendant_sign",
        "mahadashas": "mahadasha",
        "antardashas": "antardasha",
        "current_dasha_contains": "current_dasha",
    }
    for key, placeholder in sign_filters.items():
        if criteria.get(key) not in (None, "", [], ()):
            needed_params.add(placeholder)

    params_by_user = resolve_params_for_users(conn, sorted(keep), needed=needed_params)
    filtered: List[int] = []
    sun_signs = _normalized_text_set(criteria.get("sun_signs"))
    moon_signs = _normalized_text_set(criteria.get("moon_signs"))
    ascendant_signs = _normalized_text_set(criteria.get("ascendant_signs"))
    mahadashas = _normalized_text_set(criteria.get("mahadashas"))
    antardashas = _normalized_text_set(criteria.get("antardashas"))
    dasha_contains = str(criteria.get("current_dasha_contains") or "").strip().lower()
    free_question_filter = _boolish(criteria.get("free_question_available"))
    min_days = _coerce_int(criteria.get("min_days_since_last_chat"))
    max_days = _coerce_int(criteria.get("max_days_since_last_chat"))
    min_questions = _coerce_int(criteria.get("min_questions_asked"))
    max_questions = _coerce_int(criteria.get("max_questions_asked"))
    min_credits = _coerce_int(criteria.get("min_credits_balance"))
    max_credits = _coerce_int(criteria.get("max_credits_balance"))

    for uid in sorted(keep):
        params = params_by_user.get(uid) or default_params()
        try:
            days = _coerce_int(params.get("days_since_last_chat"), 0) or 0
            questions = _coerce_int(params.get("questions_asked"), 0) or 0
            credits = _coerce_int(params.get("credits_balance"), 0) or 0
        except Exception:
            continue
        if min_days is not None and days < min_days:
            continue
        if max_days is not None and days > max_days:
            continue
        if min_questions is not None and questions < min_questions:
            continue
        if max_questions is not None and questions > max_questions:
            continue
        if min_credits is not None and credits < min_credits:
            continue
        if max_credits is not None and credits > max_credits:
            continue
        if free_question_filter is not None:
            is_free = str(params.get("free_question_available") or "").strip().lower() == "yes"
            if is_free != free_question_filter:
                continue
        if sun_signs and str(params.get("sun_sign") or "").strip().lower() not in sun_signs:
            continue
        if moon_signs and str(params.get("moon_sign") or "").strip().lower() not in moon_signs:
            continue
        if ascendant_signs and str(params.get("ascendant_sign") or "").strip().lower() not in ascendant_signs:
            continue
        if mahadashas and str(params.get("mahadasha") or "").strip().lower() not in mahadashas:
            continue
        if antardashas and str(params.get("antardasha") or "").strip().lower() not in antardashas:
            continue
        if dasha_contains and dasha_contains not in str(params.get("current_dasha") or "").strip().lower():
            continue
        filtered.append(uid)
    return filtered


def estimate_campaign_audience(conn, audience_filter: Dict[str, Any]) -> Dict[str, Any]:
    user_ids = resolve_campaign_audience(conn, audience_filter or {"type": "all"})
    if not user_ids:
        return {
            "total_users": 0,
            "reachable": {"push": 0, "whatsapp": 0, "email": 0},
            "has_self_chart": 0,
            "sample_user_ids": [],
        }
    ids = sorted(set(user_ids))
    reach = {"push": 0, "whatsapp": 0, "email": 0}
    whatsapp_presence_sql = _whatsapp_presence_sql(conn)
    queries = {
        "push": "SELECT COUNT(DISTINCT userid) FROM device_tokens WHERE userid = ANY(%s)",
        "whatsapp": f"SELECT COUNT(*) FROM users WHERE userid = ANY(%s) AND {whatsapp_presence_sql}",
        "email": "SELECT COUNT(*) FROM users WHERE userid = ANY(%s) AND COALESCE(NULLIF(TRIM(email), ''), '') <> ''",
    }
    for channel, sql in queries.items():
        cur = execute(conn, sql, (ids,))
        row = cur.fetchone()
        reach[channel] = int((row[0] if row else 0) or 0)
    cur = execute(
        conn,
        """
        SELECT COUNT(DISTINCT userid)
        FROM birth_charts
        WHERE userid = ANY(%s) AND LOWER(COALESCE(relation, '')) = 'self'
        """,
        (ids,),
    )
    row = cur.fetchone()
    return {
        "total_users": len(ids),
        "reachable": reach,
        "has_self_chart": int((row[0] if row else 0) or 0),
        "sample_user_ids": ids[:10],
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def needed_placeholders(campaign: Dict[str, Any]) -> Set[str]:
    """Placeholders used by the campaign templates (plus all when AI framing)."""
    if campaign.get("ai_personalize"):
        return set(CAMPAIGN_PLACEHOLDERS)
    used: Set[str] = set()
    for key in ("title_template", "body_template", "question_template"):
        used |= set(extract_placeholders(str(campaign.get(key) or "")))
    return used & set(CAMPAIGN_PLACEHOLDERS)


def render_campaign_for_user(
    campaign: Dict[str, Any], params: Dict[str, str]
) -> Dict[str, str]:
    """Render {title, body, question} for one user (templates, then optional AI)."""
    defaults = default_params()
    title = render_template_lenient(
        str(campaign.get("title_template") or ""), params, CAMPAIGN_PLACEHOLDERS, defaults
    ).strip()[:100]
    body = render_template_lenient(
        str(campaign.get("body_template") or ""), params, CAMPAIGN_PLACEHOLDERS, defaults
    ).strip()[:200]
    question = render_template_lenient(
        str(campaign.get("question_template") or ""), params, CAMPAIGN_PLACEHOLDERS, defaults
    ).strip()[:500]

    if campaign.get("ai_personalize"):
        try:
            from .campaign_ai_framer import frame_campaign_copy

            framed = frame_campaign_copy(
                base_prompt=str(campaign.get("ai_base_prompt") or ""),
                params=params,
                fallback_title=title,
                fallback_body=body,
                fallback_question=question,
            )
            return {
                "title": framed["title"][:100],
                "body": framed["body"][:200],
                "question": (framed.get("question") or question)[:500],
            }
        except Exception as e:
            logger.warning("AI framing failed (using template copy): %s", e)
    return {"title": title, "body": body, "question": question}


# ---------------------------------------------------------------------------
# Batch worker (Cloud Tasks endpoint / inline fallback)
# ---------------------------------------------------------------------------

def process_campaign_batch(*, campaign_id: int, user_ids: List[int]) -> Dict[str, Any]:
    """Render + deliver one campaign batch. Idempotent across Cloud Tasks retries."""
    clean_ids: List[int] = []
    seen: Set[int] = set()
    for uid in user_ids or []:
        try:
            v = int(uid)
        except (TypeError, ValueError):
            continue
        if v > 0 and v not in seen:
            clean_ids.append(v)
            seen.add(v)
    if not clean_ids:
        return {"ok": True, "campaign_id": int(campaign_id), "users": 0, "delivered": 0}

    summary: Dict[str, Any] = {
        "ok": True,
        "campaign_id": int(campaign_id),
        "users": len(clean_ids),
        "delivered": 0,
        "deduped": 0,
        "failed": 0,
        "channels": {"push": 0, "whatsapp": 0, "email": 0, "stored": 0},
    }
    with db.get_conn() as conn:
        db.init_nudge_tables(conn)
        campaign = db.get_campaign(conn, int(campaign_id))
        if not campaign:
            return {"ok": True, "skipped": "missing_campaign", "campaign_id": int(campaign_id)}
        if campaign.get("status") in ("draft", "cancelled"):
            return {"ok": True, "skipped": "inactive_campaign", "campaign_id": int(campaign_id)}

        already = db.get_campaign_delivery_user_ids(
            conn, campaign_id=int(campaign_id), userids=clean_ids
        )
        targets = [uid for uid in clean_ids if uid not in already]
        summary["deduped"] = len(already)
        if not targets:
            return summary

        params_by_user = resolve_params_for_users(
            conn, targets, needed=needed_placeholders(campaign)
        )
        channels = [c for c in (campaign.get("channels") or []) if c in ALLOWED_CHANNELS] or list(
            ALLOWED_CHANNELS
        )
        policy = campaign.get("channel_policy") or "waterfall"
        landing = str(campaign.get("landing_screen") or "chat")
        cta = LANDING_SCREEN_TO_CTA.get(landing, "astroroshni://chat")
        event_params = json.dumps({"campaign_id": int(campaign_id)}, ensure_ascii=False)
        data_extra: Dict[str, Any] = {"landing_screen": landing, "campaign_id": str(int(campaign_id))}
        if landing in {"career", "marriage", "health", "wealth", "progeny", "education"}:
            data_extra["analysis_type"] = landing

        for uid in targets:
            try:
                copy = render_campaign_for_user(campaign, params_by_user.get(uid) or default_params())
                if not copy["title"] or not copy["body"]:
                    summary["failed"] += 1
                    continue
                result = deliver_nudge(
                    conn,
                    userid=uid,
                    trigger_id=campaign_trigger_id(int(campaign_id)),
                    title=copy["title"],
                    body=copy["body"],
                    question=copy.get("question") or None,
                    policy=policy,
                    channels=channels,
                    campaign_id=int(campaign_id),
                    event_params=event_params,
                    data_extra=data_extra,
                    cta_deep_link=cta,
                )
                summary["delivered"] += 1
                ch = result.get("channel") or "stored"
                if ch in summary["channels"]:
                    summary["channels"][ch] += 1
                for extra in (result.get("channels_sent") or [])[1:]:
                    if extra in summary["channels"]:
                        summary["channels"][extra] += 1
            except Exception as e:
                summary["failed"] += 1
                logger.warning(
                    "campaign %s delivery failed for user %s: %s", campaign_id, uid, e
                )
        conn.commit()
    return summary


# ---------------------------------------------------------------------------
# Dispatch (cron + admin send-now)
# ---------------------------------------------------------------------------

def _dispatch_one_campaign(conn, campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Fan out one due campaign: resolve audience, enqueue batches (or run inline)."""
    campaign_id = int(campaign["id"])
    previous_status = str(campaign.get("status") or "draft").strip().lower() or "draft"
    previous_scheduled_at = campaign.get("scheduled_at")
    audience = resolve_campaign_audience(conn, campaign.get("audience_filter") or {})
    db.update_campaign(
        conn,
        campaign_id,
        status="sending",
        total_targeted=len(audience),
    )
    conn.commit()

    try:
        from .task_queue import (
            enqueue_nudge_task,
            nudge_tasks_are_isolated,
            nudge_tasks_enabled,
            nudge_tasks_target_base_url,
        )

        tasks_enabled = nudge_tasks_enabled()
        tasks_isolated = nudge_tasks_are_isolated()
        tasks_target = nudge_tasks_target_base_url()
    except Exception as e:
        logger.warning("nudge task queue unavailable; campaign runs inline: %s", e)
        enqueue_nudge_task = None
        tasks_enabled = False
        tasks_isolated = False
        tasks_target = ""

    require_tasks = (os.getenv("NUDGE_CAMPAIGN_REQUIRE_TASKS") or "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    require_isolated = (os.getenv("NUDGE_CAMPAIGN_REQUIRE_ISOLATED_WORKERS") or "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    inline_max_users = max(1, min(int(os.getenv("NUDGE_CAMPAIGN_INLINE_MAX_USERS", "100")), 1000))
    if not tasks_enabled and (require_tasks or len(audience) > inline_max_users or campaign.get("ai_personalize")):
        raise RuntimeError(
            "Campaign dispatch requires Cloud Tasks configuration for this audience size/personalization mode."
        )
    if tasks_enabled and require_isolated and not tasks_isolated:
        raise RuntimeError(
            "Campaign dispatch is blocked because NUDGE_TASKS_TARGET_BASE_URL still points at the public API host. "
            f"Configure an isolated worker target before sending campaigns. Current target: {tasks_target or '<unset>'}"
        )

    try:
        batch_size = max(1, min(int(os.getenv("NUDGE_CAMPAIGN_BATCH_SIZE", "50")), 500))
        batches = _chunked(audience, batch_size)

        enqueued = 0
        enqueue_failed = 0
        inline_summaries: List[Dict[str, Any]] = []
        if tasks_enabled and enqueue_nudge_task:
            for batch_index, chunk in enumerate(batches):
                ok = enqueue_nudge_task(
                    task_kind="campaign-batch",
                    task_id=f"{campaign_id}-{batch_index}",
                    payload={
                        "campaign_id": campaign_id,
                        "batch_index": batch_index,
                        "user_ids": [int(u) for u in chunk],
                    },
                )
                if ok:
                    enqueued += 1
                else:
                    enqueue_failed += 1
            if batches and enqueued == 0:
                raise RuntimeError("Campaign dispatch could not enqueue any worker tasks.")
        else:
            for chunk in batches:
                inline_summaries.append(
                    process_campaign_batch(campaign_id=campaign_id, user_ids=chunk)
                )

        db.update_campaign(
            conn,
            campaign_id,
            status="sent",
            dispatched_at=datetime.now(IST_TZ),
            total_targeted=len(audience),
        )
        conn.commit()

        out: Dict[str, Any] = {
            "campaign_id": campaign_id,
            "users_targeted": len(audience),
            "batches": len(batches),
            "queued": bool(tasks_enabled and enqueue_nudge_task),
            "tasks_enqueued": enqueued,
            "enqueue_failed": enqueue_failed,
        }
        if inline_summaries:
            out["delivered"] = sum(int(s.get("delivered") or 0) for s in inline_summaries)
            out["failed"] = sum(int(s.get("failed") or 0) for s in inline_summaries)
        return out
    except Exception:
        rollback_status = "scheduled" if previous_status == "scheduled" and previous_scheduled_at else "draft"
        try:
            db.update_campaign(
                conn,
                campaign_id,
                status=rollback_status,
                dispatched_at=None,
                total_targeted=len(audience),
            )
            conn.commit()
        except Exception:
            logger.exception("failed to roll back campaign status after dispatch error id=%s", campaign_id)
            try:
                conn.rollback()
            except Exception:
                pass
        raise


def dispatch_due_campaigns(limit: int = 20) -> Dict[str, Any]:
    """Cron entry point: dispatch all campaigns whose scheduled_at has passed."""
    now = datetime.now(IST_TZ)
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            if not db.try_advisory_xact_lock(conn, "nudge_campaign_dispatch_due"):
                summary = {"ok": True, "skipped": "already_running", "due_campaigns": 0}
                db.insert_cron_run(
                    conn,
                    job_key="campaign_dispatch_due",
                    status="skipped",
                    summary_json=json.dumps(summary, ensure_ascii=False),
                )
                conn.commit()
                return summary
            due = db.acquire_due_campaigns(conn, now, limit=limit)
            if not due:
                summary = {"ok": True, "due_campaigns": 0, "message": "No due campaigns."}
                db.insert_cron_run(
                    conn,
                    job_key="campaign_dispatch_due",
                    status="success",
                    summary_json=json.dumps(summary, ensure_ascii=False),
                )
                conn.commit()
                return summary

            results = []
            for campaign in due:
                try:
                    results.append(_dispatch_one_campaign(conn, campaign))
                except Exception as e:
                    logger.exception("campaign %s dispatch failed: %s", campaign.get("id"), e)
                    results.append({"campaign_id": campaign.get("id"), "error": str(e)[:500]})
            summary = {"ok": True, "due_campaigns": len(due), "results": results}
            db.insert_cron_run(
                conn,
                job_key="campaign_dispatch_due",
                status="success",
                summary_json=json.dumps(summary, ensure_ascii=False)[:8000],
            )
            conn.commit()
            return summary
    except Exception as e:
        logger.exception("dispatch_due_campaigns failed: %s", e)
        return {"ok": False, "error": str(e)[:500]}


def dispatch_campaign_now(campaign_id: int) -> Dict[str, Any]:
    """Admin 'send now': dispatch a specific draft/scheduled campaign immediately."""
    with db.get_conn() as conn:
        db.init_nudge_tables(conn)
        campaign = db.get_campaign(conn, int(campaign_id))
        if not campaign:
            return {"ok": False, "error": "campaign_not_found"}
        if campaign.get("status") not in ("draft", "scheduled"):
            return {"ok": False, "error": f"campaign status is '{campaign.get('status')}'"}
        result = _dispatch_one_campaign(conn, campaign)
        return {"ok": True, **result}


def send_campaign_test(conn, campaign: Dict[str, Any], target_userid: int) -> Dict[str, Any]:
    """Deliver a single rendered copy of the campaign to one user (admin test send)."""
    params = resolve_params_for_users(
        conn, [int(target_userid)], needed=needed_placeholders(campaign)
    ).get(int(target_userid)) or default_params()
    copy = render_campaign_for_user(campaign, params)
    landing = str(campaign.get("landing_screen") or "chat")
    channels = [c for c in (campaign.get("channels") or []) if c in ALLOWED_CHANNELS] or list(
        ALLOWED_CHANNELS
    )
    result = deliver_nudge(
        conn,
        userid=int(target_userid),
        trigger_id="campaign_test",
        title=copy["title"],
        body=copy["body"],
        question=copy.get("question") or None,
        policy=campaign.get("channel_policy") or "waterfall",
        channels=channels,
        event_params=json.dumps(
            {"campaign_id": campaign.get("id"), "test": True}, ensure_ascii=False
        ),
        data_extra={"landing_screen": landing},
        cta_deep_link=LANDING_SCREEN_TO_CTA.get(landing, "astroroshni://chat"),
    )
    return {"copy": copy, "delivery": result}
