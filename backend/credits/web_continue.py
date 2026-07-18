"""Reusable WhatsApp → PWA web-continue tokens (land on Credits already signed in)."""
from __future__ import annotations

import logging
import os
import secrets
from typing import Any, Dict, Optional, Tuple

from db import execute, get_conn

logger = logging.getLogger(__name__)

TOKEN_BYTES = 24  # url-safe ~32 chars


def _public_mobile_base() -> str:
    base = (
        os.environ.get("PUBLIC_WEB_BASE_URL")
        or os.environ.get("PUBLIC_MOBILE_WEB_BASE_URL")
        or "https://astroroshni.com"
    ).strip().rstrip("/")
    if base.endswith("/mobile"):
        return base
    return f"{base}/mobile"


def ensure_web_continue_tokens_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS web_continue_tokens (
            token TEXT PRIMARY KEY,
            userid INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            revoked_at TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_web_continue_tokens_userid_active
        ON web_continue_tokens (userid)
        WHERE revoked_at IS NULL
        """,
    )


def get_or_create_continue_token(userid: int) -> str:
    """Return the user's active reusable continue token (create once, reuse forever until revoked)."""
    uid = int(userid)
    with get_conn() as conn:
        ensure_web_continue_tokens_table(conn)
        cur = execute(
            conn,
            """
            SELECT token FROM web_continue_tokens
            WHERE userid = ? AND revoked_at IS NULL
            LIMIT 1
            """,
            (uid,),
        )
        row = cur.fetchone()
        if row and str(row[0] or "").strip():
            return str(row[0]).strip()
        raw = secrets.token_urlsafe(TOKEN_BYTES)
        try:
            execute(
                conn,
                """
                INSERT INTO web_continue_tokens (token, userid, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (raw, uid),
            )
            conn.commit()
            return raw
        except Exception:
            conn.rollback()
            cur = execute(
                conn,
                """
                SELECT token FROM web_continue_tokens
                WHERE userid = ? AND revoked_at IS NULL
                LIMIT 1
                """,
                (uid,),
            )
            row = cur.fetchone()
            if row and str(row[0] or "").strip():
                return str(row[0]).strip()
            raise


def revoke_continue_tokens(userid: int) -> None:
    with get_conn() as conn:
        ensure_web_continue_tokens_table(conn)
        execute(
            conn,
            """
            UPDATE web_continue_tokens
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE userid = ? AND revoked_at IS NULL
            """,
            (int(userid),),
        )
        conn.commit()


def rotate_continue_token(userid: int) -> str:
    """Invalidate prior links and mint a new reusable token."""
    revoke_continue_tokens(userid)
    return get_or_create_continue_token(userid)


def build_continue_url(raw_token: str) -> str:
    tok = (raw_token or "").strip()
    return f"{_public_mobile_base()}/c/{tok}"


def resolve_continue_token(raw_token: str) -> Optional[Dict[str, Any]]:
    """Validate reusable token and return user fields. Does not burn the token."""
    raw = (raw_token or "").strip()
    if not raw or len(raw) > 200:
        return None
    with get_conn() as conn:
        ensure_web_continue_tokens_table(conn)
        cur = execute(
            conn,
            """
            SELECT t.userid, u.phone, u.name, u.role, u.email, u.signup_client
            FROM web_continue_tokens t
            JOIN users u ON u.userid = t.userid
            WHERE t.token = ?
              AND t.revoked_at IS NULL
            """,
            (raw,),
        )
        row = cur.fetchone()
        if not row:
            return None
        execute(
            conn,
            """
            UPDATE web_continue_tokens
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE token = ?
            """,
            (raw,),
        )
        conn.commit()
        return {
            "userid": int(row[0]),
            "phone": str(row[1] or "").strip(),
            "name": str(row[2] or "").strip() or "there",
            "role": str(row[3] or "user"),
            "email": row[4],
            "signup_client": row[5],
        }


def lookup_user_for_web_topup(
    *,
    userid: Optional[int] = None,
    phone: Optional[str] = None,
) -> Optional[Tuple[int, str, str]]:
    """Return (userid, phone, name) for admin link / WhatsApp send."""
    with get_conn() as conn:
        if userid is not None:
            cur = execute(
                conn,
                """
                SELECT userid, COALESCE(phone, ''), COALESCE(NULLIF(TRIM(name), ''), 'there')
                FROM users WHERE userid = ?
                """,
                (int(userid),),
            )
            row = cur.fetchone()
            if row:
                return int(row[0]), str(row[1] or "").strip(), str(row[2] or "there")
        p = (phone or "").strip()
        if p:
            digits = "".join(ch for ch in p if ch.isdigit())
            variants = [p, p.lstrip("+"), digits, f"+{digits}" if digits else ""]
            variants = [v for v in dict.fromkeys(variants) if v]
            for v in variants:
                cur = execute(
                    conn,
                    """
                    SELECT userid, COALESCE(phone, ''), COALESCE(NULLIF(TRIM(name), ''), 'there')
                    FROM users WHERE phone = ?
                    LIMIT 1
                    """,
                    (v,),
                )
                row = cur.fetchone()
                if row:
                    return int(row[0]), str(row[1] or "").strip(), str(row[2] or "there")
    return None
