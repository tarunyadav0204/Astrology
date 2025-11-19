from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os
import json
import asyncio
import html
import re
from auth import get_current_user, User
from credits.credit_service import CreditService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat.chat_context_builder import ChatContextBuilder
from chat.chat_session_manager import ChatSessionManager
from ai.gemini_chat_analyzer import GeminiChatAnalyzer

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

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize components
context_builder = ChatContextBuilder()
session_manager = ChatSessionManager()
credit_service = CreditService()

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
    chat_cost = credit_service.get_credit_setting('chat_question_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    print(f"💳 CREDIT CHECK DEBUG:")
    print(f"   User ID: {current_user.userid}")
    print(f"   Chat cost: {chat_cost} credits")
    print(f"   User balance: {user_balance} credits")
    print(f"   Has sufficient credits: {user_balance >= chat_cost}")
    
    if user_balance < chat_cost:
        print(f"❌ INSUFFICIENT CREDITS: Need {chat_cost}, have {user_balance}")
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {chat_cost} credits but have {user_balance}."
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
                'timezone': request.timezone or 'UTC+5:30',
                'gender': request.gender
            }
            
            birth_hash = session_manager.create_birth_hash(birth_data)
            
            # Build astrological context (no pre-processing needed for JSON format)
            requested_period = None
            
            # Set selected period if provided
            if request.selected_period:
                context_builder.set_selected_period(request.selected_period)
            
            # Build astrological context with requested period
            context = context_builder.build_complete_context(birth_data, request.question, requested_period=requested_period)
            
            # Get conversation history
            history = session_manager.get_conversation_history(birth_hash)
            
            # Generate AI response
            try:
                # print(f"\n=== CHAT ROUTE DEBUG ===")
                # print(f"Question: {request.question}")
                # print(f"Birth data: {birth_data}")
                # print(f"Context type: {type(context)}")
                # print(f"History length: {len(history)}")
                
                # Add instruction for Gemini about transit data requests
                enhanced_question = request.question
                if not requested_period and context.get('transit_data_availability'):
                    enhanced_question += "\n\nIMPORTANT: For PRECISE event prediction, use the advanced methodology in transit_data_availability. When dasha planets recreate their natal relationships through transits, events manifest with highest probability. For timing questions, you MUST request transit data using the JSON format. Do NOT provide a complete response - only request the transit data."
                
                gemini_analyzer = GeminiChatAnalyzer()
                ai_result = await gemini_analyzer.generate_chat_response(enhanced_question, context, history, request.language, request.response_style)
                
                # print(f"AI result success: {ai_result.get('success')}")
                # print(f"AI result keys: {list(ai_result.keys())}")
                
                if ai_result['success']:
                    response_text = ai_result['response']
                    
                    # Check if Gemini requested transit data via JSON and make second call if needed
                    if ai_result.get('has_transit_request', False):
                        
                        # Look for JSON transit request in response
                        json_pattern = r'\{[^}]*"requestType"\s*:\s*"transitRequest"[^}]*\}'
                        json_matches = re.findall(json_pattern, response_text)
                        
                        if json_matches:
                            try:
                                print(f"🔍 TRANSIT REQUEST DEBUG: Found JSON match: {json_matches[0]}")
                                transit_request = json.loads(json_matches[0])
                                start_year = transit_request.get('startYear')
                                end_year = transit_request.get('endYear')
                                specific_months = transit_request.get('specificMonths', [])
                                
                                print(f"🔄 MAKING SECOND CALL WITH TRANSIT DATA: {start_year}-{end_year}")
                                print(f"   Specific months: {specific_months}")
                                print(f"   Birth data: {birth_data}")
                                
                                # Validate years
                                if not start_year or not end_year or start_year < 1900 or end_year > 2100:
                                    print(f"❌ INVALID YEAR RANGE: {start_year}-{end_year}")
                                    response_text = "Invalid year range requested for transit data. Please try again."
                                else:
                                    try:
                                        # Build context with transit data
                                        print(f"🏗️ Building transit context...")
                                        transit_context = context_builder.build_complete_context(
                                            birth_data, 
                                            request.question, 
                                            requested_period={'start_year': start_year, 'end_year': end_year}
                                        )
                                        
                                        print(f"✅ Transit context built successfully")
                                        print(f"   Transit activations found: {len(transit_context.get('transit_activations', []))}")
                                        
                                        # Make second API call with transit data
                                        enhanced_question = request.question + "\n\nIMPORTANT: Use the provided transit_activations data to predict SPECIFIC EVENTS with EXACT DATES. In your Quick Answer, provide 2-3 concrete events (like 'property purchase', 'job promotion', 'relationship milestone') with precise date ranges from the transit data. Focus on house significations of activated planets and combine with dasha context for accurate predictions."
                                        
                                        print(f"🤖 Making second Gemini call...")
                                        second_ai_result = await gemini_analyzer.generate_chat_response(
                                            enhanced_question, transit_context, history, request.language, request.response_style
                                        )
                                        
                                        if second_ai_result['success']:
                                            response_text = second_ai_result['response']
                                            print(f"✅ SECOND CALL SUCCESSFUL - Response length: {len(response_text)}")
                                            # Only deduct credits on successful second call
                                            should_deduct_credits = True
                                        else:
                                            print(f"❌ SECOND CALL FAILED: {second_ai_result.get('error')}")
                                            response_text = f"I'm having trouble calculating precise transit data for your timing question. Error: {second_ai_result.get('error', 'Unknown error')}. Please try again."
                                            # Don't deduct credits if second call fails
                                            should_deduct_credits = False
                                    
                                    except Exception as context_error:
                                        print(f"❌ CONTEXT BUILDING ERROR: {context_error}")
                                        import traceback
                                        traceback.print_exc()
                                        response_text = f"I encountered an error building transit context: {str(context_error)}. Please try again."
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ FAILED TO PARSE TRANSIT REQUEST JSON: {e}")
                                print(f"   Raw JSON: {json_matches[0]}")
                                response_text = "I encountered an issue processing your timing question. Please try rephrasing it."
                            except Exception as e:
                                print(f"❌ UNEXPECTED ERROR IN TRANSIT PROCESSING: {e}")
                                import traceback
                                traceback.print_exc()
                                response_text = f"Unexpected error in transit processing: {str(e)}. Please try again."
                        else:
                            print(f"❌ NO VALID JSON TRANSIT REQUEST FOUND")
                            print(f"   Response text preview: {response_text[:200]}...")
                            response_text = "I need to request additional data for your timing question but encountered a formatting issue. Please try again."
                    
                    # Only deduct credits if response was successful (including second AI call)
                    should_deduct = locals().get('should_deduct_credits', True)
                    
                    if should_deduct:
                        print(f"💰 DEDUCTING CREDITS: {chat_cost} credits for user {current_user.userid}")
                        success = credit_service.spend_credits(
                            current_user.userid, 
                            chat_cost, 
                            'chat_question', 
                            f"Chat question: {request.question[:50]}..."
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
                            'response': clean_response
                        }
                        
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
                                chunk_json = json.dumps(chunk_data, ensure_ascii=True, separators=(',', ':'))
                                yield f"data: {chunk_json}\n\n"
                            
                            # Send completion signal
                            complete_data = {'status': 'complete'}
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
            'timezone': request.timezone or 'UTC+5:30',
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
            'timezone': request.timezone or 'UTC+5:30',
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
            'timezone': request.timezone or 'UTC+5:30',
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
            'timezone': request.get('timezone', 'UTC+5:30'),
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