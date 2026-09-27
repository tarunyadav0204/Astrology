"""Classical Mātṛ-śāpa combinations from BPHS 83.34-46.

The passage concerns loss or absence of progeny attributed by the text to a
mother's curse from a former birth.  It does not define ordinary Moon or
fourth-house affliction as a general-purpose "Matru Dosha".
"""

from __future__ import annotations

from typing import Any, Mapping

from .classical_pitri_shapa import (
    DEBILITATION_SIGNS,
    MALEFIC_SIGN_LORDS,
    PLANET_ORDER,
    SIGN_LORDS,
    SIGN_NAMES,
    _ascendant_sign,
    _condition,
    _house,
    _house_lord,
    _is_waxing_moon,
    _joined,
    _joined_malefics,
    _malefics,
    _navamsa_sign,
    _occupants,
    _planet_longitude,
    _planet_sign,
)
from .vedic_graha_drishti import planets_aspecting_house_sign


SOURCE = {
    "work": "Brihat Parashara Hora Shastra",
    "chapter_title": "Purvajanma-shapa-dyotana (indications of curses from a former birth)",
    "chapter_number": "83 in the Chaukhamba/Devachandra Jha arrangement",
    "verse_numbers": "83.34-46",
    "remedy_verses": "83.47-50",
    "verse_incipit": "putrasthanadhipe candre ...",
    "reference_label": "Brihat Parashara Hora Shastra, Purvajanma-shapa-dyotana 34-46 (Chaukhamba: 83.34-46)",
    "source_url": "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/par8190.html",
    "translation_url": "https://www.futurestudyonline.com/future_products/articles_documents/ARTL-17.pdf",
    "scope": "progeny",
    "stated_result": "suta-kshaya / santati-kshaya (loss or absence of progeny)",
    "textual_note": (
        "Chapter numbering varies by edition. The thirteen rules do not make every Moon, "
        "fourth-house, or fourth-lord affliction a Matri-shapa, and the text gives no "
        "Low/Medium/High grading."
    ),
}

RULE_TEXT = {
    "BPHS-MS-34": ("83.34", "putrasthanadhipe candre", "Moon is the fifth lord and is debilitated or hemmed between malefics, while malefics occupy Houses 4 and 5."),
    "BPHS-MS-35": ("83.35", "labhe mandasamayukte", "Saturn occupies House 11, a malefic occupies House 4, and the debilitated Moon occupies House 5."),
    "BPHS-MS-36": ("83.36", "putrasthanadhipe duhsthe", "The fifth lord is in a dusthana, the ascendant lord is debilitated, and Moon joins a malefic."),
    "BPHS-MS-37": ("83.37", "putreshe'shtaririphasthe", "The fifth lord is in a dusthana, Moon occupies a malefic-ruled navamsha, and malefics occupy Houses 1 and 5."),
    "BPHS-MS-38": ("83.38", "putrasthanadhipe candre", "Moon is the fifth lord, occupies House 5 or 9, and joins Saturn, Rahu and Mars."),
    "BPHS-MS-39": ("83.39", "matristhanadhipe bhaume", "Mars is the fourth lord and joins Saturn and Rahu, while Sun occupies House 5 and Moon occupies House 1."),
    "BPHS-MS-40": ("83.40", "lagnatmajeshau shatrusthau", "The ascendant and fifth lords occupy House 6, the fourth lord occupies House 8, and the eighth and tenth lords occupy House 1."),
    "BPHS-MS-41": ("83.41", "shashthashtameshau lagnasthau", "The sixth and eighth lords occupy House 1, the fourth lord occupies House 12, and Moon and Jupiter join malefics in House 5."),
    "BPHS-MS-42": ("83.42", "papamadhyagate lagne", "The ascendant is hemmed between malefics, waning Moon occupies House 7, Rahu occupies House 4 and Saturn occupies House 5."),
    "BPHS-MS-43": ("83.43", "nashasthanadhipe putre", "The fifth and eighth lords exchange houses, while Moon and the fourth lord occupy dusthanas."),
    "BPHS-MS-44": ("83.44", "candraksetre yada lagne", "Cancer rises with Mars and Rahu in House 1, while Moon and Saturn occupy House 5."),
    "BPHS-MS-45": ("83.45", "lagne putre mritau riphe", "Mars, Rahu, Sun and Saturn occupy Houses 1, 5, 8 and 12 respectively, while the ascendant and fourth lords occupy dusthanas."),
    "BPHS-MS-46": ("83.46", "nashasthanam gate jive", "Mars, Rahu and Jupiter occupy House 8, while Saturn and Moon occupy House 5."),
}


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


