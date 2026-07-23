from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from itertools import product
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from .contracts import (
    ActivationBand,
    ChartManifestation,
    HouseActivation,
    HouseActivationState,
    ManifestationHouseRole,
    Polarity,
    PredictionRequest,
    PredictionWindow,
)
from .house_significations import COMBINATION_TONE_READINGS, HOUSE_COMBINATIONS
from .subjects import SUBJECTS, native_houses_for_subject


CHART_MANIFESTATION_RESOLVER_VERSION = "1.2.0"
CHART_MANIFESTATION_REGISTRY_VERSION = "1.2.0"


@dataclass(frozen=True)
class ManifestationSignature:
    key: str
    domain: str
    required_relative_houses: Sequence[int]
    focus_relative_houses: Sequence[int]
    role_by_relative_house: Mapping[int, str]
    label: str
    alternatives: Sequence[str]
    priority: int


_DOMAINS = {
    "income_accumulation": "finance",
    "career_recognition": "career",
    "service_income": "career",
    "financial_obligation": "finance",
    "shared_finances": "finance",
    "partnership_result": "relationship",
    "property_result": "property",
    "education_creative_result": "education",
    "long_distance_opportunity": "travel",
    "health_and_recovery": "health",
    "home_change_or_relocation": "property",
    "travel_or_foreign_stay": "travel",
}

_HOUSE_ROLES = {
    1: "person or vitality affected",
    2: "resources, family or speech involved",
    3: "effort, communication or movement involved",
    4: "home, property or foundation involved",
    5: "learning, child, judgment or creation involved",
    6: "work, health, debt or obstacle involved",
    7: "partner, agreement or counterparty involved",
    8: "shared resources, vulnerability or major adjustment involved",
    9: "guidance, father, fortune or long-distance factor involved",
    10: "career, authority or visible action involved",
    11: "gain, result, network or fulfilment involved",
    12: "expense, distance, release or withdrawal involved",
}

_SIGNATURE_ROLES: Dict[str, Dict[int, str]] = {
    "income_accumulation": {
        2: "savings and retained resources",
        11: "income, gains and fulfilment of a financial objective",
    },
    "career_recognition": {
        10: "career, authority and visible responsibility",
        11: "recognition, professional gains and achieved objectives",
    },
    "service_income": {
        2: "pay, savings and available resources",
        6: "employment, service, workload or obligations",
        10: "career role and responsibility",
        11: "income, recognition and results",
    },
    "financial_obligation": {
        2: "savings, family resources and cash reserves",
        6: "debt, repayment, workload or a recurring obligation",
    },
    "shared_finances": {
        2: "personal or family resources",
        8: "joint money, tax, insurance, inheritance or consequential adjustment",
    },
    "partnership_result": {
        7: "spouse, partner, agreement or counterparty",
        11: "the result, gain or fulfilment sought through that connection",
    },
    "property_result": {
        4: "home, residence, property or emotional foundation",
        11: "progress, gain or fulfilment of the property objective",
    },
    "education_creative_result": {
        5: "study, children, creativity, judgment or counsel",
        11: "achievement, recognition or fulfilment of that objective",
    },
    "long_distance_opportunity": {
        9: "guidance, higher learning, father or long-distance opportunity",
        11: "gain, support or fulfilment of the long-term objective",
    },
    "health_and_recovery": {
        1: "the person, body, vitality and capacity to act",
        6: "health management, treatment, routine or an obstacle to overcome",
    },
    "home_change_or_relocation": {
        4: "home, residence, property and stability",
        12: "distance, expense, separation, release or foreign residence",
    },
    "travel_or_foreign_stay": {
        3: "planning, documents, communication and movement",
        9: "long-distance travel, guidance or higher purpose",
        12: "foreign stay, expense, distance or time away",
    },
}

_SIGNATURE_TOPICS: Dict[str, Tuple[str, str]] = {
    "income_accumulation": (
        "income, savings or collection of money",
        "the availability and use of accumulated resources",
    ),
    "career_recognition": (
        "recognition, promotion or gain through work",
        "progress toward a professional objective",
    ),
    "service_income": (
        "employment-related income and responsibility",
        "workload connected with compensation or professional gains",
    ),
    "financial_obligation": (
        "debt, repayment or a recurring family expense",
        "resources being directed toward an obligation",
    ),
    "shared_finances": (
        "joint money, tax, insurance or inheritance",
        "a financial adjustment involving another person",
    ),
    "partnership_result": (
        "a relationship or business agreement reaching a result",
        "a gain or objective pursued through collaboration",
    ),
    "property_result": (
        "a property or residence objective",
        "resources or gains connected with home or fixed assets",
    ),
    "education_creative_result": (
        "study, a creative objective or an application of judgment",
        "a child-related responsibility or development",
    ),
    "long_distance_opportunity": (
        "travel, higher learning, guidance or a mentor",
        "a long-term or distant opportunity",
    ),
    "health_and_recovery": (
        "health, treatment or daily routine",
        "effort directed toward managing an obstacle",
    ),
    "home_change_or_relocation": (
        "a change of home or residence",
        "expense, distance or release connected with property",
    ),
    "travel_or_foreign_stay": (
        "a significant journey or distant connection",
        "planning, documentation or expense connected with travel",
    ),
}


def _bounded_possibilities(key: str, tone: Polarity) -> Tuple[str, ...]:
    topics = _SIGNATURE_TOPICS[key]
    prefix = {
        Polarity.SUPPORTIVE: "Constructive movement may occur around",
        Polarity.MIXED: "Movement is possible, with adjustment or delay, around",
        Polarity.CHALLENGING: "Pressure, delay or obstruction may involve",
        Polarity.NEUTRAL: "A development may involve",
    }[tone]
    return tuple(f"{prefix} {topic}." for topic in topics)


MANIFESTATION_SIGNATURES: Tuple[ManifestationSignature, ...] = tuple(
    ManifestationSignature(
        key=row.key,
        domain=_DOMAINS[row.key],
        required_relative_houses=tuple(row.relative_houses),
        focus_relative_houses=tuple(row.focus_relative_houses),
        role_by_relative_house={
            house: _SIGNATURE_ROLES.get(row.key, {}).get(house, _HOUSE_ROLES[house])
            for house in row.relative_houses
        },
        label=row.label,
        alternatives=tuple(row.manifestations),
        priority=index,
    )
    for index, row in enumerate(HOUSE_COMBINATIONS)
)


_ELIGIBLE_STATES = {
    HouseActivationState.DASHA_TRANSIT_ACTIVATED,
    HouseActivationState.FULLY_REINFORCED,
}


def _same_dasha(left: HouseActivation, right: HouseActivation) -> bool:
    return (
        left.window.mahadasha == right.window.mahadasha
        and left.window.antardasha == right.window.antardasha
        and left.window.pratyantardasha == right.window.pratyantardasha
    )


def _overlap(rows: Sequence[HouseActivation]) -> Tuple[date, date] | None:
    start = max(date.fromisoformat(row.window.start_date) for row in rows)
    end = min(date.fromisoformat(row.window.end_date) for row in rows)
    return (start, end) if start <= end else None


def _direct_carriers(row: HouseActivation) -> Set[str]:
    return {
        str(connection["planet"])
        for connection in row.natal_connections
        if connection.get("planet")
    }


def _relationship_edges(rows: Sequence[HouseActivation]) -> Dict[str, Set[str]]:
    graph: Dict[str, Set[str]] = {}
    for row in rows:
        for relationship in row.dasha_relationships:
            if not relationship.relations:
                continue
            graph.setdefault(relationship.first_planet, set()).add(
                relationship.second_planet
            )
            graph.setdefault(relationship.second_planet, set()).add(
                relationship.first_planet
            )
    return graph


def _reachable(graph: Mapping[str, Set[str]], starts: Iterable[str]) -> Set[str]:
    seen = set(starts)
    pending = list(seen)
    while pending:
        current = pending.pop()
        for neighbour in graph.get(current, set()):
            if neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    return seen


def _carrier_coherence(
    rows: Sequence[HouseActivation],
) -> Tuple[str, Tuple[str, ...], Tuple[Dict[str, object], ...]] | None:
    direct_sets = [_direct_carriers(row) for row in rows]
    if any(not carriers for carriers in direct_sets):
        return None
    shared = set.intersection(*direct_sets)
    if shared:
        return "shared_direct_carrier", tuple(sorted(shared)), ()

    graph = _relationship_edges(rows)
    reachable = _reachable(graph, direct_sets[0])
    if not all(reachable.intersection(carriers) for carriers in direct_sets[1:]):
        return None
    all_direct = set().union(*direct_sets)
    relationships = []
    seen = set()
    for row in rows:
        for relationship in row.dasha_relationships:
            pair = tuple(sorted((relationship.first_planet, relationship.second_planet)))
            key = (pair, tuple(relationship.relations))
            if (
                relationship.relations
                and pair[0] in reachable
                and pair[1] in reachable
                and key not in seen
            ):
                seen.add(key)
                relationships.append({
                    "planets": pair,
                    "relations": tuple(relationship.relations),
                    "natal_houses": tuple(relationship.natal_houses),
                })
    return (
        "connected_dasha_carriers",
        tuple(sorted(all_direct)),
        tuple(relationships),
    )


