-- Source-first catalogue for scanned classical works such as Deva Keralam.
--
-- These tables are deliberately disconnected from runtime chart/chat clients.
-- Imported OCR is evidence for review; it cannot become an executable rule
-- until a reviewed classical_rule_version is explicitly published.

ALTER TABLE classical_editions
  ADD COLUMN IF NOT EXISTS volume_label TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS translator TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS publication_year INTEGER,
  ADD COLUMN IF NOT EXISTS page_count INTEGER,
  ADD COLUMN IF NOT EXISTS source_file_name TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS import_metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS classical_source_import_runs (
  import_run_key TEXT PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES classical_editions(edition_key),
  source_document_hash TEXT NOT NULL,
  source_file_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  page_start INTEGER NOT NULL CHECK (page_start > 0),
  page_end INTEGER NOT NULL CHECK (page_end >= page_start),
  pages_completed INTEGER NOT NULL DEFAULT 0 CHECK (pages_completed >= 0),
  pages_failed INTEGER NOT NULL DEFAULT 0 CHECK (pages_failed >= 0),
  options JSONB NOT NULL DEFAULT '{}'::jsonb,
  page_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
  error_message TEXT NOT NULL DEFAULT '',
  started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMPTZ
);

ALTER TABLE classical_source_import_runs
  ADD COLUMN IF NOT EXISTS page_errors JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS classical_source_pages (
  source_page_id BIGSERIAL PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES classical_editions(edition_key),
  pdf_page INTEGER NOT NULL CHECK (pdf_page > 0),
  printed_page_label TEXT NOT NULL DEFAULT '',
  chapter_label TEXT NOT NULL DEFAULT '',
  image_object_key TEXT NOT NULL DEFAULT '',
  image_hash TEXT NOT NULL DEFAULT '',
  source_document_hash TEXT NOT NULL,
  raw_ocr TEXT NOT NULL DEFAULT '',
  corrected_text TEXT NOT NULL DEFAULT '',
  ocr_engine TEXT NOT NULL DEFAULT '',
  ocr_languages TEXT NOT NULL DEFAULT '',
  ocr_confidence NUMERIC(5, 4),
  ocr_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (ocr_status IN ('pending', 'processing', 'complete', 'failed', 'not_requested')),
  review_status TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK (review_status IN ('unreviewed', 'in_review', 'verified', 'rejected')),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  last_import_run_key TEXT REFERENCES classical_source_import_runs(import_run_key),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (edition_key, pdf_page)
);

