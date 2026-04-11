"""DB rows for async Ashtakavarga life-predictions jobs (client polls status)."""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from db import execute


def ensure_life_prediction_jobs_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ashtakavarga_life_prediction_jobs (
            job_id TEXT PRIMARY KEY,
            userid INTEGER NOT NULL,
            birth_hash TEXT NOT NULL,
            birth_data_json TEXT NOT NULL,
            prediction_cost INTEGER NOT NULL,
            force_regenerate BOOLEAN NOT NULL DEFAULT FALSE,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
            result_payload TEXT,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ
        )
        """,
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_av_lp_jobs_user ON ashtakavarga_life_prediction_jobs (userid)",
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_av_lp_jobs_created ON ashtakavarga_life_prediction_jobs (created_at)",
    )


def insert_life_prediction_job(
    conn,
    job_id: str,
    userid: int,
    birth_hash: str,
    birth_data_dict: Dict[str, Any],
    prediction_cost: int,
    force_regenerate: bool,
) -> None:
    execute(
        conn,
        """
        INSERT INTO ashtakavarga_life_prediction_jobs
        (job_id, userid, birth_hash, birth_data_json, prediction_cost, force_regenerate, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            job_id,
            userid,
            birth_hash,
            json.dumps(birth_data_dict, default=str),
            prediction_cost,
            force_regenerate,
        ),
    )


def fetch_job_for_user(conn, job_id: str, userid: int):
    cur = execute(
        conn,
        """
        SELECT status, result_payload, error_message, started_at, completed_at
        FROM ashtakavarga_life_prediction_jobs
        WHERE job_id = ? AND userid = ?
        """,
        (job_id, userid),
    )
    return cur.fetchone()


def update_job_processing(conn, job_id: str) -> None:
    execute(
        conn,
        """
        UPDATE ashtakavarga_life_prediction_jobs
        SET status = 'processing', started_at = ?
        WHERE job_id = ?
        """,
        (datetime.now(), job_id),
    )


def update_job_completed(conn, job_id: str, payload: Dict[str, Any]) -> None:
    execute(
        conn,
        """
        UPDATE ashtakavarga_life_prediction_jobs
        SET status = 'completed', result_payload = ?, completed_at = ?, error_message = NULL
        WHERE job_id = ?
        """,
        (json.dumps(payload, default=str), datetime.now(), job_id),
    )


def update_job_failed(
    conn, job_id: str, error_message: str, result_payload: Optional[Dict[str, Any]] = None
) -> None:
    msg = (error_message or "")[:8000]
    rp = json.dumps(result_payload, default=str) if result_payload is not None else None
    execute(
        conn,
        """
        UPDATE ashtakavarga_life_prediction_jobs
        SET status = 'failed', error_message = ?, completed_at = ?, result_payload = ?
        WHERE job_id = ?
        """,
        (msg, datetime.now(), rp, job_id),
    )
