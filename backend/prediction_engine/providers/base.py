from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..context import EvaluationContext
from ..contracts import Evidence


class EvidenceProvider(ABC):
    provider_id: str
    version: str
    required_providers: tuple[str, ...] = ()
    supported_profiles: tuple[str, ...] = ()

    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> List[Evidence]:
        raise NotImplementedError
