"""Database helpers for nudge engine: tables and user resolution."""
import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple

from db import get_conn as _get_app_conn, execute

logger = logging.getLogger(__name__)

try:
    from encryption_utils import EncryptionManager

    _nudge_encryptor = EncryptionManager()
except (ValueError, ImportError) as e:
    _nudge_encryptor = None
    logger.debug("Nudge birth-chart decrypt disabled: %s", e)


def get_conn():
    """Return a Postgres connection to the main app database (context-managed)."""
    return _get_app_conn()


def _seed_nudge_trigger_definitions(conn) -> None:
    """Insert default rows for configurable triggers (no-op if already present)."""
    try:
        from .trigger_defaults import DEFAULT_SPECS
    except ImportError:
        return
    for spec in DEFAULT_SPECS:
        try:
            cfg = json.dumps(spec.default_config, ensure_ascii=False, sort_keys=True)
            execute(
                conn,
                """
                INSERT INTO nudge_trigger_definitions
                    (trigger_key, enabled, priority, title_template, body_template,
                     question_template, config_json)
                VALUES (%s, TRUE, NULL, %s, %s, %s, %s)
                ON CONFLICT (trigger_key) DO NOTHING
                """,
                (
                    spec.trigger_key,
                    spec.title_template,
                    spec.body_template,
                    spec.question_template,
                    cfg,
                ),
            )
        except Exception as e:
            logger.warning("Seed nudge_trigger_definitions %s: %s", spec.trigger_key, e)


