from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import date, timedelta
from itertools import product
from typing import Dict, Iterable, List, Sequence, Tuple

from .context import CalculationContext, EvaluationContext
from .contracts import (
    ActivationAssessment,
    ActivationBand,
    Evidence,
    HouseActivation,
    HouseActivationState,
    Importance,
    OutcomeAssessment,
    Polarity,
    PredictionCandidate,
    PredictionRequest,
    PredictionResult,
    PredictionWindow,
    EventResolution,
    ResolutionSpecificity,
    ResolutionStatus,
    SCHEMA_VERSION,
)
from .chart_manifestations import (
    CHART_MANIFESTATION_REGISTRY_VERSION,
    ChartManifestationResolver,
)
from .event_resolution import EVENT_RESOLUTION_VERSION, EventResolutionEngine
from .event_signatures import EVENT_SIGNATURE_REGISTRY_VERSION
from .house_significations import (
    HOUSE_COMBINATIONS,
    HOUSE_SIGNIFICATION_REGISTRY_VERSION,
    build_house_interpretations,
)
from .house_activation import HouseActivationEngine, weighted_outcome
from .errors import PredictionCalculationError, PredictionConfigurationError
from .profiles import PredictionProfile
from .primitives import aspected_houses, ruled_houses
from .subjects import SUBJECTS, SUBJECT_REGISTRY_VERSION, native_houses_for_subject
from .taxonomy import EVENT_FAMILIES, TAXONOMY_VERSION, EventFamily


ENGINE_VERSION = "5.2.0"
_ACTIVATION_PROVIDERS = {
    "dasha_house_activation",
    "dispositor_activation",
    "transit_house",
    "transit_natal_relation",
    "dasha_planet_relationship",
}


def _activation_assessment(
    evidence: Sequence[Evidence],
    profile: PredictionProfile,
    family: EventFamily,
) -> ActivationAssessment:
    activation = [
        row
        for row in evidence
        if row.provider in _ACTIVATION_PROVIDERS
        and row.rule_id != "event_karaka_confirmation"
    ]
    independent = {row.independent_key for row in activation if row.independent_key}
    primary_dasha_activation = [
        row
        for row in activation
        if row.provider == "dasha_house_activation"
        and row.importance == Importance.PRIMARY
    ]
    direct_primary_activation = [
        row
        for row in primary_dasha_activation
        if row.facts.get("relation") in {"lordship", "occupation", "natal_aspect", "aspect"}
    ]
    carrier_planets = {row.planet for row in direct_primary_activation if row.planet}
    # MD/AD/PD planets cooperate when a declared natal sambandha exists.  The
    # relationship expands delivery carriers, but never creates a house
    # promise when no dasha planet has a direct natal connection to the house.
    changed = True
    while changed:
        changed = False
        for row in activation:
            if row.provider != "dasha_planet_relationship":
                continue
            first = row.facts.get("first_planet")
            second = row.facts.get("second_planet")
            if not row.facts.get("relations"):
                continue
            pair = {planet for planet in (first, second) if planet}
            if carrier_planets.intersection(pair) and not pair.issubset(carrier_planets):
                carrier_planets.update(pair)
                changed = True
    levels_by_planet = {
        str(row.facts.get("dasha_level")): row.planet
        for row in primary_dasha_activation
        if row.facts.get("dasha_level") in {"MD", "AD", "PD"} and row.planet
    }
    for row in activation:
        if row.provider == "dasha_planet_relationship":
            for prefix in ("first", "second"):
                level = row.facts.get(f"{prefix}_level")
                planet = row.facts.get(f"{prefix}_planet")
                if level in {"MD", "AD", "PD"} and planet:
                    levels_by_planet[str(level)] = str(planet)
    levels = sorted(
        {level for level, planet in levels_by_planet.items() if planet in carrier_planets},
        key=("MD", "AD", "PD").index,
    )
    primary_houses_covered = {row.house for row in direct_primary_activation if row.house}
    transit_event_carriers = {
        row.planet
        for row in activation
        if row.provider == "transit_house"
        and row.importance == Importance.PRIMARY
        and row.planet in carrier_planets
    }
    natal_relation_carriers = {
        row.planet
        for row in activation
        if row.provider == "transit_natal_relation"
        and row.planet in carrier_planets
    }
    full_reinforcement_carriers = transit_event_carriers.intersection(
        natal_relation_carriers
    )
    transit_reinforced = bool(transit_event_carriers)
    natal_position_reinforced = bool(natal_relation_carriers)
    karaka_carriers = {
        row.planet
        for row in evidence
        if row.rule_id == "event_karaka_confirmation" and row.planet in carrier_planets
    }
    primary_house_activated = bool(direct_primary_activation)
    active_subperiod_carrier = any(
        level in {"AD", "PD"} and planet in carrier_planets
        for level, planet in levels_by_planet.items()
    )
    natal_promise_met = (
        primary_house_activated
        and active_subperiod_carrier
        and len(levels) >= family.minimum_direct_dasha_levels
        and len(primary_houses_covered) >= family.minimum_primary_houses_covered
    )

    strong_transit_met = (
        bool(full_reinforcement_carriers)
        if profile.require_transit_for_strong
        else bool(transit_event_carriers)
    )

    if (
        natal_promise_met
        and strong_transit_met
        and len(independent) >= profile.minimum_independent_confirmations
    ):
        band = ActivationBand.STRONG
        rule_id = "primary_house_two_dasha_levels_with_transit"
    elif (
        natal_promise_met
        and len(independent) >= profile.minimum_independent_confirmations
        and transit_reinforced
        and (
            not family.require_karaka_for_moderate
            or bool(karaka_carriers)
            or len(carrier_planets) >= 2
        )
    ):
        band = ActivationBand.MODERATE
        rule_id = "primary_house_multiple_independent_confirmations"
    else:
        band = ActivationBand.INSUFFICIENT
        rule_id = "minimum_activation_gate_not_met"

    return ActivationAssessment(
        band=band,
        independent_confirmations=len(independent),
        active_dasha_levels=tuple(levels),
        transit_reinforced=transit_reinforced,
        natal_position_reinforced=natal_position_reinforced,
        primary_houses_covered=tuple(sorted(primary_houses_covered)),
        carrier_planets=tuple(sorted(carrier_planets)),
        rule_id=rule_id,
    )


