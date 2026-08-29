from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.graph_live import apply_live_graph_policy  # noqa: E402
from instant_chat_v2.graph_live import enforce_live_graph_answer  # noqa: E402
from instant_chat_v2.methodology import get_methodology  # noqa: E402
from instant_chat_v2.orchestrator import build_instant_v2_packet  # noqa: E402
from instant_chat_v2.planner import build_query_plan  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _build_instant_answer_blueprint,
    _build_instant_composer_context,
    _build_instant_context,
    _compact_answer_spec_for_composer,
    _compact_wealth_foundation,
    _mode_selection_from_intent,
)
from calculators.chart_calculator import ChartCalculator  # noqa: E402
from instant_chat_v2.wealth_graph_policy import WealthGraphPolicyStore  # noqa: E402
from instant_chat_v2.wealth_graph_runtime import (  # noqa: E402
    compare_wealth_graph_policy,
    effective_wealth_category,
    observed_wealth_factors,
    wealth_graph_runtime_key,
)


EXPECTED_KEYS = {
    "wealth", "wealth_source", "wealth_diagnosis", "wealth_timing",
    "income", "income_timing", "multiple_income",
    "debt", "debt_diagnosis", "debt_repayment", "loan_support", "loan_decision",
    "investment", "investing_vs_trading", "investment_timing", "investment_risk",
    "loss_vulnerability", "inheritance", "inheritance_timing", "windfall", "wealth_remedies",
}


def _foundation_context(*, timing: bool = False):
    context = {
        "intent_summary": {"category": "wealth", "answer_mode": "topic_reading"},
        "normalized_evidence": {"wealth_foundation": {
            "d1_available": True,
            "houses_available": [2, 5, 6, 7, 8, 9, 10, 11, 12],
            "availability": {
                "d2": True, "d5": True, "d8": True, "d9": True, "d10": True,
                "lord_nakshatra_chain": True, "dignity_strength": True,
                "dhana_yogas": True, "indu_lagna": True, "hora_lagna": True,
                "arudha_gains": True, "kp_fructification": True,
                "remedy_blueprint": True,
            },
            "d2_synthesis": {
                "verdict": "mixed_capacity_with_retention_pressure",
            },
            "route_adjudication": {
                "direction": "supported_but_qualified",
                "strength_claim_permission": "qualified_only",
                "d2_verdict": "mixed_capacity_with_retention_pressure",
            },
        }},
    }
    if timing:
        context["current_dashas"] = {"levels": {"MD": {"planet": "Jupiter"}}}
        context["current_transits"] = {"planets": {"Jupiter": {"house": 11}}}
    return context


def test_wealth_ontology_compiles_and_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_wealth_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Wealth and Finance ontology PoC valid: 21 competency questions" in result.stdout


def test_compiled_bundle_covers_all_twenty_one_routes() -> None:
    assert set(WealthGraphPolicyStore().runtime_keys()) == EXPECTED_KEYS


def test_every_route_has_expandable_decision_stages_and_factor_children() -> None:
    store = WealthGraphPolicyStore()
    for runtime_key in store.runtime_keys():
        question = store.require(runtime_key).graph_tree["children"][0]
        stages = next(node for node in question["children"] if node["label"] == "Decision stages")
        assert stages["children"], runtime_key
        for stage in stages["children"]:
            factors = next(node for node in stage["children"] if node["label"] == "Required astrology factors")
            assert factors["children"], f"{runtime_key}/{stage['label']}"


def test_static_routes_exclude_timing_and_timed_routes_require_both_layers() -> None:
    store = WealthGraphPolicyStore()
    for key in EXPECTED_KEYS - {"wealth_timing", "income_timing", "debt_repayment", "investment_timing", "inheritance_timing", "loan_support", "loan_decision"}:
        policy = store.require(key)
        assert {"wealth:DashaActivation", "wealth:TransitConfirmation"}.issubset(policy.default_exclusions)
    for key in {"wealth_timing", "income_timing", "debt_repayment", "investment_timing", "inheritance_timing", "loan_support", "loan_decision"}:
        policy = store.require(key)
        assert {"wealth:DashaActivation", "wealth:TransitConfirmation"}.issubset(policy.required_factors)
        assert "wealth:StrictHorizon" in policy.guardrails


def test_indu_lagna_supports_but_never_overrides_d1_and_d2() -> None:
    store = WealthGraphPolicyStore()
    for key in ("wealth", "wealth_source", "wealth_timing"):
        factors = set(store.require(key).required_factors)
        assert {"wealth:D1", "wealth:D2", "wealth:InduLagna"}.issubset(factors)
        assert "wealth:InduNoOverride" in store.require(key).guardrails


def test_every_investment_route_requires_full_carrier_condition_and_supporting_d9() -> None:
    store = WealthGraphPolicyStore()
    for key in (
        "investment", "investing_vs_trading", "investment_timing",
        "investment_risk", "loss_vulnerability", "windfall",
    ):
        policy = store.require(key)
        assert {"wealth:D5", "wealth:D9"}.issubset(policy.required_factors), key
        assert "wealth:RuleCarrierCondition" in policy.decision_rules, key
        assert "wealth:NoSinglePlacementVerdict" in policy.guardrails, key


def test_financial_safety_guardrails_are_compiled() -> None:
    store = WealthGraphPolicyStore()
    assert "wealth:NoSecurityRecommendation" in store.require("investment").guardrails
    assert "wealth:NoGuaranteedReturn" in store.require("investment_timing").guardrails
    assert "wealth:NoDeathPrediction" in store.require("inheritance").guardrails
    assert "wealth:NoWindfallCertainty" in store.require("windfall").guardrails
    assert "wealth:NoGenericRemedy" in store.require("wealth_remedies").guardrails
    for key in ("wealth_timing", "income_timing", "debt_repayment", "loan_support", "loan_decision", "investment_timing", "inheritance_timing"):
        assert "wealth:NoNodeFifthNinth" in store.require(key).guardrails


def test_semantic_subtypes_and_modes_resolve_to_specific_routes() -> None:
    cases = [
        ("wealth", "topic_reading", "source", "wealth_source"),
        ("wealth", "problem_diagnosis", "savings_instability", "wealth_diagnosis"),
        ("income", "potential_capacity", "multiple_income", "multiple_income"),
        ("wealth", "potential_capacity", "multiple_income", "multiple_income"),
        ("debt", "decision_support", "loan_support", "debt"),
        ("debt", "timing_window", "debt_repayment", "debt_repayment"),
        ("wealth", "event_prediction", "debt_repayment", "debt_repayment"),
        ("debt", "timing_window", "loan_support", "loan_support"),
        ("debt", "event_prediction", "loan_decision", "loan_decision"),
        ("investment", "comparison_choice", "investing_vs_trading", "investing_vs_trading"),
        ("investment", "problem_diagnosis", "investment_risk", "investment_risk"),
        ("wealth", "potential_capacity", "windfall", "windfall"),
        ("wealth", "remedy_action", "general", "wealth_remedies"),
        ("wealth", "potential_capacity", "general", "wealth"),
    ]
    for category, mode, subtype, expected in cases:
        assert wealth_graph_runtime_key(category, {"answer_mode": mode, "wealth_subtype": subtype}) == expected


