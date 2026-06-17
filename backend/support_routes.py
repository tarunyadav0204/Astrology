"""
Authenticated support tickets: users create threads; admins respond via AdminPanel.
All user text is sanitized (plain text, length caps, control-char strip).
"""
from __future__ import annotations

import logging
import os
import secrets
from datetime import date
from pathlib import Path
from typing import Any, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import get_conn, execute
from utils.support_text import sanitize_support_body, sanitize_support_subject
from utils.smtp_mail import send_plain_text_email

logger = logging.getLogger(__name__)

# Inbox for new tickets and user replies (override via env).
SUPPORT_HELP_EMAIL = (os.getenv("SUPPORT_HELP_EMAIL") or "help@astroroshni.com").strip()
# Link shown in emails to the ticket owner (Contact / support UI on web).
PUBLIC_WEB_BASE_URL = (os.getenv("PUBLIC_WEB_BASE_URL") or "https://astroroshni.com").rstrip("/")

router = APIRouter(tags=["support"])

VALID_STATUSES = frozenset({"open", "pending_user", "resolved", "closed"})
USER_SOURCES = frozenset({"web", "ios", "android", "whatsapp"})

_TICKETS_TABLE_READY = False
SUPPORT_ATTACHMENT_DIR = Path(os.getenv("SUPPORT_ATTACHMENT_DIR") or Path(__file__).resolve().parent / "storage" / "support_attachments")
SUPPORT_ATTACHMENT_MAX_BYTES = int(os.getenv("SUPPORT_ATTACHMENT_MAX_BYTES") or str(15 * 1024 * 1024))


