"""BNN Nadi Desk payload — linkage web, trikonas, age & transit activation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from fastapi import APIRouter
from calculators.nadi_linkage_calculator import NadiLinkageCalculator

router = APIRouter()

PLANET_ORDER = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
)
SIGN_LORDS = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
)
SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

# Classical BNN planet-age progression (chat [N-3])
PLANET_AGES: Tuple[Tuple[str, int], ...] = (
    ("Jupiter", 16),
    ("Sun", 22),
    ("Moon", 24),
    ("Venus", 25),
    ("Mars", 28),
    ("Mercury", 32),
    ("Saturn", 36),
    ("Rahu", 42),
    ("Ketu", 48),
)

# Nakṣatra milestone ages (chat / NadiAgent)
NADI_AGE_MAP: Dict[int, Any] = {
    16: "Rohini",
    24: "Pushya",
    30: "Swati",
    36: ["Rohini", "Pushya"],
    45: "Magha",
    46: ["Magha", "Swati"],
    65: "Pushya",
    69: "Swati",
    83: "Rohini",
}

KARAKAS = {
    "jeeva": "Jupiter",
    "karma": "Saturn",
    "kalatra": "Venus",
}

TRIKONAS = (
    {"key": "dharma", "label": "Dharma", "houses": (1, 5, 9), "phala": 9},
    {"key": "artha", "label": "Artha", "houses": (2, 6, 10), "phala": 2},
    {"key": "kama", "label": "Kama", "houses": (3, 7, 11), "phala": 7},
    {"key": "moksha", "label": "Moksha", "houses": (4, 8, 12), "phala": 12},
)

TOPIC_PRESETS = {
    "career": {"label": "Career", "karakas": ("Saturn", "Mercury", "Sun", "Mars"), "houses": (2, 6, 10)},
    "marriage": {"label": "Marriage", "karakas": ("Venus", "Moon", "Jupiter"), "houses": (3, 7, 11)},
    "wealth": {"label": "Wealth", "karakas": ("Jupiter", "Mercury", "Venus"), "houses": (2, 11)},
    "self": {"label": "Self", "karakas": ("Jupiter", "Sun", "Moon"), "houses": (1, 5, 9)},
}

SLOW_TRIGGERS = frozenset({"Jupiter", "Saturn", "Rahu", "Ketu"})


def _norm_lon(lon: Any) -> float:
    return ((float(lon) % 360.0) + 360.0) % 360.0


def _nakshatra(lon: Any) -> Tuple[str, int]:
    value = _norm_lon(lon)
    idx = int(value / 13.333333) % 27
    pada = int((value % 13.333333) / 3.333333) + 1
    return NAKSHATRAS[idx], pada


def _parse_as_of(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value or "")[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return date.today()


def _age_years(birth_iso: str, as_of: date) -> int:
    dob = datetime.strptime(str(birth_iso)[:10], "%Y-%m-%d").date()
    years = as_of.year - dob.year
    if (as_of.month, as_of.day) < (dob.month, dob.day):
        years -= 1
    return max(0, years)


def _lagna_sign(chart: Dict[str, Any]) -> int:
    houses = chart.get("houses") or []
    if houses and isinstance(houses[0], dict) and houses[0].get("sign") is not None:
        return int(houses[0]["sign"])
    asc = chart.get("ascendant")
    if isinstance(asc, (int, float)):
        return int(_norm_lon(asc) // 30) % 12
    return 0


def _planet_house(sign: int, lagna_sign: int) -> int:
    return ((int(sign) - int(lagna_sign) + 12) % 12) + 1


def _moon_context(chart: Dict[str, Any]) -> Dict[str, Any]:
    moon = (chart.get("planets") or {}).get("Moon") or {}
    lon = moon.get("longitude")
    if lon is None and moon.get("sign") is not None:
        lon = int(moon["sign"]) * 30 + float(moon.get("degree") or 0)
    nak, pada = _nakshatra(lon or 0)
    lagna = _lagna_sign(chart)
    sign = int(moon["sign"]) if moon.get("sign") is not None else int(_norm_lon(lon or 0) // 30)
    return {
        "nakshatra": nak,
        "pada": pada,
        "sign": sign,
        "sign_name": SIGN_NAMES[sign],
        "house": _planet_house(sign, lagna) if moon else None,
        "longitude": float(lon) if lon is not None else None,
    }


def _build_trikonas(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    planets = chart.get("planets") or {}
    lagna = _lagna_sign(chart)
    rows = []
    for tri in TRIKONAS:
        house_set = set(tri["houses"])
        occupants = []
        for name in PLANET_ORDER:
            data = planets.get(name)
            if not data or data.get("sign") is None:
                continue
            house = int(data["house"]) if data.get("house") is not None else _planet_house(
                int(data["sign"]), lagna
            )
            if house in house_set:
                occupants.append({
                    "planet": name,
                    "house": house,
                    "sign": int(data["sign"]),
                    "sign_name": SIGN_NAMES[int(data["sign"])],
                })
        lords = []
        for house in tri["houses"]:
            sign = (lagna + house - 1) % 12
            lord = SIGN_LORDS[sign]
            lord_data = planets.get(lord) or {}
            lord_sign = lord_data.get("sign")
            lords.append({
                "house": house,
                "lord": lord,
                "sign": sign,
                "sign_name": SIGN_NAMES[sign],
                "placed_sign": int(lord_sign) if lord_sign is not None else None,
                "placed_house": (
                    int(lord_data["house"])
                    if lord_data.get("house") is not None
                    else (
                        _planet_house(int(lord_sign), lagna)
                        if lord_sign is not None else None
                    )
                ),
            })
        rows.append({
            "key": tri["key"],
            "label": tri["label"],
            "houses": list(tri["houses"]),
            "phala_house": tri["phala"],
            "occupants": occupants,
            "lords": lords,
            "strength": (
                "strong" if len(occupants) >= 3
                else "moderate" if len(occupants) >= 1
                else "quiet"
            ),
        })
    return rows


LINK_TYPE_LABELS = {
    "trine": "Trine",
    "next": "2nd",
    "prev": "12th",
    "opposite": "7th",
}
# Ranking bias: trine yogas first among same activation state
LINK_TYPE_RANK = {"trine": 0, "opposite": 1, "next": 2, "prev": 3}

KARAKA_ROLES = (
    ("jeeva", "Jeeva", "Jupiter"),
    ("karma", "Karma", "Saturn"),
    ("kalatra", "Kalatra", "Venus"),
)


def _planet_sort_key(name: str) -> int:
    try:
        return PLANET_ORDER.index(name)
    except ValueError:
        return 99


def _link_clusters(links: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Unique BNN yogas: trine groups + 2nd / 12th / 7th pairs."""
    clusters: List[Dict[str, Any]] = []
    seen_trine: Set[frozenset] = set()
    seen_pairs: Set[Tuple[str, frozenset]] = set()

    for planet, row in links.items():
        conns = row.get("connections") or {}

        # Trine — keep full co-trine group (size ≥ 2)
        trine_members = set(conns.get("trine") or [])
        trine_members.add(planet)
        if len(trine_members) >= 2:
            key = frozenset(trine_members)
            if key not in seen_trine:
                seen_trine.add(key)
                ordered = tuple(sorted(trine_members, key=_planet_sort_key))
                clusters.append({
                    "id": f"trine:{'-'.join(ordered)}",
                    "planets": list(ordered),
                    "link_type": "trine",
                    "link_label": LINK_TYPE_LABELS["trine"],
                    "size": len(ordered),
                })

        # Directional / opposition — undirected pairs
        for link_type in ("next", "prev", "opposite"):
            for other in conns.get(link_type) or []:
                if not other or other == planet:
                    continue
                pair = frozenset((planet, other))
                pair_key = (link_type, pair)
                if pair_key in seen_pairs:
                    continue
                # next(A,B) and prev(B,A) describe the same 2nd↔12th axis;
                # keep both labels as distinct yogas (future vs past).
                seen_pairs.add(pair_key)
                ordered = tuple(sorted(pair, key=_planet_sort_key))
                clusters.append({
                    "id": f"{link_type}:{'-'.join(ordered)}",
                    "planets": list(ordered),
                    "link_type": link_type,
                    "link_label": LINK_TYPE_LABELS[link_type],
                    "size": 2,
                })

    clusters.sort(key=lambda row: (
        LINK_TYPE_RANK.get(row["link_type"], 9),
        -row["size"],
        row["id"],
    ))
    return clusters


