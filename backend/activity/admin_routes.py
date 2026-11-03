"""
Admin-only API to query user activity from BigQuery (today by default, with filters and sort).
"""
import os
import logging
import threading
import time
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Any, List, Dict
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user, User
from db import get_conn, execute

logger = logging.getLogger(__name__)

router = APIRouter()

_IST = ZoneInfo("Asia/Kolkata")
_PULSE_CACHE: Dict[str, Any] = {"expires_at": 0.0, "payload": None}
_PULSE_CACHE_LOCK = threading.Lock()

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.environ.get("ASTROLOGY_DB_PATH") or os.path.join(_BACKEND_DIR, "astrology.db")


def _enrich_activity_user_ids(out: List[Dict[str, Any]]) -> None:
    """
    For activity rows that have user_phone but missing user_id or user_name (e.g. old JWTs),
    look up userid and name from the users table and set them on the row.
    """
    def _missing_uid(uid):  # treat None, 0, "" as missing
        if uid is None:
            return True
        if isinstance(uid, (int, float)):
            return int(uid) == 0
        return str(uid).strip() == ""

    def _missing_name(name):  # treat None or blank as missing
        if name is None:
            return True
        return str(name).strip() == ""

    def _phone_key(v: Any) -> str:
        """
        Normalize phone values to a comparable key across BigQuery/Postgres types.
        Handles ints from Postgres and strings like '+91 98765-43210' from events.
        """
        s = str(v or "").strip()
        if not s:
            return ""
        digits = "".join(ch for ch in s if ch.isdigit())
        return digits or s

    phones_to_lookup = set()
    for row in out:
        phone = row.get("user_phone")
        k = _phone_key(phone)
        if k:
            uid = row.get("user_id")
            name = row.get("user_name")
            if _missing_uid(uid) or _missing_name(name):
                phones_to_lookup.add(k)
    if not phones_to_lookup:
        return
    try:
        with get_conn() as conn:
            # phone may be stored as TEXT or numeric in different environments.
            # Compare via normalized digits to avoid type/format mismatches.
            cur = execute(
                conn,
                """
                SELECT userid, name, phone
                FROM users
                WHERE regexp_replace(COALESCE(phone::text, ''), '[^0-9]', '', 'g') = ANY(%s)
                """,
                (list(phones_to_lookup),),
            )
            # phone -> (userid, name); name may be None
            phone_to_user = {}
            for row in cur.fetchall() or []:
                k = _phone_key(row[2])
                if not k:
                    continue
                phone_to_user[k] = (
                    row[0],
                    row[1] if (row[1] and str(row[1]).strip()) else None,
                )
        for row in out:
            phone = row.get("user_phone")
            k = _phone_key(phone)
            if not k:
                continue
            entry = phone_to_user.get(k)
            if not entry:
                continue
            userid, name = entry
            if _missing_uid(row.get("user_id")):
                row["user_id"] = userid
            if _missing_name(row.get("user_name")) and name:
                row["user_name"] = name
    except Exception as e:
        logger.warning("Activity: enrich user_id/user_name by phone failed (db=%s): %s", _DB_PATH, e)


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _get_bigquery_table() -> Optional[str]:
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "").strip()
    dataset = os.getenv("BIGQUERY_DATASET_ID", "activity")
    table = os.getenv("BIGQUERY_TABLE_ID", "user_activity")
    if not project:
        return None
    return f"`{project}.{dataset}.{table}`"


# Columns we return (match BigQuery schema)
ACTIVITY_COLUMNS = [
    "event_id", "user_id", "user_phone", "user_name", "action", "path",
    "method", "status_code", "duration_ms", "resource_type", "resource_id",
    "metadata",
    "error_type", "error_message", "stack_trace",
    "ip", "user_agent", "created_at",
]


def _admin_today_ist() -> date:
    return datetime.now(_IST).date()


def _parse_dashboard_date(value: Optional[str]) -> date:
    if not value:
        return _admin_today_ist()
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc


def _dashboard_bounds_utc(day: date) -> tuple[datetime, datetime]:
    start = datetime(day.year, day.month, day.day, tzinfo=_IST).astimezone(timezone.utc)
    return start, start + timedelta(days=1)


