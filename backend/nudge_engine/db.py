"""Database helpers for nudge engine: tables and user resolution."""
import logging
import sqlite3
from datetime import date
from typing import List, Set, Tuple

from .config import DB_PATH

logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    """Return a connection to the main app database."""
    return sqlite3.connect(DB_PATH)


def init_nudge_tables(conn: sqlite3.Connection) -> None:
    """Create device_tokens and nudge_deliveries if they do not exist."""
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS device_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                token TEXT NOT NULL,
                platform TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(userid, platform)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nudge_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                trigger_id TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                event_params TEXT,
                sent_at DATE NOT NULL,
                channel TEXT DEFAULT 'stored',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_nudge_deliveries_user_sent "
            "ON nudge_deliveries(userid, sent_at)"
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.exception("Failed to init nudge tables: %s", e)
        raise


def get_all_user_ids(conn: sqlite3.Connection) -> List[int]:
    """Return all userids from the users table. Used to expand global events."""
    try:
        cur = conn.execute("SELECT userid FROM users")
        rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []
    except sqlite3.Error as e:
        logger.warning("Could not fetch user ids: %s", e)
        return []


def get_user_ids_receiving_nudge_on_date(
    conn: sqlite3.Connection, target_date: date
) -> Set[int]:
    """Return set of userids who already received a nudge on target_date (for cap)."""
    try:
        cur = conn.execute(
            "SELECT DISTINCT userid FROM nudge_deliveries WHERE sent_at = ?",
            (target_date.isoformat(),),
        )
        rows = cur.fetchall()
        return {r[0] for r in rows} if rows else set()
    except sqlite3.Error as e:
        logger.warning("Could not fetch deliveries for date %s: %s", target_date, e)
        return set()


def get_device_tokens_for_user(conn: sqlite3.Connection, userid: int) -> List[Tuple[str, str]]:
    """Return list of (token, platform) for the user. Empty if none."""
    try:
        cur = conn.execute(
            "SELECT token, platform FROM device_tokens WHERE userid = ?",
            (userid,),
        )
        rows = cur.fetchall()
        return list(rows) if rows else []
    except sqlite3.Error as e:
        logger.warning("Could not fetch device tokens for user %s: %s", userid, e)
        return []


def save_device_token(
    conn: sqlite3.Connection, userid: int, token: str, platform: str
) -> None:
    """Upsert device token for user (one row per platform)."""
    try:
        conn.execute(
            """
            INSERT INTO device_tokens (userid, token, platform, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(userid, platform) DO UPDATE SET
                token = excluded.token,
                updated_at = CURRENT_TIMESTAMP
            """,
            (userid, token.strip(), platform.strip().lower()[:20]),
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.exception("Failed to save device token for user %s: %s", userid, e)
        raise


def insert_delivery(
    conn: sqlite3.Connection,
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
        conn.execute(
            """
            INSERT INTO nudge_deliveries
            (userid, trigger_id, title, body, event_params, sent_at, channel)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (userid, trigger_id, title, body, event_params or "", sent_at.isoformat(), channel),
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.exception("Failed to insert nudge delivery for user %s: %s", userid, e)
        raise
