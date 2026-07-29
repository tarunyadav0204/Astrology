CREATE TABLE IF NOT EXISTS prediction_manifestation_syntheses (
    cache_key TEXT PRIMARY KEY,
    locale TEXT NOT NULL DEFAULT 'en',
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_json JSONB NOT NULL,
    output_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prediction_manifestation_syntheses_updated
    ON prediction_manifestation_syntheses (updated_at);
