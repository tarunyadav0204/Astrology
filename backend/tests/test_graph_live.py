from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.graph_live import apply_live_graph_policy, enforce_live_graph_answer  # noqa: E402
from calculators.remedy_engine import RemedyEngine  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _compact_marriage_pathway_evidence,
    _compact_spouse_meeting_evidence,
    _compact_spouse_temperament_evidence,
    _compact_spouse_appearance_evidence,
    _compact_spouse_location_evidence,
    _attach_calculated_remedy_blueprint,
    _normalize_instant_evidence,
    _build_instant_composer_context,
    _build_instant_composer_prompt_v3,
)


def _packet(category: str, answer_mode: str, **query_values):
    return {
        "query_plan": {"category": category, "answer_mode": answer_mode, **query_values},
        "answer_spec": {"max_words": 150, "answer_order": ["direct_answer"]},
        "verification": {"passed": True},
        "user_derivation": {},
    }


@pytest.mark.parametrize(
    ("packet", "intent", "context", "expected_domain", "expected_route"),
    [
        (
            _packet("career", "topic_reading", career_subtype="general"),
            {"category": "career", "career_subtype": "general"},
            {
                "intent_summary": {"category": "career", "answer_mode": "topic_reading"},
                "instant_parashari": {"career_foundation": {
                    "career_subtype": "general", "D1": {"houses": [{"house": h} for h in (2, 6, 10, 11)]},
                    "D10": {"calculated_chart": {"ascendant": 1}}, "amatyakaraka": {"planet": "Mercury"},
                    "KARAKAMSHA": {"ascendant": 8},
                }},
            },
            "career", "general",
        ),
        (
            _packet("health", "topic_reading"),
            {"category": "health"},
            {
                "intent_summary": {"category": "health", "answer_mode": "topic_reading"},
                "normalized_evidence": {"health_body_area": {
                    "major_vulnerabilities": [{"zone": "nose"}],
                    "medical_profile": {"protective_factors": ["support"]},
                    "house_map": [{"house": h} for h in (1, 6, 8, 12)],
                }},
            },
            "health", "health",
        ),
        (
            _packet("marriage", "potential_capacity"),
            {"category": "marriage"},
            {
                "intent_summary": {"category": "marriage", "answer_mode": "potential_capacity"},
                "normalized_evidence": {"natal_promise": {"status": "supported"}, "divisional_specifics": {"d9": "supportive"}},
            },
            "marriage", "marriage_promise",
        ),
    ],
)
def test_supported_domains_receive_authoritative_pre_generation_graph_policy(
    packet, intent, context, expected_domain, expected_route,
) -> None:
    result = apply_live_graph_policy(packet, intent=intent, context=context)
    policy = result["knowledge_graph_policy"]
    assert policy["live"] is True
    assert policy["enforcement"] == "authoritative_pre_generation"
    assert policy["domain"] == expected_domain
    assert policy["runtime_key"] == expected_route
    assert result["answer_spec"]["knowledge_graph_policy"]["live"] is True
    assert result["query_plan"]["knowledge_graph_route"]["runtime_key"] == expected_route
    assert result["verification"]["knowledge_graph"]["live"] is True
    route = result["user_derivation"][f"{expected_domain}_graph_route"]
    assert route["live"] is True


def test_non_graph_domain_remains_unchanged() -> None:
    packet = _packet("wealth", "topic_reading")
    assert apply_live_graph_policy(packet, intent={"category": "wealth"}, context={}) == packet


def test_career_comparison_routes_to_combined_promotion_and_job_change_graph() -> None:
    packet = _packet(
        "career", "comparison_choice", career_subtype="promotion",
        comparison_options=[
            {"event_profile": "promotion"},
            {"event_profile": "job_change"},
        ],
    )
    result = apply_live_graph_policy(
        packet,
        intent={"category": "career", "career_subtype": "promotion"},
        context={"intent_summary": {"category": "career", "answer_mode": "comparison_choice"}},
    )
    assert result["knowledge_graph_policy"]["runtime_key"] == "promotion_vs_job_change"


