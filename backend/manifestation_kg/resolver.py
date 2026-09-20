"""Deterministic activation-pattern resolver for the manifestation KG."""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    ActivationPacket,
    CombinationInterpretation,
    DomainLensMatch,
    HouseSemanticMeaning,
    ManifestationMatch,
)
from .store import ManifestationKnowledgeStore, ManifestationPattern, default_manifestation_store


class ManifestationResolver:
    def __init__(self, store: ManifestationKnowledgeStore | None = None) -> None:
        self.store = store or default_manifestation_store()

    @staticmethod
    def _domain_matches(pattern: ManifestationPattern, requested: str | None) -> bool:
        if not requested:
            return True
        normalized = requested.removeprefix("domain.")
        return normalized in {pattern.domain, pattern.parent_domain.removeprefix("domain.")}

    @staticmethod
    def _method_matches(pattern: ManifestationPattern, method: str) -> bool:
        return pattern.system_scope == "shared_semantics" or pattern.system_scope == method

    @staticmethod
    def _matches(pattern: ManifestationPattern, packet: ActivationPacket) -> bool:
        active = packet.active_houses
        if not pattern.required_all.issubset(active):
            return False
        if len(pattern.required_any & active) < pattern.minimum_any:
            return False
        if pattern.excluded & active:
            return False
        if packet.phase and packet.phase not in pattern.allowed_phases:
            return False
        return True

    @staticmethod
    def _score(pattern: ManifestationPattern, active: frozenset[int]) -> int:
        return (
            pattern.priority
            + 10 * len(pattern.required_all)
            + 6 * len(pattern.required_any & active)
            + 3 * len(pattern.supporting & active)
            + 4 * len(pattern.outcome & active)
            - 5 * len(pattern.obstructing & active)
        )

    def resolve(
        self,
        packet: ActivationPacket,
        *,
        allowed_review_statuses: Iterable[str] = ("approved",),
        include_sensitive: bool = False,
        limit: int | None = None,
    ) -> list[ManifestationMatch]:
        """Return ranked candidates without converting rank into probability.

        Provisional knowledge is excluded by default. During development and
        review it must be enabled explicitly with
        ``allowed_review_statuses=("provisional",)``.
        """
        allowed = frozenset(str(value) for value in allowed_review_statuses)
        if not allowed:
            return []
        best_by_manifestation: dict[str, ManifestationMatch] = {}
        for pattern in self.store.patterns:
            if pattern.review_status not in allowed:
                continue
            if pattern.sensitive and not include_sensitive:
                continue
            if not self._domain_matches(pattern, packet.domain):
                continue
            if not self._method_matches(pattern, packet.method):
                continue
            if not self._matches(pattern, packet):
                continue
            manifestation = self.store.manifestation(pattern.manifestation_id)
            required = tuple(sorted(pattern.required_all | (pattern.required_any & packet.active_houses)))
            candidate = ManifestationMatch(
                manifestation_id=pattern.manifestation_id,
                pattern_id=pattern.stable_id,
                label=str(manifestation["label"]),
                label_key=str(manifestation["label_key"]),
                prompt_key=str(manifestation["prompt_key"]),
                domain=pattern.domain,
                parent_domain=pattern.parent_domain,
                phase=packet.phase,
                method=packet.method,
                rank_score=self._score(pattern, packet.active_houses),
                required_houses=required,
                matched_supporting_houses=tuple(sorted(pattern.supporting & packet.active_houses)),
                matched_outcome_houses=tuple(sorted(pattern.outcome & packet.active_houses)),
                matched_obstructing_houses=tuple(sorted(pattern.obstructing & packet.active_houses)),
                claim_basis=pattern.claim_basis,
                review_status=pattern.review_status,
                sensitive=pattern.sensitive,
                source_ids=pattern.source_ids,
                ontology_version=self.store.ontology_version,
                calculator_version=packet.calculator_version,
            )
            current = best_by_manifestation.get(candidate.manifestation_id)
            if current is None or (candidate.rank_score, candidate.pattern_id) > (
                current.rank_score,
                current.pattern_id,
            ):
                best_by_manifestation[candidate.manifestation_id] = candidate
        ranked = sorted(
            best_by_manifestation.values(),
            key=lambda item: (-item.rank_score, item.manifestation_id, item.pattern_id),
        )
        return ranked if limit is None else ranked[: max(0, int(limit))]

    def _requested_parent_domain(self, requested: str | None) -> str | None:
        if not requested:
            return None
        normalized = requested.removeprefix("domain.")
        direct = f"domain.{normalized}"
        if direct in self.store.domain_lenses:
            return direct
        return self.store.domain_index.get(normalized)

    def interpret(
        self,
        packet: ActivationPacket,
        *,
        allowed_review_statuses: Iterable[str] = ("approved",),
        include_sensitive: bool = False,
        manifestation_limit: int | None = None,
        domain_limit: int | None = None,
    ) -> CombinationInterpretation:
        """Interpret every active house while preserving unresolved meanings.

        This semantic layer has exhaustive combinatorial coverage. It never
        upgrades a domain relevance score into an event prediction.
        """
        requested_parent = self._requested_parent_domain(packet.domain)
        meanings: list[HouseSemanticMeaning] = []
        for house in sorted(packet.active_houses):
            for value in self.store.house_meanings[house]:
                parent_domains = tuple(str(item) for item in value["parent_domains"])
                relevant = requested_parent is None or requested_parent in parent_domains
                meanings.append(HouseSemanticMeaning(
                    house=house,
                    meaning_id=str(value["stable_id"]),
                    label=str(value["label"]),
                    label_key=str(value["label_key"]),
                    domains=tuple(str(item) for item in value["domains"]),
                    parent_domains=parent_domains,
                    source_ids=tuple(str(item) for item in value["source_ids"]),
                    relevant_to_requested_domain=relevant,
                ))

        domain_candidates: list[DomainLensMatch] = []
        for domain, lens in self.store.domain_lenses.items():
            if requested_parent is not None and domain != requested_parent:
                continue
            anchor = tuple(sorted(lens.anchor & packet.active_houses))
            pathway = tuple(sorted(lens.pathway & packet.active_houses))
            result = tuple(sorted(lens.result & packet.active_houses))
            pressure = tuple(sorted(lens.pressure & packet.active_houses))
            # Pressure can qualify an already relevant domain, but pressure by
            # itself cannot select a life domain.
            if not (anchor or pathway or result):
                continue
            # Relevance only: pressure raises domain relevance because it is
            # still evidence about that domain; it does not make it favorable.
            score = 5 * len(anchor) + 3 * len(result) + 2 * len(pathway) + len(pressure)
            domain_candidates.append(DomainLensMatch(
                domain=domain,
                label=lens.label,
                relevance_score=score,
                matched_anchor_houses=anchor,
                matched_pathway_houses=pathway,
                matched_result_houses=result,
                matched_pressure_houses=pressure,
                source_ids=lens.source_ids,
            ))
        domain_candidates.sort(key=lambda value: (-value.relevance_score, value.domain))
        if domain_limit is not None:
            domain_candidates = domain_candidates[: max(0, int(domain_limit))]

        manifestations = self.resolve(
            packet,
            allowed_review_statuses=allowed_review_statuses,
            include_sensitive=include_sensitive,
            limit=manifestation_limit,
        )
        return CombinationInterpretation(
            active_houses=tuple(sorted(packet.active_houses)),
            method=packet.method,
            requested_domain=packet.domain,
            phase=packet.phase,
            coverage_status="specific_and_semantic" if manifestations else "semantic_only",
            ambiguity_preserved=packet.domain is None,
            house_meanings=tuple(meanings),
            domain_candidates=tuple(domain_candidates),
            manifestation_matches=tuple(manifestations),
            ontology_version=self.store.ontology_version,
            calculator_version=packet.calculator_version,
        )
