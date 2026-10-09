CREATE TABLE IF NOT EXISTS chat_conflict_resolutions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    session_id TEXT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    state JSONB NOT NULL,
    claim_owner TEXT,
    claimed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, request_id)
);
CREATE INDEX IF NOT EXISTS idx_chat_conflict_resolutions_user_updated
    ON chat_conflict_resolutions(user_id, updated_at DESC);
