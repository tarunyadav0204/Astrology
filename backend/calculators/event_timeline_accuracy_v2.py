"""Deterministic timing evidence and output validation for Event Timeline V2.

The legacy timeline asks an LLM to infer timing directly from a broad context.
V2 computes a compact, target-period evidence ledger first.  The LLM may
narrate that ledger, but it may not create uncited event candidates.
"""

from __future__ import annotations

import calendar
import copy
import hashlib
import os
import re
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from calculators.vedic_graha_drishti import get_aspect_houses_for_planet


LEGACY_ENGINE_VERSION = "legacy_v1"
ACCURACY_ENGINE_VERSION = "accuracy_v2"
ACCURACY_V3_ENGINE_VERSION = "accuracy_v3"
METHODOLOGY_VERSION = "event_timeline_accuracy_2026_09_v2"
EVIDENCE_VERSION = "target_period_ledger_v1"

_LEVELS: Tuple[Tuple[str, int], ...] = (
    ("mahadasha", 4),
    ("antardasha", 3),
    ("pratyantardasha", 2),
    ("sookshma", 1),
)
_PLANETS = ("Saturn", "Rahu", "Ketu", "Jupiter", "Mars", "Sun", "Moon", "Mercury", "Venus")
_ASPECT_OFFSETS = {
    "Saturn": (2, 6, 9),
    "Mars": (3, 6, 7),
    "Jupiter": (4, 6, 8),
    "Rahu": (6,),
    "Ketu": (6,),
    "Sun": (6,),
    "Moon": (6,),
    "Mercury": (6,),
    "Venus": (6,),
}
_TARA_NAMES = {
    1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema", 5: "Pratyak",
    6: "Sadhana", 7: "Naidhana", 8: "Mitra", 9: "Ati Mitra",
}
_PROHIBITED_CERTAINTY = re.compile(
    r"\b(guaranteed|guarantee|certain to|will definitely|must happen|"
    r"million[- ]dollar|on fire|supreme activation)\b",
    re.IGNORECASE,
)


def selected_engine_version() -> str:
    configured = os.getenv("EVENT_TIMELINE_ENGINE_VERSION")
    if configured is None or not configured.strip():
        return ACCURACY_V3_ENGINE_VERSION
    raw = configured.strip().lower()
    if raw in {"accuracy_v3", "v3", ACCURACY_V3_ENGINE_VERSION}:
        return ACCURACY_V3_ENGINE_VERSION
    if raw in {"accuracy", "v2", ACCURACY_ENGINE_VERSION}:
        return ACCURACY_ENGINE_VERSION
    # Unknown or misspelled values fail safely to the established implementation.
    return LEGACY_ENGINE_VERSION


def is_accuracy_v2() -> bool:
    return selected_engine_version() == ACCURACY_ENGINE_VERSION


def _planet_from_level(row: Any) -> Optional[str]:
    if isinstance(row, dict):
        value = row.get("planet")
    else:
        value = row
    value = str(value or "").strip()
    return value or None


def _dasha_stack(dasha: Dict[str, Any]) -> Dict[str, Optional[str]]:
    return {level: _planet_from_level(dasha.get(level)) for level, _weight in _LEVELS}


