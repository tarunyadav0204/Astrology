from __future__ import annotations

"""Validated D1-only natal promise facts for the Parashari profile.

This intentionally excludes vargas, Shadbala and Ashtakavarga.  It records
classical relationships and conservative directional factors; it does not
turn a house into a guaranteed event.
"""

from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from calculators.badhaka_calculator import BadhakaCalculator
from calculators.friendship_calculator import FriendshipCalculator

from .contracts import Polarity
from .primitives import CLASSICAL_PLANETS, aspected_houses, planetary_connections, ruled_houses


NATAL_PROMISE_POLICY_VERSION = "2.4.0"

HOUSE_KARAKAS: Dict[int, Tuple[str, ...]] = {
    1: ("Sun",),
    2: ("Jupiter", "Mercury"),
    3: ("Mars",),
    4: ("Moon",),
    5: ("Jupiter",),
    6: ("Mars", "Saturn"),
    7: ("Venus",),
    8: ("Saturn",),
    9: ("Jupiter", "Sun"),
    10: ("Sun", "Mercury", "Saturn"),
    11: ("Jupiter",),
    12: ("Saturn",),
}

EXALTATION_SIGNS = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}
DEBILITATION_SIGNS = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0,
}
NATURAL_BENEFICS = {"Jupiter", "Venus"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
NAKSHATRA_LORD_SEQUENCE = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
)
NAKSHATRA_NAMES = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
)
NODE_PLANETS = {"Rahu", "Ketu"}
FUNCTIONALLY_SUPPORTIVE_HOUSES = {1, 5, 9}
FUNCTIONALLY_CHALLENGING_HOUSES = {3, 6, 8, 11, 12}
DUSTHANA_HOUSES = {6, 8, 12}
KENDRA_HOUSES = {4, 7, 10}
TRIKONA_HOUSES = {5, 9}


def _house_from(reference_house: int, target_house: int) -> int:
    return ((int(target_house) - int(reference_house)) % 12) + 1


def _is_kendra_from(reference_house: int, target_house: int) -> bool:
    return _house_from(reference_house, target_house) in {1, 4, 7, 10}


def _house_lord(chart: Dict[str, Any], house: int) -> str:
    sign = int(chart["houses"][house - 1]["sign"])
    return str(BadhakaCalculator.SIGN_LORDS[sign])


