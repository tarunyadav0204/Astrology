import asyncio
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from ai.intent_router import IntentRouter
from ai.output_schema import build_final_prompt, resolve_output_language_policy
from ai.parallel_chat.orchestrator import _merge_instruction_blocks


def test_output_language_policy_does_not_programmatically_classify_hinglish():
    policy = resolve_output_language_policy("english", "mera career kab chalega?")

    assert policy["kind"] == "llm_current_question"
    assert policy["question_is_hindi"] is None


def test_output_language_policy_does_not_programmatically_classify_tamil():
    policy = resolve_output_language_policy("english", "என் தொழில் எப்படி இருக்கும்?")

    assert policy["kind"] == "llm_current_question"
    assert policy["question_is_hindi"] is None


def test_output_language_policy_does_not_programmatically_classify_english():
    policy = resolve_output_language_policy("spanish", "Tell me about my career")

    assert policy["kind"] == "llm_current_question"
    assert policy["app_language_lower"] == "spanish"


def test_output_language_policy_keeps_app_language_only_as_context():
    policy = resolve_output_language_policy("tamil", "mera career kab chalega?")

    assert policy["kind"] == "llm_current_question"
    assert policy["app_language_lower"] == "tamil"


def test_final_prompt_uses_current_question_language_not_previous_turn_language():
    prompt = build_final_prompt(
        user_question="मेरी शादी के बारे में बताओ",
        context={
            "analysis_type": "birth",
            "birth_details": {"name": "Tarun"},
            "ascendant_info": {"sign_name": "Cancer", "exact_degree_in_sign": 10.0},
            "intent": {"mode": "ANALYZE_TOPIC_POTENTIAL", "category": "marriage"},
        },
        history=[{"role": "user", "content": "Tell me about my marriage"}],
        language="english",
        response_style="detailed",
        user_context={"user_name": "Tarun", "user_relationship": "self"},
        premium_analysis=False,
        mode="ANALYZE_TOPIC_POTENTIAL",
    )

    assert "LLM MUST INFER FROM CURRENT QUESTION" in prompt
    assert "Hinglish / Roman Hindi" in prompt
    assert "Hindi using Devanagari" in prompt


def test_parallel_merge_blocks_follow_current_question_language():
    language_instruction, _, _, _, final_check, _ = _merge_instruction_blocks(
        user_question="என் திருமணம் எப்படி இருக்கும்?",
        context={"intent": {"mode": "ANALYZE_TOPIC_POTENTIAL", "category": "marriage"}},
        language="english",
        _response_style="detailed",
        user_context={},
        premium_analysis=False,
        mode="ANALYZE_TOPIC_POTENTIAL",
    )

    assert "LLM MUST INFER FROM CURRENT QUESTION" in language_instruction
    assert "Tamil" in language_instruction
    assert "same language and script" in final_check


def test_intent_router_prompt_uses_current_question_language_override():
    captured = {}

    class FakeModel:
        _model_name = "fake-intent-model"

        async def generate_content_async(self, prompt, request_options=None):
            captured["prompt"] = prompt
            return SimpleNamespace(
                text='{"status":"READY","chart_insights":[],"mode":"ANALYZE_PERSONALITY","context_type":"birth","category":"general","extracted_context":{},"needs_transits":false,"divisional_charts":["D1","D9"]}'
            )

    async def _run():
        router = IntentRouter()
        with patch.object(router, "_get_model", return_value=FakeModel()):
            return await router.classify_intent(
                user_question="मेरे करियर के बारे में बताओ",
                chat_history=[{"role": "user", "content": "Tell me about my career"}],
                language="english",
                d1_chart={},
            )

    result = asyncio.run(_run())

    assert result["status"] == "READY"
    assert "THE LLM MUST INFER CURRENT QUESTION LANGUAGE" in captured["prompt"]
    assert 'Hinglish / Roman Hindi question -> Hindi strings in Devanagari' in captured["prompt"]
