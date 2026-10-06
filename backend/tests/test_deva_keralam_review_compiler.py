from dataclasses import replace

import pytest

from classical_rules.deva_keralam.abala_prabhaa_slice import (
    ALL_CANDIDATES,
    APPROVED_CANDIDATES,
    COMPILATION_RESULTS,
    FIXTURES,
    REJECTIONS,
    RULES,
    coverage,
)
from classical_rules.deva_keralam.review_compiler import compile_reviewed_candidate


def _codes(result):
    return {issue.code for issue in result.issues}


def test_first_complete_slice_has_a_review_decision_for_every_candidate():
    summary = coverage()
    assert summary == {
        "context_block_key": "DK1.CTX.ABALA_PRABHA.V0054-0096",
        "verse_start": 54,
        "verse_end": 96,
        "reviewed_candidates": 27,
        "compiled_rules": 12,
        "rejected_candidates": 15,
        "globally_registered": False,
    }
    assert len(COMPILATION_RESULTS) == len(ALL_CANDIDATES)
    assert len({candidate.key for candidate in ALL_CANDIDATES}) == len(ALL_CANDIDATES)


def test_compiled_rules_are_source_linked_and_do_not_hide_the_alias_resolution():
    assert len(RULES) == 12
    candidates = {candidate.key: candidate for candidate in APPROVED_CANDIDATES}
    for rule in RULES:
        definition = rule.public_definition()
        assert definition["source"]["edition_key"] == "deva_keralam_volume_1_scan"
        assert definition["source"]["pdf_pages"]
        assert definition["source"]["printed_pages"]
        assert definition["source"]["reference"].startswith("Deva Keralam, Book 1, verse")
        uses_nadiamsa = any(
            premise["key"].startswith("deva_keralam.ascendant.nadiamsa.")
            for premise in candidates[rule.key].expression["children"]
        )
        if uses_nadiamsa:
            assert any("Prabhaa" in note for note in definition["notes"])
        else:
            assert any("independent branch" in note for note in definition["notes"])
        assert any("no draft-table auto-publication" in note for note in definition["notes"])


def test_every_compiled_rule_has_a_positive_and_negative_fixture():
    rules = {rule.key: rule for rule in RULES}
    assert len(FIXTURES) == 2 * len(RULES)
    for fixture in FIXTURES:
        evidence = rules[fixture.rule_key].evaluator(fixture.chart, None)
        assert evidence["applicability"] == fixture.expected_applicability
        if fixture.kind == "positive":
            assert evidence["outcome"]["timing"] is None
            assert evidence["inherited_context"]["passage_key"].startswith("DK1.PASSAGE.")
        else:
            assert "outcome" not in evidence


def test_missing_precision_is_unavailable_for_an_executable_slice_rule():
    fixture = next(row for row in FIXTURES if row.kind == "positive")
    chart = {"classical_facts": dict(fixture.chart["classical_facts"])}
    chart["classical_facts"].pop("deva_keralam.precision.ascendant.reliable")
    evidence = RULES[0].evaluator(chart, None)
    assert evidence["applicability"] == "unavailable"
    assert "birth time" in evidence["reason"]


def test_rejection_audit_exercises_every_required_guard():
    codes = {code for result in REJECTIONS for code in _codes(result)}
    assert {"unknown_fact", "inherited_ambiguity", "source_dispute", "unsupported_timing"} <= codes


@pytest.mark.parametrize(
    ("candidate", "expected_code"),
    [
        (replace(APPROVED_CANDIDATES[0], review_status="draft"), "not_reviewed"),
        (replace(APPROVED_CANDIDATES[0], context_status="inferred"), "unreviewed_context"),
        (replace(APPROVED_CANDIDATES[0], precision_requirements=()), "missing_precision_policy"),
        (replace(APPROVED_CANDIDATES[0], source_disputes=("two readings",)), "source_dispute"),
        (replace(APPROVED_CANDIDATES[0], inherited_ambiguities=("pronoun has two antecedents",)), "inherited_ambiguity"),
        (replace(APPROVED_CANDIDATES[0], timing_kind="dasha"), "unsupported_timing"),
    ],
)
def test_compiler_rejects_unguarded_candidate(candidate, expected_code):
    result = compile_reviewed_candidate(candidate)
    assert result.rule is None
    assert expected_code in _codes(result)


