"""Runtime resolution between Instant Career and the compiled Career graph."""

from __future__ import annotations

from typing import Any, Mapping

from .career import is_career_category, normalize_career_subtype
from .career_graph_policy import CareerGraphPolicy, CareerGraphPolicyStore, default_career_graph_policy_store


_SUBTYPE_TO_RUNTIME_KEY = {
    "promotion_vs_job_change": "promotion_vs_job_change",
    "general": "general",
    "employment": "employment",
    "offer": "offer",
    "joining": "joining",
    "career_fit": "career_fit",
    "job_vs_business": "business_vs_employment",
    "job_change": "job_change_timing",
    "resignation": "resignation",
    "job_security": "job_security",
    "promotion": "promotion",
    "salary": "salary_increase",
    "business": "business",
    "business_launch": "business_launch",
    "business_success": "business_success",
    "project": "project",
    "leadership": "leadership",
    "government": "government",
    "foreign_career": "foreign_career",
    "return_to_work": "return_to_work",
    "recognition": "recognition",
    "career_stagnation": "career_stagnation",
    "manager_relationship": "manager_relationship",
    "colleague_relationship": "colleague_relationship",
    "subordinate_relationship": "subordinate_relationship",
    "client_relationship": "client_relationship",
    "business_partner_relationship": "business_partner_relationship",
    "mentor_relationship": "mentor_relationship",
    "workplace_conflict": "workplace_conflict",
}

_MODE_COMPATIBILITY = {
    "career:ModeTopicReading": {"topic_reading"},
    "career:ModePotentialCapacity": {"potential_capacity"},
    "career:ModeProblemDiagnosis": {"problem_diagnosis"},
    "career:ModeRelationshipReading": {"relationship_person"},
    # The existing lane splits a decision into a comparison/decision response
    # and an explicitly requested delivery window.  Both satisfy the graph's
    # higher-level DecisionSupport mode.
    "career:ModeDecisionSupport": {
        "topic_reading", "comparison_choice", "decision_support", "timing_window", "event_prediction"
    },
}

_QUESTION_TYPE_LABELS = {
    "general": "Overall career",
    "employment": "Employment and job search",
    "offer": "Specific job offer",
    "joining": "Job joining and start",
    "career_fit": "Suitable career direction",
    "business_vs_employment": "Job or business",
    "job_change_timing": "Job-change timing",
    "resignation": "Leaving the current job",
    "job_security": "Job security and continuity",
    "promotion": "Promotion",
    "promotion_vs_job_change": "Promotion versus job change",
    "salary_increase": "Salary or compensation increase",
    "business": "Business potential and operating profile",
    "business_launch": "Starting a business",
    "business_success": "Business success and growth",
    "project": "Professional project outcome",
    "leadership": "Leadership and management potential",
    "government": "Government or public-sector career",
    "foreign_career": "Foreign or overseas career",
    "return_to_work": "Return to work after a break",
    "recognition": "Recognition and career stagnation",
    "career_stagnation": "Career stagnation and blockage",
    "manager_relationship": "Relationship with manager",
    "colleague_relationship": "Relationship with colleague or peer",
    "subordinate_relationship": "Relationship with direct report or team member",
    "client_relationship": "Relationship with client or customer",
    "business_partner_relationship": "Relationship with business partner",
    "mentor_relationship": "Relationship with mentor or professional guide",
    "workplace_conflict": "Workplace conflict",
}

_FACTOR_LABELS = {
    "career:D1": "D1 birth-chart foundation",
    "career:D1Foundation": "D1 career foundation",
    "career:D10": "D10 career expression",
    "career:D10Confirmation": "D10 professional confirmation",
    "career:H1": "House 1 · professional capacity and identity",
    "career:H2": "House 2 · income and compensation",
    "career:H3": "House 3 · initiative and movement",
    "career:H5": "House 5 · judgment, strategy and creativity",
    "career:H6": "House 6 · employment, workload and competition",
    "career:H7": "House 7 · clients, business and agreements",
    "career:H8": "House 8 · disruption, restructuring and hidden pressure",
    "career:H9": "House 9 · manager, mentors and guidance",
    "career:H10": "House 10 · role, status and authority",
    "career:H11": "House 11 · gains and recognition",
    "career:H12": "House 12 · exit, release and separation",
    "career:Amatyakaraka": "Amatyakaraka · Jaimini vocational significator",
    "career:Karakamsha": "Karakamsha · soul-level vocation confirmation",
    "career:DashaActivation": "Dasha activation",
    "career:TransitActivation": "Transit confirmation",
}