def _subject_lock(
    subject: str,
    rows: Sequence[HouseActivation],
    by_house: Mapping[int, Sequence[HouseActivation]],
) -> Tuple[Tuple[HouseActivation, ...], Dict[str, object]] | None:
    if subject == "self":
        return tuple(rows), {
            "method": "native_frame",
            "description": "This combination is read directly from the native chart.",
        }

    definition = SUBJECTS[subject]
    direct_carriers = set().union(*(_direct_carriers(row) for row in rows))
    active_karakas = tuple(sorted(set(definition.karakas).intersection(direct_carriers)))
    if active_karakas:
        return tuple(rows), {
            "method": "natural_karaka",
            "planets": active_karakas,
            "description": (
                f"{', '.join(active_karakas)} identifies the {subject} in the "
                "same delivered combination."
            ),
        }

    for anchor in by_house.get(definition.anchor_house, ()):
        expanded = tuple(rows) if any(anchor is row for row in rows) else (*rows, anchor)
        if not all(_same_dasha(expanded[0], row) for row in expanded[1:]):
            continue
        if _overlap(expanded) is None or _carrier_coherence(expanded) is None:
            continue
        return expanded, {
            "method": "anchor_house",
            "native_house": definition.anchor_house,
            "description": (
                f"Native House {definition.anchor_house}, the chart anchor for "
                f"{subject}, is active in the same delivery chain."
            ),
        }
    return None


def _reason_key(reason: Mapping[str, object]) -> Tuple[str, str, str]:
    return (
        str(reason.get("planet") or ""),
        str(reason.get("rule_id") or ""),
        str(reason.get("independent_key") or ""),
    )


def _merge_reasons(
    rows: Sequence[HouseActivation], attribute: str
) -> Tuple[Dict[str, object], ...]:
    merged: List[Dict[str, object]] = []
    seen = set()
    for row in rows:
        for raw in getattr(row.outcome, attribute):
            reason = dict(raw)
            reason.setdefault("house", row.house)
            key = _reason_key(reason)
            if key in seen:
                continue
            seen.add(key)
            merged.append(reason)
    return tuple(merged)


def _connection_text(row: HouseActivation) -> Tuple[str, ...]:
    grouped: Dict[Tuple[str, str], Set[str]] = {}
    for connection in row.natal_connections:
        planet = str(connection.get("planet") or "")
        relation = str(connection.get("relation") or "").replace("_", " ")
        level = str(connection.get("level") or "")
        if planet and relation:
            grouped.setdefault((planet, relation), set()).add(level)
    level_order = {"MD": 0, "AD": 1, "PD": 2}
    return tuple(
        (
            f"{planet} connects through natal {relation}"
            f" ({' and '.join(sorted(levels, key=level_order.get))})"
        )
        for (planet, relation), levels in grouped.items()
    )


def _transit_text(row: HouseActivation) -> Tuple[str, ...]:
    descriptions = []
    for connection in row.transit_connections:
        if not connection.get("timing_trigger"):
            continue
        planet = str(connection.get("planet") or "")
        source = connection.get("transit_house")
        relations = tuple(connection.get("relations") or ())
        relation_text = " and ".join(
            "occupies this house" if relation == "occupation"
            else "aspects this house"
            for relation in relations
        )
        if planet and relation_text:
            descriptions.append(
                f"Transit {planet} from House {source} {relation_text}"
            )
    return tuple(dict.fromkeys(descriptions))


def _tone_reason(
    rows: Sequence[HouseActivation],
    focus_native_houses: Set[int],
    tone: Polarity,
) -> str:
    house_tones = "; ".join(
        f"House {row.house} is {row.outcome.tone.value}"
        for row in rows
    )
    if tone == Polarity.CHALLENGING:
        pressured_focus = sorted(
            row.house
            for row in rows
            if row.house in focus_native_houses
            and row.outcome.tone == Polarity.CHALLENGING
        )
        conclusion = (
            f"Pressure in {' and '.join(f'House {house}' for house in pressured_focus)} "
            "cannot be cancelled by a more supportive companion house."
        )
    elif tone == Polarity.MIXED:
        conclusion = (
            "The houses do not point in one direction, so the combined result "
            "remains mixed rather than being forced positive or negative."
        )
    elif tone == Polarity.SUPPORTIVE:
        conclusion = "The houses describing the main outcome are supportive."
    else:
        conclusion = "The available factors do not establish a clear result direction."
    return f"{house_tones}. {conclusion}"


