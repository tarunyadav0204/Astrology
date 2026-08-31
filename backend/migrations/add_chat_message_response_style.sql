-- Snapshot the effective answer presentation style on every chat turn.
-- NULL identifies historical messages created before this migration.
ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS response_style TEXT;

ALTER TABLE chat_messages
    DROP CONSTRAINT IF EXISTS chat_messages_response_style_check;

ALTER TABLE chat_messages
    ADD CONSTRAINT chat_messages_response_style_check
    CHECK (response_style IS NULL OR response_style IN ('simple', 'technical'));
