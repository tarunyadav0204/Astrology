"""Public, birth-data-free snapshot of the current Lahiri sidereal sky."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import swisseph as swe


RASHI_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

NAKSHATRA_NAMES = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

PLANET_SPECS = (
    ("Sun", "SU", swe.SUN),
    ("Moon", "MO", swe.MOON),
    ("Mars", "MA", swe.MARS),
    ("Mercury", "ME", swe.MERCURY),
    ("Jupiter", "JU", swe.JUPITER),
    ("Venus", "VE", swe.VENUS),
    ("Saturn", "SA", swe.SATURN),
    ("Rahu", "RA", swe.MEAN_NODE),
)

NAKSHATRA_SPAN = 360.0 / 27.0
PADA_SPAN = NAKSHATRA_SPAN / 4.0


def _normalize_utc(moment: Optional[datetime]) -> datetime:
    value = moment or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _planet_payload(name: str, code: str, longitude: float, speed: float) -> Dict[str, Any]:
    normalized = longitude % 360.0
    rashi_index = int(normalized // 30.0)
    degree_in_rashi = normalized % 30.0
    nakshatra_index = min(26, int(normalized // NAKSHATRA_SPAN))
    degree_in_nakshatra = normalized % NAKSHATRA_SPAN
    pada = min(4, int(degree_in_nakshatra // PADA_SPAN) + 1)

    return {
        "name": name,
        "code": code,
        "longitude": round(normalized, 6),
        "rashi_index": rashi_index,
        "rashi": RASHI_NAMES[rashi_index],
        "degree_in_rashi": round(degree_in_rashi, 6),
        "nakshatra_index": nakshatra_index,
        "nakshatra": NAKSHATRA_NAMES[nakshatra_index],
        "pada": pada,
        "retrograde": speed < 0,
    }


def calculate_current_sky(moment: Optional[datetime] = None) -> Dict[str, Any]:
    """Calculate geocentric sidereal positions for the supplied UTC instant."""
    calculated_at = _normalize_utc(moment)
    utc_hour = (
        calculated_at.hour
        + calculated_at.minute / 60.0
        + (calculated_at.second + calculated_at.microsecond / 1_000_000.0) / 3600.0
    )
    julian_day = swe.julday(
        calculated_at.year,
        calculated_at.month,
        calculated_at.day,
        utc_hour,
    )

    # Swiss Ephemeris keeps the sidereal mode globally; set it immediately before
    # this uninterrupted calculation so public results cannot inherit a KP mode.
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH

    planets = []
    rahu_longitude = None
    rahu_speed = None
    for name, code, planet_id in PLANET_SPECS:
        position = swe.calc_ut(julian_day, planet_id, flags)[0]
        longitude = float(position[0])
        speed = float(position[3]) if len(position) > 3 else 0.0
        planets.append(_planet_payload(name, code, longitude, speed))
        if name == "Rahu":
            rahu_longitude = longitude
            rahu_speed = speed

    # Ketu is exactly opposite the mean lunar node and shares its retrograde motion.
    planets.append(_planet_payload("Ketu", "KE", (rahu_longitude or 0.0) + 180.0, rahu_speed or -1.0))

    return {
        "calculated_at": calculated_at.isoformat().replace("+00:00", "Z"),
        "coordinate_system": "sidereal",
        "ayanamsha": {
            "name": "Lahiri",
            "degrees": round(float(swe.get_ayanamsa_ut(julian_day)), 6),
        },
        "rashis": list(RASHI_NAMES),
        "nakshatras": list(NAKSHATRA_NAMES),
        "planets": planets,
    }
