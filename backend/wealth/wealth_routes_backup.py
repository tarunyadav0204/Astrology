from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sys
import os
import hashlib
import json
import sqlite3
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService

# Add the parent directory to the path to import calculators
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.chart_calculator import ChartCalculator
from calculators.wealth_calculator import WealthCalculator
from ai.gemini_wealth_analyzer import GeminiWealthAnalyzer

class BirthDetailsRequest(BaseModel):
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM
    birth_place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    force_regenerate: Optional[bool] = False
    user_role: Optional[str] = None

router = APIRouter(prefix="/wealth", tags=["wealth"])
credit_service = CreditService()

def _create_birth_hash(birth_data):
    """Create unique hash for birth data"""
    birth_string = f"{birth_data.date}_{birth_data.time}_{birth_data.latitude}_{birth_data.longitude}"
    return hashlib.sha256(birth_string.encode()).hexdigest()

def _init_ai_insights_table():
    """Initialize AI insights table if not exists"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_wealth_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            birth_hash TEXT UNIQUE,
            insights_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def _get_stored_ai_insights(birth_hash):
    """Get stored AI insights from database"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('SELECT insights_data FROM ai_wealth_insights WHERE birth_hash = ?', (birth_hash,))
    result = cursor.fetchone()
    conn.close()
    return json.loads(result[0]) if result else None

