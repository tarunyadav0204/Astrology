from types import SimpleNamespace
import sys

import pytest

from ai.gemini_chat_analyzer import GeminiChatAnalyzer, resolve_openai_reasoning_effort
from ai import intent_router
from utils import admin_settings


def test_openai_is_valid_instant_provider_and_resolves_dedicated_model(monkeypatch):
    values = {
        "instant_chat_llm_provider": "openai",
        "openai_instant_chat_model": "gpt-5.6-luna",
    }
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: values.get(key))

    assert admin_settings.get_instant_chat_llm_provider() == "openai"
    assert admin_settings.get_instant_chat_model() == "gpt-5.6-luna"


@pytest.mark.parametrize(
    ("model", "requested", "expected"),
    [
        ("gpt-5.6-luna", "none", "none"),
        ("gpt-5.4-pro", "none", "medium"),
        ("gpt-5", "none", "minimal"),
        ("gpt-4o-mini", "none", None),
        ("gpt-4o", "none", None),
        ("gpt-4-turbo", "none", None),
        ("o4-mini", "none", None),
    ],
)
def test_openai_reasoning_effort_is_model_capability_aware(model, requested, expected):
    assert resolve_openai_reasoning_effort(model, requested) == expected


def test_openai_reasoning_models_use_responses_transport():
    analyzer = GeminiChatAnalyzer.__new__(GeminiChatAnalyzer)
    assert analyzer._openai_model_uses_responses_api("gpt-5.6-luna") is True
    assert analyzer._openai_model_uses_responses_api("gpt-5.4-pro") is True
    assert analyzer._openai_model_uses_responses_api("o4-mini") is True
    assert analyzer._openai_model_uses_responses_api("gpt-4o-mini") is False


@pytest.mark.asyncio
async def test_openai_luna_live_completion_uses_override_system_prompt_and_usage(monkeypatch):
    captured = {}

    class FakeResponses:
        def stream(self, **kwargs):
            captured.update(kwargs)
            final_response = SimpleNamespace(
                error=None,
                output_text="A chart-grounded answer",
                usage=SimpleNamespace(
                    input_tokens=120,
                    output_tokens=30,
                    total_tokens=150,
                    input_tokens_details=SimpleNamespace(cached_tokens=80),
                ),
            )

            class FakeStream:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc, tb):
                    return False

                def __aiter__(self):
                    self._events = iter([
                        SimpleNamespace(type="response.output_text.delta", delta="A chart-grounded answer")
                    ])
                    return self

                async def __anext__(self):
                    try:
                        return next(self._events)
                    except StopIteration:
                        raise StopAsyncIteration

                async def get_final_response(self):
                    return final_response

            return FakeStream()

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeAsyncOpenAI))
    streamed = []

    result = await GeminiChatAnalyzer.__new__(GeminiChatAnalyzer).generate_text_from_prompt(
        "user payload",
        provider_override="openai",
        model_name_override="gpt-5.6-luna",
        system_prompt="stable instructions",
        stream_callback=lambda delta, full: streamed.append((delta, full)),
        openai_reasoning_effort="none",
    )

    assert result["success"] is True
    assert result["chat_llm_provider"] == "openai"
    assert result["chat_llm_model"] == "gpt-5.6-luna"
    assert captured["model"] == "gpt-5.6-luna"
    assert captured["input"] == "user payload"
    assert captured["instructions"] == "stable instructions"
    assert captured["reasoning"] == {"effort": "none"}
    assert result["token_usage"]["cached_tokens"] == 80
    assert result["token_usage"]["non_cached_input_tokens"] == 40
    assert streamed == [("A chart-grounded answer", "A chart-grounded answer")]


@pytest.mark.asyncio
async def test_openai_luna_is_used_by_live_intent_router(monkeypatch):
    captured = {}

    class FakeResponses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                output_text='{"status":"READY","category":"career"}',
                usage=SimpleNamespace(
                    input_tokens=40,
                    output_tokens=10,
                    total_tokens=50,
                    input_tokens_details=SimpleNamespace(cached_tokens=20),
                ),
            )

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(intent_router, "get_instant_chat_llm_provider", lambda: "openai")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeAsyncOpenAI))

    response = await intent_router.IntentRouter.__new__(intent_router.IntentRouter)._generate_instant_content(
        "classify this", "gpt-5.6-luna", 5.0
    )

    assert captured["model"] == "gpt-5.6-luna"
    assert captured["reasoning"] == {"effort": "none"}
    assert response.text.startswith('{"status"')
    assert response.usage_metadata.cached_content_token_count == 20


@pytest.mark.asyncio
async def test_gpt4_live_intent_router_omits_unsupported_reasoning_parameter(monkeypatch):
    captured = {}

    class FakeResponses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                output_text='{"status":"READY","category":"career"}',
                usage=SimpleNamespace(input_tokens=8, output_tokens=4, total_tokens=12),
            )

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(intent_router, "get_instant_chat_llm_provider", lambda: "openai")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeAsyncOpenAI))

    await intent_router.IntentRouter.__new__(intent_router.IntentRouter)._generate_instant_content(
        "classify this", "gpt-4o-mini", 5.0
    )

    assert captured["model"] == "gpt-4o-mini"
    assert "reasoning" not in captured
