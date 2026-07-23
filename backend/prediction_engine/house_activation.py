from __future__ import annotations

"""House-first Parashari activation ledger.

This module deliberately does not name events.  It establishes what can be
said before an event vocabulary is consulted: the natal connections of the
running dasha lords, cooperation within MD/AD/PD, and transit triggers.  A
transit-only house remains visible in the ledger but cannot become an event.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from calculators.badhaka_calculator import BadhakaCalculator

from .context import CalculationContext
from .contracts import (
    ActivationAssessment,
    ActivationBand,
    DashaRelationship,
    Evidence,
    EvidenceStatus,
    HouseActivation,
    HouseActivationState,
    Importance,
    OutcomeAssessment,
    Polarity,
    PredictionWindow,
)
from .primitives import CLASSICAL_PLANETS, aspected_houses, ruled_houses


HOUSE_ACTIVATION_POLICY_VERSION = "4.0.0"

# Slow transits are allowed to reinforce timing even when the planet is not a
# dasha lord.  Faster planets are retained as short triggers only when they are
# themselves in the active dasha chain.
TIMING_TRANSIT_TRIGGERS = frozenset({"Sun", "Jupiter", "Saturn", "Rahu", "Ketu"})
DASHA_LEVEL_ORDER = {"MD": 0, "AD": 1, "PD": 2}


def _dignity_polarity(dignity: str) -> Polarity:
    if dignity in {"exalted", "moolatrikona", "own_sign"}:
        return Polarity.SUPPORTIVE
    if dignity == "debilitated":
        return Polarity.CHALLENGING
    return Polarity.NEUTRAL


@dataclass(frozen=True)
class _NatalConnection:
    level: str
    planet: str
    relation: str


def _house_lord(chart: Dict[str, Any], house: int) -> str:
    sign = int(chart["houses"][house - 1]["sign"])
    return str(BadhakaCalculator.SIGN_LORDS[sign])


def _dasha_levels(window: PredictionWindow) -> Tuple[Tuple[str, str], ...]:
    return (
        ("MD", window.mahadasha),
        ("AD", window.antardasha),
        ("PD", window.pratyantardasha),
    )


def _planet_relations_to_house(
    chart: Dict[str, Any], planet: str, house: int
) -> Tuple[str, ...]:
    natal = chart["planets"][planet]
    relations: List[str] = []
    if house in ruled_houses(chart, planet):
        relations.append("lordship")
    if int(natal["house"]) == house:
        relations.append("occupation")
    if house in aspected_houses(planet, int(natal["house"])):
        relations.append("aspect")
    return tuple(relations)


def _pair_relationship(
    chart: Dict[str, Any],
    first_level: str,
    first_planet: str,
    second_level: str,
    second_planet: str,
) -> DashaRelationship:
    first = chart["planets"][first_planet]
    second = chart["planets"][second_planet]
    relations: List[str] = []
    houses: Set[int] = {int(first["house"]), int(second["house"])}

    if first_planet == second_planet:
        relations.append("same_planet_repeated_in_dasha_chain")
    else:
        if int(first["house"]) == int(second["house"]):
            relations.append("natal_conjunction")
        if int(second["house"]) in aspected_houses(first_planet, int(first["house"])):
            relations.append("first_aspects_second")
        if int(first["house"]) in aspected_houses(second_planet, int(second["house"])):
            relations.append("second_aspects_first")

        first_dispositor = BadhakaCalculator.SIGN_LORDS[int(first["sign"])]
        second_dispositor = BadhakaCalculator.SIGN_LORDS[int(second["sign"])]
        if first_dispositor == second_planet:
            relations.append("first_disposed_by_second")
        if second_dispositor == first_planet:
            relations.append("second_disposed_by_first")
        if (
            first_dispositor == second_planet
            and second_dispositor == first_planet
        ):
            relations.append("sign_exchange")

    return DashaRelationship(
        first_level=first_level,
        first_planet=first_planet,
        second_level=second_level,
        second_planet=second_planet,
        relations=tuple(dict.fromkeys(relations)),
        natal_houses=tuple(sorted(houses)),
    )


def dasha_relationships(
    chart: Dict[str, Any], window: PredictionWindow
) -> Tuple[DashaRelationship, ...]:
    levels = _dasha_levels(window)
    return tuple(
        _pair_relationship(chart, *levels[first], *levels[second])
        for first, second in ((0, 1), (0, 2), (1, 2))
    )


def _connected_planets(
    relationships: Sequence[DashaRelationship], direct_planets: Set[str]
) -> Set[str]:
    connected = set(direct_planets)
    changed = True
    while changed:
        changed = False
        for row in relationships:
            if not row.relations:
                continue
            pair = {row.first_planet, row.second_planet}
            if connected.intersection(pair) and not pair.issubset(connected):
                connected.update(pair)
                changed = True
    return connected


def _transit_aspects_natal(
    transit_planet: str,
    transit_house: int,
    natal_house: int,
) -> bool:
    return natal_house == transit_house or natal_house in aspected_houses(
        transit_planet, transit_house
    )


def _evidence(
    *,
    window: PredictionWindow,
    provider: str,
    rule_id: str,
    planet: str | None,
    house: int,
    importance: Importance,
    polarity: Polarity = Polarity.NEUTRAL,
    facts: Dict[str, Any],
    key: str,
) -> Evidence:
    return Evidence(
        provider=provider,
        provider_version=HOUSE_ACTIVATION_POLICY_VERSION,
        rule_id=rule_id,
        status=EvidenceStatus.EVALUATED,
        subject="self",
        domain="house_activation",
        window_start=window.start_date,
        window_end=window.end_date,
        planet=planet,
        house=house,
        importance=importance,
        polarity=polarity,
        facts=facts,
        independent_key=key,
    )


def _condition_evidence(
    calculation: CalculationContext,
    window: PredictionWindow,
    house: int,
    carrier_planets: Iterable[str],
) -> List[Evidence]:
    """Use only conditions whose directional meaning is stable in this profile.

    Natural benefic/malefic status and retrogression are intentionally not
    converted into good/bad votes: their result depends on ownership, context,
    and the event being judged.  Node dignity is also omitted because the
    exaltation/ownership convention is not universal.
    """

    levels_by_planet: Dict[str, List[str]] = {}
    for level, planet in _dasha_levels(window):
        levels_by_planet.setdefault(planet, []).append(level)

    output: List[Evidence] = []
    for planet in sorted(set(carrier_planets)):
        condition = calculation.natal_dignities.get(planet, {})
        dignity = str(condition.get("dignity") or "neutral")
        if planet not in {"Rahu", "Ketu"}:
            polarity = _dignity_polarity(dignity)
            output.append(_evidence(
                window=window,
                provider="house_condition",
                rule_id="carrier_natal_dignity",
                planet=planet,
                house=house,
                importance=Importance.PRIMARY,
                polarity=polarity,
                facts={"dasha_levels": levels_by_planet.get(planet, []), "dignity": dignity},
                key=f"house-condition:dignity:{planet}:{dignity}",
            ))
        combustion = str(condition.get("combustion_status") or "normal")
        if combustion == "cazimi":
            combustion = "combust"
        if combustion != "normal":
            output.append(_evidence(
                window=window,
                provider="house_condition",
                rule_id="carrier_natal_combustion",
                planet=planet,
                house=house,
                importance=Importance.PRIMARY,
                polarity=Polarity.CHALLENGING,
                facts={"dasha_levels": levels_by_planet.get(planet, []), "combustion": combustion},
                key=f"house-condition:combustion:{planet}",
            ))
    return output


def weighted_outcome(
    evidence: Sequence[Evidence], carrier_planets: Iterable[str]
) -> OutcomeAssessment:
    """Produce one directional assessment per planet.

    Natural nature, functional lordship, dignity and special statuses are
    ingredients of a planet's result, not independent events. Friendship is
    retained as an explanatory modifier and does not create a positive or
    negative vote. Correlated Avayogi/Dagdha/Tithi-Shunya rows are capped as
    one special-status contribution per planet.
    """

    carriers = set(carrier_planets)
    weights = {
        Importance.PRIMARY: 1.5,
        Importance.SECONDARY: 0.75,
        Importance.CONFIRMATORY: 0.5,
    }
    modifier_rules = {
        "fivefold_friendship_with_house_lord",
        "fivefold_friendship_with_nakshatra_lord",
        "compound_friendship_with_event_house_lord",
    }
    correlated_special_rules = {
        "avayogi_lord",
        "dagdha_rashi_lord",
        "tithi_shunya_lord",
        "planet_in_dagdha_rashi",
        "planet_in_tithi_shunya_rashi",
        "avayogi_lord_active",
        "planet_in_dagdha_rashi",
        "planet_in_tithi_shunya_rashi",
    }
    rows_by_planet: Dict[str, List[Evidence]] = {}
    seen_keys: Set[str] = set()
    for row in evidence:
        if (
            row.planet not in carriers
            and row.provider != "natal_house_promise"
        ) or not row.independent_key or row.independent_key in seen_keys:
            continue
        seen_keys.add(row.independent_key)
        rows_by_planet.setdefault(row.planet or "House", []).append(row)

    supportive = 0.0
    challenging = 0.0
    supportive_reasons: List[Dict[str, Any]] = []
    challenging_reasons: List[Dict[str, Any]] = []
    mixed_reasons: List[Dict[str, Any]] = []
    for planet, rows in sorted(rows_by_planet.items()):
        planet_support = 0.0
        planet_challenge = 0.0
        special_support = 0.0
        special_challenge = 0.0
        special_components: List[Dict[str, Any]] = []
        components: List[Dict[str, Any]] = []
        for row in rows:
            base_weight = weights[row.importance] * float(row.facts.get("weight", 1.0))
            is_modifier = row.rule_id in modifier_rules
            component_weight = 0.0 if is_modifier else base_weight
            support_part = (
                component_weight * (0.5 if row.polarity == Polarity.MIXED else 1.0)
                if row.polarity in {Polarity.SUPPORTIVE, Polarity.MIXED} else 0.0
            )
            challenge_part = (
                component_weight * (0.5 if row.polarity == Polarity.MIXED else 1.0)
                if row.polarity in {Polarity.CHALLENGING, Polarity.MIXED} else 0.0
            )
            if row.rule_id in correlated_special_rules:
                special_support = max(special_support, support_part)
                special_challenge = max(special_challenge, challenge_part)
                special_components.append(_outcome_reason(row, support_part + challenge_part))
            else:
                planet_support += support_part
                planet_challenge += challenge_part
                component = _outcome_reason(row, support_part + challenge_part)
                component["is_modifier"] = is_modifier
                components.append(component)

        planet_support += special_support
        planet_challenge += special_challenge
        if special_components:
            special_polarity = (
                Polarity.MIXED if special_support > 0 and special_challenge > 0
                else Polarity.SUPPORTIVE if special_support > 0
                else Polarity.CHALLENGING
            )
            components.append({
                "provider": "natal_house_promise",
                "rule_id": "combined_special_status",
                "planet": planet,
                "house": next((item.get("house") for item in special_components if item.get("house") is not None), None),
                "importance": Importance.CONFIRMATORY.value,
                "polarity": special_polarity.value,
                "contribution_weight": round(special_support + special_challenge, 3),
                "facts": {
                    "statuses": tuple({
                        "rule_id": item["rule_id"],
                        "polarity": item["polarity"],
                        "facts": item["facts"],
                    } for item in special_components),
                    "avayogi_tithi_shunya_overlap": any(
                        bool(item["facts"].get("avayogi_tithi_shunya_overlap") or item["facts"].get("avayogi_overlap"))
                        for item in special_components
                    ),
                },
                "independent_key": f"combined-special-status:{planet}",
                "is_modifier": False,
            })
        if planet_support <= 0 and planet_challenge <= 0:
            continue
        supportive += planet_support
        challenging += planet_challenge
        if planet_support > 0 and planet_challenge > 0:
            polarity = Polarity.MIXED
            target = mixed_reasons
        elif planet_support > 0:
            polarity = Polarity.SUPPORTIVE
            target = supportive_reasons
        else:
            polarity = Polarity.CHALLENGING
            target = challenging_reasons
        target.append({
            "provider": "planet_composite",
            "rule_id": "planet_composite_outcome",
            "planet": planet,
            "house": next((row.house for row in rows if row.house is not None), None),
            "importance": max(rows, key=lambda row: weights[row.importance]).importance.value,
            "polarity": polarity.value,
            "supportive_weight": round(planet_support, 3),
            "challenging_weight": round(planet_challenge, 3),
            "contribution_weight": round(planet_support + planet_challenge, 3),
            "facts": {"component_count": len(components)},
            "independent_key": f"planet-composite:{planet}",
            "components": tuple(components),
        })

    total = supportive + challenging
    if total == 0:
        tone = Polarity.NEUTRAL
        rule = "insufficient_validated_directional_strength_evidence"
    elif supportive >= challenging * 1.6:
        tone = Polarity.SUPPORTIVE
        rule = "weighted_supportive_strength_predominates"
    elif challenging >= supportive * 1.6:
        tone = Polarity.CHALLENGING
        rule = "weighted_challenging_strength_predominates"
    else:
        tone = Polarity.MIXED
        rule = "weighted_strength_is_materially_mixed"
    return OutcomeAssessment(
        tone=tone,
        supportive_factors=len(supportive_reasons),
        challenging_factors=len(challenging_reasons),
        rule_id=rule,
        mixed_factors=len(mixed_reasons),
        supportive_reasons=tuple(supportive_reasons),
        challenging_reasons=tuple(challenging_reasons),
        mixed_reasons=tuple(mixed_reasons),
    )


def _outcome_reason(row: Evidence, contribution_weight: float) -> Dict[str, Any]:
    """Expose every distinct factor that actually contributed to the tone."""

    return {
        "provider": row.provider,
        "rule_id": row.rule_id,
        "planet": row.planet,
        "house": row.house,
        "importance": row.importance.value,
        "polarity": row.polarity.value,
        "contribution_weight": round(contribution_weight, 3),
        "facts": dict(row.facts),
        "independent_key": row.independent_key,
    }


def _moon_short_triggers(
    calculation: CalculationContext,
    window: PredictionWindow,
    house: int,
    carrier_planets: Iterable[str],
) -> Tuple[Dict[str, Any], ...]:
    """Return lunar peak bands without allowing Moon to create an event.

    A peak requires the transiting Moon to contact both the already activated
    house and at least one natal delivery carrier on the same sampled day.
    """

    carriers = set(carrier_planets)
    if not carriers or not calculation.daily_transit_states:
        return ()
    carrier_houses = {
        planet: int(calculation.chart["planets"][planet]["house"])
        for planet in carriers
    }
    hits: List[Dict[str, Any]] = []
    current = date.fromisoformat(window.start_date)
    end = date.fromisoformat(window.end_date)
    while current <= end:
        moon = calculation.daily_transit_states.get(current.isoformat(), {}).get("Moon")
        if moon:
            moon_house = int(moon["house"])
            house_relations = []
            if moon_house == house:
                house_relations.append("occupation")
            if house in aspected_houses("Moon", moon_house):
                house_relations.append("aspect")
            contacted_carriers = tuple(sorted(
                planet for planet, natal_house in carrier_houses.items()
                if natal_house == moon_house
                or natal_house in aspected_houses("Moon", moon_house)
            ))
            if house_relations and contacted_carriers:
                hits.append({
                    "date": current.isoformat(),
                    "moon_house": moon_house,
                    "house_relations": tuple(house_relations),
                    "natal_carriers_contacted": contacted_carriers,
                })
        current += timedelta(days=1)

    bands: List[Dict[str, Any]] = []
    for hit in hits:
        if (
            bands
            and date.fromisoformat(bands[-1]["end_date"]) + timedelta(days=1)
            == date.fromisoformat(hit["date"])
            and bands[-1]["moon_house"] == hit["moon_house"]
            and bands[-1]["house_relations"] == hit["house_relations"]
            and bands[-1]["natal_carriers_contacted"]
            == hit["natal_carriers_contacted"]
        ):
            bands[-1]["end_date"] = hit["date"]
        else:
            bands.append({
                "kind": "moon_peak",
                "start_date": hit["date"],
                "end_date": hit["date"],
                "moon_house": hit["moon_house"],
                "house_relations": hit["house_relations"],
                "natal_carriers_contacted": hit["natal_carriers_contacted"],
                "creates_event": False,
            })
    return tuple(bands)


class HouseActivationEngine:
    version = HOUSE_ACTIVATION_POLICY_VERSION

    def evaluate_window(
        self, calculation: CalculationContext, window: PredictionWindow
    ) -> Tuple[HouseActivation, ...]:
        chart = calculation.chart
        levels = _dasha_levels(window)
        relationships = dasha_relationships(chart, window)
        transit_states = calculation.transit_states_by_signature[
            window.transit_signature
        ]
        dasha_planets = {planet for _, planet in levels}
        transit_trigger_set = dasha_planets | set(TIMING_TRANSIT_TRIGGERS)
        results: List[HouseActivation] = []

        for house in range(1, 13):
            evidence: List[Evidence] = []
            natal_connections: List[_NatalConnection] = []
            for level, planet in levels:
                for relation in _planet_relations_to_house(chart, planet, house):
                    connection = _NatalConnection(level, planet, relation)
                    natal_connections.append(connection)
                    evidence.append(_evidence(
                        window=window,
                        provider="natal_dasha_house",
                        rule_id=f"dasha_planet_{relation}_house",
                        planet=planet,
                        house=house,
                        importance=Importance.PRIMARY,
                        facts={"dasha_level": level, "relation": relation},
                        key=f"natal-dasha:{level}:{planet}:{relation}:{house}",
                    ))

            direct_planets = {row.planet for row in natal_connections}
            connected_planets = _connected_planets(relationships, direct_planets)
            active_levels = {
                level for level, planet in levels if planet in connected_planets
            }
            direct_subperiod = any(
                row.level in {"AD", "PD"} for row in natal_connections
            )
            cooperative_subperiod = any(
                level in {"AD", "PD"} and planet in connected_planets
                for level, planet in levels
            )
            deliverable = bool(natal_connections) and (
                direct_subperiod or cooperative_subperiod
            )

            relevant_relationships = tuple(
                row for row in relationships
                if row.relations and {row.first_planet, row.second_planet}.intersection(
                    connected_planets
                )
            )
            for row in relevant_relationships:
                evidence.append(_evidence(
                    window=window,
                    provider="dasha_relationship",
                    rule_id="md_ad_pd_natal_sambandha",
                    planet=None,
                    house=house,
                    importance=Importance.CONFIRMATORY,
                    facts={
                        "first_level": row.first_level,
                        "first_planet": row.first_planet,
                        "second_level": row.second_level,
                        "second_planet": row.second_planet,
                        "relations": list(row.relations),
                    },
                    key=(
                        f"dasha-relationship:{row.first_level}:{row.first_planet}:"
                        f"{row.second_level}:{row.second_planet}:"
                        f"{','.join(row.relations)}"
                    ),
                ))

            transit_connections: List[Dict[str, Any]] = []
            trigger_planets: Set[str] = set()
            self_natal_reinforcement_planets: Set[str] = set()
            for planet in CLASSICAL_PLANETS:
                transit = transit_states.get(planet)
                if transit is None:
                    continue
                transit_house = int(transit["house"])
                relations_to_house: List[str] = []
                if transit_house == house:
                    relations_to_house.append("occupation")
                if house in aspected_houses(planet, transit_house):
                    relations_to_house.append("aspect")
                if not relations_to_house:
                    continue

                is_timing_trigger = planet in transit_trigger_set
                transit_connections.append({
                    "planet": planet,
                    "relations": tuple(relations_to_house),
                    "transit_house": transit_house,
                    "timing_trigger": is_timing_trigger,
                    "dasha_planet": planet in dasha_planets,
                })
                if is_timing_trigger:
                    trigger_planets.add(planet)
                for relation in relations_to_house:
                    evidence.append(_evidence(
                        window=window,
                        provider="transit_house_ledger",
                        rule_id=f"transit_{relation}_house",
                        planet=planet,
                        house=house,
                        importance=(
                            Importance.PRIMARY
                            if planet in dasha_planets
                            else Importance.CONFIRMATORY
                        ),
                        facts={
                            "relation": relation,
                            "transit_house": transit_house,
                            "timing_trigger": is_timing_trigger,
                            "dasha_planet": planet in dasha_planets,
                        },
                        key=f"transit-house:{planet}:{relation}:{house}",
                    ))

                if is_timing_trigger and connected_planets:
                    for natal_planet in connected_planets:
                        natal_house = int(chart["planets"][natal_planet]["house"])
                        if _transit_aspects_natal(planet, transit_house, natal_house):
                            if planet == natal_planet:
                                self_natal_reinforcement_planets.add(planet)
                            evidence.append(_evidence(
                                window=window,
                                provider="transit_natal_ledger",
                                rule_id="timing_planet_contacts_natal_dasha_carrier",
                                planet=planet,
                                house=house,
                                importance=Importance.CONFIRMATORY,
                                facts={
                                    "natal_planet": natal_planet,
                                    "natal_house": natal_house,
                                    "transit_house": transit_house,
                                    "relation": (
                                        "conjunction"
                                        if transit_house == natal_house else "aspect"
                                    ),
                                    "same_planet_natal_repetition": planet == natal_planet,
                                },
                                key=(
                                    f"transit-natal:{planet}:{natal_planet}:"
                                    f"{transit_house}:{natal_house}"
                                ),
                            ))

            has_timing_transit = bool(trigger_planets)
            full_reinforcement_planets = (
                dasha_planets
                & trigger_planets
                & self_natal_reinforcement_planets
            )
            natal_relation_reinforcement = bool(full_reinforcement_planets)
            if deliverable and has_timing_transit and natal_relation_reinforcement:
                state = HouseActivationState.FULLY_REINFORCED
                band = ActivationBand.STRONG
                rule_id = "natal_dasha_delivery_transit_and_natal_contact"
            elif deliverable and has_timing_transit:
                state = HouseActivationState.DASHA_TRANSIT_ACTIVATED
                band = ActivationBand.MODERATE
                rule_id = "natal_dasha_delivery_with_transit_activation"
            elif natal_connections:
                state = HouseActivationState.DASHA_CONNECTED
                band = ActivationBand.MODERATE if deliverable else ActivationBand.INSUFFICIENT
                rule_id = (
                    "natal_house_connected_to_active_subperiod"
                    if deliverable else "mahadasha_only_or_unrelated_dasha_connection"
                )
            elif has_timing_transit:
                state = HouseActivationState.TRANSIT_ONLY
                band = ActivationBand.INSUFFICIENT
                rule_id = "transit_activation_without_current_dasha_natal_connection"
            else:
                state = HouseActivationState.DORMANT
                band = ActivationBand.INSUFFICIENT
                rule_id = "no_current_dasha_or_relevant_transit_activation"

            carrier_planets = connected_planets if natal_connections else set()
            promise = next(
                (row for row in calculation.natal_promises if int(row["house"]) == house),
                None,
            )
            if promise:
                for index, factor in enumerate(promise["factors"]):
                    evidence.append(_evidence(
                        window=window,
                        provider="natal_house_promise",
                        rule_id=str(factor["source"]),
                        planet=str(factor["planet"]),
                        house=house,
                        importance=(
                            Importance.PRIMARY
                            if factor["source"] == "house_lord_condition"
                            else Importance.SECONDARY
                            if factor["source"] in {
                                "occupant_natural_influence",
                                "occupant_functional_lordship",
                                "occupant_condition",
                                "final_dispositor_condition",
                            }
                            else Importance.CONFIRMATORY
                        ),
                        polarity=Polarity(str(factor["polarity"])),
                        facts={**dict(factor["facts"]), "weight": factor["weight"]},
                        key=f"natal-promise:{house}:{factor['source']}:{factor['planet']}:{index}",
                    ))
                for yoga in calculation.validated_yogas:
                    if (
                        house in set(yoga["houses"])
                        and carrier_planets.intersection(yoga["planets"])
                    ):
                        is_cancellation = str(yoga["key"]).startswith("neecha_bhanga:")
                        yoga_blocked = any(
                            (
                                str(calculation.natal_dignities.get(planet, {}).get(
                                    "dignity", "neutral"
                                )) == "debilitated"
                                and not any(
                                    cancellation.get("planet") == planet
                                    for promise_row in calculation.natal_promises
                                    for cancellation in promise_row.get("cancellations", ())
                                )
                            )
                            or str(calculation.natal_dignities.get(planet, {}).get(
                                "combustion_status", "normal"
                            )) not in {"normal", "cazimi"}
                            for planet in yoga["planets"]
                        )
                        evidence.append(_evidence(
                            window=window,
                            provider="natal_house_promise",
                            rule_id="activated_validated_yoga",
                            planet=next(iter(sorted(
                                carrier_planets.intersection(yoga["planets"])
                            )), None),
                            house=house,
                            importance=Importance.CONFIRMATORY,
                            polarity=(
                                Polarity.NEUTRAL if is_cancellation or yoga_blocked
                                else Polarity.SUPPORTIVE
                            ),
                            facts={
                                "yoga_key": yoga["key"],
                                "yoga_name": yoga["name"],
                                "yoga_planets": yoga["planets"],
                                "rule": yoga["rule"],
                                "direction_withheld_due_to_affliction": yoga_blocked,
                            },
                            key=f"natal-promise:yoga:{house}:{yoga['key']}",
                        ))
            evidence.extend(_condition_evidence(
                calculation, window, house, carrier_planets
            ))
            timing_triggers: List[Dict[str, Any]] = []
            sun_relations = tuple(
                relation
                for connection in transit_connections
                if connection["planet"] == "Sun" and connection["timing_trigger"]
                for relation in connection["relations"]
            )
            if sun_relations:
                timing_triggers.append({
                    "kind": "sun_reinforcement",
                    "start_date": window.start_date,
                    "end_date": window.end_date,
                    "house_relations": sun_relations,
                    "creates_event_without_dasha_promise": False,
                })
            timing_triggers.extend(_moon_short_triggers(
                calculation, window, house, carrier_planets
            ))
            for trigger in timing_triggers:
                if trigger["kind"] != "moon_peak":
                    continue
                evidence.append(_evidence(
                    window=window,
                    provider="moon_short_trigger",
                    rule_id="moon_contacts_activated_house_and_natal_carrier",
                    planet="Moon",
                    house=house,
                    importance=Importance.CONFIRMATORY,
                    polarity=Polarity.NEUTRAL,
                    facts=dict(trigger),
                    key=(
                        f"moon-peak:{house}:{trigger['start_date']}:"
                        f"{trigger['end_date']}:{trigger['moon_house']}"
                    ),
                ))
            outcome = weighted_outcome(evidence, carrier_planets)
            activation = ActivationAssessment(
                band=band,
                independent_confirmations=len({
                    row.independent_key for row in evidence if row.independent_key
                }),
                active_dasha_levels=tuple(sorted(active_levels, key=DASHA_LEVEL_ORDER.get)),
                transit_reinforced=has_timing_transit,
                natal_position_reinforced=natal_relation_reinforcement,
                primary_houses_covered=(house,) if natal_connections else (),
                carrier_planets=tuple(sorted(carrier_planets)),
                rule_id=rule_id,
            )
            results.append(HouseActivation(
                house=house,
                window=window,
                state=state,
                activation=activation,
                outcome=outcome,
                house_lord=_house_lord(chart, house),
                natal_connections=tuple({
                    "level": row.level,
                    "planet": row.planet,
                    "relation": row.relation,
                } for row in natal_connections),
                transit_connections=tuple(transit_connections),
                dasha_relationships=relevant_relationships,
                trigger_planets=tuple(sorted(trigger_planets)),
                timing_triggers=tuple(timing_triggers),
                evidence=tuple(evidence),
            ))
        return tuple(results)

    def evaluate(
        self, calculation: CalculationContext
    ) -> Tuple[HouseActivation, ...]:
        return tuple(
            activation
            for window in calculation.windows
            for activation in self.evaluate_window(calculation, window)
        )
