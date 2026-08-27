"""Live knowledge-graph policy enforcement for supported Instant domains.

The domain adapters still calculate parity details, but this module promotes
the resolved policy into the authoritative packet before answer generation.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Callable, Mapping

from .career import is_career_category
from .career_graph_runtime import (
    build_career_graph_route,
    compare_career_graph_policy,
    resolve_career_graph_inputs,
)
from .health_graph_runtime import (
    build_health_graph_route,
    compare_health_graph_policy,
    is_health_category,
    resolve_health_graph_inputs,
)
from .marriage_graph_runtime import (
    build_marriage_graph_route,
    compare_marriage_graph_policy,
    is_marriage_graph_request,
    resolve_marriage_graph_inputs,
)
from .wealth_graph_runtime import (
    build_wealth_graph_route,
    compare_wealth_graph_policy,
    is_wealth_category,
    resolve_wealth_graph_inputs,
)


LOGGER = logging.getLogger(__name__)


def _output_sections(graph_tree: Any) -> list[dict[str, str]]:
    if not isinstance(graph_tree, Mapping):
        return []
    questions = graph_tree.get("children")
    if not isinstance(questions, list) or not questions:
        return []
    question = questions[0] if isinstance(questions[0], Mapping) else {}
    relations = question.get("children") if isinstance(question.get("children"), list) else []
    contract_relation = next(
        (row for row in relations if isinstance(row, Mapping) and row.get("label") == "Answer contract"),
        None,
    )
    contracts = contract_relation.get("children") if isinstance(contract_relation, Mapping) else []
    contract = contracts[0] if isinstance(contracts, list) and contracts and isinstance(contracts[0], Mapping) else {}
    branches = contract.get("children") if isinstance(contract.get("children"), list) else []
    sections_branch = next(
        (row for row in branches if isinstance(row, Mapping) and row.get("label") == "Output sections"),
        None,
    )
    sections = sections_branch.get("children") if isinstance(sections_branch, Mapping) else []
    return [
        {"id": str(row.get("id")), "label": str(row.get("label"))}
        for row in sections
        if isinstance(row, Mapping) and row.get("id") and row.get("label")
    ]


def _live_contract(domain: str, comparison: Mapping[str, Any], review: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "live": True,
        "enforcement": "authoritative_pre_generation",
        "domain": domain,
        "ontology_version": comparison.get("ontology_version"),
        "runtime_key": comparison.get("runtime_key"),
        "ontology_resource": comparison.get("ontology_resource"),
        "question_type": comparison.get("question_label"),
        "expected_answer_mode": comparison.get("expected_answer_mode"),
        "mode_match": bool(comparison.get("mode_match")),
        "evidence_status": "complete" if comparison.get("match") else "incomplete_or_conflicting",
        "required_factors": list(comparison.get("required_factors") or []),
        "observed_factors": list(comparison.get("observed_factors") or []),
        "missing_required_factors": list(comparison.get("missing_required_factors") or []),
        "default_exclusions": list(comparison.get("default_exclusions") or []),
        "unexpected_default_exclusions": list(comparison.get("unexpected_default_exclusions") or []),
        "required_capabilities": list(comparison.get("required_capabilities") or []),
        "decision_rules": list(comparison.get("decision_rules") or []),
        "guardrails": list(comparison.get("guardrails") or []),
        "answer_contract": comparison.get("answer_contract"),
        "evidence_policy": comparison.get("evidence_policy"),
        "required_output_sections": _output_sections(comparison.get("graph_tree")),
        "instruction": (
            "This compiled graph route is authoritative. Follow its decision rules, guardrails and output "
            "sections; never use default-excluded factors. Treat missing required factors as unavailable "
            "evidence and do not make a conclusion that depends on them."
        ),
        "route": dict(review),
    }


def resolve_live_graph_policy(
    *,
    intent: Mapping[str, Any] | None,
    context: Mapping[str, Any] | None,
    query_plan: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Resolve exactly one supported domain policy from the final query plan."""
    context = context if isinstance(context, Mapping) else {}
    query_plan = query_plan if isinstance(query_plan, Mapping) else {}
    intent = intent if isinstance(intent, Mapping) else {}
    category = query_plan.get("category") or (context.get("intent_summary") or {}).get("category") or intent.get("category")

    resolver: Callable[..., dict[str, Any]]
    comparator: Callable[..., dict[str, Any] | None]
    reviewer: Callable[[Mapping[str, Any] | None], dict[str, Any] | None]
    domain: str
    wealth_subtype = str(
        query_plan.get("wealth_subtype")
        or (context.get("intent_summary") or {}).get("wealth_subtype")
        or intent.get("wealth_subtype")
        or ""
    ).strip().lower()
    prefer_wealth_graph = wealth_subtype in {
        "source", "savings_instability", "multiple_income", "debt_repayment",
        "loan_support", "investing_vs_trading", "investment_risk",
        "loss_vulnerability", "windfall",
    }
    # ``income`` is shared vocabulary with the Career salary route. A typed
    # Wealth subtype is the more specific domain signal and must win before
    # the broad Career alias check.
    if prefer_wealth_graph and is_wealth_category(category):
        domain, resolver, comparator, reviewer = (
            "wealth", resolve_wealth_graph_inputs, compare_wealth_graph_policy, build_wealth_graph_route,
        )
    elif is_career_category(category):
        domain, resolver, comparator, reviewer = (
            "career", resolve_career_graph_inputs, compare_career_graph_policy, build_career_graph_route,
        )
    elif is_health_category(category):
        domain, resolver, comparator, reviewer = (
            "health", resolve_health_graph_inputs, compare_health_graph_policy, build_health_graph_route,
        )
    elif is_marriage_graph_request(category, query_plan):
        domain, resolver, comparator, reviewer = (
            "marriage", resolve_marriage_graph_inputs, compare_marriage_graph_policy, build_marriage_graph_route,
        )
    elif is_wealth_category(category):
        domain, resolver, comparator, reviewer = (
            "wealth", resolve_wealth_graph_inputs, compare_wealth_graph_policy, build_wealth_graph_route,
        )
    else:
        return None

    try:
        inputs = resolver(intent=intent, context=context, query_plan=query_plan)
        comparison = comparator(**inputs, context=context)
        review = reviewer(comparison)
        if not isinstance(comparison, Mapping) or not isinstance(review, Mapping):
            raise RuntimeError(f"No compiled {domain} graph route resolved")
        review = dict(review)
        review["live"] = True
        review["enforcement"] = "authoritative_pre_generation"
        return _live_contract(domain, comparison, review)
    except Exception as exc:
        LOGGER.exception("INSTANT_GRAPH_LIVE_RESOLUTION_FAILED domain=%s", domain)
        return {
            "live": False,
            "enforcement": "fallback_non_graph",
            "domain": domain,
            "evidence_status": "graph_unavailable",
            "error": f"{type(exc).__name__}: {exc}",
        }


