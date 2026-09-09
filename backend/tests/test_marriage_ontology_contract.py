from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.marriage_graph_policy import MarriageGraphPolicyStore  # noqa: E402
from instant_chat_v2.graph_live import apply_live_graph_policy  # noqa: E402
from instant_chat_v2.orchestrator import build_instant_v2_packet  # noqa: E402
from instant_chat_v2.marriage_graph_runtime import (  # noqa: E402
    build_marriage_graph_route,
    compare_marriage_graph_policy,
    marriage_graph_runtime_key,
    resolve_marriage_graph_inputs,
)
from instant_chat_v2.planner import build_query_plan  # noqa: E402
from ai.evidence_planner_schema import normalize_evidence_plan  # noqa: E402
from ai.intent_router import apply_marriage_routing_guards  # noqa: E402
import chat.instant_chat_pipeline as pipeline  # noqa: E402


def test_marriage_ontology_compiles_and_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_marriage_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Marriage and Relationship ontology PoC valid: 22 competency questions" in result.stdout


def test_love_arranged_event_profile_survives_evidence_plan_normalization() -> None:
    plan = normalize_evidence_plan({
        "question_parts": [{
            "part_id": "p1",
            "text": "Hi meri love marriage hogi kya",
            "intent_families": ["comparison"],
            "life_domain": "marriage",
            "event_profile": "love_vs_arranged_marriage",
        }],
    })

    assert plan["question_parts"][0]["event_profile"] == "love_vs_arranged_marriage"


def test_compiled_bundle_covers_all_existing_relationship_families() -> None:
    assert set(MarriageGraphPolicyStore().runtime_keys()) == {
        "marriage_promise", "marriage_timing", "marriage_history", "married_life", "married_life_timing",
        "relationship_outlook", "relationship_timing", "separation_reconciliation",
        "separation_reconciliation_timing", "spouse_profile", "spouse_appearance", "spouse_location", "relationship_diagnosis",
        "marriage_remedies", "love_arranged_marriage", "remarriage", "engagement_wedding_timing",
        "spouse_meeting", "spouse_details", "affair_assessment", "marriage_muhurat",
        "compatibility_analysis",
    }


def test_every_marriage_route_has_expandable_stages_and_factor_children() -> None:
    store = MarriageGraphPolicyStore()
    for runtime_key in store.runtime_keys():
        question = store.require(runtime_key).graph_tree["children"][0]
        stages = next(node for node in question["children"] if node["label"] == "Decision stages")
        assert stages["children"], runtime_key
        for stage in stages["children"]:
            factors = next(node for node in stage["children"] if node["label"] == "Required astrology factors")
            assert factors["children"], f"{runtime_key}/{stage['label']}"


def test_marriage_graph_is_attached_to_canonical_parent_with_topics() -> None:
    question = MarriageGraphPolicyStore().require("marriage_timing").graph_tree["children"][0]
    branch = next(node for node in question["children"] if node["label"] == "Life domain")
    parent = branch["children"][0]
    assert parent["id"] == "domain:MarriageRelationships"
    topics = next(node for node in parent["children"] if node["label"] == "Domain topics")
    assert [node["id"] for node in topics["children"]] == [
        "domain:Marriage", "domain:Relationship", "domain:Separation",
    ]


def test_static_routes_exclude_timing_and_timed_routes_require_delivery_chain() -> None:
    store = MarriageGraphPolicyStore()
    for key in ("marriage_promise", "married_life", "relationship_outlook", "spouse_profile", "spouse_appearance", "spouse_location", "relationship_diagnosis", "marriage_remedies", "love_arranged_marriage", "spouse_meeting", "spouse_details", "affair_assessment"):
        assert {"marriage:DashaActivation", "marriage:TransitConfirmation"}.issubset(store.require(key).default_exclusions)
    for key in ("marriage_timing", "married_life_timing", "relationship_timing", "separation_reconciliation_timing", "remarriage", "engagement_wedding_timing"):
        policy = store.require(key)
        assert {"marriage:DashaActivation", "marriage:TransitConfirmation"}.issubset(policy.required_factors)
        assert "marriage:NoActivationCertainty" in policy.guardrails
    history = store.require("marriage_history")
    assert "marriage:RetrospectiveProbabilityOnly" in history.guardrails
    assert "marriage:HistoricalScopeOnly" in history.guardrails


