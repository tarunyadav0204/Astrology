from __future__ import annotations

from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity
from ..house_activation import dasha_relationships
from .base import EvidenceProvider


class DashaPlanetRelationshipProvider(EvidenceProvider):
    """Expose MD/AD/PD sambandha instead of requiring one universal carrier."""

    provider_id = "dasha_planet_relationship"
    version = "1.0.0"
    supported_profiles = ("parashari_fomo_v1",)

    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        output: List[Evidence] = []
        for row in dasha_relationships(context.calculation.chart, context.window):
            if not row.relations:
                continue
            output.append(Evidence(
                provider=self.provider_id,
                provider_version=self.version,
                rule_id="md_ad_pd_natal_sambandha",
                status=EvidenceStatus.EVALUATED,
                subject=context.subject,
                domain=context.event_family.domain,
                window_start=context.window.start_date,
                window_end=context.window.end_date,
                planet=None,
                house=None,
                importance=Importance.CONFIRMATORY,
                polarity=Polarity.NEUTRAL,
                facts={
                    "first_level": row.first_level,
                    "first_planet": row.first_planet,
                    "second_level": row.second_level,
                    "second_planet": row.second_planet,
                    "relations": list(row.relations),
                    "natal_houses": list(row.natal_houses),
                },
                independent_key=(
                    f"dasha-relationship:{row.first_level}:{row.first_planet}:"
                    f"{row.second_level}:{row.second_planet}:"
                    f"{','.join(row.relations)}"
                ),
            ))
        return output
