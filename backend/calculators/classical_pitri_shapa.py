"""Classical Pitṛ-śāpa combinations from BPHS 83.20-30.

This is deliberately narrower than the modern umbrella label "Pitra Dosha".
The selected chapter states eleven combinations in the context of loss of
progeny (suta-kṣaya / santati-nāśana).  A solar affliction, a node in the
ninth, or a pressured ninth lord is therefore never sufficient by itself.

Chapter numbering varies between editions.  The stable citation is the
chapter incipit ``atha pūrvajanmaśāpadyotanādhyāyaḥ`` and verses 20-30; the
Chaukhamba/Devachandra Jha arrangement numbers it chapter 83.
"""

from __future__ import annotations

from typing import Any, Mapping

from .vedic_graha_drishti import planets_aspecting_house_sign


PLANET_ORDER = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
DEBILITATION_SIGNS = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0,
}
UNCONDITIONAL_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
MALEFIC_SIGN_LORDS = frozenset({"Sun", "Mars", "Saturn"})

SOURCE = {
    "work": "Brihat Parashara Hora Shastra",
    "chapter_title": "Purvajanma-shapa-dyotana (indications of curses from a former birth)",
    "chapter_number": "83 in the Chaukhamba/Devachandra Jha arrangement",
    "verse_numbers": "83.20-30",
    "verse_incipit": "putrasthanam gate bhanau ...",
    "reference_label": "Brihat Parashara Hora Shastra, Purvajanma-shapa-dyotana 20-30 (Chaukhamba: 83.20-30)",
    "source_url": "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par8190.html",
    "verse_index_url": "https://vedicpupil.in/library/books/brihat-parashara-hora-shastra/chapter-83",
    "scope": "progeny",
    "stated_result": "suta-kshaya / santati-nashana (loss or absence of progeny)",
    "textual_note": (
        "The chapter number varies by edition. These rules do not define every Sun, ninth-house, "
        "or ninth-lord affliction as Pitri-shapa, and they do not state a Low/Medium/High grading."
    ),
}

RULE_TEXT = {
    "BPHS-PS-20": ("83.20", "putrasthanam gate bhanau", "The debilitated Sun is in House 5, in a Saturn-ruled navamsha, with malefics on both sides."),
    "BPHS-PS-21": ("83.21", "putrasthanadhipe bhanau", "The Sun is the fifth lord, occupies a trine, is joined and aspected by malefics, and is hemmed between malefics."),
    "BPHS-PS-22": ("83.22", "bhanurashisthite jive", "Jupiter is in Leo, the fifth lord joins the Sun, and malefics occupy both Houses 1 and 5."),
    "BPHS-PS-23": ("83.23", "lagneshe durbale putre", "The weak ascendant lord is in House 5, the fifth lord joins the Sun, and malefics occupy Houses 1 and 5."),
    "BPHS-PS-24": ("83.24", "pitristhanadhipe putre", "The ninth lord is in House 5 or the fifth lord is in House 10, while malefics occupy Houses 1 and 5."),
    "BPHS-PS-25": ("83.25", "pitristhanadhipe bhaumah", "Mars is the ninth lord and joins the fifth lord, while malefics occupy Houses 1, 5 and 9."),
    "BPHS-PS-26": ("83.26", "pitristhanadhipe duhsthe", "The ninth lord is in a dusthana, Jupiter is in a sign ruled by a natural malefic, and both the fifth and ascendant lords join malefics."),
    "BPHS-PS-27": ("83.27", "lagnapanchamabhavastha", "Sun, Mars and Saturn occupy Houses 1 and 5, Rahu is in House 8, and Jupiter is in House 12."),
    "BPHS-PS-28": ("83.28", "lagnadashtamage bhanau", "The Sun is in House 8, Saturn is in House 5, the fifth lord joins Rahu, and a malefic occupies House 1."),
    "BPHS-PS-29": ("83.29", "vyayeshe lagnabhavasthe", "The twelfth lord is in House 1, the eighth lord is in House 5, and the ninth lord is in House 8."),
    "BPHS-PS-30": ("83.30", "rogeshe putrabhavasthe", "The sixth lord is in House 5, the ninth lord is in House 6, and Jupiter joins Rahu."),
}


