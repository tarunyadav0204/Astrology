import json
import logging
import re
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
import asyncio

from ai.parallel_chat.parallel_agent_payloads import build_parashari_agent_payload
from calculators.chart_calculator import ChartCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext
from shared.dasha_calculator import DashaCalculator
from utils.admin_settings import get_gemini_instant_model


def _build_instant_usage_stage(stage: str, model_name: str, prompt_chars: int, response_chars: int, token_usage: Dict[str, Any] | None, success: bool, elapsed_s: float | None = None) -> Dict[str, Any]:
    tu = token_usage or {}
    row = {
        "stage": stage,
        "llm_model": model_name or "",
        "input_chars": int(prompt_chars or 0),
        "output_chars": int(response_chars or 0),
        "input_tokens": int(tu.get("input_tokens") or 0),
        "output_tokens": int(tu.get("output_tokens") or 0),
        "cached_tokens": int(tu.get("cached_tokens") or 0),
        "non_cached_input_tokens": int(
            tu.get("non_cached_input_tokens")
            or max(0, int(tu.get("input_tokens") or 0) - int(tu.get("cached_tokens") or 0))
        ),
        "success": bool(success),
    }
    if elapsed_s is not None:
        row["elapsed_ms"] = round(float(elapsed_s) * 1000.0, 1)
    return row
from utils.query_context import resolve_query_now


SIGN_NAMES = [
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

PLANET_SEQUENCE = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

CATEGORY_FOCUS = {
    "career": {"houses": [2, 6, 10, 11], "planets": ["Sun", "Mercury", "Saturn", "Jupiter"]},
    "wealth": {"houses": [2, 5, 9, 11], "planets": ["Jupiter", "Venus", "Mercury"]},
    "health": {"houses": [1, 6, 8, 12], "planets": ["Sun", "Moon", "Mars", "Saturn"]},
    "marriage": {"houses": [2, 5, 7, 11], "planets": ["Venus", "Moon", "Jupiter", "Mars"]},
    "progeny": {"houses": [2, 5, 9, 11], "planets": ["Jupiter", "Moon", "Venus"]},
    "education": {"houses": [2, 4, 5, 9], "planets": ["Mercury", "Jupiter", "Moon"]},
    "trading": {"houses": [2, 5, 8, 11], "planets": ["Mercury", "Jupiter", "Rahu"]},
    "general": {"houses": [1, 4, 7, 10], "planets": ["Moon", "Sun", "Jupiter"]},
}

HOUSE_THEME_LABELS = {
    1: "self, vitality, personal direction",
    2: "income, family assets, speech, resources",
    3: "effort, communication, initiative, short moves",
    4: "home, peace, property, emotional base",
    5: "creativity, children, romance, speculation",
    6: "workload, conflict, debt, health strain",
    7: "partners, clients, agreements, spouse themes",
    8: "sudden changes, hidden matters, pressure, vulnerability",
    9: "fortune, mentors, dharma, long-range support",
    10: "career, public role, authority, visibility",
    11: "gains, networks, fulfillment, support circles",
    12: "expenses, retreat, isolation, foreign or hidden matters",
}

SIGN_STYLE_THEMES = {
    "Aries": "direct, fast, and action-first",
    "Taurus": "steady, practical, and comfort-oriented",
    "Gemini": "curious, verbal, and mentally restless",
    "Cancer": "protective, feeling-led, and receptive",
    "Leo": "expressive, proud, and visibly self-driven",
    "Virgo": "analytical, careful, and improvement-focused",
    "Libra": "relational, balancing, and diplomacy-seeking",
    "Scorpio": "intense, private, and all-or-nothing",
    "Sagittarius": "frank, expansive, and principle-driven",
    "Capricorn": "serious, strategic, and responsibility-led",
    "Aquarius": "independent, unconventional, and idea-driven",
    "Pisces": "sensitive, imaginative, and porous",
}

NAKSHATRA_STYLE_THEMES = {
    "Ashwini": "fast-starting, instinctive, and action-led",
    "Bharani": "intense, carrying, and morally pressured",
    "Krittika": "sharp, cutting, and clarifying",
    "Rohini": "attractive, growth-seeking, and attachment-forming",
    "Mrigashira": "curious, searching, and mentally roaming",
    "Ardra": "restless, stormy, and truth-pulling",
    "Punarvasu": "resetting, hopeful, and return-oriented",
    "Pushya": "protective, dutiful, and stabilizing",
    "Ashlesha": "psychological, strategic, and binding",
    "Magha": "status-aware, ancestral, and throne-conscious",
    "Purva Phalguni": "expressive, pleasure-seeking, and performative",
    "Uttara Phalguni": "reliable, contractual, and support-giving",
    "Hasta": "skillful, tactical, and hands-on",
    "Chitra": "crafted, image-aware, and design-driven",
    "Swati": "independent, flexible, and wind-like",
    "Vishakha": "goal-fixed, driven, and branching",
    "Anuradha": "loyal, relational, and network-building",
    "Jyeshtha": "protective, proud, and control-seeking",
    "Mula": "root-seeking, disruptive, and truth-digging",
    "Purva Ashadha": "assertive, persuasive, and wave-making",
    "Uttara Ashadha": "enduring, duty-bound, and victory-oriented",
    "Shravana": "observant, listening, and pattern-tracking",
    "Dhanishta": "rhythmic, performative, and socially driven",
    "Shatabhisha": "detached, analytical, and system-breaking",
    "Purva Bhadrapada": "extreme, idealistic, and intensity-prone",
    "Uttara Bhadrapada": "deep, restrained, and internally steady",
    "Revati": "gentle, guiding, and protective",
}

PARASHARI_TOPIC_MAP = {
    "career": "career",
    "job": "career",
    "promotion": "career",
    "business": "career",
    "marriage": "relationship",
    "love": "relationship",
    "relationship": "relationship",
    "partner": "relationship",
    "spouse": "relationship",
    "wealth": "wealth",
    "money": "wealth",
    "finance": "wealth",
    "trading": "wealth",
    "health": "health",
    "disease": "health",
}

_INSTANT_CONTEXT_BUILDER = ChatContextBuilder()
logger = logging.getLogger(__name__)
_MONTH_NAME_TO_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

ANSWER_MODES = [
    "explanation_mechanism",
    "trait_nature",
    "relationship_person",
    "timing_window",
    "event_prediction",
    "potential_capacity",
    "comparison_choice",
    "problem_diagnosis",
    "remedy_action",
    "topic_reading",
]

TARGET_SUBJECTS = {
    "self": {"label": "self", "base_house": 1},
    "spouse": {"label": "spouse/partner", "base_house": 7},
    "partner": {"label": "spouse/partner", "base_house": 7},
    "wife": {"label": "wife", "base_house": 7},
    "husband": {"label": "husband", "base_house": 7},
    "child": {"label": "child", "base_house": 5},
    "first_child": {"label": "first child", "base_house": 5},
    "second_child": {"label": "second child", "base_house": 7},
    "third_child": {"label": "third child", "base_house": 9},
    "younger_brother": {"label": "younger brother", "base_house": 3},
    "younger_sister": {"label": "younger sister", "base_house": 3},
    "younger_sibling": {"label": "younger sibling", "base_house": 3},
    "elder_brother": {"label": "elder brother", "base_house": 11},
    "elder_sister": {"label": "elder sister", "base_house": 11},
    "elder_sibling": {"label": "elder sibling", "base_house": 11},
    "sibling": {"label": "sibling", "base_house": 3},
    "brother": {"label": "brother", "base_house": 3},
    "sister": {"label": "sister", "base_house": 3},
    "mother": {"label": "mother", "base_house": 4},
    "father": {"label": "father", "base_house": 9},
    "maternal_uncle": {"label": "maternal uncle", "base_house": 6},
    "uncle": {"label": "uncle", "base_house": 6},
}


def _truncate(text: str, limit: int) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: max(0, limit - 1)].rstrip() + "…"


def _normalize_question_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _normalize_relationship_target_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return key


def _fallback_target_subject(question: str) -> Dict[str, Any]:
    q = _normalize_question_text(question)
    checks = [
        ("second child", "second_child"),
        ("first child", "first_child"),
        ("third child", "third_child"),
        ("younger brother", "younger_brother"),
        ("younger sister", "younger_sister"),
        ("elder brother", "elder_brother"),
        ("older brother", "elder_brother"),
        ("elder sister", "elder_sister"),
        ("older sister", "elder_sister"),
        ("maternal uncle", "maternal_uncle"),
        ("wife", "wife"),
        ("husband", "husband"),
        ("spouse", "spouse"),
        ("partner", "partner"),
        ("child", "child"),
        ("children", "child"),
        ("brother", "brother"),
        ("sister", "sister"),
        ("sibling", "sibling"),
        ("mother", "mother"),
        ("father", "father"),
        ("uncle", "uncle"),
    ]
    for needle, key in checks:
        if needle in q:
            meta = TARGET_SUBJECTS.get(key) or {}
            return {
                "key": key,
                "label": meta.get("label") or key.replace("_", " "),
                "base_house": meta.get("base_house"),
                "confidence": "low",
                "source": "fallback",
            }
    return {
        "key": "self",
        "label": "self",
        "base_house": 1,
        "confidence": "low",
        "source": "fallback_self",
    }


def _rotate_house_num(native_house: int, anchor_house: int) -> int:
    return ((int(native_house) - int(anchor_house)) % 12) + 1


