"""Shared compact helpers for vedic context agents (no legacy imports)."""

from __future__ import annotations

from typing import Dict, List

# Standard output order for nine grahas (matches common engine ordering).
PLANET_ORDER: List[str] = [
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Rahu",
    "Ketu",
]

# Sidereal sign names; index 0 = Aries … 11 = Pisces (matches ChartCalculator.SIGN_NAMES).
SIGN_NAMES: List[str] = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def sign_name_from_index_0(sign_0_11: int) -> str:
    return SIGN_NAMES[int(sign_0_11) % 12]


def sign_name_from_1_12(sign_1_12: int) -> str:
    """1=Aries … 12=Pisces (human convention; not 0-based)."""
    return SIGN_NAMES[(int(sign_1_12) - 1) % 12]

# sign index 0=Aries .. 11=Pisces -> lord planet name
SIGN_LORDS: Dict[int, str] = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Mars",
    8: "Jupiter",
    9: "Saturn",
    10: "Saturn",
    11: "Jupiter",
}


def house_lordships_from_ascendant(asc_sign_0_11: int) -> Dict[str, List[int]]:
    """
    Planet -> houses ruled (whole-sign from ascendant), same mapping as
    ChatContextBuilder._get_house_lordships.
    """
    out: Dict[str, List[int]] = {}
    for house in range(1, 13):
        house_sign = (asc_sign_0_11 + house - 1) % 12
        lord = SIGN_LORDS[house_sign]
        out.setdefault(lord, []).append(house)
    for k in out:
        out[k] = sorted(out[k])
    return out


def sign_1_12_from_lon(longitude: float) -> int:
    """Vedic sign index 1–12 from absolute sidereal longitude."""
    s0 = int(float(longitude) / 30.0) % 12
    return s0 + 1
