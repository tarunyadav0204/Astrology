-- Run against the isolated notification database, not the application primary.
CREATE TABLE IF NOT EXISTS credit_campaign_whatsapp_jobs (
    job_id TEXT PRIMARY KEY,
    credit_campaign_id BIGINT NOT NULL,
    campaign_json TEXT NOT NULL,
    template_name TEXT NOT NULL,
    template_language TEXT NOT NULL,
    template_json TEXT NOT NULL,
    phone_number_id TEXT NOT NULL,
    include_unlinked BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'queued',
    total INTEGER NOT NULL DEFAULT 0,
    accepted INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    skipped INTEGER NOT NULL DEFAULT 0,
    enqueued_batches INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credit_campaign_whatsapp_recipients (
    job_id TEXT NOT NULL REFERENCES credit_campaign_whatsapp_jobs(job_id) ON DELETE CASCADE,
    userid INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'queued',
    recipient_status TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    claimed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id, userid)
);

CREATE INDEX IF NOT EXISTS idx_credit_campaign_wa_jobs_campaign
ON credit_campaign_whatsapp_jobs (credit_campaign_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_campaign_wa_jobs_one_active
ON credit_campaign_whatsapp_jobs (credit_campaign_id)
WHERE status IN ('queued', 'running');

CREATE INDEX IF NOT EXISTS idx_credit_campaign_wa_recipients_work
ON credit_campaign_whatsapp_recipients (job_id, state, claimed_at);
