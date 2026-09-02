from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, Mapping, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException

from auth import User, get_current_user
from birth_charts.routes import _row_to_chart
from birth_charts.schema import ensure_birth_chart_family_columns
from db import execute, get_conn

from .contracts import (
    CreateRectificationCaseRequest,
    CreateRectificationEventRequest,
    StartRectificationRunRequest,
    UpdateRectificationEventRequest,
)
from .engine import RECTIFICATION_ENGINE_VERSION, RectificationEngine
from .registry import EVENT_DEFINITIONS, RECTIFICATION_REGISTRY_VERSION
from .repository import RectificationRepository
from .task_queue import (
    enqueue_rectification_task,
    rectification_task_secret,
    rectification_tasks_enabled,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rectification", tags=["rectification"])
repository = RectificationRepository()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _load_owned_chart(chart_id: int, userid: int) -> Dict[str, Any]:
    with get_conn() as conn:
        ensure_birth_chart_family_columns(conn)
        row = execute(
            conn,
            """
            SELECT id, userid, name, date, time, latitude, longitude, timezone,
                   created_at, place, gender, relation, relation_order,
                   relation_side, relation_label, is_family_member
            FROM birth_charts WHERE id = %s AND userid = %s
            """,
            (chart_id, userid),
        ).fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Birth chart not found")
    return _row_to_chart(row)


def _chart_input(chart: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "name": str(chart.get("name") or "Native"),
        "date": str(chart.get("date") or "").split("T", 1)[0],
        "time": str(chart.get("time") or "").split("T", 1)[-1][:8],
        "latitude": float(chart["latitude"]),
        "longitude": float(chart["longitude"]),
        "timezone": chart.get("timezone") or "",
        "place": str(chart.get("place") or ""),
        "gender": str(chart.get("gender") or ""),
    }


def _time_seconds(value: str) -> int:
    raw = str(value or "").strip().split("T", 1)[-1]
    pieces = raw.split(":")
    if len(pieces) not in {2, 3}:
        raise ValueError("Time must be HH:MM or HH:MM:SS")
    hour, minute = int(pieces[0]), int(pieces[1])
    second = int(float(pieces[2])) if len(pieces) == 3 else 0
    if not 0 <= hour <= 23 or not 0 <= minute <= 59 or not 0 <= second <= 59:
        raise ValueError("Time is outside the local civil day")
    return hour * 3600 + minute * 60 + second


def _case_window(request: CreateRectificationCaseRequest, chart: Mapping[str, Any]) -> tuple[int, int]:
    if request.window_start_local and request.window_end_local:
        start = _time_seconds(request.window_start_local)
        end = _time_seconds(request.window_end_local)
        if end < start:
            raise ValueError("Phase 1 rectification windows cannot cross midnight")
        if end - start > 120 * 60:
            raise ValueError("Phase 1 supports birth-time windows up to 120 minutes")
        return start, end
    recorded = _time_seconds(str(chart.get("time") or ""))
    delta = int(request.uncertainty_minutes) * 60
    return max(0, recorded - delta), min(86399, recorded + delta)


def _input_hash(case: Mapping[str, Any], events: list[Mapping[str, Any]], minute_step: int) -> str:
    return _hash({
        "chart_input_hash": case["chart_input_hash"],
        "window_start_seconds": case["window_start_seconds"],
        "window_end_seconds": case["window_end_seconds"],
        "minute_step": minute_step,
        "engine_version": RECTIFICATION_ENGINE_VERSION,
        "registry_version": RECTIFICATION_REGISTRY_VERSION,
        "events": [
            {
                "id": event["id"], "event_type": event["event_type"],
                "date_start": event["date_start"], "date_end": event["date_end"],
                "precision": event["precision"],
                "source_reliability": event["source_reliability"],
                "subtype": event.get("subtype") or "", "subject": event.get("subject") or "self",
            }
            for event in events
        ],
    })


def process_rectification_run(run_id: str, expected_userid: Optional[int] = None) -> None:
    claimed = repository.claim_run(run_id=run_id)
    if not claimed:
        return
    userid = int(claimed["userid"])
    if expected_userid is not None and userid != int(expected_userid):
        repository.fail_run(run_id=run_id, error="Run ownership mismatch")
        return
    try:
        case = repository.get_case(case_id=claimed["case_id"], userid=userid)
        if not case:
            raise RuntimeError("Rectification case no longer exists")
        chart = _load_owned_chart(int(case["birth_chart_id"]), userid)
        chart_input = _chart_input(chart)
        if _hash(chart_input) != case["chart_input_hash"]:
            raise RuntimeError("The saved birth chart changed; create a new rectification case")
        events = list((claimed.get("input_snapshot") or {}).get("events") or [])
        if len(events) < 4:
            raise RuntimeError("The run snapshot contains fewer than four life events")
        total = len(RectificationEngine.candidate_times(
            case["window_start_seconds"], case["window_end_seconds"], claimed["minute_step"]
        ))
        repository.update_progress(run_id=run_id, current=0, total=total, stage="scanning_candidates")

        last_persisted = -1
        def progress(current: int, progress_total: int) -> None:
            nonlocal last_persisted
            # Limit DB churn while still giving useful polling progress.
            if current == progress_total or current - last_persisted >= 5:
                repository.update_progress(
                    run_id=run_id, current=current, total=progress_total,
                    stage="checking_candidate_evidence",
                )
                last_persisted = current

        result = RectificationEngine().run(
            chart_input=chart_input,
            events=events,
            window_start_seconds=case["window_start_seconds"],
            window_end_seconds=case["window_end_seconds"],
            minute_step=int(claimed["minute_step"]),
            progress=progress,
        )
        repository.complete_run(run_id=run_id, result=result)
    except Exception as exc:
        logger.exception("Rectification run failed run_id=%s user=%s", run_id, userid)
        repository.fail_run(run_id=run_id, error=str(exc))


@router.get("/event-types")
async def list_rectification_event_types(current_user: User = Depends(get_current_user)):
    return {
        "registry_version": RECTIFICATION_REGISTRY_VERSION,
        "event_types": [
            {
                "key": definition.key,
                "label": definition.label,
                "varga": f"D{definition.varga}",
            }
            for definition in EVENT_DEFINITIONS.values()
        ],
    }


@router.post("/cases")
async def create_rectification_case(
    request: CreateRectificationCaseRequest,
    current_user: User = Depends(get_current_user),
):
    chart = _load_owned_chart(request.birth_chart_id, current_user.userid)
    try:
        start, end = _case_window(request, chart)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    chart_input = _chart_input(chart)
    case = repository.create_case(
        userid=current_user.userid,
        birth_chart_id=request.birth_chart_id,
        chart_input_hash=_hash(chart_input),
        window_start_seconds=start,
        window_end_seconds=end,
    )
    return {**case, "events": []}


@router.get("/cases/{case_id}")
async def get_rectification_case(case_id: str, current_user: User = Depends(get_current_user)):
    case = repository.get_case(case_id=case_id, userid=current_user.userid)
    if not case:
        raise HTTPException(status_code=404, detail="Rectification case not found")
    return {**case, "events": repository.list_events(case_id=case_id, userid=current_user.userid)}


@router.post("/cases/{case_id}/events")
async def add_rectification_event(
    case_id: str,
    request: CreateRectificationEventRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return repository.add_event(
            case_id=case_id,
            userid=current_user.userid,
            event=request.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/events/{event_id}")
async def update_rectification_event(
    event_id: int,
    request: UpdateRectificationEventRequest,
    current_user: User = Depends(get_current_user),
):
    current = repository.get_event(event_id=event_id, userid=current_user.userid)
    if not current:
        raise HTTPException(status_code=404, detail="Rectification event not found")
    changes = request.model_dump(exclude_unset=True)
    start = changes.get("date_start", current["date_start"])
    end = changes.get("date_end", current["date_end"])
    if end < start:
        raise HTTPException(status_code=422, detail="date_end cannot be earlier than date_start")
    if (end - start).days > 366:
        raise HTTPException(status_code=422, detail="One event cannot span more than 366 days")
    return repository.update_event(event_id=event_id, userid=current_user.userid, changes=changes)


@router.delete("/events/{event_id}")
async def delete_rectification_event(event_id: int, current_user: User = Depends(get_current_user)):
    if not repository.deactivate_event(event_id=event_id, userid=current_user.userid):
        raise HTTPException(status_code=404, detail="Rectification event not found")
    return {"deleted": True, "event_id": event_id}


@router.post("/cases/{case_id}/runs")
async def start_rectification_run(
    case_id: str,
    request: StartRectificationRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    case = repository.get_case(case_id=case_id, userid=current_user.userid)
    if not case:
        raise HTTPException(status_code=404, detail="Rectification case not found")
    events = repository.list_events(case_id=case_id, userid=current_user.userid)
    if len(events) < 4:
        raise HTTPException(status_code=422, detail="Add at least four dated life events")
    input_hash = _input_hash(case, events, request.minute_step)
    reusable = repository.find_reusable_run(
        case_id=case_id, userid=current_user.userid, input_hash=input_hash
    )
    if reusable:
        return {**reusable, "reused": True}
    run = repository.create_run(
        case_id=case_id,
        userid=current_user.userid,
        input_hash=input_hash,
        input_snapshot={
            "events": events,
            "window_start_seconds": case["window_start_seconds"],
            "window_end_seconds": case["window_end_seconds"],
            "chart_input_hash": case["chart_input_hash"],
        },
        minute_step=request.minute_step,
    )
    queued = enqueue_rectification_task(run_id=run["id"], userid=current_user.userid)
    if rectification_tasks_enabled() and not queued:
        repository.fail_run(run_id=run["id"], error="Durable rectification queue unavailable")
        raise HTTPException(status_code=503, detail="Rectification queue is temporarily unavailable")
    if not queued:
        background_tasks.add_task(process_rectification_run, run["id"], current_user.userid)
    return {**run, "queued": queued, "reused": False}


@router.get("/runs/{run_id}")
async def get_rectification_run(run_id: str, current_user: User = Depends(get_current_user)):
    run = repository.get_run(run_id=run_id, userid=current_user.userid)
    if not run:
        raise HTTPException(status_code=404, detail="Rectification run not found")
    return run


@router.get("/runs/{run_id}/results")
async def get_rectification_results(run_id: str, current_user: User = Depends(get_current_user)):
    run = repository.get_run(run_id=run_id, userid=current_user.userid)
    if not run:
        raise HTTPException(status_code=404, detail="Rectification run not found")
    if run["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Rectification run is {run['status']}")
    return run["result"]


@router.post("/internal/process")
async def process_rectification_task(
    request: Dict[str, Any],
    x_rectification_task_secret: Optional[str] = Header(
        default=None, alias="X-Rectification-Task-Secret"
    ),
):
    expected = rectification_task_secret()
    if not expected or x_rectification_task_secret != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    run_id = str(request.get("run_id") or "").strip()
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id is required")
    userid = request.get("userid")
    process_rectification_run(run_id, int(userid) if userid is not None else None)
    return {"accepted": True, "run_id": run_id}
