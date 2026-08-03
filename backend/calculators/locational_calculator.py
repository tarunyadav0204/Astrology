"""
Personal locational astrology (Vedic digvijaya + relocated charts).

MVP: direction scores by goal + India metro / regional abroad hub ranking
from relocated D1. Abroad hubs are grouped by region pack (Gulf, SE Asia,
East Asia, Europe, UK/Ireland, Oceania, North America, Africa).
Planet longitudes stay fixed for a birth moment; houses/ASC change with lat/lon.
Timezone must remain the *birth* timezone so JD does not shift.
"""

from __future__ import annotations

import math
import re
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
    {"name": "Delhi NCR", "latitude": 28.6139, "longitude": 77.2090, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Ahmedabad", "latitude": 23.0225, "longitude": 72.5714, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Lucknow", "latitude": 26.8467, "longitude": 80.9462, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Chandigarh", "latitude": 30.7333, "longitude": 76.7794, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Kochi", "latitude": 9.9312, "longitude": 76.2673, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Indore", "latitude": 22.7196, "longitude": 75.8577, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Nagpur", "latitude": 21.1458, "longitude": 79.0882, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Bhopal", "latitude": 23.2599, "longitude": 77.4126, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Surat", "latitude": 21.1702, "longitude": 72.8311, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Coimbatore", "latitude": 11.0168, "longitude": 76.9558, "country": "India", "region": "india", "hub_region": "india"},
    {"name": "Visakhapatnam", "latitude": 17.6868, "longitude": 83.2185, "country": "India", "region": "india", "hub_region": "india"},
]


def _hub(name: str, lat: float, lon: float, country: str, hub_region: str) -> Dict[str, Any]:
    return {
        "name": name,
        "latitude": lat,
        "longitude": lon,
        "country": country,
        "region": "abroad",
        "hub_region": hub_region,
    }


