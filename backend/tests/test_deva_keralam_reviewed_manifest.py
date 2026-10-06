import json

import pytest
from pydantic import ValidationError

from classical_rules.deva_keralam.reviewed_manifest import (
    MANIFEST_SCHEMA_VERSION,
    compile_reviewed_manifest,
    load_reviewed_manifest,
    manifest_summary,
)


def _manifest():
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "batch_key": "DK1.REVIEW.TEST",
        "edition_key": "deva_keralam_volume_1_scan",
        "source_scope": {"pdf_pages": [40, 40]},
        "reviewer_method": "Direct page-image review",
        "candidates": [{
            "key": "DK.1.TEST.SUN_H1",
            "title": "Test reviewed condition",
            "passage_key": "DK1.PASSAGE.TEST",
            "context_block_key": "DK1.CTX.TEST",
            "decision": "approved",
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
                "traditional_results": ["Source-bounded test result."],
                "timing": None,
            },
            "context_status": "verified",
            "topics": ["identity"],
        }],
    }


def test_manifest_loads_and_compiles_without_registration(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest()))
    manifest = load_reviewed_manifest(path)
    results = compile_reviewed_manifest(manifest)
    assert len(results) == 1
    assert results[0].compiled is True
    assert manifest_summary(manifest) == {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "batch_key": "DK1.REVIEW.TEST",
        "reviewed_candidates": 1,
        "compiled_rules": 1,
        "rejected_candidates": 0,
        "globally_registered": False,
    }


def test_approved_manifest_record_cannot_keep_an_unresolved_blocker(tmp_path):
    payload = _manifest()
    payload["candidates"][0]["inherited_ambiguities"] = ["unclear antecedent"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValidationError):
        load_reviewed_manifest(path)


def test_manifest_rejects_unknown_fields(tmp_path):
    payload = _manifest()
    payload["candidates"][0]["invented"] = True
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValidationError):
        load_reviewed_manifest(path)
