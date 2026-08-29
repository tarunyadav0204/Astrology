from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from ai.intent_router import IntentRouter, apply_children_routing_guards  # noqa: E402
from calculators.chart_calculator import ChartCalculator  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _build_instant_context,
    _historical_children_candidate_pool,
    _instant_real_chart_facts,
    _instant_real_kp_evidence,
    _is_retrospective_event_request,
    _rank_historical_event_periods,
    _requested_charts_from_intent,
)
from instant_chat_v2.children import BOUNDARY_CHILDREN_SUBTYPES, CHILDREN_PROFILES, TIMING_CHILDREN_SUBTYPES, children_profile  # noqa: E402
from instant_chat_v2.children_calculation import _house_condition, build_children_foundation  # noqa: E402
from instant_chat_v2.children_graph_policy import ChildrenGraphPolicyStore  # noqa: E402
from instant_chat_v2.children_graph_runtime import children_graph_runtime_key, compare_children_graph_policy  # noqa: E402
from instant_chat_v2.graph_live import apply_live_graph_policy, enforce_live_graph_answer  # noqa: E402
from instant_chat_v2.planner import build_query_plan  # noqa: E402


EXPECTED_KEYS = set(CHILDREN_PROFILES)
TIMED_KEYS = set(TIMING_CHILDREN_SUBTYPES)

# Public acceptance questions.  The semantic router must select the tuple's
# subtype/mode; downstream routing may not collapse these into one progeny path.
QUESTION_MATRIX = [
    ("What does my chart show about children and parenthood?", "children_overview", "topic_reading", "children_overview"),
    ("Is parenthood an important theme in my life?", "children_overview", "potential_capacity", "children_overview"),
    ("What kind of parent might I become?", "parenthood_capacity", "potential_capacity", "parenthood_capacity"),
    ("Does my chart support natural conception?", "conception_capacity", "potential_capacity", "conception_capacity"),
    ("Is conception likely to be delayed?", "conception_capacity", "potential_capacity", "conception_capacity"),
    ("When is my next supportive period for conception?", "conception_capacity", "event_prediction", "conception_timing"),
    ("Which months next year support conception?", "conception_timing", "event_prediction", "conception_timing"),
    ("When is childbirth most strongly supported?", "childbirth_timing", "event_prediction", "childbirth_timing"),
    ("Could conception this year lead to childbirth next year?", "childbirth_timing", "event_prediction", "childbirth_timing"),
    ("Is the promise for a first child strong?", "first_child_capacity", "potential_capacity", "first_child_capacity"),
    ("When is my first child most likely?", "first_child_capacity", "event_prediction", "first_child"),
    ("Does my chart support a second child?", "subsequent_child_capacity", "potential_capacity", "subsequent_child_capacity"),
    ("When is the next supportive period for a second child?", "subsequent_child_capacity", "event_prediction", "subsequent_child"),
    ("Does my chart support another child after a long gap?", "subsequent_child_capacity", "potential_capacity", "subsequent_child_capacity"),
    ("Is my chart more supportive of a small or larger family?", "family_size_tendency", "potential_capacity", "family_size_tendency"),
    ("Does my chart support twins?", "family_size_tendency", "potential_capacity", "family_size_tendency"),
    ("What is the main astrological reason for delayed parenthood?", "children_delay_diagnosis", "problem_diagnosis", "children_delay_diagnosis"),
    ("Does my chart show denial or only postponement?", "children_delay_diagnosis", "problem_diagnosis", "children_delay_diagnosis"),
    ("Does my chart support assisted conception?", "assisted_conception", "decision_support", "assisted_conception"),
    ("Is IVF astrologically supported for me?", "assisted_conception", "potential_capacity", "assisted_conception"),
    ("Which months are supportive for an IVF cycle?", "assisted_conception", "event_prediction", "assisted_conception_timing"),
    ("Does my chart support adoption?", "adoption_pathway", "potential_capacity", "adoption_pathway"),
    ("Is adoption stronger than biological parenthood?", "adoption_pathway", "potential_capacity", "adoption_pathway"),
    ("When should I begin an adoption process?", "adoption_pathway", "event_prediction", "adoption_timing"),
    ("Does my chart support becoming a step-parent?", "step_parenthood", "potential_capacity", "step_parenthood"),
    ("Is this a supportive stage for becoming a parent?", "parenthood_decision", "decision_support", "parenthood_decision"),
    ("Should I try now or wait?", "parenthood_decision", "decision_support", "parenthood_decision"),
    ("Should I prioritise parenthood or career growth?", "parenthood_vs_career", "decision_support", "parenthood_vs_career"),
    ("Is this a better year for parenthood or professional expansion?", "parenthood_vs_career", "event_prediction", "parenthood_vs_career_timing"),
    ("Why do my child and I frequently clash?", "parent_child_relationship", "problem_diagnosis", "parent_child_relationship"),
    ("What parenting pattern do I repeat?", "parent_child_relationship", "problem_diagnosis", "parent_child_relationship"),
    ("When is communication with my child likely to improve?", "parent_child_reconciliation_timing", "event_prediction", "parent_child_reconciliation_timing"),
    ("Which past periods were most likely for childbirth?", "retrospective_child_timing", "event_prediction", "retrospective_child_timing"),
    ("When was my first child born?", "retrospective_child_timing", "event_prediction", "retrospective_child_timing"),
    ("Which calculated remedy is relevant for delayed conception?", "children_remedy", "remedy_action", "children_remedy"),
    ("What remedy supports my relationship with my child?", "children_remedy", "remedy_action", "children_remedy"),
    ("Do our charts jointly support having children?", "two_chart_children_handoff", "dedicated_partnership_flow", "two_chart_children_handoff"),
    ("What career will my child choose?", "child_chart_required_handoff", "handoff", "child_chart_required_handoff"),
    ("Will my child be healthy?", "child_chart_required_handoff", "handoff", "child_chart_required_handoff"),
    ("Will my pregnancy be healthy?", "medical_safety_handoff", "handoff", "medical_safety_handoff"),
    ("Will I miscarry again?", "medical_safety_handoff", "handoff", "medical_safety_handoff"),
    ("Is this pregnancy symptom dangerous?", "medical_safety_handoff", "handoff", "medical_safety_handoff"),
    ("Which embryo-transfer date has the cleanest Panchang?", "muhurat_handoff", "dedicated_muhurat_flow", "muhurat_handoff"),
    ("Will I get custody of my child?", "legal_custody_handoff", "handoff", "legal_custody_handoff"),
    ("Will I have a son or daughter?", "fetal_sex_refusal", "safety_refusal", "fetal_sex_refusal"),
]


