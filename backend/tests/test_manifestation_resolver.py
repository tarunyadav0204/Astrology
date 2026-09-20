from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from manifestation_kg import ActivationPacket, ManifestationResolver  # noqa: E402


def _ids(results):
    return [result.manifestation_id for result in results]


def _resolve(
    houses,
    *,
    domain=None,
    phase="developing",
    method="parashari",
    sensitive=False,
):
    return ManifestationResolver().resolve(
        ActivationPacket(
            active_houses=frozenset(houses),
            method=method,
            domain=domain,
            phase=phase,
            calculator_version="test-calculator/v1",
        ),
        allowed_review_statuses=("provisional",),
        include_sensitive=sensitive,
    )


def test_provisional_patterns_require_explicit_opt_in() -> None:
    packet = ActivationPacket(
        active_houses=frozenset({2, 6, 10, 11}),
        method="parashari",
        domain="career",
        phase="result_window",
    )
    assert ManifestationResolver().resolve(packet) == []


def test_career_chain_returns_specific_results_before_broad_activity() -> None:
    results = _resolve({2, 6, 10, 11}, domain="career", phase="result_window")
    ids = _ids(results)
    assert "career.compensation_progress" in ids
    assert "career.employment_joining" in ids
    assert "career.professional_recognition" in ids
    assert ids.index("career.compensation_progress") < ids.index("career.role_visibility")
    assert all(result.ontology_version == "0.3.2" for result in results)
    assert all(result.calculator_version == "test-calculator/v1" for result in results)


def test_preparation_does_not_become_separation_without_house_twelve() -> None:
    ids = _ids(_resolve({3, 6, 10, 11}, domain="career", phase="preparatory"))
    assert "career.job_change_preparation" in ids
    assert "career.job_separation" not in ids


def test_relationship_contact_and_reconciliation_are_distinct() -> None:
    contact = _ids(_resolve({3, 5, 7}, domain="relationships"))
    reconciled = _ids(_resolve({3, 5, 7, 11}, domain="relationships"))
    assert "relationship.communication" in contact
    assert "relationship.reconciliation" not in contact
    assert "relationship.reconciliation" in reconciled


def test_domain_filter_prevents_unrelated_same_house_matches() -> None:
    houses = {2, 4, 5, 9, 11}
    property_ids = _ids(_resolve(houses, domain="home_property", phase="result_window"))
    education_ids = _ids(_resolve(houses, domain="education", phase="result_window"))
    assert "property.acquisition" in property_ids
    assert "education.admission" not in property_ids
    assert "education.admission" in education_ids
    assert "property.acquisition" not in education_ids


def test_phase_prevents_documentation_copy_after_result_phase() -> None:
    preparatory = _ids(_resolve({3, 4, 9, 11, 12}, domain="foreign_life", phase="preparatory"))
    result = _ids(_resolve({3, 4, 9, 11, 12}, domain="foreign_life", phase="result_window"))
    assert "travel.documentation" in preparatory
    assert "travel.foreign_settlement" not in preparatory
    assert "travel.documentation" not in result
    assert "travel.foreign_settlement" in result


def test_unbounded_house_nine_activation_preserves_parallel_meanings() -> None:
    ids = _ids(_resolve({3, 9, 11}, domain=None, phase="preparatory"))
    assert {
        "travel.documentation",
        "family.father_communication_support",
        "guidance.mentor_guru_support",
        "education.higher_learning_application",
        "creativity.publishing_reach",
        "general.supportive_opportunity",
        "spirituality.pilgrimage_preparation",
    }.issubset(ids)


def test_context_filters_house_nine_without_changing_its_meanings() -> None:
    foreign_ids = _ids(_resolve({3, 9, 11}, domain="foreign_life", phase="preparatory"))
    family_ids = _ids(_resolve({3, 9, 11}, domain="family", phase="preparatory"))
    education_ids = _ids(_resolve({3, 9, 11}, domain="education", phase="preparatory"))
    assert foreign_ids == ["travel.documentation"]
    assert family_ids == ["family.father_communication_support"]
    assert education_ids == ["education.higher_learning_application"]


def test_obstruction_is_reported_without_erasing_a_valid_pattern() -> None:
    results = _resolve({2, 6, 8, 10, 11, 12}, domain="career", phase="result_window")
    recognition = next(row for row in results if row.manifestation_id == "career.professional_recognition")
    assert recognition.matched_obstructing_houses == (8, 12)
    assert recognition.rank_score < next(
        row for row in _resolve({2, 6, 10, 11}, domain="career", phase="result_window")
        if row.manifestation_id == "career.professional_recognition"
    ).rank_score


