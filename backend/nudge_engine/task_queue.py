"""Cloud Tasks adapter for scalable nudge fan-out workers."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def nudge_tasks_enabled() -> bool:
    return (os.getenv("NUDGE_TASKS_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}


def _project_id() -> str:
    return (
        os.getenv("NUDGE_TASKS_PROJECT")
        or os.getenv("CHAT_TASKS_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
        or ""
    ).strip()


def _location() -> str:
    return (os.getenv("NUDGE_TASKS_LOCATION") or os.getenv("CHAT_TASKS_LOCATION") or "asia-south1").strip()


def _queue_name() -> str:
    return (os.getenv("NUDGE_TASKS_QUEUE") or "nudge-standard-queue").strip()


def _target_base_url() -> str:
    return (
        os.getenv("NUDGE_TASKS_TARGET_BASE_URL")
        or os.getenv("CHAT_TASKS_TARGET_BASE_URL")
        or os.getenv("PUBLIC_API_BASE_URL")
        or "https://astroroshni.com"
    ).strip().rstrip("/")


def nudge_task_secret() -> str:
    return (os.getenv("NUDGE_TASKS_SECRET") or os.getenv("CHAT_TASKS_SECRET") or os.getenv("NUDGE_CRON_SECRET") or "").strip()


def enqueue_nudge_task(
    *,
    task_kind: str,
    task_id: str,
    payload: Dict[str, Any],
    dispatch_deadline_s: Optional[int] = None,
) -> bool:
    """Enqueue one durable nudge worker request."""
    if not nudge_tasks_enabled():
        return False

    project = _project_id()
    location = _location()
    queue = _queue_name()
    target = _target_base_url()
    secret = nudge_task_secret()
    if not all([project, location, queue, target, secret]):
        logger.warning(
            "NUDGE_TASKS enabled but not fully configured: project=%r location=%r queue=%r target=%r secret_set=%s",
            project,
            location,
            queue,
            target,
            bool(secret),
        )
        return False

    safe_kind = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in str(task_kind).strip())
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in str(task_id).strip())[:400]
    if not safe_kind or not safe_id:
        return False

    try:
        from google.cloud import tasks_v2
        from google.protobuf import duration_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        task_name = client.task_path(project, location, queue, f"{safe_kind}-{safe_id}")
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")

        dispatch_deadline = duration_pb2.Duration()
        dispatch_deadline.FromSeconds(
            int(dispatch_deadline_s or os.getenv("NUDGE_TASKS_DISPATCH_DEADLINE_S", "600") or "600")
        )

        task = {
            "name": task_name,
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target}/api/nudge/internal/tasks/{safe_kind}",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Nudge-Task-Secret": secret,
                },
                "body": body,
            },
            "dispatch_deadline": dispatch_deadline,
        }
        client.create_task(request={"parent": parent, "task": task})
        logger.info("enqueued nudge Cloud Task kind=%s id=%s queue=%s", safe_kind, safe_id, queue)
        return True
    except Exception as exc:
        if exc.__class__.__name__ == "AlreadyExists":
            logger.info("nudge Cloud Task already exists kind=%s id=%s", safe_kind, safe_id)
            return True
        logger.exception("failed to enqueue nudge Cloud Task kind=%s id=%s: %s", safe_kind, safe_id, exc)
        return False
