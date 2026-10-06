"""Opt-in, API-neutral Deva Keralam chart matching service.

This joins an existing sidereal D1 chart, the pinned Nadiamsa calculator and
reviewed contextual rules.  It is not imported by routes, chart calculation or
chat, so adopting it cannot alter an existing client contract.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from ..engine import ClassicalRuleEngine
from ..models import ClassicalRule
from .chapter_01 import RULES
from .chart_facts import compile_deva_keralam_chart_facts


SERVICE_VERSION = "deva-keralam-matcher/1.0.0"


def _uncertainty_from_context(context: Mapping[str, Any]) -> Tuple[Optional[float], Dict[str, Any]]:
    """Resolve longitude uncertainty without inventing an ascensional rate."""
    direct = context.get("ascendant_longitude_uncertainty_arcseconds")
    if direct is not None:
        value = float(direct)
        if value < 0:
            raise ValueError("ascendant_longitude_uncertainty_arcseconds cannot be negative")
        return value, {
            "status": "supplied_longitude_uncertainty",
            "ascendant_longitude_uncertainty_arcseconds": value,
        }

    clock_seconds = context.get("birth_time_uncertainty_seconds")
    rate = context.get("ascendant_rate_degrees_per_second")
    if clock_seconds is not None and rate is not None:
        clock_value = float(clock_seconds)
        rate_value = float(rate)
        if clock_value < 0 or rate_value < 0:
            raise ValueError("Birth-time uncertainty and ascendant rate cannot be negative")
        value = clock_value * rate_value * 3600.0
        return value, {
            "status": "derived_from_birth_time_and_local_ascensional_rate",
            "birth_time_uncertainty_seconds": clock_value,
            "ascendant_rate_degrees_per_second": rate_value,
            "ascendant_longitude_uncertainty_arcseconds": value,
        }

    if clock_seconds is not None:
        return None, {
            "status": "unverified_missing_local_ascensional_rate",
            "birth_time_uncertainty_seconds": float(clock_seconds),
            "reason": (
                "Birth-time uncertainty cannot be converted to Ascendant longitude uncertainty "
                "without the local ascensional rate."
            ),
        }
    return None, {
        "status": "unverified_not_supplied",
        "reason": "No Ascendant longitude uncertainty was supplied.",
    }


def _context_contract(fact_payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Expose canonical facts plus sourced aliases for early pilot rules."""
    rows = dict(fact_payload.get("facts") or {})
    contract: Dict[str, Any] = dict(rows)
    aliases = {
        "ascendant.sign_name": "deva_keralam.ascendant.nadiamsa.sign_name",
        "ascendant.nadiamsa.ordinal": "deva_keralam.ascendant.nadiamsa.ordinal",
        "ascendant.nadiamsa.name": "deva_keralam.ascendant.nadiamsa.name",
        "ascendant.nadiamsa.half": "deva_keralam.ascendant.nadiamsa.half",
    }
    for alias, canonical in aliases.items():
        if canonical in rows:
            contract[alias] = rows[canonical]

    warning = rows.get("deva_keralam.ascendant.nadiamsa.birth_time_precision_warning")
    if isinstance(warning, Mapping) and "value" in warning:
        reliable = dict(warning)
        reliable["value"] = warning["value"] is False
        reliable["evidence"] = {
            **dict(reliable.get("evidence") or {}),
            "derived_from": "deva_keralam.ascendant.nadiamsa.birth_time_precision_warning",
        }
        contract["ascendant.nadiamsa_half.reliable"] = reliable

    for key, raw in rows.items():
        marker = ".nadiamsa."
        if not key.startswith("deva_keralam.") or marker not in key:
            continue
        subject, suffix = key[len("deva_keralam."):].split(marker, 1)
        if subject != "ascendant":
            contract[f"planet.{subject}.nadiamsa.{suffix}"] = raw
    return contract


def _summarize(results: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    grouped = {"matched": [], "not_matched": [], "unavailable": []}
    for row in results:
        status = str(row.get("applicability") or "unavailable")
        grouped[status if status in grouped else "unavailable"].append(str(row.get("rule_key") or ""))
    overall = "matched" if grouped["matched"] else ("unavailable" if grouped["unavailable"] else "not_matched")
    return {
        "status": overall,
        "matched_rule_keys": grouped["matched"],
        "not_matched_rule_keys": grouped["not_matched"],
        "unavailable_rule_keys": grouped["unavailable"],
        "counts": {key: len(value) for key, value in grouped.items()},
    }


def match_deva_keralam_chart(
    chart: Mapping[str, Any],
    *,
    birth_context: Optional[Mapping[str, Any]] = None,
    rules: Optional[Iterable[ClassicalRule]] = None,
) -> Dict[str, Any]:
    """Calculate canonical Nadi facts and evaluate reviewed rules.

    ``chart`` uses the existing D1 shape: numeric ``ascendant`` longitude and
    optional ``planets.<name>.longitude`` rows.  ``birth_context`` can supply
    longitude uncertainty directly, or clock-time uncertainty together with
    the calculated local ascensional rate.
    """
    context = dict(birth_context or {})
    uncertainty, precision_basis = _uncertainty_from_context(context)
    facts = compile_deva_keralam_chart_facts(
        chart,
        ascendant_longitude_uncertainty_arcseconds=uncertainty,
        timing_context=context,
    )
    fact_payload = facts.as_dict()
    evaluator_chart = {"classical_facts": _context_contract(fact_payload)}
    selected_rules = tuple(RULES if rules is None else rules)
    evaluated = ClassicalRuleEngine(selected_rules).evaluate(evaluator_chart, context)
    summary = _summarize(evaluated["results"])
    return {
        "contract_version": SERVICE_VERSION,
        "status": summary["status"],
        "precision_basis": precision_basis,
        "facts": fact_payload,
        "rules_evaluated": evaluated["rules_evaluated"],
        "results": evaluated["results"],
        "summary": summary,
        "fallback_used": False,
    }
