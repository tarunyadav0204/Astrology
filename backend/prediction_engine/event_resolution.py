from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .context import CalculationContext
from .contracts import (
    DivisionalConfirmation,
    EventResolution,
    Evidence,
    LifeContext,
    PredictionCandidate,
    ResolutionSpecificity,
    ResolutionStatus,
)
from .event_signatures import EventSignature, signatures_for_family
from .primitives import aspected_houses, ruled_houses
from .subjects import native_houses_for_subject


EVENT_RESOLUTION_VERSION = "1.1.0"


@dataclass(frozen=True)
class _Match:
    signature: EventSignature
    status: ResolutionStatus
    specificity: ResolutionSpecificity
    label: str
    required_covered: Tuple[int, ...]
    supporting_covered: Tuple[int, ...]
    missing_required: Tuple[int, ...]
    carriers: Tuple[str, ...]
    dasha_levels: Tuple[str, ...]
    transit_reinforced: bool
    karaka_confirmed: bool
    vargas: Tuple[DivisionalConfirmation, ...]
    eligibility_reasons: Tuple[str, ...]
    conflicts: Tuple[int, ...]
    lock_key: Tuple[int, ...]


def _eligibility(
    signature: EventSignature, life: Optional[LifeContext]
) -> Tuple[bool, str, Tuple[str, ...]]:
    label = signature.label
    if signature.eligibility_rule == "always":
        return True, label, ()
    if life is None:
        return True, signature.unknown_eligibility_label or label, ("life_context_unknown",)
    if signature.eligibility_rule == "business_owner":
        if life.business_owner is False:
            return False, label, ("business_owner_false",)
        if life.business_owner is None:
            return True, signature.unknown_eligibility_label, ("business_owner_unknown",)
        return True, label, ("business_owner_true",)
    if signature.eligibility_rule == "has_children":
        if life.has_children is False:
            return False, label, ("has_children_false",)
        if life.has_children is None:
            return True, signature.unknown_eligibility_label, ("has_children_unknown",)
        return True, label, ("has_children_true",)
    if signature.eligibility_rule == "relationship":
        status = (life.relationship_status or "unknown").strip().lower()
        if status in {"unknown", ""}:
            return True, signature.unknown_eligibility_label, ("relationship_status_unknown",)
        if status in {"married", "committed", "partnered"}:
            return True, "important relationship decision", (f"relationship_status_{status}",)
        return True, label, (f"relationship_status_{status}",)
    return False, label, ("unsupported_eligibility_rule",)


def _direct_dasha_rows(evidence: Sequence[Evidence]) -> Sequence[Evidence]:
    return tuple(
        row for row in evidence
        if row.provider == "dasha_house_activation"
        and row.facts.get("relation") in {
            "lordship", "occupation", "natal_aspect", "aspect"
        }
        and row.facts.get("dasha_level") in {"MD", "AD", "PD"}
    )


def _single_varga_confirmation(
    calculation: CalculationContext,
    varga_name: str,
    required_relative_houses: Sequence[int],
    subject: str,
    carriers: Set[str],
) -> DivisionalConfirmation:
    chart = calculation.divisional_charts.get(varga_name)
    target_houses = set(
        native_houses_for_subject(subject, required_relative_houses)
    )
    confirmed_carriers: Set[str] = set()
    confirmed_houses: Set[int] = set()
    relations: Set[str] = set()
    if chart:
        for planet in carriers:
            placement = chart["planets"].get(planet)
            if not placement:
                continue
            relation_houses = {
                "lordship": set(ruled_houses(chart, planet)),
                "occupation": {int(placement["house"])},
                "aspect": set(aspected_houses(planet, int(placement["house"]))),
            }
            for relation, houses in relation_houses.items():
                matched = houses.intersection(target_houses)
                if matched:
                    confirmed_carriers.add(planet)
                    confirmed_houses.update(matched)
                    relations.add(relation)
    return DivisionalConfirmation(
        chart=varga_name,
        confirmed=bool(confirmed_carriers),
        carrier_planets=tuple(sorted(confirmed_carriers)),
        houses=tuple(sorted(confirmed_houses)),
        relations=tuple(sorted(relations)),
        rule_id=(
            "active_d1_carrier_confirms_relevant_varga_house"
            if confirmed_carriers else "relevant_varga_did_not_confirm_active_d1_carrier"
        ),
    )


