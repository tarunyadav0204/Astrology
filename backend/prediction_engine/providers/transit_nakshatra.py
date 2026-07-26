from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity
from ..nakshatra_transit import (
    NAKSHATRA_TRANSIT_VERSION,
    nakshatra_lord_house_relevance,
    nakshatra_lord_expression,
    nakshatra_lord_natal_condition,
    nakshatra_transit_relation,
)
from .base import EvidenceProvider


class TransitNakshatraResonanceProvider(EvidenceProvider):
    provider_id = "transit_nakshatra_resonance"
    version = NAKSHATRA_TRANSIT_VERSION
    supported_profiles = ("parashari_fomo_v1",)
    required_providers = ("dasha_house_activation",)

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        output: List[Evidence] = []
        chart = context.calculation.chart
        for level, planet in context.dasha_levels.items():
            natal = chart["planets"].get(planet)
            transit = context.transit_states.get(planet)
            if natal is None or transit is None:
                continue
            resonance = nakshatra_transit_relation(
                float(natal["longitude"]),
                float(transit["longitude"]),
            )
            if resonance is None:
                continue
            lord = str(resonance["common_nakshatra_lord"])
            for house in context.all_houses:
                relevant, relevance_reasons = nakshatra_lord_house_relevance(
                    chart, lord, house, context.dasha_levels.values()
                )
                lord_condition = nakshatra_lord_natal_condition(
                    chart, context.calculation.natal_dignities, lord
                )
                output.append(Evidence(
                    provider=self.provider_id,
                    provider_version=self.version,
                    rule_id=(
                        "dasha_planet_exact_natal_nakshatra_return"
                        if resonance["relation"] == "exact_natal_nakshatra_return"
                        else "dasha_planet_nakshatra_dispositor_resonance"
                    ),
                    status=EvidenceStatus.EVALUATED,
                    subject=context.subject,
                    domain=context.event_family.domain,
                    window_start=context.window.start_date,
                    window_end=context.window.end_date,
                    planet=planet,
                    house=house,
                    importance=Importance.CONFIRMATORY,
                    polarity=Polarity.NEUTRAL,
                    facts={
                        "dasha_level": level,
                        **resonance,
                        "nakshatra_lord_relevant": relevant,
                        "nakshatra_lord_relevance_reasons": relevance_reasons,
                        "nakshatra_lord_natal_condition": lord_condition,
                        "nakshatra_lord_expression": (
                            nakshatra_lord_expression(lord_condition)
                        ),
                        "creates_house_promise": False,
                        "qualifies_as_direct_natal_contact": False,
                        "qualifies_as_strong_natal_return_confirmation": (
                            resonance["relation"] == "exact_natal_nakshatra_return"
                        ),
                    },
                    independent_key=(
                        f"transit-nakshatra:{planet}:{resonance['relation']}:"
                        f"{resonance['transit_nakshatra']['index']}"
                    ),
                ))
        return output
