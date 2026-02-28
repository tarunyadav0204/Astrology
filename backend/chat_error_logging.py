from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sqlite3
import json
from auth import get_current_user

router = APIRouter()

class ChatErrorLog(BaseModel):
    error_type: str
    error_message: str
    user_question: Optional[str] = None
    stack_trace: Optional[str] = None
    platform: str = 'mobile'

@router.post("/chat/log-error")
async def log_chat_error_endpoint(error_log: ChatErrorLog, current_user = Depends(get_current_user)):
    """Log chat errors for developer monitoring.
    Note: Requires auth; if the client error is due to 401/expired token or network,
    this request may fail and the error will not be stored. Backend errors are logged
    in process_gemini_response and gemini_chat_analyzer."""
    from utils.error_logger import log_chat_error
    
    error = Exception(error_log.error_message)
    error.__class__.__name__ = error_log.error_type
    
    success = log_chat_error(
        current_user.userid,
        current_user.name,
        current_user.phone,
        error,
        error_log.user_question,
        None,
        'mobile'
    )
    
    return {"success": success}

@router.get("/admin/chat-errors")
async def get_chat_errors(limit: int = 100, source: str = 'all', current_user = Depends(get_current_user)):
    """Get recent chat errors (admin only)"""
    if current_user.role != 'admin':
        return {"errors": []}
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        if source == 'all':
            cursor.execute("""
                SELECT id, username, phone, error_type, error_message, user_question, 
                       platform, error_source, stack_trace, birth_data_context, created_at
                FROM chat_error_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT id, username, phone, error_type, error_message, user_question, 
                       platform, error_source, stack_trace, birth_data_context, created_at
                FROM chat_error_logs
                WHERE error_source = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (source, limit))
        
        errors = []
        for row in cursor.fetchall():
            errors.append({
                'id': row[0],
                'username': row[1],
                'phone': row[2],
                'error_type': row[3],
                'error_message': row[4],
                'user_question': row[5],
                'platform': row[6],
                'error_source': row[7],
                'stack_trace': row[8],
                'birth_data_context': row[9],
                'created_at': row[10]
            })
        
        conn.close()
        return {"errors": errors}
        
    except Exception as e:
        print(f"Failed to fetch chat errors: {e}")
        return {"errors": []}
