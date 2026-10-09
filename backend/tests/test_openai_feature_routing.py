import asyncio
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from ai import analysis_llm_backend as routing
from utils import admin_settings

@pytest.mark.parametrize('feature', ['analysis', 'report', 'timeline'])
def test_openai_feature_selection(feature):
    with patch.object(routing, f'get_{feature}_llm_vendor', return_value='openai'), patch.object(routing, 'get_openai_feature_model', return_value='gpt-4o-mini') as setting:
        model, name, provider = getattr(routing, f'build_{feature}_llm_model')()
        assert isinstance(model, routing.OpenAIGenerativeAdapter)
        assert (name, provider) == ('gpt-4o-mini', 'openai')
        setting.assert_called_once_with(feature)

@pytest.mark.parametrize('feature', ['analysis', 'report', 'timeline'])
def test_vendor_accepts_openai(feature):
    with patch.object(admin_settings, 'get_setting', return_value='openai'):
        assert getattr(admin_settings, f'get_{feature}_llm_vendor')() == 'openai'

def test_adapter_uses_selected_model_json_and_usage(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    response = SimpleNamespace(output_text='{"answer":"yes"}', status='completed', usage=SimpleNamespace(input_tokens=12, output_tokens=8))
    with patch('openai.OpenAI') as client:
        client.return_value.responses.create.return_value = response
        model = routing.OpenAIGenerativeAdapter('gpt-4o-mini')
        result = asyncio.run(model.generate_content_async('Return JSON', generation_config={'response_mime_type':'application/json'}))
        params = client.return_value.responses.create.call_args.kwargs
        assert params['model'] == 'gpt-4o-mini'
        assert params['store'] is False
        assert params['text']['format']['type'] == 'json_object'
        assert result.usage_metadata.total_token_count == 20

def test_incomplete_output_rejected(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    with patch('openai.OpenAI') as client:
        client.return_value.responses.create.return_value = SimpleNamespace(status='incomplete')
        with pytest.raises(RuntimeError, match='did not complete'):
            routing.OpenAIGenerativeAdapter('gpt-4o-mini').generate_content('prompt')

def test_timeline_narration_openai():
    with patch.object(routing, 'get_event_timeline_narration_model', return_value='gpt-4o-mini'):
        model, name, provider = routing.build_timeline_narration_llm_model()
        assert isinstance(model, routing.OpenAIGenerativeAdapter)
        assert provider == 'openai'
