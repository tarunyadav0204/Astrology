import asyncio
import json
from types import SimpleNamespace

import pytest

from chat import verified_chat_pipeline as pipeline
from chat import verified_partnership as partnership


def pair_fixture():
    return {
        'birth_data': {'native': {'name': 'A'}, 'partner': {'name': 'B'}},
        'contexts': {'native': {'natal_snapshot': {'owner': 'A'}}, 'partner': {'natal_snapshot': {'owner': 'B'}}},
        'charts': {'native': {'D1': {'owner': 'A'}, 'D9': {'owner': 'A'}},
                   'partner': {'D1': {'owner': 'B'}, 'D9': {'owner': 'B'}}},
        'relationship': 'business partners', 'synastry': {'D1': {'contacts': []}, 'D9': {'contacts': []}},
    }


def test_zero_coordinates_valid_and_missing_partner_rejected():
    partnership.validate_partner_birth_data({'name': 'A', 'date': '1990-01-01', 'time': '00:00', 'latitude': 0, 'longitude': 0})
    with pytest.raises(ValueError, match='Partner time'):
        partnership.validate_partner_birth_data({'name': 'A', 'date': '1990-01-01'})
    with pytest.raises(ValueError, match='out of range'):
        partnership.validate_partner_birth_data({'name': 'A', 'date': '1990-01-01', 'time': '12:00', 'latitude': 91, 'longitude': 0})


def test_raw_geometry_keeps_house_ownership_and_wraps_longitude():
    native = {'ascendant': 0, 'planets': {'Moon': {'longitude': 359}}}
    partner = {'ascendant': 90, 'planets': {'Venus': {'longitude': 1}}}
    result = partnership.cross_chart_geometry(native, partner)
    assert result['contacts'][0]['separation_degrees'] == 2
    assert result['overlays']['native_planets_in_partner_houses'][0] == {
        'planet': 'Moon', 'planet_owner': 'native', 'house_owner': 'partner', 'house': 9}
    assert 'score' not in result and 'verdict' not in result


def test_baseline_has_independent_named_charts_and_timelines(monkeypatch):
    monkeypatch.setattr(pipeline, '_historical_vimshottari_timeline', lambda birth: {'owner': birth['name']})
    result = partnership.build_partnership_baseline(pair_fixture())
    assert result['relationship'] == 'business partners'
    for subject, name in [('native', 'A'), ('partner', 'B')]:
        assert result['subjects'][subject]['name'] == name
        assert result['subjects'][subject]['natal_calculations']['owner'] == name
        assert result['subjects'][subject]['historical_timing_evidence']['vimshottari_md_ad_timeline']['owner'] == name


def test_calculator_selects_actual_chart_and_preserves_partial_failure(monkeypatch):
    seen = []
    def calculate(birth, requested, baseline, context, parameters):
        seen.append((birth['name'], parameters))
        if birth['name'] == 'B':
            raise ValueError('Missing time')
        return {requested[0]: {'owner': birth['name']}}
    monkeypatch.setattr(pipeline, '_calculate_requested_capabilities', calculate)
    result = partnership.calculate_partnership_capability(pair_fixture(), 'jaimini.points', 'both', {'divisions': [9]})
    assert result['subjects']['native']['owner'] == 'A'
    assert result['subjects']['partner']['error'] == 'calculation_unavailable'
    assert 'error' not in result
    assert [row[0] for row in seen] == ['A', 'B']
    with pytest.raises(ValueError, match='Choose native'):
        partnership.calculate_partnership_capability(pair_fixture(), 'jaimini.points', 'unknown', None)


