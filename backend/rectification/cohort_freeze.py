"""Freeze an audited rectification cohort before any holdout scoring.

The manifest is private research metadata.  It binds the exact blinded case
file and separate truth vault to their SHA-256 hashes, split assignment, and
the engine/registry versions that will be evaluated.  A changed case, truth
file, or split requires a new freeze and makes the former holdout result
historical rather than untouched evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from .benchmark import load_blinded_cases, load_truth_vault
from .engine import RECTIFICATION_ENGINE_VERSION
from .registry import RECTIFICATION_REGISTRY_VERSION


COHORT_FREEZE_SCHEMA_VERSION = "rectification.cohort-freeze.v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _private_path(value: Path | str) -> Path:
    path = Path(value)
    if not path.name.endswith(".private.json"):
        raise ValueError("Frozen cohort manifests must end in .private.json")
    return path


def create_frozen_manifest(
    *,
    cases_path: Path | str,
    truth_path: Path | str,
    minimum_total: int = 25,
    minimum_holdout: int = 10,
) -> Dict[str, Any]:
    """Validate and freeze a cohort; never writes source chart data itself."""
    cases_file, truth_file = Path(cases_path), Path(truth_path)
    cases = load_blinded_cases(cases_file)
    truth = load_truth_vault(truth_file)
    if cases.dataset_id != truth.dataset_id or cases.cohort_status != truth.cohort_status:
        raise ValueError("Cases and truth vault must share dataset_id and cohort_status")
    if "audited" not in cases.cohort_status or "unaudited" in cases.cohort_status:
        raise ValueError("Only independently audited cohorts can be frozen for holdout scoring")
    counts = Counter(str(case["split"]) for case in cases)
    if len(cases) < minimum_total:
        raise ValueError(f"Cohort needs at least {minimum_total} cases; got {len(cases)}")
    if counts["holdout"] < minimum_holdout:
        raise ValueError(
            f"Cohort needs at least {minimum_holdout} preassigned holdout cases; "
            f"got {counts['holdout']}"
        )
    case_ids = {str(case["id"]) for case in cases}
    truth_ids = set(truth)
    if case_ids != truth_ids:
        raise ValueError("Frozen cohort cases and truth vault must contain exactly the same ids")
    return {
        "schema_version": COHORT_FREEZE_SCHEMA_VERSION,
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_id": cases.dataset_id,
        "cohort_status": cases.cohort_status,
        "case_sha256": _sha256(cases_file),
        "truth_vault_sha256": _sha256(truth_file),
        "case_ids_sha256": hashlib.sha256(
            "\n".join(sorted(case_ids)).encode("utf-8")
        ).hexdigest(),
        "split_counts": {"development": counts["development"], "holdout": counts["holdout"]},
        "minimums": {"total": minimum_total, "holdout": minimum_holdout},
        "engine_version": RECTIFICATION_ENGINE_VERSION,
        "registry_version": RECTIFICATION_REGISTRY_VERSION,
        "holdout_scored": False,
    }


def write_frozen_manifest(
    *, output_path: Path | str, **kwargs: Any
) -> Dict[str, Any]:
    output = _private_path(output_path)
    manifest = create_frozen_manifest(**kwargs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def validate_frozen_manifest(
    *, manifest_path: Path | str, cases_path: Path | str, truth_path: Path | str
) -> Mapping[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != COHORT_FREEZE_SCHEMA_VERSION:
        raise ValueError("Invalid frozen cohort manifest schema")
    cases, truth = Path(cases_path), Path(truth_path)
    if manifest.get("case_sha256") != _sha256(cases):
        raise ValueError("Frozen cohort manifest does not match the blinded cases file")
    if manifest.get("truth_vault_sha256") != _sha256(truth):
        raise ValueError("Frozen cohort manifest does not match the truth vault")
    if manifest.get("engine_version") != RECTIFICATION_ENGINE_VERSION:
        raise ValueError("Frozen cohort manifest was created for a different engine version")
    if manifest.get("registry_version") != RECTIFICATION_REGISTRY_VERSION:
        raise ValueError("Frozen cohort manifest was created for a different registry version")
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze an audited rectification cohort")
    parser.add_argument("--cases", required=True)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum-total", type=int, default=25)
    parser.add_argument("--minimum-holdout", type=int, default=10)
    args = parser.parse_args(argv)
    manifest = write_frozen_manifest(
        output_path=args.output,
        cases_path=args.cases,
        truth_path=args.truth,
        minimum_total=args.minimum_total,
        minimum_holdout=args.minimum_holdout,
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
