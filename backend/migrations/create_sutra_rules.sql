-- Governed authoring store for classical sutras. This table contains authored
-- rules only; no evaluator or user-facing consumer reads it in phase one.
CREATE TABLE IF NOT EXISTS sutra_rules (
  id TEXT PRIMARY KEY,
  rule_key TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  primary_stream TEXT NOT NULL,
  primary_chart TEXT NOT NULL,
  category TEXT,
  subcategory TEXT,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  topics JSONB NOT NULL DEFAULT '[]'::jsonb,
  authority JSONB NOT NULL DEFAULT '{}'::jsonb,
  logic_operator TEXT NOT NULL,
  conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
  modifiers JSONB NOT NULL DEFAULT '{}'::jsonb,
  outputs JSONB NOT NULL DEFAULT '{}'::jsonb,
  visibility TEXT NOT NULL,
  safety JSONB NOT NULL DEFAULT '{}'::jsonb,
  reviewer_notes TEXT NOT NULL DEFAULT '',
  created_by INTEGER,
  updated_by INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sutra_rules_status_updated
  ON sutra_rules (status, updated_at DESC);

ALTER TABLE sutra_rules ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE sutra_rules ADD COLUMN IF NOT EXISTS subcategory TEXT;
ALTER TABLE sutra_rules ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb;
