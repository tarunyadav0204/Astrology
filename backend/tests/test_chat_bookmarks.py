import asyncio
from contextlib import contextmanager
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from chat import bookmark_routes as routes

class Cursor:
    def __init__(self, row=None, rows=None): self.row, self.rows = row, rows or []
    def fetchone(self): return self.row
    def fetchall(self): return self.rows

@pytest.fixture
def db(monkeypatch):
    queries = []
    @contextmanager
    def connection(): yield SimpleNamespace(commit=lambda: None)
    def execute(conn, query, params):
        queries.append((query, params))
        return Cursor(row=(1,) if 'SELECT cm.message_id' in query else None)
    monkeypatch.setattr(routes, 'EncryptionManager', lambda: SimpleNamespace(decrypt=lambda value: 'Amber'))
    monkeypatch.setattr(routes, 'get_conn', connection)
    monkeypatch.setattr(routes, 'execute', execute)
    return queries

def test_save_checks_owned_completed_answer_and_is_idempotent(db):
    assert asyncio.run(routes.save_answer(8, SimpleNamespace(userid=42))) == {'saved': True}
    ownership = next((q,p) for q,p in db if 'SELECT cm.message_id' in q)
    assert ownership[1] == (8, 42)
    assert "cs.user_id = %s" in ownership[0]
    assert "cm.sender = 'assistant'" in ownership[0]
    assert "cm.status" in ownership[0]
    assert any('ON CONFLICT DO NOTHING' in q and p == (42,8) for q,p in db)

def test_cannot_save_unowned_answer(monkeypatch, db):
    monkeypatch.setattr(routes, 'execute', lambda *args: Cursor())
    with pytest.raises(HTTPException) as error:
        asyncio.run(routes.save_answer(8, SimpleNamespace(userid=42)))
    assert error.value.status_code == 404

def test_remove_is_scoped_to_user(db):
    asyncio.run(routes.remove_answer(8, SimpleNamespace(userid=42)))
    assert any('WHERE user_id = %s AND message_id = %s' in q and p == (42,8) for q,p in db)

def test_search_is_scoped_parameterized_and_paginated(db):
    result = asyncio.run(routes.list_bookmarks("September%", 2, 10, SimpleNamespace(userid=42)))
    query, params = next((q,p) for q,p in db if 'ORDER BY b.saved_at' in q)
    assert 'b.user_id = %s' in query
    assert params == (42,)
    assert result == {'answers': [], 'has_more': False}


def test_decrypts_name_and_searches_it_before_pagination(monkeypatch, db):
    rows = [(8, 'Answer', '2026-10-08', 'Question', 'gAAAAencrypted', 'session-8')]
    monkeypatch.setattr(routes, 'execute', lambda conn, query, params: Cursor(rows=rows if 'ORDER BY b.saved_at' in query else []))
    result = asyncio.run(routes.list_bookmarks('Amber', 1, 10, SimpleNamespace(userid=42)))
    assert result['answers'][0]['name'] == 'Amber'
    assert result['answers'][0]['session_id'] == 'session-8'
    assert 'gAAAA' not in str(result)


def test_never_returns_ciphertext_on_decryption_failure(monkeypatch, db):
    def fail(value): raise ValueError('invalid record')
    monkeypatch.setattr(routes, 'EncryptionManager', lambda: SimpleNamespace(decrypt=fail))
    monkeypatch.setattr(routes, 'execute', lambda conn, query, params: Cursor(rows=[(8, 'Answer', '2026-10-08', 'Question', 'gAAAAencrypted', 'session-8')] if 'ORDER BY b.saved_at' in query else []))
    result = asyncio.run(routes.list_bookmarks('', 1, 10, SimpleNamespace(userid=42)))
    assert result['answers'][0]['name'] == ''
