import asyncio

import chat.instant_chat_pipeline as pipeline


class _FakeAnalyzer:
    def __init__(self):
        self.generate_calls = 0
        self.prompts = []
        self.generate_kwargs = []

    def get_named_gemini_model(self, model_name, premium_analysis=False):
        return {"model": model_name}

    async def generate_text_from_prompt(self, prompt, **kwargs):
        self.generate_calls += 1
        self.prompts.append(prompt)
        self.generate_kwargs.append(kwargs)
        return {
            "success": True,
            "response": (
                "Your career improves gradually this year, with the strongest "
                "movement in December. What change are you considering now?"
            ),
            "chat_llm_model": kwargs.get("model_name_override"),
            "token_usage": {"input_tokens": 100, "output_tokens": 25},
        }


def test_instant_answer_uses_exactly_one_generation_call(monkeypatch):
    analyzer = _FakeAnalyzer()
    compact_context = {
        "birth_summary": {"name": "Test"},
        "intent_summary": {"category": "career", "answer_mode": "timing_window"},
        "normalized_evidence": {"natal_promise": {"status": "supported"}},
        "recent_history": [],
    }
    packet = {
        "query_plan": {
            "category": "career",
            "answer_mode": "timing_window",
            "user_goal": "understand career this year",
            "language": "english",
        },
        "verdict": {"direction": "improving", "confidence": 0.8},
        "answer_spec": {"max_words": 120, "answer_order": ["direct_answer", "follow_up"]},
        "evidence_ledger": {"records": []},
        "verification": {"passed": True},
    }

    monkeypatch.setattr(pipeline, "_build_instant_context", lambda **kwargs: compact_context)
    monkeypatch.setattr(pipeline, "build_instant_v2_packet", lambda **kwargs: packet)
    monkeypatch.setattr(pipeline, "get_instant_chat_llm_provider", lambda: "gemini")
    monkeypatch.setattr(pipeline, "get_instant_chat_model", lambda: "models/gemini-flash-lite-test")
    monkeypatch.setattr(
        pipeline,
        "finalize_instant_v2_packet",
        lambda current, answer: {**current, "verification": {"passed": True, "answer_present": bool(answer)}},
    )

    result = asyncio.run(
        pipeline.generate_instant_chat_response(
            analyzer,
            question="How is my career this year?",
            birth_data={"name": "Test"},
            intent={
                "category": "career",
                "answer_mode": "timing_window",
                "target_subject_key": "self",
            },
            history=[],
            language="english",
            response_style="technical",
        )
    )

    assert result["success"] is True
    assert analyzer.generate_calls == 1
    assert "TECHNICAL STYLE IS SELECTED" in analyzer.prompts[0]
    assert "two renderings of the same adjudicated answer" in analyzer.prompts[0]
    debug = result["instant_evidence_debug"]
    assert debug["contract_enforcement"]["generation_calls"] == 1
    assert debug["contract_enforcement"]["reason"] == "single_call_contract_in_primary_prompt"
    assert debug["composer_metrics"]["generation_calls"] == 1
    assert debug["composer_metrics"]["within_prompt_budget"] is True