def test_descriptive_future_scope_does_not_convert_static_wealth_modes_to_timing() -> None:
    incidental_scope = {
        "requested": "long-term",
        "semantic": {"kind": "open_future"},
        "relation": "future",
        "as_of": "2026-08-27",
        "horizon_end": "2026-08-27",
        "is_exact_day": False,
    }
    cases = [
        ("wealth", "potential_capacity", "general", "wealth"),
        ("wealth", "potential_capacity", "source", "wealth_source"),
        ("wealth", "problem_diagnosis", "savings_instability", "wealth_diagnosis"),
        ("income", "topic_reading", "general", "income"),
        ("income", "potential_capacity", "multiple_income", "multiple_income"),
        ("debt", "problem_diagnosis", "general", "debt_diagnosis"),
        ("debt", "topic_reading", "loan_support", "debt"),
        ("investment", "potential_capacity", "general", "investment"),
        ("investment", "comparison_choice", "investing_vs_trading", "investing_vs_trading"),
        ("investment", "problem_diagnosis", "investment_risk", "investment_risk"),
        ("inheritance", "topic_reading", "general", "inheritance"),
        ("wealth", "potential_capacity", "windfall", "windfall"),
        ("wealth", "remedy_action", "general", "wealth_remedies"),
    ]
    for category, mode, subtype, expected in cases:
        assert wealth_graph_runtime_key(category, {
            "answer_mode": mode,
            "wealth_subtype": subtype,
            "time_scope": incidental_scope,
        }) == expected


def test_generic_loan_question_cannot_demand_timing_evidence() -> None:
    plan = {
        "answer_mode": "decision_support",
        "wealth_subtype": "loan_support",
        "time_scope": {},
    }
    assert wealth_graph_runtime_key("debt", plan) == "debt"
    comparison = compare_wealth_graph_policy(
        category="debt",
        query_plan=plan,
        observed_answer_mode="decision_support",
        context=_foundation_context(),
    )
    assert comparison and comparison["runtime_key"] == "debt"
    assert comparison["mode_match"] is True
    assert "wealth:DashaActivation" not in comparison["required_factors"]
    assert "wealth:TransitConfirmation" not in comparison["required_factors"]


def test_loan_decision_semantic_subtype_cannot_degrade_to_static_debt_reading() -> None:
    selection = _mode_selection_from_intent({
        "category": "debt",
        "wealth_subtype": "loan_decision",
        "answer_mode": "topic_reading",
        "target_subject_key": "self",
    })
    assert selection
    assert selection["answer_mode"] == "event_prediction"


def test_business_expansion_loan_decision_requires_conversion_not_just_debt_activity() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    forward_periods = [
        {
            "start": "2026-08-28", "end": "2026-09-18", "time_status": "current",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Saturn",
            "activated_focus_houses": [2, 8], "relevance_score": 35,
            "peak_activation_windows": [{
                "start": "2026-08-28", "end": "2026-09-18", "planet": "Rahu",
                "activated_focus_houses": [2, 8],
                "delivered_event_houses": [{"house": 2}, {"house": 8}], "trigger_score": 5,
            }],
        },
        {
            "start": "2026-09-19", "end": "2027-02-12", "time_status": "future",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Mercury",
            "activated_focus_houses": [2, 8, 12], "relevance_score": 33,
            "peak_activation_windows": [{
                "start": "2026-09-19", "end": "2026-12-05", "planet": "Rahu",
                "activated_focus_houses": [2, 8],
                "delivered_event_houses": [{"house": 2}, {"house": 8}], "trigger_score": 5,
            }],
        },
    ]
    foundation = _compact_wealth_foundation(
        chart,
        birth,
        {"forward_event_dasha_scan": {"periods": forward_periods}},
        category="debt",
        answer_mode="event_prediction",
        wealth_subtype="loan_decision",
    )
    synthesis = foundation["loan_decision_synthesis"]
    assert foundation["houses_available"] == [2, 6, 7, 8, 10, 11, 12]
    assert foundation["availability"]["d10"] is True
    assert synthesis["d2_retention"] == "mixed_capacity_with_retention_pressure"
    assert all(
        row["classification"] == "liability_or_outflow_without_business_conversion"
        for row in synthesis["decision_windows"]
    )

    context = {
        "intent_summary": {
            "category": "debt", "answer_mode": "event_prediction",
            "wealth_subtype": "loan_decision",
        },
        "normalized_evidence": {"wealth_foundation": foundation},
        "current_dashas": {"levels": {"MD": {"planet": "Saturn"}}},
        "current_transits": {"planets": {"Saturn": {"house": 9}}},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "debt", "answer_mode": "event_prediction",
                "wealth_subtype": "loan_decision",
                "time_scope": {"as_of": "2026-08-28", "horizon_end": "2026-12-31"},
            },
            "answer_spec": {"event_rules": {}}, "verification": {}, "user_derivation": {},
            "verdict": {"direction": "conditional"},
        },
        intent={"category": "debt", "wealth_subtype": "loan_decision"}, context=context,
    )
    assert packet["answer_spec"]["knowledge_graph_policy"]["runtime_key"] == "loan_decision"
    assert packet["verdict"]["direction"] == "not_a_clean_astrological_green_light_for_new_expansion_debt"
    assert packet["verdict"]["ranked_windows"][-1]["end"] == "2026-12-31"
    answer = enforce_live_graph_answer("Taking the loan is supported.", packet)
    assert "lean against taking a new business-expansion loan" in answer
    assert "houses 7, 10 and 11 do not come together strongly enough" in answer
    assert "D2 also shows mixed accumulation capacity with retention pressure" in answer
    assert "Astrology cannot establish affordability" in answer


def test_loan_decision_uses_bounded_segments_when_ranked_forward_rows_are_outside_horizon() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    normalized = {
        "forward_event_dasha_scan": {"periods": [{
            "start": "2028-04-22", "end": "2028-08-22",
            "mahadasha": "Saturn", "antardasha": "Jupiter", "pratyantardasha": "Jupiter",
            "activated_focus_houses": [2, 6, 8], "peak_activation_windows": [],
        }]},
        "window_dasha_segments": {"segments": [{
            "start": "2026-09-19", "end": "2026-12-31",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Mercury",
            "activated_focus_houses": [2, 8, 12], "peak_activation_windows": [{
                "start": "2026-09-19", "end": "2026-12-05", "planet": "Rahu",
                "activated_focus_houses": [2, 8],
                "delivered_event_houses": [{"house": 2}, {"house": 8}],
            }],
        }]},
    }
    foundation = _compact_wealth_foundation(
        chart, birth, normalized, category="debt",
        answer_mode="event_prediction", wealth_subtype="loan_decision",
    )
    windows = foundation["loan_decision_synthesis"]["decision_windows"]
    assert any(row["start"] == "2026-09-19" for row in windows)
    assert not any(row["start"] == "2028-04-22" for row in windows)


