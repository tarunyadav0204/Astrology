"""Canonical Parashari functional nature for the seven visible planets.

The calculation deliberately preserves two classical layers instead of
pretending that they always say exactly the same thing:

* BPHS 34.2-17 gives general rules based on house ownership.
* BPHS 34.19-44 gives an ascendant-by-ascendant catalogue.

Existing clients historically consume a three-value ``benefic | malefic |
neutral`` field.  ``functional_nature`` remains that compatibility field and
is taken from the ascendant-specific catalogue.  The general derivation,
Yogakaraka role, Maraka role and textual qualifications are returned
additively so callers do not have to collapse distinct doctrines together.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

KENDRAS = frozenset({1, 4, 7, 10})
YOGAKARAKA_KENDRAS = frozenset({4, 7, 10})
TRIKONAS = frozenset({1, 5, 9})
SPECIAL_TRIKONAS = frozenset({5, 9})
TRISHADAYA = frozenset({3, 6, 11})
CONDITIONAL_HOUSES = frozenset({2, 8, 12})
MARAKA_HOUSES = frozenset({2, 7})
NATURAL_BENEFICS = frozenset({"Moon", "Mercury", "Jupiter", "Venus"})


def _row(
    benefic: Iterable[str],
    malefic: Iterable[str],
    *,
    neutral: Iterable[str] = (),
    qualifications: Mapping[str, str] | None = None,
    yoga_notes: Mapping[str, str] | None = None,
    maraka_notes: Mapping[str, str] | None = None,
    verses: str,
) -> Dict[str, Any]:
    return {
        "benefic": tuple(benefic),
        "malefic": tuple(malefic),
        "neutral": tuple(neutral),
        "qualifications": dict(qualifications or {}),
        "yoga_notes": dict(yoga_notes or {}),
        "maraka_notes": dict(maraka_notes or {}),
        "verses": verses,
    }


# BPHS 34.19-44, kept as stated rather than regularised into a modern table.
# Qualified planets are mapped conservatively for the old three-value field;
# their exact qualification remains visible in ``stated_qualification``.
BPHS_ASCENDANT_ROLES: Dict[int, Dict[str, Any]] = {
    0: _row(
        ("Sun", "Mars", "Jupiter"), ("Mercury", "Venus", "Saturn"), neutral=("Moon",),
        qualifications={"Mars": "Helpful to auspicious planets despite owning House 8."},
        maraka_notes={"Venus": "Independent Maraka; other adverse planets can kill when associated with Venus."},
        verses="BPHS 34.19-22",
    ),
    1: _row(
        ("Sun", "Saturn"), ("Moon", "Mercury", "Jupiter", "Venus"), neutral=("Mars",),
        qualifications={"Mercury": "Somewhat inauspicious."},
        yoga_notes={"Saturn": "Causes Raja Yoga."},
        maraka_notes={"Mars": "Included among the planets capable of inflicting death in the stated passage."},
        verses="BPHS 34.23-24",
    ),
    2: _row(
        ("Venus",), ("Sun", "Mars", "Jupiter"), neutral=("Moon", "Mercury", "Saturn"),
        qualifications={
            "Moon": "Prime Maraka, with delivery dependent on association.",
            "Mercury": "Not separately called auspicious in the ascendant-specific passage.",
            "Saturn": "Not separately called auspicious in the ascendant-specific passage.",
        },
        maraka_notes={"Moon": "Prime Maraka; dependent on association."},
        verses="BPHS 34.25-26",
    ),
    3: _row(
        ("Moon", "Mars", "Jupiter"), ("Mercury", "Venus"), neutral=("Sun", "Saturn"),
        yoga_notes={"Mars": "Capable of conferring a full-fledged Yoga."},
        maraka_notes={"Sun": "Killer according to association.", "Saturn": "Killer according to association."},
        verses="BPHS 34.27-28",
    ),
    4: _row(
        ("Sun", "Mars", "Jupiter"), ("Mercury", "Venus", "Saturn"), neutral=("Moon",),
        maraka_notes={"Moon": "Killer according to association.", "Saturn": "Killer according to association."},
        verses="BPHS 34.29-30",
    ),
    5: _row(
        ("Mercury", "Venus"), ("Moon", "Mars", "Jupiter"), neutral=("Sun", "Saturn"),
        qualifications={"Sun": "Results depend on association."},
        yoga_notes={"Mercury": "Its union with Venus produces Yoga.", "Venus": "Its union with Mercury produces Yoga."},
        maraka_notes={"Venus": "Also carries a Maraka role."},
        verses="BPHS 34.31-32",
    ),
    6: _row(
        ("Mercury", "Saturn"), ("Sun", "Mars", "Jupiter"), neutral=("Moon", "Venus"),
        qualifications={"Venus": "Neutral."},
        yoga_notes={"Moon": "Its union with Mercury causes Raja Yoga.", "Mercury": "Its union with Moon causes Raja Yoga."},
        maraka_notes={"Mars": "Maraka."},
        verses="BPHS 34.33-34",
    ),
    7: _row(
        ("Sun", "Moon", "Jupiter"), ("Mercury", "Venus", "Saturn"), neutral=("Mars",),
        qualifications={"Mars": "Neutral."},
        yoga_notes={"Sun": "Named a Yoga-giver in the ascendant-specific passage.", "Moon": "Named a Yoga-giver in the ascendant-specific passage."},
        maraka_notes={"Venus": "Carries death-inflicting capacity along with other adverse planets."},
        verses="BPHS 34.35-36",
    ),
    8: _row(
        ("Sun", "Mars"), ("Venus",), neutral=("Moon", "Mercury", "Jupiter", "Saturn"),
        qualifications={"Jupiter": "Neutral."},
        yoga_notes={"Sun": "Its union with Mercury can confer Yoga.", "Mercury": "Its union with Sun can confer Yoga."},
        maraka_notes={"Saturn": "Killer.", "Venus": "Acquires killing powers."},
        verses="BPHS 34.37-38",
    ),
    9: _row(
        ("Mercury", "Venus"), ("Moon", "Mars", "Jupiter"), neutral=("Sun", "Saturn"),
        qualifications={"Sun": "Neutral.", "Saturn": "Does not kill independently."},
        yoga_notes={"Venus": "The only planet said to cause a superior Yoga."},
        verses="BPHS 34.39-40",
    ),
    10: _row(
        ("Venus", "Saturn"), ("Moon", "Mars", "Jupiter"), neutral=("Sun", "Mercury"),
        qualifications={"Mercury": "Gives middling results."},
        yoga_notes={"Venus": "The only planet said to cause Raja Yoga."},
        maraka_notes={"Sun": "Killer.", "Mars": "Killer.", "Jupiter": "Killer."},
        verses="BPHS 34.41-42",
    ),
    11: _row(
        ("Moon", "Mars"), ("Sun", "Mercury", "Venus", "Saturn"), neutral=("Jupiter",),
        yoga_notes={"Mars": "Its union with Jupiter causes Yoga.", "Jupiter": "Its union with Mars causes Yoga."},
        maraka_notes={"Mars": "Maraka but does not kill independently.", "Mercury": "Maraka.", "Saturn": "Maraka."},
        verses="BPHS 34.43-44",
    ),
}


def normalize_ascendant_sign(value: Any) -> int:
    """Accept a zero-based sign or an ascendant longitude."""
    number = float(value)
    if 0 <= number < 12 and number.is_integer():
        return int(number)
    return int(number // 30.0) % 12


def ruled_houses_for_ascendant(ascendant_sign: Any, planet: str) -> List[int]:
    asc = normalize_ascendant_sign(ascendant_sign)
    return [
        house for house in range(1, 13)
        if SIGN_LORDS[(asc + house - 1) % 12] == planet
    ]


def derive_lordship_nature(ruled_houses: Iterable[int], planet: str) -> Dict[str, Any]:
    """Apply BPHS 34.2-17 without replacing the stated per-lagna catalogue."""
    houses = tuple(sorted({int(house) for house in ruled_houses}))
    owned = set(houses)
    is_yogakaraka = bool(owned & YOGAKARAKA_KENDRAS) and bool(owned & SPECIAL_TRIKONAS)
    reasons: List[str] = []

    if is_yogakaraka:
        nature = "benefic"
        reasons.append("Owns both a Kendra and a Trikona; BPHS 34.13 makes it Yogakaraka.")
    elif 1 in owned:
        nature = "benefic"
        reasons.append("Owns the Lagna, which BPHS 34.3 calls specially auspicious.")
    elif owned & SPECIAL_TRIKONAS:
        if 8 in owned:
            nature = "benefic"
            reasons.append("Owns a Trikona together with House 8; BPHS 34.6 preserves auspiciousness through the Trikona ownership.")
        elif owned & TRISHADAYA:
            nature = "mixed"
            reasons.append("Combines auspicious Trikona ownership with an inauspicious 3rd, 6th or 11th lordship.")
        else:
            nature = "benefic"
            reasons.append("Owns House 5 or 9, whose lord BPHS 34.2-3 treats as auspicious.")
    elif owned & TRISHADAYA:
        nature = "malefic"
        reasons.append("Owns House 3, 6 or 11, whose lord BPHS 34.3 treats as inauspicious.")
    elif 8 in owned:
        if planet in {"Sun", "Moon"}:
            nature = "neutral"
            reasons.append("Sun and Moon are exempted from the ordinary evil of House 8 lordship in BPHS 34.7.")
        elif owned & {3, 7, 11}:
            nature = "malefic"
            reasons.append("House 8 lordship combined with House 3, 7 or 11 is specifically harmful in BPHS 34.6.")
        else:
            nature = "malefic"
            reasons.append("House 8 lordship is ordinarily inauspicious under BPHS 34.6.")
    elif owned and owned <= KENDRAS:
        nature = "neutral"
        if planet in NATURAL_BENEFICS:
            reasons.append("A natural benefic owning a Kendra alone loses part of its beneficence under BPHS 34.2 and 34.14; Moon phase and Mercury's associations must still be judged separately.")
        else:
            reasons.append("A natural malefic owning a Kendra alone loses part of its adverse character under BPHS 34.2; Kendra ownership alone is not Yogakaraka status.")
    elif owned & {2, 12}:
        nature = "conditional"
        reasons.append("House 2 and 12 lords give results according to association under BPHS 34.5.")
    else:
        nature = "neutral"
        reasons.append("No directional functional role is established by BPHS 34.2-17.")

    return {
        "nature": nature,
        "ruled_houses": list(houses),
        "is_yogakaraka": is_yogakaraka,
        "reasons": reasons,
        "source": "BPHS 34.2-17",
    }


def calculate_functional_nature(ascendant_sign: Any, planet: str) -> Dict[str, Any]:
    asc = normalize_ascendant_sign(ascendant_sign)
    planet = str(planet)
    if planet not in PLANETS:
        return {
            "functional_nature": "neutral",
            "classification": "not_applicable",
            "applicable": False,
            "planet": planet,
            "ascendant_sign": asc,
            "ascendant_sign_name": SIGN_NAMES[asc],
            "ruled_houses": [],
            "stated_nature": None,
            "stated_qualification": "Functional nature is not assigned here; nodes and special points require their own dispositor and association rules.",
            "stated_yoga_note": None,
            "stated_maraka_note": None,
            "stated_verses": None,
            "derived_nature": "not_applicable",
            "derived_reasons": [],
            "is_yogakaraka": False,
            "is_maraka_lord": False,
            "maraka_houses": [],
            "textual_departure": False,
            "source": {
                "text": "Brihat Parashara Hora Shastra",
                "chapter": 34,
                "general_rules": "34.2-17",
                "ascendant_specific": BPHS_ASCENDANT_ROLES[asc]["verses"],
            },
        }
    ruled_houses = ruled_houses_for_ascendant(asc, planet)
    derived = derive_lordship_nature(ruled_houses, planet)
    stated = BPHS_ASCENDANT_ROLES[asc]
    if planet in stated["benefic"]:
        stated_nature = "benefic"
    elif planet in stated["malefic"]:
        stated_nature = "malefic"
    else:
        stated_nature = "neutral"

    qualification = stated["qualifications"].get(planet)
    yoga_note = stated["yoga_notes"].get(planet)
    maraka_note = stated["maraka_notes"].get(planet)
    departure = derived["nature"] not in {stated_nature, "conditional"} and not (
        derived["nature"] == "mixed" and stated_nature == "neutral"
    )
    return {
        # Stable compatibility field used by existing clients.
        "functional_nature": stated_nature,
        "classification": stated_nature,
        "applicable": True,
        "planet": planet,
        "ascendant_sign": asc,
        "ascendant_sign_name": SIGN_NAMES[asc],
        "ruled_houses": ruled_houses,
        "stated_nature": stated_nature,
        "stated_qualification": qualification,
        "stated_yoga_note": yoga_note,
        "stated_maraka_note": maraka_note,
        "stated_verses": stated["verses"],
        "derived_nature": derived["nature"],
        "derived_reasons": derived["reasons"],
        "is_yogakaraka": derived["is_yogakaraka"],
        "is_maraka_lord": bool(set(ruled_houses) & MARAKA_HOUSES),
        "maraka_houses": sorted(set(ruled_houses) & MARAKA_HOUSES),
        "textual_departure": departure,
        "source": {
            "text": "Brihat Parashara Hora Shastra",
            "chapter": 34,
            "general_rules": "34.2-17",
            "ascendant_specific": stated["verses"],
        },
    }


def functional_nature_table(ascendant_sign: Any) -> Dict[str, Dict[str, Any]]:
    asc = normalize_ascendant_sign(ascendant_sign)
    return {planet: calculate_functional_nature(asc, planet) for planet in PLANETS}


def compatibility_lists() -> tuple[Dict[int, List[str]], Dict[int, List[str]], Dict[int, List[str]]]:
    benefics: Dict[int, List[str]] = {}
    malefics: Dict[int, List[str]] = {}
    neutrals: Dict[int, List[str]] = {}
    for asc in range(12):
        table = functional_nature_table(asc)
        benefics[asc] = [planet for planet in PLANETS if table[planet]["functional_nature"] == "benefic"]
        malefics[asc] = [planet for planet in PLANETS if table[planet]["functional_nature"] == "malefic"]
        neutrals[asc] = [planet for planet in PLANETS if table[planet]["functional_nature"] == "neutral"]
    return benefics, malefics, neutrals
