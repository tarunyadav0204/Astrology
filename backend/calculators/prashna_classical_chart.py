"""Astronomy and houses for the versioned Hayanaratna Prashna profile.

This is deliberately independent of the natal-chart calculator.  Tropical Swiss
Ephemeris positions are converted with the precession rule described in
Hayanaratna 1.9, then houses are divided from the four angles into alternating
cusps and junctions.  No whole-sign house substitution is made.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import swisseph as swe

from calculators.chart_calculator import _SWISSEPH_CHART_LOCK


SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

PLANETS = (
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
)


def forward_arc(start: float, end: float) -> float:
    return (end - start) % 360.0


def on_forward_arc(value: float, start: float, end: float, *, include_end: bool = False) -> bool:
    span = forward_arc(start, end)
    offset = forward_arc(start, value)
    return offset <= span if include_end else offset < span


def _saka_year(day: date) -> int:
    """Civil Saka year for the textual annual precession calculation.

    The civil year begins around 22 March (21 March in Gregorian leap years).
    The day-level distinction changes the ayanamsa by less than one arcminute but
    is kept explicit for reproducibility.
    """
    leap = day.year % 4 == 0 and (day.year % 100 != 0 or day.year % 400 == 0)
    start = date(day.year, 3, 21 if leap else 22)
    return day.year - (78 if day >= start else 79)


def hayanaratna_ayanamsa(day: date, tropical_sun: float) -> float:
    """Hayanaratna 1.9 precessional value, expressed in decimal degrees.

    The rule subtracts 421 from the Saka year, reduces the remainder by a
    tenth, divides by sixty, and adds 4.5 arcseconds per tropical sign
    traversed by the Sun.  This is a historical calculation profile, not a
    claim that the historical rate equals modern measured precession.
    """
    years = _saka_year(day) - 421
    annual = years * 0.9 / 60.0
    within_year = ((tropical_sun % 360.0) / 30.0) * 4.5 / 3600.0
    return (annual + within_year) % 360.0


def sripati_cusps(ascendant: float, midheaven: float) -> List[float]:
    """Return twelve cusps by trisecting each ecliptic quadrant.

    This is the modern exact equivalent of Hayanaratna's sequence from cusp to
    junction to cusp using sixths of each quadrant arc.
    """
    anchors = {
        1: ascendant % 360.0,
        4: (midheaven + 180.0) % 360.0,
        7: (ascendant + 180.0) % 360.0,
        10: midheaven % 360.0,
    }
    cusps: Dict[int, float] = {}
    for first, last in ((1, 4), (4, 7), (7, 10), (10, 13)):
        start = anchors[first]
        end = anchors[1] if last == 13 else anchors[last]
        step = forward_arc(start, end) / 3.0
        for index in range(3):
            house = ((first + index - 1) % 12) + 1
            cusps[house] = (start + step * index) % 360.0
    return [cusps[house] for house in range(1, 13)]


def house_junctions(cusps: Iterable[float]) -> List[float]:
    cusp_list = list(cusps)
    return [
        (cusp_list[index] + forward_arc(cusp_list[index], cusp_list[(index + 1) % 12]) / 2.0) % 360.0
        for index in range(12)
    ]


def locate_house(longitude: float, cusps: Iterable[float], junctions: Iterable[float]) -> Tuple[int, float]:
    """Return house number and 0..20 viṃśopaka positional strength."""
    cusp_list, boundary_after = list(cusps), list(junctions)
    longitude %= 360.0
    for index in range(12):
        previous_boundary = boundary_after[(index - 1) % 12]
        next_boundary = boundary_after[index]
        if not on_forward_arc(longitude, previous_boundary, next_boundary, include_end=index == 11):
            continue
        cusp = cusp_list[index]
        if on_forward_arc(longitude, previous_boundary, cusp, include_end=True):
            denominator = forward_arc(previous_boundary, cusp)
            ratio = forward_arc(previous_boundary, longitude) / denominator if denominator else 1.0
        else:
            denominator = forward_arc(cusp, next_boundary)
            ratio = forward_arc(longitude, next_boundary) / denominator if denominator else 1.0
        return index + 1, round(max(0.0, min(20.0, ratio * 20.0)), 6)
    raise ValueError(f"Unable to place longitude {longitude} between house junctions")


class ClassicalPrashnaChartCalculator:
    PROFILE_ID = "hayanaratna_textual_precession_quadrant_v1"

    def calculate_chart(self, clock) -> Dict:
        utc = clock.utc_datetime
        hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3_600_000_000.0
        with _SWISSEPH_CHART_LOCK:
            swe.set_ephe_path(str(Path(__file__).resolve().parent.parent / "ephe"))
            jd = swe.julday(utc.year, utc.month, utc.day, hour)
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            raw: Dict[str, Dict] = {}
            engines = set()
            for name, body in PLANETS:
                position, returned = swe.calc_ut(jd, body, flags)
                engines.add("Moshier" if returned & swe.FLG_MOSEPH else "Swiss Ephemeris")
                raw[name] = {"tropical_longitude": position[0] % 360.0, "speed": position[3]}
            node, returned = swe.calc_ut(jd, swe.MEAN_NODE, flags)
            engines.add("Moshier" if returned & swe.FLG_MOSEPH else "Swiss Ephemeris")
            raw["Rahu"] = {"tropical_longitude": node[0] % 360.0, "speed": node[3]}
            raw["Ketu"] = {"tropical_longitude": (node[0] + 180.0) % 360.0, "speed": node[3]}
            _, axes = swe.houses_ex(jd, clock.latitude, clock.longitude, b"P", 0)

        ayanamsa = hayanaratna_ayanamsa(utc.date(), raw["Sun"]["tropical_longitude"])
        ascendant = (axes[0] - ayanamsa) % 360.0
        midheaven = (axes[1] - ayanamsa) % 360.0
        cusps = sripati_cusps(ascendant, midheaven)
        junctions = house_junctions(cusps)
        planets: Dict[str, Dict] = {}
        for name, row in raw.items():
            longitude = (row["tropical_longitude"] - ayanamsa) % 360.0
            sign = int(longitude // 30)
            house, house_strength = locate_house(longitude, cusps, junctions)
            planets[name] = {
                "longitude": longitude,
                "tropical_longitude": row["tropical_longitude"],
                "speed": row["speed"],
                "retrograde": row["speed"] < 0,
                "sign": sign,
                "sign_name": SIGN_NAMES[sign],
                "degree": longitude % 30.0,
                "house": house,
                "house_strength": house_strength,
            }
        houses = []
        for index, cusp in enumerate(cusps):
            houses.append({
                "house": index + 1,
                "cusp": cusp,
                "cusp_sign": int(cusp // 30),
                "begin_junction": junctions[(index - 1) % 12],
                "end_junction": junctions[index],
            })
        return {
            "ascendant": ascendant,
            "midheaven": midheaven,
            "houses": houses,
            "planets": planets,
            "calculation": {
                "profile_id": self.PROFILE_ID,
                "zodiac": "sidereal",
                "ayanamsha": "Hayanaratna 1.9 textual precession",
                "ayanamsha_degrees": ayanamsa,
                "node_type": "mean",
                "house_system": "Hayanaratna quadrant cusps and junctions (Sripati geometry)",
                "julian_day_ut": jd,
                "ephemeris": sorted(engines),
                "source": "Hayanaratna 1.9",
            },
        }
