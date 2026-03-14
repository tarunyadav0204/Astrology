"""
Admin-only API to query user activity from BigQuery (today by default, with filters and sort).
"""
import os
import logging
from datetime import datetime, timezone, date
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter()


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
    "metadata", "ip", "user_agent", "created_at",
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
    return {"activity": out, "count": len(out)}
