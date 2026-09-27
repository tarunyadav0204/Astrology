"""Marriage-matching facade for the canonical classical Mangal Dosha result."""

from __future__ import annotations

from typing import Any, Dict, Optional

from calculators.classical_mangal_dosha import (
    calculate_classical_mangal_dosha,
    calculate_mangal_pair_balance,
)
from .rules import RuleProfile, get_rule_profile


class ManglikAnalyzer:
    def __init__(self, rule_profile: RuleProfile | str = "balanced_modern") -> None:
        self.rule_profile = rule_profile if isinstance(rule_profile, RuleProfile) else get_rule_profile(rule_profile)

    def analyze(self, chart: Dict[str, Any], d9_chart: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = calculate_classical_mangal_dosha(chart)
        # Kept for old clients. Only the selected Lagna reading is active;
        # Moon and Venus remain visibly supplementary and D9 is not used.
        result["active_references"] = ["lagna"] if result["present"] else []
        return result

    def compatibility(self, person1: Dict[str, Any], person2: Dict[str, Any]) -> Dict[str, Any]:
        pair = calculate_mangal_pair_balance(person1, person2)
        pair["classical_status"] = pair["status"]
        # Human-facing compatibility label retained for existing clients.
        pair["status"] = "Compatible" if pair["balanced"] or not pair["one_sided"] else "Sensitive"
        return pair