def test_static_live_policy_carries_authored_timing_exclusions() -> None:
    result = apply_live_graph_policy(
        _packet("marriage", "potential_capacity"),
        intent={"category": "marriage"},
        context={
            "intent_summary": {"category": "marriage", "answer_mode": "potential_capacity"},
            "normalized_evidence": {"natal_promise": {"status": "supported"}},
            "current_dashas": {"levels": {"MD": "Saturn"}},
            "current_transits": {"planets": {"Saturn": {"house": 7}}},
        },
    )
    exclusions = set(result["answer_spec"]["knowledge_graph_policy"]["default_exclusions"])
    assert {"marriage:DashaActivation", "marriage:TransitConfirmation"}.issubset(exclusions)


@pytest.mark.parametrize(
    ("subtype", "answer_mode", "expected_route"),
    [
        ("love_vs_arranged", "comparison_choice", "love_arranged_marriage"),
        ("remarriage", "event_prediction", "remarriage"),
        ("engagement_vs_wedding", "event_prediction", "engagement_wedding_timing"),
        ("spouse_meeting", "topic_reading", "spouse_meeting"),
        ("spouse_details", "relationship_person", "spouse_details"),
        ("affair", "problem_diagnosis", "affair_assessment"),
    ],
)
def test_extended_marriage_subtypes_are_live_graph_routes(
    subtype: str, answer_mode: str, expected_route: str,
) -> None:
    result = apply_live_graph_policy(
        _packet("marriage", answer_mode, marriage_subtype=subtype),
        intent={"category": "marriage", "marriage_subtype": subtype},
        context={
            "intent_summary": {"category": "marriage", "answer_mode": answer_mode},
            "normalized_evidence": {"person_profile_axes": [{"scope": "spouse"}]},
        },
    )
    assert result["knowledge_graph_policy"]["runtime_key"] == expected_route
    assert result["knowledge_graph_policy"]["live"] is True


def test_past_love_arranged_route_uses_static_pathway_contract_not_timed_option_windows() -> None:
    packet = _packet(
        "marriage", "comparison_choice",
        marriage_subtype="love_vs_arranged",
        time_scope={"relation": "past", "retrospective": False},
    )
    packet["verdict"] = {
        "direction": "supported_natal_promise",
        "ranked_windows": [{"start": "2027-01-01", "end": "2027-03-01"}],
    }
    context = {
        "intent_summary": {"category": "marriage", "answer_mode": "comparison_choice"},
        "normalized_evidence": {
            "natal_promise": {"status": "supported"},
            "divisional_specifics": {"d9": "supportive"},
        },
    }

    result = apply_live_graph_policy(
        packet,
        intent={"category": "marriage", "marriage_subtype": "love_vs_arranged"},
        context=context,
    )
    policy = result["answer_spec"]["knowledge_graph_policy"]
    rules = policy["marriage_pathway_rules"]

    assert policy["runtime_key"] == "love_arranged_marriage"
    assert rules["question_time_relation"] == "past"
    assert set(rules["love_led_pathway"]["required_factors"]) == {
        "marriage:H5", "marriage:H7", "marriage:D9",
    }
    assert "marriage:H2" in rules["family_mediated_pathway"]["required_factors"]
    assert "ranked_windows" not in result["verdict"]
    assert result["verdict"]["scope"].startswith("static love-led")

    composer = _build_instant_composer_context(context, result)
    prompt = _build_instant_composer_prompt_v3(
        "Did I have a love or arranged marriage?", composer, "english"
    )
    assert "love-led versus family-mediated marriage-pathway comparison" in prompt
    assert "Use past tense throughout" in prompt
    assert "Do not ask whether the user is currently in a relationship" in prompt
    assert "not a marriage-timing reading" in prompt
    assert "Never use \"active\", \"activated\", \"activation\"" in prompt

    safe = enforce_live_graph_answer(
        "The 7th house is activated, showing partnership activation.",
        result,
        language="english",
    )
    assert "activat" not in safe.lower()
    assert "natal chart" in safe.lower()


