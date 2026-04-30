"""Timing-aware marriage suitability overlay for kundli matching."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .astro_utils import get_house_from_chart

FAVORABLE_PLANETS = {"Venus", "Jupiter", "Moon", "Mercury"}
CHALLENGING_PLANETS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
MARRIAGE_HOUSES = {2, 7, 11}
PRESSURE_HOUSES = {6, 8, 12}


class DashaPeriodProvider:
    """Lazy wrapper around the shared Vimshottari calculator."""

    def get_periods(self, birth_data: Dict[str, Any], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        try:
            from shared.dasha_calculator import DashaCalculator
        except Exception:
            return []
        calc = DashaCalculator()
        return calc.get_dasha_periods_for_range(
            birth_data,
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.min.time()),
        )


class TimingOverlayAnalyzer:
    def __init__(self, current_date: Optional[date] = None, dasha_provider: Optional[DashaPeriodProvider] = None) -> None:
        self.current_date = current_date or date.today()
        self.dasha_provider = dasha_provider or DashaPeriodProvider()

    def analyze(
        self,
        boy_chart: Dict[str, Any],
        girl_chart: Dict[str, Any],
        boy_birth: Dict[str, Any],
        girl_birth: Dict[str, Any],
        boy_profile: Dict[str, Any],
        girl_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        window_start = self.current_date
        window_end = self.current_date + timedelta(days=730)

        boy_timing = self._person_timing("boy", boy_chart, boy_birth, boy_profile, window_start, window_end)
        girl_timing = self._person_timing("girl", girl_chart, girl_birth, girl_profile, window_start, window_end)
        shared = self._shared_timing(boy_timing, girl_timing)

        return {
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "boy": boy_timing,
            "girl": girl_timing,
            "shared": shared,
        }

    def _person_timing(
        self,
        label: str,
        chart: Dict[str, Any],
        birth_data: Dict[str, Any],
        profile: Dict[str, Any],
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        periods = self.dasha_provider.get_periods(birth_data, start_date, end_date)
        relevant = self._relevant_planets(chart, profile)
        windows = []
        current_window = None
        best_score = -1
        best_window = None

        for period in periods:
            scored = self._score_period(chart, profile, period, relevant)
            windows.append(scored)
            if scored["contains_current_date"]:
                current_window = scored
            if scored["score"] > best_score:
                best_score = scored["score"]
                best_window = scored

        favorable = [row for row in windows if row["score"] >= 65]
        caution = [row for row in windows if row["score"] < 45]

        return {
            "label": label,
            "relevant_planets": sorted(relevant),
            "current_window": current_window or self._unknown_window(),
            "best_window": best_window or self._unknown_window(),
            "next_favorable_windows": favorable[:5],
            "caution_windows": caution[:5],
            "window_scores": windows[:18],
        }

    def _relevant_planets(self, chart: Dict[str, Any], profile: Dict[str, Any]) -> set[str]:
        seventh_lord = (profile.get("seventh_house") or {}).get("lord")
        active = {"Venus", "Jupiter", "Moon"}
        if seventh_lord:
            active.add(seventh_lord)

        for planet in ("Venus", "Jupiter", "Moon", "Mars", "Saturn"):
            house_num = get_house_from_chart(chart, planet)
            if house_num in MARRIAGE_HOUSES:
                active.add(planet)
        return active

    def _score_period(
        self,
        chart: Dict[str, Any],
        profile: Dict[str, Any],
        period: Dict[str, Any],
        relevant: set[str],
    ) -> Dict[str, Any]:
        md = period.get("mahadasha")
        ad = period.get("antardasha")
        pd = period.get("pratyantardasha")
        start = self._to_date(period.get("start_date"))
        end = self._to_date(period.get("end_date"))

        score = 50.0
        reasons: List[str] = []
        risks: List[str] = []

        for planet, weight, label in ((md, 20, "Mahadasha"), (ad, 14, "Antardasha"), (pd, 7, "Pratyantardasha")):
            if not planet:
                continue
            if planet in relevant:
                score += weight
                reasons.append(f"{label} lord {planet} is marriage-relevant in this chart")
            if planet in FAVORABLE_PLANETS:
                score += weight * 0.35
                reasons.append(f"{label} lord {planet} is naturally supportive")
            if planet in CHALLENGING_PLANETS:
                score -= weight * 0.3
                risks.append(f"{label} lord {planet} can delay or pressure commitment")

            house_num = get_house_from_chart(chart, planet)
            if house_num in MARRIAGE_HOUSES:
                score += 8
                reasons.append(f"{label} lord {planet} activates marriage house {house_num}")
            elif house_num in PRESSURE_HOUSES:
                score -= 8
                risks.append(f"{label} lord {planet} sits in pressure house {house_num}")

        navamsa_score = ((profile.get("navamsa_synthesis") or {}).get("score") or 50)
        seventh_score = (((profile.get("seventh_house") or {}).get("d1_strength") or {}).get("score") or 50)
        score += (navamsa_score - 50) * 0.12
        score += (seventh_score - 50) * 0.08
        if navamsa_score >= 65:
            reasons.append("Navamsa supports relationship maturity during activation")
        elif navamsa_score < 45:
            risks.append("Navamsa shows adjustment pressure even if timing activates")

        score = max(0.0, min(100.0, round(score, 1)))
        climate = self._climate(score)

        return {
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None,
            "mahadasha": md,
            "antardasha": ad,
            "pratyantardasha": pd,
            "score": score,
            "climate": climate,
            "supports": reasons[:6],
            "risks": risks[:6],
            "contains_current_date": bool(start and end and start <= self.current_date <= end),
        }

    def _shared_timing(self, boy_timing: Dict[str, Any], girl_timing: Dict[str, Any]) -> Dict[str, Any]:
        windows = []
        for boy_window in boy_timing.get("window_scores", []):
            for girl_window in girl_timing.get("window_scores", []):
                overlap = self._overlap(
                    boy_window.get("start_date"),
                    boy_window.get("end_date"),
                    girl_window.get("start_date"),
                    girl_window.get("end_date"),
                )
                if not overlap:
                    continue
                joint_score = round((boy_window["score"] + girl_window["score"]) / 2.0, 1)
                windows.append(
                    {
                        "start_date": overlap["start_date"],
                        "end_date": overlap["end_date"],
                        "score": joint_score,
                        "climate": self._climate(joint_score),
                        "boy_context": f"{boy_window['mahadasha']}/{boy_window['antardasha']}",
                        "girl_context": f"{girl_window['mahadasha']}/{girl_window['antardasha']}",
                    }
                )
        windows.sort(key=lambda row: (-row["score"], row["start_date"] or ""))
        current_shared = next((row for row in windows if self._contains_current(row)), self._unknown_window())
        return {
            "joint_readiness_score": round(
                (
                    (boy_timing.get("current_window") or {}).get("score", 50)
                    + (girl_timing.get("current_window") or {}).get("score", 50)
                ) / 2.0,
                1,
            ),
            "current_window": current_shared,
            "next_favorable_windows": [row for row in windows if row["score"] >= 65][:5],
            "next_caution_windows": [row for row in windows if row["score"] < 45][:5],
        }

    def _contains_current(self, row: Dict[str, Any]) -> bool:
        start = self._to_date(row.get("start_date"))
        end = self._to_date(row.get("end_date"))
        return bool(start and end and start <= self.current_date <= end)

    def _overlap(
        self,
        start_a: Optional[str],
        end_a: Optional[str],
        start_b: Optional[str],
        end_b: Optional[str],
    ) -> Optional[Dict[str, str]]:
        sa, ea, sb, eb = map(self._to_date, (start_a, end_a, start_b, end_b))
        if not all([sa, ea, sb, eb]):
            return None
        start = max(sa, sb)
        end = min(ea, eb)
        if start > end:
            return None
        return {"start_date": start.isoformat(), "end_date": end.isoformat()}

    def _to_date(self, value: Any) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
        return None

    def _climate(self, score: float) -> str:
        if score >= 80:
            return "highly_favorable"
        if score >= 65:
            return "favorable"
        if score >= 45:
            return "mixed"
        return "challenging"

    def _unknown_window(self) -> Dict[str, Any]:
        return {
            "start_date": None,
            "end_date": None,
            "score": 50.0,
            "climate": "unknown",
            "supports": [],
            "risks": [],
            "contains_current_date": False,
        }
