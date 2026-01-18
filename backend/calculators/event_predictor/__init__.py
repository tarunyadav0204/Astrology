"""
World-Class Parashari Event Predictor
Implements 3-Layer Gate System: Dasha Authorization → Transit Trigger → Strength Validation
"""

from .gate_validator import DashaHouseGate
from .parashari_predictor import ParashariEventPredictor

# Don't alias - keep them separate
# EventPredictor = ParashariEventPredictor

__all__ = ['DashaHouseGate', 'ParashariEventPredictor']
