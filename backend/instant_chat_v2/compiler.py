"""Compile a semantic plan into calculator capability requests."""

from __future__ import annotations

from typing import Any, Dict, List

from .methodology import get_methodology


_EVIDENCE_TO_CAPABILITY = {
    "natal_topic_foundation": "parashari.topic_foundation",
    "future_dasha_event_windows": "parashari.dasha_windows",
    "historical_dasha_event_windows": "parashari.dasha_windows",
    "transit_event_windows": "transit.trigger_windows",
    "historical_transit_event_windows": "transit.trigger_windows",
    "current_dasha": "parashari.current_dasha",
    "activated_houses": "parashari.activations",
    "kp_active_houses": "kp.active_houses",
    "divisional_support": "parashari.divisional_confirmation",
    "decision_option_context": "comparison.option_specific_evidence",
}


def compile_evidence_plan(query_plan: Dict[str, Any]) -> Dict[str, Any]:
    method = get_methodology(query_plan.get("event_profile") or query_plan.get("category"), query_plan.get("answer_mode"))
    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), dict) else {}
    exact_day = bool(time_scope.get("is_exact_day"))
    if exact_day:
        # A one-day prediction is not a shortened period forecast. MD/AD/PD
        # provide permission and background, but the day is decided by the
        # five-level dasha stack, Moon/Tara Bala and KP materialisation checks.
        method = {
            **method,
            "registry_version": "instant-methodology/daily-v1",
            "operations": [
                "daily.five_level_dasha",
                "daily.moon_tara_bala",
                "daily.kp_fructification",
                "daily.school_synthesis",
            ],
            "claim_operations": [],
            "required_for_timing": [
                "daily.five_level_dasha",
                "daily.moon_tara_bala",
                "daily.kp_fructification",
            ],
            "confidence_operations": {
                "high_confidence": ["daily.school_synthesis"],
                "high_support": [],
            },
        }
    routing_only = query_plan.get("answer_mode") in {"compound_plan", "dedicated_partnership_flow"}
    confidence_operations = method.get("confidence_operations") if isinstance(method.get("confidence_operations"), dict) else {}
    high_confidence = set(confidence_operations.get("high_confidence") or [])
    high_support = set(confidence_operations.get("high_support") or [])
    operations: List[str] = []
    for operation in method.get("operations", []) + method.get("claim_operations", []):
        if operation not in operations:
            operations.append(operation)
    if not routing_only and not exact_day:
        for requested in query_plan.get("requested_evidence", []):
            operation = _EVIDENCE_TO_CAPABILITY.get(str(requested), str(requested))
            if operation and operation not in operations:
                operations.append(operation)
    requests = [
        {
            "request_id": f"cap-{index + 1:02d}",
            "capability": operation,
            "status": "requested",
            "required": operation in method.get("required_for_timing", []),
            "confidence_role": (
                "high_support" if operation in high_support
                else "high_confidence" if operation in high_confidence
                else "mandatory" if operation in method.get("required_for_timing", [])
                else "supporting"
            ),
        }
        for index, operation in enumerate(operations)
    ]
    return {
        "schema_version": "instant-evidence-plan/v1",
        "methodology_version": method["registry_version"],
        "domain": method["domain"],
        "focus_houses": method.get("focus_houses", []),
        "support_houses": method.get("support_houses", []),
        "friction_houses": method.get("friction_houses", []),
        "capability_requests": requests,
        "claim_prerequisites": method.get("required_for_timing", []),
        "confidence_prerequisites": confidence_operations,
        "forecast_shape": "daily_forecast" if exact_day else None,
    }
