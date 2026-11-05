-- Read-only PostgreSQL logic. All reporting dates use Asia/Kolkata.
-- `chat_messages.timestamp` and `credit_transactions.created_at` are UTC-naive
-- application timestamps, therefore `AT TIME ZONE 'UTC'` converts them safely.

WITH cohorts AS (
  SELECT
    COALESCE('user:' || userid::text, 'install:' || installation_id::text) AS identity_key,
    userid,
    MIN(first_open_at) AS first_open_at
  FROM app_installations
  GROUP BY 1, userid
),
questions_7d AS (
  SELECT DISTINCT c.identity_key
  FROM cohorts c
  JOIN chat_sessions s ON s.user_id = c.userid
  JOIN chat_messages q ON q.session_id = s.session_id
  WHERE q.sender = 'user'
    AND (q.timestamp AT TIME ZONE 'UTC') >= c.first_open_at
    AND (q.timestamp AT TIME ZONE 'UTC') < c.first_open_at + INTERVAL '168 hours'
),
answers_7d AS (
  SELECT DISTINCT c.identity_key
  FROM cohorts c
  JOIN chat_sessions s ON s.user_id = c.userid
  JOIN chat_messages a ON a.session_id = s.session_id
  WHERE a.sender = 'assistant'
    AND a.status = 'completed'
    AND (a.completed_at AT TIME ZONE 'UTC') >= c.first_open_at
    AND (a.completed_at AT TIME ZONE 'UTC') < c.first_open_at + INTERVAL '168 hours'
    AND EXISTS (
      SELECT 1
      FROM chat_messages q
      WHERE q.session_id = a.session_id
        AND q.sender = 'user'
        AND (q.timestamp AT TIME ZONE 'UTC') >= c.first_open_at
        AND (q.timestamp AT TIME ZONE 'UTC') <= (a.completed_at AT TIME ZONE 'UTC')
    )
),
provider_refunds AS (
  SELECT userid, reference_id
  FROM credit_transactions
  WHERE source IN ('google_play_refund', 'razorpay_refund')
    AND transaction_type = 'spent'
),
first_net_paid_purchase AS (
  SELECT DISTINCT ON (ct.userid)
    ct.userid,
    (ct.created_at AT TIME ZONE 'UTC') AS purchased_at
  FROM credit_transactions ct
  WHERE ct.source IN ('google_play', 'razorpay')
    AND ct.transaction_type = 'earned'
    AND NOT EXISTS (
      SELECT 1 FROM provider_refunds r
      WHERE r.userid = ct.userid
        AND r.reference_id IS NOT DISTINCT FROM ct.reference_id
    )
  ORDER BY ct.userid, ct.created_at, ct.reference_id
)
SELECT 'aggregate in the selected IST date range';
