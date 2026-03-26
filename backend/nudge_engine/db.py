"""Database helpers for nudge engine: tables and user resolution."""
import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple

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
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMPTZ,
                data_json TEXT
            )
            """,
        )
        execute(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_deliveries_user_sent "
            "ON nudge_deliveries(userid, sent_at)",
        )
        # Use IF NOT EXISTS so we never abort the transaction on duplicate column (Postgres 11+).
        # Swallowing ALTER errors with except pass leaves the connection in InFailedSqlTransaction.
        execute(
            conn,
            "ALTER TABLE nudge_deliveries ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ",
        )
        execute(
            conn,
            "ALTER TABLE nudge_deliveries ADD COLUMN IF NOT EXISTS data_json TEXT",
        )
        execute(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_deliveries_user_unread "
            "ON nudge_deliveries(userid) WHERE read_at IS NULL",
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
    data_payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Insert one row into nudge_deliveries (in-app inbox + audit)."""
    data_json = ""
    if data_payload:
        try:
            data_json = json.dumps(data_payload, ensure_ascii=False)[:8000]
        except Exception:
            data_json = ""
    try:
        execute(
            conn,
            """
            INSERT INTO nudge_deliveries
            (userid, trigger_id, title, body, event_params, sent_at, channel, data_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''))
            """,
            (userid, trigger_id, title, body, event_params or "", sent_at.isoformat(), channel, data_json or None),
        )
    except Exception as e:
        logger.exception("Failed to insert nudge delivery for user %s: %s", userid, e)
        raise


def list_deliveries_for_user(
    conn, userid: int, limit: int = 50, offset: int = 0
) -> List[Tuple]:
    """Rows: id, trigger_id, title, body, event_params, data_json_raw, sent_at, channel, created_at, read_at."""
    lim = max(1, min(100, int(limit)))
    off = max(0, int(offset))
    cur = execute(
        conn,
        """
        SELECT id, trigger_id, title, body, event_params, data_json, sent_at::text, channel,
               created_at, read_at
        FROM nudge_deliveries
        WHERE userid = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (userid, lim, off),
    )
    return list(cur.fetchall() or [])


def count_unread_deliveries(conn, userid: int) -> int:
    cur = execute(
        conn,
        """
        SELECT COUNT(*) FROM nudge_deliveries
        WHERE userid = %s AND read_at IS NULL
        """,
        (userid,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def mark_deliveries_read(conn, userid: int, ids: Optional[List[int]]) -> int:
    """Mark specific ids read, or all for user if ids is None or empty."""
    if ids:
        clean = [int(x) for x in ids if isinstance(x, int) or (isinstance(x, str) and str(x).isdigit())]
        if not clean:
            return 0
        placeholders = ",".join(["%s"] * len(clean))
        cur = execute(
            conn,
            f"""
            UPDATE nudge_deliveries
            SET read_at = CURRENT_TIMESTAMP
            WHERE userid = %s AND read_at IS NULL AND id IN ({placeholders})
            """,
            (userid, *clean),
        )
        return cur.rowcount or 0
    cur = execute(
        conn,
        """
        UPDATE nudge_deliveries
        SET read_at = CURRENT_TIMESTAMP
        WHERE userid = %s AND read_at IS NULL
        """,
        (userid,),
    )
    return cur.rowcount or 0
