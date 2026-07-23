"""Reusable deterministic prediction engine.

Only the public contracts and service are exported here. Consumers must not
couple themselves to provider or policy internals.
"""

from .contracts import LifeContext, PredictionRequest, PredictionResult
from .service import PredictionService

__all__ = ["LifeContext", "PredictionRequest", "PredictionResult", "PredictionService"]
