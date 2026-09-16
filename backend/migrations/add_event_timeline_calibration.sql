CREATE TABLE IF NOT EXISTS event_timeline_forecasts (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES event_timeline_jobs(job_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    birth_chart_id BIGINT NOT NULL REFERENCES birth_charts(id) ON DELETE CASCADE,
    candidate_id TEXT NOT NULL,
    target_year INTEGER NOT NULL,
    target_month INTEGER NOT NULL,
    display_rank INTEGER NOT NULL,
    event_key TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    methodology_version TEXT,
    evidence_version TEXT,
    accuracy_layer TEXT,
    support_grade TEXT,
    manifestation_phase TEXT,
    forecast_start DATE,
    forecast_end DATE,
    prediction_hash TEXT NOT NULL,
    forecast_json JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, candidate_id, target_month)
);

CREATE TABLE IF NOT EXISTS event_timeline_outcomes (
    id BIGSERIAL PRIMARY KEY,
    forecast_id BIGINT NOT NULL UNIQUE REFERENCES event_timeline_forecasts(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    occurrence TEXT NOT NULL CHECK (occurrence IN ('occurred', 'partly_occurred', 'did_not_occur')),
    actual_date DATE,
    severity INTEGER CHECK (severity IS NULL OR severity BETWEEN 1 AND 5),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_timeline_unpredicted_events (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES event_timeline_jobs(job_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    event_key TEXT NOT NULL,
    actual_date DATE NOT NULL,
    severity INTEGER CHECK (severity IS NULL OR severity BETWEEN 1 AND 5),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, user_id, event_key, actual_date)
);

CREATE INDEX IF NOT EXISTS idx_timeline_forecasts_calibration
ON event_timeline_forecasts(engine_version, accuracy_layer, event_key, target_year);

CREATE INDEX IF NOT EXISTS idx_timeline_outcomes_user
ON event_timeline_outcomes(user_id, updated_at DESC);
