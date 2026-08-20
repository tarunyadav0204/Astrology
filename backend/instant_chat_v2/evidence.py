"""Normalize current calculator output into a source-labelled evidence ledger."""

from __future__ import annotations

import re
from typing import Any, Dict, List


def _compact(value: Any, *, depth: int = 0) -> Any:
    """Keep debug evidence safe to persist and render in chat history.

    Calculator payloads can contain full charts and long diagnostic arrays.  The
    audit panel needs representative, source-labelled evidence rather than a
    second copy of the entire calculation context.
    """
    if depth >= 5:
        return "[nested value omitted]"
    if isinstance(value, str):
        return value if len(value) <= 800 else f"{value[:797]}..."
    if isinstance(value, dict):
        items = list(value.items())
        compacted = {
            str(key): _compact(item, depth=depth + 1)
            for key, item in items[:24]
        }
        if len(items) > 24:
            compacted["_omitted_keys"] = len(items) - 24
        return compacted
    if isinstance(value, (list, tuple)):
        compacted = [_compact(item, depth=depth + 1) for item in list(value)[:12]]
        if len(value) > 12:
            compacted.append({"_omitted_items": len(value) - 12})
        return compacted
    return value


def _add(records: List[Dict[str, Any]], *, source: str, kind: str, value: Any,
         strength: str = "supporting", confidence: float = 0.75,
         calculator: str | None = None) -> None:
    if value in (None, "", [], {}):
        return
    records.append({
        "evidence_id": f"ev-{len(records) + 1:03d}",
        "source": source,
        "provenance": {
            "calculator": calculator or source,
            "execution": "existing_instant_calculator_pipeline",
            "precomputed": True,
        },
        "kind": kind,
        "strength": strength,
        "confidence": round(max(0.0, min(1.0, float(confidence))), 2),
        "value": _compact(value),
    })


def _capability_evidence_kinds(capability: str) -> List[str]:
    name = str(capability or "").lower()
    if name == "daily.five_level_dasha":
        return ["daily_dasha_stack"]
    if name == "daily.moon_tara_bala":
        return ["daily_moon_tara"]
    if name == "daily.kp_fructification":
        return ["daily_kp"]
    if name == "daily.school_synthesis":
        return ["daily_school_synthesis"]
    if name == "parashari.current_dasha":
        return ["current_dasha"]
    if "dasha_windows" in name:
        # Timing permission requires an actual calculated dasha scan. A fused
        # verdict or a transit timeline cannot stand in for dasha evidence.
        return ["future_dasha_windows"]
    if name == "parashari.activations":
        return ["active_houses"]
    if re.search(r"(?:^|\.)d\d+(?:_|\.|$)", name) or "divisional" in name:
        return ["divisional_confirmation"]
    if name.startswith("parashari.") and any(
        token in name for token in ("promise", "foundation", "topic_foundation", "house_lords")
    ):
        return ["primary_drivers"]
    if name.startswith("kp."):
        return ["kp_signals"]
    if name in {"transit.double_transit", "parashari.double_transit"}:
        return ["double_transit_support"]
    if name.startswith("transit."):
        # A current planet snapshot is not an event trigger window.
        return ["transit_activation_timeline"]
    if name == "comparison.option_specific_evidence":
        return ["option_comparison"]
    if name == "parashari.health_body_area":
        return ["health_body_area"]
    if name.startswith("chart."):
        return ["chart_facts"]
    if name.startswith("jaimini.karaka") or name == "parashari.karaka_support":
        return ["karaka_support"]
    if name.startswith("nadi."):
        return ["nadi_synthesis"]
    if name.startswith("location."):
        return ["location_recommendation"]
    if name.startswith("muhurat."):
        return ["muhurat_slots"]
    # Jaimini and future capability families must expose their own record kind;
    # divisional evidence alone is not proof that a Jaimini calculation ran.
    return []


