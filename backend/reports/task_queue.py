"""Cloud Tasks adapter for durable report processing."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def report_tasks_enabled() -> bool:
    return (os.getenv("REPORT_TASKS_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}


def local_report_tasks_enabled() -> bool:
    return (os.getenv("REPORT_TASKS_LOCAL_MODE") or "").strip().lower() in {"1", "true", "yes", "on"}


def _project_id() -> str:
    return (
        os.getenv("REPORT_TASKS_PROJECT")
        or os.getenv("CHAT_TASKS_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
        or ""
    ).strip()


def _location() -> str:
    return (os.getenv("REPORT_TASKS_LOCATION") or os.getenv("CHAT_TASKS_LOCATION") or "asia-south2").strip()


def _queue_name() -> str:
    return (os.getenv("REPORT_TASKS_QUEUE") or "report-processing-queue").strip()


def _target_base_url() -> str:
    return (
        os.getenv("REPORT_TASKS_TARGET_BASE_URL")
        or os.getenv("CHAT_TASKS_TARGET_BASE_URL")
        or os.getenv("PUBLIC_API_BASE_URL")
        or "https://astroroshni.com"
    ).strip().rstrip("/")


def report_task_secret() -> str:
    return (
        os.getenv("REPORT_TASKS_SECRET")
        or os.getenv("CHAT_TASKS_SECRET")
        or os.getenv("NUDGE_CRON_SECRET")
        or ""
    ).strip()


def enqueue_report_processing_task(*, report_id: str, payload: Dict[str, Any] | None = None) -> bool:
    """
    Enqueue one durable report processing request.

    Returns False when queueing is disabled or not configured, allowing callers to
    fall back to FastAPI BackgroundTasks for local/dev safety.
    """
    if not report_tasks_enabled():
        return False

    if local_report_tasks_enabled():
        try:
            from reports.local_task_queue import enqueue_local_report_task

            return enqueue_local_report_task(report_id=report_id, payload=payload or {})
        except Exception as exc:
            logger.exception("failed to enqueue local dev report task report_id=%s: %s", report_id, exc)
            return False

    project = _project_id()
    location = _location()
    queue = _queue_name()
    target = _target_base_url()
    secret = report_task_secret()
    if not all([project, location, queue, target, secret]):
        logger.warning(
            "REPORT_TASKS enabled but not fully configured: project=%r location=%r queue=%r target=%r secret_set=%s",
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
        task_name = client.task_path(project, location, queue, f"report-{report_id}")
        body = json.dumps({"report_id": report_id, **(payload or {})}, ensure_ascii=False, default=str).encode("utf-8")

        dispatch_deadline = duration_pb2.Duration()
        dispatch_deadline.FromSeconds(int(os.getenv("REPORT_TASKS_DISPATCH_DEADLINE_S", "1800") or "1800"))

        task = {
            "name": task_name,
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target}/api/reports/internal/process",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Report-Task-Secret": secret,
                },
                "body": body,
            },
            "dispatch_deadline": dispatch_deadline,
        }
        client.create_task(request={"parent": parent, "task": task})
        logger.info("enqueued report Cloud Task report_id=%s queue=%s", report_id, queue)
        return True
    except Exception as exc:
        if exc.__class__.__name__ == "AlreadyExists":
            logger.info("report Cloud Task already exists report_id=%s", report_id)
            return True
        logger.exception("failed to enqueue report Cloud Task report_id=%s: %s", report_id, exc)
        return False
