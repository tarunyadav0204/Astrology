from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.graph_live import apply_live_graph_policy, enforce_live_graph_answer  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _compact_marriage_pathway_evidence,
    _compact_spouse_meeting_evidence,
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
