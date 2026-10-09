import asyncio
from contextlib import contextmanager
from types import SimpleNamespace
from user_facts import routes


def test_search_is_owned_ranked_and_paginated(monkeypatch):
    calls = []
    class Cursor:
        def fetchone(self): return (123,)
        def fetchall(self): return [(8, 'education', 'Studying abroad', 1, '2026-10-09')]
    @contextmanager
    def connection(): yield object()
    def execute(conn, query, params): calls.append((query, params)); return Cursor()
    owned = []
    monkeypatch.setattr(routes, 'verify_chart_ownership', lambda chart, user: owned.append((chart, user)))
    monkeypatch.setattr(routes, 'get_db_connection', connection)
    monkeypatch.setattr(routes, 'execute', execute)
    result = asyncio.run(routes.get_facts(17, SimpleNamespace(userid=42), 'studying abroad', 2, 50))
    assert owned == [(17, 42)]
    query, params = calls[-1]
    assert 'websearch_to_tsquery' in query and 'ts_rank' in query
    assert 'birth_chart_id = %s' in query
    assert params == (17, 'studying abroad', 'studying abroad', 'studying abroad', 'studying abroad', 50, 50)
    assert result['total'] == 123 and result['has_more']


def test_empty_search_returns_page_without_full_text_predicate(monkeypatch):
    calls = []
    class Cursor:
        def fetchone(self): return (0,)
        def fetchall(self): return []
    @contextmanager
    def connection(): yield object()
    monkeypatch.setattr(routes, 'verify_chart_ownership', lambda *args: None)
    monkeypatch.setattr(routes, 'get_db_connection', connection)
    monkeypatch.setattr(routes, 'execute', lambda conn, query, params: (calls.append((query, params)) or Cursor()))
    result = asyncio.run(routes.get_facts(17, SimpleNamespace(userid=42), '', 1, 50))
    assert 'websearch_to_tsquery' not in calls[-1][0]
    assert result['facts'] == [] and not result['has_more']
