"""Normalize current calculator output into a source-labelled evidence ledger."""

from __future__ import annotations

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
         strength: str = "supporting", confidence: float = 0.75) -> None:
    if value in (None, "", [], {}):
        return
    records.append({
        "evidence_id": f"ev-{len(records) + 1:03d}",
        "source": source,
        "kind": kind,
        "strength": strength,
        "confidence": round(max(0.0, min(1.0, float(confidence))), 2),
        "value": _compact(value),
    })


def _capability_evidence_kinds(capability: str) -> List[str]:
    name = str(capability or "").lower()
    if name == "parashari.current_dasha":
        return ["current_dasha"]
    if "dasha_windows" in name:
        return ["event_timing_verdict", "future_dasha_windows", "transit_activation_timeline", "option_comparison"]
    if name == "parashari.activations":
        return ["active_houses"]
    if any(token in name for token in ("d7", "d9", "d10", "divisional")):
        return ["divisional_confirmation"]
    if name.startswith("parashari.") and any(
        token in name for token in ("promise", "foundation", "topic_foundation", "house_lords")
    ):
        return ["primary_drivers"]
    if name.startswith("kp."):
        return ["kp_signals"]
    if name.startswith("transit."):
        return ["transit_activation_timeline", "event_timing_verdict", "current_transits"]
    if name == "comparison.option_specific_evidence":
        return ["option_comparison"]
    if name == "parashari.health_body_area":
        return ["health_body_area"]
    # Jaimini and future capability families must expose their own record kind;
    # divisional evidence alone is not proof that a Jaimini calculation ran.
    return []


def build_evidence_ledger(instant_context: Dict[str, Any], evidence_plan: Dict[str, Any]) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    normalized = instant_context.get("normalized_evidence") if isinstance(instant_context.get("normalized_evidence"), dict) else {}
    dashas = instant_context.get("current_dashas") if isinstance(instant_context.get("current_dashas"), dict) else {}
    parashari = instant_context.get("instant_parashari") if isinstance(instant_context.get("instant_parashari"), dict) else {}
    transits = instant_context.get("current_transits") if isinstance(instant_context.get("current_transits"), dict) else {}

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
    _add(records, source="parashari.transit_activation", kind="transit_activation_timeline",
         value={
             "natal_promise": normalized.get("natal_promise"),
             "timeline": normalized.get("transit_activation_timeline"),
             "window_segments": normalized.get("window_dasha_segments"),
         }, strength="primary", confidence=0.92)
    _add(records, source="parashari.dasha_scan", kind="future_dasha_windows",
         value=normalized.get("forward_event_dasha_scan") or normalized.get("horizon_dasha_segments"),
         strength="primary", confidence=0.88)
    _add(records, source="comparison", kind="option_comparison",
         value=normalized.get("option_comparison"), strength="primary", confidence=0.86)
    _add(records, source="parashari.health", kind="health_body_area",
         value=normalized.get("health_body_area") or normalized.get("body_area_evidence"),
         strength="primary", confidence=0.8)
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
        })
    return {
        "schema_version": "instant-evidence-ledger/v1",
        "records": records,
        "capabilities": capabilities,
        "record_count": len(records),
    }