def _normalise_sign(value: Any) -> int | None:
    if value is None:
        return None
    try:
        sign = int(value)
    except (TypeError, ValueError):
        return None
    return sign if 0 <= sign <= 11 else None


def _planet_sign(chart: Mapping[str, Any], planet: str) -> int | None:
    row = ((chart or {}).get("planets") or {}).get(planet) or {}
    sign = _normalise_sign(row.get("sign"))
    if sign is not None:
        return sign
    try:
        return int(float(row["longitude"]) % 360.0 / 30.0)
    except (KeyError, TypeError, ValueError):
        return None


def _planet_longitude(chart: Mapping[str, Any], planet: str) -> float | None:
    row = ((chart or {}).get("planets") or {}).get(planet) or {}
    try:
        return float(row["longitude"]) % 360.0
    except (KeyError, TypeError, ValueError):
        sign = _planet_sign(chart, planet)
        degree = row.get("degree")
        if sign is None or degree is None:
            return None
        try:
            return sign * 30.0 + float(degree)
        except (TypeError, ValueError):
            return None


def _ascendant_sign(chart: Mapping[str, Any]) -> int | None:
    ascendant = (chart or {}).get("ascendant")
    if isinstance(ascendant, Mapping):
        sign = _normalise_sign(ascendant.get("sign"))
        if sign is not None:
            return sign
        ascendant = ascendant.get("longitude")
    try:
        return int(float(ascendant) % 360.0 / 30.0)
    except (TypeError, ValueError):
        houses = (chart or {}).get("houses") or []
        return _normalise_sign((houses[0] or {}).get("sign")) if houses else None


def _house_from_sign(ascendant_sign: int, sign: int) -> int:
    return ((sign - ascendant_sign) % 12) + 1


def _house(chart: Mapping[str, Any], planet: str, ascendant_sign: int) -> int | None:
    sign = _planet_sign(chart, planet)
    return _house_from_sign(ascendant_sign, sign) if sign is not None else None


def _house_lord(ascendant_sign: int, house: int) -> str:
    return SIGN_LORDS[(ascendant_sign + house - 1) % 12]


def _is_waxing_moon(chart: Mapping[str, Any]) -> bool | None:
    sun = _planet_longitude(chart, "Sun")
    moon = _planet_longitude(chart, "Moon")
    if sun is None or moon is None:
        return None
    elongation = (moon - sun) % 360.0
    return 0.0 < elongation <= 180.0


def _malefics(chart: Mapping[str, Any]) -> set[str]:
    planets = (chart or {}).get("planets") or {}
    result = {name for name in UNCONDITIONAL_MALEFICS if name in planets}
    if "Moon" in planets and _is_waxing_moon(chart) is False:
        result.add("Moon")
    mercury_sign = _planet_sign(chart, "Mercury")
    if mercury_sign is not None and any(
        _planet_sign(chart, name) == mercury_sign for name in result
    ):
        result.add("Mercury")
    return result


def _occupants(chart: Mapping[str, Any], ascendant_sign: int, house: int, allowed: set[str] | None = None) -> list[str]:
    names = allowed if allowed is not None else set((chart.get("planets") or {}).keys())
    return [name for name in PLANET_ORDER if name in names and _house(chart, name, ascendant_sign) == house]


def _joined(chart: Mapping[str, Any], first: str, second: str) -> bool:
    first_sign = _planet_sign(chart, first)
    return first_sign is not None and first_sign == _planet_sign(chart, second)


def _joined_malefics(chart: Mapping[str, Any], planet: str, malefics: set[str]) -> list[str]:
    sign = _planet_sign(chart, planet)
    if sign is None:
        return []
    return [name for name in PLANET_ORDER if name != planet and name in malefics and _planet_sign(chart, name) == sign]


