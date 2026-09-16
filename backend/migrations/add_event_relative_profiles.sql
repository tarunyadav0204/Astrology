CREATE TABLE IF NOT EXISTS event_relative_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    birth_chart_id INTEGER NOT NULL REFERENCES birth_charts(id) ON DELETE CASCADE,
    subject_key TEXT NOT NULL,
    display_label TEXT NOT NULL,
    life_status TEXT NOT NULL DEFAULT 'unknown',
    age_years INTEGER,
    birth_year INTEGER,
    employment_state TEXT NOT NULL DEFAULT 'unknown',
    location_context TEXT NOT NULL DEFAULT 'unknown',
    relationship_status TEXT NOT NULL DEFAULT 'unknown',
    linked_birth_chart_id INTEGER REFERENCES birth_charts(id) ON DELETE SET NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, birth_chart_id, subject_key)
);

CREATE INDEX IF NOT EXISTS idx_event_relative_profiles_chart
    ON event_relative_profiles (user_id, birth_chart_id);