def test_live_loan_decision_context_keeps_today_and_business_conversion_houses() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    intent = {
        "category": "debt", "wealth_subtype": "loan_decision",
        "answer_mode": "topic_reading", "target_subject_key": "self",
        "extracted_context": {"timeframe": "this year"},
        "query_context": {
            "client_now_iso": "2026-08-28T13:02:00+05:30",
            "timezone_name": "Asia/Kolkata",
        },
    }
    context = _build_instant_context(
        birth, "Should I take a loan to expand my business this year?", intent, [],
        answer_mode_override="event_prediction",
        target_subject_override={"key": "self", "label": "self", "base_house": 1},
    )
    assert context["current_dashas"]["as_of"] == "2026-08-28"
    assert context["intent_summary"]["focus_houses"] == [2, 6, 7, 8, 10, 11, 12]
    synthesis = context["normalized_evidence"]["wealth_foundation"]["loan_decision_synthesis"]
    assert any(row["start"] <= "2026-12-31" for row in synthesis["decision_windows"])


def test_long_term_potential_log_shape_selects_static_overall_wealth_policy() -> None:
    context = _foundation_context(timing=True)
    packet = {
        "query_plan": {
            "category": "wealth",
            "wealth_subtype": "general",
            "answer_mode": "potential_capacity",
            "time_scope": {
                "requested": "long-term",
                "semantic": {"kind": "open_future"},
                "relation": "future",
                "as_of": "2026-08-27",
                "horizon_end": "2026-08-27",
                "is_exact_day": False,
            },
        },
        "answer_spec": {}, "verification": {}, "user_derivation": {},
        "verdict": {"direction": "calculated_wealth_foundation_available", "confidence": 0.84},
    }
    result = apply_live_graph_policy(packet, intent={
        "category": "wealth", "wealth_subtype": "general",
    }, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "wealth"
    assert policy["expected_answer_mode"] == "wealth:ModeTopic"
    assert policy["wealth_answer_rules"]["static_route"] is True
    assert policy.get("claim_permission") != "directional_only_no_timing"
    assert "wealth:DashaActivation" not in policy["observed_factors"]
    assert "wealth:TransitConfirmation" not in policy["observed_factors"]


def test_static_observation_does_not_import_background_timing() -> None:
    context = _foundation_context(timing=True)
    factors = observed_wealth_factors(context, {"answer_mode": "topic_reading", "time_scope": {}})
    assert "wealth:DashaActivation" not in factors
    assert "wealth:TransitConfirmation" not in factors
    result = compare_wealth_graph_policy(
        category="wealth", query_plan={"answer_mode": "topic_reading", "time_scope": {}},
        observed_answer_mode="topic_reading", context=context,
    )
    assert result and result["match"] is True


def test_timing_route_fails_closed_when_transit_is_missing() -> None:
    context = _foundation_context()
    context["current_dashas"] = {"levels": {"MD": {"planet": "Jupiter"}}}
    result = compare_wealth_graph_policy(
        category="wealth",
        query_plan={"answer_mode": "timing_window", "time_scope": {"requested": "next year"}},
        observed_answer_mode="timing_window", context=context,
    )
    assert result
    assert "wealth:TransitConfirmation" in result["missing_required_factors"]
    assert result["match"] is False


def test_query_planner_preserves_router_wealth_subtype() -> None:
    plan = build_query_plan(
        question="Should I invest or trade?",
        intent={"category": "investment", "wealth_subtype": "investing_vs_trading"},
        answer_mode="comparison_choice", target_subject=None, language="english",
    )
    assert plan["wealth_subtype"] == "investing_vs_trading"


def test_wealth_is_live_and_carries_financial_safety_contract() -> None:
    packet = {
        "query_plan": {"category": "wealth", "answer_mode": "topic_reading", "time_scope": {}},
        "answer_spec": {}, "verification": {}, "user_derivation": {},
    }
    result = apply_live_graph_policy(packet, intent={"category": "wealth"}, context=_foundation_context())
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["live"] is True
    assert policy["domain"] == "wealth"
    assert policy["runtime_key"] == "wealth"
    assert policy["financial_safety_rules"]["forbidden_moves"]


def test_composer_keeps_nested_d1_d2_and_indu_evidence() -> None:
    context = _foundation_context()
    foundation = context["normalized_evidence"]["wealth_foundation"]
    foundation.update({
        "natal_wealth": {"houses": {"2": {
            "basic_info": {"lord": "Jupiter", "occupants": ["Venus"]},
            "lord": {"placement": {"house": 11, "nakshatra": "Revati"}},
        }}},
        "divisional_charts": {"D2": {"planets": {"Jupiter": {"house": 2, "dignity": "own_sign"}}}},
        "indu_lagna": {"sign_name": "Pisces", "ruler_analysis": {"ruler_placement": {"house": 11}}},
    })
    packet = apply_live_graph_policy(
        {
            "query_plan": {"category": "wealth", "answer_mode": "topic_reading", "time_scope": {}},
            "answer_spec": {}, "verification": {}, "user_derivation": {}, "verdict": {"direction": "supported"},
        },
        intent={"category": "wealth"}, context=context,
    )
    composer = _build_instant_composer_context(context, packet)
    evidence = composer["evidence"]["wealth_foundation"]
    assert evidence["natal_wealth"]["houses"]["2"]["lord"]["placement"]["nakshatra"] == "Revati"
    assert evidence["divisional_charts"]["D2"]["planets"]["Jupiter"]["dignity"] == "own_sign"
    assert evidence["indu_lagna"]["ruler_analysis"]["ruler_placement"]["house"] == 11


def test_all_wealth_categories_use_the_calculated_foundation_capability() -> None:
    for category in ("wealth", "income", "debt", "investment", "inheritance"):
        methodology = get_methodology(category, "topic_reading")
        assert "parashari.wealth_foundation" in methodology["operations"]
        assert methodology["claim_operations"] == ["parashari.wealth_foundation"]
        assert methodology["required_for_timing"] == ["parashari.wealth_foundation"]


def test_static_wealth_fusion_cannot_fall_back_to_generic_natal_promise() -> None:
    context = _foundation_context(timing=True)
    context["normalized_evidence"].update({
        "natal_promise": {"status": "supported"},
        "divisional_specifics": ["D9 confirms the second house."],
        "current_timing": {"chain": "Saturn-Venus"},
    })
    packet = build_instant_v2_packet(
        question="What does my chart show about my long-term wealth potential?",
        intent={"category": "wealth", "wealth_subtype": "general"},
        answer_mode="potential_capacity",
        target_subject=None,
        language="english",
        instant_context=context,
    )
    assert packet["query_plan"]["category"] == "wealth"
    assert packet["verdict"]["direction"] == "calculated_wealth_foundation_available"
    assert packet["verdict"]["direction"] != "supported_natal_promise"


def test_static_wealth_composer_receives_only_wealth_foundation_not_d9_or_timing() -> None:
    context = _foundation_context(timing=True)
    foundation = context["normalized_evidence"]["wealth_foundation"]
    foundation.update({
        "natal_wealth": {"houses": {"2": {"basic_info": {"lord": "Jupiter"}}}},
        "divisional_charts": {"D2": {"planets": {"Venus": {"house": 2}}}},
        "indu_lagna": {"sign_name": "Pisces"},
    })
    context["normalized_evidence"].update({
        "natal_promise": {"status": "supported"},
        "divisional_specifics": ["D9 confirms wealth."],
        "current_timing": {"chain": "Saturn-Venus"},
        "transit_activation_timeline": {"peak_windows": [{"start": "2027-01-01"}]},
    })
    packet = build_instant_v2_packet(
        question="What does my chart show about my long-term wealth potential?",
        intent={"category": "wealth", "wealth_subtype": "general"},
        answer_mode="potential_capacity", target_subject=None,
        language="english", instant_context=context,
    )
    packet = apply_live_graph_policy(packet, intent={"category": "wealth"}, context=context)
    composer = _build_instant_composer_context(context, packet)
    assert composer["verdict"]["direction"] == "calculated_wealth_foundation_available"
    assert set(composer["evidence"]) == {"wealth_foundation", "_wealth_rules"}
    assert composer["evidence"]["wealth_foundation"]["divisional_charts"]["D2"]
    assert composer["query_plan"].get("time_scope") is None
    slot_sources = " ".join(
        str(row.get("source") or "") for row in composer["answer_blueprint"]["slots"]
    )
    assert "D2" in slot_sources
    assert "indu_lagna" in slot_sources


def test_wealth_rules_and_financial_safety_survive_composer_compaction() -> None:
    packet = apply_live_graph_policy(
        {
            "query_plan": {"category": "wealth", "answer_mode": "topic_reading", "time_scope": {}},
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "wealth"}, context=_foundation_context(),
    )
    compact = _compact_answer_spec_for_composer(packet["answer_spec"])
    assert compact["wealth_answer_rules"]["static_route"] is True
    assert compact["financial_safety_rules"]["forbidden_moves"]
    assert compact["knowledge_graph_policy"]["wealth_answer_rules"]["primary_evidence"] == "evidence.wealth_foundation"


def test_static_wealth_answer_boundary_removes_d9_and_activation_language() -> None:
    packet = apply_live_graph_policy(
        {
            "query_plan": {"category": "wealth", "answer_mode": "topic_reading", "time_scope": {}},
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "wealth"}, context=_foundation_context(),
    )
    answer = enforce_live_graph_answer(
        "D9 confirms your wealth. Your second house is activated. D2 qualifies retention.",
        packet,
    )
    assert "D9" not in answer
    assert "activated" not in answer
    assert "D2 qualifies retention" in answer


def test_qualified_overall_wealth_boundary_corrects_unearned_strength_and_d2_claims() -> None:
    packet = apply_live_graph_policy(
        {
            "query_plan": {"category": "wealth", "answer_mode": "potential_capacity", "time_scope": {}},
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "wealth"}, context=_foundation_context(),
    )
    answer = enforce_live_graph_answer(
        "Your chart shows a genuinely strong foundation. It is a clear pattern of accumulation and retention. "
        "The 2nd house and 5th house (gains and smart allocation) are connected. "
        "Your D2 Hora chart confirms this, so money has a good chance of staying with you and multiplying over time. "
        "Your Indu Lagna in Pisces points to wealth through creativity, beauty, or luxury. "
        "The potential is clearly there.",
        packet,
    )
    assert "genuinely strong" not in answer
    assert "clear pattern of accumulation and retention" not in answer
    assert "D2 Hora chart confirms" not in answer
    assert "5th house (gains" not in answer
    assert "5th house (judgment, speculation and investment intelligence)" in answer
    assert "wealth through creativity" not in answer
    assert "Indu Lagna is a supplementary wealth lens" in answer
    assert "real but qualified foundation" in answer
    assert "mixed pattern of accumulation capacity and retention pressure" in answer
    assert "D2 Hora chart qualifies" in answer
    assert "potential is present but qualified" in answer


def test_reference_chart_overall_wealth_is_qualified_and_d2_is_mixed() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    foundation = _compact_wealth_foundation(
        chart, birth, {}, category="wealth", answer_mode="potential_capacity",
    )
    assert foundation["d2_synthesis"]["verdict"] == "mixed_capacity_with_retention_pressure"
    assert foundation["route_adjudication"]["strength_claim_permission"] == "qualified_only"
    mars_caution = next(
        row for row in foundation["route_adjudication"]["carrier_cautions"]
        if row["house"] == 5 and row["lord"] == "Mars"
    )
    assert {"gandanta", "avayogi_lord", "dagdha_lord", "mixed_or_malefic_conjunctions"}.issubset(
        mars_caution["flags"]
    )
    assert "wealth_score" not in foundation["natal_wealth"]
    assert "wealth_constitution" not in foundation["natal_wealth"]


def test_reference_chart_wealth_source_ranks_concrete_channels_not_savings_advice() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    foundation = _compact_wealth_foundation(
        chart, birth, {}, category="wealth", answer_mode="potential_capacity",
        wealth_subtype="source",
    )
    synthesis = foundation["wealth_source_synthesis"]
    assert synthesis["verdict"] == "ranked_wealth_building_channels"
    assert synthesis["earning_structure"] == "profession_or_service_led"
    assert synthesis["ranked_channels"][0]["id"] == "technical_professional"
    assert synthesis["ranked_channels"][1]["id"] == "network_commercial_scale"
    assert any("D10 Mercury" in value for value in synthesis["ranked_channels"][0]["evidence"])
    assert any("eleventh lord Venus" in value for value in synthesis["ranked_channels"][1]["evidence"])

    context = {
        "intent_summary": {"category": "wealth", "answer_mode": "potential_capacity"},
        "normalized_evidence": {"wealth_foundation": foundation},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "wealth", "answer_mode": "potential_capacity",
                "wealth_subtype": "source", "time_scope": {},
            },
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "wealth", "wealth_subtype": "source"}, context=context,
    )
    answer = enforce_live_graph_answer(
        "Your path is disciplined savings, automated transfers and separating your spending account from investments.",
        packet,
    )
    assert "technical, analytical and systems-led professional work" in answer
    assert "scalable commercial gains through networks, platforms or products" in answer
    assert "profession- or service-led" in answer
    assert "automated savings" not in answer
    assert "D2 adds a separate caution" in answer


