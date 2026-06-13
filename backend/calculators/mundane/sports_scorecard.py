from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import swisseph as swe

from calculators.classical_shadbala import get_hora_lord


SIGN_LORDS = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Mars",
    8: "Jupiter",
    9: "Saturn",
    10: "Saturn",
    11: "Jupiter",
}

EXALTATION_SIGNS = {
    "Sun": 0,
    "Moon": 1,
    "Mars": 9,
    "Mercury": 5,
    "Jupiter": 3,
    "Venus": 11,
    "Saturn": 6,
}

DEBILITATION_SIGNS = {
    "Sun": 6,
    "Moon": 7,
    "Mars": 3,
    "Mercury": 11,
    "Jupiter": 9,
    "Venus": 5,
    "Saturn": 0,
}

NATURAL_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}

BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}

GOOD_TITHIS = {
    "Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi"
}
SHARP_TITHIS = {"Chaturthi", "Navami", "Chaturdashi", "Amavasya"}

GOOD_YOGAS = {"Siddhi", "Shubha", "Shukla", "Brahma", "Indra", "Saubhagya", "Sukarma"}
HARSH_YOGAS = {"Vyatipata", "Vaidhriti", "Atiganda", "Shula", "Ganda", "Vyaghata", "Parigha"}

GOOD_NAKSHATRAS = {"Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Hasta", "Anuradha", "Shravana", "Revati"}
FIERCE_NAKSHATRAS = {"Ardra", "Ashlesha", "Magha", "Jyeshtha", "Mula", "Purva Bhadrapada"}
VARA_LORDS = {
    "Sunday": "Sun",
    "Monday": "Moon",
    "Tuesday": "Mars",
    "Wednesday": "Mercury",
    "Thursday": "Jupiter",
    "Friday": "Venus",
    "Saturday": "Saturn",
}


@dataclass
class SideResult:
    entity: str
    house_anchor: int
    house_lord: str
    score: int
    reasons: List[str]


