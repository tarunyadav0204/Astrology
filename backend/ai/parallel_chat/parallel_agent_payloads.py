"""
Assemble VARIABLE_DATA_JSON payloads from context agents (compact keys per SCHEMA.md).

Parashari branch uses a multi-agent bundle; specialist branches use one agent each.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional
from calculators.vedic_graha_drishti import GRAHA_HOUSE_ASPECTS

# Parallel Parashari: div_intent must not repeat D1/D9 already sent as core_d1 + div_d9.
_PARASHARI_DIV_INTENT_OMIT = frozenset({"D1", "D9"})

from context_agents.base import AgentContext
from context_agents.registry import build_agent

logger = logging.getLogger(__name__)

_CATEGORY_TARGETS: Dict[str, Dict[str, Any]] = {
    "career": {"hs": [10, 6, 2, 11], "dv": ["D10", "D9"]},
    "job": {"hs": [10, 6, 2, 11], "dv": ["D10", "D9"]},
    "promotion": {"hs": [10, 6, 2, 11], "dv": ["D10", "D9"]},
    "business": {"hs": [10, 7, 2, 11], "dv": ["D10", "D9"]},
    "wealth": {"hs": [2, 11, 5, 9], "dv": ["D9"]},
    "money": {"hs": [2, 11, 5, 9], "dv": ["D9"]},
    "finance": {"hs": [2, 11, 5, 9], "dv": ["D9"]},
    "marriage": {"hs": [7, 2, 8, 11], "dv": ["D7", "D9"]},
    "love": {"hs": [5, 7, 11, 2], "dv": ["D7", "D9"]},
    "relationship": {"hs": [7, 5, 2, 11], "dv": ["D7", "D9"]},
    "partner": {"hs": [7, 2, 8, 11], "dv": ["D7", "D9"]},
    "spouse": {"hs": [7, 2, 8, 11], "dv": ["D7", "D9"]},
    "health": {"hs": [6, 8, 12, 1], "dv": ["D30", "D9"]},
    "disease": {"hs": [6, 8, 12, 1], "dv": ["D30", "D9"]},
    "education": {"hs": [4, 5, 9, 2], "dv": ["D24", "D9"]},
    "learning": {"hs": [4, 5, 9, 2], "dv": ["D24", "D9"]},
    "property": {"hs": [4, 11, 2, 8], "dv": ["D4", "D9"]},
    "home": {"hs": [4, 2, 11, 8], "dv": ["D4", "D9"]},
    "child": {"hs": [5, 9, 2, 11], "dv": ["D7", "D9"]},
    "children": {"hs": [5, 9, 2, 11], "dv": ["D7", "D9"]},
    "pregnancy": {"hs": [5, 8, 2, 11], "dv": ["D7", "D9"]},
    "travel": {"hs": [3, 9, 12, 7], "dv": ["D9", "D12"]},
    "foreign": {"hs": [12, 9, 7, 3], "dv": ["D9", "D12"]},
    "visa": {"hs": [12, 9, 7, 3], "dv": ["D9", "D12"]},
    "general": {"hs": [1, 5, 7, 10], "dv": ["D9"]},
    "timing": {"hs": [1, 5, 7, 10], "dv": ["D9"]},
}

_PLANET_FUNCTION_TAGS: Dict[str, List[str]] = {
    "Sun": ["authority", "administration", "government", "leadership"],
    "Moon": ["public-facing", "care", "hospitality", "people-work"],
    "Mars": ["technical", "engineering", "operations", "execution"],
    "Mercury": ["analysis", "communication", "sales", "commercial"],
    "Jupiter": ["teaching", "advisory", "law", "guidance"],
    "Venus": ["design", "finance", "client-facing", "creative"],
    "Saturn": ["operations", "industry", "administration", "process"],
    "Rahu": ["technology", "media", "foreign", "innovation"],
    "Ketu": ["research", "specialist", "back-end", "independent"],
}

_SIGN_ELEMENT: Dict[str, str] = {
    "Aries": "fire",
    "Leo": "fire",
    "Sagittarius": "fire",
    "Taurus": "earth",
    "Virgo": "earth",
    "Capricorn": "earth",
    "Gemini": "air",
    "Libra": "air",
    "Aquarius": "air",
    "Cancer": "water",
    "Scorpio": "water",
    "Pisces": "water",
}

_HEALTH_PLANET_SYSTEMS: Dict[str, str] = {
    "Sun": "vitality, heart, immunity",
    "Moon": "mind, fluids, digestion",
    "Mars": "inflammation, blood, injury",
    "Mercury": "nerves, skin, respiration",
    "Jupiter": "liver, growth, metabolic expansion",
    "Venus": "reproductive balance, sugars, kidneys",
    "Saturn": "bones, teeth, chronic depletion",
    "Rahu": "toxicity, irregularity, overstimulation",
    "Ketu": "hidden sensitivity, depletion, unusual patterns",
}

_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu", "GK"}
_NADI_CAREER_PLANETS = ("Saturn", "Mercury", "Mars", "Jupiter", "Rahu", "Sun")
_NADI_REL_PLANETS = ("Venus", "Moon", "Jupiter", "Saturn", "Rahu", "Ketu", "Mars")
_NADI_WEALTH_PLANETS = ("Jupiter", "Venus", "Mercury", "Moon", "Saturn", "Rahu")
_NADI_HEALTH_PLANETS = ("Sun", "Moon", "Mars", "Saturn", "Rahu", "Ketu")

_NADI_SIGNATURES: Dict[tuple[str, str], Dict[str, str]] = {
    ("Saturn", "Mercury"): {"topic": "career", "tone": "analytical-systems", "txt": "analytical, commercial, systems-oriented work"},
    ("Saturn", "Mars"): {"topic": "career", "tone": "technical-execution", "txt": "technical, engineering, operational execution"},
    ("Saturn", "Jupiter"): {"topic": "career", "tone": "advisory-governance", "txt": "advisory, policy, governance, teaching, or strategic guidance"},
    ("Saturn", "Rahu"): {"topic": "career", "tone": "technology-scale", "txt": "technology, mass systems, foreign or unconventional career channels"},
    ("Saturn", "Ketu"): {"topic": "career", "tone": "research-specialist", "txt": "research, diagnostics, detached specialist or back-end work"},
    ("Venus", "Moon"): {"topic": "relationship", "tone": "bonding", "txt": "affection, emotional bonding, and relational nourishment"},
    ("Venus", "Jupiter"): {"topic": "relationship", "tone": "supportive-alliance", "txt": "supportive alliance, values, and relationship grace"},
    ("Venus", "Saturn"): {"topic": "relationship", "tone": "delay-duty", "txt": "delay, duty, sobriety, or karmic responsibility in relationships"},
    ("Venus", "Rahu"): {"topic": "relationship", "tone": "unconventional-intense", "txt": "unconventional, foreign, intense, or unstable attraction"},
    ("Venus", "Ketu"): {"topic": "relationship", "tone": "detached-karmic", "txt": "detachment, unusual karmic bonds, or low worldly attachment"},
    ("Mars", "Venus"): {"topic": "relationship", "tone": "passion-friction", "txt": "strong passion, chemistry, and also conflict or impatience"},
    ("Mars", "Moon"): {"topic": "relationship", "tone": "emotional-heat", "txt": "emotional reactivity, passion, and interpersonal heat"},
    ("Jupiter", "Venus"): {"topic": "wealth", "tone": "prosperity-support", "txt": "prosperity, support, and value-building capacity"},
    ("Mercury", "Venus"): {"topic": "wealth", "tone": "trade-value", "txt": "trade, design, commerce, and monetizable skills"},
    ("Jupiter", "Mercury"): {"topic": "wealth", "tone": "advisory-commerce", "txt": "advisory intelligence, education, finance, or commercial judgment"},
    ("Saturn", "Moon"): {"topic": "health", "tone": "drain-stress", "txt": "stress, depletion, or chronic emotional burden"},
    ("Mars", "Saturn"): {"topic": "health", "tone": "strain-injury", "txt": "physical strain, inflammatory pressure, or wear-and-tear risk"},
    ("Rahu", "Moon"): {"topic": "health", "tone": "volatility", "txt": "volatility, overstimulation, or psychosomatic fluctuation"},
}

_DIVISIONAL_FOCUS_PLANETS: Dict[str, List[str]] = {
    "career": ["Sun", "Mercury", "Saturn", "Jupiter", "Mars"],
    "job": ["Sun", "Mercury", "Saturn", "Jupiter", "Mars"],
    "promotion": ["Sun", "Mercury", "Saturn", "Jupiter"],
    "business": ["Mercury", "Venus", "Saturn", "Jupiter"],
    "marriage": ["Venus", "Jupiter", "Moon", "Saturn", "Mars"],
    "relationship": ["Venus", "Jupiter", "Moon", "Saturn", "Mars"],
    "love": ["Venus", "Moon", "Mars", "Jupiter"],
    "partner": ["Venus", "Jupiter", "Moon", "Saturn"],
    "spouse": ["Venus", "Jupiter", "Moon", "Saturn"],
    "child": ["Jupiter", "Moon", "Venus", "Sun"],
    "children": ["Jupiter", "Moon", "Venus", "Sun"],
    "pregnancy": ["Jupiter", "Moon", "Venus"],
    "education": ["Mercury", "Jupiter", "Moon", "Sun"],
    "learning": ["Mercury", "Jupiter", "Moon", "Sun"],
    "health": ["Sun", "Moon", "Mars", "Saturn"],
    "disease": ["Sun", "Moon", "Mars", "Saturn"],
    "property": ["Moon", "Mars", "Venus", "Saturn"],
    "home": ["Moon", "Mars", "Venus", "Saturn"],
    "general": ["Sun", "Moon", "Jupiter", "Venus"],
    "timing": ["Sun", "Moon", "Jupiter", "Venus"],
}

_DIVISIONAL_TOPIC_HOUSES: Dict[str, List[int]] = {
    "career": [1, 10, 6, 11, 2],
    "job": [1, 10, 6, 11, 2],
    "promotion": [1, 10, 11, 6, 2],
    "business": [1, 7, 10, 11, 2],
    "marriage": [1, 7, 2, 8, 11],
    "relationship": [1, 7, 2, 8, 11],
    "love": [1, 5, 7, 11, 2],
    "partner": [1, 7, 2, 8, 11],
    "spouse": [1, 7, 2, 8, 11],
    "child": [1, 5, 9, 2, 11],
    "children": [1, 5, 9, 2, 11],
    "pregnancy": [1, 5, 8, 2, 11],
    "education": [1, 4, 5, 9, 2],
    "learning": [1, 4, 5, 9, 2],
    "health": [1, 6, 8, 12],
    "disease": [1, 6, 8, 12],
    "property": [1, 4, 11, 2, 8],
    "home": [1, 4, 2, 11, 8],
    "general": [1, 5, 7, 10],
    "timing": [1, 5, 7, 10],
}

_DIVISIONAL_TOPIC_CODES: Dict[str, List[str]] = {
    "career": ["D10", "Karkamsa", "D9"],
    "job": ["D10", "Karkamsa", "D9"],
    "promotion": ["D10", "Karkamsa", "D9"],
    "business": ["D10", "Karkamsa", "D9"],
    "marriage": ["D9", "D7"],
    "relationship": ["D9", "D7"],
    "love": ["D9", "D7"],
    "partner": ["D9", "D7"],
    "spouse": ["D9", "D7"],
    "child": ["D7", "D9"],
    "children": ["D7", "D9"],
    "pregnancy": ["D7", "D9"],
    "education": ["D24", "D9"],
    "learning": ["D24", "D9"],
    "health": ["D30", "D9"],
    "disease": ["D30", "D9"],
    "property": ["D4", "D9"],
    "home": ["D4", "D9"],
    "general": ["D9"],
    "timing": ["D9"],
}

# Ordered list for Parashari-style synthesis (no single parashari agent exists).
# Chara Dasha is Jaimini-only — not included here (see Jaimini branch).
# `div_intent`: intent-listed divisionals; D1/D9 are omitted when building this bundle (see `AgentContext.div_intent_omit_codes`)
# so they are not duplicated with `core_d1` + `div_d9`.
# `special_points` (Yogi / Avayogi / Dagdha / Gandanta) is merged in from full chart context when provided
# so agent-mode Parashari matches legacy `build_parashari_slice` for those keys.
PARASHARI_AGENT_IDS: tuple[str, ...] = (
    "core_d1",
    "d1_graha",
    "vim_dasha",
    "div_d9",
    "div_intent",
    "parashari_day",
    "transit_win",
    "dasha_win",
    "panch_maitri",
    "sniper_pts",
)


def _is_health_category(cat: str) -> bool:
    return str(cat or "").strip().lower() in {"health", "disease"}


def build_parashari_agent_payload(
    agent_ctx: AgentContext,
    user_question: str,
    *,
    merged_chart_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    agents: Dict[str, Any] = {}
    cat = str(((agent_ctx.intent_result or {}).get("category")) or "general")
    prev_omit = agent_ctx.div_intent_omit_codes
    agent_ctx.div_intent_omit_codes = _PARASHARI_DIV_INTENT_OMIT
    try:
        for aid in PARASHARI_AGENT_IDS:
            try:
                agents[aid] = build_agent(aid, agent_ctx)
            except Exception as e:
                logger.warning("parashari bundle agent %s failed: %s", aid, e)
                agents[aid] = {"a": aid, "error": str(e)[:300]}
        if _is_health_category(cat):
            try:
                agents["health"] = build_agent("health", agent_ctx)
            except Exception as e:
                logger.warning("parashari bundle agent health failed: %s", e)
                agents["health"] = {"a": "health", "error": str(e)[:300]}
    finally:
        agent_ctx.div_intent_omit_codes = prev_omit
    out: Dict[str, Any] = {
        "parashari_agents": agents,
        "px": _build_parashari_derived_payload(agent_ctx, agents),
        "user_question": user_question,
    }
    if merged_chart_context:
        sp = merged_chart_context.get("special_points")
        if isinstance(sp, dict) and sp:
            out["special_points"] = copy.deepcopy(sp)
    return out


def build_single_agent_payload(agent_id: str, agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    blob = build_agent(agent_id, agent_ctx)
    return {agent_id: blob, "user_question": user_question}


def build_nadi_agent_payload(agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    nadi = build_agent("nadi", agent_ctx)
    return {
        "nadi": nadi,
        "nx": _build_nadi_derived_payload(agent_ctx, nadi),
        "user_question": user_question,
    }


def _active_dasha_source(agent_ctx: AgentContext, agents: Dict[str, Any]) -> str:
    ir = agent_ctx.intent_result if isinstance(agent_ctx.intent_result, dict) else {}
    if (agents.get("parashari_day") or {}).get("x"):
        return "day"
    if ir.get("dasha_as_of") or ir.get("transit_request") or agent_ctx.requested_period:
        return "window"
    return "current"


def _topic_meta(agent_ctx: AgentContext) -> Dict[str, Any]:
    ir = agent_ctx.intent_result if isinstance(agent_ctx.intent_result, dict) else {}
    cat = str(ir.get("category") or "general").strip().lower() or "general"
    meta = _CATEGORY_TARGETS.get(cat, _CATEGORY_TARGETS["general"])
    return {"cat": cat, "hs": list(meta["hs"]), "dv": list(meta["dv"])}


def _core_planet_maps(core: Dict[str, Any]) -> tuple[Dict[str, int], Dict[str, str], Dict[str, List[int]]]:
    by_house: Dict[str, int] = {}
    by_sign: Dict[str, str] = {}
    for row in core.get("P") or []:
        if not isinstance(row, list) or len(row) < 5:
            continue
        by_sign[str(row[0])] = str(row[3])
        try:
            by_house[str(row[0])] = int(row[4])
        except (TypeError, ValueError):
            continue
    lordships = core.get("H") or {}
    return by_house, by_sign, lordships if isinstance(lordships, dict) else {}


def _chart_present(chart: Dict[str, Any]) -> bool:
    return bool(
        isinstance(chart, dict)
        and isinstance(chart.get("L"), dict)
        and isinstance(chart.get("P"), list)
        and isinstance(chart.get("H"), dict)
    )


def _chart_planet_rows(chart: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for row in chart.get("P") or []:
        if not isinstance(row, list) or len(row) < 5:
            continue
        try:
            rows[str(row[0])] = {
                "lon": row[1],
                "s": int(row[2]),
                "sn": str(row[3]),
                "h": int(row[4]),
            }
        except (TypeError, ValueError):
            continue
    return rows


def _chart_house_lords(chart: Dict[str, Any]) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for planet, houses in (chart.get("H") or {}).items():
        if not isinstance(houses, list):
            continue
        for house in houses:
            try:
                out[int(house)] = str(planet)
            except (TypeError, ValueError):
                continue
    return out


def _house_sign_from_lagna(lagna_sign: Any, house: int) -> Optional[int]:
    try:
        ls = int(lagna_sign)
        h = int(house)
    except (TypeError, ValueError):
        return None
    if not (1 <= ls <= 12 and 1 <= h <= 12):
        return None
    return ((ls + h - 2) % 12) + 1


def _support_band_from_counts(supportive: int, obstructive: int) -> str:
    if supportive > obstructive:
        return "supportive"
    if obstructive > supportive:
        return "weak"
    return "mixed"


def _divisional_house_rows(chart: Dict[str, Any], houses: List[int], focus_planets: List[str]) -> List[Dict[str, Any]]:
    if not _chart_present(chart):
        return []
    lagna_sign = (chart.get("L") or {}).get("s")
    planets = _chart_planet_rows(chart)
    lords = _chart_house_lords(chart)
    focus = set(focus_planets)
    rows: List[Dict[str, Any]] = []
    for house in houses:
        sign = _house_sign_from_lagna(lagna_sign, house)
        occ = sorted([planet for planet, row in planets.items() if int(row.get("h") or 0) == house])
        focus_occ = [planet for planet in occ if planet in focus]
        lord = lords.get(int(house))
        lord_row = planets.get(str(lord)) if lord else None
        lord_h = lord_row.get("h") if isinstance(lord_row, dict) else None
        supportive = 0
        obstructive = 0
        if isinstance(lord_h, int):
            if lord_h in {1, 2, 4, 5, 7, 9, 10, 11}:
                supportive += 1
            if lord_h in {6, 8, 12}:
                obstructive += 1
        supportive += len([planet for planet in occ if planet in _BENEFICS])
        obstructive += len([planet for planet in occ if planet in _MALEFICS])
        supportive += len(focus_occ)
        rows.append(
            {
                "h": int(house),
                "s": sign,
                "lord": lord,
                "lord_h": lord_h,
                "occ": occ,
                "foc": focus_occ,
                "band": _support_band_from_counts(supportive, obstructive),
            }
        )
    rows.sort(key=lambda item: (0 if item.get("band") == "supportive" else 1 if item.get("band") == "mixed" else 2, int(item.get("h") or 99)))
    return rows


def _divisional_chart_summary(code: str, chart: Dict[str, Any], houses: List[int], focus_planets: List[str]) -> Dict[str, Any]:
    rows = _divisional_house_rows(chart, houses, focus_planets)
    supportive = sum(1 for row in rows if row.get("band") == "supportive")
    weak = sum(1 for row in rows if row.get("band") == "weak")
    return {
        "lagna": (chart.get("L") or {}).get("s"),
        "rows": rows,
        "support": _support_band_from_counts(supportive, weak),
        "best": [row.get("h") for row in rows if row.get("band") == "supportive"][:3],
        "hard": [row.get("h") for row in rows if row.get("band") == "weak"][:3],
        "code": code,
    }


def _topic_lords_from_core(core: Dict[str, Any], houses: List[int]) -> List[str]:
    lords = _chart_house_lords(core)
    out: List[str] = []
    for house in houses:
        lord = lords.get(int(house))
        if lord and lord not in out:
            out.append(lord)
    return out


def _divisional_root_fruit(core: Dict[str, Any], d9: Dict[str, Any], category: str, houses: List[int]) -> List[Dict[str, Any]]:
    if not (_chart_present(core) and _chart_present(d9)):
        return []
    d1_rows = _chart_planet_rows(core)
    d9_rows = _chart_planet_rows(d9)
    planets = []
    for planet in _topic_lords_from_core(core, houses) + _DIVISIONAL_FOCUS_PLANETS.get(category, _DIVISIONAL_FOCUS_PLANETS["general"]):
        if planet not in planets:
            planets.append(planet)
    out: List[Dict[str, Any]] = []
    for planet in planets[:8]:
        d1 = d1_rows.get(planet)
        d9r = d9_rows.get(planet)
        if not (isinstance(d1, dict) and isinstance(d9r, dict)):
            continue
        same_sign = int(d1.get("s") or 0) == int(d9r.get("s") or 0)
        d9h = int(d9r.get("h") or 0)
        if same_sign or d9h in {1, 4, 5, 7, 9, 10, 11, 2}:
            band = "strong"
        elif d9h in {6, 8, 12}:
            band = "weak"
        else:
            band = "mixed"
        out.append(
            {
                "p": planet,
                "d1h": d1.get("h"),
                "d1s": d1.get("s"),
                "d9h": d9r.get("h"),
                "d9s": d9r.get("s"),
                "vg": same_sign,
                "band": band,
            }
        )
    return out


def _collect_divisional_charts(agents: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    charts: Dict[str, Dict[str, Any]] = {}
    d9 = agents.get("div_d9") or {}
    if _chart_present(d9):
        charts["D9"] = {k: d9[k] for k in ("L", "P", "H")}
    for code, chart in ((agents.get("div_intent") or {}).get("C") or {}).items():
        if isinstance(code, str) and _chart_present(chart):
            charts[code] = chart
    return charts


def _divisional_topic_payload(category: str, div_charts: Dict[str, Dict[str, Any]], houses: List[int]) -> Dict[str, Any]:
    codes = _DIVISIONAL_TOPIC_CODES.get(category, _DIVISIONAL_TOPIC_CODES["general"])
    focus = _DIVISIONAL_FOCUS_PLANETS.get(category, _DIVISIONAL_FOCUS_PLANETS["general"])
    charts: Dict[str, Any] = {}
    supportive = 0
    weak = 0
    for code in codes:
        chart = div_charts.get(code)
        if not _chart_present(chart or {}):
            continue
        summary = _divisional_chart_summary(code, chart, _DIVISIONAL_TOPIC_HOUSES.get(category, houses), focus)
        charts[code] = summary
        if summary["support"] == "supportive":
            supportive += 1
        elif summary["support"] == "weak":
            weak += 1
    return {
        "codes": codes,
        "charts": charts,
        "support": _support_band_from_counts(supportive, weak),
        "avail": {code: bool(code in charts) for code in codes},
    }


def _divisional_dasha_rows(
    chart: Dict[str, Any],
    houses: List[int],
    levels: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not _chart_present(chart):
        return []
    planet_rows = _chart_planet_rows(chart)
    house_lords = _chart_house_lords(chart)
    rows: List[Dict[str, Any]] = []
    for level in ("md", "ad", "pd"):
        lvl = levels.get(level) or {}
        planet = str(lvl.get("p") or "")
        if not planet:
            continue
        prow = planet_rows.get(planet)
        ruled = sorted([house for house in houses if house_lords.get(int(house)) == planet])
        occ = []
        if isinstance(prow, dict):
            try:
                ph = int(prow.get("h") or 0)
            except (TypeError, ValueError):
                ph = 0
            if ph in houses:
                occ.append(ph)
        supportive = len(ruled) + len(occ)
        band = "supportive" if supportive > 0 else "weak"
        rows.append(
            {
                "lvl": level,
                "p": planet,
                "h": prow.get("h") if isinstance(prow, dict) else None,
                "rh": ruled,
                "occ": occ,
                "band": band,
            }
        )
    return rows


def _divisional_current_payload(
    category: str,
    div_charts: Dict[str, Dict[str, Any]],
    levels: Dict[str, Dict[str, Any]],
    houses: List[int],
) -> Dict[str, Any]:
    codes = _DIVISIONAL_TOPIC_CODES.get(category, _DIVISIONAL_TOPIC_CODES["general"])
    out: Dict[str, Any] = {"codes": codes, "charts": {}, "support": "mixed"}
    supportive = 0
    weak = 0
    target_houses = _DIVISIONAL_TOPIC_HOUSES.get(category, houses)
    for code in codes:
        chart = div_charts.get(code)
        if not _chart_present(chart or {}):
            continue
        rows = _divisional_dasha_rows(chart, target_houses, levels)
        if not rows:
            continue
        score = sum(1 for row in rows if row.get("band") == "supportive")
        hard = sum(1 for row in rows if row.get("band") == "weak")
        support = _support_band_from_counts(score, hard)
        out["charts"][code] = {
            "rows": rows,
            "support": support,
            "best": [row["lvl"] for row in rows if row.get("band") == "supportive"],
            "hard": [row["lvl"] for row in rows if row.get("band") == "weak"],
        }
        if support == "supportive":
            supportive += 1
        elif support == "weak":
            weak += 1
    out["support"] = _support_band_from_counts(supportive, weak)
    out["avail"] = {code: bool(code in out["charts"]) for code in codes}
    return out


def _level_from_source(level_key: str, source: str, agents: Dict[str, Any]) -> Dict[str, Any]:
    if source == "window":
        return (agents.get("dasha_win") or {}).get(level_key) or {}
    if source == "day":
        return (agents.get("dasha_win") or {}).get(level_key) or {}
    return ((agents.get("vim_dasha") or {}).get("D") or {}).get(level_key) or {}


def _aspect_targets_from_house(house: Any, planet: str) -> List[int]:
    try:
        h = int(house)
    except (TypeError, ValueError):
        return []
    out = []
    for n in GRAHA_HOUSE_ASPECTS.get(planet, [1, 7]):
        out.append(((h + n - 2) % 12) + 1)
    return sorted(set(out))


def _active_level_summary(
    level_key: str,
    row: Dict[str, Any],
    by_house: Dict[str, int],
    by_sign: Dict[str, str],
    lordships: Dict[str, List[int]],
    graha: Dict[str, Any],
) -> Dict[str, Any]:
    planet = row.get("p")
    if not planet:
        return {}
    g = graha.get(str(planet)) if isinstance(graha, dict) else {}
    h = row.get("h")
    if h is None:
        h = by_house.get(str(planet))
    out: Dict[str, Any] = {"p": planet, "rh": lordships.get(str(planet), [])}
    if h is not None:
        out["h"] = h
        out["ahs"] = _aspect_targets_from_house(h, str(planet))
    sn = row.get("sn") or by_sign.get(str(planet))
    if sn:
        out["sn"] = sn
    for src, dst in (("fn", "fn"), ("d", "d"), ("av", "av"), ("sc", "sc"), ("cb", "cb"), ("r", "r")):
        v = (g or {}).get(src)
        if v is not None and v != "":
            out[dst] = v
    return out


def _house_impact_summary(target_houses: List[int], levels: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {}
    for house in target_houses:
        row = {"r": [], "o": [], "a": []}
        for lvl, data in levels.items():
            if not isinstance(data, dict) or not data.get("p"):
                continue
            if house in (data.get("rh") or []):
                row["r"].append(lvl)
            try:
                if int(data.get("h")) == house:
                    row["o"].append(lvl)
            except (TypeError, ValueError):
                pass
            if house in (data.get("ahs") or []):
                row["a"].append(lvl)
        out[str(house)] = row
    return out


def _transit_summary(target_houses: List[int], levels: Dict[str, Dict[str, Any]], transit_win: Dict[str, Any]) -> Dict[str, Any]:
    acts = transit_win.get("A") or []
    if not isinstance(acts, list):
        acts = []
    active_planets = {str(v.get("p")) for v in levels.values() if isinstance(v, dict) and v.get("p")}
    target_set = {int(h) for h in target_houses}
    th: Dict[str, int] = {}
    nh: Dict[str, int] = {}
    dp: List[Dict[str, Any]] = []

    for act in acts:
        if not isinstance(act, dict):
            continue
        try:
            t_h = int(act.get("th"))
            if t_h in target_set:
                th[str(t_h)] = th.get(str(t_h), 0) + 1
        except (TypeError, ValueError):
            pass
        try:
            n_h = int(act.get("nh"))
            if n_h in target_set:
                nh[str(n_h)] = nh.get(str(n_h), 0) + 1
        except (TypeError, ValueError):
            pass
        if act.get("tp") in active_planets or act.get("np") in active_planets:
            dp.append({k: act.get(k) for k in ("tp", "np", "sd", "ed", "th", "nh", "at", "pk") if act.get(k) is not None})

    out: Dict[str, Any] = {"n": len(acts), "th": th, "nh": nh}
    if dp:
        out["dp"] = dp[:10]
    if isinstance(transit_win.get("p"), list) and transit_win.get("p"):
        out["pd"] = list(transit_win["p"][:8])
    return out


def _build_parashari_derived_payload(agent_ctx: AgentContext, agents: Dict[str, Any]) -> Dict[str, Any]:
    topic = _topic_meta(agent_ctx)
    source = _active_dasha_source(agent_ctx, agents)
    core = agents.get("core_d1") or {}
    by_house, by_sign, lordships = _core_planet_maps(core)
    graha = (agents.get("d1_graha") or {}).get("G") or {}
    div_charts = _collect_divisional_charts(agents)

    levels = {
        lvl: _active_level_summary(
            lvl,
            _level_from_source(lvl, source, agents),
            by_house,
            by_sign,
            lordships,
            graha,
        )
        for lvl in ("md", "ad", "pd", "sk", "pr")
    }

    divs = {code: bool(code in div_charts) for code in topic["dv"]}
    dx_topic = _divisional_topic_payload(topic["cat"], div_charts, topic["hs"])
    dx = {
        "cat": topic["cat"],
        "rf": _divisional_root_fruit(core, div_charts.get("D9") or {}, topic["cat"], topic["hs"]),
        "topic": dx_topic,
        "current": {
            "topic": _divisional_current_payload(topic["cat"], div_charts, levels, topic["hs"]),
            "career": _divisional_current_payload("career", div_charts, levels, _CATEGORY_TARGETS["career"]["hs"]),
            "relationship": _divisional_current_payload("relationship", div_charts, levels, _CATEGORY_TARGETS["relationship"]["hs"]),
            "education": _divisional_current_payload("education", div_charts, levels, _CATEGORY_TARGETS["education"]["hs"]),
            "health": _divisional_current_payload("health", div_charts, levels, _CATEGORY_TARGETS["health"]["hs"]),
        },
        "career": _divisional_topic_payload("career", div_charts, _CATEGORY_TARGETS["career"]["hs"]),
        "relationship": _divisional_topic_payload("relationship", div_charts, _CATEGORY_TARGETS["relationship"]["hs"]),
        "education": _divisional_topic_payload("education", div_charts, _CATEGORY_TARGETS["education"]["hs"]),
        "health": _divisional_topic_payload("health", div_charts, _CATEGORY_TARGETS["health"]["hs"]),
    }

    out = {
        "src": source,
        "cat": topic["cat"],
        "hs": topic["hs"],
        "dv": divs,
        "dx": dx,
        "D": levels,
        "HI": _house_impact_summary(topic["hs"], levels),
        "TR": _transit_summary(topic["hs"], levels, agents.get("transit_win") or {}),
        "career": _build_parashari_career_payload(levels, divs),
        "relationship": _build_parashari_relationship_payload(levels, divs),
        "wealth": _build_parashari_wealth_payload(levels, divs),
    }
    if _is_health_category(topic["cat"]):
        out["health"] = _build_parashari_health_payload(levels, divs, core, agents.get("health") or {})
    return out


def _activation_score(row: Dict[str, List[str]]) -> int:
    if not isinstance(row, dict):
        return 0
    return (len(row.get("o") or []) * 3) + (len(row.get("r") or []) * 2) + len(row.get("a") or [])


def _rank_houses(hi: Dict[str, Dict[str, List[str]]]) -> List[int]:
    ranked = sorted(
        ((int(h), _activation_score(v)) for h, v in hi.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return [house for house, score in ranked if score > 0]


def _rank_function_tags(levels: Dict[str, Dict[str, Any]]) -> List[str]:
    weights = {"md": 5, "ad": 4, "pd": 2, "sk": 1, "pr": 1}
    scores: Dict[str, int] = {}
    for lvl, row in levels.items():
        if not isinstance(row, dict):
            continue
        planet = str(row.get("p") or "")
        if not planet:
            continue
        for tag in _PLANET_FUNCTION_TAGS.get(planet, []):
            scores[tag] = scores.get(tag, 0) + weights.get(lvl, 1)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [tag for tag, _score in ranked[:4]]


def _house_level_weight(levels: Dict[str, Dict[str, Any]], house: int) -> int:
    score = 0
    for row in levels.values():
        if not isinstance(row, dict):
            continue
        if house in (row.get("rh") or []):
            score += 2
        try:
            if int(row.get("h")) == house:
                score += 3
        except (TypeError, ValueError):
            pass
        if house in (row.get("ahs") or []):
            score += 1
    return score


def _build_parashari_career_payload(levels: Dict[str, Dict[str, Any]], divs: Dict[str, bool]) -> Dict[str, Any]:
    hi = _house_impact_summary([10, 6, 2, 11, 7, 3, 8, 12], levels)
    ranked = _rank_houses(hi)
    service_score = _house_level_weight(levels, 6)
    business_score = _house_level_weight(levels, 7)
    skill_score = _house_level_weight(levels, 3)
    hidden_score = _house_level_weight(levels, 8) + _house_level_weight(levels, 12)
    visibility_score = _house_level_weight(levels, 10) + _house_level_weight(levels, 11)
    if service_score and business_score and abs(service_score - business_score) <= 2:
        mode = "hybrid"
    elif business_score > service_score:
        mode = "business"
    elif service_score > 0:
        mode = "service"
    else:
        mode = "unclear"
    if visibility_score >= max(service_score, skill_score, hidden_score, 1) + 2:
        visibility = "high"
    elif visibility_score > 0:
        visibility = "mixed"
    else:
        visibility = "low"
    return {
        "hs": [10, 6, 2, 11],
        "dv": {"D10": bool(divs.get("D10")), "D9": bool(divs.get("D9"))},
        "dom": ranked[:5],
        "mode": mode,
        "work": {
            "service": service_score,
            "business": business_score,
            "skill": skill_score,
            "hidden": hidden_score,
        },
        "vis": visibility,
        "fn": _rank_function_tags(levels),
    }


def _build_parashari_relationship_payload(levels: Dict[str, Dict[str, Any]], divs: Dict[str, bool]) -> Dict[str, Any]:
    hi = _house_impact_summary([7, 2, 11, 8, 6, 12], levels)
    ranked = _rank_houses(hi)
    materialization = sum(_house_level_weight(levels, h) for h in (2, 7, 11))
    friction = sum(_house_level_weight(levels, h) for h in (6, 8, 12))
    continuity = _house_level_weight(levels, 2) + _house_level_weight(levels, 8)
    if materialization > friction + 2:
        verdict = "supportive"
    elif friction > materialization + 1:
        verdict = "obstructed"
    else:
        verdict = "mixed"
    return {
        "hs": [7, 2, 8, 11],
        "dv": {"D7": bool(divs.get("D7")), "D9": bool(divs.get("D9"))},
        "dom": ranked[:5],
        "mat": materialization,
        "fr": friction,
        "ct": continuity,
        "mode": verdict,
    }


def _build_parashari_wealth_payload(levels: Dict[str, Dict[str, Any]], divs: Dict[str, bool]) -> Dict[str, Any]:
    hi = _house_impact_summary([2, 11, 5, 9, 8, 12, 6, 10], levels)
    ranked = _rank_houses(hi)
    accumulation = _house_level_weight(levels, 2)
    gains = _house_level_weight(levels, 11)
    speculation = _house_level_weight(levels, 5)
    fortune = _house_level_weight(levels, 9)
    debt_service = _house_level_weight(levels, 6)
    sudden = _house_level_weight(levels, 8)
    expense = _house_level_weight(levels, 12)
    career_income = _house_level_weight(levels, 10) + debt_service
    business_income = _house_level_weight(levels, 7) + gains
    investment_income = speculation + fortune
    risk = sudden + expense + debt_service
    if business_income >= max(career_income, investment_income, 1) + 2:
        mode = "business_network"
    elif investment_income >= max(career_income, business_income, 1) + 2:
        mode = "investment_speculation"
    elif career_income >= max(business_income, investment_income, 1):
        mode = "salary_service"
    else:
        mode = "mixed"
    if risk > accumulation + gains + fortune:
        risk_band = "high"
    elif risk >= max(accumulation, gains, fortune, 1):
        risk_band = "medium"
    else:
        risk_band = "managed"
    return {
        "hs": [2, 11, 5, 9],
        "dv": {"D9": bool(divs.get("D9")), "D10": bool(divs.get("D10"))},
        "dom": ranked[:6],
        "acc": accumulation,
        "gain": gains,
        "spec": speculation,
        "fort": fortune,
        "risk": {"debt": debt_service, "sudden": sudden, "expense": expense, "band": risk_band},
        "mode": mode,
        "income": {"career": career_income, "business": business_income, "investment": investment_income},
    }


def _health_constitution_from_levels(levels: Dict[str, Dict[str, Any]], core: Dict[str, Any]) -> Dict[str, Any]:
    weights = {"md": 5, "ad": 4, "pd": 2, "sk": 1, "pr": 1}
    element_scores: Dict[str, int] = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    used: List[str] = []
    planet_rows = _chart_planet_rows(core)

    for lvl, row in levels.items():
        if not isinstance(row, dict):
            continue
        planet = str(row.get("p") or "")
        if not planet:
            continue
        sign_name = str(row.get("sn") or (planet_rows.get(planet) or {}).get("sn") or "")
        element = _SIGN_ELEMENT.get(sign_name)
        if not element:
            continue
        element_scores[element] += weights.get(lvl, 1)
        used.append(planet)

    ranked = sorted(element_scores.items(), key=lambda item: (-item[1], item[0]))
    lead = ranked[0][0] if ranked and ranked[0][1] > 0 else "mixed"
    if lead == "fire":
        charak = "pitta"
    elif lead in {"water", "earth"}:
        charak = "kapha"
    elif lead == "air":
        charak = "vata"
    else:
        charak = "mixed"
    return {"lead": lead, "charak": charak, "mix": ranked, "pl": used[:5]}


def _build_parashari_health_payload(
    levels: Dict[str, Dict[str, Any]],
    divs: Dict[str, bool],
    core: Dict[str, Any],
    hx: Dict[str, Any],
) -> Dict[str, Any]:
    hs = [1, 6, 8, 12, 4, 5]
    hi = _house_impact_summary(hs, levels)
    ranked = _rank_houses(hi)
    vitality = _house_level_weight(levels, 1) + _house_level_weight(levels, 5)
    acute = _house_level_weight(levels, 6)
    chronic = _house_level_weight(levels, 8) + _house_level_weight(levels, 12)
    mental = _house_level_weight(levels, 4) + _house_level_weight(levels, 12)

    planets = [str(row.get("p")) for row in levels.values() if isinstance(row, dict) and row.get("p")]
    dominant = [p for p in planets if p in _HEALTH_PLANET_SYSTEMS] or planets
    systems = [{"p": p, "sys": _HEALTH_PLANET_SYSTEMS[p]} for p in dominant if p in _HEALTH_PLANET_SYSTEMS][:5]

    if chronic >= acute + 2 and chronic > 0:
        pattern = "chronic"
    elif acute >= chronic + 2 and acute > 0:
        pattern = "acute"
    elif mental >= max(acute, chronic, 1):
        pattern = "sensitivity"
    elif acute > 0 or chronic > 0:
        pattern = "mixed"
    else:
        pattern = "preventive"

    if mental >= max(acute, chronic, 1) + 1:
        tone = "mind-body"
    elif chronic > acute:
        tone = "wear-and-tear"
    elif acute > chronic:
        tone = "flare-up"
    else:
        tone = "mixed"

    out = {
        "hs": hs,
        "dv": {"D30": bool(divs.get("D30")), "D9": bool(divs.get("D9"))},
        "dom": ranked[:6],
        "pattern": pattern,
        "tone": tone,
        "risk": {"vit": vitality, "acu": acute, "chr": chronic, "mnt": mental},
        "body": systems,
        "charak": _health_constitution_from_levels(levels, core),
    }
    if isinstance(hx, dict) and hx:
        if hx.get("hs") is not None:
            out["score"] = hx.get("hs")
        if isinstance(hx.get("ph"), list) and hx.get("ph"):
            out["ph"] = hx.get("ph")
        if isinstance(hx.get("hh"), dict) and hx.get("hh"):
            out["hh"] = hx.get("hh")
        if isinstance(hx.get("rw"), list):
            out["rw"] = hx.get("rw")
        if isinstance(hx.get("ct"), dict) and hx.get("ct"):
            out["charak_agent"] = hx.get("ct")
        if isinstance(hx.get("yg"), dict) and hx.get("yg"):
            out["yg"] = hx.get("yg")
        if hx.get("d30") is not None:
            out["dv"]["D30"] = bool(hx.get("d30"))
    return out


def _rel_from(base_sign: Any, target_sign: Any) -> Optional[int]:
    try:
        b = int(base_sign)
        t = int(target_sign)
    except (TypeError, ValueError):
        return None
    if not (1 <= b <= 12 and 1 <= t <= 12):
        return None
    return ((t - b) % 12) + 1


def _sign_aspects(from_sign: Any, to_sign: Any) -> bool:
    try:
        f0 = (int(from_sign) - 1) % 12
        t0 = (int(to_sign) - 1) % 12
    except (TypeError, ValueError):
        return False

    fm = f0 % 3
    if fm == 0:
        targets = {(f0 + 4) % 12, (f0 + 5) % 12, (f0 + 8) % 12}
    elif fm == 1:
        targets = {(f0 + 4) % 12, (f0 + 7) % 12, (f0 + 8) % 12}
    else:
        targets = {(f0 + 3) % 12, (f0 + 6) % 12, (f0 + 9) % 12}
    return t0 in targets


def _current_md_ad(chara_dasha: Dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
    periods = chara_dasha.get("P") or []
    if not isinstance(periods, list):
        return None, None

    current_md = next((p for p in periods if isinstance(p, dict) and p.get("ic")), None)
    if current_md is None and periods:
        current_md = periods[0] if isinstance(periods[0], dict) else None
    if not isinstance(current_md, dict):
        return None, None

    md_sign = current_md.get("s")
    ads = current_md.get("ad") or []
    current_ad = next((ad for ad in ads if isinstance(ad, dict) and ad.get("ic")), None)
    if current_ad is None and ads:
        current_ad = ads[0] if isinstance(ads[0], dict) else None
    ad_sign = current_ad.get("s") if isinstance(current_ad, dict) else None
    return md_sign, ad_sign


def _occupants_of_sign(planet_signs: Dict[str, Any], sign: Any) -> List[str]:
    out: List[str] = []
    try:
        s = int(sign)
    except (TypeError, ValueError):
        return out
    for planet, row in (planet_signs or {}).items():
        if not isinstance(row, dict):
            continue
        try:
            if int(row.get("s")) == s:
                out.append(str(planet))
        except (TypeError, ValueError):
            continue
    return out


def _ak_amk_connection(ck: Dict[str, Any]) -> str:
    ak = (ck.get("AK") or {}).get("s")
    amk = (ck.get("AmK") or {}).get("s")
    if ak is None or amk is None:
        return "none"
    if ak == amk:
        return "conj"
    return "asp" if _sign_aspects(ak, amk) or _sign_aspects(amk, ak) else "none"


def _build_jaimini_derived_payload(jaimini: Dict[str, Any], chara_dasha: Dict[str, Any]) -> Dict[str, Any]:
    jp = jaimini.get("JP") or {}
    ck = jaimini.get("CK") or {}
    ps = jaimini.get("PS") or {}
    ag = jaimini.get("AG") or {}
    md_sign, ad_sign = _current_md_ad(chara_dasha)

    refs: Dict[str, Dict[str, Any]] = {}
    for ref in ("UL", "A7", "AL", "KL"):
        rs = (jp.get(ref) or {}).get("s")
        if rs is None:
            continue
        refs[ref] = {"md": _rel_from(rs, md_sign), "ad": _rel_from(rs, ad_sign)}

    karakas: Dict[str, Dict[str, Any]] = {}
    for ref in ("AK", "AmK", "DK", "GK"):
        rs = (ck.get(ref) or {}).get("s")
        if rs is None:
            continue
        karakas[ref] = {"md": _rel_from(rs, md_sign), "ad": _rel_from(rs, ad_sign)}

    dk_sign = (ck.get("DK") or {}).get("s")
    dk_aspected_by: List[str] = []
    if dk_sign is not None:
        for planet, row in ps.items():
            if not isinstance(row, dict):
                continue
            if _sign_aspects(row.get("s"), dk_sign):
                dk_aspected_by.append(str(planet))

    ul_sign = (jp.get("UL") or {}).get("s")
    ul2_sign = ((int(ul_sign) % 12) + 1) if isinstance(ul_sign, int) else None
    al_sign = (jp.get("AL") or {}).get("s")
    al10_sign = ((int(al_sign) + 8) % 12) + 1 if isinstance(al_sign, int) else None
    kl_sign = (jp.get("KL") or {}).get("s")
    kl10_sign = ((int(kl_sign) + 8) % 12) + 1 if isinstance(kl_sign, int) else None

    out: Dict[str, Any] = {
        "md": md_sign,
        "ad": ad_sign,
        "rf": refs,
        "kr": karakas,
        "dk_asp": dk_aspected_by,
        "amk_ak": _ak_amk_connection(ck),
        "ag7": (ag.get("7") or {}).get("g"),
    }

    if ul2_sign is not None:
        out["ul2"] = {"s": ul2_sign, "pp": _occupants_of_sign(ps, ul2_sign)}
    if al10_sign is not None:
        out["al10"] = {"s": al10_sign, "pp": _occupants_of_sign(ps, al10_sign)}
    if kl10_sign is not None:
        out["kl10"] = {"s": kl10_sign, "pp": _occupants_of_sign(ps, kl10_sign)}
    out["career"] = _build_jaimini_career_payload(jp, ck, out)
    out["relationship"] = _build_jaimini_relationship_payload(jp, ck, out)
    return out


def _nadi_link_score(row: Dict[str, Any]) -> int:
    if not isinstance(row, dict):
        return 0
    return (
        len(row.get("t") or []) * 3
        + len(row.get("o") or []) * 2
        + len(row.get("f") or [])
        + len(row.get("b") or [])
        + (1 if row.get("rv") else 0)
        + (1 if row.get("ex") else 0)
    )


def _nadi_top_planets(lk: Dict[str, Any], planets: Optional[tuple[str, ...]] = None, limit: int = 5) -> List[Dict[str, Any]]:
    chosen = planets or tuple(lk.keys())
    rows: List[Dict[str, Any]] = []
    for planet in chosen:
        row = lk.get(planet)
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "p": planet,
                "sc": _nadi_link_score(row),
                "rv": bool(row.get("rv")),
                "ex": bool(row.get("ex")),
                "ln": {
                    "t": len(row.get("t") or []),
                    "f": len(row.get("f") or []),
                    "b": len(row.get("b") or []),
                    "o": len(row.get("o") or []),
                },
            }
        )
    rows.sort(key=lambda item: (-int(item["sc"]), str(item["p"])))
    return rows[:limit]


def _nadi_tag_scores(planets: List[Dict[str, Any]]) -> List[str]:
    scores: Dict[str, int] = {}
    for row in planets:
        for tag in _PLANET_FUNCTION_TAGS.get(str(row.get("p")), []):
            scores[tag] = scores.get(tag, 0) + int(row.get("sc") or 0)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [tag for tag, _score in ranked[:4]]


def _nadi_age_hits(aa: Dict[str, Any], allowed: tuple[str, ...]) -> List[str]:
    hits: List[str] = []
    for row in (aa.get("pl") or []):
        if not isinstance(row, dict):
            continue
        p = str(row.get("p") or "")
        if p and p in allowed:
            hits.append(p)
    return sorted(set(hits))


def _nadi_age_hit_rows(aa: Dict[str, Any], allowed: tuple[str, ...]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for row in (aa.get("pl") or []):
        if not isinstance(row, dict):
            continue
        p = str(row.get("p") or "")
        if p and p in allowed:
            hits.append({k: row.get(k) for k in ("p", "n", "h") if row.get(k) is not None})
    hits.sort(key=lambda item: (str(item.get("p") or ""), str(item.get("n") or "")))
    return hits


def _nadi_signatures(dom: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = {str(row.get("p")): int(row.get("sc") or 0) for row in dom if row.get("p")}
    hits: List[Dict[str, Any]] = []
    for pair, meta in _NADI_SIGNATURES.items():
        p1, p2 = pair
        if p1 not in ranked or p2 not in ranked:
            continue
        hits.append(
            {
                "p": [p1, p2],
                "topic": meta["topic"],
                "tone": meta["tone"],
                "txt": meta["txt"],
                "sc": ranked[p1] + ranked[p2],
            }
        )
    hits.sort(key=lambda item: (-int(item["sc"]), str(item["tone"])))
    return hits[:4]


def _build_nadi_career_payload(lk: Dict[str, Any], aa: Dict[str, Any]) -> Dict[str, Any]:
    dom = _nadi_top_planets(lk, _NADI_CAREER_PLANETS, limit=4)
    tags = _nadi_tag_scores(dom)
    hits = _nadi_age_hits(aa, _NADI_CAREER_PLANETS)
    hit_rows = _nadi_age_hit_rows(aa, _NADI_CAREER_PLANETS)
    sig = [row for row in _nadi_signatures(dom) if row.get("topic") == "career"]
    lead = tags[0] if tags else "mixed"
    if len(tags) >= 2 and dom and len(dom) > 1 and abs(int(dom[0]["sc"]) - int(dom[1]["sc"])) <= 2:
        lead = "mixed"
    return {
        "dom": dom,
        "tags": tags,
        "sig": sig,
        "lead": lead,
        "aa": hits,
        "aa_pl": hit_rows,
    }


def _build_nadi_relationship_payload(lk: Dict[str, Any], aa: Dict[str, Any]) -> Dict[str, Any]:
    dom = _nadi_top_planets(lk, _NADI_REL_PLANETS, limit=5)
    hits = _nadi_age_hits(aa, _NADI_REL_PLANETS)
    hit_rows = _nadi_age_hit_rows(aa, _NADI_REL_PLANETS)
    planets = {str(row.get("p")) for row in dom}
    flags: List[str] = []
    if "Venus" in planets or "Jupiter" in planets:
        flags.append("support")
    if "Saturn" in planets:
        flags.append("delay")
    if "Rahu" in planets or "Ketu" in planets:
        flags.append("karmic")
    if "Mars" in planets:
        flags.append("friction")
    if not flags:
        flags.append("mixed")
    return {
        "dom": dom,
        "aa": hits,
        "aa_pl": hit_rows,
        "flags": flags,
        "sig": [row for row in _nadi_signatures(dom) if row.get("topic") == "relationship"],
        "lead": flags[0],
    }


def _build_nadi_wealth_payload(lk: Dict[str, Any], aa: Dict[str, Any]) -> Dict[str, Any]:
    dom = _nadi_top_planets(lk, _NADI_WEALTH_PLANETS, limit=4)
    tags = _nadi_tag_scores(dom)
    return {
        "dom": dom,
        "tags": tags,
        "sig": [row for row in _nadi_signatures(dom) if row.get("topic") == "wealth"],
        "aa": _nadi_age_hits(aa, _NADI_WEALTH_PLANETS),
        "aa_pl": _nadi_age_hit_rows(aa, _NADI_WEALTH_PLANETS),
        "lead": tags[0] if tags else "mixed",
    }


def _build_nadi_health_payload(lk: Dict[str, Any], aa: Dict[str, Any]) -> Dict[str, Any]:
    dom = _nadi_top_planets(lk, _NADI_HEALTH_PLANETS, limit=4)
    planets = {str(row.get("p")) for row in dom}
    flags: List[str] = []
    if "Saturn" in planets:
        flags.append("chronic")
    if "Mars" in planets:
        flags.append("acute")
    if "Rahu" in planets or "Ketu" in planets:
        flags.append("irregular")
    if "Moon" in planets:
        flags.append("sensitive")
    if not flags:
        flags.append("mixed")
    systems: List[str] = []
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        if planet in planets and planet in _HEALTH_PLANET_SYSTEMS:
            systems.append(_HEALTH_PLANET_SYSTEMS[planet])
    return {
        "dom": dom,
        "flags": flags,
        "sig": [row for row in _nadi_signatures(dom) if row.get("topic") == "health"],
        "aa": _nadi_age_hits(aa, _NADI_HEALTH_PLANETS),
        "aa_pl": _nadi_age_hit_rows(aa, _NADI_HEALTH_PLANETS),
        "lead": flags[0],
        "systems": systems[:4],
    }


def _build_nadi_derived_payload(agent_ctx: AgentContext, nadi: Dict[str, Any]) -> Dict[str, Any]:
    ir = agent_ctx.intent_result if isinstance(agent_ctx.intent_result, dict) else {}
    cat = str(ir.get("category") or "general")
    lk = nadi.get("LK") or {}
    aa = nadi.get("AA") or {}
    aa_block = {
        "y": aa.get("y"),
        "k": list(aa.get("k") or []),
        "pl": list(aa.get("pl") or []),
    } if isinstance(aa, dict) and aa else {}
    top = _nadi_top_planets(lk, None, limit=5)
    out: Dict[str, Any] = {
        "top": top,
        "sig": _nadi_signatures(top),
        "aa": aa_block,
        "career": _build_nadi_career_payload(lk, aa if isinstance(aa, dict) else {}),
        "relationship": _build_nadi_relationship_payload(lk, aa if isinstance(aa, dict) else {}),
        "wealth": _build_nadi_wealth_payload(lk, aa if isinstance(aa, dict) else {}),
    }
    if _is_health_category(cat):
        out["health"] = _build_nadi_health_payload(lk, aa if isinstance(aa, dict) else {})
    return out


def _support_band(rel: Any, *, supportive: set[int], obstructive: set[int]) -> str:
    try:
        house = int(rel)
    except (TypeError, ValueError):
        return "unknown"
    if house in supportive:
        return "supportive"
    if house in obstructive:
        return "obstructed"
    return "mixed"


def _build_jaimini_career_payload(jp: Dict[str, Any], ck: Dict[str, Any], jx: Dict[str, Any]) -> Dict[str, Any]:
    kr = jx.get("kr") or {}
    rf = jx.get("rf") or {}
    md_amk = (kr.get("AmK") or {}).get("md")
    ad_amk = (kr.get("AmK") or {}).get("ad")
    md_kl = (rf.get("KL") or {}).get("md")
    ad_kl = (rf.get("KL") or {}).get("ad")
    md_al = (rf.get("AL") or {}).get("md")
    ad_al = (rf.get("AL") or {}).get("ad")
    return {
        "amk": (ck.get("AmK") or {}).get("s"),
        "kl": (jp.get("KL") or {}).get("s"),
        "al": (jp.get("AL") or {}).get("s"),
        "rf": {
            "amk": {"md": md_amk, "ad": ad_amk},
            "kl": {"md": md_kl, "ad": ad_kl},
            "al": {"md": md_al, "ad": ad_al},
        },
        "md": _support_band(md_amk, supportive={1, 2, 3, 5, 6, 9, 10, 11}, obstructive={8, 12}),
        "ad": _support_band(ad_amk, supportive={1, 2, 3, 5, 6, 9, 10, 11}, obstructive={8, 12}),
        "img": {
            "al10": (jx.get("al10") or {}).get("pp", []),
            "kl10": (jx.get("kl10") or {}).get("pp", []),
        },
        "amk_ak": jx.get("amk_ak"),
    }


def _build_jaimini_relationship_payload(jp: Dict[str, Any], ck: Dict[str, Any], jx: Dict[str, Any]) -> Dict[str, Any]:
    rf = jx.get("rf") or {}
    kr = jx.get("kr") or {}
    a7_occ = ((jp.get("A7") or {}).get("pp") or [])
    ul_occ = ((jp.get("UL") or {}).get("pp") or [])
    ul2_occ = ((jx.get("ul2") or {}).get("pp") or [])
    return {
        "dk": (ck.get("DK") or {}).get("s"),
        "ul": (jp.get("UL") or {}).get("s"),
        "a7": (jp.get("A7") or {}).get("s"),
        "rf": {
            "dk": (kr.get("DK") or {}),
            "ul": (rf.get("UL") or {}),
            "a7": (rf.get("A7") or {}),
        },
        "md": _support_band((rf.get("A7") or {}).get("md"), supportive={1, 2, 5, 7, 9, 11}, obstructive={6, 8, 12}),
        "ad": _support_band((rf.get("A7") or {}).get("ad"), supportive={1, 2, 5, 7, 9, 11}, obstructive={6, 8, 12}),
        "gk_a7": "GK" in a7_occ,
        "mal_a7": [p for p in a7_occ if p in _MALEFICS],
        "ben_a7": [p for p in a7_occ if p in _BENEFICS],
        "ul_pp": ul_occ,
        "ul2_pp": ul2_occ,
        "ct": "obstructed" if len([p for p in ul2_occ if p in _MALEFICS]) > len([p for p in ul2_occ if p in _BENEFICS]) else "supportive" if ul2_occ else "unknown",
    }


def build_jaimini_agent_payload(agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    """Jaimini static bundle + Chara Dasha timing spine."""
    jaimini = build_agent("jaimini", agent_ctx)
    chara_dasha = build_agent("chara_dasha", agent_ctx)
    return {
        "jaimini": jaimini,
        "chara_dasha": chara_dasha,
        "jx": _build_jaimini_derived_payload(jaimini, chara_dasha),
        "user_question": user_question,
    }


def build_nakshatra_agent_payload(agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    """Nakshatra + Vimshottari spine (MD/AD for NK pillar); compact agent JSON only."""
    return {
        "nakshatra": build_agent("nakshatra", agent_ctx),
        "vim_dasha": build_agent("vim_dasha", agent_ctx),
        "user_question": user_question,
    }


def build_kp_agent_payload(agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    """KP + Vimshottari spine for dasha trigger step."""
    return {
        "kp": build_agent("kp", agent_ctx),
        "vim_dasha": build_agent("vim_dasha", agent_ctx),
        "user_question": user_question,
    }


def _av_strength_band(sav: Any) -> str:
    try:
        s = int(sav)
    except (TypeError, ValueError):
        return "unknown"
    if s >= 30:
        return "strong"
    if s >= 25:
        return "workable"
    return "weak"


def _av_house_rows(av: Dict[str, Any], houses: List[int], planets: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    ho = ((av.get("D1") or {}).get("Ho") or {}) if isinstance(av, dict) else {}
    rows: List[Dict[str, Any]] = []
    for house in houses:
        row = ho.get(str(house))
        if not isinstance(row, dict):
            continue
        bmap = row.get("B") or {}
        bp = {}
        for planet, val in (bmap.items() if isinstance(bmap, dict) else []):
            if planets is None or str(planet) in planets:
                try:
                    bp[str(planet)] = int(val)
                except (TypeError, ValueError):
                    continue
        rows.append(
            {
                "h": int(house),
                "z": row.get("z"),
                "zn": row.get("zn"),
                "s": int(row.get("s") or 0),
                "band": _av_strength_band(row.get("s")),
                "bp": bp,
            }
        )
    rows.sort(key=lambda item: (-int(item.get("s") or 0), int(item.get("h") or 99)))
    return rows


def _av_d9_house_rows(av: Dict[str, Any], houses: List[int], planets: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    d9 = (av.get("D9") or {}) if isinstance(av, dict) else {}
    ho9 = d9.get("Ho9") or {}
    rows: List[Dict[str, Any]] = []
    if not isinstance(ho9, dict):
        return rows
    for house in houses:
        row = ho9.get(str(house))
        if not isinstance(row, dict):
            continue
        bmap = row.get("B") or {}
        bp = {}
        for planet, val in (bmap.items() if isinstance(bmap, dict) else []):
            if planets is None or str(planet) in planets:
                try:
                    bp[str(planet)] = int(val)
                except (TypeError, ValueError):
                    continue
        try:
            s = int(row.get("s") or 0)
        except (TypeError, ValueError):
            s = 0
        rows.append(
            {
                "h": int(house),
                "z": row.get("z"),
                "zn": row.get("zn"),
                "s": s,
                "band": _av_strength_band(s),
                "bp": bp,
            }
        )
    rows.sort(key=lambda item: (-int(item.get("s") or 0), int(item.get("h") or 99)))
    return rows


def _av_top_weak_houses(av: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    ho = ((av.get("D1") or {}).get("Ho") or {}) if isinstance(av, dict) else {}
    rows: List[Dict[str, Any]] = []
    for hk, row in ho.items() if isinstance(ho, dict) else []:
        if not isinstance(row, dict):
            continue
        try:
            h = int(hk)
            s = int(row.get("s") or 0)
        except (TypeError, ValueError):
            continue
        rows.append({"h": h, "z": row.get("z"), "zn": row.get("zn"), "s": s, "band": _av_strength_band(s)})
    top = sorted(rows, key=lambda item: (-int(item["s"]), int(item["h"])))[:4]
    weak = sorted(rows, key=lambda item: (int(item["s"]), int(item["h"])))[:4]
    return top, weak


def _av_dasha_rows(vim: Dict[str, Any], av: Dict[str, Any], houses: List[int]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    d = (vim.get("D") or {}) if isinstance(vim, dict) else {}
    house_rows = _av_house_rows(av, houses)
    for level in ("md", "ad", "pd"):
        row = d.get(level) or {}
        planet = row.get("p")
        if not planet:
            continue
        rel = []
        for hrow in house_rows:
            bp = (hrow.get("bp") or {}).get(str(planet))
            rel.append(
                {
                    "h": hrow.get("h"),
                    "s": hrow.get("s"),
                    "band": hrow.get("band"),
                    "b": bp,
                    "b_band": "blocked" if isinstance(bp, int) and bp < 3 else "supportive" if isinstance(bp, int) and bp >= 5 else "mixed" if isinstance(bp, int) else "unknown",
                }
            )
        out[level] = {"p": planet, "rows": rel}
    return out


def _av_conflicts(topic_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    for row in topic_rows:
        house = row.get("h")
        sav = row.get("s")
        for planet, bav in (row.get("bp") or {}).items():
            try:
                b = int(bav)
                s = int(sav)
            except (TypeError, ValueError):
                continue
            if s >= 28 and b < 3:
                conflicts.append({"h": house, "p": planet, "kind": "strong_house_weak_planet", "s": s, "b": b})
            elif s <= 24 and b >= 5:
                conflicts.append({"h": house, "p": planet, "kind": "weak_house_supported_planet", "s": s, "b": b})
    return conflicts[:10]


def _av_transit_rows(av: Dict[str, Any], vim: Dict[str, Any], topic_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    d = (vim.get("D") or {}) if isinstance(vim, dict) else {}
    pd_planet = str((d.get("pd") or {}).get("p") or "").strip()
    if not pd_planet:
        pd_planet = str((d.get("ad") or {}).get("p") or "").strip()
    out_rows: List[Dict[str, Any]] = []
    for row in topic_rows:
        bp = row.get("bp") if isinstance(row, dict) else {}
        b = bp.get(pd_planet) if isinstance(bp, dict) and pd_planet else None
        b_band = (
            "blocked"
            if isinstance(b, int) and b < 3
            else "supportive"
            if isinstance(b, int) and b >= 5
            else "mixed"
            if isinstance(b, int)
            else "unknown"
        )
        out_rows.append(
            {
                "h": row.get("h"),
                "s": row.get("s"),
                "s_band": row.get("band"),
                "b": b,
                "b_band": b_band,
            }
        )
    cluster = sorted(out_rows, key=lambda item: (-int(item.get("s") or 0), int(item.get("h") or 99)))
    return {
        "event_planet": pd_planet or None,
        "rows": out_rows,
        "best": cluster[:2],
        "hard": sorted(out_rows, key=lambda item: (int(item.get("s") or 0), int(item.get("h") or 99)))[:2],
    }


def build_ashtakavarga_agent_payload(agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    av = build_agent("ashtakavarga", agent_ctx)
    vim = build_agent("vim_dasha", agent_ctx)
    topic = _topic_meta(agent_ctx)
    hs = list(topic["hs"])
    naturals = {
        "marriage": ["Venus", "Jupiter", "Saturn"],
        "relationship": ["Venus", "Jupiter", "Saturn"],
        "love": ["Venus", "Moon", "Mars"],
        "career": ["Sun", "Mercury", "Saturn", "Jupiter", "Mars"],
        "job": ["Sun", "Mercury", "Saturn", "Jupiter", "Mars"],
        "promotion": ["Sun", "Mercury", "Saturn", "Jupiter"],
        "business": ["Mercury", "Venus", "Saturn", "Jupiter"],
        "wealth": ["Jupiter", "Venus", "Mercury"],
        "money": ["Jupiter", "Venus", "Mercury"],
        "finance": ["Jupiter", "Venus", "Mercury"],
        "health": ["Sun", "Moon", "Mars", "Saturn"],
        "disease": ["Sun", "Moon", "Mars", "Saturn"],
        "education": ["Mercury", "Jupiter", "Moon"],
        "child": ["Jupiter", "Sun", "Moon"],
        "children": ["Jupiter", "Sun", "Moon"],
        "pregnancy": ["Jupiter", "Moon", "Venus"],
        "property": ["Moon", "Mars", "Venus"],
        "home": ["Moon", "Mars", "Venus"],
    }
    cat = str(topic["cat"] or "general")
    topic_rows = _av_house_rows(av, hs, planets=naturals.get(cat))
    topic_rows_d9 = _av_d9_house_rows(av, hs, planets=naturals.get(cat))
    top, weak = _av_top_weak_houses(av)
    support_score = sum(1 for row in topic_rows if row.get("band") == "strong")
    weak_score = sum(1 for row in topic_rows if row.get("band") == "weak")
    support = "supportive" if support_score > weak_score else "obstructed" if weak_score > support_score else "mixed"
    ax = {
        "cat": cat,
        "hs": hs,
        "top": top,
        "weak": weak,
        "topic": {
            "rows": topic_rows,
            "rows_d9": topic_rows_d9,
            "support": support,
        },
        "dasha": _av_dasha_rows(vim, av, hs),
        "transit": _av_transit_rows(av, vim, topic_rows),
        "conflicts": _av_conflicts(topic_rows),
    }
    return {"ashtakavarga": av, "vim_dasha": vim, "ax": ax, "user_question": user_question}


def build_all_parallel_agent_payloads(
    agent_ctx: AgentContext,
    user_question: str,
    merged_chart_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return branch_label -> VARIABLE_DATA_JSON dict for specialist branches (Sudarshan payload is built in orchestrator from merged context)."""
    return {
        "parashari": build_parashari_agent_payload(
            agent_ctx, user_question, merged_chart_context=merged_chart_context
        ),
        "jaimini": build_jaimini_agent_payload(agent_ctx, user_question),
        "nadi": build_nadi_agent_payload(agent_ctx, user_question),
        "nakshatra": build_nakshatra_agent_payload(agent_ctx, user_question),
        "kp": build_kp_agent_payload(agent_ctx, user_question),
        "ashtakavarga": build_ashtakavarga_agent_payload(agent_ctx, user_question),
    }
