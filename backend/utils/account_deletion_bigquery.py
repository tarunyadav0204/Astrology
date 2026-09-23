"""
Backup account-deletion snapshots to BigQuery before Postgres data is scrubbed.

The table stores one row per deletion request. Each row has quick admin/search
columns plus a JSON payload containing per-table row snapshots.
"""

from __future__ import annotations

import base64
import gzip
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_bq_client = None
_table_ensured = False

# Streaming insertAll rejects a request over 10 MB. Stay under that after JSON
# escaping, and use a load job only when one source row itself cannot.
_STREAMING_INSERT_LIMIT_BYTES = 8_500_000
_LOAD_JOB_LIMIT_BYTES = 95_000_000
_GZIP_PREFIX = "gz1:"


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


def _utf8_json_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


def encode_backup_payload(payload: Dict[str, Any]) -> str:
    """Store the snapshot compressed. Chat text shrinks enough to avoid multi-megabyte uploads."""
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    compressed = gzip.compress(raw, compresslevel=6)
    encoded = base64.b64encode(compressed).decode("ascii")
    if len(encoded) + len(_GZIP_PREFIX) < len(raw):
        return _GZIP_PREFIX + encoded
    return raw.decode("utf-8")


def decode_backup_payload(text: str) -> Dict[str, Any]:
    raw_text = text or ""
    if raw_text.startswith(_GZIP_PREFIX):
        decoded = gzip.decompress(base64.b64decode(raw_text[len(_GZIP_PREFIX):]))
        parsed = json.loads(decoded.decode("utf-8"))
    else:
        parsed = json.loads(raw_text or "{}")
    return parsed if isinstance(parsed, dict) else {}


def _backup_insert_row(
    *,
    snapshot: Dict[str, Any],
    deletion_id: str,
    deleted_at: str,
    deleted_by_userid: Optional[int],
    deletion_source: str,
    part_index: Optional[int] = None,
    part_count: Optional[int] = None,
) -> Dict[str, Any]:
    payload = dict(snapshot)
    if part_index is not None and part_count is not None:
        payload["_part"] = {"index": int(part_index), "count": int(part_count)}
    user_rows = (payload.get("tables") or {}).get("users") or []
    user_row = user_rows[0] if user_rows else {}
    return {
        "deletion_id": deletion_id,
        "deleted_at": deleted_at,
        "userid": int(snapshot.get("userid") or 0),
        "deleted_by_userid": int(deleted_by_userid) if deleted_by_userid is not None else None,
        "deletion_source": str(deletion_source or "unknown"),
        "user_phone": str(user_row.get("phone") or ""),
        "user_name": str(user_row.get("name") or ""),
        "user_email": str(user_row.get("email") or ""),
        "signup_client": str(user_row.get("signup_client") or ""),
        "row_counts_json": json.dumps(snapshot.get("row_counts") or {}, ensure_ascii=False),
        "backup_payload": encode_backup_payload(payload),
    }


