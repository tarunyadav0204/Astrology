"""Pace reel TTS across API processes/jobs sharing the database."""
import os
import threading
import time
from contextlib import contextmanager

from db import execute, _new_connection

_ready = False
_schema_lock = threading.Lock()
_connection_lock = threading.Lock()
_KEY = 'reel_google_tts'


@contextmanager
def _pacing_connection():
    """One short-lived, non-pooled connection per process at most.

    Pacing must not compete with API requests and the parallel image cost ledger
    for the application's small pool. Close before sleeping or calling Google.
    The row lock still coordinates separate processes/instances in Postgres.
    """
    with _connection_lock:
        conn = _new_connection()
        try:
            yield conn
        finally:
            # close rolls back any unfinished transaction, including row locks.
            conn.close()


def _ensure_schema():
    global _ready
    with _schema_lock:
        if _ready:
            return
        with _pacing_connection() as conn:
            execute(conn, "SELECT pg_advisory_xact_lock(731924618)")
            execute(conn, '''CREATE TABLE IF NOT EXISTS reel_provider_pacing (
                provider TEXT PRIMARY KEY, next_allowed_at TIMESTAMPTZ NOT NULL)''')
            execute(conn, '''INSERT INTO reel_provider_pacing VALUES (%s, CURRENT_TIMESTAMP)
                ON CONFLICT(provider) DO NOTHING''', (_KEY,))
            conn.commit()
        _ready = True


def wait_for_tts_slot():
    _ensure_schema()
    interval = 60.0 / max(1, int(os.getenv('REEL_TTS_REQUESTS_PER_MINUTE', '60')))
    while True:
        with _pacing_connection() as conn:
            # Lock the one shared row only while scheduling, never during RPC/sleep.
            row = execute(conn, '''SELECT EXTRACT(EPOCH FROM
                (next_allowed_at - clock_timestamp())) FROM reel_provider_pacing
                WHERE provider=%s FOR UPDATE''', (_KEY,)).fetchone()
            delay = max(0.0, float(row[0]))
            if delay == 0:
                execute(conn, '''UPDATE reel_provider_pacing SET next_allowed_at=
                    clock_timestamp() + %s * interval '1 second' WHERE provider=%s''', (interval, _KEY))
            conn.commit()
        if delay == 0:
            return
        time.sleep(min(delay, 30.0))


def cool_down_tts(seconds):
    _ensure_schema()
    with _pacing_connection() as conn:
        execute(conn, '''UPDATE reel_provider_pacing SET next_allowed_at=GREATEST(
            next_allowed_at, clock_timestamp() + %s * interval '1 second')
            WHERE provider=%s''', (seconds, _KEY))
        conn.commit()
