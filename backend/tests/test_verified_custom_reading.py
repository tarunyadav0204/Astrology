import asyncio
import json

import pytest

from chat.verified_chat_pipeline import (
    _premium_writer_system,
    _verified_final_writer_instruction,
    _verified_presentation_mode,
    classify_verified_question,
)


@pytest.mark.parametrize('style', ['simple', 'technical'])
@pytest.mark.parametrize('mode', ['CUSTOM_READING', 'DEFAULT'])
def test_unmatched_questions_choose_their_own_source_scoped_format(style, mode):
    system = _premium_writer_system(mode, 'english', response_style=style)
    final = _verified_final_writer_instruction(style, mode)
    for prompt in (system, final):
        assert 'QUESTION-LED OUTPUT' in prompt
        assert 'annotated' in prompt
        assert 'BPHS requests do not require Jaimini, Nadi or KP' in prompt
        assert 'Never invent sutra wording, chapter/verse citations' in prompt
        assert 'STANDARD SIMPLE OUTPUT CONTRACT' not in prompt
        assert 'PARASHARI EVIDENCE DENSITY CONTRACT' not in prompt
    assert 'For any non-trivial chart reading, do not stop' not in system


def test_custom_scope_wins_over_stale_forecast_metadata():
    assert _verified_presentation_mode({
        'intent_summary': {'mode': 'CUSTOM_READING', 'period_window': {'kind': 'day'}},
        'query_plan': {'forecast_shape': 'daily_forecast'},
    }) == 'CUSTOM_READING'


def test_source_rule_matching_routes_to_custom_reading():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'select custom_reading' in prompt
            assert 'An explicit text/method scope overrides generic multi-school presentation.' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'custom_reading', 'category': 'general',
                'route_action': 'answer', 'reading_type': 'default',
                'prashna_intent': 'none', 'forecast_scope': 'other',
            })}

    intent = asyncio.run(classify_verified_question(
        Router(), question='Tell me all sutras matching my chart from BPHS',
        history=[], language='english',
    ))
    assert intent['mode'] == 'CUSTOM_READING'
    assert _verified_presentation_mode({'intent_summary': intent}) == 'CUSTOM_READING'
