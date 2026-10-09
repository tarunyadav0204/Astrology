CREATE TABLE IF NOT EXISTS chat_calculation_audits (
    message_id BIGINT PRIMARY KEY REFERENCES chat_messages(message_id) ON DELETE CASCADE,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
