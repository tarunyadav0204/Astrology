"""
Campaign engine: audience resolution, due-campaign dispatch (cron), Cloud Tasks
fan-out, and the per-batch worker that renders dynamic copy (template
placeholders or Gemini AI framing) and delivers via the channel orchestrator.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

from db import execute
from credits.credit_service import CreditService

from . import db
from .delivery import deliver_nudge
from .param_resolver import CAMPAIGN_PLACEHOLDERS, default_params, resolve_params_for_users
from .push import send_expo_push_messages
from .template_render import extract_placeholders, render_template_lenient

logger = logging.getLogger(__name__)
IST_TZ = ZoneInfo("Asia/Kolkata")

ALLOWED_CHANNELS = ("push", "whatsapp", "email")
ALLOWED_POLICIES = ("waterfall", "blast", "push_only")
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
    "blog": "astroroshni://blog",
}


def campaign_trigger_id(campaign_id: int) -> str:
    return f"campaign_{int(campaign_id)}"


def _blog_push_data(campaign: Dict[str, Any]) -> Dict[str, str]:
    blog_url = str(campaign.get("landing_url") or "").strip()
    data = {"blog_url": blog_url}
    try:
        parsed = urlparse(blog_url)
        hostname = str(parsed.hostname or "").lower()
        if hostname.startswith("www."):
            hostname = hostname[4:]
        path_parts = [part for part in parsed.path.split("/") if part]
        if hostname == "astroroshni.com" and len(path_parts) == 2 and path_parts[0].lower() == "blog":
            slug = unquote(path_parts[1]).strip()
            if slug:
                data["slug"] = slug
    except (TypeError, ValueError):
        pass
    return data


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
            conn=conn,
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


def estimate_campaign_audience(
    conn, audience_filter: Dict[str, Any], *, notification_conn=None
) -> Dict[str, Any]:
    raw_filter = audience_filter or {"type": "all"}
    replica_filter = json.loads(json.dumps(raw_filter))
    token_filter = _boolish(replica_filter.pop("has_device_token", None))
    criteria = dict(replica_filter.get("criteria") or {})
    if "has_device_token" in criteria:
        token_filter = _boolish(criteria.pop("has_device_token"))
        replica_filter["criteria"] = criteria
    ftype = str(replica_filter.get("type") or "all").strip().lower()
    if ftype in {"has_device_token", "no_device_token"}:
        token_filter = ftype == "has_device_token"
        replica_filter["type"] = "all"
    user_ids = resolve_campaign_audience(conn, replica_filter)
    token_conn = notification_conn or conn
    if token_filter is not None:
        reachable_ids = set(filter_push_reachable_user_ids(token_conn, user_ids))
        user_ids = [uid for uid in user_ids if (uid in reachable_ids) == bool(token_filter)]
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
        cur = execute(token_conn if channel == "push" else conn, sql, (ids,))
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


def filter_push_reachable_user_ids(conn, user_ids: List[int]) -> List[int]:
    """Keep campaign targets that currently have at least one push device token."""
    clean_ids = sorted({int(uid) for uid in user_ids or [] if int(uid) > 0})
    if not clean_ids:
        return []
    cur = execute(
        conn,
        "SELECT DISTINCT userid FROM device_tokens WHERE userid = ANY(%s)",
        (clean_ids,),
    )
    reachable = {int(row[0]) for row in (cur.fetchall() or []) if row and row[0] is not None}
    return [uid for uid in user_ids if int(uid) in reachable]


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


def _resolve_delivery_endpoints(conn, user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Resolve user identity/provider addresses from the application replica."""
    ids = sorted({int(uid) for uid in user_ids if str(uid).isdigit() and int(uid) > 0})
    out: Dict[int, Dict[str, Any]] = {uid: {"push": []} for uid in ids}
    if not ids:
        return out
    whatsapp_column = _users_has_column(conn, "whatsapp_wa_id")
    if whatsapp_column:
        cur = execute(
            conn,
            """
            SELECT u.userid, COALESCE(u.email, ''), COALESCE(u.phone, ''),
                   COALESCE(NULLIF(TRIM(u.name), ''), 'there'),
                   COALESCE(u.whatsapp_wa_id, ''),
                   COALESCE(ws.last_phone_number_id, '')
            FROM users u
            LEFT JOIN LATERAL (
                SELECT last_phone_number_id
                FROM whatsapp_sessions
                WHERE wa_id = u.whatsapp_wa_id
                ORDER BY updated_at DESC NULLS LAST
                LIMIT 1
            ) ws ON TRUE
            WHERE u.userid = ANY(%s)
            """,
            (ids,),
        )
    else:
        cur = execute(
            conn,
            """
            SELECT userid, COALESCE(email, ''), COALESCE(phone, ''),
                   COALESCE(NULLIF(TRIM(name), ''), 'there'), '' AS wa_id,
                   '' AS phone_number_id
            FROM users
            WHERE userid = ANY(%s)
            """,
            (ids,),
        )
    for uid, email, phone, name, wa_id, phone_number_id in cur.fetchall() or []:
        endpoint = out.setdefault(int(uid), {"push": []})
        endpoint.update(
            {
                "email": str(email or "").strip(),
                "phone": str(phone or "").strip(),
                "name": str(name or "there").strip() or "there",
                "whatsapp_wa_id": str(wa_id or "").strip(),
                "whatsapp_phone_number_id": str(phone_number_id or "").strip(),
            }
        )
    return out


