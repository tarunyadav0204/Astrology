"""Deterministic D1 / D9 relationship indicators."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .astro_utils import (
    aspects_house,
    ascendant_sign,
    dignity_score,
    element_compatibility,
    get_house_from_chart,
    natural_planet_quality,
    planet_dignity,
    planet_sign,
    planets_in_house,
    sign_name,
)
from .constants import BENEFICS, SIGN_LORDS


def profile_snapshot(chart: Dict[str, Any], d9_chart: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    asc_sign = ascendant_sign(chart)
    seventh_sign = ((asc_sign + 5) % 12) + 1 if asc_sign else None
    seventh_lord = SIGN_LORDS.get(seventh_sign) if seventh_sign else None
    seventh_lord_house = get_house_from_chart(chart, seventh_lord) if seventh_lord else None
    seventh_occupants = planets_in_house(chart, 7)
    seventh_aspects = aspects_house(chart, 7)
    venus_sign = planet_sign(chart, "Venus")
    mars_sign = planet_sign(chart, "Mars")
    jupiter_sign = planet_sign(chart, "Jupiter")

    d1_seventh = seventh_house_strength(chart)
    d9_seventh = seventh_house_strength(d9_chart) if d9_chart else {"score": 50, "band": "Unknown", "evidence": []}
    navamsa = navamsa_marriage_synthesis(chart, d9_chart)

    return {
        "ascendant_sign": asc_sign,
        "ascendant_sign_name": sign_name(asc_sign),
        "moon": {
            "sign": planet_sign(chart, "Moon"),
            "house": get_house_from_chart(chart, "Moon"),
        },
        "venus": {
            "sign": venus_sign,
            "sign_name": sign_name(venus_sign),
            "house": get_house_from_chart(chart, "Venus"),
            "dignity": planet_dignity("Venus", venus_sign),
        },
        "mars": {
            "sign": mars_sign,
            "sign_name": sign_name(mars_sign),
            "house": get_house_from_chart(chart, "Mars"),
            "dignity": planet_dignity("Mars", mars_sign),
        },
        "jupiter": {
            "sign": jupiter_sign,
            "sign_name": sign_name(jupiter_sign),
            "house": get_house_from_chart(chart, "Jupiter"),
            "dignity": planet_dignity("Jupiter", jupiter_sign),
        },
        "seventh_house": {
            "sign": seventh_sign,
            "sign_name": sign_name(seventh_sign),
            "lord": seventh_lord,
            "lord_house": seventh_lord_house,
            "occupants": seventh_occupants,
            "aspects": seventh_aspects,
            "d1_strength": d1_seventh,
            "d9_strength": d9_seventh,
        },
        "navamsa_synthesis": navamsa,
    }


def seventh_house_strength(chart: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not chart:
        return {"score": 50, "band": "Unknown", "evidence": []}
    asc_sign = ascendant_sign(chart)
    if asc_sign is None:
        return {"score": 50, "band": "Unknown", "evidence": []}
    seventh_sign = ((asc_sign + 5) % 12) + 1
    seventh_lord = SIGN_LORDS[seventh_sign]
    lord_house = get_house_from_chart(chart, seventh_lord)
    lord_sign = planet_sign(chart, seventh_lord)
    lord_dignity = planet_dignity(seventh_lord, lord_sign)
    occupants = planets_in_house(chart, 7)

    score = 50
    evidence: List[str] = []
    score += dignity_score(lord_dignity) * 5
    evidence.append(f"7th lord {seventh_lord} is {lord_dignity.lower()}")
    if lord_house in {1, 4, 5, 7, 9, 10, 11}:
        score += 10
        evidence.append(f"7th lord placed in supportive house {lord_house}")
    elif lord_house in {6, 8, 12}:
        score -= 10
        evidence.append(f"7th lord placed in difficult house {lord_house}")

    for planet in occupants:
        quality = natural_planet_quality(planet)
        if quality == "benefic":
            score += 8
            evidence.append(f"Benefic {planet} occupies the 7th house")
        elif quality == "malefic":
            score -= 8
            evidence.append(f"Malefic {planet} occupies the 7th house")

    for planet in aspects_house(chart, 7, ["Jupiter", "Venus", "Saturn", "Mars"]):
        if planet in BENEFICS:
            score += 5
            evidence.append(f"{planet} aspects the 7th house")
        else:
            score -= 4
            evidence.append(f"{planet} aspects the 7th house with pressure")

    score = max(0, min(100, score))
    band = "Strong" if score >= 75 else "Supportive" if score >= 60 else "Mixed" if score >= 45 else "Sensitive"
    return {"score": score, "band": band, "evidence": evidence}


def cross_chart_indicators(profile1: Dict[str, Any], profile2: Dict[str, Any]) -> Dict[str, Any]:
    moon_elements = element_compatibility(profile1["moon"]["sign"], profile2["moon"]["sign"])
    venus_mars = element_compatibility(profile1["venus"]["sign"], profile2["mars"]["sign"])
    mars_venus = element_compatibility(profile1["mars"]["sign"], profile2["venus"]["sign"])
    raw_score = round((moon_elements["score"] * 0.4) + (venus_mars["score"] * 0.3) + (mars_venus["score"] * 0.3), 1)
    positives: List[str] = []
    cautions: List[str] = []
    if moon_elements["score"] >= 75:
        positives.append("Moon signs share emotional element compatibility")
    else:
        cautions.append("Moon signs need emotional adjustment")
    if venus_mars["score"] >= 75 or mars_venus["score"] >= 75:
        positives.append("Venus-Mars element flow supports attraction")
    else:
        cautions.append("Venus-Mars pattern may create desire-style mismatch")
    navamsa_pair = round(
        (
            profile1.get("navamsa_synthesis", {}).get("score", 50)
            + profile2.get("navamsa_synthesis", {}).get("score", 50)
        ) / 2.0,
        1,
    )
    if navamsa_pair >= 65:
        positives.append("Navamsa maturity layer supports long-term marriage continuity")
    elif navamsa_pair < 45:
        cautions.append("Navamsa layer shows long-term adjustment pressure")
    return {
        "score": round((raw_score * 0.75) + (navamsa_pair * 0.25), 1),
        "band": "Strong" if raw_score >= 75 else "Supportive" if raw_score >= 60 else "Mixed" if raw_score >= 45 else "Sensitive",
        "moon_element_match": moon_elements,
        "venus_to_mars": venus_mars,
        "mars_to_venus": mars_venus,
        "navamsa_pair_support": navamsa_pair,
        "positive_factors": positives,
        "caution_factors": cautions,
    }


def navamsa_marriage_synthesis(chart: Dict[str, Any], d9_chart: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not chart:
        return {"score": 50, "band": "Unknown", "supportive_factors": [], "challenging_factors": []}

    supportive: List[str] = []
    challenging: List[str] = []
    score = 50

    d1_venus = planet_sign(chart, "Venus")
    d1_jupiter = planet_sign(chart, "Jupiter")
    d9_venus = planet_sign(d9_chart or {}, "Venus") if d9_chart else None
    d9_jupiter = planet_sign(d9_chart or {}, "Jupiter") if d9_chart else None

    for planet, sign_num in (("Venus", d1_venus), ("Jupiter", d1_jupiter)):
        dignity = planet_dignity(planet, sign_num)
        if dignity in {"Exalted", "Own", "Friendly"}:
            score += 6
            supportive.append(f"D1 {planet} is {dignity.lower()} for marriage support")
        elif dignity in {"Debilitated", "Enemy"}:
            score -= 6
            challenging.append(f"D1 {planet} is {dignity.lower()} and needs compensation")

    if d9_chart:
        for planet, sign_num in (("Venus", d9_venus), ("Jupiter", d9_jupiter)):
            dignity = planet_dignity(planet, sign_num)
            if dignity in {"Exalted", "Own", "Friendly"}:
                score += 8
                supportive.append(f"D9 {planet} is {dignity.lower()}, improving mature relationship outcomes")
            elif dignity in {"Debilitated", "Enemy"}:
                score -= 8
                challenging.append(f"D9 {planet} is {dignity.lower()}, adding post-marriage strain")

    d1_seventh = seventh_house_strength(chart)
    d9_seventh = seventh_house_strength(d9_chart) if d9_chart else {"score": 50, "band": "Unknown", "evidence": []}
    score += round((d1_seventh["score"] - 50) * 0.15, 1)
    score += round((d9_seventh["score"] - 50) * 0.2, 1)

    jaimini = _jaimini_relationship_snapshot(chart, d9_chart)
    if jaimini.get("marriage_stability") == "High":
        score += 8
        supportive.append("2nd from Upapada is protected, supporting marriage continuity")
    elif jaimini.get("marriage_stability") == "Challenged":
        score -= 8
        challenging.append("2nd from Upapada carries malefic pressure")

    pushkara = _pushkara_relationship_snapshot(chart)
    if pushkara["relationship_pushkara_planets"]:
        score += 6
        supportive.append(
            "Pushkara support for "
            + ", ".join(pushkara["relationship_pushkara_planets"])
            + " nourishes relationship karma"
        )

    score = max(0, min(100, score))
    band = "Strong" if score >= 75 else "Supportive" if score >= 60 else "Mixed" if score >= 45 else "Sensitive"
    root_vs_fruit = "improves" if d9_seventh["score"] - d1_seventh["score"] >= 10 else "weakens" if d1_seventh["score"] - d9_seventh["score"] >= 10 else "consistent"

    return {
        "score": score,
        "band": band,
        "root_vs_fruit": root_vs_fruit,
        "supportive_factors": supportive,
        "challenging_factors": challenging,
        "planetary": {
            "d1_venus_dignity": planet_dignity("Venus", d1_venus),
            "d1_jupiter_dignity": planet_dignity("Jupiter", d1_jupiter),
            "d9_venus_dignity": planet_dignity("Venus", d9_venus) if d9_chart else "Unknown",
            "d9_jupiter_dignity": planet_dignity("Jupiter", d9_jupiter) if d9_chart else "Unknown",
        },
        "jaimini": jaimini,
        "pushkara": pushkara,
    }


def _jaimini_relationship_snapshot(chart: Dict[str, Any], d9_chart: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not d9_chart:
        return {"available": False}
    try:
        karakas = _calculate_chara_karakas(chart)
        atmakaraka = ((karakas.get("chara_karakas") or {}).get("Atmakaraka") or {}).get("planet")
        darakaraka = ((karakas.get("chara_karakas") or {}).get("Darakaraka") or {}).get("planet")
        if not atmakaraka:
            return {"available": False}
        points = _calculate_jaimini_points(chart, d9_chart, atmakaraka)
        ul_sign = (points.get("upapada_lagna") or {}).get("sign_id")
        a7_sign = (points.get("darapada") or {}).get("sign_id")
        second_from_ul_sign = ((ul_sign + 1) % 12) if ul_sign is not None else None
        second_from_ul = _planets_in_sign(chart, second_from_ul_sign)
        blocking = [planet for planet in second_from_ul if planet in {"Saturn", "Mars", "Rahu", "Ketu"}]
        dk_sign = planet_sign(chart, darakaraka) if darakaraka else None
        return {
            "available": True,
            "upapada_sign": sign_name((ul_sign + 1)) if ul_sign is not None else None,
            "darapada_sign": sign_name((a7_sign + 1)) if a7_sign is not None else None,
            "darakaraka": darakaraka,
            "darakaraka_sign": sign_name(dk_sign),
            "second_from_ul_planets": second_from_ul,
            "blocking_factors": blocking,
            "marriage_stability": "Challenged" if blocking else "High",
        }
    except Exception:
        return {"available": False}


def _pushkara_relationship_snapshot(chart: Dict[str, Any]) -> Dict[str, Any]:
    try:
        pushkara = _analyze_pushkara(chart)
        rel_planets = []
        for row in pushkara.get("pushkara_planets", []):
            if row.get("planet") in {"Venus", "Jupiter", "Moon", "Mars"}:
                rel_planets.append(row["planet"])
        return {
            "has_pushkara": pushkara.get("has_pushkara", False),
            "relationship_pushkara_planets": rel_planets,
            "total_pushkara_planets": pushkara.get("total_pushkara_planets", 0),
        }
    except Exception:
        return {"has_pushkara": False, "relationship_pushkara_planets": [], "total_pushkara_planets": 0}


def _planets_in_sign(chart: Dict[str, Any], sign_num_zero: Optional[int]) -> List[str]:
    if sign_num_zero is None:
        return []
    planets = []
    for planet_name, data in (chart.get("planets") or {}).items():
        if data.get("sign") == sign_num_zero:
            planets.append(planet_name)
    return planets


def _calculate_chara_karakas(chart: Dict[str, Any]) -> Dict[str, Any]:
    planets = chart.get("planets", {})
    planet_degrees = {}
    for planet_name, planet_data in planets.items():
        if planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            longitude = planet_data.get("longitude", 0)
            planet_degrees[planet_name] = longitude % 30

    sorted_planets = sorted(planet_degrees.items(), key=lambda x: x[1], reverse=True)
    karaka_names = [
        "Atmakaraka",
        "Amatyakaraka",
        "Bhratrukaraka",
        "Matrukaraka",
        "Putrakaraka",
        "Gnatikaraka",
        "Darakaraka",
    ]

    chara_karakas = {}
    for i, (planet, degree_in_sign) in enumerate(sorted_planets[:7]):
        karaka_name = karaka_names[i]
        chara_karakas[karaka_name] = {
            "planet": planet,
            "degree_in_sign": round(degree_in_sign, 2),
            "sign": planets.get(planet, {}).get("sign", 0),
            "house": planets.get(planet, {}).get("house", 1),
            "longitude": planets.get(planet, {}).get("longitude", 0),
        }

    return {"chara_karakas": chara_karakas}


def _calculate_jaimini_points(chart: Dict[str, Any], d9_chart: Dict[str, Any], atmakaraka: str) -> Dict[str, Any]:
    asc_sign_d1 = int(chart.get("ascendant", 0) / 30)
    planets_d1 = chart.get("planets", {})
    planets_d9 = d9_chart.get("planets", {})

    def get_lord(sign_idx: int):
        lords = {
            0: "Mars",
            1: "Venus",
            2: "Mercury",
            3: "Moon",
            4: "Sun",
            5: "Mercury",
            6: "Venus",
            7: ["Mars", "Ketu"],
            8: "Jupiter",
            9: "Saturn",
            10: ["Saturn", "Rahu"],
            11: "Jupiter",
        }
        return lords[sign_idx]

    def count_planets_in_sign(sign_idx: int) -> int:
        return sum(1 for data in planets_d1.values() if data.get("sign") == sign_idx)

    def resolve_dual_lord(lords: List[str]) -> int:
        p1_sign = planets_d1.get(lords[0], {}).get("sign", 0)
        p2_sign = planets_d1.get(lords[1], {}).get("sign", 0)
        return p1_sign if count_planets_in_sign(p1_sign) >= count_planets_in_sign(p2_sign) else p2_sign

    def arudha(house_num: int) -> int:
        house_sign_idx = (asc_sign_d1 + (house_num - 1)) % 12
        lord = get_lord(house_sign_idx)
        lord_sign = resolve_dual_lord(lord) if isinstance(lord, list) else planets_d1.get(lord, {}).get("sign", 0)
        dist = lord_sign - house_sign_idx if lord_sign >= house_sign_idx else (12 - house_sign_idx) + lord_sign
        if dist == 0:
            return (house_sign_idx + 9) % 12
        if dist == 6:
            return (house_sign_idx + 3) % 12
        return (lord_sign + dist) % 12

    return {
        "darapada": {"sign_id": arudha(7)},
        "upapada_lagna": {"sign_id": arudha(12)},
        "karkamsa_lagna": {"sign_id": planets_d9.get(atmakaraka, {}).get("sign", 0)},
    }


def _analyze_pushkara(chart: Dict[str, Any]) -> Dict[str, Any]:
    pushkara_map = {
        "fire": [7, 9],
        "earth": [3, 5],
        "air": [6, 8],
        "water": [1, 3],
    }
    elements = {
        0: "fire",
        1: "earth",
        2: "air",
        3: "water",
        4: "fire",
        5: "earth",
        6: "air",
        7: "water",
        8: "fire",
        9: "earth",
        10: "air",
        11: "water",
    }
    pushkara_bhagas = {
        0: 21,
        4: 14,
        8: 24,
        1: 14,
        5: 24,
        9: 21,
        2: 21,
        6: 14,
        10: 24,
        3: 7,
        7: 11,
        11: 23,
    }

    rows: List[Dict[str, Any]] = []
    for planet_name, planet_data in (chart.get("planets") or {}).items():
        if planet_name in {"Rahu", "Ketu"}:
            continue
        d1_sign = planet_data.get("sign", 0)
        d1_longitude = planet_data.get("longitude", 0)
        degree_in_sign = d1_longitude % 30
        navamsa_no = int(degree_in_sign / (30 / 9)) + 1
        element = elements.get(d1_sign)
        is_pushkara_navamsa = navamsa_no in pushkara_map[element]
        is_pushkara_bhaga = abs(degree_in_sign - pushkara_bhagas.get(d1_sign, -99)) <= 1.0
        if is_pushkara_navamsa or is_pushkara_bhaga:
            rows.append(
                {
                    "planet": planet_name,
                    "navamsa_no": navamsa_no,
                    "is_pushkara_navamsa": is_pushkara_navamsa,
                    "is_pushkara_bhaga": is_pushkara_bhaga,
                }
            )
    return {
        "has_pushkara": bool(rows),
        "pushkara_planets": rows,
        "total_pushkara_planets": len(rows),
    }
