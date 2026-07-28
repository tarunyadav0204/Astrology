from __future__ import annotations

from datetime import date
from typing import Any, Dict, Mapping, Optional, Sequence

from .fomo_repository import FomoSnapshotRepository


FOMO_CHAT_SOURCE = "homepage_fomo"
FOMO_CHAT_MODE = "FOMO_MANIFESTATION_DETAIL"
FOMO_CHAT_CATEGORY = "fomo_manifestation"
FOMO_CHAT_CONTEXT_VERSION = "fomo_chat_context.v2"
FOMO_CHAT_SUPPORTED_CONTEXT_VERSIONS = frozenset({
    "fomo_chat_context.v1",
    FOMO_CHAT_CONTEXT_VERSION,
})


class FomoChatContextError(ValueError):
    def __init__(self, detail: str, *, status_code: int = 422):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def is_fomo_chat_request(query_context: Optional[Mapping[str, Any]]) -> bool:
    if not isinstance(query_context, Mapping):
        return False
    source = str(query_context.get("source") or "").strip().lower()
    mode = str(
        query_context.get("chat_mode")
        or query_context.get("mode")
        or query_context.get("answer_mode")
        or ""
    ).strip().lower()
    has_ids = bool(
        str(query_context.get("fomo_snapshot_id") or "").strip()
        and str(query_context.get("fomo_presentation_id") or "").strip()
    )
    return has_ids and (
        source == FOMO_CHAT_SOURCE
        or mode in {
            FOMO_CHAT_CATEGORY,
            FOMO_CHAT_MODE.lower(),
            "fomo_detail",
        }
    )


def is_supported_fomo_chat_context(context: Any) -> bool:
    return (
        isinstance(context, Mapping)
        and str(context.get("context_version") or "")
        in FOMO_CHAT_SUPPORTED_CONTEXT_VERSIONS
    )


