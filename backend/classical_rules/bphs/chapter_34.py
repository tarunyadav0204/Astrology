"""BPHS Chapter 34: functional lordship and Yoga Karakas.

The chapter has two distinct layers and this pack keeps them separate:

* verses 2–17 state general rules for functional lordship and Yoga Karakas;
* verses 19–44 give an ascendant-by-ascendant catalogue, including qualified
  yoga and Maraka statements that must not be regularised into a new score.

The long-standing ``classical_functional_nature`` calculator remains the
canonical calculation.  This pack certifies it against the pinned witness,
publishes source-carrying facts for later chapters, and contributes one
readable chart insight without changing any existing calculator fields.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

from calculators.classical_functional_nature import (
    BPHS_ASCENDANT_ROLES,
    KENDRAS,
    PLANETS,
    SIGN_LORDS,
    SIGN_NAMES,
    SPECIAL_TRIKONAS,
    TRIKONAS,
    TRISHADAYA,
    functional_nature_table,
)

from ..facts import ClassicalFact, ClassicalFactSet
from ..models import ClassicalRule, PassageGroup, RuleInputUnavailable, SourceProfile


WORK = "Brihat Parashara Hora Shastra"
CHAPTER = 34
TITLE = "Yoga Karakas and Effects Arising from Lordships"
SOURCE_PROFILE = "bphs-sanskritdocuments-2026-03-19"
WITNESS_URL = "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par3140.html"


def _source(start: int, end: Optional[int] = None) -> SourceProfile:
    return SourceProfile(
        key=SOURCE_PROFILE,
        work=WORK,
        chapter=CHAPTER,
        chapter_title=TITLE,
        verse_start=start,
        verse_end=end or start,
        witness_url=WITNESS_URL,
        witness_policy="external_reference_only",
        numbering_note="Verse numbering follows the SanskritDocuments Chapter 34 witness, which contains 46 verses.",
    )


ASCENDANT_VERSES = {
    0: (19, 22), 1: (23, 24), 2: (25, 26), 3: (27, 28),
    4: (29, 30), 5: (31, 32), 6: (33, 34), 7: (35, 36),
    8: (37, 38), 9: (39, 40), 10: (41, 42), 11: (43, 44),
}
GRAHA_ASPECTS = {
    "Sun": (7,), "Moon": (7,), "Mars": (4, 7, 8), "Mercury": (7,),
    "Jupiter": (5, 7, 9), "Venus": (7,), "Saturn": (3, 7, 10),
}


def _ascendant(chart: Mapping[str, Any]) -> int:
    if not isinstance(chart, Mapping):
        raise RuleInputUnavailable("Chart data is required")
    try:
        # The public chart contract carries sidereal longitude.  Do not pass
        # it through the calculator's dual-purpose sign-or-longitude helper:
        # an exact 0–11 degree value would otherwise be ambiguous with a sign
        # index and could select the wrong Lagna catalogue.
        return int((float(chart["ascendant"]) % 360.0) / 30.0)
    except (KeyError, TypeError, ValueError) as exc:
        raise RuleInputUnavailable("A numeric sidereal ascendant is required") from exc


def _general_lordship(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    ascendant = _ascendant(chart)
    return {
        "applicability": "matched",
        "ascendant_sign": ascendant,
        "ascendant_sign_name": SIGN_NAMES[ascendant],
        "planets": functional_nature_table(ascendant),
        "principle": "General lordship rules are retained separately from the ascendant-specific catalogue.",
    }


def _single_planet_yogakarakas(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    ascendant = _ascendant(chart)
    rows = functional_nature_table(ascendant)
    return {
        "applicability": "matched",
        "ascendant_sign": ascendant,
        "yogakarakas": [planet for planet, row in rows.items() if row["is_yogakaraka"]],
        "planets": {
            planet: {
                "ruled_houses": row["ruled_houses"],
                "is_yogakaraka": row["is_yogakaraka"],
                "derived_reasons": row["derived_reasons"],
            }
            for planet, row in rows.items()
        },
        "control": "Lagna ownership alone does not create the single-planet Yoga Karaka classification; one planet must own House 4, 7 or 10 and House 5 or 9.",
    }


def _planet_signs(chart: Mapping[str, Any], planets: Tuple[str, ...]) -> Dict[str, int]:
    source = chart.get("planets")
    if not isinstance(source, Mapping):
        raise RuleInputUnavailable("Natal planets are required")
    result: Dict[str, int] = {}
    for planet in planets:
        row = source.get(planet)
        if not isinstance(row, Mapping):
            raise RuleInputUnavailable(f"Natal {planet} is required")
        try:
            if row.get("longitude") is not None:
                result[planet] = int((float(row["longitude"]) % 360.0) / 30.0)
            else:
                result[planet] = int(row["sign"]) % 12
        except (KeyError, TypeError, ValueError) as exc:
            raise RuleInputUnavailable(f"Natal {planet} has no usable sign") from exc
    return result


def _aspects(source: str, source_sign: int, target_sign: int) -> bool:
    return any((source_sign + distance - 1) % 12 == target_sign for distance in GRAHA_ASPECTS[source])


def _relationship_yogas(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Evaluate only the four relationships explicitly named in 34.11–12."""
    ascendant = _ascendant(chart)
    signs = _planet_signs(chart, PLANETS)
    roles = functional_nature_table(ascendant)
    matches = []
    for index, first in enumerate(PLANETS):
        for second in PLANETS[index + 1:]:
            first_houses = set(roles[first]["ruled_houses"])
            second_houses = set(roles[second]["ruled_houses"])
            complementary_lordship = (
                bool(first_houses & KENDRAS) and bool(second_houses & SPECIAL_TRIKONAS)
            ) or (
                bool(second_houses & KENDRAS) and bool(first_houses & SPECIAL_TRIKONAS)
            )
            if not complementary_lordship:
                continue
            relationships = []
            if signs[first] == signs[second]:
                relationships.append("conjunction in one sign")
            if SIGN_LORDS[signs[first]] == second and SIGN_LORDS[signs[second]] == first:
                relationships.append("mutual sign exchange")
            elif SIGN_LORDS[signs[first]] == second or SIGN_LORDS[signs[second]] == first:
                relationships.append("one lord's occupation of the other lord's sign")
            if _aspects(first, signs[first], signs[second]) and _aspects(second, signs[second], signs[first]):
                relationships.append("full mutual aspect")
            if not relationships:
                continue
            adverse_ownership_block = bool(first_houses & TRISHADAYA) and bool(second_houses & TRISHADAYA)
            matches.append({
                "planets": [first, second],
                "first_ruled_houses": sorted(first_houses),
                "second_ruled_houses": sorted(second_houses),
                "relationships": relationships,
                "adverse_ownership_block": adverse_ownership_block,
                "forms_yoga": not adverse_ownership_block,
                "control": "Verse 15 blocks relationship alone when both lords also own adverse houses.",
            })
    return {
        "applicability": "matched",
        "ascendant_sign": ascendant,
        "matches": matches,
        "definition": "Only mutual sign exchange, conjunction, one lord occupying the other's sign, and full mutual aspect are tested because these are the relationships named in BPHS 34.11–12.",
    }


