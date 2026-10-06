from collections import Counter
from pathlib import Path

from classical_rules.deva_keralam.completion_backlog import (
    audit_backlog_against_ledger,
    load_completion_backlog,
)
from classical_rules.deva_keralam.completion_ledger import load_completion_ledger


DATA_DIR = Path(__file__).parents[1] / "classical_rules" / "deva_keralam" / "data"


def test_ambiguous_context_backlog_covers_all_three_completion_ledgers():
    backlog = load_completion_backlog(DATA_DIR / "ambiguous_context_backlog_v1.json")
    ledger_rows = tuple(
        row
        for stream in "def"
        for row in load_completion_ledger(DATA_DIR / f"completion_ledger_{stream}_v1.json").rows
    )

    assert backlog.disposition == "ambiguous_context"
    assert len(backlog.entries) == 168
    assert audit_backlog_against_ledger(backlog, ledger_rows) == ()


def test_ambiguous_context_backlog_has_bounded_resolution_routes():
    backlog = load_completion_backlog(DATA_DIR / "ambiguous_context_backlog_v1.json")

    assert Counter(entry.resolution for entry in backlog.entries) == {
        "source_review": 90,
        "second_witness": 48,
        "excluded": 23,
        "implementable_now": 7,
    }
    assert Counter(entry.priority for entry in backlog.entries) == {
        "high": 30,
        "medium": 90,
        "low": 48,
    }
    assert all(
        "independent_source_witness" in entry.required_capabilities
        for entry in backlog.entries
        if entry.resolution == "second_witness"
    )