class SportsMundaneScorecard:
    """Deterministic sports scoring layer for mundane match outcome calls."""

    def build(
        self,
        *,
        entities: List[str],
        event_chart: Dict[str, Any],
        event_panchang: Optional[Dict[str, Any]],
        entity_charts: Dict[str, Any],
        locational_analysis: Dict[str, Any],
        latitude: float,
        longitude: float,
        event_date: str,
        event_time: str,
        timezone_offset: float,
    ) -> Optional[Dict[str, Any]]:
        if len(entities) < 2 or not event_chart:
            return None

        team_a = entities[0]
        team_b = entities[1]
        asc_sign = int((event_chart.get("ascendant") or 0) / 30) % 12
        seventh_sign = (asc_sign + 6) % 12

        jd = self._julian_day(event_date, event_time, timezone_offset)
        birth_data = {"latitude": latitude, "longitude": longitude}
        day_lord = self._day_lord_from_panchang(event_panchang)
        hora_lord = get_hora_lord(jd, birth_data)

        side_a = self._score_side(
            entity=team_a,
            side_house=1,
            side_sign=asc_sign,
            event_chart=event_chart,
            day_lord=day_lord,
            hora_lord=hora_lord,
            entity_chart=entity_charts.get(team_a) or {},
            locational_chart=(locational_analysis.get(team_a) or {}).get("lagna_chart"),
        )
        side_b = self._score_side(
            entity=team_b,
            side_house=7,
            side_sign=seventh_sign,
            event_chart=event_chart,
            day_lord=day_lord,
            hora_lord=hora_lord,
            entity_chart=entity_charts.get(team_b) or {},
            locational_chart=(locational_analysis.get(team_b) or {}).get("lagna_chart"),
        )

        shared_factors = self._shared_event_factors(event_panchang)
        volatility = shared_factors["volatility"]
        closeness = abs(side_a.score - side_b.score)

        result_type = "winner"
        predicted_winner = side_a.entity if side_a.score >= side_b.score else side_b.entity
        confidence = self._confidence_from_margin(closeness, volatility)
        if closeness <= 2:
            result_type = "draw_or_extra_time" if volatility >= 2 else "narrow_edge"
        if closeness <= 1 and volatility >= 2:
            predicted_winner = None

        return {
            "available": True,
            "category": "sports",
            "method": "deterministic_event_chart_scorecard_v2",
            "sides": [
                {
                    "entity": side_a.entity,
                    "anchor_house": side_a.house_anchor,
                    "anchor_lord": side_a.house_lord,
                    "score": side_a.score,
                    "reasons": side_a.reasons,
                },
                {
                    "entity": side_b.entity,
                    "anchor_house": side_b.house_anchor,
                    "anchor_lord": side_b.house_lord,
                    "score": side_b.score,
                    "reasons": side_b.reasons,
                },
            ],
            "event_lords": {
                "day_lord": day_lord,
                "hora_lord": hora_lord,
                "ascendant_lord": SIGN_LORDS[asc_sign],
                "seventh_lord": SIGN_LORDS[seventh_sign],
            },
            "shared_factors": shared_factors,
            "edge": {
                "predicted_winner": predicted_winner,
                "margin_points": closeness,
                "result_type": result_type,
                "confidence_percent": confidence,
            },
        }

    def _score_side(
        self,
        *,
        entity: str,
        side_house: int,
        side_sign: int,
        event_chart: Dict[str, Any],
        day_lord: str,
        hora_lord: str,
        entity_chart: Dict[str, Any],
        locational_chart: Optional[Dict[str, Any]],
    ) -> SideResult:
        planets = event_chart.get("planets") or {}
        moon = planets.get("Moon") or {}
        lord = SIGN_LORDS[side_sign]
        lord_data = planets.get(lord) or {}
        score = 0
        reasons: List[str] = []

        lord_house = int(lord_data.get("house") or 0)
        lord_sign = lord_data.get("sign")

        if lord_house in {1, 4, 7, 10}:
            score += 3
            reasons.append(f"{lord} is in a kendra house ({lord_house}) in the event chart")
        elif lord_house in {5, 9, 11}:
            score += 2
            reasons.append(f"{lord} supports the side from house {lord_house}")
        elif lord_house in {6, 8, 12}:
            score -= 3
            reasons.append(f"{lord} is under pressure from dusthana house {lord_house}")

        if lord_sign == EXALTATION_SIGNS.get(lord):
            score += 3
            reasons.append(f"{lord} is exalted in the event chart")
        elif lord_sign == DEBILITATION_SIGNS.get(lord):
            score -= 3
            reasons.append(f"{lord} is debilitated in the event chart")
        elif lord_sign == side_sign:
            score += 2
            reasons.append(f"{lord} holds its own sign, stabilizing the side")

        moon_rel_house = self._relative_house(side_sign, moon.get("sign"))
        if moon_rel_house in {1, 3, 6, 10, 11}:
            score += 2
            reasons.append(f"Moon supports competitive momentum from relative house {moon_rel_house}")
        elif moon_rel_house in {8, 12}:
            score -= 2
            reasons.append(f"Moon weakens the side from relative house {moon_rel_house}")

        if hora_lord == lord:
            score += 2
            reasons.append(f"Hora lord {hora_lord} matches the side's anchor lord")
        elif self._is_friend(hora_lord, lord):
            score += 1
            reasons.append(f"Hora lord {hora_lord} is friendly to {lord}")

        if day_lord == lord:
            score += 1
            reasons.append(f"Day lord {day_lord} reinforces the side lord")
        elif self._is_friend(day_lord, lord):
            score += 1
            reasons.append(f"Day lord {day_lord} is friendly to {lord}")

        score += self._entity_dasha_score(entity_chart, lord, reasons)
        score += self._locational_support_score(locational_chart, reasons)

        return SideResult(
            entity=entity,
            house_anchor=side_house,
            house_lord=lord,
            score=score,
            reasons=reasons,
        )

    def _entity_dasha_score(self, entity_chart: Dict[str, Any], side_lord: str, reasons: List[str]) -> int:
        if not entity_chart.get("available"):
            return 0
        dasha = entity_chart.get("dasha") or {}
        natal_chart = entity_chart.get("natal_chart") or {}
        natal_planets = natal_chart.get("planets") or {}

        score = 0
        md = (dasha.get("mahadasha") or {}).get("planet")
        ad = (dasha.get("antardasha") or {}).get("planet")
        for label, planet, weight in (("Mahadasha", md, 2), ("Antardasha", ad, 2)):
            if not planet:
                continue
            if planet == side_lord:
                score += weight
                reasons.append(f"{label} lord {planet} directly matches the side lord")
            elif planet in BENEFICS:
                score += 1
                reasons.append(f"{label} lord {planet} is a natural benefic")
            elif planet in MALEFICS:
                score -= 1
                reasons.append(f"{label} lord {planet} is a natural malefic")

            natal_house = int((natal_planets.get(planet) or {}).get("house") or 0)
            if natal_house in {1, 5, 9, 10, 11}:
                score += 1
                reasons.append(f"{label} lord {planet} is well-placed in the entity natal chart")
            elif natal_house in {6, 8, 12}:
                score -= 1
                reasons.append(f"{label} lord {planet} is stressed in the entity natal chart")
        return score

    def _locational_support_score(self, locational_chart: Optional[Dict[str, Any]], reasons: List[str]) -> int:
        if not locational_chart:
            return 0
        asc = locational_chart.get("ascendant")
        planets = locational_chart.get("planets") or {}
        if asc is None:
            return 0
        lagna_sign = int(asc / 30) % 12
        lagna_lord = SIGN_LORDS[lagna_sign]
        lagna_lord_house = int((planets.get(lagna_lord) or {}).get("house") or 0)
        if lagna_lord_house in {1, 4, 7, 10, 11}:
            reasons.append(f"Locational lagna lord {lagna_lord} is supportive from house {lagna_lord_house}")
            return 2
        if lagna_lord_house in {6, 8, 12}:
            reasons.append(f"Locational lagna lord {lagna_lord} is strained from house {lagna_lord_house}")
            return -2
        return 0

    def _shared_event_factors(self, event_panchang: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not event_panchang:
            return {"volatility": 0, "notes": []}

        notes: List[str] = []
        volatility = 0
        tithi = ((event_panchang.get("tithi") or {}).get("name")) or ""
        yoga = ((event_panchang.get("yoga") or {}).get("name")) or ""
        nak = ((event_panchang.get("nakshatra") or {}).get("name")) or ""

        if tithi in GOOD_TITHIS:
            notes.append(f"Tithi {tithi} supports clean execution")
        elif tithi in SHARP_TITHIS:
            volatility += 1
            notes.append(f"Tithi {tithi} increases friction and error risk")

        if yoga in GOOD_YOGAS:
            notes.append(f"Yoga {yoga} improves coordination and finishing")
        elif yoga in HARSH_YOGAS:
            volatility += 1
            notes.append(f"Yoga {yoga} raises disruption and volatility")

        if nak in GOOD_NAKSHATRAS:
            notes.append(f"Nakshatra {nak} supports smoother play patterns")
        elif nak in FIERCE_NAKSHATRAS:
            volatility += 1
            notes.append(f"Nakshatra {nak} tends toward fierce, unstable phases")

        return {"volatility": volatility, "notes": notes}

    def _day_lord_from_panchang(self, event_panchang: Optional[Dict[str, Any]]) -> str:
        vara_name = ((event_panchang or {}).get("vara") or {}).get("name")
        return VARA_LORDS.get(vara_name, "Sun")

    def _confidence_from_margin(self, margin: int, volatility: int) -> int:
        base = 50 + min(28, margin * 6)
        penalty = volatility * 6
        return max(51, min(88, base - penalty))

    def _relative_house(self, base_sign: int, target_sign: Optional[int]) -> int:
        if target_sign is None:
            return 0
        return ((int(target_sign) - int(base_sign)) % 12) + 1

    def _is_friend(self, planet_a: str, planet_b: str) -> bool:
        return planet_b in NATURAL_FRIENDS.get(planet_a, set()) or planet_a in NATURAL_FRIENDS.get(planet_b, set())

    def _julian_day(self, event_date: str, event_time: str, timezone_offset: float) -> float:
        dt = datetime.fromisoformat(f"{event_date}T{event_time}")
        utc_hour = dt.hour + (dt.minute / 60.0) + (dt.second / 3600.0) - float(timezone_offset)
        return swe.julday(dt.year, dt.month, dt.day, utc_hour)
