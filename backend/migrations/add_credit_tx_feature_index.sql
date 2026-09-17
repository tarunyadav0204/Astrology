CREATE INDEX IF NOT EXISTS idx_credit_tx_feature_created
  ON credit_transactions (reference_id, created_at DESC)
  WHERE source = 'feature_usage';
