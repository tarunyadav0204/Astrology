"""Safety filters for data leaving astrology calculators for an LLM."""

from __future__ import annotations

from typing import Any


OUTER_PLANETS = frozenset({"uranus", "neptune", "pluto"})
_DROP = object()
_PLANET_REFERENCE_KEYS = frozenset({
    "planet", "planet_name", "source_planet", "target_planet", "aspecting_planet",
    "aspected_planet", "transit_planet", "natal_planet", "graha",
})


def strip_outer_planets_from_llm_context(value: Any) -> Any:
    """Remove modern outer-planet facts from any payload sent to a chat model.

    The chart renderer may retain these optional display bodies. This function
    is deliberately applied only at LLM boundaries and removes both keyed
    planet maps and record/list representations such as aspect rows.
    """
    cleaned = _strip(value)
    return {} if cleaned is _DROP else cleaned


def _is_outer_planet(value: Any) -> bool:
    return str(value or "").strip().lower() in OUTER_PLANETS


def _strip(value: Any) -> Any:
    if isinstance(value, dict):
        if any(_is_outer_planet(value.get(key)) for key in _PLANET_REFERENCE_KEYS if key in value):
            return _DROP
        result = {}
        for key, item in value.items():
            if _is_outer_planet(key):
                continue
            cleaned = _strip(item)
            if cleaned is not _DROP:
                result[key] = cleaned
        return result
    if isinstance(value, list):
        return [cleaned for item in value if (cleaned := _strip(item)) is not _DROP]
    if isinstance(value, tuple):
        return tuple(cleaned for item in value if (cleaned := _strip(item)) is not _DROP)
    return value
