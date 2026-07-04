"""
Backup account-deletion snapshots to BigQuery before Postgres data is scrubbed.

The table stores one row per deletion request. Each row has quick admin/search
columns plus a JSON payload containing per-table row snapshots.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_bq_client = None
_table_ensured = False


class AccountDeletionBackupError(RuntimeError):
    """Raised when a required BigQuery backup cannot be written."""


def _get_project() -> str:
    return (os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID") or "").strip()


def _get_dataset() -> str:
    return (
        os.getenv("BIGQUERY_ACCOUNT_DELETION_DATASET_ID")
        or os.getenv("BIGQUERY_DATASET_ID")
        or "activity"
    ).strip()


def _get_table_name() -> str:
    return (os.getenv("BIGQUERY_ACCOUNT_DELETION_TABLE_ID") or "deleted_account_backups").strip()


def _table_ref(backticks: bool = False) -> Optional[str]:
    project = _get_project()
    dataset = _get_dataset()
    table = _get_table_name()
    if not project or not dataset or not table:
        return None
    ref = f"{project}.{dataset}.{table}"
    return f"`{ref}`" if backticks else ref


def _get_client():
    global _bq_client
    if _bq_client is not None:
        return _bq_client
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        from utils.env_json import parse_json_from_env

        project = _get_project()
        if not project:
            return None
        key = (
            os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
            or os.getenv("GOOGLE_TTS_SERVICE_ACCOUNT_JSON")
            or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
            or ""
        )
        creds = None
        if key and str(key).strip():
            raw = str(key).strip()
            info = parse_json_from_env(raw)
            if info and isinstance(info, dict):
                creds = service_account.Credentials.from_service_account_info(info)
            elif os.path.isfile(raw):
                creds = service_account.Credentials.from_service_account_file(raw)
        _bq_client = bigquery.Client(project=project, credentials=creds) if creds else bigquery.Client(project=project)
        return _bq_client
    except Exception as e:
        logger.warning("account_deletion_bigquery: client init failed: %s", e)
        return None


def _ensure_table(client, *, required: bool = True) -> bool:
    global _table_ensured
    if _table_ensured:
        return True
    project = _get_project()
    dataset = _get_dataset()
    table_name = _get_table_name()
    if not project or not dataset or not table_name:
        if required:
            raise AccountDeletionBackupError("BigQuery account deletion backup table is not configured")
        return False

    try:
        from google.cloud import bigquery
        from google.api_core.exceptions import NotFound

        dataset_ref = bigquery.DatasetReference(project, dataset)
        table_ref = dataset_ref.table(table_name)
        try:
            client.get_table(table_ref)
            _table_ensured = True
            return True
        except NotFound:
            pass

        schema = [
            bigquery.SchemaField("deletion_id", "STRING", mode="REQUIRED", description="Unique account deletion backup id"),
            bigquery.SchemaField("deleted_at", "TIMESTAMP", mode="REQUIRED", description="Deletion time UTC"),
            bigquery.SchemaField("userid", "INT64", mode="REQUIRED", description="Deleted app user id"),
            bigquery.SchemaField("deleted_by_userid", "INT64", description="Admin/self user id that requested deletion"),
            bigquery.SchemaField("deletion_source", "STRING", description="self_service, admin, or another deletion source"),
            bigquery.SchemaField("user_phone", "STRING", description="Original phone before users.phone is scrubbed"),
            bigquery.SchemaField("user_name", "STRING", description="Original name before users.name is scrubbed"),
            bigquery.SchemaField("user_email", "STRING", description="Original email before users.email is scrubbed"),
            bigquery.SchemaField("signup_client", "STRING", description="Original users.signup_client"),
            bigquery.SchemaField("row_counts_json", "STRING", description="JSON object of backed-up row counts by source table"),
            bigquery.SchemaField("backup_payload", "STRING", description="Full JSON account snapshot grouped by source table"),
        ]
        table = bigquery.Table(table_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="deleted_at",
        )
        table.clustering_fields = ["userid", "deletion_source"]
        table.description = "Point-in-time snapshots captured before account deletion/anonymization"
        client.create_table(table)
        _table_ensured = True
        return True
    except AccountDeletionBackupError:
        raise
    except Exception as exc:
        if required:
            raise AccountDeletionBackupError(f"Could not ensure BigQuery deleted account backup table: {exc}") from exc
        logger.warning("Could not ensure BigQuery deleted account backup table: %s", exc)
        return False


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _fetch_rows(conn, table: str, sql: str, params: tuple) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    savepoint = f"sp_backup_{table}"
    cur.execute(f"SAVEPOINT {savepoint}")
    try:
        cur.execute(sql, params)
        cols = [desc[0] for desc in cur.description or []]
        rows = [{cols[i]: _json_safe(v) for i, v in enumerate(row)} for row in (cur.fetchall() or [])]
        cur.execute(f"RELEASE SAVEPOINT {savepoint}")
        return rows
    except Exception as exc:
        logger.warning("account_deletion_bigquery: skipped table %s: %s", table, exc)
        cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        cur.execute(f"RELEASE SAVEPOINT {savepoint}")
        return []


def build_account_deletion_snapshot(conn, userid: int) -> Dict[str, Any]:
    session_subquery = "SELECT session_id FROM chat_sessions WHERE user_id = %s"
    snapshot_queries = [
        ("users", "SELECT * FROM users WHERE userid = %s", (userid,)),
        ("password_reset_codes", "SELECT * FROM password_reset_codes WHERE phone IN (SELECT phone FROM users WHERE userid = %s)", (userid,)),
        ("birth_charts", "SELECT * FROM birth_charts WHERE userid = %s ORDER BY id", (userid,)),
        ("user_facts", "SELECT * FROM user_facts WHERE birth_chart_id IN (SELECT id FROM birth_charts WHERE userid = %s) ORDER BY id", (userid,)),
        ("event_timeline_jobs", "SELECT * FROM event_timeline_jobs WHERE user_id = %s ORDER BY created_at DESC", (userid,)),
        ("chat_sessions", "SELECT * FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC", (userid,)),
        ("conversation_state", f"SELECT * FROM conversation_state WHERE session_id IN ({session_subquery})", (userid,)),
        ("chat_messages", f"SELECT * FROM chat_messages WHERE session_id IN ({session_subquery}) ORDER BY timestamp, message_id", (userid,)),
        ("message_feedback", f"SELECT * FROM message_feedback WHERE message_id IN (SELECT message_id FROM chat_messages WHERE session_id IN ({session_subquery})) ORDER BY created_at, id", (userid,)),
        ("chat_wait_conversations", "SELECT * FROM chat_wait_conversations WHERE user_id = %s ORDER BY created_at DESC", (userid,)),
        ("chat_wait_conversation_messages", "SELECT * FROM chat_wait_conversation_messages WHERE conversation_id IN (SELECT conversation_id FROM chat_wait_conversations WHERE user_id = %s) ORDER BY created_at, id", (userid,)),
        ("device_tokens", "SELECT * FROM device_tokens WHERE userid = %s ORDER BY updated_at DESC", (userid,)),
        ("nudge_deliveries", "SELECT * FROM nudge_deliveries WHERE userid = %s ORDER BY created_at DESC", (userid,)),
        ("podcast_history", "SELECT * FROM podcast_history WHERE userid = %s ORDER BY created_at DESC", (userid,)),
        ("admin_allowed_devices", "SELECT * FROM admin_allowed_devices WHERE userid = %s ORDER BY created_at DESC", (userid,)),
        ("user_settings", "SELECT * FROM user_settings WHERE user_id = %s ORDER BY setting_key", (userid,)),
        ("user_subscriptions", "SELECT * FROM user_subscriptions WHERE userid = %s ORDER BY created_at DESC", (userid,)),
        ("credit_requests", "SELECT * FROM credit_requests WHERE userid = %s ORDER BY created_at DESC", (userid,)),
        ("promo_code_usage", "SELECT * FROM promo_code_usage WHERE userid = %s ORDER BY used_at DESC", (userid,)),
        ("user_credits_retained", "SELECT * FROM user_credits WHERE userid = %s", (userid,)),
        ("credit_transactions_retained", "SELECT * FROM credit_transactions WHERE userid = %s ORDER BY created_at DESC, id DESC", (userid,)),
        ("play_subscription_token_map_retained", "SELECT * FROM play_subscription_token_map WHERE userid = %s", (userid,)),
        ("play_subscription_event_log_retained", "SELECT * FROM play_subscription_event_log WHERE userid = %s ORDER BY event_time DESC", (userid,)),
        ("razorpay_subscription_map_retained", "SELECT * FROM razorpay_subscription_map WHERE userid = %s", (userid,)),
    ]

    tables: Dict[str, List[Dict[str, Any]]] = {}
    for table, sql, params in snapshot_queries:
        tables[table] = _fetch_rows(conn, table, sql, params)

    return {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "userid": int(userid),
        "tables": tables,
        "row_counts": {table: len(rows) for table, rows in tables.items()},
    }


def backup_user_deletion_to_bigquery(
    conn,
    *,
    userid: int,
    deleted_by_userid: Optional[int],
    deletion_source: str,
) -> str:
    table = _table_ref()
    client = _get_client()
    if not table or not client:
        raise AccountDeletionBackupError("BigQuery account deletion backup table is not configured")
    _ensure_table(client, required=True)

    snapshot = build_account_deletion_snapshot(conn, userid)
    user_rows = snapshot["tables"].get("users") or []
    user_row = user_rows[0] if user_rows else {}
    deletion_id = f"acctdel_{userid}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    row = {
        "deletion_id": deletion_id,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "userid": int(userid),
        "deleted_by_userid": int(deleted_by_userid) if deleted_by_userid is not None else None,
        "deletion_source": str(deletion_source or "unknown"),
        "user_phone": str(user_row.get("phone") or ""),
        "user_name": str(user_row.get("name") or ""),
        "user_email": str(user_row.get("email") or ""),
        "signup_client": str(user_row.get("signup_client") or ""),
        "row_counts_json": json.dumps(snapshot.get("row_counts") or {}, ensure_ascii=False),
        "backup_payload": json.dumps(snapshot, ensure_ascii=False),
    }
    try:
        errors = client.insert_rows_json(table, [row])
        if errors:
            raise AccountDeletionBackupError(f"BigQuery insert failed: {errors}")
        return deletion_id
    except AccountDeletionBackupError:
        raise
    except Exception as exc:
        raise AccountDeletionBackupError(f"BigQuery account deletion backup failed: {exc}") from exc


def list_deleted_account_backups(
    *,
    date_from: str,
    date_to: str,
    user_id: Optional[int] = None,
    query_text: str = "",
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    table = _table_ref(backticks=True)
    client = _get_client()
    if not table or not client:
        raise AccountDeletionBackupError("BigQuery account deletion backup table is not configured")
    if not _ensure_table(client, required=False):
        return {"backups": [], "total": 0, "limit": int(limit), "offset": int(offset)}

    from google.cloud import bigquery

    where = ["DATE(deleted_at) >= @from_date", "DATE(deleted_at) <= @to_date"]
    params: List[Any] = [
        bigquery.ScalarQueryParameter("from_date", "DATE", date_from),
        bigquery.ScalarQueryParameter("to_date", "DATE", date_to),
        bigquery.ScalarQueryParameter("limit_param", "INT64", int(limit)),
        bigquery.ScalarQueryParameter("offset_param", "INT64", int(offset)),
    ]
    if user_id is not None:
        where.append("userid = @user_id")
        params.append(bigquery.ScalarQueryParameter("user_id", "INT64", int(user_id)))
    if query_text:
        where.append(
            "("
            "LOWER(COALESCE(user_phone, '')) LIKE LOWER(@query_text) OR "
            "LOWER(COALESCE(user_name, '')) LIKE LOWER(@query_text) OR "
            "LOWER(COALESCE(user_email, '')) LIKE LOWER(@query_text)"
            ")"
        )
        params.append(bigquery.ScalarQueryParameter("query_text", "STRING", f"%{query_text}%"))

    where_sql = " AND ".join(where)
    query = f"""
        SELECT
          deletion_id, deleted_at, userid, deleted_by_userid, deletion_source,
          user_phone, user_name, user_email, signup_client, row_counts_json,
          backup_payload
        FROM {table}
        WHERE {where_sql}
        ORDER BY deleted_at DESC
        LIMIT @limit_param OFFSET @offset_param
    """
    count_query = f"SELECT COUNT(*) AS total FROM {table} WHERE {where_sql}"
    filter_params = [
        p for p in params
        if getattr(p, "name", "") not in ("limit_param", "offset_param")
    ]
    rows = list(client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params)))
    count_rows = list(client.query(count_query, job_config=bigquery.QueryJobConfig(query_parameters=filter_params)))

    def _serialize(v: Any) -> Any:
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        return v

    out = []
    for row in rows:
        d = dict(row)
        row_counts = {}
        payload = {}
        try:
            row_counts = json.loads(d.get("row_counts_json") or "{}")
        except Exception:
            row_counts = {}
        try:
            payload = json.loads(d.get("backup_payload") or "{}")
        except Exception:
            payload = {}
        out.append({
            "deletion_id": d.get("deletion_id"),
            "deleted_at": _serialize(d.get("deleted_at")),
            "userid": d.get("userid"),
            "deleted_by_userid": d.get("deleted_by_userid"),
            "deletion_source": d.get("deletion_source"),
            "user_phone": d.get("user_phone"),
            "user_name": d.get("user_name"),
            "user_email": d.get("user_email"),
            "signup_client": d.get("signup_client"),
            "row_counts": row_counts,
            "backup_payload": payload,
        })
    total = int(dict(count_rows[0]).get("total") or 0) if count_rows else 0
    return {"backups": out, "total": total, "limit": int(limit), "offset": int(offset)}
