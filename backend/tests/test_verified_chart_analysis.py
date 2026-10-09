import asyncio
import json
import pytest
from chat.verified_chat_pipeline import (
    _verified_presentation_mode, _premium_writer_system,
    _verified_final_writer_instruction, classify_verified_question,
)

@pytest.mark.parametrize('style', ['simple', 'technical'])
def test_subject_contract_reaches_both_writer_turns(style):
    for prompt in (_premium_writer_system('CHART_DASHA_ANALYSIS', 'english', response_style=style),
                   _verified_final_writer_instruction(style, 'CHART_DASHA_ANALYSIS')):
        assert 'VERIFIED CHART & DASHA ANALYSIS OUTPUT CONTRACT' in prompt
        assert 'jaimini.points' in prompt
        assert 'parameters.divisions' in prompt
        assert 'dasha.yogini for Yogini' in prompt
        assert 'supply explicit start_date and end_date' in prompt
        assert 'For an unsupported system' in prompt
        assert 'yearly Sudarshana triggers are not a full nested dasha schedule' in prompt
        assert 'Do not substitute ordinary D9 ascendant' in prompt
        assert 'STANDARD SIMPLE OUTPUT CONTRACT' not in prompt
        assert 'VERIFIED FACTUAL LOOKUP OUTPUT CONTRACT' not in prompt
    if style == 'simple':
        assert 'Preserve requested chart names' in prompt


@pytest.mark.parametrize('question', ['Explain my D9 chart', 'Explain my karkamsha chart', 'Explain my Yogini dasha', 'Explain my Chara dasha', 'Explain my Kalachakra dasha', 'Explain my Ashtottari dasha'])
def test_broad_named_subject_routes_to_analysis(question):
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'reading_type chart_dasha_analysis' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'topic_reading', 'reading_type': 'chart_dasha_analysis',
                'category': 'general', 'route_action': 'answer', 'forecast_scope': 'other'})}
    intent = asyncio.run(classify_verified_question(Router(), question=question, history=[], language='english'))
    assert intent['status'] == 'READY'
    assert intent['mode'] == 'CHART_DASHA_ANALYSIS'
    # The downstream calculator planner can identify a named chart as factual;
    # the approved interpretation mode must still control presentation.
    assert _verified_presentation_mode({'intent_summary': {
        **intent, 'answer_mode': 'factual_chart_lookup'}}) == 'CHART_DASHA_ANALYSIS'


@pytest.mark.parametrize('answer_mode,mode', [
    ('factual_chart_lookup', 'FACTUAL_LOOKUP'),
    ('event_prediction', 'PREDICT_EVENT_TIMING'),
])
def test_specific_fact_or_event_does_not_become_chart_analysis(answer_mode, mode):
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            return {'success': True, 'response': json.dumps({
                'answer_mode': answer_mode, 'reading_type': 'chart_dasha_analysis',
                'category': 'general', 'route_action': 'answer'})}
    intent = asyncio.run(classify_verified_question(Router(), question='What is my Karakamsa sign?', history=[], language='english'))
    assert intent['mode'] == mode
