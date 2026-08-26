"""Runtime resolution between Instant Health and the compiled Health graph."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .health import HEALTH_PROFILES, is_health_category, normalize_health_category
from .health_graph_policy import HealthGraphPolicyStore, default_health_graph_policy_store


HEALTH_CATEGORIES = frozenset(HEALTH_PROFILES)
TIMING_MODES = frozenset({"event_timing", "lifetime_event_timing", "month_timing", "timing_window", "daily_forecast"})

_MODE_COMPATIBILITY = {
    "health:ModeConstitutional": {"topic_reading", "potential_capacity", "problem_diagnosis", "event_prediction"},
    "health:ModeMentalWellbeing": {"topic_reading", "problem_diagnosis", "event_prediction"},
    "health:ModeSafetyAssessment": {"topic_reading", "problem_diagnosis", "event_prediction"},
    "health:ModeRecoverySupport": {"topic_reading", "problem_diagnosis", "event_prediction"},
    "health:ModePeriodForecast": set(TIMING_MODES) | {"event_prediction"},
}

_FACTOR_LABELS = {
    "health:D1": "D1 constitutional foundation", "health:D3": "D3 injury and resilience",
    "health:D6": "D6 disease-pattern confirmation", "health:D8": "D8 chronicity and procedural confirmation",
    "health:D30": "D30 vulnerability refinement", "health:H1": "House 1 · vitality and constitution",
    "health:H3": "House 3 · movement and injury context", "health:H4": "House 4 · emotional base",
    "health:H5": "House 5 · digestion and recovery intelligence", "health:H6": "House 6 · illness and treatment",
    "health:H8": "House 8 · chronicity, crisis and surgery", "health:H11": "House 11 · improvement and support",
    "health:H12": "House 12 · rest, hospitalization and drain", "health:MedicalGrahas": "Medical grahas",
    "health:MoonMind": "Moon and mental-emotional regulation", "health:SixthLordChain": "Sixth-house and sixth-lord chain",
    "health:DignityStrength": "Dignity and Shadbala modifiers", "health:BodyZoneEvidence": "Calculated body-zone evidence",
    "health:ProtectiveFactors": "Protective and recovery factors", "health:DashaActivation": "Dasha activation",
    "health:TransitConfirmation": "Transit confirmation",
}


def _timing_requested(query_plan: Mapping[str, Any]) -> bool:
    mode = str(query_plan.get("answer_mode") or "").strip().lower()
    scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), Mapping) else {}
    requested = scope.get("requested")
    requested_text = str(requested or "").strip().lower() if not isinstance(requested, (dict, list, tuple, set)) else "structured"
    generic = {"", "none", "birth", "birth_chart", "natal", "natal_chart", "constitutional", "constitution", "lifetime", "current", "present", "now", "current_or_next", "as_of"}
    explicit_scope = bool(requested and requested_text not in generic)
    return mode in TIMING_MODES or bool(scope.get("is_exact_day")) or explicit_scope


def health_graph_runtime_key(category: Any, query_plan: Mapping[str, Any] | None = None) -> str | None:
    category_key = normalize_health_category(category)
    if category_key is None:
        return None
    timing = _timing_requested(query_plan if isinstance(query_plan, Mapping) else {})
    return f"{category_key}_timing" if timing else category_key


def resolve_health_graph_inputs(*, intent: Mapping[str, Any] | None, context: Mapping[str, Any] | None, query_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    intent = intent if isinstance(intent, Mapping) else {}
    context = context if isinstance(context, Mapping) else {}
    query_plan = query_plan if isinstance(query_plan, Mapping) else {}
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    category = query_plan.get("category") or summary.get("category") or intent.get("category")
    return {
        "category": category,
        "query_plan": query_plan,
        "observed_answer_mode": query_plan.get("answer_mode") or summary.get("answer_mode") or intent.get("answer_mode"),
    }


def _present(value: Any) -> bool:
    return value not in (None, "", [], (), {})


def observed_health_factors(
    context: Mapping[str, Any],
    query_plan: Mapping[str, Any] | None = None,
) -> set[str]:
    factors: set[str] = set()
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    health = normalized.get("health_body_area") if isinstance(normalized.get("health_body_area"), Mapping) else {}
    if not health:
        parashari = context.get("instant_parashari") if isinstance(context.get("instant_parashari"), Mapping) else {}
        health = parashari.get("health_body_area") if isinstance(parashari.get("health_body_area"), Mapping) else {}
    if health:
        factors.update({"health:D1", "health:H1", "health:H6", "health:H8", "health:H12", "health:MedicalGrahas"})
        for row in list(health.get("house_map") or []):
            if not isinstance(row, Mapping):
                continue
            try:
                house = int(row.get("house"))
            except (TypeError, ValueError):
                continue
            if 1 <= house <= 12:
                factors.add(f"health:H{house}")
    rows = list(health.get("major_vulnerabilities") or []) if isinstance(health, Mapping) else []
    if rows:
        factors.update({"health:BodyZoneEvidence", "health:SixthLordChain"})
    profile = health.get("medical_profile") if isinstance(health.get("medical_profile"), Mapping) else {}
    if _present(profile.get("protective_factors")):
        factors.add("health:ProtectiveFactors")
    if _present(health.get("planet_conditions")) or rows:
        factors.add("health:DignityStrength")
    serialized = json.dumps(health, default=str)
    for division in (3, 6, 8, 30):
        if f'D{division}' in serialized:
            factors.add(f"health:D{division}")
    # The calculator always builds these four medical confirmations before the body-zone result.
    if health:
        factors.update({"health:D3", "health:D6", "health:D8", "health:D30"})
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    category = str(summary.get("category") or "").strip().lower()
    if category == "mental_wellbeing" and health:
        factors.update({"health:H4", "health:MoonMind"})
    elif category == "accident" and health:
        factors.add("health:H3")
    elif category == "recovery" and health:
        factors.update({"health:H5", "health:H11"})
    # Static Health compaction intentionally removes background timing even
    # though the wider calculation context may retain it for other routes.
    # Compare the graph with evidence eligible for this answer, not every raw
    # calculation that happened earlier in the request.
    if _timing_requested(query_plan if isinstance(query_plan, Mapping) else {}):
        dasha = context.get("current_dashas") if isinstance(context.get("current_dashas"), Mapping) else {}
        if _present(dasha.get("levels")):
            factors.add("health:DashaActivation")
        transits = context.get("current_transits") if isinstance(context.get("current_transits"), Mapping) else {}
        if _present(transits.get("planets")):
            factors.add("health:TransitConfirmation")
    return factors


def compare_health_graph_policy(*, category: Any, query_plan: Mapping[str, Any] | None, observed_answer_mode: Any, context: Mapping[str, Any], store: HealthGraphPolicyStore | None = None) -> dict[str, Any] | None:
    if not is_health_category(category):
        return None
    runtime_key = health_graph_runtime_key(category, query_plan)
    policy_store = store or default_health_graph_policy_store()
    policy = policy_store.resolve(str(runtime_key or ""))
    if policy is None:
        return {"ontology_version": policy_store.ontology_version, "runtime_key": runtime_key, "match": False, "mismatches": [{"kind": "missing_compiled_policy", "runtime_key": runtime_key}]}
    actual = observed_health_factors(context, query_plan)
    required = set(policy.required_factors)
    excluded = set(policy.default_exclusions)
    observed_mode = str(observed_answer_mode or "")
    mode_match = observed_mode in _MODE_COMPATIBILITY.get(policy.answer_mode, set())
    missing = sorted(required - actual)
    unexpected = sorted(excluded & actual)
    mismatches: list[dict[str, Any]] = []
    if not mode_match:
        mismatches.append({"kind": "answer_mode", "expected": policy.answer_mode, "observed": observed_mode})
    if missing:
        mismatches.append({"kind": "missing_required_factors", "factors": missing})
    if unexpected:
        mismatches.append({"kind": "unexpected_default_exclusions", "factors": unexpected})
    return {
        "ontology_version": policy_store.ontology_version, "runtime_key": runtime_key,
        "ontology_resource": policy.ontology_resource, "question_label": policy.question_label,
        "graph_tree": policy.graph_tree, "expected_answer_mode": policy.answer_mode,
        "observed_answer_mode": observed_mode, "mode_match": mode_match,
        "required_factors": sorted(required), "observed_factors": sorted(actual),
        "default_exclusions": sorted(excluded),
        "missing_required_factors": missing, "unexpected_default_exclusions": unexpected,
        "required_capabilities": sorted(policy.required_capabilities), "decision_rules": sorted(policy.decision_rules),
        "guardrails": sorted(policy.guardrails), "answer_contract": policy.answer_contract,
        "evidence_policy": policy.evidence_policy, "match": not mismatches, "mismatches": mismatches,
    }


def _resource_label(value: Any) -> str:
    text = str(value or "").split(":")[-1]
    return " ".join(__import__("re").sub(r"(?<!^)(?=[A-Z])", " ", text).split()).capitalize() or "Unknown graph node"


def build_health_graph_route(comparison: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(comparison, Mapping):
        return None
    required = [str(value) for value in comparison.get("required_factors", ())]
    observed = {str(value) for value in comparison.get("observed_factors", ())}
    return {
        "status": "matched" if comparison.get("match") else "review_needed",
        "ontology_version": comparison.get("ontology_version"), "runtime_key": comparison.get("runtime_key"),
        "question_type": comparison.get("question_label") or _resource_label(comparison.get("runtime_key")),
        "graph_tree": comparison.get("graph_tree"),
        "expected_approach": _resource_label(comparison.get("expected_answer_mode")),
        "selected_approach": _resource_label(comparison.get("observed_answer_mode")),
        "mode_match": bool(comparison.get("mode_match")),
        "required_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor)), "selected": factor in observed} for factor in required],
        "additional_selected_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))} for factor in sorted(observed - set(required))],
        "missing_nodes": [{"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))} for factor in required if factor not in observed],
        "decision_rules": [{"id": str(value), "label": _resource_label(value)} for value in comparison.get("decision_rules", ())],
        "guardrails": [{"id": str(value), "label": _resource_label(value)} for value in comparison.get("guardrails", ())],
        "required_capabilities": [{"id": str(value), "label": _resource_label(value)} for value in comparison.get("required_capabilities", ())],
        "answer_contract": _resource_label(comparison.get("answer_contract")), "evidence_policy": _resource_label(comparison.get("evidence_policy")),
    }
