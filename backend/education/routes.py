"""
Education Analysis API Routes
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
from calculators.chart_calculator import ChartCalculator
from .education_analyzer import EducationAnalyzer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.education_ai_context_generator import EducationAIContextGenerator
from ai.gemini_chat_analyzer import GeminiChatAnalyzer

class EducationAnalysisRequest(BaseModel):
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

router = APIRouter(prefix="/education", tags=["education"])

# Initialize components
education_context_generator = EducationAIContextGenerator()
credit_service = CreditService()

@router.post("/analyze")
async def analyze_education(
    birth_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze education prospects using classical Vedic astrology
    """
    try:
        # Calculate chart - convert dict to object-like structure
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Perform education analysis
        analyzer = EducationAnalyzer(birth_data, chart_data)
        analysis = analyzer.analyze_education()
        
        return {
            "success": True,
            "analysis": analysis,
            "birth_data": birth_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/ai-analyze")
async def analyze_education_ai(request: EducationAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Analyze education prospects with AI - requires credits"""
    
    # Check credit cost and user balance
    education_cost = credit_service.get_credit_setting('education_analysis_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < education_cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {education_cost} credits but have {user_balance}."
        )
    
    async def generate_education_analysis():
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
            
            # Build education context
            context = await asyncio.get_event_loop().run_in_executor(
                None, 
                education_context_generator.build_education_context,
                birth_data
            )
            
            # Education-specific AI question
            education_question = """
As an expert Vedic astrologer, analyze the birth chart for **Education, Intelligence, and Academic Success**.

CRITICAL DATA UTILIZATION INSTRUCTIONS:
1. **D-24 (Chaturvimshamsa)**: This is the primary chart for education. Check 'education_charts.d24_analysis'. 
   - If D-24 Lagna Lord is strong, predict **High Academic Distinctions** (Masters/PhD).
   - If weak, predict obstacles in higher education.
2. **Technical vs. Creative**: Check 'subject_analysis' and any 'technical_aptitude' data.
   - If Mars/Saturn/Rahu influence the 5th/Mercury, suggest **STEM/Engineering**.
   - If Venus/Moon influence, suggest **Arts/Humanities/Psychology**.
3. **Learning Style**: Use 'learning_capacity' (Mercury/Moon analysis).
   - Specify if the native learns better through **Visuals**, **Listening**, or **Rote Memorization**.
4. **Education Yogas**: Check 'education_yogas' (Saraswati, Budh-Aditya). Mention them by name if present.
5. **Timing**: Cross-reference 'current_dashas' with 'education_timing'. Identify periods favorable for **Exams** or **Admissions**.

CRITICAL: You MUST respond with ONLY a JSON object. NO other text, NO HTML, NO explanations.
Start your response with { and end with }. Use markdown ** for bold text within JSON strings.
{
  "quick_answer": "Summary of academic potential, best fields of study, and current educational phase.",
  "detailed_analysis": [
    {
      "question": "What is my natural learning potential and intelligence level?",
      "answer": "Analyze 5th House, Mercury, and **Jupiter**. Mention their Intelligence Type (Analytical vs. Wisdom).",
      "key_points": ["Strengths", "Weaknesses"],
      "astrological_basis": "e.g., Mercury in Virgo creates strong analytical logic..."
    },
    {
      "question": "Which subjects or career paths suit me best?",
      "answer": "Based on **Technical Aptitude** and **Subject Analysis**. Be specific (e.g., Computer Science vs Civil Engineering vs Literature)."
    },
    {
      "question": "Will I have success in higher education (Masters/PhD)?",
      "answer": "Analyze the **9th House** and **D-24 Chart**. Look for connection between 5th and 9th lords."
    },
    {
      "question": "What is the best way for me to study?",
      "answer": "Use learning_capacity data. Suggest study hacks based on their Mercury/Moon sign (e.g., Take breaks vs Deep focus)."
    },
    {
      "question": "Are there any obstacles or breaks in education?",
      "answer": "Check **Saturn/Rahu** influence on 4th/5th houses. Check Dasha periods."
    }
  ],
  "final_thoughts": "Encouraging summary focusing on maximizing their unique intellectual strengths.",
  "follow_up_questions": [
    "🎓 Best timing for higher studies?",
    "📚 Will I succeed in competitive exams?",
    "🌍 Chances of foreign education?",
    "🧠 Remedies for concentration?"
  ]
}

CRITICAL: Your entire response must be valid JSON starting with { and ending with }.
Do NOT include any text before or after the JSON object.
Do NOT use HTML div tags or HTML formatting.
Use <br> for line breaks within JSON strings.
Escape quotes properly: \"text\"
DISCLAIMER: Always mention this is astrological guidance, not career counseling.
"""
            
            # Generate AI response
            gemini_analyzer = GeminiChatAnalyzer()
            ai_result = await gemini_analyzer.generate_chat_response(
                education_question, 
                context, 
                [], 
                request.language, 
                request.response_style
            )
            
            if ai_result['success']:
                # Parse AI response
                try:
                    ai_response_text = ai_result.get('response', '')
                    print(f"📄 PARSING EDUCATION RESPONSE length: {len(ai_response_text)}")

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
                        except json.JSONDecodeError as cleanup_error:
                            print(f"❌ JSON parsing failed completely. Treating as HTML response.")
                            print(f"📄 Raw response length: {len(ai_response_text)}")
                            print(f"📄 Raw response preview: {ai_response_text[:500]}...")
                            # If JSON parsing fails completely, treat as HTML response
                            parsed_response = {
                                "raw_response": ai_response_text,
                                "quick_answer": "Analysis completed successfully.",
                                "detailed_analysis": [],
                                "final_thoughts": "Analysis provided in detailed format.",
                                "follow_up_questions": []
                            }
                            parsing_successful = True  # HTML response is still valid
                    
                    # Build complete response
                    education_insights = {
                        'education_analysis': {
                            'json_response': parsed_response if 'raw_response' not in parsed_response else None,
                            'raw_response': parsed_response.get('raw_response'),
                            'summary': 'Advanced Vedic education analysis with house and planetary calculations.'
                        },
                        'enhanced_context': True,
                        'questions_covered': len(parsed_response.get('detailed_analysis', [])),
                        'context_type': 'education_ai_context_generator',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    # Only deduct credits if parsing was successful
                    if parsing_successful:
                        success = credit_service.spend_credits(
                            current_user.userid, 
                            education_cost, 
                            'education_analysis', 
                            f"Education analysis for {birth_data.get('name', 'user')}"
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
                            CREATE TABLE IF NOT EXISTS ai_education_insights (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                birth_hash TEXT UNIQUE,
                                insights_data TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO ai_education_insights 
                            (birth_hash, insights_data, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (birth_hash, json.dumps(education_insights)))
                        
                        conn.commit()
                        conn.close()
                        print(f"💾 Analysis cached successfully")
                    except Exception as cache_error:
                        print(f"⚠️ Failed to cache analysis: {cache_error}")
                    
                    final_response = {'status': 'complete', 'data': education_insights, 'cached': False}
                    response_json = json.dumps(final_response)
                    print(f"🚀 SENDING FINAL EDUCATION RESPONSE: {len(response_json)} chars")
                    yield f"data: {response_json}\n\n"
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON PARSING FAILED: {e}")
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse AI response'})}\n\n"
                
            else:
                error_message = ai_result.get('error', 'AI analysis failed') if ai_result else 'No response from AI'
                yield f"data: {json.dumps({'status': 'error', 'error': error_message})}\n\n"
                
        except Exception as e:
            print(f"❌ EDUCATION ANALYSIS ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            full_traceback = traceback.format_exc()
            print(f"Full traceback:\n{full_traceback}")
            
            error_message = str(e) if str(e) else 'Unknown error occurred'
            yield f"data: {json.dumps({'status': 'error', 'error': error_message, 'error_type': type(e).__name__})}\n\n"
    
    return StreamingResponse(
        generate_education_analysis(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/get-analysis")
async def get_previous_education_analysis(request: EducationAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get previously generated education analysis if exists"""
    import sqlite3
    import hashlib
    
    try:
        birth_hash = hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT insights_data FROM ai_education_insights WHERE birth_hash = ?
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

@router.get("/constants")
async def get_education_constants():
    """
    Get education analysis constants and explanations
    """
    from .constants import EDUCATION_HOUSES, EDUCATION_PLANETS, SUBJECT_RECOMMENDATIONS
    
    return {
        "houses": EDUCATION_HOUSES,
        "planets": EDUCATION_PLANETS,
        "subjects": SUBJECT_RECOMMENDATIONS
    }