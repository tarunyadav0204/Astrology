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


def _is_retrospective_semantic_value(value: Any) -> bool:
    """Normalize only typed router values, never the user's question text."""
    token = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return bool(
        token in {"past", "open_past", "historical", "retrospective"}
        or token.startswith(("past_", "historical_", "retrospective_"))
        or token.endswith("_past")
    )


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
    dialogue = (
        extracted.get("instant_dialogue")
        if isinstance(extracted.get("instant_dialogue"), dict)
        else intent.get("dialogue_state") if isinstance(intent.get("dialogue_state"), dict)
        else {}
    )
    known_facts = dialogue.get("known_facts") if isinstance(dialogue.get("known_facts"), dict) else {}
    confirmed_event_date = _date_text(
        known_facts.get("confirmed_event_date")
        or known_facts.get("confirmed_date")
        or known_facts.get("actual_event_date")
    )
    confirmed_event_source = str(known_facts.get("event_date_source") or "").strip().lower()
    category = str(intent.get("category") or query_context.get("event_profile") or "general").strip().lower()
    route_action = str(intent.get("route_action") or "answer").strip().lower()
    if route_action not in {"answer", "clarify", "handoff"}:
        route_action = "answer"
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
    dialogue_time_direction = str(
        known_facts.get("timing_type")
        or known_facts.get("timing_direction")
        or known_facts.get("time_relation")
        or known_facts.get("time_direction")
        or ""
    ).strip().lower()
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
    requested_historical = any(
        str(value or "").strip().lower().startswith("historical_")
        for value in requested
    )
    retrospective_signal = bool(
        _is_retrospective_semantic_value(semantic_kind)
        or _is_retrospective_semantic_value(relation)
        or _is_retrospective_semantic_value(dialogue_time_direction)
        or requested_historical
    )
    # Grammatical past tense is not automatically a historical event-timing
    # request.  "Did I have a love or arranged marriage?" is a static pathway
    # comparison and must not trigger historical dasha/transit scans.  Only
    # timing/event-discovery modes may promote past semantics into a
    # retrospective calculation.
    retrospective_event_mode = str(answer_mode or "").strip().lower() in {
        "event_prediction", "event_timing", "lifetime_event_timing",
        "month_timing", "timing_window", "daily_forecast",
    }
    retrospective = bool(retrospective_signal and retrospective_event_mode)
    if retrospective and semantic_kind in {"", "none", "current"}:
        semantic_timeframe = {
            "kind": "open_past",
            "source": "router_dialogue_known_facts",
        }
        semantic_kind = "open_past"
    if retrospective:
        requested = [
            value for value in requested
            if value not in {"future_dasha_event_windows", "transit_event_windows"}
        ]
        for value in (
            "historical_dasha_event_windows",
            "historical_transit_event_windows",
            "natal_topic_foundation",
        ):
            if value not in requested:
                requested.append(value)
    resolved_period = intent.get("period_window") if isinstance(intent.get("period_window"), dict) else {}
    resolved_period_kind = str(resolved_period.get("kind") or "").strip().lower()
    exact_day = bool(
        resolved_period_kind == "day"
        or str(intent.get("mode") or "").strip().upper() == "PREDICT_DAILY"
    )
    target_day = _date_text(
        resolved_period.get("start")
        or resolved_period.get("date")
        or resolved_period.get("target_date")
        or as_of_day
    ) if exact_day else None
    # Prefer the semantic router's resolved calendar boundary.  A request such
    # as "this year" means the remainder of that calendar year, not a rolling
    # twelve months from today.
    resolved_horizon_end = _date_text(
        resolved_period.get("end")
        or resolved_period.get("horizon_end")
    ) if resolved_period else None
    # A rolling/bounded request such as "next 6 months" can arrive alongside
    # a generic period_window resolved to the router's current day.  That
    # current-day boundary is context, not the requested horizon.  Explicit
    # calendar periods ("this year", a named month, or an exact range) still
    # keep their resolved end date.
    rolling_duration_kinds = {"bounded_future", "rolling_window"}
    if retrospective:
        horizon_end = as_of_day
    elif duration_months is not None and semantic_kind in rolling_duration_kinds:
        horizon_end = _add_months(as_of_day, duration_months)
    else:
        horizon_end = resolved_horizon_end or _add_months(as_of_day, duration_months)
    if retrospective:
        relation = "past"
    elif retrospective_signal and _is_retrospective_semantic_value(relation):
        # Preserve grammatical/semantic past tense for static readings without
        # promoting them into historical event calculations.
        relation = "past"
    elif str(answer_mode or "") == "event_prediction" and (
        semantic_value not in (None, "") or semantic_duration not in (None, "")
    ):
        relation = "current_to_future"
    elif semantic_kind not in {"", "none", "current", "past"}:
        relation = "current_to_future" if semantic_kind in {"relative_range", "rolling_window"} else "future"
    elif not relation:
        relation = "current_or_next"
    if str(answer_mode or "") == "remedy_action":
        # Remedy selection is a static calculated-action route. Incidental
        # router horizons must not turn it into a forecast contract.
        relation = "static"
        horizon_end = None
        target_day = None
        exact_day = False
    return {
        "schema_version": "instant-query-plan/v1",
        "planner_source": "llm_intent_router",
        "question": str(question or "").strip(),
        "language": str(language or "english").strip().lower(),
        "category": category,
        "career_subtype": intent.get("career_subtype") or query_context.get("career_subtype"),
        "career_target": intent.get("career_target") or query_context.get("career_target"),
        "career_target_structure": (
            intent.get("career_target_structure")
            or query_context.get("career_target_structure")
            or "unspecified"
        ),
        "career_target_traits": (
            intent.get("career_target_traits")
            if isinstance(intent.get("career_target_traits"), list)
            else query_context.get("career_target_traits") or []
        ),
        "marriage_subtype": intent.get("marriage_subtype") or query_context.get("marriage_subtype"),
        "wealth_subtype": intent.get("wealth_subtype") or query_context.get("wealth_subtype"),
        "education_subtype": intent.get("education_subtype") or query_context.get("education_subtype"),
        "education_target": intent.get("education_target") or query_context.get("education_target"),
        "education_target_traits": (
            intent.get("education_target_traits")
            if isinstance(intent.get("education_target_traits"), list)
            else query_context.get("education_target_traits") or []
        ),
        "education_options": (
            intent.get("education_options")
            if isinstance(intent.get("education_options"), list)
            else query_context.get("education_options") or []
        ),
        "children_subtype": intent.get("children_subtype") or query_context.get("children_subtype"),
        "home_subtype": intent.get("home_subtype") or query_context.get("home_subtype"),
        "prior_marriage_context": extracted.get("prior_marriage_context"),
        "answer_mode": str(answer_mode or "topic_reading"),
        "route_action": route_action,
        "user_goal": (
            query_context.get("user_goal")
            or intent.get("user_goal")
            or extracted.get("user_goal")
        ),
        "target_subject": target_subject or intent.get("target_subject") or {"key": "self", "label": "self"},
        "time_scope": {
            "requested": extracted.get("timeframe") or query_context.get("time_scope"),
            "semantic": semantic_timeframe,
            "relation": relation,
            "as_of": as_of_day,
            "horizon_end": horizon_end,
            "granularity": "day" if exact_day else semantic_kind,
            "is_exact_day": exact_day,
            "target_date": target_day,
            "retrospective": retrospective,
        },
        "event_profile": query_context.get("event_profile") or category,
        "confirmed_life_event": ({
            "date": confirmed_event_date,
            "source": "user_confirmed",
            "category": category,
            "claim_rule": (
                "Treat this as a fact supplied by the user. It may be used to verify calculated factors "
                "on that date, but must never be described as a date recovered or proven by astrology."
            ),
        } if confirmed_event_date and confirmed_event_source == "user_confirmed" else None),
        "special_flow": {
            "requested_chart": extracted.get("requested_chart"),
            "requested_fact": extracted.get("requested_fact"),
            "spouse_detail_scope": extracted.get("spouse_detail_scope"),
            "location_scope": extracted.get("location_scope"),
            "location_goal": extracted.get("location_goal") or category,
            "hub_regions": extracted.get("hub_regions") or [],
            "muhurat_event_type": extracted.get("muhurat_event_type"),
            "muhurat_start_date": extracted.get("muhurat_start_date"),
            "muhurat_end_date": extracted.get("muhurat_end_date"),
            "muhurat_use_birth_location": extracted.get("muhurat_use_birth_location"),
            "muhurat_location_query": extracted.get("muhurat_location_query"),
        },
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
            "needed": bool(intent.get("needs_clarification")) or route_action == "clarify",
            "reason": intent.get("clarification_reason"),
            "user_message": intent.get("user_message") or intent.get("clarification_question"),
        },
        "interpretation_frame": (
            "native_chart"
            if str((target_subject or intent.get("target_subject") or {}).get("key") or "self") == "self"
            else "native_chart_derived_house"
        ),
    }
