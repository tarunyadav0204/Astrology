"""Structured house channels for debilitated and retrograde planets.

This module deliberately does not turn retrogression into exaltation or a
promise of positive results.  It exposes the houses through which a planet can
deliver its results, then records the classical conditions that qualify that
delivery.  Consumers remain responsible for judging an actual dasha or
transit period.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_calculator import BaseCalculator
from .vedic_graha_drishti import get_aspect_houses_for_planet


VISIBLE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _owned_houses(ascendant_sign: int, planet_name: str) -> List[int]:
    return [
        house
        for house in range(1, 13)
        if BaseCalculator.SIGN_LORDS[(ascendant_sign + house - 1) % 12] == planet_name
    ]


def _delivery_state(*, debilitated: bool, neecha_bhanga: bool, retrograde: bool, combust: bool) -> str:
    parts = []
    if debilitated:
        parts.append("debilitation_cancelled" if neecha_bhanga else "debilitated")
    if retrograde:
        parts.append("retrograde")
    if combust:
        parts.append("combust")
    return "_".join(parts) if parts else "ordinary"


def calculate_planet_result_delivery(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return additive, factual delivery channels for the seven visible grahas."""
    planets = chart_data.get("planets") or {}
    ascendant = chart_data.get("ascendant")
    ascendant_sign = int(float(ascendant) / 30) % 12 if ascendant is not None else 0
    neecha_bhanga = chart_data.get("neecha_bhanga") or {}
    result: Dict[str, Any] = {
        "method": "classical_planet_result_channels_v1",
        "planets": {},
        "interpretive_boundary": "house_channels_are_not_a_standalone_prediction",
    }

    for planet_name in VISIBLE_PLANETS:
        planet = planets.get(planet_name)
        if not isinstance(planet, dict) or not isinstance(planet.get("sign"), int):
            continue

        sign = planet["sign"]
        occupied_house = int(planet.get("house") or (((sign - ascendant_sign) % 12) + 1))
        owned_houses = _owned_houses(ascendant_sign, planet_name)
        aspected = []
        for aspect_number in get_aspect_houses_for_planet(planet_name):
            if aspect_number == 1:
                continue
            target_sign = (sign + aspect_number - 1) % 12
            target_house = ((target_sign - ascendant_sign) % 12) + 1
            aspected.append({"house": target_house, "aspect_number": aspect_number})

        by_house: Dict[int, Dict[str, Any]] = {}

        def add_channel(house: int, role: str, aspect_number: int | None = None) -> None:
            row = by_house.setdefault(house, {"house": house, "roles": [], "aspect_numbers": []})
            if role not in row["roles"]:
                row["roles"].append(role)
            if aspect_number is not None and aspect_number not in row["aspect_numbers"]:
                row["aspect_numbers"].append(aspect_number)

        for house in owned_houses:
            add_channel(house, "owned")
        add_channel(occupied_house, "occupied")
        for aspect in aspected:
            add_channel(aspect["house"], "aspected", aspect["aspect_number"])

        nb_result = neecha_bhanga.get(planet_name) or {}
        debilitated = sign == BaseCalculator.DEBILITATION_SIGNS.get(planet_name)
        nb_present = bool(nb_result.get("neecha_bhanga_present"))
        retrograde = bool(planet.get("retrograde"))
        combustion = planet.get("combustion") or {}
        combust = bool(
            planet.get("combust")
            or combustion.get("is_combust")
            or combustion.get("isCombust")
        )

        supporting_factors = []
        limiting_factors = []
        if nb_present:
            supporting_factors.append({
                "key": "neecha_bhanga",
                "reference": nb_result.get("source", {}).get("reference_label", "Phaladeepika 7.26-30"),
            })
        if debilitated and not nb_present:
            limiting_factors.append({"key": "debilitation_uncancelled"})
        if retrograde:
            limiting_factors.append({"key": "retrograde_not_automatically_positive"})
        if combust:
            limiting_factors.append({"key": "combustion"})

        result["planets"][planet_name] = {
            "planet": planet_name,
            "relevant": debilitated or retrograde,
            "delivery_state": _delivery_state(
                debilitated=debilitated,
                neecha_bhanga=nb_present,
                retrograde=retrograde,
                combust=combust,
            ),
            "conditions": {
                "debilitated": debilitated,
                "neecha_bhanga": nb_present,
                "retrograde": retrograde,
                "combust": combust,
            },
            "owned_houses": owned_houses,
            "occupied_house": occupied_house,
            "aspected_houses": aspected,
            "channels": [by_house[house] for house in sorted(by_house)],
            "supporting_factors": supporting_factors,
            "limiting_factors": limiting_factors,
            "timing": {"activation_planet": planet_name, "rule": "judge_in_dasha_and_transit_context"},
        }

    return result


def attach_planet_result_delivery(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    chart_data["planet_result_delivery"] = calculate_planet_result_delivery(chart_data)
    return chart_data
