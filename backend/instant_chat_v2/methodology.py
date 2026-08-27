"""Versioned methodology registry used by the evidence-plan compiler."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


REGISTRY_VERSION = "2026.08.16-v1"

_COMMON = {
    "natal_promise": ["parashari.topic_foundation", "parashari.house_lords"],
    "current_state": ["parashari.current_dasha", "parashari.activations"],
    "timing": [
        "parashari.dasha_windows",
        "transit.trigger_windows",
        "transit.double_transit",
        "parashari.divisional_confirmation",
        "parashari.karaka_support",
        "nadi.domain_synthesis",
    ],
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
    "business": {
        "focus_houses": [2, 7, 10, 11],
        "support_houses": [1, 3, 5, 9],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.business_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d10_confirmation",
            "kp.seventh_cusp_chain",
            "kp.tenth_cusp_chain",
            "kp.active_houses",
            "transit.business_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.business_triggers"],
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
            "parashari.health_body_area",
            "parashari.d3_confirmation",
            "parashari.d30_confirmation",
            "parashari.current_dasha",
            "parashari.activations",
            "kp.sixth_cusp_chain",
            "kp.eighth_cusp_chain",
            "kp.twelfth_cusp_chain",
            "kp.active_houses",
            "transit.health_triggers",
        ],
        "required_for_timing": ["parashari.health_body_area"],
    },
    "mental_wellbeing": {
        "focus_houses": [1, 4, 5, 6, 8, 12],
        "support_houses": [5, 9, 11],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.mental_wellbeing_foundation",
            "parashari.health_body_area",
            "parashari.d9_confirmation",
            "parashari.d30_confirmation",
            "parashari.current_dasha",
            "parashari.activations",
            "kp.fourth_cusp_chain",
            "kp.active_houses",
            "transit.mental_wellbeing_triggers",
        ],
        "required_for_timing": ["parashari.health_body_area"],
    },
    "surgery": {
        "focus_houses": [1, 6, 8, 12],
        "support_houses": [5, 9, 11],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.surgery_promise",
            "parashari.health_body_area",
            "parashari.d6_confirmation",
            "parashari.d8_confirmation",
            "parashari.d30_confirmation",
            "parashari.dasha_windows",
            "parashari.activations",
            "kp.sixth_cusp_chain",
            "kp.eighth_cusp_chain",
            "kp.twelfth_cusp_chain",
            "kp.active_houses",
            "transit.surgery_triggers",
            "transit.double_transit",
        ],
        "required_for_timing": ["parashari.dasha_windows", "parashari.health_body_area"],
    },
    "accident": {
        "focus_houses": [1, 3, 6, 8, 12],
        "support_houses": [5, 9, 11],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.accident_promise",
            "parashari.health_body_area",
            "parashari.d3_confirmation",
            "parashari.d8_confirmation",
            "parashari.d30_confirmation",
            "parashari.dasha_windows",
            "parashari.activations",
            "kp.sixth_cusp_chain",
            "kp.eighth_cusp_chain",
            "kp.active_houses",
            "transit.accident_triggers",
            "transit.double_transit",
        ],
        "required_for_timing": ["parashari.dasha_windows", "parashari.health_body_area"],
    },
    "recovery": {
        "focus_houses": [1, 5, 6, 8, 11, 12],
        "support_houses": [1, 5, 9, 11],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.recovery_promise",
            "parashari.health_body_area",
            "parashari.d6_confirmation",
            "parashari.d30_confirmation",
            "parashari.dasha_windows",
            "parashari.activations",
            "kp.sixth_cusp_chain",
            "kp.eleventh_cusp_chain",
            "kp.twelfth_cusp_chain",
            "kp.active_houses",
            "transit.recovery_triggers",
            "parashari.karaka_support",
        ],
        "required_for_timing": ["parashari.dasha_windows", "parashari.health_body_area"],
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
    "property": {
        "focus_houses": [2, 4, 11, 12],
        "support_houses": [9],
        "friction_houses": [3, 6, 8],
        "operations": [
            "parashari.property_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d4_confirmation",
            "kp.fourth_cusp_chain",
            "kp.active_houses",
            "transit.property_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.property_triggers"],
    },
    "education": {
        "focus_houses": [2, 4, 5, 9, 11],
        "support_houses": [1, 3],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.education_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d24_confirmation",
            "kp.fourth_cusp_chain",
            "kp.ninth_cusp_chain",
            "kp.active_houses",
            "transit.education_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.education_triggers"],
    },
    "foreign": {
        "focus_houses": [3, 7, 9, 12],
        "support_houses": [4, 11],
        "friction_houses": [2, 6, 8],
        "operations": [
            "parashari.foreign_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d4_confirmation",
            "kp.ninth_cusp_chain",
            "kp.twelfth_cusp_chain",
            "kp.active_houses",
            "transit.foreign_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.foreign_triggers"],
    },
    "mother": {
        "focus_houses": [4],
        "support_houses": [2, 9, 11],
        "friction_houses": [3, 6, 8, 12],
        "operations": [
            "parashari.mother_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "parashari.d12_confirmation",
            "kp.fourth_cusp_chain",
            "kp.active_houses",
            "transit.mother_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "transit.mother_triggers"],
    },
    "father": {
        "focus_houses": [9],
        "support_houses": [2, 5, 10, 11],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.father_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "parashari.d12_confirmation",
            "kp.ninth_cusp_chain",
            "kp.active_houses",
            "transit.father_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "transit.father_triggers"],
    },
    "siblings": {
        "focus_houses": [3, 11],
        "support_houses": [2, 5, 9],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.siblings_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "parashari.d3_confirmation",
            "kp.third_cusp_chain",
            "kp.eleventh_cusp_chain",
            "kp.active_houses",
            "transit.siblings_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "transit.siblings_triggers"],
    },
    "family": {
        "focus_houses": [2, 4],
        "support_houses": [5, 7, 9, 11],
        "friction_houses": [6, 8, 12],
        "operations": [
            "parashari.family_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "parashari.d12_confirmation",
            "kp.second_cusp_chain",
            "kp.fourth_cusp_chain",
            "kp.active_houses",
            "transit.family_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "transit.family_triggers"],
    },
    "spirituality": {
        "focus_houses": [5, 8, 9, 12],
        "support_houses": [1],
        "friction_houses": [2, 3, 6, 10, 11],
        "operations": [
            "parashari.spirituality_foundation",
            "parashari.current_dasha",
            "parashari.activations",
            "parashari.d9_confirmation",
            "jaimini.karakamsha_swamsa",
            "kp.active_houses",
            "transit.spirituality_triggers",
        ],
        "required_for_timing": ["parashari.current_dasha", "transit.spirituality_triggers"],
    },
    "vehicles": {
        "focus_houses": [4, 11, 12],
        "support_houses": [2, 9],
        "friction_houses": [3, 6, 8],
        "operations": [
            "parashari.vehicles_promise",
            "parashari.dasha_windows",
            "parashari.activations",
            "parashari.d4_confirmation",
            "kp.fourth_cusp_chain",
            "kp.active_houses",
            "transit.vehicles_triggers",
        ],
        "required_for_timing": ["parashari.dasha_windows", "transit.vehicles_triggers"],
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
    "income": "wealth",
    "debt": "wealth",
    "investment": "wealth",
    "inheritance": "wealth",
    "career_analysis": "career",
    "childbirth": "progeny",
    "children": "progeny",
    "job": "career",
    "promotion": "career",
    "partner": "marriage",
    "spouse": "marriage",
    "wealth": "wealth",
    "gain": "wealth",
    "wish": "wealth",
    "disease": "health",
    "home": "property",
    "child": "progeny",
    "pregnancy": "progeny",
    "son": "progeny",
    "daughter": "progeny",
    "learning": "education",
    "travel": "foreign",
    "visa": "foreign",
    "soul": "spirituality",
    "purpose": "spirituality",
    "dharma": "spirituality",
    "timing": "general",
}


def get_methodology(category: str, answer_mode: str) -> Dict[str, Any]:
    raw = str(category or "general").strip().lower().replace("-", "_").replace(" ", "_")
    key = _ALIASES.get(raw, raw)
    if answer_mode == "factual_chart_lookup":
        result = {
            "focus_houses": [], "support_houses": [], "friction_houses": [],
            "operations": ["chart.all_supported_facts"],
            "required_for_timing": ["chart.all_supported_facts"],
        }
        key = "chart_fact"
    elif answer_mode == "location_recommendation":
        result = {
            "focus_houses": [], "support_houses": [], "friction_houses": [],
            "operations": ["location.goal_based_recommendation"],
            "required_for_timing": ["location.goal_based_recommendation"],
        }
        key = "location"
    elif answer_mode == "dedicated_muhurat_flow":
        result = {
            "focus_houses": [], "support_houses": [], "friction_houses": [],
            "operations": ["muhurat.ranked_slots"],
            "required_for_timing": ["muhurat.ranked_slots"],
        }
        key = "muhurat"
    elif answer_mode in {"dedicated_partnership_flow", "compound_plan"}:
        result = {"focus_houses": [], "support_houses": [], "friction_houses": [], "operations": [], "required_for_timing": []}
        key = "routing_only"
    else:
        if key not in _DOMAINS:
            # A newly introduced domain still receives a real, auditable base
            # methodology instead of silently degrading to a generic reading.
            result = {
                "focus_houses": [], "support_houses": [], "friction_houses": [],
                "operations": [
                    f"parashari.{key}_promise", "parashari.dasha_windows",
                    "parashari.activations", "kp.active_houses",
                    f"transit.{key}_triggers", "nadi.domain_synthesis",
                ],
                "required_for_timing": ["parashari.dasha_windows"],
            }
        else:
            result = deepcopy(_DOMAINS[key])
    result.update({"registry_version": REGISTRY_VERSION, "domain": key})
    if answer_mode in {
        "factual_chart_lookup", "location_recommendation", "dedicated_muhurat_flow",
        "dedicated_partnership_flow", "compound_plan",
    }:
        # Dedicated flows must remain visibly and operationally distinct.  Do
        # not silently attach a generic natal/current-state methodology to a
        # chart fact, location, election, handoff, or clarification request.
        result["claim_operations"] = []
    elif answer_mode in {"event_timing", "lifetime_event_timing", "month_timing", "event_prediction", "timing_window"}:
        result["claim_operations"] = deepcopy(_COMMON["timing"])
        # Dasha permission is the minimum acceptable timing evidence. Transit,
        # divisional, karaka and double-transit records raise confidence but do
        # not convert a useful limited answer into a false hard failure.
        result["required_for_timing"] = ["parashari.dasha_windows"]
        result["confidence_operations"] = {
            "high_confidence": [
                "transit.trigger_windows",
                "parashari.divisional_confirmation",
                "parashari.karaka_support",
            ],
            "high_support": ["transit.double_transit"],
        }
    elif answer_mode in {"natal_topic", "topic_reading", "potential_capacity"}:
        result["claim_operations"] = (
            ["parashari.wealth_foundation"]
            if key == "wealth"
            else deepcopy(_COMMON["natal_promise"])
        )
        if answer_mode == "potential_capacity":
            # Promise/capacity is a static chart judgment. It must be supported
            # by the domain promise calculation; current dasha activation is
            # neither necessary nor sufficient evidence for the verdict.
            promise_capability = (
                "parashari.wealth_foundation"
                if key == "wealth"
                else f"parashari.{key}_promise"
            )
            if promise_capability not in result.setdefault("operations", []):
                result["operations"].append(promise_capability)
            result["required_for_timing"] = [promise_capability]
            if key == "marriage":
                result["required_for_timing"].append("parashari.d9_confirmation")
                result["confidence_operations"] = {
                    "high_confidence": ["kp.seventh_cusp_chain"],
                    "high_support": ["jaimini.darakaraka_upapada"],
                }
    else:
        result["claim_operations"] = deepcopy(_COMMON["current_state"])
    if key == "wealth":
        operations = result.setdefault("operations", [])
        if "parashari.wealth_foundation" not in operations:
            operations.append("parashari.wealth_foundation")
        if answer_mode in {
            "event_timing", "lifetime_event_timing", "month_timing",
            "event_prediction", "timing_window", "daily_forecast", "decision_support",
        }:
            result["required_for_timing"] = [
                "parashari.wealth_foundation",
                "parashari.dasha_windows",
                "transit.trigger_windows",
            ]
        else:
            result["claim_operations"] = ["parashari.wealth_foundation"]
            result["required_for_timing"] = ["parashari.wealth_foundation"]
    if answer_mode == "comparison_choice" and key != "wealth":
        result.setdefault("operations", []).append("comparison.option_specific_evidence")
        result.setdefault("required_for_timing", []).append("comparison.option_specific_evidence")
    if key in {"health", "mental_wellbeing", "surgery", "accident", "recovery"}:
        result.setdefault("operations", []).append("parashari.health_body_area")
        result.setdefault("required_for_timing", []).append("parashari.health_body_area")
    return result
