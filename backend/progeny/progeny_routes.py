from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os
import json
import asyncio
import sqlite3
import hashlib
import re
import html
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.progeny_ai_context_generator import ProgenyAIContextGenerator
from ai.gemini_chat_analyzer import GeminiChatAnalyzer

class ProgenyAnalysisRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: str  # Mandatory for Progeny
    language: Optional[str] = 'english'
    response_style: Optional[str] = 'detailed'
    force_regenerate: Optional[bool] = False  # Bypass cache for regeneration
    analysis_focus: str = "first_child"  # Options: "first_child", "next_child", "parenting"
    children_count: int = 0

router = APIRouter(prefix="/progeny", tags=["progeny"])

# Initialize
context_generator = ProgenyAIContextGenerator()
credit_service = CreditService()

@router.post("/ai-insights")
async def get_progeny_insights(request: ProgenyAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Analyze Progeny/Childbirth prospects - Requires Credits"""
    
    # Debug logging for gender validation
    print(f"🔍 [DEBUG] Progeny API: Received request for user {current_user.userid}")
    print(f"🔍 [DEBUG] Progeny API: Request data: {request.dict()}")
    print(f"⚧️ [DEBUG] Progeny API: Gender value: '{request.gender}'")
    print(f"⚧️ [DEBUG] Progeny API: Gender type: {type(request.gender)}")
    print(f"⚧️ [DEBUG] Progeny API: Gender stripped: '{request.gender.strip() if request.gender else None}'")
    print(f"⚧️ [DEBUG] Progeny API: Gender validation: not request.gender = {not request.gender}, gender.strip() == '' = {request.gender.strip() == '' if request.gender else 'N/A'}")
    
    # Validate gender is provided
    if not request.gender or request.gender.strip() == "":
        print(f"❌ [DEBUG] Progeny API: Gender validation FAILED - returning GENDER_REQUIRED error")
        async def gender_required_response():
            yield f"data: {json.dumps({'status': 'error', 'error_code': 'GENDER_REQUIRED', 'message': 'Gender is required for progeny analysis. Please update your profile to continue.'})}\n\n"
        return StreamingResponse(gender_required_response(), media_type="text/plain")
    
    print(f"✅ [DEBUG] Progeny API: Gender validation PASSED - proceeding with analysis")
    
    # 1. Check Cache First (Prevent duplicate charges) - Skip if regenerating
    birth_hash = hashlib.md5(f"{request.date}_{request.time}_{request.place}_{request.gender}_progeny".encode()).hexdigest()
    
    if not request.force_regenerate:
        try:
            conn = sqlite3.connect('astrology.db')
            cursor = conn.cursor()
            cursor.execute("SELECT insights_data FROM ai_career_insights WHERE birth_hash = ?", (birth_hash,))
            cached_result = cursor.fetchone()
            conn.close()
            
            if cached_result:
                print(f"✅ Serving cached Progeny result for {birth_hash}")
                # Format to match the SSE stream structure
                final_response = {'status': 'complete', 'data': json.loads(cached_result[0]), 'cached': True}
                
                async def serve_cache():
                    yield f"data: {json.dumps(final_response)}\n\n"
                
                return StreamingResponse(serve_cache(), media_type="text/plain")
        except Exception as e:
            print(f"⚠️ Cache check failed: {e}")
    else:
        print(f"🔄 [DEBUG] Progeny API: Force regenerate requested - bypassing cache")

    # 2. Check Credits
    analysis_cost = credit_service.get_credit_setting('progeny_analysis_cost') or 15
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < analysis_cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {analysis_cost}")

    async def generate_analysis():
        try:
            birth_data = request.dict()
            print(f"🔍 [DEBUG] Progeny API: Birth data for analysis: {birth_data}")
            print(f"⚧️ [DEBUG] Progeny API: Gender in birth_data: '{birth_data.get('gender')}'")
            
            # Build Context with Transit Data
            print(f"🔄 [DEBUG] Progeny API: Building context with birth_data...")
            try:
                # Build base progeny context
                context = await asyncio.get_event_loop().run_in_executor(
                    None, context_generator.build_progeny_context, birth_data
                )
                
                # Add transit data for next 12 months (progeny timing is crucial)
                from chat.chat_context_builder import ChatContextBuilder
                chat_builder = ChatContextBuilder()
                current_year = datetime.now().year
                
                print(f"🔄 [DEBUG] Progeny API: Adding transit data for {current_year}-{current_year + 1}...")
                
                # Build static context first to populate cache
                try:
                    chat_builder._build_static_context(birth_data)
                    transit_context = chat_builder._build_dynamic_context(
                        birth_data, 
                        "progeny timing analysis", 
                        None, 
                        {'start_year': current_year, 'end_year': current_year + 1}
                    )
                except Exception as transit_error:
                    print(f"⚠️ [DEBUG] Progeny API: Transit data failed, continuing without: {transit_error}")
                    transit_context = {}
                
                # Merge transit data into progeny context
                if 'transit_activations' in transit_context:
                    context['transit_activations'] = transit_context['transit_activations']
                    print(f"✅ [DEBUG] Progeny API: Added {len(context['transit_activations'])} transit activations")
                
                if 'current_dashas' in transit_context:
                    context['current_dashas'] = transit_context['current_dashas']
                    print(f"✅ [DEBUG] Progeny API: Added current dasha information")
                
                print(f"✅ [DEBUG] Progeny API: Context built successfully with transit data")
            except Exception as context_error:
                print(f"❌ [DEBUG] Progeny API: Context building failed: {context_error}")
                print(f"❌ [DEBUG] Progeny API: Context error type: {type(context_error)}")
                import traceback
                print(f"❌ [DEBUG] Progeny API: Context traceback: {traceback.format_exc()}")
                raise context_error
            
            # --- DYNAMIC PROMPT LOGIC ---
            
            # SCENARIO 1: PARENTING (Focus on Relationship)
            if request.analysis_focus == 'parenting':
                specific_questions_json = """
  "detailed_analysis": [
    {
      "question": "What is the nature of my relationship with my children?",
      "answer": "Analyze D1 5th House and D7 Lagna. Explain if the bond is friendly, disciplined, or emotional.",
      "key_points": ["Parenting Style", "Bond Quality"],
      "astrological_basis": "5th House & D7 Lagna"
    },
    {
      "question": "What does my chart indicate about my children's success?",
      "answer": "Check Jupiter strength and D7 5th House. Strong Jupiter indicates wise/successful children.",
      "key_points": ["Children's Potential", "General Health"],
      "astrological_basis": "Jupiter & D7 5th House"
    },
    {
      "question": "Are there upcoming periods of concern or joy regarding my family?",
      "answer": "Analyze current Dasha. If 5th Lord or Jupiter is active, predict focus on children.",
      "key_points": ["Current Dasha Influence", "Transit Impact"],
      "astrological_basis": "Dasha & Transits"
    },
    {
      "question": "How can I best support my children astrologically?",
      "answer": "Based on the 5th lord's element, suggest a parenting approach.",
      "key_points": ["Parenting Advice", "Remedies"],
      "astrological_basis": "5th Lord Element"
    }
  ],"""
                system_role = "You are a Vedic Astrologer specializing in Parenting and Family Dynamics."
                focus_instruction = f"The user ALREADY HAS {request.children_count} children. Do NOT predict pregnancy timing. Focus on relationship and guidance."

            # SCENARIO 2: PLANNING NEXT CHILD (The Hybrid Case)
            elif request.analysis_focus == 'next_child':
                specific_questions_json = """
  "detailed_analysis": [
    {
      "question": "What does my chart indicate about expanding my family further?",
      "answer": "Analyze the D7 chart specifically for the NEXT child. (If user has 1, look at D7 7th house. If 2, look at D7 9th house).",
      "key_points": ["Promise for Next Child", "D7 Derived Houses"],
      "astrological_basis": "D7 Derived House Analysis"
    },
    {
      "question": "When is a favorable time for conceiving the next child?",
      "answer": "Analyze current Dasha and Transits. Check for Double Transit (Jupiter/Saturn) activation.",
      "key_points": ["Conception Window", "Transit Support"],
      "astrological_basis": "Vimshottari Dasha + Transits"
    },
    {
      "question": "Are there obstacles for this specific pregnancy?",
      "answer": "Check fertility Sphuta strength and current transits of nodes (Rahu/Ketu) over the 5th house.",
      "key_points": ["Obstacles", "Sphuta Strength"],
      "astrological_basis": "Sphuta & Nodal Transits"
    },
    {
      "question": "What remedies support family expansion?",
      "answer": "Suggest Santana Gopala Mantra or remedies for the D7 Lagna lord.",
      "key_points": ["Mantra", "Lifestyle"],
      "astrological_basis": "Remedial Measures"
    }
  ],"""
                system_role = "You are an empathetic Vedic Astrologer specializing in Family Expansion."
                focus_instruction = f"The user HAS {request.children_count} children and is PLANNING FOR MORE. Focus on the timing and potential for the *next* sibling."

            # SCENARIO 3: PLANNING FIRST CHILD (Default)
            else:
                specific_questions_json = """
  "detailed_analysis": [
    {
      "question": "What does my chart indicate about having children?",
      "answer": "Analyze D1 5th House and D7 5th House. Mention if the 'Promise' is strong.",
      "key_points": ["D1 5th House", "D7 Analysis"],
      "astrological_basis": "D1 & D7 Charts"
    },
    {
      "question": "Are there any astrological delays or obstacles?",
      "answer": "Discuss Saturn/Rahu influence on 5th house or if Sphuta strength is Moderate.",
      "key_points": ["Obstacles", "Sphuta Strength"],
      "astrological_basis": "Malefic Influences & Sphuta"
    },
    {
      "question": "When is a favorable time for family expansion?",
      "answer": "Analyze current Dasha and upcoming transits (Jupiter/Saturn Double Transit).",
      "key_points": ["Favorable Dasha", "Transits"],
      "astrological_basis": "Vimshottari Dasha + Transits"
    },
    {
      "question": "What remedies can support this journey?",
      "answer": "Suggest Santana Gopala Mantra or Jupiter remedies.",
      "key_points": ["Mantra", "Lifestyle"],
      "astrological_basis": "Remedial Measures"
    }
  ],"""
                system_role = "You are an empathetic Vedic Astrologer specializing in Family Expansion."
                focus_instruction = "Focus on fertility potential, timing of conception, and overcoming delays for the first child."

            # --- CONSTRUCT FINAL PROMPT ---
            question = f"""
{system_role} Analyze the chart based on the user's specific situation.

INPUT DATA:
1. **User Goal:** {focus_instruction}
2. **Gender:** {request.gender} (Sphuta Type: {context['progeny_analysis']['fertility_sphuta']['type']})
3. **Fertility Sphuta:** {context['progeny_analysis']['fertility_sphuta']['strength']}
4. **D7 Chart (Saptamsa):**
   - Lagna Lord: {context['progeny_analysis']['d7_analysis']['d7_lagna_lord']}
   - 5th House Planets: {', '.join(context['progeny_analysis']['d7_analysis']['planets_in_d7_5th']) or 'Empty'}
   - Summary: {context['progeny_analysis']['d7_analysis']['summary']}
5. **Timing Indicators:** {', '.join(context['progeny_analysis']['timing_indicators'])}
6. **Current Dasha:** {context.get('current_dashas', {}).get('mahadasha', {}).get('planet', 'Unknown')} MD / {context.get('current_dashas', {}).get('antardasha', {}).get('planet', 'Unknown')} AD
7. **Transit Data:** Next 12 months of major planetary transits available for precise timing

STRICT ETHICAL GUARDRAILS:
1. **NO MEDICAL DIAGNOSIS:** Never use words like "Infertile", "Sterile", or specific disease names. Use "Challenges", "Delays", or "Requires medical support".
2. **NO GENDER PREDICTION:** Do not predict Boy/Girl. Focus on the health/happiness of the child.
3. **EMPATHY:** This is a sensitive topic. Be supportive, not fatalistic.

RESPONSE FORMAT (JSON ONLY):
{{
  "quick_answer": "3-4 sentences summarizing the analysis based on user's specific focus.",
  {specific_questions_json}
  "final_thoughts": "A positive concluding message tailored to the user's situation."
}}
"""
            # Generate AI Response
            gemini = GeminiChatAnalyzer()
            ai_result = await gemini.generate_chat_response(
                question, context, [], request.language, request.response_style
            )
            
            if ai_result['success']:
                try:
                    # Robust Parsing (Regex Method)
                    ai_response_text = ai_result.get('response', '')
                    
                    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                    else:
                        json_match = re.search(r'({.*})', ai_response_text, re.DOTALL)
                        json_text = json_match.group(1) if json_match else ai_response_text

                    # Unescape HTML entities
                    decoded_json = html.unescape(json_text)
                    parsed_response = json.loads(decoded_json)
                    
                    # Deduct Credits
                    success = credit_service.spend_credits(
                        current_user.userid, 
                        analysis_cost, 
                        'progeny_analysis', 
                        f"Progeny for {request.name or 'User'}"
                    )
                    
                    if success:
                        # Cache the result
                        full_result = {'progeny_analysis': parsed_response}
                        try:
                            conn = sqlite3.connect('astrology.db')
                            cursor = conn.cursor()
                            
                            # --- SAFETY BLOCK START ---
                            cursor.execute("""
                                CREATE TABLE IF NOT EXISTS ai_career_insights (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    birth_hash TEXT UNIQUE,
                                    insights_data TEXT,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                )
                            """)
                            # --- SAFETY BLOCK END ---
                            
                            # Reuse the existing table
                            cursor.execute("""
                                INSERT OR REPLACE INTO ai_career_insights 
                                (birth_hash, insights_data, updated_at)
                                VALUES (?, ?, CURRENT_TIMESTAMP)
                            """, (birth_hash, json.dumps(full_result)))
                            conn.commit()
                            conn.close()
                        except Exception as cache_err:
                            print(f"⚠️ Cache save failed: {cache_err}")

                        yield f"data: {json.dumps({'status': 'complete', 'data': full_result})}\n\n"
                    else:
                         yield f"data: {json.dumps({'status': 'error', 'message': 'Credit deduction failed'})}\n\n"
                    
                except json.JSONDecodeError:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse AI response'})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'error', 'message': 'AI Generation Failed'})}\n\n"

        except Exception as e:
            print(f"❌ [DEBUG] Progeny API: General error: {e}")
            print(f"❌ [DEBUG] Progeny API: Error type: {type(e)}")
            import traceback
            print(f"❌ [DEBUG] Progeny API: Full traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate_analysis(), media_type="text/plain")