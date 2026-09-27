"""Constitutional strength and protection for the professional health screen.

This module deliberately keeps four questions separate:
* functional agenda from ascendant lordship,
* capacity from dignity and divisional repetition,
* cleanliness from affliction/combustion,
* protection actually reaching Lagna, luminaries and the four Kendras.

No numeric "health score" is produced.  Strength never changes a difficult
planet into a benefic; it only describes how forcefully that planet can act.
"""

from __future__ import annotations

from typing import Any

from calculators.avayogi_policy import avayogi_effect


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
VISIBLE_PLANETS = PLANETS[:7]
SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
KENDRAS = (1, 4, 7, 10)
TRIKONAS = frozenset({5, 9})
SUPPORT_HOUSES = frozenset({1, 5, 9})
CHALLENGE_HOUSES = frozenset({3, 6, 8, 11, 12})
MARAKA_HOUSES = frozenset({2, 7})
NATURAL_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
EXALTATION_SIGNS = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
DEBILITATION_SIGNS = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9, "Venus": 5, "Saturn": 0}
OWN_SIGNS = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
NATURAL_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
NATURAL_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}
MOOLATRIKONA = {
    "Sun": (4, 0.0, 20.0), "Moon": (1, 4.0, 30.0), "Mars": (0, 0.0, 12.0),
    "Mercury": (5, 16.0, 20.0), "Jupiter": (8, 0.0, 10.0),
    "Venus": (6, 0.0, 15.0), "Saturn": (10, 0.0, 20.0),
}
NAKSHATRA_LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

# One explicitly named tithi-dagdha tradition.  Other published tables differ,
# so the output preserves the tradition id and this factor is never counted as
# an independent disease-producing rule.
TITHI_DAGDHA_SIGNS = {
    1: (6, 9), 2: (8, 11), 3: (4, 9), 4: (1, 10), 5: (2, 5),
    6: (0, 4), 7: (3, 8), 8: (2, 5), 9: (4, 7), 10: (4, 7),
    11: (8, 11), 12: (6, 9), 13: (1, 4), 14: (11, 2, 5, 8), 15: (),
}


def _planet(chart: dict[str, Any], name: str) -> dict[str, Any]:
    value = (chart.get("planets") or {}).get(name)
    return value if isinstance(value, dict) else {}


def _house(chart: dict[str, Any], name: str) -> int | None:
    try:
        value = int(_planet(chart, name).get("house"))
        return value if 1 <= value <= 12 else None
    except (TypeError, ValueError):
        return None


def _sign(chart: dict[str, Any], name: str) -> int | None:
    data = _planet(chart, name)
    value = data.get("sign")
    if value is None and data.get("longitude") is not None:
        value = float(data["longitude"]) // 30
    try:
        return int(value) % 12
    except (TypeError, ValueError):
        return None


def _degree(chart: dict[str, Any], name: str) -> float | None:
    data = _planet(chart, name)
    try:
        if data.get("degree") is not None:
            return float(data["degree"]) % 30.0
        return float(data["longitude"]) % 30.0
    except (KeyError, TypeError, ValueError):
        return None


def _longitude(chart: dict[str, Any], name: str) -> float | None:
    data = _planet(chart, name)
    try:
        if data.get("longitude") is not None:
            return float(data["longitude"]) % 360.0
        sign, degree = _sign(chart, name), _degree(chart, name)
        return sign * 30.0 + degree if sign is not None and degree is not None else None
    except (TypeError, ValueError):
        return None


def _angular_distance(a: float, b: float) -> float:
    difference = abs(a - b) % 360.0
    return min(difference, 360.0 - difference)