def _bigquery_client():
    """Build the same credential-aware client used by the Activity log."""
    from google.cloud import bigquery
    from google.oauth2 import service_account
    from utils.env_json import parse_json_from_env

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "").strip()
    key = (
        os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
        or os.getenv("GOOGLE_TTS_SERVICE_ACCOUNT_JSON")
        or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
    )
    creds = None
    if key and str(key).strip():
        raw = str(key).strip()
        info = parse_json_from_env(raw)
        if info and isinstance(info, dict):
            creds = service_account.Credentials.from_service_account_info(info)
        elif os.path.isfile(raw):
            creds = service_account.Credentials.from_service_account_file(raw)
    return bigquery.Client(project=project, credentials=creds) if creds else bigquery.Client(project=project)


def _query_bigquery_pulse(start_utc: datetime, end_utc: datetime) -> Dict[str, Any]:
    """Best-effort API health metrics. The dashboard remains useful without BigQuery."""
    table = _get_bigquery_table()
    if not table:
        return {"available": False, "reason": "BigQuery is not configured"}
    try:
        from google.cloud import bigquery

        client = _bigquery_client()
        params = [
            bigquery.ScalarQueryParameter("start_ts", "TIMESTAMP", start_utc),
            bigquery.ScalarQueryParameter("end_ts", "TIMESTAMP", end_utc),
        ]
        config = bigquery.QueryJobConfig(query_parameters=params)
        summary_sql = f"""
            SELECT
              COUNT(*) AS api_calls,
              COUNT(DISTINCT CASE
                WHEN user_id IS NOT NULL AND user_id != 0 THEN CAST(user_id AS STRING)
                WHEN REGEXP_REPLACE(COALESCE(user_phone, ''), r'[^0-9]', '') != ''
                  THEN REGEXP_REPLACE(user_phone, r'[^0-9]', '')
              END) AS active_users,
              COUNTIF(action = 'api_error' OR COALESCE(status_code, 200) < 200
                OR COALESCE(status_code, 200) >= 300) AS error_count,
              APPROX_QUANTILES(COALESCE(duration_ms, 0), 100)[SAFE_OFFSET(95)] AS p95_duration_ms
            FROM {table}
            WHERE created_at >= @start_ts AND created_at < @end_ts
        """
        summary_rows = list(client.query(summary_sql, job_config=config))
        summary = dict(summary_rows[0]) if summary_rows else {}

        hourly_sql = f"""
            SELECT
              FORMAT_TIMESTAMP('%H:00', created_at, 'Asia/Kolkata') AS hour,
              COUNT(*) AS api_calls,
              COUNTIF(action = 'api_error' OR COALESCE(status_code, 200) < 200
                OR COALESCE(status_code, 200) >= 300) AS errors
            FROM {table}
            WHERE created_at >= @start_ts AND created_at < @end_ts
            GROUP BY hour ORDER BY hour
        """
        endpoint_sql = f"""
            SELECT COALESCE(NULLIF(path, ''), action, 'Unknown') AS path,
                   COUNT(*) AS calls,
                   COUNTIF(action = 'api_error' OR COALESCE(status_code, 200) < 200
                     OR COALESCE(status_code, 200) >= 300) AS errors,
                   APPROX_QUANTILES(COALESCE(duration_ms, 0), 100)[SAFE_OFFSET(95)] AS p95_duration_ms
            FROM {table}
            WHERE created_at >= @start_ts AND created_at < @end_ts
            GROUP BY path ORDER BY calls DESC LIMIT 8
        """
        recent_sql = f"""
            SELECT user_id, user_name, action, path, status_code, duration_ms, created_at
            FROM {table}
            WHERE created_at >= @start_ts AND created_at < @end_ts
            ORDER BY created_at DESC LIMIT 30
        """
        # Native chart navigation already emits mobile_screen_view through
        # /activity/mobile-events.  Keep this aggregate separate from generic
        # API traffic so App Pulse can answer product questions such as
        # "how many people opened a chart today?" without adding another
        # client-side tracker.
        screen_sql = f"""
            SELECT
              COALESCE(NULLIF(JSON_VALUE(metadata, '$.screen_name'), ''),
                       NULLIF(resource_id, ''), 'Unknown') AS screen,
              COALESCE(NULLIF(JSON_VALUE(metadata, '$.content_type'), ''),
                       NULLIF(resource_type, ''), 'screen') AS content_type,
              COUNTIF(action = 'mobile_screen_view') AS opens,
              COUNT(DISTINCT CASE
                WHEN action = 'mobile_screen_view' AND user_id IS NOT NULL AND user_id != 0 THEN CAST(user_id AS STRING)
                WHEN action = 'mobile_screen_view' AND REGEXP_REPLACE(COALESCE(user_phone, ''), r'[^0-9]', '') != ''
                  THEN REGEXP_REPLACE(user_phone, r'[^0-9]', '')
              END) AS users
              ,APPROX_QUANTILES(
                IF(action = 'mobile_screen_exit', duration_ms, NULL), 100
              )[SAFE_OFFSET(50)] AS median_duration_ms
            FROM {table}
            WHERE created_at >= @start_ts AND created_at < @end_ts
              AND action IN ('mobile_screen_view', 'mobile_screen_exit')
            GROUP BY screen, content_type
            ORDER BY users DESC, opens DESC
            LIMIT 60
        """
        return {
            "available": True,
            "summary": {
                "api_calls": int(summary.get("api_calls") or 0),
                "active_users": int(summary.get("active_users") or 0),
                "error_count": int(summary.get("error_count") or 0),
                "p95_duration_ms": int(summary.get("p95_duration_ms") or 0),
            },
            "hourly": [dict(row) for row in client.query(hourly_sql, job_config=config)],
            "endpoints": [dict(row) for row in client.query(endpoint_sql, job_config=config)],
            "recent": [dict(row) for row in client.query(recent_sql, job_config=config)],
            "screens": [dict(row) for row in client.query(screen_sql, job_config=config)],
        }
    except Exception as exc:
        logger.warning("App pulse BigQuery metrics unavailable: %s", exc)
        return {"available": False, "reason": "API telemetry is temporarily unavailable"}


