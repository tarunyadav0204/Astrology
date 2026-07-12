from __future__ import annotations

from typing import Any, Dict

from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.karma_context_builder import KarmaContextBuilder
from calculators.nakshatra_calculator import NakshatraCalculator
from calculators.nadi_linkage_calculator import NadiLinkageCalculator
from app.kp.services.chart_service import KPChartService


def build_jaimini_context(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    d9_chart = DivisionalChartCalculator(chart_data).calculate_divisional_chart(9).get("divisional_chart", {})
    chara_karakas = CharaKarakaCalculator(chart_data).calculate_chara_karakas()
    atmakaraka = chara_karakas.get("chara_karakas", {}).get("Atmakaraka", {}).get("planet")
    jaimini = JaiminiPointCalculator(chart_data, d9_chart, atmakaraka).calculate_jaimini_points()
    return {
        "chara_karakas": chara_karakas,
        "d9_chart": d9_chart,
        "jaimini_points": jaimini,
        "summary": summarize_jaimini_context(chara_karakas, jaimini),
    }


def build_nakshatra_context(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    calculator = NakshatraCalculator(chart_data=chart_data)
    positions = calculator.calculate_nakshatra_positions()
    return {
        "positions": positions,
        "moon": calculator.get_moon_nakshatra(),
        "ascendant": calculator.get_ascendant_nakshatra(),
        "yogas": calculator.analyze_nakshatra_yogas(),
        "summary": summarize_nakshatra_context(positions, calculator.analyze_nakshatra_yogas()),
    }


def build_nadi_context(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    links = NadiLinkageCalculator(chart_data).get_nadi_links()
    return {
        "links": links,
        "summary": summarize_nadi_context(links),
    }


def build_d60_context(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    d60_chart = DivisionalChartCalculator(chart_data).calculate_divisional_chart(60)
    try:
        karma_builder = KarmaContextBuilder(chart_data, {"d60_shashtiamsa": d60_chart.get("divisional_chart", {})})
        karma_context = karma_builder.get_complete_karma_context()
    except Exception as exc:
        karma_context = {"error": str(exc)}
    return {
        "d60_chart": d60_chart,
        "karma_context": karma_context,
        "summary": summarize_d60_context(karma_context),
    }


def build_kp_context(birth_data: Any) -> Dict[str, Any]:
    payload = birth_data.model_dump() if hasattr(birth_data, "model_dump") else dict(birth_data)
    chart = KPChartService.calculate_kp_chart(
        payload["date"],
        payload["time"],
        payload["latitude"],
        payload["longitude"],
        payload.get("timezone") or "",
    )
    return {
        "kp_chart": chart,
        "summary": summarize_kp_context(chart),
    }


def summarize_jaimini_context(chara_karakas: Dict[str, Any], jaimini: Dict[str, Any]) -> Dict[str, Any]:
    karakas = chara_karakas.get("chara_karakas", {})
    points = jaimini or {}
    return {
        "atmakaraka": karakas.get("Atmakaraka", {}),
        "darakaraka": karakas.get("Darakaraka", {}),
        "al": points.get("arudha_lagna", {}),
        "a7": points.get("darapada", {}),
        "ul": points.get("upapada_lagna", {}),
        "karkamsa": points.get("karkamsa_lagna", {}),
        "relationship_note": (
            f"UL in {points.get('upapada_lagna', {}).get('sign_name', 'unknown')} "
            f"and A7 in {points.get('darapada', {}).get('sign_name', 'unknown')}."
        ),
    }


def summarize_nakshatra_context(positions: Dict[str, Any], yogas: Any) -> Dict[str, Any]:
    moon = positions.get("Moon", {})
    asc = positions.get("Ascendant", {}) if isinstance(positions, dict) else {}
    return {
        "moon": {
            "nakshatra": moon.get("nakshatra_name"),
            "lord": moon.get("nakshatra_lord"),
            "deity": moon.get("nakshatra_deity"),
            "pada": moon.get("pada"),
        },
        "ascendant": {
            "nakshatra": asc.get("nakshatra_name"),
            "lord": asc.get("nakshatra_lord"),
            "deity": asc.get("nakshatra_deity"),
            "pada": asc.get("pada"),
        },
        "yogas": yogas[:4] if isinstance(yogas, list) else [],
        "emotional_note": (
            f"Moon in {moon.get('nakshatra_name', 'unknown')} under {moon.get('nakshatra_lord', 'unknown')}."
        ),
    }


def summarize_nadi_context(links: Dict[str, Any]) -> Dict[str, Any]:
    scored = []
    for planet, data in links.items():
        connections = data.get("connections", {}) or {}
        scored.append({
            "planet": planet,
            "total_links": sum(len(v or []) for v in connections.values()),
            "is_retro": data.get("sign_info", {}).get("is_retro", False),
            "is_exchange": data.get("sign_info", {}).get("is_exchange", False),
        })
    scored.sort(key=lambda row: row["total_links"], reverse=True)
    return {
        "top_linked_planets": scored[:3],
        "relationship_note": "Nadi reveals repeating connection patterns and karmic flow.",
    }


def summarize_d60_context(karma_context: Dict[str, Any]) -> Dict[str, Any]:
    soul_identity = karma_context.get("soul_identity", {}) if isinstance(karma_context, dict) else {}
    soul_desire = karma_context.get("soul_desire", {}) if isinstance(karma_context, dict) else {}
    karma_evidence = karma_context.get("karma_evidence", {}) if isinstance(karma_context, dict) else {}
    return {
        "lagna_deity": soul_identity.get("lagna_deity"),
        "lagna_nature": soul_identity.get("lagna_nature"),
        "atmakaraka_deity": soul_identity.get("atmakaraka_deity"),
        "atmakaraka_nature": soul_identity.get("atmakaraka_nature"),
        "atmakaraka_planet": soul_desire.get("planet"),
        "karmic_verdict": karma_evidence.get("verdict"),
        "confidence": karma_evidence.get("d60_confidence", {}),
        "summary": soul_identity.get("lagna_theme") or "Hidden karmic residue and continuity signal.",
    }


def summarize_kp_context(chart: Dict[str, Any]) -> Dict[str, Any]:
    cusp_lords = chart.get("cusp_lords", {}) if isinstance(chart, dict) else {}
    planet_significators = chart.get("planet_significators", {}) if isinstance(chart, dict) else {}
    four_step = chart.get("four_step_theory", {}) if isinstance(chart, dict) else {}
    seventh = cusp_lords.get(7, {}) or cusp_lords.get("7", {}) or {}
    return {
        "seventh_cusp": seventh,
        "top_significators": [
            {
                "planet": planet,
                "houses": houses[:5],
            }
            for planet, houses in list(planet_significators.items())[:5]
        ],
        "four_step": four_step.get("Venus", {}) if isinstance(four_step, dict) else {},
        "materialization_note": (
            f"7th cusp star lord {seventh.get('star_lord', 'unknown')} and sub lord {seventh.get('sub_lord', 'unknown')}."
        ),
    }
