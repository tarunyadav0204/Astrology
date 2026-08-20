"""Build the user-facing chain that explains how an Instant answer was derived.

This is intentionally separate from the LLM composer brief and the technical
ledger. It exposes calculated facts in the reasoning order a user can follow:
event framework -> natal permission -> dasha delivery -> transit confirmation
-> conclusion.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


HOUSE_MEANINGS = {
    1: "self, initiative and visibility",
    2: "income, family, speech and accumulated resources",
    3: "effort, communication and initiative",
    4: "home, stability and emotional security",
    5: "creativity, children, romance and learning",
    6: "work, service, competition and daily responsibilities",
    7: "partnership, spouse, clients and agreements",
    8: "trust, intimacy, shared obligations and transformation",
    9: "fortune, mentors and opportunity",
    10: "career, authority, role and status",
    11: "gains, support, networks and fulfilment",
    12: "expenses, distance, privacy and release",
}

TOPIC_HOUSE_MEANINGS = {
    "relationship": {
        2: "family expectations, speech and shared values",
        5: "affection, romance and emotional expression",
        7: "commitment, partnership and mutual agreements",
        11: "shared goals, support and social connections",
    },
    "marriage": {
        2: "family formation, speech and shared values",
        5: "affection, romance and emotional bonding",
        7: "marriage, spouse and committed partnership",
        11: "fulfilment, support and shared goals",
    },
    "promotion": {
        2: "salary, compensation and financial advancement",
        6: "work, service, competition and responsibility",
        10: "promotion, authority, role and professional status",
        11: "gains, recognition, networks and goal fulfilment",
    },
    "career": {
        2: "income, compensation and resource decisions",
        6: "workload, service, deadlines and competition",
        10: "role, authority, status and visible responsibility",
        11: "gains, recognition, networks and goal fulfilment",
    },
    "wealth": {
        2: "income, savings and family resources",
        5: "investment judgment and calculated risk",
        9: "long-range financial support and guidance",
        11: "gains, collections and financial goals",
    },
}


def _house_meaning(event_key: str, number: int) -> str:
    return TOPIC_HOUSE_MEANINGS.get(event_key, {}).get(
        number,
        HOUSE_MEANINGS.get(number, "this life area"),
    )

DOMAIN_HOUSES = {
    "career": ([10, 6, 11, 2], []),
    "promotion": ([10, 11, 2], [6]),
    "marriage": ([7, 2, 11], [5]),
    "relationship": ([7, 5, 11, 2], []),
    "wealth": ([2, 11, 5, 9], [10]),
    "business": ([7, 10, 11, 2], []),
    "progeny": ([5, 2, 11], [9]),
    "property": ([4, 2, 11, 12], [9]),
    "education": ([4, 5, 9, 11, 2], []),
    "foreign": ([3, 7, 9, 12], [11]),
}

def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _house(value: Any) -> int | None:
    try:
        number = int(value)
        return number if 1 <= number <= 12 else None
    except (TypeError, ValueError):
        return None


def _event_key(query_plan: Dict[str, Any], instant_context: Dict[str, Any]) -> str:
    normalized = _dict(instant_context.get("normalized_evidence"))
    timing = _dict(normalized.get("event_timing_verdict"))
    label = str(timing.get("event_category") or timing.get("answer_event_label") or "").lower()
    category = str(query_plan.get("category") or "general").lower()
    question = str(query_plan.get("question") or "").lower()
    # Presentation fallback for a router that returned broad `career` while the
    # already-resolved user goal explicitly names promotion.
    if category == "career" and re.search(r"\bpromot(?:e|ed|ion)\b|पदोन्नति", question):
        return "promotion"
    return label if label in DOMAIN_HOUSES else category


def _house_rows(event_key: str, focus_houses: Iterable[Any]) -> List[Dict[str, Any]]:
    primary, support = DOMAIN_HOUSES.get(event_key, ([], []))
    if not primary:
        primary = [h for h in (_house(item) for item in focus_houses) if h]
    rows: List[Dict[str, Any]] = []
    for number in [*primary, *support]:
        if number and all(row["house"] != number for row in rows):
            rows.append({
                "house": number,
                "role": "supporting" if number in support else "primary",
                "meaning": _house_meaning(event_key, number),
            })
    return rows


def _container_segments(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        return [row for row in _list(value.get("segments")) if isinstance(row, dict)]
    return []


def _selected_segments(query_plan: Dict[str, Any], instant_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    parashari = _dict(instant_context.get("instant_parashari"))
    normalized = _dict(instant_context.get("normalized_evidence"))
    mode = str(query_plan.get("answer_mode") or "")

    def window_rows(owner: Dict[str, Any]) -> List[Dict[str, Any]]:
        return _container_segments(owner.get("window_dasha_segments"))

    def horizon_rows(owner: Dict[str, Any]) -> List[Dict[str, Any]]:
        return _container_segments(owner.get("horizon_dasha_segments"))

    def forward_rows(owner: Dict[str, Any]) -> List[Dict[str, Any]]:
        value = _dict(owner.get("forward_event_dasha_scan"))
        return [row for row in _list(value.get("periods")) if isinstance(row, dict)]

    # Prefer the source appropriate to the question shape, but fall through on
    # an empty container. Several timing aliases are emitted by the router.
    if mode in {"timing_window", "month_timing", "event_timing"}:
        sources = (
            window_rows(parashari), window_rows(normalized),
            forward_rows(parashari), forward_rows(normalized),
            horizon_rows(parashari), horizon_rows(normalized),
        )
    else:
        sources = (
            forward_rows(parashari), forward_rows(normalized),
            horizon_rows(parashari), horizon_rows(normalized),
            window_rows(parashari), window_rows(normalized),
        )
    candidates = next((rows for rows in sources if rows), [])
    candidates.sort(key=lambda row: str(row.get("start") or row.get("start_date") or ""))
    return candidates[:6]


def _split_reasons(value: Any, *, exclude_transits: bool = False) -> List[str]:
    reasons = [part.strip() for part in str(value or "").split(";") if part.strip()]
    if exclude_transits:
        reasons = [row for row in reasons if not row.lower().startswith("dated transit peak")]
    return reasons[:6]

def _segment_row(row: Dict[str, Any], event_key: str) -> Dict[str, Any]:
    activated = [h for h in (_house(item) for item in _list(row.get("activated_focus_houses"))) if h]
    carriers = []
    for carrier in _list(row.get("carrier_planets")):
        if not isinstance(carrier, dict):
            continue
        carriers.append({
            "planet": carrier.get("planet"),
            "dasha_levels": _list(carrier.get("dasha_levels") or carrier.get("levels")),
            "natal_placement_house": _house(
                carrier.get("natal_placement_house") or carrier.get("natal_house")
            ),
            "natal_event_houses": [
                h for h in (_house(item) for item in _list(carrier.get("natal_event_houses"))) if h
            ],
            "event_links": [
                {
                    "house": h,
                    "meaning": _house_meaning(event_key, h),
                    "mechanisms": _list(link.get("mechanisms")),
                }
                for link in _list(carrier.get("event_links"))
                if isinstance(link, dict) and (h := _house(link.get("house")))
            ],
        })
    return {
        "start": row.get("start") or row.get("start_date"),
        "end": row.get("end") or row.get("end_date"),
        "chain": "–".join(str(item) for item in (
            row.get("mahadasha"), row.get("antardasha"), row.get("pratyantardasha")
        ) if item),
        "strength": row.get("activation_strength") or row.get("period_strength"),
        "activated_houses": [
            {"house": h, "meaning": _house_meaning(event_key, h)} for h in activated
        ],
        "carriers": carriers,
        "reasons": _split_reasons(row.get("why"), exclude_transits=True),
        "result_areas": [
            item for item in _list(row.get("predicted_result_areas")) if isinstance(item, dict)
        ][:4],
    }


def _transit_rows(segments: List[Dict[str, Any]], normalized: Dict[str, Any],
                  event_key: str) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for segment in segments:
        candidates.extend(
            row for row in _list(segment.get("peak_activation_windows")) if isinstance(row, dict)
        )
    timeline = _dict(normalized.get("transit_activation_timeline"))
    candidates.extend(row for row in _list(timeline.get("peak_windows")) if isinstance(row, dict))
    seen = set()
    result = []
    for row in candidates:
        key = (row.get("start"), row.get("end"), row.get("planet"), row.get("why"))
        if key in seen:
            continue
        seen.add(key)
        delivered_rows = []
        for delivered in _list(row.get("delivered_event_houses")):
            if not isinstance(delivered, dict):
                continue
            house = _house(delivered.get("house"))
            if not house:
                continue
            delivered_rows.append({
                "house": house,
                "meaning": _house_meaning(event_key, house),
                "mechanism": delivered.get("mechanism"),
            })
        reasons = [
            reason for reason in _split_reasons(row.get("why"))
            if "delivers its natal dasha promise to event house" not in reason.lower()
        ]
        result.append({
            "start": row.get("start"),
            "end": row.get("end"),
            "planet": row.get("planet"),
            "dasha_levels": _list(row.get("dasha_levels")),
            "strength": row.get("strength"),
            "trigger_kinds": _list(row.get("trigger_kinds")),
            "transit_native_house": _house(row.get("transit_native_house")),
            "natal_placement_house": _house(row.get("natal_placement_house")),
            "delivered_event_houses": delivered_rows,
            "confirmed_houses": [
                {"house": h, "meaning": _house_meaning(event_key, h)}
                for h in (_house(item) for item in _list(row.get("carrier_event_houses"))) if h
            ],
            "reasons": reasons,
        })
        if len(result) >= 5:
            break
    return result


def build_user_derivation(*, query_plan: Dict[str, Any], verdict: Dict[str, Any],
                          instant_context: Dict[str, Any]) -> Dict[str, Any]:
    """Return calculated, display-ready derivation without changing the LLM prompt."""
    normalized = _dict(instant_context.get("normalized_evidence"))
    parashari = _dict(instant_context.get("instant_parashari"))
    promise = _dict(normalized.get("natal_promise"))
    event_key = _event_key(query_plan, instant_context)
    focus_houses = parashari.get("focus_houses") or _dict(instant_context.get("intent_summary")).get("focus_houses") or []
    raw_segments = _selected_segments(query_plan, instant_context)
    segments = [_segment_row(row, event_key) for row in raw_segments]
    segments = [row for row in segments if row.get("start") or row.get("chain") or row.get("reasons")]

    natal_basis: List[str] = []
    support = promise.get("topic_support") or promise.get("current_topic_support")
    if support:
        natal_basis.append(f"The {event_key} foundation is rated {str(support).replace('_', ' ')}.")
    for item in _list(normalized.get("divisional_specifics"))[:2]:
        if isinstance(item, str) and item.strip():
            natal_basis.append(item.strip())
    if not natal_basis and promise.get("status"):
        natal_basis.append("The topic-specific natal and divisional checks produced this promise status.")

    ranked = [row for row in _list(verdict.get("ranked_windows")) if isinstance(row, dict)]
    strongest = ranked[0] if ranked else (segments[-1] if segments else {})
    missing = _list(verdict.get("missing_required_capabilities"))
    return {
        "schema_version": "instant-user-derivation/v1",
        "event": {
            "key": event_key,
            "label": event_key.replace("_", " ").title(),
            "houses": _house_rows(event_key, focus_houses),
        },
        "natal_promise": {
            "status": promise.get("status") or "not_established",
            "basis": natal_basis,
        },
        "dasha_activation": segments,
        "transit_confirmation": _transit_rows(raw_segments, normalized, event_key),
        "conclusion": {
            "direction": verdict.get("direction"),
            "confidence": verdict.get("confidence"),
            "start": strongest.get("start"),
            "end": strongest.get("end"),
            "chain": strongest.get("chain"),
            "activated_houses": strongest.get("activated_focus_houses") or strongest.get("activated_houses") or [],
            "why": strongest.get("why") or strongest.get("reasons") or [],
        },
        "limitations": missing,
        "complete": bool(promise and segments),
    }
