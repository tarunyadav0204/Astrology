"""
WhatsApp inbound text: greeting → match phone / OTP signup / chart menu.
"""
from __future__ import annotations

import json
import logging
import os
import random
import re
import secrets
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple

import bcrypt
import requests

from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE
from sms_service import SMSService

from .phone_utils import (
    canonical_phone_for_registration,
    is_greeting,
    phone_lookup_variants,
    wa_id_to_lookup_phone,
)
from .schema import ensure_whatsapp_schema

logger = logging.getLogger(__name__)

sms_service = SMSService()

GREETING_LINES = (
    "Welcome to AstroRoshni on WhatsApp. "
    "We use your WhatsApp number to find your account. "
    "Say hi anytime to see your charts."
)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _encryptor():
    try:
        from encryption_utils import EncryptionManager

        return EncryptionManager()
    except ValueError:
        return None


def send_whatsapp_text(*, to_wa_id: str, body: str, phone_number_id: str) -> bool:
    token = (os.environ.get("WHATSAPP_ACCESS_TOKEN") or "").strip()
    if not token or not phone_number_id:
        logger.warning("Skipping WhatsApp send: missing WHATSAPP_ACCESS_TOKEN or phone_number_id")
        return False
    ver = (os.environ.get("WHATSAPP_GRAPH_API_VERSION") or "v22.0").strip().lstrip("/")
    url = f"https://graph.facebook.com/{ver}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "text",
        "text": {"preview_url": False, "body": body[:4090]},
    }
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if not (200 <= r.status_code < 300):
            logger.warning("WhatsApp send failed: %s %s", r.status_code, (r.text or "")[:500])
            return False
        return True
    except Exception as e:
        logger.exception("WhatsApp send error: %s", e)
        return False


def extract_inbound_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if payload.get("object") != "whatsapp_business_account":
        return out
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            if change.get("field") != "messages":
                continue
            val = change.get("value") or {}
            meta = val.get("metadata") or {}
            phone_number_id = str(meta.get("phone_number_id") or "")
            contacts = val.get("contacts") or []
            name_by_wa: Dict[str, str] = {}
            for c in contacts:
                wid = str(c.get("wa_id") or "")
                prof = (c.get("profile") or {}) if isinstance(c.get("profile"), dict) else {}
                nm = (prof.get("name") or "").strip()
                if wid and nm:
                    name_by_wa[wid] = nm
            for msg in val.get("messages") or []:
                if msg.get("type") != "text":
                    continue
                body = ((msg.get("text") or {}) if isinstance(msg.get("text"), dict) else {}).get("body") or ""
                frm = str(msg.get("from") or "")
                if not frm or not phone_number_id:
                    continue
                out.append(
                    {
                        "from": frm,
                        "body": str(body).strip(),
                        "phone_number_id": phone_number_id,
                        "profile_name": name_by_wa.get(frm, ""),
                    }
                )
    return out


def _find_user_by_phone(conn, phone: str) -> Optional[Tuple[Any, ...]]:
    variants = phone_lookup_variants(phone)
    if not variants:
        return None
    ph = ", ".join(["%s"] * len(variants))
    cur = execute(
        conn,
        f"SELECT userid, name, phone, password, role, email, signup_client FROM users WHERE phone IN ({ph})",
        tuple(variants),
    )
    return cur.fetchone()


def _find_user_by_wa_id(conn, wa_id: str) -> Optional[Tuple[Any, ...]]:
    cur = execute(
        conn,
        "SELECT userid, name, phone, password, role, email, signup_client FROM users WHERE whatsapp_wa_id = %s",
        (wa_id,),
    )
    return cur.fetchone()


