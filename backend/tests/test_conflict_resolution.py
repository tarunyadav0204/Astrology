import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from chat import conflict_routes as routes
from chat.conflict_contract import MAX_ROUNDS, validate_turn, strict_schema, resolution_markdown
from chat.conflict_transport import ConflictModelConnection

@pytest.mark.parametrize('ids', [[], [1], [1,2,3], [1,1], [0,2]])
def test_exactly_two_distinct_owned_answer_ids_required(ids):
    with pytest.raises(ValidationError):
        routes.ConflictRequest(message_ids=ids, request_id='00000000-0000-4000-8000-000000000000')

def resolved():
    return dict(action='resolve', question=None, calculations=[], resolution=dict(verdict='contradiction',
        explanation='The claims differ.', claims=[dict(answer_id=id, claim='Claim', assessment='Reviewed') for id in [1,2]],
        evidence=[dict(answer_id=1, source='baseline', finding='Calculated evidence')], corrected_answer='**Corrected answer**', uncertainty=['Timing is uncertain']))

def test_shared_three_round_limit_also_counts_user_questions():
    question = dict(action='clarify', question='Which year?', calculations=[], resolution=None)
    calculation = dict(action='calculate', question=None, calculations=[dict(answer_id=1, capabilities=['parashari.shadbala'])], resolution=None)
    for round in range(MAX_ROUNDS):
        assert validate_turn(question if round % 2 == 0 else calculation, [1,2], round, {}).action in {'clarify', 'calculate'}
    for request in (question, calculation):
        with pytest.raises(ValueError, match='information rounds'):
            validate_turn(request, [1,2], MAX_ROUNDS, {})
    assert validate_turn(resolved(), [1,2], 3, {'1':['baseline']}).action == 'resolve'

@pytest.mark.parametrize('change', ['foreign_answer', 'unknown_calculator', 'missing_claim', 'uncalculated_evidence'])
def test_rejects_untrusted_or_inconsistent_model_contract(change):
    value = resolved()
    if change == 'foreign_answer': value['resolution']['claims'][0]['answer_id'] = 9
    if change == 'missing_claim': value['resolution']['claims'] = value['resolution']['claims'][:1]
    if change == 'uncalculated_evidence': value['resolution']['evidence'][0]['source'] = 'parashari.shadbala'
    if change == 'unknown_calculator': value = dict(action='calculate', question=None, resolution=None, calculations=[dict(answer_id=1, capabilities=['execute_arbitrary_code'])])
    with pytest.raises(ValueError): validate_turn(value, [1,2], 0, {'1':['baseline']})

def test_strict_schema_requires_every_property_and_disallows_extras():
    def visit(node):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                assert node['additionalProperties'] is False
                assert set(node['required']) == set(node['properties'])
            for value in node.values(): visit(value)
        elif isinstance(node, list):
            for item in node: visit(item)
    visit(strict_schema())

def test_resolution_leads_with_answer_and_hides_internal_references():
    result = validate_turn(resolved(), [1,2], 0, {'1':['baseline']}).resolution
    text = resolution_markdown(result, [dict(answer_id=1, question='Question one'), dict(answer_id=2, question='Question two')])
    assert '**Corrected answer**' in text
    assert text.startswith('## Your answer\n\n**Corrected answer**')
    assert 'Why the guidance differed' in text and 'Keep in mind' in text
    assert 'answer #1' not in text and 'answer #2' not in text
    assert 'Claim' not in text

@pytest.mark.parametrize('rows', [[], [(1,'answer','question','session',1,'career',None)]])
def test_missing_or_foreign_source_rejected(monkeypatch, rows):
    monkeypatch.setattr(routes, 'execute', lambda *args: SimpleNamespace(fetchall=lambda: rows))
    with pytest.raises(HTTPException) as error: routes.load_sources(None, [1,2], 10)
    assert error.value.status_code == 404

def test_cross_session_answers_keep_selection_order(monkeypatch):
    rows = [(1,'first','q1','session1',1,'career',None), (2,'second','q2','session2',2,'career',None)]
    monkeypatch.setattr(routes, 'execute', lambda *args: SimpleNamespace(fetchall=lambda: rows))
    sources = routes.load_sources(None, [2,1], 10)
    assert [s['answer_id'] for s in sources] == [2,1]
    assert [s['session_id'] for s in sources] == ['session2','session1']
    assert all(s['answer_id'] in [1,2] for s in sources)

