"""Canonical Instant Health route profiles shared by calculation and graph parity tests."""

from __future__ import annotations

from typing import Any, Dict


HEALTH_ALIASES = {
    "disease": "health",
    "illness": "health",
    "mental_health": "mental_wellbeing",
    "mental": "mental_wellbeing",
    "operation": "surgery",
    "procedure": "surgery",
    "injury": "accident",
    "healing": "recovery",
}

HEALTH_PROFILES: Dict[str, Dict[str, Any]] = {
    "health": {
        "houses": [1, 6, 8, 12],
        "planets": ["Sun", "Moon", "Mars", "Saturn"],
        "label": "health constitution and vulnerability",
    },
    "mental_wellbeing": {
        "houses": [1, 4, 6, 8, 12],
        "planets": ["Moon", "Mercury", "Saturn", "Rahu", "Ketu"],
        "label": "mental and emotional wellbeing",
    },
    "surgery": {
        "houses": [1, 6, 8, 12],
        "planets": ["Mars", "Saturn", "Sun", "Ketu"],
        "label": "surgery or medical procedures",
    },
    "accident": {
        "houses": [1, 3, 6, 8, 12],
        "planets": ["Mars", "Saturn", "Rahu", "Ketu"],
        "label": "accident and injury susceptibility",
    },
    "recovery": {
        "houses": [1, 5, 6, 11, 12],
        "planets": ["Sun", "Jupiter", "Moon", "Saturn"],
        "label": "recovery and resilience support",
    },
}


def normalize_health_category(value: Any) -> str | None:
    key = str(value or "").strip().lower()
    key = HEALTH_ALIASES.get(key, key)
    return key if key in HEALTH_PROFILES else None


def is_health_category(value: Any) -> bool:
    return normalize_health_category(value) is not None
