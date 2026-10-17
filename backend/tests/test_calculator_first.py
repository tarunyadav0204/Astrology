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


    def stream(self, **kwargs):
        owner = self
        class Stream:
            async def __aenter__(self):
                self.response = await owner.create(**kwargs)
                return self
            async def __aexit__(self, *args): return False
            def __aiter__(self):
                async def events():
                    for token in self.response.output_text.splitlines(keepends=True):
                        yield SimpleNamespace(type='response.output_text.delta', delta=token)
                return events()
            async def get_final_response(self): return self.response
        return Stream()


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


def test_answer_deltas_arrive_before_provider_finishes_without_duplicate_final(monkeypatch):
    delivered = []
    class ResponsesWithTokens(Responses):
        def stream(self, **kwargs):
            owner = self
            class Stream:
                async def __aenter__(self):
                    self.response = await owner.create(**kwargs)
                    return self
                async def __aexit__(self, *args): return False
                def __aiter__(self):
                    async def events():
                        yield SimpleNamespace(type='response.reasoning_text.delta', delta='Private reasoning')
                        yield SimpleNamespace(type='response.function_call_arguments.delta', delta='Internal arguments')
                        yield SimpleNamespace(type='response.output_text.delta', delta='Your ')
                        assert delivered == [('Your ', 'Your ')]
                        yield SimpleNamespace(type='response.output_text.delta', delta='reading.')
                        assert delivered[-1] == ('reading.', 'Your reading.')
                    return events()
                async def get_final_response(self):
                    assert len(delivered) == 2
                    return self.response
            return Stream()
    responses = ResponsesWithTokens([([], 'Your reading.')])
    client(monkeypatch, responses)
    result = run(stream_callback=lambda delta, full: delivered.append((delta, full)))
    assert result['response'] == 'Your reading.'
    assert delivered == [('Your ', 'Your '), ('reading.', 'Your reading.')]
    assert result['token_usage']['input_tokens'] == 10
    assert len(responses.sent) == 1


def test_stream_iteration_obeys_turn_deadline(monkeypatch):
    class StalledResponses(Responses):
        def stream(self, **kwargs):
            class Stream:
                async def __aenter__(self): return self
                async def __aexit__(self, *args): return False
                def __aiter__(self):
                    async def events():
                        await asyncio.sleep(10)
                        yield SimpleNamespace(type='response.output_text.delta', delta='Late answer')
                    return events()
            return Stream()
    client(monkeypatch, StalledResponses([]))
    monkeypatch.setattr(agent, '_timeout', lambda: 0.05)
    with pytest.raises(asyncio.TimeoutError):
        run()


def test_chart_chat_requests_substantive_plain_language_answers_not_one_line(monkeypatch):
    responses = Responses([([], 'An explained reading.')])
    client(monkeypatch, responses)
    asyncio.run(agent.generate_calculator_first_response(
        question='What does my chart say about my career?', birth_data=BIRTH,
        history=[], query_context={**CLOCK, 'source': 'chart_sheet'}, model_name='test-model'))
    instructions = responses.sent[0]['instructions']
    assert 'simple means plain language, not a short or superficial answer' in instructions
    assert '3–6 short paragraphs' in instructions
    assert 'This limit does not apply to the final answer' in instructions
    assert 'ONLY the report_calculation progress summary' in instructions


def test_chart_answer_depth_is_not_applied_to_other_instant_conversations(monkeypatch):
    responses = Responses([([], 'A conversational answer.')])
    client(monkeypatch, responses)
    run()
    assert 'For Chart Chat' not in responses.sent[0]['instructions']


