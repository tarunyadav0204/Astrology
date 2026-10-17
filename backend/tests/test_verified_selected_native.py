import asyncio
import json
import pytest
from chat.verified_chat_pipeline import classify_verified_question
from chat.prashna_workflow import apply_prashna_transition

QUESTION = 'Break down the next three years by dashas for my friend’s health, including Parkinson’s-related concerns.'


@pytest.mark.parametrize('reply,reason,transition', [
    (QUESTION, 'missing_birth_details', 'natal'),
    ('This chart itself is my friend’s chart.', 'confirm_subject', 'natal'),
    ('yes', 'workflow', 'clarify_workflow'),
])
def test_selected_friend_chart_continues_original_natal_reading(reply, reason, transition):
    history = [{'question': QUESTION, 'response': 'Please confirm your friend’s chart.'},
               {'question': 'This chart itself is my friend’s chart.', 'response': 'Please confirm you want this health reading.'}]
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert '"available": true' in prompt
            assert 'next three years by dashas' in prompt
            assert 'not necessarily the person typing' in prompt
            return {'success': True, 'response': json.dumps({
                'subject_resolution': 'selected_chart', 'clarification_reason': reason,
                'route_action': 'clarify', 'user_message': 'Please confirm again.',
                'reading_transition': transition, 'resolved_question': QUESTION,
                'answer_mode': 'timing_window', 'category': 'health',
                'target_subject_key': 'friend', 'time_relation': 'future'})}
    context = {'selected_chart': {'available': True, 'name': 'Selected friend'}}
    intent = asyncio.run(classify_verified_question(Router(), question=reply, history=history,
        language='english', query_context=context))
    result = apply_prashna_transition(intent, reply, context)
    assert result['status'] == 'READY'
    assert result['route_action'] == 'answer'
    assert result['target_subject_key'] == 'self'
    assert result['resolved_question'] == QUESTION
    assert not result.get('workflow_choice')


def test_other_persons_missing_chart_still_requires_clarification():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            return {'success': True, 'response': json.dumps({'subject_resolution': 'other_chart',
                'clarification_reason': 'missing_birth_details', 'route_action': 'clarify',
                'user_message': 'Select your friend’s chart.', 'answer_mode': 'topic_reading',
                'category': 'health'})}
    intent = asyncio.run(classify_verified_question(Router(), question='Use a different friend’s chart',
        history=[], language='english', query_context={'selected_chart': {'available': True}}))
    assert intent['status'] == 'CLARIFY'
