"""
Cloud Run service for nudge worker task execution.

This service owns only internal batch/task work and should be the sole Cloud
Tasks target for nudge processing.
"""

import os
import sys
import logging
from functools import partial
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from starlette.concurrency import run_in_threadpool


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ENV_FILE = os.getenv("NUDGE_SERVICE_ENV_FILE", str(REPO_ROOT / ".env"))
if ENV_FILE and os.path.isfile(ENV_FILE):
    load_dotenv(ENV_FILE, override=False)

from nudge_engine.campaigns import process_campaign_batch  # noqa: E402
from nudge_engine.delivery import deliver_for_user_batch  # noqa: E402
from nudge_engine.models import NudgeEvent  # noqa: E402
from nudge_engine.routes import (  # noqa: E402
    _process_broadcast_schedule_batch,
    _process_recent_chat_followup_user,
    _verify_nudge_task_secret,
)
from nudge_engine import db  # noqa: E402


app = FastAPI(title="nudge-worker-service")
logger = logging.getLogger(__name__)


def _require_worker_role() -> None:
    role = (os.getenv("NUDGE_SERVICE_ROLE") or "").strip().lower()
    if role != "worker":
        raise HTTPException(status_code=503, detail=f"Service role mismatch: expected worker, got {role or 'unset'}")


@app.get("/")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "nudge-worker-service"}


@app.post("/api/nudge/internal/tasks/chat-followup-user")
async def internal_chat_followup_user_task(
    body: Dict[str, Any],
    x_nudge_task_secret: Optional[str] = Header(None, alias="X-Nudge-Task-Secret"),
):
    _require_worker_role()
    _verify_nudge_task_secret(x_nudge_task_secret)
    try:
        uid = int(body.get("user_id"))
        message_id = int(body.get("message_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="user_id and message_id are required")
    lookback_minutes = max(1, min(int(body.get("lookback_minutes") or 60), 24 * 60))
    max_turns = max(1, min(int(body.get("max_turns") or 2), 2))
    with db.get_conn() as conn:
        db.init_nudge_tables(conn)
        result = await run_in_threadpool(
            partial(
                _process_recent_chat_followup_user,
                conn,
                uid=uid,
                message_id=message_id,
                lookback_minutes=lookback_minutes,
                max_turns=max_turns,
            )
        )
        conn.commit()
    return result


@app.post("/api/nudge/internal/tasks/broadcast-schedule-batch")
async def internal_broadcast_schedule_batch_task(
    body: Dict[str, Any],
    x_nudge_task_secret: Optional[str] = Header(None, alias="X-Nudge-Task-Secret"),
):
    _require_worker_role()
    _verify_nudge_task_secret(x_nudge_task_secret)
    try:
        schedule_id = int(body.get("schedule_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="schedule_id is required")
    user_ids_raw = body.get("user_ids") or []
    if not isinstance(user_ids_raw, list):
        raise HTTPException(status_code=400, detail="user_ids must be a list")
    return await run_in_threadpool(
        partial(
            _process_broadcast_schedule_batch,
            schedule_id=schedule_id,
            user_ids=user_ids_raw,
        )
    )


@app.post("/api/nudge/internal/tasks/campaign-batch")
async def internal_campaign_batch_task(
    body: Dict[str, Any],
    x_nudge_task_secret: Optional[str] = Header(None, alias="X-Nudge-Task-Secret"),
):
    _require_worker_role()
    _verify_nudge_task_secret(x_nudge_task_secret)
    try:
        campaign_id = int(body.get("campaign_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="campaign_id is required")
    user_ids_raw = body.get("user_ids") or []
    if not isinstance(user_ids_raw, list):
        raise HTTPException(status_code=400, detail="user_ids must be a list")
    return await run_in_threadpool(
        partial(
            process_campaign_batch,
            campaign_id=campaign_id,
            user_ids=user_ids_raw,
        )
    )


@app.post("/api/nudge/internal/tasks/scan-delivery-batch")
async def internal_scan_delivery_batch_task(
    body: Dict[str, Any],
    x_nudge_task_secret: Optional[str] = Header(None, alias="X-Nudge-Task-Secret"),
):
    _require_worker_role()
    _verify_nudge_task_secret(x_nudge_task_secret)
    event_payload = body.get("event")
    user_ids_raw = body.get("user_ids") or []
    scan_date = str(body.get("scan_date") or "").strip()
    if not isinstance(event_payload, dict):
        raise HTTPException(status_code=400, detail="event is required")
    if not isinstance(user_ids_raw, list):
        raise HTTPException(status_code=400, detail="user_ids must be a list")
    try:
        from datetime import date

        target_date = date.fromisoformat(scan_date)
        event = NudgeEvent.from_payload(event_payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid scan batch payload: {exc}") from exc

    return await run_in_threadpool(
        partial(
            deliver_for_user_batch,
            target_date,
            event,
            user_ids_raw,
        )
    )
