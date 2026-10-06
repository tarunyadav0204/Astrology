from pathlib import Path

from classical_rules.deva_keralam.abala_prabhaa_slice import (
    APPROVED_CANDIDATES,
    REJECTED_CANDIDATES,
)
from classical_rules.deva_keralam.chapter_01 import RULES as PILOT_RULES
from classical_rules.deva_keralam.completion_ledger import audit_completion_ledgers
from classical_rules.deva_keralam.reviewed_batches import discover_reviewed_manifests
from classical_rules.deva_keralam.reviewed_manifest import load_reviewed_manifest


DATA_DIR = Path(__file__).resolve().parents[1] / "classical_rules" / "deva_keralam" / "data"


def test_all_878_catalogue_passages_have_one_linked_disposition():
    manifest_paths = discover_reviewed_manifests(DATA_DIR)
    known_keys = {
        candidate.key
        for candidate in (*APPROVED_CANDIDATES, *REJECTED_CANDIDATES)
    } | {rule.key for rule in PILOT_RULES}
    for path in manifest_paths:
        known_keys.update(candidate.key for candidate in load_reviewed_manifest(path).candidates)

    ledger_paths = tuple(sorted(DATA_DIR.glob("completion_ledger_*_v*.json")))
    assert [path.name for path in ledger_paths] == [
        "completion_ledger_d_v1.json",
        "completion_ledger_e_v1.json",
        "completion_ledger_f_v1.json",
    ]
    audit = audit_completion_ledgers(ledger_paths, known_candidate_keys=known_keys)
    assert audit.valid, audit.issues
    assert audit.rows == 878
    assert audit.disposition_counts == {
        "already_reviewed": 92,
        "ambiguous_context": 168,
        "commentary_only": 15,
        "corrupt_or_disputed": 52,
        "duplicate": 1,
        "executable": 4,
        "impossible_geometry": 1,
        "mortality_excluded": 166,
        "timing_pending": 220,
        "unsupported_fact": 159,
    }
