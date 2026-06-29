from typing import Any, Dict, Optional

from .base_calculator import BaseCalculator


class MudakkuCalculator(BaseCalculator):
    """
    Mudakku / Modakku calculator based on the Tamil Siddhar-style rule:

    1. Find the Sun's nakshatra.
    2. Count forward from the Sun's nakshatra up to Mula, counting both ends.
    3. Take that count and count forward again from Purvashada.
    4. The landing nakshatra is the Mudakku Nakshatra.
    5. If the landing nakshatra spans two signs, use the first part / first pada
       as the base Mudakku Rashi.
    """

    NAKSHATRA_NAMES = [
        "Ashwini",
        "Bharani",
        "Krittika",
        "Rohini",
        "Mrigashira",
        "Ardra",
        "Punarvasu",
        "Pushya",
        "Ashlesha",
        "Magha",
        "Purva Phalguni",
        "Uttara Phalguni",
        "Hasta",
        "Chitra",
        "Swati",
        "Vishakha",
        "Anuradha",
        "Jyeshtha",
        "Mula",
        "Purva Ashadha",
        "Uttara Ashadha",
        "Shravana",
        "Dhanishta",
        "Shatabhisha",
        "Purva Bhadrapada",
        "Uttara Bhadrapada",
        "Revati",
    ]

    # Standard nakshatra lord sequence.
    NAKSHATRA_LORDS = [
        "Ketu",
        "Venus",
        "Sun",
        "Moon",
        "Mars",
        "Rahu",
        "Jupiter",
        "Saturn",
        "Mercury",
        "Ketu",
        "Venus",
        "Sun",
        "Moon",
        "Mars",
        "Rahu",
        "Jupiter",
        "Saturn",
        "Mercury",
        "Ketu",
        "Venus",
        "Sun",
        "Moon",
        "Mars",
        "Rahu",
        "Jupiter",
        "Saturn",
        "Mercury",
    ]

    # Start sign for each nakshatra. For split nakshatras, the first pada belongs to
    # the first sign below, which is what we use as the base Mudakku Rashi.
    # Index is 0-based nakshatra index; value is 0-based zodiac sign index.
    NAKSHATRA_BASE_SIGNS = [
        0,  # Ashwini -> Aries
        0,  # Bharani -> Aries
        0,  # Krittika -> Aries first part (first pada) [split]
        1,  # Rohini -> Taurus
        1,  # Mrigashira -> Taurus first part (first pada) [split]
        2,  # Ardra -> Gemini
        2,  # Punarvasu -> Gemini
        3,  # Pushya -> Cancer
        3,  # Ashlesha -> Cancer
        4,  # Magha -> Leo
        4,  # Purva Phalguni -> Leo
        5,  # Uttara Phalguni -> Virgo first part (first pada) [split]
        5,  # Hasta -> Virgo
        6,  # Chitra -> Libra first part (first pada) [split]
        6,  # Swati -> Libra
        7,  # Vishakha -> Scorpio first part (first pada) [split]
        7,  # Anuradha -> Scorpio
        8,  # Jyeshtha -> Sagittarius
        8,  # Mula -> Sagittarius
        8,  # Purva Ashadha -> Sagittarius
        9,  # Uttara Ashadha -> Capricorn first part (first pada) [split]
        9,  # Shravana -> Capricorn
        10, # Dhanishta -> Aquarius first part (first pada) [split]
        10, # Shatabhisha -> Aquarius
        11, # Purva Bhadrapada -> Pisces first part (first pada) [split]
        11, # Uttara Bhadrapada -> Pisces
        11, # Revati -> Pisces
    ]

    MULA_INDEX = 18  # 0-based index for Mula
    PURVASHADA_INDEX = 19  # 0-based index for Purvashada

    SPLIT_NAKSHATRAS = {
        "Krittika",
        "Mrigashira",
        "Uttara Phalguni",
        "Chitra",
        "Vishakha",
        "Uttara Ashadha",
        "Dhanishta",
        "Purva Bhadrapada",
    }

    def __init__(self, chart_data: Optional[Dict[str, Any]] = None):
        super().__init__(chart_data or {})

    @classmethod
    def _normalize_index(cls, index: int) -> int:
        return index % 27

    @classmethod
    def _get_nakshatra_index_from_longitude(cls, longitude: float) -> Dict[str, Any]:
        span = 360.0 / 27.0
        idx = int((longitude % 360.0) / span)
        idx = min(max(idx, 0), 26)
        degree_in_nakshatra = (longitude % 360.0) % span
        pada = int(degree_in_nakshatra / (span / 4.0)) + 1
        if pada > 4:
            pada = 4
        return {
            "index": idx,
            "name": cls.NAKSHATRA_NAMES[idx],
            "lord": cls.NAKSHATRA_LORDS[idx],
            "degree_in_nakshatra": round(degree_in_nakshatra, 4),
            "pada": pada,
        }

    @classmethod
    def _count_inclusive(cls, start_index: int, end_index: int) -> int:
        """Count nakshatras inclusive from start to end in the 27-nakshatra cycle."""
        return ((end_index - start_index) % 27) + 1

    @classmethod
    def _count_forward_from(cls, start_index: int, steps: int) -> int:
        """
        Move forward by an inclusive count where the starting point is counted as 1.
        Example: start at Purvashada and steps=1 returns Purvashada.
        """
        return cls._normalize_index(start_index + steps - 1)

    def _get_sun_nakshatra(self, chart_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = chart_data or self.chart_data or {}
        planets = data.get("planets", {}) or {}
        sun = planets.get("Sun") or {}
        longitude = sun.get("longitude")

        if longitude is None:
            raise ValueError("Sun longitude is required to calculate Mudakku Nakshatra")

        return self._get_nakshatra_index_from_longitude(float(longitude))

    def calculate(self, chart_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate Mudakku / Modakku values for a chart.
        Returns the Sun nakshatra, the count to Mula, and the derived Mudakku Nakshatra.
        """
        data = chart_data or self.chart_data or {}
        sun_nak = self._get_sun_nakshatra(data)

        count_to_mula = self._count_inclusive(sun_nak["index"], self.MULA_INDEX)
        mudakku_index = self._count_forward_from(self.PURVASHADA_INDEX, count_to_mula)
        mudakku_nak = self._get_nakshatra_index_from_longitude(mudakku_index * (360.0 / 27.0))

        mudakku_rashi = self.get_sign_name(self.NAKSHATRA_BASE_SIGNS[mudakku_index])
        mudakku_lord = self.get_sign_lord(self.NAKSHATRA_BASE_SIGNS[mudakku_index])
        is_split = mudakku_nak["name"] in self.SPLIT_NAKSHATRAS
        mudakku_sign_index = self.NAKSHATRA_BASE_SIGNS[mudakku_index]
        mudakku_mid_longitude = mudakku_sign_index * 30.0 + 15.0
        mudakku_degree_in_sign = 15.0

        return {
            "sun_nakshatra": sun_nak,
            "count_to_mula": count_to_mula,
            "mudakku_nakshatra": {
                "index": mudakku_nak["index"] + 1,
                "name": mudakku_nak["name"],
                "lord": mudakku_nak["lord"],
                "pada": mudakku_nak["pada"],
                "degree_in_nakshatra": mudakku_nak["degree_in_nakshatra"],
            },
            "mudakku_point": {
                "longitude": round(mudakku_mid_longitude, 6),
                "sign": mudakku_sign_index,
                "degree": round(mudakku_degree_in_sign, 6),
                "sign_name": mudakku_rashi,
                "nakshatra": mudakku_nak["name"],
            },
            "mudakku_rashi": mudakku_rashi,
            "mudakku_rashi_lord": mudakku_lord,
            "is_split_nakshatra": is_split,
            "method": {
                "count_from": sun_nak["name"],
                "count_to": "Mula",
                "restart_from": "Purvashada",
                "special_rashi_rule": "Use first pada / first sign when the landing nakshatra spans two signs.",
            },
        }

    def get_mudakku_summary(self, chart_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a compact summary for chat or UI display."""
        result = self.calculate(chart_data)
        return {
            "mudakku_nakshatra": result["mudakku_nakshatra"]["name"],
            "mudakku_rashi": result["mudakku_rashi"],
            "mudakku_rashi_lord": result["mudakku_rashi_lord"],
            "mudakku_point": result["mudakku_point"],
            "sun_nakshatra": result["sun_nakshatra"]["name"],
            "count_to_mula": result["count_to_mula"],
            "is_split_nakshatra": result["is_split_nakshatra"],
        }
