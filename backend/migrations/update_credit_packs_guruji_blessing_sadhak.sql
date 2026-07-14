-- Legacy migration (superseded by update_credit_packs_shuruaat_aashirwad_sadhak_guru.sql).
-- Kept for history. Prefer the newer migration which reactivates credits_999 (Guru Pack).

UPDATE credit_product_catalog
SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
WHERE product_id IN ('credits_24', 'credits_500');

INSERT INTO credit_product_catalog (product_id, credits, is_active, sort_order)
VALUES
    ('credits_50', 50, TRUE, 1),
    ('credits_100', 100, TRUE, 2),
    ('credits_250', 250, TRUE, 3),
    ('credits_999', 999, TRUE, 4)
ON CONFLICT (product_id) DO UPDATE SET
    is_active = TRUE,
    sort_order = EXCLUDED.sort_order,
    updated_at = CURRENT_TIMESTAMP;
