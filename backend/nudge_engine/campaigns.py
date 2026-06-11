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
)

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


# ---------------------------------------------------------------------------
# Audience
# ---------------------------------------------------------------------------

def resolve_campaign_audience(conn, audience_filter: Dict[str, Any]) -> List[int]:
    """Return target user ids for a campaign audience filter."""
    ftype = str((audience_filter or {}).get("type") or "all").strip().lower()
    if ftype == "user_ids":
        ids = [
            int(u)
            for u in (audience_filter.get("user_ids") or [])
            if isinstance(u, int) or str(u).isdigit()
        ]
        return sorted(set(ids))
    if ftype == "has_device_token":
        cur = execute(conn, "SELECT DISTINCT userid FROM device_tokens ORDER BY userid")
        return [int(r[0]) for r in (cur.fetchall() or [])]
    if ftype == "no_device_token":
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
        return [int(r[0]) for r in (cur.fetchall() or [])]
    if ftype in ("active_chat_days", "inactive_chat_days"):
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
        return [int(r[0]) for r in (cur.fetchall() or [])]
    # default: all users
    return db.get_all_user_ids(conn)


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
    audience = resolve_campaign_audience(conn, campaign.get("audience_filter") or {})
    db.update_campaign(
        conn,
        campaign_id,
        status="sending",
        total_targeted=len(audience),
    )
    conn.commit()

    try:
        from .task_queue import enqueue_nudge_task, nudge_tasks_enabled

        tasks_enabled = nudge_tasks_enabled()
    except Exception as e:
        logger.warning("nudge task queue unavailable; campaign runs inline: %s", e)
        enqueue_nudge_task = None
        tasks_enabled = False

    batch_size = max(1, min(int(os.getenv("NUDGE_CAMPAIGN_BATCH_SIZE", "250")), 2000))
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
