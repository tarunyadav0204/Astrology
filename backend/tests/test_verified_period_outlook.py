import asyncio
import json
import pytest
from chat.verified_chat_pipeline import (
    _verified_presentation_mode, _premium_writer_system,
    _verified_final_writer_instruction, classify_verified_question,
)

@pytest.mark.parametrize('style', ['simple', 'technical'])
def test_period_contract_reaches_both_writer_turns(style):
    mode = 'PREDICT_PERIOD_OUTLOOK'
    for prompt in (_premium_writer_system(mode, 'english', response_style=style),
                   _verified_final_writer_instruction(style, mode)):
        assert 'VERIFIED EVENTS WITHIN A PERIOD OUTPUT CONTRACT' in prompt
        assert 'Ranked Likely Developments' in prompt
        assert 'Main Chapters of Your Period' in prompt
        assert 'ENTIRE requested horizon' in prompt
        assert 'houses (1–12), start_date and end_date' in prompt
        assert 'LIFESPAN EVENT TIMELINE (MANDATORY)' not in prompt
        assert 'STANDARD SIMPLE OUTPUT CONTRACT' not in prompt
        assert 'career-only period question' in prompt
    final = _verified_final_writer_instruction(style, mode)
    if style == 'simple':
        assert '## What Is Shaping This Period?' in final
        assert '## Dive Deep:' not in final
    else:
        assert '## Dive Deep: Why These Themes Stand Out' in final


def test_year_outlook_router_preserves_full_period_and_uses_period_contract():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'one integrated period outlook' in prompt
            assert 'period_start' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'timing_window', 'category': 'general',
                'route_action': 'answer', 'forecast_scope': 'other',
                'time_relation': 'future', 'needs_transits': True,
                'period_start': '2027-01-01', 'period_end': '2027-12-31'})}
    intent = asyncio.run(classify_verified_question(Router(),
        question='How will 2027 be for my career, finances and family?', history=[], language='english'))
    assert intent['status'] == 'READY'
    assert intent['period_window'] == {'kind': 'window', 'start': '2027-01-01', 'end': '2027-12-31'}
    assert _verified_presentation_mode({'intent_summary': intent}) == 'PREDICT_PERIOD_OUTLOOK'


@pytest.mark.parametrize('mode,contract', [
    ('PREDICT_DAILY', 'APPROVED DAILY READING CONTRACT'),
    ('PREDICT_EVENT_TIMING', 'VERIFIED EVENT TIMING OUTPUT CONTRACT'),
    ('ANALYZE_TOPIC', 'STANDARD SIMPLE OUTPUT CONTRACT'),
])
def test_other_contracts_remain_distinct(mode, contract):
    prompt = _premium_writer_system(mode, 'english', response_style='simple')
    assert contract in prompt
    assert 'VERIFIED EVENTS WITHIN A PERIOD OUTPUT CONTRACT' not in prompt
