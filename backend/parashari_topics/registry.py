"""Declarative registry for Parashari Desk topic lenses.

The registry routes canonical calculations into a topic workspace.  It does
not contain executable astrological rules and must not be used as evidence by
itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Tuple


REGISTRY_VERSION = "parashari.topic-registry/1.0.0"


@dataclass(frozen=True)
class TopicTimingQuestion:
    key: str
    label: str
    description: str
    provider: str
    event_key: str = ""


@dataclass(frozen=True)
class TopicDefinition:
    key: str
    label: str
    short_label: str
    description: str
    provider: str
    status: str
    primary_houses: Tuple[int, ...]
    supporting_houses: Tuple[int, ...]
    primary_charts: Tuple[str, ...]
    supporting_charts: Tuple[str, ...]
    karakas: Tuple[str, ...]
    sections: Tuple[str, ...]
    timing_questions: Tuple[TopicTimingQuestion, ...]
    translation_key: str
    version: str

    def public_dict(self) -> dict:
        value = asdict(self)
        value["registry_version"] = REGISTRY_VERSION
        return value


HEALTH = TopicDefinition(
    key="health",
    label="Health",
    short_label="Health",
    description=(
        "Study constitution, protection, natal susceptibilities and the periods "
        "that activate an already-established health pattern."
    ),
    provider="health_v2",
    status="active",
    primary_houses=(1, 6, 8, 12),
    supporting_houses=(5, 11),
    primary_charts=("D1", "D30"),
    supporting_charts=("D3", "D9", "D12"),
    karakas=("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"),
    sections=("overview", "promise", "timing", "why"),
    timing_questions=(
        TopicTimingQuestion(
            key="health_sensitive_periods",
            label="Sensitive health periods",
            description=(
                "Find MD–AD–PD periods in which an established natal susceptibility "
                "is repeated by relevant transits."
            ),
            provider="health_v2_timing",
        ),
        TopicTimingQuestion(
            key="health_attention_windows",
            label="Health-attention windows",
            description=(
                "Search broader health, treatment, rest or recovery windows through "
                "the reusable event-window engine."
            ),
            provider="event_windows",
            event_key="health",
        ),
    ),
    translation_key="parashariTopics.health",
    version="health-topic/1.0.0",
)


TOPIC_REGISTRY: Mapping[str, TopicDefinition] = {
    HEALTH.key: HEALTH,
}


def get_topic(topic_key: str) -> TopicDefinition:
    try:
        return TOPIC_REGISTRY[str(topic_key).strip().lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported Parashari topic: {topic_key}") from exc


def public_topics() -> dict:
    return {
        "schema_version": "parashari.topic-catalog.v1",
        "registry_version": REGISTRY_VERSION,
        "topics": [topic.public_dict() for topic in TOPIC_REGISTRY.values()],
    }
