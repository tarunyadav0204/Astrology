"""The existing generation call must retain cache context when enabling reasoning."""
import asyncio
from types import SimpleNamespace


def test_reasoning_transport_preserves_cached_context_and_timeout(monkeypatch):
    import ai.gemini_chat_analyzer as module
    captured = []
    def rest(model, prompt, api_key, thinking_level, system_prompt, **kwargs):
        captured.append((model, thinking_level, kwargs))
        return {'text': 'verified answer', 'usage': {'input_tokens': 100, 'output_tokens': 10,
                'cached_tokens': 80, 'total_tokens': 130}}
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    monkeypatch.setattr(module, 'generate_content_rest_v1beta_result', rest)
    analyzer = module.GeminiChatAnalyzer.__new__(module.GeminiChatAnalyzer)
    result = asyncio.run(analyzer.generate_text_from_prompt(
        'facts', provider_override='gemini', model_name_override='models/gemini-3-flash-preview',
        model_override=SimpleNamespace(cached_content='cachedContents/test'),
        use_gemini_rest=True, gemini_thinking_level='high', request_timeout_s=480))
    assert result['success'] is True
    assert len(captured) == 1
    assert captured[0][1] == 'high'
    assert captured[0][2] == {'timeout_s': 480.0, 'cached_content_name': 'cachedContents/test'}
    assert result['token_usage']['cached_tokens'] == 80


def test_only_supported_parallel_models_use_reasoning_transport():
    from ai.parallel_chat.orchestrator import _fact_reasoning_options
    assert _fact_reasoning_options('gemini', 'models/gemini-3.1-flash-lite') == {
        'use_gemini_rest': True, 'gemini_thinking_level': 'low'}
    assert _fact_reasoning_options('gemini', 'models/gemini-2.5-flash') == {}
    assert _fact_reasoning_options('openai', 'gpt-5') == {}


def test_branch_keeps_configured_model_and_reasoning_without_cache():
    from ai.parallel_chat.orchestrator import _run_branch_json
    calls = []
    class Analyzer:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            calls.append(kwargs)
            return {'success': True, 'response': '{"analysis":"Evidence-based interpretation","bullets":[]}',
                    'token_usage': {'input_tokens': 10, 'output_tokens': 10}}
    output, metrics = asyncio.run(_run_branch_json(
        Analyzer(), 'Use facts', {}, False, 'jaimini', critical=True,
        stage_provider='gemini', stage_model_hint='models/gemini-3.1-flash-lite'))
    assert output['analysis'] == 'Evidence-based interpretation'
    assert len(calls) == 1
    assert calls[0]['model_name_override'] == 'models/gemini-3.1-flash-lite'
    assert calls[0]['gemini_thinking_level'] == 'low'
    assert calls[0]['model_override'] is None