def test_sensitive_relationship_guardrails_are_compiled() -> None:
    store = MarriageGraphPolicyStore()
    assert "marriage:NoDivorceCertainty" in store.require("separation_reconciliation_timing").guardrails
    assert "marriage:ClarifyRelationshipStatus" in store.require("separation_reconciliation").guardrails
    assert "marriage:DerivedChartDisclosure" in store.require("spouse_profile").guardrails
    assert "marriage:SpouseDetailScope" in store.require("spouse_appearance").guardrails
    assert "marriage:SpouseDetailScope" in store.require("spouse_location").guardrails
    assert "marriage:NoAffairAssertion" in store.require("affair_assessment").guardrails
    assert "marriage:PriorMarriageRequired" in store.require("remarriage").guardrails
    assert "marriage:SeparateMilestones" in store.require("engagement_wedding_timing").guardrails
    assert "marriage:MuhuratInputsRequired" in store.require("marriage_muhurat").guardrails
    assert "marriage:TwoChartsRequired" in store.require("compatibility_analysis").guardrails


def test_live_categories_and_answer_modes_resolve_to_graph_routes() -> None:
    cases = {
        ("marriage", "potential_capacity"): "marriage_promise",
        ("marriage", "event_prediction"): "marriage_timing",
        ("marriage", "topic_reading"): "married_life",
        ("marriage", "timing_window"): "married_life_timing",
        ("love", "topic_reading"): "relationship_outlook",
        ("relationship", "event_prediction"): "relationship_timing",
        ("separation", "topic_reading"): "separation_reconciliation",
        ("reconciliation", "timing_window"): "separation_reconciliation_timing",
        ("spouse", "relationship_person"): "spouse_profile",
        ("marriage", "problem_diagnosis"): "relationship_diagnosis",
        ("partner", "dedicated_partnership_flow"): "compatibility_analysis",
    }
    store = MarriageGraphPolicyStore()
    for (category, mode), expected in cases.items():
        actual = marriage_graph_runtime_key(category, {"answer_mode": mode})
        assert actual == expected
        assert store.resolve(actual) is not None
    assert marriage_graph_runtime_key("career", {"answer_mode": "topic_reading"}) is None


def test_married_life_route_uses_complete_d1_d9_and_jaimini_foundation() -> None:
    birth = {
        "name": "ABC",
        "date": "1980-04-02",
        "time": "14:55:00",
        "latitude": 29.2396596,
        "longitude": 75.8174505,
        "timezone": "UTC+5:30",
        "place": "Hisar, Haryana, India",
    }
    intent = {
        "category": "marriage",
        "marriage_subtype": "general",
        "mode": "ANALYZE_TOPIC_POTENTIAL",
        "answer_mode": "topic_reading",
        "needs_transits": False,
        "extracted_context": {},
        "evidence_plan": {"question_parts": [], "evidence_needs": []},
    }
    context = pipeline._build_instant_context(
        birth,
        "How will be my married life?",
        intent,
        [],
        answer_mode_override="topic_reading",
        target_subject_override={"key": "self", "label": "self", "base_house": 1},
    )
    foundation = context["normalized_evidence"]["married_life_foundation"]
    assert foundation["evidence_complete"] is True
    # Keep the complete marriage ledger inside the dedicated Live prompt
    # envelope. A previous duplicate copy inside fact_contract caused generic
    # emergency compaction to discard D9/Jaimini evidence.
    assert len(json.dumps(foundation, ensure_ascii=False, separators=(",", ":"))) < 20_000
    assert {row["house"] for row in foundation["d1_houses"]} == {2, 7, 8, 11, 12}
    assert {row["house"] for row in foundation["d9_houses"]} == {1, 2, 7, 8, 11, 12}
    assert foundation["natural_significators"]["Venus"]["d9"]
    assert foundation["natural_significators"]["Jupiter"]["d9"]
    assert foundation["jaimini"]["darakaraka"]["planet"]
    assert foundation["jaimini"]["upapada_lagna"]["sign"]
    assert foundation["jaimini"]["second_from_upapada"]["sign"]

    packet = build_instant_v2_packet(
        question="How will be my married life?",
        intent=intent,
        answer_mode="topic_reading",
        target_subject={"key": "self", "label": "self", "base_house": 1},
        language="english",
        instant_context=context,
    )
    packet = apply_live_graph_policy(packet, intent=intent, context=context)
    graph = packet["answer_spec"]["knowledge_graph_policy"]
    assert graph["runtime_key"] == "married_life"
    assert graph["missing_required_factors"] == []
    assert graph["married_life_rules"]["evidence_complete"] is True
    composer = pipeline._build_instant_composer_context(context, packet)
    assert set(composer["evidence"]) == {"married_life_foundation"}
    assert composer["evidence"]["married_life_foundation"]["jaimini"]["upapada_lagna"]
    prompt = pipeline._build_instant_composer_prompt_v3(
        "How will be my married life?", composer, "english",
    )
    assert len(prompt) < 45_000
    assert "D1 House 7 and seventh-lord condition" in prompt
    assert "Give the Jaimini layer its own paragraph" in prompt
    contract = foundation["fact_contract"]
    assert pipeline._validate_married_life_fact_markers("missing", contract)
    assert pipeline._validate_married_life_fact_markers(
        " ".join(contract["required_markers"]), contract,
    ) == []


