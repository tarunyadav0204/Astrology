"""Runtime resolution between Instant Education questions and compiled policy."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .education import is_education_category, is_education_timing, normalize_education_subtype
from .education_graph_policy import EducationGraphPolicyStore, default_education_graph_policy_store


TIMING_MODES = frozenset({"event_prediction", "event_timing", "lifetime_event_timing", "month_timing", "timing_window", "daily_forecast"})
_MODE_COMPATIBILITY = {
    "education:ModeTopic": {"topic_reading", "trait_nature", "potential_capacity"},
    "education:ModeCapacity": {"potential_capacity", "topic_reading", "trait_nature", "decision_support"},
    "education:ModeDiagnosis": {"problem_diagnosis", "topic_reading"},
    "education:ModeTiming": set(TIMING_MODES),
    "education:ModeComparison": {"comparison_choice", "decision_support"},
    "education:ModeDecision": {"decision_support", "comparison_choice", "potential_capacity"},
    "education:ModeRemedy": {"remedy_action"},
}

_FACTOR_LABELS = {
    "education:D1": "D1 educational promise", "education:D9": "D9 carrier condition",
    "education:D10": "D10 qualification-to-work conversion", "education:D24": "D24 Siddhamsha confirmation",
    "education:LearningSignificators": "Learning significators", "education:LordNakshatraChain": "House-lord and nakshatra chains",
    "education:DignityStrength": "Dignity and strength", "education:EducationYogas": "Operational education combinations",
    "education:KPFructification": "KP educational materialization", "education:OptionEvidence": "Named option evidence",
    "education:DashaActivation": "Dasha permission", "education:TransitConfirmation": "Transit confirmation",
    "education:RemedyBlueprint": "Calculated remedy blueprint",
}


def education_graph_runtime_key(category: Any, query_plan: Mapping[str, Any] | None = None) -> str | None:
    if not is_education_category(category):
        return None
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    subtype = normalize_education_subtype(plan.get("education_subtype"))
    mode = str(plan.get("answer_mode") or "").strip().lower()
    if mode == "remedy_action":
        return "education_remedies"
    if subtype == "foreign_study" and mode in {"comparison_choice", "decision_support"}:
        return "foreign_study_comparison"
    if subtype == "education_vs_work" and mode in TIMING_MODES:
        return "education_vs_work_timing"
    if subtype == "overall" and is_education_timing(subtype, mode):
        return "education_timing"
    timing_map = {
        "higher_education": "higher_education_timing",
        "exam_capacity": "exam_timing",
        "admission_capacity": "admission_timing",
        "research": "research_timing",
        "foreign_study": "foreign_study_timing",
    }
    if mode in TIMING_MODES and subtype in timing_map:
        return timing_map[subtype]
    return "education" if subtype == "overall" else subtype


def resolve_education_graph_inputs(*, intent: Mapping[str, Any] | None, context: Mapping[str, Any] | None, query_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    intent = intent if isinstance(intent, Mapping) else {}
    context = context if isinstance(context, Mapping) else {}
    plan = dict(query_plan or {})
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    plan.setdefault("education_subtype", intent.get("education_subtype") or summary.get("education_subtype"))
    return {
        "category": plan.get("category") or summary.get("category") or intent.get("category"),
        "query_plan": plan,
        "observed_answer_mode": plan.get("answer_mode") or summary.get("answer_mode") or intent.get("answer_mode"),
    }


def _present(value: Any) -> bool:
    return value not in (None, "", [], (), {})


def observed_education_factors(context: Mapping[str, Any], query_plan: Mapping[str, Any] | None = None) -> set[str]:
    factors: set[str] = set()
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    foundation = normalized.get("education_foundation") if isinstance(normalized.get("education_foundation"), Mapping) else {}
    availability = foundation.get("availability") if isinstance(foundation.get("availability"), Mapping) else {}
    if availability.get("d1"): factors.add("education:D1")
    if availability.get("d9"): factors.add("education:D9")
    if availability.get("d10"): factors.add("education:D10")
    if availability.get("d24"): factors.add("education:D24")
    for house in foundation.get("houses_available") or []:
        try: factors.add(f"education:H{int(house)}")
        except (TypeError, ValueError): pass
    flag_map = {
        "learning_significators": "education:LearningSignificators",
        "lord_nakshatra_chain": "education:LordNakshatraChain",
        "dignity_strength": "education:DignityStrength",
        "education_yogas": "education:EducationYogas",
        "kp_fructification": "education:KPFructification",
        "option_evidence": "education:OptionEvidence",
        "remedy_blueprint": "education:RemedyBlueprint",
    }
    for key, factor in flag_map.items():
        if availability.get(key): factors.add(factor)
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    if str(plan.get("answer_mode") or "").lower() in TIMING_MODES:
        dashas = context.get("current_dashas") if isinstance(context.get("current_dashas"), Mapping) else {}
        transits = context.get("current_transits") if isinstance(context.get("current_transits"), Mapping) else {}
        if _present(dashas.get("levels")) or _present(normalized.get("forward_event_dasha_scan")):
            factors.add("education:DashaActivation")
        if _present(transits.get("planets")) or _present(normalized.get("transit_activation_timeline")):
            factors.add("education:TransitConfirmation")
    return factors


def compare_education_graph_policy(*, category: Any, query_plan: Mapping[str, Any] | None, observed_answer_mode: Any, context: Mapping[str, Any], store: EducationGraphPolicyStore | None = None) -> dict[str, Any] | None:
    if not is_education_category(category): return None
    runtime_key = education_graph_runtime_key(category, query_plan)
    policy_store = store or default_education_graph_policy_store()
    policy = policy_store.resolve(str(runtime_key or ""))
    if policy is None:
        return {"ontology_version": policy_store.ontology_version, "runtime_key": runtime_key, "match": False, "mismatches": [{"kind": "missing_compiled_policy"}]}
    actual = observed_education_factors(context, query_plan)
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


def build_education_graph_route(comparison: Mapping[str, Any] | None) -> dict[str, Any] | None:
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
