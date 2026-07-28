from __future__ import annotations

import pytest

from ai.output_schema import build_final_prompt, get_response_schema_for_mode
from chat.system_instruction_config import build_system_instruction
from prediction_engine.fomo_chat import (
    FOMO_CHAT_CATEGORY,
    FOMO_CHAT_MODE,
    FomoChatContextError,
    build_fomo_chat_intent,
    build_fomo_chat_payload,
    is_fomo_chat_request,
    is_supported_fomo_chat_context,
)
from utils.query_context import normalize_query_context


def _stored_evidence() -> dict:
    window = {
        "start_date": "2026-07-23",
        "end_date": "2026-08-12",
        "mahadasha": "Saturn",
        "antardasha": "Rahu",
        "pratyantardasha": "Mercury",
    }
    manifestation = {
        "manifestation_id": "manifestation-1",
        "subject": "self",
        "domain": "combined",
        "summary": "A shared obligation may require a financial adjustment.",
        "window": window,
        "house_roles": [
            {"native_house": 2, "role": "resources"},
            {"native_house": 8, "role": "shared obligations"},
        ],
        "carrier_planets": ["Saturn", "Rahu"],
        "helpful_reasons": [{"planet": "Jupiter", "reason": "Supports recovery."}],
        "pressure_reasons": [{"planet": "Saturn", "reason": "Adds delay."}],
        "constituent_themes": [
            {"key": "shared_finance", "domain": "finance"},
            {"key": "partnership_agreement", "domain": "relationship"},
        ],
    }
    return {
        "presentation_id": "presentation-1",
        "manifestation_id": "manifestation-1",
        "snapshot_id": "snapshot-1",
        "locale": "en",
        "subject": "self",
        "domain": "combined",
        "tone": "challenging",
        "title": "A financial choice may need your attention",
        "teaser": "One connected obligation may alter how you use your resources.",
        "suggested_question": "What financial development is my chart pointing to?",
        "rule_id": "finance-pressure",
        "template_version": "1",
        "birth_chart_id": 42,
        "evidence_signature": "evidence-1",
        "as_of_date": "2026-07-27",
        "horizon_days": 90,
        "profile": "parashari_fomo_v1",
        "profile_version": "1",
        "engine_version": "1",
        "schema_version": "1",
        "result_payload": {
            "chart_manifestations": [manifestation],
            "house_activations": [
                {"house": 2, "window": window, "dasha_carriers": ["Saturn"]},
                {"house": 8, "window": window, "dasha_carriers": ["Rahu"]},
                {"house": 7, "window": window, "dasha_carriers": ["Saturn"]},
                {
                    "house": 11,
                    "window": {"start_date": "2026-09-01", "end_date": "2026-09-20"},
                },
            ],
            "natal_promises": [
                {"house": 2, "outcome_tone": "mixed"},
                {"house": 8, "outcome_tone": "challenging"},
                {"house": 7, "outcome_tone": "supportive"},
                {"house": 11, "outcome_tone": "supportive"},
            ],
            "candidates": [
                {
                    "subject": "self",
                    "event_family": "shared_finance",
                    "native_houses": [2, 8],
                    "window": window,
                },
                {
                    "subject": "mother",
                    "event_family": "shared_finance",
                    "native_houses": [2, 8],
                    "window": window,
                },
            ],
        },
    }


def test_fomo_context_keeps_only_the_selected_manifestation_evidence():
    payload = build_fomo_chat_payload(
        _stored_evidence(),
        expected_birth_chart_id=42,
    )

    assert payload["presentation_shown_to_user"]["title"].startswith("A financial")
    assert payload["selected_manifestation"]["manifestation_id"] == "manifestation-1"
    assert payload["astrological_indicators"]["relevant_native_houses"] == [2, 8]
    assert [
        row["house"] for row in payload["astrological_indicators"]["house_activations"]
    ] == [2, 8]
    assert [
        row["house"] for row in payload["astrological_indicators"]["natal_promises"]
    ] == [2, 8]
    assert len(payload["astrological_indicators"]["prediction_candidates"]) == 1
    assert payload["temporal_grounding"]["selected_window_status"] == "active_now"
    assert payload["temporal_grounding"]["delivery_chain_during_selected_window"] == {
        "mahadasha": "Saturn",
        "antardasha": "Rahu",
        "pratyantardasha": "Mercury",
    }
    synthesis = payload["event_synthesis_brief"]
    assert synthesis["theme_domains"] == ["finance", "relationship"]
    assert synthesis["all_impacted_native_houses_in_window"] == [2, 7, 8]
    assert [
        row["house"] for row in synthesis["all_window_house_activations"]
    ] == [2, 8, 7]
    assert synthesis["synthesis_policy"][
        "selected_summary_and_possibilities_are_seeds_not_an_exhaustive_list"
    ]


