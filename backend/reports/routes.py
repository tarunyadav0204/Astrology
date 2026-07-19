from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, Query

from auth import User, get_current_user
from credits.credit_service import CreditService
from db import execute, get_conn
from .models import (
    PartnershipReportRequest,
    WealthReportRequest,
    HealthReportRequest,
    JanamKundliReportRequest,
    ReportBranding,
)
from .branding import get_saved_report_branding, save_report_branding
from .orchestrator import (
    build_and_cache_partnership_report,
    build_and_cache_wealth_report,
    build_and_cache_health_report,
    build_and_cache_janam_kundli_report,
    process_partnership_report_job,
)
from .cache.report_hash import build_pair_hash, build_subject_hash, normalize_language
from .cache.report_storage import (
    create_report_job,
    get_cached_report,
    get_latest_active_report_job,
    get_latest_completed_report_job,
    get_report_job,
    update_report_job,
)
from .report_registry import list_supported_report_types
from .report_types import (
    PARTNERSHIP_REPORT_CONFIG,
    WEALTH_REPORT_CONFIG,
    HEALTH_REPORT_CONFIG,
    JANAM_KUNDLI_REPORT_CONFIG,
)
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
    native = request_data.get("birth_data") or pair.get("native") or {}
    score_summary = result_data.get("score_summary") or {}
    score_value = score_summary.get("percentage")
    if score_value is None:
        score_value = score_summary.get("score")
    if score_value is None:
        score_value = score_summary.get("wealth_score")
    if score_value is None:
        score_value = score_summary.get("health_score")

    boy_pair = pair.get("boy") if isinstance(pair.get("boy"), dict) else {}
    girl_pair = pair.get("girl") if isinstance(pair.get("girl"), dict) else {}
    native_pair = pair.get("native") if isinstance(pair.get("native"), dict) else {}
    report_type = str(job.get("report_type") or "report").strip()
    if report_type == "wealth":
        person_a_name = native.get("name") or native_pair.get("name") or boy.get("name") or boy_pair.get("name") or "Native"
        person_b_name = ""
        title = premium.get("headline") or "Wealth report"
        subtitle = premium.get("wealth_verdict") or premium.get("headline") or score_summary.get("verdict") or "Ready to open"
    elif report_type == "health":
        person_a_name = native.get("name") or native_pair.get("name") or boy.get("name") or boy_pair.get("name") or "Native"
        person_b_name = ""
        title = premium.get("headline") or "Health report"
        subtitle = premium.get("health_verdict") or premium.get("headline") or score_summary.get("verdict") or "Ready to open"
    elif report_type == "janam_kundli":
        person_a_name = native.get("name") or native_pair.get("name") or boy.get("name") or boy_pair.get("name") or "Native"
        person_b_name = ""
        title = premium.get("headline") or "Janam Kundli report"
        subtitle = premium.get("janam_verdict") or premium.get("headline") or score_summary.get("verdict") or "Ready to open"
    else:
        person_a_name = boy.get("name") or boy_pair.get("name") or "Person A"
        person_b_name = girl.get("name") or girl_pair.get("name") or "Person B"
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


