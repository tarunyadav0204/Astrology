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

from ai.health_ai_context_generator import HealthAIContextGenerator
from ai.structured_analyzer import StructuredAnalysisAnalyzer

class HealthAnalysisRequest(BaseModel):
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
    force_regenerate: Optional[bool] = False

router = APIRouter(prefix="/health", tags=["health"])

# Initialize components
health_context_generator = HealthAIContextGenerator()
credit_service = CreditService()

@router.post("/analyze")
async def analyze_health(request: HealthAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Analyze health prospects with AI - requires credits"""
    
    # Check credit cost and user balance
    health_cost = credit_service.get_credit_setting('health_analysis_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < health_cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {health_cost} credits but have {user_balance}."
        )
    
    async def generate_health_analysis():
        try:
            # Check for cached analysis first (unless force_regenerate)
            print(f"🔍 DEBUG: force_regenerate = {request.force_regenerate}")
            if not request.force_regenerate:
                import sqlite3
                import hashlib
                
                birth_hash = hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()
                
                conn = sqlite3.connect('astrology.db')
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT insights_data FROM ai_health_insights WHERE birth_hash = ?
                """, (birth_hash,))
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    analysis_data = json.loads(result[0])
                    analysis_data['cached'] = True
                    final_response = {'status': 'complete', 'data': analysis_data, 'cached': True}
                    response_json = json.dumps(final_response)
                    print(f"🚀 SENDING CACHED HEALTH RESPONSE: {len(response_json)} chars")
                    yield f"data: {response_json}\n\n"
                    return
            
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
            
            # Build health context
            context = await asyncio.get_event_loop().run_in_executor(
                None, 
                health_context_generator.build_health_context,
                birth_data
            )
            
            # Health-specific AI question with advanced data utilization
            health_question = """
You are an expert Vedic astrologer. Analyze the birth chart for Health and Wellness.

IMPORTANT: You MUST respond with EXACTLY this JSON structure. Do not add extra fields or change field names.

{
  "quick_answer": "Brief health summary based on chart analysis",
  "detailed_analysis": [
    {
      "question": "What are my primary health vulnerabilities?",
      "answer": "Detailed analysis of 6th/8th house, lords, and afflictions",
      "key_points": ["Point 1", "Point 2"],
      "astrological_basis": "Planetary positions and aspects"
    },
    {
      "question": "When should I be extra cautious about health?",
      "answer": "Timing analysis based on dashas and transits",
      "key_points": ["Period 1", "Period 2"],
      "astrological_basis": "Dasha periods and planetary transits"
    },
    {
      "question": "What body parts need special attention?",
      "answer": "Body parts analysis based on houses and signs",
      "key_points": ["Body part 1", "Body part 2"],
      "astrological_basis": "House and sign correlations"
    },
    {
      "question": "How is my mental and emotional health?",
      "answer": "Moon, Mercury, and 4th house analysis",
      "key_points": ["Mental aspect 1", "Mental aspect 2"],
      "astrological_basis": "Moon and Mercury positions"
    },
    {
      "question": "What remedies can improve my health?",
      "answer": "Practical remedies and suggestions",
      "key_points": ["Remedy 1", "Remedy 2"],
      "astrological_basis": "Planetary strengthening methods"
    }
  ],
  "final_thoughts": "Positive health outlook and guidance",
  "follow_up_questions": [
    "🏥 How to improve my immunity?",
    "🧘 Best yoga/exercise for my body type?",
    "💊 Specific dietary precautions?",
    "🌿 Natural remedies for my weak planets?"
  ]
}

CRITICAL RULES:
1. Response must be ONLY valid JSON - no extra text
2. Use EXACTLY the field names shown above
3. Include exactly 5 questions in detailed_analysis array
4. Always mention this is astrological guidance, not medical advice
5. Use ** for bold text in JSON strings
"""
            
            # Generate AI response using structured analyzer
            analyzer = StructuredAnalysisAnalyzer()
            ai_result = await analyzer.generate_structured_report(
                health_question, 
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
                    
                    # Map to mobile expected format
                    detailed_analysis = []
                    for item in parsed_response.get('detailed_analysis', []):
                        detailed_analysis.append({
                            "question": item.get('question', ''),
                            "answer": item.get('answer', '')
                        })
                    
                    formatted_response = {
                        "quick_answer": parsed_response.get('quick_answer', 'Analysis completed successfully.'),
                        "detailed_analysis": detailed_analysis,
                        "final_thoughts": parsed_response.get('final_thoughts', ''),
                        "follow_up_questions": parsed_response.get('follow_up_questions', []),
                        "terms": ai_result.get('terms', []),
                        "glossary": ai_result.get('glossary', {})
                    }
                    
                    health_insights = {
                        'analysis': formatted_response,
                        'terms': ai_result.get('terms', []),
                        'glossary': ai_result.get('glossary', {}),
                        'enhanced_context': True,
                        'advanced_calculations': {
                            'mrityu_bhaga': True,
                            'badhaka_analysis': True,
                            'd30_trimsamsa': True,
                            'functional_malefics': True
                        },
                        'questions_covered': len(detailed_analysis),
                        'context_type': 'structured_analyzer',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    # Only deduct credits if analysis was successful
                    success = credit_service.spend_credits(
                        current_user.userid, 
                        health_cost, 
                        'health_analysis', 
                        f"Health analysis for {birth_data.get('name', 'user')}"
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
                            CREATE TABLE IF NOT EXISTS ai_health_insights (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                birth_hash TEXT UNIQUE,
                                insights_data TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO ai_health_insights 
                            (birth_hash, insights_data, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (birth_hash, json.dumps(health_insights)))
                        
                        conn.commit()
                        conn.close()
                        print(f"💾 Analysis cached successfully")
                    except Exception as cache_error:
                        print(f"⚠️ Failed to cache analysis: {cache_error}")
                    
                    final_response = {'status': 'complete', 'data': health_insights, 'cached': False}
                    response_json = json.dumps(final_response)
                    print(f"🚀 SENDING FINAL HEALTH RESPONSE: {len(response_json)} chars")
                    yield f"data: {response_json}\n\n"
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON PARSING FAILED: {e}")
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse AI response'})}\n\n"
                
            else:
                error_message = ai_result.get('error', 'AI analysis failed') if ai_result else 'No response from AI'
                yield f"data: {json.dumps({'status': 'error', 'error': error_message})}\n\n"
                
        except Exception as e:
            print(f"❌ HEALTH ANALYSIS ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            full_traceback = traceback.format_exc()
            print(f"Full traceback:\n{full_traceback}")
            
            # Always send proper streaming error response
            error_message = str(e) if str(e) else 'Unknown error occurred'
            yield f"data: {json.dumps({'status': 'error', 'error': error_message, 'error_type': type(e).__name__})}\n\n"
    
    return StreamingResponse(
        generate_health_analysis(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/get-analysis")
async def get_previous_analysis(request: HealthAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get previously generated health analysis if exists"""
    import sqlite3
    import hashlib
    
    try:
        birth_hash = hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT insights_data FROM ai_health_insights WHERE birth_hash = ?
        """, (birth_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            analysis_data = json.loads(result[0])
            analysis_data['cached'] = True
            return {"analysis": analysis_data}
        
        return {"analysis": None}
        
    except Exception as e:
        print(f"Error fetching previous analysis: {e}")
        return {"analysis": None}

@router.post("/ai-insights")
async def generate_health_ai_insights(request: HealthAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Generate AI insights for health analysis - alias for /analyze endpoint"""
    # This is an alias for the main analyze endpoint to match frontend expectations
    return await analyze_health(request, current_user)

@router.post("/overall-assessment")
async def get_overall_health_assessment(request: HealthAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get overall health assessment with technical analysis"""
    try:
        # Create birth data object
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.date,
            time=request.time,
            place=request.place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+0'
        )
        
        # Calculate birth chart
        from calculators.chart_calculator import ChartCalculator
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Calculate health analysis
        from calculators.health_calculator import HealthCalculator
        health_calc = HealthCalculator(chart_data, birth_data)
        health_analysis = health_calc.calculate_overall_health()
        
        return {
            "status": "success",
            "data": health_analysis
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Health calculation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Health calculation error: {str(e)}\n{error_details}")

@router.get("/test")
async def test_health_routes():
    """Test endpoint to verify health routes are working"""
    return {"status": "success", "message": "Health routes are working"}
