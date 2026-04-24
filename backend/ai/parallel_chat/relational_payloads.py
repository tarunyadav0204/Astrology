"""Relational/two-person payloads for the opt-in parallel chat pipeline."""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Optional

from marriage_analysis.guna_milan import GunaMilanCalculator

from ai.parallel_chat.context_slices import (
    _build_sudarshana_reasoning_spine,
    build_ashtakavarga_slice,
    build_jaimini_slice,
    build_kp_slice,
    build_nadi_slice,
    build_nakshatra_slice,
    build_parashari_slice,
    build_shared_kernel_lite,
    build_sudarshan_shared_kernel_lite,
    build_sudarshan_slice,
)


_RELATION_RULES: List[Dict[str, Any]] = [
    {
        "family": "spouse_romantic",
        "keywords": ["husband", "wife", "spouse", "boyfriend", "girlfriend", "lover", "marriage", "romantic", "fiance", "fiancee", "engagement"],
        "houses": [7, 2, 5, 8, 12],
        "karakas": ["Venus", "Jupiter", "Mars", "Darakaraka"],
        "divisionals": ["D9"],
    },
    {
        "family": "parent_child",
        "keywords": ["parent", "child", "son", "daughter", "mother", "father"],
        "houses": [4, 5, 9, 2],
        "karakas": ["Moon", "Sun", "Jupiter"],
        "divisionals": ["D7", "D12"],
    },
    {
        "family": "siblings",
        "keywords": ["sibling", "brother", "sister", "elder", "younger"],
        "houses": [3, 11],
        "karakas": ["Mars", "Mercury"],
        "divisionals": ["D3"],
    },
    {
        "family": "guru_disciple",
        "keywords": ["guru", "disciple", "teacher", "student", "mentor"],
        "houses": [5, 9],
        "karakas": ["Jupiter", "Sun", "Mercury"],
        "divisionals": ["D20", "D24", "D9"],
    },
    {
        "family": "business_work",
        "keywords": ["business", "business partner", "manager", "boss", "employee", "colleague", "work", "company", "founder", "investor"],
        "houses": [7, 10, 11, 6, 2],
        "karakas": ["Mercury", "Saturn", "Sun", "Venus"],
        "divisionals": ["D10"],
    },
    {
        "family": "friends_social",
        "keywords": ["friend", "cousin", "close friend"],
        "houses": [11, 3, 5],
        "karakas": ["Mercury", "Venus", "Moon"],
        "divisionals": ["D9"],
    },
]

_EVENT_RULES: List[Dict[str, Any]] = [
    {
        "topic": "legal_confinement",
        "keywords": ["jail", "prison", "arrest", "court", "case", "legal", "police", "custody"],
        "houses": [6, 8, 12],
        "karakas": ["Saturn", "Rahu", "Ketu", "Mars"],
        "mode": "predictive_yes_no",
        "safety": "legal_or_crime_accusation",
    },
    {
        "topic": "reconciliation_return",
        "keywords": ["come back", "return", "reconcile", "reconciliation", "patch up", "reunite", "talk again", "friends again"],
        "houses": [2, 4, 7, 11],
        "karakas": ["Venus", "Moon", "Jupiter", "Mercury"],
        "mode": "predictive_timing",
        "safety": "emotional_uncertainty",
    },
    {
        "topic": "trust_infidelity",
        "keywords": [
            "cheat",
            "affair",
            "betray",
            "betrayed",
            "betrayal",
            "betryade",
            "unfaithful",
            "extramarital",
            "lover",
            "third person",
            "secret",
        ],
        "houses": [5, 7, 8, 12],
        "karakas": ["Venus", "Mars", "Rahu", "Moon"],
        "mode": "truth_suspicion",
        "safety": "factual_accusation",
    },
    {
        "topic": "separation_break",
        "keywords": ["leave", "separate", "divorce", "breakup", "break up", "distance", "split", "end relationship"],
        "houses": [6, 7, 8, 12],
        "karakas": ["Venus", "Saturn", "Rahu", "Ketu"],
        "mode": "predictive_timing",
        "safety": "emotional_uncertainty",
    },
    {
        "topic": "business_betrayal",
        "keywords": ["business betrayal", "business partner betray", "partner cheated", "fraud", "stole", "steal company", "company money", "sabotage", "scam", "embezzle", "deceived in business"],
        "houses": [2, 6, 7, 8, 10, 11, 12],
        "karakas": ["Mercury", "Saturn", "Rahu", "Mars"],
        "mode": "truth_suspicion",
        "safety": "factual_accusation",
    },
    {
        "topic": "guru_trust_breach",
        "keywords": ["fake guru", "guru cheated", "guru trust", "teacher betrayed", "mentor betrayed", "spiritual fraud"],
        "houses": [5, 8, 9, 12],
        "karakas": ["Jupiter", "Ketu", "Rahu", "Sun"],
        "mode": "quality_guidance",
        "safety": "factual_accusation",
    },
    {
        "topic": "parent_child_estrangement",
        "keywords": ["estranged", "not talking", "distant from me", "so distant", "child hates", "parent hates", "mother conflict", "father conflict"],
        "houses": [2, 4, 5, 8, 9, 12],
        "karakas": ["Moon", "Sun", "Jupiter", "Saturn"],
        "mode": "quality_guidance",
        "safety": "family_conflict",
    },
    {
        "topic": "sibling_conflict",
        "keywords": ["sibling conflict", "brother fight", "sister fight", "brother dispute", "sister dispute"],
        "houses": [3, 6, 8, 11],
        "karakas": ["Mars", "Mercury", "Saturn"],
        "mode": "quality_guidance",
        "safety": "family_conflict",
    },
    {
        "topic": "in_law_friction",
        "keywords": ["in law", "in-law", "in-laws", "mother in law", "father in law", "saas", "sasur"],
        "houses": [4, 7, 8, 9, 10, 12],
        "karakas": ["Moon", "Saturn", "Mars", "Rahu"],
        "mode": "quality_guidance",
        "safety": "family_conflict",
    },
    {
        "topic": "abuse_safety",
        "keywords": ["abuse", "violent", "violence", "hit me", "threaten", "unsafe", "danger"],
        "houses": [1, 4, 6, 8, 12],
        "karakas": ["Mars", "Saturn", "Rahu", "Moon"],
        "mode": "safety_guidance",
        "safety": "abuse_or_immediate_safety",
    },
    {
        "topic": "money_dispute",
        "keywords": ["money", "repay", "loan", "debt", "property", "settlement", "inheritance"],
        "houses": [2, 6, 8, 11],
        "karakas": ["Jupiter", "Mercury", "Saturn", "Venus"],
        "mode": "predictive_yes_no",
        "safety": "financial_dispute",
    },
    {
        "topic": "support_guidance",
        "keywords": ["support", "guide", "good for me", "trust", "help", "blessing", "learn"],
        "houses": [4, 5, 9, 11],
        "karakas": ["Jupiter", "Moon", "Sun", "Mercury"],
        "mode": "quality_guidance",
        "safety": "general",
    },
]

_SIGN_NAMES = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

_SIGN_LORDS = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Mars",
    8: "Jupiter",
    9: "Saturn",
    10: "Saturn",
    11: "Jupiter",
}

_SIGN_FLAVOR = {
    "Aries": "direct, impulsive, confrontational, fast-reacting",
    "Taurus": "steady, loyal, comfort-seeking, resistant to change",
    "Gemini": "verbal, curious, dual, mentally restless",
    "Cancer": "protective, emotional, home-attached, sensitive",
    "Leo": "proud, expressive, authoritative, recognition-seeking",
    "Virgo": "critical, analytical, improvement-focused, exacting",
    "Libra": "balancing, diplomatic, relationship-oriented, fairness-seeking",
    "Scorpio": "intense, guarded, suspicious, emotionally extreme",
    "Sagittarius": "idealistic, blunt, principled, freedom-seeking",
    "Capricorn": "dutiful, controlled, serious, endurance-oriented",
    "Aquarius": "detached, unconventional, intellectual, space-seeking",
    "Pisces": "sacrificial, emotional, idealistic, porous",
}

_HOUSE_THEME = {
    2: "family, speech, food, values",
    4: "home, emotional security, domestic peace",
    5: "romance, affection, expression, children",
    7: "spouse, marriage, mutual conduct",
    8: "intimacy, trust, vulnerability, shared pain",
    12: "withdrawal, bed life, privacy, distance, escape",
}

_NAKSHATRA_FLAVOR = {
    "Ashwini": "swift, initiating, impatient, action-first",
    "Bharani": "intense, burden-bearing, forceful, passionate",
    "Krittika": "sharp, cutting, purifying, demanding",
    "Rohini": "sensual, fertile, possessive, comfort-loving",
    "Mrigashira": "searching, curious, uncertain, exploratory",
    "Ardra": "stormy, raw, disruptive, emotionally intense",
    "Punarvasu": "restoring, hopeful, forgiving, resetting",
    "Pushya": "nurturing, dutiful, protective, sustaining",
    "Ashlesha": "coiled, psychological, suspicious, binding",
    "Magha": "ancestral, proud, status-aware, dominating",
    "Purva Phalguni": "pleasure-seeking, affectionate, dramatic, indulgent",
    "Uttara Phalguni": "duty-bound, sustaining, agreement-oriented, responsible",
    "Hasta": "skillful, controlling, precise, detail-focused",
    "Chitra": "crafted, image-conscious, exacting, intense",
    "Swati": "independent, airy, flexible, peace-seeking",
    "Vishakha": "goal-driven, dual-track, ambitious, consuming",
    "Anuradha": "loyal, relational, disciplined, emotionally controlled",
    "Jyeshtha": "protective, senior, touchy, high-pressure",
    "Mula": "root-cutting, extreme, probing, destructive-then-renewing",
    "Purva Ashadha": "idealistic, persuasive, emotionally forceful, proud",
    "Uttara Ashadha": "firm, principled, enduring, status-conscious",
    "Shravana": "observant, listening, socially aware, responsive",
    "Dhanishta": "rhythmic, achievement-oriented, socially performative",
    "Shatabhisha": "detached, sealed-off, reformist, difficult to reach",
    "Purva Bhadrapada": "severe, intense, ideological, extreme",
    "Uttara Bhadrapada": "deep, enduring, serious, internally heavy",
    "Revati": "gentle, guiding, soft, protective",
}

_NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

_CORE_CROSS_CONTACTS = [
    ("Moon", "Moon", "emotional resonance"),
    ("Venus", "Mars", "romantic/creative chemistry"),
    ("Mars", "Venus", "attraction and friction"),
    ("Saturn", "Moon", "pressure, duty, emotional heaviness"),
    ("Rahu", "Venus", "obsession, irregular attraction, boundary testing"),
    ("Ketu", "Venus", "detachment or karmic distance"),
    ("Jupiter", "Moon", "guidance, protection, emotional support"),
    ("Jupiter", "Sun", "respect, dharma, mentor principle"),
]


def _text_blob(context: Dict[str, Any], user_question: str) -> str:
    relation = context.get("relationship") or {}
    return " ".join(
        str(x or "").lower()
        for x in [
            user_question,
            relation.get("raw_label"),
            relation.get("relation_family"),
        ]
    )


def _first_rule_match(rules: List[Dict[str, Any]], text: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    best_rule: Optional[Dict[str, Any]] = None
    best_score = 0
    for rule in rules:
        score = sum(max(1, len(k.split())) for k in rule["keywords"] if k in text)
        if score > best_score:
            best_rule = rule
            best_score = score
    if best_rule is not None:
        return best_rule
    return fallback


def build_relationship_profile(context: Dict[str, Any], user_question: str) -> Dict[str, Any]:
    text = _text_blob(context, user_question)
    relation_rule = _first_rule_match(
        _RELATION_RULES,
        text,
        {
            "family": "general_two_person",
            "houses": [1, 7, 3, 11],
            "karakas": ["Moon", "Mercury", "Jupiter", "Venus"],
            "divisionals": ["D9"],
        },
    )
    event_rule = _first_rule_match(
        _EVENT_RULES,
        text,
        {
            "topic": "general_relationship",
            "houses": [],
            "karakas": [],
            "mode": "general_answer",
        },
    )
    event_rule = _refine_event_rule(relation_rule, event_rule, text)

    relation = context.get("relationship") or {}
    raw_label = relation.get("raw_label") or _extract_relationship_prefix(user_question)
    houses = list(dict.fromkeys([*relation_rule.get("houses", []), *event_rule.get("houses", [])]))
    karakas = list(dict.fromkeys([*relation_rule.get("karakas", []), *event_rule.get("karakas", [])]))

    role_house = _infer_role_house(relation_rule["family"], raw_label, user_question)

    return {
        "raw_label": raw_label,
        "relation_family": relation_rule["family"],
        "event_topic": event_rule["topic"],
        "question_mode": event_rule["mode"],
        "native_role_house": role_house,
        "derived_event_houses_from_role": _derive_houses_from_role(role_house, event_rule.get("houses", [])),
        "partner_event_houses": event_rule.get("houses", []),
        "primary_houses": houses,
        "primary_karakas": karakas,
        "required_divisionals": relation_rule.get("divisionals", []),
        "answer_policy": {
            "shape_answer_from_question": True,
            "do_not_force_compatibility_sections": True,
            "include_method_evidence_without_school_dump": True,
            "state_limits_for_fact_claims": event_rule.get("safety") in {
                "abuse_or_immediate_safety",
                "factual_accusation",
                "legal_or_crime_accusation",
            },
            "safety_class": event_rule.get("safety") or "general",
        },
    }


def _refine_event_rule(relation_rule: Dict[str, Any], event_rule: Dict[str, Any], text: str) -> Dict[str, Any]:
    relation_family = relation_rule.get("family")
    event_topic = event_rule.get("topic")
    if relation_family == "business_work" and event_topic == "trust_infidelity":
        return next(rule for rule in _EVENT_RULES if rule["topic"] == "business_betrayal")
    if relation_family == "guru_disciple" and event_topic == "trust_infidelity":
        return next(rule for rule in _EVENT_RULES if rule["topic"] == "guru_trust_breach")
    if relation_family == "parent_child" and event_topic == "separation_break":
        return next(rule for rule in _EVENT_RULES if rule["topic"] == "parent_child_estrangement")
    if relation_family == "siblings" and event_topic in {"separation_break", "parent_child_estrangement"}:
        return next(rule for rule in _EVENT_RULES if rule["topic"] == "sibling_conflict")
    if "in-law" in text or "in law" in text or "in-laws" in text:
        return next(rule for rule in _EVENT_RULES if rule["topic"] == "in_law_friction")
    return event_rule


def build_relational_evidence_spine(context: Dict[str, Any], user_question: str) -> Dict[str, Any]:
    profile = build_relationship_profile(context, user_question)
    native = context.get("native") or {}
    partner = context.get("partner") or {}
    role_house = profile.get("native_role_house")
    derived_event_houses = profile.get("derived_event_houses_from_role") or {}
    partner_event_houses = profile.get("partner_event_houses") or []

    native_role = _house_snapshot(native, role_house) if isinstance(role_house, int) else {}
    native_derived = [
        {"label": label, **_house_snapshot(native, house)}
        for label, house in derived_event_houses.items()
        if isinstance(house, int)
    ]
    partner_events = [
        {"label": f"partner_{h}", **_house_snapshot(partner, h)}
        for h in partner_event_houses
        if isinstance(h, int)
    ]
    contacts = _cross_chart_contacts(native, partner)
    overlays = _mutual_overlays(native, partner, profile)
    d1_d9_confirmation = _d1_d9_confirmation_block(native, partner, profile)
    vargottama = _relationship_vargottama_block(native, partner, profile)
    kuta = _kuta_compatibility(native, partner, profile)
    kp_map = _kp_relational_cusp_map(native, partner, profile)
    relation_specific = _relation_specific_evidence(native, partner, profile)
    relational_av = _relational_ashtakavarga_evidence(native, partner, profile)
    relational_sx = _relational_sudarshana_evidence(native, partner, profile)

    native_timing = _timing_alignment(native, profile)
    partner_timing = _timing_alignment(partner, profile)
    branch_activation = _branch_activation(profile, contacts, overlays, kuta, kp_map, native, partner)

    return {
        "profile": profile,
        "native_role_house": native_role,
        "native_derived_event_houses": native_derived,
        "partner_event_houses": partner_events,
        "mutual_overlays": overlays,
        "d1_d9_confirmation": d1_d9_confirmation,
        "relationship_vargottama": vargottama,
        "kuta_compatibility": kuta,
        "kp_relational_cusps": kp_map,
        "relation_specific_evidence": relation_specific,
        "ashtakavarga_relational_evidence": relational_av,
        "sudarshana_relational_evidence": relational_sx,
        "cross_chart_contacts": contacts,
        "cross_chart_contact_summary": _contact_summary(contacts),
        "relationship_tone_summary": _relationship_tone_summary(
            profile, contacts, overlays, d1_d9_confirmation, vargottama
        ),
        "timing_alignment": {
            "native": native_timing,
            "partner": partner_timing,
            "both_active": bool(native_timing.get("active") and partner_timing.get("active")),
            "one_active": bool(native_timing.get("active") or partner_timing.get("active")),
        },
        "branch_activation": branch_activation,
        "quality_flags": _quality_flags(profile, native_role, native_derived, partner_events),
    }


def _extract_relationship_prefix(user_question: str) -> str:
    m = re.search(r"\[Relationship:\s*([^\]]+)\]", user_question or "", flags=re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _infer_role_house(relation_family: str, raw_label: str, user_question: str) -> int:
    text = f"{raw_label} {user_question}".lower()
    if relation_family == "spouse_romantic":
        return 7
    if relation_family == "parent_child":
        if any(k in text for k in ["son", "daughter", "child", "grandchild"]):
            return 5
        if "father" in text or "guru" in text:
            return 9
        if "mother" in text or "parent" in text:
            return 4
        return 5
    if relation_family == "siblings":
        return 3 if any(k in text for k in ["younger", "brother", "sister", "sibling"]) else 11
    if relation_family == "guru_disciple":
        if any(k in text for k in ["guru", "teacher", "mentor"]):
            return 9
        return 5
    if relation_family == "business_work":
        if any(k in text for k in ["manager", "boss", "authority"]):
            return 10
        if any(k in text for k in ["employee", "staff"]):
            return 6
        return 7
    if relation_family == "friends_social":
        return 11
    return 7


def _derive_houses_from_role(role_house: int, event_houses: List[int]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for h in event_houses:
        if not isinstance(h, int) or h < 1 or h > 12:
            continue
        out[f"{h}_from_role"] = ((role_house + h - 2) % 12) + 1
    return out


def _d1_chart(person_context: Dict[str, Any]) -> Dict[str, Any]:
    return person_context.get("d1_chart") or {}


def _d9_chart(person_context: Dict[str, Any]) -> Dict[str, Any]:
    direct = person_context.get("d9_navamsa")
    if isinstance(direct, dict) and direct:
        return direct.get("divisional_chart") if isinstance(direct.get("divisional_chart"), dict) else direct
    divs = person_context.get("divisional_charts")
    if isinstance(divs, dict):
        for key in ("d9_navamsa", "D9", "d9"):
            block = divs.get(key)
            if isinstance(block, dict) and block:
                return block.get("divisional_chart") if isinstance(block.get("divisional_chart"), dict) else block
    return {}


def _planets(person_context: Dict[str, Any]) -> Dict[str, Any]:
    return _d1_chart(person_context).get("planets") or {}


def _planets_d9(person_context: Dict[str, Any]) -> Dict[str, Any]:
    return _d9_chart(person_context).get("planets") or {}


def _houses(person_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    houses = _d1_chart(person_context).get("houses")
    return houses if isinstance(houses, list) else []


def _houses_d9(person_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    houses = _d9_chart(person_context).get("houses")
    return houses if isinstance(houses, list) else []


def _house_sign(person_context: Dict[str, Any], house: int) -> Optional[int]:
    houses = _houses(person_context)
    if 1 <= house <= len(houses):
        sign = houses[house - 1].get("sign")
        if isinstance(sign, int):
            return sign
    asc = _asc_sign(person_context)
    if asc is not None:
        return (asc + house - 1) % 12
    return None


def _asc_sign(person_context: Dict[str, Any]) -> Optional[int]:
    ai = person_context.get("ascendant_info") or {}
    if isinstance(ai.get("sign_number"), int):
        return int(ai["sign_number"]) - 1
    d1 = _d1_chart(person_context)
    asc = d1.get("ascendant")
    if isinstance(asc, (int, float)):
        return int(float(asc) / 30) % 12
    return None


def _asc_sign_d9(person_context: Dict[str, Any]) -> Optional[int]:
    d9 = _d9_chart(person_context)
    ai = d9.get("ascendant_info") if isinstance(d9.get("ascendant_info"), dict) else {}
    if isinstance(ai.get("sign_number"), int):
        return int(ai["sign_number"]) - 1
    asc = d9.get("ascendant")
    if isinstance(asc, (int, float)):
        return int(float(asc) / 30) % 12
    houses = _houses_d9(person_context)
    if houses:
        sign = houses[0].get("sign")
        if isinstance(sign, int):
            return sign
    return None


def _planets_in_house(person_context: Dict[str, Any], house: int) -> List[str]:
    out = []
    for planet, data in _planets(person_context).items():
        if isinstance(data, dict) and data.get("house") == house:
            out.append(planet)
    return sorted(out)


def _planets_in_house_d9(person_context: Dict[str, Any], house: int) -> List[str]:
    out = []
    for planet, data in _planets_d9(person_context).items():
        if isinstance(data, dict) and data.get("house") == house:
            out.append(planet)
    return sorted(out)


def _house_snapshot(person_context: Dict[str, Any], house: int) -> Dict[str, Any]:
    if not isinstance(house, int) or house < 1 or house > 12:
        return {
            "house": house,
            "sign": "unknown",
            "sign_index": None,
            "lord": "unknown",
            "lord_house": None,
            "lord_sign": None,
            "occupants": [],
        }
    sign = _house_sign(person_context, house)
    lord = _SIGN_LORDS.get(sign) if sign is not None else None
    lord_data = _planets(person_context).get(lord, {}) if lord else {}
    lord_sign = lord_data.get("sign") if isinstance(lord_data, dict) else None
    return {
        "house": house,
        "sign": _SIGN_NAMES[sign] if sign is not None else "unknown",
        "sign_index": sign,
        "sign_flavor": _SIGN_FLAVOR.get(_SIGN_NAMES[sign]) if sign is not None else None,
        "house_theme": _HOUSE_THEME.get(house),
        "lord": lord or "unknown",
        "lord_house": lord_data.get("house") if isinstance(lord_data, dict) else None,
        "lord_sign": _SIGN_NAMES[lord_sign] if isinstance(lord_sign, int) and 0 <= lord_sign <= 11 else None,
        "lord_sign_flavor": _SIGN_FLAVOR.get(_SIGN_NAMES[lord_sign]) if isinstance(lord_sign, int) and 0 <= lord_sign <= 11 else None,
        "occupants": _planets_in_house(person_context, house),
    }


def _house_sign_d9(person_context: Dict[str, Any], house: int) -> Optional[int]:
    houses = _houses_d9(person_context)
    if 1 <= house <= len(houses):
        sign = houses[house - 1].get("sign")
        if isinstance(sign, int):
            return sign
    asc = _asc_sign_d9(person_context)
    if asc is not None:
        return (asc + house - 1) % 12
    return None


def _house_snapshot_d9(person_context: Dict[str, Any], house: int) -> Dict[str, Any]:
    if not isinstance(house, int) or house < 1 or house > 12:
        return {
            "house": house,
            "sign": "unknown",
            "sign_index": None,
            "lord": "unknown",
            "lord_house": None,
            "lord_sign": None,
            "occupants": [],
        }
    sign = _house_sign_d9(person_context, house)
    lord = _SIGN_LORDS.get(sign) if sign is not None else None
    lord_data = _planets_d9(person_context).get(lord, {}) if lord else {}
    lord_sign = lord_data.get("sign") if isinstance(lord_data, dict) else None
    return {
        "house": house,
        "sign": _SIGN_NAMES[sign] if sign is not None else "unknown",
        "sign_index": sign,
        "sign_flavor": _SIGN_FLAVOR.get(_SIGN_NAMES[sign]) if sign is not None else None,
        "house_theme": _HOUSE_THEME.get(house),
        "lord": lord or "unknown",
        "lord_house": lord_data.get("house") if isinstance(lord_data, dict) else None,
        "lord_sign": _SIGN_NAMES[lord_sign] if isinstance(lord_sign, int) and 0 <= lord_sign <= 11 else None,
        "lord_sign_flavor": _SIGN_FLAVOR.get(_SIGN_NAMES[lord_sign]) if isinstance(lord_sign, int) and 0 <= lord_sign <= 11 else None,
        "occupants": _planets_in_house_d9(person_context, house),
    }


def _planet_sign(person_context: Dict[str, Any], planet: str) -> Optional[int]:
    data = _planets(person_context).get(planet)
    if isinstance(data, dict) and isinstance(data.get("sign"), int):
        return data["sign"]
    lon = data.get("longitude") if isinstance(data, dict) else None
    if isinstance(lon, (int, float)):
        return int(float(lon) / 30) % 12
    return None


def _planet_sign_d9(person_context: Dict[str, Any], planet: str) -> Optional[int]:
    data = _planets_d9(person_context).get(planet)
    if isinstance(data, dict) and isinstance(data.get("sign"), int):
        return data["sign"]
    lon = data.get("longitude") if isinstance(data, dict) else None
    if isinstance(lon, (int, float)):
        return int(float(lon) / 30) % 12
    return None


def _planet_longitude(person_context: Dict[str, Any], planet: str) -> Optional[float]:
    data = _planets(person_context).get(planet)
    lon = data.get("longitude") if isinstance(data, dict) else None
    return float(lon) % 360 if isinstance(lon, (int, float)) else None


def _moon_nakshatra(person_context: Dict[str, Any]) -> Optional[str]:
    lon = _planet_longitude(person_context, "Moon")
    if lon is None:
        return None
    idx = min(26, max(0, int(lon / (360.0 / 27.0))))
    return _NAKSHATRAS[idx]


def _planetary_analysis(person_context: Dict[str, Any]) -> Dict[str, Any]:
    pa = person_context.get("planetary_analysis")
    return pa if isinstance(pa, dict) else {}


def _d9_planetary_analysis(person_context: Dict[str, Any]) -> Dict[str, Any]:
    pa = person_context.get("d9_planetary_analysis")
    return pa if isinstance(pa, dict) else {}


def _basic_info(person_context: Dict[str, Any], planet: str, d9: bool = False) -> Dict[str, Any]:
    root = _d9_planetary_analysis(person_context) if d9 else _planetary_analysis(person_context)
    row = root.get(planet) or {}
    bi = row.get("basic_info") if isinstance(row, dict) else {}
    return bi if isinstance(bi, dict) else {}


def _planet_nakshatra_info(person_context: Dict[str, Any], planet: str, d9: bool = False) -> Dict[str, Any]:
    bi = _basic_info(person_context, planet, d9=d9)
    nak = bi.get("nakshatra")
    if not nak:
        sign = _planet_sign_d9(person_context, planet) if d9 else _planet_sign(person_context, planet)
        lon = None
        pdata = _planets_d9(person_context).get(planet) if d9 else _planets(person_context).get(planet)
        if isinstance(pdata, dict):
            lon = pdata.get("longitude")
        if isinstance(lon, (int, float)):
            idx = min(26, max(0, int((float(lon) % 360) / (360.0 / 27.0))))
            nak = _NAKSHATRAS[idx]
    return {
        "planet": planet,
        "nakshatra": nak,
        "pada": bi.get("nakshatra_pada"),
        "sign_name": bi.get("sign_name") or bi.get("sign"),
        "house": bi.get("house"),
        "flavor": _NAKSHATRA_FLAVOR.get(str(nak or "")),
    }


def _point_sign(person_context: Dict[str, Any], point: str) -> Optional[int]:
    if point == "Lagna":
        return _asc_sign(person_context)
    return _planet_sign(person_context, point)


def _point_longitude(person_context: Dict[str, Any], point: str) -> Optional[float]:
    if point == "Lagna":
        asc = _d1_chart(person_context).get("ascendant")
        if isinstance(asc, (int, float)):
            return float(asc) % 360
        sign = _asc_sign(person_context)
        return float(sign * 30) if sign is not None else None
    return _planet_longitude(person_context, point)


def _house_from_sign(person_context: Dict[str, Any], sign: Optional[int]) -> Optional[int]:
    asc = _asc_sign(person_context)
    if asc is None or sign is None:
        return None
    return ((sign - asc) % 12) + 1


def _house_from_sign_d9(person_context: Dict[str, Any], sign: Optional[int]) -> Optional[int]:
    asc = _asc_sign_d9(person_context)
    if asc is None or sign is None:
        return None
    return ((sign - asc) % 12) + 1


def _sign_relation(native_sign: int, partner_sign: int) -> str:
    diff = (partner_sign - native_sign) % 12
    if diff == 0:
        return "same_sign"
    if diff == 6:
        return "opposition"
    if diff in (4, 8):
        return "trine"
    if diff in (2, 10):
        return "sextile"
    if diff in (5, 7):
        return "six_eight_tension"
    if diff in (1, 11):
        return "adjacent"
    return "square"


def _orb_degrees(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    diff = abs(a - b) % 360
    return round(min(diff, 360 - diff), 2)


def _cross_chart_contacts(native: Dict[str, Any], partner: Dict[str, Any]) -> List[Dict[str, Any]]:
    contacts = []
    contact_pairs = [
        *_CORE_CROSS_CONTACTS,
        ("Lagna", "Lagna", "body/path compatibility"),
        ("Lagna", "Moon", "native identity touching partner emotions"),
        ("Moon", "Lagna", "native emotions touching partner identity"),
        ("Lagna", "Venus", "native identity touching partner affection"),
        ("Venus", "Lagna", "native affection touching partner identity"),
        ("Rahu", "Moon", "karmic pull, confusion, or emotional amplification"),
        ("Rahu", "Mars", "impulse, conflict, or high-voltage attraction"),
        ("Rahu", "Lagna", "obsessive or disruptive identity contact"),
        ("Ketu", "Moon", "emotional distance or past-life detachment"),
        ("Ketu", "Lagna", "detachment or karmic separation contact"),
        ("Saturn", "Venus", "delay, duty, seriousness, or coldness in affection"),
        ("Saturn", "Lagna", "pressure, burden, duty, or endurance contact"),
    ]
    seen = set()
    for native_planet, partner_planet, meaning in contact_pairs:
        key = (native_planet, partner_planet)
        if key in seen:
            continue
        seen.add(key)
        ns = _point_sign(native, native_planet)
        ps = _point_sign(partner, partner_planet)
        if ns is None or ps is None:
            continue
        orb = _orb_degrees(_point_longitude(native, native_planet), _point_longitude(partner, partner_planet))
        relation = _sign_relation(ns, ps)
        score = _contact_score(native_planet, partner_planet, relation, orb)
        contacts.append(
            {
                "native_planet": native_planet,
                "partner_planet": partner_planet,
                "native_sign": _SIGN_NAMES[ns],
                "partner_sign": _SIGN_NAMES[ps],
                "relation": relation,
                "orb_degrees": orb,
                "meaning": meaning,
                "strength_score": score,
                "strength_band": _contact_band(score),
                "valence": "supportive" if score >= 4 else "mixed" if score >= 1 else "stress",
            }
        )
    return contacts


def _contact_score(native_point: str, partner_point: str, relation: str, orb: Optional[float]) -> int:
    base = {
        "same_sign": 4,
        "trine": 3,
        "sextile": 2,
        "adjacent": 1,
        "opposition": 0,
        "square": -2,
        "six_eight_tension": -3,
    }.get(relation, 0)
    if orb is not None:
        if orb <= 3:
            base += 2
        elif orb <= 7:
            base += 1
        elif orb >= 20:
            base -= 1
    hard_pairs = {
        ("Saturn", "Moon"),
        ("Saturn", "Venus"),
        ("Rahu", "Moon"),
        ("Rahu", "Venus"),
        ("Rahu", "Mars"),
        ("Rahu", "Lagna"),
        ("Ketu", "Moon"),
        ("Ketu", "Venus"),
        ("Ketu", "Lagna"),
    }
    soft_pairs = {
        ("Moon", "Moon"),
        ("Jupiter", "Moon"),
        ("Jupiter", "Sun"),
        ("Venus", "Mars"),
        ("Mars", "Venus"),
        ("Lagna", "Lagna"),
    }
    pair = (native_point, partner_point)
    if pair in hard_pairs:
        base -= 1
    if pair in soft_pairs:
        base += 1
    return max(-5, min(7, base))


def _contact_band(score: int) -> str:
    if score >= 5:
        return "very_supportive"
    if score >= 3:
        return "supportive"
    if score >= 1:
        return "mixed_support"
    if score >= -1:
        return "mixed_tension"
    if score >= -3:
        return "tension"
    return "high_tension"


def _overlay_rows(source: Dict[str, Any], target: Dict[str, Any], focus_houses: List[int]) -> List[Dict[str, Any]]:
    rows = []
    focus = set(h for h in focus_houses if isinstance(h, int))
    for planet, data in _planets(source).items():
        sign = _planet_sign(source, planet)
        target_house = _house_from_sign(target, sign)
        if target_house is None:
            continue
        if focus and target_house not in focus:
            continue
        rows.append(
            {
                "planet": planet,
                "source_sign": _SIGN_NAMES[sign] if sign is not None else "unknown",
                "target_house": target_house,
                "is_focus_house": target_house in focus,
            }
        )
    return sorted(rows, key=lambda row: (row["target_house"], row["planet"]))


def _overlay_rows_d9(source: Dict[str, Any], target: Dict[str, Any], focus_houses: List[int]) -> List[Dict[str, Any]]:
    rows = []
    focus = set(h for h in focus_houses if isinstance(h, int))
    for planet, data in _planets_d9(source).items():
        sign = _planet_sign_d9(source, planet)
        target_house = _house_from_sign_d9(target, sign)
        if target_house is None:
            continue
        if focus and target_house not in focus:
            continue
        rows.append(
            {
                "planet": planet,
                "source_sign": _SIGN_NAMES[sign] if sign is not None else "unknown",
                "target_house": target_house,
                "is_focus_house": target_house in focus,
            }
        )
    return sorted(rows, key=lambda row: (row["target_house"], row["planet"]))


def _mutual_overlays(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    primary_houses = [h for h in profile.get("primary_houses") or [] if isinstance(h, int)]
    derived = list((profile.get("derived_event_houses_from_role") or {}).values())
    partner_event = [h for h in profile.get("partner_event_houses") or [] if isinstance(h, int)]
    native_focus = sorted(set([1, 7, *primary_houses, *derived]))
    partner_focus = sorted(set([1, 7, *primary_houses, *partner_event]))

    native_asc = _asc_sign(native)
    partner_asc = _asc_sign(partner)
    native_7th = _house_sign(native, 7)
    partner_7th = _house_sign(partner, 7)

    return {
        "lagna_to_lagna": _sign_pair_summary(native_asc, partner_asc),
        "native_7th_to_partner_lagna": _sign_pair_summary(native_7th, partner_asc),
        "partner_7th_to_native_lagna": _sign_pair_summary(partner_7th, native_asc),
        "spouse_axis_detail": _spouse_axis_detail(native, partner, profile),
        "partner_planets_in_native_focus_houses": _overlay_rows(partner, native, native_focus),
        "native_planets_in_partner_focus_houses": _overlay_rows(native, partner, partner_focus),
        "navamsa_d9": _navamsa_overlay_block(native, partner, profile),
        "native_focus_houses": native_focus,
        "partner_focus_houses": partner_focus,
    }


def _spouse_axis_detail(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    if profile.get("relation_family") != "spouse_romantic":
        return {"relevance": "low"}
    partner_lagna_sign = _asc_sign(partner)
    native_lagna_sign = _asc_sign(native)
    native_7th_sign = _house_sign(native, 7)
    partner_7th_sign = _house_sign(partner, 7)
    return {
        "relevance": "primary",
        "partner_lagna_in_native_chart_house": _house_from_sign(native, partner_lagna_sign),
        "native_lagna_in_partner_chart_house": _house_from_sign(partner, native_lagna_sign),
        "partner_7th_in_native_chart_house": _house_from_sign(native, partner_7th_sign),
        "native_7th_in_partner_chart_house": _house_from_sign(partner, native_7th_sign),
        "native_7th_house": _house_snapshot(native, 7),
        "partner_7th_house": _house_snapshot(partner, 7),
    }


def _navamsa_overlay_block(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    if profile.get("relation_family") != "spouse_romantic":
        return {"available": False, "relevance": "low", "reason": "D9 overlay is reserved for spouse/romantic questions."}
    native_d9 = _d9_chart(native)
    partner_d9 = _d9_chart(partner)
    if not native_d9 or not partner_d9:
        return {"available": False, "relevance": "primary", "reason": "D9/Navamsa data missing in one or both charts."}
    focus = [1, 7, 2, 5, 8]
    native_asc = _asc_sign_d9(native)
    partner_asc = _asc_sign_d9(partner)
    native_7th = _house_sign_d9(native, 7)
    partner_7th = _house_sign_d9(partner, 7)
    return {
        "available": True,
        "relevance": "primary",
        "native_d9_lagna_to_partner_d9_lagna": _sign_pair_summary(native_asc, partner_asc),
        "native_d9_7th_to_partner_d9_lagna": _sign_pair_summary(native_7th, partner_asc),
        "partner_d9_7th_to_native_d9_lagna": _sign_pair_summary(partner_7th, native_asc),
        "native_d9_7th_house": _house_snapshot_d9(native, 7),
        "partner_d9_7th_house": _house_snapshot_d9(partner, 7),
        "partner_d9_planets_in_native_d9_focus": _overlay_rows_d9(partner, native, focus),
        "native_d9_planets_in_partner_d9_focus": _overlay_rows_d9(native, partner, focus),
    }


def _relationship_planets(profile: Dict[str, Any], person_context: Dict[str, Any]) -> List[str]:
    planets = []
    for planet in profile.get("primary_karakas") or []:
        if isinstance(planet, str) and planet in _planets(person_context):
            planets.append(planet)
    if profile.get("relation_family") == "spouse_romantic":
        for planet in ("Venus", "Mars", "Moon", "Jupiter"):
            if planet in _planets(person_context) and planet not in planets:
                planets.append(planet)
        sign7 = _house_sign(person_context, 7)
        lord7 = _SIGN_LORDS.get(sign7) if sign7 is not None else None
        if lord7 and lord7 in _planets(person_context) and lord7 not in planets:
            planets.append(lord7)
    return planets


def _d1_d9_confirmation_rows(person_context: Dict[str, Any], planets: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for planet in planets:
        d1 = _planet_sign(person_context, planet)
        d9 = _planet_sign_d9(person_context, planet)
        if d1 is None or d9 is None:
            continue
        relation = _sign_relation(d1, d9)
        rows.append(
            {
                "planet": planet,
                "d1_sign": _SIGN_NAMES[d1],
                "d9_sign": _SIGN_NAMES[d9],
                "same_sign": d1 == d9,
                "relation": relation,
                "confirmation": relation in {"same_sign", "trine", "sextile"},
            }
        )
    return rows


def _d1_d9_confirmation_block(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_planets = _relationship_planets(profile, native)
    partner_planets = _relationship_planets(profile, partner)
    native_rows = _d1_d9_confirmation_rows(native, native_planets)
    partner_rows = _d1_d9_confirmation_rows(partner, partner_planets)
    return {
        "native": native_rows,
        "partner": partner_rows,
        "native_confirmed_count": sum(1 for row in native_rows if row.get("confirmation")),
        "partner_confirmed_count": sum(1 for row in partner_rows if row.get("confirmation")),
    }


def _relationship_vargottama_rows(person_context: Dict[str, Any], planets: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for planet in planets:
        d1 = _planet_sign(person_context, planet)
        d9 = _planet_sign_d9(person_context, planet)
        if d1 is None or d9 is None:
            continue
        rows.append(
            {
                "planet": planet,
                "d1_sign": _SIGN_NAMES[d1],
                "d9_sign": _SIGN_NAMES[d9],
                "vargottama_like": d1 == d9,
            }
        )
    return rows


def _relationship_vargottama_block(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_rows = _relationship_vargottama_rows(native, _relationship_planets(profile, native))
    partner_rows = _relationship_vargottama_rows(partner, _relationship_planets(profile, partner))
    return {
        "native": native_rows,
        "partner": partner_rows,
        "native_count": sum(1 for row in native_rows if row.get("vargottama_like")),
        "partner_count": sum(1 for row in partner_rows if row.get("vargottama_like")),
    }


def _sign_flavor_rows(person_context: Dict[str, Any], houses: List[int], label_prefix: str) -> List[Dict[str, Any]]:
    rows = []
    for house in houses:
        snap = _house_snapshot(person_context, house)
        rows.append(
            {
                "label": f"{label_prefix}_{house}",
                "house": house,
                "sign": snap.get("sign"),
                "sign_flavor": snap.get("sign_flavor"),
                "house_theme": snap.get("house_theme"),
                "lord": snap.get("lord"),
                "lord_sign": snap.get("lord_sign"),
                "lord_sign_flavor": snap.get("lord_sign_flavor"),
            }
        )
    return rows


def _relationship_nakshatra_focus(person_context: Dict[str, Any], profile: Dict[str, Any], label: str) -> Dict[str, Any]:
    relation_planets = _relationship_planets(profile, person_context)
    seen: List[str] = []
    for planet in relation_planets:
        if planet not in seen:
            seen.append(planet)
    moon = "Moon"
    if moon in _planets(person_context) and moon not in seen:
        seen.insert(0, moon)
    sign7 = _house_sign(person_context, 7)
    lord7 = _SIGN_LORDS.get(sign7) if sign7 is not None else None
    if lord7 and lord7 in _planets(person_context) and lord7 not in seen:
        seen.insert(0, lord7)
    rows = [_planet_nakshatra_info(person_context, planet) for planet in seen[:6]]
    d9_rows = [_planet_nakshatra_info(person_context, planet, d9=True) for planet in seen[:4] if _basic_info(person_context, planet, d9=True)]
    return {
        "label": label,
        "moon": _planet_nakshatra_info(person_context, "Moon") if "Moon" in _planets(person_context) else {},
        "seventh_lord": _planet_nakshatra_info(person_context, lord7) if lord7 else {},
        "relationship_planets": rows,
        "d9_relationship_planets": d9_rows,
    }


def _relationship_tone_summary(
    profile: Dict[str, Any],
    contacts: List[Dict[str, Any]],
    overlays: Dict[str, Any],
    d1_d9_confirmation: Dict[str, Any],
    vargottama: Dict[str, Any],
) -> Dict[str, Any]:
    support = sum(max(0, int(c.get("strength_score") or 0)) for c in contacts)
    pressure = sum(abs(min(0, int(c.get("strength_score") or 0))) for c in contacts)
    nodal_hits = sum(
        1
        for c in contacts
        if c.get("native_planet") in {"Rahu", "Ketu"} or c.get("partner_planet") in {"Rahu", "Ketu"}
    )
    saturn_hits = sum(
        1 for c in contacts if c.get("native_planet") == "Saturn" or c.get("partner_planet") == "Saturn"
    )
    volatility = nodal_hits * 2 + saturn_hits
    support += int(d1_d9_confirmation.get("native_confirmed_count") or 0)
    support += int(d1_d9_confirmation.get("partner_confirmed_count") or 0)
    support += int(vargottama.get("native_count") or 0) * 2
    support += int(vargottama.get("partner_count") or 0) * 2
    if profile.get("relation_family") == "spouse_romantic":
        d9 = overlays.get("navamsa_d9") or {}
        if d9.get("available"):
            support += len(d9.get("partner_d9_planets_in_native_d9_focus") or []) // 2
            support += len(d9.get("native_d9_planets_in_partner_d9_focus") or []) // 2

    balance = support - pressure - volatility
    if balance >= 8:
        tone = "bond_dominant"
    elif balance >= 2:
        tone = "bond_with_pressure"
    elif balance >= -3:
        tone = "mixed_unstable"
    else:
        tone = "pressure_volatility_dominant"
    return {
        "bond_score": support,
        "pressure_score": pressure,
        "volatility_score": volatility,
        "net_score": balance,
        "tone": tone,
    }


def _planets_present(person_context: Dict[str, Any], names: List[str]) -> List[str]:
    planets = _planets(person_context)
    return [name for name in names if name in planets]


def _snapshot_map(person_context: Dict[str, Any], houses: List[int], prefix: str) -> List[Dict[str, Any]]:
    return [
        {"label": f"{prefix}_{house}", **_house_snapshot(person_context, house)}
        for house in houses
        if isinstance(house, int)
    ]


def _role_overlay_focus(native: Dict[str, Any], partner: Dict[str, Any], native_houses: List[int], partner_houses: List[int]) -> Dict[str, Any]:
    return {
        "partner_into_native": _overlay_rows(partner, native, native_houses),
        "native_into_partner": _overlay_rows(native, partner, partner_houses),
    }


def _relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    family = profile.get("relation_family")
    builders = {
        "spouse_romantic": _spouse_relation_specific_evidence,
        "guru_disciple": _guru_relation_specific_evidence,
        "business_work": _business_relation_specific_evidence,
        "parent_child": _parent_child_relation_specific_evidence,
        "siblings": _siblings_relation_specific_evidence,
        "friends_social": _friends_relation_specific_evidence,
    }
    block = builders.get(family, _generic_relation_specific_evidence)(native, partner, profile)
    block["family"] = family
    return block


def _spouse_relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_houses = [2, 5, 7, 8, 12]
    partner_houses = [2, 5, 7, 8, 12]
    return {
        "focus": "spouse_axis",
        "native_houses": _snapshot_map(native, native_houses, "native"),
        "partner_houses": _snapshot_map(partner, partner_houses, "partner"),
        "native_relationship_planets": _planets_present(native, ["Venus", "Mars", "Moon", "Jupiter"]),
        "partner_relationship_planets": _planets_present(partner, ["Venus", "Mars", "Moon", "Jupiter"]),
        "sign_flavor_native": _sign_flavor_rows(native, native_houses, "native"),
        "sign_flavor_partner": _sign_flavor_rows(partner, partner_houses, "partner"),
        "nakshatra_flavor_native": _relationship_nakshatra_focus(native, profile, "native"),
        "nakshatra_flavor_partner": _relationship_nakshatra_focus(partner, profile, "partner"),
        "overlay_focus": _role_overlay_focus(native, partner, native_houses, partner_houses),
    }


def _guru_relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_role = int(profile.get("native_role_house") or 9)
    native_houses = sorted(set([5, 9, native_role, ((native_role + 7 - 2) % 12) + 1, ((native_role + 11 - 2) % 12) + 1]))
    partner_houses = [5, 9, 11]
    return {
        "focus": "teaching_guidance_axis",
        "native_role_house": _house_snapshot(native, native_role),
        "native_learning_houses": _snapshot_map(native, native_houses, "native"),
        "partner_guidance_houses": _snapshot_map(partner, partner_houses, "partner"),
        "teacher_karakas_native": _planets_present(native, ["Jupiter", "Sun", "Mercury"]),
        "teacher_karakas_partner": _planets_present(partner, ["Jupiter", "Sun", "Mercury"]),
        "sign_flavor_native": _sign_flavor_rows(native, native_houses, "native"),
        "sign_flavor_partner": _sign_flavor_rows(partner, partner_houses, "partner"),
        "nakshatra_flavor_native": _relationship_nakshatra_focus(native, profile, "native"),
        "nakshatra_flavor_partner": _relationship_nakshatra_focus(partner, profile, "partner"),
        "overlay_focus": _role_overlay_focus(native, partner, native_houses, partner_houses),
    }


def _business_relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_role = int(profile.get("native_role_house") or 7)
    native_houses = sorted(set([native_role, 2, 6, 10, 11]))
    partner_houses = [2, 6, 7, 10, 11]
    return {
        "focus": "work_trust_hierarchy_axis",
        "native_role_house": _house_snapshot(native, native_role),
        "native_business_houses": _snapshot_map(native, native_houses, "native"),
        "partner_business_houses": _snapshot_map(partner, partner_houses, "partner"),
        "authority_chain": {
            "native_role_house_number": native_role,
            "partner_lagna_in_native_house": _house_from_sign(native, _asc_sign(partner)),
            "native_lagna_in_partner_house": _house_from_sign(partner, _asc_sign(native)),
        },
        "work_karakas_native": _planets_present(native, ["Mercury", "Saturn", "Sun", "Venus"]),
        "work_karakas_partner": _planets_present(partner, ["Mercury", "Saturn", "Sun", "Venus"]),
        "sign_flavor_native": _sign_flavor_rows(native, native_houses, "native"),
        "sign_flavor_partner": _sign_flavor_rows(partner, partner_houses, "partner"),
        "nakshatra_flavor_native": _relationship_nakshatra_focus(native, profile, "native"),
        "nakshatra_flavor_partner": _relationship_nakshatra_focus(partner, profile, "partner"),
        "overlay_focus": _role_overlay_focus(native, partner, native_houses, partner_houses),
    }


def _parent_child_relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_role = int(profile.get("native_role_house") or 5)
    native_houses = sorted(set([4, 5, 9, native_role, 2]))
    partner_houses = [4, 5, 9, 2]
    return {
        "focus": "caregiving_authority_axis",
        "native_role_house": _house_snapshot(native, native_role),
        "native_family_houses": _snapshot_map(native, native_houses, "native"),
        "partner_family_houses": _snapshot_map(partner, partner_houses, "partner"),
        "care_karakas_native": _planets_present(native, ["Moon", "Sun", "Jupiter", "Saturn"]),
        "care_karakas_partner": _planets_present(partner, ["Moon", "Sun", "Jupiter", "Saturn"]),
        "sign_flavor_native": _sign_flavor_rows(native, native_houses, "native"),
        "sign_flavor_partner": _sign_flavor_rows(partner, partner_houses, "partner"),
        "nakshatra_flavor_native": _relationship_nakshatra_focus(native, profile, "native"),
        "nakshatra_flavor_partner": _relationship_nakshatra_focus(partner, profile, "partner"),
        "overlay_focus": _role_overlay_focus(native, partner, native_houses, partner_houses),
    }


def _siblings_relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_role = int(profile.get("native_role_house") or 3)
    native_houses = sorted(set([3, 6, 8, 11, native_role]))
    partner_houses = [3, 6, 8, 11]
    return {
        "focus": "support_rivalry_axis",
        "native_role_house": _house_snapshot(native, native_role),
        "native_sibling_houses": _snapshot_map(native, native_houses, "native"),
        "partner_sibling_houses": _snapshot_map(partner, partner_houses, "partner"),
        "sibling_karakas_native": _planets_present(native, ["Mars", "Mercury", "Saturn"]),
        "sibling_karakas_partner": _planets_present(partner, ["Mars", "Mercury", "Saturn"]),
        "sign_flavor_native": _sign_flavor_rows(native, native_houses, "native"),
        "sign_flavor_partner": _sign_flavor_rows(partner, partner_houses, "partner"),
        "nakshatra_flavor_native": _relationship_nakshatra_focus(native, profile, "native"),
        "nakshatra_flavor_partner": _relationship_nakshatra_focus(partner, profile, "partner"),
        "overlay_focus": _role_overlay_focus(native, partner, native_houses, partner_houses),
    }


def _friends_relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_role = int(profile.get("native_role_house") or 11)
    native_houses = sorted(set([3, 5, 11, native_role]))
    partner_houses = [3, 5, 11]
    return {
        "focus": "trust_network_axis",
        "native_role_house": _house_snapshot(native, native_role),
        "native_social_houses": _snapshot_map(native, native_houses, "native"),
        "partner_social_houses": _snapshot_map(partner, partner_houses, "partner"),
        "social_karakas_native": _planets_present(native, ["Mercury", "Venus", "Moon"]),
        "social_karakas_partner": _planets_present(partner, ["Mercury", "Venus", "Moon"]),
        "sign_flavor_native": _sign_flavor_rows(native, native_houses, "native"),
        "sign_flavor_partner": _sign_flavor_rows(partner, partner_houses, "partner"),
        "nakshatra_flavor_native": _relationship_nakshatra_focus(native, profile, "native"),
        "nakshatra_flavor_partner": _relationship_nakshatra_focus(partner, profile, "partner"),
        "overlay_focus": _role_overlay_focus(native, partner, native_houses, partner_houses),
    }


def _generic_relation_specific_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    native_role = int(profile.get("native_role_house") or 7)
    native_houses = sorted(set([native_role, *(profile.get("primary_houses") or [])]))
    partner_houses = sorted(set(profile.get("partner_event_houses") or profile.get("primary_houses") or [7]))
    return {
        "focus": "general_relation_axis",
        "native_role_house": _house_snapshot(native, native_role),
        "native_houses": _snapshot_map(native, native_houses, "native"),
        "partner_houses": _snapshot_map(partner, partner_houses, "partner"),
        "sign_flavor_native": _sign_flavor_rows(native, native_houses, "native"),
        "sign_flavor_partner": _sign_flavor_rows(partner, partner_houses, "partner"),
        "nakshatra_flavor_native": _relationship_nakshatra_focus(native, profile, "native"),
        "nakshatra_flavor_partner": _relationship_nakshatra_focus(partner, profile, "partner"),
        "overlay_focus": _role_overlay_focus(native, partner, native_houses, partner_houses),
    }


def _av_root(person_context: Dict[str, Any]) -> Dict[str, Any]:
    root = person_context.get("ashtakavarga")
    return root if isinstance(root, dict) else {}


def _av_slice_root(person_context: Dict[str, Any]) -> Dict[str, Any]:
    sliced = build_ashtakavarga_slice(person_context)
    root = sliced.get("ashtakavarga")
    return root if isinstance(root, dict) else {}


def _av_d1_block(person_context: Dict[str, Any]) -> Dict[str, Any]:
    root = _av_slice_root(person_context) or _av_root(person_context)
    d1 = root.get("d1_rashi")
    return d1 if isinstance(d1, dict) else {}


def _av_house_row(person_context: Dict[str, Any], house: int) -> Dict[str, Any]:
    d1 = _av_d1_block(person_context)
    ho = d1.get("Ho")
    if isinstance(ho, dict):
        row = ho.get(str(house)) or ho.get(house)
        if isinstance(row, dict):
            return row
    return {}


def _av_sarva_for_sign(person_context: Dict[str, Any], sign_idx: Optional[int]) -> Optional[int]:
    if sign_idx is None:
        return None
    d1 = _av_d1_block(person_context)
    ho = d1.get("Ho")
    if isinstance(ho, dict):
        for row in ho.values():
            if isinstance(row, dict) and row.get("z") == sign_idx:
                try:
                    return int(row.get("s"))
                except (TypeError, ValueError):
                    pass
    sarva = d1.get("sarvashtakavarga")
    if isinstance(sarva, dict):
        try:
            return int(sarva.get(str(sign_idx)))
        except (TypeError, ValueError):
            return None
    return None


def _av_bav_for_sign(person_context: Dict[str, Any], planet: str, sign_idx: Optional[int]) -> Optional[int]:
    if sign_idx is None:
        return None
    d1 = _av_d1_block(person_context)
    ho = d1.get("Ho")
    if isinstance(ho, dict):
        for row in ho.values():
            if isinstance(row, dict) and row.get("z") == sign_idx:
                bp = row.get("bp") or row.get("B") or {}
                if isinstance(bp, dict):
                    try:
                        return int(bp.get(planet))
                    except (TypeError, ValueError):
                        return None
    bav_root = d1.get("bhinnashtakavarga") or {}
    if isinstance(bav_root, dict):
        chart = bav_root.get(planet)
        if isinstance(chart, dict):
            values = chart.get("chart") or chart.get("bindus") or chart
            if isinstance(values, dict):
                try:
                    return int(values.get(str(sign_idx)))
                except (TypeError, ValueError):
                    return None
    return None


def _av_house_band(score: Optional[int]) -> str:
    if score is None:
        return "unknown"
    if score >= 30:
        return "strong"
    if score >= 25:
        return "workable"
    return "weak"


def _av_focus_rows(person_context: Dict[str, Any], houses: List[int], planets: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for house in houses:
        hrow = _av_house_row(person_context, house)
        sign_idx = _house_sign(person_context, house)
        if isinstance(hrow.get("z"), int):
            sign_idx = int(hrow["z"]) - 1
        try:
            sav = int(hrow.get("s")) if hrow.get("s") is not None else _av_sarva_for_sign(person_context, sign_idx)
        except (TypeError, ValueError):
            sav = _av_sarva_for_sign(person_context, sign_idx)
        bp = {}
        for planet in planets:
            bav = None
            bmap = hrow.get("B") or hrow.get("bp") or {}
            if isinstance(bmap, dict):
                try:
                    bav = int(bmap.get(planet))
                except (TypeError, ValueError):
                    bav = None
            if bav is None:
                bav = _av_bav_for_sign(person_context, planet, sign_idx)
            if bav is not None:
                bp[planet] = bav
        rows.append(
            {
                "house": house,
                "sign": _SIGN_NAMES[sign_idx] if isinstance(sign_idx, int) else "unknown",
                "sign_index": sign_idx,
                "sav": sav,
                "band": _av_house_band(sav),
                "bav": bp,
            }
        )
    return rows


def _av_conflicts_rel(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        if row.get("band") != "strong":
            continue
        weak_bav = [planet for planet, val in (row.get("bav") or {}).items() if isinstance(val, int) and val < 3]
        if weak_bav:
            out.append({"house": row.get("house"), "weak_bav_planets": weak_bav})
    return out


def _relational_ashtakavarga_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    if not (_has_ashtakavarga(native) or _has_ashtakavarga(partner)):
        return {"available": False, "reason": "Ashtakavarga data missing in both charts."}
    family = str(profile.get("relation_family") or "")
    focus_houses = sorted(
        set(
            [
                *(h for h in profile.get("primary_houses") or [] if isinstance(h, int)),
                *(h for h in (profile.get("derived_event_houses_from_role") or {}).values() if isinstance(h, int)),
                *(h for h in profile.get("partner_event_houses") or [] if isinstance(h, int)),
            ]
        )
    )
    planets = []
    for p in profile.get("primary_karakas") or []:
        if isinstance(p, str) and p in _SIGN_LORDS.values() and p not in planets:
            planets.append(p)
    if family == "spouse_romantic":
        for p in ("Venus", "Mars", "Moon", "Jupiter"):
            if p not in planets:
                planets.append(p)
    native_rows = _av_focus_rows(native, focus_houses, planets)
    partner_rows = _av_focus_rows(partner, focus_houses, planets)
    native_usable = any(isinstance(row.get("sav"), int) or bool(row.get("bav")) for row in native_rows)
    partner_usable = any(isinstance(row.get("sav"), int) or bool(row.get("bav")) for row in partner_rows)
    if not (native_usable or partner_usable):
        return {
            "available": False,
            "reason": "Ashtakavarga payload exists but usable house-indexed SAV/BAV rows were not available for these focus houses.",
            "focus_houses": focus_houses,
            "focus_planets": planets,
        }
    native_strong = sum(1 for row in native_rows if row.get("band") == "strong")
    partner_strong = sum(1 for row in partner_rows if row.get("band") == "strong")
    native_weak = sum(1 for row in native_rows if row.get("band") == "weak")
    partner_weak = sum(1 for row in partner_rows if row.get("band") == "weak")
    support = (
        "both_supportive"
        if native_strong > native_weak and partner_strong > partner_weak
        else "native_supportive_partner_mixed"
        if native_strong > native_weak
        else "partner_supportive_native_mixed"
        if partner_strong > partner_weak
        else "mixed_or_weak"
    )
    dasha_native = _current_dasha_lords(native)
    dasha_partner = _current_dasha_lords(partner)
    return {
        "available": True,
        "focus_houses": focus_houses,
        "focus_planets": planets,
        "native": {
            "rows": native_rows,
            "conflicts": _av_conflicts_rel(native_rows),
            "dasha_lords": dasha_native,
        },
        "partner": {
            "rows": partner_rows,
            "conflicts": _av_conflicts_rel(partner_rows),
            "dasha_lords": dasha_partner,
        },
        "comparative": {
            "support": support,
            "native_strong_count": native_strong,
            "partner_strong_count": partner_strong,
            "native_weak_count": native_weak,
            "partner_weak_count": partner_weak,
        },
    }


def _relational_sudarshana_category(profile: Dict[str, Any]) -> str:
    family = str(profile.get("relation_family") or "")
    if family == "business_work":
        return "career"
    if family == "guru_disciple":
        return "education"
    return "relationship"


def _build_sudarshana_for_category(person_context: Dict[str, Any], category: str) -> Dict[str, Any]:
    ctx = copy.deepcopy(person_context)
    intent = ctx.get("intent") or {}
    if not isinstance(intent, dict):
        intent = {}
    intent["category"] = category
    ctx["intent"] = intent
    return _build_sudarshana_reasoning_spine(ctx)


def _relational_sudarshana_evidence(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    if not (_has_sudarshana(native) or _has_sudarshana(partner)):
        return {"available": False, "reason": "Sudarshana data missing in both charts."}
    category = _relational_sudarshana_category(profile)
    native_sx = _build_sudarshana_for_category(native, category)
    partner_sx = _build_sudarshana_for_category(partner, category)
    native_topic = (native_sx.get("topic") or {})
    partner_topic = (partner_sx.get("topic") or {})
    native_current = ((native_sx.get("current") or {}).get("topic") or {})
    partner_current = ((partner_sx.get("current") or {}).get("topic") or {})
    return {
        "available": True,
        "focus_category": category,
        "native": {
            "support": native_topic.get("support"),
            "dominant_houses": native_sx.get("dom") or [],
            "rows": native_topic.get("rows") or [],
            "current": native_current,
            "triggers": (native_sx.get("triggers") or {}).get("rows") or [],
        },
        "partner": {
            "support": partner_topic.get("support"),
            "dominant_houses": partner_sx.get("dom") or [],
            "rows": partner_topic.get("rows") or [],
            "current": partner_current,
            "triggers": (partner_sx.get("triggers") or {}).get("rows") or [],
        },
        "comparative": {
            "both_supportive": native_topic.get("support") == "supportive" and partner_topic.get("support") == "supportive",
            "both_challenging": native_topic.get("support") == "challenging" and partner_topic.get("support") == "challenging",
            "native_current_support": native_current.get("support"),
            "partner_current_support": partner_current.get("support"),
        },
    }


def _kuta_compatibility(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    relation = profile.get("relation_family")
    relevant = relation in {"spouse_romantic", "parent_child", "family", "siblings"}
    native_nak = _moon_nakshatra(native)
    partner_nak = _moon_nakshatra(partner)
    out: Dict[str, Any] = {
        "available": bool(native_nak and partner_nak),
        "relevance": "primary" if relation == "spouse_romantic" else "supporting" if relevant else "low",
        "native_moon_nakshatra": native_nak,
        "partner_moon_nakshatra": partner_nak,
        "caveat": "Classical Ashtakoota is marriage-oriented; for non-romantic bonds, use it only as Moon-temperament support.",
    }
    if not native_nak or not partner_nak:
        out["reason"] = "Moon nakshatra missing from one or both charts."
        return out
    try:
        result = GunaMilanCalculator().calculate_ashtakoot(native_nak, partner_nak)
    except Exception as exc:  # pragma: no cover - defensive against future calculator changes
        out.update({"available": False, "error": str(exc)})
        return out
    critical = result.get("critical_issues") or []
    out.update(
        {
            "total_score": result.get("total_score"),
            "max_score": result.get("max_score"),
            "percentage": result.get("percentage"),
            "compatibility_level": result.get("compatibility_level"),
            "critical_issues": critical,
            "koot_scores": {
                key: {
                    "score": val.get("score"),
                    "max_score": val.get("max_score"),
                    "description": val.get("description"),
                }
                for key, val in (result.get("koots") or {}).items()
                if isinstance(val, dict)
            },
        }
    )
    return out


def _kp_analysis(person_context: Dict[str, Any]) -> Dict[str, Any]:
    kp = person_context.get("kp_analysis")
    return kp if isinstance(kp, dict) else {}


def _dict_get_house(mapping: Dict[str, Any], house: int) -> Any:
    if not isinstance(mapping, dict):
        return None
    return mapping.get(house) or mapping.get(str(house))


def _kp_cusp_row(person_context: Dict[str, Any], house: int, label: str) -> Dict[str, Any]:
    kp = _kp_analysis(person_context)
    cusp_lords = kp.get("cusp_lords") or {}
    significators = kp.get("significators") or {}
    return {
        "label": label,
        "house": house,
        "cusp_lords": _dict_get_house(cusp_lords, house),
        "significators": _dict_get_house(significators, house) or [],
        "available": bool(_dict_get_house(cusp_lords, house) or _dict_get_house(significators, house)),
    }


def _normalize_house_list(value: Any) -> List[int]:
    if isinstance(value, list):
        out = []
        for item in value:
            try:
                out.append(int(item))
            except (TypeError, ValueError):
                continue
        return out
    return []


def _kp_target_trigger_candidates(person_context: Dict[str, Any], house: int) -> List[Dict[str, Any]]:
    kp = _kp_analysis(person_context)
    planet_significators = kp.get("planet_significators") or {}
    four_step = kp.get("four_step_theory") or {}
    dasha_lords = set(_current_dasha_lords(person_context))
    candidates = []
    for planet, houses in planet_significators.items():
        house_hits = _normalize_house_list(houses)
        if house not in house_hits:
            continue
        chain = four_step.get(planet) or {}
        step_hits = []
        for step_name in ("planet", "star_lord", "sub_lord", "sub_sub_lord"):
            step = chain.get(step_name) or {}
            step_houses = _normalize_house_list(step.get("houses"))
            if house in step_houses:
                step_hits.append(
                    {
                        "step": step_name,
                        "name": step.get("name"),
                        "houses": step_houses,
                    }
                )
        candidates.append(
            {
                "planet": planet,
                "houses": house_hits,
                "active_in_current_dasha": planet in dasha_lords,
                "step_hits": step_hits,
                "step_hit_count": len(step_hits),
                "current_dasha_match": planet if planet in dasha_lords else None,
            }
        )
    candidates.sort(
        key=lambda row: (
            not row["active_in_current_dasha"],
            -row["step_hit_count"],
            row["planet"],
        )
    )
    return candidates


def _kp_four_step_dasha_trigger(person_context: Dict[str, Any], houses: List[int], label_prefix: str) -> Dict[str, Any]:
    dasha_lords = _current_dasha_lords(person_context)
    targets = []
    trigger_planets = []
    seen_planets = set()
    for house in houses:
        if not isinstance(house, int):
            continue
        candidates = _kp_target_trigger_candidates(person_context, house)
        targets.append(
            {
                "label": f"{label_prefix}_{house}",
                "house": house,
                "candidates": candidates[:6],
            }
        )
        for cand in candidates:
            planet = cand.get("planet")
            if planet and planet not in seen_planets:
                seen_planets.add(planet)
                trigger_planets.append(cand)
    active = [row for row in trigger_planets if row.get("active_in_current_dasha")]
    strongest = sorted(
        trigger_planets,
        key=lambda row: (
            not row["active_in_current_dasha"],
            -row["step_hit_count"],
            row["planet"],
        ),
    )[:6]
    return {
        "dasha_lords": dasha_lords,
        "targets": targets,
        "active_trigger_planets": active,
        "strongest_trigger_planets": strongest,
    }


def _kp_relational_cusp_map(native: Dict[str, Any], partner: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    role_house = profile.get("native_role_house")
    derived = profile.get("derived_event_houses_from_role") or {}
    partner_event = profile.get("partner_event_houses") or []
    native_rows = []
    if isinstance(role_house, int):
        native_rows.append(_kp_cusp_row(native, role_house, "native_role_cusp"))
    native_rows.extend(
        _kp_cusp_row(native, house, label)
        for label, house in derived.items()
        if isinstance(house, int)
    )
    partner_rows = [
        _kp_cusp_row(partner, h, f"partner_{h}_cusp")
        for h in partner_event
        if isinstance(h, int)
    ]
    rows = [*native_rows, *partner_rows]
    native_target_houses = []
    if isinstance(role_house, int):
        native_target_houses.append(role_house)
    native_target_houses.extend(house for house in derived.values() if isinstance(house, int))
    partner_target_houses = [h for h in partner_event if isinstance(h, int)]
    return {
        "available": any(row.get("available") for row in rows),
        "native_targets": native_rows,
        "partner_targets": partner_rows,
        "native_four_step_trigger": _kp_four_step_dasha_trigger(native, native_target_houses, "native"),
        "partner_four_step_trigger": _kp_four_step_dasha_trigger(partner, partner_target_houses, "partner"),
        "note": "KP branch should use these target cusps in Sign Lord -> Star Lord -> Sub Lord order, then dasha trigger.",
    }


def _sign_pair_summary(a: Optional[int], b: Optional[int]) -> Dict[str, Any]:
    return {
        "a_sign": _SIGN_NAMES[a] if isinstance(a, int) and 0 <= a <= 11 else "unknown",
        "b_sign": _SIGN_NAMES[b] if isinstance(b, int) and 0 <= b <= 11 else "unknown",
        "relation": _sign_relation(a, b) if isinstance(a, int) and isinstance(b, int) else "unknown",
    }


def _contact_summary(contacts: List[Dict[str, Any]]) -> Dict[str, int]:
    supportive = {"same_sign", "trine", "sextile"}
    hard = {"opposition", "six_eight_tension", "square"}
    return {
        "supportive": sum(1 for c in contacts if c.get("relation") in supportive),
        "hard": sum(1 for c in contacts if c.get("relation") in hard),
        "adjacent": sum(1 for c in contacts if c.get("relation") == "adjacent"),
        "nodal": sum(1 for c in contacts if c.get("native_planet") in {"Rahu", "Ketu"} or c.get("partner_planet") in {"Rahu", "Ketu"}),
        "saturn_pressure": sum(1 for c in contacts if c.get("native_planet") == "Saturn" or c.get("partner_planet") == "Saturn"),
        "weighted_support": sum(max(0, int(c.get("strength_score") or 0)) for c in contacts),
        "weighted_tension": sum(abs(min(0, int(c.get("strength_score") or 0))) for c in contacts),
        "total": len(contacts),
    }


def _branch_activation(
    profile: Dict[str, Any],
    contacts: List[Dict[str, Any]],
    overlays: Dict[str, Any],
    kuta: Dict[str, Any],
    kp_map: Dict[str, Any],
    native: Dict[str, Any],
    partner: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    event = profile.get("event_topic")
    relation = profile.get("relation_family")
    mode = profile.get("question_mode")
    safety = (profile.get("answer_policy") or {}).get("safety_class")
    has_nodal = any(
        c.get("native_planet") in {"Rahu", "Ketu"} or c.get("partner_planet") in {"Rahu", "Ketu"}
        for c in contacts
    )
    overlay_count = len(overlays.get("partner_planets_in_native_focus_houses") or []) + len(
        overlays.get("native_planets_in_partner_focus_houses") or []
    )

    activation = {
        "parashari_relational": {
            "priority": "primary",
            "reason": "Base house, lord, karaka, divisional, dasha, and transit synthesis.",
        },
        "timing_relational": {
            "priority": "primary" if mode in {"predictive_yes_no", "predictive_timing"} else "supporting",
            "reason": "Current dasha activation for one or both charts.",
        },
        "kp_relational": {
            "priority": "primary" if event in {"legal_confinement", "reconciliation_return", "separation_break", "money_dispute", "business_betrayal"} else "supporting",
            "reason": "Strongest branch for yes/no and event outcome questions when cusp data exists.",
            "data_available": bool(kp_map.get("available")),
        },
        "nadi_relational": {
            "priority": "primary" if event in {"trust_infidelity", "business_betrayal", "guru_trust_breach"} or has_nodal else "supporting",
            "reason": "Useful for hidden motives, nodal/Saturn patterns, karmic repetition, and sudden breaks.",
        },
        "nakshatra_relational": {
            "priority": "primary" if relation in {"spouse_romantic", "parent_child", "guru_disciple"} else "supporting",
            "reason": "Temperament, emotional resonance, trust pattern, and family/guru texture.",
        },
        "jaimini_relational": {
            "priority": "primary" if relation == "spouse_romantic" or event in {"separation_break", "reconciliation_return"} else "supporting",
            "reason": "Manifestation through chara karakas, arudhas, UL/A7, argala, and dasha signs.",
        },
        "ashtakoota_relational": {
            "priority": "primary" if relation == "spouse_romantic" and kuta.get("available") else "supporting" if kuta.get("available") else "skipped",
            "reason": "Moon nakshatra Kuta/Guna Milan for marriage-oriented compatibility; supporting only outside romantic bonds.",
            "data_available": bool(kuta.get("available")),
        },
        "ashtakavarga_relational": {
            "priority": "supporting" if _has_ashtakavarga(native) or _has_ashtakavarga(partner) else "skipped",
            "reason": "Use only as support for timing/house endurance if SAV/BAV data exists.",
            "data_available": bool(_has_ashtakavarga(native) or _has_ashtakavarga(partner)),
        },
        "sudarshan_relational": {
            "priority": "supporting" if _has_sudarshana(native) or _has_sudarshana(partner) else "skipped",
            "reason": "Use only as a tri-perspective confirmation layer for timing or event pressure if Sudarshana data exists.",
            "data_available": bool(_has_sudarshana(native) or _has_sudarshana(partner)),
        },
    }

    if safety == "abuse_or_immediate_safety":
        activation["parashari_relational"]["priority"] = "primary"
        activation["timing_relational"]["priority"] = "supporting"
        activation["kp_relational"]["priority"] = "primary"
        activation["nadi_relational"]["priority"] = "supporting"
    if overlay_count == 0:
        for row in activation.values():
            row["data_note"] = "Mutual overlay evidence is limited or unavailable from the supplied chart payload."
    return activation


def _has_ashtakavarga(person_context: Dict[str, Any]) -> bool:
    av = person_context.get("ashtakavarga")
    return isinstance(av, dict) and bool(av)


def _has_sudarshana(person_context: Dict[str, Any]) -> bool:
    return any(isinstance(person_context.get(key), dict) and person_context.get(key) for key in ("sudarshana_chakra", "sudarshana_dasha"))


def _current_dasha_lords(person_context: Dict[str, Any]) -> List[str]:
    current = person_context.get("current_dashas") or {}
    lords = []
    for key in ("mahadasha", "antardasha", "pratyantardasha", "sookshma"):
        node = current.get(key)
        if isinstance(node, dict):
            lord = node.get("planet") or node.get("lord") or node.get("name")
        else:
            lord = node
        if isinstance(lord, str) and lord and lord != "Unknown":
            lords.append(lord)
    return lords


def _timing_alignment(person_context: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    lords = _current_dasha_lords(person_context)
    relevant = set(profile.get("primary_karakas") or [])
    house_lords = []
    for h in profile.get("primary_houses") or []:
        snap = _house_snapshot(person_context, h)
        if snap.get("lord") and snap["lord"] != "unknown":
            house_lords.append(snap["lord"])
            relevant.add(snap["lord"])
    matched = [lord for lord in lords if lord in relevant]
    return {
        "active": bool(matched),
        "current_lords": lords,
        "matched_lords": matched,
        "relevant_house_lords": sorted(set(house_lords)),
    }


def _quality_flags(
    profile: Dict[str, Any],
    native_role: Dict[str, Any],
    native_derived: List[Dict[str, Any]],
    partner_events: List[Dict[str, Any]],
) -> List[str]:
    flags = []
    malefics = {"Saturn", "Rahu", "Ketu", "Mars", "Sun"}
    benefics = {"Jupiter", "Venus", "Moon", "Mercury"}
    if any(m in native_role.get("occupants", []) for m in malefics):
        flags.append("native_role_house_has_malefic_pressure")
    if any(b in native_role.get("occupants", []) for b in benefics):
        flags.append("native_role_house_has_benefic_support")
    if profile.get("event_topic") == "legal_confinement":
        event_occ = [p for snap in [*native_derived, *partner_events] for p in snap.get("occupants", [])]
        if any(p in event_occ for p in ["Saturn", "Rahu", "Ketu", "Mars"]):
            flags.append("legal_event_houses_have_hard_planet_pressure")
    if profile.get("event_topic") == "trust_infidelity":
        event_occ = [p for snap in [*native_derived, *partner_events] for p in snap.get("occupants", [])]
        if any(p in event_occ for p in ["Rahu", "Ketu", "Venus", "Mars"]):
            flags.append("trust_triangle_houses_are_activated")
    return flags


def _trim_divisionals(chart_context: Dict[str, Any], required: List[str]) -> Dict[str, Any]:
    if not required:
        return chart_context
    out = copy.deepcopy(chart_context)
    divs = out.get("divisional_charts")
    if not isinstance(divs, dict):
        return out
    allowed_fragments = {code.lower().replace("d", "") for code in required}
    kept = {}
    for key, value in divs.items():
        key_l = str(key).lower()
        if any(key_l.startswith(f"d{frag}_") or key_l == f"d{frag}" for frag in allowed_fragments):
            kept[key] = value
    if kept:
        out["divisional_charts"] = kept
    return out


def _method_context(method: str, person_context: Dict[str, Any], required_divisionals: List[str]) -> Dict[str, Any]:
    if method == "parashari":
        return _trim_divisionals(build_parashari_slice(person_context), required_divisionals)
    if method == "jaimini":
        return build_jaimini_slice(person_context)
    if method == "nadi":
        return build_nadi_slice(person_context)
    if method == "kp":
        return build_kp_slice(person_context)
    if method == "nakshatra":
        return build_nakshatra_slice(person_context)
    if method == "timing":
        return build_shared_kernel_lite(person_context)
    if method == "ashtakavarga":
        return build_ashtakavarga_slice(person_context)
    if method == "sudarshan":
        return {
            "shared_kernel": build_sudarshan_shared_kernel_lite(person_context),
            "sudarshana_context": build_sudarshan_slice(person_context),
        }
    return build_shared_kernel_lite(person_context)


def build_relational_branch_payloads(context: Dict[str, Any], user_question: str) -> Dict[str, Dict[str, Any]]:
    profile = build_relationship_profile(context, user_question)
    spine = build_relational_evidence_spine(context, user_question)
    native = context.get("native") or {}
    partner = context.get("partner") or {}
    required = profile.get("required_divisionals") or []

    payloads: Dict[str, Dict[str, Any]] = {}
    for method in ("parashari", "jaimini", "nadi", "kp", "nakshatra", "timing", "ashtakavarga", "sudarshan"):
        payloads[f"{method}_relational"] = {
            "relationship": profile,
            "relational_evidence": spine,
            "native": _method_context(method, native, required),
            "partner": _method_context(method, partner, required),
            "user_question": user_question,
        }
    return payloads
