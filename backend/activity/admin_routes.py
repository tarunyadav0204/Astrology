"""
Admin-only API to query user activity from BigQuery (today by default, with filters and sort).
"""
import os
import logging
from datetime import datetime, timezone, date
from typing import Optional, Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user, User
from db import get_conn, execute

logger = logging.getLogger(__name__)

router = APIRouter()

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


@router.get("/admin/activity")
async def get_activity(
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD (default: today)"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD (default: today)"),
    user_name: Optional[str] = Query(None, description="Filter by username (partial match)"),
    user_phone: Optional[str] = Query(None, description="Filter by phone (partial match)"),
    action: Optional[str] = Query(None, description="Filter by action (e.g. api_request, podcast_generated)"),
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

    # Build SQL with @param placeholders; params list built below
    where_parts = ["DATE(created_at) >= @from_date", "DATE(created_at) <= @to_date"]
    if user_name and user_name.strip():
        where_parts.append("LOWER(COALESCE(user_name, '')) LIKE LOWER(@user_name)")
    if user_phone and user_phone.strip():
        where_parts.append("COALESCE(user_phone, '') LIKE @user_phone")
    if action and action.strip():
        where_parts.append("COALESCE(action, '') = @action")
    where_clause = " AND ".join(where_parts)

    query = f"""
        SELECT {cols}
        FROM {table}
        WHERE {where_clause}
        ORDER BY {order_col} {order}
        LIMIT @limit_param OFFSET @offset_param
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
            bigquery.ScalarQueryParameter("limit_param", "INT64", int(limit)),
            bigquery.ScalarQueryParameter("offset_param", "INT64", int(offset)),
        ]
        if user_name and user_name.strip():
            job_params.append(bigquery.ScalarQueryParameter("user_name", "STRING", f"%{user_name.strip()}%"))
        if user_phone and user_phone.strip():
            job_params.append(bigquery.ScalarQueryParameter("user_phone", "STRING", f"%{user_phone.strip()}%"))
        if action and action.strip():
            job_params.append(bigquery.ScalarQueryParameter("action", "STRING", action.strip()))

        job_config = bigquery.QueryJobConfig(query_parameters=job_params)
        rows_iter = client.query(query, job_config=job_config)
        rows = list(rows_iter)
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

    return {"activity": out, "count": len(out)}
