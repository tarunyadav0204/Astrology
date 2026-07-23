from __future__ import annotations

from typing import List, Tuple

from calculators.base_calculator import BaseCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator

from ..context import EvaluationContext
from ..contracts import Evidence, Polarity
from .base import EvidenceProvider
from .common import dignity_polarity, evidence_row


class PlanetConditionProvider(EvidenceProvider):
    provider_id = "planet_condition"
    version = "1.1.0"

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        chart = context.calculation.chart
        output: List[Evidence] = []
        unique: List[Tuple[str, str]] = []
        seen = set()
        for level, planet in context.dasha_levels.items():
            if planet not in seen:
                seen.add(planet)
                unique.append((level, planet))

        transit_dignities = PlanetaryDignitiesCalculator(
            {"ascendant": chart["ascendant"], "planets": context.transit_states}
        ).calculate_planetary_dignities()
        base = BaseCalculator(chart)

        for level, planet in unique:
            natal = chart["planets"][planet]
            natal_condition = context.calculation.natal_dignities[planet]
            dignity = str(natal_condition.get("dignity") or "neutral")
            output.append(evidence_row(
                self, context, rule_id="natal_dignity", planet=planet,
                house=int(natal["house"]), polarity=dignity_polarity(dignity),
                facts={"dasha_level": level, "dignity": dignity},
                independent_key=f"natal-dignity:{planet}",
            ))
            natural = "benefic" if base.is_benefic(planet) else "malefic" if base.is_malefic(planet) else "neutral"
            output.append(evidence_row(
                self, context, rule_id="natural_nature", planet=planet,
                house=int(natal["house"]), polarity=Polarity.NEUTRAL,
                facts={"dasha_level": level, "natural_nature": natural},
                independent_key=f"natural-nature:{planet}",
            ))
            natal_combustion = str(natal_condition.get("combustion_status") or "normal")
            if natal_combustion == "cazimi":
                natal_combustion = "combust"
            if natal_combustion != "normal":
                output.append(evidence_row(
                    self, context, rule_id="natal_combustion", planet=planet,
                    house=int(natal["house"]),
                    polarity=Polarity.CHALLENGING,
                    facts={"dasha_level": level, "combustion": natal_combustion},
                    independent_key=f"natal-combustion:{planet}",
                ))
            if bool(natal_condition.get("retrograde")):
                output.append(evidence_row(
                    self, context, rule_id="natal_retrograde", planet=planet,
                    house=int(natal["house"]), polarity=Polarity.NEUTRAL,
                    facts={"dasha_level": level, "retrograde": True},
                    independent_key=f"natal-retrograde:{planet}",
                ))

            transit = context.transit_states[planet]
            transit_condition = transit_dignities[planet]
            transit_dignity = str(transit_condition.get("dignity") or "neutral")
            output.append(evidence_row(
                self, context, rule_id="transit_dignity", planet=planet,
                house=int(transit["house"]), polarity=dignity_polarity(transit_dignity),
                facts={"dasha_level": level, "dignity": transit_dignity, "sign": transit["sign"]},
                independent_key=f"transit-dignity:{planet}:{transit['sign']}",
            ))
            if transit["combustion"] != "normal":
                output.append(evidence_row(
                    self, context, rule_id="transit_combustion", planet=planet,
                    house=int(transit["house"]),
                    polarity=Polarity.CHALLENGING,
                    facts={"dasha_level": level, "combustion": transit["combustion"], "sun_distance": round(float(transit["sun_distance"]), 4)},
                    independent_key=f"transit-combustion:{planet}:{transit['combustion']}",
                ))
            if bool(transit["retrograde"]):
                output.append(evidence_row(
                    self, context, rule_id="transit_retrograde", planet=planet,
                    house=int(transit["house"]), polarity=Polarity.NEUTRAL,
                    facts={"dasha_level": level, "retrograde": True},
                    independent_key=f"transit-retrograde:{planet}",
                ))
        return output