def test_live_reconnection_context_keeps_relationship_semantics_and_transit_evidence() -> None:
    birth = {
        "name": "ABC",
        "date": "1980-04-02",
        "time": "14:55:00",
        "latitude": 29.2396596,
        "longitude": 75.8174505,
        "timezone": "UTC+5:30",
        "place": "Hisar, Haryana, India",
    }
    intent = {
        "category": "relationship",
        "mode": "LIFESPAN_EVENT_TIMING",
        "answer_mode": "event_prediction",
        "time_relation": "future",
        "period_window": {
            "kind": "current",
            "start": "2026-09-07",
            "end": "2026-09-07",
            "request_semantics": "requested_period",
        },
        "evidence_plan": {
            "question_parts": [{"timeframe": {"kind": "open_future"}}],
            "evidence_needs": [
                {"kind": "future_dasha_event_windows"},
                {"kind": "transit_event_windows"},
            ],
        },
        "query_context": {"as_of": "2026-09-07T11:23:00+05:30"},
    }

    context = pipeline._build_instant_context(
        birth,
        "When will we start talking like before?",
        intent,
        [],
        answer_mode_override="event_prediction",
        target_subject_override={"key": "self", "label": "self", "base_house": 1},
    )

    verdict = context["normalized_evidence"]["event_timing_verdict"]
    assert context["intent_summary"]["category"] == "relationship"
    assert verdict["event_category"] == "relationship"
    assert verdict["answer_event_label"] == "relationship communication and reconnection"
    assert context["normalized_evidence"]["transit_activation_timeline"]["peak_windows"]
    assert context["normalized_evidence"]["kp_evidence"]["seventh_cusp"]["sub_lord"]

    marriage_intent = dict(intent)
    marriage_intent["category"] = "marriage"
    marriage_intent["evidence_plan"] = {
        **intent["evidence_plan"],
        "question_parts": [
            {
                "part_id": "marriage-outcome",
                "life_domain": "marriage",
                "event_profile": "marriage",
                "intent_families": ["topic_outlook"],
                "timeframe": {"kind": "open_future"},
            },
            {
                "part_id": "reconnection-timing",
                "life_domain": "relationship",
                "event_profile": "relationship_reconciliation",
                "intent_families": ["event_timing"],
                "timeframe": {"kind": "open_future"},
            },
        ],
    }
    context["intent_summary"]["category"] = "marriage"
    packet = build_instant_v2_packet(
        question="Will I marry my girlfriend, and when will we speak again?",
        intent=marriage_intent,
        answer_mode="event_prediction",
        target_subject={"key": "self", "label": "self", "base_house": 1},
        language="hinglish",
        instant_context=context,
    )
    packet = apply_live_graph_policy(packet, intent=marriage_intent, context=context)
    graph = packet["answer_spec"]["knowledge_graph_policy"]
    assert graph["runtime_key"] == "marriage_timing"
    assert graph["missing_required_factors"] == []
    assert graph["fallback_to_deeper_mode"] is False
    assert graph["specific_partner_scope"]["answer_rule"].startswith(
        "Answer every supported native-chart part first."
    )
    composer = pipeline._build_instant_composer_context(context, packet)
    assert composer["evidence"]["kp_evidence"]["seventh_cusp"]["sub_lord"]
    assert composer["answer_contract"]["knowledge_graph_policy"]["specific_partner_scope"]
    fitted = pipeline._fit_composer_brief(composer)
    assert fitted["evidence"]["kp_evidence"]["seventh_cusp"]["sub_lord"]
    assert fitted["query_plan"]["question_parts"]


