"""Classical Neecha Bhanga Raja Yoga rules from Phaladeepika 7.26-30.

The module intentionally implements only the combinations stated in the cited
passage. It does not infer extra rules from Navamsha, retrogression, exchange,
conjunction, or modern strength scores.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .base_calculator import BaseCalculator
from .vedic_graha_drishti import planets_aspecting_house_sign


SOURCE: Dict[str, Any] = {
    "work": "Phaladeepika",
    "author": "Mantreswara",
    "chapter": 7,
    "verses": [26, 27, 28, 29, 30],
    "section": "Maharaja Yogas",
    "edition": "English translation, commentary and annotation by Dr. G. S. Kapoor",
    "reference_label": "Phaladeepika 7.26-30",
    "reference_url": "https://vedpuran.net/wp-content/uploads/2021/04/mantreswara_s__phaladeeplka.pdf",
    "textual_note": (
        "The commentary to verse 26 records two readings of Uchchanatha: "
        "the lord of the debilitated planet's exaltation sign, or the planet "
        "exalted in the debilitation sign. Both are kept as distinct tests."
    ),
}

CLASSICAL_RESULT = (
    "Phaladeepika 7.26-30 describes the resulting yoga in royal terms: "
    "power, status, fame and wealth."
)

KENDRA_OFFSETS = {1, 4, 7, 10}
VISIBLE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SIGN_NAMES = tuple(BaseCalculator.SIGN_NAMES)
SIGN_LORDS = dict(BaseCalculator.SIGN_LORDS)
EXALTATION_SIGNS = dict(BaseCalculator.EXALTATION_SIGNS)
DEBILITATION_SIGNS = dict(BaseCalculator.DEBILITATION_SIGNS)
PLANET_EXALTED_IN_SIGN = {sign: planet for planet, sign in EXALTATION_SIGNS.items()}


def _sign(placement: Dict[str, Any]) -> Optional[int]:
    value = placement.get("sign")
    if isinstance(value, int) and 0 <= value <= 11:
        return value
    longitude = placement.get("longitude")
    if isinstance(longitude, (int, float)):
        return int(float(longitude) % 360.0 // 30.0)
    return None


def _house(chart: Dict[str, Any], planet: str) -> Optional[int]:
    placement = (chart.get("planets") or {}).get(planet) or {}
    value = placement.get("house")
    if isinstance(value, int) and 1 <= value <= 12:
        return value
    planet_sign = _sign(placement)
    ascendant = chart.get("ascendant")
    if planet_sign is None or not isinstance(ascendant, (int, float)):
        return None
    ascendant_sign = int(float(ascendant) % 360.0 // 30.0)
    return ((planet_sign - ascendant_sign) % 12) + 1


def _distance_from(reference_house: int, target_house: int) -> int:
    return ((target_house - reference_house) % 12) + 1


def _is_kendra(reference_house: Optional[int], target_house: Optional[int]) -> bool:
    return bool(
        reference_house
        and target_house
        and _distance_from(reference_house, target_house) in KENDRA_OFFSETS
    )


def _condition(
    rule_id: str,
    verse: str,
    description: str,
    planets: Iterable[str],
    houses: Iterable[Optional[int]],
    legacy_rule_ids: Iterable[str] = (),
) -> Dict[str, Any]:
    return {
        "rule_id": rule_id,
        "condition": description,
        "description": description,
        "reference": f"Phaladeepika {verse}",
        "planets": list(dict.fromkeys(p for p in planets if p)),
        "houses": list(dict.fromkeys(int(h) for h in houses if h is not None)),
        "legacy_rule_ids": list(dict.fromkeys(legacy_rule_ids)),
    }


def _kendra_conditions(
    *,
    planet: str,
    role_planet: str,
    role_label: str,
    rule_prefix: str,
    verse: str,
    moon_house: Optional[int],
    chart: Dict[str, Any],
    legacy_role: Optional[str] = None,
) -> List[Dict[str, Any]]:
    role_house = _house(chart, role_planet)
    conditions: List[Dict[str, Any]] = []
    for reference, reference_house in (("Lagna", 1), ("Moon", moon_house)):
        if not _is_kendra(reference_house, role_house):
            continue
        legacy = []
        if legacy_role:
            legacy.append(f"{legacy_role}_in_kendra_from_{reference.lower()}")
        conditions.append(
            _condition(
                f"{rule_prefix}_{reference.upper()}",
                verse,
                f"{role_label} {role_planet} is in House {role_house}, a Kendra from {reference}.",
                (planet, role_planet),
                (role_house,),
                legacy,
            )
        )
    return conditions


def calculate_classical_neecha_bhanga(chart: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return Phaladeepika 7.26-30 matches for every debilitated visible planet."""

    planets = chart.get("planets") or {}
    moon_house = _house(chart, "Moon")
    results: Dict[str, Dict[str, Any]] = {}

    for planet in VISIBLE_PLANETS:
        placement = planets.get(planet) or {}
        debilitation_sign = DEBILITATION_SIGNS[planet]
        if _sign(placement) != debilitation_sign:
            continue

        planet_house = _house(chart, planet)
        dispositor = SIGN_LORDS[debilitation_sign]
        dispositor_house = _house(chart, dispositor)
        exaltation_sign_lord = SIGN_LORDS[EXALTATION_SIGNS[planet]]
        exaltation_sign_lord_house = _house(chart, exaltation_sign_lord)
        planet_exalted_here = PLANET_EXALTED_IN_SIGN.get(debilitation_sign)
        conditions: List[Dict[str, Any]] = []

        # 7.26 and 7.29 both state the dispositor-in-Kendra limb.
        conditions.extend(
            _kendra_conditions(
                planet=planet,
                role_planet=dispositor,
                role_label=f"The lord of {SIGN_NAMES[debilitation_sign]},",
                rule_prefix="PD_7_26_29_DEBILITATION_LORD_KENDRA_FROM",
                verse="7.26, 7.29",
                moon_house=moon_house,
                chart=chart,
                legacy_role="debilitation_sign_lord",
            )
        )

        # The first Uchchanatha reading recorded in the commentary to 7.26.
        if planet_exalted_here:
            conditions.extend(
                _kendra_conditions(
                    planet=planet,
                    role_planet=planet_exalted_here,
                    role_label=f"The planet exalted in {SIGN_NAMES[debilitation_sign]},",
                    rule_prefix="PD_7_26_EXALTED_IN_DEBILITATION_SIGN_KENDRA_FROM",
                    verse="7.26",
                    moon_house=moon_house,
                    chart=chart,
                )
            )

        # The second Uchchanatha reading, restated explicitly at 7.29.
        conditions.extend(
            _kendra_conditions(
                planet=planet,
                role_planet=exaltation_sign_lord,
                role_label=f"The lord of {planet}'s exaltation sign,",
                rule_prefix="PD_7_29_EXALTATION_SIGN_LORD_KENDRA_FROM",
                verse="7.29",
                moon_house=moon_house,
                chart=chart,
                legacy_role="exaltation_sign_lord",
            )
        )

        # 7.27: the two lords occupy mutual Kendras.
        if _is_kendra(dispositor_house, exaltation_sign_lord_house):
            conditions.append(
                _condition(
                    "PD_7_27_LORDS_IN_MUTUAL_KENDRAS",
                    "7.27",
                    f"{dispositor}, lord of the debilitation sign, and {exaltation_sign_lord}, "
                    "lord of the planet's exaltation sign, are in mutual Kendras.",
                    (planet, dispositor, exaltation_sign_lord),
                    (dispositor_house, exaltation_sign_lord_house),
                )
            )

        # 7.28 states aspect by the lord of the occupied debilitation sign.
        if planet_house is not None and dispositor in planets_aspecting_house_sign(planets, debilitation_sign):
            conditions.append(
                _condition(
                    "PD_7_28_DEBILITATED_PLANET_ASPECTED_BY_SIGN_LORD",
                    "7.28",
                    f"The debilitated {planet} is aspected by its dispositor {dispositor}.",
                    (planet, dispositor),
                    (planet_house, dispositor_house),
                    ("debilitated_planet_connected_to_sign_lord",),
                )
            )

        # The fifth cancellation formulation recorded in the Kapoor edition's
        # commentary to 7.26-30: the debilitated planet itself is angular from
        # Lagna or Moon. Keep it explicitly identified so it is not confused
        # with the separate sign-lord conditions in the translated verses.
        for reference, reference_house in (("Lagna", 1), ("Moon", moon_house)):
            if _is_kendra(reference_house, planet_house):
                conditions.append(
                    _condition(
                        f"PD_7_30_DEBILITATED_PLANET_KENDRA_FROM_{reference.upper()}",
                        "7.26-30 commentary",
                        f"The debilitated {planet} is in House {planet_house}, a Kendra from {reference}.",
                        (planet,),
                        (planet_house,),
                    )
                )

        matched_rule_ids = [row["rule_id"] for row in conditions]
        rule_catalog = [
            ("PD_7_26_29_DEBILITATION_LORD_KENDRA_FROM_LAGNA", "Phaladeepika 7.26, 7.29", True),
            ("PD_7_26_29_DEBILITATION_LORD_KENDRA_FROM_MOON", "Phaladeepika 7.26, 7.29", moon_house is not None),
            ("PD_7_26_EXALTED_IN_DEBILITATION_SIGN_KENDRA_FROM_LAGNA", "Phaladeepika 7.26", planet_exalted_here is not None),
            ("PD_7_26_EXALTED_IN_DEBILITATION_SIGN_KENDRA_FROM_MOON", "Phaladeepika 7.26", planet_exalted_here is not None and moon_house is not None),
            ("PD_7_29_EXALTATION_SIGN_LORD_KENDRA_FROM_LAGNA", "Phaladeepika 7.29", True),
            ("PD_7_29_EXALTATION_SIGN_LORD_KENDRA_FROM_MOON", "Phaladeepika 7.29", moon_house is not None),
            ("PD_7_27_LORDS_IN_MUTUAL_KENDRAS", "Phaladeepika 7.27", True),
            ("PD_7_28_DEBILITATED_PLANET_ASPECTED_BY_SIGN_LORD", "Phaladeepika 7.28", True),
            ("PD_7_30_DEBILITATED_PLANET_KENDRA_FROM_LAGNA", "Phaladeepika 7.26-30 commentary", True),
            ("PD_7_30_DEBILITATED_PLANET_KENDRA_FROM_MOON", "Phaladeepika 7.26-30 commentary", moon_house is not None),
        ]
        rules_evaluated = [
            {
                "rule_id": rule_id,
                "reference": reference,
                "applicable": applicable,
                "matched": applicable and rule_id in matched_rule_ids,
            }
            for rule_id, reference, applicable in rule_catalog
        ]

        # A rule may be repeated by Lagna and Moon; preserve both pieces of evidence.
        results[planet] = {
            "planet": planet,
            "is_debilitated": True,
            "debilitation_sign": SIGN_NAMES[debilitation_sign],
            "debilitation_sign_index": debilitation_sign,
            "debilitation_sign_lord": dispositor,
            "planet_exalted_in_debilitation_sign": planet_exalted_here,
            "exaltation_sign_lord": exaltation_sign_lord,
            "neecha_bhanga_present": bool(conditions),
            "raja_yoga_present": bool(conditions),
            "conditions_met": conditions,
            "total_conditions": len(conditions),
            "matched_rule_ids": matched_rule_ids,
            "unmatched_rule_ids": [
                row["rule_id"] for row in rules_evaluated
                if row["applicable"] and not row["matched"]
            ],
            "rules_evaluated": rules_evaluated,
            "classical_result": CLASSICAL_RESULT,
            "source": SOURCE,
        }

    return results


def legacy_reason_ids(result: Dict[str, Any]) -> List[str]:
    """Compatibility aliases used by existing prediction clients."""

    reasons: List[str] = []
    for condition in result.get("conditions_met") or []:
        reasons.extend(condition.get("legacy_rule_ids") or [])
    return list(dict.fromkeys(reasons))