# Region-specific abroad packs (flattened into GLOBAL_HUBS below).
HUB_REGION_PACKS: Dict[str, List[Dict[str, Any]]] = {
    "gulf": [
        _hub("Dubai", 25.2048, 55.2708, "UAE", "gulf"),
        _hub("Abu Dhabi", 24.4539, 54.3773, "UAE", "gulf"),
        _hub("Sharjah", 25.3463, 55.4209, "UAE", "gulf"),
        _hub("Doha", 25.2854, 51.5310, "Qatar", "gulf"),
        _hub("Riyadh", 24.7136, 46.6753, "Saudi Arabia", "gulf"),
        _hub("Jeddah", 21.4858, 39.1925, "Saudi Arabia", "gulf"),
        _hub("Kuwait City", 29.3759, 47.9774, "Kuwait", "gulf"),
        _hub("Manama", 26.2235, 50.5876, "Bahrain", "gulf"),
        _hub("Muscat", 23.5880, 58.3829, "Oman", "gulf"),
    ],
    "se_asia": [
        _hub("Singapore", 1.3521, 103.8198, "Singapore", "se_asia"),
        _hub("Bangkok", 13.7563, 100.5018, "Thailand", "se_asia"),
        _hub("Kuala Lumpur", 3.1390, 101.6869, "Malaysia", "se_asia"),
        _hub("Jakarta", -6.2088, 106.8456, "Indonesia", "se_asia"),
        _hub("Ho Chi Minh City", 10.8231, 106.6297, "Vietnam", "se_asia"),
        _hub("Hanoi", 21.0278, 105.8342, "Vietnam", "se_asia"),
        _hub("Manila", 14.5995, 120.9842, "Philippines", "se_asia"),
        _hub("Penang", 5.4141, 100.3288, "Malaysia", "se_asia"),
    ],
    "east_asia": [
        _hub("Hong Kong", 22.3193, 114.1694, "Hong Kong", "east_asia"),
        _hub("Tokyo", 35.6762, 139.6503, "Japan", "east_asia"),
        _hub("Osaka", 34.6937, 135.5023, "Japan", "east_asia"),
        _hub("Seoul", 37.5665, 126.9780, "South Korea", "east_asia"),
        _hub("Taipei", 25.0330, 121.5654, "Taiwan", "east_asia"),
        _hub("Shanghai", 31.2304, 121.4737, "China", "east_asia"),
    ],
    "europe": [
        _hub("Berlin", 52.5200, 13.4050, "Germany", "europe"),
        _hub("Frankfurt", 50.1109, 8.6821, "Germany", "europe"),
        _hub("Munich", 48.1351, 11.5820, "Germany", "europe"),
        _hub("Amsterdam", 52.3676, 4.9041, "Netherlands", "europe"),
        _hub("Paris", 48.8566, 2.3522, "France", "europe"),
        _hub("Zurich", 47.3769, 8.5417, "Switzerland", "europe"),
        _hub("Stockholm", 59.3293, 18.0686, "Sweden", "europe"),
        _hub("Barcelona", 41.3874, 2.1686, "Spain", "europe"),
        _hub("Milan", 45.4642, 9.1900, "Italy", "europe"),
        _hub("Warsaw", 52.2297, 21.0122, "Poland", "europe"),
        _hub("Lisbon", 38.7223, -9.1393, "Portugal", "europe"),
        _hub("Vienna", 48.2082, 16.3738, "Austria", "europe"),
    ],
    "uk_ireland": [
        _hub("London", 51.5074, -0.1278, "UK", "uk_ireland"),
        _hub("Manchester", 53.4808, -2.2426, "UK", "uk_ireland"),
        _hub("Edinburgh", 55.9533, -3.1883, "UK", "uk_ireland"),
        _hub("Dublin", 53.3498, -6.2603, "Ireland", "uk_ireland"),
    ],
    "oceania": [
        _hub("Sydney", -33.8688, 151.2093, "Australia", "oceania"),
        _hub("Melbourne", -37.8136, 144.9631, "Australia", "oceania"),
        _hub("Brisbane", -27.4698, 153.0251, "Australia", "oceania"),
        _hub("Perth", -31.9505, 115.8605, "Australia", "oceania"),
        _hub("Auckland", -36.8485, 174.7633, "New Zealand", "oceania"),
    ],
    "north_america": [
        _hub("Toronto", 43.6532, -79.3832, "Canada", "north_america"),
        _hub("Vancouver", 49.2827, -123.1207, "Canada", "north_america"),
        _hub("Calgary", 51.0447, -114.0719, "Canada", "north_america"),
        _hub("New York", 40.7128, -74.0060, "USA", "north_america"),
        _hub("San Francisco Bay Area", 37.7749, -122.4194, "USA", "north_america"),
        _hub("Seattle", 47.6062, -122.3321, "USA", "north_america"),
        _hub("Austin", 30.2672, -97.7431, "USA", "north_america"),
        _hub("Chicago", 41.8781, -87.6298, "USA", "north_america"),
        _hub("Dallas", 32.7767, -96.7970, "USA", "north_america"),
        _hub("Boston", 42.3601, -71.0589, "USA", "north_america"),
        _hub("Atlanta", 33.7490, -84.3880, "USA", "north_america"),
        _hub("Los Angeles", 34.0522, -118.2437, "USA", "north_america"),
    ],
    "africa": [
        _hub("Johannesburg", -26.2041, 28.0473, "South Africa", "africa"),
        _hub("Cape Town", -33.9249, 18.4241, "South Africa", "africa"),
        _hub("Nairobi", -1.2921, 36.8219, "Kenya", "africa"),
        _hub("Lagos", 6.5244, 3.3792, "Nigeria", "africa"),
        _hub("Cairo", 30.0444, 31.2357, "Egypt", "africa"),
    ],
}

HUB_REGION_LABELS: Dict[str, str] = {
    "india": "India",
    "gulf": "Gulf / GCC",
    "se_asia": "Southeast Asia",
    "east_asia": "East Asia",
    "europe": "Europe",
    "uk_ireland": "UK & Ireland",
    "oceania": "Australia & New Zealand",
    "north_america": "North America",
    "africa": "Africa",
}

VALID_HUB_REGIONS = frozenset(k for k in HUB_REGION_PACKS.keys())

# Flat abroad candidate list (all region packs).
GLOBAL_HUBS: List[Dict[str, Any]] = [
    city for pack in HUB_REGION_PACKS.values() for city in pack
]

VALID_LOCATION_SCOPES = frozenset({"india", "abroad", "both"})