def _aspecting_malefics(chart: Mapping[str, Any], planet: str, malefics: set[str]) -> list[str]:
    sign = _planet_sign(chart, planet)
    if sign is None:
        return []
    # Rahu/Ketu 5th and 9th aspects are deliberately not introduced here.
    # The generic papa-drishti clause is evaluated through visible grahas; the
    # nodes are used only where the verse names them explicitly.
    visible_malefics = malefics - {"Rahu", "Ketu"}
    return [name for name in planets_aspecting_house_sign(chart.get("planets") or {}, sign) if name in visible_malefics]


def _navamsa_sign(longitude: float | None) -> int | None:
    if longitude is None:
        return None
    sign = int(longitude % 360.0 / 30.0)
    degree = longitude % 30.0
    pada = min(int(degree / (30.0 / 9.0)), 8)
    start = (0, 9, 6, 3)[sign % 4]
    return (start + pada) % 12


def _condition(key: str, label: str, actual: Any, matched: bool) -> dict[str, Any]:
    return {"key": key, "label": label, "actual": actual, "matched": bool(matched)}


def _rule(rule_id: str, conditions: list[dict[str, Any]]) -> dict[str, Any]:
    verse, incipit, description = RULE_TEXT[rule_id]
    return {
        "rule_id": rule_id,
        "verse": verse,
        "verse_incipit": incipit,
        "description": description,
        "matched": all(row["matched"] for row in conditions),
        "conditions": conditions,
        "reference": f"BPHS {verse}",
    }


