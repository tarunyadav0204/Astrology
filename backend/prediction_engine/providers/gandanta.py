from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from .base import EvidenceProvider
from .common import evidence_row


class GandantaProvider(EvidenceProvider):
    provider_id = "gandanta"
    version = "1.1.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        gandanta = {
            row.get("planet"): row.get("gandanta_info")
            for row in context.calculation.gandanta.get("planets_in_gandanta", [])
        }
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            if planet in gandanta:
                output.append(evidence_row(
                    self, context, rule_id="natal_gandanta", planet=planet,
                    house=int(context.calculation.chart["planets"][planet]["house"]),
                    polarity=Polarity.CHALLENGING,
                    facts={"dasha_level": level, **(gandanta[planet] or {})},
                    independent_key=f"gandanta:{planet}",
                ))
        return output
