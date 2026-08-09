from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from calculators.badhaka_calculator import BadhakaCalculator
from calculators.chart_calculator import ChartCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.gandanta_calculator import GandantaCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from calculators.yogi_calculator import YogiCalculator
from shared.dasha_calculator import DashaCalculator

from .context import CalculationContext
from .contracts import BirthChartInput, PredictionWindow
from .errors import PredictionCalculationError


CLASSICAL_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
)

RESOLUTION_VARGAS = (2, 4, 7, 9, 10, 12, 24)

# Prediction-engine convention only.  The rest of AstroRoshni continues to use
# the canonical calculator's configured node aspects.  This deterministic
# Parashari implementation deliberately treats Rahu and Ketu as having only
# the universal full 7th-house graha drishti; it does not promote the disputed
# 5th/9th node glances to house-activation evidence.
PREDICTION_NODE_ASPECTS = (7,)


def _as_datetime(value: date) -> datetime:
    return datetime.combine(value, datetime.min.time())


def _date_range(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def angular_distance(first: float, second: float) -> float:
    distance = abs(float(first) - float(second)) % 360.0
    return min(distance, 360.0 - distance)


def aspected_houses(planet: str, planet_house: int) -> Tuple[int, ...]:
    from calculators.vedic_graha_drishti import get_aspect_houses_for_planet

    aspect_numbers = (
        PREDICTION_NODE_ASPECTS
        if planet in {"Rahu", "Ketu"}
        else get_aspect_houses_for_planet(planet)
    )
    return tuple(
        ((int(planet_house) + aspect_number - 2) % 12) + 1
        for aspect_number in aspect_numbers
        if aspect_number != 1
    )


def ruled_houses(chart: Dict[str, Any], planet: str) -> Tuple[int, ...]:
    ascendant_sign = int(float(chart["ascendant"]) / 30.0)
    sign_lords = BadhakaCalculator.SIGN_LORDS
    return tuple(
        house
        for house in range(1, 13)
        if sign_lords[(ascendant_sign + house - 1) % 12] == planet
    )


def planetary_connections(
    chart: Dict[str, Any], first_planet: str, second_planet: str
) -> Tuple[str, ...]:
    """Return direct Parashari sambandha between two natal planets."""

    if first_planet == second_planet:
        return ("same_planet",)
    first = chart["planets"][first_planet]
    second = chart["planets"][second_planet]
    relations: List[str] = []
    if int(first["house"]) == int(second["house"]):
        relations.append("conjunction")
    if int(second["house"]) in aspected_houses(first_planet, int(first["house"])):
        relations.append("first_aspects_second")
    if int(first["house"]) in aspected_houses(second_planet, int(second["house"])):
        relations.append("second_aspects_first")
    first_dispositor = BadhakaCalculator.SIGN_LORDS[int(first["sign"])]
    second_dispositor = BadhakaCalculator.SIGN_LORDS[int(second["sign"])]
    if first_dispositor == second_planet:
        relations.append("first_disposed_by_second")
    if second_dispositor == first_planet:
        relations.append("second_disposed_by_first")
    if first_dispositor == second_planet and second_dispositor == first_planet:
        relations.append("sign_exchange")
    return tuple(dict.fromkeys(relations))


def _validate_chart(chart: Dict[str, Any]) -> None:
    if not isinstance(chart, dict) or not isinstance(chart.get("planets"), dict):
        raise PredictionCalculationError("Natal chart calculation returned no planets")
    missing = [planet for planet in CLASSICAL_PLANETS if planet not in chart["planets"]]
    if missing:
        raise PredictionCalculationError(
            f"Natal chart is missing required planets: {', '.join(missing)}"
        )
    if chart.get("ascendant") is None or len(chart.get("houses") or []) != 12:
        raise PredictionCalculationError("Natal chart is missing whole-sign houses or ascendant")


def _build_divisional_charts(chart: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    calculator = DivisionalChartCalculator(chart)
    result: Dict[str, Dict[str, Any]] = {}
    for division in RESOLUTION_VARGAS:
        try:
            payload = calculator.calculate_divisional_chart(division)
            divisional = payload["divisional_chart"]
            _validate_chart(divisional)
        except Exception as exc:
            raise PredictionCalculationError(
                f"Required D{division} calculation failed"
            ) from exc
        result[f"D{division}"] = divisional
    return result


def _dasha_rows(
    birth: BirthChartInput,
    start: date,
    end: date,
) -> List[Dict[str, str]]:
    try:
        rows = DashaCalculator().get_dasha_periods_for_range(
            birth.to_calculator_dict(),
            _as_datetime(start),
            _as_datetime(end),
            strict=True,
        )
    except Exception as exc:
        raise PredictionCalculationError("Strict MD-AD-PD calculation failed") from exc
    if not rows:
        raise PredictionCalculationError("Strict MD-AD-PD calculation returned no periods")
    required = ("start_date", "end_date", "mahadasha", "antardasha", "pratyantardasha")
    for row in rows:
        if any(not row.get(key) for key in required):
            raise PredictionCalculationError("Dasha period is missing required real boundaries or lords")
    return rows


def _dasha_for_day(rows: Sequence[Dict[str, str]], day: date) -> Dict[str, str]:
    day_text = day.isoformat()
    matches = [row for row in rows if row["start_date"] <= day_text <= row["end_date"]]
    if len(matches) != 1:
        raise PredictionCalculationError(
            f"Expected exactly one MD-AD-PD period on {day_text}; found {len(matches)}"
        )
    return matches[0]


def _transit_states_for_day(
    calculator: RealTransitCalculator,
    chart: Dict[str, Any],
    day: date,
    planets: Iterable[str],
) -> Dict[str, Dict[str, Any]]:
    from .nakshatra_transit import nakshatra_position

    dt = _as_datetime(day)
    # Calculate the complete classical transit field once.  Event selection is
    # downstream; restricting facts to dasha planets made non-dasha Saturn,
    # Jupiter and node triggers impossible to inspect.
    required = set(CLASSICAL_PLANETS)
    states: Dict[str, Dict[str, Any]] = {}
    try:
        for planet in sorted(required):
            state = calculator.get_planet_state(dt, planet)
            state["house"] = calculator.calculate_house_from_longitude(
                state["longitude"], chart["ascendant"]
            )
            nakshatra = nakshatra_position(state["longitude"])
            state.update({
                "nakshatra_index": nakshatra["index"],
                "nakshatra_number": nakshatra["number"],
                "nakshatra": nakshatra["name"],
                "nakshatra_lord": nakshatra["lord"],
                "nakshatra_pada": nakshatra["pada"],
            })
            states[planet] = state
    except Exception as exc:
        raise PredictionCalculationError(
            f"Strict transit calculation failed on {day.isoformat()}"
        ) from exc

    sun_longitude = states["Sun"]["longitude"]
    thresholds = PlanetaryDignitiesCalculator({}).COMBUSTION_THRESHOLDS
    for planet, state in states.items():
        threshold = thresholds.get(planet)
        distance = angular_distance(state["longitude"], sun_longitude)
        state["sun_distance"] = distance
        # Parashari profile: proximity inside the classical combustion orb is
        # combustion. Do not import the Western cazimi exception into this
        # engine, even though a legacy dignity helper exposes that label.
        state["combustion"] = (
            "combust" if threshold is not None and distance <= threshold else "normal"
        )
    return states


# Slow / structural bodies whose rāśi (and Rx/combustion) define timing slices.
# Sun is intentionally omitted: a lone Sun ingress does not re-slice windows.
# Sun still affects slices indirectly when a watched planet's combustion flips.
SIGNATURE_STRUCTURE_PLANETS = ("Jupiter", "Saturn", "Rahu", "Ketu")


def _transit_signature_planets(dasha_row: Dict[str, str]) -> Tuple[str, ...]:
    """Planets whose transit facts cut activation timing windows.

    Includes MD/AD/PD lords plus Jupiter, Saturn, Rahu, Ketu.
    Does not include Sun — bare Sun sign/house change is not a window boundary.
    """
    dasha_planets = {
        dasha_row["mahadasha"],
        dasha_row["antardasha"],
        dasha_row["pratyantardasha"],
    }
    return tuple(sorted(set((*dasha_planets, *SIGNATURE_STRUCTURE_PLANETS))))


def _normalise_signature_fact(
    planet: str,
    state: Dict[str, Any],
    *,
    include_nakshatra: bool,
) -> Dict[str, Any]:
    """Canonical facts so signature hash and boundary diffs stay aligned."""
    fact: Dict[str, Any] = {
        "sign": str(state.get("sign") or ""),
        "retrograde": bool(state.get("retrograde")),
        "combustion": (
            "combust" if state.get("combustion") == "combust" else "normal"
        ),
    }
    if include_nakshatra:
        fact["nakshatra_index"] = int(state.get("nakshatra_index") or 0)
        fact["nakshatra"] = str(state.get("nakshatra") or "")
    return fact


def _transit_signature(
    dasha_row: Dict[str, str], states: Dict[str, Dict[str, Any]]
) -> str:
    dasha_planets = {
        dasha_row["mahadasha"],
        dasha_row["antardasha"],
        dasha_row["pratyantardasha"],
    }
    planets = _transit_signature_planets(dasha_row)
    payload = {
        "dasha": [
            dasha_row["mahadasha"],
            dasha_row["antardasha"],
            dasha_row["pratyantardasha"],
        ],
        "transits": {
            planet: _normalise_signature_fact(
                planet,
                states[planet],
                include_nakshatra=planet in dasha_planets,
            )
            for planet in planets
        },
    }
    # Nakṣatra name is display-only; hash must stay index-stable.
    hash_payload = {
        "dasha": payload["dasha"],
        "transits": {
            planet: {
                key: value
                for key, value in fact.items()
                if key != "nakshatra"
            }
            for planet, fact in payload["transits"].items()
        },
    }
    return hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]


def _window_boundary_changes(
    prev_row: Dict[str, str],
    prev_states: Dict[str, Dict[str, Any]],
    row: Dict[str, str],
    states: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Any], ...]:
    """Human-readable reasons a timing window opens (signature / dasha flip)."""
    changes: List[Dict[str, Any]] = []
    for level, key in (
        ("MD", "mahadasha"),
        ("AD", "antardasha"),
        ("PD", "pratyantardasha"),
    ):
        if prev_row[key] != row[key]:
            changes.append({
                "kind": "dasha",
                "level": level,
                "planet": row[key],
                "from_planet": prev_row[key],
                "to_planet": row[key],
                "label": f"{level} {row[key]} begins",
            })

    dasha_planets = {
        row["mahadasha"],
        row["antardasha"],
        row["pratyantardasha"],
    }
    watched_dasha = dasha_planets | {
        prev_row["mahadasha"],
        prev_row["antardasha"],
        prev_row["pratyantardasha"],
    }

    for planet in sorted(
        set(_transit_signature_planets(row)) | set(_transit_signature_planets(prev_row))
    ):
        if planet not in prev_states or planet not in states:
            continue
        prev = _normalise_signature_fact(
            planet, prev_states[planet], include_nakshatra=planet in watched_dasha
        )
        curr = _normalise_signature_fact(
            planet, states[planet], include_nakshatra=planet in watched_dasha
        )
        if prev["sign"] != curr["sign"]:
            changes.append({
                "kind": "sign",
                "planet": planet,
                "from_value": prev["sign"],
                "to_value": curr["sign"],
                "label": f"{planet} → {curr['sign']}",
            })
        if (
            planet in watched_dasha
            and prev.get("nakshatra_index") != curr.get("nakshatra_index")
        ):
            changes.append({
                "kind": "nakshatra",
                "planet": planet,
                "from_value": prev.get("nakshatra") or prev.get("nakshatra_index"),
                "to_value": curr.get("nakshatra") or curr.get("nakshatra_index"),
                "label": (
                    f"{planet} nakṣatra → {curr.get('nakshatra')}"
                    if curr.get("nakshatra")
                    else f"{planet} nakṣatra changes"
                ),
            })
        if prev["retrograde"] != curr["retrograde"]:
            changes.append({
                "kind": "retrograde",
                "planet": planet,
                "to_value": curr["retrograde"],
                "label": (
                    f"{planet} stations retrograde"
                    if curr["retrograde"]
                    else f"{planet} stations direct"
                ),
            })
        if prev["combustion"] != curr["combustion"]:
            changes.append({
                "kind": "combustion",
                "planet": planet,
                "to_value": curr["combustion"],
                "label": (
                    f"{planet} combust"
                    if curr["combustion"] == "combust"
                    else f"{planet} leaves combustion"
                ),
            })

    if not changes:
        changes.append({
            "kind": "signature_shift",
            "label": "Transit signature shift",
        })
    return tuple(changes)


