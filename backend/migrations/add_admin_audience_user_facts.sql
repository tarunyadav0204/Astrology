-- Curated one-row-per-user facts for NL Audience Builder (admin campaigns).
-- LLM may SELECT only from this view. Safe to re-run (CREATE OR REPLACE).

CREATE OR REPLACE VIEW admin_audience_user_facts AS
WITH paid AS (
    SELECT
        userid,
        amount,
        created_at,
        metadata,
        ROW_NUMBER() OVER (PARTITION BY userid ORDER BY created_at DESC) AS rn,
        COUNT(*) OVER (PARTITION BY userid) AS purchase_count,
        SUM(amount) OVER (PARTITION BY userid) AS lifetime_purchased_credits
    FROM credit_transactions
    WHERE transaction_type = 'earned'
      AND source IN ('razorpay', 'google_play')
),
last_paid AS (
    SELECT
        userid,
        created_at AS last_purchase_at,
        amount AS last_purchase_credits,
        purchase_count,
        lifetime_purchased_credits,
        CASE
            WHEN metadata IS NULL OR btrim(metadata) = '' THEN NULL
            WHEN metadata ~ '"amount_paise"[[:space:]]*:[[:space:]]*[0-9]+'
                THEN (substring(metadata from '"amount_paise"[[:space:]]*:[[:space:]]*([0-9]+)')::numeric / 100.0)
            WHEN metadata ~ '"price_amount_micros"[[:space:]]*:[[:space:]]*[0-9]+'
                THEN (substring(metadata from '"price_amount_micros"[[:space:]]*:[[:space:]]*([0-9]+)')::numeric / 1000000.0)
            ELSE NULL
        END AS last_purchase_amount
    FROM paid
    WHERE rn = 1
),
spent AS (
    SELECT
        userid,
        COALESCE(SUM(ABS(amount)), 0)::bigint AS lifetime_spent_credits
    FROM credit_transactions
    WHERE transaction_type = 'spent'
    GROUP BY userid
),
chat AS (
    SELECT
        cs.user_id AS userid,
        MAX(cm.timestamp) FILTER (WHERE cm.sender = 'user') AS last_user_chat_at,
        COUNT(*) FILTER (WHERE cm.sender = 'user')::bigint AS questions_asked_lifetime,
        COUNT(*) FILTER (
            WHERE cm.sender = 'user'
              AND cm.timestamp >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '30 days'
        )::bigint AS questions_asked_30d,
        COUNT(*) FILTER (
            WHERE cm.sender = 'user'
              AND ((cm.timestamp AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Kolkata')::date
                  = (NOW() AT TIME ZONE 'Asia/Kolkata')::date
        )::bigint AS questions_asked_today,
        COUNT(*) FILTER (
            WHERE cm.sender = 'user'
              AND ((cm.timestamp AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Kolkata')::date
                  = (NOW() AT TIME ZONE 'Asia/Kolkata')::date - 1
        )::bigint AS questions_asked_yesterday
    FROM chat_sessions cs
    JOIN chat_messages cm ON cm.session_id = cs.session_id
    GROUP BY cs.user_id
),
paid_question_activity AS (
    SELECT
        ct.userid,
        MAX(ct.created_at) AS last_paid_question_at,
        COUNT(*) FILTER (
            WHERE ((ct.created_at AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Kolkata')::date
                  = (NOW() AT TIME ZONE 'Asia/Kolkata')::date
        )::bigint AS paid_questions_today,
        COUNT(*) FILTER (
            WHERE ((ct.created_at AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Kolkata')::date
                  = (NOW() AT TIME ZONE 'Asia/Kolkata')::date - 1
        )::bigint AS paid_questions_yesterday
    FROM credit_transactions ct
    WHERE ct.transaction_type = 'spent'
      AND ct.source = 'feature_usage'
      AND ct.amount < 0
      AND ct.reference_id IN ('chat_question', 'instant_chat', 'speech_chat')
    GROUP BY ct.userid
),
push AS (
    SELECT DISTINCT userid
    FROM device_tokens
)
SELECT
    u.userid,
    COALESCE(NULLIF(btrim(u.name), ''), '') AS name,
    COALESCE(NULLIF(btrim(u.phone), ''), '') AS phone,
    COALESCE(NULLIF(btrim(u.email), ''), '') AS email,
    COALESCE(uc.credits, 0)::bigint AS credits_balance,
    COALESCE(lp.lifetime_purchased_credits, 0)::bigint AS lifetime_purchased_credits,
    COALESCE(sp.lifetime_spent_credits, 0)::bigint AS lifetime_spent_credits,
    COALESCE(lp.purchase_count, 0)::bigint AS purchase_count,
    lp.last_purchase_at,
    lp.last_purchase_amount,
    COALESCE(lp.last_purchase_credits, 0)::bigint AS last_purchase_credits,
    ch.last_user_chat_at,
    CASE
        WHEN ch.last_user_chat_at IS NULL THEN NULL
        ELSE GREATEST(
            0,
            FLOOR(EXTRACT(EPOCH FROM ((NOW() AT TIME ZONE 'UTC') - ch.last_user_chat_at)) / 86400.0)
        )::integer
    END AS days_since_last_chat,
    COALESCE(ch.questions_asked_30d, 0)::bigint AS questions_asked_30d,
    COALESCE(ch.questions_asked_lifetime, 0)::bigint AS questions_asked_lifetime,
    (p.userid IS NOT NULL) AS has_device_token,
    (
        COALESCE(NULLIF(btrim(u.whatsapp_wa_id), ''), '') <> ''
    ) AS has_whatsapp,
    (
        COALESCE(NULLIF(btrim(u.email), ''), '') <> ''
    ) AS has_email,
    u.created_at AS signup_at,
    COALESCE(NULLIF(btrim(u.signup_client), ''), '') AS signup_client,
    COALESCE(ch.questions_asked_today, 0)::bigint AS questions_asked_today,
    COALESCE(ch.questions_asked_yesterday, 0)::bigint AS questions_asked_yesterday,
    COALESCE(pqa.paid_questions_today, 0)::bigint AS paid_questions_today,
    COALESCE(pqa.paid_questions_yesterday, 0)::bigint AS paid_questions_yesterday,
    pqa.last_paid_question_at
FROM users u
LEFT JOIN user_credits uc ON uc.userid = u.userid
LEFT JOIN last_paid lp ON lp.userid = u.userid
LEFT JOIN spent sp ON sp.userid = u.userid
LEFT JOIN chat ch ON ch.userid = u.userid
LEFT JOIN paid_question_activity pqa ON pqa.userid = u.userid
LEFT JOIN push p ON p.userid = u.userid;
