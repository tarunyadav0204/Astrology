"""Canonical policy and deterministic adjudication for Instant Career.

Natural-language classification remains the intent LLM's job.  This module
starts only after the router has returned a structured career subtype; it
prevents individual calculators, evidence views and the answer writer from
using different house matrices or upgrading activity into a promised event.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Tuple


CAREER_ALIASES = {
    "career": "general",
    "career_outlook": "general",
    "yearly_career": "general",
    "career_timing": "general",
    "job": "employment",
    "employment": "employment",
    "job_search": "employment",
    "selection": "employment",
    "private_job": "employment",
    "private_career": "employment",
    "specific_job": "offer",
    "job_offer": "offer",
    "offer": "offer",
    "job_joining": "joining",
    "joining": "joining",
    "promotion": "promotion",
    "authority": "promotion",
    "leadership": "leadership",
    "job_change": "job_change",
    "role_change": "job_change",
    "resignation": "resignation",
    "job_security": "job_security",
    "business": "business",
    "business_launch": "business_launch",
    "business_success": "business_success",
    "project": "project",
    "government": "government",
    "foreign_career": "foreign_career",
    "career_break": "return_to_work",
    "return_to_work": "return_to_work",
    "income": "salary",
    "salary": "salary",
    "salary_growth": "salary",
    "pay_raise": "salary",
    "compensation": "salary",
    "suitable_profession": "career_fit",
    "career_fit": "career_fit",
    "job_vs_business": "job_vs_business",
    "workplace_conflict": "workplace_conflict",
    "career_stagnation": "career_stagnation",
    "recognition": "recognition",
    "professional_recognition": "recognition",
    "lack_of_recognition": "recognition",
    "visibility": "recognition",
    "appraisal": "recognition",
    "manager": "manager_relationship",
    "boss": "manager_relationship",
    "superior": "manager_relationship",
    "supervisor": "manager_relationship",
    "manager_relationship": "manager_relationship",
    "colleague": "colleague_relationship",
    "coworker": "colleague_relationship",
    "peer": "colleague_relationship",
    "colleague_relationship": "colleague_relationship",
    "subordinate": "subordinate_relationship",
    "reportee": "subordinate_relationship",
    "team_member": "subordinate_relationship",
    "subordinate_relationship": "subordinate_relationship",
    "client": "client_relationship",
    "customer": "client_relationship",
    "client_relationship": "client_relationship",
    "business_partner": "business_partner_relationship",
    "business_partner_relationship": "business_partner_relationship",
    "mentor": "mentor_relationship",
    "guide": "mentor_relationship",
    "mentor_relationship": "mentor_relationship",
}


_BASE_PLANETS = ["Sun", "Mercury", "Saturn", "Jupiter"]

CAREER_PROFILES: Dict[str, Dict[str, Any]] = {
    "general": {"houses": [10, 6, 11, 2], "planets": _BASE_PLANETS, "divisionals": ["D1", "D10"]},
    "employment": {"houses": [6, 10, 11, 2], "planets": _BASE_PLANETS, "divisionals": ["D1", "D10"]},
    "offer": {"houses": [2, 6, 10, 11], "planets": ["Mercury", "Sun", "Saturn", "Jupiter"], "divisionals": ["D1", "D10"]},
    "joining": {"houses": [3, 6, 10, 11], "planets": ["Mercury", "Saturn", "Sun", "Mars"], "divisionals": ["D1", "D10"]},
    "promotion": {"houses": [10, 11, 6, 2], "planets": ["Sun", "Saturn", "Jupiter", "Mercury"], "divisionals": ["D1", "D10"]},
    "job_change": {"houses": [2, 3, 6, 8, 10, 11, 12], "planets": ["Rahu", "Saturn", "Mars", "Mercury"], "divisionals": ["D1", "D10"]},
    "resignation": {"houses": [2, 3, 6, 8, 10, 11, 12], "planets": ["Saturn", "Rahu", "Ketu", "Mars"], "divisionals": ["D1", "D10"]},
    "job_security": {"houses": [2, 6, 8, 10, 11, 12], "planets": ["Saturn", "Sun", "Jupiter", "Rahu"], "divisionals": ["D1", "D10"]},
    "business": {"houses": [7, 10, 11, 2], "planets": ["Mercury", "Sun", "Saturn", "Jupiter", "Mars"], "divisionals": ["D1", "D10"]},
    "business_launch": {"houses": [3, 7, 10, 11], "planets": ["Mercury", "Mars", "Sun", "Rahu"], "divisionals": ["D1", "D10"]},
    "business_success": {"houses": [2, 7, 10, 11], "planets": ["Mercury", "Jupiter", "Sun", "Saturn"], "divisionals": ["D1", "D10"]},
    "salary": {"houses": [2, 6, 10, 11], "planets": ["Jupiter", "Mercury", "Venus", "Saturn"], "divisionals": ["D1", "D10"]},
    "project": {"houses": [3, 6, 10, 11], "planets": ["Mars", "Mercury", "Saturn", "Sun"], "divisionals": ["D1", "D10"]},
    "leadership": {"houses": [1, 5, 9, 10], "planets": ["Sun", "Mars", "Jupiter", "Saturn"], "divisionals": ["D1", "D10"]},
    "government": {"houses": [6, 9, 10, 11], "planets": ["Sun", "Saturn", "Mars", "Jupiter"], "divisionals": ["D1", "D10"]},
    "foreign_career": {"houses": [3, 9, 10, 12], "planets": ["Rahu", "Saturn", "Mercury", "Jupiter"], "divisionals": ["D1", "D10"]},
    "return_to_work": {"houses": [3, 6, 10, 11], "planets": ["Saturn", "Mercury", "Sun", "Jupiter"], "divisionals": ["D1", "D10"]},
    "workplace_conflict": {"houses": [6, 8, 10, 12], "planets": ["Mars", "Saturn", "Rahu", "Sun"], "divisionals": ["D1", "D10"]},
    "career_stagnation": {"houses": [6, 8, 10, 11], "planets": ["Saturn", "Rahu", "Sun", "Mercury"], "divisionals": ["D1", "D10"]},
    "recognition": {"houses": [6, 10, 11, 2], "planets": ["Sun", "Saturn", "Jupiter", "Mercury"], "divisionals": ["D1", "D10"]},
    "career_fit": {"houses": [1, 2, 5, 6, 7, 10, 11], "planets": ["Sun", "Moon", "Mercury", "Venus", "Saturn", "Mars", "Jupiter", "Rahu", "Ketu"], "divisionals": ["D1", "D10", "Karkamsa"]},
    "job_vs_business": {"houses": [6, 7, 10, 11], "planets": ["Mercury", "Saturn", "Sun", "Mars", "Jupiter"], "divisionals": ["D1", "D10"]},
    "manager_relationship": {
        "houses": [9, 10, 6, 11], "planets": ["Jupiter", "Sun", "Saturn", "Mercury"], "divisionals": ["D1", "D10"],
        "relationship_target": "manager or reporting authority",
        "house_roles": {9: "manager, mentor and guidance relationship", 10: "authority, hierarchy and reporting line", 6: "daily work, service and friction", 11: "support, recognition and shared professional gains"},
    },
    "colleague_relationship": {
        "houses": [3, 6, 11, 10], "planets": ["Mercury", "Mars", "Saturn"], "divisionals": ["D1", "D10"],
        "relationship_target": "colleague or peer", "house_roles": {3: "coordination and peer communication", 6: "daily work and conflict", 11: "team support and shared goals", 10: "professional roles and accountability"},
    },
    "subordinate_relationship": {
        "houses": [6, 10, 11], "planets": ["Sun", "Saturn", "Mercury", "Mars"], "divisionals": ["D1", "D10"],
        "relationship_target": "team member or direct report", "house_roles": {6: "staff, service and daily execution", 10: "your authority and responsibility", 11: "team results and cooperation"},
    },
    "client_relationship": {
        "houses": [7, 10, 11, 2], "planets": ["Mercury", "Venus", "Jupiter", "Saturn"], "divisionals": ["D1", "D10"],
        "relationship_target": "client or customer", "house_roles": {7: "client counterpart and agreement", 10: "professional delivery and reputation", 11: "repeat support and gains", 2: "fees, value and commercial communication"},
    },
    "business_partner_relationship": {
        "houses": [7, 10, 11, 2], "planets": ["Mercury", "Venus", "Saturn", "Jupiter"], "divisionals": ["D1", "D10"],
        "relationship_target": "business partner", "house_roles": {7: "partnership and contracts", 10: "enterprise responsibility", 11: "shared gains and goals", 2: "shared value and finances"},
    },
    "mentor_relationship": {
        "houses": [9, 5, 10, 11], "planets": ["Jupiter", "Sun", "Mercury"], "divisionals": ["D1", "D10"],
        "relationship_target": "mentor or professional guide", "house_roles": {9: "mentor, guidance and trust", 5: "counsel, learning and judgment", 10: "professional development", 11: "support and opportunity"},
    },
}

CAREER_DECISION_SUBTYPES = frozenset({"job_change", "resignation", "job_security"})
CAREER_VOCATION_SUBTYPES = frozenset({"career_fit", "job_vs_business"})
CAREER_DIAGNOSIS_SUBTYPES = frozenset({"recognition", "career_stagnation", "workplace_conflict"})
CAREER_RELATIONSHIP_SUBTYPES = frozenset({
    "manager_relationship", "colleague_relationship", "subordinate_relationship",
    "client_relationship", "business_partner_relationship", "mentor_relationship",
})
CAREER_TIMING_MODES = frozenset({"timing_window", "event_prediction"})


_SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

_VOCATION_SIGNATURES: Dict[str, Dict[str, List[str]]] = {
    "Sun": {
        "functions": ["leadership and decision-making", "institutional authority"],
        "fields": ["government and administration", "management and leadership", "medicine and public institutions"],
        "environments": ["visible responsibility", "decision-making authority"],
    },
    "Moon": {
        "functions": ["care and public engagement", "adaptive people management"],
        "fields": ["hospitality and public service", "health and care", "psychology and wellbeing"],
        "environments": ["people-facing work", "responsive and changing settings"],
    },
    "Mars": {
        "functions": ["technical execution", "operations and problem-solving"],
        "fields": ["engineering and technology", "operations and manufacturing", "surgery, security and competitive fields"],
        "environments": ["action-oriented work", "ownership of difficult execution"],
    },
    "Mercury": {
        "functions": ["analysis and communication", "commerce and coordination"],
        "fields": ["software, data and analytics", "consulting and communication", "commerce, finance and trade"],
        "environments": ["information-rich work", "multi-stakeholder coordination"],
    },
    "Jupiter": {
        "functions": ["advice and judgment", "teaching and knowledge leadership"],
        "fields": ["education and training", "law, finance and advisory", "consulting and counselling"],
        "environments": ["knowledge-led work", "ethical or advisory responsibility"],
    },
    "Venus": {
        "functions": ["design and value creation", "relationship management"],
        "fields": ["design, media and creative work", "luxury, beauty and lifestyle", "hospitality and relationship-led business"],
        "environments": ["aesthetic or client-facing work", "collaborative settings"],
    },
    "Saturn": {
        "functions": ["systems and process building", "endurance and operational control"],
        "fields": ["infrastructure and engineering", "manufacturing and operations", "compliance, audit and administration"],
        "environments": ["structured organizations", "long-horizon responsibility"],
    },
    "Rahu": {
        "functions": ["innovation and scaling", "research and unconventional problem-solving"],
        "fields": ["technology and digital platforms", "foreign or cross-border business", "research, media and emerging industries"],
        "environments": ["fast-scaling work", "unconventional or international settings"],
    },
    "Ketu": {
        "functions": ["diagnosis and deep specialization", "research and independent analysis"],
        "fields": ["research and specialist technology", "audit, investigation and diagnosis", "healing and esoteric studies"],
        "environments": ["specialist autonomy", "quiet, research-led work"],
    },
}


# Conjunctions to the 10th lord describe *how* the profession is carried out.
# They must be read as combinations, not as unrelated generic planet labels.
# The labels deliberately describe vocational functions/fields rather than a
# guaranteed job title.
_TENTH_LORD_COMBINATIONS: Dict[frozenset[str], Dict[str, List[str]]] = {
    frozenset({"Mars", "Saturn"}): {
        "functions": ["technical systems execution", "engineering and process control"],
        "fields": ["engineering, infrastructure and industrial technology", "technical operations and automation"],
        "environments": ["complex systems with demanding execution", "structured technical organizations"],
    },
    frozenset({"Mars", "Rahu"}): {
        "functions": ["advanced technology and unconventional problem-solving", "automation and rapid technical scaling"],
        "fields": ["AI, software, automation and emerging technology", "digital platforms and technology products"],
        "environments": ["innovative technology environments", "fast-changing or frontier systems"],
    },
    frozenset({"Mercury", "Rahu"}): {
        "functions": ["data-led digital analysis", "software and intelligent-system design"],
        "fields": ["AI, software, data and digital platforms", "analytics, communication technology and automation"],
        "environments": ["information-intensive technology work", "fast-scaling digital environments"],
    },
    frozenset({"Saturn", "Rahu"}): {
        "functions": ["large-scale systems modernization", "technology-enabled process transformation"],
        "fields": ["enterprise technology, infrastructure and automation", "regulated or large-scale digital systems"],
        "environments": ["large complex organizations undergoing change", "high-accountability technology programs"],
    },
    frozenset({"Jupiter", "Mars"}): {
        "functions": ["technical architecture and strategic judgment", "knowledge-led execution"],
        "fields": ["technology consulting and solution architecture", "engineering leadership and technical advisory"],
        "environments": ["knowledge-led technical work", "responsibility for complex decisions"],
    },
}


def _tenth_lord_combination_signature(lord: str, partner: str) -> Dict[str, List[str]]:
    """Return a vocation signature for every possible 10th-lord conjunction.

    Carefully curated combinations above take precedence.  The remaining
    pairs are still interpreted as a *combination* using the 10th lord as the
    principal work function and the conjoined planet as its operating style.
    This gives deterministic coverage for all 36 pairs across the nine grahas
    without pretending that an unreviewed pair has a narrowly guaranteed job
    title.
    """
    pair = frozenset({lord, partner})
    curated = _TENTH_LORD_COMBINATIONS.get(pair)
    if curated:
        return curated

    lord_signature = _VOCATION_SIGNATURES.get(lord) or {}
    partner_signature = _VOCATION_SIGNATURES.get(partner) or {}
    lord_functions = list(lord_signature.get("functions") or [])
    partner_functions = list(partner_signature.get("functions") or [])

    functions: List[str] = []
    for index in range(2):
        principal = lord_functions[index] if index < len(lord_functions) else (lord_functions[0] if lord_functions else "professional responsibility")
        modifier = partner_functions[index] if index < len(partner_functions) else (partner_functions[0] if partner_functions else "specialized execution")
        functions.append(f"{principal} shaped by {modifier}")

    def combined_values(key: str) -> List[str]:
        values: List[str] = []
        for source in (lord_signature, partner_signature):
            for value in source.get(key) or []:
                if value not in values:
                    values.append(value)
                if len(values) >= 3:
                    return values
        return values

    return {
        "functions": functions,
        "fields": combined_values("fields"),
        "environments": combined_values("environments"),
    }


def _planet_name(value: Any) -> str:
    raw = str(value or "").strip().title()
    aliases = {"Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury", "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu"}
    return aliases.get(raw, raw) if aliases.get(raw, raw) in _VOCATION_SIGNATURES else ""


def _chart_planets(chart: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(chart, Mapping):
        return {}
    # Calculators and evidence builders use a few harmless wrappers.  Career
    # synthesis must read the actual calculated placements instead of becoming
    # generic merely because a caller passed one of those wrapper shapes.
    payload: Mapping[str, Any] = chart
    for key in ("calculated_chart", "divisional_chart", "chart"):
        nested = payload.get(key)
        if isinstance(nested, Mapping):
            payload = nested
            break
    planets = payload.get("planets")
    if not isinstance(planets, Mapping):
        return {}
    return {
        name: dict(value)
        for key, value in planets.items()
        if (name := _planet_name(key)) and isinstance(value, Mapping)
    }


def _chart_ascendant_index(chart: Any) -> int | None:
    if not isinstance(chart, Mapping):
        return None
    payload: Mapping[str, Any] = chart
    for key in ("calculated_chart", "divisional_chart", "chart"):
        nested = payload.get(key)
        if isinstance(nested, Mapping):
            payload = nested
            break
    value = payload.get("ascendant_sign")
    if isinstance(value, (int, float)):
        number = int(value)
        return number if 0 <= number <= 11 else ((number - 1) % 12 if 1 <= number <= 12 else None)
    names = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    lagna = payload.get("lagna") if isinstance(payload.get("lagna"), Mapping) else {}
    normalized = str(
        value
        or payload.get("lagna_sign")
        or lagna.get("sign")
        or lagna.get("sign_name")
        or ""
    ).strip().lower()
    return names.index(normalized) if normalized in names else None


def _house_lord(chart: Any, house: int) -> str:
    ascendant = _chart_ascendant_index(chart)
    return _SIGN_LORDS[(ascendant + house - 1) % 12] if ascendant is not None else ""


def _add_signal(scores: Dict[str, float], reasons: Dict[str, List[str]], planet: Any, weight: float, reason: str) -> None:
    name = _planet_name(planet)
    if not name:
        return
    scores[name] += weight
    if reason not in reasons[name]:
        reasons[name].append(reason)


def _score_chart_layer(
    scores: Dict[str, float],
    reasons: Dict[str, List[str]],
    chart: Any,
    label: str,
    house_weights: Mapping[int, Tuple[float, float]],
) -> None:
    planets = _chart_planets(chart)
    for house, (lord_weight, occupant_weight) in house_weights.items():
        lord = _house_lord(chart, house)
        _add_signal(scores, reasons, lord, lord_weight, f"{label} House {house} lord")
        for planet, placement in planets.items():
            if int(placement.get("house") or 0) == house:
                _add_signal(scores, reasons, planet, occupant_weight, f"{planet} occupies {label} House {house}")


def _d1_tenth_lord_cluster(d1_houses: Any, d1_chart: Any) -> Dict[str, Any]:
    """Return the D1 10th lord and planets conjoined with it.

    The validated house audit is preferred because it explicitly carries the
    lord's placement.  The calculated chart supplies the same facts when the
    audit route is absent.  Same-house co-occupation is the bounded Vedic
    conjunction fact used by the current chart/evidence system.
    """
    rows = [row for row in d1_houses if isinstance(row, Mapping)] if isinstance(d1_houses, list) else []
    by_house = {int(row.get("house") or 0): row for row in rows}
    tenth_row = by_house.get(10) or {}
    lord = _planet_name(tenth_row.get("lord")) or _house_lord(d1_chart, 10)
    planets = _chart_planets(d1_chart)
    placement_house = int(tenth_row.get("lord_placement_house") or 0)
    if not placement_house and lord and isinstance(planets.get(lord), Mapping):
        placement_house = int(planets[lord].get("house") or 0)

    occupants: List[str] = []
    placement_row = by_house.get(placement_house) or {}
    for value in placement_row.get("occupants") or []:
        name = _planet_name(value)
        if name and name not in occupants:
            occupants.append(name)
    for planet, placement in planets.items():
        if placement_house and int(placement.get("house") or 0) == placement_house and planet not in occupants:
            occupants.append(planet)
    conjunct = [planet for planet in occupants if planet != lord]
    return {
        "planet": lord,
        "house": placement_house or None,
        "conjunct_planets": conjunct,
    } if lord else {}


def build_vocation_synthesis(
    *,
    d1_houses: Any,
    d1_chart: Any = None,
    d10_chart: Any,
    amatyakaraka: Any,
    karakamsha_chart: Any,
    planetary_strengths: Any = None,
) -> Dict[str, Any]:
    """Cross-chart vocation scorer used by Instant Career Fit.

    It ranks repeated *functions* before industries.  Shadbala/dignity can
    slightly qualify an already-established signature, but cannot create one.
    """
    scores: Dict[str, float] = defaultdict(float)
    reasons: Dict[str, List[str]] = defaultdict(list)

    d1_weights = {1: (2.0, 2.0), 2: (1.0, 1.0), 5: (2.0, 1.5), 6: (2.0, 1.5), 7: (1.5, 1.5), 10: (6.0, 5.0), 11: (1.5, 1.5)}
    supplied_d1_rows = [row for row in d1_houses if isinstance(row, Mapping)] if isinstance(d1_houses, list) else []
    supplied_d1_house_numbers = {int(row.get("house") or 0) for row in supplied_d1_rows}
    for row in supplied_d1_rows:
        if not isinstance(row, Mapping):
            continue
        house = int(row.get("house") or 0)
        if house not in d1_weights:
            continue
        lord_weight, occupant_weight = d1_weights[house]
        _add_signal(scores, reasons, row.get("lord"), lord_weight, f"D1 House {house} lord")
        for planet in row.get("occupants") or []:
            _add_signal(scores, reasons, planet, occupant_weight, f"{_planet_name(planet) or planet} occupies D1 House {house}")
        if house == 10:
            for planet in row.get("aspects") or []:
                _add_signal(scores, reasons, planet, 2.0, f"{_planet_name(planet) or planet} influences D1 House 10")

    # The validated natal audit is preferred because it includes aspects, but
    # it is optional in several Instant routes.  Score any missing D1 houses
    # from the authoritative calculated chart so a vocation answer can never
    # silently collapse to Amatyakaraka-only prose.
    missing_d1_weights = {
        house: weights for house, weights in d1_weights.items()
        if house not in supplied_d1_house_numbers
    }
    if missing_d1_weights:
        _score_chart_layer(scores, reasons, d1_chart, "D1", missing_d1_weights)

    _score_chart_layer(scores, reasons, d10_chart, "D10", {1: (4.0, 3.0), 6: (2.0, 2.0), 7: (2.0, 2.0), 10: (8.0, 7.0), 11: (2.0, 2.0)})
    _score_chart_layer(scores, reasons, karakamsha_chart, "Karakamsha", {1: (3.0, 2.0), 5: (2.0, 2.0), 9: (2.0, 2.0), 10: (6.0, 6.0)})

    amk = amatyakaraka.get("planet") if isinstance(amatyakaraka, Mapping) else amatyakaraka
    _add_signal(scores, reasons, amk, 8.0, f"{_planet_name(amk) or amk} is Amatyakaraka")

    tenth_lord_signature = _d1_tenth_lord_cluster(supplied_d1_rows, d1_chart)
    tenth_lord = tenth_lord_signature.get("planet")
    tenth_lord_house = tenth_lord_signature.get("house")
    for planet in tenth_lord_signature.get("conjunct_planets") or []:
        _add_signal(
            scores,
            reasons,
            planet,
            4.5,
            f"{planet} is conjunct D1 House 10 lord {tenth_lord} in House {tenth_lord_house}",
        )

    # Strength is deliberately capped at a small qualifier. It cannot turn a
    # planet with no D1/D10/Jaimini support into the vocation verdict.
    strength_rows = planetary_strengths if isinstance(planetary_strengths, Mapping) else {}
    for planet, base_score in list(scores.items()):
        strength = strength_rows.get(planet)
        if isinstance(strength, Mapping):
            grade = str(
                strength.get("shadbala_grade")
                or strength.get("strength_grade")
                or strength.get("grade")
                or ""
            ).lower()
            modifier = 1.12 if grade in {"excellent", "very strong"} else 1.06 if grade in {"good", "strong"} else 0.94 if grade in {"weak", "poor"} else 1.0
            scores[planet] = base_score * modifier

    ranked_planets = sorted(scores, key=lambda planet: (-scores[planet], planet))
    function_scores: Dict[str, float] = defaultdict(float)
    field_scores: Dict[str, float] = defaultdict(float)
    environment_scores: Dict[str, float] = defaultdict(float)
    supporters: Dict[str, List[str]] = defaultdict(list)
    for planet in ranked_planets:
        signature = _VOCATION_SIGNATURES[planet]
        for key, target in (("functions", function_scores), ("fields", field_scores), ("environments", environment_scores)):
            for rank, label in enumerate(signature[key]):
                target[label] += scores[planet] * (1.0 if rank == 0 else 0.72)
                if planet not in supporters[label]:
                    supporters[label].append(planet)

    combination_rows: List[Dict[str, Any]] = []
    tenth_lord_cluster = {tenth_lord, *(tenth_lord_signature.get("conjunct_planets") or [])} - {None, ""}
    for partner in sorted(tenth_lord_cluster - {tenth_lord}):
        planets = frozenset({tenth_lord, partner})
        if len(planets) != 2:
            continue
        signature = _tenth_lord_combination_signature(tenth_lord, partner)
        # A conjunction to the 10th lord is more specific than either
        # planet's generic vocabulary.  Boost its combined function enough to
        # control the career-fit verdict without erasing independent D10 and
        # Jaimini confirmation.
        boost = 18.0 if planets in _TENTH_LORD_COMBINATIONS else 12.0
        planet_names = sorted(planets)
        for key, target in (("functions", function_scores), ("fields", field_scores), ("environments", environment_scores)):
            for rank, label in enumerate(signature[key]):
                target[label] += boost * (1.0 if rank == 0 else 0.72)
                for planet in planet_names:
                    if planet not in supporters[label]:
                        supporters[label].append(planet)
        combination_rows.append({
            "planets": planet_names,
            "source": f"conjunction with D1 House 10 lord {tenth_lord} in House {tenth_lord_house}",
            "work_functions": list(signature["functions"]),
            "fields": list(signature["fields"]),
            "environments": list(signature["environments"]),
        })

    def ranked_rows(values: Mapping[str, float], limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                # Keep ``field`` for older prompt/evidence consumers while
                # ``name`` is the common key used by functions/environments.
                "field": name,
                "score": round(score, 1),
                "supporting_planets": supporters[name][:3],
            }
            for name, score in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]
        ]

    # Employment/business is independently assessed from the actual 6th and
    # 7th-house signatures, rather than inferred from a generic planet label.
    d1_by_house = {int(row.get("house") or 0): row for row in supplied_d1_rows}
    d1_planets = _chart_planets(d1_chart)
    d10_planets = _chart_planets(d10_chart)
    employment = 0.0
    business = 0.0
    structure_reasons: List[str] = []
    for house, target, label in ((6, "employment", "service/employment"), (7, "business", "clients/business")):
        row = d1_by_house.get(house) or {}
        value = 2.0 if row.get("lord") else 0.0
        value += 1.5 * len(row.get("occupants") or [])
        if not row:
            value += 2.0 if _house_lord(d1_chart, house) else 0.0
            value += 1.5 * sum(
                1 for placement in d1_planets.values()
                if int(placement.get("house") or 0) == house
            )
        d10_hits = sum(1 for placement in d10_planets.values() if int(placement.get("house") or 0) == house)
        value += 2.0 * d10_hits
        if target == "employment":
            employment = value
        else:
            business = value
        if value:
            structure_reasons.append(f"Houses linked to {label} repeat across D1/D10" if d10_hits else f"D1 contains a {label} signature")
    if max(employment, business) == 0 or abs(employment - business) <= max(employment, business) * 0.2:
        inclination = "hybrid or role-dependent"
    else:
        inclination = "job / structured employment" if employment > business else "business / client-led work"

    layer_count = sum(bool(value) for value in (
        supplied_d1_rows or _chart_planets(d1_chart),
        _chart_planets(d10_chart),
        amk,
        _chart_planets(karakamsha_chart),
    ))
    return {
        "source": "deterministic_cross_chart_vocation_synthesis",
        "method": "Repeated D1, D10, Amatyakaraka and Karakamsha signatures; strength only qualifies established signals.",
        "ranked_planets": [
            # These are compact calculation explanations, not an unrestricted
            # chart dump. Preserve enough rows to show all four independent
            # layers, especially Amatyakaraka which is deliberately added
            # after D1, D10 and Karakamsha scoring.
            {"planet": planet, "score": round(scores[planet], 1), "reasons": reasons[planet][:12]}
            # Keep every scored vocation planet. A 10th-lord conjunction can
            # contain four or more planets; truncating this list hid Rahu (and
            # therefore the technology/AI rationale) even though it affected
            # the deterministic field ranking.
            for planet in ranked_planets
        ],
        "tenth_lord_signature": {
            **tenth_lord_signature,
            "interpretation": (
                "Read the 10th lord together with its conjunction cluster as the primary D1 vocation signature; "
                "do not reduce the joined planets to generic occupants of the placement house."
            ),
        } if tenth_lord_signature else {},
        "combination_signatures": combination_rows,
        "primary_work_functions": ranked_rows(function_scores, 3),
        "suitable_fields": ranked_rows(field_scores, 3),
        "preferred_environments": ranked_rows(environment_scores, 3),
        "work_structure": {
            "inclination": inclination,
            "employment_score": round(employment, 1),
            "business_score": round(business, 1),
            "reasons": structure_reasons[:3],
        },
        "visibility_style": (
            "visible leadership" if ranked_planets and ranked_planets[0] in {"Sun", "Mars"}
            else "client and communication facing" if ranked_planets and ranked_planets[0] in {"Mercury", "Venus", "Moon"}
            else "specialist or systems-led" if ranked_planets and ranked_planets[0] in {"Saturn", "Ketu"}
            else "knowledge and advisory led"
        ),
        "confidence": "high" if layer_count >= 3 else "medium" if layer_count >= 2 else "limited",
        "limitations": [] if layer_count >= 3 else ["Fewer than three independent vocation layers were available."],
    }


def is_career_category(category: Any) -> bool:
    key = str(category or "").strip().lower().replace("-", "_").replace(" ", "_")
    # ``general`` is a valid subtype *inside* the career domain, but it is also
    # the global router's catch-all category.  Treating it as a career category
    # rewrites unrelated personality/day/general answers with the career
    # contract.  A routed career request arrives as ``career`` (or another
    # explicit alias/profile); only that explicit domain signal may opt in.
    return key != "general" and (key in CAREER_PROFILES or key in CAREER_ALIASES)


def normalize_career_subtype(category: Any, routed_subtype: Any = None) -> str:
    """Normalize structured router output; never infer semantics from question text."""
    for candidate in (routed_subtype, category):
        key = str(candidate or "").strip().lower().replace("-", "_").replace(" ", "_")
        if key in CAREER_PROFILES:
            return key
        if key in CAREER_ALIASES:
            return CAREER_ALIASES[key]
    return "general"


def career_profile(category: Any, routed_subtype: Any = None) -> Dict[str, Any]:
    subtype = normalize_career_subtype(category, routed_subtype)
    return {"subtype": subtype, **CAREER_PROFILES[subtype]}


def is_career_decision(category: Any, routed_subtype: Any = None) -> bool:
    return normalize_career_subtype(category, routed_subtype) in CAREER_DECISION_SUBTYPES


def is_career_relationship(category: Any, routed_subtype: Any = None) -> bool:
    return normalize_career_subtype(category, routed_subtype) in CAREER_RELATIONSHIP_SUBTYPES


def is_static_career_profile(
    category: Any,
    routed_subtype: Any = None,
    *,
    answer_mode: Any = None,
) -> bool:
    """Keep vocation/profile readings separate from present-tense job decisions."""
    if not is_career_category(category):
        return False
    subtype = normalize_career_subtype(category, routed_subtype)
    if subtype in CAREER_DECISION_SUBTYPES or subtype in CAREER_DIAGNOSIS_SUBTYPES or subtype in CAREER_RELATIONSHIP_SUBTYPES:
        return False
    return subtype in CAREER_VOCATION_SUBTYPES or (
        subtype == "general" and str(answer_mode or "") in {
        "topic_reading", "potential_capacity"
        }
    )


def career_question_family(answer_mode: Any, subtype: Any) -> str:
    """Resolve the evidence contract after LLM routing, without reading user text."""
    normalized = normalize_career_subtype("career", subtype)
    mode = str(answer_mode or "topic_reading")
    if mode == "remedy_action":
        return "remedy"
    if normalized in CAREER_DECISION_SUBTYPES:
        return "decision"
    if normalized in CAREER_RELATIONSHIP_SUBTYPES:
        return "relationship"
    if mode in CAREER_TIMING_MODES:
        return "timing"
    if mode == "comparison_choice":
        return "comparison"
    if mode == "problem_diagnosis" or normalized in CAREER_DIAGNOSIS_SUBTYPES:
        return "diagnosis"
    if normalized in CAREER_VOCATION_SUBTYPES:
        return "vocation"
    return "profile"


def normalize_career_houses(houses: Iterable[Any]) -> List[int]:
    """Return house numbers from calculator, derivation, or persisted UI shapes.

    Timing rows initially contain integers, while the readable derivation turns
    them into ``{"house": 10, "meaning": ...}`` records.  Career adjudication
    must accept both shapes or every decision gate silently evaluates false.
    """
    normalized = set()
    pending = list(houses or [])
    while pending:
        value = pending.pop(0)
        if isinstance(value, dict):
            direct = next(
                (value.get(key) for key in ("house", "house_number", "number", "h")
                 if value.get(key) is not None),
                None,
            )
            if direct is not None:
                pending.append(direct)
            for key in ("activated_focus_houses", "activated_houses", "supporting_houses", "houses"):
                nested = value.get(key)
                if isinstance(nested, (list, tuple, set)):
                    pending.extend(nested)
            continue
        if isinstance(value, (list, tuple, set)):
            pending.extend(value)
            continue
        text = str(value or "").strip()
        if text.isdigit() and 1 <= int(text) <= 12:
            normalized.add(int(text))
    return sorted(normalized)


def classify_career_decision(houses: Iterable[Any]) -> Dict[str, Any]:
    """Adjudicate stay/change/landing separately; never turn pressure into advice."""
    active = set(normalize_career_houses(houses))
    continuity = {6, 10}.issubset(active)
    continuity_strength = continuity and bool(active.intersection({2, 11}))
    change_momentum = {3, 10}.issubset(active)
    separation = {10, 12}.issubset(active)
    transition = change_momentum and separation
    landing = {6, 10, 11}.issubset(active) and 2 in active
    disruption = 8 in active and bool(active.intersection({10, 12}))

    if transition and landing:
        verdict = "planned_transition_supported"
        guidance = "A planned transition is supported, but resign only after the next role or income is secured."
    elif transition or change_momentum:
        verdict = "prepare_do_not_resign"
        guidance = "Change pressure is active, but landing support is incomplete; prepare and apply without resigning yet."
    elif continuity_strength:
        verdict = "stay_for_now"
        guidance = "Current employment has continuity support; stay for now while improving the role or preparing options."
    elif disruption:
        verdict = "instability_not_exit_permission"
        guidance = "Disruption pressure is present, but it is not evidence that resignation will improve the outcome."
    else:
        verdict = "insufficient_decision_evidence"
        guidance = "The available activation does not justify a stay-or-leave conclusion; ask about the concrete problem or offer."

    return {
        "verdict": verdict,
        "guidance": guidance,
        "active_houses": sorted(active),
        "continuity_support": continuity,
        "continuity_strength": continuity_strength,
        "change_momentum": change_momentum,
        "separation_support": separation,
        "landing_support": landing,
        "disruption_pressure": disruption,
        "rules": {
            "continuity": "H6 + H10; H2/H11 strengthen income and gains continuity.",
            "change": "H3 + H10 show an initiated role change; H12 is required for separation.",
            "landing": "H2 + H6 + H10 + H11 support income, employment, role and gains in the next position.",
            "disruption": "H8 can show restructuring or forced pressure; it never proves that leaving is beneficial.",
        },
    }


def classify_manifestations(houses: Iterable[Any], subtype: Any = None) -> List[Dict[str, Any]]:
    """Turn a calculator's activated houses into bounded, non-guaranteed outcomes."""
    active = {int(h) for h in houses if str(h).isdigit() and 1 <= int(h) <= 12}
    rules = [
        ({6}, "workload_activity", "More tasks, competition, applications or interviews", "activation"),
        ({10}, "role_visibility", "Role, authority or professional visibility becomes active", "activation"),
        ({10, 11}, "recognition_progress", "Recognition, advancement or goal fulfilment can progress", "formalization"),
        ({2, 10, 11}, "compensation_progress", "Compensation or a materially improved role can be formalized", "formalization"),
        ({3, 6, 10}, "role_change_execution", "A job or role change can move into execution", "execution"),
        ({6, 10, 11}, "employment_joining", "Selection, joining or sustained employment is supported", "execution"),
        ({7, 10, 11}, "business_growth", "Clients, contracts and business growth can materialize", "formalization"),
        ({6, 10}, "professional_stability", "Work routines and role responsibilities can stabilize", "stabilization"),
        ({8, 10, 12}, "career_exit_pressure", "Restructuring, exit or disruption pressure is active", "pressure"),
    ]
    normalized_subtype = normalize_career_subtype("career", subtype)
    pressure_houses = sorted(active.intersection({8, 12}))
    out = []
    for required, code, label, stage in rules:
        if required.issubset(active):
            out.append({
                "code": code,
                "label": label,
                "stage": stage,
                "supporting_houses": sorted(required),
                "obstructing_houses": pressure_houses,
                "confidence": "high" if len(required) >= 3 else "medium",
                "career_subtype": normalized_subtype,
                "certainty_rule": "Activation permits this manifestation; it does not guarantee the event.",
            })
    return out


