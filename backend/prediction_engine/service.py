from __future__ import annotations

from datetime import timedelta

from .contracts import PredictionRequest, PredictionResult
from .engine import PredictionEngine
from .primitives import build_calculation_context
from .profiles import get_profile
from .providers import (
    AssociationProvider,
    BadhakaProvider,
    ConflictHouseProvider,
    DagdhaTithiProvider,
    DashaHouseActivationProvider,
    DashaPlanetRelationshipProvider,
    DispositorActivationProvider,
    FriendshipProvider,
    FunctionalNatureProvider,
    GandantaProvider,
    PlanetConditionProvider,
    TransitHouseProvider,
    TransitNatalRelationProvider,
    YogiAvayogiProvider,
)
from .registry import EvidenceProviderRegistry


def build_default_registry() -> EvidenceProviderRegistry:
    return EvidenceProviderRegistry(
        (
            DashaHouseActivationProvider(),
            DashaPlanetRelationshipProvider(),
            DispositorActivationProvider(),
            TransitHouseProvider(),
            TransitNatalRelationProvider(),
            PlanetConditionProvider(),
            FunctionalNatureProvider(),
            FriendshipProvider(),
            AssociationProvider(),
            ConflictHouseProvider(),
            BadhakaProvider(),
            YogiAvayogiProvider(),
            GandantaProvider(),
            DagdhaTithiProvider(),
        )
    )


class PredictionService:
    """Public in-process service boundary for deterministic predictions."""

    def __init__(self, *, registry: EvidenceProviderRegistry | None = None) -> None:
        self.registry = registry or build_default_registry()
        self.engine = PredictionEngine(self.registry)

    def generate(self, request: PredictionRequest) -> PredictionResult:
        profile = get_profile(request.profile)
        # horizon_days is a count including as_of; a 90-day request must not
        # silently calculate 91 inclusive calendar dates.
        horizon_end = request.as_of + timedelta(days=request.horizon_days - 1)
        calculation = build_calculation_context(
            request.birth,
            request.as_of,
            horizon_end,
        )
        return self.engine.generate(request, calculation, profile)
