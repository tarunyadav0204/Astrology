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
        has_classical_dagdha_list = "tithi_dagdha_rashis" in points
        dagdha_rows = list(points.get("tithi_dagdha_rashis") or [])
        dagdha_by_sign = {int(row["sign"]): row for row in dagdha_rows if row.get("sign") is not None}
        overlap = bool((points.get("avayogi_tithi_shunya_overlap") or {}).get("is_active"))
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            natal = context.calculation.chart["planets"][planet]
            natal_sign = int(natal["sign"])
            if has_classical_dagdha_list and natal_sign in dagdha_by_sign:
                row = dagdha_by_sign[natal_sign]
                output.append(evidence_row(
                    self, context, rule_id="planet_in_dagdha_rashi", planet=planet,
                    house=int(natal["house"]), polarity=Polarity.CHALLENGING,
                    facts={"dasha_level": level, "dagdha_sign": row["sign"], "tithi_derived": True},
                    independent_key=f"dagdha:{planet}",
                ))
            elif not has_classical_dagdha_list and dagdha.get("sign") is not None and natal_sign == int(dagdha["sign"]):
                output.append(evidence_row(
                    self, context, rule_id="planet_in_dagdha_rashi", planet=planet,
                    house=int(natal["house"]), polarity=Polarity.CHALLENGING,
                    facts={"dasha_level": level, "dagdha_sign": dagdha["sign"]},
                    independent_key=f"dagdha:{planet}",
                ))
            if not has_classical_dagdha_list and tithi.get("sign") is not None and natal_sign == int(tithi["sign"]):
                output.append(evidence_row(
                    self, context, rule_id="planet_in_tithi_shunya_rashi", planet=planet,
                    house=int(natal["house"]),
                    polarity=Polarity.MIXED if overlap else Polarity.CHALLENGING,
                    facts={"dasha_level": level, "tithi_shunya_sign": tithi["sign"], "avayogi_overlap": overlap},
                    independent_key=f"tithi-shunya:{planet}",
                ))
        return output