@router.get("/admin/activity/dashboard")
async def get_activity_dashboard(
    date_value: Optional[str] = Query(None, alias="date", description="IST date YYYY-MM-DD; defaults to today"),
    current_user: User = Depends(_require_admin),
):
    """Admin App Pulse: read-replica product activity plus BigQuery API health."""
    del current_user
    day = _parse_dashboard_date(date_value)
    cache_key = day.isoformat()
    now_mono = time.monotonic()
    with _PULSE_CACHE_LOCK:
        cached = _PULSE_CACHE.get("payload")
        if cached and _PULSE_CACHE.get("key") == cache_key and _PULSE_CACHE["expires_at"] > now_mono:
            return {**cached, "cached": True}

    start_utc, end_utc = _dashboard_bounds_utc(day)
    # Application timestamps are stored as UTC timestamps without timezone in
    # the legacy schema, so send naive UTC bounds to Postgres deliberately.
    start_db, end_db = start_utc.replace(tzinfo=None), end_utc.replace(tzinfo=None)
    try:
        from nudge_engine.connections import get_audience_conn

        with get_audience_conn() as conn:
            cur = execute(
                conn,
                """
                WITH chat AS (
                  SELECT s.user_id, m.sender, m.status, m.chat_tier,
                         COALESCE(m.completed_at, m.timestamp, m.started_at) AS happened_at
                  FROM chat_messages m
                  JOIN chat_sessions s ON s.session_id = m.session_id
                  WHERE COALESCE(m.completed_at, m.timestamp, m.started_at) >= %s
                    AND COALESCE(m.completed_at, m.timestamp, m.started_at) < %s
                ), tx AS (
                  SELECT userid, transaction_type, amount, source, created_at
                  FROM credit_transactions
                  WHERE created_at >= %s AND created_at < %s
                )
                SELECT
                  (SELECT COUNT(DISTINCT user_id) FROM chat) AS chat_users,
                  (SELECT COUNT(*) FROM chat WHERE sender = 'user') AS questions,
                  (SELECT COUNT(*) FROM chat WHERE sender <> 'user' AND status = 'completed') AS answers_delivered,
                  (SELECT COUNT(*) FROM chat WHERE sender <> 'user' AND status = 'error') AS chat_failures,
                  (SELECT COUNT(DISTINCT userid) FROM tx WHERE transaction_type = 'spent') AS spending_users,
                  (SELECT COALESCE(SUM(ABS(amount)), 0) FROM tx WHERE transaction_type = 'spent') AS credits_spent,
                  (SELECT COUNT(*) FROM tx WHERE transaction_type = 'earned' AND source IN ('google_play', 'razorpay')) AS paid_purchases,
                  (SELECT COUNT(DISTINCT userid) FROM tx WHERE transaction_type = 'earned' AND source IN ('google_play', 'razorpay')) AS paid_buyers,
                  (SELECT COALESCE(SUM(amount), 0) FROM tx WHERE transaction_type = 'earned' AND source IN ('google_play', 'razorpay')) AS paid_credits
                """,
                (start_db, end_db, start_db, end_db),
            )
            summary_row = cur.fetchone() or [0] * 10
            summary = {
                key: int(summary_row[idx] or 0)
                for idx, key in enumerate((
                    "chat_users", "questions", "answers_delivered", "chat_failures",
                    "spending_users", "credits_spent", "paid_purchases", "paid_buyers", "paid_credits",
                ))
            }

            cur = execute(
                conn,
                """
                SELECT COALESCE(NULLIF(chat_tier, ''), 'standard') AS tier, COUNT(*)::int
                FROM chat_messages m JOIN chat_sessions s ON s.session_id = m.session_id
                WHERE m.sender = 'user'
                  AND COALESCE(m.completed_at, m.timestamp, m.started_at) >= %s
                  AND COALESCE(m.completed_at, m.timestamp, m.started_at) < %s
                GROUP BY 1 ORDER BY 2 DESC
                """, (start_db, end_db),
            )
            chat_by_tier = [{"name": row[0], "count": int(row[1] or 0)} for row in cur.fetchall() or []]

            cur = execute(
                conn,
                """
                SELECT to_char((COALESCE(m.completed_at, m.timestamp, m.started_at) AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Kolkata', 'HH24:00') AS hour,
                       COUNT(*) FILTER (WHERE m.sender = 'user')::int AS questions,
                       COUNT(*) FILTER (WHERE m.sender <> 'user' AND m.status = 'completed')::int AS answers
                FROM chat_messages m JOIN chat_sessions s ON s.session_id = m.session_id
                WHERE COALESCE(m.completed_at, m.timestamp, m.started_at) >= %s
                  AND COALESCE(m.completed_at, m.timestamp, m.started_at) < %s
                GROUP BY 1 ORDER BY 1
                """, (start_db, end_db),
            )
            chat_hourly = [{"hour": row[0], "questions": int(row[1] or 0), "answers": int(row[2] or 0)} for row in cur.fetchall() or []]

            cur = execute(
                conn,
                """
                SELECT feature, COUNT(*)::int AS started,
                       COUNT(*) FILTER (WHERE status = 'completed')::int AS completed,
                       COUNT(*) FILTER (WHERE status = 'failed')::int AS failed,
                       COUNT(DISTINCT userid)::int AS users
                FROM (
                  SELECT 'Nakshatra Blueprint' AS feature, userid, status, created_at FROM nakshatra_blueprints
                  WHERE created_at >= %s AND created_at < %s
                  UNION ALL
                  SELECT 'Partner Portrait', user_id, status, created_at FROM partner_portrait_jobs
                  WHERE created_at >= %s AND created_at < %s
                ) reports
                GROUP BY feature ORDER BY started DESC, feature
                """, (start_db, end_db, start_db, end_db),
            )
            reports = [
                {"feature": row[0], "started": int(row[1] or 0), "completed": int(row[2] or 0), "failed": int(row[3] or 0), "users": int(row[4] or 0)}
                for row in cur.fetchall() or []
            ]

            cur = execute(
                conn,
                """
                SELECT s.user_id, COALESCE(NULLIF(u.name, ''), 'User #' || s.user_id::text) AS name,
                       MAX(COALESCE(m.completed_at, m.timestamp, m.started_at)) AS last_activity,
                       COUNT(*) FILTER (WHERE m.sender = 'user')::int AS questions,
                       COUNT(*) FILTER (WHERE m.sender <> 'user' AND m.status = 'error')::int AS failed_answers
                FROM chat_messages m
                JOIN chat_sessions s ON s.session_id = m.session_id
                LEFT JOIN users u ON u.userid = s.user_id
                WHERE COALESCE(m.completed_at, m.timestamp, m.started_at) >= %s
                  AND COALESCE(m.completed_at, m.timestamp, m.started_at) < %s
                GROUP BY s.user_id, u.name
                HAVING COUNT(*) FILTER (WHERE m.sender <> 'user' AND m.status = 'error') > 0
                ORDER BY failed_answers DESC, last_activity DESC LIMIT 20
                """, (start_db, end_db),
            )
            attention = [
                {"user_id": int(row[0]), "name": row[1], "last_activity": row[2], "questions": int(row[3] or 0), "failed_answers": int(row[4] or 0)}
                for row in cur.fetchall() or []
            ]
    except Exception as exc:
        logger.exception("App pulse replica query failed: %s", exc)
        raise HTTPException(status_code=500, detail="App Pulse data is temporarily unavailable") from exc

    api = _query_bigquery_pulse(start_utc, end_utc)
    if api.get("available"):
        summary["active_users"] = max(summary["chat_users"], int((api.get("summary") or {}).get("active_users") or 0))
    else:
        summary["active_users"] = summary["chat_users"]
    payload = {
        "date": day.isoformat(),
        "timezone": "Asia/Kolkata",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "summary": summary,
        "chat_by_tier": chat_by_tier,
        "chat_hourly": chat_hourly,
        "reports": reports,
        "attention": attention,
        "api": api,
    }
    with _PULSE_CACHE_LOCK:
        _PULSE_CACHE.update({"key": cache_key, "expires_at": time.monotonic() + 60.0, "payload": payload})
    return payload


