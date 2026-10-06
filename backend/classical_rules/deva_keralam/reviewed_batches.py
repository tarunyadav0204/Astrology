"""Book-level audit utilities for reviewed Deva Keralam manifests.

This module deliberately has no import-time discovery and no registry side
effect.  A caller must provide the manifest paths it intends to inspect.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..models import ClassicalRule
from .reviewed_manifest import (
    ReviewedManifest,
    compile_reviewed_manifest,
    load_reviewed_manifest,
)


@dataclass(frozen=True)
class BatchAuditIssue:
    code: str
    message: str
    manifest_path: str
    candidate_key: str | None = None


@dataclass(frozen=True)
class ReviewedBookAudit:
    manifests: tuple[ReviewedManifest, ...]
    issues: tuple[BatchAuditIssue, ...]
    reviewed_candidates: int
    approved_candidates: int
    rejected_candidates: int
    compiled_rules: int

    @property
    def valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class ReviewedRulePack:
    """A validated, opt-in rule collection ready for the isolated matcher."""

    audit: ReviewedBookAudit
    rules: tuple[ClassicalRule, ...]
    included_existing_rule_count: int = 0


def _scope_page_bounds(manifest: ReviewedManifest) -> tuple[int, int] | None:
    raw = manifest.source_scope.get("pdf_pages")
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        return None
    start, end = raw
    if type(start) is not int or type(end) is not int or start < 1 or end < start:
        return None
    return start, end


def audit_reviewed_manifests(paths: Iterable[str | Path]) -> ReviewedBookAudit:
    """Load and cross-check a set of reviewed manifests.

    The per-record schema guarantees local shape.  This layer checks the
    properties that only become visible across batches: declared page scope,
    global key uniqueness, unique batch ids, and compiler/decision agreement.
    """

    manifests: list[ReviewedManifest] = []
    issues: list[BatchAuditIssue] = []
    seen_rule_keys: dict[str, str] = {}
    seen_batch_keys: dict[str, str] = {}
    reviewed = approved = rejected = compiled = 0

    for raw_path in paths:
        path = Path(raw_path)
        manifest = load_reviewed_manifest(path)
        path_label = str(path)
        manifests.append(manifest)

        prior_batch = seen_batch_keys.get(manifest.batch_key)
        if prior_batch:
            issues.append(BatchAuditIssue(
                "duplicate_batch_key",
                f"Batch key {manifest.batch_key!r} is already used by {prior_batch}.",
                path_label,
            ))
        else:
            seen_batch_keys[manifest.batch_key] = path_label

        bounds = _scope_page_bounds(manifest)
        if bounds is None:
            issues.append(BatchAuditIssue(
                "invalid_source_scope",
                "source_scope.pdf_pages must be an inclusive [start, end] pair.",
                path_label,
            ))

        results = {result.candidate_key: result for result in compile_reviewed_manifest(manifest)}
        for candidate in manifest.candidates:
            reviewed += 1
            approved += candidate.decision == "approved"
            rejected += candidate.decision == "rejected"
            result = results[candidate.key]
            compiled += result.compiled

            prior_path = seen_rule_keys.get(candidate.key)
            if prior_path:
                issues.append(BatchAuditIssue(
                    "duplicate_candidate_key",
                    f"Candidate key is already used by {prior_path}.",
                    path_label,
                    candidate.key,
                ))
            else:
                seen_rule_keys[candidate.key] = path_label

            if bounds and any(page < bounds[0] or page > bounds[1] for page in candidate.source.pdf_pages):
                issues.append(BatchAuditIssue(
                    "source_page_outside_batch_scope",
                    f"Source pages {candidate.source.pdf_pages!r} fall outside {bounds!r}.",
                    path_label,
                    candidate.key,
                ))

            if candidate.decision == "approved" and not result.compiled:
                codes = ", ".join(issue.code for issue in result.issues)
                issues.append(BatchAuditIssue(
                    "approved_candidate_did_not_compile",
                    f"Approved candidate failed the guarded compiler: {codes}.",
                    path_label,
                    candidate.key,
                ))
            if candidate.decision == "rejected" and result.compiled:
                issues.append(BatchAuditIssue(
                    "rejected_candidate_compiled",
                    "Rejected candidate unexpectedly passed the guarded compiler.",
                    path_label,
                    candidate.key,
                ))

    return ReviewedBookAudit(
        manifests=tuple(manifests),
        issues=tuple(issues),
        reviewed_candidates=reviewed,
        approved_candidates=approved,
        rejected_candidates=rejected,
        compiled_rules=compiled,
    )


def discover_reviewed_manifests(data_dir: str | Path) -> tuple[Path, ...]:
    """Return versioned review manifests without loading or publishing them."""

    return tuple(sorted(Path(data_dir).glob("reviewed_batch_*_v*.json")))


def load_reviewed_rule_pack(paths: Iterable[str | Path]) -> ReviewedRulePack:
    """Compile manifests only when the complete cross-batch audit succeeds."""

    normalized_paths = tuple(Path(path) for path in paths)
    audit = audit_reviewed_manifests(normalized_paths)
    if not audit.valid:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in audit.issues)
        raise ValueError(f"Reviewed Deva Keralam rule pack failed audit: {details}")
    rules = tuple(
        result.rule
        for manifest in audit.manifests
        for result in compile_reviewed_manifest(manifest)
        if result.rule is not None
    )
    return ReviewedRulePack(audit=audit, rules=rules)


def load_book_1_reviewed_rule_pack(paths: Iterable[str | Path]) -> ReviewedRulePack:
    """Join the reviewed manifests with the two earlier reviewed pilot slices.

    This remains opt in and performs no global registration.  It gives the
    chart matcher one coherent collection while keeping the older, already
    tested source slices intact.
    """

    from .abala_prabhaa_slice import RULES as ABALA_PRABHAA_RULES
    from .chapter_01 import RULES as CHAPTER_01_PILOT_RULES

    manifest_pack = load_reviewed_rule_pack(paths)
    existing = tuple((*ABALA_PRABHAA_RULES, *CHAPTER_01_PILOT_RULES))
    all_rules = tuple((*existing, *manifest_pack.rules))
    keys = [rule.key for rule in all_rules]
    if len(keys) != len(set(keys)):
        raise ValueError("Reviewed Deva Keralam Book 1 rules contain duplicate keys")
    return ReviewedRulePack(
        audit=manifest_pack.audit,
        rules=all_rules,
        included_existing_rule_count=len(existing),
    )
