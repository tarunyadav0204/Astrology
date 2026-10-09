import asyncio
import json
import pytest
from chat.verified_chat_pipeline import (
    _verified_presentation_mode, _premium_writer_system,
    _verified_final_writer_instruction, classify_verified_question,
)

@pytest.mark.parametrize('mode', ['PREDICT_EVENT_TIMING', 'LIFESPAN_EVENT_TIMING'])
@pytest.mark.parametrize('style', ['simple', 'technical'])
def test_event_contract_overrides_generic_layout_in_both_writer_turns(mode, style):
    system = _premium_writer_system(mode, 'english', response_style=style)
    final = _verified_final_writer_instruction(style, mode)
    for prompt in (system, final):
        assert 'VERIFIED EVENT TIMING OUTPUT CONTRACT' in prompt
        assert 'Ranked Event Windows' in prompt
        assert 'What Could Change the Timing?' in prompt
        assert 'houses (1–12), start_date and end_date' in prompt
        assert 'LIFESPAN EVENT TIMELINE (MANDATORY)' not in prompt
        assert 'STANDARD SIMPLE OUTPUT CONTRACT' not in prompt
    if style == 'simple':
        assert '## When the Opportunity Becomes Stronger' in final
        assert '## Dasha Analysis' not in final
    else:
        assert '## Dive Deep: Independent Confirmation' in final


def test_specific_event_on_one_day_is_not_daily_outlook():
    assert _verified_presentation_mode({'intent_summary': {
        'mode': 'PREDICT_EVENT_TIMING', 'answer_mode': 'event_prediction',
        'period_window': {'kind': 'day', 'start': '2026-11-01'},
    }}) == 'PREDICT_EVENT_TIMING'


def test_bounded_event_router_reaches_event_writer():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'including questions bounded to a month/year' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'event_prediction', 'category': 'career',
                'route_action': 'answer', 'forecast_scope': 'other',
                'time_relation': 'future', 'needs_transits': True})}
    intent = asyncio.run(classify_verified_question(Router(),
        question='Will I get promoted this November?', history=[], language='english'))
    mode = _verified_presentation_mode({'intent_summary': intent})
    assert mode == 'PREDICT_EVENT_TIMING'
    assert 'assess November first' in _verified_final_writer_instruction('technical', mode)


def test_verified_clarification_reply_retains_question_and_assistant_context():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'Only genuinely unrelated life areas are compound' in prompt
            assert 'Would you like the promotion timing' in prompt
            assert 'next 12 months' in prompt
            assert 'both together' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'event_prediction', 'category': 'career',
                'route_action': 'answer', 'time_relation': 'future'})}
    original = 'Will I get promoted in the next 12 months? Tell me the strongest timing windows, whether increased responsibility will come before formal promotion, and the astrological reasons.'
    intent = asyncio.run(classify_verified_question(Router(), question='both together',
        history=[{'question': original, 'response': 'Would you like the promotion timing and increased responsibility assessed together, or only the strongest promotion windows?'}],
        language='english'))
    assert intent['status'] == 'READY'
    assert intent['mode'] == 'PREDICT_EVENT_TIMING'
