"""Conservative classical Mangal (Kuja) Dosha calculation.

The selected natal rule is BPHS 80.47.  It names Mars in houses 1, 12, 4, 7
and 8 *when Mars is without a benefic aspect or conjunction*.  Placement and
the qualifying clause are therefore evaluated together instead of treating a
benefic relationship as an invented later percentage reduction.

A separate Agastya-samhita reading begins ``dhane...`` and names houses 2,
12, 4, 7 and 8.  It is reported as a distinct textual/traditional reading;
the two lists are never silently combined into the popular six-house rule.

The pair rule beginning ``kuja doshavati deya...`` is printed in the Vivaha
appendix to Muhurta Chintamani (verse 50 in the cited Hindi edition).  It is a
pair-level balancing rule.  It does not erase the formation in either natal
chart.

This module deliberately does not invent severity bands, use D9 houses, or
apply commonly circulated individual cancellation lists whose textual source
has not been selected and verified.
"""

from __future__ import annotations

from typing import Any, Mapping


PRIMARY_HOUSES = frozenset({1, 4, 7, 8, 12})
DHANA_READING_HOUSES = frozenset({2, 4, 7, 8, 12})

FORMATION_SOURCE = {
    "work": "Brihat Parashara Hora Shastra",
    "section": "Chapter 80, Strijataka",
    "verse_number": "80.47",
    "verse_incipit": "lagne vyaye sukhe vapi saptame castame kuje",
    "reference_label": "Brihat Parashara Hora Shastra 80.47",
    "textual_note": (
        "The verse is stated in the female-horoscope chapter and includes the "
        "condition ‘without a benefic aspect or conjunction’. AstroRoshni shows "
        "the formation without repeating the verse’s literal fatal wording."
    ),
}

DHANA_SOURCE = {
    "work": "Agastya Samhita",
    "section": "Vivaha, Kuja-dosha verse",
    "verse_number": "edition-dependent",
    "verse_incipit": "dhane vyaye ca patale jamitre castame kuje",
    "reference_label": "Agastya Samhita, verse beginning ‘dhane vyaye ca patale…’",
    "textual_note": (
        "This is shown as a separate second-house reading. It is not merged with "
        "BPHS 80.47 to create a six-house rule."
    ),
}

PAIR_SOURCE = {
    "work": "Muhurta Chintamani",
    "section": "Vivaha Prakarana, appendix",
    "verse_number": "50 in the cited Hindi appendix edition",
    "verse_incipit": "kuja doshavati deya kuja dosavate kila",
    "reference_label": "Muhurta Chintamani, Vivaha appendix, verse 50",
}

REFERENCE_NOTE = {
    "lagna": "The selected formation verse is read from the natal ascendant.",
    "moon": (
        "Moon-reference counting is retained as supplementary traditional evidence; "
        "it does not change the selected Lagna-based verdict."
    ),
    "venus": (
        "Venus-reference counting is retained as supplementary traditional evidence; "
        "it does not change the selected Lagna-based verdict."
    ),
}

UNCONDITIONAL_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})


def _normalise_sign(value: Any) -> int | None:
    if value is None:
        return None
    try:
        sign = int(value)
    except (TypeError, ValueError):
        return None
    if 0 <= sign <= 11:
        return sign
    if 1 <= sign <= 12:
        return sign - 1
    return None


def _planet_sign(chart: Mapping[str, Any], planet: str) -> int | None:
    row = ((chart or {}).get("planets") or {}).get(planet) or {}
    sign = _normalise_sign(row.get("sign"))
    if sign is not None:
        return sign
    longitude = row.get("longitude")
    if longitude is None:
        return None
    return int(float(longitude) % 360.0 / 30.0)


def _planet_longitude(chart: Mapping[str, Any], planet: str) -> float | None:
    row = ((chart or {}).get("planets") or {}).get(planet) or {}
    value = row.get("longitude")
    if value is None:
        return None
    try:
        return float(value) % 360.0
    except (TypeError, ValueError):
        return None


def _ascendant_sign(chart: Mapping[str, Any]) -> int | None:
    ascendant = (chart or {}).get("ascendant")
    if isinstance(ascendant, Mapping):
        sign = _normalise_sign(ascendant.get("sign"))
        if sign is not None:
            return sign
        ascendant = ascendant.get("longitude")
    if ascendant is None:
        houses = (chart or {}).get("houses") or []
        if houses:
            return _normalise_sign((houses[0] or {}).get("sign"))
        return None
    return int(float(ascendant) % 360.0 / 30.0)


def _house_from(reference_sign: int | None, target_sign: int | None) -> int | None:
    if reference_sign is None or target_sign is None:
        return None
    return ((target_sign - reference_sign) % 12) + 1


def _reading(rule_id: str, house: int | None, houses: frozenset[int], label: str) -> dict[str, Any]:
    matched = house in houses if house is not None else False
    return {
        "rule_id": rule_id,
        "label": label,
        "house": house,
        "houses_checked": sorted(houses),
        "matched": matched,
    }


