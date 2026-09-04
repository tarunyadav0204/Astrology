from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from ..primitives import aspected_houses
from calculators.avayogi_policy import AVAYOGI_REVERSAL_HOUSES, avayogi_effect
from .base import EvidenceProvider
from .common import evidence_row


class YogiAvayogiProvider(EvidenceProvider):
    provider_id = "yogi_avayogi"
    version = "1.1.0"

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
                placement_house = int(context.calculation.chart["planets"][planet]["house"])
                resolution = avayogi_effect(
                    placement_house=placement_house,
                    tithi_shunya_overlap=overlap,
                )
                output.append(evidence_row(
                    self, context, rule_id="avayogi_lord_active", planet=planet,
                    house=placement_house,
                    polarity=Polarity(resolution["polarity"]),
                    facts={
                        "dasha_level": level,
                        "avayogi_lord": avayogi_lord,
                        "tithi_shunya_overlap": overlap,
                        "avayogi_effect": resolution,
                    },
                    independent_key=f"avayogi:{planet}",
                ))
                for target_house in sorted(set(context.all_houses) & AVAYOGI_REVERSAL_HOUSES):
                    if target_house not in aspected_houses(planet, placement_house):
                        continue
                    aspect_resolution = avayogi_effect(
                        placement_house=placement_house,
                        target_house=target_house,
                        relation="aspector",
                        tithi_shunya_overlap=overlap,
                    )
                    output.append(evidence_row(
                        self, context,
                        rule_id="avayogi_aspect_reversal",
                        planet=planet,
                        house=target_house,
                        polarity=Polarity.SUPPORTIVE,
                        facts={
                            "dasha_level": level,
                            "avayogi_lord": avayogi_lord,
                            "avayogi_effect": aspect_resolution,
                        },
                        independent_key=f"avayogi-aspect-reversal:{planet}:H{target_house}",
                    ))
        return output
