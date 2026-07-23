from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from .base import EvidenceProvider
from .common import evidence_row


class BadhakaProvider(EvidenceProvider):
    provider_id = "badhaka"
    version = "1.0.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            if planet == context.calculation.badhaka_lord:
                natal = context.calculation.chart["planets"][planet]
                output.append(evidence_row(
                    self, context, rule_id="badhaka_lord_active", planet=planet,
                    house=int(natal["house"]), polarity=Polarity.CHALLENGING,
                    facts={"dasha_level": level, "badhaka_lord": planet},
                    independent_key=f"badhaka:{planet}",
                ))
        return output
