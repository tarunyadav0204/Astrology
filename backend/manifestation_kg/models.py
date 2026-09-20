"""Typed contracts for manifestation matching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


VALID_PHASES = frozenset({"background", "preparatory", "developing", "result_window"})
VALID_METHODS = frozenset({"parashari", "kp", "daily"})


def _houses(values: tuple[int, ...] | list[int] | set[int] | frozenset[int]) -> frozenset[int]:
    try:
        normalized = frozenset(int(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError("Houses must be integers from 1 to 12") from exc
    invalid = sorted(value for value in normalized if not 1 <= value <= 12)
    if invalid:
        raise ValueError(f"Invalid house numbers: {invalid}")
    return normalized


@dataclass(frozen=True)
class ActivationPacket:
    """System-owned activation evidence supplied to the shared resolver.

    This contract records what a calculator has already established. The
    manifestation resolver never calculates dashas, transits, cusps or timing.
    """

    active_houses: frozenset[int]
    method: str
    domain: str | None = None
    phase: str | None = None
    calculator_version: str | None = None
    evidence: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "active_houses", _houses(self.active_houses))
        method = str(self.method or "").strip().lower()
        if method not in VALID_METHODS:
            raise ValueError(f"Unknown activation method: {self.method!r}")
        object.__setattr__(self, "method", method)
        if self.phase is not None:
            phase = str(self.phase).strip().lower()
            if phase not in VALID_PHASES:
                raise ValueError(f"Unknown manifestation phase: {self.phase!r}")
            object.__setattr__(self, "phase", phase)
        if self.domain is not None:
            object.__setattr__(self, "domain", str(self.domain).strip().lower())


@dataclass(frozen=True)
class ManifestationMatch:
    manifestation_id: str
    pattern_id: str
    label: str
    label_key: str
    prompt_key: str
    domain: str
    parent_domain: str
    phase: str | None
    method: str
    rank_score: int
    required_houses: tuple[int, ...]
    matched_supporting_houses: tuple[int, ...]
    matched_outcome_houses: tuple[int, ...]
    matched_obstructing_houses: tuple[int, ...]
    claim_basis: str
    review_status: str
    sensitive: bool
    source_ids: tuple[str, ...]
    ontology_version: str
    calculator_version: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifestation_id": self.manifestation_id,
            "pattern_id": self.pattern_id,
            "label": self.label,
            "label_key": self.label_key,
            "prompt_key": self.prompt_key,
            "domain": self.domain,
            "parent_domain": self.parent_domain,
            "phase": self.phase,
            "method": self.method,
            "rank_score": self.rank_score,
            "required_houses": list(self.required_houses),
            "matched_supporting_houses": list(self.matched_supporting_houses),
            "matched_outcome_houses": list(self.matched_outcome_houses),
            "matched_obstructing_houses": list(self.matched_obstructing_houses),
            "claim_basis": self.claim_basis,
            "review_status": self.review_status,
            "sensitive": self.sensitive,
            "source_ids": list(self.source_ids),
            "ontology_version": self.ontology_version,
            "calculator_version": self.calculator_version,
        }


@dataclass(frozen=True)
class HouseSemanticMeaning:
    house: int
    meaning_id: str
    label: str
    label_key: str
    domains: tuple[str, ...]
    parent_domains: tuple[str, ...]
    source_ids: tuple[str, ...]
    relevant_to_requested_domain: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "house": self.house,
            "meaning_id": self.meaning_id,
            "label": self.label,
            "label_key": self.label_key,
            "domains": list(self.domains),
            "parent_domains": list(self.parent_domains),
            "source_ids": list(self.source_ids),
            "relevant_to_requested_domain": self.relevant_to_requested_domain,
        }


@dataclass(frozen=True)
class DomainLensMatch:
    domain: str
    label: str
    relevance_score: int
    matched_anchor_houses: tuple[int, ...]
    matched_pathway_houses: tuple[int, ...]
    matched_result_houses: tuple[int, ...]
    matched_pressure_houses: tuple[int, ...]
    source_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "label": self.label,
            "relevance_score": self.relevance_score,
            "matched_anchor_houses": list(self.matched_anchor_houses),
            "matched_pathway_houses": list(self.matched_pathway_houses),
            "matched_result_houses": list(self.matched_result_houses),
            "matched_pressure_houses": list(self.matched_pressure_houses),
            "source_ids": list(self.source_ids),
        }


@dataclass(frozen=True)
class CombinationInterpretation:
    active_houses: tuple[int, ...]
    method: str
    requested_domain: str | None
    phase: str | None
    coverage_status: str
    ambiguity_preserved: bool
    house_meanings: tuple[HouseSemanticMeaning, ...]
    domain_candidates: tuple[DomainLensMatch, ...]
    manifestation_matches: tuple[ManifestationMatch, ...]
    ontology_version: str
    calculator_version: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "manifestation-interpretation/v1",
            "status": "resolved",
            "coverage_status": self.coverage_status,
            "ambiguity_preserved": self.ambiguity_preserved,
            "active_houses": list(self.active_houses),
            "method": self.method,
            "requested_domain": self.requested_domain,
            "phase": self.phase,
            "house_meanings": [value.as_dict() for value in self.house_meanings],
            "domain_candidates": [value.as_dict() for value in self.domain_candidates],
            "manifestation_matches": [value.as_dict() for value in self.manifestation_matches],
            "ontology_version": self.ontology_version,
            "calculator_version": self.calculator_version,
            "claim_boundary": (
                "Domain relevance and semantic coverage are not event probability. "
                "Only manifestation_matches contain curated event candidates."
            ),
        }
