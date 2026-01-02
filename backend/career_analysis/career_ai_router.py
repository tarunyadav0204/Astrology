from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os
import json
import asyncio
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.career_ai_context_generator import CareerAIContextGenerator
from ai.structured_analyzer import StructuredAnalysisAnalyzer

class CareerAnalysisRequest(BaseModel):
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

router = APIRouter(prefix="/career", tags=["career"])

# Initialize components
career_context_generator = CareerAIContextGenerator()
credit_service = CreditService()

@router.post("/ai-insights")
async def get_career_ai_insights(request: CareerAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Analyze career prospects with AI - requires credits"""
    
    # Check credit cost and user balance
    career_cost = credit_service.get_credit_setting('career_analysis_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < career_cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {career_cost} credits but have {user_balance}."
        )
    
    async def generate_career_analysis():
        try:
            # Prepare birth data
            birth_data = {
                'name': request.name,
                'date': request.date,
                'time': request.time,
                'place': request.place,
                'latitude': request.latitude or 28.6139,
                'longitude': request.longitude or 77.2090,
                'timezone': request.timezone or 'UTC+0',
                'gender': request.gender
            }
            
            # Build career context
            context = await asyncio.get_event_loop().run_in_executor(
                None, 
                career_context_generator.build_career_context,
                birth_data
            )
            
            # Career-specific AI question
            career_question = """
You are an expert Vedic astrologer specializing in Career and Professional direction (Karma). Analyze the birth chart for Professional Success.

CRITICAL INPUT DATA TO ANALYZE (Priority Order):
1. **Amatyakaraka (AmK) in D10 (Dasamsa):** MOST IMPORTANT - Check 'd10_detailed.amatyakaraka_analysis'.
   - AmK in 10th of D10 = MASSIVE SUCCESS/CEO Potential.
   - AmK in 1st/5th/9th = Smooth steady growth.
   - AmK in 6th/8th/12th = Success through struggle, research, or foreign lands.
2. **Modern Career Indicators (Rahu/Ketu in D10):**
   - **CRITICAL:** If Rahu is in D10 Kendra (1,4,7,10) or Upachaya (3,6,11), predict TECHNOLOGY, AI, CODING, AVIATION, or FOREIGN MNC careers. Do not interpret this as negative; it is the primary indicator for modern tech success.
   - Ketu in D10 Kendra/Upachaya = Coding, Research, Mathematics, Precision work.
3. **10th Lord Nakshatra:** Use this for SPECIFIC INDUSTRY nuance.
   - Example: Mars in Chitra = Architect/Designer. Mars in Mrigashira = Researcher/Analyst.
4. **Arudha Lagna (AL) vs Rajya Pada (A10):**
   - AL = Public Status/Fame. A10 = Actual Daily Workplace.
   - Strong AL + Weak A10 = Famous but broke/unhappy work.
   - Weak AL + Strong A10 = Wealthy but low profile.
5. **Planetary Dignity Nuance:**
   - **Exalted:** High ease of success.
   - **Debilitated:** If in 3rd/6th/11th, predict "Massive success after initial struggle/hard work." If in other houses, predict "Frustration."
6. **D10 10th House Planets:** These show the EXACT role. (e.g., Mercury = Analytics, Sun = Leadership)

IMPORTANT: You MUST respond with EXACTLY this JSON structure. Do not add extra fields.

{
  "quick_answer": "A sharp, 3-sentence summary. Mention the primary strength (e.g., 'Strong AmK') and the main field (e.g., 'Tech Leadership').",
  "detailed_analysis": [
    {
      "question": "What is my true professional purpose (Dharma)?",
      "answer": "Analyze the Amatyakaraka (AmK) in D10. If AmK is in 10th/1st/5th/9th, predict high ambition/status. If Rahu is strong in D10, mention Innovation/Tech.",
      "key_points": ["AmK Position", "Soul's Career Desire"],
      "astrological_basis": "Amatyakaraka in D10 (Jaimini)"
    },
    {
      "question": "Status vs. Reality: Will I be famous or just work hard?",
      "answer": "Compare Arudha Lagna (AL) vs 10th House/A10. Strong AL with benefics = Fame. Strong 10th with weak AL = Silent achiever.",
      "key_points": ["Public Image (AL)", "Work Reality (A10)"],
      "astrological_basis": "Arudha Lagna vs Rajya Pada"
    },
    {
      "question": "What specific industry or niche is best for me?",
      "answer": "Synthesize: 1. 10th Lord Nakshatra (The Industry) + 2. D10 10th House Planets (The Role). If Rahu is prominent, suggest AI/Tech/Data.",
      "key_points": ["Primary Industry", "Specific Niche"],
      "astrological_basis": "10th Lord Nakshatra + D10 Analysis"
    },
    {
      "question": "Should I choose Job, Business, or Freelancing?",
      "answer": "Analyze D10 Ascendant and 7th House. 6th House/Saturn strong = High level Service/Job. 7th House/Mercury strong = Business. Rahu strong = Freelance/Consulting.",
      "key_points": ["Primary Path", "Risk Tolerance"],
      "astrological_basis": "6th vs 7th House Strength + D10 Ascendant"
    },
    {
      "question": "Will I have success in Government, Corporate, or Startups?",
      "answer": "Sun/Mars strong = Government/Defense. Rahu/Mercury strong = Corporate/MNC/Tech/Startup. Saturn strong = Public Sector.",
      "key_points": ["Sector Suitability", "Authority Level"],
      "astrological_basis": "Sun/Mars vs Rahu/Mercury Strength"
    },
    {
      "question": "Will I face career instability or breaks?",
      "answer": "Check 8th House and 10th Lord Dignity. If 10th Lord is in 8th or Debilitated (without Neechabhanga), predict transformation/changes.",
      "key_points": ["Stability Score", "Risk Periods"],
      "astrological_basis": "8th House & 10th Lord Dignity"
    },
    {
      "question": "What are my 'Sniper' skills (Unique Talents)?",
      "answer": "Identify the planet with the highest Shadbala or the D10 10th house occupant. Mention specific skills (e.g., 'Debugging' for Ketu, 'Strategy' for Mercury).",
      "key_points": ["Core Talent", "Hidden Skill"],
      "astrological_basis": "Strongest Planet & D10 10th House"
    },
    {
      "question": "When is my next big career breakthrough?",
      "answer": "Analyze Current Dasha. If Dasha Lord is placed in 10th/11th/1st/5th/9th of D1 or D10, predict growth.",
      "key_points": ["Timing", "Dasha Influence"],
      "astrological_basis": "Vimshottari Dasha Analysis"
    },
    {
      "question": "Action Plan: What should I do right now?",
      "answer": "Practical advice based on the weakest link in the chart (e.g., 'Improve communication' if Mercury is weak).",
      "key_points": ["Immediate Step", "Long-term Goal"],
      "astrological_basis": "Chart Synthesis"
    }
  ],
  "final_thoughts": "One empowering concluding paragraph summarizing the career trajectory.",
  "follow_up_questions": [
    "📅 When will I get a promotion?",
    "💼 Is a startup suitable for me?",
    "✈️ Chances of working abroad?",
    "💰 When will my income peak?"
  ]
}

CRITICAL RULES:
1. **JSON ONLY:** Output must be valid JSON. No markdown text before or after.
2. **Be Specific:** Do not say "You can work in technology." Say "You are suited for Backend Development or Data Science due to Ketu in D10."
3. **Modernize:** Interpret classical combinations for the 2024 job market (e.g., 8th house = Research/Data Mining, not just 'misfortune').
4. **Use the Input:** You MUST reference the provided Nakshatras and D10 placements in your answers.
5. **Rahu/Ketu = Tech:** If Rahu is in D10 Kendra/Upachaya, predict Tech/AI/Innovation. If Ketu is strong, predict Coding/Research.
6. **Debilitation Nuance:** Debilitated planet in 3rd/6th/11th = Success through hard work. In other houses = Frustration/Struggle.

CRITICAL ANALYSIS REQUIREMENTS (Priority Order):
1. **Amatyakaraka in D10 (HIGHEST PRIORITY):** Check 'd10_detailed.amatyakaraka_analysis'. This determines SUCCESS LEVEL. AmK in 10th of D10 = Top 1% success.
2. **Arudha Lagna Analysis:** Check 'arudha_analysis.status_vs_work_analysis'. This distinguishes FAME from WORK. Strong AL = public recognition.
3. **10th Lord Nakshatra:** Determines SPECIFIC INDUSTRY (e.g., Krittika = Engineering/Military, Hasta = Handicrafts)
4. **D10 10th House Planets:** Shows EXACT PROFESSION (not just D10 ascendant)
5. **Planetary Dignity:** Exalted/debilitated/retrograde status of career planets
6. **Aspects:** Planets aspecting 10th house
7. Analyze ALL career houses: 10th (career), 6th (service), 7th (business), 2nd (income), 11th (gains)
8. Check Saturn (Karma Karaka) and Sun (authority) dignity and nakshatra
9. Identify career yogas
10. Analyze dasha periods with nakshatra influences

HOUSE-SPECIFIC CAREER INTERPRETATIONS:
- 10th House: Primary career, profession, reputation, authority
- 6th House: Service, employment, daily work, subordinates, competition
- 7th House: Business, partnerships, public dealings, contracts, trade
- 2nd House: Earned wealth, speech value, family business
- 11th House: Gains, income, large organizations, fulfillment

PLANETARY CAREER SIGNIFICANCES (Modified by Nakshatra):
- Saturn: Discipline, hard work - BUT nakshatra determines if traditional (Pushya) or mystical (Uttara Bhadrapada)
- Sun: Authority, government - BUT nakshatra shows if administrative (Krittika) or creative (Bharani)
- Mercury: Business, communication - BUT nakshatra indicates if strategic (Ashlesha) or protective (Jyeshtha)
- Jupiter: Teaching, consulting - BUT nakshatra shows if philosophical (Vishakha) or transformative (Purva Bhadrapada)
- Mars: Engineering, sports - BUT nakshatra determines if research (Mrigashira) or design (Chitra)
- Venus: Arts, beauty - BUT nakshatra shows if creative (Bharani) or luxurious (Purva Phalguni)
- Moon: Public dealings - BUT nakshatra indicates if skillful (Hasta) or communicative (Shravana)

NAKSHATRA CAREER EXAMPLES:
- Ashwini: Healing, Medical, Emergency services
- Krittika: Engineering, Surgery, Military, Sharp/cutting work
- Magha: Administration, Government, Lineage-based roles
- Hasta: Handicrafts, Healing, Manual skills
- Chitra: Architecture, Design, Fashion, Photography

CRITICAL RULES:
1. Response must be ONLY valid JSON - no extra text
2. Use EXACTLY the field names shown above
3. Include exactly 9 questions in detailed_analysis array
4. Use ** for bold text in JSON strings
5. Be honest about challenges and realistic about potential

"""
            
            # Generate AI response using structured analyzer
            analyzer = StructuredAnalysisAnalyzer()
            ai_result = await analyzer.generate_structured_report(
                career_question, 
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
                    
                    career_insights = {
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
                        career_cost, 
                        'career_analysis', 
                        f"Career analysis for {birth_data.get('name', 'user')}"
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
                            CREATE TABLE IF NOT EXISTS ai_career_insights (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                birth_hash TEXT UNIQUE,
                                insights_data TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO ai_career_insights 
                            (birth_hash, insights_data, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (birth_hash, json.dumps(career_insights)))
                        
                        conn.commit()
                        conn.close()
                        print(f"💾 Analysis cached successfully")
                    except Exception as cache_error:
                        print(f"⚠️ Failed to cache analysis: {cache_error}")
                    
                    final_response = {'status': 'complete', 'data': career_insights, 'cached': False}
                    response_json = json.dumps(final_response)
                    print(f"🚀 SENDING FINAL CAREER RESPONSE: {len(response_json)} chars")
                    yield f"data: {response_json}\n\n"
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON PARSING FAILED: {e}")
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse AI response'})}\n\n"
                
            else:
                error_message = ai_result.get('error', 'AI analysis failed') if ai_result else 'No response from AI'
                yield f"data: {json.dumps({'status': 'error', 'error': error_message})}\n\n"
                
        except Exception as e:
            print(f"❌ CAREER ANALYSIS ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            full_traceback = traceback.format_exc()
            print(f"Full traceback:\\n{full_traceback}")
            
            error_message = str(e) if str(e) else 'Unknown error occurred'
            yield f"data: {json.dumps({'status': 'error', 'error': error_message, 'error_type': type(e).__name__})}\n\n"
    
    return StreamingResponse(
        generate_career_analysis(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
