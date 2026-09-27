"""Isolated professional Health V2 calculations.

Health V2 is intentionally additive.  Legacy health routes and calculators stay
active until the new engine has been validated on real charts and explicitly
promoted.
"""

from .natal_engine import NatalHealthBlueprintEngine

__all__ = ["NatalHealthBlueprintEngine"]
