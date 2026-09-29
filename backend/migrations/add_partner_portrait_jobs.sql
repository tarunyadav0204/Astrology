CREATE TABLE IF NOT EXISTS partner_portrait_jobs (
    job_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    birth_chart_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    request_json TEXT NOT NULL,
    profile_json TEXT,
    assets_json TEXT,
    error_message TEXT,
    credit_cost INTEGER NOT NULL,
    charged_at TIMESTAMP,
    refunded_at TIMESTAMP,
    idempotency_key TEXT NOT NULL,
    ruleset_version TEXT NOT NULL DEFAULT 'bphs-partner-portrait/1.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(user_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_partner_portrait_user_created
ON partner_portrait_jobs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_partner_portrait_chart
ON partner_portrait_jobs(user_id, birth_chart_id);
