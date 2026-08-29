"""Runtime resolution between Instant Wealth questions and the compiled graph."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .wealth_graph_policy import WealthGraphPolicyStore, default_wealth_graph_policy_store


WEALTH_ALIASES = {
    "wealth": "wealth", "finance": "wealth", "money": "wealth", "financial": "wealth",
    "income": "income", "salary": "income", "earnings": "income", "cashflow": "income",
    "debt": "debt", "loan": "debt", "loans": "debt", "borrowing": "debt",
    "investment": "investment", "investing": "investment", "trading": "investment",
    "speculation": "investment", "inheritance": "inheritance", "legacy": "inheritance",
}
TIMING_MODES = frozenset({"event_prediction", "event_timing", "lifetime_event_timing", "month_timing", "timing_window", "daily_forecast"})
WEALTH_SUBTYPE_CATEGORIES = {
    "source": "wealth",
    "savings_instability": "wealth",
    "multiple_income": "income",
    "debt_repayment": "debt",
    "loan_support": "debt",
    "loan_decision": "debt",
    "investing_vs_trading": "investment",
    "investment_risk": "investment",
    "loss_vulnerability": "investment",
    "windfall": "investment",
}

_MODE_COMPATIBILITY = {
    "wealth:ModeTopic": {"topic_reading", "trait_nature", "problem_diagnosis", "potential_capacity", "decision_support"},
    "wealth:ModeCapacity": {"topic_reading", "potential_capacity", "trait_nature"},
    "wealth:ModeDiagnosis": {"problem_diagnosis", "topic_reading"},
    "wealth:ModeTiming": set(TIMING_MODES),
    "wealth:ModeComparison": {"comparison_choice", "decision_support"},
    "wealth:ModeDecision": {"decision_support", "comparison_choice"} | set(TIMING_MODES),
    "wealth:ModeRemedy": {"remedy_action"},
}

_FACTOR_LABELS = {
    "wealth:D1": "D1 financial promise", "wealth:D2": "D2 Hora wealth confirmation",
    "wealth:D5": "D5 speculation refinement", "wealth:D8": "D8 inheritance and discontinuity",
    "wealth:D9": "D9 supporting carrier condition",
    "wealth:D10": "D10 earning channel", "wealth:LordNakshatraChain": "House-lord, nakshatra and dispositor chain",
    "wealth:DignityStrength": "Dignity and Shadbala modifiers", "wealth:DhanaYogas": "Operational Dhana yogas",
    "wealth:InduLagna": "Indu Lagna wealth potential", "wealth:HoraLagna": "Hora Lagna material manifestation",
    "wealth:ArudhaGains": "Second and eleventh from Arudha Lagna", "wealth:KPFructification": "KP financial fructification",
    "wealth:DashaActivation": "Dasha activation", "wealth:TransitConfirmation": "Transit confirmation",
    "wealth:RemedyBlueprint": "Calculated remedy blueprint",
}


def normalize_wealth_category(value: Any) -> str | None:
    return WEALTH_ALIASES.get(str(value or "").strip().lower())


def is_wealth_category(value: Any) -> bool:
    return normalize_wealth_category(value) is not None


def effective_wealth_category(category: Any, wealth_subtype: Any = None) -> str | None:
    """Resolve a typed Wealth subtype before a broad router category.

    The semantic subtype controls calculator selection. This keeps a broad
    ``wealth`` category from selecting the right graph node while calculating
    the wrong divisional chart or house set.
    """
    subtype = str(wealth_subtype or "").strip().lower()
    return WEALTH_SUBTYPE_CATEGORIES.get(subtype) or normalize_wealth_category(category)


def _timing_requested(query_plan: Mapping[str, Any]) -> bool:
    mode = str(query_plan.get("answer_mode") or "").strip().lower()
    scope = query_plan.get("time_scope") if isinstance(query_plan.get("time_scope"), Mapping) else {}
    # The semantic answer mode is authoritative. Descriptive scope such as
    # "long-term", "overall", "lifetime potential", or a router-supplied
    # open-future marker does not ask *when* something will happen. Promoting
    # any non-empty timeframe to timing caused static capacity, diagnosis and
    # suitability questions to demand dashas, KP and transits. A genuinely
    # bounded/date question must be routed to a timing mode (or exact-day).
    return mode in TIMING_MODES or bool(scope.get("is_exact_day"))


def wealth_graph_runtime_key(category: Any, query_plan: Mapping[str, Any] | None = None) -> str | None:
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    mode = str(plan.get("answer_mode") or "").strip().lower()
    subtype = str(plan.get("wealth_subtype") or "").strip().lower()
    category_key = effective_wealth_category(category, subtype)
    if category_key is None:
        return None
    if mode == "remedy_action":
        return "wealth_remedies"
    if category_key == "wealth":
        # The primary intent router can occasionally retain the broad Wealth
        # category while correctly resolving the semantic subtype.  Preserve
        # the more specific debt-repayment route instead of degrading a
        # payoff question to generic wealth timing.
        if subtype == "debt_repayment":
            return "debt_repayment" if _timing_requested(plan) else "debt"
        if subtype == "windfall": return "windfall"
        if subtype == "loss_vulnerability": return "loss_vulnerability"
        # Capacity describes the strength of the overall wealth promise unless
        # the semantic router explicitly identified a source/channel question.
        # Treating every capacity question as ``wealth_source`` made broad
        # questions such as long-term wealth potential drift into unsupported
        # salary-versus-business claims.
        if subtype == "source": return "wealth_source"
        if subtype == "multiple_income": return "multiple_income"
        if subtype == "savings_instability" or mode == "problem_diagnosis": return "wealth_diagnosis"
        return "wealth_timing" if _timing_requested(plan) else "wealth"
    if category_key == "income":
        if subtype == "multiple_income": return "multiple_income"
        return "income_timing" if _timing_requested(plan) else "income"
    if category_key == "debt":
        if mode == "problem_diagnosis": return "debt_diagnosis"
        if subtype == "debt_repayment": return "debt_repayment" if _timing_requested(plan) else "debt"
        if subtype == "loan_decision": return "loan_decision"
        # A generic question about loans or borrowing is a static natal debt
        # pattern. ``loan_support`` is the dated approval/support route and may
        # require dasha/transit evidence only when timing was actually asked.
        if subtype == "loan_support" and _timing_requested(plan): return "loan_support"
        return "debt_repayment" if _timing_requested(plan) else "debt"
    if category_key == "investment":
        if subtype == "windfall": return "windfall"
        if subtype == "investing_vs_trading" or mode == "comparison_choice": return "investing_vs_trading"
        if subtype == "loss_vulnerability": return "loss_vulnerability"
        if subtype == "investment_risk" or mode == "problem_diagnosis": return "investment_risk"
        return "investment_timing" if _timing_requested(plan) else "investment"
    return "inheritance_timing" if _timing_requested(plan) else "inheritance"


def resolve_wealth_graph_inputs(*, intent: Mapping[str, Any] | None, context: Mapping[str, Any] | None, query_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    intent = intent if isinstance(intent, Mapping) else {}
    context = context if isinstance(context, Mapping) else {}
    plan = dict(query_plan or {})
    summary = context.get("intent_summary") if isinstance(context.get("intent_summary"), Mapping) else {}
    plan.setdefault("wealth_subtype", intent.get("wealth_subtype") or summary.get("wealth_subtype"))
    return {
        "category": plan.get("category") or summary.get("category") or intent.get("category"),
        "query_plan": plan,
        "observed_answer_mode": plan.get("answer_mode") or summary.get("answer_mode") or intent.get("answer_mode"),
    }


def _present(value: Any) -> bool:
    return value not in (None, "", [], (), {})


def observed_wealth_factors(context: Mapping[str, Any], query_plan: Mapping[str, Any] | None = None) -> set[str]:
    factors: set[str] = set()
    normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
    foundation = normalized.get("wealth_foundation") if isinstance(normalized.get("wealth_foundation"), Mapping) else {}
    if foundation.get("d1_available"):
        factors.add("wealth:D1")
    for house in foundation.get("houses_available") or []:
        try: factors.add(f"wealth:H{int(house)}")
        except (TypeError, ValueError): pass
    availability = foundation.get("availability") if isinstance(foundation.get("availability"), Mapping) else {}
    flag_map = {
        "d2": "wealth:D2", "d5": "wealth:D5", "d8": "wealth:D8", "d9": "wealth:D9", "d10": "wealth:D10",
        "lord_nakshatra_chain": "wealth:LordNakshatraChain", "dignity_strength": "wealth:DignityStrength",
        "dhana_yogas": "wealth:DhanaYogas", "indu_lagna": "wealth:InduLagna", "hora_lagna": "wealth:HoraLagna",
        "arudha_gains": "wealth:ArudhaGains", "kp_fructification": "wealth:KPFructification",
        "remedy_blueprint": "wealth:RemedyBlueprint",
    }
    for key, factor in flag_map.items():
        if availability.get(key): factors.add(factor)
    plan = query_plan if isinstance(query_plan, Mapping) else {}
    if _timing_requested(plan):
        dashas = context.get("current_dashas") if isinstance(context.get("current_dashas"), Mapping) else {}
        transits = context.get("current_transits") if isinstance(context.get("current_transits"), Mapping) else {}
        if _present(dashas.get("levels")): factors.add("wealth:DashaActivation")
        if _present(transits.get("planets")): factors.add("wealth:TransitConfirmation")
    return factors


def compare_wealth_graph_policy(*, category: Any, query_plan: Mapping[str, Any] | None, observed_answer_mode: Any, context: Mapping[str, Any], store: WealthGraphPolicyStore | None = None) -> dict[str, Any] | None:
    if not is_wealth_category(category): return None
    runtime_key = wealth_graph_runtime_key(category, query_plan)
    policy_store = store or default_wealth_graph_policy_store()
    policy = policy_store.resolve(str(runtime_key or ""))
    if policy is None:
        return {"ontology_version": policy_store.ontology_version, "runtime_key": runtime_key, "match": False, "mismatches": [{"kind": "missing_compiled_policy"}]}
    actual, required, excluded = observed_wealth_factors(context, query_plan), set(policy.required_factors), set(policy.default_exclusions)
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


def build_wealth_graph_route(comparison: Mapping[str, Any] | None) -> dict[str, Any] | None:
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
