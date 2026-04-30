"""Deterministic exception handling for kundli matching doshas."""

from __future__ import annotations

from typing import Any, Dict, List

from .astro_utils import planet_sign
from .constants import PLANET_FRIENDSHIPS, SIGN_LORDS
from .rules import RuleProfile, get_rule_profile


class CompatibilityExceptions:
    """Evaluate classical exception rules without overwriting raw scores."""

    def __init__(self, rule_profile: RuleProfile | str = "balanced_modern") -> None:
        self.rule_profile = (
            rule_profile if isinstance(rule_profile, RuleProfile) else get_rule_profile(rule_profile)
        )

    def evaluate(
        self,
        boy_chart: Dict[str, Any],
        girl_chart: Dict[str, Any],
        boy_moon: Dict[str, Any],
        girl_moon: Dict[str, Any],
        koots: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        return {
            "nadi": self._nadi_exception(boy_moon, girl_moon, koots["nadi"]),
            "bhakoot": self._bhakoot_exception(boy_chart, girl_chart, boy_moon, girl_moon, koots["bhakoot"]),
        }

    def _nadi_exception(
        self,
        boy_moon: Dict[str, Any],
        girl_moon: Dict[str, Any],
        raw_nadi: Dict[str, Any],
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        applies = False

        same_nakshatra = boy_moon.get("nakshatra_number") == girl_moon.get("nakshatra_number")
        different_pada = boy_moon.get("pada") != girl_moon.get("pada")

        if (
            raw_nadi["score"] == 0
            and same_nakshatra
            and different_pada
            and self.rule_profile.nadi_same_nakshatra_diff_pada_exception
        ):
            applies = True
            reasons.append("Same nakshatra but different padas softens the Nadi Dosha in many traditions")
        elif (
            raw_nadi["score"] == 0
            and boy_moon.get("sign") == girl_moon.get("sign")
            and self.rule_profile.nadi_same_rashi_exception
        ):
            applies = True
            reasons.append("Same Moon sign reduces Nadi harshness in this rule profile")

        return {
            "applies": applies,
            "adjusted_score": raw_nadi["max_score"] if applies else raw_nadi["score"],
            "reasons": reasons,
            "rule_profile": self.rule_profile.key,
        }

    def _bhakoot_exception(
        self,
        boy_chart: Dict[str, Any],
        girl_chart: Dict[str, Any],
        boy_moon: Dict[str, Any],
        girl_moon: Dict[str, Any],
        raw_bhakoot: Dict[str, Any],
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        applies = False

        if raw_bhakoot["score"] != 0:
            return {
                "applies": False,
                "adjusted_score": raw_bhakoot["score"],
                "reasons": reasons,
            }

        boy_lord = SIGN_LORDS.get(boy_moon.get("sign"))
        girl_lord = SIGN_LORDS.get(girl_moon.get("sign"))
        if boy_lord and girl_lord:
            if boy_lord == girl_lord and self.rule_profile.bhakoot_same_ruler_exception:
                applies = True
                reasons.append(f"Moon signs share the same ruler ({boy_lord}), a common Bhakoot cancellation condition")
            elif (
                self._are_friendly_rulers(boy_lord, girl_lord)
                and self.rule_profile.bhakoot_mutual_friend_ruler_exception
            ):
                applies = True
                reasons.append(f"Moon sign rulers {boy_lord} and {girl_lord} are mutual friends, softening Bhakoot tension")

        # Fallback from actual Moon sign longitudes in case sign metadata is incomplete elsewhere.
        if not applies:
            boy_sign = planet_sign(boy_chart, "Moon")
            girl_sign = planet_sign(girl_chart, "Moon")
            if boy_sign and girl_sign and SIGN_LORDS.get(boy_sign) == SIGN_LORDS.get(girl_sign):
                applies = True
                reasons.append("Exact Moon-sign rulers match, so Bhakoot Dosha is softened")

        return {
            "applies": applies,
            "adjusted_score": raw_bhakoot["max_score"] if applies else raw_bhakoot["score"],
            "reasons": reasons,
            "rule_profile": self.rule_profile.key,
        }

    def _are_friendly_rulers(self, planet_a: str, planet_b: str) -> bool:
        rel_a = PLANET_FRIENDSHIPS.get(planet_a, {})
        rel_b = PLANET_FRIENDSHIPS.get(planet_b, {})
        return (
            planet_b in rel_a.get("friends", set())
            and planet_a in rel_b.get("friends", set())
        )
