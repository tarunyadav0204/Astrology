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
from ai.gemini_chat_analyzer import GeminiChatAnalyzer

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

# Initialize components
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
                'timezone': request.timezone or 'UTC+5:30',
                'gender': request.gender,
                'current_year': date.today().year
            }
            
            # Build marriage context
            context = await asyncio.get_event_loop().run_in_executor(
                None, 
                marriage_context_generator.build_marriage_context,
                birth_data
            )
            
            # Add marriage-specific AI instructions to context
            context['marriage_analysis_instructions'] = {
                'focus_areas': [
                    'Precise timing using Dasha combined with Jupiter/Saturn Transits',
                    'Spouse appearance and profession using D9 (Navamsa)',
                    'Mangal Dosha intensity (Low/High) and exact remedies',
                    'Nature of relationship (Love vs Arranged)'
                ],
                'classical_methods': [
                    'Use "Double Transit Theory": Marriage happens when Jupiter AND Saturn influence the 7th house/lord',
                    'Check D9 (Navamsa) Lagna and 7th Lord for the final confirmation of timing',
                    'Use Vimshottari Dasha for the broad timeframe',
                    'Use Jupiter Transit for the specific year of the event'
                ],
                'response_format': 'Strict JSON. Be specific with ages and years. Avoid generic advice.'
            }
            
            # Universal status-agnostic marriage question
            marriage_question = """
As an expert Vedic astrologer, analyze the birth chart for **Relationship and Marriage Destiny**.
Note: The user's marital status is UNKNOWN. You must frame your answers to be valuable for both single and married individuals.

STRATEGY FOR AMBIGUITY:
- Instead of "You will marry in...", use phrases like "Strong activation of the 7th house (Marriage/Partnership) occurs in..."
- Frame timing as "Relationship Milestones". For singles, this is marriage. For married, this is a renewal of vows, childbirth, or a significant joint event.
- Focus on the **Nature of the Partner** and **Quality of Life**, which applies to everyone.

CRITICAL INSTRUCTION FOR TIMING:
Identify the "High Probability Windows" for relationship events by cross-referencing Dasha and Transits (Jupiter/Saturn).

CRITICAL REALISM CHECK:
Ignore any astrological activations that occur before Age 22 for "Marriage Timing".
If a strong period appears at age 18-21, interpret it as a "Relationship Learning Phase" or "Serious Relationship", NOT a wedding.
Prioritize windows between Age 24-32 for the "Primary Window".

STRICT JSON FORMAT REQUIRED (Use markdown formatting for emphasis):
Respond ONLY with a valid JSON object.

{
  "quick_answer": "A summary of the 7th house strength. E.g., 'Your chart shows a relationship dynamic driven by intellect (Mercury). The years <strong>2026-2027</strong> mark a significant relationship milestone.'",
  "detailed_analysis": [
    {
      "question": "What is the timeline for major relationship events?",
      "answer": "<strong>Primary Activation Window: [Year] to [Year]</strong><br>Reason: The [Planet] Dasha and Jupiter Transit activate your 7th house.<br><em>Implication:</em> This period marks a significant evolution in your personal life—whether that manifests as a new union or the deepening of an existing bond."
    },
    {
      "question": "What is the personality and nature of my partner?", 
      "answer": "Describe the spouse's likely traits (D9 & 7th Lord). E.g., 'Your 7th lord in a fire sign suggests a partner who is ambitious and energetic, possibly in a technical or leadership role.'"
    },
    {
      "question": "Are there any Doshas (Mars/Saturn) affecting harmony?",
      "answer": "Analyze Mangal Dosha or Saturn aspects. Explain how this creates 'friction' or 'delays' generally, without assuming current status."
    },
    {
      "question": "Is my destiny inclined towards Love or Traditional connection?",
      "answer": "Analyze the 5th-7th house connection. Discuss the 'style' of the relationship (Romantic/Spontaneous vs. Stable/Traditional)."
    },
    {
      "question": "What is the key to happiness in my specific chart?",
      "answer": "Look at the D9 Navamsa. Give advice like 'You need intellectual stimulation' or 'You need emotional space' based on the chart."
    },
    {
      "question": "What remedies strengthen my relationship luck?",
      "answer": "List 2 generic remedies that help both finding a partner AND keeping peace (e.g., 'Donate to X', 'Worship Goddess Katyayani')."
    }
  ],
  "final_thoughts": "A positive summary about the long-term promise of the 7th house.",
  "follow_up_questions": [
    "📅 Is [Next Year] significant for love?",
    "❤️ How to improve compatibility?",
    "💍 What are my partner's key traits?",
    "⚡ Remedies for relationship peace?"
  ]
}

CRITICAL JSON SAFETY RULES:
1. Escape ALL double quotes inside strings: \\\"text\\\"
2. No line breaks inside JSON strings - use <br> tags instead
3. Validate JSON structure before responding
"""
            
            # Generate AI response
            gemini_analyzer = GeminiChatAnalyzer()
            ai_result = await gemini_analyzer.generate_chat_response(
                marriage_question, 
                context, 
                [], 
                request.language, 
                request.response_style
            )
            
            if ai_result['success']:
                # Parse AI response
                try:
                    ai_response_text = ai_result.get('response', '')
                    print(f"📄 PARSING MARRIAGE RESPONSE length: {len(ai_response_text)}")

                    # 1. EXTRACT JSON
                    import html
                    import re
                    
                    # Try finding markdown block first
                    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                    else:
                        # Try finding the first opening { and last closing }
                        json_match = re.search(r'({.*})', ai_response_text, re.DOTALL)
                        if json_match:
                            json_text = json_match.group(1)
                        else:
                            json_text = ai_response_text

                    # 2. CLEANUP HTML ENTITIES (Common issue with Gemini)
                    # Decode HTML entities (e.g., &quot; -> ")
                    decoded_json = html.unescape(json_text)
                    
                    # Double check specific troublesome entities just in case
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

                    # 3. PARSE JSON
                    parsing_successful = False
                    try:
                        # Attempt 1: Parse the clean string
                        parsed_response = json.loads(decoded_json)
                        parsing_successful = True
                        print(f"✅ JSON PARSED SUCCESSFULLY")

                    except json.JSONDecodeError:
                        print(f"⚠️ Standard parse failed. Attempting aggressive cleanup...")
                        try:
                            # Attempt 2: Fix newlines inside strings (common LLM error)
                            # This regex looks for newlines that are NOT followed by a JSON key
                            # It replaces them with <br>
                            cleaned_json = re.sub(r'\n(?![\s]*")', '<br>', decoded_json)
                            
                            # Fix triple backslashes which sometimes happen
                            cleaned_json = cleaned_json.replace('\\\\"', '\\"')
                            
                            parsed_response = json.loads(cleaned_json)
                            parsing_successful = True
                            print(f"✅ JSON PARSED AFTER CLEANUP")
                            
                        except json.JSONDecodeError:
                            print(f"❌ JSON parsing failed completely.")
                            # Don't deduct credits for parsing failures
                            yield f"data: {json.dumps({'status': 'error', 'message': 'AI response formatting error. Please try again.'})}\n\n"
                            return
                    
                    print(f"   Keys: {list(parsed_response.keys())}")
                    print(f"   Questions count: {len(parsed_response.get('detailed_analysis', []))}")
                    
                    # Build complete response
                    marriage_insights = {
                        'marriage_analysis': {
                            'json_response': parsed_response,
                            'summary': 'Comprehensive marriage analysis based on Vedic astrology principles.'
                        },
                        'enhanced_context': True,
                        'questions_covered': len(parsed_response.get('detailed_analysis', [])),
                        'context_type': 'marriage_ai_context_generator',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    # Only deduct credits if parsing was successful
                    if parsing_successful:
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
                    else:
                        print(f"⚠️ Skipping credit deduction due to parsing failure")
                    
                    # Cache the analysis
                    try:
                        import sqlite3
                        import hashlib
                        
                        # Create birth hash
                        birth_hash = hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()
                        
                        conn = sqlite3.connect('astrology.db')
                        cursor = conn.cursor()
                        
                        # Create table if not exists
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS ai_marriage_insights (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                birth_hash TEXT UNIQUE,
                                insights_data TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        # Insert or replace analysis
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
                error_response = {
                    'marriage_analysis': 'AI analysis failed. Please try again.',
                    'enhanced_context': False,
                    'error': ai_result.get('error', 'Unknown error') if ai_result else 'No response from AI'
                }
                yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\n\n"
                
        except Exception as e:
            print(f"❌ MARRIAGE ANALYSIS ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            full_traceback = traceback.format_exc()
            print(f"Full traceback:\n{full_traceback}")
            
            error_response = {
                'marriage_analysis': f'Analysis error: {str(e)}. Please try again.',
                'enhanced_context': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            yield f"data: {json.dumps({'status': 'error', 'error': str(e), 'error_type': type(e).__name__})}\n\n"
    
    return StreamingResponse(
        generate_marriage_analysis(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/get-analysis")
async def get_previous_analysis(request: MarriageAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get previously generated marriage analysis if exists"""
    import sqlite3
    import hashlib
    
    try:
        # Create birth hash
        birth_hash = hashlib.md5(f"{request.date}_{request.time}_{request.place}".encode()).hexdigest()
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Query for existing analysis
        cursor.execute("""
            SELECT insights_data FROM ai_marriage_insights WHERE birth_hash = ?
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

@router.get("/test")
async def test_marriage_routes():
    """Test endpoint to verify marriage routes are working"""
    return {"status": "success", "message": "Marriage routes are working"}