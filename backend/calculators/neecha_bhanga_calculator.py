"""Backward-compatible adapter for the canonical classical Neecha Bhanga engine."""

from __future__ import annotations

from typing import Any, Dict

from .classical_neecha_bhanga import SOURCE, calculate_classical_neecha_bhanga


class NeechaBhangaCalculator:
    """Keep legacy chat/AI contracts while using one Phaladeepika rule engine."""

    def __init__(self, chart_data: Dict[str, Any], divisional_charts=None):
        self.chart_data = chart_data
        # Retained in the constructor contract. Phaladeepika 7.26-30 does not
        # make Navamsha a condition, so divisional charts are deliberately unused.
        self.divisional_charts = divisional_charts or {}

    def calculate_neecha_bhanga(self) -> Dict[str, Dict[str, Any]]:
        classical = calculate_classical_neecha_bhanga(self.chart_data)
        results: Dict[str, Dict[str, Any]] = {}
        for planet, row in classical.items():
            present = bool(row["neecha_bhanga_present"])
            conditions = row["conditions_met"]
            results[planet] = {
                **row,
                # Legacy keys remain present, but contain no invented score.
                "overall_strength": "Established" if present else "Not established",
                "effects": {
                    "primary_effect": (
                        f"{planet}'s debilitation meets a Neechabhanga Raja Yoga condition "
                        "stated in Phaladeepika 7.26-30."
                        if present
                        else f"No Phaladeepika 7.26-30 cancellation condition was found for {planet}."
                    ),
                    "condition_count_note": f"{len(conditions)} classical condition(s) present",
                    "timing_note": "The cited verses do not prescribe a timing rule.",
                },
            }
        return results

    def get_neecha_bhanga_summary(self) -> Dict[str, Any]:
        results = self.calculate_neecha_bhanga()
        matched = [
            {
                "planet": planet,
                "strength": row["overall_strength"],
                "conditions": row["total_conditions"],
                "matched_rule_ids": row["matched_rule_ids"],
                "references": sorted({
                    condition["reference"] for condition in row["conditions_met"]
                }),
            }
            for planet, row in results.items()
            if row["neecha_bhanga_present"]
        ]
        summary = (
            f"{len(matched)} out of {len(results)} debilitated planet(s) meet "
            "Phaladeepika 7.26-30 Neecha Bhanga conditions"
            if results
            else "No debilitated planets found in this chart"
        )
        return {
            "total_debilitated_planets": len(results),
            "total_neecha_bhanga_planets": len(matched),
            # Both historical names are returned because different chat paths
            # consumed different versions of the old contract.
            "neecha_bhanga_planets": matched,
            "planets_with_neecha_bhanga": matched,
            "detailed_results": results,
            "source": SOURCE,
            "summary": summary,
        }