CREATE TABLE IF NOT EXISTS classical_context_blocks (
  context_block_key TEXT PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES classical_editions(edition_key),
  title TEXT NOT NULL,
  pdf_page_start INTEGER NOT NULL CHECK (pdf_page_start > 0),
  pdf_page_end INTEGER NOT NULL CHECK (pdf_page_end >= pdf_page_start),
  verse_start INTEGER,
  verse_end INTEGER,
  inherited_context JSONB NOT NULL DEFAULT '{}'::jsonb,
  context_status TEXT NOT NULL DEFAULT 'candidate'
    CHECK (context_status IN ('candidate', 'review', 'verified', 'rejected')),
  reviewer_notes TEXT NOT NULL DEFAULT '',
  content_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE classical_passages
  ADD COLUMN IF NOT EXISTS context_block_key TEXT REFERENCES classical_context_blocks(context_block_key),
  ADD COLUMN IF NOT EXISTS pdf_page_start INTEGER,
  ADD COLUMN IF NOT EXISTS pdf_page_end INTEGER,
  ADD COLUMN IF NOT EXISTS printed_page_start TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS printed_page_end TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS source_text TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS translation_text TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS editor_notes TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS textual_confidence TEXT NOT NULL DEFAULT 'unreviewed',
  ADD COLUMN IF NOT EXISTS executable_status TEXT NOT NULL DEFAULT 'catalogued',
  ADD COLUMN IF NOT EXISTS content_hash TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS classical_passage_anchors (
  passage_key TEXT NOT NULL REFERENCES classical_passages(passage_key) ON DELETE CASCADE,
  anchor_type TEXT NOT NULL,
  anchor_value TEXT NOT NULL,
  provenance TEXT NOT NULL DEFAULT 'reviewer',
  confidence NUMERIC(5, 4),
  PRIMARY KEY (passage_key, anchor_type, anchor_value)
);

CREATE TABLE IF NOT EXISTS classical_rule_anchors (
  rule_key TEXT NOT NULL,
  rule_version INTEGER NOT NULL,
  anchor_type TEXT NOT NULL,
  anchor_value TEXT NOT NULL,
  PRIMARY KEY (rule_key, rule_version, anchor_type, anchor_value),
  FOREIGN KEY (rule_key, rule_version)
    REFERENCES classical_rule_versions(rule_key, version) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS classical_rule_tests (
  test_key TEXT PRIMARY KEY,
  rule_key TEXT NOT NULL,
  rule_version INTEGER NOT NULL,
  title TEXT NOT NULL,
  chart_facts JSONB NOT NULL,
  expected_match BOOLEAN NOT NULL,
  expected_outputs JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'disabled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (rule_key, rule_version)
    REFERENCES classical_rule_versions(rule_key, version) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_classical_source_pages_review
  ON classical_source_pages (edition_key, review_status, pdf_page);

CREATE INDEX IF NOT EXISTS idx_classical_source_pages_ocr
  ON classical_source_pages (edition_key, ocr_status, pdf_page);

CREATE INDEX IF NOT EXISTS idx_classical_context_blocks_pages
  ON classical_context_blocks (edition_key, pdf_page_start, pdf_page_end);

CREATE INDEX IF NOT EXISTS idx_classical_passage_anchors_lookup
  ON classical_passage_anchors (anchor_type, anchor_value, passage_key);

CREATE INDEX IF NOT EXISTS idx_classical_rule_anchors_lookup
  ON classical_rule_anchors (anchor_type, anchor_value, rule_key, rule_version);

CREATE OR REPLACE VIEW classical_source_coverage AS
SELECT
  edition.edition_key,
  edition.page_count AS expected_pages,
  COUNT(DISTINCT source_page.pdf_page) AS catalogued_pages,
  COUNT(DISTINCT source_page.pdf_page) FILTER (
    WHERE source_page.ocr_status = 'complete'
  ) AS ocr_complete_pages,
  COUNT(DISTINCT source_page.pdf_page) FILTER (
    WHERE source_page.review_status = 'verified'
  ) AS verified_pages,
  COUNT(DISTINCT passage.passage_key) AS catalogued_passages,
  COUNT(DISTINCT passage.passage_key) FILTER (
    WHERE passage.executable_status = 'executable'
  ) AS executable_passages,
  COUNT(DISTINCT (source_link.rule_key, source_link.rule_version)) AS source_linked_rules
FROM classical_editions edition
LEFT JOIN classical_source_pages source_page
  ON source_page.edition_key = edition.edition_key
LEFT JOIN classical_passages passage
  ON passage.edition_key = edition.edition_key
LEFT JOIN classical_rule_source_links source_link
  ON source_link.passage_key = passage.passage_key
GROUP BY edition.edition_key, edition.page_count;

INSERT INTO classical_works (work_key, title, tradition)
VALUES ('deva_keralam', 'Deva Keralam (Chandra Kala Nadi)', 'nadi')
ON CONFLICT (work_key) DO UPDATE
SET title = EXCLUDED.title,
    tradition = EXCLUDED.tradition;

INSERT INTO classical_editions (
  edition_key,
  work_key,
  title,
  language,
  source_url,
  source_policy,
  numbering_note,
  volume_label,
  translator,
  source_file_name,
  import_metadata
)
VALUES (
  'deva_keralam_volume_1_scan',
  'deva_keralam',
  'Deva Keralam, Volume 1 (Chandra Kala Nadi)',
  'Sanskrit and English',
  'private://classical-sources/deva-keralam-volume-1',
  'internal_reference_only',
  'PDF page, printed page and verse numbering are stored separately; OCR is never authoritative.',
  'Volume 1',
  '',
  'Deva-Keralam-1-Chandrakala-Nadi.pdf',
  '{"prediction_gate":"reviewed_rules_only","copyright_visibility":"private"}'::jsonb
)
ON CONFLICT (edition_key) DO UPDATE
SET title = EXCLUDED.title,
    language = EXCLUDED.language,
    source_policy = EXCLUDED.source_policy,
    numbering_note = EXCLUDED.numbering_note,
    volume_label = EXCLUDED.volume_label,
    source_file_name = EXCLUDED.source_file_name,
    import_metadata = classical_editions.import_metadata || EXCLUDED.import_metadata;
