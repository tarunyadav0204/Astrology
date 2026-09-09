"""Typed ownership and evidence profiles for the Nakshatra Live domain."""

from __future__ import annotations

from typing import Any


NAKSHATRA_CATEGORIES = frozenset({"nakshatra", "birth_star", "janma_nakshatra"})
NAKSHATRA_SUBTYPES = (
    "birth_star_overview",
    "ascendant_nakshatra",
    "planet_nakshatra",
    "full_nakshatra_profile",
    "pada_expression",
    "nakshatra_dispositor_chain",
    "topic_nakshatra_analysis",
    "nakshatra_timing",
    "special_nakshatra_conditions",
    "nakshatra_remedy",
    "naming_syllable",
)

NAKSHATRA_PROFILES: dict[str, dict[str, Any]] = {
    "birth_star_overview": {"charts": ["D1"], "answer_mode": "topic_reading", "target": "Moon"},
    "ascendant_nakshatra": {"charts": ["D1"], "answer_mode": "topic_reading", "target": "Ascendant"},
    "planet_nakshatra": {"charts": ["D1"], "answer_mode": "topic_reading", "target": "named_planet"},
    "full_nakshatra_profile": {"charts": ["D1", "D9"], "answer_mode": "topic_reading", "target": "profile"},
    "pada_expression": {"charts": ["D1", "D9"], "answer_mode": "topic_reading", "target": "selected"},
    "nakshatra_dispositor_chain": {"charts": ["D1"], "answer_mode": "topic_reading", "target": "selected"},
    "topic_nakshatra_analysis": {"charts": ["D1", "D9"], "answer_mode": "topic_reading", "target": "topic"},
    "nakshatra_timing": {"charts": ["D1"], "answer_mode": "event_prediction", "target": "timing"},
    "special_nakshatra_conditions": {"charts": ["D1"], "answer_mode": "topic_reading", "target": "Moon"},
    "nakshatra_remedy": {"charts": ["D1"], "answer_mode": "remedy_action", "target": "selected"},
    "naming_syllable": {"charts": ["D1"], "answer_mode": "factual_chart_lookup", "target": "Moon"},
}

_ALIASES = {
    "birth_star": "birth_star_overview",
    "moon_nakshatra": "birth_star_overview",
    "lagna_nakshatra": "ascendant_nakshatra",
    "planet": "planet_nakshatra",
    "profile": "full_nakshatra_profile",
    "pada": "pada_expression",
    "dispositor": "nakshatra_dispositor_chain",
    "topic": "topic_nakshatra_analysis",
    "timing": "nakshatra_timing",
    "gandamoola": "special_nakshatra_conditions",
    "gandanta": "special_nakshatra_conditions",
    "remedy": "nakshatra_remedy",
    "name": "naming_syllable",
    **{key: key for key in NAKSHATRA_SUBTYPES},
}

NAKSHATRA_TOPICS = frozenset({
    "general", "personality", "emotions", "career", "relationship",
    "wealth", "health", "spirituality",
})


def normalize_nakshatra_subtype(value: Any) -> str:
    key = str(value or "birth_star_overview").strip().lower().replace("-", "_").replace(" ", "_")
    return _ALIASES.get(key, "birth_star_overview")


def is_nakshatra_category(value: Any) -> bool:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_") in NAKSHATRA_CATEGORIES


def nakshatra_profile(subtype: Any) -> dict[str, Any]:
    key = normalize_nakshatra_subtype(subtype)
    return {"subtype": key, **NAKSHATRA_PROFILES[key]}

