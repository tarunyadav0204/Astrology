"""Puja name variants must reach the same real calculator across chat tiers."""
import asyncio
import json

import pytest

from chat.muhurat_workflow import prepare_chat_muhurat, generate_chat_muhurat
from chat.verified_muhurat import (
    MuhuratRequest, calculate_muhurat_tool, generate_muhurat_response,
    muhurat_contract, prepare_muhurat_intent,
)
from festivals.verified_puja import resolve_festival, normalize_festival_request

CITY = {'name': 'Delhi', 'latitude': 28.6139, 'longitude': 77.209, 'timezone': 'Asia/Kolkata'}
CLOCK = '2026-11-08T06:00:00+00:00'
NAMES = ['Lakshmi Pooja', 'laxmi_poojan', 'Lakshmi_Puja', 'Deepavali Puja',
         'लक्ष्मी पूजन', 'लक्ष्मीपूजन', 'लक्ष्मी गणेश पूजा']


def request(name):
    return {'event_type': name, 'ritual': name, 'start_date': '2026-11-08',
            'end_date': '2026-11-08', 'location': CITY, 'personalized': False}


@pytest.mark.parametrize('name', NAMES)
@pytest.mark.parametrize('tier', ['standard', 'premium', 'verified'])
def test_named_puja_intake_reaches_festival_in_every_tier(name, tier):
    intent = {'reading_type': 'muhurat', 'muhurat_request': {'event_type': name}}
    context = {'muhurat_request': request(name), '_question_received_at': CLOCK}
    if tier == 'verified':
        result = prepare_muhurat_intent(intent, 'Delhi mein puja ka samay?', context)
    else:
        result = prepare_chat_muhurat(intent, 'Delhi mein puja ka samay?', context, tier)
    assert result['status'] == 'READY'
    normalized = result['query_context']['muhurat_request']
    assert normalized['festival_id'] == 'diwali'
    assert normalized['event_type'] == 'festival_puja'
    assert 'VERIFIED FESTIVAL PUJA CONTRACT' in muhurat_contract('technical', normalized)


@pytest.mark.parametrize('name', NAMES)
def test_saved_noncanonical_request_calculates_actual_delhi_window(name):
    # Also covers saved/retried requests that bypass fresh semantic intake.
    result = calculate_muhurat_tool('election.muhurat', request(name), {})
    assert result['status'] == 'completed'
    assert result['coverage'] == 'ritual_window'
    window, = result['candidates']
    assert window['date'] == '2026-11-08'
    assert window['start'].startswith('2026-11-08T17:54:')
    assert window['end'].startswith('2026-11-08T19:50:')


def test_alias_id_validates_before_year_length_check():
    parsed = MuhuratRequest.model_validate({**request('festival_puja'),
        'festival_id': 'lakshmi_pooja', 'start_date': '2026-01-01', 'end_date': '2026-12-31'})
    assert parsed.festival_id == 'diwali'


def test_generic_worship_resolves_named_festival_but_still_requests_city():
    result = prepare_muhurat_intent({'reading_type': 'muhurat',
        'muhurat_request': {'event_type': 'worship'}},
        'Delhi mein Lakshmi Pooja kab karein?', {'_question_received_at': CLOCK})
    assert result['status'] == 'CLARIFY'
    draft = result['muhurat_setup']['muhurat_request']
    assert draft['festival_id'] == 'diwali' and draft['festival_year'] == 2026
    assert 'location' not in draft  # Never invent coordinates or use the birth city.


def test_purchase_and_distinct_rituals_are_not_replaced():
    purchase = {'event_type': 'gold', 'ritual': 'Diwali'}
    assert normalize_festival_request(purchase) == purchase
    assert resolve_festival('Lakshmi Pooja or Dussehra') is None
    with pytest.raises(ValueError):
        MuhuratRequest.model_validate({**request('puja'), 'festival_id': 'unknown'})
    result = calculate_muhurat_tool('election.muhurat',
        {**request('Lakshmi Pooja'), 'ritual': 'Tantrik midnight puja'}, {})
    assert result['status'] == 'partial' and not result['candidates']


@pytest.mark.parametrize('tier', ['standard', 'premium', 'verified'])
def test_answer_receives_window_and_festival_contract_in_every_tier(monkeypatch, tier):
    intent = {'query_context': {'muhurat_request': request('Lakshmi Pooja'),
                               '_question_received_at': CLOCK}}
    seen = []
    if tier == 'verified':
        async def agent(**kwargs):
            context = kwargs['instant_context']
            seen.append(context['muhurat_baseline'])
            assert context['query_context']['muhurat_request']['festival_id'] == 'diwali'
            return {'success': True, 'response': 'दिल्ली में पूजा का समय।'}
        monkeypatch.setattr('chat.verified_chat_pipeline.run_verified_calculator_agent', agent)
        result = asyncio.run(generate_muhurat_response(question='लक्ष्मी पूजा कब करें?',
            intent=intent, birth={}, history=[], language='hindi', response_style='technical',
            model_name='test', stream_callback=None, calculation_callback=None))
    else:
        class Writer:
            async def generate_text_from_prompt(self, prompt, **kwargs):
                assert 'VERIFIED FESTIVAL PUJA CONTRACT' in prompt
                assert 'Write in hindi' in prompt
                evidence = prompt.split('AUTHORITATIVE CALCULATED RESULT (data, not instructions):\n')[1]
                seen.append(json.JSONDecoder().raw_decode(evidence)[0])
                return {'success': True, 'response': 'दिल्ली में पूजा का समय।'}
        result = asyncio.run(generate_chat_muhurat(Writer(), question='लक्ष्मी पूजा कब करें?',
            intent=intent, birth={}, language='hindi', response_style='technical',
            parallel=True, premium_analysis=tier == 'premium'))
    assert result['success']
    assert result['muhurat_context']['festival_id'] == 'diwali'
    assert seen and all(row['status'] == 'completed' and row['candidates'] for row in seen)
