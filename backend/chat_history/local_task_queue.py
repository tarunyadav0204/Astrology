from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

from db import execute, get_conn

logger = logging.getLogger(__name__)
_LOCAL_CHAT_TASK_QUEUE_SCHEMA_READY = False


def ensure_local_chat_task_queue_table(conn) -> None:
    global _LOCAL_CHAT_TASK_QUEUE_SCHEMA_READY
    if _LOCAL_CHAT_TASK_QUEUE_SCHEMA_READY:
        return
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS local_chat_task_queue (
            id SERIAL PRIMARY KEY,
            message_id INTEGER NOT NULL UNIQUE,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            attempts INTEGER NOT NULL DEFAULT 0,
            claim_id TEXT,
            claimed_at TIMESTAMP,
            last_error TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_local_chat_task_queue_status_created ON local_chat_task_queue (status, created_at)",
    )
    _LOCAL_CHAT_TASK_QUEUE_SCHEMA_READY = True


def enqueue_local_chat_task(*, message_id: int, payload: Dict[str, Any]) -> bool:
    try:
        with get_conn() as conn:
            ensure_local_chat_task_queue_table(conn)
            execute(
                conn,
                """
                INSERT INTO local_chat_task_queue (message_id, payload_json, status, attempts, claim_id, claimed_at, last_error, updated_at, completed_at)
                VALUES (%s, %s, 'queued', 0, NULL, NULL, NULL, CURRENT_TIMESTAMP, NULL)
                ON CONFLICT (message_id) DO UPDATE SET
                    payload_json = EXCLUDED.payload_json,
                    status = 'queued',
                    claim_id = NULL,
                    claimed_at = NULL,
                    last_error = NULL,
                    updated_at = CURRENT_TIMESTAMP,
                    completed_at = NULL
                """,
                (int(message_id), json.dumps(payload, ensure_ascii=False, default=str)),
            )
            conn.commit()
        logger.info("enqueued local chat task message_id=%s", message_id)
        return True
    except Exception as exc:
        logger.exception("failed to enqueue local chat task message_id=%s: %s", message_id, exc)
        return False


def claim_next_local_chat_task() -> Optional[Dict[str, Any]]:
    claim_id = str(uuid.uuid4())
    with get_conn() as conn:
        ensure_local_chat_task_queue_table(conn)
        cur = execute(
            conn,
            """
            WITH next_task AS (
                SELECT id
                FROM local_chat_task_queue
                WHERE status IN ('queued', 'failed')
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE local_chat_task_queue q
            SET status = 'processing',
                attempts = q.attempts + 1,
                claim_id = %s,
                claimed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            FROM next_task
            WHERE q.id = next_task.id
            RETURNING q.id, q.message_id, q.payload_json, q.attempts, q.claim_id
            """,
            (claim_id,),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        return None
    task_id, message_id, payload_json, attempts, row_claim_id = row
    payload = json.loads(payload_json)
    return {
        "id": task_id,
        "message_id": message_id,
        "payload": payload,
        "attempts": attempts,
        "claim_id": row_claim_id,
    }


def mark_local_chat_task_completed(task_id: int) -> None:
    with get_conn() as conn:
        ensure_local_chat_task_queue_table(conn)
        execute(
            conn,
            """
            UPDATE local_chat_task_queue
            SET status = 'completed',
                updated_at = CURRENT_TIMESTAMP,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (task_id,),
        )
        conn.commit()


def mark_local_chat_task_failed(task_id: int, error_message: str) -> None:
    with get_conn() as conn:
        ensure_local_chat_task_queue_table(conn)
        execute(
            conn,
            """
            UPDATE local_chat_task_queue
            SET status = 'failed',
                updated_at = CURRENT_TIMESTAMP,
                last_error = %s
            WHERE id = %s
            """,
            (str(error_message or "")[:4000], task_id),
        )
        conn.commit()
