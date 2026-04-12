-- Native gate / third-party chart classifier metadata (JSON text)
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS gate_metadata TEXT;
