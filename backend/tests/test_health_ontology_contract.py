from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.health_graph_policy import HealthGraphPolicyStore  # noqa: E402
from instant_chat_v2.health import HEALTH_PROFILES, normalize_health_category  # noqa: E402
from instant_chat_v2.health_graph_runtime import (  # noqa: E402
    HEALTH_CATEGORIES,
    build_health_graph_route,
    compare_health_graph_policy,
    health_graph_runtime_key,
    resolve_health_graph_inputs,
)


def test_health_ontology_compiles_and_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_health_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Health ontology PoC valid: 10 competency questions" in result.stdout


def test_compiled_health_bundle_has_static_and_timed_routes() -> None:
    store = HealthGraphPolicyStore()
    assert set(store.runtime_keys()) == {
        "health", "health_timing",
        "mental_wellbeing", "mental_wellbeing_timing",
        "surgery", "surgery_timing",
        "accident", "accident_timing",
        "recovery", "recovery_timing",
    }


def test_every_health_route_has_expandable_stages_and_factor_children() -> None:
    store = HealthGraphPolicyStore()
    for runtime_key in store.runtime_keys():
        question = store.require(runtime_key).graph_tree["children"][0]
        stages = next(node for node in question["children"] if node["label"] == "Decision stages")
        assert stages["children"], runtime_key
        for stage in stages["children"]:
            factors = next(node for node in stage["children"] if node["label"] == "Required astrology factors")
            assert factors["children"], f"{runtime_key}/{stage['label']}"


def test_static_health_excludes_timing_and_timed_health_requires_activation_chain() -> None:
    store = HealthGraphPolicyStore()
    static = store.require("health")
    timed = store.require("health_timing")
    assert {"health:DashaActivation", "health:TransitConfirmation"}.issubset(static.default_exclusions)
    assert "health:CapDashaActivation" not in static.required_capabilities
    assert {"health:DashaActivation", "health:TransitConfirmation"}.issubset(timed.required_factors)
    assert "health:NoActivationWithoutChain" in timed.guardrails
    assert "health:StrictRequestedHorizon" in timed.guardrails


def test_health_category_specific_safety_guardrails_are_compiled() -> None:
    store = HealthGraphPolicyStore()
    assert "health:NoSurgeryCertainty" in store.require("surgery").guardrails
    assert "health:NoAccidentPrediction" in store.require("accident_timing").guardrails
    assert "health:NoRecoveryPromise" in store.require("recovery_timing").guardrails
    assert "health:ExactRelationshipOnly" in store.require("mental_wellbeing").guardrails
    for runtime_key in store.runtime_keys():
        policy = store.require(runtime_key)
        assert "health:EmergencyTriageFirst" in policy.guardrails
        assert "health:NoDiagnosis" in policy.guardrails
        assert "health:NoTreatmentAdvice" in policy.guardrails


def test_all_live_health_categories_resolve_to_static_and_timed_graph_routes() -> None:
    store = HealthGraphPolicyStore()
    for category in HEALTH_CATEGORIES:
        static_key = health_graph_runtime_key(category, {"answer_mode": "topic_reading", "time_scope": {}})
        timed_key = health_graph_runtime_key(
            category,
            {"answer_mode": "timing_window", "time_scope": {"requested": "this year"}},
        )
        assert store.resolve(static_key) is not None, category
        assert store.resolve(timed_key) is not None, category


def test_disease_alias_resolves_to_general_health_graph() -> None:
    assert health_graph_runtime_key("disease", {"answer_mode": "topic_reading"}) == "health"
    assert health_graph_runtime_key(
        "disease", {"answer_mode": "timing_window", "time_scope": {"requested": "2027"}}
    ) == "health_timing"
    assert health_graph_runtime_key("career", {"answer_mode": "topic_reading"}) is None


def test_runtime_health_profiles_cover_every_graph_category() -> None:
    assert set(HEALTH_PROFILES) == {
        "health", "mental_wellbeing", "surgery", "accident", "recovery"
    }
    assert normalize_health_category("disease") == "health"
    assert normalize_health_category("injury") == "accident"


def test_event_prediction_without_explicit_health_timeframe_remains_constitutional() -> None:
    assert health_graph_runtime_key(
        "health",
        {"answer_mode": "event_prediction", "time_scope": {"requested": "current"}},
    ) == "health"


def test_health_graph_inputs_use_final_query_plan() -> None:
    query_plan = {
        "category": "mental_wellbeing",
        "answer_mode": "timing_window",
        "time_scope": {"requested": "next six months"},
    }
    assert resolve_health_graph_inputs(
        intent={"category": "health", "answer_mode": "topic_reading"},
        context={"intent_summary": {"category": "health"}},
        query_plan=query_plan,
    ) == {
        "category": "mental_wellbeing",
        "query_plan": query_plan,
        "observed_answer_mode": "timing_window",
    }


def test_health_runtime_exposes_authored_tree_and_missing_evidence() -> None:
    result = compare_health_graph_policy(
        category="surgery",
        query_plan={"answer_mode": "topic_reading", "time_scope": {}},
        observed_answer_mode="topic_reading",
        context={},
    )
    assert result is not None
    assert result["runtime_key"] == "surgery"
    assert result["graph_tree"]["children"][0]["label"] == "Surgery or procedure susceptibility"
    assert "health:D8" in result["missing_required_factors"]
    review = build_health_graph_route(result)
    assert review is not None
    assert review["status"] == "review_needed"
    assert review["question_type"] == "Surgery or procedure susceptibility"


def test_static_health_runtime_ignores_background_timing_removed_from_answer() -> None:
    context = {
        "intent_summary": {"category": "health"},
        "normalized_evidence": {
            "health_body_area": {
                "major_vulnerabilities": [{"zone": "nose"}],
                "medical_profile": {"protective_factors": ["Jupiter support"]},
                "house_map": [
                    {"house": 1}, {"house": 6}, {"house": 8}, {"house": 12},
                ],
            },
        },
        "current_dashas": {"levels": {"MD": "Saturn"}},
        "current_transits": {"planets": {"Saturn": {"house": 9}}},
    }
    result = compare_health_graph_policy(
        category="health",
        query_plan={"answer_mode": "topic_reading", "time_scope": {"requested": "current"}},
        observed_answer_mode="topic_reading",
        context=context,
    )
    assert result is not None
    assert result["unexpected_default_exclusions"] == []
    assert "health:DashaActivation" not in result["observed_factors"]
    assert "health:TransitConfirmation" not in result["observed_factors"]
    assert result["match"] is True
