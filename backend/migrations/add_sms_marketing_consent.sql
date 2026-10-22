-- Marketing SMS requires consent separate from a phone used for login or OTP.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS sms_marketing_opted_in_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS sms_marketing_opted_out_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS sms_marketing_consent_source TEXT,
    ADD COLUMN IF NOT EXISTS sms_marketing_consent_version TEXT;

CREATE INDEX IF NOT EXISTS idx_users_sms_marketing_eligible
    ON users (userid)
    WHERE sms_marketing_opted_in_at IS NOT NULL
      AND sms_marketing_opted_out_at IS NULL;
