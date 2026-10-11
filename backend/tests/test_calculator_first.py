import asyncio
import json
from types import SimpleNamespace
import pytest
from chat import calculator_first as agent

BIRTH = dict(name='Synthetic QA', date='1990-01-01', time='12:00:00',
             latitude=28.6139, longitude=77.209, timezone='UTC+5:30', place='Delhi')
CLOCK = {'client_now_iso':'2026-10-11T12:00:00+05:30','timezone_name':'Asia/Kolkata'}


class Responses:
    def __init__(self, rounds): self.rounds = iter(rounds); self.sent = []
    async def create(self, **kwargs):
        self.sent.append(kwargs)
        calls, text = next(self.rounds)
        return SimpleNamespace(id=str(len(self.sent)), output=calls, output_text=text,
            usage=SimpleNamespace(input_tokens=10,output_tokens=5,input_tokens_details=SimpleNamespace(cached_tokens=2)))


def call(name, args, index=0):
    return SimpleNamespace(type='function_call',name=name,arguments=json.dumps(args),call_id=f'{name}-{index}')


def client(monkeypatch, responses):
    import openai
    class Client:
        def __init__(self, **kwargs): self.responses = responses
        async def __aenter__(self): return self
        async def __aexit__(self,*args): return False
    monkeypatch.setattr(openai,'AsyncOpenAI',Client)


def run(**kwargs):
    return asyncio.run(agent.generate_calculator_first_response(question='Explain my career',birth_data=BIRTH,
        history=[],language='english',query_context=CLOCK,model_name='test-model',**kwargs))


def test_initial_request_is_question_and_menu_without_eager_chart_or_classifier(monkeypatch):
    responses=Responses([([], 'What kind of work are you considering?')]);client(monkeypatch,responses)
    def forbidden(*args,**kwargs):raise AssertionError('An unrequested calculator ran')
    monkeypatch.setattr(agent.LazyCalculators,'calculate',forbidden)
    result=run()
    request=responses.sent[0]
    assert request['tool_choice']=='auto'
    assert len(request['input'])==1
    data=json.loads(request['input'][0]['content'])
    assert data['question']=='Explain my career'
    assert data['chart_owner_inputs']==BIRTH
    assert 'natal_calculations' not in data
    assert 'query_plan' not in data
    assert 'get_instant_baseline' not in [t['name'] for t in request['tools']]
    assert result['experiment_metrics']['calculator_requests']==0
    assert result['experiment_metrics']['classification_skipped']
    assert not result['experiment_metrics']['knowledge_graph_used']


def test_more_than_sixteen_rounds_and_cached_calculation(monkeypatch):
    requested=call('calculate',{'capability_id':'parashari.natal_foundation','parameters':None})
    responses=Responses([([requested], '')]*20+[([], 'An answer from actual calculations.')]);client(monkeypatch,responses)
    executed=[]
    monkeypatch.setattr(agent.LazyCalculators,'calculate',lambda self,*args: executed.append(args) or {'facts':{'ascendant':42}})
    result=run()
    assert len(executed)==1
    assert len(responses.sent)==21  # No extra writer call after Luna has answered.
    assert result['experiment_metrics']['tool_rounds']==20
    assert result['experiment_metrics']['calculator_round_limit'] is None
    assert result['experiment_metrics']['calculator_cache_hits']==19
    assert result['token_usage']['input_tokens']==210
    assert result['token_usage']['non_cached_input_tokens']==168
    assert result['instant_llm_usage_stages'][0]['stage']=='instant_calculator_first'


def test_progress_requires_success_and_failed_calculations_can_retry(monkeypatch):
    report=call('report_calculation',{'source':'parashari.shadbala','title':'Strength','summary':'The calculated strength is seven.'})
    calculate=call('calculate',{'capability_id':'parashari.shadbala','parameters':None})
    responses=Responses([([report,calculate], ''),([calculate], ''),([report], ''),([], 'Your reading.')]);client(monkeypatch,responses)
    executed=[]
    def calculate_actual(self,*args):
        executed.append(args)
        if len(executed)==1: raise ValueError('Missing location')
        return {'facts':{'strength':7}}
    monkeypatch.setattr(agent.LazyCalculators,'calculate',calculate_actual)
    trace=[]
    result=run(calculation_callback=trace.append)
    assert len(executed)==2
    assert len(trace)==1
    assert trace[0][0]['detail']=='The calculated strength is seven.'
    assert json.loads(responses.sent[1]['input'][0]['output'])['accepted'] is False
    assert 'calculation_unavailable' in responses.sent[1]['input'][1]['output']
    assert result['experiment_metrics']['first_progress_ms'] is not None


