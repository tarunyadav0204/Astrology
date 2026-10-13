import asyncio
import json
from types import SimpleNamespace

import pytest
from ai.chat_subject_gate import ChatSubjectGate
from chat import verified_chat_pipeline as pipeline
from chat_history import routes


@pytest.mark.parametrize('reply', ['No, use my chart', 'Continue with my chart only', 'Use my chart'])
def test_explicit_choice_resolves_without_model(reply):
    result = asyncio.run(ChatSubjectGate().resolve_pending_gate_reply(
        pending_gate={'intent_gate': 'partnership_offer', 'original_question': 'Will my spouse like me?'},
        user_message=reply, birth_details={'name': 'Native'}, language='english'))
    assert result['action'] == 'continue_selected_chart'
    assert result['reason'] == 'explicit_selected_chart_choice'


def test_selected_chart_does_not_handoff_again():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert '"selected_chart_only": true' in prompt
            assert 'Will my spouse like me?' in prompt
            return {'success': True, 'response': json.dumps({'answer_mode': 'topic_reading',
                'category': 'relationship', 'route_action': 'handoff', 'user_message': 'Use Partnership'})}
    intent = asyncio.run(pipeline.classify_verified_question(Router(), question='No, use my chart',
        history=[], language='english', query_context={'selected_chart_only': True,
        '_selected_chart_question': 'Will my spouse like me?'}))
    assert intent['route_action'] == 'answer'
    assert intent['status'] == 'READY'
    assert not intent.get('clarification_question')


def test_chart_choice_is_durable_and_session_scoped(monkeypatch):
    metadata = {'intent_gate': 'partnership_offer'}
    calls = []
    monkeypatch.setattr(routes, '_ensure_chat_messages_gate_metadata', lambda conn: None)
    def execute(conn, query, params):
        calls.append((query, params))
        if 'UPDATE' in query:
            metadata.update(json.loads(params[0]))
        return SimpleNamespace(fetchone=lambda: (42, json.dumps(metadata)))
    monkeypatch.setattr(routes, 'execute', execute)
    assert not routes._selected_chart_preference(None, 'session-a')
    assert routes._selected_chart_preference(None, 'session-a', remember=True)
    assert routes._selected_chart_preference(None, 'session-a')
    assert all('session-a' in params for _, params in calls)


def test_writer_identifies_relative_house_frame():
    system = pipeline._premium_writer_system('DEFAULT', 'english', response_style='technical')
    assert "native's 7th is the spouse's derived 1st" in system
    assert 'Never' in system and 'describe a derived house as "your" house' in system
    assert "Native dasha periods remain the native's periods" in system
