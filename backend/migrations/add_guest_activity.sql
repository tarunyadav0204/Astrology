-- Guest funnel metrics: distinct installs that used free guest features per calendar day (IST/ops).
-- Applied on backend startup via acquisition_schema.ensure_guest_activity_schema().

CREATE TABLE IF NOT EXISTS guest_activity (
    id BIGSERIAL PRIMARY KEY,
    installation_id UUID NOT NULL,
    event VARCHAR(64) NOT NULL,
    day DATE NOT NULL,
    platform VARCHAR(32) NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_guest_activity_day_event
    ON guest_activity (day DESC, event);

CREATE INDEX IF NOT EXISTS idx_guest_activity_installation_day
    ON guest_activity (installation_id, day DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_guest_activity_dedupe_day
    ON guest_activity (installation_id, event, day);
