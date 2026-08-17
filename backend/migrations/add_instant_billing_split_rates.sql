-- Separate, admin-controlled first-minute and continuing-minute Instant Chat rates.
ALTER TABLE instant_billing_sessions
    ADD COLUMN IF NOT EXISTS first_minute_cost INTEGER;

ALTER TABLE instant_billing_sessions
    ADD COLUMN IF NOT EXISTS original_first_minute_cost INTEGER;

UPDATE instant_billing_sessions
SET first_minute_cost = COALESCE(first_minute_cost, per_minute_cost),
    original_first_minute_cost = COALESCE(original_first_minute_cost, original_per_minute_cost)
WHERE first_minute_cost IS NULL OR original_first_minute_cost IS NULL;

-- Legacy production schemas do not all have a UNIQUE constraint on
-- credit_settings.setting_key, so an explicit ON CONFLICT target is unsafe.
INSERT INTO credit_settings (setting_key, setting_value, description)
SELECT 'instant_chat_first_minute_cost', 1, 'Credits for the first minute of Instant Chat'
WHERE NOT EXISTS (
    SELECT 1
    FROM credit_settings
    WHERE setting_key = 'instant_chat_first_minute_cost'
);

UPDATE credit_settings
SET description = 'Credits per following started minute of Instant Chat'
WHERE setting_key = 'instant_chat_per_minute_cost';
