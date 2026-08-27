"""Isolated, durable WhatsApp delivery for targeted credit campaigns."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from db import execute
from whatsapp.messaging import send_whatsapp_template

from . import db

logger = logging.getLogger(__name__)


def ensure_credit_campaign_whatsapp_tables(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_campaign_whatsapp_jobs (
            job_id TEXT PRIMARY KEY,
            credit_campaign_id BIGINT NOT NULL,
            campaign_json TEXT NOT NULL,
            template_name TEXT NOT NULL,
            template_language TEXT NOT NULL,
            template_json TEXT NOT NULL,
            phone_number_id TEXT NOT NULL,
            include_unlinked BOOLEAN NOT NULL DEFAULT FALSE,
            status TEXT NOT NULL DEFAULT 'queued',
            total INTEGER NOT NULL DEFAULT 0,
            accepted INTEGER NOT NULL DEFAULT 0,
            failed INTEGER NOT NULL DEFAULT 0,
            skipped INTEGER NOT NULL DEFAULT 0,
            enqueued_batches INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            created_by INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_campaign_whatsapp_recipients (
            job_id TEXT NOT NULL REFERENCES credit_campaign_whatsapp_jobs(job_id) ON DELETE CASCADE,
            userid INTEGER NOT NULL,
            state TEXT NOT NULL DEFAULT 'queued',
            recipient_status TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            claimed_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            last_error TEXT,
            meta_message_id TEXT,
            meta_recipient_id TEXT,
            meta_status TEXT,
            meta_accepted_at TIMESTAMPTZ,
            meta_sent_at TIMESTAMPTZ,
            meta_delivered_at TIMESTAMPTZ,
            meta_read_at TIMESTAMPTZ,
            meta_failed_at TIMESTAMPTZ,
            meta_error TEXT,
            meta_status_updated_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (job_id, userid)
        )
        """,
    )
    for column in (
        "meta_message_id TEXT",
        "meta_recipient_id TEXT",
        "meta_status TEXT",
        "meta_accepted_at TIMESTAMPTZ",
        "meta_sent_at TIMESTAMPTZ",
        "meta_delivered_at TIMESTAMPTZ",
        "meta_read_at TIMESTAMPTZ",
        "meta_failed_at TIMESTAMPTZ",
        "meta_error TEXT",
        "meta_status_updated_at TIMESTAMPTZ",
    ):
        execute(
            conn,
            f"ALTER TABLE credit_campaign_whatsapp_recipients ADD COLUMN IF NOT EXISTS {column}",
        )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_campaign_whatsapp_pending_statuses (
            meta_message_id TEXT NOT NULL,
            meta_status TEXT NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL,
            recipient_id TEXT,
            error TEXT,
            received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (meta_message_id, meta_status, occurred_at)
        )
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_credit_campaign_wa_pending_received
        ON credit_campaign_whatsapp_pending_statuses (received_at)
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_credit_campaign_wa_jobs_campaign
        ON credit_campaign_whatsapp_jobs (credit_campaign_id, created_at DESC)
        """,
    )
    execute(
        conn,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_campaign_wa_recipients_wamid
        ON credit_campaign_whatsapp_recipients (meta_message_id)
        WHERE meta_message_id IS NOT NULL
        """,
    )
    execute(
        conn,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_campaign_wa_jobs_one_active
        ON credit_campaign_whatsapp_jobs (credit_campaign_id)
        WHERE status IN ('queued', 'running')
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_credit_campaign_wa_recipients_work
        ON credit_campaign_whatsapp_recipients (job_id, state, claimed_at)
        """,
    )


def _json(value: Any) -> Dict[str, Any]:
    try:
        parsed = json.loads(value or "{}") if isinstance(value, str) else value
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _job_dict(row: Any) -> Dict[str, Any]:
    return {
        "job_id": str(row[0]),
        "campaign_id": int(row[1]),
        "campaign": _json(row[2]),
        "template_name": str(row[3]),
        "template_language": str(row[4]),
        "status": str(row[5]),
        "total": int(row[6] or 0),
        "accepted": int(row[7] or 0),
        "failed": int(row[8] or 0),
        "skipped": int(row[9] or 0),
        "enqueued_batches": int(row[10] or 0),
        "error": row[11],
        "created_at": row[12].isoformat() if row[12] else None,
        "started_at": row[13].isoformat() if row[13] else None,
        "completed_at": row[14].isoformat() if row[14] else None,
    }


_JOB_SELECT = """
    SELECT job_id, credit_campaign_id, campaign_json, template_name,
           template_language, status, total, accepted, failed, skipped,
           enqueued_batches, error, created_at, started_at, completed_at
    FROM credit_campaign_whatsapp_jobs
"""


def _provider_status(row: Dict[str, Any]) -> str:
    if row.get("meta_read_at"):
        return "read"
    if row.get("meta_delivered_at"):
        return "delivered"
    if row.get("meta_failed_at"):
        return "failed"
    if row.get("meta_sent_at"):
        return "sent"
    return str(row.get("meta_status") or row.get("state") or "pending")


def _delivery_metrics(rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    values = list(rows)
    return {
        "accepted": sum(1 for row in values if row.get("state") == "accepted" or row.get("meta_accepted_at")),
        "sent": sum(1 for row in values if row.get("meta_sent_at") or row.get("meta_delivered_at") or row.get("meta_read_at")),
        "delivered": sum(1 for row in values if row.get("meta_delivered_at") or row.get("meta_read_at")),
        "read": sum(1 for row in values if row.get("meta_read_at")),
        "meta_failed": sum(
            1 for row in values
            if row.get("meta_failed_at") and not row.get("meta_delivered_at") and not row.get("meta_read_at")
        ),
        "legacy_accepted": sum(
            1 for row in values
            if row.get("state") == "accepted" and not row.get("meta_message_id")
        ),
    }


def _delivery_rows(conn, job_ids: Iterable[str]) -> List[Dict[str, Any]]:
    ids = [str(value) for value in job_ids if str(value)]
    if not ids:
        return []
    rows = execute(
        conn,
        """
        SELECT job_id, userid, state, recipient_status, last_error,
               meta_message_id, meta_recipient_id, meta_status,
               meta_accepted_at, meta_sent_at, meta_delivered_at,
               meta_read_at, meta_failed_at, meta_error,
               completed_at, updated_at
        FROM credit_campaign_whatsapp_recipients
        WHERE job_id = ANY(%s)
        ORDER BY userid
        """,
        (ids,),
    ).fetchall()
    return [
        {
            "job_id": str(row[0]),
            "userid": int(row[1]),
            "state": str(row[2] or "pending"),
            "recipient_status": row[3],
            "last_error": row[4],
            "meta_message_id": row[5],
            "meta_recipient_id": row[6],
            "meta_status": row[7],
            "meta_accepted_at": row[8],
            "meta_sent_at": row[9],
            "meta_delivered_at": row[10],
            "meta_read_at": row[11],
            "meta_failed_at": row[12],
            "meta_error": row[13],
            "completed_at": row[14],
            "updated_at": row[15],
        }
        for row in (rows or [])
    ]


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def get_credit_campaign_whatsapp_delivery_report(campaign_id: int) -> Dict[str, Any]:
    """Latest send-job lifecycle report; old jobs remain legacy accepted/failed."""
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        job_row = execute(
            conn,
            f"{_JOB_SELECT} WHERE credit_campaign_id = %s ORDER BY created_at DESC LIMIT 1",
            (int(campaign_id),),
        ).fetchone()
        if not job_row:
            return {"job": None, "metrics": {}, "recipients": {}}
        job = _job_dict(job_row)
        rows = _delivery_rows(conn, [job["job_id"]])
        recipients: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            recipients[row["userid"]] = {
                "send_state": row["state"],
                "recipient_status": row["recipient_status"],
                "send_error": row["meta_error"] or row["last_error"],
                "meta_message_id": row["meta_message_id"],
                "meta_status": _provider_status(row),
                "meta_tracking_available": bool(row["meta_message_id"]),
                "accepted_at": _iso(row["meta_accepted_at"] or row["completed_at"]),
                "sent_at": _iso(row["meta_sent_at"]),
                "delivered_at": _iso(row["meta_delivered_at"]),
                "read_at": _iso(row["meta_read_at"]),
                "failed_at": _iso(row["meta_failed_at"]),
            }
        metrics = _delivery_metrics(rows)
        job["meta_metrics"] = metrics
        return {"job": job, "metrics": metrics, "recipients": recipients}


def extract_meta_whatsapp_status_updates(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract Cloud API message lifecycle events from a signed webhook body."""
    updates: List[Dict[str, Any]] = []
    for entry in payload.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict) or change.get("field") != "messages":
                continue
            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue
            for status_row in value.get("statuses") or []:
                if not isinstance(status_row, dict):
                    continue
                message_id = str(status_row.get("id") or "").strip()
                status = str(status_row.get("status") or "").strip().lower()
                if not message_id or status not in {"sent", "delivered", "read", "failed"}:
                    continue
                try:
                    occurred_at = datetime.fromtimestamp(
                        int(status_row.get("timestamp")),
                        tz=timezone.utc,
                    )
                except (TypeError, ValueError, OverflowError):
                    occurred_at = datetime.now(timezone.utc)
                errors = status_row.get("errors") or []
                updates.append(
                    {
                        "message_id": message_id,
                        "recipient_id": str(status_row.get("recipient_id") or "").strip() or None,
                        "status": status,
                        "occurred_at": occurred_at,
                        "error": json.dumps(errors, default=str)[:4000] if errors else None,
                    }
                )
    return updates


