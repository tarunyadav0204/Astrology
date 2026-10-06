-- Review-gated inherited-context reconstruction for Deva Keralam.
--
-- Context reconstruction remains source scholarship. These tables have no
-- foreign key or promotion path to classical_rule_versions/releases, and no
-- chart/chat runtime reads them.

CREATE TABLE IF NOT EXISTS classical_context_reconstruction_runs (
  reconstruction_run_key TEXT PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES classical_editions(edition_key),
  method TEXT NOT NULL CHECK (method IN ('reviewer', 'ai_proposal', 'hybrid')),
  model_id TEXT NOT NULL DEFAULT '',
  prompt_version TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  options JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT NOT NULL DEFAULT '',
  started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS classical_context_spans (
  context_span_key TEXT PRIMARY KEY,
  context_block_key TEXT NOT NULL REFERENCES classical_context_blocks(context_block_key) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL CHECK (ordinal > 0),
  verse_start INTEGER NOT NULL CHECK (verse_start > 0),
  verse_end INTEGER NOT NULL CHECK (verse_end >= verse_start),
  pdf_page_start INTEGER NOT NULL CHECK (pdf_page_start > 0),
  pdf_page_end INTEGER NOT NULL CHECK (pdf_page_end >= pdf_page_start),
  title TEXT NOT NULL,
  context_json JSONB NOT NULL,
  boundary_basis JSONB NOT NULL,
  context_status TEXT NOT NULL CHECK (context_status IN ('candidate', 'review', 'verified', 'rejected')),
  content_hash TEXT NOT NULL,
  reviewer_notes TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (context_block_key, ordinal),
  UNIQUE (context_block_key, verse_start, verse_end)
);

CREATE TABLE IF NOT EXISTS classical_context_premises (
  premise_key TEXT PRIMARY KEY,
  context_block_key TEXT NOT NULL REFERENCES classical_context_blocks(context_block_key) ON DELETE CASCADE,
  context_span_key TEXT REFERENCES classical_context_spans(context_span_key) ON DELETE CASCADE,
  premise_type TEXT NOT NULL,
  applies_verse_start INTEGER NOT NULL CHECK (applies_verse_start > 0),
  applies_verse_end INTEGER NOT NULL CHECK (applies_verse_end >= applies_verse_start),
  premise_value JSONB NOT NULL,
  premise_status TEXT NOT NULL CHECK (premise_status IN ('verified', 'qualified', 'disputed', 'ambiguous')),
  provenance JSONB NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classical_context_source_links (
  context_span_key TEXT NOT NULL REFERENCES classical_context_spans(context_span_key) ON DELETE CASCADE,
  source_kind TEXT NOT NULL CHECK (source_kind IN ('passage', 'source_page', 'nadiamsa_table')),
  passage_key TEXT REFERENCES classical_passages(passage_key),
  source_page_id BIGINT REFERENCES classical_source_pages(source_page_id),
  source_reference JSONB NOT NULL DEFAULT '{}'::jsonb,
  source_reference_hash TEXT NOT NULL,
  relationship TEXT NOT NULL,
  PRIMARY KEY (context_span_key, source_kind, relationship, source_reference_hash),
  CHECK (
    (source_kind = 'passage' AND passage_key IS NOT NULL)
    OR (source_kind = 'source_page' AND source_page_id IS NOT NULL)
    OR (source_kind = 'nadiamsa_table' AND passage_key IS NULL AND source_page_id IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS classical_context_ai_proposals (
  proposal_key TEXT PRIMARY KEY,
  reconstruction_run_key TEXT NOT NULL REFERENCES classical_context_reconstruction_runs(reconstruction_run_key),
  context_block_key TEXT REFERENCES classical_context_blocks(context_block_key),
  model_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  source_snapshot_hash TEXT NOT NULL,
  proposal_json JSONB NOT NULL,
  uncertainties JSONB NOT NULL DEFAULT '[]'::jsonb,
  usage_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'in_review', 'rejected', 'accepted_as_context')),
  reviewer_notes TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_classical_context_spans_verses
  ON classical_context_spans (context_block_key, verse_start, verse_end);

CREATE INDEX IF NOT EXISTS idx_classical_context_premises_lookup
  ON classical_context_premises (premise_type, applies_verse_start, applies_verse_end);

CREATE INDEX IF NOT EXISTS idx_classical_context_ai_review
  ON classical_context_ai_proposals (status, context_block_key, created_at);
