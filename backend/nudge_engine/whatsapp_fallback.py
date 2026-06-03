"""WhatsApp fallback delivery for nudges when app push is unavailable."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from db import execute

logger = logging.getLogger(__name__)

WHATSAPP_NUDGE_CONTINUE_BUTTON_ID = "wa_nudge_continue"


def get_whatsapp_target_for_user(conn, userid: int) -> Optional[Tuple[str, str]]:
    """Return (wa_id, phone_number_id) when the user has a linked WhatsApp session."""
    try:
        cur = execute(
            conn,
            """
            SELECT u.whatsapp_wa_id, ws.last_phone_number_id
            FROM users u
            LEFT JOIN whatsapp_sessions ws ON ws.wa_id = u.whatsapp_wa_id
            WHERE u.userid = %s
            """,
            (int(userid),),
        )
        row = cur.fetchone()
    except Exception as e:
        logger.warning("WhatsApp nudge fallback lookup failed user=%s: %s", userid, e)
        return None
    if not row or not row[0] or not row[1]:
        return None
    return str(row[0]).strip(), str(row[1]).strip()


def build_whatsapp_nudge_body(title: str, body: str, question: Optional[str] = None) -> str:
    """Compact WhatsApp text for a nudge, keeping the suggested chat question actionable."""
    title_s = (title or "").strip()
    body_s = (body or "").strip()
    question_s = (question or "").strip()

    parts = []
    if title_s:
        parts.append(f"*{title_s[:120]}*")
    if body_s:
        parts.append(body_s[:500])
    if question_s:
        parts.append(
            "If you want, reply with this question:\n"
            f"{question_s[:700]}"
        )
    parts.append("Type *Menu* anytime to see AstroRoshni options.")
    return "\n\n".join(parts).strip()[:4090]


def send_whatsapp_nudge(
    conn,
    *,
    userid: int,
    title: str,
    body: str,
    question: Optional[str] = None,
) -> bool:
    """
    Best-effort fallback for users without usable app push.

    This only sends when the account is already linked to WhatsApp and we know
    the Meta phone_number_id from an existing WhatsApp session.
    """
    target = get_whatsapp_target_for_user(conn, int(userid))
    if not target:
        return False
    wa_id, phone_number_id = target
    try:
        from whatsapp.messaging import send_whatsapp_text

        return bool(
            send_whatsapp_text(
                to_wa_id=wa_id,
                phone_number_id=phone_number_id,
                body=build_whatsapp_nudge_body(title, body, question),
            )
        )
    except Exception as e:
        logger.warning("WhatsApp nudge fallback send failed user=%s: %s", userid, e)
        return False


def _digits_only(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _template_phone_number_id() -> str:
    return (
        os.getenv("WHATSAPP_NUDGE_PHONE_NUMBER_ID")
        or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        or ""
    ).strip()


def _template_name() -> str:
    return (os.getenv("WHATSAPP_NUDGE_TEMPLATE_NAME") or "chat_followup_available").strip()


def _template_language() -> str:
    return (os.getenv("WHATSAPP_NUDGE_TEMPLATE_LANGUAGE") or "en").strip()


def _get_user_phone_name(conn, userid: int) -> Optional[Tuple[str, str]]:
    try:
        cur = execute(
            conn,
            "SELECT COALESCE(phone, ''), COALESCE(NULLIF(TRIM(name), ''), 'there') FROM users WHERE userid = %s",
            (int(userid),),
        )
        row = cur.fetchone()
    except Exception as e:
        logger.warning("WhatsApp template nudge user lookup failed user=%s: %s", userid, e)
        return None
    if not row or not str(row[0] or "").strip():
        return None
    return str(row[0]).strip(), str(row[1] or "there").strip() or "there"


def send_whatsapp_nudge_template(
    conn,
    *,
    userid: int,
) -> bool:
    """
    Send the approved opt-in template to a phone-only user.

    The personalized nudge is intentionally not sent in the template. It is
    already stored in nudge_deliveries and is sent after the user taps Continue.
    """
    phone_number_id = _template_phone_number_id()
    if not phone_number_id:
        logger.warning("WhatsApp template nudge skipped: WHATSAPP_NUDGE_PHONE_NUMBER_ID/WHATSAPP_PHONE_NUMBER_ID missing")
        return False
    user = _get_user_phone_name(conn, int(userid))
    if not user:
        return False
    phone, name = user
    recipient = _digits_only(phone)
    if not recipient:
        return False
    try:
        from whatsapp.messaging import send_whatsapp_template

        return bool(
            send_whatsapp_template(
                to=recipient,
                phone_number_id=phone_number_id,
                template_name=_template_name(),
                language_code=_template_language(),
                body_params=[name[:80]],
                button_payload=WHATSAPP_NUDGE_CONTINUE_BUTTON_ID,
            )
        )
    except Exception as e:
        logger.warning("WhatsApp template nudge send failed user=%s: %s", userid, e)
        return False


def _find_user_by_wa_phone(conn, wa_id: str) -> Optional[int]:
    try:
        from whatsapp.phone_utils import phone_lookup_variants

        variants = phone_lookup_variants(wa_id)
    except Exception:
        variants = []
    if not variants:
        d = _digits_only(wa_id)
        variants = [wa_id, d, f"+{d}" if d else ""]
    variants = [v for v in dict.fromkeys(str(v or "").strip() for v in variants) if v]
    if not variants:
        return None
    placeholders = ", ".join(["%s"] * len(variants))
    try:
        # Prefer the active account whose phone matches the incoming WhatsApp
        # number. A stale whatsapp_wa_id can remain on deleted/old accounts.
        cur = execute(
            conn,
            f"""
            SELECT userid
            FROM users
            WHERE phone IN ({placeholders})
            ORDER BY userid DESC
            LIMIT 1
            """,
            tuple(variants),
        )
        row = cur.fetchone()
        if row and row[0] is not None:
            return int(row[0])
        cur = execute(
            conn,
            """
            SELECT userid
            FROM users
            WHERE whatsapp_wa_id = %s
            ORDER BY userid DESC
            LIMIT 1
            """,
            (str(wa_id).strip(),),
        )
        row = cur.fetchone()
        if row and row[0] is not None:
            return int(row[0])
    except Exception as e:
        logger.warning("WhatsApp template nudge user-by-wa lookup failed wa_id=%s: %s", wa_id, e)
    return None


def pop_pending_whatsapp_template_nudge(
    conn,
    *,
    wa_id: str,
    phone_number_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Link the WhatsApp sender to a phone-matched user and return the newest
    pending template nudge payload. The caller marks it consumed after send.
    """
    uid = _find_user_by_wa_phone(conn, wa_id)
    if not uid:
        return None
    try:
        execute(
            conn,
            "UPDATE users SET whatsapp_wa_id = %s WHERE userid = %s",
            (str(wa_id).strip(), int(uid)),
        )
        execute(
            conn,
            """
            UPDATE whatsapp_sessions
            SET userid = %s, last_phone_number_id = COALESCE(%s, last_phone_number_id), updated_at = CURRENT_TIMESTAMP
            WHERE wa_id = %s
            """,
            (int(uid), str(phone_number_id or "").strip() or None, str(wa_id).strip()),
        )
    except Exception as e:
        logger.warning("WhatsApp template nudge link update failed user=%s wa_id=%s: %s", uid, wa_id, e)

    since_dt = datetime.utcnow() - timedelta(days=7)
    try:
        cur = execute(
            conn,
            """
            SELECT id, title, body, data_json
            FROM nudge_deliveries
            WHERE userid = %s
              AND trigger_id = %s
              AND channel = %s
              AND created_at >= %s
              AND read_at IS NULL
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (int(uid), "chat_hourly_followup", "whatsapp_template", since_dt),
        )
        row = cur.fetchone()
        if not row:
            return {"userid": uid, "nudge": None}
        delivery_id = int(row[0])
        payload: Dict[str, Any] = {}
        if row[3]:
            import json

            try:
                parsed = json.loads(row[3])
                if isinstance(parsed, dict):
                    payload = parsed
            except Exception:
                payload = {}
        return {
            "userid": uid,
            "nudge": {
                "delivery_id": delivery_id,
                "title": str(row[1] or ""),
                "body": str(row[2] or ""),
                "question": str(payload.get("question") or ""),
            },
        }
    except Exception as e:
        logger.warning("WhatsApp pending template nudge fetch failed user=%s wa_id=%s: %s", uid, wa_id, e)
        return {"userid": uid, "nudge": None}


def mark_whatsapp_template_nudge_consumed(conn, delivery_id: int) -> None:
    try:
        execute(
            conn,
            "UPDATE nudge_deliveries SET read_at = CURRENT_TIMESTAMP WHERE id = %s",
            (int(delivery_id),),
        )
    except Exception as e:
        logger.warning("WhatsApp template nudge consumed marker failed delivery_id=%s: %s", delivery_id, e)
