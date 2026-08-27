"""Classical Indu Lagna calculation and structured wealth evidence.

Indu Lagna is a sign-based special lagna.  It has no independently calculated
longitude or nakshatra, so the compatibility planet row returned by
``get_indu_lagna_data`` marks its longitude as a plotting anchor only.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_calculator import BaseCalculator


class InduLagnaCalculator(BaseCalculator):
    """Calculate and analyze Indu Lagna using the classical Kala method."""

    CLASSICAL_PLANETS = (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    )

    # Planetary rays (Kalas) used by the Indu Lagna calculation.
    PLANETARY_RAYS = {
        "Sun": 30,
        "Moon": 16,
        "Mars": 6,
        "Mercury": 8,
        "Jupiter": 10,
        "Venus": 12,
        "Saturn": 1,
    }

    # Whole-sign Parashari graha drishti used by the live Wealth graph.  Node
    # occupation/conjunction is retained separately; disputed 5th/9th node
    # aspects are deliberately excluded from activation evidence.
    ASPECT_HOUSES = {
        "Sun": (7,),
        "Moon": (7,),
        "Mars": (4, 7, 8),
        "Mercury": (7,),
        "Jupiter": (5, 7, 9),
        "Venus": (7,),
        "Saturn": (3, 7, 10),
        "Rahu": (7,),
        "Ketu": (7,),
    }

    NAKSHATRA_NAMES = (
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
        "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
        "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
        "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati",
    )
    NAKSHATRA_LORDS = (
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    )

    def __init__(self, chart_data: Dict[str, Any]):
        super().__init__(chart_data or {})

    @staticmethod
    def _normalize_sign(value: Any, *, field: str) -> int:
        """Return a zero-based sign index and reject absent/malformed data."""
        try:
            sign = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Indu Lagna requires a valid {field} sign") from exc
        if not 0 <= sign < 12:
            raise ValueError(f"Indu Lagna requires {field} sign in the range 0-11")
        return sign

    def _get_ascendant_sign_index(self) -> int:
        ascendant = self.chart_data.get("ascendant")
        if isinstance(ascendant, dict):
            if ascendant.get("sign") is not None:
                return self._normalize_sign(ascendant.get("sign"), field="ascendant")
            ascendant = ascendant.get("longitude")
        try:
            longitude = float(ascendant)
        except (TypeError, ValueError) as exc:
            raise ValueError("Indu Lagna requires a valid ascendant longitude or sign") from exc
        if not 0.0 <= longitude < 360.0:
            raise ValueError("Indu Lagna requires ascendant longitude in the range 0-360")
        return int(longitude // 30)

    def _get_planet_sign_index(self, planet: str) -> int:
        row = (self.chart_data.get("planets") or {}).get(planet)
        if not isinstance(row, dict):
            raise ValueError(f"Indu Lagna requires {planet} in the natal chart")
        if row.get("sign") is not None:
            return self._normalize_sign(row.get("sign"), field=planet)
        try:
            longitude = float(row.get("longitude"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Indu Lagna requires a valid {planet} sign or longitude") from exc
        if not 0.0 <= longitude < 360.0:
            raise ValueError(f"Indu Lagna requires {planet} longitude in the range 0-360")
        return int(longitude // 30)

    def _house_from_sign(self, sign_index: int) -> int:
        return ((sign_index - self._get_ascendant_sign_index()) % 12) + 1

    def _calculation_details(self) -> Dict[str, Any]:
        ascendant_sign = self._get_ascendant_sign_index()
        moon_sign = self._get_planet_sign_index("Moon")
        ninth_from_ascendant = (ascendant_sign + 8) % 12
        ninth_from_moon = (moon_sign + 8) % 12
        ascendant_ninth_lord = self.SIGN_LORDS[ninth_from_ascendant]
        moon_ninth_lord = self.SIGN_LORDS[ninth_from_moon]
        ascendant_kalas = self.PLANETARY_RAYS[ascendant_ninth_lord]
        moon_kalas = self.PLANETARY_RAYS[moon_ninth_lord]
        kala_total = ascendant_kalas + moon_kalas
        count_from_moon = kala_total % 12 or 12
        indu_sign = (moon_sign + count_from_moon - 1) % 12
        return {
            "ascendant_sign": ascendant_sign,
            "ascendant_sign_name": self.SIGN_NAMES[ascendant_sign],
            "moon_sign": moon_sign,
            "moon_sign_name": self.SIGN_NAMES[moon_sign],
            "ninth_from_ascendant_sign": ninth_from_ascendant,
            "ninth_from_ascendant_sign_name": self.SIGN_NAMES[ninth_from_ascendant],
            "ninth_from_ascendant_lord": ascendant_ninth_lord,
            "ninth_from_ascendant_kalas": ascendant_kalas,
            "ninth_from_moon_sign": ninth_from_moon,
            "ninth_from_moon_sign_name": self.SIGN_NAMES[ninth_from_moon],
            "ninth_from_moon_lord": moon_ninth_lord,
            "ninth_from_moon_kalas": moon_kalas,
            "kala_total": kala_total,
            "count_from_moon": count_from_moon,
            "indu_lagna_sign": indu_sign,
            "indu_lagna_sign_name": self.SIGN_NAMES[indu_sign],
        }

    def calculate_indu_lagna(self) -> int:
        """Return the Indu Lagna sign as a one-based number (1-12)."""
        return int(self._calculation_details()["indu_lagna_sign"]) + 1

    def get_indu_lagna_data(self) -> Dict[str, Any]:
        """Return the legacy chart-row shape with explicit sign-only precision."""
        details = self._calculation_details()
        sign_index = int(details["indu_lagna_sign"])
        # Some chart renderers require a numeric longitude.  The sign ingress
        # is supplied solely as a plotting anchor and must never be interpreted
        # as an exact degree, nakshatra or degree-sensitive point.
        longitude_anchor = float(sign_index * 30)
        return {
            "longitude": longitude_anchor,
            "sign": sign_index,
            "sign_name": self.SIGN_NAMES[sign_index],
            "degree": 0.0,
            "house": self._house_from_sign(sign_index),
            "type": "special_lagna",
            "name": "InduLagna",
            "precision": "sign_only",
            "longitude_is_plotting_anchor": True,
            "exact_degree_available": False,
        }

    def _planet_rows_in_sign(self, sign_index: int) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        planets = self.chart_data.get("planets") or {}
        for planet in self.CLASSICAL_PLANETS:
            data = planets.get(planet)
            if not isinstance(data, dict):
                continue
            try:
                planet_sign = self._get_planet_sign_index(planet)
            except ValueError:
                continue
            if planet_sign == sign_index:
                rows.append({
                    "planet": planet,
                    "sign": planet_sign,
                    "sign_name": self.SIGN_NAMES[planet_sign],
                    "house": self._house_from_sign(planet_sign),
                })
        return rows

    def _aspect_rows_to_sign(self, target_sign: int) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        planets = self.chart_data.get("planets") or {}
        for planet in self.CLASSICAL_PLANETS:
            data = planets.get(planet)
            if not isinstance(data, dict):
                continue
            try:
                from_sign = self._get_planet_sign_index(planet)
            except ValueError:
                continue
            if from_sign == target_sign:
                continue
            hits = [
                aspect_number
                for aspect_number in self.ASPECT_HOUSES[planet]
                if (from_sign + aspect_number - 1) % 12 == target_sign
            ]
            if hits:
                rows.append({
                    "planet": planet,
                    "from_sign": from_sign,
                    "from_sign_name": self.SIGN_NAMES[from_sign],
                    "from_house": self._house_from_sign(from_sign),
                    "aspect_numbers": hits,
                })
        return rows

    def _nakshatra_for_longitude(self, longitude: Any) -> Dict[str, Any]:
        try:
            normalized = float(longitude) % 360.0
        except (TypeError, ValueError):
            return {"available": False}
        span = 360.0 / 27.0
        index = min(26, int(normalized // span))
        within = normalized - (index * span)
        pada = min(4, int(within // (span / 4.0)) + 1)
        return {
            "available": True,
            "name": self.NAKSHATRA_NAMES[index],
            "lord": self.NAKSHATRA_LORDS[index % 9],
            "pada": pada,
        }

    def _planet_analysis(self, planet: str) -> Dict[str, Any]:
        data = (self.chart_data.get("planets") or {}).get(planet)
        if not isinstance(data, dict):
            return {"available": False, "planet": planet}
        sign_index = self._get_planet_sign_index(planet)
        dispositor = self.SIGN_LORDS[sign_index]
        supplied_strength = data.get("strength_analysis") or data.get("shadbala")
        return {
            "available": True,
            "planet": planet,
            "sign": sign_index,
            "sign_name": self.SIGN_NAMES[sign_index],
            "house": self._house_from_sign(sign_index),
            "dignity": self.get_planet_dignity(planet, sign_index),
            "strength_analysis": (
                {"available": True, "evidence": supplied_strength}
                if supplied_strength
                else {
                    "available": False,
                    "reason": "Shadbala requires the separate birth-data strength capability",
                }
            ),
            "dispositor": dispositor,
            "retrograde": bool(data.get("retrograde", False)),
            "combust": bool(data.get("combust", data.get("is_combust", False))),
            "nakshatra": self._nakshatra_for_longitude(data.get("longitude")),
            "lordships": [
                house
                for house in range(1, 13)
                if self.SIGN_LORDS[(self._get_ascendant_sign_index() + house - 1) % 12] == planet
            ],
        }

    def _relative_house_analysis(self, indu_sign: int, relative_house: int) -> Dict[str, Any]:
        sign_index = (indu_sign + relative_house - 1) % 12
        ruler = self.SIGN_LORDS[sign_index]
        aspect_rows = self._aspect_rows_to_sign(sign_index)
        return {
            "relative_house": relative_house,
            "sign": sign_index,
            "sign_name": self.SIGN_NAMES[sign_index],
            "natal_house": self._house_from_sign(sign_index),
            "ruler": ruler,
            "ruler_analysis": self._planet_analysis(ruler),
            "occupying_planets": [row["planet"] for row in self._planet_rows_in_sign(sign_index)],
            "aspecting_planets": [row["planet"] for row in aspect_rows],
            "aspect_details": aspect_rows,
        }

    def get_indu_lagna_analysis(self) -> Dict[str, Any]:
        """Return structured Indu Lagna evidence for Wealth graph synthesis."""
        details = self._calculation_details()
        indu_sign = int(details["indu_lagna_sign"])
        ruler = self.SIGN_LORDS[indu_sign]
        occupants = self._planet_rows_in_sign(indu_sign)
        aspects = self._aspect_rows_to_sign(indu_sign)
        indu = {
            "available": True,
            "precision": "sign_only",
            "sign": indu_sign,
            "sign_name": self.SIGN_NAMES[indu_sign],
            "house_number": self._house_from_sign(indu_sign),
            "ruler": ruler,
            "ruler_analysis": self._planet_analysis(ruler),
            "occupying_planets": [row["planet"] for row in occupants],
            "occupant_details": occupants,
            "aspecting_planets": [row["planet"] for row in aspects],
            "aspect_details": aspects,
            "second_from_indu": self._relative_house_analysis(indu_sign, 2),
            "eleventh_from_indu": self._relative_house_analysis(indu_sign, 11),
            "calculation": details,
            "interpretation_policy": {
                "role": "prosperity manifestation support",
                "requires_d1_d2_synthesis": True,
                "requires_separate_lord_strength_evidence": True,
                "cannot_override_natal_promise": True,
                "cannot_independently_time_event": True,
                "node_aspects": "occupation/conjunction and seventh aspect only; no fifth/ninth node aspects",
            },
        }
        return {"special_lagnas": {"indu_lagna": indu}}
