import sys
from types import SimpleNamespace

import pytest

from ai.gemini_chat_analyzer import GeminiChatAnalyzer


class _AsyncChunkStream:
    def __init__(self, chunks):
        self._chunks = chunks

    def __aiter__(self):
        self._iterator = iter(self._chunks)
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration:
            raise StopAsyncIteration


@pytest.mark.asyncio
async def test_deepseek_stream_batches_provider_tokens(monkeypatch):
    text = "A" * 145
    chunks = [
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=char))],
            usage=None,
        )
        for char in text
    ]
    chunks.append(
        SimpleNamespace(
            choices=[],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
    )

    class _Completions:
        async def create(self, **_kwargs):
            return _AsyncChunkStream(chunks)

    class _AsyncOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=_AsyncOpenAI))
    published = []

    result = await GeminiChatAnalyzer.__new__(GeminiChatAnalyzer)._deepseek_chat_completion(
        "prompt",
        "deepseek-v4-flash",
        lambda delta, full: published.append((delta, full)),
    )

    assert result["text"] == text
    assert result["transport"] == "deepseek_stream"
    assert published[-1][1] == text
    assert 2 <= len(published) <= 5
    assert all(len(full) >= len(delta) for delta, full in published)


@pytest.mark.asyncio
async def test_deepseek_instant_can_disable_thinking(monkeypatch):
    captured = {}

    class _Completions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))],
                usage=SimpleNamespace(prompt_tokens=4, completion_tokens=2, total_tokens=6),
            )

    class _AsyncOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=_AsyncOpenAI))

    result = await GeminiChatAnalyzer.__new__(GeminiChatAnalyzer)._deepseek_chat_completion(
        "prompt",
        "deepseek-v4-flash",
        deepseek_thinking_enabled=False,
    )

    assert result["text"] == "answer"
    assert captured["extra_body"] == {"thinking": {"type": "disabled"}}


@pytest.mark.asyncio
async def test_deepseek_default_does_not_override_thinking(monkeypatch):
    captured = {}

    class _Completions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))],
                usage=SimpleNamespace(prompt_tokens=4, completion_tokens=2, total_tokens=6),
            )

    class _AsyncOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=_AsyncOpenAI))

    await GeminiChatAnalyzer.__new__(GeminiChatAnalyzer)._deepseek_chat_completion(
        "prompt",
        "deepseek-v4-flash",
    )

    assert "extra_body" not in captured
