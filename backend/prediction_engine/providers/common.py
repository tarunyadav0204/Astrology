from __future__ import annotations

from typing import Dict

from ..context import EvaluationContext
from ..contracts import Evidence, EvidenceStatus, Importance, Polarity


SUPPORTIVE_DIGNITIES = {"exalted", "moolatrikona", "own_sign", "favorable"}
CHALLENGING_DIGNITIES = {"debilitated", "unfavorable"}


def dignity_polarity(dignity: str) -> Polarity:
    if dignity in SUPPORTIVE_DIGNITIES:
        return Polarity.SUPPORTIVE
    if dignity in CHALLENGING_DIGNITIES:
        return Polarity.CHALLENGING
    return Polarity.NEUTRAL


def relation_polarity(relation: str) -> Polarity:
    if relation in {"friend", "great_friend", "self"}:
        return Polarity.SUPPORTIVE
    if relation in {"enemy", "great_enemy"}:
        return Polarity.CHALLENGING
    return Polarity.NEUTRAL


def evidence_row(
    provider,
    context: EvaluationContext,
    *,
    rule_id: str,
    planet: str,
    house: int | None,
    polarity: Polarity,
    facts: Dict,
    independent_key: str,
    importance: Importance = Importance.CONFIRMATORY,
) -> Evidence:
    return Evidence(
        provider=provider.provider_id,
        provider_version=provider.version,
        rule_id=rule_id,
        status=EvidenceStatus.EVALUATED,
        subject=context.subject,
        domain=context.event_family.domain,
        window_start=context.window.start_date,
        window_end=context.window.end_date,
        planet=planet,
        house=house,
        importance=importance,
        polarity=polarity,
        facts=facts,
        independent_key=independent_key,
    )
