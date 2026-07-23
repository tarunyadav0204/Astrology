from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Sequence

from .contracts import BirthChartInput, PredictionWindow
from .taxonomy import EventFamily


@dataclass(frozen=True)
class CalculationContext:
    birth: BirthChartInput
    chart: Dict[str, Any]
    natal_dignities: Dict[str, Any]
    yogi_points: Dict[str, Any]
    gandanta: Dict[str, Any]
    badhaka_lord: str
    windows: Sequence[PredictionWindow]
    transit_states_by_signature: Dict[str, Dict[str, Dict[str, Any]]]
    divisional_charts: Dict[str, Dict[str, Any]]
    daily_transit_states: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
    natal_promises: Sequence[Dict[str, Any]] = ()
    validated_yogas: Sequence[Dict[str, Any]] = ()


@dataclass(frozen=True)
class EvaluationContext:
    calculation: CalculationContext
    window: PredictionWindow
    subject: str
    event_family: EventFamily
    primary_houses: Sequence[int]
    supporting_houses: Sequence[int]
    conflicting_houses: Sequence[int]

    @property
    def all_houses(self) -> Sequence[int]:
        return tuple(dict.fromkeys((*self.primary_houses, *self.supporting_houses)))

    @property
    def dasha_levels(self) -> Dict[str, str]:
        return {
            "MD": self.window.mahadasha,
            "AD": self.window.antardasha,
            "PD": self.window.pratyantardasha,
        }

    @property
    def transit_states(self) -> Dict[str, Dict[str, Any]]:
        return self.calculation.transit_states_by_signature[self.window.transit_signature]