def test_fomo_context_rejects_a_different_selected_chart():
    with pytest.raises(FomoChatContextError) as exc:
        build_fomo_chat_payload(_stored_evidence(), expected_birth_chart_id=99)

    assert exc.value.status_code == 409


def test_fomo_request_and_intent_are_explicit_and_never_clarify():
    query_context = {
        "source": "homepage_fomo",
        "fomo_snapshot_id": "snapshot-1",
        "fomo_presentation_id": "presentation-1",
    }
    assert is_fomo_chat_request(query_context)

    intent = build_fomo_chat_intent(
        build_fomo_chat_payload(_stored_evidence(), expected_birth_chart_id=42)
    )
    assert intent["status"] == "READY"
    assert intent["mode"] == FOMO_CHAT_MODE
    assert intent["category"] == FOMO_CHAT_CATEGORY
    assert intent["answer_mode"] == "fomo_detail"


def test_fomo_worker_accepts_current_and_already_queued_context_versions():
    assert is_supported_fomo_chat_context({"context_version": "fomo_chat_context.v1"})
    assert is_supported_fomo_chat_context({"context_version": "fomo_chat_context.v2"})
    assert not is_supported_fomo_chat_context({"context_version": "fomo_chat_context.v3"})
    assert not is_supported_fomo_chat_context(None)


def test_normalized_query_context_preserves_fomo_breadcrumbs():
    normalized = normalize_query_context({
        "source": "homepage_fomo",
        "chat_mode": "fomo_manifestation",
        "category": "fomo_manifestation",
        "answer_mode": "fomo_detail",
        "fomo_snapshot_id": "snapshot-1",
        "fomo_presentation_id": "presentation-1",
        "fomo_manifestation_id": "manifestation-1",
        "fomo_evidence_signature": "evidence-1",
    })

    assert normalized["source"] == "homepage_fomo"
    assert normalized["fomo_manifestation_id"] == "manifestation-1"


def test_fomo_prompt_locks_the_answer_to_server_evidence():
    fomo_context = build_fomo_chat_payload(
        _stored_evidence(),
        expected_birth_chart_id=42,
    )
    intent = build_fomo_chat_intent(fomo_context)
    prompt = build_final_prompt(
        "What financial development is my chart pointing to?",
        {
            "analysis_type": "fomo_manifestation",
            "intent": intent,
            "fomo_manifestation_context": fomo_context,
        },
        [],
        "english",
        "detailed",
        {},
        False,
        FOMO_CHAT_MODE,
    )

    assert "AUTHORITATIVE SELECTED FOMO MANIFESTATION CONTRACT" in prompt
    assert "do not substitute another event" in prompt
    assert "do not ask a clarification question" in prompt.lower()
    assert "does not prove" in prompt
    assert "The normal ChatContextBuilder data and guardrails remain available" in prompt
    assert "natural equivalent in the requested response" in prompt
    assert "regardless of the response language" in prompt
    assert "Do not cite Ashtakavarga scores" in prompt
    assert "PD MUST NOT be omitted" in prompt
    assert "SELECTED FOMO MANIFESTATION RESPONSE" in prompt
    assert "pairs, triples, and the full active-house cluster" in prompt
    assert "full same-window active-house cluster" in prompt
    assert "are seeds and boundaries" in prompt
    assert "list. Do not simply restate them." in prompt
    assert "every materially distinct supported event family" in prompt
    assert "normally as 6–12" in prompt
    assert "Ashtakavarga (SAV & BAV)" not in prompt


def test_fomo_has_its_own_schema_without_changing_normal_chat_schema():
    fomo_schema = get_response_schema_for_mode(FOMO_CHAT_MODE)
    normal_schema = get_response_schema_for_mode("DEFAULT")

    assert "SELECTED FOMO MANIFESTATION RESPONSE" in fomo_schema
    assert "complete supplied MD–AD–PD" in fomo_schema
    assert "### Possible Developments" in fomo_schema
    assert "every materially distinct supported event family" in fomo_schema
    assert "normally as 6–12" in fomo_schema
    assert "Nakshatra Insights" in fomo_schema
    assert "Do not add extra sections" in fomo_schema
    assert "Ashtakavarga (SAV & BAV)" not in fomo_schema
    assert "Ashtakavarga (SAV & BAV)" in normal_schema


def test_fomo_system_instruction_is_isolated_from_normal_multischool_mandates():
    fomo_instruction = build_system_instruction(mode=FOMO_CHAT_MODE)
    normal_instruction = build_system_instruction(mode="DEFAULT")

    assert "DASHA-DATES" in fomo_instruction
    assert "[AV-0]" not in fomo_instruction
    assert "[JAIMINI-1]" not in fomo_instruction
    assert "[AV-0]" in normal_instruction
    assert "[JAIMINI-1]" in normal_instruction
