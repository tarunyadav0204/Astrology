-- Migration: Add Conversational Chat with Semantic Memory
-- Date: 2024-12-22
-- Description: Adds clarification support and user facts storage

-- 1. Add message_type column to chat_messages
ALTER TABLE chat_messages ADD COLUMN message_type TEXT DEFAULT 'answer';

-- 2. Create conversation_state table
CREATE TABLE IF NOT EXISTS conversation_state (
    session_id TEXT PRIMARY KEY,
    clarification_count INTEGER DEFAULT 0,
    extracted_context TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
);

-- 3. Create user_facts table (stores facts per birth_chart_id)
CREATE TABLE IF NOT EXISTS user_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    birth_chart_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    fact TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (birth_chart_id) REFERENCES birth_charts (id)
);

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_facts_birth_chart ON user_facts (birth_chart_id);
CREATE INDEX IF NOT EXISTS idx_user_facts_category ON user_facts (category);

-- Verification queries (run after migration)
-- SELECT COUNT(*) FROM conversation_state;
-- SELECT COUNT(*) FROM user_facts;
-- SELECT message_type, COUNT(*) FROM chat_messages GROUP BY message_type;
