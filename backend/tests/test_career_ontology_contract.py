from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.career_graph_policy import CareerGraphPolicyStore  # noqa: E402
from instant_chat_v2.career import CAREER_PROFILES  # noqa: E402
from instant_chat_v2.career_graph_runtime import (  # noqa: E402
    build_career_graph_route,
    career_graph_runtime_key,
    compare_career_graph_policy,
    resolve_career_graph_inputs,
)


def test_career_ontology_compiles_and_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_career_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "29 competency questions" in result.stdout


def test_compiled_bundle_has_all_twenty_nine_distinct_routes() -> None:
    store = CareerGraphPolicyStore()
    assert len(store.runtime_keys()) == 29
    assert store.resolve("not-a-route") is None


def test_static_overall_career_cannot_silently_add_timing() -> None:
    policy = CareerGraphPolicyStore().require("general")
    assert "career:DashaActivation" in policy.default_exclusions
    assert "career:TransitActivation" in policy.default_exclusions
    assert "career:CapDashaActivation" not in policy.required_capabilities


def test_manager_route_requires_manager_house_not_vocation_shortcut() -> None:
    policy = CareerGraphPolicyStore().require("manager_relationship")
    assert "career:H9" in policy.required_factors
    assert "career:Amatyakaraka" in policy.default_exclusions


def test_job_change_requires_movement_release_and_landing_rules() -> None:
    policy = CareerGraphPolicyStore().require("job_change_timing")
    assert {"career:H3", "career:H10", "career:H12"}.issubset(policy.required_factors)
    assert {"career:RuleChange", "career:RuleSeparation", "career:RuleLanding"}.issubset(policy.decision_rules)


def test_promotion_graph_exposes_exact_authored_hierarchy() -> None:
    policy = CareerGraphPolicyStore().require("promotion")
    assert policy.question_label == "Promotion and advancement"
    assert policy.graph_tree is not None
    assert policy.graph_tree["label"] == "Question type"

    question = policy.graph_tree["children"][0]
    assert question["label"] == "Promotion and advancement"
    stages = next(node for node in question["children"] if node["label"] == "Decision stages")
    assert [node["label"] for node in stages["children"]] == [
        "Increased responsibility and visibility",
        "Recognition and advancement",
        "Compensation and formalization",
    ]

    recognition = stages["children"][1]
    factors = next(
        node for node in recognition["children"]
        if node["label"] == "Required astrology factors"
    )
    assert [node["label"] for node in factors["children"]] == [
        "Role, status, authority and visible responsibility",
        "Recognition, gains, networks and goals",
    ]


def test_every_career_route_exposes_decision_stages_and_factor_children() -> None:
    store = CareerGraphPolicyStore()
    for runtime_key in store.runtime_keys():
        policy = store.require(runtime_key)
        assert policy.graph_tree is not None, runtime_key
        question = policy.graph_tree["children"][0]
        stages = next(
            (node for node in question["children"] if node["label"] == "Decision stages"),
            None,
        )
        assert stages is not None, f"{runtime_key} has no Decision stages child"
        assert stages["children"], f"{runtime_key} has no authored decision-stage nodes"
        for stage in stages["children"]:
            factors = next(
                (
                    node for node in stage.get("children", [])
                    if node["label"] == "Required astrology factors"
                ),
                None,
            )
            assert factors is not None, f"{runtime_key}/{stage['label']} has no factor branch"
            assert factors["children"], f"{runtime_key}/{stage['label']} has no factor nodes"


def test_business_route_has_declared_client_and_enterprise_factor() -> None:
    policy = CareerGraphPolicyStore().require("business_vs_employment")
    assert "career:H7" in policy.required_factors
    assert "career:NoBusinessFromH7Alone" in policy.guardrails


def _context(*, houses=(2, 6, 10, 11), jaimini=True, timing=False):
    foundation = {
        "D1": {"houses": [{"house": house} for house in houses]},
        "D10": {"calculated_chart": {"ascendant": 1}},
        "amatyakaraka": {"planet": "Mercury"} if jaimini else {},
        "KARAKAMSHA": {"ascendant": 8} if jaimini else {},
    }
    return {
        "instant_parashari": {"career_foundation": foundation},
        "current_dashas": {"levels": {"MD": "Saturn"} if timing else {}},
        "current_transits": {"planets": {"Saturn": {"house": 2}} if timing else {}},
    }


