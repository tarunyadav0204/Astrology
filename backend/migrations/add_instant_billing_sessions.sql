-- Server-authoritative minute billing for Instant Chat.
CREATE TABLE IF NOT EXISTS instant_billing_sessions (
    session_id TEXT PRIMARY KEY,
    userid INTEGER NOT NULL,
    chat_session_id TEXT NOT NULL,
    client_instance_id TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active',
    per_minute_cost INTEGER NOT NULL,
    original_per_minute_cost INTEGER NOT NULL,
    discount_percent INTEGER NOT NULL DEFAULT 0,
    starting_balance INTEGER NOT NULL,
    charged_credits INTEGER NOT NULL DEFAULT 0,
    billed_minutes INTEGER NOT NULL DEFAULT 0,
    billable_seconds INTEGER NOT NULL DEFAULT 0,
    last_heartbeat_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_instant_billing_user_started
    ON instant_billing_sessions(userid, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_instant_billing_chat_session
    ON instant_billing_sessions(chat_session_id, started_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_instant_billing_one_active_user
    ON instant_billing_sessions(userid)
    WHERE status = 'active';

INSERT INTO credit_settings (setting_key, setting_value, description)
VALUES ('instant_chat_per_minute_cost', 1, 'Credits per minute for Instant Chat')
ON CONFLICT (setting_key) DO NOTHING;