def _combined_tone(
    rows: Sequence[HouseActivation],
    focus_native_houses: Set[int],
) -> Polarity:
    focus_tones = {
        row.outcome.tone for row in rows if row.house in focus_native_houses
    }
    all_tones = {row.outcome.tone for row in rows}
    # The event-defining house is the weakest link. Its pressure may be
    # qualified by supporting houses, but never averaged into a supportive
    # result.
    if Polarity.CHALLENGING in focus_tones:
        return Polarity.CHALLENGING
    if Polarity.MIXED in focus_tones:
        return Polarity.MIXED
    if Polarity.CHALLENGING in all_tones or Polarity.MIXED in all_tones:
        return Polarity.MIXED
    if all_tones == {Polarity.SUPPORTIVE}:
        return Polarity.SUPPORTIVE
    if Polarity.SUPPORTIVE in all_tones:
        return Polarity.MIXED
    return Polarity.NEUTRAL


def _strength_score(
    rows: Sequence[HouseActivation],
    coherence: str,
    as_of: date,
    overlap: Tuple[date, date],
) -> int:
    score = 50
    score += 16 if coherence == "shared_direct_carrier" else 10
    score += 12 if all(
        row.state == HouseActivationState.FULLY_REINFORCED for row in rows
    ) else 6
    score += 6 if all(
        row.activation.band == ActivationBand.STRONG for row in rows
    ) else 2
    score += 5 if overlap[0] <= as_of <= overlap[1] else 0
    score += min(6, len(set.intersection(*[
        set(row.trigger_planets) for row in rows
    ])) * 3)
    return max(0, min(95, score))


def _window(rows: Sequence[HouseActivation], overlap: Tuple[date, date]) -> PredictionWindow:
    seed = rows[0].window
    digest = hashlib.sha256(
        "|".join(sorted(row.window.transit_signature for row in rows)).encode("utf-8")
    ).hexdigest()[:20]
    return PredictionWindow(
        start_date=overlap[0].isoformat(),
        end_date=overlap[1].isoformat(),
        mahadasha=seed.mahadasha,
        antardasha=seed.antardasha,
        pratyantardasha=seed.pratyantardasha,
        transit_signature=digest,
    )