def test_real_d1_d9_and_dated_calculators(monkeypatch):
    birth = {'name': 'A', 'date': '1990-01-01', 'time': '12:00', 'latitude': 28.61, 'longitude': 77.21, 'timezone': 'Asia/Kolkata'}
    other = {**birth, 'name': 'B', 'date': '1992-06-15', 'partnership_relationship': 'spouse'}
    pair = partnership.build_partnership_context(birth_data=birth, partner_birth_data=other,
        question='When can we marry?', intent={'target_subject': 'spouse', 'category': 'marriage'}, history=[])['verified_partnership']
    assert all(item['intent_summary']['target_subject'] == 'self' for item in pair['contexts'].values())
    assert pair['synastry']['D1']['contacts'] and pair['synastry']['D9']['contacts']
    baseline = partnership.build_partnership_baseline(pair)
    for subject in ('native', 'partner'):
        evidence = baseline['subjects'][subject]['multi_system_foundations']
        assert evidence['jaimini.significators_and_arudhas']['chara_karakas']
        assert evidence['jaimini.points']['facts']
        assert evidence['jaimini.chara_dasha']['periods']
        assert not evidence['jaimini.chara_dasha'].get('truncated')
        assert evidence['nadi.linkages']['links']
        assert evidence['nakshatra.positions']['Moon']['nakshatra_name']
        assert 1 <= evidence['nakshatra.positions']['Moon']['pada'] <= 4
        assert baseline['subjects'][subject]['core_charts']['D9']['planets']
    assert pair['charts']['native']['D1']['planets']['Moon'] != pair['charts']['partner']['D1']['planets']['Moon']
    transits = partnership.calculate_partnership_capability(pair, 'parashari.dated_transits', 'both', {'start_date': '2027-01-01'})
    assert set(transits['subjects']) == {'native', 'partner'}
    assert all(row.get('snapshot_at') == '2027-01-01T12:00:00Z' for row in transits['subjects'].values())
    periods = partnership.calculate_partnership_capability(pair, 'parashari.vimshottari_periods', 'both', {'start_date': '2027-01-01', 'end_date': '2028-01-01'})
    assert all(row.get('periods') for row in periods['subjects'].values())


def test_agent_routes_tools_by_chart_caches_separately_and_preserves_history(monkeypatch):
    import openai
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-test-key')
    monkeypatch.setattr(pipeline, '_historical_vimshottari_timeline', lambda birth: {})
    seen = []
    def calculate(birth, requested, baseline, context, parameters):
        seen.append(birth['name'])
        return {requested[0]: {'owner': birth['name']}}
    monkeypatch.setattr(pipeline, '_calculate_requested_capabilities', calculate)
    sent = []
    def call(subject, ident):
        return SimpleNamespace(type='function_call', name='get_deterministic_evidence', call_id=ident,
            arguments=json.dumps({'capability_id': 'jaimini.points', 'chart_subject': subject, 'parameters': None}))
    class Events:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        def __aiter__(self): return self
        async def __anext__(self): raise StopAsyncIteration
        async def get_final_response(self): return SimpleNamespace(output_text='A and B can work together.', usage=None)
    class Responses:
        async def create(self, **kwargs):
            sent.append(kwargs)
            if len(sent) == 1:
                outputs = [SimpleNamespace(type='function_call', name='get_instant_baseline', call_id='baseline', arguments='{}')]
            elif len(sent) == 2:
                outputs = [call('native', 'a1'), call('partner', 'b1')]
            elif len(sent) == 3:
                outputs = [call('native', 'a2'), call('both', 'both')]
            else:
                outputs = []
            return SimpleNamespace(id=f'response-{len(sent)}', usage=None, output=outputs)
        def stream(self, **kwargs): sent.append(kwargs); return Events()
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(responses=Responses()))
    result = asyncio.run(pipeline.run_verified_calculator_agent(question='Will our business work?',
        language='english', birth_data={'name': 'A'}, instant_context={'verified_partnership': pair_fixture()},
        history=[{'question': 'We plan to start in January.', 'response': 'Tell me about your partner.'}], model_name='gpt-5.6-luna', timeout_s=60))
    assert result['success']
    assert seen == ['A', 'B', 'A', 'B']  # repeated native-only call was cached; both is independent
    assert 'We plan to start in January' in sent[0]['input']
    tools = sent[0]['tools']
    assert 'chart_subject' in tools[1]['parameters']['required']
    assert set(tools[1]['parameters']['properties']['chart_subject']['enum']) == {'native', 'partner', 'both'}
    baseline = json.loads(sent[1]['input'][0]['output'])
    assert set(baseline['subjects']) == {'native', 'partner'}
    outputs = [json.loads(item['output']) for item in sent[2]['input']]
    assert outputs[0]['subjects']['native']['owner'] == 'A'
    assert outputs[1]['subjects']['partner']['owner'] == 'B'
    assert 'VERIFIED TWO-CHART READING' in sent[-1]['instructions']
    assert 'VERIFIED TWO-CHART READING' in sent[-1]['input'][-1]['content'][0]['text']
    assert result['information_rounds']['reading_mode'] == 'VERIFIED_PARTNERSHIP'