def _ensure_tables(conn) -> None:
    global _TICKETS_TABLE_READY
    if _TICKETS_TABLE_READY:
        return
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
            subject TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            source TEXT NOT NULL DEFAULT 'web',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_message_preview TEXT
        )
        """,
    )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS support_messages (
            id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
            author_role TEXT NOT NULL,
            author_userid INTEGER,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_support_tickets_user_updated
        ON support_tickets (userid, updated_at DESC)
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_support_tickets_status
        ON support_tickets (status, updated_at DESC)
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_support_messages_ticket
        ON support_messages (ticket_id, created_at)
        """,
    )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS support_message_attachments (
            id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
            message_id INTEGER NOT NULL REFERENCES support_messages(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            size_bytes BIGINT NOT NULL DEFAULT 0,
            uploaded_by_role TEXT NOT NULL,
            uploaded_by_userid INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_support_attachments_ticket_message
        ON support_message_attachments (ticket_id, message_id, created_at)
        """,
    )
    SUPPORT_ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
    conn.commit()
    _TICKETS_TABLE_READY = True


def _preview(text: str, n: int = 120) -> str:
    t = (text or "").replace("\n", " ").strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


def _email_clip(text: str, max_len: int = 8000) -> str:
    t = text or ""
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _safe_email_subject(s: str, max_len: int = 200) -> str:
    line = " ".join((s or "").splitlines()).strip()
    if len(line) > max_len:
        return line[: max_len - 1] + "…"
    return line or "(no subject)"


def _fetch_user_contact(conn, userid: int) -> Tuple[Optional[str], str, str]:
    cur = execute(conn, "SELECT email, name, phone FROM users WHERE userid = %s", (userid,))
    row = cur.fetchone()
    if not row:
        return None, "", ""
    raw_email = (row[0] or "").strip()
    email = raw_email if raw_email else None
    name = (row[1] or "").strip()
    phone = (row[2] or "").strip()
    return email, name, phone


def _notify_help_staff_new_ticket(
    ticket_id: int,
    subject: str,
    userid: int,
    user_name: str,
    user_phone: str,
    user_email: Optional[str],
    source: str,
    message: str,
) -> None:
    if not SUPPORT_HELP_EMAIL:
        return
    subj = _safe_email_subject(f"[Support #{ticket_id}] New ticket: {subject}")
    lines = [
        f"New support ticket #{ticket_id}",
        "",
        f"Subject: {subject}",
        f"User ID: {userid}",
        f"Name: {user_name or '—'}",
        f"Phone: {user_phone or '—'}",
        f"Account email (users.email): {user_email or '(not set)'}",
        f"Source: {source}",
        "",
        "Message:",
        _email_clip(message),
    ]
    body = "\n".join(lines)
    try:
        ok = send_plain_text_email(SUPPORT_HELP_EMAIL, subj, body)
        if not ok:
            logger.warning("Help desk email not sent (SMTP) for new ticket %s", ticket_id)
    except Exception:
        logger.exception("Help desk email failed for new ticket %s", ticket_id)


def _notify_help_staff_user_reply(
    ticket_id: int,
    subject: str,
    userid: int,
    user_name: str,
    user_phone: str,
    user_email: Optional[str],
    message: str,
) -> None:
    if not SUPPORT_HELP_EMAIL:
        return
    subj = _safe_email_subject(f"[Support #{ticket_id}] User replied: {subject}")
    lines = [
        f"User replied on ticket #{ticket_id}",
        "",
        f"Subject: {subject}",
        f"User ID: {userid}",
        f"Name: {user_name or '—'}",
        f"Phone: {user_phone or '—'}",
        f"Account email (users.email): {user_email or '(not set)'}",
        "",
        "Message:",
        _email_clip(message),
    ]
    body = "\n".join(lines)
    try:
        ok = send_plain_text_email(SUPPORT_HELP_EMAIL, subj, body)
        if not ok:
            logger.warning("Help desk email not sent (SMTP) for user reply ticket %s", ticket_id)
    except Exception:
        logger.exception("Help desk email failed for user reply ticket %s", ticket_id)


def _notify_ticket_owner_email(
    to_email: Optional[str],
    ticket_id: int,
    subject: str,
    headline: str,
    message_body: str,
) -> None:
    if not to_email:
        logger.info("Ticket owner has no email; skipping notification email for ticket %s", ticket_id)
        return
    subj = _safe_email_subject(f"AstroRoshni support — {subject}")
    support_url = f"{PUBLIC_WEB_BASE_URL}/contact"
    lines = [
        headline,
        "",
        f"Ticket #{ticket_id}: {subject}",
        "",
        "Message:",
        _email_clip(message_body, max_len=6000),
        "",
        f"Open the app or visit {support_url} to view the full thread and reply.",
        "",
        "— AstroRoshni",
    ]
    body = "\n".join(lines)
    try:
        ok = send_plain_text_email(to_email, subj, body)
        if not ok:
            logger.warning("User notification email not sent (SMTP) for ticket %s", ticket_id)
    except Exception:
        logger.exception("User notification email failed for ticket %s", ticket_id)


def _notify_ticket_owner_support_reply(owner_userid: int, ticket_id: int, reply_preview: str) -> None:
    """
    Best-effort Expo push + nudge_deliveries row so the user can tap to open the ticket in-app.
    Does not raise; logs failures.
    """
    try:
        from nudge_engine import db as nudge_db
        from nudge_engine import push as push_module
    except Exception as e:
        logger.warning("Support reply notify: nudge modules not available: %s", e)
        return

    title = "Support replied"
    body = (reply_preview or "").strip().replace("\n", " ")
    if len(body) > 180:
        body = body[:179] + "…"
    if not body:
        body = "You have a new message from support."

    push_data = {
        "trigger_id": "support_reply",
        "cta": "astroroshni://support",
        "support_ticket_id": str(int(ticket_id)),
    }

    try:
        with get_conn() as conn:
            nudge_db.init_nudge_tables(conn)
            tokens = nudge_db.get_device_tokens_for_user(conn, owner_userid)
            sent = 0
            for token, _platform in tokens:
                if push_module.send_expo_push(
                    token,
                    title[:100],
                    body[:200],
                    data=push_data,
                ):
                    sent += 1
                    break
            channel = "push" if sent > 0 else "stored"
            nudge_db.insert_delivery(
                conn,
                userid=owner_userid,
                trigger_id="support_reply",
                title=title[:100],
                body=body[:200],
                sent_at=date.today(),
                event_params="{}",
                channel=channel,
                data_payload=push_data,
            )
            conn.commit()
    except Exception as e:
        logger.exception("Support reply notify failed for user %s ticket %s: %s", owner_userid, ticket_id, e)


def _notify_ticket_owner_whatsapp(owner_userid: int, ticket_id: int, reply_preview: str) -> None:
    try:
        from whatsapp.messaging import send_whatsapp_text

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT u.whatsapp_wa_id, ws.last_phone_number_id
                FROM users u
                LEFT JOIN whatsapp_sessions ws ON ws.wa_id = u.whatsapp_wa_id
                WHERE u.userid = %s
                """,
                (owner_userid,),
            )
            row = cur.fetchone()
        if not row or not row[0] or not row[1]:
            return
        preview = (reply_preview or "Support replied to your ticket.").strip().replace("\n", " ")
        if len(preview) > 800:
            preview = preview[:797] + "..."
        send_whatsapp_text(
            to_wa_id=str(row[0]),
            phone_number_id=str(row[1]),
            body=(
                f"Support replied to ticket #{ticket_id}:\n"
                f"{preview}\n\n"
                "To reply here, open *Menu* > *Support* > *My tickets*."
            ),
        )
    except Exception:
        logger.exception("Support WhatsApp notify failed for user %s ticket %s", owner_userid, ticket_id)


def _sanitize_attachment_filename(name: str) -> str:
    raw = os.path.basename((name or "").strip()) or "attachment.pdf"
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in raw).strip()
    if not safe.lower().endswith(".pdf"):
        safe = f"{safe}.pdf"
    return safe[:180] or "attachment.pdf"


