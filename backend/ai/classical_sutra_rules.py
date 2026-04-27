"""Small deterministic matchers for classical rule context sent to chat LLMs."""

from __future__ import annotations

from typing import Any, Dict, List


_CATEGORY_TARGET_HOUSES: Dict[str, Dict[str, Any]] = {
    "career": {"house": 10, "label": "career/status"},
    "job": {"house": 10, "label": "job/service"},
    "promotion": {"house": 10, "label": "promotion/status"},
    "business": {"house": 7, "label": "business/marketplace"},
    "wealth": {"house": 2, "label": "wealth/resources"},
    "money": {"house": 2, "label": "money/resources"},
    "finance": {"house": 2, "label": "finance/resources"},
    "marriage": {"house": 7, "label": "marriage/partnership"},
    "relationship": {"house": 7, "label": "relationship/partnership"},
    "partner": {"house": 7, "label": "partner/spouse"},
    "spouse": {"house": 7, "label": "spouse/marriage"},
    "love": {"house": 5, "label": "love/romance"},
    "health": {"house": 6, "label": "health/disease"},
    "disease": {"house": 6, "label": "disease/health"},
    "education": {"house": 5, "label": "education/intelligence"},
    "learning": {"house": 5, "label": "learning/intelligence"},
    "property": {"house": 4, "label": "property/home"},
    "home": {"house": 4, "label": "home/domestic stability"},
    "children": {"house": 5, "label": "children/progeny"},
    "child": {"house": 5, "label": "child/progeny"},
    "pregnancy": {"house": 5, "label": "pregnancy/progeny"},
    "mother": {"house": 4, "label": "mother/home"},
    "father": {"house": 9, "label": "father/dharma"},
    "siblings": {"house": 3, "label": "siblings"},
    "travel": {"house": 9, "label": "travel/long journeys"},
    "foreign": {"house": 12, "label": "foreign/away-from-home matters"},
    "visa": {"house": 12, "label": "visa/foreign matters"},
}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _planet_house(row: Dict[str, Any]) -> int:
    return _as_int(row.get("house", row.get("h", 0)))


def _planet_sign(row: Dict[str, Any]) -> str:
    return str(row.get("sign_name") or row.get("sign") or row.get("s") or "").strip()


def _house_lords(house_lordships: Dict[str, Any], house: int) -> List[str]:
    lords: List[str] = []
    for planet, houses in (house_lordships or {}).items():
        if isinstance(houses, list) and house in {_as_int(h) for h in houses}:
            lords.append(str(planet))
    return lords


def _dasha_levels(current_dashas: Dict[str, Any], house_lordships: Dict[str, Any]) -> List[Dict[str, Any]]:
    levels: List[Dict[str, Any]] = []
    for key in ("mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana"):
        row = (current_dashas or {}).get(key)
        if isinstance(row, dict) and row.get("planet"):
            planet = str(row.get("planet") or "")
            ruled_houses = row.get("ruled_houses") or row.get("rules") or house_lordships.get(planet) or []
            levels.append(
                {
                    "level": key,
                    "planet": planet,
                    "house": row.get("house"),
                    "ruled_houses": ruled_houses,
                    "period": row.get("period") or row.get("end_date") or row.get("end"),
                }
            )
    return levels


def build_12th_from_house_rule_match(context: Dict[str, Any], intent: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Return one structured candidate for '12th from a house = investment/expense for that house'."""
    intent_block = intent if isinstance(intent, dict) else (context.get("intent") or {})
    category = str(intent_block.get("category") or "general").strip().lower()
    target = _CATEGORY_TARGET_HOUSES.get(category)
    if not target:
        return None

    target_house = _as_int(target.get("house"))
    if not 1 <= target_house <= 12:
        return None
    derived_house = ((target_house + 10) % 12) + 1

    d1_chart = context.get("d1_chart") or {}
    planets = d1_chart.get("planets") or {}
    house_lordships = context.get("house_lordships") or {}
    current_dashas = context.get("current_dashas") or {}

    derived_occupants: List[Dict[str, Any]] = []
    target_occupants: List[str] = []
    for planet, row in planets.items():
        if not isinstance(row, dict):
            continue
        house = _planet_house(row)
        if house == derived_house:
            derived_occupants.append({"planet": planet, "sign": _planet_sign(row) or None})
        if house == target_house:
            target_occupants.append(str(planet))

    derived_lords = _house_lords(house_lordships, derived_house)
    target_lords = _house_lords(house_lordships, target_house)
    derived_lord_rows = []
    for lord in derived_lords:
        row = planets.get(lord) if isinstance(planets, dict) else None
        if isinstance(row, dict):
            derived_lord_rows.append(
                {
                    "planet": lord,
                    "house": _planet_house(row) or None,
                    "sign": _planet_sign(row) or None,
                }
            )

    active_dasha_hits = []
    relevant_planets = {p["planet"] for p in derived_occupants}
    relevant_planets.update(derived_lords)
    relevant_planets.update(target_lords)
    for row in _dasha_levels(current_dashas, house_lordships):
        planet = str(row.get("planet") or "")
        ruled = {_as_int(h) for h in row.get("ruled_houses") or []}
        if planet in relevant_planets or target_house in ruled or derived_house in ruled:
            active_dasha_hits.append(row)

    evidence = []
    if derived_occupants:
        evidence.append("derived_house_occupied")
    if derived_lord_rows:
        evidence.append("derived_house_lord_available")
    if active_dasha_hits:
        evidence.append("current_dasha_links_rule")

    confidence = "medium"
    if len(evidence) >= 3:
        confidence = "high"
    elif len(evidence) <= 1:
        confidence = "low"

    return {
        "id": "derived_12th_from_topic_house",
        "title": "12th from a house shows expense, sacrifice, loss, or investment into that house",
        "status": "candidate",
        "confidence": confidence,
        "category": category,
        "topic_label": target.get("label"),
        "target_house": target_house,
        "derived_house": derived_house,
        "sutra": "For any target house H, the 12th counted from H shows what is spent, sacrificed, released, or invested for H.",
        "interpretive_frame": [
            "If supported by benefics/strong lord/dasha alignment, read it as constructive investment or service.",
            "If afflicted or unsupported, read it as leakage, conflict, debt, fatigue, or loss around the topic.",
        ],
        "evidence": {
            "target_house_occupants": target_occupants,
            "target_house_lords": target_lords,
            "derived_house_occupants": derived_occupants,
            "derived_house_lords": derived_lords,
            "derived_lord_placements": derived_lord_rows,
            "active_dasha_hits": active_dasha_hits,
            "activation_tags": evidence,
        },
    }


def build_classical_rule_matches(context: Dict[str, Any], intent: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Container shape for rule matches. Add future rules here without changing prompt contracts."""
    match = build_12th_from_house_rule_match(context, intent)
    matches = [match] if match else []
    return {
        "version": 1,
        "rules_enabled": ["derived_12th_from_topic_house"],
        "matches": matches,
        "usage_policy": (
            "Use these rule matches only as supporting evidence when they clarify the user's question. "
            "Do not force them into the answer if activation is weak or another branch gives stronger evidence."
        ),
    }