def test_disabled_response_validation_streams_without_running_fact_validator(monkeypatch):
    analyzer = _FakeAnalyzer()
    packet = {
        "query_plan": {"category": "career", "answer_mode": "topic_reading"},
        "verdict": {"direction": "mixed", "confidence": 0.6},
        "answer_spec": {
            "max_words": 120,
            "visible_astrology": {"required": True, "allowed_planets": ["Moon"]},
        },
        "evidence_ledger": {"records": []},
        "verification": {"passed": True},
    }
    compact_context = {
        "birth_summary": {"name": "Test"},
        "intent_summary": {"category": "career", "answer_mode": "topic_reading"},
        "normalized_evidence": {},
        "recent_history": [],
    }
    callback = lambda _delta, _content: None

    monkeypatch.setattr(pipeline, "_build_instant_context", lambda **kwargs: compact_context)
    monkeypatch.setattr(pipeline, "build_instant_v2_packet", lambda **kwargs: packet)
    monkeypatch.setattr(pipeline, "get_instant_chat_llm_provider", lambda: "gemini")
    monkeypatch.setattr(pipeline, "get_instant_chat_model", lambda: "models/gemini-flash-lite-test")
    monkeypatch.setattr(pipeline, "is_instant_response_validation_enabled", lambda: False)
    monkeypatch.setattr(
        pipeline,
        "validate_translated_astrology_answer",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("validator ran")),
    )
    monkeypatch.setattr(pipeline, "finalize_instant_v2_packet", lambda current, answer: current)

    result = asyncio.run(
        pipeline.generate_instant_chat_response(
            analyzer,
            question="How is my career?",
            birth_data={"name": "Test"},
            intent={"category": "career", "answer_mode": "topic_reading"},
            history=[],
            language="english",
            stream_callback=callback,
        )
    )

    assert result["success"] is True
    assert analyzer.generate_calls == 1
    assert analyzer.generate_kwargs[0]["stream_callback"] is callback
    assert "FINAL OUTPUT OVERRIDE — RESPONSE VALIDATION IS DISABLED" in analyzer.prompts[0]
    assert "Never emit text enclosed in double square brackets" in analyzer.prompts[0]
    enforcement = result["instant_evidence_debug"]["contract_enforcement"]
    assert enforcement["response_validation_enabled"] is False


def test_chart_context_is_published_before_generation_and_never_added_to_answer(monkeypatch):
    from instant_chat_v2.preview import build_instant_preview
    events = []
    packet = {
        "query_plan": {"category": "career", "answer_mode": "timing_window", "target_subject": {"key": "self"},
                       "time_scope": {"as_of": "2026-10-01"}},
        "verdict": {"direction": "conditional"},
        "answer_spec": {"max_words": 120},
        "evidence_ledger": {"records": [{"kind": "current_dasha", "evidence_id": "ev-001", "value": {
            "as_of": "2026-10-01", "levels": [{"level": "mahadasha", "planet": "Saturn"}]}}]},
        "verification": {"passed": True},
    }
    intent = {"category": "career", "answer_mode": "timing_window", "target_subject_key": "self",
              "response_language": "english", "response_script": "latn"}
    preview = build_instant_preview(packet, intent)
    assert preview

    class Analyzer(_FakeAnalyzer):
        async def generate_text_from_prompt(self, prompt, **kwargs):
            events.append("generation")
            assert events == ["preview", "generation"]
            assert "ALREADY DISPLAYED CALCULATED OPENING" not in prompt
            return await super().generate_text_from_prompt(prompt, **kwargs)

    monkeypatch.setattr(pipeline, "_build_instant_context", lambda **kwargs: {
        "birth_summary": {"name": "Test"}, "intent_summary": {"category": "career"}, "normalized_evidence": {},
    })
    monkeypatch.setattr(pipeline, "build_instant_v2_packet", lambda **kwargs: packet)
    monkeypatch.setattr(pipeline, "apply_live_graph_policy", lambda current, **kwargs: current)
    monkeypatch.setattr(pipeline, "finalize_instant_v2_packet", lambda current, **kwargs: current)
    monkeypatch.setattr(pipeline, "get_instant_chat_llm_provider", lambda: "gemini")
    monkeypatch.setattr(pipeline, "get_instant_chat_model", lambda: "models/test")
    monkeypatch.setattr(pipeline, "is_instant_response_validation_enabled", lambda: False)

    def publish(value):
        assert value == preview
        events.append("preview")
        return True

    analyzer = Analyzer()
    result = asyncio.run(pipeline.generate_instant_chat_response(
        analyzer, question="How is my career?", birth_data={"name": "Test"}, intent=intent,
        history=[], preview_callback=publish,
    ))
    assert analyzer.generate_calls == 1
    assert result["instant_preview"] == preview
    assert result["response"].startswith("Your career improves")
    assert preview["content"] not in result["response"]
    assert "first_preview" in result["timing"]["instant_stage_timings_ms"]
