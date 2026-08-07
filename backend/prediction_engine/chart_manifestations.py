from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from itertools import product
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

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
from .event_signatures import EVENT_SIGNATURES, EventSignature
from .subjects import SUBJECTS, native_houses_for_subject


CHART_MANIFESTATION_RESOLVER_VERSION = "2.0.0"
CHART_MANIFESTATION_REGISTRY_VERSION = "2.0.0"


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


@dataclass(frozen=True)
class _SemanticMatch:
    signature: EventSignature
    subject: str
    rows: Tuple[HouseActivation, ...]
    required_native_houses: Tuple[int, ...]
    supporting_native_houses: Tuple[int, ...]
    conflict_native_houses: Tuple[int, ...]
    subject_confirmation: Dict[str, object]
    overlap: Tuple[date, date]
    coherence: str
    carriers: Tuple[str, ...]
    relationships: Tuple[Dict[str, object], ...]
    score: int


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
    for evidence in row.evidence:
        if evidence.provider != "transit_nakshatra_ledger":
            continue
        natal = evidence.facts.get("natal_nakshatra") or {}
        transit = evidence.facts.get("transit_nakshatra") or {}
        lord = evidence.facts.get("common_nakshatra_lord")
        if evidence.rule_id == "dasha_planet_exact_natal_nakshatra_return":
            descriptions.append(
                f"Transit {evidence.planet} returns to its natal nakshatra "
                f"{natal.get('name')}, giving strong timing confirmation"
            )
        elif evidence.rule_id == "dasha_planet_nakshatra_dispositor_resonance":
            relevance = (
                " and its common lord is relevant to this house"
                if evidence.facts.get("nakshatra_lord_relevant")
                else ""
            )
            expression = evidence.facts.get("nakshatra_lord_expression")
            qualification = (
                "; the natal condition of that lord is strained"
                if expression == "strained"
                else (
                    "; the natal condition of that lord is clear"
                    if expression == "clear" else ""
                )
            )
            descriptions.append(
                f"Transit {evidence.planet} in {transit.get('name')} repeats "
                f"its natal nakshatra lord {lord} from {natal.get('name')}"
                f"{relevance}{qualification}; this is secondary confirmation, "
                "not direct contact"
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
    start = overlap[0].isoformat()
    end = overlap[1].isoformat()
    opened_by = seed.opened_by
    closed_by = seed.closed_by
    for row in rows:
        if row.window.start_date == start and row.window.opened_by:
            opened_by = row.window.opened_by
            break
    for row in rows:
        if row.window.end_date == end and row.window.closed_by:
            closed_by = row.window.closed_by
            break
    return PredictionWindow(
        start_date=start,
        end_date=end,
        mahadasha=seed.mahadasha,
        antardasha=seed.antardasha,
        pratyantardasha=seed.pratyantardasha,
        transit_signature=digest,
        opened_by=opened_by,
        closed_by=closed_by,
    )


_EVENT_DOMAIN: Dict[str, str] = {
    "career_authority": "career",
    "money_gains": "finance",
    "financial_pressure": "finance",
    "partnership_commitment": "relationship",
    "home_property": "property",
    "children_education": "education",
    "travel_change": "travel",
    "workload_health": "health",
    "shared_resources_change": "finance",
    "family_responsibility": "family",
    "decision_communication": "decisions",
}

_DOMAIN_LABELS: Dict[str, str] = {
    "career": "career",
    "finance": "finances",
    "relationship": "partnership",
    "property": "property",
    "education": "education or children",
    "travel": "travel",
    "health": "health and obligations",
    "family": "family responsibilities",
    "decisions": "decisions and agreements",
}

_CLUSTER_HOUSE_ROLES: Dict[int, str] = {
    1: "the person, body, vitality and capacity to act",
    2: "savings, family resources, speech and what can fund or absorb the development",
    3: "initiative, communication, documents and movement",
    4: "home, residence, property, mother and emotional foundation",
    5: "children, learning, judgment, creativity and considered risk",
    6: "health, workload, debt, service, competition or an obstacle to manage",
    7: "spouse, partner, agreement, counterparty or public dealing",
    8: "joint resources, tax, insurance, inheritance, vulnerability or consequential adjustment",
    9: "father, guidance, higher learning, fortune or long-distance opportunity",
    10: "career, authority, status and visible responsibility",
    11: "income, gain, recognition, network and the result being pursued",
    12: "expense, distance, foreign connection, release or withdrawal",
}


def _event_signature_allowed(
    signature: EventSignature,
    request: PredictionRequest,
) -> bool:
    life = request.life_context
    if signature.eligibility_rule == "business_owner":
        return life is None or life.business_owner is not False
    if signature.eligibility_rule == "has_children":
        return life is None or life.has_children is not False
    return True


def _row_identity(row: HouseActivation) -> Tuple[object, ...]:
    return (
        row.house,
        row.window.start_date,
        row.window.end_date,
        row.window.mahadasha,
        row.window.antardasha,
        row.window.pratyantardasha,
        row.window.transit_signature,
    )


def _unique_rows(rows: Iterable[HouseActivation]) -> Tuple[HouseActivation, ...]:
    unique: Dict[Tuple[object, ...], HouseActivation] = {}
    for row in rows:
        unique.setdefault(_row_identity(row), row)
    return tuple(unique.values())


def _timing_coherent_selections(
    houses: Sequence[int],
    by_house: Mapping[int, Sequence[HouseActivation]],
) -> Iterable[Tuple[HouseActivation, ...]]:
    """Avoid the cross-window Cartesian product for required houses.

    Nakshatra-accurate timing can create many short windows. Anchor every
    selection to one row, then admit only rows in the same dasha chain with a
    real timing overlap before taking the much smaller product.
    """

    if not houses:
        return
    anchor_house, *other_houses = houses
    for anchor in by_house.get(anchor_house, ()):
        compatible: List[Tuple[HouseActivation, ...]] = []
        for house in other_houses:
            rows = tuple(
                row for row in by_house.get(house, ())
                if _same_dasha(anchor, row)
                and _overlap((anchor, row)) is not None
            )
            if not rows:
                break
            compatible.append(rows)
        else:
            if compatible:
                yield from (
                    (anchor, *selection)
                    for selection in product(*compatible)
                )
            else:
                yield (anchor,)


def _semantic_matches(
    request: PredictionRequest,
    by_house: Mapping[int, Sequence[HouseActivation]],
) -> Tuple[_SemanticMatch, ...]:
    matches: List[_SemanticMatch] = []
    for signature in EVENT_SIGNATURES.values():
        if not signature.safety_allowed or not _event_signature_allowed(signature, request):
            continue
        domain = _EVENT_DOMAIN.get(signature.parent_family, signature.parent_family)
        if request.domains and domain not in set(request.domains):
            if not (domain == "finance" and "wealth" in set(request.domains)):
                continue
        for subject in request.subjects:
            required = tuple(native_houses_for_subject(
                subject, signature.required_relative_houses
            ))
            if any(house not in by_house for house in required):
                continue
            supporting_map = dict(zip(
                native_houses_for_subject(subject, signature.supporting_relative_houses),
                signature.supporting_relative_houses,
            ))
            conflict_map = dict(zip(
                native_houses_for_subject(subject, signature.conflict_relative_houses),
                signature.conflict_relative_houses,
            ))
            optional_houses = tuple(dict.fromkeys(
                house
                for house in (*supporting_map, *conflict_map)
                if house not in required and house in by_house
            ))
            for required_selected in _timing_coherent_selections(
                required, by_house
            ):
                base_rows = _unique_rows(required_selected)
                if not base_rows or not all(
                    _same_dasha(base_rows[0], row) for row in base_rows[1:]
                ):
                    continue
                if _overlap(base_rows) is None:
                    continue
                optional_choices: List[Sequence[Optional[HouseActivation]]] = []
                for house in optional_houses:
                    compatible_rows = tuple(
                        row for row in by_house[house]
                        if _same_dasha(base_rows[0], row)
                        and _overlap((*base_rows, row)) is not None
                    )
                    optional_choices.append((None, *compatible_rows))
                selections = (
                    product(*optional_choices)
                    if optional_choices
                    else ((),)
                )
                for optional_selected in selections:
                    rows = _unique_rows((
                        *base_rows,
                        *(row for row in optional_selected if row is not None),
                    ))
                    selected_houses = {row.house for row in rows}
                    supporting = tuple(sorted(
                        selected_houses.intersection(supporting_map)
                    ))
                    if len(supporting) < signature.minimum_supporting_houses:
                        continue
                    subject_lock = _subject_lock(subject, rows, by_house)
                    if subject_lock is None:
                        continue
                    coherence_rows, subject_confirmation = subject_lock
                    overlap = _overlap(coherence_rows)
                    coherent = _carrier_coherence(coherence_rows)
                    if overlap is None or coherent is None:
                        continue
                    coherence, carriers, relationships = coherent
                    score = _strength_score(rows, coherence, request.as_of, overlap)
                    matches.append(_SemanticMatch(
                        signature=signature,
                        subject=subject,
                        rows=rows,
                        required_native_houses=tuple(sorted(required)),
                        supporting_native_houses=supporting,
                        conflict_native_houses=tuple(sorted(
                            selected_houses.intersection(conflict_map)
                        )),
                        subject_confirmation=subject_confirmation,
                        overlap=overlap,
                        coherence=coherence,
                        carriers=carriers,
                        relationships=relationships,
                        score=score,
                    ))

    # Optional houses refine a theme. For the same signature and timing chain,
    # retain the widest coherent reading rather than emitting every subset.
    best: Dict[Tuple[object, ...], _SemanticMatch] = {}
    for match in matches:
        first = match.rows[0]
        required_row_key = tuple(sorted(
            _row_identity(row)
            for row in match.rows
            if row.house in set(match.required_native_houses)
        ))
        key = (
            match.signature.key,
            match.subject,
            first.window.mahadasha,
            first.window.antardasha,
            first.window.pratyantardasha,
            required_row_key,
        )
        current = best.get(key)
        candidate_rank = (
            len(match.rows),
            match.score,
            len(match.supporting_native_houses),
            -len(match.conflict_native_houses),
        )
        current_rank = (
            len(current.rows),
            current.score,
            len(current.supporting_native_houses),
            -len(current.conflict_native_houses),
        ) if current else None
        if current is None or candidate_rank > current_rank:
            best[key] = match
    return tuple(best.values())


def _cluster_is_valid(
    subject: str,
    matches: Sequence[_SemanticMatch],
    by_house: Mapping[int, Sequence[HouseActivation]],
) -> bool:
    rows = _unique_rows(row for match in matches for row in match.rows)
    if not rows or not all(_same_dasha(rows[0], row) for row in rows[1:]):
        return False
    subject_lock = _subject_lock(subject, rows, by_house)
    if subject_lock is None:
        return False
    coherence_rows, _ = subject_lock
    return _overlap(coherence_rows) is not None and _carrier_coherence(coherence_rows) is not None


def _semantic_clusters(
    matches: Sequence[_SemanticMatch],
    by_house: Mapping[int, Sequence[HouseActivation]],
) -> Tuple[Tuple[_SemanticMatch, ...], ...]:
    # House activations are emitted on common deterministic timing windows.
    # Themes from different windows can never form one simultaneous event, so
    # cluster within a timing bucket instead of repeatedly comparing every
    # future match with every other future match.
    buckets: Dict[Tuple[object, ...], List[_SemanticMatch]] = {}
    for match in matches:
        first = match.rows[0]
        key = (
            match.subject,
            first.window.mahadasha,
            first.window.antardasha,
            first.window.pratyantardasha,
            match.overlap,
        )
        buckets.setdefault(key, []).append(match)

    all_clusters: List[List[_SemanticMatch]] = []
    for bucket_matches in buckets.values():
        clusters: List[List[_SemanticMatch]] = [
            [match] for match in bucket_matches
        ]
        while True:
            merge_options = []
            for left_index in range(len(clusters)):
                for right_index in range(left_index + 1, len(clusters)):
                    left = clusters[left_index]
                    right = clusters[right_index]
                    left_houses = {
                        row.house for item in left for row in item.rows
                    }
                    right_houses = {
                        row.house for item in right for row in item.rows
                    }
                    shared = left_houses.intersection(right_houses)
                    if not shared:
                        continue
                    combined_rows: List[_SemanticMatch] = []
                    combined_seen = set()
                    for item in (*left, *right):
                        item_key = (
                            item.signature.key,
                            item.subject,
                            tuple(_row_identity(row) for row in item.rows),
                        )
                        if item_key not in combined_seen:
                            combined_seen.add(item_key)
                            combined_rows.append(item)
                    combined = tuple(combined_rows)
                    if not _cluster_is_valid(
                        left[0].subject, combined, by_house
                    ):
                        continue
                    merge_options.append((
                        len(left_houses.union(right_houses)),
                        len(shared),
                        len(combined),
                        -left_index,
                        -right_index,
                        left_index,
                        right_index,
                        combined,
                    ))
            if not merge_options:
                break
            *_, left_index, right_index, combined = max(merge_options)
            clusters[left_index] = list(combined)
            del clusters[right_index]
        all_clusters.extend(clusters)

    output = []
    seen = set()
    for cluster in all_clusters:
        houses = tuple(sorted({row.house for item in cluster for row in item.rows}))
        if len(houses) < 2:
            continue
        key = (
            cluster[0].subject,
            houses,
            tuple(sorted({item.signature.key for item in cluster})),
            min(item.overlap[0] for item in cluster),
            max(item.overlap[1] for item in cluster),
        )
        if key not in seen:
            seen.add(key)
            output.append(tuple(cluster))
    return tuple(output)


def _cluster_label(matches: Sequence[_SemanticMatch]) -> str:
    domains = tuple(dict.fromkeys(
        _DOMAIN_LABELS.get(
            _EVENT_DOMAIN.get(match.signature.parent_family, match.signature.parent_family),
            match.signature.parent_family.replace("_", " "),
        )
        for match in matches
    ))
    if len(domains) == 1:
        return f"{domains[0]} matters become interconnected"
    if len(domains) == 2:
        joined = f"{domains[0]} and {domains[1]}"
    else:
        joined = f"{', '.join(domains[:-1])} and {domains[-1]}"
    return f"{joined} become interconnected"


def _semantic_cluster_manifestation(
    request: PredictionRequest,
    matches: Sequence[_SemanticMatch],
    by_house: Mapping[int, Sequence[HouseActivation]],
) -> Tuple[Tuple[int, int, int], ChartManifestation] | None:
    subject = matches[0].subject
    rows = _unique_rows(row for match in matches for row in match.rows)
    subject_lock = _subject_lock(subject, rows, by_house)
    if subject_lock is None:
        return None
    coherence_rows, subject_confirmation = subject_lock
    overlap = _overlap(coherence_rows)
    coherent = _carrier_coherence(coherence_rows)
    if overlap is None or coherent is None:
        return None
    coherence, carriers, relationships = coherent
    representative_by_house: Dict[int, HouseActivation] = {}
    for row in rows:
        current = representative_by_house.get(row.house)
        row_rank = (
            1 if row.state == HouseActivationState.FULLY_REINFORCED else 0,
            1 if row.activation.band == ActivationBand.STRONG else 0,
            row.activation.independent_confirmations,
        )
        current_rank = (
            1 if current.state == HouseActivationState.FULLY_REINFORCED else 0,
            1 if current.activation.band == ActivationBand.STRONG else 0,
            current.activation.independent_confirmations,
        ) if current else None
        if current is None or row_rank > current_rank:
            representative_by_house[row.house] = row
    display_rows = tuple(
        representative_by_house[house]
        for house in sorted(representative_by_house)
    )
    required_native = {
        house for match in matches for house in match.required_native_houses
    }
    supporting_native = {
        house for match in matches for house in match.supporting_native_houses
    }
    conflict_native = {
        house for match in matches for house in match.conflict_native_houses
    }
    tone = _combined_tone(rows, required_native)
    score = _strength_score(rows, coherence, request.as_of, overlap)
    timing = _window(rows, overlap)
    anchor = SUBJECTS[subject].anchor_house
    roles = []
    for row in display_rows:
        relative_house = ((row.house - anchor) % 12) + 1
        role = _CLUSTER_HOUSE_ROLES[relative_house]
        if row.house in conflict_native and row.house not in required_native:
            role = (
                f"{role}; here it modifies or counterbalances one of the "
                "possible themes, according to its own outcome condition"
            )
        roles.append(ManifestationHouseRole(
            native_house=row.house,
            relative_house=relative_house,
            role=role,
            activation_state=row.state,
            activation_band=row.activation.band,
            outcome_tone=row.outcome.tone,
            direct_carriers=tuple(sorted(_direct_carriers(row))),
            dasha_connections=_connection_text(row),
            transit_connections=_transit_text(row),
        ))

    theme_rows = []
    possibilities_by_theme: List[Tuple[str, ...]] = []
    for match in sorted(matches, key=lambda item: (item.signature.priority, item.signature.key)):
        native_houses = tuple(sorted({row.house for row in match.rows}))
        theme_rows.append({
            "key": match.signature.key,
            "label": match.signature.label,
            "domain": _EVENT_DOMAIN.get(
                match.signature.parent_family, match.signature.parent_family
            ),
            "native_houses": native_houses,
            "required_native_houses": match.required_native_houses,
            "supporting_native_houses": match.supporting_native_houses,
            "modifying_native_houses": match.conflict_native_houses,
            "required_varga": match.signature.required_varga,
        })
        possibilities_by_theme.append(tuple(match.signature.manifestations))
    theme_rows = list({
        row["key"]: row for row in theme_rows
    }.values())
    possibility_topics = []
    max_theme_possibilities = max(
        (len(topics) for topics in possibilities_by_theme),
        default=0,
    )
    for index in range(max_theme_possibilities):
        for topics in possibilities_by_theme:
            if index < len(topics) and topics[index] not in possibility_topics:
                possibility_topics.append(topics[index])
    possibilities = tuple(
        f"{topic[:1].upper()}{topic[1:]}."
        for topic in possibility_topics[:8]
    )
    domains = tuple(dict.fromkeys(row["domain"] for row in theme_rows))
    house_text = ", ".join(f"House {row.house}" for row in display_rows)
    cycle = (
        f"{timing.mahadasha}–{timing.antardasha}–{timing.pratyantardasha}"
    )
    direction = {
        Polarity.SUPPORTIVE: "The connected houses lean constructive overall.",
        Polarity.MIXED: "Some parts can progress while others require adjustment, expense or patience.",
        Polarity.CHALLENGING: "Pressure or consequential adjustment dominates the connected matters.",
        Polarity.NEUTRAL: "The direction remains open, although the connected matters are active.",
    }[tone]
    summary = (
        f"The same {cycle} delivery connects {house_text}. {direction} "
        "The chart identifies a connected field of possibilities, not one guaranteed event."
    )
    signature_keys = tuple(sorted(row["key"] for row in theme_rows))
    signature_key = "cluster:" + "+".join(signature_keys)
    manifestation_id = hashlib.sha256(
        (
            f"{signature_key}|{subject}|{timing.start_date}|{timing.end_date}|"
            f"{','.join(str(row.house) for row in display_rows)}|"
            f"{','.join(carriers)}|{CHART_MANIFESTATION_RESOLVER_VERSION}"
        ).encode("utf-8")
    ).hexdigest()[:32]
    theme_labels = ", ".join(row["label"] for row in theme_rows)
    rationale = (
        (
            f"{house_text} overlap from {timing.start_date} to {timing.end_date} "
            f"in the same {cycle} period."
        ),
        (
            f"The registered Parashari themes that connect them are: {theme_labels}."
        ),
        (
            f"{', '.join(carriers)} connects the complete house cluster directly."
            if coherence == "shared_direct_carrier"
            else (
                f"The delivering planets—{', '.join(carriers)}—form one connected "
                "natal relationship chain across the cluster."
            )
        ),
        _tone_reason(rows, required_native, tone),
    )
    result = ChartManifestation(
        manifestation_id=manifestation_id,
        signature_key=signature_key,
        subject=subject,
        domain=domains[0] if len(domains) == 1 else "combined",
        label=_cluster_label(matches),
        window=timing,
        house_roles=tuple(roles),
        subject_confirmation=subject_confirmation,
        carrier_planets=carriers,
        carrier_coherence=coherence,
        carrier_relationships=relationships,
        activation_band=(
            ActivationBand.STRONG
            if all(row.activation.band == ActivationBand.STRONG for row in display_rows)
            else ActivationBand.MODERATE
        ),
        outcome_tone=tone,
        synthesis_strength=(
            "high" if score >= 85
            else "well_supported" if score >= 70
            else "moderate"
        ),
        summary=summary,
        possibilities=possibilities,
        helpful_reasons=_merge_reasons(rows, "supportive_reasons"),
        pressure_reasons=_merge_reasons(rows, "challenging_reasons"),
        mixed_reasons=_merge_reasons(rows, "mixed_reasons"),
        rationale=rationale,
        rule_id="semantic_event_signature_graph_cluster",
        constituent_themes=tuple(theme_rows),
    )
    rank = (
        0 if overlap[0] <= request.as_of <= overlap[1] else 1,
        -score,
        -len(display_rows),
    )
    return rank, result


class ChartManifestationResolver:
    """Resolve coherent chart-level manifestations from delivered houses.

    This layer never invents event vocabulary. It matches versioned Parashari
    event signatures, requires timing overlap and direct-carrier coherence,
    then joins overlapping signatures into a connected house graph. Bounded
    alternatives are preserved because a coherent house cluster still cannot
    select one guaranteed concrete event.
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
                for selected in _timing_coherent_selections(
                    native_houses, by_house
                ):
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

        semantic_matches = _semantic_matches(request, by_house)
        semantic_clusters = _semantic_clusters(semantic_matches, by_house)
        cluster_results = []
        for cluster in semantic_clusters:
            built = _semantic_cluster_manifestation(request, cluster, by_house)
            if built is not None:
                _, cluster_item = built
                cluster_houses = {
                    role.native_house for role in cluster_item.house_roles
                }
                duplicates_atomic_pair = (
                    len(cluster_houses) == 2
                    and any(
                        existing.subject == cluster_item.subject
                        and {
                            role.native_house for role in existing.house_roles
                        } == cluster_houses
                        for _, existing in resolved
                    )
                )
                if not duplicates_atomic_pair:
                    cluster_results.append(built)
        resolved.extend(cluster_results)

        # A merged activation can create identical cards through adjacent source
        # windows. Keep the strongest semantic result per subject and period.
        best: Dict[Tuple[str, str], Tuple[Tuple[int, int, int], ChartManifestation]] = {}
        for rank, item in resolved:
            key = (item.signature_key, item.subject)
            if key not in best or rank < best[key][0]:
                best[key] = (rank, item)
        ordered = sorted(best.values(), key=lambda pair: pair[0])
        cluster_items = [
            item for _, item in ordered
            if item.rule_id == "semantic_event_signature_graph_cluster"
            and len(item.house_roles) >= 3
        ]
        ordered = [
            (rank, item)
            for rank, item in ordered
            if item.rule_id == "semantic_event_signature_graph_cluster"
            or not any(
                (
                    cluster.subject == item.subject
                    or (
                        cluster.subject == "self"
                        and item.subject != "self"
                        and SUBJECTS[item.subject].anchor_house
                            in {role.native_house for role in cluster.house_roles}
                    )
                )
                and {role.native_house for role in item.house_roles}.issubset(
                    {role.native_house for role in cluster.house_roles}
                )
                and date.fromisoformat(cluster.window.start_date)
                    <= date.fromisoformat(item.window.end_date)
                and date.fromisoformat(item.window.start_date)
                    <= date.fromisoformat(cluster.window.end_date)
                for cluster in cluster_items
            )
        ]
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
