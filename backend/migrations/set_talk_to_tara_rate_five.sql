-- One-time correction for installations where the earlier Talk To Tara rate
-- was seeded as 7 credits/minute. Future admin changes must remain untouched.
CREATE TABLE IF NOT EXISTS runtime_data_migrations (
    migration_key TEXT PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

WITH applied_now AS (
    INSERT INTO runtime_data_migrations (migration_key)
    VALUES ('2026-09-11-talk-to-tara-rate-five')
    ON CONFLICT (migration_key) DO NOTHING
    RETURNING migration_key
)
UPDATE credit_settings
SET setting_value = CASE WHEN setting_value = 7 THEN 5 ELSE setting_value END,
    discount = CASE WHEN discount = 7 THEN NULL ELSE discount END,
    description = 'Credits per minute for Talk To Tara',
    updated_at = CURRENT_TIMESTAMP
WHERE setting_key = 'speech_chat_per_minute_cost'
  AND (setting_value = 7 OR discount = 7)
  AND EXISTS (SELECT 1 FROM applied_now);
