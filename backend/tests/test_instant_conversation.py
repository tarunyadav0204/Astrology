import asyncio
import json
from types import SimpleNamespace
import pytest
from fastapi import HTTPException, WebSocketDisconnect
from chat_history.conversation_transport import serve_conversation


class Socket:
    def __init__(self, commands):
        self.commands = iter(commands)
        self.sent = []
        self.query_params = {}
        self.headers = {}
        self.accepted = False
        self.closed = None

    async def accept(self): self.accepted = True
    async def close(self, **kwargs): self.closed = kwargs
    async def send_json(self, payload): self.sent.append(payload)
    async def receive_json(self):
        try: return next(self.commands)
        except StopIteration: raise WebSocketDisconnect()


def test_conversation_keeps_authenticated_socket_for_followup_and_runs_work():
    socket = Socket([{'type': 'ask', 'request_id': 'one', 'request': {'client_request_id': 'one', 'question': 'When?'}},
                     {'type': 'ask', 'request_id': 'two', 'request': {'client_request_id': 'two', 'question': 'Next year'}}])
    work = []
    questions = []
    async def ask(request, background_tasks, current_user):
        assert current_user.userid == 42
        questions.append(request['question'])
        background_tasks.add_task(work.append, request['question'])
        return {'message_id': len(questions)}
    async def relay(turn_socket, mid):
        await turn_socket.accept()
        await turn_socket.send_json({'type': 'completed', 'message_id': mid})
        await turn_socket.close(code=1000)
    async def run():
        await serve_conversation(socket, authenticate=lambda _: SimpleNamespace(userid=42), token=lambda _: 'token', ask=ask, relay=relay)
        await asyncio.sleep(.05)
    asyncio.run(run())
    assert questions == ['When?', 'Next year']
    assert work == questions
    assert socket.closed is None
    assert [p['type'] for p in socket.sent] == ['conversation_ready', 'queued', 'completed', 'queued', 'completed']


def test_authentication_rejection_and_validation_errors():
    socket = Socket([])
    def reject(_): raise ValueError('bad token')
    asyncio.run(serve_conversation(socket, authenticate=reject, token=lambda _: '', ask=None, relay=None))
    assert not socket.accepted
    assert socket.closed['code'] == 4401
    socket = Socket([{'type':'ask', 'request':{}}, {'type':'ask', 'request_id':'x', 'request':{'client_request_id':'x'}}])
    async def ask(*args, **kwargs): raise HTTPException(409, detail={'code':'chart_mismatch'})
    asyncio.run(serve_conversation(socket, authenticate=lambda _: object(), token=lambda _: '', ask=ask, relay=None))
    assert socket.sent[1]['status'] == 400
    assert socket.sent[2]['status'] == 409
    assert socket.sent[2]['detail']['code'] == 'chart_mismatch'


@pytest.mark.parametrize('clarify', [True, False])
def test_instant_agent_uses_registry_progress_and_can_ask_user(monkeypatch, clarify):
    import openai
    from chat import verified_chat_pipeline as pipeline
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setattr(pipeline, '_historical_vimshottari_timeline', lambda _: {})
    monkeypatch.setattr(pipeline, '_calculate_requested_capabilities', lambda *args: {'parashari.shadbala': {'strength': 7}})
    sent = []
    traces = []
    def call(name, args):
        return SimpleNamespace(type='function_call', name=name, arguments=json.dumps(args), call_id=name)
    class Events:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        def __aiter__(self): return self
        async def __anext__(self): raise StopAsyncIteration
        async def get_final_response(self): return SimpleNamespace(output_text='An evidence-based answer.', usage=None)
    class Responses:
        async def create(self, **kwargs):
            sent.append(kwargs)
            count = len(sent)
            if count == 1: calls = [call('get_instant_baseline', {})]
            elif count == 2: calls = [call('get_deterministic_evidence', {'capability_id':'parashari.shadbala', 'parameters':None})]
            elif count == 3: calls = [call('report_calculation', {'source':'nadi.linkages', 'title':'Not calculated', 'summary':'Unsupported finding.'}), call('report_calculation', {'source':'parashari.shadbala', 'title':'Strength checked', 'summary':'The calculated strength is seven.'})]
            elif clarify: calls = [call('ask_user', {'question':'Which year are you considering?'})]
            else: calls = []
            return SimpleNamespace(id=str(count), output=calls, usage=None)
        def stream(self, **kwargs): sent.append(kwargs); return Events()
    monkeypatch.setattr(openai, 'AsyncOpenAI', lambda **kwargs: SimpleNamespace(responses=Responses()))
    result = asyncio.run(pipeline.run_verified_calculator_agent(question='What about my career?', language='english',
        birth_data={}, instant_context={}, history=[{'role':'user','content':'I want to change jobs'}],
        model_name='gpt-5.6-luna', timeout_s=60, conversation_mode=True, calculation_callback=traces.append))
    assert result['success']
    assert any(t and t[-1]['detail'] == 'The calculated strength is seven.' for t in traces)
    assert all(not any(row['title'] == 'Not calculated' for row in trace) for trace in traces)
    assert 'correct unsupported' in sent[0]['instructions']
    tool = next(t for t in sent[0]['tools'] if t['name'] == 'get_deterministic_evidence')
    assert 'parashari.shadbala' in tool['parameters']['properties']['capability_id']['enum']
    if clarify:
        assert result['message_type'] == 'clarification'
        assert result['skip_instant_credit_charge']
        assert result['response'] == 'Which year are you considering?'
    else:
        assert result['response'] == 'An evidence-based answer.'
        assert result['information_rounds']['type'] == 'instant'


