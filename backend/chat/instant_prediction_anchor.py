"""Small, non-invasive Instant cross-checks for Standard and Premium predictions.

This module deliberately does not alter the legacy Standard/Premium calculation
or response pipeline.  It builds a compact second opinion only for questions
whose router has already selected a prediction/timing answer mode.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable


_PREDICTION_ANSWER_MODES = frozenset({
    "event_prediction",
    "event_timing",
    "lifetime_event_timing",
    "month_timing",
    "timing_window",
    "comparison_choice",
})


def is_prediction_anchor_eligible(intent: Dict[str, Any] | None) -> bool:
    """Return true only for narrowly defined prediction/timing routes."""
    if not isinstance(intent, dict):
        return False
    return str(intent.get("answer_mode") or "").strip().lower() in _PREDICTION_ANSWER_MODES


def _compact_value(value: Any, *, depth: int = 0) -> Any:
    """Bound a record while preserving user-facing astrological reasoning."""
    if depth >= 3:
        return "[additional detail omitted]"
    if isinstance(value, str):
        return value[:500]
    if isinstance(value, dict):
        keep = (
            "start", "end", "date", "label", "chain", "dasha_chain", "planet",
            "why", "reason", "summary", "support", "pressure", "caution",
            "activated_focus_houses", "allowed_house_themes", "transit_confirmations",
            "manifestations", "status", "verdict", "direction", "confidence",
        )
        return {
            str(key): _compact_value(value[key], depth=depth + 1)
            for key in keep
            if value.get(key) not in (None, "", [], {})
        }
    if isinstance(value, (list, tuple)):
        return [_compact_value(item, depth=depth + 1) for item in list(value)[:3]]
    return value


def _reason_rows(records: Iterable[Any]) -> list[Dict[str, Any]]:
    allowed_kinds = {
        "primary_drivers",
        "natal_promise",
        "divisional_confirmation",
        "event_timing_verdict",
        "transit_activation_timeline",
        "secondary_modifiers",
        "claim_gates",
    }
    rows: list[Dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or str(record.get("kind") or "") not in allowed_kinds:
            continue
        value = _compact_value(record.get("value"))
        if value in (None, "", [], {}):
            continue
        rows.append({
            "kind": record.get("kind"),
            "polarity": record.get("strength") or "supporting",
            "finding": value,
        })
        if len(rows) == 5:
            break
    return rows


def build_prediction_anchor_from_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Convert an Instant V2 packet into a safe, model-readable cross-check.

    The anchor intentionally excludes raw chart payloads, scores, calculator
    diagnostics and evidence IDs.  Every retained item comes from the existing
    Instant calculation; this function never performs astrology itself.
    """
    if not isinstance(packet, dict):
        return {}
    query_plan = packet.get("query_plan") if isinstance(packet.get("query_plan"), dict) else {}
    verdict = packet.get("verdict") if isinstance(packet.get("verdict"), dict) else {}
    ledger = packet.get("evidence_ledger") if isinstance(packet.get("evidence_ledger"), dict) else {}
    answer_spec = packet.get("answer_spec") if isinstance(packet.get("answer_spec"), dict) else {}
    if not query_plan or not verdict:
        return {}

    time_scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), dict) else {}
    event_rules = answer_spec.get("event_rules") if isinstance(answer_spec.get("event_rules"), dict) else {}
    return {
        "source": "instant_v2_prediction_cross_check",
        "purpose": "Cross-check only; preserve the existing Standard/Premium reading and writing style.",
        "question_scope": {
            key: query_plan.get(key)
            for key in ("category", "answer_mode", "target_subject", "user_goal", "interpretation_frame")
            if query_plan.get(key) not in (None, "", [], {})
        },
        "time_scope": {
            key: time_scope.get(key)
            for key in ("as_of", "horizon_end", "retrospective", "target_date")
            if time_scope.get(key) not in (None, "", [], {})
        },
        "verdict": {
            key: verdict.get(key)
            for key in ("direction", "confidence", "confidence_tier", "rationale", "modifiers", "missing_required_capabilities")
            if verdict.get(key) not in (None, "", [], {})
        },
        "ranked_windows": [_compact_value(row) for row in list(verdict.get("ranked_windows") or [])[:5] if isinstance(row, dict)],
        "calculated_reasons": _reason_rows(ledger.get("records") or []),
        "prediction_rules": {
            key: event_rules.get(key)
            for key in ("required_material_windows", "dasha_level_terms", "claim_contract")
            if event_rules.get(key) not in (None, "", [], {})
        },
    }


def build_standard_premium_prediction_anchor(
    *, question: str, birth_data: Dict[str, Any], intent: Dict[str, Any],
    history: list[Dict[str, Any]], language: str,
) -> Dict[str, Any]:
    """Run the existing Instant calculation once and return only its cross-check.

    Failures are intentionally non-fatal: Standard/Premium keep their current
    behaviour exactly when the optional cross-check cannot be produced.
    """
    if not is_prediction_anchor_eligible(intent):
        return {}

    # Import lazily: Standard/Premium must not acquire an Instant dependency at
    # module import time, and their established path remains available on error.
    from chat.instant_chat_pipeline import _build_instant_context
    from instant_chat_v2 import build_instant_v2_packet
    from instant_chat_v2.graph_live import apply_live_graph_policy

    answer_mode = str(intent.get("answer_mode") or "").strip().lower()
    target_subject = intent.get("target_subject") if isinstance(intent.get("target_subject"), dict) else {"key": "self", "label": "self", "base_house": 1}
    instant_context = _build_instant_context(
        birth_data=birth_data,
        question=question,
        intent=intent,
        history=history or [],
        answer_mode_override=answer_mode,
        target_subject_override=target_subject,
        target_subjects_override=[target_subject],
    )
    packet = build_instant_v2_packet(
        question=question,
        intent=intent,
        answer_mode=answer_mode,
        target_subject=target_subject,
        language=language,
        instant_context=instant_context,
    )
    packet = apply_live_graph_policy(packet, intent=intent, context=instant_context)
    return build_prediction_anchor_from_packet(packet)
