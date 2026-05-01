from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from calculators.real_transit_calculator import RealTransitCalculator
from context_agents.compact_vedic import house_lordships_from_ascendant
from daily_prediction_spine import (
    _build_trigger_evidence,
    _planet_natal_row,
    _planet_transit_row,
    _trigger_strength,
    _sign0,
)

FAST_PLANETS = ("Sun", "Moon", "Mercury", "Venus", "Mars")

_PLANET_CLIMATE_LABELS = {
    "Sun": "visibility_authority",
    "Moon": "emotional_flow",
    "Mercury": "communication_clarity",
    "Venus": "harmony_attraction",
    "Mars": "drive_conflict",
}

_PLANET_OPPORTUNITIES = {
    "Sun": ["take visible responsibility", "speak to authority figures clearly", "move with confidence instead of hesitation"],
    "Moon": ["listen to emotional undercurrents", "adapt quickly to mood changes", "use softer timing for sensitive topics"],
    "Mercury": ["send messages and paperwork carefully", "schedule important conversations", "double-check facts before committing"],
    "Venus": ["repair relationships gently", "use diplomacy in negotiation", "lean into comfort, aesthetics, and goodwill"],
    "Mars": ["use courage for decisive action", "channel urgency into execution", "protect focus from impulsive reactions"],
}

_PLANET_CAUTIONS = {
    "Sun": ["ego clashes", "overexposure", "boss-related friction"],
    "Moon": ["mood reactivity", "overpersonalizing events", "changing priorities too quickly"],
    "Mercury": ["miscommunication", "small errors", "revisits, delays, or back-and-forth"],
    "Venus": ["overindulgence", "avoiding hard truth for comfort", "mixed signals in affection or money"],
    "Mars": ["arguments", "haste", "cuts, burns, irritation, or forceful tone"],
}


def _planet_focus(planet: str, house: int) -> List[str]:
    base = {
        "Sun": ["authority", "confidence", "recognition"],
        "Moon": ["mood", "responsiveness", "felt experience"],
        "Mercury": ["messages", "logic", "coordination"],
        "Venus": ["harmony", "relationships", "comfort"],
        "Mars": ["action", "pressure", "conflict"],
    }.get(planet, [])
    house_overlays = {
        1: ["self", "body", "personal presence"],
        2: ["money", "family", "speech"],
        3: ["messages", "effort", "commute"],
        4: ["home", "comfort", "emotional grounding"],
        5: ["romance", "creativity", "expression"],
        6: ["workload", "health routines", "conflict"],
        7: ["partner", "clients", "agreements"],
        8: ["suddenness", "stress", "sensitivity"],
        9: ["guidance", "beliefs", "travel"],
        10: ["career", "visibility", "authority"],
        11: ["gains", "friends", "network response"],
        12: ["rest", "expenses", "withdrawal"],
    }.get(house, [])
    return base + house_overlays


def _practical_tone(planet: str, trigger_strength: str, transit_house: int) -> str:
    label = _PLANET_CLIMATE_LABELS.get(planet, "general")
    house_hint = {
        3: "messages and movement",
        5: "romance and expression",
        6: "workload and pressure",
        7: "partnership and public dealings",
        10: "visibility and work matters",
        12: "rest, withdrawal, or expense",
    }.get(transit_house, "practical daily matters")
    if trigger_strength == "massive":
        return f"{label} is highly activated through {house_hint}"
    if trigger_strength == "strong":
        return f"{label} is noticeably active through {house_hint}"
    if trigger_strength == "moderate":
        return f"{label} is present in the background through {house_hint}"
    return f"{label} is mild unless reinforced by other same-day triggers"


def _planet_row_summary(planet: str, natal: Dict[str, Any], transit: Dict[str, Any], trigger: Dict[str, Any]) -> Dict[str, Any]:
    transit_house = int(transit.get("house") or 0)
    strength = trigger.get("strength") or _trigger_strength(trigger.get("score"))
    return {
        "planet": planet,
        "climate": _PLANET_CLIMATE_LABELS.get(planet),
        "natal": natal,
        "transit": transit,
        "trigger": trigger,
        "strength": strength,
        "focus_areas": _planet_focus(planet, transit_house),
        "practical_tone": _practical_tone(planet, strength, transit_house),
        "opportunities": list(_PLANET_OPPORTUNITIES.get(planet, [])),
        "cautions": list(_PLANET_CAUTIONS.get(planet, [])),
    }


def _climate_band(score: int) -> str:
    if score >= 140:
        return "high"
    if score >= 90:
        return "active"
    if score >= 45:
        return "moderate"
    return "background"


def build_daily_fast_planets(
    *,
    birth_data: Dict[str, Any],
    static_context: Dict[str, Any],
    target_date: str,
) -> Dict[str, Any]:
    """Deterministic same-day fast-planet evidence for daily answers."""
    target_dt = datetime.strptime(str(target_date)[:10], "%Y-%m-%d").replace(hour=12, minute=0, second=0, microsecond=0)
    d1_chart = static_context.get("d1_chart") or {}
    ascendant = float(d1_chart.get("ascendant", 0.0) or 0.0)
    asc_sign = _sign0(ascendant)
    rtc = RealTransitCalculator()
    house_lordships = house_lordships_from_ascendant(asc_sign)
    planetary_analysis = static_context.get("planetary_analysis") or {}

    natal_rows = {
        planet: _planet_natal_row(planet, d1_chart, planetary_analysis, house_lordships, rtc)
        for planet in FAST_PLANETS
        if (d1_chart.get("planets") or {}).get(planet)
    }

    rows: List[Dict[str, Any]] = []
    by_planet: Dict[str, Dict[str, Any]] = {}
    total_score = 0
    for planet in FAST_PLANETS:
        natal = natal_rows.get(planet)
        if not natal:
            continue
        transit = _planet_transit_row(planet, target_dt, ascendant, rtc)
        trigger = _build_trigger_evidence(planet, natal, transit, natal_rows)
        row = _planet_row_summary(planet, natal, transit, trigger)
        rows.append(row)
        by_planet[planet] = row
        total_score += int(trigger.get("score") or 0)

    communication = by_planet.get("Mercury", {})
    relationship = by_planet.get("Venus", {})
    conflict = by_planet.get("Mars", {})
    visibility = by_planet.get("Sun", {})
    emotion = by_planet.get("Moon", {})

    return {
        "method": "daily_fast_planets_v1",
        "target_date": target_dt.strftime("%Y-%m-%d"),
        "rows": rows,
        "summary": {
            "overall_band": _climate_band(total_score),
            "communication_climate": communication.get("practical_tone"),
            "relationship_climate": relationship.get("practical_tone"),
            "conflict_risk": conflict.get("practical_tone"),
            "visibility_climate": visibility.get("practical_tone"),
            "emotional_climate": emotion.get("practical_tone"),
        },
    }

