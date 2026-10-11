import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from chat_history import admin_routes as routes


def test_tools_require_admin():
    with pytest.raises(HTTPException) as error:
        routes.require_admin(SimpleNamespace(role='user'))
    assert error.value.status_code == 403
    endpoint = next(r for r in routes.router.routes if r.path == '/admin/chat/tool-activity')
    assert any(d.call is routes.require_admin for d in endpoint.dependant.dependencies)


def test_cost_counts_cached_input_separately():
    cost = routes._chat_tool_cost({'model':'gpt-5.6-luna','usage':{'input_tokens':1000,'cached_tokens':400,'output_tokens':200}},93)
    assert cost['cost_usd'] == pytest.approx(0.000368)
    assert cost['cost_inr'] == pytest.approx(0.034224)
    assert cost['cost_basis'] == 'measured_tokens_estimate'


def test_cache_hit_has_no_new_provider_charge():
    assert routes._chat_tool_cost({'cached':True},93)['cost_usd'] == 0
    assert routes._chat_tool_cost({'legacy':True},93)['cost_usd'] is None
    assert routes._chat_tool_cost({'model':'unregistered-model','usage':{'input_tokens':1000}},93)['cost_usd'] is None


def test_item_preserves_source_messages_user_and_failure():
    state = {'model':'gpt-5.6-luna','phase':'running','last_error':{'type':'ValueError'},'usage':{'input_tokens':2,'output_tokens':1,'cached_tokens':0},'sources':[{'answer_id':8,'question':'Question','answer':'Answer','session_id':'source-session'}]}
    row = ('run1',42,'session1','conflict_resolution',state,datetime.now(timezone.utc),datetime.now(timezone.utc),'Example user')
    item = routes._chat_tool_item(row,93)
    assert item['user_id'] == 42 and item['user_name'] == 'Example user'
    assert item['status'] == 'failed' and item['error_type'] == 'ValueError'
    assert item['sources'][0]['answer_id'] == 8 and item['sources'][0]['answer'] == 'Answer'
    state['phase'] = 'completed'
    assert routes._chat_tool_item(row,93)['status'] == 'completed'


def test_activity_filters_and_pagination_are_parameterized(monkeypatch):
    queries=[]
    class Cursor:
        def __init__(self, query): self.query=query
        def fetchone(self): return (None,) if 'to_regclass' in self.query else (1,)
        def fetchall(self): return [('run1',42,'session1','summary',{'phase':'completed','sources':[],'cached':True},None,None,'Name')]
    @contextmanager
    def connection(): yield SimpleNamespace(commit=lambda:None)
    monkeypatch.setattr(routes,'get_conn',connection)
    def execute(conn,query,params): queries.append((query,params)); return Cursor(query)
    monkeypatch.setattr(routes,'execute',execute)
    from chat import tool_activity, conflict_routes
    monkeypatch.setattr(tool_activity,'execute',execute)
    monkeypatch.setattr(conflict_routes,'execute',execute)
    result = asyncio.run(routes.get_admin_chat_tool_activity(page=2,limit=30,tool='summary',user_id=42,user_name="name' OR TRUE --",start_date='2026-10-01',end_date='2026-10-11',current_user=SimpleNamespace(role='admin')))
    query,params=queries[-1]
    assert "name' OR TRUE --" not in query
    assert params[-2:] == (30,30) and 42 in params
    assert 'a.tool=%s' in query and 'u.name' in query
    assert 'chat_conflict_resolutions' in query and 'chat_tool_activity' in query
    assert result['items'][0]['cost_usd'] == 0


def test_invalid_calendar_date_is_rejected_before_query():
    with pytest.raises(HTTPException) as error:
        asyncio.run(routes.get_admin_chat_tool_activity(page=1,limit=30,tool=None,user_id=None,user_name=None,start_date='2026-02-31',end_date=None,current_user=SimpleNamespace(role='admin')))
    assert error.value.status_code == 422
