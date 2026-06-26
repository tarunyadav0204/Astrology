from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from calculators.ashtakavarga import AshtakavargaCalculator
from calculators.chart_calculator import ChartCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.house_analyzer import HouseAnalyzer
from calculators.transit_calculator import TransitCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.yogi_calculator import YogiCalculator
from shared.dasha_calculator import DashaCalculator


RELATED_CHARTS = {
    2: {"id": "hora", "name": "Hora (D2)"},
    4: {"id": "chaturthamsa", "name": "Chaturthamsa (D4)"},
    5: {"id": "saptamsa", "name": "Saptamsa (D7)"},
    7: {"id": "navamsa", "name": "Navamsa (D9)"},
    9: {"id": "vimsamsa", "name": "Vimsamsa (D20)"},
    10: {"id": "dashamsa", "name": "Dasamsa (D10)"},
    12: {"id": "dwadashamsa", "name": "Dwadashamsa (D12)"},
}

CHART_DIVISIONS = {
    "lagna": None,
    "hora": 2,
    "drekkana": 3,
    "chaturthamsa": 4,
    "saptamsa": 7,
    "navamsa": 9,
    "dashamsa": 10,
    "dasamsa": 10,
    "dwadashamsa": 12,
    "dwadasamsa": 12,
    "shodasamsa": 16,
    "shodamsa": 16,
    "vimsamsa": 20,
    "chaturvimsamsa": 24,
    "saptavimshamsa": 27,
    "trimsamsa": 30,
    "khavedamsa": 40,
    "akshavedamsa": 45,
    "shashtiamsa": 60,
    "shastiamsa": 60,
}

BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}
MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
NODE_PLANETS = {"Rahu", "Ketu"}
NAKSHATRA_LORDS = {
    1: "Ketu", 2: "Venus", 3: "Sun", 4: "Moon", 5: "Mars", 6: "Rahu", 7: "Jupiter",
    8: "Saturn", 9: "Mercury", 10: "Ketu", 11: "Venus", 12: "Sun", 13: "Moon",
    14: "Mars", 15: "Rahu", 16: "Jupiter", 17: "Saturn", 18: "Mercury", 19: "Ketu",
    20: "Venus", 21: "Sun", 22: "Moon", 23: "Mars", 24: "Rahu", 25: "Jupiter",
    26: "Saturn", 27: "Mercury",
}
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
    4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
    8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
NATURAL_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
    "Rahu": {"Venus", "Saturn", "Mercury"},
    "Ketu": {"Mars", "Sun", "Moon"},
}
NATURAL_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
    "Rahu": {"Sun", "Moon", "Mars"},
    "Ketu": {"Sun", "Moon", "Venus"},
}
NEGATIVE_YOGA_KEYWORDS = (
    "dosha",
    "dosh",
    "affliction",
    "dainya",
    "khala",
    "obstacle",
    "pitra",
    "kaal sarp",
    "mangal",
)
EXPLICIT_DOSHA_YOGA_NAMES = {
    "mangal dosha",
    "kaal sarp dosha",
    "pitra dosha",
}


def _birth_obj(birth_data: Dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        name=birth_data.get("name", "Unknown"),
        date=birth_data.get("date"),
        time=birth_data.get("time"),
        latitude=float(birth_data.get("latitude", 0)),
        longitude=float(birth_data.get("longitude", 0)),
        timezone=birth_data.get("timezone", ""),
        place=birth_data.get("place", ""),
        gender=birth_data.get("gender", ""),
        relation=birth_data.get("relation", "other"),
    )


