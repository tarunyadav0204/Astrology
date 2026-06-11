"""Database helpers for nudge engine: tables and user resolution."""
import json
import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Set, Tuple

from db import get_conn as _get_app_conn, execute, executemany
from .default_broadcast_nudges import DEFAULT_BROADCAST_NUDGES, DEFAULT_DAILY_SLOTS

logger = logging.getLogger(__name__)
IST_TZ = ZoneInfo("Asia/Kolkata")

try:
    from encryption_utils import EncryptionManager

    _nudge_encryptor = EncryptionManager()
except (ValueError, ImportError) as e:
    _nudge_encryptor = None
    logger.debug("Nudge birth-chart decrypt disabled: %s", e)


def get_conn():
    """Return a Postgres connection to the main app database (context-managed)."""
    return _get_app_conn()


def try_advisory_lock(conn, lock_name: str) -> bool:
    """Acquire a Postgres advisory lock for a cron job if it is not already running."""
    cur = execute(conn, "SELECT pg_try_advisory_lock(hashtext(%s))", (str(lock_name),))
    row = cur.fetchone()
    return bool(row and row[0])


def try_advisory_xact_lock(conn, lock_name: str) -> bool:
    """Acquire a transaction-scoped advisory lock; it auto-releases on commit/rollback."""
    cur = execute(conn, "SELECT pg_try_advisory_xact_lock(hashtext(%s))", (str(lock_name),))
    row = cur.fetchone()
    return bool(row and row[0])


def advisory_unlock(conn, lock_name: str) -> None:
    """Release a Postgres advisory lock acquired with try_advisory_lock."""
    try:
        execute(conn, "SELECT pg_advisory_unlock(hashtext(%s))", (str(lock_name),))
    except Exception as e:
        logger.warning("Could not release advisory lock %s: %s", lock_name, e)


def _safe_execute_nudge_ddl(conn, sql: str) -> None:
    try:
        execute(conn, sql)
    except Exception as exc:
        msg = str(exc or "")
        if "must be owner of table" in msg:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.warning("Skipping nudge DDL due to table ownership: %s", msg)
            return
        raise


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


def _seed_broadcast_templates(conn) -> None:
    """Seed static nudges used by admin broadcast scheduler (once)."""
    try:
        cur = execute(conn, "SELECT COUNT(*) FROM nudge_broadcast_templates")
        row = cur.fetchone()
        if row and int(row[0]) > 0:
            return
    except Exception:
        return

    for idx, item in enumerate(DEFAULT_BROADCAST_NUDGES, start=1):
        try:
            execute(
                conn,
                """
                INSERT INTO nudge_broadcast_templates(title, body, category, is_active, sort_order)
                VALUES (%s, %s, %s, TRUE, %s)
                """,
                (
                    str(item.get("title") or "").strip()[:200],
                    str(item.get("body") or "").strip()[:600],
                    str(item.get("category") or "general").strip()[:80],
                    idx,
                ),
            )
        except Exception as e:
            logger.warning("Seed nudge_broadcast_templates %s failed: %s", item.get("title"), e)


