"""Event Timeline adapter for explicitly timeline-enabled KG patterns."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

from prediction_engine.event_windows import ClassificationRule, EventDefinition, SignalGroup

from .store import ManifestationKnowledgeStore, ManifestationPattern, default_manifestation_store


@dataclass(frozen=True)
class TimelineDefinitionBundle:
    definitions: tuple[EventDefinition, ...]
    audit: Mapping[str, Any]


def timeline_integration_enabled() -> bool:
    return str(os.getenv("MANIFESTATION_KG_EVENT_TIMELINE") or "review").strip().lower() not in {
        "0", "false", "off", "disabled",
    }


def _context_matches(expression: str | None, context: Mapping[str, Any]) -> bool:
    if not expression:
        return True
    key, raw_values = expression.split("=", 1)
    allowed = {value for value in raw_values.split("|") if value}
    if key == "relative_subject":
        present = {
            str(row.get("key") or "")
            for row in context.get("eligible_relative_subjects") or []
        }
        return bool(present & allowed)
    if key == "child_order":
        return bool(set(context.get("explicit_child_orders") or []) & allowed)
    if key == "topic":
        return bool(set(context.get("explicit_topics") or []) & allowed)
    return str(context.get(key) or "") in allowed


def _definition(
    pattern: ManifestationPattern,
    manifestation: Mapping[str, Any],
    ontology_version: str,
) -> EventDefinition:
    timeline = pattern.timeline
    anchor = tuple(int(value) for value in timeline["anchor"])
    transition = tuple(int(value) for value in timeline["transition"])
    outcome = tuple(int(value) for value in timeline.get("outcome") or ())
    label = str(manifestation["label"])
    key = "kg_" + pattern.manifestation_id.replace(".", "_")
    return EventDefinition(
        key=key,
        label=label,
        description=(
            f"Manifestation KG candidate {pattern.manifestation_id}. It remains a candidate until "
            "the Event Timeline natal, delivery, transit, divisional, KP and obstruction gates pass."
        ),
        varga=str(timeline["varga"]),
        varga_houses=tuple(int(value) for value in timeline["varga_houses"]),
        varga_description=f"{timeline['varga']} is the configured topic confirmation for {label.lower()}.",
        anchor=SignalGroup(
            key="kg_anchor", label="subject anchor", houses=anchor, weight=25,
            required=True, require_all=len(anchor) > 1,
            description="Every configured KG anchor must receive Event Timeline permission.",
        ),
        transition=SignalGroup(
            key="kg_transition", label="manifestation pathway", houses=transition, weight=20,
            required=True,
            require_all=bool(timeline.get("transition_require_all")),
            minimum_hits=(len(transition) if timeline.get("transition_require_all") else 1),
            description="The KG pathway must be active in the same evaluated period.",
        ),
        outcome=SignalGroup(
            key="kg_outcome", label="visible-result support", houses=outcome, weight=10,
            required=bool(timeline.get("outcome_required")),
            require_all=bool(timeline.get("outcome_require_all")),
            minimum_hits=(len(outcome) if timeline.get("outcome_require_all") else 1),
            description="Outcome activation distinguishes development from a visible result.",
        ),
        classifications=(ClassificationRule(key, label),),
        version=f"manifestation-kg.{pattern.stable_id}.v1",
        independent_confirmation_required=True,
        source_event_key=str(timeline["profile"]),
        knowledge_pattern_id=pattern.stable_id,
        knowledge_manifestation_id=pattern.manifestation_id,
        knowledge_review_status=pattern.review_status,
        knowledge_claim_basis=pattern.claim_basis,
        knowledge_source_ids=pattern.source_ids,
        knowledge_ontology_version=ontology_version,
        knowledge_domain=str(manifestation["parent_domain"]),
    )


def build_timeline_definitions(
    context: Mapping[str, Any],
    *,
    store: ManifestationKnowledgeStore | None = None,
) -> TimelineDefinitionBundle:
    knowledge = store or default_manifestation_store()
    if not timeline_integration_enabled():
        return TimelineDefinitionBundle((), {
            "enabled": False,
            "ontology_version": knowledge.ontology_version,
            "eligible_pattern_count": 0,
            "skipped": [],
        })

    definitions: list[EventDefinition] = []
    skipped: list[dict[str, Any]] = []
    timeline_patterns = [pattern for pattern in knowledge.patterns if pattern.timeline.get("enabled")]
    for pattern in timeline_patterns:
        required_context = str(pattern.timeline.get("required_context") or "") or None
        if not _context_matches(required_context, context):
            skipped.append({
                "pattern_id": pattern.stable_id,
                "manifestation_id": pattern.manifestation_id,
                "reason": "required_context_not_present",
                "required_context": required_context,
            })
            continue
        definitions.append(_definition(
            pattern,
            knowledge.manifestation(pattern.manifestation_id),
            knowledge.ontology_version,
        ))

    return TimelineDefinitionBundle(tuple(definitions), {
        "enabled": True,
        "mode": "review_provisional_patterns_allowed",
        "ontology_version": knowledge.ontology_version,
        "timeline_pattern_count": len(timeline_patterns),
        "eligible_pattern_count": len(definitions),
        "skipped_pattern_count": len(skipped),
        "eligible_pattern_ids": [
            str(definition.knowledge_pattern_id) for definition in definitions
        ],
        "skipped": skipped,
        "claim_boundary": (
            "KG eligibility only proposes event definitions. Event Timeline evidence gates decide whether a "
            "candidate qualifies and whether it is published or retained as background."
        ),
    })
