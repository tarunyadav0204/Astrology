"""Reversible natal-delivery and integrated support layers for Event Timeline V3.

This module does not create events. It judges whether an event already opened
by the V3 timing graph is promised, deliverable, obstructed, independently
confirmed, and temporally concentrated. Missing inputs remain explicit.
"""

from __future__ import annotations

import os
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple


ACCURACY_LAYER_VERSION = "event_timeline_integrated_support_v2"

SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
NAKSHATRA_LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
OWN_SIGNS = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
EXALTATION_SIGNS = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
DEBILITATION_SIGNS = {planet: (sign + 6) % 12 for planet, sign in EXALTATION_SIGNS.items()}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
KAKSHYA_RULERS = ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Ascendant")

EVENT_KARAKAS: Dict[str, Tuple[str, ...]] = {
    "job_change": ("Sun", "Saturn", "Mercury"),
    "promotion": ("Sun", "Jupiter", "Saturn"),
    "health": ("Sun", "Moon", "Mars"),
    "property_purchase": ("Mars", "Moon", "Venus"),
    "property_gain": ("Mars", "Moon", "Venus"),
    "vehicle_purchase": ("Venus", "Moon", "Mars"),
    "relocation": ("Moon", "Mars", "Rahu"),
    "marriage": ("Venus", "Jupiter"),
    "foreign_travel": ("Jupiter", "Rahu", "Saturn"),
    "children": ("Jupiter", "Sun"),
    "education": ("Mercury", "Jupiter"),
    "income_gain": ("Jupiter", "Venus", "Mercury"),
}


def _event_karakas(event_key: str) -> Tuple[str, ...]:
    if str(event_key).startswith("relative_health_"):
        return EVENT_KARAKAS["health"]
    return EVENT_KARAKAS.get(event_key, ())

# These houses describe friction or denial of a clean outcome. A house may
# still be part of the event's transition signature; it is never treated as
# proof that the event itself cannot occur.
EVENT_OBSTRUCTION_HOUSES: Dict[str, Set[int]] = {
    "job_change": {8, 12}, "promotion": {6, 8, 12}, "health": {8, 12},
    "property_purchase": {6, 8, 12}, "property_gain": {6, 8, 12},
    "vehicle_purchase": {6, 8, 12},
    "relocation": {6, 8}, "marriage": {1, 6, 10, 12},
    "foreign_travel": {6, 8}, "children": {1, 6, 10},
    "education": {6, 8, 12}, "income_gain": {6, 8, 12},
}


def accuracy_layer_mode() -> str:
    raw = str(os.getenv("EVENT_TIMELINE_V3_ACCURACY_LAYER") or "integrated_v2").strip().lower()
    if raw in {"legacy", "legacy_v3_6", "v3_6", "off"}:
        return "legacy_v3_6"
    if raw in {"delivery_v1", "v3_7"}:
        return "delivery_v1"
    return "integrated_v2"


def _planet_rows(context: Mapping[str, Any]) -> Mapping[str, Any]:
    return ((context.get("d1_chart") or {}).get("planets") or {})


def _house_lordships(ascendant_longitude: float) -> Dict[str, List[int]]:
    ascendant_sign = int(float(ascendant_longitude) / 30.0) % 12
    result: Dict[str, List[int]] = {}
    for house in range(1, 13):
        result.setdefault(SIGN_LORDS[(ascendant_sign + house - 1) % 12], []).append(house)
    return result


def _invert_lordships(lordships: Mapping[str, Sequence[int]]) -> Dict[int, str]:
    return {int(house): str(planet) for planet, houses in lordships.items() for house in houses}


def aspected_houses(planet: str, house: int) -> Set[int]:
    offsets = {
        "Saturn": (2, 6, 9), "Mars": (3, 6, 7), "Jupiter": (4, 6, 8),
        "Rahu": (6,), "Ketu": (6,),
    }.get(planet, (6,))
    return {((int(house) + offset - 1) % 12) + 1 for offset in offsets}


def dignity_for(planet: str, placement: Mapping[str, Any]) -> str:
    supplied = str(placement.get("dignity") or "").strip().lower()
    if supplied:
        return supplied
    try:
        sign = int(placement.get("sign")) % 12
    except (TypeError, ValueError):
        return "unavailable"
    if EXALTATION_SIGNS.get(planet) == sign:
        return "exalted"
    if DEBILITATION_SIGNS.get(planet) == sign:
        return "debilitated"
    if sign in OWN_SIGNS.get(planet, set()):
        return "own_sign"
    return "neutral"


def _longitude(placement: Mapping[str, Any]) -> float | None:
    try:
        return float(placement.get("longitude")) % 360.0
    except (TypeError, ValueError):
        return None


def angular_distance(one: float, two: float) -> float:
    return abs((one - two + 180.0) % 360.0 - 180.0)


def _aspect_orb(transit_longitude: float, target_longitude: float, aspect_number: int) -> float:
    projected = (float(transit_longitude) + (int(aspect_number) - 1) * 30.0) % 360.0
    return angular_distance(projected, float(target_longitude))