def test_clarification_retains_history_without_chart_calculation(monkeypatch):
    responses=Responses([([call('ask_user',{'question':'Which city are you moving to?'})], '')]);client(monkeypatch,responses)
    def forbidden(*args,**kwargs):raise AssertionError('Unrequested calculator')
    monkeypatch.setattr(agent.LazyCalculators,'calculate',forbidden)
    streamed=[]
    result=run(stream_callback=lambda delta,full:streamed.append(full))
    assert result['message_type']=='clarification'
    assert result['skip_instant_credit_charge']
    assert streamed==['Which city are you moving to?']
    assert result['experiment_metrics']['calculator_requests']==0


def test_unregistered_calculator_never_executes(monkeypatch):
    responses=Responses([([call('calculate',{'capability_id':'execute_python','parameters':None})], ''),([], 'That calculation is unavailable.')]);client(monkeypatch,responses)
    def forbidden(*args,**kwargs):raise AssertionError('Arbitrary calculator dispatched')
    monkeypatch.setattr(agent.LazyCalculators,'calculate',forbidden)
    run()
    assert json.loads(responses.sent[1]['input'][0]['output'])['error']=='unregistered_calculator'


def test_request_deadline_stops_run_instead_of_inventing_answer(monkeypatch):
    responses=Responses([]);client(monkeypatch,responses)
    monkeypatch.setattr(agent,'_timeout',lambda:-1)
    with pytest.raises(TimeoutError):run()
    assert not responses.sent


def test_lazy_core_calculators_use_real_birth_and_requested_dates():
    calculators=agent.LazyCalculators(BIRTH,CLOCK)
    assert calculators._chart is None
    natal=calculators.calculate('parashari.natal_foundation')
    assert len(natal['facts']['chart']['planets'])>=9
    assert len(natal['facts']['house_lords'])==12
    dasha=calculators.calculate('parashari.dasha_timing',{'start_date':'2026-10-11'})
    assert dasha['facts']['mahadasha']['planet']
    periods=calculators.calculate('parashari.dasha_timing',{'start_date':'2026-10-01','end_date':'2026-11-01'})
    assert periods['facts']['periods']
    assert periods['facts']['periods'][0]['start_utc'] == '2026-10-01T00:00:00+00:00'
    assert periods['facts']['periods'][-1]['end_utc'] == '2026-11-01T00:00:00+00:00'
    assert all(a['end_utc'] == b['start_utc'] for a,b in zip(periods['facts']['periods'],periods['facts']['periods'][1:]))
    transit=calculators.calculate('parashari.transit_activation',{'start_date':'2026-10-11','time':'00:00:00','planets':['Moon']})
    assert transit['facts']['snapshot_utc']=='2026-10-11T00:00:00+00:00'
    from calculators.real_transit_calculator import RealTransitCalculator
    from datetime import datetime,timezone
    midnight=datetime(2026,10,11,tzinfo=timezone.utc)
    expected=RealTransitCalculator().get_planet_state(midnight,'Moon',exact_time=True)['longitude']
    noon=RealTransitCalculator().get_planet_state(midnight,'Moon')['longitude']
    actual=transit['facts']['planets']['Moon']['longitude']
    assert actual==pytest.approx(expected)
    assert abs(actual-noon)>1
    with pytest.raises(ValueError,match='snapshot'):
        calculators.calculate('parashari.transit_activation',{'start_date':'2026-10-11','end_date':'2026-11-11'})


def test_parallel_path_selection_preserves_baseline_and_activates_from_configuration(monkeypatch):
    monkeypatch.delenv('INSTANT_CHAT_PATH',raising=False)
    assert agent.select_instant_path()=='baseline'
    monkeypatch.setenv('INSTANT_CHAT_PATH','calculator_first')
    assert agent.select_instant_path()=='calculator_first'
    assert agent.select_instant_path('baseline')=='baseline'
    monkeypatch.setenv('INSTANT_CHAT_PATH','baseline')
    assert agent.select_instant_path()=='baseline'
    with pytest.raises(ValueError):agent.select_instant_path('unknown')


def test_generation_dispatch_skips_all_legacy_initial_processing(monkeypatch):
    from chat import instant_chat_pipeline as pipeline
    def forbidden(*args,**kwargs):raise AssertionError('Legacy initial pipeline executed')
    for name in ['_build_instant_context','_mode_selection_from_intent','_infer_answer_mode_with_llm',
                 'build_instant_v2_packet','apply_live_graph_policy']:
        monkeypatch.setattr(pipeline,name,forbidden)
    received={}
    async def fake(**kwargs):received.update(kwargs);return {'success':True,'response':'Answer'}
    monkeypatch.setattr(agent,'generate_calculator_first_response',fake)
    result=asyncio.run(pipeline.generate_instant_chat_response(None,question='Old pending topic',latest_user_question='My new question',
        birth_data=BIRTH,intent={'query_context':CLOCK},history=[],calculator_first=True))
    assert result['success']
    assert received['question']=='My new question'
    assert received['query_context']==CLOCK
