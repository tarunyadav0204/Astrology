from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from ai.intent_router import apply_nakshatra_routing_guards  # noqa: E402
from calculators.nakshatra_calculator import NakshatraCalculator  # noqa: E402
from instant_chat_v2.graph_live import apply_live_graph_policy, enforce_live_graph_answer, resolve_live_graph_policy  # noqa: E402
from instant_chat_v2.nakshatra import NAKSHATRA_PROFILES, NAKSHATRA_SUBTYPES  # noqa: E402
from instant_chat_v2.nakshatra_calculation import build_nakshatra_foundation  # noqa: E402
from instant_chat_v2.nakshatra_graph_policy import NakshatraGraphPolicyStore  # noqa: E402
from instant_chat_v2.translated_astrology import build_translated_astrology_contract  # noqa: E402


def _longitude(number: int, pada: int = 2) -> float:
    span = 360 / 27
    return (number - 1) * span + (pada - 0.5) * (span / 4)


def _chart(moon_number: int = 4, moon_pada: int = 2) -> dict:
    return {
        "ascendant": 100.0,  # Cancer
        "planets": {
            "Moon": {"longitude": _longitude(moon_number, moon_pada), "house": 1, "sign_name": "Cancer"},
            "Sun": {"longitude": 350.0, "house": 9, "sign_name": "Pisces"},
            "Mars": {"longitude": 122.0, "house": 2, "sign_name": "Leo"},
            "Mercury": {"longitude": 321.0, "house": 8, "sign_name": "Aquarius"},
            "Jupiter": {"longitude": 124.0, "house": 2, "sign_name": "Leo"},
            "Venus": {"longitude": 35.0, "house": 11, "sign_name": "Taurus"},
            "Saturn": {"longitude": 148.0, "house": 2, "sign_name": "Leo"},
            "Rahu": {"longitude": 126.0, "house": 2, "sign_name": "Leo"},
            "Ketu": {"longitude": 306.0, "house": 8, "sign_name": "Aquarius"},
        },
    }


def test_gandamoola_has_the_correct_six_stars() -> None:
    found = set()
    for number in range(1, 28):
        calc = NakshatraCalculator(chart_data={"planets": {"Moon": {"longitude": _longitude(number)}}})
        if calc.analyze_nakshatra_yogas():
            found.add(number)
    assert found == {1, 9, 10, 18, 19, 27}
    assert 2 not in found  # Bharani was the incorrect legacy entry.


def test_gandamoola_is_not_an_automatic_dosha_or_remedy_order() -> None:
    outside = NakshatraCalculator(chart_data={"planets": {"Moon": {"longitude": _longitude(1, 2)}}}).analyze_nakshatra_yogas()[0]
    junction = NakshatraCalculator(chart_data={"planets": {"Moon": {"longitude": 0.4}}}).analyze_nakshatra_yogas()[0]
    assert outside["junction_zone"] is False
    assert junction["junction_zone"] is True
    assert junction["boundary_distance_degrees"] == 0.4
    assert outside["remedy_required"] is False
    assert junction["remedy_required"] is False
    assert "outside" in outside["description"]


def test_every_nakshatra_route_has_a_typed_profile() -> None:
    assert set(NAKSHATRA_SUBTYPES) == set(NAKSHATRA_PROFILES)
    assert set(NakshatraGraphPolicyStore().runtime_keys()) == set(NAKSHATRA_SUBTYPES)


def test_guards_keep_static_timing_and_remedy_routes_separate() -> None:
    static = {
        "category": "birth_star", "nakshatra_subtype": "birth_star_overview",
        "answer_mode": "event_prediction", "needs_transits": True,
        "period_window": {"start": "2026-09-07"},
    }
    apply_nakshatra_routing_guards(static)
    assert static["category"] == "nakshatra"
    assert static["answer_mode"] == "topic_reading"
    assert static["needs_transits"] is False
    assert "period_window" not in static

    timing = {"category": "nakshatra", "nakshatra_subtype": "nakshatra_timing", "answer_mode": "topic_reading"}
    apply_nakshatra_routing_guards(timing)
    assert timing["answer_mode"] == "event_prediction"
    assert timing["needs_transits"] is True

    remedy = {"category": "nakshatra", "nakshatra_subtype": "nakshatra_remedy"}
    apply_nakshatra_routing_guards(remedy)
    assert remedy["answer_mode"] == "remedy_action"