def _required_houses(key: str) -> list[int]:
    return [int(value.split("H", 1)[1]) for value in ChildrenGraphPolicyStore().require(key).required_factors if value.startswith("children:H")]


def _context(key: str, *, timing: bool = False) -> dict:
    policy = ChildrenGraphPolicyStore().require(key)
    boundary = key in BOUNDARY_CHILDREN_SUBTYPES
    availability = {
        "d1": not boundary, "d7": not boundary,
        "d10": "children:D10" in policy.required_factors,
        "jupiter_karaka": "children:JupiterKaraka" in policy.required_factors,
        "lord_nakshatra_chain": "children:LordNakshatraChain" in policy.required_factors,
        "child_order_frame": "children:ChildOrderFrame" in policy.required_factors,
        "kp_fructification": "children:KPFructification" in policy.required_factors,
        "remedy_blueprint": "children:RemedyBlueprint" in policy.required_factors,
        "scope_boundary": boundary,
    }
    context = {
        "intent_summary": {"category": "progeny", "children_subtype": key},
        "normalized_evidence": {"children_foundation": {
            "children_subtype": key, "houses_available": _required_houses(key),
            "availability": availability, "route_synthesis": {"verdict": "qualified"},
        }},
    }
    if timing:
        context["current_dashas"] = {"levels": {"MD": {"planet": "Jupiter"}}}
        context["current_transits"] = {"planets": {"Jupiter": {"house": 5}}}
    return context


def test_children_ontology_compiles_and_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_children_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Children, Parenthood and Progeny ontology PoC valid: 29 competency questions" in result.stdout


def test_bundle_covers_every_typed_route_with_expandable_factor_children() -> None:
    store = ChildrenGraphPolicyStore()
    assert set(store.runtime_keys()) == EXPECTED_KEYS
    assert len(EXPECTED_KEYS) == 29
    for key in EXPECTED_KEYS:
        question = store.require(key).graph_tree["children"][0]
        stages = next(node for node in question["children"] if node["label"] == "Decision stages")
        assert stages["children"], key
        for stage in stages["children"]:
            factors = next(node for node in stage["children"] if node["label"] == "Required astrology factors")
            assert factors["children"], (key, stage["label"])


def test_every_acceptance_question_has_an_explicit_route() -> None:
    for question, subtype, mode, expected in QUESTION_MATRIX:
        actual = children_graph_runtime_key("progeny", {"children_subtype": subtype, "answer_mode": mode})
        assert actual == expected, question
        ChildrenGraphPolicyStore().require(actual)


def test_static_timing_and_boundary_contracts_do_not_bleed_into_each_other() -> None:
    store = ChildrenGraphPolicyStore()
    for key in EXPECTED_KEYS - TIMED_KEYS - set(BOUNDARY_CHILDREN_SUBTYPES):
        exclusions = set(store.require(key).default_exclusions)
        assert {"children:DashaActivation", "children:TransitConfirmation"}.issubset(exclusions), key
    for key in TIMED_KEYS:
        required = set(store.require(key).required_factors)
        assert {"children:KPFructification", "children:DashaActivation", "children:TransitConfirmation"}.issubset(required), key
        assert "children:NoNodeFifthNinth" in store.require(key).guardrails
    for key in BOUNDARY_CHILDREN_SUBTYPES:
        policy = store.require(key)
        assert policy.required_factors == ("children:ScopeBoundary",)
        assert all("CapNatal" not in value and "CapD7" not in value for value in policy.required_capabilities)


def test_first_and_subsequent_child_routes_are_materially_distinct() -> None:
    assert children_profile("progeny", "first_child_capacity")["houses"] == [5, 2, 11]
    assert 7 in children_profile("progeny", "subsequent_child_capacity")["houses"]
    assert 9 in children_profile("progeny", "subsequent_child_capacity")["houses"]
    first = set(ChildrenGraphPolicyStore().require("first_child_capacity").required_factors)
    later = set(ChildrenGraphPolicyStore().require("subsequent_child_capacity").required_factors)
    assert "children:H5" in first
    assert {"children:H7", "children:H9"}.issubset(later)
    assert first != later


def test_conception_childbirth_assisted_and_adoption_use_different_chains() -> None:
    store = ChildrenGraphPolicyStore()
    conception = set(store.require("conception_timing").required_factors)
    childbirth = set(store.require("childbirth_timing").required_factors)
    assisted = set(store.require("assisted_conception_timing").required_factors)
    adoption = set(store.require("adoption_timing").required_factors)
    assert "children:H9" not in conception and "children:H9" in childbirth
    assert {"children:H6", "children:H8", "children:H12"}.issubset(assisted)
    assert {"children:H4", "children:H9"}.issubset(adoption)
    assert len({frozenset(conception), frozenset(childbirth), frozenset(assisted), frozenset(adoption)}) == 4


def test_routing_guard_requests_only_real_route_charts() -> None:
    intent = {"category": "pregnancy", "children_subtype": "conception_capacity"}
    apply_children_routing_guards(intent)
    assert intent["category"] == "progeny"
    assert intent["divisional_charts"] == ["D1", "D7"]
    assert _requested_charts_from_intent(intent, answer_mode="potential_capacity") == ["D1", "D7"]
    decision = {"category": "children", "children_subtype": "parenthood_vs_career"}
    apply_children_routing_guards(decision)
    assert decision["divisional_charts"] == ["D1", "D7", "D10"]
    boundary = {"category": "pregnancy", "children_subtype": "medical_safety_handoff"}
    apply_children_routing_guards(boundary)
    assert boundary["route_action"] == "handoff"
    assert boundary["divisional_charts"] == []


