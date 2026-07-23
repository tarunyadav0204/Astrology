from __future__ import annotations

from typing import List

from vedic_predictions.config.functional_nature import (
    FUNCTIONAL_BENEFICS,
    FUNCTIONAL_MALEFICS,
)

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from .base import EvidenceProvider
from .common import evidence_row


class FunctionalNatureProvider(EvidenceProvider):
    provider_id = "functional_nature"
    version = "1.0.0"
    supported_profiles = ("parashari_fomo_v1",)

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        chart = context.calculation.chart
        ascendant_sign = int(float(chart["ascendant"]) / 30.0)
        benefics = set(FUNCTIONAL_BENEFICS[ascendant_sign])
        malefics = set(FUNCTIONAL_MALEFICS[ascendant_sign])
        output: List[Evidence] = []
        seen = set()
        for level, planet in context.dasha_levels.items():
            if planet in seen:
                continue
            seen.add(planet)
            nature = (
                "benefic" if planet in benefics
                else "malefic" if planet in malefics
                else "neutral"
            )
            output.append(evidence_row(
                self, context, rule_id="functional_nature", planet=planet,
                house=int(chart["planets"][planet]["house"]),
                polarity=(
                    Polarity.SUPPORTIVE if nature == "benefic"
                    else Polarity.CHALLENGING if nature == "malefic"
                    else Polarity.NEUTRAL
                ),
                facts={"dasha_level": level, "functional_nature": nature, "ascendant_sign": ascendant_sign},
                independent_key=f"functional-nature:{planet}",
            ))
        return output