def _contact_windows(
    daily_by_planet: Mapping[str, Sequence[Mapping[str, Any]]],
    aspect_model: Mapping[str, Sequence[int]],
    targets: Sequence[Mapping[str, Any]],
    *,
    orb: float = 3.0,
) -> List[Dict[str, Any]]:
    active: Dict[Tuple[str, str, int], List[Dict[str, Any]]] = {}
    for transit_planet, raw_rows in daily_by_planet.items():
        rows = [row for row in raw_rows if row.get("longitude") is not None and _parse_day(row.get("date"))]
        aspects = [int(value) for value in (aspect_model.get(transit_planet) or (1, 7))]
        for target in targets:
            if target.get("longitude") is None:
                continue
            target_id = str(target.get("target_id") or target.get("name") or "target")
            for aspect_number in aspects:
                distances = [
                    _aspect_orb(float(row["longitude"]), float(target["longitude"]), aspect_number)
                    for row in rows
                ]
                for index, (row, distance) in enumerate(zip(rows, distances)):
                    if distance > orb:
                        continue
                    previous = distances[index - 1] if index > 0 else None
                    following = distances[index + 1] if index + 1 < len(distances) else None
                    if distance <= 0.25:
                        phase = "exact"
                    elif following is not None and following < distance:
                        phase = "applying"
                    elif previous is not None and previous < distance:
                        phase = "separating"
                    else:
                        phase = "stationary_or_boundary"
                    active.setdefault((str(transit_planet), target_id, aspect_number), []).append({
                        "date": str(row["date"]), "orb": round(distance, 4), "phase": phase,
                        "retrograde": bool(row.get("retrograde")), "longitude": row.get("longitude"),
                        "speed": row.get("speed"),
                    })
    windows: List[Dict[str, Any]] = []
    for (planet, target_id, aspect_number), rows in active.items():
        target = next(row for row in targets if str(row.get("target_id") or row.get("name") or "target") == target_id)
        groups: List[List[Dict[str, Any]]] = []
        for row in sorted(rows, key=lambda value: value["date"]):
            if (
                not groups
                or (_parse_day(row["date"]) - _parse_day(groups[-1][-1]["date"])).days > 1
                or row["retrograde"] != groups[-1][-1]["retrograde"]
            ):
                groups.append([row])
            else:
                groups[-1].append(row)
        for pass_index, group in enumerate(groups, start=1):
            peak = min(group, key=lambda value: value["orb"])
            windows.append({
                "transit_planet": planet,
                "target": target.get("name"),
                "target_type": target.get("target_type"),
                "target_houses": list(target.get("houses") or []),
                "aspect_number": aspect_number,
                "start_date": group[0]["date"],
                "end_date": group[-1]["date"],
                "peak_date": peak["date"],
                "peak_orb": peak["orb"],
                "peak_phase": peak["phase"],
                "phases": list(dict.fromkeys(row["phase"] for row in group)),
                "retrograde": peak["retrograde"],
                "pass_index": pass_index,
                "resolution": "calendar_day_sampled_longitude",
            })
    return sorted(windows, key=lambda row: (row["peak_date"], row["peak_orb"], row["transit_planet"], row["target"]))


def exact_transit_judgment(
    context: Mapping[str, Any],
    graph: Mapping[str, Any],
    kp: Mapping[str, Any],
    event_key: str,
    event_houses: Set[int],
    anchor_houses: Set[int],
    carriers: Sequence[str],
) -> Dict[str, Any]:
    daily = graph.get("transit_daily") if isinstance(graph.get("transit_daily"), Mapping) else {}
    aspect_model = graph.get("transit_aspect_model") if isinstance(graph.get("transit_aspect_model"), Mapping) else {}
    if not daily:
        return {
            "available": False, "event_contacts": [], "reference_contacts": [],
            "kp_cusp_contacts": [], "stations": [],
            "limitations": ["daily transit longitudes unavailable"],
        }
    planets = _planet_rows(context)
    lordships = context.get("house_lordships") or {}
    event_lords = {
        planet for planet, houses in lordships.items()
        if set(int(house) for house in houses) & event_houses
    }
    target_planets = event_lords | set(_event_karakas(event_key))
    targets: List[Dict[str, Any]] = []
    for planet in sorted(target_planets):
        longitude = _longitude(planets.get(planet) or {})
        if longitude is not None:
            targets.append({
                "target_id": f"natal:{planet}", "name": planet,
                "target_type": "event_lord_or_karaka", "longitude": longitude,
                "houses": list(lordships.get(planet) or []),
            })
    reference_targets: List[Dict[str, Any]] = []
    moon_longitude = _longitude(planets.get("Moon") or {})
    if moon_longitude is not None:
        reference_targets.append({
            "target_id": "reference:Moon", "name": "Moon", "target_type": "moon_reference",
            "longitude": moon_longitude, "houses": [],
        })
    ascendant = (context.get("d1_chart") or {}).get("ascendant")
    if ascendant is not None:
        reference_targets.append({
            "target_id": "reference:Lagna", "name": "Lagna", "target_type": "lagna_reference",
            "longitude": float(ascendant), "houses": [1],
        })
    house_cusps = kp.get("house_cusps") if isinstance(kp.get("house_cusps"), Mapping) else {}
    kp_targets = [
        {
            "target_id": f"kp_cusp:{house}", "name": f"KP cusp {house}",
            "target_type": "kp_anchor_cusp", "longitude": float(house_cusps.get(house, house_cusps.get(str(house)))),
            "houses": [house],
        }
        for house in sorted(anchor_houses)
        if house_cusps.get(house, house_cusps.get(str(house))) is not None
    ]
    relevant_transit_planets = set(carriers) | {"Jupiter", "Saturn"} | set(_event_karakas(event_key))
    relevant_daily = {planet: rows for planet, rows in daily.items() if planet in relevant_transit_planets}
    event_contacts = _contact_windows(relevant_daily, aspect_model, targets)
    reference_contacts = _contact_windows(relevant_daily, aspect_model, reference_targets)
    kp_contacts = _contact_windows(relevant_daily, aspect_model, kp_targets, orb=1.0)
    # The Moon may also be an event karaka/lord. Keep its event contact once in
    # event_contacts and its reference contact once here; never add both to a score.
    return {
        "available": True,
        "event_contacts": event_contacts,
        "reference_contacts": reference_contacts,
        "kp_cusp_contacts": kp_contacts,
        "stations": [
            row for row in (graph.get("transit_stations") or [])
            if row.get("planet") in relevant_transit_planets
        ],
        "event_targets": [row["name"] for row in targets],
        "transit_planets_evaluated": sorted(relevant_daily),
        "resolution": "calendar_day_sampled_longitude",
        "limitations": ["peak dates are daily samples; intraday exact roots are not solved"],
    }


def conjunctions_for(planet: str, planets: Mapping[str, Any], orb: float = 8.0) -> List[Dict[str, Any]]:
    source = _longitude(planets.get(planet) or {})
    if source is None:
        return []
    hits = []
    for other, placement in planets.items():
        if other == planet:
            continue
        target = _longitude(placement or {})
        if target is None:
            continue
        distance = angular_distance(source, target)
        if distance <= orb:
            hits.append({"planet": other, "orb": round(distance, 3)})
    return sorted(hits, key=lambda row: (row["orb"], row["planet"]))


