from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


SCHEMA_VERSION = "evidence_plan.v1"

INTENT_FAMILIES = {
    "event_timing",
    "topic_outlook",
    "factual_chart_lookup",
    "chart_interpretation",
    "causal_diagnosis",
    "decision_guidance",
    "comparison",
    "compatibility",
    "remedy_request",
    "personality_or_traits",
    "period_forecast",
    "system_specific_analysis",
    "conversational_followup",
    "unsafe_or_blocked",
}

LIFE_DOMAINS = {
    "marriage",
    "relationship",
    "career",
    "wealth",
    "health",
    "education",
    "exam",
    "progeny",
    "property",
    "relocation",
    "travel",
    "personality",
    "family",
    "spirituality",
    "legal",
    "business",
    "pets",
    "dreams",
    "general",
}

EVENT_PROFILES = {
    "marriage",
    "promotion",
    "job_change",
    "first_job",
    "childbirth",
    "conception",
    "relationship_reconciliation",
    "meeting_partner",
    "health_recovery",
    "exam_success",
    "weight_loss",
    "appearance_glow_up",
    "property_purchase",
    "foreign_travel",
    "relocation",
    "business_start",
    "debt_resolution",
    "general_event",
}

EVIDENCE_NEED_KINDS = {
    "chart_fact_lookup",
    "natal_topic_foundation",
    "current_dasha_stack",
    "dasha_timeline_lookup",
    "future_dasha_event_windows",
    "transit_event_windows",
    "period_forecast_context",
    "divisional_chart_context",
    "house_analysis",
    "planet_analysis",
    "yoga_analysis",
    "ashtakavarga_analysis",
    "jaimini_analysis",
    "kp_cusp_analysis",
    "compatibility_context",
    "decision_option_context",
    "remedy_context",
    "safety_refusal_context",
}

ASTROLOGY_SYSTEMS = {
    "parashari",
    "vimshottari",
    "transits",
    "divisional_charts",
    "jaimini",
    "chara_dasha",
    "yogini_dasha",
    "ashtakavarga",
    "kp",
    "tajika",
    "nadi",
    "lal_kitab",
    "numerology",
    "unspecified",
}

PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
DASHA_LEVELS = {"mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana"}
LOOKUP_OPERATIONS = {"get_current", "find_start_end", "find_next", "find_previous", "list_periods", "explain_result", "compare"}
SUBJECT_TYPES = {"self", "spouse", "partner", "ex_partner", "potential_partner", "child", "parent", "sibling", "friend", "other_person", "unborn_child", "unknown"}
TIMEFRAME_KINDS = {"none", "current", "open_future", "bounded_future", "specific_date", "date_range", "relative_day", "relative_week", "relative_month", "relative_year", "named_period", "past", "recurring"}
GRANULARITIES = {"exact_fact", "day", "week", "month_window", "quarter_window", "year_window", "multi_year_window", "life_phase"}
PRIORITIES = {"required", "recommended", "optional"}
CONFIDENCES = {"high", "medium", "low"}
CLARIFICATION_REASONS = {"missing_subject", "missing_timeframe", "missing_partner_details", "ambiguous_chart_system", "ambiguous_event", "multiple_unrelated_questions", "unsafe_request", "not_needed"}
SAFETY_CHECKS = {"death_prediction", "fetal_sex_determination", "medical_emergency", "self_harm", "illegal_harmful_action", "no_fatalism", "no_guaranteed_prediction", "no_unsupported_exact_date"}
ANSWER_STYLES = {"speech_concise", "chat_concise", "detailed", "technical", "step_by_step", "comparison_table", "remedy_focused"}


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _enum(value: Any, allowed: set[str], default: str) -> str:
    raw = str(value or "").strip()
    if raw in allowed:
        return raw
    by_lower = {item.lower(): item for item in allowed}
    return by_lower.get(raw.lower(), default)


def _enum_ci(value: Any, allowed: set[str], default: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return default
    by_lower = {item.lower(): item for item in allowed}
    return by_lower.get(raw.lower(), default)


def _normalize_timeframe(value: Any) -> Dict[str, Any]:
    raw = value if isinstance(value, dict) else {"kind": "none"}
    out = dict(raw)
    out["kind"] = _enum_ci(out.get("kind"), TIMEFRAME_KINDS, "none")
    if "granularity" in out:
        out["granularity"] = _enum_ci(out.get("granularity"), GRANULARITIES, "multi_year_window")
    return out


def _normalize_need_params(kind: str, params: Any) -> Dict[str, Any]:
    out = dict(params) if isinstance(params, dict) else {}
    if "event_profile" in out:
        out["event_profile"] = _enum_ci(out.get("event_profile"), EVENT_PROFILES, "general_event")
    if "granularity" in out:
        out["granularity"] = _enum_ci(out.get("granularity"), GRANULARITIES, "multi_year_window")
    if kind == "dasha_timeline_lookup":
        planet = _enum_ci(out.get("planet"), PLANETS, "")
        if planet:
            out["planet"] = planet
        else:
            out.pop("planet", None)
        out["level"] = _enum_ci(out.get("level"), DASHA_LEVELS, "mahadasha")
        out["operation"] = _enum_ci(out.get("operation"), LOOKUP_OPERATIONS, "find_start_end")
    return out


def default_evidence_plan(question: str = "") -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "question_parts": [
            {
                "part_id": "p1",
                "text": str(question or "").strip(),
                "intent_families": ["topic_outlook"],
                "life_domain": "general",
                "event_profile": None,
                "subject": "self",
                "timeframe": _normalize_timeframe({"kind": "none"}),
                "confidence": "medium",
            }
        ],
        "evidence_needs": [],
        "safety": {
            "blocked_content_checks": [
                {"check_id": "death_prediction", "action_if_detected": "refuse_and_redirect"},
                {"check_id": "fetal_sex_determination", "action_if_detected": "refuse_and_redirect"},
            ],
            "answer_safety_checks": ["no_fatalism", "no_guaranteed_prediction", "no_unsupported_exact_date"],
        },
        "answer_plan": {
            "style": "chat_concise",
            "must_answer_parts": ["p1"],
            "answer_order": ["p1"],
        },
    }


def normalize_evidence_plan(plan: Any, *, question: str = "") -> Dict[str, Any]:
    if not isinstance(plan, dict):
        return default_evidence_plan(question)
    out = deepcopy(plan)
    out["schema_version"] = SCHEMA_VERSION

    parts = []
    for idx, raw in enumerate(_as_list(out.get("question_parts")) or default_evidence_plan(question)["question_parts"]):
        if not isinstance(raw, dict):
            continue
        part_id = str(raw.get("part_id") or f"p{idx + 1}")
        parts.append(
            {
                "part_id": part_id,
                "text": str(raw.get("text") or question or "").strip(),
                "intent_families": [
                    _enum(item, INTENT_FAMILIES, "topic_outlook")
                    for item in _as_list(raw.get("intent_families") or raw.get("intent_family"))
                ] or ["topic_outlook"],
                "life_domain": _enum(raw.get("life_domain"), LIFE_DOMAINS, "general"),
                "event_profile": None if raw.get("event_profile") in (None, "") else _enum(raw.get("event_profile"), EVENT_PROFILES, "general_event"),
                "subject": _enum(raw.get("subject"), SUBJECT_TYPES, "self"),
                "timeframe": _normalize_timeframe(raw.get("timeframe")),
                "confidence": _enum(raw.get("confidence"), CONFIDENCES, "medium"),
            }
        )
    out["question_parts"] = parts or default_evidence_plan(question)["question_parts"]

    needs = []
    valid_part_ids = {p["part_id"] for p in out["question_parts"]}
    for idx, raw in enumerate(_as_list(out.get("evidence_needs"))):
        if not isinstance(raw, dict):
            continue
        kind = _enum(raw.get("kind"), EVIDENCE_NEED_KINDS, "natal_topic_foundation")
        params = _normalize_need_params(kind, raw.get("params"))
        supports = [str(p) for p in _as_list(raw.get("supports_parts")) if str(p) in valid_part_ids]
        needs.append(
            {
                "need_id": str(raw.get("need_id") or f"n{idx + 1}"),
                "kind": kind,
                "system": _enum(raw.get("system"), ASTROLOGY_SYSTEMS, "unspecified"),
                "topic": _enum(raw.get("topic"), LIFE_DOMAINS, "general"),
                "supports_parts": supports or [out["question_parts"][0]["part_id"]],
                "params": params,
                "priority": _enum(raw.get("priority"), PRIORITIES, "required"),
            }
        )
    out["evidence_needs"] = needs

    safety = out.get("safety") if isinstance(out.get("safety"), dict) else {}
    blocked = safety.get("blocked_content_checks") if isinstance(safety.get("blocked_content_checks"), list) else []
    if not blocked:
        blocked = default_evidence_plan(question)["safety"]["blocked_content_checks"]
    answer_checks = [
        _enum(item, SAFETY_CHECKS, "no_fatalism")
        for item in _as_list(safety.get("answer_safety_checks"))
    ] or default_evidence_plan(question)["safety"]["answer_safety_checks"]
    out["safety"] = {
        "blocked_content_checks": blocked,
        "answer_safety_checks": list(dict.fromkeys(answer_checks)),
    }

    answer_plan = out.get("answer_plan") if isinstance(out.get("answer_plan"), dict) else {}
    out["answer_plan"] = {
        "style": _enum(answer_plan.get("style"), ANSWER_STYLES, "chat_concise"),
        "must_answer_parts": [str(p) for p in _as_list(answer_plan.get("must_answer_parts")) if str(p) in valid_part_ids] or [out["question_parts"][0]["part_id"]],
        "answer_order": [str(p) for p in _as_list(answer_plan.get("answer_order")) if str(p) in valid_part_ids] or [out["question_parts"][0]["part_id"]],
    }
    return out
