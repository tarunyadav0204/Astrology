"""Durable Cloud Tasks dispatch for podcast generation."""

from __future__ import annotations

import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)


def podcast_tasks_enabled() -> bool:
    """Use the established chat task infrastructure unless explicitly disabled."""
    # Local development intentionally uses FastAPI BackgroundTasks below. Do
    # not send a developer's request to the production Cloud Tasks target.
    local_mode = (os.getenv("PODCAST_TASKS_LOCAL_MODE") or os.getenv("CHAT_TASKS_LOCAL_MODE") or "").strip().lower()
    if local_mode in {"1", "true", "yes", "on"}:
        return False
    configured = (os.getenv("PODCAST_TASKS_ENABLED") or os.getenv("CHAT_TASKS_ENABLED") or "").strip().lower()
    return configured in {"1", "true", "yes", "on"}


def podcast_task_secret() -> str:
    return (
        os.getenv("PODCAST_TASKS_SECRET")
        or os.getenv("CHAT_TASKS_SECRET")
        or os.getenv("NUDGE_CRON_SECRET")
        or ""
    ).strip()


def enqueue_podcast_generation_task(job_id: str) -> bool:
    """Create one idempotent task for an already-persisted podcast job."""
    if not podcast_tasks_enabled():
        return False
    project = (os.getenv("PODCAST_TASKS_PROJECT") or os.getenv("CHAT_TASKS_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID") or "").strip()
    location = (os.getenv("PODCAST_TASKS_LOCATION") or os.getenv("CHAT_TASKS_LOCATION") or "asia-south2").strip()
    queue = (os.getenv("PODCAST_TASKS_QUEUE") or os.getenv("CHAT_TASKS_QUEUE") or "chat-standard-queue").strip()
    target = (os.getenv("PODCAST_TASKS_TARGET_BASE_URL") or os.getenv("CHAT_TASKS_TARGET_BASE_URL") or os.getenv("PUBLIC_API_BASE_URL") or "https://astroroshni.com").strip().rstrip("/")
    secret = podcast_task_secret()
    if not all([project, location, queue, target, secret]):
        logger.warning("Podcast task dispatch unavailable: project=%r location=%r queue=%r target=%r secret_set=%s", project, location, queue, target, bool(secret))
        return False
    try:
        from google.cloud import tasks_v2
        from google.protobuf import duration_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project, location, queue)
        safe_id = hashlib.sha256(str(job_id).encode("utf-8")).hexdigest()[:32]
        deadline = duration_pb2.Duration()
        deadline.FromSeconds(int(os.getenv("PODCAST_TASKS_DISPATCH_DEADLINE_S", "1800") or "1800"))
        task = {
            "name": client.task_path(project, location, queue, f"podcast-{safe_id}"),
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target}/api/tts/podcast/internal/process",
                "headers": {"Content-Type": "application/json", "X-Podcast-Task-Secret": secret},
                "body": json.dumps({"job_id": job_id}).encode("utf-8"),
            },
            "dispatch_deadline": deadline,
        }
        client.create_task(request={"parent": parent, "task": task})
        logger.info("enqueued podcast Cloud Task job_id=%s queue=%s", job_id, queue)
        return True
    except Exception as exc:
        if exc.__class__.__name__ == "AlreadyExists":
            logger.info("podcast Cloud Task already exists job_id=%s", job_id)
            return True
        logger.exception("Could not enqueue podcast Cloud Task job_id=%s: %s", job_id, exc)
        return False