_MODE_LABELS = {
    "career:ModeTopicReading": "Topic reading",
    "career:ModePotentialCapacity": "Potential and capacity",
    "career:ModeProblemDiagnosis": "Problem diagnosis",
    "career:ModeRelationshipReading": "Workplace relationship reading",
    "career:ModeDecisionSupport": "Decision support",
    "topic_reading": "Topic reading",
    "potential_capacity": "Potential and capacity",
    "problem_diagnosis": "Problem diagnosis",
    "relationship_person": "Workplace relationship reading",
    "comparison_choice": "Comparison and choice",
    "decision_support": "Decision support",
    "timing_window": "Timing window",
    "event_prediction": "Event prediction",
}


def _resource_label(value: Any) -> str:
    """Turn a compact ontology resource into a readable audit label."""
    text = str(value or "").split(":")[-1]
    if not text:
        return "Unknown graph node"
    words: list[str] = []
    current = text[0]
    for char in text[1:]:
        if char.isupper() and (not current[-1].isupper()):
            words.append(current)
            current = char
        else:
            current += char
    words.append(current)
    return " ".join(words).replace("  ", " ").strip().capitalize()


def career_graph_runtime_key(category: Any, routed_subtype: Any) -> str | None:
    """Resolve an existing structured Career route to the PoC graph key."""
    if not is_career_category(category):
        return None
    if str(routed_subtype or "").strip() == "promotion_vs_job_change":
        return "promotion_vs_job_change"
    subtype = normalize_career_subtype(category, routed_subtype)
    return _SUBTYPE_TO_RUNTIME_KEY.get(subtype)


