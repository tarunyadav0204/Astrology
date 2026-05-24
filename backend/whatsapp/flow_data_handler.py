"""
Business logic for WhatsApp Flow data channel (ping, INIT, place search exchange).

Screen ids / field names can be aligned with your Flow JSON via env vars below.
"""
from __future__ import annotations

import logging
import os
import random
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict

from db import execute, get_conn
from utils.google_places_client import place_details as gp_place_details
from utils.google_places_client import places_autocomplete_suggestions
from utils.smtp_mail import send_plain_text_email

logger = logging.getLogger(__name__)


def _env(name: str, default: str) -> str:
    return (os.environ.get(name) or default).strip()


def _flow_token(decrypted: Dict[str, Any], data: Dict[str, Any]) -> str:
    return str(decrypted.get("flow_token") or data.get("flow_token") or "").strip()


def _normalize_email(raw: str) -> str:
    email = (raw or "").strip().lower()
    if not email or len(email) > 254:
        return ""
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return ""
    return email


def _normalize_gender(raw: str) -> str:
    value = (raw or "").strip().lower()
    if value in {"1", "m", "male", "man"}:
        return "male"
    if value in {"2", "f", "female", "woman"}:
        return "female"
    return ""


def _send_email_otp(email: str, code: str) -> bool:
    body = (
        f"Your AstroRoshni email verification code is: {code}\n\n"
        "This code expires in 10 minutes."
    )
    try:
        return bool(send_plain_text_email(email, "Verify your AstroRoshni email", body))
    except Exception:
        logger.exception("registration flow email OTP failed for %s", email)
        return False


def _find_registration_session(flow_token: str):
    if not flow_token:
        return None
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT wa_id, reg_phone, reg_otp_token, reg_name, pending_charts_json
            FROM whatsapp_sessions
            WHERE pending_flow_token = %s AND state = 'await_flow_registration'
            """,
            (flow_token,),
        )
        return cur.fetchone()


def _update_registration_session(flow_token: str, **updates: Any) -> None:
    if not flow_token or not updates:
        return
    allowed = {
        "reg_otp_token",
        "reg_name",
        "pending_charts_json",
    }
    sets = []
    vals = []
    for k, v in updates.items():
        if k in allowed:
            sets.append(f"{k} = %s")
            vals.append(v)
    if not sets:
        return
    vals.append(flow_token)
    with get_conn() as conn:
        execute(
            conn,
            f"""
            UPDATE whatsapp_sessions
            SET {", ".join(sets)}, updated_at = CURRENT_TIMESTAMP
            WHERE pending_flow_token = %s AND state = 'await_flow_registration'
            """,
            tuple(vals),
        )
        conn.commit()


def _load_pending_json(raw: Any) -> Dict[str, Any]:
    try:
        import json

        val = json.loads(raw or "{}")
        return val if isinstance(val, dict) else {}
    except Exception:
        return {}


def _registration_error(screen: str, message: str) -> Dict[str, Any]:
    return {"screen": screen, "data": {"error_message": message}}


def _verify_registration_sms_otp(flow_token: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
    if not flow_token:
        return _registration_error("sms_otp", "Session expired. Close this form and start again.")
    row = _find_registration_session(flow_token)
    if not row:
        return _registration_error("sms_otp", "Session expired. Close this form and start again.")
    reg_phone = str(row[1] or "")
    code = str(data.get("sms_otp") or "").strip()
    if not re.fullmatch(r"\d{6}", code):
        return _registration_error("sms_otp", "Enter the 6-digit SMS code.")

    from whatsapp.phone_utils import phone_lookup_variants

    variants = phone_lookup_variants(reg_phone)
    if not variants:
        return _registration_error("sms_otp", "Could not verify this phone. Start again.")
    ph = ", ".join(["%s"] * len(variants))
    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            SELECT token FROM password_reset_codes
            WHERE phone IN ({ph}) AND code = %s AND expires_at > %s
              AND COALESCE(LOWER(TRIM(used::text)), '') NOT IN ('true', '1', 't', 'yes')
            """,
            tuple(variants) + (code, datetime.utcnow()),
        )
        otp_row = cur.fetchone()
    if not otp_row:
        return _registration_error("sms_otp", "That SMS code is invalid or expired.")

    _update_registration_session(flow_token, reg_otp_token=str(otp_row[0]))
    return {"screen": "profile", "data": {}}