def node_chain(planet: str, context: Mapping[str, Any], event_houses: Set[int]) -> Dict[str, Any]:
    planets = _planet_rows(context)
    placement = planets.get(planet) or {}
    if planet not in {"Rahu", "Ketu"} or not placement:
        return {"planet": planet, "available": False, "reason": "not_a_node_or_placement_unavailable"}
    longitude = _longitude(placement)
    if longitude is None:
        return {"planet": planet, "available": False, "reason": "longitude_unavailable"}
    sign = int(longitude / 30.0) % 12
    dispositor = SIGN_LORDS[sign]
    nakshatra_index = int(longitude / (360.0 / 27.0)) % 27
    nakshatra_lord = NAKSHATRA_LORDS[nakshatra_index % 9]
    dispositor_row = planets.get(dispositor) or {}
    nakshatra_row = planets.get(nakshatra_lord) or {}
    dispositor_links = sorted(
        ({int(dispositor_row.get("house") or 0)} | aspected_houses(dispositor, int(dispositor_row.get("house") or 1)))
        & event_houses
    ) if dispositor_row.get("house") else []
    nakshatra_links = sorted(
        ({int(nakshatra_row.get("house") or 0)} | aspected_houses(nakshatra_lord, int(nakshatra_row.get("house") or 1)))
        & event_houses
    ) if nakshatra_row.get("house") else []
    return {
        "planet": planet,
        "available": True,
        "occupied_house": placement.get("house"),
        "dispositor": dispositor,
        "dispositor_event_links": dispositor_links,
        "nakshatra_lord": nakshatra_lord,
        "nakshatra_lord_event_links": nakshatra_links,
        "conjunctions": conjunctions_for(planet, planets),
        "doctrine": "occupation_dispositor_nakshatra_conjunction_seventh_aspect_no_node_lordship",
    }


def natal_promise(
    event_key: str,
    anchor_houses: Set[int],
    transition_houses: Set[int],
    outcome_houses: Set[int],
    context: Mapping[str, Any],
) -> Dict[str, Any]:
    d1 = context.get("d1_chart") or {}
    planets = d1.get("planets") or {}
    if not planets or d1.get("ascendant") is None:
        return {"verdict": "unavailable", "score": 0, "reasons": [], "limitations": ["D1 placements unavailable"]}
    lordships = context.get("house_lordships") or _house_lordships(float(d1.get("ascendant") or 0.0))
    house_lords = _invert_lordships(lordships)
    event_houses = anchor_houses | transition_houses | outcome_houses
    anchor_lords = {house_lords[house] for house in anchor_houses if house in house_lords}
    transition_lords = {house_lords[house] for house in transition_houses if house in house_lords}
    outcome_lords = {house_lords[house] for house in outcome_houses if house in house_lords}
    relevant_lords = anchor_lords | transition_lords | outcome_lords
    reasons: List[str] = []
    score = 0
    direct_links: List[Dict[str, Any]] = []
    for planet in sorted(relevant_lords):
        placement = planets.get(planet) or {}
        try:
            house = int(placement.get("house"))
        except (TypeError, ValueError):
            continue
        linked = sorted(({house} | aspected_houses(planet, house)) & event_houses)
        if house in event_houses:
            score += 3
            reasons.append(f"{planet}, an event-house lord, occupies H{house}")
        elif linked:
            score += 1
            reasons.append(f"{planet}, an event-house lord, aspects event houses {linked}")
        direct_links.append({"planet": planet, "house": house, "event_links": linked, "dignity": dignity_for(planet, placement)})
    exchanges: List[Dict[str, Any]] = []
    relationship_links: List[Dict[str, Any]] = []
    for planet in sorted(relevant_lords):
        placement = planets.get(planet) or {}
        try:
            occupied_sign = int(placement.get("sign"))
        except (TypeError, ValueError):
            continue
        dispositor = SIGN_LORDS[occupied_sign % 12]
        if dispositor in relevant_lords and dispositor != planet:
            relationship_links.append({"planets": [planet, dispositor], "mechanism": "dispositor"})
            score += 1
        other = planets.get(dispositor) or {}
        try:
            other_sign = int(other.get("sign"))
        except (TypeError, ValueError):
            continue
        if SIGN_LORDS[other_sign % 12] == planet and planet != dispositor:
            identity = tuple(sorted((planet, dispositor)))
            if all(tuple(row["planets"]) != identity for row in exchanges):
                exchanges.append({"planets": list(identity)})
                score += 3
                reasons.append(f"{identity[0]} and {identity[1]} exchange signs across the event-lord network")
    for planet in sorted(relevant_lords):
        for conjunction in conjunctions_for(planet, planets):
            other = str(conjunction.get("planet") or "")
            if other not in relevant_lords or other <= planet:
                continue
            relationship_links.append({
                "planets": [planet, other],
                "mechanism": "conjunction",
                "orb": conjunction.get("orb"),
            })
            score += 2
            reasons.append(f"event-house lords {planet} and {other} are conjunct")
    karaka_links: List[Dict[str, Any]] = []
    for karaka in _event_karakas(event_key):
        placement = planets.get(karaka) or {}
        try:
            house = int(placement.get("house"))
        except (TypeError, ValueError):
            continue
        links = sorted(({house} | aspected_houses(karaka, house)) & event_houses)
        if house in anchor_houses:
            score += 3
            reasons.append(f"event karaka {karaka} occupies anchor H{house}")
        elif links:
            score += 1
        karaka_links.append({"planet": karaka, "house": house, "event_links": links, "dignity": dignity_for(karaka, placement)})
    moon = planets.get("Moon") or {}
    moon_repetition: List[Dict[str, Any]] = []
    try:
        moon_sign = int(moon.get("sign"))
    except (TypeError, ValueError):
        moon_sign = None
    if moon_sign is not None:
        for planet in sorted(relevant_lords | set(_event_karakas(event_key))):
            placement = planets.get(planet) or {}
            try:
                relative_house = ((int(placement.get("sign")) - moon_sign) % 12) + 1
            except (TypeError, ValueError):
                continue
            if relative_house in event_houses:
                moon_repetition.append({"planet": planet, "house_from_moon": relative_house})
        if moon_repetition:
            score += min(3, len(moon_repetition))
            reasons.append("the event signature repeats from the Moon reference")
    verdict = "strong" if score >= 12 else "available" if score >= 7 else "weak"
    return {
        "verdict": verdict,
        "score": score,
        "anchor_lords": sorted(anchor_lords),
        "transition_lords": sorted(transition_lords),
        "outcome_lords": sorted(outcome_lords),
        "karakas": list(_event_karakas(event_key)),
        "lord_links": direct_links,
        "karaka_links": karaka_links,
        "exchanges": exchanges,
        "relationship_links": relationship_links,
        "moon_repetition": moon_repetition,
        "reasons": reasons,
        "limitations": ["combustion and Shadbala unavailable in the minimal context"],
    }