def _store_ai_insights(birth_hash, insights_data):
    """Store AI insights in database"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO ai_wealth_insights (birth_hash, insights_data, updated_at)
        VALUES (?, ?, ?)
    ''', (birth_hash, json.dumps(insights_data), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def _parse_ai_response(response_text):
    """Parse AI response into structured Q&A format"""
    import re
    
    questions = [
        "What is my overall wealth potential according to my birth chart?",
        "Will I be wealthy or face financial struggles in life?",
        "Should I do business or job for better financial success?",
        "What are my best sources of income and earning methods?",
        "Can I do stock trading and speculation successfully?",
        "When will I see significant financial growth in my life?",
        "At what age will I achieve financial stability?",
        "What types of investments and financial strategies suit me best?",
        "Should I invest in property, stocks, or other assets?"
    ]
    
    formatted_questions = []
    
    # Try multiple splitting patterns
    patterns = [r'\*\*\d+\.', r'\d+\.\s*\*\*', r'###\s*\d+\.', r'^\d+\.', r'\n\d+\.']
    sections = []
    
    for pattern in patterns:
        test_sections = re.split(pattern, response_text, flags=re.MULTILINE)
        if len(test_sections) > len(sections):
            sections = test_sections
    
    # If no numbered sections found, try to find questions in text
    if len(sections) <= 1:
        for i, question in enumerate(questions):
            # Find the question in text (case insensitive)
            question_pattern = re.escape(question.lower())
            match = re.search(question_pattern, response_text.lower())
            if match:
                start_pos = match.end()
                # Find next question or end of text
                next_question_pos = len(response_text)
                for j, next_q in enumerate(questions[i+1:], i+1):
                    next_match = re.search(re.escape(next_q.lower()), response_text.lower()[start_pos:])
                    if next_match:
                        next_question_pos = start_pos + next_match.start()
                        break
                
                section_text = response_text[start_pos:next_question_pos].strip()
                if section_text and len(section_text) > 20:
                    # Take first few sentences as answer
                    sentences = section_text.split('.')
                    answer = '. '.join(sentences[:4]).strip()
                    if answer and not answer.endswith('.'):
                        answer += '.'
                    
                    formatted_questions.append({
                        "question": questions[i],
                        "answer": answer,
                        "key_points": [],
                        "astrological_basis": "Based on comprehensive chart analysis"
                    })
    else:
        # Process numbered sections
        for i, section in enumerate(sections[1:]):
            if i < len(questions):
                # Clean the section
                answer = section.strip()
                # Remove the question text if it appears at the start
                for q in questions:
                    if answer.lower().startswith(q.lower()):
                        answer = answer[len(q):].strip()
                        break
                
                # Take first few sentences as answer
                sentences = answer.split('.')
                answer = '. '.join(sentences[:4]).strip()
                if answer and not answer.endswith('.'):
                    answer += '.'
                
                if answer:
                    formatted_questions.append({
                        "question": questions[i],
                        "answer": answer,
                        "key_points": [],
                        "astrological_basis": "Based on comprehensive chart analysis"
                    })
    
    # Ensure we have all 9 questions - add placeholders if missing
    for i, question in enumerate(questions):
        if i >= len(formatted_questions) or formatted_questions[i]['question'] != question:
            formatted_questions.insert(i, {
                "question": question,
                "answer": "Analysis in progress. Please regenerate for complete insights.",
                "key_points": [],
                "astrological_basis": "Based on comprehensive chart analysis"
            })
    
    return {
        "summary": "Comprehensive wealth analysis based on Vedic astrology principles.",
        "questions": formatted_questions[:9]  # Ensure exactly 9 questions
    }

@router.post("/ai-insights-enhanced")
async def get_enhanced_wealth_insights(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Enhanced wealth insights using chat context builder with 9 key questions - requires credits"""
    
    # Check credit cost and user balance
    wealth_cost = credit_service.get_credit_setting('wealth_analysis_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    print(f"💳 WEALTH CREDIT CHECK:")
    print(f"   User ID: {current_user.userid}")
    print(f"   Wealth cost: {wealth_cost} credits")
    print(f"   User balance: {user_balance} credits")
    
    if user_balance < wealth_cost:
        print(f"❌ INSUFFICIENT CREDITS: Need {wealth_cost}, have {user_balance}")
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {wealth_cost} credits but have {user_balance}."
        )
    
    print(f"Enhanced wealth insights request received: {request.birth_date} {request.birth_time}")
    
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def generate_streaming_response():
        import json
        
        try:
            print(f"🔄 Starting wealth analysis for user {current_user.userid}")
            
            # Import chat components (no modifications to chat system)
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            try:
                from chat.chat_context_builder import ChatContextBuilder
                print(f"✅ ChatContextBuilder imported successfully")
            except Exception as e:
                print(f"❌ Failed to import ChatContextBuilder: {e}")
                raise
                
            try:
                from ai.gemini_chat_analyzer import GeminiChatAnalyzer
                print(f"✅ GeminiChatAnalyzer imported successfully")
            except Exception as e:
                print(f"❌ Failed to import GeminiChatAnalyzer: {e}")
                raise
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Initializing enhanced wealth analysis...'})}\n\n"
            
            # Prepare birth data in chat format
            birth_data = {
                'name': request.birth_place,
                'date': request.birth_date,
                'time': request.birth_time,
                'place': request.birth_place,
                'latitude': request.latitude or 28.6139,
                'longitude': request.longitude or 77.2090,
                'timezone': request.timezone or 'UTC+5:30'
            }
            
            # Create birth data object
            from types import SimpleNamespace
            birth_obj = SimpleNamespace(**birth_data)
            birth_hash = _create_birth_hash(birth_obj)
            
            # Initialize database table
            _init_ai_insights_table()
            
            # Check cache
            force_regen = request.force_regenerate
            if force_regen is not True:
                stored_insights = _get_stored_ai_insights(birth_hash)
                if stored_insights and stored_insights.get('enhanced_context'):
                    yield f"data: {json.dumps({'status': 'complete', 'data': stored_insights, 'cached': True})}\n\n"
                    return
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Building comprehensive astrological context...'})}\n\n"
            
            # Use chat context builder (async)
            try:
                print(f"🏗️ Building context for birth data: {birth_data['date']} {birth_data['time']}")
                context_builder = ChatContextBuilder()
                full_context = await asyncio.get_event_loop().run_in_executor(
                    None, context_builder.build_complete_context, birth_data
                )
                print(f"✅ Context built successfully")
            except Exception as e:
                print(f"❌ Context building failed: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating AI insights with enhanced context...'})}\n\n"
            
            # Create comprehensive wealth question
            wealth_question = """
As an expert Vedic astrologer, provide a comprehensive wealth analysis using the complete astrological context provided. Answer each question separately with detailed analysis.

Questions to answer with detailed astrological analysis:

**1. What is my overall wealth potential according to my birth chart?**
**2. Will I be wealthy or face financial struggles in life?**
**3. Should I do business or job for better financial success?**
**4. What are my best sources of income and earning methods?**
**5. Can I do stock trading and speculation successfully?**
**6. When will I see significant financial growth in my life?**
**7. At what age will I achieve financial stability?**
**8. What types of investments and financial strategies suit me best?**
**9. Should I invest in property, stocks, or other assets?**

Use the comprehensive birth chart data, current planetary periods, and all astrological context provided to give detailed, accurate predictions.
"""
            
            # Use chat analyzer (async)
            try:
                print(f"🤖 Initializing Gemini analyzer...")
                gemini_analyzer = GeminiChatAnalyzer()
                print(f"✅ Gemini analyzer initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini analyzer: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Prepare context as dictionary for GeminiChatAnalyzer
            if isinstance(full_context, str):
                context_dict = {
                    'astrological_data': full_context,
                    'birth_details': {
                        'name': birth_data['name'],
                        'date': birth_data['date'],
                        'time': birth_data['time'],
                        'place': birth_data['place']
                    }
                }
            else:
                context_dict = full_context if full_context else {
                    'astrological_data': 'No astrological context available',
                    'birth_details': {
                        'name': birth_data['name'],
                        'date': birth_data['date'],
                        'time': birth_data['time'],
                        'place': birth_data['place']
                    }
                }
            
            # Retry logic for API timeouts
            max_retries = 3
            retry_delay = 10  # seconds
            ai_result = None
            
            for attempt in range(max_retries):
                try:
                    print(f"🔄 Attempt {attempt + 1}/{max_retries} - Calling Gemini API...")
                    ai_result = await gemini_analyzer.generate_chat_response(
                        wealth_question, context_dict, [], 'english', 'detailed'
                    )
                    print(f"📨 Received response from Gemini API: success={ai_result.get('success')}")
                    break  # Success, exit retry loop
                    
                except Exception as api_error:
                    error_msg = str(api_error)
                    print(f"⚠️ API attempt {attempt + 1} failed: {error_msg}")
                    
                    # Check if it's a timeout/deadline error
                    if ("timeout" in error_msg.lower() or 
                        "deadline" in error_msg.lower() or 
                        "504" in error_msg or
                        "DeadlineExceeded" in error_msg):
                        
                        if attempt < max_retries - 1:  # Not the last attempt
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            print(f"⏳ Timeout detected, retrying in {wait_time} seconds...")
                            yield f"data: {json.dumps({'status': 'processing', 'message': f'API timeout, retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})'})}\n\n"
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ All retry attempts exhausted for timeout")
                            ai_result = {'success': False, 'error': f'API timeout after {max_retries} attempts'}
                            break
                    else:
                        # Non-timeout error, don't retry
                        print(f"❌ Non-timeout error, not retrying: {error_msg}")
                        ai_result = {'success': False, 'error': error_msg}
                        break
            
            if ai_result and ai_result.get('success'):
                # Parse AI response into Q&A format
                formatted_response = _parse_ai_response(ai_result['response'])
                
                # Deduct credits for successful analysis
                print(f"💰 DEDUCTING CREDITS: {wealth_cost} credits for user {current_user.userid}")
                success = credit_service.spend_credits(
                    current_user.userid, 
                    wealth_cost, 
                    'wealth_analysis', 
                    f"Wealth analysis for {request.birth_date}"
                )
                
                if not success:
                    print(f"❌ CREDIT DEDUCTION FAILED for user {current_user.userid}")
                    error_response = {
                        'wealth_analysis': 'Credit deduction failed. Please try again.',
                        'enhanced_context': False,
                        'error': 'Credit deduction failed'
                    }
                    yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\n\n"
                else:
                    print(f"✅ CREDITS DEDUCTED SUCCESSFULLY")
                    
                    # Store in wealth database with enhanced flag
                    enhanced_insights = {
                        'wealth_analysis': formatted_response,
                        'enhanced_context': True,
                        'questions_covered': len(formatted_response.get('questions', [])),
                        'context_type': 'chat_context_builder',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    await asyncio.get_event_loop().run_in_executor(
                        None, _store_ai_insights, birth_hash, enhanced_insights
                    )
                    
                    yield f"data: {json.dumps({'status': 'complete', 'data': enhanced_insights, 'cached': False})}\n\n"
            else:
                error_response = {
                    'wealth_analysis': 'AI analysis failed. Please try again.',
                    'enhanced_context': False,
                    'error': ai_result.get('error', 'Unknown error') if ai_result else 'No response from AI'
                }
                yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\n\n"
                
        except Exception as e:
            print(f"❌ ENHANCED WEALTH ANALYSIS ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            full_traceback = traceback.format_exc()
            print(f"Full traceback:\n{full_traceback}")
            
            error_response = {
                'wealth_analysis': f'Analysis error: {str(e)}. Please try again.',
                'enhanced_context': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            yield f"data: {json.dumps({'status': 'error', 'error': str(e), 'error_type': type(e).__name__})}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )