from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import sqlite3
from datetime import datetime
from auth import get_current_user

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

router = APIRouter()

def get_db_connection():
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/admin/chat/history/{user_id}")
async def get_user_chat_history(user_id: int, current_user: dict = Depends(require_admin)):
    """Get chat history for a specific user (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all sessions for the user
        cursor.execute("""
            SELECT session_id, created_at, 
                   (SELECT content FROM chat_messages 
                    WHERE session_id = cs.session_id 
                    AND sender = 'user' 
                    ORDER BY timestamp ASC LIMIT 1) as preview
            FROM chat_sessions cs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row['session_id'],
                'created_at': row['created_at'],
                'preview': row['preview'][:100] + '...' if row['preview'] and len(row['preview']) > 100 else row['preview']
            })
        
        conn.close()
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@router.get("/admin/chat/all-history")
async def get_all_chat_history(current_user: dict = Depends(require_admin)):
    """Get chat history for all users (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all sessions with user info
        cursor.execute("""
            SELECT cs.session_id, cs.user_id, cs.created_at, u.name, u.phone,
                   (SELECT content FROM chat_messages 
                    WHERE session_id = cs.session_id 
                    AND sender = 'user' 
                    ORDER BY timestamp ASC LIMIT 1) as preview
            FROM chat_sessions cs
            LEFT JOIN users u ON cs.user_id = u.userid
            ORDER BY cs.created_at DESC
            LIMIT 100
        """)
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row['session_id'],
                'user_id': row['user_id'],
                'user_name': row['name'],
                'user_phone': row['phone'],
                'created_at': row['created_at'],
                'preview': row['preview'][:100] + '...' if row['preview'] and len(row['preview']) > 100 else row['preview']
            })
        
        conn.close()
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all chat history: {str(e)}")

@router.get("/admin/chat/session/{session_id}")
async def get_session_details(session_id: str, current_user: dict = Depends(require_admin)):
    """Get detailed messages for a specific session (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all messages for the session
        cursor.execute("""
            SELECT sender, content, timestamp 
            FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """, (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'sender': row['sender'],
                'content': row['content'],
                'timestamp': row['timestamp']
            })
        
        conn.close()
        return {
            "session_id": session['session_id'],
            "user_id": session['user_id'],
            "created_at": session['created_at'],
            "messages": messages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session details: {str(e)}")