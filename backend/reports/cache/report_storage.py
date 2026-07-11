from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from db import execute

from ..constants import REPORT_CACHE_TABLE


def ensure_report_cache_table(conn: Any, execute_fn=execute) -> None:
    execute_fn(
        conn,
        f"""
        CREATE TABLE IF NOT EXISTS {REPORT_CACHE_TABLE} (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            subject_hash TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'english',
            report_version TEXT NOT NULL,
            report_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, report_type, subject_hash, language, report_version)
        )
        """,
        )


def ensure_report_jobs_table(conn: Any, execute_fn=execute) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS report_generation_jobs (
            report_id TEXT PRIMARY KEY,
            userid INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            subject_hash TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'english',
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
            request_json TEXT NOT NULL,
            result_data TEXT,
            error_message TEXT,
            report_version TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
        """,
    )
    execute_fn(conn, "CREATE INDEX IF NOT EXISTS idx_report_jobs_user ON report_generation_jobs (userid)")
    execute_fn(conn, "CREATE INDEX IF NOT EXISTS idx_report_jobs_status ON report_generation_jobs (status)")


def create_report_job(
    report_id: str,
    userid: int,
    report_type: str,
    subject_hash: str,
    language: str,
    request_json: str,
    report_version: str,
    get_conn: Any,
    execute_fn=execute,
) -> None:
    with get_conn() as conn:
        ensure_report_jobs_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            INSERT INTO report_generation_jobs (report_id, userid, report_type, subject_hash, language, status, request_json, report_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (report_id, userid, report_type, subject_hash, language, "pending", request_json, report_version),
        )
        conn.commit()


def update_report_job(
    report_id: str,
    *,
    status: str,
    result_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    get_conn: Any,
    execute_fn=execute,
) -> None:
    with get_conn() as conn:
        ensure_report_jobs_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            UPDATE report_generation_jobs
            SET status = %s,
                result_data = %s,
                error_message = %s,
                started_at = CASE WHEN %s = 'processing' AND started_at IS NULL THEN %s ELSE started_at END,
                completed_at = CASE WHEN %s IN ('completed', 'failed') THEN %s ELSE completed_at END
            WHERE report_id = %s
            """,
            (
                status,
                json.dumps(result_data, default=str) if result_data is not None else None,
                error_message,
                status,
                datetime.now(),
                status,
                datetime.now(),
                report_id,
            ),
        )
        conn.commit()


def get_report_job(report_id: str, get_conn: Any, execute_fn=execute) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_report_jobs_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT report_id, userid, report_type, subject_hash, language, status, request_json, result_data, error_message, report_version, created_at, started_at, completed_at
            FROM report_generation_jobs
            WHERE report_id = %s
            """,
            (report_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    keys = [
        "report_id",
        "userid",
        "report_type",
        "subject_hash",
        "language",
        "status",
        "request_json",
        "result_data",
        "error_message",
        "report_version",
        "created_at",
        "started_at",
        "completed_at",
    ]
    out = dict(zip(keys, row))
    if out.get("result_data"):
        try:
            out["result_data"] = json.loads(out["result_data"]) if isinstance(out["result_data"], str) else out["result_data"]
        except Exception:
            pass
    return out


def get_cached_report(userid: int, report_type: str, subject_hash: str, language: str, report_version: str, get_conn: Any, execute_fn=execute) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_report_cache_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            f"""
            SELECT report_data
            FROM {REPORT_CACHE_TABLE}
            WHERE userid = %s AND report_type = %s AND subject_hash = %s AND language = %s AND report_version = %s
            """,
            (userid, report_type, subject_hash, language, report_version),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


def upsert_report_cache(
    userid: int,
    report_type: str,
    subject_hash: str,
    language: str,
    report_version: str,
    payload: Dict[str, Any],
    get_conn: Any,
    execute_fn=execute,
) -> None:
    with get_conn() as conn:
        ensure_report_cache_table(conn, execute_fn)
        execute_fn(
            conn,
            f"""
            INSERT INTO {REPORT_CACHE_TABLE} (userid, report_type, subject_hash, language, report_version, report_data, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (userid, report_type, subject_hash, language, report_version)
            DO UPDATE SET report_data = EXCLUDED.report_data,
                          updated_at = EXCLUDED.updated_at
            """,
            (userid, report_type, subject_hash, language, report_version, json.dumps(payload, default=str)),
        )
        conn.commit()