# Text cues → hub_region (user-stated geography preference; never LLM-invented).
_HUB_REGION_TEXT_CUES: Dict[str, Tuple[str, ...]] = {
    "gulf": (
        "gulf",
        "gcc",
        "uae",
        "dubai",
        "abu dhabi",
        "sharjah",
        "qatar",
        "doha",
        "saudi",
        "riyadh",
        "jeddah",
        "kuwait",
        "bahrain",
        "oman",
        "muscat",
        "middle east",
        "गल्फ",
        "खाड़ी",
    ),
    "se_asia": (
        "southeast asia",
        "south east asia",
        "se asia",
        "asean",
        "singapore",
        "bangkok",
        "thailand",
        "malaysia",
        "kuala lumpur",
        "indonesia",
        "jakarta",
        "vietnam",
        "philippines",
        "manila",
        "दक्षिण पूर्व एशिया",
    ),
    "east_asia": (
        "east asia",
        "japan",
        "tokyo",
        "osaka",
        "korea",
        "seoul",
        "hong kong",
        "taiwan",
        "taipei",
        "shanghai",
        "china",
        "पूर्वी एशिया",
    ),
    "uk_ireland": (
        "uk",
        "u.k.",
        "united kingdom",
        "britain",
        "british",
        "london",
        "manchester",
        "edinburgh",
        "scotland",
        "england",
        "ireland",
        "dublin",
        "यूके",
    ),
    "europe": (
        "europe",
        "european",
        "eu",
        "germany",
        "berlin",
        "frankfurt",
        "munich",
        "netherlands",
        "amsterdam",
        "france",
        "paris",
        "switzerland",
        "zurich",
        "sweden",
        "stockholm",
        "spain",
        "barcelona",
        "italy",
        "milan",
        "poland",
        "warsaw",
        "portugal",
        "lisbon",
        "austria",
        "vienna",
        "यूरोप",
    ),
    "oceania": (
        "australia",
        "sydney",
        "melbourne",
        "brisbane",
        "perth",
        "new zealand",
        "auckland",
        "oceania",
        "ऑस्ट्रेलिया",
    ),
    "north_america": (
        "north america",
        "united states",
        "usa",
        "u.s.",
        "u.s.a",
        "america",
        "canada",
        "toronto",
        "vancouver",
        "calgary",
        "new york",
        "california",
        "san francisco",
        "seattle",
        "austin",
        "chicago",
        "dallas",
        "boston",
        "atlanta",
        "los angeles",
        "अमेरिका",
        "कनाडा",
    ),
    "africa": (
        "africa",
        "south africa",
        "johannesburg",
        "cape town",
        "kenya",
        "nairobi",
        "nigeria",
        "lagos",
        "egypt",
        "cairo",
        "अफ्रीका",
    ),
}


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


def normalize_hub_region(value: Any) -> Optional[str]:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "gulf": "gulf",
        "gcc": "gulf",
        "middle_east": "gulf",
        "uae": "gulf",
        "se_asia": "se_asia",
        "southeast_asia": "se_asia",
        "south_east_asia": "se_asia",
        "asean": "se_asia",
        "east_asia": "east_asia",
        "europe": "europe",
        "eu": "europe",
        "uk": "uk_ireland",
        "uk_ireland": "uk_ireland",
        "britain": "uk_ireland",
        "ireland": "uk_ireland",
        "oceania": "oceania",
        "australia": "oceania",
        "anz": "oceania",
        "north_america": "north_america",
        "usa": "north_america",
        "canada": "north_america",
        "america": "north_america",
        "africa": "africa",
        "india": "india",
    }
    region = aliases.get(raw)
    if region == "india":
        return "india"
    return region if region in VALID_HUB_REGIONS else None


def infer_hub_regions_from_text(user_question: str) -> List[str]:
    """
    Detect preferred abroad hub packs from user text (Gulf, Europe, SE Asia…).
    Deterministic word/phrase match only — never invent from LLM.
    """
    q = " ".join(str(user_question or "").lower().split())
    if not q:
        return []

    def _has_word(word: str) -> bool:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", q))

    found: List[str] = []
    for region, cues in _HUB_REGION_TEXT_CUES.items():
        for cue in cues:
            cue_l = cue.strip().lower()
            if not cue_l:
                continue
            # Avoid "east asia" matching inside "southeast asia".
            if cue_l == "east asia" and (
                "southeast asia" in q or "south east asia" in q or "se asia" in q
            ):
                continue
            # Short ASCII tokens need word boundaries ("uk", "eu", "usa").
            if " " not in cue_l and cue_l.isascii() and len(cue_l) <= 3:
                hit = _has_word(cue_l)
            elif cue_l in {"usa", "u.s.", "u.s.a", "u.k."}:
                hit = _has_word(cue_l.replace(".", "")) or cue_l in q or _has_word("usa")
            else:
                hit = cue_l in q
            if cue_l in {"eu", "uk"}:
                hit = _has_word(cue_l)
            if hit:
                found.append(region)
                break
    # Preserve pack order for stable shortlists.
    order = list(HUB_REGION_PACKS.keys())
    return [r for r in order if r in set(found)]


