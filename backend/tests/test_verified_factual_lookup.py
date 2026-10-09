import asyncio
import json
import pytest
from chat.verified_chat_pipeline import (
    _verified_presentation_mode, _premium_writer_system,
    _verified_final_writer_instruction, classify_verified_question,
)

@pytest.mark.parametrize('style', ['simple', 'technical'])
def test_factual_contract_in_both_writer_turns(style):
    for prompt in (_premium_writer_system('FACTUAL_LOOKUP', 'english', response_style=style),
                   _verified_final_writer_instruction(style, 'FACTUAL_LOOKUP')):
        assert 'VERIFIED FACTUAL LOOKUP OUTPUT CONTRACT' in prompt
        assert '## Your Answer' in prompt
        assert 'A compact Markdown' in prompt
        assert 'Neutral facts do not need Support/Caution color' in prompt
        assert 'LIFESPAN EVENT TIMELINE (MANDATORY)' not in prompt
        assert 'STANDARD SIMPLE OUTPUT CONTRACT' not in prompt
        assert 'actual value, unit, benchmark' in prompt
    system = _premium_writer_system('FACTUAL_LOOKUP', 'english', response_style=style)
    assert 'For any non-trivial chart reading, do not stop' not in system
    assert 'PARASHARI EVIDENCE DENSITY CONTRACT' not in system
    if style == 'simple':
        assert 'Do not hide "10th house"' in system
        assert 'do not expose chart codes, numbered houses' not in system


def test_lookup_scope_wins_over_stale_daily_metadata():
    assert _verified_presentation_mode({'intent_summary': {
        'mode': 'PREDICT_DAILY', 'answer_mode': 'factual_chart_lookup',
        'period_window': {'kind': 'day', 'start': '2026-10-13'},
    }}) == 'FACTUAL_LOOKUP'


def test_dasha_schedule_is_factual_even_with_a_year_horizon():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'Which dashas run' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'factual_chart_lookup', 'category': 'general',
                'route_action': 'answer', 'forecast_scope': 'other',
                'period_start': '2027-01-01', 'period_end': '2027-12-31'})}
    intent = asyncio.run(classify_verified_question(Router(),
        question='Which dashas run during 2027?', history=[], language='english'))
    assert intent['mode'] == 'FACTUAL_LOOKUP'
    assert intent['period_window']['end'] == '2027-12-31'
    assert _verified_presentation_mode({'intent_summary': intent}) == 'FACTUAL_LOOKUP'
