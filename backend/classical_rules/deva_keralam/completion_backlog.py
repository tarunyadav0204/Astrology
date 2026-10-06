"""Validated taxonomies for unresolved Deva Keralam completion rows."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .completion_ledger import CompletionLedgerRow, Disposition


BACKLOG_SCHEMA_VERSION = "deva-keralam-completion-backlog/1.0.0"
EDITION_KEY = "deva_keralam_volume_1_scan"


class CompletionBacklogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    catalogue_ordinal: int = Field(ge=1, le=878)
    passage_key: str = Field(min_length=1)
    category: str = Field(min_length=1)
    details: str = Field(min_length=1)
    required_capabilities: list[str] = Field(default_factory=list)
    resolution: Literal["implementable_now", "source_review", "second_witness", "excluded"]
    priority: Literal["high", "medium", "low"]


class CompletionBacklog(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[BACKLOG_SCHEMA_VERSION]
    edition_key: Literal[EDITION_KEY]
    disposition: Disposition
    entries: list[CompletionBacklogEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_source_rows(self) -> "CompletionBacklog":
        ordinals = [entry.catalogue_ordinal for entry in self.entries]
        keys = [entry.passage_key for entry in self.entries]
        if len(ordinals) != len(set(ordinals)) or len(keys) != len(set(keys)):
            raise ValueError("backlog entries must identify unique catalogue passages")
        return self


def load_completion_backlog(path: str | Path) -> CompletionBacklog:
    return CompletionBacklog.model_validate_json(Path(path).read_text(encoding="utf-8"), strict=True)


def audit_backlog_against_ledger(
    backlog: CompletionBacklog,
    ledger_rows: list[CompletionLedgerRow] | tuple[CompletionLedgerRow, ...],
) -> tuple[str, ...]:
    expected = {
        (row.catalogue_ordinal, row.passage_key)
        for row in ledger_rows
        if row.disposition == backlog.disposition
    }
    actual = {(entry.catalogue_ordinal, entry.passage_key) for entry in backlog.entries}
    issues: list[str] = []
    if missing := sorted(expected - actual):
        issues.append(f"backlog is missing {len(missing)} ledger rows")
    if extra := sorted(actual - expected):
        issues.append(f"backlog contains {len(extra)} rows outside its ledger disposition")
    return tuple(issues)
