"""Admin endpoints for premium report generation history."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_user
from chat_history.admin_routes import _resolve_model_rate, _usd_to_inr_rate
from db import execute, get_conn

from .cache.report_storage import ensure_report_jobs_table
from .pdf_service import sign_report_pdf_url

router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])

_IST = ZoneInfo("Asia/Kolkata")


def require_admin(current_user=Depends(get_current_user)):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _normalize_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
) -> tuple[Optional[date], Optional[date]]:
    if not start_date and not end_date:
        return None, None
    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="Provide both start_date and end_date (YYYY-MM-DD)")
    try:
        sdate = date.fromisoformat(str(start_date).strip())
        edate = date.fromisoformat(str(end_date).strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD") from exc
    if sdate > edate:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")
    return sdate, edate


def _timestamp_to_ist_iso(val) -> Optional[str]:
    if val is None:
        return None
    try:
        if isinstance(val, str):
            raw = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
        elif isinstance(val, datetime):
            dt = val
        else:
            return str(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(_IST).isoformat()
    except Exception:
        return str(val)


def _safe_json_loads(value: Any) -> Dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return {}


def _duration_seconds(started_at, completed_at) -> Optional[int]:
    if not started_at or not completed_at:
        return None
    try:
        start = started_at if isinstance(started_at, datetime) else datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        end = completed_at if isinstance(completed_at, datetime) else datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return max(0, int((end - start).total_seconds()))
    except Exception:
        return None


def _tokens_cost_inr(
    *,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int,
    non_cached_input_tokens: int,
    cache_setup_input_tokens: int,
    model: Optional[str],
    fx: float,
    chapters_generated: int = 0,
) -> Dict[str, Any]:
    input_t = int(input_tokens or 0)
    output_t = int(output_tokens or 0)
    cached_t = int(cached_input_tokens or 0)
    non_cached_t = int(non_cached_input_tokens or 0)
    setup_t = int(cache_setup_input_tokens or 0)
    if non_cached_t <= 0 and input_t > 0:
        non_cached_t = max(input_t - cached_t, 0)

    # Gemini >200k price tier is per API request. Multi-chapter reports sum tokens
    # across parallel chapter calls — use average per chapter for tier selection.
    chapters = max(0, int(chapters_generated or 0))
    tier_basis = max(input_t, non_cached_t)
    if chapters > 1 and input_t > 0:
        tier_basis = max(1, int(round(input_t / chapters)))

    rates = _resolve_model_rate(model, tier_basis)
    input_rate = float(rates["input"])
    cached_rate = float(rates.get("cached_input") or rates["input"])
    output_rate = float(rates["output"])

    input_cost_non_cached_inr = (non_cached_t / 1_000_000.0) * input_rate * fx
    input_cost_cached_inr = (cached_t / 1_000_000.0) * cached_rate * fx
    cache_setup_cost_inr = (setup_t / 1_000_000.0) * input_rate * fx
    output_cost_inr = (output_t / 1_000_000.0) * output_rate * fx
    # What those cached tokens would have cost at full input rate.
    gemini_cache_savings_inr = (cached_t / 1_000_000.0) * max(input_rate - cached_rate, 0.0) * fx
    total_cost_inr = input_cost_non_cached_inr + input_cost_cached_inr + cache_setup_cost_inr + output_cost_inr

    return {
        "rates": rates,
        "non_cached_input_tokens": non_cached_t,
        "cached_input_tokens": cached_t,
        "cache_setup_input_tokens": setup_t,
        "tier_basis_tokens": tier_basis,
        "input_cost_non_cached_inr": input_cost_non_cached_inr,
        "input_cost_cached_inr": input_cost_cached_inr,
        "cache_setup_cost_inr": cache_setup_cost_inr,
        "output_cost_inr": output_cost_inr,
        "total_cost_inr": total_cost_inr,
        "gemini_cache_savings_inr": gemini_cache_savings_inr,
    }


def _avoided_cost_inr(avoided: Any, model: Optional[str], fx: float) -> float:
    if not isinstance(avoided, dict):
        return 0.0
    priced = _tokens_cost_inr(
        input_tokens=int(avoided.get("input_tokens") or 0),
        output_tokens=int(avoided.get("output_tokens") or 0),
        cached_input_tokens=int(avoided.get("cached_input_tokens") or avoided.get("cached_tokens") or 0),
        non_cached_input_tokens=int(avoided.get("non_cached_input_tokens") or 0),
        cache_setup_input_tokens=int(avoided.get("cache_setup_input_tokens") or 0),
        model=model,
        fx=fx,
        chapters_generated=int(avoided.get("chapters_generated") or 0),
    )
    # Avoided spend valued at what those tokens would have cost if billed again.
    return float(priced["total_cost_inr"])


def _build_report_cost_summary(llm_usage: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(llm_usage, dict):
        return None

    fx = _usd_to_inr_rate()
    model = (llm_usage.get("model") or "").strip() or None
    chapters_generated = int(llm_usage.get("chapters_generated") or 0)
    priced = _tokens_cost_inr(
        input_tokens=int(llm_usage.get("input_tokens") or 0),
        output_tokens=int(llm_usage.get("output_tokens") or 0),
        cached_input_tokens=int(llm_usage.get("cached_input_tokens") or 0),
        non_cached_input_tokens=int(llm_usage.get("non_cached_input_tokens") or 0),
        cache_setup_input_tokens=int(llm_usage.get("cache_setup_input_tokens") or 0),
        model=model,
        fx=fx,
        chapters_generated=chapters_generated,
    )
    chapter_savings = _avoided_cost_inr(llm_usage.get("avoided_by_chapter_cache"), model, fx)
    document_savings = _avoided_cost_inr(llm_usage.get("avoided_by_document_cache"), model, fx)
    gemini_savings = float(priced["gemini_cache_savings_inr"])
    total_savings = chapter_savings + document_savings + gemini_savings
    rates = priced["rates"]

    return {
        "currency": "INR",
        "usd_to_inr_rate": fx,
        "model": model,
        "input_usd_per_1m": float(rates["input"]),
        "cached_input_usd_per_1m": float(rates.get("cached_input") or rates["input"]),
        "output_usd_per_1m": float(rates["output"]),
        "pricing_tier": rates.get("tier"),
        "pricing_tier_basis_tokens": int(priced.get("tier_basis_tokens") or 0),
        "input_cost_non_cached_inr_estimate": round(float(priced["input_cost_non_cached_inr"]), 6),
        "input_cost_cached_inr_estimate": round(float(priced["input_cost_cached_inr"]), 6),
        "cache_setup_cost_inr_estimate": round(float(priced["cache_setup_cost_inr"]), 6),
        "output_cost_inr_estimate": round(float(priced["output_cost_inr"]), 6),
        "total_cost_inr_estimate": round(float(priced["total_cost_inr"]), 6),
        "gemini_context_cache_savings_inr_estimate": round(gemini_savings, 6),
        "chapter_db_cache_savings_inr_estimate": round(chapter_savings, 6),
        "document_cache_savings_inr_estimate": round(document_savings, 6),
        "cache_savings_inr_estimate": round(total_savings, 6),
        "note": (
            "Estimated from model-reported tokens. "
            "Cost is this job's actual spend; cache savings include Gemini cached-input discount, "
            "chapter DB cache hits (prior chapter usage), and full document reopen. "
            "Pricing tier uses average tokens per chapter when chapters_generated is set."
        ),
    }


def _build_admin_report_item(row: Dict[str, Any]) -> Dict[str, Any]:
    request_data = _safe_json_loads(row.get("request_json"))
    result_data = _safe_json_loads(row.get("result_data"))
    premium = result_data.get("premium_report") or {}
    pair = result_data.get("pair") or {}
    boy = request_data.get("boy_birth_data") or pair.get("boy") or {}
    girl = request_data.get("girl_birth_data") or pair.get("girl") or {}
    boy_pair = pair.get("boy") if isinstance(pair.get("boy"), dict) else {}
    girl_pair = pair.get("girl") if isinstance(pair.get("girl"), dict) else {}
    score_summary = result_data.get("score_summary") or {}
    score_value = score_summary.get("percentage")
    if score_value is None:
        score_value = score_summary.get("score")

    cached = bool(result_data.get("cached"))
    credits_charged = result_data.get("credits_charged")
    if credits_charged is None:
        credits_charged = 0 if cached else None
    else:
        try:
            credits_charged = int(credits_charged)
        except (TypeError, ValueError):
            credits_charged = None

    has_pdf = bool(result_data.get("pdf_gcs_path")) and str(row.get("status") or "").lower() == "completed"
    pdf_url = None
    if has_pdf and result_data.get("pdf_gcs_path"):
        try:
            pdf_url = sign_report_pdf_url(result_data["pdf_gcs_path"])
        except Exception:
            pdf_url = None

    llm_usage = result_data.get("llm_usage")
    if not isinstance(llm_usage, dict):
        llm_usage = premium.get("llm_usage") if isinstance(premium.get("llm_usage"), dict) else None
    cost_summary = _build_report_cost_summary(llm_usage)

    return {
        "report_id": row.get("report_id"),
        "userid": row.get("userid"),
        "user_name": row.get("user_name") or "Unknown User",
        "user_phone": row.get("user_phone") or "",
        "report_type": row.get("report_type"),
        "language": row.get("language"),
        "status": row.get("status"),
        "report_version": row.get("report_version"),
        "subject_hash": row.get("subject_hash"),
        "created_at": _timestamp_to_ist_iso(row.get("created_at")),
        "started_at": _timestamp_to_ist_iso(row.get("started_at")),
        "completed_at": _timestamp_to_ist_iso(row.get("completed_at")),
        "duration_seconds": _duration_seconds(row.get("started_at"), row.get("completed_at")),
        "person_a_name": boy.get("name") or boy_pair.get("name") or "Person A",
        "person_b_name": girl.get("name") or girl_pair.get("name") or "Person B",
        "title": premium.get("headline") or f"{str(row.get('report_type') or 'report').title()} report",
        "score": score_value,
        "cached": cached,
        "credits_charged": credits_charged,
        "has_pdf": has_pdf,
        "pdf_url": pdf_url,
        "error_message": row.get("error_message") or None,
        "llm_model": (llm_usage or {}).get("model") if isinstance(llm_usage, dict) else None,
        "llm_input_tokens": int((llm_usage or {}).get("input_tokens") or 0) if isinstance(llm_usage, dict) else None,
        "llm_output_tokens": int((llm_usage or {}).get("output_tokens") or 0) if isinstance(llm_usage, dict) else None,
        "llm_cached_input_tokens": int((llm_usage or {}).get("cached_input_tokens") or 0) if isinstance(llm_usage, dict) else None,
        "llm_non_cached_input_tokens": int((llm_usage or {}).get("non_cached_input_tokens") or 0) if isinstance(llm_usage, dict) else None,
        "llm_cache_setup_input_tokens": int((llm_usage or {}).get("cache_setup_input_tokens") or 0) if isinstance(llm_usage, dict) else None,
        "llm_total_tokens": int((llm_usage or {}).get("total_tokens") or 0) if isinstance(llm_usage, dict) else None,
        "chapters_generated": (llm_usage or {}).get("chapters_generated") if isinstance(llm_usage, dict) else None,
        "chapters_from_db_cache": (llm_usage or {}).get("chapters_from_db_cache") if isinstance(llm_usage, dict) else None,
        "document_cache_hit": bool((llm_usage or {}).get("document_cache_hit")) if isinstance(llm_usage, dict) else False,
        "cost_summary": cost_summary,
    }


@router.get("/history")
async def admin_list_report_history(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user=Depends(require_admin),
):
    """Admin list of all report generation jobs with date-range and user filters."""
    sdate, edate = _normalize_date_range(start_date, end_date)
    offset = (page - 1) * limit

    where_parts: List[str] = ["1=1"]
    where_params: List[Any] = []

    if user_name and str(user_name).strip():
        where_parts.append("COALESCE(u.name, '') ILIKE %s")
        where_params.append(f"%{str(user_name).strip()}%")
    if sdate and edate:
        where_parts.append(
            "COALESCE(rgj.completed_at, rgj.created_at)::date >= %s "
            "AND COALESCE(rgj.completed_at, rgj.created_at)::date <= %s"
        )
        where_params.extend([sdate, edate])
    if report_type and str(report_type).strip() and str(report_type).strip().lower() != "all":
        where_parts.append("LOWER(rgj.report_type) = LOWER(%s)")
        where_params.append(str(report_type).strip())
    if status and str(status).strip() and str(status).strip().lower() != "all":
        where_parts.append("LOWER(rgj.status) = LOWER(%s)")
        where_params.append(str(status).strip())

    where_sql = " AND ".join(where_parts)

    try:
        with get_conn() as conn:
            ensure_report_jobs_table(conn, execute)
            cur = execute(
                conn,
                f"""
                SELECT COUNT(*)
                FROM report_generation_jobs rgj
                LEFT JOIN users u ON u.userid = rgj.userid
                WHERE {where_sql}
                """,
                tuple(where_params),
            )
            total = int((cur.fetchone() or [0])[0] or 0)

            cur = execute(
                conn,
                f"""
                SELECT
                    rgj.report_id,
                    rgj.userid,
                    rgj.report_type,
                    rgj.subject_hash,
                    rgj.language,
                    rgj.status,
                    rgj.request_json,
                    rgj.result_data,
                    rgj.error_message,
                    rgj.report_version,
                    rgj.created_at,
                    rgj.started_at,
                    rgj.completed_at,
                    u.name AS user_name,
                    u.phone AS user_phone
                FROM report_generation_jobs rgj
                LEFT JOIN users u ON u.userid = rgj.userid
                WHERE {where_sql}
                ORDER BY COALESCE(rgj.completed_at, rgj.created_at) DESC
                LIMIT %s OFFSET %s
                """,
                tuple(where_params) + (limit, offset),
            )
            rows = cur.fetchall() or []
            columns = [d[0] for d in (cur.description or [])]

        items = []
        for raw in rows:
            row = dict(zip(columns, raw))
            items.append(_build_admin_report_item(row))

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if limit else 0,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error fetching report history: {exc}") from exc