def test_extended_marriage_subtypes_resolve_without_question_text_matching() -> None:
    cases = {
        "love_vs_arranged": "love_arranged_marriage",
        "remarriage": "remarriage",
        "engagement_vs_wedding": "engagement_wedding_timing",
        "spouse_meeting": "spouse_meeting",
        "spouse_details": "spouse_details",
        "affair": "affair_assessment",
        "current_relationship_state": "relationship_timing",
        "specific_partner_decision": "relationship_timing",
    }
    for subtype, expected in cases.items():
        assert marriage_graph_runtime_key(
            "marriage",
            {"answer_mode": "topic_reading", "marriage_subtype": subtype},
        ) == expected


def test_current_relationship_state_is_forced_to_current_timing_evidence() -> None:
    intent = {
        "category": "relationship",
        "marriage_subtype": "current_relationship_state",
        "answer_mode": "topic_reading",
        "mode": "ANALYZE_TOPIC_POTENTIAL",
        "needs_transits": False,
        "extracted_context": {},
        "evidence_plan": {"question_parts": [], "evidence_needs": []},
    }

    apply_marriage_routing_guards(intent)

    assert intent["answer_mode"] == "timing_window"
    assert intent["mode"] == "PREDICT_PERIOD_OUTLOOK"
    assert intent["needs_transits"] is True
    assert intent["divisional_charts"] == ["D1", "D9"]
    assert intent["evidence_plan"]["question_parts"][0]["event_profile"] == "relationship_current_state"
    assert {
        row["kind"] for row in intent["evidence_plan"]["evidence_needs"]
    }.issuperset({"current_dasha_stack", "transit_event_windows"})


def test_specific_person_choice_overrides_affair_and_keeps_only_native_timing() -> None:
    intent = {
        "category": "relationship",
        "marriage_subtype": "affair",
        "third_party_decision_request": True,
        "answer_mode": "problem_diagnosis",
        "mode": "ANALYZE_TOPIC_POTENTIAL",
        "needs_transits": False,
        "extracted_context": {},
        "evidence_plan": {"question_parts": [], "evidence_needs": []},
    }

    apply_marriage_routing_guards(intent)

    assert intent["marriage_subtype"] == "specific_partner_decision"
    assert intent["answer_mode"] == "event_prediction"
    assert intent["mode"] == "LIFESPAN_EVENT_TIMING"
    assert intent["needs_transits"] is True
    assert intent["evidence_plan"]["question_parts"][0]["event_profile"] == "specific_partner_decision"
    assert {
        row["kind"] for row in intent["evidence_plan"]["evidence_needs"]
    }.issuperset({"future_dasha_event_windows", "transit_event_windows"})
    assert "another person's acceptance" in intent["extracted_context"]["requested_fact"]


def test_spouse_appearance_facet_resolves_before_generic_spouse_profile() -> None:
    plan = {
        "question": "How will they look like?",
        "answer_mode": "relationship_person",
        "marriage_subtype": "spouse_details",
        "special_flow": {"spouse_detail_scope": "appearance"},
    }
    assert marriage_graph_runtime_key("marriage", plan) == "spouse_appearance"

    fallback_plan = {
        "question": "How will they look like?",
        "answer_mode": "relationship_person",
        "marriage_subtype": "general",
        "special_flow": {},
    }
    assert marriage_graph_runtime_key("spouse", fallback_plan) == "spouse_profile"

    inherited_context_plan = {
        "question": "How will they look?",
        "answer_mode": "relationship_person",
        "marriage_subtype": "spouse_details",
        "target_subject": {"key": "spouse", "label": "spouse"},
        "special_flow": {"spouse_detail_scope": "appearance"},
    }
    assert marriage_graph_runtime_key("general", inherited_context_plan) == "spouse_appearance"


