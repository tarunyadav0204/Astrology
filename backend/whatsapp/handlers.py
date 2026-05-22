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
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import bcrypt

from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE
from sms_service import SMSService

from .messaging import (
    send_whatsapp_interactive_flow,
    send_whatsapp_interactive_list,
    send_whatsapp_text,
    truncate_whatsapp,
)
from .phone_utils import (
    canonical_phone_for_registration,
    is_greeting,
    phone_lookup_variants,
    wa_id_to_lookup_phone,
)

from .chat_worker import schedule_whatsapp_chart_chat
from .schema import ensure_whatsapp_schema

if TYPE_CHECKING:
    from charts.routes import BirthData

logger = logging.getLogger(__name__)

_ALLOWED_FLOW_RELATIONS = frozenset(
    {"self", "spouse", "child", "parent", "sibling", "friend", "other"}
)


def _flatten_whatsapp_flow_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """WhatsApp may send `complete` fields at the top level or nested under `payload`."""
    inner = data.get("payload")
    if isinstance(inner, dict):
        merged = {k: v for k, v in data.items() if k not in ("payload",)}
        merged.update(inner)
        return merged
    return data


def _parse_flow_birth_date(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        ts = float(raw)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.utcfromtimestamp(ts).date().isoformat()
    s = str(raw).strip()
    if not s:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    try:
        return datetime.fromisoformat(s.replace("Z", "")).date().isoformat()
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _flow_time_hhmm(hour: Any, minute: Any) -> Optional[str]:
    try:
        h = int(str(hour).strip(), 10)
        m = int(str(minute).strip(), 10)
    except (ValueError, TypeError, AttributeError):
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return f"{h:02d}:{m:02d}"


def _birth_data_from_whatsapp_flow(data: Dict[str, Any]) -> Tuple[Optional["BirthData"], Optional[str]]:
    """
    Map birth_chart_flow.json `complete` payload into BirthData.

    Timezone is never read from the flow — ``BirthData.timezone`` is computed from lat/lon
    (same as POST /charts/calculate-chart).
    """
    from charts.routes import BirthData

    flat = _flatten_whatsapp_flow_payload(data)
    name = str(flat.get("chart_name") or "").strip()
    if len(name) < 1 or len(name) > 120:
        return None, "Chart name is missing or too long."

    relation = str(flat.get("relation") or "other").strip().lower()
    if relation not in _ALLOWED_FLOW_RELATIONS:
        relation = "other"

    date_iso = _parse_flow_birth_date(flat.get("birth_date"))
    if not date_iso:
        return None, "Birth date is missing or invalid."

    time_str = _flow_time_hhmm(flat.get("birth_hour"), flat.get("birth_minute"))
    if not time_str:
        return None, "Birth hour and minute are required."

    try:
        lat = float(flat.get("latitude"))
        lon = float(flat.get("longitude"))
    except (TypeError, ValueError):
        return None, "Birth place coordinates are missing or invalid."

    place = str(flat.get("place") or "").strip()
    if not place:
        return None, "Birth place text is missing."

    gender = str(flat.get("gender") or "").strip().lower()
    if gender not in ("male", "female", "other", ""):
        gender = "other"

    try:
        bd = BirthData(
            name=name,
            date=date_iso,
            time=time_str,
            latitude=lat,
            longitude=lon,
            place=place,
            gender=gender,
            relation=relation,
        )
    except Exception as e:
        return None, f"Invalid birth details: {e}"

    return bd, None

sms_service = SMSService()

GREETING_LINES = (
    "Welcome to AstroRoshni on WhatsApp. "
    "We use your WhatsApp number to find your account. "
    "Say hi anytime to see your charts."
)

# First inbound text while idle: one-time nudge, then same routing as a greeting (Path A/B).
SOFT_FIRST_CONTACT_NUDGE = (
    "Thanks for messaging AstroRoshni. "
    "We use this WhatsApp number to find or set up your account—the next message has your next step."
)

WHATSAPP_CHAT_WAIT_ACK = (
    "Working on your *Standard* reading now. This usually takes about 1 to 1.5 minutes. "
    "If the answer is long, we will send it in a few back-to-back messages on this chat."
)


def _whatsapp_menu_command(body: str) -> Optional[str]:
    low = (body or "").strip().lower()
    if low in ("charts", "menu", "list", "choose chart", "pick chart"):
        return low
    return None


def _should_route_idle_text_to_chart_chat(body: str, sess: Dict[str, Any]) -> bool:
    if not sess.get("userid") or not sess.get("active_chart_id"):
        return False
    if not (body or "").strip():
        return False
    if is_greeting(body):
        return False
    if _whatsapp_menu_command(body):
        return False
    raw = (body or "").strip()
    if raw.startswith("cr_"):
        return False
    if len(raw) < 2:
        return False
    return True


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _encryptor():
    try:
        from encryption_utils import EncryptionManager

        return EncryptionManager()
    except ValueError:
        return None


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
                frm = str(msg.get("from") or "")
                if not frm or not phone_number_id:
                    continue
                mtype = msg.get("type")
                if mtype == "text":
                    body = (
                        ((msg.get("text") or {}) if isinstance(msg.get("text"), dict) else {}).get("body") or ""
                    )
                    out.append(
                        {
                            "from": frm,
                            "body": str(body).strip(),
                            "phone_number_id": phone_number_id,
                            "profile_name": name_by_wa.get(frm, ""),
                            "input_kind": "text",
                        }
                    )
                elif mtype == "interactive":
                    inter = msg.get("interactive") or {}
                    itype = inter.get("type")
                    if itype == "list_reply":
                        lr = inter.get("list_reply") or {}
                        rid = str(lr.get("id") or "").strip()
                        if rid:
                            out.append(
                                {
                                    "from": frm,
                                    "body": rid,
                                    "phone_number_id": phone_number_id,
                                    "profile_name": name_by_wa.get(frm, ""),
                                    "input_kind": "list_reply",
                                }
                            )
                    elif itype == "nfm_reply":
                        nfm = inter.get("nfm_reply") or {}
                        rj = nfm.get("response_json")
                        if rj is not None and str(rj).strip():
                            out.append(
                                {
                                    "from": frm,
                                    "body": str(rj).strip(),
                                    "phone_number_id": phone_number_id,
                                    "profile_name": name_by_wa.get(frm, ""),
                                    "input_kind": "flow_reply",
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
        SELECT wa_id, state, userid, reg_phone, reg_otp_token, reg_name, pending_charts_json, active_chart_id, last_phone_number_id, pending_flow_token, idle_soft_intro_done, whatsapp_chat_session_id, whatsapp_chat_session_chart_id
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
            "pending_flow_token": row[9],
            "idle_soft_intro_done": bool(row[10]),
            "whatsapp_chat_session_id": row[11],
            "whatsapp_chat_session_chart_id": row[12],
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
        SELECT wa_id, state, userid, reg_phone, reg_otp_token, reg_name, pending_charts_json, active_chart_id, last_phone_number_id, pending_flow_token, idle_soft_intro_done, whatsapp_chat_session_id, whatsapp_chat_session_chart_id
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
        "pending_flow_token": row[9],
        "idle_soft_intro_done": bool(row[10]),
        "whatsapp_chat_session_id": row[11],
        "whatsapp_chat_session_chart_id": row[12],
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
            pending_flow_token = %s,
            idle_soft_intro_done = %s,
            whatsapp_chat_session_id = %s,
            whatsapp_chat_session_chart_id = %s,
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
            merged.get("pending_flow_token"),
            bool(merged.get("idle_soft_intro_done")),
            merged.get("whatsapp_chat_session_id"),
            merged.get("whatsapp_chat_session_chart_id"),
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


def _load_chart_meta(conn, userid: int, *, limit: int = 10) -> List[Dict[str, Any]]:
    """Chart rows for WhatsApp list (newest first). Each dict: id, name, relation, label."""
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
    for row in rows:
        cid, name_raw, relation, _d = row[0], row[1], row[2] or "other", row[3]
        if encryptor:
            try:
                name = encryptor.decrypt(name_raw) if name_raw else "Chart"
            except Exception:
                name = "(chart)"
        else:
            name = name_raw or "Chart"
        rel = relation or "other"
        meta.append(
            {
                "id": int(cid),
                "name": name,
                "relation": rel,
                "label": f"{name} ({rel})",
            }
        )
    return meta


def _fetch_charts_lines(conn, userid: int, *, limit: int = 12) -> Tuple[str, List[Dict[str, Any]]]:
    """Plain-text chart list fallback (reply with number)."""
    meta = _load_chart_meta(conn, userid, limit=limit)
    lines = [f"{i}. {m['label']}" for i, m in enumerate(meta, start=1)]
    body = "Your birth charts:\n" + "\n".join(lines) if lines else "You have no saved charts yet."
    body += "\n\nReply with a number to select that chart, or reply NEW to add one on the website."
    slim = [{"id": m["id"], "label": m["label"]} for m in meta]
    return body, slim


def _clear_chart_pick_state(conn, wa_id: str, sess: Dict[str, Any]) -> Dict[str, Any]:
    return _session_write(
        conn,
        wa_id,
        sess,
        state="idle",
        pending_charts_json=None,
        reg_phone=None,
        reg_otp_token=None,
        reg_name=None,
        pending_flow_token=None,
    )


def _birth_chart_flow_config() -> Dict[str, Any]:
    return {
        "flow_id": (os.environ.get("WHATSAPP_BIRTHCHART_FLOW_ID") or "").strip(),
        "flow_name": (os.environ.get("WHATSAPP_BIRTHCHART_FLOW_NAME") or "").strip(),
        "cta": (os.environ.get("WHATSAPP_BIRTHCHART_FLOW_CTA") or "Add birth details").strip(),
        "mode": (os.environ.get("WHATSAPP_BIRTHCHART_FLOW_MODE") or "published").strip().lower(),
        "header": (os.environ.get("WHATSAPP_BIRTHCHART_FLOW_HEADER") or "").strip() or None,
        "body": (
            os.environ.get("WHATSAPP_BIRTHCHART_FLOW_BODY")
            or "Tap the button and complete the form to add a birth chart."
        ).strip(),
        "footer": (os.environ.get("WHATSAPP_BIRTHCHART_FLOW_FOOTER") or "").strip() or None,
        "screen": (os.environ.get("WHATSAPP_BIRTHCHART_FLOW_SCREEN") or "").strip() or None,
    }


def _launch_birth_chart_flow_or_url(
    conn,
    wa_id: str,
    phone_number_id: str,
    sess: Dict[str, Any],
) -> None:
    """If Flow env is set, send WhatsApp Flow; else send website URL and clear chart-pick state."""
    cfg = _birth_chart_flow_config()
    uid = sess.get("userid")
    if cfg["flow_id"] or cfg["flow_name"]:
        tok = secrets.token_urlsafe(24)
        mode = cfg["mode"] if cfg["mode"] in ("draft", "published") else "published"
        screen = cfg["screen"] or None
        merged = _session_write(
            conn,
            wa_id,
            sess,
            state="await_flow_birth",
            pending_flow_token=tok,
            userid=uid,
        )
        ok = send_whatsapp_interactive_flow(
            to_wa_id=wa_id,
            phone_number_id=phone_number_id,
            body_text=cfg["body"],
            flow_cta=cfg["cta"],
            flow_token=tok,
            flow_id=cfg["flow_id"] or None,
            flow_name=cfg["flow_name"] or None,
            header_text=cfg["header"],
            footer_text=cfg["footer"],
            mode=mode,
            screen=screen,
            screen_data=None,
        )
        if not ok:
            _session_write(
                conn,
                wa_id,
                _get_session(conn, wa_id),
                state="idle",
                pending_flow_token=None,
            )
            send_whatsapp_text(
                to_wa_id=wa_id,
                body="We could not open the form. Open https://astroroshni.com to add a birth chart, then say hi.",
                phone_number_id=phone_number_id,
            )
        return

    send_whatsapp_text(
        to_wa_id=wa_id,
        body="Open https://astroroshni.com to create a new birth chart (full form). Say hi when you are done to pick it here.",
        phone_number_id=phone_number_id,
    )
    _clear_chart_pick_state(conn, wa_id, sess)


def _handle_flow_completion(
    conn,
    wa_id: str,
    response_json_str: str,
    phone_number_id: str,
) -> None:
    """User submitted a WhatsApp Flow; `response_json` echoes `flow_token` + screen fields."""
    sess = _get_session(conn, wa_id)
    try:
        data = json.loads(response_json_str)
    except json.JSONDecodeError:
        logger.warning("whatsapp flow_reply: invalid JSON")
        send_whatsapp_text(
            to_wa_id=wa_id,
            body="We could not read that form response. Say hi to try again.",
            phone_number_id=phone_number_id,
        )
        return

    incoming_tok = str(data.get("flow_token") or "").strip()
    expected = (sess.get("pending_flow_token") or "").strip()
    if not expected or incoming_tok != expected:
        logger.info(
            "whatsapp flow_reply: token mismatch wa_id=%s expected_set=%s",
            wa_id,
            bool(expected),
        )
        send_whatsapp_text(
            to_wa_id=wa_id,
            body="This form does not match your current session. Say hi to start again.",
            phone_number_id=phone_number_id,
        )
        return

    keys = [k for k in data.keys() if k != "flow_token"]
    logger.info("whatsapp flow_reply wa_id=%s fields=%s", wa_id, keys)

    uid = sess.get("userid")
    if not uid:
        _session_write(
            conn,
            wa_id,
            sess,
            state="idle",
            pending_flow_token=None,
            pending_charts_json=None,
        )
        send_whatsapp_text(
            to_wa_id=wa_id,
            body="We saved your answers but could not link them to an AstroRoshni account. Log in on the app, then say hi here again.",
            phone_number_id=phone_number_id,
        )
        return

    birth_data, parse_err = _birth_data_from_whatsapp_flow(data)
    if parse_err or not birth_data:
        logger.warning("whatsapp flow_reply: parse failed wa_id=%s err=%s", wa_id, parse_err)
        _session_write(
            conn,
            wa_id,
            sess,
            state="idle",
            pending_flow_token=None,
            pending_charts_json=None,
        )
        send_whatsapp_text(
            to_wa_id=wa_id,
            body=f"We could not save that chart: {parse_err or 'invalid data'}. You can add it on https://astroroshni.com or say hi to try again.",
            phone_number_id=phone_number_id,
        )
        return

    from charts.routes import persist_birth_chart_for_user

    chart_id, persist_err = persist_birth_chart_for_user(int(uid), birth_data)
    if persist_err or chart_id is None:
        logger.warning("whatsapp flow_reply: persist failed wa_id=%s err=%s", wa_id, persist_err)
        _session_write(
            conn,
            wa_id,
            sess,
            state="idle",
            pending_flow_token=None,
            pending_charts_json=None,
        )
        send_whatsapp_text(
            to_wa_id=wa_id,
            body=f"We could not save your chart: {persist_err or 'database error'}. Try again from the app at https://astroroshni.com .",
            phone_number_id=phone_number_id,
        )
        return

    _session_write(
        conn,
        wa_id,
        sess,
        state="idle",
        pending_flow_token=None,
        pending_charts_json=None,
        active_chart_id=chart_id,
        whatsapp_chat_session_id=None,
        whatsapp_chat_session_chart_id=None,
    )
    send_whatsapp_text(
        to_wa_id=wa_id,
        body=(
            f"Saved birth chart *{birth_data.name}*. It is active now — ask your astrology question in one message, "
            "or use the list to switch charts. A Standard reading can take 1–1.5 minutes."
        ),
        phone_number_id=phone_number_id,
    )
    _push_chart_menu(conn, wa_id, int(uid), phone_number_id)


def _handle_chart_pick(
    conn,
    wa_id: str,
    text: str,
    phone_number_id: str,
    sess: Dict[str, Any],
) -> None:
    raw = (text or "").strip()
    low = raw.lower()
    uid = sess.get("userid")

    def _new_chart_message() -> None:
        _launch_birth_chart_flow_or_url(conn, wa_id, phone_number_id, sess)

    if low in ("new", "n", "create") or raw == "cr_new" or low == "cr_new":
        _new_chart_message()
        return

    if raw.startswith("cr_") and raw[3:].isdigit():
        cid = int(raw[3:])
        if not uid:
            send_whatsapp_text(
                to_wa_id=wa_id,
                body="Session expired. Say hi to start again.",
                phone_number_id=phone_number_id,
            )
            return
        cur = execute(
            conn,
            "SELECT id FROM birth_charts WHERE id = %s AND userid = %s",
            (cid, uid),
        )
        if not cur.fetchone():
            send_whatsapp_text(
                to_wa_id=wa_id,
                body="That chart was not found on your account. Say hi to refresh the list.",
                phone_number_id=phone_number_id,
            )
            return
        label = f"Chart #{cid}"
        try:
            charts = json.loads(sess.get("pending_charts_json") or "[]")
            for c in charts:
                if int(c.get("id", 0)) == cid:
                    label = str(c.get("label") or label)
                    break
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        _session_write(
            conn,
            wa_id,
            sess,
            state="idle",
            pending_charts_json=None,
            active_chart_id=cid,
            whatsapp_chat_session_id=None,
            whatsapp_chat_session_chart_id=None,
        )
        send_whatsapp_text(
            to_wa_id=wa_id,
            body=(
                f"Using chart: {label}. Ask your astrology question in one message. "
                "A Standard reading can take 1–1.5 minutes and may arrive in several parts."
            ),
            phone_number_id=phone_number_id,
        )
        return

    if not raw.isdigit():
        send_whatsapp_text(
            to_wa_id=wa_id,
            body=(
                "Reply with a chart number (1–9), or NEW to add one. "
                "If you see a *Choose chart* button above, you can use that list too."
            ),
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
        whatsapp_chat_session_id=None,
        whatsapp_chat_session_chart_id=None,
    )
    send_whatsapp_text(
        to_wa_id=wa_id,
        body=(
            f"Using chart: {chosen.get('label', cid)}. Ask your astrology question in one message. "
            "A Standard reading can take 1–1.5 minutes and may arrive in several parts."
        ),
        phone_number_id=phone_number_id,
    )


def _push_chart_menu(conn, wa_id: str, userid: int, phone_number_id: str) -> None:
    sess = _get_session(conn, wa_id)
    meta_full = _load_chart_meta(conn, userid, limit=10)
    truncated_note = ""
    if len(meta_full) > 9:
        meta_charts = meta_full[:9]
        truncated_note = " Showing your 9 newest charts (WhatsApp list limit)."
    else:
        meta_charts = meta_full

    slim = [{"id": m["id"], "label": m["label"]} for m in meta_charts]
    pending_json = json.dumps(slim)

    rows: List[Tuple[str, str, str]] = []
    for m in meta_charts:
        rid = f"cr_{m['id']}"
        title = truncate_whatsapp(f"{m['name']} · {m['relation']}", 24)
        desc = truncate_whatsapp(m["label"], 72)
        rows.append((rid, title, desc))

    rows.append(("cr_new", "Add new chart", "astroroshni.com"))

    if meta_charts:
        body = (
            "Tap the button below, then choose a birth chart. "
            "You can still reply with a number (1–9) or NEW if you prefer." + truncated_note
        )
    else:
        body = "You do not have a saved birth chart yet. Tap *Choose chart*, then *Add new chart*."

    _session_write(
        conn,
        wa_id,
        sess,
        state="await_chart_pick",
        userid=userid,
        pending_charts_json=pending_json,
    )

    ok = send_whatsapp_interactive_list(
        to_wa_id=wa_id,
        phone_number_id=phone_number_id,
        body=body,
        button_text="Choose chart",
        section_title="Birth charts",
        rows=rows,
        header_text="AstroRoshni",
        footer_text="astroroshni.com",
    )
    if not ok:
        sess2 = _get_session(conn, wa_id)
        body_txt, slim2 = _fetch_charts_lines(conn, userid, limit=12)
        _session_write(
            conn,
            wa_id,
            sess2,
            state="await_chart_pick",
            userid=userid,
            pending_charts_json=json.dumps(slim2),
        )
        send_whatsapp_text(to_wa_id=wa_id, body=body_txt, phone_number_id=phone_number_id)


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

                input_kind = msg.get("input_kind") or "text"
                if input_kind == "flow_reply":
                    _handle_flow_completion(conn, wa_id, body, phone_number_id)
                    continue

                st = sess.get("state") or "idle"

                if st == "await_chart_pick":
                    if is_greeting(body):
                        _handle_idle_greeting(conn, wa_id, phone_number_id, profile_name)
                    else:
                        _handle_chart_pick(conn, wa_id, body, phone_number_id, sess)
                    continue

                if st == "await_flow_birth":
                    if is_greeting(body):
                        _handle_idle_greeting(conn, wa_id, phone_number_id, profile_name)
                    else:
                        send_whatsapp_text(
                            to_wa_id=wa_id,
                            body="Please finish the form (tap the button on our last message). Or say hi to start over.",
                            phone_number_id=phone_number_id,
                        )
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
                if st == "idle" and input_kind == "text":
                    cmd = _whatsapp_menu_command(body)
                    uid_menu = sess.get("userid")
                    if cmd and uid_menu:
                        _push_chart_menu(conn, wa_id, int(uid_menu), phone_number_id)
                        continue

                if (
                    st == "idle"
                    and input_kind == "text"
                    and _should_route_idle_text_to_chart_chat(body, sess)
                ):
                    send_whatsapp_text(
                        to_wa_id=wa_id,
                        body=WHATSAPP_CHAT_WAIT_ACK,
                        phone_number_id=phone_number_id,
                    )
                    schedule_whatsapp_chart_chat(
                        wa_id=wa_id,
                        phone_number_id=phone_number_id,
                        userid=int(sess["userid"]),
                        question=body.strip(),
                    )
                    continue

                soft_intro_done = bool(sess.get("idle_soft_intro_done"))
                if (
                    st == "idle"
                    and not soft_intro_done
                    and input_kind == "text"
                    and (body or "").strip()
                ):
                    send_whatsapp_text(
                        to_wa_id=wa_id,
                        body=SOFT_FIRST_CONTACT_NUDGE,
                        phone_number_id=phone_number_id,
                    )
                    _handle_idle_greeting(conn, wa_id, phone_number_id, profile_name)
                    sess_after = _get_session(conn, wa_id)
                    _session_write(conn, wa_id, sess_after, idle_soft_intro_done=True)
                    continue

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