def _window_matches(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    return (
        str(first.get("start_date") or "") == str(second.get("start_date") or "")
        and str(first.get("end_date") or "") == str(second.get("end_date") or "")
    )


def _parse_date(value: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(value or "")[:10])
    except (TypeError, ValueError):
        return None


def _window_status(
    window: Mapping[str, Any],
    *,
    as_of_date: Any,
) -> str:
    as_of = _parse_date(as_of_date)
    start = _parse_date(window.get("start_date"))
    end = _parse_date(window.get("end_date"))
    if not as_of or not start or not end:
        return "unknown"
    if as_of < start:
        return "upcoming"
    if as_of <= end:
        return "active_now"
    return "concluded"


def build_fomo_chat_payload(
    stored: Mapping[str, Any],
    *,
    expected_birth_chart_id: Optional[int] = None,
) -> Dict[str, Any]:
    stored_chart_id = int(stored.get("birth_chart_id") or 0)
    if expected_birth_chart_id and stored_chart_id != int(expected_birth_chart_id):
        raise FomoChatContextError(
            "This chart theme belongs to a different selected chart. Reopen it from Home.",
            status_code=409,
        )

    result = stored.get("result_payload")
    if not isinstance(result, Mapping):
        raise FomoChatContextError("The chart theme evidence is unavailable.")

    manifestation_id = str(stored.get("manifestation_id") or "")
    manifestations = result.get("chart_manifestations")
    manifestations = manifestations if isinstance(manifestations, Sequence) else ()
    manifestation = next(
        (
            row
            for row in manifestations
            if isinstance(row, Mapping)
            and str(row.get("manifestation_id") or "") == manifestation_id
        ),
        None,
    )
    if not isinstance(manifestation, Mapping):
        raise FomoChatContextError("The selected chart manifestation is unavailable.")

    house_roles = manifestation.get("house_roles")
    house_roles = house_roles if isinstance(house_roles, Sequence) else ()
    relevant_houses = sorted({
        int(row.get("native_house"))
        for row in house_roles
        if isinstance(row, Mapping) and row.get("native_house") is not None
    })
    manifestation_window = (
        manifestation.get("window")
        if isinstance(manifestation.get("window"), Mapping)
        else {}
    )

    activations = result.get("house_activations")
    activations = activations if isinstance(activations, Sequence) else ()
    related_activations = [
        dict(row)
        for row in activations
        if isinstance(row, Mapping)
        and int(row.get("house") or 0) in relevant_houses
        and isinstance(row.get("window"), Mapping)
        and _window_matches(row.get("window") or {}, manifestation_window)
    ]
    window_activations = [
        dict(row)
        for row in activations
        if isinstance(row, Mapping)
        and isinstance(row.get("window"), Mapping)
        and _window_matches(row.get("window") or {}, manifestation_window)
    ]
    window_houses = sorted({
        int(row.get("house"))
        for row in window_activations
        if row.get("house") is not None
    })

    natal_promises = result.get("natal_promises")
    natal_promises = natal_promises if isinstance(natal_promises, Sequence) else ()
    related_promises = [
        dict(row)
        for row in natal_promises
        if isinstance(row, Mapping)
        and int(row.get("house") or 0) in relevant_houses
    ]

    constituent_themes = manifestation.get("constituent_themes")
    constituent_themes = (
        constituent_themes if isinstance(constituent_themes, Sequence) else ()
    )
    event_families = {
        str(row.get("key") or "")
        for row in constituent_themes
        if isinstance(row, Mapping) and str(row.get("key") or "")
    }
    theme_domains = sorted({
        str(row.get("domain") or "").strip()
        for row in constituent_themes
        if isinstance(row, Mapping) and str(row.get("domain") or "").strip()
    })
    manifestation_domain = str(manifestation.get("domain") or "").strip()
    if manifestation_domain and manifestation_domain != "combined":
        theme_domains = sorted(set(theme_domains) | {manifestation_domain})
    candidates = result.get("candidates")
    candidates = candidates if isinstance(candidates, Sequence) else ()
    related_candidates = [
        dict(row)
        for row in candidates
        if isinstance(row, Mapping)
        and str(row.get("subject") or "") == str(manifestation.get("subject") or "")
        and (
            str(row.get("event_family") or "") in event_families
            or (
                isinstance(row.get("window"), Mapping)
                and _window_matches(row.get("window") or {}, manifestation_window)
                and bool(
                    set(int(house) for house in (row.get("native_houses") or ()))
                    .intersection(relevant_houses)
                )
            )
        )
    ]
    window_candidates = [
        dict(row)
        for row in candidates
        if isinstance(row, Mapping)
        and str(row.get("subject") or "") == str(manifestation.get("subject") or "")
        and isinstance(row.get("window"), Mapping)
        and _window_matches(row.get("window") or {}, manifestation_window)
        and bool(
            set(int(house) for house in (row.get("native_houses") or ()))
            .intersection(window_houses)
        )
    ]
    window_promises = [
        dict(row)
        for row in natal_promises
        if isinstance(row, Mapping)
        and int(row.get("house") or 0) in window_houses
    ]

    presentation = {
        key: stored.get(key)
        for key in (
            "presentation_id",
            "manifestation_id",
            "locale",
            "subject",
            "domain",
            "area_label",
            "tone",
            "title",
            "teaser",
            "suggested_question",
            "rule_id",
            "template_version",
        )
    }
    as_of_date = stored.get("as_of_date")
    delivery_chain = {
        "mahadasha": manifestation_window.get("mahadasha"),
        "antardasha": manifestation_window.get("antardasha"),
        "pratyantardasha": manifestation_window.get("pratyantardasha"),
    }
    return {
        "context_version": FOMO_CHAT_CONTEXT_VERSION,
        "source": FOMO_CHAT_SOURCE,
        "snapshot": {
            "snapshot_id": stored.get("snapshot_id"),
            "birth_chart_id": stored_chart_id,
            "evidence_signature": stored.get("evidence_signature"),
            "as_of_date": stored.get("as_of_date"),
            "horizon_days": stored.get("horizon_days"),
            "profile": stored.get("profile"),
            "profile_version": stored.get("profile_version"),
            "engine_version": stored.get("engine_version"),
            "schema_version": stored.get("schema_version"),
        },
        "presentation_shown_to_user": presentation,
        "selected_manifestation": dict(manifestation),
        "temporal_grounding": {
            "as_of_date": as_of_date,
            "selected_manifestation_window": dict(manifestation_window),
            "selected_window_status": _window_status(
                manifestation_window,
                as_of_date=as_of_date,
            ),
            "delivery_chain_during_selected_window": delivery_chain,
            "interpretation_rules": [
                (
                    "The selected manifestation window is an event-delivery window "
                    "inside the named dasha chain; it is not automatically the start "
                    "of the Mahadasha, Antardasha, or Pratyantardasha."
                ),
                (
                    "A dasha layer whose start date is before the as-of date is already "
                    "running and must never be described as something the user is now "
                    "entering or transitioning into."
                ),
                (
                    "Do not state a dasha start date, duration, or future multi-year "
                    "period unless that exact boundary is present in the supplied evidence."
                ),
            ],
        },
        "astrological_indicators": {
            "relevant_native_houses": relevant_houses,
            "house_activations": related_activations,
            "natal_promises": related_promises,
            "prediction_candidates": related_candidates,
        },
        "event_synthesis_brief": {
            "subject": str(manifestation.get("subject") or "self"),
            "theme_domains": theme_domains,
            "selected_house_roles": [dict(row) for row in house_roles if isinstance(row, Mapping)],
            "all_impacted_native_houses_in_window": window_houses,
            "all_window_house_activations": window_activations,
            "all_window_natal_promises": window_promises,
            "theme_source_candidates": window_candidates,
            "synthesis_policy": {
                "deterministic_evidence_sets_boundaries_not_final_event_copy": True,
                "selected_summary_and_possibilities_are_seeds_not_an_exhaustive_list": True,
                "llm_must_synthesize_human_event_scenarios": True,
                "combine_coherent_pairs_triples_and_full_house_cluster": True,
                "do_not_mechanically_enumerate_every_house_permutation": True,
                "rank_full_cluster_and_shared_carrier_scenarios_first": True,
                "stay_within_selected_subject_and_theme_domains": True,
                "each_scenario_requires_multi_house_or_delivery_chain_support": True,
            },
        },
        "answer_contract": {
            "mode": FOMO_CHAT_MODE,
            "category": FOMO_CHAT_CATEGORY,
            "clarification_allowed": False,
            "focus_only_on_selected_manifestation": True,
            "use_server_evidence_as_authoritative": True,
            "explain_teaser_without_guaranteeing_one_event": True,
            "must_cover": [
                "what the teaser referred to",
                "ranked concrete event scenarios synthesized from the impacted houses",
                "coherent pairs, triples, and the full active-house cluster",
                "the selected current or upcoming manifestation window",
                "activated houses and their roles",
                "the complete MD-AD-PD delivery chain and each level's role",
                "transit and natal reinforcement",
                "helpful, mixed, and pressure factors",
                "how the user can prepare or decide",
            ],
        },
    }


def resolve_fomo_chat_context(
    *,
    userid: int,
    birth_chart_id: Optional[int],
    query_context: Mapping[str, Any],
    repository: Optional[FomoSnapshotRepository] = None,
) -> Dict[str, Any]:
    if not is_fomo_chat_request(query_context):
        raise FomoChatContextError("Invalid FOMO chat context.")
    snapshot_id = str(query_context.get("fomo_snapshot_id") or "").strip()
    presentation_id = str(
        query_context.get("fomo_presentation_id") or ""
    ).strip()
    stored = (repository or FomoSnapshotRepository()).load_owned_chat_evidence(
        userid=userid,
        snapshot_id=snapshot_id,
        presentation_id=presentation_id,
    )
    if not stored:
        raise FomoChatContextError(
            "This chart theme is unavailable or expired. Reopen it from Home.",
            status_code=404,
        )
    return build_fomo_chat_payload(
        stored,
        expected_birth_chart_id=birth_chart_id,
    )


def build_fomo_chat_intent(context: Mapping[str, Any]) -> Dict[str, Any]:
    presentation = context.get("presentation_shown_to_user")
    presentation = presentation if isinstance(presentation, Mapping) else {}
    manifestation = context.get("selected_manifestation")
    manifestation = manifestation if isinstance(manifestation, Mapping) else {}
    domain = str(presentation.get("domain") or manifestation.get("domain") or "general")
    return {
        "status": "READY",
        "mode": FOMO_CHAT_MODE,
        "category": FOMO_CHAT_CATEGORY,
        "answer_mode": "fomo_detail",
        "context_type": "birth",
        "target_subject_key": str(
            presentation.get("subject") or manifestation.get("subject") or "self"
        ),
        "needs_transits": False,
        "divisional_charts": [],
        "extracted_context": {
            "fomo_domain": domain,
            "fomo_manifestation_id": presentation.get("manifestation_id"),
        },
        "chart_insights": [],
    }
