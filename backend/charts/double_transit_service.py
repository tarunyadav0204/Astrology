"""Exact, isolated Jupiter–Saturn double-transit interval calculator.

The calculator is deliberately independent from chat/prediction pipelines.  It
uses Swiss Ephemeris with Lahiri ayanamsa, whole-sign houses and canonical
Parashari graha drishti.  It never substitutes guessed positions on failure.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import math
from pathlib import Path
import threading
from typing import Any, Dict, Iterable, List, Tuple

import swisseph as swe

from calculators.vedic_graha_drishti import GRAHA_HOUSE_ASPECTS


SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGN_LORDS = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
)
HOUSE_THEMES = {
    1: ("Self & vitality", "identity, vitality, body, direction and personal beginnings"),
    2: ("Wealth & family", "income, savings, family responsibilities, speech and accumulated resources"),
    3: ("Effort & communication", "skills, enterprise, courage, communication, siblings and short journeys"),
    4: ("Home & property", "home, property, mother, education, vehicles and emotional foundations"),
    5: ("Children & intelligence", "children, creativity, study, counsel, romance and merit"),
    6: ("Work & obstacles", "employment, service, competition, debts, disputes and health routines"),
    7: ("Marriage & partnership", "marriage, committed partnership, clients, contracts and public dealings"),
    8: ("Transformation", "joint assets, inheritance, vulnerability, research and major transitions"),
    9: ("Dharma & fortune", "higher learning, teachers, law, faith, father and long journeys"),
    10: ("Career & status", "profession, authority, responsibility, recognition and public contribution"),
    11: ("Gains & networks", "income gains, fulfilment, organisations, patrons, friendships and ambitions"),
    12: ("Release & foreign matters", "expenses, foreign residence, retreat, institutions, sleep and closure"),
}
_EPHEMERIS_LOCK = threading.RLock()
_EPHEMERIS_DIR = Path(__file__).resolve().parent.parent / "ephe"
_REQUIRED_PLANET_FILE = _EPHEMERIS_DIR / "sepl_18.se1"
_EPHEMERIS_START = datetime(1800, 1, 1, tzinfo=timezone.utc)
_EPHEMERIS_END = datetime(2400, 1, 1, tzinfo=timezone.utc)
_REQUIRED_NATAL_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


class DoubleTransitInputError(ValueError):
    """The request cannot be calculated without inventing missing information."""


class DoubleTransitCalculationError(RuntimeError):
    """Swiss Ephemeris or interval calculation failed."""


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _planet_state(at: datetime, planet: str) -> Tuple[float, float]:
    planet_id = {"Jupiter": swe.JUPITER, "Saturn": swe.SATURN}.get(planet)
    if planet_id is None:
        raise DoubleTransitInputError(f"Unsupported double-transit planet: {planet}")
    at = _utc(at)
    hour = at.hour + at.minute / 60.0 + at.second / 3600.0 + at.microsecond / 3_600_000_000.0
    try:
        with _EPHEMERIS_LOCK:
            if not _REQUIRED_PLANET_FILE.is_file():
                raise DoubleTransitCalculationError(
                    f"Required Swiss Ephemeris data file is unavailable: {_REQUIRED_PLANET_FILE.name}"
                )
            # Swiss Ephemeris configuration is process-global. Set and verify it
            # inside the same lock as every calculation so another calculator
            # cannot silently switch this request to the analytic fallback.
            swe.set_ephe_path(str(_EPHEMERIS_DIR))
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            values, return_flags = swe.calc_ut(
                swe.julday(at.year, at.month, at.day, hour),
                planet_id,
                swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH,
            )
            if not return_flags & swe.FLG_SWIEPH or return_flags & swe.FLG_MOSEPH:
                raise DoubleTransitCalculationError(
                    f"Swiss Ephemeris data-file mode was not available for {planet} at {at.isoformat()}"
                )
    except DoubleTransitCalculationError:
        raise
    except Exception as exc:
        raise DoubleTransitCalculationError(
            f"Swiss Ephemeris failed for {planet} at {at.isoformat()}"
        ) from exc
    if not values or len(values) < 4:
        raise DoubleTransitCalculationError(f"Incomplete Swiss Ephemeris state for {planet}")
    return float(values[0]) % 360.0, float(values[3])


def _sign(at: datetime, planet: str) -> int:
    return int(_planet_state(at, planet)[0] / 30.0)


def _screen_sign(at: datetime, planet: str) -> int:
    """Cheaply locate candidate ingress days; never supplies result positions.

    Jupiter and Saturn cannot traverse an entire sign in one day. Moshier is
    used only as a daily change detector; every candidate boundary and every
    value returned to clients is recalculated with and verified against the
    bundled Swiss data file in ``_planet_state``.
    """
    planet_id = {"Jupiter": swe.JUPITER, "Saturn": swe.SATURN}[planet]
    at = _utc(at)
    hour = at.hour + at.minute / 60.0 + at.second / 3600.0
    with _EPHEMERIS_LOCK:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        values, return_flags = swe.calc_ut(
            swe.julday(at.year, at.month, at.day, hour),
            planet_id,
            swe.FLG_SIDEREAL | swe.FLG_MOSEPH,
        )
    if not return_flags & swe.FLG_MOSEPH or not values:
        raise DoubleTransitCalculationError(f"Ingress screening failed for {planet} at {at.isoformat()}")
    return int((float(values[0]) % 360.0) / 30.0)


def _refine_boundary(lo: datetime, hi: datetime, planet: str, old_sign: int) -> datetime:
    """Bisect a detected sign change to within one second."""
    while hi - lo > timedelta(seconds=1):
        mid = lo + (hi - lo) / 2
        if _sign(mid, planet) == old_sign:
            lo = mid
        else:
            hi = mid
    return hi.replace(microsecond=0)


@lru_cache(maxsize=96)
def _decade_segments(planet: str, decade_start: int) -> Tuple[Tuple[str, str, int, bool], ...]:
    """Cache ephemeris-derived sign intervals in reusable ten-year blocks."""
    start = datetime(decade_start, 1, 1, tzinfo=timezone.utc)
    end = datetime(decade_start + 10, 1, 1, tzinfo=timezone.utc)
    cursor = start
    segment_start = start
    previous_sign = _sign(start, planet)
    previous_screen_sign = _screen_sign(start, planet)
    rows: List[Tuple[str, str, int, bool]] = []

    while cursor < end:
        nxt = min(cursor + timedelta(days=1), end)
        next_screen_sign = _screen_sign(nxt, planet)
        if next_screen_sign != previous_screen_sign:
            # Bracket by an extra day so a sub-arcsecond screening difference
            # can never move the verified Swiss ingress outside the interval.
            bracket_lo = max(segment_start, cursor - timedelta(days=1))
            bracket_hi = min(end, nxt + timedelta(days=1))
            verified_old_sign = _sign(bracket_lo, planet)
            verified_new_sign = _sign(bracket_hi, planet)
            if verified_new_sign != verified_old_sign:
                boundary = _refine_boundary(bracket_lo, bracket_hi, planet, verified_old_sign)
                midpoint = segment_start + (boundary - segment_start) / 2
                rows.append((
                    segment_start.isoformat(), boundary.isoformat(), previous_sign,
                    _planet_state(midpoint, planet)[1] < 0,
                ))
                segment_start = boundary
                previous_sign = verified_new_sign
        previous_screen_sign = next_screen_sign
        cursor = nxt

    midpoint = segment_start + (end - segment_start) / 2
    rows.append((
        segment_start.isoformat(), end.isoformat(), previous_sign,
        _planet_state(midpoint, planet)[1] < 0,
    ))
    return tuple(rows)


def _segments(planet: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    first_decade = (start.year // 10) * 10
    last_decade = (end.year // 10) * 10
    for decade in range(first_decade, last_decade + 1, 10):
        for raw_start, raw_end, sign, retrograde in _decade_segments(planet, decade):
            seg_start = datetime.fromisoformat(raw_start)
            seg_end = datetime.fromisoformat(raw_end)
            clipped_start = max(start, seg_start)
            clipped_end = min(end, seg_end)
            if clipped_start < clipped_end:
                out.append({
                    "start": clipped_start,
                    "end": clipped_end,
                    "sign": sign,
                    "retrograde_at_midpoint": retrograde,
                })
    return out


def _target_houses(transit_house: int, planet: str) -> Dict[int, int]:
    return {
        ((transit_house + aspect_number - 2) % 12) + 1: aspect_number
        for aspect_number in GRAHA_HOUSE_ASPECTS[planet]
    }


def _ascendant(chart_data: Dict[str, Any]) -> float:
    value = chart_data.get("ascendant")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DoubleTransitInputError("A numeric sidereal ascendant is required")
    if not 0.0 <= float(value) < 360.0:
        raise DoubleTransitInputError("Ascendant must be in the range 0 <= longitude < 360")
    return float(value)


def _validate_natal_planets(chart_data: Dict[str, Any]) -> None:
    planets = chart_data.get("planets")
    if not isinstance(planets, dict):
        raise DoubleTransitInputError("A complete natal planet set is required")
    for name in _REQUIRED_NATAL_PLANETS:
        data = planets.get(name)
        if not isinstance(data, dict):
            raise DoubleTransitInputError(f"Natal {name} data is required")
        longitude = data.get("longitude")
        if isinstance(longitude, bool) or not isinstance(longitude, (int, float)) or not math.isfinite(float(longitude)):
            raise DoubleTransitInputError(f"A numeric natal longitude is required for {name}")
        if not 0.0 <= float(longitude) < 360.0:
            raise DoubleTransitInputError(f"Natal longitude for {name} must be in the range 0 <= longitude < 360")
        supplied_sign = data.get("sign")
        calculated_sign = int(float(longitude) / 30.0)
        if isinstance(supplied_sign, int) and supplied_sign != calculated_sign:
            raise DoubleTransitInputError(f"Conflicting natal sign and longitude for {name}")


def _natal_context(chart_data: Dict[str, Any], asc_sign: int, house: int) -> Dict[str, Any]:
    target_sign = (asc_sign + house - 1) % 12
    occupants: List[str] = []
    for name, data in (chart_data.get("planets") or {}).items():
        if not isinstance(data, dict) or name in {"Gulika", "Mandi"}:
            continue
        sign = data.get("sign")
        longitude = data.get("longitude")
        calculated_sign = int(float(longitude) / 30.0)
        if isinstance(sign, int) and sign != calculated_sign:
            raise DoubleTransitInputError(f"Conflicting natal sign and longitude for {name}")
        sign = calculated_sign
        if sign == target_sign:
            occupants.append(name)
    return {
        "sign": target_sign,
        "sign_name": SIGN_NAMES[target_sign],
        "lord": SIGN_LORDS[target_sign],
        "occupants": sorted(occupants),
    }


def _iso(at: datetime) -> str:
    return _utc(at).isoformat().replace("+00:00", "Z")


def calculate_double_transits(
    chart_data: Dict[str, Any],
    start: datetime,
    end: datetime,
    *,
    include_aspect_only: bool = True,
) -> Dict[str, Any]:
    start, end = _utc(start), _utc(end)
    if end <= start:
        raise DoubleTransitInputError("end_date must be after start_date")
    if end - start > timedelta(days=366 * 120):
        raise DoubleTransitInputError("Date range cannot exceed 120 years")
    if start < _EPHEMERIS_START or end > _EPHEMERIS_END:
        raise DoubleTransitInputError(
            "Exact bundled ephemeris coverage is 1800-01-01 through 2399-12-31"
        )

    asc = _ascendant(chart_data)
    _validate_natal_planets(chart_data)
    asc_sign = int(asc / 30.0)
    natal_contexts = {
        house: _natal_context(chart_data, asc_sign, house)
        for house in range(1, 13)
    }
    jupiter_segments = _segments("Jupiter", start, end)
    saturn_segments = _segments("Saturn", start, end)
    windows: List[Dict[str, Any]] = []

    j = s = 0
    while j < len(jupiter_segments) and s < len(saturn_segments):
        ju = jupiter_segments[j]
        sa = saturn_segments[s]
        overlap_start = max(ju["start"], sa["start"])
        overlap_end = min(ju["end"], sa["end"])
        if overlap_start < overlap_end:
            ju_house = ((ju["sign"] - asc_sign) % 12) + 1
            sa_house = ((sa["sign"] - asc_sign) % 12) + 1
            ju_targets = _target_houses(ju_house, "Jupiter")
            sa_targets = _target_houses(sa_house, "Saturn")
            for house in sorted(set(ju_targets) & set(sa_targets)):
                ju_aspect = ju_targets[house]
                sa_aspect = sa_targets[house]
                full = ju_aspect == 1 or sa_aspect == 1
                if not full and not include_aspect_only:
                    continue
                title, themes = HOUSE_THEMES[house]
                natal = natal_contexts[house]
                status = "full" if full else "aspect_only"
                windows.append({
                    "id": f"{overlap_start.date()}-{overlap_end.date()}-h{house}-{ju['sign']}-{sa['sign']}",
                    "start_at": _iso(overlap_start),
                    "end_at": _iso(overlap_end),
                    "house": house,
                    "status": status,
                    "house_title": title,
                    "themes": themes,
                    "activation_summary": (
                        f"House {house} ({title}) receives simultaneous Jupiter and Saturn influence. "
                        f"Jupiter opens or expands {themes}; Saturn tests, formalises and makes those matters consequential."
                    ),
                    "manifestation_rule": (
                        "This is a transit activation, not a guaranteed event. Material results require natal promise "
                        "and a connected dasha; relevant divisional and Ashtakavarga support refine strength."
                    ),
                    "natal": natal,
                    "jupiter": {
                        "sign": ju["sign"], "sign_name": SIGN_NAMES[ju["sign"]],
                        "house": ju_house, "aspect_number": ju_aspect,
                        "mode": "occupies" if ju_aspect == 1 else "aspects",
                        "retrograde_at_midpoint": ju["retrograde_at_midpoint"],
                    },
                    "saturn": {
                        "sign": sa["sign"], "sign_name": SIGN_NAMES[sa["sign"]],
                        "house": sa_house, "aspect_number": sa_aspect,
                        "mode": "occupies" if sa_aspect == 1 else "aspects",
                        "retrograde_at_midpoint": sa["retrograde_at_midpoint"],
                    },
                })
        if ju["end"] <= sa["end"]:
            j += 1
        if sa["end"] <= ju["end"]:
            s += 1

    windows.sort(key=lambda row: (row["start_at"], row["house"], row["status"]))
    return {
        "schema": "double_transit.v1",
        "method": {
            "ephemeris": "Swiss Ephemeris data files",
            "ephemeris_file": _REQUIRED_PLANET_FILE.name,
            "candidate_scan": "Daily analytic screening; every ingress boundary is solved and verified with the Swiss data file",
            "zodiac": "Sidereal",
            "ayanamsa": "Lahiri",
            "houses": "Whole sign from natal ascendant",
            "aspects": {
                "Jupiter": GRAHA_HOUSE_ASPECTS["Jupiter"],
                "Saturn": GRAHA_HOUSE_ASPECTS["Saturn"],
            },
            "full_definition": "Both planets influence the same house and at least one occupies it",
            "aspect_only_definition": "Both planets aspect the same house; neither occupies it",
            "boundary_precision": "Swiss Ephemeris ingress boundaries refined to one second UTC",
            "fallbacks_used": False,
        },
        "range": {"start_at": _iso(start), "end_at": _iso(end)},
        "ascendant": {"longitude": asc, "sign": asc_sign, "sign_name": SIGN_NAMES[asc_sign]},
        "window_count": len(windows),
        "windows": windows,
    }
