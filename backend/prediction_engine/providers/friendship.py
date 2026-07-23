from __future__ import annotations

from typing import List

from calculators.base_calculator import BaseCalculator
from calculators.friendship_calculator import FriendshipCalculator

from ..context import EvaluationContext
from ..contracts import Evidence
from ..primitives import planetary_connections
from .base import EvidenceProvider
from .common import evidence_row, relation_polarity


class FriendshipProvider(EvidenceProvider):
    provider_id = "friendship"
    version = "1.2.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        chart = context.calculation.chart
        planets = chart["planets"]
        base = BaseCalculator(chart)
        calculator = FriendshipCalculator()
        output: List[Evidence] = []
        for level, planet in context.dasha_levels.items():
            # Panchadha Maitri is kept to the seven classical grahas in this
            # conservative profile. Node friendship conventions are disputed.
            if planet in {"Rahu", "Ketu"}:
                continue
            natal = planets[planet]
            for house in context.primary_houses:
                house_sign = int(chart["houses"][house - 1]["sign"])
                house_lord = base.get_sign_lord(house_sign)
                direct_relations = planetary_connections(chart, planet, house_lord)
                if planet != house_lord and not direct_relations:
                    continue
                relation = "self" if planet == house_lord else calculator.calculate_compound_relation(
                    planet, house_lord, int(natal["sign"]), int(planets[house_lord]["sign"])
                )
                output.append(evidence_row(
                    self, context,
                    rule_id="compound_friendship_with_event_house_lord",
                    planet=planet, house=house, polarity=relation_polarity(relation),
                    facts={
                        "dasha_level": level,
                        "house_lord": house_lord,
                        "compound_relation": relation,
                        "direct_relations": direct_relations,
                    },
                    independent_key=f"friendship:{planet}:{house_lord}:{house}",
                ))
        return output