def _house_sign(chart: dict[str, Any], house: int) -> int | None:
    for row in chart.get("houses") or []:
        row_house = row.get("house", row.get("house_number"))
        try:
            if int(row_house) == house:
                return int(row.get("sign")) % 12
        except (TypeError, ValueError):
            continue
    try:
        asc = int(float(chart["ascendant"]) // 30) % 12
        return (asc + house - 1) % 12
    except (KeyError, TypeError, ValueError):
        return None


def _houses_ruled(chart: dict[str, Any], planet: str) -> list[int]:
    return [house for house in range(1, 13) if SIGN_LORDS.get(_house_sign(chart, house)) == planet]


def _mutual_sign_exchange(chart: dict[str, Any], planet: str) -> dict[str, Any] | None:
    """Return a direct Parivartana relationship without transferring afflictions.

    A mutual sign exchange strengthens the dispositorship link between the two
    planets.  Pressure on the exchange partner qualifies that support, but it
    must not be reported as though every conjunction to the partner directly
    conjoined or aspected ``planet``.
    """
    occupied_sign = _sign(chart, planet)
    partner = SIGN_LORDS.get(occupied_sign) if occupied_sign is not None else None
    if not partner or partner == planet or not _planet(chart, partner):
        return None
    partner_sign = _sign(chart, partner)
    if partner_sign not in OWN_SIGNS.get(planet, set()):
        return None
    exchanged_partner_house = _house(chart, planet)
    partner_ruled_houses = _houses_ruled(chart, partner)
    return {
        "planet": partner,
        "houses": sorted({house for house in (_house(chart, planet), _house(chart, partner)) if house}),
        "partner_other_ruled_houses": [house for house in partner_ruled_houses if house != exchanged_partner_house],
        "partner_retrograde": bool(_planet(chart, partner).get("retrograde")),
        "partner_affliction_details": _affliction_details(chart, partner),
    }


def _planet_aspects_house(planet: str, source_house: int | None, target_house: int) -> bool:
    if not source_house:
        return False
    offsets = {"Mars": {4, 7, 8}, "Jupiter": {5, 7, 9}, "Saturn": {3, 7, 10}}.get(planet, {7})
    return any(((source_house + offset - 2) % 12) + 1 == target_house for offset in offsets)


def _residents(chart: dict[str, Any], house: int) -> list[str]:
    return [planet for planet in PLANETS if _house(chart, planet) == house]


def _aspectors(chart: dict[str, Any], house: int) -> list[str]:
    drishti = chart.get("graha_drishti_by_house") or {}
    if drishti:
        rows = drishti.get(house) or drishti.get(str(house)) or []
        return list(dict.fromkeys(
            str(row.get("planet")) for row in rows
            if isinstance(row, dict) and row.get("planet") not in {"Rahu", "Ketu"}
        ))
    return [planet for planet in VISIBLE_PLANETS if _planet_aspects_house(planet, _house(chart, planet), house)]


def _functional_role(chart: dict[str, Any], planet: str) -> dict[str, Any]:
    ruled = _houses_ruled(chart, planet)
    supportive = sorted(set(ruled) & SUPPORT_HOUSES)
    challenging = sorted(set(ruled) & CHALLENGE_HOUSES)
    maraka = sorted(set(ruled) & MARAKA_HOUSES)
    structural = sorted(set(ruled) & set(KENDRAS))
    yogakaraka = bool(set(ruled) & TRIKONAS and set(ruled) & {4, 7, 10})
    kendradhipati = planet in {"Moon", "Mercury", "Jupiter", "Venus"} and bool(structural) and not bool(set(ruled) & TRIKONAS)
    if yogakaraka:
        classification = "yogakaraka"
    elif supportive and challenging:
        classification = "mixed"
    elif supportive:
        classification = "supportive"
    elif challenging:
        classification = "challenging"
    elif maraka:
        classification = "vitality_sensitive"
    elif kendradhipati:
        classification = "kendra_qualified"
    else:
        classification = "structural_or_neutral"
    return {
        "classification": classification,
        "ruled_houses": ruled,
        "supportive_houses": supportive,
        "challenging_houses": challenging,
        "maraka_houses": maraka,
        "structural_houses": structural,
        "is_yogakaraka": yogakaraka,
        "kendradhipati_qualification": kendradhipati,
    }


def _dignity(chart: dict[str, Any], planet: str) -> str:
    sign, degree = _sign(chart, planet), _degree(chart, planet)
    if planet not in VISIBLE_PLANETS or sign is None:
        return "not_assigned"
    if sign == DEBILITATION_SIGNS[planet]:
        return "debilitated"
    moola = MOOLATRIKONA[planet]
    if sign == moola[0] and degree is not None and moola[1] <= degree < moola[2]:
        return "moolatrikona"
    if sign == EXALTATION_SIGNS[planet]:
        return "exalted"
    if sign in OWN_SIGNS[planet]:
        return "own_sign"
    return "ordinary"


def _sign_relationship(chart: dict[str, Any], planet: str) -> dict[str, Any]:
    sign = _sign(chart, planet)
    dispositor = SIGN_LORDS.get(sign) if sign is not None else None
    if planet not in VISIBLE_PLANETS or not dispositor:
        status = "not_assigned"
    elif dispositor == planet:
        status = "own"
    elif dispositor in NATURAL_FRIENDS.get(planet, set()):
        status = "friendly"
    elif dispositor in NATURAL_ENEMIES.get(planet, set()):
        status = "inimical"
    else:
        status = "neutral"
    return {"status": status, "dispositor": dispositor, "sign": sign}


def _combustion(chart: dict[str, Any], planet: str) -> dict[str, Any]:
    from calculators.classical_combustion import calculate_planet_combustion

    row = calculate_planet_combustion(planet, _planet(chart, planet), _planet(chart, "Sun"))
    return {
        **row,
        # Preserve the established health contract while exposing the full
        # canonical evidence under the additive keys above.
        "distance_from_sun": row["angular_distance"],
        "orb": row["threshold"],
    }


def _natural_nature(chart: dict[str, Any], planet: str) -> str:
    if planet in {"Jupiter", "Venus"}:
        return "benefic"
    if planet == "Moon":
        sun, moon = _longitude(chart, "Sun"), _longitude(chart, "Moon")
        if sun is None or moon is None:
            return "variable"
        separation = (moon - sun) % 360.0
        return "benefic" if 0.0 < separation <= 180.0 else "malefic"
    if planet == "Mercury":
        house = _house(chart, "Mercury")
        joined = set(_residents(chart, house or 0)) - {"Mercury"}
        return "malefic" if joined & NATURAL_MALEFICS else "benefic"
    return "malefic"


def _natural_nature_context(chart: dict[str, Any], planet: str) -> dict[str, Any]:
    nature = _natural_nature(chart, planet)
    if planet != "Moon":
        return {"nature": nature, "basis": "standard_natural_nature"}
    sun, moon = _longitude(chart, "Sun"), _longitude(chart, "Moon")
    if sun is None or moon is None:
        return {"nature": nature, "basis": "lunar_phase_unavailable"}
    elongation = (moon - sun) % 360.0
    return {
        "nature": nature,
        "basis": "waxing_moon" if 0.0 < elongation <= 180.0 else "waning_or_dark_moon",
        "elongation": round(elongation, 4),
    }


def _affliction_details(chart: dict[str, Any], planet: str) -> list[dict[str, Any]]:
    house = _house(chart, planet)
    if not house:
        return []
    details: list[dict[str, Any]] = []
    joined = [p for p in _residents(chart, house) if p != planet and p in NATURAL_MALEFICS]
    aspected = [p for p in _aspectors(chart, house) if p != planet and p in NATURAL_MALEFICS]
    if joined:
        details.append({"type": "joined_by_malefics", "planets": joined})
    if aspected:
        details.append({"type": "aspected_by_malefics", "planets": aspected})
    if house in {6, 8, 12}:
        details.append({"type": "difficult_house", "house": house})
    if _dignity(chart, planet) == "debilitated":
        details.append({"type": "debilitated"})
    if _combustion(chart, planet)["is_combust"]:
        details.append({"type": "combust"})
    relationship = _sign_relationship(chart, planet)
    if _dignity(chart, planet) == "ordinary" and relationship["status"] == "inimical":
        details.append({"type": "inimical_sign", "dispositor": relationship["dispositor"]})
    return details


def _afflictions(chart: dict[str, Any], planet: str) -> list[str]:
    evidence: list[str] = []
    for detail in _affliction_details(chart, planet):
        kind = detail["type"]
        if kind == "joined_by_malefics":
            evidence.append(f"joined by {', '.join(detail['planets'])}")
        elif kind == "aspected_by_malefics":
            evidence.append(f"aspected by {', '.join(detail['planets'])}")
        elif kind == "difficult_house":
            evidence.append(f"placed in House {detail['house']}")
        elif kind == "debilitated":
            evidence.append("debilitated")
        elif kind == "combust":
            evidence.append("combust")
        elif kind == "inimical_sign":
            evidence.append(f"placed in a sign ruled by natural enemy {detail['dispositor']}")
    return evidence


def _neecha_bhanga_factors(chart: dict[str, Any], planet: str) -> list[str]:
    if _dignity(chart, planet) != "debilitated":
        return []
    from calculators.classical_neecha_bhanga import calculate_classical_neecha_bhanga

    result = calculate_classical_neecha_bhanga(chart).get(planet) or {}
    factors: list[str] = []
    for condition in result.get("conditions_met") or []:
        description = str(condition.get("description") or "")
        # Preserve the familiar dispositor wording used in existing health
        # evidence while attaching the exact classical citation.
        if "lord of" in description.lower() and result.get("debilitation_sign_lord") in description:
            description = f"dispositor {result['debilitation_sign_lord']}: {description}"
        factors.append(f"{description} ({condition['reference']})")
    return list(dict.fromkeys(factors))


def _varga_dignity(chart: dict[str, Any] | None, planet: str) -> str | None:
    return _dignity(chart, planet) if isinstance(chart, dict) and _planet(chart, planet) else None


def _nakshatra_lord(longitude: float) -> str:
    index = int((longitude % 360.0) // (360.0 / 27.0))
    return NAKSHATRA_LORDS[index % 9]


def _nakshatra_context(chart: dict[str, Any], planet: str) -> dict[str, Any] | None:
    longitude = _longitude(chart, planet)
    if longitude is None:
        return None
    index = int((longitude % 360.0) // (360.0 / 27.0))
    lord = NAKSHATRA_LORDS[index % 9]
    if lord == planet:
        relationship = "own"
    elif planet in VISIBLE_PLANETS and lord in VISIBLE_PLANETS:
        if lord in NATURAL_FRIENDS.get(planet, set()):
            relationship = "friendly"
        elif lord in NATURAL_ENEMIES.get(planet, set()):
            relationship = "inimical"
        else:
            relationship = "neutral"
    else:
        # Natural-friendship schemes for the nodes vary by lineage.  Preserve
        # the star lord without manufacturing a universal grade.
        relationship = "ungraded"
    lord_afflictions = _affliction_details(chart, lord) if lord != planet else []
    return {
        "nakshatra": NAKSHATRAS[index],
        "lord": lord,
        "relationship": relationship,
        "lord_retrograde": bool(_planet(chart, lord).get("retrograde")) if lord != planet else False,
        "lord_affliction_details": lord_afflictions,
    }


def finding_modifiers_for_planet(condition: dict[str, Any]) -> dict[str, Any]:
    """Resolve one planet's support, pressure and capacity for any health finding.

    Every Health V2 consumer uses this same structure.  It prevents special
    factors from affecting only the constitution cards while being silently
    ignored by anatomical or disease findings.
    """
    planet = str(condition.get("planet") or "")
    house = condition.get("house")
    functional = condition.get("functional_role") or {}
    classification = functional.get("classification")
    support: list[dict[str, Any]] = []
    pressure: list[dict[str, Any]] = []
    capacity: list[dict[str, Any]] = []
    neutral: list[dict[str, Any]] = []

    if condition.get("natural_nature") == "benefic":
        support.append({"type": "natural_benefic", "planet": planet, "relation": "occupies", "house": house})
    elif condition.get("natural_nature") == "malefic":
        pressure.append({
            "type": (
                "waning_moon" if planet == "Moon"
                and (condition.get("natural_nature_context") or {}).get("basis") == "waning_or_dark_moon"
                else "natural_malefic"
            ),
            "planet": planet, "relation": "occupies", "house": house,
        })

    if classification in {"supportive", "yogakaraka"}:
        support.append({
            "type": "supportive_lordship", "planet": planet, "relation": "occupies", "house": house,
            "classification": classification,
        })
    elif classification == "challenging":
        pressure.append({"type": "challenging_lordship", "planet": planet, "relation": "occupies", "house": house})
    elif classification == "mixed":
        support.append({
            "type": "mixed_lordship_support", "planet": planet, "relation": "occupies", "house": house,
            "houses": list(functional.get("supportive_houses") or []),
        })
        pressure.append({
            "type": "mixed_lordship_pressure", "planet": planet, "relation": "occupies", "house": house,
            "houses": list(functional.get("challenging_houses") or []),
        })
    elif classification in {"vitality_sensitive", "kendra_qualified"}:
        pressure.append({
            "type": "qualified_lordship", "planet": planet, "relation": "occupies", "house": house,
            "classification": classification,
        })

    dignity = condition.get("dignity")
    if dignity in {"exalted", "moolatrikona", "own_sign"}:
        capacity.append({"type": "dignity_capacity", "planet": planet, "value": dignity})
    if condition.get("vargottama_d1_d9"):
        capacity.append({
            "type": "vargottama_capacity", "planet": planet,
            "agenda": "mixed" if classification == "mixed" else (
                "pressure" if classification == "challenging" else "support"
            ),
        })
    divisional = condition.get("divisional_strength") or {}
    if divisional.get("status") in {"supported", "mixed", "pressured"}:
        capacity.append({
            "type": "divisional_capacity", "planet": planet,
            "status": divisional.get("status"),
            "strong_vargas": list(divisional.get("strong_vargas") or []),
            "weak_vargas": list(divisional.get("weak_vargas") or []),
        })

    relationship = condition.get("sign_relationship") or {}
    if dignity == "ordinary" and relationship.get("status") == "friendly":
        support.append({"type": "friendly_sign", "planet": planet, "dispositor": relationship.get("dispositor")})
    nakshatra = condition.get("nakshatra_context") or {}
    if nakshatra.get("relationship") in {"own", "friendly"}:
        support.append({"type": "nakshatra_lord_support", "planet": planet, **nakshatra})
    elif nakshatra.get("relationship") == "inimical":
        pressure.append({
            "type": "inimical_nakshatra_lord", "planet": planet,
            "nakshatra": nakshatra.get("nakshatra"), "lord": nakshatra.get("lord"),
        })
    elif nakshatra.get("relationship") in {"neutral", "ungraded"}:
        neutral.append({
            "type": f"{nakshatra.get('relationship')}_nakshatra_relationship", "planet": planet,
            "nakshatra": nakshatra.get("nakshatra"), "lord": nakshatra.get("lord"),
        })

    for detail in condition.get("affliction_details") or []:
        pressure.append({"planet": planet, **detail})
    if condition.get("neecha_bhanga_factors"):
        capacity.append({
            "type": "neecha_bhanga", "planet": planet,
            "factors": list(condition.get("neecha_bhanga_factors") or []),
        })
    if condition.get("retrograde"):
        capacity.append({"type": "retrograde_intensification", "planet": planet})
    exchange = condition.get("mutual_sign_exchange") or {}
    if exchange:
        capacity.append({
            "type": "mutual_exchange_capacity",
            "planet": planet,
            "partner": exchange.get("planet"),
            "houses": list(exchange.get("houses") or []),
            "partner_other_ruled_houses": list(exchange.get("partner_other_ruled_houses") or []),
            "partner_retrograde": bool(exchange.get("partner_retrograde")),
            "partner_affliction_details": list(exchange.get("partner_affliction_details") or []),
        })

    special_roles = set(condition.get("special_roles") or [])
    if special_roles & {"yogi_lord", "duplicate_yogi"}:
        support.append({"type": "yogi_support", "planet": planet, "relation": "occupies", "house": house})
    if "avayogi_lord" in special_roles:
        avayogi = (condition.get("special_effects") or {}).get("avayogi") or {}
        if avayogi.get("polarity") == "supportive":
            support.append({"type": "reversed_avayogi_support", "planet": planet, "relation": "occupies", "house": house})
        elif avayogi.get("polarity") == "challenging":
            pressure.append({"type": "avayogi_pressure", "planet": planet, "relation": "occupies", "house": house})
    if "tithi_dagdha_occupant" in special_roles:
        pressure.append({"type": "tithi_dagdha", "planet": planet, "relation": "occupies", "house": house})

    if support and pressure:
        balance = "support_and_pressure"
    elif support:
        balance = "supportive"
    elif pressure:
        balance = "pressured"
    else:
        balance = "unqualified"
    return {
        "balance": balance,
        "support": support,
        "pressure": pressure,
        "capacity": capacity,
        "neutral": neutral,
    }


class ConstitutionalStrengthEngine:
    def __init__(self, chart: dict[str, Any], divisional_charts: dict[str, dict[str, Any]] | None = None):
        self.chart = chart
        self.divisional = divisional_charts or {}

    def calculate(self) -> dict[str, Any]:
        special = self._special_lunar_factors()
        planets = {
            planet: self._planet_condition(planet, special)
            for planet in PLANETS if _planet(self.chart, planet)
        }
        vitality_anchors = self._vitality_anchors(planets)
        pillars = [self._pillar(house, planets) for house in KENDRAS]
        jupiter = self._jupiter_protection(planets.get("Jupiter") or {})
        resilience = self._overall_resilience(pillars, jupiter, vitality_anchors)
        protection = [item for pillar in pillars for item in pillar["support"]]
        pressure = [item for pillar in pillars for item in pillar["pressure"]]
        protection.extend(jupiter["protective_reaches"])
        condition = {
            "rule_version": "constitutional-protection/1.3.0",
            "functional_nature_method": "derived_lordship_with_mixed_roles",
            "planet_conditions": planets,
            "vitality_anchors": vitality_anchors,
            "kendra_pillars": pillars,
            "jupiter_protection": jupiter,
            "overall_resilience": resilience,
            "special_lunar_factors": special,
            "protective_factors": list(dict.fromkeys(protection)),
            "pressure_factors": list(dict.fromkeys(pressure)),
            "interpretive_rules": [
                "Dignity measures capacity, not goodness.",
                "Vargottama amplifies the planet's existing functional agenda; it is not automatically benefic.",
                "Retrogression is an intensification or non-linear-delivery modifier, not a generic weakness.",
                "Protection can reduce severity and aid recovery but cannot erase a natal susceptibility.",
                "Tithi Shunya and Dagdha Rashi are treated as one selected tithi-burnt-sign tradition, never as two penalties.",
                "Rahu and Ketu special 5th/9th aspects are not assumed; node occupation, conjunction, dispositorship and authored axis rules remain available.",
            ],
            "source_references": [
                "K. S. Charak, Essentials of Medical Astrology — benefic/malefic lordship, sound-health, Kendra protection and medical-varga rule families",
                "K. S. Charak, Essentials of Medical Astrology — Rashi, Navamsha, Drekkana and Dwadashamsha medical confirmation framework",
                "Seshadri Iyer Yogi-sphuta tradition — Sun + Moon + 93°20′; Avayogi point 186°40′ from Yogi",
                "Tithi-Dagdha two-sign table, explicitly versioned because published traditions vary",
            ],
        }
        return condition

    def _planet_condition(self, planet: str, special: dict[str, Any]) -> dict[str, Any]:
        d9 = self.divisional.get("D9")
        d1_sign, d9_sign = _sign(self.chart, planet), _sign(d9 or {}, planet)
        dignity = _dignity(self.chart, planet)
        functional = _functional_role(self.chart, planet)
        afflictions = _afflictions(self.chart, planet)
        special_roles: list[str] = []
        if planet == special.get("yogi_nakshatra_lord"):
            special_roles.append("yogi_lord")
        if planet == special.get("duplicate_yogi_sign_lord"):
            special_roles.append("duplicate_yogi")
        if planet == special.get("avayogi_nakshatra_lord"):
            special_roles.append("avayogi_lord")
        if planet in (special.get("affected_planets") or []):
            special_roles.append("tithi_dagdha_occupant")
        condition = {
            "planet": planet,
            "house": _house(self.chart, planet),
            "sign": d1_sign,
            "natural_nature": _natural_nature(self.chart, planet),
            "natural_nature_context": _natural_nature_context(self.chart, planet),
            "functional_role": functional,
            "dignity": dignity,
            "sign_relationship": _sign_relationship(self.chart, planet),
            "nakshatra_context": _nakshatra_context(self.chart, planet),
            "neecha_bhanga_factors": _neecha_bhanga_factors(self.chart, planet),
            "combustion": _combustion(self.chart, planet),
            "retrograde": bool(_planet(self.chart, planet).get("retrograde")),
            "retrograde_interpretation": "intensified_or_non_linear" if _planet(self.chart, planet).get("retrograde") else None,
            "mutual_sign_exchange": _mutual_sign_exchange(self.chart, planet),
            "vargottama_d1_d9": d1_sign is not None and d1_sign == d9_sign,
            "divisional_confirmation": {
                name: {"sign": _sign(chart, planet), "dignity": _varga_dignity(chart, planet)}
                for name, chart in self.divisional.items()
                if name in {"D3", "D9", "D12"} and _planet(chart, planet)
            },
            "divisional_strength": self._divisional_strength(planet),
            "afflictions": afflictions,
            "affliction_details": _affliction_details(self.chart, planet),
            "special_roles": special_roles,
            "special_modifier_scope": "secondary_only" if special_roles else None,
            "special_effects": {
                "avayogi": special.get("avayogi_effect")
                if "avayogi_lord" in special_roles else None,
            },
            "delivery_quality": (
                "pressured" if len(afflictions) >= 2
                else "qualified" if afflictions
                else "clean"
            ),
        }
        condition["finding_modifiers"] = finding_modifiers_for_planet(condition)
        return condition

    def _pillar(self, house: int, conditions: dict[str, dict[str, Any]]) -> dict[str, Any]:
        support: list[str] = []
        pressure: list[str] = []
        support_details: list[dict[str, Any]] = []
        pressure_details: list[dict[str, Any]] = []
        relations = [(p, "occupies") for p in _residents(self.chart, house)] + [(p, "aspects") for p in _aspectors(self.chart, house)]
        for planet, relation in relations:
            data = conditions.get(planet) or {}
            functional = (data.get("functional_role") or {}).get("classification")
            natural = data.get("natural_nature")
            if natural == "benefic":
                qualification = "cleanly" if data.get("delivery_quality") == "clean" else "with qualifications"
                support.append(f"{planet} {relation} House {house} as a natural benefic {qualification}")
                support_details.append({"type": "natural_benefic", "planet": planet, "relation": relation, "qualified": qualification != "cleanly"})
            if functional in {"supportive", "yogakaraka"}:
                support.append(f"{planet} {relation} House {house} with {functional} lordship")
                support_details.append({"type": "supportive_lordship", "planet": planet, "relation": relation, "classification": functional})
            if natural == "malefic":
                pressure.append(f"{planet} {relation} House {house} as a natural malefic")
                pressure_details.append({
                    "type": "waning_moon" if planet == "Moon" and (data.get("natural_nature_context") or {}).get("basis") == "waning_or_dark_moon" else "natural_malefic",
                    "planet": planet,
                    "relation": relation,
                })
            if functional == "challenging":
                pressure.append(f"{planet} {relation} House {house} with challenging lordship")
                pressure_details.append({"type": "challenging_lordship", "planet": planet, "relation": relation})
            if functional == "mixed":
                supportive_houses = (data.get("functional_role") or {}).get("supportive_houses") or []
                challenging_houses = (data.get("functional_role") or {}).get("challenging_houses") or []
                support.append(f"{planet} {relation} House {house}; its mixed lordship includes support from Houses {', '.join(map(str, supportive_houses))}")
                pressure.append(f"{planet} {relation} House {house}; its mixed lordship includes pressure from Houses {', '.join(map(str, challenging_houses))}")
                support_details.append({"type": "mixed_lordship_support", "planet": planet, "relation": relation, "houses": supportive_houses})
                pressure_details.append({"type": "mixed_lordship_pressure", "planet": planet, "relation": relation, "houses": challenging_houses})
            if functional in {"vitality_sensitive", "kendra_qualified"}:
                pressure.append(f"{planet} {relation} House {house} with {functional.replace('_', ' ')} lordship")
                pressure_details.append({"type": "qualified_lordship", "planet": planet, "relation": relation, "classification": functional})
            special_roles = set(data.get("special_roles") or [])
            if special_roles & {"yogi_lord", "duplicate_yogi"}:
                support.append(f"{planet} {relation} House {house} with Yogi support")
                support_details.append({"type": "yogi_support", "planet": planet, "relation": relation})
            if "avayogi_lord" in special_roles:
                avayogi = (data.get("special_effects") or {}).get("avayogi") or {}
                if avayogi.get("polarity") == "supportive":
                    support.append(f"{planet} {relation} House {house} with reversed Avayogi support")
                    support_details.append({"type": "reversed_avayogi_support", "planet": planet, "relation": relation})
                elif avayogi.get("polarity") == "challenging":
                    pressure.append(f"{planet} {relation} House {house} with Avayogi pressure")
                    pressure_details.append({"type": "avayogi_pressure", "planet": planet, "relation": relation})
            if "tithi_dagdha_occupant" in special_roles:
                pressure.append(f"{planet} {relation} House {house} from a selected tithi-burnt sign")
                pressure_details.append({"type": "tithi_dagdha", "planet": planet, "relation": relation})
        if support and not pressure:
            status = "protected"
        elif support and pressure:
            status = "mixed"
        elif pressure:
            status = "pressured"
        else:
            status = "unreinforced"
        return {
            "house": house,
            "status": status,
            "support": list(dict.fromkeys(support)),
            "pressure": list(dict.fromkeys(pressure)),
            "support_details": support_details,
            "pressure_details": pressure_details,
        }

    def _divisional_strength(self, planet: str) -> dict[str, Any]:
        dignities = {
            name: _varga_dignity(chart, planet)
            for name, chart in self.divisional.items()
            if name in {"D3", "D9", "D12"} and _planet(chart, planet)
        }
        strong = [name for name, value in dignities.items() if value in {"exalted", "moolatrikona", "own_sign"}]
        weak = [name for name, value in dignities.items() if value == "debilitated"]
        if strong and weak:
            status = "mixed"
        elif strong:
            status = "supported"
        elif weak:
            status = "pressured"
        else:
            status = "unconfirmed"
        return {"status": status, "strong_vargas": strong, "weak_vargas": weak, "evaluated_vargas": sorted(dignities)}

    def _vitality_anchors(self, conditions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        asc_sign = _house_sign(self.chart, 1)
        lagna_lord = SIGN_LORDS.get(asc_sign)
        anchors = (("lagna_lord", lagna_lord), ("sun", "Sun"), ("moon", "Moon"))
        output: list[dict[str, Any]] = []
        for role, planet in anchors:
            data = conditions.get(planet or "") or {}
            delivery = data.get("delivery_quality")
            dignity = data.get("dignity")
            varga = (data.get("divisional_strength") or {}).get("status")
            house = data.get("house")
            strengthening_factors = [
                *([{"type": "dignity", "value": dignity}] if dignity in {"exalted", "moolatrikona", "own_sign"} else []),
                *([{
                    "type": "divisional_reinforcement",
                    "charts": list((data.get("divisional_strength") or {}).get("strong_vargas") or []),
                }] if varga == "supported" else []),
                *([{
                    "type": "vargottama_d1_d9",
                }] if data.get("vargottama_d1_d9") else []),
                *([{
                    "type": "supportive_house_placement",
                    "house": house,
                    "group": "kendra" if house in KENDRAS else "trikona",
                }] if house in KENDRAS or house in TRIKONAS else []),
                *([{
                    "type": "friendly_sign",
                    "dispositor": (data.get("sign_relationship") or {}).get("dispositor"),
                }] if dignity == "ordinary" and (data.get("sign_relationship") or {}).get("status") == "friendly" else []),
                *([{
                    "type": "waxing_moon",
                }] if planet == "Moon" and (data.get("natural_nature_context") or {}).get("basis") == "waxing_moon" else []),
            ]
            exchange = _mutual_sign_exchange(self.chart, planet or "")
            if exchange:
                strengthening_factors.append({"type": "mutual_sign_exchange", **exchange})
            affliction_details = list(data.get("affliction_details") or [])
            if planet == "Moon" and (data.get("natural_nature_context") or {}).get("basis") == "waning_or_dark_moon":
                affliction_details.append({"type": "waning_moon"})
            nakshatra = data.get("nakshatra_context") or {}
            nakshatra_relationship = nakshatra.get("relationship")
            neutral_factors: list[dict[str, Any]] = []
            sign_relationship = (data.get("sign_relationship") or {}).get("status")
            if sign_relationship == "neutral":
                neutral_factors.append({
                    "type": "neutral_sign_relationship",
                    "sign_name": SIGN_NAMES[(data.get("sign_relationship") or {}).get("sign")],
                    "dispositor": (data.get("sign_relationship") or {}).get("dispositor"),
                })
            if nakshatra_relationship in {"own", "friendly"}:
                strengthening_factors.append({
                    "type": "nakshatra_lord_support",
                    **nakshatra,
                })
            elif nakshatra_relationship == "inimical":
                affliction_details.append({
                    "type": "inimical_nakshatra_lord",
                    "nakshatra": nakshatra.get("nakshatra"),
                    "lord": nakshatra.get("lord"),
                })
            elif nakshatra_relationship in {"neutral", "ungraded"}:
                neutral_factors.append({
                    "type": f"{nakshatra_relationship}_nakshatra_relationship",
                    "nakshatra": nakshatra.get("nakshatra"),
                    "lord": nakshatra.get("lord"),
                })
            if delivery == "pressured":
                status = "pressured"
            elif dignity in {"exalted", "moolatrikona", "own_sign"} or varga == "supported":
                status = "strong"
            elif strengthening_factors and affliction_details:
                status = "mixed"
            elif delivery == "clean" and not affliction_details:
                status = "supported"
            else:
                status = "qualified"
            output.append({
                "role": role,
                "planet": planet,
                "house": house,
                "ruled_houses": list((data.get("functional_role") or {}).get("ruled_houses") or []),
                "sign_relationship": data.get("sign_relationship"),
                "sign_name": (
                    SIGN_NAMES[(data.get("sign_relationship") or {}).get("sign")]
                    if isinstance((data.get("sign_relationship") or {}).get("sign"), int)
                    else None
                ),
                "nakshatra_context": nakshatra or None,
                "status": status,
                "dignity": dignity,
                "delivery_quality": delivery,
                "divisional_strength": varga,
                "afflictions": list(data.get("afflictions") or []),
                "affliction_details": affliction_details,
                "strengthening_factors": strengthening_factors,
                "neutral_factors": neutral_factors,
            })
        return output

    @staticmethod
    def _overall_resilience(
        pillars: list[dict[str, Any]],
        jupiter: dict[str, Any],
        vitality_anchors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        protected = sum(row["status"] == "protected" for row in pillars)
        mixed = sum(row["status"] == "mixed" for row in pillars)
        pressured = sum(row["status"] == "pressured" for row in pillars)
        lagna_status = next((row["status"] for row in pillars if row["house"] == 1), "unreinforced")
        jupiter_quality = jupiter.get("quality")
        # Lagna lord can itself be the Sun or Moon.  Preserve both roles in the
        # report, but do not count the same planet twice as independent
        # constitutional evidence.
        unique_anchors = {
            row.get("planet"): row
            for row in vitality_anchors
            if row.get("planet")
        }
        anchor_statuses = [row["status"] for row in unique_anchors.values()]
        anchor_support = sum(status in {"strong", "supported"} for status in anchor_statuses)
        anchor_pressure = sum(status == "pressured" for status in anchor_statuses)
        anchor_qualified = sum(status in {"qualified", "mixed"} for status in anchor_statuses)
        if protected >= 3 and anchor_support >= 2 and jupiter_quality == "major_clean_support":
            status = "strongly_protected"
        elif (
            anchor_pressure == 0
            and (protected >= 2 or (protected + mixed >= 3 and jupiter_quality in {"major_clean_support", "qualified_but_present"}))
        ):
            status = "supported"
        elif pressured >= 3 and (lagna_status == "pressured" or anchor_pressure >= 2):
            status = "constitution_under_pressure"
        else:
            status = "mixed"
        if status == "strongly_protected":
            explanation = "strong_protection"
        elif status == "supported":
            explanation = "clear_support"
        elif status == "constitution_under_pressure":
            explanation = "pressure_dominates"
        elif pressured or mixed or anchor_pressure:
            explanation = "support_and_pressure"
        else:
            explanation = "support_is_limited"
        return {
            "status": status,
            "explanation": explanation,
            "protected_pillars": protected,
            "mixed_pillars": mixed,
            "pressured_pillars": pressured,
            "lagna_pillar_status": lagna_status,
            "jupiter_quality": jupiter_quality,
            "unique_vitality_anchors": len(anchor_statuses),
            "vitality_anchor_support": anchor_support,
            "vitality_anchor_qualified": anchor_qualified,
            "vitality_anchor_pressure": anchor_pressure,
            "note": "This describes support and recovery capacity; it does not erase or create a vulnerability.",
        }

    def _jupiter_protection(self, data: dict[str, Any]) -> dict[str, Any]:
        house = _house(self.chart, "Jupiter")
        # Occupation is itself a protective contact.  Earlier versions only
        # retained Jupiter's house when it happened to be a Kendra or the
        # house occupied by a luminary, which made a benefic Jupiter in (for
        # example) H2 disappear from its own judgment.
        sun_house = _house(self.chart, "Sun")
        moon_house = _house(self.chart, "Moon")
        targets = {house, 1, 4, 7, 10, sun_house, moon_house}
        reached = sorted(target for target in targets if target and (target == house or _planet_aspects_house("Jupiter", house, target)))
        dignity = data.get("dignity")
        functional = (data.get("functional_role") or {}).get("classification")
        modifiers = data.get("finding_modifiers") or finding_modifiers_for_planet(data)
        pressure_factors = list(modifiers.get("pressure") or [])
        if dignity == "debilitated" and not data.get("neecha_bhanga_factors"):
            quality = "limited_but_present"
        elif pressure_factors or functional in {"mixed", "challenging"}:
            quality = "qualified_but_present"
        else:
            quality = "major_clean_support"
        reach_details = []
        for target in reached:
            roles = []
            if target in {1, 4, 7, 10}:
                roles.append("constitutional_pillar")
            if target == sun_house:
                roles.append("vital_drive")
            if target == moon_house:
                roles.append("restoration_rhythm")
            reach_details.append({
                "house": target,
                "mode": "occupation" if target == house else "aspect",
                "health_focus_key": f"h{target}",
                "roles": roles,
            })
        return {
            "quality": quality,
            "conclusion_key": quality,
            "functional_qualification": functional,
            "reached_houses": reached,
            "reach_details": reach_details,
            "support_factors": list(modifiers.get("support") or []),
            "pressure_factors": pressure_factors,
            "capacity_modifiers": list(modifiers.get("capacity") or []),
            "judgment_scope": "modifies_severity_and_recovery_without_cancelling_vulnerability",
            "protective_reaches": [f"Jupiter protects House {target} ({quality.replace('_', ' ')})" for target in reached],
            "first_house_expansion_tendency": house == 1,
            "first_house_note": (
                "Jupiter in House 1 supplies constitutional support and an expansion tendency. Weight gain requires separate metabolic corroboration."
                if house == 1 else None
            ),
        }

    def _special_lunar_factors(self) -> dict[str, Any]:
        sun, moon = _longitude(self.chart, "Sun"), _longitude(self.chart, "Moon")
        if sun is None or moon is None:
            return {"available": False, "reason": "Sun and Moon longitudes are required"}
        yogi_point = (sun + moon + 93.0 + 20.0 / 60.0) % 360.0
        avayogi_point = (yogi_point + 66.0 + 40.0 / 60.0) % 360.0
        tithi = int(((moon - sun) % 360.0) // 12.0) + 1
        reduced_tithi = ((tithi - 1) % 15) + 1
        dagdha_signs = list(TITHI_DAGDHA_SIGNS[reduced_tithi])
        affected = [planet for planet in PLANETS if _sign(self.chart, planet) in dagdha_signs]
        avayogi_lord = _nakshatra_lord(avayogi_point)
        dagdha_lords = {SIGN_LORDS[sign] for sign in dagdha_signs}
        avayogi_resolution = avayogi_effect(
            placement_house=_house(self.chart, avayogi_lord),
            tithi_shunya_overlap=avayogi_lord in dagdha_lords,
        )
        return {
            "available": True,
            "yogi_point": round(yogi_point, 6),
            "yogi_nakshatra_lord": _nakshatra_lord(yogi_point),
            "duplicate_yogi_sign_lord": SIGN_LORDS[int(yogi_point // 30)],
            "avayogi_point": round(avayogi_point, 6),
            "avayogi_nakshatra_lord": avayogi_lord,
            "avayogi_effect": avayogi_resolution,
            "tithi_number": tithi,
            "paksha_tithi_number": reduced_tithi,
            "tithi_dagdha_signs": dagdha_signs,
            "affected_planets": affected,
            "tradition_id": "tithi-dagdha-two-sign-table/1.0.0",
            "interpretation_scope": "secondary_modifier_only",
            "tradition_note": "Published Tithi Shunya/Dagdha tables vary. This named table is counted once and never creates a health finding by itself.",
        }
