from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from .errors import PredictionConfigurationError


SUBJECT_REGISTRY_VERSION = "1.0.0"


@dataclass(frozen=True)
class SubjectDefinition:
    key: str
    label: str
    anchor_house: int
    karakas: Sequence[str]


SUBJECTS: Dict[str, SubjectDefinition] = {
    "self": SubjectDefinition("self", "self", 1, ()),
    "mother": SubjectDefinition("mother", "mother", 4, ("Moon",)),
    "father": SubjectDefinition("father", "father", 9, ("Sun",)),
    "spouse": SubjectDefinition("spouse", "spouse/partner", 7, ("Venus",)),
}


def rotate_relative_house(anchor_house: int, relative_house: int) -> int:
    if not 1 <= int(anchor_house) <= 12 or not 1 <= int(relative_house) <= 12:
        raise PredictionConfigurationError("House numbers must be between 1 and 12")
    return ((int(anchor_house) + int(relative_house) - 2) % 12) + 1


def native_houses_for_subject(subject: str, relative_houses: Iterable[int]) -> List[int]:
    definition = SUBJECTS.get(subject)
    if definition is None:
        raise PredictionConfigurationError(f"Unsupported prediction subject: {subject}")
    return [
        rotate_relative_house(definition.anchor_house, house)
        for house in relative_houses
    ]
