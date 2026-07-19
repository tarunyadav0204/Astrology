"""Chart-based planetary color scoring for Vedic remedial guidance.

Scores planets from lagna functional nature, lordship, yogakaraka, and dignity,
then maps scores onto classical planet→color phrases. Current dasha only
emphasizes already-good or already-bad planets — it never flips a chart-malefic
planet's colors into "favor."
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from calculators.base_calculator import BaseCalculator
from calculators.remedy_engine import RemedyEngine
from vedic_predictions.config.functional_nature import (
    FUNCTIONAL_BENEFICS,
    FUNCTIONAL_MALEFICS,
)

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}

FAVOR_THRESHOLD = 2.0
AVOID_THRESHOLD = -2.0
FAVOR_CAP = 5
AVOID_CAP = 5


class ColorCalculator:
    """Derive favor/avoid colors from the full D1 chart picture."""

    def __init__(self, chart_data: Dict[str, Any], birth_payload: Optional[Dict[str, Any]] = None):
        self.chart_data = chart_data if isinstance(chart_data, dict) else {}
        self.birth_payload = birth_payload if isinstance(birth_payload, dict) else {}
        self.sign_lords = BaseCalculator.SIGN_LORDS
        self.exaltation = BaseCalculator.EXALTATION_SIGNS
        self.debilitation = BaseCalculator.DEBILITATION_SIGNS

    def calculate(
        self,
        current_md: Optional[str] = None,
        current_ad: Optional[str] = None,
    ) -> Dict[str, Any]:
        asc = self._asc_sign()
        houses_by_planet = self._houses_ruled_map(asc)
        planet_scores = {
            planet: self._score_planet(
                planet,
                asc=asc,
                houses=houses_by_planet.get(planet) or [],
                current_md=current_md,
                current_ad=current_ad,
            )
            for planet in PLANETS
        }

        color_scores, color_owners = self._aggregate_colors(planet_scores)
        favor, avoid, mixed = self._pick_favor_avoid(color_scores, color_owners, planet_scores)

        ad_support = ""
        ad_score = float((planet_scores.get(current_ad) or {}).get("score") or 0)
        if current_ad and ad_score > 0:
            ad_support = RemedyEngine.COLORS.get(current_ad) or ""

        period_note = self._period_note(current_md, current_ad, planet_scores)
        period_note_hi = self._period_note_hi(current_md, current_ad, planet_scores)

        return {
            "current_md": current_md,
            "current_ad": current_ad,
            "ascendant_sign": asc,
            "planet_scores": planet_scores,
            "color_scores": {
                name: round(score, 2) for name, score in sorted(color_scores.items(), key=lambda x: -x[1])
            },
            "wear_colors": ", ".join(item["color"] for item in favor),
            "support_colors": ad_support,
            "avoid_colors": ", ".join(item["color"] for item in avoid),
            "favor_evidence": favor,
            "avoid_evidence": avoid,
            "mixed_colors": mixed,
            "period_note": period_note,
            "period_note_hi": period_note_hi,
            "note": (
                "Colors are scored from lagna functional nature, yogakaraka/lordship, and dignity. "
                "Current dasha only strengthens an already supportive or challenging signal — "
                "it does not make a chart-malefic planet's colors favorable."
            ),
            "note_hi": (
                "रंग लग्न के कार्यात्मक स्वभाव, योगकारक/भावेश और दशा से आँके गए हैं। "
                "वर्तमान दशा केवल पहले से शुभ/अशुभ संकेत को बल देती है — "
                "चार्ट-अशुभ ग्रह के रंगों को अनुकूल नहीं बनाती।"
            ),
        }

    # ------------------------------------------------------------------ scoring
    def _score_planet(
        self,
        planet: str,
        *,
        asc: int,
        houses: List[int],
        current_md: Optional[str],
        current_ad: Optional[str],
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        score = 0.0
        house_set = set(int(h) for h in houses)
        # Yogakaraka: owns both a kendra and a trikona (lagna-only lordship is not enough).
        is_yogakaraka = (
            bool(house_set & KENDRA)
            and bool(house_set & TRIKONA)
            and len(house_set) >= 2
        )

        benefics = set(FUNCTIONAL_BENEFICS.get(asc) or [])
        malefics = set(FUNCTIONAL_MALEFICS.get(asc) or [])
        if planet in benefics:
            score += 3
            reasons.append("functional benefic")
        elif planet in malefics:
            score -= 3
            reasons.append("functional malefic")

        if is_yogakaraka:
            score += 4
            reasons.append("yogakaraka")

        if 1 in house_set:
            score += 2
            reasons.append("lagna lord")
        if 5 in house_set or 9 in house_set:
            score += 1
            reasons.append("5th/9th lord")
        if (house_set & DUSTHANA) and not is_yogakaraka:
            score -= 1
            reasons.append("dusthana lord")

        dignity = self._dignity(planet)
        if dignity in {"Exalted", "Own Sign"}:
            score += 1
            reasons.append(dignity.lower())
        elif dignity == "Debilitated":
            score -= 2
            reasons.append("debilitated")

        if self._is_combust(planet):
            score -= 1
            reasons.append("combust")

        # Dasha only amplifies existing polarity — never flips sign.
        base_before_dasha = score
        if planet == current_md:
            if base_before_dasha > 0:
                score += 1
                reasons.append("current MD (supportive)")
            elif base_before_dasha < 0:
                score -= 1
                reasons.append("current MD (caution)")
        if planet == current_ad and planet != current_md:
            if base_before_dasha > 0:
                score += 0.5
                reasons.append("current AD (supportive)")
            elif base_before_dasha < 0:
                score -= 0.5
                reasons.append("current AD (caution)")

        return {
            "planet": planet,
            "score": round(score, 2),
            "houses_ruled": sorted(house_set),
            "yogakaraka": is_yogakaraka,
            "dignity": dignity,
            "reasons": reasons,
        }

    def _aggregate_colors(
        self,
        planet_scores: Dict[str, Dict[str, Any]],
    ) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
        color_scores: Dict[str, float] = {}
        color_owners: Dict[str, List[str]] = {}
        for planet, pdata in planet_scores.items():
            blob = RemedyEngine.COLORS.get(planet) or ""
            pscore = float(pdata.get("score") or 0)
            for phrase in self._split_colors(blob):
                color_scores[phrase] = color_scores.get(phrase, 0.0) + pscore
                color_owners.setdefault(phrase, []).append(planet)
        return color_scores, color_owners

    def _pick_favor_avoid(
        self,
        color_scores: Dict[str, float],
        color_owners: Dict[str, List[str]],
        planet_scores: Dict[str, Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        favor_candidates = [
            (name, score) for name, score in color_scores.items() if score >= FAVOR_THRESHOLD
        ]
        avoid_candidates = [
            (name, score) for name, score in color_scores.items() if score <= AVOID_THRESHOLD
        ]
        favor_names = {n for n, _ in favor_candidates}
        avoid_names = {n for n, _ in avoid_candidates}
        conflict = favor_names & avoid_names
        mixed = sorted(conflict)

        favor_candidates = [(n, s) for n, s in favor_candidates if n not in conflict]
        avoid_candidates = [(n, s) for n, s in avoid_candidates if n not in conflict]
        favor_candidates.sort(key=lambda x: (-x[1], x[0]))
        avoid_candidates.sort(key=lambda x: (x[1], x[0]))

        favor = [
            self._evidence_row(name, score, color_owners.get(name) or [], planet_scores)
            for name, score in favor_candidates[:FAVOR_CAP]
        ]
        avoid = [
            self._evidence_row(name, score, color_owners.get(name) or [], planet_scores)
            for name, score in avoid_candidates[:AVOID_CAP]
        ]
        return favor, avoid, mixed

    def _evidence_row(
        self,
        color: str,
        score: float,
        owners: List[str],
        planet_scores: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        bits = []
        for planet in owners:
            pdata = planet_scores.get(planet) or {}
            reasons = ", ".join(pdata.get("reasons") or []) or "chart factor"
            bits.append(f"{planet} ({reasons})")
        return {
            "color": color,
            "score": round(score, 2),
            "planets": owners,
            "evidence": f"{color} ← " + "; ".join(bits),
        }

    def _period_note(
        self,
        md: Optional[str],
        ad: Optional[str],
        planet_scores: Dict[str, Dict[str, Any]],
    ) -> str:
        parts = []
        if md:
            sc = float((planet_scores.get(md) or {}).get("score") or 0)
            if sc > 0:
                parts.append(f"Current Mahadasha ({md}) supports its colors.")
            elif sc < 0:
                parts.append(f"Current Mahadasha ({md}) is chart-challenging — do not treat its colors as lucky.")
            else:
                parts.append(f"Current Mahadasha ({md}) is mixed/neutral for color.")
        if ad and ad != md:
            sc = float((planet_scores.get(ad) or {}).get("score") or 0)
            if sc > 0:
                parts.append(f"Antardasha ({ad}) adds supportive accent colors.")
            elif sc < 0:
                parts.append(f"Antardasha ({ad}) adds caution — avoid leaning on its colors.")
        return " ".join(parts) if parts else "No active dasha emphasis available."

    def _period_note_hi(
        self,
        md: Optional[str],
        ad: Optional[str],
        planet_scores: Dict[str, Dict[str, Any]],
    ) -> str:
        parts = []
        if md:
            sc = float((planet_scores.get(md) or {}).get("score") or 0)
            if sc > 0:
                parts.append(f"वर्तमान महादशा ({md}) के रंग सहायक हैं।")
            elif sc < 0:
                parts.append(f"वर्तमान महादशा ({md}) चार्ट में चुनौतीपूर्ण है — उसके रंगों को भाग्यशाली न मानें।")
            else:
                parts.append(f"वर्तमान महादशा ({md}) रंग दृष्टि से मिश्रित/सम है।")
        if ad and ad != md:
            sc = float((planet_scores.get(ad) or {}).get("score") or 0)
            if sc > 0:
                parts.append(f"अन्तर्दशा ({ad}) सहायक रंग जोड़ती है।")
            elif sc < 0:
                parts.append(f"अन्तर्दशा ({ad}) सावधानी माँगती है — उसके रंगों पर निर्भर न रहें।")
        return " ".join(parts) if parts else "सक्रिय दशा संकेत उपलब्ध नहीं।"

    # ------------------------------------------------------------------ helpers
    def _asc_sign(self) -> int:
        asc = self.chart_data.get("ascendant")
        if isinstance(asc, (int, float)):
            return int(float(asc) // 30) % 12
        if isinstance(asc, dict):
            if asc.get("sign") is not None:
                return int(asc["sign"]) % 12
            if asc.get("longitude") is not None:
                return int(float(asc["longitude"]) // 30) % 12
        raise ValueError("Ascendant unavailable for color calculation")

    def _houses_ruled_map(self, asc: int) -> Dict[str, List[int]]:
        out: Dict[str, List[int]] = {p: [] for p in PLANETS}
        for house in range(1, 13):
            sign = (asc + house - 1) % 12
            lord = self.sign_lords.get(sign)
            if lord in out:
                out[lord].append(house)
        return out

    def _planet_sign(self, planet: str) -> Optional[int]:
        pdata = (self.chart_data.get("planets") or {}).get(planet)
        if not isinstance(pdata, dict):
            return None
        if pdata.get("sign") is not None:
            try:
                return int(pdata["sign"]) % 12
            except Exception:
                pass
        lon = pdata.get("longitude")
        if lon is not None:
            try:
                return int(float(lon) // 30) % 12
            except Exception:
                return None
        return None

    def _dignity(self, planet: str) -> str:
        sign = self._planet_sign(planet)
        if sign is None:
            return "Neutral"
        if self.exaltation.get(planet) == sign:
            return "Exalted"
        if self.debilitation.get(planet) == sign:
            return "Debilitated"
        own = [s for s, lord in self.sign_lords.items() if lord == planet]
        if sign in own:
            return "Own Sign"
        return "Neutral"

    def _is_combust(self, planet: str) -> bool:
        if planet in {"Sun", "Rahu", "Ketu"}:
            return False
        pdata = (self.chart_data.get("planets") or {}).get(planet)
        if not isinstance(pdata, dict):
            return False
        if pdata.get("is_combust") is True or str(pdata.get("combustion_status") or "").lower() == "combust":
            return True
        if pdata.get("combust") is True:
            return True
        # Fallback: within 8° of Sun longitude when available.
        sun = (self.chart_data.get("planets") or {}).get("Sun")
        if not isinstance(sun, dict):
            return False
        try:
            p_lon = float(pdata.get("longitude"))
            s_lon = float(sun.get("longitude"))
        except Exception:
            return False
        diff = abs((p_lon - s_lon + 180) % 360 - 180)
        return diff <= 8.0

    @staticmethod
    def _split_colors(raw: str) -> List[str]:
        return [p.strip() for p in str(raw or "").split(",") if p.strip()]
