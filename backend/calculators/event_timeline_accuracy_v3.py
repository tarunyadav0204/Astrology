"""Deterministic multi-house event resolution for Event Timeline Accuracy V3.

V2 fixed the requested-period clock but still handed independent evidence rows
to an LLM.  V3 turns those rows into a house-activation graph, resolves the
existing Instant event definitions, applies KP as an independent confirmation,
and uses persisted user facts only to choose an eligible real-life expression.
The LLM is a narration layer; it cannot add, remove, or retime candidates.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from prediction_engine.event_windows import (
    EVENT_DEFINITIONS,
    build_relative_event_definition,
    build_relative_health_definition,
    rotate_relative_house,
)
from calculators.event_timeline_delivery_v1 import (
    ACCURACY_LAYER_VERSION,
    EVENT_OBSTRUCTION_HOUSES,
    accuracy_layer_mode,
    ashtakavarga_judgment,
    birth_time_reliability_judgment,
    exact_transit_judgment,
    kp_judgment,
    natal_promise,
    obstruction_profile,
    outcome_dimensions,
    planet_delivery,
    supporting_systems_judgment,
    timing_windows,
    varga_judgment,
)


ACCURACY_V3_ENGINE_VERSION = "accuracy_v3"
V3_METHODOLOGY_VERSION = "event_timeline_flash_low_all_cards_narration_2026_09_v3_31"
V3_EVIDENCE_VERSION = "activation_graph_event_resolver_v20_rotated_relative_lagna"
V3_NARRATION_CONTRACT_VERSION = "flash_low_all_cards_event_brief_v7"

_CORE_LEVELS = {"mahadasha", "antardasha", "pratyantardasha"}
_SLOW_TRANSIT_PLANETS = {"Jupiter", "Saturn", "Rahu", "Ketu"}
_LEVEL_RANK = {"mahadasha": 1.0, "antardasha": 1.35, "pratyantardasha": 1.65, "sookshma": 0.65}
_LEVEL_ORDER = {"mahadasha": 0, "antardasha": 1, "pratyantardasha": 2, "sookshma": 3}
_VARGA_KEYS = {
    "D2": "d2_hora", "D3": "d3_drekkana", "D4": "d4_chaturthamsa", "D7": "d7_saptamsa",
    "D9": "d9_navamsa", "D10": "d10_dasamsa", "D12": "d12_dwadasamsa",
    "D16": "d16_shodasamsa", "D24": "d24_chaturvimsamsa",
    "D30": "d30_trimsamsa",
}

_SUBJECT_VARGAS: Dict[str, Tuple[str, Set[int]]] = {
    "spouse": ("D9", {7}),
    "child": ("D7", {5}),
    "mother": ("D12", {4}),
    "father": ("D12", {9}),
    "younger_sibling": ("D3", {3}),
    "elder_sibling": ("D3", {11}),
    "sibling": ("D3", {3, 11}),
}


def _language_code(language: Any) -> str:
    raw = str(language or "english").strip().lower().replace("_", "-")
    return "hi" if raw in {"hi", "hindi"} or raw.startswith("hi-") else "en"


def _parse_iso_date(value: Any) -> Optional[date]:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def user_fact_fingerprint(
    user_facts: Mapping[str, Any] | None,
    language: Any = "english",
    relative_profiles: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    # Include the presentation contract so cached V3.0 rows cannot mask a V3.1
    # explanation upgrade. Setting the explanation version to legacy_v1 remains
    # an immediate, reversible rollback without changing the astrology engine.
    from manifestation_kg.store import default_manifestation_store
    from utils.admin_settings import (
        get_event_timeline_narration_model,
        get_event_timeline_narration_thinking_level,
    )
    canonical = json.dumps({
        "facts": user_facts or {},
        "relative_profiles": relative_profiles or [],
        "language": _language_code(language),
        "contract_version": V3_EVIDENCE_VERSION,
        "explanation_version": v3_explanation_version(),
        "pipeline": str(os.getenv("EVENT_TIMELINE_V3_PIPELINE") or "optimized").strip().lower(),
        "narrator": str(os.getenv("EVENT_TIMELINE_V3_NARRATOR") or "llm").strip().lower(),
        "narration_contract": V3_NARRATION_CONTRACT_VERSION,
        "narration_model": get_event_timeline_narration_model(),
        "narration_thinking_level": get_event_timeline_narration_thinking_level(),
        "publication_mode": v3_publication_mode(),
        "accuracy_layer": accuracy_layer_mode(),
        "manifestation_kg_timeline": str(
            os.getenv("MANIFESTATION_KG_EVENT_TIMELINE") or "review"
        ).strip().lower(),
        "manifestation_kg_version": default_manifestation_store().ontology_version,
    }, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8", "ignore")).hexdigest()[:20]


def v3_explanation_version() -> str:
    raw = str(os.getenv("EVENT_TIMELINE_V3_EXPLANATION_VERSION") or "detailed_v2").strip().lower()
    return "legacy_v1" if raw in {"legacy", "legacy_v1", "v1"} else "detailed_v2"


def v3_publication_mode() -> str:
    """Control presentation only; both modes retain the full qualified set."""
    raw = str(os.getenv("EVENT_TIMELINE_V3_PUBLICATION_MODE") or "prioritized").strip().lower()
    return "exhaustive" if raw in {"all", "exhaustive", "legacy"} else "prioritized"


def _fact_lines(user_facts: Mapping[str, Any] | None, category: str) -> List[str]:
    values = (user_facts or {}).get(category) or []
    if isinstance(values, str):
        values = [values]
    return [" ".join(str(value or "").lower().split()) for value in values if str(value or "").strip()]


def _first_state(lines: Sequence[str], patterns: Sequence[Tuple[str, str]]) -> Tuple[str, List[str]]:
    hits: List[Tuple[str, str]] = []
    for line in lines:  # FactExtractor returns newest first.
        for state, pattern in patterns:
            if re.search(pattern, line, re.I):
                hits.append((state, line))
                break
    states = list(dict.fromkeys(state for state, _line in hits))
    if not states:
        return "unknown", []
    if len(states) > 1:
        # Facts arrive newest first.  Prefer the latest explicit statement so
        # an old "single" or "student" fact cannot permanently suppress a
        # newer marriage or employment fact; retain the conflicting basis for
        # audit instead of silently discarding it.
        return hits[0][0], [line for _state, line in hits[:3]]
    return states[0], [line for _state, line in hits[:2]]


def derive_desh_kaal_patra(
    user_facts: Mapping[str, Any] | None,
    *,
    age: int,
    target_year: int,
    relative_profiles: Sequence[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Convert explicit user statements into conservative manifestation gates."""
    career_lines = _fact_lines(user_facts, "career")
    education_lines = _fact_lines(user_facts, "education")
    family_lines = _fact_lines(user_facts, "family")
    relationship_lines = _fact_lines(user_facts, "relationships")

    employment, employment_basis = _first_state(career_lines + education_lines, (
        ("homemaker", r"\b(home[ -]?maker|housewife|stay[ -]?at[ -]?home)\b"),
        ("retired", r"\b(retired|retiree|pensioner)\b"),
        ("unemployed", r"\b(unemployed|not working|between jobs|jobless)\b"),
        ("student", r"\b(student|studying|college|university|school)\b"),
        ("self_employed", r"\b(self[ -]?employed|business owner|entrepreneur|freelanc)\w*\b"),
        ("employed", r"\b(work(?:ing)? as|employed|my job|profession|career as)\b"),
    ))
    relationship, relationship_basis = _first_state(family_lines + relationship_lines, (
        ("widowed", r"\bwidow(?:ed|er)?\b"),
        ("divorced", r"\b(divorced|separated)\b"),
        ("engaged", r"\bengaged\b"),
        ("married", r"\b(married|husband|wife|spouse)\b"),
        ("partnered", r"\b(partner|relationship|dating)\b"),
        ("single", r"\bsingle\b"),
    ))
    parenthood, parenthood_basis = _first_state(family_lines, (
        ("no_children", r"\b(no children|do not have (?:a )?(?:child|children)|childless)\b"),
        ("has_children", r"\b(my (?:son|daughter|child|children)|have (?:\d+|one|two|three|four|five) children|have (?:a )?(?:son|daughter|child))\b"),
    ))

    if age < 18:
        life_stage = "minor"
    elif age < 23:
        life_stage = "education_transition"
    elif age >= 65:
        life_stage = "senior"
    else:
        life_stage = "adult"

    all_fact_lines = [
        line
        for category in (user_facts or {})
        for line in _fact_lines(user_facts, str(category))
    ]
    explicit_topics: List[str] = []
    if any(re.search(r"\b(court|lawsuit|litigation|legal case|court case|dispute|tribunal)\b", line, re.I) for line in all_fact_lines):
        explicit_topics.append("legal")
    if any(re.search(r"\b(astrology|jyotish|occult|esoteric|hidden science|tantra|tarot)\b", line, re.I) for line in all_fact_lines):
        explicit_topics.append("occult")
    explicit_child_orders: List[str] = []
    child_order_patterns = (
        ("first", r"\b(first|1st) child\b"),
        ("second", r"\b(second|2nd) child\b"),
        ("third", r"\b(third|3rd) child\b"),
    )
    for order, pattern in child_order_patterns:
        if any(re.search(pattern, line, re.I) for line in all_fact_lines):
            explicit_child_orders.append(order)
    living_fact_lines = [
        line for line in all_fact_lines
        if not re.search(r"\b(died|deceased|late (?:mother|father|parent|brother|sister|spouse)|passed away)\b", line)
    ]
    relative_subjects: List[Dict[str, Any]] = []
    relative_contexts: Dict[str, Dict[str, Any]] = {}
    profiles_enabled = str(os.getenv("EVENT_TIMELINE_RELATIVE_PROFILES") or "true").strip().lower() in {
        "1", "true", "yes", "on",
    }
    if profiles_enabled:
        for profile in relative_profiles or []:
            key = str(profile.get("subject_key") or "").strip().lower()
            try:
                reference_house = int(profile.get("reference_house") or 0)
            except (TypeError, ValueError):
                reference_house = 0
            life_status = str(profile.get("life_status") or "unknown").strip().lower()
            if (
                not key or not reference_house or not bool(profile.get("enabled", True))
                or life_status == "deceased"
            ):
                continue
            label = str(profile.get("display_label") or key.replace("_", " ").title())
            relative_subjects.append({
                "key": key, "label": label, "reference_house": reference_house,
                "source": "structured_family_profile",
            })
            relative_contexts[key] = {
                "employment_state": str(profile.get("employment_state") or "unknown"),
                "life_status": life_status,
                "age_years": profile.get("age_years"),
                "birth_year": profile.get("birth_year"),
                "location_context": str(profile.get("location_context") or "unknown"),
                "relationship_status": str(profile.get("relationship_status") or "unknown"),
                "linked_birth_chart_id": profile.get("linked_birth_chart_id"),
                "profile_source": "structured_family_profile",
            }
    configured_keys = {row["key"] for row in relative_subjects}
    if relationship in {"married", "partnered", "engaged"}:
        if "spouse" not in configured_keys:
            relative_subjects.append({"key": "spouse", "label": "Spouse", "reference_house": 7, "source": "chat_fact"})
    if parenthood == "has_children":
        if "child" not in configured_keys:
            relative_subjects.append({"key": "child", "label": "Child", "reference_house": 5, "source": "chat_fact"})
    subject_patterns = (
        ("mother", "Mother", 4, r"\b(mother|mom|mum)\b"),
        ("father", "Father", 9, r"\b(father|dad)\b"),
        ("younger_sibling", "Younger sibling", 3, r"\b(younger|junior) (?:brother|sister|sibling)\b"),
        ("elder_sibling", "Elder sibling", 11, r"\b(elder|older|senior) (?:brother|sister|sibling)\b"),
        ("sibling", "Sibling", 3, r"\b(brother|sister|sibling)\b"),
    )
    for key, label, reference_house, pattern in subject_patterns:
        if key not in configured_keys and any(re.search(pattern, line, re.I) for line in living_fact_lines):
            if key == "sibling" and any(row["key"] in {"younger_sibling", "elder_sibling"} for row in relative_subjects):
                continue
            relative_subjects.append({"key": key, "label": label, "reference_house": reference_house, "source": "chat_fact"})

    return {
        "version": "desh_kaal_patra_family_profiles_v3",
        "target_year": target_year,
        "age": age,
        "life_stage": life_stage,
        "employment_state": employment,
        "relationship_state": relationship,
        "parenthood_state": parenthood,
        "explicit_topics": explicit_topics,
        "explicit_child_orders": explicit_child_orders,
        "eligible_relative_subjects": relative_subjects,
        "relative_contexts": relative_contexts,
        "relative_profiles_enabled": profiles_enabled,
        "fact_basis": {
            "employment": employment_basis,
            "relationship": relationship_basis,
            "parenthood": parenthood_basis,
            "relative_subjects": [row["label"] for row in relative_subjects],
        },
        "facts_present": bool(user_facts),
        "rule": "User facts constrain eligibility and wording; they never create astrological activation.",
    }


def _aspected_houses(planet: str, house: int) -> List[int]:
    offsets = {
        "Saturn": (2, 6, 9), "Mars": (3, 6, 7), "Jupiter": (4, 6, 8),
        # Nodes follow the Instant doctrine: occupation/conjunction/seventh aspect only.
        "Rahu": (6,), "Ketu": (6,),
    }.get(planet, (6,))
    return [((int(house) + offset - 1) % 12) + 1 for offset in offsets]


def _add_channel(
    graph: Dict[int, Dict[str, Any]], house: Any, *, planet: str, level: str,
    mechanism: str, evidence_id: str, start: str, end: str,
) -> None:
    try:
        number = int(house)
    except (TypeError, ValueError):
        return
    if not 1 <= number <= 12:
        return
    row = graph.setdefault(number, {
        "house": number, "dasha_channels": [], "transit_channels": [],
        "dasha_planets": [], "transit_planets": [], "evidence_ids": [],
    })
    channel = {
        "planet": planet, "dasha_level": level, "mechanism": mechanism,
        "evidence_id": evidence_id, "start_date": start, "end_date": end,
    }
    target = "transit_channels" if mechanism.startswith("transit_") else "dasha_channels"
    identity = (planet, level, mechanism, evidence_id)
    if all((c.get("planet"), c.get("dasha_level"), c.get("mechanism"), c.get("evidence_id")) != identity for c in row[target]):
        row[target].append(channel)
    planet_key = "transit_planets" if target == "transit_channels" else "dasha_planets"
    if planet not in row[planet_key]:
        row[planet_key].append(planet)
    if evidence_id and evidence_id not in row["evidence_ids"]:
        row["evidence_ids"].append(evidence_id)


def build_month_activation_graph(month_ledger: Mapping[str, Any]) -> Dict[str, Any]:
    graph: Dict[int, Dict[str, Any]] = {}
    for evidence in month_ledger.get("evidence") or []:
        if not isinstance(evidence, Mapping) or evidence.get("kind") != "dasha_lord_transit":
            continue
        planet = str(evidence.get("planet") or "")
        level = str(evidence.get("dasha_level") or "")
        evidence_id = str(evidence.get("evidence_id") or "")
        start = str(evidence.get("start_date") or "")
        end = str(evidence.get("end_date") or "")
        for house in evidence.get("lordships") or []:
            _add_channel(graph, house, planet=planet, level=level, mechanism="natal_lordship", evidence_id=evidence_id, start=start, end=end)
        natal_house = evidence.get("natal_house")
        _add_channel(graph, natal_house, planet=planet, level=level, mechanism="natal_occupation", evidence_id=evidence_id, start=start, end=end)
        if natal_house:
            for house in _aspected_houses(planet, int(natal_house)):
                _add_channel(graph, house, planet=planet, level=level, mechanism="natal_aspect", evidence_id=evidence_id, start=start, end=end)
        _add_channel(graph, evidence.get("transit_house"), planet=planet, level=level, mechanism="transit_occupation", evidence_id=evidence_id, start=start, end=end)
        for house in evidence.get("aspected_houses") or []:
            _add_channel(graph, house, planet=planet, level=level, mechanism="transit_aspect", evidence_id=evidence_id, start=start, end=end)

    for row in graph.values():
        row["dasha_levels"] = sorted({c["dasha_level"] for c in row["dasha_channels"]}, key=lambda x: -_LEVEL_RANK.get(x, 0))
        row["dasha_open"] = any(level in _CORE_LEVELS for level in row["dasha_levels"])
        row["transit_triggered"] = bool(row["transit_channels"])
        row["core_dasha_transit_occupation"] = any(
            channel.get("dasha_level") in _CORE_LEVELS
            and channel.get("mechanism") == "transit_occupation"
            for channel in row["transit_channels"]
        )
        row["persistent_transit_background"] = any(
            channel.get("planet") in _SLOW_TRANSIT_PLANETS
            and channel.get("dasha_level") in _CORE_LEVELS
            for channel in row["transit_channels"]
        )
        row["activation_score"] = round(
            sum(_LEVEL_RANK.get(c["dasha_level"], 0.5) for c in row["dasha_channels"])
            + 0.75 * len(row["transit_channels"]), 2
        )
    natal_dasha_open = sorted(h for h, row in graph.items() if row["dasha_open"])
    core_dasha_transit_occupied = sorted(
        h for h, row in graph.items() if row["core_dasha_transit_occupation"]
    )
    return {
        "houses": {str(house): graph[house] for house in sorted(graph)},
        # Keep the original field natal-only for rollback and audit. Integrated
        # V3.11 additionally lets a core dasha lord's direct transit occupation
        # open an event anchor as persistent background permission.
        "dasha_open_houses": natal_dasha_open,
        "natal_dasha_open_houses": natal_dasha_open,
        "core_dasha_transit_occupied_houses": core_dasha_transit_occupied,
        "event_anchor_permission_houses": sorted(set(natal_dasha_open) | set(core_dasha_transit_occupied)),
        "persistent_transit_background_houses": sorted(
            h for h, row in graph.items() if row["persistent_transit_background"]
        ),
        "transit_triggered_houses": sorted(h for h, row in graph.items() if row["transit_triggered"]),
        "all_activated_houses": sorted(graph),
        "transit_daily": month_ledger.get("transit_daily") or {},
        "transit_stations": month_ledger.get("transit_stations") or [],
        "transit_aspect_model": month_ledger.get("transit_aspect_model") or {},
    }


def _kp_confirmation(kp: Mapping[str, Any], anchor_houses: Set[int], event_houses: Set[int]) -> Dict[str, Any]:
    cusp_lords = kp.get("cusp_lords") if isinstance(kp.get("cusp_lords"), Mapping) else {}
    planet_sigs = kp.get("planet_significators") if isinstance(kp.get("planet_significators"), Mapping) else {}
    judgments: List[Dict[str, Any]] = []
    for house in sorted(anchor_houses):
        cusp = cusp_lords.get(house) or cusp_lords.get(str(house)) or {}
        sub_lord = str(cusp.get("sub_lord") or "") if isinstance(cusp, Mapping) else ""
        signified = {int(h) for h in (planet_sigs.get(sub_lord) or []) if str(h).isdigit()}
        links = sorted(signified & event_houses)
        judgments.append({"cusp": house, "sub_lord": sub_lord or None, "signified_houses": sorted(signified), "event_links": links})
    complete = bool(judgments) and all(row["sub_lord"] for row in judgments)
    linked = set(h for row in judgments for h in row["event_links"])
    if complete and all(row["event_links"] for row in judgments) and len(linked) >= 2:
        verdict = "supported"
    elif complete and any(row["event_links"] for row in judgments):
        verdict = "qualified"
    elif complete:
        verdict = "pressured"
    else:
        verdict = "unavailable"
    return {"complete": complete, "verdict": verdict, "cusp_judgments": judgments}


def _varga_confirmation(context: Mapping[str, Any], varga: str, houses: Set[int], carriers: Set[str]) -> Dict[str, Any]:
    key = _VARGA_KEYS.get(varga)
    raw = ((context.get("divisional_charts") or {}).get(key) or {}) if key else {}
    chart = raw.get("divisional_chart", raw) if isinstance(raw, Mapping) else {}
    planets = chart.get("planets") if isinstance(chart, Mapping) else {}
    hits: List[Dict[str, Any]] = []
    for planet in sorted(carriers):
        placement = (planets or {}).get(planet) or {}
        try:
            house = int(placement.get("house"))
        except (TypeError, ValueError):
            continue
        matched = sorted(({house} | set(_aspected_houses(planet, house))) & houses)
        if matched:
            hits.append({"planet": planet, "houses": matched})
    return {"chart": varga, "available": bool(planets), "confirmed": bool(hits), "carrier_hits": hits}


def _personalize(event_key: str, dkp: Mapping[str, Any]) -> Dict[str, Any]:
    employment = str(dkp.get("employment_state") or "unknown")
    relationship = str(dkp.get("relationship_state") or "unknown")
    parenthood = str(dkp.get("parenthood_state") or "unknown")
    life_stage = str(dkp.get("life_stage") or "adult")
    label_overrides: Dict[str, str] = {}
    forbidden: List[str] = []

    if event_key == "promotion":
        if employment == "employed":
            label = "Promotion or recognition"
        elif employment == "self_employed":
            label = "More business responsibility or recognition"
            forbidden.append("promotion")
        elif employment == "student" or life_stage in {"minor", "education_transition"}:
            label = "Study-related responsibility or recognition"
            forbidden.extend(["promotion", "salary increase"])
        elif employment == "unemployed":
            label = "New work opportunity or responsibility"
            forbidden.extend(["promotion", "salary increase"])
        elif employment == "retired":
            label = "More community or family responsibility"
            forbidden.extend(["promotion", "salary increase", "job promotion"])
        elif employment == "homemaker":
            label = "More family, community, or personal responsibility"
            forbidden.extend(["promotion", "salary increase", "job promotion"])
        else:
            label = "More responsibility or recognition"
            forbidden.extend(["promotion", "salary increase"])
        label_overrides["label"] = label
    elif event_key == "job_change":
        labels = {
            "homemaker": "Change in daily duties or responsibilities",
            "unemployed": "New work opportunity or change",
            "student": "Change in study, work, or responsibility",
            "retired": "Change in service or community work",
            "self_employed": "Change in business duties",
            "employed": "Job or role change",
        }
        label_overrides["label"] = labels.get(employment, "Work or responsibility change")
        if employment in {"homemaker", "retired", "student"}:
            forbidden.extend(["promotion", "job change", "employer"])
    elif event_key == "marriage":
        if relationship == "married":
            label_overrides["label"] = "Marriage or relationship"
            forbidden.extend(["wedding", "new spouse", "getting married"])
        elif relationship == "engaged":
            label_overrides["label"] = "Marriage plans or commitment"
        else:
            label_overrides["label"] = "Relationship or marriage"
    elif event_key == "children":
        if parenthood == "has_children":
            label_overrides["label"] = "Children or family responsibility"
        elif parenthood == "no_children":
            label_overrides["label"] = "Creative work, teaching, or family plans"
            forbidden.extend(["your child", "your children", "childbirth", "pregnancy"])
        else:
            label_overrides["label"] = "Children, care, or creative work"
            forbidden.extend(["childbirth", "pregnancy"])
    elif event_key == "education" and employment not in {"student"}:
        label_overrides["label"] = "Study, training, or qualification"

    return {**label_overrides, "forbidden_terms": forbidden}


