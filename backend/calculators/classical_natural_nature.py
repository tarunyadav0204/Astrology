"""Chart-dependent natural nature of planets used by Parashari clients.

Functional nature is a separate Lagna/lordship judgment.  This module handles
the contextual natural status of the Moon and Mercury so clients do not label
the Moon benefic without first checking Paksha.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


NATURAL_BENEFICS = frozenset({"Jupiter", "Venus"})
NATURAL_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})


def _planet(chart: Dict[str, Any], name: str) -> Dict[str, Any]:
    row = ((chart or {}).get("planets") or {}).get(name) or {}
    return row if isinstance(row, dict) else {}


def _longitude(chart: Dict[str, Any], name: str) -> Optional[float]:
    try:
        return float(_planet(chart, name).get("longitude")) % 360.0
    except (TypeError, ValueError):
        return None


def _house(chart: Dict[str, Any], name: str) -> Optional[int]:
    try:
        return int(_planet(chart, name).get("house"))
    except (TypeError, ValueError):
        return None


def moon_natural_nature(chart: Dict[str, Any]) -> Dict[str, Any]:
    sun = _longitude(chart, "Sun")
    moon = _longitude(chart, "Moon")
    if sun is None or moon is None:
        return {
            "nature": "variable",
            "phase": "unknown",
            "paksha": None,
            "elongation": None,
            "reason": "Sun–Moon elongation is unavailable, so the Moon is not forced into a benefic or malefic label.",
        }
    elongation = (moon - sun) % 360.0
    waxing = 0.0 < elongation <= 180.0
    return {
        "nature": "benefic" if waxing else "malefic",
        "phase": "waxing" if waxing else "waning_or_dark",
        "paksha": "shukla" if waxing else "krishna",
        "elongation": round(elongation, 4),
        "reason": (
            "Waxing Moon (Shukla Paksha) is treated as a natural benefic."
            if waxing else
            "Waning or dark Moon (Krishna Paksha/Amavasya boundary) is treated as a natural malefic."
        ),
    }


def _co_occupants(chart: Dict[str, Any], planet: str) -> Iterable[str]:
    house = _house(chart, planet)
    if house is None:
        return ()
    return tuple(
        str(name) for name, row in ((chart or {}).get("planets") or {}).items()
        if name != planet and isinstance(row, dict) and _house(chart, str(name)) == house
    )


def calculate_natural_nature(chart: Dict[str, Any], planet: str) -> Dict[str, Any]:
    planet = str(planet)
    if planet == "Moon":
        return {"planet": planet, "applicable": True, **moon_natural_nature(chart)}
    if planet == "Mercury":
        associates = tuple(sorted(_co_occupants(chart, planet)))
        benefic_associates = []
        malefic_associates = []
        for associate in associates:
            nature = calculate_natural_nature(chart, associate).get("nature")
            if nature == "benefic":
                benefic_associates.append(associate)
            elif nature == "malefic":
                malefic_associates.append(associate)
        if malefic_associates and not benefic_associates:
            nature = "malefic"
        elif malefic_associates and benefic_associates:
            nature = "mixed"
        else:
            nature = "benefic"
        return {
            "planet": planet,
            "applicable": True,
            "nature": nature,
            "phase": None,
            "paksha": None,
            "elongation": None,
            "associates": list(associates),
            "benefic_associates": benefic_associates,
            "malefic_associates": malefic_associates,
            "reason": "Mercury is naturally benefic when unafflicted and is conditioned by planets joined with it.",
        }
    if planet in NATURAL_BENEFICS:
        nature = "benefic"
    elif planet in NATURAL_MALEFICS:
        nature = "malefic"
    else:
        nature = "neutral"
    return {
        "planet": planet,
        "applicable": planet in NATURAL_BENEFICS or planet in NATURAL_MALEFICS,
        "nature": nature,
        "phase": None,
        "paksha": None,
        "elongation": None,
        "reason": "Standard natural planetary nature.",
    }
