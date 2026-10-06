"""Generic deterministic matcher for context-heavy classical passages.

The matcher deliberately consumes an already-calculated fact contract.  It
does not calculate Nadiamsas, infer missing premises, or turn partial matches
into predictions.  This keeps source ingestion, astronomical calculation and
rule evaluation independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .facts import ClassicalFact, ClassicalFactSet, evaluate_fact_expression
from .models import ClassicalRule, RuleEvaluator, SourceProfile


FACT_CONTRACT_KEY = "classical_facts"
ALLOWED_EDITORIAL_STATUSES = {"reviewed_clear", "reviewed_interpreted"}


@dataclass(frozen=True)
class RuleAnchor:
    """Cheap exact prefilter; the full expression remains authoritative."""

    key: str
    values: Tuple[Any, ...]


@dataclass(frozen=True)
class PrecisionRequirement:
    """A premise governing whether a rule can be assessed reliably."""

    key: str
    comparator: str
    value: Any
    unavailable_reason: str


@dataclass(frozen=True)
class ContextualRuleSpec:
    """Source-reviewed representation of one executable passage."""

    key: str
    title: str
    source: SourceProfile
    expression: Mapping[str, Any]
    outcome: Mapping[str, Any]
    anchors: Tuple[RuleAnchor, ...] = ()
    precision_requirements: Tuple[PrecisionRequirement, ...] = ()
    inherited_context: Mapping[str, Any] = field(default_factory=dict)
    editorial_status: str = "reviewed_clear"
    topics: Tuple[str, ...] = ()
    scope: str = "natal"
    status: str = "published"
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status == "published" and self.editorial_status not in ALLOWED_EDITORIAL_STATUSES:
            raise ValueError(
                f"Published contextual rule {self.key} has non-executable editorial status "
                f"{self.editorial_status!r}"
            )
        if not self.expression:
            raise ValueError(f"Contextual rule {self.key} requires an expression")
        if not self.outcome:
            raise ValueError(f"Contextual rule {self.key} requires a source-reviewed outcome")


def _fact_from_contract(key: str, raw: Any) -> ClassicalFact:
    if isinstance(raw, Mapping) and "value" in raw:
        value = raw["value"]
        source_rules = tuple(str(item) for item in raw.get("source_rules") or ("chart-fact-contract",))
        source_references = tuple(str(item) for item in raw.get("source_references") or ("calculated chart fact",))
        calculator_bindings = tuple(str(item) for item in raw.get("calculator_bindings") or ("caller",))
        evidence = dict(raw.get("evidence") or {})
    else:
        value = raw
        source_rules = ("chart-fact-contract",)
        source_references = ("calculated chart fact",)
        calculator_bindings = ("caller",)
        evidence = {}
    return ClassicalFact(key, value, source_rules, source_references, calculator_bindings, evidence)


def facts_from_contract(
    chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None,
) -> ClassicalFactSet:
    """Compile the stable flat fact input accepted by contextual rules.

    Both chart and birth payloads may provide ``classical_facts``.  Duplicate
    identical facts are accepted; conflicting facts fail loudly.
    """

    facts = ClassicalFactSet()
    for payload in (chart, birth_data or {}):
        rows = payload.get(FACT_CONTRACT_KEY) if isinstance(payload, Mapping) else None
        if rows is None:
            continue
        if not isinstance(rows, Mapping):
            raise TypeError(f"{FACT_CONTRACT_KEY} must be an object keyed by canonical fact name")
        for key, raw in rows.items():
            facts.add(_fact_from_contract(str(key), raw))
    return facts


def _precision_expression(requirement: PrecisionRequirement) -> Dict[str, Any]:
    return {
        "op": "fact",
        "key": requirement.key,
        "comparator": requirement.comparator,
        "value": requirement.value,
    }


def evaluate_contextual_spec(
    spec: ContextualRuleSpec,
    chart: Mapping[str, Any],
    birth_data: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    facts = facts_from_contract(chart, birth_data)

    # Known anchor mismatches cheaply rule a candidate out. Missing anchors do
    # not: the full expression must classify them as unavailable.
    anchor_evidence = []
    for anchor in spec.anchors:
        fact = facts.get(anchor.key)
        if fact is None:
            continue
        matched = fact.value in anchor.values
        anchor_evidence.append({
            "key": anchor.key,
            "actual": fact.value,
            "expected_any": list(anchor.values),
            "matched": matched,
        })
        if not matched:
            return {
                "applicability": "not_matched",
                "match_kind": "exact",
                "prefiltered": True,
                "anchors": anchor_evidence,
                "editorial_status": spec.editorial_status,
            }

    precision_evidence = []
    for requirement in spec.precision_requirements:
        result = evaluate_fact_expression(_precision_expression(requirement), facts)
        precision_evidence.extend(result.used_facts)
        if result.matched is not True:
            # A false reliability/precision premise means the chart is not
            # precise enough to decide this rule, rather than disproving it.
            return {
                "applicability": "unavailable",
                "reason": requirement.unavailable_reason,
                "match_kind": "exact",
                "anchors": anchor_evidence,
                "precision": precision_evidence,
                "editorial_status": spec.editorial_status,
            }

    result = evaluate_fact_expression(spec.expression, facts)
    base = {
        "applicability": result.status,
        "match_kind": "exact",
        "anchors": anchor_evidence,
        "precision": precision_evidence,
        "premises": list(result.used_facts),
        "failed_premises": list(result.failures),
        "inherited_context": dict(spec.inherited_context),
        "editorial_status": spec.editorial_status,
    }
    if result.matched is True:
        base["outcome"] = dict(spec.outcome)
    return base


def contextual_evaluator(spec: ContextualRuleSpec) -> RuleEvaluator:
    def evaluator(chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        return evaluate_contextual_spec(spec, chart, birth_data)

    return evaluator


def build_contextual_rule(spec: ContextualRuleSpec) -> ClassicalRule:
    """Adapt a structured rule to the stable ``ClassicalRuleEngine`` contract."""

    return ClassicalRule(
        key=spec.key,
        title=spec.title,
        source=spec.source,
        rule_type="contextual_exact_match",
        scope=spec.scope,
        status=spec.status,
        calculator_binding="classical_rules.contextual.evaluate_contextual_spec",
        evaluator=contextual_evaluator(spec),
        topics=spec.topics,
        notes=spec.notes,
    )