def _send_registration_email_otp(flow_token: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
    if not flow_token or not _find_registration_session(flow_token):
        return _registration_error("email_entry", "Session expired. Close this form and start again.")
    name = str(data.get("name") or "").strip()
    gender = _normalize_gender(str(data.get("gender") or ""))
    email = _normalize_email(str(data.get("email") or ""))
    if len(name) < 2 or len(name) > 80:
        return _registration_error("email_entry", "Enter your full name on the previous screen.")
    if not gender:
        return _registration_error("email_entry", "Choose your gender on the previous screen.")
    if not email:
        return _registration_error("email_entry", "Enter a valid email address.")

    code = str(random.randint(100000, 999999))
    sent = _send_email_otp(email, code)
    is_dev = (os.getenv("ENVIRONMENT", "development") == "development")
    if not sent and is_dev:
        logger.warning("registration flow email OTP (dev email failed): %s for %s", code, email)
    if not sent and not is_dev:
        return _registration_error("email_entry", "Could not send email code. Try another email.")

    pending = {
        "name": name,
        "gender": gender,
        "email": email,
        "email_code": code,
        "email_expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
    }
    import json

    _update_registration_session(flow_token, reg_name=name, pending_charts_json=json.dumps(pending))
    return {"screen": "email_otp", "data": {"email_display": email}}


def _verify_registration_email_otp(flow_token: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
    row = _find_registration_session(flow_token)
    if not flow_token or not row:
        return _registration_error("email_otp", "Session expired. Close this form and start again.")
    pending = _load_pending_json(row[4])
    expected = str(pending.get("email_code") or "").strip()
    code = str(data.get("email_otp") or "").strip()
    try:
        expires_at = datetime.fromisoformat(str(pending.get("email_expires_at") or ""))
    except ValueError:
        expires_at = datetime.utcnow() - timedelta(seconds=1)
    if not re.fullmatch(r"\d{6}", code) or code != expected or expires_at <= datetime.utcnow():
        return _registration_error("email_otp", "That email code is invalid or expired.")
    pending["email_verified"] = True
    pending.pop("email_code", None)
    import json

    _update_registration_session(flow_token, pending_charts_json=json.dumps(pending))
    return {"screen": "password", "data": {}}


def _validate_registration_password(flow_token: str, data: Dict[str, Any]) -> Dict[str, Any] | None:
    if not flow_token or not _find_registration_session(flow_token):
        return _registration_error("password", "Session expired. Close this form and start again.")
    password = str(data.get("password") or "")
    confirm = str(data.get("confirm_password") or "")
    if len(password.strip()) < 8:
        return _registration_error("password", "Password must be at least 8 characters.")
    if password != confirm:
        return _registration_error("password", "Passwords do not match.")
    return {"screen": "registration_review", "data": {}}


# Meta: RadioButtonsGroup option titles must be ≤30 chars. The client shows one red banner per bad row.
def _utf16_code_unit_len(s: str) -> int:
    """Some clients count string limits like UTF-16 (BMP) length."""
    return len(s.encode("utf-16-le")) // 2


def _truncate_flow_radio_title(text: str, max_units: int = 30) -> str:
    s = " ".join((text or "").strip().split()) or "?"
    if _utf16_code_unit_len(s) <= max_units:
        return s
    suffix = "..."
    su = _utf16_code_unit_len(suffix)
    budget = max_units - su
    if budget <= 0:
        return suffix[:max_units]
    lo, hi = 0, len(s)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        cand = s[:mid].rstrip() + suffix
        if _utf16_code_unit_len(cand) <= max_units:
            lo = mid
        else:
            hi = mid - 1
    out = s[:lo].rstrip() + suffix
    while _utf16_code_unit_len(out) > max_units and out:
        out = out[:-1]
    return out or "?"


def build_flow_data_response(decrypted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build plaintext JSON object for encrypt_flow_response.
    """
    action = str(decrypted.get("action") or "").strip().lower()
    screen = str(decrypted.get("screen") or "")
    data = decrypted.get("data")
    if not isinstance(data, dict):
        data = {}

    # Health check (no screen required)
    if action == "ping":
        return {"data": {"status": "active"}}

    flow_token = _flow_token(decrypted, data)
    if action == "data_exchange" and screen == "sms_otp":
        res = _verify_registration_sms_otp(flow_token, data)
        if res is not None:
            return res
    if action == "data_exchange" and screen == "email_entry":
        res = _send_registration_email_otp(flow_token, data)
        if res is not None:
            return res
    if action == "data_exchange" and screen == "email_otp":
        res = _verify_registration_email_otp(flow_token, data)
        if res is not None:
            return res
    if action == "data_exchange" and screen == "password":
        res = _validate_registration_password(flow_token, data)
        if res is not None:
            return res

    init_screen = _env("WHATSAPP_FLOW_DATA_INIT_SCREEN", "create_birth_chart")
    search_screen = _env("WHATSAPP_FLOW_DATA_SCREEN_SEARCH", "place_search")
    pick_screen = _env("WHATSAPP_FLOW_DATA_SCREEN_PICK", "place_pick")
    after_place_screen = _env("WHATSAPP_FLOW_DATA_SCREEN_AFTER_PLACE", "birth_place_gender")
    query_field = _env("WHATSAPP_FLOW_DATA_FIELD_PLACE_QUERY", "place_query")
    pick_field = _env("WHATSAPP_FLOW_DATA_FIELD_SELECTED_PLACE", "selected_place")

    # Meta sends action lowercased in practice; we normalize with .lower() above.
    if action == "init":
        reg_row = _find_registration_session(flow_token)
        if reg_row:
            return {
                "screen": "registration_welcome",
                "data": {"phone_display": str(reg_row[1] or "")},
            }
        return {"screen": init_screen, "data": {}}

    if action == "back":
        # Minimal: echo empty data; override with refresh_on_back logic if needed.
        return {"screen": screen or init_screen, "data": {}}

    if action == "data_exchange" and screen == search_screen:
        q = str(data.get(query_field) or "").strip()
        if len(q) < 2:
            return {
                "screen": search_screen,
                "data": {
                    "error_message": "Type at least 2 characters to search.",
                    "place_options": [],
                },
            }
        try:
            rows = places_autocomplete_suggestions(q, limit=8)
        except Exception as e:
            logger.warning("flow data_exchange autocomplete failed: %s", e)
            return {
                "screen": search_screen,
                "data": {
                    "error_message": "Could not search places. Try again.",
                    "place_options": [],
                },
            }
        place_options = [
            {"id": r["place_id"], "title": _truncate_flow_radio_title(r.get("description") or "")}
            for r in rows
        ]
        if not place_options:
            return {
                "screen": search_screen,
                "data": {
                    "error_message": "No matches. Try a different city or add country.",
                    "place_options": [],
                },
            }
        return {"screen": pick_screen, "data": {"place_options": place_options}}

    if action == "data_exchange" and screen == pick_screen:
        pid = str(data.get(pick_field) or data.get("place_id") or "").strip()
        if not pid:
            return {
                "screen": pick_screen,
                "data": {"error_message": "Please choose a place from the list."},
            }
        try:
            details = gp_place_details(pid)
        except Exception as e:
            logger.warning("flow data_exchange place details failed: %s", e)
            return {
                "screen": pick_screen,
                "data": {"error_message": "Could not load that place. Pick another."},
            }
        return {
            "screen": after_place_screen,
            "data": {
                "selected_latitude": details["latitude"],
                "selected_longitude": details["longitude"],
                "selected_formatted_address": details["formattedAddress"],
                "selected_place_id": details["place_id"],
            },
        }

    logger.info(
        "flow data: unhandled action=%r screen=%r keys=%s",
        action,
        screen,
        list(data.keys())[:20],
    )
    if action == "data_exchange" and screen:
        return {
            "screen": screen,
            "data": {"error_message": "This step is not supported on the server yet."},
        }
    return {"screen": init_screen, "data": {}}
