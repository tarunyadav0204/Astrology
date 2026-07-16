from __future__ import annotations

import json
import logging
import os
import re
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
import asyncio

from ai.parallel_chat.parallel_agent_payloads import build_parashari_agent_payload
from ai.response_parser import ResponseParser
from calculators import RemedyEngine
from calculators.chart_calculator import ChartCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext
from shared.dasha_calculator import DashaCalculator
from utils.admin_settings import get_gemini_instant_model


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


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

_SIGN_NAME_TO_INDEX = {name: idx for idx, name in enumerate(SIGN_NAMES)}

PLANET_SEQUENCE = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

CATEGORY_FOCUS = {
    "career": {"houses": [2, 6, 10, 11], "planets": ["Sun", "Mercury", "Saturn", "Jupiter"]},
    "job": {"houses": [2, 6, 10, 11], "planets": ["Sun", "Mercury", "Saturn", "Jupiter"]},
    "promotion": {"houses": [2, 6, 10, 11], "planets": ["Sun", "Mercury", "Saturn", "Jupiter"]},
    "business": {"houses": [2, 6, 10, 11], "planets": ["Sun", "Mercury", "Saturn", "Jupiter", "Mars"]},
    "wealth": {"houses": [2, 5, 9, 11], "planets": ["Jupiter", "Venus", "Mercury"]},
    "health": {"houses": [1, 6, 8, 12], "planets": ["Sun", "Moon", "Mars", "Saturn"]},
    "marriage": {"houses": [2, 5, 7, 11], "planets": ["Venus", "Moon", "Jupiter", "Mars"]},
    "progeny": {"houses": [2, 5, 9, 11], "planets": ["Jupiter", "Moon", "Venus"]},
    "education": {"houses": [2, 4, 5, 9], "planets": ["Mercury", "Jupiter", "Moon"]},
    "trading": {"houses": [2, 5, 8, 11], "planets": ["Mercury", "Jupiter", "Rahu"]},
    "property": {"houses": [4, 8, 11, 12], "planets": ["Mars", "Venus", "Moon", "Saturn"]},
    "relocation": {"houses": [3, 4, 9, 12], "planets": ["Moon", "Rahu", "Saturn", "Jupiter"]},
    "visa": {"houses": [3, 9, 12], "planets": ["Rahu", "Jupiter", "Saturn", "Mercury"]},
    "travel": {"houses": [3, 9, 12], "planets": ["Rahu", "Jupiter", "Moon", "Mercury"]},
    "litigation": {"houses": [6, 7, 8, 12], "planets": ["Mars", "Saturn", "Rahu", "Mercury"]},
    "surgery": {"houses": [1, 6, 8, 12], "planets": ["Mars", "Saturn", "Sun", "Ketu"]},
    "higher_studies": {"houses": [4, 5, 9, 12], "planets": ["Jupiter", "Mercury", "Moon", "Rahu"]},
    "general": {"houses": [1, 4, 7, 10], "planets": ["Moon", "Sun", "Jupiter"]},
}

EVENT_CATEGORY_PRIORITIES = {
    "career": {"house_weights": {10: 3.0, 6: 2.5, 11: 2.0, 2: 1.5}, "planet_weights": {"Saturn": 2.0, "Sun": 1.8, "Mercury": 1.8, "Jupiter": 1.4}},
    "job": {"house_weights": {10: 3.0, 6: 2.5, 11: 2.0, 2: 1.5}, "planet_weights": {"Saturn": 2.0, "Sun": 1.8, "Mercury": 1.8, "Jupiter": 1.4}},
    "promotion": {"house_weights": {10: 3.0, 6: 2.5, 11: 2.4, 2: 1.5}, "planet_weights": {"Sun": 2.0, "Saturn": 1.8, "Mercury": 1.6, "Jupiter": 1.5}},
    "business": {"house_weights": {10: 3.0, 7: 2.5, 11: 2.0, 2: 1.5}, "planet_weights": {"Mercury": 2.0, "Sun": 1.8, "Saturn": 1.7, "Jupiter": 1.4, "Mars": 1.3}},
    "wealth": {"house_weights": {2: 3.0, 11: 2.5, 5: 2.0, 9: 1.8}, "planet_weights": {"Jupiter": 2.0, "Venus": 1.8, "Mercury": 1.6, "Moon": 1.2}},
    "health": {"house_weights": {1: 3.0, 6: 2.5, 8: 2.0, 12: 1.8}, "planet_weights": {"Saturn": 1.8, "Mars": 1.8, "Sun": 1.6, "Moon": 1.4}},
    "marriage": {"house_weights": {7: 3.0, 11: 2.2, 2: 1.8, 5: 1.6}, "planet_weights": {"Venus": 2.0, "Jupiter": 1.8, "Moon": 1.5, "Mars": 1.2}},
    "progeny": {"house_weights": {5: 3.0, 9: 2.2, 11: 1.8, 2: 1.5}, "planet_weights": {"Jupiter": 2.0, "Moon": 1.7, "Venus": 1.5}},
    "education": {"house_weights": {4: 3.0, 5: 2.4, 9: 2.0, 2: 1.6}, "planet_weights": {"Mercury": 2.0, "Jupiter": 1.8, "Moon": 1.4}},
    "trading": {"house_weights": {5: 3.0, 11: 2.4, 2: 2.0, 8: 1.5}, "planet_weights": {"Mercury": 2.0, "Jupiter": 1.7, "Rahu": 1.5}},
    "property": {"house_weights": {4: 3.5, 11: 2.2, 2: 1.8, 8: 1.2, 12: 1.0}, "planet_weights": {"Venus": 2.4, "Moon": 1.8, "Saturn": 1.6, "Mars": 1.3}},
    "relocation": {"house_weights": {4: 3.0, 12: 2.5, 9: 2.0, 3: 1.8}, "planet_weights": {"Moon": 2.0, "Rahu": 1.8, "Saturn": 1.5, "Jupiter": 1.3}},
    "visa": {"house_weights": {12: 3.0, 9: 2.4, 3: 1.8}, "planet_weights": {"Rahu": 2.0, "Saturn": 1.6, "Jupiter": 1.5, "Mercury": 1.4}},
    "travel": {"house_weights": {9: 3.0, 12: 2.4, 3: 1.8}, "planet_weights": {"Rahu": 1.8, "Jupiter": 1.7, "Moon": 1.5, "Mercury": 1.2}},
    "litigation": {"house_weights": {6: 3.0, 7: 2.2, 8: 1.8, 12: 1.4}, "planet_weights": {"Saturn": 1.8, "Mars": 1.8, "Rahu": 1.5, "Mercury": 1.3}},
    "surgery": {"house_weights": {8: 3.0, 6: 2.4, 12: 2.0, 1: 1.6}, "planet_weights": {"Mars": 2.0, "Saturn": 1.8, "Ketu": 1.6, "Sun": 1.3}},
    "higher_studies": {"house_weights": {9: 3.0, 5: 2.3, 4: 2.0, 12: 1.6}, "planet_weights": {"Jupiter": 2.0, "Mercury": 1.8, "Rahu": 1.4, "Moon": 1.3}},
    "general": {"house_weights": {1: 2.0, 4: 2.0, 7: 2.0, 10: 2.0}, "planet_weights": {"Moon": 1.4, "Sun": 1.4, "Jupiter": 1.4}},
}

EVENT_ANSWER_LABELS = {
    "career": "career growth",
    "job": "job matters",
    "promotion": "promotion",
    "business": "business growth",
    "wealth": "wealth growth",
    "health": "health recovery",
    "marriage": "marriage",
    "progeny": "having a child",
    "education": "education",
    "trading": "trading or speculation",
    "property": "property matters",
    "relocation": "relocation",
    "visa": "visa or foreign travel",
    "travel": "travel",
    "litigation": "legal matters",
    "surgery": "surgery or medical procedures",
    "higher_studies": "higher studies",
    "general": "this event",
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

SPEECH_HOUSE_THEME_LABELS = {
    1: "personal direction and vitality",
    2: "family resources and financial stability",
    3: "effort and communication",
    4: "home and emotional stability",
    5: "children, creativity, and romance",
    6: "work routines and responsibilities",
    7: "partnerships and commitments",
    8: "pressure, change, and hidden factors",
    9: "long-range support and guidance",
    10: "career role and public progress",
    11: "gains, networks, and fulfillment",
    12: "expenses, retreat, and foreign links",
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
    "property": "wealth",
    "relocation": "career",
    "visa": "career",
    "travel": "career",
    "litigation": "health",
    "surgery": "health",
    "higher_studies": "career",
}

EVENT_CATEGORY_ALIASES = {
    "child": "progeny",
    "children": "progeny",
    "pregnancy": "progeny",
    "pregnant": "progeny",
    "baby": "progeny",
    "childbirth": "progeny",
    "conception": "progeny",
    "property_sale": "property",
    "real_estate": "property",
    "home": "property",
    "house": "property",
    "shift": "relocation",
    "move": "relocation",
    "moving": "relocation",
    "abroad": "travel",
    "travel_abroad": "travel",
    "foreign_travel": "travel",
    "court_case": "litigation",
    "legal_case": "litigation",
    "operation": "surgery",
    "procedure": "surgery",
    "higher_education": "higher_studies",
    "masters": "higher_studies",
    "phd": "higher_studies",
}

# Natural significators for instant event-horizon scan (MD/AD relevance), beyond house lordships.
EVENT_CATEGORY_KARAKAS: Dict[str, frozenset] = {
    "marriage": frozenset({"Venus", "Jupiter", "Moon", "Mars"}),
    "love": frozenset({"Venus", "Jupiter", "Moon", "Mars"}),
    "relationship": frozenset({"Venus", "Jupiter", "Moon", "Mars"}),
    "partner": frozenset({"Venus", "Jupiter", "Moon", "Mars"}),
    "spouse": frozenset({"Venus", "Jupiter", "Moon", "Mars"}),
    "career": frozenset({"Sun", "Mercury", "Saturn", "Jupiter", "Mars"}),
    "job": frozenset({"Sun", "Mercury", "Saturn", "Jupiter", "Mars"}),
    "promotion": frozenset({"Sun", "Mercury", "Saturn", "Jupiter"}),
    "business": frozenset({"Sun", "Mercury", "Saturn", "Jupiter", "Mars"}),
    "wealth": frozenset({"Jupiter", "Venus", "Mercury", "Moon"}),
    "money": frozenset({"Jupiter", "Venus", "Mercury", "Moon"}),
    "finance": frozenset({"Jupiter", "Venus", "Mercury", "Moon"}),
    "progeny": frozenset({"Jupiter", "Moon", "Venus"}),
    "education": frozenset({"Mercury", "Jupiter", "Moon"}),
    "health": frozenset({"Sun", "Moon", "Mars", "Saturn"}),
    "disease": frozenset({"Sun", "Moon", "Mars", "Saturn"}),
    "property": frozenset({"Mars", "Venus", "Moon", "Saturn"}),
    "relocation": frozenset({"Moon", "Rahu", "Saturn", "Jupiter"}),
    "visa": frozenset({"Rahu", "Jupiter", "Saturn", "Mercury"}),
    "travel": frozenset({"Rahu", "Jupiter", "Moon", "Mercury"}),
    "litigation": frozenset({"Mars", "Saturn", "Rahu", "Mercury"}),
    "surgery": frozenset({"Mars", "Saturn", "Sun", "Ketu"}),
    "higher_studies": frozenset({"Jupiter", "Mercury", "Moon", "Rahu"}),
    "general": frozenset({"Moon", "Sun", "Jupiter"}),
}

_INSTANT_EVENT_HORIZON_DAYS = int(365 * 3)

_PLANET_ASPECT_OFFSETS = {
    "Sun": [7],
    "Moon": [7],
    "Mercury": [7],
    "Venus": [7],
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9],
    "Ketu": [5, 7, 9],
}

_NATURAL_NATURE = {
    "Sun": "malefic",
    "Moon": "benefic",
    "Mars": "malefic",
    "Mercury": "benefic",
    "Jupiter": "benefic",
    "Venus": "benefic",
    "Saturn": "malefic",
    "Rahu": "malefic",
    "Ketu": "malefic",
}

_EXALTATION_SIGNS = {
    "Sun": 0,
    "Moon": 1,
    "Mars": 9,
    "Mercury": 5,
    "Jupiter": 3,
    "Venus": 11,
    "Saturn": 6,
}

_DEBILITATION_SIGNS = {
    "Sun": 6,
    "Moon": 7,
    "Mars": 3,
    "Mercury": 11,
    "Jupiter": 9,
    "Venus": 5,
    "Saturn": 0,
}

_OWN_SIGNS = {
    "Sun": {4},
    "Moon": {3},
    "Mars": {0, 7},
    "Mercury": {2, 5},
    "Jupiter": {8, 11},
    "Venus": {1, 6},
    "Saturn": {9, 10},
}

_MOOLTRIKONA_SIGNS = {
    "Sun": 4,
    "Moon": 1,
    "Mars": 0,
    "Mercury": 5,
    "Jupiter": 8,
    "Venus": 6,
    "Saturn": 10,
}

_PLANET_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}

_PLANET_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