def test_instant_finalizer_preserves_children_subtype_and_chart_contract() -> None:
    result = IntentRouter()._finalize_instant_router_result({
        "status": "READY", "mode": "ANALYZE_TOPIC_POTENTIAL", "category": "children",
        "children_subtype": "subsequent_child_capacity", "answer_mode": "potential_capacity",
        "needs_transits": False,
    }, current_year=2026, normalized_query_context=None)
    assert result["category"] == "progeny"
    assert result["children_subtype"] == "subsequent_child_capacity"
    assert result["divisional_charts"] == ["D1", "D7"]


def test_planner_carries_children_semantics_without_text_matching() -> None:
    plan = build_query_plan(
        question="Which route?", language="english", answer_mode="decision_support",
        target_subject={"key": "self", "label": "self"},
        intent={"category": "progeny", "children_subtype": "adoption_pathway"},
    )
    assert plan["category"] == "progeny"
    assert plan["children_subtype"] == "adoption_pathway"


def test_retrospective_child_timing_uses_progeny_ranking_not_marriage_ranking() -> None:
    intent = {
        "category": "progeny",
        "children_subtype": "retrospective_child_timing",
        "answer_mode": "event_prediction",
    }
    assert _is_retrospective_event_request(
        intent,
        answer_mode="event_prediction",
        category="progeny",
        question="When was my first child born?",
    ) is True
    apply_children_routing_guards(intent)
    assert intent["needs_transits"] is True
    assert intent["time_relation"] == "past"
    plan = build_query_plan(
        question="When was my first child born?", language="english",
        answer_mode="event_prediction", target_subject={"key": "self", "label": "self"},
        intent=intent,
    )
    assert plan["time_scope"]["retrospective"] is True
    rows = [
        {
            "start": "2004-01-01", "end": "2005-01-01",
            "mahadasha": "Saturn", "antardasha": "Moon", "pratyantardasha": "Jupiter",
            "activated_focus_houses": [2, 5, 11], "relevance_score": 20,
            "transit_trigger_score": 6,
            "peak_activation_windows": [{"start": "2004-06-01", "end": "2004-07-01", "trigger_score": 6, "activated_focus_houses": [5, 11]}],
        },
        {
            "start": "2007-01-01", "end": "2008-01-01",
            "mahadasha": "Venus", "antardasha": "Venus", "pratyantardasha": "Venus",
            "activated_focus_houses": [7], "relevance_score": 30,
            "transit_trigger_score": 0, "peak_activation_windows": [],
        },
    ]
    pooled = _historical_children_candidate_pool(rows, {"Moon": [5], "Venus": [7]})
    ranked = _rank_historical_event_periods(
        pooled, {"Moon": [5], "Venus": [7]}, event_kind="children"
    )
    assert ranked[0]["antardasha"] == "Moon"
    assert "historical_children_rank_score" in ranked[0]
    assert "historical_marriage_rank_score" not in ranked[0]
    assert "child-event-capable" in ranked[0]["claim_rule"]
    assert "marriage-capable" not in ranked[0]["claim_rule"]


def test_reference_chart_retrospective_child_pipeline_keeps_children_semantics() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    intent = {
        "category": "progeny", "children_subtype": "retrospective_child_timing",
        "answer_mode": "event_prediction", "time_relation": "past",
        "query_context": {"as_of": "2026-08-29T12:00:00+05:30"},
    }
    apply_children_routing_guards(intent)
    context = _build_instant_context(
        birth, "When was my first child born?", intent, [],
        answer_mode_override="event_prediction",
    )
    normalized = context["normalized_evidence"]
    assert context["intent_summary"]["time_relation"] == "past"
    assert context["intent_summary"]["focus_houses"] == [2, 5, 11]
    assert "D1-D7 progeny promise" in normalized["timing_policy"]["rule"]
    assert "marriage" not in normalized["timing_policy"]["rule"].lower()
    scan = normalized["historical_event_dasha_scan"]
    assert scan["ranking_method"] == "children_2_5_11_jupiter_d7_then_historical_transit"
    assert "marriage" not in scan["claim_rule"].lower()
    for row in scan["periods"]:
        assert "historical_children_rank_score" in row
        assert "historical_marriage_rank_score" not in row
    foundation = normalized["children_foundation"]
    assert foundation["children_subtype"] == "retrospective_child_timing"
    assert foundation["availability"]["d1"] is True
    assert foundation["availability"]["d7"] is True