def test_sensitive_manifestations_are_separately_gated() -> None:
    packet_ids = _ids(_resolve({1, 5, 6, 11}, domain="health", phase="result_window"))
    sensitive_ids = _ids(
        _resolve({1, 5, 6, 11}, domain="health", phase="result_window", sensitive=True)
    )
    assert "health.recovery_support" not in packet_ids
    assert "health.recovery_support" in sensitive_ids


def test_shared_semantics_are_available_to_each_method_without_mixing_calculation() -> None:
    parashari = _ids(_resolve({3, 9, 12}, domain="foreign_life", method="parashari"))
    kp = _ids(_resolve({3, 9, 12}, domain="foreign_life", method="kp"))
    daily = _ids(_resolve({3, 9, 12}, domain="foreign_life", method="daily"))
    assert parashari == kp == daily


def test_activation_packet_rejects_invalid_method_house_and_phase() -> None:
    for kwargs in (
        {"active_houses": frozenset({0, 10}), "method": "kp"},
        {"active_houses": frozenset({10}), "method": "mixed"},
        {"active_houses": frozenset({10}), "method": "kp", "phase": "peak"},
    ):
        try:
            ActivationPacket(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Invalid packet accepted: {kwargs}")


def test_match_serialization_keeps_audit_fields() -> None:
    result = _resolve({3, 9, 12}, domain="foreign_life")[0].as_dict()
    assert result["manifestation_id"]
    assert result["pattern_id"]
    assert result["source_ids"]
    assert result["claim_basis"] in {"traditional_derived", "modern_mapping"}
    assert result["review_status"] == "provisional"
    assert result["ontology_version"] == "0.3.2"


def test_semantic_interpretation_covers_every_non_empty_house_combination() -> None:
    resolver = ManifestationResolver()
    for mask in range(1, 1 << 12):
        houses = frozenset(
            house for house in range(1, 13)
            if mask & (1 << (house - 1))
        )
        result = resolver.interpret(ActivationPacket(houses, method="parashari"))
        assert result.active_houses == tuple(sorted(houses))
        assert {meaning.house for meaning in result.house_meanings} == set(houses)
        assert result.domain_candidates
        assert result.coverage_status == "semantic_only"


def test_one_six_eight_keeps_health_conflict_debt_and_transformation_meanings() -> None:
    result = ManifestationResolver().interpret(
        ActivationPacket(frozenset({1, 6, 8}), method="parashari", phase="developing"),
        allowed_review_statuses=("provisional",),
        include_sensitive=True,
    )
    meaning_ids = {meaning.meaning_id for meaning in result.house_meanings}
    assert {
        "house.1.vitality",
        "house.6.health",
        "house.6.debt",
        "house.6.dispute",
        "house.8.vulnerability",
        "house.8.shared_resources",
        "house.8.consequential_change",
    }.issubset(meaning_ids)
    assert result.domain_candidates[0].domain == "domain.health"
    assert "health.attention" in {
        match.manifestation_id for match in result.manifestation_matches
    }


def test_requested_domain_filters_lenses_but_preserves_house_polysemy() -> None:
    result = ManifestationResolver().interpret(
        ActivationPacket(
            frozenset({3, 9, 11}), method="parashari",
            domain="foreign_life", phase="preparatory",
        ),
        allowed_review_statuses=("provisional",),
    )
    assert [candidate.domain for candidate in result.domain_candidates] == ["domain.foreign_life"]
    meanings = {meaning.meaning_id: meaning for meaning in result.house_meanings}
    assert meanings["house.9.long_journey"].relevant_to_requested_domain is True
    assert meanings["house.9.father"].relevant_to_requested_domain is False
    assert meanings["house.9.guru"].relevant_to_requested_domain is False
    assert result.ambiguity_preserved is False


def test_semantic_only_result_is_distinct_from_specific_event_claim() -> None:
    result = ManifestationResolver().interpret(
        ActivationPacket(frozenset({1, 2, 3}), method="kp")
    )
    assert result.coverage_status == "semantic_only"
    assert result.manifestation_matches == ()
    serialized = result.as_dict()
    assert serialized["status"] == "resolved"
    assert "not event probability" in serialized["claim_boundary"]