def test_spouse_location_facet_resolves_before_umbrella_spouse_details() -> None:
    plan = {
        "question": "Does my spouse appear connected with a different city, culture or background?",
        "answer_mode": "relationship_person",
        "marriage_subtype": "spouse_details",
        "target_subject": {"key": "spouse", "label": "spouse"},
        "special_flow": {"spouse_detail_scope": "location"},
    }
    assert marriage_graph_runtime_key("marriage", plan) == "spouse_location"
    assert marriage_graph_runtime_key(
        "marriage", {"answer_mode": "remedy_action", "marriage_subtype": "general"}
    ) == "marriage_remedies"


def test_marriage_muhurat_resolves_from_dedicated_flow_even_with_muhurat_category() -> None:
    plan = {
        "category": "muhurat",
        "answer_mode": "dedicated_muhurat_flow",
        "special_flow": {"muhurat_event_type": "marriage"},
    }
    assert marriage_graph_runtime_key("muhurat", plan) == "marriage_muhurat"


def test_marriage_remedy_query_plan_discards_incidental_forecast_horizon() -> None:
    plan = build_query_plan(
        question="Which calculated remedy is most relevant for recurring marital conflict?",
        intent={
            "category": "marriage",
            "explicit_remedy_request": True,
            "extracted_context": {"timeframe": "next three years"},
        },
        answer_mode="remedy_action",
        target_subject={"key": "self", "label": "self"},
        language="english",
    )
    assert plan["time_scope"]["relation"] == "static"
    assert plan["time_scope"]["horizon_end"] is None
    assert plan["time_scope"]["is_exact_day"] is False


def test_query_plan_preserves_semantic_marriage_subtype_and_prior_context() -> None:
    plan = build_query_plan(
        question="ignored by typed planner",
        intent={
            "category": "marriage",
            "marriage_subtype": "remarriage",
            "extracted_context": {"prior_marriage_context": "divorced; decree final"},
        },
        answer_mode="event_prediction",
        target_subject={"key": "self", "label": "self"},
        language="english",
        as_of="2026-08-26",
    )
    assert plan["marriage_subtype"] == "remarriage"
    assert plan["prior_marriage_context"] == "divorced; decree final"


def test_past_tense_love_arranged_question_is_not_retrospective_event_timing() -> None:
    plan = build_query_plan(
        question="Did I have a love or arranged marriage?",
        intent={
            "category": "marriage",
            "marriage_subtype": "love_vs_arranged",
            "time_relation": "past",
            "evidence_plan": {
                "question_parts": [{
                    "event_profile": "marriage",
                    "timeframe": {"kind": "open_past"},
                }],
                "evidence_needs": [
                    {"kind": "natal_topic_foundation"},
                    {"kind": "divisional_confirmation"},
                ],
            },
        },
        answer_mode="comparison_choice",
        target_subject={"key": "self", "label": "self"},
        language="english",
        as_of="2026-08-26",
    )

    assert plan["marriage_subtype"] == "love_vs_arranged"
    assert plan["time_scope"]["relation"] == "past"
    assert plan["time_scope"]["retrospective"] is False
    assert "historical_dasha_event_windows" not in plan["requested_evidence"]
    assert "historical_transit_event_windows" not in plan["requested_evidence"]


def test_retrospective_marriage_plan_resolves_to_history_route() -> None:
    plan = {
        "answer_mode": "event_prediction",
        "time_scope": {"relation": "past", "retrospective": True},
    }
    assert marriage_graph_runtime_key("marriage", plan) == "marriage_history"
    assert MarriageGraphPolicyStore().resolve("marriage_history") is not None


def test_marriage_graph_inputs_follow_final_query_plan() -> None:
    query_plan = {"category": "separation", "answer_mode": "timing_window"}
    assert resolve_marriage_graph_inputs(
        intent={"category": "marriage", "answer_mode": "topic_reading"},
        context={"intent_summary": {"category": "relationship"}},
        query_plan=query_plan,
    ) == {
        "category": "separation",
        "query_plan": query_plan,
        "observed_answer_mode": "timing_window",
    }