def _varga_confirmations(
    calculation: CalculationContext,
    signature: EventSignature,
    subject: str,
    carriers: Set[str],
) -> Tuple[DivisionalConfirmation, ...]:
    # For relatives, inspect both the relationship and event-domain vargas.
    # Neither is allowed to create or universally veto a D1 event.
    vargas = [signature.required_varga]
    if subject in {"mother", "father"}:
        vargas.append("D12")
    elif subject == "spouse":
        vargas.append("D9")
    return tuple(
        _single_varga_confirmation(
            calculation,
            varga,
            signature.required_relative_houses,
            subject,
            carriers,
        )
        for varga in dict.fromkeys(vargas)
    )


def _match_signature(
    candidate: PredictionCandidate,
    calculation: CalculationContext,
    signature: EventSignature,
    life: Optional[LifeContext],
) -> _Match:
    required = set(native_houses_for_subject(candidate.subject, signature.required_relative_houses))
    supporting = set(native_houses_for_subject(candidate.subject, signature.supporting_relative_houses))
    conflicts = set(native_houses_for_subject(candidate.subject, signature.conflict_relative_houses))
    direct_rows = _direct_dasha_rows(candidate.evidence)
    required_covered = {row.house for row in direct_rows if row.house in required}
    supporting_covered = {row.house for row in direct_rows if row.house in supporting}
    levels = {
        str(row.facts["dasha_level"])
        for row in direct_rows if row.house in required | supporting
    }
    d1_carriers = {
        row.planet for row in direct_rows
        if row.planet and row.house in required
    }
    transit_rows = tuple(
        row for row in candidate.evidence
        if row.provider == "transit_house" and row.house in required
    )
    # Cooperative MD/AD/PD delivery has already been established by the
    # house-first activation ledger.  A transit trigger need not be the same
    # planet that supplies natal lordship, occupation, or aspect.
    delivery_carriers = set(candidate.activation.carrier_planets)
    transit_carriers = {
        row.planet for row in transit_rows if row.planet in delivery_carriers
    }
    locked_carriers = set(d1_carriers).union(transit_carriers)
    vargas = _varga_confirmations(calculation, signature, candidate.subject, locked_carriers)
    varga_complete = bool(vargas) and all(row.confirmed for row in vargas)
    eligible, label, eligibility_reasons = _eligibility(signature, life)
    conflict_covered = {
        row.house for row in candidate.evidence
        if row.provider == "conflict_house" and row.house in conflicts
    }
    karaka_confirmed = bool(locked_carriers.intersection(signature.karakas))
    required_complete = required == required_covered
    supporting_complete = len(supporting_covered) >= signature.minimum_supporting_houses
    dasha_complete = bool(
        {"AD", "PD"}.intersection(candidate.activation.active_dasha_levels)
    )
    transit_complete = candidate.activation.transit_reinforced and bool(transit_carriers)
    if not eligible:
        status = ResolutionStatus.INELIGIBLE
        specificity = ResolutionSpecificity.NONE
    elif required_complete and dasha_complete and transit_complete:
        status = ResolutionStatus.RESOLVED
        specificity = (
            ResolutionSpecificity.CORROBORATED
            if supporting_complete and varga_complete
            else ResolutionSpecificity.CORE
        )
    else:
        status = ResolutionStatus.UNCONFIRMED
        specificity = ResolutionSpecificity.NONE
    lock_key = (
        int(required_complete),
        len(required_covered),
        int(supporting_complete),
        len(supporting_covered),
        int(dasha_complete),
        int(transit_complete),
        int(varga_complete),
        int(karaka_confirmed),
        -len(conflict_covered),
    )
    return _Match(
        signature=signature,
        status=status,
        specificity=specificity,
        label=label,
        required_covered=tuple(sorted(required_covered)),
        supporting_covered=tuple(sorted(supporting_covered)),
        missing_required=tuple(sorted(required - required_covered)),
        carriers=tuple(sorted(locked_carriers)),
        dasha_levels=tuple(candidate.activation.active_dasha_levels),
        transit_reinforced=transit_complete,
        karaka_confirmed=karaka_confirmed,
        vargas=vargas,
        eligibility_reasons=eligibility_reasons,
        conflicts=tuple(sorted(conflict_covered)),
        lock_key=lock_key,
    )


