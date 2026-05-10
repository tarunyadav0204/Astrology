-- Canonical fingerprint for free-question / abuse checks (computed from plaintext date, time, lat, lon before encryption).
ALTER TABLE birth_charts ADD COLUMN IF NOT EXISTS birth_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_birth_charts_policy_hash ON birth_charts (birth_hash);
