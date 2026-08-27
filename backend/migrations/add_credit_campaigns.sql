CREATE TABLE IF NOT EXISTS credit_campaigns (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    multiplier NUMERIC(6, 3) NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    product_ids_json TEXT NOT NULL DEFAULT '[]',
    payment_channel TEXT NOT NULL DEFAULT 'razorpay_web',
    whatsapp_template_name TEXT,
    whatsapp_template_language TEXT,
    created_by INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credit_campaign_recipients (
    campaign_id BIGINT NOT NULL REFERENCES credit_campaigns(id) ON DELETE CASCADE,
    userid INTEGER NOT NULL,
    notified_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    message_status TEXT,
    message_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (campaign_id, userid)
);

CREATE TABLE IF NOT EXISTS credit_campaign_awards (
    id BIGSERIAL PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES credit_campaigns(id),
    userid INTEGER NOT NULL,
    purchase_source TEXT NOT NULL,
    purchase_reference_id TEXT NOT NULL,
    product_id TEXT,
    purchased_credits INTEGER NOT NULL,
    credits_before_campaign INTEGER NOT NULL DEFAULT 0,
    campaign_bonus_credits INTEGER NOT NULL,
    target_total_credits INTEGER NOT NULL,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (campaign_id, purchase_source, purchase_reference_id)
);

CREATE INDEX IF NOT EXISTS idx_credit_campaign_recipients_user
ON credit_campaign_recipients (userid, campaign_id);

CREATE INDEX IF NOT EXISTS idx_credit_campaign_awards_campaign
ON credit_campaign_awards (campaign_id, awarded_at DESC);
