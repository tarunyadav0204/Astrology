CREATE TABLE IF NOT EXISTS chat_answer_evidence_audits (
    message_id BIGINT PRIMARY KEY REFERENCES chat_messages(message_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    evidence_brief TEXT NOT NULL DEFAULT '{}',
    evaluator_result TEXT,
    evaluator_provider TEXT,
    evaluator_model TEXT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
