"""Idempotent DDL for WhatsApp onboarding + sessions."""
from __future__ import annotations

import logging

from db import get_conn, execute

logger = logging.getLogger(__name__)


def ensure_whatsapp_schema() -> None:
    with get_conn() as conn:
        execute(
            conn,
            """
            ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_wa_id TEXT
            """,
        )
        execute(
            conn,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_users_whatsapp_wa_id
            ON users (whatsapp_wa_id)
            WHERE whatsapp_wa_id IS NOT NULL AND whatsapp_wa_id <> ''
            """,
        )
        execute(
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
        execute(
            conn,
            """
            ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS pending_flow_token TEXT
            """,
        )
        execute(
            conn,
            """
            ALTER TABLE whatsapp_sessions
            ADD COLUMN IF NOT EXISTS idle_soft_intro_done BOOLEAN NOT NULL DEFAULT FALSE
            """,
        )
        execute(
            conn,
            """
            ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS whatsapp_chat_session_id TEXT
            """,
        )
        execute(
            conn,
            """
            ALTER TABLE whatsapp_sessions ADD COLUMN IF NOT EXISTS whatsapp_chat_session_chart_id INTEGER
            """,
        )
        execute(
            conn,
            """
            ALTER TABLE whatsapp_sessions
            ADD COLUMN IF NOT EXISTS tara_disclaimer_accepted BOOLEAN NOT NULL DEFAULT FALSE
            """,
        )
        execute(
            conn,
            """
            ALTER TABLE whatsapp_sessions
            ADD COLUMN IF NOT EXISTS tara_disclaimer_accepted_on DATE
            """,
        )
        execute(
            conn,
            """
            ALTER TABLE whatsapp_sessions
            ADD COLUMN IF NOT EXISTS pending_disclaimer_question TEXT
            """,
        )
        conn.commit()
    logger.debug("whatsapp schema ensured")