def _resolve_push_endpoints(conn, user_ids: List[int]) -> Dict[int, List[Dict[str, str]]]:
    """Resolve push endpoints from notification-owned token storage."""
    ids = sorted({int(uid) for uid in user_ids if str(uid).isdigit() and int(uid) > 0})
    out: Dict[int, List[Dict[str, str]]] = {uid: [] for uid in ids}
    if not ids:
        return out
    cur = execute(
        conn,
        "SELECT userid, token, platform FROM device_tokens WHERE userid = ANY(%s)",
        (ids,),
    )
    for uid, token, platform in cur.fetchall() or []:
        token_s = str(token or "").strip()
        if token_s:
            out.setdefault(int(uid), []).append(
                {"token": token_s, "platform": str(platform or "")[:20]}
            )
    return out


def _snapshot_campaign_batch(
    *, campaign: Dict[str, Any], campaign_id: int, user_ids: List[int]
) -> None:
    """Read app context from the replica, then store provider-ready work."""
    with db.get_read_conn() as read_conn:
        params_by_user = resolve_params_for_users(
            read_conn, user_ids, needed=needed_placeholders(campaign)
        )
        endpoints_by_user = _resolve_delivery_endpoints(read_conn, user_ids)
    with db.get_conn() as notification_conn:
        push_by_user = _resolve_push_endpoints(notification_conn, user_ids)
    for uid in user_ids:
        endpoints_by_user.setdefault(uid, {})["push"] = push_by_user.get(uid) or []

    channels = [c for c in (campaign.get("channels") or []) if c in ALLOWED_CHANNELS] or list(
        ALLOWED_CHANNELS
    )
    policy = str(campaign.get("channel_policy") or "waterfall")
    landing = str(campaign.get("landing_screen") or "chat")
    cta = LANDING_SCREEN_TO_CTA.get(landing, "astroroshni://chat")
    data_extra: Dict[str, Any] = {
        "landing_screen": landing,
        "campaign_id": str(int(campaign_id)),
        "cta": cta,
        "trigger_id": campaign_trigger_id(int(campaign_id)),
    }
    if landing in {"career", "marriage", "health", "wealth", "progeny", "education"}:
        data_extra["analysis_type"] = landing
    if landing == "blog":
        data_extra.update(_blog_push_data(campaign))

    snapshots: List[Dict[str, Any]] = []
    for uid in user_ids:
        copy = render_campaign_for_user(campaign, params_by_user.get(uid) or default_params())
        if not copy.get("title") or not copy.get("body"):
            continue
        group_id = uuid.uuid4().hex
        data = {**data_extra, "nudge_id": group_id}
        if copy.get("question"):
            data["question"] = copy["question"][:500]
        snapshots.append(
            {
                "campaign_id": campaign_id,
                "userid": uid,
                "delivery_group_id": group_id,
                "title": copy["title"],
                "body": copy["body"],
                "question": copy.get("question"),
                "policy": policy,
                "channels": channels,
                "endpoints": endpoints_by_user.get(uid) or {"push": []},
                "data": data,
            }
        )
    with db.get_conn() as notification_conn:
        db.upsert_campaign_recipient_snapshots(notification_conn, snapshots)
        notification_conn.commit()


