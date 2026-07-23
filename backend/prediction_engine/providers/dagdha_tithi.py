from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from .base import EvidenceProvider
from .common import evidence_row


class DagdhaTithiProvider(EvidenceProvider):
    provider_id = "dagdha_tithi"
    version = "1.0.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        points = context.calculation.yogi_points
        dagdha = points.get("dagdha_rashi") or {}
        tithi = points.get("tithi_shunya_rashi") or {}
        overlap = bool((points.get("avayogi_tithi_shunya_overlap") or {}).get("is_active"))
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            natal = context.calculation.chart["planets"][planet]
            if int(natal["sign"]) == int(dagdha["sign"]):
                output.append(evidence_row(
                    self, context, rule_id="planet_in_dagdha_rashi", planet=planet,
                    house=int(natal["house"]), polarity=Polarity.CHALLENGING,
                    facts={"dasha_level": level, "dagdha_sign": dagdha["sign"]},
                    independent_key=f"dagdha:{planet}",
                ))
            if int(natal["sign"]) == int(tithi["sign"]):
                output.append(evidence_row(
                    self, context, rule_id="planet_in_tithi_shunya_rashi", planet=planet,
                    house=int(natal["house"]),
                    polarity=Polarity.MIXED if overlap else Polarity.CHALLENGING,
                    facts={"dasha_level": level, "tithi_shunya_sign": tithi["sign"], "avayogi_overlap": overlap},
                    independent_key=f"tithi-shunya:{planet}",
                ))
        return output