_META_STATUS_TIMESTAMP_COLUMNS = {
        "sent": "meta_sent_at",
        "delivered": "meta_delivered_at",
        "read": "meta_read_at",
        "failed": "meta_failed_at",
}


def _apply_meta_status_update(conn, update: Dict[str, Any]) -> int:
    status = update["status"]
    timestamp_column = _META_STATUS_TIMESTAMP_COLUMNS[status]
    cursor = execute(
        conn,
        f"""
        UPDATE credit_campaign_whatsapp_recipients
        SET meta_recipient_id = COALESCE(%s, meta_recipient_id),
            {timestamp_column} = COALESCE({timestamp_column}, %s),
            meta_status = CASE
                WHEN %s = 'read' THEN 'read'
                WHEN %s = 'delivered' AND COALESCE(meta_status, '') <> 'read' THEN 'delivered'
                WHEN %s = 'sent' AND COALESCE(meta_status, '') NOT IN ('delivered', 'read', 'failed') THEN 'sent'
                WHEN %s = 'failed' AND COALESCE(meta_status, '') NOT IN ('delivered', 'read') THEN 'failed'
                ELSE COALESCE(meta_status, 'accepted')
            END,
            meta_error = CASE WHEN %s = 'failed' THEN COALESCE(%s, meta_error) ELSE meta_error END,
            meta_status_updated_at = GREATEST(
                COALESCE(meta_status_updated_at, %s),
                %s
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE meta_message_id = %s
        """,
        (
            update["recipient_id"], update["occurred_at"],
            status, status, status, status,
            status, update["error"],
            update["occurred_at"], update["occurred_at"],
            update["message_id"],
        ),
    )
    return max(0, int(getattr(cursor, "rowcount", 0) or 0))


