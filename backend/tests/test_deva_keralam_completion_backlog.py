import json

from classical_rules.deva_keralam.completion_backlog import (
    BACKLOG_SCHEMA_VERSION,
    audit_backlog_against_ledger,
    load_completion_backlog,
)
from classical_rules.deva_keralam.completion_ledger import CompletionLedgerRow


def test_backlog_must_cover_the_corresponding_ledger_rows(tmp_path):
    path = tmp_path / "timing.json"
    path.write_text(json.dumps({
        "schema_version": BACKLOG_SCHEMA_VERSION,
        "edition_key": "deva_keralam_volume_1_scan",
        "disposition": "timing_pending",
        "entries": [{
            "catalogue_ordinal": 10,
            "passage_key": "PASSAGE.10",
            "category": "age_year",
            "details": "A natal result is assigned to a stated age.",
            "required_capabilities": ["age-window fact"],
            "resolution": "implementable_now",
            "priority": "high",
        }],
    }))
    backlog = load_completion_backlog(path)
    rows = [
        CompletionLedgerRow(
            catalogue_ordinal=10,
            passage_key="PASSAGE.10",
            pdf_page=30,
            verse_start=10,
            verse_end=10,
            disposition="timing_pending",
            reason="Timing needs modelling.",
            source_check="catalogue",
        ),
        CompletionLedgerRow(
            catalogue_ordinal=11,
            passage_key="PASSAGE.11",
            pdf_page=30,
            verse_start=11,
            verse_end=11,
            disposition="unsupported_fact",
            reason="Missing fact.",
            source_check="catalogue",
        ),
    ]
    assert audit_backlog_against_ledger(backlog, rows) == ()
    assert audit_backlog_against_ledger(backlog, rows[:0]) == (
        "backlog contains 1 rows outside its ledger disposition",
    )