def answer_contract(answer_mode: Any, subtype: str) -> Dict[str, Any]:
    mode = str(answer_mode or "topic_reading")
    family = career_question_family(mode, subtype)
    shapes = {
        "topic_reading": "Direct overall career verdict -> Concrete lived work pattern -> D1/D10 professional signature -> Amatyakaraka and Karkamsa vocation signature -> strongest support and pressure -> natural follow-up",
        "potential_capacity": "Best work function -> up to three suitable fields -> preferred environment -> job/business/hybrid inclination -> what to avoid -> natural follow-up",
        "timing_window": "Plain-language year verdict -> chronological career phases in the requested period -> Concrete likely outcomes -> strongest future window -> caution -> At most one compact astrological reason -> natural follow-up",
        "event_prediction": "Possibility -> ranked windows in the next 3 years -> activity/interview window -> formalization/offer window -> joining/execution window -> stabilization -> Support vs obstruction vs uncertainty -> confidence -> natural follow-up",
        "problem_diagnosis": "Primary cause of the career problem -> secondary drag -> what changes the pattern -> practical next move -> natural follow-up",
        "comparison_choice": "Compare both options -> stronger fit and why -> risk of each -> recommendation -> natural follow-up",
        "remedy_action": "One-sentence career pressure -> exactly three calculated remedies with action, frequency and astrological reason -> practicality caution -> natural follow-up",
    }
    decision = family == "decision"
    diagnosis_shape = (
        "Direct explanation of why effort is not becoming recognition -> H6 effort versus H10 visibility versus H11 reward, with H2 only for compensation -> natal D1/D10 cause -> verified current activation only if supplied -> practical visibility move -> natural follow-up"
        if subtype == "recognition"
        else shapes["problem_diagnosis"]
    )
    relationship_shape = (
        "Direct outlook for the named workplace relationship -> how the role-specific relationship houses interact -> "
        "strongest support -> likely friction -> how the dynamic can develop -> one practical communication or boundary step -> natural follow-up. "
        "Do not replace this with profession fit, generic career identity, Amatyakaraka, Karakamsha or dated timing unless the user explicitly asks when."
    )
    return {
        "subtype": subtype,
        "mandatory_foundation": ["D1", "D10"],
        "required_shape": (
            "Direct stay/change verdict -> continuity evidence -> change/separation evidence -> next-role landing support -> condition and practical next step -> natural follow-up"
            if decision else relationship_shape if family == "relationship" else diagnosis_shape if family == "diagnosis" else shapes.get(mode, shapes["topic_reading"])
        ),
        "question_family": family,
        "allow_current_activation": family in {"diagnosis", "decision", "timing"},
        "allow_future_windows": family == "timing",
        "allow_dated_timing": family == "timing",
        "required_evidence": {
            "profile": ["D1", "D10", "Amatyakaraka", "Karakamsha"],
            "vocation": ["D1", "D10", "Amatyakaraka", "Karakamsha", "vocation_synthesis"],
            "diagnosis": ["D1", "D10", "current_dasha_activation", "current_transit_activation"],
            "decision": ["D1", "D10", "current_dasha_activation", "current_transit_activation"],
            "timing": ["D1", "D10", "dasha_windows", "transit_confirmation"],
            "comparison": ["D1", "D10", "option_specific_factors"],
            "remedy": ["D1", "D10", "remedy_blueprint"],
            "relationship": ["D1_role_houses", "D10_role_confirmation", "role_specific_planets"],
        }[family],
        "forbidden_evidence": (
            ["future_dates", "future_peaks", "ranked_windows", "calendar_forecast"]
            if family != "timing" else []
        ),
        "career_not_wealth_rule": "Answer role, work and professional outcome first. House 2 may explain compensation only; it must never replace the career answer.",
        "event_certainty_rule": "Keep activity, formalization, execution and stabilization distinct. Never turn activation alone into a guaranteed offer, promotion or joining.",
        "fit_rule": (
            "For career-fit questions, the supplied deterministic vocation_synthesis is the controlling source. "
            "State the person's strongest work functions first, then no more than three suitable fields, the "
            "preferred work environment, and job/business/hybrid inclination. Explain the repeated D1, D10, "
            "Amatyakaraka and Karakamsha signatures behind the result. Never infer a profession from the strongest "
            "Shadbala planet, one placement, or a generic planet-to-career list. Only name fields and work "
            "environments present in vocation_synthesis; if those ranked arrays are empty, ask one focused "
            "clarification instead of inventing a profession."
        ),
        "decision_rule": (
            "This is a present career decision, not a vocation-fit reading. Compare H6/H10 continuity, H3/H10/H12 change and separation, H2/H6/H10/H11 next-role landing, and H8 disruption separately using current dasha/transit evidence. Never recommend resignation merely because another profession fits better, because the user is dissatisfied, or because H8/H12 is active. Prefer a secured-offer transition; real-world safety overrides astrology."
            if decision else None
        ),
        "static_profile_rule": "For genuine vocation/profile questions only, stay natal. Do not mention dasha, transit, dates, years, peaks or delivery windows. This rule never applies to job-change, resignation or job-security decisions.",
        "diagnosis_rule": (
            "Diagnose the user's stated career problem. Use natal D1/D10 structure and only verified CURRENT dasha/transit activation supplied in the packet. Do not mention a future date, year, peak, or window; timing requires an explicit when-question. If current activation is absent, give a natal-only diagnosis and say the immediate trigger is not established."
            if family == "diagnosis" else None
        ),
        "recognition_rule": (
            "Recognition is a conversion chain: H6 shows effort/service, H10 shows visibility/status, H11 shows recognition/reward, and H2 only adds compensation. H6 without H10/H11 means effort is not converting into visibility or reward; H10 without H11 means responsibility may be visible while reward lags; H10+H11 supports recognition. State only the pattern actually present in supplied evidence."
            if subtype == "recognition" else None
        ),
        "remedy_rule": "For remedy questions, give exactly three calculated, practical remedies. Each must state the action, frequency, and the chart factor it addresses; do not replace remedies with generic discipline advice.",
    }
