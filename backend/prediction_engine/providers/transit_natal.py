from __future__ import annotations

from typing import List

from calculators.vedic_graha_drishti import get_aspect_houses_for_planet
from calculators.badhaka_calculator import BadhakaCalculator

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity
from ..primitives import angular_distance
from .base import EvidenceProvider


class TransitNatalRelationProvider(EvidenceProvider):
    provider_id = "transit_natal_relation"
    version = "1.0.0"
    supported_profiles = ("parashari_fomo_v1",)

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        output: List[Evidence] = []
        chart = context.calculation.chart
        targets = set(context.dasha_levels.values())
        for house in context.all_houses:
            sign = int(chart["houses"][house - 1]["sign"])
            targets.add(BadhakaCalculator.SIGN_LORDS[sign])
            targets.update(
                name for name, placement in chart["planets"].items()
                if int(placement["house"]) == house
            )

        seen = set()
        for level, planet in context.dasha_levels.items():
            transit = context.transit_states.get(planet)
            if transit is None:
                raise KeyError(f"Missing transit state for dasha planet {planet}")
            for natal_planet in sorted(targets):
                natal = chart["planets"].get(natal_planet)
                if natal is None:
                    continue
                transit_sign = int(transit["sign"])
                natal_sign = int(natal["sign"])
                aspect_number = ((natal_sign - transit_sign) % 12) + 1
                if aspect_number not in get_aspect_houses_for_planet(planet):
                    continue
                relation = "conjunction" if aspect_number == 1 else "aspect"
                key = (planet, natal_planet, relation, aspect_number)
                if key in seen:
                    continue
                seen.add(key)
                output.append(Evidence(
                provider=self.provider_id,
                provider_version=self.version,
                rule_id=f"dasha_planet_transit_{relation}_natal_relevant_planet",
                status=EvidenceStatus.EVALUATED,
                subject=context.subject,
                domain=context.event_family.domain,
                window_start=context.window.start_date,
                window_end=context.window.end_date,
                planet=planet,
                house=int(natal["house"]),
                importance=Importance.CONFIRMATORY,
                polarity=Polarity.NEUTRAL,
                facts={
                    "dasha_level": level,
                    "natal_planet": natal_planet,
                    "transit_sign": transit_sign,
                    "natal_sign": natal_sign,
                    "aspect_number": aspect_number,
                    "relation": relation,
                    "angular_distance_degrees": round(
                        angular_distance(transit["longitude"], natal["longitude"]), 4
                    ),
                },
                independent_key=(
                    f"transit-natal:{planet}:{natal_planet}:{relation}:{aspect_number}"
                ),
            ))
        return output
