"""Semantic profiles for Children, Parenthood and Progeny graph routes.

The intent model chooses a subtype.  These helpers normalize structured output
only; they never infer a route from English question text.
"""

from __future__ import annotations

from typing import Any


CHILDREN_CATEGORIES = frozenset({
    "progeny", "children", "child", "pregnancy", "conception", "childbirth",
    "adoption", "son", "daughter",
})

CHILDREN_SUBTYPE_ALIASES = {
    "general": "children_overview", "overall": "children_overview",
    "children": "children_overview", "parenthood": "parenthood_capacity",
    "fertility": "conception_capacity", "conception": "conception_capacity",
    "pregnancy_timing": "conception_timing", "delivery_timing": "childbirth_timing",
    "first_child_timing": "first_child", "first_child_capacity": "first_child_capacity",
    "second_child": "subsequent_child_capacity", "second_child_timing": "subsequent_child",
    "more_children": "subsequent_child_capacity", "family_size": "family_size_tendency",
    "delay": "children_delay_diagnosis", "ivf": "assisted_conception",
    "ivf_timing": "assisted_conception_timing", "adoption": "adoption_pathway",
    "stepchildren": "step_parenthood", "decision": "parenthood_decision",
    "children_vs_career": "parenthood_vs_career", "children_vs_career_timing": "parenthood_vs_career_timing",
    "relationship": "parent_child_relationship",
    "reconciliation": "parent_child_reconciliation_timing", "past_timing": "retrospective_child_timing",
    "remedy": "children_remedy", "partner": "two_chart_children_handoff",
    "child_profile": "child_chart_required_handoff", "medical": "medical_safety_handoff",
    "muhurat": "muhurat_handoff", "custody": "legal_custody_handoff",
    "gender": "fetal_sex_refusal", "sex_prediction": "fetal_sex_refusal",
}

# Houses are ordered by decision importance.  A profile is a calculation
# contract, not a claim that every listed house is supportive.
CHILDREN_PROFILES: dict[str, dict[str, Any]] = {
    "children_overview": {"houses": [5, 2, 11, 9], "planets": ["Jupiter", "Moon", "Venus", "Saturn"]},
    "parenthood_capacity": {"houses": [5, 2, 11, 1, 4], "planets": ["Jupiter", "Moon", "Saturn"]},
    "conception_capacity": {"houses": [5, 2, 11, 8], "planets": ["Jupiter", "Moon", "Venus", "Mars", "Saturn", "Rahu", "Ketu"]},
    "conception_timing": {"houses": [2, 5, 11], "planets": ["Jupiter", "Moon", "Venus", "Saturn"]},
    "childbirth_timing": {"houses": [2, 5, 11, 9], "planets": ["Jupiter", "Moon", "Saturn"]},
    "first_child_capacity": {"houses": [5, 2, 11], "planets": ["Jupiter", "Moon"]},
    "first_child": {"houses": [5, 2, 11], "planets": ["Jupiter", "Moon"]},
    "subsequent_child_capacity": {"houses": [7, 9, 11, 2, 5], "planets": ["Jupiter", "Moon", "Saturn"]},
    "subsequent_child": {"houses": [7, 9, 11, 2, 5], "planets": ["Jupiter", "Moon", "Saturn"]},
    "family_size_tendency": {"houses": [5, 7, 9, 11, 2], "planets": ["Jupiter", "Moon", "Saturn"]},
    "children_delay_diagnosis": {"houses": [5, 2, 11, 1, 4, 8, 10, 12], "planets": ["Jupiter", "Moon", "Saturn", "Rahu", "Ketu", "Mars"]},
    "assisted_conception": {"houses": [5, 8, 11, 6, 12, 2], "planets": ["Jupiter", "Moon", "Venus", "Mars", "Rahu", "Ketu"]},
    "assisted_conception_timing": {"houses": [5, 8, 11, 6, 12, 2], "planets": ["Jupiter", "Moon", "Venus", "Mars", "Rahu", "Ketu"]},
    "adoption_pathway": {"houses": [5, 9, 11, 4, 8], "planets": ["Jupiter", "Moon", "Saturn", "Rahu"]},
    "adoption_timing": {"houses": [5, 9, 11, 4], "planets": ["Jupiter", "Moon", "Saturn"]},
    "step_parenthood": {"houses": [5, 7, 9, 11], "planets": ["Jupiter", "Moon", "Saturn"]},
    "parenthood_decision": {"houses": [1, 4, 5, 2, 11], "planets": ["Jupiter", "Moon", "Saturn"]},
    "parenthood_vs_career": {"houses": [5, 2, 11, 6, 10], "planets": ["Jupiter", "Moon", "Saturn", "Sun"]},
    "parenthood_vs_career_timing": {"houses": [5, 2, 11, 6, 10], "planets": ["Jupiter", "Moon", "Saturn", "Sun"]},
    "parent_child_relationship": {"houses": [1, 4, 5, 2], "planets": ["Moon", "Jupiter", "Mercury", "Saturn", "Mars"]},
    "parent_child_reconciliation_timing": {"houses": [2, 5, 11, 4], "planets": ["Moon", "Jupiter", "Mercury", "Saturn"]},
    "retrospective_child_timing": {"houses": [2, 5, 11], "planets": ["Jupiter", "Moon", "Saturn"]},
    "children_remedy": {"houses": [2, 5, 11, 8], "planets": ["Jupiter", "Moon", "Saturn", "Rahu", "Ketu"]},
    "two_chart_children_handoff": {"houses": [], "planets": []},
    "child_chart_required_handoff": {"houses": [], "planets": []},
    "medical_safety_handoff": {"houses": [], "planets": []},
    "muhurat_handoff": {"houses": [], "planets": []},
    "legal_custody_handoff": {"houses": [], "planets": []},
    "fetal_sex_refusal": {"houses": [], "planets": []},
}

TIMING_CHILDREN_SUBTYPES = frozenset({
    "conception_timing", "childbirth_timing", "first_child", "subsequent_child",
    "assisted_conception_timing", "adoption_timing",
    "parenthood_vs_career_timing", "parent_child_reconciliation_timing", "retrospective_child_timing",
})

BOUNDARY_CHILDREN_SUBTYPES = frozenset({
    "two_chart_children_handoff", "child_chart_required_handoff", "medical_safety_handoff",
    "muhurat_handoff", "legal_custody_handoff", "fetal_sex_refusal",
})


def normalize_children_subtype(value: Any) -> str:
    raw = str(value or "children_overview").strip().lower().replace("-", "_").replace(" ", "_")
    resolved = CHILDREN_SUBTYPE_ALIASES.get(raw, raw)
    return resolved if resolved in CHILDREN_PROFILES else "children_overview"


def children_profile(category: Any, subtype: Any = None) -> dict[str, Any]:
    category_key = str(category or "").strip().lower()
    inferred = subtype
    if not inferred and category_key == "adoption":
        inferred = "adoption_pathway"
    resolved = normalize_children_subtype(inferred)
    return {"subtype": resolved, **CHILDREN_PROFILES[resolved]}


def is_children_category(value: Any) -> bool:
    return str(value or "").strip().lower() in CHILDREN_CATEGORIES


def is_children_timing(subtype: Any, answer_mode: Any = None) -> bool:
    return (
        normalize_children_subtype(subtype) in TIMING_CHILDREN_SUBTYPES
        or str(answer_mode or "").strip().lower() in {
            "event_prediction", "event_timing", "lifetime_event_timing",
            "month_timing", "timing_window", "daily_forecast",
        }
    )
