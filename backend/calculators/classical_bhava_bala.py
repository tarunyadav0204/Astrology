"""Classical Parashari Bhava Bala (house strength).

The worksheet follows BPHS chapter 27, verses 26-31 and keeps every term in
virupas so it can be audited beside Parashara's Light:

    Bhava Bala = lord's Shadbala + Bhava Dig Bala + Bhava Drishti Bala
                 + occupation adjustment + day/twilight/night adjustment

This is intentionally separate from ``HouseStrengthCalculator``.  That class
is an application-specific weighted diagnostic and is not classical Bhava Bala.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from .base_calculator import BaseCalculator
from .classical_shadbala import (
    _birth_julian_days,
    _functional_benefics_and_malefics,
    _sunrise_sunset_for_birth,
    calculate_classical_shadbala,
    get_aspect_value,
)


SIGN_LORDS = BaseCalculator.SIGN_LORDS
SIGN_NAMES = BaseCalculator.SIGN_NAMES

# BPHS 27.26-28: the listed reference Bhava is the zero point.  The shortest
# distance from it, divided by three, gives 0..60 virupas.
REFERENCE_HOUSE_BY_FORM = {
    "biped": 7,
    "quadruped": 4,
    "insect": 1,
    "water": 10,
}

SEERSHODAYA_SIGNS = {2, 4, 5, 6, 7, 10}       # Gemini, Leo, Virgo, Libra, Scorpio, Aquarius
PRISHTODAYA_SIGNS = {0, 1, 3, 8, 9}            # Aries, Taurus, Cancer, Sagittarius, Capricorn
DUAL_SIGNS = {2, 5, 8, 11}                     # Gemini, Virgo, Sagittarius, Pisces


def _shortest_arc(first: float, second: float) -> float:
    distance = abs((float(first) - float(second)) % 360.0)
    return min(distance, 360.0 - distance)


def _sign_form(longitude: float) -> str:
    sign = int(float(longitude) % 360.0 // 30.0)
    degree = float(longitude) % 30.0
    if sign in {2, 5, 6, 10} or (sign == 8 and degree < 15.0):
        return "biped"
    if sign in {0, 1, 4} or (sign == 8 and degree >= 15.0) or (sign == 9 and degree < 15.0):
        return "quadruped"
    if sign in {3, 7}:
        return "insect"
    return "water"  # Pisces and the latter half of Capricorn


def calculate_bhava_dig_bala(bhava_longitude: float, bhava_madhyas: List[float]) -> Tuple[float, str, int]:
    """Return (virupas, sign-form, zero-reference house)."""
    form = _sign_form(bhava_longitude)
    reference_house = REFERENCE_HOUSE_BY_FORM[form]
    distance = _shortest_arc(bhava_longitude, bhava_madhyas[reference_house - 1])
    return round(distance / 3.0, 2), form, reference_house


def _occupants_for_house(
    bhava_sign: int,
    planets: Dict[str, Dict[str, Any]],
) -> List[str]:
    """PL/BPHS occupation adjustment uses planets in the Bhava's Rashi."""
    return [
        name for name, data in planets.items()
        if name in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        and int(float(data.get("longitude", 0.0)) % 360.0 // 30.0) == bhava_sign
    ]


def _bhava_drishti_details(
    target_longitude: float,
    planets: Dict[str, Dict[str, Any]],
) -> Tuple[float, List[Dict[str, Any]]]:
    benefics, malefics = _functional_benefics_and_malefics(planets)
    total = 0.0
    details: List[Dict[str, Any]] = []
    excluded = {"Rahu", "Ketu", "Gulika", "Mandi", "InduLagna", "Ascendant"}
    for planet, data in planets.items():
        if planet in excluded:
            continue
        aspect = get_aspect_value(planet, float(data.get("longitude", 0.0)), target_longitude)
        if aspect <= 0.0 or planet not in benefics | malefics:
            continue
        factor = 1.0 if planet in {"Mercury", "Jupiter"} else 0.25
        signed = aspect * factor * (-1.0 if planet in malefics else 1.0)
        total += signed
        details.append({
            "planet": planet,
            "aspect_virupas": round(aspect, 2),
            "classical_factor": factor,
            "nature": "malefic" if planet in malefics else "benefic",
            "contribution": round(signed, 2),
        })
    return round(total, 2), details


def _birth_phase(jd: float, birth_data: Dict[str, Any]) -> str:
    """Classify BPHS day/twilight/night; Sandhya is one ghati around rise/set.

    BPHS specifies the twilight rule but not its boundary in these verses.  One
    ghati (24 minutes) on either side of sunrise or sunset is retained explicitly
    as the worksheet convention rather than silently using modern civil twilight.
    """
    sunrise, sunset = _sunrise_sunset_for_birth(jd, birth_data)
    one_ghati = 1.0 / 60.0
    if abs(jd - sunrise) <= one_ghati or abs(jd - sunset) <= one_ghati:
        return "twilight"
    return "day" if sunrise < jd < sunset else "night"


def _time_sign_adjustment(sign: int, phase: str) -> float:
    if phase == "day" and sign in SEERSHODAYA_SIGNS:
        return 15.0
    if phase == "twilight" and sign in DUAL_SIGNS:
        return 15.0
    if phase == "night" and sign in PRISHTODAYA_SIGNS:
        return 15.0
    return 0.0


def _occupation_adjustment(occupants: Iterable[str]) -> Tuple[float, List[Dict[str, Any]]]:
    adjustments = {"Mercury": 60.0, "Jupiter": 60.0, "Sun": -60.0, "Mars": -60.0, "Saturn": -60.0}
    rows = [
        {"planet": planet, "virupas": adjustments[planet]}
        for planet in occupants if planet in adjustments
    ]
    return sum(row["virupas"] for row in rows), rows


def calculate_classical_bhava_bala(
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    shadbala: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Calculate the complete BPHS/Parashara's-Light-style 12-house worksheet."""
    jd, _local_jd, _offset = _birth_julian_days(birth_data)
    # Parashara's Light's detailed Bhava Bala table advances the Lagna sphuta
    # by exactly 30 degrees for each Bhava (the same degree repeats across all
    # twelve Rashis).  This is not its separate Sripati Bhava-chalit chart.
    lagna = float(chart_data.get("ascendant"))
    madhyas = [(lagna + index * 30.0) % 360.0 for index in range(12)]
    planets = chart_data.get("planets") or {}
    if not planets:
        raise ValueError("chart_data.planets is required for Bhava Bala")
    shadbala = shadbala or calculate_classical_shadbala(birth_data, chart_data)
    phase = _birth_phase(jd, birth_data)

    rows: Dict[str, Dict[str, Any]] = {}
    for house_number, madhya in enumerate(madhyas, start=1):
        sign = int(madhya % 360.0 // 30.0)
        lord = SIGN_LORDS[sign]
        lord_strength = float(shadbala[lord]["total_points"])
        dig_bala, sign_form, reference_house = calculate_bhava_dig_bala(madhya, madhyas)
        drishti_bala, drishti_details = _bhava_drishti_details(madhya, planets)
        occupants = _occupants_for_house(sign, planets)
        occupation_bala, occupation_details = _occupation_adjustment(occupants)
        day_night_bala = _time_sign_adjustment(sign, phase)
        total = lord_strength + dig_bala + drishti_bala + occupation_bala + day_night_bala
        rows[str(house_number)] = {
            "house": house_number,
            "sign": sign,
            "sign_name": SIGN_NAMES[sign],
            "degree": round(madhya % 30.0, 2),
            "longitude": round(madhya, 4),
            "lord": lord,
            "from_lord": round(lord_strength, 2),
            "dig_bala": dig_bala,
            "drishti_bala": drishti_bala,
            "planets_in_bala": round(occupation_bala, 2),
            "day_night_bala": round(day_night_bala, 2),
            "total_points": round(total, 2),
            "total_rupas": round(total / 60.0, 2),
            "occupants": occupants,
            "details": {
                "sign_form": sign_form,
                "dig_zero_reference_house": reference_house,
                "drishti": drishti_details,
                "occupation": occupation_details,
                "birth_phase": phase,
            },
        }

    ranked = sorted(rows.items(), key=lambda item: (-item[1]["total_points"], int(item[0])))
    for rank, (_house, row) in enumerate(ranked, start=1):
        row["relative_rank"] = rank
    return rows
