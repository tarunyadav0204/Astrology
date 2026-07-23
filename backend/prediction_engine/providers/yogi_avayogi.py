from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from .base import EvidenceProvider
from .common import evidence_row


class YogiAvayogiProvider(EvidenceProvider):
    provider_id = "yogi_avayogi"
    version = "1.0.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        points = context.calculation.yogi_points
        yogi_lord = (points.get("yogi") or {}).get("lord")
        avayogi_lord = (points.get("avayogi") or {}).get("lord")
        overlap = bool((points.get("avayogi_tithi_shunya_overlap") or {}).get("is_active"))
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            if planet == yogi_lord:
                output.append(evidence_row(
                    self, context, rule_id="yogi_lord_active", planet=planet,
                    house=int(context.calculation.chart["planets"][planet]["house"]),
                    polarity=Polarity.SUPPORTIVE,
                    facts={"dasha_level": level, "yogi_lord": yogi_lord},
                    independent_key=f"yogi:{planet}",
                ))
            if planet == avayogi_lord:
                output.append(evidence_row(
                    self, context, rule_id="avayogi_lord_active", planet=planet,
                    house=int(context.calculation.chart["planets"][planet]["house"]),
                    polarity=Polarity.MIXED if overlap else Polarity.CHALLENGING,
                    facts={"dasha_level": level, "avayogi_lord": avayogi_lord, "tithi_shunya_overlap": overlap},
                    independent_key=f"avayogi:{planet}",
                ))
        return output
