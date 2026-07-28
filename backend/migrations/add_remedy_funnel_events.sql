CREATE TABLE IF NOT EXISTS remedy_funnel_events (
    id BIGSERIAL PRIMARY KEY,
    userid INTEGER NOT NULL,
    message_id TEXT,
    event_name TEXT NOT NULL,
    platform TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_remedy_funnel_user_event_created
ON remedy_funnel_events (userid, event_name, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS ux_remedy_funnel_user_msg_event
ON remedy_funnel_events (userid, (COALESCE(message_id, '')), event_name);