def test_compiler_rejects_unknown_and_impossible_fact_conditions():
    base = APPROVED_CANDIDATES[0]
    unknown = replace(
        base,
        expression={"op": "fact", "key": "deva_keralam.invented.answer", "comparator": "equals", "value": 1},
    )
    assert "unknown_fact" in _codes(compile_reviewed_candidate(unknown))

    conflict = replace(
        base,
        expression={
            "op": "all",
            "children": [
                {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.half", "comparator": "equals", "value": "former"},
                {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.half", "comparator": "equals", "value": "latter"},
            ],
        },
    )
    assert "impossible_condition" in _codes(compile_reviewed_candidate(conflict))

    wrong_pair = replace(
        base,
        expression={
            "op": "all",
            "children": [
                {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.ordinal", "comparator": "equals", "value": 16},
                {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.name", "comparator": "equals", "value": "Kaalaa"},
            ],
        },
    )
    assert "impossible_condition" in _codes(compile_reviewed_candidate(wrong_pair))

    astronomically_impossible = replace(
        base,
        expression={
            "op": "all",
            "children": [
                {"op": "fact", "key": "deva_keralam.ascendant.rashi.name", "comparator": "equals", "value": "Taurus"},
                {"op": "fact", "key": "deva_keralam.ascendant.navamsa.name", "comparator": "equals", "value": "Aries"},
                {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.ordinal", "comparator": "equals", "value": 16},
                {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.name", "comparator": "equals", "value": "Prabhaa"},
            ],
        },
    )
    assert "impossible_ascendant_context" in _codes(compile_reviewed_candidate(astronomically_impossible))


def test_verse_67_matches_a_real_chart_adapter_and_fails_when_rahu_is_not_with_mercury():
    from classical_rules.deva_keralam.service import match_deva_keralam_chart

    def chart(rahu_longitude):
        return {
            # Taurus 26°51′: Prabhaa ordinal 16, former half, Virgo Navamsa.
            "ascendant": 56.85,
            "planets": {
                "Sun": {"longitude": 15.0},
                "Moon": {"longitude": 100.0},
                "Mars": {"longitude": 190.0},
                "Mercury": {"longitude": 70.0},
                "Jupiter": {"longitude": 220.0},
                "Venus": {"longitude": 125.0},
                "Saturn": {"longitude": 340.0},
                "Rahu": {"longitude": rahu_longitude},
                "Ketu": {"longitude": (rahu_longitude + 180.0) % 360.0},
            },
        }

    positive = match_deva_keralam_chart(
        chart(71.0),
        birth_context={"ascendant_longitude_uncertainty_arcseconds": 20},
        rules=RULES,
    )
    negative = match_deva_keralam_chart(
        chart(101.0),
        birth_context={"ascendant_longitude_uncertainty_arcseconds": 20},
        rules=RULES,
    )
    rule_key = "DK.1.67.PRABHAA_FORMER_PROGENY_OBSTACLE"
    positive_row = next(row for row in positive["results"] if row["rule_key"] == rule_key)
    negative_row = next(row for row in negative["results"] if row["rule_key"] == rule_key)
    assert positive_row["applicability"] == "matched"
    assert negative_row["applicability"] == "not_matched"
    assert positive["facts"]["facts"]["deva_keralam.ascendant.navamsa.name"]["value"] == "Virgo"


def test_slice_is_not_added_to_global_rule_registry():
    from classical_rules.registry import list_packs

    assert all(row["work_key"] != "deva_keralam" for row in list_packs())
