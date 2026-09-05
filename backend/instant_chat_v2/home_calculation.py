"""Deterministic D1/D4 evidence for Home, Property and Vehicles graph routes."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

from .home import BOUNDARY_HOME_SUBTYPES, home_profile, normalize_home_subtype
from .home_remedies import build_classical_property_remedy_blueprint


_SIGN_LORDS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
_DIGNITY = {"exalted": 2.0, "mooltrikona": 1.5, "own_sign": 1.25, "friendly_sign": 0.5, "friend_sign": 0.5, "debilitated": -2.0, "enemy_sign": -0.5}
_PRESSURE = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})


_TIMING_EVENT_COPY: dict[str, dict[str, str]] = {
    "property_purchase_timing": {
        "event": "property purchase",
        "supported_decision": "buying_in_requested_period_is_supported",
        "supported": "The requested period is astrologically supportive for buying property, subject to ordinary financial and legal checks.",
        "wait": "The requested period is not fully aligned for buying property; waiting for the next stronger purchase window is wiser.",
        "none": "No fully triangulated property-purchase window was found in the evaluated horizon.",
    },
    "property_sale_timing": {
        "event": "property sale",
        "supported_decision": "selling_in_requested_period_is_supported",
        "supported": "The requested period is astrologically supportive for selling the property, subject to ordinary transaction and legal checks.",
        "wait": "The requested period is not fully aligned for selling the property; waiting for the next stronger sale window is wiser.",
        "none": "No fully triangulated property-sale window was found in the evaluated horizon.",
    },
    "possession_documentation_timing": {
        "event": "possession and documentation",
        "supported_decision": "possession_documentation_in_requested_period_is_supported",
        "supported": "The requested period is astrologically supportive for completing possession or property documentation, subject to ordinary procedural checks.",
        "wait": "The requested period is not fully aligned for possession or documentation; waiting for the next stronger completion window is wiser.",
        "none": "No fully triangulated possession or documentation window was found in the evaluated horizon.",
    },
    "construction_timing": {
        "event": "construction or renovation",
        "supported_decision": "construction_in_requested_period_is_supported",
        "supported": "The requested period is astrologically supportive for beginning or advancing construction or renovation, subject to ordinary practical checks.",
        "wait": "The requested period is not fully aligned for construction or renovation; waiting for the next stronger execution window is wiser.",
        "none": "No fully triangulated construction or renovation window was found in the evaluated horizon.",
    },
    "relocation_timing": {
        "event": "domestic relocation",
        "supported_decision": "relocation_in_requested_period_is_supported",
        "supported": "The requested period is astrologically supportive for a domestic move, subject to ordinary practical checks.",
        "wait": "The requested period is not fully aligned for relocating; waiting for the next stronger moving window is wiser.",
        "none": "No fully triangulated domestic-relocation window was found in the evaluated horizon.",
    },
    "vehicle_timing": {
        "event": "vehicle purchase",
        "supported_decision": "vehicle_purchase_in_requested_period_is_supported",
        "supported": "The requested period is astrologically supportive for purchasing a vehicle, subject to ordinary financial and mechanical checks.",
        "wait": "The requested period is not fully aligned for purchasing a vehicle; waiting for the next stronger vehicle window is wiser.",
        "none": "No fully triangulated vehicle-purchase window was found in the evaluated horizon.",
    },
}


def _home_timing_decision(
    subtype: str,
    *,
    requested_period_supportive: bool,
    next_window: Mapping[str, Any] | None,
    next_event_request: bool = False,
    fructification_status: str = "supported",
) -> dict[str, Any]:
    """Build event-specific timing copy; never leak purchase language into another route."""
    available_window = bool(next_window)
    if subtype == "retrospective_property_timing":
        return {
            "event": "historical property acquisition",
            "requested_period_supportive": requested_period_supportive,
            "next_supported_window_available": available_window,
            "decision": "probable_historical_periods_identified" if available_window else "no_historical_window_found_in_evaluated_horizon",
            "required_visible_conclusion": (
                "The chart identifies probable historical periods for property acquisition; these are candidates for the user to verify, not a confirmed past date."
                if available_window
                else "No fully triangulated historical property-acquisition period was found in the evaluated horizon."
            ),
            "next_window": dict(next_window or {}),
            "rule": "Present historical periods as ranked candidates for verification, never as a now-versus-wait decision or a confirmed date.",
        }

    copy = _TIMING_EVENT_COPY[subtype]
    fully_fructified = str(fructification_status or "").strip().lower() == "supported"
    if not fully_fructified:
        start = str((next_window or {}).get("start") or "").strip()
        end = str((next_window or {}).get("end") or "").strip()
        dated_window = f" from {start} to {end}" if start and end else ""
        qualified = str(fructification_status or "").strip().lower() == "qualified"
        return {
            "event": copy["event"],
            "question_scope": "next_event_window" if next_event_request else "requested_period",
            "requested_period_supportive": False,
            "next_supported_window_available": False,
            "conditional_window_available": bool(qualified and available_window),
            "decision": "conditional_window_only" if qualified and available_window else "no_supported_window_found_in_evaluated_horizon",
            "required_visible_conclusion": (
                f"No fully supported {copy['event']} window is established; the strongest calculated window is conditional{dated_window}."
                if qualified and available_window else copy["none"]
            ),
            "next_window": dict(next_window or {}) if qualified else {},
            "rule": "A complete but qualified or pressured KP judgment is not affirmative fructification and must never be promoted to a supportive event window.",
        }
    if next_event_request:
        start = str((next_window or {}).get("start") or "").strip()
        end = str((next_window or {}).get("end") or "").strip()
        dated_window = f" from {start} to {end}" if start and end else ""
        return {
            "event": copy["event"],
            "question_scope": "next_event_window",
            "requested_period_supportive": False,
            "next_supported_window_available": available_window,
            "decision": (
                "next_supported_window_identified"
                if available_window else "no_supported_window_found_in_evaluated_horizon"
            ),
            "required_visible_conclusion": (
                f"The next fully supported {copy['event']} window is{dated_window}."
                if available_window else copy["none"]
            ),
            "next_window": dict(next_window or {}),
            "rule": "This is an open-ended when question. Lead with the next calculated event window; never describe the scan-anchor date as a requested period.",
        }
    decision = (
        copy["supported_decision"]
        if requested_period_supportive
        else "wait_for_next_supported_window"
        if available_window
        else "no_supported_window_found_in_evaluated_horizon"
    )
    conclusion = copy["supported"] if requested_period_supportive else copy["wait"] if available_window else copy["none"]
    return {
        "event": copy["event"],
        "requested_period_supportive": requested_period_supportive,
        "next_supported_window_available": available_window,
        "decision": decision,
        "required_visible_conclusion": conclusion,
        "next_window": dict(next_window or {}),
        "rule": "Answer the requested period for this exact event. Do not substitute ownership, purchase, sale, possession, construction, relocation or vehicle language from another route.",
    }


def _material_natal_factors(row: Mapping[str, Any], *, limit: int = 12) -> list[dict[str, Any]]:
    """Keep the strongest supplied natal facts without interpreting new astrology."""
    factors = [dict(item) for item in row.get("factors") or [] if isinstance(item, Mapping)]
    factors.sort(key=lambda item: abs(float(item.get("weight") or 0)), reverse=True)
    return factors[:limit]


def _focus_house_bundle(
    house: int,
    *,
    natal_by_house: Mapping[int, Mapping[str, Any]],
    d1_by_house: Mapping[int, Mapping[str, Any]],
    d4_by_house: Mapping[int, Mapping[str, Any]],
    d16_by_house: Mapping[int, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    natal = dict(natal_by_house.get(house) or {})
    return {
        "house": house,
        "natal_summary": {
            key: natal.get(key)
            for key in (
                "lord", "occupants", "aspecting_planets", "karakas", "yogas",
                "tone", "supportive_weight", "challenging_weight",
            )
            if natal.get(key) not in (None, "", [], (), {})
        },
        "material_natal_factors": _material_natal_factors(natal),
        "d1_lord_and_house_condition": dict(d1_by_house.get(house) or {}),
        "d4_lord_and_house_condition": dict(d4_by_house.get(house) or {}),
        "d16_lord_and_house_condition": dict((d16_by_house or {}).get(house) or {}),
    }


def _date(value: Any) -> date | None:
    try:
        return datetime.fromisoformat(str(value or "")[:10]).date()
    except (TypeError, ValueError):
        return None


def _average_score(rows: list[Mapping[str, Any]]) -> float:
    available = [row for row in rows if row.get("available")]
    return sum(float(row.get("score") or 0) for row in available) / len(available) if available else 0.0


def _branch(
    name: str,
    *,
    primary: tuple[int, ...],
    supporting: tuple[int, ...],
    by_house: Mapping[int, Mapping[str, Any]],
    d4_by_house: Mapping[int, Mapping[str, Any]],
    d16_by_house: Mapping[int, Mapping[str, Any]] | None,
    evidence_by_house: Mapping[int, Mapping[str, Any]],
    rule: str,
    require_d16: bool = False,
) -> dict[str, Any]:
    primary_d1 = [by_house.get(house, {}) for house in primary]
    primary_d4 = [d4_by_house.get(house, {}) for house in primary]
    support_d1 = [by_house.get(house, {}) for house in supporting]
    support_d4 = [d4_by_house.get(house, {}) for house in supporting]
    primary_d16 = [(d16_by_house or {}).get(house, {}) for house in primary]
    support_d16 = [(d16_by_house or {}).get(house, {}) for house in supporting]
    score = (
        _average_score(primary_d1)
        + 0.6 * _average_score(primary_d4)
        + 0.35 * _average_score(support_d1)
        + 0.2 * _average_score(support_d4)
        + 0.6 * _average_score(primary_d16)
        + 0.2 * _average_score(support_d16)
    )
    evidence_complete = (
        all((by_house.get(house) or {}).get("available") for house in primary)
        and bool((d4_by_house.get(4) or {}).get("available"))
        and (not require_d16 or bool(((d16_by_house or {}).get(4) or {}).get("available")))
    )
    return {
        "name": name,
        "primary_houses": list(primary),
        "supporting_houses": list(supporting),
        "score": round(score, 3),
        "verdict": (
            "not_established" if not evidence_complete
            else "supportive" if score >= 1.0
            else "qualified" if score >= -0.25
            else "pressured"
        ),
        "evidence_complete": evidence_complete,
        "evidence_ledger": [dict(evidence_by_house.get(house) or {}) for house in dict.fromkeys((*primary, *supporting))],
        "rule": rule,
    }


def _compare_options(options: Mapping[str, Mapping[str, Any]], *, rule: str) -> dict[str, Any]:
    ranked = sorted(
        ({"option": key, **dict(value)} for key, value in options.items()),
        key=lambda row: (-float(row.get("score") or 0), str(row.get("option"))),
    )
    if not ranked or any(not row.get("evidence_complete") for row in ranked):
        direction, winner, margin = "not_established", None, 0.0
    elif len(ranked) == 1:
        direction, winner, margin = "single_path", ranked[0]["option"], float(ranked[0].get("score") or 0)
    else:
        margin = float(ranked[0].get("score") or 0) - float(ranked[1].get("score") or 0)
        direction = "close_or_hybrid" if margin < 0.45 else "leans_to_option"
        winner = None if direction == "close_or_hybrid" else ranked[0]["option"]
    return {
        "direction": direction,
        "favored_option": winner,
        "margin": round(margin, 3),
        "ranked_options": ranked,
        "rule": rule,
    }


def _kp_adjudication(
    kp: Mapping[str, Any], *, primary_cusps: tuple[int, ...], success_houses: set[int], pressure_houses: set[int],
) -> dict[str, Any]:
    cusp_lords = kp.get("cusp_lords") if isinstance(kp.get("cusp_lords"), Mapping) else {}
    significators = kp.get("planet_significators") if isinstance(kp.get("planet_significators"), Mapping) else {}
    judgments = []
    for cusp in primary_cusps:
        cusp_row = cusp_lords.get(cusp) or cusp_lords.get(str(cusp)) or {}
        sub_lord = str(cusp_row.get("sub_lord") or "") if isinstance(cusp_row, Mapping) else ""
        signified = {_as_int(value) for value in significators.get(sub_lord) or []}
        signified.discard(None)
        support = sorted(int(value) for value in signified & success_houses)
        pressure = sorted(int(value) for value in signified & pressure_houses)
        judgments.append({
            "cusp": cusp,
            "sub_lord": sub_lord or None,
            "sub_lord_signifies": sorted(int(value) for value in signified),
            "success_house_links": support,
            "pressure_house_links": pressure,
            "supports_route": bool(support) and len(support) >= len(pressure),
        })
    complete = bool(judgments) and all(row.get("sub_lord") for row in judgments)
    supported = sum(1 for row in judgments if row.get("supports_route"))
    return {
        "complete": complete,
        "verdict": (
            "not_established" if not complete else "supported" if supported == len(judgments)
            else "qualified" if supported else "pressured"
        ),
        "supported_cusps": supported,
        "required_cusps": len(judgments),
        "cusp_judgments": judgments,
        "rule": "KP must link the route's relevant cusp sub-lords to its result houses; merely calculating a KP chart is not fructification.",
    }


def _timing_windows(
    normalized: Mapping[str, Any], *, success_houses: set[int], required_event_houses: set[int], period_window: Mapping[str, Any] | None,
    retrospective: bool,
) -> list[dict[str, Any]]:
    source_key = "historical_event_dasha_scan" if retrospective else "forward_event_dasha_scan"
    source = normalized.get(source_key)
    rows = source.get("periods") or source.get("ranked_windows") or [] if isinstance(source, Mapping) else []
    period_kind = str((period_window or {}).get("kind") or "")
    # Event prediction uses a one-day "current" anchor for the authoritative
    # dasha display while its forward scan intentionally covers the horizon.
    # That anchor must not erase every future candidate.
    requested_start = _date((period_window or {}).get("start")) if retrospective or period_kind != "current" else None
    requested_end = _date((period_window or {}).get("end")) if retrospective or period_kind != "current" else None
    ranked = []
    for value in rows:
        if not isinstance(value, Mapping):
            continue
        start = _date(value.get("start") or value.get("start_date"))
        end = _date(value.get("end") or value.get("end_date"))
        if requested_start and end and end < requested_start:
            continue
        if requested_end and start and start > requested_end:
            continue
        activated = {_as_int(item) for item in value.get("activated_focus_houses") or value.get("active_houses") or []}
        activated.discard(None)
        coverage = sorted(int(item) for item in activated & success_houses)
        transit_peaks = []
        for peak in value.get("transit_trigger_windows") or value.get("peak_activation_windows") or []:
            if not isinstance(peak, Mapping):
                continue
            delivered_rows = peak.get("delivered_event_houses")
            if isinstance(delivered_rows, list):
                delivered_houses = {
                    _as_int(item.get("house") if isinstance(item, Mapping) else item)
                    for item in delivered_rows
                }
                delivered_houses.discard(None)
                route_transit_houses = delivered_houses & success_houses
            else:
                # Compatibility for older scan rows that predate the explicit
                # delivery ledger. New rows must deliver to a route house; a
                # natal sign/nakshatra return alone is not event confirmation.
                route_transit_houses = {
                    _as_int(item) for item in peak.get("activated_focus_houses") or []
                } & success_houses
            if not route_transit_houses:
                continue
            peak_start = _date(peak.get("start"))
            peak_end = _date(peak.get("end")) or peak_start
            if requested_start and peak_end and peak_end < requested_start:
                continue
            if requested_end and peak_start and peak_start > requested_end:
                continue
            transit_peaks.append({**dict(peak), "route_transit_houses": sorted(route_transit_houses)})
        transit_peaks.sort(
            key=lambda peak: (
                -len(peak.get("route_transit_houses") or []),
                -int(peak.get("trigger_score") or 0),
                str(peak.get("start") or ""),
            )
        )
        if len(coverage) < 2 or not required_event_houses.issubset(activated) or not transit_peaks:
            continue
        ranked.append({
            **dict(value),
            "route_success_houses": sorted(success_houses),
            "route_success_coverage": coverage,
            "coverage_count": len(coverage),
            "transit_confirmed": True,
            "route_peak_windows": transit_peaks[:4],
            "dasha_activation": {
                "mahadasha": value.get("mahadasha"),
                "antardasha": value.get("antardasha"),
                "pratyantardasha": value.get("pratyantardasha"),
                "activated_houses": coverage,
                "carrier_planets": [
                    dict(row) for row in value.get("carrier_planets") or []
                    if isinstance(row, Mapping)
                ],
                "mechanism": value.get("why"),
            },
            "transit_confirmation": [
                {
                    key: peak.get(key)
                    for key in (
                        "start", "end", "planet", "strength", "trigger_score",
                        "transit_native_house", "natal_placement_house",
                        "delivered_event_houses", "activated_focus_houses", "why",
                    )
                    if peak.get(key) not in (None, "", [], {})
                }
                for peak in transit_peaks[:4]
            ],
            "claim_rule": "This is a calculated event-activation window, not a guaranteed event, approval, transaction, possession or legal outcome.",
        })
    return sorted(
        ranked,
        key=lambda row: (-int(row.get("coverage_count") or 0), -int(row.get("transit_trigger_score") or 0), -float(row.get("relevance_score") or 0)),
    )[:8]


def _as_int(value: Any) -> int | None:
    try: return int(value)
    except (TypeError, ValueError): return None


def _planet_map(chart: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(k): dict(v) for k, v in (chart.get("planets") or {}).items() if isinstance(v, Mapping)}


def _houses(chart: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    return {_as_int(row.get("house")): dict(row) for row in chart.get("houses") or [] if isinstance(row, Mapping) and _as_int(row.get("house"))}


def _chart_for(chart_data: Mapping[str, Any], code: str, normalized_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    charts = chart_data.get("charts") if isinstance(chart_data.get("charts"), Mapping) else {}
    if isinstance(charts.get(code), Mapping):
        return dict(charts[code])
    facts = (normalized_evidence or {}).get("chart_facts") if isinstance((normalized_evidence or {}).get("chart_facts"), Mapping) else {}
    calculated = facts.get("charts") if isinstance(facts.get("charts"), Mapping) else {}
    if isinstance(calculated.get(code), Mapping):
        return dict(calculated[code])
    return {"planets": chart_data.get("planets") or {}, "houses": chart_data.get("houses") or []} if code == "D1" else {}


def _house_row(chart: Mapping[str, Any], house: int) -> dict[str, Any]:
    rows = _houses(chart)
    if house in rows: return rows[house]
    asc = _as_int(chart.get("ascendant"))
    if asc is None: asc = _as_int(chart.get("ascendant_longitude"))
    if asc is None: return {}
    sign_index = int(asc // 30) % 12
    sign_index = (sign_index + house - 1) % 12
    return {"house": house, "sign": sign_index, "lord": _SIGN_LORDS[sign_index], "occupants": []}


def _condition(chart_code: str, chart: Mapping[str, Any], house: int) -> dict[str, Any]:
    row = _house_row(chart, house)
    planets = _planet_map(chart)
    lord = str(row.get("lord") or "")
    p = planets.get(lord) or {}
    if not lord or not p:
        return {"chart": chart_code, "house": house, "available": False, "support": [], "cautions": []}
    placement = _as_int(p.get("house"))
    dignity = str(p.get("dignity") or "").lower()
    score = _DIGNITY.get(dignity, 0.0)
    support: list[str] = []
    cautions: list[str] = []
    if dignity in {"exalted", "mooltrikona", "own_sign", "friendly_sign", "friend_sign"}: support.append(f"{chart_code}: H{house} lord {lord} is {dignity}")
    if dignity in {"debilitated", "enemy_sign"}: cautions.append(f"{chart_code}: H{house} lord {lord} is {dignity}")
    if placement in {1, 2, 4, 5, 7, 9, 10, 11}:
        score += 1.0; support.append(f"{chart_code}: H{house} lord {lord} is in H{placement}")
    elif placement in {6, 8, 12}:
        score -= 0.8; cautions.append(f"{chart_code}: H{house} lord {lord} is in H{placement}")
    occupants = [str(x) for x in row.get("occupants") or []]
    if not occupants:
        occupants = [name for name, item in planets.items() if _as_int(item.get("house")) == house]
    for planet in occupants:
        if planet in {"Jupiter", "Venus", "Moon"}: score += 0.45; support.append(f"{chart_code}: {planet} occupies H{house}")
        elif planet in _PRESSURE: score -= 0.35; cautions.append(f"{chart_code}: {planet} occupies H{house}; this qualifies the result")
    aspectors = []
    for name, item in planets.items():
        if house in [int(value) for value in item.get("aspects_to_houses") or [] if str(value).isdigit()]:
            tone = str(item.get("functional_nature") or item.get("natural_nature") or "")
            aspectors.append({"planet": name, "tone": tone})
            if "benefic" in tone and "malefic" not in tone:
                score += 0.25; support.append(f"{chart_code}: {name} gives a supportive aspect to H{house}")
            elif "malefic" in tone or name in _PRESSURE:
                score -= 0.25; cautions.append(f"{chart_code}: {name} gives a challenging aspect to H{house}")
    return {"chart": chart_code, "house": house, "available": True, "lord": lord, "lord_house": placement, "lord_sign": p.get("sign"), "lord_dignity": dignity or None, "lord_aspects_received": p.get("aspects_received") or [], "lord_conjunctions": p.get("conjunctions") or [], "occupants": occupants, "house_aspects": aspectors, "score": round(score, 2), "support": support, "cautions": cautions}


_VEHICLE_PLANET_COLORS: dict[str, tuple[str, ...]] = {
    "Sun": ("gold", "copper", "warm red"),
    "Moon": ("white", "silver", "pearl"),
    "Mars": ("red", "maroon"),
    "Mercury": ("green", "teal"),
    "Jupiter": ("yellow", "gold", "cream"),
    "Venus": ("white", "silver", "light blue"),
    "Saturn": ("navy", "black", "charcoal"),
    "Rahu": ("smoky grey", "electric blue"),
    "Ketu": ("brown", "matte grey"),
}


def _vehicle_color_synthesis(
    d1: Mapping[str, Any],
    d16: Mapping[str, Any],
    d1_h4: Mapping[str, Any],
    d16_h4: Mapping[str, Any],
) -> dict[str, Any]:
    """Rank colour families from actual D1/D16 vehicle carriers."""
    evidence_complete = bool(d1_h4.get("available") and d16_h4.get("available"))
    carrier_scores: dict[str, float] = {}
    carrier_reasons: dict[str, list[str]] = {}

    def add(planet: Any, weight: float, reason: str) -> None:
        name = str(planet or "").strip()
        if name not in _VEHICLE_PLANET_COLORS:
            return
        carrier_scores[name] = carrier_scores.get(name, 0.0) + weight
        carrier_reasons.setdefault(name, []).append(reason)

    add(d1_h4.get("lord"), 2.0, "D1 House 4 lord")
    add(d16_h4.get("lord"), 3.0, "D16 House 4 lord")
    add("Venus", 1.5, "natural vehicle and comfort significator")
    for label, chart, h4 in (("D1", d1, d1_h4), ("D16", d16, d16_h4)):
        for planet in h4.get("occupants") or []:
            add(planet, 1.0, f"{label} House 4 occupant")
        for row in h4.get("house_aspects") or []:
            if not isinstance(row, Mapping):
                continue
            tone = str(row.get("tone") or "").lower()
            add(row.get("planet"), -0.5 if "malefic" in tone else 0.4, f"{label} House 4 aspect")
        for planet, row in _planet_map(chart).items():
            if planet not in carrier_scores:
                continue
            dignity = str(row.get("dignity") or "").lower()
            adjustment = _DIGNITY.get(dignity, 0.0) * 0.35
            if adjustment:
                add(planet, adjustment, f"{label} {dignity}")

    color_scores: dict[str, float] = {}
    color_carriers: dict[str, list[str]] = {}
    for planet, score in carrier_scores.items():
        for rank, color in enumerate(_VEHICLE_PLANET_COLORS[planet]):
            color_scores[color] = color_scores.get(color, 0.0) + score * (1.0 - 0.15 * rank)
            color_carriers.setdefault(color, []).append(planet)
    ranked = sorted(color_scores, key=lambda color: (-color_scores[color], color))
    return {
        "attribute": "exterior_colour_family",
        "verdict": "ranked_palette" if evidence_complete and ranked else "not_established",
        "evidence_complete": evidence_complete,
        "recommended_colors": [
            {
                "color": color,
                "score": round(color_scores[color], 3),
                "carriers": list(dict.fromkeys(color_carriers[color])),
            }
            for color in ranked[:4]
        ],
        "carrier_scores": [
            {"planet": planet, "score": round(score, 3), "reasons": carrier_reasons.get(planet, [])}
            for planet, score in sorted(carrier_scores.items(), key=lambda item: (-item[1], item[0]))
        ],
        "required_visible_conclusion": (
            f"The strongest calculated vehicle colour family is {ranked[0]}, with {', '.join(ranked[1:3])} as secondary options."
            if evidence_complete and ranked else
            "A chart-based vehicle colour recommendation is not established because the required D1/D16 evidence is incomplete."
        ),
        "rule": "Rank colour families only from the actual D1 House 4, D16 House 4 and Venus carriers. Present them as preferences, not guarantees, and do not introduce purchase timing.",
    }


def _home_fact_contract(
    *,
    d1_ascendant: Mapping[str, Any],
    d1_fourth: Mapping[str, Any],
    d4_fourth: Mapping[str, Any],
    d16_fourth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return role-safe facts for the answer writer.

    A fluent answer must never turn an occupant into a house lord or an aspect
    received by a planet into an aspect on the house.  Keeping those roles in
    separate immutable fields also gives the multilingual composer one small,
    authoritative ledger instead of asking it to infer roles from prose.
    """
    def house_fact(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "available": bool(row.get("available")),
            "lord": row.get("lord"),
            "lord_house": row.get("lord_house"),
            "lord_sign": row.get("lord_sign"),
            "lord_dignity": row.get("lord_dignity"),
            "occupants": list(row.get("occupants") or []),
            "house_aspectors": [
                item.get("planet")
                for item in row.get("house_aspects") or []
                if isinstance(item, Mapping) and item.get("planet")
            ],
            "lord_aspects_received": list(row.get("lord_aspects_received") or []),
            "lord_conjunctions": list(row.get("lord_conjunctions") or []),
            "support": list(row.get("support") or []),
            "cautions": list(row.get("cautions") or []),
        }

    d1 = house_fact(d1_fourth)
    d4 = house_fact(d4_fourth)
    d16 = house_fact(d16_fourth or {})
    ascendant_lord = d1_ascendant.get("lord") if d1_ascendant.get("available") else None
    marker_d1 = (
        "[[HOME_D1_H4:"
        f"LORD={d1.get('lord') or 'none'};"
        f"LORD_HOUSE={d1.get('lord_house') or 'none'};"
        f"OCCUPANTS={','.join(d1.get('occupants') or []) or 'none'};"
        f"ASPECTORS={','.join(d1.get('house_aspectors') or []) or 'none'}]]"
    ) if d1.get("available") else ""
    marker_d4 = (
        "[[HOME_D4_H4:"
        f"LORD={d4.get('lord') or 'none'};"
        f"LORD_HOUSE={d4.get('lord_house') or 'none'};"
        f"OCCUPANTS={','.join(d4.get('occupants') or []) or 'none'};"
        f"ASPECTORS={','.join(d4.get('house_aspectors') or []) or 'none'}]]"
    ) if d4.get("available") else ""
    marker_d16 = (
        "[[HOME_D16_H4:"
        f"LORD={d16.get('lord') or 'none'};"
        f"LORD_HOUSE={d16.get('lord_house') or 'none'};"
        f"OCCUPANTS={','.join(d16.get('occupants') or []) or 'none'};"
        f"ASPECTORS={','.join(d16.get('house_aspectors') or []) or 'none'}]]"
    ) if d16.get("available") else ""
    return {
        "schema_version": "home-property-facts/v1",
        "d1_ascendant_lord": ascendant_lord,
        "d1_fourth_house": d1,
        "d4_fourth_house": d4,
        "d16_fourth_house": d16,
        "validation_markers": [marker for marker in (marker_d1, marker_d4, marker_d16) if marker],
        "role_rules": [
            "A House 4 occupant is not the House 4 lord unless the lord field independently names the same planet.",
            "house_aspectors is the complete allowed list of planets aspecting House 4.",
            "lord_aspects_received applies to the lord planet, not automatically to House 4.",
            "The D1 and D4 records are different charts and must never be merged.",
            "D16 is the vehicle-and-comfort confirmation chart; never describe it as a property chart.",
        ],
    }