def _node_delivery(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Apply the conditioned Rahu/Ketu rules in 34.16–17 without assigning nodes universal lordship."""
    ascendant = _ascendant(chart)
    signs = _planet_signs(chart, (*PLANETS, "Rahu", "Ketu"))
    roles = functional_nature_table(ascendant)
    rows = []
    for node in ("Rahu", "Ketu"):
        node_sign = signs[node]
        node_house = ((node_sign - ascendant) % 12) + 1
        joined = [planet for planet in PLANETS if signs[planet] == node_sign]
        yoga_contacts = []
        relevant_lords = set()
        if node_house in KENDRAS:
            relevant_lords.update(
                planet for planet in PLANETS
                if set(roles[planet]["ruled_houses"]) & SPECIAL_TRIKONAS
            )
        if node_house in TRIKONAS:
            relevant_lords.update(
                planet for planet in PLANETS
                if set(roles[planet]["ruled_houses"]) & {4, 7, 10}
            )
        for planet in PLANETS:
            if planet not in relevant_lords:
                continue
            contact = "joined" if signs[planet] == node_sign else "full aspect" if _aspects(planet, signs[planet], node_sign) else None
            if contact:
                yoga_contacts.append({
                    "planet": planet,
                    "contact": contact,
                    "ruled_houses": roles[planet]["ruled_houses"],
                })
        rows.append({
            "node": node,
            "sign": node_sign,
            "house": node_house,
            "house_lord": SIGN_LORDS[node_sign],
            "joined_planets": joined,
            "delivers_from": {
                "occupied_house": node_house,
                "occupied_sign_lord": SIGN_LORDS[node_sign],
                "joined_planets": joined,
            },
            "is_conditioned_yogakaraka": bool(yoga_contacts),
            "yogakaraka_contacts": yoga_contacts,
        })
    return {
        "applicability": "matched",
        "ascendant_sign": ascendant,
        "nodes": rows,
        "control": "The nodes receive results through occupied house, association and the stated Kendra/Trikona contact; they are not assigned independent sign lordship.",
    }


def _ascendant_catalogue_rule(ascendant: int):
    def evaluator(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        actual = _ascendant(chart)
        if actual != ascendant:
            return {"applicability": "not_matched"}
        return {
            "applicability": "matched",
            "ascendant_sign": actual,
            "ascendant_sign_name": SIGN_NAMES[actual],
            "planets": functional_nature_table(actual),
            "catalogue": BPHS_ASCENDANT_ROLES[actual],
        }
    return evaluator


GENERAL_LORDSHIP_RULE = ClassicalRule(
    "BPHS.34.2-10.FUNCTIONAL_LORDSHIP",
    "Functional results arising from house lordship",
    _source(2, 10),
    "classification",
    "D1 whole-sign ascendant and visible graha lordships",
    "published",
    "calculators.classical_functional_nature.functional_nature_table",
    _general_lordship,
    ("functional_nature", "lordship"),
    ("Natural nature, functional lordship and strength remain separate chart factors.",),
)

YOGAKARAKA_RULE = ClassicalRule(
    "BPHS.34.13-15.SINGLE_PLANET_YOGAKARAKA",
    "Single planet owning a Kendra and a Trikona",
    _source(13, 15),
    "classification",
    "D1 whole-sign lordship",
    "published",
    "calculators.classical_functional_nature.derive_lordship_nature",
    _single_planet_yogakarakas,
    ("yogakaraka", "lordship"),
    ("Kendra ownership alone is not Yoga Karaka status.", "Adverse-house ownership qualifications remain visible."),
)

RELATIONSHIP_YOGA_RULE = ClassicalRule(
    "BPHS.34.11-12.KENDRA_TRIKONA_RELATIONSHIP",
    "Relationship between Kendra and Trikona lords",
    _source(11, 12),
    "yoga_condition",
    "D1 whole-sign lordship, sign occupation and full graha drishti",
    "published",
    "classical_rules.bphs.chapter_34._relationship_yogas",
    _relationship_yogas,
    ("yogakaraka", "planetary_relationship"),
    ("Only the relationships explicitly named in verses 11–12 are evaluated.",),
)

NODE_DELIVERY_RULE = ClassicalRule(
    "BPHS.34.16-17.NODE_DELIVERY",
    "Rahu and Ketu results by placement and association",
    _source(16, 17),
    "conditioned_node_rule",
    "D1 whole-sign placement, conjunction and full graha drishti",
    "published",
    "classical_rules.bphs.chapter_34._node_delivery",
    _node_delivery,
    ("rahu", "ketu", "yogakaraka"),
    ("No independent node lordship or universal node friendship is introduced.",),
)

ASCENDANT_RULES: Tuple[ClassicalRule, ...] = tuple(
    ClassicalRule(
        key=f"BPHS.34.{start}-{end}.{SIGN_NAMES[ascendant].upper()}_CATALOGUE",
        title=f"Functional planetary roles for {SIGN_NAMES[ascendant]} Lagna",
        source=_source(start, end),
        rule_type="ascendant_catalogue",
        scope=f"{SIGN_NAMES[ascendant]} D1 whole-sign ascendant",
        status="published",
        calculator_binding="calculators.classical_functional_nature.functional_nature_table",
        evaluator=_ascendant_catalogue_rule(ascendant),
        topics=("functional_nature", f"lagna_{SIGN_NAMES[ascendant].lower()}"),
        notes=("Qualified, yoga and Maraka statements are preserved as stated; omitted planets are not silently reclassified by this rule.",),
    )
    for ascendant, (start, end) in ASCENDANT_VERSES.items()
)

RULES: Tuple[ClassicalRule, ...] = (
    GENERAL_LORDSHIP_RULE, RELATIONSHIP_YOGA_RULE, YOGAKARAKA_RULE,
    NODE_DELIVERY_RULE, *ASCENDANT_RULES,
)

PASSAGE_GROUPS: Tuple[PassageGroup, ...] = (
    PassageGroup("BPHS.34.1", 1, 1, "Introduction", "foundation", "Introduces results arising from planetary lordships.", False, "catalogued"),
    PassageGroup("BPHS.34.2-7", 2, 7, "General functional lordship", "chart_rule", "Classifies the functional direction of lords of Kendras, Trikonas and adverse houses, including stated exceptions.", True, "published", (GENERAL_LORDSHIP_RULE.key,)),
    PassageGroup("BPHS.34.8-10", 8, 10, "Natural order and Kendradhipati qualification", "interpretive_control", "Orders natural benefic and malefic strength and qualifies the Kendra-lord rule.", True, "published", (GENERAL_LORDSHIP_RULE.key,)),
    PassageGroup("BPHS.34.11-12", 11, 12, "Relationship of Kendra and Trikona lords", "chart_rule", "Tests the relationships explicitly named in the passage: exchange, conjunction, one lord in the other's sign, and full mutual aspect.", True, "published", (RELATIONSHIP_YOGA_RULE.key,)),
    PassageGroup("BPHS.34.13-15", 13, 15, "Single-planet Yoga Karaka and qualifications", "chart_rule", "Identifies a planet owning both a Kendra and a Trikona and preserves the stated exclusions and qualifications.", True, "published", (YOGAKARAKA_RULE.key,)),
    PassageGroup("BPHS.34.16-17", 16, 17, "Rahu and Ketu by association", "chart_rule", "Calculates node delivery from occupied house and conjunction, and the stated Kendra/Trikona lord contact without assigning universal node lordship.", True, "published", (NODE_DELIVERY_RULE.key,)),
    PassageGroup("BPHS.34.18", 18, 18, "Question introducing Lagna-specific roles", "foundation", "Introduces the ascendant-by-ascendant catalogue.", False, "catalogued"),
    *tuple(
        PassageGroup(
            f"BPHS.34.{start}-{end}.{SIGN_NAMES[ascendant].upper()}",
            start,
            end,
            f"Roles for {SIGN_NAMES[ascendant]} Lagna",
            "chart_rule",
            f"Preserves the stated benefic, adverse, neutral, yoga and Maraka qualifications for {SIGN_NAMES[ascendant]} Lagna.",
            True,
            "published",
            (ASCENDANT_RULES[ascendant].key,),
        )
        for ascendant, (start, end) in ASCENDANT_VERSES.items()
    ),
    PassageGroup("BPHS.34.45-46", 45, 46, "Conclusion and scope", "interpretive_control", "Concludes the ascendant-specific catalogue and directs the reader to judge the stated planetary roles in context.", False, "catalogued"),
)


def _source_payload(rule: ClassicalRule) -> Dict[str, Any]:
    return {
        "profile": rule.source.key,
        "work": rule.source.work,
        "chapter": rule.source.chapter,
        "verses": [rule.source.verse_start, rule.source.verse_end],
        "reference": rule.source.reference,
        "witness_url": rule.source.witness_url,
        "rule_key": rule.key,
        "rule_title": rule.title,
        "calculator_binding": rule.calculator_binding,
    }


def _join_planets(planets: list[str]) -> str:
    if not planets:
        return "none"
    if len(planets) == 1:
        return planets[0]
    return f"{', '.join(planets[:-1])} and {planets[-1]}"


def _sentence_fragment(value: Any) -> str:
    return str(value or "").strip().rstrip(".!?;:")


def _readable_maraka_note(value: Any) -> str:
    """Keep the doctrine visible without presenting death as a prediction."""
    text = _sentence_fragment(value)
    lower = text.lower()
    if "independent maraka" in lower:
        return "Maraka capacity is stated as independent; the other adverse planets require association with it"
    if "does not kill independently" in lower or "not independent" in lower:
        return "Maraka capacity is stated, but not as an independent result"
    if "dependent on association" in lower or "according to association" in lower:
        return "Maraka capacity depends on association"
    if "acquires killing" in lower:
        return "Maraka capacity arises under the conditions stated in the passage"
    return "Maraka capacity is stated in the ascendant-specific passage"


def _reading_insight(
    ascendant: int,
    rows: Mapping[str, Mapping[str, Any]],
    relationship_result: Mapping[str, Any],
    node_result: Mapping[str, Any],
) -> Dict[str, Any]:
    catalogue = BPHS_ASCENDANT_ROLES[ascendant]
    benefics = list(catalogue["benefic"])
    malefics = list(catalogue["malefic"])
    neutrals = list(catalogue["neutral"])
    ascendant_rule = ASCENDANT_RULES[ascendant]

    yoga_lines = []
    for planet in PLANETS:
        row = rows[planet]
        if row["is_yogakaraka"]:
            yoga_lines.append(f"{planet} owns Houses {_join_planets([str(house) for house in row['ruled_houses']])} and is the single-planet Yoga Karaka under the general rule")
        if row.get("stated_yoga_note"):
            yoga_lines.append(f"{planet}: {_sentence_fragment(row['stated_yoga_note'])}")
    for match in relationship_result.get("matches") or ():
        if match.get("forms_yoga"):
            yoga_lines.append(
                f"{_join_planets(list(match['planets']))} form a Kendra–Trikona lord relationship through {_join_planets(list(match['relationships']))}"
            )
    for node in node_result.get("nodes") or ():
        if node.get("is_conditioned_yogakaraka"):
            contacts = [f"{row['planet']} ({row['contact']})" for row in node["yogakaraka_contacts"]]
            yoga_lines.append(
                f"{node['node']} in House {node['house']} meets the conditioned node Yoga Karaka rule through {_join_planets(contacts)}"
            )

    maraka_lines = [
        f"Maraka role — {planet}: {_readable_maraka_note(rows[planet]['stated_maraka_note'])}"
        for planet in PLANETS if rows[planet].get("stated_maraka_note")
    ]
    qualification_lines = [
        f"{planet}: {_sentence_fragment(rows[planet]['stated_qualification'])}"
        for planet in PLANETS if rows[planet].get("stated_qualification")
    ]

    supports = [f"{planet}: functionally supportive for {SIGN_NAMES[ascendant]} Lagna" for planet in benefics]
    supports.extend(yoga_lines)
    pressures = [f"{planet}: adverse functional lordship for {SIGN_NAMES[ascendant]} Lagna" for planet in malefics]
    pressures.extend(maraka_lines)

    facts = []
    for planet in PLANETS:
        row = rows[planet]
        detail = f"{row['stated_nature']}; rules Houses {_join_planets([str(house) for house in row['ruled_houses']])}"
        if row["is_yogakaraka"]:
            detail += "; single-planet Yoga Karaka"
        if row.get("stated_qualification"):
            detail += f"; {_sentence_fragment(row['stated_qualification'])}"
        state = "support" if row["stated_nature"] == "benefic" else "pressure" if row["stated_nature"] == "malefic" else "neutral"
        facts.append({
            "key": f"BPHS.34.{SIGN_NAMES[ascendant]}.{planet}.role",
            "label": planet,
            "value": detail,
            "state": state,
        })

    statements = [{
        "key": "premiumUi.planetaryPositions.natalPromise.functionalRoles.summary",
        "text": f"For {SIGN_NAMES[ascendant]} Lagna, the chapter treats {_join_planets(benefics)} as functionally supportive, {_join_planets(malefics)} as adverse, and {_join_planets(neutrals)} as neutral or conditional.",
        "parameters": {
            "lagna": SIGN_NAMES[ascendant],
            "supportive": _join_planets(benefics),
            "adverse": _join_planets(malefics),
            "conditional": _join_planets(neutrals),
        },
    }]
    if yoga_lines:
        statements.append({
            "key": "premiumUi.planetaryPositions.natalPromise.functionalRoles.yoga",
            "text": f"Yoga-giving conditions named for this Lagna: {'; '.join(yoga_lines)}.",
            "parameters": {"details": "; ".join(yoga_lines)},
        })
    if qualification_lines:
        statements.append({
            "key": "premiumUi.planetaryPositions.natalPromise.functionalRoles.qualifications",
            "text": f"The text adds these qualifications: {'; '.join(qualification_lines)}.",
            "parameters": {"details": "; ".join(qualification_lines)},
        })

    return {
        "insight_id": ascendant_rule.key,
        "dedupe_key": "house_1.functional_planetary_roles",
        "area": {
            "key": "house_1", "house": 1, "order": 1,
            "label": "Self and constitution", "label_key": "classical.area.house_1",
        },
        "subject": {
            "key": "functional_planetary_roles",
            "label": "Planetary roles for this Lagna",
            "label_key": "premiumUi.planetaryPositions.natalPromise.subjects.functionalPlanetaryRoles",
        },
        "kind": "chart_foundation",
        "priority": 120,
        "title": f"Planetary roles for {SIGN_NAMES[ascendant]} Lagna",
        "title_key": "premiumUi.planetaryPositions.natalPromise.subjects.functionalPlanetaryRoles",
        "statements": statements,
        "supports": supports,
        "pressures": pressures,
        "evidence": {
            "summary": {
                "key": "premiumUi.planetaryPositions.natalPromise.functionalRoles.evidence",
                "text": f"BPHS Chapter 34 assigns functional roles from {SIGN_NAMES[ascendant]} Lagna and then gives a specific catalogue for this ascendant.",
                "parameters": {"lagna": SIGN_NAMES[ascendant]},
            },
            "facts": facts,
            "raw": {
                "ascendant_sign": ascendant,
                "ascendant_sign_name": SIGN_NAMES[ascendant],
                "planetary_roles": {planet: dict(row) for planet, row in rows.items()},
                "yoga_conditions": yoga_lines,
                "maraka_statements": maraka_lines,
                "relationship_yogas": dict(relationship_result),
                "node_delivery": dict(node_result),
            },
        },
        "sources": [
            _source_payload(GENERAL_LORDSHIP_RULE),
            _source_payload(RELATIONSHIP_YOGA_RULE),
            _source_payload(YOGAKARAKA_RULE),
            _source_payload(NODE_DELIVERY_RULE),
            _source_payload(ascendant_rule),
        ],
        "controls": [{
            "key": "premiumUi.planetaryPositions.natalPromise.functionalRoles.marakaControl",
            "reference": ascendant_rule.source.reference,
            "text": "A Maraka statement identifies a classical capacity under relevant conditions; it is not a standalone event or death prediction.",
            "witness_url": WITNESS_URL,
        }],
    }


def evaluate_chapter_34(chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    del birth_data
    ascendant = _ascendant(chart)
    rows = functional_nature_table(ascendant)
    ascendant_rule = ASCENDANT_RULES[ascendant]
    relationship_result = _relationship_yogas(chart)
    try:
        node_result = _node_delivery(chart)
    except RuleInputUnavailable as exc:
        node_result = {
            "applicability": "unavailable",
            "reason": str(exc),
            "nodes": [],
            "fallback_used": False,
        }
    return {
        "engine_version": "classical-rule-engine/1.0.0",
        "pack_version": "bphs-34/1.0.0",
        "work": WORK,
        "chapter": CHAPTER,
        "title": TITLE,
        "ascendant_sign": ascendant,
        "ascendant_sign_name": SIGN_NAMES[ascendant],
        "method": "D1 whole-sign functional lordship; general rules and the Lagna-specific catalogue are preserved as separate evidence",
        "general_rule": _general_lordship(chart),
        "relationship_yoga_rule": relationship_result,
        "yogakaraka_rule": _single_planet_yogakarakas(chart),
        "node_delivery_rule": node_result,
        "ascendant_catalogue": {
            "rule_key": ascendant_rule.key,
            "source": _source_payload(ascendant_rule),
            "roles": rows,
        },
        "insights": [_reading_insight(ascendant, rows, relationship_result, node_result)],
        "fallback_used": False,
    }


def compile_chapter_34_facts(
    chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None,
) -> ClassicalFactSet:
    """Publish source-carrying functional-role facts for later chapters."""
    del birth_data
    ascendant = _ascendant(chart)
    rows = functional_nature_table(ascendant)
    ascendant_rule = ASCENDANT_RULES[ascendant]
    relationship_result = _relationship_yogas(chart)
    facts = ClassicalFactSet()

    def add(key: str, value: Any, rule: ClassicalRule, evidence: Mapping[str, Any]) -> None:
        facts.add(ClassicalFact(
            key=key,
            value=value,
            source_rules=(rule.key,),
            source_references=(rule.source.reference,),
            calculator_bindings=(rule.calculator_binding,),
            evidence=dict(evidence),
        ))

    add("chart.ascendant.functional_role_catalogue", SIGN_NAMES[ascendant], ascendant_rule, {"ascendant_sign": ascendant})
    add("chart.kendra_trikona_relationship_yogas", list(relationship_result["matches"]), RELATIONSHIP_YOGA_RULE, relationship_result)
    for planet, row in rows.items():
        add(f"planet.{planet}.ruled_houses", list(row["ruled_houses"]), GENERAL_LORDSHIP_RULE, row)
        add(f"planet.{planet}.derived_functional_nature", row["derived_nature"], GENERAL_LORDSHIP_RULE, row)
        add(f"planet.{planet}.is_yogakaraka", bool(row["is_yogakaraka"]), YOGAKARAKA_RULE, row)
        add(f"planet.{planet}.functional_nature", row["stated_nature"], ascendant_rule, row)
        if row.get("stated_qualification"):
            add(f"planet.{planet}.functional_qualification", row["stated_qualification"], ascendant_rule, row)
        if row.get("stated_yoga_note"):
            add(f"planet.{planet}.stated_yoga_condition", row["stated_yoga_note"], ascendant_rule, row)
        if row.get("stated_maraka_note"):
            add(f"planet.{planet}.stated_maraka_role", row["stated_maraka_note"], ascendant_rule, row)
    try:
        node_result = _node_delivery(chart)
    except RuleInputUnavailable:
        node_result = None
    if node_result:
        for node in node_result["nodes"]:
            add(f"planet.{node['node']}.delivery", node["delivers_from"], NODE_DELIVERY_RULE, node)
            add(f"planet.{node['node']}.is_conditioned_yogakaraka", node["is_conditioned_yogakaraka"], NODE_DELIVERY_RULE, node)
    return facts


def coverage() -> Dict[str, Any]:
    verse_owners: Dict[int, str] = {}
    duplicates = []
    for group in PASSAGE_GROUPS:
        for verse in group.verses():
            if verse in verse_owners:
                duplicates.append(verse)
            verse_owners[verse] = group.key
    executable = sorted({verse for group in PASSAGE_GROUPS if group.executable for verse in group.verses()})
    return {
        "chapter": CHAPTER,
        "total_verses": 46,
        "catalogued_verses": len(verse_owners),
        "executable_verses": len(executable),
        "missing_verses": [verse for verse in range(1, 47) if verse not in verse_owners],
        "duplicate_verses": sorted(set(duplicates)),
        "published_rules": len(RULES),
        "ascendant_catalogues": len(ASCENDANT_RULES),
        "source_profile": SOURCE_PROFILE,
    }


CHAPTER_34 = {
    "work_key": "bphs",
    "work": WORK,
    "chapter": CHAPTER,
    "title": TITLE,
    "source_profile": SOURCE_PROFILE,
    "witness_url": WITNESS_URL,
    "passage_groups": PASSAGE_GROUPS,
    "rules": RULES,
    "coverage_provider": coverage,
    "evaluator": evaluate_chapter_34,
    "contributes_reading_insights": True,
}