def test_runtime_resolves_existing_subtypes_to_graph_routes() -> None:
    assert career_graph_runtime_key("career", "job_vs_business") == "business_vs_employment"
    assert career_graph_runtime_key("career", "salary") == "salary_increase"
    assert career_graph_runtime_key("career", "employment") == "employment"
    assert career_graph_runtime_key("career", "career_stagnation") == "career_stagnation"
    assert career_graph_runtime_key("health", "general") is None


def test_static_career_runtime_matches_without_timing() -> None:
    result = compare_career_graph_policy(
        category="career", routed_subtype="general", observed_answer_mode="topic_reading",
        context=_context(),
    )
    assert result is not None
    assert result["match"] is True
    assert result["missing_required_factors"] == []
    assert result["unexpected_default_exclusions"] == []


def test_static_career_runtime_flags_incidental_timing() -> None:
    result = compare_career_graph_policy(
        category="career", routed_subtype="general", observed_answer_mode="topic_reading",
        context=_context(timing=True),
    )
    assert result is not None
    assert result["match"] is False
    assert result["unexpected_default_exclusions"] == [
        "career:DashaActivation", "career:TransitActivation"
    ]


def test_manager_runtime_requires_house_nine() -> None:
    result = compare_career_graph_policy(
        category="career", routed_subtype="manager_relationship",
        observed_answer_mode="relationship_person", context=_context(houses=(6, 10, 11), jaimini=False),
    )
    assert result is not None
    assert "career:H9" in result["missing_required_factors"]


def test_runtime_policy_evaluation_is_deterministic() -> None:
    result = compare_career_graph_policy(
        category="career", routed_subtype="general", observed_answer_mode="topic_reading",
        context=_context(),
    )
    assert result and result["match"] is True


def test_every_non_graph_career_profile_has_a_compiled_graph_route() -> None:
    store = CareerGraphPolicyStore()
    for subtype in CAREER_PROFILES:
        runtime_key = career_graph_runtime_key("career", subtype)
        assert runtime_key is not None, subtype
        assert store.resolve(runtime_key) is not None, subtype


def test_graph_review_exposes_selected_and_missing_nodes() -> None:
    review = build_career_graph_route({
        "match": False,
        "runtime_key": "manager_relationship",
        "expected_answer_mode": "relationship_person",
        "observed_answer_mode": "topic_reading",
        "mode_match": False,
        "required_factors": ["career:H9", "career:D1Foundation"],
        "observed_factors": ["career:D1Foundation", "career:D10Confirmation"],
        "decision_rules": ["career:RuleAuthorityRelationship"],
        "guardrails": ["career:NoVocationShortcut"],
        "required_capabilities": [],
        "answer_contract": "career:RelationshipAnswerContract",
        "evidence_policy": "career:RelationshipEvidencePolicy",
    })
    assert review is not None
    assert review["status"] == "review_needed"
    assert review["mode_match"] is False
    assert review["required_nodes"] == [
        {"id": "career:H9", "label": "House 9 · manager, mentors and guidance", "selected": False},
        {"id": "career:D1Foundation", "label": "D1 career foundation", "selected": True},
    ]
    assert review["additional_selected_nodes"] == [
        {"id": "career:D10Confirmation", "label": "D10 professional confirmation"}
    ]


def test_event_prediction_resolves_graph_route_from_final_career_foundation() -> None:
    context = _context(timing=True)
    context["intent_summary"] = {
        "category": "career",
        "answer_mode": "event_prediction",
    }
    context["instant_parashari"]["career_foundation"]["career_subtype"] = "promotion"
    resolved = resolve_career_graph_inputs(
        intent={"category": "career"},
        context=context,
        query_plan={"category": "career", "answer_mode": "event_prediction"},
    )
    assert resolved == {
        "category": "career",
        "routed_subtype": "promotion",
        "observed_answer_mode": "event_prediction",
    }
    comparison = compare_career_graph_policy(context=context, **resolved)
    assert comparison is not None
    assert comparison["runtime_key"] == "promotion"
    review = build_career_graph_route(comparison)
    assert review is not None
    assert review["question_type"] == "Promotion and advancement"
    assert review["graph_tree"]["children"][0]["label"] == "Promotion and advancement"
