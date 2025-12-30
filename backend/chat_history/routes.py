"""
Chat History API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timedelta
import sqlite3
import uuid
import json
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
            birth_chart_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (userid),
            FOREIGN KEY (birth_chart_id) REFERENCES birth_charts (id)
        )
    ''')
    
    # Add birth_chart_id column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE chat_sessions ADD COLUMN birth_chart_id INTEGER')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_birth_chart ON chat_sessions (birth_chart_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON chat_sessions (created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages (session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_status ON chat_messages (status)')
    
    conn.commit()
    conn.close()

@router.post("/session")
async def create_chat_session(request: dict, current_user = Depends(get_current_user)):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    birth_chart_id = request.get("birth_chart_id")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO chat_sessions (session_id, user_id, birth_chart_id) VALUES (?, ?, ?)",
        (session_id, current_user.userid, birth_chart_id)
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
            cm.content as first_message,
            cs.birth_chart_id,
            bc.name as native_name
        FROM chat_sessions cs
        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id 
            AND cm.sender = 'user'
            AND cm.message_id = (
                SELECT MIN(message_id) 
                FROM chat_messages 
                WHERE session_id = cs.session_id AND sender = 'user'
            )
        LEFT JOIN birth_charts bc ON cs.birth_chart_id = bc.id
        WHERE cs.user_id = ?
        ORDER BY cs.created_at DESC
        LIMIT ? OFFSET ?
    ''', (current_user.userid, limit, offset))
    
    sessions = cursor.fetchall()
    conn.close()
    
    from encryption_utils import EncryptionManager
    encryptor = EncryptionManager()
    
    history = []
    for session in sessions:
        native_name = None
        if session[4]:  # If native_name exists
            try:
                native_name = encryptor.decrypt(session[4])
            except:
                native_name = session[4]  # Use as-is if decryption fails
        
        history.append({
            "session_id": session[0],
            "created_at": session[1],
            "preview": session[2][:100] + "..." if session[2] and len(session[2]) > 100 else session[2],
            "birth_chart_id": session[3],
            "native_name": native_name
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
        SELECT message_id, sender, content, timestamp, terms, glossary
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    ''', (session_id,))
    
    messages = cursor.fetchall()
    conn.close()
    
    conversation = []
    for msg in messages:
        message_data = {
            "message_id": msg[0],
            "sender": msg[1],
            "content": msg[2],
            "timestamp": msg[3]
        }
        
        # Add terms and glossary if they exist
        if msg[4]:  # terms
            try:
                message_data["terms"] = json.loads(msg[4])
            except:
                message_data["terms"] = []
        else:
            message_data["terms"] = []
            
        if msg[5]:  # glossary
            try:
                message_data["glossary"] = json.loads(msg[5])
            except:
                message_data["glossary"] = []
        else:
            message_data["glossary"] = []
            
        conversation.append(message_data)
    
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
    partnership_mode = request.get("partnership_mode", False) or request.get("partnershipMode", False)
    partner_birth_details = request.get("partner_birth_details") or {
        'name': request.get('partner_name') or request.get('partnerName'),
        'date': request.get('partner_date') or request.get('partnerDate'),
        'time': request.get('partner_time') or request.get('partnerTime'),
        'place': request.get('partner_place') or request.get('partnerPlace'),
        'latitude': request.get('partner_latitude') or request.get('partnerLatitude'),
        'longitude': request.get('partner_longitude') or request.get('partnerLongitude'),
        'timezone': request.get('partner_timezone') or request.get('partnerTimezone'),
        'gender': request.get('partner_gender') or request.get('partnerGender')
    } if partnership_mode else None
    
    # Check credit cost and user balance
    credit_service = CreditService()
    if partnership_mode:
        base_cost = credit_service.get_credit_setting('chat_question_cost')
        chat_cost = base_cost * 2  # Partnership mode costs double
    elif premium_analysis:
        chat_cost = credit_service.get_credit_setting('premium_chat_cost')
    else:
        chat_cost = credit_service.get_credit_setting('chat_question_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    print(f"💳 CREDIT CHECK (chat-v2):")
    print(f"   User ID: {current_user.userid}")
    print(f"   Partnership Mode: {partnership_mode}")
    print(f"   Premium Analysis: {premium_analysis}")
    print(f"   Chat cost: {chat_cost} credits")
    print(f"   User balance: {user_balance} credits")
    
    if user_balance < chat_cost:
        if partnership_mode:
            analysis_type = "Partnership Analysis"
        elif premium_analysis:
            analysis_type = "Premium Deep Analysis"
        else:
            analysis_type = "Standard Analysis"
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
    
    user_message_id = cursor.lastrowid
    print(f"💾 User message saved with ID: {user_message_id}")
    
    # Create processing assistant message
    cursor.execute(
        "INSERT INTO chat_messages (session_id, sender, content, status, started_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, "assistant", "", "processing", datetime.now())
    )
    
    assistant_message_id = cursor.lastrowid
    print(f"💾 Assistant message saved with ID: {assistant_message_id}")
    conn.commit()
    conn.close()
    
    # Start background processing
    background_tasks.add_task(
        process_gemini_response,
        assistant_message_id, session_id, sanitize_text(question), current_user.userid, language, response_style, premium_analysis, birth_details, chat_cost, partnership_mode, partner_birth_details
    )
    
    return {
        "user_message_id": user_message_id,
        "message_id": assistant_message_id,
        "status": "processing",
        "message": "Analyzing your chart..."
    }
    print(f"🚀 Returning IDs - User: {user_message_id}, Assistant: {assistant_message_id}")

@router.get("/status/{message_id}")
async def check_message_status(message_id: int, current_user = Depends(get_current_user)):
    """Poll message status for async processing"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cm.status, cm.content, cm.error_message, cm.started_at, cm.completed_at, cs.user_id, cm.message_type, cm.terms, cm.glossary
        FROM chat_messages cm
        JOIN chat_sessions cs ON cm.session_id = cs.session_id
        WHERE cm.message_id = ?
    ''', (message_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")
    
    status, content, error_message, started_at, completed_at, user_id, message_type, terms, glossary = result
    
    # Verify message belongs to user
    if user_id != current_user.userid:
        raise HTTPException(status_code=403, detail="Access denied")
    
    response = {"status": status, "message_type": message_type or "answer"}
    
    if status == "completed":
        response["content"] = content
        response["completed_at"] = completed_at
        
        # Add terms and glossary if they exist
        if terms:
            try:
                response["terms"] = json.loads(terms)
            except:
                response["terms"] = []
        else:
            response["terms"] = []
            
        if glossary:
            try:
                response["glossary"] = json.loads(glossary)
            except:
                response["glossary"] = {}
        else:
            response["glossary"] = {}
            
    elif status == "failed":
        response["error_message"] = error_message or "An error occurred while processing your request"
    elif status == "processing":
        response["started_at"] = started_at
        response["message"] = "Still analyzing your chart..."
    
    return response

async def process_gemini_response(message_id: int, session_id: str, question: str, user_id: int, language: str, response_style: str, premium_analysis: bool, birth_details: dict = None, chat_cost: int = 1, partnership_mode: bool = False, partner_birth_details: dict = None):
    """Background task to process Gemini response"""
    import sys
    import os
    import json
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from ai.gemini_chat_analyzer import GeminiChatAnalyzer
    from chat.chat_context_builder import ChatContextBuilder
    from credits.credit_service import CreditService
    from ai.intent_router import IntentRouter
    from chat.fact_extractor import FactExtractor
    
    try:
        # Get birth_chart_id from session
        with sqlite3.connect('astrology.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT birth_chart_id FROM chat_sessions WHERE session_id = ?", (session_id,))
            session_data = cursor.fetchone()
            birth_chart_id = session_data[0] if session_data else None
        
        # Use birth data from request (required)
        if not birth_details:
            raise Exception("Birth details are required for chat analysis")
        
        birth_data = birth_details
        
        # Validate partnership mode data
        if partnership_mode and partner_birth_details:
            required_fields = ['name', 'date', 'time', 'latitude', 'longitude']
            for field in required_fields:
                if not partner_birth_details.get(field):
                    raise Exception(f"Partner {field} is required for partnership analysis")
            
            # Ensure time is not None
            if partner_birth_details.get('time') is None:
                raise Exception("Partner birth time cannot be empty for partnership analysis")
        
        # Build context
        context_builder = ChatContextBuilder()
        
        # Get conversation history for intent routing
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
            
            # Get conversation state
            cursor.execute("SELECT clarification_count, extracted_context FROM conversation_state WHERE session_id = ?", (session_id,))
            state_row = cursor.fetchone()
            clarification_count = state_row[0] if state_row else 0
            extracted_context = json.loads(state_row[1]) if state_row and state_row[1] else {}
        
        # === INTENT ROUTING ===
        import time
        routing_start = time.time()
        
        intent = {'status': 'READY', 'mode': 'birth', 'category': 'general', 'extracted_context': {}}  # Default
        
        if not partnership_mode:
            # Use AI to classify (Fast)
            print(f"\n{'='*80}")
            print(f"🛣️ ROUTING DECISION STARTED")
            print(f"{'='*80}")
            
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
                
                # Get conversation state
                cursor.execute("SELECT clarification_count FROM conversation_state WHERE session_id = ?", (session_id,))
                state_row = cursor.fetchone()
                clarification_count = state_row[0] if state_row else 0
            
            intent_router = IntentRouter()
            intent = await intent_router.classify_intent(question, history)
            
            print(f"🔍 CLARIFICATION CHECK:")
            print(f"   Intent status: {intent.get('status')}")
            print(f"   Clarification count: {clarification_count}")
            print(f"   Will clarify: {intent.get('status') == 'CLARIFY' and clarification_count < 2}")
            
            # Check if clarification needed and under limit
            if intent.get('status') == 'CLARIFY' and clarification_count < 2:
                print(f"✅ RETURNING CLARIFICATION QUESTION")
                # Return clarification question
                with sqlite3.connect('astrology.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE chat_messages SET content = ?, status = ?, message_type = ?, completed_at = ? WHERE message_id = ?",
                        (sanitize_text(intent.get('clarification_question', 'Could you provide more details?')), "completed", "clarification", datetime.now(), message_id)
                    )
                    
                    # Update conversation state
                    cursor.execute("""
                        INSERT INTO conversation_state (session_id, clarification_count, extracted_context)
                        VALUES (?, ?, ?)
                        ON CONFLICT(session_id) DO UPDATE SET 
                            clarification_count = clarification_count + 1,
                            extracted_context = ?,
                            last_updated = CURRENT_TIMESTAMP
                    """, (session_id, 1, json.dumps(intent.get('extracted_context', {})), json.dumps(intent.get('extracted_context', {}))))
                    
                    conn.commit()
                print(f"✅ CLARIFICATION SAVED TO DATABASE, EXITING EARLY")
                return  # Exit early, no chart calculation needed
            elif intent.get('status') == 'READY':
                # Reset clarification count when ready to answer
                with sqlite3.connect('astrology.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO conversation_state (session_id, clarification_count, extracted_context)
                        VALUES (?, ?, ?)
                        ON CONFLICT(session_id) DO UPDATE SET 
                            clarification_count = 0,
                            last_updated = CURRENT_TIMESTAMP
                    """, (session_id, 0, json.dumps(intent.get('extracted_context', {}))))
                    conn.commit()
                print(f"✅ RESET CLARIFICATION COUNT TO 0 (READY status)")
            
            routing_time = time.time() - routing_start
            print(f"✅ ROUTING DECISION COMPLETE: {intent['mode'].upper()} mode")
            print(f"Category: {intent.get('category', 'general')}")
            print(f"Routing time: {routing_time:.3f}s")
            print(f"{'='*80}\n")
        
        # Build context based on intent
        context_start = time.time()
        
        if partnership_mode and partner_birth_details:
            print(f"\n{'='*80}")
            print(f"👥 PARTNERSHIP MODE - Building synastry context")
            print(f"{'='*80}")
            print(f"Native: {birth_data.get('name')}")
            print(f"Partner: {partner_birth_details.get('name')}")
            context = context_builder.build_synastry_context(birth_data, partner_birth_details, question, intent)
            context_time = time.time() - context_start
            print(f"✅ Synastry context built in {context_time:.3f}s")
            print(f"{'='*80}\n")
            
        elif intent['mode'] == 'annual':
            # === ANNUAL MODE ===
            print(f"\n{'='*80}")
            print(f"📅 ANNUAL MODE ACTIVATED")
            print(f"{'='*80}")
            target_year = intent.get('year', datetime.now().year)
            print(f"Target year: {target_year}")
            
            # Convert intent router transit request to old format if needed
            requested_period = None
            if intent.get('needs_transits') and intent.get('transit_request'):
                tr = intent['transit_request']
                requested_period = {
                    'start_year': tr['startYear'],
                    'end_year': tr['endYear'],
                    'yearMonthMap': tr.get('yearMonthMap', {})
                }
                print(f"Transit period: {tr['startYear']}-{tr['endYear']}")
            
            # Use build_complete_context with intent_result to get transit data
            context = context_builder.build_complete_context(
                birth_data, question, None, requested_period, intent
            )
            
            # Add annual-specific data
            context['analysis_type'] = 'annual_forecast'
            context['focus_year'] = target_year
            
            context_time = time.time() - context_start
            print(f"✅ Annual context built in {context_time:.3f}s")
            print(f"{'='*80}\n")
            
        elif intent['mode'] == 'prashna':
            # === PRASHNA MODE ===
            print(f"\n{'='*80}")
            print(f"🔮 PRASHNA MODE ACTIVATED")
            print(f"{'='*80}")
            print(f"Question: {question}")
            print(f"Category: {intent.get('category', 'general')}")
            
            user_location = {
                'latitude': birth_data.get('latitude'),
                'longitude': birth_data.get('longitude'),
                'timezone': birth_data.get('timezone', 'Asia/Kolkata'),
                'place': birth_data.get('place', 'Query Location')
            }
            
            context = context_builder.build_prashna_context(
                user_location,
                question,
                intent.get('category', 'general')
            )
            
            context_time = time.time() - context_start
            print(f"✅ PRASHNA CONTEXT READY in {context_time:.3f}s")
            print(f"{'='*80}\n")
            
        else:
            # === BIRTH CHART MODE (Standard) ===
            print(f"\n{'='*80}")
            print(f"🔮 BIRTH CHART MODE (Standard)")
            print(f"{'='*80}")
            
            # Convert intent router transit request to old format if needed
            requested_period = None
            if intent.get('needs_transits') and intent.get('transit_request'):
                tr = intent['transit_request']
                requested_period = {
                    'start_year': tr['startYear'],
                    'end_year': tr['endYear'],
                    'yearMonthMap': tr.get('yearMonthMap', {})
                }
                print(f"Transit period: {tr['startYear']}-{tr['endYear']}")
            
            # Log divisional charts being requested
            if intent.get('divisional_charts'):
                print(f"Divisional charts requested: {intent['divisional_charts']}")
            
            context = context_builder.build_complete_context(
                birth_data, question, None, requested_period, intent
            )
            context_time = time.time() - context_start
            print(f"✅ Birth chart context built in {context_time:.3f}s")
            print(f"{'='*80}\n")
        
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
            
            # Get user facts if birth_chart_id exists
            user_facts = {}
            if birth_chart_id:
                fact_extractor = FactExtractor()
                user_facts = fact_extractor.get_facts(birth_chart_id)
        
        # Inject user facts into context
        if user_facts:
            context['user_facts'] = user_facts
        
        # Inject extracted context from clarifications
        if intent.get('extracted_context'):
            context['extracted_context'] = intent['extracted_context']
        
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
                # Use already parsed terms and glossary from GeminiChatAnalyzer
                terms = result.get('terms', [])
                glossary = result.get('glossary', {})
                
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
                        "UPDATE chat_messages SET content = ?, terms = ?, glossary = ?, status = ?, message_type = ?, completed_at = ? WHERE message_id = ?",
                        (
                            sanitize_text(result['response']), 
                            json.dumps(terms),
                            json.dumps(glossary),
                            "completed", 
                            "answer", 
                            datetime.now(), 
                            message_id
                        )
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
        
        # Extract facts AFTER transaction commits to avoid database lock
        if result.get('success') and birth_chart_id:
            try:
                fact_extractor = FactExtractor()
                await fact_extractor.extract_facts(question, result['response'], birth_chart_id)
            except Exception as e:
                print(f"❌ Fact extraction error: {e}")
        
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

@router.delete("/message/{message_id}")
async def delete_message(message_id: int, current_user = Depends(get_current_user)):
    """Hard delete a specific message"""
    print(f"🗑️ DELETE STEP 1: Request received for message ID: {message_id} by user: {current_user.userid}")
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        print(f"🗑️ DELETE STEP 2: Database connection established")
        
        # First, let's see what messages exist for this user
        cursor.execute('''
            SELECT cm.message_id, cm.sender, cm.message_type, SUBSTR(cm.content, 1, 50)
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.session_id
            WHERE cs.user_id = ?
            ORDER BY cm.message_id DESC LIMIT 10
        ''', (current_user.userid,))
        
        user_messages = cursor.fetchall()
        print(f"🔍 Recent messages for user {current_user.userid}:")
        for msg in user_messages:
            print(f"   ID: {msg[0]}, Sender: {msg[1]}, Type: {msg[2]}, Content: {msg[3]}...")
        
        print(f"🗑️ DELETE STEP 3: Verifying message ownership")
        # Verify message belongs to user
        cursor.execute('''
            SELECT cm.session_id, cs.user_id, cm.message_type, cm.sender
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.session_id
            WHERE cm.message_id = ?
        ''', (message_id,))
        
        result = cursor.fetchone()
        print(f"🔍 Database lookup result for ID {message_id}: {result}")
        
        if not result:
            print(f"❌ Message {message_id} not found in database")
            conn.close()
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found in database")
        
        session_id, user_id, message_type, sender = result
        print(f"🔍 Message details - User: {user_id}, Type: {message_type}, Sender: {sender}")
        print(f"🔍 Requesting user: {current_user.userid}")
        
        if user_id != current_user.userid:
            print(f"❌ Access denied: message belongs to user {user_id}, not {current_user.userid}")
            conn.close()
            raise HTTPException(status_code=403, detail="Access denied")
        
        print(f"🗑️ DELETE STEP 4: Getting message details for audit")
        # Get message details for audit log
        cursor.execute("SELECT content, message_type, sender FROM chat_messages WHERE message_id = ?", (message_id,))
        msg_details = cursor.fetchone()
        print(f"🗑️ DELETE STEP 5: Message details retrieved: {msg_details is not None}")
        
        if msg_details:
            content, msg_type, sender = msg_details
            print(f"🗑️ DELETE STEP 6: Inserting audit record")
            # Insert audit record
            try:
                cursor.execute("""
                    INSERT INTO message_deletion_audit 
                    (message_id, user_id, session_id, message_content, message_type, sender) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (message_id, current_user.userid, session_id, None, msg_type, sender))
                print(f"🗑️ DELETE STEP 7: Audit record inserted successfully")
            except Exception as audit_error:
                print(f"❌ DELETE STEP 7 ERROR: Audit insert failed: {audit_error}")
                # Continue with deletion even if audit fails
        
        print(f"🗑️ DELETE STEP 8: Performing actual deletion")
        # Hard delete the message
        cursor.execute("DELETE FROM chat_messages WHERE message_id = ?", (message_id,))
        deleted_rows = cursor.rowcount
        print(f"🗑️ DELETE STEP 9: Deleted {deleted_rows} rows for message ID {message_id}")
        
        print(f"🗑️ DELETE STEP 10: Committing transaction")
        conn.commit()
        print(f"🗑️ DELETE STEP 11: Transaction committed successfully")
        
        conn.close()
        print(f"🗑️ DELETE STEP 12: Database connection closed")
        
        print(f"✅ DELETE COMPLETE: Message {message_id} deleted successfully")
        return {"message": "Message deleted successfully"}
        
    except HTTPException as he:
        print(f"❌ DELETE HTTP ERROR: {he.detail}")
        raise he
    except Exception as e:
        print(f"❌ DELETE UNEXPECTED ERROR: {str(e)}")
        print(f"❌ ERROR TYPE: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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