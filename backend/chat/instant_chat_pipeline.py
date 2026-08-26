from __future__ import annotations

import json
import logging
import os
import re
import uuid
from calendar import monthrange
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional
import asyncio
import time

from ai.parallel_chat.parallel_agent_payloads import build_parashari_agent_payload
from ai.response_parser import ResponseParser
from calculators import RemedyEngine
from calculators.chart_calculator import ChartCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.gandanta_calculator import GandantaCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from calculators.shadbala_calculator import ShadbalaCalculator
from calculators.yogi_calculator import YogiCalculator
from chat.chat_context_builder import ChatContextBuilder
from daily_prediction_spine import build_daily_prediction_spine
from instant_chat_v2 import build_instant_v2_packet, finalize_instant_v2_packet
from instant_chat_v2.career import (
    CAREER_ALIASES,
    CAREER_PROFILES,
    answer_contract as build_career_answer_contract,
    build_vocation_synthesis,
    career_profile,
    classify_manifestations as classify_career_manifestations,
    is_career_decision,
    is_career_category,
    is_career_relationship,
    is_static_career_profile,
    normalize_career_subtype,
)
from instant_chat_v2.health import HEALTH_ALIASES, HEALTH_PROFILES
from instant_chat_v2.graph_live import apply_live_graph_policy, enforce_live_graph_answer
from instant_chat_v2.marriage_timeline import (
    apply_timeline_intent_guard,
    build_phase_action,
    build_selection_response,
)
from instant_aspect_policy import instant_activation_aspects
from context_agents.base import AgentContext
from prediction_engine.nakshatra_transit import nakshatra_transit_relation
from prediction_engine.natal_promise import build_natal_promises
from shared.dasha_calculator import DashaCalculator
from utils.admin_settings import (
    CHAT_LLM_DEEPSEEK,
    CHAT_LLM_GEMINI,
    get_instant_chat_llm_provider,
    get_instant_chat_model,
)
from utils.query_context import (
    is_remedy_followup_request,
    NO_INLINE_REMEDY_PLAN_RULE,
    NEXT_ACTION_NONE_IN_REMEDY_MODE,
    apply_normal_answer_remedy_guards,
    REMEDY_CARD_FOMO_COPY_RULES,
)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _instant_timeout_seconds(name: str, default: float, *, maximum: float) -> float:
    try:
        return max(3.0, min(maximum, float(os.getenv(name, str(default)) or default)))
    except (TypeError, ValueError):
        return default


def _instant_thinking_level(model_name: str) -> Optional[str]:
    """Fast but non-zero reasoning for Gemini 3; Gemini 2.x omits the setting."""
    model_id = str(model_name or "").lower()
    if "gemini-3" not in model_id:
        return None
    configured = str(os.getenv("INSTANT_CHAT_THINKING_LEVEL") or "").strip().lower()
    if configured in {"minimal", "low", "medium", "high"}:
        return configured
    return "minimal" if "flash-lite" in model_id else "low"


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
    "job_change": {"houses": [3, 6, 10, 12], "planets": ["Rahu", "Saturn", "Mars", "Mercury"]},
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

# Career routing, calculation, evidence and answer composition must all use
# one policy.  Keep the legacy names as aliases because older clients and
# stored intent rows still send them.
for _career_name, _career_policy in CAREER_PROFILES.items():
    CATEGORY_FOCUS[_career_name] = {
        "houses": list(_career_policy["houses"]),
        "planets": list(_career_policy["planets"]),
    }
for _career_alias, _career_name in CAREER_ALIASES.items():
    CATEGORY_FOCUS[_career_alias] = dict(CATEGORY_FOCUS[_career_name])
for _health_name, _health_policy in HEALTH_PROFILES.items():
    CATEGORY_FOCUS[_health_name] = {
        "houses": list(_health_policy["houses"]),
        "planets": list(_health_policy["planets"]),
    }
for _health_alias, _health_name in HEALTH_ALIASES.items():
    CATEGORY_FOCUS[_health_alias] = dict(CATEGORY_FOCUS[_health_name])

EVENT_CATEGORY_PRIORITIES = {
    "career": {"house_weights": {10: 3.0, 6: 2.5, 11: 2.0, 2: 1.5}, "planet_weights": {"Saturn": 2.0, "Sun": 1.8, "Mercury": 1.8, "Jupiter": 1.4}},
    "job": {"house_weights": {10: 3.0, 6: 2.5, 11: 2.0, 2: 1.5}, "planet_weights": {"Saturn": 2.0, "Sun": 1.8, "Mercury": 1.8, "Jupiter": 1.4}},
    "promotion": {"house_weights": {10: 3.0, 6: 2.5, 11: 2.4, 2: 1.5}, "planet_weights": {"Sun": 2.0, "Saturn": 1.8, "Mercury": 1.6, "Jupiter": 1.5}},
    "job_change": {"house_weights": {10: 3.0, 6: 2.5, 12: 2.4, 3: 2.0}, "planet_weights": {"Rahu": 2.0, "Saturn": 1.8, "Mars": 1.6, "Mercury": 1.5}},
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

for _career_name, _career_policy in CAREER_PROFILES.items():
    _houses = list(_career_policy["houses"])
    _planets = list(_career_policy["planets"])
    EVENT_CATEGORY_PRIORITIES[_career_name] = {
        "house_weights": {house: max(1.2, 3.0 - (index * 0.45)) for index, house in enumerate(_houses)},
        "planet_weights": {planet: max(1.2, 2.0 - (index * 0.18)) for index, planet in enumerate(_planets)},
    }
for _career_alias, _career_name in CAREER_ALIASES.items():
    EVENT_CATEGORY_PRIORITIES[_career_alias] = dict(EVENT_CATEGORY_PRIORITIES[_career_name])
for _health_name, _health_policy in HEALTH_PROFILES.items():
    _houses = list(_health_policy["houses"])
    _planets = list(_health_policy["planets"])
    EVENT_CATEGORY_PRIORITIES[_health_name] = {
        "house_weights": {house: max(1.2, 3.0 - (index * 0.4)) for index, house in enumerate(_houses)},
        "planet_weights": {planet: max(1.2, 2.0 - (index * 0.18)) for index, planet in enumerate(_planets)},
    }
for _health_alias, _health_name in HEALTH_ALIASES.items():
    EVENT_CATEGORY_PRIORITIES[_health_alias] = dict(EVENT_CATEGORY_PRIORITIES[_health_name])

EVENT_ANSWER_LABELS = {
    "career": "career growth",
    "job": "job matters",
    "promotion": "promotion",
    "job_change": "job change",
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
EVENT_ANSWER_LABELS.update({
    name: str(profile["label"])
    for name, profile in HEALTH_PROFILES.items()
})

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
    "mental_wellbeing": "health",
    "accident": "health",
    "recovery": "health",
    "property": "wealth",
    "relocation": "career",
    "visa": "career",
    "travel": "career",
    "litigation": "health",
    "surgery": "health",
    "higher_studies": "career",
}

EVENT_CATEGORY_ALIASES = {
    "money": "wealth",
    "finance": "wealth",
    "financial": "wealth",
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
EVENT_CATEGORY_ALIASES.update(HEALTH_ALIASES)

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
    "job_change": frozenset({"Rahu", "Saturn", "Mars", "Mercury"}),
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
for _health_name, _health_policy in HEALTH_PROFILES.items():
    EVENT_CATEGORY_KARAKAS[_health_name] = frozenset(_health_policy["planets"])
for _health_alias, _health_name in HEALTH_ALIASES.items():
    EVENT_CATEGORY_KARAKAS[_health_alias] = EVENT_CATEGORY_KARAKAS[_health_name]

_INSTANT_EVENT_HORIZON_DAYS = int(365 * 3)

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
    # Instant policy values are ordinal aspect numbers (7 means "7th from the
    # planet"), not zero-based movement offsets. The target is therefore
    # origin + aspect_number - 1. Rahu/Ketu deliberately expose only the 7th
    # aspect here; occupation/conjunction is handled separately.
    for aspect_number in instant_activation_aspects(planet, include_conjunction=False):
        if _norm_house(th + aspect_number - 1) == tgt:
            return True
    return False


def _planet_aspect_number_from(origin_house: int, target_house: int, planet: str) -> Optional[int]:
    """Return the classical ordinal aspect that connects two houses, if any."""
    origin = _norm_house(origin_house)
    target = _norm_house(target_house)
    if origin is None or target is None:
        return None
    for aspect_number in instant_activation_aspects(planet, include_conjunction=False):
        if _norm_house(origin + aspect_number - 1) == target:
            return int(aspect_number)
    return None


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
    career_subtype: Any = None,
    forward_scan_periods: List[Dict[str, Any]],
    horizon_segments: List[Dict[str, Any]],
    current_chain_rows: List[Dict[str, Any]],
    timing_policy: Dict[str, Any],
    focus_houses: Optional[List[int]] = None,
    current_transits: Optional[Dict[str, Any]] = None,
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

    # A conversational answer must distinguish the first material easing from
    # the later absolute peak. Keeping only the maximum-scoring period can make
    # a truthful answer sound as though nothing improves for years.
    material_threshold = current_score + 8 if current_row else 1
    materially_better = sorted(
        [row for row in future_candidates if _event_row_score(row) >= material_threshold],
        key=lambda row: str(row.get("start") or ""),
    )
    earliest_material_future = materially_better[0] if materially_better else {}
    # Preserve distinct material stages in chronological order. A later window
    # can activate a different event house while scoring a few points below the
    # absolute peak; dropping it would make a time-bound answer incomplete.
    material_future_progression: List[Dict[str, Any]] = []
    seen_progression_keys = set()
    for row in materially_better:
        key = (
            str(row.get("start") or ""),
            str(row.get("end") or ""),
            str(row.get("chain") or ""),
        )
        if key in seen_progression_keys:
            continue
        if material_future_progression:
            previous = material_future_progression[-1]
            previous_houses = {
                int(h) for h in (previous.get("activated_focus_houses") or [])
                if str(h).isdigit()
            }
            row_houses = {
                int(h) for h in (row.get("activated_focus_houses") or [])
                if str(h).isdigit()
            }
            # Consecutive PD changes are not automatically distinct stages.
            # If the new row activates no additional topic house and is not
            # stronger, keep the earlier cleaner statement and leave room for
            # a later material escalation.  Missing house metadata is not
            # treated as redundancy because it cannot prove equivalence.
            if (
                previous_houses
                and row_houses
                and row_houses.issubset(previous_houses)
                and _event_row_score(row) <= _event_row_score(previous)
            ):
                continue
        seen_progression_keys.add(key)
        material_future_progression.append(row)
    if len(material_future_progression) > 3:
        earliest = material_future_progression[0]
        intermediate_candidates = [
            row for row in material_future_progression[1:]
            if row is not best_future
        ]
        strongest_intermediate = (
            max(intermediate_candidates, key=_event_row_score)
            if intermediate_candidates
            else None
        )
        material_future_progression = [
            row for row in (earliest, strongest_intermediate, best_future)
            if row
        ]
        material_future_progression.sort(key=lambda row: str(row.get("start") or ""))
    elif best_future and all(row is not best_future for row in material_future_progression):
        material_future_progression.append(best_future)
        material_future_progression.sort(key=lambda row: str(row.get("start") or ""))

    topical_transits: List[Dict[str, Any]] = []
    focus_house_set = {int(h) for h in (focus_houses or []) if str(h).isdigit()}
    for planet, row in (current_transits or {}).items():
        if not isinstance(row, dict):
            continue
        try:
            transit_house = int(row.get("house_from_lagna") or row.get("house") or 0)
        except (TypeError, ValueError):
            transit_house = 0
        if transit_house not in focus_house_set:
            continue
        topical_transits.append({
            "planet": str(planet),
            "house": transit_house,
            "sign": row.get("sign"),
            "retrograde": bool(row.get("retrograde")),
        })

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
    if earliest_material_future and best_future and earliest_material_future is not best_future:
        required_points.append(
            "Lead with the earliest materially better future window, then mention the later peak separately."
        )
    if topical_transits:
        required_points.append(
            "Use the listed current topic transit as part of the explanation of why the issue feels active now."
        )
    if abs(score_delta) <= 5 and current_window and future_cluster:
        required_points.append("Say the future window is only slightly cleaner/stronger; do not overstate the gap.")

    return {
        "event_category": _normalize_event_category(category),
        "answer_event_label": EVENT_ANSWER_LABELS.get(_normalize_event_category(category), EVENT_ANSWER_LABELS["general"]),
        "timing_policy": timing_policy or {},
        "current_window": current_window,
        "best_future_window": _event_row_window(best_future) if best_future else {},
        "best_future_cluster": future_cluster,
        "earliest_material_future_window": (
            _event_row_window(earliest_material_future) if earliest_material_future else {}
        ),
        "material_future_progression": [
            _event_row_window(row) for row in material_future_progression
        ],
        "current_topic_transits": topical_transits[:5],
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
            "Do not imply the user must wait until the absolute peak when an earlier materially better window is provided.",
            "Do not flip the same period from supportive house significations (e.g. 7th/contracts) to hostile ones (e.g. 8th/rejection) without new activated_focus_houses evidence.",
            "Do not treat a PD / micro-dasha start date as an offer or joining SLA; PD starts are activation/environment shifts unless the ranked execution window supports offer/joining.",
            "Do not use guarantee / copper-bottomed / mathematical conclusion / perfectly accurate / absolute truth / non-negotiable / will get phrasing.",
        ],
        "career_layer_contract": (
            {
                "profile": career_profile(category, career_subtype),
                "manifestations": classify_career_manifestations(
                    (future_claim_contract or current_claim_contract or {}).get("activated_focus_houses") or [],
                    career_subtype,
                ),
                "rule": (
                    "Use only the supplied house-gated manifestation stages. Separate activity, "
                    "formalization, execution/joining, compensation, stability and exit pressure; "
                    "never let one dasha date mean all of them."
                ),
            }
            if is_career_category(category)
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
    career_subtype: Any = None,
    question: str,
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
    named_dasha_lookup: Optional[Dict[str, Any]] = None,
    evidence_plan: Optional[Dict[str, Any]] = None,
    daily_prediction_spine: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    focus_houses = list((instant_parashari or {}).get("focus_houses") or [])
    historical_scan = (
        (instant_parashari or {}).get("historical_event_dasha_scan")
        or (normalized_evidence or {}).get("historical_event_dasha_scan")
        or {}
    )
    is_retrospective = bool(
        isinstance(historical_scan, dict)
        and (
            historical_scan.get("periods")
            or str(((normalized_evidence or {}).get("timing_policy") or {}).get("time_direction") or "").lower()
            == "retrospective"
        )
    )
    is_target_relative = str((target_chart_context or {}).get("key") or "self") != "self"
    prediction_house_lordships = (
        dict((target_chart_context or {}).get("target_house_lordships") or {})
        if is_target_relative
        else house_lordships
    )
    prediction_chart_data = (
        {"planets": dict((target_chart_context or {}).get("target_key_planets") or {})}
        if is_target_relative
        else chart_data
    )
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
                **_planet_prediction_status(
                    planet,
                    row,
                    prediction_chart_data,
                    prediction_house_lordships,
                ),
                "current_transit_contact": _current_transit_contacts_for_planet(planet, row, current_transits_formatted),
            }
        )
    future_windows: List[Dict[str, Any]] = []
    as_of_day = str((period_window or {}).get("start") or "")[:10]
    duration_months: Optional[int] = None
    for part in list((evidence_plan or {}).get("question_parts") or []):
        timeframe = part.get("timeframe") if isinstance(part, dict) and isinstance(part.get("timeframe"), dict) else {}
        if timeframe.get("duration_months") is not None:
            try:
                duration_months = max(0, int(timeframe.get("duration_months")))
            except (TypeError, ValueError):
                duration_months = None
            break
    requested_horizon_end = ""
    if duration_months is not None and as_of_day:
        try:
            as_of_date = datetime.strptime(as_of_day, "%Y-%m-%d").date()
            month_index = as_of_date.month - 1 + duration_months
            horizon_year = as_of_date.year + month_index // 12
            horizon_month = month_index % 12 + 1
            horizon_day = min(as_of_date.day, monthrange(horizon_year, horizon_month)[1])
            requested_horizon_end = f"{horizon_year:04d}-{horizon_month:02d}-{horizon_day:02d}"
        except (TypeError, ValueError):
            requested_horizon_end = ""

    def _clip_to_requested_horizon(row: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(row, dict):
            return None
        start = str(row.get("start") or "")[:10]
        end = str(row.get("end") or "")[:10]
        if as_of_day and end and end < as_of_day:
            return None
        if requested_horizon_end and start and start > requested_horizon_end:
            return None
        clipped = dict(row)
        if as_of_day and start and start < as_of_day:
            clipped["start"] = as_of_day
        if requested_horizon_end and end and end > requested_horizon_end:
            clipped["end"] = requested_horizon_end
            clipped["clipped_to_requested_horizon"] = True
        return clipped

    horizon_segments = [
        clipped
        for row in list(((instant_parashari or {}).get("horizon_dasha_segments") or {}).get("segments") or [])
        if (clipped := _clip_to_requested_horizon(row)) is not None
    ]
    forward_scan_periods = [
        clipped
        for row in list((((instant_parashari or {}).get("forward_event_dasha_scan") or {}).get("periods") or []))
        if not _is_fallback_dasha_triplet(row.get("mahadasha"), row.get("antardasha"), row.get("pratyantardasha"))
        and (clipped := _clip_to_requested_horizon(row)) is not None
    ]
    timing_policy = dict((normalized_evidence or {}).get("timing_policy") or {})
    if is_retrospective:
        def _compact_historical_period(row: Dict[str, Any]) -> Dict[str, Any]:
            peaks = []
            for peak in list(row.get("peak_activation_windows") or [])[:4]:
                if not isinstance(peak, dict):
                    continue
                peaks.append({
                    key: peak.get(key)
                    for key in (
                        "start", "end", "planet", "dasha_levels", "trigger_kinds",
                        "strength", "trigger_score", "activated_focus_houses", "why",
                    )
                    if peak.get(key) not in (None, "", [], {})
                })
            carriers = []
            for carrier in list(row.get("carrier_planets") or [])[:3]:
                if not isinstance(carrier, dict):
                    continue
                carriers.append({
                    key: carrier.get(key)
                    for key in (
                        "planet", "dasha_levels", "natal_placement_house", "natal_event_houses",
                    )
                    if carrier.get(key) not in (None, "", [], {})
                })
            return {
                key: value
                for key, value in {
                    "start": row.get("start"),
                    "end": row.get("end"),
                    "phase_start": row.get("phase_start"),
                    "phase_end": row.get("phase_end"),
                    "phase_dasha_chain": row.get("phase_dasha_chain"),
                    "phase_granularity": row.get("phase_granularity"),
                    "mahadasha": row.get("mahadasha"),
                    "antardasha": row.get("antardasha"),
                    "pratyantardasha": row.get("pratyantardasha"),
                    "strongest_pd_window": row.get("strongest_pd_window"),
                    "relevance_score": row.get("relevance_score"),
                    "historical_marriage_rank_score": row.get("historical_marriage_rank_score"),
                    "period_strength": row.get("period_strength"),
                    "period_label": row.get("period_label"),
                    "time_status": "past",
                    "activated_focus_houses": row.get("activated_focus_houses"),
                    "natal_promise_status": row.get("natal_promise_status"),
                    "activation_strength": row.get("activation_strength"),
                    "transit_trigger_score": row.get("transit_trigger_score"),
                    "carrier_planets": carriers,
                    "peak_activation_windows": peaks,
                    "probable_peak_windows": list(row.get("probable_peak_windows") or [])[:4],
                    "predicted_result_areas": list(row.get("predicted_result_areas") or [])[:4],
                    "why": row.get("why"),
                    "claim_rule": row.get("claim_rule"),
                }.items()
                if value not in (None, "", [], {})
            }

        historical_periods = [
            _compact_historical_period(row)
            for row in list(historical_scan.get("periods") or [])
            if isinstance(row, dict) and (row.get("start") or row.get("end"))
        ][:6]
        transit_confirmed_periods = [
            row for row in historical_periods
            if int(row.get("transit_trigger_score") or 0) > 0
            and bool(row.get("peak_activation_windows"))
        ]
        event_timing_verdict = {
            "event_category": category,
            "answer_event_label": EVENT_ANSWER_LABELS.get(category, "marriage"),
            "verdict": "probable_past_windows" if transit_confirmed_periods else "insufficient_historical_evidence",
            "comparison": "ranked probable past periods",
            "confidence": "medium" if transit_confirmed_periods else "low",
            "ranked_windows": transit_confirmed_periods[:3],
            "answer_rule": (
                "Present each MD-AD range as a broad probable past phase and its supplied probable_peak_windows "
                "as narrower astrological concentrations. Never call a peak the known marriage date. Ask the user "
                "whether a phase is close or to enter the actual date."
            ),
            "required_answer_points": [
                "Give no more than three strongest past periods in ranked order.",
                "For each period, give the broad MD-AD phase before one or two probable peak dates.",
                "Explain the dasha and historical transit convergence for each period.",
                "Ask whether one is close or invite the user to enter the actual date.",
            ],
            "forbidden_answer_moves": [
                "Do not claim that a probable period is the actual marriage date.",
                "Do not include a future or current period.",
                "Do not invent an exact day from a broad activation window.",
            ],
            "claim_contract": {
                "claim_type": "probable_past_periods_only",
                "historical_scope_start": historical_scan.get("horizon_start"),
                "historical_scope_end": historical_scan.get("horizon_end"),
                "claim_rule": historical_scan.get("claim_rule"),
            },
        }
    else:
        historical_periods = []
        transit_confirmed_periods = []
        event_timing_verdict = _build_event_timing_verdict(
            category=category,
            career_subtype=career_subtype,
            forward_scan_periods=forward_scan_periods,
            horizon_segments=horizon_segments,
            current_chain_rows=current_chain_rows,
            timing_policy=timing_policy,
            focus_houses=focus_houses,
            current_transits=current_transits_formatted,
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
            "answer_skeleton": (
                "Apply retrospective timing policy -> Rank probable past windows -> Explain dasha/transit convergence -> Ask which matches"
                if is_retrospective
                else "Apply timing_policy -> Verdict from strongest future windows -> Phase shifts from MD/AD/PD changes -> Support vs obstruction vs uncertainty -> Practical takeaway"
            ),
        },
        "timing_policy": timing_policy,
        # Promise evidence is static natal evidence, not prompt-heavy timing
        # workspace.  Preserve its adjudicated status in the slim event path;
        # otherwise the UI incorrectly reports that the D1 promise was absent
        # even though the same D1 chart powers the dasha/transit calculations.
        "natal_promise": dict((normalized_evidence or {}).get("natal_promise") or {}),
        "event_timing_verdict": event_timing_verdict,
        "current_timing": ({
            "active_dashas": safe_current_dashas_levels,
            "current_dasha_chain": current_chain,
            "authoritative_current_dasha_display": current_display,
            "authoritative_current_dasha_chain": current_chain,
            "authoritative_current_dasha_fact": authoritative_fact,
            "time_relation": str((normalized_evidence.get("current_timing") or {}).get("time_relation") or "current") if isinstance(normalized_evidence, dict) else "current",
            "period_window": period_window,
            "ownership": "native_chart",
            "target_interpretation": (
                f"This is the native chart's derived indication for {compact_target_context['label']}; "
                f"it is not {compact_target_context['label']}'s own dasha."
                if compact_target_context["key"] != "self"
                else "This is the native's own dasha."
            ),
        } if not is_retrospective else {}),
        "dasha_level_effects": list((normalized_evidence or {}).get("dasha_level_effects") or [])[:5],
        "future_windows": ([] if is_retrospective else future_windows),
        "forward_event_dasha_scan": ({
            "horizon_days": ((instant_parashari or {}).get("forward_event_dasha_scan") or {}).get("horizon_days"),
            "horizon_end": requested_horizon_end or ((instant_parashari or {}).get("forward_event_dasha_scan") or {}).get("horizon_end"),
            "periods": forward_scan_periods[:8],
        } if not is_retrospective else {}),
        "horizon_dasha_segments": ({
            "enabled": bool(horizon_segments),
            "segments": horizon_segments[:8],
            "label": ((instant_parashari or {}).get("horizon_dasha_segments") or {}).get("label"),
        } if not is_retrospective else {}),
        "topic_houses": _topic_house_rows(
            focus_houses,
            prediction_house_lordships,
            prediction_chart_data,
        ),
        # The native's D10/D7/etc. is not the other person's own divisional
        # chart. Omit it for derived-subject readings instead of inviting a
        # precise-sounding but invalid claim about their career or life.
        "divisional_topic": (
            {} if is_target_relative
            else _compact_divisional_topic_payload((instant_parashari or {}).get("divisional_support") or {})
        ),
        "divisional_support": (
            {} if is_target_relative
            else _compact_divisional_support((instant_parashari or {}).get("divisional_support") or {})
        ),
        "divisional_specifics": (
            [] if is_target_relative
            else list((normalized_evidence or {}).get("divisional_specifics") or [])[:3]
        ),
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
            (
                f"Native chart current chain: {current_display}; interpret it only through the derived {compact_target_context['label']} frame."
                if current_display and compact_target_context["key"] != "self"
                else f"Current chain: {current_display}." if current_display else ""
            ) if not is_retrospective else "",
            *([] if is_target_relative else [
                f"Divisional support: {line}"
                for line in list((normalized_evidence or {}).get("divisional_specifics") or [])[:2]
            ]),
            *[
                f"Probable past window {row.get('start')}–{row.get('end')}: "
                f"broad {row.get('phase_dasha_chain') or (str(row.get('mahadasha')) + '-' + str(row.get('antardasha')))} phase; "
                f"probable peaks {row.get('probable_peak_windows') or row.get('peak_activation_windows')}; "
                f"(houses {row.get('activated_focus_houses')}; {row.get('why')})"
                for row in transit_confirmed_periods[:3]
            ],
            *[
                f"Future window {row.get('start')}–{row.get('end')}: {row.get('chain')} (score {row.get('score')}; houses {row.get('activated_focus_houses')}; {row.get('why')})"
                for row in ([] if is_retrospective else future_windows[:4])
            ],
        ],
    }
    if is_retrospective:
        slim_normalized["historical_event_dasha_scan"] = {
            **dict(historical_scan),
            "periods": historical_periods,
        }
    # Preserve compact calculator provenance required by the v2 confidence
    # contract. These are already bounded by the evidence ledger compactor.
    for evidence_key in (
        "karaka_evidence",
        "double_transit",
        "nadi_evidence",
        "chart_facts",
        "location_recommendation",
        "muhurat_slots",
    ):
        if (normalized_evidence or {}).get(evidence_key) not in (None, "", [], {}):
            slim_normalized[evidence_key] = (normalized_evidence or {}).get(evidence_key)
    if is_career_category(category) and not is_target_relative:
        career_foundation = _compact_career_foundation(
            category,
            career_subtype,
            (instant_parashari or {}).get("natal_topic_factors") or {},
            (instant_parashari or {}).get("divisional_support") or {},
            (normalized_evidence or {}).get("chart_facts") or {},
            (normalized_evidence or {}).get("karaka_evidence") or {},
            (normalized_evidence or {}).get("profession_evidence") or {},
        )
        slim_normalized["career_foundation"] = career_foundation
        slim_normalized["answer_mode_contract"]["career_contract"] = build_career_answer_contract(
            "event_prediction",
            career_foundation.get("career_subtype"),
        )
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
        "future_windows": ([] if is_retrospective else future_windows),
        "forward_event_dasha_scan": slim_normalized["forward_event_dasha_scan"],
        "horizon_dasha_segments": slim_normalized["horizon_dasha_segments"],
        "topic_houses": _topic_house_rows(focus_houses, house_lordships, chart_data),
        "divisional_topic": _compact_divisional_topic_payload((instant_parashari or {}).get("divisional_support") or {}),
        "divisional_support": _compact_divisional_support((instant_parashari or {}).get("divisional_support") or {}),
        "major_transits": major_transits,
        "horizon_transit_anchors": (instant_parashari or {}).get("horizon_transit_anchors") or {},
    }
    if is_retrospective:
        slim_parashari["historical_event_dasha_scan"] = slim_normalized["historical_event_dasha_scan"]
    if slim_normalized.get("career_foundation"):
        slim_parashari["career_foundation"] = slim_normalized["career_foundation"]
    if named_dasha_lookup:
        slim_parashari["named_dasha_lookup"] = named_dasha_lookup
    return {
        "birth_summary": birth_summary,
        "intent_summary": {
            "category": category,
            "career_subtype": (
                career_profile(category, career_subtype)["subtype"]
                if is_career_category(category)
                else None
            ),
            "mode": "LIFESPAN_EVENT_TIMING",
            "answer_mode": "event_prediction",
            "period_window": period_window,
            "time_relation": (
                "past"
                if is_retrospective
                else str((normalized_evidence.get("current_timing") or {}).get("time_relation") or "current") if isinstance(normalized_evidence, dict) else "current"
            ),
            "focus_houses": focus_houses,
            "extracted_context": {"timeframe": question},
            "target_subject": {
                "key": compact_target_context["key"],
                "label": compact_target_context["label"],
                "base_house": compact_target_context["anchor_house"],
            },
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
        "current_dashas": ({
            "as_of": str((period_window or {}).get("start") or ""),
            "levels": safe_current_dashas_levels,
            "named_dasha_lookup": named_dasha_lookup or {},
        } if not is_retrospective else {}),
        "current_transits": ({
            "as_of_local": str((period_window or {}).get("start") or ""),
            "planets": major_transits,
        } if not is_retrospective else {}),
        "current_transits_formatted": ({} if is_retrospective else major_transits),
        "instant_parashari": slim_parashari,
        # The detailed D1 ledger is display/audit evidence.  Keep it available
        # to user_derivation while the composer boundary continues to exclude
        # `_user_evidence` from the Flash Lite prompt.
        "_user_evidence": {
            "natal_topic_factors": dict(
                (instant_parashari or {}).get("natal_topic_factors") or {}
            ),
        },
        "normalized_evidence": slim_normalized,
        # Exact-day questions can still be routed through the compact event
        # payload. Keep the authoritative five-level/KP/Moon calculation at
        # the top level so the Instant v2 evidence gateway can see it.
        "daily_prediction_spine": daily_prediction_spine or {},
        "recent_history": [],
        "complexity_hint": {"mode": "slim_event_prediction", "question_length": len(question or "")},
        "named_dasha_lookup": named_dasha_lookup or {},
    }

_INSTANT_CONTEXT_BUILDER = ChatContextBuilder()
logger = logging.getLogger(__name__)


def _log_instant_llm_request(
    *,
    stage: str,
    model_name: str,
    prompt: str,
    context: Any,
    answer_mode: str,
    speech_mode: bool,
    compacted: bool,
) -> Optional[str]:
    """Log the exact Instant Chat model input without Cloud Logging truncation.

    The model receives one prompt string rather than separate system/user
    messages. Prompt and serialized context are emitted independently in
    ordered chunks so an operator can reconstruct the complete request.
    """
    if not _env_flag("INSTANT_CHAT_LOG_FULL_LLM_REQUEST", True):
        return None
    try:
        chunk_chars = max(
            2_000,
            min(100_000, int(os.getenv("INSTANT_CHAT_LLM_LOG_CHUNK_CHARS", "24000") or "24000")),
        )
    except (TypeError, ValueError):
        chunk_chars = 24_000
    request_id = f"{stage}-{uuid.uuid4().hex[:12]}"
    context_json = json.dumps(
        context,
        ensure_ascii=False,
        default=str,
        separators=(",", ":"),
    )
    prompt_text = str(prompt or "")
    logger.info(
        "INSTANT_LLM_REQUEST_META %s",
        json.dumps({
            "request_id": request_id,
            "stage": stage,
            "model": model_name,
            "answer_mode": answer_mode,
            "speech_mode": bool(speech_mode),
            "compacted_context": bool(compacted),
            "context_chars": len(context_json),
            "prompt_chars": len(prompt_text),
            "sent_chars": len(prompt_text),
            "separate_system_prompt": False,
            "note": "Gemini receives the logged prompt as one complete prompt string.",
        }, ensure_ascii=False, separators=(",", ":")),
    )
    for payload_name, payload in (("CONTEXT", context_json), ("PROMPT", prompt_text)):
        chunks = [payload[i:i + chunk_chars] for i in range(0, len(payload), chunk_chars)] or [""]
        for index, chunk in enumerate(chunks, start=1):
            logger.info(
                "INSTANT_LLM_REQUEST_%s %s",
                payload_name,
                json.dumps({
                    "request_id": request_id,
                    "chunk": index,
                    "chunks": len(chunks),
                    "content": chunk,
                }, ensure_ascii=False, separators=(",", ":")),
            )
    return request_id


def _log_instant_llm_response(
    *,
    request_id: Optional[str],
    stage: str,
    model_name: str,
    prompt: str,
    result: Optional[Dict[str, Any]],
    elapsed_s: float,
) -> None:
    """Log the actual characters sent to and received from an instant LLM call."""
    payload = result or {}
    response_text = str(payload.get("response") or "")
    usage = payload.get("token_usage") if isinstance(payload.get("token_usage"), dict) else {}
    logger.info(
        "INSTANT_LLM_RESPONSE_META %s",
        json.dumps({
            "request_id": request_id,
            "stage": stage,
            "model": payload.get("chat_llm_model") or model_name,
            "success": bool(payload.get("success")),
            "sent_chars": len(str(prompt or "")),
            "received_chars": len(response_text),
            "input_tokens": int((usage or {}).get("input_tokens") or 0),
            "output_tokens": int((usage or {}).get("output_tokens") or 0),
            "cached_tokens": int((usage or {}).get("cached_tokens") or 0),
            "elapsed_ms": round(max(0.0, float(elapsed_s or 0.0)) * 1000.0, 1),
            "error": str(payload.get("error") or "")[:500] or None,
        }, ensure_ascii=False, separators=(",", ":")),
    )
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
    "factual_chart_lookup",
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
    "location_recommendation",
    "dedicated_muhurat_flow",
    "dedicated_partnership_flow",
    "compound_plan",
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


def _marriage_timeline_selection_response(
    result: Dict[str, Any],
    language: str,
    *,
    speech_mode: bool,
) -> Dict[str, Any]:
    """Package a deterministic timeline refinement without another LLM charge."""
    body = str(result.get("body") or "").strip()
    next_action = result.get("next_action") if isinstance(result.get("next_action"), dict) else None
    response = _conversational_ack_response(language, speech_mode=speech_mode)
    response.update(
        {
            "response": body,
            "raw_response": body,
            "chat_llm_model": "__marriage_timeline__",
            "llm_response_chars": len(body),
            "next_action": next_action,
            "next_best_need": (next_action or {}).get("type"),
            "next_best_need_confidence": (next_action or {}).get("confidence"),
            "next_best_need_title": (next_action or {}).get("title"),
            "next_best_need_reason": (next_action or {}).get("reason"),
            "instant_context_summary": {
                "category": "marriage",
                "mode": "LIFESPAN_EVENT_TIMING",
                "answer_mode": "event_prediction",
                "time_relation": "past",
                "timeline_stage": result.get("stage"),
                "target_subject": {"key": "self", "label": "self", "base_house": 1},
            },
        }
    )
    response["timing"] = {
        **dict(response.get("timing") or {}),
        "chat_llm_model": "__marriage_timeline__",
        "marriage_timeline_selection": True,
    }
    return response


# This is deliberately narrow. Natural-language medical triage belongs to the
# multilingual intent LLM; these patterns are only a defence-in-depth circuit
# breaker for unmistakable, actively occurring emergency symptoms.
_OBVIOUS_ACUTE_MEDICAL_EMERGENCY_PATTERNS = (
    re.compile(r"\b(?:i\s+(?:have|am\s+having|feel)|having|experiencing)\s+(?:a\s+)?(?:chest\s+pain|chest\s+pressure|chest\s+tightness)\b", re.I),
    re.compile(r"\b(?:chest\s+pain|chest\s+pressure|chest\s+tightness)\s+(?:right\s+now|now|currently)\b", re.I),
    re.compile(r"\b(?:cannot|can't|can\s+not)\s+breathe\b", re.I),
    re.compile(r"\b(?:face\s+droop|slurred\s+speech|sudden\s+one-sided\s+weakness)\b", re.I),
)


def _instant_medical_triage_decision(
    question: str,
    intent: Optional[Dict[str, Any]],
) -> Optional[Dict[str, str]]:
    """Return an urgent triage decision before any astrology is calculated."""
    text = str(question or "").strip()
    if any(pattern.search(text) for pattern in _OBVIOUS_ACUTE_MEDICAL_EMERGENCY_PATTERNS):
        return {"urgency": "emergency", "user_message": "", "source": "direct_fail_safe"}

    triage = (intent or {}).get("medical_triage")
    if isinstance(triage, dict):
        urgency = str(triage.get("urgency") or "none").strip().lower()
        if urgency in {"urgent", "emergency"}:
            return {
                "urgency": urgency,
                "user_message": str(triage.get("user_message") or "").strip(),
                "source": "semantic_router",
            }

    return None


def _instant_medical_triage_response(
    language: str,
    *,
    speech_mode: bool,
    urgency: str,
    localized_message: str = "",
    source: str,
) -> Dict[str, Any]:
    """Package an uncharged medical-safety response with no astrology content."""
    lang = str(language or "english").strip().lower()
    body = str(localized_message or "").strip()
    if not body and lang.startswith("hi"):
        body = (
            "सीने में दर्द जैसी समस्या मेडिकल इमरजेंसी हो सकती है। ज्योतिष यह तय नहीं कर सकता कि यह गंभीर है या नहीं। "
            "अगर दर्द अभी है, नया या तेज है, बढ़ रहा है, या सांस फूलने, पसीना, मतली, चक्कर, बेहोशी, अथवा बांह, "
            "जबड़े या पीठ में फैलते दर्द के साथ है, तो अभी 112/108 पर कॉल करें या नजदीकी इमरजेंसी विभाग जाएँ। "
            "खुद गाड़ी न चलाएँ। दर्द हल्का हो तब भी आज ही तुरंत चिकित्सा जाँच कराएँ।"
        )
    elif not body:
        body = (
            "Chest pain can be a medical emergency. Astrology cannot determine whether it is serious. "
            "If the pain is happening now, is new, severe, persistent or worsening, or comes with shortness of breath, "
            "sweating, nausea, faintness, or pain spreading to your arm, jaw or back, call emergency services now "
            "(India: 112/108) or go to the nearest emergency department. Do not drive yourself. "
            "Even if it feels mild, seek prompt medical evaluation today."
        )

    response = _conversational_ack_response(language, speech_mode=speech_mode)
    response.update({
        "response": body,
        "raw_response": body,
        "llm_response_chars": len(body),
        "chat_llm_model": "__medical_safety_triage__",
        "follow_up_questions": [],
        "skip_instant_credit_charge": True,
        "instant_evidence_debug": None,
    })
    response["timing"].update({
        "medical_safety_triage": True,
        "medical_urgency": urgency,
        "medical_triage_source": source,
        "calculator_execution_skipped": True,
    })
    response["instant_context_summary"].update({
        "category": "health",
        "answer_mode": "medical_safety_triage",
        "mode": "medical_safety_triage",
    })
    return response


def _instant_route_response(
    *,
    body: str,
    answer_mode: str,
    route_action: str,
    language: str,
    speech_mode: bool,
) -> Dict[str, Any]:
    """Return a router-owned clarification/handoff without running calculators.

    The multilingual LLM router writes ``body``.  This helper only packages it
    into the normal chat response contract and therefore performs no natural-
    language interpretation or generation itself.
    """
    message = str(body or "").strip()
    if not message:
        # This is an exceptional degraded-router fallback, not semantic routing.
        message = (
            "Please ask one clear question at a time so I can calculate it accurately."
            if route_action == "clarify"
            else "Please open the dedicated Partnership experience for this two-chart reading."
        )
    response = _conversational_ack_response(language, speech_mode=speech_mode)
    response.update({
        "response": message,
        "raw_response": message,
        "llm_response_chars": len(message),
        "chat_llm_model": "__instant_semantic_router__",
        "follow_up_questions": [],
        "skip_instant_credit_charge": True,
    })
    response["timing"].update({
        "route_action": route_action,
        "calculator_execution_skipped": True,
    })
    response["instant_context_summary"].update({
        "answer_mode": answer_mode,
        "mode": route_action,
    })
    return response


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


def _target_house_to_native_house(target_house: int, anchor_house: int) -> int:
    """Map a house in a derived-person frame back to the native chart frame."""
    return ((int(anchor_house) - 1 + int(target_house) - 1) % 12) + 1


def _target_focus_calculation_frame(
    target_houses: List[Any], anchor_house: int
) -> tuple[List[int], Dict[int, int]]:
    """Return native calculation houses and their target-relative labels.

    Dasha lords, placements, and aspects belong to the native chart, so the
    calculator must work in native houses.  Category weights and user-facing
    claims belong to the derived person's frame.  Keeping this mapping
    explicit prevents a native house from being silently described as the
    same-numbered spouse/child/parent house.
    """
    native_houses: List[int] = []
    display_map: Dict[int, int] = {}
    for raw_house in target_houses or []:
        target_house = _safe_int(raw_house)
        if target_house is None:
            continue
        native_house = _target_house_to_native_house(target_house, anchor_house)
        native_houses.append(native_house)
        display_map[native_house] = target_house
    return native_houses, display_map


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
    resolved_period = ir.get("period_window") if isinstance(ir.get("period_window"), dict) else {}
    timeframe_text = str(extracted.get("timeframe") or "").strip().lower()
    if not timeframe_text:
        timeframe_text = str(question or "").strip().lower()

    # The LLM intent router owns natural-language interpretation. Once it has
    # classified a request as daily (or supplied an exact-day period), preserve
    # that result here instead of degrading it to the legacy "current" window.
    is_daily_request = bool(
        str(ir.get("mode") or "").strip().upper() == "PREDICT_DAILY"
        or str(resolved_period.get("kind") or "").strip().lower() == "day"
    )
    if is_daily_request:
        target_raw = str(
            resolved_period.get("start")
            or resolved_period.get("date")
            or resolved_period.get("target_date")
            or extracted.get("specific_date")
            or ir.get("dasha_as_of")
            or now_local.strftime("%Y-%m-%d")
        ).strip()
        target = _parse_ymd(target_raw) or now_local.replace(tzinfo=None)
        return {
            "kind": "day",
            "start": target.strftime("%Y-%m-%d"),
            "end": target.strftime("%Y-%m-%d"),
            "span_days": 1,
            "label": target.strftime("%d %B %Y"),
            "use_pd": True,
            "use_sk_pr": True,
        }
    
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


def _is_retrospective_event_request(
    intent: Optional[Dict[str, Any]],
    *,
    answer_mode: str,
    category: str,
    question: str = "",
) -> bool:
    """Resolve retrospective direction, including an explicit-tense safety net.

    The semantic router is authoritative, but a degraded/compact router result
    can occasionally omit its time fields.  An unambiguous English past-event
    construction is safe to recover here; it must not be allowed to fall
    through to a future/current event scan.
    """
    def is_past_value(value: Any) -> bool:
        token = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        return bool(
            token in {"past", "open_past", "historical", "retrospective"}
            or token.startswith(("past_", "historical_", "retrospective_"))
            or token.endswith("_past")
        )

    if str(answer_mode or "") not in {
        "event_prediction", "event_timing", "lifetime_event_timing", "timing_window",
    }:
        return False
    if _normalize_event_category(category) not in {"marriage", "relationship", "love"}:
        return False
    payload = intent if isinstance(intent, dict) else {}
    relation = str(payload.get("time_relation") or "").strip().lower()
    if is_past_value(relation):
        return True
    extracted = payload.get("extracted_context") if isinstance(payload.get("extracted_context"), dict) else {}
    dialogue = (
        extracted.get("instant_dialogue")
        if isinstance(extracted.get("instant_dialogue"), dict)
        else payload.get("dialogue_state") if isinstance(payload.get("dialogue_state"), dict)
        else {}
    )
    known_facts = dialogue.get("known_facts") if isinstance(dialogue.get("known_facts"), dict) else {}
    dialogue_direction = str(
        known_facts.get("timing_type")
        or known_facts.get("timing_direction")
        or known_facts.get("time_relation")
        or known_facts.get("time_direction")
        or ""
    ).strip().lower()
    if is_past_value(dialogue_direction):
        return True
    evidence_plan = payload.get("evidence_plan") if isinstance(payload.get("evidence_plan"), dict) else {}
    for part in evidence_plan.get("question_parts") or []:
        timeframe = part.get("timeframe") if isinstance(part, dict) and isinstance(part.get("timeframe"), dict) else {}
        if is_past_value(timeframe.get("kind")):
            return True
    if any(
        str(need.get("kind") or "").startswith("historical_")
        for need in (evidence_plan.get("evidence_needs") or [])
        if isinstance(need, dict)
    ):
        return True
    normalized_question = " ".join(str(question or "").strip().lower().split())
    return bool(re.search(
        r"\bwhen\s+(?:did|was|were)\b.{0,80}\b(?:married|marriage|wedding)\b",
        normalized_question,
    ))
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
    house_display_map: Optional[Dict[int, int]] = None,
    scan_start: Optional[datetime] = None,
    scan_end: Optional[datetime] = None,
    time_direction: str = "future",
) -> Dict[str, Any]:
    """Rank MD/AD/PD segments in a bounded future or historical range."""
    cat = str(category or "general").lower()
    karakas = EVENT_CATEGORY_KARAKAS.get(cat, frozenset())
    now_local = _as_naive_local_datetime(now_local)
    range_start = _as_naive_local_datetime(scan_start or now_local)
    end_local = _as_naive_local_datetime(scan_end or (now_local + timedelta(days=_INSTANT_EVENT_HORIZON_DAYS)))
    if end_local < range_start:
        range_start, end_local = end_local, range_start
    if raw_periods is not None:
        raw_rows = raw_periods
    else:
        calc = DashaCalculator()
        try:
            raw_rows = calc.get_dasha_periods_for_range(birth_data, range_start, end_local)
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
    display_map = {
        int(native): int(relative)
        for native, relative in (house_display_map or {}).items()
    }

    def display_house(house: int) -> int:
        return display_map.get(int(house), int(house))

    def priority_weight(house: int) -> float:
        return _house_priority_weight(cat, display_house(house))
    house_frame_label = "target-relative focus" if display_map else "focus"
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
        activated_native_focus: set[int] = set()
        score = 0

        for lvl, p, weight in chain:
            if not p:
                continue
            p_row = ((chart_data or {}).get("planets") or {}).get(p) or {}
            natal_house = _norm_house(p_row.get("house"))
            ruled_houses = {_norm_house(h) for h in (house_lordships.get(p) or [])}
            ruled_houses.discard(None)
            if ruled_houses & focus:
                matched = sorted(ruled_houses & focus)
                displayed = [display_house(h) for h in matched]
                bonus = sum(priority_weight(h) for h in matched)
                score += int(round((weight * 2) * bonus))
                activated_native_focus |= set(matched)
                activated_focus |= set(displayed)
                reasons.append(f"{lvl.upper()} {p} rules {house_frame_label} house(s) {displayed}")
            if natal_house and natal_house in focus:
                displayed = display_house(natal_house)
                score += int(round(weight * priority_weight(natal_house)))
                activated_native_focus.add(natal_house)
                activated_focus.add(displayed)
                reasons.append(f"{lvl.upper()} {p} occupies {house_frame_label} house {displayed}")
            if natal_house:
                for fh in focus:
                    if _planet_aspects_house_from(natal_house, fh, p):
                        displayed = display_house(fh)
                        score += int(round(1 * priority_weight(fh)))
                        activated_native_focus.add(fh)
                        activated_focus.add(displayed)
                        reasons.append(f"{lvl.upper()} {p} aspects {house_frame_label} house {displayed} from natal")
                        break
            if p in karakas:
                score += int(round(_planet_priority_weight(cat, p)))
                reasons.append(f"{lvl.upper()} {p} is a category significator")
            top_house_hits = [display_house(h) for h in sorted(ruled_houses & focus) if priority_weight(h) >= 2.5]
            if top_house_hits:
                    score += 2
                    reasons.append(f"{lvl.upper()} {p} links strongly to primary event house(s) {top_house_hits}")
        if len([h for h in activated_focus if _house_priority_weight(cat, h) >= 2.0]) >= 2:
            score += 2
            reasons.append("Multiple category-priority houses are activated together")
        transit_activation: Dict[str, Any] = {
            "natal_permission": bool(activated_native_focus),
            "activation_strength": "background",
            "transit_trigger_windows": [],
            "peak_windows": [],
            "carrier_planets": [],
            "predicted_result_areas": [],
        }
        if transit_calc is not None and ascendant_longitude is not None:
            transit_activation = _segment_transit_activation(
                segment_start=max(st, range_start),
                segment_end=min(en, end_local),
                chain=chain,
                chart_data=chart_data or {},
                house_lordships=house_lordships,
                native_focus_houses={int(h) for h in focus if h is not None},
                activated_native_houses=activated_native_focus,
                display_house=display_house,
                transit_calc=transit_calc,
                ascendant_longitude=ascendant_longitude,
            )
        trigger_windows = list(transit_activation.get("transit_trigger_windows") or [])
        peak_windows = list(transit_activation.get("peak_windows") or [])
        transit_score = max(
            [int(item.get("trigger_score") or 0) for item in trigger_windows] or [0]
        )
        score += transit_score
        for peak in peak_windows[:2]:
            reasons.append(
                f"Dated transit peak {peak.get('start')}–{peak.get('end')}: {peak.get('why')}"
            )
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
                "period_strength": transit_activation.get("activation_strength") or ("weak" if score <= 2 else "normal"),
                "period_label": (
                    "highly active period" if transit_activation.get("activation_strength") == "highly_active"
                    else "active period" if transit_activation.get("activation_strength") == "active"
                    else "background period"
                ),
                "time_status": (
                    "past" if str(time_direction).lower() in {"past", "historical", "retrospective"}
                    else "current" if is_current_chain else "future"
                ),
                "activated_focus_houses": sorted(activated_focus),
                "natal_promise_status": (
                    "supported_by_active_dasha_carriers"
                    if transit_activation.get("natal_permission")
                    else "not_established_for_this_dasha_chain"
                ),
                "activation_strength": transit_activation.get("activation_strength"),
                "transit_trigger_score": transit_score,
                "carrier_planets": transit_activation.get("carrier_planets") or [],
                "transit_trigger_windows": trigger_windows,
                "peak_activation_windows": peak_windows,
                "predicted_result_areas": transit_activation.get("predicted_result_areas") or [],
                "why": "; ".join(list(dict.fromkeys(reasons))[:8]),
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
        "horizon_days": max(0, (end_local - range_start).days),
        "horizon_start": range_start.strftime("%Y-%m-%d"),
        "horizon_end": end_local.strftime("%Y-%m-%d"),
        "time_direction": str(time_direction or "future"),
        "focus_houses": sorted(display_map.values()) if display_map else list(focus_houses),
        "native_calculation_houses": sorted(focus) if display_map else list(focus_houses),
        "house_frame": "target_relative" if display_map else "native",
        "periods": periods,
    }


def _historical_marriage_candidate_pool(
    periods: List[Dict[str, Any]],
    house_lordships: Dict[str, Any],
    *,
    limit: int = 64,
) -> List[Dict[str, Any]]:
    """Preserve marriage-capable life phases before expensive transit scoring.

    A global natal-score cutoff is unsafe for retrospective questions: a
    modest Jupiter-Venus period can acquire decisive historical transit
    confirmation, while repeated Saturn levels can occupy every high natal
    rank before transits are calculated.  Keep a bounded, coverage-oriented
    pool containing the global leaders, every primary marriage AD, and the
    strongest period from each two-year life band.
    """
    rows = [row for row in periods if isinstance(row, dict)]
    if not rows:
        return []

    seventh_lords = {
        str(planet)
        for planet, houses in (house_lordships or {}).items()
        if 7 in {_norm_house(house) for house in (houses or [])}
    }
    primary_antardashas = {"Venus", "Jupiter"} | seventh_lords
    selected: List[Dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def add(row: Dict[str, Any]) -> None:
        key = (
            row.get("start"), row.get("end"), row.get("mahadasha"),
            row.get("antardasha"), row.get("pratyantardasha"),
        )
        if key in seen:
            return
        seen.add(key)
        selected.append(row)

    # Retain the strongest global natal candidates for continuity with the
    # existing scorer, but do not let them be the only periods transit-scored.
    for row in rows[:12]:
        add(row)

    # Venus/Jupiter ADs and the seventh-lord AD are primary marriage delivery
    # phases.  Keep every PD inside them so a strong transit is not discarded
    # merely because its natal-only PD score is modest.
    for row in rows:
        if str(row.get("antardasha") or "") in primary_antardashas:
            add(row)

    # Preserve chronological coverage for an unknown past event instead of
    # allowing one later mahadasha to monopolize the candidate pool.
    band_best: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        start = _parse_ymd(row.get("start"))
        if start is None:
            continue
        band = start.year // 2
        incumbent = band_best.get(band)
        if incumbent is None or int(row.get("relevance_score") or 0) > int(incumbent.get("relevance_score") or 0):
            band_best[band] = row
    for band in sorted(band_best):
        add(band_best[band])

    # The pool is intentionally bounded for Instant latency.  Global leaders
    # are already first; the remaining rows retain primary-AD and life-band
    # coverage in deterministic order.
    return selected[: max(1, int(limit))]


def _historical_marriage_rank_score(
    row: Dict[str, Any],
    house_lordships: Dict[str, Any],
) -> int:
    """Rank past marriage windows without triple-counting one planet's links."""
    houses = {_norm_house(house) for house in (row.get("activated_focus_houses") or [])}
    houses.discard(None)
    score = sum({7: 32, 2: 14, 11: 14, 5: 8}.get(int(house), 0) for house in houses)

    seventh_lords = {
        str(planet)
        for planet, ruled in (house_lordships or {}).items()
        if 7 in {_norm_house(house) for house in (ruled or [])}
    }
    levels = [
        ("MD", str(row.get("mahadasha") or "")),
        ("AD", str(row.get("antardasha") or "")),
        ("PD", str(row.get("pratyantardasha") or "")),
    ]
    # Count each planet once for its natal role. Repetition across levels gets
    # only the small role-specific level bonus below.
    for planet in {planet for _, planet in levels if planet}:
        if planet == "Venus":
            score += 16
        elif planet == "Jupiter":
            score += 12
        elif planet in seventh_lords:
            score += 12
        else:
            score += 4

    level_weights = {"MD": 10, "AD": 16, "PD": 4}
    seventh_level_weights = {"MD": 8, "AD": 6, "PD": 4}
    for level, planet in levels:
        if planet in {"Venus", "Jupiter"}:
            score += level_weights[level]
        if planet in seventh_lords:
            score += seventh_level_weights[level]

    transit_score = max(0, min(14, int(row.get("transit_trigger_score") or 0)))
    score += transit_score * 2
    peaks = [peak for peak in (row.get("peak_activation_windows") or []) if isinstance(peak, dict)]
    if peaks:
        score += 12
        peak_houses = {
            _norm_house(house)
            for peak in peaks
            for house in (peak.get("activated_focus_houses") or [])
        }
        peak_houses.discard(None)
        score += min(8, len(peak_houses) * 2)
    return int(score)


def _rank_historical_marriage_periods(
    periods: List[Dict[str, Any]],
    house_lordships: Dict[str, Any],
    *,
    limit: int = 12,
    phase_bounds: Optional[Dict[tuple[str, str], tuple[str, str]]] = None,
) -> List[Dict[str, Any]]:
    """Put transit-confirmed marriage windows first, then apply the final cap."""
    ranked: List[Dict[str, Any]] = []
    for source in periods:
        if not isinstance(source, dict):
            continue
        row = dict(source)
        row["historical_marriage_rank_score"] = _historical_marriage_rank_score(
            row, house_lordships
        )
        ranked.append(row)

    def confirmed(row: Dict[str, Any]) -> bool:
        return bool(
            int(row.get("transit_trigger_score") or 0) > 0
            and row.get("peak_activation_windows")
        )

    ranked.sort(
        key=lambda row: (
            0 if confirmed(row) else 1,
            -int(row.get("historical_marriage_rank_score") or 0),
            -int(row.get("relevance_score") or 0),
            _parse_ymd(row.get("start")) or datetime.max,
        )
    )
    # One long MD-AD phase contains several adjacent PD rows. Returning three
    # variants of that same phase is false precision and crowds out other
    # genuinely distinct life periods. Lead with the best row from each MD-AD
    # phase, then use alternates only if the caller requests more rows than
    # there are distinct phases.
    def merge_peak_windows(phase_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raw_peaks: List[Dict[str, Any]] = []
        for phase_row in phase_rows:
            for peak in phase_row.get("peak_activation_windows") or []:
                if not isinstance(peak, dict) or _parse_ymd(peak.get("start")) is None:
                    continue
                item = dict(peak)
                item["supporting_pratyantardasha"] = phase_row.get("pratyantardasha")
                raw_peaks.append(item)
        raw_peaks.sort(key=lambda peak: _parse_ymd(peak.get("start")) or datetime.max)

        clusters: List[List[Dict[str, Any]]] = []
        for peak in raw_peaks:
            start = _parse_ymd(peak.get("start"))
            end = _parse_ymd(peak.get("end")) or start
            if not clusters:
                clusters.append([peak])
                continue
            previous_end = max(
                (_parse_ymd(item.get("end")) or _parse_ymd(item.get("start")) or datetime.min)
                for item in clusters[-1]
            )
            if start and start <= previous_end + timedelta(days=30):
                clusters[-1].append(peak)
            else:
                clusters.append([peak])

        merged: List[Dict[str, Any]] = []
        for cluster in clusters:
            strongest = max(
                cluster,
                key=lambda peak: (
                    int(peak.get("trigger_score") or 0),
                    -((_parse_ymd(peak.get("start")) or datetime.max) - datetime.min).days,
                ),
            )
            starts = [_parse_ymd(peak.get("start")) for peak in cluster]
            ends = [_parse_ymd(peak.get("end")) or _parse_ymd(peak.get("start")) for peak in cluster]
            start = min(value for value in starts if value is not None)
            end = max(value for value in ends if value is not None)
            merged.append({
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "probable_peak_date": strongest.get("start"),
                "probable_peak_end": strongest.get("end") or strongest.get("start"),
                "planet": strongest.get("planet"),
                "trigger_score": strongest.get("trigger_score"),
                "strength": strongest.get("strength"),
                "activated_focus_houses": strongest.get("activated_focus_houses") or [],
                "supporting_pratyantardashas": list(dict.fromkeys(
                    str(peak.get("supporting_pratyantardasha") or "")
                    for peak in cluster
                    if peak.get("supporting_pratyantardasha")
                )),
                "why": strongest.get("why"),
                "claim_type": "probable_peak_not_confirmed_event_date",
            })
        merged.sort(key=lambda peak: (-int(peak.get("trigger_score") or 0), str(peak.get("start") or "")))
        return merged[:4]

    def diversify(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        phase_groups: Dict[tuple[str, str], List[Dict[str, Any]]] = {}
        for row in rows:
            phase = (
                str(row.get("mahadasha") or ""),
                str(row.get("antardasha") or ""),
            )
            phase_groups.setdefault(phase, []).append(row)

        phase_leaders: List[Dict[str, Any]] = []
        alternates: List[Dict[str, Any]] = []
        for phase, phase_rows in phase_groups.items():
            leader = dict(phase_rows[0])
            bounds = (phase_bounds or {}).get(phase)
            phase_start = bounds[0] if bounds else min(str(row.get("start") or "") for row in phase_rows)
            phase_end = bounds[1] if bounds else max(str(row.get("end") or "") for row in phase_rows)
            strongest_pd = {
                "start": leader.get("start"),
                "end": leader.get("end"),
                "pratyantardasha": leader.get("pratyantardasha"),
                "rank_score": leader.get("historical_marriage_rank_score"),
            }
            peaks = merge_peak_windows(phase_rows)
            leader.update({
                "start": phase_start,
                "end": phase_end,
                "phase_start": phase_start,
                "phase_end": phase_end,
                "phase_dasha_chain": " - ".join(value for value in phase if value),
                "phase_granularity": "MD_AD",
                "strongest_pd_window": strongest_pd,
                "probable_peak_windows": peaks,
                "peak_activation_windows": peaks,
                "claim_rule": (
                    "The MD-AD dates are the broader marriage-capable phase. Peak dates are probable "
                    "astrological concentrations, not the factual marriage date until the user confirms one."
                ),
            })
            phase_leaders.append(leader)
            alternates.extend(phase_rows[1:])
        return phase_leaders + alternates

    confirmed_rows = [row for row in ranked if confirmed(row)]
    unconfirmed_rows = [row for row in ranked if not confirmed(row)]
    return (diversify(confirmed_rows) + diversify(unconfirmed_rows))[: max(1, int(limit))]


def _build_comparison_option_evidence(
    *,
    evidence_plan: Dict[str, Any],
    birth_data: Dict[str, Any],
    now_local: datetime,
    house_lordships: Dict[str, Any],
    chart_data: Dict[str, Any],
    transit_calc: RealTransitCalculator,
    ascendant_longitude: float,
    current_dashas: Dict[str, Any],
    target_subject: Optional[Dict[str, Any]] = None,
    raw_periods: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compare only the options semantically identified by the LLM router.

    The calculator never interprets the user's wording.  It receives typed
    event profiles from ``question_parts`` and applies a disclosed house/lord/
    significator scoring frame to the same dasha timeline for every option.
    """
    parts = [
        part for part in list((evidence_plan or {}).get("question_parts") or [])
        if isinstance(part, dict) and str(part.get("event_profile") or "").strip()
    ]
    if len(parts) < 2:
        return {}

    duration_months = 36
    for part in parts:
        timeframe = part.get("timeframe") if isinstance(part.get("timeframe"), dict) else {}
        try:
            candidate = int(timeframe.get("duration_months"))
        except (TypeError, ValueError):
            continue
        if candidate > 0:
            duration_months = min(36, candidate)
            break
    month_index = now_local.month - 1 + duration_months
    horizon_year = now_local.year + month_index // 12
    horizon_month = month_index % 12 + 1
    horizon_day = min(now_local.day, monthrange(horizon_year, horizon_month)[1])
    horizon_end = now_local.replace(
        year=horizon_year, month=horizon_month, day=horizon_day
    )

    options: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for part in parts:
        profile = _normalize_event_category(str(part.get("event_profile") or "general"))
        if profile in seen:
            continue
        seen.add(profile)
        focus = CATEGORY_FOCUS.get(profile, CATEGORY_FOCUS["general"])
        try:
            base_house = int((target_subject or {}).get("base_house") or 1)
        except (TypeError, ValueError):
            base_house = 1
        calculation_focus_houses = [
            ((base_house - 1 + int(house) - 1) % 12) + 1
            for house in focus["houses"]
        ]
        scan = _build_forward_event_dasha_scan(
            birth_data=birth_data,
            now_local=now_local,
            house_lordships=house_lordships,
            focus_houses=calculation_focus_houses,
            category=profile,
            chart_data=chart_data,
            transit_calc=transit_calc,
            ascendant_longitude=ascendant_longitude,
            current_dashas=current_dashas,
            raw_periods=raw_periods,
        )
        periods = [
            dict(row) for row in list(scan.get("periods") or [])
            if isinstance(row, dict)
            and str(row.get("end") or "")[:10] >= now_local.strftime("%Y-%m-%d")
            and str(row.get("start") or "")[:10] <= horizon_end.strftime("%Y-%m-%d")
        ]
        for row in periods:
            if str(row.get("start") or "")[:10] < now_local.strftime("%Y-%m-%d"):
                row["start"] = now_local.strftime("%Y-%m-%d")
            if str(row.get("end") or "")[:10] > horizon_end.strftime("%Y-%m-%d"):
                row["end"] = horizon_end.strftime("%Y-%m-%d")
        periods.sort(
            key=lambda row: (
                -int(row.get("relevance_score") or 0),
                str(row.get("start") or ""),
            )
        )
        best = dict(periods[0]) if periods else {}
        current = next(
            (dict(row) for row in periods if row.get("time_status") == "current"),
            {},
        )
        options.append({
            "part_id": part.get("part_id"),
            "label": str(part.get("label") or profile.replace("_", " ")).strip(),
            "event_profile": profile,
            "target_relative_focus_houses": list(focus["houses"]),
            "native_calculation_houses": calculation_focus_houses,
            "best_window": best,
            "current_window": current,
            "peak_score": int(best.get("relevance_score") or 0),
            "method": "Identical MD/AD/PD scan scored for option-specific houses, lordships, natal placements, aspects, significators, and transit reinforcement.",
        })

    ranked = sorted(options, key=lambda row: -int(row.get("peak_score") or 0))
    if len(ranked) < 2 or int(ranked[0].get("peak_score") or 0) <= 0:
        direction = "insufficient_option_evidence"
        favored = None
        gap = 0
    else:
        top = int(ranked[0].get("peak_score") or 0)
        second = int(ranked[1].get("peak_score") or 0)
        gap = top - second
        # Small numerical differences are not treated as a real astrological
        # distinction; this prevents false precision in a conversational reply.
        if gap < max(4, round(top * 0.08)):
            direction = "close_call"
            favored = None
        else:
            direction = "leans_to_option"
            favored = ranked[0].get("event_profile")
    return {
        "as_of": now_local.strftime("%Y-%m-%d"),
        "horizon_end": horizon_end.strftime("%Y-%m-%d"),
        "options": options,
        "comparison": {
            "direction": direction,
            "favored_option": favored,
            "score_gap": gap,
            "instruction": (
                "Scores compare activation strength, not guaranteed real-world outcomes. "
                "Choose an option only when direction is leans_to_option; otherwise describe a close call."
            ),
        },
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
    house_display_map: Optional[Dict[int, int]] = None,
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
        house_display_map=house_display_map,
    )
    if isinstance(segs, dict):
        segs["label"] = "next 3 years"
    return segs


def _natal_longitude_from_planet_row(row: Dict[str, Any]) -> Optional[float]:
    """Return a sidereal natal longitude without assuming every chart payload shape."""
    if not isinstance(row, dict):
        return None
    raw_longitude = row.get("longitude")
    if raw_longitude is not None:
        try:
            return float(raw_longitude) % 360.0
        except (TypeError, ValueError):
            pass
    sign_index = _sign_index_from_row(row)
    if sign_index is None:
        return None
    try:
        degree = float(row.get("degree") or 0.0)
    except (TypeError, ValueError):
        degree = 0.0
    return ((sign_index * 30.0) + degree) % 360.0


def _circular_degree_distance(first: float, second: float) -> float:
    return abs(((float(first) - float(second) + 180.0) % 360.0) - 180.0)


def _transit_scan_step_days(planet: str) -> int:
    """Cadence precise enough to find a trigger without making Instant Chat slow."""
    return {
        "Moon": 1,
        "Sun": 2,
        "Mercury": 2,
        "Venus": 2,
        "Mars": 4,
        "Jupiter": 7,
        "Saturn": 7,
        "Rahu": 7,
        "Ketu": 7,
    }.get(str(planet or ""), 4)


def _segment_transit_activation(
    *,
    segment_start: datetime,
    segment_end: datetime,
    chain: List[tuple[str, str, int]],
    chart_data: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
    native_focus_houses: set[int],
    activated_native_houses: set[int],
    display_house,
    transit_calc: RealTransitCalculator,
    ascendant_longitude: float,
) -> Dict[str, Any]:
    """Find dated transit triggers only after a dasha carrier has natal permission.

    Transit does not create an event promise. A MD/AD/PD planet first has to
    connect to a requested house by natal lordship, occupation, or aspect. We
    then scan its transit for delivery to those houses and for repetition of
    its own natal position/sign/nakshatra pattern.
    """
    planets = (chart_data.get("planets") or {}) if isinstance(chart_data, dict) else {}
    carriers: Dict[str, Dict[str, Any]] = {}
    for level, planet, _weight in chain:
        if not planet or planet not in planets:
            continue
        natal = planets.get(planet) or {}
        natal_house = _norm_house(natal.get("house"))
        ruled = {_norm_house(h) for h in (house_lordships.get(planet) or [])}
        ruled.discard(None)
        natal_aspects = {
            house for house in native_focus_houses
            if natal_house and _planet_aspects_house_from(natal_house, house, planet)
        }
        natal_links = (ruled & native_focus_houses) | (
            {natal_house} if natal_house in native_focus_houses else set()
        ) | natal_aspects
        if not natal_links:
            # A natural/category significator can describe an event, but it
            # cannot open that event for timing by itself.
            continue
        # The verdict only consumes links to the requested career houses, but
        # the explanation must retain the planet's complete natal activation
        # pattern. Otherwise a Saturn MD/PD can appear to activate only the
        # career subset even though its occupation, lordships and aspects also
        # activate houses such as 4, 7 and 8.
        all_natal_aspects = {
            house for house in range(1, 13)
            if natal_house and _planet_aspects_house_from(natal_house, house, planet)
        }
        all_natal_links = set(ruled) | all_natal_aspects
        if natal_house:
            all_natal_links.add(natal_house)
        event_links = []
        for house in sorted(all_natal_links):
            mechanisms = []
            if house in ruled:
                mechanisms.append("lordship")
            if natal_house == house:
                mechanisms.append("natal_occupation")
            if house in all_natal_aspects:
                mechanisms.append("natal_aspect")
            event_links.append({
                "house": display_house(house),
                "native_house": house,
                "mechanisms": mechanisms,
            })
        carrier = carriers.setdefault(planet, {
            "planet": planet,
            "levels": [],
            "natal_house": natal_house,
            "natal_longitude": _natal_longitude_from_planet_row(natal),
            "natal_event_houses": set(),
            "event_links": event_links,
        })
        carrier["levels"].append(level.upper())
        carrier["natal_event_houses"].update(natal_links)

    if not carriers:
        return {
            "natal_permission": False,
            "activation_strength": "not_established",
            "carrier_planets": [],
            "transit_trigger_windows": [],
            "peak_windows": [],
            "predicted_result_areas": [],
            "method_note": "No active dasha planet has a natal link to the requested event houses; transit cannot create the promise.",
        }

    snapshots: List[Dict[str, Any]] = []
    position_cache: Dict[tuple[str, str], Optional[float]] = {}
    for planet, carrier in carriers.items():
        step_days = _transit_scan_step_days(planet)
        sample_at = segment_start
        sample_dates: List[datetime] = []
        while sample_at <= segment_end:
            sample_dates.append(sample_at)
            sample_at += timedelta(days=step_days)
        if not sample_dates or sample_dates[-1].date() != segment_end.date():
            sample_dates.append(segment_end)

        natal_house = carrier.get("natal_house")
        natal_longitude = carrier.get("natal_longitude")
        event_houses = set(carrier.get("natal_event_houses") or set())
        event_houses.update(activated_native_houses & native_focus_houses)
        for sample in sample_dates:
            cache_key = (planet, sample.strftime("%Y-%m-%d"))
            if cache_key not in position_cache:
                try:
                    position_cache[cache_key] = transit_calc.get_planet_position(sample, planet)
                except Exception:
                    position_cache[cache_key] = None
            longitude = position_cache[cache_key]
            if longitude is None:
                continue
            transit_house = _norm_house(
                transit_calc.calculate_house_from_longitude(longitude, ascendant_longitude)
            )
            trigger_kinds: List[str] = []
            labels: List[str] = []
            primary_score = 0
            secondary_score = 0
            delivered = {
                house for house in event_houses
                if transit_house and (
                    transit_house == house
                    or _planet_aspects_house_from(transit_house, house, planet)
                )
            }
            if delivered:
                trigger_kinds.append("event_house_delivery")
                labels.append(
                    f"{planet} delivers its natal dasha promise to event house(s) "
                    f"{[display_house(h) for h in sorted(delivered)]}"
                )
                primary_score += 2
            if natal_house and transit_house == natal_house:
                trigger_kinds.append("natal_sign_return")
                labels.append(f"{planet} returns to its natal sign/house")
                primary_score += 3
            elif natal_house and transit_house and _planet_aspects_house_from(
                transit_house, natal_house, planet
            ):
                trigger_kinds.append("own_natal_aspect")
                labels.append(f"{planet} re-aspects its natal position")
                primary_score += 3
            if natal_longitude is not None:
                if _circular_degree_distance(float(longitude), natal_longitude) <= 1.0:
                    trigger_kinds.append("exact_degree_return")
                    labels.append(f"{planet} is within 1 degree of its natal longitude")
                    primary_score += 5
                relation = nakshatra_transit_relation(natal_longitude, float(longitude))
                if relation and relation.get("relation") == "exact_natal_nakshatra_return":
                    trigger_kinds.append("exact_natal_nakshatra_return")
                    labels.append(
                        f"{planet} returns to natal {relation['natal_nakshatra']['name']} nakshatra"
                    )
                    primary_score += 4
                elif relation and relation.get("relation") == "nakshatra_dispositor_resonance":
                    trigger_kinds.append("same_nakshatra_lord")
                    labels.append(
                        f"{planet} transits a nakshatra ruled by its natal nakshatra lord "
                        f"{relation.get('common_nakshatra_lord')}"
                    )
                    secondary_score += 1
            if not trigger_kinds:
                continue
            direct_contact = any(kind in trigger_kinds for kind in (
                "natal_sign_return", "own_natal_aspect", "exact_degree_return",
                "exact_natal_nakshatra_return",
            ))
            strength = (
                "high" if direct_contact or (delivered and "same_nakshatra_lord" in trigger_kinds)
                else "medium" if delivered
                else "secondary"
            )
            delivered_details = [
                {
                    "house": display_house(house),
                    "native_house": house,
                    "mechanism": "transit_occupation" if transit_house == house else "transit_aspect",
                    "aspect_number": (
                        None if transit_house == house
                        else _planet_aspect_number_from(transit_house, house, planet)
                    ),
                }
                for house in sorted(delivered)
            ]
            snapshots.append({
                "start": sample.strftime("%Y-%m-%d"),
                "end": sample.strftime("%Y-%m-%d"),
                "planet": planet,
                "dasha_levels": list(dict.fromkeys(carrier.get("levels") or [])),
                "trigger_kinds": list(dict.fromkeys(trigger_kinds)),
                "strength": strength,
                "trigger_score": primary_score + secondary_score,
                "transit_native_house": transit_house,
                "natal_placement_house": natal_house,
                "natal_reaspect_number": (
                    _planet_aspect_number_from(transit_house, natal_house, planet)
                    if "own_natal_aspect" in trigger_kinds else None
                ),
                "carrier_event_houses": [display_house(h) for h in sorted(event_houses)],
                "delivered_event_houses": delivered_details,
                "activated_focus_houses": [display_house(h) for h in sorted(delivered or event_houses)],
                "why": "; ".join(labels),
                "sample_cadence_days": step_days,
            })

    # Consecutive observations of the same astronomical condition become a
    # conservative date band instead of dozens of noisy daily evidence rows.
    snapshots.sort(key=lambda row: (row["planet"], row["start"], row["trigger_kinds"]))
    windows: List[Dict[str, Any]] = []
    for row in snapshots:
        previous = windows[-1] if windows else None
        previous_end = _parse_ymd(previous.get("end")) if previous else None
        current_start = _parse_ymd(row.get("start"))
        can_merge = bool(
            previous
            and previous.get("planet") == row.get("planet")
            and previous.get("trigger_kinds") == row.get("trigger_kinds")
            and previous_end
            and current_start
            and (current_start - previous_end).days <= int(row.get("sample_cadence_days") or 1) + 1
        )
        if can_merge:
            previous["end"] = row["end"]
            previous["trigger_score"] = max(previous["trigger_score"], row["trigger_score"])
            if row["strength"] == "high":
                previous["strength"] = "high"
        else:
            windows.append(dict(row))

    windows.sort(key=lambda row: (
        {"high": 0, "medium": 1, "secondary": 2}.get(str(row.get("strength")), 3),
        -int(row.get("trigger_score") or 0),
        str(row.get("start") or ""),
    ))
    peak_windows = [row for row in windows if row.get("strength") == "high"][:5]
    active_windows = [row for row in windows if row.get("strength") in {"high", "medium"}]
    overall_strength = "highly_active" if peak_windows else "active" if active_windows else "background"
    result_houses = sorted({
        int(house)
        for row in (peak_windows or active_windows)
        for house in (row.get("activated_focus_houses") or [])
        if _norm_house(house) is not None
    })
    return {
        "natal_permission": True,
        "activation_strength": overall_strength,
        "carrier_planets": [
            {
                "planet": row["planet"],
                "dasha_levels": list(dict.fromkeys(row["levels"])),
                "natal_placement_house": row.get("natal_house"),
                "natal_event_houses": [display_house(h) for h in sorted(row["natal_event_houses"])],
                "event_links": list(row.get("event_links") or []),
            }
            for row in carriers.values()
        ],
        "transit_trigger_windows": windows[:10],
        "peak_windows": peak_windows,
        "predicted_result_areas": [
            {"house": house, "theme": SPEECH_HOUSE_THEME_LABELS.get(house, HOUSE_THEME_LABELS.get(house, "life results"))}
            for house in result_houses
        ],
        "method_note": (
            "Transit windows are confirmations of natal dasha permission, not independent promises. "
            "Exact natal/nakshatra contacts are primary; same-nakshatra-lord resonance is secondary unless it also delivers to an activated event house."
        ),
    }


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
    house_display_map: Optional[Dict[int, int]] = None,
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
    display_map = {
        int(native): int(relative)
        for native, relative in (house_display_map or {}).items()
    }

    def display_house(house: int) -> int:
        return display_map.get(int(house), int(house))

    def priority_weight(house: int) -> float:
        return _house_priority_weight(cat, display_house(house))
    house_frame_label = "target-relative focus" if display_map else "focus"
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
        activated_native_focus: set[int] = set()
        reasons: List[str] = []
        score = 0

        for lvl, p, weight in chain:
            if not p:
                continue
            p_row = ((chart_data.get("planets") or {}).get(p) or {})
            natal_house = _norm_house(p_row.get("house"))
            ruled_houses = {_norm_house(h) for h in (house_lordships.get(p) or [])}
            ruled_houses.discard(None)
            if ruled_houses & focus:
                matched = sorted(ruled_houses & focus)
                displayed = [display_house(h) for h in matched]
                bonus = sum(priority_weight(h) for h in matched)
                score += int(round((weight * 2) * bonus))
                activated_native_focus |= set(matched)
                activated_focus |= set(displayed)
                reasons.append(f"{lvl.upper()} {p} rules {house_frame_label} house(s) {displayed}")
            if natal_house and natal_house in focus:
                displayed = display_house(natal_house)
                score += int(round(weight * priority_weight(natal_house)))
                activated_native_focus.add(natal_house)
                activated_focus.add(displayed)
                reasons.append(f"{lvl.upper()} {p} occupies {house_frame_label} house {displayed}")
            if natal_house:
                for fh in focus:
                    if _planet_aspects_house_from(natal_house, fh, p):
                        displayed = display_house(fh)
                        score += int(round(1 * priority_weight(fh)))
                        activated_native_focus.add(fh)
                        activated_focus.add(displayed)
                        reasons.append(f"{lvl.upper()} {p} aspects {house_frame_label} house {displayed} from natal")
                        break
            if p in karakas:
                score += int(round(_planet_priority_weight(cat, p)))
                reasons.append(f"{lvl.upper()} {p} is a category significator")
            top_house_hits = [display_house(h) for h in sorted(ruled_houses & focus) if priority_weight(h) >= 2.5]
            if top_house_hits:
                score += 2
                reasons.append(f"{lvl.upper()} {p} links strongly to primary event house(s) {top_house_hits}")

        if len([h for h in activated_focus if _house_priority_weight(cat, h) >= 2.0]) >= 2:
            score += 2
            reasons.append("Multiple category-priority houses are activated together")

        scan_start = max(s, start_dt)
        scan_end = min(e, end_dt)
        transit_activation = _segment_transit_activation(
            segment_start=scan_start,
            segment_end=scan_end,
            chain=chain,
            chart_data=chart_data,
            house_lordships=house_lordships,
            native_focus_houses={int(h) for h in focus if h is not None},
            activated_native_houses=activated_native_focus,
            display_house=display_house,
            transit_calc=transit_calc,
            ascendant_longitude=ascendant_longitude,
        )
        peak_windows = list(transit_activation.get("peak_windows") or [])
        trigger_windows = list(transit_activation.get("transit_trigger_windows") or [])
        transit_score = max(
            [int(item.get("trigger_score") or 0) for item in trigger_windows] or [0]
        )
        score += transit_score
        if peak_windows:
            for peak in peak_windows[:2]:
                reasons.append(
                    f"Dated transit peak {peak.get('start')}–{peak.get('end')}: {peak.get('why')}"
                )

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
                "natal_promise_status": (
                    "supported_by_active_dasha_carriers"
                    if transit_activation.get("natal_permission")
                    else "not_established_for_this_dasha_chain"
                ),
                "activation_strength": transit_activation.get("activation_strength"),
                "transit_trigger_score": transit_score,
                "activated_focus_houses": sorted(activated_focus),
                "carrier_planets": transit_activation.get("carrier_planets") or [],
                "transit_trigger_windows": trigger_windows,
                "peak_activation_windows": peak_windows,
                "predicted_result_areas": transit_activation.get("predicted_result_areas") or [],
                "why": "; ".join(list(dict.fromkeys(reasons))[:8]),
            }
        )

    segs.sort(key=lambda r: (-int(r.get("relevance_score") or 0), r.get("start") or ""))
    all_peaks = [
        {**peak, "dasha_segment_start": seg.get("start"), "dasha_segment_end": seg.get("end")}
        for seg in segs
        for peak in (seg.get("peak_activation_windows") or [])
    ]
    all_peaks.sort(key=lambda row: (-int(row.get("trigger_score") or 0), str(row.get("start") or "")))
    return {
        "enabled": bool(segs),
        "focus_houses": sorted(display_map.values()) if display_map else sorted([h for h in focus if h is not None]),
        "native_calculation_houses": sorted([h for h in focus if h is not None]) if display_map else [],
        "house_frame": "target_relative" if display_map else "native",
        "segments": segs[:limit],
        "activation_timeline": {
            "method": "natal promise -> dasha permission -> dated transit trigger -> real-life result area",
            "peak_windows": all_peaks[:8],
            "high_activity_claim_gate": "A period may be called highly active only when natal dasha permission and a primary dated transit trigger are both present.",
        },
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


_PROTECTED_CHART_FACT_OVERRIDE_MODES = {
    "comparison_choice",
    "dedicated_partnership_flow",
    "compound_plan",
    "dedicated_muhurat_flow",
    "location_recommendation",
    "remedy_action",
    "timing_window",
    "event_prediction",
    "explanation_mechanism",
}


def _llm_explicit_chart_focus(intent: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return LLM-emitted explicit chart_focus only. Do not parse user wording."""
    focus = (intent or {}).get("chart_focus") if isinstance((intent or {}).get("chart_focus"), dict) else {}
    if focus.get("explicit") and (focus.get("primary") or focus.get("requested")):
        return focus
    return None


def _llm_chart_fact_evidence_family(intent: Optional[Dict[str, Any]]) -> bool:
    evidence_plan = (intent or {}).get("evidence_plan") if isinstance((intent or {}).get("evidence_plan"), dict) else {}
    for part in evidence_plan.get("question_parts") or []:
        if not isinstance(part, dict):
            continue
        families = part.get("intent_families") or []
        if any(str(family or "").strip() == "factual_chart_lookup" for family in families):
            return True
    return False


def _apply_llm_chart_fact_mode_guard(
    mode: str,
    intent: Optional[Dict[str, Any]] = None,
) -> str:
    """Protect explicit named-chart reads without erasing semantic intent.

    ``chart_focus`` describes which chart the user named; it does not by
    itself describe the question being asked about that chart.  In
    particular, a natal-promise question may legitimately request D9 as
    evidence and must remain ``potential_capacity``.  Only generic topic or
    trait classifications are safe to repair into a named-chart read here.
    """
    resolved = str(mode or "").strip() or "topic_reading"
    if resolved in _PROTECTED_CHART_FACT_OVERRIDE_MODES:
        return resolved
    if resolved == "factual_chart_lookup":
        return resolved
    if _llm_explicit_chart_focus(intent) or _llm_chart_fact_evidence_family(intent):
        if resolved in {"topic_reading", "trait_nature"}:
            return "factual_chart_lookup"
    return resolved


def _explicit_remedy_followup_requested(
    intent: Optional[Dict[str, Any]],
    question: str = "",
) -> bool:
    """True for a CTA breadcrumb or the router's explicit semantic remedy decision."""
    from utils.query_context import is_remedy_chain_question, is_remedy_followup_request

    return is_remedy_followup_request(intent) or is_remedy_chain_question(question)


def _clamp_remedy_answer_mode(
    mode: str,
    intent: Optional[Dict[str, Any]],
    question: str = "",
) -> str:
    """Reject accidental remedy modes, while allowing explicit multilingual remedy asks."""
    resolved = str(mode or "").strip() or "topic_reading"
    if resolved == "remedy_action" and not _explicit_remedy_followup_requested(intent, question):
        if _looks_like_problem_question(question) or _looks_like_remedy_question(question):
            return "problem_diagnosis"
        return "topic_reading"
    return resolved


def _looks_like_potential_question(question: str, intent: Optional[Dict[str, Any]]) -> bool:
    q = str(question or "").lower()
    cat = str((intent or {}).get("category") or "").lower()
    chart_context = any(term in q for term in ("birth chart", "kundli", "kundali", "horoscope"))
    promise_language = any(term in q for term in ("possibility", "possibilities", "possible", "promise", "promised"))
    if chart_context and promise_language:
        return True
    markers = [
        "potential", "suited", "good for", "best for", "can i become", "aptitude",
        "strength", "talent", "capacity", "suitable", "promise", "prospects",
        "possibility in my chart", "possibility in my birth chart", "possibility in my kundli",
        "possibility in my kundali", "possible in my chart", "possible in my kundli",
        "possible in my kundali", "possibilities in my chart",
        "possibilities in my birth chart", "possibilities in my kundli",
        "possibilities in my kundali", "possibilities of marriage in my chart",
        "possibilities of marriage in my birth chart", "possibilities of marriage in my kundli",
        "possibilities of marriage in my kundali",
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
    if _explicit_remedy_followup_requested(intent, question):
        return "remedy_action"
    if _apply_llm_chart_fact_mode_guard(str((intent or {}).get("answer_mode") or "topic_reading"), intent) == "factual_chart_lookup":
        return "factual_chart_lookup"
    if _looks_like_explanatory_followup(question, history):
        return "explanation_mechanism"
    if _looks_like_comparison_question(question):
        return "comparison_choice"
    if _looks_like_problem_question(question):
        return "problem_diagnosis"
    if _looks_like_relationship_person_question(question):
        return "relationship_person"
    if _looks_like_personality_question(question):
        return "trait_nature"
    # The multilingual LLM router is authoritative. This fallback ordering is
    # intentionally narrow: an explicit "in my birth chart/kundali" promise
    # question is natal capacity even when it contains words such as
    # possibility or marriage. It must be resolved before event timing.
    if _looks_like_potential_question(question, intent):
        return "potential_capacity"
    if _looks_like_open_ended_life_event_when(question, intent):
        return "event_prediction"
    if _looks_like_timing_window_question(question, intent):
        return "timing_window"
    # This is only the deterministic outage fallback. The multilingual LLM
    # router remains authoritative, but a chart-promise question must not be
    # degraded into event timing merely because it contains "possibility".
    if _looks_like_event_prediction_question(question, intent):
        return "event_prediction"
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
        "explicit_remedy_request": bool(intent.get("explicit_remedy_request")),
        "needs_transits": bool(intent.get("needs_transits")),
        "context_type": str(intent.get("context_type") or ""),
        "chart_focus": intent.get("chart_focus") if isinstance(intent.get("chart_focus"), dict) else None,
        "requested_chart": ((intent.get("extracted_context") or {}) if isinstance(intent.get("extracted_context"), dict) else {}).get("requested_chart"),
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
- factual_chart_lookup: the asked object is a named chart or calculated fact, in any language/script. If INPUT.chart_focus.explicit is true or requested_chart is a named varga/Karkamsa/Swamsa, prefer this over family/career/soul topic_reading. A period outlook that only mentions a varga stays timing_window.
- explanation_mechanism: user asks how/why a prior chart claim was made
- trait_nature: user asks about behavior, nature, speech, temperament, personality
- relationship_person: user asks about the nature/characteristics of spouse/partner/person
- timing_window: user asks how a named calendar window feels overall (this month, next six months, October 2026) without a single concrete life-event line as the main ask
- event_prediction: user asks whether/when one specific event will materialize in time (e.g. "Will I marry this person?", "When will I get married?", "Will I get this job this year?"); prefer this over timing_window even if they add "this year" or similar
- potential_capacity: user asks what the natal/birth chart promises or permits, or asks suitability, aptitude, fit or sustainable capacity. A question such as "Is marriage possible in my birth chart/kundali?" belongs here, not event_prediction: it asks for natal marriage promise, not a calendar prediction.
- comparison_choice: user asks between two or more options
- problem_diagnosis: user asks why something is blocked, unstable, delayed, leaking, or difficult
- remedy_action: choose this when the primary semantic router set explicit_remedy_request=true, or when the client marked a Remedies CTA follow-up. Do not choose it for vague general advice such as "what should I do?".
- topic_reading: default focused reading when none of the above fit best
- location_recommendation: where/place/direction recommendation for a stated life goal; this is distinct from event timing
- dedicated_muhurat_flow: best date/time for an action; requires the event, location/timezone and usable date range
- dedicated_partnership_flow: two-chart compatibility; Instant must hand this to Partnership mode and must not calculate it
- compound_plan: two or more materially different questions; ask the user to send only one question first and do not calculate

Routing action:
- `answer`: the question is single, sufficiently clear and can enter its calculator flow.
- `clarify`: a material fact is missing, or answer_mode is compound_plan. Write one short natural clarification in the user's language.
- `handoff`: answer_mode is dedicated_partnership_flow. Write one short natural message in the user's language directing them to Partnership mode.
- For dedicated_muhurat_flow, clarify if event, location/timezone, or date range is missing; otherwise answer through that dedicated flow.
- For location_recommendation, clarify only when the goal or requested scope is materially missing.
- Do not classify a question as compound merely because it needs several astrology calculations. It must contain materially different user asks.

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
{{"answer_mode":"one_of_the_allowed_modes","route_action":"answer|clarify|handoff","confidence":"high|medium|low","reason":"very short reason","target_subject_key":"allowed_target_or_self","needs_year_clarification":true_or_false,"user_message":"required for clarify or handoff; same language as user"}}

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
    model_name = get_instant_chat_model()
    instant_provider = get_instant_chat_llm_provider()

    def _pack(mode: str, target_subject: Optional[Dict[str, Any]] = None, **extra: Any) -> Dict[str, Any]:
        resolved_mode = _apply_llm_chart_fact_mode_guard(
            _clamp_remedy_answer_mode(mode, intent, question),
            intent,
        )
        return {
            "raw_answer_mode": str(mode or "topic_reading"),
            "answer_mode": resolved_mode,
            "target_subject": target_subject or _fallback_target_subject(question),
            "router_source": "secondary_answer_mode_llm",
            **extra,
        }

    try:
        llm_result = await analyzer.generate_text_from_prompt(
            prompt,
            premium_analysis=False,
            model_override=None,
            model_name_override=model_name,
            llm_log_tag="instant_answer_mode",
            request_timeout_s=_instant_timeout_seconds(
                "INSTANT_CHAT_ROUTER_TIMEOUT_SECONDS",
                10.0,
                maximum=20.0,
            ),
            force_gemini=False,
            provider_override=instant_provider,
            use_gemini_rest=instant_provider == CHAT_LLM_GEMINI,
            gemini_thinking_level=(
                _instant_thinking_level(model_name) if instant_provider == CHAT_LLM_GEMINI else None
            ),
            deepseek_thinking_enabled=(
                False if instant_provider == CHAT_LLM_DEEPSEEK else None
            ),
        )
    except Exception as exc:
        logger.warning("instant answer mode llm classification failed: %s", exc)
        return _pack(
            "topic_reading",
            route_action="answer",
            router_degraded=True,
            router_source="secondary_answer_mode_llm_error_fallback",
            router_reason=f"{type(exc).__name__}: {str(exc)[:160]}",
        )
    if not llm_result.get("success"):
        logger.warning("instant answer mode llm classification unsuccessful: %s", llm_result.get("error"))
        return _pack(
            "topic_reading",
            route_action="answer",
            router_degraded=True,
            router_source="secondary_answer_mode_llm_error_fallback",
            router_reason=str(llm_result.get("error") or "unsuccessful classification")[:180],
        )
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
            route_action = str(data.get("route_action") or "answer").strip().lower()
            if route_action not in {"answer", "clarify", "handoff"}:
                route_action = "answer"
            if mode == "compound_plan":
                route_action = "clarify"
            elif mode == "dedicated_partnership_flow":
                route_action = "handoff"
            return _pack(
                mode,
                target_subject,
                needs_year_clarification=needs_year_clarification,
                route_action=route_action,
                user_message=str(data.get("user_message") or "").strip(),
                router_confidence=str(data.get("confidence") or "medium").strip().lower(),
                router_reason=str(data.get("reason") or "").strip(),
            )
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
            return _pack(
                mode,
                target_subject,
                needs_year_clarification=needs_year_clarification,
                route_action="answer",
                router_source="secondary_answer_mode_llm_regex_recovery",
                router_confidence="low",
                router_reason="Recovered answer_mode from non-conforming LLM output.",
            )
    logger.warning("instant answer mode llm output invalid, falling back: %s", _truncate(raw, 240))
    return _pack(
        "topic_reading",
        needs_year_clarification=False,
        route_action="answer",
        router_degraded=True,
        router_source="secondary_answer_mode_llm_invalid_fallback",
        router_confidence="low",
        router_reason="Invalid answer-mode LLM output.",
    )


def _mode_selection_from_intent(
    intent: Optional[Dict[str, Any]],
    question: str = "",
) -> Optional[Dict[str, Any]]:
    if not isinstance(intent, dict):
        return None
    raw_mode = str(intent.get("answer_mode") or "").strip()
    if raw_mode not in ANSWER_MODES:
        return None
    mode = raw_mode
    requested_object = str(intent.get("requested_object") or "").strip().lower()
    # Validate the primary LLM's semantic fields against one another. This is
    # intentionally not a keyword parser: the LLM identifies the requested
    # object in every supported language. A lived outcome cannot become a
    # chart-fact lookup merely because its supporting chart was named.
    if mode == "factual_chart_lookup" and requested_object and requested_object != "named_chart":
        if str(intent.get("mode") or "").strip() == "ANALYZE_TOPIC_POTENTIAL":
            mode = "potential_capacity"
        else:
            mode = "topic_reading"
    # The intent router sometimes labels a request for a named life event's
    # future window as the generic ``timing_window`` mode.  Do not interpret
    # the user's wording here (that would be language-specific and brittle).
    # Instead, honor the router's structured evidence contract: requesting
    # event-window calculators means the event-prediction pipeline must run.
    evidence_plan = intent.get("evidence_plan") if isinstance(intent.get("evidence_plan"), dict) else {}
    evidence_kinds = {
        str(item.get("kind") or "").strip()
        for item in (evidence_plan.get("evidence_needs") or [])
        if isinstance(item, dict)
    }
    question_families = {
        str(family or "").strip()
        for part in (evidence_plan.get("question_parts") or [])
        if isinstance(part, dict)
        for family in (part.get("intent_families") or [])
    }
    # Only an actual event-timing intent should enter the event scanner. A
    # period/topic outlook may still request transit context, but that does not
    # turn "which health area" into "when will recovery happen".
    event_timing_contract = bool(
        str(intent.get("mode") or "").strip().upper()
        in {"LIFESPAN_EVENT_TIMING", "PREDICT_EVENT_TIMING"}
        or "event_timing" in question_families
        or any(
            value in evidence_kinds
            for value in {
                "future_dasha_event_windows",
                "historical_dasha_event_windows",
                "historical_transit_event_windows",
            }
        )
    )
    # A new life-event timing request cannot coherently be an explanation of a
    # prior answer. Providers occasionally emit that contradictory pair even
    # while correctly returning LIFESPAN_EVENT_TIMING and open_past. Preserve
    # explanation mode only for a genuine follow-up turn.
    turn_relation = str(intent.get("turn_relation") or "new_request").strip().lower()
    explicit_retrospective_question = bool(re.search(
        r"\bwhen\s+(?:did|was|were)\b.{0,80}\b(?:married|marriage|wedding)\b",
        " ".join(str(question or "").strip().lower().split()),
    ))
    if mode in {"timing_window", "problem_diagnosis", "explanation_mechanism"} and (
        event_timing_contract
        and (turn_relation != "follow_up" or explicit_retrospective_question)
    ):
        mode = "event_prediction"
    mode = _clamp_remedy_answer_mode(
        mode,
        intent,
        question or str(intent.get("original_question") or ""),
    )
    mode = _apply_llm_chart_fact_mode_guard(mode, intent)
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
        "raw_answer_mode": raw_mode,
        "answer_mode": mode,
        "requested_object": requested_object or None,
        "target_subject": target_subject,
        "router_source": "primary_intent_llm",
        "router_confidence": str(intent.get("answer_mode_confidence") or intent.get("confidence") or "medium").strip().lower(),
        "router_reason": str(intent.get("answer_mode_reason") or intent.get("reason") or "").strip(),
        "router_degraded": False,
        "needs_year_clarification": bool(intent.get("needs_year_clarification")),
        "route_action": str(intent.get("route_action") or "answer").strip().lower(),
        "user_message": str(intent.get("clarification_question") or intent.get("route_message") or "").strip(),
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
    elif answer_mode == "factual_chart_lookup":
        base.update(
            {
                "primary_evidence": ["chart_facts", "requested_charts", "chart_focus"],
                "secondary_evidence": ["natal_snapshot", "karaka_evidence"],
                "avoid_drift": [
                    "current dasha dominating the answer",
                    "planet-by-planet placement dump as the whole answer",
                    "generic varga textbook essay without citing this chart's data",
                    "D1 dasha or transits as the prediction engine",
                    "inventing placements not present in chart_facts",
                ],
                "answer_skeleton": (
                    "Direct prediction in this named chart's life area -> Lagna and lagna-lord result -> "
                    "Two strongest supported outcomes -> One main caution -> One compact proof from this chart"
                ),
            }
        )
    elif answer_mode == "timing_window":
        period_kind = str((period_window or {}).get("kind") or "")
        span_days = int((period_window or {}).get("span_days") or 0)
        if period_kind == "day":
            skeleton = "Plain-language day verdict with Exact date anchor -> What the user is likely to experience -> Best use and caution -> At most one compact Sookshma/Prana astrological reason"
            avoid_drift = ["broad lifetime reading", "month/year generalization", "natal-only reading", "overstating one day as destiny"]
        elif span_days >= 180:
            skeleton = "Plain-language year verdict (Year verdict) -> Concrete likely outcomes in the asked life area -> Stronger and weaker phases -> Practical use -> At most one compact astrological reason"
            avoid_drift = ["broad lifetime reading", "single-day transit overreach", "one static dasha summary for the whole year", "unanchored natal-only reading"]
        else:
            skeleton = "Plain-language period verdict -> Concrete likely outcomes in the asked life area -> Stronger and more demanding phases -> Practical use -> At most one compact MD/AD/PD astrological reason"
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
                "primary_evidence": ["natal_promise", "topic_signals", "divisional_support.topic", "natal_snapshot"],
                "secondary_evidence": [],
                "avoid_drift": [
                    "current dasha or transit being used to establish natal promise",
                    "active houses being upgraded into event certainty",
                    "daily transit narration",
                    "timing claims when timing was not asked",
                ],
                "answer_skeleton": "Clear natal-promise verdict -> Direct natal support -> Direct natal limitation -> Practical next question",
            }
        )
        if cat in {"marriage", "love", "relationship", "partner", "spouse"}:
            base["answer_skeleton"] = (
                "Clear marriage-promise verdict -> D1 seventh-house/lord basis -> D9 confirmation or qualification -> "
                "Main obstruction/condition -> Ask whether the user wants timing or has a specific relationship concern"
            )
            base["avoid_drift"] = list(base["avoid_drift"]) + [
                "using only houses 2 or 8 to declare marriage promised",
                "claiming an unconventional spouse or sudden marriage merely from Rahu",
                "calling marriage definite when D1 and D9 evidence is incomplete",
            ]
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
                    "replacing remedies with forecasts or favorable dates",
                    "calling ordinary career advice the remedy",
                ],
                "answer_skeleton": "One-sentence astrological pressure -> Three prioritized remedies, each stating what to do, how often, and why it fits the chart -> One safety or practicality caution -> One natural follow-up question",
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
    if is_career_category(cat):
        profile = career_profile(cat)
        career_contract = build_career_answer_contract(answer_mode, profile["subtype"])
        base["career_contract"] = career_contract
        base["answer_skeleton"] = career_contract["required_shape"]
        family = str(career_contract.get("question_family") or "profile")
        evidence_by_family = {
            "profile": ["career_foundation"],
            "vocation": ["career_foundation"],
            "diagnosis": ["career_foundation", "current_timing", "active_areas"],
            "timing": ["career_foundation", "career_manifestations", "transit_activation_timeline"],
            "comparison": ["career_foundation", "option_comparison"],
            "decision": ["career_foundation", "career_decision", "current_timing"],
            "remedy": ["remedy_blueprint"],
        }
        base["primary_evidence"] = evidence_by_family.get(family, ["career_foundation"])
        career_avoid_drift = [
            career_contract.get(key)
            for key in (
                "career_not_wealth_rule",
                "event_certainty_rule",
                "diagnosis_rule",
                "recognition_rule",
                "decision_rule",
                "fit_rule",
                "remedy_rule",
            )
            if str(career_contract.get(key) or "").strip()
        ]
        base["avoid_drift"] = list(dict.fromkeys([
            *(base.get("avoid_drift") or []),
            *career_avoid_drift,
            "generic career advice instead of a professional outcome",
            "invented offer, promotion, selection, joining, resignation or business result",
        ]))
    elif cat in {"marriage", "love", "relationship", "partner", "spouse"} and answer_mode in {"topic_reading"}:
        base["answer_skeleton"] = "Relationship promise -> Current activation -> Support vs friction -> Practical guidance"
    return base


def _attach_calculated_remedy_blueprint(
    *,
    normalized: Dict[str, Any],
    chart_data: Dict[str, Any],
    question: str,
    category: str,
    instant_parashari: Dict[str, Any],
    current_dashas_context: Dict[str, Any],
    target_chart_context: Optional[Dict[str, Any]],
) -> bool:
    """Build and attach the authoritative remedy packet once, returning success."""
    if isinstance(normalized.get("remedy_blueprint"), dict) and normalized["remedy_blueprint"].get("top_recommendation"):
        return True
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
        if not isinstance(remedy_blueprint, dict) or not remedy_blueprint.get("top_recommendation"):
            logger.error(
                "INSTANT_REMEDY_BLUEPRINT_INCOMPLETE category=%s selection_mode=%s ranked_count=%s",
                category,
                (remedy_blueprint or {}).get("selection_mode") if isinstance(remedy_blueprint, dict) else None,
                len((remedy_blueprint or {}).get("ranked_remedies") or []) if isinstance(remedy_blueprint, dict) else 0,
            )
            return False
        normalized["remedy_blueprint"] = remedy_blueprint
        normalized["question_focus"] = remedy_blueprint.get("question_focus") or normalized.get("question_focus")
        normalized["primary_drivers"] = list(remedy_blueprint.get("candidate_planets") or normalized.get("primary_drivers") or [])
        normalized["top_risks"] = list(remedy_blueprint.get("priority_order") or normalized.get("top_risks") or [])
        normalized["special_points"] = remedy_blueprint.get("special_points") or {}
        normalized["remedy_sections"] = remedy_blueprint.get("remedy_sections") or {}
        normalized["follow_up_prompts"] = remedy_blueprint.get("follow_up_prompts") or []
        normalized["caution"] = remedy_blueprint.get("caution") or ""
        return True
    except Exception:
        logger.exception("INSTANT_REMEDY_BLUEPRINT_BUILD_FAILED category=%s", category)
        return False


def _normalize_instant_evidence(
    answer_mode: str,
    category: str,
    question: str,
    chart_data: Dict[str, Any],
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
    selected_activation_source = (
        window_dasha_segments
        if answer_mode == "timing_window"
        else horizon_dasha_segments
        if answer_mode == "event_prediction"
        else window_dasha_segments or horizon_dasha_segments
    )
    activation_timeline = (
        selected_activation_source.get("activation_timeline")
        if isinstance(selected_activation_source, dict)
        else {}
    ) or {}
    activation_segments = (
        selected_activation_source.get("segments")
        if isinstance(selected_activation_source, dict)
        else []
    ) or []
    dasha_permission_segments = [
        row for row in activation_segments
        if isinstance(row, dict) and row.get("natal_promise_status") == "supported_by_active_dasha_carriers"
    ]
    natal_promise = {
        "status": (
            "supported"
            if topic_support in {"supportive", "strong"}
            else "qualified"
            if topic_support or topic_signals
            else "not_established"
        ),
        "topic_support": topic_support,
        "current_topic_support": current_topic_support,
        "dasha_permission_segment_count": len(dasha_permission_segments),
        "rule": "Transit may time only an event already permitted by natal promise and the active dasha carriers.",
    }
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
        historical_scan = instant_parashari.get("historical_event_dasha_scan") or {}
        retrospective = bool(historical_scan.get("periods"))
        fd_scan = historical_scan if retrospective else (instant_parashari.get("forward_event_dasha_scan") or {})
        strong_lines: List[str] = []
        weak_lines: List[str] = []
        for p in (fd_scan.get("periods") or [])[:10]:
            window_prefix = (
                "probable past window" if retrospective
                else "current window" if str(p.get("time_status") or "").strip().lower() == "current"
                else "future window"
            )
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
        for seg in ([] if retrospective else (horizon_dasha_segments.get("segments") or []))[:6]:
            horizon_segment_lines.append(
                f"horizon phase {seg.get('start')}–{seg.get('end')}: "
                f"{seg.get('mahadasha')}-{seg.get('antardasha')}-{seg.get('pratyantardasha')} "
                f"(score {seg.get('relevance_score')}; houses {seg.get('activated_focus_houses')}; {seg.get('why')})"
            )
    primary_drivers = top_supports
    if answer_mode == "timing_window":
        seg_lines: List[str] = []
        for seg in (window_dasha_segments.get("segments") or [])[:4]:
            peaks = list(seg.get("peak_activation_windows") or [])[:2]
            seg_lines.append(
                f"window segment {seg.get('start')}–{seg.get('end')}: "
                f"{seg.get('mahadasha')}-{seg.get('antardasha')}-{seg.get('pratyantardasha')} "
                f"(activation {seg.get('activation_strength')}; houses {seg.get('activated_focus_houses')}; "
                f"real-life areas {seg.get('predicted_result_areas')}; dated peaks {peaks}; {seg.get('why')})"
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
        "current_timing": ({
            "active_dashas": current_dashas_context,
            "current_dasha_chain": current_chain,
            "authoritative_current_dasha_display": current_chain_display,
            "authoritative_current_dasha_chain": current_chain,
            "authoritative_current_dasha_fact": authoritative_current_dasha_fact,
            "time_relation": instant_parashari.get("time_relation"),
            "period_window": period_window,
        } if not instant_parashari.get("historical_event_dasha_scan") else {}),
        "topic_confirmation": {
            "topic_signals": topic_signals,
            "topic_support": topic_support,
            "current_topic_support": current_topic_support,
        },
        "natal_promise": natal_promise,
        "transit_activation_timeline": activation_timeline,
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
    if str(category or "").lower() in CAREER_ALIASES or str(category or "").lower() in CAREER_PROFILES:
        profile = career_profile(category, instant_parashari.get("career_subtype"))
        activated = [row.get("house") for row in active_area_rows if isinstance(row, dict)]
        normalized["career_profile"] = profile
        normalized["career_manifestations"] = classify_career_manifestations(activated)
    if answer_mode == "remedy_action":
        _attach_calculated_remedy_blueprint(
            normalized=normalized,
            chart_data=chart_data,
            question=question,
            category=category,
            instant_parashari=instant_parashari,
            current_dashas_context=current_dashas_context,
            target_chart_context=target_chart_context,
        )
    if answer_mode == "event_prediction":
        normalized["timing_policy"] = instant_parashari.get("timing_policy") or {}
        if instant_parashari.get("historical_event_dasha_scan"):
            normalized["historical_event_dasha_scan"] = instant_parashari.get("historical_event_dasha_scan") or {}
        else:
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
    if answer_mode == "factual_chart_lookup":
        primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "chart_facts"
        secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "natal snapshot"
        avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "topic-reading drift"
        skeleton = str(
            contract.get("answer_skeleton")
            or "Direct prediction in this named chart's life area -> Lagna and lagna-lord result -> Two strongest supported outcomes -> One main caution -> One compact proof from this chart"
        )
        return "\n".join(
            [
                f"This answer uses universal answer mode `{answer_mode}`.",
                "CRITICAL: Follow the method instructions below exactly.",
                "CRITICAL: Predict from the requested chart's calculated packet. Placements, dignity, and aspects are evidence, not the user-facing answer.",
                "CRITICAL: Your response will be marked failed if you dump planet-by-planet placements, use D1 current dasha/transits, or write generic varga lore without citing this chart's data.",
                f"Answer skeleton: {skeleton}.",
                f"Primary evidence priority: {primary}.",
                f"Secondary evidence only after primary evidence: {secondary}.",
                f"Avoid these drifts: {avoid}.",
                "- `normalized_evidence.chart_facts`: this is the only source of truth. Use `charts[X].domain.life_area` as the prediction domain, then lagna/lagna-lord, dignity, occupation, conjunctions, and aspects.",
                "- Name the requested chart clearly (D12, D9, Karkamsa, Swamsa, etc.) while stating the life-area prediction.",
                "- If `chart_facts.missing_requested_charts` is present, say that chart could not be calculated. Do not invent it.",
                "- Use `support_signals` and `caution_signals` to rank outcomes. One compact proof must cite this named chart only.",
                "- `normalized_evidence.karaka_evidence`: use this only when the requested chart is Karkamsa or Swamsa, to name the Atmakaraka that the chart is built from.",
                "Do not mention the current dasha chain or transits. Do not answer as a placement inventory.",
                "A D12 prediction is about parents/elders/ancestry FROM this D12 packet, not D1 family houses. A D10 prediction is about career FROM this D10 packet. Do not write textbook meanings without the supplied facts.",
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
        remedy_blueprint = (normalized_evidence or {}).get("remedy_blueprint") if isinstance((normalized_evidence or {}).get("remedy_blueprint"), dict) else {}
        single_top = str(remedy_blueprint.get("selection_mode") or "") == "single_top"
        primary = ", ".join(str(v) for v in (contract.get("primary_evidence") or [])) or "remedy blueprint and active pressure"
        secondary = ", ".join(str(v) for v in (contract.get("secondary_evidence") or [])) or "supporting modifiers"
        avoid = "; ".join(str(v) for v in (contract.get("avoid_drift") or [])) or "generic remedy dump"
        skeleton = (
            "Name the single top calculated remedy -> Exact action -> Frequency/duration -> Calculated chart reason -> One caution"
            if single_top
            else str(contract.get("answer_skeleton") or "One-sentence problem focus -> Three prioritized remedies -> One caution -> One natural follow-up question")
        )
        return "\n".join(
            [
                f"This answer uses universal answer mode `{answer_mode}`.",
                "CRITICAL: Follow the method instructions below exactly.",
                "CRITICAL: This is a remedy-only answer, not a full predictive reading.",
                "CRITICAL: Do not give all astrological schools or a generic upaya list. Build remedies only from the remedy blueprint and the strongest active chart pressure.",
                "CRITICAL: Keep the remedy language practical, layered, and non-dramatic.",
                "CRITICAL: Answer the request immediately. Do not replace remedies with forecasts, favorable dates, diagnosis, or advice such as merely work harder / be disciplined.",
                (
                    "CRITICAL: The user asked which remedy is most relevant. Give exactly one: copy `remedy_blueprint.top_recommendation`, including its action, frequency, and astrological_reason."
                    if single_top
                    else "CRITICAL: Keep this Instant version concise: give exactly 3 prioritized remedies. For each, state exactly what to do, how/often to do it, and the astrological reason in plain language."
                ),
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
                "- `normalized_evidence.remedy_blueprint.caution`: use this to avoid overcommitting to gemstones or too many remedies at once.",
                "- `normalized_evidence.current_timing` and `active_dashas_formatted`: use these only to identify the planet(s) currently pressing the issue.",
                "- `normalized_evidence.divisional_specifics`: use only if the blueprint actually points there. Do not widen into general astrology.",
                "The user should see a complete remedy reading in one pass — no Follow-up section heading, no follow-up chips, and no second remedy CTA.",
                "Do not turn the answer into a broad horoscope or a long explanation of all planets.",
                "If the user is already positively channeling the planet through study, research, service, teaching, building, or disciplined work, say that directly and treat it as the strongest remedy layer.",
                "End with exactly one short, natural conversational question about which remedy is practical for the user or whether they want its precise routine.",
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
            "CRITICAL: For timing/window answers, reason internally through PD and Sookshma/Prana when supplied. These are calculation evidence, not the user-facing answer.",
            "CRITICAL: Internally distinguish the jobs of MD, AD, PD, and SK/PR, but do not make the user decode those levels. Expose at most one compact astrological reason unless the user explicitly asks how the prediction was derived.",
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
            "For timing/window answers, keep the dasha chain in the evidence layer by default. The visible answer must translate it into likely events, work conditions, opportunities, pressures, and decisions. Name the chain only once if it materially improves credibility.",
            "CRITICAL: If the `window_dasha_segments` show a material PD or AD change inside the asked period, mention the phase boundary and how the user's lived experience changes. Do not name the technical dasha levels or planets unless that one compact proof sentence materially helps.",
            "Use the dasha levels with distinct jobs: MD sets the background period, AD carries the main channel, PD sharpens the month/window result, and Sookshma/Prana refine delivery when enabled.",
            "A timing/window answer fails if it merely lists periods, planets, or house numbers without answering what the user is likely to experience.",
            "Ground every conclusion in the supplied dasha roles and repeated house themes internally, then state the conclusion in ordinary life language first.",
            "These are critical reasoning steps for all timing/window answers, but they are not a required visible recital: read the active chain, identify activated houses, combine repeated themes, and convert that evidence into a prediction the user can act on.",
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
            "Use 2 or 3 concrete astrological reasons internally to form the conclusion, but expose at most one compact proof sentence unless the user explicitly asks for the astrological derivation.",
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


def _instant_real_karaka_evidence(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run the existing Jaimini calculator and expose only its real result."""
    try:
        from calculators.chara_karaka_calculator import CharaKarakaCalculator

        result = CharaKarakaCalculator(chart_data).calculate_chara_karakas()
        return result if isinstance(result, dict) else {}
    except Exception:
        logger.exception("Instant Jaimini karaka calculation failed")
        return {}


def _instant_compact_profession_evidence(
    chart_data: Dict[str, Any],
    birth_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Reuse the deterministic profession engine for career-fit questions only.

    The engine is intentionally not run for ordinary career/timing questions:
    it performs Shadbala, dignity and Chara Karaka calculations and would add
    avoidable latency.  Its verbose result is reduced to answer-bearing facts.
    """
    try:
        from calculators.profession_calculator import ProfessionCalculator

        result = ProfessionCalculator(
            chart_data,
            birth_data=birth_data,
        ).calculate_professional_analysis()
        if not isinstance(result, dict):
            return {}
        tenth = result.get("tenth_house_analysis") if isinstance(result.get("tenth_house_analysis"), dict) else {}
        ak_amk = (
            result.get("atmakaraka_amatyakaraka_analysis")
            if isinstance(result.get("atmakaraka_amatyakaraka_analysis"), dict)
            else {}
        )
        return {
            "source": "profession_calculator",
            "tenth_house": {
                "sign": tenth.get("house_sign"),
                "lord": tenth.get("house_lord"),
                "lord_strength_rupas": tenth.get("lord_shadbala_rupas"),
                "lord_dignity": tenth.get("lord_dignity"),
                "occupants": list(tenth.get("planets_in_house") or ()),
                "strength_grade": tenth.get("house_strength_grade"),
            },
            "vocation_significators": ak_amk,
            # Retained only as audit evidence. The legacy recommendations are
            # based mainly on strongest planets and must never drive the user
            # answer; _compact_career_foundation replaces them with the
            # cross-chart vocation synthesis.
            "legacy_ranked_fields": list(result.get("profession_recommendations") or ())[:3],
            "planetary_strengths": result.get("planetary_career_strengths") or {},
            "career_yogas": list(result.get("professional_yogas") or ())[:4],
            "professional_obstacles": list(result.get("career_obstacles") or ())[:3],
        }
    except Exception:
        logger.exception("Instant deterministic profession calculation failed")
        return {}


def _instant_real_kp_evidence(birth_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate the compact KP payload required by the exact-day spine."""
    try:
        from app.kp.services.chart_service import KPChartService

        result = KPChartService.calculate_kp_chart(
            birth_data.get("date"),
            birth_data.get("time"),
            birth_data.get("latitude"),
            birth_data.get("longitude"),
            birth_data.get("timezone"),
        )
        if not isinstance(result, dict) or result.get("error"):
            return {}
        return {
            "planet_lords": result.get("planet_lords") or {},
            "cusp_lords": result.get("cusp_lords") or {},
            "significators": result.get("significators") or {},
            "planet_significators": result.get("planet_significators") or {},
            "four_step_theory": result.get("four_step_theory") or {},
        }
    except Exception:
        logger.exception("Instant exact-day KP calculation failed")
        return {}


def _should_force_event_current_window(
    answer_mode: str,
    period_window: Optional[Dict[str, Any]],
) -> bool:
    """Keep a resolved exact day intact while retaining legacy event behavior."""
    return (
        str(answer_mode or "").strip() == "event_prediction"
        and str((period_window or {}).get("kind") or "").strip().lower() != "day"
    )


_INSTANT_SUPPORTED_VARGAS = {1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60}

_CHART_PREDICTION_DOMAINS: Dict[str, Dict[str, Any]] = {
    "D1": {
        "code": "D1", "name": "Rasi",
        "life_area": "overall life pattern and visible results",
        "predicts": "core life direction, temperament, and how results show in the world",
        "focus_houses": [1, 4, 7, 10],
        "house_overlays": {},
    },
    "D2": {
        "code": "D2", "name": "Hora",
        "life_area": "wealth and material resources",
        "predicts": "capacity to accumulate, hold, and use resources",
        "focus_houses": [1, 2, 8, 11],
        "house_overlays": {},
    },
    "D3": {
        "code": "D3", "name": "Drekkana",
        "life_area": "siblings, courage, and self-effort",
        "predicts": "initiative, sibling dynamics, and the will to act",
        "focus_houses": [1, 3, 11],
        "house_overlays": {},
    },
    "D4": {
        "code": "D4", "name": "Chaturthamsha",
        "life_area": "home, property, and inner security",
        "predicts": "residence, assets, and emotional base",
        "focus_houses": [1, 4, 10, 12],
        "house_overlays": {},
    },
    "D7": {
        "code": "D7", "name": "Saptamsha",
        "life_area": "children, creativity, and progeny",
        "predicts": "children, creative output, and lineage through offspring",
        "focus_houses": [1, 5, 7, 9],
        "house_overlays": {},
    },
    "D9": {
        "code": "D9", "name": "Navamsha",
        "life_area": "marriage, dharma, and spouse",
        "predicts": "partnership quality, inner dharma, and how fortune matures",
        "focus_houses": [1, 5, 7, 9],
        "house_overlays": {},
    },
    "D10": {
        "code": "D10", "name": "Dashamsha",
        "life_area": "career, status, and public work",
        "predicts": "profession, authority, visibility, and work results",
        "focus_houses": [1, 2, 6, 10, 11],
        "house_overlays": {},
    },
    "D12": {
        "code": "D12", "name": "Dwadashamsha",
        "life_area": "parents, elders, ancestry, and inherited family patterns",
        "predicts": "parental support, ancestral imprint, and how elders shape the native's inner base",
        "focus_houses": [1, 4, 9, 10, 12],
        "house_overlays": {
            1: "native's experience of lineage and parental imprint",
            4: "mother, home, ancestral property, emotional inheritance",
            9: "father, dharma from lineage, guidance from elders",
            10: "status and duty through parents or family",
            12: "ancestral losses, distant elders, hidden family karma",
        },
    },
    "D16": {
        "code": "D16", "name": "Shodashamsha",
        "life_area": "comforts, vehicles, and enjoyments",
        "predicts": "luxuries, conveyances, and ease in daily comforts",
        "focus_houses": [1, 4, 11, 12],
        "house_overlays": {},
    },
    "D20": {
        "code": "D20", "name": "Vimshamsha",
        "life_area": "spiritual practice and devotion",
        "predicts": "worship, sadhana, and religious inclination",
        "focus_houses": [1, 5, 8, 9, 12],
        "house_overlays": {},
    },
    "D24": {
        "code": "D24", "name": "Chaturvimshamsha",
        "life_area": "education and learning",
        "predicts": "study, knowledge, and academic results",
        "focus_houses": [1, 4, 5, 9],
        "house_overlays": {},
    },
    "D27": {
        "code": "D27", "name": "Saptavimshamsha",
        "life_area": "inherent strengths and weaknesses",
        "predicts": "native stamina, inner fortitude, and fragile spots",
        "focus_houses": [1, 3, 6, 8],
        "house_overlays": {},
    },
    "D30": {
        "code": "D30", "name": "Trimshamsha",
        "life_area": "evils, ailments, and misfortune",
        "predicts": "vulnerability to trouble, illness, and hidden strain",
        "focus_houses": [1, 6, 8, 12],
        "house_overlays": {},
    },
    "D40": {
        "code": "D40", "name": "Khavedamsha",
        "life_area": "maternal lineage and mother's family",
        "predicts": "maternal relatives and support from the mother's side",
        "focus_houses": [1, 4, 11, 12],
        "house_overlays": {},
    },
    "D45": {
        "code": "D45", "name": "Akshavedamsha",
        "life_area": "paternal lineage and father's family",
        "predicts": "paternal relatives and support from the father's side",
        "focus_houses": [1, 9, 10, 11],
        "house_overlays": {},
    },
    "D60": {
        "code": "D60", "name": "Shashtyamsha",
        "life_area": "karmic residue and past-life imprint",
        "predicts": "subtle karmic tone that colors other results",
        "focus_houses": [1, 6, 8, 9, 12],
        "house_overlays": {},
    },
    "KARAKAMSHA": {
        "code": "Karkamsa", "name": "Karakamsa",
        "life_area": "soul-direction and Atmakaraka path in worldly life",
        "predicts": "how the Atmakaraka seeks fulfillment in material life",
        "focus_houses": [1, 5, 9, 10],
        "house_overlays": {},
    },
    "SWAMSA": {
        "code": "Swamsa", "name": "Swamsa",
        "life_area": "self-expression of the Atmakaraka",
        "predicts": "inner vocation, spiritual leaning, and how the soul wants to act",
        "focus_houses": [1, 5, 9, 10],
        "house_overlays": {},
    },
}

_CHART_PREDICTION_FORMAT = [
    "direct prediction in this chart's life area",
    "lagna and lagna-lord result",
    "two strongest supported outcomes",
    "one main caution",
    "one compact proof from this named chart",
    "one domain follow-up",
]


def _instant_compact_calculated_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Keep exact placements while avoiding a second full chart context."""
    if not isinstance(chart, dict):
        return {}
    payload = chart.get("divisional_chart") if isinstance(chart.get("divisional_chart"), dict) else chart
    planets = payload.get("planets") if isinstance(payload.get("planets"), dict) else {}
    compact_planets: Dict[str, Any] = {}
    for name, row in planets.items():
        if not isinstance(row, dict):
            continue
        compact_planets[str(name)] = {
            key: row.get(key)
            for key in (
                "sign", "sign_name", "house", "longitude", "degree",
                "degree_in_sign", "nakshatra", "pada", "retrograde",
                "combust", "exalted", "debilitated", "dignity",
                "functional_nature", "own_sign", "moolatrikona", "mooltrikona",
            )
            if row.get(key) is not None
        }
    ascendant = payload.get("ascendant")
    return {
        "chart_name": chart.get("chart_name") or payload.get("chart_type"),
        "division_number": chart.get("division_number"),
        "ascendant": ascendant,
        "ascendant_sign": (
            payload.get("ascendant_sign")
            if payload.get("ascendant_sign") is not None
            else int(float(ascendant) / 30) if isinstance(ascendant, (int, float)) else None
        ),
        "ayanamsa": payload.get("ayanamsa"),
        "planets": compact_planets,
    }


def _normalize_instant_chart_code(raw: Any) -> str:
    label = str(raw or "").strip()
    if not label:
        return ""
    normalized = re.sub(r"[\s_-]+", "", label).upper()
    if normalized in {"KARAKAMSHA", "KARKAMSA", "KARAKAMSA", "KARKAMSHA"}:
        return "KARAKAMSHA"
    if normalized in {"SWAMSA", "SWAMSHA"}:
        return "SWAMSA"
    if normalized and normalized[0].isdigit():
        return f"D{normalized}"
    if re.fullmatch(r"D\d{1,2}", normalized):
        return normalized
    return normalized


def _requested_charts_from_intent(intent: Optional[Dict[str, Any]], *, answer_mode: str) -> List[str]:
    """Collect charts the LLM already named. Do not parse the user question."""
    intent = intent if isinstance(intent, dict) else {}
    extracted = intent.get("extracted_context") if isinstance(intent.get("extracted_context"), dict) else {}
    focus = intent.get("chart_focus") if isinstance(intent.get("chart_focus"), dict) else {}
    requested: List[str] = []
    for raw in list(focus.get("requested") or []):
        code = _normalize_instant_chart_code(raw)
        if code and code not in requested:
            requested.append(code)
    primary = _normalize_instant_chart_code(focus.get("primary"))
    if primary and primary not in requested:
        requested.append(primary)
    extracted_chart = _normalize_instant_chart_code(extracted.get("requested_chart"))
    if extracted_chart and extracted_chart not in requested:
        requested.append(extracted_chart)
    category = intent.get("category")
    subtype = intent.get("career_subtype")
    static_career_profile = is_static_career_profile(
        category, subtype, answer_mode=answer_mode
    )
    if static_career_profile:
        # A static career profile needs the Jaimini vocation signature as well
        # as D1 and D10. Timing-only questions can stay on their bounded packet.
        for code in ("D1", "D10", "KARAKAMSHA"):
            if code not in requested:
                requested.append(code)
    elif is_career_decision(category, subtype) or is_career_relationship(category, subtype):
        for code in ("D1", "D10"):
            if code not in requested:
                requested.append(code)
    if requested:
        return requested
    if str(answer_mode or "").strip() != "factual_chart_lookup":
        return []
    extras: List[str] = []
    for raw in intent.get("divisional_charts") or []:
        code = _normalize_instant_chart_code(raw)
        if code and code not in extras:
            extras.append(code)
    named = [code for code in extras if code != "D1"]
    return named or extras


def _chart_fact_sign_label(row: Dict[str, Any]) -> str:
    name = str(row.get("sign_name") or "").strip()
    if name:
        return name
    sign = row.get("sign")
    if isinstance(sign, int):
        return SIGN_NAMES[sign % 12]
    if isinstance(sign, str) and sign.strip():
        return sign.strip()
    return "unknown sign"


def _chart_prediction_domain(chart_name: str) -> Dict[str, Any]:
    code = _normalize_instant_chart_code(chart_name)
    fallback = {
        "code": chart_name,
        "name": str(chart_name),
        "life_area": "the asked chart's native life area",
        "predicts": "results shown by this named chart",
        "focus_houses": [1, 4, 7, 10],
        "house_overlays": {},
    }
    domain = _CHART_PREDICTION_DOMAINS.get(code) or fallback
    return dict(domain)


def _houses_aspected_by_planet(planet: str, from_house: Any) -> List[int]:
    origin = _norm_house(from_house)
    if origin is None:
        return []
    houses: List[int] = []
    for aspect_number in instant_activation_aspects(planet, include_conjunction=False):
        house = _norm_house(origin + aspect_number - 1)
        if house is not None and house not in houses:
            houses.append(house)
    return houses


def _uniq_signal_lines(items: List[str], limit: int = 6) -> List[str]:
    seen: List[str] = []
    for item in items:
        text = str(item or "").strip()
        if text and text not in seen:
            seen.append(text)
        if len(seen) >= limit:
            break
    return seen


def _chart_prediction_signals(
    domain: Dict[str, Any],
    lagna_lord: Optional[str],
    lagna_lord_row: Optional[Dict[str, Any]],
    planets: Dict[str, Any],
    houses: List[Dict[str, Any]],
) -> tuple:
    support: List[str] = []
    caution: List[str] = []
    focus = {int(h) for h in (domain.get("focus_houses") or [1, 4, 7, 10]) if _safe_int(h) is not None}
    strong_dignity = {"exalted", "own_sign", "mooltrikona", "moolatrikona"}
    if isinstance(lagna_lord_row, dict) and lagna_lord:
        dignity = str(lagna_lord_row.get("dignity") or "")
        house = lagna_lord_row.get("house")
        if dignity in strong_dignity:
            support.append(f"Lagna lord {lagna_lord} is {dignity} in house {house}")
        elif dignity == "debilitated":
            caution.append(f"Lagna lord {lagna_lord} is debilitated in house {house}")
        if house in {6, 8, 12}:
            caution.append(f"Lagna lord {lagna_lord} occupies dusthana house {house}")
        elif house in {1, 4, 5, 7, 9, 10, 11}:
            support.append(f"Lagna lord {lagna_lord} occupies house {house}")
        received = lagna_lord_row.get("aspects_received") or []
        for aspect in received:
            if not isinstance(aspect, dict):
                continue
            other = str(aspect.get("planet") or "")
            tone = str(aspect.get("aspect_tone") or aspect.get("nature") or "")
            if tone == "benefic" and other:
                support.append(f"Lagna lord {lagna_lord} is aspected by {other}")
            elif tone == "malefic" and other:
                caution.append(f"Lagna lord {lagna_lord} is aspected by {other}")
    for name, row in planets.items():
        if not isinstance(row, dict):
            continue
        house = _norm_house(row.get("house"))
        dignity = str(row.get("dignity") or "")
        nature = str(row.get("natural_nature") or _natural_nature(str(name)))
        if house in focus and dignity in strong_dignity:
            support.append(f"{name} is {dignity} in focus house {house}")
        if house in focus and dignity == "debilitated":
            caution.append(f"{name} is debilitated in focus house {house}")
        if house in focus and nature == "benefic":
            support.append(f"Benefic {name} occupies focus house {house}")
        if house in focus and nature == "malefic":
            caution.append(f"Malefic {name} occupies focus house {house}")
        for asp_house in row.get("aspects_to_houses") or []:
            target = _norm_house(asp_house)
            if target not in focus:
                continue
            if nature == "benefic":
                support.append(f"{name} aspects focus house {target}")
            elif nature == "malefic":
                caution.append(f"{name} aspects focus house {target}")
    for house_row in houses:
        if not isinstance(house_row, dict) or not house_row.get("focus"):
            continue
        occupants = [str(p) for p in (house_row.get("occupants") or [])]
        if not occupants:
            continue
        hh = house_row.get("house")
        if hh in {6, 8, 12} and occupants:
            caution.append(f"Focus house {hh} occupied by {', '.join(occupants)}")
    return _uniq_signal_lines(support), _uniq_signal_lines(caution)


def _enrich_calculated_chart_for_prediction(chart_name: str, compact: Dict[str, Any]) -> Dict[str, Any]:
    """Add dignity, aspects, lordships, and domain so the LLM can predict from this chart."""
    if not isinstance(compact, dict):
        return {}
    planets = compact.get("planets") if isinstance(compact.get("planets"), dict) else {}
    if not planets:
        return dict(compact)
    asc_sign = compact.get("ascendant_sign")
    if not isinstance(asc_sign, int):
        asc = compact.get("ascendant")
        try:
            asc_sign = int(float(asc) / 30) % 12 if asc is not None else None
        except (TypeError, ValueError):
            asc_sign = None
    lordships = _get_house_lordships(int(asc_sign)) if isinstance(asc_sign, int) else {}
    lagna_lord = _SIGN_LORDS.get(int(asc_sign)) if isinstance(asc_sign, int) else None
    chart_like = {"planets": planets}
    house_occupants: Dict[int, List[str]] = {house: [] for house in range(1, 13)}
    enriched_planets: Dict[str, Any] = {}
    for name, row in planets.items():
        if not isinstance(row, dict):
            continue
        house = _norm_house(row.get("house"))
        if house is not None:
            house_occupants[house].append(str(name))
        planet_lordships = list(lordships.get(str(name)) or [])
        dignity = _planet_dignity_status(str(name), _sign_index_from_row(row))
        calc_dignity = str(row.get("dignity") or "")
        if calc_dignity in {"exalted", "debilitated", "own_sign", "mooltrikona", "moolatrikona"}:
            dignity["dignity"] = "mooltrikona" if calc_dignity == "moolatrikona" else calc_dignity
            dignity["in_own_sign"] = dignity["dignity"] == "own_sign"
            dignity["in_mooltrikona"] = dignity["dignity"] in {"mooltrikona", "moolatrikona"}
        conjunctions = [
            other
            for other, other_row in planets.items()
            if other != name
            and isinstance(other_row, dict)
            and house is not None
            and _norm_house(other_row.get("house")) == house
        ]
        enriched_planets[str(name)] = {
            **{key: value for key, value in row.items() if value is not None},
            "sign_name": _chart_fact_sign_label(row),
            "house": house,
            "lordships": planet_lordships,
            "natural_nature": _natural_nature(str(name)),
            "functional_nature": _functional_nature(planet_lordships),
            "dignity": dignity.get("dignity"),
            "sign_relation": dignity.get("sign_relation"),
            "in_own_sign": dignity.get("in_own_sign"),
            "in_mooltrikona": dignity.get("in_mooltrikona"),
            "sign_lord": dignity.get("sign_lord"),
            "retrograde": bool(row.get("retrograde")),
            "combust": bool(row.get("combust")),
            "conjunctions": conjunctions,
            "aspects_received": _natal_aspects_to_planet(str(name), chart_like),
            "aspects_to_houses": _houses_aspected_by_planet(str(name), house),
        }
    domain = _chart_prediction_domain(chart_name)
    overlays = domain.get("house_overlays") if isinstance(domain.get("house_overlays"), dict) else {}
    focus_houses = {int(h) for h in (domain.get("focus_houses") or []) if _safe_int(h) is not None}
    houses: List[Dict[str, Any]] = []
    for house in range(1, 13):
        sign_index = ((int(asc_sign) + house - 1) % 12) if isinstance(asc_sign, int) else None
        houses.append(
            {
                "house": house,
                "sign": sign_index,
                "sign_name": SIGN_NAMES[sign_index] if sign_index is not None else None,
                "theme": overlays.get(house) or HOUSE_THEME_LABELS.get(house, ""),
                "lord": _lord_of_house(lordships, house) if lordships else "",
                "occupants": house_occupants.get(house) or [],
                "focus": house in focus_houses,
            }
        )
    lagna_lord_row = enriched_planets.get(str(lagna_lord or "")) if lagna_lord else None
    support_signals, caution_signals = _chart_prediction_signals(
        domain, lagna_lord, lagna_lord_row if isinstance(lagna_lord_row, dict) else None, enriched_planets, houses,
    )
    return {
        **compact,
        "domain": {
            "code": domain.get("code"),
            "name": domain.get("name"),
            "life_area": domain.get("life_area"),
            "predicts": domain.get("predicts"),
            "focus_houses": list(domain.get("focus_houses") or []),
        },
        "lagna": {
            "sign": asc_sign,
            "sign_name": SIGN_NAMES[int(asc_sign) % 12] if isinstance(asc_sign, int) else None,
            "lord": lagna_lord,
            "lord_house": (lagna_lord_row or {}).get("house") if isinstance(lagna_lord_row, dict) else None,
            "lord_dignity": (lagna_lord_row or {}).get("dignity") if isinstance(lagna_lord_row, dict) else None,
            "lord_sign": (lagna_lord_row or {}).get("sign_name") if isinstance(lagna_lord_row, dict) else None,
        },
        "planets": enriched_planets,
        "houses": houses,
        "support_signals": support_signals,
        "caution_signals": caution_signals,
    }


def _compact_planet_for_composer_prediction(row: Dict[str, Any]) -> Dict[str, Any]:
    received = []
    for aspect in row.get("aspects_received") or []:
        if isinstance(aspect, dict) and aspect.get("planet"):
            received.append(
                {
                    "planet": aspect.get("planet"),
                    "tone": aspect.get("aspect_tone") or aspect.get("nature"),
                }
            )
    return {
        key: value
        for key, value in {
            "sign": _chart_fact_sign_label(row),
            "house": row.get("house"),
            "dignity": row.get("dignity"),
            "lordships": list(row.get("lordships") or []),
            "natural_nature": row.get("natural_nature"),
            "functional_nature": row.get("functional_nature"),
            "retrograde": bool(row.get("retrograde")) or None,
            "combust": bool(row.get("combust")) or None,
            "conjunctions": list(row.get("conjunctions") or []),
            "aspects_received": received,
            "aspects_to_houses": list(row.get("aspects_to_houses") or []),
        }.items()
        if value not in (None, "", [], {}, False)
    }


def _compact_chart_for_composer_prediction(chart_name: str, row: Dict[str, Any]) -> Dict[str, Any]:
    enriched = row if isinstance(row.get("domain"), dict) else _enrich_calculated_chart_for_prediction(chart_name, row)
    planets = enriched.get("planets") if isinstance(enriched.get("planets"), dict) else {}
    houses = []
    for house_row in enriched.get("houses") or []:
        if not isinstance(house_row, dict):
            continue
        houses.append(
            {
                key: value
                for key, value in {
                    "house": house_row.get("house"),
                    "sign": house_row.get("sign_name"),
                    "lord": house_row.get("lord"),
                    "occupants": house_row.get("occupants") or [],
                    "theme": house_row.get("theme"),
                    "focus": bool(house_row.get("focus")) or None,
                }.items()
                if value not in (None, "", [], {})
            }
        )
    return {
        key: value
        for key, value in {
            "domain": enriched.get("domain"),
            "lagna": enriched.get("lagna"),
            "ayanamsa": enriched.get("ayanamsa"),
            "atmakaraka": enriched.get("atmakaraka"),
            "support_signals": enriched.get("support_signals") or [],
            "caution_signals": enriched.get("caution_signals") or [],
            "planets": {
                str(planet): _compact_planet_for_composer_prediction(prow)
                for planet, prow in planets.items()
                if isinstance(prow, dict)
            },
            "houses": houses,
        }.items()
        if value not in (None, "", [], {})
    }


def _format_planet_chart_fact_line(label: str, planet_name: str, row: Dict[str, Any]) -> str:
    house = row.get("house")
    house_bit = f", house {house}" if house not in (None, "") else ""
    extras: List[str] = []
    dignity = str(row.get("dignity") or "").strip()
    if dignity and dignity not in {"unknown", "neutral_sign", "neutral"}:
        extras.append(dignity)
    if row.get("retrograde"):
        extras.append("retrograde")
    if row.get("combust"):
        extras.append("combust")
    lordships = row.get("lordships") or []
    if lordships:
        extras.append("lords " + "/".join(str(house) for house in lordships))
    conjunctions = row.get("conjunctions") or []
    if conjunctions:
        extras.append("conjunct " + ", ".join(str(item) for item in conjunctions))
    received = []
    for aspect in row.get("aspects_received") or []:
        if isinstance(aspect, dict) and aspect.get("planet"):
            received.append(str(aspect.get("planet")))
        elif aspect:
            received.append(str(aspect))
    if received:
        extras.append("aspected by " + ", ".join(received))
    extra_bit = f" ({', '.join(extras)})" if extras else ""
    return f"{label} {planet_name}: {_chart_fact_sign_label(row)}{house_bit}{extra_bit}"


def _format_chart_fact_reading(chart_facts: Dict[str, Any]) -> Dict[str, Any]:
    display = {"KARAKAMSHA": "Karkamsa", "SWAMSA": "Swamsa"}
    lines: List[str] = []
    analysis: List[str] = []
    charts = chart_facts.get("charts") if isinstance(chart_facts.get("charts"), dict) else {}
    for chart_name, compact in charts.items():
        if not isinstance(compact, dict):
            continue
        label = display.get(str(chart_name), str(chart_name))
        domain = compact.get("domain") if isinstance(compact.get("domain"), dict) else {}
        lagna = compact.get("lagna") if isinstance(compact.get("lagna"), dict) else {}
        asc_sign = compact.get("ascendant_sign") if compact.get("ascendant_sign") is not None else lagna.get("sign")
        if isinstance(asc_sign, int):
            lagna_name = SIGN_NAMES[asc_sign % 12]
        else:
            lagna_name = str(lagna.get("sign_name") or asc_sign or compact.get("ascendant") or "unknown")
        life_area = str(domain.get("life_area") or "").strip()
        if life_area:
            analysis.append(f"{label} predicts {life_area}")
        lagna_line = f"{label} lagna: {lagna_name}"
        if lagna.get("lord"):
            lord_bits = [str(lagna.get("lord"))]
            if lagna.get("lord_sign"):
                lord_bits.append(str(lagna.get("lord_sign")))
            if lagna.get("lord_house") not in (None, ""):
                lord_bits.append(f"house {lagna.get('lord_house')}")
            if lagna.get("lord_dignity"):
                lord_bits.append(str(lagna.get("lord_dignity")))
            lagna_line += f"; lagna lord {' '.join(lord_bits)}"
        lines.append(lagna_line.split(";")[0])
        analysis.append(lagna_line)
        for signal in compact.get("support_signals") or []:
            analysis.append(f"{label} support: {signal}")
        for signal in compact.get("caution_signals") or []:
            analysis.append(f"{label} caution: {signal}")
        planets = compact.get("planets") if isinstance(compact.get("planets"), dict) else {}
        for planet_name, row in planets.items():
            if not isinstance(row, dict):
                continue
            planet_line = _format_planet_chart_fact_line(label, str(planet_name), row)
            lines.append(planet_line)
            analysis.append(planet_line)
        focus_houses = [
            house_row
            for house_row in (compact.get("houses") or [])
            if isinstance(house_row, dict) and house_row.get("focus")
        ]
        for house_row in focus_houses:
            occupants = ", ".join(str(item) for item in (house_row.get("occupants") or [])) or "empty"
            analysis.append(
                f"{label} house {house_row.get('house')} ({house_row.get('sign_name') or 'unknown'}), "
                f"lord {house_row.get('lord') or 'unknown'}, occupants {occupants}: {house_row.get('theme') or ''}"
            )
        ayanamsa = compact.get("ayanamsa")
        if ayanamsa not in (None, ""):
            lines.append(f"{label} ayanamsa: {ayanamsa}")
        if compact.get("atmakaraka"):
            ak_line = f"{label} Atmakaraka: {compact.get('atmakaraka')}"
            lines.append(ak_line)
            analysis.append(ak_line)
    failures = chart_facts.get("calculation_failures") if isinstance(chart_facts.get("calculation_failures"), dict) else {}
    for missing in chart_facts.get("missing_requested_charts") or []:
        reason = str(failures.get(missing) or "could not be calculated")
        lines.append(f"{missing} unavailable: {reason}")
        analysis.append(f"{missing} unavailable: {reason}")
    source = str(chart_facts.get("source") or "").strip()
    if source:
        lines.append(f"Source: {source}")
    return {
        "reading_lines": lines,
        "reading_text": "\n".join(lines),
        "analysis_brief": "\n".join(analysis),
        "prediction_format": list(_CHART_PREDICTION_FORMAT),
    }


def _instant_real_chart_facts(
    *, chart_data: Dict[str, Any], requested_charts: List[str], requested_fact: Any,
    karaka_evidence: Dict[str, Any], d1_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate every explicitly requested supported chart.

    A chart name appearing in a prose summary is not proof that the chart was
    calculated.  This adapter is the sole source for the chart-fact capability.
    """
    requested = []
    for raw in requested_charts or ["D1"]:
        label = str(raw or "").strip()
        normalized = re.sub(r"[\s_-]+", "", label).upper()
        if normalized in {"KARAKAMSHA", "KARKAMSA", "KARAKAMSA", "KARKAMSHA"}:
            normalized = "KARAKAMSHA"
        elif normalized in {"SWAMSA", "SWAMSHA"}:
            normalized = "SWAMSA"
        elif normalized and normalized[0].isdigit():
            normalized = f"D{normalized}"
        if normalized and normalized not in requested:
            requested.append(normalized)
    if not requested:
        requested = ["D1"]

    calculated: Dict[str, Any] = {}
    missing: List[str] = []
    failures: Dict[str, str] = {}
    divisional_calc = None
    jaimini_calc = None

    for chart_name in requested:
        try:
            if chart_name == "D1":
                calculated[chart_name] = _enrich_calculated_chart_for_prediction(
                    chart_name,
                    _instant_compact_calculated_chart(chart_data) or d1_snapshot,
                )
                continue
            match = re.fullmatch(r"D(\d{1,2})", chart_name)
            if match:
                division = int(match.group(1))
                if division not in _INSTANT_SUPPORTED_VARGAS:
                    missing.append(chart_name)
                    failures[chart_name] = "This divisional chart is not supported by the verified calculator set."
                    continue
                if divisional_calc is None:
                    from calculators.divisional_chart_calculator import DivisionalChartCalculator
                    divisional_calc = DivisionalChartCalculator(chart_data)
                result = divisional_calc.calculate_divisional_chart(division)
                compact = _instant_compact_calculated_chart(result)
                if not compact.get("planets"):
                    raise ValueError("calculator returned no planetary placements")
                calculated[chart_name] = _enrich_calculated_chart_for_prediction(chart_name, compact)
                continue
            if chart_name in {"KARAKAMSHA", "SWAMSA"}:
                karakas = karaka_evidence.get("chara_karakas") if isinstance(karaka_evidence, dict) else {}
                atmakaraka = (karakas.get("Atmakaraka") or {}).get("planet") if isinstance(karakas, dict) else None
                if not atmakaraka:
                    raise ValueError("Atmakaraka is unavailable")
                if jaimini_calc is None:
                    from calculators.jaimini_chart_calculator import JaiminiChartCalculator
                    # Older saved calculation payloads may contain longitude
                    # but omit the redundant degree-within-sign field expected
                    # by this legacy Jaimini adapter.
                    jaimini_chart_data = dict(chart_data)
                    jaimini_chart_data["planets"] = {
                        name: {
                            **row,
                            "sign": row.get("sign", int(float(row.get("longitude") or 0) / 30)),
                            "degree": row.get("degree", float(row.get("longitude") or 0) % 30),
                        }
                        for name, row in (chart_data.get("planets") or {}).items()
                        if isinstance(row, dict)
                    }
                    jaimini_calc = JaiminiChartCalculator(jaimini_chart_data, atmakaraka)
                result = (
                    jaimini_calc.calculate_karkamsa_chart()
                    if chart_name == "KARAKAMSHA"
                    else jaimini_calc.calculate_swamsa_chart()
                )
                chart_key = "karkamsa_chart" if chart_name == "KARAKAMSHA" else "swamsa_chart"
                compact = _instant_compact_calculated_chart(result.get(chart_key) or {})
                if not compact.get("planets"):
                    raise ValueError("calculator returned no planetary placements")
                calculated[chart_name] = _enrich_calculated_chart_for_prediction(
                    chart_name,
                    {
                        **compact,
                        "atmakaraka": result.get("atmakaraka"),
                        "atmakaraka_degree_in_d9": result.get("atmakaraka_degree_in_d9"),
                        "significance": result.get("significance"),
                    },
                )
                continue
            missing.append(chart_name)
            failures[chart_name] = "Unknown chart identifier."
        except Exception as exc:
            logger.exception("Instant chart fact calculation failed for %s", chart_name)
            missing.append(chart_name)
            failures[chart_name] = str(exc)[:180]

    payload = {
        "requested_charts": requested,
        "requested_fact": requested_fact,
        "charts": calculated,
        "calculation_complete": bool(calculated) and not missing,
        "missing_requested_charts": missing,
        "calculation_failures": failures,
        "supported_divisional_charts": [f"D{number}" for number in sorted(_INSTANT_SUPPORTED_VARGAS)],
        "source": "DivisionalChartCalculator and JaiminiChartCalculator",
    }
    payload.update(_format_chart_fact_reading(payload))
    return payload


def _instant_real_nadi_evidence(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run the existing Bhrigu Nandi Nadi linkage calculator.

    A methodology declaration is not evidence.  Instant may cite Nadi only
    when this adapter has produced a real linkage network for the chart.
    """
    try:
        from calculators.nadi_linkage_calculator import NadiLinkageCalculator

        links = NadiLinkageCalculator(chart_data).get_nadi_links()
        return {
            "method": "Bhrigu Nandi Nadi planetary linkage network",
            "links": links,
        } if isinstance(links, dict) and links else {}
    except Exception:
        logger.exception("Instant Nadi linkage calculation failed")
        return {}


def _instant_real_double_transit_evidence(
    *, chart_data: Dict[str, Any], start: datetime, end: datetime,
    focus_houses: List[int], answer_mode: str,
) -> Dict[str, Any]:
    """Calculate exact Jupiter-Saturn double-transit windows for timing flows."""
    if answer_mode not in {
        "event_timing", "lifetime_event_timing", "month_timing",
        "event_prediction", "timing_window",
    }:
        return {}
    try:
        from charts.double_transit_service import calculate_double_transits

        result = calculate_double_transits(chart_data, start, end)
        if not isinstance(result, dict):
            return {}
        wanted = {int(house) for house in (focus_houses or []) if str(house).isdigit()}
        windows = [
            row for row in (result.get("windows") or [])
            if isinstance(row, dict) and (not wanted or int(row.get("house") or 0) in wanted)
        ]
        return {
            "schema": result.get("schema"),
            "method": result.get("method"),
            "range": result.get("range"),
            "focus_houses": sorted(wanted),
            "window_count": len(windows),
            "windows": windows[:16],
        }
    except Exception:
        logger.exception("Instant double-transit calculation failed")
        return {}


def _instant_resolve_muhurat_location(
    *, birth_data: Dict[str, Any], extracted: Dict[str, Any], language: str,
    start_date: str,
) -> Dict[str, Any]:
    """Resolve a user-supplied place name through Places; never trust LLM coordinates."""
    if extracted.get("muhurat_use_birth_location") is True:
        lat = birth_data.get("latitude")
        lon = birth_data.get("longitude")
        if lat is None or lon is None:
            return {}
        return {
            "latitude": float(lat),
            "longitude": float(lon),
            "timezone": birth_data.get("timezone"),
            "label": birth_data.get("place") or birth_data.get("birth_place") or "birth location",
            "source": "saved_birth_location",
        }
    query = str(extracted.get("muhurat_location_query") or "").strip()
    if not query:
        return {}
    try:
        from utils.google_places_client import place_details, places_autocomplete_suggestions
        from utils.timezone_service import get_iana_timezone

        suggestions = places_autocomplete_suggestions(query, language=language or "en", limit=1)
        if not suggestions:
            return {}
        detail = place_details(suggestions[0]["place_id"], language=language or "en")
        lat = float(detail["latitude"])
        lon = float(detail["longitude"])
        return {
            "latitude": lat,
            "longitude": lon,
            "timezone": get_iana_timezone(lat, lon),
            "label": detail.get("formattedAddress") or detail.get("name") or query,
            "place_id": detail.get("place_id"),
            "source": "google_places_verified",
        }
    except Exception:
        logger.exception("Instant Muhurat location resolution failed query=%s", query)
        return {}


def _instant_real_location_evidence(
    *, birth_data: Dict[str, Any], intent: Dict[str, Any], chart_data: Dict[str, Any],
    current_dashas: Dict[str, Any], answer_mode: str,
) -> Dict[str, Any]:
    if answer_mode != "location_recommendation":
        return {}
    try:
        from chat.locational_context_builder import build_locational_recommendation_pack

        location_intent = dict(intent or {})
        location_intent["mode"] = "RECOMMEND_LOCATION"
        result = build_locational_recommendation_pack(
            birth_data,
            intent_result=location_intent,
            natal_chart=chart_data,
            current_dashas=current_dashas,
            # Geography is accepted only from LLM-normalized extracted_context;
            # no English keyword parsing is allowed in Instant Chat.
            user_question="",
        )
        return result if isinstance(result, dict) else {}
    except Exception:
        logger.exception("Instant location recommendation calculation failed")
        return {}


def _instant_real_muhurat_evidence(
    *, birth_data: Dict[str, Any], intent: Dict[str, Any], chart_data: Dict[str, Any],
    answer_mode: str,
) -> Dict[str, Any]:
    """Run a supported election calculator using LLM-normalized parameters."""
    if answer_mode != "dedicated_muhurat_flow":
        return {}
    extracted = (intent or {}).get("extracted_context")
    extracted = extracted if isinstance(extracted, dict) else {}
    event_type = str(extracted.get("muhurat_event_type") or "").strip().lower()
    start_date = str(extracted.get("muhurat_start_date") or "").strip()
    end_date = str(extracted.get("muhurat_end_date") or "").strip()
    language = str((intent or {}).get("language") or "en").strip().lower()
    resolved_location = _instant_resolve_muhurat_location(
        birth_data=birth_data,
        extracted=extracted,
        language=language,
        start_date=start_date,
    )
    lat = resolved_location.get("latitude")
    lon = resolved_location.get("longitude")
    timezone_name = resolved_location.get("timezone")
    if not event_type or not start_date or not end_date or lat is None or lon is None:
        return {}
    moon = ((chart_data.get("planets") or {}).get("Moon") or {})
    try:
        user_nakshatra = int((float(moon.get("longitude")) % 360.0) / (360.0 / 27.0)) + 1
    except (TypeError, ValueError):
        return {}
    try:
        from calculators.muhurat_calculator import MuhuratCalculator

        calculator = MuhuratCalculator()
        common = (start_date, end_date, float(lat), float(lon), user_nakshatra)
        if event_type == "childbirth":
            result = calculator.calculate_childbirth_muhurat(*common, tz=timezone_name)
        elif event_type == "vehicle":
            result = calculator.calculate_vehicle_muhurat(
                *common, tz=timezone_name, birth_data=birth_data,
            )
        elif event_type == "griha_pravesh":
            result = calculator.calculate_griha_pravesh_muhurat(*common, tz=timezone_name)
        elif event_type == "gold":
            result = calculator.calculate_gold_muhurat(*common, tz=timezone_name)
        elif event_type == "business_opening":
            result = calculator.calculate_business_muhurat(*common, tz=timezone_name)
        elif event_type in {"marriage", "property"}:
            from panchang.muhurat_calculator import MuhuratCalculator as PanchangMuhuratCalculator

            day_calculator = PanchangMuhuratCalculator()
            start_day = datetime.strptime(start_date[:10], "%Y-%m-%d").date()
            end_day = datetime.strptime(end_date[:10], "%Y-%m-%d").date()
            if end_day < start_day or (end_day - start_day).days > 62:
                return {}
            recommendations = []
            cursor = start_day
            method = (
                day_calculator.calculate_vivah_muhurat
                if event_type == "marriage"
                else day_calculator.calculate_property_muhurat
            )
            while cursor <= end_day:
                day_result = method(
                    cursor.isoformat(), float(lat), float(lon), timezone_name,
                )
                if isinstance(day_result, dict) and day_result.get("muhurtas"):
                    recommendations.append(day_result)
                cursor += timedelta(days=1)
            result = {
                "category": "Marriage" if event_type == "marriage" else "Property Purchase",
                "period": f"{start_date[:10]} to {end_date[:10]}",
                "dates_found": len(recommendations),
                "recommendations": recommendations,
                "rejected_dates": [],
                "mode": "panchang_election",
            }
        else:
            return {}
        if not isinstance(result, dict) or result.get("error"):
            return {}
        compact = dict(result)
        compact["recommendations"] = list(result.get("recommendations") or [])[:5]
        compact["rejected_dates"] = list(result.get("rejected_dates") or [])[:8]
        compact["calculator_event_type"] = event_type
        compact["calculation_location"] = resolved_location
        return compact
    except Exception:
        logger.exception("Instant Muhurat calculation failed event_type=%s", event_type)
        return {}


def _compact_natal_topic_factors(
    chart_data: Dict[str, Any], focus_houses: List[int], birth_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Expose validated D1 promise facts without leaking the full engine payload.

    This is display evidence, not an additional interpretation pass.  The
    underlying promise engine remains the authority for lord condition,
    occupants, aspects, karakas, yogas, dispositors and contradictory weight.
    """
    try:
        dignities = PlanetaryDignitiesCalculator(chart_data).calculate_planetary_dignities()
        yogi_points = YogiCalculator(chart_data).calculate_yogi_points(birth_data or {})
        gandanta = GandantaCalculator(chart_data).calculate_gandanta_analysis()
        promises, yogas = build_natal_promises(
            chart_data,
            dignities,
            yogi_points=yogi_points,
            gandanta=gandanta,
        )
    except Exception as exc:
        logger.warning("instant natal promise detail build failed: %s", exc)
        return {}

    yoga_by_key = {str(row.get("key")): row for row in yogas if isinstance(row, dict)}
    wanted = {int(house) for house in focus_houses if str(house).isdigit() and 1 <= int(house) <= 12}
    rows: List[Dict[str, Any]] = []
    for promise in promises:
        house = int(promise.get("house") or 0)
        if house not in wanted:
            continue
        factors = []
        for factor in promise.get("factors") or ():
            if not isinstance(factor, dict):
                continue
            facts = factor.get("facts") if isinstance(factor.get("facts"), dict) else {}
            factors.append({
                "source": factor.get("source"),
                "planet": factor.get("planet"),
                "polarity": factor.get("polarity"),
                "weight": factor.get("weight"),
                "facts": {
                    key: facts.get(key)
                    for key in (
                        "dignity", "combustion", "neecha_bhanga", "placement_house",
                        "relation", "functional_role", "ruled_houses", "yogakaraka",
                        "dispositor", "dispositor_house", "compound_relation",
                        "direct_relations", "nakshatra_name", "nakshatra_lord", "chain",
                        "origin", "karaka_for_house", "natural_nature", "roles",
                        "target_house", "special_sign", "special_sign_name",
                        "dagdha_sign", "dagdha_sign_name", "tithi_shunya_sign",
                        "tithi_shunya_sign_name", "avayogi_tithi_shunya_overlap",
                        "avayogi_overlap", "gandanta_name", "gandanta_type",
                        "intensity", "distance_from_junction", "statuses",
                    )
                    if facts.get(key) not in (None, "", [], (), {})
                },
            })
        rows.append({
            "house": house,
            "lord": promise.get("lord"),
            "occupants": list(promise.get("occupants") or ()),
            "aspecting_planets": list(promise.get("aspecting_planets") or ()),
            "karakas": list(promise.get("karakas") or ()),
            "yogas": [
                {
                    "key": key,
                    "name": (yoga_by_key.get(str(key)) or {}).get("name"),
                    "planets": list((yoga_by_key.get(str(key)) or {}).get("planets") or ()),
                }
                for key in promise.get("yogas") or ()
            ],
            "tone": promise.get("tone"),
            "supportive_weight": promise.get("supportive_weight"),
            "challenging_weight": promise.get("challenging_weight"),
            "factors": factors,
        })
    return {
        "source": "validated_d1_natal_promise",
        "policy_version": next((row.get("policy_version") for row in promises), None),
        "houses": rows,
    } if rows else {}


def _compact_marriage_pathway_evidence(
    natal_topic_factors: Any,
    divisional_support: Any,
) -> Dict[str, Any]:
    """Bounded D1/D9 evidence for love-led versus family-mediated marriage."""
    wanted = {2, 5, 7, 9, 11}
    natal = natal_topic_factors if isinstance(natal_topic_factors, dict) else {}
    rows: List[Dict[str, Any]] = []
    lord_links: List[Dict[str, Any]] = []
    for row in natal.get("houses") or []:
        if not isinstance(row, dict) or _safe_int(row.get("house")) not in wanted:
            continue
        factors = []
        for factor in list(row.get("factors") or [])[:8]:
            if not isinstance(factor, dict):
                continue
            factors.append({
                key: factor.get(key)
                for key in ("source", "planet", "polarity", "weight", "facts")
                if factor.get(key) not in (None, "", [], {})
            })
        lord = str(row.get("lord") or "").strip()
        lord_placement_house = None
        for factor in factors:
            facts = factor.get("facts") if isinstance(factor.get("facts"), dict) else {}
            if str(factor.get("planet") or "").strip() == lord:
                lord_placement_house = _safe_int(facts.get("placement_house"))
                if lord_placement_house is not None:
                    break
        compact_row = {
            key: value
            for key, value in {
                "house": row.get("house"),
                "lord": lord,
                "lord_placement_house": lord_placement_house,
                "occupants": list(row.get("occupants") or []),
                "aspecting_planets": list(row.get("aspecting_planets") or []),
                "karakas": list(row.get("karakas") or []),
                "tone": row.get("tone"),
                "supportive_weight": row.get("supportive_weight"),
                "challenging_weight": row.get("challenging_weight"),
                "factors": factors,
            }.items()
            if value not in (None, "", [], {})
        }
        rows.append(compact_row)
        if lord and lord_placement_house in wanted:
            lord_links.append({
                "from_house": int(row.get("house")),
                "lord": lord,
                "to_house": lord_placement_house,
                "source_house_tone": row.get("tone"),
                "claim_rule": "This is a natal lord-placement link, not a dasha or transit activation.",
            })
    rows.sort(key=lambda row: int(row.get("house") or 0))
    return {
        "scope": "static natal pathway comparison",
        "love_led_houses": [5, 7],
        "family_mediated_houses": [2, 7, 9, 11],
        "comparison_rule": (
            "Compare actual links, lord/occupant/aspect evidence and tone across both pathways. "
            "Do not infer a link merely because both house rows exist. D9 may confirm or qualify D1, not replace it."
        ),
        "tone_fidelity_rule": (
            "Copy each D1 house tone exactly. Challenging is not supportive; mixed is not strongly supportive. "
            "Do not call any static house active or activated."
        ),
        "d1_house_evidence": rows,
        "natal_lord_links": lord_links,
        "d9_confirmation": _compact_divisional_topic_payload(
            divisional_support if isinstance(divisional_support, dict) else {}
        ),
    } if rows else {}


_SPOUSE_MEETING_CHANNELS = {
    1: "through personal initiative or a setting centered on the native",
    2: "through family, relatives, shared values, food, finance or a family-linked setting",
    3: "through communication, siblings, neighbors, short travel, messages or a local connection",
    4: "through home, family roots, property, education or a familiar residential setting",
    5: "through romance, studies, creativity, entertainment, children or a hobby",
    6: "through work routines, service, colleagues, health care or a practical obligation",
    7: "through a direct introduction, client, agreement, business contact or one-to-one setting",
    8: "through in-laws, shared resources, research, healing or a major life transition",
    9: "through higher education, long travel, religion, ceremony, a mentor or a different background",
    10: "through career, public life, authority, reputation or a professional setting",
    11: "through friends, groups, professional networks, community or social connections",
    12: "through distance, a foreign link, travel, a private setting, retreat or institution",
}


def _compact_spouse_meeting_evidence(
    natal_topic_factors: Any,
    person_profile_axes: Any,
    divisional_support: Any,
) -> Dict[str, Any]:
    """Build a natal-only, auditable probable spouse-meeting channel."""
    natal = natal_topic_factors if isinstance(natal_topic_factors, dict) else {}
    wanted = {3, 7, 9, 11, 12}
    rows: List[Dict[str, Any]] = []
    seventh_lord = ""
    seventh_lord_house = None
    for row in natal.get("houses") or []:
        if not isinstance(row, dict) or _safe_int(row.get("house")) not in wanted:
            continue
        house = int(row.get("house"))
        lord = str(row.get("lord") or "").strip()
        factors = []
        for factor in list(row.get("factors") or [])[:8]:
            if not isinstance(factor, dict):
                continue
            compact_factor = {
                key: factor.get(key)
                for key in ("source", "planet", "polarity", "weight", "facts")
                if factor.get(key) not in (None, "", [], {})
            }
            factors.append(compact_factor)
            facts = compact_factor.get("facts") if isinstance(compact_factor.get("facts"), dict) else {}
            if house == 7 and str(compact_factor.get("planet") or "").strip() == lord:
                placement = _safe_int(facts.get("placement_house"))
                if placement is not None:
                    seventh_lord = lord
                    seventh_lord_house = placement
        rows.append({
            key: value
            for key, value in {
                "house": house,
                "channel_meaning": _SPOUSE_MEETING_CHANNELS[house],
                "lord": lord,
                "occupants": list(row.get("occupants") or []),
                "aspecting_planets": list(row.get("aspecting_planets") or []),
                "tone": row.get("tone"),
                "supportive_weight": row.get("supportive_weight"),
                "challenging_weight": row.get("challenging_weight"),
                "factors": factors,
            }.items()
            if value not in (None, "", [], {})
        })
    rows.sort(key=lambda row: int(row.get("house") or 0))
    static_profile = [
        str(line) for line in (person_profile_axes or [])
        if str(line).strip() and not re.search(r"\b(current|active|dasha|period|transit)\b", str(line), re.I)
    ][:4]
    d9 = _compact_divisional_topic_payload(
        divisional_support if isinstance(divisional_support, dict) else {}
    ).get("topic") or {}
    required_present = {int(row["house"]) for row in rows}
    return {
        "scope": "static natal meeting-channel probability; no timing",
        "required_channel_houses": [3, 7, 9, 11, 12],
        "required_channel_houses_present": sorted(required_present),
        "evidence_complete": wanted.issubset(required_present) and seventh_lord_house is not None and bool(d9),
        "primary_channel": ({
            "basis": "seventh-lord natal placement",
            "seventh_lord": seventh_lord,
            "placement_house": seventh_lord_house,
            "probable_context": _SPOUSE_MEETING_CHANNELS.get(seventh_lord_house),
            "claim_rule": "This is a probable context from natal placement, not a known fact or a timing activation.",
        } if seventh_lord_house is not None else {}),
        "channel_house_evidence": rows,
        "derived_spouse_frame": static_profile,
        "d9_confirmation": d9,
        "answer_rule": (
            "Lead with the seventh-lord destination as the primary probable context. Add a secondary channel only "
            "when its house row supplies a concrete lord, occupant, aspect or tone connection. Copy tones exactly."
        ),
        "forbidden_inferences": [
            "Do not infer work or duty from Saturn unless House 6 or House 10 is the supplied meeting context.",
            "Do not infer a shared circle unless House 11 is concretely supported.",
            "Do not mention dasha, transit, a Saturn-driven period, a date or a life phase.",
            "Do not claim the probable context is how the meeting factually happened without user confirmation.",
        ],
    }


def _compact_spouse_temperament_evidence(
    chart_data: Any,
    natal_topic_factors: Any,
    karaka_evidence: Any,
    divisional_support: Any,
) -> Dict[str, Any]:
    """Five-layer natal spouse-temperament evidence for the Instant composer."""
    chart = chart_data if isinstance(chart_data, dict) else {}
    planets = chart.get("planets") if isinstance(chart.get("planets"), dict) else {}
    natal = natal_topic_factors if isinstance(natal_topic_factors, dict) else {}
    try:
        from reports.context.shared_branch_context import build_nakshatra_context

        nakshatras = build_nakshatra_context(chart).get("positions") or {}
    except Exception:
        logger.exception("Instant spouse temperament nakshatra calculation failed")
        nakshatras = {}

    def planet_layer(planet: Any, *, role: str) -> Dict[str, Any]:
        name = str(planet or "").strip()
        row = planets.get(name) if isinstance(planets.get(name), dict) else {}
        nak = nakshatras.get(name) if isinstance(nakshatras.get(name), dict) else {}
        sign_index = _sign_index_from_row(row)
        return {
            key: value
            for key, value in {
                "role": role,
                "planet": name,
                "house": _safe_int(row.get("house")),
                "rashi": SIGN_NAMES[sign_index] if sign_index is not None else row.get("sign_name"),
                "degree_in_rashi": round(float(row.get("longitude")) % 30, 3) if row.get("longitude") is not None else None,
                "nakshatra": nak.get("nakshatra_name") or nak.get("name") or nak.get("nakshatra"),
                "nakshatra_lord": nak.get("nakshatra_lord") or nak.get("lord"),
                "nakshatra_deity": nak.get("nakshatra_deity") or nak.get("deity"),
                "pada": nak.get("pada"),
                "conjunctions": [
                    other for other, other_row in planets.items()
                    if other != name
                    and isinstance(other_row, dict)
                    and _safe_int(other_row.get("house")) == _safe_int(row.get("house"))
                ],
            }.items()
            if value not in (None, "", [], {})
        }

    seventh = next(
        (row for row in natal.get("houses") or [] if isinstance(row, dict) and _safe_int(row.get("house")) == 7),
        {},
    )
    seventh_lord = str(seventh.get("lord") or "").strip()
    seventh_house = {
        key: value for key, value in {
            "house": 7,
            "lord": seventh_lord,
            "occupants": list(seventh.get("occupants") or []),
            "aspecting_planets": list(seventh.get("aspecting_planets") or []),
            "tone": seventh.get("tone"),
            "supportive_weight": seventh.get("supportive_weight"),
            "challenging_weight": seventh.get("challenging_weight"),
            "factors": list(seventh.get("factors") or [])[:8],
        }.items() if value not in (None, "", [], {})
    }
    karakas = (
        karaka_evidence.get("chara_karakas")
        if isinstance(karaka_evidence, dict) and isinstance(karaka_evidence.get("chara_karakas"), dict)
        else {}
    )
    darakaraka_row = karakas.get("Darakaraka") if isinstance(karakas.get("Darakaraka"), dict) else {}
    darakaraka = planet_layer(darakaraka_row.get("planet"), role="Darakaraka · spouse significator")
    if darakaraka:
        darakaraka["chara_karaka_degree_in_rashi"] = darakaraka_row.get("degree_in_sign")
        darakaraka["calculation_method"] = (
            karaka_evidence.get("calculation_method")
            if isinstance(karaka_evidence, dict)
            else None
        )
    d9_topic = _compact_divisional_topic_payload(
        divisional_support if isinstance(divisional_support, dict) else {}
    ).get("topic") or {}
    d9_chart = (d9_topic.get("charts") or {}).get("D9") if isinstance(d9_topic.get("charts"), dict) else {}
    layers = {
        "seventh_house": seventh_house,
        "seventh_lord_rashi_nakshatra": planet_layer(
            seventh_lord, role="seventh lord · spouse temperament anchor",
        ),
        "darakaraka_rashi_nakshatra": darakaraka,
        "venus_rashi_nakshatra": planet_layer(
            "Venus", role="Venus · relationship style and affection",
        ),
        "d9_confirmation": d9_chart if isinstance(d9_chart, dict) else {},
    }
    missing = [key for key, value in layers.items() if not value]
    return {
        "scope": "static natal spouse temperament; no timing",
        "layers": layers,
        "evidence_complete": not missing,
        "missing_layers": missing,
        "synthesis_rule": (
            "Synthesize all five layers. The seventh house/lord anchors observable temperament; the seventh-lord "
            "nakshatra refines instinctive style; Darakaraka adds the spouse archetype; Venus describes relating and "
            "affection; D9 confirms or qualifies. No single planet may become the whole personality."
        ),
        "fidelity_rules": [
            "Copy rashi, nakshatra, lord, pada, house and tone exactly.",
            "Do not infer temperament from the seventh house alone.",
            "Do not use current dasha, transit, activation or timing.",
            "Describe probable traits, not hidden motives, mental-health diagnoses or fixed identity.",
        ],
    }


def _spouse_detail_scope(question: str, intent: Any) -> Optional[str]:
    routed = intent if isinstance(intent, dict) else {}
    extracted = routed.get("extracted_context") if isinstance(routed.get("extracted_context"), dict) else {}
    explicit = str(extracted.get("spouse_detail_scope") or "").strip().lower()
    if explicit in {"profession", "location", "appearance", "combined"}:
        return explicit
    text = f"{extracted.get('requested_fact') or ''} {question or ''}".lower()
    if any(marker in text for marker in (
        "appearance", "physical", "look like", "looks like", "how will they look",
        "height", "build", "complexion", "face", "facial", "body type",
    )):
        return "appearance"
    if any(marker in text for marker in (
        "different city", "different culture", "different background", "foreign background",
        "where from", "which city", "which country", "spouse location", "geographical background",
        "cultural background", "distant place", "another city", "another country",
    )):
        return "location"
    return None


def _compact_spouse_appearance_evidence(
    chart_data: Any,
    natal_topic_factors: Any,
    karaka_evidence: Any,
    divisional_support: Any,
) -> Dict[str, Any]:
    """Placement facts used only for a bounded spouse-appearance reading."""
    temperament = _compact_spouse_temperament_evidence(
        chart_data, natal_topic_factors, karaka_evidence, divisional_support,
    )
    chart = chart_data if isinstance(chart_data, dict) else {}
    ascendant = chart.get("ascendant")
    try:
        ascendant_sign = int(float(ascendant) / 30) % 12
    except (TypeError, ValueError):
        ascendant_sign = None
    seventh_sign = ((ascendant_sign + 6) % 12) if ascendant_sign is not None else None
    source_layers = temperament.get("layers") if isinstance(temperament.get("layers"), dict) else {}
    seventh = source_layers.get("seventh_house") if isinstance(source_layers.get("seventh_house"), dict) else {}
    layers = {
        "seventh_house_sign": {
            key: value for key, value in {
                "house": 7,
                "rashi": SIGN_NAMES[seventh_sign] if seventh_sign is not None else None,
                "lord": seventh.get("lord"),
                "occupants": list(seventh.get("occupants") or []),
                "aspecting_planets": list(seventh.get("aspecting_planets") or []),
                "tone": seventh.get("tone"),
            }.items() if value not in (None, "", [], {})
        },
        "seventh_lord_rashi_nakshatra": source_layers.get("seventh_lord_rashi_nakshatra") or {},
        "darakaraka_rashi_nakshatra": source_layers.get("darakaraka_rashi_nakshatra") or {},
        "venus_rashi_nakshatra": source_layers.get("venus_rashi_nakshatra") or {},
        "d9_confirmation": source_layers.get("d9_confirmation") or {},
    }
    missing = [key for key, value in layers.items() if not value]
    return {
        "scope": "spouse physical appearance and visual presence only; no temperament, profession, location or timing",
        "layers": layers,
        "evidence_complete": not missing,
        "missing_layers": missing,
        "appearance_dimensions": [
            "overall build and stature band",
            "face and expression",
            "visual style and grooming",
            "distinctive presence or mannerisms visible to others",
        ],
        "synthesis_rule": (
            "Translate only convergent physical symbolism across the seventh-house rashi, seventh lord, Darakaraka, "
            "Venus and D9. Separate likely build, facial/expression qualities and visual style; conflicts must be "
            "reported as a range rather than silently choosing one placement."
        ),
        "fidelity_rules": [
            "Answer appearance directly; do not substitute personality, compatibility or married-life advice.",
            "Use probable bands such as lean-to-medium or medium-to-solid, never exact measurements.",
            "Do not infer ethnicity, caste, nationality, disability, medical condition or exact skin colour.",
            "Do not use dasha, transit, activation, dates or current periods.",
            "Disclose that this is a symbolic appearance range from the native chart, not a photograph or certainty.",
        ],
    }


def _compact_spouse_location_evidence(
    chart_data: Any,
    natal_topic_factors: Any,
    karaka_evidence: Any,
    divisional_support: Any,
) -> Dict[str, Any]:
    """Calculate bounded local-versus-different-background spouse evidence."""
    temperament = _compact_spouse_temperament_evidence(
        chart_data, natal_topic_factors, karaka_evidence, divisional_support,
    )
    layers = temperament.get("layers") if isinstance(temperament.get("layers"), dict) else {}
    seventh_lord = layers.get("seventh_lord_rashi_nakshatra") if isinstance(layers.get("seventh_lord_rashi_nakshatra"), dict) else {}
    darakaraka = layers.get("darakaraka_rashi_nakshatra") if isinstance(layers.get("darakaraka_rashi_nakshatra"), dict) else {}
    seventh_house = layers.get("seventh_house") if isinstance(layers.get("seventh_house"), dict) else {}
    d9 = layers.get("d9_confirmation") if isinstance(layers.get("d9_confirmation"), dict) else {}

    distance_signals: List[Dict[str, Any]] = []
    local_signals: List[Dict[str, Any]] = []

    def placement_signal(source: str, row: Dict[str, Any]) -> None:
        house = _safe_int(row.get("house"))
        if house == 3:
            distance_signals.append({"source": source, "weight": 2.0, "meaning": "different city or mobile regional connection", "fact": f"placed in house {house}"})
        elif house == 9:
            distance_signals.append({"source": source, "weight": 3.0, "meaning": "distant region, worldview or cultural difference", "fact": f"placed in house {house}"})
        elif house == 12:
            distance_signals.append({"source": source, "weight": 3.0, "meaning": "foreign or far-away connection", "fact": f"placed in house {house}"})
        elif house == 4:
            local_signals.append({"source": source, "weight": 3.0, "meaning": "same-region, familiar-root or home-linked connection", "fact": f"placed in house {house}"})

        sign = str(row.get("rashi") or "")
        if sign in {"Aries", "Cancer", "Libra", "Capricorn"}:
            distance_signals.append({"source": source, "weight": 0.5, "meaning": "mobility modifier only", "fact": f"in movable rashi {sign}"})
        elif sign in {"Taurus", "Leo", "Scorpio", "Aquarius"}:
            local_signals.append({"source": source, "weight": 0.5, "meaning": "rootedness modifier only", "fact": f"in fixed rashi {sign}"})

        conjunctions = {str(value) for value in row.get("conjunctions") or []}
        if "Rahu" in conjunctions:
            distance_signals.append({
                "source": source, "weight": 2.0,
                "meaning": "unconventional or cross-cultural modifier",
                "fact": "conjunct Rahu",
            })

    placement_signal("seventh lord", seventh_lord)
    placement_signal("Darakaraka", darakaraka)
    seventh_occupants = {str(value) for value in seventh_house.get("occupants") or []}
    if "Rahu" in seventh_occupants:
        distance_signals.append({
            "source": "seventh house", "weight": 2.0,
            "meaning": "unconventional or cross-cultural partnership modifier",
            "fact": "Rahu occupies house 7",
        })

    distance_score = round(sum(float(row["weight"]) for row in distance_signals), 2)
    local_score = round(sum(float(row["weight"]) for row in local_signals), 2)
    strong_distance = sum(float(row["weight"]) for row in distance_signals if float(row["weight"]) >= 2)
    strong_local = sum(float(row["weight"]) for row in local_signals if float(row["weight"]) >= 2)
    if strong_distance >= 3 and distance_score >= local_score + 1:
        verdict = "different_city_culture_or_background_supported"
    elif strong_local >= 3 and local_score >= distance_score + 1:
        verdict = "local_or_familiar_background_supported"
    elif strong_distance >= 2 and strong_local >= 2:
        verdict = "mixed_distance_and_local_signals"
    else:
        verdict = "insufficient_specific_distance_evidence"

    evidence_layers = {
        "seventh_house": seventh_house,
        "seventh_lord_location": seventh_lord,
        "darakaraka_location": darakaraka,
        "d9_confirmation": d9,
    }
    missing = [key for key, value in evidence_layers.items() if not value]
    return {
        "scope": "static spouse city, cultural or geographical-background tendency; no timing",
        "layers": evidence_layers,
        "distance_signals": distance_signals,
        "local_signals": local_signals,
        "distance_score": distance_score,
        "local_score": local_score,
        "verdict": verdict,
        "evidence_complete": not missing,
        "missing_layers": missing,
        "decision_rules": [
            "Only direct spouse links to houses 3, 9 or 12, or explicit Rahu linkage, can materially support a different-city/culture/background claim.",
            "House 4 directly connected to spouse indicators supports familiar or local roots.",
            "Movable or fixed rashi is a weak modifier and cannot decide the verdict alone.",
            "A planet's generic nature, nakshatra folklore or timing activation cannot prove foreignness.",
            "D9 may confirm or qualify but cannot manufacture a distance claim absent a supplied link.",
        ],
    }


def _compact_career_foundation(
    category: str,
    routed_subtype: Any,
    natal_topic_factors: Any,
    divisional_support: Any,
    chart_facts: Any = None,
    karaka_evidence: Any = None,
    profession_evidence: Any = None,
) -> Dict[str, Any]:
    """Build the bounded D1 + D10 professional foundation sent to Instant.

    The full natal audit remains available to the evidence UI.  The writer gets
    only the relevant professional houses and the already-calculated D10 rows,
    preventing both missing-D1 answers and large-context regression.
    """
    profile = career_profile(category, routed_subtype)
    wanted = set(profile["houses"])
    d1_rows: List[Dict[str, Any]] = []
    natal = natal_topic_factors if isinstance(natal_topic_factors, dict) else {}
    for row in natal.get("houses") or []:
        if not isinstance(row, dict) or _safe_int(row.get("house")) not in wanted:
            continue
        factors = []
        for factor in row.get("factors") or []:
            if not isinstance(factor, dict):
                continue
            facts = factor.get("facts") if isinstance(factor.get("facts"), dict) else {}
            factors.append({
                "planet": factor.get("planet"),
                "source": factor.get("source"),
                "polarity": factor.get("polarity"),
                "functional_role": facts.get("functional_role"),
                "dignity": facts.get("dignity"),
                "placement_house": facts.get("placement_house"),
            })
        d1_rows.append({
            "house": row.get("house"),
            "lord": row.get("lord"),
            "lord_placement_house": row.get("lord_placement_house"),
            "occupants": list(row.get("occupants") or []),
            "aspects": list(row.get("aspecting_planets") or []),
            "tone": row.get("tone"),
            "key_factors": factors[:4],
        })
    compact_divisional = _compact_divisional_topic_payload(
        divisional_support if isinstance(divisional_support, dict) else {}
    )
    d10: Dict[str, Any] = {}
    for bucket_name in ("topic", "current_topic"):
        bucket = compact_divisional.get(bucket_name) or {}
        chart = (bucket.get("charts") or {}).get("D10") or (bucket.get("charts") or {}).get("10")
        if isinstance(chart, dict):
            d10[bucket_name] = chart
    facts = chart_facts if isinstance(chart_facts, dict) else {}
    calculated_charts = facts.get("charts") if isinstance(facts.get("charts"), dict) else {}
    calculated_d1 = calculated_charts.get("D1") if isinstance(calculated_charts.get("D1"), dict) else {}

    # Some static-career routes do not run the separate natal-promise audit.
    # Build the same bounded professional house rows from the calculated D1
    # chart rather than telling the writer that the career foundation is
    # missing (or leaving it to invent generic professions).
    if not d1_rows and calculated_d1:
        d1_planets = calculated_d1.get("planets") if isinstance(calculated_d1.get("planets"), dict) else {}
        d1_houses = calculated_d1.get("houses") if isinstance(calculated_d1.get("houses"), list) else []
        houses_by_number = {
            _safe_int(row.get("house")): row
            for row in d1_houses
            if isinstance(row, dict) and _safe_int(row.get("house")) is not None
        }
        for house in sorted(wanted):
            house_row = houses_by_number.get(house) or {}
            occupants = list(house_row.get("occupants") or [])
            if not occupants:
                occupants = [
                    str(planet) for planet, placement in d1_planets.items()
                    if isinstance(placement, dict) and _norm_house(placement.get("house")) == house
                ]
            aspects = [
                str(planet) for planet, placement in d1_planets.items()
                if isinstance(placement, dict) and house in (placement.get("aspects_to_houses") or [])
            ]
            d1_rows.append({
                "house": house,
                "lord": house_row.get("lord"),
                "lord_placement_house": next((
                    placement.get("house")
                    for planet, placement in d1_planets.items()
                    if isinstance(placement, dict) and str(planet) == str(house_row.get("lord"))
                ), None),
                "occupants": occupants,
                "aspects": aspects,
                "tone": None,
                "source": "authoritative_calculated_D1",
            })
    if isinstance(calculated_charts.get("D10"), dict):
        d10["calculated_chart"] = calculated_charts["D10"]
    karakas = (
        karaka_evidence.get("chara_karakas")
        if isinstance(karaka_evidence, dict) and isinstance(karaka_evidence.get("chara_karakas"), dict)
        else {}
    )
    amatyakaraka = karakas.get("Amatyakaraka") if isinstance(karakas.get("Amatyakaraka"), dict) else {}
    karkamsa = calculated_charts.get("KARAKAMSHA")
    profession = dict(profession_evidence) if isinstance(profession_evidence, dict) else {}
    calculated_d10 = d10.get("calculated_chart") if isinstance(d10.get("calculated_chart"), dict) else {}
    vocation_synthesis = build_vocation_synthesis(
        d1_houses=d1_rows,
        d1_chart=calculated_d1,
        d10_chart=calculated_d10,
        amatyakaraka=amatyakaraka,
        karakamsha_chart=karkamsa if isinstance(karkamsa, dict) else {},
        planetary_strengths=profession.get("planetary_strengths") or {},
    )
    # Never expose the old strongest-planet recommendation as a competing
    # answer source. The audit copy remains available under an explicit legacy
    # key, while all answer-bearing fields come from repeated chart evidence.
    profession["vocation_synthesis"] = vocation_synthesis
    profession["ranked_fields"] = vocation_synthesis.get("suitable_fields") or []
    mandatory_missing = []
    if not d1_rows:
        mandatory_missing.append("D1")
    if not d10:
        mandatory_missing.append("D10")
    return {
        "career_subtype": profile["subtype"],
        "focus_houses": profile["houses"],
        "career_planets": profile["planets"],
        "D1": {"source": natal.get("source"), "houses": d1_rows},
        "D10": d10,
        "amatyakaraka": {
            "planet": amatyakaraka.get("planet"),
            "house": amatyakaraka.get("house"),
            "sign": amatyakaraka.get("sign"),
            "degree_in_sign": amatyakaraka.get("degree_in_sign"),
        } if amatyakaraka else {},
        "KARAKAMSHA": karkamsa if isinstance(karkamsa, dict) else {},
        "career_fit": profession,
        "vocation_synthesis": vocation_synthesis,
        "mandatory_evidence_complete": not mandatory_missing,
        "missing_mandatory_evidence": mandatory_missing,
        "interpretation_rules": [
            "D1 establishes professional promise and life-level delivery.",
            "D10 confirms role, work environment, authority and professional expression.",
            "House 2 describes pay or resources only; it must not replace the career verdict.",
            "If mandatory_evidence_complete is false, state that the reading is limited; never convert missing evidence into a negative career verdict.",
            "For a static career profile, synthesize D1 and D10 first, then use Amatyakaraka and Karkamsa as the Jaimini vocation signature.",
            "For vocation, use vocation_synthesis as the controlling result: work functions first, then suitable fields, environment, and job/business/hybrid structure.",
            "Within vocation_synthesis, read tenth_lord_signature and combination_signatures first. A planet conjoined with the D1 10th lord modifies the profession itself; do not treat it as a generic occupant of the 10th lord's placement house.",
            "When Mars, Saturn and Rahu connect to the D1 10th lord, explicitly consider engineering, technical systems, software, automation, AI/digital platforms and emerging technology. Jupiter in that cluster adds architecture, strategy, knowledge and advisory responsibility. Present these as supported vocational directions, not a guaranteed job title.",
            "Only recommend work functions, fields, and environments present in vocation_synthesis. Never invent adjacent professions or generic career labels.",
            "If vocation_synthesis.suitable_fields is empty, say the calculated vocation signature is incomplete and ask one focused clarification instead of guessing.",
            "Do not infer a profession from a single strong planet or from Shadbala alone; strength only qualifies a vocation signature already repeated across charts.",
            "Do not introduce dasha, transit, dates, peaks, or delivery windows unless the user asks when, names a period, or asks about a time-bound outcome.",
            "For career fit, use the deterministic career_fit packet for ranked fields; use Amatyakaraka and Karkamsa as confirmation after D1 and D10.",
        ],
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
    marriage_subtype = str((intent or {}).get("marriage_subtype") or "").lower()
    marriage_route_houses = {
        "love_vs_arranged": [2, 5, 7, 9, 11],
        "spouse_meeting": [3, 7, 9, 11, 12],
        "spouse_details": [4, 7, 9, 10, 12],
    }
    if str(category or "").lower() == "marriage" and marriage_subtype in marriage_route_houses:
        focus = {**focus, "houses": marriage_route_houses[marriage_subtype]}
    if marriage_subtype == "spouse_details" and _spouse_detail_scope(question, intent) == "location":
        focus = {**focus, "houses": [3, 4, 7, 9, 12]}
    focus_planets = set(focus["planets"]) | {"Moon"}

    query_context = (intent or {}).get("query_context") if isinstance((intent or {}).get("query_context"), dict) else None
    extracted_context = (intent or {}).get("extracted_context") if isinstance((intent or {}).get("extracted_context"), dict) else {}
    now_local = resolve_query_now(query_context)
    resolved_answer_mode = str(answer_mode_override or "").strip()
    retrospective_event = _is_retrospective_event_request(
        intent,
        answer_mode=resolved_answer_mode,
        category=category,
        question=question,
    )
    period_window = _resolve_period_window(intent, now_local, question)
    # Event-window scans always start from the actual query date. The legacy
    # period resolver treats phrases containing "year" as a calendar-year
    # outlook and can otherwise anchor "next three years" to 1 January.
    if _should_force_event_current_window(resolved_answer_mode, period_window) and not retrospective_event:
        period_window = {
            "kind": "current",
            "start": now_local.strftime("%Y-%m-%d"),
            "end": now_local.strftime("%Y-%m-%d"),
            "span_days": 1,
            "label": now_local.strftime("%d %B %Y"),
            "use_pd": True,
            "use_sk_pr": False,
        }
    if retrospective_event:
        birth_start = _parse_birth_date_only(birth_data)
        if birth_start is not None:
            try:
                history_start = birth_start.replace(year=birth_start.year + 16)
            except ValueError:
                history_start = birth_start.replace(year=birth_start.year + 16, day=28)
        else:
            history_start = now_local - timedelta(days=365 * 40)
        period_window = {
            "kind": "historical_range",
            "start": history_start.strftime("%Y-%m-%d"),
            "end": now_local.strftime("%Y-%m-%d"),
            "span_days": max(1, (now_local.date() - history_start.date()).days),
            "label": "probable past event periods",
            "use_pd": True,
            "use_sk_pr": False,
        }
    time_relation = _period_time_relation(period_window, now_local)
    if retrospective_event:
        time_relation = "past"
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
    # The intent LLM, not language-specific Python parsing, decides whether the
    # user answered the open clarification or started a different request.  Old
    # marriage/career/etc. context must not steer the composer after a new ask.
    if str((intent or {}).get("turn_relation") or "").strip().lower() == "new_request":
        recent_history = []

    complexity_hint = {
        "mode": str((intent or {}).get("mode") or "birth"),
        "needs_transits": bool((intent or {}).get("needs_transits")),
        "has_multiple_parts": "?" in question and question.count("?") > 1,
        "question_length": len(question or ""),
    }

    answer_mode = str(answer_mode_override or "").strip() or _infer_answer_mode(question, intent, history)
    # Retrospective life-event discovery always needs the historical event
    # scanner. A router may label the surface request ``timing_window``; keep
    # that harmless variation from bypassing the event-prediction scan below.
    if retrospective_event:
        answer_mode = "event_prediction"
    target_subject = target_subject_override if isinstance(target_subject_override, dict) else None
    if (
        answer_mode == "remedy_action"
        and str(category or "").lower() in {"marriage", "relationship", "love"}
        and str((target_subject or {}).get("key") or "").lower() in {"spouse", "wife", "husband", "partner"}
        and not re.search(r"\b(?:for|help|support)\s+(?:my\s+)?(?:spouse|wife|husband|partner)\b", str(question or ""), re.IGNORECASE)
    ):
        # "marital conflict" concerns the native's relationship, not a
        # derived spouse chart. Keep an explicit "remedy for my spouse" as a
        # true other-person request.
        target_subject = {
            "key": "self", "label": "self", "base_house": 1,
            "confidence": "high", "source": "marriage_remedy_native_frame",
        }
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
    marriage_subtype = str((intent or {}).get("marriage_subtype") or "").lower()
    marriage_route_houses = {
        "love_vs_arranged": [2, 5, 7, 9, 11],
        "spouse_meeting": [3, 7, 9, 11, 12],
        "spouse_details": [4, 7, 9, 10, 12],
    }
    if str(category or "").lower() == "marriage" and marriage_subtype in marriage_route_houses:
        focus = {**focus, "houses": marriage_route_houses[marriage_subtype]}
    if marriage_subtype == "spouse_details" and _spouse_detail_scope(question, intent) == "location":
        focus = {**focus, "houses": [3, 4, 7, 9, 12]}
    if (
        answer_mode == "remedy_action"
        and str(category or "").lower() in {"marriage", "relationship", "love", "partner", "spouse"}
        and any(marker in str(question or "").lower() for marker in ("conflict", "argument", "fight", "friction"))
    ):
        focus = {**focus, "houses": [2, 6, 7, 8, 11, 12]}
        instant_parashari["focus_houses"] = list(focus["houses"])
    instant_parashari["natal_topic_factors"] = _compact_natal_topic_factors(
        chart_data,
        list(focus.get("houses") or []),
        birth_data,
    )
    
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
    if answer_mode == "event_prediction" and not retrospective_event:
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
    if answer_mode == "event_prediction" and retrospective_event:
        instant_parashari["timing_policy"] = {
            "time_direction": "retrospective",
            "claim_type": "probable_past_periods_only",
            "rule": (
                "Rank past marriage-capable periods from natal promise, D9, dasha carriers and historical "
                "transit reinforcement. Never claim the actual marriage date without user confirmation."
            ),
        }
        history_start = _parse_ymd(period_window.get("start")) or (now_local - timedelta(days=365 * 40))
        history_end = _parse_ymd(period_window.get("end")) or now_local
        historical_raw_periods: List[Dict[str, Any]] = []
        try:
            historical_raw_periods = dasha_calc.get_dasha_periods_for_range(
                birth_data,
                _as_naive_local_datetime(history_start),
                _as_naive_local_datetime(history_end),
            )
        except Exception as exc:
            logger.warning("historical marriage dasha prebuild failed: %s", exc)
        natal_candidates = _build_forward_event_dasha_scan(
            birth_data=birth_data,
            now_local=now_local,
            house_lordships=dict(house_lordships),
            focus_houses=list(focus["houses"]),
            category=category,
            chart_data=chart_data,
            current_dashas=current_dashas,
            raw_periods=historical_raw_periods,
            scan_start=history_start,
            scan_end=history_end,
            time_direction="past",
            limit=max(1, len(historical_raw_periods)),
        )
        historical_candidates = _historical_marriage_candidate_pool(
            list(natal_candidates.get("periods") or []),
            dict(house_lordships),
        )
        historical_scan = _build_forward_event_dasha_scan(
            birth_data=birth_data,
            now_local=now_local,
            house_lordships=dict(house_lordships),
            focus_houses=list(focus["houses"]),
            category=category,
            chart_data=chart_data,
            transit_calc=transit_calc,
            ascendant_longitude=ascendant_longitude,
            current_dashas=current_dashas,
            raw_periods=historical_candidates,
            scan_start=history_start,
            scan_end=history_end,
            time_direction="past",
            limit=max(1, len(historical_candidates)),
        )
        phase_bounds: Dict[tuple[str, str], tuple[str, str]] = {}
        for row in natal_candidates.get("periods") or []:
            if not isinstance(row, dict):
                continue
            phase = (str(row.get("mahadasha") or ""), str(row.get("antardasha") or ""))
            start = str(row.get("start") or "")
            end = str(row.get("end") or "")
            if not start or not end:
                continue
            current = phase_bounds.get(phase)
            phase_bounds[phase] = (
                min(start, current[0]) if current else start,
                max(end, current[1]) if current else end,
            )
        historical_scan["periods"] = _rank_historical_marriage_periods(
            list(historical_scan.get("periods") or []),
            dict(house_lordships),
            limit=12,
            phase_bounds=phase_bounds,
        )
        historical_scan["candidate_pool_size"] = len(historical_candidates)
        historical_scan["ranking_method"] = "marriage_evidence_then_historical_transit"
        historical_scan["claim_rule"] = (
            "These are ranked probable periods, not the known or proven marriage date. Ask the user which period matches."
        )
        historical_scan["minimum_age"] = 16
        instant_parashari["historical_event_dasha_scan"] = historical_scan
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
        if answer_mode == "event_prediction":
            anchor_house = _safe_int(target_chart_context.get("anchor_house")) or 1
            native_focus_houses, house_display_map = _target_focus_calculation_frame(
                list(focus["houses"]),
                anchor_house,
            )
            # Rebuild target-person timing in the native chart frame.  The
            # native chart owns the dasha, placements and aspects; the explicit
            # display map converts only the resulting meaning back to the
            # spouse/child/parent-relative frame.
            instant_parashari["forward_event_dasha_scan"] = _build_forward_event_dasha_scan(
                birth_data=birth_data,
                now_local=now_local,
                house_lordships=dict(house_lordships),
                focus_houses=native_focus_houses,
                category=category,
                chart_data=chart_data,
                transit_calc=transit_calc,
                ascendant_longitude=ascendant_longitude,
                current_dashas=current_dashas,
                raw_periods=event_horizon_raw_periods,
                house_display_map=house_display_map,
            )
            instant_parashari["horizon_dasha_segments"] = _horizon_dasha_segments_for_event(
                birth_data=birth_data,
                chart_data=chart_data,
                house_lordships=house_lordships,
                now_local=now_local,
                focus_houses=native_focus_houses,
                transit_calc=transit_calc,
                ascendant_longitude=ascendant_longitude,
                category=category,
                raw_periods=event_horizon_raw_periods,
                house_display_map=house_display_map,
            )
            instant_parashari["house_frame"] = {
                "meaning": "target_relative",
                "target_label": str((target_subject or {}).get("label") or "target person"),
                "anchor_native_house": anchor_house,
                "target_relative_focus_houses": list(focus["houses"]),
                "native_calculation_houses": native_focus_houses,
                "native_to_target_house_map": house_display_map,
            }
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
        # The final universal mode is authoritative. A rotated target packet
        # may carry an older/missing answer_mode and previously skipped remedy
        # calculation even though the query plan correctly said remedy_action.
        answer_mode=answer_mode,
        category=category,
        question=question,
        chart_data=chart_data,
        instant_parashari=evidence_instant_parashari,
        current_transits_formatted=evidence_current_transits_context,
        current_dashas_context=evidence_current_dashas_context,
        birth_summary=evidence_birth_summary,
        natal_snapshot=evidence_natal_snapshot,
        relationship_target=target_subject,
        target_chart_context=target_chart_context,
    )
    if answer_mode == "remedy_action" and not (
        isinstance(normalized_evidence.get("remedy_blueprint"), dict)
        and normalized_evidence["remedy_blueprint"].get("top_recommendation")
    ):
        # Retry from the native marriage frame. Remedy selection belongs to
        # the native's relationship chart; an incorrectly rotated spouse
        # target must not suppress the calculator packet.
        _attach_calculated_remedy_blueprint(
            normalized=normalized_evidence,
            chart_data=chart_data,
            question=question,
            category=category,
            instant_parashari=instant_parashari,
            current_dashas_context=current_dashas_context,
            target_chart_context=None,
        )
    # Dedicated calculator adapters. These records are intentionally created
    # only from calculator output; their mere presence in a prompt or method
    # registry never marks a capability as available.
    karaka_evidence = _instant_real_karaka_evidence(chart_data)
    if karaka_evidence:
        normalized_evidence["karaka_evidence"] = karaka_evidence

    nadi_evidence = _instant_real_nadi_evidence(chart_data)
    if nadi_evidence:
        normalized_evidence["nadi_evidence"] = nadi_evidence

    double_transit_evidence = _instant_real_double_transit_evidence(
        chart_data=chart_data,
        start=now_local,
        end=now_local + timedelta(days=_INSTANT_EVENT_HORIZON_DAYS),
        focus_houses=list(focus.get("houses") or []),
        answer_mode=answer_mode,
    )
    if double_transit_evidence:
        normalized_evidence["double_transit"] = double_transit_evidence

    if isinstance(intent, dict):
        try:
            from ai.intent_router import apply_chart_focus_guards
            apply_chart_focus_guards(intent, question)
        except Exception:
            logger.exception("Instant chart-focus guard failed")
        extracted_context = intent.get("extracted_context") if isinstance(intent.get("extracted_context"), dict) else extracted_context
    requested_charts = _requested_charts_from_intent(intent, answer_mode=answer_mode)
    normalized_evidence["chart_facts"] = _instant_real_chart_facts(
        chart_data=chart_data,
        requested_charts=requested_charts,
        requested_fact=extracted_context.get("requested_fact"),
        karaka_evidence=karaka_evidence,
        d1_snapshot=evidence_natal_snapshot,
    )

    location_evidence = _instant_real_location_evidence(
        birth_data=birth_data,
        intent=intent or {},
        chart_data=chart_data,
        current_dashas=current_dashas,
        answer_mode=answer_mode,
    )
    if location_evidence:
        normalized_evidence["location_recommendation"] = location_evidence

    muhurat_evidence = _instant_real_muhurat_evidence(
        birth_data=birth_data,
        intent=intent or {},
        chart_data=chart_data,
        answer_mode=answer_mode,
    )
    if muhurat_evidence:
        normalized_evidence["muhurat_slots"] = muhurat_evidence

    daily_prediction_spine: Dict[str, Any] = {}
    if str((period_window or {}).get("kind") or "").lower() == "day":
        try:
            daily_static_context: Dict[str, Any] = {
                "d1_chart": chart_data,
                "planetary_analysis": chart_data.get("planetary_analysis") or {},
            }
            kp_evidence = _instant_real_kp_evidence(birth_data)
            if kp_evidence:
                daily_static_context["kp_analysis"] = kp_evidence
            if karaka_evidence:
                daily_static_context["chara_karakas"] = karaka_evidence
            daily_prediction_spine = build_daily_prediction_spine(
                birth_data=birth_data,
                static_context=daily_static_context,
                intent_result={
                    **(intent or {}),
                    "mode": "PREDICT_DAILY",
                    "dasha_as_of": (
                        period_window.get("start")
                        or period_window.get("date")
                        or dasha_anchor.strftime("%Y-%m-%d")
                    ),
                    "query_context": query_context,
                },
            ) or {}
            if daily_prediction_spine:
                normalized_evidence["daily_prediction_spine"] = daily_prediction_spine
        except Exception:
            logger.exception("Instant exact-day prediction spine calculation failed")
    if answer_mode == "comparison_choice" and not dasha_calc_fallback:
        comparison_raw_periods: Optional[List[Dict[str, Any]]] = None
        try:
            comparison_raw_periods = dasha_calc.get_dasha_periods_for_range(
                birth_data,
                _as_naive_local_datetime(now_local),
                _as_naive_local_datetime(now_local + timedelta(days=_INSTANT_EVENT_HORIZON_DAYS)),
            )
        except Exception:
            logger.exception("Instant comparison dasha timeline calculation failed")
        option_comparison = _build_comparison_option_evidence(
            evidence_plan=evidence_plan,
            birth_data=birth_data,
            now_local=now_local,
            house_lordships=dict(house_lordships),
            chart_data=chart_data,
            transit_calc=transit_calc,
            ascendant_longitude=ascendant_longitude,
            current_dashas=current_dashas,
            target_subject=target_subject,
            raw_periods=comparison_raw_periods,
        )
        if option_comparison:
            normalized_evidence["option_comparison"] = option_comparison
    health_categories = {"health", "mental_wellbeing", "surgery", "accident", "recovery"}
    if category in health_categories:
        # Body-area claims must come from the established Parashari body-zone
        # calculator, never from the language model's general knowledge.  This
        # is susceptibility evidence only; the answer contract still forbids a
        # diagnosis or medical certainty.
        try:
            from reports.context.health_body_zones import build_priority_body_zones
            from reports.context.shared_branch_context import build_nakshatra_context

            medical_calc_started = time.monotonic()
            health_divisions: Dict[str, Any] = {}
            divisional_calc = DivisionalChartCalculator(chart_data)
            for division_number in (3, 6, 8, 30):
                try:
                    health_divisions[f"D{division_number}"] = (
                        divisional_calc.calculate_divisional_chart(division_number)
                    )
                except Exception:
                    logger.exception(
                        "Instant medical divisional calculation failed D%s",
                        division_number,
                    )

            health_conditions = (
                PlanetaryDignitiesCalculator(chart_data).calculate_planetary_dignities()
            )
            try:
                shadbala = ShadbalaCalculator(chart_data, birth_data).calculate_shadbala()
            except Exception:
                logger.exception("Instant medical Shadbala calculation failed")
                shadbala = {}
            for planet, strength in (shadbala or {}).items():
                if not isinstance(strength, dict):
                    continue
                health_conditions.setdefault(planet, {})["strength_analysis"] = {
                    "total_rupas": strength.get("total_rupas"),
                    "grade": strength.get("grade"),
                    "ishta_percent": strength.get("ishta_percent"),
                    "kashta_percent": strength.get("kashta_percent"),
                    "result_tendency": strength.get("result_tendency"),
                }

            # The medical body-area foundation requires the 6th lord's exact
            # nakshatra.  Reports already supplied this layer, but Instant Chat
            # previously omitted it and therefore could not apply the same
            # classical sixth-house chain.
            sixth_lord = _lord_of_house(house_lordships, 6)
            lords_nakshatra: Dict[str, Any] = {}
            if sixth_lord:
                try:
                    nakshatra_context = build_nakshatra_context(chart_data)
                    nak_positions = (
                        nakshatra_context.get("positions")
                        if isinstance(nakshatra_context, dict)
                        else {}
                    ) or {}
                    nak_row = nak_positions.get(sixth_lord) or {}
                    lords_nakshatra["sixth_lord"] = {
                        "planet": sixth_lord,
                        "nakshatra": {
                            "planet": sixth_lord,
                            "nakshatra": nak_row.get("nakshatra_name") or nak_row.get("nakshatra"),
                            "lord": nak_row.get("nakshatra_lord"),
                            "pada": nak_row.get("pada"),
                            "deity": nak_row.get("nakshatra_deity"),
                            "longitude": nak_row.get("longitude"),
                        },
                    }
                except Exception:
                    logger.exception("Instant medical nakshatra calculation failed")

            body_zone_evidence = build_priority_body_zones(
                chart_data,
                lords_nakshatra=lords_nakshatra,
                current_dashas=current_dashas,
                divisional_charts=health_divisions,
                planet_conditions=health_conditions,
                requested_category=category,
            )
            event_patterns = list(body_zone_evidence.get("event_patterns") or [])
            if category in {"surgery", "accident"}:
                category_marker = "surgery" if category == "surgery" else "accident"
                event_patterns = [
                    item for item in event_patterns
                    if category_marker in str(item.get("key") or "").lower()
                ]
            medical_profile = body_zone_evidence.get("medical_profile") or {}
            profile_vulnerabilities = (
                medical_profile.get("major_vulnerabilities")
                if isinstance(medical_profile, dict)
                else []
            )
            # The normalized profile can be intentionally compact.  Merge it
            # with the calculator rows by zone instead of replacing those rows,
            # otherwise exact causes such as "Mars in Gemini, House 8" are
            # dropped before the answer contract is built.
            calculated_vulnerabilities = list(
                body_zone_evidence.get("major_vulnerabilities") or []
            )
            calculated_by_zone = {
                str(row.get("zone") or "").strip().lower(): row
                for row in calculated_vulnerabilities
                if isinstance(row, dict) and str(row.get("zone") or "").strip()
            }
            merged_vulnerabilities: List[Dict[str, Any]] = []
            seen_health_zones = set()
            for profile_row in list(profile_vulnerabilities or []):
                if not isinstance(profile_row, dict):
                    continue
                zone_key = str(profile_row.get("zone") or "").strip().lower()
                base_row = calculated_by_zone.get(zone_key) or {}
                merged_row = {**base_row, **profile_row}
                for rich_key in (
                    "primary_medical_reasons",
                    "primary_medical_factors",
                    "anatomical_members",
                    "confirmation_factors",
                    "natal_layers",
                    "sources",
                    "why",
                ):
                    if not profile_row.get(rich_key) and base_row.get(rich_key):
                        merged_row[rich_key] = base_row[rich_key]
                merged_vulnerabilities.append(merged_row)
                if zone_key:
                    seen_health_zones.add(zone_key)
            for calculated_row in calculated_vulnerabilities:
                if not isinstance(calculated_row, dict):
                    continue
                zone_key = str(calculated_row.get("zone") or "").strip().lower()
                if zone_key and zone_key not in seen_health_zones:
                    merged_vulnerabilities.append(calculated_row)
                    seen_health_zones.add(zone_key)
            normalized_evidence["health_body_area"] = {
                # Only these zones have enough independent natal confluence to
                # support a named body-system vulnerability in user-facing text.
                # Prefer the normalized medical profile because it attaches the
                # exact allowed mechanism and divisional confirmation to each
                # zone.  The composer must not infer those links itself.
                "major_vulnerabilities": list(
                    merged_vulnerabilities or calculated_vulnerabilities
                )[:4],
                # Keep the broader ranking in evidence/debug output. It must not
                # be promoted to a body-part claim by the answer model.
                "priority_zones": list(body_zone_evidence.get("priority_zones") or [])[:5],
                "event_patterns": event_patterns[:3],
                "sixth_house_chain": body_zone_evidence.get("sixth_house_chain") or {},
                "house_map": list(body_zone_evidence.get("house_map") or [])[:8],
                "claim_policy": body_zone_evidence.get("claim_policy"),
                "medical_profile": medical_profile,
                "disclaimer": body_zone_evidence.get("disclaimer"),
            }
            logger.info(
                "INSTANT_MEDICAL_PROFILE category=%s divisions=%s conditions=%s elapsed_ms=%.1f",
                category,
                sorted(health_divisions),
                len(health_conditions),
                (time.monotonic() - medical_calc_started) * 1000.0,
            )
        except Exception:
            logger.exception("Instant health body-zone evidence calculation failed")
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
        presented_event_prediction_dashas = (
            _rotate_active_dashas_context(final_event_prediction_dashas, target_chart_context)
            if is_non_self_target
            else final_event_prediction_dashas
        )
        _override_current_timing_with_authoritative_dashas(
            normalized_evidence=normalized_evidence,
            active_dashas_context=presented_event_prediction_dashas,
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
            current_dashas_levels=(
                _rotate_active_dashas_context(final_event_prediction_dashas, target_chart_context)
                if is_non_self_target
                else final_event_prediction_dashas
            ),
            current_transits_formatted=evidence_current_transits_context,
            instant_parashari=evidence_instant_parashari,
            normalized_evidence=normalized_evidence,
            period_window=period_window,
            category=category,
            career_subtype=(intent or {}).get("career_subtype"),
            question=question,
            chart_data=chart_data,
            house_lordships=house_lordships,
            named_dasha_lookup=named_dasha_lookup,
            evidence_plan=evidence_plan,
            daily_prediction_spine=daily_prediction_spine,
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
    # The complete natal factor ledger is intended for the expandable,
    # astrologer-readable evidence panel.  Keep it out of the Flash Lite
    # composer context: the fused verdict already carries the answer-bearing
    # conclusion and resending the full ledger would make Instant slower.
    user_evidence = {
        "natal_topic_factors": prompt_instant_parashari.pop("natal_topic_factors", {}),
    }
    prompt_normalized_evidence = dict(normalized_evidence)
    if category in CAREER_ALIASES or category in CAREER_PROFILES:
        career_subtype = career_profile(category, (intent or {}).get("career_subtype"))["subtype"]
        profession_evidence = (
            _instant_compact_profession_evidence(chart_data, birth_data)
            if is_static_career_profile(
                category, career_subtype, answer_mode=answer_mode
            )
            else {}
        )
        career_foundation = _compact_career_foundation(
            category,
            (intent or {}).get("career_subtype"),
            user_evidence.get("natal_topic_factors"),
            evidence_instant_parashari.get("divisional_support") or {},
            normalized_evidence.get("chart_facts") or {},
            normalized_evidence.get("karaka_evidence") or {},
            profession_evidence,
        )
        prompt_instant_parashari["career_foundation"] = career_foundation
        prompt_normalized_evidence["career_foundation"] = career_foundation
    if (
        str(category or "").lower() == "marriage"
        and str((intent or {}).get("marriage_subtype") or "").lower() == "love_vs_arranged"
    ):
        marriage_pathway_evidence = _compact_marriage_pathway_evidence(
            user_evidence.get("natal_topic_factors"),
            evidence_instant_parashari.get("divisional_support") or {},
        )
        prompt_normalized_evidence["marriage_pathway_comparison"] = marriage_pathway_evidence
    if (
        str(category or "").lower() == "marriage"
        and str((intent or {}).get("marriage_subtype") or "").lower() == "spouse_meeting"
    ):
        prompt_normalized_evidence["spouse_meeting_context"] = _compact_spouse_meeting_evidence(
            user_evidence.get("natal_topic_factors"),
            normalized_evidence.get("person_profile_axes") or [],
            evidence_instant_parashari.get("divisional_support") or {},
        )
    if (
        str(answer_mode or "").lower() == "relationship_person"
        and str(category or "").lower() in {"marriage", "spouse", "partner"}
        and _spouse_detail_scope(question, intent) not in {"appearance", "location"}
    ):
        prompt_normalized_evidence["spouse_temperament_context"] = _compact_spouse_temperament_evidence(
            chart_data,
            user_evidence.get("natal_topic_factors"),
            normalized_evidence.get("karaka_evidence") or {},
            evidence_instant_parashari.get("divisional_support") or {},
        )
    if (
        str(answer_mode or "").lower() in {"relationship_person", "topic_reading"}
        and (
            str(category or "").lower() in {"marriage", "spouse", "partner"}
            or str((intent or {}).get("marriage_subtype") or "").lower() == "spouse_details"
        )
        and _spouse_detail_scope(question, intent) == "appearance"
    ):
        prompt_normalized_evidence["spouse_appearance_context"] = _compact_spouse_appearance_evidence(
            chart_data,
            user_evidence.get("natal_topic_factors"),
            normalized_evidence.get("karaka_evidence") or {},
            evidence_instant_parashari.get("divisional_support") or {},
        )
    if (
        str(answer_mode or "").lower() in {"relationship_person", "topic_reading"}
        and (
            str(category or "").lower() in {"marriage", "spouse", "partner"}
            or str((intent or {}).get("marriage_subtype") or "").lower() == "spouse_details"
        )
        and _spouse_detail_scope(question, intent) == "location"
    ):
        prompt_normalized_evidence["spouse_location_context"] = _compact_spouse_location_evidence(
            chart_data,
            user_evidence.get("natal_topic_factors"),
            normalized_evidence.get("karaka_evidence") or {},
            evidence_instant_parashari.get("divisional_support") or {},
        )
    prompt_current_dashas_levels = evidence_current_dashas_context if is_non_self_target else current_dashas_context
    if answer_mode == "event_prediction" and authoritative_event_prediction_dashas:
        prompt_current_dashas_levels = authoritative_event_prediction_dashas
        prompt_instant_parashari = dict(prompt_instant_parashari)
        prompt_instant_parashari["active_dashas_formatted"] = authoritative_event_prediction_dashas
    static_career_profile = is_static_career_profile(
        category, (intent or {}).get("career_subtype"), answer_mode=answer_mode
    )
    if static_career_profile:
        # Static vocation questions must not inherit incidental timing context
        # from the session. Keep only the natal/divisional career foundation.
        prompt_current_dashas_levels = {}
        prompt_current_transits = {}
        prompt_transits_context = {}
        prompt_instant_parashari = {
            key: value
            for key, value in prompt_instant_parashari.items()
            if key not in {
                "active_dashas",
                "active_dashas_formatted",
                "current_dashas",
                "forward_periods",
                "horizon_segments",
                "transit_confirmation",
                "transit_windows",
            }
        }
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
                "spouse_temperament_context",
                "spouse_appearance_context",
                "spouse_location_context",
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
    if answer_mode == "factual_chart_lookup":
        prompt_current_transits = {}
        prompt_transits_context = {}
        prompt_instant_parashari = {
            k: v
            for k, v in prompt_instant_parashari.items()
            if k in {
                "source",
                "category",
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
                "chart_facts",
                "karaka_evidence",
                "natal_snapshot",
                "claim_gates",
                "avoid_drift",
            }
        }
        prompt_current_dashas_levels = {}
        current_dashas_context = {}
        recent_history = recent_history[-1:]
    if answer_mode == "remedy_action":
        marriage_remedy = str(category or "").lower() in {"marriage", "relationship", "love", "partner", "spouse"}
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
                "health_body_area",
                "option_comparison",
            }
        }
        if marriage_remedy:
            prompt_instant_parashari.pop("active_dashas_formatted", None)
            prompt_instant_parashari.pop("period_window", None)
            prompt_instant_parashari.pop("time_relation", None)
            prompt_normalized_evidence.pop("current_timing", None)
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
    if is_general_month_window and answer_mode != "factual_chart_lookup":
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

    context_result = {
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
        "_user_evidence": user_evidence,
        "normalized_evidence": prompt_normalized_evidence,
        "daily_prediction_spine": daily_prediction_spine,
        "recent_history": recent_history,
        "complexity_hint": complexity_hint,
        "named_dasha_lookup": named_dasha_lookup,
    }
    return context_result


_FOLLOW_UPS_START = "###FOLLOW_UPS_START###"
_FOLLOW_UPS_END = "###FOLLOW_UPS_END###"


def _repair_common_utf8_mojibake(value: Any) -> str:
    """Repair text whose UTF-8 bytes were decoded as a Western encoding.

    Instant responses are multilingual.  A UTF-8/Latin-1 boundary turns Hindi
    into sequences such as ``à¤``/``à¥`` and smart punctuation into ``â...``.
    Only accept a round-trip repair when those signatures become less common;
    genuine translated scripts and ordinary Western text are left untouched.
    """
    text = str(value or "")
    replacements = {
        "â\x80\x99": "’",
        "â\x80\x98": "‘",
        "â\x80\x9c": "“",
        "â\x80\x9d": "”",
        "â\x80\x93": "–",
        "â\x80\x94": "—",
        "â\x80¦": "…",
    }
    for broken, repaired in replacements.items():
        text = text.replace(broken, repaired)

    suspicious = ("à¤", "à¥", "Ã", "Â", "â€", "ðŸ")

    def corruption_score(candidate: str) -> int:
        return sum(candidate.count(marker) for marker in suspicious)

    def repair_candidate(candidate: str) -> str:
        if not candidate or corruption_score(candidate) == 0:
            return candidate
        for encoding in ("latin-1", "cp1252"):
            try:
                repaired = candidate.encode(encoding).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if (
                corruption_score(repaired) < corruption_score(candidate)
                and repaired.count("�") <= candidate.count("�")
            ):
                return repaired
        return candidate

    repaired_text = repair_candidate(text)
    if repaired_text != text:
        return repaired_text

    # Mixed content can contain both already-correct Unicode and a corrupted
    # paragraph. Repair those independently instead of re-encoding the valid
    # script around them.
    return "\n".join(repair_candidate(line) for line in text.split("\n"))


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
                "natal_promise_status": seg.get("natal_promise_status"),
                "activation_strength": seg.get("activation_strength"),
                "transit_trigger_score": seg.get("transit_trigger_score"),
                "activated_focus_houses": seg.get("activated_focus_houses"),
                "carrier_planets": seg.get("carrier_planets"),
                "peak_activation_windows": list(seg.get("peak_activation_windows") or [])[:3],
                "predicted_result_areas": seg.get("predicted_result_areas"),
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
        "activation_timeline": window_segments.get("activation_timeline"),
        "segments": selected[:limit],
    }


_PERIOD_TOPIC_HOUSE_MANIFESTATIONS: Dict[str, Dict[int, str]] = {
    "career": {
        2: "income, compensation, and resource decisions",
        3: "skill-building, communication, and self-driven initiatives",
        6: "workload, deadlines, service, and competition",
        7: "clients, contracts, and professional partnerships",
        8: "role restructuring, shared resources, and difficult transitions",
        9: "mentors, advanced learning, and long-range opportunities",
        10: "role, status, recognition, and visible responsibility",
        11: "gains, networks, support, and goal fulfilment",
        12: "expenses, remote or foreign work, and work behind the scenes",
    },
    "business": {
        2: "cash flow, pricing, and business resources",
        3: "sales effort, communication, and new initiatives",
        6: "operations, staffing pressure, and competition",
        7: "customers, contracts, and business partnerships",
        8: "funding, liabilities, and structural change",
        9: "advisers, expansion, and long-range opportunities",
        10: "market position, authority, and execution",
        11: "revenue gains, networks, and scale",
        12: "overheads, foreign links, and behind-the-scenes work",
    },
    "relationship": {
        2: "family expectations, speech, and shared values",
        4: "home life and emotional security",
        5: "affection, romance, and emotional expression",
        6: "daily friction, responsibilities, and conflict resolution",
        7: "commitment, partnership, and mutual agreements",
        8: "trust, intimacy, and shared obligations",
        11: "shared goals, support, and social connections",
        12: "distance, privacy, withdrawal, or sacrifice",
    },
    "wealth": {
        2: "income, savings, and family resources",
        5: "investment judgment and calculated risk",
        6: "debt, obligations, and expense control",
        8: "shared money, liabilities, and sudden financial change",
        9: "long-range financial support and sound guidance",
        10: "earnings through work and professional standing",
        11: "gains, collections, and financial goals",
        12: "expenses, leakage, and overseas transactions",
    },
    "health": {
        1: "vitality and physical resilience",
        6: "health routines, treatment, and manageable strain",
        8: "changes in stamina that merit closer observation",
        12: "rest, sleep, and energy conservation",
    },
}


def _period_topic_manifestations(category: str, houses: List[Any], areas: Any) -> List[str]:
    """Translate activated houses into bounded, user-facing possibilities.

    These are manifestation candidates, not promises.  The composer is told to
    phrase them according to the fused verdict and never infer positivity from
    activation strength alone.
    """
    cat = _normalize_event_category(category)
    if cat in {"job", "promotion", "job_change", "higher_studies", "relocation", "visa", "travel"}:
        cat = "career"
    elif cat in {"marriage", "love", "partner", "spouse"}:
        cat = "relationship"
    elif cat in {"money", "finance", "trading", "property"}:
        cat = "wealth"
    mapping = _PERIOD_TOPIC_HOUSE_MANIFESTATIONS.get(cat, {})
    out: List[str] = []
    normalized_houses = [house for house in (_norm_house(raw) for raw in (houses or [])) if house is not None]
    # A topic forecast must lead with the topic's primary delivery house.  Raw
    # house order is numeric, which previously made house 2 dominate a career
    # answer even when houses 10 and 11 were active in the same phase.
    normalized_houses = sorted(
        dict.fromkeys(normalized_houses),
        key=lambda house: (-_house_priority_weight(cat, house), house),
    )
    for house in normalized_houses:
        label = mapping.get(house) if house is not None else None
        if label and label not in out:
            out.append(label)
    if not out and isinstance(areas, list):
        for row in areas:
            label = str((row or {}).get("theme") or "").strip() if isinstance(row, dict) else ""
            if label and label not in out:
                out.append(label)
    return out[:4]


def _build_period_topic_forecast(
    normalized: Dict[str, Any],
    category: str,
    time_scope: Optional[Dict[str, Any]] = None,
    health_rules: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create the compact, chronological forecast the composer must narrate.

    Window calculations are ranked for evidence selection.  A period forecast,
    however, must be chronological or the model can mistake the top-ranked peak
    for the whole year.  This adapter retains the calculated phases while
    removing calculator diagnostics.
    """
    if not isinstance(normalized, dict):
        return {}
    rules = normalized.get("window_rules") if isinstance(normalized.get("window_rules"), dict) else {}
    source = normalized.get("window_dasha_segments")
    if not isinstance(source, dict):
        return {}
    raw_segments = [row for row in (source.get("segments") or []) if isinstance(row, dict)]
    if not raw_segments:
        return {}
    period = ((normalized.get("current_timing") or {}).get("period_window") or {})
    period = period if isinstance(period, dict) else {}
    time_scope = time_scope if isinstance(time_scope, dict) else {}
    window_start = str(time_scope.get("as_of") or period.get("start") or "")
    window_end = str(time_scope.get("horizon_end") or period.get("end") or "")
    if window_start:
        period["start"] = window_start
    if window_end:
        period["end"] = window_end

    health_rules = health_rules if isinstance(health_rules, dict) else {}
    is_health = _normalize_event_category(category) in {
        "health", "mental_wellbeing", "surgery", "accident", "recovery",
    }

    def health_phase_detail(
        houses: List[int],
        peaks: List[Dict[str, Any]],
        permission: str,
    ) -> Dict[str, Any]:
        """Join dated activation evidence to already-calculated natal risks.

        The language model must not infer a disease from a dasha house.  This
        adapter therefore exposes only body zones and condition
        susceptibilities that the medical calculator has already permitted.
        """
        if not is_health or not health_rules:
            return {}
        active = {int(h) for h in houses if str(h).isdigit()}
        health_active = sorted(active & {1, 6, 8, 12})
        has_dasha_permission = permission == "supported_by_active_dasha_carriers"
        has_transit_confirmation = bool(peaks)
        if has_dasha_permission and has_transit_confirmation and health_active:
            level = "strongest_watch_period"
        elif has_dasha_permission and health_active:
            level = "elevated_watch_period"
        else:
            level = "background_only"

        zones = []
        if level != "background_only":
            for row in list(health_rules.get("allowed_zone_evidence") or [])[:4]:
                if not isinstance(row, dict) or not row.get("zone"):
                    continue
                zones.append({
                    "zone": row.get("zone"),
                    "confidence": row.get("confidence"),
                    "possible_expression": list(row.get("mechanisms") or [])[:3],
                    "natal_basis": list(row.get("why") or row.get("sources") or [])[:2],
                    "calculated_activation_basis": list(row.get("activation_sources") or [])[:3],
                })
        conditions = []
        if level != "background_only":
            for row in list(health_rules.get("condition_susceptibilities") or [])[:3]:
                if not isinstance(row, dict) or not row.get("title"):
                    continue
                conditions.append({
                    "title": row.get("title"),
                    "risk_level": row.get("risk_level"),
                    "interpretation": row.get("interpretation"),
                })
        return {
            "health_level": level,
            "activated_health_houses": health_active,
            "dasha_permission": has_dasha_permission,
            "transit_confirmed": has_transit_confirmation,
            "possible_body_regions": zones,
            "possible_condition_patterns": conditions,
            "protective_factors": list(health_rules.get("protective_factors") or [])[:3],
            "claim_rule": (
                "Describe these only as heightened astrological susceptibility during this period, "
                "never as a diagnosis or certain illness. If this is background_only, do not claim a "
                "health problem is likely in the period."
            ),
        }

    phases: List[Dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for row in sorted(raw_segments, key=lambda item: (str(item.get("start") or ""), str(item.get("end") or ""))):
        row_start = str(row.get("start") or "")
        row_end = str(row.get("end") or "")
        if window_start and row_end and row_end < window_start:
            continue
        if window_end and row_start and row_start > window_end:
            continue
        phase_start = max(row_start, window_start) if row_start and window_start else row_start or window_start
        phase_end = min(row_end, window_end) if row_end and window_end else row_end or window_end
        key = (
            phase_start, phase_end, row.get("mahadasha"),
            row.get("antardasha"), row.get("pratyantardasha"),
        )
        if key in seen:
            continue
        seen.add(key)
        houses = list(row.get("activated_focus_houses") or [])
        peaks = _compact_composer_windows(list(row.get("peak_activation_windows") or []), limit=3)
        bounded_peaks: List[Dict[str, Any]] = []
        for peak in peaks:
            peak_start = str(peak.get("start") or "")
            peak_end = str(peak.get("end") or "")
            if window_start and peak_end and peak_end < window_start:
                continue
            if window_end and peak_start and peak_start > window_end:
                continue
            bounded = dict(peak)
            if window_start and peak_start:
                bounded["start"] = max(peak_start, window_start)
            if window_end and peak_end:
                bounded["end"] = min(peak_end, window_end)
            bounded_peaks.append(bounded)
        peaks = bounded_peaks
        permission = str(row.get("natal_promise_status") or "")
        phase_state = (
            "transit_reinforced_peak"
            if peaks
            else "dasha_activated"
            if permission == "supported_by_active_dasha_carriers"
            else "background_only"
        )
        phase = {
                "start": phase_start,
                "end": phase_end,
                "dasha_chain": " - ".join(
                    str(row.get(key_name) or "").strip()
                    for key_name in ("mahadasha", "antardasha", "pratyantardasha")
                    if str(row.get(key_name) or "").strip()
                ),
                "phase_state": phase_state,
                "relevance_score": row.get("relevance_score"),
                "activation_strength": row.get("activation_strength"),
                "transit_trigger_score": row.get("transit_trigger_score"),
                "activated_focus_houses": houses,
                "manifestation_candidates": _period_topic_manifestations(category, houses, row.get("predicted_result_areas")),
                "peak_windows": peaks,
            }
        if _normalize_event_category(category) in CAREER_ALIASES or _normalize_event_category(category) in CAREER_PROFILES:
            phase["career_manifestations"] = classify_career_manifestations(houses)
        health_detail = health_phase_detail(houses, peaks, permission)
        if health_detail:
            phase["health_forecast"] = health_detail
        phases.append(phase)
        if len(phases) >= 10:
            break

    if not phases:
        return {}
    strongest = max(phases, key=lambda item: float(item.get("relevance_score") or 0))
    result = {
        "forecast_shape": "period_topic_forecast",
        "category": _normalize_event_category(category),
        "period": period,
        "year_like": bool(rules.get("year_like")),
        "phase_count": len(phases),
        "chronological_phases": phases,
        "strongest_phase": {
            key: strongest.get(key)
            for key in ("start", "end", "phase_state", "manifestation_candidates", "career_manifestations", "peak_windows")
        },
        "narration_rule": (
            "Cover the full requested period in chronological phases. A peak window is a peak within its "
            "phase, never a substitute for the rest of the year. Activation indicates where results concentrate; "
            "use the fused verdict/support/risk evidence to decide whether delivery is constructive, demanding, or mixed."
        ),
    }
    if is_health and health_rules:
        result["health_narration_contract"] = (
            "Answer the paid question directly: identify the dated strongest and elevated watch periods, "
            "state which supplied body regions or condition patterns could be more susceptible in each, "
            "and explain the dasha trigger plus dated transit reinforcement. Cover quieter phases briefly. "
            "Do not replace this with routine, consistency, vitality-management, or general wellness advice."
        )
    return result


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
            "natal_promise_status": row.get("natal_promise_status"),
            "activation_strength": row.get("activation_strength"),
            "transit_trigger_score": row.get("transit_trigger_score"),
            "carrier_planets": row.get("carrier_planets"),
            "peak_activation_windows": (row.get("peak_activation_windows") or [])[:3],
            "predicted_result_areas": row.get("predicted_result_areas"),
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


def _compact_composer_windows(rows: Any, *, limit: int = 5) -> List[Dict[str, Any]]:
    """Keep only answer-bearing fields from a ranked/timing window.

    Calculator payloads intentionally carry diagnostics for audit and testing.
    The language model does not need those diagnostics after fusion has produced
    a verdict, and sending them again both slows Flash Lite and invites it to
    reinterpret evidence that has already been adjudicated.
    """
    if not isinstance(rows, list):
        return []
    allowed = {
        "start",
        "end",
        "label",
        "option",
        "event_profile",
        "chain",
        "mahadasha",
        "antardasha",
        "pratyantardasha",
        "phase_start",
        "phase_end",
        "phase_dasha_chain",
        "phase_granularity",
        "strongest_pd_window",
        "probable_peak_windows",
        "planet",
        "dasha_levels",
        "strength",
        "confidence",
        "score",
        "trigger_score",
        "trigger_kinds",
        "activated_focus_houses",
        "allowed_house_themes",
        "predicted_result_areas",
        "career_manifestations",
        "why",
    }
    return [
        {
            key: _limit_composer_value(value)
            for key, value in row.items()
            if key in allowed and value not in (None, "", [], {})
        }
        for row in rows[:limit]
        if isinstance(row, dict)
    ]


def _bound_composer_windows(
    rows: Any,
    *,
    start: Any = None,
    end: Any = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Remove historical/out-of-scope windows before the writer sees them."""
    # Compact every candidate before applying the output limit; otherwise five
    # historical rows at the front could hide a valid sixth future window.
    compact = _compact_composer_windows(
        rows,
        limit=len(rows) if isinstance(rows, list) else limit,
    )
    scope_start = str(start or "").strip()[:10]
    scope_end = str(end or "").strip()[:10]
    bounded: List[Dict[str, Any]] = []
    for row in compact:
        row_start = str(row.get("start") or "").strip()[:10]
        row_end = str(row.get("end") or row_start).strip()[:10]
        if scope_start and row_end and row_end < scope_start:
            continue
        if scope_end and row_start and row_start > scope_end:
            continue
        item = dict(row)
        if scope_start and row_start and row_start < scope_start:
            item["start"] = scope_start
        if scope_end and row_end and row_end > scope_end:
            item["end"] = scope_end
        bounded.append(item)
        if len(bounded) >= limit:
            break
    return bounded


def _limit_composer_value(
    value: Any,
    *,
    depth: int = 0,
    max_depth: int = 5,
    list_limit: int = 7,
    string_limit: int = 280,
) -> Any:
    """Bound model-facing evidence without changing the audit ledger.

    Calculators return rich nested diagnostics for reproducibility.  After the
    adjudicator has fused those diagnostics, the composer only needs the
    answer-bearing values.  This limiter is intentionally language agnostic:
    it never interprets the user's words or writes an answer.
    """
    if value in (None, "", [], {}):
        return None
    if isinstance(value, str):
        clean = value.strip()
        if len(clean) <= string_limit:
            return clean
        return f"{clean[: max(0, string_limit - 1)].rstrip()}…"
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        if depth >= max_depth:
            scalars = [item for item in value if isinstance(item, (str, int, float, bool))]
            return [
                _limit_composer_value(
                    item,
                    depth=depth + 1,
                    max_depth=max_depth,
                    list_limit=list_limit,
                    string_limit=string_limit,
                )
                for item in scalars[:list_limit]
            ]
        return [
            compact
            for item in list(value)[:list_limit]
            if (
                compact := _limit_composer_value(
                    item,
                    depth=depth + 1,
                    max_depth=max_depth,
                    list_limit=list_limit,
                    string_limit=string_limit,
                )
            )
            not in (None, "", [], {})
        ]
    if isinstance(value, dict):
        compact_dict: Dict[str, Any] = {}
        for key, item in value.items():
            if depth >= max_depth and isinstance(item, (dict, list, tuple)):
                continue
            compact = _limit_composer_value(
                item,
                depth=depth + 1,
                max_depth=max_depth,
                list_limit=list_limit,
                string_limit=string_limit,
            )
            if compact not in (None, "", [], {}):
                compact_dict[str(key)] = compact
        return compact_dict
    return _limit_composer_value(
        str(value),
        depth=depth,
        max_depth=max_depth,
        list_limit=list_limit,
        string_limit=string_limit,
    )


def _fit_composer_brief(context: Dict[str, Any], *, target_chars: int = 9500) -> Dict[str, Any]:
    """Fit the composer JSON to a latency-safe envelope in two semantic passes."""
    source_evidence = context.get("evidence") if isinstance(context.get("evidence"), dict) else {}
    source_career = (
        source_evidence.get("career_foundation")
        if isinstance(source_evidence.get("career_foundation"), dict)
        else {}
    )
    source_vocation = (
        source_career.get("vocation_synthesis")
        if isinstance(source_career.get("vocation_synthesis"), dict)
        else {}
    )
    source_career_decision = (
        source_evidence.get("career_decision")
        if isinstance(source_evidence.get("career_decision"), dict)
        else {}
    )
    source_option_comparison = (
        source_evidence.get("option_comparison")
        if isinstance(source_evidence.get("option_comparison"), dict)
        else {}
    )
    source_query_plan = context.get("query_plan") if isinstance(context.get("query_plan"), dict) else {}
    source_verdict = context.get("verdict") if isinstance(context.get("verdict"), dict) else {}
    source_contract = context.get("answer_contract") if isinstance(context.get("answer_contract"), dict) else {}
    source_event_rules = (
        source_contract.get("event_rules")
        if isinstance(source_contract.get("event_rules"), dict)
        else {}
    )
    source_retrospective_windows = (
        _compact_composer_windows(source_verdict.get("ranked_windows"), limit=3)
        if bool((source_query_plan.get("time_scope") or {}).get("retrospective"))
        else []
    )

    def restore_vocation(payload: Dict[str, Any]) -> None:
        """Keep answer-bearing career combinations through depth limiting."""
        if not source_vocation:
            return
        payload_evidence = payload.setdefault("evidence", {})
        if not isinstance(payload_evidence, dict):
            return
        payload_career = payload_evidence.setdefault("career_foundation", {})
        if not isinstance(payload_career, dict):
            return
        payload_career["vocation_synthesis"] = _limit_composer_value(
            source_vocation,
            max_depth=7,
            list_limit=7,
            string_limit=180,
        )

    def restore_career_decision(payload: Dict[str, Any]) -> None:
        """Keep the calculated cause of every stay/change verdict.

        The generic depth limiter used to retain the verdict matrix while
        dropping its nested dasha carriers and transit confirmations.  That
        made both the writer and the readable audit UI see only a bare list of
        active houses.  These rows are answer-bearing evidence, not optional
        diagnostics, so preserve them through both compaction passes.
        """
        if not source_career_decision:
            return
        payload_evidence = payload.setdefault("evidence", {})
        if not isinstance(payload_evidence, dict):
            return
        payload_evidence["career_decision"] = _limit_composer_value(
            source_career_decision,
            max_depth=9,
            list_limit=12,
            string_limit=220,
        )

    def restore_option_comparison(payload: Dict[str, Any]) -> None:
        """Keep each comparison option attached to its own calculated window."""
        if not source_option_comparison:
            return
        rows: List[Dict[str, Any]] = []
        for option in list(source_option_comparison.get("options") or [])[:3]:
            if not isinstance(option, dict):
                continue
            window = option.get("best_window") if isinstance(option.get("best_window"), dict) else {}
            rows.append({
                "label": option.get("label"),
                "event_profile": option.get("event_profile"),
                "peak_score": option.get("peak_score"),
                "focus_houses": option.get("target_relative_focus_houses"),
                "best_window": {
                    key: window.get(key)
                    for key in (
                        "start", "end", "mahadasha", "antardasha", "pratyantardasha",
                        "relevance_score", "activated_focus_houses", "predicted_result_areas", "why",
                    )
                    if window.get(key) not in (None, "", [], {})
                },
            })
        payload_evidence = payload.setdefault("evidence", {})
        if isinstance(payload_evidence, dict):
            payload_evidence["option_comparison"] = {
                "as_of": source_option_comparison.get("as_of"),
                "horizon_end": source_option_comparison.get("horizon_end"),
                "options": rows,
                "comparison": source_option_comparison.get("comparison"),
                "writer_rule": (
                    "Never attach one option's best_window, dasha chain, score, or why to another option."
                ),
            }

    def restore_retrospective_windows(payload: Dict[str, Any]) -> None:
        """PD boundaries and probable peaks are answer-bearing, not diagnostics."""
        if not source_retrospective_windows:
            return
        payload_verdict = payload.setdefault("verdict", {})
        if isinstance(payload_verdict, dict):
            payload_verdict["ranked_windows"] = source_retrospective_windows
        payload_contract = payload.setdefault("answer_contract", {})
        if not isinstance(payload_contract, dict):
            return
        payload_rules = payload_contract.setdefault("event_rules", {})
        if not isinstance(payload_rules, dict):
            return
        payload_rules["allowed_timing_windows"] = _compact_composer_windows(
            source_event_rules.get("allowed_timing_windows"), limit=3
        )
        payload_rules["required_material_windows"] = _compact_composer_windows(
            source_event_rules.get("required_material_windows"), limit=3
        )

    compact = _limit_composer_value(context)
    compact = compact if isinstance(compact, dict) else {}
    restore_vocation(compact)
    restore_career_decision(compact)
    restore_option_comparison(compact)
    restore_retrospective_windows(compact)
    if _json_size(compact) <= target_chars:
        return compact

    tighter = _limit_composer_value(
        context,
        max_depth=4,
        list_limit=6,
        string_limit=180,
    )
    tighter = tighter if isinstance(tighter, dict) else {}
    restore_vocation(tighter)
    restore_career_decision(tighter)
    restore_option_comparison(tighter)
    restore_retrospective_windows(tighter)

    # The shallow emergency pass above intentionally drops nested collections.
    # Constitutional-health cause facts live one level deeper than each zone
    # row (``anatomy_basis`` / ``why``), so losing them leaves the writer with
    # region names but no permitted astrological explanation.  Restore the
    # authoritative compact health contract after generic size reduction.  It
    # is small, answer-critical, and must take precedence over optional
    # diagnostics when fitting the latency envelope.
    source_health = (
        source_evidence.get("health_rules")
        if isinstance(source_evidence.get("health_rules"), dict)
        else {}
    )
    if source_health and not source_health.get("is_time_bound_question"):
        tighter_evidence = tighter.setdefault("evidence", {})
        if isinstance(tighter_evidence, dict):
            tighter_evidence["health_rules"] = _limit_composer_value(
                source_health,
                max_depth=6,
                list_limit=6,
                string_limit=180,
            )
        source_contract = (
            context.get("answer_contract")
            if isinstance(context.get("answer_contract"), dict)
            else {}
        )
        if isinstance(source_contract.get("health_rules"), dict):
            tighter_contract = tighter.setdefault("answer_contract", {})
            if isinstance(tighter_contract, dict):
                tighter_contract["health_rules"] = _limit_composer_value(
                    source_contract["health_rules"],
                    max_depth=6,
                    list_limit=6,
                    string_limit=180,
                )
    # The emergency depth limiter above can keep ``career_foundation`` while
    # silently dropping the dictionaries inside
    # ``vocation_synthesis.combination_signatures``.  Those conjunctions are
    # the answer-bearing career evidence (for example Mars-Saturn-Rahu), not
    # optional diagnostics. Restore that bounded synthesis after the generic
    # pass so the writer receives the same individualized result calculated by
    # the career engine.
    if _json_size(tighter) <= target_chars:
        return tighter

    # These are explanatory duplicates of facts already represented by the
    # verdict, promise, timing, and ranked windows. Keep them in the audit
    # packet, but remove them from an exceptionally large writing brief.
    evidence = tighter.get("evidence") if isinstance(tighter.get("evidence"), dict) else {}
    for key in ("divisional_specifics", "active_areas", "topic_confirmation"):
        evidence.pop(key, None)
        if _json_size(tighter) <= target_chars:
            break
    if _json_size(tighter) > target_chars:
        contract = (
            tighter.get("answer_contract")
            if isinstance(tighter.get("answer_contract"), dict)
            else {}
        )
        for key in ("current_cause_rules", "evidence_limitations"):
            contract.pop(key, None)
            if _json_size(tighter) <= target_chars:
                break
        query_plan = tighter.get("query_plan") if isinstance(tighter.get("query_plan"), dict) else {}
        if (
            _json_size(tighter) > target_chars
            and query_plan.get("forecast_shape") == "period_topic_forecast"
        ):
            # The chronological forecast and fused verdict already contain the
            # allowed windows. The event rule object is an adjudicator-facing
            # duplicate for this answer shape.
            contract.pop("event_rules", None)
        if _json_size(tighter) > target_chars:
            contract.pop("activation_prediction_rules", None)
    return tighter


def _compact_answer_spec_for_composer(answer_spec: Any) -> Dict[str, Any]:
    if not isinstance(answer_spec, dict):
        return {}
    activation = answer_spec.get("activation_prediction_rules")
    activation = activation if isinstance(activation, dict) else {}
    event_rules = answer_spec.get("event_rules")
    event_rules = event_rules if isinstance(event_rules, dict) else {}
    compact_event_rules = {
        "hard_horizon_end": event_rules.get("hard_horizon_end"),
        "window_comparison": event_rules.get("window_comparison"),
        "window_score_delta": event_rules.get("window_score_delta"),
        "window_answer_rule": event_rules.get("window_answer_rule"),
        "allowed_timing_windows": _compact_composer_windows(event_rules.get("allowed_timing_windows")),
        "required_material_windows": _compact_composer_windows(event_rules.get("required_material_windows")),
        "career_manifestations": event_rules.get("career_manifestations"),
        "derived_subject_rule": event_rules.get("derived_subject_rule"),
    }
    health_rules = answer_spec.get("health_rules")
    health_rules = health_rules if isinstance(health_rules, dict) else {}
    compact_health_rules: Dict[str, Any] = {}
    if health_rules:
        time_bound_health = bool(health_rules.get("is_time_bound_question"))
        zone_rows: List[Dict[str, Any]] = []
        for row in list(health_rules.get("allowed_zone_evidence") or [])[:4]:
            if not isinstance(row, dict):
                continue
            compact_row = {
                key: row.get(key)
                for key in (
                    "zone", "anatomical_members", "confidence", "confluence_count", "sources", "why",
                    "mechanisms", "divisional_repetition", "primary_medical_factors",
                    "anatomy_basis", "confirmation_factors",
                )
                if row.get(key) not in (None, "", [], {})
            }
            # Activation sources belong only to an explicitly time-bound
            # health forecast. They must never leak into a constitutional
            # vulnerability answer merely because the calculator recorded them.
            if time_bound_health and row.get("activation_sources"):
                compact_row["activation_sources"] = row.get("activation_sources")
            zone_rows.append(compact_row)
        compact_health_rules = {
            key: health_rules.get(key)
            for key in (
                "health_question_type", "is_time_bound_question",
                "allowed_zone_names", "required_zone_count", "require_all_allowed_zones",
                "allowed_mechanisms",
                "answer_order", "constitutional_question_rule",
                "forbidden_topics",
                "category_safety", "claim_allow_list", "forbidden_claims",
                "requested_horizon", "period_forecast_rule", "timing_framing",
                "dasha_framing", "protective_factors", "condition_susceptibilities",
            )
            if health_rules.get(key) not in (None, "", [], {})
        }
        compact_health_rules["allowed_zone_evidence"] = zone_rows

    graph_policy = answer_spec.get("knowledge_graph_policy")
    graph_policy = graph_policy if isinstance(graph_policy, dict) else {}
    compact_graph_policy = {
        key: graph_policy.get(key)
        for key in (
            "live", "enforcement", "domain", "ontology_version", "runtime_key",
            "ontology_resource", "question_type", "expected_answer_mode", "mode_match",
            "evidence_status", "required_factors", "observed_factors",
            "missing_required_factors", "default_exclusions",
            "unexpected_default_exclusions", "required_capabilities",
            "decision_rules", "guardrails", "answer_contract", "evidence_policy",
            "required_output_sections", "instruction",
            "claim_permission", "timing_missing_factors",
            "marriage_pathway_rules",
            "spouse_meeting_rules",
            "spouse_temperament_rules", "missing_temperament_layers",
            "spouse_appearance_rules", "missing_appearance_layers",
            "spouse_location_rules", "missing_location_layers",
            "marriage_remedy_rules",
        )
        if graph_policy.get(key) not in (None, "", [], {})
    }

    compact = {
        "max_words": answer_spec.get("max_words"),
        "composer_word_target": answer_spec.get("composer_word_target"),
        "activation_prediction_rules": {
            "natal_promise": activation.get("natal_promise"),
            "allowed_peak_windows": _compact_composer_windows(activation.get("allowed_peak_windows")),
        },
        "target_framing": answer_spec.get("target_framing"),
        "required_derived_opening": answer_spec.get("required_derived_opening"),
        "evidence_limitations": answer_spec.get("evidence_limitations"),
        "health_rules": compact_health_rules,
        "knowledge_graph_policy": compact_graph_policy,
        "current_cause_rules": answer_spec.get("current_cause_rules"),
        "comparison_rules": answer_spec.get("comparison_rules"),
        "daily_rules": answer_spec.get("daily_rules"),
        "chart_fact_rules": answer_spec.get("chart_fact_rules"),
        "capacity_rules": answer_spec.get("capacity_rules"),
        "career_rules": answer_spec.get("career_rules"),
        "marriage_pathway_rules": answer_spec.get("marriage_pathway_rules"),
        "spouse_meeting_rules": answer_spec.get("spouse_meeting_rules"),
        "spouse_temperament_rules": answer_spec.get("spouse_temperament_rules"),
        "spouse_appearance_rules": answer_spec.get("spouse_appearance_rules"),
        "spouse_location_rules": answer_spec.get("spouse_location_rules"),
        "marriage_remedy_rules": answer_spec.get("marriage_remedy_rules"),
        "event_rules": compact_event_rules,
        "forbidden": answer_spec.get("forbidden"),
        "answer_order": answer_spec.get("answer_order"),
        "presentation_contract": answer_spec.get("presentation_contract"),
    }
    return {key: value for key, value in compact.items() if value not in (None, "", [], {})}


def _compact_daily_prediction_for_composer(value: Any) -> Dict[str, Any]:
    """Keep the decisive daily evidence while excluding the full chart workspace."""
    if not isinstance(value, dict) or not value:
        return {}
    moon = value.get("moon") if isinstance(value.get("moon"), dict) else {}
    schools = value.get("school_judgments") if isinstance(value.get("school_judgments"), dict) else {}
    judgment = value.get("daily_judgment") if isinstance(value.get("daily_judgment"), dict) else {}
    compact_dashas = []
    for row in list(value.get("dasha_stack") or [])[:5]:
        if not isinstance(row, dict):
            continue
        trigger = row.get("trigger") if isinstance(row.get("trigger"), dict) else {}
        compact_dashas.append({
            "level": row.get("level"),
            "planet": row.get("planet"),
            "start": row.get("start"),
            "end": row.get("end"),
            "natal_house": (row.get("natal") or {}).get("house") if isinstance(row.get("natal"), dict) else None,
            "natal_lordships": (row.get("natal") or {}).get("lordships") if isinstance(row.get("natal"), dict) else None,
            "transit_house": (row.get("transit") or {}).get("house") if isinstance(row.get("transit"), dict) else None,
            "trigger_strength": trigger.get("strength"),
            "trigger_score": trigger.get("weighted_score") or trigger.get("score"),
            "trigger_flags": list(trigger.get("flags") or [])[:5],
        })
    kp = schools.get("kp") if isinstance(schools.get("kp"), dict) else {}
    return {
        "target_date": value.get("target_date"),
        "panchanga": value.get("panchanga"),
        "moon": {
            "transit": moon.get("transit"),
            "tara_bala": moon.get("tara_bala"),
        },
        "five_level_dasha": compact_dashas,
        "daily_judgment": judgment,
        "kp": kp,
        "school_verdicts": {
            name: row.get("verdict")
            for name, row in schools.items()
            if isinstance(row, dict) and row.get("verdict")
        },
        "merge_rule": schools.get("merge_rule"),
        "interpretation_rules": list(value.get("interpretation_rules") or [])[:6],
    }


def _build_instant_answer_blueprint(
    *,
    query_plan: Dict[str, Any],
    verdict: Dict[str, Any],
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Expose semantic answer slots without writing the answer in code.

    This is deliberately not a template or a language generator. The LLM still
    owns natural-language understanding and expression in every supported
    language. The blueprint only prevents the single composer call from losing
    the adjudicated verdict, progression, peak, or material caution inside a
    compact evidence object.
    """
    health_rules = (
        evidence.get("health_rules")
        if isinstance(evidence.get("health_rules"), dict)
        else {}
    )
    career_decision = (
        evidence.get("career_decision")
        if isinstance(evidence.get("career_decision"), dict)
        else {}
    )
    if query_plan.get("forecast_shape") == "career_decision":
        return {
            "purpose": "semantic slots for a calculated stay-or-change decision; not a vocation-fit profile",
            "slots": [
                {
                    "slot": "direct safe verdict",
                    "source": "evidence.career_decision.permission and verdict.direction",
                },
                {
                    "slot": "continuity in the present job",
                    "source": "evidence.career_decision.windows[].decision_matrix.continuity_support",
                },
                {
                    "slot": "change and separation support",
                    "source": "evidence.career_decision.windows[].decision_matrix.change_momentum and separation_support",
                },
                {
                    "slot": "next-role and income landing support",
                    "source": "evidence.career_decision.windows[].decision_matrix.landing_support",
                },
                {
                    "slot": "safest practical action",
                    "source": "evidence.career_decision.guidance",
                },
                {
                    "slot": "one natural follow-up about a secured offer, concrete workplace problem, or intended transition window",
                    "source": "user_goal",
                },
            ],
            "hard_gate": {
                "affirmative_exit_allowed": bool(career_decision.get("affirmative_exit_allowed")),
                "supported_transition_windows": career_decision.get("supported_transition_windows") or [],
                "rule": (
                    "Never describe landing support as missing inside a planned_transition_supported window. "
                    "Recommend resignation only when affirmative_exit_allowed is true; otherwise advise staying "
                    "while preparing or ask for the missing offer/window. A supported window has all four "
                    "calculated gates, but remains astrological support rather than a real-world guarantee. "
                    "If supported_transition_windows is empty, explicitly say that no supported change window "
                    "was established in the calculated horizon and do not present any other date as favorable."
                ),
            },
            "forbidden_content": [
                "advising resignation from career fit, dissatisfaction, House 8 pressure, or House 12 alone",
                "turning a better-fit vocation profile into permission to leave the current job",
                "an affirmative leave recommendation when affirmative_exit_allowed is false",
                "inventing a transition date or supported window not present in evidence.career_decision.windows",
                "calling a non-supported window a job-change window",
                "saying next-role landing support is absent for a planned_transition_supported window",
            ],
            "user_goal": query_plan.get("user_goal"),
        }
    if (
        query_plan.get("answer_mode") in {"topic_reading", "potential_capacity"}
        and evidence.get("career_foundation")
    ):
        return {
            "purpose": "semantic slots for a timeless career-profile reading; not a forecast and not prewritten prose",
            "slots": [
                {
                    "slot": "direct overall career pattern and working style",
                    "source": "evidence.career_foundation.D1 and evidence.career_foundation.D10",
                },
                {
                    "slot": "professional strengths and environments where they express well",
                    "source": "evidence.career_foundation.D10 and evidence.career_foundation.career_fit",
                },
                {
                    "slot": "vocation signature",
                    "source": "evidence.career_foundation.amatyakaraka and evidence.career_foundation.KARAKAMSHA",
                },
                {
                    "slot": "main natal pressure or condition",
                    "source": "evidence.natal_promise, evidence.risk_specifics, and evidence.special_natal_factors",
                },
                {
                    "slot": "one practical career implication",
                    "source": "the natal and vocational facts above",
                },
                {
                    "slot": "one natural follow-up about role, industry, work style, or present concern",
                    "source": "user_goal",
                },
            ],
            "forbidden_content": [
                "dates, years, windows, peaks, or future phases",
                "current dasha, current transit, or currently active houses",
                "promotion, joining, compensation, or event-timing claims",
            ],
            "user_goal": query_plan.get("user_goal"),
        }
    if health_rules and not health_rules.get("is_time_bound_question"):
        return {
            "purpose": "semantic slots for a constitutional health-susceptibility reading; not a current-period forecast",
            "slots": [
                {
                    "slot": "ranked susceptibility zones in the exact supplied order",
                    "source": "evidence.health_rules.allowed_zone_evidence",
                },
                {
                    "slot": "one zone-specific natal reason for each zone without borrowing mechanisms",
                    "source": "each matching evidence.health_rules.allowed_zone_evidence row",
                },
                {
                    "slot": "ordinary prevention guidance without diagnosis",
                    "source": "the allowed zones only",
                },
                {"slot": "one natural symptom-or-prevention follow-up", "source": "user_goal"},
            ],
            "forbidden_content": [
                "current dasha, current transit, or currently active houses",
                "body systems, symptoms, severity, or diagnoses absent from the zone evidence",
                "combining mechanisms across zones",
                "acute-versus-chronic comparison not explicitly supplied for that same zone",
            ],
            "user_goal": query_plan.get("user_goal"),
        }
    if query_plan.get("forecast_shape") == "daily_forecast":
        return {
            "purpose": "semantic slots for one exact-day forecast; not prewritten prose",
            "slots": [
                {"slot": "direct overall outlook for the target day", "source": "verdict"},
                {"slot": "one or two likely real-life manifestations", "source": "evidence.daily_prediction.daily_judgment and evidence.daily_prediction.kp"},
                {"slot": "best use or opportunity", "source": "supportive daily factors"},
                {"slot": "main caution", "source": "caution daily factors"},
                {"slot": "one practical action", "source": "the ranked daily evidence"},
                {"slot": "one compact astrological reason", "source": "KP plus Moon/Tara plus Sookshma/Prana"},
                {"slot": "one natural follow-up question", "source": "the user's real concern"},
            ],
            "user_goal": query_plan.get("user_goal"),
        }
    if query_plan.get("forecast_shape") == "chart_fact_reading" or evidence.get("chart_facts"):
        return {
            "purpose": "semantic slots for one named-chart prediction grounded in calculated chart data; not prewritten prose",
            "slots": [
                {"slot": "direct prediction in this chart's life area", "source": "evidence.chart_facts.charts.*.domain"},
                {"slot": "lagna and lagna-lord result", "source": "evidence.chart_facts.charts.*.lagna"},
                {"slot": "two strongest supported outcomes", "source": "evidence.chart_facts.charts.*.support_signals"},
                {"slot": "one main caution", "source": "evidence.chart_facts.charts.*.caution_signals"},
                {"slot": "one compact proof from this named chart", "source": "evidence.chart_facts.analysis_brief"},
                {"slot": "one domain follow-up", "source": "evidence.chart_facts.charts.*.domain.life_area"},
            ],
            "user_goal": query_plan.get("user_goal"),
        }
    if query_plan.get("answer_mode") == "potential_capacity":
        return {
            "purpose": "semantic slots for a static natal-promise judgment; not event timing and not prewritten prose",
            "slots": [
                {"slot": "clear yes, qualified yes, mixed, or not-established natal-promise verdict", "source": "verdict.direction"},
                {"slot": "direct natal support or limitation", "source": "evidence.natal_promise and evidence.topic_confirmation"},
                {"slot": "relevant divisional confirmation or qualification", "source": "evidence.divisional_specifics"},
                {"slot": "main condition or obstruction without invented biography", "source": "verdict.rationale, evidence.risk_specifics, and evidence.special_natal_factors"},
                {"slot": "one natural follow-up about timing or the user's real situation", "source": "user_goal"},
            ],
            "user_goal": query_plan.get("user_goal"),
        }
    slots = [{"slot": "direct real-life verdict", "source": "verdict"}]
    if evidence.get("period_topic_forecast"):
        slots.append(
            {
                "slot": "material chronological phases",
                "source": "evidence.period_topic_forecast.chronological_phases",
            }
        )
    timeline = evidence.get("transit_activation_timeline")
    has_peak = bool(
        (isinstance(timeline, dict) and timeline.get("peak_windows"))
        or verdict.get("ranked_windows")
    )
    if has_peak:
        slots.append(
            {
                "slot": "strongest supported window",
                "source": "verdict.ranked_windows or evidence.transit_activation_timeline.peak_windows",
            }
        )
    if evidence.get("active_areas") or evidence.get("topic_confirmation"):
        slots.append(
            {
                "slot": "main opportunity",
                "source": "evidence.active_areas and evidence.topic_confirmation",
            }
        )
    if evidence.get("risk_specifics") or verdict.get("modifiers"):
        slots.append(
            {"slot": "main pressure", "source": "evidence.risk_specifics and verdict.modifiers"}
        )
    slots.extend(
        [
            {"slot": "one practical implication", "source": "the fused facts above"},
            {
                "slot": "one natural follow-up question",
                "source": "user_goal and the user's real-life concern",
            },
        ]
    )
    return {
        "purpose": "semantic slots for one direct user-facing answer; not prewritten prose",
        "slots": slots,
        "user_goal": query_plan.get("user_goal"),
    }


def _build_instant_composer_context(
    instant_context: Dict[str, Any],
    instant_v2_packet: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the sole evidence brief sent to the answer-writing model.

    The full packet remains available for audit/UI evidence.  This boundary is
    deliberately verdict-first: the composer receives the fused result and a
    small set of answer-bearing facts, not the raw calculation workspace plus
    three differently-normalized copies of it.
    """
    query_plan = instant_v2_packet.get("query_plan")
    query_plan = query_plan if isinstance(query_plan, dict) else {}
    verdict = instant_v2_packet.get("verdict")
    verdict = verdict if isinstance(verdict, dict) else {}
    answer_spec = instant_v2_packet.get("answer_spec")
    normalized = instant_context.get("normalized_evidence")
    normalized = normalized if isinstance(normalized, dict) else {}
    intent = instant_context.get("intent_summary")
    intent = intent if isinstance(intent, dict) else {}
    birth = instant_context.get("birth_summary")
    birth = birth if isinstance(birth, dict) else {}

    user_derivation = instant_v2_packet.get("user_derivation")
    user_derivation = user_derivation if isinstance(user_derivation, dict) else {}
    career_reading = user_derivation.get("career_reading")
    career_reading = career_reading if isinstance(career_reading, dict) else {}
    derived_promise = user_derivation.get("natal_promise")
    derived_promise = derived_promise if isinstance(derived_promise, dict) else {}
    special_natal_factors: List[Dict[str, Any]] = []
    for house_row in derived_promise.get("d1_house_factors") or []:
        if not isinstance(house_row, dict):
            continue
        house = house_row.get("house")
        for polarity, key in (
            ("supportive", "special_support_notes"),
            ("challenging", "special_caution_notes"),
        ):
            for note in house_row.get(key) or []:
                if not str(note or "").strip():
                    continue
                special_natal_factors.append({
                    "house": house,
                    "polarity": polarity,
                    "effect": str(note).strip(),
                })
                if len(special_natal_factors) >= 8:
                    break
            if len(special_natal_factors) >= 8:
                break
        if len(special_natal_factors) >= 8:
            break

    compact_query_plan = {
        key: query_plan.get(key)
        for key in (
            "category",
            "answer_mode",
            "user_goal",
            "interpretation_frame",
            "target_subject",
            "time_scope",
        )
        if query_plan.get(key) not in (None, "", [], {})
    }
    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), dict) else {}
    scope_start = time_scope.get("as_of")
    scope_end = time_scope.get("horizon_end")
    if time_scope.get("retrospective"):
        scope_start = None
    compact_verdict = {
        "direction": verdict.get("direction"),
        "confidence": verdict.get("confidence"),
        "ranked_windows": _bound_composer_windows(
            verdict.get("ranked_windows"), start=scope_start, end=scope_end
        ),
        "rationale": verdict.get("rationale"),
        "modifiers": verdict.get("modifiers"),
        "missing_required_capabilities": verdict.get("missing_required_capabilities"),
    }
    compact_verdict = {
        key: value for key, value in compact_verdict.items() if value not in (None, "", [], {})
    }

    answer_mode = str(intent.get("answer_mode") or query_plan.get("answer_mode") or "")
    category = str(intent.get("category") or query_plan.get("category") or "general")
    career_foundation = (
        normalized.get("career_foundation")
        if isinstance(normalized.get("career_foundation"), dict)
        else {}
    )
    career_reading = (
        user_derivation.get("career_reading")
        if isinstance(user_derivation.get("career_reading"), dict)
        else {}
    )
    career_subtype = normalize_career_subtype(
        category,
        intent.get("career_subtype")
        or query_plan.get("career_subtype")
        or career_foundation.get("career_subtype")
        or career_reading.get("subtype"),
    )
    career_contract = (
        build_career_answer_contract(answer_mode, career_subtype)
        if is_career_category(category)
        else {}
    )
    career_family = str(career_contract.get("question_family") or "")
    career_diagnosis_question = career_family == "diagnosis"
    career_relationship_question = is_career_relationship(category, career_subtype)
    career_decision_question = is_career_decision(category, career_subtype)
    if is_career_category(category):
        compact_query_plan["career_subtype"] = career_subtype
    if career_decision_question:
        compact_query_plan["forecast_shape"] = "career_decision"
    static_career_profile = is_static_career_profile(
        category,
        career_subtype,
        answer_mode=answer_mode,
    )
    health_rules = (
        answer_spec.get("health_rules")
        if isinstance(answer_spec, dict) and isinstance(answer_spec.get("health_rules"), dict)
        else {}
    )
    period_topic_forecast = (
        _build_period_topic_forecast(
            normalized,
            category,
            query_plan.get("time_scope"),
            health_rules=health_rules,
        )
        if (
            answer_mode == "timing_window"
            or (
                answer_mode == "event_prediction"
                and _normalize_event_category(category)
                in {"health", "mental_wellbeing", "surgery", "accident", "recovery"}
            )
        )
        and _normalize_event_category(category) not in {"general", "timing"}
        else {}
    )
    if period_topic_forecast:
        compact_query_plan["forecast_shape"] = "period_topic_forecast"
    exact_day = bool(time_scope.get("is_exact_day"))
    if exact_day:
        compact_query_plan["forecast_shape"] = "daily_forecast"

    compact_answer_contract = _compact_answer_spec_for_composer(answer_spec)
    if career_contract:
        # The normalized evidence contract is category-level.  Replace its
        # generic career contract with the exact subtype/family contract that
        # was selected for this turn (recognition, stagnation, decision, etc.).
        compact_answer_contract["career_contract"] = career_contract
        compact_answer_contract["answer_skeleton"] = career_contract.get("required_shape")
    broad_health_question = bool(
        health_rules and not health_rules.get("is_time_bound_question")
    )
    if broad_health_question:
        # The generic adjudicated verdict may legitimately contain current
        # dasha/transit rationale for other answer shapes.  A constitutional
        # vulnerability question must not expose that alternate narrative to
        # the writer, even when the natal health evidence is already clean.
        compact_verdict = {
            "direction": "constitutional susceptibility",
            "confidence": verdict.get("confidence"),
            "scope": "natal constitution only; no current timing",
        }
    if static_career_profile:
        # Routing is already correct for questions such as "How is my career
        # overall?".  Do not let the final writer see incidental horizon,
        # dasha, or transit fields that were calculated for other answer
        # shapes.  A prompt warning is insufficient when the evidence itself
        # contradicts it, so enforce the boundary structurally.
        compact_query_plan.pop("time_scope", None)
        compact_query_plan.pop("forecast_shape", None)
        compact_verdict = {
            key: value
            for key, value in {
                "direction": verdict.get("direction"),
                "confidence": verdict.get("confidence"),
                "missing_required_capabilities": verdict.get("missing_required_capabilities"),
                "scope": "natal and vocational profile only; no event timing",
            }.items()
            if value not in (None, "", [], {})
        }
        # Static vocation/capacity answers must not inherit the generic event
        # contract assembled upstream. Keeping event windows here gives the
        # composer a second, contradictory route to dated predictions.
        for key in ("activation_prediction_rules", "event_rules", "current_cause_rules", "daily_rules"):
            compact_answer_contract.pop(key, None)

    if career_diagnosis_question:
        # A causal "why" question is neither a static vocation profile nor a
        # future forecast.  Keep only an auditable current trigger, when one is
        # actually present, and never expose ranked future windows to the
        # writer merely because the calculation workspace produced them.
        compact_query_plan.pop("time_scope", None)
        compact_query_plan.pop("forecast_shape", None)
        compact_verdict = {
            key: value
            for key, value in {
                "direction": verdict.get("direction"),
                "confidence": verdict.get("confidence"),
                "missing_required_capabilities": verdict.get("missing_required_capabilities"),
                "scope": "career cause diagnosis; current trigger only when directly evidenced; no future timing",
            }.items()
            if value not in (None, "", [], {})
        }
        for key in ("activation_prediction_rules", "event_rules", "current_cause_rules", "daily_rules"):
            compact_answer_contract.pop(key, None)
        compact_verdict = {
            key: value for key, value in compact_verdict.items()
            if value not in (None, "", [], {})
        }

    chart_facts = normalized.get("chart_facts") if isinstance(normalized.get("chart_facts"), dict) else {}
    is_chart_fact = str(answer_mode or "") == "factual_chart_lookup"
    if is_chart_fact:
        compact_query_plan["forecast_shape"] = "chart_fact_reading"
        special = query_plan.get("special_flow") if isinstance(query_plan.get("special_flow"), dict) else {}
        requested_chart = special.get("requested_chart") or (chart_facts.get("requested_charts") or [None])[0]
        if requested_chart:
            compact_query_plan["requested_chart"] = requested_chart

    evidence = {
        "natal_promise": normalized.get("natal_promise"),
        "special_natal_factors": special_natal_factors,
        # A future option-comparison already carries its window-specific dasha
        # evidence in the verdict. Supplying the present chain as well invited
        # the composer to explain a 2027 result with a 2026 chain.
        "current_timing": (
            None
            if period_topic_forecast or (answer_mode.startswith("comparison") and compact_verdict.get("ranked_windows"))
            else normalized.get("current_timing")
        ),
        "period_topic_forecast": period_topic_forecast,
        "active_areas": list(normalized.get("active_areas") or [])[:4],
        "topic_confirmation": normalized.get("topic_confirmation"),
        "transit_activation_timeline": {
            "peak_windows": _bound_composer_windows(
                (normalized.get("transit_activation_timeline") or {}).get("peak_windows")
                if isinstance(normalized.get("transit_activation_timeline"), dict)
                else [],
                start=scope_start,
                end=scope_end,
            ),
            "high_activity_claim_gate": (
                (normalized.get("transit_activation_timeline") or {}).get("high_activity_claim_gate")
                if isinstance(normalized.get("transit_activation_timeline"), dict)
                else None
            ),
        },
        "divisional_specifics": list(normalized.get("divisional_specifics") or [])[:3],
        "career_foundation": normalized.get("career_foundation"),
        "risk_specifics": list(normalized.get("risk_specifics") or [])[:3],
        "health_body_area": normalized.get("health_body_area"),
        "option_comparison": normalized.get("option_comparison"),
        "marriage_pathway_comparison": normalized.get("marriage_pathway_comparison"),
        "spouse_meeting_context": normalized.get("spouse_meeting_context"),
        "spouse_temperament_context": normalized.get("spouse_temperament_context"),
        "spouse_appearance_context": normalized.get("spouse_appearance_context"),
        "spouse_location_context": normalized.get("spouse_location_context"),
        "historical_event_dasha_scan": normalized.get("historical_event_dasha_scan"),
        "daily_prediction": _compact_daily_prediction_for_composer(
            instant_context.get("daily_prediction_spine") or normalized.get("daily_prediction_spine")
        ) if exact_day else None,
    }
    live_graph_policy = (
        compact_answer_contract.get("knowledge_graph_policy")
        if isinstance(compact_answer_contract.get("knowledge_graph_policy"), dict)
        else {}
    )
    graph_exclusions = {
        str(value) for value in live_graph_policy.get("default_exclusions") or []
    }
    graph_excludes_timing = bool(
        live_graph_policy.get("live")
        and (
            str(live_graph_policy.get("runtime_key") or "") == "marriage_remedies"
            or any(
                marker in value.lower()
                for value in graph_exclusions
                for marker in ("dashaactivation", "transitactivation", "transitconfirmation")
            )
        )
    )
    if graph_excludes_timing:
        # Enforce authored static/timing separation on the data boundary. The
        # writer cannot leak incidental dates or activations it never receives.
        compact_query_plan.pop("time_scope", None)
        compact_query_plan.pop("forecast_shape", None)
        evidence["current_timing"] = None
        evidence["period_topic_forecast"] = None
        evidence["transit_activation_timeline"] = None
        if isinstance(evidence.get("natal_promise"), dict):
            evidence["natal_promise"] = {
                key: value for key, value in evidence["natal_promise"].items()
                if key not in {"current_topic_support", "dasha_permission_segment_count", "rule"}
            }
        if isinstance(evidence.get("topic_confirmation"), dict):
            evidence["topic_confirmation"] = {
                key: value for key, value in evidence["topic_confirmation"].items()
                if key != "current_topic_support"
            }
        evidence["divisional_specifics"] = [
            line for line in list(evidence.get("divisional_specifics") or [])
            if not re.search(r"\b(current|active|dasha|period|transit)\b", str(line), re.I)
        ]
        compact_verdict.pop("ranked_windows", None)
        compact_verdict["scope"] = "static graph route; natal/topic evidence only; no timing"
        for key in ("activation_prediction_rules", "event_rules", "current_cause_rules", "daily_rules"):
            compact_answer_contract.pop(key, None)
    if career_decision_question:
        career_rules = (
            answer_spec.get("career_rules")
            if isinstance(answer_spec, dict) and isinstance(answer_spec.get("career_rules"), dict)
            else {}
        )
        rich_windows = [
            row for row in (career_reading.get("delivery_windows") or [])
            if isinstance(row, dict)
        ]
        raw_windows = career_rules.get("material_windows") or rich_windows

        def _matching_rich_career_window(row: Dict[str, Any]) -> Dict[str, Any]:
            """Join the decision verdict to its auditable dasha/transit record."""
            def normalized_chain(value: Any) -> str:
                # Material windows and calculator windows may use hyphens or
                # en-dashes for the same MD/AD/PD chain.
                return "".join(char.lower() for char in str(value or "") if char.isalnum())

            for candidate in rich_windows:
                same_dates = (
                    str(candidate.get("start") or "") == str(row.get("start") or "")
                    and str(candidate.get("end") or "") == str(row.get("end") or "")
                )
                same_chain = (
                    not row.get("chain")
                    or not candidate.get("chain")
                    or normalized_chain(candidate.get("chain")) == normalized_chain(row.get("chain"))
                )
                if same_dates and same_chain:
                    return candidate
            return {}

        decision_windows: List[Dict[str, Any]] = []
        for row in raw_windows:
            if not isinstance(row, dict):
                continue
            rich_row = _matching_rich_career_window(row)
            matrix = row.get("decision_matrix") if isinstance(row.get("decision_matrix"), dict) else {}
            if not matrix and isinstance(rich_row.get("decision_matrix"), dict):
                matrix = rich_row.get("decision_matrix") or {}
            activated_houses = list(matrix.get("active_houses") or [])
            compact_row = {
                "start": row.get("start") or rich_row.get("start"),
                "end": row.get("end") or rich_row.get("end"),
                "chain": row.get("chain") or rich_row.get("chain"),
                "activated_focus_houses": (
                    activated_houses
                    or rich_row.get("activated_focus_houses")
                    or []
                ),
                "decision_matrix": matrix,
                "manifestations": row.get("manifestations") or row.get("stages") or [],
                "why": row.get("why") or rich_row.get("why"),
                "dasha_carriers": (
                    row.get("dasha_carriers")
                    or rich_row.get("dasha_carriers")
                    or []
                ),
                "transit_confirmations": (
                    row.get("transit_confirmations")
                    or rich_row.get("transit_confirmations")
                    or []
                ),
            }
            decision_windows.append({
                key: value for key, value in compact_row.items()
                if value not in (None, "", [], {})
            })
        supported_windows = [
            row for row in decision_windows
            if (row.get("decision_matrix") or {}).get("verdict") == "planned_transition_supported"
        ]
        unsupported_windows = [
            row for row in decision_windows
            if (row.get("decision_matrix") or {}).get("verdict") != "planned_transition_supported"
        ]
        affirmative_exit_allowed = bool(supported_windows)
        safe_guidance = (
            "A planned transition has calculated change, separation, and next-role landing support. "
            "Discuss only the supplied supported windows and still advise securing the next role or income before resigning."
            if affirmative_exit_allowed
            else
            "The available calculations do not authorize resignation. Keep the current role while preparing options, "
            "or ask about a secured offer or a specific intended transition window."
        )
        evidence["career_decision"] = {
            "subtype": career_subtype,
            "permission": (
                "planned_transition_supported" if affirmative_exit_allowed else "resignation_not_authorized"
            ),
            "affirmative_exit_allowed": affirmative_exit_allowed,
            "guidance": safe_guidance,
            "windows": decision_windows,
            "supported_transition_windows": supported_windows,
            "non_transition_windows": unsupported_windows,
            "required_logic": {
                "continuity": "H6 + H10; H2/H11 strengthen employment and income continuity.",
                "change_and_separation": "H3 + H10 indicate an initiated role change; H12 is required for separation.",
                "next_role_landing": "H2 + H6 + H10 + H11 support income, employment, role, and gains in the next position.",
                "not_permission": "Career fit, dissatisfaction, H8 disruption, or H12 alone never authorizes resignation.",
            },
            "composer_rule": (
                "Positive change dates may be named only from supported_transition_windows."
                if affirmative_exit_allowed else
                "No supported transition window was calculated. Do not name any supplied window as a good time "
                "to leave or change jobs; say that the calculated horizon does not yet establish one."
            ),
        }
        compact_verdict = {
            "direction": (
                "planned transition supported only in supplied windows"
                if affirmative_exit_allowed
                else "do not resign on the available evidence"
            ),
            "confidence": verdict.get("confidence") or ("medium" if affirmative_exit_allowed else "low"),
            "scope": "calculated stay/change/separation/landing decision",
            "guidance": safe_guidance,
        }
    if broad_health_question:
        # A constitutional health question must not expose dasha, transit, or
        # generic active-area data to the writer. Those are valid elsewhere,
        # but here they create a competing timing narrative and encourage the
        # model to claim that Houses 6/8 are "currently active" without an
        # adjudicated health-timing question.
        evidence = {"health_rules": compact_answer_contract.get("health_rules")}
    if career_diagnosis_question:
        evidence = {
            "natal_promise": evidence.get("natal_promise"),
            "career_foundation": evidence.get("career_foundation"),
            "special_natal_factors": evidence.get("special_natal_factors"),
            "current_timing": evidence.get("current_timing"),
            "active_areas": evidence.get("active_areas"),
            "topic_confirmation": evidence.get("topic_confirmation"),
            "divisional_specifics": evidence.get("divisional_specifics"),
            "risk_specifics": evidence.get("risk_specifics"),
            # This is the adjudicated question-specific diagnosis.  Without
            # it the composer sees only the generic D1/D10 foundation and is
            # tempted to invent a timing story for questions such as
            # "why am I not getting recognition?".
            "career_diagnosis": career_reading.get("diagnosis"),
        }
    if career_relationship_question:
        evidence = {
            "natal_promise": evidence.get("natal_promise"),
            "career_relationship": career_reading.get("relationship"),
            "special_natal_factors": evidence.get("special_natal_factors"),
        }
        compact_verdict = {
            "direction": "role-specific workplace relationship",
            "confidence": verdict.get("confidence") or "medium",
            "scope": career_reading.get("relationship", {}).get("target"),
        }
    if static_career_profile:
        natal_promise = evidence.get("natal_promise")
        natal_promise = dict(natal_promise) if isinstance(natal_promise, dict) else natal_promise
        if isinstance(natal_promise, dict):
            for key in (
                "current_topic_support",
                "dasha_permission_segment_count",
                "dasha_permission",
                "transit_permission",
                "rule",
            ):
                natal_promise.pop(key, None)
        topic_confirmation = evidence.get("topic_confirmation")
        topic_confirmation = (
            dict(topic_confirmation) if isinstance(topic_confirmation, dict) else topic_confirmation
        )
        # ``topic_signals.fn`` is an older generic function list. Once the
        # chart-specific vocation synthesis exists, leaving this parallel list
        # in the brief lets the writer choose generic administration/process
        # labels over the actual 10th-lord combinations.
        if (
            isinstance(topic_confirmation, dict)
            and isinstance(evidence.get("career_foundation"), dict)
            and (evidence.get("career_foundation") or {}).get("vocation_synthesis")
        ):
            topic_signals = topic_confirmation.get("topic_signals")
            if isinstance(topic_signals, dict):
                topic_signals = dict(topic_signals)
                topic_signals.pop("fn", None)
                topic_confirmation["topic_signals"] = topic_signals
        evidence = {
            "natal_promise": natal_promise,
            "career_foundation": evidence.get("career_foundation"),
            "special_natal_factors": evidence.get("special_natal_factors"),
            "topic_confirmation": topic_confirmation,
            "divisional_specifics": evidence.get("divisional_specifics"),
            "risk_specifics": evidence.get("risk_specifics"),
        }
    if answer_mode == "potential_capacity":
        # A natal-promise question must not expose current timing as an
        # alternative reasoning path. This also keeps the composer brief small.
        evidence = {
            "natal_promise": evidence.get("natal_promise"),
            "special_natal_factors": evidence.get("special_natal_factors"),
            "topic_confirmation": evidence.get("topic_confirmation"),
            "divisional_specifics": evidence.get("divisional_specifics"),
            "risk_specifics": evidence.get("risk_specifics"),
            # Static career-capacity questions (for example, "what career
            # will I do?") require the calculated D1/D10/Jaimini vocation
            # synthesis.  Dropping this here left only the old generic
            # topic_signals.fn labels for the composer, even though the
            # calculation stage had produced the correct individualized
            # signature.
            "career_foundation": (
                evidence.get("career_foundation") if static_career_profile else None
            ),
        }
    if exact_day:
        # Exact-day forecasts have their own authoritative calculation spine.
        # Do not let broad-period timing, generic active-area summaries, or slow
        # transit timelines compete with KP/Moon/Tara and five-level dashas in
        # the composer prompt.
        evidence = {
            "natal_promise": evidence.get("natal_promise"),
            "daily_prediction": evidence.get("daily_prediction"),
        }
    if is_chart_fact:
        compact_charts: Dict[str, Any] = {}
        raw_charts = chart_facts.get("charts") if isinstance(chart_facts.get("charts"), dict) else {}
        for chart_name, row in raw_charts.items():
            if not isinstance(row, dict):
                continue
            compact_charts[str(chart_name)] = _compact_chart_for_composer_prediction(str(chart_name), row)
        evidence = {
            "chart_facts": {
                "requested_charts": chart_facts.get("requested_charts"),
                "prediction_format": chart_facts.get("prediction_format") or list(_CHART_PREDICTION_FORMAT),
                "analysis_brief": chart_facts.get("analysis_brief") or chart_facts.get("reading_text"),
                "reading_text": chart_facts.get("reading_text"),
                "missing_requested_charts": chart_facts.get("missing_requested_charts"),
                "source": chart_facts.get("source"),
                "charts": compact_charts,
            }
        }
    if answer_mode == "remedy_action":
        # RemedyEngine has already converted the chart, current dasha and
        # special-point calculations into an actionable remedy plan.  Keep
        # that plan at the verdict-first composer boundary; otherwise the
        # writer sees only ordinary topic evidence and improvises generic
        # career/relationship advice instead of returning remedies.
        remedy_blueprint = (
            normalized.get("remedy_blueprint")
            if isinstance(normalized.get("remedy_blueprint"), dict)
            else {}
        )
        evidence = {
            "remedy_blueprint": remedy_blueprint,
            "question_focus": normalized.get("question_focus") or remedy_blueprint.get("question_focus"),
            "primary_drivers": list(
                normalized.get("primary_drivers")
                or remedy_blueprint.get("candidate_planets")
                or []
            )[:4],
            "top_risks": list(
                normalized.get("top_risks")
                or remedy_blueprint.get("priority_order")
                or []
            )[:4],
            "special_points": normalized.get("special_points") or remedy_blueprint.get("special_points"),
            "remedy_sections": normalized.get("remedy_sections") or remedy_blueprint.get("remedy_sections"),
            "caution": normalized.get("caution") or remedy_blueprint.get("caution"),
            "current_timing": (
                None
                if str(live_graph_policy.get("runtime_key") or "") == "marriage_remedies"
                else normalized.get("current_timing")
            ),
        }
    evidence = {key: value for key, value in evidence.items() if value not in (None, "", [], {})}

    answer_blueprint = _build_instant_answer_blueprint(
        query_plan=compact_query_plan,
        verdict=compact_verdict,
        evidence=evidence,
    )
    answer_blueprint = {
        key: value for key, value in answer_blueprint.items() if value not in (None, "", [], {})
    }

    context = {
        "context_profile": "instant_composer_v3",
        "native": {
            key: birth.get(key)
            for key in ("name", "ascendant", "moon")
            if birth.get(key) not in (None, "", [], {})
        },
        "intent": {
            "category": intent.get("category") or query_plan.get("category"),
            "answer_mode": intent.get("answer_mode") or query_plan.get("answer_mode"),
            "period_window": intent.get("period_window"),
            "time_relation": intent.get("time_relation"),
            "target_subject": intent.get("target_subject") or query_plan.get("target_subject"),
            "career_subtype": career_subtype if is_career_category(category) else None,
        },
        "query_plan": compact_query_plan,
        "verdict": compact_verdict,
        "evidence": evidence,
        "answer_blueprint": answer_blueprint,
        "answer_contract": compact_answer_contract,
        # Prior turns can contain perfectly valid dasha discussion, but it is
        # not evidence for a fresh, non-time-bound health susceptibility
        # question.  Excluding it prevents timing language from leaking back
        # into an otherwise natal-only composer brief.
        "recent_history": (
            []
            if broad_health_question or static_career_profile or career_diagnosis_question or graph_excludes_timing
            else list(instant_context.get("recent_history") or [])[-2:]
        ),
    }
    context["intent"] = {
        key: value for key, value in context["intent"].items()
        if value not in (None, "", [], {})
    }
    if static_career_profile or career_diagnosis_question:
        context["intent"].pop("period_window", None)
        context["intent"].pop("time_relation", None)
    app_language = str(query_plan.get("language") or intent.get("language") or "").strip().lower()
    if app_language:
        context["app_language_fallback"] = app_language
    if is_chart_fact:
        return context
    return _fit_composer_brief(context)


def _instant_composer_language_rule(language: str) -> str:
    """Ask the composer to follow the user's conversation, not the app locale."""
    fallback = (language or "english").strip().lower() or "english"
    return (
        f"- The resolved language of the latest user message is `{fallback}`. Use it as the controlling language. "
        "Write in the same language and script as the USER QUESTION and latest user message, using recent user messages for natural tone. "
        "If this turn is a short clarification answer, keep the language of the original question in USER QUESTION or recent_history. "
        "Chart evidence and this brief are English internally; never switch the user-facing answer to English because of that. "
        f"The app language setting `{fallback}` is only a fallback when the conversation language is truly unclear. "
        "If the user mixes languages or writes a regional language in Latin letters, mirror that mix instead of switching to English or a more formal script."
    )


def _instant_relational_voice_contract() -> str:
    """Shared user-facing voice for every Instant LLM answer path."""
    return """RELATIONAL VOICE CONTRACT:
- Sound like a warm, emotionally perceptive and honest personal guide. The user should feel understood as a person, not processed as a question.
- Infer the human need behind the question—uncertainty, hope, fear, validation, direction, reassurance or self-understanding—and respond to it naturally without naming or announcing that inference.
- Answer directly first, then translate the supported result into lived experience: what the pattern may feel like, how it may show up, and why it matters to this person.
- Make empathy specific through the substance of the answer. Never add canned lines such as "I understand how you feel", "that must be difficult", or "the universe has a plan".
- Preserve emotional nuance. Explain mixed evidence as competing needs or pressures rather than calling it merely unclear. Make difficult indications illuminating, not frightening; make supportive indications encouraging, not guaranteed.
- Use psychologically perceptive language without diagnosing mental-health conditions, inventing motives, claiming to know hidden feelings, or presenting astrology as fixed identity or fate. Protect the user's agency and include a useful reflection or next step when appropriate.
- Match the user's emotional intensity. Be gentle for vulnerable subjects, energizing for opportunities, grounding for anxiety and direct for decisions. Do not make every answer dramatic.
- Use natural modern conversation, not forced youth slang, excessive emojis, therapy-speak, mystical theatre, pet names or manufactured intimacy.
- End with one specific, emotionally meaningful question that helps reveal the user's real concern or lived situation; never use a generic continuation or sales question.
- Never encourage dependency or imply Tara is conscious, uniquely understands the user, replaces people or professionals, or is the only guidance they need."""


def _build_budgeted_instant_prompt(
    question: str,
    context: Dict[str, Any],
    language: str,
) -> str:
    """Compact equivalent used only when the full house prompt exceeds budget."""
    context_json = json.dumps(context, ensure_ascii=False, default=str, separators=(",", ":"))
    return f"""You are AstroRoshni's Instant Chat answer composer.
Answer the user's astrology question from the supplied adjudicated context only.
{_instant_composer_language_rule(language)}
{_instant_relational_voice_contract()}
- Lead with the direct real-world answer. Stay under the contract word limit and end with one natural question.
- Treat query_plan, verdict, answer_contract, and evidence as strict. Never invent a date, body area, option winner, chart fact, activated house, or causal factor.
- A live knowledge_graph_policy is authoritative. Obey its exclusions, required sections, guardrails, claim_permission, and limitation_instruction. Missing required factors mean the dependent conclusion is unavailable.
- Never mention a date after query_plan.time_scope.horizon_end. Use only ranked/allowed windows attached to their own evidence.
- When query_plan.time_scope.retrospective is true, rank only past windows and describe them as probable periods that need user confirmation; never claim you recovered the factual marriage date.
- For retrospective marriage timing, every ranked window must show: (1) the broad MD-AD phase, (2) the exact strongest_pd_window as an MD-AD-PD sub-sub-period with its start and end dates, and (3) one or two probable_peak_windows. Never label the whole MD-AD phase with its winning PD planet.
- For comparisons, evaluate both options from option-specific evidence. If evidence does not distinguish them, do not choose a winner.
- For comparisons, every date, dasha chain, score, and reason belongs only to the option row that contains it. Never attach one option's window to the other.
- MD, AD, and PD mean major, sub-, and sub-sub-period. Never call the PD planet the sub-period lord.
- Health statements are susceptibilities, not diagnoses. Name only zones explicitly allowed by health_rules and recommend professional care for persistent symptoms.
- Translate astrology into ordinary life language; use at most one compact technical reason unless the user asks why.
- Do not expose internal IDs or JSON. Do not add a decorative heading.
- Finish the response with exactly: NEXT_ACTION_META: {{"type":"none","title":"","reason":"","confidence":""}}

USER QUESTION:
{question}

ADJUDICATED CONTEXT:
{context_json}""".strip()


def _build_retrospective_budget_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Keep phase, PD and peak dates under the compact prompt budget.

    Generic emergency depth limiting is unsafe for retrospective timing because
    the decisive PD and peak rows are nested below each broad MD-AD phase.
    """
    if not isinstance(context, dict):
        return {}
    query_plan = context.get("query_plan") if isinstance(context.get("query_plan"), dict) else {}
    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), dict) else {}
    if not time_scope.get("retrospective"):
        return {}
    verdict = context.get("verdict") if isinstance(context.get("verdict"), dict) else {}
    windows: List[Dict[str, Any]] = []
    for row in list(verdict.get("ranked_windows") or [])[:3]:
        if not isinstance(row, dict):
            continue
        strongest = row.get("strongest_pd_window") if isinstance(row.get("strongest_pd_window"), dict) else {}
        peaks = []
        for peak in list(row.get("probable_peak_windows") or [])[:2]:
            if not isinstance(peak, dict):
                continue
            peaks.append({
                key: peak.get(key)
                for key in (
                    "probable_peak_date", "probable_peak_end", "planet",
                    "supporting_pratyantardashas", "strength", "activated_focus_houses",
                )
                if peak.get(key) not in (None, "", [], {})
            })
        windows.append({
            key: value
            for key, value in {
                "start": row.get("start"),
                "end": row.get("end"),
                "phase_dasha_chain": row.get("phase_dasha_chain"),
                "phase_granularity": row.get("phase_granularity"),
                "mahadasha": row.get("mahadasha"),
                "antardasha": row.get("antardasha"),
                "strongest_pd_window": {
                    key: strongest.get(key)
                    for key in ("start", "end", "pratyantardasha")
                    if strongest.get(key) not in (None, "")
                },
                "probable_peak_windows": peaks,
            }.items()
            if value not in (None, "", [], {})
        })
    answer_contract = context.get("answer_contract") if isinstance(context.get("answer_contract"), dict) else {}
    graph_policy = (
        answer_contract.get("knowledge_graph_policy")
        if isinstance(answer_contract.get("knowledge_graph_policy"), dict)
        else {}
    )
    return {
        "context_profile": "instant_retrospective_budget_v1",
        "query_plan": {
            "category": query_plan.get("category"),
            "answer_mode": query_plan.get("answer_mode"),
            "time_scope": time_scope,
        },
        "verdict": {
            "direction": verdict.get("direction"),
            "confidence": verdict.get("confidence"),
            "ranked_windows": windows,
            "claim_rule": (
                (verdict.get("rationale") or {}).get("claim_rule")
                if isinstance(verdict.get("rationale"), dict) else None
            ),
        },
        "answer_contract": {
            "max_words": answer_contract.get("max_words"),
            "knowledge_graph_policy": {
                key: graph_policy.get(key)
                for key in ("live", "domain", "runtime_key", "question_type", "guardrails")
                if graph_policy.get(key) not in (None, "", [], {})
            },
            "required_structure": [
                "For each ranked row, state the broad MD-AD phase and its dates.",
                "Then state strongest_pd_window as the PD/sub-sub-period and copy its exact dates.",
                "Then state one or two probable_peak_windows as narrower concentrations.",
                "Never call a probable period the user's confirmed marriage date.",
            ],
        },
        "app_language_fallback": context.get("app_language_fallback"),
    }


def _instant_response_language(
    question: str,
    intent: Optional[Dict[str, Any]],
    app_language: str,
) -> str:
    """Prefer the multilingual router's latest-message language over UI locale.

    The mobile UI language controls chrome and may legitimately differ from
    the language typed in chat. The semantic router sees the full message and
    owns mixed/romanized-language detection; the UI value is only a fallback
    for older cached or degraded intent payloads.
    """
    intent = intent if isinstance(intent, dict) else {}
    text = str(question or "")
    script_languages = (
        (r"[\u0900-\u097f]", "hindi"),
        (r"[\u0980-\u09ff]", "bengali"),
        (r"[\u0a80-\u0aff]", "gujarati"),
        (r"[\u0b80-\u0bff]", "tamil"),
        (r"[\u0c00-\u0c7f]", "telugu"),
        (r"[\u0c80-\u0cff]", "kannada"),
        (r"[\u0d00-\u0d7f]", "malayalam"),
    )
    for pattern, language_name in script_languages:
        if re.search(pattern, text):
            return language_name
    # Override a bad router/UI locale only for unmistakably English syntax.
    # This is language detection, not intent routing. Requiring multiple
    # English function words avoids misclassifying Romanized Hindi/Hinglish.
    english_function_words = {
        "a", "an", "and", "are", "am", "can", "could", "do", "does",
        "for", "from", "how", "i", "in", "is", "me", "my", "of", "on",
        "should", "the", "this", "to", "what", "when", "where", "which",
        "why", "will", "with", "would", "you", "your",
    }
    latin_tokens = re.findall(r"[A-Za-z]+", text.lower())
    if len({token for token in latin_tokens if token in english_function_words}) >= 2:
        return "english"
    routed = str(
        intent.get("response_language")
        or intent.get("detected_language")
        or ""
    ).strip().lower()
    if routed:
        return routed[:40]
    # Latin-script ambiguity (English versus romanized Indian languages)
    # remains delegated to the app preference when syntax is inconclusive.
    return str(app_language or "english").strip().lower() or "english"


def _instant_answer_language_error(answer: str, response_language: str) -> str | None:
    """Detect a clearly wrong output script for fail-closed Health correction."""
    visible = str(answer or "").split("NEXT_ACTION_META:", 1)[0]
    language = str(response_language or "").strip().lower()
    devanagari_count = len(re.findall(r"[\u0900-\u097f]", visible))
    latin_count = len(re.findall(r"[A-Za-z]", visible))
    if language in {"english", "en"} and devanagari_count >= 8:
        return "answer language mismatch: expected English from the latest user question, received Devanagari/Hindi"
    if language in {"hindi", "hi"} and latin_count >= 40 and devanagari_count == 0:
        return "answer language mismatch: expected Hindi from the latest user question, received Latin-only text"
    return None


_HEALTH_FACT_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_HEALTH_FACT_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
_HEALTH_FACT_NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)


def _constitutional_health_required_rows(health_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the exact calculated rows that the health composer may verbalize."""
    rows: List[Dict[str, Any]] = []
    for rank, row in enumerate(list(health_rules.get("allowed_zone_evidence") or []), start=1):
        if not isinstance(row, dict) or not row.get("zone"):
            continue
        anatomy_basis = [str(value).strip() for value in (row.get("anatomy_basis") or []) if str(value).strip()]
        why = [str(value).strip() for value in (row.get("why") or []) if str(value).strip()]
        cause_facts = anatomy_basis or why
        anchors = list(dict.fromkeys(
            anchor
            for fact in cause_facts
            for anchor in _constitutional_health_fact_anchors(fact)
        ))
        marker_payload = "|".join([
            str(row.get("zone") or "").strip(),
            *anchors,
        ]).replace("]", "").replace("[", "")
        rows.append({
            "rank": rank,
            "region": str(row.get("zone") or "").strip(),
            "required_cause_facts": cause_facts,
            "allowed_mechanisms": list(row.get("mechanisms") or []),
            "confidence": row.get("confidence"),
            # A localized answer may translate every region, graha, sign and
            # house noun. This exact temporary marker lets the deterministic
            # validator bind that translated sentence back to its calculated
            # row. It is removed before anything is shown to the user.
            "validation_marker": f"[[HEALTH_EVIDENCE_{rank}:{marker_payload}]]",
        })
    return rows


def _resolve_constitutional_health_rules(
    prompt_context: Optional[Dict[str, Any]],
    instant_v2_packet: Optional[Dict[str, Any]],
    instant_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Resolve constitutional rules across every supported packet shape.

    Composer compaction intentionally moves fields around for different answer
    routes.  Validation must follow the authoritative answer specification, not
    assume that `evidence.health_rules` is always populated.
    """
    candidates: List[Any] = []
    for container in (prompt_context, instant_v2_packet, instant_context):
        if not isinstance(container, dict):
            continue
        evidence = container.get("evidence")
        if isinstance(evidence, dict):
            candidates.append(evidence.get("health_rules"))
        answer_contract = container.get("answer_contract")
        if isinstance(answer_contract, dict):
            candidates.append(answer_contract.get("health_rules"))
        answer_spec = container.get("answer_spec")
        if isinstance(answer_spec, dict):
            candidates.append(answer_spec.get("health_rules"))
        v2_contract = container.get("instant_v2_answer_contract")
        if isinstance(v2_contract, dict):
            v2_answer_spec = v2_contract.get("answer_spec")
            if isinstance(v2_answer_spec, dict):
                candidates.append(v2_answer_spec.get("health_rules"))

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("is_time_bound_question"):
            continue
        if candidate.get("allowed_zone_evidence"):
            return candidate
    return {}


def _constitutional_health_fact_anchors(fact: str) -> List[str]:
    """Extract invariant chart nouns from a calculated anatomical cause.

    These names and house numbers remain stable even when the surrounding prose
    is translated.  Requiring them prevents a small model from replacing, for
    example, `Mars in House 8` with `Mars in House 1` or `Moon in House 6`.
    """
    text = str(fact or "")
    anchors: List[str] = []
    for value in (*_HEALTH_FACT_PLANETS, *_HEALTH_FACT_SIGNS, *_HEALTH_FACT_NAKSHATRAS):
        if re.search(rf"\b{re.escape(value)}\b", text, flags=re.IGNORECASE):
            anchors.append(value)
    for house in re.findall(r"\bHouse\s+(\d{1,2})\b", text, flags=re.IGNORECASE):
        anchors.append(f"House {house}")
    return list(dict.fromkeys(anchors))


def _validate_constitutional_health_answer(
    answer: str,
    required_rows: List[Dict[str, Any]],
    *,
    strict_sentence_binding: bool = True,
) -> List[str]:
    """Reject health prose that drops or changes calculated anatomical causes."""
    visible = str(answer or "").split("NEXT_ACTION_META:", 1)[0]
    normalized = re.sub(r"\s+", " ", visible).strip()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    errors: List[str] = []
    for row in required_rows:
        region = str(row.get("region") or "").strip()
        validation_marker = str(row.get("validation_marker") or "").strip()
        localized_row_bound = bool(
            not strict_sentence_binding
            and validation_marker
            and validation_marker in visible
        )
        region_tokens = [
            token.lower()
            for token in re.findall(r"[A-Za-z]+", region)
            if len(token) >= 4 and token.lower() not in {"including", "region"}
        ]
        if not localized_row_bound and region and region.lower() not in normalized.lower() and not any(
            re.search(rf"\b{re.escape(token)}\b", normalized, flags=re.IGNORECASE)
            for token in region_tokens
        ):
            errors.append(f"missing region: {region}")
        facts = list(row.get("required_cause_facts") or [])
        if not facts:
            errors.append(f"{region}: missing calculated cause evidence")
            continue
        fact_anchor_sets = [
            _constitutional_health_fact_anchors(str(fact))
            for fact in facts
            if str(fact).strip()
        ]
        fact_anchor_sets = [anchors for anchors in fact_anchor_sets if anchors]
        def _anchor_is_present(anchor: str) -> bool:
            house_match = re.fullmatch(r"House\s+(\d{1,2})", anchor, flags=re.IGNORECASE)
            if house_match:
                number = house_match.group(1)
                return bool(re.search(
                    rf"(?:\bHouse\s+{number}\b|\b{number}(?:st|nd|rd|th)\s+(?:house|lord)\b|\blord\s+of\s+(?:the\s+)?(?:House\s+)?{number}\b)",
                    normalized,
                    flags=re.IGNORECASE,
                ))
            return bool(re.search(rf"\b{re.escape(anchor)}\b", normalized, flags=re.IGNORECASE))

        def _anchor_is_present_in(anchor: str, sentence: str) -> bool:
            house_match = re.fullmatch(r"House\s+(\d{1,2})", anchor, flags=re.IGNORECASE)
            if house_match:
                number = house_match.group(1)
                return bool(re.search(
                    rf"(?:\bHouse\s+{number}\b|\b{number}(?:st|nd|rd|th)\s+(?:house|lord)\b|\blord\s+of\s+(?:the\s+)?(?:House\s+)?{number}\b)",
                    sentence,
                    flags=re.IGNORECASE,
                ))
            return bool(re.search(rf"\b{re.escape(anchor)}\b", sentence, flags=re.IGNORECASE))

        anchors_present_globally = fact_anchor_sets and any(
            all(_anchor_is_present(anchor) for anchor in anchors)
            for anchors in fact_anchor_sets
        )
        anchors_bound_to_region = True
        if strict_sentence_binding and fact_anchor_sets and region_tokens:
            region_sentences = [
                sentence
                for sentence in sentences
                if any(re.search(rf"\b{re.escape(token)}\b", sentence, flags=re.IGNORECASE) for token in region_tokens)
            ]
            anchors_bound_to_region = any(
                all(_anchor_is_present_in(anchor, sentence) for anchor in anchors)
                for sentence in region_sentences
                for anchors in fact_anchor_sets
            )
        if not localized_row_bound and fact_anchor_sets and (not anchors_present_globally or not anchors_bound_to_region):
            expected = " or ".join(" + ".join(anchors) for anchors in fact_anchor_sets)
            errors.append(f"{region}: missing or misassigned immutable cause anchors ({expected})")
    return errors


def _strip_constitutional_health_validation_markers(answer: str) -> str:
    """Remove temporary multilingual fact-binding markers before display."""
    return re.sub(r"\s*\[\[HEALTH_EVIDENCE_\d+:[^\]]*\]\]", "", str(answer or "")).strip()


def _build_instant_composer_prompt_v3(
    question: str,
    composer_context: Dict[str, Any],
    language: str,
    *,
    speech_mode: bool = False,
) -> str:
    """Small, verdict-first prompt for the evidence-driven Instant pipeline."""
    context_json = json.dumps(composer_context, ensure_ascii=False, separators=(",", ":"))
    is_period_topic_forecast = str((composer_context.get("query_plan") or {}).get("forecast_shape") or "") == "period_topic_forecast"
    is_daily_forecast = str((composer_context.get("query_plan") or {}).get("forecast_shape") or "") == "daily_forecast"
    composer_health_rules = (
        (composer_context.get("evidence") or {}).get("health_rules")
        if isinstance(composer_context.get("evidence"), dict)
        else {}
    )
    if not isinstance(composer_health_rules, dict) or not composer_health_rules:
        composer_health_rules = (
            (composer_context.get("answer_contract") or {}).get("health_rules")
            if isinstance(composer_context.get("answer_contract"), dict)
            else {}
        )
    composer_health_rules = composer_health_rules if isinstance(composer_health_rules, dict) else {}
    is_constitutional_health = bool(
        composer_health_rules and not composer_health_rules.get("is_time_bound_question")
    )
    is_time_bound_health = bool(
        composer_health_rules and composer_health_rules.get("is_time_bound_question")
    )
    if is_constitutional_health:
        # Use a dedicated, deliberately small prompt.  The generic Instant
        # composer explains several timing answer shapes and even explicit
        # negative instructions were not enough to stop a small model from
        # borrowing that vocabulary.  This prompt contains no timing workflow
        # for it to imitate.
        # Give the small composer only the adjudicated zone rows it is allowed
        # to verbalize.  Passing the wider health foundation here made it easy
        # to confuse a planet's lordship (for example, Mars as ascendant lord)
        # with its actual house placement (Mars in House 8).
        required_zone_rows = _constitutional_health_required_rows(composer_health_rules)
        natal_health_context = {
            "scope": "natal constitution only",
            "native": composer_context.get("native") or {},
            "knowledge_graph_policy": (
                (composer_context.get("answer_contract") or {}).get("knowledge_graph_policy")
                if isinstance(composer_context.get("answer_contract"), dict)
                else {}
            ),
            "required_zone_count": composer_health_rules.get("required_zone_count"),
            "required_zone_rows": required_zone_rows,
            "protective_factors": composer_health_rules.get("protective_factors") or [],
            "condition_susceptibilities": composer_health_rules.get("condition_susceptibilities") or [],
        }
        natal_health_json = json.dumps(
            natal_health_context, ensure_ascii=False, separators=(",", ":")
        )
        return f"""
You are Tara in AstroRoshni Instant Chat. Write one natal constitutional-health susceptibility reading from the calculated evidence below.

{_instant_composer_language_rule(language)}
{_instant_relational_voice_contract()}

Required answer:
0. Follow the language and script of the USER QUESTION. The app-language fallback or internal English evidence must not override the user's actual language.
0a. The live `knowledge_graph_policy` is authoritative. Follow its guardrails and required output sections, never use its default exclusions, and do not infer any missing required factor.
1. Answer directly by naming every supplied anatomical region in its exact ranked order. None may be omitted, including a region derived from the anatomical field of the house occupied by the 6th lord.
2. Give every region its own explicit explanatory sentence. That sentence must name the region and faithfully express at least one item from that row's `required_cause_facts`; a bare label or a shared phrase such as "these areas are inflammatory" does not satisfy this requirement.
3. Treat every planet, sign, nakshatra, lordship and house number in `required_cause_facts` as immutable calculated data. Translate the prose when needed, but never replace, infer, or change those facts. If the fact says the 6th lord is placed in House 8, the visible answer must say House 8—not House 1 or any other house.
   When the answer is not English, copy that row's `validation_marker` exactly at the end of its explanatory sentence. This temporary marker is mandatory for every row and will be removed before display. Do not translate, alter, or collect the markers elsewhere.
4. When a row is derived from the house occupied by the 6th lord, explicitly state that exact destination house and connect its supplied anatomical field to the named region. Do not reduce this to a generic acute/inflammatory mechanism.
5. Explain each region only from its own `required_zone_rows` row. Do not move a reason or mechanism from one region to another and do not combine multiple regions under one shared explanation.
6. Give ordinary preventive care guidance without diagnosis, certainty, fear, or invented symptoms.
7. End with exactly one natural question about symptoms or preventive care.

Completeness and length:
- Use roughly 140-220 visible words when four regions are supplied. Completeness is more important than making this answer unusually short.
- Before finishing, compare the visible answer against every row in `required_zone_rows`: every region must have a distinct cause sentence and every planet/house fact must still match exactly.

Absolute exclusions:
- Do not mention a current period, Mahadasha, Antardasha, Pratyantardasha, dasha, transit, active houses, today, now, or any timing window.
- Do not say any vulnerability is currently active.
- Do not add any body area, condition, severity, or mechanism absent from the supplied evidence.
- Do not recalculate the chart. Do not add headings, bullets, disclaimers, remedies, sales copy, or feedback requests.

Append exactly one final metadata line after the visible answer:
NEXT_ACTION_META: {{"type":"none","title":"","reason":"","confidence":"low","follow_up_questions":[],"source":"instant"}}

USER QUESTION:
{question}

NATAL-ONLY HEALTH EVIDENCE:
{natal_health_json}
""".strip()
    is_chart_fact = (
        str((composer_context.get("query_plan") or {}).get("forecast_shape") or "") == "chart_fact_reading"
        or str((composer_context.get("intent") or {}).get("answer_mode") or "") == "factual_chart_lookup"
        or str((composer_context.get("query_plan") or {}).get("answer_mode") or "") == "factual_chart_lookup"
    )
    answer_mode = str(
        (composer_context.get("intent") or {}).get("answer_mode")
        or (composer_context.get("query_plan") or {}).get("answer_mode")
        or ""
    )
    answer_contract = (
        composer_context.get("answer_contract")
        if isinstance(composer_context.get("answer_contract"), dict)
        else {}
    )
    career_contract = (
        answer_contract.get("career_contract")
        if isinstance(answer_contract.get("career_contract"), dict)
        else {}
    )
    career_family = str(career_contract.get("question_family") or "")
    career_subtype = str(career_contract.get("career_subtype") or "")
    career_rules = ""
    if career_contract:
        career_rules = """
- This is a career answer. `answer_contract.career_contract` is a hard evidence boundary, not optional guidance.
- Use only the selected career question family. Do not turn a profile or diagnosis into a forecast, and do not turn a decision into a career-fit answer.
- Future dates, years, peaks and windows are forbidden unless `allow_dated_timing` is true. Never manufacture timing from remembered astrology or from a current dasha label.
- Current dasha or transit may be mentioned only when `allow_current_activation` is true and the supplied evidence explicitly connects it to the diagnosed career mechanism.
"""
        if career_family == "diagnosis":
            career_rules += """
- This is a present problem diagnosis. Give: direct cause -> recurring D1/D10 mechanism -> verified present trigger only if supplied -> one concrete action -> one follow-up question.
- Do not promise that recognition is coming. Do not cite a future date, year, peak or window.
- Do not say Saturn or a dasha creates behind-the-scenes work, delay, invisibility or lack of praise unless the supplied diagnostic evidence states that exact causal link.
"""
            if career_subtype == "recognition":
                career_rules += """
- Recognition must be explained as a conversion chain: House 6 effort/workload -> House 10 visibility/authority -> House 11 recognition/reward -> House 2 compensation.
- Hard work alone does not prove recognition. Identify the first unsupported or difficult conversion in that chain from `evidence.career_diagnosis`; do not substitute vocation fields or future timing.
"""
        elif career_family == "relationship":
            career_rules += """
- This is a workplace-relationship reading, not a vocation profile and not a generic career forecast. The named counterpart in `evidence.career_relationship.target` is the entire subject of the answer.
- Use `evidence.career_relationship.house_roles` as a semantic matrix. Explain the likely relationship dynamic by combining the supplied D1 role houses with their D10 confirmation; do not replace them with the generic Houses 2, 6, 10 and 11 career template.
- For a manager or authority relationship, House 9 describes guidance, judgment, senior authority and the native's receptivity to counsel; House 10 describes hierarchy, reputation and accountability; House 6 describes everyday service, disagreement and friction; House 11 describes support, recognition and fulfilment through that authority.
- For colleagues or peers, use the supplied peer-communication, daily-work, team-support and professional-standing roles. For direct reports, clients, business partners or mentors, use only their supplied role meanings rather than borrowing the manager rules.
- Give: (1) the likely relationship trajectory, (2) the strongest supportive mechanism, (3) the main friction mechanism, (4) one practical way to improve the dynamic, and (5) exactly one natural clarification about the present relationship.
- Do not discuss suitable industries, technical identity, career fields, 10th-lord vocation combinations, Amatyakaraka or Karakamsha unless the user separately asks what work they should do.
- Do not mention dasha, transit, dates or future windows unless the user explicitly asks when the relationship changes and authoritative timing evidence is supplied.
"""
        elif career_family in {"profile", "vocation"}:
            career_rules += """
- This is timeless professional profile/vocation analysis. Use D1, D10, Amatyakaraka and Karakamsha where supplied. No dasha, transit or calendar timing.
"""
        elif career_family == "timing":
            career_rules += """
- Use only the dated windows supplied by the calculation. Explain the delivery stage and distinguish activity, visibility, recognition, compensation and joining.
"""
    graph_policy = (
        answer_contract.get("knowledge_graph_policy")
        if isinstance(answer_contract.get("knowledge_graph_policy"), dict)
        else {}
    )
    marriage_pathway_contract = (
        answer_contract.get("marriage_pathway_rules")
        if isinstance(answer_contract.get("marriage_pathway_rules"), dict)
        else graph_policy.get("marriage_pathway_rules")
        if isinstance(graph_policy.get("marriage_pathway_rules"), dict)
        else {}
    )
    spouse_meeting_contract = (
        answer_contract.get("spouse_meeting_rules")
        if isinstance(answer_contract.get("spouse_meeting_rules"), dict)
        else graph_policy.get("spouse_meeting_rules")
        if isinstance(graph_policy.get("spouse_meeting_rules"), dict)
        else {}
    )
    spouse_temperament_contract = (
        answer_contract.get("spouse_temperament_rules")
        if isinstance(answer_contract.get("spouse_temperament_rules"), dict)
        else graph_policy.get("spouse_temperament_rules")
        if isinstance(graph_policy.get("spouse_temperament_rules"), dict)
        else {}
    )
    spouse_appearance_contract = (
        answer_contract.get("spouse_appearance_rules")
        if isinstance(answer_contract.get("spouse_appearance_rules"), dict)
        else graph_policy.get("spouse_appearance_rules")
        if isinstance(graph_policy.get("spouse_appearance_rules"), dict)
        else {}
    )
    spouse_location_contract = (
        answer_contract.get("spouse_location_rules")
        if isinstance(answer_contract.get("spouse_location_rules"), dict)
        else graph_policy.get("spouse_location_rules")
        if isinstance(graph_policy.get("spouse_location_rules"), dict)
        else {}
    )
    marriage_rules = ""
    if str(graph_policy.get("runtime_key") or "") == "love_arranged_marriage":
        past_relation = str(marriage_pathway_contract.get("question_time_relation") or "") == "past"
        marriage_rules = """
- This is a love-led versus family-mediated marriage-pathway comparison, not a general marriage-promise reading and not a marriage-timing reading.
- Start with one direct comparative verdict: love-led stronger, family-mediated stronger, mixed/hybrid, or insufficient comparative evidence. Do not merely say that marriage itself is supported.
- Explain both sides before finishing from `evidence.marriage_pathway_comparison`: love-led evidence uses actual House 5 to House 7 commitment links with D9 confirmation; family-mediated evidence uses actual Houses 2, 7, 9 and 11 family/formalization/continuity links with D9 confirmation. Describe only connections present in `d1_house_evidence`; do not manufacture a link merely because two house rows exist.
- Treat every `d1_house_evidence[*].tone` as immutable. If House 2 is challenging or House 11 is mixed, say exactly that; never describe either as stronger or supportive. Use `natal_lord_links` for real connections and distinguish connection from strength.
- This is static natal evidence. Never use "active", "activated", "activation", "currently", or equivalent timing language for any house. Say natal support, challenge, mixed tone, lord-placement link, occupation, aspect, or D9 confirmation instead.
- A hybrid result is meaningful: for example, personal choice followed by family approval, or a family introduction followed by genuine attachment. Do not force a binary answer when both pathways are supported.
- Do not mention historical-data scarcity, dasha, transit, dates, timing periods, sudden changes, hidden matters, or generic marriage potential unless that exact comparative evidence appears in the brief.
- End with one verification question about whether this matches how the marriage happened. Do not ask whether the user is currently in a relationship or considering an arranged setup.
"""
        if past_relation:
            marriage_rules += """
- The marriage is already in the past. Use past tense throughout: say what was more likely to have happened. Never say "will", "on the cards", or otherwise turn the answer into a future prediction.
"""
    elif str(graph_policy.get("runtime_key") or "") == "spouse_meeting":
        past_relation = str(spouse_meeting_contract.get("question_time_relation") or "") == "past"
        marriage_rules = """
- This asks for a probable spouse-meeting context from static natal evidence. Use only `evidence.spouse_meeting_context`; generic marriage promise, spouse personality and timing evidence cannot answer it.
- Lead with `primary_channel.probable_context`, which comes from the natal placement of the seventh lord. Name it as the strongest probable context, not a recovered historical fact.
- Explain that placement in one compact sentence. Add at most one secondary channel, and only when its own `channel_house_evidence` row supplies a concrete connection. Copy every supplied tone exactly.
- Never mention dasha, transit, activation, a Saturn-driven or Venus-driven period, a date, or a life phase. A planet's natural symbolism is not permission to invent work, duty, comfort, attraction or a shared circle.
- In particular, do not say work/duty unless House 6 or House 10 is the supplied meeting context, and do not say friends/shared circle unless House 11 is concretely supported.
- Keep the derived-chart disclosure clear: this is the native chart's probable context for meeting the spouse, not the spouse's own chart and not certainty about the venue.
- End by asking whether this probable context matches how the meeting actually happened.
"""
        if past_relation:
            marriage_rules += """
- The meeting already happened. Use past tense throughout and do not turn the answer into a future prediction.
"""
    elif str(graph_policy.get("runtime_key") or "") == "spouse_profile":
        marriage_rules = """
- This is a five-layer spouse-temperament synthesis. Use only `evidence.spouse_temperament_context.layers`; a generic `person_profile_axes` sentence or the seventh house alone is insufficient.
- Begin with a clear, nuanced temperament synthesis in ordinary language. Then show how all five layers contribute: (1) seventh house, (2) seventh-lord rashi and nakshatra, (3) Darakaraka rashi and nakshatra, (4) Venus rashi and nakshatra, and (5) D9 confirmation or qualification.
- Give each layer its proper role. The seventh house/lord anchors observable partnership temperament; the seventh-lord nakshatra refines instinctive style; Darakaraka adds the spouse archetype; Venus describes affection and relating style; D9 confirms or modifies the D1 picture.
- Copy every planet, rashi, nakshatra, nakshatra lord, pada, house and tone exactly. Do not substitute generic Mercury, Saturn or Venus folklore for a missing layer.
- No single placement may become the whole personality. Explicitly reconcile reinforcing and conflicting traits so the result sounds like a real person rather than a list of planets.
- This is the native chart's indication of the spouse, not the spouse's own chart. Use probable language and do not diagnose, claim hidden motives, or describe fixed identity with certainty.
- Never mention dasha, transit, activation, dates, current periods or timing. End with one question about which part of this temperament best matches the spouse in real life.
"""
        if not spouse_temperament_contract.get("evidence_complete"):
            marriage_rules += """
- The required five-layer packet is incomplete. Obey the graph limitation and do not improvise a temperament profile from the available subset.
"""
    elif str(graph_policy.get("runtime_key") or "") == "spouse_appearance":
        marriage_rules = """
- This asks specifically how the spouse may look. Use only `evidence.spouse_appearance_context.layers`; do not answer with temperament, reliability, intelligence, compatibility, profession, location or married-life advice.
- Lead with a concise visual summary. Then cover: (1) likely build/stature band, (2) face and visible expression, (3) styling/grooming or visual presence, and (4) the strongest distinctive visible feature or mannerism.
- Synthesize the seventh-house rashi, seventh-lord rashi/nakshatra, Darakaraka rashi/nakshatra, Venus rashi/nakshatra and D9. Reconcile agreement and conflict; never let Mercury, Venus, the seventh house or any one placement become the whole description.
- Copy placement facts exactly. Convert them into bounded visual ranges, not exact measurements or photographic certainty.
- Never infer ethnicity, caste, nationality, disability, medical condition or exact skin colour. Do not sexualize the spouse.
- State once that this is a probable symbolic range derived from the native's chart. Never mention dasha, transit, activation, timing or current periods.
- End by asking whether the user wants the strongest two or three visual markers summarized—not by redirecting them to temperament.
"""
        if not spouse_appearance_contract.get("evidence_complete"):
            marriage_rules += """
- The required appearance packet is incomplete. Obey the graph limitation and do not replace missing physical evidence with personality prose.
"""
    elif str(graph_policy.get("runtime_key") or "") == "spouse_location":
        marriage_rules = """
- This asks whether the spouse is connected with a different city, culture or background. Use only `evidence.spouse_location_context` and copy its calculated `verdict`; do not create a softer or stronger verdict from generic astrology lore.
- Only direct spouse-indicator links to houses 3, 9 or 12, or explicit Rahu linkage, materially support distance/different-background. A direct house-4 link supports local or familiar roots. Movable/fixed rashi is only a weak modifier and cannot decide the answer.
- Begin with one direct plain-language verdict: supported, local/familiar is stronger, mixed, or not specifically shown. Then cite the exact strongest distance and local facts actually present.
- Saturn in Virgo, a nakshatra, Moon/Jupiter proximity, or a Darakaraka's generic symbolism does not by itself mean another city, culture or country.
- Never mention timing, dasha, transit, activation, manifestation, current/future unfolding, temperament, appearance or profession. Never name an unsupplied city, country, caste, religion, ethnicity or nationality.
- D9 may only confirm or qualify the supplied result. End by asking whether the verdict matches the spouse's known background.
"""
        if not spouse_location_contract.get("evidence_complete"):
            marriage_rules += """
- The required location packet is incomplete. Obey the graph limitation and do not invent either a foreign or local-background story.
"""
    if is_chart_fact:
        return f"""
You are Tara in AstroRoshni Instant Chat. The requested chart has already been calculated with placements, dignity, aspects, and house data. Your job is to predict from that chart.

Hard rules:
{_instant_composer_language_rule(language)}
{_instant_relational_voice_contract()}
- Predict lived results in `evidence.chart_facts.charts[X].domain.life_area`. D12 predicts parents/elders/ancestry FROM this D12 packet; D10 predicts career FROM this D10 packet; D9 predicts marriage/dharma FROM this D9 packet; Karkamsa/Swamsa predict soul-direction FROM that chart. Do not write a textbook varga essay, and do not use D1 dasha or transits.
- Use ONLY `evidence.chart_facts`. Every claim must be grounded in lagna/lagna-lord, dignity, occupation, conjunction, or aspect in the packet.
- Placements are hidden evidence. Do not answer as a planet-by-planet placement list.
- Required output shape:
  1. First sentence: a direct prediction for this chart's life area.
  2. How lagna and lagna lord shape that area.
  3. Two strongest supported outcomes.
  4. One main caution.
  5. One compact proof citing only this named chart.
  6. One short follow-up in this same life area, if natural.
- Prefer `support_signals` and `caution_signals`, then `analysis_brief`.
- Do not say the chart lacks detail when `charts` or `analysis_brief` are supplied.
- If `missing_requested_charts` is present, say that chart could not be calculated. Do not invent data.
- No HTML, tables, JSON except required metadata, internal tags, or hidden reasoning.
- Append exactly one final metadata line after the visible answer:
NEXT_ACTION_META: {{"type":"none","title":"","reason":"","confidence":"low","follow_up_questions":[],"source":"instant"}}

USER QUESTION:
{question}

AUTHORITATIVE COMPOSER BRIEF:
{context_json}
""".strip()
    period_forecast_rules = ""
    if answer_mode == "potential_capacity":
        period_forecast_rules = """
- This is a static natal-promise question, not a timing question. Do not mention the current dasha, current transits, active houses, or a calendar window.
- The first sentence must give the exact bounded verdict from `verdict.direction`: supported natal promise, qualified/mixed promise, or not responsibly established from the available evidence. Never upgrade it to "definitely".
- For marriage, judge D1 seventh-house/lord evidence first and D9 confirmation second. Houses 2 or 8 alone cannot establish marriage promise.
- Do not claim sudden marriage, an unconventional route, a foreign/different-background spouse, or volatility merely because Rahu exists in the chart.
- If required D1/D9 capability is missing, say the marriage promise cannot yet be judged responsibly from this packet and ask one precise question; do not substitute current-period activity.
- Explain what is supported and the main condition in ordinary language. End by asking whether the user wants timing or is asking about a specific relationship.
"""
    if answer_mode == "remedy_action":
        composer_remedy_blueprint = (
            (composer_context.get("evidence") or {}).get("remedy_blueprint")
            if isinstance((composer_context.get("evidence") or {}).get("remedy_blueprint"), dict)
            else {}
        )
        single_top_remedy = str(composer_remedy_blueprint.get("selection_mode") or "") == "single_top"
        remedy_delivery_line = (
            "- The user asks which remedy is most relevant. Give exactly one remedy: copy `evidence.remedy_blueprint.top_recommendation` and state its action, frequency, and astrological_reason. Do not add two alternatives."
            if single_top_remedy
            else "- Give exactly three prioritized, concrete remedies from `evidence.remedy_blueprint.ranked_remedies`. For each state the action, frequency, and astrological_reason."
        )
        period_forecast_rules = f"""
- This is an explicit remedy request. Give remedies, not another diagnosis, forecast, favorable date, or lecture about discipline and patience.
- `evidence.remedy_blueprint` is the authoritative remedy plan. If it is absent or empty, say that the chart-specific remedy plan could not be prepared and ask one precise clarification; never improvise generic advice as a remedy.
{remedy_delivery_line}
- Start by naming the remedy itself, not by retelling the marital-conflict diagnosis or current planetary period.
- Prefer constructive house expression first, then the strongest suitable mantra, seva/charity, nakshatra, biological/tree, or behavioral action. Do not dump every available remedy layer.
- Ordinary career advice such as work consistently, improve communication, seek training, avoid shortcuts, or plan carefully is not a remedy unless it is a concrete `house_expression` or `behavioral` action from the supplied blueprint and its chart connection is stated.
- Gemstones must remain optional and suitability-dependent. Preserve `evidence.caution`; avoid fear, guarantees, expensive prescriptions, and excessive ritual.
- Do not mention current dasha, sub-period, transit or activation. Do not give event dates or claim that a remedy guarantees an outcome.
"""
    elif is_period_topic_forecast:
        period_forecast_rules = """
- This is a period-topic forecast, not a generic topic reading.
- Sentence 1: answer how the requested life area is likely to go overall, using plain real-life language.
- Then narrate the supplied chronological phases. Combine adjacent phases only when their manifestation candidates are materially the same; otherwise preserve their date boundary.
- For each material phase, say what changes in lived experience: for example workload, role/visibility, income, clients, gains, conflict, or responsibility. A phase sentence that only names dates, planets, dashas, or houses is invalid.
- Treat manifestation candidates as priority ordered. Lead each phase with its first candidate; use later candidates as consequences or secondary themes.
- Keep the requested topic dominant. For a career question, lead with work, role, responsibility, clients, recognition, gains, or professional direction. Mention income only as a career consequence; never turn a career forecast into a wealth forecast merely because house 2 is active.
- Clearly distinguish (a) the main opportunity, (b) the main pressure or limitation, and (c) the strongest peak inside the year. Do not call the peak the only meaningful period.
- Do not use empty phrases such as "steady development", "mixed period", "building resources", or "potential gains" unless the same sentence says the concrete supported manifestation and its phase.
- Do not finish with a generic house-number proof such as "the second house is emphasized." For this forecast shape, omit astrological terminology unless one compact mechanism genuinely clarifies why two phases differ.
"""
    if is_daily_forecast:
        period_forecast_rules = """
- This is an exact-day forecast, not a shortened annual, monthly, or general dasha reading.
- Decide the day in this order: KP daily materialisation; transiting Moon, current nakshatra and Tara Bala; Prana and Sookshma triggers; Pratyantardasha as the day frame. Mahadasha and Antardasha are background permission only.
- Never decide or describe today mainly from MD/AD/PD. Do not say the day is slow, heavy, favorable, difficult, career-active, or relationship-active merely because those three levels or slow transits suggest it.
- Sentence 1 must give a plain overall outlook for the target day. Then give one or two ranked concrete manifestations, the best use/opportunity, the main caution, and one practical action.
- Use KP to say which event areas are most likely to materialize. Use Moon/nakshatra/Tara Bala to describe the day's flow or ease. Use Sookshma and Prana to explain the immediate trigger. Mention MD/AD only in one short background clause if genuinely useful.
- Do not dump all five dasha levels, houses, scores, school verdicts, or Panchanga fields. Give one compact understandable astrology reason after the practical answer.
- If any mandatory daily evidence is missing, ask one precise clarification or state that a responsible exact-day judgment is not available; never substitute a generic period forecast.
"""
    constitutional_health_rules = ""
    if is_constitutional_health:
        constitutional_health_rules = """
- This is a natal constitutional-susceptibility reading. It is not a current-period or timing forecast.
- Use this exact visible structure: (1) name the supplied ranked anatomical regions, (2) explain each only from its own natal row, (3) give ordinary preventive guidance, and (4) ask one natural follow-up.
- Do not mention or imply the current period, Mahadasha, Antardasha, Pratyantardasha, dasha, transit, currently active houses, or any calendar window. Those subjects are forbidden for this answer even if you remember them from general astrology.
- Do not say a vulnerability is active now. Timing requires a separate time-bound question and explicit timing evidence.
"""
    elif is_time_bound_health:
        constitutional_health_rules = """
- This is a time-bound health forecast. Obey `health_rules.period_forecast_rule` as a hard contract.
- Stay strictly inside `health_rules.requested_horizon`; "this year" must never extend into the following year.
- Begin by naming the strongest dated health watch period and the possible calculated health problem/body region in plain language. Then compare every materially distinct supplied phase chronologically.
- Keep three layers separate: standing natal vulnerability, dated dasha activation, and dated transit confirmation. A natal vulnerability alone is not an active health forecast. Dasha support without transit confirmation is background vigilance, not likely manifestation.
- Treat `period_topic_forecast.chronological_phases[*].health_forecast` as authoritative. For each `strongest_watch_period` or `elevated_watch_period`, state its exact dates, its allowed possible body regions or condition patterns, the activated health houses, and whether a dated transit confirms it. Briefly identify quieter phases as lower concern.
- A paying user is asking when health trouble is more plausible and what form it could take. Do not evade that question with "generally stable", "maintain a routine", "manage vitality", "be consistent", or other generic wellness language unless the calculated phase record truly contains no elevated period; even then, explicitly say which calculations were checked and that no convergence was found.
- Name only body regions and condition susceptibilities allowed by `health_rules`. Never invent sleep, digestion, diet, posture, fitness, a symptom, or another body system.
- Gandanta is only a natal modifier and must never be the principal reason that a dated health phase is active.
- Never recommend or reject a medical treatment and never advise avoiding experimental or conventional treatment. Use restrained preventive language and qualified medical care where appropriate.
- State protective factors when supplied. Never predict illness, diagnosis, recovery, hospitalization, surgery, or an acute event as certain.
"""
    speech_rules = ""
    if speech_mode:
        speech_rules = f"""
- Write 60-100 words for listening. Use short sentences and no bullets or markdown.
- Do not greet or introduce Tara; the app already did that.
- After the answer emit exactly:
{_FOLLOW_UPS_START}
["Spoken follow-up 1?", "Spoken follow-up 2?"]
{_FOLLOW_UPS_END}
- Use zero to three short follow-ups and valid JSON inside the markers.
"""
    else:
        word_guidance = str(answer_contract.get("composer_word_target") or "Usually 90-180 words; expand when necessary.")
        prohibited_additions = (
            "feedback requests, mode suggestions, or sales copy"
            if answer_mode == "remedy_action"
            else "remedies, feedback requests, mode suggestions, or sales copy"
        )
        speech_rules = f"""
- Length guidance: {word_guidance} Do not omit a material phase, evidence limitation, or direct answer merely to stay short.
- End the visible answer with exactly one natural, topic-specific question about the user's real concern or goal.
- Do not recommend a deeper reading and do not add {prohibited_additions} beyond what this answer mode explicitly requires.
- Append exactly one final metadata line after the visible answer:
NEXT_ACTION_META: {{"type":"none","title":"","reason":"","confidence":"low","follow_up_questions":[],"source":"instant"}}
"""
    return f"""
You are Tara in AstroRoshni Instant Chat. The astrology has already been calculated, normalized, and fused. Your only job is to turn the supplied verdict into a useful conversational answer. Do not recalculate or reinterpret raw astrology.

Hard rules:
{_instant_composer_language_rule(language)}
{_instant_relational_voice_contract()}
- Answer the real-life question in the first sentence. Never open with planets, dashas, dates, evidence IDs, or house numbers.
- Treat `verdict` and `answer_contract` as authoritative. Use `evidence` only to explain them; never invent a stronger conclusion.
- If `query_plan.confirmed_life_event` is present, its date is a fact supplied by the user. Acknowledge it as confirmed, do not present competing probable windows, and never claim astrology discovered or proved that date. Use calculated exact-day evidence only to explain what was active around the confirmed event.
- Fill `answer_blueprint` in order. It contains semantic answer slots, not prose to repeat. The first slot must become a concrete answer to what the user asked.
- For career, follow `answer_contract.career_contract` only. For non-career event/timing questions, reason internally from natal promise to dasha delivery to dated transit confirmation to real-life outcome.
- Translate supported areas into concrete life language. Never leave the user to decode house numbers or a list of dasha phases.
- When `query_plan.forecast_shape` is `period_topic_forecast`, the answer format is mandatory: (1) a direct overall verdict, (2) the chronological progression across the full requested period, (3) the strongest opportunity and main pressure/caution, and (4) one practical takeaway. Use `evidence.period_topic_forecast.chronological_phases`; do not collapse multiple phases into one generic year summary.
- For a broad period, give two or three supported real-life manifestations. Describe what is likely to happen or require attention, not merely which astrological sectors are active.
- A dated peak is only the most concentrated part of its containing phase. Never present the final or strongest peak as though nothing meaningful happens during the rest of the requested period.
- A period is "highly active" only when it appears in an allowed/peak window. Copy supplied dates exactly. If no peak exists, call it background activity, not a peak.
- Include at least one short, understandable astrological reason in every completed answer so it is visibly chart-based. Add more only when needed to explain materially different phases or evidence.
- `evidence.special_natal_factors` contains only calculated Gandanta, Yogi, Avayogi, Dagdha Rashi, or Tithi Shunya factors connected to the relevant natal houses. If present, use a factor when it materially supports or qualifies the verdict; describe its practical effect in plain language. Do not list every factor, treat a caution as an absolute denial, or invent a special factor that is absent.
- If evidence is missing, state the limited conclusion plainly. Never fill gaps with generic planet folklore.
- Preserve all cautions and limitations. For health, describe only allowed susceptibilities, never diagnosis or certainty.
- For a constitutional health question, name every ranked zone in `health_rules.allowed_zone_evidence` in exact order; `required_zone_count` is mandatory, not a maximum. Do not reorder or omit the fourth region to shorten the answer. Explain each zone only from its own row. The composer brief intentionally contains no current timing: never add a dasha, transit, or "currently active" statement from general astrology knowledge.
- For a derived person, keep ownership explicit: these are the native chart's indications for that person, not that person's own chart or dasha.
- An MD-AD-PD sequence is a dasha chain. MD is the major period, AD the sub-period, and PD the sub-sub-period; never rename a level.
- No HTML, tables, JSON except required metadata, internal tags, evidence IDs, decorative headings, disclaimers, or hidden reasoning.
{period_forecast_rules}
{constitutional_health_rules}
{career_rules}
{marriage_rules}
{speech_rules}

USER QUESTION:
{question}

AUTHORITATIVE COMPOSER BRIEF:
{context_json}
""".strip()


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
        "natal_promise": normalized.get("natal_promise"),
        "transit_activation_timeline": normalized.get("transit_activation_timeline"),
        "divisional_specifics": list(normalized.get("divisional_specifics") or [])[:3],
        "career_foundation": normalized.get("career_foundation"),
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
        "health_body_area": normalized.get("health_body_area"),
        "option_comparison": normalized.get("option_comparison"),
    }
    if str(intent_summary.get("answer_mode") or "") == "remedy_action":
        # The speech/legacy compact path must retain the same authoritative
        # remedy plan as the verdict-first composer.  Do not make Listen turn
        # a real remedy answer back into generic chart advice.
        for key in (
            "remedy_blueprint",
            "question_focus",
            "special_points",
            "remedy_sections",
            "follow_up_prompts",
            "caution",
        ):
            compact_normalized[key] = normalized.get(key)
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
        "instant_v2_answer_contract": instant_context.get("instant_v2_answer_contract"),
        "context_profile": "instant_compact_v2",
    }


def _build_instant_prompt(
    question: str,
    instant_context: Dict[str, Any],
    language: str,
    *,
    speech_mode: bool = False,
) -> str:
    if instant_context.get("context_profile") == "instant_composer_v3":
        return _build_instant_composer_prompt_v3(
            question,
            instant_context,
            language,
            speech_mode=speech_mode,
        )
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
    if answer_mode != "remedy_action":
        analysis_block = (
            analysis_block
            + "\nCRITICAL: "
            + NO_INLINE_REMEDY_PLAN_RULE
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
- Be conversational and natural, not report-like. Use everyday language people actually use in normal conversation. Prefer short familiar words, contractions where natural, and direct sentences over formal or academic wording.
- Match the user's language, script, and level of formality. When the user mixes languages naturally, you may mirror that mix instead of forcing textbook language.
- Do not output HTML, JSON, markdown tables, glossary blocks, follow-up widgets, FAQ_META, or internal tags.
- Do not mention hidden reasoning, token limits, or model limitations.
- Use plain astrological language that normal users can understand.
- If the question is complex, still give the strongest useful answer supported by the available evidence. Never end by recommending a "deeper reading", "more precise breakdown", "full synthesis", or another report.
- End the visible answer with exactly one short, natural question that continues the same real-life conversation. Make it specific to what was just discussed and invite the user to reveal their concern, goal, or relevant situation. For example, after a career reading: "Is something at work worrying you right now, or are you mainly looking for growth?" Adapt the question to the topic and conversation; never copy this example mechanically.
- The closing question must sound like an astrologer listening to the user, not a sales CTA. Do not ask whether they want more details, a deeper analysis, or another reading.
- Create a gentle sense that the current situation is worth paying attention to. If the evidence shows a real active pressure, opportunity, transition, or upcoming shift, say so plainly and connect it to the user's life.
- Build curiosity for the next conversational turn by briefly surfacing one adjacent, genuinely relevant concern or opportunity, then let the closing question invite the user to talk about it.
- Never manufacture FOMO. Do not invent urgency, scarcity, deadlines, danger, certainty, or hidden bad news. Do not use fear, threaten loss, exaggerate weak evidence, or hold back the requested answer merely to make the user continue chatting.
- Never invent missing chart data."""
    )
    length_rule = (
        "- Keep it concise for listening: 60 to 100 words, then the follow-up block."
        if speech_mode
        else "- Keep it conversational and proportionate to the question. Do not enforce a fixed 120-word ceiling; end with one natural question."
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
    if answer_mode == "remedy_action":
        next_action_tail = f"""

At the very end of the answer, append exactly one line:
NEXT_ACTION_META: {{"type":"none","title":"","reason":"","confidence":"low","follow_up_questions":[],"source":"instant"}}
{NEXT_ACTION_NONE_IN_REMEDY_MODE}
Keep it short and valid JSON.
"""
    else:
        next_action_tail = f"""

At the very end of the answer, append exactly one line in this format:
NEXT_ACTION_META: {{"type":"<remedy|diagnosis|timing|clarification|comparison|chart_explanation|none>","title":"<FOMO headline>","reason":"<FOMO subline>","confidence":"<high|medium|low>","follow_up_questions":["<button label>"],"source":"instant"}}
Always include this line.
- If the reading discusses health problems, stress, blocks, afflictions, or active chart pressure, you MUST set type="remedy" (main answer must NOT contain inline remedies — the card opens remedy mode).
- If no follow-up is needed, set type to "none" and follow_up_questions to an empty array.
{REMEDY_CARD_FOMO_COPY_RULES}
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
{_instant_composer_language_rule(language)}
{_instant_relational_voice_contract()}
{length_rule}
- Use daily-use language, not consultant language. Prefer phrases such as "right now", "this phase", "work pressure", "money matters", or "relationship tension" over abstract phrases such as "current energetic configuration", "professional materialization", or "relational dynamics".
- Keep astrology credible but easy to follow: give the result in normal language first, then one compact chart reason. Do not make the user decode jargon.
- Natal chart facts (dignity, avastha including Mrit, Mrityu Bhaga, natal combustion) are birth properties — say "in the natal chart" / "by birth", never "currently Mrit/debilitated" unless you mean a transit planet's sky position.
- If the user is only deferring or declining to ask (for example: "nothing for now", "no thanks", "not yet", "I'm good"), reply in one or two warm sentences. Do not analyze the chart, dashas, houses, or transits, and do not say you will look something up in the chart — there is no question to answer yet.
- Lead with the direct answer in the first 1 to 2 sentences when there is a real astrological question.
- The astrology context is evidence, not the answer. Never respond mainly with dasha date ranges, planet placements, activated-house numbers, or a catalogue of chart factors.
- For broad questions such as "How is my career this year?", the first sentence must give a clear real-world verdict such as supportive, mixed-but-improving, demanding, or change-oriented. Then state what that means in life: workload, recognition, income, role change, interviews, clients, authority, conflict, or stability—but only when supported by the supplied evidence.
- Translate house themes into ordinary outcomes. Do not say only "houses 2, 6 and 11 are active"; say what the supplied themes mean for the user's work and money. House numbers may appear once as a short reason, never as the substance of the reply.
- When the evidence supports timing phases, describe how the lived experience changes between phases. Do not merely list three dasha chains and their dates.
- Unless the user asks "why" or requests technical astrology, use no more than one sentence of astrological proof. The rest must answer the life question.
- If `named_dasha_lookup.matches` is present, use its `authoritative_fact` for the requested planet dasha start/end date. Do not infer a different date from transits, event windows, or current dasha summaries.
- If `normalized_evidence.event_timing_verdict.answer_event_label` is present, name that event plainly in the first sentence. Avoid vague placeholders like "this event" or "these matters" as the only topic name.
- In speech mode, sound like a live guide, not a report. Prefer openers like "For promotion, I would look most closely at..." or "For having a child, the cleaner window is..." Avoid stiff phrases such as "the astrological indicators suggest", "materialization window", "these matters", "this event", and "planetary influences".
- In speech mode, do not repeat the same timing noun in every sentence. After naming the window once, use natural phrasing like "that phase", "that stretch", or "then" only when the reference is clear.
- In speech mode, keep technical proof compact: name the dasha chain and 1 concrete reason from `allowed_house_themes` or `why`; do not narrate every activated house if it makes the answer sound mechanical.
- If `normalized_evidence.divisional_specifics` has concrete D7, D9, D10, or Karkamsa evidence, mention one relevant chart code naturally. This is good credibility in speech, but keep it to one compact sentence unless the user asks for technical detail.
- Mention the strongest current dasha or transit factor only when it genuinely helps clarity for this answer mode.
- Start from `normalized_evidence.primary_drivers` and only then bring in `secondary_modifiers`.
- Use `normalized_evidence.answer_mode_contract.answer_skeleton` as the structural backbone of the response.
- If `instant_v2_answer_contract` is present, treat its query plan, verdict, answer order, evidence IDs, and forbidden-claim list as a strict answer contract. Do not add a factual or timing claim merely because it sounds plausible.
- When `answer_contract.knowledge_graph_policy.live` is true, that compiled graph route is authoritative for this answer. Follow its required output sections, decision rules, evidence policy and guardrails. Never use a factor listed in `default_exclusions`. If `missing_required_factors` is non-empty, state only what the available evidence supports and do not manufacture the missing conclusion. Do not switch to a different question type or answer mode.
- For career questions, obey `instant_v2_answer_contract.answer_spec.career_rules` literally. For job-change, resignation, or job-security decisions, give a direct stay/prepare/transition recommendation from the supplied decision matrices. Compare continuity (H6+H10), change (H3+H10), separation (H10+H12), and landing support (H2+H6+H10+H11). H8 means disruption or restructuring only; it is never permission to resign. Do not substitute career fit, Amatyakaraka, Karakamsha, suitable fields, or personality for this decision evidence. If landing support is absent, advise preparation rather than resignation unless the user reports a real-world safety, health, or ethical emergency.
- `instant_v2_answer_contract.evidence_records` is authoritative when any legacy summary conflicts with it. Never change the MD/AD/PD planets, active houses, or dates stated in those records.
- Obey `instant_v2_answer_contract.answer_spec.dasha_level_terms`: a displayed MD-AD-PD chain contains three separate levels. Never call the whole chain a Mahadasha/Antardasha or call its PD planet the sub-period lord.
- Obey `instant_v2_answer_contract.answer_spec.composer_word_target` as a hard output limit. Count conservatively and finish under 120 visible words.
- If the verdict direction is `insufficient_option_evidence`, explicitly say the chart does not reliably distinguish the options. Do not use phrases such as "leans toward", "favors", "more likely", or any equivalent winner. Give only the shared supported context and end with one question about which option is appearing in real life.
- Obey `instant_v2_answer_contract.answer_spec.limitation_instruction` literally. Missing health-body-area evidence forbids naming an organ, body system, symptom, or recovery window.
- For health answers, obey `instant_v2_answer_contract.answer_spec.health_rules` literally. Name only its `allowed_zone_names`; frame them as astrological susceptibilities, not diagnoses. For each named zone, use only the reasons and mechanisms inside that same zone's `allowed_zone_evidence`. Never borrow a mechanism from another zone or invent a connecting body system. If the user asks for general vulnerabilities, include every retained standing natal susceptibility in exact ranked order (the mandatory count is `required_zone_count`), explain one concrete chart reason for each, then give prevention-oriented guidance; do not turn it into a current-period forecast. If it says there is no ranked risk window inside the requested horizon, do not describe that horizon as heightened, dangerous, acute, or high-risk. Do not name a current MD/AD/PD chain unless every level is explicitly present in current-dasha evidence.
- When the comparison verdict is `close_call`, do not call either option more supported, favored, stronger, or more likely—even by "slightly". Compare their distinct windows and mechanisms, then ask which is materially emerging.
- Obey `instant_v2_answer_contract.answer_spec.timing_sequence` literally. For a current-problem-plus-improvement question, explain the supplied current cause, give the earliest materially better window first, and identify a later peak only as a later strengthening—not as the first relief.
- Obey `instant_v2_answer_contract.answer_spec.current_cause_rules` literally. It is an allow-list: never add a natal conjunction, placement, lordship, or generic planet effect that is absent from it.
- For event predictions, mention every distinct `event_rules.required_material_windows` entry in chronological order when supplied. Apply `event_rules.dasha_level_terms` exactly: MD is major period, AD is sub-period, and PD is sub-sub-period. Never call a PD planet the sub-period lord.
- For retrospective marriage timing, each ranked row is a broad MD-AD phase. State that broad phase first, then explicitly state the start/end and planet from its `strongest_pd_window`, and then give one or two supplied `probable_peak_windows`. Never attach the PD planet label to the entire MD-AD range, and never omit the PD dates when `strongest_pd_window` is present.
- Obey `instant_v2_answer_contract.answer_spec.comparison_rules` literally and keep its required conclusion logically consistent in every sentence.
- For comparison answers, keep each `evidence.option_comparison.options[].best_window` attached to that same option. Never explain the favored option with the other option's window, dasha chain, score, or `why`.
- If `query_plan.time_scope.horizon_end` is present, never mention or imply a date after it, even if a legacy evidence block contains a later date. The v2 filtered ranked windows win.
- When explaining a dated future window, use only the dasha chain attached to that exact window. Never use `current_timing` or the present MD/AD/PD chain as the astrological reason for a later window.
- Obey `instant_v2_answer_contract.answer_spec.target_framing`. For a spouse, child, parent, or other derived subject without that person's own birth data, say "your chart's indications for your wife/child/etc." Never call the native's dasha "her dasha" or "his dasha".
- If `instant_v2_answer_contract.verdict.missing_required_capabilities` is non-empty, state the supported directional evidence but do not invent the missing specificity. For a comparison without option-specific evidence, do not pick a winner; say what the chart supports and ask the one real-life distinction needed next.
- For future time-bound questions, use only windows in `instant_v2_answer_contract.verdict` or `normalized_evidence.event_timing_verdict`; never restart a future window before the context's as-of date. For a retrospective query, use only ranked historical windows, keep every date in the past, and call them probable periods rather than the actual event date.
- For health answers, translate difficult 8th/12th-house or hidden-pressure evidence into restrained self-care language such as rest, routine, observation, and checking persistent symptoms with a qualified professional. Do not claim recovery complications, isolation, acute danger, or a medical outcome unless that exact conclusion is explicit in the adjudicated health evidence.
- For event-prediction answers, obey `normalized_evidence.event_timing_verdict.claim_contract` as a hard evidence gate. A focus house is only a possible topic house; it is not active in a timing window unless that same window lists it in `activated_focus_houses` or names it in `why`.
- For event-prediction answers, never translate a raw line like "Jupiter rules focus house(s) [9]" into "Jupiter rules the progeny house" or another named domain house unless that exact domain house number is explicitly active in the same window. Safer wording is "Jupiter activates an event-relevant support house" or the exact house theme from `allowed_house_themes`.
- For event-prediction answers, do not say "career house", "marriage house", "progeny house", "health house", or similar named-house claims unless the corresponding house number is active in that window. Use the listed `allowed_house_themes` instead.
- If the question is about career, relationship, wealth, or health, use the corresponding topic signals and divisional specifics from `normalized_evidence` or `instant_parashari` to keep the answer precise.
- If the question is about a specific facet inside a broader area, answer that facet directly from the house activation and dasha logic instead of widening the answer into a whole life summary.
- If `intent_summary.target_subject.key` is not `self`, treat `target_chart_context` as the primary chart frame for that person instead of reading only from the native's direct Lagna context.
- No decorative headers unless absolutely needed.
- In non-speech Instant Chat, the final visible sentence before NEXT_ACTION_META must be the one natural conversational question required above. Do not place any recommendation for a deeper/full reading before it.
- In non-speech Instant Chat, create grounded conversational pull: identify one evidence-backed thing that is active now or changing next, but answer the user's question fully before inviting the next turn. Never use fake scarcity or fear-based FOMO.
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
    latest_user_question: Optional[str] = None,
    speech_mode: bool = False,
    stream_callback: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    intent = apply_timeline_intent_guard(intent)
    requested_app_language = str(language or "english").strip().lower() or "english"
    language = _instant_response_language(
        latest_user_question or question,
        intent,
        requested_app_language,
    )
    medical_triage = _instant_medical_triage_decision(question, intent)
    if medical_triage:
        return _instant_medical_triage_response(
            language,
            speech_mode=speech_mode,
            urgency=str(medical_triage.get("urgency") or "emergency"),
            localized_message=str(medical_triage.get("user_message") or ""),
            source=str(medical_triage.get("source") or "safety_gate"),
        )
    timeline_result = build_selection_response(birth_data=birth_data, intent=intent)
    if timeline_result:
        return _marriage_timeline_selection_response(
            timeline_result,
            language,
            speech_mode=speech_mode,
        )
    if _is_conversational_non_question(question):
        return _conversational_ack_response(language, speech_mode=speech_mode)

    pipeline_started = time.perf_counter()
    instant_stages: List[Dict[str, Any]] = []
    stage_timings_ms: Dict[str, float] = {}

    def _finish_local_stage(stage: str, started: float) -> None:
        elapsed_s = max(0.0, time.perf_counter() - started)
        stage_timings_ms[stage] = round(elapsed_s * 1000.0, 1)
        instant_stages.append(
            _build_instant_usage_stage(stage, "local", 0, 0, {}, True, elapsed_s)
        )

    mode_started = time.perf_counter()
    mode_selection = _mode_selection_from_intent(intent, question)
    structured_parts = (
        ((intent or {}).get("evidence_plan") or {}).get("question_parts")
        if isinstance((intent or {}).get("evidence_plan"), dict)
        else []
    )
    if isinstance(structured_parts, list) and len(structured_parts) > 1:
        # The multilingual intent LLM has already established that this is a
        # compound request. Ask the compact semantic router to write the one-
        # question clarification in the user's language; calculators must not
        # run for either part yet.
        mode_selection = None
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
    _finish_local_stage("answer_mode", mode_started)
    route_action = str((mode_selection or {}).get("route_action") or "answer").strip().lower()
    if route_action in {"clarify", "handoff"}:
        return _instant_route_response(
            body=str((mode_selection or {}).get("user_message") or ""),
            answer_mode=str((mode_selection or {}).get("answer_mode") or "topic_reading"),
            route_action=route_action,
            language=language,
            speech_mode=speech_mode,
        )
    if bool((mode_selection or {}).get("needs_year_clarification")):
        return _instant_lifetime_event_year_clarification_response(language, speech_mode=speech_mode)
    answer_mode = _apply_llm_chart_fact_mode_guard(
        _clamp_remedy_answer_mode(
            str((mode_selection or {}).get("answer_mode") or "topic_reading"),
            intent,
            question,
        ),
        intent,
    )
    # Preserve an already structured comparison.  The secondary mode router
    # may see future-tense wording and collapse a two-option decision into a
    # single event prediction, which discards one side of the evidence plan.
    # The primary router's explicit comparison contract is stronger evidence
    # than that later generic classification.
    if str((intent or {}).get("answer_mode") or "").strip() == "comparison_choice":
        answer_mode = "comparison_choice"
    routing_decision = {
        "selected_mode": str((mode_selection or {}).get("raw_answer_mode") or answer_mode),
        "final_mode": answer_mode,
        "source": str((mode_selection or {}).get("router_source") or "unknown"),
        "confidence": str((mode_selection or {}).get("router_confidence") or "unknown"),
        "reason": str((mode_selection or {}).get("router_reason") or ""),
        "degraded": bool((mode_selection or {}).get("router_degraded")),
        "intent_answer_mode": str((intent or {}).get("answer_mode") or ""),
        "intent_mode": str((intent or {}).get("mode") or ""),
        "intent_category": str((intent or {}).get("category") or ""),
        "post_selection_changed": str((mode_selection or {}).get("raw_answer_mode") or answer_mode) != answer_mode,
        "response_language": language,
        "app_language_fallback": requested_app_language,
    }
    target_subject = (mode_selection or {}).get("target_subject") if isinstance(mode_selection, dict) else None
    if (
        answer_mode == "remedy_action"
        and str((intent or {}).get("category") or "").lower() in {"marriage", "relationship", "love"}
        and str((target_subject or {}).get("key") or "").lower() in {"spouse", "wife", "husband", "partner"}
        and not re.search(r"\b(?:for|help|support)\s+(?:my\s+)?(?:spouse|wife|husband|partner)\b", str(question or ""), re.IGNORECASE)
    ):
        target_subject = {
            "key": "self", "label": "self", "base_house": 1,
            "confidence": "high", "source": "marriage_remedy_native_frame",
        }
    calculations_started = time.perf_counter()
    instant_context = _build_instant_context(
        birth_data=birth_data,
        question=question,
        intent=intent,
        history=history,
        answer_mode_override=answer_mode,
        target_subject_override=target_subject,
    )
    instant_v2_packet = None
    instant_v2_packet_error = None
    if _env_flag("INSTANT_CHAT_V2_ENABLED", True):
        try:
            instant_v2_packet = build_instant_v2_packet(
                question=question,
                intent=intent,
                answer_mode=answer_mode,
                target_subject=target_subject,
                language=language,
                instant_context=instant_context,
            )
            if isinstance(instant_v2_packet.get("query_plan"), dict):
                instant_v2_packet["query_plan"]["routing_decision"] = routing_decision
            instant_v2_packet["routing_decision"] = routing_decision
            # Resolve the compiled domain route before the composer context is
            # built. Career, Health and Marriage graph rules are authoritative
            # for this generation rather than post-answer shadow diagnostics.
            instant_v2_packet = apply_live_graph_policy(
                instant_v2_packet,
                intent=intent,
                context=instant_context,
            )
            # The composer receives the compact contract, not the full audit
            # ledger. The full packet is returned for test inspection.
            instant_context["instant_v2_answer_contract"] = {
                "query_plan": instant_v2_packet.get("query_plan"),
                "verdict": instant_v2_packet.get("verdict"),
                "answer_spec": instant_v2_packet.get("answer_spec"),
            }
        except Exception as exc:
            instant_v2_packet_error = f"{type(exc).__name__}: {exc}"
            logger.exception("instant_v2_packet_build_failed")
    _finish_local_stage("calculations_and_evidence", calculations_started)
    prompt_context = instant_context
    if instant_v2_packet:
        prompt_context = _build_instant_composer_context(instant_context, instant_v2_packet)
        fallback_language = str(language or "").strip().lower()
        if fallback_language:
            prompt_context["app_language_fallback"] = fallback_language
        full_chars = _json_size(instant_context)
        compact_chars = _json_size(prompt_context)
        reduction_pct = round(((full_chars - compact_chars) / full_chars) * 100.0, 1) if full_chars else 0.0
        logger.info(
            "INSTANT_PERF context_compact profile=instant_composer_v3 full_chars=%s compact_chars=%s reduction_pct=%s",
            full_chars,
            compact_chars,
            reduction_pct,
        )
    elif speech_mode and _env_flag("SPEECH_COMPACT_CONTEXT", True):
        compact_context = _compact_context_for_speech(instant_context)
        full_chars = _json_size(instant_context)
        compact_chars = _json_size(compact_context)
        reduction_pct = round(((full_chars - compact_chars) / full_chars) * 100.0, 1) if full_chars else 0.0
        logger.info(
            "INSTANT_PERF context_compact profile=instant_compact_v2 full_chars=%s compact_chars=%s reduction_pct=%s",
            full_chars,
            compact_chars,
            reduction_pct,
        )
        prompt_context = compact_context
    elif isinstance(prompt_context, dict) and prompt_context.get("_user_evidence"):
        # Defensive path for a disabled/failed v2 packet: display-only audit
        # evidence must never leak into the generation prompt.
        prompt_context = dict(prompt_context)
        prompt_context.pop("_user_evidence", None)
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
    try:
        prompt_budget = max(8000, int(os.getenv("INSTANT_CHAT_PROMPT_CHAR_BUDGET", "15000") or 15000))
    except (TypeError, ValueError):
        prompt_budget = 15000
    prompt_started = time.perf_counter()
    authoritative_prompt_context = prompt_context
    prompt = _build_instant_prompt(question, prompt_context, language, speech_mode=speech_mode)
    if len(prompt) > prompt_budget:
        # Fit against the complete prompt, not just the JSON brief.  The fixed
        # composer instructions are sizeable, so a 9.5k context can otherwise
        # produce a 20k+ request.  Re-run semantic compaction while retaining
        # the verdict and answer-bearing domain contracts.
        fixed_chars = max(0, len(prompt) - _json_size(prompt_context))
        context_budget = max(3000, prompt_budget - fixed_chars - 250)
        prompt_context = _fit_composer_brief(prompt_context, target_chars=context_budget)
        prompt = _build_instant_prompt(question, prompt_context, language, speech_mode=speech_mode)
    if len(prompt) > prompt_budget and not speech_mode:
        # Some domain combinations make the fixed full instruction block alone
        # larger than the configured envelope.  Use the concise equivalent and
        # reserve the remaining space for adjudicated evidence; never truncate
        # JSON or silently exceed the declared budget.
        compact_fixed = len(_build_budgeted_instant_prompt(question, {}, language))
        compact_budget = max(2500, prompt_budget - compact_fixed - 250)
        prompt_context = _fit_composer_brief(prompt_context, target_chars=compact_budget)
        prompt = _build_budgeted_instant_prompt(question, prompt_context, language)
        if len(prompt) > prompt_budget:
            retrospective_budget_context = _build_retrospective_budget_context(
                authoritative_prompt_context
            )
            prompt_context = (
                retrospective_budget_context
                if retrospective_budget_context
                else _limit_composer_value(
                    prompt_context, max_depth=3, list_limit=3, string_limit=120
                )
            )
            prompt = _build_budgeted_instant_prompt(question, prompt_context, language)
        if len(prompt) > prompt_budget:
            prompt_context = {
                key: _limit_composer_value(
                    prompt_context.get(key), max_depth=2, list_limit=2, string_limit=100
                )
                for key in ("query_plan", "verdict", "evidence", "answer_contract")
                if isinstance(prompt_context, dict) and prompt_context.get(key) not in (None, {}, [])
            }
            prompt = _build_budgeted_instant_prompt(question, prompt_context, language)
    if len(prompt) > prompt_budget:
        logger.warning(
            "INSTANT_PERF prompt_budget_exceeded prompt_chars=%s budget_chars=%s profile=%s",
            len(prompt),
            prompt_budget,
            (prompt_context or {}).get("context_profile"),
        )
    _finish_local_stage("prompt_build", prompt_started)
    model_name = get_instant_chat_model()
    instant_provider = get_instant_chat_llm_provider()
    if instant_v2_packet:
        instant_v2_packet["composer_brief"] = prompt_context
        instant_v2_packet["composer_metrics"] = {
            "context_chars": _json_size(prompt_context),
            "section_chars": {
                str(key): _json_size(value)
                for key, value in (prompt_context or {}).items()
            },
            "prompt_chars": len(prompt),
            "prompt_budget_chars": prompt_budget,
            "within_prompt_budget": len(prompt) <= prompt_budget,
            "generation_calls": 1,
            "response_model": model_name,
        }
    answer_request_id = _log_instant_llm_request(
        stage="instant_answer",
        model_name=model_name,
        prompt=prompt,
        context=prompt_context,
        answer_mode=answer_mode,
        speech_mode=speech_mode,
        compacted=bool(prompt_context is not instant_context),
    )

    answer_timeout_s = _instant_timeout_seconds(
        "INSTANT_CHAT_ANSWER_TIMEOUT_SECONDS",
        30.0,
        maximum=45.0,
    )
    thinking_level = _instant_thinking_level(model_name)
    logger.info(
        "INSTANT_PERF latency_policy model=%s thinking_level=%s deepseek_thinking=%s timeout_s=%.1f transport=%s",
        model_name,
        thinking_level or "model_default",
        "disabled" if instant_provider == CHAT_LLM_DEEPSEEK else "not_applicable",
        answer_timeout_s,
        "deepseek_chat_completions" if instant_provider == CHAT_LLM_DEEPSEEK else "genai_rest",
    )
    response_health_rules = _resolve_constitutional_health_rules(
        prompt_context,
        instant_v2_packet,
        instant_context,
    )
    constitutional_health_rows = (
        _constitutional_health_required_rows(response_health_rules)
        if response_health_rules and not response_health_rules.get("is_time_bound_question")
        else []
    )
    if response_health_rules:
        logger.info(
            "INSTANT_HEALTH_FACT_GATE active rows=%s sources=%s",
            len(constitutional_health_rows),
            json.dumps(constitutional_health_rows, ensure_ascii=False, default=str),
        )
    # Constitutional health claims are buffered until their immutable chart
    # facts pass validation.  Streaming an invented placement and correcting it
    # afterwards is worse than showing this one answer shape atomically.
    generation_stream_callback = None if constitutional_health_rows else stream_callback
    started_at = datetime.utcnow()
    llm_result = await analyzer.generate_text_from_prompt(
        prompt,
        premium_analysis=False,
        model_override=None,
        model_name_override=model_name,
        llm_log_tag="instant_chat",
        request_timeout_s=answer_timeout_s,
        force_gemini=False,
        provider_override=instant_provider,
        use_gemini_rest=instant_provider == CHAT_LLM_GEMINI,
        gemini_thinking_level=(thinking_level if instant_provider == CHAT_LLM_GEMINI else None),
        deepseek_thinking_enabled=(False if instant_provider == CHAT_LLM_DEEPSEEK else None),
        stream_callback=generation_stream_callback,
    )
    elapsed_s = max(0.0, (datetime.utcnow() - started_at).total_seconds())
    pipeline_elapsed_s = max(0.0, time.perf_counter() - pipeline_started)
    stage_timings_ms["answer_model"] = round(elapsed_s * 1000.0, 1)
    stage_timings_ms["pipeline_total"] = round(pipeline_elapsed_s * 1000.0, 1)
    _log_instant_llm_response(
        request_id=answer_request_id,
        stage="instant_answer",
        model_name=model_name,
        prompt=prompt,
        result=llm_result,
        elapsed_s=elapsed_s,
    )

    if not llm_result.get("success"):
        error_text = llm_result.get("error") or "Instant chat failed"
        answer_usage_stage = _build_instant_usage_stage(
            "instant_answer",
            llm_result.get("chat_llm_model") or model_name,
            len(prompt),
            0,
            llm_result.get("token_usage") or {},
            False,
            elapsed_s,
        )
        return {
            "success": False,
            "response": "I’m having trouble giving the instant reading right now. Please try again in a moment.",
            "error": error_text,
            "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
            "timing": {
                "chat_llm_provider": instant_provider,
                "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
                "instant_chat": True,
                "total_request_time": pipeline_elapsed_s,
                "answer_model_time": elapsed_s,
                "instant_stage_timings_ms": stage_timings_ms,
                "instant_transport": (
                    "genai_rest_stream" if stream_callback else "genai_rest"
                ) if instant_provider == CHAT_LLM_GEMINI else "deepseek_chat_completions",
                "instant_thinking_level": thinking_level,
            },
            "token_usage": llm_result.get("token_usage") or {},
            "llm_prompt_chars": len(prompt),
            "llm_response_chars": 0,
            "instant_llm_usage_stage": answer_usage_stage,
            "instant_llm_usage_stages": [*instant_stages, answer_usage_stage],
            "terms": [],
            "glossary": {},
            "follow_up_questions": [],
        }

    raw_response = _repair_common_utf8_mojibake(llm_result.get("response")).strip()
    strict_health_fact_binding = bool(
        str(language or "english").strip().lower() in {"english", "en"}
        and not re.search(r"[^\x00-\x7F]", str(question or ""))
    )
    health_fact_validation_errors = (
        _validate_constitutional_health_answer(
            raw_response,
            constitutional_health_rows,
            strict_sentence_binding=strict_health_fact_binding,
        )
        if constitutional_health_rows
        else []
    )
    if constitutional_health_rows:
        if language_error := _instant_answer_language_error(raw_response, language):
            health_fact_validation_errors.append(language_error)
    health_fact_correction_attempted = False
    health_fact_correction_applied = False
    if health_fact_validation_errors:
        health_fact_correction_attempted = True
        logger.error(
            "INSTANT_HEALTH_FACT_REJECTED errors=%s answer=%r required_rows=%s",
            health_fact_validation_errors,
            raw_response[:1200],
            json.dumps(constitutional_health_rows, ensure_ascii=False, default=str),
        )
        correction_prompt = f"""
Your previous constitutional-health answer was rejected because it changed or omitted calculated chart facts.

{_instant_composer_language_rule(language)}
{_instant_relational_voice_contract()}

The rejected answer may itself use the wrong language. Do not copy its language; follow the USER QUESTION below.

Rewrite the complete answer once. Use every region in ranked order. For each region, state one distinct cause sentence using only that row's exact `required_cause_facts`. Planet, sign, nakshatra and house data are immutable. When the answer is not English, copy each row's exact `validation_marker` at the end of that row's explanatory sentence; it is mandatory, must not be translated, and will be removed before display. Do not mention dashas, transits, timing, current periods, diagnoses, or additional body regions. End with one natural preventive-care or symptom question, followed by the required metadata line.

VALIDATION FAILURES:
{json.dumps(health_fact_validation_errors, ensure_ascii=False)}

AUTHORITATIVE CALCULATED ROWS:
{json.dumps(constitutional_health_rows, ensure_ascii=False, separators=(",", ":"))}

USER QUESTION:
{question}

REJECTED ANSWER:
{raw_response}

Append exactly:
NEXT_ACTION_META: {{"type":"none","title":"","reason":"","confidence":"low","follow_up_questions":[],"source":"instant"}}
""".strip()
        correction_request_id = _log_instant_llm_request(
            stage="instant_health_fact_correction",
            model_name=model_name,
            prompt=correction_prompt,
            context={"required_zone_rows": constitutional_health_rows},
            answer_mode=answer_mode,
            speech_mode=speech_mode,
            compacted=True,
        )
        correction_started = datetime.utcnow()
        corrected_result = await analyzer.generate_text_from_prompt(
            correction_prompt,
            premium_analysis=False,
            model_override=None,
            model_name_override=model_name,
            llm_log_tag="instant_chat_health_fact_correction",
            request_timeout_s=answer_timeout_s,
            force_gemini=False,
            provider_override=instant_provider,
            use_gemini_rest=instant_provider == CHAT_LLM_GEMINI,
            gemini_thinking_level=(thinking_level if instant_provider == CHAT_LLM_GEMINI else None),
            deepseek_thinking_enabled=(False if instant_provider == CHAT_LLM_DEEPSEEK else None),
            stream_callback=None,
        )
        correction_elapsed_s = max(0.0, (datetime.utcnow() - correction_started).total_seconds())
        _log_instant_llm_response(
            request_id=correction_request_id,
            stage="instant_health_fact_correction",
            model_name=model_name,
            prompt=correction_prompt,
            result=corrected_result,
            elapsed_s=correction_elapsed_s,
        )
        corrected_raw = _repair_common_utf8_mojibake(corrected_result.get("response")).strip()
        corrected_errors = (
            _validate_constitutional_health_answer(
                corrected_raw,
                constitutional_health_rows,
                strict_sentence_binding=strict_health_fact_binding,
            )
            if corrected_result.get("success")
            else [str(corrected_result.get("error") or "correction generation failed")]
        )
        if corrected_result.get("success"):
            if language_error := _instant_answer_language_error(corrected_raw, language):
                corrected_errors.append(language_error)
        if corrected_errors:
            logger.error(
                "INSTANT_HEALTH_FACT_CORRECTION_REJECTED errors=%s answer=%r",
                corrected_errors,
                corrected_raw[:1200],
            )
            # Never return confidently wrong chart placements. The evidence is
            # still available to the UI for audit, while the user gets an
            # honest retry request instead of fabricated astrology.
            raw_response = (
                "I could not produce a reliable health-susceptibility explanation from the calculated chart facts. "
                "Please try this question again.\n\n"
                'NEXT_ACTION_META: {"type":"none","title":"","reason":"","confidence":"low","follow_up_questions":[],"source":"instant"}'
            )
            health_fact_validation_errors = corrected_errors
        else:
            raw_response = corrected_raw
            llm_result = corrected_result
            elapsed_s += correction_elapsed_s
            health_fact_validation_errors = []
            health_fact_correction_applied = True
    if constitutional_health_rows:
        raw_response = _strip_constitutional_health_validation_markers(raw_response)
    if constitutional_health_rows and stream_callback is not None:
        # Publish only the validated/corrected answer; no incorrect partial
        # placement ever reaches the processing message shown to the user.
        stream_callback(raw_response, raw_response)
    if speech_mode:
        response_text, speech_followups = _parse_speech_followups_from_answer(raw_response)
        response_text = _strip_speech_answer_greeting(response_text)
    else:
        response_text = raw_response
        speech_followups = []
    parsed_response = ResponseParser.parse_images_in_chat_response(response_text)
    response_content = parsed_response.get("content") or response_text
    response_content, prediction_anchor_meta = ResponseParser.parse_prediction_anchor_metadata(response_content)
    if instant_v2_packet:
        response_content = enforce_live_graph_answer(
            response_content,
            instant_v2_packet,
            language=language,
        )
        graph_policy = ((instant_v2_packet.get("answer_spec") or {}).get("knowledge_graph_policy") or {})
        if graph_policy.get("live") and not str(response_content or "").rstrip().endswith("?"):
            domain = str(graph_policy.get("domain") or "").lower()
            if str(language or "").lower().startswith("hi"):
                follow_up = (
                    "क्या कोई खास लक्षण या चिंता है जिसे आप ध्यान में रखना चाहते हैं?"
                    if domain == "health"
                    else "वास्तविक जीवन में अभी कौन-सा विकल्प ठोस रूप से सामने आ रहा है?"
                    if domain == "career"
                    else "क्या आप उपलब्ध गैर-समयबद्ध संकेत जानना चाहेंगे?"
                )
            else:
                follow_up = (
                    "Is there a specific symptom or concern you want me to keep in view?"
                    if domain == "health"
                    else "Which option is already becoming concrete in real life?"
                    if domain == "career"
                    else "Would you like the supported non-timing indications instead?"
                )
            response_content = f"{str(response_content or '').rstrip()}\n\n{follow_up}"
    if speech_mode:
        response_content = _strip_speech_answer_greeting(response_content)
        response_content = _polish_speech_event_answer(response_content, prompt_context)
        response_content = _truncate_speech_answer(response_content)
    # Instant is intentionally a single-generation product. Contract compliance
    # belongs in the authoritative first prompt; a second LLM editor adds
    # latency, can distort multilingual wording, and makes the experience no
    # longer instant.
    contract_enforcement = {
        "applied": health_fact_correction_applied,
        "reason": (
            "health_fact_validation_and_correction"
            if health_fact_correction_attempted
            else "single_call_contract_in_primary_prompt"
        ),
        "generation_calls": 2 if health_fact_correction_attempted else 1,
        "health_fact_validation_passed": not health_fact_validation_errors,
        "health_fact_validation_errors": health_fact_validation_errors,
    } if instant_v2_packet else None
    if instant_v2_packet:
        instant_v2_packet = finalize_instant_v2_packet(
            instant_v2_packet,
            answer=response_content,
        )
    next_action = parsed_response.get("next_action") or {}
    category = str(
        (intent or {}).get("category")
        or ((instant_context.get("intent_summary") or {}).get("category"))
        or "general"
    )
    remedy_active = _explicit_remedy_followup_requested(intent, question)
    health_rules = (
        ((instant_v2_packet or {}).get("answer_spec") or {}).get("health_rules")
        if isinstance(instant_v2_packet, dict)
        else None
    )
    suppress_remedy_cta = bool(
        isinstance(health_rules, dict)
        and not health_rules.get("is_time_bound_question")
    )
    response_content, next_action, combined_followups = apply_normal_answer_remedy_guards(
        content=response_content,
        next_action=next_action if next_action else None,
        follow_up_questions=list(
            (next_action or {}).get("follow_up_questions")
            or parsed_response.get("follow_up_questions")
            or []
        ),
        answer_mode=answer_mode,
        category=category,
        question=question,
        language=(language or "english").strip().lower(),
        remedy_followup_active=remedy_active,
        suppress_remedy_cta=suppress_remedy_cta,
    )
    next_action = next_action or {}
    graph_policy = (
        ((instant_v2_packet or {}).get("answer_spec") or {}).get("knowledge_graph_policy") or {}
        if isinstance(instant_v2_packet, dict)
        else {}
    )
    if (
        not speech_mode
        and str(graph_policy.get("runtime_key") or "").strip().lower() == "marriage_history"
    ):
        phase_action = build_phase_action((instant_v2_packet or {}).get("verdict"))
        if phase_action:
            next_action = phase_action
            combined_followups = []
    if not combined_followups and speech_followups and not remedy_active:
        combined_followups = list(speech_followups)
    logger.info(
        "instant_chat_next_action_decoded type=%s title=%s confidence=%s follow_up_count=%s speech_mode=%s",
        next_action.get("type"),
        next_action.get("title"),
        next_action.get("confidence"),
        len(combined_followups),
        bool(speech_mode),
    )
    pipeline_elapsed_s = max(0.0, time.perf_counter() - pipeline_started)
    stage_timings_ms["pipeline_total"] = round(pipeline_elapsed_s * 1000.0, 1)
    answer_usage_stage = _build_instant_usage_stage(
        "instant_answer",
        llm_result.get("chat_llm_model") or model_name,
        len(prompt),
        len(response_text),
        llm_result.get("token_usage") or {},
        True,
        elapsed_s,
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
        "suppress_remedy_cta": suppress_remedy_cta,
        "error": None,
        "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
        "timing": {
            "chat_llm_provider": instant_provider,
            "chat_llm_model": llm_result.get("chat_llm_model") or model_name,
            "instant_chat": True,
            "total_request_time": pipeline_elapsed_s,
            "answer_model_time": elapsed_s,
            "instant_stage_timings_ms": stage_timings_ms,
            "instant_transport": (
                "genai_rest_stream" if stream_callback else "genai_rest"
            ) if instant_provider == CHAT_LLM_GEMINI else "deepseek_chat_completions",
            "instant_thinking_level": thinking_level,
        },
        "token_usage": llm_result.get("token_usage") or {},
        "llm_prompt_chars": len(prompt),
        "llm_response_chars": len(response_content),
        "instant_llm_usage_stage": answer_usage_stage,
        "instant_llm_usage_stages": [*instant_stages, answer_usage_stage],
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
        "instant_evidence_debug": (
            ({**instant_v2_packet, "contract_enforcement": contract_enforcement} if instant_v2_packet else None)
            or ({"build_error": instant_v2_packet_error} if instant_v2_packet_error else None)
            if _env_flag("INSTANT_CHAT_EVIDENCE_DEBUG", True)
            else None
        ),
    }
