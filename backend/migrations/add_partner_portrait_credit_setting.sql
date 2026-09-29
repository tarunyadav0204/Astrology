-- Add the admin-controlled price for one Partner Portrait generation.
-- Older credit_settings tables do not always have a unique setting_key.
INSERT INTO credit_settings (setting_key, setting_value, description)
SELECT 'partner_portrait_cost', 44, 'Credits per AI Partner Portrait with face and full-body views'
WHERE NOT EXISTS (
    SELECT 1
    FROM credit_settings
    WHERE setting_key = 'partner_portrait_cost'
);