def split_account_deletion_backup_rows(
    snapshot: Dict[str, Any],
    *,
    deletion_id: str,
    deleted_at: str,
    deleted_by_userid: Optional[int],
    deletion_source: str,
    max_bytes: int = _STREAMING_INSERT_LIMIT_BYTES,
) -> List[Dict[str, Any]]:
    """Split a snapshot into BigQuery rows that each fit a streaming insert.

    A single source row that is still too large is marked with ``_use_load_job``
    so the caller can append it with a load job (100 MB row limit) instead.
    """
    meta = dict(
        deletion_id=deletion_id,
        deleted_at=deleted_at,
        deleted_by_userid=deleted_by_userid,
        deletion_source=deletion_source,
    )
    whole = _backup_insert_row(snapshot=snapshot, **meta)
    if _utf8_json_size(whole) <= max_bytes:
        return [whole]

    raw_json = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
    stored = max(len(whole["backup_payload"]), 1)
    ratio = stored / max(len(raw_json), 1)
    raw_budget = max(1024, int(max_bytes / max(ratio, 0.05) * 0.7))
    shell = {key: value for key, value in snapshot.items() if key != "tables"}
    shell_size = _utf8_json_size({**shell, "tables": {}})
    pieces: List[Dict[str, List[Dict[str, Any]]]] = []
    current: Dict[str, List[Dict[str, Any]]] = {}
    current_size = shell_size

    def flush() -> None:
        nonlocal current, current_size
        if current:
            pieces.append(current)
        current = {}
        current_size = shell_size

    for table_name, rows in (snapshot.get("tables") or {}).items():
        rows = list(rows or [])
        key_overhead = _utf8_json_size(table_name) + 8
        batch: List[Dict[str, Any]] = []
        batch_size = 0
        for item in rows:
            item_size = _utf8_json_size(item) + 1
            projected = current_size + key_overhead + batch_size + item_size
            if batch and projected > raw_budget:
                current[table_name] = batch
                flush()
                batch = []
                batch_size = 0
            if not batch and current and (current_size + key_overhead + item_size) > raw_budget:
                flush()
            batch.append(item)
            batch_size += item_size
        if batch:
            if current and (current_size + key_overhead + batch_size) > raw_budget:
                flush()
            current[table_name] = batch
            current_size += key_overhead + batch_size
    flush()

    if not pieces:
        pieces = [{name: list(rows or []) for name, rows in (snapshot.get("tables") or {}).items()}]

    identity_rows = (snapshot.get("tables") or {}).get("users") or []
    identity = identity_rows[0] if identity_rows else {}
    rows_out: List[Dict[str, Any]] = []
    part_count = len(pieces)
    for index, tables in enumerate(pieces):
        part_snapshot = {**shell, "tables": tables}
        row = _backup_insert_row(
            snapshot=part_snapshot,
            part_index=index,
            part_count=part_count,
            **meta,
        )
        # The users table may sit in a different part from this chunk.
        if not row["user_phone"] and not row["user_name"] and not row["user_email"]:
            row["user_phone"] = str(identity.get("phone") or "")
            row["user_name"] = str(identity.get("name") or "")
            row["user_email"] = str(identity.get("email") or "")
            row["signup_client"] = str(identity.get("signup_client") or "")
        encoded = _utf8_json_size(row)
        if encoded > max_bytes:
            if encoded > _LOAD_JOB_LIMIT_BYTES:
                raise AccountDeletionBackupError(
                    "Account deletion backup has a single record larger than BigQuery can store "
                    f"({encoded} bytes)"
                )
            row["_use_load_job"] = True
        rows_out.append(row)
    return rows_out


