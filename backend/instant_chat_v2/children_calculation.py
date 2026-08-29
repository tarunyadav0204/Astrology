"""Deterministic evidence synthesis for Children graph routes.

This module adjudicates calculated D1/D7/D10, KP and event-window records.  It
does not parse the user's prose and does not generate astrological placements.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from .children import BOUNDARY_CHILDREN_SUBTYPES, TIMING_CHILDREN_SUBTYPES, children_profile, normalize_children_subtype


_DIGNITY = {"exalted": 3.0, "mooltrikona": 2.5, "own_sign": 2.0, "friendly_sign": 0.5, "debilitated": -3.0, "enemy_sign": -0.5}
_NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
    "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)
_STAR_LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
_SUPPORTIVE_PLANETS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_PRESSURE_PLANETS = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _date(value: Any) -> datetime | None:
    text = str(value or "").strip()[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        return None


def _chart(chart_facts: Mapping[str, Any], code: str) -> dict[str, Any]:
    charts = chart_facts.get("charts") if isinstance(chart_facts.get("charts"), Mapping) else {}
    value = charts.get(code)
    return dict(value) if isinstance(value, Mapping) else {}


def _house_map(chart: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        int(row["house"]): dict(row)
        for row in chart.get("houses") or []
        if isinstance(row, Mapping) and _int(row.get("house")) is not None
    }


def _planet_map(chart: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(name): dict(row)
        for name, row in (chart.get("planets") or {}).items()
        if isinstance(row, Mapping)
    } if isinstance(chart.get("planets"), Mapping) else {}


def _aspects_house(origin: int | None, target: int, planet: str) -> bool:
    if origin is None:
        return False
    aspects = {7}
    if planet == "Mars":
        aspects.update({4, 8})
    elif planet == "Jupiter":
        aspects.update({5, 9})
    elif planet == "Saturn":
        aspects.update({3, 10})
    # Rahu and Ketu intentionally retain only the seventh aspect. Their fifth
    # and ninth aspects are excluded across Instant; occupation and
    # conjunction are handled separately below.
    return any(((int(origin) + aspect - 2) % 12) + 1 == target for aspect in aspects)


def _house_condition(chart_code: str, chart: Mapping[str, Any], house: int) -> dict[str, Any]:
    hrow = _house_map(chart).get(house) or {}
    lord = str(hrow.get("lord") or "")
    prow = _planet_map(chart).get(lord) or {}
    if not lord or not prow:
        return {"chart": chart_code, "house": house, "available": False, "score": 0.0}
    placement = _int(prow.get("house"))
    dignity = str(prow.get("dignity") or "").lower()
    score = _DIGNITY.get(dignity, 0.0)
    support: list[str] = []
    cautions: list[str] = []
    if score > 0:
        support.append(f"{chart_code}: H{house} lord {lord} is {dignity}")
    elif score < 0:
        cautions.append(f"{chart_code}: H{house} lord {lord} is {dignity}")
    if placement in {1, 2, 4, 5, 7, 9, 10, 11}:
        score += 1.0
        support.append(f"{chart_code}: H{house} lord {lord} is placed in H{placement}")
    elif placement in {6, 8, 12}:
        score -= 0.75
        cautions.append(f"{chart_code}: H{house} lord {lord} is placed in H{placement}")
    pmap = _planet_map(chart)
    occupants = [str(value) for value in hrow.get("occupants") or []]
    if "Jupiter" in occupants:
        score += 1.0
        support.append(f"{chart_code}: Jupiter occupies H{house}")
    for pressure in ("Saturn", "Rahu", "Ketu", "Mars"):
        if pressure in occupants:
            score -= 0.35
            cautions.append(f"{chart_code}: {pressure} occupies H{house}; this qualifies rather than automatically denies the result")
    aspects = []
    for planet, planet_row in pmap.items():
        if planet == lord:
            continue
        origin = _int(planet_row.get("house"))
        if not _aspects_house(origin, house, planet):
            continue
        aspects.append({"planet": planet, "from_house": origin, "aspect": 7 if planet in {"Rahu", "Ketu"} else None})
        if planet in _SUPPORTIVE_PLANETS:
            score += 0.4 if planet != "Jupiter" else 0.75
            support.append(f"{chart_code}: {planet} aspects H{house} from H{origin}")
        elif planet in _PRESSURE_PLANETS:
            score -= 0.3
            cautions.append(f"{chart_code}: {planet} aspects H{house} from H{origin}")
    lord_conjunctions = [
        planet for planet, planet_row in pmap.items()
        if planet != lord and placement is not None and _int(planet_row.get("house")) == placement
    ]
    for planet in lord_conjunctions:
        if planet in _SUPPORTIVE_PLANETS:
            score += 0.3
            support.append(f"{chart_code}: H{house} lord {lord} is conjunct {planet} in H{placement}")
        elif planet in _PRESSURE_PLANETS:
            score -= 0.25
            cautions.append(f"{chart_code}: H{house} lord {lord} is conjunct {planet} in H{placement}")
    if prow.get("combust"):
        score -= 0.5
        cautions.append(f"{chart_code}: H{house} lord {lord} is combust")
    return {
        "chart": chart_code, "house": house, "available": True, "lord": lord,
        "lord_house": placement, "lord_sign": prow.get("sign_name") or prow.get("sign"),
        "lord_dignity": dignity or None, "occupants": occupants, "aspects": aspects,
        "lord_conjunctions": lord_conjunctions, "score": round(score, 3),
        "support": support, "cautions": cautions,
    }


def _branch(name: str, charts: list[tuple[str, Mapping[str, Any]]], primary: list[int], supporting: list[int], rule: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    weighted = 0.0
    total = 0.0
    complete = True
    chart_totals: dict[str, dict[str, Any]] = {}
    for chart_code, chart in charts:
        chart_total = chart_totals.setdefault(chart_code, {"weighted": 0.0, "total": 0.0, "complete": True})
        for house in primary + supporting:
            row = _house_condition(chart_code, chart, house)
            weight = 2.0 if house in primary else 1.0
            row["decision_weight"] = weight
            rows.append(row)
            if not row.get("available"):
                if house in primary:
                    complete = False
                    chart_total["complete"] = False
                continue
            weighted += float(row.get("score") or 0) * weight
            total += weight
            chart_total["weighted"] += float(row.get("score") or 0) * weight
            chart_total["total"] += weight
    score = round(weighted / total, 3) if total else 0.0
    verdict = "not_established" if not complete or not total else "supported" if score >= 0.75 else "qualified" if score >= 0 else "pressured"
    chart_verdicts = {}
    for code, values in chart_totals.items():
        chart_score = round(values["weighted"] / values["total"], 3) if values["total"] else 0.0
        chart_verdicts[code] = {
            "score": chart_score,
            "evidence_complete": bool(values["complete"] and values["total"]),
            "verdict": (
                "not_established" if not values["complete"] or not values["total"]
                else "supported" if chart_score >= 0.75
                else "qualified" if chart_score >= 0 else "pressured"
            ),
        }
    return {
        "route": name, "verdict": verdict, "score": score,
        "primary_houses": primary, "supporting_houses": supporting,
        "evidence_complete": complete and bool(total), "house_lord_conditions": rows,
        "chart_verdicts": chart_verdicts,
        "supporting_factors": [line for row in rows for line in row.get("support") or []][:12],
        "cautions": [line for row in rows for line in row.get("cautions") or []][:10],
        "rule": rule,
    }


def _jupiter_condition(d1: Mapping[str, Any], d7: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for code, chart in (("D1", d1), ("D7", d7)):
        row = _planet_map(chart).get("Jupiter") or {}
        if not row:
            rows.append({"chart": code, "available": False})
            continue
        dignity = str(row.get("dignity") or "").lower()
        score = _DIGNITY.get(dignity, 0.0)
        house = _int(row.get("house"))
        if house in {1, 2, 5, 9, 11}:
            score += 1.0
        elif house in {6, 8, 12}:
            score -= 0.5
        if row.get("combust"):
            score -= 0.5
        rows.append({
            "chart": code, "available": True, "house": house,
            "sign": row.get("sign_name") or row.get("sign"), "dignity": dignity or None,
            "score": round(score, 3), "combust": bool(row.get("combust")),
        })
    available = [row for row in rows if row.get("available")]
    score = round(sum(float(row.get("score") or 0) for row in available) / len(available), 3) if available else 0.0
    return {
        "verdict": "not_established" if len(available) < 2 else "supported" if score >= 1 else "qualified" if score >= 0 else "pressured",
        "score": score, "rows": rows,
        "rule": "Jupiter qualifies progeny support only after the relevant D1 and D7 house chains; Jupiter alone never promises a child.",
    }


def _nakshatra_chains(chart_data: Mapping[str, Any], d1: Mapping[str, Any], houses: list[int]) -> list[dict[str, Any]]:
    raw_planets = chart_data.get("planets") if isinstance(chart_data.get("planets"), Mapping) else {}
    pmap = _planet_map(d1)
    rows = []
    for house in houses:
        lord = str((_house_map(d1).get(house) or {}).get("lord") or "")
        raw = raw_planets.get(lord) if isinstance(raw_planets.get(lord), Mapping) else {}
        try:
            longitude = float(raw.get("longitude")) % 360
            index = min(26, int(longitude / (360 / 27)))
            nakshatra = _NAKSHATRAS[index]
            star_lord = _STAR_LORDS[index % 9]
        except (TypeError, ValueError):
            nakshatra, star_lord = None, None
        prow = pmap.get(lord) or {}
        star_row = pmap.get(str(star_lord or "")) or {}
        star_house = _int(star_row.get("house"))
        star_dignity = str(star_row.get("dignity") or "").lower()
        chain_score = _DIGNITY.get(star_dignity, 0.0)
        if star_house in {1, 2, 4, 5, 7, 9, 10, 11}:
            chain_score += 0.5
        elif star_house in {6, 8, 12}:
            chain_score -= 0.5
        rows.append({
            "house": house, "lord": lord or None, "lord_house": _int(prow.get("house")),
            "lord_sign": prow.get("sign_name") or prow.get("sign"), "lord_dignity": prow.get("dignity"),
            "lord_nakshatra": nakshatra, "nakshatra_lord": star_lord,
            "nakshatra_lord_house": star_house,
            "nakshatra_lord_dignity": star_dignity or None,
            "chain_score": round(chain_score, 3),
        })
    return rows


def _kp_adjudication(kp: Mapping[str, Any], primary_cusps: list[int], success_houses: set[int]) -> dict[str, Any]:
    cusp_lords = kp.get("cusp_lords") if isinstance(kp.get("cusp_lords"), Mapping) else {}
    planet_significators = kp.get("planet_significators") if isinstance(kp.get("planet_significators"), Mapping) else {}
    rows = []
    for cusp in primary_cusps:
        crow = cusp_lords.get(cusp) or cusp_lords.get(str(cusp)) or {}
        sub_lord = str(crow.get("sub_lord") or "") if isinstance(crow, Mapping) else ""
        signified = {_int(v) for v in planet_significators.get(sub_lord) or []}
        signified.discard(None)
        support = sorted(int(v) for v in signified & success_houses)
        negation = sorted(int(v) for v in signified & {1, 4, 10})
        rows.append({
            "cusp": cusp, "sub_lord": sub_lord or None, "sub_lord_signifies": sorted(int(v) for v in signified),
            "success_house_links": support, "negation_house_links": negation,
            "supports_route": bool(support) and len(support) >= len(negation),
        })
    supported = sum(1 for row in rows if row.get("supports_route"))
    complete = bool(rows) and len(rows) == len(primary_cusps) and all(row.get("sub_lord") for row in rows)
    return {
        "complete": complete, "supported_cusps": supported, "required_cusps": len(primary_cusps),
        "verdict": "not_established" if not complete else "supported" if supported == len(rows) else "qualified" if supported else "pressured",
        "cusp_judgments": rows,
        "rule": "KP requires the relevant cusp sub-lords to signify the route success chain; 1/4/10 qualify childbirth fructification and data availability is not support.",
    }


def _timing_windows(normalized: Mapping[str, Any], success_houses: set[int], period_window: Mapping[str, Any] | None, retrospective: bool) -> list[dict[str, Any]]:
    source_key = "historical_event_dasha_scan" if retrospective else "forward_event_dasha_scan"
    source = normalized.get(source_key)
    rows = []
    if isinstance(source, Mapping):
        rows = source.get("ranked_windows") or source.get("periods") or source.get("windows") or []
    elif isinstance(source, list):
        rows = source
    requested_start = _date((period_window or {}).get("start"))
    requested_end = _date((period_window or {}).get("end"))
    ranked = []
    for value in rows:
        if not isinstance(value, Mapping):
            continue
        row_start = _date(value.get("start") or value.get("start_date"))
        row_end = _date(value.get("end") or value.get("end_date"))
        if requested_start and row_end and row_end < requested_start:
            continue
        if requested_end and row_start and row_start > requested_end:
            continue
        active = {_int(v) for v in value.get("activated_focus_houses") or value.get("active_houses") or []}
        active.discard(None)
        coverage = sorted(int(v) for v in active & success_houses)
        if len(coverage) < 2:
            continue
        ranked.append({
            **dict(value), "route_success_houses": sorted(success_houses),
            "route_success_coverage": coverage, "coverage_count": len(coverage),
            "timing_claim": "supportive period, not a guaranteed conception, pregnancy, birth or legal outcome",
        })
    return sorted(ranked, key=lambda row: (-int(row.get("coverage_count") or 0), -float(row.get("score") or 0)))[:8]


def build_children_foundation(
    *, chart_data: Mapping[str, Any], normalized_evidence: Mapping[str, Any], category: Any,
    answer_mode: Any, children_subtype: Any, period_window: Mapping[str, Any] | None = None,
    kp_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    subtype = normalize_children_subtype(children_subtype)
    mode = str(answer_mode or "").strip().lower()
    if mode == "remedy_action":
        subtype = "children_remedy"
    elif subtype == "conception_capacity" and mode in {"event_prediction", "timing_window", "event_timing"}:
        subtype = "conception_timing"
    elif subtype == "adoption_pathway" and mode in {"event_prediction", "timing_window", "event_timing"}:
        subtype = "adoption_timing"
    elif subtype == "assisted_conception" and mode in {"event_prediction", "timing_window", "event_timing"}:
        subtype = "assisted_conception_timing"
    elif subtype == "first_child_capacity" and mode in {"event_prediction", "timing_window", "event_timing"}:
        subtype = "first_child"
    elif subtype == "subsequent_child_capacity" and mode in {"event_prediction", "timing_window", "event_timing"}:
        subtype = "subsequent_child"
    elif subtype == "parenthood_vs_career" and mode in {"event_prediction", "timing_window", "event_timing"}:
        subtype = "parenthood_vs_career_timing"
    profile = children_profile(category, subtype)
    if subtype in BOUNDARY_CHILDREN_SUBTYPES:
        return {
            "children_subtype": subtype, "focus_houses": [], "houses_available": [],
            "route_synthesis": {"verdict": "specialist_boundary", "boundary": subtype},
            "availability": {"scope_boundary": True},
        }
    facts = normalized_evidence.get("chart_facts") if isinstance(normalized_evidence.get("chart_facts"), Mapping) else {}
    d1, d7, d10 = _chart(facts, "D1"), _chart(facts, "D7"), _chart(facts, "D10")
    houses = list(profile["houses"])
    jupiter = _jupiter_condition(d1, d7)
    lord_chains = _nakshatra_chains(chart_data, d1, houses)
    d1_d7 = [("D1", d1), ("D7", d7)]
    promise = _branch(
        "core children promise", d1_d7, [5], [2, 11],
        "D1 establishes H5/H2/H11 promise and D7 must independently confirm or qualify the same family-expansion pattern.",
    )
    promise["jupiter_karaka"] = jupiter
    if promise["verdict"] == "supported" and jupiter["verdict"] == "pressured":
        promise["verdict"] = "qualified"

    first = _branch("first child", d1_d7, [5], [2, 11], "First-child promise is led by H5 and verified in D7; H2 and H11 support family expansion and realization.")
    second = _branch("second child", d1_d7, [7], [5, 9, 11], "The second-child route uses the explicit H7 progression from H5, with H9/later-child and D7 confirmation; it never copies the H5 result.")
    later = _branch("later children", d1_d7, [9], [5, 7, 11], "Later-child potential uses H9 as fifth-from-fifth with the preceding order chain and D7 confirmation.")
    order_frames = {"first": first, "second": second, "later": later}
    supported_orders = sum(1 for row in order_frames.values() if row.get("verdict") in {"supported", "qualified"})
    family_size = {
        "verdict": "not_established" if any(not row.get("evidence_complete") for row in order_frames.values()) else "multiple_parenthood_potential" if supported_orders >= 2 else "more_concentrated_parenthood_pattern",
        "supported_order_frames": supported_orders, "order_frames": order_frames,
        "claim_rule": "This is a relative family-size tendency, never an exact number of children or a twins prediction.",
    }

    mechanisms = []
    for name, primary, supporting in (
        ("promise_pressure", [5], [2, 11]), ("sustaining_or_transition_pressure", [8], [5, 11]),
        ("treatment_or_routine_pressure", [6, 12], [5, 11]), ("delay_or_negation_pressure", [1, 4, 10], [5]),
    ):
        row = _branch(name, d1_d7, primary, supporting, "Relative pressure is ranked from the full D1/D7 house-lord chain; it is not a medical diagnosis or automatic denial.")
        row["pressure_score"] = round(-float(row.get("score") or 0), 3)
        mechanisms.append(row)
    mechanisms.sort(key=lambda row: (-float(row.get("pressure_score") or 0), str(row.get("route"))))
    delay = {
        "verdict": "relative_pressure_ranked", "dominant_relative_pressure": mechanisms[0]["route"] if mechanisms else None,
        "mechanisms": mechanisms,
        "rule": "Name the strongest repeated pressure while separating delay from denial and astrology from fertility diagnosis.",
    }

    pathways = {
        "biological": _branch("biological conception", d1_d7, [5], [2, 8, 11], "Biological conception uses H5 with family expansion H2, reproductive transition H8 and realization H11; this is astrological potential, not fertility diagnosis."),
        "assisted": _branch("assisted conception", d1_d7, [8, 11], [5, 6, 12, 2], "Assisted conception adds intervention H8, treatment/routine H6, expense or clinical setting H12 and realization H11 to the natal promise."),
        "adoption": _branch("adoption", d1_d7, [9, 11], [4, 5, 8], "Adoption is a distinct care/legal-parenthood pathway through H9/H11 with H4/H5/H8 qualification; it is not inferred from weak biological fertility."),
        "step_parenthood": _branch("step-parenthood", d1_d7, [7, 9], [5, 11], "Step-parenthood uses relationship-linked H7, later-child H9, H5 parenting and H11 realization."),
    }

    relationship = _branch("parent-child relationship", d1_d7, [5, 4], [1, 2], "Describe the native's parenting and relationship pattern only; the child's motives, temperament and fate require the child's chart.")
    readiness = _branch("parenthood readiness", d1_d7, [1, 5], [2, 4, 11], "Readiness combines the native's disposition H1, parenting H5, family H2, care/home H4 and realization H11; it supports reflection, not a command to conceive.")
    childbirth = _branch("childbirth realization", d1_d7, [5, 11], [2, 9], "Childbirth is separated from conception by requiring H11 realization and H9 sustaining/grace support alongside H5 and H2.")
    reconciliation = _branch("parent-child reconciliation", d1_d7, [5, 11], [2, 4], "Reconciliation requires the relationship H5, communication/family H2, emotional base H4 and realization H11; it does not claim the child's motives.")
    parenthood_branch = _branch("parenthood", d1_d7, [5, 11], [2, 4], "Parenthood branch uses D1/D7 H5/H11 with family and care support.")
    career_branch = _branch("career", [("D1", d1), ("D10", d10)], [10, 6], [2, 11], "Career branch uses D1/D10 H10/H6 with income and realization support.")
    margin = round(float(parenthood_branch.get("score") or 0) - float(career_branch.get("score") or 0), 3)
    parenthood_vs_career = {
        "parenthood": parenthood_branch, "career": career_branch, "margin": margin,
        "direction": "parenthood" if margin >= 0.5 else "career" if margin <= -0.5 else "mixed",
        "rule": "Compare both complete branches independently; a structural preference is not a command about reproductive choices.",
    }

    success_by_route = {
        "conception_timing": {2, 5, 11}, "childbirth_timing": {2, 5, 9, 11},
        "first_child": {2, 5, 11}, "subsequent_child": {2, 7, 9, 11},
        "assisted_conception_timing": {2, 5, 6, 8, 11, 12}, "adoption_timing": {4, 5, 9, 11},
        "parenthood_vs_career_timing": {2, 5, 6, 10, 11},
        "parent_child_reconciliation_timing": {2, 4, 5, 11},
        "retrospective_child_timing": {2, 5, 11},
    }
    primary_cusps = {
        "conception_timing": [5, 11], "childbirth_timing": [5, 11], "first_child": [5, 11],
        "subsequent_child": [7, 9, 11], "assisted_conception_timing": [5, 8, 11],
        "adoption_timing": [5, 9, 11], "parenthood_vs_career_timing": [5, 10, 11],
        "parent_child_reconciliation_timing": [5, 11], "retrospective_child_timing": [5, 11],
    }
    route_success = success_by_route.get(subtype, {2, 5, 11})
    kp = _kp_adjudication(kp_evidence or {}, primary_cusps.get(subtype, [5, 11]), route_success) if subtype in TIMING_CHILDREN_SUBTYPES else {}
    windows = _timing_windows(normalized_evidence, route_success, period_window, subtype == "retrospective_child_timing") if subtype in TIMING_CHILDREN_SUBTYPES else []

    route_map = {
        "children_overview": promise, "parenthood_capacity": relationship,
        "conception_capacity": pathways["biological"], "conception_timing": pathways["biological"],
        "childbirth_timing": childbirth, "first_child_capacity": first, "first_child": first,
        "subsequent_child_capacity": second, "subsequent_child": second,
        "family_size_tendency": family_size, "children_delay_diagnosis": delay,
        "assisted_conception": pathways["assisted"], "assisted_conception_timing": pathways["assisted"],
        "adoption_pathway": pathways["adoption"], "adoption_timing": pathways["adoption"],
        "step_parenthood": pathways["step_parenthood"], "parenthood_decision": readiness,
        "parenthood_vs_career": parenthood_vs_career, "parenthood_vs_career_timing": parenthood_vs_career,
        "parent_child_relationship": relationship, "parent_child_reconciliation_timing": reconciliation,
        "retrospective_child_timing": promise,
    }
    remedy_blueprint = normalized_evidence.get("remedy_blueprint") if isinstance(normalized_evidence.get("remedy_blueprint"), Mapping) else {}
    remedy = {
        "verdict": "calculated_remedy" if remedy_blueprint.get("top_recommendation") else "not_established",
        "diagnosed_mechanism": delay.get("dominant_relative_pressure"),
        "top_recommendation": remedy_blueprint.get("top_recommendation"),
        "alternatives": list(remedy_blueprint.get("alternatives") or [])[:3],
        "calculated": bool(remedy_blueprint.get("top_recommendation")),
        "rule": "Use only the calculated remedy as spiritual support; never frame it as fertility treatment or an outcome guarantee.",
    }
    if subtype == "children_remedy":
        route_map[subtype] = remedy
    route = dict(route_map.get(subtype) or promise)
    available_chains = [row for row in lord_chains if row.get("lord_nakshatra") and row.get("nakshatra_lord")]
    chain_score = round(
        sum(float(row.get("chain_score") or 0) for row in available_chains) / len(available_chains), 3
    ) if available_chains else 0.0
    route["lord_nakshatra_chains"] = available_chains
    route["nakshatra_qualification"] = {
        "available": len(available_chains) == len(houses),
        "score": chain_score,
        "verdict": "supportive" if chain_score >= 0.5 else "qualified" if chain_score >= 0 else "pressured",
        "rule": "The relevant house lords' nakshatra dispositors qualify the route; they do not replace D1/D7 promise.",
    }
    route["jupiter_karaka"] = jupiter
    if route.get("verdict") == "supported" and (chain_score < 0 or jupiter.get("verdict") == "pressured"):
        route["verdict"] = "qualified"
    if subtype in TIMING_CHILDREN_SUBTYPES:
        route.update({
            "promise_verdict": route.get("verdict") or route.get("direction"),
            "kp_fructification": kp, "kp_chain_available": bool(kp.get("complete")),
            "timing_windows": windows, "timing_window_count": len(windows),
            "timing_verdict": "missing_kp_fructification" if not kp.get("complete") else "supportive_windows_found" if windows else "no_supported_window_in_horizon",
            "timing_rule": "Promise precedes KP, dasha and transit. Conception, childbirth, adoption and reconciliation use different success chains.",
        })
    return {
        "children_subtype": subtype, "focus_houses": houses,
        "houses_available": houses if d1 else [],
        "charts": {key: value for key, value in {"D1": d1, "D7": d7, "D10": d10 if subtype in {"parenthood_vs_career", "parenthood_vs_career_timing"} else {}}.items() if value},
        "lord_nakshatra_chains": lord_chains, "jupiter_karaka_synthesis": jupiter,
        "promise_synthesis": promise, "child_order_synthesis": order_frames,
        "family_size_synthesis": family_size, "delay_synthesis": delay,
        "pathway_synthesis": pathways, "relationship_synthesis": relationship,
        "parenthood_vs_career_synthesis": parenthood_vs_career,
        "remedy_synthesis": remedy if subtype == "children_remedy" else {},
        "kp_route_evidence": kp, "timing_windows": windows, "route_synthesis": route,
        "availability": {
            "d1": bool(d1), "d7": bool(d7), "d10": bool(d10) if subtype in {"parenthood_vs_career", "parenthood_vs_career_timing"} else False,
            "jupiter_karaka": len([row for row in jupiter.get("rows") or [] if row.get("available")]) == 2,
            "lord_nakshatra_chain": bool(lord_chains) and all(row.get("lord_nakshatra") for row in lord_chains),
            "child_order_frame": bool(order_frames) and all(row.get("evidence_complete") for row in order_frames.values()),
            "kp_fructification": bool(kp.get("complete")),
            "remedy_blueprint": bool(remedy.get("calculated")) if subtype == "children_remedy" else False,
        },
        "claim_boundaries": {
            "medical_diagnosis": False, "pregnancy_loss_prediction": False,
            "fetal_sex_prediction": False, "exact_child_count": False,
            "child_specific_fate_from_parent_chart": False,
        },
    }
