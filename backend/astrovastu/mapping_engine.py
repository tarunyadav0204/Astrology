"""
AstroVastu deterministic mapping v2 — sign-based directions (fixed compass).

Each planet is placed in a compass sector from the **sign it occupies** (sidereal whole-sign),
using a fixed cycle: Aries→East, Taurus→SE, … stepping clockwise through eight directions,
repeating every eight signs. The **main door** does not rotate the zodiac; it is only used
for zone tags and entrance context.

Document mapping_version when rules change; see docs/ASTROVASTU_PRODUCT_SPEC.md.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

MAPPING_VERSION = "v4_spiritual_area_scores"

DIRS: List[str] = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
DIR_INDEX: Dict[str, int] = {d: i for i, d in enumerate(DIRS)}

SIGN_NAMES: List[str] = [
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

# Vedic sign lords (0=Aries … 11=Pisces)
SIGN_LORD: List[str] = [
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

GRAHAS: Set[str] = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
)

# Whole-sign house meanings for AI/UI (goal-neutral). Keeps sector copy tied to actual houses.
_HOUSE_NEUTRAL_THEME: Dict[int, str] = {
    1: "Self, body, outlook",
    2: "Wealth, speech, food, close family",
    3: "Siblings, courage, skills, short trips",
    4: "Home, mother, emotional base",
    5: "Children, intellect, creativity",
    6: "Health, habits, service, obstacles",
    7: "Partnership, marriage, contracts",
    8: "Shared assets, change, longevity stress",
    9: "Dharma, fortune, higher learning",
    10: "Career, status, public life",
    11: "Gains, friends, aspirations",
    12: "Solitude, expenses, liberation themes",
}


def _house_life_themes_blurb(mapped_houses: List[int], occupied_houses: List[int]) -> Dict[str, List[str]]:
    """Deterministic hints so narratives match houses in each compass sector."""

    def line(hn: int) -> str:
        t = _HOUSE_NEUTRAL_THEME.get(int(hn), "General life themes")
        return f"H{int(hn)}: {t}"

    return {
        "mapped_houses_with_themes": [line(hn) for hn in sorted({int(h) for h in mapped_houses})],
        "houses_with_planets_themes": [line(hn) for hn in sorted({int(h) for h in occupied_houses})],
    }

_GOAL_HOUSE_BOOST: Dict[str, Dict[int, float]] = {
    "wealth": {2: 1.4, 11: 1.4, 9: 1.15, 5: 1.1},
    "career": {10: 1.45, 6: 1.2, 2: 1.15},
    "relationship": {7: 1.45, 5: 1.2, 2: 1.1},
    "health": {1: 1.35, 6: 1.25, 8: 1.15},
    "focus": {5: 1.35, 1: 1.15, 3: 1.1},
    "spiritual": {9: 1.4, 4: 1.25, 12: 1.1, 5: 1.05},
    "everything_feels_stuck": {},
    "complete_all": {},
    "stuck": {},
}

_TAG_BASE_WEIGHT: Dict[str, float] = {
    "toilet": -6,
    "toilet_bath": -6,
    "storage": -1.5,
    "store_clutter": -2.2,
    "clutter": -2,
    "kitchen": -1,
    "kitchen_fire": -1,
    "bed": 0,
    "master_bedroom": 0.3,
    "kids_room": 0.2,
    "living_room": 0.6,
    "study_room": 0.7,
    "garden_plants": 1.2,
    "temple_prayer": 2.2,
    "water_body": 0.8,
    "balcony_open": 0.5,
    "main_door": 1,
    "desk": 0,
    "empty": 0.5,
    "other": -0.5,
}

# Direction-aware placement calibration (Vastu-inspired, non-absolute):
# score > 0 => generally supportive/acceptable for that direction
# score = 0 => neutral
# score < 0 => challenging for that direction
_TAG_DIRECTION_WEIGHT: Dict[str, Dict[str, float]] = {
    "toilet_bath": {
        "N": -2.5, "NE": -4.5, "E": -2.0, "SE": -1.0,
        "S": -0.5, "SW": -2.5, "W": -1.0, "NW": 0.0,
    },
    "store_clutter": {
        "N": -1.5, "NE": -2.0, "E": -1.2, "SE": -0.5,
        "S": 0.0, "SW": 0.8, "W": 0.4, "NW": 0.2,
    },
    "kitchen_fire": {
        "N": -0.7, "NE": -3.5, "E": 0.6, "SE": 2.2,
        "S": 0.6, "SW": -0.8, "W": -0.4, "NW": -0.8,
    },
    "master_bedroom": {
        "N": 0.0, "NE": -0.8, "E": -0.2, "SE": -0.8,
        "S": 0.6, "SW": 2.0, "W": 0.8, "NW": -0.7,
    },
    "kids_room": {
        "N": 0.8, "NE": 1.2, "E": 0.9, "SE": -0.4,
        "S": -0.2, "SW": -0.6, "W": 0.2, "NW": 0.6,
    },
    "living_room": {
        "N": 0.7, "NE": 1.0, "E": 1.0, "SE": 0.1,
        "S": 0.0, "SW": -0.2, "W": 0.4, "NW": 0.8,
    },
    "study_room": {
        "N": 1.1, "NE": 1.5, "E": 1.0, "SE": -0.3,
        "S": -0.4, "SW": -0.6, "W": 0.2, "NW": 0.9,
    },
    "temple_prayer": {
        "N": 1.6, "NE": 2.4, "E": 1.7, "SE": -1.5,
        "S": -1.0, "SW": -1.7, "W": -0.4, "NW": 0.2,
    },
    "garden_plants": {
        "N": 1.0, "NE": 1.4, "E": 1.1, "SE": 0.2,
        "S": 0.4, "SW": 0.4, "W": 0.6, "NW": 0.8,
    },
    "water_body": {
        "N": 1.2, "NE": 1.8, "E": 1.0, "SE": -0.7,
        "S": -0.8, "SW": -1.2, "W": 0.2, "NW": 0.4,
    },
    "balcony_open": {
        "N": 0.6, "NE": 1.0, "E": 0.9, "SE": 0.3,
        "S": 0.2, "SW": -0.2, "W": 0.4, "NW": 0.5,
    },
}

# Human copy: how each goal weights houses (for on-screen explanations)
_GOAL_COPY: Dict[str, Dict[str, str]] = {
    "wealth": {
        "label": "Wealth / stability",
        "scoring": "We emphasise houses 2 (income, voice), 11 (gains), 9 (fortune), and 5 (speculation) when scoring — planets there matter more for this focus.",
    },
    "career": {
        "label": "Career / reputation",
        "scoring": "We emphasise houses 10 (career, status), 6 (work, obstacles), and 2 (resources) when scoring — planets there matter more for this focus.",
    },
    "relationship": {
        "label": "Relationship / family",
        "scoring": "We emphasise houses 7 (partnership), 5 (children, romance), and 2 (family resources) when scoring.",
    },
    "health": {
        "label": "Health / rest",
        "scoring": "We emphasise houses 1 (body), 6 (illness, habits), and 8 (chronic stress) when scoring.",
    },
    "focus": {
        "label": "Focus / mental noise",
        "scoring": "We emphasise houses 5 (intellect), 1 (self), and 3 (courage, efforts) when scoring.",
    },
    "everything_feels_stuck": {
        "label": "Everything feels stuck",
        "scoring": "No extra house weights — all twelve houses contribute equally to the base planetary mix.",
    },
    "complete_all": {
        "label": "Complete life analysis",
        "scoring": "No single-theme weighting is forced. The engine evaluates all major life areas from the same chart-direction map, then ranks sectors by combined chart, dasha, and home-tag pressure.",
    },
    "stuck": {
        "label": "General",
        "scoring": "No extra house weights — all twelve houses contribute equally to the base planetary mix.",
    },
}

# Optional one-line classical-topic hint per (goal, house) for explanations
_HOUSE_GOAL_HINT: Dict[str, Dict[int, str]] = {
    "career": {
        10: "House 10 is the career / name / vocation house — extra weight for this goal.",
        6: "House 6 is daily work, service, rivals — extra weight for this goal.",
        2: "House 2 is resources and voice — moderate extra weight for career stability.",
    },
    "wealth": {
        2: "House 2 is wealth and sustenance — extra weight.",
        11: "House 11 is gains and fulfilment — extra weight.",
        9: "House 9 is fortune and dharma — moderate boost.",
        5: "House 5 is speculation and intellect — mild boost.",
    },
    "relationship": {
        7: "House 7 is partnership — extra weight.",
        5: "House 5 is children and romance — extra weight.",
        2: "House 2 is family resources — moderate boost.",
    },
    "health": {
        1: "House 1 is the physical self — extra weight.",
        6: "House 6 is disease and habits — extra weight.",
        8: "House 8 is longevity and stress — moderate boost.",
    },
    "focus": {
        5: "House 5 is intellect and focus — extra weight.",
        1: "House 1 is identity — moderate boost.",
        3: "House 3 is courage and communication — moderate boost.",
    },
}


def sign_cycle_blurb() -> str:
    """Single reusable sentence for sign→direction rule."""
    seq = ", ".join(f"{SIGN_NAMES[i]}→{sign_to_direction(i)}" for i in range(8))
    return (
        f"Signs map to winds in a fixed cycle (door does not rotate this): "
        f"{seq}; the same pattern repeats for signs 8–11."
    )


def _house_goal_hint(goal: str, house: int) -> str:
    return _HOUSE_GOAL_HINT.get(goal, {}).get(int(house), "")


def _planet_breakdown_entry(
    goal_n: str,
    pname: str,
    sign_idx: int,
    hn: int,
    direction: str,
    temperament: str,
    w_raw: float,
    gm: float,
    dasha_mult: float = 1.0,
) -> Dict[str, Any]:
    sign_name = SIGN_NAMES[sign_idx]
    mapped = sign_to_direction(sign_idx)
    cycle_bit = (
        f"{sign_name} → {mapped} because Aries is fixed at East, then each sign steps clockwise "
        f"(Taurus→SE … Virgo→NW …); your planet simply inherits the wind for the sign it occupies."
    )
    hint = _house_goal_hint(goal_n, hn)
    goal_part = hint if hint else f"House {hn} uses the normal weight (×{gm:.2f}) for this goal."
    return {
        "planet": pname,
        "sign": sign_name,
        "sign_index": sign_idx,
        "house": hn,
        "direction": direction,
        "temperament": temperament,
        "maps_explanation": cycle_bit,
        "goal_relevance": goal_part,
        "score_multiplier": round(gm, 3),
        "dasha_multiplier": round(dasha_mult, 3),
        "weight_contribution": round(w_raw, 3),
    }


def normalize_door_facing(raw: str) -> str:
    if not raw or not str(raw).strip():
        return "E"
    s = str(raw).strip().upper().replace(" ", "")
    aliases = {
        "NORTH": "N",
        "NORTHEAST": "NE",
        "EAST": "E",
        "SOUTHEAST": "SE",
        "SOUTH": "S",
        "SOUTHWEST": "SW",
        "WEST": "W",
        "NORTHWEST": "NW",
    }
    if s in DIR_INDEX:
        return s
    if s in aliases:
        return aliases[s]
    return "E"


def normalize_goal(raw: str) -> str:
    if not raw:
        return "stuck"
    g = str(raw).strip().lower().replace(" ", "_").replace("-", "_")
    if g in (
        "wealth",
        "career",
        "relationship",
        "health",
        "focus",
        "everything_feels_stuck",
        "complete_all",
        "stuck",
    ):
        return g
    if "wealth" in g or "money" in g or "stability" in g:
        return "wealth"
    if "career" in g or "reputation" in g or "work" in g:
        return "career"
    if "relationship" in g or "family" in g or "marriage" in g or "love" in g:
        return "relationship"
    if "health" in g or "rest" in g or "sleep" in g:
        return "health"
    if "focus" in g or "mental" in g or "stress" in g:
        return "focus"
    if "stuck" in g or "everything" in g:
        return "everything_feels_stuck"
    if "complete" in g or "all" in g or "full" in g:
        return "complete_all"
    return "stuck"


def _normalize_tag_name(tag: str) -> str:
    t = (tag or "").strip().lower().replace(" ", "_")
    aliases = {
        "toilet": "toilet_bath",
        "bathroom": "toilet_bath",
        "kitchen": "kitchen_fire",
        "storage": "store_clutter",
        "clutter": "store_clutter",
    }
    return aliases.get(t, t)


def sign_index_from_planet(pdata: Dict[str, Any]) -> Optional[int]:
    """Sidereal sign index 0–11 from planet payload."""
    if pdata.get("sign") is not None:
        try:
            s = int(pdata["sign"])
            if 0 <= s <= 11:
                return s
        except (TypeError, ValueError):
            pass
    lon = pdata.get("longitude")
    if lon is None:
        return None
    try:
        return int(float(lon) / 30.0) % 12
    except (TypeError, ValueError):
        return None


def sign_to_direction(sign_idx: int) -> str:
    """
    Map rāśi (0=Aries … 11=Pisces) to one of eight compass directions.

    Rule: step clockwise through directions starting **East** for Aries — E, SE, S, SW, W, NW, N, NE,
    then repeat for the next signs. Indices align with DIRS order N,NE,E,SE,S,SW,W,NW via (sign+2)%8.
    """
    s = int(sign_idx) % 12
    return DIRS[(s + 2) % 8]


def _planet_weight(name: str) -> float:
    if name in ("Jupiter", "Venus"):
        return 1.3
    if name == "Mercury":
        return 0.9
    if name == "Moon":
        return 0.7
    if name == "Sun":
        return 0.6
    if name in ("Mars", "Saturn", "Rahu", "Ketu"):
        return -1.1
    return 0.0


def _planet_temperament(name: str) -> str:
    if name in ("Jupiter", "Venus"):
        return "benefic"
    if name in ("Mars", "Saturn", "Rahu", "Ketu"):
        return "malefic"
    if name in ("Sun", "Moon", "Mercury"):
        return "mixed / luminaries & Mercury"
    return "neutral"


def _goal_multiplier(goal: str, house: int) -> float:
    boosts = _GOAL_HOUSE_BOOST.get(goal, _GOAL_HOUSE_BOOST["stuck"])
    return float(boosts.get(house, 1.0))


def _normalize_zone_tags(raw: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    if not raw:
        return {}
    out: Dict[str, List[str]] = {}
    for k, v in raw.items():
        key = str(k).strip().upper()
        if key not in DIR_INDEX and key in ("NORTH", "NORTHEAST", "SOUTHEAST", "SOUTHWEST", "NORTHWEST"):
            key = normalize_door_facing(key)
        if key not in DIR_INDEX:
            continue
        if isinstance(v, str):
            out[key] = [_normalize_tag_name(v)]
        elif isinstance(v, list):
            out[key] = [_normalize_tag_name(str(x)) for x in v if x]
        else:
            out[key] = []
    return out


def _tag_penalty(direction: str, tags: List[str]) -> Tuple[float, List[str]]:
    if not tags:
        return 0.0, []
    reasons: List[str] = []
    p = 0.0
    for t in tags:
        t_low = _normalize_tag_name(t)
        default_base = _TAG_BASE_WEIGHT.get(t_low, _TAG_BASE_WEIGHT["other"])
        base = _TAG_DIRECTION_WEIGHT.get(t_low, {}).get(direction, default_base)
        extra_note = ""
        if base >= 0.75:
            extra_note = " (placement is generally acceptable/supportive in this direction)"
        elif base <= -1.25:
            extra_note = " (placement is traditionally more challenging in this direction)"
        else:
            extra_note = " (placement is mixed/neutral; depends on overall chart and upkeep)"
        p += base
        label = t_low.replace("_", " ")
        if base >= 0:
            reasons.append(f"Room tag “{label}” in {direction}: contributes support to this sector.{extra_note}")
        else:
            reasons.append(f"Room tag “{label}” in {direction}: adds some pressure to this sector.{extra_note}")
    return p, reasons


def _remedy_hints(direction: str, tags: List[str], planets: List[str]) -> List[str]:
    hints: List[str] = []
    tags_l = {t.lower() for t in tags}
    if "toilet_bath" in tags_l:
        hints.append(
            f"Keep the {direction} zone clean, dry, and well-lit; close doors; add earthy or metallic accents where practical (non-destructive first)."
        )
    if "kitchen_fire" in tags_l and direction == "NE":
        hints.append(
            "Reduce fire element load in NE if possible: lighter cooking times; store harsh metals elsewhere."
        )
    if "store_clutter" in tags_l or "clutter" in tags_l:
        hints.append(
            f"Declutter the {direction} sector — open space allows the planetary mix here to register more clearly."
        )
    if "temple_prayer" in tags_l:
        hints.append(f"Keep the prayer/temple area in {direction} sattvic and uncluttered; avoid heavy storage around it.")
    if "garden_plants" in tags_l:
        hints.append(f"Maintain live, healthy plants in {direction}; remove dry/decaying foliage quickly.")
    if not hints:
        if any(p in planets for p in ("Saturn", "Rahu", "Ketu")):
            hints.append(
                f"The {direction} zone carries weighty energies in your chart — prefer calm colors (blues/greys), avoid chaos, and keep the area structured."
            )
        if any(p in planets for p in ("Jupiter", "Venus")):
            hints.append(
                f"Benefic emphasis in {direction} — keep it pleasant, fragrant, and dignified to amplify support."
            )
    if not hints:
        hints.append(
            f"Audit the {direction} sector weekly: remove broken items, ensure good light, and keep use aligned with that zone’s chart mix."
        )
    return hints[:5]


def _priority_label(total: float) -> str:
    if total <= -4:
        return "Needs attention first"
    if total <= -1:
        return "Worth balancing"
    if total <= 1:
        return "Moderate"
    return "Relatively supportive"


def _build_methodology(goal_n: str) -> Dict[str, Any]:
    cycle = ", ".join(f"{SIGN_NAMES[i]}→{sign_to_direction(i)}" for i in range(8))
    gc = _GOAL_COPY.get(goal_n, _GOAL_COPY["stuck"])
    return {
        "title": "Sign-based directions (fixed compass)",
        "summary": (
            "Planets are mapped by the sidereal sign they occupy — not by rotating the chart from your door. "
            "Each sign corresponds to one compass sector in a repeating eight-step cycle starting from East for Aries, "
            "moving clockwise through the eight directions."
        ),
        "sign_cycle_first_eight": cycle,
        "sign_cycle_rule": sign_cycle_blurb(),
        "goal_label": gc["label"],
        "goal_scoring": gc["scoring"],
        "door_note": (
            "Your main door direction is used for room tags and context only; it does not move houses or signs around the compass."
        ),
        "scoring_note": (
            "The index mixes planet nature, goal-weighted houses, and room-tag penalties. "
            "Lower totals flag sectors to address first — read the chart and tag reasons below, not only the number."
        ),
    }


def _build_hero_summary(
    goal_n: str,
    hero_dir: str,
    hero_score: float,
    door: str,
    has_chart_grahas: bool,
    has_tag_reasons: bool,
    first_chart_line: Optional[str],
    first_tag_line: Optional[str],
) -> str:
    gc = _GOAL_COPY.get(goal_n, _GOAL_COPY["stuck"])
    g = gc["label"]
    parts: List[str] = [
        f"For your focus ({g}), {hero_dir} is the sector to work on first. {gc['scoring']} "
    ]
    if has_chart_grahas and has_tag_reasons:
        parts.append(
            f"Chart and space both weigh on {hero_dir}: planets sit in signs that map here, and your tags add pressure. "
        )
    elif has_chart_grahas:
        parts.append(
            f"Here, planets occupy signs that map to {hero_dir} — that is why this wind matters for your chart for this goal. "
        )
    elif has_tag_reasons:
        parts.append(
            f"No planet occupies a sign that maps to {hero_dir}; this direction still ranks first because of your room tags there "
            f"(see below). Chart and door do not move the sign→wind rule. "
        )
    else:
        parts.append(f"This direction has the lowest combined index in your run. ")

    parts.append(f"Main entrance faces {door} — used for tagging only, not to rotate signs. ")
    if first_chart_line:
        parts.append(first_chart_line.strip() + " ")
    if first_tag_line:
        parts.append(first_tag_line.strip() + " ")
    if hero_score < -4:
        parts.append(
            "Several factors stack here — small, steady fixes in this wind often register before larger moves elsewhere."
        )
    return "".join(parts).strip()


def build_energy_map(
    chart_data: Dict[str, Any],
    door_facing: str,
    zone_tags: Optional[Dict[str, Any]],
    goal: str,
    dasha_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    door = normalize_door_facing(door_facing)
    goal_n = normalize_goal(goal)
    tags_by_dir = _normalize_zone_tags(zone_tags)

    houses: List[Dict[str, Any]] = chart_data.get("houses") or []
    if len(houses) < 12:
        raise ValueError("chart_data must include 12 whole-sign houses")

    planets: Dict[str, Any] = chart_data.get("planets") or {}
    mapped_signs_by_dir: Dict[str, List[str]] = {d: [] for d in DIRS}
    for i, sname in enumerate(SIGN_NAMES):
        mapped_signs_by_dir[sign_to_direction(i)].append(sname)
    mapped_houses_by_dir: Dict[str, List[int]] = {d: [] for d in DIRS}
    for hn in range(1, 13):
        sig = houses[hn - 1].get("sign")
        if sig is None:
            continue
        try:
            d = sign_to_direction(int(sig))
            mapped_houses_by_dir[d].append(hn)
        except (TypeError, ValueError):
            continue

    per_dir: Dict[str, Dict[str, Any]] = {
        d: {
            "planets": [],
            "planet_details": [],
            "house_numbers": set(),
            "signs_seen": set(),
            "raw_score": 0.0,
            "why_lines": [],
        }
        for d in DIRS
    }

    for pname, pdata in planets.items():
        if pname not in GRAHAS or not isinstance(pdata, dict):
            continue
        sign_idx = sign_index_from_planet(pdata)
        if sign_idx is None:
            continue
        h = pdata.get("house")
        if h is None:
            continue
        try:
            hn = int(h)
        except (TypeError, ValueError):
            continue
        if hn < 1 or hn > 12:
            continue

        direction = sign_to_direction(sign_idx)
        sign_name = SIGN_NAMES[sign_idx]
        gm = _goal_multiplier(goal_n, hn)
        dasha_mult = 1.0
        md = str((dasha_context or {}).get("mahadasha", {}).get("planet") or "")
        ad = str((dasha_context or {}).get("antardasha", {}).get("planet") or "")
        if pname and pname == md:
            dasha_mult *= 1.25
        if pname and pname == ad:
            dasha_mult *= 1.12
        w_raw = _planet_weight(pname) * gm * dasha_mult
        temperament = _planet_temperament(pname)
        hint = _house_goal_hint(goal_n, hn)
        if hint:
            goal_sentence = f"{hint} Applied multiplier ×{gm:.2f}."
        elif gm > 1.01:
            goal_sentence = f"This house gets extra weight for your focus (×{gm:.2f})."
        else:
            goal_sentence = f"Standard house weight for your focus (×{gm:.2f})."
        dasha_sentence = f" Active dasha emphasis applies (×{dasha_mult:.2f})." if dasha_mult > 1.0 else ""

        line = (
            f"{pname} in {sign_name}, whole-sign house {hn} → compass sector {direction}. "
            f"{sign_name} maps to {direction} in the fixed eight-wind cycle (Aries→East, stepping clockwise; not from door). "
            f"{temperament.capitalize()} baseline. {goal_sentence}{dasha_sentence}"
        )

        per_dir[direction]["planets"].append(pname)
        per_dir[direction]["house_numbers"].add(hn)
        per_dir[direction]["signs_seen"].add(sign_name)
        per_dir[direction]["raw_score"] += w_raw
        per_dir[direction]["why_lines"].append(line)
        per_dir[direction]["planet_details"].append(
            _planet_breakdown_entry(goal_n, pname, sign_idx, hn, direction, temperament, w_raw, gm, dasha_mult)
        )

    directions_out: Dict[str, Any] = {}
    for d in DIRS:
        hs: Set[int] = per_dir[d]["house_numbers"]
        house_lords: List[str] = []
        for hn in sorted(hs):
            sig = houses[hn - 1].get("sign")
            if sig is not None and 0 <= int(sig) <= 11:
                house_lords.append(SIGN_LORD[int(sig)])

        tag_list = tags_by_dir.get(d, [])
        tag_adj, tag_reasons = _tag_penalty(d, tag_list)
        raw = float(per_dir[d]["raw_score"])
        total = raw + tag_adj

        why_chart: List[str] = list(per_dir[d]["why_lines"])
        if not why_chart:
            why_chart.append(
                f"No natal planets occupy signs that map to {d}. Nothing from the chart places grahas in this wind by our sign→direction rule."
            )

        why_tag: List[str] = list(tag_reasons)
        why_all: List[str] = why_chart + why_tag

        directions_out[d] = {
            "planets": sorted(per_dir[d]["planets"]),
            "planet_details": per_dir[d]["planet_details"],
            "mapped_signs": mapped_signs_by_dir[d],
            "mapped_house_numbers": mapped_houses_by_dir[d],
            "house_numbers": sorted(hs),
            "house_life_themes": _house_life_themes_blurb(mapped_houses_by_dir[d], list(hs)),
            "signs": sorted(per_dir[d]["signs_seen"]),
            "house_lords": list(dict.fromkeys(house_lords)),
            "raw_score": round(raw, 2),
            "tag_penalty": round(tag_adj, 2),
            "total_score": round(total, 2),
            "priority_label": _priority_label(total),
            "why_chart_lines": why_chart[:12],
            "why_tag_lines": why_tag,
            "why_lines": why_all[:14],
            "tags": tag_list,
        }

    ranked: List[Dict[str, Any]] = []
    for d in DIRS:
        row = {k: v for k, v in directions_out[d].items() if k != "tags"}
        row["direction"] = d
        ranked.append(row)
    ranked.sort(key=lambda x: float(x.get("total_score") or 0))

    hero = ranked[0] if ranked else None
    hero_dir = hero["direction"] if hero else "E"
    hero_tags = tags_by_dir.get(hero_dir, [])
    hero_block = directions_out.get(hero_dir) or {}
    hero_planets = hero_block.get("planets") or []
    why_chart = list(hero_block.get("why_chart_lines") or [])
    why_tag = list(hero_block.get("why_tag_lines") or [])
    hero_why_full = why_chart + why_tag
    has_chart_grahas = len(hero_planets) > 0
    has_tag_reasons = len(why_tag) > 0
    first_chart = why_chart[0] if why_chart else None
    first_tag = why_tag[0] if why_tag else None

    narrative = _build_hero_summary(
        goal_n,
        hero_dir,
        float(hero["total_score"]) if hero else 0.0,
        door,
        has_chart_grahas,
        has_tag_reasons,
        first_chart,
        first_tag,
    )
    remedies = _remedy_hints(hero_dir, hero_tags, hero_planets)

    methodology = _build_methodology(goal_n)
    gc = _GOAL_COPY.get(goal_n, _GOAL_COPY["stuck"])
    areas = ["career", "wealth", "relationship", "health", "focus", "spiritual"]
    area_scores: Dict[str, Any] = {}
    for area in areas:
        rows: List[Dict[str, Any]] = []
        for d in DIRS:
            hsum = 0.0
            tag_pen = float(directions_out[d]["tag_penalty"])
            for p in directions_out[d]["planet_details"]:
                p_name = str(p.get("planet") or "")
                house_n = int(p.get("house") or 1)
                dm = float(p.get("dasha_multiplier") or 1.0)
                hsum += _planet_weight(p_name) * _goal_multiplier(area, house_n) * dm
            rows.append({"direction": d, "score": round(hsum + tag_pen, 2)})
        rows.sort(key=lambda x: x["score"])
        area_scores[area] = {"top_directions": rows[:3], "all": rows}

    return {
        "mapping_version": MAPPING_VERSION,
        "mapping_model": "sign_to_fixed_dik",
        "goal": goal_n,
        "door_facing": door,
        "methodology": methodology,
        "dasha_context": dasha_context or {},
        "area_scores": area_scores,
        "directions": directions_out,
        "ranked_directions": ranked,
        "hero": {
            "direction": hero_dir,
            "summary": narrative,
            "total_score": hero["total_score"] if hero else 0,
            "priority_label": hero["priority_label"] if hero else "",
            "planets": hero_planets,
            "planet_breakdown": sorted(
                hero_block.get("planet_details") or [],
                key=lambda x: str(x.get("planet") or ""),
            ),
            "goal_label": gc["label"],
            "goal_scoring": gc["scoring"],
            "chart_why_lines": why_chart,
            "tag_why_lines": why_tag,
            "why_lines": hero_why_full,
            "tags": hero_tags,
            "remedies": remedies,
        },
        "narrative": narrative,
    }
