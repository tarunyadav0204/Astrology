-- Add the admin-controlled price for one successfully produced Prashna chart.
-- Older credit_settings tables do not always have a unique setting_key.
INSERT INTO credit_settings (setting_key, setting_value, description)
SELECT 'prashna_analysis_cost', 3, 'Credits per classical Prashna question chart'
WHERE NOT EXISTS (
    SELECT 1
    FROM credit_settings
    WHERE setting_key = 'prashna_analysis_cost'
);
