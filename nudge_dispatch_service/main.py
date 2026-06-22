"""
Cloud Run service for nudge dispatch entrypoints.

This service owns only scheduler-facing work:
- daily scan
- due campaign dispatch
- due broadcast dispatch
- recent chat follow-up dispatch

It must never run on the main API fleet.
"""

import os
import sys
import logging
from functools import partial
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from starlette.concurrency import run_in_threadpool


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ENV_FILE = os.getenv("NUDGE_SERVICE_ENV_FILE", str(REPO_ROOT / ".env"))
if ENV_FILE and os.path.isfile(ENV_FILE):
    load_dotenv(ENV_FILE, override=False)

from nudge_engine.campaigns import dispatch_due_campaigns  # noqa: E402
from nudge_engine.routes import (  # noqa: E402
    _dispatch_due_broadcast,
    _dispatch_recent_chat_followups,
    _verify_cron_secret,
)
from nudge_engine.service import run_nudge_scan  # noqa: E402


app = FastAPI(title="nudge-dispatch-service")
logger = logging.getLogger(__name__)


def _require_dispatch_role() -> None:
    role = (os.getenv("NUDGE_SERVICE_ROLE") or "").strip().lower()
    if role != "dispatch":
        raise HTTPException(status_code=503, detail=f"Service role mismatch: expected dispatch, got {role or 'unset'}")


@app.get("/")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "nudge-dispatch-service"}


@app.post("/api/nudge/scan")
async def trigger_nudge_scan(
    scan_date: Optional[str] = Query(None, description="Date YYYY-MM-DD; default is today"),
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    _require_dispatch_role()
    _verify_cron_secret(x_cron_secret)
    try:
        from datetime import date

        target = date.today()
        if scan_date:
            target = date.fromisoformat(scan_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date: {e}") from e

    return await run_in_threadpool(run_nudge_scan, target)


@app.post("/api/nudge/cron/broadcast/dispatch-due")
async def cron_dispatch_due_broadcast(
    limit: int = Query(100, ge=1, le=500),
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    _require_dispatch_role()
    _verify_cron_secret(x_cron_secret)
    return await run_in_threadpool(_dispatch_due_broadcast, limit)


@app.post("/api/nudge/cron/campaign/dispatch-due")
async def cron_dispatch_due_campaigns(
    limit: int = Query(20, ge=1, le=100),
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    _require_dispatch_role()
    _verify_cron_secret(x_cron_secret)
    return await run_in_threadpool(dispatch_due_campaigns, limit)


@app.post("/api/nudge/cron/chat-followup/dispatch-recent")
async def cron_dispatch_recent_chat_followups(
    limit_users: int = Query(200, ge=1, le=500),
    lookback_minutes: int = Query(60, ge=1, le=1440),
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    _require_dispatch_role()
    _verify_cron_secret(x_cron_secret)
    return await run_in_threadpool(
        partial(
            _dispatch_recent_chat_followups,
            limit_users=int(limit_users),
            lookback_minutes=int(lookback_minutes),
            max_turns=2,
        )
    )