_PREDICTIONS = {
    "job_change": "Your work or daily duties may change.",
    "promotion": "You may receive more responsibility or recognition.",
    "health": "Your health or daily routine may need more attention.",
    "property_purchase": "Plans to buy a home or property may move forward.",
    "vehicle_purchase": "Plans to buy a vehicle may move forward.",
    "relocation": "You may plan a move or spend time away from your present home.",
    "property_gain": "A home or property goal may move forward.",
    "marriage": "An important relationship matter may move forward.",
    "foreign_travel": "A long journey or stay away from home may become possible.",
    "children": "A matter involving children, care, or a creative project may need attention.",
    "education": "Study, training, or an exam may move forward.",
    "income_gain": "Money, savings, or a payment may improve or move forward.",
    "kg_family_mother_development": "A conversation, home matter, or practical responsibility involving your mother may need attention.",
    "kg_family_sibling_development": "A conversation, responsibility, or shared plan involving a sibling may move forward.",
    "kg_family_in_law_development": "A conversation, visit, practical responsibility, or family decision involving your spouse's family may arise.",
    "kg_legal_dispute_activity": "A disagreement, formal complaint, negotiation, or legal matter may require active attention.",
    "kg_legal_resolution": "A dispute may move toward settlement, judgment, compromise, or another clear resolution.",
    "kg_legal_contract_agreement": "A negotiation may move toward signing, approval, or a clear shared commitment.",
    "kg_legal_competition_result": "An exam, selection, dispute, or competitive effort may move toward a result.",
    "kg_spirituality_occult_study": "Astrology, spiritual practice, research, or another hidden subject may draw deeper study.",
    "kg_career_staff_hiring": "You may find or appoint an employee, helper, contractor, or other practical support.",
    "kg_career_staff_change": "A staff member or practical helper may change, leave, face pressure, or need a new arrangement.",
    "kg_relationship_remarriage_development": "A relationship may move toward a serious discussion or commitment involving remarriage.",
    "kg_children_first_child_development": "A decision, responsibility, or milestone involving your first child may need attention.",
    "kg_children_second_child_development": "A decision, responsibility, or milestone involving your second child may need attention.",
    "kg_children_third_child_development": "A decision, responsibility, or milestone involving your third child may need attention.",
    "kg_relationship_private_intimacy": "You and your partner may find more privacy, affection, physical closeness, or restful time together.",
}

_LEVEL_LABELS = {
    "mahadasha": "Mahadasha",
    "antardasha": "Antardasha",
    "pratyantardasha": "Pratyantardasha",
    "sookshma": "Sookshma dasha",
}
_MECHANISM_LABELS = {
    "natal_lordship": "by natal lordship",
    "natal_occupation": "by natal placement",
    "natal_aspect": "by natal aspect",
    "transit_occupation": "by transit placement",
    "transit_aspect": "by transit aspect",
}


def _natural_join(values: Sequence[str]) -> str:
    clean = [str(value) for value in values if str(value)]
    if len(clean) < 2:
        return "".join(clean)
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def _house_list(values: Iterable[int]) -> str:
    return _natural_join([f"H{house}" for house in sorted(set(int(value) for value in values))])


def _planet_activation_sentences(relevant_rows: Sequence[Mapping[str, Any]]) -> List[str]:
    grouped: Dict[Tuple[str, str], Dict[str, Set[int]]] = {}
    for row in relevant_rows:
        house = int(row.get("house") or 0)
        for channel in (row.get("dasha_channels") or []) + (row.get("transit_channels") or []):
            planet = str(channel.get("planet") or "")
            level = str(channel.get("dasha_level") or "")
            mechanism = str(channel.get("mechanism") or "")
            if planet and house and mechanism:
                grouped.setdefault((level, planet), {}).setdefault(mechanism, set()).add(house)

    sentences: List[str] = []
    for (level, planet), mechanisms in sorted(
        grouped.items(), key=lambda item: (_LEVEL_ORDER.get(item[0][0], 99), item[0][1])
    ):
        clauses = [
            f"{_house_list(houses)} {label}"
            for mechanism, label in _MECHANISM_LABELS.items()
            if (houses := mechanisms.get(mechanism))
        ]
        if clauses:
            level_label = _LEVEL_LABELS.get(level, level.replace("_", " ").title())
            sentences.append(f"{planet} {level_label} activates {_natural_join(clauses)}.")
    return sentences


def _period_stack_sentence(graph: Mapping[str, Any]) -> str:
    by_level: Dict[str, Set[str]] = {}
    for row in (graph.get("houses") or {}).values():
        for channel in row.get("dasha_channels") or []:
            level = str(channel.get("dasha_level") or "")
            planet = str(channel.get("planet") or "")
            if level and planet:
                by_level.setdefault(level, set()).add(planet)
    parts = [
        f"{_natural_join(sorted(by_level[level]))} {_LEVEL_LABELS.get(level, level)}"
        for level in sorted(by_level, key=lambda value: _LEVEL_ORDER.get(value, 99))
    ]
    return f"The active period stack is {_natural_join(parts)}." if parts else ""


def _confirmation_sentence(kp_result: Mapping[str, Any], varga: Mapping[str, Any]) -> str:
    kp_verdict = str(kp_result.get("verdict") or "unavailable")
    if kp_verdict == "supported":
        linked = sorted({
            int(house)
            for row in kp_result.get("cusp_judgments") or []
            for house in row.get("event_links") or []
        })
        kp_text = f"KP independently supports the combination through {_house_list(linked)}"
    elif kp_verdict == "qualified":
        kp_text = "KP gives partial independent support"
    elif kp_verdict == "pressured":
        kp_text = "KP data is present but does not independently connect the required event houses"
    elif kp_verdict == "blocked":
        kp_text = "KP cusp and significator chains emphasize obstruction without sufficient event-house permission"
    else:
        kp_text = "KP confirmation is unavailable"

    varga_text = _varga_confirmation_sentence(varga, "en")
    return f"{kp_text}; {varga_text}."


def _varga_confirmation_sentence(varga: Mapping[str, Any], language: str) -> str:
    chart = str(varga.get("chart") or ("संबंधित विभागीय कुंडली" if _language_code(language) == "hi" else "the relevant divisional chart"))
    if not varga.get("available"):
        return f"{chart} की पुष्टि उपलब्ध नहीं है" if _language_code(language) == "hi" else f"{chart} confirmation is unavailable"
    confirmed = list(varga.get("confirmed_carriers") or [])
    non_confirming = list(varga.get("non_confirming_carriers") or [])
    required = varga.get("required_divisional_houses") or []
    if _language_code(language) == "hi":
        if confirmed:
            details = _hi_join([
                f"{_hi_planet(row.get('planet'))} D1 के {_hi_house_list(row.get('d1_event_links') or [])} और {chart} के {_hi_house_list(row.get('houses') or [])} दोनों से जुड़ता है"
                for row in confirmed
            ])
            text = f"{chart} घटना को दोहराता है क्योंकि {details}"
        else:
            text = (
                f"{chart} D1 की घटना की स्वतंत्र पुष्टि नहीं करता क्योंकि कोई सक्रिय दशा ग्रह D1 के घटना-भावों और "
                f"{chart} के आवश्यक {_hi_house_list(required)} दोनों से नहीं जुड़ता"
            )
        if non_confirming:
            text += f"; {_hi_join([_hi_planet(row.get('planet')) for row in non_confirming])} आवश्यक भावों को दोनों कुंडलियों में नहीं दोहराते"
        return text
    if confirmed:
        details = _natural_join([
            f"{row.get('planet')} links D1 {_house_list(row.get('d1_event_links') or [])} with {chart} {_house_list(row.get('houses') or [])}"
            for row in confirmed
        ])
        text = f"{chart} repeats the event because {details}"
    else:
        text = (
            f"{chart} does not independently confirm the D1 event because no active dasha planet connects both the D1 event houses "
            f"and the required {chart} houses {_house_list(required)}"
        )
    if non_confirming:
        text += (
            f"; {_natural_join([str(row.get('planet')) for row in non_confirming])} "
            f"{'does' if len(non_confirming) == 1 else 'do'} not repeat the required houses in both charts"
        )
    return text


def _event_signature_sentence(
    definition: Any,
    anchor_hits: Sequence[int],
    transition_hits: Sequence[int],
    outcome_hits: Sequence[int],
) -> str:
    transition_subject = _house_list(transition_hits)
    sentence = (
        f"For {definition.label.lower()}, {_house_list(anchor_hits)} opens the "
        f"{definition.anchor.label.lower()}, while {transition_subject} "
        f"{'supply' if len(transition_hits) != 1 else 'supplies'} the "
        f"{definition.transition.label.lower()}."
    )
    if outcome_hits:
        sentence += (
            f" {_house_list(outcome_hits)} "
            f"{'add' if len(outcome_hits) != 1 else 'adds'} {definition.outcome.label.lower()}, "
            "strengthening a visible result."
        )
    else:
        sentence += f" The outcome houses ({_house_list(definition.outcome.houses)}) are not active, so the result may remain preparatory or incomplete."
    return sentence


def _scenario_reason(houses: Sequence[int], graph: Mapping[str, Any]) -> str:
    parts: List[str] = []
    rows = graph.get("houses") or {}
    for house in houses:
        row = rows.get(str(house)) or {}
        dasha_sources = sorted({
            f"{channel.get('planet')} {_LEVEL_LABELS.get(str(channel.get('dasha_level') or ''), str(channel.get('dasha_level') or 'dasha'))}"
            for channel in row.get("dasha_channels") or []
            if channel.get("planet")
        })
        dasha = _natural_join(dasha_sources)
        transit = _natural_join(row.get("transit_planets") or [])
        if dasha and transit:
            parts.append(f"H{house} is opened by {dasha} and timed by {transit} transit")
        elif dasha:
            parts.append(f"H{house} is opened by {dasha}")
        elif transit:
            parts.append(f"H{house} is timed by {transit} transit")
    return f"{'; '.join(parts)}." if parts else "The required event houses are active in the same period."


def _manifestation_specs(event_key: str, dkp: Mapping[str, Any]) -> List[Tuple[str, Tuple[int, ...]]]:
    employment = str(dkp.get("employment_state") or "unknown")
    relationship = str(dkp.get("relationship_state") or "unknown")
    parenthood = str(dkp.get("parenthood_state") or "unknown")
    specs: Dict[str, List[Tuple[str, Tuple[int, ...]]]] = {
        "job_change": [
            ("A change in duties, team, schedule, or working arrangement rather than a complete exit.", (6, 10, 3)),
            ("Applications, a transfer, restructuring, or release from the present role may move forward.", (6, 10, 8, 12)),
        ],
        "promotion": [
            ("Greater authority, visibility, or responsibility may be formally assigned.", (10, 5, 11)),
            ("Recognition may translate into a useful opportunity or improved resources.", (10, 11, 2)),
        ],
        "health": [
            ("A persistent health or energy concern may prompt a check-up, treatment plan, or stricter routine.", (1, 6, 8)),
            ("Rest, reduced workload, therapy, or recovery time may become necessary.", (1, 6, 12)),
        ],
        "property_purchase": [
            ("A home or property search may advance into budgeting, negotiation, or documentation.", (4, 2)),
            ("A mortgage, joint funding, inheritance, or major payment may become part of a property decision.", (4, 8, 11)),
        ],
        "vehicle_purchase": [
            ("A vehicle search may advance into budgeting, comparison, documentation, or delivery.", (4, 2, 11)),
            ("A conveyance or transport upgrade may become obtainable for practical or family use.", (4, 3, 11)),
        ],
        "property_gain": [
            ("A home, land, or fixed-property objective may become obtainable.", (4, 11)),
            ("Family resources or accumulated savings may support improvement of the living situation.", (4, 2, 11)),
        ],
        "relocation": [
            ("A residential move, change of neighbourhood, or reorganization of the present home may develop.", (4, 3)),
            ("A temporary stay away from home or a longer-distance move may require planning.", (4, 9, 12)),
        ],
        "marriage": [
            ("A partnership may move toward a clearer commitment, agreement, or shared family decision.", (7, 2, 11)),
            ("Romance, reconciliation, or a meaningful development in an existing relationship may occur.", (7, 5, 9)),
        ],
        "foreign_travel": [
            ("A temporary stay away from the present base for study, work, family, or retreat may develop.", (9, 12, 11)),
        ],
        "kg_travel_documentation": [
            ("A visa, travel permission, application, booking, or other journey paperwork may move forward.", (3, 9, 11)),
        ],
        "children": [
            ("A child-related milestone, education decision, or added caregiving responsibility may arise.", (5, 9, 11)),
            ("A creative project, mentoring role, or family-expansion discussion may become important.", (5, 2, 11)),
        ],
        "education": [
            ("A course, examination, application, or qualification process may advance.", (5, 4, 11)),
            ("Higher study, specialist training, teaching, or guided learning may become active.", (5, 9)),
        ],
        "income_gain": [
            ("Income, receivables, savings, or family resources may improve or be reorganized.", (2, 11)),
            ("A bonus, profitable opportunity, support from a network, or return from prior effort may emerge.", (2, 5, 9, 11)),
        ],
    }
    rows = list(specs.get(event_key) or [])
    if event_key == "promotion" and employment == "homemaker":
        rows = [
            ("Greater authority in household, family, community, or independent work may be recognized.", (10, 5, 11)),
            ("A personal project or community responsibility may bring visibility and useful support.", (10, 11, 2)),
        ]
    elif event_key == "promotion" and employment == "student":
        rows = [
            ("Academic leadership, selection, recognition, or greater responsibility may arise.", (10, 5, 11)),
            ("A result or opportunity may improve future educational or professional standing.", (10, 11, 2)),
        ]
    if event_key == "marriage" and relationship == "married":
        rows = [
            ("The existing marriage may enter a phase of joint decisions, renewed commitment, or shared responsibility.", (7, 2, 11)),
            ("A spouse-related milestone, reconciliation, or family ceremony may become important.", (7, 5, 9)),
        ]
    if event_key == "children" and parenthood == "no_children":
        rows = [
            ("A creative project or mentoring responsibility may demand sustained care and development.", (5, 9, 11)),
            ("Family-expansion discussions may arise, but the astrology alone does not establish pregnancy or childbirth.", (5, 2, 11)),
        ]
    return rows


def _detailed_manifestations(
    event_key: str,
    graph: Mapping[str, Any],
    dkp: Mapping[str, Any],
    channel_evidence: Mapping[str, Any] | None = None,
) -> List[Dict[str, str]]:
    active = {int(house) for house in graph.get("all_activated_houses") or []}
    results: List[Dict[str, str]] = []
    for scenario, desired_houses in _manifestation_specs(event_key, dkp):
        used = tuple(house for house in desired_houses if house in active)
        if used:
            results.append({
                "scenario": scenario,
                "reasoning": " ".join(filter(None, (
                    _scenario_reason(used, graph),
                    _scenario_channel_reason(channel_evidence or {}, "en"),
                ))),
            })
    return results[:2]


_HI_PLANETS = {
    "Sun": "सूर्य", "Moon": "चंद्र", "Mars": "मंगल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु",
}
_HI_LEVELS = {
    "mahadasha": "महादशा", "antardasha": "अंतर्दशा",
    "pratyantardasha": "प्रत्यंतरदशा", "sookshma": "सूक्ष्म दशा",
}
_HI_MECHANISMS = {
    "natal_lordship": "जन्म कुंडली के स्वामित्व से",
    "natal_occupation": "जन्म कुंडली की स्थिति से",
    "natal_aspect": "जन्म कुंडली की दृष्टि से",
    "transit_occupation": "गोचर स्थिति से",
    "transit_aspect": "गोचर दृष्टि से",
}


def _hi_join(values: Sequence[str]) -> str:
    clean = [str(value) for value in values if str(value)]
    if len(clean) < 2:
        return "".join(clean)
    return f"{', '.join(clean[:-1])} और {clean[-1]}"


def _hi_house_list(values: Iterable[int]) -> str:
    return _hi_join([f"H{house}" for house in sorted(set(int(value) for value in values))])


def _hi_planet(planet: Any) -> str:
    return _HI_PLANETS.get(str(planet), str(planet))


def _hindi_label(event_key: str, dkp: Mapping[str, Any]) -> str:
    employment = str(dkp.get("employment_state") or "unknown")
    relationship = str(dkp.get("relationship_state") or "unknown")
    parenthood = str(dkp.get("parenthood_state") or "unknown")
    if event_key == "job_change":
        return {
            "employed": "नौकरी या भूमिका में बदलाव", "self_employed": "व्यवसायिक भूमिका या संचालन में बदलाव",
            "student": "पढ़ाई से काम या जिम्मेदारी की ओर बदलाव", "homemaker": "दिनचर्या, सेवा या जिम्मेदारी में बदलाव",
            "unemployed": "रोज़गार का अवसर या कार्य परिवर्तन", "retired": "सलाहकारी या सेवा-भूमिका में बदलाव",
        }.get(employment, "काम या जिम्मेदारी में बदलाव")
    if event_key == "promotion":
        return {
            "employed": "पदोन्नति या पेशेवर मान्यता", "self_employed": "व्यवसायिक जिम्मेदारी या पहचान",
            "student": "शैक्षणिक जिम्मेदारी या पहचान", "homemaker": "घर, समुदाय या स्वतंत्र जिम्मेदारी",
            "unemployed": "करियर अवसर या सार्वजनिक जिम्मेदारी", "retired": "सलाहकारी, सामुदायिक या पारिवारिक जिम्मेदारी",
        }.get(employment, "स्थिति या जिम्मेदारी में विकास")
    if event_key == "marriage":
        return "विवाह या रिश्ते में बदलाव" if relationship == "married" else "रिश्ता या विवाह"
    if event_key == "children":
        if parenthood == "has_children":
            return "संतान या परिवार की जिम्मेदारी"
        if parenthood == "no_children":
            return "रचनात्मक काम, सिखाना या परिवार की योजना"
        return "संतान, देखभाल या रचनात्मक काम"
    return {
        "health": "स्वास्थ्य और दिनचर्या", "property_purchase": "घर या संपत्ति की खरीद",
        "vehicle_purchase": "वाहन की खरीद या प्राप्ति",
        "property_gain": "घर या संपत्ति से लाभ", "relocation": "स्थान परिवर्तन",
        "foreign_travel": "लंबी दूरी या विदेश यात्रा", "education": "पढ़ाई, प्रशिक्षण या योग्यता",
        "income_gain": "आय, बचत या संसाधनों में वृद्धि",
        "kg_travel_documentation": "वीज़ा, यात्रा दस्तावेज़ या अनुमति",
        "kg_family_mother_development": "माता, उनके घर या सहयोग से जुड़ा घटनाक्रम",
        "kg_family_sibling_development": "भाई-बहन से जुड़ा संवाद या घटनाक्रम",
        "kg_family_in_law_development": "ससुराल या जीवनसाथी के परिवार से जुड़ा घटनाक्रम",
        "kg_legal_dispute_activity": "विवाद, विरोध या कानूनी मामला",
        "kg_legal_resolution": "विवाद का समझौता, निर्णय या समाधान",
        "kg_legal_contract_agreement": "अनुबंध, समझौता या बातचीत से बनी सहमति",
        "kg_legal_competition_result": "प्रतियोगिता या बाधा पर परिणाम",
        "kg_spirituality_occult_study": "ज्योतिष, गूढ़ या रहस्य-विज्ञान का अध्ययन",
        "kg_career_staff_hiring": "कर्मचारी या व्यावहारिक सहायता की नियुक्ति",
        "kg_career_staff_change": "कर्मचारी या सेवा-सहयोग में बदलाव",
        "kg_relationship_remarriage_development": "पुनर्विवाह से जुड़ा घटनाक्रम",
        "kg_children_first_child_development": "पहली संतान से जुड़ा घटनाक्रम",
        "kg_children_second_child_development": "दूसरी संतान से जुड़ा घटनाक्रम",
        "kg_children_third_child_development": "तीसरी संतान से जुड़ा घटनाक्रम",
        "kg_relationship_private_intimacy": "रिश्ते में निजी निकटता और अंतरंगता",
    }.get(event_key, event_key)


