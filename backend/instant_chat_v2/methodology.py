"""Versioned methodology registry used by the evidence-plan compiler."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


REGISTRY_VERSION = "2026.08.16-v1"

_COMMON = {
    "natal_promise": ["parashari.topic_foundation", "parashari.house_lords"],
    "current_state": ["parashari.current_dasha", "parashari.activations"],
    "timing": ["parashari.dasha_windows", "transit.trigger_windows"],
}

_DOMAINS: Dict[str, Dict[str, Any]] = {
    "marriage": {
        "focus_houses": [2, 7, 11],
        "support_houses": [5],
        "friction_houses": [1, 6, 8, 10, 12],
        "operations": [
            "parashari.marriage_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d9_confirmation",
            "kp.seventh_cusp_chain",
            "kp.active_houses",
            "jaimini.darakaraka_upapada",
            "transit.marriage_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.marriage_triggers"],
    },
    "career": {
        "focus_houses": [2, 6, 10, 11],
        "support_houses": [1, 5, 9],
        "friction_houses": [8, 12],
        "operations": [
            "parashari.career_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d10_confirmation",
            "kp.tenth_cusp_chain",
            "kp.active_houses",
            "jaimini.amatyakaraka",
            "transit.career_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.career_triggers"],
    },
    "relationship": {
        "focus_houses": [2, 5, 7, 11],
        "support_houses": [9],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.relationship_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "parashari.d9_confirmation",
            "kp.seventh_cusp_chain",
            "kp.active_houses",
            "transit.relationship_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "kp.active_houses"],
    },
    "wealth": {
        "focus_houses": [2, 5, 9, 11],
        "support_houses": [10],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.wealth_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "kp.active_houses",
            "transit.wealth_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "parashari.activations"],
    },
    "health": {
        "focus_houses": [1, 6, 8, 12],
        "support_houses": [5, 9, 11],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.health_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "kp.active_houses",
            "transit.health_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "parashari.activations"],
    },
    "progeny": {
        "focus_houses": [2, 5, 11],
        "support_houses": [9],
        "friction_houses": [1, 4, 10],
        "operations": [
            "parashari.progeny_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d7_confirmation",
            "kp.fifth_cusp_chain",
            "kp.active_houses",
            "transit.progeny_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.progeny_triggers"],
    },
    "general": {
        "focus_houses": [],
        "support_houses": [],
        "friction_houses": [],
        "operations": ["parashari.current_dasha", "parashari.activations", "kp.active_houses"],
        "required_for_timing": ["parashari.current_dasha"],
    },
}

_ALIASES = {
    "marriage_timing": "marriage",
    "marriage_analysis": "marriage",
    "love": "relationship",
    "relationships": "relationship",
    "finance": "wealth",
    "money": "wealth",
    "career_analysis": "career",
    "childbirth": "progeny",
    "children": "progeny",
}


def get_methodology(category: str, answer_mode: str) -> Dict[str, Any]:
    raw = str(category or "general").strip().lower().replace("-", "_").replace(" ", "_")
    key = _ALIASES.get(raw, raw)
    if key not in _DOMAINS:
        key = "general"
    result = deepcopy(_DOMAINS[key])
    result.update({"registry_version": REGISTRY_VERSION, "domain": key})
    if answer_mode in {"event_timing", "lifetime_event_timing", "month_timing", "event_prediction", "timing_window"}:
        result["claim_operations"] = deepcopy(_COMMON["timing"])
    elif answer_mode in {"natal_topic", "topic_reading"}:
        result["claim_operations"] = deepcopy(_COMMON["natal_promise"])
    else:
        result["claim_operations"] = deepcopy(_COMMON["current_state"])
    if answer_mode == "comparison_choice":
        result.setdefault("operations", []).append("comparison.option_specific_evidence")
        result.setdefault("required_for_timing", []).append("comparison.option_specific_evidence")
    if key == "health":
        result.setdefault("operations", []).append("parashari.health_body_area")
        result.setdefault("required_for_timing", []).append("parashari.health_body_area")
    return result
