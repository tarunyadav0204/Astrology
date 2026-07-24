CREATE TABLE IF NOT EXISTS payment_failure_alerts (
    id BIGSERIAL PRIMARY KEY,
    dedupe_key TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    stage TEXT NOT NULL,
    userid INTEGER,
    reference_id TEXT,
    email_sent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email_attempted_at TIMESTAMP
);

ALTER TABLE payment_failure_alerts
    ADD COLUMN IF NOT EXISTS userid INTEGER;

CREATE INDEX IF NOT EXISTS idx_payment_failure_alerts_created_at
    ON payment_failure_alerts (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_payment_failure_alerts_user_created
    ON payment_failure_alerts (userid, created_at DESC);