def _is_waxing_moon(chart: Mapping[str, Any]) -> bool | None:
    sun = _planet_longitude(chart, "Sun")
    moon = _planet_longitude(chart, "Moon")
    if sun is None or moon is None:
        return None
    elongation = (moon - sun) % 360.0
    return 0.0 < elongation <= 180.0


def _benefic_planets(chart: Mapping[str, Any]) -> tuple[set[str], dict[str, Any]]:
    """BPHS natural benefics, with Moon and Mercury treated contextually."""
    planets = (chart or {}).get("planets") or {}
    benefics = {planet for planet in ("Jupiter", "Venus") if _planet_sign(chart, planet) is not None}
    waxing = _is_waxing_moon(chart)
    if waxing is True and _planet_sign(chart, "Moon") is not None:
        benefics.add("Moon")

    mercury_sign = _planet_sign(chart, "Mercury")
    mercury_with_malefics: list[str] = []
    if mercury_sign is not None:
        for planet in UNCONDITIONAL_MALEFICS:
            if planet in planets and _planet_sign(chart, planet) == mercury_sign:
                mercury_with_malefics.append(planet)
        if waxing is False and _planet_sign(chart, "Moon") == mercury_sign:
            mercury_with_malefics.append("waning Moon")
        if not mercury_with_malefics:
            benefics.add("Mercury")

    return benefics, {
        "waxing_moon": waxing,
        "mercury_joined_malefics": sorted(mercury_with_malefics),
        "source": {
            "work": "Brihat Parashara Hora Shastra",
            "section": "Chapter 3, Graha qualities",
            "reference_label": "BPHS Chapter 3, natural benefic and malefic nature",
        },
    }


def _aspects_target(source_sign: int, target_sign: int, planet: str) -> bool:
    distance = ((target_sign - source_sign) % 12) + 1
    aspects = {7}
    if planet == "Jupiter":
        aspects.update({5, 9})
    return distance in aspects


