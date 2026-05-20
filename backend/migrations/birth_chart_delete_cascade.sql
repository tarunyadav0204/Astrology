-- Ensure birth chart deletes cascade to dependent rows (Postgres).
-- Safe to run multiple times: drops and recreates FKs with ON DELETE CASCADE.

ALTER TABLE user_facts
    DROP CONSTRAINT IF EXISTS user_facts_birth_chart_id_fkey;

ALTER TABLE user_facts
    ADD CONSTRAINT user_facts_birth_chart_id_fkey
    FOREIGN KEY (birth_chart_id) REFERENCES birth_charts (id) ON DELETE CASCADE;

ALTER TABLE event_timeline_jobs
    DROP CONSTRAINT IF EXISTS event_timeline_jobs_birth_chart_id_fkey;

ALTER TABLE event_timeline_jobs
    ADD CONSTRAINT event_timeline_jobs_birth_chart_id_fkey
    FOREIGN KEY (birth_chart_id) REFERENCES birth_charts (id) ON DELETE CASCADE;
