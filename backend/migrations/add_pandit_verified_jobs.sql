-- Admin flag: pandit is eligible for future puja job routing.
-- Idempotent PostgreSQL migration.

ALTER TABLE pandit_profiles
  ADD COLUMN IF NOT EXISTS verified_jobs BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_pandit_profiles_verified_jobs
  ON pandit_profiles (verified_jobs);
