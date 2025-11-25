from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sys
import os
import hashlib
import json
import sqlite3
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService

# Add the parent directory to the path to import calculators
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.chart_calculator import ChartCalculator
from calculators.wealth_calculator import WealthCalculator
from ai.gemini_wealth_analyzer import GeminiWealthAnalyzer

class BirthDetailsRequest(BaseModel):
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM
    birth_place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    force_regenerate: Optional[bool] = False
    user_role: Optional[str] = None

router = APIRouter(prefix="/wealth", tags=["wealth"])
credit_service = CreditService()

def _create_birth_hash(birth_data):
    """Create unique hash for birth data"""
    birth_string = f"{birth_data.date}_{birth_data.time}_{birth_data.latitude}_{birth_data.longitude}"
    return hashlib.sha256(birth_string.encode()).hexdigest()

def _init_ai_insights_table():
    """Initialize AI insights table if not exists"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_wealth_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            birth_hash TEXT UNIQUE,
            insights_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def _get_stored_ai_insights(birth_hash):
    """Get stored AI insights from database"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('SELECT insights_data FROM ai_wealth_insights WHERE birth_hash = ?', (birth_hash,))
    result = cursor.fetchone()
    conn.close()
    return json.loads(result[0]) if result else None

def _store_ai_insights(birth_hash, insights_data):
    """Store AI insights in database"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO ai_wealth_insights (birth_hash, insights_data, updated_at)
        VALUES (?, ?, ?)
    ''', (birth_hash, json.dumps(insights_data), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def _clean_html_tags(text):
    """Remove HTML tags and decode HTML entities while preserving content structure"""
    import re
    import html
    
    if not text:
        return text
    
    # Decode HTML entities first
    text = html.unescape(text)
    
    # Remove HTML tags but preserve line breaks
    text = re.sub(r'<br[^>]*>', '\n', text)
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove JSON artifacts more carefully
    text = re.sub(r'"\s*,\s*"[^"]*"\s*:', '', text)  # Remove JSON field names
    text = re.sub(r'"\s*}\s*,\s*{\s*"', ' ', text)  # Remove JSON separators
    
    # Remove JSON structure but preserve content
    text = re.sub(r'^[{\["\s]*', '', text)  # Remove leading JSON chars
    text = re.sub(r'[}\]"\s]*$', '', text)  # Remove trailing JSON chars
    text = re.sub(r'[{}\[\]]+', ' ', text)  # Remove remaining brackets
    
    # Clean up quotes more selectively
    text = re.sub(r'"([^"]{0,10})":', r'\1:', text)  # Remove quotes around short keys
    text = re.sub(r'""', '', text)  # Remove empty quotes
    
    # Preserve paragraph structure
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)  # Clean horizontal whitespace
    text = text.strip()
    
    return text

def _format_ai_response(raw_response):
    """Format AI response into structured Q&A format"""
    try:
        # Clean HTML tags first
        cleaned_response = _clean_html_tags(raw_response)
        
        # Try to parse as JSON first
        if cleaned_response.strip().startswith('{'):
            return json.loads(cleaned_response)
        
        # If not JSON, parse the text response
        return _parse_text_response(cleaned_response)
    except:
        # Fallback to text parsing
        return _parse_text_response(_clean_html_tags(raw_response))

def _parse_text_response(text):
    """Parse unstructured text into Q&A format"""
    import re
    
    # Clean HTML first
    text = _clean_html_tags(text)
    
    questions = [
        "What is my overall wealth potential according to my birth chart?",
        "Will I be wealthy or face financial struggles in life?", 
        "Should I do business or job for better financial success?",
        "What are my best sources of income and earning methods?",
        "Can I do stock trading and speculation successfully?",
        "When will I see significant financial growth in my life?",
        "At what age will I achieve financial stability?",
        "What types of investments and financial strategies suit me best?",
        "Should I invest in property, stocks, or other assets?"
    ]
    
    # Extract summary from Quick Answer
    summary = ""
    if "Quick Answer" in text:
        start = text.find("Quick Answer")
        # Look for the end of the summary - either double newline or start of first question
        end_markers = ["\n\n", "**1.", "1.", "### 1."]
        end = len(text)  # Default to end of text
        
        for marker in end_markers:
            marker_pos = text.find(marker, start + 50)  # Skip immediate area after "Quick Answer"
            if marker_pos != -1 and marker_pos < end:
                end = marker_pos
        
        summary = text[start:end].replace("**Quick Answer**:", "").replace("Quick Answer:", "").strip()
        # Remove any leading asterisks or colons
        summary = summary.lstrip("*: ")
    
    formatted_questions = []
    
    # Split text by numbered questions (1., 2., etc.) - try multiple patterns
    sections = []
    patterns = [r'\*\*\d+\.', r'\d+\.\s*\*\*', r'###\s*\d+\.', r'^\d+\.', r'\n\d+\.']
    
    for pattern in patterns:
        test_sections = re.split(pattern, text, flags=re.MULTILINE)
        if len(test_sections) > len(sections):
            sections = test_sections
    
    # If no numbered sections found, try to extract from the full text
    if len(sections) <= 1:
        # Look for question patterns and extract content after each
        for i, question in enumerate(questions):
            # Find the question in text (case insensitive)
            question_pattern = re.escape(question.lower())
            match = re.search(question_pattern, text.lower())
            if match:
                start_pos = match.end()
                # Find next question or end of text
                next_question_pos = len(text)
                for j, next_q in enumerate(questions[i+1:], i+1):
                    next_match = re.search(re.escape(next_q.lower()), text.lower()[start_pos:])
                    if next_match:
                        next_question_pos = start_pos + next_match.start()
                        break
                
                section_text = text[start_pos:next_question_pos].strip()
                if section_text and len(section_text) > 50:
                    # Clean and format the section
                    paragraphs = [p.strip() for p in section_text.split('\n') if p.strip()]
                    answer = ' '.join(paragraphs[:3])  # Take first few paragraphs
                    
                    formatted_questions.append({
                        "question": questions[i],
                        "answer": answer,
                        "key_points": _extract_key_points(section_text),
                        "astrological_basis": _extract_astrological_basis(section_text)
                    })
    else:
        # Process numbered sections
        for i, section in enumerate(sections[1:]):
            if i < len(questions):
                # Clean the section
                section = section.strip()
                
                # Remove question text from section start
                question_text = questions[i]
                if section.lower().startswith(question_text.lower()):
                    section = section[len(question_text):].strip()
                
                # Extract answer - take more content to avoid truncation
                paragraphs = [p.strip() for p in section.split('\n\n') if p.strip()]
                
                answer = ""
                # Combine multiple paragraphs for a complete answer
                valid_paragraphs = []
                for para in paragraphs:
                    if (len(para) > 20 and 
                        not para.startswith("Key") and 
                        not para.startswith("Astrological") and
                        not any(q.lower() in para.lower() for q in questions)):
                        valid_paragraphs.append(para)
                        if len(valid_paragraphs) >= 2:  # Take up to 2 paragraphs
                            break
                
                answer = ' '.join(valid_paragraphs) if valid_paragraphs else section[:500]
                
                # Extract key points and astrological basis from the section
                full_section = ' '.join(paragraphs)
                key_points = _extract_key_points(full_section)
                astrological_basis = _extract_astrological_basis(full_section)
                
                if answer:
                    formatted_questions.append({
                        "question": questions[i],
                        "answer": answer,
                        "key_points": key_points,
                        "astrological_basis": astrological_basis
                    })
    
    # Fallback: if no numbered sections found, try to extract from content
    if not formatted_questions:
        # Look for question patterns in text
        for i, question in enumerate(questions):
            # Find content related to each question
            question_keywords = {
                0: ["wealth potential", "overall wealth"],
                1: ["wealthy", "financial struggles", "prosperity"],
                2: ["business", "job", "employment"],
                3: ["income sources", "earning methods"],
                4: ["stock trading", "speculation"],
                5: ["financial growth", "growth timing"],
                6: ["financial stability", "stability age"],
                7: ["investment strategies", "financial strategies"],
                8: ["property", "assets", "investment types"]
            }
            
            if i in question_keywords:
                # Find relevant paragraphs
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                best_match = ""
                
                for para in paragraphs:
                    if any(keyword.lower() in para.lower() for keyword in question_keywords[i]):
                        if len(para) > best_match:
                            best_match = para
                
                if best_match:
                    formatted_questions.append({
                        "question": question,
                        "answer": best_match,
                        "key_points": _extract_key_points(best_match),
                        "astrological_basis": _extract_astrological_basis(best_match)
                    })
    
    return {
        "summary": summary or "Comprehensive wealth analysis based on Vedic astrology principles.",
        "questions": formatted_questions
    }

def _extract_key_points(text):
    """Extract key points from text"""
    import re
    text = _clean_html_tags(text)
    
    # Remove JSON artifacts and question text
    text = re.sub(r'key_points.*?:', '', text)
    text = re.sub(r'astrological_basis.*', '', text)
    
    # Remove question patterns
    questions_to_remove = [
        "What is my overall wealth potential",
        "Will I be wealthy or face", 
        "Should I do business or job",
        "What are my best sources",
        "Can I do stock trading",
        "When will I see significant",
        "At what age will I achieve",
        "What types of investments",
        "Should I invest in property"
    ]
    
    for q in questions_to_remove:
        text = re.sub(rf'{re.escape(q)}[^.]*\?', '', text, flags=re.IGNORECASE)
    
    points = []
    sentences = text.split('.')
    for sentence in sentences[:3]:
        sentence = sentence.strip()
        if (sentence and len(sentence) > 20 and 
            not any(x in sentence.lower() for x in ['question', 'answer', 'key_points', 'according to my birth chart'])):
            points.append(sentence)
    return points

def _extract_astrological_basis(text):
    """Extract astrological reasoning from text"""
    import re
    text = _clean_html_tags(text)
    
    # Remove JSON field names and question text
    text = re.sub(r'astrological_basis.*?:', '', text)
    
    # Remove question patterns
    questions_to_remove = [
        "What is my overall wealth potential",
        "Will I be wealthy or face", 
        "Should I do business or job",
        "What are my best sources",
        "Can I do stock trading",
        "When will I see significant",
        "At what age will I achieve",
        "What types of investments",
        "Should I invest in property"
    ]
    
    for q in questions_to_remove:
        text = re.sub(rf'{re.escape(q)}[^.]*\?', '', text, flags=re.IGNORECASE)
    
    # Look for planetary mentions, house references, etc.
    astrological_terms = ['Jupiter', 'Saturn', 'Mars', 'Venus', 'Mercury', 'Sun', 'Moon', 'house', 'lord', 'yoga', 'dasha', 'BPHS', 'Brihat', 'Parashara', 'Lagna', 'exalted']
    basis_parts = []
    
    sentences = text.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if (sentence and any(term in sentence for term in astrological_terms) and 
            len(sentence) > 25 and
            not any(q.lower() in sentence.lower() for q in questions_to_remove)):
            # Clean up the sentence
            sentence = re.sub(r'^[^A-Za-z]*', '', sentence)  # Remove leading non-letters
            if sentence and not sentence.lower().startswith('according to my birth chart'):
                basis_parts.append(sentence)
            if len(basis_parts) >= 2:
                break
    
    return '. '.join(basis_parts) if basis_parts else "Based on planetary positions and house analysis."

@router.post("/overall-assessment")
async def get_overall_wealth_assessment(request: BirthDetailsRequest):
    """Get complete wealth assessment without AI insights"""
    try:
        # Create birth data object
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.birth_date,
            time=request.birth_time,
            place=request.birth_place,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone
        )
        
        # Calculate birth chart
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Calculate wealth analysis
        wealth_calc = WealthCalculator(chart_data, birth_data)
        wealth_analysis = wealth_calc.calculate_overall_wealth()
        
        return {
            "status": "success",
            "data": wealth_analysis
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Wealth calculation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Wealth calculation error: {str(e)}\n{error_details}")

from fastapi.responses import StreamingResponse
import asyncio

@router.post("/ai-insights-enhanced")
async def get_enhanced_wealth_insights(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Enhanced wealth insights using chat context builder with 9 key questions - requires credits"""
    
    # Check credit cost and user balance
    wealth_cost = credit_service.get_credit_setting('wealth_analysis_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    print(f"💳 WEALTH CREDIT CHECK:")
    print(f"   User ID: {current_user.userid}")
    print(f"   Wealth cost: {wealth_cost} credits")
    print(f"   User balance: {user_balance} credits")
    
    if user_balance < wealth_cost:
        print(f"❌ INSUFFICIENT CREDITS: Need {wealth_cost}, have {user_balance}")
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {wealth_cost} credits but have {user_balance}."
        )
    
    print(f"Enhanced wealth insights request received: {request.birth_date} {request.birth_time}")
    
    async def generate_streaming_response():
        import json
        
        try:
            # Import chat components (no modifications to chat system)
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from chat.chat_context_builder import ChatContextBuilder
            from ai.gemini_chat_analyzer import GeminiChatAnalyzer
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Initializing enhanced wealth analysis...'})}\n\n"
            
            # Prepare birth data in chat format
            birth_data = {
                'name': request.birth_place,
                'date': request.birth_date,
                'time': request.birth_time,
                'place': request.birth_place,
                'latitude': request.latitude or 28.6139,
                'longitude': request.longitude or 77.2090,
                'timezone': request.timezone or 'UTC+5:30'
            }
            
            # Create birth data object
            from types import SimpleNamespace
            birth_obj = SimpleNamespace(**birth_data)
            birth_hash = _create_birth_hash(birth_obj)
            
            # Initialize database table
            _init_ai_insights_table()
            
            # Check cache
            force_regen = request.force_regenerate
            if force_regen is not True:
                stored_insights = _get_stored_ai_insights(birth_hash)
                if stored_insights and stored_insights.get('enhanced_context'):
                    yield f"data: {json.dumps({'status': 'complete', 'data': stored_insights, 'cached': True})}\n\n"
                    return
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Building comprehensive astrological context...'})}\n\n"
            
            # Use chat context builder (async)
            context_builder = ChatContextBuilder()
            full_context = await asyncio.get_event_loop().run_in_executor(
                None, context_builder.build_complete_context, birth_data
            )
            
            # Debug context
            print(f"=== CONTEXT DEBUG ===")
            print(f"Context type: {type(full_context)}")
            if isinstance(full_context, str):
                print(f"Context length: {len(full_context)} chars")
                print(f"Context preview: {full_context[:300]}...")
                print(f"Contains 'Jupiter'? {('Jupiter' in full_context)}")
                print(f"Contains 'dasha'? {('dasha' in full_context)}")
                print(f"Contains 'house'? {('house' in full_context)}")
            else:
                print(f"Context value: {full_context}")
                # Convert to string if needed
                full_context = str(full_context) if full_context else "No context available"
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating AI insights with enhanced context...'})}\n\n"
            
            # Create comprehensive wealth question with formatting instructions
            wealth_question = """
As an expert Vedic astrologer, provide a comprehensive wealth analysis using the complete astrological context provided. Answer each question separately with detailed analysis.

IMPORTANT INSTRUCTIONS:
- Use ALL the astrological data provided including birth chart, divisional charts (D1, D9, D10, D12), current dashas, nakshatras, yogas, and planetary strengths
- Apply BOTH Parashari and Jaimini astrology principles for comprehensive analysis
- Analyze Chara Karakas (Atmakaraka, Amatyakaraka, Bhratrukaraka, Matrukaraka, Putrakaraka, Gnatikaraka, Darakaraka) and their significance for wealth
- Use Jaimini aspects, Argala (planetary influences), and Arudha Padas for deeper insights
- Answer each question individually with unique, specific content
- Include references to classical texts (BPHS, Phaladeepika, Jaimini Sutras, Hora Sara, etc.)
- Analyze current dasha periods (both Vimshottari and Chara Dasha) and their impact on wealth
- Consider planetary aspects, conjunctions, and house lordships from both systems
- Examine divisional charts for career (D10) and wealth indicators
- Include nakshatra analysis for relevant planets and Chara Karakas

Questions to answer with detailed astrological analysis:

**1. What is my overall wealth potential according to my birth chart?**
Analyze: 2nd house (accumulated wealth), 11th house (gains), Jupiter (natural significator), Venus (luxury), Dhana yogas, Lagna lord strength, and overall chart promise.

**2. Will I be wealthy or face financial struggles in life?**
Examine: Malefic influences on wealth houses, 6th/8th/12th house connections, debilitated planets affecting wealth, dasha periods, and long-term financial trajectory.

**3. Should I do business or job for better financial success?**
Compare: 10th house (career) vs 7th house (partnerships/business), relevant divisional charts (D10), planetary strengths for entrepreneurship vs employment, dasha support.

**4. What are my best sources of income and earning methods?**
Analyze: 10th lord placement, planets in 10th house, Atmakaraka (soul's desire), Amatyakaraka (career significator), strongest planets, relevant nakshatras, Arudha Lagna, and specific career indicators from D10 chart using both Parashari and Jaimini methods.

**5. Can I do stock trading and speculation successfully?**
Examine: 5th house (speculation), 8th house (sudden gains/losses), Mercury (trading), Mars (risk-taking), relevant yogas, and current dasha support for speculation.

**6. When will I see significant financial growth in my life?**
Analyze: Current Mahadasha and Antardasha periods, upcoming beneficial periods, Jupiter transits, Saturn returns, and specific timing using dasha analysis.

**7. At what age will I achieve financial stability?**
Calculate: Based on current age, dasha progression, planetary maturity periods, and when beneficial combinations will manifest fully.

**8. What types of investments and financial strategies suit me best?**
Recommend: Based on planetary strengths, risk tolerance from chart, long-term vs short-term indicators, and suitable investment vehicles per astrological indications.

**9. Should I invest in property, stocks, or other assets?**
Compare: 4th house (property), 5th house (speculation), 8th house (investments), Mars (real estate), Mercury (trading), and current planetary periods.

For each answer, provide:
- Specific planetary positions and degrees
- House lordships and their significance from both Parashari and Jaimini perspectives
- Chara Karaka analysis (especially Atmakaraka, Amatyakaraka for wealth and career)
- Jaimini aspects and Argala influences on wealth houses
- Arudha Pada analysis for material prosperity
- Relevant yogas and combinations from both systems
- Divisional chart analysis where applicable
- Current dasha impact (Vimshottari and Chara Dasha)
- Classical text references (BPHS, Jaimini Sutras, etc.)
- Practical recommendations based on integrated analysis

Use the comprehensive birth chart data, current planetary periods, and all astrological context provided to give detailed, accurate predictions.
"""
            
            # Use chat analyzer (async) - no modifications to chat system
            gemini_analyzer = GeminiChatAnalyzer()
            
            # Debug the question being sent
            print(f"=== QUESTION DEBUG ===")
            print(f"Question length: {len(wealth_question)} chars")
            print(f"Question preview: {wealth_question[:200]}...")
            
            # Prepare context as dictionary for GeminiChatAnalyzer
            if isinstance(full_context, str):
                # If context is string, wrap it in a dictionary
                context_dict = {
                    'astrological_data': full_context,
                    'birth_details': {
                        'name': birth_data['name'],
                        'date': birth_data['date'],
                        'time': birth_data['time'],
                        'place': birth_data['place']
                    }
                }
            else:
                # If context is already a dictionary, use it directly
                context_dict = full_context if full_context else {
                    'astrological_data': 'No astrological context available',
                    'birth_details': {
                        'name': birth_data['name'],
                        'date': birth_data['date'],
                        'time': birth_data['time'],
                        'place': birth_data['place']
                    }
                }
            
            ai_result = await gemini_analyzer.generate_chat_response(
                wealth_question, context_dict, [], 'english', 'detailed'
            )
            
            if ai_result['success']:
                # Debug logging
                print(f"=== RECEIVED FROM AI (ASYNC) ===")
                print(f"Original length: {len(ai_result['response'])} chars")
                cleaned_preview = _clean_html_tags(ai_result['response'])
                print(f"Cleaned length: {len(cleaned_preview)} chars")
                print(f"Response preview: {ai_result['response'][:200]}...")
                print(f"Response ends with: {repr(ai_result['response'][-100:])}")
                
                # Parse and format AI response
                formatted_response = _format_ai_response(ai_result['response'])
                print(f"Formatted response type: {type(formatted_response)}")
                print(f"Questions found: {len(formatted_response.get('questions', [])) if isinstance(formatted_response, dict) else 0}")
                
                # Debug the cleaned text
                cleaned_text = _clean_html_tags(ai_result['response'])
                print(f"Cleaned text preview: {cleaned_text[:500]}...")
                print(f"Contains '**1.'? {('**1.' in cleaned_text)}")
                print(f"Contains '1.'? {('1.' in cleaned_text)}")
                print(f"Contains '### 1.'? {('### 1.' in cleaned_text)}")
                
                # Show first few questions if found
                if isinstance(formatted_response, dict) and formatted_response.get('questions'):
                    for i, q in enumerate(formatted_response['questions'][:2]):
                        print(f"Q{i+1}: {q['question'][:50]}... -> {q['answer'][:100]}...")
                
                # Deduct credits for successful analysis
                print(f"💰 DEDUCTING CREDITS: {wealth_cost} credits for user {current_user.userid}")
                success = credit_service.spend_credits(
                    current_user.userid, 
                    wealth_cost, 
                    'wealth_analysis', 
                    f"Wealth analysis for {request.birth_date}"
                )
                
                if not success:
                    print(f"❌ CREDIT DEDUCTION FAILED for user {current_user.userid}")
                    error_response = {
                        'wealth_analysis': 'Credit deduction failed. Please try again.',
                        'enhanced_context': False,
                        'error': 'Credit deduction failed'
                    }
                    yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\n\n"
                else:
                    print(f"✅ CREDITS DEDUCTED SUCCESSFULLY")
                    new_balance = credit_service.get_user_credits(current_user.userid)
                    print(f"   New balance: {new_balance} credits")
                    
                    # Store in wealth database with enhanced flag
                    enhanced_insights = {
                        'wealth_analysis': formatted_response,
                        'enhanced_context': True,
                        'questions_covered': len(formatted_response.get('questions', [])) if isinstance(formatted_response, dict) else 0,
                        'context_type': 'chat_context_builder',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    await asyncio.get_event_loop().run_in_executor(
                        None, _store_ai_insights, birth_hash, enhanced_insights
                    )
                    
                    yield f"data: {json.dumps({'status': 'complete', 'data': enhanced_insights, 'cached': False})}\n\n"
            else:
                error_response = {
                    'wealth_analysis': 'AI analysis failed. Please try again.',
                    'enhanced_context': False,
                    'error': ai_result.get('error', 'Unknown error')
                }
                yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\n\n"
                
        except Exception as e:
            print(f"Enhanced wealth analysis error: {e}")
            import traceback
            traceback.print_exc()
            
            error_response = {
                'wealth_analysis': f'Analysis error: {str(e)}. Please try again.',
                'enhanced_context': False,
                'error': str(e)
            }
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

@router.post("/astrological-context")
async def get_astrological_context(request: BirthDetailsRequest):
    """Get the complete astrological context that's sent to AI - Admin only"""
    # Check admin access
    if request.user_role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        # Import chat components
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from chat.chat_context_builder import ChatContextBuilder
        
        # Prepare birth data in chat format
        birth_data = {
            'name': request.birth_place,
            'date': request.birth_date,
            'time': request.birth_time,
            'place': request.birth_place,
            'latitude': request.latitude or 28.6139,
            'longitude': request.longitude or 77.2090,
            'timezone': request.timezone or 'UTC+5:30'
        }
        
        # Build complete context
        context_builder = ChatContextBuilder()
        full_context = await asyncio.get_event_loop().run_in_executor(
            None, context_builder.build_complete_context, birth_data
        )
        
        return {
            "status": "success",
            "context": full_context,
            "birth_details": birth_data,
            "context_length": len(str(full_context))
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Context fetch error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Context fetch error: {str(e)}")

@router.post("/ai-insights")
async def get_ai_wealth_insights(request: BirthDetailsRequest):
    """Get AI-powered wealth insights with streaming keep-alive"""
    print(f"AI wealth insights request received: {request.birth_date} {request.birth_time}")
    print(f"Debug - Full request: {request}")
    print(f"Debug - Request force_regenerate: {request.force_regenerate}")
    print(f"Debug - Request dict: {request.__dict__}")
    
    async def generate_streaming_response():
        import json
        
        try:
            # Send initial status
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Initializing wealth analysis...'})}\n\n"
            
            # Create birth data object
            from types import SimpleNamespace
            birth_data = SimpleNamespace(
                date=request.birth_date,
                time=request.birth_time,
                place=request.birth_place,
                latitude=request.latitude,
                longitude=request.longitude,
                timezone=request.timezone
            )
            
            # Create unique hash for this birth data
            birth_hash = _create_birth_hash(birth_data)
            
            # Initialize database table
            _init_ai_insights_table()
            
            # Check if we have stored insights (unless force regenerate)
            force_regen = request.force_regenerate
            print(f"Debug - Force regenerate: {force_regen}")
            print(f"Debug - Force regenerate type: {type(force_regen)}")
            if force_regen is not True:
                stored_insights = _get_stored_ai_insights(birth_hash)
                print(f"Debug - Found cached insights: {bool(stored_insights)}")
                if stored_insights:
                    print(f"Debug - Returning cached data")
                    yield f"data: {json.dumps({'status': 'complete', 'data': stored_insights, 'cached': True})}\n\n"
                    return
            else:
                print(f"Debug - Skipping cache due to force regenerate")
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Calculating birth chart...'})}\n\n"
            
            # Calculate birth chart and wealth analysis
            chart_calc = ChartCalculator({})
            chart_data = chart_calc.calculate_chart(birth_data)
            
            wealth_calc = WealthCalculator(chart_data, birth_data)
            wealth_analysis = wealth_calc.calculate_overall_wealth()
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating AI insights...'})}\n\n"
            
            # Generate AI insights
            try:
                print("Initializing Gemini wealth analyzer...")
                gemini_analyzer = GeminiWealthAnalyzer()
                print("Gemini wealth analyzer initialized successfully")
                
                # Run AI generation with periodic updates
                import threading
                import time
                result = {}
                exception = {}
                
                def ai_worker():
                    try:
                        print("Starting Gemini AI wealth generation...")
                        # Pass birth data to Gemini analyzer
                        wealth_analysis_with_birth = wealth_analysis.copy()
                        wealth_analysis_with_birth.update({
                            'name': birth_data.place,
                            'date': birth_data.date,
                            'time': birth_data.time,
                            'latitude': birth_data.latitude,
                            'longitude': birth_data.longitude,
                            'timezone': birth_data.timezone
                        })
                        
                        # Generate AI insights
                        result['data'] = gemini_analyzer.generate_wealth_insights(wealth_analysis_with_birth, chart_data)
                        print("AI wealth generation completed")
                    except Exception as e:
                        print(f"AI worker error: {e}")
                        exception['error'] = e
                
                thread = threading.Thread(target=ai_worker)
                thread.start()
                
                # Send keep-alive messages with timeout
                count = 0
                max_iterations = 24  # 2 minutes
                
                while thread.is_alive() and count < max_iterations:
                    yield f"data: {json.dumps({'status': 'processing', 'message': 'AI wealth analysis in progress...'})}\n\n"
                    await asyncio.sleep(5)
                    count += 1
                
                if thread.is_alive():
                    yield f"data: {json.dumps({'status': 'error', 'error': 'AI analysis timed out'})}\n\n"
                    return
                
                thread.join(timeout=1)
                
                if 'error' in exception:
                    raise exception['error']
                
                ai_insights = result['data']
                
                # Store insights in database
                _store_ai_insights(birth_hash, ai_insights)
                
                # Send final result
                yield f"data: {json.dumps({'status': 'complete', 'data': ai_insights, 'cached': False})}\n\n"
                
            except Exception as e:
                error_response = {
                    'success': False,
                    'insights': {
                        'wealth_overview': '',
                        'income_analysis': '',
                        'investment_guidance': [],
                        'business_prospects': [],
                        'financial_challenges': [],
                        'prosperity_indicators': '',
                        'wealth_timeline': [],
                        'career_money': []
                    },
                    'error': str(e)
                }
                yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )