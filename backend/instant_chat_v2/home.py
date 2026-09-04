"""Semantic profiles for the Home, Property and Vehicles graph.

The multilingual intent router selects a subtype.  This module only normalizes
that structured decision; it deliberately does not parse user wording.
"""

from __future__ import annotations

from typing import Any


HOME_CATEGORIES = frozenset({"property", "vehicle", "vehicles", "home"})

HOME_SUBTYPE_ALIASES = {
    "general": "home_overview", "home": "home_overview", "overview": "home_overview",
    "property": "property_potential", "ownership": "property_potential", "property_potential": "property_potential",
    "living_arrangement": "living_arrangement", "independent_vs_family": "living_arrangement", "independent_living": "living_arrangement", "family_living": "living_arrangement",
    "purchase": "property_purchase", "buy": "property_purchase", "property_buy": "property_purchase",
    "purchase_timing": "property_purchase_timing", "buy_timing": "property_purchase_timing",
    "sale": "property_sale_timing", "sell": "property_sale_timing", "sale_timing": "property_sale_timing",
    "sale_decision": "property_sale_decision", "sell_vs_hold": "property_sale_decision", "hold_vs_sell": "property_sale_decision",
    "property_finance": "property_finance", "home_loan": "property_finance", "property_loan": "property_finance",
    "property_comparison": "property_comparison", "rent_vs_buy": "property_comparison",
    "property_type": "property_type_fit", "land_vs_flat": "property_type_fit", "commercial_property": "property_type_fit",
    "joint_property": "joint_property", "co_ownership": "joint_property", "spouse_property": "joint_property",
    "rental": "rental_income", "rental_income": "rental_income", "landlord": "rental_income",
    "possession": "possession_documentation_timing", "registration": "possession_documentation_timing", "builder_delay": "possession_documentation_timing", "documentation": "possession_documentation_timing",
    "retrospective_property": "retrospective_property_timing", "first_house_when": "retrospective_property_timing",
    "portfolio": "property_portfolio_comparison", "sell_and_buy": "property_portfolio_comparison",
    "vastu": "vastu_handoff", "property_business": "property_business_handoff", "real_estate_business": "property_business_handoff",
    "construction": "construction_renovation", "renovation": "construction_renovation", "land": "construction_renovation",
    "construction_timing": "construction_timing", "renovation_timing": "construction_timing",
    "relocation": "relocation_home", "moving": "relocation_home", "move": "relocation_home",
    "relocation_timing": "relocation_timing", "move_timing": "relocation_timing",
    "property_obstacles": "property_obstacles", "property_delays": "property_obstacles", "deal_failures": "property_obstacles",
    "vehicle": "vehicle_potential", "vehicles": "vehicle_potential", "vehicle_purchase": "vehicle_potential",
    "vehicle_selection": "vehicle_selection", "vehicle_color": "vehicle_selection", "vehicle_colour": "vehicle_selection", "car_selection": "vehicle_selection",
    "vehicle_timing": "vehicle_timing",
    "remedy": "property_remedy", "property_remedy": "property_remedy",
    "property_dispute": "property_dispute_handoff", "legal_property": "property_dispute_handoff",
    "muhurat": "muhurat_handoff", "foreign": "foreign_handoff", "inheritance": "inheritance_handoff",
}

