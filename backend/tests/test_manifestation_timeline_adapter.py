from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from manifestation_kg.timeline import build_timeline_definitions  # noqa: E402
from calculators.event_timeline_accuracy_v3 import build_v3_prediction_model  # noqa: E402


def _keys(context):
    return {definition.knowledge_manifestation_id for definition in build_timeline_definitions(context).definitions}


def test_unconditional_agreement_and_competition_patterns_are_available() -> None:
    keys = _keys({})
    assert "travel.documentation" in keys
    assert "legal.contract_agreement" in keys
    assert "legal.competition_result" in keys
    assert "relationship.remarriage_development" not in keys
    assert "children.second_child_development" not in keys


def test_sensitive_ordinal_and_remarriage_patterns_require_matching_context() -> None:
    keys = _keys({
        "relationship_state": "divorced",
        "explicit_child_orders": ["second"],
    })
    assert "relationship.remarriage_development" in keys
    assert "children.second_child_development" in keys
    assert "children.first_child_development" not in keys
    assert "children.third_child_development" not in keys


def test_topic_and_relative_patterns_require_explicit_context() -> None:
    keys = _keys({
        "explicit_topics": ["legal", "occult"],
        "eligible_relative_subjects": [{"key": "mother"}, {"key": "younger_sibling"}],
        "employment_state": "self_employed",
        "relationship_state": "married",
    })
    expected = {
        "family.mother_development",
        "family.sibling_development",
        "family.in_law_development",
        "legal.dispute_activity",
        "legal.resolution",
        "spirituality.occult_study",
        "career.staff_hiring",
        "career.staff_change",
        "relationship.private_intimacy",
    }
    assert expected <= keys


def test_adapter_exposes_auditable_timeline_roles() -> None:
    bundle = build_timeline_definitions({})
    definition = next(
        value for value in bundle.definitions
        if value.knowledge_manifestation_id == "legal.contract_agreement"
    )
    assert definition.anchor.houses == (7,)
    assert definition.transition.houses == (3,)
    assert definition.outcome.houses == (11,)
    assert definition.outcome.required is True
    assert definition.varga == "D9"
    assert definition.knowledge_review_status == "provisional"
    assert bundle.audit["mode"] == "review_provisional_patterns_allowed"


def test_event_timeline_evaluates_and_exposes_kg_candidate() -> None:
    evidence = [
        {
            "kind": "dasha_lord_transit", "evidence_id": "saturn",
            "dasha_level": "mahadasha", "planet": "Saturn",
            "natal_house": 7, "lordships": [7], "transit_house": 11,
            "aspected_houses": [3], "start_date": "2030-01-01", "end_date": "2030-01-31",
        },
        {
            "kind": "dasha_lord_transit", "evidence_id": "mercury",
            "dasha_level": "pratyantardasha", "planet": "Mercury",
            "natal_house": 3, "lordships": [3], "transit_house": 3,
            "aspected_houses": [11], "start_date": "2030-01-01", "end_date": "2030-01-31",
        },
    ]
    model = build_v3_prediction_model(
        {"divisional_charts": {}},
        {"months": {"1": {"evidence": evidence}}},
        kp_evidence={}, user_facts={}, year=2030, age=40,
    )
    candidate = next(
        row for row in model["months"]["1"]["qualified_candidates"]
        if row["event_key"] == "kg_legal_contract_agreement"
    )
    assert candidate["manifestation_kg"]["pattern_id"] == "pattern.legal.contract_agreement"
    assert candidate["manifestation_kg"]["evidence_gate_result"] == "qualified_candidate"
    assert candidate["anchor_hits"] == [7]
    assert candidate["transition_hits"] == [3]
    assert candidate["outcome_hits"] == [11]
    assert model["manifestation_kg"]["enabled"] is True

    hindi = build_v3_prediction_model(
        {"divisional_charts": {}},
        {"months": {"1": {"evidence": evidence}}},
        kp_evidence={}, user_facts={}, year=2030, age=40, language="hindi",
    )
    hindi_candidate = next(
        row for row in hindi["months"]["1"]["qualified_candidates"]
        if row["event_key"] == "kg_legal_contract_agreement"
    )
    assert hindi_candidate["event_family"] == "अनुबंध, समझौता या बातचीत से बनी सहमति"
    assert hindi_candidate["possible_manifestations"] == []


def test_travel_documentation_does_not_claim_physical_travel_without_departure_trigger(monkeypatch) -> None:
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    evidence = [
        {
            "kind": "dasha_lord_transit", "evidence_id": "saturn",
            "dasha_level": "mahadasha", "planet": "Saturn",
            "natal_house": 8, "lordships": [11], "transit_house": 9,
            "aspected_houses": [3, 11], "start_date": "2030-01-01", "end_date": "2030-01-31",
        },
        {
            "kind": "dasha_lord_transit", "evidence_id": "mercury",
            "dasha_level": "pratyantardasha", "planet": "Mercury",
            "natal_house": 10, "lordships": [3, 12], "transit_house": 3,
            "aspected_houses": [9], "start_date": "2030-01-01", "end_date": "2030-01-31",
        },
    ]
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, {"months": {"1": {"evidence": evidence}}},
        kp_evidence={}, user_facts={}, year=2030, age=40,
    )
    rows = model["months"]["1"]["qualified_candidates"]
    documentation = next(row for row in rows if row["event_key"] == "kg_travel_documentation")
    assert "visa" in documentation["prediction"].lower()
    assert documentation["anchor_hits"] == [9]
    assert documentation["transition_hits"] == [3]
    assert not any(row["event_key"] == "foreign_travel" for row in rows)
