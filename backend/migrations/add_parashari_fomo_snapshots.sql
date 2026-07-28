-- Persist deterministic Parashari FOMO results and their presentation funnel.
-- Idempotent PostgreSQL migration.

CREATE TABLE IF NOT EXISTS parashari_prediction_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    birth_chart_id INTEGER NOT NULL REFERENCES birth_charts(id) ON DELETE CASCADE,
    cache_key TEXT NOT NULL UNIQUE,
    chart_hash TEXT NOT NULL,
    locale TEXT NOT NULL,
    as_of_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL,
    profile TEXT NOT NULL,
    profile_version TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    evidence_signature TEXT NOT NULL,
    display_signature TEXT NOT NULL,
    result_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE parashari_prediction_snapshots
    ADD COLUMN IF NOT EXISTS display_signature TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_parashari_snapshots_user_expiry
    ON parashari_prediction_snapshots(userid, expires_at DESC);

CREATE INDEX IF NOT EXISTS idx_parashari_snapshots_chart_signature
    ON parashari_prediction_snapshots(birth_chart_id, evidence_signature);

CREATE INDEX IF NOT EXISTS idx_parashari_snapshots_display_signature
    ON parashari_prediction_snapshots(userid, display_signature);

CREATE TABLE IF NOT EXISTS parashari_prediction_teasers (
    snapshot_id TEXT NOT NULL
        REFERENCES parashari_prediction_snapshots(snapshot_id) ON DELETE CASCADE,
    presentation_id TEXT NOT NULL,
    manifestation_id TEXT NOT NULL,
    display_rank INTEGER NOT NULL,
    locale TEXT NOT NULL,
    subject TEXT NOT NULL,
    domain TEXT NOT NULL,
    area_label TEXT NOT NULL DEFAULT '',
    tone TEXT NOT NULL,
    title TEXT NOT NULL,
    teaser TEXT NOT NULL,
    suggested_question TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    template_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(snapshot_id, presentation_id),
    UNIQUE(snapshot_id, manifestation_id, locale)
);

ALTER TABLE parashari_prediction_teasers
    ADD COLUMN IF NOT EXISTS area_label TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_parashari_teasers_snapshot_rank
    ON parashari_prediction_teasers(snapshot_id, display_rank);

CREATE TABLE IF NOT EXISTS parashari_prediction_funnel_events (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    snapshot_id TEXT NOT NULL
        REFERENCES parashari_prediction_snapshots(snapshot_id) ON DELETE CASCADE,
    presentation_id TEXT,
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'shown',
            'opened',
            'dismissed',
            'question_prefilled',
            'question_sent',
            'answer_completed'
        )
    ),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT parashari_prediction_funnel_events_snapshot_presentation_fkey
    FOREIGN KEY(snapshot_id, presentation_id)
        REFERENCES parashari_prediction_teasers(snapshot_id, presentation_id)
        ON DELETE CASCADE
);

-- Upgrade the brief pre-release single-column teaser key if it was applied.
DO $$
DECLARE
    key_column_count INTEGER;
BEGIN
    SELECT array_length(conkey, 1)
    INTO key_column_count
    FROM pg_constraint
    WHERE conrelid = 'parashari_prediction_teasers'::regclass
      AND contype = 'p';

    IF key_column_count = 1 THEN
        ALTER TABLE parashari_prediction_funnel_events
            DROP CONSTRAINT IF EXISTS parashari_prediction_funnel_events_presentation_id_fkey;
        ALTER TABLE parashari_prediction_teasers
            DROP CONSTRAINT IF EXISTS parashari_prediction_teasers_pkey;
        ALTER TABLE parashari_prediction_teasers
            ADD CONSTRAINT parashari_prediction_teasers_pkey
            PRIMARY KEY(snapshot_id, presentation_id);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'parashari_prediction_funnel_events'::regclass
          AND conname = 'parashari_prediction_funnel_events_snapshot_presentation_fkey'
    ) THEN
        ALTER TABLE parashari_prediction_funnel_events
            ADD CONSTRAINT parashari_prediction_funnel_events_snapshot_presentation_fkey
            FOREIGN KEY(snapshot_id, presentation_id)
            REFERENCES parashari_prediction_teasers(snapshot_id, presentation_id)
            ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_parashari_funnel_user_type_created
    ON parashari_prediction_funnel_events(userid, event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_parashari_funnel_snapshot_created
    ON parashari_prediction_funnel_events(snapshot_id, created_at DESC);

CREATE TABLE IF NOT EXISTS parashari_prediction_preferences (
    userid INTEGER PRIMARY KEY REFERENCES users(userid) ON DELETE CASCADE,
    homepage_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