HOME_PROFILES: dict[str, dict[str, Any]] = {
    "home_overview": {"houses": [4, 2, 11, 12], "planets": ["Moon", "Venus", "Mars", "Saturn"]},
    "property_potential": {"houses": [4, 2, 11, 9], "planets": ["Mars", "Venus", "Moon", "Jupiter"]},
    "living_arrangement": {"houses": [2, 3, 4, 11, 12], "planets": ["Moon", "Venus", "Saturn", "Rahu"]},
    "property_purchase": {"houses": [2, 4, 11, 9], "planets": ["Mars", "Venus", "Moon", "Jupiter", "Saturn"]},
    "property_purchase_timing": {"houses": [2, 4, 11, 9], "planets": ["Mars", "Venus", "Moon", "Jupiter", "Saturn"]},
    "property_sale_timing": {"houses": [3, 4, 8, 11], "planets": ["Mars", "Mercury", "Venus", "Saturn"]},
    "property_sale_decision": {"houses": [2, 3, 4, 8, 11], "planets": ["Mars", "Mercury", "Venus", "Saturn"]},
    "property_finance": {"houses": [2, 4, 6, 8, 11, 12], "planets": ["Mars", "Venus", "Jupiter", "Saturn"]},
    "property_comparison": {"houses": [2, 3, 4, 6, 9, 11, 12], "planets": ["Moon", "Mars", "Venus", "Jupiter", "Saturn"]},
    "property_type_fit": {"houses": [2, 4, 8, 9, 11, 12], "planets": ["Mars", "Venus", "Moon", "Saturn"]},
    "joint_property": {"houses": [2, 4, 7, 8, 11], "planets": ["Venus", "Mars", "Moon", "Saturn"]},
    "rental_income": {"houses": [2, 4, 6, 8, 11, 12], "planets": ["Mercury", "Venus", "Saturn", "Jupiter"]},
    "possession_documentation_timing": {"houses": [3, 4, 6, 8, 11], "planets": ["Mercury", "Mars", "Saturn", "Jupiter"]},
    "retrospective_property_timing": {"houses": [2, 4, 9, 11], "planets": ["Mars", "Venus", "Moon", "Jupiter"]},
    "property_portfolio_comparison": {"houses": [2, 3, 4, 8, 9, 11, 12], "planets": ["Mars", "Venus", "Mercury", "Jupiter", "Saturn"]},
    "construction_renovation": {"houses": [2, 3, 4, 8, 11, 12], "planets": ["Mars", "Venus", "Saturn", "Mercury"]},
    "construction_timing": {"houses": [2, 3, 4, 8, 11, 12], "planets": ["Mars", "Venus", "Saturn", "Mercury"]},
    "relocation_home": {"houses": [3, 4, 9, 11, 12], "planets": ["Moon", "Saturn", "Jupiter", "Rahu"]},
    "relocation_timing": {"houses": [3, 4, 9, 11, 12], "planets": ["Moon", "Saturn", "Jupiter", "Rahu"]},
    "property_obstacles": {"houses": [3, 4, 6, 8, 11, 12], "planets": ["Mars", "Mercury", "Saturn", "Rahu", "Ketu"]},
    "vehicle_potential": {"houses": [2, 4, 11, 12], "planets": ["Venus", "Mars", "Moon", "Saturn"]},
    "vehicle_selection": {"houses": [2, 4, 11, 12], "planets": ["Venus", "Moon", "Mercury", "Mars", "Saturn"]},
    "vehicle_timing": {"houses": [2, 4, 11, 12], "planets": ["Venus", "Mars", "Moon", "Saturn"]},
    "property_remedy": {"houses": [2, 3, 4, 6, 8, 11, 12], "planets": ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]},
    "property_dispute_handoff": {"houses": [], "planets": []},
    "muhurat_handoff": {"houses": [], "planets": []},
    "foreign_handoff": {"houses": [], "planets": []},
    "inheritance_handoff": {"houses": [], "planets": []},
    "vastu_handoff": {"houses": [], "planets": []},
    "property_business_handoff": {"houses": [], "planets": []},
}

TIMING_HOME_SUBTYPES = frozenset({"property_purchase_timing", "property_sale_timing", "construction_timing", "relocation_timing", "vehicle_timing", "possession_documentation_timing", "retrospective_property_timing"})
BOUNDARY_HOME_SUBTYPES = frozenset({"property_dispute_handoff", "muhurat_handoff", "foreign_handoff", "inheritance_handoff", "vastu_handoff", "property_business_handoff"})


def normalize_home_subtype(value: Any) -> str:
    raw = str(value or "home_overview").strip().lower().replace("-", "_").replace(" ", "_")
    resolved = HOME_SUBTYPE_ALIASES.get(raw, raw)
    return resolved if resolved in HOME_PROFILES else "home_overview"


def home_profile(category: Any, subtype: Any = None) -> dict[str, Any]:
    inferred = subtype
    category_key = str(category or "").strip().lower()
    if not inferred and category_key == "vehicles":
        inferred = "vehicle_potential"
    return {"subtype": normalize_home_subtype(inferred), **HOME_PROFILES[normalize_home_subtype(inferred)]}


def is_home_category(value: Any) -> bool:
    return str(value or "").strip().lower() in HOME_CATEGORIES


def is_home_timing(subtype: Any, answer_mode: Any = None) -> bool:
    return normalize_home_subtype(subtype) in TIMING_HOME_SUBTYPES or str(answer_mode or "").strip().lower() in {
        "event_prediction", "event_timing", "lifetime_event_timing", "month_timing", "timing_window", "daily_forecast",
    }
