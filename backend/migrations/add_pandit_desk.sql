-- Pandit Desk: practice profiles + free pandit subscription entitlement.
-- Idempotent PostgreSQL migration.

CREATE TABLE IF NOT EXISTS pandit_profiles (
    id BIGSERIAL PRIMARY KEY,
    userid INTEGER NOT NULL UNIQUE REFERENCES users(userid) ON DELETE CASCADE,
    display_name TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    pincode TEXT NOT NULL DEFAULT '',
    languages TEXT NOT NULL DEFAULT '["hindi","english"]',
    puja_types TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active_tools',
    tagline TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    website TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    setup_complete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pandit_profiles_userid
    ON pandit_profiles (userid);

CREATE INDEX IF NOT EXISTS idx_pandit_profiles_pincode
    ON pandit_profiles (pincode);

CREATE INDEX IF NOT EXISTS idx_pandit_profiles_status
    ON pandit_profiles (status);

-- Free Pandit Desk plan (₹0 complimentary entitlement).
WITH next_plan AS (
    SELECT COALESCE(MAX(plan_id), 0) + 1 AS plan_id
    FROM subscription_plans
)
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
    next_plan.plan_id,
    'astroroshni',
    'pandit_desk_free',
    0.00,
    120,
    '{"benefits":["Branded Janam Kundli","Muhurat shortlist with reasons","Practice profile for puja routing"],"entitlements":["pandit_desk"]}',
    'true',
    'Pandit Desk Free',
    0,
    'pandit_desk_free',
    'pandit',
    'pandit_desk'
FROM next_plan
WHERE NOT EXISTS (
    SELECT 1
    FROM subscription_plans
    WHERE platform = 'astroroshni'
      AND subscription_family = 'pandit'
      AND google_play_product_id = 'pandit_desk_free'
);