def test_responses_websocket_uses_incremental_input_and_no_storage():
    async def scenario():
        model = ConflictModelConnection('gpt-5.6-luna')
        response = dict(id='response-one',status='completed',output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(resolved()))])])
        socket = SimpleNamespace(send=AsyncMock(), recv=AsyncMock(return_value=json.dumps(dict(type='response.completed',response=response))))
        model.socket = socket
        transcript = [dict(role='user',content='Initial context')]
        value, _ = await model.turn('instructions', transcript)
        assert value['action'] == 'resolve'
        first = json.loads(socket.send.call_args.args[0])
        assert first['store'] is False and first['type'] == 'response.create'
        transcript += [dict(role='assistant',content='Old output'),dict(role='user',content='New detail')]
        await model.turn('instructions',transcript)
        second = json.loads(socket.send.call_args.args[0])
        assert second['previous_response_id'] == 'response-one'
        assert second['input'] == [transcript[-1]]
    asyncio.run(scenario())

def test_incomplete_websocket_response_rejected():
    async def scenario():
        model = ConflictModelConnection('gpt-5.6-luna')
        model.socket = SimpleNamespace(send=AsyncMock(), recv=AsyncMock(return_value=json.dumps(dict(type='response.incomplete'))))
        with pytest.raises(RuntimeError): await model.turn('instructions', [])
    asyncio.run(scenario())

@pytest.fixture
def workflow(monkeypatch):
    import copy
    import sys
    from contextlib import contextmanager
    from collections import deque
    state = dict(phase='ready', rounds=0, revision=0, sources=[dict(answer_id=id, question=f'q{id}', session_id='session', answered_at='now') for id in [1,2]], concern='', language='english', model='gpt-5.6-luna', events=[], transcript=[], contexts={}, available={}, usage=dict(input_tokens=0,output_tokens=0,cached_tokens=0))
    saved = {'state':copy.deepcopy(state), 'finals':0}
    monkeypatch.setitem(sys.modules, 'chat_history.routes', SimpleNamespace(_chat_stream_user=lambda token:SimpleNamespace(userid=10), _chat_stream_token=lambda socket:'token'))
    @contextmanager
    def connection(): yield SimpleNamespace(commit=lambda:None)
    monkeypatch.setattr(routes,'get_conn',connection)
    monkeypatch.setattr(routes,'execute',lambda *args:SimpleNamespace(fetchone=lambda:None))
    monkeypatch.setattr(routes,'load_run',lambda *args:copy.deepcopy(saved['state']))
    monkeypatch.setattr(routes,'claim_run',lambda *args:copy.deepcopy(saved['state']))
    def save(run,user,owner,value,release=False):
        value['revision']+=1
        saved['state']=copy.deepcopy(value)
    monkeypatch.setattr(routes,'save_state',save)
    def finish(run,user,owner,value,result):
        saved['finals']+=1
        value.update(phase='completed',resolution=result.model_dump(),question=None,content='Corrected answer',message_id=99)
        saved['state']=copy.deepcopy(value)
        return value
    monkeypatch.setattr(routes,'persist_resolution',finish)
    monkeypatch.setattr(routes,'build_initial_contexts',lambda *args:({'1':{}},[],{'1':['baseline'],'2':[]}))
    monkeypatch.setattr(routes,'calculate_requests',lambda requests,contexts:[dict(answer_id=1,source='parashari.shadbala',calculation={'strength':1})])
    outputs=deque()
    class Model:
        def __init__(self,model):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def turn(self,instructions,transcript):
            value=outputs.popleft()
            if isinstance(value,Exception): raise value
            return value,dict(output=[dict(type='message',role='assistant',content=[dict(type='output_text',text=json.dumps(value))])],usage=dict(input_tokens=5,output_tokens=2))
    monkeypatch.setattr(routes,'ConflictModelConnection',Model)
    class Socket:
        query_params={}
        headers={}
        def __init__(self,commands):self.commands=iter(commands);self.sent=[]
        async def accept(self):pass
        async def send_json(self,value):self.sent.append(copy.deepcopy(value))
        async def close(self,**kwargs):pass
        async def receive_json(self):
            try:command=next(self.commands)
            except StopIteration:raise routes.WebSocketDisconnect()
            return dict(revision=saved['state']['revision'],**command)
    return saved,outputs,Socket


