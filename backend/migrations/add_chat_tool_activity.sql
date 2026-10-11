-- Source snapshots and measured usage for selected-answer summaries.
-- Conflict resolution already retains these fields in chat_conflict_resolutions.state.
CREATE TABLE IF NOT EXISTS chat_tool_activity (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    session_id TEXT REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    tool TEXT NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS chat_tool_activity_user_created_idx ON chat_tool_activity(user_id, created_at DESC);
