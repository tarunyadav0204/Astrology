from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

from .primitives import aspected_houses, ruled_houses


NAKSHATRA_TRANSIT_VERSION = "1.0.0"
NAKSHATRA_SPAN = 40.0 / 3.0
PADA_SPAN = 10.0 / 3.0

NAKSHATRA_LORD_SEQUENCE = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
)
NAKSHATRA_NAMES = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
)


def nakshatra_position(longitude: float) -> Dict[str, Any]:
    """Return the deterministic Lahiri-longitude nakshatra subdivision."""

    normalized = float(longitude) % 360.0
    index = min(26, int(normalized / NAKSHATRA_SPAN))
    position = normalized - (index * NAKSHATRA_SPAN)
    return {
        "index": index,
        "number": index + 1,
        "name": NAKSHATRA_NAMES[index],
        "lord": NAKSHATRA_LORD_SEQUENCE[index % 9],
        "pada": min(4, int(position / PADA_SPAN) + 1),
        "degrees_in_nakshatra": round(position, 6),
    }


def nakshatra_transit_relation(
    natal_longitude: float,
    transit_longitude: float,
) -> Optional[Dict[str, Any]]:
    """Classify exact-star return separately from same-lord resonance.

    A different nakshatra of the same lord repeats the natal star dispositor,
    but it is deliberately not called a nakshatra return or positional contact.
    """

    natal = nakshatra_position(natal_longitude)
    transit = nakshatra_position(transit_longitude)
    if natal["index"] == transit["index"]:
        relation = "exact_natal_nakshatra_return"
        strength = "strong_confirmation"
    elif natal["lord"] == transit["lord"]:
        relation = "nakshatra_dispositor_resonance"
        strength = "secondary_confirmation"
    else:
        return None
    return {
        "relation": relation,
        "strength": strength,
        "natal_nakshatra": natal,
        "transit_nakshatra": transit,
        "common_nakshatra_lord": natal["lord"],
    }


def nakshatra_lord_house_relevance(
    chart: Dict[str, Any],
    lord: str,
    house: int,
    active_dasha_planets: Iterable[str],
) -> Tuple[bool, Tuple[str, ...]]:
    natal = chart["planets"].get(lord)
    if natal is None:
        return False, ()
    reasons = []
    if lord in set(active_dasha_planets):
        reasons.append("nakshatra_lord_in_active_dasha_chain")
    if house in ruled_houses(chart, lord):
        reasons.append("nakshatra_lord_rules_event_house")
    if int(natal["house"]) == house:
        reasons.append("nakshatra_lord_occupies_event_house")
    if house in aspected_houses(lord, int(natal["house"])):
        reasons.append("nakshatra_lord_aspects_event_house")
    return bool(reasons), tuple(reasons)


def nakshatra_lord_natal_condition(
    chart: Dict[str, Any],
    natal_dignities: Dict[str, Any],
    lord: str,
) -> Dict[str, Any]:
    natal = chart["planets"].get(lord, {})
    condition = natal_dignities.get(lord, {})
    return {
        "natal_house": natal.get("house"),
        "natal_sign": natal.get("sign"),
        "dignity": condition.get("dignity", "neutral"),
        "combustion_status": condition.get("combustion_status", "normal"),
        "retrograde": condition.get("retrograde", natal.get("retrograde", False)),
    }


def nakshatra_lord_expression(condition: Dict[str, Any]) -> str:
    dignity = str(condition.get("dignity") or "neutral")
    combustion = str(condition.get("combustion_status") or "normal")
    if dignity == "debilitated" or combustion not in {"normal", "cazimi"}:
        return "strained"
    if dignity in {"exalted", "moolatrikona", "own_sign"}:
        return "clear"
    return "qualified"
