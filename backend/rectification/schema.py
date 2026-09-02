from __future__ import annotations

from db import execute


_RECTIFICATION_SCHEMA_READY = False


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS rectification_cases (
        id TEXT PRIMARY KEY,
        userid BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        birth_chart_id BIGINT NOT NULL REFERENCES birth_charts(id) ON DELETE CASCADE,
        chart_input_hash TEXT NOT NULL,
        window_start_seconds INTEGER NOT NULL CHECK (window_start_seconds >= 0),
        window_end_seconds INTEGER NOT NULL CHECK (window_end_seconds < 86400),
        status TEXT NOT NULL DEFAULT 'draft',
        active_run_id TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (window_start_seconds <= window_end_seconds)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rectification_events (
        id BIGSERIAL PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES rectification_cases(id) ON DELETE CASCADE,
        userid BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        subtype TEXT NOT NULL DEFAULT '',
        subject TEXT NOT NULL DEFAULT 'self',
        date_start DATE NOT NULL,
        date_end DATE NOT NULL,
        precision TEXT NOT NULL,
        source_reliability TEXT NOT NULL,
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (date_end >= date_start)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rectification_runs (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES rectification_cases(id) ON DELETE CASCADE,
        userid BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'pending',
        stage TEXT NOT NULL DEFAULT 'queued',
        progress_current INTEGER NOT NULL DEFAULT 0,
        progress_total INTEGER NOT NULL DEFAULT 0,
        minute_step INTEGER NOT NULL DEFAULT 1,
        input_hash TEXT NOT NULL,
        input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        engine_version TEXT NOT NULL,
        registry_version TEXT NOT NULL,
        result_json JSONB,
        error_text TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "ALTER TABLE rectification_runs ADD COLUMN IF NOT EXISTS input_json JSONB NOT NULL DEFAULT '{}'::jsonb",
    """
    CREATE TABLE IF NOT EXISTS rectification_result_clusters (
        id BIGSERIAL PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES rectification_runs(id) ON DELETE CASCADE,
        rank INTEGER NOT NULL,
        start_local_time TIME NOT NULL,
        end_local_time TIME NOT NULL,
        best_local_time TIME NOT NULL,
        relative_fit DOUBLE PRECISION NOT NULL,
        evidence_json JSONB NOT NULL,
        UNIQUE (run_id, rank)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_rectification_cases_user ON rectification_cases(userid, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_rectification_events_case ON rectification_events(case_id, active, date_start)",
    "CREATE INDEX IF NOT EXISTS idx_rectification_runs_case ON rectification_runs(case_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_rectification_runs_input ON rectification_runs(case_id, input_hash, status)",
)


def ensure_rectification_schema(conn) -> None:
    global _RECTIFICATION_SCHEMA_READY
    if _RECTIFICATION_SCHEMA_READY:
        return
    for statement in SCHEMA_STATEMENTS:
        execute(conn, statement)
    conn.commit()
    _RECTIFICATION_SCHEMA_READY = True
