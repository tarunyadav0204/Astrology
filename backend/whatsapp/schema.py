"""Idempotent DDL for WhatsApp onboarding + sessions."""
from __future__ import annotations

import logging
import threading

from db import get_conn, execute

logger = logging.getLogger(__name__)

_SCHEMA_READY = False
_SCHEMA_LOCK = threading.Lock()
_DDL_LOCK_TIMEOUT = "3s"


def _column_exists(conn, table: str, column: str) -> bool:
    cur = execute(
        conn,
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND column_name = %s
        LIMIT 1
        """,
        (table, column),
    )
    return bool(cur.fetchone())


def _table_exists(conn, table: str) -> bool:
    cur = execute(
        conn,
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = %s
        LIMIT 1
        """,
        (table,),
    )
    return bool(cur.fetchone())


def _safe_ddl(conn, sql: str) -> None:
    """Run DDL with a short lock wait so we never block API traffic for minutes."""
    try:
        execute(conn, f"SET LOCAL lock_timeout = '{_DDL_LOCK_TIMEOUT}'")
        execute(conn, sql)
        conn.commit()
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        msg = str(exc or "")
        if "lock timeout" in msg.lower() or "canceling statement due to lock timeout" in msg.lower():
            logger.warning("WhatsApp DDL skipped due to lock timeout: %s", sql.strip().splitlines()[0][:80])
            return
        raise


def ensure_whatsapp_schema() -> None:
    """Idempotent schema ensure — intended for API startup, not request handlers."""
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        with get_conn() as conn:
            # If column + table already exist, skip ALTER on users entirely.
            if _column_exists(conn, "users", "whatsapp_wa_id") and _table_exists(conn, "whatsapp_sessions"):
                # Still ensure newer session columns without touching users.
                _ensure_session_columns(conn)
                conn.commit()
                _SCHEMA_READY = True
                logger.debug("whatsapp schema already present")
                return

            _safe_ddl(
                conn,
                """
                ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_wa_id TEXT
                """,
            )
            _safe_ddl(
                conn,
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_users_whatsapp_wa_id
                ON users (whatsapp_wa_id)
                WHERE whatsapp_wa_id IS NOT NULL AND whatsapp_wa_id <> ''
                """,
            )
            _safe_ddl(
                conn,
                """
                CREATE TABLE IF NOT EXISTS whatsapp_sessions (
                    wa_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL DEFAULT 'idle',
                    userid INTEGER REFERENCES users(userid) ON DELETE SET NULL,
                    reg_phone TEXT,
                    reg_otp_token TEXT,
                    reg_name TEXT,
                    pending_charts_json TEXT,
                    active_chart_id INTEGER,
                    last_phone_number_id TEXT,
                    pending_flow_token TEXT,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            _ensure_session_columns(conn)
            try:
                conn.commit()
            except Exception:
                pass
            if not (
                _column_exists(conn, "users", "whatsapp_wa_id")
                and _table_exists(conn, "whatsapp_sessions")
            ):
                logger.warning("whatsapp schema not fully ready; will retry on next call")
                return
        _SCHEMA_READY = True
        logger.debug("whatsapp schema ensured")


def _ensure_session_columns(conn) -> None:
    for sql in (
        """
        ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS pending_flow_token TEXT
        """,
        """
        ALTER TABLE whatsapp_sessions
        ADD COLUMN IF NOT EXISTS idle_soft_intro_done BOOLEAN NOT NULL DEFAULT FALSE
        """,
        """
        ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS whatsapp_chat_session_id TEXT
        """,
        """
        ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS whatsapp_chat_session_chart_id INTEGER
        """,
        """
        ALTER TABLE whatsapp_sessions
        ADD COLUMN IF NOT EXISTS tara_disclaimer_accepted BOOLEAN NOT NULL DEFAULT FALSE
        """,
        """
        ALTER TABLE whatsapp_sessions
        ADD COLUMN IF NOT EXISTS tara_disclaimer_accepted_on DATE
        """,
        """
        ALTER TABLE whatsapp_sessions
        ADD COLUMN IF NOT EXISTS pending_disclaimer_question TEXT
        """,
    ):
        _safe_ddl(conn, sql)
