from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


RECTIFICATION_REGISTRY_VERSION = "rectification.events.v1"


@dataclass(frozen=True)
class RectificationEventDefinition:
    key: str
    label: str
    anchor_houses: Tuple[int, ...]
    transition_houses: Tuple[int, ...]
    outcome_houses: Tuple[int, ...]
    varga: int
    varga_houses: Tuple[int, ...]
    karakas: Tuple[str, ...]
    transition_required: bool = False

    @property
    def relevant_houses(self) -> Tuple[int, ...]:
        return tuple(dict.fromkeys(
            (*self.anchor_houses, *self.transition_houses, *self.outcome_houses)
        ))


EVENT_DEFINITIONS: Dict[str, RectificationEventDefinition] = {
    "marriage": RectificationEventDefinition(
        "marriage", "Marriage or formal commitment",
        (7,), (2, 5), (11,), 9, (7,), ("Venus", "Jupiter"),
    ),
    "childbirth": RectificationEventDefinition(
        "childbirth", "Birth of a child",
        (5,), (2,), (11,), 7, (5,), ("Jupiter",),
    ),
    "career_change": RectificationEventDefinition(
        "career_change", "First job or major job change",
        (6, 10), (3, 8, 12), (2, 11), 10, (6, 10),
        ("Sun", "Saturn", "Mercury"), True,
    ),
    "promotion": RectificationEventDefinition(
        "promotion", "Promotion or major status increase",
        (10,), (6,), (2, 11), 10, (10,),
        ("Sun", "Saturn", "Mercury"),
    ),
    "education": RectificationEventDefinition(
        "education", "Admission, graduation or education milestone",
        (4, 5, 9), (), (11,), 24, (4, 5, 9), ("Mercury", "Jupiter"),
    ),
    "relocation": RectificationEventDefinition(
        "relocation", "Major relocation or foreign move",
        (4,), (3, 9, 12), (11,), 4, (4, 12),
        ("Moon", "Jupiter", "Rahu"), True,
    ),
    "property_purchase": RectificationEventDefinition(
        "property_purchase", "Property or home purchase",
        (4,), (2, 8), (11,), 4, (4,), ("Moon", "Mars", "Venus"), True,
    ),
}


def get_event_definition(key: str) -> RectificationEventDefinition:
    try:
        return EVENT_DEFINITIONS[str(key or "").strip().lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported rectification event type: {key}") from exc