def test_reference_chart_multiple_income_uses_specific_streams_and_complete_route() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    foundation = _compact_wealth_foundation(
        chart, birth, {}, category="income", answer_mode="potential_capacity",
        wealth_subtype="multiple_income",
    )
    synthesis = foundation["multiple_income_synthesis"]
    assert synthesis["verdict"] == "multiple_complementary_streams_supported"
    assert synthesis["primary_stream"]["id"] == "technical_professional"
    assert synthesis["secondary_streams"][0]["id"] == "network_commercial_scale"

    context = {
        "intent_summary": {
            "category": "income", "answer_mode": "potential_capacity",
            "wealth_subtype": "multiple_income",
        },
        "normalized_evidence": {"wealth_foundation": foundation},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "income", "answer_mode": "potential_capacity",
                "wealth_subtype": "multiple_income", "time_scope": {},
            },
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "income", "wealth_subtype": "multiple_income"}, context=context,
    )
    policy = packet["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "multiple_income"
    assert policy.get("missing_required_factors") == []
    assert policy.get("claim_permission") != "no_complete_wealth_verdict"

    answer = enforce_live_graph_answer(
        "Diversifying may help, but build savings first.", packet,
    )
    assert "Yes—your chart supports more than one income stream" in answer
    assert "technical, analytical and systems-led professional work" in answer
    assert "scalable commercial gains through networks, platforms or products" in answer
    assert "unrelated side hustles" in answer
    assert "required calculated layers are unavailable" not in answer


def test_all_typed_wealth_subtypes_drive_their_own_calculator_layers_from_broad_category() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    cases = [
        ("source", "potential_capacity", "wealth_source"),
        ("savings_instability", "problem_diagnosis", "wealth_diagnosis"),
        ("multiple_income", "potential_capacity", "multiple_income"),
        ("debt_repayment", "timing_window", "debt_repayment"),
        ("loan_support", "timing_window", "loan_support"),
        ("loan_decision", "event_prediction", "loan_decision"),
        ("investing_vs_trading", "comparison_choice", "investing_vs_trading"),
        ("investment_risk", "problem_diagnosis", "investment_risk"),
        ("loss_vulnerability", "topic_reading", "loss_vulnerability"),
        ("windfall", "potential_capacity", "windfall"),
    ]
    for subtype, answer_mode, expected_runtime_key in cases:
        category = effective_wealth_category("wealth", subtype)
        foundation = _compact_wealth_foundation(
            chart, birth, {}, category=category or "wealth",
            answer_mode=answer_mode, wealth_subtype=subtype,
        )
        context = {
            "intent_summary": {
                "category": category, "answer_mode": answer_mode,
                "wealth_subtype": subtype,
            },
            "normalized_evidence": {"wealth_foundation": foundation},
            "current_dashas": {"levels": {"MD": {"planet": "Saturn"}}},
            "current_transits": {"planets": {"Jupiter": {"house": 11}}},
        }
        packet = apply_live_graph_policy(
            {
                "query_plan": {
                    "category": "wealth", "answer_mode": answer_mode,
                    "wealth_subtype": subtype, "time_scope": {},
                },
                "answer_spec": {}, "verification": {}, "user_derivation": {},
            },
            intent={"category": "wealth", "wealth_subtype": subtype},
            context=context,
        )
        policy = packet["answer_spec"]["knowledge_graph_policy"]
        assert policy["domain"] == "wealth", subtype
        assert policy["runtime_key"] == expected_runtime_key, subtype
        assert policy.get("missing_required_factors") == [], (subtype, policy.get("missing_required_factors"))
        assert policy.get("claim_permission") != "no_complete_wealth_verdict", subtype


def test_reference_chart_loss_vulnerability_has_d5_and_ranked_loss_mechanisms() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    foundation = _compact_wealth_foundation(
        chart, birth, {}, category="wealth", answer_mode="topic_reading",
        wealth_subtype="loss_vulnerability",
    )
    assert foundation["availability"]["d5"] is True
    assert 6 in foundation["houses_available"]
    synthesis = foundation["loss_vulnerability_synthesis"]
    assert synthesis["ranked_vulnerabilities"][0]["id"] == "speculation_volatility"
    assert synthesis["ranked_vulnerabilities"][1]["id"] == "retention_leakage"

    context = {
        "intent_summary": {
            "category": "investment", "answer_mode": "topic_reading",
            "wealth_subtype": "loss_vulnerability",
        },
        "normalized_evidence": {"wealth_foundation": foundation},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "wealth", "answer_mode": "topic_reading",
                "wealth_subtype": "loss_vulnerability", "time_scope": {},
            },
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "wealth", "wealth_subtype": "loss_vulnerability"}, context=context,
    )
    policy = packet["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "loss_vulnerability"
    assert policy.get("missing_required_factors") == []
    answer = enforce_live_graph_answer("Your chart has mixed financial risk.", packet)
    assert "high-conviction speculation and volatile investment decisions" in answer
    assert "fifth lord Mars" in answer
    assert "D5 is mixed" in answer
    assert "D2 gives a mixed accumulation pattern with retention pressure" in answer
    assert "D9 remains mixed" in answer
    assert "complete Wealth reading" not in answer


def test_reference_chart_investment_synthesis_is_specific_and_generic_answer_fails_safe() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    foundation = _compact_wealth_foundation(
        chart, birth, {}, category="investment", answer_mode="potential_capacity",
    )
    synthesis = foundation["investment_synthesis"]
    assert synthesis["verdict"] == "disciplined_investing_favored_over_high_risk_speculation"
    assert synthesis["fifth_lord"]["planet"] == "Mars"
    assert {"gandanta", "avayogi_lord", "dagdha_lord", "mixed_or_malefic_conjunctions"}.issubset(
        synthesis["fifth_lord"]["caution_flags"]
    )
    assert any(row["planet"] == "Jupiter" and row["house"] == 11 for row in synthesis["d5"]["supporting_placements"])
    assert any(row["planet"] == "Moon" and "debilitated" in row["reasons"] for row in synthesis["d5"]["caution_placements"])
    assert any(row["node"] == "Rahu" and "Mars" in row["companions"] for row in synthesis["d5"]["node_cooccupancies"])
    assert any(row["planet"] == "Mars" and row["house"] == 2 for row in synthesis["d9"]["supporting_placements"])
    assert any(row["planet"] == "Venus" and row["house"] == 12 for row in synthesis["d9"]["caution_placements"])

    context = {
        "intent_summary": {"category": "investment", "answer_mode": "potential_capacity"},
        "normalized_evidence": {"wealth_foundation": foundation},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "investment", "answer_mode": "potential_capacity",
                "wealth_subtype": "general", "time_scope": {},
            },
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "investment"}, context=context,
    )
    answer = enforce_live_graph_answer(
        "Your chart gives a qualified yes. The fifth lord needs to be weighed. "
        "D2 is mixed and D9 can qualify the result, so long-term investing is preferable.",
        packet,
    )
    assert "The fifth lord Mars" in answer
    assert "D5 is mixed" in answer
    assert "Jupiter in the 11th house" in answer
    assert "D9 provides supporting qualification" in answer
    assert "Venus in the 12th house" in answer
    assert "needs to be weighed" not in answer
    assert "building and holding" not in answer


