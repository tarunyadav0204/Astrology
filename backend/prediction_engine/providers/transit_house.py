from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity
from ..primitives import aspected_houses
from .base import EvidenceProvider


class TransitHouseProvider(EvidenceProvider):
    provider_id = "transit_house"
    version = "1.0.0"
    supported_profiles = ("parashari_fomo_v1",)

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        output: List[Evidence] = []
        targets = set(context.all_houses)
        primary = set(context.primary_houses)
        for level, planet in context.dasha_levels.items():
            transit = context.transit_states.get(planet)
            if transit is None:
                raise KeyError(f"Missing transit state for dasha planet {planet}")
            transit_house = int(transit["house"])
            relations = {
                "occupation": {transit_house},
                "aspect": set(aspected_houses(planet, transit_house)),
            }
            for relation, houses in relations.items():
                for house in sorted(houses.intersection(targets)):
                    output.append(Evidence(
                        provider=self.provider_id,
                        provider_version=self.version,
                        rule_id=(
                            "dasha_planet_transits_event_house"
                            if relation == "occupation"
                            else "dasha_planet_transit_aspects_event_house"
                        ),
                        status=EvidenceStatus.EVALUATED,
                        subject=context.subject,
                        domain=context.event_family.domain,
                        window_start=context.window.start_date,
                        window_end=context.window.end_date,
                        planet=planet,
                        house=house,
                        importance=Importance.PRIMARY if house in primary else Importance.SECONDARY,
                        polarity=Polarity.NEUTRAL,
                        facts={
                            "dasha_level": level,
                            "transit_house": transit_house,
                            "relation": relation,
                        },
                        independent_key=f"transit-event:{planet}:{relation}:{house}",
                    ))
        return output