def test_marriage_runtime_exposes_authored_tree_and_route_metadata() -> None:
    result = compare_marriage_graph_policy(
        category="marriage",
        query_plan={"answer_mode": "event_prediction"},
        observed_answer_mode="event_prediction",
        context={},
    )
    assert result is not None
    assert result["runtime_key"] == "marriage_timing"
    assert result["graph_tree"]["children"][0]["label"] == "Marriage likelihood and timing"
    assert "marriage:D1" in result["missing_required_factors"]
    review = build_marriage_graph_route(result)
    assert review is not None
    assert review["question_type"] == "Marriage likelihood and timing"
    assert review["status"] == "review_needed"


def test_static_marriage_does_not_select_background_timing() -> None:
    context = {
        "intent_summary": {"category": "marriage"},
        "normalized_evidence": {"natal_promise": {"status": "supported"}, "divisional_specifics": {"d9": "supportive"}},
        "current_dashas": {"levels": {"MD": "Saturn"}},
        "current_transits": {"planets": {"Saturn": {"house": 7}}},
    }
    result = compare_marriage_graph_policy(
        category="marriage", query_plan={"answer_mode": "potential_capacity"},
        observed_answer_mode="potential_capacity", context=context,
    )
    assert result is not None
    assert result["unexpected_default_exclusions"] == []
    assert "marriage:DashaActivation" not in result["observed_factors"]
    assert "marriage:TransitConfirmation" not in result["observed_factors"]
    assert result["match"] is True


def test_instant_chat_response_returns_marriage_graph_route(monkeypatch) -> None:
    class Analyzer:
        def get_named_gemini_model(self, model_name, premium_analysis=False):
            return {"model": model_name}

        async def generate_text_from_prompt(self, prompt, **kwargs):
            return {
                "success": True,
                "response": "Marriage is supported conditionally. Are you currently in a relationship?",
                "chat_llm_model": kwargs.get("model_name_override"),
                "token_usage": {"input_tokens": 10, "output_tokens": 10},
            }

    context = {
        "birth_summary": {"name": "Test"},
        "intent_summary": {"category": "marriage", "answer_mode": "potential_capacity"},
        "normalized_evidence": {
            "natal_promise": {"status": "supported"},
            "divisional_specifics": {"d9": "supportive"},
        },
        "recent_history": [],
    }
    packet = {
        "query_plan": {"category": "marriage", "answer_mode": "potential_capacity", "language": "english"},
        "verdict": {"direction": "supported_natal_promise", "confidence": 0.8},
        "answer_spec": {"max_words": 120, "answer_order": ["direct_answer", "follow_up"]},
        "evidence_ledger": {"records": []}, "verification": {"passed": True},
    }
    monkeypatch.setattr(pipeline, "_build_instant_context", lambda **kwargs: context)
    monkeypatch.setattr(pipeline, "build_instant_v2_packet", lambda **kwargs: packet)
    monkeypatch.setattr(pipeline, "get_instant_chat_llm_provider", lambda: "gemini")
    monkeypatch.setattr(pipeline, "get_instant_chat_model", lambda: "models/gemini-flash-lite-test")
    monkeypatch.setattr(pipeline, "finalize_instant_v2_packet", lambda current, answer: current)

    result = asyncio.run(pipeline.generate_instant_chat_response(
        Analyzer(), question="Is marriage possible in my kundali?", birth_data={"name": "Test"},
        intent={"category": "marriage", "answer_mode": "potential_capacity", "target_subject_key": "self"},
        history=[], language="english",
    ))

    debug = result["instant_evidence_debug"]
    route = debug["user_derivation"]["marriage_graph_route"]
    assert route["domain"] == "marriage"
    assert route["live"] is True
    assert route["runtime_key"] == "marriage_promise"
    assert route["graph_tree"]["children"][0]["label"] == "Marriage promise in the natal chart"
    assert any(item["domain"] == "marriage" for item in debug["user_derivation"]["knowledge_graph_routes"])
    assert debug["knowledge_graph_policy"]["enforcement"] == "authoritative_pre_generation"
    assert debug["answer_spec"]["knowledge_graph_policy"]["live"] is True
