"""Deterministic evaluator for versioned classical rule packs."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional

from .models import ClassicalRule, RuleInputUnavailable, RuleResult


class ClassicalRuleEngine:
    """Evaluate published rules without generating or interpreting prose."""

    ENGINE_VERSION = "classical-rule-engine/1.0.0"

    def __init__(self, rules: Iterable[ClassicalRule]):
        self.rules = tuple(rules)
        keys = [rule.key for rule in self.rules]
        if len(keys) != len(set(keys)):
            raise ValueError("Classical rule keys must be unique")

    def evaluate(
        self,
        chart: Mapping[str, Any],
        birth_data: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        results = []
        for rule in self.rules:
            if rule.status != "published":
                continue
            source = {
                "profile": rule.source.key,
                "work": rule.source.work,
                "chapter": rule.source.chapter,
                "verses": [rule.source.verse_start, rule.source.verse_end],
                "reference": rule.source.reference,
                "witness_url": rule.source.witness_url,
                "witness_policy": rule.source.witness_policy,
            }
            try:
                payload = rule.evaluator(chart, birth_data)
                applicability = str(payload.pop("applicability", "matched"))
                results.append(RuleResult(
                    rule_key=rule.key,
                    title=rule.title,
                    source=source,
                    status=rule.status,
                    applicability=applicability,
                    evidence=payload,
                    calculator_binding=rule.calculator_binding,
                ).as_dict())
            except RuleInputUnavailable as exc:
                results.append(RuleResult(
                    rule_key=rule.key,
                    title=rule.title,
                    source=source,
                    status=rule.status,
                    applicability="unavailable",
                    reason=str(exc),
                    calculator_binding=rule.calculator_binding,
                ).as_dict())
        return {
            "engine_version": self.ENGINE_VERSION,
            "rules_evaluated": len(results),
            "results": results,
            "fallback_used": False,
        }
