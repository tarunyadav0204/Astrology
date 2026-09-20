from __future__ import annotations

import hmac
import os
import uuid
from datetime import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user

from .repository import EngagementSuggestionRepository
from .service import EngagementSuggestionService
from .deterministic_copy import normalize_locale


router = APIRouter(prefix="/engagement-suggestions", tags=["engagement-suggestions"])
repository = EngagementSuggestionRepository()
service = EngagementSuggestionService(repository)


class InteractionRequest(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=8, max_length=120)
    opportunity_id: str = Field(min_length=8, max_length=120)
    presentation_id: Optional[int] = None
    event_type: str
    surface: str
    birth_chart_id: Optional[int] = None
    session_id: Optional[str] = Field(default=None, max_length=160)
    delivery_group_id: Optional[str] = Field(default=None, max_length=160)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RefreshRequest(BaseModel):
    birth_chart_id: int = Field(ge=1)
    sources: list[str] = Field(default_factory=lambda: ["monthly_manifestation", "kp_daily"])


class PreferenceRequest(BaseModel):
    timezone: Optional[str] = None
    preferred_locale: Optional[str] = None
    astrology_alerts_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    preferred_delivery_time: Optional[time] = None
    daily_notification_limit: Optional[int] = Field(default=None, ge=0, le=20)
    weekly_notification_limit: Optional[int] = Field(default=None, ge=0, le=100)
    suppressed_domains: Optional[list[str]] = None
    consent: Optional[Dict[str, Any]] = None


def _verify_cron_secret(received: Optional[str]) -> None:
    expected = (os.getenv("NUDGE_CRON_SECRET") or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="NUDGE_CRON_SECRET is not configured on server.")
    if not received or not hmac.compare_digest(received.strip(), expected):
        raise HTTPException(status_code=401, detail="Invalid cron secret")


def _require_background_role() -> None:
    role = (os.getenv("NUDGE_SERVICE_ROLE") or "api").strip().lower()
    if role not in {"dispatch", "worker"}:
        raise HTTPException(
            status_code=503,
            detail=f"Engagement background work is disabled on service role: {role}",
        )


@router.get("")
async def list_suggestions(
    birth_chart_id: Optional[int] = Query(default=None, ge=1),
    language: str = Query(default="en", min_length=2, max_length=16),
    limit: int = Query(default=4, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    rows = await run_in_threadpool(
        repository.list_ranked,
        userid=int(current_user.userid),
        birth_chart_id=birth_chart_id,
        locale=normalize_locale(language),
        limit=limit,
    )
    return {"suggestions": rows, "count": len(rows)}


@router.get("/preferences")
async def get_preferences(current_user: User = Depends(get_current_user)):
    return await run_in_threadpool(repository.get_preferences, int(current_user.userid))


@router.put("/preferences")
async def update_preferences(payload: PreferenceRequest, current_user: User = Depends(get_current_user)):
    values = payload.model_dump(exclude_unset=True)
    clearable = {"quiet_hours_start", "quiet_hours_end", "preferred_delivery_time"}
    values = {
        key: value for key, value in values.items()
        if value is not None or key in clearable
    }
    if "preferred_locale" in values:
        values["preferred_locale"] = normalize_locale(values["preferred_locale"])
    return await run_in_threadpool(repository.upsert_preferences, int(current_user.userid), values)


@router.post("/interactions")
async def record_interaction(payload: InteractionRequest, current_user: User = Depends(get_current_user)):
    if payload.event_type not in {"shown", "clicked", "dismissed", "asked", "edited", "converted"}:
        raise HTTPException(status_code=422, detail="Unsupported event_type")
    inserted = await run_in_threadpool(
        repository.record_interaction,
        userid=int(current_user.userid),
        opportunity_id=payload.opportunity_id,
        presentation_id=payload.presentation_id,
        event_id=payload.event_id,
        event_type=payload.event_type,
        surface=payload.surface,
        birth_chart_id=payload.birth_chart_id,
        session_id=payload.session_id,
        delivery_group_id=payload.delivery_group_id,
        metadata=payload.metadata,
    )
    if inserted is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"ok": True, "inserted": bool(inserted)}


@router.post("/refresh")
async def enqueue_refresh(
    payload: RefreshRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    from db import execute, get_conn

    with get_conn() as conn:
        owned = execute(
            conn,
            "SELECT 1 FROM birth_charts WHERE id = %s AND userid = %s",
            (payload.birth_chart_id, int(current_user.userid)),
        ).fetchone()
    if not owned:
        raise HTTPException(status_code=404, detail="Birth chart not found")
    await run_in_threadpool(
        repository.enqueue_refresh,
        userid=int(current_user.userid),
        birth_chart_id=payload.birth_chart_id,
        reason="explicit_refresh",
        sources=payload.sources,
    )
    # User-triggered generation must also work in local development and must
    # not wait for the production scheduler's next five-minute tick.
    background_tasks.add_task(
        service.process_due_refreshes,
        limit=1,
        userid=int(current_user.userid),
        birth_chart_id=payload.birth_chart_id,
    )
    return {"ok": True, "queued": True, "processing": True}


@router.post("/cron/repair")
async def cron_repair(
    background_tasks: BackgroundTasks,
    lookback_hours: int = Query(default=48, ge=1, le=720),
    limit: int = Query(default=500, ge=1, le=5000),
    x_cron_secret: Optional[str] = Header(default=None, alias="X-Cron-Secret"),
):
    _require_background_role()
    _verify_cron_secret(x_cron_secret)
    background_tasks.add_task(service.repair_from_stored_sources, lookback_hours=lookback_hours, limit=limit)
    return {"ok": True, "queued": True, "lookback_hours": lookback_hours, "limit": limit}


@router.post("/cron/process-due")
async def cron_process_due(
    background_tasks: BackgroundTasks,
    limit: int = Query(default=2, ge=1, le=5),
    x_cron_secret: Optional[str] = Header(default=None, alias="X-Cron-Secret"),
):
    _require_background_role()
    _verify_cron_secret(x_cron_secret)
    background_tasks.add_task(service.process_due_refreshes, limit=limit)
    return {"ok": True, "queued": True, "limit": limit}


@router.post("/cron/schedule-notification-refreshes")
async def cron_schedule_notification_refreshes(
    limit: int = Query(default=500, ge=1, le=5000),
    x_cron_secret: Optional[str] = Header(default=None, alias="X-Cron-Secret"),
):
    _require_background_role()
    _verify_cron_secret(x_cron_secret)
    queued = await run_in_threadpool(repository.enqueue_notification_refreshes, limit=limit)
    return {"ok": True, "queued": queued}
