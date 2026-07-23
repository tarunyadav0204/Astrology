from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity
from ..primitives import aspected_houses, ruled_houses
from .base import EvidenceProvider


class DashaHouseActivationProvider(EvidenceProvider):
    provider_id = "dasha_house_activation"
    version = "1.0.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        output: List[Evidence] = []
        chart = context.calculation.chart
        target_houses = set(context.all_houses)
        primary_houses = set(context.primary_houses)

        for level, planet in context.dasha_levels.items():
            natal = chart["planets"].get(planet)
            if not natal:
                raise KeyError(f"Dasha planet {planet} is absent from the natal chart")
            relations = {
                "lordship": set(ruled_houses(chart, planet)),
                "occupation": {int(natal["house"])},
                "natal_aspect": set(aspected_houses(planet, int(natal["house"]))),
            }
            for relation, houses in relations.items():
                for house in sorted(houses.intersection(target_houses)):
                    output.append(
                        Evidence(
                            provider=self.provider_id,
                            provider_version=self.version,
                            rule_id=f"dasha_{relation}",
                            status=EvidenceStatus.EVALUATED,
                            subject=context.subject,
                            domain=context.event_family.domain,
                            window_start=context.window.start_date,
                            window_end=context.window.end_date,
                            planet=planet,
                            house=house,
                            importance=(
                                Importance.PRIMARY
                                if house in primary_houses
                                else Importance.SECONDARY
                            ),
                            polarity=Polarity.NEUTRAL,
                            facts={"dasha_level": level, "relation": relation},
                            independent_key=f"dasha:{level}:{planet}:{relation}:{house}",
                        )
                    )

            if planet in context.event_family.karakas and any(
                evidence.planet == planet for evidence in output
            ):
                output.append(
                    Evidence(
                        provider=self.provider_id,
                        provider_version=self.version,
                        rule_id="event_karaka_confirmation",
                        status=EvidenceStatus.EVALUATED,
                        subject=context.subject,
                        domain=context.event_family.domain,
                        window_start=context.window.start_date,
                        window_end=context.window.end_date,
                        planet=planet,
                        house=None,
                        importance=Importance.CONFIRMATORY,
                        polarity=Polarity.NEUTRAL,
                        facts={"dasha_level": level, "karaka_for": context.event_family.key},
                        independent_key=f"karaka:{level}:{planet}:{context.event_family.key}",
                    )
                )
        return output