@router.get("/admin/activity")
async def get_activity(
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD (default: today)"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD (default: today)"),
    user_id: Optional[int] = Query(None, description="Filter by BigQuery user_id (exact match)"),
    user_name: Optional[str] = Query(None, description="Filter by logged user_name; also matches users.name/email in DB via user_id/phone"),
    user_phone: Optional[str] = Query(None, description="Filter by phone (partial match)"),
    action: Optional[str] = Query(None, description="Filter by action (e.g. api_request, podcast_generated)"),
    resource_id: Optional[str] = Query(None, description="Filter by resource id (e.g. Google Play order id)"),
    errors_only: bool = Query(
        False,
        description="If true: rows where action=api_error (unhandled exception) OR action=api_request with HTTP status outside 2xx",
    ),
    sort_by: Optional[str] = Query("created_at", description="Column to sort by"),
    order: Optional[str] = Query("desc", description="asc or desc"),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(_require_admin),
):
    """
    Return activity rows from BigQuery. Default: today's activity, sorted by created_at desc.
    """
    table = _get_bigquery_table()
    if not table:
        raise HTTPException(status_code=503, detail="BigQuery not configured (GOOGLE_CLOUD_PROJECT)")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    from_date = (date_from or "").strip() or today
    to_date = (date_to or "").strip() or today

    # Validate sort column
    if sort_by and sort_by not in ACTIVITY_COLUMNS:
        sort_by = "created_at"
    order = "DESC" if (order or "").lower() == "desc" else "ASC"

    order_col = sort_by if sort_by in ACTIVITY_COLUMNS else "created_at"
    cols = ", ".join(ACTIVITY_COLUMNS)

    # Resolve name/email to user ids + phone digits (Postgres) so we still match BigQuery rows
    # where user_name was empty but user_id / phone was logged.
    resolved_user_ids: List[int] = []
    resolved_phone_digits: List[str] = []
    if user_name and user_name.strip():
        pat = f"%{user_name.strip()}%"
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT userid,
                           regexp_replace(COALESCE(phone::text, ''), '[^0-9]', '', 'g')
                    FROM users
                    WHERE name ILIKE %s OR COALESCE(email, '') ILIKE %s
                    """,
                    (pat, pat),
                )
                seen_ph = set()
                for row in cur.fetchall() or []:
                    if row[0] is not None:
                        try:
                            resolved_user_ids.append(int(row[0]))
                        except (TypeError, ValueError):
                            pass
                    dig = (row[1] or "").strip()
                    if dig and dig not in seen_ph:
                        seen_ph.add(dig)
                        resolved_phone_digits.append(dig)
                resolved_user_ids = list(dict.fromkeys(resolved_user_ids))
        except Exception as e:
            logger.warning("Activity: resolve users by name/email failed: %s", e)

    # Build SQL with @param placeholders; params list built below
    where_parts = ["DATE(created_at) >= @from_date", "DATE(created_at) <= @to_date"]
    if user_id is not None:
        where_parts.append("user_id = @filter_user_id")
    if user_name and user_name.strip():
        name_or_parts = ["LOWER(COALESCE(user_name, '')) LIKE LOWER(@user_name)"]
        if resolved_user_ids:
            name_or_parts.append("user_id IN UNNEST(@resolved_user_ids)")
        if resolved_phone_digits:
            name_or_parts.append(
                "REGEXP_REPLACE(COALESCE(user_phone, ''), r'[^0-9]', '') IN UNNEST(@resolved_phone_digits)"
            )
        where_parts.append(f"({' OR '.join(name_or_parts)})")
    if user_phone and user_phone.strip():
        where_parts.append("COALESCE(user_phone, '') LIKE @user_phone")
    if errors_only:
        # Unhandled exceptions (middleware) + normal FastAPI responses with non-success HTTP status
        where_parts.append(
            "("
            "action = 'api_error' "
            "OR (action = 'api_request' AND status_code IS NOT NULL "
            "AND (status_code < 200 OR status_code >= 300))"
            ")"
        )
    elif action and action.strip():
        where_parts.append("COALESCE(action, '') = @action")
    if resource_id and resource_id.strip():
        where_parts.append("COALESCE(resource_id, '') LIKE @resource_id")
    where_clause = " AND ".join(where_parts)

    query = f"""
        SELECT {cols}
        FROM {table}
        WHERE {where_clause}
        ORDER BY {order_col} {order}
        LIMIT @limit_param OFFSET @offset_param
    """
    distinct_query = f"""
        WITH base AS (
            SELECT user_id, user_name, user_phone, duration_ms, created_at
            FROM {table}
            WHERE {where_clause}
        ),
        keyed AS (
            SELECT
                user_id,
                user_name,
                user_phone,
                duration_ms,
                created_at,
                CASE
                    WHEN user_id IS NOT NULL AND user_id != 0
                        THEN CONCAT('id:', CAST(user_id AS STRING))
                    WHEN REGEXP_REPLACE(COALESCE(user_phone, ''), r'[^0-9]', '') != ''
                        THEN CONCAT(
                            'ph:',
                            REGEXP_REPLACE(COALESCE(user_phone, ''), r'[^0-9]', '')
                        )
                    ELSE NULL
                END AS dedup_key
            FROM base
        ),
        grouped AS (
            SELECT
                ANY_VALUE(user_id) AS user_id,
                ANY_VALUE(user_name) AS user_name,
                ANY_VALUE(user_phone) AS user_phone,
                COUNT(*) AS api_calls,
                SUM(COALESCE(duration_ms, 0)) AS total_duration_ms,
                MAX(created_at) AS last_activity_at
            FROM keyed
            WHERE dedup_key IS NOT NULL
            GROUP BY dedup_key
        )
        SELECT user_id, user_name, user_phone, api_calls, total_duration_ms, last_activity_at
        FROM grouped
        ORDER BY last_activity_at DESC
        LIMIT 5000
    """
    # Rolling distinct users at ref time (UTC), same filters + dedup as distinct_users — full table scan, not LIMIT 500.
    window_query = f"""
        WITH base AS (
            SELECT user_id, user_phone, created_at
            FROM {table}
            WHERE {where_clause}
        ),
        keyed AS (
            SELECT
                created_at,
                CASE
                    WHEN user_id IS NOT NULL AND user_id != 0
                        THEN CONCAT('id:', CAST(user_id AS STRING))
                    WHEN REGEXP_REPLACE(COALESCE(user_phone, ''), r'[^0-9]', '') != ''
                        THEN CONCAT(
                            'ph:',
                            REGEXP_REPLACE(COALESCE(user_phone, ''), r'[^0-9]', '')
                        )
                    ELSE NULL
                END AS dedup_key
            FROM base
        ),
        f AS (
            SELECT created_at, dedup_key FROM keyed WHERE dedup_key IS NOT NULL
        )
        SELECT
            (SELECT COUNT(DISTINCT dedup_key) FROM f WHERE created_at >= TIMESTAMP_SUB(@ref_ts, INTERVAL 5 MINUTE)) AS uniq_5m,
            (SELECT COUNT(DISTINCT dedup_key) FROM f WHERE created_at >= TIMESTAMP_SUB(@ref_ts, INTERVAL 15 MINUTE)) AS uniq_15m,
            (SELECT COUNT(DISTINCT dedup_key) FROM f WHERE created_at >= TIMESTAMP_SUB(@ref_ts, INTERVAL 30 MINUTE)) AS uniq_30m,
            (SELECT COUNT(DISTINCT dedup_key) FROM f WHERE created_at >= TIMESTAMP_SUB(@ref_ts, INTERVAL 60 MINUTE)) AS uniq_60m,
            (SELECT COUNT(DISTINCT dedup_key) FROM f WHERE created_at >= TIMESTAMP_SUB(@ref_ts, INTERVAL 1 DAY)) AS uniq_1d
    """
    unique_users_by_window: Optional[Dict[str, Any]] = None
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        from utils.env_json import parse_json_from_env

        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "").strip()
        key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") or os.getenv("GOOGLE_TTS_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
        creds = None
        if key and str(key).strip():
            raw = str(key).strip()
            info = parse_json_from_env(raw)
            if info and isinstance(info, dict):
                creds = service_account.Credentials.from_service_account_info(info)
            elif os.path.isfile(raw):
                creds = service_account.Credentials.from_service_account_file(raw)
        client = bigquery.Client(project=project, credentials=creds) if creds else bigquery.Client(project=project)

        filter_params: List[Any] = [
            bigquery.ScalarQueryParameter("from_date", "DATE", from_date),
            bigquery.ScalarQueryParameter("to_date", "DATE", to_date),
        ]
        if user_id is not None:
            filter_params.append(bigquery.ScalarQueryParameter("filter_user_id", "INT64", int(user_id)))
        if user_name and user_name.strip():
            filter_params.append(bigquery.ScalarQueryParameter("user_name", "STRING", f"%{user_name.strip()}%"))
            if resolved_user_ids:
                filter_params.append(
                    bigquery.ArrayQueryParameter("resolved_user_ids", "INT64", resolved_user_ids)
                )
            if resolved_phone_digits:
                filter_params.append(
                    bigquery.ArrayQueryParameter("resolved_phone_digits", "STRING", resolved_phone_digits)
                )
        if user_phone and user_phone.strip():
            filter_params.append(bigquery.ScalarQueryParameter("user_phone", "STRING", f"%{user_phone.strip()}%"))
        if not errors_only and action and action.strip():
            filter_params.append(bigquery.ScalarQueryParameter("action", "STRING", action.strip()))
        if resource_id and resource_id.strip():
            filter_params.append(bigquery.ScalarQueryParameter("resource_id", "STRING", f"%{resource_id.strip()}%"))

        job_params = filter_params + [
            bigquery.ScalarQueryParameter("limit_param", "INT64", int(limit)),
            bigquery.ScalarQueryParameter("offset_param", "INT64", int(offset)),
        ]

        job_config = bigquery.QueryJobConfig(query_parameters=job_params)
        rows_iter = client.query(query, job_config=job_config)
        rows = list(rows_iter)

        distinct_job_config = bigquery.QueryJobConfig(query_parameters=filter_params)
        distinct_rows = list(client.query(distinct_query, job_config=distinct_job_config))

        # Anchor rolling windows: "now" in UTC when range includes today; else end of to_date UTC (historical drill-down).
        if to_date >= today:
            ref_dt = datetime.now(timezone.utc)
        else:
            d_end = date.fromisoformat(to_date)
            ref_dt = datetime(
                d_end.year, d_end.month, d_end.day, 23, 59, 59, 999999, tzinfo=timezone.utc
            )
        window_params = list(filter_params) + [
            bigquery.ScalarQueryParameter("ref_ts", "TIMESTAMP", ref_dt),
        ]
        try:
            window_job = bigquery.QueryJobConfig(query_parameters=window_params)
            window_rows = list(client.query(window_query, job_config=window_job))
            if window_rows:
                wd = dict(window_rows[0])
                unique_users_by_window = {
                    "reference_at": ref_dt.isoformat().replace("+00:00", "Z"),
                    "windows": [
                        {"label": "5 min", "ms": 5 * 60 * 1000, "count": int(wd.get("uniq_5m") or 0)},
                        {"label": "15 min", "ms": 15 * 60 * 1000, "count": int(wd.get("uniq_15m") or 0)},
                        {"label": "30 min", "ms": 30 * 60 * 1000, "count": int(wd.get("uniq_30m") or 0)},
                        {"label": "1 hour", "ms": 60 * 60 * 1000, "count": int(wd.get("uniq_60m") or 0)},
                        {"label": "1 day", "ms": 24 * 60 * 60 * 1000, "count": int(wd.get("uniq_1d") or 0)},
                    ],
                }
        except Exception as win_e:
            logger.warning("Activity window stats query failed: %s", win_e)
    except Exception as e:
        logger.exception("BigQuery activity query failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Activity query failed: {e}")

    def _serialize(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (datetime, date)):
            return v.isoformat() if hasattr(v, "isoformat") else str(v)
        if isinstance(v, dict):
            return {k: _serialize(vk) for k, vk in v.items()}
        return v

    # BigQuery Row -> dict (keys may be lowercase); serialize for JSON
    out = []
    for row in rows:
        d = dict(row)
        row_dict = {col: d.get(col) or d.get(col.lower()) for col in ACTIVITY_COLUMNS}
        out.append({k: _serialize(v) for k, v in row_dict.items()})

    # Enrich rows that have user_phone but no user_id (e.g. old JWTs): look up userid from users table
    _enrich_activity_user_ids(out)

    distinct_out: List[Dict[str, Any]] = []
    for row in distinct_rows:
        d = dict(row)
        tdur = d.get("total_duration_ms")
        try:
            total_dur = float(tdur) if tdur is not None else 0.0
        except (TypeError, ValueError):
            total_dur = 0.0
        distinct_out.append({
            "user_id": _serialize(d.get("user_id")),
            "user_name": _serialize(d.get("user_name")),
            "user_phone": _serialize(d.get("user_phone")),
            "api_calls": int(d.get("api_calls") or 0),
            "total_duration_ms": round(total_dur, 2),
            "last_activity_at": _serialize(d.get("last_activity_at")),
        })
    _enrich_activity_user_ids(distinct_out)

    payload: Dict[str, Any] = {
        "activity": out,
        "count": len(out),
        "distinct_users": distinct_out,
        "distinct_user_count": len(distinct_out),
    }
    if unique_users_by_window is not None:
        payload["unique_users_by_window"] = unique_users_by_window
    return payload


def fetch_activity_rows_for_user(
    user_id: int,
    from_date: str,
    to_date: str,
    limit: int = 2000,
) -> List[Dict[str, Any]]:
    """
    BigQuery activity rows for a single user (used by admin user profile).
    Returns an empty list if BigQuery is not configured or the query fails.
    """
    table = _get_bigquery_table()
    if not table:
        return []

    def _serialize(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (datetime, date)):
            return v.isoformat() if hasattr(v, "isoformat") else str(v)
        if isinstance(v, dict):
            return {k: _serialize(vk) for k, vk in v.items()}
        return v

    cols = ", ".join(ACTIVITY_COLUMNS)
    query = f"""
        SELECT {cols}
        FROM {table}
        WHERE DATE(created_at) >= @from_date
          AND DATE(created_at) <= @to_date
          AND user_id = @filter_user_id
        ORDER BY created_at DESC
        LIMIT @limit_param
    """
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        from utils.env_json import parse_json_from_env

        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID", "").strip()
        key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") or os.getenv("GOOGLE_TTS_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
        creds = None
        if key and str(key).strip():
            raw = str(key).strip()
            info = parse_json_from_env(raw)
            if info and isinstance(info, dict):
                creds = service_account.Credentials.from_service_account_info(info)
            elif os.path.isfile(raw):
                creds = service_account.Credentials.from_service_account_file(raw)
        client = bigquery.Client(project=project, credentials=creds) if creds else bigquery.Client(project=project)

        job_params = [
            bigquery.ScalarQueryParameter("from_date", "DATE", from_date),
            bigquery.ScalarQueryParameter("to_date", "DATE", to_date),
            bigquery.ScalarQueryParameter("filter_user_id", "INT64", int(user_id)),
            bigquery.ScalarQueryParameter("limit_param", "INT64", int(limit)),
        ]
        job_config = bigquery.QueryJobConfig(query_parameters=job_params)
        rows = list(client.query(query, job_config=job_config))
    except Exception as e:
        logger.warning("fetch_activity_rows_for_user failed: %s", e)
        return []

    out: List[Dict[str, Any]] = []
    for row in rows:
        d = dict(row)
        row_dict = {col: d.get(col) or d.get(col.lower()) for col in ACTIVITY_COLUMNS}
        out.append({k: _serialize(v) for k, v in row_dict.items()})
    _enrich_activity_user_ids(out)
    return out