def _outcome_assessment(
    evidence: Sequence[Evidence], activation: ActivationAssessment
) -> OutcomeAssessment:
    directional = tuple(
        row for row in evidence if row.provider not in _ACTIVATION_PROVIDERS
    )
    return weighted_outcome(directional, activation.carrier_planets)


def _assessment_from_house_ledger(
    rows: Sequence[HouseActivation],
    primary_houses: Sequence[int],
    family: EventFamily,
) -> ActivationAssessment:
    relevant = [row for row in rows if row.house in set(primary_houses)]
    delivered = [
        row for row in relevant
        if row.state in {
            HouseActivationState.DASHA_TRANSIT_ACTIVATED,
            HouseActivationState.FULLY_REINFORCED,
        }
    ]
    covered = tuple(sorted(row.house for row in delivered))
    if len(covered) < family.minimum_primary_houses_covered:
        return ActivationAssessment(
            band=ActivationBand.INSUFFICIENT,
            independent_confirmations=sum(
                row.activation.independent_confirmations for row in relevant
            ),
            active_dasha_levels=(),
            transit_reinforced=any(row.activation.transit_reinforced for row in relevant),
            natal_position_reinforced=False,
            primary_houses_covered=covered,
            carrier_planets=(),
            rule_id="house_first_required_primary_coverage_not_met",
        )
    carriers = tuple(sorted({
        planet for row in delivered for planet in row.activation.carrier_planets
    }))
    levels = tuple(
        level for level in ("MD", "AD", "PD")
        if any(level in row.activation.active_dasha_levels for row in delivered)
    )
    strong = any(row.state == HouseActivationState.FULLY_REINFORCED for row in delivered)
    return ActivationAssessment(
        band=ActivationBand.STRONG if strong else ActivationBand.MODERATE,
        independent_confirmations=sum(
            row.activation.independent_confirmations for row in delivered
        ),
        active_dasha_levels=levels,
        transit_reinforced=True,
        natal_position_reinforced=any(
            row.activation.natal_position_reinforced for row in delivered
        ),
        primary_houses_covered=covered,
        carrier_planets=carriers,
        rule_id=(
            "house_first_fully_reinforced_delivery"
            if strong else "house_first_cooperative_dasha_transit_delivery"
        ),
    )


def _candidate_id(
    request: PredictionRequest,
    profile: PredictionProfile,
    subject: str,
    family: EventFamily,
    window_start: str,
    evidence: Sequence[Evidence],
) -> str:
    payload = {
        "schema": SCHEMA_VERSION,
        "engine": ENGINE_VERSION,
        "profile": profile.key,
        "profile_version": profile.version,
        "chart": request.birth.birth_chart_id,
        "birth": request.birth.to_calculator_dict(),
        "subject": subject,
        "family": family.key,
        "window_start": window_start,
        "evidence": sorted(row.independent_key for row in evidence if row.independent_key),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:32]


def _rank_key(
    candidate: PredictionCandidate,
    family_priority: Sequence[str] = (),
) -> Tuple:
    band_order = {
        ActivationBand.STRONG: 0,
        ActivationBand.MODERATE: 1,
        ActivationBand.INSUFFICIENT: 2,
    }
    resolution_order = {
        ResolutionStatus.RESOLVED: 0,
        ResolutionStatus.AMBIGUOUS: 1,
        ResolutionStatus.UNCONFIRMED: 2,
        ResolutionStatus.INELIGIBLE: 3,
    }
    duration_days = (
        date.fromisoformat(candidate.window.end_date)
        - date.fromisoformat(candidate.window.start_date)
    ).days + 1
    try:
        priority = tuple(family_priority).index(candidate.event_family)
    except ValueError:
        priority = len(tuple(family_priority))
    return (
        resolution_order.get(
            candidate.resolution.status if candidate.resolution else ResolutionStatus.UNCONFIRMED,
            9,
        ),
        band_order[candidate.activation.band],
        -candidate.activation.independent_confirmations,
        -duration_days,
        priority,
        candidate.window.start_date,
        candidate.subject,
        candidate.event_family,
    )


def _merge_evidence_windows(
    evidence: Sequence[Evidence], start_date: str, end_date: str
) -> Tuple[Evidence, ...]:
    unique: Dict[Tuple, Evidence] = {}
    for row in evidence:
        key = (
            row.provider,
            row.rule_id,
            row.independent_key,
            row.planet,
            row.house,
            row.polarity.value,
            json.dumps(row.facts, sort_keys=True, default=str),
        )
        unique.setdefault(
            key,
            replace(row, window_start=start_date, window_end=end_date),
        )
    return tuple(unique.values())


def _consolidate_candidates(
    candidates: Sequence[PredictionCandidate],
    request: PredictionRequest,
    profile: PredictionProfile,
) -> List[PredictionCandidate]:
    ordered = sorted(
        candidates,
        key=lambda row: (row.subject, row.event_family, row.window.start_date),
    )
    merged: List[PredictionCandidate] = []
    for candidate in ordered:
        if not merged:
            merged.append(candidate)
            continue
        previous = merged[-1]
        contiguous = (
            date.fromisoformat(candidate.window.start_date)
            <= date.fromisoformat(previous.window.end_date) + timedelta(days=1)
        )
        same_basis = (
            previous.subject == candidate.subject
            and previous.event_family == candidate.event_family
            and previous.activation.band == candidate.activation.band
            and previous.outcome.tone == candidate.outcome.tone
            and previous.activation.carrier_planets == candidate.activation.carrier_planets
            and previous.window.mahadasha == candidate.window.mahadasha
            and previous.window.antardasha == candidate.window.antardasha
            and previous.window.pratyantardasha == candidate.window.pratyantardasha
        )
        if not contiguous or not same_basis:
            merged.append(candidate)
            continue
        start = previous.window.start_date
        end = max(previous.window.end_date, candidate.window.end_date)
        signatures = sorted(
            {previous.window.transit_signature, candidate.window.transit_signature}
        )
        combined_evidence = _merge_evidence_windows(
            (*previous.evidence, *candidate.evidence), start, end
        )
        family = EVENT_FAMILIES[candidate.event_family]
        activation = _activation_assessment(combined_evidence, profile, family)
        outcome = _outcome_assessment(combined_evidence, activation)
        window = PredictionWindow(
            start_date=start,
            end_date=end,
            mahadasha=previous.window.mahadasha,
            antardasha=previous.window.antardasha,
            pratyantardasha=previous.window.pratyantardasha,
            transit_signature=hashlib.sha256(
                "|".join(signatures).encode("utf-8")
            ).hexdigest()[:20],
        )
        merged[-1] = replace(
            previous,
            candidate_id=_candidate_id(
                request, profile, previous.subject, family, start, combined_evidence
            ),
            window=window,
            activation=activation,
            outcome=outcome,
            evidence=combined_evidence,
        )
    return merged


def _group_shared_house_interpretations(
    candidates: Sequence[PredictionCandidate],
    family_priority: Sequence[str],
    subjects: Sequence[str],
) -> List[PredictionCandidate]:
    """Group derived-house meanings that share one delivered native activation.

    A native house can simultaneously be the native's house and a different
    relative house for mother, father, or spouse. Registry order must not turn
    one of those frames into a unique prediction when the timing evidence is
    identical.
    """

    remaining = list(candidates)
    grouped: List[PredictionCandidate] = []
    while remaining:
        seed = remaining.pop(0)
        seed_resolution = seed.resolution
        cluster = [seed]
        if seed_resolution is not None:
            seed_carriers = set(seed_resolution.carrier_planets)
            matches: List[PredictionCandidate] = []
            for candidate in remaining:
                resolution = candidate.resolution
                if resolution is None:
                    continue
                same_timing = (
                    candidate.window.start_date == seed.window.start_date
                    and candidate.window.end_date == seed.window.end_date
                    and candidate.window.mahadasha == seed.window.mahadasha
                    and candidate.window.antardasha == seed.window.antardasha
                    and candidate.window.pratyantardasha == seed.window.pratyantardasha
                )
                different_frame = (
                    candidate.subject != seed.subject
                    or candidate.domain != seed.domain
                    or candidate.event_family != seed.event_family
                )
                if (
                    same_timing
                    and different_frame
                    and seed_carriers.intersection(resolution.carrier_planets)
                ):
                    matches.append(candidate)
            for candidate in matches:
                remaining.remove(candidate)
            cluster.extend(matches)

        should_expand_house_meanings = bool(
            seed_resolution
            and seed_resolution.specificity == ResolutionSpecificity.CORE
        )
        if len(cluster) == 1 and not should_expand_house_meanings:
            grouped.append(seed)
            continue

        cluster.sort(key=lambda row: _rank_key(row, family_priority))
        lead = cluster[0]
        assert lead.resolution is not None
        houses = tuple(sorted({
            house
            for row in cluster
            if row.resolution is not None
            for house in row.resolution.required_houses_covered
        }))
        common_carriers = set(lead.resolution.carrier_planets)
        for row in cluster[1:]:
            if row.resolution is not None:
                common_carriers.intersection_update(row.resolution.carrier_planets)
        combined_evidence = tuple(row for item in cluster for row in item.evidence)
        shared_activation = replace(
            lead.activation, carrier_planets=tuple(sorted(common_carriers))
        )
        shared_outcome = _outcome_assessment(
            tuple(row for row in combined_evidence if row.provider != "conflict_house"),
            shared_activation,
        )
        alternatives = build_house_interpretations(
            houses,
            subjects,
            tuple(sorted(common_carriers)),
            shared_outcome,
        )
        manifestations = tuple(
            dict.fromkeys(
                manifestation
                for row in alternatives
                for manifestation in row.manifestations
            )
        )
        specificity = (
            ResolutionSpecificity.CORROBORATED
            if all(
                row.resolution
                and row.resolution.specificity == ResolutionSpecificity.CORROBORATED
                for row in cluster
            )
            else ResolutionSpecificity.CORE
        )
        resolution = replace(
            lead.resolution,
            status=(
                ResolutionStatus.AMBIGUOUS
                if len(alternatives) > 1 else ResolutionStatus.RESOLVED
            ),
            specificity=specificity,
            signature_key=(alternatives[0].signature_key if len(alternatives) == 1 else None),
            label=(
                "multiple possible manifestations of the same activated house"
                if len(alternatives) > 1 else alternatives[0].label
            ),
            manifestations=manifestations,
            alternative_signature_keys=tuple(
                f"{row.subject}:{row.resolution.signature_key or row.event_family}"
                for row in cluster
                if row.resolution is not None
            ),
            interpretation_alternatives=alternatives,
            required_houses_covered=houses,
            carrier_planets=tuple(sorted(common_carriers)),
            rule_id=(
                "shared_native_house_multiple_derived_interpretations"
                if len(alternatives) > 1 else "house_first_single_interpretation"
            ),
        )
        candidate_id = hashlib.sha256(
            (
                "|".join(sorted(row.candidate_id for row in cluster))
                + "|shared-derived-house-interpretations-v1"
            ).encode("utf-8")
        ).hexdigest()[:32]
        grouped.append(
            replace(
                lead,
                candidate_id=candidate_id,
                subject=("multiple" if len(alternatives) > 1 else alternatives[0].subject),
                domain="house_significations",
                event_family="house_activation_" + "_".join(map(str, houses)),
                native_houses=houses,
                resolution=resolution,
                outcome=shared_outcome,
                evidence=combined_evidence,
            )
        )
    return grouped


