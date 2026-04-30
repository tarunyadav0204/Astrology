"""Astrology helpers for deterministic kundli matching."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .constants import (
    BENEFICS,
    MALEFICS,
    NAKSHATRA_NAMES,
    PLANET_DEBILITATION_SIGNS,
    PLANET_EXALTATION_SIGNS,
    PLANET_FRIENDSHIPS,
    PLANET_OWN_SIGNS,
    SIGN_ELEMENTS,
    SIGN_LORDS,
    SIGN_NAMES,
)

NAKSHATRA_SIZE = 360.0 / 27.0
PADA_SIZE = NAKSHATRA_SIZE / 4.0


def normalize_sign(sign_value: Any) -> Optional[int]:
    if sign_value is None:
        return None
    if isinstance(sign_value, str):
        if sign_value in SIGN_NAMES:
            return SIGN_NAMES.index(sign_value) + 1
        try:
            sign_value = int(sign_value)
        except ValueError:
            return None
    sign_num = int(sign_value)
    if 0 <= sign_num <= 11:
        return sign_num + 1
    if 1 <= sign_num <= 12:
        return sign_num
    return None


def sign_name(sign_num: Optional[int]) -> Optional[str]:
    if sign_num is None or sign_num < 1 or sign_num > 12:
        return None
    return SIGN_NAMES[sign_num - 1]


def get_planet(chart: Dict[str, Any], planet: str) -> Dict[str, Any]:
    return chart.get("planets", {}).get(planet, {}) or {}


def get_longitude(chart: Dict[str, Any], planet: str) -> Optional[float]:
    data = get_planet(chart, planet)
    longitude = data.get("longitude")
    return float(longitude) if longitude is not None else None


def moon_profile_from_longitude(longitude: float) -> Dict[str, Any]:
    normalized = longitude % 360.0
    sign_num = int(normalized / 30.0) + 1
    nak_num = int(normalized / NAKSHATRA_SIZE) + 1
    offset_in_nak = normalized % NAKSHATRA_SIZE
    pada = int(offset_in_nak / PADA_SIZE) + 1
    return {
        "longitude": round(normalized, 6),
        "sign": sign_num,
        "sign_name": sign_name(sign_num),
        "nakshatra_number": nak_num,
        "nakshatra_name": NAKSHATRA_NAMES[nak_num - 1],
        "pada": pada,
    }


def get_moon_profile(chart: Dict[str, Any]) -> Dict[str, Any]:
    longitude = get_longitude(chart, "Moon")
    if longitude is None:
        return {
            "longitude": None,
            "sign": None,
            "sign_name": None,
            "nakshatra_number": None,
            "nakshatra_name": None,
            "pada": None,
        }
    return moon_profile_from_longitude(longitude)


def house_from_reference(reference_sign: int, target_sign: int) -> int:
    return ((target_sign - reference_sign) % 12) + 1


def get_house_from_chart(chart: Dict[str, Any], planet: str) -> Optional[int]:
    data = get_planet(chart, planet)
    house = data.get("house")
    if house is not None:
        return int(house)
    sign_num = normalize_sign(data.get("sign"))
    asc_sign = ascendant_sign(chart)
    if sign_num is None or asc_sign is None:
        return None
    return house_from_reference(asc_sign, sign_num)


def ascendant_sign(chart: Dict[str, Any]) -> Optional[int]:
    asc = chart.get("ascendant")
    if asc is None:
        return None
    return int((float(asc) % 360.0) / 30.0) + 1


def planet_sign(chart: Dict[str, Any], planet: str) -> Optional[int]:
    data = get_planet(chart, planet)
    sign_num = normalize_sign(data.get("sign"))
    if sign_num is not None:
        return sign_num
    longitude = data.get("longitude")
    if longitude is None:
        return None
    return int((float(longitude) % 360.0) / 30.0) + 1


def planet_dignity(planet: str, sign_num: Optional[int]) -> str:
    if sign_num is None:
        return "Unknown"
    if PLANET_EXALTATION_SIGNS.get(planet) == sign_num:
        return "Exalted"
    if PLANET_DEBILITATION_SIGNS.get(planet) == sign_num:
        return "Debilitated"
    if sign_num in PLANET_OWN_SIGNS.get(planet, set()):
        return "Own"
    lord = SIGN_LORDS.get(sign_num)
    if lord is None:
        return "Neutral"
    if lord in PLANET_FRIENDSHIPS.get(planet, {}).get("friends", set()):
        return "Friendly"
    if lord in PLANET_FRIENDSHIPS.get(planet, {}).get("enemies", set()):
        return "Enemy"
    return "Neutral"


def dignity_score(dignity: str) -> int:
    mapping = {
        "Exalted": 4,
        "Own": 3,
        "Friendly": 2,
        "Neutral": 1,
        "Enemy": -1,
        "Debilitated": -3,
        "Unknown": 0,
    }
    return mapping.get(dignity, 0)


def planets_in_house(chart: Dict[str, Any], house_number: int, allowed: Optional[Iterable[str]] = None) -> List[str]:
    names = allowed if allowed is not None else chart.get("planets", {}).keys()
    return [
        name for name in names
        if get_house_from_chart(chart, name) == house_number
    ]


def aspect_targets(planet: str, house_num: Optional[int]) -> List[int]:
    if house_num is None:
        return []
    targets = [((house_num + 5) % 12) + 1]
    if planet == "Mars":
        targets.extend([((house_num + 2) % 12) + 1, ((house_num + 6) % 12) + 1])
    elif planet == "Jupiter":
        targets.extend([((house_num + 3) % 12) + 1, ((house_num + 7) % 12) + 1])
    elif planet == "Saturn":
        targets.extend([((house_num + 1) % 12) + 1, ((house_num + 8) % 12) + 1])
    return sorted(set(targets))


def aspects_house(chart: Dict[str, Any], house_number: int, allowed: Optional[Iterable[str]] = None) -> List[str]:
    names = allowed if allowed is not None else chart.get("planets", {}).keys()
    aspected = []
    for name in names:
        source_house = get_house_from_chart(chart, name)
        if house_number in aspect_targets(name, source_house):
            aspected.append(name)
    return aspected


def reference_house_from_planet(chart: Dict[str, Any], reference_planet: str, target_planet: str) -> Optional[int]:
    reference_sign = planet_sign(chart, reference_planet)
    target_sign = planet_sign(chart, target_planet)
    if reference_sign is None or target_sign is None:
        return None
    return house_from_reference(reference_sign, target_sign)


def score_to_band(score: float, thresholds: List[float], labels: List[str]) -> str:
    for threshold, label in zip(thresholds, labels):
        if score >= threshold:
            return label
    return labels[-1]


def grade_from_percentage(percentage: float) -> str:
    return score_to_band(
        percentage,
        [85.0, 70.0, 55.0, 40.0],
        ["Excellent", "Good", "Average", "Delicate", "Challenging"],
    )


def element_compatibility(sign_a: Optional[int], sign_b: Optional[int]) -> Dict[str, Any]:
    if sign_a is None or sign_b is None:
        return {"score": 50, "relationship": "Unknown"}
    elem_a = SIGN_ELEMENTS[sign_a]
    elem_b = SIGN_ELEMENTS[sign_b]
    if elem_a == elem_b:
        return {"score": 90, "relationship": "Same element"}
    if {elem_a, elem_b} in [{"Fire", "Air"}, {"Earth", "Water"}]:
        return {"score": 75, "relationship": "Complementary elements"}
    return {"score": 45, "relationship": "Cross-element tension"}


def natural_planet_quality(planet: str) -> str:
    if planet in BENEFICS:
        return "benefic"
    if planet in MALEFICS:
        return "malefic"
    return "neutral"
