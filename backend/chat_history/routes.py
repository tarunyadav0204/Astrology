"""
Chat History API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
import sqlite3
import uuid
from auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat_history"])

def init_chat_tables():
    """Initialize chat history tables"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (userid)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL CHECK (sender IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    
    # Add indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON chat_sessions (created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages (session_id)')
    
    conn.commit()
    conn.close()

@router.post("/session")
async def create_chat_session(current_user = Depends(get_current_user)):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO chat_sessions (session_id, user_id) VALUES (?, ?)",
        (session_id, current_user.userid)
    )
    
    conn.commit()
    conn.close()
    
    return {"session_id": session_id}

@router.post("/message")
async def save_chat_message(request: dict, current_user = Depends(get_current_user)):
    """Save a chat message"""
    session_id = request.get("session_id")
    sender = request.get("sender")  # 'user' or 'assistant'
    content = request.get("content")
    
    if not all([session_id, sender, content]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Verify session belongs to user
    cursor.execute(
        "SELECT user_id FROM chat_sessions WHERE session_id = ?",
        (session_id,)
    )
    session = cursor.fetchone()
    
    if not session or session[0] != current_user.userid:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    
    cursor.execute(
        "INSERT INTO chat_messages (session_id, sender, content) VALUES (?, ?, ?)",
        (session_id, sender, content)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Message saved"}

@router.get("/history")
async def get_chat_history(current_user = Depends(get_current_user)):
    """Get user's chat session history"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            cs.session_id,
            cs.created_at,
            cm.content as first_message
        FROM chat_sessions cs
        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id 
            AND cm.sender = 'user'
            AND cm.message_id = (
                SELECT MIN(message_id) 
                FROM chat_messages 
                WHERE session_id = cs.session_id AND sender = 'user'
            )
        WHERE cs.user_id = ?
        ORDER BY cs.created_at DESC
    ''', (current_user.userid,))
    
    sessions = cursor.fetchall()
    conn.close()
    
    history = []
    for session in sessions:
        history.append({
            "session_id": session[0],
            "created_at": session[1],
            "preview": session[2][:100] + "..." if session[2] and len(session[2]) > 100 else session[2]
        })
    
    return {"sessions": history}

@router.get("/session/{session_id}")
async def get_chat_session(session_id: str, current_user = Depends(get_current_user)):
    """Get full conversation for a session"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Verify session belongs to user
    cursor.execute(
        "SELECT user_id FROM chat_sessions WHERE session_id = ?",
        (session_id,)
    )
    session = cursor.fetchone()
    
    if not session or session[0] != current_user.userid:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    
    cursor.execute('''
        SELECT sender, content, timestamp
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    ''', (session_id,))
    
    messages = cursor.fetchall()
    conn.close()
    
    conversation = []
    for msg in messages:
        conversation.append({
            "sender": msg[0],
            "content": msg[1],
            "timestamp": msg[2]
        })
    
    return {"session_id": session_id, "messages": conversation}

@router.delete("/cleanup")
async def cleanup_old_chats():
    """Clean up chats older than 1 month (admin only)"""
    cutoff_date = datetime.now() - timedelta(days=30)
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Delete old messages first (foreign key constraint)
    cursor.execute('''
        DELETE FROM chat_messages 
        WHERE session_id IN (
            SELECT session_id FROM chat_sessions 
            WHERE created_at < ?
        )
    ''', (cutoff_date,))
    
    # Delete old sessions
    cursor.execute(
        "DELETE FROM chat_sessions WHERE created_at < ?",
        (cutoff_date,)
    )
    
    deleted_sessions = cursor.rowcount
    conn.commit()
    conn.close()
    
    return {"message": f"Cleaned up {deleted_sessions} old sessions"}