def test_verified_dispatch_bypasses_single_chart_writer(monkeypatch):
    from chat.instant_chat_pipeline import generate_instant_chat_response
    async def generate(**kwargs):
        assert kwargs['partner_birth_data']['name'] == 'B'
        return {'success': True, 'response': 'two-chart answer'}
    monkeypatch.setattr(partnership, 'generate_verified_partnership_response', generate)
    result = asyncio.run(generate_instant_chat_response(None, question='Compare us', birth_data={'name': 'A'},
        intent={}, history=[], verified_evidence_review=True, verified_partner_birth_data={'name': 'B'}, model_name_override='gpt-5.6-luna'))
    assert result['response'] == 'two-chart answer'


def test_two_chart_router_does_not_offer_prashna(monkeypatch):
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'two actual birth charts are already supplied' in prompt
            return {'success': True, 'response': json.dumps({'answer_mode': 'topic_reading', 'category': 'relationship',
                'route_action': 'answer', 'prashna_intent': 'offer'})}
    intent = asyncio.run(pipeline.classify_verified_question(Router(), question='Will we stay together?', history=[],
        language='english', query_context={'verified_partnership': True, 'chart_names': ['A', 'B']}))
    assert intent['status'] == 'READY'
    assert intent['prashna_intent'] == 'none'


def test_active_partnership_recovers_compatibility_handoff():
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'ONLY when TWO-CHART CONTEXT is disabled' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'topic_reading', 'category': 'relationship',
                'route_action': 'handoff', 'user_message': 'Please use partnership mode.'})}
    intent = asyncio.run(pipeline.classify_verified_question(Router(),
        question='Are we compatible?', history=[], language='english',
        query_context={'verified_partnership': True, 'chart_names': ['A', 'B']}))
    assert intent['status'] == 'READY'
    assert not intent.get('clarification_question')
    single = asyncio.run(pipeline.classify_verified_question(Router(),
        question='Are we compatible?', history=[], language='english', query_context={}))
    assert intent['route_action'] == 'answer'
    assert single['route_action'] == 'handoff'
    assert single['clarification_question'] == 'Please use partnership mode.'


@pytest.mark.parametrize('category,division', [('business','D10'), ('children','D7'), ('property','D4'), ('family','D12')])
def test_partnership_supplies_topic_divisions_for_each_real_chart(category, division):
    birth = {'name':'A','date':'1990-01-01','time':'12:00','latitude':28.61,'longitude':77.21,'timezone':'Asia/Kolkata'}
    pair = partnership.build_partnership_context(birth_data=birth,
        partner_birth_data={**birth,'name':'B','date':'1992-06-15'},
        question='Analyze our partnership',intent={'category':category},history=[])['verified_partnership']
    for subject in ('native','partner'):
        assert pair['charts'][subject][division]['planets']
        assert pair['charts'][subject]['D9']['planets']
    assert pair['charts']['native'][division]['planets'] != pair['charts']['partner'][division]['planets']