def planet_delivery(
    event_key: str,
    carriers: Sequence[str],
    event_houses: Set[int],
    context: Mapping[str, Any],
) -> Dict[str, Any]:
    d1 = context.get("d1_chart") or {}
    planets = d1.get("planets") or {}
    lordships = context.get("house_lordships") or {}
    obstruction = EVENT_OBSTRUCTION_HOUSES.get(event_key, set())
    rows: List[Dict[str, Any]] = []
    supportive = 0
    pressure = 0
    for planet in carriers:
        placement = planets.get(planet) or {}
        if not placement:
            rows.append({"planet": planet, "available": False})
            continue
        house = int(placement.get("house") or 0)
        links = sorted((set(lordships.get(planet) or []) | {house} | aspected_houses(planet, house or 1)) & event_houses)
        obstructing_links = sorted((set(lordships.get(planet) or []) | {house} | aspected_houses(planet, house or 1)) & obstruction)
        dignity = dignity_for(planet, placement)
        dignity_score = 2 if dignity in {"exalted", "moolatrikona", "own_sign"} else -2 if dignity == "debilitated" else 0
        direct = sorted((set(lordships.get(planet) or []) | {house}) & event_houses)
        carrier_support = (3 if direct else 1 if links else 0) + dignity_score
        carrier_pressure = min(3, len(obstructing_links)) + (2 if dignity == "debilitated" else 0)
        supportive += max(0, carrier_support)
        pressure += carrier_pressure
        dispositor = None
        dispositor_links: List[int] = []
        longitude = _longitude(placement)
        if longitude is not None:
            dispositor = SIGN_LORDS[int(longitude / 30.0) % 12]
            drow = planets.get(dispositor) or {}
            if drow.get("house"):
                dhouse = int(drow["house"])
                dispositor_links = sorted(({dhouse} | aspected_houses(dispositor, dhouse)) & event_houses)
                if dispositor_links:
                    supportive += 1
        rows.append({
            "planet": planet,
            "available": True,
            "house": house,
            "lordships": list(lordships.get(planet) or []),
            "event_links": links,
            "direct_event_links": direct,
            "obstruction_links": obstructing_links,
            "dignity": dignity,
            "retrograde": bool(placement.get("retrograde")),
            "dispositor": dispositor,
            "dispositor_event_links": dispositor_links,
            "conjunctions": conjunctions_for(planet, planets),
            "node_chain": node_chain(planet, context, event_houses) if planet in {"Rahu", "Ketu"} else None,
            "combustion": "unavailable",
            "shadbala": "unavailable",
        })
    linked_sets = [set(row.get("event_links") or []) for row in rows if row.get("available")]
    shared_houses = sorted(set.intersection(*linked_sets)) if len(linked_sets) >= 2 and all(linked_sets) else []
    if shared_houses:
        supportive += 2
    if not any(row.get("available") for row in rows):
        verdict = "unavailable"
    elif pressure >= supportive + 3:
        verdict = "obstructed"
    elif pressure >= supportive:
        verdict = "mixed"
    else:
        verdict = "supportive"
    return {
        "verdict": verdict,
        "support_score": supportive,
        "pressure_score": pressure,
        "shared_event_houses": shared_houses,
        "carriers": rows,
        "limitations": ["combustion, planetary war, and Shadbala not supplied by the minimal context"],
    }


def obstruction_profile(event_key: str, graph: Mapping[str, Any], outcome_houses: Set[int]) -> Dict[str, Any]:
    houses = graph.get("houses") or {}
    obstruction_houses = EVENT_OBSTRUCTION_HOUSES.get(event_key, set())
    active: List[Dict[str, Any]] = []
    strength = 0
    for house in sorted(obstruction_houses):
        row = houses.get(str(house)) or {}
        if not row:
            continue
        dasha_direct = [c for c in row.get("dasha_channels") or [] if c.get("mechanism") in {"natal_lordship", "natal_occupation"}]
        transit_direct = [c for c in row.get("transit_channels") or [] if c.get("mechanism") == "transit_occupation"]
        row_strength = (2 if dasha_direct else 1 if row.get("dasha_channels") else 0) + (2 if transit_direct else 1 if row.get("transit_channels") else 0)
        strength += row_strength
        active.append({"house": house, "strength": row_strength, "dasha_direct": bool(dasha_direct), "transit_direct": bool(transit_direct)})
    outcome_active = sum(1 for house in outcome_houses if houses.get(str(house)))
    verdict = "high" if strength >= 8 and not outcome_active else "moderate" if strength >= 4 else "low"
    return {"verdict": verdict, "score": strength, "active_houses": active, "outcome_house_count": outcome_active}