def init_nudge_tables(conn) -> None:
    """Create device_tokens and nudge_deliveries if they do not exist."""
    # Important:
    # Postgres marks the whole transaction as aborted if any statement fails.
    # This nudge init runs during mobile app flows, so we must not let a
    # single DDL failure poison the connection and break later inserts.
    #
    # Running DDL in autocommit isolates each statement so one failure
    # cannot cause "InFailedSqlTransaction" for the next statement.
    prev_autocommit = getattr(conn, "autocommit", False)
    try:
        conn.autocommit = True

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

        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_trigger_definitions (
                trigger_key TEXT PRIMARY KEY,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                priority INTEGER,
                title_template TEXT NOT NULL,
                body_template TEXT NOT NULL,
                question_template TEXT NOT NULL,
                config_json TEXT NOT NULL DEFAULT '{}',
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER
            )
            """,
        )
        _seed_nudge_trigger_definitions(conn)
    except Exception as e:
        # With autocommit enabled, the exception raised here should be the
        # real failing statement error (not a follow-on InFailedSqlTransaction).
        logger.exception("Failed to init nudge tables: %s", e)
        raise
    finally:
        try:
            conn.autocommit = prev_autocommit
        except Exception:
            pass


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
    """Return userids with at least one delivery on target_date."""
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


def get_delivery_fingerprints_on_date(
    conn, target_date: date
) -> Set[Tuple[int, str, str]]:
    """
    (userid, trigger_id, title) for rows already stored on target_date.
    Used to skip duplicates if the scan runs more than once the same day.
    """
    try:
        cur = execute(
            conn,
            """
            SELECT userid, trigger_id, title
            FROM nudge_deliveries
            WHERE sent_at = %s
            """,
            (target_date.isoformat(),),
        )
        rows = cur.fetchall()
        return {(int(r[0]), str(r[1]), str(r[2])) for r in rows} if rows else set()
    except Exception as e:
        logger.warning("Could not fetch delivery fingerprints for %s: %s", target_date, e)
        return set()


def get_planet_window_dedupe_keys(
    conn, trigger_id: str, since_date: date
) -> Set[Tuple[int, str, str]]:
    """
    (userid, planet, window_start_iso) already notified for this trigger
    since since_date (dedupe across days). Expects event_params JSON with planet + window_start.
    """
    keys: Set[Tuple[int, str, str]] = set()
    try:
        cur = execute(
            conn,
            """
            SELECT userid, event_params
            FROM nudge_deliveries
            WHERE trigger_id = %s AND sent_at >= %s
            """,
            (trigger_id, since_date.isoformat()),
        )
        rows = cur.fetchall() or []
        for userid, raw in rows:
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            planet = obj.get("planet")
            ws = obj.get("window_start")
            if planet and ws:
                keys.add((int(userid), str(planet), str(ws)))
    except Exception as e:
        logger.warning("Could not load dedupe keys for %s: %s", trigger_id, e)
    return keys


def get_vimshottari_dasha_dedupe_keys(
    conn, since_date: date
) -> Set[Tuple[int, str, str]]:
    """
    (userid, level, change_start_iso) for vimshottari_dasha_change since since_date.
    """
    keys: Set[Tuple[int, str, str]] = set()
    try:
        cur = execute(
            conn,
            """
            SELECT userid, event_params
            FROM nudge_deliveries
            WHERE trigger_id = %s AND sent_at >= %s
            """,
            ("vimshottari_dasha_change", since_date.isoformat()),
        )
        rows = cur.fetchall() or []
        for userid, raw in rows:
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            level = obj.get("level")
            cs = obj.get("change_start")
            if level and cs:
                keys.add((int(userid), str(level), str(cs)))
    except Exception as e:
        logger.warning("Could not load vimshottari dasha dedupe keys: %s", e)
    return keys


def get_self_charts_for_nudge(conn) -> List[Dict[str, Any]]:
    """
    One row per user: self birth chart for personalized nudges.
    Returns dicts: birth_chart_id, userid, date, time, latitude, longitude, timezone.
    """
    rows: List[Any] = []
    try:
        cur = execute(
            conn,
            """
            SELECT id, userid, date, time, latitude, longitude, timezone
            FROM birth_charts
            WHERE LOWER(COALESCE(relation, '')) = 'self'
            ORDER BY userid ASC, id ASC
            """,
        )
        rows = cur.fetchall() or []
    except Exception as e:
        logger.warning("Could not load self charts for nudges: %s", e)
        return []

    out: List[Dict[str, Any]] = []
    enc = _nudge_encryptor
    seen_users: Set[int] = set()
    for row in rows:
        cid, uid, d, t, lat, lon, tz = row
        uid = int(uid)
        if uid in seen_users:
            continue
        try:
            if enc:
                d = enc.decrypt(d) if d else ""
                t = enc.decrypt(t) if t else ""
                lat_s = enc.decrypt(str(lat)) if lat is not None else "0"
                lon_s = enc.decrypt(str(lon)) if lon is not None else "0"
                lat_f = float(lat_s) if lat_s else 0.0
                lon_f = float(lon_s) if lon_s else 0.0
            else:
                lat_f = float(lat) if lat is not None else 0.0
                lon_f = float(lon) if lon is not None else 0.0
            out.append(
                {
                    "birth_chart_id": int(cid),
                    "userid": uid,
                    "date": (d or "").strip(),
                    "time": (t or "").strip(),
                    "latitude": lat_f,
                    "longitude": lon_f,
                    "timezone": (tz or "").strip() or "UTC+0",
                }
            )
            seen_users.add(uid)
        except (TypeError, ValueError) as e:
            logger.debug("Skip birth chart %s for nudge: %s", cid, e)
            continue
    return out


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


def fetch_trigger_definition_row(
    conn, trigger_key: str
) -> Optional[Tuple[Any, ...]]:
    try:
        cur = execute(
            conn,
            """
            SELECT enabled, priority, title_template, body_template,
                   question_template, config_json
            FROM nudge_trigger_definitions
            WHERE trigger_key = %s
            """,
            (trigger_key,),
        )
        row = cur.fetchone()
        return row if row else None
    except Exception as e:
        logger.warning("fetch_trigger_definition_row %s: %s", trigger_key, e)
        return None


def upsert_trigger_definition(
    conn,
    trigger_key: str,
    enabled: bool,
    priority: Optional[int],
    title_template: str,
    body_template: str,
    question_template: str,
    config_json: str,
    updated_by: Optional[int],
) -> None:
    execute(
        conn,
        """
        INSERT INTO nudge_trigger_definitions
            (trigger_key, enabled, priority, title_template, body_template,
             question_template, config_json, updated_at, updated_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
        ON CONFLICT (trigger_key) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            priority = EXCLUDED.priority,
            title_template = EXCLUDED.title_template,
            body_template = EXCLUDED.body_template,
            question_template = EXCLUDED.question_template,
            config_json = EXCLUDED.config_json,
            updated_at = CURRENT_TIMESTAMP,
            updated_by = EXCLUDED.updated_by
        """,
        (
            trigger_key,
            enabled,
            priority,
            title_template,
            body_template,
            question_template,
            config_json,
            updated_by,
        ),
    )
