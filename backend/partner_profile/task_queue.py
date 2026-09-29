"""Durable Cloud Tasks adapter for Partner Portrait generation."""

from __future__ import annotations

import json
import logging
import os


logger = logging.getLogger(__name__)


def tasks_enabled() -> bool:
    return (os.getenv("PARTNER_PORTRAIT_TASKS_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}


def task_secret() -> str:
    return (
        os.getenv("PARTNER_PORTRAIT_TASKS_SECRET")
        or os.getenv("REPORT_TASKS_SECRET")
        or os.getenv("CHAT_TASKS_SECRET")
        or ""
    ).strip()


def enqueue_partner_portrait(job_id: str) -> bool:
    if not tasks_enabled():
        return False
    project = (
        os.getenv("PARTNER_PORTRAIT_TASKS_PROJECT")
        or os.getenv("REPORT_TASKS_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
        or ""
    ).strip()
    location = (os.getenv("PARTNER_PORTRAIT_TASKS_LOCATION") or os.getenv("REPORT_TASKS_LOCATION") or "asia-south2").strip()
    queue = (os.getenv("PARTNER_PORTRAIT_TASKS_QUEUE") or os.getenv("REPORT_TASKS_QUEUE") or "report-processing-queue").strip()
    target = (
        os.getenv("PARTNER_PORTRAIT_TASKS_TARGET_BASE_URL")
        or os.getenv("REPORT_TASKS_TARGET_BASE_URL")
        or os.getenv("PUBLIC_API_BASE_URL")
        or "https://astroroshni.com"
    ).strip().rstrip("/")
    secret = task_secret()
    if not all((project, location, queue, target, secret)):
        logger.error("Partner Portrait task queue is enabled but incompletely configured")
        return False
    try:
        from google.cloud import tasks_v2
        from google.protobuf import duration_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        task_name = client.task_path(project, location, queue, f"partner-portrait-{job_id}")
        deadline = duration_pb2.Duration()
        deadline.FromSeconds(int(os.getenv("PARTNER_PORTRAIT_TASKS_DISPATCH_DEADLINE_S", "1800") or "1800"))
        task = {
            "name": task_name,
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target}/api/partner-portrait/internal/process",
                "headers": {"Content-Type": "application/json", "X-Partner-Portrait-Task-Secret": secret},
                "body": json.dumps({"job_id": job_id}).encode("utf-8"),
            },
            "dispatch_deadline": deadline,
        }
        client.create_task(request={"parent": parent, "task": task})
        return True
    except Exception as exc:
        if exc.__class__.__name__ == "AlreadyExists":
            return True
        logger.exception("Could not enqueue Partner Portrait job %s", job_id)
        return False
