#!/usr/bin/env python3
"""Audit reviewed Deva Keralam manifests without registering their rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from classical_rules.deva_keralam.reviewed_batches import (
    audit_reviewed_manifests,
    discover_reviewed_manifests,
    load_book_1_reviewed_rule_pack,
)
from classical_rules.deva_keralam.abala_prabhaa_slice import (
    APPROVED_CANDIDATES,
    REJECTED_CANDIDATES,
)
from classical_rules.deva_keralam.chapter_01 import RULES as PILOT_RULES
from classical_rules.deva_keralam.completion_backlog import (
    audit_backlog_against_ledger,
    load_completion_backlog,
)
from classical_rules.deva_keralam.completion_ledger import (
    audit_completion_ledgers,
    load_completion_ledger,
)
from classical_rules.deva_keralam.reviewed_manifest import load_reviewed_manifest


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "classical_rules" / "deva_keralam" / "data"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    paths = discover_reviewed_manifests(args.data_dir)
    if not paths:
        print(json.dumps({
            "valid": False,
            "error": "no_reviewed_manifests_found",
            "data_dir": str(args.data_dir),
        }, indent=2))
        return 1

    audit = audit_reviewed_manifests(paths)
    book_pack = load_book_1_reviewed_rule_pack(paths) if audit.valid else None
    ledger_paths = tuple(sorted(args.data_dir.glob("completion_ledger_*_v*.json")))
    known_keys = {
        candidate.key for candidate in (*APPROVED_CANDIDATES, *REJECTED_CANDIDATES)
    } | {rule.key for rule in PILOT_RULES}
    for path in paths:
        known_keys.update(candidate.key for candidate in load_reviewed_manifest(path).candidates)
    ledger_audit = audit_completion_ledgers(ledger_paths, known_candidate_keys=known_keys)
    ledger_rows = [
        row
        for path in ledger_paths
        for row in load_completion_ledger(path).rows
    ]
    backlog_audits = {}
    for path in sorted(args.data_dir.glob("*_backlog_v*.json")):
        backlog = load_completion_backlog(path)
        backlog_audits[path.name] = {
            "disposition": backlog.disposition,
            "entries": len(backlog.entries),
            "issues": list(audit_backlog_against_ledger(backlog, ledger_rows)),
        }
    complete_valid = audit.valid and ledger_audit.valid and all(
        not row["issues"] for row in backlog_audits.values()
    )
    print(json.dumps({
        "valid": complete_valid,
        "globally_registered": False,
        "manifest_paths": [str(path) for path in paths],
        "manifest_count": len(audit.manifests),
        "reviewed_candidates": audit.reviewed_candidates,
        "approved_candidates": audit.approved_candidates,
        "rejected_candidates": audit.rejected_candidates,
        "compiled_rules": audit.compiled_rules,
        "existing_reviewed_rules": book_pack.included_existing_rule_count if book_pack else None,
        "total_executable_book_1_rules": len(book_pack.rules) if book_pack else None,
        "issues": [issue.__dict__ for issue in audit.issues],
        "completion_ledger": {
            "rows": ledger_audit.rows,
            "disposition_counts": ledger_audit.disposition_counts,
            "issues": list(ledger_audit.issues),
        },
        "backlogs": backlog_audits,
    }, indent=2))
    return 0 if complete_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
