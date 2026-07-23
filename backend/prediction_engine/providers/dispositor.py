from __future__ import annotations

from typing import List

from calculators.base_calculator import BaseCalculator

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity
from ..primitives import aspected_houses, ruled_houses
from .base import EvidenceProvider


class DispositorActivationProvider(EvidenceProvider):
    provider_id = "dispositor_activation"
    version = "1.0.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        chart = context.calculation.chart
        base = BaseCalculator(chart)
        targets = set(context.all_houses)
        primary = set(context.primary_houses)
        output: List[Evidence] = []
        for level, dasha_planet in context.dasha_levels.items():
            dasha_natal = chart["planets"][dasha_planet]
            dispositor = base.get_sign_lord(int(dasha_natal["sign"]))
            dispositor_natal = chart["planets"].get(dispositor)
            if dispositor_natal is None:
                raise KeyError(
                    f"Dispositor {dispositor} for {dasha_planet} is absent from natal chart"
                )
            relations = {
                "lordship": set(ruled_houses(chart, dispositor)),
                "occupation": {int(dispositor_natal["house"])},
                "natal_aspect": set(
                    aspected_houses(dispositor, int(dispositor_natal["house"]))
                ),
            }
            for relation, houses in relations.items():
                for house in sorted(houses.intersection(targets)):
                    output.append(
                        Evidence(
                            provider=self.provider_id,
                            provider_version=self.version,
                            rule_id=f"dasha_dispositor_{relation}",
                            status=EvidenceStatus.EVALUATED,
                            subject=context.subject,
                            domain=context.event_family.domain,
                            window_start=context.window.start_date,
                            window_end=context.window.end_date,
                            planet=dasha_planet,
                            house=house,
                            importance=(
                                Importance.PRIMARY
                                if house in primary
                                else Importance.SECONDARY
                            ),
                            polarity=Polarity.NEUTRAL,
                            facts={
                                "dasha_level": level,
                                "dasha_planet": dasha_planet,
                                "dispositor": dispositor,
                                "relation": relation,
                            },
                            independent_key=(
                                f"dispositor:{level}:{dasha_planet}:"
                                f"{dispositor}:{relation}:{house}"
                            ),
                        )
                    )
        return output
