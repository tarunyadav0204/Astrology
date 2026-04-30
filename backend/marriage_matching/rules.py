"""Rule profiles for deterministic kundli matching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet


@dataclass(frozen=True)
class RuleProfile:
    key: str
    label: str
    description: str
    manglik_houses: FrozenSet[int]
    nadi_same_nakshatra_diff_pada_exception: bool
    nadi_same_rashi_exception: bool
    bhakoot_same_ruler_exception: bool
    bhakoot_mutual_friend_ruler_exception: bool
    manglik_pair_cancellation: bool
    manglik_benefic_cancellation: bool
    manglik_jupiter_aspect_cancellation: bool
    manglik_own_exalted_cancellation: bool


RULE_PROFILES: Dict[str, RuleProfile] = {
    "classical_strict": RuleProfile(
        key="classical_strict",
        label="Classical Strict",
        description="Conservative rule handling with minimal exception relief.",
        manglik_houses=frozenset({1, 2, 4, 7, 8, 12}),
        nadi_same_nakshatra_diff_pada_exception=False,
        nadi_same_rashi_exception=False,
        bhakoot_same_ruler_exception=True,
        bhakoot_mutual_friend_ruler_exception=False,
        manglik_pair_cancellation=True,
        manglik_benefic_cancellation=True,
        manglik_jupiter_aspect_cancellation=True,
        manglik_own_exalted_cancellation=True,
    ),
    "balanced_modern": RuleProfile(
        key="balanced_modern",
        label="Balanced Modern",
        description="Classical raw scoring with practical exception handling for real-world matching.",
        manglik_houses=frozenset({1, 2, 4, 7, 8, 12}),
        nadi_same_nakshatra_diff_pada_exception=True,
        nadi_same_rashi_exception=True,
        bhakoot_same_ruler_exception=True,
        bhakoot_mutual_friend_ruler_exception=True,
        manglik_pair_cancellation=True,
        manglik_benefic_cancellation=True,
        manglik_jupiter_aspect_cancellation=True,
        manglik_own_exalted_cancellation=True,
    ),
    "southern_practical": RuleProfile(
        key="southern_practical",
        label="Southern Practical",
        description="Practical profile with broader Manglik house scope and generous cancellation handling.",
        manglik_houses=frozenset({1, 2, 4, 7, 8, 12}),
        nadi_same_nakshatra_diff_pada_exception=True,
        nadi_same_rashi_exception=True,
        bhakoot_same_ruler_exception=True,
        bhakoot_mutual_friend_ruler_exception=True,
        manglik_pair_cancellation=True,
        manglik_benefic_cancellation=True,
        manglik_jupiter_aspect_cancellation=True,
        manglik_own_exalted_cancellation=True,
    ),
}


def get_rule_profile(name: str = "balanced_modern") -> RuleProfile:
    return RULE_PROFILES.get(name, RULE_PROFILES["balanced_modern"])
