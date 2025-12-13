"""
Chat History API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timedelta
import sqlite3
import uuid
from auth import get_current_user

def sanitize_text(text):
    """Remove invalid Unicode characters and surrogates to prevent encoding attacks"""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    text = text.encode('utf-8', 'surrogatepass').decode('utf-8', 'ignore')
    text = text.replace('\0', '')
    return text.strip()

router = APIRouter(prefix="/chat-v2", tags=["chat_history"])

def init_chat_tables():
    """Initialize chat history tables with polling support"""
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
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'completed' CHECK (status IN ('processing', 'completed', 'failed', 'cancelled')),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    
    # Add status columns to existing table if they don't exist
    try:
        cursor.execute('ALTER TABLE chat_messages ADD COLUMN status TEXT DEFAULT "completed"')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE chat_messages ADD COLUMN started_at TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE chat_messages ADD COLUMN completed_at TIMESTAMP')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE chat_messages ADD COLUMN error_message TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Add indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON chat_sessions (created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages (session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_status ON chat_messages (status)')
    
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
        (session_id, sender, sanitize_text(content))
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Message saved"}

@router.get("/history")
async def get_chat_history(page: int = 1, limit: int = 20, current_user = Depends(get_current_user)):
    """Get user's chat session history with pagination"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM chat_sessions WHERE user_id = ?', (current_user.userid,))
    total_count = cursor.fetchone()[0]
    
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
        LIMIT ? OFFSET ?
    ''', (current_user.userid, limit, offset))
    
    sessions = cursor.fetchall()
    conn.close()
    
    history = []
    for session in sessions:
        history.append({
            "session_id": session[0],
            "created_at": session[1],
            "preview": session[2][:100] + "..." if session[2] and len(session[2]) > 100 else session[2]
        })
    
    return {
        "sessions": history,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "has_more": offset + limit < total_count
        }
    }

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

@router.post("/ask")
async def ask_question_async(request: dict, background_tasks: BackgroundTasks, current_user = Depends(get_current_user)):
    """Start async chat processing - returns immediately with message_id for polling"""
    from credits.credit_service import CreditService
    
    # Validate required fields
    session_id = request.get("session_id")
    question = request.get("question")
    birth_details = request.get("birth_details")
    
    if not session_id or not question or not birth_details:
        raise HTTPException(status_code=422, detail="Missing required fields: session_id, question, and birth_details")
    
    # Optional fields with defaults
    language = request.get("language", "english")
    response_style = request.get("response_style", "detailed")
    premium_analysis = request.get("premium_analysis", False)
    
    # Check credit cost and user balance
    credit_service = CreditService()
    if premium_analysis:
        chat_cost = credit_service.get_credit_setting('premium_chat_cost')
    else:
        chat_cost = credit_service.get_credit_setting('chat_question_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    print(f"💳 CREDIT CHECK (chat-v2):")
    print(f"   User ID: {current_user.userid}")
    print(f"   Premium Analysis: {premium_analysis}")
    print(f"   Chat cost: {chat_cost} credits")
    print(f"   User balance: {user_balance} credits")
    
    if user_balance < chat_cost:
        analysis_type = "Premium Deep Analysis" if premium_analysis else "Standard Analysis"
        print(f"❌ INSUFFICIENT CREDITS: Need {chat_cost}, have {user_balance}")
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits for {analysis_type}. You need {chat_cost} credits but have {user_balance}."
        )
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Verify session belongs to user
    cursor.execute("SELECT user_id FROM chat_sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    if not session or session[0] != current_user.userid:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user question (sanitized)
    cursor.execute(
        "INSERT INTO chat_messages (session_id, sender, content, status, completed_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, "user", sanitize_text(question), "completed", datetime.now())
    )
    
    # Create processing assistant message
    cursor.execute(
        "INSERT INTO chat_messages (session_id, sender, content, status, started_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, "assistant", "", "processing", datetime.now())
    )
    
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Start background processing
    background_tasks.add_task(
        process_gemini_response,
        message_id, session_id, sanitize_text(question), current_user.userid, language, response_style, premium_analysis, birth_details, chat_cost
    )
    
    return {
        "message_id": message_id,
        "status": "processing",
        "message": "Analyzing your chart..."
    }

@router.get("/status/{message_id}")
async def check_message_status(message_id: int, current_user = Depends(get_current_user)):
    """Poll message status for async processing"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cm.status, cm.content, cm.error_message, cm.started_at, cm.completed_at, cs.user_id
        FROM chat_messages cm
        JOIN chat_sessions cs ON cm.session_id = cs.session_id
        WHERE cm.message_id = ?
    ''', (message_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")
    
    status, content, error_message, started_at, completed_at, user_id = result
    
    # Verify message belongs to user
    if user_id != current_user.userid:
        raise HTTPException(status_code=403, detail="Access denied")
    
    response = {"status": status}
    
    if status == "completed":
        response["content"] = content
        response["completed_at"] = completed_at
    elif status == "failed":
        response["error_message"] = error_message or "An error occurred while processing your request"
    elif status == "processing":
        response["started_at"] = started_at
        response["message"] = "Still analyzing your chart..."
    
    return response

async def process_gemini_response(message_id: int, session_id: str, question: str, user_id: int, language: str, response_style: str, premium_analysis: bool, birth_details: dict = None, chat_cost: int = 1):
    """Background task to process Gemini response"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from ai.gemini_chat_analyzer import GeminiChatAnalyzer
    from chat.chat_context_builder import ChatContextBuilder
    from credits.credit_service import CreditService
    
    try:
        # Use birth data from request (required)
        if not birth_details:
            raise Exception("Birth details are required for chat analysis")
        
        birth_data = birth_details
        
        # Build context
        context_builder = ChatContextBuilder()
        context = context_builder.build_complete_context(birth_data)
        
        # Get conversation history
        with sqlite3.connect('astrology.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sender, content FROM chat_messages 
                WHERE session_id = ? AND status = 'completed' AND content IS NOT NULL
                ORDER BY timestamp DESC LIMIT 6
            ''', (session_id,))
            
            history_rows = cursor.fetchall()
            history = []
            for i in range(0, len(history_rows), 2):
                if i + 1 < len(history_rows):
                    history.append({
                        "question": history_rows[i+1][1],
                        "response": history_rows[i][1]
                    })
        
        # Generate response
        analyzer = GeminiChatAnalyzer()
        result = await analyzer.generate_chat_response(
            user_question=question,
            astrological_context=context,
            conversation_history=history,
            language=language,
            response_style=response_style,
            premium_analysis=premium_analysis
        )
        
        # Update database with result
        with sqlite3.connect('astrology.db') as conn:
            cursor = conn.cursor()
            
            if result.get('success'):
                # Deduct credits on successful response
                credit_service = CreditService()
                analysis_type = "Premium Deep Analysis" if premium_analysis else "Standard Chat"
                success = credit_service.spend_credits(
                    user_id, 
                    chat_cost, 
                    'chat_question', 
                    f"{analysis_type}: {question[:50]}..."
                )
                
                if success:
                    print(f"✅ CREDITS DEDUCTED: {chat_cost} credits for user {user_id}")
                    cursor.execute(
                        "UPDATE chat_messages SET content = ?, status = ?, completed_at = ? WHERE message_id = ?",
                        (sanitize_text(result['response']), "completed", datetime.now(), message_id)
                    )
                else:
                    print(f"❌ CREDIT DEDUCTION FAILED for user {user_id}")
                    cursor.execute(
                        "UPDATE chat_messages SET status = ?, error_message = ?, completed_at = ? WHERE message_id = ?",
                        ("failed", "Credit deduction failed. Please try again.", datetime.now(), message_id)
                    )
            else:
                error_msg = result.get('error', 'Unable to process your request at this time. Please try again.')
                cursor.execute(
                    "UPDATE chat_messages SET status = ?, error_message = ?, completed_at = ? WHERE message_id = ?",
                    ("failed", error_msg, datetime.now(), message_id)
                )
            
            conn.commit()
        
    except Exception as e:
        # Handle any errors with user-friendly message
        user_friendly_error = "I'm having trouble analyzing your chart right now. Please try again in a moment."
        
        with sqlite3.connect('astrology.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chat_messages SET status = ?, error_message = ?, completed_at = ? WHERE message_id = ?",
                ("failed", user_friendly_error, datetime.now(), message_id)
            )
            conn.commit()
        print(f"Error processing message {message_id}: {e}")
        import traceback
        traceback.print_exc()

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