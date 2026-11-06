"""Durable Cloud Tasks dispatch and worker registration for Reel Studio."""

from __future__ import annotations

import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)


def reel_task_secret() -> str:
    """Shared authentication secret for API → Cloud Tasks → Reel worker."""
    return (
        os.getenv("REEL_TASKS_SECRET")
        or os.getenv("NUDGE_TASKS_SECRET")
        or os.getenv("CHAT_TASKS_SECRET")
        or os.getenv("NUDGE_CRON_SECRET")
        or ""
    ).strip()


def _project_id() -> str:
    return (
        os.getenv("REEL_TASKS_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
        or ""
    ).strip()


def _location() -> str:
    return (os.getenv("REEL_TASKS_LOCATION") or "asia-south2").strip()


def _queue_name() -> str:
    return (os.getenv("REEL_TASKS_QUEUE") or "reel-render-queue").strip()


def _ensure_worker_config_table(conn) -> None:
    from db import execute

    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS reel_worker_config (
            config_key TEXT PRIMARY KEY,
            config_value TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )


def register_reel_worker_url(worker_url: str) -> None:
    """Register the deployed worker URL without exposing it as an API setting."""
    normalized = str(worker_url or "").strip().rstrip("/")
    if not normalized.startswith("https://"):
        raise ValueError("Reel worker URL must use HTTPS")
    from db import execute, get_conn

    with get_conn() as conn:
        _ensure_worker_config_table(conn)
        row = execute(
            conn,
            "SELECT config_key FROM reel_worker_config WHERE config_key = ? LIMIT 1",
            ("target_url",),
        ).fetchone()
        if row:
            execute(
                conn,
                "UPDATE reel_worker_config SET config_value = ?, updated_at = CURRENT_TIMESTAMP WHERE config_key = ?",
                (normalized, "target_url"),
            )
        else:
            execute(
                conn,
                "INSERT INTO reel_worker_config (config_key, config_value) VALUES (?, ?)",
                ("target_url", normalized),
            )
        conn.commit()


def _registered_worker_url() -> str:
    configured = (os.getenv("REEL_TASKS_TARGET_BASE_URL") or "").strip().rstrip("/")
    if configured:
        return configured
    try:
        from db import execute, get_conn

        with get_conn() as conn:
            _ensure_worker_config_table(conn)
            row = execute(
                conn,
                "SELECT config_value FROM reel_worker_config WHERE config_key = ? LIMIT 1",
                ("target_url",),
            ).fetchone()
            conn.commit()
        return str(row[0] or "").strip().rstrip("/") if row else ""
    except Exception:
        logger.exception("Could not resolve registered Reel worker URL")
        return ""


def reel_tasks_enabled() -> bool:
    """Cloud Tasks are active once the dedicated worker has registered itself."""
    configured = (os.getenv("REEL_TASKS_ENABLED") or "").strip().lower()
    if configured in {"0", "false", "no", "off"}:
        return False
    return bool(_registered_worker_url())


def enqueue_reel_render_task(job_id: str) -> bool:
    """Create an idempotent Cloud Task for a persisted Reel render job."""
    target = _registered_worker_url()
    project = _project_id()
    location = _location()
    queue = _queue_name()
    secret = reel_task_secret()
    if not all([project, location, queue, target, secret]):
        logger.warning(
            "Reel task dispatch unavailable: project=%r location=%r queue=%r target_set=%s secret_set=%s",
            project,
            location,
            queue,
            bool(target),
            bool(secret),
        )
        return False
    try:
        from google.cloud import tasks_v2
        from google.protobuf import duration_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        safe_id = hashlib.sha256(str(job_id).encode("utf-8")).hexdigest()[:32]
        deadline = duration_pb2.Duration()
        deadline.FromSeconds(int(os.getenv("REEL_TASKS_DISPATCH_DEADLINE_S", "1800") or "1800"))
        task = {
            "name": client.task_path(project, location, queue, f"reel-{safe_id}"),
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target}/api/reel-worker/internal/process",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Reel-Task-Secret": secret,
                },
                "body": json.dumps({"job_id": job_id}).encode("utf-8"),
            },
            "dispatch_deadline": deadline,
        }
        client.create_task(request={"parent": parent, "task": task})
        logger.info("enqueued Reel Cloud Task job_id=%s queue=%s", job_id, queue)
        return True
    except Exception as exc:
        if exc.__class__.__name__ == "AlreadyExists":
            logger.info("Reel Cloud Task already exists job_id=%s", job_id)
            return True
        logger.exception("Could not enqueue Reel Cloud Task job_id=%s: %s", job_id, exc)
        return False
