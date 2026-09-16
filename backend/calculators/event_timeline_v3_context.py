"""Minimal calculation context for Event Timeline V3.

This deliberately avoids ChatContextBuilder. V3 consumes only D1 placements,
classical house lordships, ten event/subject-specific vargas, D1 SAV, target-period
Vimshottari/transits, KP evidence, and user facts supplied separately.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from types import SimpleNamespace
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Mapping

from calculators.divisional_chart_calculator import DivisionalChartCalculator


V3_CONTEXT_VERSION = "event_timeline_minimal_context_v3_d12_d16"

_CACHE_LOCK = threading.RLock()
_NATAL_CACHE: "OrderedDict[str, tuple[float, Dict[str, Any]]]" = OrderedDict()
_KP_CACHE: "OrderedDict[str, tuple[float, Dict[str, Any]]]" = OrderedDict()

_SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
_VARGAS = {
    2: "d2_hora",
    3: "d3_drekkana",
    4: "d4_chaturthamsa",
    7: "d7_saptamsa",
    9: "d9_navamsa",
    10: "d10_dasamsa",
    12: "d12_dwadasamsa",
    16: "d16_shodasamsa",
    24: "d24_chaturvimsamsa",
    30: "d30_trimsamsa",
}


def _cache_settings() -> tuple[int, int]:
    ttl = max(300, int(os.getenv("EVENT_TIMELINE_V3_NATAL_CACHE_TTL_S", "43200") or 43200))
    size = max(8, int(os.getenv("EVENT_TIMELINE_V3_NATAL_CACHE_MAX_ENTRIES", "128") or 128))
    return ttl, size


def _birth_key(birth_data: Mapping[str, Any], namespace: str) -> str:
    identifying_calculation_inputs = {
        key: birth_data.get(key)
        for key in (
            "date", "time", "latitude", "longitude", "timezone",
            "birth_time_source", "time_source", "birth_time_verified",
            "birth_time_uncertainty_minutes", "time_uncertainty_minutes", "uncertainty_minutes",
        )
    }
    raw = json.dumps(
        {"namespace": namespace, "version": V3_CONTEXT_VERSION, **identifying_calculation_inputs},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()


def _cache_get(cache: OrderedDict, key: str) -> Dict[str, Any] | None:
    ttl, _size = _cache_settings()
    with _CACHE_LOCK:
        row = cache.get(key)
        if row is None:
            return None
        created, value = row
        if time.monotonic() - created > ttl:
            cache.pop(key, None)
            return None
        cache.move_to_end(key)
        return copy.deepcopy(value)


def _cache_put(cache: OrderedDict, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
    _ttl, size = _cache_settings()
    with _CACHE_LOCK:
        cache[key] = (time.monotonic(), copy.deepcopy(value))
        cache.move_to_end(key)
        while len(cache) > size:
            cache.popitem(last=False)
    return copy.deepcopy(value)


def house_lordships(ascendant_longitude: float) -> Dict[str, list[int]]:
    ascendant_sign = int(float(ascendant_longitude) / 30.0) % 12
    result: Dict[str, list[int]] = {}
    for house in range(1, 13):
        sign = (ascendant_sign + house - 1) % 12
        result.setdefault(_SIGN_LORDS[sign], []).append(house)
    return result


def build_minimal_v3_context(
    birth_data: Mapping[str, Any],
    *,
    chart_calculator: Any,
    ashtakavarga_calculator_cls: Any,
) -> Dict[str, Any]:
    """Calculate only natal fields consumed by the V3 resolver."""
    cache_key = _birth_key(birth_data, "natal")
    cached = _cache_get(_NATAL_CACHE, cache_key)
    if cached is not None:
        cached["cache_status"] = "hit"
        return cached

    chart = chart_calculator.calculate_chart(SimpleNamespace(**dict(birth_data)))
    d1_chart = copy.deepcopy(chart)
    divisional_calculator = DivisionalChartCalculator(chart)
    divisional_charts: Dict[str, Any] = {}
    for division, key in _VARGAS.items():
        divisional_charts[key] = divisional_calculator.calculate_divisional_chart(division)

    # SAV is retained because it is part of each deterministic ledger row and
    # therefore contributes to stable evidence IDs, even though V3 does not use
    # it as a standalone event gate.
    av_calculator = ashtakavarga_calculator_cls(dict(birth_data), chart)
    sav = av_calculator.calculate_sarvashtakavarga()
    try:
        advanced_ashtakavarga = av_calculator.calculate_advanced_ashtakavarga()
    except (AttributeError, KeyError, TypeError, ValueError):
        advanced_ashtakavarga = {
            "available": False,
            "reason": "advanced_ashtakavarga_not_supported_by_calculator",
        }
    uncertainty_raw = (
        birth_data.get("birth_time_uncertainty_minutes")
        or birth_data.get("time_uncertainty_minutes")
        or birth_data.get("uncertainty_minutes")
    )
    try:
        uncertainty_minutes = max(0, int(uncertainty_raw)) if uncertainty_raw is not None else None
    except (TypeError, ValueError):
        uncertainty_minutes = None
    time_source = str(
        birth_data.get("birth_time_source") or birth_data.get("time_source") or "unknown"
    ).strip().lower()
    result = {
        "context_version": V3_CONTEXT_VERSION,
        "cache_status": "miss",
        "d1_chart": d1_chart,
        "house_lordships": house_lordships(float(chart.get("ascendant") or 0.0)),
        "divisional_charts": divisional_charts,
        "ashtakavarga": {
            "d1_rashi": {"sarvashtakavarga": sav},
            "advanced": advanced_ashtakavarga,
        },
        "birth_time_reliability": {
            "source": time_source,
            "uncertainty_minutes": uncertainty_minutes,
            "verified": bool(birth_data.get("birth_time_verified")) or time_source in {"documented", "birth_certificate", "hospital_record"},
            "available": uncertainty_minutes is not None or time_source != "unknown",
        },
    }
    return _cache_put(_NATAL_CACHE, cache_key, result)


def build_target_year_supporting_context(
    birth_data: Mapping[str, Any],
    *,
    chart: Mapping[str, Any],
    chart_calculator: Any,
    target_year: int,
    month_ids: list[int],
) -> Dict[str, Any]:
    """Run existing independent timing calculators for the requested period."""
    from calculators.chara_dasha_calculator import CharaDashaCalculator
    from calculators.kalachakra_dasha_calculator import KalachakraDashaCalculator
    from calculators.sudarshana_dasha_calculator import SudarshanaDashaCalculator
    from calculators.varshphal_calculator import VarshphalCalculator
    from calculators.yogini_dasha_calculator import YoginiDashaCalculator

    output: Dict[str, Any] = {
        "version": "event_timeline_supporting_calculators_v1",
        "independence_groups": {
            "chara": "jaimini_sign_dasha",
            "yogini": "nakshatra_dasha",
            "kalachakra": "nakshatra_pada_dasha",
            "varshphal": "solar_return_subset",
            "sudarshana": "annual_age_clock",
        },
        "limitations": [],
    }
    birth = dict(birth_data)
    selected_months = sorted(set(int(month) for month in month_ids if 1 <= int(month) <= 12))
    try:
        varshphal = VarshphalCalculator(chart_calculator).calculate_varshphal(birth, target_year)
        output["varshphal"] = {
            "available": True,
            "year": target_year,
            "return_time": varshphal.get("return_time"),
            "chart": varshphal.get("chart"),
            "muntha": varshphal.get("muntha"),
            "year_lord": varshphal.get("year_lord"),
            "mudda_dasha": varshphal.get("mudda_dasha") or [],
            "scope": "solar_return_muntha_year_lord_mudda_only",
            "not_available": ["panchavargiya_bala", "tajika_aspects", "sahams", "verified_varshesha_selection"],
        }
    except Exception as exc:
        output["varshphal"] = {"available": False, "error": type(exc).__name__}
    try:
        dob = datetime.strptime(str(birth["date"]), "%Y-%m-%d")
        chara = CharaDashaCalculator(dict(chart)).calculate_dasha(
            dob, focus_date=datetime(target_year, 7, 1, 12)
        )
        year_start = datetime(target_year, 1, 1)
        year_end = datetime(target_year, 12, 31, 23, 59, 59)
        periods = []
        for period in chara.get("periods") or []:
            start = datetime.strptime(str(period.get("start_date")), "%Y-%m-%d")
            end = datetime.strptime(str(period.get("end_date")), "%Y-%m-%d")
            if start <= year_end and end >= year_start:
                periods.append(period)
        output["chara_dasha"] = {"available": bool(periods), "system": chara.get("system"), "periods": periods}
    except Exception as exc:
        output["chara_dasha"] = {"available": False, "error": type(exc).__name__}
    moon_longitude = float((((chart.get("planets") or {}).get("Moon") or {}).get("longitude") or 0.0))
    yogini = YoginiDashaCalculator()
    kalachakra = KalachakraDashaCalculator(dict(chart))
    output["monthly"] = {}
    for month in selected_months:
        focus = datetime(target_year, month, 15, 12)
        month_row: Dict[str, Any] = {}
        try:
            value = yogini.calculate_current_yogini(birth, moon_longitude, focus)
            month_row["yogini"] = {"available": bool(value), **(value or {})}
        except Exception as exc:
            month_row["yogini"] = {"available": False, "error": type(exc).__name__}
        try:
            value = kalachakra.calculate_kalchakra_dasha(birth, focus)
            if value.get("error"):
                raise ValueError(str(value["error"]))
            month_row["kalachakra"] = {"available": True, **value}
        except Exception as exc:
            month_row["kalachakra"] = {"available": False, "error": type(exc).__name__}
        output["monthly"][str(month)] = month_row
    try:
        output["sudarshana"] = {
            "available": True,
            **SudarshanaDashaCalculator(dict(chart), birth).calculate_precision_triggers(target_year),
        }
    except Exception as exc:
        output["sudarshana"] = {"available": False, "error": type(exc).__name__}
    output["limitations"].append(
        "Supporting systems remain capped comparators; they cannot create an event or multiply confidence when they reuse the same signal."
    )
    return output


def build_birth_time_sensitivity(
    birth_data: Mapping[str, Any],
    *,
    chart_calculator: Any,
    dasha_calculator: Any,
    target_year: int,
) -> Dict[str, Any]:
    """Recalculate sensitive structures at the supplied birth-time bounds."""
    raw_uncertainty = (
        birth_data.get("birth_time_uncertainty_minutes")
        or birth_data.get("time_uncertainty_minutes")
        or birth_data.get("uncertainty_minutes")
    )
    try:
        uncertainty = max(0, min(60, int(raw_uncertainty)))
    except (TypeError, ValueError):
        return {"available": False, "boundary_risk": "unknown", "reason": "birth_time_uncertainty_not_supplied"}
    if uncertainty == 0:
        return {"available": True, "boundary_risk": "low", "uncertainty_minutes": 0, "samples": []}
    base = datetime.strptime(
        f"{str(birth_data.get('date'))[:10]} {str(birth_data.get('time') or '00:00')[:8]}",
        "%Y-%m-%d %H:%M:%S" if len(str(birth_data.get("time") or "").split(":")) >= 3 else "%Y-%m-%d %H:%M",
    )
    samples: List[Dict[str, Any]] = []
    from app.kp.services.chart_service import KPChartService

    for offset in (-uncertainty, 0, uncertainty):
        moment = base + timedelta(minutes=offset)
        shifted = {
            **dict(birth_data),
            "date": moment.strftime("%Y-%m-%d"),
            "time": moment.strftime("%H:%M:%S"),
        }
        chart = chart_calculator.calculate_chart(SimpleNamespace(**shifted))
        divisional = DivisionalChartCalculator(chart)
        varga_ascendants = {}
        for division in (4, 7, 9, 10, 24, 30):
            value = divisional.calculate_divisional_chart(division)
            inner = value.get("divisional_chart", value) if isinstance(value, Mapping) else {}
            ascendant = inner.get("ascendant")
            varga_ascendants[f"D{division}"] = int(float(ascendant) // 30) if ascendant is not None else None
        moon = float((((chart.get("planets") or {}).get("Moon") or {}).get("longitude") or 0.0))
        kp = KPChartService.calculate_kp_chart(
            shifted.get("date"), shifted.get("time"), shifted.get("latitude"),
            shifted.get("longitude"), shifted.get("timezone"),
        )
        dasha = dasha_calculator.calculate_current_dashas(
            shifted, datetime(target_year, 7, 1, 12), strict=True
        )
        samples.append({
            "offset_minutes": offset,
            "local_time": shifted["time"],
            "lagna_sign": int(float(chart.get("ascendant") or 0.0) // 30),
            "moon_nakshatra": int(moon // (360.0 / 27.0)),
            "varga_ascendant_signs": varga_ascendants,
            "kp_cusp_sub_lords": {
                str(house): (row or {}).get("sub_lord")
                for house, row in (kp.get("cusp_lords") or {}).items()
            },
            "midyear_dasha_stack": {
                level: str((dasha.get(level) or {}).get("planet") or "")
                for level in ("mahadasha", "antardasha", "pratyantardasha")
            },
        })
    lagna_changed = len({row["lagna_sign"] for row in samples}) > 1
    moon_changed = len({row["moon_nakshatra"] for row in samples}) > 1
    dasha_changed = len({json.dumps(row["midyear_dasha_stack"], sort_keys=True) for row in samples}) > 1
    varga_changed = any(
        len({row["varga_ascendant_signs"].get(varga) for row in samples}) > 1
        for varga in samples[0]["varga_ascendant_signs"]
    )
    kp_changed = any(
        len({row["kp_cusp_sub_lords"].get(str(house)) for row in samples}) > 1
        for house in range(1, 13)
    )
    boundary_risk = "high" if lagna_changed or moon_changed or kp_changed else "moderate" if varga_changed or dasha_changed else "low"
    return {
        "available": True, "uncertainty_minutes": uncertainty,
        "boundary_risk": boundary_risk, "lagna_changed": lagna_changed,
        "moon_nakshatra_changed": moon_changed, "varga_ascendant_changed": varga_changed,
        "kp_cusp_sub_lord_changed": kp_changed, "dasha_stack_changed": dasha_changed,
        "samples": samples,
    }


def get_cached_v3_kp_evidence(
    birth_data: Mapping[str, Any],
    calculate: Callable[[], Dict[str, Any]],
) -> Dict[str, Any]:
    """Cache natal KP separately from target-year timing calculations."""
    cache_key = _birth_key(birth_data, "kp")
    cached = _cache_get(_KP_CACHE, cache_key)
    if cached is not None:
        return cached
    return _cache_put(_KP_CACHE, cache_key, calculate() or {})


def clear_v3_natal_caches_for_tests() -> None:
    with _CACHE_LOCK:
        _NATAL_CACHE.clear()
        _KP_CACHE.clear()
