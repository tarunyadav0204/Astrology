"""World-class foundation for deterministic kundli matching."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from .ashtakoota import AshtakootaCalculator
from .indicators import cross_chart_indicators, profile_snapshot
from .manglik import ManglikAnalyzer
from .evidence import bundle_evidence, evidence_item
from .rules import get_rule_profile
from .timing import TimingOverlayAnalyzer


class KundliMatchingEngine:
    """Deterministic matching engine with structured evidence payloads."""

    def __init__(
        self,
        rule_profile: str = "balanced_modern",
        current_date: Optional[date] = None,
        dasha_provider: Any = None,
    ) -> None:
        self.rule_profile = get_rule_profile(rule_profile)
        self.ashtakoota = AshtakootaCalculator(self.rule_profile)
        self.manglik = ManglikAnalyzer(self.rule_profile)
        self.timing = TimingOverlayAnalyzer(current_date=current_date, dasha_provider=dasha_provider)

    def analyze(
        self,
        boy_chart: Dict[str, Any],
        girl_chart: Dict[str, Any],
        boy_birth: Dict[str, Any],
        girl_birth: Dict[str, Any],
    ) -> Dict[str, Any]:
        boy_d9 = self._d9_chart(boy_chart)
        girl_d9 = self._d9_chart(girl_chart)

        kuta = self.ashtakoota.calculate(boy_chart, girl_chart)
        boy_manglik = self.manglik.analyze(boy_chart, boy_d9)
        girl_manglik = self.manglik.analyze(girl_chart, girl_d9)
        manglik_pair = self.manglik.compatibility(boy_manglik, girl_manglik)

        boy_profile = profile_snapshot(boy_chart, boy_d9)
        girl_profile = profile_snapshot(girl_chart, girl_d9)
        cross = cross_chart_indicators(boy_profile, girl_profile)
        timing = self.timing.analyze(boy_chart, girl_chart, boy_birth, girl_birth, boy_profile, girl_profile)

        overall = self._overall_score(kuta, boy_manglik, girl_manglik, boy_profile, girl_profile, cross)
        evidence = self._evidence_summary(kuta, boy_manglik, girl_manglik, boy_profile, girl_profile, cross, timing)
        recommendation = self._recommendation(overall, kuta, manglik_pair, evidence, timing)

        result = {
            "engine_version": "kundli_matching_v2",
            "rule_profile": {
                "key": self.rule_profile.key,
                "label": self.rule_profile.label,
                "description": self.rule_profile.description,
            },
            "inputs": {
                "boy": boy_birth,
                "girl": girl_birth,
            },
            "profiles": {
                "boy": boy_profile,
                "girl": girl_profile,
            },
            "ashtakoota": kuta,
            "manglik": {
                "boy": boy_manglik,
                "girl": girl_manglik,
                "compatibility": manglik_pair,
            },
            "relationship_indicators": {
                "cross_chart": cross,
                "boy_d1_d9": {
                    "d1_seventh": boy_profile["seventh_house"]["d1_strength"],
                    "d9_seventh": boy_profile["seventh_house"]["d9_strength"],
                },
                "girl_d1_d9": {
                    "d1_seventh": girl_profile["seventh_house"]["d1_strength"],
                    "d9_seventh": girl_profile["seventh_house"]["d9_strength"],
                },
            },
            "timing_overlay": timing,
            "overall_score": overall,
            "evidence_summary": evidence,
            "evidence_objects": self._evidence_objects(kuta, boy_manglik, girl_manglik, boy_profile, girl_profile, cross, timing),
            "recommendation": recommendation,
        }
        result["legacy"] = self._legacy_payload(result)
        return result

    def _d9_chart(self, d1_chart: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from calculators.divisional_chart_calculator import DivisionalChartCalculator
            d9 = DivisionalChartCalculator(d1_chart).calculate_divisional_chart(9)
            return d9.get("divisional_chart", {})
        except Exception:
            # D9 support is valuable, but the engine should still return a usable
            # deterministic matching result even when the divisional dependency is unavailable.
            return {}

    def _overall_score(
        self,
        kuta: Dict[str, Any],
        boy_manglik: Dict[str, Any],
        girl_manglik: Dict[str, Any],
        boy_profile: Dict[str, Any],
        girl_profile: Dict[str, Any],
        cross: Dict[str, Any],
    ) -> Dict[str, Any]:
        pair_manglik = self.manglik.compatibility(boy_manglik, girl_manglik)
        kuta_pct = float(kuta["effective_percentage"])
        manglik_pct = float(pair_manglik["score"]) * 10.0
        d1_d9_avg = (
            boy_profile["seventh_house"]["d1_strength"]["score"] * 0.25
            + boy_profile["seventh_house"]["d9_strength"]["score"] * 0.15
            + girl_profile["seventh_house"]["d1_strength"]["score"] * 0.25
            + girl_profile["seventh_house"]["d9_strength"]["score"] * 0.15
        )
        overall = round(
            (kuta_pct * 0.45)
            + (manglik_pct * 0.2)
            + (d1_d9_avg * 0.2)
            + (cross["score"] * 0.15),
            1,
        )
        if kuta["effective_critical_issues"] and not pair_manglik["pair_cancellation"]:
            overall = round(max(0.0, overall - 5.0), 1)
        grade = (
            "Excellent" if overall >= 85 else
            "Good" if overall >= 70 else
            "Average" if overall >= 55 else
            "Delicate" if overall >= 40 else
            "Challenging"
        )
        return {
            "percentage": overall,
            "grade": grade,
            "components": {
                "ashtakoota": round(kuta_pct * 0.45, 1),
                "manglik": round(manglik_pct * 0.2, 1),
                "marriage_support_d1_d9": round(d1_d9_avg * 0.2, 1),
                "cross_chart_chemistry": round(cross["score"] * 0.15, 1),
            },
        }

    def _evidence_summary(
        self,
        kuta: Dict[str, Any],
        boy_manglik: Dict[str, Any],
        girl_manglik: Dict[str, Any],
        boy_profile: Dict[str, Any],
        girl_profile: Dict[str, Any],
        cross: Dict[str, Any],
        timing: Dict[str, Any],
    ) -> Dict[str, Any]:
        positives = []
        cautions = []
        contradictions = []

        if kuta["effective_percentage"] >= 70:
            positives.append(f"Strong effective Ashtakoota support at {kuta['effective_total_score']}/36")
        else:
            cautions.append(f"Ashtakoota is only {kuta['total_score']}/36 before exception handling")

        for key in ("nadi", "bhakoot"):
            if kuta.get("exceptions", {}).get(key, {}).get("applies"):
                positives.extend(kuta["exceptions"][key]["reasons"])

        positives.extend(cross["positive_factors"])
        cautions.extend(cross["caution_factors"])

        if boy_profile["seventh_house"]["d9_strength"]["score"] >= 60 and kuta["effective_percentage"] < 55:
            contradictions.append("Traditional koota score is low, but boy's Navamsa marriage support is better than the raw score suggests")
        if girl_profile["seventh_house"]["d9_strength"]["score"] >= 60 and kuta["effective_percentage"] < 55:
            contradictions.append("Traditional koota score is low, but girl's Navamsa marriage support is better than the raw score suggests")
        if boy_manglik["is_manglik"] != girl_manglik["is_manglik"]:
            cautions.append("Manglik is one-sided, so pair handling needs care")
        elif boy_manglik["is_manglik"] and girl_manglik["is_manglik"]:
            positives.append("Both charts carry Manglik influence, so the dosha is balanced at pair level")
        positives.extend(self.manglik.compatibility(boy_manglik, girl_manglik).get("exception_reasons", []))
        shared_now = ((timing.get("shared") or {}).get("current_window") or {})
        if shared_now.get("climate") in {"highly_favorable", "favorable"}:
            positives.append("Current joint timing climate supports formal relationship progress")
        elif shared_now.get("climate") == "challenging":
            cautions.append("Current joint timing climate is not ideal for formalizing marriage immediately")

        return {
            "positive_factors": positives,
            "caution_factors": cautions + kuta["effective_critical_issues"],
            "contradictions": contradictions,
        }

    def _recommendation(
        self,
        overall: Dict[str, Any],
        kuta: Dict[str, Any],
        manglik_pair: Dict[str, Any],
        evidence: Dict[str, Any],
        timing: Dict[str, Any],
    ) -> Dict[str, Any]:
        pct = overall["percentage"]
        if pct >= 85:
            verdict = "Highly supportive match"
            proceed = True
        elif pct >= 70:
            verdict = "Good match with manageable differences"
            proceed = True
        elif pct >= 55:
            verdict = "Workable match, but not automatic"
            proceed = True
        elif pct >= 40:
            verdict = "Sensitive match that needs conscious effort"
            proceed = False
        else:
            verdict = "Classically difficult match"
            proceed = False

        remedies = []
        if manglik_pair["status"] in {"Sensitive", "Manageable"}:
            remedies.append("Review Manglik handling before finalizing the match")
        if any("Nadi Dosha" in item for item in kuta["effective_critical_issues"]):
            remedies.append("Review Nadi Dosha with family tradition and exception rules")
        if any("Bhakoot" in item for item in kuta["effective_critical_issues"]):
            remedies.append("Check Bhakoot exception handling and practical life compatibility")
        if not remedies and pct < 70:
            remedies.append("Use the structured result as a base for deeper chart synthesis before a final decision")
        shared_now = ((timing.get("shared") or {}).get("current_window") or {})
        if shared_now.get("climate") == "challenging":
            remedies.append("Prefer a better joint marriage window before locking in a formal decision")

        return {
            "verdict": verdict,
            "proceed": proceed,
            "remedies": remedies,
            "notes": evidence["contradictions"],
            "timing_note": self._timing_note(timing),
        }

    def _legacy_payload(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "guna_milan": result["ashtakoota"],
            "manglik_analysis": {
                "boy_manglik": result["manglik"]["boy"],
                "girl_manglik": result["manglik"]["girl"],
                "compatibility": result["manglik"]["compatibility"],
            },
            "overall_score": result["overall_score"],
            "recommendation": {
                "recommendation": result["recommendation"]["verdict"],
                "proceed": result["recommendation"]["proceed"],
                "remedies": result["recommendation"]["remedies"],
                "critical_issues": result["ashtakoota"]["effective_critical_issues"],
            },
        }

    def _evidence_objects(
        self,
        kuta: Dict[str, Any],
        boy_manglik: Dict[str, Any],
        girl_manglik: Dict[str, Any],
        boy_profile: Dict[str, Any],
        girl_profile: Dict[str, Any],
        cross: Dict[str, Any],
        timing: Dict[str, Any],
    ) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = []

        items.append(
            evidence_item(
                code="ASHTAKOOTA_EFFECTIVE_SCORE",
                category="ashtakoota",
                polarity="supportive" if kuta["effective_percentage"] >= 70 else "challenging",
                weight=kuta["effective_percentage"] / 100.0,
                summary=f"Effective Ashtakoota is {kuta['effective_total_score']}/36 under the active rule profile",
                facts={
                    "raw_total_score": kuta["total_score"],
                    "effective_total_score": kuta["effective_total_score"],
                    "effective_critical_issues": kuta["effective_critical_issues"],
                },
                rule_profile=self.rule_profile.key,
            )
        )

        for key in ("nadi", "bhakoot"):
            exception = kuta.get("exceptions", {}).get(key, {})
            if exception.get("applies"):
                items.append(
                    evidence_item(
                        code=f"{key.upper()}_EXCEPTION",
                        category="exceptions",
                        polarity="supportive",
                        weight=0.55,
                        summary="; ".join(exception.get("reasons", [])),
                        facts=exception,
                        rule_profile=self.rule_profile.key,
                    )
                )

        pair_manglik = self.manglik.compatibility(boy_manglik, girl_manglik)
        items.append(
            evidence_item(
                code="MANGLIK_PAIR_STATUS",
                category="manglik",
                polarity="supportive" if pair_manglik["status"] == "Compatible" else "neutral" if pair_manglik["status"] == "Manageable" else "challenging",
                weight=pair_manglik["score"] / 10.0,
                summary=pair_manglik["description"],
                facts=pair_manglik,
                rule_profile=self.rule_profile.key,
            )
        )

        for label, profile in (("boy", boy_profile), ("girl", girl_profile)):
            navamsa = profile.get("navamsa_synthesis", {})
            items.append(
                evidence_item(
                    code=f"{label.upper()}_NAVAMSA_MARRIAGE_SUPPORT",
                    category="navamsa",
                    polarity="supportive" if navamsa.get("score", 50) >= 60 else "challenging" if navamsa.get("score", 50) < 45 else "neutral",
                    weight=navamsa.get("score", 50) / 100.0,
                    summary=f"{label.title()} Navamsa marriage layer is {navamsa.get('band', 'Unknown').lower()} and {navamsa.get('root_vs_fruit', 'consistent')}",
                    facts=navamsa,
                    rule_profile=self.rule_profile.key,
                )
            )

        items.append(
            evidence_item(
                code="CROSS_CHART_CHEMISTRY",
                category="cross_chart",
                polarity="supportive" if cross["score"] >= 60 else "challenging",
                weight=cross["score"] / 100.0,
                summary=f"Cross-chart chemistry band is {cross['band'].lower()}",
                facts=cross,
                rule_profile=self.rule_profile.key,
            )
        )
        shared = (timing.get("shared") or {})
        current_timing = shared.get("current_window") or {}
        items.append(
            evidence_item(
                code="TIMING_OVERLAY_CURRENT_WINDOW",
                category="timing",
                polarity="supportive" if current_timing.get("climate") in {"highly_favorable", "favorable"} else "challenging" if current_timing.get("climate") == "challenging" else "neutral",
                weight=(shared.get("joint_readiness_score") or 50) / 100.0,
                summary=f"Current joint timing climate is {current_timing.get('climate', 'unknown')}",
                facts=shared,
                rule_profile=self.rule_profile.key,
            )
        )

        return bundle_evidence(items)

    def _timing_note(self, timing: Dict[str, Any]) -> str:
        shared = (timing.get("shared") or {})
        current_window = shared.get("current_window") or {}
        next_windows = shared.get("next_favorable_windows") or []
        climate = current_window.get("climate", "unknown")
        if climate in {"highly_favorable", "favorable"}:
            return "Current joint timing is supportive for marriage decisions."
        if next_windows:
            first = next_windows[0]
            return f"Static compatibility may be fine, but the next better joint window starts around {first.get('start_date')}."
        return "Timing overlay is neutral or unavailable, so rely more on the static match and deeper chart review."
