"""Isolated runtime for the compiled manifestation knowledge graph.

No existing product imports this package. Integrations must be explicit and
product-specific.
"""

from .models import ActivationPacket, CombinationInterpretation, ManifestationMatch
from .resolver import ManifestationResolver
from .store import ManifestationKnowledgeStore

__all__ = [
    "ActivationPacket",
    "CombinationInterpretation",
    "ManifestationKnowledgeStore",
    "ManifestationMatch",
    "ManifestationResolver",
]
