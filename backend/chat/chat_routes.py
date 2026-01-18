from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import sys
import os
import json
import asyncio
import html
import re
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat.chat_context_builder import ChatContextBuilder
from chat.chat_session_manager import ChatSessionManager
from ai.gemini_chat_analyzer import GeminiChatAnalyzer
from ai.intent_router import IntentRouter
from calculators.chart_calculator import ChartCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from calculators.event_predictor_ai import EventPredictor
from calculators.ashtakavarga import AshtakavargaCalculator
from shared.dasha_calculator import DashaCalculator

class ChatRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None
    question: str
    language: Optional[str] = 'english'
    response_style: Optional[str] = 'detailed'
    selected_period: Optional[Dict] = None
    include_context: Optional[bool] = False
    premium_analysis: Optional[bool] = False
    # User context
    user_name: Optional[str] = Field(None, alias="userName")
    user_relationship: Optional[str] = Field('self', alias="userRelationship")
    # Partnership mode
    partnership_mode: Optional[bool] = Field(False, alias="partnershipMode")
    partner_name: Optional[str] = Field(None, alias="partnerName")
    partner_date: Optional[str] = Field(None, alias="partnerDate")
    partner_time: Optional[str] = Field(None, alias="partnerTime")
    partner_place: Optional[str] = Field(None, alias="partnerPlace")
    partner_latitude: Optional[float] = Field(None, alias="partnerLatitude")
    partner_longitude: Optional[float] = Field(None, alias="partnerLongitude")
    partner_timezone: Optional[str] = Field(None, alias="partnerTimezone")
    partner_gender: Optional[str] = Field(None, alias="partnerGender")
    
    class Config:
        populate_by_name = True  # Allows both snake_case and camelCase

class ClearChatRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None
    selectedYear: Optional[int] = None
    birth_chart_id: Optional[int] = None

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize components
context_builder = ChatContextBuilder()
session_manager = ChatSessionManager()
credit_service = CreditService()
intent_router = IntentRouter()

def _smart_chunk_response(response_text: str, max_size: int) -> List[str]:
    """Simple chunking that breaks at paragraph boundaries"""
    chunks = []
    
    # Split at double newlines (paragraph breaks)
    paragraphs = response_text.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        # If adding this paragraph would exceed max size
        if len(current_chunk + '\n\n' + para) > max_size and current_chunk:
            # Save current chunk
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += '\n\n' + para
            else:
                current_chunk = para
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

