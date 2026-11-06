"""Dedicated Cloud Run worker for durable Reel Studio renders."""

from __future__ import annotations

import os
import sys
import logging
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from starlette.concurrency import run_in_threadpool


logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

env_file = os.getenv("REEL_WORKER_ENV_FILE", str(REPO_ROOT / ".env"))
if env_file and os.path.isfile(env_file):
    load_dotenv(env_file, override=False)

from db import get_conn  # noqa: E402
from reel_studio.routes import _ensure_tables  # noqa: E402
from reel_studio.task_queue import reel_task_secret, register_reel_worker_url  # noqa: E402
from reel_studio.worker import process_reel_job  # noqa: E402


app = FastAPI(title="reel-worker-service")


@app.on_event("startup")
def initialize_reel_worker() -> None:
    with get_conn() as conn:
        _ensure_tables(conn)
        conn.commit()
    worker_url = str(os.getenv("REEL_WORKER_PUBLIC_URL") or "").strip()
    if not worker_url:
        raise RuntimeError("REEL_WORKER_PUBLIC_URL is required for durable Reel dispatch")
    # Cloud Run assigns the public URL only after its first deployment.  That
    # bootstrap revision must not temporarily register a non-routable target
    # in the API database before the next revision receives the real URL.
    if "placeholder.invalid" in worker_url:
        logger.info("Reel worker bootstrap revision is ready; awaiting public URL registration")
        return
    register_reel_worker_url(worker_url)


@app.get("/")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "reel-worker-service"}


@app.post("/api/reel-worker/internal/process")
async def process_reel_task(
    body: Dict[str, Any],
    x_reel_task_secret: Optional[str] = Header(None, alias="X-Reel-Task-Secret"),
) -> Dict[str, Any]:
    expected_secret = reel_task_secret()
    if not expected_secret or x_reel_task_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    job_id = str(body.get("job_id") or "").strip()
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    state = await run_in_threadpool(partial(process_reel_job, job_id))
    if state == "missing":
        raise HTTPException(status_code=404, detail="Reel job not found")
    if state == "busy":
        # A duplicate Cloud Tasks delivery should be retried after the active
        # lease expires instead of allowing concurrent paid provider calls.
        raise HTTPException(status_code=409, detail="Reel job is already being processed")
    return {"ok": True, "job_id": job_id, "state": state}
