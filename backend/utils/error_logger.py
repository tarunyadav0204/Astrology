"""
Shared error logging utility for chat errors
"""
import json
import traceback

from db import get_conn, execute


def log_chat_error(
    user_id,
    username,
    phone,
    error,
    user_question,
    birth_data=None,
    error_source='backend',
    error_type: str | None = None,
):
    """
    Log chat error to database
    
    Args:
        user_id: User ID
        username: Username
        phone: Phone number
        error: Exception object
        user_question: User's question
        birth_data: Optional birth data dict
        error_source: 'mobile' or 'backend'
    """
    try:
        stack_trace = traceback.format_exc()
        
        birth_context = None
        if birth_data:
            birth_context = json.dumps({
                'name': birth_data.get('name', ''),
                'date': birth_data.get('date', ''),
                'time': birth_data.get('time', ''),
                'place': birth_data.get('place', '')
            })
        
        # Prefer an explicit error_type string when provided (e.g. from mobile),
        # otherwise fall back to the Python exception class name.
        resolved_error_type = error_type or type(error).__name__

        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO chat_error_logs
                (user_id, username, phone, error_type, error_message, user_question,
                 stack_trace, platform, error_source, birth_data_context)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    username,
                    phone,
                    resolved_error_type,
                    str(error),
                    user_question,
                    stack_trace,
                    error_source,
                    error_source,
                    birth_context,
                ),
            )
            conn.commit()

        print(f"🚨 ERROR LOGGED: {resolved_error_type} for user {username}")
        return True
        
    except Exception as log_error:
        print(f"⚠️ Failed to log error: {log_error}")
        return False
