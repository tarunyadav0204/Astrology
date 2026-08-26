import asyncio

import chat.instant_chat_pipeline as pipeline


class _FakeAnalyzer:
    def __init__(self):
        self.generate_calls = 0

    def get_named_gemini_model(self, model_name, premium_analysis=False):
        return {"model": model_name}

    async def generate_text_from_prompt(self, prompt, **kwargs):
        self.generate_calls += 1
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
        )
    )

    assert result["success"] is True
    assert analyzer.generate_calls == 1
    debug = result["instant_evidence_debug"]
    assert debug["contract_enforcement"]["generation_calls"] == 1
    assert debug["contract_enforcement"]["reason"] == "single_call_contract_in_primary_prompt"
    assert debug["composer_metrics"]["generation_calls"] == 1
    assert debug["composer_metrics"]["within_prompt_budget"] is True
