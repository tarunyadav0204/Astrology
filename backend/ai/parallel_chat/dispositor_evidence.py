"""Compact dispositor evidence for Parashari chat reasoning.

The helpers here intentionally stay small and data-only. They expose the
sign-lord "host" of planets that matter for the current question so branch and
merge prompts can cite dispositors without inventing chart facts.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

SIGN_LORDS_1_12: Dict[int, str] = {
    1: "Mars",
    2: "Venus",
    3: "Mercury",
    4: "Moon",
    5: "Sun",
    6: "Mercury",
    7: "Venus",
    8: "Mars",
    9: "Jupiter",
    10: "Saturn",
    11: "Saturn",
    12: "Jupiter",
}


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _unique(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for value in values:
        s = str(value or "").strip()
        if s and s not in out:
            out.append(s)
    return out


def _band_from_graha(row: Dict[str, Any], own_sign: bool) -> str:
    if own_sign:
        return "self-ruled"
    dignity = str(row.get("d") or "").strip().lower()
    score = row.get("sc")
    try:
        score_f = float(score)
    except (TypeError, ValueError):
        score_f = None
    if dignity in {"exalted", "own", "moolatrikona"} or (score_f is not None and score_f >= 65):
        return "supportive"
    if dignity in {"debilitated", "enemy", "great enemy"} or (score_f is not None and score_f < 40):
        return "weak"
    return "mixed"


def _legacy_graha_row(planet: str, planetary_analysis: Dict[str, Any]) -> Dict[str, Any]:
    row = planetary_analysis.get(planet) if isinstance(planetary_analysis, dict) else {}
    if not isinstance(row, dict):
        return {}
    basic = row.get("basic_info") or {}
    dignity = row.get("dignity_analysis") or {}
    combust = row.get("combustion_status") or {}
    overall = row.get("overall_assessment") or {}
    return {
        "d": dignity.get("dignity"),
        "fn": dignity.get("functional_nature"),
        "av": basic.get("avastha"),
        "sc": overall.get("overall_strength_score"),
        "cb": combust.get("is_combust"),
    }


def _planet_row(
    planet: str,
    planets: Dict[str, Dict[str, Any]],
    lordships: Dict[str, List[int]],
    graha: Dict[str, Any],
) -> Dict[str, Any]:
    p = planets.get(planet) or {}
    row: Dict[str, Any] = {
        "p": planet,
        "s": p.get("s"),
        "sn": p.get("sn"),
        "h": p.get("h"),
        "rh": lordships.get(planet) or [],
    }
    grow = graha.get(planet) if isinstance(graha, dict) else {}
    if isinstance(grow, dict):
        for key in ("d", "fn", "av", "sc", "cb"):
            if grow.get(key) is not None and grow.get(key) != "":
                row[key] = grow.get(key)
    return row


def _dispositor_chain(planet: str, planets: Dict[str, Dict[str, Any]], max_steps: int = 4) -> List[str]:
    chain = [planet]
    current = planet
    seen = {planet}
    for _ in range(max_steps):
        sign = _safe_int((planets.get(current) or {}).get("s"))
        if not sign:
            break
        dispositor = SIGN_LORDS_1_12.get(sign)
        if not dispositor:
            break
        chain.append(dispositor)
        if dispositor in seen:
            break
        seen.add(dispositor)
        current = dispositor
    return chain


def build_dispositor_evidence(
    *,
    planets: Dict[str, Dict[str, Any]],
    lordships: Dict[str, List[int]],
    graha: Dict[str, Any],
    topic_houses: List[int],
    active_levels: Dict[str, str],
) -> Dict[str, Any]:
    """Build compact dispositor rows for active dasha and topic planets.

    `planets` must use sign numbers 1-12. `active_levels` is level -> planet.
    """
    if not planets:
        return {}
    house_lords: Dict[int, str] = {}
    for planet, houses in (lordships or {}).items():
        if not isinstance(houses, list):
            continue
        for house in houses:
            h = _safe_int(house)
            if h:
                house_lords[h] = str(planet)

    topic_set = {int(h) for h in topic_houses if _safe_int(h)}
    topic_lords = _unique(house_lords.get(h) for h in topic_houses)
    topic_occupants = _unique(
        planet for planet, row in planets.items() if _safe_int(row.get("h")) in topic_set
    )
    active_planets = _unique(active_levels.values())
    selected = _unique(active_planets + topic_lords + topic_occupants)

    rows: List[Dict[str, Any]] = []
    controller_counts: Dict[str, int] = {}
    for planet in selected:
        base = _planet_row(planet, planets, lordships, graha)
        sign = _safe_int(base.get("s"))
        dispositor = SIGN_LORDS_1_12.get(sign) if sign else None
        if not dispositor:
            continue
        drow = _planet_row(dispositor, planets, lordships, graha)
        own_sign = dispositor == planet
        controller_counts[dispositor] = controller_counts.get(dispositor, 0) + 1
        row: Dict[str, Any] = {
            "p": planet,
            "h": base.get("h"),
            "s": base.get("s"),
            "sn": base.get("sn"),
            "rh": base.get("rh") or [],
            "disp": dispositor,
            "disp_h": drow.get("h"),
            "disp_s": drow.get("s"),
            "disp_sn": drow.get("sn"),
            "disp_rh": drow.get("rh") or [],
            "band": _band_from_graha(drow, own_sign),
            "chain": _dispositor_chain(planet, planets),
        }
        for src, dst in (("d", "disp_d"), ("fn", "disp_fn"), ("av", "disp_av"), ("sc", "disp_sc"), ("cb", "disp_cb")):
            if drow.get(src) is not None and drow.get(src) != "":
                row[dst] = drow.get(src)
        levels = [level for level, p in active_levels.items() if p == planet]
        if levels:
            row["levels"] = levels
        lord_of = sorted([h for h, p in house_lords.items() if p == planet and h in topic_set])
        if lord_of:
            row["lord_of_topic_houses"] = lord_of
        if _safe_int(base.get("h")) in topic_set:
            row["occupies_topic_house"] = base.get("h")
        rows.append(row)

    rows.sort(
        key=lambda r: (
            0 if r.get("levels") else 1 if r.get("lord_of_topic_houses") else 2,
            str(r.get("p") or ""),
        )
    )
    controllers = sorted(controller_counts.items(), key=lambda item: (-item[1], item[0]))
    return {
        "topic_houses": list(topic_houses),
        "active_levels": active_levels,
        "topic_lords": topic_lords,
        "topic_occupants": topic_occupants,
        "rows": rows[:12],
        "dominant_dispositors": [{"p": p, "n": n} for p, n in controllers[:5]],
        "rule": "A planet delivers through the lord of the sign it occupies; use this as a delivery/support layer, not a standalone override.",
    }


def compact_planets_from_core(core: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[int]]]:
    planets: Dict[str, Dict[str, Any]] = {}
    for row in core.get("P") or []:
        if not isinstance(row, list) or len(row) < 5:
            continue
        sign = _safe_int(row[2])
        house = _safe_int(row[4])
        if sign is None:
            continue
        planets[str(row[0])] = {"s": sign, "sn": str(row[3]), "h": house}
    lordships = core.get("H") or {}
    return planets, lordships if isinstance(lordships, dict) else {}


def legacy_planets_from_context(context: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[int]], Dict[str, Any]]:
    chart = context.get("d1_chart") or {}
    planets: Dict[str, Dict[str, Any]] = {}
    for planet, row in (chart.get("planets") or {}).items():
        if not isinstance(row, dict):
            continue
        sign0 = _safe_int(row.get("sign"))
        house = _safe_int(row.get("house"))
        if sign0 is None:
            continue
        planets[str(planet)] = {
            "s": sign0 + 1,
            "sn": row.get("sign_name"),
            "h": house,
        }
    lordships = context.get("house_lordships") or {}
    planetary_analysis = context.get("planetary_analysis") or {}
    graha = {planet: _legacy_graha_row(planet, planetary_analysis) for planet in planets}
    return planets, lordships if isinstance(lordships, dict) else {}, graha
