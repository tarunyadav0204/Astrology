"""Build the user-facing chain that explains how an Instant answer was derived.

This is intentionally separate from the LLM composer brief and the technical
ledger. It exposes calculated facts in the reasoning order a user can follow:
event framework -> natal permission -> dasha delivery -> transit confirmation
-> conclusion.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


HOUSE_MEANINGS = {
    1: "self, initiative and visibility",
    2: "income, family, speech and accumulated resources",
    3: "effort, communication and initiative",
    4: "home, stability and emotional security",
    5: "creativity, children, romance and learning",
    6: "work, service, competition and daily responsibilities",
    7: "partnership, spouse, clients and agreements",
    8: "trust, intimacy, shared obligations and transformation",
    9: "fortune, mentors and opportunity",
    10: "career, authority, role and status",
    11: "gains, support, networks and fulfilment",
    12: "expenses, distance, privacy and release",
}

TOPIC_HOUSE_MEANINGS = {
    "relationship": {
        2: "family expectations, speech and shared values",
        5: "affection, romance and emotional expression",
        7: "commitment, partnership and mutual agreements",
        11: "shared goals, support and social connections",
    },
    "marriage": {
        2: "family formation, speech and shared values",
        5: "affection, romance and emotional bonding",
        7: "marriage, spouse and committed partnership",
        11: "fulfilment, support and shared goals",
    },
    "promotion": {
        2: "salary, compensation and financial advancement",
        6: "work, service, competition and responsibility",
        10: "promotion, authority, role and professional status",
        11: "gains, recognition, networks and goal fulfilment",
    },
    "career": {
        2: "income, compensation and resource decisions",
        6: "workload, service, deadlines and competition",
        10: "role, authority, status and visible responsibility",
        11: "gains, recognition, networks and goal fulfilment",
    },
    "wealth": {
        2: "income, savings and family resources",
        5: "investment judgment and calculated risk",
        9: "long-range financial support and guidance",
        11: "gains, collections and financial goals",
    },
}

DIVISIONAL_HOUSE_MEANINGS = {
    "marriage": {
        1: "the overall strength and lived quality of married life",
        2: "family continuity, shared values and life built together",
        7: "the spouse, commitment and the marriage bond itself",
        8: "durability, intimacy and the ability to handle shared pressures",
        11: "fulfilment, support and gains through partnership",
    },
    "relationship": {
        1: "the overall strength and lived quality of partnership",
        2: "shared values, family expectations and communication",
        7: "the partner and the committed relationship itself",
        8: "trust, intimacy and resilience under pressure",
        11: "mutual support, fulfilment and shared goals",
    },
}


def _house_meaning(event_key: str, number: int) -> str:
    return TOPIC_HOUSE_MEANINGS.get(event_key, {}).get(
        number,
        HOUSE_MEANINGS.get(number, "this life area"),
    )

DOMAIN_HOUSES = {
    "career": ([10, 6, 11, 2], []),
    "promotion": ([10, 11, 2], [6]),
    "marriage": ([7, 2, 11], [5]),
    "relationship": ([7, 5, 11, 2], []),
    "wealth": ([2, 11, 5, 9], [10]),
    "business": ([7, 10, 11, 2], []),
    "progeny": ([5, 2, 11], [9]),
    "property": ([4, 2, 11, 12], [9]),
    "education": ([4, 5, 9, 11, 2], []),
    "foreign": ([3, 7, 9, 12], [11]),
}

def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _house(value: Any) -> int | None:
    try:
        number = int(value)
        return number if 1 <= number <= 12 else None
    except (TypeError, ValueError):
        return None


def _event_key(query_plan: Dict[str, Any], instant_context: Dict[str, Any]) -> str:
    normalized = _dict(instant_context.get("normalized_evidence"))
    timing = _dict(normalized.get("event_timing_verdict"))
    label = str(timing.get("event_category") or timing.get("answer_event_label") or "").lower()
    category = str(query_plan.get("category") or "general").lower()
    question = str(query_plan.get("question") or "").lower()
    # Presentation fallback for a router that returned broad `career` while the
    # already-resolved user goal explicitly names promotion.
    if category == "career" and re.search(r"\bpromot(?:e|ed|ion)\b|पदोन्नति", question):
        return "promotion"
    return label if label in DOMAIN_HOUSES else category


def _house_rows(event_key: str, focus_houses: Iterable[Any]) -> List[Dict[str, Any]]:
    primary, support = DOMAIN_HOUSES.get(event_key, ([], []))
    if not primary:
        primary = [h for h in (_house(item) for item in focus_houses) if h]
    rows: List[Dict[str, Any]] = []
    for number in [*primary, *support]:
        if number and all(row["house"] != number for row in rows):
            rows.append({
                "house": number,
                "role": "supporting" if number in support else "primary",
                "meaning": _house_meaning(event_key, number),
            })
    return rows


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" .")


def _topic_signal_lines(topic_signals: Any, event_key: str) -> tuple[List[str], List[str]]:
    """Turn calculated D1 topic signals into readable support/caution facts."""
    if not isinstance(topic_signals, dict):
        return [], []
    supports: List[str] = []
    cautions: List[str] = []
    body = topic_signals.get("body")
    if isinstance(body, str):
        body = [body]
    for item in _list(body):
        text = _clean_text(item.get("txt") if isinstance(item, dict) else item)
        if text:
            supports.append(text + ".")
    house_rows = topic_signals.get("hh") if isinstance(topic_signals.get("hh"), dict) else {}
    for key, row in house_rows.items():
        if not isinstance(row, dict):
            continue
        house = _house(key)
        text = _clean_text(row.get("txt"))
        if not text:
            continue
        line = (
            f"D1 House {house} ({_house_meaning(event_key, house)}) shows {text}."
            if house else text + "."
        )
        score = row.get("sc")
        try:
            is_caution = float(score) < 0
        except (TypeError, ValueError):
            is_caution = False
        (cautions if is_caution else supports).append(line)
    risk = _clean_text(topic_signals.get("risk"))
    if risk:
        cautions.append(risk + ".")
    pattern = _clean_text(topic_signals.get("pattern"))
    if pattern:
        supports.append(pattern + ".")
    return list(dict.fromkeys(supports))[:4], list(dict.fromkeys(cautions))[:3]


def _divisional_promise_lines(divisional_support: Any, event_key: str) -> tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Explain static divisional promise; deliberately ignore current_topic timing."""
    if not isinstance(divisional_support, dict):
        return [], [], []
    topic = divisional_support.get("topic") if isinstance(divisional_support.get("topic"), dict) else {}
    charts = topic.get("charts") if isinstance(topic.get("charts"), dict) else {}
    supports: List[str] = []
    cautions: List[str] = []
    structured: List[Dict[str, Any]] = []
    meanings = DIVISIONAL_HOUSE_MEANINGS.get(event_key, {})
    for code, detail in charts.items():
        if not isinstance(detail, dict):
            continue
        chart_support = _clean_text(detail.get("support")).replace("_", " ")
        if chart_support:
            supports.append(
                f"{code} is rated {chart_support} after checking its relevant houses, their lords and occupants."
            )
        rows = [row for row in _list(detail.get("rows")) if isinstance(row, dict)]
        # The direct topic house is more useful than whichever row happened to
        # sort first. For marriage/relationship this makes D9 house 7 primary.
        rows.sort(key=lambda row: (0 if _house(row.get("h")) == 7 else 1, _house(row.get("h")) or 99))
        for row in rows[:3]:
            house = _house(row.get("h"))
            if not house:
                continue
            lord = _clean_text(row.get("lord"))
            lord_house = _house(row.get("lord_h"))
            occupants = [_clean_text(value) for value in _list(row.get("occ")) if _clean_text(value)]
            band = _clean_text(row.get("band")).replace("_", " ") or "mixed"
            meaning = meanings.get(house, _house_meaning(event_key, house))
            facts = []
            if lord:
                facts.append(f"its lord {lord}" + (f" is placed in House {lord_house}" if lord_house else ""))
            if occupants:
                facts.append(f"occupants are {', '.join(occupants)}")
            line = f"In {code}, House {house} governs {meaning}"
            if facts:
                line += "; " + ", and ".join(facts)
            line += f". This factor is rated {band}."
            (cautions if band == "weak" else supports).append(line)
            structured.append({
                "chart": str(code),
                "house": house,
                "meaning": meaning,
                "lord": lord or None,
                "lord_placement_house": lord_house,
                "occupants": occupants,
                "rating": band,
            })
    return list(dict.fromkeys(supports))[:5], list(dict.fromkeys(cautions))[:3], structured


