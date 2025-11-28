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
from ai.gemini_chat_analyzer import GeminiChatAnalyzer

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
            # Prepare birth data
            from datetime import date
            birth_data = {
                'name': request.name,
                'date': request.date,
                'time': request.time,
                'place': request.place,
                'latitude': request.latitude or 28.6139,
                'longitude': request.longitude or 77.2090,
                'timezone': request.timezone or 'UTC+5:30',
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
As an expert Vedic astrologer, analyze the birth chart for **Health and Wellness**.

CRITICAL DATA UTILIZATION INSTRUCTIONS:
1. **Badhaka Analysis**: Check 'badhaka_analysis' in context. If the Badhaka Lord is active or afflicted, identify "hard-to-diagnose" or "karmic" issues.
2. **Mrityu Bhaga**: Check 'mrityu_bhaga_analysis'. If any planet is in these fatal degrees, flag the corresponding organ/system as "High Risk".
3. **D-30 (Trimsamsa)**: Use 'health_charts.d30_analysis' to determine if an ailment is "Curable" or "Chronic/Serious".
4. **Functional Nature**: Differentiate between 'Natural Malefics' and 'Functional Malefics' using the 'functional_nature' data.
5. **Body Parts Analysis**: Use 'body_parts_analysis' to correlate House (Location) with Sign (Nature of ailment).

CRITICAL: You MUST respond with ONLY a JSON object. NO other text, NO HTML, NO explanations.
Start your response with { and end with }. Use markdown ** for bold text within JSON strings.
{
  "quick_answer": "Summary of constitution (Prakriti) and primary health risks based on Ascendant and strongest planet.",
  "detailed_analysis": [
    {
      "question": "What are my primary health vulnerabilities?",
      "answer": "Analyze 6th/8th lord. **CRITICAL:** Mention if any planet is in **Mrityu Bhaga** (Fatal Degree) or is a **Badhaka** (Tormentor). Specify body parts using 'body_parts_analysis' data.",
      "key_points": ["Vulnerability 1", "Vulnerability 2"],
      "astrological_basis": "Explain planetary positions (e.g., 'Sun in Mrityu Bhaga affects heart')"
    },
    {
      "question": "When should I be extra cautious about health?",
      "answer": "Identify Dasha periods of Maraka (2nd/7th) or 6th Lords. Check 'health_timing' data for vulnerable periods."
    },
    {
      "question": "What body parts or systems need special attention?",
      "answer": "Use 'body_parts_analysis' data. Correlate House (Location) with Sign (Nature of ailment). Highlight any Mrityu Bhaga connections."
    },
    {
      "question": "Is there a risk of chronic or 'mystery' illnesses?",
      "answer": "Analyze **Badhaka Lord** and **Saturn**. If Badhaka is active, mention 'undiagnosable issues'. Check **D-30 analysis** for severity (Curable vs Chronic)."
    },
    {
      "question": "How is my mental and emotional health?",
      "answer": "Analyze Moon, Mercury, and 4th house. Check if Moon is in Mrityu Bhaga or afflicted by Badhaka."
    },
    {
      "question": "What is my immunity and vitality level?",
      "answer": "Analyze Ascendant lord, Sun, and Mars. Use 'vitality_analysis' data and check for Mrityu Bhaga afflictions."
    },
    {
      "question": "What remedies can improve my health?",
      "answer": "Suggest practical remedies. If Badhaka is involved, suggest spiritual/karmic remedies. Use 'remedial_measures' data."
    }
  ],
  "final_thoughts": "Positive summary emphasizing prevention and wellness path.",
  "follow_up_questions": [
    "🏥 How to improve my immunity?",
    "🧘 Best yoga/exercise for my body type?",
    "💊 Specific dietary precautions?",
    "🌿 Natural remedies for my weak planets?"
  ]
}

CRITICAL: Your entire response must be valid JSON starting with { and ending with }.
Do NOT include any text before or after the JSON object.
Do NOT use HTML div tags or HTML formatting.
Use <br> for line breaks within JSON strings.
Escape quotes properly: \"text\"
DISCLAIMER: Always mention this is astrological guidance, not medical advice
"""
            
            # Generate AI response
            gemini_analyzer = GeminiChatAnalyzer()
            ai_result = await gemini_analyzer.generate_chat_response(
                health_question, 
                context, 
                [], 
                request.language, 
                request.response_style
            )
            
            if ai_result['success']:
                # Parse AI response
                try:
                    ai_response_text = ai_result.get('response', '')
                    print(f"📄 PARSING HEALTH RESPONSE length: {len(ai_response_text)}")

                    # Extract and clean JSON
                    import html
                    import re
                    
                    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                    else:
                        json_match = re.search(r'({.*})', ai_response_text, re.DOTALL)
                        if json_match:
                            json_text = json_match.group(1)
                        else:
                            json_text = ai_response_text

                    decoded_json = html.unescape(json_text)
                    
                    replacements = {
                        '&quot;': '"',
                        '&amp;': '&',
                        '&lt;': '<',
                        '&gt;': '>',
                        '&#39;': "'",
                        '&apos;': "'"
                    }
                    for code, char in replacements.items():
                        decoded_json = decoded_json.replace(code, char)

                    parsing_successful = False
                    try:
                        parsed_response = json.loads(decoded_json)
                        parsing_successful = True
                        print(f"✅ JSON PARSED SUCCESSFULLY")
                        print(f"   Keys: {list(parsed_response.keys())}")
                        print(f"   Questions count: {len(parsed_response.get('detailed_analysis', []))}")
                    except json.JSONDecodeError as parse_error:
                        print(f"⚠️ Standard parse failed: {parse_error}")
                        try:
                            cleaned_json = re.sub(r'\n(?![\s]*")', '<br>', decoded_json)
                            cleaned_json = cleaned_json.replace('\\\\"', '\\"')
                            parsed_response = json.loads(cleaned_json)
                            parsing_successful = True
                            print(f"✅ JSON PARSED AFTER CLEANUP")
                            print(f"   Keys: {list(parsed_response.keys())}")
                            print(f"   Questions count: {len(parsed_response.get('detailed_analysis', []))}")
                        except json.JSONDecodeError as cleanup_error:
                            print(f"❌ JSON parsing failed: {cleanup_error}")
                            print(f"📄 Raw response appears to be HTML, using as raw_response")
                            # If JSON parsing fails, treat as HTML response
                            parsed_response = {
                                "raw_response": ai_response_text,
                                "quick_answer": "Analysis completed successfully.",
                                "detailed_analysis": [],
                                "final_thoughts": "Analysis provided in detailed format.",
                                "follow_up_questions": []
                            }
                            parsing_successful = True  # HTML response is still valid
                    
                    # Build complete response with advanced data indicators
                    health_insights = {
                        'health_analysis': {
                            'json_response': parsed_response if 'raw_response' not in parsed_response else None,
                            'raw_response': parsed_response.get('raw_response'),
                            'summary': 'Advanced Vedic health analysis with Mrityu Bhaga, Badhaka, and D-30 calculations.'
                        },
                        'enhanced_context': True,
                        'advanced_calculations': {
                            'mrityu_bhaga': True,
                            'badhaka_analysis': True,
                            'd30_trimsamsa': True,
                            'functional_malefics': True
                        },
                        'questions_covered': len(parsed_response.get('detailed_analysis', [])),
                        'context_type': 'health_ai_context_generator_advanced',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    # Only deduct credits if parsing was successful
                    if parsing_successful:
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
                    else:
                        print(f"⚠️ Skipping credit deduction due to parsing failure")
                    
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
            timezone=request.timezone or 'UTC+5:30'
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