def _benefic_relations_to_mars(chart: Mapping[str, Any], mars_sign: int | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    benefics, nature_context = _benefic_planets(chart)
    relations: list[dict[str, Any]] = []
    if mars_sign is None:
        return relations, nature_context
    for planet in sorted(benefics):
        sign = _planet_sign(chart, planet)
        if sign is None:
            continue
        if sign == mars_sign:
            relations.append({"planet": planet, "relation": "conjunction", "matched": True})
        elif _aspects_target(sign, mars_sign, planet):
            relations.append({"planet": planet, "relation": "aspect", "matched": True})
    return relations, nature_context


def calculate_classical_mangal_dosha(chart: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a structured single-chart verdict without merging traditions."""
    chart = chart or {}
    mars_sign = _planet_sign(chart, "Mars")
    lagna_sign = _ascendant_sign(chart)
    moon_sign = _planet_sign(chart, "Moon")
    venus_sign = _planet_sign(chart, "Venus")

    lagna_house = _house_from(lagna_sign, mars_sign)
    moon_house = _house_from(moon_sign, mars_sign)
    venus_house = _house_from(venus_sign, mars_sign)
    benefic_relations, benefic_nature = _benefic_relations_to_mars(chart, mars_sign)

    primary = _reading(
        "MS-LAGNE",
        lagna_house,
        PRIMARY_HOUSES,
        "Lagna reading: Mars in House 1, 4, 7, 8 or 12",
    )
    dhana_variant = _reading(
        "MS-DHANE-VARIANT",
        lagna_house,
        DHANA_READING_HOUSES,
        "Dhane textual reading: Mars in House 2, 4, 7, 8 or 12",
    )
    dhana_variant["material_difference"] = dhana_variant["matched"] != primary["matched"]
    moon_reference = _reading(
        "SUPPLEMENT-MOON",
        moon_house,
        PRIMARY_HOUSES,
        "Supplementary count from the Moon",
    )
    venus_reference = _reading(
        "SUPPLEMENT-VENUS",
        venus_house,
        PRIMARY_HOUSES,
        "Supplementary count from Venus",
    )

    available = mars_sign is not None and lagna_sign is not None
    placement_present = bool(primary["matched"]) if available else False
    exception_applied = placement_present and bool(benefic_relations)
    present = placement_present and not exception_applied
    status = (
        "formed" if present
        else "protected" if exception_applied
        else "not_formed" if available
        else "unavailable"
    )
    if status == "formed":
        summary = f"Mangal Dosha is formed in the selected Lagna reading: Mars is in House {lagna_house}."
    elif status == "protected":
        relation_text = ", ".join(f"{row['planet']} {row['relation']}" for row in benefic_relations)
        summary = (
            f"Mars is in House {lagna_house}, but the complete BPHS 80.47 condition is not formed "
            f"because Mars has a benefic relationship: {relation_text}."
        )
    elif status == "not_formed":
        summary = f"Mangal Dosha is not formed in the selected Lagna reading: Mars is in House {lagna_house}."
    else:
        summary = "Mangal Dosha could not be calculated because Mars or the ascendant is missing."

    return {
        "method": "bphs_80_47_lagna_reading",
        "available": available,
        "status": status,
        "present": present,
        "placement_present": placement_present,
        "is_manglik": present,
        "effective": present,
        "summary": summary,
        "mars_sign": mars_sign,
        "mars_house": lagna_house,
        "mars_house_lagna": lagna_house,
        "mars_house_moon": moon_house,
        "mars_house_venus": venus_house,
        "from_lagna": present,
        "from_moon": bool(moon_reference["matched"]),
        "from_venus": bool(venus_reference["matched"]),
        # Legacy keys remain, but their values no longer claim an invented intensity.
        "type": "Present" if present else "None",
        "severity": "Present" if present else "None",
        "primary_reading": primary,
        "textual_variants": [{**dhana_variant, "source": DHANA_SOURCE}],
        "supplementary_references": {
            "moon": {**moon_reference, "note": REFERENCE_NOTE["moon"]},
            "venus": {**venus_reference, "note": REFERENCE_NOTE["venus"]},
        },
        "references": {
            "lagna": {**primary, "note": REFERENCE_NOTE["lagna"]},
            "moon": {**moon_reference, "note": REFERENCE_NOTE["moon"]},
            "venus": {**venus_reference, "note": REFERENCE_NOTE["venus"]},
            "navamsa_d9": {
                "house": None,
                "matched": False,
                "used": False,
                "note": "D9 houses are not part of the selected formation verse.",
            },
        },
        "individual_exceptions": {
            "applied": exception_applied,
            "matched_rules": benefic_relations,
            "note": (
                "BPHS 80.47 makes absence of a benefic aspect or conjunction part of the rule itself. "
                "No sign-strength, age, D9, ritual, or percentage shortcut is added."
            ),
        },
        "cancellation": {
            "has_cancellation": exception_applied,
            "factors": [f"{row['planet']} {row['relation']}" for row in benefic_relations],
            "note": "This field mirrors the BPHS qualifying clause for old clients; pair balancing remains separate.",
        },
        "benefic_condition": {
            "required_absent": True,
            "relations_to_mars": benefic_relations,
            "nature_context": benefic_nature,
        },
        "source": FORMATION_SOURCE,
        "pair_source": PAIR_SOURCE,
        "evidence": [
            {
                "rule_id": primary["rule_id"],
                "matched": primary["matched"],
                "fact": f"Mars is House {lagna_house} from Lagna" if lagna_house else "Lagna placement unavailable",
                "source": FORMATION_SOURCE,
            },
            {
                "rule_id": "BPHS-80.47-SUBHA-DRG-YOGA-HINA",
                "matched": placement_present and not benefic_relations,
                "fact": (
                    "Mars has no benefic aspect or conjunction"
                    if not benefic_relations
                    else "Benefic relation to Mars: " + ", ".join(
                        f"{row['planet']} {row['relation']}" for row in benefic_relations
                    )
                ),
                "source": FORMATION_SOURCE,
            },
            {
                "rule_id": dhana_variant["rule_id"],
                "matched": dhana_variant["matched"],
                "material_difference": dhana_variant["material_difference"],
                "fact": (
                    "The separate Agastya reading includes Mars in House 2; BPHS 80.47 does not."
                    if lagna_house == 2
                    else "BPHS 80.47 includes Mars in House 1; the separate Agastya reading does not."
                    if lagna_house == 1
                    else "The separate Agastya reading gives the same placement result for this house."
                ),
                "source": DHANA_SOURCE,
            },
            {
                "rule_id": moon_reference["rule_id"],
                "matched": moon_reference["matched"],
                "fact": f"Mars is House {moon_house} from Moon" if moon_house else "Moon reference unavailable",
                "source": DHANA_SOURCE,
                "supplementary": True,
            },
            {
                "rule_id": venus_reference["rule_id"],
                "matched": venus_reference["matched"],
                "fact": f"Mars is House {venus_house} from Venus" if venus_house else "Venus reference unavailable",
                "source": DHANA_SOURCE,
                "supplementary": True,
            },
        ],
    }


def calculate_mangal_pair_balance(
    first: Mapping[str, Any], second: Mapping[str, Any]
) -> dict[str, Any]:
    """Apply the cited pair rule without erasing either natal formation."""
    first_present = bool(first.get("present", first.get("is_manglik")))
    second_present = bool(second.get("present", second.get("is_manglik")))
    both = first_present and second_present
    one = first_present ^ second_present
    if both:
        status = "balanced"
        description = "Both charts contain the selected Mangal Dosha formation, so the cited pair rule treats the dosha as balanced."
    elif one:
        status = "one_sided"
        description = "The selected Mangal Dosha formation is present in only one chart; the cited pair-balancing rule does not apply."
    else:
        status = "not_applicable"
        description = "Neither chart contains the selected Mangal Dosha formation."
    return {
        "status": status,
        "balanced": both,
        "pair_cancellation": both,
        "one_sided": one,
        "description": description,
        "source": PAIR_SOURCE,
        # Compatibility fields retained for old clients; not a classical score.
        "score": 9 if both else 4 if one else 10,
        "score_is_classical": False,
        "score_note": "Legacy product compatibility value; the classical rule supplies no numeric score.",
        "exception_reasons": [description] if both else [],
    }
