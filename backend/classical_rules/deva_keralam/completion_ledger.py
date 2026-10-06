"""Strict full-book disposition ledger for Deva Keralam Book 1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LEDGER_SCHEMA_VERSION = "deva-keralam-completion-ledger/1.0.0"
EDITION_KEY = "deva_keralam_volume_1_scan"
BOOK_1_CATALOGUE_COUNT = 878

Disposition = Literal[
    "executable",
    "duplicate",
    "commentary_only",
    "timing_pending",
    "unsupported_fact",
    "ambiguous_context",
    "corrupt_or_disputed",
    "impossible_geometry",
    "mortality_excluded",
    "already_reviewed",
]


class CompletionLedgerRow(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    catalogue_ordinal: int = Field(ge=1, le=BOOK_1_CATALOGUE_COUNT)
    passage_key: str = Field(min_length=1)
    pdf_page: int = Field(ge=1, le=260)
    verse_start: int = Field(gt=0)
    verse_end: int = Field(gt=0)
    disposition: Disposition
    candidate_keys: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    source_check: Literal["catalogue", "ocr_context", "page_image_context"]

    @model_validator(mode="after")
    def validate_disposition(self) -> "CompletionLedgerRow":
        if self.verse_end < self.verse_start:
            raise ValueError("verse range is inverted")
        if self.disposition in {"executable", "already_reviewed"} and not self.candidate_keys:
            raise ValueError(f"{self.disposition} requires at least one candidate/rule key")
        if self.disposition == "executable" and self.source_check != "page_image_context":
            raise ValueError("new executable rules require page-image context review")
        return self


class CompletionLedger(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[LEDGER_SCHEMA_VERSION]
    edition_key: Literal[EDITION_KEY]
    stream_key: str = Field(min_length=1)
    catalog_ordinal_start: int = Field(ge=1, le=BOOK_1_CATALOGUE_COUNT)
    catalog_ordinal_end: int = Field(ge=1, le=BOOK_1_CATALOGUE_COUNT)
    source_snapshot_count: Literal[BOOK_1_CATALOGUE_COUNT]
    rows: list[CompletionLedgerRow] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_complete_stream(self) -> "CompletionLedger":
        if self.catalog_ordinal_end < self.catalog_ordinal_start:
            raise ValueError("ledger range is inverted")
        expected = list(range(self.catalog_ordinal_start, self.catalog_ordinal_end + 1))
        actual = [row.catalogue_ordinal for row in self.rows]
        if actual != expected:
            raise ValueError("ledger rows must cover their declared ordinal range exactly and in order")
        keys = [row.passage_key for row in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError("passage keys must be unique within a ledger")
        return self


@dataclass(frozen=True)
class CompletionAudit:
    valid: bool
    rows: int
    disposition_counts: dict[str, int]
    issues: tuple[str, ...]


def load_completion_ledger(path: str | Path) -> CompletionLedger:
    return CompletionLedger.model_validate_json(Path(path).read_text(encoding="utf-8"), strict=True)


def audit_completion_ledgers(
    paths: list[str | Path] | tuple[str | Path, ...],
    *,
    known_candidate_keys: set[str] | None = None,
) -> CompletionAudit:
    ledgers = [load_completion_ledger(path) for path in paths]
    issues: list[str] = []
    all_rows = [row for ledger in ledgers for row in ledger.rows]
    ordinals = [row.catalogue_ordinal for row in all_rows]
    passage_keys = [row.passage_key for row in all_rows]
    if sorted(ordinals) != list(range(1, BOOK_1_CATALOGUE_COUNT + 1)):
        issues.append("combined ledgers do not cover catalogue ordinals 1..878 exactly once")
    if len(passage_keys) != len(set(passage_keys)):
        issues.append("combined ledgers contain duplicate passage keys")
    if known_candidate_keys is not None:
        missing_links = sorted({
            key
            for row in all_rows
            if row.disposition in {"executable", "already_reviewed"}
            for key in row.candidate_keys
            if key not in known_candidate_keys
        })
        if missing_links:
            issues.append(
                "ledger executable/already-reviewed rows reference unknown candidate keys: "
                + ", ".join(missing_links)
            )
    counts: dict[str, int] = {}
    for row in all_rows:
        counts[row.disposition] = counts.get(row.disposition, 0) + 1
    return CompletionAudit(not issues, len(all_rows), counts, tuple(issues))
