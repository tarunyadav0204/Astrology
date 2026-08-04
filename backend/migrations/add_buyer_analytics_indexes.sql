-- Optional indexes for Credits → Buyer analysis admin dashboard.
-- Safe to run multiple times. Prefer running offline (maintenance window) on large DBs.
-- Do NOT create these from the API request path (locking / pool hold risk).
--
-- Run manually, e.g.:
--   psql "$DATABASE_URL" -f backend/migrations/add_buyer_analytics_indexes.sql
--
-- For production with live traffic, prefer CONCURRENTLY variants (cannot run inside a
-- transaction block):
--   CREATE INDEX CONCURRENTLY IF NOT EXISTS ...

-- Paid credit purchases by time (range scans for weekly buyer analytics).
CREATE INDEX IF NOT EXISTS idx_ct_paid_created
    ON credit_transactions (created_at DESC)
    WHERE transaction_type = 'earned'
      AND source IN ('google_play', 'razorpay');

-- First-purchase lookup per buyer in the selected window.
CREATE INDEX IF NOT EXISTS idx_ct_paid_userid_created
    ON credit_transactions (userid, created_at)
    WHERE transaction_type = 'earned'
      AND source IN ('google_play', 'razorpay');

-- First-touch UTM attribution: earliest install row per linked user.
CREATE INDEX IF NOT EXISTS idx_app_installations_userid_first_open
    ON app_installations (userid, first_open_at)
    WHERE userid IS NOT NULL;