@router.post("/ask")
async def ask_question(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Ask astrological question with streaming response - requires credits"""
    
    # Check credit cost and user balance
    if request.partnership_mode:
        base_cost = credit_service.get_credit_setting('chat_question_cost')
        chat_cost = base_cost * 2  # Partnership mode costs double
    elif request.premium_analysis:
        chat_cost = credit_service.get_credit_setting('premium_chat_cost')
    else:
        chat_cost = credit_service.get_credit_setting('chat_question_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    print(f"💳 CREDIT CHECK DEBUG:")
    print(f"   User ID: {current_user.userid}")
    print(f"   Partnership Mode: {request.partnership_mode}")
    print(f"   Premium Analysis: {request.premium_analysis}")
    print(f"   Chat cost: {chat_cost} credits")
    print(f"   User balance: {user_balance} credits")
    print(f"   Has sufficient credits: {user_balance >= chat_cost}")
    
    if user_balance < chat_cost:
        if request.partnership_mode:
            analysis_type = "Partnership Analysis"
        elif request.premium_analysis:
            analysis_type = "Premium Deep Analysis"
        else:
            analysis_type = "Standard Analysis"
        print(f"❌ INSUFFICIENT CREDITS: Need {chat_cost}, have {user_balance}")
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits for {analysis_type}. You need {chat_cost} credits but have {user_balance}."
        )
    """Ask astrological question with streaming response"""
    
    async def generate_streaming_response():
        # print(f"\n=== STREAMING STARTED ===")
        # print(f"Request question: {request.question}")
        # print(f"Request data: {request}")
        try:
            # Import json at function level
            import json
            import re
            
            # Prepare birth data
            from types import SimpleNamespace
            birth_data = {
                'name': request.name,
                'date': request.date,
                'time': request.time,
                'place': request.place,
                'latitude': request.latitude or 28.6139,
                'longitude': request.longitude or 77.2090,
                'timezone': request.timezone,
                'gender': request.gender
            }
            
            birth_hash = session_manager.create_birth_hash(birth_data)
            
            # Use Intent Router to classify question and determine transit needs
            print(f"\n🧠 CLASSIFYING INTENT FOR: {request.question}")
            intent_result = await intent_router.classify_intent(request.question)
            print(f"✅ INTENT CLASSIFICATION RESULT: {intent_result}")
            
            # Set selected period if provided
            if request.selected_period:
                context_builder.set_selected_period(request.selected_period)
            
            # Build astrological context with requested period (run in thread pool)
            import asyncio
            try:
                # Check if partnership mode
                if request.partnership_mode:
                    print(f"\n👥 PARTNERSHIP MODE REQUEST DETECTED")
                    print(f"   Native: {birth_data.get('name')}")
                    print(f"   Partner: {request.partner_name}")
                    print(f"   Question: {request.question}")
                    
                    # Validate partner data
                    if not all([request.partner_date, request.partner_time, request.partner_place]):
                        print(f"   ❌ Missing partner data")
                        yield f"data: {json.dumps({'status': 'error', 'error': 'Partner birth details are required for partnership mode'})}\n\n"
                        return
                    
                    partner_birth_data = {
                        'name': request.partner_name,
                        'date': request.partner_date,
                        'time': request.partner_time,
                        'place': request.partner_place,
                        'latitude': request.partner_latitude or 28.6139,
                        'longitude': request.partner_longitude or 77.2090,
                        'timezone': request.partner_timezone,
                        'gender': request.partner_gender
                    }
                    
                    print(f"   ✅ Building synastry context for both charts...")
                    context = await asyncio.get_event_loop().run_in_executor(
                        None,
                        context_builder.build_synastry_context,
                        birth_data, partner_birth_data, request.question, intent_result
                    )
                    print(f"   ✅ Synastry context built successfully")
                elif intent_result.get('mode') == 'prashna':
                    print(f"\n🔮 PRASHNA MODE DETECTED")
                    print(f"   Category: {intent_result.get('category')}")
                    
                    # Build prashna context using user's location (approximate)
                    user_location = {
                        'latitude': birth_data['latitude'],
                        'longitude': birth_data['longitude'],
                        'place': birth_data['place']
                    }
                    
                    context = await asyncio.get_event_loop().run_in_executor(
                        None,
                        context_builder.build_prashna_context,
                        user_location, request.question, intent_result.get('category', 'general')
                    )
                    print(f"   ✅ Prashna context built successfully")
                elif intent_result.get('mode') == 'annual':
                    print(f"\n📅 ANNUAL MODE DETECTED")
                    target_year = intent_result.get('year', datetime.now().year + 1)
                    print(f"   Target year: {target_year}")
                    
                    # Convert intent router transit request to old format if needed
                    requested_period = None
                    if intent_result.get('needs_transits') and intent_result.get('transit_request'):
                        tr = intent_result['transit_request']
                        requested_period = {
                            'start_year': tr['startYear'],
                            'end_year': tr['endYear'],
                            'yearMonthMap': tr.get('yearMonthMap', {})
                        }
                        print(f"   Transit period: {tr['startYear']}-{tr['endYear']}")
                    
                    # Use build_complete_context to handle transit requests properly
                    # Pass intent_result directly without thread executor to avoid serialization issues
                    print(f"   🔧 Calling build_complete_context with intent_result: {intent_result is not None}")
                    context = context_builder.build_complete_context(
                        birth_data, request.question, None, requested_period, intent_result
                    )
                    
                    # Add annual-specific data
                    context['analysis_type'] = 'annual_forecast'
                    context['focus_year'] = target_year
                    
                    print(f"   ✅ Annual context built successfully")
                else:
                    print(f"\n🌟 BIRTH CHART MODE (Default)")
                    print(f"   Needs transits: {intent_result.get('needs_transits', False)}")
                    
                    # Convert intent router transit request to old format if needed
                    requested_period = None
                    if intent_result.get('needs_transits') and intent_result.get('transit_request'):
                        tr = intent_result['transit_request']
                        requested_period = {
                            'start_year': tr['startYear'],
                            'end_year': tr['endYear'],
                            'yearMonthMap': tr.get('yearMonthMap', {})
                        }
                        print(f"   Transit period: {tr['startYear']}-{tr['endYear']}")
                    
                    # Pass intent_result directly without thread executor to avoid serialization issues
                    print(f"   🔧 Calling build_complete_context with intent_result: {intent_result is not None}")
                    context = context_builder.build_complete_context(
                        birth_data, request.question, None, requested_period, intent_result
                    )
            except Exception as context_error:
                print(f"❌ CONTEXT BUILDING ERROR: {context_error}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'status': 'error', 'error': f'Chart calculation failed: {str(context_error)}'})}\n\n"
                return
            
            # Send context data immediately for admin users
            if request.include_context and current_user.role == 'admin':
                try:
                    # Send full context as string for admin viewing
                    context_json = json.dumps({'status': 'context', 'context': str(context)}, ensure_ascii=True)
                    yield f"data: {context_json}\n\n"

                except Exception as ctx_error:

                    # Fallback with error info
                    fallback_json = json.dumps({'status': 'context', 'context': f'Context serialization failed: {str(ctx_error)}'}, ensure_ascii=True)
                    yield f"data: {fallback_json}\n\n"
            
            # Get conversation history
            history = session_manager.get_conversation_history(birth_hash)
            
            # Generate AI response
            try:
                # print(f"\n=== CHAT ROUTE DEBUG ===")
                # print(f"Question: {request.question}")
                # print(f"Birth data: {birth_data}")
                # print(f"Context type: {type(context)}")
                # print(f"History length: {len(history)}")
                
                # Add instruction for Gemini based on intent classification
                enhanced_question = request.question
                
                # Add mode-specific instructions
                if request.partnership_mode:
                    native_name = birth_data.get('name', 'Native')
                    partner_name = partner_birth_data.get('name', 'Partner')
                    enhanced_question = f"PARTNERSHIP ANALYSIS REQUEST:\nNative: {native_name}\nPartner: {partner_name}\n\nQuestion: {request.question}\n\nIMPORTANT: Use context['native'] for {native_name}'s data and context['partner'] for {partner_name}'s data. Do not mix their planetary positions, dashas, or chart details."
                elif intent_result.get('needs_transits') and context.get('transit_activations'):
                    enhanced_question += "\n\nIMPORTANT: Transit data has been pre-calculated based on your question. Use the provided transit_activations to predict SPECIFIC EVENTS with EXACT DATES. Focus on house significations and dasha correlations for accurate predictions."
                elif not intent_result.get('needs_transits') and intent_result.get('mode') == 'birth':
                    enhanced_question += "\n\nNOTE: This is a general birth chart analysis. Focus on personality, yogas, and long-term life patterns rather than specific timing predictions."
                
                # Extract user context
                user_context = {
                    'user_name': request.user_name,
                    'user_relationship': request.user_relationship or 'self'
                }
                
                print(f"\n=== USER CONTEXT DEBUG ===")
                print(f"Request user_name: {request.user_name}")
                print(f"Request user_relationship: {request.user_relationship}")
                print(f"Final user_context: {user_context}")
                print(f"Birth data name: {birth_data.get('name')}")
                
                gemini_analyzer = GeminiChatAnalyzer()
                ai_result = await gemini_analyzer.generate_chat_response(enhanced_question, context, history, request.language, request.response_style, user_context, request.premium_analysis)
                
                # print(f"AI result success: {ai_result.get('success')}")
                # print(f"AI result keys: {list(ai_result.keys())}")
                
                if ai_result['success']:
                    response_text = ai_result['response']
                    
                    # Transit data is now pre-calculated by Intent Router, no second call needed
                    print(f"✅ SINGLE CALL COMPLETE - Response length: {len(response_text)}")
                    if context.get('transit_optimization', {}).get('source') == 'intent_router':
                        print(f"🚀 OPTIMIZATION SUCCESS: Eliminated second Gemini call using Intent Router")
                    
                    # Deduct credits for successful response
                    should_deduct = True
                    
                    if should_deduct:
                        print(f"💰 DEDUCTING CREDITS: {chat_cost} credits for user {current_user.userid}")
                        analysis_type = "Premium Deep Analysis" if request.premium_analysis else "Standard Chat"
                        success = credit_service.spend_credits(
                            current_user.userid, 
                            chat_cost, 
                            'chat_question', 
                            f"{analysis_type}: {request.question[:50]}..."
                        )
                        
                        if not success:
                            print(f"❌ CREDIT DEDUCTION FAILED for user {current_user.userid}")
                            response_text = "Credit deduction failed. Please try again."
                        else:
                            print(f"✅ CREDITS DEDUCTED SUCCESSFULLY")
                            new_balance = credit_service.get_user_credits(current_user.userid)
                            print(f"   New balance: {new_balance} credits")
                    else:
                        print(f"⚠️ NOT DEDUCTING CREDITS due to second AI call failure")
                    
                    # Note: Message saving handled by ChatModal via /api/chat/message endpoint
                    
                    # Send final result with robust JSON handling
                    try:
                        # Clean and validate response text
                        if not response_text or response_text.strip() == '':
                            response_text = "I apologize, but I couldn't generate a proper response. Please try asking your question again."
                        
                        # Clean response text - remove any problematic characters
                        clean_response = response_text.strip()
                        
                        # Remove any null bytes or control characters that could break JSON
                        clean_response = ''.join(char for char in clean_response if ord(char) >= 32 or char in '\n\r\t')
                        
                        # Replace problematic quotes and characters
                        clean_response = clean_response.replace('"', '"').replace('"', '"')
                        clean_response = clean_response.replace(''', "'").replace(''', "'")
                        clean_response = clean_response.replace('–', '-').replace('—', '-')
                        
                        # print(f"Cleaned response length: {len(clean_response)}")
                        # print(f"Response preview: {clean_response[:100]}...")
                        # print(f"Will chunk response: {len(clean_response) > max_chunk_size}")
                        
                        # Use json.dumps with proper error handling
                        response_data = {
                            'status': 'complete', 
                            'response': clean_response,
                            'terms': ai_result.get('terms', []),
                            'glossary': ai_result.get('glossary', {})
                        }
                        
                        # Add images if available (DEPRECATED - use summary_image)
                        if ai_result.get('images'):
                            response_data['images'] = ai_result['images']
                            print(f"📸 Including {len(ai_result['images'])} images in response")
                        
                        # Add summary image if available
                        if ai_result.get('summary_image'):
                            response_data['summary_image'] = ai_result['summary_image']
                            print(f"🇼 Including summary image in response: {ai_result['summary_image']}")
                        
                        # Context already sent earlier for admin users
                        
                        # Smart chunking that preserves markdown structure
                        max_chunk_size = 3500
                        
                        if len(clean_response) > max_chunk_size:
                            # print(f"Response too long ({len(clean_response)} chars), using smart chunking")
                            
                            # Smart chunking that respects markdown sections
                            chunks = _smart_chunk_response(clean_response, max_chunk_size)
                            
                            for i, chunk in enumerate(chunks):
                                chunk_data = {
                                    'status': 'chunk',
                                    'chunk_index': i,
                                    'total_chunks': len(chunks),
                                    'response': chunk
                                }
                                # Include summary_image and terms/glossary in first chunk
                                if i == 0:
                                    if ai_result.get('summary_image'):
                                        chunk_data['summary_image'] = ai_result['summary_image']
                                    chunk_data['terms'] = ai_result.get('terms', [])
                                    chunk_data['glossary'] = ai_result.get('glossary', {})
                                # Context already sent earlier for admin users
                                chunk_json = json.dumps(chunk_data, ensure_ascii=True, separators=(',', ':'))
                                yield f"data: {chunk_json}\n\n"
                            
                            # Send completion signal
                            complete_data = {'status': 'complete'}
                            # Context already sent earlier for admin users
                            complete_json = json.dumps(complete_data, ensure_ascii=True)
                            yield f"data: {complete_json}\n\n"
                        else:
                            # Send as single response if small enough
                            response_json = json.dumps(response_data, ensure_ascii=True, separators=(',', ':'))
                            
                            # print(f"JSON length: {len(response_json)}")
                            # print(f"JSON preview: {response_json[:200]}...")
                            
                            # Validate JSON by parsing it back
                            json.loads(response_json)
                            
                            yield f"data: {response_json}\n\n"
                        
                    except Exception as json_error:
                        # print(f"JSON serialization error: {json_error}")
                        # print(f"Error type: {type(json_error).__name__}")
                        # print(f"Problematic response length: {len(clean_response)}")
                        # print(f"First 500 chars: {repr(clean_response[:500])}")
                        
                        # Try to send response without chunking as fallback
                        try:
                            # Further clean the response
                            safe_response = clean_response.encode('ascii', 'ignore').decode('ascii')
                            safe_data = {'status': 'complete', 'response': safe_response}
                            safe_json = json.dumps(safe_data, ensure_ascii=True)
                            yield f"data: {safe_json}\n\n"
                        except:
                            # Ultimate fallback
                            safe_message = "I generated a response but encountered a formatting issue. Please try asking your question again."
                            fallback_data = {'status': 'error', 'error': safe_message}
                            fallback_json = json.dumps(fallback_data, ensure_ascii=True)
                            yield f"data: {fallback_json}\n\n"
                else:
                    print(f"❌ AI ERROR: {ai_result.get('error')}")
                    
                    # Log AI error details for debugging
                    ai_error = ai_result.get('error', 'AI analysis failed')
                    print(f"❌ AI ERROR: {ai_error}")
                    
                    # Show generic user-friendly message
                    user_error = "I'm having trouble processing your question right now. Please try again in a moment."
                    
                    if "timeout" in str(ai_error).lower():
                        user_error = "Your question is taking longer than expected to process. Please try again."
                    elif "rate limit" in str(ai_error).lower():
                        user_error = "I'm processing many requests right now. Please wait a moment and try again."
                    
                    # Don't deduct credits if AI fails
                    print(f"⚠️ NOT DEDUCTING CREDITS due to AI failure")
                    
                    yield f"data: {json.dumps({'status': 'error', 'error': user_error})}\n\n"
                    
            except Exception as e:
                # print(f"Chat route exception: {str(e)}")
                # import traceback
                # traceback.print_exc()
                pass
                
                # Log technical error details for debugging
                print(f"❌ CHAT ROUTE ERROR: {type(e).__name__}: {str(e)}")
                
                # Always show generic user-friendly message
                error_message = "I'm having trouble processing your question right now. Please try again in a moment."
                
                # Only vary the message for clearly user-facing issues
                if "timeout" in str(e).lower() or "503" in str(e):
                    error_message = "The service is temporarily busy. Please try again in a few moments."
                elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
                    error_message = "I'm receiving too many requests right now. Please wait a moment and try again."
                
                yield f"data: {json.dumps({'status': 'error', 'error': error_message})}\n\n"
                
        except Exception as e:
            # print(f"\n=== STREAMING ERROR ===")
            # print(f"Error: {str(e)}")
            # import traceback
            # traceback.print_exc()
            pass
            
            # User-friendly error for outer exceptions
            user_error = "Something went wrong while processing your request. Please try again."
            yield f"data: {json.dumps({'status': 'error', 'error': user_error})}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/history")
async def get_chat_history(request: ClearChatRequest):
    """Get conversation history for birth data"""
    try:
        birth_data = {
            'name': request.name,
            'date': request.date,
            'time': request.time,
            'place': request.place,
            'latitude': request.latitude or 28.6139,
            'longitude': request.longitude or 77.2090,
            'timezone': request.timezone or 'UTC+0',
            'gender': request.gender
        }
        
        birth_hash = session_manager.create_birth_hash(birth_data)
        history = session_manager.get_conversation_history(birth_hash, limit=20)
        
        return {
            "status": "success",
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
async def clear_chat_history(request: ClearChatRequest):
    """Clear conversation history for birth data"""
    try:
        birth_data = {
            'name': request.name,
            'date': request.date,
            'time': request.time,
            'place': request.place,
            'latitude': request.latitude or 28.6139,
            'longitude': request.longitude or 77.2090,
            'timezone': request.timezone or 'UTC+0',
            'gender': request.gender
        }
        
        birth_hash = session_manager.create_birth_hash(birth_data)
        session_manager.clear_conversation(birth_hash)
        
        return {
            "status": "success",
            "message": "Chat history cleared"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_chat_routes():
    """Test endpoint to verify chat routes are working"""
    # print("Chat test endpoint called")
    return {"status": "success", "message": "Chat routes are working"}

@router.post("/event-periods")
async def get_event_periods(request: ClearChatRequest):
    """Get high-significance event periods for next 2 years"""
    try:
        print(f"📅 Event periods request: {request}")
        
        # Normalize date format from ISO to YYYY-MM-DD
        date_str = request.date
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        
        # Normalize time format from ISO to HH:MM
        time_str = request.time
        if 'T' in time_str:
            time_part = time_str.split('T')[1]
            time_str = time_part[:5]  # Extract HH:MM
        
        birth_data = {
            'name': request.name,
            'date': date_str,
            'time': time_str,
            'place': request.place,
            'latitude': request.latitude or 28.6139,
            'longitude': request.longitude or 77.2090,
            'timezone': request.timezone or 'UTC+0',
            'gender': request.gender
        }
        
        print(f"📊 Birth data prepared: {birth_data}")
        print(f"📅 Selected year: {request.selectedYear}")
        
        periods = context_builder.get_high_significance_periods(birth_data, selected_year=request.selectedYear)
        
        print(f"✅ Periods calculated: {len(periods)} periods")
        
        return {
            "status": "success",
            "periods": periods
        }
        
    except Exception as e:
        print(f"❌ Event periods error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_question_suggestions():
    """Get suggested questions for users"""
    suggestions = [
        "What does my birth chart say about my personality?",
        "When is a good time for me to get married?",
        "What career path suits me best according to my chart?",
        "What are my strengths and weaknesses?",
        "When should I start a new business or venture?",
        "How is my health according to my birth chart?",
        "What does my chart say about my relationships?",
        "What is my life purpose according to Vedic astrology?",
        "When will I see positive changes in my career?",
        "What remedies can help improve my situation?"
    ]
    
    
    return {
        "status": "success",
        "suggestions": suggestions
    }

@router.get("/scan-timeline")
async def scan_timeline(birth_chart_id: int, current_user: User = Depends(get_current_user)):
    """Silent background scan for calibration events"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, date, time, latitude, longitude, timezone, place, gender
            FROM birth_charts WHERE id = ? AND userid = ?
        ''', (birth_chart_id, current_user.userid))
        
        birth_row = cursor.fetchone()
        conn.close()
        
        if not birth_row:
            return {"events": []}
        
        from encryption_utils import EncryptionManager
        try:
            encryptor = EncryptionManager()
            birth_data = {
                'name': encryptor.decrypt(birth_row[0]),
                'date': encryptor.decrypt(birth_row[1]),
                'time': encryptor.decrypt(birth_row[2]),
                'latitude': float(encryptor.decrypt(str(birth_row[3]))),
                'longitude': float(encryptor.decrypt(str(birth_row[4]))),
                'timezone': birth_row[5],
                'place': encryptor.decrypt(birth_row[6] or ''),
                'gender': birth_row[7] or ''
            }
        except:
            birth_data = {
                'name': birth_row[0],
                'date': birth_row[1],
                'time': birth_row[2],
                'latitude': birth_row[3],
                'longitude': birth_row[4],
                'timezone': birth_row[5],
                'place': birth_row[6] or '',
                'gender': birth_row[7] or ''
            }
        
        from calculators.life_event_scanner import LifeEventScanner
        from calculators.chart_calculator import ChartCalculator
        from shared.dasha_calculator import DashaCalculator
        from calculators.real_transit_calculator import RealTransitCalculator
        
        scanner = LifeEventScanner(
            ChartCalculator({}), 
            DashaCalculator(), 
            RealTransitCalculator()
        )
        
        events = scanner.scan_timeline(birth_data, start_age=18)
        high_confidence = [e for e in events if e['confidence'] == 'High']
        
        return {"events": high_confidence[:1]}
        
    except Exception as e:
        print(f"❌ Timeline scan error: {e}")
        import traceback
        traceback.print_exc()
        return {"events": []}

@router.post("/verify-calibration")
async def verify_calibration(request: dict, current_user: User = Depends(get_current_user)):
    """Store user's verification response"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE birth_charts 
            SET is_rectified = ?, calibration_year = ?
            WHERE id = ? AND userid = ?
        ''', (
            1 if request.get('verified') else 0,
            request.get('event_year'),
            request.get('birth_chart_id'),
            current_user.userid
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True}
        
    except Exception as e:
        print(f"❌ Calibration verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save-message")
async def save_message(request: dict):
    """Save individual message to chat history"""
    try:
        birth_data = {
            'name': request.get('name'),
            'date': request.get('date'),
            'time': request.get('time'),
            'place': request.get('place'),
            'latitude': request.get('latitude', 28.6139),
            'longitude': request.get('longitude', 77.2090),
            'timezone': request.get('timezone', 'UTC+0'),
            'gender': request.get('gender')
        }
        
        message = request.get('message', {})
        birth_hash = session_manager.create_birth_hash(birth_data)
        
        # Add message to session manager
        session_manager.add_individual_message(birth_hash, message)
        
        return {
            "status": "success",
            "message": "Message saved"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def init_event_timeline_table():
    """Initialize event timeline jobs table"""
    import sqlite3
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_timeline_jobs (
            job_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            birth_chart_id INTEGER NOT NULL,
            selected_year INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
            result_data TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (userid),
            FOREIGN KEY (birth_chart_id) REFERENCES birth_charts (id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_user_id ON event_timeline_jobs (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_birth_chart ON event_timeline_jobs (birth_chart_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_status ON event_timeline_jobs (status)')
    
    conn.commit()
    conn.close()

@router.post("/monthly-events")
async def get_monthly_events(request: ClearChatRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """
    Start async event timeline generation - returns job_id for polling
    """
    import uuid
    import sqlite3
    
    try:
        # Initialize table if needed
        init_event_timeline_table()
        
        # Check credit cost and user balance
        event_timeline_cost = credit_service.get_credit_setting('event_timeline_cost')
        user_balance = credit_service.get_user_credits(current_user.userid)
        
        if user_balance < event_timeline_cost:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient credits for Event Timeline Analysis. You need {event_timeline_cost} credits but have {user_balance}."
            )
        
        # Normalize date/time format
        date_str = request.date.split('T')[0] if 'T' in request.date else request.date
        time_str = request.time.split('T')[1][:5] if 'T' in request.time else request.time
        
        birth_data_dict = {
            'name': request.name,
            'date': date_str,
            'time': time_str,
            'place': request.place,
            'latitude': request.latitude or 28.6139,
            'longitude': request.longitude or 77.2090,
            'timezone': request.timezone or 'UTC+0',
            'gender': request.gender
        }
        
        target_year = request.selectedYear or datetime.now().year
        
        # Create job
        job_id = str(uuid.uuid4())
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        birth_chart_id = request.birth_chart_id
        if not birth_chart_id:
            print(f"❌ Missing birth_chart_id in request: {request}")
            raise HTTPException(status_code=400, detail="birth_chart_id is required. Please ensure birth chart is saved to database.")
        
        # Verify birth chart exists and belongs to user
        cursor.execute(
            "SELECT id FROM birth_charts WHERE id = ? AND userid = ?",
            (birth_chart_id, current_user.userid)
        )
        if not cursor.fetchone():
            print(f"❌ Birth chart {birth_chart_id} not found for user {current_user.userid}")
            raise HTTPException(
                status_code=404, 
                detail=f"Birth chart not found. Please re-select your birth chart from the profile screen."
            )
        
        cursor.execute(
            "INSERT INTO event_timeline_jobs (job_id, user_id, birth_chart_id, selected_year, status) VALUES (?, ?, ?, ?, ?)",
            (job_id, current_user.userid, birth_chart_id, target_year, 'pending')
        )
        
        conn.commit()
        conn.close()
        
        # Start background processing
        background_tasks.add_task(
            process_event_timeline,
            job_id, birth_chart_id, target_year, current_user.userid, event_timeline_cost
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Generating your cosmic timeline..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Monthly Event Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monthly-events/status/{job_id}")
async def get_event_timeline_status(job_id: str, current_user: User = Depends(get_current_user)):
    """Poll event timeline job status"""
    import sqlite3
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT status, result_data, error_message, started_at, completed_at
        FROM event_timeline_jobs
        WHERE job_id = ? AND user_id = ?
    ''', (job_id, current_user.userid))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status, result_data, error_message, started_at, completed_at = result
    
    response = {"status": status}
    
    if status == "completed" and result_data:
        response["data"] = json.loads(result_data)
        response["completed_at"] = completed_at
    elif status == "failed":
        response["error"] = error_message or "Analysis failed"
    elif status in ["pending", "processing"]:
        response["message"] = "Analyzing planetary positions..."
        if started_at:
            response["started_at"] = started_at
    
    return response

@router.post("/monthly-events/cached")
async def get_cached_timeline(request: ClearChatRequest, current_user: User = Depends(get_current_user)):
    """Get cached event timeline if exists for user and year"""
    import sqlite3
    
    try:
        target_year = request.selectedYear or datetime.now().year
        
        print(f"🔍 Checking cache for user {current_user.userid}, birth_chart_id {request.birth_chart_id}, year {target_year}")
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        birth_chart_id = request.birth_chart_id
        if not birth_chart_id:
            print(f"⚠️ No birth_chart_id provided for cache lookup")
            return {"cached": False}
        
        # Debug: Show all jobs for this user and birth_chart
        cursor.execute('''
            SELECT job_id, birth_chart_id, selected_year, status
            FROM event_timeline_jobs
            WHERE user_id = ? AND birth_chart_id = ?
            ORDER BY created_at DESC
        ''', (current_user.userid, birth_chart_id))
        all_jobs = cursor.fetchall()
        print(f"📊 All jobs for user {current_user.userid}, birth_chart {birth_chart_id}: {all_jobs}")
        
        # Find most recent completed job for this user/birth_chart/year
        cursor.execute('''
            SELECT result_data, completed_at, job_id
            FROM event_timeline_jobs
            WHERE user_id = ? AND birth_chart_id = ? AND selected_year = ? AND status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 1
        ''', (current_user.userid, birth_chart_id, target_year))
        
        print(f"🔎 Cache query params: user_id={current_user.userid}, birth_chart_id={birth_chart_id}, year={target_year}")
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            print(f"✅ Found cached timeline: job_id={result[2]}, cached_at={result[1]}")
            return {
                "cached": True,
                "data": json.loads(result[0]),
                "cached_at": result[1]
            }
        
        print(f"❌ No cached timeline found")
        return {"cached": False}
        
    except Exception as e:
        print(f"❌ Error fetching cached timeline: {e}")
        import traceback
        traceback.print_exc()
        return {"cached": False}

async def process_event_timeline(job_id: str, birth_chart_id: int, target_year: int, user_id: int, cost: int):
    """Background task to process event timeline"""
    import sqlite3
    
    print("\n" + "*"*100)
    print(f"🚀 BACKGROUND TASK STARTED: process_event_timeline")
    print(f"   - Job ID: {job_id}")
    print(f"   - Birth Chart ID: {birth_chart_id}")
    print(f"   - Target Year: {target_year}")
    print(f"   - User ID: {user_id}")
    print(f"   - Cost: {cost} credits")
    print("*"*100 + "\n")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    try:
        # Update status to processing
        print("🔄 Updating job status to 'processing'...")
        cursor.execute(
            "UPDATE event_timeline_jobs SET status = ?, started_at = ? WHERE job_id = ?",
            ('processing', datetime.now(), job_id)
        )
        conn.commit()
        print("✅ Job status updated")
        
        # Fetch birth data from database
        print(f"🔍 Fetching birth chart {birth_chart_id} from database...")
        cursor.execute('''
            SELECT name, date, time, latitude, longitude, timezone, place, gender
            FROM birth_charts WHERE id = ?
        ''', (birth_chart_id,))
        
        birth_row = cursor.fetchone()
        print(f"📊 Birth row result: {birth_row}")
        
        if not birth_row:
            print(f"❌ Birth chart {birth_chart_id} not found in database")
            raise Exception(f"Birth chart with ID {birth_chart_id} not found in database")
        
        from encryption_utils import EncryptionManager
        try:
            print(f"🔐 Attempting to decrypt birth data...")
            encryptor = EncryptionManager()
            birth_data_dict = {
                'name': encryptor.decrypt(birth_row[0]),
                'date': encryptor.decrypt(birth_row[1]),
                'time': encryptor.decrypt(birth_row[2]),
                'latitude': float(encryptor.decrypt(str(birth_row[3]))),
                'longitude': float(encryptor.decrypt(str(birth_row[4]))),
                'timezone': birth_row[5],
                'place': encryptor.decrypt(birth_row[6] or ''),
                'gender': birth_row[7] or ''
            }
            print(f"✅ Birth data decrypted successfully")
        except Exception as decrypt_error:
            print(f"⚠️ Decryption failed, using raw data: {decrypt_error}")
            birth_data_dict = {
                'name': birth_row[0],
                'date': birth_row[1],
                'time': birth_row[2],
                'latitude': birth_row[3],
                'longitude': birth_row[4],
                'timezone': birth_row[5],
                'place': birth_row[6] or '',
                'gender': birth_row[7] or ''
            }
        
        print(f"📅 Birth data prepared: date={birth_data_dict['date']}, time={birth_data_dict['time']}, place={birth_data_dict['place'][:20]}...")
        
        # Generate predictions
        chart_calc = ChartCalculator({}) 
        transit_calc = RealTransitCalculator()
        from shared.dasha_calculator import DashaCalculator
        dasha_calc = DashaCalculator()
        
        predictor = EventPredictor(chart_calc, transit_calc, dasha_calc, AshtakavargaCalculator)
        
        print(f"\n🚀 Calling predict_yearly_events for year {target_year}...")
        predictions = await predictor.predict_yearly_events(birth_data_dict, target_year)
        
        print(f"\n📦 Predictions received:")
        print(f"   - Status: {predictions.get('status')}")
        print(f"   - Keys: {list(predictions.keys())}")
        
        if predictions.get('status') == 'success':
            # Deduct credits
            success = credit_service.spend_credits(
                user_id, 
                cost, 
                'event_timeline', 
                f"Cosmic Timeline Analysis for {target_year}"
            )
            
            if not success:
                raise Exception("Credit deduction failed")
            
            # Save result
            print(f"\n💾 Saving result to database...")
            result_json = json.dumps(predictions)
            print(f"   - Result JSON length: {len(result_json)} characters")
            
            cursor.execute(
                "UPDATE event_timeline_jobs SET status = ?, result_data = ?, completed_at = ? WHERE job_id = ?",
                ('completed', json.dumps(predictions), datetime.now(), job_id)
            )
            conn.commit()
            print(f"✅ Result saved, task completed")
        else:
            raise Exception(predictions.get('error', 'Prediction failed'))
        
    except Exception as e:
        print(f"\n❌ BACKGROUND TASK ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        cursor.execute(
            "UPDATE event_timeline_jobs SET status = ?, error_message = ?, completed_at = ? WHERE job_id = ?",
            ('failed', str(e), datetime.now(), job_id)
        )
        conn.commit()
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed for job {job_id}\n")