@router.post("/partnership/existing")
async def lookup_existing_partnership_report(
    request: PartnershipReportRequest,
    current_user: User = Depends(get_current_user),
):
    """Check for a completed/cached report, or an in-progress job, for this pair+language."""
    resolved_language = normalize_language(request.language)
    subject_hash = build_pair_hash(
        request.boy_birth_data,
        request.girl_birth_data,
        request.report_type,
        resolved_language,
    )
    report_version = PARTNERSHIP_REPORT_CONFIG.key + "_v6_nakshatra_nature"

    job = get_latest_completed_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    cached = get_cached_report(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    active = get_latest_active_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )

    if not job and not cached and not active:
        return {
            "exists": False,
            "report_id": None,
            "status": None,
            "has_pdf": False,
            "cached": False,
            "in_progress": False,
        }

    # Prefer a finished report when available.
    if job or cached:
        result_data = {}
        report_id = None
        if job:
            report_id = job.get("report_id")
            result_data = job.get("result_data") if isinstance(job.get("result_data"), dict) else {}
        if cached and isinstance(cached, dict):
            if not result_data:
                result_data = cached
            if not report_id:
                report_id = cached.get("report_id")
            if report_id and not job:
                existing_job = get_report_job(str(report_id), get_conn, execute)
                if (
                    not existing_job
                    or int(existing_job.get("userid") or 0) != int(current_user.userid)
                    or str(existing_job.get("status") or "").lower() != "completed"
                ):
                    pass

        has_pdf = bool(result_data.get("pdf_gcs_path") or result_data.get("pdf_url"))
        return {
            "exists": True,
            "report_id": report_id,
            "status": "completed",
            "has_pdf": has_pdf,
            "cached": True,
            "in_progress": False,
            "language": resolved_language,
            "report_type": request.report_type,
            "report_version": report_version,
        }

    active_status = str(active.get("status") or "pending").lower()
    if active_status not in ("pending", "processing"):
        active_status = "pending"
    return {
        "exists": True,
        "report_id": active.get("report_id"),
        "status": active_status,
        "has_pdf": False,
        "cached": False,
        "in_progress": True,
        "language": resolved_language,
        "report_type": request.report_type,
        "report_version": report_version,
    }