class ChartManifestationResolver:
    """Resolve coherent chart-level manifestations from delivered houses.

    This layer never invents event vocabulary. It matches a versioned registry,
    requires timing overlap and direct-carrier coherence, and preserves bounded
    alternatives where a house combination cannot select one concrete event.
    """

    version = CHART_MANIFESTATION_RESOLVER_VERSION
    registry_version = CHART_MANIFESTATION_REGISTRY_VERSION

    def resolve(
        self,
        request: PredictionRequest,
        activations: Sequence[HouseActivation],
        *,
        maximum_results: int = 8,
    ) -> Tuple[ChartManifestation, ...]:
        eligible = [row for row in activations if row.state in _ELIGIBLE_STATES]
        by_house: Dict[int, List[HouseActivation]] = {}
        for row in eligible:
            by_house.setdefault(row.house, []).append(row)

        resolved: List[Tuple[int, ChartManifestation]] = []
        for signature in MANIFESTATION_SIGNATURES:
            if request.domains and signature.domain not in set(request.domains):
                # Existing clients historically use "wealth" for finance.
                if not (
                    signature.domain == "finance"
                    and "wealth" in set(request.domains)
                ):
                    continue
            for subject in request.subjects:
                native_houses = tuple(
                    native_houses_for_subject(
                        subject, signature.required_relative_houses
                    )
                )
                if any(house not in by_house for house in native_houses):
                    continue
                for selected in product(*(by_house[house] for house in native_houses)):
                    rows = tuple(selected)
                    if not all(_same_dasha(rows[0], row) for row in rows[1:]):
                        continue
                    subject_lock = _subject_lock(subject, rows, by_house)
                    if subject_lock is None:
                        continue
                    coherence_rows, subject_confirmation = subject_lock
                    overlap = _overlap(coherence_rows)
                    if overlap is None:
                        continue
                    coherent = _carrier_coherence(coherence_rows)
                    if coherent is None:
                        continue
                    coherence, carriers, relationships = coherent
                    focus_native = set(native_houses_for_subject(
                        subject, signature.focus_relative_houses
                    ))
                    tone = _combined_tone(rows, focus_native)
                    band = (
                        ActivationBand.STRONG
                        if all(row.activation.band == ActivationBand.STRONG for row in rows)
                        else ActivationBand.MODERATE
                    )
                    score = _strength_score(rows, coherence, request.as_of, overlap)
                    roles = tuple(
                        ManifestationHouseRole(
                            native_house=native_house,
                            relative_house=relative_house,
                            role=signature.role_by_relative_house[relative_house],
                            activation_state=row.state,
                            activation_band=row.activation.band,
                            outcome_tone=row.outcome.tone,
                            direct_carriers=tuple(sorted(_direct_carriers(row))),
                            dasha_connections=_connection_text(row),
                            transit_connections=_transit_text(row),
                        )
                        for relative_house, native_house, row in zip(
                            signature.required_relative_houses,
                            native_houses,
                            rows,
                        )
                    )
                    tone_reading = COMBINATION_TONE_READINGS[signature.key][tone]
                    possibilities = _bounded_possibilities(signature.key, tone)
                    timing = _window(rows, overlap)
                    manifestation_id = hashlib.sha256(
                        (
                            f"{signature.key}|{subject}|{timing.start_date}|"
                            f"{timing.end_date}|{timing.mahadasha}|"
                            f"{timing.antardasha}|{timing.pratyantardasha}|"
                            f"{','.join(map(str, native_houses))}|{','.join(carriers)}|"
                            f"{CHART_MANIFESTATION_RESOLVER_VERSION}"
                        ).encode("utf-8")
                    ).hexdigest()[:32]
                    rationale_rows = [
                        (
                            f"Houses {', '.join(map(str, native_houses))} are active "
                            f"together from {timing.start_date} to {timing.end_date} "
                            f"during {timing.mahadasha} MD, {timing.antardasha} AD "
                            f"and {timing.pratyantardasha} PD."
                        ),
                        (
                            f"{', '.join(carriers)} has a direct natal connection "
                            "to every house in this combination."
                            if coherence == "shared_direct_carrier"
                            else (
                                f"The planets connecting these houses—{', '.join(carriers)}—"
                                "have a natal relationship with one another."
                            )
                        ),
                        _tone_reason(rows, focus_native, tone),
                    ]
                    if subject != "self":
                        rationale_rows.insert(2, str(subject_confirmation["description"]))
                    rationale = tuple(rationale_rows)
                    result = ChartManifestation(
                        manifestation_id=manifestation_id,
                        signature_key=signature.key,
                        subject=subject,
                        domain=signature.domain,
                        label=signature.label,
                        window=timing,
                        house_roles=roles,
                        subject_confirmation=subject_confirmation,
                        carrier_planets=carriers,
                        carrier_coherence=coherence,
                        carrier_relationships=relationships,
                        activation_band=band,
                        outcome_tone=tone,
                        synthesis_strength=(
                            "high" if score >= 85
                            else "well_supported" if score >= 70
                            else "moderate"
                        ),
                        summary=tone_reading,
                        possibilities=possibilities,
                        helpful_reasons=_merge_reasons(rows, "supportive_reasons"),
                        pressure_reasons=_merge_reasons(rows, "challenging_reasons"),
                        mixed_reasons=_merge_reasons(rows, "mixed_reasons"),
                        rationale=rationale,
                        rule_id="registry_signature_with_coherent_dasha_carriers",
                    )
                    rank = (
                        0 if overlap[0] <= request.as_of <= overlap[1] else 1,
                        -score,
                        signature.priority,
                    )
                    resolved.append((rank, result))

        # A merged activation can create identical cards through adjacent source
        # windows. Keep the strongest semantic result per subject and period.
        best: Dict[Tuple[str, str], Tuple[Tuple[int, int, int], ChartManifestation]] = {}
        for rank, item in resolved:
            key = (item.signature_key, item.subject)
            if key not in best or rank < best[key][0]:
                best[key] = (rank, item)
        ordered = sorted(best.values(), key=lambda pair: pair[0])
        diverse: List[ChartManifestation] = []
        semantic_frames = set()
        for _, item in ordered:
            frame_key = (
                item.signature_key,
                tuple(sorted(role.native_house for role in item.house_roles)),
                item.window.start_date,
                item.window.end_date,
                item.outcome_tone,
            )
            if frame_key in semantic_frames:
                continue
            semantic_frames.add(frame_key)
            diverse.append(item)
            if len(diverse) >= maximum_results:
                break
        return tuple(diverse)