def _attachment_download_path(attachment_id: int) -> str:
    return f"{PUBLIC_WEB_BASE_URL}/api/support/attachments/{attachment_id}/download"


async def _store_pdf_attachment(upload: UploadFile) -> Tuple[str, str, int]:
    filename = _sanitize_attachment_filename(upload.filename or "attachment.pdf")
    mime_type = (upload.content_type or "").strip().lower()
    if mime_type and mime_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=400, detail="Only PDF attachments are allowed.")
    blob = await upload.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Attachment is empty.")
    if len(blob) > SUPPORT_ATTACHMENT_MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"PDF is too large. Max allowed size is {SUPPORT_ATTACHMENT_MAX_BYTES // (1024 * 1024)} MB.",
        )
    if not blob.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Only valid PDF files are allowed.")

    ext = ".pdf"
    stored_name = f"{secrets.token_hex(16)}{ext}"
    stored_path = SUPPORT_ATTACHMENT_DIR / stored_name
    stored_path.write_bytes(blob)
    return filename, str(stored_path), len(blob)


def _fetch_ticket_attachment_rows(conn, ticket_id: int) -> dict:
    cur = execute(
        conn,
        """
        SELECT id, message_id, filename, mime_type, size_bytes, uploaded_by_role, uploaded_by_userid, created_at
        FROM support_message_attachments
        WHERE ticket_id = %s
        ORDER BY created_at ASC, id ASC
        """,
        (ticket_id,),
    )
    rows = cur.fetchall() or []
    out = {}
    for r in rows:
        msg_id = int(r[1])
        out.setdefault(msg_id, []).append(
            {
                "id": r[0],
                "filename": r[2],
                "mime_type": r[3],
                "size_bytes": int(r[4] or 0),
                "uploaded_by_role": r[5],
                "uploaded_by_userid": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
                "download_url": _attachment_download_path(int(r[0])),
            }
        )
    return out


def _rate_limit_new_tickets(conn, userid: int, max_per_hour: int = 5) -> None:
    cur = execute(
        conn,
        """
        SELECT COUNT(*) FROM support_tickets
        WHERE userid = %s AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
        """,
        (userid,),
    )
    row = cur.fetchone()
    if row and row[0] and int(row[0]) >= max_per_hour:
        raise HTTPException(
            status_code=429,
            detail="Too many new tickets. Please wait before submitting another.",
        )


def _rate_limit_user_messages(conn, userid: int, max_per_hour: int = 40) -> None:
    cur = execute(
        conn,
        """
        SELECT COUNT(*) FROM support_messages sm
        JOIN support_tickets st ON st.id = sm.ticket_id
        WHERE st.userid = %s AND sm.author_role = 'user'
          AND sm.created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
        """,
        (userid,),
    )
    row = cur.fetchone()
    if row and row[0] and int(row[0]) >= max_per_hour:
        raise HTTPException(
            status_code=429,
            detail="Too many messages. Please try again later.",
        )


class CreateTicketBody(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=1, max_length=12000)
    source: str = Field(default="web", max_length=20)


class PostMessageBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=12000)


class AdminReplyBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=12000)


