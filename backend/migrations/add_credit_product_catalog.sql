-- Credit packs sold via Google Play (credits_N) and Razorpay.
-- Admin can disable packs without removing them from Google Play Console.
CREATE TABLE IF NOT EXISTS credit_product_catalog (
    product_id TEXT PRIMARY KEY,
    credits INTEGER NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO credit_product_catalog (product_id, credits, is_active, sort_order)
VALUES
    ('credits_24', 24, TRUE, 1),
    ('credits_50', 50, TRUE, 2),
    ('credits_100', 100, TRUE, 3),
    ('credits_250', 250, TRUE, 4),
    ('credits_500', 500, TRUE, 5),
    ('credits_999', 999, TRUE, 6)
ON CONFLICT (product_id) DO NOTHING;
