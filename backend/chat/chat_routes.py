from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os
import json
import asyncio
import html
import re

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

class ClearChatRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize components
context_builder = ChatContextBuilder()
session_manager = ChatSessionManager()

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
async def ask_question(request: ChatRequest):
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
                                transit_request = json.loads(json_matches[0])
                                start_year = transit_request.get('startYear')
                                end_year = transit_request.get('endYear')
                                specific_months = transit_request.get('specificMonths', [])
                                
                                # print(f"🔄 MAKING SECOND CALL WITH TRANSIT DATA: {start_year}-{end_year}")
                                # print(f"   Specific months: {specific_months}")
                                # print(f"   NOT SENDING FIRST RESPONSE TO FRONTEND - Contains transit request")
                                
                                # Build context with transit data
                                transit_context = context_builder.build_complete_context(
                                    birth_data, 
                                    request.question, 
                                    requested_period={'start_year': start_year, 'end_year': end_year}
                                )
                                
                                # Make second API call with transit data
                                enhanced_question = request.question + "\n\nIMPORTANT: Use the provided transit_activations data to predict SPECIFIC EVENTS with EXACT DATES. In your Quick Answer, provide 2-3 concrete events (like 'property purchase', 'job promotion', 'relationship milestone') with precise date ranges from the transit data. Focus on house significations of activated planets and combine with dasha context for accurate predictions."
                                
                                second_ai_result = await gemini_analyzer.generate_chat_response(
                                    enhanced_question, transit_context, history, request.language, request.response_style
                                )
                                
                                if second_ai_result['success']:
                                    response_text = second_ai_result['response']
                                    # print(f"✅ SECOND CALL SUCCESSFUL - Response length: {len(response_text)}")
                                    # print(f"   SENDING FINAL RESPONSE TO FRONTEND")
                                else:
                                    # print(f"❌ SECOND CALL FAILED: {second_ai_result.get('error')}")
                                    # Send error message instead of first response
                                    response_text = "I'm having trouble calculating precise transit data for your timing question. Please try again."
                                    
                            except json.JSONDecodeError as e:
                                # print(f"❌ FAILED TO PARSE TRANSIT REQUEST JSON: {e}")
                                # Send error message instead of first response
                                response_text = "I encountered an issue processing your timing question. Please try rephrasing it."
                        else:
                            # print(f"❌ NO VALID JSON TRANSIT REQUEST FOUND")
                            # Send error message instead of first response
                            response_text = "I need to request additional data for your timing question but encountered a formatting issue. Please try again."
                    
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
                    # print(f"AI error: {ai_result.get('error')}")
                    
                    # Convert AI errors to user-friendly messages
                    ai_error = ai_result.get('error', 'AI analysis failed')
                    user_error = "I'm having trouble processing your question right now. Please try rephrasing it or try again later."
                    
                    if "timeout" in str(ai_error).lower():
                        user_error = "Your question is taking longer than expected to process. Please try again."
                    elif "rate limit" in str(ai_error).lower():
                        user_error = "I'm processing many requests right now. Please wait a moment and try again."
                    
                    yield f"data: {json.dumps({'status': 'error', 'error': user_error})}\n\n"
                    
            except Exception as e:
                # print(f"Chat route exception: {str(e)}")
                # import traceback
                # traceback.print_exc()
                pass
                
                # Convert technical errors to user-friendly messages
                error_message = "I'm having trouble connecting right now. Please try again in a moment."
                
                if "timeout" in str(e).lower() or "503" in str(e):
                    error_message = "The service is temporarily busy. Please try again in a few moments."
                elif "connection" in str(e).lower() or "connect" in str(e).lower():
                    error_message = "I'm having connection issues. Please check your internet and try again."
                elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
                    error_message = "I'm receiving too many requests right now. Please wait a moment and try again."
                elif "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                    error_message = "There's a temporary service issue. Please try again shortly."
                
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