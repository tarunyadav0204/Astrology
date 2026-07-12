"""Single-native wealth report context — reuses existing calculators only."""

from __future__ import annotations

import calendar
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional

from calculators.d10_analyzer import D10Analyzer
from calculators.indu_lagna_calculator import InduLagnaCalculator
from calculators.wealth_calculator import WealthCalculator
from shared.dasha_calculator import DashaCalculator

from .base_context_builder import calculate_chart_for_birth, calculate_divisional_chart
from .shared_branch_context import (
    build_jaimini_context,
    build_kp_context,
    build_nadi_context,
    build_nakshatra_context,
)
from ..cache.report_hash import normalize_birth_data, normalize_language

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
    """ChartCalculator stores ascendant as sidereal longitude (float), not a dict."""
    asc = chart.get("ascendant")
    if isinstance(asc, (int, float)):
        return _lon_to_sign_1based(asc)
    if isinstance(asc, dict):
        if asc.get("sign") is not None:
            try:
                # Some payloads use 0-based sign index
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

    # SIGN_LORDS keys are 0-11; _asc_sign_1based returns 1-12.
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
            logger.warning("wealth dasha month failed %s-%s: %s", year, month, exc)
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


def _build_trading_snapshot(chart: Dict[str, Any], birth_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from calculators.trading_luck_calculator import TradingLuckCalculator

        today = datetime.now()
        transit_payload = dict(birth_payload)
        transit_payload["date"] = today.strftime("%Y-%m-%d")
        transit_payload["time"] = "12:00"
        transit_chart = calculate_chart_for_birth(transit_payload)
        forecast = TradingLuckCalculator(chart, transit_chart, birth_payload, today).calculate_trading_forecast()
        return forecast if isinstance(forecast, dict) else {"raw": forecast}
    except Exception as exc:
        logger.warning("trading luck snapshot failed: %s", exc)
        return {"error": str(exc)[:200]}


def _try_wealth_evidence(chart: Dict[str, Any], birth_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from wealth.wealth_enhanced_execute import attach_wealth_agentic_context

        ctx = {
            "d1_chart": chart,
            "birth_data": birth_payload,
        }
        attach_wealth_agentic_context(ctx, birth_payload)
        return ctx.get("wealth_evidence") or {}
    except Exception as exc:
        logger.warning("wealth_evidence attach failed: %s", exc)
        return {"error": str(exc)[:200]}


def build_wealth_report_context(request: Any) -> Dict[str, Any]:
    person = normalize_birth_data(request.birth_data)
    birth_payload = _birth_dict(request.birth_data)
    chart = calculate_chart_for_birth(request.birth_data)

    jaimini = build_jaimini_context(chart)
    nadi = build_nadi_context(chart)
    nakshatra = build_nakshatra_context(chart)
    kp = build_kp_context(request.birth_data)

    wealth = WealthCalculator(chart, birth_payload).calculate_overall_wealth()
    try:
        indu = InduLagnaCalculator(chart).get_indu_lagna_analysis()
    except Exception as exc:
        indu = {"error": str(exc)[:200]}

    d2 = calculate_divisional_chart(chart, 2)
    d9 = calculate_divisional_chart(chart, 9)
    d10_chart = calculate_divisional_chart(chart, 10)
    try:
        d10 = D10Analyzer(chart).analyze_d10_chart()
    except Exception as exc:
        d10 = {"error": str(exc)[:200]}

    lord_2 = _lord_of_house(chart, 2)
    lord_11 = _lord_of_house(chart, 11)
    nak_positions = (nakshatra.get("positions") or {}) if isinstance(nakshatra, dict) else {}
    lords_nakshatra = {
        "second_lord": {
            "planet": lord_2,
            "house": _house_of_planet(chart, lord_2) if lord_2 else None,
            "nakshatra": _nakshatra_for_planet(nak_positions, lord_2) if lord_2 else {},
        },
        "eleventh_lord": {
            "planet": lord_11,
            "house": _house_of_planet(chart, lord_11) if lord_11 else None,
            "nakshatra": _nakshatra_for_planet(nak_positions, lord_11) if lord_11 else {},
        },
    }

    current_dashas: Dict[str, Any] = {}
    try:
        current_dashas = DashaCalculator().calculate_current_dashas(birth_payload)
    except Exception as exc:
        current_dashas = {"error": str(exc)[:200]}

    twelve_months = _build_twelve_month_dasha(birth_payload)
    trading = _build_trading_snapshot(chart, birth_payload)
    wealth_evidence = _try_wealth_evidence(chart, birth_payload)

    px_wealth: Dict[str, Any] = {}
    try:
        px = ((wealth_evidence.get("parashari") or {}).get("px") or {})
        px_wealth = px.get("wealth") or {}
    except Exception:
        px_wealth = {}

    seventh_lord = _lord_of_house(chart, 7)

    return {
        "report_type": "wealth",
        "language": normalize_language(getattr(request, "language", "english")),
        "chart_style": getattr(request, "chart_style", "both"),
        "person": person,
        "chart": chart,
        "branches": {
            "jaimini": jaimini,
            "nadi": nadi,
            "nakshatra": nakshatra,
            "kp": kp,
            "d2": d2,
        },
        "summaries": {
            "jaimini": jaimini.get("summary"),
            "nadi": nadi.get("summary"),
            "nakshatra": nakshatra.get("summary"),
            "kp": kp.get("summary"),
        },
        "wealth": wealth,
        "indu_lagna": indu,
        "d2_chart": d2,
        "d9_chart": d9,
        "d10_chart": d10_chart,
        "d10_analysis": d10,
        "lords_nakshatra": lords_nakshatra,
        "current_dashas": current_dashas,
        "twelve_month_dasha": twelve_months,
        "trading_luck": trading,
        "wealth_evidence": wealth_evidence,
        "px_wealth": px_wealth,
        "spouse_finance_hints": {
            "seventh_lord": seventh_lord,
            "seventh_lord_house": _house_of_planet(chart, seventh_lord or ""),
            "venus_house": _house_of_planet(chart, "Venus"),
            "jupiter_house": _house_of_planet(chart, "Jupiter"),
            "d9_available": bool(d9),
        },
    }
