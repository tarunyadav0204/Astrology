from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity
from ..primitives import aspected_houses, ruled_houses
from .base import EvidenceProvider


class ConflictHouseProvider(EvidenceProvider):
    """Records obstruction pressure specific to an event family.

    This never creates an event candidate. It only adjusts outcome tone after
    the event's independent natal/timing gate has already passed.
    """

    provider_id = "conflict_house"
    version = "1.0.0"
    supported_profiles = ("parashari_fomo_v1",)

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        targets = set(context.conflicting_houses)
        chart = context.calculation.chart
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            natal = chart["planets"][planet]
            relations = {
                "lordship": set(ruled_houses(chart, planet)),
                "occupation": {int(natal["house"])},
                "natal_aspect": set(aspected_houses(planet, int(natal["house"]))),
            }
            for relation, houses in relations.items():
                for house in sorted(houses.intersection(targets)):
                    output.append(Evidence(
                        provider=self.provider_id,
                        provider_version=self.version,
                        rule_id=f"event_conflict_house_{relation}",
                        status=EvidenceStatus.EVALUATED,
                        subject=context.subject,
                        domain=context.event_family.domain,
                        window_start=context.window.start_date,
                        window_end=context.window.end_date,
                        planet=planet,
                        house=house,
                        importance=Importance.CONFIRMATORY,
                        polarity=Polarity.CHALLENGING,
                        facts={"dasha_level": level, "relation": relation},
                        independent_key=f"conflict:{level}:{planet}:{relation}:{house}",
                    ))
        return output
