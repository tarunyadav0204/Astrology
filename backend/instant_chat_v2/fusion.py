"""Produce a compact verdict from normalized evidence records."""

from __future__ import annotations

from typing import Any, Dict


def _within_horizon(row: Any, *, as_of: str | None, horizon_end: str | None) -> bool:
    if not isinstance(row, dict):
        return False
    start = str(row.get("start") or "")[:10]
    end = str(row.get("end") or "")[:10]
    if as_of and end and end < as_of:
        return False
    if horizon_end and start and start > horizon_end:
        return False
    return True


def _confidence_score(value: Any, default: float = 0.82) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    labels = {"low": 0.45, "medium": 0.68, "high": 0.86, "very_high": 0.94}
    return labels.get(str(value or "").strip().lower().replace(" ", "_"), default)


def fuse_evidence(query_plan: Dict[str, Any], ledger: Dict[str, Any]) -> Dict[str, Any]:
    records = ledger.get("records", [])
    by_kind = {str(item.get("kind")): item for item in records if isinstance(item, dict)}
    timing = (by_kind.get("event_timing_verdict") or {}).get("value")
    primary = (by_kind.get("primary_drivers") or {}).get("value") or []
    modifiers = (by_kind.get("secondary_modifiers") or {}).get("value") or []
    capability_rows = {
        row.get("capability"): row for row in ledger.get("capabilities", []) if isinstance(row, dict)
    }
    missing_required = [
        name for name, row in capability_rows.items()
        if row.get("required") and row.get("status") != "available"
    ]
    option_comparison = (by_kind.get("option_comparison") or {}).get("value")
    if query_plan.get("answer_mode") == "comparison_choice" and isinstance(option_comparison, dict) and option_comparison:
        comparison = option_comparison.get("comparison") if isinstance(option_comparison.get("comparison"), dict) else {}
        direction = comparison.get("direction") or "insufficient_option_evidence"
        windows = [
            option.get("best_window")
            for option in list(option_comparison.get("options") or [])
            if isinstance(option, dict) and isinstance(option.get("best_window"), dict) and option.get("best_window")
        ]
        rationale = {
            "favored_option": comparison.get("favored_option"),
            "score_gap": comparison.get("score_gap"),
            "options": option_comparison.get("options"),
            "instruction": comparison.get("instruction"),
        }
        confidence = 0.84 if direction == "leans_to_option" else 0.7
    elif query_plan.get("answer_mode") == "comparison_choice" and "comparison.option_specific_evidence" in missing_required:
        direction = "insufficient_option_evidence"
        windows = []
        rationale = primary[:2] if isinstance(primary, list) else primary
        confidence = 0.4
    elif isinstance(timing, dict) and timing:
        direction = timing.get("verdict") or timing.get("direction") or timing.get("status") or "conditional"
        windows = timing.get("windows") or timing.get("ranked_windows") or timing.get("best_windows") or []
        if not windows:
            progression = [
                row for row in (timing.get("material_future_progression") or [])
                if isinstance(row, dict) and row
            ]
            windows = [
                row for row in [timing.get("current_window"), *progression]
                if isinstance(row, dict) and row
            ]
            if not progression:
                windows.extend([
                    row for row in (
                        timing.get("earliest_material_future_window"),
                        timing.get("best_future_cluster") or timing.get("best_future_window"),
                    )
                    if isinstance(row, dict) and row
                ])
        time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), dict) else {}
        windows = [
            row for row in windows
            if _within_horizon(
                row,
                as_of=time_scope.get("as_of"),
                horizon_end=time_scope.get("horizon_end"),
            )
        ]
        rationale = timing.get("why") or timing.get("summary") or timing.get("reason") or []
        confidence = _confidence_score(timing.get("confidence"), 0.82)
    else:
        direction = "supported_with_conditions" if primary else "insufficient_evidence"
        windows = []
        rationale = primary[:4] if isinstance(primary, list) else primary
        confidence = 0.72 if primary else 0.35
    conflicts = []
    if primary and modifiers:
        conflicts.append("Primary drivers and secondary modifiers must both be represented; modifiers cannot overturn primary evidence without an explicit rule.")
    return {
        "schema_version": "instant-verdict/v1",
        "category": query_plan.get("category"),
        "answer_mode": query_plan.get("answer_mode"),
        "direction": direction,
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
        "ranked_windows": windows[:5] if isinstance(windows, list) else windows,
        "rationale": rationale,
        "modifiers": modifiers[:5] if isinstance(modifiers, list) else modifiers,
        "conflicts": conflicts,
        "missing_required_capabilities": missing_required,
        "evidence_ids": [item.get("evidence_id") for item in records if item.get("strength") == "primary"],
    }
