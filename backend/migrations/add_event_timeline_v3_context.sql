ALTER TABLE event_timeline_jobs
    ADD COLUMN IF NOT EXISTS context_fingerprint TEXT;

COMMENT ON COLUMN event_timeline_jobs.context_fingerprint IS
    'Hash of the user-fact context used by Accuracy V3; prevents stale personalized cache reuse.';