def test_reference_chart_debt_repayment_uses_route_polarity_not_current_date() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    forward_periods = [
        {
            "start": "2026-08-27", "end": "2026-09-18", "time_status": "current",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Saturn",
            "activated_focus_houses": [2, 8], "relevance_score": 35,
            "peak_activation_windows": [{
                "start": "2026-08-27", "end": "2026-09-18", "planet": "Rahu",
                "activated_focus_houses": [2, 8], "delivered_event_houses": [{"house": 2}, {"house": 8}],
            }],
        },
        {
            "start": "2028-04-22", "end": "2028-08-22", "time_status": "future",
            "mahadasha": "Saturn", "antardasha": "Jupiter", "pratyantardasha": "Jupiter",
            "activated_focus_houses": [2, 6, 8], "relevance_score": 70,
            "peak_activation_windows": [{
                "start": "2028-04-22", "end": "2028-07-22", "planet": "Jupiter",
                "activated_focus_houses": [2, 6, 8], "delivered_event_houses": [{"house": 2}, {"house": 6}, {"house": 8}],
            }],
        },
        {
            "start": "2029-07-21", "end": "2029-08-26", "time_status": "future",
            "mahadasha": "Saturn", "antardasha": "Jupiter", "pratyantardasha": "Venus",
            "activated_focus_houses": [2, 6, 8, 11], "relevance_score": 63,
            "peak_activation_windows": [{
                "start": "2029-08-11", "end": "2029-08-26", "planet": "Saturn",
                "activated_focus_houses": [8, 11], "delivered_event_houses": [{"house": 8}, {"house": 11}],
            }],
        },
    ]
    foundation = _compact_wealth_foundation(
        chart,
        birth,
        {"forward_event_dasha_scan": {"periods": forward_periods}},
        category="debt",
        answer_mode="timing_window",
    )
    synthesis = foundation["debt_repayment_synthesis"]
    assert synthesis["current_window_assessment"]["classification"] == "debt_activity_not_repayment_support"
    assert synthesis["current_window_assessment"]["support_houses"] == [2]
    assert synthesis["ranked_repayment_windows"][0]["start"] == "2029-07-21"
    assert synthesis["ranked_repayment_windows"][0]["classification"] == "strongest_repayment_support"
    assert any(row["start"] == "2028-04-22" for row in synthesis["ranked_repayment_windows"])

    context = {
        "intent_summary": {"category": "debt", "answer_mode": "timing_window"},
        "normalized_evidence": {"wealth_foundation": foundation},
        "current_dashas": {"levels": {"MD": {"planet": "Saturn"}}},
        "current_transits": {"planets": {"Saturn": {"house": 9}}},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "debt", "answer_mode": "timing_window",
                "wealth_subtype": "general", "time_scope": {"as_of": "2026-08-27"},
            },
            "answer_spec": {"event_rules": {}}, "verification": {}, "user_derivation": {},
            "verdict": {"direction": "conditional", "ranked_windows": [{"start": "2026-08-27"}]},
        },
        intent={"category": "debt"}, context=context,
    )
    assert packet["verdict"]["ranked_windows"][0]["start"] == "2029-07-21"
    answer = enforce_live_graph_answer(
        "27 August 2026 is a significant marker. Treat this as repayment season and consolidate smaller debts.",
        packet,
    )
    assert "significant marker" not in answer
    assert "consolidate" not in answer
    assert "22 April 2028 to 22 August 2028" in answer
    assert "21 July 2029 to 26 August 2029" in answer
    assert "not an exact payoff date" in answer