def _neecha_bhanga(chart: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Conservative D1 cancellation conditions with exact provenance.

    Cancellation removes an automatic debilitation penalty; it does not turn a
    debilitated planet into an unqualified benefic or Raja Yoga.
    """

    moon_house = int(chart["planets"]["Moon"]["house"])
    result: Dict[str, Dict[str, Any]] = {}
    for planet, debilitation_sign in DEBILITATION_SIGNS.items():
        placement = chart["planets"].get(planet)
        if not placement or int(placement["sign"]) != debilitation_sign:
            continue
        reasons: List[str] = []
        debilitation_lord = BadhakaCalculator.SIGN_LORDS[debilitation_sign]
        exaltation_lord = BadhakaCalculator.SIGN_LORDS[EXALTATION_SIGNS[planet]]
        for role, lord in (
            ("debilitation_sign_lord", debilitation_lord),
            ("exaltation_sign_lord", exaltation_lord),
        ):
            lord_house = int(chart["planets"][lord]["house"])
            if _is_kendra_from(1, lord_house):
                reasons.append(f"{role}_in_kendra_from_lagna")
            if _is_kendra_from(moon_house, lord_house):
                reasons.append(f"{role}_in_kendra_from_moon")
        if planetary_connections(chart, planet, debilitation_lord):
            reasons.append("debilitated_planet_connected_to_sign_lord")
        result[planet] = {
            "cancelled": bool(reasons),
            "reasons": tuple(dict.fromkeys(reasons)),
            "debilitation_sign_lord": debilitation_lord,
            "exaltation_sign_lord": exaltation_lord,
        }
    return result


def _validated_yogas(
    chart: Dict[str, Any], cancellations: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], ...]:
    yogas: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def add(key: str, name: str, planets: Iterable[str], houses: Iterable[int], rule: str) -> None:
        if key in seen:
            return
        seen.add(key)
        yogas.append({
            "key": key,
            "name": name,
            "planets": tuple(sorted(set(planets))),
            "houses": tuple(sorted(set(int(house) for house in houses))),
            "rule": rule,
        })

    # Kendra-trikona sambandha, including one planet owning both roles.
    for kendra in (1, 4, 7, 10):
        for trikona in (1, 5, 9):
            if kendra == trikona:
                continue
            first, second = _house_lord(chart, kendra), _house_lord(chart, trikona)
            relations = planetary_connections(chart, first, second)
            if relations:
                add(
                    f"kendra_trikona:{kendra}:{trikona}:{first}:{second}",
                    "Kendra-Trikona sambandha",
                    (first, second),
                    (kendra, trikona),
                    ",".join(relations),
                )

    for key, name, houses in (
        ("dhana_2_11", "Dhana sambandha", (2, 11)),
        ("dharma_karma_9_10", "Dharma-Karma sambandha", (9, 10)),
    ):
        first, second = (_house_lord(chart, house) for house in houses)
        relations = planetary_connections(chart, first, second)
        if relations:
            add(key, name, (first, second), houses, ",".join(relations))

    own_or_exalted = {
        "Mars": {0, 7, 9},
        "Mercury": {2, 5},
        "Jupiter": {8, 11, 3},
        "Venus": {1, 6, 11},
        "Saturn": {9, 10, 6},
    }
    names = {
        "Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
        "Venus": "Malavya", "Saturn": "Shasha",
    }
    for planet, signs in own_or_exalted.items():
        placement = chart["planets"][planet]
        if int(placement["house"]) in {1, 4, 7, 10} and int(placement["sign"]) in signs:
            add(
                f"mahapurusha:{planet}",
                f"{names[planet]} Mahapurusha Yoga",
                (planet,),
                (int(placement["house"]),),
                "planet_in_kendra_in_own_or_exaltation_sign",
            )

    for planet, cancellation in cancellations.items():
        if cancellation["cancelled"]:
            add(
                f"neecha_bhanga:{planet}",
                "Neecha Bhanga",
                (planet,),
                ruled_houses(chart, planet),
                ",".join(cancellation["reasons"]),
            )
    return tuple(yogas)


def _moon_phase(chart: Dict[str, Any]) -> Dict[str, Any]:
    separation = (
        float(chart["planets"]["Moon"]["longitude"])
        - float(chart["planets"]["Sun"]["longitude"])
    ) % 360.0
    return {
        "separation": round(separation, 4),
        "phase": "waxing" if 0.0 < separation < 180.0 else "waning",
    }


def _natural_polarity(chart: Dict[str, Any], planet: str, phase: Dict[str, Any]) -> Polarity:
    if planet in NATURAL_BENEFICS:
        return Polarity.SUPPORTIVE
    if planet == "Moon":
        return (
            Polarity.SUPPORTIVE
            if phase["phase"] == "waxing" else Polarity.CHALLENGING
        )
    if planet == "Mercury":
        house = int(chart["planets"][planet]["house"])
        associates = {
            name for name, data in chart["planets"].items()
            if name != planet and int(data["house"]) == house
        }
        benefics = associates.intersection(NATURAL_BENEFICS | {"Moon"})
        malefics = associates.intersection(NATURAL_MALEFICS)
        if benefics and not malefics:
            return Polarity.SUPPORTIVE
        if malefics and not benefics:
            return Polarity.CHALLENGING
        return Polarity.NEUTRAL
    if planet in NATURAL_MALEFICS:
        return Polarity.CHALLENGING
    return Polarity.NEUTRAL


def _natural_nature(chart: Dict[str, Any], planet: str, phase: Dict[str, Any]) -> str:
    """Name the actual natural-status fact used by `_natural_polarity`."""

    polarity = _natural_polarity(chart, planet, phase)
    if planet == "Moon":
        return f"{phase['phase']}_moon_{polarity.value}"
    if planet == "Mercury":
        return f"associated_mercury_{polarity.value}"
    if planet in NATURAL_BENEFICS:
        return "natural_benefic"
    if planet in NATURAL_MALEFICS:
        return "natural_malefic"
    return "natural_neutral"


def _natural_nature_context(chart: Dict[str, Any], planet: str) -> Dict[str, Any]:
    if planet != "Mercury":
        return {}
    house = int(chart["planets"][planet]["house"])
    associates = {
        name for name, data in chart["planets"].items()
        if name != planet and int(data["house"]) == house
    }
    return {
        "conditioning_associations": tuple(sorted(associates)),
        "benefic_associations": tuple(sorted(associates.intersection(NATURAL_BENEFICS | {"Moon"}))),
        "malefic_associations": tuple(sorted(associates.intersection(NATURAL_MALEFICS))),
    }


def _functional_lordship(chart: Dict[str, Any], planet: str) -> Dict[str, Any]:
    owned = tuple(sorted(ruled_houses(chart, planet)))
    owned_set = set(owned)
    supportive = tuple(sorted(owned_set & FUNCTIONALLY_SUPPORTIVE_HOUSES))
    challenging = tuple(sorted(owned_set & FUNCTIONALLY_CHALLENGING_HOUSES))
    placement_house = int(chart["planets"][planet]["house"])
    reversal_houses = tuple(sorted(
        set(challenging) & DUSTHANA_HOUSES
        if placement_house in DUSTHANA_HOUSES else set()
    ))
    effective_challenging = tuple(sorted(set(challenging) - set(reversal_houses)))
    yogakaraka = bool(owned_set & KENDRA_HOUSES) and bool(owned_set & TRIKONA_HOUSES)
    if yogakaraka:
        polarity = Polarity.SUPPORTIVE
        role = "yogakaraka"
    elif supportive and effective_challenging:
        polarity = Polarity.MIXED
        role = "mixed_lordship"
    elif supportive:
        polarity = Polarity.SUPPORTIVE
        role = "functional_supportive"
    elif effective_challenging:
        polarity = Polarity.CHALLENGING
        role = "functional_challenging"
    else:
        polarity = Polarity.NEUTRAL
        role = "functional_neutral"
    original_directional_count = len(supportive) + len(challenging)
    effective_directional_count = len(supportive) + len(effective_challenging)
    return {
        "polarity": polarity,
        "role": role,
        "ruled_houses": owned,
        "supportive_houses": supportive,
        "challenging_houses": challenging,
        "effective_challenging_houses": effective_challenging,
        "reversal_houses": reversal_houses,
        "directional_weight_multiplier": (
            effective_directional_count / original_directional_count
            if original_directional_count else 1.0
        ),
        "yogakaraka": yogakaraka,
    }


def _relation_polarity(relation: str) -> Polarity:
    if relation in {"self", "great_friend", "friend"}:
        return Polarity.SUPPORTIVE
    if relation in {"enemy", "great_enemy"}:
        return Polarity.CHALLENGING
    return Polarity.NEUTRAL


def _natural_relation(calculator: FriendshipCalculator, planet: str, other: str) -> str:
    if planet == other:
        return "self"
    if other in calculator.NATURAL_FRIENDS.get(planet, ()):
        return "friend"
    if other in calculator.NATURAL_ENEMIES.get(planet, ()):
        return "enemy"
    return "neutral"


def _nakshatra_lord(longitude: float) -> Tuple[int, str, str]:
    index = min(26, int((float(longitude) % 360.0) / (40.0 / 3.0)))
    return index + 1, NAKSHATRA_NAMES[index], NAKSHATRA_LORD_SEQUENCE[index % 9]


def _condition_polarity(
    planet: str,
    dignities: Dict[str, Any],
    cancellations: Dict[str, Dict[str, Any]],
) -> Polarity:
    condition = dignities.get(planet, {})
    dignity = str(condition.get("dignity") or "neutral")
    if dignity in {"exalted", "moolatrikona", "own_sign"}:
        return Polarity.SUPPORTIVE
    if dignity == "debilitated" and not cancellations.get(planet, {}).get("cancelled"):
        return Polarity.CHALLENGING
    if str(condition.get("combustion_status") or "normal") not in {"normal", "cazimi"}:
        return Polarity.CHALLENGING
    return Polarity.NEUTRAL


def _dusthana_reversal_context(
    chart: Dict[str, Any],
    planet: str,
    target_house: int,
    dignities: Dict[str, Any],
    cancellations: Dict[str, Dict[str, Any]],
    friendship: FriendshipCalculator,
) -> Dict[str, Any] | None:
    placement = chart["planets"][planet]
    placement_house = int(placement["house"])
    owned_houses = set(ruled_houses(chart, planet))
    reversed_houses = tuple(sorted(owned_houses & DUSTHANA_HOUSES))
    if placement_house not in DUSTHANA_HOUSES or not reversed_houses:
        return None

    yoga_names = {
        6: "Harsha-type",
        8: "Sarala-type",
        12: "Vimala-type",
    }
    associates = tuple(sorted(
        other for other, data in chart["planets"].items()
        if other != planet
        and other in CLASSICAL_PLANETS
        and int(data["sign"]) == int(placement["sign"])
    ))
    afflictions: List[str] = []
    qualifications: List[str] = []
    dignity = str(dignities.get(planet, {}).get("dignity") or "neutral")
    combustion = str(dignities.get(planet, {}).get("combustion_status") or "normal")
    if dignity == "debilitated" and not cancellations.get(planet, {}).get("cancelled"):
        afflictions.append("uncancelled_debilitation")
    if combustion not in {"normal", "cazimi"}:
        afflictions.append("combustion")
    node_associates = tuple(sorted(set(associates) & NODE_PLANETS))
    malefic_associates = tuple(sorted(set(associates) & NATURAL_MALEFICS))
    if node_associates:
        afflictions.append("node_conjunction")
    elif malefic_associates:
        afflictions.append("natural_malefic_conjunction")
    if associates and not afflictions:
        qualifications.append("planetary_conjunction")

    dispositor = str(BadhakaCalculator.SIGN_LORDS[int(placement["sign"])])
    host_relation = "self"
    if dispositor != planet:
        host_relation = friendship.calculate_compound_relation(
            planet,
            dispositor,
            int(placement["sign"]),
            int(chart["planets"][dispositor]["sign"]),
        )
        if host_relation in {"enemy", "great_enemy"}:
            afflictions.append("hostile_dispositor_relationship")
    other_lordships = tuple(sorted(owned_houses - DUSTHANA_HOUSES))
    if other_lordships:
        qualifications.append("additional_non_dusthana_lordship")

    if afflictions:
        strength = "afflicted"
        mitigation_weight = 0.25
    elif qualifications:
        strength = "qualified"
        mitigation_weight = 0.5
    else:
        strength = "strong"
        mitigation_weight = 0.75
    return {
        "classification": strength,
        "yoga_types": tuple(yoga_names[house] for house in reversed_houses),
        "reversed_lordships": reversed_houses,
        "placement_house": placement_house,
        "target_house": target_house,
        "other_lordships": other_lordships,
        "associations": associates,
        "node_associations": node_associates,
        "malefic_associations": malefic_associates,
        "dispositor": dispositor,
        "natural_dispositor_relation": _natural_relation(friendship, planet, dispositor),
        "compound_dispositor_relation": host_relation,
        "dignity": dignity,
        "combustion": combustion,
        "afflictions": tuple(dict.fromkeys(afflictions)),
        "qualifications": tuple(dict.fromkeys(qualifications)),
        "mitigation_weight": mitigation_weight,
        "rule": "dusthana_lord_in_dusthana_reduces_only_its_corresponding_dusthana_penalty",
    }


def _score_polarity(
    supportive: float, challenging: float
) -> Polarity:
    if supportive == challenging == 0:
        return Polarity.NEUTRAL
    if supportive >= challenging * 1.6:
        return Polarity.SUPPORTIVE
    if challenging >= supportive * 1.6:
        return Polarity.CHALLENGING
    return Polarity.MIXED


def _polarity_parts(polarity: Polarity, weight: float = 1.0) -> Tuple[float, float]:
    if polarity == Polarity.SUPPORTIVE:
        return weight, 0.0
    if polarity == Polarity.CHALLENGING:
        return 0.0, weight
    if polarity == Polarity.MIXED:
        return weight * 0.5, weight * 0.5
    return 0.0, 0.0


def _node_conditioned_context(
    chart: Dict[str, Any],
    node: str,
    target_house: int,
    phase: Dict[str, Any],
    dignities: Dict[str, Any],
    cancellations: Dict[str, Dict[str, Any]],
    friendship: FriendshipCalculator,
) -> Dict[str, Any]:
    """Resolve a node once through its dispositor and conjunct classical grahas."""

    placement = chart["planets"][node]
    dispositor = str(BadhakaCalculator.SIGN_LORDS[int(placement["sign"])])
    roles_by_planet: Dict[str, Set[str]] = {dispositor: {"dispositor"}}
    for other, data in chart["planets"].items():
        if (
            other != node
            and other not in NODE_PLANETS
            and other in CLASSICAL_PLANETS
            and int(data["sign"]) == int(placement["sign"])
        ):
            roles_by_planet.setdefault(other, set()).add("conjunct")

    node_supportive = 0.0
    node_challenging = 1.0  # Nodes retain their classical natural-malefic baseline.
    influencers: List[Dict[str, Any]] = []
    for planet, roles in sorted(
        roles_by_planet.items(), key=lambda item: ("dispositor" not in item[1], item[0])
    ):
        components: List[Dict[str, Any]] = []
        planet_supportive = 0.0
        planet_challenging = 0.0

        natural = _natural_polarity(chart, planet, phase)
        functional = _functional_lordship(chart, planet)
        condition = _condition_polarity(planet, dignities, cancellations)
        component_specs = (
            ("natural_nature", natural, 1.0, {"natural_nature": _natural_nature(chart, planet, phase)}),
            ("functional_lordship", functional["polarity"], functional["directional_weight_multiplier"], {
                "functional_role": functional["role"],
                "ruled_houses": functional["ruled_houses"],
                "supportive_houses": functional["supportive_houses"],
                "challenging_houses": functional["challenging_houses"],
                "effective_challenging_houses": functional["effective_challenging_houses"],
                "reversal_houses": functional["reversal_houses"],
                "yogakaraka": functional["yogakaraka"],
            }),
            ("placement_condition", condition, 1.0, {
                "dignity": dignities.get(planet, {}).get("dignity", "neutral"),
                "combustion": dignities.get(planet, {}).get("combustion_status", "normal"),
                "neecha_bhanga": cancellations.get(planet, {}).get("cancelled", False),
            }),
        )
        for source, polarity, component_weight, facts in component_specs:
            support_part, challenge_part = _polarity_parts(polarity, component_weight)
            planet_supportive += support_part
            planet_challenging += challenge_part
            components.append({
                "source": source,
                "polarity": polarity.value,
                "weight": component_weight,
                "facts": facts,
            })

        reversal = _dusthana_reversal_context(
            chart, planet, target_house, dignities, cancellations, friendship
        )
        if reversal:
            planet_supportive += reversal["mitigation_weight"]
            components.append({
                "source": "dusthana_reversal_mitigation",
                "polarity": Polarity.SUPPORTIVE.value,
                "weight": reversal["mitigation_weight"],
                "facts": reversal,
            })

        planet_placement = chart["planets"][planet]
        host = str(BadhakaCalculator.SIGN_LORDS[int(planet_placement["sign"])])
        if host != planet:
            host_relation = friendship.calculate_compound_relation(
                planet,
                host,
                int(planet_placement["sign"]),
                int(chart["planets"][host]["sign"]),
            )
            host_polarity = _relation_polarity(host_relation)
            support_part, challenge_part = _polarity_parts(host_polarity, 0.75)
            planet_supportive += support_part
            planet_challenging += challenge_part
            components.append({
                "source": "placement_dispositor_relationship",
                "polarity": host_polarity.value,
                "weight": 0.75,
                "facts": {
                    "dispositor": host,
                    "natural_relation": _natural_relation(friendship, planet, host),
                    "compound_relation": host_relation,
                },
            })

        influence_weight = 1.0 if "dispositor" in roles else 0.75
        node_supportive += planet_supportive * influence_weight
        node_challenging += planet_challenging * influence_weight
        influencers.append({
            "planet": planet,
            "roles": tuple(sorted(roles)),
            "polarity": _score_polarity(planet_supportive, planet_challenging).value,
            "supportive_score": round(planet_supportive, 3),
            "challenging_score": round(planet_challenging, 3),
            "influence_weight": influence_weight,
            "components": tuple(components),
        })

    polarity = _score_polarity(node_supportive, node_challenging)
    return {
        "base_nature": "natural_malefic",
        "dispositor": dispositor,
        "dispositor_house": int(chart["planets"][dispositor]["house"]),
        "associated_planets": tuple(
            row["planet"] for row in influencers if "conjunct" in row["roles"]
        ),
        "influencers": tuple(influencers),
        "supportive_score": round(node_supportive, 3),
        "challenging_score": round(node_challenging, 3),
        "resolved_polarity": polarity.value,
        "placement_house": int(placement["house"]),
        "placement_sign": int(placement["sign"]),
        "placement_sign_name": placement.get("sign_name"),
        "target_house": target_house,
    }


def _dispositor_chain(chart: Dict[str, Any], planet: str) -> Tuple[str, ...]:
    chain = [planet]
    current = planet
    for _ in range(9):
        sign = int(chart["planets"][current]["sign"])
        dispositor = str(BadhakaCalculator.SIGN_LORDS[sign])
        chain.append(dispositor)
        if dispositor == current or dispositor in chain[:-1]:
            break
        current = dispositor
    return tuple(chain)


def _promise_tone(factors: Sequence[Dict[str, Any]]) -> Tuple[Polarity, float, float]:
    supportive = sum(
        float(row["weight"]) for row in factors if row["polarity"] == "supportive"
    )
    challenging = sum(
        float(row["weight"]) for row in factors if row["polarity"] == "challenging"
    )
    if supportive == challenging == 0:
        tone = Polarity.NEUTRAL
    elif supportive >= challenging * 1.6:
        tone = Polarity.SUPPORTIVE
    elif challenging >= supportive * 1.6:
        tone = Polarity.CHALLENGING
    else:
        tone = Polarity.MIXED
    return tone, supportive, challenging


def build_natal_promises(
    chart: Dict[str, Any],
    dignities: Dict[str, Any],
    yogi_points: Dict[str, Any] | None = None,
    gandanta: Dict[str, Any] | None = None,
) -> Tuple[Tuple[Dict[str, Any], ...], Tuple[Dict[str, Any], ...]]:
    cancellations = _neecha_bhanga(chart)
    yogas = _validated_yogas(chart, cancellations)
    phase = _moon_phase(chart)
    yogi_points = yogi_points or {}
    gandanta = gandanta or {}
    friendship = FriendshipCalculator()
    gandanta_planets = {
        row.get("planet"): row.get("gandanta_info") or {}
        for row in gandanta.get("planets_in_gandanta", ())
    }
    yogi_lord = (yogi_points.get("yogi") or {}).get("lord")
    avayogi_lord = (yogi_points.get("avayogi") or {}).get("lord")
    dagdha = yogi_points.get("dagdha_rashi") or {}
    tithi_shunya = yogi_points.get("tithi_shunya_rashi") or {}
    overlap = bool((yogi_points.get("avayogi_tithi_shunya_overlap") or {}).get("is_active"))
    promises: List[Dict[str, Any]] = []
    for house in range(1, 13):
        lord = _house_lord(chart, house)
        occupants = tuple(sorted(
            planet for planet, data in chart["planets"].items()
            if planet in CLASSICAL_PLANETS and int(data["house"]) == house
        ))
        aspectors = tuple(sorted(
            planet for planet, data in chart["planets"].items()
            if planet in CLASSICAL_PLANETS
            and house in aspected_houses(planet, int(data["house"]))
        ))
        factors: List[Dict[str, Any]] = []

        lord_polarity = _condition_polarity(lord, dignities, cancellations)
        factors.append({
            "source": "house_lord_condition",
            "planet": lord,
            "polarity": lord_polarity.value,
            "weight": 1.5,
            "facts": {
                "dignity": dignities.get(lord, {}).get("dignity", "neutral"),
                "combustion": dignities.get(lord, {}).get("combustion_status", "normal"),
                "neecha_bhanga": cancellations.get(lord, {}).get("cancelled", False),
                "placement_house": int(chart["planets"][lord]["house"]),
            },
        })
        for role, planets, weight in (
            ("occupant", occupants, 1.0),
            ("aspector", aspectors, 0.75),
        ):
            for planet in planets:
                functional = _functional_lordship(chart, planet)
                factors.append({
                    "source": f"{role}_functional_lordship",
                    "planet": planet,
                    "polarity": functional["polarity"].value,
                    "weight": (
                        1.25 if functional["yogakaraka"]
                        else weight * functional["directional_weight_multiplier"]
                    ),
                    "facts": {
                        "relation": role,
                        "functional_role": functional["role"],
                        "ruled_houses": functional["ruled_houses"],
                        "supportive_houses": functional["supportive_houses"],
                        "challenging_houses": functional["challenging_houses"],
                        "effective_challenging_houses": functional["effective_challenging_houses"],
                        "reversal_houses": functional["reversal_houses"],
                        "directional_weight_multiplier": functional["directional_weight_multiplier"],
                        "yogakaraka": functional["yogakaraka"],
                        "placement_house": int(chart["planets"][planet]["house"]),
                        "target_house": house,
                    },
                })
                if planet in NODE_PLANETS:
                    node_context = _node_conditioned_context(
                        chart, planet, house, phase, dignities, cancellations, friendship
                    )
                    factors.append({
                        "source": "node_conditioned_influence",
                        "planet": planet,
                        "polarity": node_context["resolved_polarity"],
                        "weight": weight,
                        "facts": {"relation": role, **node_context},
                    })
                else:
                    factors.append({
                        "source": f"{role}_natural_influence",
                        "planet": planet,
                        "polarity": _natural_polarity(chart, planet, phase).value,
                        "weight": weight,
                        "facts": {
                            "relation": role,
                            "natural_nature": _natural_nature(chart, planet, phase),
                            **_natural_nature_context(chart, planet),
                            "functional_role": functional["role"],
                            "ruled_houses": functional["ruled_houses"],
                            "supportive_houses": functional["supportive_houses"],
                            "challenging_houses": functional["challenging_houses"],
                            "yogakaraka": functional["yogakaraka"],
                            "placement_house": int(chart["planets"][planet]["house"]),
                            "target_house": house,
                            "aspect_distance": (
                                ((house - int(chart["planets"][planet]["house"])) % 12) + 1
                                if role == "aspector" else None
                            ),
                            "moon_phase": phase if planet == "Moon" else None,
                        },
                    })
                factors.append({
                    "source": f"{role}_condition",
                    "planet": planet,
                    "polarity": _condition_polarity(
                        planet, dignities, cancellations
                    ).value,
                    "weight": weight,
                    "facts": {
                        "relation": role,
                        "dignity": dignities.get(planet, {}).get("dignity", "neutral"),
                        "combustion": dignities.get(planet, {}).get(
                            "combustion_status", "normal"
                        ),
                        "neecha_bhanga": cancellations.get(planet, {}).get(
                            "cancelled", False
                        ),
                    },
                })

        relevant_roles: Dict[str, Set[str]] = {lord: {"house_lord"}}
        for role, planets in (("occupant", occupants), ("aspector", aspectors)):
            for planet in planets:
                relevant_roles.setdefault(planet, set()).add(role)
        for planet, roles in sorted(relevant_roles.items()):
            placement = chart["planets"][planet]
            role_names = tuple(sorted(roles))
            if planet not in NODE_PLANETS:
                dispositor = str(BadhakaCalculator.SIGN_LORDS[int(placement["sign"])])
                if dispositor != planet:
                    host_relation = friendship.calculate_compound_relation(
                        planet,
                        dispositor,
                        int(placement["sign"]),
                        int(chart["planets"][dispositor]["sign"]),
                    )
                    factors.append({
                        "source": "placement_dispositor_relationship",
                        "planet": planet,
                        "polarity": _relation_polarity(host_relation).value,
                        "weight": 0.75,
                        "facts": {
                            "roles": role_names,
                            "dispositor": dispositor,
                            "dispositor_house": int(chart["planets"][dispositor]["house"]),
                            "natural_relation": _natural_relation(friendship, planet, dispositor),
                            "compound_relation": host_relation,
                            "placement_sign": int(placement["sign"]),
                            "placement_sign_name": placement.get("sign_name"),
                            "placement_house": int(placement["house"]),
                            "target_house": house,
                        },
                    })
                reversal = _dusthana_reversal_context(
                    chart, planet, house, dignities, cancellations, friendship
                )
                if reversal:
                    factors.append({
                        "source": "dusthana_reversal_mitigation",
                        "planet": planet,
                        "polarity": Polarity.SUPPORTIVE.value,
                        "weight": reversal["mitigation_weight"],
                        "facts": {
                            "roles": role_names,
                            **reversal,
                        },
                    })
            direct_house_lord_relations = (
                planetary_connections(chart, planet, lord)
                if planet != lord and planet not in NODE_PLANETS and lord not in NODE_PLANETS
                else ()
            )
            if direct_house_lord_relations:
                relation = friendship.calculate_compound_relation(
                    planet,
                    lord,
                    int(placement["sign"]),
                    int(chart["planets"][lord]["sign"]),
                )
                factors.append({
                    "source": "fivefold_friendship_with_house_lord",
                    "planet": planet,
                    "polarity": _relation_polarity(relation).value,
                    "weight": 0.75,
                    "facts": {
                        "roles": role_names,
                        "house_lord": lord,
                        "compound_relation": relation,
                        "direct_relations": direct_house_lord_relations,
                        "placement_house": int(placement["house"]),
                        "target_house": house,
                    },
                })
            nakshatra_number, nakshatra_name, nakshatra_lord = _nakshatra_lord(float(placement["longitude"]))
            if planet not in NODE_PLANETS and nakshatra_lord not in NODE_PLANETS:
                nakshatra_relation = (
                    "self" if planet == nakshatra_lord else friendship.calculate_compound_relation(
                        planet,
                        nakshatra_lord,
                        int(placement["sign"]),
                        int(chart["planets"][nakshatra_lord]["sign"]),
                    )
                )
                factors.append({
                    "source": "fivefold_friendship_with_nakshatra_lord",
                    "planet": planet,
                    "polarity": _relation_polarity(nakshatra_relation).value,
                    "weight": 0.75,
                    "facts": {
                        "roles": role_names,
                        "nakshatra_number": nakshatra_number,
                        "nakshatra_name": nakshatra_name,
                        "nakshatra_lord": nakshatra_lord,
                        "compound_relation": nakshatra_relation,
                        "placement_house": int(placement["house"]),
                        "target_house": house,
                    },
                })
            if planet in gandanta_planets:
                factors.append({
                    "source": "planet_gandanta",
                    "planet": planet,
                    "polarity": Polarity.CHALLENGING.value,
                    "weight": 1.0,
                    "facts": {
                        "roles": role_names,
                        "placement_house": int(placement["house"]),
                        "target_house": house,
                        **gandanta_planets[planet],
                    },
                })
            for source, special_lord, polarity, details in (
                ("yogi_lord", yogi_lord, Polarity.SUPPORTIVE, yogi_points.get("yogi") or {}),
                ("avayogi_lord", avayogi_lord, Polarity.MIXED if overlap else Polarity.CHALLENGING, yogi_points.get("avayogi") or {}),
                ("dagdha_rashi_lord", dagdha.get("lord"), Polarity.CHALLENGING, dagdha),
                ("tithi_shunya_lord", tithi_shunya.get("lord"), Polarity.MIXED if overlap and planet == avayogi_lord else Polarity.CHALLENGING, tithi_shunya),
            ):
                if special_lord and planet == special_lord:
                    factors.append({
                        "source": source,
                        "planet": planet,
                        "polarity": polarity.value,
                        "weight": 0.75,
                        "facts": {
                            "roles": role_names,
                            "placement_house": int(placement["house"]),
                            "target_house": house,
                            "special_sign": details.get("sign"),
                            "special_sign_name": details.get("sign_name"),
                            "avayogi_tithi_shunya_overlap": overlap,
                        },
                    })
            if dagdha.get("sign") is not None and int(placement["sign"]) == int(dagdha["sign"]):
                factors.append({
                    "source": "planet_in_dagdha_rashi",
                    "planet": planet,
                    "polarity": Polarity.CHALLENGING.value,
                    "weight": 0.75,
                    "facts": {"roles": role_names, "placement_house": int(placement["house"]), "target_house": house, "dagdha_sign": dagdha.get("sign"), "dagdha_sign_name": dagdha.get("sign_name")},
                })
            if tithi_shunya.get("sign") is not None and int(placement["sign"]) == int(tithi_shunya["sign"]):
                factors.append({
                    "source": "planet_in_tithi_shunya_rashi",
                    "planet": planet,
                    "polarity": (Polarity.MIXED if overlap and planet == avayogi_lord else Polarity.CHALLENGING).value,
                    "weight": 0.75,
                    "facts": {"roles": role_names, "placement_house": int(placement["house"]), "target_house": house, "tithi_shunya_sign": tithi_shunya.get("sign"), "tithi_shunya_sign_name": tithi_shunya.get("sign_name"), "avayogi_overlap": overlap},
                })

        if house == 1 and (gandanta.get("lagna_gandanta") or {}).get("is_gandanta"):
            factors.append({
                "source": "lagna_gandanta",
                "planet": "Lagna",
                "polarity": Polarity.CHALLENGING.value,
                "weight": 1.0,
                "facts": {"target_house": 1, **((gandanta.get("lagna_gandanta") or {}).get("gandanta_info") or {})},
            })

        chains = {planet: _dispositor_chain(chart, planet) for planet in (lord, *occupants)}
        for origin, chain in chains.items():
            final = chain[-1]
            factors.append({
                "source": "final_dispositor_condition",
                "planet": final,
                "polarity": _condition_polarity(final, dignities, cancellations).value,
                "weight": 0.75,
                "facts": {
                    "origin": origin,
                    "chain": chain,
                    "dignity": dignities.get(final, {}).get("dignity", "neutral"),
                    "combustion": dignities.get(final, {}).get("combustion_status", "normal"),
                    "neecha_bhanga": cancellations.get(final, {}).get("cancelled", False),
                    "placement_house": int(chart["planets"][final]["house"]),
                    "target_house": house,
                },
            })

        karakas = HOUSE_KARAKAS[house]
        for planet in karakas:
            factors.append({
                "source": "natural_karaka_condition",
                "planet": planet,
                "polarity": _condition_polarity(planet, dignities, cancellations).value,
                "weight": 0.75,
                "facts": {
                    "karaka_for_house": house,
                    "dignity": dignities.get(planet, {}).get("dignity", "neutral"),
                    "combustion": dignities.get(planet, {}).get("combustion_status", "normal"),
                    "neecha_bhanga": cancellations.get(planet, {}).get("cancelled", False),
                    "placement_house": int(chart["planets"][planet]["house"]),
                },
            })

        relevant_yogas = tuple(
            yoga for yoga in yogas if house in set(yoga["houses"])
        )
        tone, supportive, challenging = _promise_tone(factors)
        promises.append({
            "policy_version": NATAL_PROMISE_POLICY_VERSION,
            "house": house,
            "lord": lord,
            "occupants": occupants,
            "aspecting_planets": aspectors,
            "dispositor_chains": chains,
            "karakas": karakas,
            "yogas": tuple(yoga["key"] for yoga in relevant_yogas),
            "cancellations": tuple(
                {"planet": planet, **value}
                for planet, value in cancellations.items()
                if value["cancelled"] and (
                    planet == lord or planet in occupants or planet in karakas
                )
            ),
            "moon_phase": phase,
            "tone": tone.value,
            "supportive_weight": round(supportive, 3),
            "challenging_weight": round(challenging, 3),
            "factors": tuple(factors),
        })
    return tuple(promises), yogas
