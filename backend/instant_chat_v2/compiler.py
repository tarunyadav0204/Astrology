"""Compile a semantic plan into calculator capability requests."""

from __future__ import annotations

from typing import Any, Dict, List

from .methodology import get_methodology


_EVIDENCE_TO_CAPABILITY = {
    "natal_topic_foundation": "parashari.topic_foundation",
    "future_dasha_event_windows": "parashari.dasha_windows",
    "transit_event_windows": "transit.trigger_windows",
    "current_dasha": "parashari.current_dasha",
    "activated_houses": "parashari.activations",
    "kp_active_houses": "kp.active_houses",
    "divisional_support": "parashari.divisional_confirmation",
    "decision_option_context": "comparison.option_specific_evidence",
}


def compile_evidence_plan(query_plan: Dict[str, Any]) -> Dict[str, Any]:
    method = get_methodology(query_plan.get("event_profile") or query_plan.get("category"), query_plan.get("answer_mode"))
    operations: List[str] = []
    for operation in method.get("operations", []) + method.get("claim_operations", []):
        if operation not in operations:
            operations.append(operation)
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
    }