def apply_live_graph_policy(
    packet: dict[str, Any],
    *,
    intent: Mapping[str, Any] | None,
    context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Attach a live graph contract to the packet before composer generation."""
    result = dict(packet or {})
    query_plan = dict(result.get("query_plan") or {})
    graph_context = dict(context or {})
    # The fused verdict owns option-specific comparison rows.  Make that
    # adjudicated evidence visible to the graph comparator without copying it
    # into the legacy normalized context.
    graph_context["_graph_packet_verdict"] = result.get("verdict") or {}
    policy = resolve_live_graph_policy(intent=intent, context=graph_context, query_plan=query_plan)
    if policy is None:
        return result

    result["knowledge_graph_policy"] = policy
    query_plan["knowledge_graph_route"] = {
        key: policy.get(key)
        for key in ("live", "domain", "runtime_key", "ontology_resource", "ontology_version", "enforcement")
        if policy.get(key) is not None
    }
    result["query_plan"] = query_plan

    answer_spec = dict(result.get("answer_spec") or {})
    compact_policy = {
        key: value for key, value in policy.items() if key != "route"
    }
    missing = [str(value) for value in policy.get("missing_required_factors") or []]
    timing_missing = [
        value for value in missing
        if any(marker in value.lower() for marker in ("dasha", "transit", "kp"))
    ]
    time_bound_mode = str(query_plan.get("answer_mode") or "") in {
        "event_prediction", "timing_window", "event_timing"
    } or bool(
        policy.get("domain") == "wealth"
        and policy.get("runtime_key") in {
            "wealth_timing", "income_timing", "debt_repayment",
            "loan_support", "investment_timing", "inheritance_timing",
        }
    )
    love_arranged_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "love_arranged_marriage"
    )
    spouse_meeting_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_meeting"
    )
    spouse_profile_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_profile"
    )
    spouse_appearance_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_appearance"
    )
    spouse_location_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "spouse_location"
    )
    marriage_remedy_route = bool(
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "marriage_remedies"
    )
    wealth_route = policy.get("domain") == "wealth"
    # Career option comparisons use calculated future option windows.  Love
    # versus arranged marriage is a static natal-pathway comparison, so it
    # must never inherit that timing-based winner machinery.
    comparison_mode = bool(
        str(query_plan.get("answer_mode") or "") == "comparison_choice"
        and not love_arranged_route
        and not (
            policy.get("domain") == "wealth"
            and policy.get("runtime_key") == "investing_vs_trading"
        )
    )
    verdict_missing = {
        str(value) for value in (result.get("verdict") or {}).get("missing_required_capabilities") or []
    }
    if policy.get("domain") == "health" and "parashari.health_body_area" in verdict_missing:
        compact_policy["claim_permission"] = "no_health_area_specificity"
        compact_policy["instruction"] = (
            "The required health body-area calculation is unavailable. Do not name a body zone, organ, system, "
            "symptom pattern, recovery theme, dasha, transit, date, or relative risk window. Give a concise "
            "evidence limitation and general preventive guidance only."
        )
        answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and wealth_route:
        runtime_key = str(policy.get("runtime_key") or "")
        normalized = context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"), Mapping) else {}
        wealth_foundation = normalized.get("wealth_foundation") if isinstance(normalized.get("wealth_foundation"), Mapping) else {}
        wealth_adjudication = (
            dict(wealth_foundation.get("route_adjudication"))
            if isinstance(wealth_foundation.get("route_adjudication"), Mapping)
            else {}
        )
        route_focus = {
            "wealth": "overall wealth potential, accumulation and retention",
            "wealth_source": "primary wealth-building channels",
            "wealth_diagnosis": "savings instability and financial leakage",
            "wealth_timing": "wealth-growth timing",
            "income": "income and cash-flow stability",
            "income_timing": "income-growth timing",
            "multiple_income": "capacity for multiple income streams",
            "debt": "debt and borrowing pattern",
            "debt_diagnosis": "persistent debt mechanism",
            "debt_repayment": "debt-repayment timing",
            "loan_support": "loan-support timing and conditions",
            "investing_vs_trading": "long-term investing versus active trading suitability",
            "investment": "investment and speculation suitability",
            "investment_timing": "investment-support timing",
            "investment_risk": "investment volatility and risk mechanism",
            "loss_vulnerability": "financial-loss vulnerability",
            "inheritance": "inheritance and settlement potential",
            "inheritance_timing": "inheritance or settlement timing",
            "windfall": "sudden-gain potential and retention",
            "wealth_remedies": "calculated financial remedy",
        }.get(runtime_key, "the requested financial timing or decision")
        is_static_wealth = runtime_key not in {
            "wealth_timing", "income_timing", "debt_repayment",
            "loan_support", "investment_timing", "inheritance_timing",
        }
        investment_family = runtime_key in {
            "investment", "investing_vs_trading", "investment_timing",
            "investment_risk", "loss_vulnerability", "windfall",
        }
        wealth_answer_rules = {
            "runtime_key": runtime_key,
            "scope": route_focus,
            "static_route": is_static_wealth,
            "primary_evidence": "evidence.wealth_foundation",
            "route_adjudication": wealth_adjudication,
            "investment_synthesis": (
                dict(wealth_foundation.get("investment_synthesis"))
                if investment_family and isinstance(wealth_foundation.get("investment_synthesis"), Mapping)
                else {}
            ),
            "wealth_source_synthesis": (
                dict(wealth_foundation.get("wealth_source_synthesis"))
                if runtime_key in {"wealth_source", "multiple_income"} and isinstance(wealth_foundation.get("wealth_source_synthesis"), Mapping)
                else {}
            ),
            "multiple_income_synthesis": (
                dict(wealth_foundation.get("multiple_income_synthesis"))
                if runtime_key == "multiple_income" and isinstance(wealth_foundation.get("multiple_income_synthesis"), Mapping)
                else {}
            ),
            "loss_vulnerability_synthesis": (
                dict(wealth_foundation.get("loss_vulnerability_synthesis"))
                if runtime_key == "loss_vulnerability" and isinstance(wealth_foundation.get("loss_vulnerability_synthesis"), Mapping)
                else {}
            ),
            "wealth_growth_timing_synthesis": (
                dict(wealth_foundation.get("wealth_growth_timing_synthesis"))
                if runtime_key == "wealth_timing" and isinstance(wealth_foundation.get("wealth_growth_timing_synthesis"), Mapping)
                else {}
            ),
            "required_answer_order": [
                "direct route-specific financial verdict",
                (
                    "D1 promise, complete fifth-lord/carrier condition, D2 retention, D5 refinement and supporting D9 qualification"
                    if investment_family
                    else "D1 promise and D2 Hora confirmation or qualification"
                ),
                "route-specific financial mechanism from the required houses and divisional chart",
                "earning or gain capacity separated from savings, retention, liabilities and loss exposure",
                (
                    "Indu Lagna, Hora Lagna and Arudha manifestation as supporting evidence"
                    if is_static_wealth
                    else "dasha permission followed by dated transit confirmation within the requested horizon"
                ),
                "one practical non-prescriptive takeaway",
            ],
            "factor_precedence": [
                "D1 establishes financial promise.",
                "D2 confirms or qualifies accumulation and retention.",
                "Route-specific houses and D5, D8 or D10 answer only their authorized question.",
                (
                    "For investment routes, D5 refines speculative judgment and D9 qualifies the underlying carriers; D9 cannot replace D1, D2 or D5."
                    if investment_family
                    else "D9 is not a substitute for the Wealth route's required divisional evidence."
                ),
                "Judge every relevant lord as a combined carrier: placement, dignity, strength, Gandanta, special lordships, conjunctions and declared overlap rules.",
                "Dhana yogas must be operational through actual lords and placements, not merely named.",
                "Indu Lagna, Hora Lagna and Arudha are manifestation support and cannot override D1/D2.",
                "Dasha and transit may time an established promise but cannot create one.",
            ],
            "forbidden_moves": [
                (
                    "Do not use D9 as a standalone Wealth confirmation; on investment routes it may only qualify the supplied D1/D2/D5 carrier evidence."
                    if investment_family
                    else "Do not use D9 as the Wealth confirmation chart; D2 is mandatory."
                ),
                "Do not judge investment or speculation from the fifth lord's destination alone; include every supplied carrier condition and contradiction.",
                (
                    "For an investment route, state the calculated investment_synthesis verdict and actual fifth-lord, D2, D5 and D9 evidence; never say these factors merely 'need to be weighed'."
                    if investment_family
                    else "Do not introduce investment suitability unless the selected route asks for it."
                ),
                "Do not say a natal house is active or activated on a static route; use supports, challenges, strengthens, weakens, connects, occupies or aspects.",
                "Do not call the result a clear yes unless the supplied D1 and D2 synthesis actually supports that strength.",
                "Do not infer salary/service, business, speculation, debt, expenses, inheritance or windfall unless the selected route and supplied evidence support it.",
                "For wealth_source, name and rank the supplied concrete earning channels; savings automation, budgeting and retention discipline are qualifications, not wealth sources.",
                "For multiple_income, answer yes or no from multiple_income_synthesis and name the supplied primary and secondary streams; do not replace them with generic diversification or savings advice.",
                "For loss_vulnerability, rank the supplied loss mechanisms and distinguish volatility, retention leakage and shared-liability exposure; do not answer as generic investment suitability.",
                "Do not let Gandanta, Dagdha Rashi or another special factor replace the D1/D2 synthesis; use it only as a connected modifier.",
                "Do not turn a numerical wealth score into certainty or quote it as a probability.",
                "D2 availability is not a positive verdict; use only wealth_foundation.d2_synthesis.verdict to say whether it confirms or qualifies retention.",
                "When route_adjudication.strength_claim_permission is qualified_only, do not call the foundation strong, genuinely strong, clear, confirmed or unqualified.",
                "Do not infer creativity, beauty, luxury, profession or income channel from Indu Lagna's sign or lord alone.",
                "Do not describe the fifth house as the house of gains. The fifth governs judgment, speculation and investment intelligence; gains belong primarily to the eleventh.",
                "Do not mention current dasha, transit, dates, peaks or current activation on a static route.",
                "Do not use Rahu or Ketu fifth/ninth aspects.",
            ],
        }
        compact_policy["financial_safety_rules"] = {
            "scope": "astrological financial tendencies and timing; not regulated financial advice",
            "required_order": [
                "direct chart-based verdict",
                "promise or capacity evidence",
                "retention and risk qualification",
                "practical non-prescriptive takeaway",
            ],
            "forbidden_moves": [
                "Do not guarantee wealth, returns, profit, inheritance, loan approval, or freedom from loss.",
                "Do not recommend a named security, asset, leverage level, trade, lender, or transaction.",
                "Do not infer timing from natal promise or Indu Lagna alone.",
                "Do not use dasha or transit language on a static route.",
                "Do not treat Indu Lagna as an exact-degree point or as overriding D1 and D2.",
                "Do not describe Rahu or Ketu fifth/ninth aspects; node activation is occupation, conjunction, or seventh aspect only.",
                "Do not predict another person's death in an inheritance answer.",
            ],
        }
        compact_policy["instruction"] = (
            "Synthesize only the supplied Wealth foundation in the graph's decision order. Generic natal-promise "
            "or D9 evidence cannot replace D1 and D2; investment routes may use supplied D9 only as a carrier "
            "qualification after D5. Separate earning capacity, retention, risk and timing. "
            "Follow wealth_answer_rules and financial_safety_rules exactly."
        )
        compact_policy["wealth_answer_rules"] = wealth_answer_rules
        compact_policy["wealth_adjudication"] = wealth_adjudication
        answer_spec["financial_safety_rules"] = compact_policy["financial_safety_rules"]
        answer_spec["wealth_answer_rules"] = wealth_answer_rules
        if runtime_key == "wealth_timing":
            growth_synthesis = (
                dict(wealth_foundation.get("wealth_growth_timing_synthesis"))
                if isinstance(wealth_foundation.get("wealth_growth_timing_synthesis"), Mapping)
                else {}
            )
            growth_windows = [
                dict(row) for row in list(growth_synthesis.get("ranked_growth_windows") or [])
                if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
            ]
            compact_policy["wealth_growth_timing_synthesis"] = growth_synthesis
            wealth_answer_rules["wealth_growth_timing_synthesis"] = growth_synthesis
            wealth_answer_rules["forbidden_moves"].extend([
                "Do not call the current/as-of date or current dasha boundary the next wealth-growth period.",
                "Do not equate financial activity, house 5, Rahu opportunity or a high generic event score with realized wealth growth.",
                "Lead with the earliest supplied future meaningful-growth phase; name the stronger later phase separately when supplied.",
                "Do not claim an exact gain, transaction or windfall date; present the supplied broad support windows.",
            ])
            if growth_synthesis.get("forecast_kind") == "bounded_period_support_forecast":
                wealth_answer_rules["forbidden_moves"].extend([
                    "Do not apply the open-future event threshold to a bounded month, quarter or year forecast.",
                    "Do not refuse a bounded forecast when bounded_period_synthesis maps stronger, secondary and lower-support months.",
                    "Do not collapse the requested calendar period into one dasha boundary; cover its full chronological progression.",
                ])
            verdict = dict(result.get("verdict") or {})
            verdict["direction"] = (
                "bounded_wealth_support_forecast"
                if growth_synthesis.get("forecast_kind") == "bounded_period_support_forecast"
                else "future_wealth_growth_phases"
                if growth_windows else "insufficient_future_wealth_growth_evidence"
            )
            verdict["ranked_windows"] = growth_windows
            verdict["rationale"] = {
                "source": "wealth_foundation.wealth_growth_timing_synthesis",
                "current_window_assessment": growth_synthesis.get("current_window_assessment"),
                "partial_support_windows": growth_synthesis.get("partial_support_windows"),
                "claim_rule": growth_synthesis.get("claim_rule"),
            }
            result["verdict"] = verdict
            event_rules = dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"] = growth_windows
            event_rules["required_material_windows"] = growth_windows[:2]
            event_rules["window_answer_rule"] = growth_synthesis.get("claim_rule")
            answer_spec["event_rules"] = event_rules
            if (
                not growth_windows
                and growth_synthesis.get("forecast_kind") != "bounded_period_support_forecast"
                and not timing_missing
            ):
                compact_policy["claim_permission"] = "no_ranked_wealth_growth_window"
                compact_policy["instruction"] = (
                    "No route-adjudicated future wealth-growth phase is available. Do not turn the current date, "
                    "financial activity or a dasha boundary into growth timing."
                )
        if runtime_key == "debt_repayment":
            debt_synthesis = (
                dict(wealth_foundation.get("debt_repayment_synthesis"))
                if isinstance(wealth_foundation.get("debt_repayment_synthesis"), Mapping)
                else {}
            )
            repayment_windows = [
                dict(row) for row in list(debt_synthesis.get("ranked_repayment_windows") or [])
                if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
            ]
            compact_policy["debt_repayment_synthesis"] = debt_synthesis
            wealth_answer_rules["debt_repayment_synthesis"] = debt_synthesis
            wealth_answer_rules["forbidden_moves"].extend([
                "Do not call the current/as-of date a repayment marker merely because a current dasha segment begins there.",
                "Debt, eighth-house or twelfth-house activation is pressure/activity, not repayment support by itself.",
                "Do not claim an exact payoff or debt-free date; present only the supplied broad repayment-support windows.",
                "Do not prescribe consolidation, refinancing, highest-interest-first repayment or another financial strategy unless the user explicitly asks for practical financial guidance.",
            ])
            compact_policy["financial_safety_rules"]["forbidden_moves"].append(
                "Do not prescribe debt consolidation, refinancing or a repayment ordering in an astrology answer."
            )
            verdict = dict(result.get("verdict") or {})
            verdict["direction"] = (
                "probable_repayment_support_windows"
                if repayment_windows else "insufficient_debt_repayment_timing_evidence"
            )
            verdict["ranked_windows"] = repayment_windows
            verdict["rationale"] = {
                "source": "wealth_foundation.debt_repayment_synthesis",
                "current_window_assessment": debt_synthesis.get("current_window_assessment"),
                "preparatory_relief_windows": debt_synthesis.get("preparatory_relief_windows"),
                "claim_rule": debt_synthesis.get("claim_rule"),
            }
            result["verdict"] = verdict
            event_rules = dict(answer_spec.get("event_rules") or {})
            event_rules["allowed_timing_windows"] = repayment_windows
            event_rules["required_material_windows"] = repayment_windows[:2]
            event_rules["window_answer_rule"] = debt_synthesis.get("claim_rule")
            answer_spec["event_rules"] = event_rules
            if not repayment_windows and not timing_missing:
                compact_policy["claim_permission"] = "no_ranked_debt_repayment_window"
                compact_policy["instruction"] = (
                    "No route-adjudicated debt-repayment window is available. Do not turn debt-house activity or the "
                    "current date into repayment timing. Explain that a reliable window was not established."
                )
        if time_bound_mode:
            # Every required Wealth factor belongs to the timing chain. Missing
            # natal/divisional promise is as disqualifying as missing dasha or
            # transit confirmation; timing must not be manufactured on top of it.
            timing_missing = list(missing)
        elif missing:
            compact_policy["claim_permission"] = "no_complete_wealth_verdict"
            compact_policy["instruction"] = (
                "Required Wealth evidence is incomplete. State which graph factors are unavailable and give only "
                "the bounded observations supported by evidence.wealth_foundation. Do not substitute D9, generic "
                "natal promise, current activation, or planet folklore for the missing layer."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and love_arranged_route:
        relation = str((query_plan.get("time_scope") or {}).get("relation") or "").strip().lower()
        pathway_rules = {
            "scope": "static natal marriage-pathway comparison; no event timing",
            "question_time_relation": relation or "unspecified",
            "love_led_pathway": {
                "required_factors": ["marriage:H5", "marriage:H7", "marriage:D9"],
                "meaning": "romance or personal choice develops into committed partnership",
            },
            "family_mediated_pathway": {
                "required_factors": [
                    "marriage:H2", "marriage:H7", "marriage:H9", "marriage:H11", "marriage:D9",
                ],
                "meaning": "family, community or a formal introduction mediates the committed partnership",
            },
            "allowed_verdicts": [
                "love-led pathway is stronger",
                "family-mediated pathway is stronger",
                "mixed or hybrid pathway",
                "insufficient comparative evidence",
            ],
            "required_answer_order": [
                "direct comparative verdict",
                "love-led evidence",
                "family-mediated evidence",
                "D9 confirmation or qualification",
                "one question asking whether the reading matches how the marriage happened",
            ],
            "past_tense_rule": (
                "Because the question asks about an already-past marriage, describe what the chart suggests was "
                "more likely to have happened. Do not switch to future tense or ask about the user's current "
                "relationship status."
                if relation == "past"
                else "Match the tense of the user's question."
            ),
            "forbidden_moves": [
                "Do not answer only whether marriage is promised.",
                "Do not say historical data, dasha evidence or transit evidence is required.",
                "Do not mention a current or future dasha, transit, date, period or timing window.",
                "Do not use vague sudden-change or hidden-matter language unless supplied comparative evidence requires it.",
                "Do not ask whether the user is currently in a relationship or considering an arranged setup.",
                "Do not claim binary certainty; a mixed or hybrid pathway is valid when both sides are supported.",
                "Do not call a natal house active or activated; activation is reserved for timing routes.",
            ],
            "static_vocabulary": [
                "supports", "challenges", "has mixed tone", "connects", "contains", "receives an aspect", "confirms",
            ],
        }
        compact_policy["marriage_pathway_rules"] = pathway_rules
        compact_policy["instruction"] = (
            "Compare the love-led and family-mediated marriage pathways from the supplied D1/D9 evidence. "
            "Explain both pathways before supporting one or calling the result mixed. This is not a marriage-"
            "promise or historical-timing question. Follow marriage_pathway_rules exactly."
        )
        answer_spec["marriage_pathway_rules"] = pathway_rules
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static love-led versus family-mediated marriage-pathway comparison"
        result["verdict"] = verdict
    if bool(policy.get("live")) and spouse_meeting_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        meeting = normalized.get("spouse_meeting_context") if isinstance(normalized.get("spouse_meeting_context"), Mapping) else {}
        relation = str((query_plan.get("time_scope") or {}).get("relation") or "").strip().lower()
        meeting_rules = {
            "scope": "static natal probable meeting context; no timing",
            "question_time_relation": relation or "unspecified",
            "evidence_complete": bool(meeting.get("evidence_complete")),
            "primary_evidence": "evidence.spouse_meeting_context.primary_channel",
            "required_answer_order": [
                "one direct probable meeting context",
                "the seventh-lord natal-placement basis",
                "at most one concretely supported secondary channel",
                "D9 confirmation or qualification",
                "one question asking whether that context matches how they met",
            ],
            "forbidden_moves": [
                "Do not mention dasha, transit, activation, a planet-driven period, date or life phase.",
                "Do not infer work or duty from Saturn unless the supplied primary channel is House 6 or House 10.",
                "Do not infer friends or a shared circle unless supplied House 11 evidence supports it.",
                "Do not claim an exact venue or known historical fact from a one-chart probability.",
                "Do not turn meeting context into spouse personality or relationship quality.",
            ],
            "past_tense_rule": (
                "The user asks about an event that already happened. Use past tense and ask whether the probable "
                "context matches their actual meeting."
                if relation == "past"
                else "Match the tense of the user's question."
            ),
        }
        compact_policy["spouse_meeting_rules"] = meeting_rules
        answer_spec["spouse_meeting_rules"] = meeting_rules
        compact_policy["instruction"] = (
            "Answer only from the calculated spouse_meeting_context. Lead with its seventh-lord natal-placement "
            "channel and keep it probabilistic. Never substitute dasha timing, spouse personality or generic marriage promise."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static probable spouse-meeting channel from natal evidence"
        result["verdict"] = verdict
        if not meeting.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_meeting_story"
            compact_policy["instruction"] = (
                "The calculated spouse-meeting packet is incomplete. Do not invent work, friends, travel, family, "
                "an exact venue or any other meeting story. State that a reliable channel cannot be distinguished."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and spouse_profile_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        temperament = normalized.get("spouse_temperament_context") if isinstance(normalized.get("spouse_temperament_context"), Mapping) else {}
        temperament_rules = {
            "scope": "static five-layer spouse temperament; no timing",
            "evidence_complete": bool(temperament.get("evidence_complete")),
            "primary_evidence": "evidence.spouse_temperament_context.layers",
            "required_layers": [
                "seventh_house",
                "seventh_lord_rashi_nakshatra",
                "darakaraka_rashi_nakshatra",
                "venus_rashi_nakshatra",
                "d9_confirmation",
            ],
            "required_answer_order": [
                "direct synthesized temperament",
                "seventh house and seventh-lord contribution",
                "seventh-lord nakshatra refinement",
                "Darakaraka spouse archetype",
                "Venus relationship style",
                "D9 confirmation or qualification",
                "one question about which traits match the spouse",
            ],
            "forbidden_moves": [
                "Do not infer the whole personality from the seventh house or Mercury alone.",
                "Do not omit Darakaraka, seventh-lord nakshatra, Venus rashi/nakshatra or D9.",
                "Do not mention dasha, transit, activation, timing or current-period effects.",
                "Do not diagnose, assert hidden motives or describe fixed identity with certainty.",
            ],
        }
        compact_policy["spouse_temperament_rules"] = temperament_rules
        answer_spec["spouse_temperament_rules"] = temperament_rules
        compact_policy["instruction"] = (
            "Synthesize the supplied five spouse-temperament layers. Give each layer a distinct role and let D9 "
            "confirm or qualify the natal picture; no single house, planet, rashi or nakshatra may dominate the answer."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static five-layer spouse temperament synthesis"
        result["verdict"] = verdict
        if not temperament.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_spouse_temperament"
            compact_policy["missing_temperament_layers"] = list(temperament.get("missing_layers") or [])
            compact_policy["instruction"] = (
                "Required spouse-temperament layers are missing. Do not invent a personality profile from the seventh "
                "house alone. State which calculation layers are unavailable."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and spouse_appearance_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        appearance = normalized.get("spouse_appearance_context") if isinstance(normalized.get("spouse_appearance_context"), Mapping) else {}
        appearance_rules = {
            "scope": "spouse physical appearance and visual presence only; no temperament or timing",
            "evidence_complete": bool(appearance.get("evidence_complete")),
            "primary_evidence": "evidence.spouse_appearance_context.layers",
            "required_layers": [
                "seventh_house_sign",
                "seventh_lord_rashi_nakshatra",
                "darakaraka_rashi_nakshatra",
                "venus_rashi_nakshatra",
                "d9_confirmation",
            ],
            "required_answer_order": [
                "direct visual summary",
                "probable build and stature band",
                "face and visible expression",
                "style grooming and visual presence",
                "one or two strongest distinguishing visible markers",
                "native-chart probability disclosure",
            ],
            "forbidden_moves": [
                "Do not replace appearance with temperament or character.",
                "Do not discuss profession, location, compatibility or marriage timing.",
                "Do not infer exact height, exact measurements, exact skin colour, ethnicity, caste or nationality.",
                "Do not diagnose, sexualize or claim photographic certainty.",
                "Do not mention dasha, transit, activation or current periods.",
            ],
        }
        compact_policy["spouse_appearance_rules"] = appearance_rules
        answer_spec["spouse_appearance_rules"] = appearance_rules
        compact_policy["instruction"] = (
            "Answer the requested physical-appearance facet directly from the calculated spouse_appearance_context. "
            "Synthesize all five layers into bounded visual ranges and keep personality prose out of the answer."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static probable spouse appearance from native-chart symbolism"
        result["verdict"] = verdict
        if not appearance.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_spouse_appearance"
            compact_policy["missing_appearance_layers"] = list(appearance.get("missing_layers") or [])
            compact_policy["instruction"] = (
                "Required spouse-appearance layers are missing. Do not answer with personality traits or invent "
                "physical features; state which calculation layers are unavailable."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and spouse_location_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        location = normalized.get("spouse_location_context") if isinstance(normalized.get("spouse_location_context"), Mapping) else {}
        location_rules = {
            "scope": "static local-versus-different city, culture or geographical background; no timing",
            "evidence_complete": bool(location.get("evidence_complete")),
            "calculated_verdict": location.get("verdict"),
            "distance_score": location.get("distance_score"),
            "local_score": location.get("local_score"),
            "primary_evidence": [
                "evidence.spouse_location_context.distance_signals",
                "evidence.spouse_location_context.local_signals",
            ],
            "allowed_verdicts": [
                "different_city_culture_or_background_supported",
                "local_or_familiar_background_supported",
                "mixed_distance_and_local_signals",
                "insufficient_specific_distance_evidence",
            ],
            "required_answer_order": [
                "direct plain-language verdict",
                "strongest direct distance evidence if present",
                "strongest local or familiar-root evidence if present",
                "D9 confirmation or qualification",
                "one question asking whether this matches the known background",
            ],
            "forbidden_moves": [
                "Do not infer foreignness from Saturn, Virgo, a nakshatra or a planet's generic nature alone.",
                "Do not convert ordinary conjunctions into a different-city or cultural claim.",
                "Do not mention dasha, transit, activation or whether the result has manifested yet.",
                "Do not describe temperament, appearance, profession or relationship quality.",
                "Do not name a city, country, ethnicity, caste, religion or nationality not supplied by the user.",
            ],
        }
        compact_policy["spouse_location_rules"] = location_rules
        answer_spec["spouse_location_rules"] = location_rules
        compact_policy["instruction"] = (
            "Use the calculated local-versus-distance verdict exactly. Explain only direct spouse links to houses 3, "
            "4, 9 or 12 and explicit Rahu linkage; weak sign modality cannot decide the answer."
        )
        verdict = dict(result.get("verdict") or {})
        verdict.pop("ranked_windows", None)
        verdict["scope"] = "static spouse geographical or cultural-background tendency"
        verdict["spouse_location_verdict"] = location.get("verdict")
        result["verdict"] = verdict
        if not location.get("evidence_complete"):
            compact_policy["claim_permission"] = "no_specific_spouse_location"
            compact_policy["missing_location_layers"] = list(location.get("missing_layers") or [])
            compact_policy["instruction"] = (
                "Required spouse-location layers are missing. Do not invent a foreign, different-city, cultural or "
                "local-background story; state which calculation layers are unavailable."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and marriage_remedy_route:
        normalized = (context or {}).get("normalized_evidence") if isinstance((context or {}).get("normalized_evidence"), Mapping) else {}
        blueprint = normalized.get("remedy_blueprint") if isinstance(normalized.get("remedy_blueprint"), Mapping) else {}
        selection_mode = str(blueprint.get("selection_mode") or "ranked_three")
        top = blueprint.get("top_recommendation") if isinstance(blueprint.get("top_recommendation"), Mapping) else {}
        remedy_rules = {
            "scope": "calculated marriage remedy delivery; no fresh diagnosis or timing",
            "selection_mode": selection_mode,
            "required_count": 1 if selection_mode == "single_top" else 3,
            "top_recommendation": dict(top),
            "primary_evidence": "evidence.remedy_blueprint.ranked_remedies",
            "required_fields_per_remedy": ["action", "frequency", "astrological_reason"],
            "required_answer_order": [
                "name the top calculated remedy immediately",
                "state the exact action",
                "state frequency or duration",
                "state the calculated chart reason",
                "one concise practicality caution",
            ],
            "forbidden_moves": [
                "Do not answer with another marital-conflict diagnosis.",
                "Do not mention current dasha, transit, activation, manifestation or forecast timing.",
                "Do not replace the calculated remedy with generic communication advice.",
                "Do not ask what the conflict is about before delivering the available top remedy.",
                "Do not invent a mantra, gemstone, charity or behavioral action absent from ranked_remedies.",
                "Do not guarantee reconciliation or conflict resolution.",
            ],
        }
        compact_policy["marriage_remedy_rules"] = remedy_rules
        answer_spec["marriage_remedy_rules"] = remedy_rules
        compact_policy["instruction"] = (
            "Deliver the calculated remedy selection directly from remedy_blueprint.ranked_remedies. If the user "
            "asks which remedy is most relevant, give exactly top_recommendation with action, frequency and reason."
        )
        if not blueprint or not top:
            compact_policy["claim_permission"] = "no_calculated_marriage_remedy"
            compact_policy["instruction"] = (
                "The calculated marriage remedy blueprint or its ranked top recommendation is unavailable. Do not "
                "improvise a remedy or substitute another conflict diagnosis."
            )
            answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and comparison_mode and not missing:
        verdict = dict(result.get("verdict") or {})
        rationale = verdict.get("rationale") if isinstance(verdict.get("rationale"), Mapping) else {}
        favored = str(rationale.get("favored_option") or "")
        option_windows: list[dict[str, Any]] = []
        for option in rationale.get("options") or []:
            if not isinstance(option, Mapping):
                continue
            window = option.get("best_window") if isinstance(option.get("best_window"), Mapping) else {}
            if not window:
                continue
            row = dict(window)
            row["option"] = str(option.get("event_profile") or option.get("label") or "")
            option_windows.append(row)
        if option_windows:
            option_windows.sort(key=lambda row: (str(row.get("option")) != favored, str(row.get("start") or "")))
            verdict["ranked_windows"] = option_windows
            verdict["option_window_rule"] = (
                "Each ranked window is labeled with its owning option. The first row belongs to the favored option; "
                "never attach another option's window to it."
            )
            result["verdict"] = verdict
    if bool(policy.get("live")) and comparison_mode and missing:
        compact_policy["claim_permission"] = "no_option_winner"
        compact_policy["instruction"] = (
            "Required option-comparison factors are missing. Do not favor, recommend, or call either option "
            "more likely. State that the options cannot be reliably distinguished from the available evidence."
        )
        verdict = dict(result.get("verdict") or {})
        verdict["direction"] = "insufficient_option_evidence"
        verdict["missing_required_capabilities"] = list(dict.fromkeys(
            list(verdict.get("missing_required_capabilities") or []) + missing
        ))
        result["verdict"] = verdict
        answer_spec["limitation_instruction"] = compact_policy["instruction"]
    if bool(policy.get("live")) and time_bound_mode and timing_missing:
        compact_policy["claim_permission"] = "directional_only_no_timing"
        compact_policy["timing_missing_factors"] = timing_missing
        compact_policy["instruction"] = (
            "Required timing evidence is missing. Give only a supported directional reading; "
            "do not name, rank, or imply any date, month, year, period, or timing window. "
            "State the evidence limitation plainly."
        )
        verdict = dict(result.get("verdict") or {})
        verdict["direction"] = "insufficient_timing_evidence"
        verdict["ranked_windows"] = []
        verdict["missing_required_capabilities"] = list(dict.fromkeys(
            list(verdict.get("missing_required_capabilities") or []) + timing_missing
        ))
        result["verdict"] = verdict
        event_rules = dict(answer_spec.get("event_rules") or {})
        event_rules["allowed_timing_windows"] = []
        event_rules["required_material_windows"] = []
        event_rules["window_answer_rule"] = "No timing claim is permitted because required graph evidence is missing."
        answer_spec["event_rules"] = event_rules
        answer_spec["limitation_instruction"] = compact_policy["instruction"]
    answer_spec["knowledge_graph_policy"] = compact_policy
    result["answer_spec"] = answer_spec

    verification = dict(result.get("verification") or {})
    verification["knowledge_graph"] = {
        "live": bool(policy.get("live")),
        "domain": policy.get("domain"),
        "runtime_key": policy.get("runtime_key"),
        "mode_match": policy.get("mode_match"),
        "evidence_status": policy.get("evidence_status"),
    }
    result["verification"] = verification

    route = policy.get("route")
    if isinstance(route, Mapping):
        route = dict(route)
        route["domain"] = policy.get("domain")
        derivation = dict(result.get("user_derivation") or {})
        graph_routes = [
            row for row in list(derivation.get("knowledge_graph_routes") or [])
            if not isinstance(row, Mapping) or row.get("domain") != policy.get("domain")
        ]
        graph_routes.append(route)
        derivation["knowledge_graph_routes"] = graph_routes
        derivation[f"{policy.get('domain')}_graph_route"] = route
        result["user_derivation"] = derivation
    return result


def enforce_live_graph_answer(
    answer: str,
    packet: Mapping[str, Any] | None,
    *,
    language: str = "english",
) -> str:
    """Fail closed when the live route denies timing specificity.

    This is deliberately deterministic: unsupported dates must not reach the
    user even if the single composer call ignores its contract.
    """
    clean_answer = str(answer or "")
    # In an MD-AD-PD chain, the third planet is the sub-sub-period lord.
    # Correct this common wording slip before any answer reaches the client.
    chain_pattern = re.compile(
        r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s*[-–—]\s*"
        r"(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s*[-–—]\s*"
        r"(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b",
        re.IGNORECASE,
    )
    for match in chain_pattern.finditer(clean_answer):
        pd_planet = re.escape(match.group(3))
        clean_answer = re.sub(
            rf"\b({pd_planet})(\s*,?\s+as\s+(?:the\s+)?)sub-period lord\b",
            r"\1\2sub-sub-period lord",
            clean_answer,
            flags=re.IGNORECASE,
        )
    packet = packet if isinstance(packet, Mapping) else {}
    spec = packet.get("answer_spec") if isinstance(packet.get("answer_spec"), Mapping) else {}
    policy = spec.get("knowledge_graph_policy") if isinstance(spec.get("knowledge_graph_policy"), Mapping) else {}
    if policy.get("claim_permission") == "no_specific_meeting_story":
        if str(language or "").lower().startswith("hi"):
            return (
                "उपलब्ध जन्म-कुंडली साक्ष्य यह विश्वसनीय रूप से अलग नहीं करते कि जीवनसाथी से मुलाकात परिवार, काम, "
                "दोस्तों, यात्रा या किसी अन्य माध्यम से हुई थी। कोई खास कहानी बताना अनुमान होगा। "
                "क्या आप बताना चाहेंगे कि मुलाकात किस परिस्थिति में हुई थी?"
            )
        return (
            "The available natal evidence does not reliably distinguish whether you met through family, work, "
            "friends, travel, or another channel. Choosing a specific story would be speculation. "
            "What was the actual setting in which you first met?"
        )
    if policy.get("claim_permission") == "no_specific_spouse_temperament":
        missing = ", ".join(
            str(value).replace("_", " ")
            for value in list(policy.get("missing_temperament_layers") or [])[:5]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं जीवनसाथी के स्वभाव का विश्वसनीय विश्लेषण नहीं दे सकता क्योंकि आवश्यक परतें पूरी नहीं हैं"
                f" ({missing})। केवल सातवें भाव से व्यक्तित्व बनाना अनुमान होगा।"
            )
        return (
            "I can’t give a reliable spouse-temperament profile because the required chart layers are incomplete"
            f" ({missing}). Building the personality from the seventh house alone would be speculation."
        )
    if policy.get("claim_permission") == "no_specific_spouse_appearance":
        missing = ", ".join(
            str(value).replace("_", " ")
            for value in list(policy.get("missing_appearance_layers") or [])[:5]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं जीवनसाथी के रूप-रंग का विश्वसनीय संभावित विवरण नहीं दे सकता क्योंकि आवश्यक कुंडली-परतें "
                f"पूरी नहीं हैं ({missing})। स्वभाव को शारीरिक रूप बताना अनुमान होगा।"
            )
        return (
            "I can’t give a reliable probable appearance description because the required chart layers are incomplete"
            f" ({missing}). Replacing physical evidence with personality traits would be speculation."
        )
    if policy.get("claim_permission") == "no_specific_spouse_location":
        missing = ", ".join(
            str(value).replace("_", " ")
            for value in list(policy.get("missing_location_layers") or [])[:4]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं यह विश्वसनीय रूप से नहीं बता सकता कि जीवनसाथी किसी अलग शहर, संस्कृति या पृष्ठभूमि से जुड़े हैं, "
                f"क्योंकि आवश्यक कुंडली-परतें पूरी नहीं हैं ({missing})।"
            )
        return (
            "I can’t reliably distinguish a different-city, cultural, or local-background connection because the "
            f"required chart layers are incomplete ({missing}). Choosing one would be speculation."
        )
    if policy.get("claim_permission") == "no_calculated_marriage_remedy":
        if str(language or "").lower().startswith("hi"):
            return "गणना किया हुआ विवाह-उपाय उपलब्ध नहीं है, इसलिए कोई सामान्य या मनगढ़ंत उपाय बताना उचित नहीं होगा।"
        return (
            "The calculated marriage-remedy recommendation is unavailable, so I won’t replace it with a generic "
            "remedy or another conflict diagnosis."
        )
    if policy.get("runtime_key") == "spouse_meeting":
        # A static meeting-context answer may not borrow timing prose even if
        # the composer disregards the graph exclusions.
        sentences = re.split(r"(?<=[.!?])\s+", clean_answer)
        clean_answer = " ".join(
            sentence for sentence in sentences
            if not re.search(
                r"\b(dasha|mahadasha|antardasha|pratyantardasha|transit|activated|activation|"
                r"(?:sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu)[- ]driven period)\b",
                sentence,
                re.IGNORECASE,
            )
        ).strip()
    if (
        policy.get("domain") == "marriage"
        and policy.get("runtime_key") == "love_arranged_marriage"
    ):
        # Static natal comparison must never borrow timing vocabulary. Keep a
        # deterministic last line of defense in case the composer disregards
        # the route-specific instruction.
        clean_answer = re.sub(
            r"\bactivated\b",
            "emphasized in the natal chart",
            clean_answer,
            flags=re.IGNORECASE,
        )
        clean_answer = re.sub(r"\bactivation\b", "natal emphasis", clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(
            r"\b(is|are|was|were)\s+active\b",
            r"\1 relevant in the natal chart",
            clean_answer,
            flags=re.IGNORECASE,
        )
    wealth_rules = policy.get("wealth_answer_rules") if isinstance(policy.get("wealth_answer_rules"), Mapping) else {}
    if policy.get("domain") == "wealth" and wealth_rules.get("static_route"):
        # Static Wealth routes use D2 as the mandatory Wealth divisional and
        # natal relationships are conditions rather than time activations.
        # D9 is retained only for the authored investment-family carrier check.
        sentences = re.split(r"(?<=[.!?])\s+", clean_answer)
        investment_family = str(policy.get("runtime_key") or "") in {
            "investment", "investing_vs_trading", "investment_risk",
            "loss_vulnerability", "windfall",
        }
        if not investment_family:
            clean_answer = " ".join(
                sentence for sentence in sentences
                if not re.search(r"\b(?:D9|Navamsha|Navamsa)\b", sentence, re.IGNORECASE)
            ).strip()
        clean_answer = re.sub(r"\bactivated\b", "emphasized in the natal chart", clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r"\bactivation\b", "natal emphasis", clean_answer, flags=re.IGNORECASE)
        clean_answer = re.sub(r"\b(is|are|was|were)\s+active\b", r"\1 relevant in the natal chart", clean_answer, flags=re.IGNORECASE)
        adjudication = policy.get("wealth_adjudication") if isinstance(policy.get("wealth_adjudication"), Mapping) else {}
        if adjudication.get("strength_claim_permission") == "qualified_only":
            # The writer may not turn calculator availability or a legacy
            # aggregate score into an unqualified Wealth verdict. Preserve the
            # prose while deterministically correcting the common overclaims.
            clean_answer = re.sub(
                r"\b(?:a\s+)?genuinely strong foundation\b",
                "a real but qualified foundation",
                clean_answer,
                flags=re.IGNORECASE,
            )
            clean_answer = re.sub(
                r"\ba clear pattern of accumulation and retention\b",
                "a mixed pattern of accumulation capacity and retention pressure",
                clean_answer,
                flags=re.IGNORECASE,
            )
            clean_answer = re.sub(
                r"\bthe potential is clearly there\b",
                "the potential is present but qualified",
                clean_answer,
                flags=re.IGNORECASE,
            )
            clean_answer = re.sub(
                r"\bhas a good chance of staying with you and multiplying over time\b",
                "requires deliberate retention discipline to compound over time",
                clean_answer,
                flags=re.IGNORECASE,
            )
            # A mixed D2 can qualify a D1 promise but cannot positively confirm
            # retention. Limit this correction to sentences that name D2/Hora.
            sentences = re.split(r"(?<=[.!?])\s+", clean_answer)
            corrected_sentences = []
            for sentence in sentences:
                if re.search(r"\b(?:D2|Hora)\b", sentence, re.IGNORECASE):
                    sentence = re.sub(r"\bconfirms?\b", "qualifies", sentence, flags=re.IGNORECASE)
                if re.search(r"\bIndu Lagna\b", sentence, re.IGNORECASE) and re.search(
                    r"\b(?:creativ\w*|beauty|luxury|profession|income channel)\b", sentence, re.IGNORECASE
                ):
                    sentence = (
                        "Indu Lagna is a supplementary wealth lens here; its sign or lord alone does not establish "
                        "a profession, industry, or income channel."
                    )
                sentence = re.sub(
                    r"\b5th house\s*\(\s*gains(?:\s+and\s+smart\s+allocation)?\s*\)",
                    "5th house (judgment, speculation and investment intelligence)",
                    sentence,
                    flags=re.IGNORECASE,
                )
                corrected_sentences.append(sentence)
            clean_answer = " ".join(corrected_sentences).strip()
        source_synthesis = (
            wealth_rules.get("wealth_source_synthesis")
            if isinstance(wealth_rules.get("wealth_source_synthesis"), Mapping)
            else {}
        )
        if (
            str(policy.get("runtime_key") or "") == "wealth_source"
            and source_synthesis
            and str(language or "").lower().startswith("en")
        ):
            ranked_channels = [
                dict(row) for row in list(source_synthesis.get("ranked_channels") or [])
                if isinstance(row, Mapping) and row.get("label")
            ]
            top_keywords = [
                str(value).lower() for value in list((ranked_channels[0] if ranked_channels else {}).get("required_keywords") or [])
                if value
            ]
            names_calculated_source = bool(
                ranked_channels
                and any(re.search(rf"\b{re.escape(keyword)}\w*\b", clean_answer, re.IGNORECASE) for keyword in top_keywords)
            )
            substitutes_retention_for_source = bool(
                re.search(r"\b(?:automated savings|spending account|investment account|budgeting system)\b", clean_answer, re.IGNORECASE)
                and not names_calculated_source
            )
            if ranked_channels and (not names_calculated_source or substitutes_retention_for_source):
                def channel_sentence(row: Mapping[str, Any], *, lead: str) -> str:
                    label = str(row.get("label") or "supported work").strip()
                    evidence = [str(value).strip() for value in list(row.get("evidence") or []) if str(value).strip()]
                    basis = "; ".join(evidence[:2])
                    return f"{lead} {label}. The chart basis is that {basis}." if basis else f"{lead} {label}."

                parts = [channel_sentence(ranked_channels[0], lead="Your strongest wealth-building path is")]
                if len(ranked_channels) > 1:
                    parts.append(channel_sentence(ranked_channels[1], lead="Your second channel is"))
                if len(ranked_channels) > 2:
                    parts.append(f"A third supported channel is {ranked_channels[2].get('label')}.")
                structure = str(source_synthesis.get("earning_structure") or "")
                structure_text = {
                    "profession_or_service_led": "Overall, the structure is profession- or service-led rather than primarily speculative or partnership-dependent.",
                    "business_or_enterprise_led": "Overall, the structure is business- or enterprise-led, with professional skill supplying the value being sold.",
                    "profession_led_hybrid_with_enterprise_upside": "Overall, this is a profession-led hybrid: specialized expertise is the base, with stronger upside when it is scaled through products, platforms, consulting or enterprise rather than kept as salary alone.",
                }.get(structure)
                if structure_text:
                    parts.append(structure_text)
                if str(source_synthesis.get("retention_qualification") or "") == "mixed_capacity_with_retention_pressure":
                    parts.append(
                        "D2 adds a separate caution: earning capacity is better supported than retention, so keeping and compounding the money needs discipline—but that is a qualification, not the source itself."
                    )
                parts.append("Which of these paths matches the work or business you are already building?")
                clean_answer = " ".join(parts)
        multiple_income_synthesis = (
            wealth_rules.get("multiple_income_synthesis")
            if isinstance(wealth_rules.get("multiple_income_synthesis"), Mapping)
            else {}
        )
        if (
            str(policy.get("runtime_key") or "") == "multiple_income"
            and multiple_income_synthesis
            and str(language or "").lower().startswith("en")
        ):
            primary_stream = (
                multiple_income_synthesis.get("primary_stream")
                if isinstance(multiple_income_synthesis.get("primary_stream"), Mapping)
                else {}
            )
            secondary_streams = [
                dict(row) for row in list(multiple_income_synthesis.get("secondary_streams") or [])
                if isinstance(row, Mapping) and row.get("label")
            ]
            required_channel_keywords = [
                str(value).lower()
                for row in [primary_stream, *secondary_streams[:1]]
                for value in list(row.get("required_keywords") or [])
                if value
            ]
            names_streams = sum(
                1 for keyword in required_channel_keywords
                if re.search(rf"\b{re.escape(keyword)}\w*\b", clean_answer, re.IGNORECASE)
            ) >= 2
            gives_direct_verdict = bool(re.search(r"\b(?:yes|supports? more than one|multiple (?:income )?streams?)\b", clean_answer, re.IGNORECASE))
            if not names_streams or not gives_direct_verdict:
                verdict = str(multiple_income_synthesis.get("verdict") or "")
                if verdict == "multiple_complementary_streams_supported":
                    parts = [
                        "Yes—your chart supports more than one income stream, but the strongest pattern is complementary streams built around one core expertise, not unrelated side hustles."
                    ]
                else:
                    parts = [
                        "Your chart is clearer for one primary income engine than for several equally strong streams."
                    ]
                if primary_stream.get("label"):
                    primary_evidence = [str(value) for value in list(primary_stream.get("evidence") or []) if value]
                    basis = "; ".join(primary_evidence[:2])
                    parts.append(
                        f"The primary stream is {primary_stream.get('label')}."
                        + (f" The chart basis is that {basis}." if basis else "")
                    )
                if secondary_streams:
                    parts.append(f"The strongest secondary stream is {secondary_streams[0].get('label')}.")
                if len(secondary_streams) > 1:
                    parts.append(f"A further supporting stream is {secondary_streams[1].get('label')}.")
                parts.append(
                    "This favors a structure such as core professional income plus a scalable product/platform or consulting-advisory layer, rather than several disconnected ventures."
                )
                if str(multiple_income_synthesis.get("retention_qualification") or "") == "mixed_capacity_with_retention_pressure":
                    parts.append(
                        "D2 separately shows retention pressure, so several inflows can still feel financially thin unless the streams are consolidated and retained; that does not cancel the multiple-income promise."
                    )
                parts.append("Which second stream are you considering alongside your main work?")
                clean_answer = " ".join(parts)
        loss_synthesis = (
            wealth_rules.get("loss_vulnerability_synthesis")
            if isinstance(wealth_rules.get("loss_vulnerability_synthesis"), Mapping)
            else {}
        )
        if (
            str(policy.get("runtime_key") or "") == "loss_vulnerability"
            and loss_synthesis
            and str(language or "").lower().startswith("en")
        ):
            vulnerabilities = [
                dict(row) for row in list(loss_synthesis.get("ranked_vulnerabilities") or [])
                if isinstance(row, Mapping) and row.get("label")
            ]
            top_keywords = [
                str(value) for value in list((vulnerabilities[0] if vulnerabilities else {}).get("required_keywords") or [])
                if value
            ]
            names_top_loss = any(
                re.search(rf"\b{re.escape(keyword)}\w*\b", clean_answer, re.IGNORECASE)
                for keyword in top_keywords
            )
            has_loss_layers = bool(
                re.search(r"\bD2\b", clean_answer, re.IGNORECASE)
                and re.search(r"\b(?:D5|Panchamsha)\b", clean_answer, re.IGNORECASE)
                and re.search(r"\b(?:D9|Navamsha|Navamsa)\b", clean_answer, re.IGNORECASE)
            )
            if vulnerabilities and (not names_top_loss or not has_loss_layers):
                def vulnerability_sentence(row: Mapping[str, Any], lead: str) -> str:
                    evidence = [str(value).strip() for value in list(row.get("evidence") or []) if str(value).strip()]
                    basis = "; ".join(evidence[:4])
                    return f"{lead} {row.get('label')}. The evidence is that {basis}."

                parts = [vulnerability_sentence(vulnerabilities[0], "Your chart is most vulnerable to loss through")]
                if len(vulnerabilities) > 1:
                    parts.append(vulnerability_sentence(vulnerabilities[1], "The second vulnerability is"))
                if len(vulnerabilities) > 2:
                    parts.append(f"A further pressure point is {vulnerabilities[2].get('label')}.")
                counterweight = loss_synthesis.get("protective_counterweight") if isinstance(loss_synthesis.get("protective_counterweight"), Mapping) else {}
                eleventh = counterweight.get("eleventh_lord") if isinstance(counterweight.get("eleventh_lord"), Mapping) else {}
                if eleventh.get("planet"):
                    dignity = str(eleventh.get("dignity") or "").replace("_", " ")
                    parts.append(
                        f"This does not deny gain capacity: the eleventh lord {eleventh.get('planet')} is in house {eleventh.get('placement_house')}"
                        + (f" with {dignity} dignity" if dignity else "")
                        + ". The vulnerability is in decision quality and retention, not an inability to earn."
                    )
                parts.append("Which feels more familiar in real life—losses from risky decisions, or money leaving after you earn it?")
                clean_answer = " ".join(parts)
        investment_synthesis = (
            wealth_rules.get("investment_synthesis")
            if isinstance(wealth_rules.get("investment_synthesis"), Mapping)
            else {}
        )
        if (
            investment_family
            and str(policy.get("runtime_key") or "") != "loss_vulnerability"
            and investment_synthesis
            and str(language or "").lower().startswith("en")
        ):
            fifth_lord = (
                investment_synthesis.get("fifth_lord")
                if isinstance(investment_synthesis.get("fifth_lord"), Mapping)
                else {}
            )
            fifth_planet = str(fifth_lord.get("planet") or "")
            d5 = investment_synthesis.get("d5") if isinstance(investment_synthesis.get("d5"), Mapping) else {}
            d9 = investment_synthesis.get("d9") if isinstance(investment_synthesis.get("d9"), Mapping) else {}
            d5_named_planets = [
                str(row.get("planet") or "")
                for row in list(d5.get("supporting_placements") or []) + list(d5.get("caution_placements") or [])
                if isinstance(row, Mapping) and row.get("planet")
            ]
            d9_named_planets = [
                str(row.get("planet") or "")
                for row in list(d9.get("supporting_placements") or []) + list(d9.get("caution_placements") or [])
                if isinstance(row, Mapping) and row.get("planet")
            ]
            has_concrete_fifth = bool(fifth_planet and re.search(rf"\b{re.escape(fifth_planet)}\b", clean_answer, re.IGNORECASE))
            has_concrete_d5 = bool(
                re.search(r"\b(?:D5|Panchamsha)\b", clean_answer, re.IGNORECASE)
                and any(re.search(rf"\b{re.escape(planet)}\b", clean_answer, re.IGNORECASE) for planet in d5_named_planets)
            )
            has_concrete_d9 = bool(
                re.search(r"\b(?:D9|Navamsha|Navamsa)\b", clean_answer, re.IGNORECASE)
                and any(re.search(rf"\b{re.escape(planet)}\b", clean_answer, re.IGNORECASE) for planet in d9_named_planets)
            )
            if not (has_concrete_fifth and has_concrete_d5 and has_concrete_d9):
                def ordinal(value: Any) -> str:
                    try:
                        number = int(value)
                    except (TypeError, ValueError):
                        return str(value or "")
                    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
                    return f"{number}{suffix}"

                def placement_text(row: Mapping[str, Any]) -> str:
                    planet = str(row.get("planet") or "a carrier")
                    house = row.get("house")
                    dignity = str(row.get("dignity") or "").replace("_", " ")
                    text = f"{planet} in the {ordinal(house)} house" if house else planet
                    if dignity and dignity != "neutral":
                        text += f" ({dignity})"
                    return text

                def join_items(values: list[str]) -> str:
                    values = [value for value in values if value]
                    if len(values) < 2:
                        return "".join(values)
                    if len(values) == 2:
                        return f"{values[0]} and {values[1]}"
                    return f"{', '.join(values[:-1])}, and {values[-1]}"

                flag_labels = {
                    "gandanta": "Gandanta",
                    "avayogi_lord": "Avayogi lordship",
                    "dagdha_lord": "Dagdha lordship",
                    "tithi_shunya_lord": "Tithi-Shunya lordship",
                    "avayogi_tithi_shunya_override": "the Avayogi–Tithi-Shunya mitigating overlap",
                    "mixed_or_malefic_conjunctions": "mixed or difficult conjunctions",
                }
                flags = [flag_labels.get(str(flag), str(flag).replace("_", " ")) for flag in fifth_lord.get("caution_flags") or []]
                fifth_strength = str(fifth_lord.get("shadbala_grade") or "").lower()
                fifth_parts = []
                if fifth_strength:
                    fifth_parts.append(f"{fifth_strength} Shadbala")
                if fifth_lord.get("retrograde"):
                    fifth_parts.append("retrograde motion")
                fifth_parts.extend(flags)

                eleventh = (
                    investment_synthesis.get("eleventh_lord")
                    if isinstance(investment_synthesis.get("eleventh_lord"), Mapping)
                    else {}
                )
                eleventh_planet = str(eleventh.get("planet") or "The eleventh lord")
                eleventh_house = eleventh.get("placement_house")
                eleventh_dignity = str(eleventh.get("dignity") or "").replace("_", " ")
                gains_sentence = (
                    f"{eleventh_planet}, the eleventh lord, is in the {ordinal(eleventh_house)} house"
                    if eleventh_house else f"{eleventh_planet}, the eleventh lord"
                )
                if eleventh_dignity == "own sign":
                    gains_sentence += " in its own sign"
                elif eleventh_dignity and eleventh_dignity != "neutral":
                    gains_sentence += f" with {eleventh_dignity} dignity"

                d5_support = [placement_text(row) for row in list(d5.get("supporting_placements") or [])[:2] if isinstance(row, Mapping)]
                d5_cautions = [placement_text(row) for row in list(d5.get("caution_placements") or [])[:2] if isinstance(row, Mapping)]
                node_notes = [
                    f"{row.get('node')} sharing the {ordinal(row.get('house'))} house with {', '.join(str(value) for value in row.get('companions') or [])}"
                    for row in list(d5.get("node_cooccupancies") or [])[:1]
                    if isinstance(row, Mapping)
                ]
                d9_support = [placement_text(row) for row in list(d9.get("supporting_placements") or [])[:2] if isinstance(row, Mapping)]
                d9_cautions = [placement_text(row) for row in list(d9.get("caution_placements") or [])[:2] if isinstance(row, Mapping)]

                d5_sentence = "D5 is mixed"
                if d5_support:
                    d5_sentence += f": {join_items(d5_support)} support investment judgment"
                if d5_cautions or node_notes:
                    d5_sentence += f", while {join_items(d5_cautions + node_notes)} add volatility or pressure"
                d5_sentence += "."
                d9_sentence = "D9 provides supporting qualification"
                if d9_support:
                    d9_sentence += f": {join_items(d9_support)} sustain the carriers"
                if d9_cautions:
                    d9_sentence += f", while {join_items(d9_cautions)} temper consistency"
                d9_sentence += "."

                clean_answer = (
                    "Your chart supports investing, but high-risk speculation is a qualified area rather than an open green light. "
                    f"{gains_sentence}, supporting the capacity to realize gains. "
                    f"The fifth lord {fifth_planet or 'carrier'} is placed in the {ordinal(fifth_lord.get('placement_house'))} house"
                    f"; its complete condition includes {join_items(fifth_parts) if fifth_parts else 'mixed evidence'}, so that placement cannot be read as positive by itself. "
                    f"D2 gives a {str(investment_synthesis.get('retention') or 'mixed').replace('_', ' ')} verdict, separating gain capacity from the ability to retain it. "
                    f"{d5_sentence} {d9_sentence} "
                    "Overall, disciplined, researched and longer-horizon investing is better supported than frequent, leveraged or impulsive speculation. "
                    "That does not mean every speculative decision must fail; it means volatility and retention risk need tighter control."
                )
    if policy.get("domain") == "wealth" and policy.get("runtime_key") == "wealth_timing":
        growth_synthesis = (
            policy.get("wealth_growth_timing_synthesis")
            if isinstance(policy.get("wealth_growth_timing_synthesis"), Mapping)
            else {}
        )
        growth_windows = [
            dict(row) for row in list(growth_synthesis.get("ranked_growth_windows") or [])
            if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
        ]
        bounded_forecast = (
            growth_synthesis.get("bounded_period_synthesis")
            if isinstance(growth_synthesis.get("bounded_period_synthesis"), Mapping)
            else {}
        )
        if (
            policy.get("claim_permission") == "no_ranked_wealth_growth_window"
            or (not growth_windows and not bounded_forecast)
        ):
            if str(language or "").lower().startswith("hi"):
                return (
                    "गणना में भविष्य की कोई विश्वसनीय धन-वृद्धि अवधि स्थापित नहीं हुई। केवल वर्तमान दशा, "
                    "पाँचवें भाव या वित्तीय गतिविधि को धन-वृद्धि मानकर मैं कोई तारीख नहीं बनाऊँगा।"
                )
            return (
                "I can’t identify a reliable future wealth-growth phase from the calculated evidence. Current "
                "financial activity or a dasha boundary alone is not realized growth, so I won’t turn today into the answer."
            )
        if bounded_forecast and str(language or "").lower().startswith("en"):
            def format_bounded_date(value: Any) -> str:
                try:
                    return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                except (TypeError, ValueError):
                    return str(value or "")

            def natural_months(values: Any) -> str:
                months = [str(value) for value in list(values or []) if value]
                if not months:
                    return ""
                if len(months) == 1:
                    return months[0]
                if len(months) == 2:
                    return f"{months[0]} and {months[1]}"
                return f"{', '.join(months[:-1])}, and {months[-1]}"

            strongest_phase = (
                bounded_forecast.get("strongest_phase")
                if isinstance(bounded_forecast.get("strongest_phase"), Mapping)
                else {}
            )
            peak_rows = [
                row for row in list(bounded_forecast.get("strongest_peak_months") or [])
                if isinstance(row, Mapping) and row.get("month")
            ]
            peak_months = [str(row.get("month")) for row in peak_rows]
            reinforced = [
                str(value) for value in list(bounded_forecast.get("reinforced_support_months") or [])
                if value and str(value) not in peak_months
            ]
            background = list(bounded_forecast.get("background_support_months") or [])
            secondary = list(bounded_forecast.get("secondary_support_months") or [])
            lower = list(bounded_forecast.get("lower_support_months") or [])
            peak_text = natural_months(peak_months) or "the strongest dated transit concentration"
            parts = [
                f"{peak_text} is the strongest financially supportive part of the requested period."
            ]
            if strongest_phase.get("start") and strongest_phase.get("end"):
                parts.append(
                    f"The broader supportive phase runs from {format_bounded_date(strongest_phase.get('start'))} "
                    f"to {format_bounded_date(strongest_phase.get('end'))}, during {strongest_phase.get('chain')}."
                )
            if reinforced:
                parts.append(
                    f"Within that phase, {natural_months(reinforced)} receive additional dated transit reinforcement."
                )
            if background:
                parts.append(
                    f"{natural_months(background)} remains part of the supportive dasha phase, but without the same concentrated transit peak."
                )
            if secondary:
                parts.append(
                    f"{natural_months(secondary)} {'form' if len(secondary) > 1 else 'forms'} a secondary supportive period: "
                    "the financial houses remain engaged, but the KP/gain confirmation is less complete than in the strongest phase."
                )
            if lower:
                parts.append(
                    f"{natural_months(lower)} {'are' if len(lower) > 1 else 'is'} comparatively lower-support, so "
                    f"{'they are' if len(lower) > 1 else 'it is'} better read as consolidation and financial management rather than a primary growth window."
                )
            if growth_synthesis.get("retention_qualification") == "mixed_capacity_with_retention_pressure":
                parts.append(
                    "Your D2 still shows retention pressure, so supportive months are better for creating or collecting gains than assuming every inflow will automatically stay."
                )
            parts.append(
                "This is a relative astrological forecast across the year, not a guarantee of profit or a substitute for financial planning."
            )
            parts.append(
                "Would you like me to separate these months further for career income, business, investments, or debt repayment?"
            )
            return " ".join(parts)
        if str(language or "").lower().startswith("en"):
            def format_growth_date(value: Any) -> str:
                try:
                    return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                except (TypeError, ValueError):
                    return str(value or "")

            def growth_range(row: Mapping[str, Any]) -> str:
                return f"{format_growth_date(row.get('start'))} to {format_growth_date(row.get('end'))}"

            required_dates = [
                (str(row.get(key) or "")[:10], format_growth_date(row.get(key)))
                for row in growth_windows[:2]
                for key in ("start", "end")
                if row.get(key)
            ]
            names_required_windows = all(
                iso_value in clean_answer or human_value in clean_answer
                for iso_value, human_value in required_dates
            )
            current = (
                growth_synthesis.get("current_window_assessment")
                if isinstance(growth_synthesis.get("current_window_assessment"), Mapping)
                else {}
            )
            current_start = format_growth_date(current.get("start")) if current.get("start") else ""
            mislabels_current = bool(
                current_start
                and current_start in clean_answer
                and re.search(
                    rf"(?:next|meaningful|growth|significant marker).{{0,100}}{re.escape(current_start)}|"
                    rf"{re.escape(current_start)}.{{0,100}}(?:next|meaningful|growth|significant marker)",
                    clean_answer,
                    re.IGNORECASE,
                )
            )
            unsafe_exact_claim = bool(re.search(
                r"\b(?:exact gain date|guaranteed gains?|will become wealthy|certain profit)\b",
                clean_answer,
                re.IGNORECASE,
            ))
            if not names_required_windows or mislabels_current or unsafe_exact_claim:
                next_window = growth_windows[0]
                strongest = next(
                    (
                        row for row in growth_windows
                        if row.get("answer_role") == "strongest_later_growth_phase"
                    ),
                    max(
                        growth_windows,
                        key=lambda row: (
                            int(row.get("tier") or 0),
                            len(row.get("transit_growth_houses") or []),
                        ),
                    ),
                )
                current_sentence = (
                    f"The current {current.get('chain')} phase beginning {format_growth_date(current.get('start'))} "
                    "shows financial activity, but it does not have the complete KP-and-transit gain combination, so it is not the answer to ‘next meaningful growth’. "
                    if current else "The current period is context, not automatically the next growth phase. "
                )
                next_sentence = (
                    f"Your next meaningful wealth-growth phase is {growth_range(next_window)}, during {next_window.get('chain')}. "
                    f"The period connects wealth houses {', '.join(str(value) for value in next_window.get('growth_houses') or [])}; "
                    f"the dasha chain supplies KP support through houses {', '.join(str(value) for value in next_window.get('kp_growth_houses') or [])}, "
                    f"and transit confirms realized-gain house 11."
                )
                strongest_sentence = ""
                if strongest is not next_window:
                    strongest_sentence = (
                        f" The fuller and stronger later phase is {growth_range(strongest)}, during {strongest.get('chain')}, "
                        f"when houses {', '.join(str(value) for value in strongest.get('growth_houses') or [])} combine with broader KP and transit confirmation."
                    )
                retention_sentence = (
                    " D2 still shows mixed accumulation capacity with retention pressure, so these periods support growth opportunities more clearly than automatic wealth retention."
                    if growth_synthesis.get("retention_qualification") == "mixed_capacity_with_retention_pressure"
                    else ""
                )
                clean_answer = (
                    f"{current_sentence}{next_sentence}{strongest_sentence}{retention_sentence} "
                    "These are broad astrological support periods, not guaranteed gains or exact transaction dates. "
                    "Are you looking for growth through career income, business, or investments?"
                ).strip()
    if policy.get("domain") == "wealth" and policy.get("runtime_key") == "debt_repayment":
        debt_synthesis = (
            policy.get("debt_repayment_synthesis")
            if isinstance(policy.get("debt_repayment_synthesis"), Mapping)
            else {}
        )
        repayment_windows = [
            dict(row) for row in list(debt_synthesis.get("ranked_repayment_windows") or [])
            if isinstance(row, Mapping) and (row.get("start") or row.get("end"))
        ]
        if policy.get("claim_permission") == "no_ranked_debt_repayment_window" or not repayment_windows:
            if str(language or "").lower().startswith("hi"):
                return (
                    "गणना में कोई विश्वसनीय ऋण-चुकौती अवधि स्थापित नहीं हुई। केवल ऋण या दबाव वाले भावों का सक्रिय "
                    "होना चुकौती का संकेत नहीं है, इसलिए मैं उससे कोई तारीख नहीं बनाऊँगा।"
                )
            return (
                "I can’t identify a reliable repayment-support window from the calculated evidence. Debt-house "
                "activity alone is not repayment, so I won’t turn the current date or dasha into a payoff prediction."
            )
        if str(language or "").lower().startswith("en"):
            allowed_dates = {
                str(row.get(key) or "")[:10]
                for row in repayment_windows for key in ("start", "end")
                if row.get(key)
            }
            names_allowed_window = any(value in clean_answer for value in allowed_dates)
            contains_unsafe_debt_claim = bool(re.search(
                r"\b(significant marker|repayment season|highest[- ]interest|consolidat\w*|refinanc\w*)\b",
                clean_answer,
                re.IGNORECASE,
            ))
            if not names_allowed_window or contains_unsafe_debt_claim:
                def format_date(value: Any) -> str:
                    try:
                        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")
                    except (TypeError, ValueError):
                        return str(value or "")

                def range_text(row: Mapping[str, Any]) -> str:
                    return f"{format_date(row.get('start'))} to {format_date(row.get('end'))}"

                def house_list(values: Any) -> str:
                    items = [str(value) for value in list(values or [])]
                    if len(items) < 2:
                        return "".join(items)
                    return f"{', '.join(items[:-1])} and {items[-1]}"

                earliest = min(repayment_windows, key=lambda row: str(row.get("start") or ""))
                strongest = max(
                    repayment_windows,
                    key=lambda row: (int(row.get("tier") or 0), len(row.get("support_houses") or [])),
                )
                current = (
                    debt_synthesis.get("current_window_assessment")
                    if isinstance(debt_synthesis.get("current_window_assessment"), Mapping)
                    else {}
                )
                opening = (
                    "The current period shows debt pressure and financial activity, but it is not a clean repayment window"
                    if current.get("classification") == "debt_activity_not_repayment_support"
                    else "The current period does not establish a debt-free date"
                )
                earliest_sentence = (
                    f"The first calculated repayment-progress phase is {range_text(earliest)} "
                    f"during {earliest.get('chain')}. It connects repayment houses "
                    f"{house_list(earliest.get('support_houses'))}, with KP and transit support, "
                    "but pressure houses remain involved, so this is better described as progress than guaranteed clearance."
                )
                strongest_sentence = ""
                if strongest is not earliest:
                    strongest_sentence = (
                        f"The fuller repayment-support combination appears from {range_text(strongest)} "
                        f"during {strongest.get('chain')}, when houses "
                        f"{house_list(strongest.get('support_houses'))} come together. "
                    )
                clean_answer = (
                    f"{opening}; its active houses show resources and burden without the complete repayment combination. "
                    f"{earliest_sentence} {strongest_sentence}"
                    "These are broad astrological support periods, not an exact payoff date. Your actual debt-free date "
                    "depends on the outstanding balance, interest, cash flow and repayments, which the chart does not calculate. "
                    "Are you asking about one specific loan or your total debt burden?"
                ).strip()
    if policy.get("claim_permission") == "no_health_area_specificity":
        if str(language or "").lower().startswith("hi"):
            return (
                "मैं अगले छह महीनों के लिए किसी विशेष स्वास्थ्य क्षेत्र को विश्वसनीय रूप से प्राथमिकता नहीं दे सकता, "
                "क्योंकि आवश्यक शरीर-क्षेत्र गणना उपलब्ध नहीं है। किसी अंग, लक्षण या जोखिम-अवधि का नाम देना अनुमान होगा। "
                "सामान्य रोकथाम, नियमित जाँच और लगातार बने रहने वाले लक्षणों पर चिकित्सकीय सलाह सबसे उचित है। "
                "क्या कोई विशेष स्वास्थ्य चिंता है जिसे आप ध्यान में रखना चाहते हैं?"
            )
        return (
            "I can’t reliably identify one health area as needing the most caution because the required body-area "
            "calculation is unavailable. Naming a body zone or risk window would be speculation. General preventive "
            "care, routine check-ups, and professional advice for persistent symptoms are the safest guidance. "
            "Is there a specific health concern you want me to keep in view?"
        )
    if policy.get("claim_permission") == "no_option_winner":
        domain = str(policy.get("domain") or "these options").replace("_", " ")
        if str(language or "").lower().startswith("hi"):
            return (
                f"उपलब्ध {domain} साक्ष्य इन दोनों विकल्पों में विश्वसनीय रूप से अंतर नहीं करते। "
                "इसलिए किसी एक को अधिक संभावित बताना अनुमान होगा। वास्तविक जीवन में अभी कौन-सा विकल्प ठोस रूप से सामने आ रहा है?"
            )
        return (
            "The available career evidence does not reliably distinguish these two options, so choosing promotion "
            "or job change as more likely would be speculation. Which option is already becoming concrete in real life?"
        )
    if policy.get("claim_permission") == "no_complete_wealth_verdict":
        missing = ", ".join(
            str(value).split(":")[-1]
            for value in list(policy.get("missing_required_factors") or [])[:5]
        )
        if str(language or "").lower().startswith("hi"):
            return (
                f"मैं अभी पूर्ण धन-वित्त निष्कर्ष नहीं दे सकता क्योंकि आवश्यक गणना-परतें ({missing}) उपलब्ध नहीं हैं। "
                "D9 या सामान्य ग्रह-अर्थ से इस कमी को भरना अनुमान होगा।"
            )
        return (
            f"I can’t give a complete Wealth reading because required calculated layers are unavailable ({missing}). "
            "Substituting D9 or generic planet meanings for them would be speculation."
        )
    if policy.get("claim_permission") != "directional_only_no_timing":
        return clean_answer
    domain = str(policy.get("domain") or "this topic").replace("_", " ")
    missing = list(policy.get("timing_missing_factors") or [])
    missing_labels = ", ".join(value.split(":")[-1] for value in missing[:3])
    if str(language or "").lower().startswith("hi"):
        return (
            f"मैं अभी {domain} के लिए विश्वसनीय समय नहीं बता सकता, क्योंकि ग्राफ में आवश्यक "
            f"समय-साक्ष्य ({missing_labels}) पूरे नहीं हैं। उपलब्ध संकेत केवल सामान्य दिशा बताते हैं; "
            "किसी तारीख या अवधि को चुनना अनुमान होगा। क्या आप बिना समय-निर्धारण के सामान्य संकेत जानना चाहेंगे?"
        )
    return (
        f"I can’t give a reliable {domain} timing result because the live graph is missing required "
        f"timing evidence ({missing_labels}). The available chart evidence supports only a general "
        "direction; choosing a date would be speculation. Would you like the supported non-timing reading instead?"
    )