def _seed_default_broadcast_schedule(conn, days: int = 30) -> None:
    """
    On a fresh system start, pre-create a 30-day schedule with 4 nudges/day
    at 07:00, 13:00, 17:00, 20:00 in rotating order.
    """
    try:
        cur = execute(conn, "SELECT COUNT(*) FROM nudge_broadcast_schedule")
        row = cur.fetchone()
        if row and int(row[0]) > 0:
            return
    except Exception:
        return

    try:
        cur = execute(
            conn,
            """
            SELECT id
            FROM nudge_broadcast_templates
            WHERE is_active = TRUE
            ORDER BY sort_order ASC, id ASC
            """,
        )
        template_ids = [int(r[0]) for r in (cur.fetchall() or [])]
    except Exception:
        template_ids = []

    if not template_ids:
        return

    today = date.today()
    try:
        # Keep default schedule anchored to IST dates regardless of server timezone.
        from datetime import datetime
        today = datetime.now(IST_TZ).date()
    except Exception:
        # Fall back to server-local date if timezone data is unavailable.
        pass
    cursor = 0
    for d in range(max(1, int(days))):
        target_day = today + timedelta(days=d)
        for slot in DEFAULT_DAILY_SLOTS:
            template_id = template_ids[cursor % len(template_ids)]
            cursor += 1
            try:
                execute(
                    conn,
                    """
                    INSERT INTO nudge_broadcast_schedule(template_id, send_date, send_time, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    """,
                    (template_id, target_day.isoformat(), slot),
                )
            except Exception as e:
                logger.warning(
                    "Seed nudge_broadcast_schedule %s %s failed: %s",
                    target_day,
                    slot,
                    e,
                )


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

        _safe_execute_nudge_ddl(
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
        # Multi-channel campaign columns:
        # - campaign_id: nudge_campaigns.id when sent by a campaign
        # - delivery_group_id: one logical nudge that may produce several channel rows
        # - send_status: 'sent' | 'failed' | 'stored' (legacy rows have NULL = sent)
        # - is_primary: the single row per group shown in the in-app inbox
        # - clicked_at: email/CTA tracking-link click time
        for _ddl in (
            "ALTER TABLE nudge_deliveries ADD COLUMN IF NOT EXISTS campaign_id INTEGER",
            "ALTER TABLE nudge_deliveries ADD COLUMN IF NOT EXISTS delivery_group_id TEXT",
            "ALTER TABLE nudge_deliveries ADD COLUMN IF NOT EXISTS send_status TEXT",
            "ALTER TABLE nudge_deliveries ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT TRUE",
            "ALTER TABLE nudge_deliveries ADD COLUMN IF NOT EXISTS clicked_at TIMESTAMPTZ",
        ):
            _safe_execute_nudge_ddl(conn, _ddl)
        _safe_execute_nudge_ddl(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_deliveries_campaign "
            "ON nudge_deliveries(campaign_id) WHERE campaign_id IS NOT NULL",
        )
        _safe_execute_nudge_ddl(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_deliveries_group "
            "ON nudge_deliveries(delivery_group_id) WHERE delivery_group_id IS NOT NULL",
        )

        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_campaigns (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                title_template TEXT NOT NULL,
                body_template TEXT NOT NULL,
                question_template TEXT,
                channel_policy TEXT NOT NULL DEFAULT 'waterfall',
                channels_json TEXT NOT NULL DEFAULT '["push","whatsapp","email"]',
                ai_personalize BOOLEAN NOT NULL DEFAULT FALSE,
                ai_base_prompt TEXT,
                audience_filter_json TEXT NOT NULL DEFAULT '{"type":"all"}',
                landing_screen TEXT NOT NULL DEFAULT 'chat',
                scheduled_at TIMESTAMPTZ,
                dispatched_at TIMESTAMPTZ,
                total_targeted INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        _safe_execute_nudge_ddl(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_campaigns_status_sched "
            "ON nudge_campaigns(status, scheduled_at)",
        )

        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_conversions (
                id SERIAL PRIMARY KEY,
                delivery_group_id TEXT NOT NULL UNIQUE,
                campaign_id INTEGER,
                userid INTEGER NOT NULL,
                trigger_id TEXT,
                question TEXT,
                converted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                seconds_since_sent INTEGER,
                attribution TEXT NOT NULL DEFAULT 'tap'
            )
            """,
        )
        _safe_execute_nudge_ddl(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_conversions_campaign "
            "ON nudge_conversions(campaign_id) WHERE campaign_id IS NOT NULL",
        )
        _safe_execute_nudge_ddl(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_conversions_converted "
            "ON nudge_conversions(converted_at)",
        )

        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_admin_send_jobs (
                job_id TEXT PRIMARY KEY,
                admin_userid INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                audience TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                total_users INTEGER NOT NULL DEFAULT 0,
                tokens_found INTEGER NOT NULL DEFAULT 0,
                sent INTEGER NOT NULL DEFAULT 0,
                failed INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ
            )
            """,
        )
        _safe_execute_nudge_ddl(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_admin_send_jobs_created "
            "ON nudge_admin_send_jobs(created_at DESC)",
        )

        _safe_execute_nudge_ddl(
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
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_broadcast_templates (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_broadcast_schedule (
                id SERIAL PRIMARY KEY,
                template_id INTEGER NOT NULL REFERENCES nudge_broadcast_templates(id) ON DELETE CASCADE,
                send_date DATE NOT NULL,
                send_time TIME NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                dispatched_at TIMESTAMPTZ,
                dispatched_count INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        execute(
            conn,
            "ALTER TABLE nudge_broadcast_schedule ADD COLUMN IF NOT EXISTS dispatched_at TIMESTAMPTZ",
        )
        execute(
            conn,
            "ALTER TABLE nudge_broadcast_schedule ADD COLUMN IF NOT EXISTS dispatched_count INTEGER NOT NULL DEFAULT 0",
        )
        execute(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_broadcast_schedule_date_time "
            "ON nudge_broadcast_schedule(send_date, send_time)",
        )
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS nudge_cron_runs (
                id SERIAL PRIMARY KEY,
                job_key TEXT NOT NULL,
                status TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        execute(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_nudge_cron_runs_job_created ON nudge_cron_runs(job_key, created_at DESC)",
        )
        _seed_nudge_trigger_definitions(conn)
        _seed_broadcast_templates(conn)
        _seed_default_broadcast_schedule(conn)
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


def get_user_ids_after(conn, *, after_userid: int = 0, limit: int = 500) -> List[int]:
    """Return a stable userid page for fan-out workers."""
    lim = max(1, min(int(limit), 5000))
    cur = execute(
        conn,
        """
        SELECT userid
        FROM users
        WHERE userid > %s
        ORDER BY userid ASC
        LIMIT %s
        """,
        (int(after_userid or 0), lim),
    )
    return [int(r[0]) for r in (cur.fetchall() or [])]


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


def get_device_tokens_for_users(conn, userids: List[int]) -> List[Tuple[int, str, str]]:
    """Return (userid, token, platform) for the provided user ids."""
    ids = [int(u) for u in userids if str(u).isdigit()]
    if not ids:
        return []
    try:
        cur = execute(
            conn,
            "SELECT userid, token, platform FROM device_tokens WHERE userid = ANY(%s)",
            (ids,),
        )
        rows = cur.fetchall()
        return list(rows) if rows else []
    except Exception as e:
        logger.warning("Could not fetch device tokens for users: %s", e)
        return []


def resolve_notification_recipient_user_ids(
    conn,
    *,
    name: Optional[str] = None,
    require_device_token: bool = True,
    limit: int = 100000,
) -> List[int]:
    """Resolve admin bulk-notification recipients across all pages."""
    params: List[Any] = []
    where: List[str] = []
    join = ""
    if require_device_token:
        join = "JOIN (SELECT DISTINCT userid FROM device_tokens) dt ON dt.userid = u.userid"
    if name and str(name).strip():
        pat = f"%{str(name).strip()}%"
        where.append("(u.name ILIKE %s OR COALESCE(u.email, '') ILIKE %s OR COALESCE(u.phone::text, '') ILIKE %s)")
        params.extend([pat, pat, pat])
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    try:
        cur = execute(
            conn,
            f"""
            SELECT DISTINCT u.userid
            FROM users u
            {join}
            {where_sql}
            ORDER BY u.userid ASC
            LIMIT %s
            """,
            tuple(params + [int(limit)]),
        )
        rows = cur.fetchall() or []
        return [int(r[0]) for r in rows]
    except Exception as e:
        logger.warning("Could not resolve notification recipient user ids: %s", e)
        return []


def create_admin_send_job(
    conn,
    *,
    job_id: str,
    admin_userid: int,
    audience: str,
    title: str,
    body: str,
) -> None:
    execute(
        conn,
        """
        INSERT INTO nudge_admin_send_jobs
        (job_id, admin_userid, status, audience, title, body)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (job_id, admin_userid, "queued", audience, title, body),
    )


def update_admin_send_job(conn, job_id: str, **fields: Any) -> None:
    allowed = {
        "status",
        "total_users",
        "tokens_found",
        "sent",
        "failed",
        "error",
        "started_at",
        "completed_at",
    }
    updates = []
    params: List[Any] = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        updates.append(f"{key} = %s")
        params.append(value)
    if not updates:
        return
    params.append(job_id)
    execute(
        conn,
        f"UPDATE nudge_admin_send_jobs SET {', '.join(updates)} WHERE job_id = %s",
        tuple(params),
    )


def get_admin_send_job(conn, job_id: str) -> Optional[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT job_id, admin_userid, status, audience, title, body,
               total_users, tokens_found, sent, failed, error,
               created_at, started_at, completed_at
        FROM nudge_admin_send_jobs
        WHERE job_id = %s
        """,
        (job_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    keys = [
        "job_id",
        "admin_userid",
        "status",
        "audience",
        "title",
        "body",
        "total_users",
        "tokens_found",
        "sent",
        "failed",
        "error",
        "created_at",
        "started_at",
        "completed_at",
    ]
    out = dict(zip(keys, row))
    for key in ("created_at", "started_at", "completed_at"):
        if hasattr(out.get(key), "isoformat"):
            out[key] = out[key].isoformat()
    return out


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
    campaign_id: Optional[int] = None,
    delivery_group_id: Optional[str] = None,
    send_status: Optional[str] = None,
    is_primary: bool = True,
) -> Optional[int]:
    """Insert one row into nudge_deliveries (in-app inbox + audit). Returns the row id."""
    data_json = ""
    if data_payload:
        try:
            data_json = json.dumps(data_payload, ensure_ascii=False)[:8000]
        except Exception:
            data_json = ""
    try:
        cur = execute(
            conn,
            """
            INSERT INTO nudge_deliveries
            (userid, trigger_id, title, body, event_params, sent_at, channel, data_json,
             campaign_id, delivery_group_id, send_status, is_primary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''), %s, %s, %s, %s)
            RETURNING id
            """,
            (
                userid, trigger_id, title, body, event_params or "", sent_at.isoformat(),
                channel, data_json or None,
                campaign_id, delivery_group_id, send_status, bool(is_primary),
            ),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None
    except Exception as e:
        logger.exception("Failed to insert nudge delivery for user %s: %s", userid, e)
        raise


def insert_deliveries_batch(
    conn,
    rows: List[Tuple[Any, ...]],
) -> None:
    """
    Bulk insert nudge_deliveries. Each row tuple:
    (userid, trigger_id, title, body, event_params, sent_at_iso, channel, data_json_or_empty)
    optionally followed by (delivery_group_id, send_status).
    """
    if not rows:
        return
    normalized: List[Tuple[Any, ...]] = []
    for row in rows:
        if len(row) == 8:
            normalized.append(tuple(row) + (None, None))
        else:
            normalized.append(tuple(row))
    try:
        executemany(
            conn,
            """
            INSERT INTO nudge_deliveries
            (userid, trigger_id, title, body, event_params, sent_at, channel, data_json,
             delivery_group_id, send_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''), %s, %s)
            """,
            normalized,
        )
    except Exception as e:
        logger.exception("Failed batch insert nudge deliveries (%s rows): %s", len(rows), e)
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
        WHERE userid = %s AND COALESCE(is_primary, TRUE)
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (userid, lim, off),
    )
    return list(cur.fetchall() or [])


def list_deliveries_for_date_admin(
    conn, target_date: str, limit: int = 500
) -> List[Tuple]:
    """
    Admin list for a specific sent_at date.
    Rows: id, userid, user_name, user_phone, trigger_id, title, body, sent_at,
    channel, created_at, read_at, data_json
    """
    lim = max(1, min(2000, int(limit)))
    cur = execute(
        conn,
        """
        SELECT d.id,
               d.userid,
               COALESCE(u.name, '') AS user_name,
               COALESCE(u.phone, '') AS user_phone,
               d.trigger_id,
               d.title,
               d.body,
               d.sent_at::text,
               d.channel,
               d.created_at,
               d.read_at,
               d.data_json
        FROM nudge_deliveries d
        LEFT JOIN users u ON u.userid = d.userid
        WHERE d.sent_at = %s
        ORDER BY d.created_at DESC, d.id DESC
        LIMIT %s
        """,
        (target_date, lim),
    )
    return list(cur.fetchall() or [])


def summarize_deliveries_for_date_admin(conn, target_date: str) -> Dict[str, int]:
    """
    Whole-day channel counts for a sent_at date (unaffected by the list LIMIT).
    whatsapp_template_continued = template recipients who tapped Continue and
    received the personalized nudge (read_at set on consumption).
    """
    cur = execute(
        conn,
        """
        SELECT COUNT(DISTINCT COALESCE(delivery_group_id, id::text)) AS total,
               COUNT(*) FILTER (WHERE channel = 'push' AND COALESCE(send_status, 'sent') = 'sent') AS push,
               COUNT(*) FILTER (WHERE channel = 'whatsapp' AND COALESCE(send_status, 'sent') = 'sent') AS whatsapp,
               COUNT(*) FILTER (WHERE channel = 'whatsapp_template' AND COALESCE(send_status, 'sent') = 'sent') AS whatsapp_template,
               COUNT(*) FILTER (WHERE channel = 'whatsapp_template' AND read_at IS NOT NULL) AS whatsapp_template_continued,
               COUNT(*) FILTER (WHERE channel = 'email' AND COALESCE(send_status, 'sent') = 'sent') AS email,
               COUNT(*) FILTER (WHERE COALESCE(send_status, '') = 'failed') AS failed_attempts,
               COUNT(*) FILTER (WHERE COALESCE(is_primary, TRUE)
                                AND (channel IS NULL OR TRIM(channel) = '' OR channel = 'stored')) AS stored_only
        FROM nudge_deliveries
        WHERE sent_at = %s
        """,
        (target_date,),
    )
    row = cur.fetchone() or (0, 0, 0, 0, 0, 0, 0, 0)
    return {
        "total": int(row[0] or 0),
        "push": int(row[1] or 0),
        "whatsapp": int(row[2] or 0),
        "whatsapp_template": int(row[3] or 0),
        "whatsapp_template_continued": int(row[4] or 0),
        "email": int(row[5] or 0),
        "failed_attempts": int(row[6] or 0),
        "stored_only": int(row[7] or 0),
    }


def count_unread_deliveries(conn, userid: int) -> int:
    cur = execute(
        conn,
        """
        SELECT COUNT(*) FROM nudge_deliveries
        WHERE userid = %s AND read_at IS NULL AND COALESCE(is_primary, TRUE)
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


def list_broadcast_templates(conn) -> List[Tuple]:
    cur = execute(
        conn,
        """
        SELECT id, title, body, category, is_active, sort_order, created_at, updated_at
        FROM nudge_broadcast_templates
        ORDER BY sort_order ASC, id ASC
        """,
    )
    return list(cur.fetchall() or [])


def create_broadcast_template(
    conn,
    title: str,
    body: str,
    category: str = "general",
    is_active: bool = True,
    sort_order: Optional[int] = None,
) -> Optional[int]:
    cur = execute(conn, "SELECT COALESCE(MAX(sort_order), 0) FROM nudge_broadcast_templates")
    row = cur.fetchone()
    next_sort = int(row[0] or 0) + 1
    so = int(sort_order) if sort_order is not None else next_sort
    cur = execute(
        conn,
        """
        INSERT INTO nudge_broadcast_templates(title, body, category, is_active, sort_order, updated_at)
        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        RETURNING id
        """,
        (title, body, category, bool(is_active), so),
    )
    created = cur.fetchone()
    return int(created[0]) if created else None


def list_broadcast_schedule(
    conn, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> List[Tuple]:
    q = [
        """
        SELECT s.id, s.template_id, t.title, t.body, t.category,
               s.send_date::text, s.send_time::text, s.is_active, s.created_by, s.created_at,
               s.dispatched_at, s.dispatched_count
        FROM nudge_broadcast_schedule s
        JOIN nudge_broadcast_templates t ON t.id = s.template_id
        WHERE 1=1
        """
    ]
    params: List[Any] = []
    if start_date:
        q.append(" AND s.send_date >= %s")
        params.append(start_date)
    if end_date:
        q.append(" AND s.send_date <= %s")
        params.append(end_date)
    q.append(" ORDER BY s.send_date ASC, s.send_time ASC, s.id ASC")
    cur = execute(conn, "".join(q), tuple(params))
    return list(cur.fetchall() or [])


def acquire_due_broadcast_schedule(
    conn, today_iso: str, now_hhmm: str, limit: int = 100
) -> List[Tuple]:
    """
    Return due schedule rows and lock them for this transaction.
    Rows remain due until caller marks them dispatched.
    """
    lim = max(1, min(500, int(limit)))
    cur = execute(
        conn,
        """
        SELECT s.id, s.template_id, t.title, t.body, t.category,
               s.send_date::text, s.send_time::text
        FROM nudge_broadcast_schedule s
        JOIN nudge_broadcast_templates t ON t.id = s.template_id
        WHERE s.is_active = TRUE
          AND s.dispatched_at IS NULL
          AND (s.send_date < %s OR (s.send_date = %s AND s.send_time <= %s))
        ORDER BY s.send_date ASC, s.send_time ASC, s.id ASC
        FOR UPDATE OF s SKIP LOCKED
        LIMIT %s
        """,
        (today_iso, today_iso, now_hhmm, lim),
    )
    return list(cur.fetchall() or [])


def mark_broadcast_schedule_dispatched(
    conn, schedule_id: int, dispatched_count: int
) -> int:
    cur = execute(
        conn,
        """
        UPDATE nudge_broadcast_schedule
        SET dispatched_at = CURRENT_TIMESTAMP,
            dispatched_count = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (max(0, int(dispatched_count)), int(schedule_id)),
    )
    return int(cur.rowcount or 0)


def get_broadcast_schedule_item(conn, schedule_id: int) -> Optional[Tuple]:
    """Return one broadcast schedule row with template content."""
    cur = execute(
        conn,
        """
        SELECT s.id, s.template_id, t.title, t.body, t.category,
               s.send_date::text, s.send_time::text, s.is_active,
               s.dispatched_at, s.dispatched_count
        FROM nudge_broadcast_schedule s
        JOIN nudge_broadcast_templates t ON t.id = s.template_id
        WHERE s.id = %s
        """,
        (int(schedule_id),),
    )
    return cur.fetchone()


def get_broadcast_delivery_user_ids(conn, *, schedule_id: int, userids: List[int]) -> Set[int]:
    """Users that already have a delivery row for this broadcast schedule."""
    ids = [int(u) for u in userids if str(u).isdigit()]
    if not ids:
        return set()
    cur = execute(
        conn,
        """
        SELECT userid
        FROM nudge_deliveries
        WHERE trigger_id = 'broadcast_schedule'
          AND userid = ANY(%s)
          AND NULLIF(event_params, '')::jsonb ->> 'schedule_id' = %s
        """,
        (ids, str(int(schedule_id))),
    )
    return {int(r[0]) for r in (cur.fetchall() or [])}


def create_broadcast_schedule_item(
    conn,
    template_id: int,
    send_date: str,
    send_time: str,
    created_by: Optional[int] = None,
    is_active: bool = True,
) -> Optional[int]:
    cur = execute(
        conn,
        """
        INSERT INTO nudge_broadcast_schedule(template_id, send_date, send_time, is_active, created_by)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (template_id, send_date, send_time, bool(is_active), created_by),
    )
    row = cur.fetchone()
    return int(row[0]) if row else None


def delete_broadcast_schedule_item(conn, schedule_id: int) -> int:
    cur = execute(conn, "DELETE FROM nudge_broadcast_schedule WHERE id = %s", (schedule_id,))
    return int(cur.rowcount or 0)


def insert_cron_run(conn, job_key: str, status: str, summary_json: str) -> Optional[int]:
    cur = execute(
        conn,
        """
        INSERT INTO nudge_cron_runs(job_key, status, summary_json)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (str(job_key or "").strip(), str(status or "").strip(), str(summary_json or "{}")),
    )
    row = cur.fetchone()
    return int(row[0]) if row else None


# ---------------------------------------------------------------------------
# Campaigns (multi-channel nudge campaigns defined in the admin UI)
# ---------------------------------------------------------------------------

_CAMPAIGN_COLUMNS = (
    "id", "name", "status", "title_template", "body_template", "question_template",
    "channel_policy", "channels_json", "ai_personalize", "ai_base_prompt",
    "audience_filter_json", "landing_screen", "scheduled_at", "dispatched_at",
    "total_targeted", "created_by", "created_at", "updated_at",
)


def _campaign_row_to_dict(row: Tuple[Any, ...]) -> Dict[str, Any]:
    out = dict(zip(_CAMPAIGN_COLUMNS, row))
    for key in ("scheduled_at", "dispatched_at", "created_at", "updated_at"):
        if hasattr(out.get(key), "isoformat"):
            out[key] = out[key].isoformat()
    try:
        out["channels"] = json.loads(out.get("channels_json") or "[]")
    except Exception:
        out["channels"] = []
    try:
        out["audience_filter"] = json.loads(out.get("audience_filter_json") or "{}")
    except Exception:
        out["audience_filter"] = {}
    out["ai_personalize"] = bool(out.get("ai_personalize"))
    return out


def create_campaign(
    conn,
    *,
    name: str,
    title_template: str,
    body_template: str,
    question_template: str,
    channel_policy: str,
    channels_json: str,
    ai_personalize: bool,
    ai_base_prompt: str,
    audience_filter_json: str,
    landing_screen: str,
    scheduled_at: Optional[Any],
    status: str,
    created_by: Optional[int],
) -> Optional[int]:
    cur = execute(
        conn,
        """
        INSERT INTO nudge_campaigns
            (name, status, title_template, body_template, question_template,
             channel_policy, channels_json, ai_personalize, ai_base_prompt,
             audience_filter_json, landing_screen, scheduled_at, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            name, status, title_template, body_template, question_template or None,
            channel_policy, channels_json, bool(ai_personalize), ai_base_prompt or None,
            audience_filter_json, landing_screen, scheduled_at, created_by,
        ),
    )
    row = cur.fetchone()
    return int(row[0]) if row else None


def update_campaign(conn, campaign_id: int, **fields: Any) -> int:
    allowed = {
        "name", "status", "title_template", "body_template", "question_template",
        "channel_policy", "channels_json", "ai_personalize", "ai_base_prompt",
        "audience_filter_json", "landing_screen", "scheduled_at", "dispatched_at",
        "total_targeted",
    }
    updates = []
    params: List[Any] = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        updates.append(f"{key} = %s")
        params.append(value)
    if not updates:
        return 0
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(int(campaign_id))
    cur = execute(
        conn,
        f"UPDATE nudge_campaigns SET {', '.join(updates)} WHERE id = %s",
        tuple(params),
    )
    return int(cur.rowcount or 0)


def get_campaign(conn, campaign_id: int) -> Optional[Dict[str, Any]]:
    cur = execute(
        conn,
        f"SELECT {', '.join(_CAMPAIGN_COLUMNS)} FROM nudge_campaigns WHERE id = %s",
        (int(campaign_id),),
    )
    row = cur.fetchone()
    return _campaign_row_to_dict(row) if row else None


def list_campaigns(conn, limit: int = 200) -> List[Dict[str, Any]]:
    lim = max(1, min(int(limit), 500))
    cur = execute(
        conn,
        f"""
        SELECT {', '.join(_CAMPAIGN_COLUMNS)}
        FROM nudge_campaigns
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """,
        (lim,),
    )
    return [_campaign_row_to_dict(r) for r in (cur.fetchall() or [])]


def delete_campaign(conn, campaign_id: int) -> int:
    cur = execute(
        conn,
        "DELETE FROM nudge_campaigns WHERE id = %s AND status IN ('draft', 'scheduled', 'cancelled')",
        (int(campaign_id),),
    )
    return int(cur.rowcount or 0)


def acquire_due_campaigns(conn, now_dt: Any, limit: int = 20) -> List[Dict[str, Any]]:
    """Lock and return campaigns due for dispatch (status=scheduled, scheduled_at <= now)."""
    lim = max(1, min(int(limit), 100))
    cur = execute(
        conn,
        f"""
        SELECT {', '.join(_CAMPAIGN_COLUMNS)}
        FROM nudge_campaigns
        WHERE status = 'scheduled'
          AND scheduled_at IS NOT NULL
          AND scheduled_at <= %s
        ORDER BY scheduled_at ASC, id ASC
        FOR UPDATE SKIP LOCKED
        LIMIT %s
        """,
        (now_dt, lim),
    )
    return [_campaign_row_to_dict(r) for r in (cur.fetchall() or [])]


def get_campaign_delivery_user_ids(conn, *, campaign_id: int, userids: List[int]) -> Set[int]:
    """Users who already have a delivery row for this campaign (worker retry dedupe)."""
    ids = [int(u) for u in userids if str(u).isdigit()]
    if not ids:
        return set()
    cur = execute(
        conn,
        """
        SELECT DISTINCT userid
        FROM nudge_deliveries
        WHERE campaign_id = %s AND userid = ANY(%s)
        """,
        (int(campaign_id), ids),
    )
    return {int(r[0]) for r in (cur.fetchall() or [])}


# ---------------------------------------------------------------------------
# Conversions (nudge → user asked a chat question)
# ---------------------------------------------------------------------------

def find_primary_delivery_by_group(conn, delivery_group_id: str) -> Optional[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT id, userid, campaign_id, trigger_id, created_at
        FROM nudge_deliveries
        WHERE delivery_group_id = %s
        ORDER BY (COALESCE(is_primary, TRUE)) DESC, id ASC
        LIMIT 1
        """,
        (str(delivery_group_id).strip(),),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": int(row[0]),
        "userid": int(row[1]),
        "campaign_id": int(row[2]) if row[2] is not None else None,
        "trigger_id": row[3] or "",
        "created_at": row[4],
    }


def insert_conversion(
    conn,
    *,
    delivery_group_id: str,
    campaign_id: Optional[int],
    userid: int,
    trigger_id: str,
    question: str,
    seconds_since_sent: Optional[int],
    attribution: str = "tap",
) -> bool:
    """Record the first chat question attributed to a nudge group. Idempotent per group."""
    cur = execute(
        conn,
        """
        INSERT INTO nudge_conversions
            (delivery_group_id, campaign_id, userid, trigger_id, question,
             seconds_since_sent, attribution)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (delivery_group_id) DO NOTHING
        """,
        (
            str(delivery_group_id).strip(),
            campaign_id,
            int(userid),
            (trigger_id or "")[:120],
            (question or "")[:2000],
            seconds_since_sent,
            (attribution or "tap")[:40],
        ),
    )
    return bool(cur.rowcount)


def mark_delivery_clicked(conn, delivery_group_id: str) -> int:
    cur = execute(
        conn,
        """
        UPDATE nudge_deliveries
        SET clicked_at = COALESCE(clicked_at, CURRENT_TIMESTAMP)
        WHERE delivery_group_id = %s
        """,
        (str(delivery_group_id).strip(),),
    )
    return int(cur.rowcount or 0)


# ---------------------------------------------------------------------------
# Analytics / dashboard aggregates
# ---------------------------------------------------------------------------

_TIME_BUCKETS_SQL = """
    COUNT(*) FILTER (WHERE seconds_since_sent IS NOT NULL AND seconds_since_sent < 300) AS under_5m,
    COUNT(*) FILTER (WHERE seconds_since_sent >= 300 AND seconds_since_sent < 3600) AS under_1h,
    COUNT(*) FILTER (WHERE seconds_since_sent >= 3600 AND seconds_since_sent < 21600) AS under_6h,
    COUNT(*) FILTER (WHERE seconds_since_sent >= 21600 AND seconds_since_sent < 86400) AS under_24h,
    COUNT(*) FILTER (WHERE seconds_since_sent >= 86400) AS over_24h,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY seconds_since_sent) AS median_seconds
"""


def _delivery_channel_counts(conn, where_sql: str, params: Tuple[Any, ...]) -> Dict[str, int]:
    cur = execute(
        conn,
        f"""
        SELECT COUNT(DISTINCT COALESCE(delivery_group_id, id::text)) AS targeted,
               COUNT(*) FILTER (WHERE channel = 'push' AND COALESCE(send_status, 'sent') = 'sent') AS push,
               COUNT(*) FILTER (WHERE channel IN ('whatsapp', 'whatsapp_template') AND COALESCE(send_status, 'sent') = 'sent') AS whatsapp,
               COUNT(*) FILTER (WHERE channel = 'email' AND COALESCE(send_status, 'sent') = 'sent') AS email,
               COUNT(*) FILTER (WHERE COALESCE(send_status, '') = 'failed') AS failed_attempts,
               COUNT(*) FILTER (WHERE COALESCE(is_primary, TRUE)
                                AND (channel IS NULL OR TRIM(channel) = '' OR channel = 'stored')) AS stored_only,
               COUNT(*) FILTER (WHERE clicked_at IS NOT NULL) AS clicked
        FROM nudge_deliveries
        WHERE {where_sql}
        """,
        params,
    )
    row = cur.fetchone() or (0,) * 7
    keys = ("targeted", "push", "whatsapp", "email", "failed_attempts", "stored_only", "clicked")
    return {k: int(v or 0) for k, v in zip(keys, row)}


def _conversion_summary(conn, where_sql: str, params: Tuple[Any, ...]) -> Dict[str, Any]:
    cur = execute(
        conn,
        f"""
        SELECT COUNT(*) AS conversions,
               {_TIME_BUCKETS_SQL}
        FROM nudge_conversions
        WHERE {where_sql}
        """,
        params,
    )
    row = cur.fetchone() or (0, 0, 0, 0, 0, 0, None)
    return {
        "conversions": int(row[0] or 0),
        "time_buckets": {
            "under_5m": int(row[1] or 0),
            "under_1h": int(row[2] or 0),
            "under_6h": int(row[3] or 0),
            "under_24h": int(row[4] or 0),
            "over_24h": int(row[5] or 0),
        },
        "median_seconds": float(row[6]) if row[6] is not None else None,
    }


def _conversions_by_channel(conn, where_sql: str, params: Tuple[Any, ...]) -> Dict[str, int]:
    try:
        cur = execute(
            conn,
            f"""
            SELECT COALESCE(d.channel, 'stored') AS channel, COUNT(*)
            FROM nudge_conversions c
            JOIN nudge_deliveries d
              ON d.delivery_group_id = c.delivery_group_id
             AND COALESCE(d.is_primary, TRUE)
            WHERE {where_sql}
            GROUP BY 1
            """,
            params,
        )
        return {str(r[0]): int(r[1] or 0) for r in (cur.fetchall() or [])}
    except Exception as e:
        logger.warning("conversions-by-channel query failed: %s", e)
        return {}


def count_window_conversions(
    conn, where_sql: str, params: Tuple[Any, ...], window_hours: int = 24
) -> int:
    """
    Time-window attribution fallback: nudge groups with no tap conversion where the
    user still asked a chat question within `window_hours` of the nudge.
    """
    try:
        cur = execute(
            conn,
            f"""
            SELECT COUNT(DISTINCT COALESCE(d.delivery_group_id, d.id::text))
            FROM nudge_deliveries d
            WHERE {where_sql}
              AND COALESCE(d.is_primary, TRUE)
              AND (d.delivery_group_id IS NULL OR NOT EXISTS (
                    SELECT 1 FROM nudge_conversions c
                    WHERE c.delivery_group_id = d.delivery_group_id
              ))
              AND EXISTS (
                    SELECT 1
                    FROM chat_messages cm
                    JOIN chat_sessions cs ON cs.session_id = cm.session_id
                    WHERE cs.user_id = d.userid
                      AND cm.sender = 'user'
                      AND cm.timestamp >= d.created_at
                      AND cm.timestamp <= d.created_at + (%s || ' hours')::interval
              )
            """,
            params + (str(int(window_hours)),),
        )
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    except Exception as e:
        logger.warning("window-conversion query failed: %s", e)
        return 0


def campaign_stats(conn, campaign_id: int) -> Dict[str, Any]:
    cid = int(campaign_id)
    sends = _delivery_channel_counts(conn, "campaign_id = %s", (cid,))
    conv = _conversion_summary(conn, "campaign_id = %s", (cid,))
    conv_by_channel = _conversions_by_channel(conn, "c.campaign_id = %s", (cid,))
    window_conversions = count_window_conversions(conn, "d.campaign_id = %s", (cid,))
    targeted = sends.get("targeted") or 0
    conversions = conv.get("conversions") or 0
    return {
        "campaign_id": cid,
        "sends": sends,
        "conversions": conversions,
        "window_conversions": window_conversions,
        "conversion_rate": round(conversions / targeted, 4) if targeted else 0.0,
        "conversions_by_channel": conv_by_channel,
        "time_buckets": conv.get("time_buckets"),
        "median_seconds_to_question": conv.get("median_seconds"),
    }


def overview_stats(conn, start_date: str, end_date: str) -> Dict[str, Any]:
    sends = _delivery_channel_counts(
        conn, "sent_at >= %s AND sent_at <= %s", (start_date, end_date)
    )
    conv = _conversion_summary(
        conn,
        "converted_at::date >= %s AND converted_at::date <= %s",
        (start_date, end_date),
    )
    conv_by_channel = _conversions_by_channel(
        conn,
        "c.converted_at::date >= %s AND c.converted_at::date <= %s",
        (start_date, end_date),
    )
    # Per-trigger/campaign breakdown of sends in range.
    cur = execute(
        conn,
        """
        SELECT d.trigger_id,
               d.campaign_id,
               COUNT(DISTINCT COALESCE(d.delivery_group_id, d.id::text)) AS targeted,
               COUNT(*) FILTER (WHERE d.channel = 'push' AND COALESCE(d.send_status, 'sent') = 'sent') AS push,
               COUNT(*) FILTER (WHERE d.channel IN ('whatsapp','whatsapp_template') AND COALESCE(d.send_status, 'sent') = 'sent') AS whatsapp,
               COUNT(*) FILTER (WHERE d.channel = 'email' AND COALESCE(d.send_status, 'sent') = 'sent') AS email
        FROM nudge_deliveries d
        WHERE d.sent_at >= %s AND d.sent_at <= %s
        GROUP BY 1, 2
        ORDER BY 3 DESC
        LIMIT 100
        """,
        (start_date, end_date),
    )
    by_source = [
        {
            "trigger_id": r[0] or "",
            "campaign_id": int(r[1]) if r[1] is not None else None,
            "targeted": int(r[2] or 0),
            "push": int(r[3] or 0),
            "whatsapp": int(r[4] or 0),
            "email": int(r[5] or 0),
        }
        for r in (cur.fetchall() or [])
    ]
    # Conversions per trigger in range.
    cur = execute(
        conn,
        """
        SELECT COALESCE(trigger_id, ''), campaign_id, COUNT(*)
        FROM nudge_conversions
        WHERE converted_at::date >= %s AND converted_at::date <= %s
        GROUP BY 1, 2
        """,
        (start_date, end_date),
    )
    conv_index: Dict[Tuple[str, Optional[int]], int] = {}
    for r in cur.fetchall() or []:
        conv_index[(str(r[0] or ""), int(r[1]) if r[1] is not None else None)] = int(r[2] or 0)
    for item in by_source:
        item["conversions"] = conv_index.get(
            (item["trigger_id"], item["campaign_id"]), 0
        )
    targeted = sends.get("targeted") or 0
    conversions = conv.get("conversions") or 0
    return {
        "start_date": start_date,
        "end_date": end_date,
        "sends": sends,
        "conversions": conversions,
        "conversion_rate": round(conversions / targeted, 4) if targeted else 0.0,
        "conversions_by_channel": conv_by_channel,
        "time_buckets": conv.get("time_buckets"),
        "median_seconds_to_question": conv.get("median_seconds"),
        "by_source": by_source,
    }


def list_cron_runs(conn, job_key: str, limit: int = 20) -> List[Tuple]:
    lim = max(1, min(int(limit), 200))
    cur = execute(
        conn,
        """
        SELECT id, job_key, status, summary_json, created_at
        FROM nudge_cron_runs
        WHERE job_key = %s
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """,
        (str(job_key or "").strip(), lim),
    )
    return list(cur.fetchall() or [])
