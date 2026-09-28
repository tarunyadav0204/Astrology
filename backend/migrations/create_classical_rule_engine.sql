-- Versioned source and rule catalogue for the classical reasoning engine.
-- Runtime evaluation remains code-first until a reviewed release is promoted;
-- no existing chart, chat or prediction client reads these tables.

CREATE TABLE IF NOT EXISTS classical_works (
  work_key TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  tradition TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classical_editions (
  edition_key TEXT PRIMARY KEY,
  work_key TEXT NOT NULL REFERENCES classical_works(work_key),
  title TEXT NOT NULL,
  language TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_policy TEXT NOT NULL,
  numbering_note TEXT NOT NULL DEFAULT '',
  content_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classical_passages (
  passage_key TEXT PRIMARY KEY,
  edition_key TEXT NOT NULL REFERENCES classical_editions(edition_key),
  chapter_number INTEGER NOT NULL,
  verse_start INTEGER NOT NULL,
  verse_end INTEGER NOT NULL,
  title TEXT NOT NULL,
  classification TEXT NOT NULL,
  operational_summary TEXT NOT NULL,
  source_text_status TEXT NOT NULL,
  review_status TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (edition_key, chapter_number, verse_start, verse_end)
);

CREATE TABLE IF NOT EXISTS classical_rule_versions (
  rule_key TEXT NOT NULL,
  version INTEGER NOT NULL,
  title TEXT NOT NULL,
  rule_type TEXT NOT NULL,
  scope TEXT NOT NULL,
  status TEXT NOT NULL,
  calculator_binding TEXT NOT NULL,
  expression JSONB NOT NULL DEFAULT '{}'::jsonb,
  topics JSONB NOT NULL DEFAULT '[]'::jsonb,
  notes JSONB NOT NULL DEFAULT '[]'::jsonb,
  content_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (rule_key, version)
);

CREATE TABLE IF NOT EXISTS classical_rule_source_links (
  rule_key TEXT NOT NULL,
  rule_version INTEGER NOT NULL,
  passage_key TEXT NOT NULL REFERENCES classical_passages(passage_key),
  relationship TEXT NOT NULL DEFAULT 'authority',
  PRIMARY KEY (rule_key, rule_version, passage_key),
  FOREIGN KEY (rule_key, rule_version)
    REFERENCES classical_rule_versions(rule_key, version)
);

CREATE TABLE IF NOT EXISTS classical_rule_releases (
  release_key TEXT PRIMARY KEY,
  work_key TEXT NOT NULL REFERENCES classical_works(work_key),
  status TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  released_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classical_rule_release_members (
  release_key TEXT NOT NULL REFERENCES classical_rule_releases(release_key),
  rule_key TEXT NOT NULL,
  rule_version INTEGER NOT NULL,
  PRIMARY KEY (release_key, rule_key),
  FOREIGN KEY (rule_key, rule_version)
    REFERENCES classical_rule_versions(rule_key, version)
);

CREATE INDEX IF NOT EXISTS idx_classical_passages_chapter
  ON classical_passages (edition_key, chapter_number, verse_start);

CREATE INDEX IF NOT EXISTS idx_classical_rule_versions_status
  ON classical_rule_versions (status, rule_key, version DESC);
