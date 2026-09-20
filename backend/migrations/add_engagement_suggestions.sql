-- Shared source of ranked questions for chat surfaces and notification channels.
-- PostgreSQL; safe to run repeatedly.

CREATE TABLE IF NOT EXISTS engagement_opportunities (
    id TEXT PRIMARY KEY,
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    birth_chart_id INTEGER REFERENCES birth_charts(id) ON DELETE CASCADE,
    chart_name_snapshot TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL CHECK (
        source_type IN ('chat_followup', 'monthly_manifestation', 'kp_daily')
    ),
    source_reference_id TEXT NOT NULL,
    source_version TEXT NOT NULL DEFAULT '1',
    manifestation_id TEXT,
    domain TEXT NOT NULL DEFAULT 'other',
    subject TEXT NOT NULL DEFAULT 'self',
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    support_strength DOUBLE PRECISION NOT NULL DEFAULT 0,
    relevance_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    event_window_start TIMESTAMPTZ,
    event_window_end TIMESTAMPTZ,
    eligible_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    dedupe_key TEXT NOT NULL,
    semantic_cluster TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'consumed', 'expired', 'suppressed')
    ),
    cooldown_until TIMESTAMPTZ,
    presentation_count INTEGER NOT NULL DEFAULT 0,
    last_presented_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(userid, dedupe_key)
);

CREATE INDEX IF NOT EXISTS idx_engagement_opportunities_rank
    ON engagement_opportunities(userid, birth_chart_id, status, eligible_from, expires_at);
CREATE INDEX IF NOT EXISTS idx_engagement_opportunities_source
    ON engagement_opportunities(source_type, source_reference_id);
CREATE INDEX IF NOT EXISTS idx_engagement_opportunities_expiry
    ON engagement_opportunities(status, expires_at);

CREATE TABLE IF NOT EXISTS engagement_presentations (
    id BIGSERIAL PRIMARY KEY,
    opportunity_id TEXT NOT NULL REFERENCES engagement_opportunities(id) ON DELETE CASCADE,
    locale TEXT NOT NULL DEFAULT 'en',
    chat_question TEXT NOT NULL,
    push_title TEXT,
    push_body TEXT,
    whatsapp_body TEXT,
    whatsapp_template_name TEXT,
    whatsapp_template_params_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    sms_body TEXT,
    email_subject TEXT,
    email_body TEXT,
    landing_screen TEXT NOT NULL DEFAULT 'chat',
    prefilled_question TEXT NOT NULL,
    generation_method TEXT NOT NULL CHECK (
        generation_method IN ('deterministic', 'existing_llm')
    ),
    model_name TEXT,
    prompt_version TEXT,
    content_version TEXT NOT NULL DEFAULT '1',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(opportunity_id, locale, content_version)
);

CREATE INDEX IF NOT EXISTS idx_engagement_presentations_active
    ON engagement_presentations(opportunity_id, locale) WHERE active = TRUE;

CREATE TABLE IF NOT EXISTS engagement_interactions (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    opportunity_id TEXT NOT NULL REFERENCES engagement_opportunities(id) ON DELETE CASCADE,
    presentation_id BIGINT REFERENCES engagement_presentations(id) ON DELETE SET NULL,
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    birth_chart_id INTEGER REFERENCES birth_charts(id) ON DELETE SET NULL,
    surface TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('shown', 'clicked', 'dismissed', 'asked', 'edited', 'converted')
    ),
    delivery_group_id TEXT,
    session_id TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_engagement_interactions_recent
    ON engagement_interactions(userid, event_type, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_engagement_interactions_opportunity
    ON engagement_interactions(opportunity_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS user_engagement_preferences (
    userid INTEGER PRIMARY KEY REFERENCES users(userid) ON DELETE CASCADE,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    preferred_locale TEXT NOT NULL DEFAULT 'en',
    astrology_alerts_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    push_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    whatsapp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    sms_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    email_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    preferred_delivery_time TIME,
    daily_notification_limit INTEGER NOT NULL DEFAULT 1 CHECK (daily_notification_limit BETWEEN 0 AND 20),
    weekly_notification_limit INTEGER NOT NULL DEFAULT 5 CHECK (weekly_notification_limit BETWEEN 0 AND 100),
    suppressed_domains_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    consent_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagement_refresh_queue (
    id BIGSERIAL PRIMARY KEY,
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    birth_chart_id INTEGER NOT NULL REFERENCES birth_charts(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    sources_json JSONB NOT NULL DEFAULT '["monthly_manifestation","kp_daily"]'::jsonb,
    scheduled_for TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    state TEXT NOT NULL DEFAULT 'pending' CHECK (
        state IN ('pending', 'running', 'completed', 'failed')
    ),
    attempts INTEGER NOT NULL DEFAULT 0,
    lease_until TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(userid, birth_chart_id)
);

CREATE INDEX IF NOT EXISTS idx_engagement_refresh_due
    ON engagement_refresh_queue(state, scheduled_for, lease_until);

CREATE TABLE IF NOT EXISTS engagement_delivery_attempts (
    id BIGSERIAL PRIMARY KEY,
    opportunity_id TEXT NOT NULL REFERENCES engagement_opportunities(id) ON DELETE CASCADE,
    presentation_id BIGINT REFERENCES engagement_presentations(id) ON DELETE SET NULL,
    userid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    birth_chart_id INTEGER REFERENCES birth_charts(id) ON DELETE SET NULL,
    delivery_group_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    provider TEXT,
    rendered_title TEXT,
    rendered_body TEXT NOT NULL,
    destination_hash TEXT,
    provider_message_id TEXT,
    provider_status TEXT NOT NULL DEFAULT 'queued',
    attempt_number INTEGER NOT NULL DEFAULT 1,
    scheduled_at TIMESTAMPTZ,
    attempted_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    failure_code TEXT,
    provider_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(delivery_group_id, channel, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_engagement_delivery_user_created
    ON engagement_delivery_attempts(userid, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_engagement_delivery_provider_message
    ON engagement_delivery_attempts(provider_message_id)
    WHERE provider_message_id IS NOT NULL;