def test_reference_chart_next_wealth_growth_searches_future_phases_not_as_of_date() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    forward_periods = [
        {
            "start": "2026-08-27", "end": "2026-09-18", "time_status": "current",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Saturn",
            "activated_focus_houses": [2, 11], "relevance_score": 38,
            "peak_activation_windows": [{
                "start": "2026-08-27", "end": "2026-09-18", "planet": "Rahu",
                "activated_focus_houses": [2], "delivered_event_houses": [{"house": 2}],
            }],
        },
        {
            "start": "2027-04-15", "end": "2027-10-04", "time_status": "future",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Venus",
            "activated_focus_houses": [2, 5, 11], "relevance_score": 69,
            "peak_activation_windows": [{
                "start": "2027-06-08", "end": "2027-06-08", "planet": "Venus",
                "activated_focus_houses": [5, 11], "delivered_event_houses": [{"house": 5}, {"house": 11}],
            }],
        },
        {
            "start": "2028-04-22", "end": "2028-08-22", "time_status": "future",
            "mahadasha": "Saturn", "antardasha": "Jupiter", "pratyantardasha": "Jupiter",
            "activated_focus_houses": [2, 9, 11], "relevance_score": 65,
            "peak_activation_windows": [{
                "start": "2028-04-22", "end": "2028-07-22", "planet": "Jupiter",
                "activated_focus_houses": [2], "delivered_event_houses": [{"house": 2}],
            }],
        },
        {
            "start": "2029-07-21", "end": "2029-08-26", "time_status": "future",
            "mahadasha": "Saturn", "antardasha": "Jupiter", "pratyantardasha": "Venus",
            "activated_focus_houses": [2, 5, 9, 11], "relevance_score": 71,
            "peak_activation_windows": [{
                "start": "2029-08-08", "end": "2029-08-18", "planet": "Venus",
                "activated_focus_houses": [2, 11], "delivered_event_houses": [{"house": 2}, {"house": 11}],
            }],
        },
    ]
    foundation = _compact_wealth_foundation(
        chart,
        birth,
        {"forward_event_dasha_scan": {"periods": forward_periods}},
        category="wealth",
        answer_mode="timing_window",
    )
    synthesis = foundation["wealth_growth_timing_synthesis"]
    assert synthesis["current_window_assessment"]["classification"] == "current_financial_activity_not_next_growth"
    assert synthesis["next_growth_window"]["start"] == "2027-04-15"
    assert synthesis["strongest_growth_window"]["start"] == "2029-07-21"
    assert [row["start"] for row in synthesis["ranked_growth_windows"]] == ["2027-04-15", "2029-07-21"]
    assert any(row["start"] == "2028-04-22" for row in synthesis["partial_support_windows"])

    context = {
        "intent_summary": {"category": "wealth", "answer_mode": "timing_window"},
        "normalized_evidence": {"wealth_foundation": foundation},
        "current_dashas": {"levels": {"MD": {"planet": "Saturn"}}},
        "current_transits": {"planets": {"Saturn": {"house": 9}}},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "wealth", "answer_mode": "timing_window",
                "wealth_subtype": "general", "time_scope": {"as_of": "2026-08-27"},
            },
            "answer_spec": {"event_rules": {}}, "verification": {}, "user_derivation": {},
            "verdict": {"direction": "conditional", "ranked_windows": [{"start": "2026-08-27"}]},
        },
        intent={"category": "wealth"}, context=context,
    )
    assert [row["start"] for row in packet["verdict"]["ranked_windows"]] == ["2027-04-15", "2029-07-21"]
    answer = enforce_live_graph_answer(
        "Your next meaningful wealth-growth window is 27 August 2026 under Saturn-Rahu-Saturn.",
        packet,
    )
    assert "Your next meaningful wealth-growth phase is 15 April 2027 to 4 October 2027" in answer
    assert "21 July 2029 to 26 August 2029" in answer
    assert "not guaranteed gains or exact transaction dates" in answer