def test_marriage_pathway_evidence_carries_all_authored_d1_houses_and_d9() -> None:
    natal = {
        "source": "validated_d1_natal_promise",
        "houses": [
            {
                "house": house,
                "lord": f"Lord{house}",
                "tone": "supportive",
                "supportive_weight": house,
                "factors": [{
                    "source": "house_lord",
                    "planet": f"Lord{house}",
                    "polarity": "supportive",
                    "facts": {"target_house": 7, "placement_house": 2},
                }],
            }
            for house in (2, 5, 7, 9, 11)
        ],
    }
    evidence = _compact_marriage_pathway_evidence(
        natal,
        {"topic": {"support": "supportive", "codes": ["D9"], "charts": {
            "D9": {"support": "supportive", "rows": [{"planet": "Venus"}]},
        }}},
    )

    assert [row["house"] for row in evidence["d1_house_evidence"]] == [2, 5, 7, 9, 11]
    assert evidence["love_led_houses"] == [5, 7]
    assert evidence["family_mediated_houses"] == [2, 7, 9, 11]
    assert evidence["d9_confirmation"]["topic"]["charts"]["D9"]["support"] == "supportive"
    assert evidence["natal_lord_links"][0]["to_house"] == 2
    assert "Challenging is not supportive" in evidence["tone_fidelity_rule"]


def test_spouse_meeting_uses_seventh_lord_destination_and_excludes_timing_story() -> None:
    natal = {
        "houses": [
            {
                "house": house,
                "lord": "Saturn" if house == 7 else f"Lord{house}",
                "tone": "challenging",
                "factors": ([{
                    "source": "house_lord",
                    "planet": "Saturn",
                    "polarity": "challenging",
                    "facts": {"placement_house": 2},
                }] if house == 7 else []),
            }
            for house in (3, 7, 9, 11, 12)
        ],
    }
    meeting = _compact_spouse_meeting_evidence(
        natal,
        [
            "Spouse nature anchor: seventh lord Saturn is placed in house 2.",
            "Current D9 spouse-tone support: MD Saturn connects through D9 house 10.",
        ],
        {"topic": {"support": "supportive", "codes": ["D9"], "charts": {
            "D9": {"support": "supportive", "rows": [{"h": 7, "lord": "Saturn"}]},
        }}},
    )

    assert meeting["evidence_complete"] is True
    assert meeting["primary_channel"]["placement_house"] == 2
    assert "family" in meeting["primary_channel"]["probable_context"]
    assert not any("Current" in row for row in meeting["derived_spouse_frame"])

    packet = _packet(
        "marriage", "topic_reading", marriage_subtype="spouse_meeting",
        time_scope={"relation": "past", "retrospective": False},
    )
    context = {
        "intent_summary": {"category": "marriage", "answer_mode": "topic_reading"},
        "normalized_evidence": {"spouse_meeting_context": meeting},
    }
    result = apply_live_graph_policy(
        packet,
        intent={"category": "marriage", "marriage_subtype": "spouse_meeting"},
        context=context,
    )
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "spouse_meeting"
    assert policy["spouse_meeting_rules"]["evidence_complete"] is True
    assert policy.get("claim_permission") != "no_specific_meeting_story"

    composer = _build_instant_composer_context(context, result)
    prompt = _build_instant_composer_prompt_v3("How did I meet my spouse?", composer, "english")
    assert "Lead with `primary_channel.probable_context`" in prompt
    assert "Never mention dasha, transit, activation" in prompt
    safe = enforce_live_graph_answer(
        "The Saturn-driven period suggests work or duty. Family involvement is more likely.",
        result,
        language="english",
    )
    assert "Saturn-driven" not in safe
    assert safe == "Family involvement is more likely."


