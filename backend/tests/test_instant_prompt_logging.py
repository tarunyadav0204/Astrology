import json
import logging

from chat.instant_chat_pipeline import (
    _build_instant_composer_context,
    _build_instant_prompt,
    _build_period_topic_forecast,
    _log_instant_llm_request,
    _log_instant_llm_response,
)


def test_period_forecast_is_clamped_to_requested_horizon():
    normalized = {
        "current_timing": {"period_window": {"start": "2026-08-17", "end": "2027-04-14"}},
        "window_dasha_segments": {
            "segments": [
                {
                    "start": "2026-09-19",
                    "end": "2027-02-12",
                    "mahadasha": "Saturn",
                    "antardasha": "Rahu",
                    "pratyantardasha": "Mercury",
                    "activated_focus_houses": [6],
                },
                {
                    "start": "2027-02-13",
                    "end": "2027-04-14",
                    "mahadasha": "Saturn",
                    "antardasha": "Rahu",
                    "pratyantardasha": "Ketu",
                    "activated_focus_houses": [8],
                },
            ]
        },
    }

    forecast = _build_period_topic_forecast(
        normalized,
        "health",
        {"as_of": "2026-08-17", "horizon_end": "2027-02-17"},
    )

    assert forecast["period"]["end"] == "2027-02-17"
    assert forecast["chronological_phases"][-1]["end"] == "2027-02-17"


def _payloads(caplog, prefix):
    rows = []
    for record in caplog.records:
        message = record.getMessage()
        if message.startswith(prefix):
            rows.append(json.loads(message[len(prefix):].strip()))
    return sorted(rows, key=lambda row: row.get("chunk", 0))


def test_full_instant_request_log_can_be_reassembled(monkeypatch, caplog):
    monkeypatch.setenv("INSTANT_CHAT_LOG_FULL_LLM_REQUEST", "true")
    monkeypatch.setenv("INSTANT_CHAT_LLM_LOG_CHUNK_CHARS", "2000")
    context = {"question": "When will it launch?", "evidence": "x" * 2300}
    prompt = "SYSTEM AND USER PROMPT\n" + ("p" * 2500)

    with caplog.at_level(logging.INFO, logger="chat.instant_chat_pipeline"):
        request_id = _log_instant_llm_request(
            stage="instant_answer",
            model_name="models/gemini-test",
            prompt=prompt,
            context=context,
            answer_mode="timing_window",
            speech_mode=False,
            compacted=True,
        )

    metadata = _payloads(caplog, "INSTANT_LLM_REQUEST_META ")
    context_chunks = _payloads(caplog, "INSTANT_LLM_REQUEST_CONTEXT ")
    prompt_chunks = _payloads(caplog, "INSTANT_LLM_REQUEST_PROMPT ")
    assert metadata[0]["request_id"] == request_id
    assert metadata[0]["separate_system_prompt"] is False
    assert metadata[0]["sent_chars"] == len(prompt)
    assert json.loads("".join(row["content"] for row in context_chunks)) == context
    assert "".join(row["content"] for row in prompt_chunks) == prompt


def test_instant_response_log_records_sent_and_received_characters(caplog):
    prompt = "compact request"
    response = "short answer"
    with caplog.at_level(logging.INFO, logger="chat.instant_chat_pipeline"):
        _log_instant_llm_response(
            request_id="instant_answer-test123",
            stage="instant_answer",
            model_name="models/gemini-test",
            prompt=prompt,
            result={
                "success": True,
                "response": response,
                "token_usage": {"input_tokens": 4, "output_tokens": 3},
            },
            elapsed_s=0.25,
        )

    metadata = _payloads(caplog, "INSTANT_LLM_RESPONSE_META ")
    assert metadata[0]["request_id"] == "instant_answer-test123"
    assert metadata[0]["sent_chars"] == len(prompt)
    assert metadata[0]["received_chars"] == len(response)
    assert metadata[0]["input_tokens"] == 4
    assert metadata[0]["output_tokens"] == 3
    assert metadata[0]["elapsed_ms"] == 250.0


def test_full_instant_request_log_can_be_disabled(monkeypatch, caplog):
    monkeypatch.setenv("INSTANT_CHAT_LOG_FULL_LLM_REQUEST", "false")
    with caplog.at_level(logging.INFO, logger="chat.instant_chat_pipeline"):
        request_id = _log_instant_llm_request(
            stage="instant_answer",
            model_name="models/gemini-test",
            prompt="prompt",
            context={"context": True},
            answer_mode="topic_reading",
            speech_mode=False,
            compacted=True,
        )
    assert request_id is None
    assert not any("INSTANT_LLM_REQUEST_" in record.getMessage() for record in caplog.records)