def candidate_cities_for_scope(
    location_scope: str,
    *,
    hub_regions: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    scope = normalize_location_scope(location_scope) or "india"
    wanted = []
    for raw in hub_regions or []:
        region = normalize_hub_region(raw)
        if region and region != "india" and region not in wanted:
            wanted.append(region)

    if scope == "india":
        return list(INDIA_METROS)

    if wanted:
        abroad = [city for region in wanted for city in HUB_REGION_PACKS.get(region, [])]
    else:
        abroad = list(GLOBAL_HUBS)

    if scope == "abroad":
        return abroad
    # both
    return list(INDIA_METROS) + abroad

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
        hub_regions: Optional[Sequence[str]] = None,
        natal_chart: Optional[Dict[str, Any]] = None,
        current_dashas: Optional[Dict[str, Any]] = None,
        top_n: int = 5,
        metros: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        goal = normalize_goal_category(category)
        scope = normalize_location_scope(location_scope) or "india"
        preferred_hub_regions: List[str] = []
        for raw in hub_regions or []:
            region = normalize_hub_region(raw)
            if region and region != "india" and region not in preferred_hub_regions:
                preferred_hub_regions.append(region)
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
        candidates = list(
            metros
            or candidate_cities_for_scope(scope, hub_regions=preferred_hub_regions or None)
        )
        city_rows: List[Dict[str, Any]] = []
        for metro in candidates:
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

        # Best city per abroad hub pack (helps answers when scanning many regions).
        top_by_hub_region: List[Dict[str, Any]] = []
        if scope in {"abroad", "both"}:
            region_order = preferred_hub_regions or list(HUB_REGION_PACKS.keys())
            for hub_key in region_order:
                best = next((c for c in abroad_rows if c.get("hub_region") == hub_key), None)
                if not best:
                    continue
                top_by_hub_region.append(
                    {
                        "hub_region": hub_key,
                        "hub_region_label": HUB_REGION_LABELS.get(hub_key, hub_key),
                        "city": best,
                    }
                )

        md_lord, ad_lord = _extract_dasha_lords(current_dashas)
        pool_note = (
            f"Abroad pool filtered to hub packs: {', '.join(preferred_hub_regions)}."
            if preferred_hub_regions
            else "Abroad pool uses curated regional hub packs (Gulf, SE Asia, East Asia, Europe, UK/Ireland, Oceania, North America, Africa)."
        )

        return {
            "schema_version": "locational_recommendation.v2",
            "goal_category": goal,
            "location_scope": scope,
            "preferred_hub_regions": preferred_hub_regions,
            "hub_regions_considered": [
                {
                    "id": key,
                    "label": HUB_REGION_LABELS.get(key, key),
                    "city_count": sum(1 for c in city_rows if c.get("hub_region") == key),
                }
                for key in (preferred_hub_regions or list(HUB_REGION_PACKS.keys()))
                if any(c.get("hub_region") == key for c in city_rows)
            ],
            "goal_houses": goal_houses,
            "goal_karakas": karakas,
            "method_notes": [
                "Direction scores use Ashta-Dikpala lords weighted by dignity, house quality, and link to goal houses/karakas.",
                "City scores use relocated D1 (same birth JD, new lat/lon): ASC quality, goal-house occupancy, lord strength, dasha-lord placement, and compass alignment to preferred directions.",
                "Candidate pool is India metros and/or region-specific global hub packs based on location_scope (and optional user-stated region like Gulf/Europe/SE Asia). Not Western ASC/MC ACG lines.",
                pool_note,
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
            "top_cities_by_hub_region": top_by_hub_region,
            "all_cities_ranked": [
                {
                    "name": c["name"],
                    "score": c["score"],
                    "compass_direction": c["compass_direction"],
                    "country": c.get("country"),
                    "region": c.get("region"),
                    "hub_region": c.get("hub_region"),
                    "hub_region_label": c.get("hub_region_label"),
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
        hub_region = str(metro.get("hub_region") or ("india" if region == "india" else "abroad"))
        hub_region_label = HUB_REGION_LABELS.get(hub_region, hub_region.replace("_", " ").title())
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
            "hub_region": hub_region,
            "hub_region_label": hub_region_label,
            "latitude": lat,
            "longitude": lon,
            "score": round(score, 2),
            "compass_direction": compass,
            "bearing_deg": round(bearing, 1),
            "relocated_ascendant": SIGN_NAMES[asc_sign],
            "relocated_asc_lord": asc_lord,
            "reasons": reasons[:6],
        }