def test_spouse_temperament_requires_seventh_lord_nakshatra_darakaraka_venus_and_d9() -> None:
    chart = {
        "ascendant": 120.0,
        "planets": {
            "Saturn": {"longitude": 155.0, "house": 2, "sign": 5},
            "Mercury": {"longitude": 201.0, "house": 7, "sign": 6},
            "Venus": {"longitude": 350.0, "house": 8, "sign": 11},
            "Mars": {"longitude": 12.0, "house": 9, "sign": 0},
            "Sun": {"longitude": 40.0, "house": 10, "sign": 1},
            "Moon": {"longitude": 70.0, "house": 11, "sign": 2},
            "Jupiter": {"longitude": 100.0, "house": 12, "sign": 3},
        },
    }
    natal = {"houses": [{
        "house": 7,
        "lord": "Saturn",
        "occupants": ["Mercury"],
        "tone": "challenging",
        "factors": [{
            "source": "house_lord", "planet": "Saturn",
            "facts": {"placement_house": 2},
        }],
    }]}
    karakas = {
        "calculation_method": "test",
        "chara_karakas": {"Darakaraka": {
            "planet": "Mars", "degree_in_sign": 12.0,
        }},
    }
    divisional = {"topic": {
        "support": "supportive", "codes": ["D9"], "charts": {
            "D9": {"support": "supportive", "rows": [{"h": 7, "lord": "Saturn", "occ": ["Venus"]}]},
        },
    }}
    temperament = _compact_spouse_temperament_evidence(chart, natal, karakas, divisional)
    layers = temperament["layers"]

    assert temperament["evidence_complete"] is True
    assert layers["seventh_house"]["tone"] == "challenging"
    assert layers["seventh_lord_rashi_nakshatra"]["planet"] == "Saturn"
    assert layers["seventh_lord_rashi_nakshatra"]["nakshatra"]
    assert layers["darakaraka_rashi_nakshatra"]["planet"] == "Mars"
    assert layers["venus_rashi_nakshatra"]["rashi"] == "Pisces"
    assert layers["venus_rashi_nakshatra"]["nakshatra"]
    assert layers["d9_confirmation"]["support"] == "supportive"

    packet = _packet("spouse", "relationship_person")
    context = {
        "intent_summary": {"category": "spouse", "answer_mode": "relationship_person"},
        "normalized_evidence": {"spouse_temperament_context": temperament},
    }
    result = apply_live_graph_policy(packet, intent={"category": "spouse"}, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "spouse_profile"
    assert policy["spouse_temperament_rules"]["evidence_complete"] is True
    assert policy.get("claim_permission") != "no_specific_spouse_temperament"

    composer = _build_instant_composer_context(context, result)
    prompt = _build_instant_composer_prompt_v3(
        "What kind of temperament does my chart indicate for my spouse?", composer, "english"
    )
    assert "five-layer spouse-temperament synthesis" in prompt
    assert "seventh-lord rashi and nakshatra" in prompt
    assert "Darakaraka rashi and nakshatra" in prompt
    assert "Venus rashi and nakshatra" in prompt
    assert "D9 confirmation" in prompt


def test_spouse_temperament_does_not_fall_back_to_seventh_house_when_layers_are_missing() -> None:
    packet = _packet("spouse", "relationship_person")
    context = {
        "intent_summary": {"category": "spouse", "answer_mode": "relationship_person"},
        "normalized_evidence": {
            "spouse_temperament_context": {
                "evidence_complete": False,
                "missing_layers": [
                    "seventh_lord_rashi_nakshatra",
                    "darakaraka_rashi_nakshatra",
                    "venus_rashi_nakshatra",
                    "d9_confirmation",
                ],
                "layers": {"seventh_house": {"occupants": ["Mercury"]}},
            },
        },
    }

    result = apply_live_graph_policy(packet, intent={"category": "spouse"}, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["claim_permission"] == "no_specific_spouse_temperament"
    assert "darakaraka_rashi_nakshatra" in policy["missing_temperament_layers"]

    safe = enforce_live_graph_answer(
        "Mercury makes your spouse analytical, practical, and highly communicative.",
        result,
        language="english",
    )
    assert "Mercury" not in safe
    assert "seventh house alone would be speculation" in safe


def test_spouse_appearance_answers_physical_facet_without_temperament_fallback() -> None:
    chart = {
        "ascendant": 120.0,
        "planets": {
            "Saturn": {"longitude": 155.0, "house": 2, "sign": 5},
            "Mercury": {"longitude": 201.0, "house": 7, "sign": 6},
            "Venus": {"longitude": 350.0, "house": 8, "sign": 11},
            "Mars": {"longitude": 12.0, "house": 9, "sign": 0},
        },
    }
    natal = {"houses": [{
        "house": 7, "lord": "Saturn", "occupants": ["Mercury"],
        "aspecting_planets": ["Jupiter"], "tone": "mixed",
    }]}
    karakas = {"chara_karakas": {"Darakaraka": {"planet": "Mars", "degree_in_sign": 12.0}}}
    divisional = {"topic": {"support": "supportive", "charts": {
        "D9": {"support": "supportive", "rows": [{"h": 7, "lord": "Saturn", "occ": ["Venus"]}]},
    }}}
    appearance = _compact_spouse_appearance_evidence(chart, natal, karakas, divisional)
    assert appearance["evidence_complete"] is True
    assert appearance["layers"]["seventh_house_sign"]["rashi"] == "Aquarius"

    packet = _packet(
        "marriage", "relationship_person",
        question="How will they look like?",
        marriage_subtype="spouse_details",
        special_flow={"spouse_detail_scope": "appearance"},
    )
    context = {
        "intent_summary": {"category": "marriage", "answer_mode": "relationship_person"},
        "normalized_evidence": {"spouse_appearance_context": appearance},
    }
    result = apply_live_graph_policy(
        packet,
        intent={"category": "marriage", "marriage_subtype": "spouse_details"},
        context=context,
    )
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "spouse_appearance"
    assert policy["spouse_appearance_rules"]["evidence_complete"] is True

    composer = _build_instant_composer_context(context, result)
    prompt = _build_instant_composer_prompt_v3("How will they look like?", composer, "english")
    assert "asks specifically how the spouse may look" in prompt
    assert "do not answer with temperament" in prompt
    assert "likely build/stature band" in prompt
    assert "exact skin colour" in prompt


def test_spouse_appearance_missing_layers_cannot_be_replaced_with_personality() -> None:
    packet = _packet(
        "spouse", "relationship_person",
        question="How will they look?",
        special_flow={"spouse_detail_scope": "appearance"},
    )
    context = {
        "intent_summary": {"category": "spouse", "answer_mode": "relationship_person"},
        "normalized_evidence": {"spouse_appearance_context": {
            "evidence_complete": False,
            "missing_layers": ["darakaraka_rashi_nakshatra", "d9_confirmation"],
            "layers": {"seventh_house_sign": {"rashi": "Aquarius"}},
        }},
    }
    result = apply_live_graph_policy(packet, intent={"category": "spouse"}, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["claim_permission"] == "no_specific_spouse_appearance"
    safe = enforce_live_graph_answer(
        "They will be intelligent, practical, reliable and quietly warm.", result, language="english"
    )
    assert "quietly warm" not in safe
    assert "Replacing physical evidence with personality traits would be speculation" in safe


def test_spouse_location_requires_direct_distance_links_not_generic_placement_folklore() -> None:
    chart = {
        "ascendant": 120.0,
        "planets": {
            "Saturn": {"longitude": 155.0, "house": 2, "sign": 5},
            "Moon": {"longitude": 160.0, "house": 2, "sign": 5},
            "Jupiter": {"longitude": 165.0, "house": 2, "sign": 5},
            "Venus": {"longitude": 350.0, "house": 8, "sign": 11},
            "Sun": {"longitude": 345.0, "house": 8, "sign": 11},
            "Mars": {"longitude": 355.0, "house": 8, "sign": 11},
        },
    }
    natal = {"houses": [{
        "house": 7, "lord": "Saturn", "occupants": [], "aspecting_planets": [], "tone": "mixed",
    }]}
    karakas = {"chara_karakas": {"Darakaraka": {"planet": "Venus", "degree_in_sign": 20.0}}}
    divisional = {"topic": {"charts": {
        "D9": {"support": "mixed", "rows": [{"h": 7, "lord": "Mercury", "occ": []}]},
    }}}
    location = _compact_spouse_location_evidence(chart, natal, karakas, divisional)
    assert location["evidence_complete"] is True
    assert location["verdict"] == "insufficient_specific_distance_evidence"
    assert not any(float(row["weight"]) >= 2 for row in location["distance_signals"])

    packet = _packet(
        "marriage", "relationship_person",
        question="Does my spouse appear connected with a different city, culture or background?",
        marriage_subtype="spouse_details",
        special_flow={"spouse_detail_scope": "location"},
    )
    context = {
        "intent_summary": {"category": "marriage", "answer_mode": "relationship_person"},
        "normalized_evidence": {"spouse_location_context": location},
    }
    result = apply_live_graph_policy(packet, intent={"category": "marriage"}, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "spouse_location"
    assert policy["spouse_location_rules"]["calculated_verdict"] == "insufficient_specific_distance_evidence"

    composer = _build_instant_composer_context(context, result)
    prompt = _build_instant_composer_prompt_v3(packet["query_plan"]["question"], composer, "english")
    assert "Saturn in Virgo" in prompt
    assert "does not by itself mean another city" in prompt
    assert "Never mention timing" in prompt


def test_spouse_location_supports_distance_only_from_direct_spouse_link() -> None:
    chart = {
        "ascendant": 120.0,
        "planets": {
            "Saturn": {"longitude": 250.0, "house": 9, "sign": 8},
            "Venus": {"longitude": 320.0, "house": 12, "sign": 10},
        },
    }
    natal = {"houses": [{"house": 7, "lord": "Saturn", "occupants": [], "tone": "supportive"}]}
    karakas = {"chara_karakas": {"Darakaraka": {"planet": "Venus", "degree_in_sign": 20.0}}}
    divisional = {"topic": {"charts": {
        "D9": {"support": "supportive", "rows": [{"h": 7, "lord": "Jupiter", "occ": []}]},
    }}}
    location = _compact_spouse_location_evidence(chart, natal, karakas, divisional)
    assert location["verdict"] == "different_city_culture_or_background_supported"
    assert location["distance_score"] >= 6


def test_marriage_remedy_selection_returns_one_calculated_action_before_diagnosis() -> None:
    chart = {
        "planets": {
            "Saturn": {"house": 3, "sign_name": "Virgo"},
            "Venus": {"house": 9, "sign_name": "Pisces"},
            "Mars": {"house": 9, "sign_name": "Pisces"},
        },
    }
    natal = {"houses": [
        {"house": 7, "lord": "Saturn", "occupants": []},
        {"house": 6, "lord": "Jupiter", "occupants": []},
        {"house": 8, "lord": "Saturn", "occupants": []},
        {"house": 12, "lord": "Mercury", "occupants": []},
    ]}
    blueprint = RemedyEngine(chart).build_remedy_blueprint(
        question="Which calculated remedy is most relevant for recurring marital conflict?",
        category="marriage",
        instant_parashari={
            "focus_houses": [2, 6, 7, 8, 11, 12],
            "natal_topic_factors": natal,
        },
        normalized_evidence={},
        current_dashas_context={},
    )
    top = blueprint["top_recommendation"]
    assert blueprint["selection_mode"] == "single_top"
    assert blueprint["recurring_marital_conflict"] is True
    assert top["source_section"] == "behavioral_house_expression"
    assert top["planet"] == "Saturn"
    assert top["action"]
    assert top["frequency"]
    assert top["astrological_reason"]

    packet = _packet("marriage", "remedy_action", marriage_subtype="general")
    context = {
        "intent_summary": {"category": "marriage", "answer_mode": "remedy_action"},
        "normalized_evidence": {
            "remedy_blueprint": blueprint,
            "current_timing": {"active_dashas": {"md": {"planet": "Saturn"}}},
        },
    }
    result = apply_live_graph_policy(packet, intent={"category": "marriage"}, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "marriage_remedies"
    assert "marriage:DashaActivation" not in policy["observed_factors"]
    assert "marriage:DashaActivation" not in policy["unexpected_default_exclusions"]
    assert policy["marriage_remedy_rules"]["required_count"] == 1
    assert policy["marriage_remedy_rules"]["top_recommendation"] == top

    composer = _build_instant_composer_context(context, result)
    assert composer["evidence"].get("current_timing") is None
    prompt = _build_instant_composer_prompt_v3(
        "Which calculated remedy is most relevant for recurring marital conflict?", composer, "english"
    )
    assert "Give exactly one remedy" in prompt
    assert "give exactly three" not in prompt.lower()
    assert "Do not mention current dasha" in prompt
    assert "not by retelling the marital-conflict diagnosis" in prompt


def test_remedy_blueprint_second_pass_attaches_ranked_top_recommendation() -> None:
    chart = {"planets": {
        "Saturn": {"house": 3, "sign_name": "Virgo"},
        "Venus": {"house": 9, "sign_name": "Pisces"},
    }}
    normalized = {}
    attached = _attach_calculated_remedy_blueprint(
        normalized=normalized,
        chart_data=chart,
        question="Which calculated remedy is most relevant for recurring marital conflict?",
        category="marriage",
        instant_parashari={
            "focus_houses": [2, 6, 7, 8, 11, 12],
            "natal_topic_factors": {"houses": [
                {"house": 7, "lord": "Saturn", "occupants": []},
                {"house": 6, "lord": "Jupiter", "occupants": []},
                {"house": 8, "lord": "Saturn", "occupants": []},
                {"house": 12, "lord": "Mercury", "occupants": []},
            ]},
        },
        current_dashas_context={},
        target_chart_context=None,
    )
    assert attached is True
    assert normalized["remedy_blueprint"]["selection_mode"] == "single_top"
    assert normalized["remedy_blueprint"]["top_recommendation"]["action"]


def test_remedy_normalization_receives_question_and_chart_data() -> None:
    normalized = _normalize_instant_evidence(
        answer_mode="remedy_action",
        category="marriage",
        question="Which calculated remedy is most relevant for recurring marital conflict?",
        chart_data={"planets": {"Saturn": {"house": 3, "sign_name": "Virgo"}}},
        instant_parashari={
            "focus_houses": [2, 6, 7, 8, 11, 12],
            "natal_topic_factors": {"houses": [
                {"house": 7, "lord": "Saturn", "occupants": []},
                {"house": 6, "lord": "Jupiter", "occupants": []},
                {"house": 8, "lord": "Saturn", "occupants": []},
                {"house": 12, "lord": "Mercury", "occupants": []},
            ]},
        },
        current_transits_formatted={},
        current_dashas_context={},
    )

    assert normalized["remedy_blueprint"]["selection_mode"] == "single_top"
    assert normalized["remedy_blueprint"]["top_recommendation"]["action"]


def test_marriage_remedy_route_fails_closed_without_ranked_calculation() -> None:
    packet = _packet("marriage", "remedy_action")
    context = {
        "intent_summary": {"category": "marriage", "answer_mode": "remedy_action"},
        "normalized_evidence": {"remedy_blueprint": {"selection_mode": "single_top"}},
    }
    result = apply_live_graph_policy(packet, intent={"category": "marriage"}, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["claim_permission"] == "no_calculated_marriage_remedy"
    safe = enforce_live_graph_answer(
        "The Saturn period suggests improving communication.", result, language="english"
    )
    assert "Saturn period" not in safe
    assert "calculated marriage-remedy recommendation is unavailable" in safe


def test_marriage_muhurat_uses_live_graph_route_for_dedicated_flow() -> None:
    packet = _packet(
        "muhurat", "dedicated_muhurat_flow",
        special_flow={
            "muhurat_event_type": "marriage",
            "muhurat_start_date": "2027-01-01",
            "muhurat_end_date": "2027-02-01",
            "muhurat_use_birth_location": True,
        },
    )
    result = apply_live_graph_policy(
        packet,
        intent={"category": "muhurat"},
        context={"intent_summary": {"category": "muhurat", "answer_mode": "dedicated_muhurat_flow"}},
    )
    assert result["knowledge_graph_policy"]["runtime_key"] == "marriage_muhurat"
    assert result["knowledge_graph_policy"]["missing_required_factors"] == []


def test_static_live_graph_route_structurally_removes_timing_before_generation() -> None:
    context = {
        "birth_summary": {"name": "Test"},
        "intent_summary": {"category": "marriage", "answer_mode": "potential_capacity"},
        "normalized_evidence": {
            "natal_promise": {"status": "supported"},
            "current_timing": {"chain": "Saturn-Venus"},
            "transit_activation_timeline": {"peak_windows": [{"start": "2027-01", "end": "2027-03"}]},
        },
    }
    packet = {
        **_packet("marriage", "potential_capacity", time_scope={"requested": "current"}),
        "verdict": {"direction": "supported_natal_promise", "ranked_windows": [{"start": "2027-01", "end": "2027-03"}]},
        "answer_spec": {
            "max_words": 150, "answer_order": ["direct_answer"],
            "event_rules": {"allowed_timing_windows": [{"start": "2027-01", "end": "2027-03"}]},
        },
    }
    live_packet = apply_live_graph_policy(packet, intent={"category": "marriage"}, context=context)
    composer = _build_instant_composer_context(context, live_packet)

    assert composer["answer_contract"]["knowledge_graph_policy"]["live"] is True
    assert composer["query_plan"].get("time_scope") is None
    assert composer["verdict"].get("ranked_windows") is None
    assert composer["evidence"].get("current_timing") is None
    assert composer["evidence"].get("transit_activation_timeline") is None
    assert "event_rules" not in composer["answer_contract"]


def test_incomplete_timing_route_fails_closed_before_and_after_generation() -> None:
    packet = _packet(
        "marriage", "event_prediction",
        time_scope={"as_of": "2026-08-26", "horizon_end": "2029-08-26"},
    )
    packet["verdict"] = {"direction": "supported", "ranked_windows": [{"start": "2027-04-01"}]}
    packet["answer_spec"]["event_rules"] = {"allowed_timing_windows": [{"start": "2027-04-01"}]}
    result = apply_live_graph_policy(
        packet,
        intent={"category": "marriage"},
        context={
            "intent_summary": {"category": "marriage", "answer_mode": "event_prediction"},
            "normalized_evidence": {"natal_promise": {"status": "supported"}},
        },
    )

    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["claim_permission"] == "directional_only_no_timing"
    assert result["verdict"]["ranked_windows"] == []
    assert result["answer_spec"]["event_rules"]["allowed_timing_windows"] == []
    safe = enforce_live_graph_answer(
        "August 2027 is your strongest marriage window.", result, language="english"
    )
    assert "August 2027" not in safe
    assert "missing required timing evidence" in safe


def test_live_answer_corrects_pd_sub_period_terminology() -> None:
    packet = _packet("career", "event_prediction")
    corrected = enforce_live_graph_answer(
        "Saturn-Rahu-Venus is active, with Venus as the sub-period lord.",
        packet,
        language="english",
    )
    assert "Venus as the sub-sub-period lord" in corrected


def test_incomplete_comparison_route_cannot_select_a_winner() -> None:
    packet = _packet(
        "career", "comparison_choice", career_subtype="promotion",
        comparison_options=[{"event_profile": "promotion"}, {"event_profile": "job_change"}],
    )
    packet["verdict"] = {"direction": "leans_to_option", "rationale": {"favored_option": "job_change"}}
    result = apply_live_graph_policy(
        packet,
        intent={"category": "career"},
        context={"intent_summary": {"category": "career", "answer_mode": "comparison_choice"}},
    )
    assert result["verdict"]["direction"] == "insufficient_option_evidence"
    safe = enforce_live_graph_answer("A job change is more likely.", result, language="english")
    assert "job change is more likely" not in safe.lower()
    assert safe.endswith("?")


def test_comparison_graph_reads_both_option_house_sets_from_fused_verdict() -> None:
    packet = _packet(
        "career", "comparison_choice", career_subtype="promotion",
        comparison_options=[{"event_profile": "promotion"}, {"event_profile": "job_change"}],
    )
    packet["verdict"] = {
        "direction": "leans_to_option",
        "rationale": {"favored_option": "job_change", "options": [
            {
                "event_profile": "promotion",
                "native_calculation_houses": [2, 6, 10, 11],
                "best_window": {"start": "2027-04-15", "end": "2027-08-26"},
            },
            {
                "event_profile": "job_change",
                "native_calculation_houses": [2, 3, 6, 10, 11, 12],
                "best_window": {"start": "2026-09-19", "end": "2027-02-12"},
            },
        ]},
    }
    context = {
        "intent_summary": {"category": "career", "answer_mode": "comparison_choice"},
        "instant_parashari": {"career_foundation": {
            "D1": {"houses": [{"house": h} for h in (2, 6, 10, 11)]},
            "D10": {"calculated_chart": {"ascendant": 1}},
        }},
        "current_dashas": {"levels": {"MD": "Saturn"}},
        "current_transits": {"planets": {"Saturn": {"house": 9}}},
    }
    result = apply_live_graph_policy(packet, intent={"category": "career"}, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "promotion_vs_job_change"
    assert policy["evidence_status"] == "complete"
    assert not policy.get("missing_required_factors")
    assert result["verdict"]["direction"] == "leans_to_option"
    assert result["verdict"]["ranked_windows"][0]["option"] == "job_change"


def test_missing_health_body_area_is_hard_gated_after_generation() -> None:
    packet = _packet("health", "event_prediction")
    packet["verdict"] = {
        "direction": "insufficient_evidence",
        "missing_required_capabilities": ["parashari.health_body_area"],
    }
    result = apply_live_graph_policy(
        packet,
        intent={"category": "health"},
        context={"intent_summary": {"category": "health", "answer_mode": "event_prediction"}},
    )
    assert result["answer_spec"]["knowledge_graph_policy"]["claim_permission"] == "no_health_area_specificity"
    safe = enforce_live_graph_answer(
        "Your 8th house shows a recovery concern from September 2026.", result, language="english"
    )
    assert "8th house" not in safe
    assert "September 2026" not in safe
    assert safe.endswith("?")
