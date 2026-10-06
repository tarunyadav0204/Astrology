"""Canonical, source-carrying facts shared by later classical rules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


@dataclass(frozen=True)
class ClassicalFact:
    key: str
    value: Any
    source_rules: Tuple[str, ...]
    source_references: Tuple[str, ...]
    calculator_bindings: Tuple[str, ...]
    evidence: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ClassicalFactSet:
    """Immutable-by-key fact collection; conflicting producers fail loudly."""

    VERSION = "classical-facts/1.0.0"

    def __init__(self, facts: Iterable[ClassicalFact] = ()):
        self._facts: Dict[str, ClassicalFact] = {}
        for fact in facts:
            self.add(fact)

    def add(self, fact: ClassicalFact) -> None:
        existing = self._facts.get(fact.key)
        if existing and existing != fact:
            raise ValueError(f"Conflicting classical fact producers for {fact.key}")
        self._facts[fact.key] = fact

    def get(self, key: str) -> Optional[ClassicalFact]:
        return self._facts.get(str(key))

    def require(self, key: str) -> ClassicalFact:
        fact = self.get(key)
        if fact is None:
            raise KeyError(f"Required classical fact is unavailable: {key}")
        return fact

    def as_dict(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "facts": {key: fact.as_dict() for key, fact in sorted(self._facts.items())},
        }


@dataclass(frozen=True)
class ExpressionResult:
    matched: Optional[bool]
    used_facts: Tuple[Dict[str, Any], ...] = ()
    failures: Tuple[str, ...] = ()

    @property
    def status(self) -> str:
        if self.matched is None:
            return "unavailable"
        return "matched" if self.matched else "not_matched"

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status
        return payload


def evaluate_fact_expression(expression: Mapping[str, Any], facts: ClassicalFactSet) -> ExpressionResult:
    """Evaluate a small explicit Boolean AST and preserve premise evidence."""
    operator = str(expression.get("op") or "").lower()
    if operator == "fact":
        key = str(expression.get("key") or "")
        fact = facts.get(key)
        if fact is None:
            return ExpressionResult(None, failures=(f"Missing fact: {key}",))
        comparator = str(expression.get("comparator") or "equals")
        expected = expression.get("value")
        actual = fact.value
        if comparator == "equals":
            matched = actual == expected
        elif comparator == "not_equals":
            matched = actual != expected
        elif comparator == "in":
            matched = actual in (expected or [])
        elif comparator == "contains":
            matched = expected in (actual or [])
        elif comparator == "exists":
            matched = actual is not None
        elif comparator == "gte":
            matched = actual >= expected
        elif comparator == "lte":
            matched = actual <= expected
        elif comparator == "gt":
            matched = actual > expected
        elif comparator == "lt":
            matched = actual < expected
        elif comparator == "between":
            if not isinstance(expected, (list, tuple)) or len(expected) != 2:
                raise ValueError("between comparator requires [minimum, maximum]")
            matched = expected[0] <= actual <= expected[1]
        else:
            raise ValueError(f"Unsupported classical fact comparator: {comparator}")
        used = ({
            "key": key, "actual": actual, "expected": expected,
            "comparator": comparator, "matched": matched,
            "source_rules": fact.source_rules,
            "source_references": fact.source_references,
        },)
        return ExpressionResult(matched, used, () if matched else (f"{key}: expected {comparator} {expected!r}, found {actual!r}",))

    children = tuple(expression.get("children") or ())
    if operator == "not":
        if len(children) != 1:
            raise ValueError("not requires exactly one child")
        child = evaluate_fact_expression(children[0], facts)
        if child.matched is None:
            return child
        return ExpressionResult(not child.matched, child.used_facts, () if not child.matched else ("Negated premise matched",))
    if operator not in {"all", "any", "at_least"}:
        raise ValueError(f"Unsupported classical expression operator: {operator}")
    results = tuple(evaluate_fact_expression(child, facts) for child in children)
    match_count = sum(1 for result in results if result.matched is True)
    unavailable_count = sum(1 for result in results if result.matched is None)
    if operator == "all":
        matched = False if any(result.matched is False for result in results) else (None if unavailable_count else True)
    elif operator == "any":
        matched = True if match_count else (None if unavailable_count else False)
    else:
        threshold = int(expression.get("count") or 0)
        if threshold < 1:
            raise ValueError("at_least requires a positive count")
        if match_count >= threshold:
            matched = True
        elif match_count + unavailable_count >= threshold:
            matched = None
        else:
            matched = False
    return ExpressionResult(
        matched,
        tuple(fact for result in results for fact in result.used_facts),
        tuple(failure for result in results for failure in result.failures),
    )
