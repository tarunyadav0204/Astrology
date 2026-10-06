-- AI-assisted authoring candidates for Deva Keralam passages.
--
-- This is deliberately separate from classical_rule_versions and releases.
-- No row in these tables can be published or consumed by runtime chart/chat
-- evaluation. A human review workflow must promote a candidate explicitly in
-- a later governed stage.

CREATE TABLE IF NOT EXISTS classical_rule_extraction_runs (
  extraction_run_key TEXT PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES classical_editions(edition_key),
  model_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  last_passage_key TEXT,
  passages_requested INTEGER NOT NULL DEFAULT 0 CHECK (passages_requested >= 0),
  passages_completed INTEGER NOT NULL DEFAULT 0 CHECK (passages_completed >= 0),
  passages_failed INTEGER NOT NULL DEFAULT 0 CHECK (passages_failed >= 0),
  options JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT NOT NULL DEFAULT '',
  started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS classical_rule_candidates (
  candidate_key TEXT PRIMARY KEY,
  extraction_run_key TEXT NOT NULL REFERENCES classical_rule_extraction_runs(extraction_run_key),
  passage_key TEXT NOT NULL REFERENCES classical_passages(passage_key),
  source_content_hash TEXT NOT NULL,
  model_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_review', 'rejected')),
  source_review_status TEXT NOT NULL,
  source_text_status TEXT NOT NULL,
  context_status TEXT NOT NULL,
  candidate_json JSONB NOT NULL,
  source_snapshot JSONB NOT NULL,
  uncertainties JSONB NOT NULL DEFAULT '[]'::jsonb,
  usage_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  reviewer_notes TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (passage_key, source_content_hash, model_id, prompt_version)
);

-- The migration is rerunnable after early local smoke tests created the draft
-- table before provenance snapshots were added.
ALTER TABLE classical_rule_candidates
  ADD COLUMN IF NOT EXISTS source_review_status TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS source_text_status TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS context_status TEXT NOT NULL DEFAULT 'missing',
  ADD COLUMN IF NOT EXISTS source_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Compatibility for databases that created the draft table before source
-- provenance snapshots were added. CREATE TABLE IF NOT EXISTS does not add
-- later columns to an existing table, so keep this migration genuinely
-- idempotent for local and deployed upgrades.
ALTER TABLE classical_rule_candidates
  ADD COLUMN IF NOT EXISTS source_review_status TEXT NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS source_text_status TEXT NOT NULL DEFAULT 'ocr_unverified',
  ADD COLUMN IF NOT EXISTS context_status TEXT NOT NULL DEFAULT 'unreviewed',
  ADD COLUMN IF NOT EXISTS source_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_classical_rule_candidates_review
  ON classical_rule_candidates (status, passage_key);

CREATE INDEX IF NOT EXISTS idx_classical_rule_extraction_runs_resume
  ON classical_rule_extraction_runs (status, edition_key, updated_at);
