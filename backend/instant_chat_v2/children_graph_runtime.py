"""Runtime resolution between Instant Children questions and compiled policy."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .children import (
    BOUNDARY_CHILDREN_SUBTYPES,
    TIMING_CHILDREN_SUBTYPES,
    is_children_category,
    normalize_children_subtype,
)
from .children_graph_policy import ChildrenGraphPolicyStore, default_children_graph_policy_store


TIMING_MODES = frozenset({"event_prediction", "event_timing", "lifetime_event_timing", "month_timing", "timing_window", "daily_forecast"})
_MODE_COMPATIBILITY = {
    "children:ModeTopic": {"topic_reading", "trait_nature", "potential_capacity"},
    "children:ModeCapacity": {"potential_capacity", "topic_reading", "trait_nature"},
    "children:ModeDiagnosis": {"problem_diagnosis", "topic_reading"},
    "children:ModeTiming": set(TIMING_MODES),
    "children:ModeDecision": {"decision_support", "comparison_choice", "potential_capacity"},
    "children:ModeRemedy": {"remedy_action"},
    "children:ModeHandoff": {"dedicated_partnership_flow", "dedicated_muhurat_flow", "handoff", "topic_reading", "potential_capacity", "problem_diagnosis", "event_prediction"},
    "children:ModeRefusal": {"safety_refusal", "handoff", "topic_reading", "potential_capacity"},
}

_FACTOR_LABELS = {
    "children:D1": "D1 progeny promise", "children:D7": "D7 Saptamsa confirmation",
    "children:D10": "D10 career branch", "children:H1": "House 1 self and readiness",
    "children:H2": "House 2 family expansion", "children:H4": "House 4 care and emotional base",
    "children:H5": "House 5 children and first-child promise", "children:H6": "House 6 treatment and routine",
    "children:H7": "House 7 subsequent-child derivative", "children:H8": "House 8 reproductive transition",
    "children:H9": "House 9 subsequent-child and grace", "children:H10": "House 10 career and negation pressure",
    "children:H11": "House 11 realization", "children:H12": "House 12 treatment, loss and distance",
    "children:JupiterKaraka": "Jupiter progeny karaka condition",
    "children:LordNakshatraChain": "House-lord and nakshatra chains",
    "children:ChildOrderFrame": "First/subsequent-child house progression",
    "children:KPFructification": "KP 2-5-11 materialization",
    "children:DashaActivation": "Dasha permission", "children:TransitConfirmation": "Transit confirmation",
    "children:RemedyBlueprint": "Calculated remedy blueprint",
    "children:ScopeBoundary": "Question-scope boundary",
}


def children_graph_runtime_key(category: Any, query_plan: Mapping[str, Any] | None = None) -> str | None:
    if not is_children_category(category):
        return None
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    subtype = normalize_children_subtype(plan.get("children_subtype"))
    mode = str(plan.get("answer_mode") or "").strip().lower()
    if mode == "remedy_action":
        return "children_remedy"
    if subtype in BOUNDARY_CHILDREN_SUBTYPES:
        return subtype
    if subtype == "conception_capacity" and mode in TIMING_MODES:
        return "conception_timing"
    if subtype == "adoption_pathway" and mode in TIMING_MODES:
        return "adoption_timing"
    if subtype == "assisted_conception" and mode in TIMING_MODES:
        return "assisted_conception_timing"
    if subtype == "first_child_capacity" and mode in TIMING_MODES:
        return "first_child"
    if subtype == "subsequent_child_capacity" and mode in TIMING_MODES:
        return "subsequent_child"
    if subtype == "parenthood_vs_career" and mode in TIMING_MODES:
        return "parenthood_vs_career_timing"
    return subtype


def resolve_children_graph_inputs(*, intent: Mapping[str, Any] | None, context: Mapping[str, Any] | None, query_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    intent = intent if isinstance(intent, Mapping) else {}
    context = context if isinstance(context, Mapping) else {}
    plan = dict(query_plan or {})
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    plan.setdefault("children_subtype", intent.get("children_subtype") or summary.get("children_subtype"))
    return {
        "category": plan.get("category") or summary.get("category") or intent.get("category"),
        "query_plan": plan,
        "observed_answer_mode": plan.get("answer_mode") or summary.get("answer_mode") or intent.get("answer_mode"),
    }


def _present(value: Any) -> bool:
    return value not in (None, "", [], (), {})


def observed_children_factors(context: Mapping[str, Any], query_plan: Mapping[str, Any] | None = None) -> set[str]:
    factors: set[str] = set()
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    runtime_key = children_graph_runtime_key(plan.get("category"), plan)
    if runtime_key in BOUNDARY_CHILDREN_SUBTYPES:
        factors.add("children:ScopeBoundary")
        return factors
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    foundation = normalized.get("children_foundation") if isinstance(normalized.get("children_foundation"), Mapping) else {}
    availability = foundation.get("availability") if isinstance(foundation.get("availability"), Mapping) else {}
    if availability.get("d1"): factors.add("children:D1")
    if availability.get("d7"): factors.add("children:D7")
    if availability.get("d10"): factors.add("children:D10")
    for house in foundation.get("houses_available") or []:
        try: factors.add(f"children:H{int(house)}")
        except (TypeError, ValueError): pass
    flag_map = {
        "jupiter_karaka": "children:JupiterKaraka",
        "lord_nakshatra_chain": "children:LordNakshatraChain",
        "child_order_frame": "children:ChildOrderFrame",
        "kp_fructification": "children:KPFructification",
        "remedy_blueprint": "children:RemedyBlueprint",
    }
    for key, factor in flag_map.items():
        if availability.get(key): factors.add(factor)
    if runtime_key in TIMING_CHILDREN_SUBTYPES:
        dashas = context.get("current_dashas") if isinstance(context.get("current_dashas"), Mapping) else {}
        transits = context.get("current_transits") if isinstance(context.get("current_transits"), Mapping) else {}
        if _present(dashas.get("levels")) or _present(normalized.get("forward_event_dasha_scan")) or _present(normalized.get("historical_event_dasha_scan")):
            factors.add("children:DashaActivation")
        if _present(transits.get("planets")) or _present(normalized.get("transit_activation_timeline")) or _present(normalized.get("double_transit")):
            factors.add("children:TransitConfirmation")
    return factors


def compare_children_graph_policy(*, category: Any, query_plan: Mapping[str, Any] | None, observed_answer_mode: Any, context: Mapping[str, Any], store: ChildrenGraphPolicyStore | None = None) -> dict[str, Any] | None:
    if not is_children_category(category): return None
    runtime_key = children_graph_runtime_key(category, query_plan)
    policy_store = store or default_children_graph_policy_store()
    policy = policy_store.resolve(str(runtime_key or ""))
    if policy is None:
        return {"ontology_version": policy_store.ontology_version, "runtime_key": runtime_key, "match": False, "mismatches": [{"kind": "missing_compiled_policy"}]}
    actual = observed_children_factors(context, query_plan)
    required, excluded = set(policy.required_factors), set(policy.default_exclusions)
    observed_mode = str(observed_answer_mode or "")
    mode_match = observed_mode in _MODE_COMPATIBILITY.get(policy.answer_mode, set())
    missing, unexpected = sorted(required - actual), sorted(excluded & actual)
    mismatches = ([] if mode_match else [{"kind": "answer_mode", "expected": policy.answer_mode, "observed": observed_mode}])
    if missing: mismatches.append({"kind": "missing_required_factors", "factors": missing})
    if unexpected: mismatches.append({"kind": "unexpected_default_exclusions", "factors": unexpected})
    return {
        "ontology_version": policy_store.ontology_version, "runtime_key": runtime_key,
        "ontology_resource": policy.ontology_resource, "question_label": policy.question_label,
        "graph_tree": policy.graph_tree, "expected_answer_mode": policy.answer_mode, "observed_answer_mode": observed_mode,
        "mode_match": mode_match, "required_factors": sorted(required), "observed_factors": sorted(actual),
        "default_exclusions": sorted(excluded), "missing_required_factors": missing,
        "unexpected_default_exclusions": unexpected, "required_capabilities": sorted(policy.required_capabilities),
        "decision_rules": sorted(policy.decision_rules), "guardrails": sorted(policy.guardrails),
        "answer_contract": policy.answer_contract, "evidence_policy": policy.evidence_policy,
        "match": not mismatches, "mismatches": mismatches,
    }


def _resource_label(value: Any) -> str:
    text = str(value or "").split(":")[-1]
    return " ".join(re.sub(r"(?<!^)(?=[A-Z])", " ", text).split()).capitalize() or "Unknown graph node"


def build_children_graph_route(comparison: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(comparison, Mapping): return None
    required = [str(value) for value in comparison.get("required_factors", ())]
    observed = {str(value) for value in comparison.get("observed_factors", ())}
    return {
        "status": "matched" if comparison.get("match") else "review_needed",
        "ontology_version": comparison.get("ontology_version"), "runtime_key": comparison.get("runtime_key"),
        "question_type": comparison.get("question_label") or _resource_label(comparison.get("runtime_key")),
        "graph_tree": comparison.get("graph_tree"), "expected_approach": _resource_label(comparison.get("expected_answer_mode")),
        "selected_approach": _resource_label(comparison.get("observed_answer_mode")), "mode_match": bool(comparison.get("mode_match")),
        "required_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor)), "selected": factor in observed} for factor in required],
        "additional_selected_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))} for factor in sorted(observed - set(required))],
        "missing_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))} for factor in required if factor not in observed],
        "decision_rules": [{"id": str(v), "label": _resource_label(v)} for v in comparison.get("decision_rules", ())],
        "guardrails": [{"id": str(v), "label": _resource_label(v)} for v in comparison.get("guardrails", ())],
        "required_capabilities": [{"id": str(v), "label": _resource_label(v)} for v in comparison.get("required_capabilities", ())],
        "answer_contract": _resource_label(comparison.get("answer_contract")), "evidence_policy": _resource_label(comparison.get("evidence_policy")),
    }


__all__ = [
    "build_children_graph_route", "children_graph_runtime_key", "compare_children_graph_policy",
    "is_children_category", "resolve_children_graph_inputs",
]