def merge_account_deletion_payloads(payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Join part rows written by split_account_deletion_backup_rows back into one snapshot."""
    parsed = [payload for payload in payloads if isinstance(payload, dict)]
    if not parsed:
        return {}

    def _index(payload: Dict[str, Any]) -> int:
        part = payload.get("_part")
        if isinstance(part, dict):
            try:
                return int(part.get("index") or 0)
            except (TypeError, ValueError):
                return 0
        return 0

    ordered = sorted(parsed, key=_index)
    if len(ordered) == 1 and "_part" not in ordered[0]:
        return ordered[0]

    merged = {key: value for key, value in ordered[0].items() if key not in ("tables", "_part")}
    tables: Dict[str, Any] = {}
    for payload in ordered:
        for name, rows in (payload.get("tables") or {}).items():
            if isinstance(rows, list):
                tables.setdefault(name, []).extend(rows)
            elif name not in tables:
                tables[name] = rows
    merged["tables"] = tables
    if "row_counts" not in merged:
        merged["row_counts"] = {name: len(rows) if isinstance(rows, list) else 0 for name, rows in tables.items()}
    return merged


def _insert_backup_rows(client, table: str, rows: List[Dict[str, Any]]) -> None:
    if len(rows) <= 1:
        for row in rows:
            _insert_backup_row(client, table, row)
        return
    workers = min(4, len(rows))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_insert_backup_row, client, table, row) for row in rows]
        for future in futures:
            future.result()


def _insert_backup_row(client, table: str, row: Dict[str, Any]) -> None:
    use_load_job = bool(row.pop("_use_load_job", False))
    if not use_load_job:
        errors = client.insert_rows_json(table, [row])
        if errors:
            raise AccountDeletionBackupError(f"BigQuery insert failed: {errors}")
        return

    from google.cloud import bigquery

    job = client.load_table_from_json(
        [row],
        table,
        job_config=bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND),
    )
    job.result(timeout=180)
    if job.errors:
        raise AccountDeletionBackupError(f"BigQuery load failed: {job.errors}")


def upload_account_deletion_snapshot(
    snapshot: Dict[str, Any],
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

    deletion_id = f"acctdel_{userid}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    deleted_at = datetime.now(timezone.utc).isoformat()
    rows = split_account_deletion_backup_rows(
        snapshot,
        deletion_id=deletion_id,
        deleted_at=deleted_at,
        deleted_by_userid=deleted_by_userid,
        deletion_source=deletion_source,
    )
    payload_bytes = sum(len(str(row.get("backup_payload") or "")) for row in rows)
    logger.info(
        "account_deletion_bigquery: userid=%s backup %s part(s), %s bytes",
        userid,
        len(rows),
        payload_bytes,
    )
    try:
        _insert_backup_rows(client, table, rows)
        return deletion_id
    except AccountDeletionBackupError:
        raise
    except Exception as exc:
        raise AccountDeletionBackupError(f"BigQuery account deletion backup failed: {exc}") from exc


def backup_user_deletion_to_bigquery(
    conn,
    *,
    userid: int,
    deleted_by_userid: Optional[int],
    deletion_source: str,
) -> str:
    snapshot = build_account_deletion_snapshot(conn, userid)
    return upload_account_deletion_snapshot(
        snapshot,
        userid=userid,
        deleted_by_userid=deleted_by_userid,
        deletion_source=deletion_source,
    )


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
          deletion_id,
          MIN(deleted_at) AS deleted_at,
          ANY_VALUE(userid) AS userid,
          ANY_VALUE(deleted_by_userid) AS deleted_by_userid,
          ANY_VALUE(deletion_source) AS deletion_source,
          ANY_VALUE(user_phone) AS user_phone,
          ANY_VALUE(user_name) AS user_name,
          ANY_VALUE(user_email) AS user_email,
          ANY_VALUE(signup_client) AS signup_client,
          ANY_VALUE(row_counts_json) AS row_counts_json
        FROM {table}
        WHERE {where_sql}
        GROUP BY deletion_id
        ORDER BY deleted_at DESC
        LIMIT @limit_param OFFSET @offset_param
    """
    count_query = f"SELECT COUNT(DISTINCT deletion_id) AS total FROM {table} WHERE {where_sql}"
    filter_params = [
        p for p in params
        if getattr(p, "name", "") not in ("limit_param", "offset_param")
    ]
    rows = list(client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params)))
    count_rows = list(client.query(count_query, job_config=bigquery.QueryJobConfig(query_parameters=filter_params)))
    deletion_ids = [dict(row).get("deletion_id") for row in rows if dict(row).get("deletion_id")]
    payloads_by_id: Dict[str, List[Dict[str, Any]]] = {deletion_id: [] for deletion_id in deletion_ids}
    if deletion_ids:
        payload_query = f"""
            SELECT deletion_id, backup_payload
            FROM {table}
            WHERE deletion_id IN UNNEST(@deletion_ids)
        """
        payload_rows = client.query(
            payload_query,
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ArrayQueryParameter("deletion_ids", "STRING", deletion_ids),
            ]),
        )
        for payload_row in payload_rows:
            item = dict(payload_row)
            deletion_id = item.get("deletion_id")
            try:
                parsed = decode_backup_payload(item.get("backup_payload") or "")
            except Exception:
                parsed = {}
            if deletion_id in payloads_by_id and isinstance(parsed, dict):
                payloads_by_id[deletion_id].append(parsed)

    def _serialize(v: Any) -> Any:
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        return v

    out = []
    for row in rows:
        d = dict(row)
        row_counts = {}
        try:
            row_counts = json.loads(d.get("row_counts_json") or "{}")
        except Exception:
            row_counts = {}
        payload = merge_account_deletion_payloads(payloads_by_id.get(d.get("deletion_id")) or [])
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
