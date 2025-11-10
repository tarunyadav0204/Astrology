from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys
import os
import json
import asyncio

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

@router.post("/ask")
async def ask_question(request: ChatRequest):
    """Ask astrological question with streaming response"""
    
    async def generate_streaming_response():
        print(f"\n=== STREAMING STARTED ===")
        print(f"Request question: {request.question}")
        print(f"Request data: {request}")
        try:
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
            
            # Build astrological context
            context = context_builder.build_complete_context(birth_data, request.question)
            
            # Get conversation history
            history = session_manager.get_conversation_history(birth_hash)
            
            # Generate AI response
            try:
                print(f"\n=== CHAT ROUTE DEBUG ===")
                print(f"Question: {request.question}")
                print(f"Birth data: {birth_data}")
                print(f"Context type: {type(context)}")
                print(f"History length: {len(history)}")
                
                gemini_analyzer = GeminiChatAnalyzer()
                ai_result = await gemini_analyzer.generate_chat_response(request.question, context, history, request.language, request.response_style)
                
                print(f"AI result success: {ai_result.get('success')}")
                print(f"AI result keys: {list(ai_result.keys())}")
                
                if ai_result['success']:
                    response_text = ai_result['response']
                    
                    # Note: Message saving handled by ChatModal via /api/chat/message endpoint
                    
                    # Send final result with proper JSON escaping
                    try:
                        # Clean and validate response text
                        if not response_text or response_text.strip() == '':
                            response_text = "I apologize, but I couldn't generate a proper response. Please try asking your question again."
                        
                        # Ensure response is properly formatted
                        clean_response = response_text.strip()
                        
                        response_json = json.dumps({
                            'status': 'complete', 
                            'response': clean_response
                        }, ensure_ascii=False, separators=(',', ':'))
                        
                        print(f"Sending response length: {len(clean_response)}")
                        print(f"Response preview: {clean_response[:100]}...")
                        
                        yield f"data: {response_json}\n\n"
                        
                    except Exception as json_error:
                        print(f"JSON serialization error: {json_error}")
                        print(f"Problematic response: {response_text[:200]}...")
                        
                        # Fallback with manual escaping
                        try:
                            safe_response = response_text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                            fallback_json = f'{{"status": "complete", "response": "{safe_response}"}}'
                            yield f"data: {fallback_json}\n\n"
                        except Exception as fallback_error:
                            print(f"Fallback error: {fallback_error}")
                            error_json = json.dumps({'status': 'error', 'error': 'Response formatting failed'})
                            yield f"data: {error_json}\n\n"
                else:
                    print(f"AI error: {ai_result.get('error')}")
                    
                    # Convert AI errors to user-friendly messages
                    ai_error = ai_result.get('error', 'AI analysis failed')
                    user_error = "I'm having trouble processing your question right now. Please try rephrasing it or try again later."
                    
                    if "timeout" in str(ai_error).lower():
                        user_error = "Your question is taking longer than expected to process. Please try again."
                    elif "rate limit" in str(ai_error).lower():
                        user_error = "I'm processing many requests right now. Please wait a moment and try again."
                    
                    yield f"data: {json.dumps({'status': 'error', 'error': user_error})}\n\n"
                    
            except Exception as e:
                print(f"Chat route exception: {str(e)}")
                import traceback
                traceback.print_exc()
                
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
            print(f"\n=== STREAMING ERROR ===")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
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
    print("Chat test endpoint called")
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