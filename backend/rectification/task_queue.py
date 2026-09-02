from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict


logger = logging.getLogger(__name__)


def rectification_tasks_enabled() -> bool:
    return str(os.getenv("RECTIFICATION_TASKS_ENABLED") or "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def rectification_task_secret() -> str:
    return str(
        os.getenv("RECTIFICATION_TASKS_SECRET")
        or os.getenv("CHAT_TASKS_SECRET")
        or ""
    ).strip()


def enqueue_rectification_task(*, run_id: str, userid: int) -> bool:
    if not rectification_tasks_enabled():
        return False
    project = str(os.getenv("RECTIFICATION_TASKS_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
    location = str(os.getenv("RECTIFICATION_TASKS_LOCATION") or "asia-south2").strip()
    queue = str(os.getenv("RECTIFICATION_TASKS_QUEUE") or "rectification").strip()
    target = str(os.getenv("RECTIFICATION_TASKS_TARGET_BASE_URL") or "").strip().rstrip("/")
    secret = rectification_task_secret()
    if not all((project, location, queue, target, secret)):
        logger.error("Rectification Cloud Tasks is enabled but not fully configured")
        return False
    try:
        from google.cloud import tasks_v2
        from google.protobuf import duration_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in run_id)[:400]
        body = json.dumps({"run_id": run_id, "userid": userid}).encode("utf-8")
        deadline = duration_pb2.Duration()
        deadline.FromSeconds(1800)
        task = {
            "name": client.task_path(project, location, queue, f"rectification-{safe_id}"),
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target}/api/rectification/internal/process",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Rectification-Task-Secret": secret,
                },
                "body": body,
            },
            "dispatch_deadline": deadline,
        }
        client.create_task(request={"parent": parent, "task": task})
        return True
    except Exception:
        logger.exception("Failed to enqueue rectification run %s", run_id)
        return False
