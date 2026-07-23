class PredictionEngineError(RuntimeError):
    """Base error for deterministic prediction failures."""


class PredictionInputError(PredictionEngineError):
    """The request or chart input is incomplete or invalid."""


class PredictionCalculationError(PredictionEngineError):
    """A required astronomical/astrological calculation failed."""


class PredictionConfigurationError(PredictionEngineError):
    """A profile, provider, or rule configuration is invalid."""
