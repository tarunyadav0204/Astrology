"""Deterministic evidence spine for exact-day chat predictions.

The goal is to give the LLM hard Jyotish facts for a single day instead of
letting it improvise from a large natal context. The spine focuses on the
five-level Vimshottari stack and what those lords are doing by transit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from calculators.panchang_calculator import PanchangCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from calculators.vedic_graha_drishti import DEFAULT_ASPECTS, GRAHA_HOUSE_ASPECTS
from context_agents.compact_vedic import SIGN_NAMES, house_lordships_from_ascendant
from shared.dasha_calculator import DashaCalculator

_DASHA_LEVELS = (
    ("mahadasha", "MD", 8),
    ("antardasha", "AD", 12),
    ("pratyantardasha", "PD", 20),
    ("sookshma", "SK", 25),
    ("prana", "PR", 30),
)

_NAKSHATRA_LORDS = (
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
)

_TARA_NAMES = (
    "Janma",
    "Sampat",
    "Vipat",
    "Kshema",
    "Pratyak",
    "Sadhana",
    "Naidhana",
    "Mitra",
    "Ati Mitra",
)

_HOUSE_DOMAINS = {
    1: ("body", "head", "vitality", "confidence", "visibility", "health"),
    2: ("money", "family", "speech", "food", "face", "mouth", "right eye"),
    3: ("communication", "effort", "siblings", "short travel", "change", "hands", "arms", "shoulders", "commute"),
    4: ("home", "mother", "peace", "property", "vehicle", "land", "chest", "heart", "emotional security"),
    5: ("intelligence", "children", "romance", "creative output", "stomach", "education", "speculation"),
    6: ("workload", "conflict", "health routines", "debts", "injury", "illness", "competition", "litigation"),
    7: ("partner", "clients", "public dealings", "agreements", "marriage", "marketplace", "lower abdomen"),
    8: ("sudden events", "accidents", "anxiety", "research", "vulnerability", "surgery", "shock", "chronic issues"),
    9: ("luck", "teachers", "father", "dharma", "long travel", "fortune", "hips", "thighs"),
    10: ("career", "authority", "status", "actions", "profession", "knees", "public responsibility"),
    11: ("income", "networks", "gains", "fulfilment", "friends", "elder siblings", "calves"),
    12: ("sleep", "expenses", "isolation", "foreign links", "hospitalization", "loss", "feet", "left eye"),
}

_LEVEL_EVENT_WEIGHT = {
    "MD": 12,
    "AD": 20,
    "PD": 40,
    "SK": 65,
    "PR": 85,
}

_DUSHTHANA_HOUSES = {6, 8, 12}
_TRIKONA_HOUSES = {1, 5, 9}
_KENDRA_HOUSES = {1, 4, 7, 10}

_CATEGORY_HOUSES = {
    "career": [2, 6, 10, 11],
    "job": [2, 6, 10, 11],
    "business": [2, 7, 10, 11],
    "love": [5, 7, 11],
    "relationship": [5, 7, 11],
    "marriage": [2, 7, 11],
    "wealth": [2, 5, 9, 11],
    "money": [2, 5, 9, 11],
    "health": [1, 6, 8, 12],
    "accident": [8, 6, 12, 3, 4],
    "accidents": [8, 6, 12, 3, 4],
    "vehicle": [4, 3, 8, 12],
    "education": [4, 5, 9],
    "travel": [3, 9, 12],
    "property": [4, 11],
    "general": [1, 4, 7, 10, 11],
}

_KARAKA_LABELS = {
    "Atmakaraka": "AK",
    "Amatyakaraka": "AmK",
    "Bhratrukaraka": "BK",
    "Matrukaraka": "MK",
    "Putrakaraka": "PK",
    "Gnatikaraka": "GK",
    "Darakaraka": "DK",
}

_AV_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}


def _iso_date(value: Any) -> Optional[str]:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str) and value:
        return value[:10]
    return None


def _sign0(longitude: float) -> int:
    return int(float(longitude) / 30.0) % 12


def _house_from_longitude(longitude: float, ascendant_longitude: float) -> int:
    return ((_sign0(longitude) - _sign0(ascendant_longitude)) % 12) + 1


def _angle_diff(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def _nakshatra_lord(index_0: int) -> str:
    return _NAKSHATRA_LORDS[int(index_0) % 9]


def _tara_from_indexes(natal_index_0: Optional[int], transit_index_0: Optional[int]) -> Optional[Dict[str, Any]]:
    if natal_index_0 is None or transit_index_0 is None:
        return None
    distance = ((int(transit_index_0) - int(natal_index_0)) % 27) + 1
    tara_number = ((distance - 1) % 9) + 1
    return {
        "distance": distance,
        "tara_number": tara_number,
        "tara": _TARA_NAMES[tara_number - 1],
    }


def _house_domains(house: Any) -> List[str]:
    try:
        return list(_HOUSE_DOMAINS.get(int(house), ()))
    except (TypeError, ValueError):
        return []


def _target_snapshot(planet: str, row: Dict[str, Any]) -> Dict[str, Any]:
    house = int(row.get("house") or 0)
    return {
        "planet": planet,
        "house": house,
        "sign": row.get("sign"),
        "nakshatra": row.get("nakshatra"),
        "pada": row.get("pada"),
        "lordships": row.get("lordships") or [],
        "domains": _house_domains(house),
    }


def _trigger_strength(score: Any) -> str:
    n = int(score or 0)
    if n >= 125:
        return "massive"
    if n >= 85:
        return "strong"
    if n >= 45:
        return "moderate"
    return "background"


def _sign_distance_1(from_sign_name: Any, to_sign_name: Any) -> Optional[int]:
    if from_sign_name not in SIGN_NAMES or to_sign_name not in SIGN_NAMES:
        return None
    return ((SIGN_NAMES.index(str(to_sign_name)) - SIGN_NAMES.index(str(from_sign_name))) % 12) + 1


def _same_element_distance(from_sign_name: Any, to_sign_name: Any) -> bool:
    distance = _sign_distance_1(from_sign_name, to_sign_name)
    return distance in (1, 5, 9)


def _event_houses_for_intent(intent: Dict[str, Any], daily_judgment: Dict[str, Any]) -> List[int]:
    category = str(intent.get("category") or "general").lower()
    houses = list(_CATEGORY_HOUSES.get(category, _CATEGORY_HOUSES["general"]))
    for row in daily_judgment.get("top_activated_houses") or []:
        try:
            h = int(row.get("house"))
        except (TypeError, ValueError, AttributeError):
            continue
        if h not in houses:
            houses.append(h)
    return houses[:8]


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def _planet_natal_row(
    planet: str,
    d1_chart: Dict[str, Any],
    planetary_analysis: Dict[str, Any],
    house_lordships: Dict[str, List[int]],
    rtc: RealTransitCalculator,
) -> Dict[str, Any]:
    pdata = (d1_chart.get("planets") or {}).get(planet) or {}
    lon = float(pdata.get("longitude", 0.0) or 0.0)
    computed_nakshatra = rtc.get_nakshatra_from_longitude(lon)
    nk_info = ((planetary_analysis.get(planet) or {}).get("basic_info") or {})
    nk_name = nk_info.get("nakshatra")
    if not nk_name:
        nk_name = computed_nakshatra.get("name")
    return {
        "planet": planet,
        "longitude": round(lon, 4),
        "sign": SIGN_NAMES[_sign0(lon)],
        "house": int(pdata.get("house") or 0),
        "nakshatra": nk_name,
        "nakshatra_index": int(computed_nakshatra.get("index", 0)),
        "pada": nk_info.get("pada") or computed_nakshatra.get("pada"),
        "lordships": house_lordships.get(planet, []),
    }


def _planet_transit_row(
    planet: str,
    target_dt: datetime,
    ascendant_longitude: float,
    rtc: RealTransitCalculator,
) -> Dict[str, Any]:
    lon = rtc.get_planet_position(target_dt, planet)
    if lon is None:
        return {"planet": planet, "available": False}
    nk = rtc.get_nakshatra_from_longitude(lon)
    sign = _sign0(lon)
    return {
        "planet": planet,
        "available": True,
        "longitude": round(lon, 4),
        "sign": SIGN_NAMES[sign],
        "house": _house_from_longitude(lon, ascendant_longitude),
        "degree_in_sign": round(lon % 30.0, 2),
        "nakshatra": nk.get("name"),
        "nakshatra_index": int(nk.get("index", 0)),
        "pada": nk.get("pada"),
        "nakshatra_lord": _nakshatra_lord(int(nk.get("index", 0))),
        "retrograde": rtc.is_planet_retrograde(target_dt, planet),
    }


def _aspected_house(transit_house: int, aspect_number: int) -> int:
    return ((int(transit_house) + int(aspect_number) - 2) % 12) + 1


def _build_trigger_evidence(
    planet: str,
    natal: Dict[str, Any],
    transit: Dict[str, Any],
    all_natal_rows: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    if not transit.get("available"):
        return {"planet": planet, "available": False, "score": 0, "flags": []}

    score = 0
    flags: List[str] = []
    conjunctions: List[str] = []
    conjunction_details: List[Dict[str, Any]] = []
    aspects: List[Dict[str, Any]] = []

    transit_house = int(transit.get("house") or 0)

    if transit.get("sign") == natal.get("sign"):
        score += 35
        flags.append("same_sign_return")

    if transit.get("nakshatra") and transit.get("nakshatra") == natal.get("nakshatra"):
        score += 35
        flags.append("same_nakshatra_return")

    if transit.get("longitude") is not None and natal.get("longitude") is not None:
        orb = _angle_diff(transit["longitude"], natal["longitude"])
        if orb <= 3:
            score += 35
            flags.append(f"degree_return_orb_{round(orb, 2)}")

    for natal_planet, row in all_natal_rows.items():
        if int(row.get("house") or 0) == transit_house:
            conjunctions.append(natal_planet)
            conjunction_details.append(_target_snapshot(natal_planet, row))
            score += 25 if natal_planet == planet else 10

    available_aspects = GRAHA_HOUSE_ASPECTS.get(planet, DEFAULT_ASPECTS)
    for aspect_number in available_aspects:
        target_house = _aspected_house(transit_house, aspect_number)
        target_planets = [
            natal_planet
            for natal_planet, row in all_natal_rows.items()
            if int(row.get("house") or 0) == target_house
        ]
        if not target_planets:
            continue
        target_details = [
            _target_snapshot(natal_planet, all_natal_rows[natal_planet])
            for natal_planet in target_planets
        ]
        aspects.append({
            "aspect_number": aspect_number,
            "target_house": target_house,
            "target_planets": target_planets,
            "target_planet_details": target_details,
            "target_domains": sorted({
                domain
                for detail in target_details
                for domain in (detail.get("domains") or [])
            }),
        })
        score += 30 if planet in target_planets else 12
        if planet in target_planets:
            flags.append(f"aspects_own_natal_position_{aspect_number}")

    return {
        "planet": planet,
        "available": True,
        "score": score,
        "strength": _trigger_strength(score),
        "flags": sorted(set(flags)),
        "conjunct_natal_planets": conjunctions,
        "conjunct_natal_planet_details": conjunction_details,
        "aspects_to_natal_planets": aspects,
    }


def _add_house_score(
    bucket: Dict[int, Dict[str, Any]],
    house: Any,
    points: int,
    reason: str,
    *,
    planet: str,
    level: str,
) -> None:
    try:
        h = int(house)
    except (TypeError, ValueError):
        return
    if h < 1 or h > 12:
        return
    row = bucket.setdefault(
        h,
        {
            "house": h,
            "score": 0,
            "domains": _house_domains(h),
            "reasons": [],
        },
    )
    row["score"] += int(points)
    row["reasons"].append({
        "planet": planet,
        "level": level,
        "points": int(points),
        "reason": reason,
    })


def _derive_daily_judgment(
    dasha_rows: List[Dict[str, Any]],
    trigger_rows: List[Dict[str, Any]],
    moon_tara: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compact deterministic synthesis so the LLM does not invent daily priorities."""
    house_bucket: Dict[int, Dict[str, Any]] = {}
    domain_bucket: Dict[str, int] = {}
    massive_factors: List[Dict[str, Any]] = []
    caution_houses: List[int] = []
    support_houses: List[int] = []

    trigger_by_level_planet = {
        (row.get("level"), row.get("planet")): row
        for row in trigger_rows
    }

    for row in dasha_rows:
        level = str(row.get("level") or "")
        planet = str(row.get("planet") or "")
        level_weight = _LEVEL_EVENT_WEIGHT.get(level, 10)
        natal = row.get("natal") or {}
        transit = row.get("transit") or {}
        trigger = trigger_by_level_planet.get((level, planet), row.get("trigger") or {})
        trigger_score = int(trigger.get("score") or 0)

        # Natal promise: the dasha lord's own house and lordships show what it can deliver.
        _add_house_score(house_bucket, natal.get("house"), level_weight, "dasha_lord_natal_house", planet=planet, level=level)
        for lorded_house in natal.get("lordships") or []:
            _add_house_score(
                house_bucket,
                lorded_house,
                max(6, level_weight // 2),
                "dasha_lord_house_lordship",
                planet=planet,
                level=level,
            )

        # Transit field: where the active dasha lord is moving today.
        if transit.get("available"):
            _add_house_score(
                house_bucket,
                transit.get("house"),
                max(8, level_weight // 2),
                "dasha_lord_transit_house",
                planet=planet,
                level=level,
            )

        for detail in trigger.get("conjunct_natal_planet_details") or []:
            _add_house_score(
                house_bucket,
                detail.get("house"),
                max(10, level_weight // 2),
                f"transit_dasha_lord_conjuncts_natal_{detail.get('planet')}",
                planet=planet,
                level=level,
            )
            for lorded_house in detail.get("lordships") or []:
                _add_house_score(
                    house_bucket,
                    lorded_house,
                    max(5, level_weight // 4),
                    f"conjunct_target_lordship_{detail.get('planet')}",
                    planet=planet,
                    level=level,
                )

        for aspect in trigger.get("aspects_to_natal_planets") or []:
            for detail in aspect.get("target_planet_details") or []:
                _add_house_score(
                    house_bucket,
                    detail.get("house"),
                    max(10, level_weight // 2),
                    f"transit_dasha_lord_aspects_natal_{detail.get('planet')}",
                    planet=planet,
                    level=level,
                )
                for lorded_house in detail.get("lordships") or []:
                    _add_house_score(
                        house_bucket,
                        lorded_house,
                        max(5, level_weight // 4),
                        f"aspected_target_lordship_{detail.get('planet')}",
                        planet=planet,
                        level=level,
                    )

        flags = set(trigger.get("flags") or [])
        if flags.intersection({"same_sign_return", "same_nakshatra_return"}) or any(
            str(flag).startswith("degree_return_orb_") for flag in flags
        ):
            massive_factors.append({
                "level": level,
                "planet": planet,
                "strength": _trigger_strength(trigger_score),
                "flags": sorted(flags),
                "rule": "Dasha lord returning to natal sign/nakshatra/degree can give outsized results of its natal house and lordships.",
            })

    ranked_houses = sorted(house_bucket.values(), key=lambda item: item.get("score", 0), reverse=True)
    for item in ranked_houses:
        h = int(item.get("house") or 0)
        if h in _DUSHTHANA_HOUSES:
            caution_houses.append(h)
        if h in _TRIKONA_HOUSES or h in _KENDRA_HOUSES or h == 11:
            support_houses.append(h)
        for domain in item.get("domains") or []:
            domain_bucket[domain] = domain_bucket.get(domain, 0) + int(item.get("score") or 0)

    top_domains = [
        {"domain": domain, "score": score}
        for domain, score in sorted(domain_bucket.items(), key=lambda kv: kv[1], reverse=True)[:8]
    ]

    tara = (moon_tara or {}).get("tara")
    tara_quality = "neutral"
    if tara in ("Sampat", "Kshema", "Sadhana", "Mitra", "Ati Mitra"):
        tara_quality = "supportive"
    elif tara in ("Vipat", "Pratyak", "Naidhana"):
        tara_quality = "caution"

    return {
        "method": "daily_judgment_v1",
        "top_activated_houses": ranked_houses[:6],
        "top_event_domains": top_domains,
        "massive_result_factors": massive_factors,
        "support_houses": sorted(set(support_houses)),
        "caution_houses": sorted(set(caution_houses)),
        "moon_tara_quality": {
            "tara": tara,
            "quality": tara_quality,
            "rule": "Tara Bala modifies smoothness of events; it does not override active dasha lord triggers.",
        },
        "prediction_rule": (
            "For the direct daily answer, prioritize PR/SK/PD planets and the top activated houses/domains. "
            "Use AD/MD only as permission/background unless their trigger strength is strong or massive."
        ),
    }


def _derive_daily_nadi(
    dasha_rows: List[Dict[str, Any]],
    all_natal_rows: Dict[str, Dict[str, Any]],
    moon_transit: Dict[str, Any],
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []

    def add_links(source: str, level: str, planet: str, transit: Dict[str, Any]) -> None:
        if not transit.get("available"):
            return
        for natal_planet, natal in all_natal_rows.items():
            relation = None
            if transit.get("sign") == natal.get("sign"):
                relation = "same_sign_conjunction"
            elif _same_element_distance(transit.get("sign"), natal.get("sign")):
                relation = "trinal_nadi_link"
            if relation is None:
                continue
            rows.append({
                "source": source,
                "level": level,
                "transit_planet": planet,
                "transit_sign": transit.get("sign"),
                "natal_planet": natal_planet,
                "natal_house": natal.get("house"),
                "natal_lordships": natal.get("lordships") or [],
                "relation": relation,
                "domains": _house_domains(natal.get("house")),
            })

    for row in dasha_rows:
        add_links(
            "dasha_lord_transit",
            str(row.get("level") or ""),
            str(row.get("planet") or ""),
            row.get("transit") or {},
        )
    add_links("moon_transit", "Moon", "Moon", moon_transit)

    priority = {"same_sign_conjunction": 2, "trinal_nadi_link": 1}
    rows.sort(
        key=lambda item: (
            _LEVEL_EVENT_WEIGHT.get(str(item.get("level") or ""), 15),
            priority.get(str(item.get("relation") or ""), 0),
        ),
        reverse=True,
    )
    return {
        "method": "nadi_daily_v1",
        "principle": "Daily Nadi uses exact conjunction or 1/5/9 sign links from the transiting Moon and active dasha lords to natal grahas; other sign relations are not counted as Nadi links.",
        "activation_links": rows[:12],
        "verdict": "active" if rows else "no_exact_daily_nadi_link_found",
    }


def _karaka_rows(static_context: Dict[str, Any], all_natal_rows: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    raw = static_context.get("chara_karakas") or {}
    inner = raw.get("chara_karakas") if isinstance(raw, dict) else {}
    if not isinstance(inner, dict):
        return []
    rows: List[Dict[str, Any]] = []
    for long_name, short_name in _KARAKA_LABELS.items():
        data = inner.get(long_name)
        if not isinstance(data, dict):
            continue
        planet = data.get("planet")
        natal = all_natal_rows.get(str(planet)) or {}
        rows.append({
            "karaka": short_name,
            "name": long_name,
            "planet": planet,
            "house": natal.get("house") or data.get("house"),
            "sign": natal.get("sign"),
            "nakshatra": natal.get("nakshatra"),
            "domains": _house_domains(natal.get("house") or data.get("house")),
        })
    return rows


def _derive_daily_jaimini(
    static_context: Dict[str, Any],
    dasha_rows: List[Dict[str, Any]],
    all_natal_rows: Dict[str, Dict[str, Any]],
    moon_transit: Dict[str, Any],
) -> Dict[str, Any]:
    karakas = _karaka_rows(static_context, all_natal_rows)
    hits: List[Dict[str, Any]] = []
    moon_from_karakas: List[Dict[str, Any]] = []

    karaka_by_planet = {
        str(row.get("planet")): row
        for row in karakas
        if row.get("planet")
    }
    for row in karakas:
        distance = _sign_distance_1(row.get("sign"), moon_transit.get("sign"))
        if distance is not None:
            moon_from_karakas.append({
                "karaka": row.get("karaka"),
                "planet": row.get("planet"),
                "moon_house_from_karaka": distance,
                "moon_sign": moon_transit.get("sign"),
            })

    for dasha in dasha_rows:
        level = str(dasha.get("level") or "")
        planet = str(dasha.get("planet") or "")
        trigger = dasha.get("trigger") or {}
        touched = {planet} if planet in karaka_by_planet else set()
        for detail in trigger.get("conjunct_natal_planet_details") or []:
            target = str(detail.get("planet") or "")
            if target in karaka_by_planet:
                touched.add(target)
        for aspect in trigger.get("aspects_to_natal_planets") or []:
            for detail in aspect.get("target_planet_details") or []:
                target = str(detail.get("planet") or "")
                if target in karaka_by_planet:
                    touched.add(target)
        for target in sorted(touched):
            krow = karaka_by_planet[target]
            hits.append({
                "level": level,
                "dasha_planet": planet,
                "karaka": krow.get("karaka"),
                "karaka_planet": target,
                "karaka_house": krow.get("house"),
                "domains": krow.get("domains") or [],
                "strength": trigger.get("strength"),
                "rule": "Active dasha lord transit touches a Chara Karaka; judge the day through that karaka's agenda and house.",
            })

    return {
        "method": "jaimini_daily_v1",
        "principle": "Daily Jaimini reads the transiting Moon and active PR/SK/PD dasha-lord hits to AK/AmK/DK/GK and other Chara Karakas; broad static karaka biography is secondary.",
        "moon_from_karakas": moon_from_karakas,
        "karaka_hits": hits[:10],
        "verdict": "active" if hits or moon_from_karakas else "karaka_data_unavailable",
    }


def _house_in_list(value: Any, houses: List[int]) -> bool:
    try:
        return int(value) in set(int(h) for h in houses)
    except (TypeError, ValueError):
        return False


def _kp_houses_for_planet(kp: Dict[str, Any], planet: str) -> List[int]:
    raw = (kp.get("planet_significators") or {}).get(planet)
    houses: List[int] = []
    for item in _as_list(raw):
        try:
            houses.append(int(item))
        except (TypeError, ValueError):
            continue
    four_step = (kp.get("four_step_theory") or {}).get(planet)
    if isinstance(four_step, dict):
        for block in four_step.values():
            if not isinstance(block, dict):
                continue
            for item in _as_list(block.get("houses")):
                try:
                    houses.append(int(item))
                except (TypeError, ValueError):
                    continue
    return sorted(set(h for h in houses if 1 <= h <= 12))


def _derive_daily_kp(
    static_context: Dict[str, Any],
    dasha_rows: List[Dict[str, Any]],
    event_houses: List[int],
) -> Dict[str, Any]:
    kp = static_context.get("kp_analysis") or {}
    if not isinstance(kp, dict) or kp.get("error"):
        return {
            "method": "kp_daily_v1",
            "available": False,
            "verdict": "kp_data_unavailable",
        }

    cusp_lords = kp.get("cusp_lords") or {}
    cusp_rows: List[Dict[str, Any]] = []
    for house in event_houses[:6]:
        row = cusp_lords.get(str(house), cusp_lords.get(house, {}))
        if isinstance(row, dict):
            cusp_rows.append({
                "house": house,
                "sign_lord": row.get("sign_lord"),
                "star_lord": row.get("star_lord"),
                "sub_lord": row.get("sub_lord"),
                "sub_sub_lord": row.get("sub_sub_lord"),
            })

    active_hits: List[Dict[str, Any]] = []
    for dasha in dasha_rows:
        level = str(dasha.get("level") or "")
        if level not in {"PD", "SK", "PR"}:
            continue
        planet = str(dasha.get("planet") or "")
        houses = _kp_houses_for_planet(kp, planet)
        matched = [h for h in houses if h in event_houses]
        if matched:
            active_hits.append({
                "level": level,
                "planet": planet,
                "signifies_houses": houses,
                "matched_event_houses": matched,
                "rule": "KP daily materialization improves when PR/SK/PD lords signify the requested event cusps.",
            })

    return {
        "method": "kp_daily_v1",
        "available": True,
        "event_houses": event_houses,
        "cusp_chain": cusp_rows,
        "active_dasha_significator_hits": active_hits,
        "verdict": "supports_materialization" if active_hits else "weak_or_indirect_kp_trigger",
    }


def _av_strength(sav: int, bav: Optional[int]) -> str:
    if sav >= 30 and (bav is None or bav >= 4):
        return "strong"
    if sav < 25 or (bav is not None and bav < 3):
        return "strained"
    return "workable"


def _av_house_rows(static_context: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    av = static_context.get("ashtakavarga") or {}
    d1 = av.get("d1_rashi") or {}
    sav_inner = (d1.get("sarvashtakavarga") or {}).get("sarvashtakavarga") or {}
    bav_root = d1.get("bhinnashtakavarga") or {}
    ascendant = float((static_context.get("d1_chart") or {}).get("ascendant", 0.0) or 0.0)
    asc0 = _sign0(ascendant)
    rows: Dict[int, Dict[str, Any]] = {}
    for house in range(1, 13):
        sign0 = (asc0 + house - 1) % 12
        try:
            sav = int(sav_inner.get(str(sign0), sav_inner.get(sign0, 0)) or 0)
        except (TypeError, ValueError):
            sav = 0
        bav: Dict[str, int] = {}
        for planet in _AV_PLANETS:
            bindus = ((bav_root.get(planet) or {}).get("bindus") or {})
            try:
                bav[planet] = int(bindus.get(str(sign0), bindus.get(sign0, 0)) or 0)
            except (TypeError, ValueError):
                bav[planet] = 0
        rows[house] = {
            "house": house,
            "sign": SIGN_NAMES[sign0],
            "sav": sav,
            "bav": bav,
        }
    return rows


def _derive_daily_ashtakavarga(
    static_context: Dict[str, Any],
    dasha_rows: List[Dict[str, Any]],
    event_houses: List[int],
) -> Dict[str, Any]:
    av_rows = _av_house_rows(static_context)
    if not av_rows or all(row.get("sav", 0) == 0 for row in av_rows.values()):
        return {
            "method": "ashtakavarga_daily_v1",
            "available": False,
            "verdict": "ashtakavarga_data_unavailable",
        }

    house_support: List[Dict[str, Any]] = []
    for house in event_houses[:8]:
        row = av_rows.get(house)
        if not row:
            continue
        house_support.append({
            "house": house,
            "sign": row.get("sign"),
            "sav": row.get("sav"),
            "strength": _av_strength(int(row.get("sav") or 0), None),
            "domains": _house_domains(house),
        })

    transit_usability: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    for dasha in dasha_rows:
        level = str(dasha.get("level") or "")
        if level not in {"PD", "SK", "PR"}:
            continue
        planet = str(dasha.get("planet") or "")
        transit = dasha.get("transit") or {}
        house = int(transit.get("house") or 0)
        row = av_rows.get(house)
        if not row:
            continue
        bav = (row.get("bav") or {}).get(planet) if planet in _AV_PLANETS else None
        strength = _av_strength(int(row.get("sav") or 0), bav)
        transit_usability.append({
            "level": level,
            "planet": planet,
            "transit_house": house,
            "transit_sign": row.get("sign"),
            "sav": row.get("sav"),
            "planet_bav": bav,
            "strength": strength,
            "rule": "Daily AV judges local usability: active dasha lord's transit house SAV plus that planet's BAV in the sign.",
        })
        if int(row.get("sav") or 0) >= 30 and bav is not None and bav < 3:
            conflicts.append({
                "level": level,
                "planet": planet,
                "house": house,
                "conflict": "high_sav_low_planet_bav",
                "meaning": "The field is supportive, but this dasha planet delivers it with friction.",
            })
        elif int(row.get("sav") or 0) < 25 and bav is not None and bav >= 4:
            conflicts.append({
                "level": level,
                "planet": planet,
                "house": house,
                "conflict": "low_sav_high_planet_bav",
                "meaning": "The broader field is resistant, but this dasha planet has localized ability to act.",
            })

    return {
        "method": "ashtakavarga_daily_v1",
        "available": True,
        "event_house_support": house_support,
        "dasha_transit_usability": transit_usability,
        "conflicts": conflicts,
        "verdict": "supportive" if any(row.get("strength") == "strong" for row in transit_usability) else "mixed_or_workable",
    }


def _derive_daily_school_judgments(
    *,
    static_context: Dict[str, Any],
    intent: Dict[str, Any],
    dasha_rows: List[Dict[str, Any]],
    trigger_rows: List[Dict[str, Any]],
    all_natal_rows: Dict[str, Dict[str, Any]],
    moon_transit: Dict[str, Any],
    daily_judgment: Dict[str, Any],
) -> Dict[str, Any]:
    event_houses = _event_houses_for_intent(intent, daily_judgment)
    return {
        "method": "daily_school_judgments_v1",
        "event_houses": event_houses,
        "parashari": {
            "method": "parashari_daily_v1",
            "principle": "PR/SK/PD are the event triggers; AD/MD are permission. Use transit conjunction/aspect/return evidence before broad natal reading.",
            "top_triggers": trigger_rows[:5],
            "activated_houses": daily_judgment.get("top_activated_houses") or [],
            "massive_result_factors": daily_judgment.get("massive_result_factors") or [],
        },
        "nadi": _derive_daily_nadi(dasha_rows, all_natal_rows, moon_transit),
        "jaimini": _derive_daily_jaimini(static_context, dasha_rows, all_natal_rows, moon_transit),
        "kp": _derive_daily_kp(static_context, dasha_rows, event_houses),
        "ashtakavarga": _derive_daily_ashtakavarga(static_context, dasha_rows, event_houses),
        "merge_rule": (
            "Parashari gives the main day event trigger; KP confirms materialization through event cusps; "
            "Nadi explains subtle linkage/activation; Jaimini explains karaka-level manifestation; "
            "Ashtakavarga modifies ease, resistance, and confidence."
        ),
    }


def build_daily_prediction_spine(
    *,
    birth_data: Dict[str, Any],
    static_context: Dict[str, Any],
    intent_result: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Return deterministic daily evidence, or None when not an exact-day query."""
    intent = intent_result if isinstance(intent_result, dict) else {}
    mode = str(intent.get("mode") or "").upper()
    as_of = intent.get("dasha_as_of")
    if mode != "PREDICT_DAILY" and not as_of:
        return None

    try:
        target_dt = datetime.strptime(str(as_of)[:10], "%Y-%m-%d") if as_of else datetime.now()
    except (TypeError, ValueError):
        target_dt = datetime.now()
    target_dt = target_dt.replace(hour=12, minute=0, second=0, microsecond=0)

    d1_chart = static_context.get("d1_chart") or {}
    ascendant = float(d1_chart.get("ascendant", 0.0) or 0.0)
    asc_sign = _sign0(ascendant)
    house_lordships = house_lordships_from_ascendant(asc_sign)
    planetary_analysis = static_context.get("planetary_analysis") or {}
    rtc = RealTransitCalculator()

    all_natal_rows = {
        planet: _planet_natal_row(planet, d1_chart, planetary_analysis, house_lordships, rtc)
        for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
        if (d1_chart.get("planets") or {}).get(planet)
    }

    raw_dashas = DashaCalculator().calculate_dashas_for_date(target_dt, birth_data)
    dasha_rows: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    trigger_rows: List[Dict[str, Any]] = []

    for key, label, base_weight in _DASHA_LEVELS:
        info = raw_dashas.get(key) or {}
        planet = info.get("planet")
        if not planet or planet not in all_natal_rows:
            continue
        natal = all_natal_rows[planet]
        transit = _planet_transit_row(planet, target_dt, ascendant, rtc)
        trigger = _build_trigger_evidence(planet, natal, transit, all_natal_rows)
        trigger["level"] = label
        trigger["weighted_score"] = int(base_weight + trigger.get("score", 0))
        trigger_rows.append(trigger)
        row_key = (label, planet)
        if row_key not in seen:
            dasha_rows.append({
                "level": label,
                "planet": planet,
                "start": _iso_date(info.get("start")),
                "end": _iso_date(info.get("end")),
                "natal": natal,
                "transit": transit,
                "trigger": trigger,
            })
            seen.add(row_key)

    lat = float(birth_data.get("latitude") or 0.0)
    lon = float(birth_data.get("longitude") or 0.0)
    tz = birth_data.get("timezone")
    panchang = PanchangCalculator().calculate_panchang(
        target_dt.strftime("%Y-%m-%d"),
        "12:00:00",
        lat,
        lon,
        timezone=str(tz) if tz is not None else None,
    )

    moon_transit = _planet_transit_row("Moon", target_dt, ascendant, rtc)
    natal_moon = all_natal_rows.get("Moon") or {}
    moon_tara = _tara_from_indexes(
        natal_moon.get("nakshatra_index"),
        moon_transit.get("nakshatra_index") if moon_transit.get("available") else None,
    )

    trigger_rows.sort(key=lambda item: item.get("weighted_score", 0), reverse=True)
    daily_judgment = _derive_daily_judgment(dasha_rows, trigger_rows, moon_tara)
    school_judgments = _derive_daily_school_judgments(
        static_context=static_context,
        intent=intent,
        dasha_rows=dasha_rows,
        trigger_rows=trigger_rows,
        all_natal_rows=all_natal_rows,
        moon_transit=moon_transit,
        daily_judgment=daily_judgment,
    )
    return {
        "target_date": target_dt.strftime("%Y-%m-%d"),
        "method": "daily_spine_v1",
        "panchanga": {
            "vara": ((panchang.get("vara") or {}).get("name") or ""),
            "tithi": ((panchang.get("tithi") or {}).get("name") or ""),
            "paksha": ((panchang.get("tithi") or {}).get("paksha") or ""),
            "yoga": ((panchang.get("yoga") or {}).get("name") or ""),
            "karana": ((panchang.get("karana") or {}).get("name") or ""),
        },
        "moon": {
            "natal": natal_moon,
            "transit": moon_transit,
            "tara_bala": moon_tara,
        },
        "dasha_stack": dasha_rows,
        "ranked_triggers": trigger_rows[:8],
        "daily_judgment": daily_judgment,
        "school_judgments": school_judgments,
        "interpretation_rules": [
            "For daily prediction, Prana and Sookshma lords are the sharpest event triggers; PD is the main day frame; AD/MD are background permission.",
            "If a dasha lord transits its natal sign, natal degree, natal nakshatra, or aspects/conjoins its natal position, treat that planet's natal house and lordship results as strongly activated.",
            "Conjunction/aspect to other natal planets activates both planets' houses, lordships, and karakatwa; synthesize concrete events from those house combinations.",
            "Use daily_judgment.top_activated_houses and daily_judgment.top_event_domains to keep the answer concrete and ranked by event likelihood.",
            "Use school_judgments to cross-check the day through Parashari, Nadi, Jaimini, KP, and Ashtakavarga instead of giving broad lifetime branch reports.",
            "Use slow planets as background unless they are one of the active five dasha lords or directly hit a natal dasha lord.",
        ],
    }