def _segment_rows(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        rows = value.get("segments") or value.get("periods") or []
        return [row for row in rows if isinstance(row, dict)]
    return []


def _first_timing_container(*values: Any) -> Any:
    return next((value for value in values if _segment_rows(value)), {})


def build_evidence_ledger(instant_context: Dict[str, Any], evidence_plan: Dict[str, Any]) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    normalized = instant_context.get("normalized_evidence") if isinstance(instant_context.get("normalized_evidence"), dict) else {}
    dashas = instant_context.get("current_dashas") if isinstance(instant_context.get("current_dashas"), dict) else {}
    parashari = instant_context.get("instant_parashari") if isinstance(instant_context.get("instant_parashari"), dict) else {}
    transits = instant_context.get("current_transits") if isinstance(instant_context.get("current_transits"), dict) else {}
    daily = instant_context.get("daily_prediction_spine") if isinstance(instant_context.get("daily_prediction_spine"), dict) else {}

    if daily:
        schools = daily.get("school_judgments") if isinstance(daily.get("school_judgments"), dict) else {}
        _add(
            records, source="daily_prediction_spine", kind="daily_dasha_stack",
            value={
                "target_date": daily.get("target_date"),
                "dasha_stack": daily.get("dasha_stack"),
                "ranked_triggers": daily.get("ranked_triggers"),
                "interpretation_rules": daily.get("interpretation_rules"),
            }, strength="primary", confidence=0.96, calculator="daily_prediction_spine",
        )
        _add(
            records, source="daily_prediction_spine", kind="daily_moon_tara",
            value={
                "target_date": daily.get("target_date"),
                "moon": daily.get("moon"),
                "panchanga": daily.get("panchanga"),
            }, strength="primary", confidence=0.94, calculator="daily_prediction_spine",
        )
        _add(
            records, source="daily_prediction_spine.kp", kind="daily_kp",
            value=schools.get("kp"), strength="primary", confidence=0.94,
            calculator="kp_daily_fructification",
        )
        _add(
            records, source="daily_prediction_spine.synthesis", kind="daily_school_synthesis",
            value={
                "daily_judgment": daily.get("daily_judgment"),
                "school_judgments": schools,
            }, strength="supporting", confidence=0.9, calculator="daily_school_judgments",
        )

    _add(records, source="parashari.dasha", kind="current_dasha", value={
        "as_of": dashas.get("as_of"), "levels": dashas.get("levels") or []
    }, strength="primary", confidence=0.95)
    _add(records, source="parashari.activation", kind="active_houses", value={
        "dominant_houses": parashari.get("dominant_houses"),
        "activation_mechanisms": parashari.get("activation_mechanisms"),
        "active_dashas": parashari.get("active_dashas_formatted"),
    }, strength="primary", confidence=0.9)
    _add(records, source="evidence.fusion.legacy", kind="primary_drivers",
         value=normalized.get("primary_drivers"), strength="primary", confidence=0.88)
    _add(records, source="evidence.fusion.legacy", kind="secondary_modifiers",
         value=normalized.get("secondary_modifiers"), strength="supporting", confidence=0.72)
    _add(records, source="parashari.divisional", kind="divisional_confirmation",
         value=normalized.get("divisional_specifics") or parashari.get("divisional_support"), confidence=0.82)
    _add(records, source="kp", kind="kp_signals",
         value=normalized.get("kp_evidence") or parashari.get("kp_evidence"), confidence=0.84)
    _add(records, source="transit", kind="current_transits",
         value={"as_of": transits.get("as_of"), "planets": transits.get("planets")}, confidence=0.78)
    _add(records, source="timing.fusion", kind="event_timing_verdict",
         value=normalized.get("event_timing_verdict"), strength="primary", confidence=0.9)
    activation_timeline = normalized.get("transit_activation_timeline")
    # Dasha segment containers live on instant_parashari in the calculation
    # pipeline. Older normalization copied only the transit timeline, which made
    # the audit packet claim required dasha evidence was missing even though the
    # answer composer had already used those calculated segments.
    window_segments = _first_timing_container(
        normalized.get("window_dasha_segments"),
        parashari.get("window_dasha_segments"),
    )
    horizon_segments = _first_timing_container(
        normalized.get("horizon_dasha_segments"),
        parashari.get("horizon_dasha_segments"),
    )
    forward_segments = _first_timing_container(
        normalized.get("forward_event_dasha_scan"),
        parashari.get("forward_event_dasha_scan"),
    )
    activation_segments = _segment_rows(window_segments) or _segment_rows(horizon_segments)
    if activation_timeline or activation_segments:
        _add(records, source="parashari.transit_activation", kind="transit_activation_timeline",
             value={
                 "natal_promise": normalized.get("natal_promise"),
                 "timeline": activation_timeline,
                 "window_segments": activation_segments,
             }, strength="primary", confidence=0.92)
    _add(records, source="parashari.dasha_scan", kind="future_dasha_windows",
         value=(forward_segments or horizon_segments or window_segments),
         strength="primary", confidence=0.88)
    _add(records, source="comparison", kind="option_comparison",
         value=normalized.get("option_comparison"), strength="primary", confidence=0.86)
    _add(records, source="parashari.health", kind="health_body_area",
         value=normalized.get("health_body_area") or normalized.get("body_area_evidence"),
         strength="primary", confidence=0.8)
    chart_facts = normalized.get("chart_facts") if isinstance(normalized.get("chart_facts"), dict) else {}
    chart_fact_value = {}
    if isinstance(chart_facts, dict) and (
        chart_facts.get("charts")
        or chart_facts.get("missing_requested_charts")
        or chart_facts.get("reading_text")
        or chart_facts.get("analysis_brief")
    ):
        chart_fact_value = chart_facts
    _add(
        records, source="chart.calculation", kind="chart_facts",
        value=chart_fact_value,
        strength="primary", confidence=0.98, calculator="chart_and_divisional_calculators",
    )
    _add(records, source="jaimini.karaka", kind="karaka_support",
         value=normalized.get("karaka_evidence") or normalized.get("jaimini_evidence") or parashari.get("karaka_evidence"),
         strength="supporting", confidence=0.84, calculator="jaimini_karaka_calculator")
    timing_payload = normalized.get("event_timing_verdict") if isinstance(normalized.get("event_timing_verdict"), dict) else {}
    _add(records, source="transit.double_transit", kind="double_transit_support",
         value=(normalized.get("double_transit") or timing_payload.get("double_transit")),
         strength="supporting", confidence=0.9, calculator="double_transit_service")
    _add(records, source="nadi.domain_synthesis", kind="nadi_synthesis",
         value=normalized.get("nadi_evidence"), strength="supporting", confidence=0.82,
         calculator="nadi_domain_synthesis_calculator")
    _add(records, source="location.recommendation", kind="location_recommendation",
         value=normalized.get("location_recommendation") or instant_context.get("location_recommendation"),
         strength="primary", confidence=0.85, calculator="location_recommendation_calculator")
    _add(records, source="muhurat.election", kind="muhurat_slots",
         value=normalized.get("muhurat_slots") or instant_context.get("muhurat_slots"),
         strength="primary", confidence=0.9, calculator="muhurat_calculator")
    _add(records, source="claim.gates", kind="claim_gates",
         value=normalized.get("claim_gates"), strength="constraint", confidence=1.0)

    requested = {item["capability"]: item for item in evidence_plan.get("capability_requests", [])}
    records_by_kind = {
        str(item.get("kind")): item
        for item in records
        if isinstance(item, dict) and item.get("kind")
    }
    capabilities = []
    for name, request in requested.items():
        matching_kinds = _capability_evidence_kinds(name)
        evidence_ids = [
            records_by_kind[kind]["evidence_id"]
            for kind in matching_kinds
            if kind in records_by_kind
        ]
        status = "available" if evidence_ids else "not_exposed"
        capabilities.append({
            **request,
            "status": status,
            "evidence_ids": evidence_ids,
            "unavailable_reason": None if evidence_ids else "No result from the named calculator was exposed for this request.",
        })
    return {
        "schema_version": "instant-evidence-ledger/v1",
        "records": records,
        "capabilities": capabilities,
        "record_count": len(records),
        "calculator_contract": "A capability is available only when its own calculator-family record is present; unrelated chart evidence never satisfies it.",
    }