def resolve_career_graph_inputs(
    *,
    intent: Mapping[str, Any] | None,
    context: Mapping[str, Any] | None,
    query_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve graph inputs from the *finished* route and compact context.

    The event-prediction lane builds an authoritative compact career
    foundation after the early intent-router pass.  That final foundation is
    therefore the source of truth for the graph subtype; relying only on the
    router's early ``career_subtype`` silently dropped graph traces for valid
    routes such as promotion.
    """
    intent = intent if isinstance(intent, Mapping) else {}
    context = context if isinstance(context, Mapping) else {}
    query_plan = query_plan if isinstance(query_plan, Mapping) else {}
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    parashari = context.get("instant_parashari") if isinstance(context.get("instant_parashari"), Mapping) else {}
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    foundation = parashari.get("career_foundation") if isinstance(parashari.get("career_foundation"), Mapping) else {}
    if not foundation and isinstance(normalized.get("career_foundation"), Mapping):
        foundation = normalized.get("career_foundation")

    category = (
        query_plan.get("category")
        or summary.get("category")
        or intent.get("category")
        or "general"
    )
    routed_subtype = (
        foundation.get("career_subtype")
        or query_plan.get("career_subtype")
        or summary.get("career_subtype")
        or intent.get("career_subtype")
    )
    comparison_profiles = {
        str(row.get("event_profile") or "").strip().lower()
        for row in (query_plan.get("comparison_options") or [])
        if isinstance(row, Mapping)
    }
    if str(query_plan.get("answer_mode") or "") == "comparison_choice" and {
        "promotion", "job_change"
    }.issubset(comparison_profiles):
        routed_subtype = "promotion_vs_job_change"
    observed_answer_mode = (
        query_plan.get("answer_mode")
        or summary.get("answer_mode")
        or intent.get("answer_mode")
    )
    return {
        "category": category,
        "routed_subtype": routed_subtype,
        "observed_answer_mode": observed_answer_mode,
    }


def _present(value: Any) -> bool:
    return value not in (None, "", [], (), {})


def observed_career_factors(context: Mapping[str, Any]) -> set[str]:
    """Describe only independently observable factors in the finished context."""
    factors: set[str] = set()
    parashari = context.get("instant_parashari") if isinstance(context.get("instant_parashari"), Mapping) else {}
    foundation = parashari.get("career_foundation") if isinstance(parashari.get("career_foundation"), Mapping) else {}

    d1 = foundation.get("D1") if isinstance(foundation.get("D1"), Mapping) else {}
    d1_rows = d1.get("houses") if isinstance(d1.get("houses"), list) else []
    if d1_rows:
        factors.add("career:D1")
        for row in d1_rows:
            if isinstance(row, Mapping):
                try:
                    house = int(row.get("house"))
                except (TypeError, ValueError):
                    continue
                if 1 <= house <= 12:
                    factors.add(f"career:H{house}")

    if _present(foundation.get("D10")):
        factors.add("career:D10")
    if _present(foundation.get("amatyakaraka")):
        factors.add("career:Amatyakaraka")
    if _present(foundation.get("KARAKAMSHA")):
        factors.add("career:Karakamsha")

    dashas = context.get("current_dashas") if isinstance(context.get("current_dashas"), Mapping) else {}
    if _present(dashas.get("levels")):
        factors.add("career:DashaActivation")
    transits = context.get("current_transits") if isinstance(context.get("current_transits"), Mapping) else {}
    if _present(transits.get("planets")):
        factors.add("career:TransitActivation")

    # A comparison route calculates each option against its own house set.
    # Those option rows are authoritative evidence that the corresponding
    # graph factors were evaluated, even when the compact career-foundation
    # snapshot contains only the primary option's houses.
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    option_comparison = normalized.get("option_comparison") if isinstance(normalized.get("option_comparison"), Mapping) else {}
    comparison = option_comparison.get("comparison") if isinstance(option_comparison.get("comparison"), Mapping) else option_comparison
    verdict = context.get("_graph_packet_verdict") if isinstance(context.get("_graph_packet_verdict"), Mapping) else {}
    rationale = verdict.get("rationale") if isinstance(verdict.get("rationale"), Mapping) else {}
    option_rows = list(comparison.get("options") or []) + list(rationale.get("options") or [])
    for option in option_rows:
        if not isinstance(option, Mapping):
            continue
        for value in option.get("native_calculation_houses") or []:
            try:
                house = int(value)
            except (TypeError, ValueError):
                continue
            if 1 <= house <= 12:
                factors.add(f"career:H{house}")
    return factors


def compare_career_graph_policy(
    *,
    category: Any,
    routed_subtype: Any,
    observed_answer_mode: Any,
    context: Mapping[str, Any],
    store: CareerGraphPolicyStore | None = None,
) -> dict[str, Any] | None:
    """Evaluate the final Career route against its compiled policy."""
    if not is_career_category(category):
        return None
    runtime_key = career_graph_runtime_key(category, routed_subtype)
    if runtime_key is None:
        subtype = normalize_career_subtype(category, routed_subtype)
        return {
            "ontology_version": None,
            "runtime_key": None,
            "career_subtype": subtype,
            "match": False,
            "mismatches": [{"kind": "unmapped_runtime_route", "career_subtype": subtype}],
        }
    policy_store = store or default_career_graph_policy_store()
    policy: CareerGraphPolicy | None = policy_store.resolve(runtime_key)
    if policy is None:
        return {
            "ontology_version": policy_store.ontology_version,
            "runtime_key": runtime_key,
            "career_subtype": normalize_career_subtype(category, routed_subtype),
            "match": False,
            "mismatches": [{"kind": "missing_compiled_policy", "runtime_key": runtime_key}],
        }

    observed_mode = str(observed_answer_mode or "")
    compatible_modes = _MODE_COMPATIBILITY.get(policy.answer_mode, set())
    actual = observed_career_factors(context)
    required = set(policy.required_factors)
    excluded = set(policy.default_exclusions)
    missing = sorted(required - actual)
    unexpected_excluded = sorted(excluded & actual)
    mode_match = observed_mode in compatible_modes

    mismatches: list[dict[str, Any]] = []
    if not mode_match:
        mismatches.append({
            "kind": "answer_mode",
            "expected": policy.answer_mode,
            "compatible_runtime_modes": sorted(compatible_modes),
            "observed": observed_mode,
        })
    if missing:
        mismatches.append({"kind": "missing_required_factors", "factors": missing})
    if unexpected_excluded:
        mismatches.append({"kind": "unexpected_default_exclusions", "factors": unexpected_excluded})

    return {
        "ontology_version": policy_store.ontology_version,
        "runtime_key": runtime_key,
        "career_subtype": normalize_career_subtype(category, routed_subtype),
        "ontology_resource": policy.ontology_resource,
        "question_label": policy.question_label,
        "graph_tree": policy.graph_tree,
        "expected_answer_mode": policy.answer_mode,
        "observed_answer_mode": observed_mode,
        "mode_match": mode_match,
        "required_factors": sorted(required),
        "default_exclusions": sorted(excluded),
        "observed_factors": sorted(actual),
        "missing_required_factors": missing,
        "unexpected_default_exclusions": unexpected_excluded,
        "required_capabilities": sorted(policy.required_capabilities),
        "decision_rules": sorted(policy.decision_rules),
        "guardrails": sorted(policy.guardrails),
        "answer_contract": policy.answer_contract,
        "evidence_policy": policy.evidence_policy,
        "match": not mismatches,
        "mismatches": mismatches,
    }


def build_career_graph_route(comparison: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Create the human-readable route attached to the live answer contract."""
    if not isinstance(comparison, Mapping):
        return None
    required = [str(value) for value in comparison.get("required_factors", ())]
    observed = {str(value) for value in comparison.get("observed_factors", ())}
    required_set = set(required)
    return {
        "status": "matched" if comparison.get("match") else "review_needed",
        "ontology_version": comparison.get("ontology_version"),
        "runtime_key": comparison.get("runtime_key"),
        "question_type": str(comparison.get("question_label") or _QUESTION_TYPE_LABELS.get(
            str(comparison.get("runtime_key") or ""),
            _resource_label(comparison.get("runtime_key")),
        )),
        "graph_tree": comparison.get("graph_tree"),
        "expected_approach": _MODE_LABELS.get(
            str(comparison.get("expected_answer_mode") or ""),
            _resource_label(comparison.get("expected_answer_mode")),
        ),
        "selected_approach": _MODE_LABELS.get(
            str(comparison.get("observed_answer_mode") or ""),
            _resource_label(comparison.get("observed_answer_mode")),
        ),
        "mode_match": bool(comparison.get("mode_match")),
        "required_nodes": [
            {
                "id": factor,
                "label": _FACTOR_LABELS.get(factor, _resource_label(factor)),
                "selected": factor in observed,
            }
            for factor in required
        ],
        "additional_selected_nodes": [
            {"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))}
            for factor in sorted(observed - required_set)
        ],
        "missing_nodes": [
            {"id": factor, "label": _FACTOR_LABELS.get(factor, _resource_label(factor))}
            for factor in required
            if factor not in observed
        ],
        "decision_rules": [
            {"id": str(value), "label": _resource_label(value)}
            for value in comparison.get("decision_rules", ())
        ],
        "guardrails": [
            {"id": str(value), "label": _resource_label(value)}
            for value in comparison.get("guardrails", ())
        ],
        "required_capabilities": [
            {"id": str(value), "label": _resource_label(value)}
            for value in comparison.get("required_capabilities", ())
        ],
        "answer_contract": _resource_label(comparison.get("answer_contract")),
        "evidence_policy": _resource_label(comparison.get("evidence_policy")),
    }
