-- Admin issue / enhancement tracker (internal).
-- Applied automatically on backend startup via admin_issue_schema.ensure_admin_issues_schema().

CREATE TABLE IF NOT EXISTS admin_issues (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date DATE,
    screenshot_original_name TEXT,
    screenshot_storage_path TEXT,
    screenshot_mime TEXT,
    screenshot_size_bytes INTEGER,
    created_by_userid INTEGER REFERENCES users (userid) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_issue_comments (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES admin_issues (id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_by_userid INTEGER REFERENCES users (userid) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_issues_status_opened
    ON admin_issues (status, opened_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_issue_comments_issue_created
    ON admin_issue_comments (issue_id, created_at ASC);
