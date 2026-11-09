from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import threading
import time

import pytest
from reel_studio import database


def test_transactions_serialize_but_provider_work_remains_parallel(monkeypatch):
    active = 0
    maximum = 0
    barrier = threading.Barrier(12)
    @contextmanager
    def connection(**kwargs):
        nonlocal active, maximum
        assert kwargs['acquire_timeout'] > 0
        active += 1
        maximum = max(maximum, active)
        try:
            time.sleep(.005)
            yield object()
        finally:
            active -= 1
    monkeypatch.setattr(database, 'pooled_connection', connection)
    def generate(_):
        with database.get_conn():
            pass  # pre-request ledger write
        barrier.wait(timeout=5)  # all 12 provider requests can run concurrently
        with database.get_conn():
            pass  # post-request ledger write
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(generate, range(12)))
    assert maximum == 1
    assert active == 0


def test_gate_released_after_acquisition_and_transaction_failures(monkeypatch):
    @contextmanager
    def unavailable(**kwargs):
        raise RuntimeError('database unavailable')
        yield
    monkeypatch.setattr(database, 'pooled_connection', unavailable)
    with pytest.raises(RuntimeError):
        with database.get_conn():
            pass
    @contextmanager
    def available(**kwargs):
        yield object()
    monkeypatch.setattr(database, 'pooled_connection', available)
    with pytest.raises(ValueError):
        with database.get_conn():
            raise ValueError('write failed')
    with database.get_conn() as conn:
        assert conn is not None
