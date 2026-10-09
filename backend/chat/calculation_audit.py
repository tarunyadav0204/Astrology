"""Admin-only request/response audit; no model reasoning or credentials."""
import json
from db import execute

DDL = '''CREATE TABLE IF NOT EXISTS chat_calculation_audits (
 message_id BIGINT PRIMARY KEY REFERENCES chat_messages(message_id) ON DELETE CASCADE,
 payload JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)'''

def store_audit(conn, message_id, payload):
    if not payload:
        return
    execute(conn, DDL)
    execute(conn, '''INSERT INTO chat_calculation_audits(message_id,payload) VALUES (%s,%s::jsonb)
        ON CONFLICT(message_id) DO UPDATE SET payload=EXCLUDED.payload''',
        (message_id, json.dumps(payload, default=str, ensure_ascii=False)))

def read_audit(conn, message_id):
    exists = execute(conn, 'SELECT message_id FROM chat_messages WHERE message_id=%s', (message_id,)).fetchone()
    if not exists:
        return None
    table = execute(conn, "SELECT to_regclass('chat_calculation_audits')").fetchone()
    if not table or not table[0]:
        return {}
    row = execute(conn, 'SELECT payload FROM chat_calculation_audits WHERE message_id=%s', (message_id,)).fetchone()
    if not row:
        return {}
    return json.loads(row[0]) if isinstance(row[0], str) else row[0]
