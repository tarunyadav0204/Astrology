"""Improved deterministic Ashtakoota calculator."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .astro_utils import get_moon_profile, grade_from_percentage
from .constants import (
    NAKSHATRA_GANA,
    NAKSHATRA_NADI,
    NAKSHATRA_YONI,
    PLANET_FRIENDSHIPS,
    SIGN_LORDS,
)
from .exceptions import CompatibilityExceptions
from .rules import RuleProfile, get_rule_profile


class AshtakootaCalculator:
    def __init__(self, rule_profile: RuleProfile | str = "balanced_modern") -> None:
        self.rule_profile = rule_profile if isinstance(rule_profile, RuleProfile) else get_rule_profile(rule_profile)
        self.exceptions = CompatibilityExceptions(self.rule_profile)

    def calculate(self, boy_chart: Dict[str, Any], girl_chart: Dict[str, Any]) -> Dict[str, Any]:
        boy_moon = get_moon_profile(boy_chart)
        girl_moon = get_moon_profile(girl_chart)

        if not boy_moon["nakshatra_number"] or not girl_moon["nakshatra_number"]:
            raise ValueError("Moon longitude missing for one or both charts")

        boy_rashi = boy_moon["sign"]
        girl_rashi = girl_moon["sign"]
        boy_nak = boy_moon["nakshatra_number"]
        girl_nak = girl_moon["nakshatra_number"]

        koots = {
            "varna": self._varna(boy_rashi, girl_rashi),
            "vashya": self._vashya(boy_rashi, girl_rashi),
            "tara": self._tara(boy_nak, girl_nak),
            "yoni": self._yoni(boy_nak, girl_nak),
            "graha_maitri": self._graha_maitri(boy_rashi, girl_rashi),
            "gana": self._gana(boy_nak, girl_nak),
            "bhakoot": self._bhakoot(boy_rashi, girl_rashi),
            "nadi": self._nadi(boy_nak, girl_nak),
        }
        exceptions = self.exceptions.evaluate(boy_chart, girl_chart, boy_moon, girl_moon, koots)

        total_score = round(sum(float(item["score"]) for item in koots.values()), 2)
        percentage = round((total_score / 36.0) * 100.0, 1)
        critical_issues = self._critical_issues(koots)
        effective_total_score = round(self._effective_total_score(koots, exceptions), 2)
        effective_percentage = round((effective_total_score / 36.0) * 100.0, 1)
        effective_critical_issues = self._effective_critical_issues(critical_issues, exceptions)
        strengths = [name for name, item in koots.items() if item["score"] == item["max_score"]]

        return {
            "version": "v2",
            "source": "deterministic_ashtakoota",
            "rule_profile": self.rule_profile.key,
            "boy_moon_profile": boy_moon,
            "girl_moon_profile": girl_moon,
            "total_score": total_score,
            "max_score": 36,
            "percentage": percentage,
            "grade": grade_from_percentage(percentage),
            "compatibility_level": self._compatibility_level(percentage),
            "effective_total_score": effective_total_score,
            "effective_percentage": effective_percentage,
            "effective_grade": grade_from_percentage(effective_percentage),
            "effective_compatibility_level": self._compatibility_level(effective_percentage),
            "koots": koots,
            "exceptions": exceptions,
            "critical_issues": critical_issues,
            "effective_critical_issues": effective_critical_issues,
            "strengths": strengths,
        }

    def _varna(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        varna_map = {
            1: "Kshatriya",
            2: "Vaishya",
            3: "Shudra",
            4: "Brahmin",
            5: "Kshatriya",
            6: "Vaishya",
            7: "Shudra",
            8: "Brahmin",
            9: "Kshatriya",
            10: "Vaishya",
            11: "Shudra",
            12: "Brahmin",
        }
        order = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1}
        boy_varna = varna_map[boy_rashi]
        girl_varna = varna_map[girl_rashi]
        score = 1 if order[boy_varna] >= order[girl_varna] else 0
        return {
            "score": score,
            "max_score": 1,
            "boy_varna": boy_varna,
            "girl_varna": girl_varna,
            "description": f"Boy: {boy_varna}, Girl: {girl_varna}",
            "interpretation": (
                "**What Varna measures**\n"
                "Varna Koota compares the mental and spiritual orientation of both partners through their Moon signs. "
                "It is a small 1-point factor, so it should never dominate the match by itself.\n"
                "**How to read this result**\n"
                f"The boy's Varna is {boy_varna} and the girl's Varna is {girl_varna}. "
                + (
                    "This supports compatibility because the traditional order is balanced for this pairing."
                    if score
                    else "This shows a traditional mismatch in orientation, but because Varna carries only 1 point, it is a mild caution rather than a decisive rejection."
                )
            ),
        }

    def _vashya(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        vashya_map = {
            1: "Chatushpada",
            2: "Chatushpada",
            3: "Manava",
            4: "Jalachara",
            5: "Vanachara",
            6: "Manava",
            7: "Manava",
            8: "Keeta",
            9: "Manava",
            10: "Chatushpada",
            11: "Manava",
            12: "Jalachara",
        }
        score_matrix = {
            ("Chatushpada", "Chatushpada"): 2,
            ("Manava", "Manava"): 2,
            ("Jalachara", "Jalachara"): 2,
            ("Vanachara", "Vanachara"): 2,
            ("Keeta", "Keeta"): 2,
            ("Manava", "Jalachara"): 1,
            ("Jalachara", "Manava"): 1,
            ("Chatushpada", "Manava"): 1,
            ("Manava", "Chatushpada"): 1,
            ("Vanachara", "Chatushpada"): 1,
            ("Chatushpada", "Vanachara"): 1,
        }
        boy_v = vashya_map[boy_rashi]
        girl_v = vashya_map[girl_rashi]
        score = score_matrix.get((boy_v, girl_v), 0)
        return {
            "score": score,
            "max_score": 2,
            "boy_vashya": boy_v,
            "girl_vashya": girl_v,
            "description": f"Boy: {boy_v}, Girl: {girl_v}",
            "interpretation": (
                "**What Vashya measures**\n"
                "Vashya Koota studies natural influence, attraction, and how easily two people respond to each other's temperament. "
                "It is about relational pull and day-to-day adaptability.\n"
                "**How to read this result**\n"
                f"The boy's Vashya type is {boy_v} and the girl's Vashya type is {girl_v}. "
                + (
                    "This indicates easy responsiveness and a smoother ability to adjust to each other."
                    if score == 2
                    else "This suggests partial adjustment. The relationship can work, but both people may need conscious patience with each other's instincts."
                    if score
                    else "This suggests a stronger difference in natural temperament, so control, ego, or adjustment issues should be handled carefully."
                )
            ),
        }

    def _tara(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        tara_boy = self._tara_number(girl_nak, boy_nak)
        tara_girl = self._tara_number(boy_nak, girl_nak)
        good = {1, 3, 5, 7}
        okay = {2, 4, 6, 8, 9}
        boy_good = tara_boy in good
        girl_good = tara_girl in good
        if boy_good and girl_good:
            score = 3.0
        elif boy_good or girl_good or tara_boy in okay or tara_girl in okay:
            score = 1.5
        else:
            score = 0.0
        return {
            "score": score,
            "max_score": 3,
            "boy_tara_number": tara_boy,
            "girl_tara_number": tara_girl,
            "description": f"Boy Tara: {tara_boy}, Girl Tara: {tara_girl}",
            "interpretation": (
                "**What Tara measures**\n"
                "Tara Koota checks nakshatra-based wellbeing, fortune, and mutual support. It indicates whether the pair's lunar stars help or disturb each other's growth.\n"
                "**How to read this result**\n"
                f"The boy-side Tara number is {tara_boy} and the girl-side Tara number is {tara_girl}. "
                + (
                    "Both sides are supportive, which is favorable for mutual wellbeing and continuity."
                    if score == 3.0
                    else "The Tara result is mixed or partially supportive. This is workable, but the couple may experience uneven emotional or circumstantial support at times."
                    if score
                    else "This is a sensitive Tara result. It asks for care around wellbeing, family support, and timing of major commitments."
                )
            ),
        }

    def _yoni(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        yoni_a = NAKSHATRA_YONI[boy_nak]
        yoni_b = NAKSHATRA_YONI[girl_nak]
        if yoni_a == yoni_b:
            score = 4
        elif {yoni_a, yoni_b} in [
            {"Horse", "Elephant"},
            {"Cow", "Buffalo"},
            {"Deer", "Monkey"},
            {"Cat", "Sheep"},
        ]:
            score = 3
        elif {yoni_a, yoni_b} in [
            {"Tiger", "Lion"},
            {"Dog", "Monkey"},
            {"Serpent", "Mongoose"},
        ]:
            score = 1
        else:
            score = 2
        return {
            "score": score,
            "max_score": 4,
            "boy_yoni": yoni_a,
            "girl_yoni": yoni_b,
            "description": f"Boy: {yoni_a}, Girl: {yoni_b}",
            "interpretation": (
                "**What Yoni measures**\n"
                "Yoni Koota looks at instinctive attraction, physical chemistry, intimacy, and the private comfort between partners.\n"
                "**How to read this result**\n"
                f"The boy's Yoni is {yoni_a} and the girl's Yoni is {yoni_b}. "
                + (
                    "This is a strong instinctive match, supporting natural comfort and attraction."
                    if score >= 3
                    else "This is a moderate instinctive match. Attraction can exist, but the couple may need emotional safety and communication for intimacy to mature."
                    if score == 2
                    else "This is a sensitive Yoni result. Physical rhythm, comfort, or instinctive reactions may need extra care and understanding."
                )
            ),
        }

    def _graha_maitri(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        boy_lord = SIGN_LORDS[boy_rashi]
        girl_lord = SIGN_LORDS[girl_rashi]
        rel_a = self._planet_relation(boy_lord, girl_lord)
        rel_b = self._planet_relation(girl_lord, boy_lord)

        if boy_lord == girl_lord:
            score = 5
        elif rel_a == "friend" and rel_b == "friend":
            score = 5
        elif "enemy" in {rel_a, rel_b} and "friend" not in {rel_a, rel_b}:
            score = 0
        elif "enemy" in {rel_a, rel_b}:
            score = 1
        elif rel_a == "neutral" and rel_b == "neutral":
            score = 3
        else:
            score = 4
        return {
            "score": score,
            "max_score": 5,
            "boy_lord": boy_lord,
            "girl_lord": girl_lord,
            "description": f"Boy: {boy_lord} ({rel_a}), Girl: {girl_lord} ({rel_b})",
            "interpretation": (
                "**What Graha Maitri measures**\n"
                "Graha Maitri compares the friendship between the Moon sign lords. It reflects mental harmony, communication style, and mutual goodwill.\n"
                "**How to read this result**\n"
                f"The boy's Moon sign lord is {boy_lord} and the girl's Moon sign lord is {girl_lord}. "
                + (
                    "The planetary relationship is supportive, so mental rapport and friendship are strengthened."
                    if score >= 4
                    else "The planetary relationship is neutral or mixed. Communication can be good, but assumptions should be checked."
                    if score >= 3
                    else "The planetary relationship is strained. This does not reject the match, but it highlights the need for mature communication and respect."
                )
            ),
        }

    def _gana(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        boy_g = NAKSHATRA_GANA[boy_nak]
        girl_g = NAKSHATRA_GANA[girl_nak]
        matrix = {
            ("Deva", "Deva"): 6,
            ("Manushya", "Manushya"): 6,
            ("Rakshasa", "Rakshasa"): 6,
            ("Deva", "Manushya"): 5,
            ("Manushya", "Deva"): 5,
            ("Manushya", "Rakshasa"): 1,
            ("Rakshasa", "Manushya"): 1,
            ("Deva", "Rakshasa"): 0,
            ("Rakshasa", "Deva"): 0,
        }
        score = matrix[(boy_g, girl_g)]
        return {
            "score": score,
            "max_score": 6,
            "boy_gana": boy_g,
            "girl_gana": girl_g,
            "description": f"Boy: {boy_g}, Girl: {girl_g}",
            "interpretation": (
                "**What Gana measures**\n"
                "Gana Koota compares basic temperament: gentle, human/practical, or intense/forceful tendencies. It is important for daily behavior and conflict style.\n"
                "**How to read this result**\n"
                f"The boy's Gana is {boy_g} and the girl's Gana is {girl_g}. "
                + (
                    "This shows strong temperament compatibility and an easier behavioral rhythm."
                    if score >= 5
                    else "This shows a workable temperament difference. The couple should consciously respect each other's pace and reactions."
                    if score > 1
                    else "This is a significant temperament gap. It can still be handled, but ego clashes, sensitivity, or lifestyle differences need active management."
                )
            ),
        }

    def _bhakoot(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        forward = ((girl_rashi - boy_rashi) % 12) + 1
        reverse = ((boy_rashi - girl_rashi) % 12) + 1
        if {forward, reverse} == {2, 12}:
            score = 0
            issue = "2/12 Bhakoot Dosha"
        elif {forward, reverse} == {5, 9}:
            score = 0
            issue = "5/9 Bhakoot Dosha"
        elif {forward, reverse} == {6, 8}:
            score = 0
            issue = "6/8 Bhakoot Dosha"
        else:
            score = 7
            issue = None
        return {
            "score": score,
            "max_score": 7,
            "forward_distance": forward,
            "reverse_distance": reverse,
            "issue": issue,
            "description": f"Rashi distances: {forward}/{reverse}",
            "interpretation": (
                "**What Bhakoot measures**\n"
                "Bhakoot Koota studies Moon sign distance and its effect on emotional flow, family growth, prosperity, and long-term domestic harmony.\n"
                "**How to read this result**\n"
                f"The Moon sign distance is {forward}/{reverse}. "
                + (
                    "This is favorable by classical Bhakoot rules and supports family continuity and emotional flow."
                    if score == 7
                    else f"This creates {issue}. It is a serious traditional caution, but final judgment should also consider exceptions, Manglik balance, D1/D9 marriage support, and timing."
                )
            ),
        }

    def _nadi(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        boy_n = NAKSHATRA_NADI[boy_nak]
        girl_n = NAKSHATRA_NADI[girl_nak]
        score = 8 if boy_n != girl_n else 0
        return {
            "score": score,
            "max_score": 8,
            "boy_nadi": boy_n,
            "girl_nadi": girl_n,
            "critical": score == 0,
            "description": f"Boy: {boy_n}, Girl: {girl_n}",
            "interpretation": (
                "**What Nadi measures**\n"
                "Nadi Koota is the highest-weighted Ashtakoota factor. It is traditionally linked with health compatibility, pranic rhythm, progeny, and biological harmony.\n"
                "**How to read this result**\n"
                f"The boy's Nadi is {boy_n} and the girl's Nadi is {girl_n}. "
                + (
                    "Different Nadis are favorable and give full support to this layer."
                    if score == 8
                    else "Same Nadi creates Nadi Dosha in classical matching. This is important, but it should be reviewed together with valid exceptions, nakshatra/pada details, D1/D9 strength, and practical relationship factors."
                )
            ),
        }

    def _tara_number(self, from_nak: int, to_nak: int) -> int:
        distance = ((to_nak - from_nak) % 27) + 1
        return ((distance - 1) % 9) + 1

    def _planet_relation(self, source: str, target: str) -> str:
        if source == target:
            return "same"
        info = PLANET_FRIENDSHIPS.get(source, {})
        if target in info.get("friends", set()):
            return "friend"
        if target in info.get("enemies", set()):
            return "enemy"
        return "neutral"

    def _critical_issues(self, koots: Dict[str, Dict[str, Any]]) -> List[str]:
        issues: List[str] = []
        if koots["nadi"]["score"] == 0:
            issues.append("Nadi Dosha - same Nadi")
        if koots["bhakoot"]["score"] == 0 and koots["bhakoot"].get("issue"):
            issues.append(koots["bhakoot"]["issue"])
        if koots["gana"]["score"] <= 1:
            issues.append("Gana mismatch - temperament gap")
        return issues

    def _effective_total_score(
        self,
        koots: Dict[str, Dict[str, Any]],
        exceptions: Dict[str, Dict[str, Any]],
    ) -> float:
        total = 0.0
        for name, item in koots.items():
            total += float(exceptions.get(name, {}).get("adjusted_score", item["score"]))
        return total

    def _effective_critical_issues(
        self,
        issues: List[str],
        exceptions: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        effective: List[str] = []
        for issue in issues:
            if issue.startswith("Nadi Dosha") and exceptions.get("nadi", {}).get("applies"):
                continue
            if "Bhakoot" in issue and exceptions.get("bhakoot", {}).get("applies"):
                continue
            effective.append(issue)
        return effective

    def _compatibility_level(self, percentage: float) -> str:
        if percentage >= 85:
            return "Strong traditional match"
        if percentage >= 70:
            return "Good traditional match"
        if percentage >= 55:
            return "Workable traditional match"
        if percentage >= 40:
            return "Sensitive traditional match"
        return "Classically difficult match"