def calculate_classical_pitri_shapa(chart: Mapping[str, Any] | None) -> dict[str, Any]:
    """Evaluate all eleven BPHS combinations without modern shortcuts."""
    chart = chart or {}
    planets = chart.get("planets") or {}
    ascendant_sign = _ascendant_sign(chart)
    required = set(PLANET_ORDER)
    missing = sorted(required - set(planets))
    missing_positions = sorted(name for name in required if name in planets and _planet_sign(chart, name) is None)
    if ascendant_sign is None or missing or missing_positions:
        return {
            "method": "bphs_pitri_shapa_83_20_30",
            "available": False,
            "status": "unavailable",
            "present": False,
            "type": "Pitri-shapa",
            "display_name": "Pitṛ-śāpa · progeny-related classical combination",
            "scope": "progeny",
            "missing_planets": missing,
            "missing_positions": missing_positions,
            "summary": "The classical Pitri-shapa check is unavailable because the ascendant or required planetary positions are missing.",
            "matched_rules": [],
            "matched_rule_ids": [],
            "evaluated_rules": [],
            "reasons": [],
            "source": SOURCE,
        }

    malefics = _malefics(chart)
    planet_houses = {name: _house(chart, name, ascendant_sign) for name in PLANET_ORDER}
    lords = {number: _house_lord(ascendant_sign, number) for number in range(1, 13)}

    def malefics_in(house: int) -> list[str]:
        return _occupants(chart, ascendant_sign, house, malefics)

    sun_sign = _planet_sign(chart, "Sun")
    sun_house = planet_houses["Sun"]
    sun_navamsa = _navamsa_sign(_planet_longitude(chart, "Sun"))
    sun_joined = _joined_malefics(chart, "Sun", malefics)
    sun_aspected = _aspecting_malefics(chart, "Sun", malefics)
    previous_house = 12 if sun_house == 1 else sun_house - 1
    next_house = 1 if sun_house == 12 else sun_house + 1

    rules = [
        _rule("BPHS-PS-20", [
            _condition("sun_house", "Sun occupies House 5", sun_house, sun_house == 5),
            _condition("sun_debilitated", "Sun is debilitated in Libra", SIGN_NAMES[sun_sign], sun_sign == DEBILITATION_SIGNS["Sun"]),
            _condition("sun_saturn_navamsa", "Sun occupies a Saturn-ruled navamsha", SIGN_NAMES[sun_navamsa], SIGN_LORDS.get(sun_navamsa) == "Saturn"),
            _condition("malefic_previous_side", "A malefic occupies the previous house", malefics_in(4), bool(malefics_in(4))),
            _condition("malefic_next_side", "A malefic occupies the next house", malefics_in(6), bool(malefics_in(6))),
        ]),
        _rule("BPHS-PS-21", [
            _condition("sun_fifth_lord", "Sun is the fifth lord", lords[5], lords[5] == "Sun"),
            _condition("sun_trine", "Sun occupies a trine", sun_house, sun_house in {1, 5, 9}),
            _condition("sun_joined_malefic", "Sun joins a malefic", sun_joined, bool(sun_joined)),
            _condition("sun_hemmed_previous", "A malefic occupies the previous house from Sun", malefics_in(previous_house), bool(malefics_in(previous_house))),
            _condition("sun_hemmed_next", "A malefic occupies the next house from Sun", malefics_in(next_house), bool(malefics_in(next_house))),
            _condition("sun_aspected_malefic", "Sun receives a visible malefic graha aspect", sun_aspected, bool(sun_aspected)),
        ]),
        _rule("BPHS-PS-22", [
            _condition("jupiter_leo", "Jupiter occupies Leo", SIGN_NAMES[_planet_sign(chart, "Jupiter")], _planet_sign(chart, "Jupiter") == 4),
            _condition("fifth_lord_sun", "The fifth lord joins Sun", lords[5], _joined(chart, lords[5], "Sun") and lords[5] != "Sun"),
            _condition("malefic_lagna", "A malefic occupies House 1", malefics_in(1), bool(malefics_in(1))),
            _condition("malefic_fifth", "A malefic occupies House 5", malefics_in(5), bool(malefics_in(5))),
        ]),
        _rule("BPHS-PS-23", [
            _condition("weak_lagna_lord_fifth", "The ascendant lord occupies House 5 and weakness is established by debilitation", {"lord": lords[1], "house": planet_houses[lords[1]], "sign": SIGN_NAMES[_planet_sign(chart, lords[1])]}, planet_houses[lords[1]] == 5 and _planet_sign(chart, lords[1]) == DEBILITATION_SIGNS.get(lords[1])),
            _condition("fifth_lord_sun", "The fifth lord joins Sun", lords[5], _joined(chart, lords[5], "Sun") and lords[5] != "Sun"),
            _condition("malefic_lagna", "A malefic occupies House 1", malefics_in(1), bool(malefics_in(1))),
            _condition("malefic_fifth", "A malefic occupies House 5", malefics_in(5), bool(malefics_in(5))),
        ]),
        _rule("BPHS-PS-24", [
            _condition("ninth_fifth_or_fifth_tenth", "The ninth lord is in House 5 or the fifth lord is in House 10", {"ninth_lord": lords[9], "ninth_lord_house": planet_houses[lords[9]], "fifth_lord": lords[5], "fifth_lord_house": planet_houses[lords[5]]}, planet_houses[lords[9]] == 5 or planet_houses[lords[5]] == 10),
            _condition("malefic_lagna", "A malefic occupies House 1", malefics_in(1), bool(malefics_in(1))),
            _condition("malefic_fifth", "A malefic occupies House 5", malefics_in(5), bool(malefics_in(5))),
        ]),
        _rule("BPHS-PS-25", [
            _condition("mars_ninth_lord", "Mars is the ninth lord", lords[9], lords[9] == "Mars"),
            _condition("mars_fifth_lord_join", "Mars joins the fifth lord", lords[5], lords[5] != "Mars" and _joined(chart, "Mars", lords[5])),
            _condition("malefic_lagna", "A malefic occupies House 1", malefics_in(1), bool(malefics_in(1))),
            _condition("malefic_fifth", "A malefic occupies House 5", malefics_in(5), bool(malefics_in(5))),
            _condition("malefic_ninth", "A malefic occupies House 9", malefics_in(9), bool(malefics_in(9))),
        ]),
        _rule("BPHS-PS-26", [
            _condition("ninth_lord_dusthana", "The ninth lord occupies House 6, 8 or 12", {"lord": lords[9], "house": planet_houses[lords[9]]}, planet_houses[lords[9]] in {6, 8, 12}),
            _condition("jupiter_malefic_sign", "Jupiter occupies a sign ruled by Sun, Mars or Saturn", {"sign": SIGN_NAMES[_planet_sign(chart, "Jupiter")], "lord": SIGN_LORDS[_planet_sign(chart, "Jupiter")]}, SIGN_LORDS[_planet_sign(chart, "Jupiter")] in MALEFIC_SIGN_LORDS),
            _condition("fifth_lord_joined_malefic", "The fifth lord joins a malefic", _joined_malefics(chart, lords[5], malefics), bool(_joined_malefics(chart, lords[5], malefics))),
            _condition("lagna_lord_joined_malefic", "The ascendant lord joins a malefic", _joined_malefics(chart, lords[1], malefics), bool(_joined_malefics(chart, lords[1], malefics))),
        ]),
        _rule("BPHS-PS-27", [
            _condition("sun_mars_saturn_lagna_fifth", "Sun, Mars and Saturn occupy Houses 1 and 5, with both houses represented", {name: planet_houses[name] for name in ("Sun", "Mars", "Saturn")}, all(planet_houses[name] in {1, 5} for name in ("Sun", "Mars", "Saturn")) and {planet_houses[name] for name in ("Sun", "Mars", "Saturn")} == {1, 5}),
            _condition("rahu_eighth", "Rahu occupies House 8", planet_houses["Rahu"], planet_houses["Rahu"] == 8),
            _condition("jupiter_twelfth", "Jupiter occupies House 12", planet_houses["Jupiter"], planet_houses["Jupiter"] == 12),
        ]),
        _rule("BPHS-PS-28", [
            _condition("sun_eighth", "Sun occupies House 8", sun_house, sun_house == 8),
            _condition("saturn_fifth", "Saturn occupies House 5", planet_houses["Saturn"], planet_houses["Saturn"] == 5),
            _condition("fifth_lord_rahu", "The fifth lord joins Rahu", lords[5], _joined(chart, lords[5], "Rahu") and lords[5] != "Rahu"),
            _condition("malefic_lagna", "A malefic occupies House 1", malefics_in(1), bool(malefics_in(1))),
        ]),
        _rule("BPHS-PS-29", [
            _condition("twelfth_lord_lagna", "The twelfth lord occupies House 1", {"lord": lords[12], "house": planet_houses[lords[12]]}, planet_houses[lords[12]] == 1),
            _condition("eighth_lord_fifth", "The eighth lord occupies House 5", {"lord": lords[8], "house": planet_houses[lords[8]]}, planet_houses[lords[8]] == 5),
            _condition("ninth_lord_eighth", "The ninth lord occupies House 8", {"lord": lords[9], "house": planet_houses[lords[9]]}, planet_houses[lords[9]] == 8),
        ]),
        _rule("BPHS-PS-30", [
            _condition("sixth_lord_fifth", "The sixth lord occupies House 5", {"lord": lords[6], "house": planet_houses[lords[6]]}, planet_houses[lords[6]] == 5),
            _condition("ninth_lord_sixth", "The ninth lord occupies House 6", {"lord": lords[9], "house": planet_houses[lords[9]]}, planet_houses[lords[9]] == 6),
            _condition("jupiter_rahu", "Jupiter, the progeny significator, joins Rahu", planet_houses["Jupiter"], _joined(chart, "Jupiter", "Rahu")),
        ]),
    ]

    matched_rules = [rule for rule in rules if rule["matched"]]
    present = bool(matched_rules)
    reasons = [f"{rule['reference']}: {rule['description']}" for rule in matched_rules]
    involved_planets = sorted({
        name for rule in matched_rules for condition in rule["conditions"]
        for name in PLANET_ORDER if name.lower() in str(condition["actual"]).lower() or name.lower() in condition["label"].lower()
    }, key=PLANET_ORDER.index)

    benefics = {"Jupiter", "Venus"}
    if _is_waxing_moon(chart) is True:
        benefics.add("Moon")
    protective_factors = []
    fifth_sign = (ascendant_sign + 4) % 12
    for planet in sorted(benefics, key=PLANET_ORDER.index):
        if _planet_sign(chart, planet) == fifth_sign:
            protective_factors.append({"planet": planet, "relation": "occupies_house_5", "note": f"{planet} occupies House 5."})
        elif planet in planets_aspecting_house_sign(planets, fifth_sign):
            protective_factors.append({"planet": planet, "relation": "aspects_house_5", "note": f"{planet} aspects House 5."})

    if present:
        summary = (
            f"{len(matched_rules)} complete BPHS Pitri-shapa combination"
            f"{'s' if len(matched_rules) != 1 else ''} match this chart. "
            "In this chapter the stated scope is progeny; this is not a general label for ancestral problems in every area of life."
        )
    else:
        summary = (
            "None of the eleven complete BPHS Pitri-shapa combinations matches this chart. "
            "A separate Sun or ninth-house affliction is not relabelled as Pitri-shapa."
        )

    return {
        "method": "bphs_pitri_shapa_83_20_30",
        "available": True,
        "status": "formed" if present else "not_formed",
        "present": present,
        "type": "Pitri-shapa",
        "display_name": "Pitṛ-śāpa · progeny-related classical combination",
        "scope": "progeny",
        "classical_result": SOURCE["stated_result"],
        "summary": summary,
        "matched_rules": matched_rules,
        "matched_rule_ids": [rule["rule_id"] for rule in matched_rules],
        "evaluated_rules": rules,
        "reasons": reasons,
        "planets": involved_planets,
        "houses": [5] if present else [],
        "corroborating_factors": ({"multiple_classical_rules_match": len(matched_rules)} if len(matched_rules) > 1 else {}),
        "protective_factors": protective_factors,
        "protection_note": "These contextual benefic factors do not cancel a matched BPHS combination; verses 20-30 state no cancellation rule.",
        "excluded_shortcuts": [
            "Sun-Rahu conjunction by itself",
            "Sun-Saturn conjunction by itself",
            "Rahu, Ketu or Saturn in House 9 by itself",
            "an afflicted ninth lord by itself",
        ],
        "interpretive_notes": [
            "Verse 20's manda-amsha is evaluated specifically as a Saturn-ruled navamsha.",
            "Verse 23's durbala condition is matched conservatively only when the ascendant lord is debilitated.",
            "Verse 26's papa-rashi is evaluated as a sign ruled by Sun, Mars or Saturn.",
            "Generic malefic aspects do not use the debated Rahu/Ketu fifth and ninth aspects.",
        ],
        "source": SOURCE,
    }


def compact_pitri_shapa_for_ai(yogas: dict[str, Any]) -> dict[str, Any]:
    """Prune unmatched clause ledgers from an AI context without changing API data."""
    major = (yogas or {}).get("major_doshas") or {}
    result = major.get("pitra_dosha")
    if not isinstance(result, dict):
        return yogas
    # Copy only the path being changed. Other yoga contracts retain identity and
    # shape, while the full evaluated_rules ledger remains available to the API/UI.
    compact = dict(yogas)
    compact_major = dict(major)
    compact_result = dict(result)
    compact_result.pop("evaluated_rules", None)
    compact_result.pop("excluded_shortcuts", None)
    compact_result.pop("interpretive_notes", None)
    compact_result["matched_rules"] = result.get("matched_rules") or []
    compact_major["pitra_dosha"] = compact_result
    compact["major_doshas"] = compact_major
    return compact
