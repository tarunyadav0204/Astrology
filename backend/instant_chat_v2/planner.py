"""Typed query planning from already-LLM-derived intent metadata."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import Any, Dict, List


def _strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _date_text(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else None


def _add_months(iso_day: str | None, months: Any) -> str | None:
    try:
        start = date.fromisoformat(str(iso_day))
        count = max(0, int(months))
        month_index = start.month - 1 + count
        year = start.year + month_index // 12
        month = month_index % 12 + 1
        return date(year, month, min(start.day, monthrange(year, month)[1])).isoformat()
    except (TypeError, ValueError):
        return None


def build_query_plan(
    *, question: str, intent: Dict[str, Any] | None, answer_mode: str,
    target_subject: Dict[str, Any] | None, language: str, as_of: Any = None,
) -> Dict[str, Any]:
    """Build a strict plan without interpreting raw wording.

    `intent` is produced by the Flash/Flash-Lite intent router.  Raw question is
    retained only for audit and composition, never inspected for keywords here.
    """
    intent = intent if isinstance(intent, dict) else {}
    query_context = intent.get("query_context") if isinstance(intent.get("query_context"), dict) else {}
    extracted = intent.get("extracted_context") if isinstance(intent.get("extracted_context"), dict) else {}
    router_evidence_plan = intent.get("evidence_plan") if isinstance(intent.get("evidence_plan"), dict) else {}
    question_parts = router_evidence_plan.get("question_parts") if isinstance(router_evidence_plan.get("question_parts"), list) else []
    semantic_timeframe = next(
        (
            part.get("timeframe")
            for part in question_parts
            if isinstance(part, dict) and part.get("timeframe") not in (None, "", {})
        ),
        None,
    )
    category = str(intent.get("category") or query_context.get("event_profile") or "general").strip().lower()
    requested = _strings(query_context.get("required_evidence"))
    if not requested:
        requested = _strings(intent.get("required_evidence"))
    for need in (
        router_evidence_plan.get("evidence_needs")
        if isinstance(router_evidence_plan.get("evidence_needs"), list)
        else []
    ):
        kind = str((need or {}).get("kind") or "").strip() if isinstance(need, dict) else ""
        if kind and kind not in requested:
            requested.append(kind)
    certainty = str(query_context.get("certainty") or intent.get("certainty") or "probabilistic")
    semantic_kind = str((semantic_timeframe or {}).get("kind") or "none").strip().lower()
    relation = str(intent.get("time_relation") or extracted.get("time_scope") or "").strip().lower()
    semantic_value = (semantic_timeframe or {}).get("value")
    semantic_duration = (semantic_timeframe or {}).get("duration")
    duration_months = (semantic_timeframe or {}).get("duration_months")
    if duration_months is None:
        try:
            amount = int((semantic_timeframe or {}).get("amount"))
            unit = str((semantic_timeframe or {}).get("unit") or "").strip().lower()
            if unit in {"month", "months"}:
                duration_months = amount
            elif unit in {"year", "years"}:
                duration_months = amount * 12
        except (TypeError, ValueError):
            duration_months = None
    as_of_day = _date_text(as_of)
    horizon_end = _add_months(as_of_day, duration_months)
    if str(answer_mode or "") == "event_prediction" and (
        semantic_value not in (None, "") or semantic_duration not in (None, "")
    ):
        relation = "current_to_future"
    elif semantic_kind not in {"", "none", "current", "past"}:
        relation = "current_to_future" if semantic_kind in {"relative_range", "rolling_window"} else "future"
    elif not relation:
        relation = "current_or_next"
    return {
        "schema_version": "instant-query-plan/v1",
        "planner_source": "llm_intent_router",
        "question": str(question or "").strip(),
        "language": str(language or "english").strip().lower(),
        "category": category,
        "answer_mode": str(answer_mode or "topic_reading"),
        "target_subject": target_subject or intent.get("target_subject") or {"key": "self", "label": "self"},
        "time_scope": {
            "requested": extracted.get("timeframe") or query_context.get("time_scope"),
            "semantic": semantic_timeframe,
            "relation": relation,
            "as_of": as_of_day,
            "horizon_end": horizon_end,
        },
        "event_profile": query_context.get("event_profile") or category,
        "requested_evidence": requested,
        "requested_precision": query_context.get("requested_precision") or "best_supported",
        "comparison_options": [
            {
                "part_id": part.get("part_id"),
                "event_profile": part.get("event_profile"),
                "life_domain": part.get("life_domain"),
            }
            for part in question_parts
            if isinstance(part, dict) and part.get("event_profile")
        ] if str(answer_mode or "") == "comparison_choice" else [],
        "certainty_policy": certainty,
        "clarification": {
            "needed": bool(intent.get("needs_clarification")),
            "reason": intent.get("clarification_reason"),
        },
        "interpretation_frame": (
            "native_chart"
            if str((target_subject or intent.get("target_subject") or {}).get("key") or "self") == "self"
            else "native_chart_derived_house"
        ),
    }