class AdminStatusBody(BaseModel):
    status: str = Field(..., min_length=1, max_length=32)


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def create_support_ticket_for_user(userid: int, subject: str, message: str, source: str = "web") -> int:
    subject = sanitize_support_subject(subject)
    message = sanitize_support_body(message)
    if not subject or not message:
        raise HTTPException(status_code=400, detail="Subject and message are required")
    src = (source or "web").strip().lower()
    if src not in USER_SOURCES:
        src = "web"

    with get_conn() as conn:
        _ensure_tables(conn)
        _rate_limit_new_tickets(conn, userid)
        cur = execute(
            conn,
            """
            INSERT INTO support_tickets (userid, subject, status, source, last_message_preview, updated_at)
            VALUES (%s, %s, 'open', %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (userid, subject, src, _preview(message)),
        )
        tid = int(cur.fetchone()[0])
        execute(
            conn,
            """
            INSERT INTO support_messages (ticket_id, author_role, author_userid, body)
            VALUES (%s, 'user', %s, %s)
            """,
            (tid, userid, message),
        )
        u_email, u_name, u_phone = _fetch_user_contact(conn, userid)
        conn.commit()

    _notify_help_staff_new_ticket(tid, subject, userid, u_name, u_phone, u_email, src, message)
    return tid


def post_support_message_for_user(userid: int, ticket_id: int, message: str) -> None:
    message = sanitize_support_body(message)
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    with get_conn() as conn:
        _ensure_tables(conn)
        _rate_limit_user_messages(conn, userid)
        cur = execute(
            conn,
            "SELECT id, userid, status FROM support_tickets WHERE id = %s",
            (ticket_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if row[1] != userid:
            raise HTTPException(status_code=403, detail="Access denied")
        status = row[2]
        if status == "closed":
            raise HTTPException(status_code=400, detail="Ticket is closed. Open a new ticket if needed.")

        execute(
            conn,
            """
            INSERT INTO support_messages (ticket_id, author_role, author_userid, body)
            VALUES (%s, 'user', %s, %s)
            """,
            (ticket_id, userid, message),
        )
        execute(
            conn,
            """
            UPDATE support_tickets
            SET status = 'open',
                updated_at = CURRENT_TIMESTAMP,
                last_message_preview = %s
            WHERE id = %s
            """,
            (_preview(message), ticket_id),
        )
        cur_sub = execute(conn, "SELECT subject FROM support_tickets WHERE id = %s", (ticket_id,))
        sub_row = cur_sub.fetchone()
        ticket_subject = (sub_row[0] if sub_row else "") or ""
        u_email, u_name, u_phone = _fetch_user_contact(conn, userid)
        conn.commit()

    _notify_help_staff_user_reply(ticket_id, ticket_subject, userid, u_name, u_phone, u_email, message)


@router.post("/tickets")
async def create_ticket(body: CreateTicketBody, current_user: User = Depends(get_current_user)):
    tid = create_support_ticket_for_user(current_user.userid, body.subject, body.message, body.source)
    return {"ticket_id": tid, "message": "Ticket created"}


@router.get("/tickets")
async def list_my_tickets(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    with get_conn() as conn:
        _ensure_tables(conn)
        cur = execute(
            conn,
            """
            SELECT id, subject, status, source, created_at, updated_at, last_message_preview
            FROM support_tickets
            WHERE userid = %s
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (current_user.userid, limit),
        )
        rows = cur.fetchall() or []
    out = []
    for r in rows:
        out.append(
            {
                "id": r[0],
                "subject": r[1],
                "status": r[2],
                "source": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
                "updated_at": r[5].isoformat() if r[5] else None,
                "last_message_preview": r[6],
            }
        )
    return {"tickets": out}


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(ticket_id: int, current_user: User = Depends(get_current_user)):
    with get_conn() as conn:
        _ensure_tables(conn)
        cur = execute(
            conn,
            """
            SELECT id, userid, subject, status, source, created_at, updated_at
            FROM support_tickets WHERE id = %s
            """,
            (ticket_id,),
        )
        t = cur.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if t[1] != current_user.userid:
            raise HTTPException(status_code=403, detail="Access denied")
        cur2 = execute(
            conn,
            """
            SELECT id, author_role, author_userid, body, created_at
            FROM support_messages
            WHERE ticket_id = %s
            ORDER BY created_at ASC
            """,
            (ticket_id,),
        )
        msgs = cur2.fetchall() or []
        attachment_map = _fetch_ticket_attachment_rows(conn, ticket_id)
    messages_out = [
        {
            "id": m[0],
            "author_role": m[1],
            "author_userid": m[2],
            "body": m[3],
            "created_at": m[4].isoformat() if m[4] else None,
            "attachments": attachment_map.get(int(m[0]), []),
        }
        for m in msgs
    ]
    return {
        "ticket": {
            "id": t[0],
            "subject": t[2],
            "status": t[3],
            "source": t[4],
            "created_at": t[5].isoformat() if t[5] else None,
            "updated_at": t[6].isoformat() if t[6] else None,
        },
        "messages": messages_out,
    }