def _reconcile_pending_meta_statuses(conn, message_ids: Iterable[str]) -> int:
    ids = sorted({str(value) for value in message_ids if str(value)})
    if not ids:
        return 0
    pending = execute(
        conn,
        """
        SELECT meta_message_id, meta_status, occurred_at, recipient_id, error
        FROM credit_campaign_whatsapp_pending_statuses
        WHERE meta_message_id = ANY(%s)
        ORDER BY occurred_at
        """,
        (ids,),
    ).fetchall()
    matched = 0
    for row in pending or []:
        matched += _apply_meta_status_update(
            conn,
            {
                "message_id": str(row[0]),
                "status": str(row[1]),
                "occurred_at": row[2],
                "recipient_id": row[3],
                "error": row[4],
            },
        )
    if pending:
        execute(
            conn,
            "DELETE FROM credit_campaign_whatsapp_pending_statuses WHERE meta_message_id = ANY(%s)",
            (ids,),
        )
    return matched


def record_meta_whatsapp_status_updates(payload: Dict[str, Any]) -> Dict[str, int]:
    """Apply campaign statuses or buffer events that beat wamid persistence."""
    updates = extract_meta_whatsapp_status_updates(payload)
    if not updates:
        return {"received": 0, "matched": 0, "buffered": 0}
    matched = 0
    buffered = 0
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        for update in updates:
            applied = _apply_meta_status_update(conn, update)
            matched += applied
            if applied:
                continue
            execute(
                conn,
                """
                INSERT INTO credit_campaign_whatsapp_pending_statuses
                  (meta_message_id, meta_status, occurred_at, recipient_id, error)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    update["message_id"],
                    update["status"],
                    update["occurred_at"],
                    update["recipient_id"],
                    update["error"],
                ),
            )
            buffered += 1
        execute(
            conn,
            """
            DELETE FROM credit_campaign_whatsapp_pending_statuses
            WHERE received_at < CURRENT_TIMESTAMP - INTERVAL '2 days'
            """,
        )
        conn.commit()
    return {"received": len(updates), "matched": matched, "buffered": buffered}


def _expire_stale_jobs(conn) -> bool:
    try:
        configured_timeout = int(os.getenv("WHATSAPP_CAMPAIGN_JOB_TIMEOUT_MINUTES", "120") or "120")
    except (TypeError, ValueError):
        configured_timeout = 120
    timeout_minutes = max(30, min(configured_timeout, 1440))
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
    stale_rows = execute(
        conn,
        """
        SELECT job_id FROM credit_campaign_whatsapp_jobs
        WHERE status IN ('queued', 'running') AND updated_at < %s
        FOR UPDATE SKIP LOCKED
        """,
        (cutoff,),
    ).fetchall()
    stale_ids = [str(row[0]) for row in (stale_rows or [])]
    if not stale_ids:
        return False
    execute(
        conn,
        """
        UPDATE credit_campaign_whatsapp_recipients
        SET state = 'failed', last_error = 'Worker job timed out',
            completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE job_id = ANY(%s) AND state IN ('queued', 'retry', 'processing')
        """,
        (stale_ids,),
    )
    for stale_id in stale_ids:
        _refresh_job(conn, stale_id)
        execute(
            conn,
            """
            UPDATE credit_campaign_whatsapp_jobs
            SET status = 'failed', error = 'Isolated worker job timed out',
                completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = %s
            """,
            (stale_id,),
        )
    return True


def create_credit_campaign_whatsapp_job(
    *,
    job_id: str,
    campaign: Dict[str, Any],
    template: Dict[str, Any],
    phone_number_id: str,
    include_unlinked: bool,
    tokens_by_user: Dict[int, str],
    created_by: int,
) -> Dict[str, Any]:
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        execute(
            conn,
            """
            INSERT INTO credit_campaign_whatsapp_jobs
              (job_id, credit_campaign_id, campaign_json, template_name,
               template_language, template_json, phone_number_id,
               include_unlinked, total, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(job_id), int(campaign["id"]), json.dumps(campaign, default=str),
                str(template.get("name") or ""), str(template.get("language") or ""),
                json.dumps(template, default=str), str(phone_number_id), bool(include_unlinked),
                len(tokens_by_user), int(created_by),
            ),
        )
        for userid in tokens_by_user:
            execute(
                conn,
                """
                INSERT INTO credit_campaign_whatsapp_recipients (job_id, userid)
                VALUES (%s, %s) ON CONFLICT DO NOTHING
                """,
                (str(job_id), int(userid)),
            )
        conn.commit()
    return get_credit_campaign_whatsapp_job(job_id) or {}


