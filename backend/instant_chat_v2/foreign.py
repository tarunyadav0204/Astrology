"""Typed routes for Travel, Relocation and Foreign Life."""
from __future__ import annotations
from typing import Any

FOREIGN_CATEGORIES = frozenset({"travel", "foreign", "visa", "immigration", "location", "relocation"})
TIMING_MODES = frozenset({"event_prediction", "event_timing", "lifetime_event_timing", "month_timing", "timing_window", "daily_forecast"})

FOREIGN_PROFILES: dict[str, dict[str, Any]] = {
    "foreign_overview": {"houses":[3,4,7,9,11,12], "charts":["D1","D3","D4","D9","D12"]},
    "travel_tendency": {"houses":[3,9,12], "charts":["D1","D3","D9"]},
    "short_travel": {"houses":[3,11], "charts":["D1","D3"]},
    "short_travel_timing": {"houses":[3,11], "charts":["D1","D3"]},
    "long_travel": {"houses":[3,9,11,12], "charts":["D1","D3","D9"]},
    "long_travel_timing": {"houses":[3,9,11,12], "charts":["D1","D3","D9"]},
    "travel_purpose": {"houses":[3,7,9,10,11,12], "charts":["D1","D3","D9"]},
    "travel_obstacles": {"houses":[3,6,8,9,12], "charts":["D1","D3","D9"]},
    "retrospective_travel": {"houses":[3,9,11,12], "charts":["D1","D3","D9"]},
    "domestic_relocation": {"houses":[3,4,11,12], "charts":["D1","D3","D4"]},
    "domestic_relocation_timing": {"houses":[3,4,11,12], "charts":["D1","D3","D4"]},
    "stay_vs_relocate": {"houses":[3,4,9,11,12], "charts":["D1","D4","D9"]},
    "temporary_vs_permanent": {"houses":[3,4,9,11,12], "charts":["D1","D4","D9","D12"]},
    "foreign_travel": {"houses":[3,9,11,12], "charts":["D1","D3","D9"]},
    "foreign_travel_timing": {"houses":[3,9,11,12], "charts":["D1","D3","D9"]},
    "foreign_residence": {"houses":[4,7,9,11,12], "charts":["D1","D4","D9","D12"]},
    "foreign_residence_timing": {"houses":[4,7,9,11,12], "charts":["D1","D4","D9","D12"]},
    "permanent_settlement": {"houses":[4,7,9,11,12], "charts":["D1","D4","D9","D12"]},
    "settlement_timing": {"houses":[4,7,9,11,12], "charts":["D1","D4","D9","D12"]},
    "visa_support": {"houses":[3,6,9,11,12], "charts":["D1","D3","D9","D12"]},
    "visa_timing": {"houses":[3,6,9,11,12], "charts":["D1","D3","D9","D12"]},
    "migration_pathway": {"houses":[3,4,7,9,10,11,12], "charts":["D1","D4","D9","D12"]},
    "return_home": {"houses":[3,4,9,11,12], "charts":["D1","D4","D9","D12"]},
    "return_home_timing": {"houses":[3,4,9,11,12], "charts":["D1","D4","D9","D12"]},
    "foreign_life_adjustment": {"houses":[4,7,11,12], "charts":["D1","D4","D9","D12"]},
    "foreign_obstacles": {"houses":[3,4,6,8,9,11,12], "charts":["D1","D4","D9","D12"]},
    "foreign_remedy": {"houses":[3,4,6,8,9,11,12], "charts":["D1","D4","D9","D12"]},
    "location_comparison": {"houses":[4,9,10,11,12], "charts":["D1","D4","D9","D10","D12"]},
    "location_recommendation_handoff": {"houses":[], "charts":[]},
    "legal_immigration_handoff": {"houses":[], "charts":[]},
    "muhurat_handoff": {"houses":[], "charts":[]},
    "travel_safety_handoff": {"houses":[], "charts":[]},
    "other_person_handoff": {"houses":[], "charts":[]},
}

ALIASES = {"overview":"foreign_overview", "travel":"travel_tendency", "relocation":"domestic_relocation", "visa":"visa_support", "settlement":"permanent_settlement", **{k:k for k in FOREIGN_PROFILES}}
TIMING_SUBTYPES = frozenset(k for k in FOREIGN_PROFILES if k.endswith("_timing") or k == "retrospective_travel")
BOUNDARY_SUBTYPES = frozenset(k for k in FOREIGN_PROFILES if k.endswith("_handoff"))

def normalize_foreign_subtype(value: Any) -> str:
    key = str(value or "foreign_overview").strip().lower().replace("-","_").replace(" ","_")
    return ALIASES.get(key, "foreign_overview")

def foreign_profile(category: Any, subtype: Any = None) -> dict[str, Any]:
    key = normalize_foreign_subtype(subtype or ("visa_support" if str(category).lower()=="visa" else "travel_tendency" if str(category).lower()=="travel" else "foreign_overview"))
    return {
        "subtype": key,
        "planets": ["Rahu", "Ketu", "Saturn", "Jupiter", "Moon"],
        **FOREIGN_PROFILES[key],
    }

def is_foreign_category(value: Any) -> bool:
    return str(value or "").strip().lower() in FOREIGN_CATEGORIES