def test_reference_chart_children_remedy_pipeline_uses_real_remedy_engine() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    intent = {
        "category": "progeny", "children_subtype": "children_remedy",
        "answer_mode": "remedy_action", "query_context": {"as_of": "2026-08-29T12:00:00+05:30"},
    }
    apply_children_routing_guards(intent)
    context = _build_instant_context(
        birth, "Which calculated remedy is relevant for delayed conception?", intent, [],
        answer_mode_override="remedy_action",
    )
    normalized = context["normalized_evidence"]
    blueprint = normalized["remedy_blueprint"]
    assert blueprint["top_recommendation"]
    foundation = normalized["children_foundation"]
    assert foundation["availability"]["remedy_blueprint"] is True
    assert foundation["route_synthesis"]["calculated"] is True
    assert foundation["route_synthesis"]["top_recommendation"] == blueprint["top_recommendation"]


def test_complete_foundation_matches_every_graph_route() -> None:
    modes = {key: "event_prediction" if key in TIMED_KEYS else "handoff" if key in BOUNDARY_CHILDREN_SUBTYPES else "remedy_action" if key == "children_remedy" else "problem_diagnosis" if key in {"children_delay_diagnosis", "parent_child_relationship"} else "decision_support" if key in {"assisted_conception", "parenthood_decision", "parenthood_vs_career"} else "potential_capacity" for key in EXPECTED_KEYS}
    modes["children_overview"] = "topic_reading"
    modes["fetal_sex_refusal"] = "safety_refusal"
    for key, mode in modes.items():
        comparison = compare_children_graph_policy(
            category="progeny", query_plan={"category": "progeny", "children_subtype": key, "answer_mode": mode},
            observed_answer_mode=mode, context=_context(key, timing=key in TIMED_KEYS),
        )
        assert comparison and comparison["runtime_key"] == key
        assert comparison["match"] is True, (key, comparison["mismatches"])


def test_live_graph_is_authoritative_for_calculation_and_boundary_routes() -> None:
    for key, mode in (("conception_capacity", "potential_capacity"), ("conception_timing", "event_prediction"), ("medical_safety_handoff", "handoff")):
        packet = {"query_plan": {"category": "progeny", "children_subtype": key, "answer_mode": mode}, "verdict": {}, "answer_spec": {}, "verification": {}}
        resolved = apply_live_graph_policy(packet, intent=packet["query_plan"], context=_context(key, timing=key in TIMED_KEYS))
        policy = resolved["answer_spec"]["knowledge_graph_policy"]
        assert policy["live"] is True
        assert policy["domain"] == "children"
        assert policy["runtime_key"] == key


def test_boundary_answers_fail_closed_even_if_writer_hallucinates() -> None:
    expected_phrases = {
        "fetal_sex_refusal": "can’t predict or imply",
        "medical_safety_handoff": "cannot determine whether a pregnancy is healthy",
        "two_chart_children_handoff": "needs both resolved birth charts",
        "child_chart_required_handoff": "need the child’s own chart",
        "muhurat_handoff": "dedicated Muhurat",
        "legal_custody_handoff": "cannot guarantee custody",
    }
    for key, phrase in expected_phrases.items():
        packet = {"query_plan": {"category": "progeny", "children_subtype": key, "answer_mode": "safety_refusal" if key == "fetal_sex_refusal" else "handoff"}, "verdict": {}, "answer_spec": {}, "verification": {}}
        resolved = apply_live_graph_policy(packet, intent=packet["query_plan"], context=_context(key))
        answer = enforce_live_graph_answer("A fabricated astrological certainty.", resolved)
        assert phrase in answer
        assert "fabricated" not in answer


