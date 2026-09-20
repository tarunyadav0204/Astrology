"""Fail-closed loader for the compiled manifestation runtime bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping


DEFAULT_BUNDLE = (
    Path(__file__).resolve().parents[2]
    / "knowledge_graph"
    / "manifestation"
    / "manifestation-runtime.json"
)
EXPECTED_SCHEMA_VERSION = "manifestation-runtime/v1"


@dataclass(frozen=True)
class ManifestationPattern:
    stable_id: str
    manifestation_id: str
    domain: str
    parent_domain: str
    required_all: frozenset[int]
    required_any: frozenset[int]
    supporting: frozenset[int]
    outcome: frozenset[int]
    obstructing: frozenset[int]
    excluded: frozenset[int]
    minimum_any: int
    allowed_phases: frozenset[str]
    system_scope: str
    claim_basis: str
    review_status: str
    priority: int
    sensitive: bool
    source_ids: tuple[str, ...]
    masks: Mapping[str, int]
    timeline: Mapping[str, Any]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ManifestationPattern":
        return cls(
            stable_id=str(value["stable_id"]),
            manifestation_id=str(value["manifestation_id"]),
            domain=str(value["domain"]),
            parent_domain=str(value["parent_domain"]),
            required_all=frozenset(int(v) for v in value.get("required_all", ())),
            required_any=frozenset(int(v) for v in value.get("required_any", ())),
            supporting=frozenset(int(v) for v in value.get("supporting", ())),
            outcome=frozenset(int(v) for v in value.get("outcome", ())),
            obstructing=frozenset(int(v) for v in value.get("obstructing", ())),
            excluded=frozenset(int(v) for v in value.get("excluded", ())),
            minimum_any=int(value.get("minimum_any", 0)),
            allowed_phases=frozenset(str(v) for v in value.get("allowed_phases", ())),
            system_scope=str(value["system_scope"]),
            claim_basis=str(value["claim_basis"]),
            review_status=str(value["review_status"]),
            priority=int(value["priority"]),
            sensitive=bool(value.get("sensitive")),
            source_ids=tuple(str(v) for v in value.get("source_ids", ())),
            masks={str(k): int(v) for k, v in dict(value.get("masks", {})).items()},
            timeline=dict(value.get("timeline") or {}),
        )


@dataclass(frozen=True)
class DomainLens:
    domain: str
    stable_id: str
    label: str
    anchor: frozenset[int]
    pathway: frozenset[int]
    result: frozenset[int]
    pressure: frozenset[int]
    source_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, domain: str, value: Mapping[str, Any]) -> "DomainLens":
        return cls(
            domain=domain,
            stable_id=str(value["stable_id"]),
            label=str(value["label"]),
            anchor=frozenset(int(v) for v in value.get("anchor", ())),
            pathway=frozenset(int(v) for v in value.get("pathway", ())),
            result=frozenset(int(v) for v in value.get("result", ())),
            pressure=frozenset(int(v) for v in value.get("pressure", ())),
            source_ids=tuple(str(v) for v in value.get("source_ids", ())),
        )


class ManifestationKnowledgeStore:
    """Immutable compiled ontology store.

    Loading errors are intentionally propagated. A future client must decide
    how to represent unavailability; this package never substitutes legacy
    rules or an empty success response.
    """

    def __init__(self, bundle_path: Path | str = DEFAULT_BUNDLE) -> None:
        self.bundle_path = Path(bundle_path)
        document = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        schema_version = str(document.get("schema_version") or "")
        if schema_version != EXPECTED_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported manifestation bundle schema {schema_version!r}; "
                f"expected {EXPECTED_SCHEMA_VERSION!r}"
            )
        self.schema_version = schema_version
        self.ontology_version = str(document["ontology_version"])
        self.core_domain_version = str(document["core_domain_version"])
        self.manifestations: Mapping[str, Mapping[str, Any]] = {
            str(key): dict(value)
            for key, value in dict(document["manifestations"]).items()
        }
        self.sources: Mapping[str, Mapping[str, Any]] = {
            str(key): dict(value)
            for key, value in dict(document["sources"]).items()
        }
        self.patterns = tuple(
            ManifestationPattern.from_dict(value)
            for value in document["patterns"]
        )
        self.review_summary = {
            str(key): int(value)
            for key, value in dict(document.get("review_summary", {})).items()
        }
        self.house_meanings: Mapping[int, tuple[Mapping[str, Any], ...]] = {
            int(house): tuple(dict(value) for value in values)
            for house, values in dict(document["house_meanings"]).items()
        }
        self.domain_index: Mapping[str, str] = {
            str(key): str(value)
            for key, value in dict(document["domain_index"]).items()
        }
        self.domain_lenses: Mapping[str, DomainLens] = {
            str(domain): DomainLens.from_dict(str(domain), value)
            for domain, value in dict(document["domain_lenses"]).items()
        }
        semantic_coverage = dict(document.get("semantic_coverage", {}))
        if semantic_coverage.get("coverage_status") != "complete":
            raise ValueError("Manifestation bundle does not declare complete semantic coverage")
        if int(semantic_coverage.get("non_empty_house_combinations", 0)) != 4095:
            raise ValueError("Manifestation bundle does not cover all 4,095 house combinations")
        self.semantic_coverage = semantic_coverage

    def manifestation(self, stable_id: str) -> Mapping[str, Any]:
        try:
            return self.manifestations[stable_id]
        except KeyError as exc:
            raise KeyError(f"Unknown manifestation: {stable_id}") from exc


@lru_cache(maxsize=1)
def default_manifestation_store() -> ManifestationKnowledgeStore:
    return ManifestationKnowledgeStore()