def test_bounded_wealth_forecast_maps_months_instead_of_using_open_future_refusal() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    segments = [
        {
            "start": "2027-01-01", "end": "2027-04-14",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Mercury",
            "activated_focus_houses": [2, 11], "relevance_score": 29,
            "peak_activation_windows": [], "transit_trigger_windows": [],
        },
        {
            "start": "2027-04-15", "end": "2027-10-04",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Venus",
            "activated_focus_houses": [2, 5, 11], "relevance_score": 69,
            "peak_activation_windows": [{
                "start": "2027-06-08", "end": "2027-06-08", "planet": "Venus",
                "activated_focus_houses": [5, 11], "delivered_event_houses": [{"house": 5}, {"house": 11}],
                "trigger_score": 14,
            }],
            "transit_trigger_windows": [
                {
                    "start": "2027-04-15", "end": "2027-05-27", "planet": "Saturn",
                    "activated_focus_houses": [11], "delivered_event_houses": [{"house": 11}],
                    "trigger_score": 2,
                },
                {
                    "start": "2027-06-08", "end": "2027-06-08", "planet": "Venus",
                    "activated_focus_houses": [5, 11], "delivered_event_houses": [{"house": 5}, {"house": 11}],
                    "trigger_score": 14,
                },
                {
                    "start": "2027-08-17", "end": "2027-09-06", "planet": "Venus",
                    "activated_focus_houses": [2], "delivered_event_houses": [{"house": 2}],
                    "trigger_score": 2,
                },
            ],
        },
        {
            "start": "2027-10-05", "end": "2027-11-25",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Sun",
            "activated_focus_houses": [2, 9, 11], "relevance_score": 57,
            "peak_activation_windows": [{
                "start": "2027-10-05", "end": "2027-10-17", "planet": "Sun",
                "activated_focus_houses": [9], "delivered_event_houses": [{"house": 9}],
                "trigger_score": 5,
            }],
            "transit_trigger_windows": [],
        },
        {
            "start": "2027-11-26", "end": "2027-12-31",
            "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Moon",
            "activated_focus_houses": [2, 11], "relevance_score": 22,
            "peak_activation_windows": [], "transit_trigger_windows": [],
        },
    ]
    normalized = {
        "current_timing": {"period_window": {
            "kind": "window", "start": "2027-01-01", "end": "2027-12-31", "span_days": 365,
        }},
        "window_dasha_segments": {"segments": segments},
    }
    foundation = _compact_wealth_foundation(
        chart, birth, normalized, category="wealth", answer_mode="timing_window",
    )
    synthesis = foundation["wealth_growth_timing_synthesis"]
    bounded = synthesis["bounded_period_synthesis"]
    assert synthesis["forecast_kind"] == "bounded_period_support_forecast"
    assert synthesis["verdict"] == "bounded_period_support_mapped"
    assert [row["month"] for row in bounded["strongest_peak_months"]] == ["June 2027"]
    assert bounded["reinforced_support_months"] == [
        "April 2027", "May 2027", "June 2027", "August 2027", "September 2027",
    ]
    assert bounded["background_support_months"] == ["July 2027"]
    assert bounded["secondary_support_months"] == ["October 2027", "November 2027"]
    assert bounded["lower_support_months"] == ["January 2027", "February 2027", "March 2027", "December 2027"]

    context = {
        "intent_summary": {"category": "wealth", "answer_mode": "timing_window"},
        "normalized_evidence": {"wealth_foundation": foundation},
        "current_dashas": {"levels": {"MD": {"planet": "Saturn"}}},
        "current_transits": {"planets": {"Saturn": {"house": 9}}},
    }
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "wealth", "answer_mode": "timing_window", "wealth_subtype": "general",
                "time_scope": {"requested": "next year", "as_of": "2027-01-01", "horizon_end": "2027-12-31"},
            },
            "answer_spec": {"event_rules": {}}, "verification": {}, "user_derivation": {},
            "verdict": {"direction": "conditional"},
        },
        intent={"category": "wealth"}, context=context,
    )
    assert packet["verdict"]["direction"] == "bounded_wealth_support_forecast"
    answer = enforce_live_graph_answer(
        "I cannot identify a reliable future wealth-growth phase from the calculated evidence.",
        packet,
    )
    assert answer.startswith("June 2027 is the strongest financially supportive")
    assert "15 April 2027 to 4 October 2027" in answer
    assert "October 2027 and November 2027 form a secondary supportive period" in answer
    assert "January 2027, February 2027, March 2027, and December 2027 are comparatively lower-support" in answer
    assert "cannot identify" not in answer


def test_investment_answer_boundary_retains_supporting_d9_qualification() -> None:
    context = _foundation_context()
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "investment", "answer_mode": "potential_capacity",
                "wealth_subtype": "general", "time_scope": {},
            },
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "investment"}, context=context,
    )
    answer = enforce_live_graph_answer(
        "D5 qualifies speculative judgment. D9 places Venus in the 12th and tempers sustainable expression.",
        packet,
    )
    assert "D5 qualifies" in answer
    assert "D9 places Venus" in answer


def test_investment_composer_preserves_carrier_conditions_d5_and_d9() -> None:
    context = _foundation_context()
    foundation = context["normalized_evidence"]["wealth_foundation"]
    foundation.update({
        "natal_wealth": {"houses": {"5": {"lord": {
            "placement": {"planet": "Mars", "house": 2},
            "conditions": {
                "gandanta": {"is_gandanta": True, "name": "Ashlesha-Magha Gandanta"},
                "special_lordships": {
                    "is_avayogi_lord": True, "is_dagdha_lord": True,
                    "avayogi_tithi_shunya_benefic_override": True,
                },
                "conjunctions": [{"planet": "Rahu", "orb": 1.03}, {"planet": "Saturn", "orb": 26.2}],
            },
        }}}},
        "route_carrier_conditions": {"Venus": {"dignity": "own_sign"}},
        "divisional_charts": {
            "D2": {"planets": {"Venus": {"house": 2}}},
            "D5": {"planets": {"Mars": {"house": 5}}},
            "D9": {"planets": {"Venus": {"house": 12, "sign_name": "Aquarius"}}},
        },
    })
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "investment", "answer_mode": "potential_capacity",
                "wealth_subtype": "general", "time_scope": {},
            },
            "answer_spec": {}, "verification": {}, "user_derivation": {},
            "verdict": {"direction": "calculated_wealth_foundation_available"},
        },
        intent={"category": "investment"}, context=context,
    )
    composer = _build_instant_composer_context(context, packet)
    delivered = composer["evidence"]["wealth_foundation"]
    conditions = delivered["natal_wealth"]["houses"]["5"]["lord"]["conditions"]
    assert conditions["gandanta"]["is_gandanta"] is True
    assert conditions["special_lordships"]["is_avayogi_lord"] is True
    assert conditions["special_lordships"]["is_dagdha_lord"] is True
    assert conditions["conjunctions"][0]["planet"] == "Rahu"
    assert delivered["divisional_charts"]["D5"]
    assert delivered["divisional_charts"]["D9"]["planets"]["Venus"]["house"] == 12
    slots = " ".join(row["slot"] for row in composer["answer_blueprint"]["slots"])
    assert "complete investment-carrier condition" in slots
    assert "D5 speculative refinement and D9 carrier qualification" in slots