def _build_windows(
    birth: BirthChartInput,
    chart: Dict[str, Any],
    start: date,
    end: date,
) -> Tuple[
    List[PredictionWindow],
    Dict[str, Dict[str, Dict[str, Any]]],
    Dict[str, Dict[str, Dict[str, Any]]],
]:
    dasha_rows = _dasha_rows(birth, start, end)
    transit_calculator = RealTransitCalculator()
    windows: List[PredictionWindow] = []
    states_by_signature: Dict[str, Dict[str, Dict[str, Any]]] = {}
    daily_states: Dict[str, Dict[str, Dict[str, Any]]] = {}
    active_start: date | None = None
    active_signature = ""
    active_row: Dict[str, str] | None = None
    active_states: Dict[str, Dict[str, Any]] | None = None
    active_opened_by: Tuple[Dict[str, Any], ...] = (
        {
            "kind": "horizon_start",
            "label": "Scan start",
        },
    )

    for day in _date_range(start, end):
        row = _dasha_for_day(dasha_rows, day)
        dasha_planets = (
            row["mahadasha"], row["antardasha"], row["pratyantardasha"]
        )
        states = _transit_states_for_day(transit_calculator, chart, day, dasha_planets)
        daily_states[day.isoformat()] = states
        signature = _transit_signature(row, states)
        states_by_signature.setdefault(signature, states)

        if active_start is None:
            active_start, active_signature, active_row, active_states = (
                day, signature, row, states
            )
            continue
        if signature == active_signature:
            continue
        assert active_row is not None and active_states is not None
        boundary = _window_boundary_changes(active_row, active_states, row, states)
        windows.append(
            PredictionWindow(
                start_date=active_start.isoformat(),
                end_date=(day - timedelta(days=1)).isoformat(),
                mahadasha=active_row["mahadasha"],
                antardasha=active_row["antardasha"],
                pratyantardasha=active_row["pratyantardasha"],
                transit_signature=active_signature,
                opened_by=active_opened_by,
                closed_by=boundary,
            )
        )
        active_start, active_signature, active_row, active_states = (
            day, signature, row, states
        )
        active_opened_by = boundary or (
            {
                "kind": "signature_shift",
                "label": "Transit signature shift",
            },
        )

    if active_start is None or active_row is None:
        raise PredictionCalculationError("No deterministic prediction windows were constructed")
    windows.append(
        PredictionWindow(
            start_date=active_start.isoformat(),
            end_date=end.isoformat(),
            mahadasha=active_row["mahadasha"],
            antardasha=active_row["antardasha"],
            pratyantardasha=active_row["pratyantardasha"],
            transit_signature=active_signature,
            opened_by=active_opened_by,
            closed_by=(
                {
                    "kind": "horizon_end",
                    "label": "Horizon end",
                },
            ),
        )
    )
    return windows, states_by_signature, daily_states