def build_target_year_dasha_facts(dasha_calc: Any, birth_data: Dict[str, Any], year: int) -> Dict[str, Any]:
    """Return target-year dasha anchors and calendar-day boundary changes."""
    points = {
        "start": datetime(year, 1, 1, 12),
        "middle": datetime(year, 7, 1, 12),
        "end": datetime(year, 12, 31, 12),
    }
    samples = {
        label: {"date": dt.strftime("%Y-%m-%d"), **_dasha_stack(dasha_calc.calculate_current_dashas(birth_data, dt, strict=True))}
        for label, dt in points.items()
    }
    monthly: Dict[str, Dict[str, Any]] = {}
    for month in range(1, 13):
        last = calendar.monthrange(year, month)[1]
        dt = datetime(year, month, min(15, last), 12)
        monthly[str(month)] = {"date": dt.strftime("%Y-%m-%d"), **_dasha_stack(dasha_calc.calculate_current_dashas(birth_data, dt, strict=True))}

    changes: List[Dict[str, Any]] = []
    previous: Optional[Dict[str, Optional[str]]] = None
    cursor = datetime(year, 1, 1, 12)
    end = datetime(year, 12, 31, 12)
    while cursor <= end:
        stack = _dasha_stack(dasha_calc.calculate_current_dashas(birth_data, cursor, strict=True))
        if previous is not None and stack != previous:
            changed_levels = [level for level, _weight in _LEVELS if stack.get(level) != previous.get(level)]
            changes.append({
                "date": cursor.strftime("%Y-%m-%d"),
                "changed_levels": changed_levels,
                "from": previous,
                "to": stack,
            })
        previous = stack
        cursor += timedelta(days=1)
    return {"year": year, "samples": samples, "monthly": monthly, "changes": changes, "resolution": "calendar_day"}


def build_target_month_dasha_facts(
    dasha_calc: Any,
    birth_data: Dict[str, Any],
    year: int,
    month: int,
) -> Dict[str, Any]:
    """Return the same ledger inputs as the yearly scanner for one month only."""
    last = calendar.monthrange(year, month)[1]
    points = {
        "start": datetime(year, month, 1, 12),
        "middle": datetime(year, month, min(15, last), 12),
        "end": datetime(year, month, last, 12),
    }
    samples = {
        label: {"date": dt.strftime("%Y-%m-%d"), **_dasha_stack(dasha_calc.calculate_current_dashas(birth_data, dt, strict=True))}
        for label, dt in points.items()
    }
    changes: List[Dict[str, Any]] = []
    previous: Optional[Dict[str, Optional[str]]] = None
    for day in range(1, last + 1):
        cursor = datetime(year, month, day, 12)
        stack = _dasha_stack(dasha_calc.calculate_current_dashas(birth_data, cursor, strict=True))
        if previous is not None and stack != previous:
            changes.append({
                "date": cursor.strftime("%Y-%m-%d"),
                "changed_levels": [level for level, _weight in _LEVELS if stack.get(level) != previous.get(level)],
                "from": previous,
                "to": stack,
            })
        previous = stack
    return {
        "year": year,
        "selected_month": month,
        "samples": samples,
        "monthly": {str(month): samples["middle"]},
        "changes": changes,
        "resolution": "calendar_day",
    }


def _snapshot(transit_calc: Any, asc_lon: float, dt: datetime, planet: str) -> Dict[str, Any]:
    state = transit_calc.get_planet_state(dt, planet)
    lon = float(state["longitude"])
    nk = transit_calc.get_nakshatra_from_longitude(lon)
    return {
        "date": dt.strftime("%Y-%m-%d"),
        "longitude": round(lon % 360.0, 6),
        "house": int(transit_calc.calculate_house_from_longitude(lon, asc_lon)),
        "sign": int(lon / 30) + 1,
        "degree": round(lon % 30, 3),
        "nakshatra": nk.get("name"),
        "nakshatra_index": int(nk.get("index", 0)),
        "pada": nk.get("pada"),
        "retrograde": bool(state.get("retrograde")),
        "speed": round(float(state.get("speed") or 0.0), 8),
    }