def _theme_for_cluster(planets: Sequence[str], link_type: str = "trine") -> List[str]:
    themes: List[str] = []
    set_p = set(planets)
    if link_type == "next":
        themes.append("2nd-house direction — growth / next chapter")
    elif link_type == "prev":
        themes.append("12th-house direction — past / expenditure / retreat")
    elif link_type == "opposite":
        themes.append("7th opposition — other / partnership axis")

    if "Saturn" in set_p and "Mercury" in set_p:
        themes.append("analytical / commercial work")
    if "Saturn" in set_p and "Mars" in set_p:
        themes.append("technical / execution")
    if "Saturn" in set_p and "Jupiter" in set_p:
        themes.append("advisory / teaching")
    if "Saturn" in set_p and "Rahu" in set_p:
        themes.append("technology / foreign scale")
    if "Saturn" in set_p and "Ketu" in set_p:
        themes.append("research / specialist")
    if "Venus" in set_p and "Moon" in set_p:
        themes.append("affection / bonding")
    if "Venus" in set_p and "Jupiter" in set_p:
        themes.append("supportive alliance")
    if "Venus" in set_p and "Saturn" in set_p:
        themes.append("dutiful / delayed bond")
    if "Venus" in set_p and "Rahu" in set_p:
        themes.append("unconventional attraction")
    if "Venus" in set_p and "Ketu" in set_p:
        themes.append("detached / non-ordinary bond")
    if len(themes) <= 1:
        if "Saturn" in set_p:
            themes.append("karma / profession field")
        if "Venus" in set_p:
            themes.append("relationship field")
        if "Jupiter" in set_p:
            themes.append("jeeva / growth field")
    return themes or ["graha blend"]


