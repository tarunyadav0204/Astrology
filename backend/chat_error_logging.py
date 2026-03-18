from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
from auth import get_current_user
from db import get_conn, execute

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

    # Create a simple Exception instance; we record the logical error type
    # separately instead of mutating the built-in Exception class.
    error = Exception(error_log.error_message)

    success = log_chat_error(
        current_user.userid,
        current_user.name,
        current_user.phone,
        error,
        error_log.user_question,
        None,
        'mobile',
        error_log.error_type,
    )
    
    return {"success": success}

@router.get("/admin/chat-errors")
async def get_chat_errors(limit: int = 100, source: str = 'all', current_user = Depends(get_current_user)):
    """Get recent chat errors (admin only)"""
    if current_user.role != 'admin':
        return {"errors": []}
    
    try:
        with get_conn() as conn:
            if source == 'all':
                cur = execute(
                    conn,
                    """
                    SELECT id, username, phone, error_type, error_message, user_question,
                           platform, error_source, stack_trace, birth_data_context, created_at
                    FROM chat_error_logs
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            else:
                cur = execute(
                    conn,
                    """
                    SELECT id, username, phone, error_type, error_message, user_question,
                           platform, error_source, stack_trace, birth_data_context, created_at
                    FROM chat_error_logs
                    WHERE error_source = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (source, limit),
                )
            rows = cur.fetchall() or []

        errors = []
        for row in rows:
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
        return {"errors": errors}
        
    except Exception as e:
        print(f"Failed to fetch chat errors: {e}")
        return {"errors": []}
