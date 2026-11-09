"""Serialize short reel DB transactions, never image/audio provider calls.

Shared by every rendering thread/job in this process. Other API work retains
its pool capacity and existing acquisition deadline. No transaction retries:
a failed commit must not duplicate ledger entries or purchases.
"""
import os
import threading
import time
from contextlib import contextmanager

from db import get_conn as pooled_connection

_gate = threading.Lock()


def _reset_gate():
    global _gate
    _gate = threading.Lock()


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(after_in_child=_reset_gate)


@contextmanager
def get_conn():
    timeout = max(1.0, float(os.getenv('REEL_DB_WAIT_SECONDS', '60')))
    deadline = time.monotonic() + timeout
    gate = _gate
    if not gate.acquire(timeout=timeout):
        raise TimeoutError('Reel database transaction queue timed out')
    try:
        with pooled_connection(acquire_timeout=max(0.0, deadline-time.monotonic())) as conn:
            yield conn
    finally:
        gate.release()