def _container_segments(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        return [row for row in _list(value.get("segments")) if isinstance(row, dict)]
    return []


def _selected_segments(query_plan: Dict[str, Any], instant_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    parashari = _dict(instant_context.get("instant_parashari"))
    normalized = _dict(instant_context.get("normalized_evidence"))
    mode = str(query_plan.get("answer_mode") or "")

    def window_rows(owner: Dict[str, Any]) -> List[Dict[str, Any]]:
        return _container_segments(owner.get("window_dasha_segments"))

    def horizon_rows(owner: Dict[str, Any]) -> List[Dict[str, Any]]:
        return _container_segments(owner.get("horizon_dasha_segments"))

    def forward_rows(owner: Dict[str, Any]) -> List[Dict[str, Any]]:
        value = _dict(owner.get("forward_event_dasha_scan"))
        return [row for row in _list(value.get("periods")) if isinstance(row, dict)]

    # Prefer the source appropriate to the question shape, but fall through on
    # an empty container. Several timing aliases are emitted by the router.
    if mode in {"timing_window", "month_timing", "event_timing"}:
        sources = (
            window_rows(parashari), window_rows(normalized),
            forward_rows(parashari), forward_rows(normalized),
            horizon_rows(parashari), horizon_rows(normalized),
        )
    else:
        sources = (
            forward_rows(parashari), forward_rows(normalized),
            horizon_rows(parashari), horizon_rows(normalized),
            window_rows(parashari), window_rows(normalized),
        )
    candidates = next((rows for rows in sources if rows), [])
    candidates.sort(key=lambda row: str(row.get("start") or row.get("start_date") or ""))
    return candidates[:6]


def _split_reasons(value: Any, *, exclude_transits: bool = False) -> List[str]:
    reasons = [part.strip() for part in str(value or "").split(";") if part.strip()]
    if exclude_transits:
        reasons = [row for row in reasons if not row.lower().startswith("dated transit peak")]
    return reasons[:6]

def _segment_row(row: Dict[str, Any], event_key: str) -> Dict[str, Any]:
    activated = [h for h in (_house(item) for item in _list(row.get("activated_focus_houses"))) if h]
    carriers = []
    for carrier in _list(row.get("carrier_planets")):
        if not isinstance(carrier, dict):
            continue
        carriers.append({
            "planet": carrier.get("planet"),
            "dasha_levels": _list(carrier.get("dasha_levels") or carrier.get("levels")),
            "natal_placement_house": _house(
                carrier.get("natal_placement_house") or carrier.get("natal_house")
            ),
            "natal_event_houses": [
                h for h in (_house(item) for item in _list(carrier.get("natal_event_houses"))) if h
            ],
            "event_links": [
                {
                    "house": h,
                    "meaning": _house_meaning(event_key, h),
                    "mechanisms": _list(link.get("mechanisms")),
                }
                for link in _list(carrier.get("event_links"))
                if isinstance(link, dict) and (h := _house(link.get("house")))
            ],
        })
    return {
        "start": row.get("start") or row.get("start_date"),
        "end": row.get("end") or row.get("end_date"),
        "chain": "–".join(str(item) for item in (
            row.get("mahadasha"), row.get("antardasha"), row.get("pratyantardasha")
        ) if item),
        "strength": row.get("activation_strength") or row.get("period_strength"),
        "activated_houses": [
            {"house": h, "meaning": _house_meaning(event_key, h)} for h in activated
        ],
        "carriers": carriers,
        "reasons": _split_reasons(row.get("why"), exclude_transits=True),
        "result_areas": [
            item for item in _list(row.get("predicted_result_areas")) if isinstance(item, dict)
        ][:4],
    }


def _transit_rows(segments: List[Dict[str, Any]], normalized: Dict[str, Any],
                  event_key: str) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for segment in segments:
        candidates.extend(
            row for row in _list(segment.get("peak_activation_windows")) if isinstance(row, dict)
        )
    timeline = _dict(normalized.get("transit_activation_timeline"))
    candidates.extend(row for row in _list(timeline.get("peak_windows")) if isinstance(row, dict))
    seen = set()
    result = []
    for row in candidates:
        key = (row.get("start"), row.get("end"), row.get("planet"), row.get("why"))
        if key in seen:
            continue
        seen.add(key)
        delivered_rows = []
        for delivered in _list(row.get("delivered_event_houses")):
            if not isinstance(delivered, dict):
                continue
            house = _house(delivered.get("house"))
            if not house:
                continue
            delivered_rows.append({
                "house": house,
                "meaning": _house_meaning(event_key, house),
                "mechanism": delivered.get("mechanism"),
            })
        reasons = [
            reason for reason in _split_reasons(row.get("why"))
            if "delivers its natal dasha promise to event house" not in reason.lower()
        ]
        result.append({
            "start": row.get("start"),
            "end": row.get("end"),
            "planet": row.get("planet"),
            "dasha_levels": _list(row.get("dasha_levels")),
            "strength": row.get("strength"),
            "trigger_kinds": _list(row.get("trigger_kinds")),
            "transit_native_house": _house(row.get("transit_native_house")),
            "natal_placement_house": _house(row.get("natal_placement_house")),
            "delivered_event_houses": delivered_rows,
            "confirmed_houses": [
                {"house": h, "meaning": _house_meaning(event_key, h)}
                for h in (_house(item) for item in _list(row.get("carrier_event_houses"))) if h
            ],
            "reasons": reasons,
        })
        if len(result) >= 5:
            break
    return result


def _d1_natal_factor_lines(value: Any, event_key: str) -> tuple[List[str], List[str], List[Dict[str, Any]]]:
    def explain_factor(factor: Dict[str, Any], house: int) -> str:
        source = str(factor.get("source") or "")
        planet = str(factor.get("planet") or "the planet")
        facts = _dict(factor.get("facts"))
        polarity = str(factor.get("polarity") or "mixed")
        if source in {"occupant_condition", "aspector_condition"}:
            role = "occupant" if source.startswith("occupant") else "aspector"
            dignity = str(facts.get("dignity") or "neutral").replace("_", " ")
            combustion = str(facts.get("combustion") or "normal").replace("_", " ")
            extras = [item for item in (dignity if dignity != "neutral" else None, combustion if combustion != "normal" else None) if item]
            return f"{planet}, a D1 House {house} {role}, is assessed {polarity}" + (f" ({', '.join(extras)})" if extras else "") + "."
        if source.endswith("functional_lordship"):
            role = str(facts.get("relation") or "influence")
            ruled = ", ".join(f"House {item}" for item in _list(facts.get("ruled_houses")))
            functional = str(facts.get("functional_role") or polarity).replace("_", " ")
            if functional.startswith("functional "):
                functional = functional[len("functional "):]
            return f"{planet}'s {role} influence is functionally {functional}" + (f" because it rules {ruled}" if ruled else "") + "."
        if source == "placement_dispositor_relationship":
            relation = str(facts.get("compound_relation") or polarity).replace("_", " ")
            return f"{planet} is hosted by dispositor {facts.get('dispositor')} in a {relation} fivefold relationship."
        if source == "fivefold_friendship_with_nakshatra_lord":
            relation = str(facts.get("compound_relation") or polarity).replace("_", " ")
            return f"{planet} is in {facts.get('nakshatra_name')} ruled by {facts.get('nakshatra_lord')}, with a {relation} fivefold relationship."
        if source == "final_dispositor_condition":
            chain = " → ".join(str(item) for item in _list(facts.get("chain")))
            return f"The dispositor chain {chain or planet} ends at {planet}, whose condition is {polarity}."
        if source == "node_conditioned_influence":
            return f"{planet}'s node influence on D1 House {house} resolves as {polarity} after its lord, sign and conjunction context are checked."
        if source == "planet_gandanta":
            name = facts.get("gandanta_name") or "a Gandanta junction"
            intensity = str(facts.get("intensity") or "").lower()
            detail = f" with {intensity} intensity" if intensity else ""
            return f"{planet} is in {name}{detail}, adding transition pressure to D1 House {house}."
        if source == "lagna_gandanta":
            name = facts.get("gandanta_name") or "a Gandanta junction"
            return f"The D1 ascendant is in {name}, adding sensitivity to the chart foundation."
        if source == "yogi_lord":
            sign = facts.get("special_sign_name")
            return f"{planet} is the Yogi lord" + (f" for {sign}" if sign else "") + f" and supports D1 House {house}."
        if source == "avayogi_lord":
            sign = facts.get("special_sign_name")
            overlap = facts.get("avayogi_tithi_shunya_overlap")
            if overlap:
                return f"{planet} is both the Avayogi and Tithi Shunya lord; the declared overlap rule makes its effect on D1 House {house} mixed rather than purely obstructive."
            return f"{planet} is the Avayogi lord" + (f" for {sign}" if sign else "") + f" and adds obstruction to D1 House {house}."
        if source == "dagdha_rashi_lord":
            sign = facts.get("special_sign_name")
            return f"{planet} rules the Dagdha Rashi" + (f" {sign}" if sign else "") + f" and adds pressure to D1 House {house}."
        if source == "tithi_shunya_lord":
            sign = facts.get("special_sign_name")
            return f"{planet} rules the Tithi Shunya Rashi" + (f" {sign}" if sign else "") + f" and restricts D1 House {house}."
        if source == "planet_in_dagdha_rashi":
            sign = facts.get("dagdha_sign_name") or facts.get("special_sign_name")
            return f"{planet} is placed in the Dagdha Rashi" + (f" {sign}" if sign else "") + f", weakening its contribution to D1 House {house}."
        if source == "planet_in_tithi_shunya_rashi":
            sign = facts.get("tithi_shunya_sign_name") or facts.get("special_sign_name")
            return f"{planet} is placed in the Tithi Shunya Rashi" + (f" {sign}" if sign else "") + f", restricting its contribution to D1 House {house}."
        if source == "combined_special_status":
            labels = [str(item.get("rule_id") or "").replace("_", " ") for item in _list(facts.get("statuses")) if isinstance(item, dict)]
            return f"{planet}'s correlated special conditions ({', '.join(labels)}) are counted as one combined influence on D1 House {house}." if labels else ""
        return ""

    payload = _dict(value)
    supports: List[str] = []
    cautions: List[str] = []
    structured: List[Dict[str, Any]] = []
    for row in _list(payload.get("houses")):
        if not isinstance(row, dict):
            continue
        house = _house(row.get("house"))
        if not house:
            continue
        lord = str(row.get("lord") or "").strip()
        occupants = [str(item) for item in _list(row.get("occupants")) if item]
        aspectors = [str(item) for item in _list(row.get("aspecting_planets")) if item]
        karakas = [str(item) for item in _list(row.get("karakas")) if item]
        tone = str(row.get("tone") or "mixed").replace("_", " ")
        factors = [factor for factor in _list(row.get("factors")) if isinstance(factor, dict)]
        lord_condition = next((
            factor for factor in factors
            if factor.get("source") == "house_lord_condition" and str(factor.get("planet") or "") == lord
        ), {})
        lord_facts = _dict(lord_condition.get("facts"))
        lord_house = _house(lord_facts.get("placement_house"))
        condition_bits = [str(lord_facts.get("dignity") or "").replace("_", " ")]
        combustion = str(lord_facts.get("combustion") or "normal").replace("_", " ")
        if combustion != "normal":
            condition_bits.append(combustion)
        if lord_facts.get("neecha_bhanga"):
            condition_bits.append("with debilitation cancellation")
        condition = ", ".join(bit for bit in condition_bits if bit and bit != "neutral")
        meaning = _house_meaning(event_key, house)
        line = f"D1 House {house} ({meaning}) is ruled by {lord or 'an unavailable lord'}"
        if lord_house:
            line += f", placed in House {lord_house}"
        if condition:
            line += f" in {condition} condition"
        line += f"; the combined house assessment is {tone}."
        (cautions if tone == "challenging" else supports).append(line)
        if occupants:
            supports.append(f"D1 House {house} contains {', '.join(occupants)}; their lordship, natural nature and condition are included in the assessment.")
        else:
            supports.append(f"D1 House {house} has no classical planetary occupant; its lord and aspects therefore carry more of the judgment.")
        if aspectors:
            supports.append(f"D1 House {house} receives classical aspects from {', '.join(aspectors)}.")
        if karakas:
            karaka_rows = []
            for planet in karakas:
                factor = next((
                    item for item in factors
                    if item.get("source") == "natural_karaka_condition" and item.get("planet") == planet
                ), {})
                facts = _dict(factor.get("facts"))
                placement = _house(facts.get("placement_house"))
                dignity = str(facts.get("dignity") or "neutral").replace("_", " ")
                karaka_rows.append(f"{planet}" + (f" in House {placement}" if placement else "") + (f" ({dignity})" if dignity != "neutral" else ""))
            supports.append(f"Natural karaka check for D1 House {house}: {', '.join(karaka_rows)}.")
        yoga_names = [str(item.get("name") or item.get("key")) for item in _list(row.get("yogas")) if isinstance(item, dict)]
        if yoga_names:
            supports.append(f"Relevant validated D1 yoga links for House {house}: {', '.join(yoga_names)}.")

        factor_support = sorted(
            (item for item in factors if item.get("polarity") == "supportive"),
            key=lambda item: float(item.get("weight") or 0), reverse=True,
        )
        factor_challenges = sorted(
            (item for item in factors if item.get("polarity") == "challenging"),
            key=lambda item: float(item.get("weight") or 0), reverse=True,
        )
        for factor in factor_support[:3]:
            detail = explain_factor(factor, house)
            if detail and detail not in supports:
                supports.append(detail)
        for factor in factor_challenges[:3]:
            detail = explain_factor(factor, house)
            if detail and detail not in cautions:
                cautions.append(detail)
        special_sources = {
            "planet_gandanta", "lagna_gandanta", "yogi_lord", "avayogi_lord",
            "dagdha_rashi_lord", "tithi_shunya_lord", "planet_in_dagdha_rashi",
            "planet_in_tithi_shunya_rashi", "combined_special_status",
        }
        special_support = [
            detail for factor in factor_support if factor.get("source") in special_sources
            if (detail := explain_factor(factor, house))
        ]
        special_cautions = [
            detail for factor in factor_challenges if factor.get("source") in special_sources
            if (detail := explain_factor(factor, house))
        ]
        support_notes = list(dict.fromkeys([
            *[detail for factor in factor_support[:2] if (detail := explain_factor(factor, house))],
            *special_support,
        ]))
        caution_notes = list(dict.fromkeys([
            *[detail for factor in factor_challenges[:2] if (detail := explain_factor(factor, house))],
            *special_cautions,
        ]))
        structured.append({
            "house": house,
            "meaning": meaning,
            "lord": lord,
            "lord_placement_house": lord_house,
            "lord_condition": lord_facts,
            "occupants": occupants,
            "aspecting_planets": aspectors,
            "karakas": karakas,
            "yogas": _list(row.get("yogas")),
            "tone": row.get("tone"),
            "supportive_weight": row.get("supportive_weight"),
            "challenging_weight": row.get("challenging_weight"),
            "strongest_supports": factor_support[:4],
            "strongest_challenges": factor_challenges[:4],
            "support_notes": support_notes,
            "caution_notes": caution_notes,
            # Keep these separate from the general audit notes so the answer
            # composer can receive the small, relevant special-factor subset
            # without receiving the complete natal factor ledger.
            "special_support_notes": list(dict.fromkeys(special_support)),
            "special_caution_notes": list(dict.fromkeys(special_cautions)),
        })
    return list(dict.fromkeys(supports)), list(dict.fromkeys(cautions)), structured


def build_user_derivation(*, query_plan: Dict[str, Any], verdict: Dict[str, Any],
                          instant_context: Dict[str, Any]) -> Dict[str, Any]:
    """Return calculated, display-ready derivation without changing the LLM prompt."""
    normalized = _dict(instant_context.get("normalized_evidence"))
    answer_mode = str(query_plan.get("answer_mode") or "")
    health_category = str(query_plan.get("category") or "").lower()
    health_value = _dict(normalized.get("health_body_area"))
    medical_profile = _dict(health_value.get("medical_profile"))
    if health_category in {"health", "mental_wellbeing", "surgery", "accident", "recovery"} and medical_profile:
        constitution = _dict(medical_profile.get("constitution"))
        constitutional_lines: List[str] = []
        if constitution.get("ascendant_sign"):
            constitutional_lines.append(
                f"D1 ascendant is {constitution.get('ascendant_sign')}; its lord "
                f"{constitution.get('ascendant_lord') or 'is unavailable'} is placed in "
                f"House {constitution.get('ascendant_lord_house') or 'an unavailable house'}."
            )
        if constitution.get("sun_house") or constitution.get("moon_house"):
            constitutional_lines.append(
                f"Sun is in House {constitution.get('sun_house') or '—'} and Moon is in "
                f"House {constitution.get('moon_house') or '—'} in the D1 health foundation."
            )
        for row in _list(constitution.get("core_houses")):
            if not isinstance(row, dict):
                continue
            residents = ", ".join(str(item) for item in _list(row.get("residents"))) or "no occupants"
            aspects = ", ".join(str(item) for item in _list(row.get("aspecting_planets"))) or "no calculated aspects"
            constitutional_lines.append(
                f"House {row.get('house')} ({row.get('role') or 'health role'}) is ruled by "
                f"{row.get('lord') or '—'} from House {row.get('lord_house') or '—'}; "
                f"occupants: {residents}; aspects: {aspects}."
            )

        vulnerability_groups: List[Dict[str, Any]] = []
        for item in _list(medical_profile.get("major_vulnerabilities")):
            if not isinstance(item, dict) or not item.get("zone"):
                continue
            lines = []
            mechanisms = [str(value) for value in _list(item.get("mechanisms")) if value]
            if mechanisms:
                lines.append(f"Likely expression pattern: {', '.join(mechanisms)}.")
            lines.extend(str(value) for value in _list(item.get("why")) if value)
            repetitions = [str(value) for value in _list(item.get("divisional_repetition")) if value]
            if repetitions:
                lines.append("Divisional repetition: " + "; ".join(repetitions) + ".")
            lines.append(
                f"Confidence: {str(item.get('confidence') or 'directional').replace('_', ' ')}; "
                f"supported by {item.get('confluence_count') or 0} independent natal layers."
            )
            vulnerability_groups.append({"title": str(item.get("zone")).title(), "lines": lines})

        for item in _list(medical_profile.get("condition_susceptibilities")):
            if not isinstance(item, dict) or not item.get("title"):
                continue
            lines = []
            if item.get("risk_level"):
                lines.append(f"Calculated signal: {item.get('risk_level')} astrological susceptibility; not a diagnosis.")
            lines.extend(str(value) for value in _list(item.get("evidence")) if value)
            if item.get("interpretation"):
                lines.append(str(item.get("interpretation")))
            if item.get("responsible_guidance"):
                lines.append(str(item.get("responsible_guidance")))
            vulnerability_groups.append({"title": str(item.get("title")), "lines": lines})

        condition_lines: List[str] = []
        for row in _list(medical_profile.get("planet_conditions")):
            if not isinstance(row, dict) or not row.get("planet"):
                continue
            details = [
                str(row.get("dignity") or "").replace("_", " "),
                str(row.get("functional_nature") or "").replace("_", " "),
                f"Shadbala {row.get('shadbala_grade')}" if row.get("shadbala_grade") else None,
                "combust" if row.get("combustion") == "combust" else None,
                "retrograde" if row.get("retrograde") else None,
            ]
            details = [value for value in details if value]
            if details:
                condition_lines.append(f"{row.get('planet')}: {', '.join(details)}.")

        requested_judgment = _dict(_dict(medical_profile.get("judgments")).get(health_category))
        judgment_lines = []
        if requested_judgment:
            judgment_lines.append(
                f"The calculated {health_category.replace('_', ' ')} judgment is "
                f"{'supported' if requested_judgment.get('supported') or requested_judgment.get('active') else 'not established'}; "
                "this is an astrological susceptibility judgment, not a medical diagnosis."
            )
        judgment_lines.extend(str(item) for item in _list(medical_profile.get("protective_factors")) if item)
        return {
            "schema_version": "instant-user-derivation/v2",
            "medical_reading": {
                "category": health_category,
                "constitutional_lines": constitutional_lines,
                "vulnerability_groups": vulnerability_groups,
                "condition_lines": condition_lines,
                "judgment_lines": judgment_lines,
                "divisions_checked": sorted(_dict(medical_profile.get("divisional_health_charts")).keys()),
                "safety": (
                    "This describes constitutional astrological susceptibility, not current timing, "
                    "a diagnosis or certainty."
                    if health_category == "health"
                    else "This describes astrological susceptibility and timing, not a diagnosis or certainty."
                ),
            },
            "conclusion": {
                "direction": verdict.get("direction"),
                "confidence": verdict.get("confidence"),
            },
            "limitations": _list(verdict.get("missing_required_capabilities")),
            "complete": bool(constitutional_lines and vulnerability_groups),
        }
    chart_facts = _dict(normalized.get("chart_facts"))
    if answer_mode == "factual_chart_lookup" and chart_facts:
        charts = _dict(chart_facts.get("charts"))
        requested = [str(item) for item in _list(chart_facts.get("requested_charts")) if item]
        fact_groups: List[Dict[str, Any]] = []
        for chart_name, raw_chart in charts.items():
            chart = _dict(raw_chart)
            domain = _dict(chart.get("domain"))
            lagna = _dict(chart.get("lagna"))
            lines: List[str] = []
            sign_name = lagna.get("sign_name") or chart.get("ascendant")
            if sign_name:
                lines.append(f"{chart_name} ascendant is {sign_name}.")
            if lagna.get("lord"):
                placement = f" in House {lagna.get('lord_house')}" if lagna.get("lord_house") not in (None, "") else ""
                dignity = f" ({str(lagna.get('lord_dignity')).replace('_', ' ')})" if lagna.get("lord_dignity") else ""
                lines.append(f"Its ascendant lord {lagna.get('lord')} is placed{placement}{dignity}.")
            lines.extend(str(item) for item in _list(chart.get("support_signals")) if item)
            lines.extend(f"Caution: {item}" for item in _list(chart.get("caution_signals")) if item)
            focus_rows = [row for row in _list(chart.get("houses")) if isinstance(row, dict) and row.get("focus")]
            for row in focus_rows:
                occupants = ", ".join(str(item) for item in _list(row.get("occupants"))) or "no occupants"
                lines.append(
                    f"House {row.get('house')} ({row.get('theme') or 'relevant area'}) is ruled by "
                    f"{row.get('lord') or 'an unavailable lord'} and has {occupants}."
                )
            fact_groups.append({
                "chart": str(chart_name),
                "life_area": domain.get("life_area"),
                "lines": list(dict.fromkeys(lines)),
            })
        missing = [str(item) for item in _list(chart_facts.get("missing_requested_charts")) if item]
        return {
            "schema_version": "instant-user-derivation/v2",
            "chart_reading": {
                "requested_charts": requested,
                "source": chart_facts.get("source"),
                "calculation_complete": bool(chart_facts.get("calculation_complete")),
                "fact_groups": fact_groups,
                "missing_charts": missing,
            },
            "conclusion": {
                "direction": verdict.get("direction") or "calculated_chart",
                "confidence": verdict.get("confidence"),
                "why": [str(item) for item in _list(chart_facts.get("reading_lines")) if item][:8],
            },
            "limitations": missing,
            "complete": bool(fact_groups and not missing),
        }
    parashari = _dict(instant_context.get("instant_parashari"))
    user_evidence = _dict(instant_context.get("_user_evidence"))
    promise = _dict(normalized.get("natal_promise"))
    event_key = _event_key(query_plan, instant_context)
    focus_houses = parashari.get("focus_houses") or _dict(instant_context.get("intent_summary")).get("focus_houses") or []
    raw_segments = _selected_segments(query_plan, instant_context)
    segments = [_segment_row(row, event_key) for row in raw_segments]
    segments = [row for row in segments if row.get("start") or row.get("chain") or row.get("reasons")]

    natal_basis: List[str] = []
    support = promise.get("topic_support")
    if answer_mode != "potential_capacity" and not support:
        support = promise.get("current_topic_support")
    if support:
        natal_basis.append(f"The {event_key} foundation is rated {str(support).replace('_', ' ')}.")
    topic_confirmation = _dict(normalized.get("topic_confirmation"))
    topic_signals = topic_confirmation.get("topic_signals") or parashari.get("topic_signals") or {}
    d1_support, d1_cautions, d1_house_factors = _d1_natal_factor_lines(
        user_evidence.get("natal_topic_factors") or parashari.get("natal_topic_factors"), event_key
    )
    if not d1_support and not d1_cautions:
        d1_support, d1_cautions = _topic_signal_lines(topic_signals, event_key)
    divisional_support, divisional_cautions, divisional_house_factors = _divisional_promise_lines(
        parashari.get("divisional_support"), event_key
    )
    # Legacy generic lines remain useful for timed questions, but a static
    # capacity/promise question must never cite current divisional timing as
    # evidence of natal promise.
    if answer_mode != "potential_capacity" and not divisional_support:
        for item in _list(normalized.get("divisional_specifics"))[:2]:
            if isinstance(item, str) and item.strip():
                natal_basis.append(item.strip())
    if not natal_basis and promise.get("status"):
        natal_basis.append("The topic-specific natal and divisional checks produced this promise status.")

    ranked = [row for row in _list(verdict.get("ranked_windows")) if isinstance(row, dict)]
    strongest = ranked[0] if ranked else (segments[-1] if segments else {})
    missing = _list(verdict.get("missing_required_capabilities"))
    return {
        "schema_version": "instant-user-derivation/v2",
        "event": {
            "key": event_key,
            "label": event_key.replace("_", " ").title(),
            "houses": _house_rows(event_key, focus_houses),
        },
        "natal_promise": {
            "status": promise.get("status") or "not_established",
            "basis": natal_basis,
            "d1_factors": d1_support,
            "d1_house_factors": d1_house_factors,
            "divisional_factors": divisional_support,
            "divisional_house_factors": divisional_house_factors,
            # This panel is explicitly expandable audit evidence. Do not hide
            # contradictory natal factors merely to keep it visually short;
            # those qualifications are what let an astrologer assess whether
            # the promise judgment is real and balanced.
            "cautions": list(dict.fromkeys([*d1_cautions, *divisional_cautions])),
            "evidence_complete": bool(d1_support and divisional_support),
        },
        "dasha_activation": segments,
        "transit_confirmation": _transit_rows(raw_segments, normalized, event_key),
        "conclusion": {
            "direction": verdict.get("direction"),
            "confidence": verdict.get("confidence"),
            "start": strongest.get("start"),
            "end": strongest.get("end"),
            "chain": strongest.get("chain"),
            "activated_houses": strongest.get("activated_focus_houses") or strongest.get("activated_houses") or [],
            "why": strongest.get("why") or strongest.get("reasons") or [],
        },
        "limitations": missing,
        "complete": bool(promise and segments),
    }
