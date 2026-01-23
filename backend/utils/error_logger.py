"""
Shared error logging utility for chat errors
"""
import sqlite3
import json
import traceback

def log_chat_error(user_id, username, phone, error, user_question, birth_data=None, error_source='backend'):
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
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO chat_error_logs 
            (user_id, username, phone, error_type, error_message, user_question, 
             stack_trace, platform, error_source, birth_data_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            username,
            phone,
            type(error).__name__,
            str(error),
            user_question,
            stack_trace,
            error_source,
            error_source,
            birth_context
        ))
        
        conn.commit()
        conn.close()
        
        print(f"🚨 ERROR LOGGED: {type(error).__name__} for user {username}")
        return True
        
    except Exception as log_error:
        print(f"⚠️ Failed to log error: {log_error}")
        return False
