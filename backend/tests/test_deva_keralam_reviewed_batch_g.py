from collections import Counter
from pathlib import Path

import pytest

from classical_rules.deva_keralam.completion_backlog import load_completion_backlog
from classical_rules.deva_keralam.reviewed_manifest import (
    compile_reviewed_manifest,
    load_reviewed_manifest,
)
from classical_rules.facts import ClassicalFact, ClassicalFactSet, evaluate_fact_expression


DATA_DIR = Path(__file__).parents[1] / "classical_rules" / "deva_keralam" / "data"
HIGH_PRIORITY_ORDINALS = {
    52, 56, 78, 88, 90, 140, 148, 207, 246, 248,
    349, 354, 364, 382, 393, 426, 468, 472, 489, 528,
    590, 598, 609, 649, 669, 700, 714, 728, 781, 790,
}


def _manifest():
    return load_reviewed_manifest(DATA_DIR / "reviewed_batch_g_v1.json")


def _fact_nodes(expression):
    if expression.get("op") == "fact":
        yield expression
    for child in expression.get("children") or ():
        yield from _fact_nodes(child)


def _facts_for(expression, *, mutate_first=False):
    facts = []
    for index, node in enumerate(_fact_nodes(expression)):
        value = node["value"]
        if mutate_first and index == 0:
            if type(value) is bool:
                value = not value
            elif type(value) in (int, float):
                value = value + 1
            else:
                value = f"not-{value}"
        facts.append(ClassicalFact(
            key=node["key"],
            value=value,
            source_rules=("test",),
            source_references=("batch-g",),
            calculator_bindings=("test",),
        ))
    return ClassicalFactSet(facts)


def test_batch_g_records_all_30_page_review_decisions_fail_closed():
    manifest = _manifest()
    results = compile_reviewed_manifest(manifest)

    assert len(manifest.candidates) == 30
    assert Counter(row.decision for row in manifest.candidates) == {
        "approved": 7,
        "rejected": 23,
    }
    assert sum(result.compiled for result in results) == 7
    assert all(
        row.inherited_context.get("source_check") == "page_image_context"
        for row in manifest.candidates
    )
    by_key = {result.candidate_key: result for result in results}
    assert all(by_key[row.key].compiled for row in manifest.candidates if row.decision == "approved")
    assert all(not by_key[row.key].compiled for row in manifest.candidates if row.decision == "rejected")


@pytest.mark.parametrize("candidate", [row for row in _manifest().candidates if row.decision == "approved"], ids=lambda row: row.key)
def test_every_approved_batch_g_expression_has_positive_and_negative_match(candidate):
    positive = evaluate_fact_expression(candidate.expression, _facts_for(candidate.expression))
    negative = evaluate_fact_expression(candidate.expression, _facts_for(candidate.expression, mutate_first=True))

    assert positive.matched is True
    assert negative.matched is False


def test_high_priority_backlog_rows_are_resolved_without_changing_full_coverage():
    backlog = load_completion_backlog(DATA_DIR / "ambiguous_context_backlog_v1.json")
    selected = [row for row in backlog.entries if row.catalogue_ordinal in HIGH_PRIORITY_ORDINALS]

    assert len(backlog.entries) == 168
    assert len(selected) == 30
    assert Counter(row.resolution for row in selected) == {
        "implementable_now": 7,
        "excluded": 23,
    }
    assert all("Rendered page and adjacent context reviewed" in row.details for row in selected)


def test_known_unmapped_nadi_labels_are_not_smuggled_into_executable_expressions():
    manifest = _manifest()
    approved_text = " ".join(str(row.expression) for row in manifest.candidates if row.decision == "approved")

    for unresolved in ("Agada", "Varuna", "Varuni", "Guha", "Uraga", "Sumathi"):
        assert unresolved not in approved_text