@pytest.mark.parametrize('question', [
    'मेरी शादी कब होगी?',
    'meri shaadi kab hogi?',
    'When will I get married?',
    'என் திருமணம் எப்போது?',
])
def test_chart_chat_language_is_chosen_from_current_question_and_survives_tools(monkeypatch, question):
    responses = Responses([
        ([call('calculate', {'capability_id': 'parashari.natal_foundation', 'parameters': None})], ''),
        ([], 'Synthetic answer'),
    ])
    client(monkeypatch, responses)
    monkeypatch.setattr(agent.LazyCalculators, 'calculate', lambda *args: {'facts': {'English tool label': 7}})
    asyncio.run(agent.generate_calculator_first_response(
        question=question, birth_data=BIRTH,
        history=[{'role': 'user', 'content': 'An older English question'}],
        language='english', query_context={**CLOCK, 'source': 'chart_sheet'}, model_name='test-model'))
    assert json.loads(responses.sent[0]['input'][0]['content'])['question'] == question
    for request in responses.sent:
        instructions = request['instructions']
        assert 'The current user question is authoritative' in instructions
        assert 'Roman Hindi/Hinglish questions in natural Roman Hindi/Hinglish' in instructions
        assert 'Never switch to English after receiving a calculator result' in instructions
        assert 'most recent substantive USER question in history' in instructions
        assert 'Explicit language-switch requests still take priority' in instructions
    assert question in responses.sent[1]['input'][-1]['content']
    assert 'Do not let your own earlier progress labels choose the language' in responses.sent[1]['input'][-1]['content']


def test_requested_calculation_activity_is_published_before_execution(monkeypatch):
    capability = 'parashari.natal_foundation'
    responses = Responses([
        ([call('calculate', {'capability_id': capability, 'parameters': None, 'activity_title': 'जन्म कुंडली की जाँच'})], ''),
        ([call('report_calculation', {'source': capability, 'title': 'Calculated placements', 'summary': 'A supported chart finding.'})], ''),
        ([], 'An explained answer.'),
    ])
    client(monkeypatch, responses)
    traces = []
    def calculate(*args):
        assert traces[0][0]['title'] == 'जन्म कुंडली की जाँच'
        assert traces[0][0]['detail'] == ''  # activity, not an invented finding
        return {'facts': {'ascendant': 42}}
    monkeypatch.setattr(agent.LazyCalculators, 'calculate', calculate)
    run(calculation_callback=traces.append)
    assert len(traces) == 2
    assert traces[1] == [{'id': f'instant-calculation-{capability}', 'title': 'Calculated placements', 'detail': 'A supported chart finding.'}]


def test_chart_health_policy_requires_interpretation_without_false_medical_causation(monkeypatch):
    responses = Responses([([], 'Synthetic answer.')])
    client(monkeypatch, responses)
    asyncio.run(agent.generate_calculator_first_response(
        question='What in this chart gave Parkinson’s to this native?', birth_data=BIRTH,
        history=[], query_context={**CLOCK, 'source': 'chart_sheet'}, model_name='test-model'))
    instructions = responses.sent[0]['instructions']
    assert 'not the native receiving a personal consultation' in instructions
    assert 'request relevant natal and strength calculators first' in instructions
    assert 'Do not claim that a placement establishes a medical cause or diagnosis' in instructions
    assert 'Do not append routine medical disclaimers or unsolicited symptom checklists' in instructions
    assert 'Do not predict death' not in instructions
    assert 'not blanket-banned discussion topics' in instructions
    assert 'Do not state an individual’s death date or lifespan as a reliable fact' in instructions


def test_activity_is_visible_before_provider_round_finishes(monkeypatch):
    traces = []
    item = call('calculate', {'capability_id': 'parashari.natal_foundation', 'parameters': None, 'activity_title': 'Inspecting natal placements'})
    class EarlyResponses(Responses):
        def stream(self, **kwargs):
            owner = self
            class Stream:
                async def __aenter__(self):
                    self.response = await owner.create(**kwargs)
                    return self
                async def __aexit__(self, *args): return False
                def __aiter__(self):
                    async def events():
                        if self.response.output:
                            yield SimpleNamespace(type='response.output_item.done', item=item)
                            assert traces[0][0]['title'] == 'Inspecting natal placements'
                        elif self.response.output_text:
                            yield SimpleNamespace(type='response.output_text.delta', delta=self.response.output_text)
                    return events()
                async def get_final_response(self): return self.response
            return Stream()
    client(monkeypatch, EarlyResponses([([item], ''), ([], 'Answer')]))
    monkeypatch.setattr(agent.LazyCalculators, 'calculate', lambda *args: {'facts': {'ascendant': 42}})
    run(calculation_callback=traces.append)
    assert len(traces) == 1  # executing the requested tool does not duplicate its activity