class EventResolutionEngine:
    """Resolves broad activated themes into hard-gated event signatures."""

    version = EVENT_RESOLUTION_VERSION

    def resolve(
        self,
        candidate: PredictionCandidate,
        calculation: CalculationContext,
        life_context: Optional[LifeContext],
    ) -> EventResolution:
        signatures = signatures_for_family(candidate.event_family)
        matches = [
            _match_signature(candidate, calculation, signature, life_context)
            for signature in signatures
        ]
        resolved = [row for row in matches if row.status == ResolutionStatus.RESOLVED]
        pool = resolved or [row for row in matches if row.status != ResolutionStatus.INELIGIBLE] or matches
        if not pool:
            return EventResolution(
                ResolutionStatus.UNCONFIRMED, ResolutionSpecificity.NONE,
                None, candidate.event_family, (), (), (), (), (), (),
                (), (), False, False, (), (), (), "no_registered_signature",
            )
        best_lock = max(row.lock_key for row in pool)
        tied = [row for row in pool if row.lock_key == best_lock]
        tied.sort(key=lambda row: (row.signature.priority, row.signature.key))
        best = tied[0]
        status = best.status
        alternatives: Tuple[str, ...] = ()
        signature_key: Optional[str] = best.signature.key
        label = best.label
        manifestations = tuple(best.signature.manifestations)
        if status == ResolutionStatus.RESOLVED and len(tied) > 1:
            status = ResolutionStatus.AMBIGUOUS
            signature_key = None
            label = candidate.event_family.replace("_", " ")
            alternatives = tuple(row.signature.key for row in tied)
            manifestations = tuple(
                dict.fromkeys(
                    manifestation
                    for row in tied
                    for manifestation in row.signature.manifestations
                )
            )
        return EventResolution(
            status=status,
            specificity=best.specificity,
            signature_key=signature_key,
            label=label,
            manifestations=manifestations,
            alternative_signature_keys=alternatives,
            interpretation_alternatives=(),
            required_houses_covered=best.required_covered,
            supporting_houses_covered=best.supporting_covered,
            missing_required_houses=best.missing_required,
            carrier_planets=best.carriers,
            dasha_levels=best.dasha_levels,
            transit_reinforced=best.transit_reinforced,
            karaka_confirmed=best.karaka_confirmed,
            divisional_confirmations=best.vargas,
            eligibility_reasons=best.eligibility_reasons,
            conflict_houses_activated=best.conflicts,
            rule_id=(
                "multiple_event_signatures_share_all_resolution_locks"
                if status == ResolutionStatus.AMBIGUOUS
                else "d1_dasha_transit_with_supporting_houses_and_varga_corroboration"
                if status == ResolutionStatus.RESOLVED
                and best.specificity == ResolutionSpecificity.CORROBORATED
                else "d1_dasha_transit_core_event"
                if status == ResolutionStatus.RESOLVED
                else "event_signature_hard_gate_not_met"
                if status == ResolutionStatus.UNCONFIRMED
                else "real_life_eligibility_rejected_signature"
            ),
        )
