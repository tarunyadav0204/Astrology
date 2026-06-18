from __future__ import annotations

import asyncio
import logging
import os
import time

from chat_history.local_task_queue import (
    claim_next_local_chat_task,
    mark_local_chat_task_completed,
    mark_local_chat_task_failed,
)
from chat_history.routes import process_chat_task
from chat_history.task_queue import chat_task_secret

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("chat_local_worker")


def _poll_interval_seconds() -> float:
    try:
        return max(0.2, float(os.getenv("CHAT_TASKS_LOCAL_POLL_S", "1.0")))
    except Exception:
        return 1.0


async def _run_task(task: dict) -> None:
    payload = dict(task["payload"] or {})
    if not payload.get("claim_id"):
        payload["claim_id"] = task.get("claim_id")
    await process_chat_task(payload, x_chat_task_secret=chat_task_secret())


def run_forever() -> None:
    if not chat_task_secret():
        raise RuntimeError("CHAT_TASKS_SECRET (or NUDGE_CRON_SECRET) is required for local chat worker mode")

    poll_s = _poll_interval_seconds()
    logger.info("Starting local chat worker poll_interval=%ss", poll_s)
    while True:
        task = claim_next_local_chat_task()
        if not task:
            time.sleep(poll_s)
            continue

        task_id = int(task["id"])
        message_id = task.get("message_id")
        try:
            logger.info("Processing local chat task task_id=%s message_id=%s attempts=%s", task_id, message_id, task.get("attempts"))
            asyncio.run(_run_task(task))
            mark_local_chat_task_completed(task_id)
            logger.info("Completed local chat task task_id=%s message_id=%s", task_id, message_id)
        except Exception as exc:
            mark_local_chat_task_failed(task_id, str(exc))
            logger.exception("Local chat task failed task_id=%s message_id=%s: %s", task_id, message_id, exc)
            time.sleep(poll_s)


if __name__ == "__main__":
    run_forever()