def test_end_to_end_combined_rounds_save_one_final_answer(workflow):
    saved,outputs,Socket=workflow
    calculation=dict(action='calculate',question=None,resolution=None,calculations=[dict(answer_id=1,capabilities=['parashari.shadbala'])])
    question=dict(action='clarify',question='Which year?',resolution=None,calculations=[])
    outputs.extend([calculation,question,calculation,resolved()])
    socket=Socket([dict(type='start'),dict(type='reply',text='2026')])
    asyncio.run(routes.conflict_socket(socket,'run'))
    assert saved['state']['phase']=='completed'
    assert saved['state']['rounds']==3
    assert saved['state']['usage']['input_tokens']==20
    assert saved['finals']==1
    assert len([event for event in saved['state']['events'] if event['kind']=='question'])==1
    assert socket.sent[-1]['resolution']['verdict']=='contradiction'


def test_reconnect_resumes_pending_calculation_without_new_round(workflow,monkeypatch):
    saved,outputs,Socket=workflow
    calculation=dict(action='calculate',question=None,resolution=None,calculations=[dict(answer_id=1,capabilities=['parashari.shadbala'])])
    outputs.append(calculation)
    def disconnect(*args):raise routes.WebSocketDisconnect()
    monkeypatch.setattr(routes,'calculate_requests',disconnect)
    asyncio.run(routes.conflict_socket(Socket([dict(type='start')]),'run'))
    assert saved['state']['rounds']==1
    assert saved['state']['pending_calculations']
    monkeypatch.setattr(routes,'calculate_requests',lambda *args:[dict(answer_id=1,source='parashari.shadbala',calculation={})])
    outputs.append(resolved())
    asyncio.run(routes.conflict_socket(Socket([dict(type='start')]),'run'))
    assert saved['state']['phase']=='completed'
    assert saved['state']['rounds']==1
    assert 'pending_calculations' not in saved['state']
    assert saved['finals']==1


def test_disconnect_during_progress_preserves_round_budget(workflow):
    saved,outputs,Socket=workflow
    outputs.append(dict(action='calculate',question=None,resolution=None,calculations=[dict(answer_id=1,capabilities=['parashari.shadbala'])]))
    class DisconnectingSocket(Socket):
        async def send_json(self,value):
            if value.get('text','').startswith('Checking additional calculations'):
                raise routes.WebSocketDisconnect()
            await super().send_json(value)
    asyncio.run(routes.conflict_socket(DisconnectingSocket([dict(type='start')]),'run'))
    assert saved['state']['rounds']==1
    assert saved['state']['pending_calculations']


def test_initial_context_keeps_computed_timezone(monkeypatch):
    import sys
    from contextlib import contextmanager
    from chat import instant_chat_pipeline, verified_chat_pipeline
    @contextmanager
    def connection():yield None
    monkeypatch.setattr(routes,'get_conn',connection)
    monkeypatch.setattr(routes,'execute',lambda *args:SimpleNamespace(fetchone=lambda:('Test','1990-01-01','12:00',28.6,77.2,5.5,'Delhi'),fetchall=lambda:[]))
    class Birth:
        timezone=5.5
        def __init__(self,**kwargs):self.data=kwargs
        def model_dump(self):return self.data
    monkeypatch.setitem(sys.modules,'main',SimpleNamespace(BirthData=Birth))
    captured={}
    def build(birth,*args,**kwargs):captured.update(birth);return {'natal_snapshot':{'ascendant':1}}
    monkeypatch.setattr(instant_chat_pipeline,'_build_instant_context',build)
    monkeypatch.setattr(verified_chat_pipeline,'_historical_vimshottari_timeline',lambda *args:{})
    contexts,packets,available=routes.build_initial_contexts([dict(answer_id=1,chart_id=1,session_id='session',category='career',question='Question')],10)
    assert captured['timezone']==5.5
    assert contexts['1']['birth']['timezone']==5.5
    assert packets[0]['baseline']['natal_calculations']


def test_source_context_contains_only_previous_three_completed_answers(monkeypatch):
    rows=[(1,'first','q1','session1',1,'career',None),(2,'second','q2','session2',2,'career',None)]
    seen=[]
    def query(conn,sql,params):
        seen.append((sql,params))
        return SimpleNamespace(fetchall=lambda:rows if 'cm.message_id = ANY' in sql else [('Earlier answer','Earlier question','date')])
    monkeypatch.setattr(routes,'execute',query)
    sources=routes.load_sources(None,[1,2],10,include_history=True)
    assert all(s['recent_context'][0]['answer']=='Earlier answer' for s in sources)
    assert all('LIMIT 3' in sql and "cm.status='completed'" in sql for sql,params in seen[1:])
    assert [params for sql,params in seen[1:]]==[('session1',1),('session2',2)]