def test_reference_chart_produces_individualized_evidence_for_all_calculated_routes() -> None:
    birth = {"name": "Tarun", "date": "1980-04-02", "time": "14:55:00", "latitude": 29.2396596, "longitude": 75.8174505, "timezone": "UTC+5:30", "place": "Hisar, Haryana, India"}
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    facts = _instant_real_chart_facts(chart_data=chart, requested_charts=["D1", "D7", "D10"], requested_fact=None, karaka_evidence={}, d1_snapshot={})
    normalized = {
        "chart_facts": facts,
        "forward_event_dasha_scan": {"ranked_windows": [{"start": "2027-01-01", "end": "2027-03-31", "active_houses": list(range(1, 13)), "score": 5}]},
        "historical_event_dasha_scan": {"periods": [{"start": "2005-01-01", "end": "2005-12-31", "active_houses": [2, 5, 11], "score": 5}]},
        "remedy_blueprint": {"top_recommendation": {"id": "calculated_children_support", "label": "Calculated support practice"}, "alternatives": []},
    }
    kp = _instant_real_kp_evidence(birth)
    modes = {key: "event_prediction" if key in TIMED_KEYS else "remedy_action" if key == "children_remedy" else "problem_diagnosis" if key in {"children_delay_diagnosis", "parent_child_relationship"} else "decision_support" if key in {"assisted_conception", "parenthood_decision", "parenthood_vs_career"} else "potential_capacity" for key in EXPECTED_KEYS - set(BOUNDARY_CHILDREN_SUBTYPES)}
    for subtype, mode in modes.items():
        foundation = build_children_foundation(chart_data=chart, normalized_evidence=normalized, category="progeny", answer_mode=mode, children_subtype=subtype, kp_evidence=kp)
        route = foundation["route_synthesis"]
        assert route
        assert route.get("verdict") or route.get("direction"), subtype
        assert foundation["availability"]["d1"] is True
        assert foundation["availability"]["d7"] is True
        assert foundation["lord_nakshatra_chains"]
        assert all(row["lord_nakshatra"] and row["nakshatra_lord"] for row in foundation["lord_nakshatra_chains"]), subtype
        assert all("chain_score" in row for row in foundation["lord_nakshatra_chains"]), subtype
        assert route["nakshatra_qualification"]["available"] is True, subtype
        if route.get("house_lord_conditions"):
            assert set(route["chart_verdicts"]) == {"D1", "D7"}, subtype
        if subtype in TIMED_KEYS:
            assert route["kp_chain_available"] is True, subtype
            assert route["timing_verdict"] == "supportive_windows_found", subtype
            assert route["timing_windows"], subtype
        if subtype == "children_remedy":
            assert route["calculated"] is True


def test_calculator_bindings_are_concrete_and_no_route_is_a_placeholder() -> None:
    forbidden = {"placeholder", "todo", "coming soon", "not implemented"}
    for key in EXPECTED_KEYS:
        policy = ChildrenGraphPolicyStore().require(key)
        assert policy.calculator_bindings, key
        for binding in policy.calculator_bindings.values():
            lower = str(binding).lower()
            assert lower.strip()
            assert not any(token in lower for token in forbidden), (key, binding)


def test_high_risk_boundaries_and_aspect_policy_are_authored() -> None:
    store = ChildrenGraphPolicyStore()
    assert "children:NoMedicalDiagnosis" in store.require("medical_safety_handoff").guardrails
    assert "children:NoLossPrediction" in store.require("medical_safety_handoff").guardrails
    assert "children:NoSexPrediction" in store.require("fetal_sex_refusal").guardrails
    assert "children:ChildChartRequired" in store.require("child_chart_required_handoff").guardrails
    assert "children:TwoChartsRequired" in store.require("two_chart_children_handoff").guardrails
    assert "children:MuhuratSeparate" in store.require("muhurat_handoff").guardrails
    assert "children:LegalSeparate" in store.require("legal_custody_handoff").guardrails
    for key in TIMED_KEYS:
        assert "children:NoNodeFifthNinth" in store.require(key).guardrails


def test_children_house_ledger_keeps_node_occupation_conjunction_and_seventh_aspect_only() -> None:
    chart = {
        "houses": [
            {"house": house, "lord": "Venus", "occupants": []}
            for house in range(1, 13)
        ],
        "planets": {
            "Venus": {"house": 2, "dignity": "own_sign"},
            "Rahu": {"house": 1},
        },
    }
    h5 = _house_condition("D1", chart, 5)
    h7 = _house_condition("D1", chart, 7)
    h9 = _house_condition("D1", chart, 9)
    assert not any(row["planet"] == "Rahu" for row in h5["aspects"])
    assert any(row["planet"] == "Rahu" for row in h7["aspects"])
    assert not any(row["planet"] == "Rahu" for row in h9["aspects"])
