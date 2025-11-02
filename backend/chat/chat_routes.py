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
                ai_result = gemini_analyzer.generate_chat_response(request.question, context, history)
                
                print(f"AI result success: {ai_result.get('success')}")
                print(f"AI result keys: {list(ai_result.keys())}")
                
                if ai_result['success']:
                    response_text = ai_result['response']
                    
                    # Save to conversation history
                    session_manager.add_message(birth_hash, request.question, response_text)
                    
                    # Send final result with proper JSON escaping
                    try:
                        response_json = json.dumps({
                            'status': 'complete', 
                            'response': response_text
                        }, ensure_ascii=False, separators=(',', ':'))
                        yield f"data: {response_json}\n\n"
                    except Exception as json_error:
                        print(f"JSON serialization error: {json_error}")
                        # Fallback with escaped response
                        safe_response = response_text.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                        yield f"data: {{\"status\": \"complete\", \"response\": \"{safe_response}\"}}\n\n"
                else:
                    print(f"AI error: {ai_result.get('error')}")
                    yield f"data: {json.dumps({'status': 'error', 'error': ai_result.get('error', 'AI analysis failed')})}\n\n"
                    
            except Exception as e:
                print(f"Chat route exception: {str(e)}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
                
        except Exception as e:
            print(f"\n=== STREAMING ERROR ===")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
    
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