def test_final_resolution_ignores_stale_information_requests():
    value = resolved()
    value['question'] = 'Which year?'
    value['calculations'] = [dict(answer_id=1, capabilities=['parashari.shadbala'])]
    turn = validate_turn(value, [1, 2], 3, {'1': ['baseline']})
    assert turn.question is None
    assert turn.calculations == []
    assert turn.resolution.corrected_answer == '**Corrected answer**'

def test_final_resolution_still_rejects_invalid_evidence_with_stale_fields():
    value = resolved()
    value['question'] = 'Which year?'
    value['resolution']['evidence'][0]['source'] = 'invented'
    with pytest.raises(ValueError, match='unavailable calculation'):
        validate_turn(value, [1, 2], 3, {'1': ['baseline']})


def test_prompt_requests_plain_decisive_outcome_without_internal_language():
    prompt = routes.model_instructions(dict(language='english', rounds=0, available={}))
    assert "most likely" in prompt
    assert "Never mention answer IDs" in prompt
    assert "at most ONE short" in prompt
    assert "Do not manufacture precision" in prompt


def test_prompt_requires_grounded_astrological_explanation():
    prompt = routes.model_instructions(dict(language='english', rounds=0, available={}))
    assert 'Explain the astrological basis' in prompt
    assert 'active dasha (planetary period)' in prompt
    assert 'without a fixed target count' in prompt
    assert '2–4' not in prompt
    assert 'under 450 words' not in prompt
    assert 'never assume these factors are present' in prompt
    assert 'do not invent a rationale' in prompt

@pytest.mark.parametrize('params', [None, {'houses': [], 'start_date': '2027-01-01', 'end_date': '2028-01-01'}, {'houses': [13], 'start_date': '2027-01-01', 'end_date': '2028-01-01'}, {'houses': [10,10], 'start_date': '2027-01-01', 'end_date': '2028-01-01'}, {'houses': [10], 'start_date': '2028-01-01', 'end_date': '2027-01-01'}, {'houses': [10], 'start_date': 'not-a-date', 'end_date': '2028-01-01'}])
def test_double_transit_requires_valid_houses_and_dates(params):
    raw = dict(action='calculate', calculations=[dict(answer_id=1, capabilities=['parashari.double_transit'], double_transit=params)])
    with pytest.raises(ValueError):
        validate_turn(raw, [1,2], 0, {})


def test_double_transit_dispatches_exact_range_and_filters_houses(monkeypatch):
    from calculators.chart_calculator import ChartCalculator
    from charts import double_transit_service
    from datetime import datetime, timezone
    monkeypatch.setattr(ChartCalculator, 'calculate_chart', lambda *args, **kwargs: {'chart': True})
    calls = []
    def calculate(chart, start, end, **kwargs):
        calls.append((chart, start, end))
        return dict(windows=[dict(house=10, status='full'), dict(house=7, status='aspect_only')], range={'start': str(start), 'end': str(end)})
    monkeypatch.setattr(double_transit_service, 'calculate_double_transits', calculate)
    raw = dict(action='calculate', calculations=[dict(answer_id=1, capabilities=['parashari.double_transit'], double_transit=dict(houses=[10], start_date='2027-01-01', end_date='2028-01-01'))])
    turn = validate_turn(raw, [1,2], 0, {})
    # Durable payload is JSON-safe and resumes with the same parameters.
    json.dumps(turn.calculations[0].model_dump(mode='json'))
    results = routes.calculate_requests(turn.calculations, {'1': dict(birth={}, capabilities={}, instant={})})
    assert calls[0][1:] == (datetime(2027,1,1,tzinfo=timezone.utc), datetime(2028,1,1,tzinfo=timezone.utc))
    assert results[0]['calculation']['facts']['windows'] == [dict(house=10, status='full')]
    assert results[0]['calculation']['facts']['focus_houses'] == [10]
    prompt = routes.model_instructions(dict(language='english', rounds=0, available={}))
    assert 'parameters.houses' in prompt and 'end_date exclusive' in prompt
