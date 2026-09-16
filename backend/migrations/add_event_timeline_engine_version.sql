ALTER TABLE event_timeline_jobs
ADD COLUMN IF NOT EXISTS engine_version TEXT;

CREATE INDEX IF NOT EXISTS idx_event_timeline_engine_version
ON event_timeline_jobs (user_id, birth_chart_id, selected_year, selected_month, engine_version, status);