def test_production_conversation_keeps_baseline_and_bypasses_legacy_composer(monkeypatch):
    from chat import instant_chat_pipeline as pipeline
    from chat import instant_conversation
    baseline = {'natal_snapshot': {'ascendant': 42}, 'normalized_evidence': {'career': {'facts': [1, 2]}}}
    monkeypatch.setattr(pipeline, '_build_instant_context', lambda **kwargs: baseline)
    def forbidden(*args, **kwargs): raise AssertionError('legacy composer must not constrain the agent')
    monkeypatch.setattr(pipeline, '_build_instant_prompt', forbidden)
    monkeypatch.setattr(pipeline, 'build_instant_v2_packet', forbidden)
    received = {}
    async def agent(**kwargs):
        received.update(kwargs)
        return {'success': True, 'response': 'Which field are you considering?'}
    monkeypatch.setattr(instant_conversation, 'generate_conversation_response', agent)
    result = asyncio.run(pipeline.generate_instant_chat_response(object(), question='How is my career?',
        birth_data={'name':'Test'}, intent={'category':'career','answer_mode':'topic_reading','target_subject_key':'self'},
        history=[{'question':'I want to change jobs','response':'What are you considering?'}], instant_conversation=True))
    assert result['success']
    assert received['instant_context'] is baseline
    assert received['history'][0]['question'] == 'I want to change jobs'


def test_agent_wrapper_preserves_token_accounting_when_optional_glossary_fails(monkeypatch):
    import time
    from chat import instant_conversation, verified_chat_pipeline
    from ai import term_matcher
    monkeypatch.setenv('INSTANT_CHAT_AGENT_MODEL', 'test-openai-model')
    async def agent(**kwargs):
        assert kwargs['conversation_mode']
        assert kwargs['model_name'] == 'test-openai-model'
        return {'success':True, 'response':'Which year?', 'message_type':'clarification',
                'skip_instant_credit_charge':True, 'prompt_chars':321,
                'token_usage':{'input_tokens':100,'output_tokens':20,'cached_tokens':30}}
    monkeypatch.setattr(verified_chat_pipeline, 'run_verified_calculator_agent', agent)
    def fail(*args, **kwargs): raise RuntimeError('optional glossary unavailable')
    monkeypatch.setattr(term_matcher, 'find_terms_in_text', fail)
    result = asyncio.run(instant_conversation.generate_conversation_response(
        stage_timings_ms={}, pipeline_started=time.perf_counter(), question='When?', language='english'))
    assert result['response'] == 'Which year?'
    assert result['timing']['route_action'] == 'clarify'
    assert result['skip_instant_credit_charge']
    stage = result['instant_llm_usage_stages'][0]
    assert stage['input_tokens'] == 100
    assert stage['output_tokens'] == 20
    assert stage['non_cached_input_tokens'] == 70
    assert result['terms'] == []
