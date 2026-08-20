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
    timing_mode = query_plan.get("answer_mode") in {
        "event_timing", "lifetime_event_timing", "month_timing", "event_prediction", "timing_window"
    }
    calculator_required_mode = query_plan.get("answer_mode") in {
        "factual_chart_lookup", "location_recommendation", "dedicated_muhurat_flow"
    }
    available_capabilities = {
        str(name) for name, row in capability_rows.items() if row.get("status") == "available"
    }
    high_confidence_capabilities = {
        str(name) for name, row in capability_rows.items() if row.get("confidence_role") == "high_confidence"
    }
    high_support_capabilities = {
        str(name) for name, row in capability_rows.items() if row.get("confidence_role") == "high_support"
    }
    option_comparison = (by_kind.get("option_comparison") or {}).get("value")
    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), dict) else {}
    exact_day = bool(time_scope.get("is_exact_day"))
    daily_synthesis = (by_kind.get("daily_school_synthesis") or {}).get("value")
    daily_synthesis = daily_synthesis if isinstance(daily_synthesis, dict) else {}
    daily_judgment = daily_synthesis.get("daily_judgment") if isinstance(daily_synthesis.get("daily_judgment"), dict) else {}
    if exact_day:
        tara = daily_judgment.get("moon_tara_quality") if isinstance(daily_judgment.get("moon_tara_quality"), dict) else {}
        direction = (
            "insufficient_evidence" if missing_required else
            "supportive_day" if tara.get("quality") == "supportive" and daily_judgment.get("support_houses") else
            "caution_day" if tara.get("quality") == "caution" and daily_judgment.get("caution_houses") else
            "mixed_day"
        )
        windows = []
        rationale = {
            "target_date": time_scope.get("target_date") or time_scope.get("as_of"),
            "top_activated_houses": daily_judgment.get("top_activated_houses") or [],
            "top_event_domains": daily_judgment.get("top_event_domains") or [],
            "moon_tara_quality": tara,
            "massive_result_factors": daily_judgment.get("massive_result_factors") or [],
            "decision_rule": daily_judgment.get("prediction_rule"),
        }
        confidence = 0.9 if not missing_required else 0.38
    elif query_plan.get("answer_mode") == "comparison_choice" and isinstance(option_comparison, dict) and option_comparison:
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
    elif query_plan.get("answer_mode") == "factual_chart_lookup":
        chart = (by_kind.get("chart_facts") or {}).get("value") if isinstance((by_kind.get("chart_facts") or {}).get("value"), dict) else {}
        charts = chart.get("charts") if isinstance(chart.get("charts"), dict) else {}
        reading = [str(line).strip() for line in (chart.get("reading_lines") or []) if str(line).strip()]
        if not reading and chart.get("reading_text"):
            reading = [str(chart.get("reading_text"))]
        missing_charts = [str(item) for item in (chart.get("missing_requested_charts") or []) if str(item).strip()]
        if charts or reading:
            direction = "calculated_chart"
            windows = []
            signals = []
            for compact in charts.values():
                if not isinstance(compact, dict):
                    continue
                signals.extend(str(item).strip() for item in (compact.get("support_signals") or []) if str(item).strip())
                signals.extend(str(item).strip() for item in (compact.get("caution_signals") or []) if str(item).strip())
            domain_lines = []
            for compact in charts.values():
                domain = compact.get("domain") if isinstance(compact, dict) and isinstance(compact.get("domain"), dict) else {}
                life_area = str(domain.get("life_area") or "").strip()
                if life_area:
                    domain_lines.append(life_area)
            rationale = signals or domain_lines or reading or list(charts.keys())
            confidence = 0.94 if not missing_charts else 0.72
        else:
            direction = "insufficient_evidence"
            windows = []
            rationale = missing_charts or ["The requested chart was not calculated."]
            confidence = 0.35
    elif query_plan.get("answer_mode") == "potential_capacity":
        promise = (by_kind.get("natal_promise") or {}).get("value")
        promise = promise if isinstance(promise, dict) else {}
        status = str(promise.get("status") or "not_established").strip().lower()
        if missing_required or status == "not_established":
            direction = "insufficient_evidence"
            confidence = 0.38
        elif status == "supported":
            direction = "supported_natal_promise"
            confidence = 0.84
        else:
            direction = "qualified_natal_promise"
            confidence = 0.68
        windows = []
        rationale = {
            "promise_status": status,
            "topic_support": promise.get("topic_support"),
            "rule": "Natal promise is judged from natal and relevant divisional evidence; current activation cannot establish it.",
        }
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
    if (timing_mode or calculator_required_mode or exact_day or query_plan.get("answer_mode") == "potential_capacity") and missing_required:
        if not (query_plan.get("answer_mode") == "factual_chart_lookup" and direction == "calculated_chart"):
            direction = "insufficient_evidence"
            confidence = min(confidence, 0.39)
            windows = []
    confidence_tier = "directional"
    if timing_mode or exact_day:
        high_confidence_complete = bool(high_confidence_capabilities) and high_confidence_capabilities.issubset(available_capabilities)
        high_support_complete = bool(high_support_capabilities) and high_support_capabilities.issubset(available_capabilities)
        if high_confidence_complete and high_support_complete and not missing_required:
            confidence_tier = "high_support"
        elif high_confidence_complete and not missing_required:
            confidence_tier = "high_confidence"
        elif not missing_required:
            confidence_tier = "limited_timing_support"
    else:
        high_confidence_complete = False
        high_support_complete = False
    conflicts = []
    if primary and modifiers:
        conflicts.append("Primary drivers and secondary modifiers must both be represented; modifiers cannot overturn primary evidence without an explicit rule.")
    return {
        "schema_version": "instant-verdict/v1",
        "category": query_plan.get("category"),
        "answer_mode": query_plan.get("answer_mode"),
        "direction": direction,
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
        "confidence_tier": confidence_tier,
        "confidence_evidence": {
            "mandatory_complete": not missing_required,
            "high_confidence_complete": high_confidence_complete,
            "high_support_complete": high_support_complete,
            "available": sorted(available_capabilities),
        },
        "ranked_windows": windows[:5] if isinstance(windows, list) else windows,
        "rationale": rationale,
        "modifiers": modifiers[:5] if isinstance(modifiers, list) else modifiers,
        "conflicts": conflicts,
        "missing_required_capabilities": missing_required,
        "evidence_ids": [item.get("evidence_id") for item in records if item.get("strength") == "primary"],
    }