def calculate_classical_matri_shapa(chart: Mapping[str, Any] | None) -> dict[str, Any]:
    """Evaluate the thirteen complete BPHS Mātṛ-śāpa combinations."""
    chart = chart or {}
    planets = chart.get("planets") or {}
    ascendant_sign = _ascendant_sign(chart)
    required = set(PLANET_ORDER)
    missing = sorted(required - set(planets))
    missing_positions = sorted(name for name in required if name in planets and _planet_sign(chart, name) is None)
    if ascendant_sign is None or missing or missing_positions:
        return {
            "method": "bphs_matri_shapa_83_34_46",
            "available": False,
            "status": "unavailable",
            "present": False,
            "type": "Matri-shapa",
            "display_name": "Mātṛ-śāpa · progeny-related classical combination",
            "scope": "progeny",
            "missing_planets": missing,
            "missing_positions": missing_positions,
            "summary": "The classical Matri-shapa check is unavailable because the ascendant or required planetary positions are missing.",
            "matched_rules": [], "matched_rule_ids": [], "evaluated_rules": [], "reasons": [],
            "source": SOURCE,
        }

    malefics = _malefics(chart)
    houses = {name: _house(chart, name, ascendant_sign) for name in PLANET_ORDER}
    lords = {number: _house_lord(ascendant_sign, number) for number in range(1, 13)}

    def malefics_in(house: int) -> list[str]:
        return _occupants(chart, ascendant_sign, house, malefics)

    def joined_malefic(planet: str) -> list[str]:
        return _joined_malefics(chart, planet, malefics)

    moon_house = houses["Moon"]
    moon_sign = _planet_sign(chart, "Moon")
    moon_prev = 12 if moon_house == 1 else moon_house - 1
    moon_next = 1 if moon_house == 12 else moon_house + 1
    moon_hemmed = bool(malefics_in(moon_prev) and malefics_in(moon_next))
    moon_navamsa = _navamsa_sign(_planet_longitude(chart, "Moon"))
    moon_navamsa_name = SIGN_NAMES[moon_navamsa] if moon_navamsa is not None else "Unavailable"
    moon_navamsa_lord = SIGN_LORDS.get(moon_navamsa)
    dusthanas = {6, 8, 12}

    rules = [
        _rule("BPHS-MS-34", [
            _condition("moon_fifth_lord", "Moon is the fifth lord", lords[5], lords[5] == "Moon"),
            _condition("moon_debilitated_or_hemmed", "Moon is debilitated or hemmed between malefics", {"debilitated": moon_sign == DEBILITATION_SIGNS["Moon"], "previous": malefics_in(moon_prev), "next": malefics_in(moon_next)}, moon_sign == DEBILITATION_SIGNS["Moon"] or moon_hemmed),
            _condition("malefic_fourth", "A malefic occupies House 4", malefics_in(4), bool(malefics_in(4))),
            _condition("malefic_fifth", "A malefic occupies House 5", malefics_in(5), bool(malefics_in(5))),
        ]),
        _rule("BPHS-MS-35", [
            _condition("saturn_eleventh", "Saturn occupies House 11", houses["Saturn"], houses["Saturn"] == 11),
            _condition("malefic_fourth", "A malefic occupies House 4", malefics_in(4), bool(malefics_in(4))),
            _condition("moon_fifth_debilitated", "Moon occupies House 5 in Scorpio", {"house": moon_house, "sign": SIGN_NAMES[moon_sign]}, moon_house == 5 and moon_sign == DEBILITATION_SIGNS["Moon"]),
        ]),
        _rule("BPHS-MS-36", [
            _condition("fifth_lord_dusthana", "The fifth lord occupies House 6, 8 or 12", {"lord": lords[5], "house": houses[lords[5]]}, houses[lords[5]] in dusthanas),
            _condition("lagna_lord_debilitated", "The ascendant lord is debilitated", {"lord": lords[1], "sign": SIGN_NAMES[_planet_sign(chart, lords[1])]}, _planet_sign(chart, lords[1]) == DEBILITATION_SIGNS.get(lords[1])),
            _condition("moon_joined_malefic", "Moon joins a malefic", joined_malefic("Moon"), bool(joined_malefic("Moon"))),
        ]),
        _rule("BPHS-MS-37", [
            _condition("fifth_lord_dusthana", "The fifth lord occupies House 6, 8 or 12", {"lord": lords[5], "house": houses[lords[5]]}, houses[lords[5]] in dusthanas),
            _condition("moon_malefic_navamsa", "Moon occupies a navamsha ruled by Sun, Mars or Saturn", {"navamsha": moon_navamsa_name, "lord": moon_navamsa_lord}, moon_navamsa_lord in MALEFIC_SIGN_LORDS),
            _condition("malefic_lagna", "A malefic occupies House 1", malefics_in(1), bool(malefics_in(1))),
            _condition("malefic_fifth", "A malefic occupies House 5", malefics_in(5), bool(malefics_in(5))),
        ]),
        _rule("BPHS-MS-38", [
            _condition("moon_fifth_lord", "Moon is the fifth lord", lords[5], lords[5] == "Moon"),
            _condition("moon_fifth_or_ninth", "Moon occupies House 5 or 9", moon_house, moon_house in {5, 9}),
            _condition("moon_saturn_rahu_mars", "Moon joins Saturn, Rahu and Mars", [name for name in ("Saturn", "Rahu", "Mars") if _joined(chart, "Moon", name)], all(_joined(chart, "Moon", name) for name in ("Saturn", "Rahu", "Mars"))),
        ]),
        _rule("BPHS-MS-39", [
            _condition("mars_fourth_lord", "Mars is the fourth lord", lords[4], lords[4] == "Mars"),
            _condition("mars_saturn_rahu", "Mars joins Saturn and Rahu", [name for name in ("Saturn", "Rahu") if _joined(chart, "Mars", name)], all(_joined(chart, "Mars", name) for name in ("Saturn", "Rahu"))),
            _condition("sun_fifth", "Sun occupies House 5", houses["Sun"], houses["Sun"] == 5),
            _condition("moon_lagna", "Moon occupies House 1", moon_house, moon_house == 1),
        ]),
        _rule("BPHS-MS-40", [
            _condition("lagna_lord_sixth", "The ascendant lord occupies House 6", {"lord": lords[1], "house": houses[lords[1]]}, houses[lords[1]] == 6),
            _condition("fifth_lord_sixth", "The fifth lord occupies House 6", {"lord": lords[5], "house": houses[lords[5]]}, houses[lords[5]] == 6),
            _condition("fourth_lord_eighth", "The fourth lord occupies House 8", {"lord": lords[4], "house": houses[lords[4]]}, houses[lords[4]] == 8),
            _condition("eighth_lord_lagna", "The eighth lord occupies House 1", {"lord": lords[8], "house": houses[lords[8]]}, houses[lords[8]] == 1),
            _condition("tenth_lord_lagna", "The tenth lord occupies House 1", {"lord": lords[10], "house": houses[lords[10]]}, houses[lords[10]] == 1),
        ]),
        _rule("BPHS-MS-41", [
            _condition("sixth_lord_lagna", "The sixth lord occupies House 1", {"lord": lords[6], "house": houses[lords[6]]}, houses[lords[6]] == 1),
            _condition("eighth_lord_lagna", "The eighth lord occupies House 1", {"lord": lords[8], "house": houses[lords[8]]}, houses[lords[8]] == 1),
            _condition("fourth_lord_twelfth", "The fourth lord occupies House 12", {"lord": lords[4], "house": houses[lords[4]]}, houses[lords[4]] == 12),
            _condition("moon_jupiter_fifth", "Moon and Jupiter occupy House 5", {"Moon": moon_house, "Jupiter": houses["Jupiter"]}, moon_house == 5 and houses["Jupiter"] == 5),
            _condition("moon_jupiter_with_malefics", "Moon and Jupiter each join a malefic", {"Moon": joined_malefic("Moon"), "Jupiter": joined_malefic("Jupiter")}, bool(joined_malefic("Moon")) and bool(joined_malefic("Jupiter"))),
        ]),
        _rule("BPHS-MS-42", [
            _condition("lagna_hemmed", "The ascendant is hemmed between malefics", {"House 12": malefics_in(12), "House 2": malefics_in(2)}, bool(malefics_in(12) and malefics_in(2))),
            _condition("waning_moon_seventh", "Waning Moon occupies House 7", {"house": moon_house, "waxing": _is_waxing_moon(chart)}, moon_house == 7 and _is_waxing_moon(chart) is False),
            _condition("rahu_fourth", "Rahu occupies House 4", houses["Rahu"], houses["Rahu"] == 4),
            _condition("saturn_fifth", "Saturn occupies House 5", houses["Saturn"], houses["Saturn"] == 5),
        ]),
        _rule("BPHS-MS-43", [
            _condition("fifth_eighth_exchange", "The fifth and eighth lords exchange Houses 5 and 8", {"fifth_lord": lords[5], "house": houses[lords[5]], "eighth_lord": lords[8], "eighth_house": houses[lords[8]]}, houses[lords[5]] == 8 and houses[lords[8]] == 5),
            _condition("moon_dusthana", "Moon occupies House 6, 8 or 12", moon_house, moon_house in dusthanas),
            _condition("fourth_lord_dusthana", "The fourth lord occupies House 6, 8 or 12", {"lord": lords[4], "house": houses[lords[4]]}, houses[lords[4]] in dusthanas),
        ]),
        _rule("BPHS-MS-44", [
            _condition("cancer_ascendant", "Cancer is the ascendant", SIGN_NAMES[ascendant_sign], ascendant_sign == 3),
            _condition("mars_rahu_lagna", "Mars and Rahu occupy House 1", {"Mars": houses["Mars"], "Rahu": houses["Rahu"]}, houses["Mars"] == 1 and houses["Rahu"] == 1),
            _condition("moon_saturn_fifth", "Moon and Saturn occupy House 5", {"Moon": moon_house, "Saturn": houses["Saturn"]}, moon_house == 5 and houses["Saturn"] == 5),
        ]),
        _rule("BPHS-MS-45", [
            _condition("four_planet_chain", "Mars, Rahu, Sun and Saturn occupy Houses 1, 5, 8 and 12 respectively", {name: houses[name] for name in ("Mars", "Rahu", "Sun", "Saturn")}, houses["Mars"] == 1 and houses["Rahu"] == 5 and houses["Sun"] == 8 and houses["Saturn"] == 12),
            _condition("lagna_lord_dusthana", "The ascendant lord occupies House 6, 8 or 12", {"lord": lords[1], "house": houses[lords[1]]}, houses[lords[1]] in dusthanas),
            _condition("fourth_lord_dusthana", "The fourth lord occupies House 6, 8 or 12", {"lord": lords[4], "house": houses[lords[4]]}, houses[lords[4]] in dusthanas),
        ]),
        _rule("BPHS-MS-46", [
            _condition("mars_rahu_jupiter_eighth", "Mars, Rahu and Jupiter occupy House 8", {name: houses[name] for name in ("Mars", "Rahu", "Jupiter")}, all(houses[name] == 8 for name in ("Mars", "Rahu", "Jupiter"))),
            _condition("saturn_moon_fifth", "Saturn and Moon occupy House 5", {"Saturn": houses["Saturn"], "Moon": moon_house}, houses["Saturn"] == 5 and moon_house == 5),
        ]),
    ]

    matched_rules = [rule for rule in rules if rule["matched"]]
    present = bool(matched_rules)
    involved_planets = sorted({
        name for rule in matched_rules for condition in rule["conditions"] for name in PLANET_ORDER
        if name.lower() in str(condition["actual"]).lower() or name.lower() in condition["label"].lower()
    }, key=PLANET_ORDER.index)

    benefics = {"Jupiter", "Venus"}
    if _is_waxing_moon(chart) is True:
        benefics.add("Moon")
    fifth_sign = (ascendant_sign + 4) % 12
    fourth_sign = (ascendant_sign + 3) % 12
    protective_factors = []
    for planet in sorted(benefics, key=PLANET_ORDER.index):
        for house, sign in ((4, fourth_sign), (5, fifth_sign)):
            if _planet_sign(chart, planet) == sign:
                protective_factors.append({"planet": planet, "relation": f"occupies_house_{house}", "note": f"{planet} occupies House {house}."})
            elif planet in planets_aspecting_house_sign(planets, sign):
                protective_factors.append({"planet": planet, "relation": f"aspects_house_{house}", "note": f"{planet} aspects House {house}."})

    summary = (
        f"{len(matched_rules)} complete BPHS Matri-shapa combination{'s' if len(matched_rules) != 1 else ''} match this chart. "
        "The stated scope is progeny, not a general judgment about the native's mother or maternal relationship."
        if present else
        "None of the thirteen complete BPHS Matri-shapa combinations matches this chart. A separate Moon, fourth-house, or fourth-lord affliction is not relabelled as Matri-shapa."
    )
    return {
        "method": "bphs_matri_shapa_83_34_46",
        "available": True,
        "status": "formed" if present else "not_formed",
        "present": present,
        "type": "Matri-shapa",
        "display_name": "Mātṛ-śāpa · progeny-related classical combination",
        "scope": "progeny",
        "classical_result": SOURCE["stated_result"],
        "summary": summary,
        "matched_rules": matched_rules,
        "matched_rule_ids": [rule["rule_id"] for rule in matched_rules],
        "evaluated_rules": rules,
        "reasons": [f"{rule['reference']}: {rule['description']}" for rule in matched_rules],
        "planets": involved_planets,
        "houses": [4, 5] if present else [],
        "corroborating_factors": ({"multiple_classical_rules_match": len(matched_rules)} if len(matched_rules) > 1 else {}),
        "protective_factors": protective_factors,
        "protection_note": "These contextual benefic factors do not cancel a matched BPHS combination; verses 34-46 state no cancellation rule.",
        "excluded_shortcuts": [
            "Moon-Rahu conjunction by itself", "Moon-Saturn conjunction by itself",
            "a malefic in House 4 by itself", "an afflicted Moon or fourth lord by itself",
        ],
        "interpretive_notes": [
            "Verse 34 is evaluated with its stated alternative: Moon is debilitated or hemmed between malefics.",
            "Verse 37's papa-amsha is evaluated as a navamsha ruled by Sun, Mars or Saturn.",
            "Generic malefic association means same-sign conjunction; debated Rahu/Ketu fifth and ninth aspects are not introduced.",
            "The remedies belong to verses 47-50 and are reported as the text's prescriptions, not medical or guaranteed outcomes.",
        ],
        "source_stated_remedies": [
            "ritual bathing at Setu", "one hundred thousand Gayatri recitations",
            "planet-related charity", "feeding Brahmins", "1,008 circumambulations of a peepal tree",
        ],
        "source": SOURCE,
    }


def compact_matri_shapa_for_ai(yogas: dict[str, Any]) -> dict[str, Any]:
    """Remove the unmatched-rule ledger from chat context without mutating API data."""
    major = (yogas or {}).get("major_doshas") or {}
    result = major.get("matru_dosha")
    if not isinstance(result, dict):
        return yogas
    compact = dict(yogas)
    compact_major = dict(major)
    compact_result = dict(result)
    for key in ("evaluated_rules", "excluded_shortcuts", "interpretive_notes"):
        compact_result.pop(key, None)
    compact_result["matched_rules"] = result.get("matched_rules") or []
    compact_major["matru_dosha"] = compact_result
    compact["major_doshas"] = compact_major
    return compact
