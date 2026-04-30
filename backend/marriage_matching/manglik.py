"""Deterministic Manglik analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .astro_utils import (
    aspects_house,
    get_house_from_chart,
    planet_dignity,
    planet_sign,
    planets_in_house,
    reference_house_from_planet,
)
from .rules import RuleProfile, get_rule_profile


class ManglikAnalyzer:
    def __init__(self, rule_profile: RuleProfile | str = "balanced_modern") -> None:
        self.rule_profile = rule_profile if isinstance(rule_profile, RuleProfile) else get_rule_profile(rule_profile)

    def analyze(self, chart: Dict[str, Any], d9_chart: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        mars_house_lagna = get_house_from_chart(chart, "Mars")
        mars_house_moon = reference_house_from_planet(chart, "Moon", "Mars")
        mars_house_venus = reference_house_from_planet(chart, "Venus", "Mars")
        mars_house_d9 = get_house_from_chart(d9_chart or {}, "Mars") if d9_chart else None

        references = {
            "lagna": self._reference_result(mars_house_lagna),
            "moon": self._reference_result(mars_house_moon),
            "venus": self._reference_result(mars_house_venus),
            "navamsa_d9": self._reference_result(mars_house_d9) if d9_chart else None,
        }

        active_refs = [key for key, value in references.items() if value and value["is_manglik"]]
        base_severity = self._severity_from_count(len(active_refs))
        cancellation = self._cancellation(chart, mars_house_lagna)

        return {
            "is_manglik": bool(active_refs),
            "severity": "Low" if cancellation["has_cancellation"] and base_severity != "None" else base_severity,
            "active_references": active_refs,
            "mars_house": mars_house_lagna,
            "mars_sign": planet_sign(chart, "Mars"),
            "references": references,
            "cancellation": cancellation,
            "evidence": self._evidence(active_refs, cancellation, references),
        }

    def compatibility(self, person1: Dict[str, Any], person2: Dict[str, Any]) -> Dict[str, Any]:
        both = person1["is_manglik"] and person2["is_manglik"]
        one = person1["is_manglik"] ^ person2["is_manglik"]
        cancelled_pair = both or (
            one
            and (
                person1["cancellation"]["has_cancellation"]
                or person2["cancellation"]["has_cancellation"]
            )
        )
        if cancelled_pair:
            if both:
                score = 9
                status = "Compatible"
                description = "Both partners carry Manglik influence, so the dosha is balanced in pair matching."
            else:
                score = 7
                status = "Manageable"
                description = "One-sided Manglik is present, but strong cancellation factors soften the dosha."
        elif one:
            unmatched = person1 if person1["is_manglik"] else person2
            if unmatched["cancellation"]["has_cancellation"]:
                score = 7
                status = "Manageable"
                description = "One-sided Manglik is present, but cancellation factors soften the dosha."
            else:
                score = 4
                status = "Sensitive"
                description = "One-sided Manglik remains active and needs deeper review before a final verdict."
        else:
            score = 10
            status = "Compatible"
            description = "Neither partner shows active Manglik dosha."
        return {
            "status": status,
            "score": score,
            "description": description,
            "pair_cancellation": cancelled_pair,
            "exception_reasons": self._pair_exception_reasons(person1, person2, both, one),
        }

    def _reference_result(self, house_num: Optional[int]) -> Dict[str, Any]:
        is_manglik = house_num in self.rule_profile.manglik_houses if house_num is not None else False
        return {"house": house_num, "is_manglik": is_manglik}

    def _severity_from_count(self, count: int) -> str:
        if count >= 3:
            return "High"
        if count == 2:
            return "Medium"
        if count == 1:
            return "Low"
        return "None"

    def _cancellation(self, chart: Dict[str, Any], mars_house_lagna: Optional[int]) -> Dict[str, Any]:
        sign_num = planet_sign(chart, "Mars")
        dignity = planet_dignity("Mars", sign_num)
        factors: List[str] = []
        if dignity in {"Own", "Exalted"} and self.rule_profile.manglik_own_exalted_cancellation:
            factors.append(f"Mars is {dignity.lower()} in sign strength")
        if mars_house_lagna in {1, 4, 7, 10} and self.rule_profile.manglik_benefic_cancellation:
            benefics = [p for p in planets_in_house(chart, mars_house_lagna, ["Jupiter", "Venus", "Moon"]) if p != "Mars"]
            if benefics:
                factors.append(f"Benefic company in Mars house: {', '.join(benefics)}")
        if mars_house_lagna is not None and self.rule_profile.manglik_jupiter_aspect_cancellation:
            jupiter_aspects = "Jupiter" in aspects_house(chart, mars_house_lagna, ["Jupiter"])
            if jupiter_aspects:
                factors.append("Jupiter aspects Mars house")
        return {
            "has_cancellation": bool(factors),
            "factors": factors,
        }

    def _evidence(self, active_refs: List[str], cancellation: Dict[str, Any], references: Dict[str, Any]) -> List[str]:
        evidence: List[str] = []
        for ref in active_refs:
            house = references[ref]["house"]
            evidence.append(f"Mars triggers Manglik from {ref} reference at house {house}")
        evidence.extend(cancellation.get("factors", []))
        return evidence

    def _pair_exception_reasons(
        self,
        person1: Dict[str, Any],
        person2: Dict[str, Any],
        both: bool,
        one: bool,
    ) -> List[str]:
        if both:
            return ["Both charts show Manglik influence, which balances the dosha at pair level"]
        if one and (person1["cancellation"]["has_cancellation"] or person2["cancellation"]["has_cancellation"]):
            softened = person1 if person1["cancellation"]["has_cancellation"] else person2
            return softened["cancellation"].get("factors", [])
        return []
