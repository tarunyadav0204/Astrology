"""BPHS Chapter 3: Graha-guna-svarupa.

This pack covers every verse in the selected 74-verse witness.  Narrative and
descriptive passages remain searchable doctrine; only rules backed by a
deterministic calculator are executable.  No source wording is copied into the
repository because the pinned volunteer transcription restricts commercial
redistribution.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

from calculators.classical_natural_nature import calculate_natural_nature
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.classical_special_points import ClassicalSpecialPointsCalculator

from ..engine import ClassicalRuleEngine
from ..facts import ClassicalFact, ClassicalFactSet
from ..models import ClassicalRule, PassageGroup, RuleInputUnavailable, SourceProfile


WORK = "Brihat Parashara Hora Shastra"
CHAPTER = 3
CHAPTER_TITLE = "Graha-guna-svarupa (qualities and nature of the grahas)"
SOURCE_PROFILE = "bphs-sanskritdocuments-2023-12-22"
WITNESS_URL = "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par0110.html"
SEVEN_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SIGN_LORDS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
OWN_SIGNS = {
    "Sun": (4,), "Moon": (3,), "Mars": (0, 7), "Mercury": (2, 5),
    "Jupiter": (8, 11), "Venus": (1, 6), "Saturn": (9, 10),
}
MOOLATRIKONA_SIGNS = {
    "Sun": 4, "Moon": 1, "Mars": 0, "Mercury": 5,
    "Jupiter": 8, "Venus": 6, "Saturn": 10,
}
EXALTATION_SIGNS = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}


def _source(start: int, end: Optional[int] = None) -> SourceProfile:
    return SourceProfile(
        key=SOURCE_PROFILE,
        work=WORK,
        chapter=CHAPTER,
        chapter_title=CHAPTER_TITLE,
        verse_start=start,
        verse_end=end or start,
        witness_url=WITNESS_URL,
        witness_policy="external_reference_only_pending_permission",
    )


PASSAGE_GROUPS: Tuple[PassageGroup, ...] = (
    PassageGroup("bphs.3.1-10", 1, 10, "Astronomical and interpretive foundation", "foundation", "Defines grahas, nakshatras, rashis, Lagna and the need for place- and time-correct positions.", False, "catalogued"),
    PassageGroup("bphs.3.11", 11, 11, "Natural benefic and malefic nature", "chart_rule", "Classifies the grahas, with the Moon dependent on phase and Mercury dependent on association.", True, "published", ("BPHS.3.11.NATURAL_NATURE",)),
    PassageGroup("bphs.3.12-15", 12, 15, "Planetary significations and offices", "doctrine_table", "Assigns core significations and social offices to the grahas.", False, "catalogued"),
    PassageGroup("bphs.3.16-30", 16, 30, "Planetary form and temperament", "doctrine_table", "Describes appearance, constitution, gender, element, social class, guna and temperament.", False, "catalogued"),
    PassageGroup("bphs.3.31", 31, 31, "Bodily tissue correspondence", "doctrine_table", "Maps the seven visible grahas to bodily tissues.", False, "catalogued"),
    PassageGroup("bphs.3.32-48", 32, 48, "Objects, time, direction and contextual strength", "doctrine_table", "Records places, periods, tastes, directions, day/night and paksha strength, vegetation and related correspondences.", False, "catalogued"),
    PassageGroup("bphs.3.49-50", 49, 50, "Exaltation and debilitation", "calculation", "Defines exaltation signs and exact exaltation degrees; debilitation is opposite.", True, "published", ("BPHS.3.49-50.DIGNITY",)),
    PassageGroup("bphs.3.51-54", 51, 54, "Moolatrikona and own-sign spans", "calculation", "Defines the moolatrikona portions and remaining own-sign portions for the seven visible grahas.", True, "published", ("BPHS.3.51-54.MOOLATRIKONA",)),
    PassageGroup("bphs.3.55", 55, 55, "Natural friendship", "calculation", "Derives natural friendship from moolatrikona-relative lordships and exaltation lordship.", True, "published", ("BPHS.3.55.NATURAL_FRIENDSHIP",)),
    PassageGroup("bphs.3.56", 56, 56, "Temporary friendship", "calculation", "Planets in the second, third, fourth, tenth, eleventh or twelfth from one another are temporary friends.", True, "published", ("BPHS.3.56.TEMPORARY_FRIENDSHIP",)),
    PassageGroup("bphs.3.57-58", 57, 58, "Fivefold compound friendship", "calculation", "Combines natural and temporary friendship into the fivefold relationship.", True, "published", ("BPHS.3.57-58.COMPOUND_FRIENDSHIP",)),
    PassageGroup("bphs.3.59-60", 59, 60, "Dignity-based result proportions", "interpretive_rule", "States graduated auspicious and adverse result proportions by dignity.", False, "catalogued"),
    PassageGroup("bphs.3.61-65", 61, 65, "Solar upagrahas", "calculation", "Calculates Dhuma, Vyatipata, Parivesha, Indrachapa and Upaketu from the Sun.", True, "published", ("BPHS.3.61-65.SOLAR_UPAGRAHAS",)),
    PassageGroup("bphs.3.66-70", 66, 70, "Time upagrahas and Gulika", "calculation", "Divides the local day or night into eight portions and derives the applicable ascendants, including Gulika.", True, "published", ("BPHS.3.66-70.TIME_UPAGRAHAS",)),
    PassageGroup("bphs.3.71-74", 71, 74, "Pranapada", "calculation", "Calculates Pranapada from elapsed vighatis and the Sun and classifies its natal house.", True, "published", ("BPHS.3.71-74.PRANAPADA",)),
)


PLANETARY_DOCTRINE = {
    "core_signification": {
        "Sun": "self/soul", "Moon": "mind", "Mars": "strength and initiative",
        "Mercury": "speech", "Jupiter": "knowledge and happiness",
        "Venus": "reproductive vitality", "Saturn": "sorrow and hardship",
    },
    "office": {
        "Sun": "king", "Moon": "king", "Mars": "leader", "Mercury": "prince",
        "Jupiter": "minister", "Venus": "minister", "Saturn": "servant",
        "Rahu": "army", "Ketu": "army",
    },
    "tissue": {
        "Sun": "bone", "Moon": "blood", "Mars": "marrow", "Mercury": "skin",
        "Jupiter": "fat", "Venus": "reproductive tissue", "Saturn": "sinews",
    },
}


def _chart_planets(chart: Mapping[str, Any]) -> Mapping[str, Any]:
    planets = chart.get("planets")
    if not isinstance(planets, Mapping):
        raise RuleInputUnavailable("D1 chart planets are required")
    return planets


def _nature(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    _chart_planets(chart)
    return {
        "planets": [calculate_natural_nature(dict(chart), planet) for planet in (*SEVEN_PLANETS, "Rahu", "Ketu")],
        "principle": "Moon is phase-dependent; Mercury is conditioned by conjunction; the remaining classifications are fixed.",
    }


def _dignities(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    _chart_planets(chart)
    rows = PlanetaryDignitiesCalculator(dict(chart)).calculate_planetary_dignities()
    return {
        "planets": {
            planet: {
                "planet": planet,
                "sign": row.get("sign"),
                "degree": row.get("degree"),
                "dignity": row.get("dignity"),
            }
            for planet, row in rows.items() if planet in SEVEN_PLANETS
        }
    }


def _moolatrikona(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    evidence = _dignities(chart, None)
    return {
        "planets": {
            planet: {
                "dignity": row.get("dignity"),
                "sign": row.get("sign"),
                "degree": row.get("degree"),
                "is_moolatrikona": row.get("dignity") == "moolatrikona",
            }
            for planet, row in evidence["planets"].items()
        }
    }


def _positions(chart: Mapping[str, Any]) -> Dict[str, int]:
    rows = _chart_planets(chart)
    result: Dict[str, int] = {}
    for planet in SEVEN_PLANETS:
        row = rows.get(planet)
        if not isinstance(row, Mapping):
            raise RuleInputUnavailable(f"D1 chart is missing {planet}")
        try:
            raw_sign = row.get("sign")
            if raw_sign is None:
                raw_sign = float(row["longitude"]) // 30
            result[planet] = int(raw_sign) % 12
        except (KeyError, TypeError, ValueError) as exc:
            raise RuleInputUnavailable(f"D1 chart has no usable sign for {planet}") from exc
    return result


def _natural_friendship(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    _positions(chart)
    matrix = _derived_natural_friendship_matrix()
    return {
        "matrix": matrix,
        "nodes_excluded": True,
        "derivation": "For each Moolatrikona, inspect the lords of its 2nd, 4th, 5th, 8th, 9th and 12th signs and the lord of the graha's exaltation sign. A graha occurring on both the friendly and remaining sides is neutral.",
        "reason": "BPHS 3.55 derives this scheme for the seven visible grahas; node friendships are not added to this rule.",
    }


def _derived_natural_friendship_matrix() -> Dict[str, Dict[str, str]]:
    friend_offsets = {2, 4, 5, 8, 9, 12}
    matrix: Dict[str, Dict[str, str]] = {}
    for planet in SEVEN_PLANETS:
        mt_sign = MOOLATRIKONA_SIGNS[planet]
        friendly_signs = {((mt_sign + offset - 1) % 12) for offset in friend_offsets}
        exaltation_lord = SIGN_LORDS[EXALTATION_SIGNS[planet]]
        matrix[planet] = {}
        for other in SEVEN_PLANETS:
            if other == planet:
                continue
            signs = set(OWN_SIGNS[other])
            has_friendly_sign = bool(signs & friendly_signs) or other == exaltation_lord
            has_other_sign = bool(signs - friendly_signs)
            if has_friendly_sign and has_other_sign:
                relation = "neutral"
            elif has_friendly_sign:
                relation = "friend"
            else:
                relation = "enemy"
            matrix[planet][other] = relation
    return matrix


def _temporary_friendship(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    positions = _positions(chart)
    matrix = {}
    for planet, sign in positions.items():
        matrix[planet] = {}
        for other, other_sign in positions.items():
            if other == planet:
                continue
            distance = ((other_sign - sign) % 12) + 1
            matrix[planet][other] = {
                "relationship": "temporary_friend" if distance in {2, 3, 4, 10, 11, 12} else "temporary_enemy",
                "house_distance": distance,
            }
    return {"matrix": matrix, "nodes_excluded": True}


def _compound_friendship(chart: Mapping[str, Any], _: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    positions = _positions(chart)
    natural = _derived_natural_friendship_matrix()

    def compound(planet: str, other: str) -> str:
        distance = ((positions[other] - positions[planet]) % 12) + 1
        temporary_friend = distance in {2, 3, 4, 10, 11, 12}
        relation = natural[planet][other]
        if relation == "friend":
            return "great_friend" if temporary_friend else "neutral"
        if relation == "enemy":
            return "neutral" if temporary_friend else "great_enemy"
        return "friend" if temporary_friend else "enemy"

    return {
        "matrix": {
            planet: {
                other: compound(planet, other)
                for other in SEVEN_PLANETS if other != planet
            }
            for planet in SEVEN_PLANETS
        },
        "nodes_excluded": True,
    }


def _special(chart: Mapping[str, Any], birth: Optional[Mapping[str, Any]]) -> ClassicalSpecialPointsCalculator:
    if not isinstance(birth, Mapping):
        raise RuleInputUnavailable("Birth date, time, latitude, longitude and timezone are required")
    return ClassicalSpecialPointsCalculator(dict(chart), dict(birth))


def _solar_upagrahas(chart: Mapping[str, Any], birth: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    # These five points depend on the natal Sun, not on civil-time inputs.
    return ClassicalSpecialPointsCalculator(dict(chart), dict(birth or {})).solar_upagrahas()


def _time_upagrahas(chart: Mapping[str, Any], birth: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    result = _special(chart, birth).time_upagrahas()
    result["points"] = [row for row in result.get("points", []) if row.get("name") != "Mandi"]
    result["chapter_scope_note"] = "BPHS 3.66–70 names Gulika; the separate Mandi alias is not emitted by this rule."
    return result


def _pranapada(chart: Mapping[str, Any], birth: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    return _special(chart, birth).pranapada()


RULES: Tuple[ClassicalRule, ...] = (
    ClassicalRule("BPHS.3.11.NATURAL_NATURE", "Natural benefic and malefic nature", _source(11), "classification", "natal", "published", "calculators.classical_natural_nature.calculate_natural_nature", _nature, ("planetary_nature",)),
    ClassicalRule("BPHS.3.49-50.DIGNITY", "Exaltation and debilitation", _source(49, 50), "calculation", "natal", "published", "PlanetaryDignitiesCalculator.calculate_planetary_dignities", _dignities, ("dignity",)),
    ClassicalRule("BPHS.3.51-54.MOOLATRIKONA", "Moolatrikona and own-sign spans", _source(51, 54), "calculation", "natal", "published", "PlanetaryDignitiesCalculator.calculate_planetary_dignities", _moolatrikona, ("dignity",)),
    ClassicalRule("BPHS.3.55.NATURAL_FRIENDSHIP", "Natural planetary friendship", _source(55), "calculation", "natal", "published", "classical_rules.bphs.chapter_03._derived_natural_friendship_matrix", _natural_friendship, ("friendship",)),
    ClassicalRule("BPHS.3.56.TEMPORARY_FRIENDSHIP", "Temporary planetary friendship", _source(56), "calculation", "natal", "published", "classical_rules.bphs.chapter_03._temporary_friendship", _temporary_friendship, ("friendship",)),
    ClassicalRule("BPHS.3.57-58.COMPOUND_FRIENDSHIP", "Fivefold planetary friendship", _source(57, 58), "calculation", "natal", "published", "classical_rules.bphs.chapter_03._compound_friendship", _compound_friendship, ("friendship",)),
    ClassicalRule("BPHS.3.61-65.SOLAR_UPAGRAHAS", "Solar upagrahas", _source(61, 65), "calculation", "natal", "published", "ClassicalSpecialPointsCalculator.solar_upagrahas", _solar_upagrahas, ("special_points",)),
    ClassicalRule("BPHS.3.66-70.TIME_UPAGRAHAS", "Time upagrahas and Gulika", _source(66, 70), "calculation", "natal", "published", "ClassicalSpecialPointsCalculator.time_upagrahas", _time_upagrahas, ("special_points",)),
    ClassicalRule("BPHS.3.71-74.PRANAPADA", "Pranapada", _source(71, 74), "calculation", "natal", "published", "ClassicalSpecialPointsCalculator.pranapada", _pranapada, ("special_points",)),
)


def coverage() -> Dict[str, Any]:
    verse_owners: Dict[int, str] = {}
    duplicate_verses = []
    for group in PASSAGE_GROUPS:
        for verse in group.verses():
            if verse in verse_owners:
                duplicate_verses.append(verse)
            verse_owners[verse] = group.key
    missing = [verse for verse in range(1, 75) if verse not in verse_owners]
    executable = sorted({verse for group in PASSAGE_GROUPS if group.executable for verse in group.verses()})
    return {
        "chapter": CHAPTER,
        "total_verses": 74,
        "catalogued_verses": len(verse_owners),
        "executable_verses": len(executable),
        "missing_verses": missing,
        "duplicate_verses": sorted(set(duplicate_verses)),
        "source_profile": SOURCE_PROFILE,
        "source_text_storage": "external_reference_only_pending_permission",
        "published_rules": len([rule for rule in RULES if rule.status == "published"]),
    }


CHAPTER_03 = {
    "work_key": "bphs",
    "work": WORK,
    "chapter": CHAPTER,
    "title": CHAPTER_TITLE,
    "source_profile": SOURCE_PROFILE,
    "witness_url": WITNESS_URL,
    "passage_groups": PASSAGE_GROUPS,
    "planetary_doctrine": PLANETARY_DOCTRINE,
    "rules": RULES,
}


def evaluate_chapter_03(chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    result = ClassicalRuleEngine(RULES).evaluate(chart, birth_data)
    result.update({"work": WORK, "chapter": CHAPTER, "coverage": coverage()})
    return result


# Pack capabilities are declared beside the chapter.  The registry discovers
# this object, so publishing a later chapter does not require another central
# import or evaluation branch.
CHAPTER_03.update({
    "coverage_provider": coverage,
    "evaluator": evaluate_chapter_03,
    "contributes_reading_insights": False,
})


def compile_chapter_03_facts(
    chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None,
) -> ClassicalFactSet:
    """Materialize Chapter 3 outputs once for reuse by later rule packs."""
    evaluated = evaluate_chapter_03(chart, birth_data)
    facts = ClassicalFactSet()

    def add(key: str, value: Any, row: Mapping[str, Any], evidence: Optional[Dict[str, Any]] = None) -> None:
        facts.add(ClassicalFact(
            key=key,
            value=value,
            source_rules=(str(row["rule_key"]),),
            source_references=(str(row["source"]["reference"]),),
            calculator_bindings=(str(row["calculator_binding"]),),
            evidence=evidence or {},
        ))

    for row in evaluated["results"]:
        if row["applicability"] != "matched":
            continue
        rule_key = row["rule_key"]
        evidence = row["evidence"]
        if rule_key == "BPHS.3.11.NATURAL_NATURE":
            for planet in evidence["planets"]:
                add(f"planet.{planet['planet']}.natural_nature", planet["nature"], row, planet)
                if planet.get("phase"):
                    add(f"planet.{planet['planet']}.phase", planet["phase"], row, planet)
        elif rule_key in {"BPHS.3.49-50.DIGNITY", "BPHS.3.51-54.MOOLATRIKONA"}:
            for planet, data in evidence["planets"].items():
                suffix = "dignity" if rule_key.endswith("DIGNITY") else "is_moolatrikona"
                value = data.get("dignity") if suffix == "dignity" else data.get("is_moolatrikona")
                add(f"planet.{planet}.{suffix}", value, row, data)
        elif rule_key.endswith("NATURAL_FRIENDSHIP"):
            for planet, others in evidence["matrix"].items():
                for other, relationship in others.items():
                    add(f"relationship.{planet}.{other}.natural", relationship, row)
        elif rule_key.endswith("TEMPORARY_FRIENDSHIP"):
            for planet, others in evidence["matrix"].items():
                for other, data in others.items():
                    add(f"relationship.{planet}.{other}.temporary", data["relationship"], row, data)
        elif rule_key.endswith("COMPOUND_FRIENDSHIP"):
            for planet, others in evidence["matrix"].items():
                for other, relationship in others.items():
                    add(f"relationship.{planet}.{other}.compound", relationship, row)
        elif rule_key.endswith("SOLAR_UPAGRAHAS") or rule_key.endswith("TIME_UPAGRAHAS"):
            for point in evidence.get("points", []):
                name = str(point["name"])
                for field in ("longitude", "sign", "house"):
                    if point.get(field) is not None:
                        add(f"point.{name}.{field}", point[field], row, point)
        elif rule_key.endswith("PRANAPADA"):
            for field in ("longitude", "sign", "house", "classical_house_classification"):
                if evidence.get(field) is not None:
                    add(f"point.Pranapada.{field}", evidence[field], row, evidence)
    return facts