def get_credit_campaign_whatsapp_job(
    job_id: str,
    *,
    include_issues: bool = False,
) -> Optional[Dict[str, Any]]:
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        if _expire_stale_jobs(conn):
            conn.commit()
        row = execute(conn, f"{_JOB_SELECT} WHERE job_id = %s", (str(job_id),)).fetchone()
        if not row:
            return None
        job = _job_dict(row)
        delivery_rows = _delivery_rows(conn, [job["job_id"]])
        job["meta_metrics"] = _delivery_metrics(delivery_rows)
        if include_issues:
            issues = execute(
                conn,
                """
                SELECT userid, state, recipient_status, last_error
                FROM credit_campaign_whatsapp_recipients
                WHERE job_id = %s AND state IN ('failed', 'skipped')
                ORDER BY userid LIMIT 200
                """,
                (str(job_id),),
            ).fetchall()
            job["issues"] = [
                {
                    "user_id": int(issue[0]),
                    "status": str(issue[1]),
                    "reason": str(issue[2] or ""),
                    "error": str(issue[3] or ""),
                }
                for issue in (issues or [])
            ]
            job["issues_truncated"] = (job["failed"] + job["skipped"]) > len(job["issues"])
        return job


def active_credit_campaign_whatsapp_job(campaign_id: int) -> Optional[Dict[str, Any]]:
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        if _expire_stale_jobs(conn):
            conn.commit()
        row = execute(
            conn,
            f"""
            {_JOB_SELECT}
            WHERE credit_campaign_id = %s AND status IN ('queued', 'running')
            ORDER BY created_at DESC LIMIT 1
            """,
            (int(campaign_id),),
        ).fetchone()
        return _job_dict(row) if row else None


