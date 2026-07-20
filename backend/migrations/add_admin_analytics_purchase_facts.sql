-- Curated one-row-per-paid-purchase facts for admin Analytics Q&A.
-- LLM-generated analytics may SELECT only from this view.

CREATE OR REPLACE VIEW admin_analytics_purchase_facts AS
WITH purchases AS (
    SELECT
        ct.id AS transaction_id,
        ct.userid,
        ct.created_at AS purchased_at,
        ct.source AS provider,
        ct.reference_id,
        ct.amount::bigint AS credits_purchased,
        CASE
            WHEN ct.metadata IS NULL OR btrim(ct.metadata) = '' THEN NULL
            WHEN ct.metadata ~ '"amount_paise"[[:space:]]*:[[:space:]]*[0-9]+'
                THEN substring(ct.metadata from '"amount_paise"[[:space:]]*:[[:space:]]*([0-9]+)')::numeric / 100.0
            WHEN ct.metadata ~ '"price_amount_micros"[[:space:]]*:[[:space:]]*[0-9]+'
                THEN substring(ct.metadata from '"price_amount_micros"[[:space:]]*:[[:space:]]*([0-9]+)')::numeric / 1000000.0
            ELSE NULL
        END AS purchase_amount,
        COALESCE(
            NULLIF(upper(substring(ct.metadata from '"currency"[[:space:]]*:[[:space:]]*"([^"]+)"')), ''),
            NULLIF(upper(substring(ct.metadata from '"price_currency"[[:space:]]*:[[:space:]]*"([^"]+)"')), ''),
            'INR'
        ) AS currency
    FROM credit_transactions ct
    WHERE ct.transaction_type = 'earned'
      AND ct.source IN ('razorpay', 'google_play')
),
refunds AS (
    SELECT
        ct.userid,
        ct.reference_id,
        CASE
            WHEN ct.source = 'razorpay_refund' THEN 'razorpay'
            WHEN ct.source = 'google_play_refund' THEN 'google_play'
        END AS provider,
        COALESCE(SUM(ABS(ct.amount)), 0)::bigint AS refunded_credits
    FROM credit_transactions ct
    WHERE ct.source IN ('razorpay_refund', 'google_play_refund')
    GROUP BY ct.userid, ct.reference_id, ct.source
)
SELECT
    p.transaction_id,
    p.userid,
    p.purchased_at,
    p.provider,
    p.credits_purchased,
    p.purchase_amount,
    p.currency,
    COALESCE(r.refunded_credits, 0)::bigint AS refunded_credits,
    GREATEST(p.credits_purchased - COALESCE(r.refunded_credits, 0), 0)::bigint AS net_credits_purchased,
    CASE
        WHEN COALESCE(r.refunded_credits, 0) <= 0 THEN 'paid'
        WHEN r.refunded_credits >= p.credits_purchased THEN 'refunded'
        ELSE 'partially_refunded'
    END AS purchase_status
FROM purchases p
LEFT JOIN refunds r
  ON r.userid = p.userid
 AND r.provider = p.provider
 AND NULLIF(btrim(COALESCE(r.reference_id, '')), '') IS NOT NULL
 AND btrim(r.reference_id) = btrim(p.reference_id);
