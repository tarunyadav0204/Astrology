from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, Query

from auth import User, get_current_user
from credits.credit_service import CreditService
from db import execute, get_conn
from .models import PartnershipReportRequest
from .orchestrator import build_and_cache_partnership_report, process_partnership_report_job
from .cache.report_hash import build_pair_hash, normalize_language
from .cache.report_storage import create_report_job, get_report_job, update_report_job
from .report_registry import list_supported_report_types
from .report_types import PARTNERSHIP_REPORT_CONFIG
from .pdf_service import sign_report_pdf_url, store_report_pdf
from .task_queue import (
    enqueue_report_processing_task,
    local_report_tasks_enabled,
    report_task_secret,
    report_tasks_enabled,
)

router = APIRouter(prefix="/reports", tags=["reports"])
credit_service = CreditService()


def _safe_json_loads(value: Any) -> Dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return {}


def _attach_pdf_url(payload: Dict[str, Any]) -> Dict[str, Any]:
    pdf_gcs_path = payload.get("pdf_gcs_path")
    if pdf_gcs_path:
        try:
            payload["pdf_url"] = sign_report_pdf_url(pdf_gcs_path)
        except Exception:
            payload.pop("pdf_url", None)
    return payload


def _build_report_history_item(job: Dict[str, Any]) -> Dict[str, Any]:
    request_data = _safe_json_loads(job.get("request_json"))
    result_data = _safe_json_loads(job.get("result_data"))
    premium = result_data.get("premium_report") or {}
    pair = result_data.get("pair") or {}
    boy = request_data.get("boy_birth_data") or pair.get("boy") or {}
    girl = request_data.get("girl_birth_data") or pair.get("girl") or {}
    score_summary = result_data.get("score_summary") or {}
    score_value = score_summary.get("percentage")
    if score_value is None:
        score_value = score_summary.get("score")

    boy_pair = pair.get("boy") if isinstance(pair.get("boy"), dict) else {}
    girl_pair = pair.get("girl") if isinstance(pair.get("girl"), dict) else {}
    person_a_name = boy.get("name") or boy_pair.get("name") or "Person A"
    person_b_name = girl.get("name") or girl_pair.get("name") or "Person B"
    report_type = str(job.get("report_type") or "report").strip()
    title = premium.get("headline") or f"{report_type.title()} report"
    subtitle = premium.get("compatibility_verdict") or premium.get("headline") or score_summary.get("verdict") or "Ready to open"

    return {
        "report_id": job.get("report_id"),
        "report_type": report_type,
        "status": job.get("status"),
        "language": job.get("language"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "person_a_name": person_a_name,
        "person_b_name": person_b_name,
        "title": title,
        "subtitle": subtitle,
        "score": score_value,
        "has_pdf": bool(result_data.get("pdf_gcs_path")) and job.get("status") == "completed",
        "cached": bool(result_data.get("cached")),
    }


@router.get("/history")
async def list_report_history(
    report_type: Optional[str] = Query(None, description="Optional report type filter"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    where_clauses = ["userid = %s"]
    params: list[Any] = [current_user.userid]
    if report_type:
        where_clauses.append("LOWER(report_type) = LOWER(%s)")
        params.append(report_type)
    if status:
        where_clauses.append("LOWER(status) = LOWER(%s)")
        params.append(status)
    params.extend([limit, offset])

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT report_id, userid, report_type, subject_hash, language, status, request_json, result_data, error_message, report_version, created_at, started_at, completed_at
            FROM report_generation_jobs
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """.format(where=" AND ".join(where_clauses)),
            tuple(params),
        )
        rows = cur.fetchall() or []

    items = []
    for row in rows:
        job = {
            "report_id": row[0],
            "userid": row[1],
            "report_type": row[2],
            "subject_hash": row[3],
            "language": row[4],
            "status": row[5],
            "request_json": row[6],
            "result_data": row[7],
            "error_message": row[8],
            "report_version": row[9],
            "created_at": row[10],
            "started_at": row[11],
            "completed_at": row[12],
        }
        items.append(_build_report_history_item(job))

    return {
        "success": True,
        "data": items,
        "count": len(items),
        "offset": offset,
        "limit": limit,
    }


@router.get("/types")
async def list_report_types(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": list_supported_report_types(),
    }


@router.post("/partnership/generate")
async def generate_partnership_report(
    request: PartnershipReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    return await start_partnership_report_job(request, background_tasks, current_user)


@router.post("/partnership/start")
async def start_partnership_report_job(
    request: PartnershipReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    report_id = str(uuid.uuid4())
    resolved_language = normalize_language(request.language)
    subject_hash = build_pair_hash(request.boy_birth_data, request.girl_birth_data, request.report_type, resolved_language)
    report_version = PARTNERSHIP_REPORT_CONFIG.key + "_v1"
    request_json = json.dumps(request.model_dump() if hasattr(request, "model_dump") else request.dict())

    create_report_job(
        report_id,
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        request_json,
        report_version,
        get_conn,
        execute,
    )

    queued = enqueue_report_processing_task(report_id=report_id)
    if not queued:
        if report_tasks_enabled() and not local_report_tasks_enabled():
            update_report_job(
                report_id,
                status="failed",
                error_message="Report worker queue unavailable",
                get_conn=get_conn,
                execute_fn=execute,
            )
            raise HTTPException(
                status_code=503,
                detail="Report worker queue unavailable. Please try again in a moment.",
            )
        background_tasks.add_task(
            _run_partnership_report_job,
            report_id,
            current_user.userid,
            request,
        )

    return {
        "success": True,
        "report_id": report_id,
        "status": "pending",
        "message": "Partnership report started.",
    }


@router.post("/internal/process")
async def process_report_task(
    request: dict,
    x_report_task_secret: str | None = Header(None, alias="X-Report-Task-Secret"),
):
    expected_secret = report_task_secret()
    if not expected_secret or x_report_task_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    report_id = str(request.get("report_id") or "").strip()
    if not report_id:
        raise HTTPException(status_code=400, detail="report_id is required")

    return await _process_report_job(report_id)


@router.get("/partnership/status/{report_id}")
async def get_partnership_report_status(report_id: str, current_user: User = Depends(get_current_user)):
    job = get_report_job(report_id, get_conn, execute)
    if not job or int(job.get("userid")) != int(current_user.userid):
        raise HTTPException(status_code=404, detail="Report not found")
    out = {
        "success": True,
        "report_id": report_id,
        "status": job.get("status"),
        "report_type": job.get("report_type"),
        "language": job.get("language"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
    }
    if job.get("status") == "completed" and job.get("result_data"):
        out["data"] = _attach_pdf_url(job.get("result_data") or {})
    elif job.get("status") == "failed":
        out["error"] = job.get("error_message") or "Report generation failed"
    return out


@router.get("/partnership/{report_id}")
async def get_partnership_report(report_id: str, current_user: User = Depends(get_current_user)):
    job = get_report_job(report_id, get_conn, execute)
    if not job or int(job.get("userid")) != int(current_user.userid):
        raise HTTPException(status_code=404, detail="Report not found")
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Report is not completed yet")
    return {
        "success": True,
        "report_id": report_id,
        "data": _attach_pdf_url(job.get("result_data") or {}),
    }


async def _run_partnership_report_job(report_id: str, userid: int, request: PartnershipReportRequest):
    try:
        update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
        payload = await build_and_cache_partnership_report(
            userid,
            request,
            credit_service=credit_service,
            get_conn=get_conn,
            execute_fn=execute,
            report_id=report_id,
        )
        if not payload.get("report_type"):
            raise RuntimeError(payload.get("error") or "Report generation failed")
        update_report_job(report_id, status="completed", result_data=payload, get_conn=get_conn, execute_fn=execute)
    except Exception as exc:
        update_report_job(report_id, status="failed", error_message=str(exc), get_conn=get_conn, execute_fn=execute)


async def _process_report_job(report_id: str):
    job = get_report_job(report_id, get_conn, execute)
    if not job:
        raise HTTPException(status_code=404, detail="Report not found")

    if job.get("status") == "completed" and job.get("result_data"):
        result_data = _attach_pdf_url(job.get("result_data") or {})
        return {
            "success": True,
            "report_id": report_id,
            "status": "completed",
            "data": result_data,
            "cached": True,
        }

    try:
        report_type = job.get("report_type")
        request_json = job.get("request_json") or "{}"
        request_data = json.loads(request_json)

        if report_type == "partnership":
            request = PartnershipReportRequest.model_validate(request_data)
            update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
            payload = await build_and_cache_partnership_report(
                int(job.get("userid")),
                request,
                credit_service=credit_service,
                get_conn=get_conn,
                execute_fn=execute,
                report_id=report_id,
            )
            if not payload.get("report_type"):
                raise RuntimeError(payload.get("error") or "Report generation failed")
            update_report_job(report_id, status="completed", result_data=payload, get_conn=get_conn, execute_fn=execute)
            return {
                "success": True,
                "report_id": report_id,
                "status": "completed",
                "data": _attach_pdf_url(payload),
            }

        raise HTTPException(status_code=400, detail=f"Unsupported report type: {report_type}")
    except HTTPException:
        update_report_job(report_id, status="failed", error_message="Unsupported report type", get_conn=get_conn, execute_fn=execute)
        raise
    except Exception as exc:
        update_report_job(report_id, status="failed", error_message=str(exc), get_conn=get_conn, execute_fn=execute)
        raise


@router.get("/pdf/{report_id}")
async def get_report_pdf_url(report_id: str, current_user: User = Depends(get_current_user)):
    job = get_report_job(report_id, get_conn, execute)
    if not job or int(job.get("userid")) != int(current_user.userid):
        raise HTTPException(status_code=404, detail="Report not found")
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Report is not completed yet")

    result_data = _safe_json_loads(job.get("result_data"))
    if not result_data:
        raise HTTPException(status_code=404, detail="PDF is not available yet")

    if not result_data.get("pdf_gcs_path"):
        try:
            result_data = store_report_pdf(result_data)
            update_report_job(report_id, status="completed", result_data={**_safe_json_loads(job.get("result_data")), **result_data}, get_conn=get_conn, execute_fn=execute)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Could not create PDF: {exc}") from exc

    return {
        "success": True,
        "report_id": report_id,
        "pdf_url": sign_report_pdf_url(result_data["pdf_gcs_path"]),
        "pdf_gcs_path": result_data["pdf_gcs_path"],
        "pdf_expires_in_s": result_data.get("pdf_expires_in_s", 86400),
    }
