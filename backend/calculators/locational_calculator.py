"""
Personal locational astrology (Vedic digvijaya + relocated charts).

MVP: direction scores by goal + India metro ranking from relocated D1.
Planet longitudes stay fixed for a birth moment; houses/ASC change with lat/lon.
Timezone must remain the *birth* timezone so JD does not shift.
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from calculators.chart_calculator import ChartCalculator
from utils.timezone_service import parse_timezone_offset

SIGN_LORDS = [
    "Mars",
    "Venus",
    "Mercury",
    "Moon",
    "Sun",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Saturn",
    "Jupiter",
]

SIGN_NAMES = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

# Ashta Dikpala style direction lords (travel / digvijaya layer)
DIRECTION_LORDS: Dict[str, str] = {
    "East": "Sun",
    "Southeast": "Venus",
    "South": "Mars",
    "Southwest": "Rahu",
    "West": "Saturn",
    "Northwest": "Moon",
    "North": "Mercury",
    "Northeast": "Jupiter",
}

COMPASS_BEARING: Dict[str, float] = {
    "East": 90.0,
    "Southeast": 135.0,
    "South": 180.0,
    "Southwest": 225.0,
    "West": 270.0,
    "Northwest": 315.0,
    "North": 0.0,
    "Northeast": 45.0,
}

GOAL_HOUSES: Dict[str, List[int]] = {
    "career": [10, 6, 2],
    "job": [10, 6, 2],
    "promotion": [10, 11, 6],
    "business": [10, 7, 11],
    "wealth": [2, 11, 5],
    "money": [2, 11, 5],
    "finance": [2, 11, 5],
    "relationship": [7, 5, 2],
    "love": [7, 5, 2],
    "marriage": [7, 2, 11],
    "partner": [7, 5, 2],
    "health": [1, 6, 8],
    "education": [4, 5, 9],
    "learning": [4, 5, 9],
    "property": [4, 11, 12],
    "home": [4, 11, 12],
    "travel": [3, 9, 12],
    "visa": [9, 12, 3],
    "foreign": [9, 12, 7],
    "general": [1, 10, 11],
}

GOAL_KARAKAS: Dict[str, List[str]] = {
    "career": ["Saturn", "Sun", "Mercury"],
    "job": ["Saturn", "Sun", "Mercury"],
    "promotion": ["Sun", "Jupiter", "Mercury"],
    "business": ["Mercury", "Jupiter", "Sun"],
    "wealth": ["Jupiter", "Venus", "Mercury"],
    "money": ["Jupiter", "Venus", "Mercury"],
    "finance": ["Jupiter", "Venus", "Mercury"],
    "relationship": ["Venus", "Jupiter", "Moon"],
    "love": ["Venus", "Moon", "Mars"],
    "marriage": ["Venus", "Jupiter", "Moon"],
    "partner": ["Venus", "Jupiter", "Moon"],
    "health": ["Sun", "Moon", "Mars"],
    "education": ["Mercury", "Jupiter", "Moon"],
    "learning": ["Mercury", "Jupiter", "Moon"],
    "property": ["Mars", "Moon", "Venus"],
    "home": ["Moon", "Mars", "Venus"],
    "travel": ["Moon", "Rahu", "Mercury"],
    "visa": ["Rahu", "Saturn", "Moon"],
    "foreign": ["Rahu", "Saturn", "Moon"],
    "general": ["Jupiter", "Moon", "Sun"],
}

# Curated India metros for ranking
INDIA_METROS: List[Dict[str, Any]] = [
    {"name": "Delhi NCR", "latitude": 28.6139, "longitude": 77.2090, "country": "India", "region": "india"},
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "country": "India", "region": "india"},
    {"name": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946, "country": "India", "region": "india"},
    {"name": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867, "country": "India", "region": "india"},
    {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "country": "India", "region": "india"},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "country": "India", "region": "india"},
    {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567, "country": "India", "region": "india"},
    {"name": "Ahmedabad", "latitude": 23.0225, "longitude": 72.5714, "country": "India", "region": "india"},
    {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873, "country": "India", "region": "india"},
    {"name": "Lucknow", "latitude": 26.8467, "longitude": 80.9462, "country": "India", "region": "india"},
    {"name": "Chandigarh", "latitude": 30.7333, "longitude": 76.7794, "country": "India", "region": "india"},
    {"name": "Kochi", "latitude": 9.9312, "longitude": 76.2673, "country": "India", "region": "india"},
    {"name": "Indore", "latitude": 22.7196, "longitude": 75.8577, "country": "India", "region": "india"},
    {"name": "Nagpur", "latitude": 21.1458, "longitude": 79.0882, "country": "India", "region": "india"},
    {"name": "Bhopal", "latitude": 23.2599, "longitude": 77.4126, "country": "India", "region": "india"},
]

# Curated global hubs for abroad / India+abroad ranking
GLOBAL_HUBS: List[Dict[str, Any]] = [
    {"name": "Dubai", "latitude": 25.2048, "longitude": 55.2708, "country": "UAE", "region": "abroad"},
    {"name": "Abu Dhabi", "latitude": 24.4539, "longitude": 54.3773, "country": "UAE", "region": "abroad"},
    {"name": "Doha", "latitude": 25.2854, "longitude": 51.5310, "country": "Qatar", "region": "abroad"},
    {"name": "Riyadh", "latitude": 24.7136, "longitude": 46.6753, "country": "Saudi Arabia", "region": "abroad"},
    {"name": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "country": "Singapore", "region": "abroad"},
    {"name": "Hong Kong", "latitude": 22.3193, "longitude": 114.1694, "country": "Hong Kong", "region": "abroad"},
    {"name": "Tokyo", "latitude": 35.6762, "longitude": 139.6503, "country": "Japan", "region": "abroad"},
    {"name": "Bangkok", "latitude": 13.7563, "longitude": 100.5018, "country": "Thailand", "region": "abroad"},
    {"name": "Sydney", "latitude": -33.8688, "longitude": 151.2093, "country": "Australia", "region": "abroad"},
    {"name": "Melbourne", "latitude": -37.8136, "longitude": 144.9631, "country": "Australia", "region": "abroad"},
    {"name": "London", "latitude": 51.5074, "longitude": -0.1278, "country": "UK", "region": "abroad"},
    {"name": "Dublin", "latitude": 53.3498, "longitude": -6.2603, "country": "Ireland", "region": "abroad"},
    {"name": "Berlin", "latitude": 52.5200, "longitude": 13.4050, "country": "Germany", "region": "abroad"},
    {"name": "Amsterdam", "latitude": 52.3676, "longitude": 4.9041, "country": "Netherlands", "region": "abroad"},
    {"name": "Toronto", "latitude": 43.6532, "longitude": -79.3832, "country": "Canada", "region": "abroad"},
    {"name": "Vancouver", "latitude": 49.2827, "longitude": -123.1207, "country": "Canada", "region": "abroad"},
    {"name": "New York", "latitude": 40.7128, "longitude": -74.0060, "country": "USA", "region": "abroad"},
    {"name": "San Francisco Bay Area", "latitude": 37.7749, "longitude": -122.4194, "country": "USA", "region": "abroad"},
    {"name": "Seattle", "latitude": 47.6062, "longitude": -122.3321, "country": "USA", "region": "abroad"},
    {"name": "Austin", "latitude": 30.2672, "longitude": -97.7431, "country": "USA", "region": "abroad"},
]

VALID_LOCATION_SCOPES = frozenset({"india", "abroad", "both"})


def normalize_location_scope(value: Any) -> Optional[str]:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "india": "india",
        "india_only": "india",
        "domestic": "india",
        "within_india": "india",
        "indian": "india",
        "abroad": "abroad",
        "overseas": "abroad",
        "foreign": "abroad",
        "international": "abroad",
        "outside_india": "abroad",
        "both": "both",
        "india_and_abroad": "both",
        "anywhere": "both",
        "either": "both",
        "all": "both",
    }
    scope = aliases.get(raw)
    return scope if scope in VALID_LOCATION_SCOPES else None


def candidate_cities_for_scope(location_scope: str) -> List[Dict[str, Any]]:
    scope = normalize_location_scope(location_scope) or "india"
    if scope == "abroad":
        return list(GLOBAL_HUBS)
    if scope == "both":
        return list(INDIA_METROS) + list(GLOBAL_HUBS)
    return list(INDIA_METROS)

OWN_SIGNS = {
    "Sun": {4},
    "Moon": {3},
    "Mars": {0, 7},
    "Mercury": {2, 5},
    "Jupiter": {8, 11},
    "Venus": {1, 6},
    "Saturn": {9, 10},
    "Rahu": {10},
    "Ketu": {4},
}

EXALTATION = {
    "Sun": 0,
    "Moon": 1,
    "Mars": 9,
    "Mercury": 5,
    "Jupiter": 3,
    "Venus": 11,
    "Saturn": 6,
    "Rahu": 2,
    "Ketu": 8,
}

DEBILITATION = {
    "Sun": 6,
    "Moon": 7,
    "Mars": 3,
    "Mercury": 11,
    "Jupiter": 9,
    "Venus": 5,
    "Saturn": 0,
    "Rahu": 8,
    "Ketu": 2,
}

MALEFICS = frozenset({"Mars", "Saturn", "Rahu", "Ketu", "Sun"})
BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})


def _extract_dasha_lords(current_dashas: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    """Support both flat current_dashas and nested vimshottari shapes."""
    if not isinstance(current_dashas, dict):
        return None, None

    def _planet(val: Any) -> Optional[str]:
        if isinstance(val, dict):
            p = val.get("planet") or val.get("lord") or val.get("name")
            return str(p) if p else None
        if isinstance(val, str) and val.strip():
            return val.strip()
        return None

    md = _planet(current_dashas.get("mahadasha") or current_dashas.get("maha_dasha"))
    ad = _planet(current_dashas.get("antardasha") or current_dashas.get("antar_dasha"))
    if md or ad:
        return md, ad

    vim = current_dashas.get("vimshottari") or current_dashas.get("Vimshottari") or {}
    if isinstance(vim, dict):
        md = _planet(vim.get("mahadasha") or vim.get("maha_dasha") or vim.get("md"))
        ad = _planet(vim.get("antardasha") or vim.get("antar_dasha") or vim.get("ad"))
    return md, ad


def normalize_goal_category(category: Optional[str]) -> str:
    cat = str(category or "general").strip().lower()
    aliases = {
        "spouse": "marriage",
        "child": "general",
        "children": "general",
        "pregnancy": "general",
        "disease": "health",
        "soul": "general",
        "spirituality": "general",
        "purpose": "general",
        "dharma": "general",
        "timing": "general",
    }
    return aliases.get(cat, cat if cat in GOAL_HOUSES else "general")


def _planet_sign(planets: Dict[str, Any], planet: str) -> Optional[int]:
    data = planets.get(planet) or {}
    if not isinstance(data, dict):
        return None
    if data.get("sign") is not None:
        try:
            return int(data["sign"])
        except (TypeError, ValueError):
            pass
    lon = data.get("longitude")
    if lon is None:
        return None
    try:
        return int(float(lon) / 30.0) % 12
    except (TypeError, ValueError):
        return None


def _planet_house(planets: Dict[str, Any], planet: str) -> Optional[int]:
    data = planets.get(planet) or {}
    if not isinstance(data, dict):
        return None
    try:
        house = int(data.get("house"))
    except (TypeError, ValueError):
        return None
    return house if 1 <= house <= 12 else None


def _lord_of_house(asc_sign: int, house: int) -> str:
    sign = (int(asc_sign) + int(house) - 1) % 12
    return SIGN_LORDS[sign]


def _dignity_score(planet: str, sign: Optional[int]) -> float:
    if sign is None:
        return 0.0
    score = 0.0
    if sign in OWN_SIGNS.get(planet, set()):
        score += 2.5
    if EXALTATION.get(planet) == sign:
        score += 3.0
    if DEBILITATION.get(planet) == sign:
        score -= 2.5
    return score


def _house_quality(house: Optional[int]) -> float:
    if house is None:
        return 0.0
    if house in (1, 4, 7, 10):
        return 2.0
    if house in (5, 9):
        return 1.5
    if house in (2, 11):
        return 1.0
    if house in (6, 8, 12):
        return -1.0
    return 0.0


def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def _bearing_to_direction(bearing: float) -> str:
    sectors = (
        (22.5, "North"),
        (67.5, "Northeast"),
        (112.5, "East"),
        (157.5, "Southeast"),
        (202.5, "South"),
        (247.5, "Southwest"),
        (292.5, "West"),
        (337.5, "Northwest"),
        (360.0, "North"),
    )
    for limit, name in sectors:
        if bearing < limit:
            return name
    return "North"


def _angular_diff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _resolve_birth_timezone(birth_data: Dict[str, Any]) -> float:
    tz_input = birth_data.get("timezone", "")
    lat = birth_data.get("latitude")
    lon = birth_data.get("longitude")
    date_str = str(birth_data.get("date") or "").split("T")[0] or None
    return float(parse_timezone_offset(tz_input, lat, lon, for_date=date_str))


def _relocated_birth_obj(birth_data: Dict[str, Any], latitude: float, longitude: float, place: str) -> SimpleNamespace:
    birth_tz = _resolve_birth_timezone(birth_data)
    return SimpleNamespace(
        name=birth_data.get("name", "Native"),
        date=str(birth_data.get("date") or "").split("T")[0],
        time=birth_data.get("time"),
        latitude=float(latitude),
        longitude=float(longitude),
        place=place,
        timezone=birth_tz,  # keep birth JD fixed
        gender=birth_data.get("gender", ""),
    )


def _extract_asc_sign(chart: Dict[str, Any]) -> int:
    asc = chart.get("ascendant")
    if isinstance(asc, (int, float)):
        return int(float(asc) / 30.0) % 12
    if isinstance(asc, dict):
        if asc.get("sign") is not None:
            try:
                return int(asc["sign"]) % 12
            except (TypeError, ValueError):
                pass
        lon = asc.get("longitude")
        if lon is not None:
            return int(float(lon) / 30.0) % 12

    houses = chart.get("houses")
    h1 = None
    if isinstance(houses, list) and houses:
        h1 = houses[0]
    elif isinstance(houses, dict):
        h1 = houses.get("1") or houses.get(1) or houses.get("House1")
    if isinstance(h1, dict):
        if h1.get("sign") is not None:
            return int(h1["sign"]) % 12
        lon = h1.get("longitude")
        if lon is not None:
            return int(float(lon) / 30.0) % 12
    return 0


class LocationalCalculator:
    """Score digvijaya directions and rank India metros for a life goal."""

    def __init__(self) -> None:
        self._chart_calc = ChartCalculator({})

    def analyze(
        self,
        birth_data: Dict[str, Any],
        *,
        category: str = "general",
        location_scope: str = "india",
        natal_chart: Optional[Dict[str, Any]] = None,
        current_dashas: Optional[Dict[str, Any]] = None,
        top_n: int = 5,
        metros: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        goal = normalize_goal_category(category)
        scope = normalize_location_scope(location_scope) or "india"
        goal_houses = list(GOAL_HOUSES.get(goal, GOAL_HOUSES["general"]))
        # Foreign settlement questions emphasize 9th/12th alongside the goal.
        if scope in {"abroad", "both"}:
            for house in (9, 12):
                if house not in goal_houses:
                    goal_houses.append(house)
        karakas = list(GOAL_KARAKAS.get(goal, GOAL_KARAKAS["general"]))
        if scope in {"abroad", "both"}:
            for planet in ("Rahu", "Saturn", "Moon"):
                if planet not in karakas:
                    karakas.append(planet)

        if natal_chart is None:
            natal_obj = _relocated_birth_obj(
                birth_data,
                float(birth_data["latitude"]),
                float(birth_data["longitude"]),
                str(birth_data.get("place") or "Birth place"),
            )
            natal_chart = self._chart_calc.calculate_chart(natal_obj)

        planets = natal_chart.get("planets") or {}
        asc_sign = _extract_asc_sign(natal_chart)

        direction_scores = self._score_directions(planets, asc_sign, goal_houses, karakas)
        prefer = [d["direction"] for d in direction_scores[:3]]
        avoid = [d["direction"] for d in sorted(direction_scores, key=lambda x: x["score"])[:2]]

        birth_lat = float(birth_data["latitude"])
        birth_lon = float(birth_data["longitude"])
        city_rows: List[Dict[str, Any]] = []
        for metro in list(metros or candidate_cities_for_scope(scope)):
            try:
                row = self._score_metro(
                    birth_data=birth_data,
                    metro=metro,
                    birth_lat=birth_lat,
                    birth_lon=birth_lon,
                    goal_houses=goal_houses,
                    karakas=karakas,
                    prefer_directions=prefer,
                    current_dashas=current_dashas,
                    location_scope=scope,
                )
                city_rows.append(row)
            except Exception:
                continue

        city_rows.sort(key=lambda r: r["score"], reverse=True)
        limit = max(1, min(int(top_n), 8))
        india_rows = [c for c in city_rows if c.get("region") == "india"]
        abroad_rows = [c for c in city_rows if c.get("region") == "abroad"]
        if scope == "both":
            top_india = india_rows[: min(3, limit)]
            top_abroad = abroad_rows[: min(3, limit)]
            # Prefer balanced shortlist, then fill from overall rank.
            merged: List[Dict[str, Any]] = []
            seen = set()
            for row in top_india + top_abroad + city_rows:
                key = row["name"]
                if key in seen:
                    continue
                seen.add(key)
                merged.append(row)
                if len(merged) >= limit:
                    break
            top_cities = merged
        else:
            top_india = india_rows[:limit] if scope == "india" else []
            top_abroad = abroad_rows[:limit] if scope == "abroad" else []
            top_cities = city_rows[:limit]

        md_lord, ad_lord = _extract_dasha_lords(current_dashas)

        return {
            "schema_version": "locational_recommendation.v1",
            "goal_category": goal,
            "location_scope": scope,
            "goal_houses": goal_houses,
            "goal_karakas": karakas,
            "method_notes": [
                "Direction scores use Ashta-Dikpala lords weighted by dignity, house quality, and link to goal houses/karakas.",
                "City scores use relocated D1 (same birth JD, new lat/lon): ASC quality, goal-house occupancy, lord strength, dasha-lord placement, and compass alignment to preferred directions.",
                "Candidate pool is India metros, curated global hubs, or both — based on location_scope. Not Western ASC/MC ACG lines.",
            ],
            "birth_place": {
                "place": birth_data.get("place"),
                "latitude": birth_lat,
                "longitude": birth_lon,
            },
            "preferred_directions": prefer,
            "avoid_directions": avoid,
            "direction_scores": direction_scores,
            "top_cities": top_cities,
            "top_cities_india": top_india,
            "top_cities_abroad": top_abroad,
            "all_cities_ranked": [
                {
                    "name": c["name"],
                    "score": c["score"],
                    "compass_direction": c["compass_direction"],
                    "country": c.get("country"),
                    "region": c.get("region"),
                }
                for c in city_rows
            ],
            "timing_caution": {
                "mahadasha_lord": md_lord,
                "antardasha_lord": ad_lord,
                "note": (
                    "Favor moves when current dasha lords support the goal houses in the chosen city's relocated chart; "
                    "avoid locking long leases while dasha lords are heavily afflicted in dusthana houses there."
                ),
            },
            "disclaimer": (
                "Locational guidance is probabilistic chart support for direction and city shortlisting, "
                "not a guarantee of job, wealth, visa, or relationship outcomes."
            ),
        }

    def _score_directions(
        self,
        planets: Dict[str, Any],
        asc_sign: int,
        goal_houses: Sequence[int],
        karakas: Sequence[str],
    ) -> List[Dict[str, Any]]:
        goal_lords = {_lord_of_house(asc_sign, h) for h in goal_houses}
        rows: List[Dict[str, Any]] = []
        for direction, lord in DIRECTION_LORDS.items():
            sign = _planet_sign(planets, lord)
            house = _planet_house(planets, lord)
            score = 5.0 + _dignity_score(lord, sign) + _house_quality(house)
            reasons: List[str] = []

            if lord in goal_lords:
                score += 2.0
                reasons.append(f"{lord} rules a goal house")
            if any(_planet_house(planets, lord) == h for h in goal_houses):
                score += 1.5
                reasons.append(f"{lord} sits in a goal house")

            for karaka in karakas:
                k_house = _planet_house(planets, karaka)
                k_sign = _planet_sign(planets, karaka)
                # Karaka in direction lord's sign or co-located house with direction lord
                if k_sign is not None and sign is not None and k_sign == sign:
                    score += 1.2
                    reasons.append(f"goal karaka {karaka} joins {lord}")
                if k_house is not None and house is not None and k_house == house and karaka != lord:
                    score += 0.8

            # Dusthana direction lord = caution
            if house in (6, 8, 12):
                reasons.append(f"{lord} is in dusthana from lagna")

            rows.append(
                {
                    "direction": direction,
                    "lord": lord,
                    "score": round(score, 2),
                    "lord_sign": SIGN_NAMES[sign] if sign is not None else None,
                    "lord_house": house,
                    "reasons": reasons[:4],
                }
            )

        rows.sort(key=lambda r: r["score"], reverse=True)
        return rows

    def _score_metro(
        self,
        *,
        birth_data: Dict[str, Any],
        metro: Dict[str, Any],
        birth_lat: float,
        birth_lon: float,
        goal_houses: Sequence[int],
        karakas: Sequence[str],
        prefer_directions: Sequence[str],
        current_dashas: Optional[Dict[str, Any]],
        location_scope: str = "india",
    ) -> Dict[str, Any]:
        lat = float(metro["latitude"])
        lon = float(metro["longitude"])
        name = str(metro["name"])
        region = str(metro.get("region") or ("india" if metro.get("country") == "India" else "abroad"))
        country = str(metro.get("country") or metro.get("state") or "")
        obj = _relocated_birth_obj(birth_data, lat, lon, name)
        chart = self._chart_calc.calculate_chart(obj)
        planets = chart.get("planets") or {}
        asc_sign = _extract_asc_sign(chart)
        asc_lord = SIGN_LORDS[asc_sign]
        asc_lord_house = _planet_house(planets, asc_lord)
        asc_lord_sign = _planet_sign(planets, asc_lord)

        score = 10.0 + _dignity_score(asc_lord, asc_lord_sign) + _house_quality(asc_lord_house)
        reasons: List[str] = [f"Relocated ASC {SIGN_NAMES[asc_sign]} (lord {asc_lord})"]
        if location_scope in {"abroad", "both"} and region == "abroad":
            # Slight preference signal for foreign hubs when user wants abroad options.
            rahu_house = _planet_house(planets, "Rahu")
            if rahu_house in (1, 9, 10, 11):
                score += 1.0
                reasons.append("Rahu supports foreign/visibility houses in relocated chart")

        # Occupancy of goal houses
        for house in goal_houses:
            occupants = [
                p
                for p, pdata in planets.items()
                if isinstance(pdata, dict) and _planet_house(planets, p) == house
            ]
            for p in occupants:
                if p in BENEFICS:
                    score += 1.4
                    reasons.append(f"Benefic {p} in relocated {house}H")
                elif p in MALEFICS:
                    score -= 0.9
                    reasons.append(f"Malefic {p} in relocated {house}H")

            lord = _lord_of_house(asc_sign, house)
            score += 0.6 * (_dignity_score(lord, _planet_sign(planets, lord)) / 3.0)
            score += 0.5 * _house_quality(_planet_house(planets, lord))

        for karaka in karakas[:2]:
            score += 0.4 * _house_quality(_planet_house(planets, karaka))
            score += 0.3 * _dignity_score(karaka, _planet_sign(planets, karaka))

        # Current dasha lords in relocated chart
        md_lord, ad_lord = _extract_dasha_lords(current_dashas)
        for lord in [x for x in (md_lord, ad_lord) if x]:
            h = _planet_house(planets, lord)
            bump = _house_quality(h)
            score += bump
            if bump >= 1.5:
                reasons.append(f"Dasha lord {lord} angular/trikonal in relocated chart")
            elif bump < 0:
                reasons.append(f"Dasha lord {lord} in dusthana in relocated chart")

        bearing = _bearing_deg(birth_lat, birth_lon, lat, lon)
        compass = _bearing_to_direction(bearing)
        if compass in prefer_directions[:2]:
            score += 2.0
            reasons.append(f"Lies {compass} of birth place (preferred digvijaya)")
        elif compass in prefer_directions[2:3]:
            score += 1.0
            reasons.append(f"Lies {compass} of birth place")
        elif prefer_directions:
            # mild penalty if opposite preferred sector
            pref_bearing = COMPASS_BEARING.get(prefer_directions[0], 0.0)
            if _angular_diff(bearing, pref_bearing) > 135.0:
                score -= 0.8

        # Near birth place: still valid but note staying local
        dist_proxy = abs(lat - birth_lat) + abs(lon - birth_lon)
        if dist_proxy < 0.8:
            reasons.append("Near birth coordinates (local reinforcement)")

        return {
            "name": name,
            "state": metro.get("state"),
            "country": country,
            "region": region,
            "latitude": lat,
            "longitude": lon,
            "score": round(score, 2),
            "compass_direction": compass,
            "bearing_deg": round(bearing, 1),
            "relocated_ascendant": SIGN_NAMES[asc_sign],
            "relocated_asc_lord": asc_lord,
            "reasons": reasons[:6],
        }
