-- Additive, backward-compatible support for Meta template campaigns.
ALTER TABLE nudge_campaigns
    ADD COLUMN IF NOT EXISTS whatsapp_template_json TEXT,
    ADD COLUMN IF NOT EXISTS conversion_event TEXT NOT NULL DEFAULT 'click',
    ADD COLUMN IF NOT EXISTS frequency_cap_days INTEGER NOT NULL DEFAULT 0;

ALTER TABLE nudge_deliveries
    ADD COLUMN IF NOT EXISTS meta_message_id TEXT,
    ADD COLUMN IF NOT EXISTS meta_recipient_id TEXT,
    ADD COLUMN IF NOT EXISTS meta_status TEXT,
    ADD COLUMN IF NOT EXISTS meta_accepted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS meta_sent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS meta_delivered_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS meta_read_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS meta_failed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS meta_error TEXT,
    ADD COLUMN IF NOT EXISTS meta_status_updated_at TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS idx_nudge_deliveries_meta_message
    ON nudge_deliveries(meta_message_id)
    WHERE meta_message_id IS NOT NULL;