_HI_SCENARIOS: Dict[str, List[Tuple[str, Tuple[int, ...]]]] = {
    "job_change": [
        ("पूरी नौकरी छोड़ने के बजाय काम, टीम, समय-सारिणी या जिम्मेदारियों में बदलाव हो सकता है।", (6, 10, 3)),
        ("आवेदन, स्थानांतरण, पुनर्गठन या वर्तमान भूमिका से निकलने की प्रक्रिया आगे बढ़ सकती है।", (6, 10, 8, 12)),
    ],
    "promotion": [
        ("अधिक अधिकार, दृश्यता या जिम्मेदारी औपचारिक रूप से मिल सकती है।", (10, 5, 11)),
        ("मान्यता किसी उपयोगी अवसर या बेहतर संसाधनों में बदल सकती है।", (10, 11, 2)),
    ],
    "health": [
        ("लगातार स्वास्थ्य या ऊर्जा की समस्या जाँच, उपचार-योजना या सख्त दिनचर्या की जरूरत बना सकती है।", (1, 6, 8)),
        ("आराम, काम का बोझ घटाना, उपचार या स्वस्थ होने का समय जरूरी हो सकता है।", (1, 6, 12)),
    ],
    "property_purchase": [
        ("घर या संपत्ति की खोज बजट, बातचीत या दस्तावेज़ों तक आगे बढ़ सकती है।", (4, 2)),
        ("ऋण, संयुक्त धन, विरासत या बड़ा भुगतान संपत्ति के निर्णय का हिस्सा बन सकता है।", (4, 8, 11)),
    ],
    "vehicle_purchase": [
        ("वाहन की खोज बजट, तुलना, दस्तावेज़ या डिलीवरी तक आगे बढ़ सकती है।", (4, 2, 11)),
        ("व्यावहारिक या पारिवारिक उपयोग के लिए वाहन या परिवहन सुविधा में सुधार हो सकता है।", (4, 3, 11)),
    ],
    "property_gain": [
        ("घर, भूमि या स्थायी संपत्ति का लक्ष्य प्राप्त होने योग्य बन सकता है।", (4, 11)),
        ("पारिवारिक संसाधन या जमा बचत रहने की स्थिति सुधारने में सहायता कर सकती है।", (4, 2, 11)),
    ],
    "relocation": [
        ("घर बदलने, पड़ोस बदलने या वर्तमान घर को पुनर्गठित करने की स्थिति बन सकती है।", (4, 3)),
        ("घर से दूर अस्थायी ठहराव या लंबी दूरी के स्थान परिवर्तन की योजना बन सकती है।", (4, 9, 12)),
    ],
    "marriage": [
        ("रिश्ता स्पष्ट प्रतिबद्धता, समझौते या साझा पारिवारिक निर्णय की ओर बढ़ सकता है।", (7, 2, 11)),
        ("प्रेम, मेल-मिलाप या मौजूदा रिश्ते में महत्वपूर्ण विकास हो सकता है।", (7, 5, 9)),
    ],
    "foreign_travel": [
        ("लंबी यात्रा, तीर्थ या महत्वपूर्ण सफर के लिए बुकिंग और कागज़ी कार्य जरूरी हो सकता है।", (9, 3)),
        ("पढ़ाई, काम, परिवार या विश्राम के लिए वर्तमान स्थान से दूर अस्थायी ठहराव बन सकता है।", (9, 12, 11)),
    ],
    "children": [
        ("संतान से जुड़ी उपलब्धि, शिक्षा का निर्णय या देखभाल की अतिरिक्त जिम्मेदारी आ सकती है।", (5, 9, 11)),
        ("रचनात्मक परियोजना, मार्गदर्शन की भूमिका या परिवार-विस्तार की चर्चा महत्वपूर्ण हो सकती है।", (5, 2, 11)),
    ],
    "education": [
        ("पाठ्यक्रम, परीक्षा, आवेदन या योग्यता की प्रक्रिया आगे बढ़ सकती है।", (5, 4, 11)),
        ("उच्च शिक्षा, विशेष प्रशिक्षण, अध्यापन या मार्गदर्शित अध्ययन सक्रिय हो सकता है।", (5, 9)),
    ],
    "income_gain": [
        ("आय, मिलने वाला धन, बचत या पारिवारिक संसाधन सुधर सकते हैं या पुनर्गठित हो सकते हैं।", (2, 11)),
        ("बोनस, लाभकारी अवसर, संपर्कों से सहायता या पुराने प्रयास का फल मिल सकता है।", (2, 5, 9, 11)),
    ],
}


def _hindi_scenario_reason(houses: Sequence[int], graph: Mapping[str, Any]) -> str:
    parts: List[str] = []
    rows = graph.get("houses") or {}
    for house in houses:
        row = rows.get(str(house)) or {}
        dasha_sources = sorted({
            f"{_hi_planet(channel.get('planet'))} {_HI_LEVELS.get(str(channel.get('dasha_level') or ''), 'दशा')}"
            for channel in row.get("dasha_channels") or [] if channel.get("planet")
        })
        transit = _hi_join([_hi_planet(planet) for planet in row.get("transit_planets") or []])
        if dasha_sources and transit:
            parts.append(f"H{house} को {_hi_join(dasha_sources)} खोलते हैं और {transit} का गोचर समय सक्रिय करता है")
        elif dasha_sources:
            parts.append(f"H{house} को {_hi_join(dasha_sources)} खोलते हैं")
        elif transit:
            parts.append(f"H{house} को {transit} का गोचर समय सक्रिय करता है")
    return f"{'; '.join(parts)}।" if parts else "आवश्यक घटना-भाव इसी अवधि में सक्रिय हैं।"


def _hindi_manifestations(
    event_key: str,
    graph: Mapping[str, Any],
    dkp: Mapping[str, Any],
    channel_evidence: Mapping[str, Any] | None = None,
) -> List[Dict[str, str]]:
    specs = list(_HI_SCENARIOS.get(event_key) or [])
    if event_key == "promotion" and str(dkp.get("employment_state")) == "homemaker":
        specs = [
            ("घर, परिवार, समुदाय या स्वतंत्र काम में अधिक जिम्मेदारी और पहचान मिल सकती है।", (10, 5, 11)),
            ("व्यक्तिगत परियोजना या सामुदायिक जिम्मेदारी दृश्यता और उपयोगी सहयोग ला सकती है।", (10, 11, 2)),
        ]
    if event_key == "marriage" and str(dkp.get("relationship_state")) == "married":
        specs = [
            ("मौजूदा विवाह में साझा निर्णय, नई प्रतिबद्धता या संयुक्त जिम्मेदारी का दौर आ सकता है।", (7, 2, 11)),
            ("जीवनसाथी से जुड़ी उपलब्धि, मेल-मिलाप या पारिवारिक समारोह महत्वपूर्ण हो सकता है।", (7, 5, 9)),
        ]
    active = {int(house) for house in graph.get("all_activated_houses") or []}
    result: List[Dict[str, str]] = []
    for scenario, desired in specs:
        used = tuple(house for house in desired if house in active)
        if used:
            result.append({
                "scenario": scenario,
                "reasoning": " ".join(filter(None, (
                    _hindi_scenario_reason(used, graph),
                    _scenario_channel_reason(channel_evidence or {}, "hi"),
                ))),
            })
    return result[:2]


_EVENT_DOMAINS = {
    "job_change": "work", "promotion": "work",
    "property_purchase": "home", "vehicle_purchase": "home", "property_gain": "home", "relocation": "home",
    "marriage": "relationships", "children": "family",
    "foreign_travel": "travel", "education": "education",
    "income_gain": "resources", "health": "health",
}

_BHAVA_THREADS: Dict[int, Tuple[str, ...]] = {
    1: ("body and vitality", "identity and appearance", "personal initiative"),
    2: ("savings and family resources", "speech and food", "family continuity"),
    3: ("communication and skills", "siblings", "documents and local movement"),
    4: ("mother", "home and residence", "land or property", "vehicles and comforts", "foundational education", "emotional security"),
    5: ("children", "education and intelligence", "creativity", "romance", "speculation"),
    6: ("health and treatment", "service and work routines", "debt", "conflict and competition"),
    7: ("spouse and partnership", "contracts and business", "clients and public dealings"),
    8: ("acute change or intervention", "joint assets and inheritance", "research and hidden matters", "crisis and transformation"),
    9: ("father and mentors", "higher education", "religion and pilgrimage", "law", "long-distance travel"),
    10: ("career and profession", "status and authority", "public responsibility", "major action"),
    11: ("income and gains", "networks", "elder siblings", "fulfilment of objectives"),
    12: ("expense and release", "foreign stay", "hospital or retreat", "sleep and seclusion", "spiritual withdrawal"),
}

_EVENT_CHANNELS: Dict[str, Dict[str, Any]] = {
    "job_change": {"channel": "work/service transition", "karakas": ("Saturn", "Mercury", "Sun"), "varga": "D10"},
    "promotion": {"channel": "status/recognition", "karakas": ("Sun", "Jupiter", "Saturn"), "varga": "D10"},
    "health": {"channel": "health/treatment", "karakas": ("Sun", "Moon", "Mars"), "varga": "D30"},
    "property_purchase": {"channel": "land/home acquisition", "karakas": ("Mars", "Moon"), "varga": "D4"},
    "property_gain": {"channel": "land/home fulfilment", "karakas": ("Mars", "Moon"), "varga": "D4"},
    "vehicle_purchase": {"channel": "vehicle/conveyance acquisition", "karakas": ("Venus", "Moon", "Mars"), "varga": "D16"},
    "relocation": {"channel": "residence change", "karakas": ("Moon", "Mars", "Rahu"), "varga": "D4"},
    "marriage": {"channel": "spouse/partnership", "karakas": ("Venus", "Jupiter"), "varga": "D9"},
    "foreign_travel": {"channel": "long-distance travel/foreign stay", "karakas": ("Jupiter", "Rahu", "Saturn"), "varga": "D9"},
    "travel_documentation": {"channel": "visa/travel documentation or permission", "karakas": ("Mercury", "Jupiter", "Rahu"), "varga": "D9"},
    "children": {"channel": "children/creative progeny", "karakas": ("Jupiter", "Sun"), "varga": "D7"},
    "education": {"channel": "education/qualification", "karakas": ("Mercury", "Jupiter"), "varga": "D24"},
    "income_gain": {"channel": "income/accumulated resources", "karakas": ("Jupiter", "Venus", "Mercury"), "varga": "D2"},
    "family_member": {"channel": "family-member development", "karakas": ("Moon", "Jupiter"), "varga": "D12"},
    "legal": {"channel": "legal dispute or resolution", "karakas": ("Saturn", "Mars", "Jupiter"), "varga": "D30"},
    "agreement": {"channel": "contract or negotiated agreement", "karakas": ("Mercury", "Venus", "Jupiter"), "varga": "D9"},
    "competition": {"channel": "competition and result", "karakas": ("Mars", "Saturn", "Jupiter"), "varga": "D10"},
    "occult_study": {"channel": "astrology or occult study", "karakas": ("Jupiter", "Mercury", "Ketu"), "varga": "D24"},
    "staff": {"channel": "staff or service support", "karakas": ("Saturn", "Mercury"), "varga": "D10"},
    "remarriage": {"channel": "remarriage development", "karakas": ("Venus", "Jupiter"), "varga": "D9"},
    "numbered_child": {"channel": "numbered-child development", "karakas": ("Jupiter", "Sun"), "varga": "D7"},
    "intimacy": {"channel": "private relationship closeness", "karakas": ("Venus", "Moon"), "varga": "D9"},
}


def _bhava_channel_disambiguation(
    definition: Any,
    *,
    source_event_key: str,
    dasha_planets: Sequence[str],
    transit_planets: Sequence[str],
    varga: Mapping[str, Any],
    transition_hits: Sequence[int],
    outcome_hits: Sequence[int],
) -> Dict[str, Any]:
    """Separate a bhava department from a concrete manifestation channel."""
    profile = _EVENT_CHANNELS.get(source_event_key) or {
        "channel": source_event_key.replace("_", " "), "karakas": (), "varga": definition.varga,
    }
    is_relative = str(getattr(definition, "event_kind", "native")) == "relative"
    source_definition = EVENT_DEFINITIONS.get(source_event_key, definition)
    semantic_anchor_houses = tuple(int(house) for house in source_definition.anchor.houses)
    threads = list(dict.fromkeys(
        thread for house in semantic_anchor_houses for thread in _BHAVA_THREADS.get(house, ())
    ))
    expected_karakas = set(str(planet) for planet in profile.get("karakas") or ())
    active_karakas = sorted(expected_karakas & (set(dasha_planets) | set(transit_planets)))
    varga_confirmed = bool(varga.get("confirmed"))
    if active_karakas and varga_confirmed:
        specificity = "channel_distinguished"
    elif active_karakas or varga_confirmed:
        specificity = "channel_supported_but_ranked"
    else:
        specificity = "bhava_level_ranked"
    return {
        "version": "bhava_channel_disambiguation_v1_all_houses",
        "subject_key": str(getattr(definition, "subject_key", "self") or "self"),
        "subject_frame": "relative" if is_relative else "native",
        "native_anchor_houses": sorted(int(house) for house in definition.anchor.houses),
        "semantic_anchor_houses": sorted(semantic_anchor_houses),
        "possible_anchor_threads": threads,
        "selected_channel": str(profile.get("channel")),
        "active_companion_houses": sorted(set(int(house) for house in transition_hits) | set(int(house) for house in outcome_hits)),
        "expected_karakas": sorted(expected_karakas),
        "active_karakas": active_karakas,
        "varga_required_for_specificity": str(profile.get("varga") or definition.varga),
        "varga_available": bool(varga.get("available")),
        "varga_confirmed": varga_confirmed,
        "specificity": specificity,
        "rule": (
            "The anchor house identifies a department, not an event. A concrete channel needs its configured "
            "companion houses, an involved natural karaka, and non-contradictory topic varga evidence."
        ),
    }


def _bhava_disambiguation_sentence(result: Mapping[str, Any], language: str) -> str:
    native_houses = _house_list(result.get("native_anchor_houses") or [])
    threads = list(result.get("possible_anchor_threads") or [])
    alternatives = _natural_join(threads[:5])
    karakas = _natural_join(result.get("active_karakas") or []) or "no channel-specific karaka"
    varga = str(result.get("varga_required_for_specificity") or "the topic varga")
    status = str(result.get("specificity") or "bhava_level_ranked")
    if _language_code(language) == "hi":
        status_text = {
            "channel_distinguished": "चयनित जीवन-विषय को अलग पहचान मिलती है",
            "channel_supported_but_ranked": "चयनित विषय समर्थित है, पर अन्य अर्थ भी संभव हैं",
            "bhava_level_ranked": "केवल भाव-स्तर का संकेत है; सटीक जीवन-विषय निश्चित नहीं है",
        }[status]
        return (
            f" भाव-विभाजन: {native_houses} के कई अर्थ हो सकते हैं; चयनित विषय {result.get('selected_channel')} है। "
            f"साथ सक्रिय भाव {_hi_house_list(result.get('active_companion_houses') or [])}; सक्रिय प्राकृतिक कारक {karakas}; "
            f"{varga} पुष्टि {'मिलती है' if result.get('varga_confirmed') else 'नहीं मिलती'}; {status_text}।"
        )
    return (
        f" Bhava disambiguation: {native_houses} can signify {alternatives}. The selected channel is "
        f"{result.get('selected_channel')} because the configured companion houses "
        f"{_house_list(result.get('active_companion_houses') or [])} also activate; active natural karakas are {karakas}, and {varga} "
        f"{'confirms it' if result.get('varga_confirmed') else 'does not independently confirm it'}. "
        f"Specificity is {status.replace('_', ' ')}."
    )


def _scenario_channel_reason(result: Mapping[str, Any], language: str) -> str:
    """Explain why a concrete scenario wins over other meanings of its anchor houses."""
    if not result:
        return ""
    anchors = result.get("native_anchor_houses") or []
    companions = result.get("active_companion_houses") or []
    karakas = [str(value) for value in result.get("active_karakas") or []]
    varga = str(result.get("varga_required_for_specificity") or "the topic chart")
    channel = str(result.get("selected_channel") or "this life channel")
    specificity = str(result.get("specificity") or "bhava_level_ranked")
    if _language_code(language) == "hi":
        if specificity == "channel_distinguished":
            return (
                f"इसे केवल {_hi_house_list(anchors)} का सामान्य विषय नहीं, बल्कि {channel} इसलिए माना गया है क्योंकि "
                f"साथ के भाव {_hi_house_list(companions)} सक्रिय हैं, प्राकृतिक कारक {_hi_join([_hi_planet(value) for value in karakas])} "
                f"शामिल हैं और {varga} इसकी पुष्टि करता है।"
            )
        return (
            f"{_hi_house_list(anchors)} के कई अर्थ हो सकते हैं। {channel} को साथ के भाव {_hi_house_list(companions)}, "
            f"प्राकृतिक कारक {_hi_join([_hi_planet(value) for value in karakas]) or 'अनुपलब्ध'} और {varga} के आधार पर ऊपर रखा गया है, "
            "लेकिन दूसरे जीवन-विषय भी संभव हैं।"
        )
    if specificity == "channel_distinguished":
        return (
            f"This is identified as {channel}, rather than only a general {_house_list(anchors)} theme, because companion houses "
            f"{_house_list(companions)} are active, natural significator{'' if len(karakas) == 1 else 's'} "
            f"{_natural_join(karakas)} {'participates' if len(karakas) == 1 else 'participate'}, and {varga} confirms the same channel."
        )
    return (
        f"{_house_list(anchors)} has several possible meanings. {channel} is ranked from companion houses "
        f"{_house_list(companions)}, natural significators {_natural_join(karakas) or 'not independently active'}, and {varga}; "
        "other life channels remain possible."
    )


