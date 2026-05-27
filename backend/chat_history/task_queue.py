"""Cloud Tasks adapter for durable chat-v2 processing."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def chat_tasks_enabled() -> bool:
    return (os.getenv("CHAT_TASKS_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}


def _project_id() -> str:
    return (
        os.getenv("CHAT_TASKS_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
        or ""
    ).strip()


def _location() -> str:
    return (os.getenv("CHAT_TASKS_LOCATION") or "asia-south2").strip()


def _queue_name() -> str:
    return (os.getenv("CHAT_TASKS_QUEUE") or "chat-standard-queue").strip()


def _target_base_url() -> str:
    return (
        os.getenv("CHAT_TASKS_TARGET_BASE_URL")
        or os.getenv("PUBLIC_API_BASE_URL")
        or "https://astroroshni.com"
    ).strip().rstrip("/")


def chat_task_secret() -> str:
    return (os.getenv("CHAT_TASKS_SECRET") or os.getenv("NUDGE_CRON_SECRET") or "").strip()


def enqueue_chat_processing_task(*, message_id: int, payload: Dict[str, Any]) -> bool:
    """
    Enqueue one durable processing request for a chat assistant message.

    Returns False when queueing is disabled or not configured, allowing callers to
    fall back to FastAPI BackgroundTasks for local/dev safety.
    """
    if not chat_tasks_enabled():
        return False

    project = _project_id()
    location = _location()
    queue = _queue_name()
    target = _target_base_url()
    secret = chat_task_secret()
    if not all([project, location, queue, target, secret]):
        logger.warning(
            "CHAT_TASKS enabled but not fully configured: project=%r location=%r queue=%r target=%r secret_set=%s",
            project,
            location,
            queue,
            target,
            bool(secret),
        )
        return False

    try:
        from google.cloud import tasks_v2
        from google.protobuf import duration_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        task_name = client.task_path(project, location, queue, f"chat-message-{int(message_id)}")
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")

        dispatch_deadline = duration_pb2.Duration()
        dispatch_deadline.FromSeconds(int(os.getenv("CHAT_TASKS_DISPATCH_DEADLINE_S", "1800") or "1800"))

        task = {
            "name": task_name,
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target}/api/chat-v2/internal/process",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Chat-Task-Secret": secret,
                },
                "body": body,
            },
            "dispatch_deadline": dispatch_deadline,
        }
        client.create_task(request={"parent": parent, "task": task})
        logger.info("enqueued chat Cloud Task message_id=%s queue=%s", message_id, queue)
        return True
    except Exception as exc:
        if exc.__class__.__name__ == "AlreadyExists":
            logger.info("chat Cloud Task already exists message_id=%s", message_id)
            return True
        logger.exception("failed to enqueue chat Cloud Task message_id=%s: %s", message_id, exc)
        return False
