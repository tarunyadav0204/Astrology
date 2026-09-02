"""Apply an independent-source audit to a private public-chart seed cohort.

The Astro-Databank research event rows are discovery leads, not benchmark
ground truth.  This module keeps the audit separate from both the blinded cases
and the birth-time truth vault, and promotes only events whose date *and event
meaning* are supported by an independently reviewed public source.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

from .benchmark import BLINDED_DATASET_SCHEMA_VERSION, TRUTH_VAULT_SCHEMA_VERSION


EVENT_AUDIT_SCHEMA_VERSION = "rectification.event-source-audit.v1"
AUDITED_COHORT_STATUS = "development_event_sources_audited"
VERIFIED_STATUSES = {"verified_exact", "verified_precision"}
EXCLUDED_STATUSES = {"semantic_mismatch", "contradicted", "unsupported"}
AUDIT_STATUSES = VERIFIED_STATUSES | EXCLUDED_STATUSES
PRECISIONS = {"exact_day", "month", "year"}


def _private_path(path: Path | str) -> Path:
    resolved = Path(path)
    if not resolved.name.endswith(".private.json"):
        raise ValueError("Public-chart audit inputs and outputs must end in .private.json")
    return resolved


def _valid_source_url(value: str) -> bool:
    parsed = urlparse(str(value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_iso_date(value: str) -> str:
    parsed = date.fromisoformat(str(value or ""))
    return parsed.isoformat()


def _audit_index(payload: Mapping[str, Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    if payload.get("schema_version") != EVENT_AUDIT_SCHEMA_VERSION:
        raise ValueError(f"Expected {EVENT_AUDIT_SCHEMA_VERSION} event audit")
    rows = payload.get("events")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Event audit must contain a non-empty events list")
    indexed: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in rows:
        case_id = str(row.get("case_id") or "").strip()
        event_id = str(row.get("event_id") or "").strip()
        key = (case_id, event_id)
        if not all(key) or key in indexed:
            raise ValueError(f"Audit rows require a unique case_id/event_id pair: {key!r}")
        status = str(row.get("status") or "").strip()
        if status not in AUDIT_STATUSES:
            raise ValueError(f"{case_id}/{event_id}: unsupported audit status {status!r}")
        sources = row.get("sources") or []
        if status in VERIFIED_STATUSES:
            if not sources:
                raise ValueError(f"{case_id}/{event_id}: verified audit needs a source")
            for source in sources:
                if not _valid_source_url(source.get("url")):
                    raise ValueError(f"{case_id}/{event_id}: source needs an http(s) URL")
                if not str(source.get("publisher") or "").strip():
                    raise ValueError(f"{case_id}/{event_id}: source publisher is required")
            audited_type = str(row.get("audited_event_type") or "").strip()
            audited_date = _validate_iso_date(row.get("audited_date_start"))
            precision = str(row.get("audited_precision") or "").strip()
            if not audited_type or precision not in PRECISIONS:
                raise ValueError(
                    f"{case_id}/{event_id}: verified audit needs type, date and precision"
                )
            if status == "verified_exact" and precision != "exact_day":
                raise ValueError(
                    f"{case_id}/{event_id}: verified_exact requires exact_day precision"
                )
            row = {**row, "audited_date_start": audited_date}
        indexed[key] = dict(row)
    return indexed


def apply_event_audit(
    *,
    blinded_payload: Mapping[str, Any],
    truth_payload: Mapping[str, Any],
    audit_payload: Mapping[str, Any],
    minimum_events: int = 4,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Return an audited development cohort and a machine-readable audit report."""
    if blinded_payload.get("schema_version") != BLINDED_DATASET_SCHEMA_VERSION:
        raise ValueError("Invalid blinded dataset schema")
    if truth_payload.get("schema_version") != TRUTH_VAULT_SCHEMA_VERSION:
        raise ValueError("Invalid truth vault schema")
    dataset_id = str(blinded_payload.get("dataset_id") or "")
    if not dataset_id or dataset_id != str(truth_payload.get("dataset_id") or ""):
        raise ValueError("Blinded cases and truth vault must share a dataset_id")
    audit_dataset_id = str(audit_payload.get("dataset_id") or "")
    if audit_dataset_id != dataset_id:
        raise ValueError("Event audit dataset_id does not match the seed cohort")
    if minimum_events < 4:
        raise ValueError("Audited rectification cases require at least four events")

    indexed = _audit_index(audit_payload)
    truth_by_id = {
        str(row.get("id")): deepcopy(row) for row in truth_payload.get("truth") or []
    }
    retained_cases = []
    retained_truth = []
    case_reports = []
    consumed = set()
    for original_case in blinded_payload.get("cases") or []:
        case = deepcopy(original_case)
        case_id = str(case.get("id") or "")
        verified_events = []
        event_reports = []
        for original_event in case.get("events") or []:
            event_id = str(original_event.get("id") or "")
            key = (case_id, event_id)
            audit = indexed.get(key)
            if audit is None:
                event_reports.append({"event_id": event_id, "status": "not_audited"})
                continue
            consumed.add(key)
            status = audit["status"]
            event_reports.append({"event_id": event_id, "status": status})
            if status not in VERIFIED_STATUSES:
                continue
            event = deepcopy(original_event)
            event["event_type"] = audit["audited_event_type"]
            event["date_start"] = audit["audited_date_start"]
            event["precision"] = audit["audited_precision"]
            event["source_reliability"] = "documented"
            # Keep identifying citations in the separate audit overlay. The
            # scorer needs only the adjudicated status, not a person's URL.
            event["source_audit"] = {
                "status": status,
            }
            verified_events.append(event)
        retained = len(verified_events) >= minimum_events and case_id in truth_by_id
        case_reports.append({
            "case_id": case_id,
            "retained": retained,
            "verified_event_count": len(verified_events),
            "events": event_reports,
        })
        if retained:
            case["events"] = verified_events
            case["event_source_audit"] = "independently_audited_date_and_semantics"
            retained_cases.append(case)
            retained_truth.append(truth_by_id[case_id])

    unknown = sorted(set(indexed).difference(consumed))
    if unknown:
        formatted = ", ".join(f"{case}/{event}" for case, event in unknown)
        raise ValueError(f"Audit refers to unknown case/event rows: {formatted}")
    if not retained_cases:
        raise ValueError(
            f"No case retained at least {minimum_events} independently verified events"
        )

    audited_dataset_id = str(audit_payload.get("audited_dataset_id") or f"{dataset_id}-audited-v1")
    audited_status = (
        "preassigned_development_holdout_event_sources_audited"
        if any(case.get("split") == "holdout" for case in retained_cases)
        else AUDITED_COHORT_STATUS
    )
    blinded = deepcopy(dict(blinded_payload))
    blinded.update({
        "dataset_id": audited_dataset_id,
        "cohort_status": audited_status,
        "cases": retained_cases,
        "source_dataset_id": dataset_id,
        "event_audit_schema_version": EVENT_AUDIT_SCHEMA_VERSION,
    })
    truth = deepcopy(dict(truth_payload))
    truth.update({
        "dataset_id": audited_dataset_id,
        "cohort_status": audited_status,
        "truth": retained_truth,
        "source_dataset_id": dataset_id,
    })
    report = {
        "schema_version": EVENT_AUDIT_SCHEMA_VERSION,
        "source_dataset_id": dataset_id,
        "audited_dataset_id": audited_dataset_id,
        "minimum_events": minimum_events,
        "input_cases": len(blinded_payload.get("cases") or []),
        "retained_cases": len(retained_cases),
        "excluded_cases": len(blinded_payload.get("cases") or []) - len(retained_cases),
        "cases": case_reports,
    }
    return blinded, truth, report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Apply independent event audits to a private cohort")
    parser.add_argument("--cases", required=True)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--blinded-output", required=True)
    parser.add_argument("--truth-output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--minimum-events", type=int, default=4)
    args = parser.parse_args(argv)
    paths = [_private_path(value) for value in (
        args.cases, args.truth, args.audit, args.blinded_output,
        args.truth_output, args.report_output,
    )]
    source_cases, source_truth, audit_path, output_cases, output_truth, output_report = paths
    blinded, truth, report = apply_event_audit(
        blinded_payload=json.loads(source_cases.read_text(encoding="utf-8")),
        truth_payload=json.loads(source_truth.read_text(encoding="utf-8")),
        audit_payload=json.loads(audit_path.read_text(encoding="utf-8")),
        minimum_events=args.minimum_events,
    )
    for path in (output_cases, output_truth, output_report):
        path.parent.mkdir(parents=True, exist_ok=True)
    output_cases.write_text(json.dumps(blinded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_truth.write_text(json.dumps(truth, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "audited_dataset_id": report["audited_dataset_id"],
        "retained_cases": report["retained_cases"],
        "excluded_cases": report["excluded_cases"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
