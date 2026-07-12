"""Single-native health report context — reuses existing health calculators and branch builders."""

from __future__ import annotations

import calendar
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from dateutil.relativedelta import relativedelta
from shared.dasha_calculator import DashaCalculator

from .base_context_builder import calculate_chart_for_birth, calculate_divisional_chart
from .shared_branch_context import (
    build_jaimini_context,
    build_kp_context,
    build_nadi_context,
    build_nakshatra_context,
)
from ..cache.report_hash import normalize_birth_data, normalize_language
from ..constants import MEDICAL_DISCLAIMER
from .health_body_zones import build_priority_body_zones

logger = logging.getLogger(__name__)


def _birth_dict(birth_data: Any) -> Dict[str, Any]:
    if hasattr(birth_data, "model_dump"):
        return birth_data.model_dump()
    if hasattr(birth_data, "dict"):
        return birth_data.dict()
    return dict(birth_data) if not isinstance(birth_data, dict) else birth_data


def _lon_to_sign_1based(longitude: Any) -> int:
    try:
        return int(float(longitude) // 30) + 1
    except Exception:
        return 1


def _asc_sign_1based(chart: Dict[str, Any]) -> int:
    asc = chart.get("ascendant")
    if isinstance(asc, (int, float)):
        return _lon_to_sign_1based(asc)
    if isinstance(asc, dict):
        if asc.get("sign") is not None:
            try:
                return int(asc["sign"]) + 1
            except Exception:
                pass
        if asc.get("longitude") is not None:
            return _lon_to_sign_1based(asc.get("longitude"))
    return 1


def _planet_sign_1based(chart: Dict[str, Any], planet: str) -> Optional[int]:
    pdata = (chart.get("planets") or {}).get(planet)
    if isinstance(pdata, (int, float)):
        return _lon_to_sign_1based(pdata)
    if not isinstance(pdata, dict):
        return None
    if pdata.get("sign") is not None:
        try:
            return int(pdata["sign"]) + 1
        except Exception:
            return None
    lon = pdata.get("longitude")
    if lon is None:
        return None
    return _lon_to_sign_1based(lon)


def _house_of_planet(chart: Dict[str, Any], planet: str) -> Optional[int]:
    if not planet:
        return None
    asc = _asc_sign_1based(chart)
    psign = _planet_sign_1based(chart, planet)
    if not psign:
        return None
    return ((psign - asc) % 12) + 1


def _lord_of_house(chart: Dict[str, Any], house: int) -> Optional[str]:
    from calculators.base_calculator import BaseCalculator

    asc = _asc_sign_1based(chart)
    sign_0based = (asc - 1 + house - 1) % 12
    return BaseCalculator.SIGN_LORDS.get(sign_0based)


def _nakshatra_for_planet(nak_positions: Dict[str, Any], planet: str) -> Dict[str, Any]:
    row = nak_positions.get(planet) or {}
    return {
        "planet": planet,
        "nakshatra": row.get("nakshatra_name") or row.get("nakshatra"),
        "lord": row.get("nakshatra_lord"),
        "pada": row.get("pada"),
        "deity": row.get("nakshatra_deity"),
        "longitude": row.get("longitude"),
    }


def _build_twelve_month_dasha(birth_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    dasha_calc = DashaCalculator()
    start = datetime.now().replace(day=1, hour=12, minute=0, second=0, microsecond=0)
    months: List[Dict[str, Any]] = []
    for offset in range(12):
        cursor = start + relativedelta(months=offset)
        year, month = cursor.year, cursor.month
        last_day = calendar.monthrange(year, month)[1]
        mid = datetime(year, month, min(15, last_day), 12, 0, 0)
        try:
            levels = dasha_calc.calculate_current_dashas(birth_payload, mid)
        except Exception as exc:
            logger.warning("health dasha month failed %s-%s: %s", year, month, exc)
            levels = {}
        md = levels.get("mahadasha") or {}
        ad = levels.get("antardasha") or {}
        pd = levels.get("pratyantardasha") or {}
        months.append({
            "month_index": offset + 1,
            "year": year,
            "month": month,
            "label": mid.strftime("%b %Y"),
            "mahadasha": md.get("planet"),
            "antardasha": ad.get("planet"),
            "pratyantardasha": pd.get("planet"),
            "md_start": md.get("start"),
            "md_end": md.get("end"),
            "ad_start": ad.get("start"),
            "ad_end": ad.get("end"),
        })
    return months


def _build_ai_health_layers(birth_payload: Dict[str, Any]) -> Dict[str, Any]:
    """D30, badhaka, mrityu bhaga, mental/vitality blocks from HealthAIContextGenerator."""
    try:
        from ai.health_ai_context_generator import HealthAIContextGenerator

        full = HealthAIContextGenerator().build_health_context(birth_payload)
        return {
            "health_charts": full.get("health_charts") or {},
            "health_houses_ai": full.get("health_houses") or {},
            "vitality_analysis": full.get("vitality_analysis") or {},
            "disease_indicators": full.get("disease_indicators") or {},
            "mental_health": full.get("mental_health") or {},
            "health_timing_ai": full.get("health_timing") or {},
            "body_parts": full.get("body_parts") or {},
            "badhaka_analysis": full.get("badhaka_analysis") or {},
            "mrityu_bhaga_analysis": full.get("mrityu_bhaga_analysis") or {},
            "functional_nature": full.get("functional_nature") or {},
            "health_analysis_instructions": full.get("health_analysis_instructions") or {},
        }
    except Exception as exc:
        logger.warning("HealthAIContextGenerator failed: %s", exc)
        return {"error": str(exc)[:300]}


def _attach_health_agent(chart: Dict[str, Any], birth_payload: Dict[str, Any], layers: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from health.health_analysis_execute import attach_health_agent_context

        ctx: Dict[str, Any] = {
            "d1_chart": chart,
            "birth_data": birth_payload,
            **{k: v for k, v in layers.items() if k != "error"},
        }
        attach_health_agent_context(ctx, birth_payload)
        return ctx.get("health_agent") or {}
    except Exception as exc:
        logger.warning("health_agent attach failed: %s", exc)
        return {"error": str(exc)[:200]}


def _planet_system_ranks(health: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten planet → body systems with impact cues for PDF metrics."""
    ranks: List[Dict[str, Any]] = []
    planet_analysis = health.get("planet_analysis") or {}
    if not isinstance(planet_analysis, dict):
        return ranks
    for planet, row in planet_analysis.items():
        if not isinstance(row, dict):
            continue
        impact = row.get("health_impact") or {}
        ranks.append({
            "planet": planet,
            "systems": row.get("body_systems") or [],
            "element": row.get("element"),
            "impact_summary": impact if isinstance(impact, str) else (
                impact.get("summary") or impact.get("level") or impact.get("status")
            ),
            "house": None,
        })
    return ranks


def _attention_houses(health: Dict[str, Any], chart: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    house_analysis = health.get("house_analysis") or {}
    if not isinstance(house_analysis, dict):
        return out
    chart = chart or {}
    planets = chart.get("planets") or {}
    drishti_by_house = chart.get("graha_drishti_by_house") or {}
    residents_by_house: Dict[int, List[str]] = {}
    for planet_name, pdata in planets.items():
        if not isinstance(pdata, dict):
            continue
        try:
            h = int(pdata.get("house"))
        except (TypeError, ValueError):
            continue
        if 1 <= h <= 12:
            residents_by_house.setdefault(h, []).append(str(planet_name))

    for house_num in (1, 6, 8, 12, 2, 7):
        key = house_num if house_num in house_analysis else str(house_num)
        row = house_analysis.get(key) or house_analysis.get(house_num)
        if not isinstance(row, dict):
            continue
        drishti_rows = drishti_by_house.get(str(house_num)) or drishti_by_house.get(house_num) or []
        aspecting = []
        for item in drishti_rows:
            if not isinstance(item, dict):
                continue
            aspecting.append({
                "planet": item.get("planet"),
                "from_house": item.get("planet_house"),
                "aspect": item.get("aspect_labels") or item.get("aspect_from_planet"),
            })
        out.append({
            "house": house_num,
            "significance": row.get("health_significance"),
            "interpretation": row.get("health_interpretation"),
            "residents": residents_by_house.get(house_num) or [],
            "aspecting_planets": aspecting,
        })
    return out


def build_health_report_context(request: Any) -> Dict[str, Any]:
    person = normalize_birth_data(request.birth_data)
    birth_payload = _birth_dict(request.birth_data)
    chart = calculate_chart_for_birth(request.birth_data)

    jaimini = build_jaimini_context(chart)
    nadi = build_nadi_context(chart)
    nakshatra = build_nakshatra_context(chart)
    kp = build_kp_context(request.birth_data)

    from calculators.health_calculator import HealthCalculator

    health = HealthCalculator(chart, birth_payload).calculate_overall_health()
    ai_layers = _build_ai_health_layers(birth_payload)
    health_agent = _attach_health_agent(chart, birth_payload, ai_layers)

    d9 = calculate_divisional_chart(chart, 9)
    d30 = (ai_layers.get("health_charts") or {}).get("d30_trimsamsa")
    if not d30:
        try:
            from calculators.divisional_chart_calculator import DivisionalChartCalculator

            d30 = DivisionalChartCalculator(chart).calculate_divisional_chart(30)
        except Exception as exc:
            logger.warning("D30 chart failed: %s", exc)
            d30 = {"error": str(exc)[:200]}

    lord_1 = _lord_of_house(chart, 1)
    lord_6 = _lord_of_house(chart, 6)
    lord_8 = _lord_of_house(chart, 8)
    nak_positions = (nakshatra.get("positions") or {}) if isinstance(nakshatra, dict) else {}
    lords_nakshatra = {
        "lagna_lord": {
            "planet": lord_1,
            "house": _house_of_planet(chart, lord_1) if lord_1 else None,
            "nakshatra": _nakshatra_for_planet(nak_positions, lord_1) if lord_1 else {},
        },
        "sixth_lord": {
            "planet": lord_6,
            "house": _house_of_planet(chart, lord_6) if lord_6 else None,
            "nakshatra": _nakshatra_for_planet(nak_positions, lord_6) if lord_6 else {},
        },
        "eighth_lord": {
            "planet": lord_8,
            "house": _house_of_planet(chart, lord_8) if lord_8 else None,
            "nakshatra": _nakshatra_for_planet(nak_positions, lord_8) if lord_8 else {},
        },
        "moon": {
            "planet": "Moon",
            "house": _house_of_planet(chart, "Moon"),
            "nakshatra": _nakshatra_for_planet(nak_positions, "Moon"),
        },
    }

    current_dashas: Dict[str, Any] = {}
    try:
        current_dashas = DashaCalculator().calculate_current_dashas(birth_payload)
    except Exception as exc:
        current_dashas = {"error": str(exc)[:200]}

    twelve_months = _build_twelve_month_dasha(birth_payload)
    body_zone_map = build_priority_body_zones(
        chart,
        lords_nakshatra=lords_nakshatra,
        current_dashas=current_dashas,
    )

    return {
        "report_type": "health",
        "language": normalize_language(getattr(request, "language", "english")),
        "chart_style": getattr(request, "chart_style", "both"),
        "person": person,
        "chart": chart,
        "medical_disclaimer": MEDICAL_DISCLAIMER,
        "branches": {
            "jaimini": jaimini,
            "nadi": nadi,
            "nakshatra": nakshatra,
            "kp": kp,
            "d30": d30,
        },
        "summaries": {
            "jaimini": jaimini.get("summary"),
            "nadi": nadi.get("summary"),
            "nakshatra": nakshatra.get("summary"),
            "kp": kp.get("summary"),
        },
        "health": health,
        "health_agent": health_agent,
        "ai_layers": ai_layers,
        "d9_chart": d9,
        "d30_chart": d30,
        "d30_analysis": (ai_layers.get("health_charts") or {}).get("d30_analysis") or {},
        "vitality_analysis": ai_layers.get("vitality_analysis") or {},
        "disease_indicators": ai_layers.get("disease_indicators") or {},
        "mental_health": ai_layers.get("mental_health") or {},
        "body_parts": ai_layers.get("body_parts") or {},
        "body_zone_map": body_zone_map,
        "badhaka_analysis": ai_layers.get("badhaka_analysis") or {},
        "mrityu_bhaga_analysis": ai_layers.get("mrityu_bhaga_analysis") or {},
        "functional_nature": ai_layers.get("functional_nature") or {},
        "lords_nakshatra": lords_nakshatra,
        "planet_system_ranks": _planet_system_ranks(health),
        "attention_houses": _attention_houses(health, chart),
        "current_dashas": current_dashas,
        "twelve_month_dasha": twelve_months,
    }
