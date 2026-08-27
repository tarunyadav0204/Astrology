from __future__ import annotations

import subprocess
import sys
from pathlib import Path


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
    _compact_answer_spec_for_composer,
)
from instant_chat_v2.wealth_graph_policy import WealthGraphPolicyStore  # noqa: E402
from instant_chat_v2.wealth_graph_runtime import (  # noqa: E402
    compare_wealth_graph_policy,
    observed_wealth_factors,
    wealth_graph_runtime_key,
)


EXPECTED_KEYS = {
    "wealth", "wealth_source", "wealth_diagnosis", "wealth_timing",
    "income", "income_timing", "multiple_income",
    "debt", "debt_diagnosis", "debt_repayment", "loan_support",
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
    assert "Wealth and Finance ontology PoC valid: 20 competency questions" in result.stdout


def test_compiled_bundle_covers_all_twenty_routes() -> None:
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
    for key in EXPECTED_KEYS - {"wealth_timing", "income_timing", "debt_repayment", "investment_timing", "inheritance_timing", "loan_support"}:
        policy = store.require(key)
        assert {"wealth:DashaActivation", "wealth:TransitConfirmation"}.issubset(policy.default_exclusions)
    for key in {"wealth_timing", "income_timing", "debt_repayment", "investment_timing", "inheritance_timing", "loan_support"}:
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
    for key in ("wealth_timing", "income_timing", "debt_repayment", "loan_support", "investment_timing", "inheritance_timing"):
        assert "wealth:NoNodeFifthNinth" in store.require(key).guardrails


def test_semantic_subtypes_and_modes_resolve_to_specific_routes() -> None:
    cases = [
        ("wealth", "topic_reading", "source", "wealth_source"),
        ("wealth", "problem_diagnosis", "savings_instability", "wealth_diagnosis"),
        ("income", "potential_capacity", "multiple_income", "multiple_income"),
        ("debt", "decision_support", "loan_support", "loan_support"),
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
        "loan_support", "investment_timing", "inheritance_timing",
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
        ("debt", "decision_support", "loan_support", "loan_support"),
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
