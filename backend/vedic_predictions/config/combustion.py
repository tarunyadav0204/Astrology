"""Compatibility exports for the canonical Parashari combustion service.

New calculations must call ``calculators.classical_combustion`` so motion and
the source evidence are retained. These names remain for older consumers.
"""

from calculators.classical_combustion import CLASSICAL_COMBUSTION_LIMITS


COMBUSTION_THRESHOLDS = {
    planet: float(limits["direct"])
    for planet, limits in CLASSICAL_COMBUSTION_LIMITS.items()
}

# Retained as imports only. The selected Parashari rule has no cazimi state.
CAZIMI_THRESHOLD = None
CAZIMI_CAPABLE = []

# The source supplies a condition and loss-of-rays doctrine, not an invented
# numeric multiplier. Prediction clients receive the condition separately.
COMBUSTION_MULTIPLIERS = {
    "combust": 1.0,
    "normal": 1.0,
}
