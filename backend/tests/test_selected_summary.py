import asyncio
from contextlib import contextmanager
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from chat import summary_routes as routes

@pytest.mark.parametrize('ids', [[], [1,2,3,4], [1,1], [-1]])
def test_summary_rejects_invalid_selection(ids):
    with pytest.raises(ValidationError): routes.SummaryRequest(message_ids=ids)

@pytest.fixture
def database(monkeypatch):
    monkeypatch.setattr(routes, 'get_chat_summary_model', lambda: 'selected-summary-model')
    queries=[]
    class Cursor:
        def fetchall(self): return [(8, 'Answer', 'Question', 'session1')]
        def fetchone(self): return ('Cached summary',)
    @contextmanager
    def conn(): yield SimpleNamespace(commit=lambda: None)
    def execute(connection, query, params): queries.append((query,params)); return Cursor()
    monkeypatch.setattr(routes, 'get_conn', conn)
    monkeypatch.setattr(routes, 'execute', execute)
    from chat import tool_activity
    monkeypatch.setattr(tool_activity, 'execute', lambda conn, query, params: routes.execute(conn, query, params))
    return queries

def test_cached_selection_does_not_require_api_key(monkeypatch, database):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    result=asyncio.run(routes.summarize_answers(routes.SummaryRequest(message_ids=[8]), SimpleNamespace(userid=42)))
    assert result == {'summary':'Cached summary','count':1,'cached':True}
    import json
    audit = next(json.loads(params[0]) for query, params in database if 'UPDATE chat_tool_activity' in query)
    assert audit['cached'] is True and audit['usage']['input_tokens'] == 0
    assert audit['sources'][0]['answer_id'] == 8
    query,params=database[0]
    assert 'cs.user_id = %s' in query and params == ([8],42)
    assert any('pg_advisory_xact_lock' in query for query,params in database)

def test_unowned_or_unavailable_answers_rejected(database):
    with pytest.raises(HTTPException) as error:
        asyncio.run(routes.summarize_answers(routes.SummaryRequest(message_ids=[8,9]),SimpleNamespace(userid=42)))
    assert error.value.status_code == 404

def test_sources_remove_internal_metadata():
    assert routes.visible_text('<span>Important</span>\nNEXT_ACTION_META: {"x":1}') == 'Important'

def test_generation_is_bounded_and_cached(monkeypatch, database):
    import sys
    calls = []
    class Client:
        def __init__(self, **kwargs):
            assert kwargs['max_retries'] == 0
            self.responses = self
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_text='Short summary', status='completed', model='selected-summary-model', usage=SimpleNamespace(input_tokens=1000,output_tokens=200,input_tokens_details=SimpleNamespace(cached_tokens=400)))
    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(AsyncOpenAI=Client))
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder')
    class Cursor:
        def fetchall(self): return [(8, 'Answer', 'Question', 'session1')]
        def fetchone(self): return None
    monkeypatch.setattr(routes, 'execute', lambda conn, query, params: (database.append((query,params)) or Cursor()))
    result = asyncio.run(routes.summarize_answers(routes.SummaryRequest(message_ids=[8]), SimpleNamespace(userid=42)))
    assert result['summary'] == 'Short summary' and not result['cached']
    assert calls[0]['model'] == 'selected-summary-model'
    assert calls[0]['max_output_tokens'] == 1400 and calls[0]['store'] is False
    assert 'Question' in calls[0]['input'] and 'Answer' in calls[0]['input']
    assert any('INSERT INTO chat_selected_summaries' in query for query, params in database)
    import json
    audit = [json.loads(params[0]) for query, params in database if 'UPDATE chat_tool_activity' in query][-1]
    assert audit['usage'] == {'input_tokens':1000,'output_tokens':200,'cached_tokens':400}
    assert audit['model'] == 'selected-summary-model'
    assert audit['sources'][0]['answer_id'] == 8
    assert audit['sources'][0]['session_id'] == 'session1'
    assert audit['summary'] == 'Short summary' and audit['phase'] == 'completed'

def test_model_changes_use_distinct_summary_cache_keys(monkeypatch, database):
    monkeypatch.setattr(routes, 'get_chat_summary_model', lambda: 'model-a')
    asyncio.run(routes.summarize_answers(routes.SummaryRequest(message_ids=[8]), SimpleNamespace(userid=42)))
    first = next(params[1] for query, params in database if 'SELECT summary FROM' in query)
    database.clear()
    monkeypatch.setattr(routes, 'get_chat_summary_model', lambda: 'model-b')
    asyncio.run(routes.summarize_answers(routes.SummaryRequest(message_ids=[8]), SimpleNamespace(userid=42)))
    second = next(params[1] for query, params in database if 'SELECT summary FROM' in query)
    assert first != second


def test_failed_summary_is_visible_in_audit(monkeypatch, database):
    import sys, json
    class Client:
        def __init__(self, **kwargs): self.responses = self
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def create(self, **kwargs): raise RuntimeError('provider private details')
    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(AsyncOpenAI=Client))
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder')
    class Cursor:
        def fetchall(self): return [(8,'Answer','Question','session1')]
        def fetchone(self): return None
    monkeypatch.setattr(routes,'execute',lambda conn,query,params: (database.append((query,params)) or Cursor()))
    with pytest.raises(HTTPException) as error:
        asyncio.run(routes.summarize_answers(routes.SummaryRequest(message_ids=[8]),SimpleNamespace(userid=42)))
    assert error.value.status_code == 502
    state = next(json.loads(params[0]) for query,params in database if 'UPDATE chat_tool_activity' in query)
    assert state['phase'] == 'failed' and state['error_type'] == 'RuntimeError'
    assert state['usage'] is None
    assert 'provider private details' not in json.dumps(state)