_SIGN_LORDS = {
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


def _normalize_event_category(category: str) -> str:
    c = str(category or "").strip().lower()
    if not c:
        return "general"
    c = EVENT_CATEGORY_ALIASES.get(c, c)
    return c if c in CATEGORY_FOCUS else "general"


def _norm_house(h: Any) -> Optional[int]:
    hh = _safe_int(h)
    if hh is None:
        return None
    return ((hh - 1) % 12) + 1


def _planet_aspects_house_from(transit_house: int, target_house: int, planet: str) -> bool:
    th = _norm_house(transit_house)
    tgt = _norm_house(target_house)
    if th is None or tgt is None:
        return False
    for off in _PLANET_ASPECT_OFFSETS.get(str(planet or ""), [7]):
        if _norm_house(th + off) == tgt:
            return True
    return False


def _sign_index_from_row(row: Dict[str, Any]) -> Optional[int]:
    if not isinstance(row, dict):
        return None
    raw = row.get("sign")
    if raw is not None:
        try:
            return int(raw) % 12
        except (TypeError, ValueError):
            pass
    sign_name = str(row.get("sign_name") or row.get("sign") or "").strip()
    if sign_name in _SIGN_NAME_TO_INDEX:
        return _SIGN_NAME_TO_INDEX[sign_name]
    return None


def _natural_nature(planet: str) -> str:
    return _NATURAL_NATURE.get(str(planet or "").strip(), "neutral")


def _functional_nature(lordships: List[int]) -> str:
    good = {1, 5, 9}
    bad = {3, 6, 8, 11, 12}
    neutral = {2, 4, 7, 10}
    hs = {int(h) for h in (lordships or []) if _safe_int(h) is not None}
    good_hits = len(hs & good)
    bad_hits = len(hs & bad)
    neutral_hits = len(hs & neutral)
    if good_hits > bad_hits:
        return "functional_benefic"
    if bad_hits > good_hits:
        return "functional_malefic"
    if neutral_hits and not good_hits and not bad_hits:
        return "functional_neutral"
    return "mixed_functional"


def _planet_dignity_status(planet: str, sign_index: Optional[int]) -> Dict[str, Any]:
    planet = str(planet or "").strip()
    if sign_index is None:
        return {
            "dignity": "unknown",
            "in_own_sign": False,
            "in_mooltrikona": False,
            "sign_relation": "unknown",
        }
    if _EXALTATION_SIGNS.get(planet) == sign_index:
        dignity = "exalted"
    elif _DEBILITATION_SIGNS.get(planet) == sign_index:
        dignity = "debilitated"
    elif sign_index in _OWN_SIGNS.get(planet, set()):
        dignity = "own_sign"
    elif _MOOLTRIKONA_SIGNS.get(planet) == sign_index:
        dignity = "mooltrikona"
    else:
        sign_lord = _SIGN_LORDS.get(sign_index)
        if sign_lord in _PLANET_FRIENDS.get(planet, set()):
            dignity = "friend_sign"
        elif sign_lord in _PLANET_ENEMIES.get(planet, set()):
            dignity = "enemy_sign"
        else:
            dignity = "neutral_sign"
    sign_lord = _SIGN_LORDS.get(sign_index)
    sign_relation = "neutral"
    if sign_lord in _PLANET_FRIENDS.get(planet, set()):
        sign_relation = "friend_rashi"
    elif sign_lord in _PLANET_ENEMIES.get(planet, set()):
        sign_relation = "enemy_rashi"
    elif sign_lord == planet:
        sign_relation = "own_rashi"
    return {
        "dignity": dignity,
        "in_own_sign": dignity == "own_sign",
        "in_mooltrikona": dignity == "mooltrikona",
        "sign_relation": sign_relation,
        "sign_lord": sign_lord,
    }


def _category_priority_profile(category: str) -> Dict[str, Any]:
    return EVENT_CATEGORY_PRIORITIES.get(_normalize_event_category(category), EVENT_CATEGORY_PRIORITIES["general"])


def _house_priority_weight(category: str, house: Optional[int]) -> float:
    hh = _norm_house(house)
    if hh is None:
        return 1.0
    profile = _category_priority_profile(category)
    return float((profile.get("house_weights") or {}).get(hh, 1.0))


def _planet_priority_weight(category: str, planet: str) -> float:
    profile = _category_priority_profile(category)
    return float((profile.get("planet_weights") or {}).get(str(planet or "").strip(), 1.0))


def _natal_aspects_to_planet(target_planet: str, chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    planets = (chart_data or {}).get("planets") or {}
    target_row = planets.get(target_planet) or {}
    target_house = _safe_int(target_row.get("house"))
    if target_house is None:
        return []
    out: List[Dict[str, Any]] = []
    for other, other_row in planets.items():
        if other == target_planet or not isinstance(other_row, dict):
            continue
        other_house = _safe_int(other_row.get("house"))
        if other_house is None:
            continue
        if _planet_aspects_house_from(other_house, target_house, other):
            out.append(
                {
                    "planet": str(other),
                    "from_house": other_house,
                    "nature": _natural_nature(str(other)),
                    "aspect_tone": "benefic" if _natural_nature(str(other)) == "benefic" else "malefic",
                }
            )
    return out[:5]


def _topic_house_rows(
    focus_houses: List[int],
    house_lordships: Dict[str, List[int]],
    chart_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    planets = (chart_data or {}).get("planets") or {}
    out: List[Dict[str, Any]] = []
    for house in focus_houses or []:
        hh = _safe_int(house)
        if hh is None:
            continue
        lord = _lord_of_house(house_lordships, hh)
        occupants = []
        for planet, row in planets.items():
            if _safe_int((row or {}).get("house")) == hh:
                occupants.append(str(planet))
        out.append(
            {
                "house": hh,
                "theme": HOUSE_THEME_LABELS.get(hh, ""),
                "lord": lord,
                "occupants": occupants,
            }
        )
    return out


def _planet_prediction_status(
    planet: str,
    row: Dict[str, Any],
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
) -> Dict[str, Any]:
    lordships = list(row.get("lordships") or [])
    sign_index = _sign_index_from_row(((chart_data or {}).get("planets") or {}).get(planet) or {})
    dignity = _planet_dignity_status(planet, sign_index)
    return {
        "planet": planet,
        "natal_house": row.get("natal_house"),
        "natal_sign": row.get("natal_sign"),
        "lordships": lordships,
        "natural_nature": _natural_nature(planet),
        "functional_nature": _functional_nature(lordships if lordships else list((house_lordships or {}).get(planet) or [])),
        "dignity": dignity.get("dignity"),
        "sign_relation": dignity.get("sign_relation"),
        "in_own_sign": dignity.get("in_own_sign"),
        "in_mooltrikona": dignity.get("in_mooltrikona"),
        "sign_lord": dignity.get("sign_lord"),
        "retrograde": bool((((chart_data or {}).get("planets") or {}).get(planet) or {}).get("retrograde")),
        "conjunctions": list(row.get("conjunctions") or []),
        "natal_aspects_received": _natal_aspects_to_planet(planet, chart_data),
    }


def _current_transit_contacts_for_planet(
    planet: str,
    active_row: Dict[str, Any],
    current_transits_formatted: Dict[str, Any],
) -> Dict[str, Any]:
    transit_row = (current_transits_formatted or {}).get(planet) or {}
    if not isinstance(transit_row, dict):
        return {}
    natal_house = _safe_int(active_row.get("natal_house"))
    transit_house = _safe_int(transit_row.get("house_from_lagna"))
    over_natal = bool(natal_house is not None and transit_house == natal_house)
    aspects_natal = bool(
        natal_house is not None
        and transit_house is not None
        and _planet_aspects_house_from(transit_house, natal_house, planet)
    )
    return {
        "planet": planet,
        "transit_sign": transit_row.get("sign"),
        "transit_house": transit_house,
        "over_natal_house": over_natal,
        "aspects_natal_house": aspects_natal,
        "retrograde": bool(transit_row.get("retrograde")),
    }


def _compact_divisional_topic_payload(divisional_support: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    topic = (divisional_support or {}).get("topic") or {}
    current_topic = (divisional_support or {}).get("current_topic") or {}
    for bucket_name, bucket in (("topic", topic), ("current_topic", current_topic)):
        if not isinstance(bucket, dict):
            continue
        compact_charts: Dict[str, Any] = {}
        for code, chart in ((bucket.get("charts") or {}).items() if isinstance(bucket.get("charts"), dict) else []):
            if not isinstance(chart, dict):
                continue
            compact_charts[code] = {
                "support": chart.get("support"),
                "best": chart.get("best"),
                "hard": chart.get("hard"),
                "rows": list(chart.get("rows") or [])[:6],
            }
        out[bucket_name] = {
            "support": bucket.get("support"),
            "codes": bucket.get("codes"),
            "charts": compact_charts,
        }
    return out


def _event_divisional_category(category: str) -> str:
    cat = _normalize_event_category(category)
    if cat == "progeny":
        return "child"
    return cat


def _divisional_levels_for_payload(current_dashas_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for level in ("md", "ad", "pd"):
        row = (current_dashas_context or {}).get(level) or {}
        if not isinstance(row, dict):
            continue
        planet = str(row.get("planet") or row.get("p") or "").strip()
        if planet:
            out[level] = {"p": planet}
    return out


def _requested_event_divisional_support(
    *,
    birth_data: Dict[str, Any],
    question: str,
    intent: Optional[Dict[str, Any]],
    category: str,
    focus_houses: List[int],
    current_dashas_context: Dict[str, Any],
) -> Dict[str, Any]:
    requested = [
        str(code).strip()
        for code in ((intent or {}).get("divisional_charts") or [])
        if str(code or "").strip()
    ]
    if not requested:
        return {}
    try:
        from context_agents.registry import build_agent
        from ai.parallel_chat.parallel_agent_payloads import (
            _collect_divisional_charts,
            _divisional_current_payload,
            _divisional_root_fruit,
            _divisional_topic_payload,
        )

        birth_hash = _INSTANT_CONTEXT_BUILDER._create_birth_hash(birth_data)
        static_cache = getattr(_INSTANT_CONTEXT_BUILDER, "static_cache", None)
        with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
            if isinstance(static_cache, dict):
                if birth_hash not in static_cache:
                    static_cache[birth_hash] = _INSTANT_CONTEXT_BUILDER._build_static_context(birth_data)
                static = static_cache[birth_hash]
            else:
                static = _INSTANT_CONTEXT_BUILDER._build_static_context(birth_data)
        agent_ctx = AgentContext(
            birth_data=birth_data,
            user_question=question,
            intent_result={**(intent or {}), "divisional_charts": requested},
            precomputed_static=static,
            div_intent_omit_codes=frozenset({"D1", "D9"}),
        )
        agents = {
            "core_d1": build_agent("core_d1", agent_ctx),
            "div_d9": build_agent("div_d9", agent_ctx),
            "div_intent": build_agent("div_intent", agent_ctx),
        }
        div_charts = _collect_divisional_charts(agents)
        div_category = _event_divisional_category(category)
        levels = _divisional_levels_for_payload(current_dashas_context)
        topic = _divisional_topic_payload(div_category, div_charts, focus_houses)
        current_topic = _divisional_current_payload(div_category, div_charts, levels, focus_houses)
        navamsa_root_fruit = _divisional_root_fruit(
            agents.get("core_d1") or {},
            agents.get("div_d9") or {},
            div_category,
            focus_houses,
        )
        support: Dict[str, Any] = {
            "requested_charts": requested,
            "available_charts": sorted(div_charts.keys()),
            "topic": topic,
            "current_topic": current_topic,
        }
        skipped = (agents.get("div_intent") or {}).get("S")
        if skipped:
            support["skipped_charts"] = list(skipped)
        return {
            "divisional_support": support,
            "navamsa_root_fruit": navamsa_root_fruit,
        }
    except Exception as exc:
        logger.warning("event divisional support build failed: %s", exc)
        return {}


def _event_chain_label(row: Dict[str, Any]) -> str:
    return " - ".join(
        str(row.get(key) or "").strip()
        for key in ("mahadasha", "antardasha", "pratyantardasha")
        if str(row.get(key) or "").strip()
    )


def _event_row_score(row: Dict[str, Any]) -> int:
    try:
        return int(float(row.get("relevance_score") or row.get("score") or 0))
    except (TypeError, ValueError):
        return 0


def _event_row_window(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "start": row.get("start"),
        "end": row.get("end"),
        "chain": _event_chain_label(row),
        "score": _event_row_score(row),
        "activated_focus_houses": row.get("activated_focus_houses"),
        "why": row.get("why"),
        "time_status": row.get("time_status"),
        "period_strength": row.get("period_strength"),
        "period_label": row.get("period_label"),
    }


def _event_window_claim_contract(category: str, row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict) or not row:
        return {}
    activated_houses = [
        h
        for h in (_norm_house(h) for h in (row.get("activated_focus_houses") or []))
        if h is not None
    ]
    focus_houses = [
        h
        for h in (_norm_house(h) for h in (CATEGORY_FOCUS.get(_normalize_event_category(category), {}).get("houses") or []))
        if h is not None
    ]
    return {
        "dasha_chain": _event_chain_label(row),
        "activated_focus_houses": activated_houses,
        "allowed_house_themes": [
            {"house": h, "theme": SPEECH_HOUSE_THEME_LABELS.get(h, HOUSE_THEME_LABELS.get(h, ""))}
            for h in activated_houses
        ],
        "inactive_focus_houses": [h for h in focus_houses if h not in activated_houses],
        "claim_rule": (
            "Only activated_focus_houses may be described as active/supportive for this timing window. "
            "Other focus houses are possible topic houses, not active evidence for this window."
        ),
    }


def _cluster_best_future_event_windows(periods: List[Dict[str, Any]], best_row: Dict[str, Any]) -> Dict[str, Any]:
    if not best_row:
        return {}
    best_chain = _event_chain_label(best_row)
    best_score = _event_row_score(best_row)
    selected: List[Dict[str, Any]] = []
    for row in periods:
        if not isinstance(row, dict):
            continue
        if str(row.get("time_status") or "").lower() == "current":
            continue
        if _event_chain_label(row) != best_chain:
            continue
        if abs(_event_row_score(row) - best_score) > 5:
            continue
        selected.append(row)
    if not selected:
        selected = [best_row]
    selected.sort(key=lambda r: str(r.get("start") or ""))
    reasons: List[str] = []
    for row in selected:
        reason = str(row.get("why") or "").strip()
        if reason:
            reasons.extend([part.strip() for part in reason.split(";") if part.strip()])
    return {
        "start": selected[0].get("start"),
        "end": selected[-1].get("end"),
        "chain": best_chain,
        "score": best_score,
        "segments": [_event_row_window(row) for row in selected[:6]],
        "why": list(dict.fromkeys(reasons))[:6],
    }


def _build_event_timing_verdict(
    *,
    category: str,
    forward_scan_periods: List[Dict[str, Any]],
    horizon_segments: List[Dict[str, Any]],
    current_chain_rows: List[Dict[str, Any]],
    timing_policy: Dict[str, Any],
) -> Dict[str, Any]:
    periods = [row for row in (forward_scan_periods or []) if isinstance(row, dict)]
    current_candidates = [
        row for row in periods if str(row.get("time_status") or "").lower() == "current"
    ]
    if not current_candidates:
        current_candidates = [
            row for row in (horizon_segments or [])
            if isinstance(row, dict) and str(row.get("time_status") or "").lower() == "current"
        ]
    current_row = max(current_candidates, key=_event_row_score) if current_candidates else {}
    future_candidates = [
        row for row in periods
        if str(row.get("time_status") or "").lower() != "current"
    ]
    best_future = max(future_candidates, key=_event_row_score) if future_candidates else {}

    current_score = _event_row_score(current_row) if current_row else 0
    future_score = _event_row_score(best_future) if best_future else 0
    score_delta = future_score - current_score

    if current_row and best_future:
        if abs(score_delta) <= 5:
            comparison = "current_active_future_slightly_cleaner" if score_delta >= 0 else "current_comparable_or_stronger"
            answer_rule = (
                "Say the current period is active, but mixed or less settled if current dasha factors show pressure. "
                "Say the future window is only slightly cleaner/stronger, not overwhelmingly better. Do not imply current potential is absent."
            )
            confidence = "medium"
        elif score_delta <= 15:
            comparison = "future_meaningfully_stronger" if score_delta > 0 else "current_meaningfully_stronger"
            answer_rule = (
                "Lead with the stronger window, but still acknowledge the other active window. "
                "Use measured wording: meaningfully stronger, not guaranteed."
            )
            confidence = "medium"
        else:
            comparison = "future_clearly_stronger" if score_delta > 0 else "current_clearly_stronger"
            answer_rule = (
                "Lead with the clearly stronger window and mention the weaker window only as background activation. "
                "Avoid guaranteed dates."
            )
            confidence = "medium_high"
    elif best_future:
        comparison = "future_window_available_current_not_prominent"
        answer_rule = "Lead with the best future window; say current evidence is not the main materialization window."
        confidence = "medium"
    elif current_row:
        comparison = "current_window_available_future_thin"
        answer_rule = "Lead with current activation; say the scan does not show a cleaner future window inside the horizon."
        confidence = "medium_low"
    else:
        comparison = "thin_timing_evidence"
        answer_rule = "Do not give a strong timing claim; explain that the current horizon evidence is thin."
        confidence = "low"

    pressure_factors: List[str] = []
    support_factors: List[str] = []
    for row in current_chain_rows:
        if not isinstance(row, dict):
            continue
        planet = str(row.get("planet") or "")
        level = str(row.get("level") or "")
        if row.get("lordships"):
            support_factors.append(f"{level} {planet} carries lordships {row.get('lordships')}.")
        if row.get("natal_house"):
            support_factors.append(f"{level} {planet} is placed in natal house {row.get('natal_house')}.")
        conjunctions = row.get("conjunctions") if isinstance(row.get("conjunctions"), list) else []
        if conjunctions:
            pressure_factors.append(
                f"{level} {planet} is modified by conjunctions with "
                + ", ".join(str(c.get("planet")) for c in conjunctions[:3] if isinstance(c, dict) and c.get("planet"))
                + "."
            )
        if planet in {"Rahu", "Ketu"}:
            pressure_factors.append(f"{level} {planet} can make the active window irregular, unconventional, or less settled.")
        elif planet in {"Saturn", "Mars"} and level in {"AD", "PD"}:
            pressure_factors.append(f"{level} {planet} can add pressure or delay to materialization.")

    future_cluster = _cluster_best_future_event_windows(periods, best_future) if best_future else {}
    current_window = _event_row_window(current_row) if current_row else {}
    current_claim_contract = _event_window_claim_contract(category, current_row)
    future_claim_contract = _event_window_claim_contract(category, best_future)
    required_points = []
    if current_window:
        required_points.append("Mention current activation and its score relationship to the future window.")
    if future_cluster:
        required_points.append("Mention the best future cluster start/end and dasha chain.")
    if abs(score_delta) <= 5 and current_window and future_cluster:
        required_points.append("Say the future window is only slightly cleaner/stronger; do not overstate the gap.")

    return {
        "event_category": _normalize_event_category(category),
        "answer_event_label": EVENT_ANSWER_LABELS.get(_normalize_event_category(category), EVENT_ANSWER_LABELS["general"]),
        "timing_policy": timing_policy or {},
        "current_window": current_window,
        "best_future_window": _event_row_window(best_future) if best_future else {},
        "best_future_cluster": future_cluster,
        "score_delta": score_delta,
        "comparison": comparison,
        "confidence": confidence,
        "support_factors": list(dict.fromkeys(support_factors))[:6],
        "pressure_factors": list(dict.fromkeys(pressure_factors))[:5],
        "answer_rule": answer_rule,
        "claim_contract": {
            "house_claim_rule": (
                "For each timing window, treat activated_focus_houses and the exact why text as the only evidence for which houses are active. "
                "Do not convert a possible focus house into an active house claim unless that house appears in the same window's activated_focus_houses or why text."
            ),
            "current_window": current_claim_contract,
            "best_future_window": future_claim_contract,
        },
        "required_answer_points": required_points,
        "forbidden_answer_moves": [
            "Do not imply current active evidence is absent when current_window exists.",
            "Do not call a small score delta a clearly superior future period.",
            "Do not invent an exact event date beyond the provided windows.",
            "Do not say a planet rules/supports/activates a named domain house unless that exact house is present in that window's activated_focus_houses or why text.",
            "Do not translate 'rules focus house(s) [N]' into 'rules the event house' unless N is the primary event house explicitly active in the same window.",
            "Do not re-rank Window 1 away from the scored best cluster unless score_delta / comparison materially flips.",
            "Do not flip the same period from supportive house significations (e.g. 7th/contracts) to hostile ones (e.g. 8th/rejection) without new activated_focus_houses evidence.",
            "Do not treat a PD / micro-dasha start date as an offer or joining SLA; PD starts are activation/environment shifts unless the ranked execution window supports offer/joining.",
            "Do not use guarantee / copper-bottomed / mathematical conclusion / perfectly accurate / absolute truth / non-negotiable / will get phrasing.",
        ],
        "career_layer_contract": (
            {
                "activation": "more calls, effort, interviews, visibility",
                "offer": "offer letter likely",
                "joining": "start date / settle-in",
                "rule": (
                    "For career/job questions, executive summary must separate Activation vs Offer vs Joining. "
                    "Never let one dasha date mean all three."
                ),
            }
            if _normalize_event_category(category) == "career"
            else None
        ),
    }


def _slim_event_prediction_payload(
    *,
    birth_summary: Dict[str, Any],
    natal_snapshot: Dict[str, Any],
    target_chart_context: Dict[str, Any],
    current_dashas_levels: Dict[str, Any],
    current_transits_formatted: Dict[str, Any],
    instant_parashari: Dict[str, Any],
    normalized_evidence: Dict[str, Any],
    period_window: Dict[str, Any],
    category: str,
    question: str,
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
    named_dasha_lookup: Optional[Dict[str, Any]] = None,
    evidence_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    focus_houses = list((instant_parashari or {}).get("focus_houses") or [])
    safe_current_dashas_levels = current_dashas_levels if isinstance(current_dashas_levels, dict) else {}
    md_p = str((((safe_current_dashas_levels or {}).get("md") or {}).get("planet") or "")).strip()
    ad_p = str((((safe_current_dashas_levels or {}).get("ad") or {}).get("planet") or "")).strip()
    pd_p = str((((safe_current_dashas_levels or {}).get("pd") or {}).get("planet") or "")).strip()
    current_chain_list = [p for p in [md_p, ad_p, pd_p] if p]
    current_chain = " > ".join(current_chain_list)
    current_display = " - ".join(current_chain_list)
    authoritative_fact = (
        f"As of {str((period_window or {}).get('start') or '')}, the current Vimshottari chain is {current_display}."
        if current_display
        else ""
    )
    current_chain_rows: List[Dict[str, Any]] = []
    for lvl in ["md", "ad", "pd"]:
        row = (safe_current_dashas_levels or {}).get(lvl) or {}
        if not isinstance(row, dict) or not row.get("planet"):
            continue
        planet = str(row.get("planet") or "")
        current_chain_rows.append(
            {
                "level": lvl.upper(),
                **_planet_prediction_status(planet, row, chart_data, house_lordships),
                "current_transit_contact": _current_transit_contacts_for_planet(planet, row, current_transits_formatted),
            }
        )
    future_windows: List[Dict[str, Any]] = []
    horizon_segments = list(((instant_parashari or {}).get("horizon_dasha_segments") or {}).get("segments") or [])
    forward_scan_periods = [
        row
        for row in list((((instant_parashari or {}).get("forward_event_dasha_scan") or {}).get("periods") or []))
        if not _is_fallback_dasha_triplet(row.get("mahadasha"), row.get("antardasha"), row.get("pratyantardasha"))
    ]
    timing_policy = dict((normalized_evidence or {}).get("timing_policy") or {})
    event_timing_verdict = _build_event_timing_verdict(
        category=category,
        forward_scan_periods=forward_scan_periods,
        horizon_segments=horizon_segments,
        current_chain_rows=current_chain_rows,
        timing_policy=timing_policy,
    )
    for seg in horizon_segments[:8]:
        future_windows.append(
            {
                "start": seg.get("start"),
                "end": seg.get("end"),
                "chain": " - ".join([str(seg.get("mahadasha") or ""), str(seg.get("antardasha") or ""), str(seg.get("pratyantardasha") or "")]).strip(" -"),
                "activated_focus_houses": seg.get("activated_focus_houses"),
                "score": seg.get("relevance_score"),
                "why": seg.get("why"),
            }
        )
    major_transits: Dict[str, Any] = {}
    for planet in ["Jupiter", "Saturn", "Rahu", "Ketu"]:
        row = (current_transits_formatted or {}).get(planet) or {}
        if isinstance(row, dict) and row:
            major_transits[planet] = {
                "sign": row.get("sign"),
                "house_from_lagna": row.get("house_from_lagna"),
                "retrograde": bool(row.get("retrograde")),
                "nakshatra": row.get("nakshatra"),
            }
    compact_target_context = {
        "key": str(((target_chart_context or {}).get("key") or "self")),
        "label": str(((target_chart_context or {}).get("label") or "self")),
        "anchor_house": (target_chart_context or {}).get("anchor_house"),
        "target_ascendant_sign": (target_chart_context or {}).get("target_ascendant_sign"),
    }
    slim_normalized = {
        "answer_mode_contract": {
            "answer_mode": "event_prediction",
            "category": category,
            "answer_skeleton": "Apply timing_policy -> Verdict from strongest future windows -> Phase shifts from MD/AD/PD changes -> Support vs obstruction vs uncertainty -> Practical takeaway",
        },
        "timing_policy": timing_policy,
        "event_timing_verdict": event_timing_verdict,
        "current_timing": {
            "active_dashas": safe_current_dashas_levels,
            "current_dasha_chain": current_chain,
            "authoritative_current_dasha_display": current_display,
            "authoritative_current_dasha_chain": current_chain,
            "authoritative_current_dasha_fact": authoritative_fact,
            "time_relation": str((normalized_evidence.get("current_timing") or {}).get("time_relation") or "current") if isinstance(normalized_evidence, dict) else "current",
            "period_window": period_window,
        },
        "dasha_level_effects": list((normalized_evidence or {}).get("dasha_level_effects") or [])[:5],
        "future_windows": future_windows,
        "forward_event_dasha_scan": {
            "horizon_days": ((instant_parashari or {}).get("forward_event_dasha_scan") or {}).get("horizon_days"),
            "horizon_end": ((instant_parashari or {}).get("forward_event_dasha_scan") or {}).get("horizon_end"),
            "periods": forward_scan_periods[:8],
        },
        "horizon_dasha_segments": {
            "enabled": bool(horizon_segments),
            "segments": horizon_segments[:8],
            "label": ((instant_parashari or {}).get("horizon_dasha_segments") or {}).get("label"),
        },
        "topic_houses": _topic_house_rows(focus_houses, house_lordships, chart_data),
        "divisional_topic": _compact_divisional_topic_payload((instant_parashari or {}).get("divisional_support") or {}),
        "divisional_support": _compact_divisional_support((instant_parashari or {}).get("divisional_support") or {}),
        "divisional_specifics": list((normalized_evidence or {}).get("divisional_specifics") or [])[:3],
        "transit_contacts": [row.get("current_transit_contact") for row in current_chain_rows if row.get("current_transit_contact")],
        "target_subject": {
            "key": compact_target_context["key"],
            "label": compact_target_context["label"],
            "base_house": compact_target_context["anchor_house"],
        },
        "primary_drivers": [
            f"Asked event: {event_timing_verdict.get('answer_event_label') or event_timing_verdict.get('event_category')}.",
            f"Event timing verdict: {event_timing_verdict.get('comparison')} (confidence {event_timing_verdict.get('confidence')}; score_delta {event_timing_verdict.get('score_delta')}).",
            f"Answer rule: {event_timing_verdict.get('answer_rule')}",
            f"Current chain: {current_display}." if current_display else "",
            *[
                f"Divisional support: {line}"
                for line in list((normalized_evidence or {}).get("divisional_specifics") or [])[:2]
            ],
            *[
                f"Future window {row.get('start')}–{row.get('end')}: {row.get('chain')} (score {row.get('score')}; houses {row.get('activated_focus_houses')}; {row.get('why')})"
                for row in future_windows[:4]
            ],
        ],
    }
    if named_dasha_lookup:
        slim_normalized["named_dasha_lookup"] = named_dasha_lookup
        slim_normalized["primary_drivers"] = [
            *[
                str(row.get("authoritative_fact") or "")
                for row in list(named_dasha_lookup.get("matches") or [])[:3]
                if isinstance(row, dict) and row.get("authoritative_fact")
            ],
            *slim_normalized["primary_drivers"],
        ]
    slim_normalized["primary_drivers"] = [line for line in slim_normalized["primary_drivers"] if line]
    slim_parashari = {
        "source": (instant_parashari or {}).get("source"),
        "category": category,
        "period_window": period_window,
        "focus_houses": focus_houses,
        "topic_key": (instant_parashari or {}).get("topic_key"),
        "current_chain": current_chain_rows,
        "future_windows": future_windows,
        "forward_event_dasha_scan": slim_normalized["forward_event_dasha_scan"],
        "horizon_dasha_segments": slim_normalized["horizon_dasha_segments"],
        "topic_houses": _topic_house_rows(focus_houses, house_lordships, chart_data),
        "divisional_topic": _compact_divisional_topic_payload((instant_parashari or {}).get("divisional_support") or {}),
        "divisional_support": _compact_divisional_support((instant_parashari or {}).get("divisional_support") or {}),
        "major_transits": major_transits,
        "horizon_transit_anchors": (instant_parashari or {}).get("horizon_transit_anchors") or {},
    }
    if named_dasha_lookup:
        slim_parashari["named_dasha_lookup"] = named_dasha_lookup
    return {
        "birth_summary": birth_summary,
        "intent_summary": {
            "category": category,
            "mode": "LIFESPAN_EVENT_TIMING",
            "answer_mode": "event_prediction",
            "period_window": period_window,
            "time_relation": str((normalized_evidence.get("current_timing") or {}).get("time_relation") or "current") if isinstance(normalized_evidence, dict) else "current",
            "focus_houses": focus_houses,
            "extracted_context": {"timeframe": question},
            "target_subject": {"key": "self", "label": "self", "base_house": 1},
        },
        "evidence_plan": evidence_plan or {},
        "natal_snapshot": {
            "house_lordships": natal_snapshot.get("house_lordships") if isinstance(natal_snapshot, dict) else {},
            "topic_houses": _topic_house_rows(focus_houses, house_lordships, chart_data),
            "relevant_planets": {
                row["planet"]: {
                    "natal_house": row["natal_house"],
                    "natal_sign": row["natal_sign"],
                    "lordships": row["lordships"],
                    "dignity": row["dignity"],
                    "natural_nature": row["natural_nature"],
                    "functional_nature": row["functional_nature"],
                    "conjunctions": row["conjunctions"],
                    "natal_aspects_received": row["natal_aspects_received"],
                }
                for row in current_chain_rows
            },
        },
        "target_chart_context": compact_target_context,
        "current_dashas": {
            "as_of": str((period_window or {}).get("start") or ""),
            "levels": safe_current_dashas_levels,
            "named_dasha_lookup": named_dasha_lookup or {},
        },
        "current_transits": {
            "as_of_local": str((period_window or {}).get("start") or ""),
            "planets": major_transits,
        },
        "current_transits_formatted": major_transits,
        "instant_parashari": slim_parashari,
        "normalized_evidence": slim_normalized,
        "recent_history": [],
        "complexity_hint": {"mode": "slim_event_prediction", "question_length": len(question or "")},
        "named_dasha_lookup": named_dasha_lookup or {},
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


def _truncate_speech_answer(text: str, limit: int = 760) -> str:
    raw = re.sub(r"\s+", " ", str(text or "").strip())
    if len(raw) <= limit:
        return raw
    boundary = max(raw.rfind(".", 0, limit), raw.rfind("?", 0, limit), raw.rfind("!", 0, limit), raw.rfind("।", 0, limit))
    if boundary >= 500:
        return raw[: boundary + 1].strip()
    return _truncate(raw, limit)


def _speech_event_label_from_context(instant_context: Dict[str, Any]) -> str:
    normalized = instant_context.get("normalized_evidence") if isinstance(instant_context.get("normalized_evidence"), dict) else {}
    verdict = normalized.get("event_timing_verdict") if isinstance(normalized.get("event_timing_verdict"), dict) else {}
    label = str(verdict.get("answer_event_label") or "").strip()
    if label and label.lower() not in {"general", "this event"}:
        return label
    category = _normalize_event_category(str(((instant_context.get("intent_summary") or {}).get("category") or "")))
    return EVENT_ANSWER_LABELS.get(category, "")


def _polish_speech_event_answer(text: str, instant_context: Dict[str, Any]) -> str:
    raw = str(text or "").strip()
    if not raw:
        return raw
    label = _speech_event_label_from_context(instant_context)
    if label:
        raw = re.sub(r"\bthis event\b", label, raw, flags=re.IGNORECASE)
        raw = re.sub(r"\bthese matters\b", label, raw, flags=re.IGNORECASE)
        raw = re.sub(r"\bthese themes\b", label, raw, flags=re.IGNORECASE)
    replacements = {
        r"\bthe astrological indicators suggest that?\b": "I would read this as",
        r"\bthe astrological indicators point toward\b": "I would look toward",
        r"\bthe astrological indicators point to\b": "I would look to",
        r"\bmaterialization window\b": "main timing window",
        r"\bplanetary influences\b": "dasha pattern",
        r"\bhouse of fortune and dharma\b": "long-range support",
        r"\bhouses? of fortune and dharma\b": "long-range support",
        r"\bfortune and dharma\b": "long-range support",
    }
    for pattern, replacement in replacements.items():
        raw = re.sub(pattern, replacement, raw, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", raw).strip()


def _normalize_question_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


# Phrases where the user is declining to ask, not stating an astrological question.
_CONVERSATIONAL_NON_QUESTION_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bnothing\s+for\s+now\b",
        r"\bnothing\s+right\s+now\b",
        r"\bnothing\s+at\s+the\s+moment\b",
        r"\bnot\s+right\s+now\b",
        r"\bno\s+thanks?\b",
        r"\bno\s+thank\s+you\b",
        r"\bnot\s+yet\b",
        r"\bmaybe\s+later\b",
        r"\blater\s+maybe\b",
        r"\b(don'?t|do\s+not)\s+have\s+a\s+question\b",
        r"\bno\s+questions?\b",
        r"\bnot\s+sure\s+yet\b",
        r"\bstill\s+thinking\b",
        r"\b(i'?m|i\s+am)\s+good\b",
        r"\b(all\s+)?good\s+for\s+now\b",
        r"\bthat'?s\s+all\b",
        r"\bthat\s+is\s+all\b",
        r"\bnothing\s+else\b",
        r"\bnothing\s+more\b",
        r"\bjust\s+browsing\b",
        r"\bnot\s+today\b",
        r"\b(i'?ll|i\s+will)\s+pass\b",
        r"\bnever\s*mind\b",
        r"\bnvm\b",
        r"\bi\s+don'?t\s+know\s+yet\b",
        r"\bno\s+idea\s+yet\b",
    )
)
_CONVERSATIONAL_NON_QUESTION_EXACT = frozenset(
    {
        "no",
        "nope",
        "nah",
        "ok",
        "okay",
        "k",
        "thanks",
        "thank you",
        "ty",
        "nothing",
    }
)


def _is_conversational_non_question(question: str) -> bool:
    """True when the user is not asking for chart work (deferral / thanks / no question yet)."""
    q = _normalize_question_text(question)
    if not q:
        return False
    if q in _CONVERSATIONAL_NON_QUESTION_EXACT:
        return True
    for rx in _CONVERSATIONAL_NON_QUESTION_PATTERNS:
        if rx.search(q):
            return True
    return False


def _conversational_ack_response(language: str, *, speech_mode: bool) -> Dict[str, Any]:
    """Short reply without chart analysis; caller should not charge instant/speech credits."""
    lang = (language or "english").strip().lower()
    if lang.startswith("hi"):
        if speech_mode:
            body = (
                "ठीक है, कोई बात नहीं। जब आपके पास कोई सवाल हो, बस पूछ लीजिए। "
                "अभी मैं चार्ट में कुछ नहीं देख रही हूँ।"
            )
        else:
            body = (
                "ठीक है। जब आप तैयार हों, तब पूछिए — अभी मैं चार्ट में कुछ देखूँगी नहीं।"
            )
    elif speech_mode:
        body = (
            "No problem. I’m not looking anything up in the chart until you have a real question — "
            "just ask when you’re ready."
        )
    else:
        body = (
            "Sure — I won’t dig into the chart until you actually ask something. "
            "Whenever you’re ready, go ahead."
        )
    elapsed_s = 0.0
    return {
        "success": True,
        "response": body,
        "error": None,
        "chat_llm_model": "__conversational_ack__",
        "timing": {
            "chat_llm_provider": "none",
            "chat_llm_model": "__conversational_ack__",
            "instant_chat": True,
            "total_request_time": elapsed_s,
            "conversational_ack": True,
        },
        "token_usage": {},
        "llm_prompt_chars": 0,
        "llm_response_chars": len(body),
        "instant_llm_usage_stage": _build_instant_usage_stage(
            "conversational_ack",
            "__conversational_ack__",
            0,
            len(body),
            {},
            True,
            elapsed_s,
        ),
        "terms": [],
        "glossary": {},
        "follow_up_questions": [],
        "summary_image": None,
        "analysis_steps": [],
        "faq_metadata": None,
        "raw_response": body,
        "instant_context_summary": {
            "category": "general",
            "mode": "conversational",
            "answer_mode": "conversational_ack",
            "period_window": {},
            "time_relation": "none",
            "focus_houses": [],
            "focus_planets": [],
            "extracted_context": {},
            "target_subject": {"key": "self", "label": "self", "base_house": 1},
        },
        "skip_instant_credit_charge": True,
    }


def _instant_lifetime_event_year_clarification_response(language: str, *, speech_mode: bool) -> Dict[str, Any]:
    """Ask user to provide a specific year for instant lane; suggest Standard/Premium for lifetime scan."""
    lang = (language or "english").strip().lower()
    if lang.startswith("hi"):
        body = (
            "क्या आप किसी specific year के लिए पूछ रहे हैं? "
            "Instant chat में मैं year-targeted timing देती हूँ. "
            "अगर lifetime timing चाहिए, तो Standard या Premium chat में switch करें."
        )
    elif speech_mode:
        body = (
            "Are you asking for a specific year? "
            "In instant chat I keep timing year-targeted. "
            "If you want lifetime timing, please switch to Standard or Premium chat."
        )
    else:
        body = (
            "Are you looking for a specific year? In Instant chat I keep timing year-targeted. "
            "If you want lifetime timing, please switch to Standard or Premium chat."
        )
    elapsed_s = 0.0
    return {
        "success": True,
        "response": body,
        "error": None,
        "chat_llm_model": "__instant_year_clarification__",
        "timing": {
            "chat_llm_provider": "none",
            "chat_llm_model": "__instant_year_clarification__",
            "instant_chat": True,
            "total_request_time": elapsed_s,
            "year_clarification": True,
        },
        "token_usage": {},
        "llm_prompt_chars": 0,
        "llm_response_chars": len(body),
        "instant_llm_usage_stage": _build_instant_usage_stage(
            "instant_year_clarification",
            "__instant_year_clarification__",
            0,
            len(body),
            {},
            True,
            elapsed_s,
        ),
        "terms": [],
        "glossary": {},
        "follow_up_questions": [],
        "summary_image": None,
        "analysis_steps": [],
        "faq_metadata": None,
        "raw_response": body,
        "instant_context_summary": {
            "category": "general",
            "mode": "clarification",
            "answer_mode": "year_clarification",
            "period_window": {},
            "time_relation": "none",
            "focus_houses": [],
            "focus_planets": [],
            "extracted_context": {},
            "target_subject": {"key": "self", "label": "self", "base_house": 1},
        },
        "skip_instant_credit_charge": True,
    }


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


def _rotate_house_list(houses: List[Any], anchor_house: int) -> List[int]:
    out: List[int] = []
    for house in houses or []:
        h = _safe_int(house)
        if h is None:
            continue
        out.append(_rotate_house_num(h, anchor_house))
    return out


def _rewrite_house_refs(text: str, anchor_house: int) -> str:
    raw = str(text or "")
    if not raw:
        return raw

    def repl_single(match: re.Match[str]) -> str:
        num = _safe_int(match.group(1))
        if num is None:
            return match.group(0)
        return f"house {_rotate_house_num(num, anchor_house)}"

    def repl_list(match: re.Match[str]) -> str:
        nums = re.findall(r"\d+", match.group(1) or "")
        rotated = [str(_rotate_house_num(int(n), anchor_house)) for n in nums]
        return f"houses {', '.join(rotated)}"

    raw = re.sub(r"houses\s+((?:\d+\s*,\s*)*\d+)", repl_list, raw)
    raw = re.sub(r"house\s+(\d+)", repl_single, raw)
    return raw


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


def _resolve_period_window(intent: Optional[Dict[str, Any]], now_local: datetime, question: str = "") -> Dict[str, Any]:
    ir = intent or {}
    extracted = ir.get("extracted_context") if isinstance(ir.get("extracted_context"), dict) else {}
    tr = ir.get("transit_request") if isinstance(ir.get("transit_request"), dict) else {}
    year_month_map = tr.get("yearMonthMap") if isinstance(tr.get("yearMonthMap"), dict) else {}
    timeframe_text = str(extracted.get("timeframe") or "").strip().lower()
    if not timeframe_text:
        timeframe_text = str(question or "").strip().lower()
    
    # Handle "this year" or generic year requests
    if "year" in timeframe_text or str(now_local.year) in timeframe_text:
        year = now_local.year
        if "next year" in timeframe_text:
            year += 1
        elif "last year" in timeframe_text:
            year -= 1
        # Extract year number if present (e.g. "in 2027")
        year_matches = re.findall(r"20\d{2}", timeframe_text)
        if year_matches:
            try:
                year = int(year_matches[0])
            except ValueError:
                pass
        
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)
        span_days = (end - start).days + 1
        return {
            "kind": "window",
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "span_days": span_days,
            "label": f"the year {year}",
            "use_pd": True,
            "use_sk_pr": False,
        }

    # If the router resolved a calendar month/window, prefer that window.
    if year_month_map:
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
    today = now_local.date()
    if kind == "window":
        start_raw = str((period_window or {}).get("start") or "").strip()
        end_raw = str((period_window or {}).get("end") or "").strip()
        start_dt = _parse_ymd(start_raw)
        end_dt = _parse_ymd(end_raw)
        if start_dt and end_dt:
            if start_dt.date() <= today <= end_dt.date():
                return now_local.replace(hour=12, minute=0, second=0, microsecond=0)
            if end_dt.date() < today:
                return datetime.combine(end_dt.date(), now_local.time())
            if start_dt.date() > today:
                return datetime.combine(start_dt.date(), now_local.time())
    if kind in {"day", "window"}:
        start = str((period_window or {}).get("start") or "").strip()
        if start:
            try:
                return datetime.strptime(start, "%Y-%m-%d").replace(hour=12, minute=0, second=0, microsecond=0)
            except ValueError:
                pass
    return now_local


def _as_naive_local_datetime(value: datetime) -> datetime:
    """Match standard chat's dasha caller: pass local wall-clock datetimes without tzinfo."""
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


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


def _parse_birth_date_only(birth_data: Optional[Dict[str, Any]]) -> Optional[datetime]:
    if not birth_data or not birth_data.get("date"):
        return None
    raw = str(birth_data.get("date") or "").strip().split("T")[0][:10]
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


def _compute_age_years(birth_dt: Optional[datetime], now_local: datetime) -> Optional[int]:
    if birth_dt is None:
        return None
    bd = birth_dt.date() if hasattr(birth_dt, "date") else birth_dt
    nd = now_local.date() if hasattr(now_local, "date") else now_local
    days = (nd - bd).days
    if days < 0:
        return None
    return max(0, days // 365)


def _life_stage_from_age(age_years: Optional[int]) -> str:
    if age_years is None:
        return "unknown"
    if age_years < 13:
        return "child"
    if age_years < 18:
        return "teen"
    if age_years < 22:
        return "young_adult"
    if age_years < 60:
        return "adult"
    return "senior"


def _timing_policy_for_instant_event(
    *,
    age_years: Optional[int],
    life_stage: str,
    category: str,
) -> Dict[str, Any]:
    """Deterministic guardrails for instant event-timing answers (age × category)."""
    cat = str(category or "general").lower()
    restrictions: List[str] = []
    notes: List[str] = []

    if life_stage in {"child", "teen"} and cat in {
        "marriage", "love", "relationship", "partner", "spouse",
    }:
        restrictions.append(
            "Do not predict imminent legal marriage, wedding dates, or partnership contracts for a child or young teen. "
            "If the chart shows 7th-house activity, frame it as social/emotional learning, family dynamics, or long-horizon "
            "natal promise without near-term execution."
        )
    if life_stage == "child" and cat in {"progeny", "marriage", "love"}:
        restrictions.append(
            "For a young child, do not time pregnancy, childbirth, or romantic union as happening soon; stay developmental or refuse false precision."
        )
    if age_years is not None and age_years < 16 and cat in {"career", "job", "promotion", "business"}:
        notes.append(
            "Career questions for minors: emphasize education, skills, and family context rather than job offers or promotions."
        )

    return {
        "age_years": age_years,
        "life_stage": life_stage,
        "event_category": cat,
        "restrictions": restrictions,
        "notes": notes,
    }


def _planet_rules_any_houses(planet: str, house_lordships: Dict[str, Any], houses: List[int]) -> bool:
    if not planet or not houses:
        return False
    hs = {int(h) for h in houses if h is not None}
    ruled = house_lordships.get(planet) if isinstance(house_lordships, dict) else None
    if not ruled:
        return False
    try:
        for h in ruled:
            if int(h) in hs:
                return True
    except (TypeError, ValueError):
        return False
    return False


def _score_event_dasha_row(
    md: str,
    ad: str,
    house_lordships: Dict[str, Any],
    focus_houses: List[int],
    karakas: frozenset,
) -> tuple:
    score = 0
    reasons: List[str] = []
    if _planet_rules_any_houses(md, house_lordships, focus_houses):
        score += 3
        reasons.append(f"{md} MD rules an event-relevant house")
    if _planet_rules_any_houses(ad, house_lordships, focus_houses):
        score += 3
        reasons.append(f"{ad} AD rules an event-relevant house")
    if md in karakas:
        score += 1
        reasons.append(f"{md} is a natural significator for this topic")
    if ad in karakas:
        score += 1
        reasons.append(f"{ad} is a natural significator for this topic")
    return score, reasons


def _merge_adjacent_low_score_event_periods(
    periods: List[Dict[str, Any]],
    *,
    low_score_threshold: int = 2,
) -> List[Dict[str, Any]]:
    """Collapse neighboring low-signal MD-AD rows to keep instant JSON lean."""
    if not periods:
        return []
    out: List[Dict[str, Any]] = []
    for row in periods:
        if not out:
            row["ad_chain"] = [row.get("antardasha")]
            row["merged_segments"] = 1
            row["period_strength"] = "normal"
            out.append(row)
            continue
        prev = out[-1]
        prev_score = int(prev.get("relevance_score") or 0)
        row_score = int(row.get("relevance_score") or 0)
        prev_start = _parse_ymd(prev.get("start"))
        prev_end = _parse_ymd(prev.get("end"))
        row_start = _parse_ymd(row.get("start"))
        row_end = _parse_ymd(row.get("end"))
        is_adjacent = (
            prev_end is not None
            and row_start is not None
            and row_start <= (prev_end + timedelta(days=1))
        )
        should_merge = (
            is_adjacent
            and prev.get("mahadasha") == row.get("mahadasha")
            and prev_score <= low_score_threshold
            and row_score <= low_score_threshold
        )
        if not should_merge:
            row["ad_chain"] = [row.get("antardasha")]
            row["merged_segments"] = 1
            row["period_strength"] = "normal"
            out.append(row)
            continue
        prev["end"] = row.get("end")
        prev["merged_segments"] = int(prev.get("merged_segments") or 1) + 1
        chain = list(prev.get("ad_chain") or [])
        chain.append(row.get("antardasha"))
        prev["ad_chain"] = chain
        if chain and chain[0] != chain[-1]:
            prev["antardasha"] = f"{chain[0]}->{chain[-1]}"
        prev["relevance_score"] = max(prev_score, row_score)
        prev_reason = str(prev.get("why") or "").strip()
        row_reason = str(row.get("why") or "").strip()
        if row_reason and row_reason not in prev_reason:
            prev["why"] = "; ".join(x for x in [prev_reason, row_reason] if x)
    for row in out:
        merged_count = int(row.get("merged_segments") or 1)
        score = int(row.get("relevance_score") or 0)
        is_background_weak = merged_count > 1 and score <= low_score_threshold
        if is_background_weak:
            row["period_strength"] = "background_weak"
            row["period_label"] = "background/weak period"
            row["why"] = f"Low-support stretch: {row.get('why')}"
        elif score <= low_score_threshold:
            row["period_strength"] = "weak"
            row["period_label"] = "weaker period"
        else:
            row["period_strength"] = "normal"
    return out


def _build_forward_event_dasha_scan(
    birth_data: Dict[str, Any],
    now_local: datetime,
    house_lordships: Dict[str, Any],
    focus_houses: List[int],
    category: str,
    chart_data: Optional[Dict[str, Any]] = None,
    transit_calc: Optional[RealTransitCalculator] = None,
    ascendant_longitude: Optional[float] = None,
    current_dashas: Optional[Dict[str, Any]] = None,
    *,
    limit: int = 12,
    raw_periods: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Ranked MD/AD/PD segments over the next ~3 years relevant to the event category."""
    cat = str(category or "general").lower()
    karakas = EVENT_CATEGORY_KARAKAS.get(cat, frozenset())
    now_local = _as_naive_local_datetime(now_local)
    end_local = now_local + timedelta(days=_INSTANT_EVENT_HORIZON_DAYS)
    if raw_periods is not None:
        raw_rows = raw_periods
    else:
        calc = DashaCalculator()
        try:
            raw_rows = calc.get_dasha_periods_for_range(birth_data, now_local, end_local)
        except Exception as exc:
            logger.warning("forward event dasha scan failed: %s", exc)
            return {"horizon_days": _INSTANT_EVENT_HORIZON_DAYS, "periods": [], "error": str(exc)}

    focus = {_norm_house(h) for h in (focus_houses or [])}
    focus.discard(None)
    scored_rows: List[Dict[str, Any]] = []
    current_md = str((((current_dashas or {}).get("mahadasha") or {}).get("planet") or "")).strip()
    current_ad = str((((current_dashas or {}).get("antardasha") or {}).get("planet") or "")).strip()
    current_pd = str((((current_dashas or {}).get("pratyantardasha") or {}).get("planet") or "")).strip()
    current_is_fallback = _is_dasha_calculator_fallback_payload(current_dashas or {})
    profile = _category_priority_profile(cat)
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        md = str(row.get("mahadasha") or "")
        ad = str(row.get("antardasha") or "")
        pd = str(row.get("pratyantardasha") or "")
        if not current_is_fallback and _is_fallback_dasha_triplet(md, ad, pd):
            continue
        st = _parse_ymd(row.get("start_date") or row.get("start"))
        en = _parse_ymd(row.get("end_date") or row.get("end"))
        if st is None or en is None:
            continue
        chain = [("md", md, 2), ("ad", ad, 3), ("pd", pd, 4)]
        reasons: List[str] = []
        activated_focus: set[int] = set()
        score = 0
        seg_anchor = st + (en - st) / 2

        for lvl, p, weight in chain:
            if not p:
                continue
            p_row = ((chart_data or {}).get("planets") or {}).get(p) or {}
            natal_house = _norm_house(p_row.get("house"))
            ruled_houses = {_norm_house(h) for h in (house_lordships.get(p) or [])}
            ruled_houses.discard(None)
            if ruled_houses & focus:
                matched = sorted(ruled_houses & focus)
                bonus = sum(_house_priority_weight(cat, h) for h in matched)
                score += int(round((weight * 2) * bonus))
                activated_focus |= set(matched)
                reasons.append(f"{lvl.upper()} {p} rules focus house(s) {matched}")
            if natal_house and natal_house in focus:
                score += int(round(weight * _house_priority_weight(cat, natal_house)))
                activated_focus.add(natal_house)
                reasons.append(f"{lvl.upper()} {p} occupies focus house {natal_house}")
            if natal_house:
                for fh in focus:
                    if _planet_aspects_house_from(natal_house, fh, p):
                        score += int(round(1 * _house_priority_weight(cat, fh)))
                        activated_focus.add(fh)
                        reasons.append(f"{lvl.upper()} {p} aspects focus house {fh} from natal")
                        break
            if p in karakas:
                score += int(round(_planet_priority_weight(cat, p)))
                reasons.append(f"{lvl.upper()} {p} is a category significator")
            if any(h in (ruled_houses or set()) for h in (profile.get("house_weights") or {}).keys()):
                top_house_hits = [h for h in sorted(ruled_houses & focus) if _house_priority_weight(cat, h) >= 2.5]
                if top_house_hits:
                    score += 2
                    reasons.append(f"{lvl.upper()} {p} links strongly to primary event house(s) {top_house_hits}")
            if transit_calc is not None and ascendant_longitude is not None and natal_house:
                try:
                    lon = transit_calc.get_planet_position(seg_anchor, p)
                except Exception:
                    lon = None
                if lon is not None:
                    tr_house = _norm_house(
                        transit_calc.calculate_house_from_longitude(lon, ascendant_longitude)
                    )
                    if tr_house == natal_house:
                        score += 2
                        reasons.append(f"{lvl.upper()} {p} transits its natal house {natal_house} (confidence up)")
                    elif _planet_aspects_house_from(tr_house, natal_house, p):
                        score += 1
                        reasons.append(f"{lvl.upper()} {p} transits aspect its natal house {natal_house} (confidence up)")
        if len([h for h in activated_focus if _house_priority_weight(cat, h) >= 2.0]) >= 2:
            score += 2
            reasons.append("Multiple category-priority houses are activated together")
        if score <= 0:
            continue
        is_current_chain = bool(
            md
            and ad
            and md == current_md
            and ad == current_ad
            and (not current_pd or not pd or pd == current_pd)
        )
        scored_rows.append(
            {
                "start": st.strftime("%Y-%m-%d"),
                "end": en.strftime("%Y-%m-%d"),
                "mahadasha": md,
                "antardasha": ad,
                "pratyantardasha": pd,
                "relevance_score": score,
                "period_strength": "weak" if score <= 2 else "normal",
                "period_label": "weaker period" if score <= 2 else "stronger period",
                "time_status": "current" if is_current_chain else "future",
                "activated_focus_houses": sorted(activated_focus),
                "why": "; ".join(list(dict.fromkeys(reasons))[:5]),
            }
        )
    scored_rows.sort(
        key=lambda p: (
            -int(p.get("relevance_score") or 0),
            _parse_ymd(p.get("start")) or now_local,
        )
    )
    periods = scored_rows[:limit]
    return {
        "horizon_days": _INSTANT_EVENT_HORIZON_DAYS,
        "horizon_end": end_local.strftime("%Y-%m-%d"),
        "focus_houses": list(focus_houses),
        "periods": periods,
    }


def _horizon_dasha_segments_for_event(
    *,
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
    now_local: datetime,
    focus_houses: List[int],
    transit_calc: RealTransitCalculator,
    ascendant_longitude: float,
    category: str,
    limit: int = 12,
    raw_periods: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Ranked MD/AD/PD phase segments across the next bounded event horizon."""
    horizon_window = {
        "kind": "horizon",
        "start": now_local.strftime("%Y-%m-%d"),
        "end": (now_local + timedelta(days=_INSTANT_EVENT_HORIZON_DAYS)).strftime("%Y-%m-%d"),
        "span_days": _INSTANT_EVENT_HORIZON_DAYS,
        "label": "next 3 years",
        "use_pd": True,
        "use_sk_pr": False,
    }
    segs = _window_dasha_segments_for_period(
        birth_data=birth_data,
        chart_data=chart_data,
        house_lordships=house_lordships,
        period_window=horizon_window,
        focus_houses=focus_houses,
        transit_calc=transit_calc,
        ascendant_longitude=ascendant_longitude,
        category=category,
        limit=limit,
        raw_periods=raw_periods,
    )
    if isinstance(segs, dict):
        segs["label"] = "next 3 years"
    return segs


def _window_dasha_segments_for_period(
    *,
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
    period_window: Dict[str, Any],
    focus_houses: List[int],
    transit_calc: RealTransitCalculator,
    ascendant_longitude: float,
    category: str,
    limit: int = 18,
    raw_periods: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build ranked MD/AD/PD window segments with activation + transit-to-natal reinforcement."""
    start_dt = _parse_ymd((period_window or {}).get("start"))
    end_dt = _parse_ymd((period_window or {}).get("end"))
    if not start_dt or not end_dt or end_dt < start_dt:
        return {"enabled": False, "segments": []}
    if raw_periods is None:
        calc = DashaCalculator()
        try:
            raw_periods = calc.get_dasha_periods_for_range(birth_data, start_dt, end_dt)
        except Exception as exc:
            logger.warning("window dasha segments failed: %s", exc)
            return {"enabled": False, "segments": [], "error": str(exc)}

    focus = {_norm_house(h) for h in (focus_houses or [])}
    focus.discard(None)
    karakas = EVENT_CATEGORY_KARAKAS.get(_normalize_event_category(category), frozenset())
    cat = _normalize_event_category(category)
    profile = _category_priority_profile(cat)
    segs: List[Dict[str, Any]] = []
    for row in raw_periods:
        if not isinstance(row, dict):
            continue
        s = _parse_ymd(row.get("start_date"))
        e = _parse_ymd(row.get("end_date"))
        if not s or not e:
            continue
        md = str(row.get("mahadasha") or "").strip()
        ad = str(row.get("antardasha") or "").strip()
        pd = str(row.get("pratyantardasha") or "").strip()
        chain = [("md", md, 2), ("ad", ad, 3), ("pd", pd, 4)]
        activated_focus: set[int] = set()
        reasons: List[str] = []
        score = 0
        seg_anchor = s + (e - s) / 2

        for lvl, p, weight in chain:
            if not p:
                continue
            p_row = ((chart_data.get("planets") or {}).get(p) or {})
            natal_house = _norm_house(p_row.get("house"))
            ruled_houses = {_norm_house(h) for h in (house_lordships.get(p) or [])}
            ruled_houses.discard(None)
            if ruled_houses & focus:
                matched = sorted(ruled_houses & focus)
                bonus = sum(_house_priority_weight(cat, h) for h in matched)
                score += int(round((weight * 2) * bonus))
                activated_focus |= set(matched)
                reasons.append(f"{lvl.upper()} {p} rules focus house(s) {matched}")
            if natal_house and natal_house in focus:
                score += int(round(weight * _house_priority_weight(cat, natal_house)))
                activated_focus.add(natal_house)
                reasons.append(f"{lvl.upper()} {p} occupies focus house {natal_house}")
            if natal_house:
                for fh in focus:
                    if _planet_aspects_house_from(natal_house, fh, p):
                        score += int(round(1 * _house_priority_weight(cat, fh)))
                        activated_focus.add(fh)
                        reasons.append(f"{lvl.upper()} {p} aspects focus house {fh} from natal")
                        break
            if p in karakas:
                score += int(round(_planet_priority_weight(cat, p)))
                reasons.append(f"{lvl.upper()} {p} is a category significator")
            if any(h in (ruled_houses or set()) for h in (profile.get("house_weights") or {}).keys()):
                top_house_hits = [h for h in sorted(ruled_houses & focus) if _house_priority_weight(cat, h) >= 2.5]
                if top_house_hits:
                    score += 2
                    reasons.append(f"{lvl.upper()} {p} links strongly to primary event house(s) {top_house_hits}")

            # Transit reinforcement: dasha lord transiting on/aspecting its own natal house.
            try:
                lon = transit_calc.get_planet_position(seg_anchor, p)
            except Exception:
                lon = None
            if lon is not None and natal_house:
                tr_house = _norm_house(
                    transit_calc.calculate_house_from_longitude(lon, ascendant_longitude)
                )
                if tr_house == natal_house:
                    score += 2
                    reasons.append(f"{lvl.upper()} {p} transits its natal house {natal_house} (confidence up)")
                elif _planet_aspects_house_from(tr_house, natal_house, p):
                    score += 1
                    reasons.append(f"{lvl.upper()} {p} transits aspect its natal house {natal_house} (confidence up)")

        if len([h for h in activated_focus if _house_priority_weight(cat, h) >= 2.0]) >= 2:
            score += 2
            reasons.append("Multiple category-priority houses are activated together")

        if score <= 0:
            continue
        segs.append(
            {
                "start": s.strftime("%Y-%m-%d"),
                "end": e.strftime("%Y-%m-%d"),
                "mahadasha": md,
                "antardasha": ad,
                "pratyantardasha": pd,
                "relevance_score": score,
                "activated_focus_houses": sorted(activated_focus),
                "why": "; ".join(list(dict.fromkeys(reasons))[:5]),
            }
        )

    segs.sort(key=lambda r: (-int(r.get("relevance_score") or 0), r.get("start") or ""))
    return {
        "enabled": bool(segs),
        "focus_houses": sorted([h for h in focus if h is not None]),
        "segments": segs[:limit],
    }


def _horizon_jupiter_saturn_anchors(
    transit_calc: RealTransitCalculator,
    ascendant_longitude: float,
    anchor_start: datetime,
    anchor_end: datetime,
) -> Dict[str, Any]:
    """Minimal slow-planet anchors at start and end of the 5y horizon (sign + house from lagna)."""
    out: Dict[str, Any] = {}
    for label, dt in (("at_horizon_start", anchor_start), ("at_horizon_end", anchor_end)):
        row: Dict[str, str] = {}
        for planet in ("Jupiter", "Saturn"):
            try:
                lon = transit_calc.get_planet_position(dt, planet)
                if lon is None:
                    continue
                sign_index = int(lon / 30) % 12
                sign = SIGN_NAMES[sign_index]
                house = transit_calc.calculate_house_from_longitude(lon, ascendant_longitude)
                row[planet] = f"{sign}, house {house} from lagna"
            except Exception:
                continue
        if row:
            out[label] = row
    return out


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
        if str(active_row.get("p") or "").strip() != planet:
            active_row = {}
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
        conjunctions = list(row.get("conjunctions") or [])[:2]

        contribution_parts: List[str] = []
        if natal_house is not None:
            contribution_parts.append(f"anchors through natal house {natal_house}")
        if lordships:
            contribution_parts.append(f"carries houses {', '.join(str(v) for v in lordships[:3])}")
        if aspect_houses:
            contribution_parts.append(f"pushes activation to houses {', '.join(str(v) for v in aspect_houses[:4])}")
        if conjunctions:
            conj_parts: List[str] = []
            for conj in conjunctions:
                if not isinstance(conj, dict):
                    continue
                other = str(conj.get("planet") or "").strip()
                if not other:
                    continue
                orb = conj.get("orb_degrees")
                conj_parts.append(f"{other} (orb {orb}°)" if orb is not None else other)
            if conj_parts:
                contribution_parts.append(f"is conjunct {'; '.join(conj_parts)}")
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
                "conjunctions": conjunctions,
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
            rotated_row["house_from_lagna"] = rotated_house
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


def _rotate_active_dashas_context(
    current_dashas_context: Dict[str, Any],
    target_chart_context: Dict[str, Any],
) -> Dict[str, Any]:
    target_house_lordships = (target_chart_context.get("target_house_lordships") or {}) if isinstance(target_chart_context, dict) else {}
    target_planets = (target_chart_context.get("target_key_planets") or {}) if isinstance(target_chart_context, dict) else {}
    out: Dict[str, Any] = {}
    for lvl, row in (current_dashas_context or {}).items():
        if not isinstance(row, dict):
            continue
        planet = str(row.get("planet") or "")
        rotated = dict(row)
        target_row = (target_planets.get(planet) or {}) if planet else {}
        house = _safe_int(target_row.get("house"))
        if house is not None:
            rotated["natal_house"] = house
        rotated["lordships"] = target_house_lordships.get(planet, []) if planet else []
        out[str(lvl)] = rotated
    return out


def _rotate_raw_active_dashas(
    raw_levels: Dict[str, Any],
    target_chart_context: Dict[str, Any],
) -> Dict[str, Any]:
    target_house_lordships = (target_chart_context.get("target_house_lordships") or {}) if isinstance(target_chart_context, dict) else {}
    target_planets = (target_chart_context.get("target_key_planets") or {}) if isinstance(target_chart_context, dict) else {}
    out: Dict[str, Any] = {}
    for lvl, row in (raw_levels or {}).items():
        if not isinstance(row, dict):
            continue
        planet = str(row.get("p") or "")
        rotated = dict(row)
        target_row = (target_planets.get(planet) or {}) if planet else {}
        house = _safe_int(target_row.get("house"))
        if house is not None:
            rotated["h"] = house
        rotated["rh"] = target_house_lordships.get(planet, []) if planet else []
        rotated["ahs"] = _rotate_house_list(row.get("ahs") or [], _safe_int(target_chart_context.get("anchor_house")) or 1)
        out[str(lvl)] = rotated
    return out


def _rotate_house_activation_map(hi: Dict[str, Any], anchor_house: int) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {}
    for house_key, row in (hi or {}).items():
        house = _safe_int(house_key)
        if house is None or not isinstance(row, dict):
            continue
        rotated_house = _rotate_house_num(house, anchor_house)
        out[str(rotated_house)] = {
            "r": list(row.get("r") or []),
            "o": list(row.get("o") or []),
            "a": list(row.get("a") or []),
        }
    return out


def _rotate_transit_pressure(tr: Dict[str, Any], anchor_house: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {k: v for k, v in (tr or {}).items() if k not in {"dp", "th", "nh", "n"}}
    rows: List[Dict[str, Any]] = []
    th_counts: Dict[str, int] = {}
    nh_counts: Dict[str, int] = {}
    for row in (tr.get("dp") or []):
        if not isinstance(row, dict):
            continue
        rotated = dict(row)
        th = _safe_int(row.get("th"))
        nh = _safe_int(row.get("nh"))
        if th is not None:
            rotated_th = _rotate_house_num(th, anchor_house)
            rotated["th"] = rotated_th
            th_counts[str(rotated_th)] = th_counts.get(str(rotated_th), 0) + 1
        if nh is not None:
            rotated_nh = _rotate_house_num(nh, anchor_house)
            rotated["nh"] = rotated_nh
            nh_counts[str(rotated_nh)] = nh_counts.get(str(rotated_nh), 0) + 1
        if row.get("at"):
            rotated["at"] = _rewrite_house_refs(str(row.get("at") or ""), anchor_house)
        rows.append(rotated)
    out["dp"] = rows
    out["n"] = len(rows)
    if th_counts:
        out["th"] = th_counts
    if nh_counts:
        out["nh"] = nh_counts
    return out


def _rotate_instant_parashari_for_target(
    instant_parashari: Dict[str, Any],
    target_chart_context: Dict[str, Any],
    category_focus_houses: List[int],
) -> Dict[str, Any]:
    anchor_house = _safe_int(target_chart_context.get("anchor_house")) or 1
    rotated = dict(instant_parashari or {})
    raw_levels = instant_parashari.get("active_dashas") or {}
    hi = instant_parashari.get("house_activation") or {}
    rotated_raw_levels = _rotate_raw_active_dashas(raw_levels, target_chart_context)
    rotated_hi = _rotate_house_activation_map(hi, anchor_house)
    rotated_tr = _rotate_transit_pressure(instant_parashari.get("transit_pressure") or {}, anchor_house)
    rotated["active_dashas"] = rotated_raw_levels
    rotated["active_dashas_formatted"] = _rotate_active_dashas_context(
        instant_parashari.get("active_dashas_formatted") or {},
        target_chart_context,
    )
    rotated["house_activation"] = rotated_hi
    rotated["transit_pressure"] = rotated_tr
    rotated["top_supports"] = [_rewrite_house_refs(v, anchor_house) for v in (instant_parashari.get("top_supports") or [])[:4]]
    rotated["top_risks"] = [_rewrite_house_refs(v, anchor_house) for v in (instant_parashari.get("top_risks") or [])[:3]]
    focus_houses = category_focus_houses or list(instant_parashari.get("focus_houses") or [])
    rotated["focus_houses"] = focus_houses
    rotated["dominant_houses"] = [line for line in _dominant_house_lines(rotated_hi, limit=3)]
    rotated["activation_mechanisms"] = _house_activation_mechanisms(focus_houses, rotated_hi, rotated_raw_levels, limit=3)
    return rotated


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


def _explicit_remedy_followup_requested(intent: Optional[Dict[str, Any]]) -> bool:
    """
    Remedy should only run when the client explicitly marks the request as a remedy follow-up.
    We do not infer it from generic wording because that can hijack the first answer.
    """
    query_context = (intent or {}).get("query_context")
    if not isinstance(query_context, dict):
        return False

    candidate_values = [
        query_context.get("follow_up_type"),
        query_context.get("followUpType"),
        query_context.get("chat_action"),
        query_context.get("chatAction"),
        query_context.get("mode"),
        query_context.get("answer_mode"),
    ]
    normalized = {str(value or "").strip().lower() for value in candidate_values if str(value or "").strip()}
    if normalized & {"remedy", "remedy_followup", "remedy_action"}:
        return True
    if bool(query_context.get("remedy_followup")) or bool(query_context.get("remedy_action")):
        return True
    if bool(query_context.get("open_remedy")) or bool(query_context.get("openRemedy")):
        return True
    return False


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


def _looks_like_open_ended_life_event_when(question: str, intent: Optional[Dict[str, Any]]) -> bool:
    """Single life-event timing ('when will I get X') vs a generic calendar window read."""
    q = str(question or "").lower()
    mode = str((intent or {}).get("mode") or "").upper()
    when_clause = bool(
        re.search(r"\bwhen\s+(will|would|can|shall)\s+(i|my|we)\b", q)
        or re.search(r"\bkab\b", q)
    )
    if not when_clause and mode not in {"LIFESPAN_EVENT_TIMING", "PREDICT_EVENT_TIMING"}:
        return False
    markers = (
        "married",
        "marriage",
        "wedding",
        "marry",
        "shaadi",
        "vivah",
        "job",
        "naukri",
        "employ",
        "career",
        "promotion",
        "baby",
        "child",
        "children",
        "pregnant",
        "pregnancy",
        "conceive",
        " give birth",
        "come back",
        "lover",
        " ex ",
        " ex?",
        "my ex",
        "reconcile",
        "get back together",
        "wealth",
        "money",
        "become rich",
        "health",
        "recover",
        "buy a house",
        "buy house",
        "property",
        "visa",
        "travel abroad",
        "fall in love",
        "soulmate",
    )
    return any(m in q for m in markers)


def _looks_like_timing_window_question(question: str, intent: Optional[Dict[str, Any]]) -> bool:
    q = str(question or "").lower()
    mode = str((intent or {}).get("mode") or "").upper()
    if mode in {"PREDICT_DAILY", "PREDICT_PERIOD_OUTLOOK"}:
        return True
    if _looks_like_open_ended_life_event_when(question, intent):
        return False
    markers = ["today", "tomorrow", "this month", "next month", "this year", "next year", "how will be"]
    return any(marker in q for marker in markers)


def _looks_like_event_prediction_question(question: str, intent: Optional[Dict[str, Any]]) -> bool:
    q = str(question or "").lower()
    mode = str((intent or {}).get("mode") or "").upper()
    if mode in {"LIFESPAN_EVENT_TIMING", "PREDICT_EVENT_TIMING"}:
        return True
    markers = [
        "will ", "what will happen", "when will", "is it likely", "will it happen",
        "can this happen", "chance of", "possibility of",
    ]
    return any(marker in q for marker in markers)


def _infer_answer_mode(question: str, intent: Optional[Dict[str, Any]], history: List[Dict[str, Any]]) -> str:
    if _looks_like_explanatory_followup(question, history):
        return "explanation_mechanism"
    if _explicit_remedy_followup_requested(intent):
        return "remedy_action"
    if _looks_like_comparison_question(question):
        return "comparison_choice"
    if _looks_like_problem_question(question):
        return "problem_diagnosis"
    if _looks_like_relationship_person_question(question):
        return "relationship_person"
    if _looks_like_personality_question(question):
        return "trait_nature"
    if _looks_like_open_ended_life_event_when(question, intent):
        return "event_prediction"
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
- timing_window: user asks how a named calendar window feels overall (this month, next six months, October 2026) without a single concrete life-event line as the main ask
- event_prediction: user asks when/if one specific life event will happen (e.g. marriage, job, child, lover returning); prefer this over timing_window even if they add "this year" or similar
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

Instant chat now handles open-ended event timing by scanning a bounded forward horizon itself:
- Set `needs_year_clarification=false` for open-ended event timing like "when will I get married" or "when will I get a job"; do not ask for a specific year first.
- Set `needs_year_clarification=false` when a specific year/window is already given, or when the question is not event timing.

Return JSON only:
{{"answer_mode":"one_of_the_allowed_modes","confidence":"high|medium|low","reason":"very short reason","target_subject_key":"allowed_target_or_self","needs_year_clarification":true_or_false}}

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
        needs_year_clarification = False
        if mode in ANSWER_MODES:
            if target_subject is None:
                target_subject = _fallback_target_subject(question)
            return {
                "answer_mode": mode,
                "target_subject": target_subject,
                "needs_year_clarification": needs_year_clarification,
            }
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
            needs_year_clarification = False
            return {
                "answer_mode": mode,
                "target_subject": target_subject,
                "needs_year_clarification": needs_year_clarification,
            }
    logger.warning("instant answer mode llm output invalid, falling back: %s", _truncate(raw, 240))
    fallback_mode = _infer_answer_mode(question, intent, history)
    return {
        "answer_mode": fallback_mode,
        "target_subject": _fallback_target_subject(question),
        "needs_year_clarification": False,
    }


def _mode_selection_from_intent(intent: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(intent, dict):
        return None
    mode = str(intent.get("answer_mode") or "").strip()
    if mode not in ANSWER_MODES:
        return None
    target_key = _normalize_relationship_target_key(intent.get("target_subject_key") or "")
    target_subject: Optional[Dict[str, Any]] = None
    if target_key in TARGET_SUBJECTS:
        meta = TARGET_SUBJECTS.get(target_key) or {}
        target_subject = {
            "key": target_key,
            "label": meta.get("label") or target_key.replace("_", " "),
            "base_house": meta.get("base_house"),
            "confidence": str(intent.get("answer_mode_confidence") or intent.get("confidence") or "medium"),
            "source": "intent_router",
        }
    if target_subject is None:
        target_subject = {"key": "self", "label": "self", "base_house": 1, "confidence": "medium", "source": "intent_router_default"}
    return {
        "answer_mode": mode,
        "target_subject": target_subject,
        "needs_year_clarification": bool(intent.get("needs_year_clarification")),
    }


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


def _active_dasha_conjunctions(
    planet: str,
    chart_data: Dict[str, Any],
    *,
    max_orb_degrees: float = 8.0,
) -> List[Dict[str, Any]]:
    planets = (chart_data or {}).get("planets") or {}
    base = planets.get(planet) or {}
    if not isinstance(base, dict):
        return []
    base_house = _safe_int(base.get("house"))
    base_sign = str(base.get("sign_name") or "")
    try:
        base_degree = float(base.get("degree", 0) or 0)
    except (TypeError, ValueError):
        base_degree = None

    rows: List[Dict[str, Any]] = []
    for other, other_row in planets.items():
        if other == planet or not isinstance(other_row, dict):
            continue
        other_house = _safe_int(other_row.get("house"))
        other_sign = str(other_row.get("sign_name") or "")
        if base_house is None or other_house is None or base_house != other_house:
            continue
        if base_sign and other_sign and base_sign != other_sign:
            continue
        try:
            other_degree = float(other_row.get("degree", 0) or 0)
        except (TypeError, ValueError):
            other_degree = None
        orb = None
        if base_degree is not None and other_degree is not None:
            orb = round(abs(base_degree - other_degree), 2)
            if orb > max_orb_degrees:
                continue
        rows.append(
            {
                "planet": str(other),
                "house": other_house,
                "sign": other_sign,
                "orb_degrees": orb,
            }
        )
    rows.sort(key=lambda row: (999.0 if row.get("orb_degrees") is None else float(row.get("orb_degrees")), row.get("planet") or ""))
    return rows[:3]


def _authoritative_active_dasha_context(
    current_dashas: Dict[str, Any],
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
    period_window: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build MD/AD/PD (and optional SK/PR) context directly from DashaCalculator output.
    This is the source of truth for active dasha names in instant answers.
    """
    out: Dict[str, Any] = {}
    level_key_map = [("md", "mahadasha"), ("ad", "antardasha"), ("pd", "pratyantardasha")]
    if (period_window or {}).get("use_sk_pr"):
        level_key_map.extend([("sk", "sookshma"), ("pr", "prana")])
    for lvl, key in level_key_map:
        row = (current_dashas or {}).get(key) or {}
        if not isinstance(row, dict):
            continue
        planet = str(row.get("planet") or "").strip()
        if not planet:
            continue
        natal = ((chart_data or {}).get("planets") or {}).get(planet) or {}
        out[lvl] = {
            "planet": planet,
            "natal_house": natal.get("house"),
            "natal_sign": natal.get("sign_name"),
            "lordships": list((house_lordships or {}).get(planet) or []),
            "conjunctions": _active_dasha_conjunctions(planet, chart_data),
        }
    return out


def _enrich_active_dasha_context_with_conjunctions(
    active_dashas: Dict[str, Any],
    chart_data: Dict[str, Any],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for lvl, row in (active_dashas or {}).items():
        if not isinstance(row, dict):
            out[lvl] = row
            continue
        next_row = dict(row)
        planet = str(next_row.get("planet") or "").strip()
        if planet and "conjunctions" not in next_row:
            next_row["conjunctions"] = _active_dasha_conjunctions(planet, chart_data)
        out[lvl] = next_row
    return out


def _override_current_timing_with_authoritative_dashas(
    *,
    normalized_evidence: Dict[str, Any],
    active_dashas_context: Dict[str, Any],
    period_window: Dict[str, Any],
) -> None:
    if not isinstance(normalized_evidence, dict):
        return
    md_p = str(((active_dashas_context.get("md") or {}).get("planet") or "")).strip()
    ad_p = str(((active_dashas_context.get("ad") or {}).get("planet") or "")).strip()
    pd_p = str(((active_dashas_context.get("pd") or {}).get("planet") or "")).strip()
    chain_list = [p for p in [md_p, ad_p, pd_p] if p]
    chain = " > ".join(chain_list)
    display = " - ".join(chain_list)
    fact = ""
    if display:
        fact = f"As of {period_window.get('start') or ''}, the current Vimshottari chain is {display}."
    normalized_evidence["current_timing"] = {
        "active_dashas": active_dashas_context,
        "current_dasha_chain": chain,
        "authoritative_current_dasha_display": display,
        "authoritative_current_dasha_chain": chain,
        "authoritative_current_dasha_fact": fact,
        "time_relation": normalized_evidence.get("current_timing", {}).get("time_relation") if isinstance(normalized_evidence.get("current_timing"), dict) else "current",
        "period_window": period_window,
    }


def _is_dasha_calculator_fallback_payload(current_dashas: Dict[str, Any]) -> bool:
    """
    Detect shared calculator emergency fallback payload:
    MD Sun / AD Moon / PD Mars with empty maha_dashas and moon_lord Sun.
    """
    if not isinstance(current_dashas, dict):
        return True
    md = str(((current_dashas.get("mahadasha") or {}).get("planet") or "")).strip()
    ad = str(((current_dashas.get("antardasha") or {}).get("planet") or "")).strip()
    pd = str(((current_dashas.get("pratyantardasha") or {}).get("planet") or "")).strip()
    maha_list = current_dashas.get("maha_dashas")
    moon_lord = str(current_dashas.get("moon_lord") or "").strip()
    return (
        md == "Sun"
        and ad == "Moon"
        and pd == "Mars"
        and isinstance(maha_list, list)
        and len(maha_list) == 0
        and moon_lord == "Sun"
    )


def _is_fallback_dasha_triplet(md: str, ad: str, pd: str) -> bool:
    return (
        str(md or "").strip() == "Sun"
        and str(ad or "").strip() == "Moon"
        and str(pd or "").strip() == "Mars"
    )


def _standard_chat_current_dashas(
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
) -> Dict[str, Any]:
    """Use the same current-dasha path as standard chat when instant's dated anchor fails."""
    try:
        builder = _INSTANT_CONTEXT_BUILDER
        birth_hash = builder._create_birth_hash(birth_data)
        if birth_hash not in builder.static_cache:
            builder.static_cache[birth_hash] = builder._build_static_context(birth_data)
        dynamic_context = builder._build_dynamic_context(birth_data, "", None, None, None)
        current_dashas = dynamic_context.get("current_dashas") or {}
        builder.augment_current_dashas_with_chart_hints(current_dashas, chart_data, house_lordships)
        return current_dashas
    except Exception as exc:
        logger.warning("standard chat current dasha fallback failed for instant context: %s", exc)
        return {}


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
        period_kind = str((period_window or {}).get("kind") or "")
        span_days = int((period_window or {}).get("span_days") or 0)
        if period_kind == "day":
            skeleton = "Day verdict -> Exact date anchor -> MD/AD/PD plus Sookshma/Prana roles -> Top 2-3 active areas for that day -> Transit trigger/caution -> Practical use of the day"
            avoid_drift = ["broad lifetime reading", "month/year generalization", "natal-only reading", "overstating one day as destiny"]
        elif span_days >= 180:
            skeleton = "Year verdict -> Phase-wise window_dasha_segments across the year -> Top 2-3 active life areas -> Stronger and weaker phases -> Slow transit confirmation -> Practical use of the year"
            avoid_drift = ["broad lifetime reading", "single-day transit overreach", "one static dasha summary for the whole year", "unanchored natal-only reading"]
        else:
            skeleton = "Window verdict -> Phase-wise window_dasha_segments (MD/AD/PD transitions) -> Top 2-3 active areas in this period -> Exact mechanism for each major area -> Month tone-setter if truly relevant -> Opportunity vs pressure -> Practical use of the period"
            avoid_drift = ["broad lifetime reading", "unanchored natal-only reading", "whole-month prose from one-day fast-planet snapshots"]
        base.update(
            {
                "primary_evidence": ["window_dasha_segments", "active_dashas_formatted", "dasha_level_effects", "dasha_chain_synthesis", "active_areas", "transit_pressure"],
                "secondary_evidence": ["month_tone", "divisional_support.current_topic", "topic_signals"],
                "avoid_drift": avoid_drift,
                "answer_skeleton": skeleton,
            }
        )
    elif answer_mode == "event_prediction":
        base.update(
            {
                "primary_evidence": [
                    "timing_policy",
                    "forward_event_dasha_scan",
                    "horizon_dasha_segments",
                    "horizon_transit_anchors",
                    "window_dasha_segments",
                    "active_dashas_formatted",
                    "activation_mechanisms",
                    "transit_pressure",
                ],
                "secondary_evidence": ["divisional_support.current_topic", "current_transits_formatted"],
                "avoid_drift": [
                    "generic motivation talk",
                    "unrelated personality analysis",
                    "question-led yes bias",
                    "upgrading activation into certainty",
                    "ignoring timing_policy restrictions for minors",
                    "inventing specific years or wedding dates not supported by forward_event_dasha_scan or current evidence",
                    "answering only from the current MD/AD when ranked horizon periods show a stronger later window",
                    "flattening the next 3 years into one static dasha pair when horizon_dasha_segments show AD or PD changes",
                ],
                "answer_skeleton": "Apply timing_policy (age-appropriate) -> Verdict using the strongest ranked windows in the next 3 years -> Phase shifts from horizon_dasha_segments (AD/PD changes) -> Support vs obstruction vs uncertainty -> Practical takeaway",
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
                "primary_evidence": ["top_risks", "activation_mechanisms", "transit_pressure", "active_dashas_formatted", "target_subject", "target_chart_context"],
                "secondary_evidence": ["divisional_support.current_topic"],
                "avoid_drift": ["generic reassurance", "unasked remedy list", "broad event prediction", "cinematic injury narrative", "using native-frame health houses for a non-self target"],
                "answer_skeleton": "Main vulnerable target-relative houses -> Exact dasha activation -> Trigger layer if clearly supported -> Why the event or problem became tangible -> Practical handling",
            }
        )
        if cat == "health" and str(time_relation or "").lower() == "past":
            base["answer_skeleton"] = "Past vulnerable target-relative houses -> Exact active dasha lords -> Trigger layer only if clearly supported -> Why the event likely became tangible -> Brief caution on certainty"
            base["avoid_drift"] = list(base["avoid_drift"]) + [
                "treating one house as a complete injury verdict",
                "overstated causal certainty",
                "dramatic injury phrasing",
            ]
    elif answer_mode == "remedy_action":
        base.update(
            {
                "primary_evidence": ["remedy_blueprint.priority_order", "remedy_blueprint.special_points", "top_risks", "active_dashas_formatted"],
                "secondary_evidence": ["divisional_support.current_topic", "remedy_blueprint.remedy_sections"],
                "avoid_drift": [
                    "too many remedies",
                    "non-astrological lecture",
                    "generic remedy dump",
                    "mixing diagnosis with remedy instructions",
                ],
                "answer_skeleton": "Problem focus -> What is most pressing now -> Constructive house expression -> Remedy layers by category -> Special blockage notes -> One caution",
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
    elif cat in {"marriage", "love", "relationship", "partner", "spouse"} and answer_mode in {"topic_reading"}:
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
    window_dasha_segments = instant_parashari.get("window_dasha_segments") or {}
    horizon_dasha_segments = instant_parashari.get("horizon_dasha_segments") or {}
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
    md_p = str((current_dashas_context.get("md") or {}).get("planet") or "").strip()
    ad_p = str((current_dashas_context.get("ad") or {}).get("planet") or "").strip()
    pd_p = str((current_dashas_context.get("pd") or {}).get("planet") or "").strip()
    current_chain = " > ".join([p for p in [md_p, ad_p, pd_p] if p]) if any([md_p, ad_p, pd_p]) else ""
    current_chain_display = " - ".join([p for p in [md_p, ad_p, pd_p] if p]) if any([md_p, ad_p, pd_p]) else ""
    authoritative_current_dasha_fact = ""
    if current_chain:
        authoritative_current_dasha_fact = (
            f"As of {period_window.get('start') or ''}, the current Vimshottari chain is {current_chain_display}."
        ).strip()
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
    period_kind = str((period_window or {}).get("kind") or "")
    period_span_days = int((period_window or {}).get("span_days") or 0)
    if period_kind == "window":
        contradiction_flags.append("Do not narrate the whole month from a one-day Sun or Moon snapshot; use MD/AD/PD first and treat only slow-planet transits as month-wide anchors.")
    horizon_lines: List[str] = []
    horizon_segment_lines: List[str] = []
    if answer_mode == "event_prediction":
        fd_scan = instant_parashari.get("forward_event_dasha_scan") or {}
        strong_lines: List[str] = []
        weak_lines: List[str] = []
        for p in (fd_scan.get("periods") or [])[:10]:
            window_prefix = "current window" if str(p.get("time_status") or "").strip().lower() == "current" else "future window"
            line = (
                f"{window_prefix} {p.get('start')}–{p.get('end')}: "
                f"{p.get('mahadasha')}–{p.get('antardasha')}–{p.get('pratyantardasha')} "
                f"(score {p.get('relevance_score')}; houses {p.get('activated_focus_houses')}; {p.get('why', '')})"
            )
            strength = str(p.get("period_strength") or "").strip().lower()
            label = str(p.get("period_label") or "").strip()
            if strength in {"background_weak", "weak"}:
                weak_prefix = label or "background/weak period"
                weak_lines.append(f"{weak_prefix}: {line}")
            else:
                strong_lines.append(line)
        horizon_lines = strong_lines + weak_lines
        for seg in (horizon_dasha_segments.get("segments") or [])[:6]:
            horizon_segment_lines.append(
                f"horizon phase {seg.get('start')}–{seg.get('end')}: "
                f"{seg.get('mahadasha')}-{seg.get('antardasha')}-{seg.get('pratyantardasha')} "
                f"(score {seg.get('relevance_score')}; houses {seg.get('activated_focus_houses')}; {seg.get('why')})"
            )
    primary_drivers = top_supports
    if answer_mode == "timing_window":
        seg_lines: List[str] = []
        for seg in (window_dasha_segments.get("segments") or [])[:4]:
            seg_lines.append(
                f"window segment {seg.get('start')}–{seg.get('end')}: "
                f"{seg.get('mahadasha')}-{seg.get('antardasha')}-{seg.get('pratyantardasha')} "
                f"(score {seg.get('relevance_score')}; houses {seg.get('activated_focus_houses')}; {seg.get('why')})"
            )
        primary_drivers = seg_lines or window_area_lines or top_supports
    elif answer_mode == "event_prediction" and (horizon_lines or horizon_segment_lines):
        primary_drivers = list(top_supports) + horizon_lines[:6] + horizon_segment_lines[:4]
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
            "current_dasha_chain": current_chain,
            "authoritative_current_dasha_display": current_chain_display,
            "authoritative_current_dasha_chain": current_chain,
            "authoritative_current_dasha_fact": authoritative_current_dasha_fact,
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
            "period_kind": period_kind,
            "day_like": period_kind == "day",
            "month_like": period_kind == "window" and period_span_days <= 45,
            "year_like": period_kind == "window" and period_span_days >= 180,
            "use_pd": bool((period_window or {}).get("use_pd")),
            "use_sk_pr": bool((period_window or {}).get("use_sk_pr")),
            "snapshot_warning": "Use fast-planet snapshots only for exact-day or very short windows; for months/years, rely first on dasha segments and slow-planet anchors.",
        },
        "contradiction_flags": contradiction_flags,
        "avoid_drift": contract.get("avoid_drift") or [],
    }
    if answer_mode == "remedy_action":
        try:
            remedy_blueprint = RemedyEngine(
                chart_data=chart_data,
                divisional_charts=chart_data.get("divisional_charts") or {},
            ).build_remedy_blueprint(
                question=question,
                category=category,
                instant_parashari=instant_parashari,
                normalized_evidence=normalized,
                current_dashas_context=current_dashas_context,
                target_chart_context=target_chart_context,
            )
            if isinstance(remedy_blueprint, dict):
                normalized["remedy_blueprint"] = remedy_blueprint
                normalized["question_focus"] = remedy_blueprint.get("question_focus") or normalized.get("question_focus")
                normalized["primary_drivers"] = list(remedy_blueprint.get("candidate_planets") or normalized.get("primary_drivers") or [])
                normalized["top_risks"] = list(remedy_blueprint.get("priority_order") or normalized.get("top_risks") or [])
                normalized["special_points"] = remedy_blueprint.get("special_points") or {}
                normalized["remedy_sections"] = remedy_blueprint.get("remedy_sections") or {}
                normalized["follow_up_prompts"] = remedy_blueprint.get("follow_up_prompts") or []
                normalized["caution"] = remedy_blueprint.get("caution") or ""
        except Exception as exc:
            logger.warning("remedy blueprint build failed: %s", exc)
    if answer_mode == "event_prediction":
        normalized["timing_policy"] = instant_parashari.get("timing_policy") or {}
        normalized["forward_event_dasha_scan"] = instant_parashari.get("forward_event_dasha_scan") or {}
        normalized["horizon_dasha_segments"] = horizon_dasha_segments
        normalized["horizon_transit_anchors"] = instant_parashari.get("horizon_transit_anchors") or {}
    if answer_mode in {"event_prediction", "timing_window"}:
        normalized["window_dasha_segments"] = window_dasha_segments
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
    category = _normalize_event_category(str((intent or {}).get("category") or px.get("cat") or "general"))
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


def _lightweight_event_parashari_evidence(
    *,
    category: str,
    focus_houses: List[int],
    answer_mode: str,
) -> Dict[str, Any]:
    """Minimal event-timing spine; avoids full parallel-agent context builds in speech/instant event timing."""
    cat = _normalize_event_category(category)
    return {
        "source": "event_lightweight",
        "category": cat,
        "focus_houses": list(focus_houses or []),
        "topic_key": PARASHARI_TOPIC_MAP.get(cat),
        "active_dashas": {},
        "active_dashas_formatted": {},
        "house_activation": {},
        "transit_pressure": {},
        "transit_pressure_legend": {},
        "divisional_support": {},
        "topic_signals": {},
        "top_supports": [],
        "top_risks": [],
        "topic_band": "mixed",
        "dominant_houses": [],
        "activation_mechanisms": [],
        "answer_mode": answer_mode,
    }


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
    if answer_mode == "problem_diagnosis":
        primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "risk and activation evidence"
        secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "secondary modifiers"
        avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "generic drift"
        skeleton = str(contract.get("answer_skeleton") or "Main vulnerable target-relative houses -> Exact dasha activation -> Trigger layer if clearly supported -> Why the event or problem became tangible -> Practical handling")
        diagnosis_time_note = ""
        if str(category or "").lower() == "health" and str(time_relation or "").lower() == "past":
            diagnosis_time_note = "This is a past health-event diagnosis. Use restrained evidentiary language like likely vulnerability, likely trigger, or supports injury risk unless the provided evidence is unusually explicit."
        return "\n".join(
            [
                f"This answer uses universal answer mode `{answer_mode}`.",
                "CRITICAL: Follow the method instructions below exactly.",
                "CRITICAL: For diagnosis questions, explain the problem from exact chart mechanisms, not from polished or cinematic storytelling.",
                "CRITICAL: If the target_subject is not self, use the rotated target chart context for houses, dasha houses, and transit pressure. Using the native's direct health frame for a relative is a failed answer.",
                "CRITICAL: Do not say an event was 'caused by' a transit or dasha layer unless the provided evidence clearly supports it. Prefer wording like supports injury, raises vulnerability, or likely trigger.",
                f"Answer skeleton: {skeleton}.",
                f"Primary evidence priority: {primary}.",
                f"Secondary evidence only after primary evidence: {secondary}.",
                f"Avoid these drifts: {avoid}.",
                diagnosis_time_note,
                "- `normalized_evidence.target_subject`: if this is not self, name and follow the target person being analyzed.",
                "- `target_chart_context`: for non-self questions, this is the primary frame for houses, planets, and transits.",
                "- `activation_mechanisms`: use these to show the exact vulnerable houses and why they are activated.",
                "- `active_dashas_formatted`: make the active period lords visible if they materially explain the problem.",
                "- `transit_pressure`: use this only as a sharpening layer, not as a complete explanation by itself.",
                "- `normalized_evidence.risk_specifics`: if you use words like vulnerability, injury, obstruction, or suddenness, tie them to a concrete mechanism from here or from the activation links.",
                "For past health or injury questions, first identify the target-relative vulnerable houses, then show which dasha levels activated them, then mention a trigger layer only if it is clearly supported.",
                "Do not use dramatic phrases like high-intensity, specifically targeted, double-hit, double-activation, perfect storm, final spotlight, karmic knot, wear-and-tear, or physical resilience was at a low point unless the evidence is unusually explicit and you immediately prove it.",
                "Do not treat one house, one transit, or one planet as a complete injury verdict by itself. Show the vulnerability pattern first, then the activation, then only a limited trigger claim if supported.",
                "Do not widen the answer into generic personality or broad fate narrative. Stay with the mechanism of the asked problem.",
            ]
        )
    if answer_mode == "remedy_action":
        primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "remedy blueprint and active pressure"
        secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "supporting modifiers"
        avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "generic remedy dump"
        skeleton = str(contract.get("answer_skeleton") or "Problem focus -> What is most pressing now -> Remedy layers by category -> Special blockage notes -> One caution")
        return "\n".join(
            [
                f"This answer uses universal answer mode `{answer_mode}`.",
                "CRITICAL: Follow the method instructions below exactly.",
                "CRITICAL: This is a remedy-only answer, not a full predictive reading.",
                "CRITICAL: Do not give all astrological schools or a generic upaya list. Build remedies only from the remedy blueprint and the strongest active chart pressure.",
                "CRITICAL: Keep the remedy language practical, layered, and non-dramatic.",
                f"Answer skeleton: {skeleton}.",
                f"Primary evidence priority: {primary}.",
                f"Secondary evidence only after primary evidence: {secondary}.",
                f"Avoid these drifts: {avoid}.",
                "- `normalized_evidence.remedy_blueprint`: this is the main source for what is most pressing now, the priority planet order, special blockages, and the remedy sections.",
                "- `normalized_evidence.remedy_blueprint.remedy_sections`: use these sections to organize the reply. Prefer the strongest 2-4 sections, not every possible remedy layer.",
                "- `normalized_evidence.remedy_blueprint.constructive_house_expression`: this is the biggest remedy layer. Use it first when the user can solve the issue by expressing the planet through a positive house function.",
                "- `normalized_evidence.remedy_blueprint.remedy_sections.gemstones`: surface this when suitable. Keep gemstone advice optional, specific to the strongest planet, and suitability-dependent.",
                "- `normalized_evidence.remedy_blueprint.remedy_sections.biological`: include this as the biological / tree-based remedy layer when available.",
                "- `normalized_evidence.remedy_blueprint.remedy_sections.nakshatra`: include this as a distinct nakshatra remedy layer when available; mention shakti, deity, vriksha, mantra, and the actionable remedy.",
                "- `normalized_evidence.remedy_blueprint.special_points`: use Mudakku, Gandanta, and Mrityu Bhaga only when present. Explain them briefly and precisely.",
                "- `normalized_evidence.remedy_blueprint.follow_up_prompts`: use these to propose the next remedy question, not as a new diagnosis.",
                "- `normalized_evidence.remedy_blueprint.caution`: use this to avoid overcommitting to gemstones or too many remedies at once.",
                "- `normalized_evidence.current_timing` and `active_dashas_formatted`: use these only to identify the planet(s) currently pressing the issue.",
                "- `normalized_evidence.divisional_specifics`: use only if the blueprint actually points there. Do not widen into general astrology.",
                "The user should see a focused remedy card, with the strongest remedy layers first and one clear follow-up question if needed.",
                "Do not turn the answer into a broad horoscope or a long explanation of all planets.",
                "If the user is already positively channeling the planet through study, research, service, teaching, building, or disciplined work, say that directly and treat it as the strongest remedy layer.",
            ]
        )
    if answer_mode == "event_prediction":
        primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "timing policy and dasha horizon"
        secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "secondary modifiers"
        avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "broad drift"
        skeleton = str(
            contract.get("answer_skeleton")
            or "Timing policy -> Verdict with horizon MD/AD -> Mechanisms -> Uncertainty -> Takeaway"
        )
        tp = (normalized_evidence or {}).get("timing_policy") or {}
        restr_list = [str(x) for x in (tp.get("restrictions") or []) if str(x).strip()]
        restr_block = " ".join(restr_list) if restr_list else "No extra age-based restrictions."
        notes_list = [str(x) for x in (tp.get("notes") or []) if str(x).strip()]
        notes_block = " ".join(notes_list) if notes_list else ""
        property_guard_block = ""
        if str(category or "").lower() in {"property", "relocation"}:
            property_guard_block = (
                "Property-specific rule: keep the reading anchored to property houses and support levels first. "
                "Do not automatically translate 8th-house pressure into loans, paperwork, hidden defects, inheritance, or sudden transaction drama "
                "unless those concrete themes are explicitly supported by the provided reasons, topic_signals, or activated focus houses. "
                "If current support is weaker than a later window, say current support is weaker now and stronger later; do not pad that gap with generic "
                "phrases like preparation phase, internal adjustment, or financial restructuring unless the evidence clearly points there."
            )
        fd = (normalized_evidence or {}).get("forward_event_dasha_scan") or {}
        horizon_segments = (normalized_evidence or {}).get("horizon_dasha_segments") or {}
        n_periods = len(fd.get("periods") or [])
        n_horizon_segments = len(horizon_segments.get("segments") or [])
        horizon_end = str(fd.get("horizon_end") or "")
        return "\n".join(
            [
                f"This answer uses universal answer mode `{answer_mode}`.",
                "CRITICAL: Follow the method instructions below exactly.",
                "CRITICAL: Act like an investigator — support, obstruction, and uncertainty before the verdict.",
                "CRITICAL: Use the ranked next ~3-year Vimshottari horizon in `normalized_evidence.forward_event_dasha_scan` together with current activation. Do not answer as if only 'right now' exists unless the horizon list is empty.",
                "CRITICAL: Obey `instant_parashari.timing_policy` as hard rules (especially for children/teens). If restrictions forbid a near-term marriage or similar claim, comply fully.",
                "CRITICAL: Start with the active dasha chain itself. Usually explain MD first, then AD, then PD if relevant. For each one, say what houses it rules, where it sits natally, and whether a conjunction materially modifies it before you jump to the event verdict.",
                "CRITICAL: For asked windows (like a year), use `instant_parashari.window_dasha_segments` phase-by-phase. For open-ended lifetime-style event timing, use `instant_parashari.horizon_dasha_segments` phase-by-phase across the next 3 years. Do not collapse the full horizon into one single dasha pair.",
                "CRITICAL: Score confidence higher when active dasha lords are transiting on or aspecting their natal houses (already encoded in segment scoring and reasons).",
                "CRITICAL: Your response will be marked failed if you mention only the current MD/AD when `forward_event_dasha_scan` or `horizon_dasha_segments` show stronger later AD/PD windows inside the next 3 years.",
                "CRITICAL: Use `normalized_evidence.event_timing_verdict` as the final comparison contract. Its `comparison`, `score_delta`, `answer_rule`, `required_answer_points`, and `forbidden_answer_moves` override your own interpretation of raw scores.",
                "CRITICAL: Window order must match scored clusters in event_timing_verdict. Do not promote a secondary window to #1 on a follow-up unless scores flip; if they flip, say what changed and why.",
                "CRITICAL: Use `normalized_evidence.event_timing_verdict.answer_event_label` to name the asked event plainly in the opening sentence. For example: 'For having a child...' or 'For promotion...'. Do not hide the topic behind vague wording like 'this event' unless the label itself is general.",
                "CRITICAL: If event_timing_verdict says the future is only slightly cleaner/stronger, do not call it clearly superior or overwhelmingly better. If it says current_window exists, acknowledge current activation.",
                "CRITICAL: For career/job timing, separate Activation (calls/effort) vs Offer vs Joining. PD/micro-dasha starts are environment shifts, not delivery SLAs.",
                "CRITICAL: If TIMING_CONTRACT_LOCK is present in the prompt, obey it over narrative improvisation.",
                "CRITICAL: When AD or PD changes across the horizon materially change the event support, mention that shift explicitly instead of smoothing all years into one generic trend.",
                "CRITICAL: If a ranked horizon row is marked `current window`, describe it as already active now or ongoing now. Do not phrase that row as if the same MD/AD/PD combination will start in the future.",
                "CRITICAL: If the current broader MD/AD pair continues into a later stronger sub-phase, say it is the same ongoing MD/AD period with a later shift in PD or support level. Do not describe that later strengthening as if the MD/AD pair itself begins only then.",
                f"Answer skeleton: {skeleton}.",
                f"Primary evidence priority: {primary}.",
                f"Secondary evidence only after primary evidence: {secondary}.",
                f"Avoid these drifts: {avoid}.",
                f"Timing policy: life_stage={tp.get('life_stage', 'unknown')}, age_years={tp.get('age_years', 'unknown')}, event_category={tp.get('event_category', '')}.",
                f"Age-based restrictions: {restr_block}",
                notes_block,
                property_guard_block,
                f"Horizon scan: {n_periods} ranked MD/AD/PD windows through ~{horizon_end} plus {n_horizon_segments} ranked MD/AD/PD phase segments in the next 3 years. Prefer the strongest-ranked windows when discussing when the event is more likely to materialize.",
                "If a horizon row is tagged as `background/weak period`, treat it as lower-priority context and avoid making it the headline timing window unless stronger rows are absent.",
                "CRITICAL: When you mention the CURRENT active dasha chain, read it only from `normalized_evidence.current_timing.active_dashas` (or `current_dasha_chain`). Do NOT infer current MD/AD/PD from `forward_event_dasha_scan` future windows.",
                "CRITICAL: Do not name a current dasha chain unless the exact planets are present in `normalized_evidence.current_timing.active_dashas` or `current_dasha_chain`. Never invent a current MD/AD/PD label from impressionistic reading of risks, houses, or future-window rows.",
                "CRITICAL: Treat `normalized_evidence.current_timing.authoritative_current_dasha_chain` as the source of truth for the current MD/AD/PD names. If any raw `instant_parashari.active_dashas` rows look different, ignore them for naming the current chain; those raw rows are compact activation metadata, not authoritative labels.",
                "CRITICAL: If you mention the current dasha in prose, use `normalized_evidence.current_timing.authoritative_current_dasha_fact` exactly as your naming anchor. Do not mutate it into a repeated single-planet chain like `Rahu-Rahu-Rahu` unless that exact repetition is what the authoritative fact says.",
                "CRITICAL: Do not compress a mixed chain into one repeated planet. For example, if the authoritative current chain is Saturn / Rahu / Saturn, you must not restate it as Rahu-Rahu-Rahu or Saturn-Saturn-Saturn.",
                "CRITICAL: The exact current MD/AD/PD display is `normalized_evidence.current_timing.authoritative_current_dasha_display`. If your answer mentions the current chain, it must preserve the exact planet order from that field. If you are not sure, do not name the current dasha planets at all.",
                "CRITICAL: Keep two lanes separate: current dasha naming comes only from `normalized_evidence.current_timing.authoritative_current_dasha_display`, while future timing windows come only from `forward_event_dasha_scan` and `horizon_dasha_segments`. Do not let future-window planets overwrite the current chain.",
                "- `instant_parashari.horizon_transit_anchors`: optional Jupiter/Saturn sign+house at start and end of the horizon; use as a light confirmation layer, not a replacement for dasha.",
                "- `instant_parashari.window_dasha_segments`: this is the phase timeline for the asked window with MD/AD/PD, activated houses, and reinforcement reasons. Use top segments first.",
                "- `normalized_evidence.horizon_dasha_segments`: this is the ranked next-3-year phase timeline with MD/AD/PD and reinforcement reasons. Use it for open-ended event timing to show where the support strengthens or weakens.",
                "- `normalized_evidence.primary_drivers`: includes compact horizon lines — cite them when you name future windows.",
                "- `normalized_evidence.event_timing_verdict`: this is the backend ruleset synthesis for current-vs-future timing strength. Follow it before raw horizon rows.",
                "- `normalized_evidence.event_timing_verdict.answer_event_label`: use this exact plain-language event label early so the answer is clearly about the user's asked event.",
                "CRITICAL: If `normalized_evidence.divisional_specifics` contains concrete support and divisional mentions are allowed, mention the strongest relevant divisional chart code in the answer for credibility. Keep it compact, for example: 'D10 also supports the career side...' or 'D7 adds support for children...'.",
                "- `activation_mechanisms` and `active_dashas_formatted`: current-period mechanisms; combine with horizon windows (near vs later activation).",
                "- `normalized_evidence.dasha_level_effects`: this is critical. Use it to build explicit astrological reasoning such as 'Mercury rules houses 3 and 12, sits in natal house 8, and is conjunct Ketu, so ...'.",
                "- `normalized_evidence.current_timing.active_dashas`: this is the authoritative source for the current MD/AD/PD planets and their natal metadata, including conjunctions when present.",
                "- `topic_signals`: topic-specific Parashari summary for the event category.",
                "For event-prediction answers, do not jump to 'yes' just because relevant houses are active. Activation can mean pressure, preparation, or delay.",
                "Do not convert a generic 8th-house, dusthana, or pressure signal into a specific story like paperwork trouble, loan restructuring, legal blocks, or sudden cancellation unless that concrete angle is supported by the provided reasons, topic_signals, or activated focus houses.",
                "If forward_event_dasha_scan.periods is empty, say horizon scan was thin and lean on current dasha plus divisional/topic signals without inventing dated sub-periods.",
                "Do not invent calendar dates or months beyond what the ranked periods and current evidence can support.",
                "Avoid vague filler such as 'preparation phase', 'internal adjustment', or 'energy is shifting'. If current support is weaker than a later window, name the exact dasha reason, house link, conjunction, or transit reason from the evidence.",
                "Keep the answer concise: usually 2–5 short paragraphs for instant mode.",
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
            "If `normalized_evidence.window_rules.day_like` is true, answer as an exact-day outlook: name the date/window, use MD/AD/PD plus Sookshma/Prana when present, and keep fast transits limited to that day.",
            "If `normalized_evidence.window_rules.year_like` is true, answer as an annual outlook: use phase-wise `window_dasha_segments`, mention stronger/weaker parts of the year, and do not narrate the year from a single transit snapshot.",
            "- `normalized_evidence.contradiction_flags`: if present, explicitly balance the answer instead of sounding absolute.",
            "- `active_dashas`: this is compact activation metadata. Use it for mechanism support only. Do not treat it as the authoritative source for the current MD/AD/PD names when `normalized_evidence.current_timing.active_dashas` or `authoritative_current_dasha_chain` is present.",
            "- `house_activation`: this shows whether the important houses are being activated by rulership, occupation, or aspect from active dasha lords. This should drive the core interpretation.",
            "For timing/window answers, first identify what each active lord is activating through natal residence, rulership, transit position, and active aspects. Then combine the house themes that repeat across MD/AD/PD and, when enabled, Sookshma/Prana. Only after that should you synthesize the prediction.",
            "For asked windows (for example a year), use `normalized_evidence.window_dasha_segments` to describe phase changes across the window; do not answer from a single static dasha pair.",
            "Increase confidence for house activation claims only when a segment reason explicitly shows dasha-lord transit reinforcement (transiting on/aspecting its natal house).",
            "If PD or Sookshma is enabled for this asked period, treat it as critical evidence. Do not collapse the answer into only Mahadasha and Antardasha language.",
            "For timing/window answers, surface the dasha chain explicitly in the answer. Do not hide MD/AD/PD and Sookshma/Prana behind generic summary prose.",
            "CRITICAL: If the `window_dasha_segments` show a change in Pratyantardasha (PD) or Antardasha (AD) within the asked period, you MUST mention when this transition happens and how the focus shifts.",
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


def _fmt_dt_date(value: Any) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value or "")


def _dasha_timeline_needs_from_plan(evidence_plan: Any) -> List[Dict[str, Any]]:
    if not isinstance(evidence_plan, dict):
        return []
    needs = evidence_plan.get("evidence_needs")
    if not isinstance(needs, list):
        return []
    return [
        need
        for need in needs
        if isinstance(need, dict)
        and str(need.get("kind") or "") == "dasha_timeline_lookup"
    ]


def _build_named_dasha_lookup_from_evidence_plan(
    *,
    evidence_plan: Any,
    current_dashas: Dict[str, Any],
    as_of: datetime,
) -> Dict[str, Any]:
    timeline_needs = _dasha_timeline_needs_from_plan(evidence_plan)
    if not timeline_needs:
        return {}

    maha_dashas = list((current_dashas or {}).get("maha_dashas") or [])
    requested_planets: List[str] = []
    requested_levels: List[str] = []
    matches: List[Dict[str, Any]] = []

    for need in timeline_needs:
        params = need.get("params") if isinstance(need.get("params"), dict) else {}
        planet = str(params.get("planet") or "").strip()
        level = str(params.get("level") or "mahadasha").strip().lower()
        operation = str(params.get("operation") or "find_start_end").strip()
        if not planet or level != "mahadasha" or operation not in {"get_current", "find_start_end", "find_next", "list_periods"}:
            continue
        if planet not in requested_planets:
            requested_planets.append(planet)
        if level not in requested_levels:
            requested_levels.append(level)
        if maha_dashas:
            current_match = None
            future_match = None
            for row in maha_dashas:
                if not isinstance(row, dict) or str(row.get("planet") or "") != planet:
                    continue
                start = row.get("start")
                end = row.get("end")
                if isinstance(start, datetime) and isinstance(end, datetime) and start <= as_of <= end:
                    current_match = row
                    break
                if isinstance(start, datetime) and start > as_of:
                    if future_match is None or start < future_match.get("start"):
                        future_match = row
            row = current_match or future_match
            if row:
                relation = "current" if row is current_match else "future"
                matches.append(
                    {
                        "level": "mahadasha",
                        "planet": planet,
                        "relation_to_as_of": relation,
                        "start": _fmt_dt_date(row.get("start")),
                        "end": _fmt_dt_date(row.get("end")),
                        "years": row.get("years"),
                        "authoritative_fact": (
                            f"{planet} Mahadasha {'started' if relation == 'current' else 'starts'} "
                            f"on {_fmt_dt_date(row.get('start'))} and ends on {_fmt_dt_date(row.get('end'))}."
                        ),
                    }
                )

    if not matches:
        return {}
    return {
        "source": "shared_dasha_calculator.maha_dashas",
        "planner_source": "evidence_plan.dasha_timeline_lookup",
        "as_of": _fmt_dt_date(as_of),
        "requested_planets": requested_planets,
        "requested_levels": requested_levels,
        "matches": matches,
        "instruction": "For named dasha start/date questions, treat matches[].authoritative_fact as exact. Do not infer or substitute a transit/event window date.",
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

    category = _normalize_event_category(str((intent or {}).get("category") or "general"))
    focus = CATEGORY_FOCUS.get(category, CATEGORY_FOCUS["general"])
    focus_planets = set(focus["planets"]) | {"Moon"}

    query_context = (intent or {}).get("query_context") if isinstance((intent or {}).get("query_context"), dict) else None
    extracted_context = (intent or {}).get("extracted_context") if isinstance((intent or {}).get("extracted_context"), dict) else {}
    now_local = resolve_query_now(query_context)
    period_window = _resolve_period_window(intent, now_local, question)
    time_relation = _period_time_relation(period_window, now_local)
    dasha_anchor = _as_naive_local_datetime(_period_anchor_datetime(period_window, now_local))
    dasha_calc = DashaCalculator()
    current_dashas = dasha_calc.calculate_current_dashas(birth_data, dasha_anchor)
    evidence_plan = (intent or {}).get("evidence_plan") if isinstance((intent or {}).get("evidence_plan"), dict) else {}
    named_dasha_lookup = _build_named_dasha_lookup_from_evidence_plan(
        evidence_plan=evidence_plan,
        current_dashas=current_dashas,
        as_of=dasha_anchor,
    )
    authoritative_dasha_context: Dict[str, Any] = {}
    dasha_calc_fallback = _is_dasha_calculator_fallback_payload(current_dashas)
    dasha_payload_untrusted = bool(dasha_calc_fallback)
    if not dasha_calc_fallback:
        authoritative_dasha_context = _authoritative_active_dasha_context(
            current_dashas,
            chart_data,
            house_lordships,
            period_window,
        )
    else:
        logger.warning(
            "DashaCalculator fallback payload detected for instant context; trying standard chat current dasha path."
        )
        standard_current_dashas = _standard_chat_current_dashas(birth_data, chart_data, house_lordships)
        if standard_current_dashas and not _is_dasha_calculator_fallback_payload(standard_current_dashas):
            current_dashas = standard_current_dashas
            dasha_calc_fallback = False
            authoritative_dasha_context = _authoritative_active_dasha_context(
                current_dashas,
                chart_data,
                house_lordships,
                period_window,
            )
            logger.info(
                "SPEECH_DEBUG instant_dasha_standard_fallback md=%s ad=%s pd=%s",
                ((current_dashas.get("mahadasha") or {}).get("planet") or ""),
                ((current_dashas.get("antardasha") or {}).get("planet") or ""),
                ((current_dashas.get("pratyantardasha") or {}).get("planet") or ""),
            )
        else:
            logger.warning(
                "Standard chat current dasha fallback unavailable for instant context; current dasha names will be omitted."
            )
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
    authoritative_event_prediction_dashas: Dict[str, Any] = {}
    if answer_mode == "event_prediction" and not dasha_calc_fallback:
        forced_period_window = dict(period_window or {})
        forced_period_window["use_pd"] = True
        authoritative_event_prediction_dashas = _authoritative_active_dasha_context(
            current_dashas,
            chart_data,
            house_lordships,
            forced_period_window,
        )
    if answer_mode == "event_prediction":
        instant_parashari = _lightweight_event_parashari_evidence(
            category=category,
            focus_houses=list(focus["houses"]),
            answer_mode=answer_mode,
        )
    else:
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
    if dasha_payload_untrusted:
        for key in (
            "active_dashas",
            "active_dashas_formatted",
            "house_activation",
            "activation_mechanisms",
            "dominant_houses",
            "top_supports",
            "top_risks",
        ):
            if key in {"top_supports", "top_risks", "dominant_houses", "activation_mechanisms"}:
                instant_parashari[key] = []
            else:
                instant_parashari[key] = {}
    
    # Refine category and focus from what the compact evidence found (px.get("cat"))
    category = instant_parashari.get("category") or category
    focus = CATEGORY_FOCUS.get(category, CATEGORY_FOCUS["general"])
    
    if answer_mode == "event_prediction" and authoritative_event_prediction_dashas:
        instant_parashari["active_dashas_formatted"] = authoritative_event_prediction_dashas
        instant_parashari["active_dasha_source"] = "dasha_calculator_authoritative_event_prediction"
    elif authoritative_dasha_context:
        instant_parashari["active_dashas_formatted"] = authoritative_dasha_context
        instant_parashari["active_dasha_source"] = "dasha_calculator_authoritative"
    elif dasha_calc_fallback:
        instant_parashari["active_dashas_formatted"] = {}
        instant_parashari["active_dasha_source"] = "unavailable"
    instant_parashari["active_dashas_formatted"] = _enrich_active_dasha_context_with_conjunctions(
        instant_parashari.get("active_dashas_formatted") or {},
        chart_data,
    )
    instant_parashari["period_window"] = period_window
    instant_parashari["time_relation"] = time_relation

    birth_dt_for_age = _parse_birth_date_only(birth_data)
    age_years = _compute_age_years(birth_dt_for_age, now_local)
    life_stage = _life_stage_from_age(age_years)
    if answer_mode == "event_prediction":
        instant_parashari["timing_policy"] = _timing_policy_for_instant_event(
            age_years=age_years,
            life_stage=life_stage,
            category=category,
        )
        event_horizon_raw_periods: Optional[List[Dict[str, Any]]] = None
        event_horizon_start = datetime.utcnow()
        try:
            event_horizon_raw_periods = dasha_calc.get_dasha_periods_for_range(
                birth_data,
                _as_naive_local_datetime(now_local),
                _as_naive_local_datetime(now_local + timedelta(days=_INSTANT_EVENT_HORIZON_DAYS)),
            )
            logger.info(
                "SPEECH_PERF event_horizon_dasha_periods rows=%s elapsed_ms=%s",
                len(event_horizon_raw_periods or []),
                round((datetime.utcnow() - event_horizon_start).total_seconds() * 1000, 1),
            )
        except Exception as exc:
            logger.warning("event horizon dasha period prebuild failed: %s", exc)
        instant_parashari["forward_event_dasha_scan"] = _build_forward_event_dasha_scan(
            birth_data=birth_data,
            now_local=now_local,
            house_lordships=dict(house_lordships),
            focus_houses=list(focus["houses"]),
            category=category,
            chart_data=chart_data,
            transit_calc=transit_calc,
            ascendant_longitude=ascendant_longitude,
            current_dashas=current_dashas,
            raw_periods=event_horizon_raw_periods,
        )
        instant_parashari["horizon_transit_anchors"] = _horizon_jupiter_saturn_anchors(
            transit_calc,
            ascendant_longitude,
            now_local,
            now_local + timedelta(days=_INSTANT_EVENT_HORIZON_DAYS),
        )
        instant_parashari["horizon_dasha_segments"] = _horizon_dasha_segments_for_event(
            birth_data=birth_data,
            chart_data=chart_data,
            house_lordships=house_lordships,
            now_local=now_local,
            focus_houses=list(focus["houses"]),
            transit_calc=transit_calc,
            ascendant_longitude=ascendant_longitude,
            category=category,
            raw_periods=event_horizon_raw_periods,
        )
    if str((period_window or {}).get("kind") or "") in {"day", "window"}:
        instant_parashari["window_dasha_segments"] = _window_dasha_segments_for_period(
            birth_data=birth_data,
            chart_data=chart_data,
            house_lordships=house_lordships,
            period_window=period_window,
            focus_houses=list(focus["houses"]),
            transit_calc=transit_calc,
            ascendant_longitude=ascendant_longitude,
            category=category,
        )

    current_dashas_context = instant_parashari.get("active_dashas_formatted") or {}
    try:
        logger.info(
            "SPEECH_DEBUG instant_dasha_context answer_mode=%s category=%s source=%s dasha_anchor=%s active_source=%s authoritative_md=%s authoritative_ad=%s authoritative_pd=%s birth=%s %s %s",
            answer_mode,
            category,
            instant_parashari.get("source"),
            dasha_anchor.strftime("%Y-%m-%d %H:%M:%S"),
            instant_parashari.get("active_dasha_source"),
            ((current_dashas_context.get("md") or {}).get("planet") or ""),
            ((current_dashas_context.get("ad") or {}).get("planet") or ""),
            ((current_dashas_context.get("pd") or {}).get("planet") or ""),
            birth_data.get("date"),
            birth_data.get("time"),
            birth_data.get("timezone"),
        )
    except Exception:
        pass
    if answer_mode == "event_prediction":
        event_divisional = _requested_event_divisional_support(
            birth_data=birth_data,
            question=question,
            intent=intent,
            category=category,
            focus_houses=list(focus["houses"]),
            current_dashas_context=current_dashas_context,
        )
        if event_divisional.get("divisional_support"):
            instant_parashari["divisional_support"] = event_divisional["divisional_support"]
        if event_divisional.get("navamsa_root_fruit"):
            instant_parashari["navamsa_root_fruit"] = event_divisional["navamsa_root_fruit"]
    current_transits_context = _format_transit_context(transit_rows)
    target_chart_context = _build_target_chart_context(
        birth_summary,
        natal_snapshot,
        current_transits_context,
        target_subject,
    )
    target_birth_summary = _target_context_as_birth_summary(target_chart_context)
    is_non_self_target = str((target_subject or {}).get("key") or "self") != "self"
    evidence_birth_summary = birth_summary
    evidence_natal_snapshot = natal_snapshot
    evidence_current_transits_context = current_transits_context
    evidence_current_dashas_context = current_dashas_context
    evidence_instant_parashari = instant_parashari
    if is_non_self_target:
        evidence_birth_summary = {
            **target_birth_summary,
            "name": str((target_subject or {}).get("label") or "target person"),
            "source": "rotated_target_context",
        }
        evidence_natal_snapshot = _target_context_as_natal_snapshot(target_chart_context)
        evidence_current_transits_context = dict(target_chart_context.get("target_transits") or {})
        evidence_instant_parashari = _rotate_instant_parashari_for_target(
            instant_parashari,
            target_chart_context,
            focus["houses"],
        )
        evidence_current_dashas_context = evidence_instant_parashari.get("active_dashas_formatted") or {}
    normalized_evidence = _normalize_instant_evidence(
        answer_mode=evidence_instant_parashari.get("answer_mode") or "topic_reading",
        category=category,
        instant_parashari=evidence_instant_parashari,
        current_transits_formatted=evidence_current_transits_context,
        current_dashas_context=evidence_current_dashas_context,
        birth_summary=evidence_birth_summary,
        natal_snapshot=evidence_natal_snapshot,
        relationship_target=target_subject,
        target_chart_context=target_chart_context,
    )
    final_event_prediction_dashas: Dict[str, Any] = {}
    if answer_mode == "event_prediction":
        if dasha_calc_fallback:
            logger.warning(
                "Skipping authoritative current dasha naming for instant event prediction because shared DashaCalculator returned fallback payload."
            )
        else:
            forced_period_window = dict(period_window or {})
            forced_period_window["use_pd"] = True
            final_event_prediction_dashas = _authoritative_active_dasha_context(
                current_dashas,
                chart_data,
                house_lordships,
                forced_period_window,
            ) or authoritative_event_prediction_dashas

    if answer_mode == "event_prediction" and final_event_prediction_dashas:
        _override_current_timing_with_authoritative_dashas(
            normalized_evidence=normalized_evidence,
            active_dashas_context=final_event_prediction_dashas,
            period_window=period_window,
        )
        current_dashas["md"] = dict(final_event_prediction_dashas.get("md") or {})
        current_dashas["ad"] = dict(final_event_prediction_dashas.get("ad") or {})
        current_dashas["pd"] = dict(final_event_prediction_dashas.get("pd") or {})
    elif answer_mode == "event_prediction":
        current_timing = dict((normalized_evidence or {}).get("current_timing") or {})
        current_timing["active_dashas"] = {}
        current_timing["current_dasha_chain"] = ""
        current_timing["authoritative_current_dasha_display"] = ""
        current_timing["authoritative_current_dasha_chain"] = ""
        current_timing["authoritative_current_dasha_fact"] = ""
        current_timing["period_window"] = period_window
        normalized_evidence["current_timing"] = current_timing

    if answer_mode == "event_prediction":
        return _slim_event_prediction_payload(
            birth_summary=evidence_birth_summary,
            natal_snapshot=evidence_natal_snapshot,
            target_chart_context=target_chart_context,
            current_dashas_levels=final_event_prediction_dashas,
            current_transits_formatted=evidence_current_transits_context,
            instant_parashari=evidence_instant_parashari,
            normalized_evidence=normalized_evidence,
            period_window=period_window,
            category=category,
            question=question,
            chart_data=chart_data,
            house_lordships=house_lordships,
            named_dasha_lookup=named_dasha_lookup,
            evidence_plan=evidence_plan,
        )

    is_general_month_window = (
        str((intent or {}).get("mode") or "").upper() == "PREDICT_PERIOD_OUTLOOK"
        and str(category or "").lower() in {"general", "timing"}
        and str((period_window or {}).get("kind") or "") == "window"
    )
    prompt_transits_context = dict(evidence_current_transits_context)
    prompt_current_transits = {
        "as_of_local": transit_anchor.strftime("%Y-%m-%d %H:%M"),
        "planets": dict(evidence_current_transits_context),
    }
    prompt_instant_parashari = dict(evidence_instant_parashari)
    prompt_normalized_evidence = dict(normalized_evidence)
    prompt_current_dashas_levels = evidence_current_dashas_context if is_non_self_target else current_dashas_context
    if answer_mode == "event_prediction" and authoritative_event_prediction_dashas:
        prompt_current_dashas_levels = authoritative_event_prediction_dashas
        prompt_instant_parashari = dict(prompt_instant_parashari)
        prompt_instant_parashari["active_dashas_formatted"] = authoritative_event_prediction_dashas
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
    if answer_mode == "event_prediction":
        prompt_instant_parashari = dict(prompt_instant_parashari)
        prompt_instant_parashari.pop("active_dashas", None)
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
        birth_summary = evidence_birth_summary
        recent_history = recent_history[-1:]
    if answer_mode == "remedy_action":
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
                "top_risks",
                "top_supports",
                "active_dashas_formatted",
                "remedy_blueprint",
            }
        }
        prompt_normalized_evidence = {
            k: v
            for k, v in prompt_normalized_evidence.items()
            if k in {
                "answer_mode_contract",
                "primary_drivers",
                "secondary_modifiers",
                "target_subject",
                "target_chart_context",
                "divisional_specifics",
                "claim_gates",
                "avoid_drift",
                "remedy_blueprint",
                "question_focus",
                "special_points",
                "remedy_sections",
                "follow_up_prompts",
                "caution",
                "current_timing",
                "topic_confirmation",
            }
        }
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
    if answer_mode != "remedy_action" and not claim_gates.get("allow_abstract_risk_labels"):
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

    session_extracted = (intent or {}).get("_session_extracted_context")
    if not isinstance(session_extracted, dict):
        session_extracted = (intent or {}).get("extracted_context") if isinstance((intent or {}).get("extracted_context"), dict) else {}

    return {
        "birth_summary": evidence_birth_summary if is_non_self_target else birth_summary,
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
        "session_extracted_context": session_extracted if isinstance(session_extracted, dict) else {},
        "evidence_plan": evidence_plan,
        "natal_snapshot": evidence_natal_snapshot if is_non_self_target else natal_snapshot,
        "target_chart_context": target_chart_context,
        "current_dashas": {
            "as_of": dasha_anchor.strftime("%Y-%m-%d"),
            "levels": prompt_current_dashas_levels,
            "named_dasha_lookup": named_dasha_lookup,
        },
        "current_transits": prompt_current_transits,
        "current_transits_formatted": prompt_transits_context,
        "instant_parashari": prompt_instant_parashari,
        "normalized_evidence": prompt_normalized_evidence,
        "recent_history": recent_history,
        "complexity_hint": complexity_hint,
        "named_dasha_lookup": named_dasha_lookup,
    }


_FOLLOW_UPS_START = "###FOLLOW_UPS_START###"
_FOLLOW_UPS_END = "###FOLLOW_UPS_END###"


def _parse_speech_followups_from_answer(raw: str) -> tuple[str, List[str]]:
    """Strip structured follow-up JSON from model output; return (answer_text, followups)."""
    text = (raw or "").strip()
    if _FOLLOW_UPS_START not in text:
        return text, []
    before, _, rest = text.partition(_FOLLOW_UPS_START)
    inner, _, _after = rest.partition(_FOLLOW_UPS_END)
    answer = (before or "").strip()
    inner = (inner or "").strip()
    if not inner:
        return answer, []
    if inner.startswith("```"):
        inner = re.sub(r"^```(?:json)?\s*", "", inner, flags=re.IGNORECASE).strip()
        inner = re.sub(r"\s*```$", "", inner).strip()
    try:
        data = json.loads(inner)
    except (json.JSONDecodeError, TypeError):
        return answer, []
    if not isinstance(data, list):
        return answer, []
    out: List[str] = []
    for item in data[:3]:
        s = str(item or "").strip()
        if not s:
            continue
        s = " ".join(s.split())
        if len(s) > 160:
            s = f"{s[:157].rstrip()}..."
        out.append(s)
    return answer, out


def _strip_speech_answer_greeting(text: str) -> str:
    """Speech chat already greets the user before the answer; remove model re-introductions."""
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(
        r"^\s*(?:hello|hi|hey|namaste|नमस्ते|नमस्कार)\s+[^,.!?।]{1,40}[,.!?।]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"^\s*(?:hello|hi|hey|namaste|नमस्ते|नमस्कार)[,.!?।]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"^\s*(?:i\s*(?:am|'m)\s+tara|this\s+is\s+tara|मैं\s+तारा\s+हूँ)[,.!?।]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned or str(text or "").strip()


def _json_size(value: Any) -> int:
    try:
        return len(json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":")))
    except Exception:
        return 0


def _only_keys(value: Any, keys: set[str]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {k: value.get(k) for k in keys if k in value and value.get(k) not in (None, "", [], {})}


def _compact_topic_signals(topic_signals: Any, focus_houses: List[int]) -> Dict[str, Any]:
    if not isinstance(topic_signals, dict):
        return {}
    out = _only_keys(
        topic_signals,
        {"score", "tone", "pattern", "risk", "body", "charak", "charak_agent", "dom", "hs", "dv", "yg"},
    )
    hh = topic_signals.get("hh") if isinstance(topic_signals.get("hh"), dict) else {}
    if hh:
        keep_houses = {str(h) for h in (focus_houses or [])}
        keep_houses.update(str(h) for h in (topic_signals.get("dom") or [])[:3])
        out["hh"] = {
            k: _only_keys(v, {"sc", "cg", "txt"})
            for k, v in hh.items()
            if str(k) in keep_houses and isinstance(v, dict)
        }
    if isinstance(out.get("body"), list):
        out["body"] = out["body"][:4]
    return out


def _compact_divisional_support(divisional_support: Any) -> Dict[str, Any]:
    if not isinstance(divisional_support, dict):
        return {}
    out: Dict[str, Any] = {}
    if divisional_support.get("requested_charts"):
        out["requested_charts"] = list(divisional_support.get("requested_charts") or [])[:8]
    if divisional_support.get("available_charts"):
        out["available_charts"] = list(divisional_support.get("available_charts") or [])[:8]
    if divisional_support.get("skipped_charts"):
        out["skipped_charts"] = list(divisional_support.get("skipped_charts") or [])[:8]
    for bucket_name in ("topic", "current_topic"):
        bucket = divisional_support.get(bucket_name)
        if not isinstance(bucket, dict):
            continue
        charts_out: Dict[str, Any] = {}
        charts = bucket.get("charts") if isinstance(bucket.get("charts"), dict) else {}
        for code, chart in charts.items():
            if not isinstance(chart, dict):
                continue
            charts_out[str(code)] = {
                "support": chart.get("support"),
                "best": list(chart.get("best") or [])[:3],
                "hard": list(chart.get("hard") or [])[:3],
                "rows": list(chart.get("rows") or [])[:3],
            }
        out[bucket_name] = {
            "support": bucket.get("support"),
            "codes": bucket.get("codes"),
            "charts": charts_out,
        }
    return out


def _compact_window_segments(window_segments: Any, as_of: str, *, limit: int = 6) -> Dict[str, Any]:
    if not isinstance(window_segments, dict):
        return {}
    segments = [s for s in (window_segments.get("segments") or []) if isinstance(s, dict)]
    if not segments:
        return _only_keys(window_segments, {"enabled", "label", "focus_houses"})
    selected: List[Dict[str, Any]] = []
    as_of_dt = _parse_ymd(as_of)

    def add(seg: Dict[str, Any]) -> None:
        key = (seg.get("start"), seg.get("end"), seg.get("mahadasha"), seg.get("antardasha"), seg.get("pratyantardasha"))
        for existing in selected:
            existing_key = (
                existing.get("start"),
                existing.get("end"),
                existing.get("mahadasha"),
                existing.get("antardasha"),
                existing.get("pratyantardasha"),
            )
            if existing_key == key:
                return
        selected.append(
            {
                "start": seg.get("start"),
                "end": seg.get("end"),
                "mahadasha": seg.get("mahadasha"),
                "antardasha": seg.get("antardasha"),
                "pratyantardasha": seg.get("pratyantardasha"),
                "relevance_score": seg.get("relevance_score"),
                "activated_focus_houses": seg.get("activated_focus_houses"),
                "why": seg.get("why"),
            }
        )

    if as_of_dt:
        for seg in segments:
            st = _parse_ymd(seg.get("start"))
            en = _parse_ymd(seg.get("end"))
            if st and en and st <= as_of_dt <= en:
                add(seg)
                break
        for seg in segments:
            st = _parse_ymd(seg.get("start"))
            if st and st > as_of_dt:
                add(seg)
                break
    for seg in sorted(
        segments,
        key=lambda row: (-(float(row.get("relevance_score") or 0)), str(row.get("start") or "")),
    ):
        add(seg)
        if len(selected) >= limit:
            break
    return {
        "enabled": bool(window_segments.get("enabled")),
        "label": window_segments.get("label"),
        "focus_houses": window_segments.get("focus_houses"),
        "segments": selected[:limit],
    }


def _compact_forward_event_scan(scan: Any, *, limit: int = 6) -> Dict[str, Any]:
    if not isinstance(scan, dict):
        return {}
    periods = [p for p in (scan.get("periods") or []) if isinstance(p, dict)]
    compact_periods = [
        {
            "start": row.get("start"),
            "end": row.get("end"),
            "mahadasha": row.get("mahadasha"),
            "antardasha": row.get("antardasha"),
            "pratyantardasha": row.get("pratyantardasha"),
            "relevance_score": row.get("relevance_score"),
            "period_strength": row.get("period_strength"),
            "period_label": row.get("period_label"),
            "time_status": row.get("time_status"),
            "activated_focus_houses": row.get("activated_focus_houses"),
            "why": row.get("why"),
        }
        for row in periods[:limit]
    ]
    return {
        "horizon_days": scan.get("horizon_days"),
        "horizon_end": scan.get("horizon_end"),
        "focus_houses": scan.get("focus_houses"),
        "periods": compact_periods,
    }


def _compact_planet_map(planets: Any, keep_planets: set[str]) -> Dict[str, Any]:
    if not isinstance(planets, dict):
        return {}
    out: Dict[str, Any] = {}
    for planet, row in planets.items():
        if keep_planets and str(planet) not in keep_planets:
            continue
        if isinstance(row, dict):
            out[str(planet)] = _only_keys(
                row,
                {
                    "sign",
                    "house",
                    "house_from_lagna",
                    "house_from_target",
                    "native_house",
                    "degree",
                    "retrograde",
                    "nakshatra",
                },
            )
    return out


def _compact_context_for_speech(instant_context: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(instant_context, dict):
        return {}
    intent_summary = dict(instant_context.get("intent_summary") or {})
    current_dashas = dict(instant_context.get("current_dashas") or {})
    named_dasha_lookup = (
        instant_context.get("named_dasha_lookup")
        if isinstance(instant_context.get("named_dasha_lookup"), dict)
        else current_dashas.get("named_dasha_lookup")
        if isinstance(current_dashas.get("named_dasha_lookup"), dict)
        else {}
    )
    dasha_levels = current_dashas.get("levels") if isinstance(current_dashas.get("levels"), dict) else {}
    active_planets = {
        str((row or {}).get("planet"))
        for row in (dasha_levels or {}).values()
        if isinstance(row, dict) and row.get("planet")
    }
    focus_planets = {str(p) for p in (intent_summary.get("focus_planets") or []) if p}
    focus_planets.update(str(p) for p in (named_dasha_lookup.get("requested_planets") or []) if p)
    keep_planets = active_planets | focus_planets | {"Jupiter", "Saturn", "Rahu", "Ketu"}
    focus_houses = list(intent_summary.get("focus_houses") or [])
    normalized = instant_context.get("normalized_evidence") if isinstance(instant_context.get("normalized_evidence"), dict) else {}
    parashari = instant_context.get("instant_parashari") if isinstance(instant_context.get("instant_parashari"), dict) else {}
    target_ctx = instant_context.get("target_chart_context") if isinstance(instant_context.get("target_chart_context"), dict) else {}
    is_self_target = str((intent_summary.get("target_subject") or {}).get("key") or target_ctx.get("key") or "self") == "self"

    topic_confirmation = dict(normalized.get("topic_confirmation") or {})
    topic_signals = topic_confirmation.get("topic_signals") if isinstance(topic_confirmation.get("topic_signals"), dict) else {}
    topic_confirmation["topic_signals"] = _compact_topic_signals(topic_signals, focus_houses)

    stable_transits = normalized.get("stable_transits") or {}
    if not stable_transits:
        stable_transits = (instant_context.get("current_transits") or {}).get("planets") if isinstance(instant_context.get("current_transits"), dict) else {}

    compact_normalized = {
        "answer_mode_contract": normalized.get("answer_mode_contract"),
        "primary_drivers": list(normalized.get("primary_drivers") or [])[:5],
        "secondary_modifiers": list(normalized.get("secondary_modifiers") or [])[:4],
        "current_timing": normalized.get("current_timing"),
        "event_timing_verdict": normalized.get("event_timing_verdict"),
        "named_dasha_lookup": named_dasha_lookup or normalized.get("named_dasha_lookup"),
        "dasha_level_effects": list(normalized.get("dasha_level_effects") or [])[:5],
        "dasha_chain_synthesis": list(normalized.get("dasha_chain_synthesis") or [])[:4],
        "active_areas": list(normalized.get("active_areas") or [])[:4],
        "window_area_mechanisms": list(normalized.get("window_area_mechanisms") or [])[:4],
        "topic_confirmation": topic_confirmation,
        "divisional_specifics": list(normalized.get("divisional_specifics") or [])[:3],
        "risk_specifics": list(normalized.get("risk_specifics") or [])[:3],
        "stable_transits": _compact_planet_map(stable_transits, keep_planets),
        "claim_gates": normalized.get("claim_gates"),
        "window_rules": normalized.get("window_rules"),
        "contradiction_flags": list(normalized.get("contradiction_flags") or [])[:3],
        "avoid_drift": list(normalized.get("avoid_drift") or [])[:4],
        "window_dasha_segments": _compact_window_segments(
            normalized.get("window_dasha_segments") or parashari.get("window_dasha_segments"),
            str(current_dashas.get("as_of") or ""),
        ),
        "forward_event_dasha_scan": _compact_forward_event_scan(
            normalized.get("forward_event_dasha_scan") or parashari.get("forward_event_dasha_scan"),
        ),
        "horizon_dasha_segments": _compact_window_segments(
            normalized.get("horizon_dasha_segments") or parashari.get("horizon_dasha_segments"),
            str(current_dashas.get("as_of") or ""),
        ),
        "target_subject": normalized.get("target_subject") or intent_summary.get("target_subject"),
    }
    compact_normalized = {k: v for k, v in compact_normalized.items() if v not in (None, "", [], {})}

    compact_parashari = {
        "source": parashari.get("source"),
        "category": parashari.get("category"),
        "topic_key": parashari.get("topic_key"),
        "divisional_support": _compact_divisional_support(parashari.get("divisional_support")),
        "answer_mode": parashari.get("answer_mode"),
        "period_window": parashari.get("period_window"),
        "time_relation": parashari.get("time_relation"),
        "focus_houses": parashari.get("focus_houses"),
        "active_dasha_source": parashari.get("active_dasha_source"),
        "active_dashas_formatted": parashari.get("active_dashas_formatted"),
        "named_dasha_lookup": named_dasha_lookup or parashari.get("named_dasha_lookup"),
        "activation_mechanisms": list(parashari.get("activation_mechanisms") or [])[:4],
        "top_supports": list(parashari.get("top_supports") or [])[:4],
        "top_risks": list(parashari.get("top_risks") or [])[:2],
        "dominant_houses": list(parashari.get("dominant_houses") or [])[:3],
        "topic_band": parashari.get("topic_band"),
        "horizon_transit_anchors": parashari.get("horizon_transit_anchors"),
    }
    compact_parashari = {k: v for k, v in compact_parashari.items() if v not in (None, "", [], {})}

    natal_snapshot = instant_context.get("natal_snapshot") if isinstance(instant_context.get("natal_snapshot"), dict) else {}
    key_planets = natal_snapshot.get("key_planets") if isinstance(natal_snapshot.get("key_planets"), dict) else {}
    compact_natal = {
        "house_lordships": natal_snapshot.get("house_lordships"),
        "key_planets": _compact_planet_map(key_planets, keep_planets),
    }
    compact_natal = {k: v for k, v in compact_natal.items() if v not in (None, "", [], {})}

    compact_target = {
        "key": target_ctx.get("key"),
        "label": target_ctx.get("label"),
        "anchor_house": target_ctx.get("anchor_house"),
        "target_ascendant_sign": target_ctx.get("target_ascendant_sign"),
        "target_house_lordships": target_ctx.get("target_house_lordships"),
    }
    if not is_self_target:
        compact_target["target_key_planets"] = _compact_planet_map(target_ctx.get("target_key_planets") or {}, keep_planets)
        compact_target["target_transits"] = _compact_planet_map(target_ctx.get("target_transits") or {}, keep_planets)
    compact_target = {k: v for k, v in compact_target.items() if v not in (None, "", [], {})}

    compact_transits = {
        "as_of_local": (instant_context.get("current_transits") or {}).get("as_of_local")
        if isinstance(instant_context.get("current_transits"), dict)
        else None,
        "planets": _compact_planet_map(
            (instant_context.get("current_transits") or {}).get("planets")
            if isinstance(instant_context.get("current_transits"), dict)
            else {},
            keep_planets,
        ),
    }
    compact_transits = {k: v for k, v in compact_transits.items() if v not in (None, "", [], {})}

    return {
        "birth_summary": instant_context.get("birth_summary"),
        "intent_summary": intent_summary,
        "evidence_plan": instant_context.get("evidence_plan") if isinstance(instant_context.get("evidence_plan"), dict) else {},
        "natal_snapshot": compact_natal,
        "target_chart_context": compact_target,
        "current_dashas": current_dashas,
        "named_dasha_lookup": named_dasha_lookup,
        "current_transits": compact_transits,
        "instant_parashari": compact_parashari,
        "normalized_evidence": compact_normalized,
        "recent_history": list(instant_context.get("recent_history") or [])[-1:],
        "complexity_hint": instant_context.get("complexity_hint"),
        "context_profile": "speech_compact_v1",
    }


def _build_instant_prompt(
    question: str,
    instant_context: Dict[str, Any],
    language: str,
    *,
    speech_mode: bool = False,
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
    identity_block = (
        """You are Tara, the voice guide on AstroRoshni (speech / voice chat).

Your job:
- Answer quickly and clearly from the provided chart evidence, in a warm, spoken voice — as if the user is listening, not reading a report.
- If the user is only deferring or has no question yet (for example "nothing for now", "no thanks"), reply warmly in one or two sentences. Do not analyze the chart and do not say you will look anything up — wait until they ask something real.
- Use `instant_parashari` as the primary reasoning spine. That section already compresses the strongest current dasha, house activation, transit pressure, divisional support, and topic-specific Parashari signals.
- Use the raw natal/dasha/transit fields only to support or clarify the Parashari reading, not to replace it.
- Prefer short sentences and plain language; avoid lists, bullets, markdown, numbered steps, and long parenthetical asides (they are hard to follow by ear).
- Avoid report-language in speech. Do not say "the astrological indicators suggest", "materialization window", "this event", or "these matters" when you can name the real topic directly.
- Do not ask a new clarifying question inside the main answer; give your best answer from the evidence. Optional next steps go only in the follow-up block at the end.
- Do not output HTML, JSON (except the required follow-up block after the answer), markdown tables, glossary blocks, FAQ_META, or internal tags.
- Do not mention hidden reasoning, token limits, or model limitations.
- Never invent missing chart data.
- The app has already played Tara's greeting before this answer. Never say hello, never address the user by name as a greeting, and never introduce yourself as Tara. Start directly with the astrological answer."""
        if speech_mode
        else """You are AstroRoshni Instant Chat, the fast conversational astrology lane.

Your job:
- Answer quickly and clearly from the provided chart evidence.
- If the user is only deferring or has no question yet (for example "nothing for now", "no thanks"), reply briefly and warmly without chart analysis or saying you will look something up.
- Use `instant_parashari` as the primary reasoning spine. That section already compresses the strongest current dasha, house activation, transit pressure, divisional support, and topic-specific Parashari signals.
- Use the raw natal/dasha/transit fields only to support or clarify the Parashari reading, not to replace it.
- Be conversational and natural, not report-like.
- Do not output HTML, JSON, markdown tables, glossary blocks, follow-up widgets, FAQ_META, or internal tags.
- Do not mention hidden reasoning, token limits, or model limitations.
- Use plain astrological language that normal users can understand.
- If the question is too complex for a fast answer, still answer helpfully but say one short line that a deeper reading would be better for exact timing or full synthesis.
- Never invent missing chart data."""
    )
    length_rule = (
        "- Keep it concise for listening: usually 1 to 3 short paragraphs; favour shorter sentences."
        if speech_mode
        else "- Keep it concise but useful: usually 2 to 5 short paragraphs."
    )
    followup_tail = ""
    if speech_mode:
        followup_tail = f"""

After the main answer, output EXACTLY this structure (nothing after {_FOLLOW_UPS_END}):
{_FOLLOW_UPS_START}
["Spoken follow-up 1?", "Spoken follow-up 2?", "Spoken follow-up 3?"]
{_FOLLOW_UPS_END}

Follow-up rules:
- 0 to 3 strings only; use [] if none are helpful.
- Each string: natural when read aloud, ONE idea, at most 14 words.
- If the user's last message was very short (e.g. "in general"), start the follow-up with a brief topic anchor so they know what it refers to (e.g. "Eating habits — want a timeframe next?").
- Do not repeat the same clarification dimension you already resolved (e.g. don't ask general vs timed again if they just chose general).
- Valid JSON array of strings only inside the markers; no trailing comma."""
    next_action_tail = """

At the very end of the answer, append exactly one line in this format:
NEXT_ACTION_META: {"type":"<remedy|diagnosis|timing|clarification|comparison|chart_explanation|none>","title":"<short label>","reason":"<short reason in the same language as the answer>","confidence":"<high|medium|low>","follow_up_questions":["<up to 3 short user-facing options>"],"source":"instant"}
Always include this line. If no follow-up is needed, set type to "none" and follow_up_questions to an empty array.
Keep it short and valid JSON.
"""
    timing_lock_block = ""
    try:
        from ai.prediction_anchor import (
            career_timing_prompt_for_topic,
            compare_verdict_to_anchor,
            format_timing_contract_lock_block,
            get_locked_anchor,
            infer_topic_key,
            should_apply_timing_contract,
        )

        session_ctx = (
            instant_context.get("session_extracted_context")
            if isinstance(instant_context.get("session_extracted_context"), dict)
            else {}
        )
        if should_apply_timing_contract(mode=mode, category=category, question=question) or answer_mode == "event_prediction":
            topic_key = infer_topic_key(question, category=category)
            locked = get_locked_anchor(session_ctx, topic_key)
            verdict = (
                normalized_evidence.get("event_timing_verdict")
                if isinstance(normalized_evidence.get("event_timing_verdict"), dict)
                else {}
            )
            if locked:
                rerank = compare_verdict_to_anchor(locked, verdict)
                timing_lock_block = "\n\n" + format_timing_contract_lock_block(locked, rerank=rerank)
            elif str(category or "").lower() in {"career", "job", "promotion", "business"} or topic_key.startswith("career"):
                timing_lock_block = "\n\n" + career_timing_prompt_for_topic(
                    topic_key, category=category, question=question
                )
    except Exception:
        logger.exception("instant_timing_contract_lock_inject_failed")
        timing_lock_block = ""
    return f"""
{identity_block}

Astrological method:
{analysis_block}
{timing_lock_block}

Style rules:
- Language: {language_label}
{length_rule}
- Natal chart facts (dignity, avastha including Mrit, Mrityu Bhaga, natal combustion) are birth properties — say "in the natal chart" / "by birth", never "currently Mrit/debilitated" unless you mean a transit planet's sky position.
- If the user is only deferring or declining to ask (for example: "nothing for now", "no thanks", "not yet", "I'm good"), reply in one or two warm sentences. Do not analyze the chart, dashas, houses, or transits, and do not say you will look something up in the chart — there is no question to answer yet.
- Lead with the direct answer in the first 1 to 2 sentences when there is a real astrological question.
- If `named_dasha_lookup.matches` is present, use its `authoritative_fact` for the requested planet dasha start/end date. Do not infer a different date from transits, event windows, or current dasha summaries.
- If `normalized_evidence.event_timing_verdict.answer_event_label` is present, name that event plainly in the first sentence. Avoid vague placeholders like "this event" or "these matters" as the only topic name.
- In speech mode, sound like a live guide, not a report. Prefer openers like "For promotion, I would look most closely at..." or "For having a child, the cleaner window is..." Avoid stiff phrases such as "the astrological indicators suggest", "materialization window", "these matters", "this event", and "planetary influences".
- In speech mode, do not repeat the same timing noun in every sentence. After naming the window once, use natural phrasing like "that phase", "that stretch", or "then" only when the reference is clear.
- In speech mode, keep technical proof compact: name the dasha chain and 1 concrete reason from `allowed_house_themes` or `why`; do not narrate every activated house if it makes the answer sound mechanical.
- If `normalized_evidence.divisional_specifics` has concrete D7, D9, D10, or Karkamsa evidence, mention one relevant chart code naturally. This is good credibility in speech, but keep it to one compact sentence unless the user asks for technical detail.
- Mention the strongest current dasha or transit factor only when it genuinely helps clarity for this answer mode.
- Start from `normalized_evidence.primary_drivers` and only then bring in `secondary_modifiers`.
- Use `normalized_evidence.answer_mode_contract.answer_skeleton` as the structural backbone of the response.
- For event-prediction answers, obey `normalized_evidence.event_timing_verdict.claim_contract` as a hard evidence gate. A focus house is only a possible topic house; it is not active in a timing window unless that same window lists it in `activated_focus_houses` or names it in `why`.
- For event-prediction answers, never translate a raw line like "Jupiter rules focus house(s) [9]" into "Jupiter rules the progeny house" or another named domain house unless that exact domain house number is explicitly active in the same window. Safer wording is "Jupiter activates an event-relevant support house" or the exact house theme from `allowed_house_themes`.
- For event-prediction answers, do not say "career house", "marriage house", "progeny house", "health house", or similar named-house claims unless the corresponding house number is active in that window. Use the listed `allowed_house_themes` instead.
- If the question is about career, relationship, wealth, or health, use the corresponding topic signals and divisional specifics from `normalized_evidence` or `instant_parashari` to keep the answer precise.
- If the question is about a specific facet inside a broader area, answer that facet directly from the house activation and dasha logic instead of widening the answer into a whole life summary.
- If `intent_summary.target_subject.key` is not `self`, treat `target_chart_context` as the primary chart frame for that person instead of reading only from the native's direct Lagna context.
- No decorative headers unless absolutely needed.
{next_action_tail}

USER QUESTION:
{question}

ASTROLOGY CONTEXT:
{context_json}
{followup_tail}
""".strip()


async def generate_instant_chat_response(
    analyzer,
    *,
    question: str,
    birth_data: Dict[str, Any],
    intent: Optional[Dict[str, Any]],
    history: List[Dict[str, Any]],
    language: str = "english",
    speech_mode: bool = False,
) -> Dict[str, Any]:
    if _is_conversational_non_question(question):
        return _conversational_ack_response(language, speech_mode=speech_mode)

    mode_selection = _mode_selection_from_intent(intent)
    if mode_selection:
        logger.info(
            "instant_answer_mode_from_intent answer_mode=%s target=%s",
            mode_selection.get("answer_mode"),
            (mode_selection.get("target_subject") or {}).get("key"),
        )
    else:
        mode_selection = await _infer_answer_mode_with_llm(
            analyzer,
            question=question,
            intent=intent,
            history=history,
        )
    if bool((mode_selection or {}).get("needs_year_clarification")):
        return _instant_lifetime_event_year_clarification_response(language, speech_mode=speech_mode)
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
    prompt_context = instant_context
    if speech_mode and _env_flag("SPEECH_COMPACT_CONTEXT", True):
        compact_context = _compact_context_for_speech(instant_context)
        full_chars = _json_size(instant_context)
        compact_chars = _json_size(compact_context)
        reduction_pct = round(((full_chars - compact_chars) / full_chars) * 100.0, 1) if full_chars else 0.0
        logger.info(
            "SPEECH_PERF speech_context_compact profile=speech_compact_v1 full_chars=%s compact_chars=%s reduction_pct=%s",
            full_chars,
            compact_chars,
            reduction_pct,
        )
        prompt_context = compact_context
    if speech_mode:
        try:
            if _env_flag("SPEECH_LOG_FULL_CONTEXT", False):
                logger.info(
                    "SPEECH_DEBUG instant_llm_context_full answer_mode=%s target_subject=%s question=%r context_json=%s",
                    answer_mode,
                    json.dumps(target_subject, ensure_ascii=False, default=str, sort_keys=True) if target_subject else "null",
                    question,
                    json.dumps(instant_context, ensure_ascii=False, default=str, sort_keys=True),
                )
            logger.info(
                "SPEECH_DEBUG instant_llm_context_prompt answer_mode=%s target_subject=%s compact=%s context_json=%s",
                answer_mode,
                json.dumps(target_subject, ensure_ascii=False, default=str, sort_keys=True) if target_subject else "null",
                bool(prompt_context is not instant_context),
                json.dumps(prompt_context, ensure_ascii=False, default=str, sort_keys=True),
            )
        except Exception as exc:
            logger.warning("SPEECH_DEBUG instant_llm_context_full_log_failed error=%s", str(exc)[:200])
    prompt = _build_instant_prompt(question, prompt_context, language, speech_mode=speech_mode)
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

    raw_response = (llm_result.get("response") or "").strip()
    if speech_mode:
        response_text, speech_followups = _parse_speech_followups_from_answer(raw_response)
        response_text = _strip_speech_answer_greeting(response_text)
    else:
        response_text = raw_response
        speech_followups = []
    parsed_response = ResponseParser.parse_images_in_chat_response(response_text)
    response_content = parsed_response.get("content") or response_text
    response_content, prediction_anchor_meta = ResponseParser.parse_prediction_anchor_metadata(response_content)
    if speech_mode:
        response_content = _strip_speech_answer_greeting(response_content)
        response_content = _polish_speech_event_answer(response_content, prompt_context)
        response_content = _truncate_speech_answer(response_content)
    next_action = parsed_response.get("next_action") or {}
    combined_followups = list(next_action.get("follow_up_questions") or parsed_response.get("follow_up_questions", []))
    if not combined_followups and speech_followups:
        combined_followups = list(speech_followups)
    logger.info(
        "instant_chat_next_action_decoded type=%s title=%s confidence=%s follow_up_count=%s speech_mode=%s",
        next_action.get("type"),
        next_action.get("title"),
        next_action.get("confidence"),
        len(combined_followups),
        bool(speech_mode),
    )
    event_timing_verdict = None
    try:
        ne = (prompt_context or {}).get("normalized_evidence") or {}
        if isinstance(ne.get("event_timing_verdict"), dict):
            event_timing_verdict = ne.get("event_timing_verdict")
    except Exception:
        event_timing_verdict = None
    return {
        "success": True,
        "response": response_content,
        "prediction_anchor_meta": prediction_anchor_meta,
        "event_timing_verdict": event_timing_verdict,
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
        "llm_response_chars": len(response_content),
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
        "follow_up_questions": combined_followups,
        "recommended_follow_up_questions": combined_followups,
        "next_best_need": next_action.get("type"),
        "next_best_need_confidence": next_action.get("confidence"),
        "next_best_need_title": next_action.get("title"),
        "next_best_need_reason": next_action.get("reason"),
        "next_action": next_action or None,
        "summary_image": None,
        "analysis_steps": [],
        "faq_metadata": None,
        "raw_response": raw_response,
        "instant_context_summary": instant_context.get("intent_summary") or {},
    }
