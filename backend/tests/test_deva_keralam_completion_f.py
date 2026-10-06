from collections import Counter
from pathlib import Path

from classical_rules.deva_keralam.completion_ledger import load_completion_ledger
from classical_rules.deva_keralam.reviewed_manifest import (
    compile_reviewed_manifest,
    load_reviewed_manifest,
)


DATA_DIR = Path(__file__).parents[1] / "classical_rules" / "deva_keralam" / "data"


def test_completion_f_accounts_for_every_assigned_catalogue_record():
    ledger = load_completion_ledger(DATA_DIR / "completion_ledger_f_v1.json")

    assert (ledger.catalog_ordinal_start, ledger.catalog_ordinal_end) == (587, 878)
    assert len(ledger.rows) == 292
    assert Counter(row.disposition for row in ledger.rows) == {
        "executable": 2,
        "already_reviewed": 21,
        "unsupported_fact": 76,
        "timing_pending": 71,
        "ambiguous_context": 56,
        "mortality_excluded": 46,
        "corrupt_or_disputed": 20,
    }


def test_completion_f_new_rules_pass_the_guarded_compiler():
    manifest = load_reviewed_manifest(DATA_DIR / "reviewed_batch_f_v1.json")
    results = compile_reviewed_manifest(manifest)

    assert len(results) == 2
    assert all(result.compiled for result in results)
    assert all(not result.issues for result in results)


def test_verse_2605_preserves_saturn_to_mars_aspect_direction():
    manifest = load_reviewed_manifest(DATA_DIR / "reviewed_batch_f_v1.json")
    candidate = next(row for row in manifest.candidates if row.source.verse_start == 2605)
    serialized = str(candidate.expression)

    assert "deva_keralam.relationship.aspect.Saturn.Mars.present" in serialized
    assert "deva_keralam.relationship.aspect.Mars.Saturn.present" not in serialized