def test_missing_d2_fails_closed_instead_of_substituting_d9() -> None:
    context = _foundation_context()
    context["normalized_evidence"]["wealth_foundation"]["availability"]["d2"] = False
    context["normalized_evidence"]["divisional_specifics"] = ["D9 is supportive."]
    packet = apply_live_graph_policy(
        {
            "query_plan": {"category": "wealth", "answer_mode": "topic_reading", "time_scope": {}},
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "wealth"}, context=context,
    )
    policy = packet["answer_spec"]["knowledge_graph_policy"]
    assert policy["claim_permission"] == "no_complete_wealth_verdict"
    answer = enforce_live_graph_answer("D9 gives a clear yes.", packet)
    assert "complete Wealth reading" in answer
    assert "speculation" in answer


def test_all_static_wealth_routes_exclude_timing_at_runtime() -> None:
    store = WealthGraphPolicyStore()
    timed = {
        "wealth_timing", "income_timing", "debt_repayment",
        "loan_support", "loan_decision", "investment_timing", "inheritance_timing",
    }
    context = _foundation_context(timing=True)
    for runtime_key in EXPECTED_KEYS - timed:
        policy = store.require(runtime_key)
        result = compare_wealth_graph_policy(
            category={
                "income": "income", "multiple_income": "income",
                "debt": "debt", "debt_diagnosis": "debt",
                "investment": "investment", "investing_vs_trading": "investment",
                "investment_risk": "investment", "loss_vulnerability": "investment",
                "inheritance": "inheritance",
            }.get(runtime_key, "wealth"),
            query_plan={
                "answer_mode": {
                    "wealth_source": "potential_capacity", "wealth_diagnosis": "problem_diagnosis",
                    "multiple_income": "potential_capacity", "debt_diagnosis": "problem_diagnosis",
                    "investing_vs_trading": "comparison_choice", "investment_risk": "problem_diagnosis",
                    "wealth_remedies": "remedy_action",
                }.get(runtime_key, "topic_reading"),
                "wealth_subtype": {
                    "wealth_source": "source", "wealth_diagnosis": "savings_instability",
                    "multiple_income": "multiple_income", "investing_vs_trading": "investing_vs_trading",
                    "investment_risk": "investment_risk", "loss_vulnerability": "loss_vulnerability",
                    "windfall": "windfall",
                }.get(runtime_key, "general"),
                "time_scope": {},
            },
            observed_answer_mode={
                "wealth_source": "potential_capacity", "wealth_diagnosis": "problem_diagnosis",
                "multiple_income": "potential_capacity", "debt_diagnosis": "problem_diagnosis",
                "investing_vs_trading": "comparison_choice", "investment_risk": "problem_diagnosis",
                "wealth_remedies": "remedy_action",
            }.get(runtime_key, "topic_reading"),
            context=context,
        )
        assert result and result["runtime_key"] == runtime_key
        assert "wealth:DashaActivation" not in result["observed_factors"]
        assert "wealth:TransitConfirmation" not in result["observed_factors"]
        assert set(policy.default_exclusions).isdisjoint(result["observed_factors"])


def test_every_timed_wealth_route_requires_dasha_and_transit_confirmation() -> None:
    cases = [
        ("wealth", "timing_window", "general", "wealth_timing"),
        ("income", "timing_window", "general", "income_timing"),
        ("debt", "timing_window", "general", "debt_repayment"),
        ("debt", "timing_window", "loan_support", "loan_support"),
        ("debt", "event_prediction", "loan_decision", "loan_decision"),
        ("investment", "timing_window", "general", "investment_timing"),
        ("inheritance", "timing_window", "general", "inheritance_timing"),
    ]
    for category, mode, subtype, runtime_key in cases:
        plan = {
            "answer_mode": mode,
            "wealth_subtype": subtype,
            "time_scope": {"requested": "next year"} if mode == "timing_window" else {},
        }
        complete = compare_wealth_graph_policy(
            category=category, query_plan=plan,
            observed_answer_mode=mode, context=_foundation_context(timing=True),
        )
        assert complete and complete["runtime_key"] == runtime_key
        assert complete["match"] is True
        assert {"wealth:DashaActivation", "wealth:TransitConfirmation"}.issubset(
            complete["observed_factors"]
        )

        missing_transit_context = _foundation_context(timing=True)
        missing_transit_context["current_transits"] = {}
        incomplete = compare_wealth_graph_policy(
            category=category, query_plan=plan,
            observed_answer_mode=mode, context=missing_transit_context,
        )
        assert incomplete and incomplete["match"] is False
        assert "wealth:TransitConfirmation" in incomplete["missing_required_factors"]


def test_investing_vs_trading_does_not_request_generic_option_winner() -> None:
    packet = apply_live_graph_policy(
        {
            "query_plan": {
                "category": "investment", "answer_mode": "comparison_choice",
                "wealth_subtype": "investing_vs_trading", "time_scope": {},
            },
            "answer_spec": {}, "verification": {}, "user_derivation": {},
        },
        intent={"category": "investment", "wealth_subtype": "investing_vs_trading"},
        context=_foundation_context(),
    )
    policy = packet["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "investing_vs_trading"
    assert policy.get("claim_permission") != "no_option_winner"
    assert "comparison.option_specific_evidence" not in policy.get("required_capabilities", [])


def test_wealth_blueprint_uses_foundation_for_every_route_shape() -> None:
    foundation = _foundation_context()["normalized_evidence"]["wealth_foundation"]
    for static in (True, False):
        blueprint = _build_instant_answer_blueprint(
            query_plan={"category": "wealth", "answer_mode": "topic_reading" if static else "timing_window"},
            verdict={"direction": "calculated_wealth_foundation_available"},
            evidence={
                "wealth_foundation": foundation,
                "_wealth_rules": {"static_route": static, "forbidden_moves": ["no drift"]},
            },
        )
        assert blueprint["purpose"].startswith("semantic slots for the selected live Wealth graph route")
        assert any("D1 promise and D2" in row["slot"] for row in blueprint["slots"])
        assert any(
            ("manifestation support" in row["slot"]) if static else ("timing window" in row["slot"])
            for row in blueprint["slots"]
        )
