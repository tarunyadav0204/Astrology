-- Mobile acquisition funnel: anonymous first-open rows, optional UTM/referrer, link to users.userid after auth.
-- Applied automatically on backend startup (idempotent) via acquisition_schema.ensure_app_installations_schema().
-- You may still run this file manually against Postgres (psql, Cloud SQL console) if needed.

CREATE TABLE IF NOT EXISTS app_installations (
    installation_id UUID PRIMARY KEY,
    platform VARCHAR(32) NOT NULL DEFAULT 'unknown',
    app_version VARCHAR(64),
    referrer_raw TEXT,
    utm_source VARCHAR(512),
    utm_medium VARCHAR(512),
    utm_campaign VARCHAR(512),
    first_open_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_open_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    open_count INTEGER NOT NULL DEFAULT 1,
    userid INTEGER REFERENCES users (userid) ON DELETE SET NULL,
    registered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_app_installations_first_open_at
    ON app_installations (first_open_at DESC);

CREATE INDEX IF NOT EXISTS idx_app_installations_userid
    ON app_installations (userid)
    WHERE userid IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_app_installations_utm_campaign
    ON app_installations (utm_campaign);
