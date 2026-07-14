-- One-time pack relaunch gift: +25 credits
-- Eligible ONLY if:
--   1) current balance > 0, OR
--   2) recharged via Google Play / Razorpay in the last 90 days
-- Idempotent: skips anyone who already has this description.

BEGIN;

WITH eligible AS (
  SELECT uc.userid, uc.credits AS old_credits
  FROM user_credits uc
  WHERE uc.credits > 0

  UNION

  SELECT DISTINCT ct.userid, COALESCE(uc.credits, 0) AS old_credits
  FROM credit_transactions ct
  LEFT JOIN user_credits uc ON uc.userid = ct.userid
  WHERE ct.transaction_type = 'earned'
    AND ct.source IN ('google_play', 'razorpay')
    AND ct.created_at >= (CURRENT_TIMESTAMP - INTERVAL '90 days')
),
filtered AS (
  SELECT e.userid, e.old_credits
  FROM eligible e
  WHERE NOT EXISTS (
    SELECT 1
    FROM credit_transactions x
    WHERE x.userid = e.userid
      AND x.description = 'Pack relaunch: 25 free credits'
  )
),
-- Create missing balance rows (recharged users with no user_credits row)
ensured AS (
  INSERT INTO user_credits (userid, credits, updated_at)
  SELECT f.userid, 0, CURRENT_TIMESTAMP
  FROM filtered f
  WHERE NOT EXISTS (
    SELECT 1 FROM user_credits uc WHERE uc.userid = f.userid
  )
  RETURNING userid
),
updated AS (
  UPDATE user_credits uc
  SET credits = uc.credits + 25,
      updated_at = CURRENT_TIMESTAMP
  FROM filtered f
  WHERE uc.userid = f.userid
  RETURNING uc.userid, uc.credits AS new_credits
)
INSERT INTO credit_transactions
  (userid, transaction_type, amount, balance_after, source, reference_id, description)
SELECT
  userid,
  'earned',
  25,
  new_credits,
  'admin_adjustment',
  NULL,
  'Pack relaunch: 25 free credits'
FROM updated;

COMMIT;

-- Preview before running (optional):
-- SELECT COUNT(DISTINCT userid) FROM (
--   SELECT userid FROM user_credits WHERE credits > 0
--   UNION
--   SELECT DISTINCT userid FROM credit_transactions
--   WHERE transaction_type = 'earned'
--     AND source IN ('google_play', 'razorpay')
--     AND created_at >= CURRENT_TIMESTAMP - INTERVAL '90 days'
-- ) t;
