-- Durable provider-ready notification work. This migration is applied to the
-- dedicated notification database, not the AstroRoshni application primary.
CREATE TABLE IF NOT EXISTS nudge_campaign_recipients (
    id BIGSERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL,
    userid INTEGER NOT NULL,
    delivery_group_id TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    question TEXT,
    policy TEXT NOT NULL,
    channels_json TEXT NOT NULL,
    endpoints_json TEXT NOT NULL DEFAULT '{}',
    data_json TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL DEFAULT 'ready',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    available_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    claimed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id, userid),
    UNIQUE(delivery_group_id)
);

CREATE INDEX IF NOT EXISTS idx_nudge_campaign_recipients_ready
    ON nudge_campaign_recipients(campaign_id, state, available_at);

CREATE TABLE IF NOT EXISTS nudge_dead_letters (
    id BIGSERIAL PRIMARY KEY,
    recipient_id BIGINT,
    campaign_id INTEGER,
    userid INTEGER,
    channel TEXT,
    payload_json TEXT,
    error TEXT NOT NULL,
    attempt_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_nudge_dead_letters_open
    ON nudge_dead_letters(created_at DESC)
    WHERE resolved_at IS NULL;
