from __future__ import annotations

from typing import List

from calculators.base_calculator import BaseCalculator
from calculators.vedic_graha_drishti import planets_aspecting_house_sign

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from .base import EvidenceProvider
from .common import evidence_row


class AssociationProvider(EvidenceProvider):
    provider_id = "benefic_malefic_association"
    version = "1.0.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        planets = context.calculation.chart["planets"]
        base = BaseCalculator(context.calculation.chart)
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            natal = planets[planet]
            conjuncts = sorted(
                other for other, data in planets.items()
                if other != planet and other in BaseCalculator.NATURAL_BENEFICS + BaseCalculator.NATURAL_MALEFICS
                and int(data["sign"]) == int(natal["sign"])
            )
            aspectors = planets_aspecting_house_sign(planets, int(natal["sign"]))
            for relation, related in (("conjunction", conjuncts), ("aspect", aspectors)):
                for other in related:
                    polarity = Polarity.SUPPORTIVE if base.is_benefic(other) else Polarity.CHALLENGING if base.is_malefic(other) else Polarity.NEUTRAL
                    output.append(evidence_row(
                        self, context, rule_id=f"natal_{relation}_association",
                        planet=planet, house=int(natal["house"]), polarity=polarity,
                        facts={"dasha_level": level, "associated_planet": other, "relation": relation},
                        independent_key=f"association:{planet}:{other}:{relation}",
                    ))
        return output