@router.post("/partnership/start")
async def start_partnership_report_job(
    request: PartnershipReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    resolved_language = normalize_language(request.language)
    subject_hash = build_pair_hash(request.boy_birth_data, request.girl_birth_data, request.report_type, resolved_language)
    report_version = PARTNERSHIP_REPORT_CONFIG.key + "_v6_nakshatra_nature"
    request_json = json.dumps(request.model_dump() if hasattr(request, "model_dump") else request.dict())
    cached = None
    if not request.force_regenerate:
        # Resume an already-running job for this pair instead of starting a duplicate.
        active = get_latest_active_report_job(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
        if active and active.get("report_id"):
            status = str(active.get("status") or "pending").lower()
            return {
                "success": True,
                "report_id": active.get("report_id"),
                "status": status if status in ("pending", "processing") else "pending",
                "message": "Partnership report already in progress.",
                "resumed": True,
            }
        cached = get_cached_report(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
    report_id = str(uuid.uuid4())
    if cached is None:
        cost = credit_service.get_effective_cost(
            current_user.userid,
            credit_service.get_credit_setting("partnership_report_cost"),
            "partnership_report_cost",
        )
        balance = credit_service.get_user_credits(current_user.userid)
        if balance < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You need {cost} credits.",
            )

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


@router.post("/wealth/existing")
async def lookup_existing_wealth_report(
    request: WealthReportRequest,
    current_user: User = Depends(get_current_user),
):
    resolved_language = normalize_language(request.language)
    subject_hash = build_subject_hash(request.birth_data, request.report_type, resolved_language)
    report_version = WEALTH_REPORT_CONFIG.key + "_v1"

    job = get_latest_completed_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    cached = get_cached_report(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    active = get_latest_active_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )

    if not job and not cached and not active:
        return {
            "exists": False,
            "report_id": None,
            "status": None,
            "has_pdf": False,
            "cached": False,
            "in_progress": False,
        }

    if job or cached:
        result_data = {}
        report_id = None
        if job:
            report_id = job.get("report_id")
            result_data = job.get("result_data") if isinstance(job.get("result_data"), dict) else {}
        if cached and isinstance(cached, dict):
            if not result_data:
                result_data = cached
            if not report_id:
                report_id = cached.get("report_id")
        has_pdf = bool(result_data.get("pdf_gcs_path") or result_data.get("pdf_url"))
        return {
            "exists": True,
            "report_id": report_id,
            "status": "completed",
            "has_pdf": has_pdf,
            "cached": True,
            "in_progress": False,
            "language": resolved_language,
            "report_type": request.report_type,
            "report_version": report_version,
        }

    active_status = str(active.get("status") or "pending").lower()
    if active_status not in ("pending", "processing"):
        active_status = "pending"
    return {
        "exists": True,
        "report_id": active.get("report_id"),
        "status": active_status,
        "has_pdf": False,
        "cached": False,
        "in_progress": True,
        "language": resolved_language,
        "report_type": request.report_type,
        "report_version": report_version,
    }


@router.post("/wealth/start")
async def start_wealth_report_job(
    request: WealthReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    if not WEALTH_REPORT_CONFIG.enabled:
        raise HTTPException(status_code=404, detail="Wealth report is not enabled")

    resolved_language = normalize_language(request.language)
    subject_hash = build_subject_hash(request.birth_data, request.report_type, resolved_language)
    report_version = WEALTH_REPORT_CONFIG.key + "_v1"
    request_json = json.dumps(request.model_dump() if hasattr(request, "model_dump") else request.dict())
    cached = None
    if not request.force_regenerate:
        active = get_latest_active_report_job(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
        if active and active.get("report_id"):
            status = str(active.get("status") or "pending").lower()
            return {
                "success": True,
                "report_id": active.get("report_id"),
                "status": status if status in ("pending", "processing") else "pending",
                "message": "Wealth report already in progress.",
                "resumed": True,
            }
        cached = get_cached_report(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
    report_id = str(uuid.uuid4())
    if cached is None:
        cost = credit_service.get_effective_cost(
            current_user.userid,
            credit_service.get_credit_setting("wealth_report_cost"),
            "wealth_report_cost",
        )
        balance = credit_service.get_user_credits(current_user.userid)
        if balance < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You need {cost} credits.",
            )

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
            _run_wealth_report_job,
            report_id,
            current_user.userid,
            request,
        )

    return {
        "success": True,
        "report_id": report_id,
        "status": "pending",
        "message": "Wealth report started.",
    }


@router.get("/wealth/status/{report_id}")
async def get_wealth_report_status(report_id: str, current_user: User = Depends(get_current_user)):
    return await get_partnership_report_status(report_id, current_user)


@router.get("/wealth/{report_id}")
async def get_wealth_report(report_id: str, current_user: User = Depends(get_current_user)):
    return await get_partnership_report(report_id, current_user)


@router.post("/health/existing")
async def lookup_existing_health_report(
    request: HealthReportRequest,
    current_user: User = Depends(get_current_user),
):
    resolved_language = normalize_language(request.language)
    subject_hash = build_subject_hash(request.birth_data, request.report_type, resolved_language)
    report_version = HEALTH_REPORT_CONFIG.key + "_v1"

    job = get_latest_completed_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    cached = get_cached_report(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    active = get_latest_active_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )

    if not job and not cached and not active:
        return {
            "exists": False,
            "report_id": None,
            "status": None,
            "has_pdf": False,
            "cached": False,
            "in_progress": False,
        }

    if job or cached:
        result_data = {}
        report_id = None
        if job:
            report_id = job.get("report_id")
            result_data = job.get("result_data") if isinstance(job.get("result_data"), dict) else {}
        if cached and isinstance(cached, dict):
            if not result_data:
                result_data = cached
            if not report_id:
                report_id = cached.get("report_id")
        has_pdf = bool(result_data.get("pdf_gcs_path") or result_data.get("pdf_url"))
        return {
            "exists": True,
            "report_id": report_id,
            "status": "completed",
            "has_pdf": has_pdf,
            "cached": True,
            "in_progress": False,
            "language": resolved_language,
            "report_type": request.report_type,
            "report_version": report_version,
        }

    active_status = str(active.get("status") or "pending").lower()
    if active_status not in ("pending", "processing"):
        active_status = "pending"
    return {
        "exists": True,
        "report_id": active.get("report_id"),
        "status": active_status,
        "has_pdf": False,
        "cached": False,
        "in_progress": True,
        "language": resolved_language,
        "report_type": request.report_type,
        "report_version": report_version,
    }


@router.post("/health/start")
async def start_health_report_job(
    request: HealthReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    if not HEALTH_REPORT_CONFIG.enabled:
        raise HTTPException(status_code=404, detail="Health report is not enabled")

    resolved_language = normalize_language(request.language)
    subject_hash = build_subject_hash(request.birth_data, request.report_type, resolved_language)
    report_version = HEALTH_REPORT_CONFIG.key + "_v1"
    request_json = json.dumps(request.model_dump() if hasattr(request, "model_dump") else request.dict())
    cached = None
    if not request.force_regenerate:
        active = get_latest_active_report_job(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
        if active and active.get("report_id"):
            status = str(active.get("status") or "pending").lower()
            return {
                "success": True,
                "report_id": active.get("report_id"),
                "status": status if status in ("pending", "processing") else "pending",
                "message": "Health report already in progress.",
                "resumed": True,
            }
        cached = get_cached_report(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
    report_id = str(uuid.uuid4())
    if cached is None:
        cost = credit_service.get_effective_cost(
            current_user.userid,
            credit_service.get_credit_setting("health_report_cost"),
            "health_report_cost",
        )
        balance = credit_service.get_user_credits(current_user.userid)
        if balance < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You need {cost} credits.",
            )

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
            _run_health_report_job,
            report_id,
            current_user.userid,
            request,
        )

    return {
        "success": True,
        "report_id": report_id,
        "status": "pending",
        "message": "Health report started.",
    }


@router.get("/health/status/{report_id}")
async def get_health_report_status(report_id: str, current_user: User = Depends(get_current_user)):
    return await get_partnership_report_status(report_id, current_user)


@router.get("/health/{report_id}")
async def get_health_report(report_id: str, current_user: User = Depends(get_current_user)):
    return await get_partnership_report(report_id, current_user)


@router.post("/janam_kundli/existing")
async def lookup_existing_janam_kundli_report(
    request: JanamKundliReportRequest,
    current_user: User = Depends(get_current_user),
):
    resolved_language = normalize_language(request.language)
    subject_hash = build_subject_hash(request.birth_data, request.report_type, resolved_language)
    report_version = JANAM_KUNDLI_REPORT_CONFIG.key + "_v2"

    job = get_latest_completed_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    cached = get_cached_report(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )
    active = get_latest_active_report_job(
        current_user.userid,
        request.report_type,
        subject_hash,
        resolved_language,
        report_version,
        get_conn,
        execute,
    )

    if not job and not cached and not active:
        return {
            "exists": False,
            "report_id": None,
            "status": None,
            "has_pdf": False,
            "cached": False,
            "in_progress": False,
        }

    if job or cached:
        result_data = {}
        report_id = None
        if job:
            report_id = job.get("report_id")
            result_data = job.get("result_data") if isinstance(job.get("result_data"), dict) else {}
        if cached and isinstance(cached, dict):
            if not result_data:
                result_data = cached
            if not report_id:
                report_id = cached.get("report_id")
        has_pdf = bool(result_data.get("pdf_gcs_path") or result_data.get("pdf_url"))
        return {
            "exists": True,
            "report_id": report_id,
            "status": "completed",
            "has_pdf": has_pdf,
            "cached": True,
            "in_progress": False,
            "language": resolved_language,
            "report_type": request.report_type,
            "report_version": report_version,
        }

    active_status = str(active.get("status") or "pending").lower()
    if active_status not in ("pending", "processing"):
        active_status = "pending"
    return {
        "exists": True,
        "report_id": active.get("report_id"),
        "status": active_status,
        "has_pdf": False,
        "cached": False,
        "in_progress": True,
        "language": resolved_language,
        "report_type": request.report_type,
        "report_version": report_version,
    }


@router.get("/branding")
async def get_report_branding(current_user: User = Depends(get_current_user)):
    branding = get_saved_report_branding(current_user.userid, get_conn, execute)
    return {"success": True, "branding": branding}


@router.put("/branding")
async def put_report_branding(
    branding: ReportBranding,
    current_user: User = Depends(get_current_user),
):
    saved = save_report_branding(current_user.userid, branding, get_conn, execute)
    return {"success": True, "branding": saved}


@router.post("/janam_kundli/start")
async def start_janam_kundli_report_job(
    request: JanamKundliReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    if not JANAM_KUNDLI_REPORT_CONFIG.enabled:
        raise HTTPException(status_code=404, detail="Janam Kundli report is not enabled")

    resolved_language = normalize_language(request.language)
    if resolved_language not in {"english", "hindi"}:
        raise HTTPException(status_code=400, detail="Janam Kundli supports english and hindi only")

    # Persist branding from the generate form so next run is prefilled.
    if request.branding is not None:
        save_report_branding(current_user.userid, request.branding, get_conn, execute)

    subject_hash = build_subject_hash(request.birth_data, request.report_type, resolved_language)
    report_version = JANAM_KUNDLI_REPORT_CONFIG.key + "_v2"
    request_json = json.dumps(request.model_dump() if hasattr(request, "model_dump") else request.dict())
    cached = None
    if not request.force_regenerate:
        active = get_latest_active_report_job(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
        if active and active.get("report_id"):
            status = str(active.get("status") or "pending").lower()
            return {
                "success": True,
                "report_id": active.get("report_id"),
                "status": status if status in ("pending", "processing") else "pending",
                "message": "Janam Kundli report already in progress.",
                "resumed": True,
            }
        cached = get_cached_report(
            current_user.userid,
            request.report_type,
            subject_hash,
            resolved_language,
            report_version,
            get_conn,
            execute,
        )
    report_id = str(uuid.uuid4())
    if cached is None:
        cost = credit_service.get_effective_cost(
            current_user.userid,
            credit_service.get_credit_setting("janam_kundli_report_cost"),
            "janam_kundli_report_cost",
        )
        balance = credit_service.get_user_credits(current_user.userid)
        if balance < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You need {cost} credits.",
            )

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
            _run_janam_kundli_report_job,
            report_id,
            current_user.userid,
            request,
        )

    return {
        "success": True,
        "report_id": report_id,
        "status": "pending",
        "message": "Janam Kundli report started.",
    }


@router.get("/janam_kundli/status/{report_id}")
async def get_janam_kundli_report_status(report_id: str, current_user: User = Depends(get_current_user)):
    return await get_partnership_report_status(report_id, current_user)


@router.get("/janam_kundli/{report_id}")
async def get_janam_kundli_report(report_id: str, current_user: User = Depends(get_current_user)):
    return await get_partnership_report(report_id, current_user)


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


async def _run_wealth_report_job(report_id: str, userid: int, request: WealthReportRequest):
    try:
        update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
        payload = await build_and_cache_wealth_report(
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


async def _run_health_report_job(report_id: str, userid: int, request: HealthReportRequest):
    try:
        update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
        payload = await build_and_cache_health_report(
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


async def _run_janam_kundli_report_job(report_id: str, userid: int, request: JanamKundliReportRequest):
    try:
        update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
        payload = await build_and_cache_janam_kundli_report(
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

        if report_type == "wealth":
            request = WealthReportRequest.model_validate(request_data)
            update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
            payload = await build_and_cache_wealth_report(
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

        if report_type == "health":
            request = HealthReportRequest.model_validate(request_data)
            update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
            payload = await build_and_cache_health_report(
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

        if report_type == "janam_kundli":
            request = JanamKundliReportRequest.model_validate(request_data)
            update_report_job(report_id, status="processing", get_conn=get_conn, execute_fn=execute)
            payload = await build_and_cache_janam_kundli_report(
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
