-- Speed up admin user listing, summary, and subscription filters (Postgres).
-- Safe to run multiple times (CREATE INDEX IF NOT EXISTS).
-- Run manually: psql "$DATABASE_URL" -f backend/migrations/add_admin_users_perf_indexes.sql

-- Paginated admin list: ORDER BY u.created_at DESC; DATE(u.created_at) in summary aggregates.
CREATE INDEX IF NOT EXISTS idx_users_created_at_desc
    ON users (created_at DESC);

-- Batched active subs per page: userid IN (...) AND status AND end_date;
-- also helps subscription filter subqueries that join subscription_plans.
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_userid_status_end
    ON user_subscriptions (userid, status, end_date);

-- user_subscriptions → subscription_plans joins (no implicit index on FK child in this schema).
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id
    ON user_subscriptions (plan_id);

-- Subscription filter subqueries (active rows, end_date predicate) without a userid prefix.
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active_end_userid
    ON user_subscriptions (end_date, userid)
    WHERE status = 'active';

-- device_tokens already has UNIQUE (userid, platform), which btree-indexes userid as a prefix;
-- no separate userid-only index added here to avoid redundant write amplification.
