from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import sqlite3
import json
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
        
        # Get new system sessions
        cursor.execute("""
            SELECT cs.session_id, cs.user_id, cs.created_at, u.name, u.phone,
                   (SELECT content FROM chat_messages 
                    WHERE session_id = cs.session_id 
                    AND sender = 'user' 
                    ORDER BY timestamp ASC LIMIT 1) as preview,
                   'new' as system_type
            FROM chat_sessions cs
            LEFT JOIN users u ON cs.user_id = u.userid
            WHERE cs.created_at >= datetime('now', '-30 days')
            ORDER BY cs.created_at DESC
        """)
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row['session_id'],
                'user_id': row['user_id'],
                'user_name': row['name'],
                'user_phone': row['phone'],
                'created_at': row['created_at'],
                'preview': row['preview'][:100] + '...' if row['preview'] and len(row['preview']) > 100 else row['preview'],
                'system_type': row['system_type']
            })
        
        # Get old system conversations
        cursor.execute("""
            SELECT cc.birth_hash, cc.conversation_data, cc.updated_at,
                   'old' as system_type
            FROM chat_conversations cc
            WHERE cc.updated_at >= datetime('now', '-30 days')
            ORDER BY cc.updated_at DESC
        """)
        
        for row in cursor.fetchall():
            try:
                conv_data = json.loads(row['conversation_data'])
                messages = conv_data.get('messages', [])
                if messages:
                    first_question = messages[0].get('question', 'Chat conversation')
                    sessions.append({
                        'session_id': row['birth_hash'],
                        'user_id': 'unknown',
                        'user_name': f'Legacy User #{row["birth_hash"][:8]}',
                        'user_phone': 'Legacy System',
                        'created_at': row['updated_at'],
                        'preview': first_question[:100] + '...' if len(first_question) > 100 else first_question,
                        'system_type': row['system_type']
                    })
            except:
                pass
        
        # Sort all sessions by date
        sessions.sort(key=lambda x: x['created_at'], reverse=True)
        
        conn.close()
        return {"sessions": sessions[:500]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all chat history: {str(e)}")

@router.get("/admin/chat/session/{session_id}")
async def get_session_details(session_id: str, current_user: dict = Depends(require_admin)):
    """Get detailed messages for a specific session (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First try new system
        cursor.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,))
        session = cursor.fetchone()
        
        if session:
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
        
        # Try legacy system
        cursor.execute("SELECT * FROM chat_conversations WHERE birth_hash = ?", (session_id,))
        legacy_conv = cursor.fetchone()
        
        if legacy_conv:
            try:
                conv_data = json.loads(legacy_conv['conversation_data'])
                messages = []
                
                for msg in conv_data.get('messages', []):
                    if msg.get('question'):
                        messages.append({
                            'sender': 'user',
                            'content': msg['question'],
                            'timestamp': msg.get('timestamp', legacy_conv['updated_at'])
                        })
                    
                    if msg.get('response'):
                        messages.append({
                            'sender': 'assistant',
                            'content': msg['response'],
                            'timestamp': msg.get('timestamp', legacy_conv['updated_at'])
                        })
                
                conn.close()
                return {
                    "session_id": session_id,
                    "user_id": "legacy",
                    "created_at": legacy_conv['updated_at'],
                    "messages": messages
                }
            except Exception:
                pass
        
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session details: {str(e)}")