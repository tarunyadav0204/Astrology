"""
Marriage Analysis API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict
import sys
import os
import json
import asyncio
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.marriage_ai_context_generator import MarriageAIContextGenerator
from ai.structured_analyzer import StructuredAnalysisAnalyzer

class MarriageAnalysisRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None
    language: Optional[str] = 'english'
    response_style: Optional[str] = 'detailed'

router = APIRouter(prefix="/marriage", tags=["marriage"])

marriage_context_generator = MarriageAIContextGenerator()
credit_service = CreditService()

@router.post("/analyze")
async def analyze_marriage(request: MarriageAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Analyze marriage prospects with AI - requires credits"""
    
    # Check credit cost and user balance
    marriage_cost = credit_service.get_credit_setting('marriage_analysis_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < marriage_cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {marriage_cost} credits but have {user_balance}."
        )
    
    async def generate_marriage_analysis():
        try:
            # Prepare birth data
            from datetime import date
            birth_data = {
                'name': request.name,
                'date': request.date,
                'time': request.time,
                'place': request.place,
                'latitude': request.latitude or 28.6139,
                'longitude': request.longitude or 77.2090,
                'timezone': request.timezone or 'UTC+0',
                'gender': request.gender,
                'current_year': date.today().year
            }
            
            # Build marriage context
            context = await asyncio.get_event_loop().run_in_executor(
                None, 
                marriage_context_generator.build_marriage_context,
                birth_data
            )
            
            # Marriage-specific AI question (EXACT same format as education)
            marriage_question = """
As an expert Vedic astrologer, analyze the birth chart for **Relationship and Marriage Destiny**.

CRITICAL: You MUST respond with ONLY a JSON object. NO other text, NO HTML, NO explanations.
Start your response with { and end with }. Use markdown ** for bold text within JSON strings.
{
  "quick_answer": "Summary of marriage prospects and timing.",
  "detailed_analysis": [
    {
      "question": "What is the timeline for major relationship events?",
      "answer": "Analyze timing using Vimshottari Dasha and Jupiter/Saturn transits",
      "key_points": ["Current period", "Best timing"],
      "astrological_basis": "7th house and lord analysis..."
    },
    {
      "question": "What is the personality and nature of my partner?",
      "answer": "Describe spouse traits from 7th house and D9 Navamsa"
    },
    {
      "question": "Are there any Doshas affecting harmony?",
      "answer": "Analyze Mangal Dosha and Saturn aspects"
    },
    {
      "question": "Is my destiny inclined towards Love or Traditional connection?",
      "answer": "Analyze 5th-7th house connection and relationship style"
    },
    {
      "question": "What is the key to happiness in my specific chart?",
      "answer": "Guidance based on D9 Navamsa analysis"
    }
  ],
  "final_thoughts": "Encouraging summary focusing on marriage potential.",
  "follow_up_questions": [
    "📅 Best timing for marriage?",
    "❤️ How to improve compatibility?",
    "💍 What are my partner's key traits?",
    "⚡ Remedies for relationship peace?"
  ]
}

CRITICAL: Your entire response must be valid JSON starting with { and ending with }.
Do NOT include any text before or after the JSON object.
Do NOT use HTML div tags or HTML formatting.
Use <br> for line breaks within JSON strings.
Escape quotes properly: \"text\"
"""
            
            # Generate AI response using structured analyzer
            analyzer = StructuredAnalysisAnalyzer()
            ai_result = await analyzer.generate_structured_report(
                marriage_question, 
                context, 
                request.language or 'english'
            )
            
            if ai_result['success']:
                try:
                    # Handle structured analyzer response format
                    if ai_result.get('is_raw'):
                        # Raw response format (fallback)
                        parsed_response = {
                            "quick_answer": "Analysis completed successfully.",
                            "detailed_analysis": [],
                            "final_thoughts": "Analysis provided in detailed format.",
                            "follow_up_questions": []
                        }
                    else:
                        # JSON data format (preferred) - map to mobile expected format
                        raw_data = ai_result.get('data', {})
                        
                        # Map detailed_analysis fields to mobile expected format
                        detailed_analysis = []
                        for item in raw_data.get('detailed_analysis', []):
                            detailed_analysis.append({
                                "question": item.get('question', ''),
                                "answer": item.get('answer', '')
                            })
                        
                        parsed_response = {
                            "quick_answer": raw_data.get('quick_answer', 'Analysis completed successfully.'),
                            "detailed_analysis": detailed_analysis,
                            "final_thoughts": raw_data.get('final_thoughts', ''),
                            "follow_up_questions": raw_data.get('follow_up_questions', []),
                            "terms": ai_result.get('terms', []),
                            "glossary": ai_result.get('glossary', {})
                        }
                    
                    marriage_insights = {
                        'analysis': parsed_response,
                        'terms': ai_result.get('terms', []),
                        'glossary': ai_result.get('glossary', {}),
                        'enhanced_context': True,
                        'questions_covered': len(parsed_response.get('detailed_analysis', [])),
                        'context_type': 'structured_analyzer',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    # Deduct credits for successful analysis
                    success = credit_service.spend_credits(
                        current_user.userid, 
                        marriage_cost, 
                        'marriage_analysis', 
                        f"Marriage analysis for {birth_data.get('name', 'user')}"
                    )
                    
                    if success:
                        print(f"💳 Credits deducted successfully")
                    else:
                        print(f"❌ Credit deduction failed")
                    
                    # Cache the analysis
                    try:
                        import sqlite3
                        import hashlib
                        
                        birth_hash = hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()
                        
                        conn = sqlite3.connect('astrology.db')
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS ai_marriage_insights (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                birth_hash TEXT UNIQUE,
                                insights_data TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO ai_marriage_insights 
                            (birth_hash, insights_data, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (birth_hash, json.dumps(marriage_insights)))
                        
                        conn.commit()
                        conn.close()
                        print(f"💾 Analysis cached successfully")
                    except Exception as cache_error:
                        print(f"⚠️ Failed to cache analysis: {cache_error}")
                    
                    final_response = {'status': 'complete', 'data': marriage_insights, 'cached': False}
                    response_json = json.dumps(final_response)
                    print(f"🚀 SENDING FINAL MARRIAGE RESPONSE: {len(response_json)} chars")
                    yield f"data: {response_json}\n\n"
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON PARSING FAILED: {e}")
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse AI response'})}\n\n"
                
            else:
                error_message = ai_result.get('error', 'AI analysis failed') if ai_result else 'No response from AI'
                yield f"data: {json.dumps({'status': 'error', 'error': error_message})}\n\n"
                
        except Exception as e:
            print(f"❌ MARRIAGE ANALYSIS ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            full_traceback = traceback.format_exc()
            print(f"Full traceback:\n{full_traceback}")
            
            error_message = str(e) if str(e) else 'Unknown error occurred'
            yield f"data: {json.dumps({'status': 'error', 'error': error_message, 'error_type': type(e).__name__})}\n\n"
    
    return StreamingResponse(
        generate_marriage_analysis(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )