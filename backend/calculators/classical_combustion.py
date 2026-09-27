"""Canonical Parashari combustion (asta/astangata) calculation.

Primary basis
-------------
*Brihat Parashara Hora Shastra*, chapter 7, verses 28-29 describes loss
of rays as a planet approaches the Sun: full strength opposite the Sun and
loss at identical longitude, with proportional treatment in between.

The operational visibility limits below are printed in R. Santhanam,
*Brihat Parashara Hora Sastra*, Vol. I, 1984 ed., pp. 99-100, in the
translator's explanatory table immediately following verses 28-29.  The
table is cited as an edition note rather than misrepresented as a verse.

The same note expressly excludes Rahu and Ketu because they are mathematical
points.  No Western cazimi exception is introduced.
"""

from __future__ import annotations

from typing import Any, Mapping


CLASSICAL_COMBUSTION_LIMITS: dict[str, dict[str, float | None]] = {
    "Moon": {"direct": 12.0, "retrograde": None},
    "Mars": {"direct": 17.0, "retrograde": 8.0},
    "Mercury": {"direct": 14.0, "retrograde": 12.0},
    "Jupiter": {"direct": 11.0, "retrograde": 11.0},
    "Venus": {"direct": 10.0, "retrograde": 8.0},
    "Saturn": {"direct": 16.0, "retrograde": 16.0},
}

CLASSICAL_COMBUSTION_SOURCE = {
    "work": "Brihat Parashara Hora Shastra",
    "chapter": 7,
    "verses": "28-29",
    "edition": "R. Santhanam, Vol. I, 1984",
    "pages": "99-100",
    "table_note": (
        "The degree limits and direct/retrograde columns are the translator's "
        "explanatory table following verses 28-29; they are not presented as "
        "part of the Sanskrit verse text."
    ),
}


def angular_distance(first: float, second: float) -> float:
    """Return the shortest zodiacal separation in the closed range 0..180."""
    distance = abs((float(first) % 360.0) - (float(second) % 360.0))
    return 360.0 - distance if distance > 180.0 else distance


def _not_applicable(planet: str, reason: str) -> dict[str, Any]:
    return {
        "planet": planet,
        "applicable": False,
        "is_combust": False,
        "status": "not_applicable",
        "motion": "not_applicable",
        "angular_distance": None,
        "threshold": None,
        "direct_threshold": None,
        "retrograde_threshold": None,
        "excluded_reason": reason,
        "source": CLASSICAL_COMBUSTION_SOURCE,
    }


def calculate_planet_combustion(
    planet: str,
    planet_data: Mapping[str, Any] | None,
    sun_data: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Calculate one planet's combustion with complete audit evidence."""
    if planet == "Sun":
        return _not_applicable(planet, "The Sun is the source of the condition.")
    if planet in {"Rahu", "Ketu"}:
        return _not_applicable(
            planet,
            "Rahu and Ketu are excluded by the selected source as mathematical points.",
        )
    limits = CLASSICAL_COMBUSTION_LIMITS.get(planet)
    if limits is None:
        return _not_applicable(planet, "No combustion limit is assigned by the selected rule table.")

    retrograde = bool((planet_data or {}).get("retrograde"))
    motion = "retrograde" if retrograde else "direct"
    threshold = limits["retrograde"] if retrograde and limits["retrograde"] is not None else limits["direct"]
    planet_longitude = (planet_data or {}).get("longitude")
    sun_longitude = (sun_data or {}).get("longitude")
    distance = None
    if planet_longitude is not None and sun_longitude is not None:
        distance = angular_distance(float(planet_longitude), float(sun_longitude))
    is_combust = distance is not None and distance <= float(threshold)

    return {
        "planet": planet,
        "applicable": True,
        "is_combust": is_combust,
        "status": "combust" if is_combust else "normal",
        "motion": motion,
        "angular_distance": round(distance, 6) if distance is not None else None,
        "threshold": float(threshold),
        "direct_threshold": limits["direct"],
        "retrograde_threshold": limits["retrograde"],
        "excluded_reason": None,
        "source": CLASSICAL_COMBUSTION_SOURCE,
    }


def calculate_chart_combustion(chart_data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Calculate the additive, canonical combustion block for a chart."""
    planets = (chart_data or {}).get("planets") or {}
    sun = planets.get("Sun") or {}
    rows = {
        planet: calculate_planet_combustion(planet, data, sun)
        for planet, data in planets.items()
        if isinstance(data, Mapping)
    }
    return {
        "method": "parashari_loss_of_rays",
        "source": CLASSICAL_COMBUSTION_SOURCE,
        "boundary_rule": "Combust when shortest zodiacal separation is less than or equal to the applicable limit.",
        "planets": rows,
    }


def attach_classical_combustion(chart_data: dict[str, Any]) -> dict[str, Any]:
    """Attach structured and legacy-compatible fields without removing keys."""
    result = calculate_chart_combustion(chart_data)
    chart_data["combustion"] = result
    planets = chart_data.get("planets") or {}
    for planet, row in result["planets"].items():
        data = planets.get(planet)
        if not isinstance(data, dict):
            continue
        data["combustion"] = row
        data["combustion_status"] = row["status"] if row["applicable"] else "normal"
        data["combust"] = bool(row["is_combust"])
    return chart_data

