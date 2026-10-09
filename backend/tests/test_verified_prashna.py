import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
import json
import pytest
from chat.verified_prashna import freeze_prashna, question_birth, calculate_prashna, PRASHNA_CAPABILITIES

LOCATION = {'name':'Gurugram','latitude':28.4595,'longitude':77.0266}


def fixed():
    return freeze_prashna(LOCATION, datetime(2026,10,9,16,3,tzinfo=timezone.utc))


def test_clock_uses_question_location_and_immutable_received_moment():
    context = fixed()
    birth = question_birth(context)
    assert birth['date'] == '2026-10-09'
    assert birth['time'] == '21:33:00'
    assert birth['place'] == 'Gurugram'
    assert birth['relation'] == 'prashna'
    assert question_birth(json.loads(json.dumps(context))) == birth
    with pytest.raises(ValueError): freeze_prashna({'name':'Invalid','latitude':91,'longitude':0}, datetime.now(timezone.utc))


@pytest.mark.parametrize('capability', list(PRASHNA_CAPABILITIES))
def test_actual_question_calculators_have_explicit_question_basis(capability):
    output = calculate_prashna(capability, fixed(), {'planets':['Mars','Venus'], 'houses':[10]})
    assert output['chart_basis'] == 'question_chart'
    assert output['clock']['submitted_at'] == fixed()['submitted_at']
    assert output['facts']
    json.dumps(output)
    if capability == 'prashna.kp': assert output['facts']['cusp_lords']
    if capability == 'prashna.tajika': assert output['profile'] == 'hayanaratna_textual_precession_quadrant_v1'


def test_no_natal_tool_or_invalid_tajika_parameters():
    with pytest.raises(ValueError): calculate_prashna('dasha.yogini', fixed(), {})
    with pytest.raises(ValueError): calculate_prashna('prashna.tajika', fixed(), {})


def test_agent_only_exposes_question_tools_and_streams(monkeypatch):
    import openai
    import chat.verified_chat_pipeline as pipeline
    import chat.verified_prashna as prashna
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    # Any accidental natal baseline timeline computation must fail this test.
    monkeypatch.setattr(pipeline,'_historical_vimshottari_timeline',lambda *a: (_ for _ in ()).throw(AssertionError('natal timeline')))
    sent=[]; streamed=[]
    class Events:
        async def __aenter__(self): return self
        async def __aexit__(self,*args): return False
        def __aiter__(self):
            async def events():
                yield SimpleNamespace(type='response.output_text.delta',delta='**The opportunity looks conditional.**')
            return events()
        async def get_final_response(self): return SimpleNamespace(usage=None,output_text='')
    class Responses:
        async def create(self,**kwargs):
            sent.append(kwargs)
            if len(sent)==1:
                return SimpleNamespace(id='baseline',usage=None,output=[SimpleNamespace(type='function_call',name='get_instant_baseline',call_id='base',arguments='{}')])
            if len(sent)==2:
                return SimpleNamespace(id='kp',usage=None,output=[SimpleNamespace(type='function_call',name='get_deterministic_evidence',call_id='kp-call',arguments=json.dumps({'capability_id':'prashna.kp','parameters':None}))])
            return SimpleNamespace(id='done',usage=None,output=[])
        def stream(self,**kwargs): sent.append(kwargs); return Events()
    monkeypatch.setattr(openai,'AsyncOpenAI',lambda **kwargs: SimpleNamespace(responses=Responses()))
    result=asyncio.run(prashna.generate_prashna_response(question='Will I get this job?',
        intent={'category':'career','query_context':{'prashna':fixed()}}, history=[{'question':'Will I get this job?', 'response':'The earlier conclusion remains favorable. KP was previously considered.'}],language='english',response_style='technical',
        model_name='gpt-5.6-luna',stream_callback=lambda delta,full:streamed.append(full),calculation_callback=None))
    assert streamed == ['**The opportunity looks conditional.**']
    enum = sent[0]['tools'][1]['parameters']['properties']['capability_id']['enum']
    assert set(enum)==set(PRASHNA_CAPABILITIES)
    baseline=json.loads(sent[1]['input'][0]['output'])
    assert baseline['chart_basis']=='question_chart'
    assert 'historical_timing_evidence' not in baseline
    assert result['information_rounds']['reading_mode']=='PRASHNA'
    assert result['information_rounds']['events'][-1]['calculator']=='prashna.kp'
    assert 'VERIFIED PRASHNA CONTRACT' in sent[-1]['input'][-1]['content'][0]['text']
    assert 'KP was previously considered.' in sent[0]['input']  # Keep follow-up history.
    assert 'not previously delivered readings' in sent[0]['input']
    assert 'CURRENT READING, NOT A RECAP' in sent[0]['instructions']
    assert 'CURRENT READING, NOT A RECAP' in sent[-1]['input'][-1]['content'][0]['text']


@pytest.mark.parametrize('style', ['simple', 'technical'])
def test_prashna_contract_is_current_reading_in_both_writer_phases(style):
    from chat.verified_prashna import prashna_contract
    from chat.verified_chat_pipeline import _verified_final_writer_instruction
    for prompt in (prashna_contract(style), _verified_final_writer_instruction(style, 'PRASHNA')):
        assert 'CURRENT READING, NOT A RECAP' in prompt
        assert 'CURRENT question explicitly asks to revisit or compare' in prompt
        assert 'not verified evidence' in prompt
        assert 'internal preparation' in prompt
        assert 'successfully calculated IN THIS REQUEST' in prompt
