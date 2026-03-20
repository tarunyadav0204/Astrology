"""Database helpers for nudge engine: tables and user resolution."""
import logging
from datetime import date
from typing import List, Set, Tuple

from db import get_conn as _get_app_conn, execute

logger = logging.getLogger(__name__)


def get_conn():
    """Return a Postgres connection to the main app database (context-managed)."""
    return _get_app_conn()


def init_nudge_tables(conn) -> None:
    """Create device_tokens and nudge_deliveries if they do not exist."""
    try:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS device_tokens (
                id SERIAL PRIMARY KEY,
                userid INTEGER NOT NULL,
                token TEXT NOT NULL,
                platform TEXT NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(userid, platform)
            )
            """,
        )
        # Ensure ON CONFLICT(userid, platform) works even if the table was
        # created earlier without the unique constraint (common after partial migrations).
        execute(
            conn,
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_device_tokens_userid_platform ON device_tokens(userid, platform)",
        )
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_deliveries (
                id SERIAL PRIMARY KEY,
                userid INTEGER NOT NULL,
                trigger_id TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                event_params TEXT,
                sent_at DATE NOT NULL,
                channel TEXT DEFAULT 'stored',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        execute(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_deliveries_user_sent "
            "ON nudge_deliveries(userid, sent_at)",
        )
        # DDL statements are transactional in Postgres; ensure persistence
        # because our connection context manager closes without auto-commit.
        try:
            conn.commit()
        except Exception:
            # If the connection/driver is already in autocommit mode, commit is harmless.
            pass
    except Exception as e:
        logger.exception("Failed to init nudge tables: %s", e)
        raise


def get_all_user_ids(conn) -> List[int]:
    """Return all userids from the users table. Used to expand global events."""
    try:
        cur = execute(conn, "SELECT userid FROM users")
        rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []
    except Exception as e:
        logger.warning("Could not fetch user ids: %s", e)
        return []


def get_user_ids_receiving_nudge_on_date(
    conn, target_date: date
) -> Set[int]:
    """Return set of userids who already received a nudge on target_date (for cap)."""
    try:
        cur = execute(
            conn,
            "SELECT DISTINCT userid FROM nudge_deliveries WHERE sent_at = %s",
            (target_date.isoformat(),),
        )
        rows = cur.fetchall()
        return {r[0] for r in rows} if rows else set()
    except Exception as e:
        logger.warning("Could not fetch deliveries for date %s: %s", target_date, e)
        return set()


def get_device_tokens_for_user(conn, userid: int) -> List[Tuple[str, str]]:
    """Return list of (token, platform) for the user. Empty if none."""
    try:
        cur = execute(
            conn,
            "SELECT token, platform FROM device_tokens WHERE userid = %s",
            (userid,),
        )
        rows = cur.fetchall()
        return list(rows) if rows else []
    except Exception as e:
        logger.warning("Could not fetch device tokens for user %s: %s", userid, e)
        return []


def get_all_device_tokens(conn) -> List[Tuple[int, str, str]]:
    """
    Return list of (userid, token, platform) for all users who have a device token.
    Used by admin blog notifications to broadcast or target multiple users.
    """
    try:
        cur = execute(
            conn,
            "SELECT userid, token, platform FROM device_tokens",
        )
        rows = cur.fetchall()
        return list(rows) if rows else []
    except Exception as e:
        logger.warning("Could not fetch all device tokens: %s", e)
        return []


def save_device_token(
    conn, userid: int, token: str, platform: str
) -> None:
    """Upsert device token for user (one row per platform)."""
    try:
        execute(
            conn,
            """
            INSERT INTO device_tokens (userid, token, platform, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT(userid, platform) DO UPDATE SET
                token = EXCLUDED.token,
                updated_at = CURRENT_TIMESTAMP
            """,
            (userid, token.strip(), platform.strip().lower()[:20]),
        )
    except Exception as e:
        logger.exception("Failed to save device token for user %s: %s", userid, e)
        raise


def insert_delivery(
    conn,
    userid: int,
    trigger_id: str,
    title: str,
    body: str,
    sent_at: date,
    event_params: str = "",
    channel: str = "stored",
) -> None:
    """Insert one row into nudge_deliveries."""
    try:
        execute(
            conn,
            """
            INSERT INTO nudge_deliveries
            (userid, trigger_id, title, body, event_params, sent_at, channel)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (userid, trigger_id, title, body, event_params or "", sent_at.isoformat(), channel),
        )
    except Exception as e:
        logger.exception("Failed to insert nudge delivery for user %s: %s", userid, e)
        raise