def latest_credit_campaign_whatsapp_jobs(campaign_ids: Iterable[int]) -> Dict[int, Dict[str, Any]]:
    ids = sorted({int(value) for value in campaign_ids})
    if not ids:
        return {}
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        if _expire_stale_jobs(conn):
            conn.commit()
        rows = execute(
            conn,
            f"""
            SELECT DISTINCT ON (credit_campaign_id)
                   job_id, credit_campaign_id, campaign_json, template_name,
                   template_language, status, total, accepted, failed, skipped,
                   enqueued_batches, error, created_at, started_at, completed_at
            FROM credit_campaign_whatsapp_jobs
            WHERE credit_campaign_id = ANY(%s)
            ORDER BY credit_campaign_id, created_at DESC
            """,
            (ids,),
        ).fetchall()
        jobs = {int(row[1]): _job_dict(row) for row in (rows or [])}
        delivery_rows = _delivery_rows(conn, [job["job_id"] for job in jobs.values()])
        rows_by_job: Dict[str, List[Dict[str, Any]]] = {}
        for delivery_row in delivery_rows:
            rows_by_job.setdefault(delivery_row["job_id"], []).append(delivery_row)
        for job in jobs.values():
            job["meta_metrics"] = _delivery_metrics(rows_by_job.get(job["job_id"], []))
        return jobs


