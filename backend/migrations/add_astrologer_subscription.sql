-- Family-aware subscriptions and the monthly Astrologer License.
-- Idempotent PostgreSQL migration.

ALTER TABLE subscription_plans
    ADD COLUMN IF NOT EXISTS subscription_family TEXT NOT NULL DEFAULT 'vip';

ALTER TABLE subscription_plans
    ADD COLUMN IF NOT EXISTS entitlement_key TEXT;

UPDATE subscription_plans
SET subscription_family = 'vip'
WHERE subscription_family IS NULL OR TRIM(subscription_family) = '';

UPDATE subscription_plans
SET entitlement_key = 'vip_discounts'
WHERE subscription_family = 'vip'
  AND COALESCE(discount_percent, 0) > 0
  AND (entitlement_key IS NULL OR TRIM(entitlement_key) = '');

INSERT INTO subscription_plans (
    plan_id,
    platform,
    plan_name,
    price,
    duration_months,
    features,
    is_active,
    tier_name,
    discount_percent,
    google_play_product_id,
    subscription_family,
    entitlement_key
)
SELECT
    COALESCE(MAX(plan_id), 0) + 1,
    'astroroshni',
    'astrologer_license_monthly',
    100.00,
    1,
    '{"benefits":["What is activated now?","Professional house activation reasoning","Combined chart manifestations"],"entitlements":["astrologer_tools"]}',
    'true',
    'Astrologer License',
    0,
    'astrologer_license_monthly',
    'astrologer',
    'astrologer_tools'
FROM subscription_plans
WHERE NOT EXISTS (
    SELECT 1
    FROM subscription_plans
    WHERE platform = 'astroroshni'
      AND subscription_family = 'astrologer'
      AND google_play_product_id = 'astrologer_license_monthly'
);

CREATE INDEX IF NOT EXISTS idx_subscription_plans_family
    ON subscription_plans (platform, subscription_family);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active_family
    ON user_subscriptions (userid, status, end_date, plan_id);
