"""
Canonical Parāśara-style graha drishti (whole sign). Single source of truth for:
- natal aspect lists (AspectCalculator)
- transit aspect numbers (RealTransitCalculator)
- chart API payload (graha_drishti_by_house)

House numbers are 1–12 *from the planet*: 1 = same sign as planet (conjunction);
7 = 7th sign from planet; etc. Occupants of the target sign are excluded from
\"aspecting\" lists because they are not casting drishti from another sign.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

# Same structure historically used in RealTransitCalculator.vedic_aspects
GRAHA_HOUSE_ASPECTS: Dict[str, List[int]] = {
    "Sun": [1, 7],
    "Moon": [1, 7],
    "Mars": [1, 4, 7, 8],
    "Mercury": [1, 7],
    "Jupiter": [1, 5, 7, 9],
    "Venus": [1, 7],
    "Saturn": [1, 3, 7, 10],
    "Rahu": [1, 5, 7, 9],
    "Ketu": [1, 5, 7, 9],
}

DEFAULT_ASPECTS = [1, 7]

PLANET_ORDER = [
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Rahu",
    "Ketu",
    "Uranus",
    "Neptune",
    "Pluto",
    "Gulika",
    "Mandi",
    "InduLagna",
]


def get_aspect_houses_for_planet(planet_name: str) -> List[int]:
    return list(GRAHA_HOUSE_ASPECTS.get(planet_name, DEFAULT_ASPECTS))


def _nth_house_label(n: int) -> str:
    if n == 1:
        return "1st"
    if n == 2:
        return "2nd"
    if n == 3:
        return "3rd"
    return f"{n}th"


def _aspect_labels(aspect_houses: List[int]) -> str:
    return ", ".join(_nth_house_label(n) for n in sorted(set(aspect_houses)))


def house_number_for_sign(chart_data: Dict[str, Any], sign_index: int) -> Optional[int]:
    houses = chart_data.get("houses") or []
    for i, h in enumerate(houses):
        if isinstance(h, dict) and h.get("sign") == sign_index:
            return i + 1
    return None


def _iter_planet_names(planets: Dict[str, Any]):
    seen: Set[str] = set()
    for name in PLANET_ORDER:
        if name in planets:
            seen.add(name)
            yield name
    for name in planets:
        if name in seen or name in ("ascendant_longitude",):
            continue
        yield name


def _planet_sort_key(name: str):
    try:
        return (0, PLANET_ORDER.index(name))
    except ValueError:
        return (1, name)


def planets_aspecting_house_sign(planets: Dict[str, Any], target_sign: int) -> List[str]:
    """
    Planets whose drishti falls on target_sign (whole sign), excluding planets
    located in target_sign (occupants).
    """
    found: List[str] = []
    for planet_name in _iter_planet_names(planets):
        data = planets.get(planet_name)
        if not isinstance(data, dict) or not isinstance(data.get("sign"), int):
            continue
        p_sign = data["sign"]
        if p_sign == target_sign:
            continue
        for n in get_aspect_houses_for_planet(planet_name):
            if (p_sign + n - 1) % 12 == target_sign:
                found.append(planet_name)
                break
    return sorted(set(found), key=_planet_sort_key)


def compute_graha_drishti_by_house(chart_data: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
    """For each house number 1–12, list planets aspecting that house's sign from other signs."""
    planets = chart_data.get("planets") or {}
    houses = chart_data.get("houses") or []
    if len(houses) < 12:
        return {}

    out: Dict[int, List[Dict[str, Any]]] = {}
    for h in range(1, 13):
        target_sign = houses[h - 1].get("sign")
        if not isinstance(target_sign, int):
            out[h] = []
            continue
        rows: List[Dict[str, Any]] = []
        for planet_name in _iter_planet_names(planets):
            data = planets.get(planet_name)
            if not isinstance(data, dict) or not isinstance(data.get("sign"), int):
                continue
            p_sign = data["sign"]
            if p_sign == target_sign:
                continue
            hits = [
                n
                for n in get_aspect_houses_for_planet(planet_name)
                if (p_sign + n - 1) % 12 == target_sign
            ]
            if not hits:
                continue
            uniq = sorted(set(hits))
            ph = house_number_for_sign(chart_data, p_sign)
            rows.append(
                {
                    "planet": planet_name,
                    "planet_house": ph,
                    "aspect_from_planet": uniq,
                    "aspect_labels": _aspect_labels(uniq),
                }
            )
        rows.sort(key=lambda r: (_planet_sort_key(r["planet"]), r["planet"]))
        out[h] = rows
    return out


def attach_graha_drishti_to_chart(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mutates chart_data: adds top-level graha_drishti_by_house and each houses[i].graha_drishti.
    Safe to call only when planets and houses are fully populated.
    """
    by_h = compute_graha_drishti_by_house(chart_data)
    chart_data["graha_drishti_by_house"] = {str(k): v for k, v in by_h.items()}
    houses = chart_data.get("houses") or []
    for i in range(min(12, len(houses))):
        if isinstance(houses[i], dict):
            houses[i]["graha_drishti"] = by_h.get(i + 1, [])
    return chart_data