def build_home_foundation(*, chart_data: Mapping[str, Any], normalized_evidence: Mapping[str, Any], category: Any, answer_mode: Any, home_subtype: Any = None, kp_evidence: Mapping[str, Any] | None = None, natal_topic_factors: Mapping[str, Any] | None = None, period_window: Mapping[str, Any] | None = None) -> dict[str, Any]:
    subtype = normalize_home_subtype(home_subtype)
    profile = home_profile(category, subtype)
    if subtype in BOUNDARY_HOME_SUBTYPES:
        return {"home_subtype": subtype, "scope": "boundary handoff", "houses_available": [], "availability": {"scope_boundary": True}}
    d1, d4 = _chart_for(chart_data, "D1", normalized_evidence), _chart_for(chart_data, "D4", normalized_evidence)
    d16 = _chart_for(chart_data, "D16", normalized_evidence) if subtype.startswith("vehicle_") else {}
    d1_ascendant = _condition("D1", d1, 1)
    rows = [_condition("D1", d1, house) for house in profile["houses"]]
    d4_rows = [_condition("D4", d4, house) for house in profile["houses"]] if d4 else []
    d16_rows = [_condition("D16", d16, house) for house in profile["houses"]] if d16 else []
    available = [row["house"] for row in rows if row.get("available")]
    supports = [item for row in rows + d4_rows + d16_rows for item in row.get("support") or []]
    cautions = [item for row in rows + d4_rows + d16_rows for item in row.get("cautions") or []]
    score = sum(float(row.get("score") or 0) for row in rows) + 0.6 * sum(float(row.get("score") or 0) for row in d4_rows + d16_rows)
    verdict = "supportive" if score >= 2 else "qualified" if score >= -0.5 else "pressured"
    remedy = normalized_evidence.get("remedy_blueprint") if isinstance(normalized_evidence.get("remedy_blueprint"), Mapping) else {}
    natal_promise = natal_topic_factors if isinstance(natal_topic_factors, Mapping) else {}
    by_house = {int(row["house"]): row for row in rows if row.get("house") is not None}
    d4_by_house = {int(row["house"]): row for row in d4_rows if row.get("house") is not None}
    d16_by_house = {int(row["house"]): row for row in d16_rows if row.get("house") is not None}
    natal_by_house = {
        int(row.get("house")): dict(row)
        for row in natal_promise.get("houses") or []
        if isinstance(row, Mapping) and _as_int(row.get("house")) is not None
    }
    if subtype == "property_remedy":
        remedy = build_classical_property_remedy_blueprint(
            d1_conditions=rows,
            d4_conditions=d4_rows,
            natal_factors_by_house={
                house: [dict(item) for item in row.get("factors") or [] if isinstance(item, Mapping)]
                for house, row in natal_by_house.items()
            },
        )
    focus_house_evidence = [
        _focus_house_bundle(
            house,
            natal_by_house=natal_by_house,
            d1_by_house=by_house,
            d4_by_house=d4_by_house,
            d16_by_house=d16_by_house,
        )
        for house in profile["houses"]
    ]
    evidence_by_house = {int(row["house"]): row for row in focus_house_evidence}
    def branch(name: str, primary: tuple[int, ...], supporting: tuple[int, ...], rule: str) -> dict[str, Any]:
        return _branch(
            name,
            primary=primary,
            supporting=supporting,
            by_house=by_house,
            d4_by_house=d4_by_house,
            d16_by_house=d16_by_house,
            evidence_by_house=evidence_by_house,
            rule=rule,
            require_d16=subtype.startswith("vehicle_"),
        )

    core_home = branch(
        "home and property foundation", (4,), tuple(house for house in profile["houses"] if house != 4),
        "House 4, its lord, occupants and aspects establish the D1 foundation; D4 H4 independently confirms or qualifies it. Supporting houses answer the specific route but cannot replace H4.",
    )
    route_synthesis: dict[str, Any] = dict(core_home)
    comparison_synthesis: dict[str, Any] = {}
    finance_synthesis: dict[str, Any] = {}
    obstacle_synthesis: dict[str, Any] = {}

    if subtype == "property_potential":
        route_synthesis = branch("property ownership potential", (4, 11), (2, 9), "Ownership requires property promise H4 plus realization H11; resources H2 and fortune/support H9 qualify whether the promise can materialize.")
    elif subtype == "property_purchase":
        route_synthesis = branch("property purchase suitability", (4, 11), (2, 9), "A purchase decision needs H4 property promise and H11 realization, qualified by resources H2 and support H9; timing is a separate route.")
    elif subtype == "property_finance":
        resource = branch("property and repayment capacity", (2, 11), (4, 6), "Resources and gains must support both the property and the work of repayment.")
        liability = branch("debt and leakage pressure", (6, 8, 12), (2, 11), "H6 debt, H8 shared liability and H12 outflow are read as a separate pressure ledger, not mistaken for purchase promise.")
        finance_synthesis = {"resource_capacity": resource, "liability_pressure": liability, "rule": "Keep affordability, repayment capacity, shared liability and cash outflow separate; astrology cannot replace lender affordability checks."}
        route_synthesis = {"verdict": "two_sided_finance_assessment", "evidence_complete": resource["evidence_complete"] and liability["evidence_complete"], **finance_synthesis}
    elif subtype == "property_sale_decision":
        comparison_synthesis = _compare_options({
            "retain": branch("retain property", (4, 2), (9, 11), "Retention needs a sustainable H4 asset supported by resources and longer-term gain."),
            "sell": branch("sell property", (3, 8, 11), (4, 2), "Sale needs separation/documents H3, transfer H8 and realization H11, qualified by the H4 asset and H2 resources."),
        }, rule="Compare holding and selling as separate natal decisions. If the user asks when or names a period, use the sale-timing route instead.")
        route_synthesis = comparison_synthesis
    elif subtype == "property_comparison":
        comparison_synthesis = _compare_options({
            "buy": branch("buy", (4, 11), (2, 9), "Buying needs owned-property promise and realization, backed by resources."),
            "rent": branch("rent", (3, 12), (4, 2), "Renting is evaluated through mobility H3 and recurring residence outflow H12 while preserving H4 comfort and H2 affordability."),
        }, rule="Compare buying and renting as separate complete branches; never infer renting merely from weak ownership or buying merely from a strong H4.")
        route_synthesis = comparison_synthesis
    elif subtype == "property_type_fit":
        comparison_synthesis = _compare_options({
            "land_or_independent_property": branch("land or independent property", (4, 9), (2, 8, 11), "Land/independent property emphasizes fixed property H4, ground/expansion H9 and construction/shared-risk qualification."),
            "flat_or_managed_residence": branch("flat or managed residence", (4, 11), (2, 12), "A flat/managed residence emphasizes home comfort H4, community realization H11, affordability H2 and recurring outflow H12."),
            "commercial_property_as_asset": branch("commercial property as an asset", (4, 11), (2, 8, 12), "Commercial property in this graph is assessed only as a personal asset; operating a real-estate business is a Career/Wealth handoff."),
        }, rule="Rank each named property type through a distinct ledger; do not give every option the same H4 explanation.")
        route_synthesis = comparison_synthesis
    elif subtype == "joint_property":
        sole = branch("sole ownership", (4, 2), (9, 11), "Sole ownership emphasizes personal resources and property promise.")
        joint = branch("joint ownership", (4, 7, 8), (2, 11), "Joint ownership must add partnership H7 and shared assets/liability H8 to property H4 and realization H11.")
        comparison_synthesis = _compare_options({"sole_ownership": sole, "joint_ownership": joint}, rule="Compare sole and joint ownership separately; a spouse cannot be judged without the spouse's chart, so this assesses only the native's co-ownership pattern.")
        comparison_synthesis["asked_option_assessment"] = {
            "option": "joint_ownership",
            "verdict": joint.get("verdict"),
            "score": joint.get("score"),
            "evidence_complete": joint.get("evidence_complete"),
            "relative_to_alternative": (
                "less_supported_than_sole_ownership"
                if comparison_synthesis.get("favored_option") == "sole_ownership"
                else "more_supported_than_sole_ownership"
                if comparison_synthesis.get("favored_option") == "joint_ownership"
                else "close_to_sole_ownership"
            ),
            "required_visible_conclusion": (
                "Joint ownership is not established from the available D1/D4 evidence."
                if not joint.get("evidence_complete")
                else "Joint ownership is supported, but sole ownership has the stronger calculated fit."
                if joint.get("verdict") == "supportive" and comparison_synthesis.get("favored_option") == "sole_ownership"
                else "Joint ownership is supported and has the stronger calculated fit."
                if joint.get("verdict") == "supportive" and comparison_synthesis.get("favored_option") == "joint_ownership"
                else "Joint ownership is supported, with little calculated difference from sole ownership."
                if joint.get("verdict") == "supportive"
                else "Joint ownership is possible only with conditions; shared liability and partnership factors need caution."
                if joint.get("verdict") == "qualified"
                else "Joint ownership is pressured in the calculated comparison; do not present it as favourable."
            ),
            "scope_boundary": "This judges the native's co-ownership pattern only; it does not judge a spouse or family member without that person's chart.",
        }
        route_synthesis = comparison_synthesis
    elif subtype == "rental_income":
        route_synthesis = branch("rental-income potential", (4, 11), (2, 6, 8, 12), "Rental income requires an asset H4 and realized gains H11, qualified by income retention H2, tenancy/service H6, shared risk H8 and expenses H12.")
    elif subtype == "construction_renovation":
        route_synthesis = branch("construction or renovation suitability", (3, 4), (2, 8, 11, 12), "Construction/renovation combines initiative and execution H3 with property H4, then checks resources, disruption, completion and outflow through H2/H8/H11/H12.")
    elif subtype == "construction_timing":
        route_synthesis = branch("construction or renovation promise", (3, 4, 11), (2, 8, 12), "Timed construction requires execution H3, property H4 and completion H11, qualified by resources, disruption and outflow.")
    elif subtype == "relocation_home":
        roots = branch("remain rooted", (4,), (2, 11), "Remaining rooted is led by H4 continuity with family/resources and support.")
        move = branch("domestic relocation", (3, 12), (4, 9, 11), "Domestic relocation requires movement H3 and leaving/changing residence H12, qualified by H4, distance H9 and successful transition H11.")
        comparison_synthesis = _compare_options({"remain_rooted": roots, "domestic_relocation": move}, rule="Compare staying and moving separately; this route does not decide foreign settlement or name a location.")
        route_synthesis = comparison_synthesis
    elif subtype == "relocation_timing":
        route_synthesis = branch("domestic relocation promise", (3, 12, 11), (4, 9), "Timed domestic relocation requires movement H3, change of residence H12 and realization H11, qualified by H4 and distance H9.")
    elif subtype == "property_obstacles":
        delays = {
            "documents_and_execution": branch("documents and execution", (3, 6), (4, 11), "H3/H6 isolate paperwork, effort and procedural obstruction."),
            "asset_and_title_complexity": branch("asset and title complexity", (4, 8), (3, 11), "H4/H8 isolate property transition and hidden/shared complications without predicting a legal outcome."),
            "expense_or_release_pressure": branch("expense or release pressure", (12,), (2, 4, 11), "H12 isolates leakage, delay or the need to release an unsuitable plan."),
        }
        ranked_delays = sorted(({"mechanism": key, **value} for key, value in delays.items()), key=lambda row: (float(row.get("score") or 0), str(row.get("mechanism"))))
        obstacle_synthesis = {"verdict": "relative_pressures_ranked", "dominant_pressure": ranked_delays[0]["mechanism"] if ranked_delays else None, "ranked_pressures": ranked_delays, "rule": "Diagnose the strongest repeated D1/D4 pressure mechanism; do not turn delay into denial or a property/legal outcome."}
        route_synthesis = obstacle_synthesis
    elif subtype == "vehicle_potential":
        route_synthesis = branch("vehicle ownership potential", (4, 11), (2, 12), "Vehicle comfort and ownership are led by H4 and Venus, with H11 realization, H2 affordability and H12 expenditure qualification.")
    elif subtype == "vehicle_selection":
        route_synthesis = _vehicle_color_synthesis(
            d1,
            d16,
            dict(by_house.get(4) or {}),
            dict(d16_by_house.get(4) or {}),
        )
    elif subtype == "property_portfolio_comparison":
        comparison_synthesis = _compare_options({
            "retain_current_property": branch("retain current property", (4, 2), (9, 11), "Retention emphasizes stable asset holding and resources."),
            "sell_property": branch("sell property", (3, 8, 11), (4, 2), "Sale requires separation/documentation H3, asset transition H8 and realization H11."),
            "buy_replacement_property": branch("buy replacement property", (4, 11), (2, 9, 12), "Replacement purchase needs property and realization plus funding, support and outflow."),
        }, rule="A sell-and-buy question is three decisions—retain, sell and replace—and each must be evaluated separately.")
        route_synthesis = comparison_synthesis
    elif subtype == "possession_documentation_timing":
        route_synthesis = branch("possession and documentation promise", (3, 4, 11), (6, 8), "Documents H3, property H4 and delivery H11 must align; obstruction H6 and complications H8 qualify possession.")
    elif subtype == "property_sale_timing":
        route_synthesis = branch("property sale promise", (3, 8, 11), (4,), "Sale requires separation/documents H3, transfer H8 and realization H11 while preserving the underlying H4 asset evidence.")
    elif subtype in {"property_purchase_timing", "retrospective_property_timing"}:
        route_synthesis = branch("property acquisition promise", (4, 11), (2, 9), "Acquisition timing can operate only when H4 property and H11 realization are supported by H2/H9.")
    elif subtype == "vehicle_timing":
        route_synthesis = branch("vehicle acquisition promise", (4, 11), (2, 12), "Vehicle timing requires D1 House 4 and Venus with H11 realization, independently confirmed by D16; H2 resources and H12 expenditure qualify the purchase.")
    elif subtype == "property_remedy":
        route_synthesis = {"verdict": "calculated_remedy" if remedy.get("top_recommendation") else "not_established", "top_recommendation": remedy.get("top_recommendation"), "alternatives": list(remedy.get("alternatives") or [])[:3], "evidence_complete": bool(remedy.get("top_recommendation")), "rule": "Use only the calculated remedy tied to the diagnosed Home/Property pressure; never invent a generic planetary remedy."}
    natal_h4 = dict(natal_by_house.get(4) or {})
    d1_h4 = dict(by_house.get(4) or {})
    d4_h4 = dict(d4_by_house.get(4) or {})
    immutable_fact_contract = _home_fact_contract(
        d1_ascendant=d1_ascendant,
        d1_fourth=d1_h4,
        d4_fourth=d4_h4,
        d16_fourth=dict(d16_by_house.get(4) or {}),
    )
    visible_facts = [
        *d1_h4.get("support", []), *d1_h4.get("cautions", []),
        *d4_h4.get("support", []), *d4_h4.get("cautions", []),
    ]
    if subtype == "living_arrangement":
        def ledger(houses: tuple[int, ...]) -> list[dict[str, Any]]:
            return [
                _focus_house_bundle(
                    house,
                    natal_by_house=natal_by_house,
                    d1_by_house=by_house,
                    d4_by_house=d4_by_house,
                )
                for house in houses
            ]
        complete_arrangement_evidence = all((by_house.get(h) or {}).get("available") for h in (2, 3, 4, 11, 12)) and bool((d4_by_house.get(4) or {}).get("available"))
        family_score = sum(float((by_house.get(h) or {}).get("score") or 0) for h in (2, 4, 11)) + 0.6 * float((d4_by_house.get(4) or {}).get("score") or 0)
        independent_score = sum(float((by_house.get(h) or {}).get("score") or 0) for h in (3, 4, 12)) + 0.6 * sum(float((d4_by_house.get(h) or {}).get("score") or 0) for h in (4, 12))
        delta = independent_score - family_score
        arrangement = {
            "family_living": {"score": round(family_score, 2), "houses": [2, 4, 11], "evidence_ledger": ledger((2, 4, 11))},
            "independent_living": {"score": round(independent_score, 2), "houses": [3, 4, 12], "evidence_ledger": ledger((3, 4, 12))},
            "evidence_complete": complete_arrangement_evidence,
            "verdict": "unavailable" if not complete_arrangement_evidence else "independent" if delta >= 0.9 else "family" if delta <= -0.9 else "hybrid_or_close",
            "difference": round(delta, 2),
            "required_visible_conclusion": (
                "The living-arrangement comparison is unavailable because its D1/D4 evidence chain is incomplete."
                if not complete_arrangement_evidence else "The calculated comparison is close/hybrid; neither living arrangement has a decisive chart advantage."
                if abs(delta) < 0.9 else
                "Independent living has the stronger calculated support." if delta > 0 else
                "Living with family has the stronger calculated support."
            ),
            "rule": "Family living is weighed through H2/H4/H11; independent living through H3/H4/H12. Both must be qualified by the actual H4 lord, occupants, aspects and D4 H4 condition.",
        }
    else:
        arrangement = {}
    if subtype == "living_arrangement":
        comparison_synthesis = arrangement
        route_synthesis = arrangement
    kp = kp_evidence if isinstance(kp_evidence, Mapping) else (normalized_evidence.get("kp_evidence") if isinstance(normalized_evidence.get("kp_evidence"), Mapping) else {})
    timing_success = {
        "property_purchase_timing": ({2, 4, 9, 11}, {4, 11}, (4, 11), {3, 8, 12}),
        "property_sale_timing": ({3, 4, 8, 11}, {3, 8, 11}, (4, 11), {6, 12}),
        "possession_documentation_timing": ({3, 4, 11}, {4, 11}, (4, 11), {6, 8, 12}),
        "retrospective_property_timing": ({2, 4, 9, 11}, {4, 11}, (4, 11), {3, 8, 12}),
        "vehicle_timing": ({2, 4, 11}, {4, 11}, (4, 11), {6, 8, 12}),
        "construction_timing": ({2, 3, 4, 8, 11, 12}, {3, 4, 11}, (4, 11), {6, 8, 12}),
        "relocation_timing": ({3, 4, 9, 11, 12}, {3, 11, 12}, (4, 12), {6, 8}),
    }
    timing_synthesis: dict[str, Any] = {}
    if subtype in timing_success:
        success_houses, required_event_houses, primary_cusps, pressure_houses = timing_success[subtype]
        kp_route = _kp_adjudication(kp, primary_cusps=primary_cusps, success_houses=success_houses, pressure_houses=pressure_houses)
        windows = _timing_windows(
            normalized_evidence,
            success_houses=success_houses,
            required_event_houses=required_event_houses,
            period_window=period_window,
            retrospective=subtype == "retrospective_property_timing",
        )
        scan_key = "historical_event_dasha_scan" if subtype == "retrospective_property_timing" else "forward_event_dasha_scan"
        scan = normalized_evidence.get(scan_key) if isinstance(normalized_evidence.get(scan_key), Mapping) else {}
        evaluated_rows = [row for row in scan.get("periods") or [] if isinstance(row, Mapping)]
        dasha_evaluation_complete = bool(
            scan.get("dasha_evaluation_complete")
            or evaluated_rows
        )
        transit_evaluation_complete = bool(
            scan.get("transit_evaluation_complete")
            or (
                evaluated_rows
                and all(
                    "transit_trigger_windows" in row
                    or "peak_activation_windows" in row
                    or "transit_trigger_score" in row
                    for row in evaluated_rows
                )
            )
        )
        chronological = sorted(windows, key=lambda row: (_date(row.get("start")) or date.max))
        strongest = max(
            windows,
            key=lambda row: (
                int(row.get("coverage_count") or 0),
                int(row.get("transit_trigger_score") or 0),
                float(row.get("relevance_score") or 0),
            ),
            default={},
        )
        requested_kind = str((period_window or {}).get("kind") or "").strip().lower()
        next_event_request = str((period_window or {}).get("request_semantics") or "").strip().lower() == "next_event_window"
        requested_start = _date((period_window or {}).get("start"))
        requested_end = _date((period_window or {}).get("end")) or requested_start

        def overlaps_requested(value: Mapping[str, Any]) -> bool:
            if requested_start is None:
                return False
            start = _date(value.get("start")) or date.min
            end = _date(value.get("end")) or start
            return start <= (requested_end or requested_start) and end >= requested_start

        requested_period_rows = [dict(row) for row in windows if overlaps_requested(row)]
        requested_transit_rows = [
            dict(peak)
            for row in requested_period_rows
            for peak in row.get("route_peak_windows") or []
            if isinstance(peak, Mapping) and overlaps_requested(peak)
        ]
        current_period = max(
            requested_period_rows,
            key=lambda row: (
                int(row.get("coverage_count") or 0),
                int(row.get("transit_trigger_score") or 0),
                float(row.get("relevance_score") or 0),
            ),
            default={},
        )
        requested_window_assessment = {
            "question_scope": "next_event_window" if next_event_request else "requested_period",
            "kind": requested_kind or None,
            "start": requested_start.isoformat() if requested_start else None,
            "end": requested_end.isoformat() if requested_end else None,
            "dasha_window_matches_requested_period": bool(current_period),
            "transit_confirmation_overlaps_requested_period": bool(requested_transit_rows),
            "supportive_now": bool(not next_event_request and kp_route.get("verdict") == "supported" and current_period and requested_transit_rows),
            "current_period": current_period,
            "current_transit_confirmations": requested_transit_rows[:4],
            "verdict": (
                "missing_kp_fructification" if not kp_route.get("complete")
                else "kp_fructification_not_fully_supportive" if kp_route.get("verdict") != "supported"
                else "next_supported_window_identified" if next_event_request and chronological
                else "no_supported_window_found_in_evaluated_horizon" if next_event_request
                else "supportive_requested_period" if current_period and requested_transit_rows
                else "dasha_support_without_requested_period_transit" if current_period
                else "requested_period_not_triangulated"
            ),
            "rule": (
                "A present-period yes requires a route-capable dasha row overlapping the requested period, "
                "a fully supportive—not merely complete or qualified—KP fructification result, and a dated transit confirmation overlapping that same period. "
                "A future peak elsewhere in the dasha cannot be used as proof that today is supportive."
            ),
        }
        compact_next_window = (
            {
                key: chronological[0].get(key)
                for key in (
                    "start", "end", "mahadasha", "antardasha", "pratyantardasha",
                    "route_success_coverage", "activated_focus_houses", "transit_confirmed",
                )
                if chronological[0].get(key) not in (None, "", [], {})
            }
            if chronological else {}
        )
        now_vs_wait_synthesis = _home_timing_decision(
            subtype,
            requested_period_supportive=requested_window_assessment["supportive_now"],
            next_window=compact_next_window,
            next_event_request=next_event_request,
            fructification_status=str(kp_route.get("verdict") or "not_established"),
        )
        answer_window = current_period if requested_window_assessment["supportive_now"] else (chronological[0] if chronological else {})
        answer_transits = (
            requested_transit_rows
            if requested_window_assessment["supportive_now"]
            else list(answer_window.get("transit_confirmation") or answer_window.get("route_peak_windows") or [])
        )
        kp_marker_parts = [
            f"H{row.get('cusp')}={row.get('sub_lord') or 'none'}>{','.join(str(house) for house in row.get('success_house_links') or []) or 'none'}"
            for row in kp_route.get("cusp_judgments") or []
            if isinstance(row, Mapping)
        ]
        dasha_marker = (
            "[[HOME_TIMING_DASHA:"
            f"MD={answer_window.get('mahadasha') or 'none'};"
            f"AD={answer_window.get('antardasha') or 'none'};"
            f"PD={answer_window.get('pratyantardasha') or 'none'};"
            f"HOUSES={','.join(str(house) for house in answer_window.get('route_success_coverage') or answer_window.get('activated_focus_houses') or []) or 'none'}]]"
            if answer_window else ""
        )
        first_transit = answer_transits[0] if answer_transits and isinstance(answer_transits[0], Mapping) else {}
        transit_marker = (
            "[[HOME_TIMING_TRANSIT:"
            f"PLANET={first_transit.get('planet') or 'none'};"
            f"START={first_transit.get('start') or 'none'};"
            f"END={first_transit.get('end') or first_transit.get('start') or 'none'};"
            f"HOUSES={','.join(str(house) for house in first_transit.get('activated_focus_houses') or []) or 'none'}]]"
            if first_transit else ""
        )
        kp_marker = f"[[HOME_TIMING_KP:{';'.join(kp_marker_parts)}]]" if kp_route.get("complete") and kp_marker_parts else ""
        answer_dasha_activation = dict(answer_window.get("dasha_activation") or {})
        if answer_window:
            # Preserve the broad phase with the activation ledger so the
            # answer cannot collapse a period question into one transit date.
            answer_dasha_activation.update({
                "start": answer_window.get("start"),
                "end": answer_window.get("end"),
            })
        answer_evidence_contract = {
            "requested_period_verdict": requested_window_assessment["verdict"],
            "window_role": (
                "conditional_candidate"
                if kp_route.get("verdict") == "qualified"
                else "next_supported_window" if next_event_request
                else "requested_period" if requested_window_assessment["supportive_now"]
                else "next_supported_window"
            ),
            "kp_fructification": kp_route,
            "dasha_activation": answer_dasha_activation,
            "transit_confirmation": [dict(row) for row in answer_transits[:4] if isinstance(row, Mapping)],
            "validation_markers": [marker for marker in (kp_marker, dasha_marker, transit_marker) if marker],
            "rule": (
                "For a positive timing statement, explain the KP result, the MD-AD-PD house activation and one "
                "dated named-planet transit confirmation in separate evidence-bound clauses. Copy the corresponding "
                "validation marker after each clause; markers are removed before display."
            ),
        }
        timing_synthesis = {
            "promise_verdict": route_synthesis.get("verdict") or route_synthesis.get("direction"),
            "kp_fructification": kp_route,
            "timing_windows": windows,
            "timing_window_count": len(windows),
            "next_window": chronological[0] if chronological else {},
            "strongest_window": strongest,
            "requested_window_assessment": requested_window_assessment,
            "now_vs_wait_synthesis": now_vs_wait_synthesis,
            "answer_evidence_contract": answer_evidence_contract,
            "dasha_activation_established": bool(windows),
            "transit_confirmation_established": any(row.get("transit_confirmed") for row in windows),
            "dasha_evaluation_complete": dasha_evaluation_complete,
            "transit_evaluation_complete": transit_evaluation_complete,
            "verdict": "missing_kp_fructification" if not kp_route.get("complete") else "kp_fructification_not_fully_supportive" if kp_route.get("verdict") != "supported" else "supportive_windows_found" if windows else "no_triangulated_window_in_horizon",
            "rule": "Promise precedes KP fructification, dasha activation and transit confirmation. For a next/when question lead with next_window and name strongest_window separately when different. A current period or transit alone is never a property event window.",
        }
        route_synthesis = {**route_synthesis, "timing_synthesis": timing_synthesis}
    return {
        "home_subtype": subtype, "scope": "single-native home, property and vehicle evidence", "focus_houses": profile["houses"],
        "home_planets": profile["planets"], "houses_available": available, "d1": rows, "d4": d4_rows,
        "d16": d16_rows,
        "focus_house_evidence": focus_house_evidence,
        "fourth_house_evidence": {
            "natal_summary": _focus_house_bundle(
                4,
                natal_by_house=natal_by_house,
                d1_by_house=by_house,
                d4_by_house=d4_by_house,
            ),
            "d1": natal_h4,
            "d1_lord_condition": d1_h4,
            "d4_lord_condition": d4_h4,
            "d16_vehicle_condition": dict(d16_by_house.get(4) or {}),
            "material_natal_factors": _material_natal_factors(natal_h4),
            "visible_facts": visible_facts[:12],
        },
        "immutable_fact_contract": immutable_fact_contract,
        "living_arrangement_synthesis": arrangement,
        "comparison_synthesis": comparison_synthesis,
        "finance_synthesis": finance_synthesis,
        "obstacle_synthesis": obstacle_synthesis,
        "remedy_blueprint": remedy if subtype == "property_remedy" else {},
        "timing_synthesis": timing_synthesis,
        "route_synthesis": route_synthesis,
        "ownership_capacity_synthesis": (
            {
                "verdict": route_synthesis.get("verdict"),
                "evidence_complete": route_synthesis.get("evidence_complete"),
                "required_visible_conclusion": (
                    "The chart supports the capacity to own a home."
                    if route_synthesis.get("verdict") == "supportive"
                    else "The chart supports home ownership with material conditions."
                    if route_synthesis.get("verdict") == "qualified"
                    else "A reliable home-ownership capacity conclusion is not established."
                ),
                "timing_boundary": "This is a capacity conclusion only. Do not give a date or imply that purchase is imminent.",
            }
            if subtype == "property_potential" else {}
        ),
        "summary": {"verdict": verdict, "score": round(score, 2), "support": supports[:8], "cautions": cautions[:8], "rule": "D1 establishes the property/home promise; D4 confirms or qualifies settlement, property fruition and vehicle comfort."},
        "availability": {"d1": bool(available), "d4": any(row.get("available") for row in d4_rows), "d16": any(row.get("available") for row in d16_rows), "lord_nakshatra_chain": bool(natal_h4.get("factors")), "dignity_strength": bool(natal_h4.get("factors")), "kp_fructification": bool((timing_synthesis.get("kp_fructification") or {}).get("complete")), "dasha_activation": bool(timing_synthesis.get("dasha_evaluation_complete")), "transit_confirmation": bool(timing_synthesis.get("transit_evaluation_complete")), "remedy_blueprint": bool(remedy.get("top_recommendation"))},
        "interpretation_rules": [
            "D1 establishes home/property promise; D4 qualifies it and cannot be replaced by generic wealth evidence.",
            "A property purchase or sale timing claim requires promise, KP materialization, dasha permission and transit confirmation.",
            "Property disputes, title conflicts, tenant/builder conflict and court outcomes belong to the Legal graph and are not predicted here.",
            "Foreign relocation and permanent settlement belong to the Foreign Life graph; inheritance ownership belongs to Wealth/Inheritance; electional dates belong to Muhurat.",
            "Rahu and Ketu contribute through occupation, conjunction and seventh aspect only; never fifth or ninth aspects.",
        ],
    }
