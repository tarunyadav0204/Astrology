"""Stable contracts for the classical corpus and deterministic rule engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple


RuleEvaluator = Callable[[Mapping[str, Any], Optional[Mapping[str, Any]]], Dict[str, Any]]


class RuleInputUnavailable(ValueError):
    """Expected chart/birth input is absent; this is not a calculator failure."""


@dataclass(frozen=True)
class SourceProfile:
    key: str
    work: str
    chapter: int
    chapter_title: str
    verse_start: int
    verse_end: int
    witness_url: str
    witness_policy: str = "external_reference_only"
    numbering_note: str = "Verse numbering follows the pinned witness."
    reference_label: Optional[str] = None
    edition_key: Optional[str] = None
    pdf_pages: Tuple[int, ...] = ()
    printed_pages: Tuple[int, ...] = ()
    editorial_status: Optional[str] = None

    @property
    def reference(self) -> str:
        if self.reference_label:
            return self.reference_label
        suffix = str(self.verse_start) if self.verse_start == self.verse_end else f"{self.verse_start}–{self.verse_end}"
        return f"BPHS {self.chapter}.{suffix}"


@dataclass(frozen=True)
class PassageGroup:
    key: str
    verse_start: int
    verse_end: int
    title: str
    classification: str
    operational_summary: str
    executable: bool
    review_status: str
    rule_keys: Tuple[str, ...] = ()

    def verses(self) -> Iterable[int]:
        return range(self.verse_start, self.verse_end + 1)


@dataclass(frozen=True)
class ClassicalRule:
    key: str
    title: str
    source: SourceProfile
    rule_type: str
    scope: str
    status: str
    calculator_binding: str
    evaluator: RuleEvaluator
    topics: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def public_definition(self) -> Dict[str, Any]:
        row = asdict(self)
        row.pop("evaluator", None)
        row["source"]["reference"] = self.source.reference
        for key in ("reference_label", "edition_key", "editorial_status"):
            if row["source"].get(key) is None:
                row["source"].pop(key, None)
        for key in ("pdf_pages", "printed_pages"):
            if not row["source"].get(key):
                row["source"].pop(key, None)
        return row


@dataclass
class RuleResult:
    rule_key: str
    title: str
    source: Dict[str, Any]
    status: str
    applicability: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    reason: Optional[str] = None
    calculator_binding: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