def _relative_event_copy(
    definition: Any, graph: Mapping[str, Any], transition_hits: Sequence[int], language: str,
    channel_evidence: Mapping[str, Any] | None = None,
    subject_context: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Create subject-aware copy without borrowing the native's life circumstances."""
    source_key = str(definition.source_event_key or "health")
    subject_context = subject_context or {}
    subject_employment = str(subject_context.get("employment_state") or "unknown")
    try:
        subject_age = int(subject_context.get("age_years")) if subject_context.get("age_years") is not None else None
    except (TypeError, ValueError):
        subject_age = None
    if subject_employment == "unknown" and subject_age is not None and subject_age < 23:
        subject_employment = "student"
    subject = str(definition.label).split(" · ", 1)[0]
    reference_house = int(definition.reference_house)
    intervention_house = rotate_relative_house(reference_house, 8)
    treatment_house = rotate_relative_house(reference_house, 6)
    rest_house = rotate_relative_house(reference_house, 12)
    event_rows = [
        (graph.get("houses") or {}).get(str(house)) or {}
        for house in set(definition.anchor.houses) | set(definition.transition.houses)
    ]
    active_planets = {
        str(planet)
        for row in event_rows
        for planet in (row.get("dasha_planets") or []) + (row.get("transit_planets") or [])
    }
    intervention_supported = source_key == "health" and (
        intervention_house in set(int(house) for house in transition_hits)
        and bool({treatment_house, rest_house} & set(int(house) for house in transition_hits))
        and "Mars" in active_planets
    )
    if _language_code(language) == "hi":
        hi_subjects = {
            "spouse": "जीवनसाथी", "child": "संतान", "mother": "माता", "father": "पिता",
            "younger_sibling": "छोटे भाई या बहन", "elder_sibling": "बड़े भाई या बहन", "sibling": "भाई या बहन",
        }
        subject_text = hi_subjects.get(str(definition.subject_key), subject)
        hi_copy = {
            "job_change": ("काम, पढ़ाई, दिनचर्या या जिम्मेदारी में बदलाव", "भूमिका, समय-सारणी या काम की व्यवस्था बदलना", "नए कार्य, आवेदन या जिम्मेदारी की तैयारी"),
            "promotion": ("स्थिति, पहचान या जिम्मेदारी में वृद्धि", "औपचारिक या अनौपचारिक पहचान मिलना", "नेतृत्व या अधिक जिम्मेदारी लेना"),
            "health": ("स्वास्थ्य की जाँच, इलाज या आराम", "डॉक्टर से जाँच या इलाज की योजना", "आराम या घर पर देखभाल"),
            "property_purchase": ("घर या संपत्ति का निर्णय", "घर या भूमि के लिए बातचीत", "पैसा या कागज़ी काम तैयार करना"),
            "vehicle_purchase": ("वाहन या परिवहन सुविधा का निर्णय", "वाहन की तुलना, बुकिंग या खरीद", "वित्त, दस्तावेज़ या डिलीवरी व्यवस्थित करना"),
            "property_gain": ("घर या स्थायी संपत्ति से जुड़ी प्रगति", "घर या भूमि मिलने की संभावना", "परिवार या जान-पहचान से मदद"),
            "relocation": ("स्थान परिवर्तन या रहने की व्यवस्था में बदलाव", "घर या शहर बदलना", "अस्थायी ठहराव या घर की व्यवस्था बदलना"),
            "marriage": ("रिश्ते में कोई महत्वपूर्ण बदलाव", "साथ मिलकर कोई फैसला करना", "परिवार की भागीदारी या रिश्ते पर बातचीत"),
            "foreign_travel": ("लंबी यात्रा, दस्तावेज़ या घर से दूर ठहराव", "लंबी यात्रा या दूर रहना", "बुकिंग, अनुमति या यात्रा दस्तावेज़ आगे बढ़ना"),
            "children": ("संतान, देखभाल, मार्गदर्शन या रचनात्मक जिम्मेदारी", "परिवार या देखभाल की नई जिम्मेदारी", "मार्गदर्शन या रचनात्मक परियोजना आगे बढ़ना"),
            "education": ("पढ़ाई, परीक्षा, प्रशिक्षण या योग्यता", "कोर्स, परीक्षा या आवेदन", "विशेष प्रशिक्षण, अध्यापन या मार्गदर्शित अध्ययन"),
            "income_gain": ("आय, बचत या मिलने वाले संसाधनों में गतिविधि", "आय या मिलने वाला धन", "बचत, भुगतान या नेटवर्क से आर्थिक सहयोग"),
        }
        theme, first, second = hi_copy.get(source_key, ("जीवन के किसी क्षेत्र में बदलाव", "मुख्य परिस्थिति में बदलाव", "तैयारी या बातचीत"))
        if source_key in {"job_change", "promotion"}:
            if subject_employment == "homemaker":
                theme, first, second = (
                    "घर-परिवार की जिम्मेदारी, दिनचर्या या मान्यता में बदलाव",
                    "घर या परिवार की बड़ी जिम्मेदारी लेना",
                    "रोज़ के काम या फैसले लेने की भूमिका बदलना",
                )
            elif subject_employment == "student":
                theme, first, second = (
                    "पढ़ाई की जिम्मेदारी, उपलब्धि या दिशा में बदलाव",
                    "पढ़ाई में बड़ा लक्ष्य या जिम्मेदारी लेना",
                    "कोर्स, आवेदन, परीक्षा या पढ़ाई की दिनचर्या बदलना",
                )
            elif subject_employment == "retired":
                theme, first, second = (
                    "परिवार, समाज या निजी जिम्मेदारी में बदलाव",
                    "परिवार या समाज में बड़ी भूमिका लेना",
                    "नियमित जिम्मेदारी या दिनचर्या बदलना",
                )
        if source_key == "education" and subject_age is not None and subject_age >= 60:
            theme, first, second = (
                "सीखने, आध्यात्मिक अध्ययन, सिखाने या कौशल बढ़ाने का अवसर",
                "कोर्स, साधना या मार्गदर्शित अध्ययन शुरू करना",
                "अपने अनुभव से किसी को सिखाना या मार्गदर्शन देना",
            )
        prediction = f"{theme} से जुड़ा घटनाक्रम हो सकता है।"
        if source_key == "health":
            prediction += " यह केवल स्वास्थ्य पर अधिक ध्यान देने का समय है। यह किसी बीमारी की पक्की जानकारी नहीं है।"
        scenarios = [
            {"scenario": first, "reasoning": f"H{reference_house} को {subject_text} का लग्न मानकर निकाले गए घटना और परिवर्तन भाव एक ही अवधि में सक्रिय हैं; H{reference_house} का अलग से सक्रिय होना आवश्यक नहीं है।"},
            {"scenario": second, "reasoning": "दशा और गोचर संबंधित व्यक्ति के व्युत्पन्न भावों को साथ सक्रिय करते हैं; ठोस परिणाम निश्चित नहीं है।"},
        ]
        if intervention_supported:
            scenarios[0] = {
                "scenario": "अधिक गहन उपचार या किसी प्रक्रिया पर विचार",
                "reasoning": f"{subject_text} का व्युत्पन्न आठवाँ भाव H{intervention_house}, उपचार/आराम भाव और मंगल एक साथ सक्रिय हैं; यह संभावना है, निश्चित शल्यक्रिया नहीं।",
            }
        channel_reason = _scenario_channel_reason(channel_evidence or {}, "hi")
        for scenario in scenarios:
            scenario["reasoning"] = " ".join(filter(None, (scenario.get("reasoning"), channel_reason)))
        hi_labels = {
            "job_change": "काम या जिम्मेदारी में बदलाव", "promotion": "स्थिति या जिम्मेदारी में विकास",
            "health": "स्वास्थ्य या उपचार", "property_purchase": "घर या संपत्ति का निर्णय",
            "vehicle_purchase": "वाहन की खरीद या प्राप्ति",
            "property_gain": "संपत्ति से लाभ", "relocation": "स्थान परिवर्तन", "marriage": "रिश्ता या साझेदारी",
            "foreign_travel": "लंबी यात्रा या दूर ठहराव", "children": "संतान या देखभाल",
            "education": "पढ़ाई या प्रशिक्षण", "income_gain": "आय या संसाधन",
        }
        if source_key == "job_change":
            hi_labels[source_key] = {
                "homemaker": "घर की दिनचर्या या जिम्मेदारी में बदलाव",
                "student": "पढ़ाई की दिशा या जिम्मेदारी में बदलाव",
                "retired": "परिवार, समाज या दिनचर्या में बदलाव",
            }.get(subject_employment, hi_labels[source_key])
        elif source_key == "promotion":
            hi_labels[source_key] = {
                "homemaker": "घर-परिवार में बड़ी जिम्मेदारी",
                "student": "पढ़ाई में पहचान या बड़ी जिम्मेदारी",
                "retired": "परिवार या समाज में बड़ी जिम्मेदारी",
            }.get(subject_employment, hi_labels[source_key])
        return {"label": f"{subject_text} · {hi_labels.get(source_key, theme)}", "prediction": prediction, "manifestations": scenarios, "intervention_supported": intervention_supported}

    en_copy = {
        "job_change": ("a change in work, study, routine, or responsibility", "A role, schedule, or working arrangement changes", "Preparation for a new task, application, or responsibility"),
        "promotion": ("greater recognition, standing, or responsibility", "Formal or informal recognition", "Leadership or a larger responsibility"),
        "health": ("a health check-up, treatment, rest, or recovery", "A doctor visit, test, or treatment plan", "Rest, recovery, or care at home"),
        "property_purchase": ("a home or property decision", "Negotiation for a home or land", "Arranging finance, documents, or family resources"),
        "vehicle_purchase": ("a decision about buying a vehicle", "Comparing, booking, or buying a vehicle", "Arranging money, papers, or delivery"),
        "property_gain": ("progress involving a home or fixed property", "A home or land gain", "Property support through family or a network"),
        "relocation": ("a relocation or change in living arrangement", "Moving home or changing location", "A temporary stay or reorganization of the present home"),
        "marriage": ("an important relationship change", "Making an important decision together", "Family involvement or an important relationship discussion"),
        "foreign_travel": ("long-distance travel, paperwork, or time away from home", "Long-distance travel or a stay away", "Bookings, permission, or travel documentation"),
        "children": ("children, caregiving, mentoring, or creative responsibility", "A new family or caregiving responsibility", "Mentoring or a creative project develops"),
        "education": ("study, examinations, training, or qualifications", "A course, examination, or application", "Specialized training, teaching, or guided study"),
        "income_gain": ("activity involving income, savings, or receivables", "Income or a receivable moves", "Savings, payment, or financial network support"),
    }
    theme, first, second = en_copy.get(source_key, ("a meaningful life-area change", "A change in the main situation", "Preparation or negotiation"))
    if source_key in {"job_change", "promotion"}:
        if subject_employment == "homemaker":
            theme, first, second = (
                "a change in household responsibility, routine, or recognition",
                "Taking on a larger family or household responsibility",
                "A meaningful change in daily duties or decision-making",
            )
        elif subject_employment == "student":
            theme, first, second = (
                "a change in study responsibility, recognition, or direction",
                "Taking on a more demanding academic role or goal",
                "A course, application, examination, or study routine changes",
            )
        elif subject_employment == "retired":
            theme, first, second = (
                "a change in family, community, or personal responsibility",
                "Taking on a larger family or community role",
                "A regular responsibility or routine changes",
            )
    if source_key == "education" and subject_age is not None and subject_age >= 60:
        theme, first, second = (
            "learning, spiritual study, teaching, or skill development",
            "Beginning a course, practice, or guided study",
            "Sharing experience through teaching or mentoring",
        )
    prediction = f"{theme[:1].upper()}{theme[1:]} may become relevant."
    if source_key == "health":
        prediction += " This is only a time to pay extra attention to health. It is not a diagnosis or a certain surgery."
    scenarios = [
        {"scenario": first, "reasoning": f"Using H{reference_house} as the {subject.lower()}'s reference ascendant, the rotated event and transition houses activate in the same period; H{reference_house} does not need separate activation."},
        {"scenario": second, "reasoning": "Dasha and transit channels converge on the person's derived houses, but do not guarantee a completed outcome."},
    ]
    if intervention_supported:
        scenarios[0] = {
            "scenario": "A procedure or more intensive treatment may be considered",
            "reasoning": f"The {subject.lower()}'s derived eighth house H{intervention_house}, a treatment/rest house, and Mars are active together; this is a possibility, not a surgery prediction.",
        }
    channel_reason = _scenario_channel_reason(channel_evidence or {}, "en")
    for scenario in scenarios:
        scenario["reasoning"] = " ".join(filter(None, (scenario.get("reasoning"), channel_reason)))
    display_label = str(definition.label).split(" · ", 1)[-1]
    if source_key == "job_change":
        display_label = {
            "homemaker": "Household routine or responsibility change",
            "student": "Study direction or responsibility change",
            "retired": "Family, community, or routine change",
        }.get(subject_employment, display_label)
    elif source_key == "promotion":
        display_label = {
            "homemaker": "Greater family or household responsibility",
            "student": "Academic recognition or responsibility",
            "retired": "Greater family or community responsibility",
        }.get(subject_employment, display_label)
    return {"label": f"{subject} · {display_label}", "prediction": prediction, "manifestations": scenarios, "intervention_supported": intervention_supported}


def _role_profile(house_numbers: Set[int], graph: Mapping[str, Any]) -> Dict[str, Any]:
    direct_dasha: Set[Tuple[int, str, str, str]] = set()
    aspect_dasha: Set[Tuple[int, str, str, str]] = set()
    direct_transit: Set[Tuple[int, str, str]] = set()
    aspect_transit: Set[Tuple[int, str, str]] = set()
    dasha_planets: Set[str] = set()
    transit_planets: Set[str] = set()
    levels: Set[str] = set()
    rows = graph.get("houses") or {}
    for house in house_numbers:
        row = rows.get(str(house)) or {}
        for channel in row.get("dasha_channels") or []:
            level = str(channel.get("dasha_level") or "")
            if level not in _CORE_LEVELS:
                continue
            planet = str(channel.get("planet") or "")
            mechanism = str(channel.get("mechanism") or "")
            signature = (house, planet, level, mechanism)
            (aspect_dasha if mechanism == "natal_aspect" else direct_dasha).add(signature)
            dasha_planets.add(planet)
            levels.add(level)
        for channel in row.get("transit_channels") or []:
            planet = str(channel.get("planet") or "")
            mechanism = str(channel.get("mechanism") or "")
            signature = (house, planet, mechanism)
            (aspect_transit if mechanism == "transit_aspect" else direct_transit).add(signature)
            transit_planets.add(planet)
    return {
        "direct_dasha": len(direct_dasha), "aspect_dasha": len(aspect_dasha),
        "direct_transit": len(direct_transit), "aspect_transit": len(aspect_transit),
        "dasha_planets": dasha_planets, "transit_planets": transit_planets,
        "levels": levels,
    }


def _phase_from_profiles(outcome_profile: Mapping[str, Any]) -> str:
    dasha = int(outcome_profile.get("direct_dasha") or 0) + int(outcome_profile.get("aspect_dasha") or 0)
    transit = int(outcome_profile.get("direct_transit") or 0) + int(outcome_profile.get("aspect_transit") or 0)
    if dasha and transit:
        return "result_window"
    if dasha or transit:
        return "developing"
    return "preparatory"


def _deterministic_prediction(
    event_key: str, label: str, transition_hits: Sequence[int], phase: str,
    transit_planets: Sequence[str], kp_result: Mapping[str, Any], varga: Mapping[str, Any],
) -> str:
    """Produce specific but restrained copy from the event pathway and phase."""
    transition = set(int(house) for house in transition_hits)
    pathways: Dict[str, List[Tuple[Set[int], str]]] = {
        "job_change": [
            ({8, 12}, "Your work setup or daily duties may change."),
            ({3}, "An application, interview, transfer, or new duty may move forward."),
        ],
        "promotion": [
            ({11}, "You may receive more responsibility, support, or recognition."),
            ({5}, "Good work, leadership, or an important project may bring recognition."),
        ],
        "health": [
            ({8}, "A health or daily-routine concern may need a check-up or practical action."),
            ({12}, "You may need more rest, treatment, or a lighter routine."),
        ],
        "property_purchase": [
            ({8}, "A home or property plan may involve a loan, shared money, inheritance, or a large payment."),
            ({2}, "Savings, family money, or paperwork may help a home or property plan move forward."),
        ],
        "vehicle_purchase": [
            ({2, 11}, "A vehicle purchase may move to budgeting, paperwork, booking, or delivery."),
        ],
        "property_gain": [
            ({11}, "A goal involving a home, land, or property may become easier to achieve."),
        ],
        "relocation": [
            ({12}, "You may plan a move or a temporary stay away from home."),
            ({3}, "You may change your home, neighbourhood, or living setup."),
        ],
        "marriage": [
            ({2, 11}, "You and your partner may make an important decision together. Family may also be involved."),
            ({5}, "Love, reconciliation, or greater closeness may become important."),
        ],
        "foreign_travel": [
            ({12}, "A long journey or temporary stay away may happen for work, study, family, pilgrimage, or rest."),
        ],
        "kg_travel_documentation": [
            ({3}, "A visa, travel permission, application, booking, or other journey paperwork may move forward."),
        ],
        "children": [
            ({11}, "A matter involving children, care, teaching, or a creative project may receive support."),
            ({9}, "A decision about a child's study, guidance, or travel may arise."),
        ],
        "education": [
            ({9}, "Higher study, training, teaching, or learning with a guide may begin."),
            ({4}, "A course, exam, or application may need steady preparation."),
        ],
        "income_gain": [
            ({11}, "Income, savings, or money owed to you may improve or be reorganized."),
        ],
    }
    base = next(
        (text for houses, text in pathways.get(event_key, []) if houses & transition),
        _PREDICTIONS.get(event_key, f"{label} may become active."),
    )
    return base


def _hindi_prediction(
    event_key: str, transition_hits: Sequence[int], phase: str,
    transit_planets: Sequence[str], kp_result: Mapping[str, Any], varga: Mapping[str, Any],
) -> str:
    transition = set(int(house) for house in transition_hits)
    pathways: Dict[str, List[Tuple[Set[int], str]]] = {
        "job_change": [
            ({8, 12}, "काम की व्यवस्था या रोज़ की जिम्मेदारियाँ बदल सकती हैं।"),
            ({3}, "आवेदन, इंटरव्यू, तबादला या नई जिम्मेदारी आगे बढ़ सकती है।"),
        ],
        "promotion": [
            ({11}, "आपको अधिक जिम्मेदारी, सहयोग या पहचान मिल सकती है।"),
            ({5}, "अच्छा काम, नेतृत्व या कोई महत्वपूर्ण काम पहचान दिला सकता है।"),
        ],
        "health": [
            ({8}, "स्वास्थ्य या दिनचर्या की किसी परेशानी पर जाँच या सही कदम की जरूरत हो सकती है।"),
            ({12}, "अधिक आराम, इलाज या हल्की दिनचर्या की जरूरत हो सकती है।"),
        ],
        "property_purchase": [
            ({8}, "घर या संपत्ति की योजना में लोन, साझा पैसा, विरासत या बड़ा भुगतान जुड़ सकता है।"),
            ({2}, "बचत, परिवार का पैसा या कागज़ी काम घर-संपत्ति की योजना आगे बढ़ा सकता है।"),
        ],
        "vehicle_purchase": [
            ({2, 11}, "बजट, दस्तावेज़, बुकिंग या डिलीवरी के माध्यम से वाहन की खरीद आगे बढ़ सकती है।"),
        ],
        "property_gain": [({11}, "सहयोग या लाभ के माध्यम से घर, भूमि या स्थायी संपत्ति का लक्ष्य प्राप्त होने योग्य बन सकता है।")],
        "relocation": [
            ({12}, "स्थान परिवर्तन या वर्तमान घर से दूर अस्थायी ठहराव के लिए व्यावहारिक योजना बन सकती है।"),
            ({3}, "स्थानीय स्थान परिवर्तन, पड़ोस बदलना या वर्तमान घर का पुनर्गठन हो सकता है।"),
        ],
        "marriage": [
            ({2, 11}, "आप और आपके साथी मिलकर कोई महत्वपूर्ण फैसला कर सकते हैं। परिवार भी इसमें शामिल हो सकता है।"),
            ({5}, "प्यार, मेल-मिलाप या रिश्ते में नज़दीकी बढ़ सकती है।"),
        ],
        "foreign_travel": [
            ({12}, "काम, पढ़ाई, परिवार, तीर्थ या आराम के लिए लंबी यात्रा हो सकती है।"),
        ],
        "kg_travel_documentation": [
            ({3}, "वीज़ा, यात्रा अनुमति, आवेदन, बुकिंग या अन्य यात्रा दस्तावेज़ आगे बढ़ सकते हैं।"),
        ],
        "children": [
            ({11}, "संतान, रचनात्मक परियोजना, मार्गदर्शन या परिवार-विस्तार की चर्चा को सहयोग मिल सकता है।"),
            ({9}, "संतान या रचनात्मक जिम्मेदारी से जुड़ा शिक्षा, मार्गदर्शन या यात्रा का निर्णय आ सकता है।"),
        ],
        "education": [
            ({9}, "आगे की पढ़ाई, प्रशिक्षण या किसी शिक्षक की मदद से सीखना शुरू हो सकता है।"),
            ({4}, "कोर्स, परीक्षा या आवेदन के लिए लगातार तैयारी करनी पड़ सकती है।"),
        ],
        "income_gain": [({11}, "आय, मिलने वाला धन, बचत या संपर्कों से सहयोग सुधर सकता है या पुनर्गठित हो सकता है।")],
    }
    fallback = {
        "job_change": "काम या जिम्मेदारी बदल सकती है।", "promotion": "जिम्मेदारी या पहचान बढ़ सकती है।",
        "health": "स्वास्थ्य और दिनचर्या पर ध्यान देना पड़ सकता है।", "property_purchase": "घर या संपत्ति का निर्णय सक्रिय हो सकता है।",
        "vehicle_purchase": "वाहन खरीदने की योजना आगे बढ़ सकती है।",
        "property_gain": "घर या संपत्ति का लक्ष्य आगे बढ़ सकता है।", "relocation": "घर या जगह बदलने की योजना बन सकती है।",
        "marriage": "रिश्ते से जुड़ा महत्वपूर्ण मामला आगे बढ़ सकता है।", "foreign_travel": "लंबी यात्रा या घर से दूर रहना संभव हो सकता है।",
        "kg_travel_documentation": "वीज़ा, यात्रा अनुमति या यात्रा से जुड़ा कागज़ी काम आगे बढ़ सकता है।",
        "kg_family_mother_development": "माता से जुड़ी बातचीत, उनके घर का मामला या कोई व्यावहारिक जिम्मेदारी ध्यान मांग सकती है।",
        "kg_family_sibling_development": "भाई-बहन से जुड़ी बातचीत, जिम्मेदारी या साझा योजना आगे बढ़ सकती है।",
        "kg_family_in_law_development": "ससुराल पक्ष से जुड़ी बातचीत, मुलाकात, जिम्मेदारी या पारिवारिक फैसला सामने आ सकता है।",
        "kg_legal_dispute_activity": "मतभेद, औपचारिक शिकायत, बातचीत या कानूनी मामला सक्रिय ध्यान मांग सकता है।",
        "kg_legal_resolution": "विवाद समझौते, निर्णय, सहमति या किसी स्पष्ट समाधान की ओर बढ़ सकता है।",
        "kg_legal_contract_agreement": "बातचीत हस्ताक्षर, मंजूरी या स्पष्ट साझा सहमति की ओर बढ़ सकती है।",
        "kg_legal_competition_result": "परीक्षा, चयन, विवाद या प्रतिस्पर्धी प्रयास किसी नतीजे की ओर बढ़ सकता है।",
        "kg_spirituality_occult_study": "ज्योतिष, आध्यात्मिक अभ्यास, शोध या किसी गूढ़ विषय का गहरा अध्ययन आकर्षित कर सकता है।",
        "kg_career_staff_hiring": "कर्मचारी, सहायक, ठेकेदार या दूसरी व्यावहारिक मदद मिल सकती है।",
        "kg_career_staff_change": "कर्मचारी या व्यावहारिक सहायक बदल सकता है, काम छोड़ सकता है या नई व्यवस्था की जरूरत पड़ सकती है।",
        "kg_relationship_remarriage_development": "कोई रिश्ता पुनर्विवाह से जुड़ी गंभीर बातचीत या प्रतिबद्धता की ओर बढ़ सकता है।",
        "kg_children_first_child_development": "पहली संतान से जुड़ा फैसला, जिम्मेदारी या महत्वपूर्ण पड़ाव ध्यान मांग सकता है।",
        "kg_children_second_child_development": "दूसरी संतान से जुड़ा फैसला, जिम्मेदारी या महत्वपूर्ण पड़ाव ध्यान मांग सकता है।",
        "kg_children_third_child_development": "तीसरी संतान से जुड़ा फैसला, जिम्मेदारी या महत्वपूर्ण पड़ाव ध्यान मांग सकता है।",
        "kg_relationship_private_intimacy": "आप और आपके साथी को अधिक निजता, स्नेह, शारीरिक निकटता या साथ आराम का समय मिल सकता है।",
        "children": "संतान, रचनात्मकता या पारिवारिक जिम्मेदारी महत्वपूर्ण हो सकती है।", "education": "पढ़ाई या प्रशिक्षण आगे बढ़ सकता है।",
        "income_gain": "आय, बचत या संसाधनों की गतिविधि सक्रिय हो सकती है।",
    }
    base = next((text for houses, text in pathways.get(event_key, []) if houses & transition), fallback.get(event_key, "यह विषय सक्रिय हो सकता है।"))
    return base


def _hindi_activation_reasoning(
    definition: Any, graph: Mapping[str, Any], relevant_rows: Sequence[Mapping[str, Any]],
    anchor_hits: Sequence[int], transition_hits: Sequence[int], outcome_hits: Sequence[int],
    kp_result: Mapping[str, Any], varga: Mapping[str, Any], dkp: Mapping[str, Any],
) -> str:
    by_level: Dict[str, Set[str]] = {}
    for row in (graph.get("houses") or {}).values():
        for channel in row.get("dasha_channels") or []:
            level = str(channel.get("dasha_level") or "")
            planet = str(channel.get("planet") or "")
            if level and planet:
                by_level.setdefault(level, set()).add(planet)
    stack = _hi_join([
        f"{_hi_join([_hi_planet(planet) for planet in sorted(by_level[level])])} {_HI_LEVELS.get(level, 'दशा')}"
        for level in sorted(by_level, key=lambda value: _LEVEL_ORDER.get(value, 99))
    ])
    sentences = [f"सक्रिय दशा क्रम {stack} है।"] if stack else []
    grouped: Dict[Tuple[str, str], Dict[str, Set[int]]] = {}
    for row in relevant_rows:
        house = int(row.get("house") or 0)
        for channel in (row.get("dasha_channels") or []) + (row.get("transit_channels") or []):
            planet = str(channel.get("planet") or "")
            level = str(channel.get("dasha_level") or "")
            mechanism = str(channel.get("mechanism") or "")
            if planet and house and mechanism:
                grouped.setdefault((level, planet), {}).setdefault(mechanism, set()).add(house)
    for (level, planet), mechanisms in sorted(grouped.items(), key=lambda item: (_LEVEL_ORDER.get(item[0][0], 99), item[0][1])):
        clauses = [
            f"{_hi_house_list(houses)} को {label}"
            for mechanism, label in _HI_MECHANISMS.items() if (houses := mechanisms.get(mechanism))
        ]
        if clauses:
            sentences.append(f"{_hi_planet(planet)} {_HI_LEVELS.get(level, 'दशा')} {_hi_join(clauses)} सक्रिय करता है।")
    signature_label = (
        "संबंधित व्यक्ति की घटना"
        if str(getattr(definition, "event_kind", "native")) == "relative"
        else _hindi_label(definition.key, dkp)
    )
    signature = f"{signature_label} के लिए {_hi_house_list(anchor_hits)} मूल विषय खोलता है और {_hi_house_list(transition_hits)} परिवर्तन का रास्ता सक्रिय करता है।"
    if outcome_hits:
        signature += f" {_hi_house_list(outcome_hits)} परिणाम की संभावना को अधिक ठोस बनाता है।"
    else:
        signature += f" परिणाम भाव ({_hi_house_list(definition.outcome.houses)}) सक्रिय नहीं हैं, इसलिए मामला तैयारी तक सीमित रह सकता है।"
    sentences.append(signature)
    kp_verdict = str(kp_result.get("verdict") or "unavailable")
    kp_text = {
        "supported": "KP इस संयोजन की स्वतंत्र पुष्टि करता है",
        "qualified": "KP से आंशिक स्वतंत्र समर्थन मिलता है",
        "pressured": "KP उपलब्ध है, पर आवश्यक घटना-भावों को स्वतंत्र रूप से नहीं जोड़ता",
        "blocked": "KP के कस्प और कारक आवश्यक घटना-भावों से अधिक बाधा वाले भावों पर जोर देते हैं",
        "unavailable": "KP पुष्टि उपलब्ध नहीं है",
    }.get(kp_verdict, "KP पुष्टि उपलब्ध नहीं है")
    varga_text = _varga_confirmation_sentence(varga, "hi")
    sentences.append(f"{kp_text}; {varga_text}।")
    return " ".join(sentences)


def _priority_score(
    *, anchor_profile: Mapping[str, Any], transition_profile: Mapping[str, Any],
    outcome_profile: Mapping[str, Any], kp_result: Mapping[str, Any],
    varga: Mapping[str, Any], levels: Sequence[str],
) -> Tuple[int, List[str]]:
    """Rank manifestations without presenting the number as a probability."""
    score = 30
    factors: List[str] = []
    if anchor_profile["direct_dasha"]:
        score += 15
        factors.append("anchor opened by direct natal lordship/placement")
    elif anchor_profile["aspect_dasha"]:
        score += 3
        factors.append("anchor opened by natal aspect")
    if transition_profile["direct_dasha"]:
        score += 9
        factors.append("transition opened directly by dasha")
    elif transition_profile["aspect_dasha"]:
        score += 4
        factors.append("transition opened by dasha aspect")
    if transition_profile["direct_transit"]:
        score += 8
        factors.append("transition timed by transit placement")
    elif transition_profile["aspect_transit"]:
        score += 3
        factors.append("transition timed by transit aspect")
    if outcome_profile["direct_dasha"] or outcome_profile["aspect_dasha"]:
        score += 5
        factors.append("outcome house opened by dasha")
    if outcome_profile["direct_transit"]:
        score += 5
        factors.append("outcome timed by transit placement")
    elif outcome_profile["aspect_transit"]:
        score += 2
        factors.append("outcome timed by transit aspect")
    bridge = set(anchor_profile["dasha_planets"]) & (
        set(transition_profile["dasha_planets"]) | set(transition_profile["transit_planets"])
    )
    if bridge:
        score += 6
        factors.append(f"same carrier links anchor and transition ({_natural_join(sorted(bridge))})")
    score += min(8, 2 * len(levels))
    if len(levels) >= 2:
        factors.append(f"confirmed across {len(levels)} core dasha levels")
    if kp_result.get("verdict") == "supported":
        score += 9
        factors.append("KP independently supported")
    elif kp_result.get("verdict") == "qualified":
        score += 4
        factors.append("KP partially supported")
    if varga.get("confirmed"):
        score += 7
        factors.append(f"{varga.get('chart')} carrier confirmed")
    return score, factors


def _select_publishable(candidates: Sequence[Mapping[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    ordered = [dict(row) for row in sorted(
        candidates, key=lambda row: (-int(row.get("priority_score") or 0), row.get("event_key") or "")
    )]
    mode = v3_publication_mode()
    legacy_layer = bool(ordered) and str(ordered[0].get("accuracy_layer") or "") == "legacy_v3_6"
    eligible = ordered if legacy_layer else [
        row for row in ordered if str(row.get("support_grade") or "C") in {"A", "B"}
    ]
    if mode == "exhaustive":
        selected = ordered
    elif len(eligible) <= 3:
        selected = eligible
    else:
        top_score = int(eligible[0].get("priority_score") or 0)
        threshold = top_score - 12
        selected = []
        used_domains: Set[str] = set()
        # First show distinct life areas with evidence reasonably close to the leader.
        for row in eligible:
            domain = str(row.get("life_domain") or row.get("event_key") or "")
            if int(row.get("priority_score") or 0) >= threshold and domain not in used_domains:
                selected.append(row)
                used_domains.add(domain)
            if len(selected) == 5:
                break
        # Never collapse a multi-event month back to one headline.
        for row in eligible:
            if len(selected) >= min(3, len(eligible)):
                break
            if not any(item.get("candidate_id") == row.get("candidate_id") for item in selected):
                selected.append(row)
        selected = sorted(selected, key=lambda row: (-int(row.get("priority_score") or 0), row.get("event_key") or ""))[:5]
    selected_ids = {row.get("candidate_id") for row in selected}
    background = [row for row in ordered if row.get("candidate_id") not in selected_ids]
    summary = {
        "mode": mode,
        "qualified_count": len(ordered),
        "published_count": len(selected),
        "background_count": len(background),
        "rule": "Prioritized mode shows up to five Grade A/B life areas within twelve ranking points of the leader, with at least three when three qualify. Grade C remains a weak signal. Exhaustive mode publishes every qualified candidate.",
    }
    return selected, background, summary


def _select_people_candidates(
    candidates: Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    ordered = [dict(row) for row in sorted(
        candidates, key=lambda row: (-int(row.get("priority_score") or 0), row.get("event_key") or "")
    )]
    visible: List[Dict[str, Any]] = []
    used_subjects: Set[str] = set()
    for row in ordered:
        subject = str(row.get("subject_key") or "relative")
        if str(row.get("support_grade") or "C") not in {"A", "B"} or subject in used_subjects:
            continue
        visible.append(row)
        used_subjects.add(subject)
    visible_ids = {row.get("candidate_id") for row in visible}
    overflow = [row for row in ordered if row.get("candidate_id") not in visible_ids]
    return visible, overflow, {
        "qualified_count": len(ordered),
        "visible_count": len(visible),
        "overflow_count": len(overflow),
        "rule": "Show one leading Grade A/B event for every qualified person; additional events for the same person remain available under that person's details.",
    }


def _display_copy(tier: str, reason: str, language: str, grade: str) -> Tuple[str, str, str]:
    """Return a non-probabilistic label and plain explanation for a UI tier."""
    hi = _language_code(language) == "hi"
    if hi:
        tier_labels = {
            "primary": "मुख्य संभावना",
            "also_possible": "यह भी संभव है",
            "ongoing_background": "चल रहा विषय",
            "annual_context": "वार्षिक पृष्ठभूमि",
            "weak_signal": "कमज़ोर संकेत",
        }
        grade_labels = {"A": "मज़बूत संकेत", "B": "मध्यम संकेत", "C": "कमज़ोर संकेत"}
        explanations = {
            "strongest_for_month": "यह इस महीने की सबसे साफ़ समर्थित संभावनाओं में से एक है। फिर भी यह संभावना है, पक्का परिणाम नहीं।",
            "competing_event_stronger": "यह भी समर्थित है, लेकिन इसी जीवन क्षेत्र की एक दूसरी संभावना इस महीने अधिक साफ़ दिखाई देती है।",
            "not_in_top_monthly_events": "इसके संकेत मौजूद हैं, लेकिन इस महीने ऊपर दिखाई गई घटनाओं का समय या समर्थन अधिक साफ़ है।",
            "persistent_theme_outside_peak": "यह विषय लंबे समय तक खुला रह सकता है, लेकिन इस महीने इसके होने का समय बहुत साफ़ नहीं है।",
            "continuing_event_window": "यह विषय पास के चरम महीने से जारी है, लेकिन इस महीने इसे नई घटना नहीं माना गया है।",
            "annual_permission_outside_peak": "वर्ष में इस विषय की संभावना खुली है, लेकिन इस महीने इसे घटना मानने लायक खास समय-संकेत नहीं है।",
            "weak_support": "कुछ संकेत मौजूद हैं, लेकिन पुष्टि इतनी मिली-जुली है कि इसे अभी भविष्यवाणी नहीं माना जाना चाहिए।",
        }
    else:
        tier_labels = {
            "primary": "Main possibility",
            "also_possible": "Also possible",
            "ongoing_background": "Ongoing theme",
            "annual_context": "Annual background",
            "weak_signal": "Weak signal",
        }
        grade_labels = {"A": "Strong indication", "B": "Moderate indication", "C": "Weak indication"}
        explanations = {
            "strongest_for_month": "This is one of the clearest supported possibilities for the month. It is still a possibility, not a certainty.",
            "competing_event_stronger": "This is also supported, but another possibility in the same area of life is clearer this month.",
            "not_in_top_monthly_events": "There is meaningful support for this, but the events shown above have clearer support or timing this month.",
            "persistent_theme_outside_peak": "This theme may remain open for a longer period, but its timing is not especially clear in this month.",
            "continuing_event_window": "This theme continues from a nearby peak month, but it is not counted as a new event this month.",
            "annual_permission_outside_peak": "This possibility is open during the year, but this month lacks a distinctive timing signal for treating it as an event.",
            "weak_support": "Some supporting signs are present, but the confirmation is too mixed to treat this as a prediction.",
        }
    tier_label = tier_labels[tier]
    support_label = (
        ("पृष्ठभूमि संकेत" if hi else "Background indication")
        if tier in {"ongoing_background", "annual_context"} else grade_labels.get(grade, grade_labels["C"])
    )
    return tier_label, support_label, explanations[reason]


def _annotate_display_tiers(months: Mapping[str, Any], language: str) -> None:
    """Split omitted candidates by meaning while retaining legacy combined lists."""
    for month in months.values():
        native_primary = list(month.get("publishable_candidates") or [])
        people_primary = list(month.get("people_candidates") or [])
        native_primary_ids = {str(row.get("candidate_id")) for row in native_primary}
        people_primary_ids = {str(row.get("candidate_id")) for row in people_primary}
        primary_domains = {str(row.get("life_domain") or "") for row in native_primary}
        people_primary_domains = {
            (str(row.get("subject_key") or "relative"), str(row.get("life_domain") or ""))
            for row in people_primary
        }

        def classify(candidate: Dict[str, Any], *, person: bool = False) -> Dict[str, Any]:
            candidate_id = str(candidate.get("candidate_id"))
            person = person or str(candidate.get("subject_key") or "self") != "self"
            is_primary = candidate_id in (people_primary_ids if person else native_primary_ids)
            grade = str(candidate.get("support_grade") or "C")
            legacy_primary = is_primary and str(candidate.get("accuracy_layer") or "") == "legacy_v3_6"
            if grade not in {"A", "B"} and not legacy_primary:
                tier, reason = "weak_signal", "weak_support"
            elif is_primary:
                tier, reason = "primary", "strongest_for_month"
            elif candidate.get("monthly_peak_status") == "continuation":
                tier, reason = "ongoing_background", "continuing_event_window"
            elif candidate.get("monthly_peak_status") in {"active_outside_peak", "untimed_annual_permission"}:
                tier, reason = "annual_context", "annual_permission_outside_peak"
            elif candidate.get("background_permission_houses") and not candidate.get("persistent_permission_peak"):
                tier, reason = "ongoing_background", "persistent_theme_outside_peak"
            else:
                domain = str(candidate.get("life_domain") or "")
                competing = (
                    (str(candidate.get("subject_key") or "relative"), domain) in people_primary_domains
                    if person else domain in primary_domains
                )
                tier = "also_possible"
                reason = "competing_event_stronger" if competing else "not_in_top_monthly_events"
            tier_label, support_label, explanation = _display_copy(tier, reason, language, grade)
            candidate.update({
                "display_tier": tier,
                "display_tier_label": tier_label,
                "support_label": support_label,
                "display_reason": reason,
                "display_explanation": explanation,
            })
            return candidate

        for field, person in (
            ("qualified_candidates", False),
            ("publishable_candidates", False),
            ("background_candidates", False),
            ("people_candidates", True),
            ("people_background_candidates", True),
        ):
            month[field] = [classify(row, person=person) for row in month.get(field) or []]

        native_background = list(month.get("background_candidates") or [])
        month["also_possible_candidates"] = [row for row in native_background if row.get("display_tier") == "also_possible"]
        month["ongoing_background_candidates"] = [row for row in native_background if row.get("display_tier") == "ongoing_background"]
        month["weak_signal_candidates"] = [row for row in native_background if row.get("display_tier") == "weak_signal"]
        month["annual_context_candidates"] = [row for row in native_background if row.get("display_tier") == "annual_context"]

        people_background = list(month.get("people_background_candidates") or [])
        month["people_also_possible_candidates"] = [row for row in people_background if row.get("display_tier") == "also_possible"]
        month["people_ongoing_background_candidates"] = [row for row in people_background if row.get("display_tier") == "ongoing_background"]
        month["people_weak_signal_candidates"] = [row for row in people_background if row.get("display_tier") == "weak_signal"]
        month["people_annual_context_candidates"] = [row for row in people_background if row.get("display_tier") == "annual_context"]
        if isinstance(month.get("selection_summary"), dict):
            month["selection_summary"].update({
                "also_possible_count": len(month["also_possible_candidates"]),
                "ongoing_background_count": len(month["ongoing_background_candidates"]),
                "weak_signal_count": len(month["weak_signal_candidates"]),
                "annual_context_count": len(month["annual_context_candidates"]),
            })
        if not month.get("publishable_candidates"):
            if month.get("ongoing_background_candidates"):
                month["prediction_state"] = "background_themes_only"
            elif month.get("weak_signal_candidates"):
                month["prediction_state"] = "weak_signals_only"
            elif month.get("annual_context_candidates"):
                month["prediction_state"] = "quiet_month"


def _candidate_from_definition(
    *, definition: Any, graph: Mapping[str, Any], month: int, year: int,
    kp: Mapping[str, Any], context: Mapping[str, Any], dkp: Mapping[str, Any], language: str,
) -> Optional[Dict[str, Any]]:
    houses = graph.get("houses") or {}
    selected_accuracy_layer = accuracy_layer_mode()
    delivery_mode = selected_accuracy_layer in {"delivery_v1", "integrated_v2"}
    integrated_mode = selected_accuracy_layer == "integrated_v2"
    dasha_open = {int(h) for h in graph.get("dasha_open_houses") or []}
    dasha_transit_permission = {
        int(h) for h in graph.get("core_dasha_transit_occupied_houses") or []
    } if integrated_mode else set()
    anchor_permission = dasha_open | dasha_transit_permission
    transit = {int(h) for h in graph.get("transit_triggered_houses") or []}
    anchor = set(int(h) for h in definition.anchor.houses)
    transition = set(int(h) for h in definition.transition.houses)
    legacy_source_key = str(getattr(definition, "source_event_key", "") or definition.key)
    if selected_accuracy_layer == "legacy_v3_6" and legacy_source_key == "foreign_travel":
        legacy_document_house = (
            rotate_relative_house(int(definition.reference_house), 3)
            if str(getattr(definition, "event_kind", "native")) == "relative"
            else 3
        )
        transition.add(legacy_document_house)
    outcome = set(int(h) for h in definition.outcome.houses)
    subject_anchor = set(int(h) for h in ((definition.subject_anchor.houses if definition.subject_anchor else ())))
    # The relative's reference house is the origin for house rotation, not an
    # event gate.  Only the already-rotated anchor/transition/outcome houses
    # participate in event permission and timing.
    event_houses = anchor | transition | outcome
    anchor_natal_dasha_hits = sorted(anchor & dasha_open)
    anchor_dasha_transit_hits = sorted(anchor & dasha_transit_permission)
    anchor_hits = sorted(anchor & anchor_permission)
    transition_dasha = sorted(transition & dasha_open)
    transition_hits = sorted(transition & (dasha_open | transit))
    outcome_hits = sorted(outcome & (dasha_open | transit))
    transit_hits = sorted(event_houses & transit)
    if definition.anchor.require_all:
        anchor_ok = anchor.issubset(anchor_permission)
    else:
        anchor_ok = len(anchor_hits) >= max(1, int(definition.anchor.minimum_hits))
    if definition.transition.require_all:
        transition_ok = transition.issubset(dasha_open | transit)
    else:
        transition_ok = len(transition_hits) >= max(1, int(definition.transition.minimum_hits))
    if definition.outcome.required:
        if definition.outcome.require_all:
            outcome_ok = outcome.issubset(dasha_open | transit)
        else:
            outcome_ok = len(outcome_hits) >= max(1, int(definition.outcome.minimum_hits))
    else:
        outcome_ok = True
    if not (anchor_ok and transition_ok and outcome_ok and transit_hits):
        return None
    required_direct_transit_houses = {
        int(house) for house in getattr(definition, "required_direct_transit_houses", ())
    }
    direct_timing_channels: List[Dict[str, Any]] = []
    if integrated_mode and required_direct_transit_houses:
        direct_timing_channels = [
            {**channel, "house": int(house)}
            for house in required_direct_transit_houses
            for channel in (houses.get(str(house)) or {}).get("transit_channels") or []
            if channel.get("mechanism") == "transit_occupation"
            and (
                not getattr(definition, "direct_transit_excludes_slow_planets", False)
                or channel.get("planet") not in _SLOW_TRANSIT_PLANETS
            )
        ]
        if not direct_timing_channels:
            return None
    is_relative = str(getattr(definition, "event_kind", "native")) == "relative"
    source_event_key = str(getattr(definition, "source_event_key", "") or definition.key)
    subject_anchor_natal_hits = sorted(subject_anchor & dasha_open)
    subject_anchor_dasha_transit_hits = sorted(subject_anchor & dasha_transit_permission)
    # Only retain the direct-transit houses actually needed to pass a required
    # gate. Optional extra occupation must not turn an already natal-open event
    # into a background-permission event.
    slow_direct_permission_houses = {
        house for house in dasha_transit_permission
        if any(
            channel.get("mechanism") == "transit_occupation"
            and channel.get("dasha_level") in _CORE_LEVELS
            and channel.get("planet") in _SLOW_TRANSIT_PLANETS
            for channel in (houses.get(str(house)) or {}).get("transit_channels") or []
        )
        and not any(
            channel.get("mechanism") == "transit_occupation"
            and channel.get("dasha_level") in _CORE_LEVELS
            and channel.get("planet") not in _SLOW_TRANSIT_PLANETS
            for channel in (houses.get(str(house)) or {}).get("transit_channels") or []
        )
    }
    missing_anchor_permission = set(anchor_dasha_transit_hits) - set(anchor_natal_dasha_hits)
    if definition.anchor.require_all:
        required_anchor_transit = missing_anchor_permission
    else:
        needed = max(0, int(definition.anchor.minimum_hits) - len(anchor_natal_dasha_hits))
        required_anchor_transit = set(sorted(
            missing_anchor_permission,
            key=lambda house: (house in slow_direct_permission_houses, house),
        )[:needed])
    background_permission_houses = required_anchor_transit & slow_direct_permission_houses
    background_permission_sources = {
        (str(channel.get("planet") or ""), str(channel.get("dasha_level") or ""))
        for house in background_permission_houses
        for channel in (houses.get(str(house)) or {}).get("transit_channels") or []
        if channel.get("mechanism") == "transit_occupation"
        and channel.get("dasha_level") in _CORE_LEVELS
        and channel.get("planet") in _SLOW_TRANSIT_PLANETS
    }
    timing_role_houses = transition | outcome
    independent_timing_channels = [
        {**channel, "house": int(house)}
        for house in timing_role_houses
        for channel in (
            ((houses.get(str(house)) or {}).get("dasha_channels") or [])
            + ((houses.get(str(house)) or {}).get("transit_channels") or [])
        )
        if (
            channel.get("dasha_level") in {"pratyantardasha", "sookshma"}
            or (
                str(channel.get("mechanism") or "").startswith("transit_")
                and channel.get("planet") not in _SLOW_TRANSIT_PLANETS
            )
        )
        and (str(channel.get("planet") or ""), str(channel.get("dasha_level") or ""))
        not in background_permission_sources
    ]
    # A core dasha lord occupying an event anchor supplies background
    # permission. It must not also time its own event.
    if integrated_mode and background_permission_houses and not independent_timing_channels:
        return None
    if is_relative and source_event_key == "health":
        # A relative-health theme needs both natal/dasha permission and current
        # timing inside the derived medical houses.  A transit-only pile-up or
        # a transit touching houses outside the derived medical set is insufficient.
        if not transition_dasha or not (transition & transit):
            return None

    relevant_rows = [houses[str(h)] for h in sorted(event_houses) if str(h) in houses]
    levels = sorted({level for row in relevant_rows for level in row.get("dasha_levels") or [] if level in _CORE_LEVELS}, key=lambda x: -_LEVEL_RANK.get(x, 0))
    dasha_planets = sorted({p for row in relevant_rows for p in row.get("dasha_planets") or []})
    transit_planets = sorted({p for row in relevant_rows for p in row.get("transit_planets") or []})
    evidence_ids = list(dict.fromkeys(eid for row in relevant_rows for eid in row.get("evidence_ids") or []))
    channels = [c for row in relevant_rows for c in (row.get("dasha_channels") or []) + (row.get("transit_channels") or [])]
    starts = [c.get("start_date") for c in channels if c.get("start_date")]
    ends = [c.get("end_date") for c in channels if c.get("end_date")]
    start = min(starts) if starts else f"{year}-{month:02d}-01"
    end = max(ends) if ends else f"{year}-{month:02d}-28"

    promise = natal_promise(source_event_key, anchor, transition, outcome, context) if delivery_mode else {
        "verdict": "legacy_not_evaluated", "score": 0, "reasons": [], "limitations": []
    }
    delivery = planet_delivery(source_event_key, dasha_planets, event_houses, context) if delivery_mode else {
        "verdict": "legacy_not_evaluated", "support_score": 0, "pressure_score": 0, "carriers": []
    }
    obstruction_key = source_event_key
    obstruction = obstruction_profile(obstruction_key, graph, outcome) if delivery_mode else {
        "verdict": "legacy_not_evaluated", "score": 0, "active_houses": []
    }
    exact_transits = exact_transit_judgment(
        context, graph, kp, source_event_key, event_houses, anchor, dasha_planets,
    ) if integrated_mode else {
        "available": False, "event_contacts": [], "reference_contacts": [],
        "kp_cusp_contacts": [], "stations": [], "limitations": [],
    }
    kp_result = (
        kp_judgment(
            kp, anchor, event_houses,
            ({rotate_relative_house(definition.reference_house, house) for house in EVENT_OBSTRUCTION_HOUSES.get(source_event_key, set())} if is_relative else EVENT_OBSTRUCTION_HOUSES.get(source_event_key, set())),
            dasha_planets, exact_transits.get("kp_cusp_contacts") or [],
        ) if delivery_mode else _kp_confirmation(kp, anchor, event_houses)
    )
    varga = (
        varga_judgment(
            context, definition.varga, _VARGA_KEYS.get(definition.varga), source_event_key,
            set(int(house) for house in (definition.varga_houses or event_houses)),
            dasha_planets, promise, delivery,
        )
        if delivery_mode else _varga_confirmation(context, definition.varga, anchor | transition, set(dasha_planets))
    )
    subject_varga_spec = _SUBJECT_VARGAS.get(str(getattr(definition, "subject_key", "self"))) if is_relative else None
    subject_varga_confirmation = (
        _varga_confirmation(
            context, subject_varga_spec[0], subject_varga_spec[1], set(dasha_planets),
        )
        if subject_varga_spec else
        {"chart": None, "available": False, "confirmed": False, "carrier_hits": [], "role": "not_applicable"}
    )
    bhava_disambiguation = _bhava_channel_disambiguation(
        definition,
        source_event_key=source_event_key,
        dasha_planets=dasha_planets,
        transit_planets=transit_planets,
        varga=varga,
        transition_hits=transition_hits,
        outcome_hits=outcome_hits,
    )
    ashtakavarga = ashtakavarga_judgment(
        context, graph, dasha_planets, event_houses,
    ) if integrated_mode else {"available": False, "verdict": "not_evaluated_in_layer", "rows": []}
    supporting_systems = supporting_systems_judgment(
        context, source_event_key, event_houses, month, year,
    ) if integrated_mode else {"available": False, "systems": [], "capped_priority_adjustment": 0}
    birth_time_reliability = birth_time_reliability_judgment(
        context, varga, kp_result,
    ) if integrated_mode else {"verdict": "not_evaluated_in_layer"}
    anchor_profile = _role_profile(anchor, graph)
    transition_profile = _role_profile(transition, graph)
    outcome_profile = _role_profile(outcome, graph)
    phase = _phase_from_profiles(outcome_profile)
    dimensions = outcome_dimensions(phase, obstruction, delivery, kp_result, varga, ashtakavarga) if delivery_mode else {
        "initiation": "legacy", "ease": "legacy", "result": phase,
        "permanence": "legacy", "completion": "legacy",
    }
    timing = timing_windows(
        graph, anchor, transition, event_houses,
        require_all_anchor=bool(definition.anchor.require_all),
        require_all_transition=bool(definition.transition.require_all),
        minimum_anchor_hits=int(definition.anchor.minimum_hits),
        minimum_transition_hits=int(definition.transition.minimum_hits),
        minimum_transition_dasha_hits=(1 if is_relative and source_event_key == "health" else 0),
        require_transition_transit=is_relative and source_event_key == "health",
        required_dasha_houses=set(),
        required_outcome_houses=(outcome if definition.outcome.required else set()),
        minimum_outcome_hits=(int(definition.outcome.minimum_hits) if definition.outcome.required else 0),
        require_all_outcome=bool(definition.outcome.require_all),
        allow_core_dasha_transit_permission=integrated_mode,
        require_independent_timing=integrated_mode and bool(background_permission_houses),
    ) if delivery_mode else {"windows": [], "resolution": "legacy_month_span", "limitations": []}
    if integrated_mode and background_permission_houses and not (timing.get("windows") or []):
        return None
    if delivery_mode:
        clean_delivery = delivery.get("verdict") == "supportive" and obstruction.get("verdict") == "low"
        promised = promise.get("verdict") in {"strong", "available"}
        if (
            len(levels) >= 2
            and promise.get("verdict") == "strong"
            and clean_delivery
            and (not integrated_mode or birth_time_reliability.get("verdict") == "stable")
            and kp_result["verdict"] == "supported"
            and varga["confirmed"]
        ):
            grade = "A"
        elif (
            len(levels) >= 2
            and promised
            and delivery.get("verdict") in {"supportive", "mixed"}
            and obstruction.get("verdict") != "high"
            and (kp_result["verdict"] in {"supported", "qualified"} or varga.get("verdict") in {"confirmed", "mixed"})
        ):
            grade = "B"
        else:
            grade = "C"
    elif len(levels) >= 2 and kp_result["verdict"] == "supported" and varga["confirmed"]:
        grade = "A"
    elif len(levels) >= 2 and (kp_result["verdict"] in {"supported", "qualified"} or varga["confirmed"]):
        grade = "B"
    else:
        grade = "C"
    score = 45 + 5 * len(levels) + 3 * len(transit_planets) + (8 if outcome_hits else 0)
    score += 8 if kp_result["verdict"] == "supported" else 3 if kp_result["verdict"] == "qualified" else 0
    score += 6 if varga["confirmed"] else 0
    priority_score, priority_factors = _priority_score(
        anchor_profile=anchor_profile,
        transition_profile=transition_profile,
        outcome_profile=outcome_profile,
        kp_result=kp_result,
        varga=varga,
        levels=levels,
    )
    if delivery_mode:
        promise_adjustment = {"strong": 10, "available": 6, "weak": -6, "unavailable": 0}.get(str(promise.get("verdict")), 0)
        delivery_adjustment = {"supportive": 8, "mixed": 1, "obstructed": -10, "unavailable": 0}.get(str(delivery.get("verdict")), 0)
        obstruction_adjustment = {"low": 0, "moderate": -4, "high": -9}.get(str(obstruction.get("verdict")), 0)
        kp_block_adjustment = -10 if kp_result.get("verdict") == "blocked" else 0
        varga_mixed_adjustment = 2 if varga.get("verdict") == "mixed" else 0
        av_adjustment = {"supportive": 2, "mixed": 0, "pressured": -2}.get(str(ashtakavarga.get("verdict")), 0) if integrated_mode else 0
        support_adjustment = int(supporting_systems.get("capped_priority_adjustment") or 0) if integrated_mode else 0
        birth_time_adjustment = {"stable": 0, "qualified": -1, "unknown": -2, "sensitive": -6}.get(str(birth_time_reliability.get("verdict")), 0) if integrated_mode else 0
        exact_rows = exact_transits.get("event_contacts") or []
        exact_contact_adjustment = (
            (2 + int(any(row.get("peak_phase") == "exact" for row in exact_rows)))
            if integrated_mode and exact_rows else 0
        )
        priority_score += (
            promise_adjustment + delivery_adjustment + obstruction_adjustment
            + kp_block_adjustment + varga_mixed_adjustment + av_adjustment
            + support_adjustment + birth_time_adjustment + exact_contact_adjustment
        )
        priority_factors.extend([
            f"natal promise {promise.get('verdict')} ({promise_adjustment:+d})",
            f"planet delivery {delivery.get('verdict')} ({delivery_adjustment:+d})",
            f"obstruction {obstruction.get('verdict')} ({obstruction_adjustment:+d})",
        ])
        if integrated_mode:
            priority_factors.extend([
                f"daily-sampled exact contacts ({exact_contact_adjustment:+d}, capped)",
                f"BAV/Kakshya {ashtakavarga.get('verdict')} ({av_adjustment:+d})",
                f"independent supporting systems ({support_adjustment:+d}, capped)",
                f"birth-time reliability {birth_time_reliability.get('verdict')} ({birth_time_adjustment:+d})",
            ])
    personal = {} if is_relative else _personalize(definition.key, dkp)
    label = personal.get("label") or definition.label
    detailed_explanations = v3_explanation_version() == "detailed_v2"
    if detailed_explanations:
        activation_reasoning = " ".join(
            [_period_stack_sentence(graph)]
            + _planet_activation_sentences(relevant_rows)
            + [
                _event_signature_sentence(definition, anchor_hits, transition_hits, outcome_hits),
                _confirmation_sentence(kp_result, varga),
            ]
        )
        manifestations = _detailed_manifestations(definition.key, graph, dkp, bhava_disambiguation)
    else:
        activation_reasoning = (
            f"Dasha-open anchor H{','.join(map(str, anchor_hits))}; "
            f"transition H{','.join(map(str, transition_hits))}; "
            f"transit-triggered H{','.join(map(str, transit_hits))}."
        )
        manifestations = [
            {"scenario": label, "reasoning": "This event combination passed the dasha-house and transit gates."}
        ]
    candidate_id = "ET3-" + hashlib.sha1(
        f"{year}:{month}:{definition.key}:{','.join(evidence_ids)}".encode("utf-8", "ignore")
    ).hexdigest()[:12]
    timing_rows = timing.get("windows") or []
    if timing_rows:
        start = str(timing_rows[0].get("start_date") or start)
        end = str(timing_rows[-1].get("end_date") or end)
    display_phase = "obstructed" if dimensions.get("ease") == "obstructed" else phase
    claim_scope = (
        "broad_theme_only"
        if delivery_mode and promise.get("verdict") == "weak"
        else "event_specific"
        if delivery_mode and promise.get("verdict") in {"strong", "available"}
        else "data_limited"
    )
    candidate = {
        "candidate_id": candidate_id,
        "event_key": definition.key,
        "life_domain": _EVENT_DOMAINS.get(definition.key, definition.key),
        "event_family": label,
        "prediction": _deterministic_prediction(
            definition.key, label, transition_hits, phase, transit_planets, kp_result, varga,
        ),
        "possible_manifestations": manifestations,
        "activation_reasoning": activation_reasoning,
        "trigger_logic": f"{'>'.join(levels)} carriers {', '.join(dasha_planets)}; transit carriers {', '.join(transit_planets)}.",
        "anchor_houses": sorted(anchor),
        "anchor_hits": anchor_hits,
        "anchor_natal_dasha_hits": anchor_natal_dasha_hits,
        "anchor_dasha_transit_hits": anchor_dasha_transit_hits,
        "subject_anchor_natal_dasha_hits": subject_anchor_natal_hits,
        "subject_anchor_dasha_transit_hits": subject_anchor_dasha_transit_hits,
        "background_permission_houses": sorted(background_permission_houses),
        "background_permission_sources": [
            {"planet": planet, "dasha_level": level}
            for planet, level in sorted(background_permission_sources)
        ],
        "independent_timing_channels": independent_timing_channels,
        "required_direct_transit_houses": sorted(required_direct_transit_houses),
        "direct_timing_channels": direct_timing_channels,
        "transition_houses": sorted(transition),
        "transition_hits": transition_hits,
        "transition_dasha_hits": transition_dasha,
        "outcome_houses": sorted(outcome),
        "outcome_hits": outcome_hits,
        "transit_hits": transit_hits,
        "dasha_levels": levels,
        "dasha_planets": dasha_planets,
        "transit_planets": transit_planets,
        "kp_confirmation": kp_result,
        "varga_confirmation": varga,
        "subject_varga_confirmation": subject_varga_confirmation,
        "bhava_disambiguation": bhava_disambiguation,
        "support_grade": grade,
        "support_score": score,
        "priority_score": priority_score,
        "priority_factors": priority_factors,
        "manifestation_phase": display_phase,
        "claim_scope": claim_scope,
        "timing_windows": timing_rows,
        "exact_transit_contacts": exact_transits,
        "ashtakavarga_confirmation": ashtakavarga,
        "supporting_systems": supporting_systems,
        "birth_time_reliability": birth_time_reliability,
        "timing_resolution": timing.get("resolution"),
        "outcome_dimensions": dimensions,
        "natal_promise": promise,
        "planet_delivery": delivery,
        "obstruction_profile": obstruction,
        "accuracy_layer": selected_accuracy_layer,
        "accuracy_limitations": list(dict.fromkeys(
            list(promise.get("limitations") or [])
            + list(delivery.get("limitations") or [])
            + list(timing.get("limitations") or [])
            + list(exact_transits.get("limitations") or [])
            + list((context.get("supporting_systems") or {}).get("limitations") or [])
        )),
        "intensity": "High" if grade == "A" else "Medium" if grade == "B" else "Low",
        "evidence_ids": evidence_ids,
        "start_date": start,
        "end_date": end,
        "desh_kaal_patra": {
            "employment_state": dkp.get("employment_state"),
            "relationship_state": dkp.get("relationship_state"),
            "parenthood_state": dkp.get("parenthood_state"),
            "eligible_relative_subjects": dkp.get("eligible_relative_subjects"),
            "fact_basis": dkp.get("fact_basis"),
        },
        "forbidden_terms": personal.get("forbidden_terms") or [],
        "explanation_version": v3_explanation_version(),
    }
    if getattr(definition, "knowledge_pattern_id", ""):
        candidate["life_domain"] = str(definition.knowledge_domain).removeprefix("domain.")
        candidate["manifestation_kg"] = {
            "pattern_id": definition.knowledge_pattern_id,
            "manifestation_id": definition.knowledge_manifestation_id,
            "ontology_version": definition.knowledge_ontology_version,
            "review_status": definition.knowledge_review_status,
            "claim_basis": definition.knowledge_claim_basis,
            "source_ids": list(definition.knowledge_source_ids),
            "timeline_profile": source_event_key,
            "role_mapping": {
                "anchor_houses": sorted(anchor),
                "transition_houses": sorted(transition),
                "outcome_houses": sorted(outcome),
            },
            "evidence_gate_result": "qualified_candidate",
        }
    if delivery_mode:
        closest_contact = min(
            exact_transits.get("event_contacts") or [],
            key=lambda row: float(row.get("peak_orb") or 999.0),
            default=None,
        )
        candidate["activation_reasoning"] += (
            f" Natal promise is {promise.get('verdict')} (score {promise.get('score')}); "
            f"active-planet delivery is {delivery.get('verdict')} "
            f"({delivery.get('support_score')} support versus {delivery.get('pressure_score')} pressure); "
            f"event-specific obstruction is {obstruction.get('verdict')}. "
            f"Initiation is {dimensions.get('initiation')}, ease is {dimensions.get('ease')}, "
            f"the result is {dimensions.get('result')}, and permanence is {dimensions.get('permanence')}."
        )
        if integrated_mode:
            candidate["activation_reasoning"] += (
                f" BAV/Kakshya is {ashtakavarga.get('verdict')}; independent supporting groups are "
                f"{', '.join(supporting_systems.get('supportive_independence_groups') or []) or 'none'}; "
                f"birth-time reliability is {birth_time_reliability.get('verdict')}."
            )
        if integrated_mode and closest_contact:
            candidate["activation_reasoning"] += (
                f" The closest degree contact is {closest_contact.get('transit_planet')} "
                f"to natal {closest_contact.get('target')} around {closest_contact.get('peak_date')} "
                f"({closest_contact.get('peak_phase')}, orb {closest_contact.get('peak_orb')}°); "
                f"{len(exact_transits.get('event_contacts') or [])} relevant contact windows were retained."
            )
        if display_phase == "obstructed":
            candidate["prediction"] += " Delays or difficulties may make the result less smooth than expected."
        if claim_scope == "broad_theme_only":
            candidate["prediction"] += " More than one kind of outcome is possible, so do not treat this as a fixed event."
    if _language_code(language) == "hi":
        candidate["event_family"] = _hindi_label(definition.key, dkp)
        candidate["prediction"] = _hindi_prediction(
            definition.key, transition_hits, phase, transit_planets, kp_result, varga,
        )
        candidate["possible_manifestations"] = _hindi_manifestations(
            definition.key, graph, dkp, bhava_disambiguation,
        )
        if detailed_explanations:
            candidate["activation_reasoning"] = _hindi_activation_reasoning(
                definition, graph, relevant_rows, anchor_hits, transition_hits, outcome_hits,
                kp_result, varga, dkp,
            )
        else:
            candidate["activation_reasoning"] = (
                f"दशा से खुला मूल भाव {_hi_house_list(anchor_hits)}; परिवर्तन भाव {_hi_house_list(transition_hits)}; "
                f"गोचर से सक्रिय भाव {_hi_house_list(transit_hits)}।"
            )
        candidate["trigger_logic"] = (
            f"दशा स्तर {_hi_join([_HI_LEVELS.get(level, level) for level in levels])}; "
            f"दशा कारक {_hi_join([_hi_planet(planet) for planet in dasha_planets])}; "
            f"गोचर कारक {_hi_join([_hi_planet(planet) for planet in transit_planets])}।"
        )
        if delivery_mode:
            hi_verdict = {
                "strong": "मजबूत", "available": "उपलब्ध", "weak": "कमज़ोर", "unavailable": "अनुपलब्ध",
                "supportive": "सहयोगी", "mixed": "मिश्रित", "obstructed": "बाधित",
                "low": "कम", "moderate": "मध्यम", "high": "अधिक",
                "pressured": "दबावयुक्त", "stable": "स्थिर", "qualified": "सीमित रूप से विश्वसनीय",
                "unknown": "अज्ञात", "sensitive": "समय-संवेदनशील",
            }
            candidate["activation_reasoning"] += (
                f" जन्म कुंडली का मूल समर्थन {hi_verdict.get(str(promise.get('verdict')), str(promise.get('verdict')))} है; "
                f"सक्रिय दशा ग्रहों की परिणाम देने की क्षमता {hi_verdict.get(str(delivery.get('verdict')), str(delivery.get('verdict')))} है; "
                f"घटना-विशेष बाधा {hi_verdict.get(str(obstruction.get('verdict')), str(obstruction.get('verdict')))} है।"
            )
            if integrated_mode:
                candidate["activation_reasoning"] += (
                    f" BAV/कक्ष्या का निर्णय {hi_verdict.get(str(ashtakavarga.get('verdict')), str(ashtakavarga.get('verdict')))} है; "
                    f"जन्म-समय विश्वसनीयता {hi_verdict.get(str(birth_time_reliability.get('verdict')), str(birth_time_reliability.get('verdict')))} है।"
                )
            closest_contact = min(
                exact_transits.get("event_contacts") or [],
                key=lambda row: float(row.get("peak_orb") or 999.0),
                default=None,
            )
            if integrated_mode and closest_contact:
                candidate["activation_reasoning"] += (
                    f" सबसे निकट अंश-संपर्क {closest_contact.get('peak_date')} के आसपास "
                    f"{_hi_planet(str(closest_contact.get('transit_planet') or ''))} और जन्मकालीन "
                    f"{_hi_planet(str(closest_contact.get('target') or ''))} के बीच है "
                    f"(अंतर {closest_contact.get('peak_orb')}°)।"
                )
            if display_phase == "obstructed":
                candidate["prediction"] += " देरी या परेशानी के कारण नतीजा उम्मीद से कम आसान हो सकता है।"
            if claim_scope == "broad_theme_only":
                candidate["prediction"] += " एक से अधिक नतीजे संभव हैं, इसलिए इसे पक्की घटना न मानें।"
    if is_relative:
        relative_copy = _relative_event_copy(
            definition, graph, transition_hits, language, bhava_disambiguation,
            (dkp.get("relative_contexts") or {}).get(str(definition.subject_key)) or {},
        )
        candidate.update({
            "life_domain": f"people_{_EVENT_DOMAINS.get(source_event_key, source_event_key)}",
            "event_family": relative_copy["label"],
            "prediction": relative_copy["prediction"],
            "possible_manifestations": relative_copy["manifestations"],
            "subject_key": definition.subject_key,
            "subject_label": str(relative_copy["label"]).split(" · ", 1)[0],
            "subject_reference_house": definition.reference_house,
            "source_event_key": source_event_key,
            "intervention_signal_supported": relative_copy["intervention_supported"],
            "claim_scope": "broad_health_attention" if source_event_key == "health" else "subject_relative_event",
            "relative_desh_kaal_patra": {
                "employment_state": ((dkp.get("relative_contexts") or {}).get(str(definition.subject_key)) or {}).get("employment_state", "unknown"),
                "age_years": ((dkp.get("relative_contexts") or {}).get(str(definition.subject_key)) or {}).get("age_years"),
                "location_context": ((dkp.get("relative_contexts") or {}).get(str(definition.subject_key)) or {}).get("location_context", "unknown"),
                "profile_source": ((dkp.get("relative_contexts") or {}).get(str(definition.subject_key)) or {}).get("profile_source", "chat_fact"),
            },
        })
        if source_event_key == "health":
            candidate["subject_relative_houses"] = {
                "illness_or_treatment": rotate_relative_house(definition.reference_house, 6),
                "acute_change_or_intervention": rotate_relative_house(definition.reference_house, 8),
                "rest_or_hospital_setting": rotate_relative_house(definition.reference_house, 12),
            }
        if _language_code(language) == "hi":
            candidate["activation_reasoning"] += (
                f" H{definition.reference_house} संबंधित व्यक्ति के भावों की गणना का आरंभ है; इसका सक्रिय होना अनिवार्य नहीं है। घटना के मूल भाव "
                f"{_hi_house_list(anchor)}, परिवर्तन भाव {_hi_house_list(transition)} और परिणाम भाव {_hi_house_list(outcome)} उनके भावों से निकले हैं।"
            )
        else:
            candidate["activation_reasoning"] += (
                f" H{definition.reference_house} is the reference ascendant used to rotate this person's houses; it does not need separate activation. In that person's frame, the event anchor maps to "
                f"native {_natural_join([f'H{house}' for house in sorted(anchor)])}, its transition maps to "
                f"{_natural_join([f'H{house}' for house in sorted(transition)])}, and its outcome maps to "
                f"{_natural_join([f'H{house}' for house in sorted(outcome)])}."
            )
        if subject_varga_spec:
            if _language_code(language) == "hi":
                candidate["activation_reasoning"] += (
                    f" संबंधित व्यक्ति की पहचान के लिए {subject_varga_spec[0]} "
                    f"{'पुष्टि देता है' if subject_varga_confirmation.get('confirmed') else 'स्वतंत्र पुष्टि नहीं देता'}।"
                )
            else:
                candidate["activation_reasoning"] += (
                    f" For subject identification, {subject_varga_spec[0]} "
                    f"{'adds confirmation' if subject_varga_confirmation.get('confirmed') else 'does not add independent confirmation'}."
                )
    candidate["activation_reasoning"] += _bhava_disambiguation_sentence(
        bhava_disambiguation, language,
    )
    if bhava_disambiguation["specificity"] != "channel_distinguished":
        candidate["claim_scope"] = "ranked_manifestation_channel"
    if background_permission_houses:
        source_text = _natural_join([
            f"{planet} {level.replace('dasha', ' dasha')}"
            for planet, level in sorted(background_permission_sources)
        ])
        if _language_code(language) == "hi":
            candidate["activation_reasoning"] += (
                f" {_hi_join([f'{_hi_planet(planet)} {_HI_LEVELS.get(level, level)}' for planet, level in sorted(background_permission_sources)])} "
                f"का सीधा गोचर {_hi_house_list(background_permission_houses)} को दीर्घकालीन पृष्ठभूमि-अनुमति देता है; "
                "घटना की अवधि अलग प्रत्यंतर/सूक्ष्म दशा या तेज गोचर संकेत से तय हुई है।"
            )
        else:
            candidate["activation_reasoning"] += (
                f" The direct transit of {source_text} through {_house_list(background_permission_houses)} "
                "provides persistent background permission; a separate PD/Sookshma or faster-transit "
                "channel supplies the event timing."
            )
    return candidate


def _attach_supported_alternatives(candidates: Sequence[Dict[str, Any]], language: str) -> None:
    """Name qualified peer readings instead of displaying a vague ambiguity warning."""
    for candidate in candidates:
        candidate["alternative_event_labels"] = []
        if str(candidate.get("claim_scope") or "") != "ranked_manifestation_channel":
            continue
        subject_key = str(candidate.get("subject_key") or "self")
        anchors = {
            int(house)
            for house in ((candidate.get("bhava_disambiguation") or {}).get("semantic_anchor_houses") or [])
        }
        labels: List[str] = []
        for peer in candidates:
            if peer is candidate or str(peer.get("subject_key") or "self") != subject_key:
                continue
            peer_anchors = {
                int(house)
                for house in ((peer.get("bhava_disambiguation") or {}).get("semantic_anchor_houses") or [])
            }
            if anchors and peer_anchors and not (anchors & peer_anchors):
                continue
            label = str(peer.get("event_family") or "").split(" · ", 1)[-1].strip()
            if label and label not in labels:
                labels.append(label)
            if len(labels) == 3:
                break
        candidate["alternative_event_labels"] = labels
        if not labels:
            continue
        if _language_code(language) == "hi":
            candidate["prediction"] += f" इन्हीं सक्रिय भावों से समर्थित दूसरे संकेत: {_hi_join(labels)}।"
        else:
            candidate["prediction"] += (
                f" Other supported readings from the same active houses: {_natural_join(labels)}."
            )


def _candidate_family_key(candidate: Mapping[str, Any]) -> str:
    if candidate.get("manifestation_kg"):
        return str(candidate.get("event_key") or "event")
    return str(candidate.get("source_event_key") or candidate.get("event_key") or "event")


def _annotate_event_windows(months: Mapping[str, Any]) -> None:
    """Merge adjacent monthly instances into auditable event windows.

    This does not suppress a month from its own screen. It tells yearly and
    monthly consumers that, for example, late November and early December are
    one continuous activation rather than two independent predictions.
    """
    grouped: Dict[Tuple[str, str], List[Tuple[date, date, str]]] = {}
    for month in months.values():
        for candidate in month.get("qualified_candidates") or []:
            key = (
                str(candidate.get("subject_key") or "self"),
                _candidate_family_key(candidate),
            )
            for window in candidate.get("timing_windows") or []:
                start = _parse_iso_date(window.get("start_date"))
                end = _parse_iso_date(window.get("end_date"))
                if start and end:
                    grouped.setdefault(key, []).append((start, end, str(candidate.get("candidate_id"))))

    annotations: Dict[str, List[Dict[str, Any]]] = {}
    for (subject, event_key), raw_intervals in grouped.items():
        merged: List[Dict[str, Any]] = []
        for start, end, candidate_id in sorted(raw_intervals):
            if merged and start <= merged[-1]["end"] + timedelta(days=1):
                merged[-1]["end"] = max(merged[-1]["end"], end)
                merged[-1]["candidate_ids"].add(candidate_id)
            else:
                merged.append({"start": start, "end": end, "candidate_ids": {candidate_id}})
        for index, window in enumerate(merged, start=1):
            window_id = "ETW3-" + hashlib.sha1(
                f"{subject}:{event_key}:{window['start']}:{window['end']}".encode("utf-8", "ignore")
            ).hexdigest()[:12]
            payload = {
                "window_id": window_id,
                "start_date": window["start"].isoformat(),
                "end_date": window["end"].isoformat(),
                "subject_key": subject,
                "event_key": event_key,
                "sequence": index,
            }
            for candidate_id in window["candidate_ids"]:
                annotations.setdefault(candidate_id, []).append(payload)

    for month in months.values():
        for field in (
            "qualified_candidates", "publishable_candidates", "background_candidates",
            "people_candidates", "people_background_candidates",
            "also_possible_candidates", "ongoing_background_candidates", "weak_signal_candidates",
            "annual_context_candidates",
            "people_also_possible_candidates", "people_ongoing_background_candidates", "people_weak_signal_candidates",
            "people_annual_context_candidates",
        ):
            for candidate in month.get(field) or []:
                windows = annotations.get(str(candidate.get("candidate_id"))) or []
                candidate["event_windows"] = [dict(window) for window in windows]
                if windows:
                    candidate["event_window"] = dict(windows[0])


def _apply_persistent_permission_peak_policy(months: Mapping[str, Any]) -> None:
    """Keep slow-transit permission visible without publishing it every month."""
    if v3_publication_mode() == "exhaustive":
        return
    grouped: Dict[Tuple[str, str], List[Tuple[int, Dict[str, Any]]]] = {}
    for month_id, month in months.items():
        for candidate in month.get("qualified_candidates") or []:
            if not candidate.get("background_permission_houses"):
                continue
            key = (
                str(candidate.get("subject_key") or "self"),
                _candidate_family_key(candidate),
            )
            grouped.setdefault(key, []).append((int(month_id), candidate))

    peak_ids: Set[str] = set()
    for rows in grouped.values():
        by_month = {month_id: candidate for month_id, candidate in rows}

        def strength(item: Tuple[int, Mapping[str, Any]]) -> Tuple[int, int, int]:
            month_id, candidate = item
            exact_count = len(((candidate.get("exact_transit_contacts") or {}).get("event_contacts") or []))
            return int(candidate.get("priority_score") or 0), exact_count, month_id

        peak_month, peak_candidate = max(rows, key=strength)
        selected = [(peak_month, peak_candidate)]
        neighbours = [
            (month_id, by_month[month_id])
            for month_id in (peak_month - 1, peak_month + 1)
            if month_id in by_month
        ]
        if neighbours:
            selected.append(max(neighbours, key=strength))
        for _month_id, candidate in selected:
            peak_ids.add(str(candidate.get("candidate_id")))

    for month in months.values():
        qualified = month.get("qualified_candidates") or []
        for candidate in qualified:
            if candidate.get("background_permission_houses"):
                candidate["persistent_permission_peak"] = str(candidate.get("candidate_id")) in peak_ids

        for visible_field, background_field in (
            ("publishable_candidates", "background_candidates"),
            ("people_candidates", "people_background_candidates"),
        ):
            visible = list(month.get(visible_field) or [])
            demoted = [
                candidate for candidate in visible
                if candidate.get("background_permission_houses")
                and str(candidate.get("candidate_id")) not in peak_ids
            ]
            if not demoted:
                continue
            demoted_ids = {str(candidate.get("candidate_id")) for candidate in demoted}
            month[visible_field] = [
                candidate for candidate in visible
                if str(candidate.get("candidate_id")) not in demoted_ids
            ]
            existing = list(month.get(background_field) or [])
            existing_ids = {str(candidate.get("candidate_id")) for candidate in existing}
            month[background_field] = sorted(
                existing + [candidate for candidate in demoted if str(candidate.get("candidate_id")) not in existing_ids],
                key=lambda candidate: (-int(candidate.get("priority_score") or 0), str(candidate.get("event_key") or "")),
            )

        # Reserve at most one primary slot for the strongest persistent-
        # permission peak. Otherwise a valid peak can remain hidden merely
        # because unrelated high-scoring domains filled the relative threshold.
        native_visible = list(month.get("publishable_candidates") or [])
        native_ids = {str(candidate.get("candidate_id")) for candidate in native_visible}
        native_peaks = [
            candidate for candidate in qualified
            if str(candidate.get("subject_key") or "self") == "self"
            and str(candidate.get("candidate_id")) in peak_ids
            and str(candidate.get("candidate_id")) not in native_ids
            and str(candidate.get("support_grade") or "C") in {"A", "B"}
        ]
        if native_peaks and len(native_visible) < 5:
            promoted = max(native_peaks, key=lambda candidate: int(candidate.get("priority_score") or 0))
            native_visible.append(dict(promoted))
            month["publishable_candidates"] = sorted(
                native_visible,
                key=lambda candidate: (-int(candidate.get("priority_score") or 0), str(candidate.get("event_key") or "")),
            )
            promoted_id = str(promoted.get("candidate_id"))
            month["background_candidates"] = [
                candidate for candidate in month.get("background_candidates") or []
                if str(candidate.get("candidate_id")) != promoted_id
            ]

        people_visible = list(month.get("people_candidates") or [])
        visible_subjects = {str(candidate.get("subject_key") or "relative") for candidate in people_visible}
        people_peaks = [
            candidate for candidate in qualified
            if str(candidate.get("subject_key") or "self") != "self"
            and str(candidate.get("candidate_id")) in peak_ids
            and str(candidate.get("support_grade") or "C") in {"A", "B"}
            and str(candidate.get("subject_key") or "relative") not in visible_subjects
        ]
        if people_peaks and len(people_visible) < 2:
            promoted = max(people_peaks, key=lambda candidate: int(candidate.get("priority_score") or 0))
            people_visible.append(dict(promoted))
            month["people_candidates"] = sorted(
                people_visible,
                key=lambda candidate: (-int(candidate.get("priority_score") or 0), str(candidate.get("event_key") or "")),
            )
            promoted_id = str(promoted.get("candidate_id"))
            month["people_background_candidates"] = [
                candidate for candidate in month.get("people_background_candidates") or []
                if str(candidate.get("candidate_id")) != promoted_id
            ]
        month["published_candidate_count"] = len(month.get("publishable_candidates") or [])
        if isinstance(month.get("selection_summary"), dict):
            month["selection_summary"]["published_count"] = len(month.get("publishable_candidates") or [])
            month["selection_summary"]["background_count"] = len(month.get("background_candidates") or [])
            month["selection_summary"]["persistent_permission_rule"] = (
                "A slow-transit permission may qualify throughout a long period, but only its strongest "
                "one- or two-month corridor remains a primary card."
            )
        if isinstance(month.get("people_selection_summary"), dict):
            month["people_selection_summary"]["visible_count"] = len(month.get("people_candidates") or [])
            month["people_selection_summary"]["overflow_count"] = len(month.get("people_background_candidates") or [])


def _contact_timing_strength(contact: Mapping[str, Any]) -> int:
    phase = str(contact.get("peak_phase") or "").lower()
    phase_score = {
        "exact": 8,
        "applying": 5,
        "separating": 4,
        "stationary_or_boundary": 2,
    }.get(phase, 1)
    try:
        orb = float(contact.get("peak_orb"))
    except (TypeError, ValueError):
        orb = 99.0
    orb_score = 6 if orb <= 0.25 else 4 if orb <= 0.75 else 2 if orb <= 1.5 else 0
    planet = str(contact.get("transit_planet") or "")
    speed_score = 3 if planet in {"Moon", "Mercury", "Venus", "Mars", "Sun"} else 1
    target_score = 2 if contact.get("target_type") in {"event_lord_or_karaka", "kp_anchor_cusp"} else 0
    return phase_score + orb_score + speed_score + target_score


def _distinctive_fast_contacts(candidate: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    rows = list(((candidate.get("exact_transit_contacts") or {}).get("event_contacts") or []))
    retained = []
    for row in rows:
        if row.get("transit_planet") not in {"Moon", "Mercury", "Venus", "Mars", "Sun"}:
            continue
        if str(row.get("peak_phase") or "").lower() not in {"exact", "applying", "separating"}:
            continue
        try:
            if float(row.get("peak_orb")) > 1.5:
                continue
        except (TypeError, ValueError):
            continue
        retained.append(row)
    return retained


def _monthly_timing_strength(candidate: Mapping[str, Any]) -> Tuple[int, Tuple[str, ...]]:
    """Score only evidence that can change the event's timing within the year."""
    contacts = _distinctive_fast_contacts(candidate)
    contact_scores = sorted((_contact_timing_strength(row) for row in contacts), reverse=True)
    # Several contacts can corroborate a peak, but a noisy high count must not
    # overwhelm one close, event-specific contact.
    contact_score = sum(contact_scores[:2]) + min(3, max(0, len(contact_scores) - 2))

    channels = list(candidate.get("independent_timing_channels") or [])
    fine_signatures = {
        f"{row.get('planet')}:{row.get('dasha_level')}"
        for row in channels
        if row.get("dasha_level") in {"pratyantardasha", "sookshma"}
    }
    fast_signatures = {
        f"{row.get('planet')}:{row.get('mechanism')}"
        for row in channels
        if str(row.get("mechanism") or "").startswith("transit_")
        and row.get("planet") in {"Moon", "Mercury", "Venus", "Mars", "Sun"}
    }
    fine_score = min(14, 5 * len(fine_signatures) + 2 * len(fast_signatures))

    total_days = 0
    for window in candidate.get("timing_windows") or []:
        start = _parse_iso_date(window.get("start_date"))
        end = _parse_iso_date(window.get("end_date"))
        if start and end and end >= start:
            total_days += (end - start).days + 1
    corridor_score = 8 if 0 < total_days <= 7 else 5 if total_days <= 14 else 2 if total_days <= 21 else 0
    phase_score = {"result_window": 3, "developing": 1}.get(str(candidate.get("manifestation_phase") or ""), 0)
    score = contact_score + fine_score + corridor_score + phase_score
    signature = tuple(sorted(fine_signatures | fast_signatures))
    return score, signature


def _apply_general_monthly_peak_policy(months: Mapping[str, Any]) -> None:
    """Turn year-long permission into a small number of genuinely timed peaks."""
    if v3_publication_mode() == "exhaustive" or accuracy_layer_mode() != "integrated_v2":
        return

    grouped: Dict[Tuple[str, str], List[Tuple[int, Dict[str, Any], Tuple[str, ...]]]] = {}
    for month_id, month in months.items():
        for candidate in month.get("qualified_candidates") or []:
            timing_score, signature = _monthly_timing_strength(candidate)
            contacts = _distinctive_fast_contacts(candidate)
            best_contact = max(
                contacts,
                key=lambda row: (
                    _contact_timing_strength(row),
                    -float(row.get("peak_orb") or 999.0),
                ),
                default=None,
            )
            candidate["annual_baseline_score"] = int(candidate.get("priority_score") or 0)
            candidate["monthly_timing_score"] = timing_score
            candidate["monthly_timing_signature"] = list(signature)
            candidate["peak_timing_contact"] = dict(best_contact) if best_contact else None
            candidate["distinctive_fast_contact_count"] = len(contacts)
            key = (
                str(candidate.get("subject_key") or "self"),
                _candidate_family_key(candidate),
            )
            grouped.setdefault(key, []).append((int(month_id), candidate, signature))

    primary_peak_ids: Set[str] = set()
    continuation_ids: Set[str] = set()
    for rows in grouped.values():
        scores = sorted(row[1]["monthly_timing_score"] for row in rows)
        median_score = scores[len(scores) // 2]
        for _month_id, candidate, _signature in rows:
            candidate["monthly_timing_lift"] = int(candidate["monthly_timing_score"] - median_score)

        eligible = [
            row for row in rows
            if str(row[1].get("support_grade") or "C") in {"A", "B"}
            and row[1].get("timing_windows")
            and int(row[1].get("distinctive_fast_contact_count") or 0) > 0
            and row[2]
        ]
        if not eligible:
            for _month_id, candidate, _signature in rows:
                candidate["monthly_peak_status"] = "untimed_annual_permission"
            continue

        ordered = sorted(
            eligible,
            key=lambda row: (
                -int(row[1].get("monthly_timing_score") or 0),
                -int(row[1].get("priority_score") or 0),
                row[0],
            ),
        )
        selected = [ordered[0]]
        first_month, first_candidate, first_signature = ordered[0]
        first_score = int(first_candidate.get("monthly_timing_score") or 0)
        for row in ordered[1:]:
            month_id, candidate, signature = row
            if (
                abs(month_id - first_month) > 1
                and int(candidate.get("monthly_timing_score") or 0) >= first_score - 2
                and signature != first_signature
            ):
                selected.append(row)
                break
        peak_months = {row[0] for row in selected}
        for month_id, candidate, _signature in rows:
            candidate_id = str(candidate.get("candidate_id"))
            if month_id in peak_months and any(str(row[1].get("candidate_id")) == candidate_id for row in selected):
                candidate["monthly_peak_status"] = "peak"
                peak_contact = candidate.get("peak_timing_contact") or {}
                if peak_contact.get("start_date") and peak_contact.get("end_date"):
                    candidate["start_date"] = peak_contact["start_date"]
                    candidate["end_date"] = peak_contact["end_date"]
                primary_peak_ids.add(candidate_id)
            elif any(abs(month_id - peak_month) == 1 for peak_month in peak_months):
                candidate["monthly_peak_status"] = "continuation"
                continuation_ids.add(candidate_id)
            else:
                candidate["monthly_peak_status"] = "active_outside_peak"
            if candidate.get("background_permission_houses"):
                candidate["persistent_permission_peak"] = candidate.get("monthly_peak_status") == "peak"

    for month in months.values():
        qualified = list(month.get("qualified_candidates") or [])
        native_peaks = [
            dict(row) for row in qualified
            if str(row.get("subject_key") or "self") == "self"
            and str(row.get("candidate_id")) in primary_peak_ids
        ]
        native_peaks.sort(key=lambda row: (
            -int(row.get("monthly_timing_score") or 0),
            -int(row.get("priority_score") or 0),
            str(row.get("event_key") or ""),
        ))
        selected: List[Dict[str, Any]] = []
        used_domains: Set[str] = set()
        for row in native_peaks:
            domain = str(row.get("life_domain") or row.get("event_key") or "")
            if domain in used_domains:
                continue
            selected.append(row)
            used_domains.add(domain)
            if len(selected) == 4:
                break
        selected_ids = {str(row.get("candidate_id")) for row in selected}
        month["publishable_candidates"] = selected
        month["background_candidates"] = [
            dict(row) for row in qualified
            if str(row.get("subject_key") or "self") == "self"
            and str(row.get("candidate_id")) not in selected_ids
        ]

        people_peaks = [
            dict(row) for row in qualified
            if str(row.get("subject_key") or "self") != "self"
            and str(row.get("candidate_id")) in primary_peak_ids
        ]
        people_peaks.sort(key=lambda row: (
            -int(row.get("monthly_timing_score") or 0),
            -int(row.get("priority_score") or 0),
        ))
        people_selected: List[Dict[str, Any]] = []
        used_subjects: Set[str] = set()
        for row in people_peaks:
            subject = str(row.get("subject_key") or "relative")
            if subject in used_subjects:
                continue
            people_selected.append(row)
            used_subjects.add(subject)
        people_ids = {str(row.get("candidate_id")) for row in people_selected}
        month["people_candidates"] = people_selected
        month["people_background_candidates"] = [
            dict(row) for row in qualified
            if str(row.get("subject_key") or "self") != "self"
            and str(row.get("candidate_id")) not in people_ids
        ]
        month["published_candidate_count"] = len(selected)
        if isinstance(month.get("selection_summary"), dict):
            month["selection_summary"].update({
                "published_count": len(selected),
                "background_count": len(month["background_candidates"]),
                "timing_policy": "annual_permission_plus_event_specific_monthly_peak_v1",
                "forced_minimum": 0,
            })
        if isinstance(month.get("people_selection_summary"), dict):
            month["people_selection_summary"].update({
                "visible_count": len(people_selected),
                "overflow_count": len(month["people_background_candidates"]),
            })


def build_v3_prediction_model(
    context: Mapping[str, Any],
    ledger: Mapping[str, Any],
    *,
    kp_evidence: Mapping[str, Any] | None,
    user_facts: Mapping[str, Any] | None,
    year: int,
    age: int,
    language: str = "english",
    relative_profiles: Sequence[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    dkp = derive_desh_kaal_patra(
        user_facts, age=age, target_year=year, relative_profiles=relative_profiles,
    )
    from manifestation_kg.timeline import build_timeline_definitions
    kg_timeline = build_timeline_definitions(dkp)
    relative_definitions = [
        build_relative_event_definition(
            definition, str(subject["key"]), str(subject["label"]), int(subject["reference_house"]),
        )
        for subject in dkp.get("eligible_relative_subjects") or []
        for definition in EVENT_DEFINITIONS.values()
        if not (str(subject["key"]) == "spouse" and definition.key in {"marriage", "children"})
    ]
    kg_definitions = () if accuracy_layer_mode() == "legacy_v3_6" else kg_timeline.definitions
    definitions = [*EVENT_DEFINITIONS.values(), *kg_definitions, *relative_definitions]
    months: Dict[str, Any] = {}
    for month in range(1, 13):
        month_ledger = ((ledger.get("months") or {}).get(str(month)) or {})
        graph = build_month_activation_graph(month_ledger)
        candidates = [
            candidate
            for definition in definitions
            if (candidate := _candidate_from_definition(
                definition=definition, graph=graph, month=month, year=year,
                kp=kp_evidence or {}, context=context, dkp=dkp, language=language,
            )) is not None
        ]
        candidates.sort(key=lambda row: (-int(row["priority_score"]), row["event_key"]))
        _attach_supported_alternatives(candidates, language)
        native_candidates = [row for row in candidates if str(row.get("subject_key") or "self") == "self"]
        relative_candidates = [row for row in candidates if str(row.get("subject_key") or "self") != "self"]
        people_evaluations = []
        for subject in dkp.get("eligible_relative_subjects") or []:
            subject_key = str(subject.get("key") or "")
            subject_rows = [
                row for row in relative_candidates
                if str(row.get("subject_key") or "") == subject_key
            ]
            people_evaluations.append({
                "subject_key": subject_key,
                "subject_label": subject.get("label") or subject_key.replace("_", " ").title(),
                "reference_house": subject.get("reference_house"),
                "evaluated": True,
                "qualified_event_count": len(subject_rows),
                "status": "qualified_events" if subject_rows else "no_qualified_event_this_month",
            })
        published, background, selection_summary = _select_publishable(native_candidates)
        people, people_overflow, people_selection_summary = _select_people_candidates(relative_candidates)
        months[str(month)] = {
            "month_id": month,
            "activation_graph": graph,
            "activated_house_count": len(graph.get("all_activated_houses") or []),
            "candidate_count": len(candidates),
            "qualified_candidate_count": len(candidates),
            "published_candidate_count": len(published),
            "qualified_candidates": candidates,
            "publishable_candidates": published,
            "background_candidates": background,
            "people_candidates": people,
            "people_background_candidates": people_overflow,
            "people_selection_summary": people_selection_summary,
            "people_evaluations": people_evaluations,
            "selection_summary": selection_summary,
            "prediction_state": "supported_candidates" if candidates else "insufficient_event_combination",
        }
    _annotate_event_windows(months)
    _apply_general_monthly_peak_policy(months)
    _annotate_display_tiers(months, language)
    return {
        "version": V3_EVIDENCE_VERSION,
        "explanation_version": v3_explanation_version(),
        "language": _language_code(language),
        "publication_mode": v3_publication_mode(),
        "accuracy_layer": accuracy_layer_mode(),
        "year": year,
        "node_doctrine": "Nodes have no direct house lordship; use occupation, dispositor/conjunction evidence when available, and seventh aspect only.",
        "house_systems": {"parashari": "whole_sign", "kp": "placidus_independent_confirmation"},
        "desh_kaal_patra": dkp,
        "manifestation_kg": dict(kg_timeline.audit),
        "user_fact_fingerprint": user_fact_fingerprint(user_facts, language, relative_profiles),
        "months": months,
    }


_USER_FACING_ASTROLOGY_TERMS = re.compile(
    r"\b(?:mahadasha|antardasha|pratyantardasha|sookshma|dasha|transit|natal|kp|varga|bhava|karaka|cusp|"
    r"ashtakavarga|kakshya|sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu|d\d{1,2})\b",
    re.I,
)
_CERTAINTY_TERMS = re.compile(
    r"\b(?:definitely|guaranteed|certainly|will certainly|must happen|is certain to)\b|"
    r"(?:निश्चित रूप से|गारंटी|अवश्य होगा|पक्का होगा)",
    re.I,
)
_CONDITIONAL_TERMS = re.compile(
    r"\b(?:may|might|could|possible|possibly|likely|chance|watch for|can)\b|"
    r"(?:हो सकता|हो सकती|हो सकते|संभावना|संभव|दिख सकती|दिख सकता)",
    re.I,
)
_DATE_LITERAL = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _safe_narration(candidate: Mapping[str, Any], supplied: Mapping[str, Any] | None) -> Tuple[Dict[str, Any], List[str]]:
    warnings: List[str] = []
    supplied = supplied or {}
    fallback = " ".join(str(candidate.get("prediction") or "").split())
    supplied_prediction = " ".join(str(supplied.get("prediction") or "").split())
    prediction = supplied_prediction or fallback
    narration_source = "llm" if supplied_prediction else "deterministic"
    lowered = prediction.lower()
    for term in candidate.get("forbidden_terms") or []:
        if term.lower() in lowered:
            prediction = fallback
            narration_source = "deterministic_fallback"
            warnings.append(f"Replaced narration violating Desh-Kaal-Patra gate for {candidate.get('candidate_id')}")
            break
    if _USER_FACING_ASTROLOGY_TERMS.search(prediction):
        prediction = fallback
        narration_source = "deterministic_fallback"
        warnings.append(
            f"Replaced technical user-facing narration for {candidate.get('candidate_id')}"
        )
    if supplied_prediction and (
        len(prediction.split()) > 32
        or _CERTAINTY_TERMS.search(prediction)
        or not _CONDITIONAL_TERMS.search(prediction)
        or _DATE_LITERAL.search(prediction)
    ):
        prediction = fallback
        narration_source = "deterministic_fallback"
        warnings.append(
            f"Replaced unsafe or over-specific narration for {candidate.get('candidate_id')}"
        )
    if candidate.get("explanation_version") == "detailed_v2":
        manifestations = candidate.get("possible_manifestations") or []
    else:
        manifestations = supplied.get("possible_manifestations")
        if not isinstance(manifestations, list) or not manifestations:
            manifestations = candidate.get("possible_manifestations") or []
    # Scenario cards only name real-life possibilities. Their calculation
    # details belong in the prediction-level Show Why, not in another nested
    # implementation explanation.
    public_manifestations = [
        {"scenario": str(row.get("scenario") or "").strip()}
        for row in manifestations[:2]
        if isinstance(row, Mapping) and str(row.get("scenario") or "").strip()
    ]
    event_label = str(candidate.get("event_family") or "").split(" · ", 1)[-1]
    normalize = lambda value: re.sub(r"[^a-z0-9]+", "", str(value).lower())
    if (
        len(public_manifestations) == 1
        and normalize(public_manifestations[0]["scenario"]) == normalize(event_label)
    ):
        public_manifestations = []
    return ({
        "candidate_id": candidate.get("candidate_id"),
        "event_key": candidate.get("event_key"),
        "life_domain": candidate.get("life_domain"),
        "subject_key": candidate.get("subject_key") or "self",
        "subject_label": candidate.get("subject_label"),
        "subject_reference_house": candidate.get("subject_reference_house"),
        "source_event_key": candidate.get("source_event_key") or candidate.get("event_key"),
        "type": candidate.get("event_family"),
        "prediction": prediction,
        "narration_source": narration_source,
        "possible_manifestations": public_manifestations,
        "activation_reasoning": candidate.get("activation_reasoning"),
        "trigger_logic": candidate.get("trigger_logic"),
        "evidence_ids": list(candidate.get("evidence_ids") or []),
        "start_date": candidate.get("start_date"),
        "end_date": candidate.get("end_date"),
        "intensity": candidate.get("intensity"),
        "support_grade": candidate.get("support_grade"),
        "support_label": candidate.get("support_label"),
        "display_tier": candidate.get("display_tier"),
        "display_tier_label": candidate.get("display_tier_label"),
        "display_reason": candidate.get("display_reason"),
        "display_explanation": candidate.get("display_explanation"),
        "support_score": candidate.get("support_score"),
        "priority_score": candidate.get("priority_score"),
        "annual_baseline_score": candidate.get("annual_baseline_score"),
        "monthly_timing_score": candidate.get("monthly_timing_score"),
        "monthly_timing_lift": candidate.get("monthly_timing_lift"),
        "monthly_peak_status": candidate.get("monthly_peak_status"),
        "peak_timing_contact": candidate.get("peak_timing_contact"),
        "priority_factors": list(candidate.get("priority_factors") or []),
        "manifestation_phase": candidate.get("manifestation_phase"),
        "claim_scope": candidate.get("claim_scope"),
        "alternative_event_labels": list(candidate.get("alternative_event_labels") or []),
        "timing_windows": list(candidate.get("timing_windows") or []),
        "event_window": candidate.get("event_window"),
        "event_windows": list(candidate.get("event_windows") or []),
        "background_permission_houses": list(candidate.get("background_permission_houses") or []),
        "background_permission_sources": list(candidate.get("background_permission_sources") or []),
        "independent_timing_channels": list(candidate.get("independent_timing_channels") or []),
        "exact_transit_contacts": candidate.get("exact_transit_contacts"),
        "ashtakavarga_confirmation": candidate.get("ashtakavarga_confirmation"),
        "supporting_systems": candidate.get("supporting_systems"),
        "birth_time_reliability": candidate.get("birth_time_reliability"),
        "timing_resolution": candidate.get("timing_resolution"),
        "outcome_dimensions": candidate.get("outcome_dimensions"),
        "natal_promise": candidate.get("natal_promise"),
        "planet_delivery": candidate.get("planet_delivery"),
        "obstruction_profile": candidate.get("obstruction_profile"),
        "accuracy_layer": candidate.get("accuracy_layer"),
        "accuracy_limitations": list(candidate.get("accuracy_limitations") or []),
        "activated_houses": sorted(set(
            (candidate.get("anchor_hits") or [])
            + (candidate.get("transition_hits") or [])
            + (candidate.get("outcome_hits") or [])
            + (candidate.get("transit_hits") or [])
        )),
        "kp_confirmation": candidate.get("kp_confirmation"),
        "varga_confirmation": candidate.get("varga_confirmation"),
        "subject_varga_confirmation": candidate.get("subject_varga_confirmation"),
        "bhava_disambiguation": candidate.get("bhava_disambiguation"),
        "desh_kaal_patra": candidate.get("desh_kaal_patra"),
        "explanation_version": candidate.get("explanation_version"),
        "manifestation_kg": candidate.get("manifestation_kg"),
    }, warnings)


_MONTH_NAMES = (
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_HI_MONTH_NAMES = (
    "", "जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
    "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर",
)


def _peak_timing_clause(month_scores: Mapping[int, int], language: str = "en") -> str:
    peak_score = max(month_scores.values())
    near_peak = sorted(month for month, score in month_scores.items() if score >= peak_score - 2)
    if len(near_peak) >= 4:
        return (
            "जिसकी शक्ति किसी एक शिखर के बजाय कई अवधियों में फैली है"
            if language == "hi" else "with strength spread across multiple periods rather than one isolated peak"
        )
    peak_months = [
        month for month, _score in sorted(month_scores.items(), key=lambda item: (-item[1], item[0]))[:2]
    ]
    peak_months.sort()
    if language == "hi":
        return f"जिसकी सबसे मजबूत अवधि {_hi_join([_HI_MONTH_NAMES[month] for month in peak_months])} के आसपास है"
    return f"with the strongest concentration around {_natural_join([_MONTH_NAMES[month] for month in peak_months])}"


def _annual_domain_text(domain: str, dkp: Mapping[str, Any]) -> str:
    employment = str(dkp.get("employment_state") or "unknown")
    relationship = str(dkp.get("relationship_state") or "unknown")
    if domain == "work":
        return {
            "homemaker": "Household, community, and independent responsibilities",
            "student": "Study-to-work choices, recognition, and responsibility",
            "unemployed": "Employment openings, applications, and changing responsibilities",
            "retired": "Advisory, service, community, and family responsibilities",
            "self_employed": "Business operations, visibility, and responsibility",
            "employed": "Work changes, visibility, and professional responsibility",
        }.get(employment, "Work, public standing, and changing responsibilities")
    if domain == "relationships":
        return (
            "The existing partnership and shared family decisions"
            if relationship == "married"
            else "Relationship, commitment, and partnership decisions"
        )
    return {
        "home": "Home, property, and relocation decisions",
        "family": "Children, mentoring, creativity, and family responsibilities",
        "travel": "Long-distance travel, paperwork, study, and time away from home",
        "education": "Learning, examinations, training, and qualifications",
        "resources": "Income, savings, receivables, and shared resources",
        "health": "Health routines, workload, recovery, and practical problem-solving",
    }.get(domain, "A recurring life-area transition")


def _hindi_annual_domain_text(domain: str, dkp: Mapping[str, Any]) -> str:
    employment = str(dkp.get("employment_state") or "unknown")
    relationship = str(dkp.get("relationship_state") or "unknown")
    if domain == "work":
        return {
            "homemaker": "घर, समुदाय और स्वतंत्र जिम्मेदारियाँ",
            "student": "पढ़ाई से काम की ओर चुनाव, पहचान और जिम्मेदारी",
            "unemployed": "रोज़गार के अवसर, आवेदन और बदलती जिम्मेदारियाँ",
            "retired": "सलाहकारी, सेवा, समुदाय और परिवार की जिम्मेदारियाँ",
            "self_employed": "व्यवसाय संचालन, दृश्यता और जिम्मेदारी",
            "employed": "काम में बदलाव, दृश्यता और पेशेवर जिम्मेदारी",
        }.get(employment, "काम, सार्वजनिक स्थिति और बदलती जिम्मेदारियाँ")
    if domain == "relationships":
        return "मौजूदा साझेदारी और साझा पारिवारिक निर्णय" if relationship == "married" else "रिश्ता, प्रतिबद्धता और साझेदारी के निर्णय"
    return {
        "home": "घर, संपत्ति और स्थान परिवर्तन के निर्णय",
        "family": "संतान, मार्गदर्शन, रचनात्मकता और पारिवारिक जिम्मेदारियाँ",
        "travel": "लंबी यात्रा, दस्तावेज़, पढ़ाई और घर से दूर रहने के विषय",
        "education": "पढ़ाई, परीक्षा, प्रशिक्षण और योग्यता",
        "resources": "आय, बचत, मिलने वाला धन और साझा संसाधन",
        "health": "स्वास्थ्य दिनचर्या, काम का बोझ, स्वास्थ्य-लाभ और व्यावहारिक समाधान",
    }.get(domain, "जीवन के किसी क्षेत्र में बार-बार आने वाला बदलाव")


def _build_annual_trends(prediction_model: Mapping[str, Any], month_ids: Sequence[int]) -> List[str]:
    """Summarize recurrence and peak timing across the whole requested period."""
    # One score per domain per month prevents two closely related work/home cards
    # from overpowering every other annual theme merely through duplication.
    domains: Dict[str, Dict[str, Any]] = {}
    months = prediction_model.get("months") or {}
    for month_id in month_ids:
        month = months.get(str(month_id)) or {}
        month_best: Dict[str, Mapping[str, Any]] = {}
        for candidate in month.get("publishable_candidates") or []:
            domain = str(candidate.get("life_domain") or candidate.get("event_key") or "other")
            previous = month_best.get(domain)
            if previous is None or int(candidate.get("priority_score") or 0) > int(previous.get("priority_score") or 0):
                month_best[domain] = candidate
        for domain, candidate in month_best.items():
            bucket = domains.setdefault(domain, {
                "month_scores": {}, "result_months": 0, "confirmed_months": 0,
                "obstructed_months": 0, "broad_months": 0,
            })
            score = int(candidate.get("priority_score") or 0)
            bucket["month_scores"][month_id] = score
            if candidate.get("manifestation_phase") == "result_window":
                bucket["result_months"] += 1
            if candidate.get("manifestation_phase") == "obstructed":
                bucket["obstructed_months"] += 1
            if candidate.get("claim_scope") == "broad_theme_only":
                bucket["broad_months"] += 1
            kp = candidate.get("kp_confirmation") or {}
            varga = candidate.get("varga_confirmation") or {}
            if kp.get("verdict") == "supported" or varga.get("confirmed"):
                bucket["confirmed_months"] += 1

    ranked = sorted(
        domains.items(),
        key=lambda item: (
            -sum(item[1]["month_scores"].values()),
            -len(item[1]["month_scores"]),
            item[0],
        ),
    )[:3]
    dkp = prediction_model.get("desh_kaal_patra") or {}
    language = _language_code(prediction_model.get("language"))
    trends: List[str] = []
    for domain, data in ranked:
        month_scores = data["month_scores"]
        count = len(month_scores)
        if language == "hi":
            recurrence = "वर्ष के बड़े हिस्से में बार-बार सक्रिय रहती हैं" if count >= 7 else "कई अलग अवधियों में लौटती हैं" if count >= 3 else "एक केंद्रित अवधि बनाती हैं"
            peak_timing = _peak_timing_clause(month_scores, "hi")
            phase = (
                " इनमें से कई अवधियों में परिणाम भाव भी सक्रिय हैं।"
                if int(data["result_months"]) >= max(2, count // 2)
                else " अधिकतर सक्रिय अवधियों में यह संकेत अंतिम परिणाम से अधिक विकास की प्रक्रिया दिखाता है।"
            )
            confirmation = " मजबूत अवधियों में KP या विभागीय कुंडली का स्वतंत्र समर्थन भी मिलता है।" if data["confirmed_months"] else ""
            qualification = (
                " कई अवधियों में बाधा अधिक है, इसलिए सक्रियता को अनुकूल पूर्ण परिणाम न मानें।"
                if int(data["obstructed_months"]) >= max(1, count // 2)
                else " जन्म कुंडली का समर्थन अधिकतर व्यापक विषय तक सीमित है।"
                if int(data["broad_months"]) >= max(1, count // 2)
                else ""
            )
            trends.append(f"{_hindi_annual_domain_text(domain, dkp)} {recurrence}, {peak_timing}।{phase}{confirmation}{qualification}")
        else:
            recurrence = "remain a recurring thread through much of the year" if count >= 7 else "return in several distinct periods" if count >= 3 else "form a concentrated window"
            peak_timing = _peak_timing_clause(month_scores)
            phase = (
                " Several of these periods also activate outcome houses."
                if int(data["result_months"]) >= max(2, count // 2)
                else " The pattern is more developmental than final in most of its active periods."
            )
            confirmation = " Independent KP or divisional-chart support is present in the stronger windows." if data["confirmed_months"] else ""
            qualification = (
                " Obstruction dominates several periods, so activation should not be read as a favourable completed outcome."
                if int(data["obstructed_months"]) >= max(1, count // 2)
                else " Natal support mostly limits this to a broad theme rather than a concrete-event forecast."
                if int(data["broad_months"]) >= max(1, count // 2)
                else ""
            )
            trends.append(f"{_annual_domain_text(domain, dkp)} {recurrence}, {peak_timing}.{phase}{confirmation}{qualification}")
    return trends


def validate_v3_payload(
    payload: Mapping[str, Any] | None,
    prediction_model: Mapping[str, Any],
    *,
    selected_month: Optional[int] = None,
    narration_expected: bool = True,
    expected_narration_ids: Mapping[int, Set[str]] | None = None,
    expected_narration_fact_ids: Mapping[int, Mapping[str, Set[str]]] | None = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Make deterministic candidates sovereign over LLM selection and timing."""
    payload = payload if isinstance(payload, Mapping) else {}
    supplied_by_month: Dict[int, Dict[str, Mapping[str, Any]]] = {}
    for month_row in payload.get("monthly_predictions") or []:
        if not isinstance(month_row, Mapping):
            continue
        try:
            month_id = int(month_row.get("month_id"))
        except (TypeError, ValueError):
            continue
        supplied_rows = list(month_row.get("events") or []) + list(month_row.get("narrations") or [])
        supplied_by_month[month_id] = {
            str(row.get("candidate_id")): row
            for row in supplied_rows
            if isinstance(row, Mapping) and row.get("candidate_id")
        }

    warnings: List[str] = []
    rows: List[Dict[str, Any]] = []
    month_ids = [selected_month] if selected_month else list(range(1, 13))
    for month_id in month_ids:
        model_month = ((prediction_model.get("months") or {}).get(str(month_id)) or {})
        warned_missing: Set[str] = set()

        def render(candidate: Mapping[str, Any]) -> Dict[str, Any]:
            candidate_id = str(candidate.get("candidate_id") or "")
            supplied = supplied_by_month.get(month_id, {}).get(candidate_id)
            allowed_fact_ids = (
                (expected_narration_fact_ids.get(month_id) or {}).get(candidate_id) or set()
                if expected_narration_fact_ids is not None
                else set()
            )
            if supplied is not None and allowed_fact_ids:
                cited_fact_ids = {
                    str(value) for value in supplied.get("used_fact_ids") or [] if str(value)
                }
                if not cited_fact_ids or not cited_fact_ids.issubset(allowed_fact_ids):
                    warnings.append(
                        f"Replaced narration with missing or invalid fact citations for {candidate_id}"
                    )
                    supplied = None
            should_be_narrated = narration_expected and (
                expected_narration_ids is None
                or candidate_id in (expected_narration_ids.get(month_id) or set())
            )
            if supplied is None and should_be_narrated and candidate_id not in warned_missing:
                warnings.append(f"Restored deterministic candidate omitted by narration: {candidate_id}")
                warned_missing.add(candidate_id)
            event, event_warnings = _safe_narration(candidate, supplied)
            if should_be_narrated and supplied is None:
                event["narration_source"] = "deterministic_fallback"
            warnings.extend(event_warnings)
            return event

        events: List[Dict[str, Any]] = []
        for candidate in model_month.get("publishable_candidates") or []:
            events.append(render(candidate))
        rows.append({
            "month_id": month_id,
            "focus_areas": [row["type"] for row in events[:5]],
            "events": events,
            "prediction_state": model_month.get("prediction_state") or "insufficient_event_combination",
            "selection_summary": model_month.get("selection_summary") or {},
            # Compatibility union retained for older clients and frozen forecasts.
            "background_candidates": [
                render(candidate)
                for candidate in model_month.get("background_candidates") or []
            ],
            "also_possible_candidates": [
                render(candidate)
                for candidate in model_month.get("also_possible_candidates") or []
            ],
            "ongoing_background_candidates": [
                render(candidate)
                for candidate in model_month.get("ongoing_background_candidates") or []
            ],
            "weak_signal_candidates": [
                render(candidate)
                for candidate in model_month.get("weak_signal_candidates") or []
            ],
            "annual_context_candidates": [
                render(candidate)
                for candidate in model_month.get("annual_context_candidates") or []
            ],
            "people_candidates": [
                render(candidate)
                for candidate in model_month.get("people_candidates") or []
            ],
            "people_background_candidates": [
                render(candidate)
                for candidate in model_month.get("people_background_candidates") or []
            ],
            "people_also_possible_candidates": [
                render(candidate)
                for candidate in model_month.get("people_also_possible_candidates") or []
            ],
            "people_ongoing_background_candidates": [
                render(candidate)
                for candidate in model_month.get("people_ongoing_background_candidates") or []
            ],
            "people_weak_signal_candidates": [
                render(candidate)
                for candidate in model_month.get("people_weak_signal_candidates") or []
            ],
            "people_annual_context_candidates": [
                render(candidate)
                for candidate in model_month.get("people_annual_context_candidates") or []
            ],
            "people_selection_summary": model_month.get("people_selection_summary") or {},
            "people_evaluations": model_month.get("people_evaluations") or [],
            "activation_summary": {
                "all_activated_houses": (model_month.get("activation_graph") or {}).get("all_activated_houses") or [],
                "dasha_open_houses": (model_month.get("activation_graph") or {}).get("dasha_open_houses") or [],
                "transit_triggered_houses": (model_month.get("activation_graph") or {}).get("transit_triggered_houses") or [],
            },
        })

    deterministic_trends = _build_annual_trends(prediction_model, month_ids)
    out = {
        "macro_trends": deterministic_trends,
        "monthly_predictions": rows,
        "accuracy_layer": prediction_model.get("accuracy_layer"),
        "explanation_version": prediction_model.get("explanation_version"),
        "publication_mode": prediction_model.get("publication_mode"),
        "language": prediction_model.get("language") or "en",
        "validation_warnings": warnings,
        "narration_status": (
            "deterministic"
            if not narration_expected
            else "complete" if not warnings else "partial_fallback"
        ),
        "desh_kaal_patra": prediction_model.get("desh_kaal_patra") or {},
        "manifestation_kg": prediction_model.get("manifestation_kg") or {},
        "user_fact_fingerprint": prediction_model.get("user_fact_fingerprint"),
    }
    return out, warnings
