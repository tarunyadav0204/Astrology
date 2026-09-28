"""BPHS Chapter 24: deterministic natal results of house lords in houses.

The Sanskrit witness numbers the 144 placements consecutively: verse
``(source house - 1) * 12 + occupied house``.  Verse 145 requires the reader
to judge every result according to strength and weakness; this implementation
therefore exposes condition evidence and never turns the verse into certainty.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

from calculators.classical_natural_nature import calculate_natural_nature
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator

from ..models import ClassicalRule, PassageGroup, RuleInputUnavailable, SourceProfile
from .chapter_24_data import VERSE_OUTCOMES

WORK = "Brihat Parashara Hora Shastra"
CHAPTER = 24
TITLE = "Effects of the Lords of the Houses"
WITNESS_URL = "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par2130.html"
SOURCE_KEY = "bphs-sanskritdocuments-2023-12-22"
SIGN_LORDS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
HOUSE_NAMES = (
    "Self and constitution", "Wealth, family and speech", "Courage, skills and siblings",
    "Home, mother and property", "Children, learning and creativity", "Health, conflict and service",
    "Marriage and partnership", "Longevity, vulnerability and transformation", "Fortune, teachers and dharma",
    "Work, status and responsibility", "Gains, networks and fulfilment", "Expenditure, retreat and release",
)
VISIBLE_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
GRAHA_ASPECTS = {
    "Sun": (7,), "Moon": (7,), "Mars": (4, 7, 8), "Mercury": (7,),
    "Jupiter": (5, 7, 9), "Venus": (7,), "Saturn": (3, 7, 10),
}
STRONG_DIGNITIES = {"exalted", "moolatrikona", "own_sign"}
WEAK_DIGNITIES = {"debilitated"}


def _source(verse: int) -> SourceProfile:
    return SourceProfile(
        SOURCE_KEY, WORK, CHAPTER, TITLE, verse, verse, WITNESS_URL,
        numbering_note="Verse numbering follows the SanskritDocuments Chapter 24 witness; verse 145 qualifies all 144 placement results by strength and weakness.",
    )


def _public_evaluator(source_house: int, occupied_house: int):
    def evaluator(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        context = _chart_context(chart)
        placement = context["placements"][source_house]
        if placement["occupied_house"] != occupied_house:
            return {"applicability": "not_matched"}
        return {"applicability": "matched", **placement}
    return evaluator


def _verse(source_house: int, occupied_house: int) -> int:
    return (source_house - 1) * 12 + occupied_house


def _title(source_house: int, occupied_house: int) -> str:
    return f"Lord of House {source_house} in House {occupied_house}"


RULES: Tuple[ClassicalRule, ...] = tuple(
    ClassicalRule(
        key=f"BPHS.24.{_verse(source_house, occupied_house)}.H{source_house}_LORD_IN_H{occupied_house}",
        title=_title(source_house, occupied_house),
        source=_source(_verse(source_house, occupied_house)),
        rule_type="natal_judgment",
        scope="D1 whole-sign house lord placement",
        status="published",
        calculator_binding="classical_rules.bphs.chapter_24.evaluate_chapter_24",
        evaluator=_public_evaluator(source_house, occupied_house),
        topics=(f"house_{source_house}", "natal_promise"),
        notes=("Apply with the strength-and-weakness instruction in BPHS 24.145.",),
    )
    for source_house in range(1, 13)
    for occupied_house in range(1, 13)
)

PASSAGE_GROUPS = tuple(
    PassageGroup(
        key=f"BPHS.24.H{house}.LORD_PLACEMENTS",
        verse_start=(house - 1) * 12 + 1,
        verse_end=house * 12,
        title=f"Lord of House {house} in the twelve houses",
        classification="natal_judgment",
        operational_summary=f"Twelve placement results concerning {HOUSE_NAMES[house - 1].lower()}.",
        executable=True,
        review_status="published",
        rule_keys=tuple(rule.key for rule in RULES[(house - 1) * 12:house * 12]),
    )
    for house in range(1, 13)
) + (
    PassageGroup(
        key="BPHS.24.145.STRENGTH_QUALIFICATION",
        verse_start=145,
        verse_end=145,
        title="Judge all results by strength and weakness",
        classification="interpretive_control",
        operational_summary="Every placement result must be qualified by the strength and weakness of the relevant house lord.",
        executable=True,
        review_status="published",
        rule_keys=tuple(rule.key for rule in RULES),
    ),
)


def _longitude(row: Mapping[str, Any]) -> Optional[float]:
    try:
        if row.get("longitude") is not None:
            return float(row["longitude"]) % 360.0
        return (int(row["sign"]) % 12) * 30.0 + float(row.get("degree") or 0.0)
    except (KeyError, TypeError, ValueError):
        return None


def _chart_context(chart: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(chart, Mapping):
        raise RuleInputUnavailable("Chart data is required")
    try:
        ascendant = float(chart["ascendant"]) % 360.0
    except (KeyError, TypeError, ValueError) as exc:
        raise RuleInputUnavailable("A numeric sidereal ascendant is required") from exc
    planets = chart.get("planets")
    if not isinstance(planets, Mapping):
        raise RuleInputUnavailable("Natal planets are required")
    ascendant_sign = int(ascendant / 30.0) % 12
    normalized: Dict[str, Dict[str, Any]] = {}
    for planet in VISIBLE_GRAHAS:
        row = planets.get(planet)
        longitude = _longitude(row) if isinstance(row, Mapping) else None
        if longitude is None:
            raise RuleInputUnavailable(f"Natal {planet} longitude is required")
        sign = int(longitude / 30.0) % 12
        normalized[planet] = {
            **dict(row), "longitude": longitude, "sign": sign,
            "house": ((sign - ascendant_sign) % 12) + 1,
        }

    normalized_chart = {**dict(chart), "ascendant": ascendant, "planets": {**dict(planets), **normalized}}
    dignity_rows = PlanetaryDignitiesCalculator(normalized_chart).calculate_planetary_dignities()
    placements: Dict[int, Dict[str, Any]] = {}
    for house in range(1, 13):
        sign = (ascendant_sign + house - 1) % 12
        lord = SIGN_LORDS[sign]
        lord_row = normalized[lord]
        conjunctions = tuple(p for p, row in normalized.items() if p != lord and row["sign"] == lord_row["sign"])
        aspectors = tuple(
            p for p, row in normalized.items()
            if p != lord and any((row["sign"] + distance - 1) % 12 == lord_row["sign"] for distance in GRAHA_ASPECTS[p])
        )
        influences = tuple(dict.fromkeys(conjunctions + aspectors))
        benefics, malefics = [], []
        for planet in influences:
            nature = calculate_natural_nature(normalized_chart, planet)["nature"]
            (benefics if nature == "benefic" else malefics).append(planet)
        dignity = (dignity_rows.get(lord) or {}).get("dignity", "neutral")
        combust = bool(((dignity_rows.get(lord) or {}).get("combustion") or {}).get("is_combust"))
        supports = []
        pressures = []
        if dignity in STRONG_DIGNITIES:
            supports.append(dignity)
        if benefics:
            supports.append(f"benefic influence from {', '.join(benefics)}")
        if dignity in WEAK_DIGNITIES:
            pressures.append(dignity)
        if combust:
            pressures.append("combust")
        if malefics:
            pressures.append(f"malefic influence from {', '.join(malefics)}")
        if supports and pressures:
            condition = "mixed"
        elif supports:
            condition = "supported"
        elif pressures:
            condition = "under_pressure"
        else:
            condition = "unqualified"
        placements[house] = {
            "source_house": house,
            "life_area": HOUSE_NAMES[house - 1],
            "source_sign": sign,
            "lord": lord,
            "occupied_house": lord_row["house"],
            "occupied_sign": lord_row["sign"],
            "lord_condition": {
                "classification": condition,
                "dignity": dignity,
                "combust": combust,
                "retrograde": bool(lord_row.get("retrograde")),
                "conjunctions": list(conjunctions),
                "aspected_by": list(aspectors),
                "benefic_influences": benefics,
                "malefic_influences": malefics,
                "supports": supports,
                "pressures": pressures,
            },
        }
    return {"ascendant_sign": ascendant_sign, "placements": placements, "chart": normalized_chart}


def _qualifications(verse: int, placement: Mapping[str, Any]) -> list[Dict[str, Any]]:
    state = placement["lord_condition"]
    benefic = bool(state["benefic_influences"])
    malefic = bool(state["malefic_influences"])
    conjunctions = set(state["conjunctions"])
    conditions: list[Dict[str, Any]] = []

    def add(label: str, active: bool, evidence: str) -> None:
        conditions.append({"label": label, "active": active, "evidence": evidence})

    if verse in {6, 12}:
        add("Affliction without benefic relief", malefic and not benefic, f"benefic influences: {state['benefic_influences'] or 'none'}; malefic influences: {state['malefic_influences'] or 'none'}")
    if verse == 7:
        add("Strong lord", state["classification"] == "supported", f"condition: {state['classification']}; dignity: {state['dignity']}")
    if verse in {15, 18, 29, 53}:
        add("Benefic association", benefic, f"{state['benefic_influences'] or 'none'}")
        add("Malefic association", malefic, f"{state['malefic_influences'] or 'none'}")
    if verse == 16:
        add("Exalted and joined Jupiter", state["dignity"] == "exalted" and "Jupiter" in conjunctions, f"dignity: {state['dignity']}; conjunctions: {state['conjunctions'] or 'none'}")
    if verse == 19:
        add("Malefic conjunction or aspect", malefic, f"{state['malefic_influences'] or 'none'}")
    if verse == 91:
        joined_malefics = [p for p in state["malefic_influences"] if p in conjunctions]
        add("Joined by a malefic", bool(joined_malefics), f"{joined_malefics or 'none'}")
    if verse == 92:
        add("Lord is strong", state["classification"] == "supported", f"condition: {state['classification']}; dignity: {state['dignity']}")
    if verse == 94:
        benefic_aspects = [p for p in state["benefic_influences"] if p in state["aspected_by"]]
        add("Benefic aspect provides relief", bool(benefic_aspects), f"{benefic_aspects or 'none'}")
    if verse == 95:
        joined_benefics = [p for p in state["benefic_influences"] if p in conjunctions]
        joined_malefics = [p for p in state["malefic_influences"] if p in conjunctions]
        add("Joined by a benefic", bool(joined_benefics), f"{joined_benefics or 'none'}")
        add("Joined by a malefic", bool(joined_malefics), f"{joined_malefics or 'none'}")
    if verse == 96:
        add("Additional malefic influence", malefic, f"{state['malefic_influences'] or 'none'}")
    return conditions


def evaluate_chapter_24(chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    del birth_data
    context = _chart_context(chart)
    matches = []
    for house in range(1, 13):
        placement = context["placements"][house]
        occupied = placement["occupied_house"]
        verse = _verse(house, occupied)
        source = _source(verse)
        match = {
            "rule_key": f"BPHS.24.{verse}.H{house}_LORD_IN_H{occupied}",
            "title": _title(house, occupied),
            "applicability": "matched",
            **placement,
            "outcomes": list(VERSE_OUTCOMES[verse]),
            "qualifications": _qualifications(verse, placement),
            "source": {
                "profile": source.key,
                "work": source.work,
                "chapter": source.chapter,
                "verses": [verse, verse],
                "reference": source.reference,
                "witness_url": source.witness_url,
            },
        }
        matches.append(match)
    return {
        "engine_version": "classical-rule-engine/1.0.0",
        "pack_version": "bphs-24/1.0.0",
        "work": WORK,
        "chapter": CHAPTER,
        "title": TITLE,
        "method": "D1 whole-sign lords; one matched placement for each of the twelve houses",
        "interpretive_control": {
            "reference": "BPHS 24.145",
            "text": "Every result is qualified by the relevant lord's strength and weakness.",
        },
        "ascendant_sign": context["ascendant_sign"],
        "matches": matches,
        "insights": [_reading_insight(row) for row in matches],
        "fallback_used": False,
    }


def _reading_insight(match: Mapping[str, Any]) -> Dict[str, Any]:
    """Publish Chapter 24 through the corpus-wide reading contract.

    The legacy ``matches`` response remains intact.  New product clients use
    these normalized claims and therefore do not need to understand the
    internal response shape of this chapter.
    """
    house = int(match["source_house"])
    rule_key = str(match["rule_key"])
    condition = dict(match["lord_condition"])
    return {
        "insight_id": rule_key,
        "dedupe_key": f"house_{house}.lord_placement",
        "area": {
            "key": f"house_{house}",
            "house": house,
            "order": house,
            "label": str(match["life_area"]),
            "label_key": f"classical.area.house_{house}",
        },
        "subject": {
            "key": "house_lord_placement",
            "label": "House lord placement",
            "label_key": "premiumUi.planetaryPositions.natalPromise.subjects.houseLordPlacement",
        },
        "kind": "natal_promise",
        "priority": 100,
        "title": str(match["life_area"]),
        "title_key": f"classical.area.house_{house}",
        "statements": [
            {
                "key": f"{rule_key}.outcome.{index}",
                "text": str(outcome),
                "parameters": {},
            }
            for index, outcome in enumerate(match.get("outcomes") or (), start=1)
        ],
        "condition": str(condition.get("classification") or "unqualified"),
        "supports": list(condition.get("supports") or ()),
        "pressures": list(condition.get("pressures") or ()),
        "evidence": {
            "summary": {
                "key": f"{rule_key}.evidence.placement",
                "text": f"House {house} lord {match['lord']} is in House {match['occupied_house']}",
                "parameters": {
                    "source_house": house,
                    "lord": match["lord"],
                    "occupied_house": match["occupied_house"],
                },
            },
            "facts": [
                {
                    "key": f"{rule_key}.evidence.dignity",
                    "label": "Dignity",
                    "value": str(condition.get("dignity") or "ordinary").replace("_", " "),
                    "state": "pressure" if condition.get("dignity") in WEAK_DIGNITIES else "support" if condition.get("dignity") in STRONG_DIGNITIES else "neutral",
                },
                *[
                    {
                        "key": f"{rule_key}.qualification.{index}",
                        "label": str(item["label"]),
                        "value": str(item["evidence"]),
                        "state": "support" if item.get("active") else "neutral",
                    }
                    for index, item in enumerate(match.get("qualifications") or (), start=1)
                ],
            ],
            "raw": {
                "placement": {
                "source_house": house,
                "lord": match["lord"],
                "occupied_house": match["occupied_house"],
                "source_sign": match["source_sign"],
                "occupied_sign": match["occupied_sign"],
                },
                "lord_condition": condition,
                "qualifications": list(match.get("qualifications") or ()),
            },
        },
        "sources": [{
            **dict(match["source"]),
            "rule_key": rule_key,
            "rule_title": str(match["title"]),
            "calculator_binding": "classical_rules.bphs.chapter_24.evaluate_chapter_24",
        }],
        "controls": [{
            "key": "BPHS.24.145.STRENGTH_QUALIFICATION",
            "reference": "BPHS 24.145",
            "text": "Every result is qualified by the relevant lord's strength and weakness.",
            "witness_url": WITNESS_URL,
        }],
    }


def coverage() -> Dict[str, Any]:
    verses = [_verse(h, p) for h in range(1, 13) for p in range(1, 13)]
    return {
        "total_verses": 145,
        "catalogued_verses": 145,
        "placement_rules": len(verses),
        "interpretive_controls": 1,
        "missing_verses": [],
        "duplicate_verses": [],
    }


CHAPTER_24 = {
    "work_key": "bphs",
    "work": WORK,
    "chapter": CHAPTER,
    "title": TITLE,
    "source_profile": SOURCE_KEY,
    "witness_url": WITNESS_URL,
    "passage_groups": PASSAGE_GROUPS,
    "rules": RULES,
    "coverage_provider": coverage,
    "evaluator": evaluate_chapter_24,
    "contributes_reading_insights": True,
}