def _get_house_lordships(ascendant_sign_index: int) -> Dict[str, List[int]]:
    sign_lords = {
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
    house_lordships: Dict[str, List[int]] = {}
    for house in range(1, 13):
        sign_index = (ascendant_sign_index + house - 1) % 12
        lord = sign_lords[sign_index]
        house_lordships.setdefault(lord, []).append(house)
    return house_lordships


def _support_rank(level: str) -> int:
    return {"md": 5, "ad": 4, "pd": 3, "sk": 2, "pr": 1}.get(str(level or "").lower(), 0)


def _planet_theme(planet: str) -> str:
    themes = {
        "Sun": "authority, recognition, decisions involving bosses or visibility",
        "Moon": "emotions, responsiveness, support, and day-to-day flow",
        "Mars": "action, pressure, conflict, technical execution, and haste",
        "Mercury": "communication, business, paperwork, negotiation, and analysis",
        "Jupiter": "guidance, growth, support, learning, and protection",
        "Venus": "relationships, comfort, attraction, finance, and agreements",
        "Saturn": "workload, delay, responsibility, discipline, and long-term effort",
        "Rahu": "suddenness, ambition, foreign links, volatility, and unconventional moves",
        "Ketu": "detachment, uncertainty, back-end matters, and low-visibility shifts",
    }
    return themes.get(str(planet or ""), "mixed influences")


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _topic_support_band(payload: Dict[str, Any]) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    if payload.get("support"):
        return str(payload.get("support"))
    if payload.get("mode") in {"supportive", "mixed", "obstructed"}:
        return str(payload.get("mode"))
    if payload.get("vis") in {"high", "mixed", "low"}:
        return str(payload.get("vis"))
    return None


def _last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (datetime(year, month + 1, 1) - datetime(year, month, 1)).days


def _parse_ymd(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


def _resolve_period_window(intent: Optional[Dict[str, Any]], now_local: datetime) -> Dict[str, Any]:
    ir = intent or {}
    extracted = ir.get("extracted_context") if isinstance(ir.get("extracted_context"), dict) else {}
    tr = ir.get("transit_request") if isinstance(ir.get("transit_request"), dict) else {}
    year_month_map = tr.get("yearMonthMap") if isinstance(tr.get("yearMonthMap"), dict) else {}
    timeframe_text = str(extracted.get("timeframe") or "").strip().lower()
    # If the router resolved a calendar month/window, prefer that window even if
    # a synthetic first-of-month specific_date is also present.
    if year_month_map and timeframe_text:
        for year_str, months in year_month_map.items():
            for month_name in months or []:
                if str(month_name or "").strip().lower() in timeframe_text:
                    try:
                        year = int(str(year_str))
                    except (TypeError, ValueError):
                        continue
                    month_num = _MONTH_NAME_TO_NUM.get(str(month_name or "").strip().lower())
                    if not month_num:
                        continue
                    start = datetime(year, month_num, 1)
                    end = datetime(year, month_num, _last_day_of_month(year, month_num))
                    span_days = (end - start).days + 1
                    return {
                        "kind": "window",
                        "start": start.strftime("%Y-%m-%d"),
                        "end": end.strftime("%Y-%m-%d"),
                        "span_days": span_days,
                        "label": f"{str(month_name).strip()} {year}",
                        "use_pd": True,
                        "use_sk_pr": span_days <= 31,
                    }
    specific_date = str(extracted.get("specific_date") or ir.get("dasha_as_of") or "").strip()
    if specific_date:
        try:
            dt = datetime.strptime(specific_date, "%Y-%m-%d")
            return {
                "kind": "day",
                "start": dt.strftime("%Y-%m-%d"),
                "end": dt.strftime("%Y-%m-%d"),
                "span_days": 1,
                "label": dt.strftime("%d %B %Y"),
                "use_pd": True,
                "use_sk_pr": True,
            }
        except ValueError:
            pass

    if year_month_map:
        starts: List[datetime] = []
        ends: List[datetime] = []
        labels: List[str] = []
        for year_str, months in year_month_map.items():
            try:
                year = int(str(year_str))
            except (TypeError, ValueError):
                continue
            for month_name in months or []:
                month_num = _MONTH_NAME_TO_NUM.get(str(month_name or "").strip().lower())
                if not month_num:
                    continue
                starts.append(datetime(year, month_num, 1))
                ends.append(datetime(year, month_num, _last_day_of_month(year, month_num)))
                labels.append(f"{str(month_name).strip()} {year}")
        if starts and ends:
            start = min(starts)
            end = max(ends)
            span_days = (end - start).days + 1
            return {
                "kind": "window",
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "span_days": span_days,
                "label": labels[0] if len(labels) == 1 else f"{labels[0]} to {labels[-1]}",
                "use_pd": True,
                "use_sk_pr": span_days <= 31,
            }

    return {
        "kind": "current",
        "start": now_local.strftime("%Y-%m-%d"),
        "end": now_local.strftime("%Y-%m-%d"),
        "span_days": 1,
        "label": now_local.strftime("%d %B %Y"),
        "use_pd": False,
        "use_sk_pr": False,
    }


def _period_anchor_datetime(period_window: Dict[str, Any], now_local: datetime) -> datetime:
    kind = str((period_window or {}).get("kind") or "current")
    if kind in {"day", "window"}:
        start = str((period_window or {}).get("start") or "").strip()
        if start:
            try:
                return datetime.strptime(start, "%Y-%m-%d").replace(hour=12, minute=0, second=0, microsecond=0)
            except ValueError:
                pass
    return now_local.replace(hour=12, minute=0, second=0, microsecond=0)


def _period_time_relation(period_window: Dict[str, Any], now_local: datetime) -> str:
    start = str((period_window or {}).get("start") or "").strip()
    end = str((period_window or {}).get("end") or "").strip()
    if not start or not end:
        return "current"
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        return "current"
    today = now_local.date()
    if end_dt < today:
        return "past"
    if start_dt > today:
        return "future"
    return "current"


def _dominant_house_lines(hi: Dict[str, Any], limit: int = 3) -> List[str]:
    rows: List[tuple[int, int, Dict[str, Any]]] = []
    for house, row in (hi or {}).items():
        if not isinstance(row, dict):
            continue
        score = (len(row.get("o") or []) * 3) + (len(row.get("r") or []) * 2) + len(row.get("a") or [])
        if score <= 0:
            continue
        house_num = _safe_int(house)
        if house_num is None:
            continue
        rows.append((house_num, score, row))
    rows.sort(key=lambda item: (-item[1], item[0]))
    out: List[str] = []
    for house_num, score, row in rows[:limit]:
        bits: List[str] = []
        if row.get("r"):
            bits.append(f"ruled by {', '.join(str(v).upper() for v in row.get('r')[:2])}")
        if row.get("o"):
            bits.append(f"occupied by {', '.join(str(v).upper() for v in row.get('o')[:2])}")
        if row.get("a"):
            bits.append(f"aspected by {', '.join(str(v).upper() for v in row.get('a')[:2])}")
        detail = ", ".join(bits) if bits else "active through current periods"
        out.append(f"House {house_num} is strongly active ({detail}).")
    return out


def _rank_house_activation_rows(hi: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    rows: List[tuple[int, int, Dict[str, Any]]] = []
    for house, row in (hi or {}).items():
        if not isinstance(row, dict):
            continue
        score = (len(row.get("o") or []) * 3) + (len(row.get("r") or []) * 2) + len(row.get("a") or [])
        if score <= 0:
            continue
        house_num = _safe_int(house)
        if house_num is None:
            continue
        rows.append((house_num, score, row))
    rows.sort(key=lambda item: (-item[1], item[0]))
    out: List[Dict[str, Any]] = []
    for house_num, score, row in rows[:limit]:
        out.append(
            {
                "house": house_num,
                "score": score,
                "theme": HOUSE_THEME_LABELS.get(house_num, "mixed house themes"),
                "rulership_levels": list(row.get("r") or [])[:2],
                "occupancy_levels": list(row.get("o") or [])[:2],
                "aspect_levels": list(row.get("a") or [])[:2],
            }
        )
    return out


def _all_house_activation_from_levels(levels: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {}
    for house in range(1, 13):
        row = {"r": [], "o": [], "a": []}
        for lvl, data in (levels or {}).items():
            if not isinstance(data, dict):
                continue
            if house in (data.get("rh") or []):
                row["r"].append(lvl)
            try:
                if int(data.get("h")) == house:
                    row["o"].append(lvl)
            except (TypeError, ValueError):
                pass
            if house in (data.get("ahs") or []):
                row["a"].append(lvl)
        out[str(house)] = row
    return out


def _window_area_mechanism_lines(active_area_rows: List[Dict[str, Any]], levels: Dict[str, Any], limit: int = 3) -> List[str]:
    out: List[str] = []
    for row in (active_area_rows or [])[:limit]:
        house = _safe_int(row.get("house"))
        if house is None:
            continue
        bits: List[str] = []
        for lvl in (row.get("rulership_levels") or [])[:1]:
            planet = ((levels or {}).get(str(lvl).lower()) or {}).get("p")
            bits.append(f"{str(lvl).upper()} {planet or ''} rules house {house}".strip())
        for lvl in (row.get("occupancy_levels") or [])[:1]:
            planet = ((levels or {}).get(str(lvl).lower()) or {}).get("p")
            bits.append(f"{str(lvl).upper()} {planet or ''} occupies house {house}".strip())
        for lvl in (row.get("aspect_levels") or [])[:1]:
            planet = ((levels or {}).get(str(lvl).lower()) or {}).get("p")
            bits.append(f"{str(lvl).upper()} {planet or ''} aspects house {house}".strip())
        if bits:
            out.append(f"House {house} ({HOUSE_THEME_LABELS.get(house, 'mixed themes')}) is a major active area because " + ", ".join(bits[:3]) + ".")
    return out


def _dasha_chain_synthesis_lines(
    formatted_levels: Dict[str, Any],
    raw_levels: Dict[str, Any],
    current_transits_formatted: Dict[str, Any],
    period_window: Dict[str, Any],
) -> List[str]:
    out: List[str] = []
    if not isinstance(formatted_levels, dict):
        return out
    order = ["md", "ad", "pd"]
    if (period_window or {}).get("use_sk_pr"):
        order.extend(["sk", "pr"])
    elif (period_window or {}).get("use_pd"):
        order.append("sk")
    for lvl in order:
        row = (formatted_levels or {}).get(lvl) or {}
        if not isinstance(row, dict):
            continue
        planet = str(row.get("planet") or "")
        if not planet:
            continue
        pieces: List[str] = []
        natal_house = _safe_int(row.get("natal_house"))
        natal_sign = str(row.get("natal_sign") or "")
        lordships = [str(v) for v in (row.get("lordships") or [])[:3]]
        if natal_house is not None:
            pieces.append(f"natal residence house {natal_house}")
        if natal_sign:
            pieces.append(f"natal sign {natal_sign}")
        if lordships:
            pieces.append(f"rules houses {', '.join(lordships)}")
        active_row = (raw_levels or {}).get(lvl) or {}
        aspect_houses = [str(v) for v in (active_row.get("ahs") or [])[:4]]
        if aspect_houses:
            pieces.append(f"actively aspects houses {', '.join(aspect_houses)}")
        transit_row = (current_transits_formatted or {}).get(planet) or {}
        if isinstance(transit_row, dict) and transit_row:
            transit_house = _safe_int(transit_row.get("house_from_lagna"))
            transit_sign = str(transit_row.get("sign") or "")
            if transit_house is not None:
                if transit_sign:
                    pieces.append(f"currently transits house {transit_house} in {transit_sign}")
                else:
                    pieces.append(f"currently transits house {transit_house}")
        if pieces:
            out.append(f"{str(lvl).upper()} {planet}: " + "; ".join(pieces) + ".")
    return out[:5]


def _dasha_role_label(level: str, period_window: Dict[str, Any]) -> str:
    lvl = str(level or "").lower()
    if lvl == "md":
        return "background period setter"
    if lvl == "ad":
        return "main operating channel"
    if lvl == "pd":
        return "short-window sharpener"
    if lvl == "sk":
        return "finer trigger"
    if lvl == "pr":
        return "micro-delivery trigger" if (period_window or {}).get("use_sk_pr") else "fine delivery layer"
    return "active timing layer"


def _dasha_level_effects(
    formatted_levels: Dict[str, Any],
    raw_levels: Dict[str, Any],
    current_transits_formatted: Dict[str, Any],
    period_window: Dict[str, Any],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(formatted_levels, dict):
        return out
    order = ["md", "ad", "pd"]
    if (period_window or {}).get("use_sk_pr"):
        order.extend(["sk", "pr"])
    elif (period_window or {}).get("use_pd"):
        order.append("sk")
    for lvl in order:
        row = (formatted_levels or {}).get(lvl) or {}
        raw_row = (raw_levels or {}).get(lvl) or {}
        if not isinstance(row, dict):
            continue
        planet = str(row.get("planet") or "")
        if not planet:
            continue
        natal_house = _safe_int(row.get("natal_house"))
        natal_sign = str(row.get("natal_sign") or "")
        lordships = [int(v) for v in (row.get("lordships") or []) if _safe_int(v) is not None][:4]
        aspect_houses = [int(v) for v in (raw_row.get("ahs") or []) if _safe_int(v) is not None][:6]
        transit_row = (current_transits_formatted or {}).get(planet) or {}
        transit_house = _safe_int(transit_row.get("house_from_lagna")) if isinstance(transit_row, dict) else None
        transit_sign = str(transit_row.get("sign") or "") if isinstance(transit_row, dict) else ""

        contribution_parts: List[str] = []
        if natal_house is not None:
            contribution_parts.append(f"anchors through natal house {natal_house}")
        if lordships:
            contribution_parts.append(f"carries houses {', '.join(str(v) for v in lordships[:3])}")
        if aspect_houses:
            contribution_parts.append(f"pushes activation to houses {', '.join(str(v) for v in aspect_houses[:4])}")
        if transit_house is not None:
            if transit_sign:
                contribution_parts.append(f"currently channels through transit house {transit_house} in {transit_sign}")
            else:
                contribution_parts.append(f"currently channels through transit house {transit_house}")
        out.append(
            {
                "level": str(lvl).upper(),
                "planet": planet,
                "role": _dasha_role_label(lvl, period_window),
                "natal_house": natal_house,
                "natal_sign": natal_sign,
                "lordships": lordships,
                "aspect_houses": aspect_houses,
                "transit_house": transit_house,
                "transit_sign": transit_sign,
                "contribution": "; ".join(contribution_parts),
            }
        )
    return out[:5]


def _repeated_house_theme_lines(active_area_rows: List[Dict[str, Any]], limit: int = 3) -> List[str]:
    out: List[str] = []
    for row in (active_area_rows or [])[:limit]:
        if not isinstance(row, dict):
            continue
        house = _safe_int(row.get("house"))
        if house is None:
            continue
        repeated_levels: List[str] = []
        for key in ("rulership_levels", "occupancy_levels", "aspect_levels"):
            repeated_levels.extend([str(v).upper() for v in (row.get(key) or []) if v])
        repeated_levels = list(dict.fromkeys(repeated_levels))
        if not repeated_levels:
            continue
        out.append(
            f"House {house} themes repeat across {', '.join(repeated_levels[:4])}, so {HOUSE_THEME_LABELS.get(house, 'this area')} should be synthesized as one of the core period themes."
        )
    return out


def _divisional_specific_lines(divisional_support: Dict[str, Any], navamsa_root_fruit: List[Dict[str, Any]], limit: int = 2) -> List[str]:
    out: List[str] = []
    if isinstance(divisional_support, dict):
        topic = (divisional_support.get("topic") or {}) if isinstance(divisional_support.get("topic"), dict) else {}
        current_topic = (divisional_support.get("current_topic") or {}) if isinstance(divisional_support.get("current_topic"), dict) else {}
        for bucket, label in ((topic, "Topic divisional support"), (current_topic, "Current divisional timing")):
            charts = bucket.get("charts") or {}
            if not isinstance(charts, dict):
                continue
            for code, detail in charts.items():
                if not isinstance(detail, dict):
                    continue
                rows = detail.get("rows") or []
                if rows and isinstance(rows[0], dict):
                    first = rows[0]
                    house = _safe_int(first.get("h"))
                    lord = str(first.get("lord") or first.get("p") or "")
                    occ = ", ".join(str(v) for v in (first.get("occ") or [])[:3])
                    bits: List[str] = []
                    if house is not None:
                        bits.append(f"house {house}")
                    if lord:
                        bits.append(f"lord {lord}")
                    if occ:
                        bits.append(f"occupants {occ}")
                    if bits:
                        out.append(f"{label} in {code} specifically highlights " + ", ".join(bits) + ".")
                        break
        for row in (navamsa_root_fruit or [])[:2]:
            if not isinstance(row, dict):
                continue
            planet = str(row.get("p") or "")
            d1h = _safe_int(row.get("d1h"))
            d9h = _safe_int(row.get("d9h"))
            band = str(row.get("band") or "")
            if planet and d1h is not None and d9h is not None:
                extra = f" with a {band} band" if band else ""
                out.append(f"In D9, {planet} carries from D1 house {d1h} into D9 house {d9h}{extra}.")
    deduped = list(dict.fromkeys(out))
    return deduped[:limit]


def _risk_specific_lines(
    top_risks: List[str],
    mechanisms: List[Dict[str, Any]],
    transit_pressure: Dict[str, Any],
    limit: int = 2,
) -> List[str]:
    out: List[str] = []
    for row in (mechanisms or [])[:3]:
        if not isinstance(row, dict):
            continue
        house = _safe_int(row.get("house"))
        summary = str(row.get("summary") or "").strip()
        if house in {6, 8, 12} and summary:
            out.append(f"Risk pressure is concretely tied to house {house}: {summary}.")
    for row in (transit_pressure.get("dp") or [])[:3]:
        if not isinstance(row, dict):
            continue
        tp = str(row.get("tp") or "")
        np = str(row.get("np") or "")
        th = _safe_int(row.get("th"))
        nh = _safe_int(row.get("nh"))
        if tp and np and (th is not None or nh is not None):
            bits: List[str] = [f"{tp} is interacting with natal {np}"]
            if th is not None:
                bits.append(f"through transit-side house {th}")
            if nh is not None:
                bits.append(f"while natal house {nh} is involved")
            out.append("Risk pressure is also sharpened because " + ", ".join(bits) + ".")
    if not out:
        out.extend([str(v) for v in (top_risks or [])[:limit] if str(v).strip()])
    deduped = list(dict.fromkeys(out))
    return deduped[:limit]


def _build_personality_axes(
    birth_summary: Dict[str, Any],
    natal_snapshot: Dict[str, Any],
) -> List[str]:
    out: List[str] = []
    ascendant = (birth_summary.get("ascendant") or {}) if isinstance(birth_summary, dict) else {}
    asc_sign = str(ascendant.get("sign") or "")
    asc_nak = ((ascendant.get("nakshatra") or {}) if isinstance(ascendant.get("nakshatra"), dict) else {})
    asc_nak_name = str(asc_nak.get("name") or "")
    moon = (birth_summary.get("moon") or {}) if isinstance(birth_summary, dict) else {}
    moon_sign = str(moon.get("sign") or "")
    moon_house = _safe_int(moon.get("house"))
    moon_nak = ((moon.get("nakshatra") or {}) if isinstance(moon.get("nakshatra"), dict) else {})
    moon_nak_name = str(moon_nak.get("name") or "")
    key_planets = (natal_snapshot.get("key_planets") or {}) if isinstance(natal_snapshot, dict) else {}

    if asc_sign:
        line = f"Core temperament anchor: Ascendant in {asc_sign} gives an outer style that is {SIGN_STYLE_THEMES.get(asc_sign, 'distinctive and sign-colored')}."
        if asc_nak_name:
            line += f" Nakshatra flavor from {asc_nak_name} adds a subtler tone that is {NAKSHATRA_STYLE_THEMES.get(asc_nak_name, 'psychologically specific and motive-colored')}."
        out.append(line)
    if moon_sign:
        moon_line = ""
        if moon_house is not None:
            moon_line = f"Emotional style anchor: Moon in {moon_sign} in house {moon_house} shows how the person processes feelings, safety, and inner reactions."
        else:
            moon_line = f"Emotional style anchor: Moon in {moon_sign} shows how the person processes feelings, safety, and inner reactions."
        if moon_nak_name:
            moon_line += f" Nakshatra flavor from {moon_nak_name} makes the emotional style more {NAKSHATRA_STYLE_THEMES.get(moon_nak_name, 'motive-colored and psychologically textured')}."
        out.append(moon_line)

    second_house_planets: List[str] = []
    for planet in ["Mercury", "Mars", "Saturn", "Rahu", "Ketu", "Jupiter", "Sun", "Venus", "Moon"]:
        row = key_planets.get(planet) or {}
        if _safe_int(row.get("house")) == 2:
            second_house_planets.append(planet)
    if second_house_planets:
        out.append(
            f"Expression and speech anchor: house 2 is loaded with {', '.join(second_house_planets[:4])}, so communication, tone, and value-expression are major parts of the personality pattern."
        )

    mars = key_planets.get("Mars") or {}
    saturn = key_planets.get("Saturn") or {}
    pressure_bits: List[str] = []
    if _safe_int(mars.get("house")) is not None:
        pressure_bits.append(f"Mars in house {_safe_int(mars.get('house'))}")
    if _safe_int(saturn.get("house")) is not None:
        pressure_bits.append(f"Saturn in house {_safe_int(saturn.get('house'))}")
    if pressure_bits:
        out.append(
            f"Pressure-response anchor: {' and '.join(pressure_bits[:2])} show how the person reacts under stress, conflict, and sustained pressure."
        )

    sun = key_planets.get("Sun") or {}
    jupiter = key_planets.get("Jupiter") or {}
    values_bits: List[str] = []
    if _safe_int(sun.get("house")) is not None:
        values_bits.append(f"Sun in house {_safe_int(sun.get('house'))}")
    if _safe_int(jupiter.get("house")) is not None:
        values_bits.append(f"Jupiter in house {_safe_int(jupiter.get('house'))}")
    if values_bits:
        out.append(
            f"Value and guidance anchor: {' and '.join(values_bits[:2])} help show what principles, beliefs, and meaning-patterns guide the person."
        )

    deduped = list(dict.fromkeys(out))
    return deduped[:5]


def _planet_names_in_house(key_planets: Dict[str, Any], house: int) -> List[str]:
    out: List[str] = []
    for planet in PLANET_SEQUENCE:
        row = (key_planets or {}).get(planet) or {}
        if _safe_int(row.get("house")) == house:
            out.append(planet)
    return out


def _lord_of_house(house_lordships: Dict[str, List[int]], target_house: int) -> str:
    for planet, houses in (house_lordships or {}).items():
        if target_house in (houses or []):
            return str(planet)
    return ""


def _planet_flavor_line(planet: str, row: Dict[str, Any]) -> str:
    if not planet or not isinstance(row, dict):
        return ""
    sign = str(row.get("sign") or "")
    nak = (row.get("nakshatra") or {}) if isinstance(row.get("nakshatra"), dict) else {}
    nak_name = str(nak.get("name") or "")
    bits = [planet]
    if sign:
        bits.append(f"in {sign} ({SIGN_STYLE_THEMES.get(sign, 'sign-colored')})")
    if nak_name:
        bits.append(f"through {nak_name} ({NAKSHATRA_STYLE_THEMES.get(nak_name, 'nakshatra-colored')})")
    return " ".join(bits)


def _build_target_chart_context(
    birth_summary: Dict[str, Any],
    natal_snapshot: Dict[str, Any],
    current_transits_formatted: Dict[str, Any],
    target_subject: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    target = target_subject if isinstance(target_subject, dict) else {}
    target_key = str(target.get("key") or "self")
    target_label = str(target.get("label") or (TARGET_SUBJECTS.get(target_key) or {}).get("label") or "self")
    anchor_house = _safe_int(target.get("base_house")) or _safe_int((TARGET_SUBJECTS.get(target_key) or {}).get("base_house")) or 1
    asc_sign = str(((birth_summary.get("ascendant") or {}) if isinstance(birth_summary.get("ascendant"), dict) else {}).get("sign") or "")
    try:
        asc_sign_index = SIGN_NAMES.index(asc_sign)
    except ValueError:
        asc_sign_index = 0
    target_asc_index = (asc_sign_index + anchor_house - 1) % 12
    target_house_lordships = _get_house_lordships(target_asc_index)
    key_planets = (natal_snapshot.get("key_planets") or {}) if isinstance(natal_snapshot, dict) else {}
    rotated_key_planets: Dict[str, Dict[str, Any]] = {}
    for planet, row in key_planets.items():
        if not isinstance(row, dict):
            continue
        native_house = _safe_int(row.get("house"))
        rotated_row = dict(row)
        if native_house is not None:
            rotated_house = _rotate_house_num(native_house, anchor_house)
            rotated_row["native_house"] = native_house
            rotated_row["house_from_target"] = rotated_house
            rotated_row["house"] = rotated_house
        rotated_key_planets[str(planet)] = rotated_row
    rotated_transits: Dict[str, Dict[str, Any]] = {}
    for planet, row in (current_transits_formatted or {}).items():
        if not isinstance(row, dict):
            continue
        native_house = _safe_int(row.get("house_from_lagna"))
        rotated_row = dict(row)
        if native_house is not None:
            rotated_house = _rotate_house_num(native_house, anchor_house)
            rotated_row["house_from_native"] = native_house
            rotated_row["house_from_target"] = rotated_house
            rotated_row["house"] = rotated_house
        rotated_transits[str(planet)] = rotated_row
    return {
        "key": target_key,
        "label": target_label,
        "anchor_house": anchor_house,
        "target_ascendant_sign": SIGN_NAMES[target_asc_index],
        "target_house_lordships": target_house_lordships,
        "target_key_planets": rotated_key_planets,
        "target_transits": rotated_transits,
    }


def _target_context_as_birth_summary(target_chart_context: Dict[str, Any]) -> Dict[str, Any]:
    key_planets = (target_chart_context.get("target_key_planets") or {}) if isinstance(target_chart_context, dict) else {}
    moon = (key_planets.get("Moon") or {}) if isinstance(key_planets, dict) else {}
    return {
        "ascendant": {
            "sign": target_chart_context.get("target_ascendant_sign"),
            "degree": None,
            "nakshatra": None,
        },
        "moon": {
            "sign": moon.get("sign"),
            "house": moon.get("house_from_target"),
            "nakshatra": moon.get("nakshatra"),
        },
    }


def _target_context_as_natal_snapshot(target_chart_context: Dict[str, Any]) -> Dict[str, Any]:
    target_planets = (target_chart_context.get("target_key_planets") or {}) if isinstance(target_chart_context, dict) else {}
    rotated_planets: Dict[str, Dict[str, Any]] = {}
    for planet, row in target_planets.items():
        if not isinstance(row, dict):
            continue
        rotated = dict(row)
        if _safe_int(rotated.get("house_from_target")) is not None:
            rotated["house"] = _safe_int(rotated.get("house_from_target"))
        rotated_planets[str(planet)] = rotated
    return {
        "house_lordships": target_chart_context.get("target_house_lordships") or {},
        "key_planets": rotated_planets,
    }


def _build_area_behavior_axes(
    birth_summary: Dict[str, Any],
    natal_snapshot: Dict[str, Any],
) -> Dict[str, List[str]]:
    house_lordships = (natal_snapshot.get("house_lordships") or {}) if isinstance(natal_snapshot, dict) else {}
    key_planets = (natal_snapshot.get("key_planets") or {}) if isinstance(natal_snapshot, dict) else {}
    axes: Dict[str, List[str]] = {}

    def build_axis(name: str, houses: List[int], label: str, extra_planets: List[str] | None = None) -> None:
        lines: List[str] = []
        for house in houses:
            lord = _lord_of_house(house_lordships, house)
            occupants = _planet_names_in_house(key_planets, house)
            parts: List[str] = []
            if lord:
                lord_row = key_planets.get(lord) or {}
                lord_flavor = _planet_flavor_line(lord, lord_row)
                if lord_flavor:
                    parts.append(f"house {house} lord is {lord_flavor}")
            if occupants:
                occ_bits: List[str] = []
                for occ in occupants[:2]:
                    occ_row = key_planets.get(occ) or {}
                    occ_bits.append(_planet_flavor_line(occ, occ_row) or occ)
                parts.append(f"occupants include {', '.join(occ_bits)}")
            if parts:
                lines.append(f"{label} axis through house {house}: " + "; ".join(parts) + ".")
        for planet in (extra_planets or []):
            row = key_planets.get(planet) or {}
            if row:
                flavor = _planet_flavor_line(planet, row)
                if flavor:
                    lines.append(f"{label} is also colored by {flavor}.")
        if lines:
            axes[name] = list(dict.fromkeys(lines))[:3]

    build_axis("home_behavior", [4], "Home/emotional-base")
    build_axis("work_behavior", [6, 10], "Work/public-persona")
    build_axis("relationship_behavior", [7], "One-to-one/relationship")
    build_axis("children_family_behavior", [5, 2], "Children/family-affection")
    build_axis("speech_expression", [2, 3], "Speech/expression")
    build_axis("pressure_conflict_response", [6, 8], "Pressure/conflict-response", extra_planets=["Mars", "Saturn", "Rahu"])
    return axes


def _build_person_profile_axes(
    natal_snapshot: Dict[str, Any],
    divisional_support: Dict[str, Any],
    relationship_target: Optional[Dict[str, Any]],
    target_chart_context: Optional[Dict[str, Any]] = None,
) -> List[str]:
    house_lordships = (natal_snapshot.get("house_lordships") or {}) if isinstance(natal_snapshot, dict) else {}
    key_planets = (natal_snapshot.get("key_planets") or {}) if isinstance(natal_snapshot, dict) else {}
    out: List[str] = []

    target = relationship_target if isinstance(relationship_target, dict) else {}
    target_key = str(target.get("key") or "spouse")
    target_label = str(target.get("label") or TARGET_SUBJECTS.get(target_key, {}).get("label") or "person")
    base_house = _safe_int(target.get("base_house"))
    if base_house is None:
        base_house = _safe_int((TARGET_SUBJECTS.get(target_key) or {}).get("base_house")) or 7

    target_lord = _lord_of_house(house_lordships, base_house)
    if target_lord:
        row = key_planets.get(target_lord) or {}
        flavor = _planet_flavor_line(target_lord, row)
        if flavor:
            house = _safe_int(row.get("house"))
            if house is not None:
                out.append(
                    f"{target_label.capitalize()} nature anchor: the key house is {base_house} and its lord is {flavor}, placed in house {house}, so this person's nature should be read mainly from this pattern rather than from the native's ascendant."
                )
            else:
                out.append(
                    f"{target_label.capitalize()} nature anchor: the key house is {base_house} and its lord is {flavor}, so this person's nature should be read mainly from this pattern rather than from the native's ascendant."
                )

    occupants = _planet_names_in_house(key_planets, base_house)
    if occupants:
        occ_bits: List[str] = []
        for occ in occupants[:3]:
            occ_row = key_planets.get(occ) or {}
            occ_bits.append(_planet_flavor_line(occ, occ_row) or occ)
        out.append(f"{target_label.capitalize()} expression axis: house {base_house} is occupied by {', '.join(occ_bits)}, which colors how this person behaves and presents themselves.")

    speech_house = ((base_house + 1 - 1) % 12) + 1
    speech_lord = _lord_of_house(house_lordships, speech_house)
    if speech_lord:
        row = key_planets.get(speech_lord) or {}
        flavor = _planet_flavor_line(speech_lord, row)
        if flavor:
            out.append(
                f"{target_label.capitalize()} communication axis: second-from-target house {speech_house} is led by {flavor}, which helps describe speech, values, and day-to-day expression."
            )

    charts = ((divisional_support.get("topic") or {}).get("charts") or {}) if isinstance(divisional_support, dict) else {}
    d9 = charts.get("D9") if isinstance(charts, dict) else None
    if isinstance(d9, dict):
        for row in d9.get("rows") or []:
            if not isinstance(row, dict):
                continue
            house = _safe_int(row.get("h"))
            if house == base_house:
                lord = str(row.get("lord") or "")
                occ = ", ".join(str(v) for v in (row.get("occ") or [])[:3])
                bits: List[str] = []
                if lord:
                    bits.append(f"lord {lord}")
                if occ:
                    bits.append(f"occupants {occ}")
                if bits:
                    out.append(f"D9 {target_label} confirmation: in D9, house {base_house} is specifically marked by " + ", ".join(bits) + ".")
                break

    current_topic = (divisional_support.get("current_topic") or {}) if isinstance(divisional_support, dict) else {}
    d9_current = (current_topic.get("charts") or {}).get("D9") if isinstance(current_topic, dict) else None
    if isinstance(d9_current, dict):
        rows = d9_current.get("rows") or []
        for row in rows[:2]:
            if not isinstance(row, dict):
                continue
            lvl = str(row.get("lvl") or "").upper()
            planet = str(row.get("p") or "")
            house = _safe_int(row.get("h"))
            if planet and house is not None:
                out.append(f"Current D9 {target_label}-tone support: {lvl} {planet} connects through D9 house {house}.")
                break

    if isinstance(target_chart_context, dict) and target_chart_context:
        rotated_birth_summary = _target_context_as_birth_summary(target_chart_context)
        rotated_snapshot = _target_context_as_natal_snapshot(target_chart_context)
        rotated_personality = _build_personality_axes(rotated_birth_summary, rotated_snapshot)
        rotated_axes = _build_area_behavior_axes(rotated_birth_summary, rotated_snapshot)
        if rotated_personality:
            out.append(f"{target_label.capitalize()} core-from-target context: {rotated_personality[0]}")
            if len(rotated_personality) > 1:
                out.append(f"{target_label.capitalize()} emotional-from-target context: {rotated_personality[1]}")
        rel_axis = (rotated_axes.get("relationship_behavior") or [])[:1]
        speech_axis = (rotated_axes.get("speech_expression") or [])[:1]
        for line in rel_axis + speech_axis:
            out.append(f"{target_label.capitalize()} target-context axis: {line}")

    deduped = list(dict.fromkeys(out))
    return deduped[:4]


def _house_activation_mechanisms(
    focus_houses: List[int],
    hi: Dict[str, Any],
    levels: Dict[str, Any],
    limit: int = 3,
) -> List[Dict[str, Any]]:
    items: List[tuple[int, int, Dict[str, Any]]] = []
    target = [int(h) for h in (focus_houses or []) if _safe_int(h) is not None]
    for house_num in target:
        row = (hi or {}).get(str(house_num)) or {}
        if not isinstance(row, dict):
            continue
        score = (len(row.get("o") or []) * 3) + (len(row.get("r") or []) * 2) + len(row.get("a") or [])
        if score <= 0:
            continue
        items.append((house_num, score, row))
    items.sort(key=lambda item: (-item[1], item[0]))
    out: List[Dict[str, Any]] = []
    for house_num, _score, row in items[:limit]:
        links: List[str] = []
        for lvl in row.get("r") or []:
            planet = ((levels or {}).get(str(lvl).lower()) or {}).get("p")
            links.append(f"{str(lvl).upper()} {planet or ''} rules house {house_num}".strip())
        for lvl in row.get("o") or []:
            planet = ((levels or {}).get(str(lvl).lower()) or {}).get("p")
            links.append(f"{str(lvl).upper()} {planet or ''} occupies house {house_num}".strip())
        for lvl in row.get("a") or []:
            planet = ((levels or {}).get(str(lvl).lower()) or {}).get("p")
            links.append(f"{str(lvl).upper()} {planet or ''} aspects house {house_num}".strip())
        out.append(
            {
                "house": house_num,
                "links": links[:4],
                "summary": "; ".join(links[:3]) if links else f"House {house_num} has no strong active dasha linkage",
            }
        )
    return out


def _looks_like_personality_question(question: str) -> bool:
    q = str(question or "").lower()
    markers = [
        "behaviour", "behavior", "nature", "personality", "temper", "attitude", "speech",
        "communication", "confidence", "mindset", "how am i", "what am i like",
        "my habits", "my traits", "my expression", "my temperament",
    ]
    return any(marker in q for marker in markers)


def _looks_like_explanatory_followup(question: str, history: List[Dict[str, Any]]) -> bool:
    q = str(question or "").lower()
    follow_markers = [
        "why do you", "why did you", "how do you", "how exactly", "what relation",
        "what makes you say", "how is", "how are", "you said", "you mean", "on what basis",
    ]
    if not any(marker in q for marker in follow_markers):
        return False
    return bool(history)


def _looks_like_relationship_person_question(question: str) -> bool:
    q = str(question or "").lower()
    person_markers = [
        "wife", "husband", "spouse", "partner", "girlfriend", "boyfriend", "mother", "father",
        "son", "daughter", "child", "children", "boss", "friend",
    ]
    trait_markers = [
        "character", "characteristics", "nature", "behavior", "behaviour", "personality",
        "temperament", "traits", "how is", "what is", "what kind of",
    ]
    return any(p in q for p in person_markers) and any(t in q for t in trait_markers)


def _looks_like_comparison_question(question: str) -> bool:
    q = str(question or "").lower()
    markers = [
        "which is better", "better or", "or better", "compare", "comparison", "versus", "vs",
        "should i choose", "option a", "option b", "between", "this or that",
    ]
    return any(marker in q for marker in markers)


def _looks_like_problem_question(question: str) -> bool:
    q = str(question or "").lower()
    markers = [
        "why is", "why am i", "why do i", "problem", "issue", "delay", "obstacle", "blocked",
        "struggling", "suffering", "not happening", "what is wrong", "cause of",
    ]
    return any(marker in q for marker in markers)


def _looks_like_remedy_question(question: str) -> bool:
    q = str(question or "").lower()
    markers = ["remedy", "upay", "solution", "what should i do", "how to fix", "what can i do"]
    return any(marker in q for marker in markers)


def _looks_like_potential_question(question: str, intent: Optional[Dict[str, Any]]) -> bool:
    q = str(question or "").lower()
    cat = str((intent or {}).get("category") or "").lower()
    markers = [
        "potential", "suited", "good for", "best for", "can i become", "aptitude",
        "strength", "talent", "capacity", "suitable", "promise", "prospects",
    ]
    if any(marker in q for marker in markers):
        return True
    return cat in {"career", "job", "business", "education", "learning"} and any(
        token in q for token in ["what should", "which field", "career for me", "good career", "best career"]
    )


def _looks_like_timing_window_question(question: str, intent: Optional[Dict[str, Any]]) -> bool:
    q = str(question or "").lower()
    mode = str((intent or {}).get("mode") or "").upper()
    if mode in {"PREDICT_DAILY", "PREDICT_PERIOD_OUTLOOK"}:
        return True
    markers = ["today", "tomorrow", "this month", "next month", "this year", "next year", "how will be"]
    return any(marker in q for marker in markers)


def _looks_like_event_prediction_question(question: str, intent: Optional[Dict[str, Any]]) -> bool:
    q = str(question or "").lower()
    mode = str((intent or {}).get("mode") or "").upper()
    if mode == "LIFESPAN_EVENT_TIMING":
        return True
    markers = [
        "will ", "what will happen", "when will", "is it likely", "will it happen",
        "can this happen", "chance of", "possibility of",
    ]
    return any(marker in q for marker in markers)


def _infer_answer_mode(question: str, intent: Optional[Dict[str, Any]], history: List[Dict[str, Any]]) -> str:
    if _looks_like_explanatory_followup(question, history):
        return "explanation_mechanism"
    if _looks_like_remedy_question(question):
        return "remedy_action"
    if _looks_like_comparison_question(question):
        return "comparison_choice"
    if _looks_like_problem_question(question):
        return "problem_diagnosis"
    if _looks_like_relationship_person_question(question):
        return "relationship_person"
    if _looks_like_personality_question(question):
        return "trait_nature"
    if _looks_like_timing_window_question(question, intent):
        return "timing_window"
    if _looks_like_event_prediction_question(question, intent):
        return "event_prediction"
    if _looks_like_potential_question(question, intent):
        return "potential_capacity"
    return "topic_reading"


def _build_answer_mode_router_prompt(question: str, intent: Optional[Dict[str, Any]], history: List[Dict[str, Any]]) -> str:
    intent = intent or {}
    recent_items: List[Dict[str, str]] = []
    for row in history[-3:]:
        if not isinstance(row, dict):
            continue
        q = _truncate(str(row.get("question") or ""), 220)
        a = _truncate(str(row.get("answer") or row.get("response") or ""), 260)
        if q or a:
            recent_items.append({"question": q, "answer": a})
    payload = {
        "question": question,
        "intent_mode": str(intent.get("mode") or ""),
        "intent_category": str(intent.get("category") or ""),
        "needs_transits": bool(intent.get("needs_transits")),
        "context_type": str(intent.get("context_type") or ""),
        "recent_history": recent_items,
        "allowed_answer_modes": ANSWER_MODES,
        "allowed_target_subjects": sorted(TARGET_SUBJECTS.keys()),
    }
    context_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"""
Classify the user's astrology chat question into exactly one answer_mode.

CRITICAL:
- Choose from the provided allowed_answer_modes only.
- Use semantic meaning, not keyword matching.
- The app runs in many languages and nuanced phrasings, so infer intent from meaning and conversation context.
- Do not be biased by the user's wording. For example, a 'will X happen' question should still map to the mode that best fits the chart-reading task, not what the user seems to want to hear.

Answer mode meanings:
- explanation_mechanism: user asks how/why a prior chart claim was made
- trait_nature: user asks about behavior, nature, speech, temperament, personality
- relationship_person: user asks about the nature/characteristics of spouse/partner/person
- timing_window: user asks about a period/day/month/year and wants how that window will be
- event_prediction: user asks if an event will happen / likelihood / outcome
- potential_capacity: user asks suitability, aptitude, promise, fit, capacity
- comparison_choice: user asks between two or more options
- problem_diagnosis: user asks why something is blocked, unstable, delayed, leaking, or difficult
- remedy_action: user asks what to do, how to fix, remedy, upay, practical action
- topic_reading: default focused reading when none of the above fit best

Also infer the target_subject_key from the allowed_target_subjects list.
Examples:
- questions about the native themselves -> self
- wife/husband/spouse/partner -> spouse-type target
- first child / second child -> the matching child target
- younger brother / elder sister -> the matching sibling target
- maternal uncle / uncle -> the closest matching uncle target

Return JSON only:
{{"answer_mode":"one_of_the_allowed_modes","confidence":"high|medium|low","reason":"very short reason","target_subject_key":"allowed_target_or_self"}}

INPUT:
{context_json}
""".strip()


async def _infer_answer_mode_with_llm(
    analyzer,
    *,
    question: str,
    intent: Optional[Dict[str, Any]],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prompt = _build_answer_mode_router_prompt(question, intent, history)
    model_name = get_gemini_instant_model()
    selected_model = analyzer.get_named_gemini_model(model_name, premium_analysis=False)
    try:
        llm_result = await analyzer.generate_text_from_prompt(
            prompt,
            premium_analysis=False,
            model_override=selected_model,
            model_name_override=model_name,
            llm_log_tag="instant_answer_mode",
            request_timeout_s=20.0,
            force_gemini=True,
        )
    except Exception as exc:
        logger.warning("instant answer mode llm classification failed: %s", exc)
        return {"answer_mode": _infer_answer_mode(question, intent, history), "target_subject": _fallback_target_subject(question)}
    if not llm_result.get("success"):
        logger.warning("instant answer mode llm classification unsuccessful: %s", llm_result.get("error"))
        return {"answer_mode": _infer_answer_mode(question, intent, history), "target_subject": _fallback_target_subject(question)}
    raw = str(llm_result.get("response") or "").strip()
    target_subject: Optional[Dict[str, Any]] = None
    try:
        data = json.loads(raw)
        mode = str(data.get("answer_mode") or "").strip()
        target_key = _normalize_relationship_target_key(data.get("target_subject_key") or "")
        if target_key in TARGET_SUBJECTS:
            meta = TARGET_SUBJECTS.get(target_key) or {}
            target_subject = {
                "key": target_key,
                "label": meta.get("label") or target_key.replace("_", " "),
                "base_house": meta.get("base_house"),
                "confidence": str(data.get("confidence") or "medium"),
                "source": "llm",
            }
        if mode in ANSWER_MODES:
            if target_subject is None:
                target_subject = _fallback_target_subject(question)
            return {"answer_mode": mode, "target_subject": target_subject}
    except Exception:
        pass
    m = re.search(r'"answer_mode"\s*:\s*"([^"]+)"', raw)
    if m:
        mode = str(m.group(1) or "").strip()
        if mode in ANSWER_MODES:
            target_match = re.search(r'"target_subject_key"\s*:\s*"([^"]+)"', raw)
            if target_match:
                target_key = _normalize_relationship_target_key(target_match.group(1) or "")
                if target_key in TARGET_SUBJECTS:
                    meta = TARGET_SUBJECTS.get(target_key) or {}
                    target_subject = {
                            "key": target_key,
                            "label": meta.get("label") or target_key.replace("_", " "),
                            "base_house": meta.get("base_house"),
                            "confidence": "medium",
                            "source": "llm_regex",
                    }
            if target_subject is None:
                target_subject = _fallback_target_subject(question)
            return {"answer_mode": mode, "target_subject": target_subject}
    logger.warning("instant answer mode llm output invalid, falling back: %s", _truncate(raw, 240))
    fallback_mode = _infer_answer_mode(question, intent, history)
    return {"answer_mode": fallback_mode, "target_subject": _fallback_target_subject(question)}


def _top_dasha_lines(levels: Dict[str, Any], limit: int = 3) -> List[str]:
    rows: List[str] = []
    ordered = sorted(
        ((lvl, row) for lvl, row in (levels or {}).items() if isinstance(row, dict) and row.get("p")),
        key=lambda item: -_support_rank(item[0]),
    )
    for lvl, row in ordered[:limit]:
        planet = str(row.get("p") or "")
        if not planet:
            continue
        houses = ", ".join(str(v) for v in (row.get("rh") or [])[:3]) or "key houses"
        place = f"house {row.get('h')}" if row.get("h") is not None else "its natal position"
        rows.append(
            f"{str(lvl).upper()} runs through {planet} from {place}, linking houses {houses} and highlighting {_planet_theme(planet)}."
        )
    return rows


def _format_active_dasha_context(levels: Dict[str, Any], period_window: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    order = ["md", "ad", "pd"]
    if (period_window or {}).get("use_sk_pr"):
        order.extend(["sk", "pr"])
    for lvl in order:
        row = (levels or {}).get(lvl) or {}
        if not isinstance(row, dict) or not row.get("p"):
            continue
        out[lvl] = {
            "planet": row.get("p"),
            "natal_house": row.get("h"),
            "natal_sign": row.get("sn"),
            "lordships": row.get("rh") or [],
        }
    return out


def _format_transit_context(transit_rows: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for planet, row in (transit_rows or {}).items():
        if not isinstance(row, dict):
            continue
        out[str(planet)] = {
            "sign": row.get("sign"),
            "house_from_lagna": row.get("house_from_lagna"),
            "nakshatra": row.get("nakshatra"),
            "retrograde": bool(row.get("retrograde")),
        }
    return out


def _stable_transit_context(transit_rows: Dict[str, Dict[str, Any]], period_window: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    include = {"Jupiter", "Saturn", "Rahu", "Ketu"}
    kind = str((period_window or {}).get("kind") or "current")
    if kind == "day":
        include = include | {"Moon", "Sun"}
    for planet, row in (transit_rows or {}).items():
        if planet not in include or not isinstance(row, dict):
            continue
        out[planet] = dict(row)
    return out


def _build_month_tone_signals(
    current_transits_formatted: Dict[str, Any],
    current_dashas_context: Dict[str, Any],
    active_area_rows: List[Dict[str, Any]],
    activation_mechanisms: List[Dict[str, Any]],
    period_window: Dict[str, Any],
) -> Dict[str, Any]:
    if str((period_window or {}).get("kind") or "") != "window":
        return {"enabled": False, "signals": [], "summary": ""}
    sun = (current_transits_formatted or {}).get("Sun") or {}
    if not isinstance(sun, dict) or not sun:
        return {"enabled": False, "signals": [], "summary": ""}
    sun_house = _safe_int(sun.get("house_from_lagna"))
    sun_sign = str(sun.get("sign") or "")
    dominant_houses = {
        int(row.get("house"))
        for row in (active_area_rows or [])
        if _safe_int(row.get("house")) is not None
    }
    activated_houses = set(dominant_houses)
    for row in (activation_mechanisms or []):
        if not isinstance(row, dict):
            continue
        house = _safe_int(row.get("house"))
        if house is not None:
            activated_houses.add(house)
    signals: List[str] = []
    if sun_house in activated_houses:
        area_label = HOUSE_THEME_LABELS.get(sun_house, "that area")
        if sun_house in dominant_houses:
            signals.append(
                f"Transit Sun is moving through house {sun_house}, one of the dominant activated houses for this month, so it can set the visible tone around {area_label}."
            )
        else:
            signals.append(
                f"Transit Sun is moving through house {sun_house}, which is being actively triggered by the current dasha chain, so it can still set the visible tone around {area_label} this month."
            )
    for lvl, row in (current_dashas_context or {}).items():
        if not isinstance(row, dict):
            continue
        planet = str(row.get("planet") or "")
        natal_sign = str(row.get("natal_sign") or "")
        natal_house = _safe_int(row.get("natal_house"))
        if sun_sign and natal_sign and sun_sign == natal_sign:
            signals.append(
                f"Transit Sun is in {sun_sign}, the natal sign of {str(lvl).upper()} lord {planet}, so it can spotlight that period lord's agenda during the month."
            )
        if sun_house is not None and natal_house is not None and sun_house == natal_house:
            signals.append(
                f"Transit Sun is passing through house {sun_house}, the natal house of {str(lvl).upper()} lord {planet}, so it can make that period lord's themes more visible this month."
            )
        transit_row = (current_transits_formatted or {}).get(planet) or {}
        if not isinstance(transit_row, dict) or not transit_row:
            continue
        if str(transit_row.get("sign") or "") == sun_sign and _safe_int(transit_row.get("house_from_lagna")) == sun_house:
            signals.append(
                f"Transit Sun is conjunct the transiting {planet} influence in {sun_sign}/house {sun_house}, which can give that active period lord extra tonal weight this month."
            )
    deduped = list(dict.fromkeys(signals))
    return {"enabled": bool(deduped), "signals": deduped[:4], "summary": deduped[0] if deduped else ""}


def _filter_transit_pressure_window(tr: Dict[str, Any], period_window: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(tr, dict):
        return {}
    start_dt = _parse_ymd((period_window or {}).get("start"))
    end_dt = _parse_ymd((period_window or {}).get("end"))
    if not start_dt or not end_dt:
        return dict(tr)
    out: Dict[str, Any] = {k: v for k, v in tr.items() if k not in {"dp", "n", "th", "nh"}}
    filtered_dp: List[Dict[str, Any]] = []
    th_counts: Dict[str, int] = {}
    nh_counts: Dict[str, int] = {}
    for row in tr.get("dp") or []:
        if not isinstance(row, dict):
            continue
        sd = _parse_ymd(row.get("sd"))
        ed = _parse_ymd(row.get("ed"))
        if not sd or not ed:
            continue
        if ed < start_dt or sd > end_dt:
            continue
        filtered_dp.append(row)
        try:
            th = int(row.get("th"))
            th_counts[str(th)] = th_counts.get(str(th), 0) + 1
        except (TypeError, ValueError):
            pass
        try:
            nh = int(row.get("nh"))
            nh_counts[str(nh)] = nh_counts.get(str(nh), 0) + 1
        except (TypeError, ValueError):
            pass
    out["dp"] = filtered_dp[:10]
    out["n"] = len(filtered_dp)
    if th_counts:
        out["th"] = th_counts
    if nh_counts:
        out["nh"] = nh_counts
    return out


def _transit_lines(tr: Dict[str, Any], limit: int = 2) -> List[str]:
    out: List[str] = []
    for row in (tr.get("dp") or [])[:limit]:
        if not isinstance(row, dict):
            continue
        tp = row.get("tp")
        np = row.get("np")
        th = row.get("th")
        nh = row.get("nh")
        at = row.get("at")
        if tp and np:
            out.append(
                f"Transit {tp} is interacting with natal {np}; the transit-side activation is around house {th or 'unknown'} while the natal planet involved sits in house {nh or 'unknown'}, which can trigger {at or 'noticeable movement'}."
            )
    if not out and (tr.get("pd") or []):
        out.append(f"Current transit pressure is concentrated through {', '.join(str(v) for v in (tr.get('pd') or [])[:3])}.")
    return out


def _topic_signal_lines(topic_key: Optional[str], topic_payload: Dict[str, Any]) -> List[str]:
    if not topic_key or not isinstance(topic_payload, dict):
        return []
    if topic_key == "career":
        fn = ", ".join(str(v) for v in (topic_payload.get("fn") or [])[:3]) or "mixed functions"
        return [
            f"Career mode looks {topic_payload.get('mode') or 'mixed'}, with strongest emphasis on {fn}.",
            f"Work visibility is {topic_payload.get('vis') or 'mixed'} and the dominant houses are {', '.join(str(v) for v in (topic_payload.get('dom') or [])[:4])}.",
        ]
    if topic_key == "relationship":
        return [
            f"Relationship materialization score is {topic_payload.get('mat', 0)} while friction is {topic_payload.get('fr', 0)}, so the overall tone is {topic_payload.get('mode') or 'mixed'}.",
            f"Continuity pressure is {topic_payload.get('ct', 0)} with key houses {', '.join(str(v) for v in (topic_payload.get('dom') or [])[:4])}.",
        ]
    if topic_key == "wealth":
        risk = topic_payload.get("risk") or {}
        return [
            f"Wealth-building mode looks {topic_payload.get('mode') or 'mixed'} with accumulation {topic_payload.get('acc', 0)}, gains {topic_payload.get('gain', 0)}, and fortune {topic_payload.get('fort', 0)}.",
            f"Risk band is {risk.get('band') or 'mixed'} because debt {risk.get('debt', 0)}, sudden swings {risk.get('sudden', 0)}, and expenses {risk.get('expense', 0)} are also active.",
        ]
    if topic_key == "health":
        return [
            f"Health pattern looks {topic_payload.get('pattern') or 'mixed'} with a {topic_payload.get('tone') or 'mixed'} tone.",
            f"The main risk mix is vitality {((topic_payload.get('risk') or {}).get('vit')) or 0}, acute pressure {((topic_payload.get('risk') or {}).get('acu')) or 0}, chronic pressure {((topic_payload.get('risk') or {}).get('chr')) or 0}.",
        ]
    return []


def _divisional_lines(dx: Dict[str, Any], topic_key: Optional[str]) -> List[str]:
    out: List[str] = []
    topic = (dx or {}).get("topic") or {}
    current = ((dx or {}).get("current") or {}).get("topic") or {}
    if topic.get("support"):
        avail = [code for code, enabled in (topic.get("avail") or {}).items() if enabled]
        if avail:
            out.append(
                f"Divisional support is {topic.get('support')} through {', '.join(avail[:3])} for the core topic."
            )
    if current.get("support"):
        out.append(f"Current divisional timing reads as {current.get('support')} for the active periods.")
    if topic_key and topic_key in (dx or {}) and isinstance(dx.get(topic_key), dict) and dx.get(topic_key, {}).get("support"):
        out.append(f"{str(topic_key).capitalize()} divisional background is {dx.get(topic_key, {}).get('support')}.")
    return out[:2]


def _build_answer_mode_contract(answer_mode: str, category: str, period_window: Dict[str, Any], time_relation: str) -> Dict[str, Any]:
    cat = str(category or "general").lower()
    base = {
        "answer_mode": answer_mode,
        "category": cat,
        "time_relation": time_relation,
        "primary_evidence": [],
        "secondary_evidence": [],
        "avoid_drift": [],
        "answer_skeleton": "",
    }
    if answer_mode == "explanation_mechanism":
        base.update(
            {
                "primary_evidence": ["activation_mechanisms", "house_activation", "current_transits_formatted"],
                "secondary_evidence": ["active_dashas_formatted", "transit_pressure"],
                "avoid_drift": ["fresh broad reading", "generic personality prose", "unasked timing detours"],
                "answer_skeleton": "Direct explanation -> Exact chart mechanism -> Correction if earlier claim was too strong",
            }
        )
    elif answer_mode == "trait_nature":
        base.update(
            {
                "primary_evidence": ["personality_axes", "area_behavior_axes", "natal_snapshot", "house_activation", "divisional_specifics"],
                "secondary_evidence": ["active_dashas_formatted"],
                "avoid_drift": ["current dasha dominating the answer", "broad event prediction", "random transit commentary", "generic flattering summary", "whole-life summary without personality structure"],
                "answer_skeleton": "Core temperament -> Emotional style -> Expression/communication -> Pressure response -> Two area-specific behavior patterns (such as work/home/relationship/speech) -> One strength and one caution",
            }
        )
    elif answer_mode == "relationship_person":
        base.update(
            {
                "primary_evidence": ["person_profile_axes", "target_subject", "target_chart_context", "topic_signals", "focus_houses", "divisional_specifics", "activation_mechanisms"],
                "secondary_evidence": ["natal_snapshot", "active_dashas_formatted"],
                "avoid_drift": ["current-period narrative unless asked", "full marriage timing", "career detours", "using the native's ascendant or Moon as the asked person's direct personality anchor"],
                "answer_skeleton": "Target-person anchor -> Temperament/value pattern -> Communication/relating style -> One caution",
            }
        )
    elif answer_mode == "timing_window":
        base.update(
            {
                "primary_evidence": ["active_dashas_formatted", "dasha_level_effects", "dasha_chain_synthesis", "active_areas", "transit_pressure"],
                "secondary_evidence": ["month_tone", "divisional_support.current_topic", "topic_signals"],
                "avoid_drift": ["broad lifetime reading", "unanchored natal-only reading", "whole-month prose from one-day fast-planet snapshots"],
                "answer_skeleton": "Window verdict -> Dasha-chain synthesis (MD/AD/PD and SK/PR when enabled) -> Top 2-3 active areas in this period -> Exact mechanism for each major area -> Month tone-setter if truly relevant -> Opportunity vs pressure -> Practical use of the period",
            }
        )
    elif answer_mode == "event_prediction":
        base.update(
            {
                "primary_evidence": ["active_dashas_formatted", "activation_mechanisms", "transit_pressure"],
                "secondary_evidence": ["divisional_support.current_topic", "current_transits_formatted"],
                "avoid_drift": ["generic motivation talk", "unrelated personality analysis", "question-led yes bias", "upgrading activation into certainty"],
                "answer_skeleton": "Evidence-led verdict -> Why the chart supports or obstructs the event -> What is activation versus what is certainty -> Timing caution",
            }
        )
    elif answer_mode == "potential_capacity":
        base.update(
            {
                "primary_evidence": ["topic_signals", "divisional_support.topic", "natal_snapshot"],
                "secondary_evidence": ["house_activation"],
                "avoid_drift": ["current-period overemphasis", "daily transit narration"],
                "answer_skeleton": "Core promise -> Strongest capacity/fit -> Limitation or caution -> Practical direction",
            }
        )
    elif answer_mode == "comparison_choice":
        base.update(
            {
                "primary_evidence": ["topic_signals", "activation_mechanisms", "active_dashas_formatted"],
                "secondary_evidence": ["divisional_support", "current_transits_formatted"],
                "avoid_drift": ["answering only one side", "broad philosophy without choice logic"],
                "answer_skeleton": "Option comparison -> Which side is stronger and why -> Risk on the weaker side -> Practical recommendation",
            }
        )
    elif answer_mode == "problem_diagnosis":
        base.update(
            {
                "primary_evidence": ["top_risks", "activation_mechanisms", "transit_pressure"],
                "secondary_evidence": ["divisional_support.current_topic", "active_dashas_formatted"],
                "avoid_drift": ["generic reassurance", "unasked remedy list", "broad event prediction"],
                "answer_skeleton": "Main astrological cause -> How it is being activated -> Why it persists/softens -> Practical handling",
            }
        )
    elif answer_mode == "remedy_action":
        base.update(
            {
                "primary_evidence": ["top_risks", "active_dashas_formatted", "activation_mechanisms"],
                "secondary_evidence": ["divisional_support.current_topic"],
                "avoid_drift": ["too many remedies", "non-astrological lecture"],
                "answer_skeleton": "Problem focus -> Why this needs remedy/action -> Short practical steps -> One caution",
            }
        )
    else:
        base.update(
            {
                "primary_evidence": ["top_supports", "activation_mechanisms", "topic_signals"],
                "secondary_evidence": ["divisional_support", "active_dashas_formatted"],
                "avoid_drift": ["whole-life drift", "unasked detailed timing"],
                "answer_skeleton": "Direct answer -> Strongest chart reasons -> One support and one caution -> Practical takeaway",
            }
        )
    if cat in {"career", "job", "promotion", "business"} and answer_mode in {"topic_reading", "potential_capacity"}:
        base["answer_skeleton"] = "Career promise -> Best fit/work function -> Current support or drag -> Practical direction"
    elif cat in {"marriage", "love", "relationship", "partner", "spouse"} and answer_mode in {"topic_reading", "event_prediction"}:
        base["answer_skeleton"] = "Relationship promise -> Current activation -> Support vs friction -> Practical guidance"
    return base


def _normalize_instant_evidence(
    answer_mode: str,
    category: str,
    instant_parashari: Dict[str, Any],
    current_transits_formatted: Dict[str, Any],
    current_dashas_context: Dict[str, Any],
    birth_summary: Optional[Dict[str, Any]] = None,
    natal_snapshot: Optional[Dict[str, Any]] = None,
    relationship_target: Optional[Dict[str, Any]] = None,
    target_chart_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    contract = _build_answer_mode_contract(
        answer_mode,
        category,
        instant_parashari.get("period_window") if isinstance(instant_parashari.get("period_window"), dict) else {},
        str(instant_parashari.get("time_relation") or "current"),
    )
    top_supports = list((instant_parashari.get("top_supports") or [])[:3])
    top_risks = list((instant_parashari.get("top_risks") or [])[:3])
    mechanisms = list((instant_parashari.get("activation_mechanisms") or [])[:3])
    dominant_houses = list((instant_parashari.get("dominant_houses") or [])[:3])
    divisional_support = instant_parashari.get("divisional_support") or {}
    topic_signals = instant_parashari.get("topic_signals") or {}
    navamsa_root_fruit = instant_parashari.get("navamsa_root_fruit") or []
    current_topic_support = (divisional_support.get("current_topic") or {}).get("support")
    topic_support = (divisional_support.get("topic") or {}).get("support")
    period_window = instant_parashari.get("period_window") if isinstance(instant_parashari.get("period_window"), dict) else {}
    hi_for_area_ranking = instant_parashari.get("house_activation") or {}
    if answer_mode == "timing_window" and str(category or "").lower() in {"general", "timing"}:
        hi_for_area_ranking = _all_house_activation_from_levels(instant_parashari.get("active_dashas") or {})
    active_area_rows = _rank_house_activation_rows(hi_for_area_ranking, limit=4)
    stable_transits = _stable_transit_context(current_transits_formatted, period_window)
    month_tone = _build_month_tone_signals(
        current_transits_formatted,
        current_dashas_context,
        active_area_rows,
        mechanisms,
        period_window,
    )
    window_area_lines = _window_area_mechanism_lines(active_area_rows, instant_parashari.get("active_dashas") or {}, limit=3)
    repeated_house_themes = _repeated_house_theme_lines(active_area_rows, limit=3)
    dasha_chain_lines = _dasha_chain_synthesis_lines(
        current_dashas_context,
        instant_parashari.get("active_dashas") or {},
        current_transits_formatted,
        period_window,
    )
    dasha_level_effects = _dasha_level_effects(
        current_dashas_context,
        instant_parashari.get("active_dashas") or {},
        current_transits_formatted,
        period_window,
    )
    personality_axes = _build_personality_axes(birth_summary or {}, natal_snapshot or {})
    area_behavior_axes = _build_area_behavior_axes(birth_summary or {}, natal_snapshot or {})
    person_profile_axes = _build_person_profile_axes(
        natal_snapshot or {},
        divisional_support,
        relationship_target,
        target_chart_context,
    )
    divisional_specifics = _divisional_specific_lines(divisional_support, navamsa_root_fruit, limit=2)
    risk_specifics = _risk_specific_lines(top_risks, mechanisms, instant_parashari.get("transit_pressure") or {}, limit=2)
    claim_gates = {
        "allow_divisional_mentions": bool(divisional_specifics),
        "allow_abstract_risk_labels": bool(risk_specifics),
    }
    contradiction_flags: List[str] = []
    if top_risks and top_supports:
        contradiction_flags.append("Both supportive and pressurizing factors are active, so the answer should balance support with caution.")
    if current_topic_support == "weak" and topic_support in {"supportive", "strong"}:
        contradiction_flags.append("The natal/divisional promise looks better than the immediate activation, so current delivery may lag the underlying promise.")
    if str((period_window or {}).get("kind") or "") == "window":
        contradiction_flags.append("Do not narrate the whole month from a one-day Sun or Moon snapshot; use MD/AD/PD first and treat only slow-planet transits as month-wide anchors.")
    primary_drivers = top_supports
    if answer_mode == "timing_window":
        primary_drivers = window_area_lines or top_supports
    normalized = {
        "answer_mode_contract": contract,
        "primary_drivers": primary_drivers,
        "secondary_modifiers": risk_specifics or [],
        "personality_axes": personality_axes,
        "area_behavior_axes": area_behavior_axes,
        "person_profile_axes": person_profile_axes,
        "target_subject": relationship_target or {"key": "self", "label": "self", "base_house": 1},
        "target_chart_context": target_chart_context or {},
        "mechanism_links": mechanisms,
        "dasha_chain_synthesis": dasha_chain_lines,
        "dasha_level_effects": dasha_level_effects,
        "repeated_house_themes": repeated_house_themes,
        "dominant_house_signals": dominant_houses,
        "active_areas": active_area_rows,
        "window_area_mechanisms": window_area_lines,
        "current_timing": {
            "active_dashas": current_dashas_context,
            "time_relation": instant_parashari.get("time_relation"),
            "period_window": period_window,
        },
        "topic_confirmation": {
            "topic_signals": topic_signals,
            "topic_support": topic_support,
            "current_topic_support": current_topic_support,
        },
        "divisional_specifics": divisional_specifics,
        "risk_specifics": risk_specifics,
        "transit_anchor_rows": current_transits_formatted,
        "stable_transits": stable_transits,
        "month_tone": month_tone,
        "claim_gates": claim_gates,
        "window_rules": {
            "month_like": str((period_window or {}).get("kind") or "") == "window",
            "use_pd": bool((period_window or {}).get("use_pd")),
            "use_sk_pr": bool((period_window or {}).get("use_sk_pr")),
            "snapshot_warning": "Do not generalize a whole month from fast-planet snapshots unless explicitly narrowed to a day or very short period.",
        },
        "contradiction_flags": contradiction_flags,
        "avoid_drift": contract.get("avoid_drift") or [],
    }
    return normalized


def _compact_parashari_evidence(
    *,
    birth_data: Dict[str, Any],
    question: str,
    intent: Optional[Dict[str, Any]],
    period_window: Dict[str, Any],
) -> Dict[str, Any]:
    static_context = _INSTANT_CONTEXT_BUILDER._build_static_context(birth_data)
    agent_ctx = AgentContext(
        birth_data=birth_data,
        user_question=question,
        intent_result=intent or {},
        precomputed_static=static_context,
    )
    payload = build_parashari_agent_payload(agent_ctx, question)
    px = payload.get("px") or {}
    category = str((intent or {}).get("category") or px.get("cat") or "general").lower()
    topic_key = PARASHARI_TOPIC_MAP.get(category)
    topic_payload = px.get(topic_key) if topic_key else None
    levels = px.get("D") or {}
    hi = px.get("HI") or {}
    tr = px.get("TR") or {}
    tr = _filter_transit_pressure_window(tr, period_window)
    dx = px.get("dx") or {}

    dasha_line_limit = 2
    if (period_window or {}).get("use_sk_pr"):
        dasha_line_limit = 5
    elif (period_window or {}).get("use_pd"):
        dasha_line_limit = 3

    supports: List[str] = []
    supports.extend(_top_dasha_lines(levels, limit=dasha_line_limit))
    supports.extend(_dominant_house_lines(hi, limit=2))
    supports.extend(_divisional_lines(dx, topic_key)[:1])
    if topic_payload:
        supports.extend(_topic_signal_lines(topic_key, topic_payload)[:1])

    risks: List[str] = []
    if topic_key == "relationship" and isinstance(topic_payload, dict) and topic_payload.get("fr", 0) >= topic_payload.get("mat", 0):
        risks.append("Relationship friction is at least as strong as materialization, so reactions and misunderstandings need care.")
    if topic_key == "wealth" and isinstance(topic_payload, dict):
        risk = topic_payload.get("risk") or {}
        if risk.get("band") in {"medium", "high"}:
            risks.append("Financial risk factors are active, so avoid impulsive moves and overcommitting resources.")
    if topic_key == "health" and isinstance(topic_payload, dict) and topic_payload.get("pattern") in {"acute", "chronic"}:
        risks.append(f"Health pattern leans {topic_payload.get('pattern')}, so strain signals should not be brushed aside.")
    transit_risk_lines = _transit_lines(tr, limit=1)
    risks.extend(transit_risk_lines)
    if not risks and dx.get("current", {}).get("topic", {}).get("support") == "weak":
        risks.append("Current divisional timing is not fully supportive, so results may come with delay or extra effort.")

    summary = {
        "source": px.get("src") or "current",
        "category": px.get("cat") or category,
        "focus_houses": px.get("hs") or [],
        "topic_key": topic_key,
        "active_dashas": levels,
        "active_dashas_formatted": _format_active_dasha_context(levels, period_window),
        "house_activation": hi,
        "transit_pressure": tr,
        "transit_pressure_legend": {
            "th": "transit-side house activated by the transit interaction",
            "nh": "natal house of the natal planet involved in the transit interaction",
            "dp": "compact transit interaction rows, not literal planet placement rows",
        },
        "divisional_support": {
            "topic": (dx.get("topic") or {}),
            "current_topic": ((dx.get("current") or {}).get("topic") or {}),
        },
        "topic_signals": topic_payload or {},
        "top_supports": supports[:4],
        "top_risks": risks[:3],
        "topic_band": _topic_support_band(topic_payload or {}) or _topic_support_band((dx.get("current") or {}).get("topic") or {}) or "mixed",
        "dominant_houses": [line for line in _dominant_house_lines(hi, limit=3)],
        "activation_mechanisms": _house_activation_mechanisms(px.get("hs") or [], hi, levels, limit=3),
    }
    if dx.get("rf"):
        summary["navamsa_root_fruit"] = list(dx.get("rf")[:4])
    return summary


def _instant_parashari_instruction_block(
    category: str,
    mode: str,
    answer_mode: str,
    period_window: Dict[str, Any],
    time_relation: str,
    normalized_evidence: Dict[str, Any],
) -> str:
    period_span = int((period_window or {}).get("span_days") or 0)
    contract = (normalized_evidence or {}).get("answer_mode_contract") or {}
    if answer_mode == "trait_nature":
        primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "personality axes"
        secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "secondary modifiers"
        avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "broad drift"
        skeleton = str(contract.get("answer_skeleton") or "Core temperament -> Emotional style -> Expression/communication -> Pressure response -> Two area-specific behavior patterns -> One strength and one caution")
        return "\n".join(
            [
                f"This answer uses universal answer mode `{answer_mode}`.",
                "CRITICAL: Follow the method instructions below exactly.",
                "CRITICAL: Treat this as a stable personality/behavior reading, not a period prediction.",
                "CRITICAL: Your response will be marked failed if you turn this into a life summary, if you let current dasha dominate without being asked, or if you flatten behavior into one generic trait.",
                f"Answer skeleton: {skeleton}.",
                f"Primary evidence priority: {primary}.",
                f"Secondary evidence only after primary evidence: {secondary}.",
                f"Avoid these drifts: {avoid}.",
                "- `normalized_evidence.personality_axes`: start from these first for core temperament, emotional style, expression, and pressure response.",
                "- `normalized_evidence.area_behavior_axes`: use these to distinguish home behavior, work behavior, relationship behavior, children/family behavior, speech/expression, and pressure/conflict response.",
                "- `normalized_evidence.divisional_specifics`: if you mention D9 or any divisional support, cite at least one concrete line from here. Otherwise do not mention it.",
                "- `normalized_evidence.mechanism_links`: use these only to justify a behavior pattern if needed; do not let them take over the whole answer.",
                "Use rashi as style/flavor and nakshatra as motive/texture whenever those are available in the provided evidence.",
                "If the question is broad, mention at least two area-specific behavior patterns after the core personality read.",
                "If the question points to one area like work, home, spouse, children, speech, or pressure, prioritize that area behavior axis first.",
                "Do not mention current transits unless they are explicitly necessary, which is rare for this category.",
                "Do not give vague flattering language. Prefer plain, mechanism-first wording.",
            ]
        )
    if answer_mode == "relationship_person":
        primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "person profile axes"
        secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "secondary modifiers"
        avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "native-self drift"
        skeleton = str(contract.get("answer_skeleton") or "Target-person anchor -> Temperament/value pattern -> Communication/relating style -> One caution")
        return "\n".join(
            [
                f"This answer uses universal answer mode `{answer_mode}`.",
                "CRITICAL: Follow the method instructions below exactly.",
                "CRITICAL: Treat this as a reading about the asked person, not the native directly.",
                "CRITICAL: Your response will be marked failed if you describe the asked person by using the native's Lagna, Moon, or natal houses as if they belonged directly to that person.",
                f"Answer skeleton: {skeleton}.",
                f"Primary evidence priority: {primary}.",
                f"Secondary evidence only after primary evidence: {secondary}.",
                f"Avoid these drifts: {avoid}.",
                "- `normalized_evidence.target_subject`: this tells you who the reading is about and which anchor house defines them.",
                "- `target_chart_context`: this is the rotated chart frame for the asked person. If the target_subject is not self, use this as the primary frame for ascendant, houses, planets, and transits.",
                "- `normalized_evidence.person_profile_axes`: start from these first for nature, temperament, communication, and relating style.",
                "- `normalized_evidence.divisional_specifics`: if you mention D9 or divisional support, cite a concrete line from here or do not mention it.",
                "If you mention a house position for the asked person, it must come from the target chart context or target-based profile axes, not from the native's direct house placement.",
                "Do not bring in current dasha or transit narration unless it is explicitly needed for this relationship-person answer.",
                "Do not flatten all relatives into spouse logic. Follow the target_subject and target_chart_context provided.",
                "Use plain, mechanism-first wording rather than flattering or dramatic language.",
            ]
        )
    time_authority_block = (
        "Time authority rule: follow `instant_parashari.source`. "
        "If source is `window` or `day`, the asked period overrides generic current-chart narration."
    )
    time_relation_block = {
        "past": "This asked period is in the past relative to today. Speak in past framing like what was active or what the period likely brought, not as if it is still upcoming.",
        "future": "This asked period is in the future relative to today. Speak in future framing like what is likely to unfold, not as if it already happened.",
        "current": "This asked period includes or touches the present. Speak in present/near-future framing.",
    }.get(str(time_relation or "current"), "Speak with correct time framing for the asked period.")
    dasha_depth_block = (
        "For short asked windows, do not stop at Mahadasha or Antardasha."
        if period_span > 0
        else ""
    )
    if (period_window or {}).get("use_sk_pr"):
        dasha_depth_block = (
            "For this very short window, it is critical to read MD/AD/PD first and also use Sookshma and Prana as real timing drivers, not optional extras."
        )
    elif (period_window or {}).get("use_pd"):
        dasha_depth_block = (
            "For this asked period, it is critical to read MD/AD/PD together. PD must matter for month-level or short-window answers; do not answer from MD/AD alone."
        )
    primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "top supports and activation mechanisms"
    secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "secondary modifiers"
    avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "broad drift"
    skeleton = str(contract.get("answer_skeleton") or "Direct answer -> strongest reasons -> practical takeaway")
    return "\n".join(
        [
            f"This answer uses universal answer mode `{answer_mode}`.",
            "CRITICAL: Follow the method instructions below exactly.",
            "CRITICAL: For timing/window answers, your response will be marked failed if you ignore PD, ignore Sookshma/Prana when enabled, flatten all dasha levels into one blob, or replace explicit dasha-role reasoning with generic summary prose.",
            "CRITICAL: For timing/window answers, your response will be marked failed if you do not distinguish the jobs of MD, AD, PD, and SK/PR when they are available in the provided evidence.",
            "CRITICAL: Do not be biased by the wording of the user's question. Center the answer on astrological logic, not on agreeing with what the user seems to want.",
            "CRITICAL: For event-prediction questions like 'will X happen' or 'is X likely', act like an investigator. Examine support, obstruction, and uncertainty before giving the verdict.",
            f"Answer skeleton: {skeleton}.",
            f"Primary evidence priority: {primary}.",
            f"Secondary evidence only after primary evidence: {secondary}.",
            f"Avoid these drifts: {avoid}.",
            time_authority_block,
            time_relation_block,
            dasha_depth_block,
            "Read `instant_parashari` the way the deep Parashari branch reads `px`.",
            "- `normalized_evidence`: this is the main evidence hierarchy for this answer. Prefer it over freelancing from raw context.",
            "- `normalized_evidence.primary_drivers`: start from these first.",
            "- `normalized_evidence.secondary_modifiers`: use them to soften, complicate, or caution the answer after the primary drivers.",
            "- `normalized_evidence.personality_axes`: this is critical for trait/nature/characteristics questions. Start from these stable natal anchors before widening into any other interpretation.",
            "- `normalized_evidence.area_behavior_axes`: this is critical for behavior questions. Use it to distinguish home behavior, work behavior, relationship behavior, children/family behavior, speech/expression, and pressure/conflict response instead of flattening behavior into one generic trait.",
            "- `normalized_evidence.person_profile_axes`: this is critical for relationship-person questions. Use it before anything else for wife, husband, partner, child, sibling, parent, or other asked-person behavior and characteristics.",
            "- `normalized_evidence.target_subject`: this tells you which person the reading is about and which house is being used as the anchor. Follow it rather than defaulting to the native's personality anchors.",
            "- `target_chart_context`: if the target_subject is not self, this is the rotated target chart frame. Use it as the primary chart context for that person's houses, planets, and transits.",
            "- `normalized_evidence.mechanism_links`: use these when you need to justify why a house or topic is being activated.",
            "- `normalized_evidence.dasha_level_effects`: this is critical for timing/window answers. Use it to distinguish what MD sets in the background, what AD carries as the main channel, what PD sharpens for the month/window, and what Sookshma/Prana trigger more finely.",
            "- `normalized_evidence.dasha_chain_synthesis`: this is critical for timing/window answers. Read each active dasha lord through natal residence, ruled houses, active aspects, and current transit house before you synthesize the final themes.",
            "- `normalized_evidence.repeated_house_themes`: this is critical for timing/window answers. Use it to notice which houses repeat across the active dasha chain, then combine those repeated house significations into the final prediction.",
            "- `normalized_evidence.active_areas`: for month/window questions, rank the top 2-3 active life areas from here before building the narrative. Do not jump to one storyline too early.",
            "- `normalized_evidence.window_area_mechanisms`: for month/window questions, use these as the concrete 'because' lines behind each major theme. This is especially important for general month questions.",
            "- `normalized_evidence.month_tone`: for month/window questions, use this only as a tone-setter layer. Sun can set the month's visible tone when it is contacting active period lords or moving through a dominant activated house, but it does not replace MD/AD/PD.",
            "- `normalized_evidence.topic_confirmation`: use this to confirm the topic promise versus current activation.",
            "- `normalized_evidence.divisional_specifics`: if you mention D9 or any divisional support, cite at least one concrete line from here. Otherwise do not mention divisional support vaguely.",
            "- `normalized_evidence.risk_specifics`: if you mention volatility, suddenness, expense pressure, obstruction, or risk, cite at least one concrete line from here. Otherwise do not mention the risk label vaguely.",
            "- `normalized_evidence.claim_gates`: obey these as hard gates. If a gate is false, do not mention that claim type at all.",
            "- `normalized_evidence.stable_transits`: for month-style answers, use these slow-planet placements if you need transit anchors. Do not narrate the whole month from a one-day Sun or Moon snapshot.",
            "- `normalized_evidence.window_rules`: obey these explicitly for month/window answers, especially the snapshot warning.",
            "- `normalized_evidence.contradiction_flags`: if present, explicitly balance the answer instead of sounding absolute.",
            "- `active_dashas`: these are the active time lords. Use them to say which planets are currently driving the result and through which ruled houses / natal placement.",
            "- `house_activation`: this shows whether the important houses are being activated by rulership, occupation, or aspect from active dasha lords. This should drive the core interpretation.",
            "For timing/window answers, first identify what each active lord is activating through natal residence, rulership, transit position, and active aspects. Then combine the house themes that repeat across MD/AD/PD and, when enabled, Sookshma/Prana. Only after that should you synthesize the prediction.",
            "If PD or Sookshma is enabled for this asked period, treat it as critical evidence. Do not collapse the answer into only Mahadasha and Antardasha language.",
            "For timing/window answers, surface the dasha chain explicitly in the answer. Do not hide MD/AD/PD and Sookshma/Prana behind generic summary prose.",
            "Use the dasha levels with distinct jobs: MD sets the background period, AD carries the main channel, PD sharpens the month/window result, and Sookshma/Prana refine delivery when enabled.",
            "Your timing/window answer fails if it does not make the dasha roles visible enough for a reviewer to see what MD did, what AD did, what PD changed, and what Sookshma/Prana refined.",
            "Your timing/window answer fails if it jumps straight to polished conclusions like visibility, pressure, or opportunity without first grounding them in the active dasha roles and repeated house themes.",
            "These are critical teachings for all timing/window answers, not just this question: read the active dasha chain, identify the houses activated by each lord through natal residence, rulership, transit position, and aspects, combine the repeating house themes, and then predict.",
            "- `transit_pressure`: use this as a compact near-term filter for the asked period. For short windows, use transit pressure to refine the period answer, not to replace dasha logic.",
            "- `transit_pressure_legend`: `th` means the transit-side house being activated in that interaction, `nh` means the natal house of the natal planet involved. These are interaction markers, not placement markers.",
            "- `current_transits.planets` / `current_transits_formatted`: if you mention a transit planet's sign or house, quote it exactly from there.",
            "- Never treat `transit_pressure` or target-house hits as proof that Jupiter/Saturn/Rahu is physically in that house. `transit_pressure` shows impact, not exact sign/house placement.",
            "- `divisional_support`: use this to confirm or soften the answer. If divisional support is weak or missing, reduce certainty instead of sounding absolute.",
            "If you mention Navamsa, D9, or any divisional support, you must say what it is specifically showing from the provided evidence. Saying only 'D9 is supportive' or 'divisional charts support this' is a failed answer.",
            "If you mention risk words like volatility, suddenness, feast-or-famine, obstruction, pressure, instability, or expense risk, you must immediately ground them in a concrete mechanism from the provided evidence. Otherwise that is a failed answer.",
            "If `normalized_evidence.claim_gates.allow_divisional_mentions` is false, do not mention D9, Navamsa, or divisional support at all.",
            "If `normalized_evidence.claim_gates.allow_abstract_risk_labels` is false, do not use abstract risk language at all. Stay with concrete mechanism only.",
            "Do not use dramatic or salesy phrases like 'highly active', 'potentially productive', 'massive emphasis', 'feast-or-famine', 'big breakthrough', or similar language unless the evidence is unusually explicit and you immediately prove it.",
            "Do not add extra future windows, sub-periods, or trigger dates beyond the asked range unless those windows are explicitly present in the provided evidence. If the user asked about coming months, stay with the coming months unless the backend evidence specifically highlights a narrower later window.",
            "For finance answers, keep the structure tight: direct trend -> main mechanism -> main caution -> practical use. Do not widen into investment sectors, windfalls, or broad market-style language unless the user asked for that.",
            "For trait/nature/characteristics answers, treat the question as a stable personality reading unless the user explicitly asks about the current period. Start from core temperament, emotional style, expression, and pressure response. Do not let current dasha dominate unless the user asks how the current period is affecting behavior.",
            "For behavior questions, do not assume behavior is flat across all life areas. If the question points toward work, home, spouse, children, speech, or pressure, use the corresponding area-behavior axis. If the question is broad, use core temperament first and then mention at least two area-specific behavior patterns that are strongly supported.",
            "For behavior and personality answers, use rashi as style/flavor and nakshatra as subtler motive/texture whenever those are available in the provided evidence.",
            "If the user asks something like 'Define me as a person', do not give a life summary. Give a personality architecture from the chart: who they are at core, how they process emotion, how they speak/express, how they handle pressure, then at least two area-specific behavior patterns, then one strength and one caution.",
            "For relationship-person questions, do not use the native's ascendant, Moon, or personality axes as the asked person's direct personality anchor. Start from the target house, its lord, occupants, and the corresponding D9 confirmation.",
            "If the question is about wife, husband, spouse, child, sibling, parent, uncle, or another relative, your answer fails if you describe that person using the native's Lagna/Moon as if it belongs to them.",
            "For event-prediction answers, do not jump to 'yes' just because career, marriage, money, or movement houses are active. Activation can mean pressure, desire, preparation, negotiation, or restructuring; it does not automatically mean the event will happen.",
            "For event-prediction answers, separate these clearly: what supports the event, what obstructs it, and what remains uncertain. If the evidence is mixed, say it is mixed. Do not force a positive verdict.",
            "If the chart shows movement more clearly than completion, say that. If it shows pressure more clearly than result, say that. If it shows possibility but not certainty, say that.",
            "- `topic_signals`: this is the first topic-specific Parashari summary. Prefer it over inventing your own broad category summary from scratch.",
            "- `activation_mechanisms`: if you say a house is activated, justify it from these links. If the links are weak or absent, do not overclaim.",
            "Do not give vague lines like 'communication is generally supported' unless you immediately explain why in chart terms.",
            "Name 2 or 3 concrete astrological reasons from the provided evidence, not a long list of raw data.",
            "Avoid dramatic filler language like 'massive emphasis', 'high stakes', 'disciplined architect', 'catalyst', or similar polished phrases unless the evidence is unusually explicit. Prefer plain, mechanism-first wording.",
            "If the user asks 'how exactly' or challenges an earlier claim, answer that challenge directly from the activation mechanisms. If the earlier claim is not strongly supported, say that clearly and correct course.",
            "If exact transit placement is not needed, do not mention it. If you do mention it, it must match the provided transit row exactly.",
            "For month or multi-week questions, do not describe the whole period from the Sun or Moon transit on one anchor date. Use MD/AD/PD + ranked active areas first, then stable slow-planet transits only as secondary filters.",
            "If Sun is clearly contacting an active period lord or moving through one of the dominant activated houses, you may mention it as the month's visible tone-setter. But make that a secondary tone layer, not the primary mechanism of the month.",
            "For each major month theme you mention, tie it to an explicit mechanism from `normalized_evidence.window_area_mechanisms`, active dasha houses, or activation links. Do not rely only on polished summary prose.",
            "For general month questions, do not force a career or finance story unless the ranked active areas and mechanisms clearly make those the top themes.",
            "Do not speak like a report generator. Speak like an astrologer who is being concise but specific.",
        ]
    )


def _planet_row(planet_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(planet_data, dict):
        return {}
    return {
        "sign": planet_data.get("sign_name") or SIGN_NAMES[int(planet_data.get("sign", 0) or 0) % 12],
        "house": planet_data.get("house"),
        "degree": round(float(planet_data.get("degree", 0) or 0), 2),
        "retrograde": bool(planet_data.get("retrograde")),
        "nakshatra": planet_data.get("nakshatra"),
    }


def _build_instant_context(
    birth_data: Dict[str, Any],
    question: str,
    intent: Optional[Dict[str, Any]],
    history: List[Dict[str, Any]],
    answer_mode_override: Optional[str] = None,
    target_subject_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    birth_obj = SimpleNamespace(**birth_data)
    chart_calc = ChartCalculator({})
    chart_data = chart_calc.calculate_chart(birth_obj)

    ascendant_longitude = float(chart_data.get("ascendant", 0) or 0)
    ascendant_sign_index = int(ascendant_longitude / 30) % 12
    ascendant_sign_name = SIGN_NAMES[ascendant_sign_index]
    house_lordships = _get_house_lordships(ascendant_sign_index)

    category = str((intent or {}).get("category") or "general").lower()
    focus = CATEGORY_FOCUS.get(category, CATEGORY_FOCUS["general"])
    focus_planets = set(focus["planets"]) | {"Moon"}

    query_context = (intent or {}).get("query_context") if isinstance((intent or {}).get("query_context"), dict) else None
    extracted_context = (intent or {}).get("extracted_context") if isinstance((intent or {}).get("extracted_context"), dict) else {}
    now_local = resolve_query_now(query_context)
    period_window = _resolve_period_window(intent, now_local)
    time_relation = _period_time_relation(period_window, now_local)
    dasha_anchor = _period_anchor_datetime(period_window, now_local)
    dasha_calc = DashaCalculator()
    current_dashas = dasha_calc.calculate_current_dashas(birth_data, dasha_anchor)
    specific_date = str(extracted_context.get("specific_date") or (intent or {}).get("dasha_as_of") or "").strip()
    transit_anchor = dasha_anchor
    if specific_date and str((period_window or {}).get("kind") or "") == "day":
        try:
            transit_anchor = datetime.strptime(specific_date, "%Y-%m-%d").replace(
                hour=now_local.hour,
                minute=now_local.minute,
            )
        except ValueError:
            transit_anchor = dasha_anchor
    transit_calc = RealTransitCalculator()
    asc_nakshatra = transit_calc.get_nakshatra_from_longitude(ascendant_longitude)

    transit_rows: Dict[str, Dict[str, Any]] = {}
    for planet in sorted(focus_planets | {"Saturn", "Jupiter", "Rahu", "Ketu"}):
        longitude = transit_calc.get_planet_position(transit_anchor, planet)
        if longitude is None:
            continue
        sign_index = int(longitude / 30) % 12
        transit_rows[planet] = {
            "sign": SIGN_NAMES[sign_index],
            "house_from_lagna": transit_calc.calculate_house_from_longitude(longitude, ascendant_longitude),
            "retrograde": bool(transit_calc.is_planet_retrograde(transit_anchor, planet)),
            "nakshatra": transit_calc.get_nakshatra_from_longitude(longitude),
        }

    key_planets = {
        planet: _planet_row(chart_data.get("planets", {}).get(planet, {}))
        for planet in PLANET_SEQUENCE
        if chart_data.get("planets", {}).get(planet)
    }
    birth_summary = {
        "name": birth_data.get("name"),
        "date": birth_data.get("date"),
        "time": birth_data.get("time"),
        "place": birth_data.get("place"),
        "ascendant": {
            "sign": ascendant_sign_name,
            "degree": round(ascendant_longitude % 30, 2),
            "nakshatra": asc_nakshatra,
        },
        "moon": {
            **_planet_row(chart_data.get("planets", {}).get("Moon", {})),
            "nakshatra": chart_data.get("planets", {}).get("Moon", {}).get("nakshatra"),
        },
    }
    natal_snapshot = {
        "house_lordships": house_lordships,
        "key_planets": key_planets,
    }

    def _compact_dasha(level: str) -> Dict[str, Any]:
        row = current_dashas.get(level, {}) if isinstance(current_dashas, dict) else {}
        lord = row.get("planet")
        natal = chart_data.get("planets", {}).get(lord or "", {})
        return {
            "planet": lord,
            "started": row.get("start_date"),
            "ends": row.get("end_date"),
            "natal_house": natal.get("house"),
            "natal_sign": natal.get("sign_name"),
            "lordships": house_lordships.get(lord or "", []),
        }

    current_q_norm = _normalize_question_text(question)
    recent_history = []
    for item in (history or [])[-2:]:
        if not isinstance(item, dict):
            continue
        q = _truncate(str(item.get("question") or ""), 180)
        a = _truncate(str(item.get("response") or ""), 260)
        if _normalize_question_text(q) == current_q_norm:
            continue
        if q or a:
            recent_history.append({"question": q, "answer": a})

    complexity_hint = {
        "mode": str((intent or {}).get("mode") or "birth"),
        "needs_transits": bool((intent or {}).get("needs_transits")),
        "has_multiple_parts": "?" in question and question.count("?") > 1,
        "question_length": len(question or ""),
    }

    answer_mode = str(answer_mode_override or "").strip() or _infer_answer_mode(question, intent, history)
    target_subject = target_subject_override if isinstance(target_subject_override, dict) else None
    try:
        instant_parashari = _compact_parashari_evidence(
            birth_data=birth_data,
            question=question,
            intent=intent,
            period_window=period_window,
        )
    except Exception as exc:
        logger.warning("instant parashari evidence build failed: %s", exc)
        instant_parashari = {
            "source": "fallback",
            "category": category,
            "focus_houses": focus["houses"],
            "topic_key": PARASHARI_TOPIC_MAP.get(category),
            "active_dashas": {},
            "active_dashas_formatted": {},
            "house_activation": {},
            "transit_pressure": {},
            "divisional_support": {},
            "topic_signals": {},
            "top_supports": [],
            "top_risks": [],
            "topic_band": "mixed",
            "dominant_houses": [],
            "activation_mechanisms": [],
            "answer_mode": answer_mode,
        }
    else:
        instant_parashari["answer_mode"] = answer_mode
    instant_parashari["period_window"] = period_window
    instant_parashari["time_relation"] = time_relation

    current_dashas_context = instant_parashari.get("active_dashas_formatted") or {}
    current_transits_context = _format_transit_context(transit_rows)
    target_chart_context = _build_target_chart_context(
        birth_summary,
        natal_snapshot,
        current_transits_context,
        target_subject,
    )
    target_birth_summary = _target_context_as_birth_summary(target_chart_context)
    normalized_evidence = _normalize_instant_evidence(
        answer_mode=instant_parashari.get("answer_mode") or "topic_reading",
        category=category,
        instant_parashari=instant_parashari,
        current_transits_formatted=current_transits_context,
        current_dashas_context=current_dashas_context,
        birth_summary=birth_summary,
        natal_snapshot=natal_snapshot,
        relationship_target=target_subject,
        target_chart_context=target_chart_context,
    )

    is_general_month_window = (
        str((intent or {}).get("mode") or "").upper() == "PREDICT_PERIOD_OUTLOOK"
        and str(category or "").lower() in {"general", "timing"}
        and str((period_window or {}).get("kind") or "") == "window"
    )
    prompt_transits_context = dict(current_transits_context)
    prompt_current_transits = {
        "as_of_local": transit_anchor.strftime("%Y-%m-%d %H:%M"),
        "planets": dict(transit_rows),
    }
    prompt_instant_parashari = dict(instant_parashari)
    prompt_normalized_evidence = dict(normalized_evidence)
    claim_gates = (normalized_evidence.get("claim_gates") or {}) if isinstance(normalized_evidence.get("claim_gates"), dict) else {}
    if answer_mode == "trait_nature":
        prompt_current_transits = {}
        prompt_transits_context = {}
        prompt_instant_parashari = {
            k: v
            for k, v in prompt_instant_parashari.items()
            if k in {
                "source",
                "category",
                "focus_houses",
                "topic_key",
                "divisional_support",
                "activation_mechanisms",
                "navamsa_root_fruit",
                "answer_mode",
                "period_window",
                "time_relation",
            }
        }
        prompt_normalized_evidence = {
            k: v
            for k, v in prompt_normalized_evidence.items()
            if k in {
                "answer_mode_contract",
                "primary_drivers",
                "personality_axes",
                "area_behavior_axes",
                "mechanism_links",
                "divisional_specifics",
                "claim_gates",
                "avoid_drift",
            }
        }
        recent_history = recent_history[-1:]
    if answer_mode == "relationship_person":
        prompt_current_transits = {}
        prompt_transits_context = {}
        prompt_instant_parashari = {
            k: v
            for k, v in prompt_instant_parashari.items()
            if k in {
                "source",
                "category",
                "focus_houses",
                "topic_key",
                "divisional_support",
                "activation_mechanisms",
                "answer_mode",
                "period_window",
                "time_relation",
            }
        }
        prompt_normalized_evidence = {
            k: v
            for k, v in prompt_normalized_evidence.items()
            if k in {
                "answer_mode_contract",
                "person_profile_axes",
                "target_subject",
                "target_chart_context",
                "mechanism_links",
                "divisional_specifics",
                "claim_gates",
                "avoid_drift",
            }
        }
        natal_snapshot = {}
        current_dashas_context = {}
        birth_summary = {
            **target_birth_summary,
            "name": str((target_subject or {}).get("label") or "target person"),
            "source": "rotated_target_context",
        }
        recent_history = recent_history[-1:]
    if not claim_gates.get("allow_divisional_mentions"):
        prompt_instant_parashari.pop("divisional_support", None)
        prompt_instant_parashari.pop("navamsa_root_fruit", None)
        prompt_normalized_evidence.pop("divisional_specifics", None)
        if isinstance(prompt_normalized_evidence.get("topic_confirmation"), dict):
            prompt_normalized_evidence["topic_confirmation"] = {
                k: v
                for k, v in prompt_normalized_evidence["topic_confirmation"].items()
                if k not in {"topic_support", "current_topic_support"}
            }
    if not claim_gates.get("allow_abstract_risk_labels"):
        prompt_instant_parashari.pop("top_risks", None)
        prompt_normalized_evidence["secondary_modifiers"] = []
        prompt_normalized_evidence.pop("risk_specifics", None)
    if is_general_month_window:
        month_tone = (normalized_evidence.get("month_tone") or {}) if isinstance(normalized_evidence.get("month_tone"), dict) else {}
        if not month_tone.get("enabled"):
            prompt_transits_context.pop("Sun", None)
            prompt_current_transits["planets"].pop("Sun", None)
            if isinstance(prompt_normalized_evidence.get("transit_anchor_rows"), dict):
                prompt_normalized_evidence["transit_anchor_rows"] = dict(prompt_normalized_evidence["transit_anchor_rows"])
                prompt_normalized_evidence["transit_anchor_rows"].pop("Sun", None)
        prompt_normalized_evidence.pop("dominant_house_signals", None)
        prompt_instant_parashari.pop("dominant_houses", None)
        prompt_instant_parashari.pop("top_supports", None)

    return {
        "birth_summary": birth_summary,
        "intent_summary": {
            "category": category,
            "mode": (intent or {}).get("mode") or "birth",
            "answer_mode": instant_parashari.get("answer_mode") or "topic_reading",
            "period_window": period_window,
            "time_relation": time_relation,
            "focus_houses": focus["houses"],
            "focus_planets": sorted(focus_planets),
            "extracted_context": (intent or {}).get("extracted_context") or {},
            "target_subject": target_subject or {"key": "self", "label": "self", "base_house": 1},
        },
        "natal_snapshot": natal_snapshot,
        "target_chart_context": target_chart_context,
        "current_dashas": {
            "as_of": dasha_anchor.strftime("%Y-%m-%d"),
            "levels": current_dashas_context,
        },
        "current_transits": prompt_current_transits,
        "current_transits_formatted": prompt_transits_context,
        "instant_parashari": prompt_instant_parashari,
        "normalized_evidence": prompt_normalized_evidence,
        "recent_history": recent_history,
        "complexity_hint": complexity_hint,
    }


def _build_instant_prompt(
    question: str,
    instant_context: Dict[str, Any],
    language: str,
) -> str:
    language_label = (language or "english").strip().lower()
    context_json = json.dumps(instant_context, ensure_ascii=False, separators=(",", ":"))
    intent_summary = instant_context.get("intent_summary") or {}
    category = str(intent_summary.get("category") or "general")
    mode = str(intent_summary.get("mode") or "birth")
    answer_mode = str(intent_summary.get("answer_mode") or "topic_reading")
    period_window = intent_summary.get("period_window") if isinstance(intent_summary.get("period_window"), dict) else {}
    time_relation = str(intent_summary.get("time_relation") or "current")
    normalized_evidence = instant_context.get("normalized_evidence") if isinstance(instant_context.get("normalized_evidence"), dict) else {}
    analysis_block = _instant_parashari_instruction_block(
        category,
        mode,
        answer_mode,
        period_window,
        time_relation,
        normalized_evidence,
    )
    return f"""
You are AstroRoshni Instant Chat, the fast conversational astrology lane.

Your job:
- Answer quickly and clearly from the provided chart evidence.
- Use `instant_parashari` as the primary reasoning spine. That section already compresses the strongest current dasha, house activation, transit pressure, divisional support, and topic-specific Parashari signals.
- Use the raw natal/dasha/transit fields only to support or clarify the Parashari reading, not to replace it.
- Be conversational and natural, not report-like.
- Do not output HTML, JSON, markdown tables, glossary blocks, follow-up widgets, FAQ_META, or internal tags.
- Do not mention hidden reasoning, token limits, or model limitations.
- Use plain astrological language that normal users can understand.
- If the question is too complex for a fast answer, still answer helpfully but say one short line that a deeper reading would be better for exact timing or full synthesis.
- Never invent missing chart data.

Astrological method:
{analysis_block}

Style rules:
- Language: {language_label}
- Keep it concise but useful: usually 2 to 5 short paragraphs.
- Lead with the direct answer in the first 1 to 2 sentences.
- Mention the strongest current dasha or transit factor only when it genuinely helps clarity for this answer mode.
- Start from `normalized_evidence.primary_drivers` and only then bring in `secondary_modifiers`.
- Use `normalized_evidence.answer_mode_contract.answer_skeleton` as the structural backbone of the response.
- If the question is about career, relationship, wealth, or health, use the corresponding `instant_parashari.topic_signals` and `divisional_support` to keep the answer precise.
- If the question is about a specific facet inside a broader area, answer that facet directly from the house activation and dasha logic instead of widening the answer into a whole life summary.
- If `intent_summary.target_subject.key` is not `self`, treat `target_chart_context` as the primary chart frame for that person instead of reading only from the native's direct Lagna context.
- No decorative headers unless absolutely needed.

USER QUESTION:
{question}

ASTROLOGY CONTEXT:
{context_json}
""".strip()


async def generate_instant_chat_response(
    analyzer,
    *,
    question: str,
    birth_data: Dict[str, Any],
    intent: Optional[Dict[str, Any]],
    history: List[Dict[str, Any]],
    language: str = "english",
) -> Dict[str, Any]:
    mode_selection = await _infer_answer_mode_with_llm(
        analyzer,
        question=question,
        intent=intent,
        history=history,
    )
    answer_mode = str((mode_selection or {}).get("answer_mode") or "topic_reading")
    target_subject = (mode_selection or {}).get("target_subject") if isinstance(mode_selection, dict) else None
    instant_context = _build_instant_context(
        birth_data=birth_data,
        question=question,
        intent=intent,
        history=history,
        answer_mode_override=answer_mode,
        target_subject_override=target_subject,
    )
    prompt = _build_instant_prompt(question, instant_context, language)
    model_name = get_gemini_instant_model()
    selected_model = analyzer.get_named_gemini_model(model_name, premium_analysis=False)

    started_at = datetime.utcnow()
    llm_result = await analyzer.generate_text_from_prompt(
        prompt,
        premium_analysis=False,
        model_override=selected_model,
        model_name_override=model_name,
        llm_log_tag="instant_chat",
        request_timeout_s=90.0,
        force_gemini=True,
    )
    elapsed_s = max(0.0, (datetime.utcnow() - started_at).total_seconds())

    if not llm_result.get("success"):
        error_text = llm_result.get("error") or "Instant chat failed"
        return {
            "success": False,
            "response": "I’m having trouble giving the instant reading right now. Please try again in a moment.",
            "error": error_text,
            "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
            "timing": {
                "chat_llm_provider": "gemini",
                "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
                "instant_chat": True,
                "total_request_time": elapsed_s,
            },
            "token_usage": llm_result.get("token_usage") or {},
            "llm_prompt_chars": len(prompt),
            "llm_response_chars": 0,
            "instant_llm_usage_stage": _build_instant_usage_stage(
                "instant_answer",
                llm_result.get("chat_llm_model") or model_name,
                len(prompt),
                0,
                llm_result.get("token_usage") or {},
                False,
                elapsed_s,
            ),
            "terms": [],
            "glossary": {},
            "follow_up_questions": [],
        }

    response_text = (llm_result.get("response") or "").strip()
    return {
        "success": True,
        "response": response_text,
        "error": None,
        "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
        "timing": {
            "chat_llm_provider": "gemini",
            "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
            "instant_chat": True,
            "total_request_time": elapsed_s,
        },
        "token_usage": llm_result.get("token_usage") or {},
        "llm_prompt_chars": len(prompt),
        "llm_response_chars": len(response_text),
        "instant_llm_usage_stage": _build_instant_usage_stage(
            "instant_answer",
            llm_result.get("chat_llm_model") or model_name,
            len(prompt),
            len(response_text),
            llm_result.get("token_usage") or {},
            True,
            elapsed_s,
        ),
        "terms": [],
        "glossary": {},
        "follow_up_questions": [],
        "summary_image": None,
        "analysis_steps": [],
        "faq_metadata": None,
        "raw_response": response_text,
        "instant_context_summary": instant_context.get("intent_summary") or {},
    }
