"""Durable audit trail for selected-answer summaries, including cache hits."""
import json
import uuid
from db import execute


def ensure_table(conn):
    execute(conn, '''CREATE TABLE IF NOT EXISTS chat_tool_activity (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
        session_id TEXT REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
        tool TEXT NOT NULL,
        state JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)''', ())
    execute(conn, 'CREATE INDEX IF NOT EXISTS chat_tool_activity_user_created_idx ON chat_tool_activity(user_id, created_at DESC)', ())


def begin_summary(conn, user_id, session_id, state):
    ensure_table(conn)
    activity_id = str(uuid.uuid4())
    execute(conn, '''INSERT INTO chat_tool_activity(id,user_id,session_id,tool,state)
        VALUES (%s,%s,%s,'summary',%s::jsonb)''', (activity_id,user_id,session_id,json.dumps(state,ensure_ascii=False)))
    # Commit before acquiring the cache lock so in-flight work is visible in Admin.
    conn.commit()
    return activity_id


def update_summary(conn, activity_id, state):
    execute(conn, '''UPDATE chat_tool_activity SET state=%s::jsonb,updated_at=CURRENT_TIMESTAMP
        WHERE id=%s''', (json.dumps(state,ensure_ascii=False),activity_id))


def response_usage(response):
    usage = getattr(response, 'usage', None)
    if usage is None:
        return None
    if hasattr(usage, 'model_dump'):
        usage = usage.model_dump()
    elif not isinstance(usage, dict):
        usage = vars(usage)
    details = usage.get('input_tokens_details') or {}
    if not isinstance(details, dict):
        details = vars(details)
    return dict(input_tokens=max(0,int(usage.get('input_tokens') or 0)),
                output_tokens=max(0,int(usage.get('output_tokens') or 0)),
                cached_tokens=max(0,int(details.get('cached_tokens') or 0)))
