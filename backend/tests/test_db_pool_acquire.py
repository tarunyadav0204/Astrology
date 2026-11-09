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


def test_pool_acquire_reuses_connection_returned_while_pool_growth_times_out(monkeypatch):
    from psycopg2 import OperationalError

    connection = object()

    class RecoveringPool:
        def __init__(self):
            self.calls = 0
            self._used = {1: object()}
            self._pool = []

        def getconn(self):
            self.calls += 1
            if self.calls == 1:
                self._pool.append(connection)
                raise OperationalError("connection timed out")
            return self._pool.pop()

    pool = RecoveringPool()
    assert db._acquire_from_pool(pool, dict_rows=False) is connection
    assert pool.calls == 2


def test_worker_can_wait_longer_without_changing_api_default(monkeypatch):
    class BusyPool:
        calls = 0
        def getconn(self):
            self.calls += 1
            if self.calls < 3:
                raise PoolError('connection pool exhausted')
            return 'connection'
    monkeypatch.setenv('DB_POOL_ACQUIRE_TIMEOUT_MS', '0')
    monkeypatch.setenv('DB_POOL_ACQUIRE_POLL_MS', '1')
    assert db._acquire_from_pool(BusyPool(), dict_rows=False, timeout=.1) == 'connection'
    with pytest.raises(PoolError):
        db._acquire_from_pool(BusyPool(), dict_rows=False)


def test_concurrent_initialization_creates_one_pool(monkeypatch):
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor
    import psycopg2.pool
    calls = []
    pool = object()
    def create(*args, **kwargs):
        calls.append(1)
        time.sleep(.01)
        return pool
    monkeypatch.setattr(db, '_POOLS', {})
    monkeypatch.setattr(db, '_postgres_dsn', lambda: 'test')
    monkeypatch.setattr(db, '_pool_enabled', lambda: True)
    monkeypatch.setattr(psycopg2.pool, 'ThreadedConnectionPool', create)
    barrier = threading.Barrier(8)
    def acquire(_):
        barrier.wait(timeout=3)
        return db._get_pool()
    with ThreadPoolExecutor(max_workers=8) as executor:
        assert all(result is pool for result in executor.map(acquire, range(8)))
    assert len(calls) == 1