def _merge_house_activation_windows(
    rows: Sequence[HouseActivation],
) -> Tuple[HouseActivation, ...]:
    """Merge presentation windows only when material astrological facts agree."""

    merged: List[HouseActivation] = []
    for row in sorted(rows, key=lambda item: (item.house, item.window.start_date)):
        if not merged or merged[-1].house != row.house:
            merged.append(row)
            continue
        previous = merged[-1]
        adjacent = (
            date.fromisoformat(previous.window.end_date) + timedelta(days=1)
            == date.fromisoformat(row.window.start_date)
        )
        materially_equal = (
            previous.state == row.state
            and previous.activation.band == row.activation.band
            and tuple(previous.activation.carrier_planets)
            == tuple(row.activation.carrier_planets)
            and previous.outcome == row.outcome
            and previous.window.mahadasha == row.window.mahadasha
            and previous.window.antardasha == row.window.antardasha
            and previous.window.pratyantardasha == row.window.pratyantardasha
            and tuple(previous.natal_connections) == tuple(row.natal_connections)
            and tuple(previous.transit_connections) == tuple(row.transit_connections)
            and previous.activation.natal_position_reinforced
            == row.activation.natal_position_reinforced
        )
        if not adjacent or not materially_equal:
            merged.append(row)
            continue

        combined_evidence_by_key = {
            evidence.independent_key: evidence
            for evidence in (*previous.evidence, *row.evidence)
        }
        window = replace(
            previous.window,
            end_date=row.window.end_date,
            transit_signature=hashlib.sha256(
                (
                    previous.window.transit_signature
                    + "|"
                    + row.window.transit_signature
                ).encode("utf-8")
            ).hexdigest()[:20],
        )
        evidence = tuple(
            replace(
                item,
                window_start=window.start_date,
                window_end=window.end_date,
            )
            for item in combined_evidence_by_key.values()
        )
        merged[-1] = replace(
            previous,
            window=window,
            evidence=evidence,
            trigger_planets=tuple(sorted(set(
                (*previous.trigger_planets, *row.trigger_planets)
            ))),
            timing_triggers=tuple({
                (
                    trigger["kind"],
                    trigger["start_date"],
                    trigger["end_date"],
                    trigger.get("moon_house"),
                ): trigger
                for trigger in (*previous.timing_triggers, *row.timing_triggers)
            }.values()),
            activation=replace(
                previous.activation,
                independent_confirmations=len(combined_evidence_by_key),
            ),
        )
    return tuple(sorted(merged, key=lambda item: (item.window.start_date, item.house)))


def _house_activation_rank(row: HouseActivation, as_of: date) -> Tuple:
    state_rank = {
        HouseActivationState.FULLY_REINFORCED: 0,
        HouseActivationState.DASHA_TRANSIT_ACTIVATED: 1,
        HouseActivationState.DASHA_CONNECTED: 2,
        HouseActivationState.TRANSIT_ONLY: 3,
        HouseActivationState.DORMANT: 4,
    }
    relation_diversity = len({
        connection["relation"] for connection in row.natal_connections
    })
    return (
        0
        if date.fromisoformat(row.window.start_date) <= as_of
        <= date.fromisoformat(row.window.end_date)
        else 1,
        state_rank[row.state],
        -relation_diversity,
        -len(row.activation.active_dasha_levels),
        -row.activation.independent_confirmations,
        row.window.start_date,
        row.house,
    )


def _allowed_native_houses(
    request: PredictionRequest, profile: PredictionProfile
) -> set[int]:
    if not request.domains:
        return set()
    domains = set(request.domains)
    allowed: set[int] = set()
    for family_key in profile.event_families:
        family = EVENT_FAMILIES[family_key]
        if family.domain not in domains:
            continue
        relative_houses = tuple(dict.fromkeys(
            (*family.primary_relative_houses, *family.supporting_relative_houses)
        ))
        for subject in request.subjects:
            allowed.update(native_houses_for_subject(subject, relative_houses))
    return allowed


def _subject_relevant(
    calculation: CalculationContext,
    activation: HouseActivation,
    subject: str,
) -> bool:
    if subject == "self":
        return True
    definition = SUBJECTS[subject]
    if activation.house == definition.anchor_house:
        return True
    carriers = set(activation.activation.carrier_planets)
    # A relative's natural karaka can make that person's derived-house frame
    # relevant for a specific future window when it both activates this house
    # and contacts a natal dasha carrier. This is timing-specific evidence; it
    # must not make the relative appear in earlier windows.
    if any(
        evidence.provider == "transit_natal_ledger"
        and evidence.planet in definition.karakas
        and evidence.facts.get("natal_planet") in carriers
        for evidence in activation.evidence
    ):
        return True
    if carriers.intersection(definition.karakas):
        return True
    chart = calculation.chart
    for planet in carriers:
        placement = chart["planets"][planet]
        if definition.anchor_house in ruled_houses(chart, planet):
            return True
        if int(placement["house"]) == definition.anchor_house:
            return True
        if definition.anchor_house in aspected_houses(planet, int(placement["house"])):
            return True
    return False


