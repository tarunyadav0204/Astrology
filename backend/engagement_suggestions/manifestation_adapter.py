"""The only engagement adapter to the shared Manifestation Knowledge Graph."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from manifestation_kg import ActivationPacket, ManifestationResolver


def _phase(value: object) -> str:
    normalized = str(value or "developing").strip().lower()
    return normalized if normalized in {"background", "preparatory", "developing", "result_window"} else "developing"


def _subject_context(subject: Optional[str]) -> Optional[tuple[str, str]]:
    normalized = str(subject or "self").strip().lower()
    if normalized in {"", "self", "native", "querent"}:
        return None
    labels: Dict[str, tuple[str, str]] = {
        "spouse": ("my spouse", "their"),
        "partner": ("my partner", "their"),
        "father": ("my father", "his"),
        "mother": ("my mother", "her"),
        "child": ("my child", "their"),
        "first_child": ("my first child", "their"),
        "second_child": ("my second child", "their"),
        "third_child": ("my third child", "their"),
        "sibling": ("my sibling", "their"),
    }
    return labels.get(normalized, (f"my {normalized.replace('_', ' ')}", "their"))


def question_for_match(
    match: Mapping[str, Any],
    *,
    phase: Optional[str] = None,
    daily: bool = False,
    subject: Optional[str] = None,
) -> str:
    label = str(match.get("label") or "this matter").strip()
    lower = label[:1].lower() + label[1:] if label else "this matter"
    subject_context = _subject_context(subject)
    if subject_context:
        subject_phrase, possessive = subject_context
        lower = re.sub(r"\byour\b", possessive, lower, flags=re.IGNORECASE)
        if daily:
            return f"What does the chart show about {lower} for {subject_phrase}?"
        return f"Could {subject_phrase} experience {lower} in this period?"
    if daily:
        return f"What does my chart show about {lower}?"
    phase = _phase(phase)
    if phase == "preparatory":
        return f"What should I prepare for regarding {lower}?"
    if phase == "result_window":
        return f"Could {lower} produce a visible result in this period?"
    if phase == "background":
        return f"How is the background period influencing {lower}?"
    return f"How could {lower} develop in this period?"


def resolve_manifestations(
    houses: Iterable[int],
    *,
    method: str,
    phase: str = "developing",
    domain: Optional[str] = None,
    calculator_version: Optional[str] = None,
    limit: int = 12,
) -> Sequence[Dict[str, Any]]:
    normalized_houses = frozenset(int(value) for value in houses if 1 <= int(value) <= 12)
    if not normalized_houses:
        return ()
    interpretation = ManifestationResolver().interpret(
        ActivationPacket(
            active_houses=normalized_houses,
            method=method,
            domain=domain,
            phase=_phase(phase),
            calculator_version=calculator_version,
        ),
        # Event Timeline currently runs the KG in review mode. Engagement must
        # consume exactly that same catalog until review status is promoted.
        allowed_review_statuses=("approved", "provisional"),
        include_sensitive=False,
        manifestation_limit=max(1, int(limit)),
        domain_limit=8,
    )
    return tuple(match.as_dict() for match in interpretation.manifestation_matches)
