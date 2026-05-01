from __future__ import annotations

from typing import Any, Dict, List


def _top_trigger_labels(ranked_triggers: List[Dict[str, Any]]) -> List[str]:
    labels: List[str] = []
    for row in ranked_triggers or []:
        level = str(row.get("level") or "")
        planet = str(row.get("planet") or "")
        strength = str(row.get("strength") or "")
        if not planet:
            continue
        bit = f"{level} {planet}".strip()
        if strength:
            bit = f"{bit} ({strength})"
        labels.append(bit)
    return labels[:4]


def _domain_labels(rows: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    for row in rows or []:
        domain = str(row.get("domain") or "").strip()
        if domain:
            out.append(domain)
    return out[:5]


def _window_labels(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows or []:
        out.append({
            "label": row.get("label"),
            "start": row.get("start"),
            "end": row.get("end"),
            "quality": row.get("quality"),
            "source": row.get("source"),
        })
    return out[:4]


def _transition_note(transition_windows: List[Dict[str, Any]]) -> str:
    if not transition_windows:
        return ""
    first = transition_windows[0]
    label = str(first.get("label") or "").strip()
    time_label = str(first.get("time_label") or "").strip()
    if label and time_label:
        return f"{label} around {time_label}"
    if label:
        return label
    return "The day changes character midstream."


def build_daily_output_contract(
    *,
    target_date: str,
    daily_prediction_spine: Dict[str, Any],
    daily_micro_intent: Dict[str, Any],
    daily_confidence: Dict[str, Any],
    intraday: Dict[str, Any],
) -> Dict[str, Any]:
    daily_judgment = daily_prediction_spine.get("daily_judgment") or {}
    ranked_triggers = daily_prediction_spine.get("ranked_triggers") or []
    favorable_windows = intraday.get("favorable_windows") or []
    caution_windows = intraday.get("caution_windows") or []
    transitions = intraday.get("transition_windows") or []
    best_for = list(daily_micro_intent.get("best_for") or [])[:3]
    watch_for = list(daily_micro_intent.get("watch_for") or [])[:3]
    support = list(daily_confidence.get("supporting_factors") or [])[:3]
    contradictions = list(daily_confidence.get("contradicting_factors") or [])[:3]

    verdict = str(daily_confidence.get("verdict") or "mixed")
    confidence = str(daily_confidence.get("confidence_band") or "guarded")
    day_shape = str(daily_confidence.get("day_shape") or "mixed_and_manageable")
    micro_name = str(daily_micro_intent.get("name") or "general_day")
    micro_focus = str(daily_micro_intent.get("daily_focus") or "").strip()

    direct_answer = (
        f"{verdict.capitalize()} day with {confidence} confidence for {micro_name.replace('_', ' ')}."
    )
    if day_shape:
        direct_answer += f" Overall shape: {day_shape.replace('_', ' ')}."

    return {
        "method": "daily_output_contract_v1",
        "target_date": target_date,
        "micro_intent": {
            "name": micro_name,
            "focus": micro_focus,
            "best_for": best_for,
            "watch_for": watch_for,
        },
        "verdict": verdict,
        "confidence_band": confidence,
        "event_likelihood": daily_confidence.get("event_likelihood"),
        "day_shape": day_shape,
        "direct_answer": direct_answer,
        "top_triggers": _top_trigger_labels(ranked_triggers),
        "top_domains": _domain_labels(daily_judgment.get("top_event_domains") or []),
        "best_uses_of_day": best_for,
        "watchouts": watch_for,
        "best_windows": _window_labels(favorable_windows),
        "caution_windows": _window_labels(caution_windows),
        "transition_note": _transition_note(transitions),
        "supporting_factors": support,
        "contradictions": contradictions,
        "practical_guidance": daily_confidence.get("practical_guidance"),
    }
