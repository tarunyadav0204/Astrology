import json

import pytest
from pydantic import ValidationError

from classical_rules.deva_keralam.completion_ledger import (
    BOOK_1_CATALOGUE_COUNT,
    LEDGER_SCHEMA_VERSION,
    audit_completion_ledgers,
    load_completion_ledger,
)


def _ledger(start, end):
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "edition_key": "deva_keralam_volume_1_scan",
        "stream_key": f"test-{start}-{end}",
        "catalog_ordinal_start": start,
        "catalog_ordinal_end": end,
        "source_snapshot_count": BOOK_1_CATALOGUE_COUNT,
        "rows": [{
            "catalogue_ordinal": ordinal,
            "passage_key": f"PASSAGE.{ordinal}",
            "pdf_page": min(260, ordinal),
            "verse_start": ordinal,
            "verse_end": ordinal,
            "disposition": "commentary_only",
            "candidate_keys": [],
            "reason": "Test catalogue commentary.",
            "source_check": "catalogue",
        } for ordinal in range(start, end + 1)],
    }


def test_ledger_requires_exact_contiguous_stream_coverage(tmp_path):
    payload = _ledger(1, 2)
    payload["rows"].pop()
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValidationError, match="cover their declared ordinal range"):
        load_completion_ledger(path)


def test_combined_audit_requires_all_878_catalogue_rows(tmp_path):
    paths = []
    for label, bounds in zip("def", ((1, 293), (294, 586), (587, 878))):
        path = tmp_path / f"{label}.json"
        path.write_text(json.dumps(_ledger(*bounds)))
        paths.append(path)
    audit = audit_completion_ledgers(paths)
    assert audit.valid
    assert audit.rows == 878
    assert audit.disposition_counts == {"commentary_only": 878}


def test_combined_audit_can_verify_rule_links(tmp_path):
    paths = []
    for label, bounds in zip("def", ((1, 293), (294, 586), (587, 878))):
        payload = _ledger(*bounds)
        if bounds[0] == 1:
            payload["rows"][0].update({
                "disposition": "already_reviewed",
                "candidate_keys": ["DK.EXISTING"],
            })
        path = tmp_path / f"{label}.json"
        path.write_text(json.dumps(payload))
        paths.append(path)
    assert audit_completion_ledgers(paths, known_candidate_keys={"DK.EXISTING"}).valid
    audit = audit_completion_ledgers(paths, known_candidate_keys=set())
    assert not audit.valid
    assert "unknown candidate keys" in audit.issues[0]


def test_new_executable_rule_requires_page_image_review(tmp_path):
    payload = _ledger(1, 1)
    payload["rows"][0].update({
        "disposition": "executable",
        "candidate_keys": ["DK.TEST"],
        "source_check": "ocr_context",
    })
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValidationError, match="page-image"):
        load_completion_ledger(path)
