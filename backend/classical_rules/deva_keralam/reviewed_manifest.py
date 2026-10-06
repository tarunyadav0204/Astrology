"""Strict, data-driven manifests for reviewed Deva Keralam rule batches.

The source review lives in versioned JSON. Loading a manifest never registers
or publishes its rules; it only converts reviewed records into the guarded
compiler contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contextual import PrecisionRequirement
from ..models import SourceProfile
from .review_compiler import CompilationResult, ReviewedRuleCandidate, compile_reviewed_batch


MANIFEST_SCHEMA_VERSION = "deva-keralam-reviewed-manifest/1.0.0"
EDITION_KEY = "deva_keralam_volume_1_scan"


class ManifestSource(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    verse_start: int = Field(gt=0)
    verse_end: int = Field(gt=0)
    pdf_pages: list[int] = Field(min_length=1)
    printed_pages: list[int] = Field(default_factory=list)
    reference_label: str = Field(min_length=1)
    editorial_status: Literal["reviewed_clear", "reviewed_interpreted"]
    numbering_note: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ranges(self) -> "ManifestSource":
        if self.verse_end < self.verse_start:
            raise ValueError("source verse range is inverted")
        if any(page < 1 for page in self.pdf_pages + self.printed_pages):
            raise ValueError("source pages must be positive")
        return self


class ManifestPrecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    key: str
    comparator: str
    value: Any
    unavailable_reason: str = Field(min_length=1)


class ManifestCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    passage_key: str = Field(min_length=1)
    context_block_key: str = Field(min_length=1)
    decision: Literal["approved", "rejected"]
    source: ManifestSource
    expression: dict[str, Any]
    outcome: dict[str, Any]
    precision_requirements: list[ManifestPrecision] = Field(default_factory=list)
    context_status: Literal["verified", "qualified", "candidate", "review", "rejected"]
    context_qualification_acknowledged: bool = False
    source_disputes: list[str] = Field(default_factory=list)
    inherited_ambiguities: list[str] = Field(default_factory=list)
    timing_kind: str = "none"
    operationalization_status: str = "approved"
    inherited_context: dict[str, Any] = Field(default_factory=dict)
    topics: list[str] = Field(default_factory=list)
    scope: str = "D1 source-bounded natal judgment"
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_review_decision(self) -> "ManifestCandidate":
        blockers = bool(
            self.source_disputes
            or self.inherited_ambiguities
            or self.timing_kind != "none"
            or self.operationalization_status != "approved"
            or self.context_status not in {"verified", "qualified"}
        )
        if self.decision == "approved" and blockers:
            raise ValueError("an approved candidate cannot retain a review blocker")
        if self.decision == "rejected" and not blockers:
            raise ValueError("a rejected candidate must retain a machine-readable blocker")
        if self.context_status == "qualified" and self.decision == "approved" and not self.context_qualification_acknowledged:
            raise ValueError("qualified approved context requires explicit acknowledgement")
        return self


class ReviewedManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[MANIFEST_SCHEMA_VERSION]
    batch_key: str = Field(min_length=1)
    edition_key: Literal[EDITION_KEY]
    source_scope: dict[str, Any]
    reviewer_method: str = Field(min_length=1)
    candidates: list[ManifestCandidate] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_candidates(self) -> "ReviewedManifest":
        keys = [candidate.key for candidate in self.candidates]
        if len(keys) != len(set(keys)):
            raise ValueError("candidate keys must be unique within a manifest")
        return self


def load_reviewed_manifest(path: str | Path) -> ReviewedManifest:
    return ReviewedManifest.model_validate_json(Path(path).read_text(encoding="utf-8"), strict=True)


def _source(batch_key: str, row: ManifestCandidate) -> SourceProfile:
    source = row.source
    return SourceProfile(
        key=f"{batch_key}:{row.key}",
        work="Deva Keralam (Chandra Kala Nadi)",
        chapter=1,
        chapter_title="Reviewed Deva Keralam source batch",
        verse_start=source.verse_start,
        verse_end=source.verse_end,
        witness_url=f"local-source://Deva-Keralam-1-Chandrakala-Nadi.pdf/pdf-page/{source.pdf_pages[0]}",
        witness_policy="private_source_reference",
        numbering_note=source.numbering_note,
        reference_label=source.reference_label,
        edition_key=EDITION_KEY,
        pdf_pages=tuple(source.pdf_pages),
        printed_pages=tuple(source.printed_pages),
        editorial_status=source.editorial_status,
    )


def candidates_from_manifest(manifest: ReviewedManifest) -> tuple[ReviewedRuleCandidate, ...]:
    rows = []
    for item in manifest.candidates:
        rejected = item.decision == "rejected"
        rows.append(ReviewedRuleCandidate(
            key=item.key,
            title=item.title,
            passage_key=item.passage_key,
            context_block_key=item.context_block_key,
            source=_source(manifest.batch_key, item),
            expression=item.expression,
            outcome=item.outcome,
            precision_requirements=tuple(
                PrecisionRequirement(row.key, row.comparator, row.value, row.unavailable_reason)
                for row in item.precision_requirements
            ),
            review_status="reviewed_approved",
            context_status=item.context_status,
            context_qualification_acknowledged=item.context_qualification_acknowledged,
            source_disputes=tuple(item.source_disputes),
            inherited_ambiguities=tuple(item.inherited_ambiguities),
            timing_kind=item.timing_kind,
            operationalization_status=("rejected" if rejected and item.operationalization_status == "approved" else item.operationalization_status),
            inherited_context=item.inherited_context,
            topics=tuple(item.topics),
            scope=item.scope,
            notes=tuple(item.notes),
        ))
    return tuple(rows)


def compile_reviewed_manifest(manifest: ReviewedManifest) -> tuple[CompilationResult, ...]:
    return compile_reviewed_batch(candidates_from_manifest(manifest))


def manifest_summary(manifest: ReviewedManifest) -> dict[str, Any]:
    results = compile_reviewed_manifest(manifest)
    return {
        "schema_version": manifest.schema_version,
        "batch_key": manifest.batch_key,
        "reviewed_candidates": len(results),
        "compiled_rules": sum(result.compiled for result in results),
        "rejected_candidates": sum(not result.compiled for result in results),
        "globally_registered": False,
    }

