ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS chat_tier TEXT NOT NULL DEFAULT 'standard';

CREATE INDEX IF NOT EXISTS idx_chat_messages_tier
    ON chat_messages (chat_tier);
