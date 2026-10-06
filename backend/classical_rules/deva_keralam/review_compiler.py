"""Guarded compiler from reviewed Deva Keralam passages to executable rules.

This module is deliberately disconnected from the extraction-candidate table.
An extracted draft becomes input here only after a reviewer has supplied a
complete context, resolved every source issue, and selected canonical fact
keys.  Compilation is fail-closed and has no database write or registry side
effect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from ..contextual import (
    ContextualRuleSpec,
    PrecisionRequirement,
    RuleAnchor,
    build_contextual_rule,
)
from ..models import ClassicalRule, SourceProfile
from .nadiamsa import load_nadiamsa_table
from .ontology import definition_for_key, is_canonical_fact_key


SUPPORTED_COMPARATORS = {
    "equals", "not_equals", "in", "contains", "exists",
    "gte", "lte", "gt", "lt", "between",
}
SUPPORTED_TIMING = {"none"}
REVIEWED_CONTEXT_STATUSES = {"verified", "qualified"}


@dataclass(frozen=True)
class LintIssue:
    code: str
    message: str
    path: str = "candidate"


@dataclass(frozen=True)
class ReviewedRuleCandidate:
    """Human-reviewed input; never constructed from AI output implicitly."""

    key: str
    title: str
    passage_key: str
    context_block_key: str
    source: SourceProfile
    expression: Mapping[str, Any]
    outcome: Mapping[str, Any]
    precision_requirements: Tuple[PrecisionRequirement, ...]
    review_status: str = "reviewed_approved"
    context_status: str = "verified"
    context_qualification_acknowledged: bool = False
    source_disputes: Tuple[str, ...] = ()
    inherited_ambiguities: Tuple[str, ...] = ()
    timing_kind: str = "none"
    operationalization_status: str = "approved"
    inherited_context: Mapping[str, Any] = field(default_factory=dict)
    topics: Tuple[str, ...] = ()
    scope: str = "D1 exact Nadiamsa context"
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CompilationResult:
    candidate_key: str
    rule: Optional[ClassicalRule]
    spec: Optional[ContextualRuleSpec]
    issues: Tuple[LintIssue, ...]

    @property
    def compiled(self) -> bool:
        return self.rule is not None and not self.issues


def _walk_expression(expression: Mapping[str, Any], path: str = "expression") -> Iterable[tuple[str, Mapping[str, Any]]]:
    yield path, expression
    operator = str(expression.get("op") or "").lower()
    if operator in {"all", "any", "at_least", "not"}:
        children = expression.get("children")
        if isinstance(children, (list, tuple)):
            for index, child in enumerate(children):
                if isinstance(child, Mapping):
                    yield from _walk_expression(child, f"{path}.children.{index}")


def _lint_fact_node(node: Mapping[str, Any], path: str) -> list[LintIssue]:
    issues: list[LintIssue] = []
    key = str(node.get("key") or "")
    comparator = str(node.get("comparator") or "equals")
    if not is_canonical_fact_key(key):
        issues.append(LintIssue("unknown_fact", f"Unknown canonical fact key: {key!r}", path))
        return issues
    if comparator not in SUPPORTED_COMPARATORS:
        issues.append(LintIssue("unsupported_comparator", f"Unsupported comparator: {comparator!r}", path))
        return issues
    expected = node.get("value")
    if comparator == "between":
        if not isinstance(expected, (list, tuple)) or len(expected) != 2:
            issues.append(LintIssue("impossible_condition", "between requires exactly two bounds", path))
        else:
            try:
                if expected[0] > expected[1]:
                    issues.append(LintIssue("impossible_condition", "between lower bound exceeds upper bound", path))
            except TypeError:
                issues.append(LintIssue("impossible_condition", "between bounds are not comparable", path))
    if comparator == "in" and (not isinstance(expected, (list, tuple, set)) or not expected):
        issues.append(LintIssue("impossible_condition", "in requires a non-empty collection", path))
    definition = definition_for_key(key)
    if definition and comparator == "equals":
        value_type = definition.value_type
        if value_type == "boolean" and type(expected) is not bool:
            issues.append(LintIssue("fact_type_mismatch", f"{key} requires a boolean", path))
        elif value_type == "integer" and (type(expected) is not int):
            issues.append(LintIssue("fact_type_mismatch", f"{key} requires an integer", path))
        elif value_type == "number" and (isinstance(expected, bool) or not isinstance(expected, (int, float))):
            issues.append(LintIssue("fact_type_mismatch", f"{key} requires a number", path))
    return issues


def _lint_expression(expression: Mapping[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for path, node in _walk_expression(expression):
        operator = str(node.get("op") or "").lower()
        if operator == "fact":
            issues.extend(_lint_fact_node(node, path))
            continue
        children = node.get("children")
        if operator not in {"all", "any", "at_least", "not"}:
            issues.append(LintIssue("malformed_expression", f"Unsupported operator: {operator!r}", path))
        elif not isinstance(children, (list, tuple)) or not children:
            issues.append(LintIssue("malformed_expression", f"{operator} requires children", path))
        elif operator == "not" and len(children) != 1:
            issues.append(LintIssue("malformed_expression", "not requires exactly one child", path))
        elif operator == "at_least":
            count = node.get("count")
            if type(count) is not int or count < 1 or count > len(children):
                issues.append(LintIssue("impossible_condition", "at_least count must fit its children", path))

    equality_values = _conjunctive_equalities(expression)
    for key, values in equality_values.items():
        if len(values) > 1:
            issues.append(LintIssue(
                "impossible_condition",
                f"Conjunction requires conflicting exact values for {key}: {sorted(map(repr, values))}",
                "expression",
            ))

    ordinal_values = equality_values.get("deva_keralam.ascendant.nadiamsa.ordinal", set())
    name_values = equality_values.get("deva_keralam.ascendant.nadiamsa.name", set())
    if len(ordinal_values) == 1 and len(name_values) == 1:
        ordinal, name = next(iter(ordinal_values)), next(iter(name_values))
        table = load_nadiamsa_table()
        if type(ordinal) is int and table.names_by_ordinal.get(ordinal) != name:
            issues.append(LintIssue(
                "impossible_condition",
                f"Nadiamsa ordinal {ordinal} is {table.names_by_ordinal.get(ordinal)!r}, not {name!r}",
                "expression",
            ))
    return issues


def _conjunctive_equalities(expression: Mapping[str, Any]) -> Dict[str, set[Any]]:
    """Return only equalities that must coexist on the same match path."""
    operator = str(expression.get("op") or "").lower()
    if operator == "fact" and str(expression.get("comparator") or "equals") == "equals":
        value = expression.get("value")
        try:
            return {str(expression.get("key") or ""): {value}}
        except TypeError:
            return {}
    if operator != "all":
        # Alternatives and negations do not assert simultaneous equalities.
        return {}
    merged: Dict[str, set[Any]] = {}
    for child in expression.get("children") or ():
        if not isinstance(child, Mapping):
            continue
        for key, values in _conjunctive_equalities(child).items():
            merged.setdefault(key, set()).update(values)
    return merged


def _uses_exact_nadiamsa(expression: Mapping[str, Any]) -> bool:
    return any(
        str(node.get("key") or "").startswith("deva_keralam.ascendant.nadiamsa.")
        for _, node in _walk_expression(expression)
        if str(node.get("op") or "").lower() == "fact"
    )


def _ascendant_context_is_possible(expression: Mapping[str, Any]) -> bool:
    """Return whether conjunctive Ascendant subdivision facts can coexist."""
    if str(expression.get("op") or "").lower() != "all":
        return True
    supported = {
        "deva_keralam.ascendant.rashi.index",
        "deva_keralam.ascendant.rashi.name",
        "deva_keralam.ascendant.navamsa.index",
        "deva_keralam.ascendant.navamsa.name",
        "deva_keralam.ascendant.nadiamsa.ordinal",
        "deva_keralam.ascendant.nadiamsa.name",
        "deva_keralam.ascendant.nadiamsa.half",
        "deva_keralam.ascendant.nadiamsa.sign_modality",
    }
    constraints: Dict[str, set[Any]] = {}
    for _, node in _walk_expression(expression):
        if str(node.get("op") or "").lower() != "fact":
            continue
        key = str(node.get("key") or "")
        if key not in supported:
            continue
        comparator = str(node.get("comparator") or "equals")
        if comparator == "equals":
            constraints.setdefault(key, set()).add(node.get("value"))
        elif comparator == "in":
            constraints.setdefault(key, set()).update(node.get("value") or ())
        else:
            return True
    if not constraints:
        return True

    sign_names = (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    )
    table = load_nadiamsa_table()
    for sign_index, sign_name in enumerate(sign_names):
        modality = "movable" if sign_index in {0, 3, 6, 9} else (
            "fixed" if sign_index in {1, 4, 7, 10} else "dual"
        )
        for physical_division in range(1, 151):
            ordinal = (
                physical_division if modality == "movable"
                else 151 - physical_division if modality == "fixed"
                else ((physical_division + 74) % 150) + 1
            )
            for half, offset in (("former", 0.05), ("latter", 0.15)):
                longitude = sign_index * 30 + (physical_division - 1) * 0.2 + offset
                navamsa_index = int(((longitude * 9) % 360) // 30)
                values = {
                    "deva_keralam.ascendant.rashi.index": sign_index,
                    "deva_keralam.ascendant.rashi.name": sign_name,
                    "deva_keralam.ascendant.navamsa.index": navamsa_index,
                    "deva_keralam.ascendant.navamsa.name": sign_names[navamsa_index],
                    "deva_keralam.ascendant.nadiamsa.ordinal": ordinal,
                    "deva_keralam.ascendant.nadiamsa.name": table.names_by_ordinal[ordinal],
                    "deva_keralam.ascendant.nadiamsa.half": half,
                    "deva_keralam.ascendant.nadiamsa.sign_modality": modality,
                }
                if all(values[key] in allowed for key, allowed in constraints.items()):
                    return True
    return False


def _lint_precision(candidate: ReviewedRuleCandidate) -> list[LintIssue]:
    if not _uses_exact_nadiamsa(candidate.expression):
        return []
    for requirement in candidate.precision_requirements:
        accepted = (
            requirement.key == "deva_keralam.precision.ascendant.reliable"
            and requirement.comparator == "equals"
            and requirement.value is True
        ) or (
            requirement.key == "deva_keralam.ascendant.nadiamsa.birth_time_precision_warning"
            and requirement.comparator == "equals"
            and requirement.value is False
        )
        if accepted and requirement.unavailable_reason.strip():
            return []
    return [LintIssue(
        "missing_precision_policy",
        "Exact Ascendant Nadiamsa rules require a fail-closed birth-time precision policy.",
        "precision_requirements",
    )]


def lint_reviewed_candidate(candidate: ReviewedRuleCandidate) -> Tuple[LintIssue, ...]:
    issues: list[LintIssue] = []
    if candidate.review_status != "reviewed_approved":
        issues.append(LintIssue("not_reviewed", "Candidate is not explicitly approved by a human reviewer."))
    if candidate.context_status not in REVIEWED_CONTEXT_STATUSES:
        issues.append(LintIssue("unreviewed_context", f"Context status is {candidate.context_status!r}."))
    if candidate.context_status == "qualified" and not candidate.context_qualification_acknowledged:
        issues.append(LintIssue(
            "unacknowledged_context_qualification",
            "Qualified context requires an explicit reviewer acknowledgement.",
        ))
    if not candidate.passage_key or not candidate.context_block_key:
        issues.append(LintIssue("missing_source_link", "Passage and context-block keys are required."))
    if not candidate.source.pdf_pages or not candidate.source.reference_label:
        issues.append(LintIssue("missing_source_link", "PDF pages and a source reference are required."))
    if candidate.source.editorial_status not in {"reviewed_clear", "reviewed_interpreted"}:
        issues.append(LintIssue("unreviewed_source", "Source editorial status is not executable."))
    if candidate.source_disputes:
        issues.append(LintIssue("source_dispute", "; ".join(candidate.source_disputes)))
    if candidate.inherited_ambiguities:
        issues.append(LintIssue("inherited_ambiguity", "; ".join(candidate.inherited_ambiguities)))
    if candidate.operationalization_status != "approved":
        issues.append(LintIssue(
            "not_operationalizable",
            f"Operationalization status is {candidate.operationalization_status!r}.",
        ))
    if candidate.timing_kind not in SUPPORTED_TIMING or candidate.outcome.get("timing") is not None:
        issues.append(LintIssue(
            "unsupported_timing",
            "This compiler release supports natal outcomes only; dasha, transit, age and life-phase timing are rejected.",
        ))
    issues.extend(_lint_expression(candidate.expression))
    if not _ascendant_context_is_possible(candidate.expression):
        issues.append(LintIssue(
            "impossible_ascendant_context",
            "The Ascendant Rashi, Navamsa and Nadiamsa conditions cannot occur at one longitude.",
            "expression",
        ))
    for index, requirement in enumerate(candidate.precision_requirements):
        if not is_canonical_fact_key(requirement.key):
            issues.append(LintIssue(
                "unknown_fact",
                f"Unknown precision fact key: {requirement.key!r}",
                f"precision_requirements.{index}",
            ))
        if requirement.comparator not in SUPPORTED_COMPARATORS:
            issues.append(LintIssue(
                "unsupported_comparator",
                f"Unsupported precision comparator: {requirement.comparator!r}",
                f"precision_requirements.{index}",
            ))
    issues.extend(_lint_precision(candidate))
    return tuple(issues)


def _anchors(expression: Mapping[str, Any]) -> Tuple[RuleAnchor, ...]:
    preferred = (
        "deva_keralam.ascendant.nadiamsa.ordinal",
        "deva_keralam.ascendant.nadiamsa.name",
        "deva_keralam.ascendant.rashi.name",
        "deva_keralam.ascendant.rashi.index",
    )
    values: Dict[str, list[Any]] = {}
    for _, node in _walk_expression(expression):
        if str(node.get("op") or "").lower() != "fact":
            continue
        key = str(node.get("key") or "")
        comparator = str(node.get("comparator") or "equals")
        if key not in preferred:
            continue
        if comparator == "equals":
            values.setdefault(key, []).append(node.get("value"))
        elif comparator == "in":
            values.setdefault(key, []).extend(node.get("value") or ())
    return tuple(RuleAnchor(key, tuple(dict.fromkeys(values[key]))) for key in preferred if values.get(key))


def compile_reviewed_candidate(candidate: ReviewedRuleCandidate) -> CompilationResult:
    issues = lint_reviewed_candidate(candidate)
    if issues:
        return CompilationResult(candidate.key, None, None, issues)
    spec = ContextualRuleSpec(
        key=candidate.key,
        title=candidate.title,
        source=candidate.source,
        expression=dict(candidate.expression),
        outcome=dict(candidate.outcome),
        anchors=_anchors(candidate.expression),
        precision_requirements=candidate.precision_requirements,
        inherited_context={
            **dict(candidate.inherited_context),
            "passage_key": candidate.passage_key,
            "context_block_key": candidate.context_block_key,
        },
        editorial_status=candidate.source.editorial_status or "reviewed_clear",
        topics=candidate.topics,
        scope=candidate.scope,
        # Executable in an isolated engine, but this module performs no global
        # registry or database publication.
        status="published",
        notes=(
            *candidate.notes,
            "Compiled from an explicitly reviewed candidate; no draft-table auto-publication.",
        ),
    )
    return CompilationResult(candidate.key, build_contextual_rule(spec), spec, ())


def compile_reviewed_batch(candidates: Iterable[ReviewedRuleCandidate]) -> Tuple[CompilationResult, ...]:
    return tuple(compile_reviewed_candidate(candidate) for candidate in candidates)