def set_job_enqueue_result(
    job_id: str,
    *,
    enqueued_batches: int,
    failed_userids: Optional[Iterable[int]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    failed_ids = sorted({int(value) for value in (failed_userids or [])})
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        if failed_ids:
            execute(
                conn,
                """
                UPDATE credit_campaign_whatsapp_recipients
                SET state = 'failed', last_error = %s, completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s AND userid = ANY(%s) AND state = 'queued'
                """,
                ((error or "Could not enqueue worker task")[:1000], str(job_id), failed_ids),
            )
        execute(
            conn,
            """
            UPDATE credit_campaign_whatsapp_jobs
            SET enqueued_batches = %s, error = %s, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = %s
            """,
            (int(enqueued_batches), (error or "")[:1000] or None, str(job_id)),
        )
        _refresh_job(conn, str(job_id))
        conn.commit()
    return get_credit_campaign_whatsapp_job(job_id) or {}


def _claim_recipients(conn, job_id: str, user_ids: List[int]) -> List[Dict[str, Any]]:
    rows = execute(
        conn,
        """
        SELECT userid, attempt_count
        FROM credit_campaign_whatsapp_recipients
        WHERE job_id = %s AND userid = ANY(%s)
          AND (
            state IN ('queued', 'retry')
            OR (state = 'processing' AND claimed_at < CURRENT_TIMESTAMP - INTERVAL '5 minutes')
          )
        FOR UPDATE SKIP LOCKED
        """,
        (str(job_id), user_ids),
    ).fetchall()
    claimed = []
    for userid, attempt_count in rows or []:
        execute(
            conn,
            """
            UPDATE credit_campaign_whatsapp_recipients
            SET state = 'processing', attempt_count = attempt_count + 1,
                claimed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = %s AND userid = %s
            """,
            (str(job_id), int(userid)),
        )
        claimed.append({
            "userid": int(userid),
            "attempt_count": int(attempt_count or 0) + 1,
        })
    if claimed:
        execute(
            conn,
            """
            UPDATE credit_campaign_whatsapp_jobs
            SET status = 'running', started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = %s
            """,
            (str(job_id),),
        )
    return claimed


def _digits(value: Any) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits if 8 <= len(digits) <= 15 else ""


def _resolve_from_replica(user_ids: List[int]) -> Dict[int, Dict[str, str]]:
    with db.get_read_conn() as conn:
        rows = execute(
            conn,
            """
            SELECT userid, COALESCE(name, ''), COALESCE(phone::text, ''),
                   COALESCE(whatsapp_wa_id, '')
            FROM users WHERE userid = ANY(%s)
            """,
            (user_ids,),
        ).fetchall()
    return {
        int(row[0]): {
            "name": str(row[1] or ""),
            "phone": _digits(row[2]),
            "whatsapp": _digits(row[3]),
        }
        for row in (rows or [])
    }


def _retryable_provider_error(error: Optional[str]) -> bool:
    message = str(error or "").lower()
    if message.startswith("meta 4") and not message.startswith(("meta 408", "meta 429")):
        return False
    permanent = ("missing recipient", "missing whatsapp_access_token", "phone_number_id")
    return not any(value in message for value in permanent)


def _refresh_job(conn, job_id: str) -> None:
    row = execute(
        conn,
        """
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE state = 'accepted'),
               COUNT(*) FILTER (WHERE state = 'failed'),
               COUNT(*) FILTER (WHERE state = 'skipped'),
               COUNT(*) FILTER (WHERE state IN ('queued', 'retry', 'processing'))
        FROM credit_campaign_whatsapp_recipients WHERE job_id = %s
        """,
        (str(job_id),),
    ).fetchone()
    total, accepted, failed, skipped, pending = [int(value or 0) for value in row]
    started_row = execute(
        conn,
        "SELECT started_at FROM credit_campaign_whatsapp_jobs WHERE job_id = %s",
        (str(job_id),),
    ).fetchone()
    status = "running" if started_row and started_row[0] else "queued"
    completed_at = None
    if pending == 0:
        status = "completed" if failed == 0 else "completed_with_errors"
        completed_at = datetime.now(timezone.utc)
    execute(
        conn,
        """
        UPDATE credit_campaign_whatsapp_jobs
        SET status = %s, total = %s, accepted = %s, failed = %s, skipped = %s,
            completed_at = %s, updated_at = CURRENT_TIMESTAMP
        WHERE job_id = %s
        """,
        (status, total, accepted, failed, skipped, completed_at, str(job_id)),
    )


def process_credit_campaign_whatsapp_batch(*, job_id: str, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolve on the replica, call Meta without DB connections, then persist once."""
    tokens_by_user: Dict[int, str] = {}
    for value in recipients or []:
        if not isinstance(value, dict):
            continue
        try:
            uid = int(value.get("user_id"))
        except (TypeError, ValueError):
            continue
        token = str(value.get("secure_token") or "").strip()
        if uid > 0 and token:
            tokens_by_user[uid] = token
    clean_ids = sorted(tokens_by_user)
    if not clean_ids:
        return {"ok": True, "job_id": str(job_id), "processed": 0}
    with db.get_conn() as conn:
        ensure_credit_campaign_whatsapp_tables(conn)
        job_row = execute(
            conn,
            """
            SELECT campaign_json, template_json, template_name, template_language,
                   phone_number_id, include_unlinked, status
            FROM credit_campaign_whatsapp_jobs WHERE job_id = %s
            """,
            (str(job_id),),
        ).fetchone()
        if not job_row:
            return {"ok": True, "job_id": str(job_id), "skipped": "missing_job"}
        if str(job_row[6]) in {"completed", "completed_with_errors", "cancelled"}:
            return {"ok": True, "job_id": str(job_id), "skipped": "terminal_job"}
        claimed = _claim_recipients(conn, str(job_id), clean_ids)
        conn.commit()
    if not claimed:
        with db.get_conn() as conn:
            processing = execute(
                conn,
                """
                SELECT COUNT(*) FROM credit_campaign_whatsapp_recipients
                WHERE job_id = %s AND userid = ANY(%s) AND state = 'processing'
                """,
                (str(job_id), clean_ids),
            ).fetchone()
        if processing and int(processing[0] or 0) > 0:
            # A prior execution died or is still in flight. Keep the Cloud Task
            # retrying until the lease becomes stale instead of acknowledging
            # and silently abandoning the batch.
            raise RuntimeError("WhatsApp batch is already processing; retry after claim lease")
        return {"ok": True, "job_id": str(job_id), "processed": 0, "deduped": len(clean_ids)}

    campaign = _json(job_row[0])
    template = _json(job_row[1])
    template_name = str(job_row[2])
    language = str(job_row[3])
    phone_number_id = str(job_row[4])
    include_unlinked = bool(job_row[5])
    try:
        configured_attempts = int(os.getenv("WHATSAPP_CAMPAIGN_MAX_ATTEMPTS", "5") or "5")
    except (TypeError, ValueError):
        configured_attempts = 5
    max_attempts = max(1, min(configured_attempts, 10))
    campaign_end = datetime.fromisoformat(str(campaign["ends_at"]).replace("Z", "+00:00"))
    if campaign_end.tzinfo is None:
        campaign_end = campaign_end.replace(tzinfo=timezone.utc)
    campaign_expired = campaign_end <= datetime.now(timezone.utc)

    try:
        resolved = _resolve_from_replica([row["userid"] for row in claimed])
    except Exception:
        with db.get_conn() as conn:
            for row in claimed:
                execute(
                    conn,
                    """
                    UPDATE credit_campaign_whatsapp_recipients
                    SET state = 'retry', last_error = 'Audience replica lookup failed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s AND userid = %s
                    """,
                    (str(job_id), row["userid"]),
                )
            conn.commit()
        raise

    from credits.credit_campaign_routes import _template_values
    from whatsapp.admin_routes import _build_send_components

    outcomes = []
    needs_retry = False
    for row in claimed:
        uid = row["userid"]
        profile = resolved.get(uid)
        if campaign_expired:
            outcomes.append((uid, "skipped", "campaign_expired", None, None))
            continue
        recipient_status = "not_found"
        target = ""
        if profile:
            if profile["whatsapp"]:
                recipient_status, target = "linked", profile["whatsapp"]
            elif profile["phone"]:
                recipient_status, target = "phone_only", profile["phone"]
            else:
                recipient_status = "no_phone"
        if not target or (recipient_status == "phone_only" and not include_unlinked):
            outcomes.append((uid, "skipped", recipient_status, None, None))
            continue
        try:
            secure_token = f"{tokens_by_user[uid]}.cc{int(campaign['id'])}"
            values = _template_values(template, campaign, {"name": profile["name"]}, secure_token)
            components = _build_send_components(template, values)
            ok, error, meta = send_whatsapp_template(
                to=target,
                phone_number_id=phone_number_id,
                template_name=template_name,
                language_code=language,
                components_override=components,
                return_error=True,
                return_meta=True,
            )
            if ok:
                outcomes.append((uid, "accepted", recipient_status, None, meta))
            elif row["attempt_count"] < max_attempts and _retryable_provider_error(error):
                outcomes.append((uid, "retry", recipient_status, error, meta))
                needs_retry = True
            else:
                outcomes.append((uid, "failed", recipient_status, error, meta))
        except Exception as exc:
            if row["attempt_count"] < max_attempts:
                outcomes.append((uid, "retry", recipient_status, str(exc), None))
                needs_retry = True
            else:
                outcomes.append((uid, "failed", recipient_status, str(exc), None))

    with db.get_conn() as conn:
        accepted_message_ids: List[str] = []
        for uid, state, recipient_status, error, meta in outcomes:
            meta = meta or {}
            message_id = str(meta.get("message_id") or "").strip() or None
            if message_id:
                accepted_message_ids.append(message_id)
            meta_recipient_id = str(meta.get("wa_id") or "").strip() or None
            execute(
                conn,
                """
                UPDATE credit_campaign_whatsapp_recipients
                SET state = %s, recipient_status = %s, last_error = %s,
                    meta_message_id = COALESCE(%s, meta_message_id),
                    meta_recipient_id = COALESCE(%s, meta_recipient_id),
                    meta_status = CASE WHEN %s = 'accepted' THEN 'accepted' ELSE meta_status END,
                    meta_accepted_at = CASE WHEN %s = 'accepted'
                                            THEN COALESCE(meta_accepted_at, CURRENT_TIMESTAMP)
                                            ELSE meta_accepted_at END,
                    completed_at = CASE WHEN %s IN ('accepted', 'failed', 'skipped')
                                        THEN CURRENT_TIMESTAMP ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s AND userid = %s
                """,
                (
                    state, recipient_status, str(error or "")[:1000] or None,
                    message_id, meta_recipient_id, state, state, state, str(job_id), uid,
                ),
            )
        _reconcile_pending_meta_statuses(conn, accepted_message_ids)
        _refresh_job(conn, str(job_id))
        conn.commit()
    summary = get_credit_campaign_whatsapp_job(str(job_id)) or {}
    if needs_retry:
        raise RuntimeError("One or more WhatsApp recipients require retry")
    return {"ok": True, **summary, "processed": len(outcomes)}
