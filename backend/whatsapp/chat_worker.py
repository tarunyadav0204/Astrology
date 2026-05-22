"""
Background WhatsApp → chat-v2 pipeline (Standard tier, same contract as mobile).

Uses HTTP to the app's own /api/chat-v2/ask + /status so credits, intent router, and
persistence stay identical to the AstroRoshni app.
"""
from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import requests

from auth import create_access_token_for_phone
from credits.credit_service import CreditService
from db import execute, get_conn

from .messaging import send_whatsapp_text

logger = logging.getLogger(__name__)

_LOCK_GUARD = threading.Lock()
_WA_LOCKS: Dict[str, threading.Lock] = {}


def _wa_lock(wa_id: str) -> threading.Lock:
    with _LOCK_GUARD:
        if wa_id not in _WA_LOCKS:
            _WA_LOCKS[wa_id] = threading.Lock()
        return _WA_LOCKS[wa_id]


def _api_base() -> str:
    """
    Base URL for same-machine HTTP calls to /api/chat-v2/* from the WhatsApp worker thread.

    Prefer WHATSAPP_INTERNAL_API_URL (or ASTRO_INTERNAL_API_URL / PUBLIC_API_BASE_URL).
    If unset, default to loopback using PORT or UVICORN_PORT when present (e.g. Cloud Run,
    gunicorn --bind 0.0.0.0:$PORT); else 8000.
    """
    explicit = (
        os.environ.get("WHATSAPP_INTERNAL_API_URL")
        or os.environ.get("ASTRO_INTERNAL_API_URL")
        or os.environ.get("PUBLIC_API_BASE_URL")
    )
    if explicit:
        return explicit.strip().rstrip("/")
    port_raw = (os.environ.get("PORT") or os.environ.get("UVICORN_PORT") or "8000").strip()
    if not port_raw.isdigit():
        port_raw = "8000"
    return f"http://127.0.0.1:{port_raw}".rstrip("/")


def _encryptor():
    try:
        from encryption_utils import EncryptionManager

        return EncryptionManager()
    except ValueError:
        return None


def chunk_text_for_whatsapp(text: str, max_len: int = 4090) -> List[str]:
    """Split for WhatsApp Cloud API text bodies (Meta limit 4096; stay under)."""
    t = (text or "").strip()
    if not t:
        return []
    if len(t) <= max_len:
        return [t]
    parts: List[str] = []
    while t:
        if len(t) <= max_len:
            parts.append(t)
            break
        chunk = t[:max_len]
        cut = max(chunk.rfind("\n\n"), chunk.rfind("\n"), chunk.rfind(" "))
        if cut < max_len // 2:
            cut = max_len
        parts.append(t[:cut].rstrip())
        t = t[cut:].lstrip()
    return parts


def _load_user_phone(conn, userid: int) -> Optional[str]:
    cur = execute(conn, "SELECT phone FROM users WHERE userid = %s", (userid,))
    row = cur.fetchone()
    if not row or not row[0]:
        return None
    return str(row[0]).strip()


def load_birth_details_for_chart(conn, userid: int, chart_id: int) -> Optional[Dict[str, Any]]:
    """Decrypt birth_charts row into chat-v2 birth_details dict."""
    from chat_history.routes import coerce_chat_birth_details

    enc = _encryptor()
    cur = execute(
        conn,
        """
        SELECT id, userid, name, date, time, latitude, longitude, place, gender
        FROM birth_charts
        WHERE id = %s AND userid = %s
        """,
        (chart_id, userid),
    )
    row = cur.fetchone()
    if not row:
        return None

    def dec(val: Any) -> str:
        if val is None:
            return ""
        s = str(val)
        if enc:
            try:
                return enc.decrypt(s)
            except Exception:
                return s
        return s

    try:
        lat = float(str(dec(row[5])).strip())
        lon = float(str(dec(row[6])).strip())
    except (TypeError, ValueError):
        return None

    return coerce_chat_birth_details(
        {
            "id": int(row[0]),
            "name": dec(row[2]),
            "date": dec(row[3]),
            "time": dec(row[4]),
            "latitude": lat,
            "longitude": lon,
            "place": dec(row[7]) or "",
            "gender": dec(row[8]) or "",
        }
    )