def build_month_transit_facts(
    transit_calc: Any,
    birth_data: Dict[str, Any],
    year: int,
    month: int,
    *,
    natal_positions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compact daily-scanned transit segments for a target month."""
    natal = natal_positions or transit_calc._calculate_natal_positions(birth_data)
    if not natal or natal.get("ascendant_longitude") is None:
        raise ValueError("Natal ascendant unavailable for target-month transit calculation")
    asc_lon = float(natal["ascendant_longitude"])
    last = calendar.monthrange(year, month)[1]
    by_planet: Dict[str, Dict[str, Any]] = {}
    for planet in _PLANETS:
        rows = [_snapshot(transit_calc, asc_lon, datetime(year, month, day, 12), planet) for day in range(1, last + 1)]
        segments: List[Dict[str, Any]] = []
        segment_start = rows[0]
        previous = rows[0]
        station_events: List[Dict[str, Any]] = []
        for row in rows[1:]:
            key = (row["sign"], row["house"], row["nakshatra"], row["pada"], row["retrograde"])
            prev_key = (previous["sign"], previous["house"], previous["nakshatra"], previous["pada"], previous["retrograde"])
            if key != prev_key:
                segments.append({
                    **segment_start,
                    "end_date": previous["date"],
                    "end_longitude": previous["longitude"],
                    "end_speed": previous["speed"],
                })
                segment_start = row
            if row["retrograde"] != previous["retrograde"]:
                station_events.append({
                    "date": row["date"],
                    "planet": planet,
                    "direction": "retrograde" if row["retrograde"] else "direct",
                    "longitude": row["longitude"],
                    "resolution": "calendar_day_direction_change",
                })
            previous = row
        segments.append({
            **segment_start,
            "end_date": rows[-1]["date"],
            "end_longitude": rows[-1]["longitude"],
            "end_speed": rows[-1]["speed"],
        })
        by_planet[planet] = {
            "start": rows[0],
            "middle": rows[min(14, len(rows) - 1)],
            "end": rows[-1],
            "segments": segments,
            "change_dates": [segment["date"] for segment in segments[1:]],
            "station_events": station_events,
            "daily": rows,
        }
    return {
        "year": year,
        "month": month,
        "resolution": "calendar_day_at_12UT",
        "ascendant_longitude": asc_lon,
        "planets": by_planet,
        "aspect_model": {
            planet: get_aspect_houses_for_planet(planet)
            for planet in _PLANETS
        },
    }


def build_target_year_transit_facts(
    transit_calc: Any,
    birth_data: Dict[str, Any],
    year: int,
    *,
    month_completed_callback: Optional[Callable[[int], None]] = None,
) -> Dict[str, Any]:
    natal = transit_calc._calculate_natal_positions(birth_data)
    if not natal:
        raise ValueError("Natal positions unavailable for target-year transit calculation")
    result: Dict[str, Any] = {}
    for month in range(1, 13):
        result[str(month)] = build_month_transit_facts(
            transit_calc, birth_data, year, month, natal_positions=natal
        )
        if month_completed_callback:
            month_completed_callback(month)
    return result


def _aspected_houses(planet: str, house: int) -> List[int]:
    return [((int(house) + offset - 1) % 12) + 1 for offset in _ASPECT_OFFSETS.get(planet, (6,))]


def _sav_by_sign(context: Dict[str, Any]) -> Dict[int, int]:
    raw = (((context.get("ashtakavarga") or {}).get("d1_rashi") or {}).get("sarvashtakavarga") or {})
    if isinstance(raw.get("sarvashtakavarga"), dict):
        raw = raw["sarvashtakavarga"]
    out: Dict[int, int] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            try:
                idx = int(key)
                sign = idx + 1 if 0 <= idx <= 11 else idx
                out[sign] = int(value)
            except (TypeError, ValueError):
                continue
    return out


def _stable_evidence_id(year: int, month: int, payload: Dict[str, Any], ordinal: int) -> str:
    basis = repr(sorted(payload.items())).encode("utf-8", "ignore")
    digest = hashlib.sha1(basis).hexdigest()[:7]
    return f"ET2-{year}{month:02d}-{ordinal:02d}-{digest}"


def _dasha_segments_for_month(dasha_facts: Dict[str, Any], year: int, month: int) -> List[Dict[str, Any]]:
    month_start = datetime(year, month, 1)
    month_end = datetime(year, month, calendar.monthrange(year, month)[1])
    start_sample = ((dasha_facts.get("samples") or {}).get("start") or {})
    state = {level: start_sample.get(level) for level, _weight in _LEVELS}
    changes: List[Tuple[datetime, Dict[str, Any]]] = []
    for row in dasha_facts.get("changes") or []:
        try:
            change_date = datetime.strptime(str(row.get("date")), "%Y-%m-%d")
        except (TypeError, ValueError):
            continue
        changes.append((change_date, row))
    changes.sort(key=lambda item: item[0])
    for change_date, row in changes:
        if change_date < month_start:
            next_state = row.get("to") if isinstance(row.get("to"), dict) else {}
            state.update({level: next_state.get(level) for level, _weight in _LEVELS})

    segments: List[Dict[str, Any]] = []
    cursor = month_start
    for change_date, row in changes:
        if change_date < month_start or change_date > month_end:
            continue
        if change_date > cursor:
            segments.append({
                "start_date": cursor.strftime("%Y-%m-%d"),
                "end_date": (change_date - timedelta(days=1)).strftime("%Y-%m-%d"),
                **state,
            })
        next_state = row.get("to") if isinstance(row.get("to"), dict) else {}
        state.update({level: next_state.get(level) for level, _weight in _LEVELS})
        cursor = change_date
    if cursor <= month_end:
        segments.append({
            "start_date": cursor.strftime("%Y-%m-%d"),
            "end_date": month_end.strftime("%Y-%m-%d"),
            **state,
        })
    return segments


def build_evidence_ledger(
    context: Dict[str, Any],
    year: int,
    dasha_facts: Dict[str, Any],
    transit_facts: Dict[str, Any],
    *,
    month_ids: Optional[Iterable[int]] = None,
    max_transit_segments_per_planet: Optional[int] = 8,
) -> Dict[str, Any]:
    d1 = context.get("d1_chart") or {}
    natal_planets = d1.get("planets") or {}
    lordships = context.get("house_lordships") or {}
    sav = _sav_by_sign(context)
    moon_lon = float(((natal_planets.get("Moon") or {}).get("longitude") or 0.0))
    moon_nk = int(moon_lon / (360.0 / 27.0))
    ledger: Dict[str, Any] = {"version": EVIDENCE_VERSION, "year": year, "months": {}}

    selected_months = sorted(set(int(month) for month in (month_ids or range(1, 13))))
    for month in selected_months:
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid event timeline month: {month}")
        rows: List[Dict[str, Any]] = []
        stack = copy.deepcopy((dasha_facts.get("monthly") or {}).get(str(month)) or {})
        dasha_segments = _dasha_segments_for_month(dasha_facts, year, month)
        month_transits = ((transit_facts.get(str(month)) or {}).get("planets") or {})
        for dasha_segment in dasha_segments:
            dasha_start = datetime.strptime(dasha_segment["start_date"], "%Y-%m-%d")
            dasha_end = datetime.strptime(dasha_segment["end_date"], "%Y-%m-%d")
            for level, level_weight in _LEVELS:
                planet = str(dasha_segment.get(level) or "").strip()
                if not planet or planet not in month_transits:
                    continue
                natal = natal_planets.get(planet) or {}
                planet_segments = month_transits[planet].get("segments") or []
                if max_transit_segments_per_planet is not None:
                    planet_segments = planet_segments[:max_transit_segments_per_planet]
                for segment in planet_segments:
                    try:
                        transit_start = datetime.strptime(str(segment.get("date")), "%Y-%m-%d")
                        transit_end = datetime.strptime(str(segment.get("end_date")), "%Y-%m-%d")
                    except (TypeError, ValueError):
                        continue
                    overlap_start = max(dasha_start, transit_start)
                    overlap_end = min(dasha_end, transit_end)
                    if overlap_end < overlap_start:
                        continue
                    transit_house = int(segment.get("house") or 0)
                    transit_sign = int(segment.get("sign") or 0)
                    nk_idx = int(segment.get("nakshatra_index") or 0)
                    tara_number = ((nk_idx - moon_nk) % 27) % 9 + 1
                    score = level_weight + (1 if transit_house in set(lordships.get(planet) or []) else 0)
                    if segment.get("nakshatra") == (natal.get("nakshatra") or {}).get("name"):
                        score += 1
                    row = {
                        "kind": "dasha_lord_transit",
                        "dasha_level": level,
                        "planet": planet,
                        "start_date": overlap_start.strftime("%Y-%m-%d"),
                        "end_date": overlap_end.strftime("%Y-%m-%d"),
                        "dasha_segment_start": dasha_segment.get("start_date"),
                        "dasha_segment_end": dasha_segment.get("end_date"),
                        "transit_house": transit_house,
                        "transit_sign": transit_sign,
                        "transit_nakshatra": segment.get("nakshatra"),
                        "tara": _TARA_NAMES.get(tara_number),
                        "natal_house": natal.get("house"),
                        "lordships": list(lordships.get(planet) or []),
                        "aspected_houses": _aspected_houses(planet, transit_house),
                        "sav": sav.get(transit_sign),
                        "score": score,
                        "interpretation": "supporting_evidence_only",
                    }
                    rows.append(row)

        # Saturn/Jupiter overlap is supporting evidence, never an automatic event.
        sat = (month_transits.get("Saturn") or {}).get("middle") or {}
        jup = (month_transits.get("Jupiter") or {}).get("middle") or {}
        if sat.get("house") and jup.get("house"):
            overlap = sorted(set(_aspected_houses("Saturn", int(sat["house"]))) & set(_aspected_houses("Jupiter", int(jup["house"]))))
            if overlap:
                rows.append({
                    "kind": "saturn_jupiter_double_transit",
                    "planets": ["Saturn", "Jupiter"],
                    "start_date": f"{year}-{month:02d}-01",
                    "end_date": f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}",
                    "houses": overlap,
                    "score": 2,
                    "interpretation": "supporting_evidence_only_not_a_guarantee",
                })

        rows.sort(key=lambda row: (-int(row.get("score") or 0), str(row.get("start_date") or "")))
        for idx, row in enumerate(rows, start=1):
            row["evidence_id"] = _stable_evidence_id(year, month, row, idx)
        max_score = max([int(row.get("score") or 0) for row in rows] or [0])
        ledger["months"][str(month)] = {
            "dasha_stack": stack,
            "dasha_segments": dasha_segments,
            "evidence": rows,
            "transit_daily": {
                planet: list((data or {}).get("daily") or [])
                for planet, data in month_transits.items()
            },
            "transit_stations": [
                event
                for data in month_transits.values()
                for event in ((data or {}).get("station_events") or [])
            ],
            "transit_aspect_model": (transit_facts.get(str(month)) or {}).get("aspect_model") or {},
            "max_support_score": max_score,
            "quiet_month_allowed": True,
        }
    return ledger


def validate_v2_payload(
    payload: Dict[str, Any],
    ledger: Dict[str, Any],
    *,
    year: int,
    selected_month: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Fail closed on uncited/invalid events while preserving the mobile shape."""
    warnings: List[str] = []
    out = copy.deepcopy(payload) if isinstance(payload, dict) else {}
    months = out.get("monthly_predictions")
    if not isinstance(months, list):
        months = []
    allowed_months = {selected_month} if selected_month else set(range(1, 13))
    max_events = 6 if selected_month else 3
    normalized: Dict[int, Dict[str, Any]] = {}

    def soften(value: Any, month_id: int) -> Any:
        if not isinstance(value, str):
            return value
        if not _PROHIBITED_CERTAINTY.search(value):
            return value
        warnings.append(f"Softened certainty language in month {month_id}")
        return _PROHIBITED_CERTAINTY.sub("is strongly indicated", value)

    for month_row in months:
        if not isinstance(month_row, dict):
            warnings.append("Dropped a non-object month entry")
            continue
        try:
            month_id = int(month_row.get("month_id"))
        except (TypeError, ValueError):
            warnings.append("Dropped a month with an invalid month_id")
            continue
        if month_id not in allowed_months or month_id in normalized:
            warnings.append(f"Dropped unexpected or duplicate month {month_id}")
            continue
        evidence_rows = ((ledger.get("months") or {}).get(str(month_id)) or {}).get("evidence") or []
        allowed_ids = {str(row.get("evidence_id")) for row in evidence_rows if row.get("evidence_id")}
        clean_events: List[Dict[str, Any]] = []
        for event in month_row.get("events") or []:
            if not isinstance(event, dict):
                continue
            cited = event.get("evidence_ids") or []
            if isinstance(cited, str):
                cited = [cited]
            cited = [str(value) for value in cited if str(value) in allowed_ids]
            if not cited:
                warnings.append(f"Dropped month {month_id} event without valid deterministic evidence")
                continue
            prediction = " ".join(str(event.get("prediction") or "").split())
            if not prediction:
                continue
            prediction = soften(prediction, month_id)
            start = str(event.get("start_date") or "")
            end = str(event.get("end_date") or "")
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                end_dt = datetime.strptime(end, "%Y-%m-%d")
                if start_dt.year != year or end_dt.year != year or start_dt.month != month_id or end_dt.month != month_id or end_dt < start_dt:
                    raise ValueError
            except ValueError:
                warnings.append(f"Dropped month {month_id} event with an invalid execution window")
                continue
            intensity = str(event.get("intensity") or "Low").title()
            if intensity not in {"High", "Medium", "Low"}:
                intensity = "Low"
            cited_rows = [row for row in evidence_rows if row.get("evidence_id") in cited]
            overlaps_evidence = False
            for cited_row in cited_rows:
                try:
                    evidence_start = datetime.strptime(str(cited_row.get("start_date")), "%Y-%m-%d")
                    evidence_end = datetime.strptime(str(cited_row.get("end_date")), "%Y-%m-%d")
                    if start_dt <= evidence_end and end_dt >= evidence_start:
                        overlaps_evidence = True
                        break
                except (TypeError, ValueError):
                    continue
            if not overlaps_evidence:
                warnings.append(f"Dropped month {month_id} event outside its cited evidence window")
                continue
            max_score = max([int(row.get("score") or 0) for row in cited_rows] or [0])
            if intensity == "High" and max_score < 5:
                intensity = "Medium"
                warnings.append(f"Downgraded unsupported High intensity in month {month_id}")
            manifestations = []
            for manifestation in (event.get("possible_manifestations") or [])[:2]:
                if isinstance(manifestation, dict):
                    manifestations.append({
                        **manifestation,
                        "scenario": soften(manifestation.get("scenario"), month_id),
                        "reasoning": soften(manifestation.get("reasoning"), month_id),
                    })
            clean_events.append({
                **event,
                "prediction": prediction,
                "activation_reasoning": soften(event.get("activation_reasoning"), month_id),
                "trigger_logic": soften(event.get("trigger_logic"), month_id),
                "possible_manifestations": manifestations,
                "intensity": intensity,
                "evidence_ids": cited,
            })
            if len(clean_events) >= max_events:
                break
        normalized[month_id] = {
            **month_row,
            "events": clean_events,
            "prediction_state": "supported_candidates" if clean_events else "insufficient_evidence",
        }

    required = [selected_month] if selected_month else list(range(1, 13))
    for month_id in required:
        if month_id not in normalized:
            normalized[month_id] = {
                "month_id": month_id,
                "focus_areas": [],
                "events": [],
                "prediction_state": "insufficient_evidence",
            }
    out["monthly_predictions"] = [normalized[m] for m in sorted(normalized)]
    out["validation_warnings"] = warnings
    return out, warnings