def _karaka_readout(chart: Dict[str, Any], links: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Jeeva / Karma / Kalatra placement + who links to each karaka."""
    planets = chart.get("planets") or {}
    lagna = _lagna_sign(chart)
    rows: List[Dict[str, Any]] = []
    for role, label, planet in KARAKA_ROLES:
        data = planets.get(planet) or {}
        link = links.get(planet) or {}
        conns = link.get("connections") or {}
        sign_info = link.get("sign_info") or {}
        sign = data.get("sign")
        lon = data.get("longitude")
        if lon is None and sign is not None:
            lon = int(sign) * 30 + float(data.get("degree") or 0)
        nak, pada = _nakshatra(lon or 0) if lon is not None or sign is not None else ("", 0)
        house = None
        if data.get("house") is not None:
            house = int(data["house"])
        elif sign is not None:
            house = _planet_house(int(sign), lagna)
        rows.append({
            "role": role,
            "label": label,
            "planet": planet,
            "house": house,
            "sign": int(sign) if sign is not None else None,
            "sign_name": SIGN_NAMES[int(sign)] if sign is not None else None,
            "nakshatra": nak or None,
            "pada": pada or None,
            "longitude": float(lon) if lon is not None else None,
            "is_retro": bool(sign_info.get("is_retro") or data.get("retrograde")),
            "is_exchange": bool(sign_info.get("is_exchange")),
            "links": {
                "trine": list(conns.get("trine") or []),
                "next": list(conns.get("next") or []),
                "prev": list(conns.get("prev") or []),
                "opposite": list(conns.get("opposite") or []),
            },
            "all_links": list(link.get("all_links") or []),
        })
    return rows


def _planet_age_timeline(age: int) -> List[Dict[str, Any]]:
    rows = []
    for planet, milestone in PLANET_AGES:
        if age < milestone:
            status = "upcoming"
        elif age == milestone:
            status = "current"
        else:
            status = "past"
        rows.append({"planet": planet, "age": milestone, "status": status})
    return rows


def _nakshatra_milestones(
    age: int,
    chart: Dict[str, Any],
) -> List[Dict[str, Any]]:
    planets = chart.get("planets") or {}
    lagna = _lagna_sign(chart)
    rows = []
    for milestone, stars in sorted(NADI_AGE_MAP.items()):
        star_list = stars if isinstance(stars, list) else [stars]
        hit_planets = []
        for name in PLANET_ORDER:
            data = planets.get(name)
            if not data:
                continue
            lon = data.get("longitude")
            if lon is None and data.get("sign") is not None:
                lon = int(data["sign"]) * 30 + float(data.get("degree") or 0)
            nak, _ = _nakshatra(lon or 0)
            if nak in star_list:
                house = int(data["house"]) if data.get("house") is not None else (
                    _planet_house(int(data["sign"]), lagna) if data.get("sign") is not None else None
                )
                hit_planets.append({"planet": name, "nakshatra": nak, "house": house})
        if age < milestone:
            status = "upcoming"
        elif age == milestone:
            status = "current"
        else:
            status = "past"
        rows.append({
            "age": milestone,
            "nakshatras": star_list,
            "planets": hit_planets,
            "status": status,
        })
    return rows


def _sign_trine_mates(sign: int) -> Set[int]:
    return {sign % 12, (sign + 4) % 12, (sign + 8) % 12}


def _transit_hits(
    chart: Dict[str, Any],
    transit_planets: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not transit_planets:
        return []
    natal = chart.get("planets") or {}
    hits: List[Dict[str, Any]] = []
    for t_name in SLOW_TRIGGERS:
        t_data = transit_planets.get(t_name)
        if not t_data or t_data.get("sign") is None:
            continue
        t_sign = int(t_data["sign"])
        t_trines = _sign_trine_mates(t_sign)
        for n_name in PLANET_ORDER:
            n_data = natal.get(n_name)
            if not n_data or n_data.get("sign") is None:
                continue
            n_sign = int(n_data["sign"])
            if n_sign == t_sign:
                relation = "conjunction"
            elif n_sign in t_trines:
                relation = "trine"
            else:
                continue
            hits.append({
                "transit_planet": t_name,
                "natal_planet": n_name,
                "relation": relation,
                "transit_sign": t_sign,
                "natal_sign": n_sign,
            })
    return hits


def _activations(
    clusters: Sequence[Dict[str, Any]],
    age: int,
    planet_ages: Sequence[Dict[str, Any]],
    milestones: Sequence[Dict[str, Any]],
    transit_hits: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    current_age_planets = {
        row["planet"] for row in planet_ages if row["status"] == "current"
    }
    milestone_planets = set()
    for row in milestones:
        if row["status"] == "current":
            for item in row["planets"]:
                milestone_planets.add(item["planet"])
    transit_by_natal: Dict[str, List[Dict[str, Any]]] = {}
    for hit in transit_hits:
        transit_by_natal.setdefault(hit["natal_planet"], []).append(hit)

    rows = []
    for cluster in clusters:
        planets = list(cluster["planets"])
        reasons: List[str] = []
        for planet in planets:
            if planet in current_age_planets:
                reasons.append(f"{planet} planet-age")
            if planet in milestone_planets:
                reasons.append(f"{planet} nakṣatra milestone")
            for hit in transit_by_natal.get(planet, []):
                reasons.append(
                    f"{hit['transit_planet']} transit {hit['relation']} {planet}"
                )
        if reasons:
            state = "strong" if len(reasons) >= 2 else "active"
        else:
            state = "promise"
        link_type = cluster.get("link_type") or "trine"
        rows.append({
            "id": cluster["id"],
            "planets": planets,
            "link_type": link_type,
            "link_label": cluster.get("link_label") or LINK_TYPE_LABELS.get(link_type, link_type),
            "themes": _theme_for_cluster(planets, link_type),
            "state": state,
            "reasons": reasons[:6],
        })
    rank = {"strong": 0, "active": 1, "promise": 2}
    rows.sort(key=lambda row: (
        rank.get(row["state"], 9),
        LINK_TYPE_RANK.get(row["link_type"], 9),
        -len(row["planets"]),
        row["id"],
    ))
    return rows


def build_nadi_desk(
    *,
    chart_data: Dict[str, Any],
    birth_data: Dict[str, Any],
    as_of: Any = None,
    transit_planets: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    as_of_day = _parse_as_of(as_of)
    birth_date = str((birth_data or {}).get("date") or "")[:10]
    age = _age_years(birth_date, as_of_day) if birth_date else 0

    links = NadiLinkageCalculator(chart_data).get_nadi_links()
    clusters = _link_clusters(links)
    planet_ages = _planet_age_timeline(age)
    milestones = _nakshatra_milestones(age, chart_data)
    transit_hits = _transit_hits(chart_data, transit_planets)
    activations = _activations(clusters, age, planet_ages, milestones, transit_hits)
    karaka_readout = _karaka_readout(chart_data, links)

    return {
        "schema": "nadi_desk.v2",
        "system": "bhrigu_nandi_nadi",
        "as_of": as_of_day.isoformat(),
        "age": age,
        "moon": _moon_context(chart_data),
        "karakas": KARAKAS,
        "karaka_readout": karaka_readout,
        "links": links,
        "clusters": clusters,
        "trikonas": _build_trikonas(chart_data),
        "planet_ages": planet_ages,
        "nakshatra_milestones": milestones,
        "transit_hits": transit_hits,
        "activations": activations,
        "topic_presets": TOPIC_PRESETS,
        "link_type_labels": LINK_TYPE_LABELS,
    }


@router.post("/nadi-desk")
async def get_nadi_desk(request: Dict[str, Any]):
    chart = request.get("chart_data") or {}
    birth = request.get("birth_data") or {}
    if not chart.get("planets"):
        return {"success": False, "error": "chart_data.planets required"}
    payload = build_nadi_desk(
        chart_data=chart,
        birth_data=birth,
        as_of=request.get("as_of"),
        transit_planets=request.get("transit_planets"),
    )
    return {"success": True, **payload}