def schedule_whatsapp_chart_chat(
    *,
    wa_id: str,
    phone_number_id: str,
    userid: int,
    question: str,
) -> None:
    threading.Thread(
        target=_run_whatsapp_chart_chat_guarded,
        kwargs={
            "wa_id": wa_id,
            "phone_number_id": phone_number_id,
            "userid": userid,
            "question": question,
        },
        daemon=True,
        name=f"wa-chat-{wa_id}",
    ).start()


def _run_whatsapp_chart_chat_guarded(**kwargs: Any) -> None:
    try:
        _run_whatsapp_chart_chat(**kwargs)
    except Exception:
        logger.exception("whatsapp chart chat worker crashed wa_id=%s", kwargs.get("wa_id"))
        try:
            send_whatsapp_text(
                to_wa_id=str(kwargs.get("wa_id") or ""),
                body="Something went wrong while preparing your reading. Please try again in a minute or use the AstroRoshni app.",
                phone_number_id=str(kwargs.get("phone_number_id") or ""),
            )
        except Exception:
            pass


def _run_whatsapp_chart_chat(
    *,
    wa_id: str,
    phone_number_id: str,
    userid: int,
    question: str,
) -> None:
    lock = _wa_lock(wa_id)
    if not lock.acquire(blocking=False):
        send_whatsapp_text(
            to_wa_id=wa_id,
            body="We are still working on your previous question. Please wait for it to finish, then ask again.",
            phone_number_id=phone_number_id,
        )
        return

    try:
        base = _api_base()
        token: Optional[str] = None
        chart_id: Optional[int] = None
        session_id: Optional[str] = None

        with get_conn() as conn:
            phone = _load_user_phone(conn, userid)
            if not phone:
                send_whatsapp_text(
                    to_wa_id=wa_id,
                    body="We could not load your account phone. Say hi to reconnect.",
                    phone_number_id=phone_number_id,
                )
                return
            token = create_access_token_for_phone(phone, expire_minutes=180)

            cur = execute(
                conn,
                """
                SELECT active_chart_id, whatsapp_chat_session_id, whatsapp_chat_session_chart_id
                FROM whatsapp_sessions
                WHERE wa_id = %s
                """,
                (wa_id,),
            )
            srow = cur.fetchone()
            if not srow or not srow[0]:
                send_whatsapp_text(
                    to_wa_id=wa_id,
                    body="Pick a birth chart first (say hi → Choose chart), then ask your question.",
                    phone_number_id=phone_number_id,
                )
                return
            chart_id = int(srow[0])
            cached_sid = srow[1]
            cached_cid = srow[2]
            bd = load_birth_details_for_chart(conn, userid, chart_id)
            if not bd:
                send_whatsapp_text(
                    to_wa_id=wa_id,
                    body="That birth chart could not be loaded. Choose another chart from the menu (say hi).",
                    phone_number_id=phone_number_id,
                )
                return

            if cached_sid and cached_cid == chart_id:
                session_id = str(cached_sid)
            else:
                session_id = str(uuid.uuid4())
                execute(
                    conn,
                    "INSERT INTO chat_sessions (session_id, user_id, birth_chart_id) VALUES (%s, %s, %s)",
                    (session_id, userid, chart_id),
                )
                execute(
                    conn,
                    """
                    UPDATE whatsapp_sessions
                    SET whatsapp_chat_session_id = %s, whatsapp_chat_session_chart_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE wa_id = %s
                    """,
                    (session_id, chart_id, wa_id),
                )
            conn.commit()

        assert token and session_id and chart_id

        credit_service = CreditService()
        balance_before: Optional[int] = None
        try:
            balance_before = credit_service.get_user_credits(userid)
        except Exception:
            logger.exception("whatsapp chat: could not read balance_before user=%s", userid)

        client_request_id = str(uuid.uuid4())
        ask_url = f"{base}/api/chat-v2/ask"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "session_id": session_id,
            "question": question,
            "birth_details": bd,
            "language": "english",
            "response_style": "detailed",
            "premium_analysis": False,
            "chat_tier": "standard",
            "partnership_mode": False,
            "native_name": bd.get("name"),
            "query_context": {},
            "client_request_id": client_request_id,
        }

        content: Optional[str] = None
        err: Optional[str] = None
        try:
            r = requests.post(ask_url, headers=headers, json=payload, timeout=120)
            if r.status_code == 402:
                send_whatsapp_text(
                    to_wa_id=wa_id,
                    body="You do not have enough credits for a standard reading on this chart. Open the AstroRoshni app to top up, then try again here.",
                    phone_number_id=phone_number_id,
                )
                return
            if r.status_code == 409 and "CHART_SESSION_MISMATCH" in (r.text or ""):
                with get_conn() as conn:
                    sid_new = str(uuid.uuid4())
                    execute(
                        conn,
                        "INSERT INTO chat_sessions (session_id, user_id, birth_chart_id) VALUES (%s, %s, %s)",
                        (sid_new, userid, chart_id),
                    )
                    execute(
                        conn,
                        """
                        UPDATE whatsapp_sessions
                        SET whatsapp_chat_session_id = %s, whatsapp_chat_session_chart_id = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE wa_id = %s
                        """,
                        (sid_new, chart_id, wa_id),
                    )
                    conn.commit()
                session_id = sid_new
                payload["session_id"] = session_id
                payload["client_request_id"] = str(uuid.uuid4())
                r = requests.post(ask_url, headers=headers, json=payload, timeout=120)

            if not (200 <= r.status_code < 300):
                logger.warning(
                    "whatsapp chat ask failed status=%s body=%s",
                    r.status_code,
                    (r.text or "")[:800],
                )
                send_whatsapp_text(
                    to_wa_id=wa_id,
                    body="We could not start that reading (server error). Please try again or use the AstroRoshni app.",
                    phone_number_id=phone_number_id,
                )
                return

            ask_json = r.json()
            assistant_message_id = ask_json.get("message_id")
            if not assistant_message_id:
                send_whatsapp_text(
                    to_wa_id=wa_id,
                    body="We could not start that reading (unexpected response). Please try again.",
                    phone_number_id=phone_number_id,
                )
                return

            status_url = f"{base}/api/chat-v2/status/{int(assistant_message_id)}"
            deadline = time.time() + 600.0
            while time.time() < deadline:
                sr = requests.get(status_url, headers=headers, timeout=60)
                if sr.status_code != 200:
                    time.sleep(4.0)
                    continue
                sj = sr.json()
                st = (sj.get("status") or "").strip().lower()
                if st == "completed":
                    content = sj.get("content") or ""
                    break
                if st == "failed":
                    err = sj.get("error_message") or sj.get("postprocess_error_message") or "Reading failed."
                    if (sj.get("content") or "").strip():
                        content = sj.get("content")
                    break
                time.sleep(4.0)
        except requests.RequestException:
            logger.exception(
                "whatsapp chat: HTTP to internal API failed (set WHATSAPP_INTERNAL_API_URL / PORT). base=%r ask=%s",
                base,
                ask_url,
            )
            send_whatsapp_text(
                to_wa_id=wa_id,
                body=(
                    "This server could not reach its own chat API (often wrong port or missing "
                    "WHATSAPP_INTERNAL_API_URL). Ask the admin to point that env var at this API's base URL "
                    "(same host and port the app listens on). You can use the AstroRoshni app for chat meanwhile."
                )[:4090],
                phone_number_id=phone_number_id,
            )
            return

        if content and str(content).strip():
            sent_any = False
            for part in chunk_text_for_whatsapp(str(content)):
                ok = send_whatsapp_text(to_wa_id=wa_id, body=part, phone_number_id=phone_number_id)
                if ok:
                    sent_any = True
                if not ok:
                    logger.warning("whatsapp chat chunk send failed mid-stream wa_id=%s", wa_id)
                    break
                time.sleep(0.35)
            if sent_any and balance_before is not None:
                try:
                    balance_after = credit_service.get_user_credits(userid)
                    charged = balance_before - balance_after
                    if charged > 0:
                        credit_line = (
                            f"Credits charged: {charged}. Your balance now: {balance_after} credits."
                        )
                    elif charged == 0:
                        credit_line = (
                            "No credits charged for this Standard reading "
                            "(for example a free first question on this chart). "
                            f"Credits balance: {balance_after}."
                        )
                    else:
                        credit_line = (
                            f"Credits balance: {balance_after}. "
                            "Your balance changed during this reading — open the AstroRoshni app for a full statement."
                        )
                    time.sleep(0.45)
                    send_whatsapp_text(
                        to_wa_id=wa_id,
                        body=credit_line[:4090],
                        phone_number_id=phone_number_id,
                    )
                except Exception:
                    logger.exception("whatsapp chat: credit summary failed user=%s", userid)
            return

        send_whatsapp_text(
            to_wa_id=wa_id,
            body=err or "Your reading is taking longer than expected. Check the AstroRoshni app for the full answer, or try asking again.",
            phone_number_id=phone_number_id,
        )
    finally:
        lock.release()