def _candidate_from_house_activation(
    request: PredictionRequest,
    profile: PredictionProfile,
    calculation: CalculationContext,
    row: HouseActivation,
) -> PredictionCandidate:
    subjects = tuple(
        subject for subject in request.subjects
        if _subject_relevant(calculation, row, subject)
    ) or ("self",)
    alternatives = build_house_interpretations(
        (row.house,), subjects, row.activation.carrier_planets, row.outcome
    )
    manifestations = tuple(dict.fromkeys(
        text for alternative in alternatives for text in alternative.manifestations
    ))
    candidate_id = hashlib.sha256(
        json.dumps({
            "schema": SCHEMA_VERSION,
            "engine": ENGINE_VERSION,
            "profile": profile.key,
            "chart": request.birth.birth_chart_id,
            "birth": request.birth.to_calculator_dict(),
            "house": row.house,
            "window": [row.window.start_date, row.window.end_date],
            "state": row.state.value,
            "carriers": list(row.activation.carrier_planets),
            "subjects": list(subjects),
            "evidence": sorted(
                evidence.independent_key for evidence in row.evidence
                if evidence.independent_key
            ),
        }, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:32]
    resolution = EventResolution(
        status=(
            ResolutionStatus.AMBIGUOUS
            if len(manifestations) > 1 or len(alternatives) > 1
            else ResolutionStatus.RESOLVED
        ),
        specificity=ResolutionSpecificity.CORE,
        signature_key=(alternatives[0].signature_key if len(alternatives) == 1 else None),
        label=(
            alternatives[0].label
            if len(alternatives) == 1
            else "multiple bounded manifestations of one activated native house"
        ),
        manifestations=manifestations,
        alternative_signature_keys=tuple(
            f"{alternative.subject}:{alternative.signature_key}"
            for alternative in alternatives
        ),
        interpretation_alternatives=alternatives,
        required_houses_covered=(row.house,),
        supporting_houses_covered=(),
        missing_required_houses=(),
        carrier_planets=row.activation.carrier_planets,
        dasha_levels=row.activation.active_dasha_levels,
        transit_reinforced=row.activation.transit_reinforced,
        karaka_confirmed=False,
        divisional_confirmations=(),
        eligibility_reasons=(),
        conflict_houses_activated=(),
        rule_id="house_first_activation_with_bounded_manifestations",
    )
    return PredictionCandidate(
        candidate_id=candidate_id,
        subject=(subjects[0] if len(subjects) == 1 else "multiple"),
        domain="house_significations",
        event_family=f"house_activation_{row.house}",
        native_houses=(row.house,),
        window=row.window,
        activation=row.activation,
        outcome=row.outcome,
        evidence=row.evidence,
        resolution=resolution,
    )


def _combination_candidates(
    request: PredictionRequest,
    profile: PredictionProfile,
    calculation: CalculationContext,
    activations: Sequence[HouseActivation],
) -> List[PredictionCandidate]:
    event_states = {
        HouseActivationState.DASHA_TRANSIT_ACTIVATED,
        HouseActivationState.FULLY_REINFORCED,
    }
    by_house = {
        house: [
            row for row in activations
            if row.house == house and row.state in event_states
        ]
        for house in range(1, 13)
    }
    output: List[PredictionCandidate] = []
    for combination in HOUSE_COMBINATIONS:
        if not all(by_house[house] for house in combination.relative_houses):
            continue
        best: PredictionCandidate | None = None
        for rows in product(*(by_house[house] for house in combination.relative_houses)):
            chain = {
                (
                    row.window.mahadasha,
                    row.window.antardasha,
                    row.window.pratyantardasha,
                )
                for row in rows
            }
            if len(chain) != 1:
                continue
            start = max(date.fromisoformat(row.window.start_date) for row in rows)
            end = min(date.fromisoformat(row.window.end_date) for row in rows)
            if start > end:
                continue
            carriers = tuple(sorted({
                planet for row in rows for planet in row.activation.carrier_planets
            }))
            if not carriers:
                continue
            evidence_by_key = {
                evidence.independent_key: replace(
                    evidence,
                    window_start=start.isoformat(),
                    window_end=end.isoformat(),
                )
                for row in rows for evidence in row.evidence
            }
            evidence = tuple(evidence_by_key.values())
            all_full = all(
                row.state == HouseActivationState.FULLY_REINFORCED for row in rows
            )
            outcome = weighted_outcome(evidence, carriers)
            first = rows[0]
            window = PredictionWindow(
                start.isoformat(),
                end.isoformat(),
                first.window.mahadasha,
                first.window.antardasha,
                first.window.pratyantardasha,
                hashlib.sha256(
                    "|".join(row.window.transit_signature for row in rows).encode("utf-8")
                ).hexdigest()[:20],
            )
            activation = ActivationAssessment(
                band=ActivationBand.STRONG if all_full else ActivationBand.MODERATE,
                independent_confirmations=len(evidence_by_key),
                active_dasha_levels=tuple(
                    level for level in ("MD", "AD", "PD")
                    if any(level in row.activation.active_dasha_levels for row in rows)
                ),
                transit_reinforced=True,
                natal_position_reinforced=all(
                    row.activation.natal_position_reinforced for row in rows
                ),
                primary_houses_covered=tuple(combination.relative_houses),
                carrier_planets=carriers,
                rule_id="simultaneous_house_combination_delivery",
            )
            aggregate = replace(
                first,
                house=combination.relative_houses[0],
                window=window,
                state=(
                    HouseActivationState.FULLY_REINFORCED
                    if all_full else HouseActivationState.DASHA_TRANSIT_ACTIVATED
                ),
                activation=activation,
                outcome=outcome,
                evidence=evidence,
            )
            candidate = _candidate_from_house_activation(
                request, profile, calculation, aggregate
            )
            # Replace the single-house interpretation with the complete,
            # simultaneously delivered combination.
            subjects = tuple(
                subject for subject in request.subjects
                if subject == "self"
                or any(_subject_relevant(calculation, row, subject) for row in rows)
            ) or ("self",)
            alternatives = build_house_interpretations(
                combination.relative_houses, subjects, carriers, outcome
            )
            manifestations = tuple(dict.fromkeys(
                text for alternative in alternatives for text in alternative.manifestations
            ))
            resolution = replace(
                candidate.resolution,
                status=ResolutionStatus.AMBIGUOUS,
                signature_key=(
                    alternatives[0].signature_key if len(alternatives) == 1 else None
                ),
                label=(
                    alternatives[0].label
                    if len(alternatives) == 1
                    else "multiple bounded manifestations of one activated house combination"
                ),
                manifestations=manifestations,
                alternative_signature_keys=tuple(
                    f"{alternative.subject}:{alternative.signature_key}"
                    for alternative in alternatives
                ),
                interpretation_alternatives=alternatives,
                required_houses_covered=tuple(combination.relative_houses),
                rule_id="house_first_combination_with_bounded_manifestations",
            )
            candidate = replace(
                candidate,
                candidate_id=hashlib.sha256(
                    (
                        candidate.candidate_id
                        + "|"
                        + combination.key
                        + "|"
                        + start.isoformat()
                        + "|"
                        + end.isoformat()
                    ).encode("utf-8")
                ).hexdigest()[:32],
                subject=(subjects[0] if len(subjects) == 1 else "multiple"),
                event_family=f"house_combination_{combination.key}",
                native_houses=tuple(combination.relative_houses),
                activation=activation,
                outcome=outcome,
                evidence=evidence,
                resolution=resolution,
            )
            rank = (
                0 if start <= request.as_of <= end else 1,
                0 if all_full else 1,
                -activation.independent_confirmations,
                start,
            )
            if best is None:
                best = candidate
            else:
                best_start = date.fromisoformat(best.window.start_date)
                best_end = date.fromisoformat(best.window.end_date)
                best_rank = (
                    0 if best_start <= request.as_of <= best_end else 1,
                    0 if best.activation.band == ActivationBand.STRONG else 1,
                    -best.activation.independent_confirmations,
                    best_start,
                )
                if rank < best_rank:
                    best = candidate
        if best is not None:
            output.append(best)
    return output


class PredictionEngine:
    def __init__(self, registry) -> None:
        self.registry = registry
        self.event_resolver = EventResolutionEngine()
        self.house_activation_engine = HouseActivationEngine()
        self.chart_manifestation_resolver = ChartManifestationResolver()

    def generate(
        self,
        request: PredictionRequest,
        calculation: CalculationContext,
        profile: PredictionProfile,
    ) -> PredictionResult:
        """Generate from the house ledger; event vocabulary is downstream."""

        # Resolve the registry even though house facts are calculated by the
        # independent ledger.  This keeps profile/provider version failures
        # fail-closed and preserves the public configuration contract.
        self.registry.resolve(
            profile.provider_ids,
            profile_key=profile.key,
            expected_versions=dict(profile.provider_versions),
        )
        unknown_subjects = sorted(set(request.subjects).difference(SUBJECTS))
        if unknown_subjects:
            raise PredictionConfigurationError(
                f"Unsupported subjects: {', '.join(unknown_subjects)}"
            )

        raw_activations = self.house_activation_engine.evaluate(calculation)
        house_activations = _merge_house_activation_windows(raw_activations)
        allowed_houses = _allowed_native_houses(request, profile)
        eligible = [
            row for row in house_activations
            if row.state in {
                HouseActivationState.DASHA_TRANSIT_ACTIVATED,
                HouseActivationState.FULLY_REINFORCED,
            }
            and (not allowed_houses or row.house in allowed_houses)
        ]

        best_by_house: Dict[int, HouseActivation] = {}
        for row in sorted(
            eligible,
            key=lambda item: _house_activation_rank(item, request.as_of),
        ):
            best_by_house.setdefault(row.house, row)

        candidate_activation_rows = (
            eligible if request.exploration_mode else best_by_house.values()
        )
        single_house_candidates = [
            _candidate_from_house_activation(request, profile, calculation, row)
            for row in candidate_activation_rows
        ]
        candidates = _combination_candidates(
            request, profile, calculation, eligible
        ) + single_house_candidates
        candidates.sort(key=lambda row: (
            0
            if date.fromisoformat(row.window.start_date) <= request.as_of
            <= date.fromisoformat(row.window.end_date)
            else 1,
            0 if row.activation.band == ActivationBand.STRONG else 1,
            -len(row.native_houses),
            -row.activation.independent_confirmations,
            row.window.start_date,
            row.native_houses,
        ))
        requested_limit = (
            request.maximum_candidates
            if request.exploration_mode
            else min(request.maximum_candidates, profile.maximum_candidates)
        )
        final_candidates = tuple(candidates[:requested_limit])
        chart_manifestations = self.chart_manifestation_resolver.resolve(
            request,
            house_activations,
            maximum_results=min(12, requested_limit),
        )

        signature_payload = {
            "engine": ENGINE_VERSION,
            "schema": SCHEMA_VERSION,
            "profile": profile.key,
            "profile_version": profile.version,
            "conventions": profile.conventions.__dict__,
            "providers": self.registry.versions(profile.provider_ids),
            "subject_registry_version": SUBJECT_REGISTRY_VERSION,
            "house_signification_registry_version": HOUSE_SIGNIFICATION_REGISTRY_VERSION,
            "house_activation_policy_version": self.house_activation_engine.version,
            "chart_manifestation_resolver_version": self.chart_manifestation_resolver.version,
            "chart_manifestation_registry_version": CHART_MANIFESTATION_REGISTRY_VERSION,
            "natal_promise_policy_versions": sorted({
                str(row.get("policy_version")) for row in calculation.natal_promises
            }),
            "as_of": request.as_of.isoformat(),
            "horizon_days": request.horizon_days,
            "subjects": list(request.subjects),
            "domains": list(request.domains or ()),
            "candidate_ids": [candidate.candidate_id for candidate in final_candidates],
            "manifestation_ids": [
                manifestation.manifestation_id
                for manifestation in chart_manifestations
            ],
            "house_states": [
                (row.window.start_date, row.window.end_date, row.house, row.state.value)
                for row in house_activations
            ],
        }
        evidence_signature = hashlib.sha256(
            json.dumps(signature_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return PredictionResult(
            engine_version=ENGINE_VERSION,
            schema_version=SCHEMA_VERSION,
            profile=profile.key,
            profile_version=profile.version,
            as_of=request.as_of.isoformat(),
            horizon_end=(request.as_of + timedelta(days=request.horizon_days - 1)).isoformat(),
            evidence_signature=evidence_signature,
            candidates=final_candidates,
            house_activations=house_activations,
            chart_manifestations=chart_manifestations,
            natal_promises=tuple(calculation.natal_promises),
            diagnostics=(
                {
                    "windows": len(calculation.windows),
                    "raw_house_activation_rows": len(raw_activations),
                    "merged_house_activation_rows": len(house_activations),
                    "eligible_before_deduplication": len(eligible),
                    "eligible_activation_windows": len(eligible),
                    "provider_versions": self.registry.versions(profile.provider_ids),
                    "conventions": profile.conventions.__dict__,
                    "house_activation_policy_version": self.house_activation_engine.version,
                    "chart_manifestation_resolver_version": self.chart_manifestation_resolver.version,
                    "chart_manifestations": len(chart_manifestations),
                    "house_state_counts": {
                        state.value: sum(
                            1 for row in house_activations if row.state == state
                        )
                        for state in HouseActivationState
                    },
                }
                if request.trace else {}
            ),
        )

    def _legacy_family_first_reference_only(
        self,
        request: PredictionRequest,
        calculation: CalculationContext,
        profile: PredictionProfile,
    ) -> PredictionResult:
        providers = self.registry.resolve(
            profile.provider_ids,
            profile_key=profile.key,
            expected_versions=dict(profile.provider_versions),
        )
        unknown_subjects = sorted(set(request.subjects).difference(SUBJECTS))
        if unknown_subjects:
            raise PredictionConfigurationError(
                f"Unsupported subjects: {', '.join(unknown_subjects)}"
            )
        domain_filter = set(request.domains or ())
        families = [
            EVENT_FAMILIES[key]
            for key in profile.event_families
            if key not in set(profile.blocked_event_families)
            and EVENT_FAMILIES[key].safety_allowed
        ]
        if domain_filter:
            families = [family for family in families if family.domain in domain_filter]

        # Establish the complete 12-house field before consulting any event
        # family.  Event taxonomies may filter or phrase this ledger, but they
        # are no longer allowed to decide whether a house exists.
        house_activations = self.house_activation_engine.evaluate(calculation)
        ledger_by_window: Dict[Tuple[str, str, str], Tuple[HouseActivation, ...]] = {}
        for window in calculation.windows:
            key = (window.start_date, window.end_date, window.transit_signature)
            ledger_by_window[key] = tuple(
                row for row in house_activations
                if row.window.start_date == window.start_date
                and row.window.end_date == window.end_date
                and row.window.transit_signature == window.transit_signature
            )

        candidates: List[PredictionCandidate] = []
        evaluated_combinations = 0
        for window in calculation.windows:
            for subject in request.subjects:
                for family in families:
                    evaluated_combinations += 1
                    primary_houses = native_houses_for_subject(
                        subject, family.primary_relative_houses
                    )
                    supporting_houses = native_houses_for_subject(
                        subject, family.supporting_relative_houses
                    )
                    conflicting_houses = native_houses_for_subject(
                        subject, family.conflicting_relative_houses
                    )
                    window_ledger = ledger_by_window[
                        (window.start_date, window.end_date, window.transit_signature)
                    ]
                    activation = _assessment_from_house_ledger(
                        window_ledger, primary_houses, family
                    )
                    if activation.band == ActivationBand.INSUFFICIENT:
                        continue
                    eval_context = EvaluationContext(
                        calculation=calculation,
                        window=window,
                        subject=subject,
                        event_family=family,
                        primary_houses=primary_houses,
                        supporting_houses=supporting_houses,
                        conflicting_houses=conflicting_houses,
                    )
                    evidence: List[Evidence] = []
                    for provider in providers:
                        try:
                            rows = provider.evaluate(eval_context)
                        except Exception as exc:
                            raise PredictionCalculationError(
                                "Evidence provider "
                                f"{provider.provider_id}@{provider.version} failed for "
                                f"{subject}/{family.key}/{window.start_date}"
                            ) from exc
                        if not isinstance(rows, list):
                            raise PredictionCalculationError(
                                f"Evidence provider {provider.provider_id}@{provider.version} "
                                "did not return a list"
                            )
                        evidence.extend(rows)
                    outcome = _outcome_assessment(evidence, activation)
                    candidates.append(
                        PredictionCandidate(
                            candidate_id=_candidate_id(
                                request,
                                profile,
                                subject,
                                family,
                                window.start_date,
                                evidence,
                            ),
                            subject=subject,
                            domain=family.domain,
                            event_family=family.key,
                            native_houses=tuple(
                                dict.fromkeys((*primary_houses, *supporting_houses))
                            ),
                            window=window,
                            activation=activation,
                            outcome=outcome,
                            evidence=tuple(evidence),
                        )
                    )

        candidates = _consolidate_candidates(candidates, request, profile)

        resolution_counts: Dict[str, int] = {}
        resolved_candidates: List[PredictionCandidate] = []
        for candidate in candidates:
            resolution = self.event_resolver.resolve(
                candidate, calculation, request.life_context
            )
            resolution_counts[resolution.status.value] = (
                resolution_counts.get(resolution.status.value, 0) + 1
            )
            if profile.require_event_resolution and resolution.status not in {
                ResolutionStatus.RESOLVED,
                ResolutionStatus.AMBIGUOUS,
            }:
                continue
            resolved_id = hashlib.sha256(
                (
                    candidate.candidate_id
                    + "|"
                    + str(resolution.signature_key)
                    + "|"
                    + ",".join(resolution.alternative_signature_keys)
                    + "|"
                    + resolution.status.value
                    + "|"
                    + EVENT_RESOLUTION_VERSION
                ).encode("utf-8")
            ).hexdigest()[:32]
            resolved_candidates.append(
                replace(candidate, candidate_id=resolved_id, resolution=resolution)
            )
        candidates = resolved_candidates
        candidates = _group_shared_house_interpretations(
            candidates, profile.event_family_priority, request.subjects
        )

        # This profile needs distinct homepage themes, not repeated daily/window
        # variants of the same subject/event family. Preserve the strongest and
        # earliest reproducible candidate for each theme.
        best_theme: Dict[Tuple[str, str], PredictionCandidate] = {}
        for candidate in sorted(
            candidates,
            key=lambda row: _rank_key(row, profile.event_family_priority),
        ):
            best_theme.setdefault((candidate.subject, candidate.event_family), candidate)

        final_candidates: List[PredictionCandidate] = []
        subject_counts: Dict[str, int] = {}
        timing_counts: Dict[Tuple[str, str, Tuple[str, ...]], int] = {}
        used_families = set()
        requested_limit = min(request.maximum_candidates, profile.maximum_candidates)
        ordered_themes = sorted(
            best_theme.values(),
            key=lambda row: _rank_key(row, profile.event_family_priority),
        )
        for candidate in ordered_themes:
            timing_key = (
                candidate.window.start_date,
                candidate.window.end_date,
                tuple(candidate.activation.carrier_planets),
            )
            if subject_counts.get(candidate.subject, 0) >= profile.maximum_per_subject:
                continue
            if timing_counts.get(timing_key, 0) >= profile.maximum_per_timing_signature:
                continue
            if candidate.event_family in used_families:
                continue
            final_candidates.append(candidate)
            used_families.add(candidate.event_family)
            subject_counts[candidate.subject] = subject_counts.get(candidate.subject, 0) + 1
            timing_counts[timing_key] = timing_counts.get(timing_key, 0) + 1
            if len(final_candidates) >= requested_limit:
                break

        signature_payload = {
            "engine": ENGINE_VERSION,
            "schema": SCHEMA_VERSION,
            "profile": profile.key,
            "profile_version": profile.version,
            "providers": self.registry.versions(profile.provider_ids),
            "subject_registry_version": SUBJECT_REGISTRY_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
            "event_signature_registry_version": EVENT_SIGNATURE_REGISTRY_VERSION,
            "house_signification_registry_version": HOUSE_SIGNIFICATION_REGISTRY_VERSION,
            "event_resolution_version": EVENT_RESOLUTION_VERSION,
            "house_activation_policy_version": self.house_activation_engine.version,
            "safety_policy_version": profile.safety_policy_version,
            "as_of": request.as_of.isoformat(),
            "horizon_days": request.horizon_days,
            "subjects": list(request.subjects),
            "domains": list(request.domains or ()),
            "candidate_ids": [candidate.candidate_id for candidate in final_candidates],
            "house_activation_states": [
                (row.window.start_date, row.house, row.state.value)
                for row in house_activations
            ],
        }
        evidence_signature = hashlib.sha256(
            json.dumps(signature_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return PredictionResult(
            engine_version=ENGINE_VERSION,
            schema_version=SCHEMA_VERSION,
            profile=profile.key,
            profile_version=profile.version,
            as_of=request.as_of.isoformat(),
            horizon_end=(request.as_of + timedelta(days=request.horizon_days - 1)).isoformat(),
            evidence_signature=evidence_signature,
            candidates=tuple(final_candidates),
            house_activations=tuple(house_activations),
            diagnostics=(
                {
                    "windows": len(calculation.windows),
                    "evaluated_combinations": evaluated_combinations,
                    "eligible_before_deduplication": len(candidates),
                    "provider_versions": self.registry.versions(profile.provider_ids),
                    "resolution_counts": resolution_counts,
                    "house_activation_policy_version": self.house_activation_engine.version,
                    "house_state_counts": {
                        state.value: sum(1 for row in house_activations if row.state == state)
                        for state in HouseActivationState
                    },
                }
                if request.trace
                else {}
            ),
        )