def build_calculation_context(
    birth: BirthChartInput,
    start: date,
    end: date,
    *,
    include_exact_transit_returns: bool = False,
) -> CalculationContext:
    from .natal_promise import build_natal_promises
    from .transit_returns import build_exact_natal_return_passes

    try:
        chart = ChartCalculator({}).calculate_chart(
            SimpleNamespace(**birth.to_calculator_dict())
        )
        _validate_chart(chart)
        yogi_points = YogiCalculator(chart).calculate_yogi_points(birth.to_calculator_dict())
        gandanta = GandantaCalculator(chart).calculate_gandanta_analysis()
        natal_dignities = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()
        natal_promises, validated_yogas = build_natal_promises(
            chart, natal_dignities, yogi_points, gandanta
        )
        ascendant_sign = int(float(chart["ascendant"]) / 30.0)
        badhaka_lord = BadhakaCalculator(chart).get_badhaka_lord(ascendant_sign)
        # Profile 2.1 keeps divisional confirmation out of the decisive path
        # until its event-specific rules have golden-chart validation.
        divisional_charts: Dict[str, Dict[str, Any]] = {}
    except PredictionCalculationError:
        raise
    except Exception as exc:
        raise PredictionCalculationError("Natal Parashari context calculation failed") from exc

    windows, states_by_signature, daily_states = _build_windows(birth, chart, start, end)
    transit_return_passes = (
        build_exact_natal_return_passes(chart, windows, daily_states, start, end)
        if include_exact_transit_returns
        else {}
    )
    return CalculationContext(
        birth=birth,
        chart=chart,
        natal_dignities=natal_dignities,
        yogi_points=yogi_points,
        gandanta=gandanta,
        badhaka_lord=badhaka_lord,
        windows=windows,
        transit_states_by_signature=states_by_signature,
        divisional_charts=divisional_charts,
        daily_transit_states=daily_states,
        transit_return_passes=transit_return_passes,
        natal_promises=natal_promises,
        validated_yogas=validated_yogas,
    )