def varga_judgment(
    context: Mapping[str, Any],
    varga: str,
    varga_key: str | None,
    event_key: str,
    event_houses: Set[int],
    carriers: Sequence[str],
    d1_promise: Mapping[str, Any],
    d1_delivery: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    raw = ((context.get("divisional_charts") or {}).get(varga_key) or {}) if varga_key else {}
    chart = raw.get("divisional_chart", raw) if isinstance(raw, Mapping) else {}
    planets = chart.get("planets") if isinstance(chart, Mapping) else {}
    if not planets or chart.get("ascendant") is None:
        return {"chart": varga, "verdict": "unavailable", "available": False, "confirmed": False, "carrier_hits": []}
    lordships = _house_lordships(float(chart.get("ascendant") or 0.0))
    house_lords = _invert_lordships(lordships)
    relevant_lords = {house_lords[house] for house in event_houses if house in house_lords}
    ascendant_lord = house_lords.get(1)
    ascendant_lord_judgment: Dict[str, Any] = {"planet": ascendant_lord, "available": False}
    if ascendant_lord and (planets.get(ascendant_lord) or {}).get("house"):
        ascendant_row = planets[ascendant_lord]
        ascendant_house = int(ascendant_row["house"])
        ascendant_links = sorted(
            ({ascendant_house} | set(lordships.get(ascendant_lord) or []) | aspected_houses(ascendant_lord, ascendant_house))
            & event_houses
        )
        ascendant_lord_judgment = {
            "planet": ascendant_lord,
            "available": True,
            "house": ascendant_house,
            "event_links": ascendant_links,
            "dignity": dignity_for(ascendant_lord, ascendant_row),
        }
        if ascendant_links:
            score = 1
        else:
            score = 0
    else:
        score = 0
    house_lord_hits: List[Dict[str, Any]] = []
    for lord in sorted(relevant_lords):
        placement = planets.get(lord) or {}
        if not placement.get("house"):
            house_lord_hits.append({"planet": lord, "available": False})
            continue
        house = int(placement["house"])
        links = sorted(({house} | aspected_houses(lord, house)) & event_houses)
        dignity = dignity_for(lord, placement)
        if links:
            score += 2
        if links and dignity in {"exalted", "moolatrikona", "own_sign"}:
            score += 1
        house_lord_hits.append({
            "planet": lord, "available": True, "house": house,
            "event_links": links, "dignity": dignity,
        })
    d1_delivery_rows = {
        str(row.get("planet")): row
        for row in (d1_delivery or {}).get("carriers") or []
        if isinstance(row, Mapping) and row.get("planet")
    }
    carrier_hits = []
    pressure = 0
    for planet in carriers:
        d1_row = d1_delivery_rows.get(str(planet)) or {}
        d1_links = sorted(int(house) for house in d1_row.get("event_links") or [])
        placement = planets.get(planet) or {}
        if not placement.get("house"):
            carrier_hits.append({
                "planet": planet,
                "available": False,
                "d1_event_links": d1_links,
                "houses": [],
                "confirms_event": False,
                "reason": "planet_unavailable_in_divisional_chart",
            })
            continue
        house = int(placement["house"])
        occupied_links = sorted({house} & event_houses)
        lordship_links = sorted(set(lordships.get(planet) or []) & event_houses)
        aspect_links = sorted(aspected_houses(planet, house) & event_houses)
        links = sorted(set(occupied_links) | set(lordship_links) | set(aspect_links))
        dignity = dignity_for(planet, placement)
        confirms_event = bool(d1_links and links)
        if confirms_event:
            score += 3 if house in event_houses or set(lordships.get(planet) or []) & event_houses else 1
        if confirms_event and dignity in {"exalted", "moolatrikona", "own_sign"}:
            score += 2
        elif confirms_event and dignity == "debilitated":
            pressure += 2
        conjunctions = conjunctions_for(planet, planets)
        cooperating_conjunctions = [row for row in conjunctions if row.get("planet") in relevant_lords or row.get("planet") in _event_karakas(event_key)]
        if confirms_event and cooperating_conjunctions:
            score += 1
        carrier_hits.append({
            "planet": planet, "available": True, "house": house, "houses": links, "dignity": dignity,
            "d1_event_links": d1_links,
            "divisional_occupation_links": occupied_links,
            "divisional_lordship_links": lordship_links,
            "divisional_aspect_links": aspect_links,
            "confirms_event": confirms_event,
            "functional_nature": placement.get("functional_nature"),
            "conjunctions": conjunctions,
            "cooperating_conjunctions": cooperating_conjunctions,
        })
    karaka_hits = []
    for karaka in _event_karakas(event_key):
        placement = planets.get(karaka) or {}
        if placement.get("house"):
            house = int(placement["house"])
            links = sorted(({house} | aspected_houses(karaka, house)) & event_houses)
            if links:
                score += 1
            karaka_hits.append({"planet": karaka, "house": house, "houses": links, "dignity": dignity_for(karaka, placement)})
    confirmed_carriers = [row for row in carrier_hits if row.get("confirms_event")]
    non_confirming_carriers = [row for row in carrier_hits if not row.get("confirms_event")]
    pressured_carriers = [
        row for row in confirmed_carriers
        if row.get("dignity") == "debilitated"
    ]
    d1_repetition = bool(
        d1_promise.get("verdict") in {"strong", "available"}
        and confirmed_carriers
    )
    if d1_repetition:
        score += 2
    if not d1_repetition:
        verdict = "not_confirmed"
    elif score >= 7 and pressure < score:
        verdict = "confirmed"
    else:
        verdict = "mixed"
    return {
        "chart": varga,
        "available": True,
        "confirmed": verdict == "confirmed",
        "verdict": verdict,
        "score": score,
        "pressure_score": pressure,
        "ascendant": chart.get("ascendant"),
        "ascendant_lord": ascendant_lord_judgment,
        "relevant_house_lords": sorted(relevant_lords),
        "house_lord_hits": house_lord_hits,
        "carrier_hits": carrier_hits,
        "confirmed_carriers": confirmed_carriers,
        "non_confirming_carriers": non_confirming_carriers,
        "pressured_carriers": pressured_carriers,
        "required_divisional_houses": sorted(event_houses),
        "rule": (
            "A divisional chart confirms only when the same active dasha planet links the event in D1 "
            "and repeats the configured event houses in this divisional chart."
        ),
        "karaka_hits": karaka_hits,
        "d1_repetition": d1_repetition,
    }


def kp_judgment(
    kp: Mapping[str, Any],
    anchor_houses: Set[int],
    event_houses: Set[int],
    obstruction_houses: Set[int],
    carriers: Sequence[str],
    transit_contacts: Sequence[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    cusp_lords = kp.get("cusp_lords") if isinstance(kp.get("cusp_lords"), Mapping) else {}
    planet_sigs = kp.get("planet_significators") if isinstance(kp.get("planet_significators"), Mapping) else {}
    four_step = kp.get("four_step_theory") if isinstance(kp.get("four_step_theory"), Mapping) else {}
    judgments = []
    positive_total = 0
    obstruction_total = 0
    for house in sorted(anchor_houses):
        cusp = cusp_lords.get(house) or cusp_lords.get(str(house)) or {}
        sub_lord = str(cusp.get("sub_lord") or "") if isinstance(cusp, Mapping) else ""
        signified = {int(h) for h in (planet_sigs.get(sub_lord) or []) if str(h).isdigit()}
        positive = sorted(signified & event_houses)
        negative = sorted(signified & obstruction_houses)
        positive_total += len(positive)
        obstruction_total += len(negative)
        judgments.append({
            "cusp": house, "sign_lord": cusp.get("sign_lord") if isinstance(cusp, Mapping) else None,
            "star_lord": cusp.get("star_lord") if isinstance(cusp, Mapping) else None,
            "sub_lord": sub_lord or None, "sub_sub_lord": cusp.get("sub_sub_lord") if isinstance(cusp, Mapping) else None,
            "signified_houses": sorted(signified), "event_links": positive, "obstruction_links": negative,
        })
    carrier_chains = []
    carrier_support = 0
    carrier_pressure = 0
    carriers_with_event_links = 0
    for carrier in carriers:
        steps = four_step.get(carrier) or {}
        chain = []
        for key in ("planet", "star_lord", "sub_lord", "sub_sub_lord"):
            row = steps.get(key) or {}
            houses = {int(h) for h in row.get("houses") or [] if str(h).isdigit()}
            positive = sorted(houses & event_houses)
            negative = sorted(houses & obstruction_houses)
            carrier_support += len(positive)
            carrier_pressure += len(negative)
            chain.append({"step": key, "lord": row.get("name"), "houses": sorted(houses), "event_links": positive, "obstruction_links": negative})
        has_event_link = any(step.get("event_links") for step in chain)
        carriers_with_event_links += int(has_event_link)
        carrier_chains.append({"planet": carrier, "has_event_link": has_event_link, "chain": chain})
    complete = bool(judgments) and all(row.get("sub_lord") for row in judgments)
    support = positive_total + carrier_support
    pressure = obstruction_total + carrier_pressure
    if not complete:
        verdict = "unavailable"
    elif positive_total == 0 and pressure > 0:
        verdict = "blocked"
    elif (
        support >= max(4, pressure + 2)
        and carrier_support > 0
        and carriers_with_event_links == len(carriers)
    ):
        verdict = "supported"
    elif support > 0:
        verdict = "qualified" if pressure <= support else "pressured"
    else:
        verdict = "pressured"
    return {
        "complete": complete,
        "verdict": verdict,
        "support_score": support,
        "pressure_score": pressure,
        "cusp_judgments": judgments,
        "carrier_chains": carrier_chains,
        "active_carriers_confirmed": carriers_with_event_links,
        "active_carriers_total": len(carriers),
        "transit_contact": (
            "exact_cusp_contact_present" if transit_contacts
            else "no_exact_cusp_contact_in_period" if kp.get("house_cusps")
            else "unavailable_without_kp_cusp_degrees"
        ),
        "transit_contact_windows": [dict(row) for row in (transit_contacts or [])],
    }


def _parse_day(value: Any) -> date | None:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def timing_windows(
    graph: Mapping[str, Any],
    anchor_houses: Set[int],
    transition_houses: Set[int],
    event_houses: Set[int],
    require_all_anchor: bool = False,
    require_all_transition: bool = False,
    minimum_anchor_hits: int = 1,
    minimum_transition_hits: int = 1,
    minimum_transition_dasha_hits: int = 0,
    require_transition_transit: bool = False,
    required_dasha_houses: Set[int] | None = None,
    required_outcome_houses: Set[int] | None = None,
    minimum_outcome_hits: int = 0,
    require_all_outcome: bool = False,
    allow_core_dasha_transit_permission: bool = False,
    require_independent_timing: bool = False,
) -> Dict[str, Any]:
    rows = graph.get("houses") or {}
    channels = [
        {**channel, "house": int(house)}
        for house, row in rows.items()
        for channel in (row.get("dasha_channels") or []) + (row.get("transit_channels") or [])
        if _parse_day(channel.get("start_date")) and _parse_day(channel.get("end_date"))
    ]
    if not channels:
        return {"windows": [], "resolution": "unavailable", "limitations": ["channel date boundaries unavailable"]}
    boundaries: Set[date] = set()
    for channel in channels:
        start = _parse_day(channel.get("start_date"))
        end = _parse_day(channel.get("end_date"))
        if start and end:
            boundaries.add(start)
            boundaries.add(end + timedelta(days=1))
    points = sorted(boundaries)
    windows: List[Dict[str, Any]] = []
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1] - timedelta(days=1)
        active = [channel for channel in channels if _parse_day(channel["start_date"]) <= start <= _parse_day(channel["end_date"])]
        dasha_houses = {channel["house"] for channel in active if not str(channel.get("mechanism") or "").startswith("transit_") and channel.get("dasha_level") in {"mahadasha", "antardasha", "pratyantardasha"}}
        transit_houses = {channel["house"] for channel in active if str(channel.get("mechanism") or "").startswith("transit_")}
        dasha_transit_permission_channels = [
            channel for channel in active
            if channel.get("mechanism") == "transit_occupation"
            and channel.get("dasha_level") in {"mahadasha", "antardasha", "pratyantardasha"}
        ] if allow_core_dasha_transit_permission else []
        dasha_permission_houses = dasha_houses | {
            channel["house"] for channel in dasha_transit_permission_channels
        }
        background_sources = {
            (str(channel.get("planet") or ""), str(channel.get("dasha_level") or ""))
            for channel in dasha_transit_permission_channels
            if channel["house"] in (anchor_houses | set(required_dasha_houses or set()))
            and channel.get("planet") in {"Jupiter", "Saturn", "Rahu", "Ketu"}
        }
        independent_timing_channels = [
            channel for channel in active
            if channel["house"] in transition_houses | (event_houses - anchor_houses)
            and (
                channel.get("dasha_level") in {"pratyantardasha", "sookshma"}
                or (
                    str(channel.get("mechanism") or "").startswith("transit_")
                    and channel.get("planet") not in {"Jupiter", "Saturn", "Rahu", "Ketu"}
                )
            )
            and (str(channel.get("planet") or ""), str(channel.get("dasha_level") or ""))
            not in background_sources
        ]
        anchor_ok = (
            anchor_houses.issubset(dasha_permission_houses)
            if require_all_anchor
            else len(anchor_houses & dasha_permission_houses) >= max(1, int(minimum_anchor_hits))
        )
        transition_union = dasha_houses | transit_houses
        transition_ok = (
            transition_houses.issubset(transition_union)
            if require_all_transition
            else len(transition_houses & transition_union) >= max(1, int(minimum_transition_hits))
        )
        transition_dasha_ok = len(transition_houses & dasha_houses) >= int(minimum_transition_dasha_hits)
        transition_transit_ok = not require_transition_transit or bool(transition_houses & transit_houses)
        required_dasha_ok = set(required_dasha_houses or set()).issubset(dasha_permission_houses)
        required_outcomes = set(required_outcome_houses or set())
        outcome_ok = (
            required_outcomes.issubset(transition_union)
            if require_all_outcome else
            len(required_outcomes & transition_union) >= int(minimum_outcome_hits)
        ) if required_outcomes else True
        independent_timing_ok = not require_independent_timing or bool(independent_timing_channels)
        if anchor_ok and transition_ok and transition_dasha_ok and transition_transit_ok and required_dasha_ok and outcome_ok and independent_timing_ok and bool(event_houses & transit_houses):
            carrier_planets = sorted({str(channel.get("planet")) for channel in active if channel.get("planet")})
            row = {"start_date": start.isoformat(), "end_date": end.isoformat(), "carriers": carrier_planets}
            if windows and windows[-1]["end_date"] == (start - timedelta(days=1)).isoformat() and windows[-1]["carriers"] == carrier_planets:
                windows[-1]["end_date"] = end.isoformat()
            else:
                windows.append(row)
    exact_available = bool(graph.get("transit_daily"))
    return {
        "windows": windows,
        "resolution": "calendar_day_segment_boundaries",
        "contact_phase": "daily_sampled_degree_contacts_available" if exact_available else "sign_nakshatra_pada_level_only",
        "limitations": (
            ["Exact-contact peaks are daily samples; intraday roots are not solved."]
            if exact_available else
            ["Exact applying/exact/separating degree contacts and stations are unavailable in this ledger."]
        ),
    }


def ashtakavarga_judgment(
    context: Mapping[str, Any],
    graph: Mapping[str, Any],
    carriers: Sequence[str],
    event_houses: Set[int],
) -> Dict[str, Any]:
    advanced = (context.get("ashtakavarga") or {}).get("advanced") or {}
    prastara = advanced.get("prastara") if isinstance(advanced.get("prastara"), Mapping) else {}
    daily = graph.get("transit_daily") if isinstance(graph.get("transit_daily"), Mapping) else {}
    d1 = context.get("d1_chart") or {}
    if not prastara or not daily or d1.get("ascendant") is None:
        return {"available": False, "verdict": "unavailable", "rows": [], "role": "ease_modifier_only"}
    ascendant_sign = int(float(d1["ascendant"]) // 30) % 12
    event_signs = {(ascendant_sign + house - 1) % 12 for house in event_houses}
    rows: List[Dict[str, Any]] = []
    for planet in carriers:
        matrix = ((prastara.get(planet) or {}).get("matrix") or {})
        totals = ((prastara.get(planet) or {}).get("sign_totals") or {})
        if not matrix:
            continue
        seen: Set[Tuple[int, int, bool]] = set()
        for state in daily.get(planet) or []:
            try:
                longitude = float(state.get("longitude")) % 360.0
            except (TypeError, ValueError):
                continue
            sign = int(longitude // 30) % 12
            if sign not in event_signs:
                continue
            kakshya_index = min(7, int((longitude % 30.0) // 3.75))
            identity = (sign, kakshya_index, bool(state.get("retrograde")))
            if identity in seen:
                continue
            seen.add(identity)
            ruler = KAKSHYA_RULERS[kakshya_index]
            bindu = int((matrix.get(ruler) or {}).get(str(sign), 0) or 0)
            bav_total = int(totals.get(str(sign), 0) or 0)
            rows.append({
                "planet": planet, "sign_id": sign, "event_houses": sorted(event_houses),
                "kakshya_number": kakshya_index + 1, "kakshya_ruler": ruler,
                "kakshya_bindu": bindu, "kakshya_active": bindu == 1,
                "bav_bindus": bav_total,
                "bav_band": "bindu_rich" if bav_total >= 5 else "mixed" if bav_total >= 3 else "bindu_poor",
                "retrograde": bool(state.get("retrograde")),
            })
    if not rows:
        verdict = "unavailable"
    else:
        supportive = sum(1 for row in rows if row["kakshya_active"] and row["bav_bindus"] >= 5)
        pressured = sum(1 for row in rows if not row["kakshya_active"] and row["bav_bindus"] <= 2)
        verdict = "supportive" if supportive > pressured and supportive else "pressured" if pressured > supportive else "mixed"
    return {
        "available": bool(rows), "verdict": verdict, "rows": rows,
        "role": "ease_modifier_only",
        "basis": "fixed_natal_bav_prastara_kakshya",
        "guardrail": "BAV/Kakshya modifies ease and timing; it cannot create an event.",
    }


def _planet_event_links(planet: str, context: Mapping[str, Any], event_houses: Set[int]) -> List[int]:
    placement = _planet_rows(context).get(planet) or {}
    lordships = set((context.get("house_lordships") or {}).get(planet) or [])
    try:
        house = int(placement.get("house"))
    except (TypeError, ValueError):
        house = 0
    return sorted((lordships | ({house} if house else set()) | (aspected_houses(planet, house) if house else set())) & event_houses)


def supporting_systems_judgment(
    context: Mapping[str, Any],
    event_key: str,
    event_houses: Set[int],
    month: int,
    year: int,
) -> Dict[str, Any]:
    support = context.get("supporting_systems") or {}
    if not support:
        # Full-context compatibility: use its already-calculated top-level rows.
        support = {
            "varshphal": context.get("varshphal") or {},
            "chara_dasha": context.get("chara_dasha") or {},
            "sudarshana": context.get("sudarshana_dasha") or {},
            "monthly": {str(month): {
                "yogini": context.get("yogini_dasha") or {},
                "kalachakra": context.get("kalchakra_dasha") or {},
            }},
        }
    groups: List[Dict[str, Any]] = []
    ascendant = (context.get("d1_chart") or {}).get("ascendant")
    ascendant_sign = int(float(ascendant or 0.0) // 30) % 12
    varshphal = support.get("varshphal") or {}
    if varshphal.get("available", bool(varshphal)):
        muntha = varshphal.get("muntha") or {}
        muntha_house = int(muntha.get("house") or varshphal.get("muntha_house") or 0)
        year_lord = str(varshphal.get("year_lord") or "")
        mudda_active = []
        month_start = date(year, month, 1)
        month_end = date(year, month, 28) + timedelta(days=4)
        month_end = month_end - timedelta(days=month_end.day)
        for period in varshphal.get("mudda_dasha") or []:
            start = _parse_day(period.get("start"))
            end = _parse_day(period.get("end"))
            if start and end and start <= month_end and end >= month_start:
                planet = str(period.get("planet") or "")
                mudda_active.append({"planet": planet, "event_links": _planet_event_links(planet, context, event_houses)})
        links = sorted(({muntha_house} if muntha_house else set()) & event_houses)
        year_lord_links = _planet_event_links(year_lord, context, event_houses) if year_lord else []
        groups.append({
            "group": "solar_return_subset", "system": "Varshaphal subset",
            "verdict": "supportive" if links and (year_lord_links or any(row["event_links"] for row in mudda_active)) else "mixed" if links or year_lord_links or any(row["event_links"] for row in mudda_active) else "neutral",
            "muntha_house": muntha_house or None, "muntha_event_links": links,
            "year_lord": year_lord or None, "year_lord_event_links": year_lord_links,
            "active_mudda": mudda_active,
            "scope": varshphal.get("scope") or "muntha_year_lord_mudda_only",
            "not_available": varshphal.get("not_available") or ["complete_tajika_strengths"],
        })
    chara = support.get("chara_dasha") or {}
    chara_hits = []
    comparison_month_end = date(year, month, monthrange(year, month)[1])
    for period in chara.get("periods") or []:
        start = _parse_day(period.get("start_date"))
        end = _parse_day(period.get("end_date"))
        if not start or not end or not (start <= comparison_month_end and end >= date(year, month, 1)):
            continue
        sign_id = int(period.get("sign_id") or 0) % 12
        house = ((sign_id - ascendant_sign) % 12) + 1
        antar_hits = []
        for antar in period.get("antardashas") or []:
            astart = _parse_day(antar.get("start_date"))
            aend = _parse_day(antar.get("end_date"))
            if astart and aend and astart <= comparison_month_end and aend >= date(year, month, 1):
                ahouse = ((int(antar.get("sign_id") or 0) - ascendant_sign) % 12) + 1
                antar_hits.append({"sign": antar.get("sign_name"), "house": ahouse, "event_link": ahouse in event_houses})
        chara_hits.append({"sign": period.get("sign_name"), "house": house, "event_link": house in event_houses, "antardashas": antar_hits})
    if chara.get("available", bool(chara)):
        groups.append({
            "group": "jaimini_sign_dasha", "system": "Chara Dasha",
            "verdict": "supportive" if any(row["event_link"] and any(a["event_link"] for a in row["antardashas"]) for row in chara_hits) else "mixed" if any(row["event_link"] or any(a["event_link"] for a in row["antardashas"]) for row in chara_hits) else "neutral",
            "periods": chara_hits,
        })
    monthly = (support.get("monthly") or {}).get(str(month)) or {}
    for key, group_name, label in (
        ("yogini", "nakshatra_dasha", "Yogini Dasha"),
        ("kalachakra", "nakshatra_pada_dasha", "Kalachakra Dasha"),
    ):
        value = monthly.get(key) or {}
        if not value.get("available", bool(value)):
            continue
        planets: List[str] = []
        for level in ("mahadasha", "antardasha"):
            row = value.get(level) or {}
            planet = str(row.get("lord") or row.get("planet") or "")
            if planet:
                planets.append(planet)
        rows = [{"planet": planet, "event_links": _planet_event_links(planet, context, event_houses)} for planet in planets]
        groups.append({
            "group": group_name, "system": label,
            "verdict": "supportive" if len(rows) >= 2 and all(row["event_links"] for row in rows) else "mixed" if any(row["event_links"] for row in rows) else "neutral",
            "active_planets": rows,
        })
    sudarshana = support.get("sudarshana") or {}
    relevant_planets = set(_event_karakas(event_key)) | {
        planet for planet, houses in (context.get("house_lordships") or {}).items()
        if set(houses or []) & event_houses
    }
    trigger_rows = [
        row for row in sudarshana.get("precision_triggers") or []
        if _parse_day(row.get("date")) and _parse_day(row.get("date")).year == year
        and _parse_day(row.get("date")).month == month
        and row.get("planet") in relevant_planets
    ]
    if sudarshana.get("available", bool(sudarshana)):
        groups.append({
            "group": "annual_age_clock", "system": "Sudarshana annual clock",
            "verdict": "supportive" if trigger_rows else "neutral", "triggers": trigger_rows,
        })
    supportive_groups = sorted({row["group"] for row in groups if row["verdict"] == "supportive"})
    pressured_groups = sorted({row["group"] for row in groups if row["verdict"] == "pressured"})
    adjustment = max(-3, min(3, len(supportive_groups) - len(pressured_groups)))
    return {
        "available": bool(groups), "systems": groups,
        "supportive_independence_groups": supportive_groups,
        "pressured_independence_groups": pressured_groups,
        "capped_priority_adjustment": adjustment,
        "guardrail": "Each independent group contributes at most once; supporting systems cannot create an event.",
    }


def birth_time_reliability_judgment(
    context: Mapping[str, Any], varga: Mapping[str, Any], kp: Mapping[str, Any]
) -> Dict[str, Any]:
    reliability = dict(context.get("birth_time_reliability") or {})
    sensitivity = context.get("birth_time_sensitivity") or {}
    trust_supplied_time = str(
        os.getenv("EVENT_TIMELINE_TRUST_SUPPLIED_BIRTH_TIME") or "true"
    ).strip().lower() in {"1", "true", "yes", "on"}
    if trust_supplied_time:
        supplied_source = str(reliability.get("source") or "").strip().lower()
        return {
            **reliability,
            "source": supplied_source if supplied_source and supplied_source != "unknown" else "user_provided",
            "available": True,
            "verdict": "stable",
            "boundary_risk": "accepted_as_entered",
            "assumption": "user_supplied_birth_time_is_authoritative",
            "user_supplied_time_trusted": True,
            "kp_specificity": "retained",
            "varga_specificity": "retained",
            "sensitivity": sensitivity,
        }
    uncertainty = reliability.get("uncertainty_minutes")
    boundary_risk = str(sensitivity.get("boundary_risk") or "unknown")
    if uncertainty is None:
        verdict = "stable" if reliability.get("verified") else "unknown"
    elif boundary_risk == "high":
        verdict = "sensitive"
    elif int(uncertainty) <= 5 or reliability.get("verified"):
        verdict = "stable"
    else:
        verdict = "qualified"
    return {
        **reliability, "verdict": verdict, "boundary_risk": boundary_risk,
        "assumption": "reliability_assessed_from_available_metadata",
        "user_supplied_time_trusted": False,
        "kp_specificity": "downgraded" if verdict in {"unknown", "sensitive"} and kp.get("complete") else "retained",
        "varga_specificity": "downgraded" if verdict in {"unknown", "sensitive"} and varga.get("available") else "retained",
        "sensitivity": sensitivity,
    }


def outcome_dimensions(
    phase: str,
    obstruction: Mapping[str, Any],
    delivery: Mapping[str, Any],
    kp: Mapping[str, Any],
    varga: Mapping[str, Any],
    ashtakavarga: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    obstruction_level = str(obstruction.get("verdict") or "low")
    delivery_verdict = str(delivery.get("verdict") or "unavailable")
    kp_verdict = str(kp.get("verdict") or "unavailable")
    varga_verdict = str(varga.get("verdict") or "unavailable")
    initiation = "strong" if delivery_verdict == "supportive" else "moderate" if delivery_verdict == "mixed" else "weak"
    av_verdict = str((ashtakavarga or {}).get("verdict") or "unavailable")
    ease = "obstructed" if obstruction_level == "high" or delivery_verdict == "obstructed" or kp_verdict == "blocked" else "mixed" if obstruction_level == "moderate" or kp_verdict == "pressured" or av_verdict == "pressured" else "supported"
    result = "strong" if phase == "result_window" and ease != "obstructed" else "developing" if phase in {"result_window", "developing"} else "preparatory"
    permanence = "supported" if varga_verdict == "confirmed" and kp_verdict == "supported" else "possible" if varga_verdict in {"confirmed", "mixed"} else "unconfirmed"
    completion = "likely_to_progress" if result == "strong" else "may_progress" if result == "developing" else "not_yet_shown"
    return {"initiation": initiation, "ease": ease, "result": result, "permanence": permanence, "completion": completion}