@router.post("/tickets/{ticket_id}/messages")
async def post_user_message(
    ticket_id: int, body: PostMessageBody, current_user: User = Depends(get_current_user)
):
    post_support_message_for_user(current_user.userid, ticket_id, body.message)
    return {"message": "Sent"}


@router.get("/attachments/{attachment_id}/download")
async def download_support_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
):
    with get_conn() as conn:
        _ensure_tables(conn)
        cur = execute(
            conn,
            """
            SELECT
                sma.id,
                sma.filename,
                sma.mime_type,
                sma.storage_path,
                st.userid
            FROM support_message_attachments sma
            INNER JOIN support_tickets st ON st.id = sma.ticket_id
            WHERE sma.id = %s
            """,
            (attachment_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Attachment not found")
        owner_userid = int(row[4])
        if current_user.role != "admin" and owner_userid != current_user.userid:
            raise HTTPException(status_code=403, detail="Access denied")

    file_path = Path(row[3])
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file missing")

    return FileResponse(
        path=str(file_path),
        media_type=row[2] or "application/pdf",
        filename=row[1] or "attachment.pdf",
    )


# --- Admin ---

admin_router = APIRouter(prefix="/admin/support", tags=["support_admin"])


@admin_router.get("/tickets")
async def admin_list_tickets(
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search subject"),
    sort_by: str = Query(
        "updated_at",
        description="Sort order: updated_at (last activity) or created_at (newest ticket first)",
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(_require_admin),
):
    sort_col = (sort_by or "updated_at").strip().lower()
    if sort_col not in ("updated_at", "created_at"):
        raise HTTPException(status_code=400, detail="sort_by must be updated_at or created_at")

    with get_conn() as conn:
        _ensure_tables(conn)
        where = ["1=1"]
        params: List[Any] = []
        if status and status in VALID_STATUSES:
            where.append("st.status = %s")
            params.append(status)
        if q and q.strip():
            where.append("st.subject ILIKE %s")
            params.append(f"%{q.strip()[:100]}%")
        w = " AND ".join(where)
        cur = execute(
            conn,
            f"""
            SELECT st.id, st.userid, st.subject, st.status, st.source, st.created_at, st.updated_at,
                   st.last_message_preview, u.phone, u.name, u.email
            FROM support_tickets st
            LEFT JOIN users u ON u.userid = st.userid
            WHERE {w}
            ORDER BY st.{sort_col} DESC
            LIMIT %s OFFSET %s
            """,
            tuple(params) + (limit, offset),
        )
        rows = cur.fetchall() or []
        curc = execute(
            conn,
            f"SELECT COUNT(*) FROM support_tickets st WHERE {w}",
            tuple(params),
        )
        total = curc.fetchone()[0]

    tickets = []
    for r in rows:
        tickets.append(
            {
                "id": r[0],
                "userid": r[1],
                "subject": r[2],
                "status": r[3],
                "source": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
                "updated_at": r[6].isoformat() if r[6] else None,
                "last_message_preview": r[7],
                "user_phone": r[8] or "",
                "user_name": r[9] or "",
                "user_email": (r[10] or "").strip(),
            }
        )
    return {"tickets": tickets, "total": int(total), "sort_by": sort_col}


@admin_router.get("/tickets/{ticket_id}")
async def admin_get_ticket(ticket_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        _ensure_tables(conn)
        cur = execute(
            conn,
            """
            SELECT st.id, st.userid, st.subject, st.status, st.source, st.created_at, st.updated_at,
                   u.phone, u.name, u.email
            FROM support_tickets st
            LEFT JOIN users u ON u.userid = st.userid
            WHERE st.id = %s
            """,
            (ticket_id,),
        )
        t = cur.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        cur2 = execute(
            conn,
            """
            SELECT id, author_role, author_userid, body, created_at
            FROM support_messages WHERE ticket_id = %s ORDER BY created_at ASC
            """,
            (ticket_id,),
        )
        msgs = cur2.fetchall() or []
        attachment_map = _fetch_ticket_attachment_rows(conn, ticket_id)
    return {
        "ticket": {
            "id": t[0],
            "userid": t[1],
            "subject": t[2],
            "status": t[3],
            "source": t[4],
            "created_at": t[5].isoformat() if t[5] else None,
            "updated_at": t[6].isoformat() if t[6] else None,
            "user_phone": t[7] or "",
            "user_name": t[8] or "",
            "user_email": (t[9] or "").strip(),
        },
        "messages": [
            {
                "id": m[0],
                "author_role": m[1],
                "author_userid": m[2],
                "body": m[3],
                "created_at": m[4].isoformat() if m[4] else None,
                "attachments": attachment_map.get(int(m[0]), []),
            }
            for m in msgs
        ],
    }


@admin_router.post("/tickets/{ticket_id}/messages")
async def admin_post_message(
    ticket_id: int, request: Request, current_user: User = Depends(_require_admin)
):
    content_type = (request.headers.get("content-type") or "").lower()
    upload: Optional[UploadFile] = None
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        message = sanitize_support_body(str(form.get("message") or ""))
        maybe_upload = form.get("attachment")
        if maybe_upload is not None and hasattr(maybe_upload, "filename") and hasattr(maybe_upload, "read"):
            upload = maybe_upload
    else:
        payload = AdminReplyBody(**(await request.json()))
        message = sanitize_support_body(payload.message)

    if not message and upload is None:
        raise HTTPException(status_code=400, detail="Reply message or PDF attachment is required.")

    owner_userid: int
    owner_email: Optional[str] = None
    ticket_subject = ""
    stored_filename: Optional[str] = None
    stored_path: Optional[str] = None
    stored_size = 0
    if upload is not None:
        stored_filename, stored_path, stored_size = await _store_pdf_attachment(upload)
    with get_conn() as conn:
        _ensure_tables(conn)
        cur = execute(
            conn,
            """
                SELECT st.id, st.userid, st.subject, st.source, u.email
                FROM support_tickets st
                LEFT JOIN users u ON u.userid = st.userid
                WHERE st.id = %s
            """,
            (ticket_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        owner_userid = int(row[1])
        ticket_subject = (row[2] or "").strip()
        ticket_source = (row[3] or "").strip().lower()
        raw_em = (row[4] or "").strip()
        owner_email = raw_em if raw_em else None
        message_body = message or ""
        insert_cur = execute(
            conn,
            """
            INSERT INTO support_messages (ticket_id, author_role, author_userid, body)
            VALUES (%s, 'admin', %s, %s)
            RETURNING id
            """,
            (ticket_id, current_user.userid, message_body),
        )
        inserted = insert_cur.fetchone()
        if not inserted:
            raise HTTPException(status_code=500, detail="Failed to save support reply")
        message_id = int(inserted[0])
        if stored_filename and stored_path:
            execute(
                conn,
                """
                INSERT INTO support_message_attachments (
                    ticket_id, message_id, filename, mime_type, storage_path, size_bytes,
                    uploaded_by_role, uploaded_by_userid
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'admin', %s)
                """,
                (
                    ticket_id,
                    message_id,
                    stored_filename,
                    "application/pdf",
                    stored_path,
                    stored_size,
                    current_user.userid,
                ),
            )
        preview_text = message or (f"PDF attached: {stored_filename}" if stored_filename else "")
        execute(
            conn,
            """
            UPDATE support_tickets
            SET status = 'pending_user',
                updated_at = CURRENT_TIMESTAMP,
                last_message_preview = %s
            WHERE id = %s
            """,
            (_preview(preview_text), ticket_id),
        )
        conn.commit()

    push_preview = message or (f"Support attached {stored_filename}" if stored_filename else "Support replied")
    email_body = message or "Support has attached a PDF to your ticket."
    if stored_filename:
        email_body = f"{email_body}\n\nAttached PDF: {stored_filename}"

    _notify_ticket_owner_support_reply(owner_userid, ticket_id, _preview(push_preview))
    if ticket_source == "whatsapp":
        _notify_ticket_owner_whatsapp(owner_userid, ticket_id, _preview(push_preview))
    _notify_ticket_owner_email(
        owner_email,
        ticket_id,
        ticket_subject,
        "Support has replied to your ticket.",
        email_body,
    )
    return {"message": "Reply sent"}


@admin_router.patch("/tickets/{ticket_id}")
async def admin_patch_ticket(
    ticket_id: int, body: AdminStatusBody, current_user: User = Depends(_require_admin)
):
    st = (body.status or "").strip().lower()
    if st not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    with get_conn() as conn:
        _ensure_tables(conn)
        cur = execute(
            conn,
            "UPDATE support_tickets SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id",
            (st, ticket_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Ticket not found")
        conn.commit()
    return {"message": "Updated", "status": st}
