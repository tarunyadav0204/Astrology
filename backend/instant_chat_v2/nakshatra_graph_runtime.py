"""Authoritative Live graph contract for Nakshatra questions."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .nakshatra import is_nakshatra_category, nakshatra_profile, normalize_nakshatra_subtype
from .nakshatra_graph_policy import NakshatraGraphPolicyStore, default_nakshatra_graph_policy_store


def resolve_nakshatra_graph_inputs(*, intent: Mapping[str, Any] | None, context: Mapping[str, Any] | None, query_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    intent = intent if isinstance(intent, Mapping) else {}
    context = context if isinstance(context, Mapping) else {}
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    plan = dict(query_plan or {})
    plan.setdefault("nakshatra_subtype", intent.get("nakshatra_subtype") or summary.get("nakshatra_subtype"))
    return {
        "category": plan.get("category") or summary.get("category") or intent.get("category"),
        "query_plan": plan,
        "observed_answer_mode": plan.get("answer_mode") or summary.get("answer_mode") or intent.get("answer_mode"),
    }


def _observed(context: Mapping[str, Any]) -> set[str]:
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    foundation = normalized.get("nakshatra_foundation") if isinstance(normalized.get("nakshatra_foundation"), Mapping) else {}
    availability = foundation.get("availability") if isinstance(foundation.get("availability"), Mapping) else {}
    factors: set[str] = set()
    if availability.get("d1"): factors.add("nakshatra:D1")
    if availability.get("target_carrier"): factors.add("nakshatra:TargetCarrier")
    if availability.get("pada"): factors.add("nakshatra:Pada")
    if availability.get("dispositor"): factors.add("nakshatra:Dispositor")
    if availability.get("timing"): factors.add("nakshatra:TimingCarrier")
    if availability.get("remedy"): factors.add("nakshatra:RemedyBlueprint")
    if availability.get("naming"): factors.add("nakshatra:NamingSyllable")
    return factors


def compare_nakshatra_graph_policy(*, category: Any, query_plan: Mapping[str, Any] | None, observed_answer_mode: Any, context: Mapping[str, Any], store: NakshatraGraphPolicyStore | None = None) -> dict[str, Any] | None:
    if not is_nakshatra_category(category):
        return None
    plan = dict(query_plan or {})
    subtype = normalize_nakshatra_subtype(plan.get("nakshatra_subtype"))
    profile = nakshatra_profile(subtype)
    policy_store = store or default_nakshatra_graph_policy_store()
    policy = policy_store.resolve(subtype)
    if policy is None:
        return {"ontology_version": policy_store.ontology_version, "runtime_key": subtype, "match": False, "mismatches": [{"kind": "missing_compiled_policy"}]}
    required = set(policy.required_factors)
    observed = _observed(context)
    missing = sorted(required - observed)
    expected_mode = str(policy.answer_mode or profile["answer_mode"])
    mode = str(observed_answer_mode or "")
    mode_match = mode == expected_mode or (subtype == "nakshatra_timing" and mode in {"event_timing", "timing_window"})
    mismatches = []
    if not mode_match:
        mismatches.append({"kind": "answer_mode", "expected": expected_mode, "observed": mode})
    if missing:
        mismatches.append({"kind": "missing_required_factors", "factors": missing})
    return {
        "ontology_version": policy_store.ontology_version,
        "runtime_key": subtype,
        "ontology_resource": policy.ontology_resource,
        "question_label": policy.question_label,
        "graph_tree": policy.graph_tree,
        "expected_answer_mode": expected_mode,
        "observed_answer_mode": mode,
        "mode_match": mode_match,
        "required_factors": sorted(required),
        "observed_factors": sorted(observed),
        "default_exclusions": list(policy.default_exclusions),
        "missing_required_factors": missing,
        "unexpected_default_exclusions": [],
        "required_capabilities": sorted(policy.required_capabilities),
        "decision_rules": sorted(policy.decision_rules),
        "guardrails": sorted(policy.guardrails),
        "answer_contract": policy.answer_contract,
        "evidence_policy": policy.evidence_policy,
        "match": not mismatches,
        "mismatches": mismatches,
    }


def _label(value: Any) -> str:
    return " ".join(re.sub(r"(?<!^)(?=[A-Z])", " ", str(value or "").split(":")[-1]).replace("_", " ").split()).capitalize()


def build_nakshatra_graph_route(comparison: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(comparison, Mapping):
        return None
    required = [str(value) for value in comparison.get("required_factors") or []]
    observed = {str(value) for value in comparison.get("observed_factors") or []}
    return {
        "status": "matched" if comparison.get("match") else "review_needed",
        "ontology_version": comparison.get("ontology_version"),
        "runtime_key": comparison.get("runtime_key"),
        "question_type": comparison.get("question_label"),
        "graph_tree": comparison.get("graph_tree"),
        "expected_approach": _label(comparison.get("expected_answer_mode")),
        "selected_approach": _label(comparison.get("observed_answer_mode")),
        "mode_match": bool(comparison.get("mode_match")),
        "required_nodes": [{"id": item, "label": _label(item), "selected": item in observed} for item in required],
        "missing_nodes": [{"id": item, "label": _label(item)} for item in required if item not in observed],
        "decision_rules": [{"id": str(item), "label": _label(item)} for item in comparison.get("decision_rules") or []],
        "guardrails": [{"id": str(item), "label": _label(item)} for item in comparison.get("guardrails") or []],
        "required_capabilities": [{"id": str(item), "label": _label(item)} for item in comparison.get("required_capabilities") or []],
        "answer_contract": _label(comparison.get("answer_contract")),
        "evidence_policy": _label(comparison.get("evidence_policy")),
    }
