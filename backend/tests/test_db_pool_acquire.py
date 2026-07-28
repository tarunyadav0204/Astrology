from __future__ import annotations

import pytest
from psycopg2.pool import PoolError

import db


def test_pool_acquire_waits_for_a_brief_transient_exhaustion(monkeypatch):
    connection = object()

    class FakePool:
        def __init__(self):
            self.calls = 0
            self._used = {1: object()}
            self._pool = []

        def getconn(self):
            self.calls += 1
            if self.calls < 3:
                raise PoolError("connection pool exhausted")
            return connection

    pool = FakePool()
    monkeypatch.setenv("DB_POOL_ACQUIRE_TIMEOUT_MS", "50")
    monkeypatch.setenv("DB_POOL_ACQUIRE_POLL_MS", "1")

    assert db._acquire_from_pool(pool, dict_rows=False) is connection
    assert pool.calls == 3


def test_pool_acquire_remains_bounded(monkeypatch, caplog):
    class ExhaustedPool:
        _used = {1: object(), 2: object(), 3: object(), 4: object()}
        _pool = []

        def getconn(self):
            raise PoolError("connection pool exhausted")

    monkeypatch.setenv("DB_POOL_ACQUIRE_TIMEOUT_MS", "0")

    with pytest.raises(PoolError):
        db._acquire_from_pool(ExhaustedPool(), dict_rows=False)

    assert "db_pool_acquire_timeout" in caplog.text
