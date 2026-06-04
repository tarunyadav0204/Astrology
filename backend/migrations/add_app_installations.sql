-- Mobile acquisition funnel: anonymous first-open rows, optional UTM/referrer, link to users.userid after auth.
-- Applied automatically on backend startup (idempotent) via acquisition_schema.ensure_app_installations_schema().
-- You may still run this file manually against Postgres (psql, Cloud SQL console) if needed.

CREATE TABLE IF NOT EXISTS app_installations (
    installation_id UUID PRIMARY KEY,
    platform VARCHAR(32) NOT NULL DEFAULT 'unknown',
    app_version VARCHAR(64),
    app_build VARCHAR(64),
    referrer_raw TEXT,
    utm_source VARCHAR(512),
    utm_medium VARCHAR(512),
    utm_campaign VARCHAR(512),
    client_install_key VARCHAR(128),
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

ALTER TABLE app_installations
    ADD COLUMN IF NOT EXISTS client_install_key VARCHAR(128);

ALTER TABLE app_installations
    ADD COLUMN IF NOT EXISTS app_build VARCHAR(64);

CREATE UNIQUE INDEX IF NOT EXISTS idx_app_installations_client_install_key
    ON app_installations (client_install_key)
    WHERE client_install_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS app_installation_events (
    id BIGSERIAL PRIMARY KEY,
    installation_id UUID REFERENCES app_installations (installation_id) ON DELETE CASCADE,
    event_name VARCHAR(120) NOT NULL,
    event_status VARCHAR(32),
    screen_name VARCHAR(120),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_installation_events_installation_created
    ON app_installation_events (installation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_app_installation_events_name_created
    ON app_installation_events (event_name, created_at DESC);
