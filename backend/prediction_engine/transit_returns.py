"""Strict exact natal-longitude returns for active Vimshottari lords.

Daily transit states are used only to screen for a crossing.  Every returned
timestamp and orb boundary is recalculated with the bundled Swiss Ephemeris
data file in Lahiri sidereal mode.  A failed data-file calculation is an
explicit prediction calculation error; it is never replaced with Moshier.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import threading
from typing import Any, Callable, Dict, List, Sequence, Tuple

import swisseph as swe

from .contracts import PredictionWindow
from .errors import PredictionCalculationError


EXACT_NATAL_RETURN_ORB_DEGREES = 1.0
_EPHEMERIS_LOCK = threading.RLock()
_EPHEMERIS_DIR = Path(__file__).resolve().parent.parent / "ephe"
_REQUIRED_EPHEMERIS_FILES = (
    _EPHEMERIS_DIR / "sepl_18.se1",
    _EPHEMERIS_DIR / "semo_18.se1",
)
_PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Ketu": swe.MEAN_NODE,
}
_ORB_SEARCH_STEPS = {
    "Moon": timedelta(minutes=30),
    "Mercury": timedelta(hours=2),
    "Venus": timedelta(hours=3),
    "Sun": timedelta(hours=3),
    "Mars": timedelta(hours=6),
    "Jupiter": timedelta(hours=12),
    "Saturn": timedelta(hours=12),
    "Rahu": timedelta(hours=12),
    "Ketu": timedelta(hours=12),
}
_RETURN_SEQUENCE_GAPS = {
    "Moon": timedelta(days=5),
    "Mercury": timedelta(days=55),
    "Venus": timedelta(days=110),
    "Sun": timedelta(days=10),
    "Mars": timedelta(days=180),
    "Jupiter": timedelta(days=300),
    "Saturn": timedelta(days=300),
    "Rahu": timedelta(days=30),
    "Ketu": timedelta(days=30),
}


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _angular_distance(first: float, second: float) -> float:
    distance = abs(float(first) - float(second)) % 360.0
    return min(distance, 360.0 - distance)


def _signed_delta(first: float, second: float) -> float:
    """Shortest signed arc from ``first`` to ``second`` in degrees."""
    return ((float(second) - float(first) + 180.0) % 360.0) - 180.0


def _strict_planet_state(at: datetime, planet: str) -> Tuple[float, float]:
    planet_id = _PLANET_IDS.get(planet)
    if planet_id is None:
        raise PredictionCalculationError(
            f"Exact natal return does not support planet: {planet}"
        )
    at = _utc(at)
    hour = (
        at.hour
        + at.minute / 60.0
        + at.second / 3600.0
        + at.microsecond / 3_600_000_000.0
    )
    try:
        with _EPHEMERIS_LOCK:
            missing = [path.name for path in _REQUIRED_EPHEMERIS_FILES if not path.is_file()]
            if missing:
                raise PredictionCalculationError(
                    "Required Swiss Ephemeris data is unavailable: " + ", ".join(missing)
                )
            swe.set_ephe_path(str(_EPHEMERIS_DIR))
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            values, return_flags = swe.calc_ut(
                swe.julday(at.year, at.month, at.day, hour),
                planet_id,
                swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH,
            )
            if not return_flags & swe.FLG_SWIEPH or return_flags & swe.FLG_MOSEPH:
                raise PredictionCalculationError(
                    f"Swiss data-file mode was unavailable for {planet} at {at.isoformat()}"
                )
    except PredictionCalculationError:
        raise
    except Exception as exc:
        raise PredictionCalculationError(
            f"Exact natal return calculation failed for {planet} at {at.isoformat()}"
        ) from exc
    if not values or len(values) < 4:
        raise PredictionCalculationError(
            f"Swiss Ephemeris returned an incomplete state for {planet}"
        )
    longitude = float(values[0]) % 360.0
    speed = float(values[3])
    if planet == "Ketu":
        longitude = (longitude + 180.0) % 360.0
    return longitude, speed


def _crosses_target(start_longitude: float, end_longitude: float, target: float) -> bool:
    travel = _signed_delta(start_longitude, end_longitude)
    target_arc = _signed_delta(start_longitude, target)
    if travel > 0.0 and target_arc < 0.0:
        target_arc += 360.0
    elif travel < 0.0 and target_arc > 0.0:
        target_arc -= 360.0
    return (0.0 <= target_arc <= travel) if travel >= 0.0 else (travel <= target_arc <= 0.0)


def _refine_crossing(
    lo: datetime,
    hi: datetime,
    planet: str,
    target: float,
    state_at: Callable[[datetime, str], Tuple[float, float]],
) -> datetime:
    lo_longitude, _ = state_at(lo, planet)
    while hi - lo > timedelta(seconds=1):
        mid = lo + (hi - lo) / 2
        mid_longitude, _ = state_at(mid, planet)
        if _crosses_target(lo_longitude, mid_longitude, target):
            hi = mid
        else:
            lo = mid
            lo_longitude = mid_longitude
    return hi.replace(microsecond=0)


def _refine_station(
    lo: datetime,
    hi: datetime,
    planet: str,
    state_at: Callable[[datetime, str], Tuple[float, float]],
) -> datetime:
    """Resolve a direct/retrograde station so roots cannot hide around it."""
    _, lo_speed = state_at(lo, planet)
    while hi - lo > timedelta(seconds=1):
        mid = lo + (hi - lo) / 2
        _, mid_speed = state_at(mid, planet)
        if (lo_speed < 0.0) == (mid_speed < 0.0):
            lo = mid
            lo_speed = mid_speed
        else:
            hi = mid
    return hi.replace(microsecond=0)


def _refine_orb_boundary(
    inside: datetime,
    outside: datetime,
    planet: str,
    target: float,
    state_at: Callable[[datetime, str], Tuple[float, float]],
) -> datetime:
    """Bisect an inside/outside pair to a one-second orb boundary."""
    while abs(outside - inside) > timedelta(seconds=1):
        mid = inside + (outside - inside) / 2
        longitude, _ = state_at(mid, planet)
        if _angular_distance(longitude, target) <= EXACT_NATAL_RETURN_ORB_DEGREES:
            inside = mid
        else:
            outside = mid
    return inside.replace(microsecond=0)


def _orb_boundary(
    exact_at: datetime,
    planet: str,
    target: float,
    direction: int,
    state_at: Callable[[datetime, str], Tuple[float, float]],
) -> datetime:
    step = _ORB_SEARCH_STEPS[planet] * direction
    inside = exact_at
    outside = exact_at + step
    # A slow planet can station while still inside the orb.  Four hundred days
    # safely spans the complete retrograde loop of every supported planet.
    for _ in range(max(2, int(timedelta(days=400) / abs(step)))):
        longitude, _ = state_at(outside, planet)
        if _angular_distance(longitude, target) > EXACT_NATAL_RETURN_ORB_DEGREES:
            return _refine_orb_boundary(inside, outside, planet, target, state_at)
        inside = outside
        outside += step
    raise PredictionCalculationError(
        f"Could not resolve the ±{EXACT_NATAL_RETURN_ORB_DEGREES:g}° orb boundary "
        f"for {planet} natal return"
    )


def _screen_samples(
    planet: str,
    start: date,
    end: date,
    daily_states: Dict[str, Dict[str, Dict[str, Any]]],
    state_at: Callable[[datetime, str], Tuple[float, float]],
) -> List[Tuple[datetime, float, float]]:
    samples: List[Tuple[datetime, float, float]] = []
    start_at = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_at = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    start_longitude, start_speed = state_at(start_at, planet)
    samples.append((start_at, start_longitude, start_speed))
    day = start
    while day <= end:
        state = (daily_states.get(day.isoformat()) or {}).get(planet)
        if state is None or state.get("longitude") is None:
            raise PredictionCalculationError(
                f"Daily transit screening state is missing for {planet} on {day.isoformat()}"
            )
        samples.append((
            datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12),
            float(state["longitude"]) % 360.0,
            float(state.get("speed") or 0.0),
        ))
        day += timedelta(days=1)
    end_longitude, end_speed = state_at(end_at, planet)
    samples.append((end_at, end_longitude, end_speed))
    return sorted(samples, key=lambda row: row[0])


def build_exact_natal_return_passes(
    chart: Dict[str, Any],
    windows: Sequence[PredictionWindow],
    daily_states: Dict[str, Dict[str, Dict[str, Any]]],
    start: date,
    end: date,
    *,
    state_at: Callable[[datetime, str], Tuple[float, float]] = _strict_planet_state,
) -> Dict[str, Sequence[Dict[str, Any]]]:
    """Return exact direct/retrograde passes for all dasha lords in the horizon."""
    dasha_planets = sorted({
        planet
        for window in windows
        for planet in (window.mahadasha, window.antardasha, window.pratyantardasha)
    })
    results: Dict[str, Sequence[Dict[str, Any]]] = {}
    for planet in dasha_planets:
        natal = (chart.get("planets") or {}).get(planet)
        if not isinstance(natal, dict) or natal.get("longitude") is None:
            raise PredictionCalculationError(
                f"Natal longitude is required for active dasha lord {planet}"
            )
        target = float(natal["longitude"]) % 360.0
        samples = _screen_samples(planet, start, end, daily_states, state_at)
        exact_times: List[datetime] = []
        for lo_row, hi_row in zip(samples, samples[1:]):
            intervals = [lo_row, hi_row]
            # A station can put two return roots inside one daily screening
            # interval while both endpoints sit on the same side of natal
            # longitude. Split at the verified speed-zero boundary first.
            if (
                planet not in {"Rahu", "Ketu"}
                and lo_row[2] * hi_row[2] < 0.0
            ):
                station_at = _refine_station(lo_row[0], hi_row[0], planet, state_at)
                station_longitude, station_speed = state_at(station_at, planet)
                intervals.insert(1, (station_at, station_longitude, station_speed))
            for segment_lo, segment_hi in zip(intervals, intervals[1:]):
                lo, lo_longitude, _ = segment_lo
                hi, hi_longitude, _ = segment_hi
                if not _crosses_target(lo_longitude, hi_longitude, target):
                    continue
                exact_at = _refine_crossing(lo, hi, planet, target, state_at)
                if not exact_times or abs(exact_at - exact_times[-1]) > timedelta(minutes=2):
                    exact_times.append(exact_at)

        passes: List[Dict[str, Any]] = []
        for exact_at in exact_times:
            exact_longitude, speed = state_at(exact_at, planet)
            retrograde = speed < 0.0 or planet in {"Rahu", "Ketu"}
            motion = "retrograde" if retrograde else "direct"
            passes.append({
                "planet": planet,
                "natal_longitude": round(target, 8),
                "exact_longitude": round(exact_longitude, 8),
                "exact_distance_degrees": round(_angular_distance(exact_longitude, target), 8),
                "orb_degrees": EXACT_NATAL_RETURN_ORB_DEGREES,
                "start_at": _orb_boundary(exact_at, planet, target, -1, state_at).isoformat(),
                "exact_at": exact_at.isoformat(),
                "end_at": _orb_boundary(exact_at, planet, target, 1, state_at).isoformat(),
                "motion": motion,
                "retrograde": retrograde,
            })
        if passes:
            grouped: List[List[Dict[str, Any]]] = []
            for row in passes:
                exact_at = datetime.fromisoformat(str(row["exact_at"]))
                if (
                    grouped
                    and exact_at - datetime.fromisoformat(
                        str(grouped[-1][-1]["exact_at"])
                    ) <= _RETURN_SEQUENCE_GAPS[planet]
                ):
                    grouped[-1].append(row)
                else:
                    grouped.append([row])
            numbered: List[Dict[str, Any]] = []
            for sequence_number, group in enumerate(grouped, start=1):
                sequence = " → ".join(row["motion"].title() for row in group)
                for pass_number, row in enumerate(group, start=1):
                    numbered.append({
                        **row,
                        "sequence_number": sequence_number,
                        "pass_number": pass_number,
                        "pass_label": f"{row['motion'].title()} pass {pass_number}",
                        "pass_sequence": sequence,
                    })
            results[planet] = tuple(numbered)
    return results
