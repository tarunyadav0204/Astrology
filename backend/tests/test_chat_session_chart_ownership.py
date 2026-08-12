import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from chat.fact_extractor import FactExtractor
from chat import fact_extractor as fact_extractor_module
from chat_history import routes


class _Cursor:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True


def _install_db(monkeypatch, *, owned_chart):
    conn = _Connection()
    statements = []

    @contextmanager
    def fake_get_conn():
        yield conn

    def fake_execute(_conn, sql, params=None):
        normalized = " ".join(sql.split())
        statements.append((normalized, params))
        if normalized.startswith("SELECT id FROM birth_charts"):
            return _Cursor((params[0],) if owned_chart else None)
        return _Cursor()

    monkeypatch.setattr(routes, "get_conn", fake_get_conn)
    monkeypatch.setattr(routes, "execute", fake_execute)
    return conn, statements


def test_create_session_accepts_chart_owned_by_authenticated_user(monkeypatch):
    conn, statements = _install_db(monkeypatch, owned_chart=True)

    result = asyncio.run(
        routes.create_chat_session(
            {"birth_chart_id": "17"},
            current_user=SimpleNamespace(userid=42),
        )
    )

    assert result["session_id"]
    assert conn.committed is True
    assert (
        "SELECT id FROM birth_charts WHERE id = %s AND userid = %s",
        (17, 42),
    ) in statements
    assert any(
        sql.startswith("INSERT INTO chat_sessions") and params[2] == 17
        for sql, params in statements
    )


def test_create_session_rejects_foreign_or_missing_chart_without_inserting(monkeypatch):
    conn, statements = _install_db(monkeypatch, owned_chart=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            routes.create_chat_session(
                {"birth_chart_id": 17},
                current_user=SimpleNamespace(userid=42),
            )
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Birth chart not found"
    assert conn.committed is False
    assert not any(sql.startswith("INSERT INTO chat_sessions") for sql, _ in statements)


@pytest.mark.parametrize("value", [True, 0, -2, 1.5, "1.5", "abc"])
def test_create_session_rejects_invalid_chart_ids(monkeypatch, value):
    _conn, statements = _install_db(monkeypatch, owned_chart=True)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            routes.create_chat_session(
                {"birth_chart_id": value},
                current_user=SimpleNamespace(userid=42),
            )
        )

    assert exc_info.value.status_code == 422
    assert statements == []


def test_create_session_still_allows_an_unbound_session(monkeypatch):
    conn, statements = _install_db(monkeypatch, owned_chart=False)

    result = asyncio.run(
        routes.create_chat_session({}, current_user=SimpleNamespace(userid=42))
    )

    assert result["session_id"]
    assert conn.committed is True
    assert not any(sql.startswith("SELECT id FROM birth_charts") for sql, _ in statements)
    assert any(
        sql.startswith("INSERT INTO chat_sessions") and params[2] is None
        for sql, params in statements
    )


def test_fact_lookup_is_scoped_to_chart_owner(monkeypatch):
    statements = []

    @contextmanager
    def fake_get_conn():
        yield object()

    def fake_execute(_conn, sql, params=None):
        statements.append((" ".join(sql.split()), params))
        return SimpleNamespace(fetchall=lambda: [])

    monkeypatch.setattr(fact_extractor_module, "get_conn", fake_get_conn)
    monkeypatch.setattr(fact_extractor_module, "execute", fake_execute)

    assert FactExtractor().get_facts(17, 42) == {}
    sql, params = statements[0]
    assert "INNER JOIN birth_charts AS bc" in sql
    assert "bc.userid = %s" in sql
    assert params == (42, 17)