def test_v3_composer_receives_fused_brief_not_calculation_workspace():
    bulky = "diagnostic detail " * 1000
    instant_context = {
        "birth_summary": {"name": "Test", "date": "1980-01-01", "ascendant": {"sign": "Cancer"}},
        "intent_summary": {
            "category": "career",
            "answer_mode": "timing_window",
            "period_window": {"start": "2026-01-01", "end": "2026-12-31"},
        },
        "normalized_evidence": {
            "natal_promise": {"status": "supported"},
            "active_areas": ["workload", "income"],
            "current_timing": {
                "period_window": {
                    "kind": "window", "span_days": 365,
                    "start": "2026-01-01", "end": "2026-12-31",
                }
            },
            "window_rules": {"year_like": True},
            "window_dasha_segments": {
                "enabled": True,
                # Deliberately ranked rather than chronological, as emitted by the calculator.
                "segments": [
                    {
                        "start": "2026-09-19", "end": "2026-12-31",
                        "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Mercury",
                        "relevance_score": 18,
                        "natal_promise_status": "supported_by_active_dasha_carriers",
                        "activation_strength": "strong", "transit_trigger_score": 6,
                        "activated_focus_houses": [2, 10, 11],
                        "predicted_result_areas": [{"house": 10, "theme": "career role and public progress"}],
                        "peak_activation_windows": [
                            {"start": "2026-12-12", "end": "2026-12-31", "why": "dated trigger"}
                        ],
                    },
                    {
                        "start": "2026-01-01", "end": "2026-04-06",
                        "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Jupiter",
                        "relevance_score": 11,
                        "natal_promise_status": "supported_by_active_dasha_carriers",
                        "activation_strength": "moderate", "transit_trigger_score": 2,
                        "activated_focus_houses": [6, 11],
                        "predicted_result_areas": [{"house": 6, "theme": "work routines and responsibilities"}],
                    },
                    {
                        "start": "2026-04-07", "end": "2026-09-18",
                        "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Saturn",
                        "relevance_score": 14,
                        "natal_promise_status": "supported_by_active_dasha_carriers",
                        "activation_strength": "moderate", "transit_trigger_score": 3,
                        "activated_focus_houses": [2, 6, 11],
                        "predicted_result_areas": [{"house": 2, "theme": "family resources and financial stability"}],
                    },
                ],
            },
            "transit_activation_timeline": {
                "peak_windows": [{"start": "2026-12-12", "end": "2026-12-31", "why": "dated trigger"}],
            },
        },
        "natal_snapshot": {"raw": bulky},
        "current_transits": {"raw": bulky},
        "instant_parashari": {"raw": bulky},
        "recent_history": [{"role": "user", "text": "I am building a large project."}],
    }
    packet = {
        "query_plan": {"category": "career", "answer_mode": "timing_window", "language": "english"},
        "verdict": {
            "direction": "mixed_but_improving",
            "ranked_windows": [{"start": "2026-12-12", "end": "2026-12-31", "why": "dated trigger"}],
        },
        "answer_spec": {
            "max_words": 120,
            "answer_order": ["direct_answer", "natural_follow_up_question"],
            "activation_prediction_rules": {
                "natal_promise": {"status": "supported"},
                "allowed_peak_windows": [{"start": "2026-12-12", "end": "2026-12-31"}],
            },
        },
    }

    brief = _build_instant_composer_context(instant_context, packet)
    prompt = _build_instant_prompt("How is my career this year?", brief, "english")

    assert brief["context_profile"] == "instant_composer_v3"
    assert "natal_snapshot" not in brief
    assert "current_transits" not in brief
    assert "instant_parashari" not in brief
    assert bulky not in prompt
    assert brief["verdict"]["ranked_windows"][0]["start"] == "2026-12-12"
    forecast = brief["evidence"]["period_topic_forecast"]
    assert brief["query_plan"]["forecast_shape"] == "period_topic_forecast"
    assert [row["start"] for row in forecast["chronological_phases"]] == [
        "2026-01-01", "2026-04-07", "2026-09-19"
    ]
    assert "workload, deadlines" in forecast["chronological_phases"][0]["manifestation_candidates"][0]
    assert "role, status, recognition" in forecast["chronological_phases"][2]["manifestation_candidates"][0]
    assert "income, compensation" in forecast["chronological_phases"][2]["manifestation_candidates"][-1]
    assert forecast["strongest_phase"]["peak_windows"][0]["start"] == "2026-12-12"
    assert brief["answer_blueprint"]["slots"][0]["slot"] == "direct real-life verdict"
    assert brief["answer_blueprint"]["slots"][-1]["slot"] == "one natural follow-up question"
    assert "do not collapse multiple phases" in prompt
    assert "never turn a career forecast into a wealth forecast" in prompt
    assert "Fill `answer_blueprint` in order" in prompt
    assert len(prompt) < 12000


def test_future_comparison_does_not_send_current_chain_to_composer():
    instant_context = {
        "intent_summary": {"category": "career", "answer_mode": "comparison"},
        "normalized_evidence": {
            "current_timing": {
                "authoritative_current_dasha_display": "Saturn-Rahu-Saturn",
            },
        },
    }
    packet = {
        "query_plan": {
            "category": "career",
            "answer_mode": "comparison",
            "time_scope": {"as_of": "2026-08-17", "horizon_end": "2027-08-17"},
        },
        "verdict": {
            "direction": "promotion",
            "ranked_windows": [
                {
                    "start": "2027-04-15",
                    "end": "2027-08-17",
                    "dasha_chain": "Saturn-Rahu-Venus",
                }
            ],
        },
        "answer_spec": {},
    }

    brief = _build_instant_composer_context(instant_context, packet)

    assert "current_timing" not in (brief.get("evidence") or {})
    assert "Saturn-Rahu-Saturn" not in json.dumps(brief)
    assert brief["verdict"]["ranked_windows"][0]["start"] == "2027-04-15"