def test_generic_career_is_not_stolen_by_nakshatra_domain() -> None:
    intent = {"category": "career", "career_subtype": "career_fit", "answer_mode": "topic_reading"}
    apply_nakshatra_routing_guards(intent)
    assert intent["category"] == "career"
    assert "nakshatra_subtype" not in intent


def test_topic_route_selects_house_lord_before_secondary_karakas() -> None:
    foundation = build_nakshatra_foundation(
        chart_data=_chart(), normalized_evidence={}, subtype="topic_nakshatra_analysis", topic="career",
    )
    assert foundation["carriers"][0]["carrier"] == "Mars"  # Cancer H10 lord
    assert foundation["carriers"][0]["role"] == "lord_of_house_10"
    assert foundation["carriers"][0]["nakshatra"] == "Magha"
    assert foundation["carriers"][0]["pada_navamsha_sign"]
    assert foundation["carriers"][0]["nakshatra_lord"] == "Ketu"


def test_named_planet_route_uses_only_that_planet_as_primary_carrier() -> None:
    foundation = build_nakshatra_foundation(
        chart_data=_chart(), normalized_evidence={}, subtype="planet_nakshatra", target_planet="Mercury",
    )
    assert [(row["carrier"], row["role"]) for row in foundation["carriers"]] == [
        ("Mercury", "user_selected_planet")
    ]


def test_remedy_and_naming_payloads_are_explicit_route_only() -> None:
    ordinary = build_nakshatra_foundation(chart_data=_chart(), normalized_evidence={}, subtype="birth_star_overview")
    assert ordinary["remedy"] is None and ordinary["naming"] is None
    remedy = build_nakshatra_foundation(chart_data=_chart(), normalized_evidence={}, subtype="nakshatra_remedy")
    assert remedy["remedy"]["target_planet"] == "Moon"
    naming = build_nakshatra_foundation(chart_data=_chart(), normalized_evidence={}, subtype="naming_syllable")
    assert naming["naming"]["syllable"]


def test_nakshatra_live_graph_matches_complete_calculated_foundation() -> None:
    foundation = build_nakshatra_foundation(
        chart_data=_chart(), normalized_evidence={}, subtype="topic_nakshatra_analysis", topic="career",
    )
    intent = {"category": "nakshatra", "nakshatra_subtype": "topic_nakshatra_analysis", "answer_mode": "topic_reading"}
    context = {"intent_summary": intent, "normalized_evidence": {"nakshatra_foundation": foundation}}
    policy = resolve_live_graph_policy(intent=intent, context=context, query_plan=intent)
    assert policy and policy["domain"] == "nakshatra"
    assert policy["evidence_status"] == "complete"
    assert policy["fallback_to_deeper_mode"] is False
    assert policy["missing_required_factors"] == []


def test_visible_contract_and_post_filter_allow_only_selected_carriers() -> None:
    foundation = build_nakshatra_foundation(
        chart_data=_chart(), normalized_evidence={}, subtype="planet_nakshatra", target_planet="Mercury",
    )
    intent = {"category": "nakshatra", "nakshatra_subtype": "planet_nakshatra", "answer_mode": "topic_reading"}
    context = {"intent_summary": intent, "normalized_evidence": {"nakshatra_foundation": foundation}}
    base = {"query_plan": intent, "answer_spec": {}, "verdict": {}, "verification": {}, "user_derivation": {}}
    packet = apply_live_graph_policy(base, intent=intent, context=context)
    policy = packet["answer_spec"]["knowledge_graph_policy"]
    filtered = enforce_live_graph_answer(
        "Mercury is in Purva Bhadrapada pada 1, ruled by Jupiter. Moon and Rahu show emotional restlessness.",
        packet,
    )
    assert "Mercury" in filtered and "Purva Bhadrapada" in filtered
    assert "Moon" not in filtered and "Rahu" not in filtered

    composer = {
        "query_plan": intent,
        "verdict": {"direction": "calculated"},
        "evidence": {"nakshatra_foundation": foundation},
        "answer_contract": {"knowledge_graph_policy": policy},
    }
    technical = build_translated_astrology_contract(
        composer, question="Explain Mercury's nakshatra", language="english", response_style="technical",
    )
    simple = build_translated_astrology_contract(
        composer, question="Explain Mercury's nakshatra", language="english", response_style="simple",
    )
    assert technical["technical_detail_allowed"] is True
    assert technical["minimum_technical_references"] >= 2
    assert set(technical["allowed_planets"]).issubset({"Mercury", "Jupiter"})
    assert simple["technical_detail_allowed"] is False
