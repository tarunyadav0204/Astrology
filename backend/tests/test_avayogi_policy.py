from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from calculators.avayogi_policy import AVAYOGI_CHAT_DOCTRINE, avayogi_effect  # noqa: E402
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator  # noqa: E402
from ai.parallel_chat.prompt_blocks import _parashari_json_footer  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _build_budgeted_instant_prompt,
    _build_instant_composer_prompt_v3,
)
from chat.system_instruction_config import build_merge_synthesis_instruction, build_system_instruction  # noqa: E402
from prediction_engine.context import CalculationContext, EvaluationContext  # noqa: E402
from prediction_engine.contracts import BirthChartInput, Polarity, PredictionWindow  # noqa: E402
from prediction_engine.natal_promise import build_natal_promises  # noqa: E402
from prediction_engine.providers.yogi_avayogi import YogiAvayogiProvider  # noqa: E402
from prediction_engine.taxonomy import EVENT_FAMILIES  # noqa: E402


def _chart(*, saturn_house: int = 4) -> dict:
    signs = {house: house - 1 for house in range(1, 13)}
    placements = {
        "Sun": 1,
        "Moon": 2,
        "Mars": 3,
        "Mercury": 5,
        "Jupiter": 7,
        "Venus": 9,
        "Saturn": saturn_house,
        "Rahu": 10,
        "Ketu": 4,
    }
    planets = {
        planet: {
            "house": house,
            "sign": signs[house],
            "sign_name": str(signs[house]),
            "longitude": signs[house] * 30.0 + 10.0,
            "degree": 10.0,
        }
        for planet, house in placements.items()
    }
    return {
        "ascendant": 0.0,
        "houses": [{"house_number": house, "sign": signs[house]} for house in range(1, 13)],
        "planets": planets,
    }


def _special_points(planet: str, *, overlap: bool) -> dict:
    return {
        "yogi": {"lord": "Jupiter", "sign": 8, "sign_name": "Sagittarius"},
        "avayogi": {"lord": planet, "sign": 9, "sign_name": "Capricorn"},
        "dagdha_rashi": {"lord": "Venus", "sign": 1, "sign_name": "Taurus"},
        "tithi_shunya_rashi": {
            "lord": planet if overlap else "Mercury",
            "sign": 2,
            "sign_name": "Gemini",
        },
        "avayogi_tithi_shunya_overlap": {"is_active": overlap, "planet": planet if overlap else None},
    }


def test_avayogi_tithi_shunya_overlap_cancels_instead_of_remaining_mixed() -> None:
    result = avayogi_effect(placement_house=2, tithi_shunya_overlap=True)
    assert result["polarity"] == "neutral"
    assert result["rule"] == "avayogi_tithi_shunya_cancellation"


def test_avayogi_placement_in_declared_reversal_houses_is_supportive() -> None:
    for house in (3, 6, 8, 12):
        result = avayogi_effect(placement_house=house, tithi_shunya_overlap=False)
        assert result["polarity"] == "supportive"
        assert result["rule"] == "avayogi_placement_reversal"


def test_avayogi_aspect_to_declared_reversal_houses_is_supportive_only_there() -> None:
    for house in (3, 6, 8, 12):
        result = avayogi_effect(
            placement_house=2,
            target_house=house,
            relation="aspector",
        )
        assert result["polarity"] == "supportive"
        assert result["rule"] == "avayogi_aspect_reversal"
    assert avayogi_effect(
        placement_house=2,
        target_house=5,
        relation="aspector",
    )["polarity"] == "challenging"


def test_natal_promise_uses_cancellation_and_house_reversals() -> None:
    chart = _chart(saturn_house=4)
    dignities = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()

    cancelled, _ = build_natal_promises(
        chart,
        dignities,
        yogi_points=_special_points("Saturn", overlap=True),
    )
    house_four = next(row for row in cancelled if row["house"] == 4)
    cancelled_factor = next(
        factor for factor in house_four["factors"]
        if factor["source"] == "avayogi_lord" and factor["planet"] == "Saturn"
    )
    assert cancelled_factor["polarity"] == "neutral"
    assert cancelled_factor["facts"]["avayogi_effect"]["rule"] == "avayogi_tithi_shunya_cancellation"

    aspect_chart = _chart(saturn_house=4)
    aspect_dignities = PlanetaryDignitiesCalculator(aspect_chart).calculate_planetary_dignities()
    promises, _ = build_natal_promises(
        aspect_chart,
        aspect_dignities,
        yogi_points=_special_points("Saturn", overlap=False),
    )
    house_six = next(row for row in promises if row["house"] == 6)
    aspect_factor = next(
        factor for factor in house_six["factors"]
        if factor["source"] == "avayogi_lord" and factor["planet"] == "Saturn"
    )
    assert aspect_factor["polarity"] == "supportive"
    assert aspect_factor["facts"]["avayogi_effect"]["rule"] == "avayogi_aspect_reversal"


def test_standard_premium_and_merge_prompts_share_the_same_policy() -> None:
    standard = build_system_instruction(intent_category="career")
    merge = build_merge_synthesis_instruction()
    parashari = _parashari_json_footer()
    for prompt in (standard, merge, parashari):
        assert AVAYOGI_CHAT_DOCTRINE in prompt
        assert "House 3, 6, 8 or 12" in prompt
        assert "ordinary Avayogi obstruction is cancelled" in prompt


def test_instant_full_and_budget_prompts_share_the_same_policy() -> None:
    context = {
        "query_plan": {},
        "answer_contract": {},
        "evidence": {},
        "answer_blueprint": {},
    }
    prompts = (
        _build_instant_composer_prompt_v3("What does my chart show?", context, "english"),
        _build_budgeted_instant_prompt("What does my chart show?", context, "english"),
    )
    for prompt in prompts:
        assert AVAYOGI_CHAT_DOCTRINE in prompt


def test_active_avayogi_provider_emits_support_for_dusthana_aspect() -> None:
    chart = _chart(saturn_house=4)
    window = PredictionWindow(
        "2026-09-01", "2026-09-30", "Saturn", "Venus", "Mercury", "test",
    )
    calculation = CalculationContext(
        birth=BirthChartInput.from_mapping({
            "date": "1990-01-15",
            "time": "10:30",
            "latitude": 28.6,
            "longitude": 77.2,
            "timezone": "Asia/Kolkata",
        }),
        chart=chart,
        natal_dignities={},
        yogi_points=_special_points("Saturn", overlap=False),
        gandanta={},
        badhaka_lord="",
        windows=(window,),
        transit_states_by_signature={"test": {}},
        divisional_charts={},
    )
    context = EvaluationContext(
        calculation=calculation,
        window=window,
        subject="self",
        event_family=EVENT_FAMILIES["financial_pressure"],
        primary_houses=(6,),
        supporting_houses=(),
        conflicting_houses=(),
    )

    evidence = YogiAvayogiProvider().evaluate(context)
    reversal = next(row for row in evidence if row.rule_id == "avayogi_aspect_reversal")
    assert reversal.house == 6
    assert reversal.polarity == Polarity.SUPPORTIVE
    assert reversal.facts["avayogi_effect"]["rule"] == "avayogi_aspect_reversal"
