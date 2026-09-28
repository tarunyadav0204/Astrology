"""Versioned, source-traceable classical rule packs.

Rule packs are deliberately independent from chat and UI consumers.  A pack
may be imported and tested before any product surface is allowed to use it.
"""

from .engine import ClassicalRuleEngine
from .reading import build_classical_reading

__all__ = ["ClassicalRuleEngine", "build_classical_reading"]
