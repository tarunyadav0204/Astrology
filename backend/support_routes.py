"""
Authenticated support tickets: users create threads; admins respond via AdminPanel.
All user text is sanitized (plain text, length caps, control-char strip).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import get_conn, execute
from utils.support_text import sanitize_support_body, sanitize_support_subject

logger = logging.getLogger(__name__)

router = APIRouter(tags=["support"])

VALID_STATUSES = frozenset({"open", "pending_user", "resolved", "closed"})
USER_SOURCES = frozenset({"web", "ios", "android"})

_TICKETS_TABLE_READY = False


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
    conn.commit()
    _TICKETS_TABLE_READY = True


def _preview(text: str, n: int = 120) -> str:
    t = (text or "").replace("\n", " ").strip()
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


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


@router.post("/tickets")
async def create_ticket(body: CreateTicketBody, current_user: User = Depends(get_current_user)):
    subject = sanitize_support_subject(body.subject)
    message = sanitize_support_body(body.message)
    if not subject or not message:
        raise HTTPException(status_code=400, detail="Subject and message are required")
    src = (body.source or "web").strip().lower()
    if src not in USER_SOURCES:
        src = "web"

    with get_conn() as conn:
        _ensure_tables(conn)
        _rate_limit_new_tickets(conn, current_user.userid)
        cur = execute(
            conn,
            """
            INSERT INTO support_tickets (userid, subject, status, source, last_message_preview, updated_at)
            VALUES (%s, %s, 'open', %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (current_user.userid, subject, src, _preview(message)),
        )
        tid = cur.fetchone()[0]
        execute(
            conn,
            """
            INSERT INTO support_messages (ticket_id, author_role, author_userid, body)
            VALUES (%s, 'user', %s, %s)
            """,
            (tid, current_user.userid, message),
        )
        conn.commit()
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
    messages_out = [
        {
            "id": m[0],
            "author_role": m[1],
            "author_userid": m[2],
            "body": m[3],
            "created_at": m[4].isoformat() if m[4] else None,
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
    message = sanitize_support_body(body.message)
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    with get_conn() as conn:
        _ensure_tables(conn)
        _rate_limit_user_messages(conn, current_user.userid)
        cur = execute(
            conn,
            "SELECT id, userid, status FROM support_tickets WHERE id = %s",
            (ticket_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if row[1] != current_user.userid:
            raise HTTPException(status_code=403, detail="Access denied")
        status = row[2]
        if status == "closed":
            raise HTTPException(status_code=400, detail="Ticket is closed. Open a new ticket if needed.")

        new_status = "open"
        if status == "resolved":
            new_status = "open"

        execute(
            conn,
            """
            INSERT INTO support_messages (ticket_id, author_role, author_userid, body)
            VALUES (%s, 'user', %s, %s)
            """,
            (ticket_id, current_user.userid, message),
        )
        execute(
            conn,
            """
            UPDATE support_tickets
            SET status = %s,
                updated_at = CURRENT_TIMESTAMP,
                last_message_preview = %s
            WHERE id = %s
            """,
            (new_status, _preview(message), ticket_id),
        )
        conn.commit()
    return {"message": "Sent"}


# --- Admin ---

admin_router = APIRouter(prefix="/admin/support", tags=["support_admin"])


@admin_router.get("/tickets")
async def admin_list_tickets(
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search subject"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(_require_admin),
):
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
            ORDER BY st.updated_at DESC
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
    return {"tickets": tickets, "total": int(total)}


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
            }
            for m in msgs
        ],
    }


@admin_router.post("/tickets/{ticket_id}/messages")
async def admin_post_message(
    ticket_id: int, body: AdminReplyBody, current_user: User = Depends(_require_admin)
):
    message = sanitize_support_body(body.message)
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    owner_userid: int
    with get_conn() as conn:
        _ensure_tables(conn)
        cur = execute(
            conn,
            "SELECT id, userid FROM support_tickets WHERE id = %s",
            (ticket_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        owner_userid = int(row[1])
        execute(
            conn,
            """
            INSERT INTO support_messages (ticket_id, author_role, author_userid, body)
            VALUES (%s, 'admin', %s, %s)
            """,
            (ticket_id, current_user.userid, message),
        )
        execute(
            conn,
            """
            UPDATE support_tickets
            SET status = 'pending_user',
                updated_at = CURRENT_TIMESTAMP,
                last_message_preview = %s
            WHERE id = %s
            """,
            (_preview(message), ticket_id),
        )
        conn.commit()

    _notify_ticket_owner_support_reply(owner_userid, ticket_id, _preview(message))
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
