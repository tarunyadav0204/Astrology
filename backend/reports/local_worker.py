from __future__ import annotations

import asyncio
import json
import logging
import os
import time

from reports.local_task_queue import (
    claim_next_local_report_task,
    mark_local_report_task_completed,
    mark_local_report_task_failed,
)
from reports.routes import process_report_task
from reports.task_queue import report_task_secret

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("report_local_worker")


def _poll_interval_seconds() -> float:
    try:
        return max(0.2, float(os.getenv("REPORT_TASKS_LOCAL_POLL_S", "1.0")))
    except Exception:
        return 1.0


async def _run_task(task: dict) -> None:
    payload = dict(task["payload"] or {})
    payload["report_id"] = task.get("report_id")
    logger.info(
        "local_report_worker_task_payload task_id=%s report_id=%s payload=%s",
        task.get("id"),
        task.get("report_id"),
        json.dumps(
            {
                "report_type": payload.get("report_type"),
                "language": payload.get("language"),
            },
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        ),
    )
    await process_report_task(payload, x_report_task_secret=report_task_secret())


def run_forever() -> None:
    if not report_task_secret():
        raise RuntimeError("REPORT_TASKS_SECRET (or CHAT_TASKS_SECRET / NUDGE_CRON_SECRET) is required for local report worker mode")

    poll_s = _poll_interval_seconds()
    logger.info("Starting local report worker poll_interval=%ss", poll_s)
    while True:
        task = claim_next_local_report_task()
        if not task:
            time.sleep(poll_s)
            continue

        task_id = int(task["id"])
        report_id = task.get("report_id")
        try:
            logger.info("Processing local report task task_id=%s report_id=%s attempts=%s", task_id, report_id, task.get("attempts"))
            asyncio.run(_run_task(task))
            mark_local_report_task_completed(task_id)
            logger.info("Completed local report task task_id=%s report_id=%s", task_id, report_id)
        except Exception as exc:
            mark_local_report_task_failed(task_id, str(exc))
            logger.exception("Local report task failed task_id=%s report_id=%s: %s", task_id, report_id, exc)
            time.sleep(poll_s)


if __name__ == "__main__":
    run_forever()