def _normalize_chart_data(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(chart_data, dict) and isinstance(chart_data.get("divisional_chart"), dict):
        return chart_data["divisional_chart"]
    return chart_data


def _normalize_transit_chart_data(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich TransitCalculator output so HouseAnalyzer can read planet house placements."""
    sign_names = ChartCalculator.SIGN_NAMES
    houses = chart_data.get("houses") or []
    if not houses:
        return chart_data

    ascendant_sign = int(houses[0].get("sign", 0))
    normalized_houses = []
    for house in houses:
        sign = int(house.get("sign", 0))
        normalized_houses.append({
            **house,
            "sign_name": sign_names[sign] if 0 <= sign < 12 else "Unknown",
        })

    normalized_planets: Dict[str, Any] = {}
    for planet_name, planet_data in (chart_data.get("planets") or {}).items():
        sign = int(planet_data.get("sign", int(planet_data.get("longitude", 0) / 30)))
        house_number = ((sign - ascendant_sign) % 12) + 1
        normalized_planets[planet_name] = {
            **planet_data,
            "sign": sign,
            "sign_name": sign_names[sign] if 0 <= sign < 12 else "Unknown",
            "house": house_number,
        }

    return {
        **chart_data,
        "planets": normalized_planets,
        "houses": normalized_houses,
    }


def _factor(label: str, tone: str, category: str) -> Dict[str, str]:
    return {"label": label, "tone": tone, "category": category}


def _relation_label(relation: str) -> Optional[str]:
    mapping = {
        "great_friend": "strong temporal support with the sign owner",
        "friend": "friendly support with the sign owner",
        "neutral": "neutral support with the sign owner",
        "enemy": "friction with the sign owner",
        "great_enemy": "strong friction with the sign owner",
    }
    return mapping.get(relation)


def _nakshatra_lord_from_longitude(longitude: Optional[float]) -> Optional[str]:
    if longitude is None:
        return None
    nakshatra_num = int(float(longitude) / 13.3333333333) + 1
    nakshatra_num = max(1, min(27, nakshatra_num))
    return NAKSHATRA_LORDS.get(nakshatra_num)


def _natural_relationship(planet: str, other: Optional[str]) -> Optional[str]:
    if not other:
        return None
    if other in NATURAL_FRIENDS.get(planet, set()):
        return "friend"
    if other in NATURAL_ENEMIES.get(planet, set()):
        return "enemy"
    return "neutral"


def _sign_lord(sign: Optional[int]) -> Optional[str]:
    if sign is None:
        return None
    return SIGN_LORDS.get(int(sign))


def _house_ordinal(house_num: int) -> str:
    if house_num == 1:
        return "1st"
    if house_num == 2:
        return "2nd"
    if house_num == 3:
        return "3rd"
    return f"{house_num}th"


def _ordinal_suffix(house_num: int) -> str:
    if 10 <= house_num % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(house_num % 10, "th")


def _chart_display_name(chart_id: str) -> str:
    labels = {
        "lagna": "Lagna (D1)",
        "navamsa": "Navamsa (D9)",
        "transit": "Transit",
        "hora": "Hora (D2)",
        "drekkana": "Drekkana (D3)",
        "chaturthamsa": "Chaturthamsa (D4)",
        "saptamsa": "Saptamsa (D7)",
        "dashamsa": "Dasamsa (D10)",
        "dwadashamsa": "Dwadashamsa (D12)",
        "shodasamsa": "Shodasamsa (D16)",
        "vimsamsa": "Vimsamsa (D20)",
        "chaturvimsamsa": "Chaturvimsamsa (D24)",
        "saptavimshamsa": "Saptavimshamsa (D27)",
        "trimsamsa": "Trimsamsa (D30)",
    }
    return labels.get(chart_id, chart_id.upper())


def _verdict_for_counts(support_count: int, stress_count: int) -> Dict[str, str]:
    if support_count >= stress_count + 2:
        return {"key": "strong", "label": "Well supported"}
    if stress_count >= support_count + 2:
        return {"key": "mixed", "label": "Under stress"}
    if support_count and stress_count:
        return {"key": "mixed", "label": "Supported but pressured"}
    if support_count:
        return {"key": "strong", "label": "Quietly supported"}
    if stress_count:
        return {"key": "quiet", "label": "Sensitive area"}
    return {"key": "quiet", "label": "Balanced but not strongly marked"}


def _timing_verdict(activation_count: int) -> Dict[str, str]:
    if activation_count >= 2:
        return {"key": "active", "label": "Actively unfolding now"}
    if activation_count == 1:
        return {"key": "active", "label": "Lightly activated now"}
    return {"key": "quiet", "label": "Natal pattern, not especially triggered now"}


def _build_summary(
    chart_name: str,
    house_num: int,
    significance: str,
    condition: Dict[str, str],
    timing: Dict[str, str],
) -> str:
    area = significance.split(",")[0].strip().lower()
    if condition["key"] == "strong":
        return (
            f"In {chart_name}, the {_house_ordinal(house_num)} house is coming through as {condition['label'].lower()}. "
            f"{area.capitalize()} has cleaner support here, and the current timing is {timing['label'].lower()}."
        )
    if condition["label"] == "Supported but pressured":
        return (
            f"In {chart_name}, the {_house_ordinal(house_num)} house shows both support and pressure. "
            f"{area.capitalize()} can deliver, but results are shaped by effort, maturity, and timing."
        )
    if condition["label"] == "Under stress":
        return (
            f"In {chart_name}, the {_house_ordinal(house_num)} house is under noticeable pressure. "
            f"{area.capitalize()} may require patience, better choices, and stronger timing support."
        )
    return (
        f"In {chart_name}, the {_house_ordinal(house_num)} house is not weak, but it is not overemphasized either. "
        f"{area.capitalize()} depends more on the lord, aspects, and timing than on a single dominant signature."
    )


def _houses_ruled_by_planet(chart_data: Dict[str, Any], planet: str) -> List[int]:
    ruled = []
    for index, house in enumerate(chart_data.get("houses") or [], start=1):
        if house and house.get("sign") is not None:
            sign_lord = _sign_lord(house.get("sign"))
            if sign_lord == planet:
                ruled.append(index)
    return ruled


def _prioritize_factors(factors: List[Dict[str, str]], limit: Optional[int] = None) -> List[Dict[str, str]]:
    priority = {
        "occupant_nakshatra": 0,
        "occupant_friendship": 1,
        "dignity": 2,
        "placement": 3,
        "occupant": 4,
        "ashtakavarga": 5,
        "special": 6,
        "special_house": 7,
        "gandanta": 8,
        "aspect": 9,
        "yoga": 10,
        "strength": 11,
        "dasha": 12,
        "transit": 13,
        "dosha": 14,
    }
    ordered = sorted(
        factors,
        key=lambda item: (priority.get(item.get("category", ""), 99), factors.index(item)),
    )

    deduped: List[Dict[str, str]] = []
    seen = set()
    for item in ordered:
        key = (item.get("category"), item.get("label"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    if limit is None:
        return deduped
    return deduped[:limit]


def _collect_house_factors(
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    house_num: int,
    chart_id: str,
    transit_date: Optional[str],
) -> Dict[str, Any]:
    birth_obj = _birth_obj(birth_data)
    analyzer = HouseAnalyzer(chart_data, birth_obj)
    analysis = analyzer.analyze_house(house_num)
    yogi_data = YogiCalculator(chart_data).calculate_yogi_points(birth_data)

    support: List[Dict[str, str]] = []
    stress: List[Dict[str, str]] = []
    activation: List[Dict[str, str]] = []
    occupant_roles: Dict[str, List[str]] = {}
    ashtakavarga_summary: Optional[Dict[str, Any]] = None

    lord_analysis = analysis["house_lord_analysis"]
    lord = lord_analysis["basic_info"]["planet"]
    lord_house = lord_analysis["basic_info"]["house"]
    lord_sign = lord_analysis["basic_info"]["sign"]
    lord_nakshatra = lord_analysis["basic_info"].get("nakshatra")
    lord_retrograde = (
        lord not in NODE_PLANETS
        and lord_analysis["basic_info"].get("planet")
        and chart_data.get("planets", {}).get(lord, {}).get("retrograde", False)
    )
    lord_dignity = lord_analysis["dignity_analysis"].get("dignity", "neutral")
    lord_states = lord_analysis["dignity_analysis"].get("states", [])
    lord_house_types = lord_analysis["house_position_analysis"].get("house_types", [])
    lord_special = lord_analysis.get("special_lordships", {})
    lord_gandanta = lord_analysis.get("gandanta_analysis", {})
    house_sign = analysis["basic_info"]["house_sign"]
    sign_owner = analyzer.get_sign_lord(lord_sign)
    yogi_sign = yogi_data.get("yogi", {}).get("sign")
    avayogi_sign = yogi_data.get("avayogi", {}).get("sign")
    dagdha_sign = yogi_data.get("dagdha_rashi", {}).get("sign")
    yogi_lord = yogi_data.get("yogi", {}).get("lord")
    avayogi_lord = yogi_data.get("avayogi", {}).get("lord")
    dagdha_lord = yogi_data.get("dagdha_rashi", {}).get("lord")

    if lord_dignity in {"own_sign", "exalted", "moolatrikona", "favorable"}:
        support.append(_factor(f"{lord} is {lord_dignity.replace('_', ' ')}.", "good", "dignity"))
    elif lord_dignity in {"debilitated", "unfavorable"}:
        stress.append(_factor(f"{lord} is {lord_dignity.replace('_', ' ')}.", "warn", "dignity"))

    if "Kendra" in lord_house_types:
        support.append(_factor(f"{lord}, the house lord, sits in a kendra.", "good", "placement"))
    if "Trikona" in lord_house_types and house_num != lord_house:
        support.append(_factor(f"{lord}, the house lord, sits in a trikona.", "good", "placement"))
    if "Dusthana" in lord_house_types:
        stress.append(_factor(f"{lord}, the house lord, sits in a dusthana.", "warn", "placement"))
    elif "Upachaya" in lord_house_types:
        support.append(_factor(f"{lord} gains strength through an upachaya placement.", "good", "placement"))

    if lord_special.get("is_yogi_lord"):
        support.append(_factor(f"{lord} is the Yogi lord.", "good", "special"))
    if lord_special.get("is_avayogi_lord"):
        stress.append(_factor(f"{lord} is the Avayogi lord.", "warn", "special"))
    if lord_special.get("is_dagdha_lord"):
        stress.append(_factor(f"{lord} is functioning as a Dagdha lord.", "warn", "special"))

    if lord_retrograde:
        if lord_house in {6, 8, 12} or lord_dignity in {"debilitated", "unfavorable"}:
            stress.append(_factor(f"{lord}, the house lord, is retrograde and behaves less straightforwardly here.", "warn", "retrograde"))
        else:
            support.append(_factor(f"{lord}, the house lord, is retrograde, making this house more reflective and internally active.", "good", "retrograde"))

    if lord_gandanta.get("is_gandanta"):
        stress.append(_factor(f"{lord} is in Gandanta.", "warn", "gandanta"))

    friendship_matrix = lord_analysis.get("friendship_analysis", {}).get("friendship_matrix", {})
    relation = friendship_matrix.get(sign_owner) if isinstance(friendship_matrix, dict) else None
    relation_label = _relation_label(relation)
    if sign_owner != lord and relation_label:
        if relation in {"great_friend", "friend"}:
            support.append(_factor(f"{lord} has {relation_label}.", "good", "friendship"))
        elif relation in {"enemy", "great_enemy"}:
            stress.append(_factor(f"{lord} has {relation_label}.", "warn", "friendship"))

    if house_sign == yogi_sign:
        support.append(_factor("This house falls on the Yogi sign axis.", "good", "special_house"))
    if house_sign == avayogi_sign:
        stress.append(_factor("This house falls on the Avayogi sign axis.", "warn", "special_house"))
    if house_sign == dagdha_sign:
        stress.append(_factor("This house falls on the Dagdha sign axis.", "warn", "special_house"))

    if lord == yogi_lord:
        support.append(_factor(f"{lord} is the Yogi lord for this chart.", "good", "special"))
    if lord == avayogi_lord:
        stress.append(_factor(f"{lord} is the Avayogi lord for this chart.", "warn", "special"))
    if lord == dagdha_lord:
        stress.append(_factor(f"{lord} is the Dagdha lord for this chart.", "warn", "special"))

    special_house = analysis.get("special_house_analysis", {})
    if special_house.get("is_yogi_house"):
        support.append(_factor("This is marked as a yogi house in the chart.", "good", "special_house"))
    if special_house.get("is_badhaka_house"):
        stress.append(_factor("This house falls in the badhaka axis for the ascendant.", "warn", "special_house"))
    if special_house.get("dusthana_cancellation"):
        support.append(_factor(special_house["dusthana_cancellation"], "good", "yoga"))

    for combo in special_house.get("special_combinations", [])[:2]:
        support.append(_factor(combo, "good", "yoga"))

    gandanta_analysis = analysis.get("gandanta_analysis", {})
    gandanta_impact = gandanta_analysis.get("overall_house_gandanta_impact")
    has_specific_gandanta_reason = False
    resident_gandanta = gandanta_analysis.get("resident_planets_gandanta", []) or []
    if resident_gandanta:
        resident_names = [item.get("planet") for item in resident_gandanta if item.get("planet")]
        if resident_names:
            has_specific_gandanta_reason = True
            stress.append(_factor(
                f"Gandanta affects resident planet{'s' if len(resident_names) > 1 else ''} {', '.join(resident_names)}.",
                "warn",
                "gandanta",
            ))
    house_lord_gandanta = gandanta_analysis.get("house_lord_gandanta", {}) or {}
    if house_lord_gandanta.get("is_gandanta"):
        has_specific_gandanta_reason = True
        stress.append(_factor(f"The house lord {lord} is in Gandanta.", "warn", "gandanta"))
    house_cusp_gandanta = gandanta_analysis.get("house_cusp_gandanta", {}) or {}
    if house_cusp_gandanta.get("is_gandanta"):
        has_specific_gandanta_reason = True
        stress.append(_factor("The house cusp itself falls in Gandanta.", "warn", "gandanta"))
    if gandanta_impact in {"High", "Medium"} and not has_specific_gandanta_reason:
        stress.append(_factor(
            f"Overall Gandanta impact on this house is {gandanta_impact.lower()}.",
            "warn",
            "gandanta",
        ))

    residents = analysis.get("resident_planets", [])
    for resident in residents:
        planet = resident["planet"]
        planet_analysis = resident["analysis"]
        dignity = planet_analysis.get("dignity_analysis", {}).get("dignity", "neutral")
        resident_retrograde = (
            planet not in NODE_PLANETS
            and planet_analysis.get("retrograde_analysis", {}).get("is_retrograde", False)
        )
        resident_sign = planet_analysis.get("basic_info", {}).get("sign")
        resident_longitude = planet_analysis.get("basic_info", {}).get("longitude")
        resident_sign_lord = analyzer.get_sign_lord(resident_sign) if resident_sign is not None else None
        resident_nakshatra_lord = _nakshatra_lord_from_longitude(resident_longitude)
        resident_friendship = planet_analysis.get("friendship_analysis", {}).get("friendship_matrix", {})
        added_specific_support = False
        added_specific_stress = False
        occupant_roles.setdefault(planet, [])

        if planet == yogi_lord:
            support.append(_factor(f"{planet} occupies this house as the Yogi lord.", "good", "special"))
            added_specific_support = True
            occupant_roles[planet].append("Yogi lord")
        if planet == avayogi_lord:
            stress.append(_factor(f"{planet} occupies this house as the Avayogi lord.", "warn", "special"))
            added_specific_stress = True
            occupant_roles[planet].append("Avayogi lord")
        if planet == dagdha_lord:
            stress.append(_factor(f"{planet} occupies this house as the Dagdha lord.", "warn", "special"))
            added_specific_stress = True
            occupant_roles[planet].append("Dagdha lord")

        if isinstance(resident_friendship, dict) and resident_sign_lord and resident_sign_lord != planet:
            resident_relation = resident_friendship.get(resident_sign_lord)
            resident_relation_label = _relation_label(resident_relation)
            if resident_relation in {"great_friend", "friend"} and resident_relation_label:
                support.append(_factor(
                    f"{planet} is placed in a sign ruled by a {resident_relation_label}.",
                    "good",
                    "occupant_friendship",
                ))
                added_specific_support = True
            elif resident_relation in {"enemy", "great_enemy"} and resident_relation_label:
                stress.append(_factor(
                    f"{planet} is placed in a sign ruled by a {resident_relation_label}.",
                    "warn",
                    "occupant_friendship",
                ))
                added_specific_stress = True
            else:
                natural_sign_relation = _natural_relationship(planet, resident_sign_lord)
                if natural_sign_relation == "friend":
                    support.append(_factor(
                        f"{planet} is in a sign ruled by its natural friend {resident_sign_lord}.",
                        "good",
                        "occupant_friendship",
                    ))
                    added_specific_support = True
                elif natural_sign_relation == "enemy":
                    stress.append(_factor(
                        f"{planet} is in a sign ruled by its natural enemy {resident_sign_lord}.",
                        "warn",
                        "occupant_friendship",
                    ))
                    added_specific_stress = True

        if resident_nakshatra_lord == planet:
            support.append(_factor(f"{planet} is placed in its own nakshatra.", "good", "occupant_nakshatra"))
            added_specific_support = True
        else:
            natural_nakshatra_relation = _natural_relationship(planet, resident_nakshatra_lord)
            if natural_nakshatra_relation == "friend":
                support.append(_factor(
                    f"{planet} is in a nakshatra ruled by its natural friend {resident_nakshatra_lord}.",
                    "good",
                    "occupant_nakshatra",
                ))
                added_specific_support = True
            elif natural_nakshatra_relation == "enemy":
                stress.append(_factor(
                    f"{planet} is in a nakshatra ruled by its natural enemy {resident_nakshatra_lord}.",
                    "warn",
                    "occupant_nakshatra",
                ))
                added_specific_stress = True

        if dignity in {"own_sign", "exalted", "moolatrikona", "favorable"}:
            support.append(_factor(f"{planet} occupies this house in {dignity.replace('_', ' ')} dignity.", "good", "occupant"))
        elif dignity in {"debilitated", "unfavorable"}:
            stress.append(_factor(f"{planet} occupies this house in {dignity.replace('_', ' ')} dignity.", "warn", "occupant"))
        elif planet in BENEFICS and not added_specific_support:
            support.append(_factor(f"{planet} occupies this house and supports its matters.", "good", "occupant"))
        elif planet in MALEFICS and not added_specific_stress:
            stress.append(_factor(f"{planet} occupies this house and adds pressure to its matters.", "warn", "occupant"))

        if resident_retrograde:
            if dignity in {"debilitated", "unfavorable"} or planet in MALEFICS:
                stress.append(_factor(f"{planet} is retrograde here, making its results more irregular or delayed.", "warn", "retrograde"))
            else:
                support.append(_factor(f"{planet} is retrograde here, adding inward strength and reworking to this house.", "good", "retrograde"))

    for aspect in analysis.get("aspects_received", [])[:4]:
        planet = aspect["aspecting_planet"]
        effect = aspect.get("house_specific_effect", "")
        aspect_planet_analysis = aspect.get("planet_analysis", {}) or {}
        aspect_house = aspect_planet_analysis.get("basic_info", {}).get("house")
        aspect_dignity = aspect_planet_analysis.get("dignity_analysis", {}).get("dignity", "neutral")
        aspect_retrograde = (
            planet not in NODE_PLANETS
            and aspect_planet_analysis.get("retrograde_analysis", {}).get("is_retrograde", False)
        )
        aspect_special = aspect_planet_analysis.get("special_lordships", {}) or {}
        ruled_houses = _houses_ruled_by_planet(chart_data, planet)
        rules_dusthana = any(h in {6, 8, 12} for h in ruled_houses)
        rules_trikona = any(h in {1, 5, 9} for h in ruled_houses)
        sits_in_dusthana = aspect_house in {6, 8, 12}

        if (
            planet == avayogi_lord
            or planet == dagdha_lord
            or
            aspect_special.get("is_avayogi_lord")
            or aspect_special.get("is_dagdha_lord")
            or aspect_special.get("is_badhaka_lord")
            or sits_in_dusthana
            or aspect_dignity in {"debilitated", "unfavorable"}
            or (aspect_retrograde and (planet in MALEFICS or rules_dusthana))
            or (rules_dusthana and not rules_trikona)
        ):
            if sits_in_dusthana and ruled_houses:
                stress.append(_factor(
                    f"{planet} aspects this house from the {_house_ordinal(aspect_house)} while ruling {', '.join(_house_ordinal(h) for h in ruled_houses)}.",
                    "warn",
                    "aspect",
                ))
            else:
                stress.append(_factor(f"{planet} aspects this house with pressure.", "warn", "aspect"))
        elif "supports" in effect.lower() or "enhances" in effect.lower() or planet in BENEFICS:
            if planet == yogi_lord:
                support.append(_factor(f"{planet} aspects this house as the Yogi lord.", "good", "aspect"))
            elif ruled_houses and rules_trikona:
                support.append(_factor(
                    f"{planet} aspects this house while also carrying {', '.join(_house_ordinal(h) for h in ruled_houses)} lordship.",
                    "good",
                    "aspect",
                ))
            else:
                support.append(_factor(f"{planet} aspects this house.", "good", "aspect"))
            if aspect_retrograde:
                support.append(_factor(f"{planet} is retrograde while aspecting this house, so its influence is more inward and reconsidering than direct.", "good", "retrograde"))
        else:
            stress.append(_factor(f"{planet} aspects this house with pressure.", "warn", "aspect"))

    house_strength = analysis.get("overall_house_assessment", {})
    classical_grade = house_strength.get("classical_grade")
    if classical_grade == "Uttama":
        support.append(_factor("Overall house assessment comes through as Uttama.", "good", "strength"))
    elif classical_grade == "Adhama":
        stress.append(_factor("Overall house assessment comes through as Adhama.", "warn", "strength"))

    try:
        ashtakavarga = AshtakavargaCalculator(birth_data, chart_data)
        sav = ashtakavarga.calculate_sarvashtakavarga()
        sav_points_list = sav.get("house_points") or []
        if len(sav_points_list) >= house_num:
            sav_points = sav_points_list[house_num - 1]
            if sav_points >= 34:
                support.append(_factor(f"Sarvashtakavarga gives strong support with {sav_points} SAV points.", "good", "ashtakavarga"))
            elif sav_points <= 25:
                stress.append(_factor(f"Sarvashtakavarga is weak here with {sav_points} SAV points.", "warn", "ashtakavarga"))

            ashtakavarga_summary = {
                "sav": {
                    "house_points": sav_points,
                    "classification": "strong" if sav_points >= 34 else "weak" if sav_points <= 25 else "moderate",
                    "max_points": max(sav_points_list) if sav_points_list else None,
                    "min_points": min(sav_points_list) if sav_points_list else None,
                }
            }
    except Exception as error:
        print(f"⚠️ Ashtakavarga SAV unavailable for house insight: {error}")

    if ashtakavarga_summary is not None and lord in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}:
        try:
            ashtakavarga = AshtakavargaCalculator(birth_data, chart_data)
            bav = ashtakavarga.calculate_individual_ashtakavarga(lord)
            house_points = bav.get("house_points") or []
            if len(house_points) >= house_num:
                lord_bav = house_points[house_num - 1]
                if lord_bav >= 5:
                    support.append(_factor(f"{lord}'s Bhinnashtakavarga is supportive here with {lord_bav} points.", "good", "ashtakavarga"))
                elif lord_bav <= 3:
                    stress.append(_factor(f"{lord}'s Bhinnashtakavarga is thin here with {lord_bav} points.", "warn", "ashtakavarga"))
                if house_points and lord_bav == max(house_points):
                    support.append(_factor(f"This is one of the strongest BAV houses for {lord}.", "good", "ashtakavarga"))
                elif house_points and lord_bav == min(house_points):
                    stress.append(_factor(f"This is one of the weakest BAV houses for {lord}.", "warn", "ashtakavarga"))
                max_bav = max(house_points) if house_points else None
                min_bav = min(house_points) if house_points else None
                strongest_houses = [idx + 1 for idx, points in enumerate(house_points) if points == max_bav] if house_points else []
                weakest_houses = [idx + 1 for idx, points in enumerate(house_points) if points == min_bav] if house_points else []
                ashtakavarga_summary["lord_bav"] = {
                    "planet": lord,
                    "house_points": lord_bav,
                    "classification": "strong" if lord_bav >= 5 else "weak" if lord_bav <= 3 else "moderate",
                    "max_points": max_bav,
                    "min_points": min_bav,
                    "strongest_houses": strongest_houses,
                    "weakest_houses": weakest_houses,
                }
        except Exception as error:
            print(f"⚠️ Ashtakavarga BAV unavailable for house insight: {error}")

    try:
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        all_yogas = yoga_calc.calculate_all_yogas()
        yoga_hits: List[str] = []
        for category, value in all_yogas.items():
            entries = []
            if isinstance(value, list):
                entries = value
            elif isinstance(value, dict):
                for nested in value.values():
                    if isinstance(nested, list):
                        entries.extend(nested)
            for entry in entries:
                description = str(entry.get("description", ""))
                if f"{house_num}th house" in description or f"{_house_ordinal(house_num)} house" in description:
                    yoga_hits.append(entry.get("name", "Yoga"))
        for yoga_name in list(dict.fromkeys(yoga_hits))[:2]:
            lowered = yoga_name.lower()
            if lowered in EXPLICIT_DOSHA_YOGA_NAMES:
                continue
            if any(keyword in lowered for keyword in NEGATIVE_YOGA_KEYWORDS):
                stress.append(_factor(f"{yoga_name} is also touching this house.", "warn", "yoga"))
            else:
                support.append(_factor(f"{yoga_name} also touches this house.", "good", "yoga"))

        major_doshas = all_yogas.get("major_doshas", {})
        mangal_dosha = major_doshas.get("mangal_dosha", {})
        if mangal_dosha.get("present") and house_num in {1, 2, 4, 7, 8, 12}:
            stress.append(_factor("Mangal Dosha is impacting this house axis.", "warn", "dosha"))

        kaal_sarp = major_doshas.get("kaal_sarp_dosha", {})
        if kaal_sarp.get("present"):
            stress.append(_factor("Kaal Sarp Dosha adds pressure to the chart pattern here.", "warn", "dosha"))

        pitra_dosha = major_doshas.get("pitra_dosha", {})
        if pitra_dosha.get("present") and house_num == 9:
            stress.append(_factor("Pitra Dosha is directly affecting ninth-house themes.", "warn", "dosha"))
    except Exception:
        pass

    try:
        dasha_calc = DashaCalculator()
        dashas = dasha_calc.calculate_current_dashas(
            birth_data,
            current_date=datetime.strptime(transit_date, "%Y-%m-%d") if transit_date else None,
        )
        md_planet = dashas.get("mahadasha", {}).get("planet")
        ad_planet = dashas.get("antardasha", {}).get("planet")
        pd_planet = dashas.get("pratyantardasha", {}).get("planet")
        occupant_names = {resident["planet"] for resident in residents}
        aspecting_names = {aspect["aspecting_planet"] for aspect in analysis.get("aspects_received", [])}

        if md_planet and md_planet == lord:
            activation.append(_factor(f"Mahadasha is running through {lord}, the house lord.", "good", "dasha"))
        elif md_planet and md_planet in occupant_names:
            activation.append(_factor(f"Mahadasha is running through {md_planet}, an occupant of this house.", "good", "dasha"))
        elif md_planet and md_planet in aspecting_names:
            activation.append(_factor(f"Mahadasha is running through {md_planet}, which aspects this house.", "good", "dasha"))

        if ad_planet and ad_planet == lord:
            activation.append(_factor(f"Antardasha is running through {lord}, the house lord.", "good", "dasha"))
        elif ad_planet and ad_planet in occupant_names:
            activation.append(_factor(f"Antardasha is running through {ad_planet}, an occupant of this house.", "good", "dasha"))
        elif ad_planet and ad_planet in aspecting_names:
            activation.append(_factor(f"Antardasha is running through {ad_planet}, which aspects this house.", "good", "dasha"))

        if pd_planet and pd_planet == lord:
            activation.append(_factor(f"Pratyantardasha is running through {lord}, the house lord.", "good", "dasha"))
        elif pd_planet and pd_planet in occupant_names:
            activation.append(_factor(f"Pratyantardasha is running through {pd_planet}, an occupant of this house.", "good", "dasha"))
        elif pd_planet and pd_planet in aspecting_names:
            activation.append(_factor(f"Pratyantardasha is running through {pd_planet}, which aspects this house.", "good", "dasha"))
    except Exception:
        pass

    if chart_id != "transit":
        try:
            transit_chart = TransitCalculator({}).calculate_transits(
                birth_obj,
                transit_date or datetime.now().strftime("%Y-%m-%d"),
            )
            target_sign = house_sign
            transit_hits = []
            for planet, data in (transit_chart.get("planets") or {}).items():
                sign = data.get("sign")
                if sign == target_sign:
                    transit_hits.append(planet)
            if transit_hits:
                activation.append(_factor(f"Current transits through this sign include {', '.join(transit_hits[:3])}.", "good", "transit"))
        except Exception:
            pass

    condition = _verdict_for_counts(len(support), len(stress))
    timing = _timing_verdict(len(activation))
    chart_name = _chart_display_name(chart_id)
    summary = _build_summary(
        chart_name,
        house_num,
        analysis["basic_info"]["significance"],
        condition,
        timing,
    )

    return {
        "house_num": house_num,
        "chart_id": chart_id,
        "chart_name": chart_name,
        "sign_name": analysis["basic_info"]["house_sign_name"],
        "house_lord": lord,
        "significance": analysis["basic_info"]["significance"],
        "verdict": condition,
        "timing_verdict": timing,
        "interpretation": summary,
        "support_factors": _prioritize_factors(support),
        "stress_factors": _prioritize_factors(stress),
        "activation_factors": _prioritize_factors(activation),
        "reasons": [item["label"] for item in (support[:3] + stress[:2] + activation[:2])],
        "related_chart": RELATED_CHARTS.get(house_num) if chart_id == "lagna" else None,
        "raw": {
            "classical_grade": classical_grade,
            "lord_dignity": lord_dignity,
            "lord_house": lord_house,
            "support_count": len(support),
            "stress_count": len(stress),
            "activation_count": len(activation),
            "occupant_roles": occupant_roles,
            "ashtakavarga": ashtakavarga_summary,
        },
    }


def build_house_insight(
    birth_data: Dict[str, Any],
    house_num: int,
    chart_id: str = "lagna",
    transit_date: Optional[str] = None,
) -> Dict[str, Any]:
    birth_obj = _birth_obj(birth_data)
    natal_chart = ChartCalculator({}).calculate_chart(birth_obj)

    if chart_id == "transit":
        transit_raw = TransitCalculator({}).calculate_transits(
            birth_obj,
            transit_date or datetime.now().strftime("%Y-%m-%d"),
        )
        chart_data = _normalize_transit_chart_data(transit_raw)
    else:
        division = CHART_DIVISIONS.get(chart_id)
        if division:
            divisional_chart = DivisionalChartCalculator(natal_chart).calculate_divisional_chart(division)
            chart_data = _normalize_chart_data(divisional_chart)
        else:
            chart_data = natal_chart

    return _collect_house_factors(
        birth_data=birth_data,
        chart_data=chart_data,
        house_num=house_num,
        chart_id=chart_id,
        transit_date=transit_date,
    )


def _preview_highlight_type(chart_data: Dict[str, Any], house_num: int) -> str:
    planets = chart_data.get("planets") or {}
    for data in planets.values():
        if isinstance(data, dict) and int(data.get("house", 0) or 0) == house_num:
            return "planets"
    return "ascendant" if house_num == 1 else "empty"


def _preview_house_topic(insight: Dict[str, Any]) -> str:
    significance = str(insight.get("significance") or "")
    primary = significance.split(",")[0].strip().lower()
    return primary or "this area of life"


def _preview_resident_names(chart_data: Dict[str, Any], house_num: int) -> List[str]:
    planets = chart_data.get("planets") or {}
    residents: List[str] = []
    for planet_name, data in planets.items():
        if isinstance(data, dict) and int(data.get("house", 0) or 0) == house_num:
            residents.append(str(planet_name))
    return residents


def _preview_opening(insight: Dict[str, Any], chart_data: Dict[str, Any], house_num: int) -> str:
    topic = _preview_house_topic(insight)
    residents = _preview_resident_names(chart_data, house_num)
    if house_num == 1:
        sign_name = insight.get("sign_name") or "the ascendant sign"
        return f"The 1st house stands out strongly through {sign_name}, so personality and self-direction come forward first."
    if residents:
        if len(residents) == 1:
            return f"{residents[0]} anchors the {house_num}{_ordinal_suffix(house_num)} house, making {topic} a visible life theme."
        if len(residents) == 2:
            return f"{residents[0]} and {residents[1]} concentrate energy in the {house_num}{_ordinal_suffix(house_num)} house, so {topic} becomes a major focus."
        joined = ", ".join(residents[:3])
        return f"{joined} all emphasize the {house_num}{_ordinal_suffix(house_num)} house, making {topic} one of the stronger chart signatures."
    return f"The {house_num}{_ordinal_suffix(house_num)} house quietly shapes {topic}, even without a heavy planetary pile-up there."


def _preview_reason_sentence(label: str, prefix: str) -> str:
    clean = str(label or "").strip().rstrip(".")
    if not clean:
        return ""
    return f"{prefix} {clean}."


def _preview_message_from_house_insight(insight: Dict[str, Any]) -> str:
    support = [item.get("label") for item in (insight.get("support_factors") or []) if item.get("label")]
    stress = [item.get("label") for item in (insight.get("stress_factors") or []) if item.get("label")]
    activation = [item.get("label") for item in (insight.get("activation_factors") or []) if item.get("label")]
    topic = _preview_house_topic(insight)
    house_num = int(insight.get("house_num") or insight.get("house_number") or 0)
    raw = insight.get("raw") or {}
    lord = insight.get("house_lord") or "The house lord"

    parts: List[str] = []
    verdict = (insight.get("verdict") or {}).get("label")
    if verdict:
        chart_data = insight.get("_chart_data") or {}
        parts.append(_preview_opening(insight, chart_data, house_num))
        parts.append(f"Overall it looks {str(verdict).lower()}.")
    else:
        parts.append("This house has a clear chart signature.")

    if support:
        parts.append(_preview_reason_sentence(support[0], "Support comes from"))
    if stress:
        parts.append(_preview_reason_sentence(stress[0], "Pressure comes from"))

    if activation:
        parts.append(_preview_reason_sentence(activation[0], "Right now this house is active because"))
    elif raw.get("activation_count", 0):
        parts.append(f"Timing is also live here, so {topic} may be easier to notice in day-to-day life.")

    if not support and not stress:
        parts.append(f"{topic.capitalize()} depends more on {lord} and timing than on a single dominant placement.")

    return " ".join(parts)


def _preview_score(insight: Dict[str, Any], chart_data: Dict[str, Any], house_num: int) -> float:
    raw = insight.get("raw") or {}
    support_count = float(raw.get("support_count") or 0)
    stress_count = float(raw.get("stress_count") or 0)
    activation_count = float(raw.get("activation_count") or 0)
    occupant_count = len(_preview_resident_names(chart_data, house_num))
    occupant_bonus = float(occupant_count) * 2.0
    asc_bonus = 2.5 if house_num == 1 else 0.0
    angle_bonus = 1.8 if house_num in {1, 4, 7, 10} else 0.0
    trikona_bonus = 1.4 if house_num in {1, 5, 9} else 0.0
    relationship_bonus = 1.2 if house_num in {2, 5, 7, 8, 11} else 0.0
    dignity_bonus = 1.5 if raw.get("lord_dignity") in {"own_sign", "exalted", "moolatrikona", "favorable"} else 0.0
    stress_signal_bonus = min(stress_count, 3.0) * 0.8
    support_signal_bonus = min(support_count, 3.0) * 1.0
    timing_bonus = activation_count * 1.6
    return (
        occupant_bonus
        + asc_bonus
        + angle_bonus
        + trikona_bonus
        + relationship_bonus
        + dignity_bonus
        + stress_signal_bonus
        + support_signal_bonus
        + timing_bonus
    )


def build_chart_preview_insights(
    birth_data: Dict[str, Any],
    chart_data: Dict[str, Any],
    chart_id: str = "lagna",
    transit_date: Optional[str] = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    normalized_chart = _normalize_chart_data(chart_data or {})
    if not isinstance(normalized_chart, dict) or not isinstance(normalized_chart.get("planets"), dict):
        birth_obj = _birth_obj(birth_data)
        natal_chart = ChartCalculator({}).calculate_chart(birth_obj)
        normalized_chart = _normalize_chart_data(natal_chart)
    ranked: List[Dict[str, Any]] = []

    for house_num in range(1, 13):
        try:
            insight = _collect_house_factors(
                birth_data=birth_data,
                chart_data=normalized_chart,
                house_num=house_num,
                chart_id=chart_id,
                transit_date=transit_date,
            )
        except Exception:
            continue

        ranked.append(
            {
                "house_number": house_num,
                "message": _preview_message_from_house_insight(
                    {
                        **insight,
                        "house_number": house_num,
                        "_chart_data": normalized_chart,
                    }
                ),
                "highlight_type": _preview_highlight_type(normalized_chart, house_num),
                "_score": _preview_score(insight, normalized_chart, house_num),
            }
        )

    ranked.sort(key=lambda item: (-float(item.get("_score") or 0), int(item.get("house_number") or 99)))
    trimmed = ranked[: max(1, limit)]
    for item in trimmed:
        item.pop("_score", None)
    return trimmed
