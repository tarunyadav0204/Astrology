import json

import pytest

from classical_rules.deva_keralam.reviewed_batches import (
    audit_reviewed_manifests,
    load_reviewed_rule_pack,
)
from classical_rules.deva_keralam.reviewed_manifest import MANIFEST_SCHEMA_VERSION


def _candidate(key="DK.1.TEST.SUN_H1", decision="approved"):
    row = {
        "key": key,
        "title": "Reviewed test condition",
        "passage_key": f"PASSAGE.{key}",
        "context_block_key": "CTX.TEST",
        "decision": decision,
        "source": {
            "verse_start": 100,
            "verse_end": 100,
            "pdf_pages": [40],
            "printed_pages": [15],
            "reference_label": "Deva Keralam, Book 1, verse 100",
            "editorial_status": "reviewed_clear",
            "numbering_note": "Pinned supplied scan.",
        },
        "expression": {
            "op": "fact",
            "key": "deva_keralam.planet.Sun.house",
            "comparator": "equals",
            "value": 1,
        },
        "outcome": {
            "topic": "identity",
            "prediction_kind": "natal_promise",
            "traditional_results": ["Source-bounded result."],
            "timing": None,
        },
        "context_status": "verified",
    }
    if decision == "rejected":
        row["operationalization_status"] = "unsupported_condition"
    return row


def _manifest(batch, start, end, candidates):
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "batch_key": batch,
        "edition_key": "deva_keralam_volume_1_scan",
        "source_scope": {"pdf_pages": [start, end]},
        "reviewer_method": "Direct page-image review",
        "candidates": candidates,
    }


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_book_audit_accepts_decisions_that_match_the_guarded_compiler(tmp_path):
    path = _write(tmp_path / "reviewed_batch_a_v1.json", _manifest(
        "DK1.A", 37, 110, [_candidate(), _candidate("DK.1.TEST.REJECTED", "rejected")],
    ))
    audit = audit_reviewed_manifests([path])
    assert audit.valid
    assert audit.reviewed_candidates == 2
    assert audit.approved_candidates == 1
    assert audit.rejected_candidates == 1
    assert audit.compiled_rules == 1
    pack = load_reviewed_rule_pack([path])
    assert [rule.key for rule in pack.rules] == ["DK.1.TEST.SUN_H1"]


def test_book_audit_rejects_duplicate_keys_and_out_of_scope_pages(tmp_path):
    first = _write(tmp_path / "reviewed_batch_a_v1.json", _manifest(
        "DK1.A", 37, 50, [_candidate()],
    ))
    second_payload = _manifest("DK1.B", 51, 60, [_candidate()])
    second_payload["candidates"][0]["source"]["pdf_pages"] = [40]
    second = _write(tmp_path / "reviewed_batch_b_v1.json", second_payload)
    audit = audit_reviewed_manifests([first, second])
    assert not audit.valid
    assert {issue.code for issue in audit.issues} == {
        "duplicate_candidate_key",
        "source_page_outside_batch_scope",
    }
    with pytest.raises(ValueError, match="failed audit"):
        load_reviewed_rule_pack([first, second])
