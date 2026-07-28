-- Account-level cadence for automatic homepage prompts.
-- Idempotent PostgreSQL migration.

CREATE TABLE IF NOT EXISTS homepage_prompt_exposures (
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    prompt_key TEXT NOT NULL CHECK (
        prompt_key IN ('first_free_question', 'monthly_events')
    ),
    first_shown_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_shown_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    shown_count INTEGER NOT NULL DEFAULT 1,
    last_session_id TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (userid, prompt_key)
);

CREATE INDEX IF NOT EXISTS idx_homepage_prompt_exposures_user_last
    ON homepage_prompt_exposures(userid, last_shown_at DESC);
