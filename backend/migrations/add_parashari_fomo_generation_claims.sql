-- Short-lived distributed leases prevent duplicate deterministic FOMO
-- calculations across API workers and VM instances.

CREATE TABLE IF NOT EXISTS parashari_prediction_generation_claims (
    cache_key TEXT PRIMARY KEY,
    owner_token TEXT NOT NULL,
    lease_until TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parashari_generation_claims_lease
    ON parashari_prediction_generation_claims(lease_until);