def _deliver_recipient_snapshots(recipients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Call providers without holding any database connection."""
    results: Dict[int, Dict[str, Any]] = {
        int(r["id"]): {"recipient": r, "attempts": [], "sent": []} for r in recipients
    }

    # Push is the high-volume channel: send all tokens in Expo batches of 100.
    messages: List[Dict[str, Any]] = []
    message_owners: List[int] = []
    push_requested: Set[int] = set()
    for recipient in recipients:
        rid = int(recipient["id"])
        channels = recipient.get("channels") or []
        if "push" not in channels:
            continue
        push_requested.add(rid)
        for token_row in (recipient.get("endpoints") or {}).get("push") or []:
            token = str((token_row or {}).get("token") or "").strip()
            if not token.startswith("ExponentPushToken["):
                continue
            messages.append(
                {
                    "to": token,
                    "title": recipient.get("title") or "",
                    "body": recipient.get("body") or "",
                    "sound": "default",
                    "data": recipient.get("data") or {},
                }
            )
            message_owners.append(rid)
    push_success: Set[int] = set()
    if messages:
        for rid, ok in zip(message_owners, send_expo_push_messages(messages)):
            if ok:
                push_success.add(rid)
    for rid in push_requested:
        ok = rid in push_success
        results[rid]["attempts"].append(("push", ok))
        if ok:
            results[rid]["sent"].append("push")

    from .email_channel import send_nudge_email_to_address
    from .whatsapp_fallback import (
        send_whatsapp_nudge_to_target,
        send_whatsapp_template_to_phone,
    )

    for recipient in recipients:
        rid = int(recipient["id"])
        result = results[rid]
        policy = str(recipient.get("policy") or "waterfall").lower()
        endpoints = recipient.get("endpoints") or {}
        requested = [c for c in (recipient.get("channels") or []) if c in ALLOWED_CHANNELS]
        if policy == "push_only":
            requested = ["push"]
        for channel in requested:
            if channel == "push":
                continue
            if result["sent"] and policy != "blast":
                break
            ok = False
            actual = channel
            if channel == "whatsapp":
                wa_id = str(endpoints.get("whatsapp_wa_id") or "")
                phone_number_id = str(endpoints.get("whatsapp_phone_number_id") or "")
                if wa_id and phone_number_id:
                    ok = send_whatsapp_nudge_to_target(
                        wa_id=wa_id,
                        phone_number_id=phone_number_id,
                        title=recipient.get("title") or "",
                        body=recipient.get("body") or "",
                        question=recipient.get("question"),
                    )
                elif endpoints.get("phone"):
                    actual = "whatsapp_template"
                    ok = send_whatsapp_template_to_phone(
                        phone=str(endpoints.get("phone") or ""),
                        name=str(endpoints.get("name") or "there"),
                    )
            elif channel == "email" and endpoints.get("email"):
                ok = send_nudge_email_to_address(
                    str(endpoints.get("email")),
                    title=recipient.get("title") or "",
                    body=recipient.get("body") or "",
                    question=recipient.get("question"),
                    delivery_group_id=str(recipient.get("delivery_group_id") or ""),
                )
            result["attempts"].append((actual, bool(ok)))
            if ok:
                result["sent"].append(actual)
    return list(results.values())


# ---------------------------------------------------------------------------
# Batch worker (Cloud Tasks endpoint / inline fallback)
# ---------------------------------------------------------------------------

def process_campaign_batch(*, campaign_id: int, user_ids: List[int]) -> Dict[str, Any]:
    """Snapshot, claim and deliver a batch without DB connections during I/O."""
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
    # Phase 1: short notification DB read, followed by a read-replica snapshot.
    with db.get_conn() as conn:
        db.init_nudge_tables(conn)
        campaign = db.get_campaign(conn, int(campaign_id))
    if not campaign:
        return {"ok": True, "skipped": "missing_campaign", "campaign_id": int(campaign_id)}
    if campaign.get("status") in ("draft", "cancelled"):
        return {"ok": True, "skipped": "inactive_campaign", "campaign_id": int(campaign_id)}

    _snapshot_campaign_batch(
        campaign=campaign,
        campaign_id=int(campaign_id),
        user_ids=clean_ids,
    )
    max_attempts = max(1, min(int(os.getenv("NUDGE_PROVIDER_MAX_ATTEMPTS", "5") or "5"), 20))
    with db.get_conn() as conn:
        recipients = db.claim_campaign_recipients(
            conn,
            campaign_id=int(campaign_id),
            userids=clean_ids,
            max_attempts=max_attempts,
        )
        conn.commit()
    summary["deduped"] = len(clean_ids) - len(recipients)
    if not recipients:
        return summary

    # Phase 2: all provider calls happen with zero database connections held.
    provider_results = _deliver_recipient_snapshots(recipients)

    # Phase 3: persist outcomes in one short notification DB transaction.
    should_retry = False
    with db.get_conn() as conn:
        for result in provider_results:
            recipient = result["recipient"]
            attempts = list(result.get("attempts") or [])
            sent_channels = list(result.get("sent") or [])
            endpoints = recipient.get("endpoints") or {}
            policy = str(recipient.get("policy") or "waterfall").lower()
            requested = [
                c for c in (recipient.get("channels") or []) if c in ALLOWED_CHANNELS
            ]
            if policy == "push_only":
                requested = ["push"]
            had_reachable_endpoint = any(
                (
                    channel == "push"
                    and bool(endpoints.get("push") or [])
                )
                or (
                    channel == "whatsapp"
                    and bool(
                        (
                            endpoints.get("whatsapp_wa_id")
                            and endpoints.get("whatsapp_phone_number_id")
                        )
                        or endpoints.get("phone")
                    )
                )
                or (channel == "email" and bool(endpoints.get("email")))
                for channel in requested
            )
            if (
                not sent_channels
                and had_reachable_endpoint
                and int(recipient.get("attempt_count") or 0) < max_attempts
            ):
                error = "All reachable notification providers failed; retry scheduled"
                db.complete_campaign_recipient(
                    conn, recipient_id=int(recipient["id"]), state="retry", error=error
                )
                summary["failed"] += 1
                should_retry = True
                continue
            primary_assigned = False
            for channel, ok in attempts:
                is_primary = bool(ok and not primary_assigned)
                if is_primary:
                    primary_assigned = True
                db.insert_delivery(
                    conn,
                    userid=int(recipient["userid"]),
                    trigger_id=campaign_trigger_id(int(campaign_id)),
                    title=str(recipient.get("title") or ""),
                    body=str(recipient.get("body") or ""),
                    sent_at=datetime.now(IST_TZ).date(),
                    event_params=json.dumps({"campaign_id": int(campaign_id)}, ensure_ascii=False),
                    channel=str(channel),
                    data_payload=recipient.get("data") or {},
                    campaign_id=int(campaign_id),
                    delivery_group_id=str(recipient.get("delivery_group_id") or ""),
                    send_status="sent" if ok else "failed",
                    is_primary=is_primary,
                )
            if not primary_assigned:
                db.insert_delivery(
                    conn,
                    userid=int(recipient["userid"]),
                    trigger_id=campaign_trigger_id(int(campaign_id)),
                    title=str(recipient.get("title") or ""),
                    body=str(recipient.get("body") or ""),
                    sent_at=datetime.now(IST_TZ).date(),
                    event_params=json.dumps({"campaign_id": int(campaign_id)}, ensure_ascii=False),
                    channel="stored",
                    data_payload=recipient.get("data") or {},
                    campaign_id=int(campaign_id),
                    delivery_group_id=str(recipient.get("delivery_group_id") or ""),
                    send_status="stored",
                    is_primary=True,
                )
            if sent_channels or not had_reachable_endpoint:
                db.complete_campaign_recipient(conn, recipient_id=int(recipient["id"]), state="completed")
                summary["delivered"] += 1
                primary = sent_channels[0] if sent_channels else "stored"
                if primary in summary["channels"]:
                    summary["channels"][primary] += 1
            elif int(recipient.get("attempt_count") or 0) >= max_attempts:
                error = "All reachable notification providers rejected the delivery"
                db.complete_campaign_recipient(
                    conn, recipient_id=int(recipient["id"]), state="dead", error=error
                )
                db.insert_dead_letter(conn, recipient=recipient, channel=None, error=error)
                summary["failed"] += 1
        summary["progress"] = db.refresh_campaign_delivery_status(conn, int(campaign_id))
        conn.commit()
    if should_retry:
        # Cloud Tasks applies exponential backoff.  Returning an error is
        # intentional; recipient claims make each retry idempotent.
        raise RuntimeError("One or more campaign recipients require provider retry")
    return summary


# ---------------------------------------------------------------------------
# Dispatch (cron + admin send-now)
# ---------------------------------------------------------------------------

def _dispatch_one_campaign(conn, campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Fan out one due campaign: resolve audience, enqueue batches (or run inline)."""
    campaign_id = int(campaign["id"])
    previous_status = str(campaign.get("status") or "draft").strip().lower() or "draft"
    previous_scheduled_at = campaign.get("scheduled_at")
    audience_filter = campaign.get("audience_filter") or {}
    selected_user_ids = (
        sorted(
            {
                int(uid)
                for uid in (audience_filter.get("user_ids") or [])
                if isinstance(uid, int) or str(uid).isdigit()
            }
        )
        if str(audience_filter.get("type") or "").strip().lower() == "user_ids"
        else []
    )
    # Audience/history/personalization reads are isolated on the application
    # replica.  The notification database is used only for campaign state.
    replica_filter = json.loads(json.dumps(audience_filter))
    token_filter = _boolish(replica_filter.pop("has_device_token", None))
    criteria = dict(replica_filter.get("criteria") or {})
    if "has_device_token" in criteria:
        token_filter = _boolish(criteria.pop("has_device_token"))
        replica_filter["criteria"] = criteria
    audience_type = str(replica_filter.get("type") or "all").strip().lower()
    if audience_type in {"has_device_token", "no_device_token"}:
        token_filter = audience_type == "has_device_token"
        replica_filter["type"] = "all"
    if selected_user_ids:
        audience = list(selected_user_ids)
    else:
        with db.get_read_conn() as audience_conn:
            audience = resolve_campaign_audience(audience_conn, replica_filter)
    if token_filter is not None or str(campaign.get("channel_policy") or "").strip().lower() == "push_only":
        reachable = set(filter_push_reachable_user_ids(conn, audience))
        require_push = (
            True
            if str(campaign.get("channel_policy") or "").strip().lower() == "push_only"
            else bool(token_filter)
        )
        audience = [uid for uid in audience if (uid in reachable) == require_push]
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

        if not audience:
            db.update_campaign(
                conn,
                campaign_id,
                status="sent",
                dispatched_at=datetime.now(IST_TZ),
                total_targeted=0,
            )
        conn.commit()
        current_campaign = db.get_campaign(conn, campaign_id) or {}

        out: Dict[str, Any] = {
            "campaign_id": campaign_id,
            "users_selected": len(selected_user_ids) if selected_user_ids else None,
            "users_targeted": len(audience),
            "batches": len(batches),
            "queued": bool(tasks_enabled and enqueue_nudge_task),
            "tasks_enqueued": enqueued,
            "enqueue_failed": enqueue_failed,
            "status": current_campaign.get("status") or ("sending" if audience else "sent"),
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


def send_campaign_test(campaign: Dict[str, Any], target_userid: int) -> Dict[str, Any]:
    """Deliver one test using the same replica/snapshot/provider boundary as a campaign."""
    uid = int(target_userid)
    with db.get_read_conn() as read_conn:
        params = resolve_params_for_users(
            read_conn, [uid], needed=needed_placeholders(campaign)
        ).get(uid) or default_params()
        endpoints = _resolve_delivery_endpoints(read_conn, [uid]).get(uid) or {}
    with db.get_conn() as notification_conn:
        endpoints["push"] = _resolve_push_endpoints(notification_conn, [uid]).get(uid) or []

    copy = render_campaign_for_user(campaign, params)
    landing = str(campaign.get("landing_screen") or "chat")
    group_id = uuid.uuid4().hex
    channels = [c for c in (campaign.get("channels") or []) if c in ALLOWED_CHANNELS] or list(
        ALLOWED_CHANNELS
    )
    data: Dict[str, Any] = {
        "landing_screen": landing,
        "cta": LANDING_SCREEN_TO_CTA.get(landing, "astroroshni://chat"),
        "trigger_id": "campaign_test",
        "nudge_id": group_id,
    }
    if landing == "blog":
        data.update(_blog_push_data(campaign))
    if copy.get("question"):
        data["question"] = copy["question"][:500]
    recipient = {
        "id": 0,
        "userid": uid,
        "delivery_group_id": group_id,
        "title": copy["title"],
        "body": copy["body"],
        "question": copy.get("question"),
        "policy": campaign.get("channel_policy") or "waterfall",
        "channels": channels,
        "endpoints": endpoints,
        "data": data,
    }
    delivered = _deliver_recipient_snapshots([recipient])[0]

    with db.get_conn() as notification_conn:
        sent_channels = list(delivered.get("sent") or [])
        primary_assigned = False
        for channel, ok in delivered.get("attempts") or []:
            is_primary = bool(ok and not primary_assigned)
            primary_assigned = primary_assigned or is_primary
            db.insert_delivery(
                notification_conn,
                userid=uid,
                trigger_id="campaign_test",
                title=copy["title"],
                body=copy["body"],
                sent_at=datetime.now(IST_TZ).date(),
                event_params=json.dumps(
                    {"campaign_id": campaign.get("id"), "test": True}, ensure_ascii=False
                ),
                channel=str(channel),
                data_payload=data,
                campaign_id=None,
                delivery_group_id=group_id,
                send_status="sent" if ok else "failed",
                is_primary=is_primary,
            )
        if not primary_assigned:
            db.insert_delivery(
                notification_conn,
                userid=uid,
                trigger_id="campaign_test",
                title=copy["title"],
                body=copy["body"],
                sent_at=datetime.now(IST_TZ).date(),
                event_params=json.dumps(
                    {"campaign_id": campaign.get("id"), "test": True}, ensure_ascii=False
                ),
                channel="stored",
                data_payload=data,
                campaign_id=None,
                delivery_group_id=group_id,
                send_status="stored",
                is_primary=True,
            )
        notification_conn.commit()
    return {
        "copy": copy,
        "delivery": {
            "delivery_group_id": group_id,
            "channel": sent_channels[0] if sent_channels else "stored",
            "channels_sent": sent_channels,
            "channels_failed": [c for c, ok in delivered.get("attempts") or [] if not ok],
        },
    }
