"""Aspect policy used specifically for Instant Chat house activation.

The broader application may expose different astrological traditions, but the
Instant activation pipeline must use one deterministic rule for dasha and
transit delivery.  Rahu and Ketu activate by occupation/conjunction and their
7th aspect only; their disputed 5th and 9th aspects are deliberately excluded.
"""

from __future__ import annotations

from typing import Tuple


INSTANT_ACTIVATION_ASPECTS = {
    "Sun": (1, 7),
    "Moon": (1, 7),
    "Mars": (1, 4, 7, 8),
    "Mercury": (1, 7),
    "Jupiter": (1, 5, 7, 9),
    "Venus": (1, 7),
    "Saturn": (1, 3, 7, 10),
    "Rahu": (1, 7),
    "Ketu": (1, 7),
}


def instant_activation_aspects(
    planet: str,
    *,
    include_conjunction: bool = True,
) -> Tuple[int, ...]:
    """Return allowed whole-sign aspects for Instant activation checks."""
    aspects = INSTANT_ACTIVATION_ASPECTS.get(str(planet or ""), (1, 7))
    if include_conjunction:
        return aspects
    return tuple(number for number in aspects if number != 1)