def _get_session(conn, wa_id: str) -> Dict[str, Any]:
    cur = execute(
        conn,
        """
        SELECT wa_id, state, userid, reg_phone, reg_otp_token, reg_name, pending_charts_json, active_chart_id, last_phone_number_id
        FROM whatsapp_sessions WHERE wa_id = %s
        """,
        (wa_id,),
    )
    row = cur.fetchone()
    if row:
        return {
            "wa_id": row[0],
            "state": row[1] or "idle",
            "userid": row[2],
            "reg_phone": row[3],
            "reg_otp_token": row[4],
            "reg_name": row[5],
            "pending_charts_json": row[6],
            "active_chart_id": row[7],
            "last_phone_number_id": row[8],
        }
    try:
        execute(
            conn,
            "INSERT INTO whatsapp_sessions (wa_id, state, updated_at) VALUES (%s, 'idle', CURRENT_TIMESTAMP)",
            (wa_id,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    cur = execute(
        conn,
        """
        SELECT wa_id, state, userid, reg_phone, reg_otp_token, reg_name, pending_charts_json, active_chart_id, last_phone_number_id
        FROM whatsapp_sessions WHERE wa_id = %s
        """,
        (wa_id,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("whatsapp_sessions insert failed for wa_id=%s" % wa_id)
    return {
        "wa_id": row[0],
        "state": row[1] or "idle",
        "userid": row[2],
        "reg_phone": row[3],
        "reg_otp_token": row[4],
        "reg_name": row[5],
        "pending_charts_json": row[6],
        "active_chart_id": row[7],
        "last_phone_number_id": row[8],
    }


def _session_write(conn, wa_id: str, sess: Dict[str, Any], **updates: Any) -> Dict[str, Any]:
    """Merge `updates` into session row and persist. Returns the merged dict."""
    merged = {**sess, **updates}
    execute(
        conn,
        """
        UPDATE whatsapp_sessions SET
            state = %s,
            userid = %s,
            reg_phone = %s,
            reg_otp_token = %s,
            reg_name = %s,
            pending_charts_json = %s,
            active_chart_id = %s,
            last_phone_number_id = COALESCE(%s, last_phone_number_id),
            updated_at = CURRENT_TIMESTAMP
        WHERE wa_id = %s
        """,
        (
            merged.get("state") or "idle",
            merged.get("userid"),
            merged.get("reg_phone"),
            merged.get("reg_otp_token"),
            merged.get("reg_name"),
            merged.get("pending_charts_json"),
            merged.get("active_chart_id"),
            merged.get("last_phone_number_id"),
            wa_id,
        ),
    )
    conn.commit()
    return merged


def _touch_phone_number_id(conn, wa_id: str, phone_number_id: str) -> None:
    if not phone_number_id:
        return
    execute(
        conn,
        """
        UPDATE whatsapp_sessions SET last_phone_number_id = %s, updated_at = CURRENT_TIMESTAMP
        WHERE wa_id = %s
        """,
        (phone_number_id, wa_id),
    )
    conn.commit()


def _link_whatsapp_to_user(conn, wa_id: str, userid: int) -> None:
    execute(
        conn,
        "UPDATE users SET whatsapp_wa_id = NULL WHERE whatsapp_wa_id = %s AND userid <> %s",
        (wa_id, userid),
    )
    execute(conn, "UPDATE users SET whatsapp_wa_id = %s WHERE userid = %s", (wa_id, userid))
    conn.commit()


def _send_registration_sms(conn, canonical_phone: str) -> Tuple[bool, Optional[str]]:
    """Returns (ok, error_message). Inserts password_reset_codes row like /api/send-registration-otp."""
    existing = _find_user_by_phone(conn, canonical_phone)
    if existing:
        return False, "already_registered"

    code = str(random.randint(100000, 999999))
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    execute(
        conn,
        "INSERT INTO password_reset_codes (phone, code, token, expires_at) VALUES (%s, %s, %s, %s)",
        (canonical_phone, code, token, expires_at),
    )
    conn.commit()

    sent = sms_service.send_reset_code(canonical_phone, code)
    is_dev = (os.getenv("ENVIRONMENT", "development") == "development")
    if not sent and is_dev:
        logger.warning("WhatsApp registration OTP (dev SMS failed): %s for %s", code, canonical_phone)
    if not sent and not is_dev:
        return False, "sms_failed"
    return True, None


def _verify_otp_code(conn, phone: str, code: str) -> Optional[str]:
    """Return reset token if valid, else None."""
    variants = phone_lookup_variants(phone)
    if not variants:
        return None
    ph = ", ".join(["%s"] * len(variants))
    cur = execute(
        conn,
        f"""
        SELECT token FROM password_reset_codes
        WHERE phone IN ({ph}) AND code = %s AND expires_at > %s
          AND COALESCE(LOWER(TRIM(used::text)), '') NOT IN ('true', '1', 't', 'yes')
        """,
        tuple(variants) + (code, datetime.utcnow()),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _grant_free_subscriptions(conn, userid: int) -> None:
    start_date = date.today()
    end_date = start_date + timedelta(days=365)
    cur = execute(
        conn,
        f"SELECT plan_id FROM subscription_plans WHERE plan_name = 'Free' AND platform = 'astrovishnu' AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}",
    )
    av = cur.fetchone()
    cur = execute(
        conn,
        f"SELECT plan_id FROM subscription_plans WHERE plan_name = 'Free' AND platform = 'astroroshni' AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}",
    )
    ar = cur.fetchone()
    if av:
        execute(
            conn,
            "INSERT INTO user_subscriptions (userid, plan_id, start_date, end_date) VALUES (%s, %s, %s, %s)",
            (userid, av[0], start_date, end_date),
        )
    if ar:
        execute(
            conn,
            "INSERT INTO user_subscriptions (userid, plan_id, start_date, end_date) VALUES (%s, %s, %s, %s)",
            (userid, ar[0], start_date, end_date),
        )


def _complete_whatsapp_registration(
    conn,
    *,
    wa_id: str,
    canonical_phone: str,
    otp_token: str,
    name: str,
    password: str,
) -> Tuple[bool, str]:
    cur = execute(
        conn,
        """
            SELECT token FROM password_reset_codes
            WHERE phone = %s AND token = %s AND expires_at > %s
              AND COALESCE(LOWER(TRIM(used::text)), '') NOT IN ('true', '1', 't', 'yes')
        """,
        (canonical_phone, otp_token.strip(), datetime.utcnow()),
    )
    if not cur.fetchone():
        return False, "Invalid or expired verification. Say hi to start again."

    cur = execute(conn, "SELECT phone FROM users WHERE phone = %s", (canonical_phone,))
    if cur.fetchone():
        return False, "That number is already registered. Try logging in on the app."

    hashed = _hash_password(password)
    try:
        execute(
            conn,
            "INSERT INTO users (name, phone, password, role, email, signup_client, gender) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name.strip(), canonical_phone, hashed, "user", None, "mobile", None),
        )
    except Exception as e:
        conn.rollback()
        err = str(e).lower()
        if "unique" in err or "duplicate" in err:
            return False, "Could not create account (duplicate). Contact support."
        logger.exception("WhatsApp register insert failed")
        return False, "Could not create account. Try again later."

    cur = execute(
        conn,
        "SELECT userid, name, phone FROM users WHERE phone = %s",
        (canonical_phone,),
    )
    user = cur.fetchone()
    if not user:
        conn.rollback()
        return False, "Registration failed unexpectedly."

    userid = user[0]
    _grant_free_subscriptions(conn, userid)
    execute(conn, "UPDATE password_reset_codes SET used = 'TRUE' WHERE token = %s", (otp_token.strip(),))
    _link_whatsapp_to_user(conn, wa_id, userid)
    conn.commit()
    return True, f"Welcome, {name.strip()}! You are signed up and linked."


def _fetch_charts_lines(conn, userid: int, *, limit: int = 12) -> Tuple[str, List[Dict[str, Any]]]:
    encryptor = _encryptor()
    cur = execute(
        conn,
        """
        SELECT id, name, relation, date
        FROM birth_charts
        WHERE userid = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (userid, limit),
    )
    rows = cur.fetchall() or []
    meta: List[Dict[str, Any]] = []
    lines: List[str] = []
    for i, row in enumerate(rows, start=1):
        cid, name_raw, relation, _d = row[0], row[1], row[2] or "other", row[3]
        if encryptor:
            try:
                name = encryptor.decrypt(name_raw) if name_raw else "Chart"
            except Exception:
                name = "(chart)"
        else:
            name = name_raw or "Chart"
        meta.append({"id": int(cid), "label": f"{name} ({relation})"})
        lines.append(f"{i}. {name} ({relation})")
    body = "Your birth charts:\n" + "\n".join(lines) if lines else "You have no saved charts yet."
    body += "\n\nReply with a number to select that chart, or reply NEW to add one on the website."
    return body, meta


def _handle_chart_pick(
    conn,
    wa_id: str,
    text: str,
    phone_number_id: str,
    sess: Dict[str, Any],
) -> None:
    raw = (text or "").strip()
    low = raw.lower()
    if low in ("new", "n", "create"):
        send_whatsapp_text(
            to_wa_id=wa_id,
            body="Open https://astroroshni.com to create a new birth chart (full form). Say hi when you are done to pick it here.",
            phone_number_id=phone_number_id,
        )
        _session_write(
            conn,
            wa_id,
            sess,
            state="idle",
            pending_charts_json=None,
            reg_phone=None,
            reg_otp_token=None,
            reg_name=None,
        )
        return
    if not raw.isdigit():
        send_whatsapp_text(
            to_wa_id=wa_id,
            body="Reply with a chart number from the list, or NEW to add a chart on the website.",
            phone_number_id=phone_number_id,
        )
        return
    idx = int(raw)
    try:
        charts = json.loads(sess.get("pending_charts_json") or "[]")
    except json.JSONDecodeError:
        charts = []
    if not charts or idx < 1 or idx > len(charts):
        send_whatsapp_text(
            to_wa_id=wa_id,
            body="Invalid choice. Say hi to see your chart list again.",
            phone_number_id=phone_number_id,
        )
        return
    chosen = charts[idx - 1]
    cid = int(chosen["id"])
    _session_write(
        conn,
        wa_id,
        sess,
        state="idle",
        pending_charts_json=None,
        active_chart_id=cid,
    )
    send_whatsapp_text(
        to_wa_id=wa_id,
        body=f"Using chart: {chosen.get('label', cid)}. (Chat and chart features from WhatsApp can be wired next.)",
        phone_number_id=phone_number_id,
    )


def _push_chart_menu(conn, wa_id: str, userid: int, phone_number_id: str) -> None:
    sess = _get_session(conn, wa_id)
    body, meta = _fetch_charts_lines(conn, userid)
    _session_write(
        conn,
        wa_id,
        sess,
        state="await_chart_pick",
        userid=userid,
        pending_charts_json=json.dumps(meta),
    )
    send_whatsapp_text(to_wa_id=wa_id, body=body, phone_number_id=phone_number_id)


def _handle_idle_greeting(
    conn,
    wa_id: str,
    phone_number_id: str,
    profile_name: str,
) -> None:
    lookup_phone = wa_id_to_lookup_phone(wa_id)

    sess = _get_session(conn, wa_id)
    row_wa = _find_user_by_wa_id(conn, wa_id)
    if row_wa:
        uid = row_wa[0]
        _session_write(conn, wa_id, sess, state="idle", userid=uid)
        send_whatsapp_text(to_wa_id=wa_id, body=GREETING_LINES, phone_number_id=phone_number_id)
        _push_chart_menu(conn, wa_id, uid, phone_number_id)
        return

    row_phone = _find_user_by_phone(conn, lookup_phone)
    if row_phone:
        uid = row_phone[0]
        _link_whatsapp_to_user(conn, wa_id, uid)
        send_whatsapp_text(
            to_wa_id=wa_id,
            body=f"Hi{', ' + profile_name if profile_name else ''}! Your AstroRoshni account is linked.",
            phone_number_id=phone_number_id,
        )
        sess = _get_session(conn, wa_id)
        _session_write(conn, wa_id, sess, state="idle", userid=uid)
        _push_chart_menu(conn, wa_id, uid, phone_number_id)
        return

    canonical = canonical_phone_for_registration(wa_id)
    ok, err = _send_registration_sms(conn, canonical)
    if not ok:
        if err == "already_registered":
            send_whatsapp_text(
                to_wa_id=wa_id,
                body="This number looks registered already but is not linked here. Log in on the AstroRoshni app with this number, or contact help@astroroshni.com.",
                phone_number_id=phone_number_id,
            )
        else:
            send_whatsapp_text(
                to_wa_id=wa_id,
                body="We could not send an SMS code right now. Try again later or use the AstroRoshni app to sign up.",
                phone_number_id=phone_number_id,
            )
        return

    sess = _get_session(conn, wa_id)
    _session_write(
        conn,
        wa_id,
        sess,
        state="await_otp",
        reg_phone=canonical,
        reg_otp_token=None,
        reg_name=None,
        pending_charts_json=None,
        userid=None,
        last_phone_number_id=phone_number_id,
    )
    send_whatsapp_text(
        to_wa_id=wa_id,
        body=f"We sent a 6-digit code to {canonical}. Reply here with that code to create your AstroRoshni account.",
        phone_number_id=phone_number_id,
    )


def process_whatsapp_payload(payload: Dict[str, Any]) -> None:
    ensure_whatsapp_schema()
    messages = extract_inbound_messages(payload)
    if not messages:
        return

    for msg in messages:
        wa_id = msg["from"]
        body = msg["body"]
        phone_number_id = msg["phone_number_id"]
        profile_name = msg.get("profile_name") or ""

        try:
            with get_conn() as conn:
                sess = _get_session(conn, wa_id)
                if phone_number_id:
                    _touch_phone_number_id(conn, wa_id, phone_number_id)
                    sess["last_phone_number_id"] = phone_number_id

                st = sess.get("state") or "idle"

                if st == "await_chart_pick":
                    _handle_chart_pick(conn, wa_id, body, phone_number_id, sess)
                    continue

                if st == "await_otp":
                    if re.fullmatch(r"\d{6}", body.strip()):
                        token = _verify_otp_code(conn, sess.get("reg_phone") or "", body.strip())
                        if not token:
                            send_whatsapp_text(
                                to_wa_id=wa_id,
                                body="That code is invalid or expired. Say hi to request a new code.",
                                phone_number_id=phone_number_id,
                            )
                            continue
                        _session_write(
                            conn,
                            wa_id,
                            sess,
                            state="await_name",
                            reg_otp_token=token,
                            userid=None,
                        )
                        send_whatsapp_text(
                            to_wa_id=wa_id,
                            body="Code accepted. Reply with your full name as you want it on AstroRoshni.",
                            phone_number_id=phone_number_id,
                        )
                    else:
                        send_whatsapp_text(
                            to_wa_id=wa_id,
                            body="Please send the 6-digit code from your SMS, or say hi to start over.",
                            phone_number_id=phone_number_id,
                        )
                    continue

                if st == "await_name":
                    name = body.strip()
                    if len(name) < 2 or len(name) > 80:
                        send_whatsapp_text(
                            to_wa_id=wa_id,
                            body="Please send your name (2–80 characters).",
                            phone_number_id=phone_number_id,
                        )
                        continue
                    _session_write(
                        conn,
                        wa_id,
                        sess,
                        state="await_password",
                        reg_name=name,
                    )
                    send_whatsapp_text(
                        to_wa_id=wa_id,
                        body="Choose a password (at least 8 characters). You can change it later in the app.",
                        phone_number_id=phone_number_id,
                    )
                    continue

                if st == "await_password":
                    pw = body.strip()
                    if len(pw) < 8:
                        send_whatsapp_text(
                            to_wa_id=wa_id,
                            body="Password must be at least 8 characters. Try again.",
                            phone_number_id=phone_number_id,
                        )
                        continue
                    reg_phone = sess.get("reg_phone") or ""
                    otp_tok = sess.get("reg_otp_token") or ""
                    nm = sess.get("reg_name") or "User"
                    ok, detail = _complete_whatsapp_registration(
                        conn,
                        wa_id=wa_id,
                        canonical_phone=reg_phone,
                        otp_token=otp_tok,
                        name=nm,
                        password=pw,
                    )
                    if ok:
                        linked = _find_user_by_wa_id(conn, wa_id)
                        uid = linked[0] if linked else None
                        if uid is not None:
                            _session_write(
                                conn,
                                wa_id,
                                sess,
                                state="idle",
                                userid=uid,
                                reg_phone=None,
                                reg_otp_token=None,
                                reg_name=None,
                                pending_charts_json=None,
                            )
                        send_whatsapp_text(to_wa_id=wa_id, body=detail, phone_number_id=phone_number_id)
                        if uid is not None:
                            _push_chart_menu(conn, wa_id, uid, phone_number_id)
                    else:
                        send_whatsapp_text(to_wa_id=wa_id, body=detail, phone_number_id=phone_number_id)
                    continue

                # idle (default)
                if is_greeting(body):
                    _handle_idle_greeting(conn, wa_id, phone_number_id, profile_name)
                else:
                    send_whatsapp_text(
                        to_wa_id=wa_id,
                        body="Say hi to connect your AstroRoshni account or see your charts.",
                        phone_number_id=phone_number_id,
                    )
        except Exception:
            logger.exception("WhatsApp handler failed for wa_id=%s", wa_id)
