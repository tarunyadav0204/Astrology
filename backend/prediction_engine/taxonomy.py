from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence


TAXONOMY_VERSION = "1.3.0"


@dataclass(frozen=True)
class EventFamily:
    key: str
    domain: str
    primary_relative_houses: Sequence[int]
    supporting_relative_houses: Sequence[int]
    conflicting_relative_houses: Sequence[int]
    karakas: Sequence[str]
    minimum_direct_dasha_levels: int = 2
    minimum_primary_houses_covered: int = 1
    require_karaka_for_moderate: bool = True
    safety_allowed: bool = True


EVENT_FAMILIES: Dict[str, EventFamily] = {
    "career_authority": EventFamily(
        "career_authority", "career", (10,), (2, 6, 7, 11), (8, 12), ("Sun", "Saturn", "Mercury")
    ),
    "money_gains": EventFamily(
        "money_gains", "wealth", (2, 11), (5, 9), (6, 8, 12), ("Jupiter", "Venus", "Mercury"),
        minimum_primary_houses_covered=2,
    ),
    "financial_pressure": EventFamily(
        "financial_pressure", "wealth", (2,), (6, 8, 12), (11,),
        ("Saturn", "Mars", "Rahu", "Jupiter"),
    ),
    "partnership_commitment": EventFamily(
        "partnership_commitment", "relationship", (7,), (2, 5, 11), (6, 8, 12), ("Venus", "Jupiter")
    ),
    "home_property": EventFamily(
        "home_property", "home", (4,), (2, 11), (6, 8, 12), ("Moon", "Mars", "Venus")
    ),
    "children_education": EventFamily(
        "children_education", "children_education", (5,), (2, 4, 9, 11), (6, 8, 12), ("Jupiter", "Mercury")
    ),
    "travel_change": EventFamily(
        "travel_change", "travel", (9, 12), (3,), (6, 8), ("Jupiter", "Rahu", "Moon")
    ),
    "workload_health": EventFamily(
        "workload_health", "workload", (6,), (1, 10), (8, 12), ("Mars", "Saturn", "Sun")
    ),
    "shared_resources_change": EventFamily(
        "shared_resources_change", "shared_resources", (8,), (2, 7, 11), (6, 12),
        ("Saturn", "Mars", "Rahu", "Jupiter"),
    ),
    "family_responsibility": EventFamily(
        "family_responsibility", "family", (2, 4), (9,), (6, 8, 12), ("Moon", "Jupiter", "Saturn"),
        minimum_primary_houses_covered=2,
    ),
    "decision_communication": EventFamily(
        "decision_communication", "decisions", (3, 5), (9, 10), (6, 8, 12), ("Mercury", "Jupiter")
    ),
}
