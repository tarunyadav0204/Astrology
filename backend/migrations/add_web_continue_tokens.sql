-- Reusable WhatsApp → PWA Credits continue links
CREATE TABLE IF NOT EXISTS web_continue_tokens (
    token TEXT PRIMARY KEY,
    userid INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_web_continue_tokens_userid_active
ON web_continue_tokens (userid)
WHERE revoked_at IS NULL;
