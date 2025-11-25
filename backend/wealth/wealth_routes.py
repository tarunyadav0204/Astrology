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

def parse_gemini_astrology_response(raw_text):
    """
    Parses the raw text response from Gemini into a structured dictionary
    suitable for UI rendering.
    """
    import re
    import html
    
    # Debug: Print the complete response format
    print("\n" + "="*100)
    print("COMPLETE GEMINI RESPONSE - FULL TEXT:")
    print("="*100)
    print(raw_text)
    print("="*100)
    print(f"Total length: {len(raw_text)} characters")
    print("="*100 + "\n")
    
    parsed_data = {
        "quick_answer": None,
        "key_insights": [],
        "detailed_analysis": [],
        "final_thoughts": None,
        "follow_up_questions": []
    }

    # Extract Quick Answer from div structure
    quick_answer_match = re.search(r'&lt;div class=&quot;quick-answer-card&quot;&gt;(.*?)&lt;/div&gt;', raw_text, re.DOTALL)
    if quick_answer_match:
        quick_content = quick_answer_match.group(1)
        # Decode HTML entities
        quick_content = html.unescape(quick_content)
        # Convert ** to <strong> tags
        quick_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', quick_content)
        parsed_data["quick_answer"] = quick_content.strip()
        print(f"✅ EXTRACTED QUICK ANSWER: {parsed_data['quick_answer'][:100]}...")
        
        # Also add to detailed_analysis for frontend display
        parsed_data["detailed_analysis"].append({
            "title": "Wealth Analysis Summary",
            "content": quick_content.strip()
        })
    
    # If no quick answer found, add fallback content
    if not parsed_data["quick_answer"]:
        parsed_data["quick_answer"] = "Analysis in progress..."
        parsed_data["detailed_analysis"].append({
            "title": "Complete Analysis",
            "content": raw_text[:1000] + "..." if len(raw_text) > 1000 else raw_text
        })

    return parsed_data

def _parse_ai_response(response_text):
    """Parse JSON response from Gemini"""
    
    # Log the response for debugging
    print("\n" + "="*100)
    print("GEMINI JSON RESPONSE:")
    print("="*100)
    print(response_text)
    print("="*100 + "\n")
    
    import re
    import html
    
    # Extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
        # Decode HTML entities
        json_text = html.unescape(json_text)
        print(f"✅ Extracted and decoded JSON: {json_text[:100]}...")
    else:
        json_text = response_text
    
    try:
        json_response = json.loads(json_text)
        print(f"✅ Successfully parsed JSON response")
        
        return {
            "summary": "Comprehensive wealth analysis based on Vedic astrology principles.",
            "json_response": json_response,
            "wealth_analysis": {
                "json_response": json_response,
                "summary": "Comprehensive wealth analysis based on Vedic astrology principles."
            }
        }
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return {
            "summary": "Comprehensive wealth analysis based on Vedic astrology principles.",
            "raw_response": response_text,
            "wealth_analysis": {
                "raw_response": response_text,
                "summary": "Comprehensive wealth analysis based on Vedic astrology principles."
            }
        }



@router.post("/overall-assessment")
async def get_overall_wealth_assessment(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Complete wealth assessment with technical analysis"""
    try:
        # Prepare birth data
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.birth_date,
            time=request.birth_time,
            place=request.birth_place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+5:30'
        )
        
        # Calculate chart
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_data)
        
        # Calculate wealth analysis
        wealth_calculator = WealthCalculator(chart_data, birth_data)
        wealth_data = wealth_calculator.calculate_overall_wealth()
        
        return {"success": True, "data": wealth_data}
        
    except Exception as e:
        print(f"❌ Wealth assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def generate_streaming_response():
        import json
        
        try:
            print(f"🔄 Starting wealth analysis for user {current_user.userid}")
            
            # Import chat components (no modifications to chat system)
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            try:
                from chat.chat_context_builder import ChatContextBuilder
                print(f"✅ ChatContextBuilder imported successfully")
            except Exception as e:
                print(f"❌ Failed to import ChatContextBuilder: {e}")
                raise
                
            try:
                from ai.gemini_chat_analyzer import GeminiChatAnalyzer
                print(f"✅ GeminiChatAnalyzer imported successfully")
            except Exception as e:
                print(f"❌ Failed to import GeminiChatAnalyzer: {e}")
                raise
            
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
            try:
                print(f"🏗️ STARTING CONTEXT BUILD for: {birth_data['date']} {birth_data['time']}")
                print(f"   Birth data keys: {list(birth_data.keys())}")
                
                context_builder = ChatContextBuilder()
                print(f"🏗️ ChatContextBuilder instance created")
                
                print(f"🏗️ Calling build_complete_context in executor...")
                full_context = await asyncio.get_event_loop().run_in_executor(
                    None, context_builder.build_complete_context, birth_data
                )
                print(f"✅ CONTEXT BUILD COMPLETED")
                print(f"   Context type: {type(full_context)}")
                print(f"   Context length: {len(str(full_context))} chars")
                
            except Exception as e:
                print(f"❌ CONTEXT BUILD FAILED: {type(e).__name__}: {e}")
                import traceback
                full_traceback = traceback.format_exc()
                print(f"Context build traceback:\n{full_traceback}")
                raise
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating AI insights with enhanced context...'})}\n\n"
            
            # Create comprehensive wealth question with strict JSON format requirement
            wealth_question = """
As an expert Vedic astrologer, provide a comprehensive wealth analysis using the complete astrological context provided.

SPECIAL FOCUS ON WEALTH INDICATORS:
- InduLagna (Wealth Ascendant): Analyze the InduLagna position, sign, house placement, and aspects for wealth potential
- 2nd House (Wealth): Primary wealth house analysis with lord placement and aspects
- 11th House (Gains): Income and gains analysis with planetary influences
- 9th House (Fortune): Luck and fortune factors affecting wealth accumulation
- Jupiter (Karaka for Wealth): Natural significator analysis for financial wisdom
- Venus (Luxury): Material comforts and luxury potential
- Dhana Yogas: Classical wealth combinations from BPHS and other texts
- Dasha Periods: Current and upcoming periods affecting financial growth

MANDATORY INDU LAGNA ANALYSIS:
In the Wealth Analysis section, specifically analyze the Indu Lagna provided in the special_lagnas data.
Assess the financial magnitude based on the planets occupying or aspecting the Indu Lagna sign.
Cross-reference this with the 2nd and 11th house strength to determine if the wealth is 'Stable' (2nd/11th) or 'Sudden/Speculative' (Indu Lagna).
Mention the Indu Lagna explicitly in your final verdict on financial volume.

CRITICAL REQUIREMENT: You MUST respond ONLY with valid JSON. No other text, no explanations, no markdown. Just pure JSON.

STRICT MANDATORY FORMAT - Validate your JSON before responding:

{
  "quick_answer": "Brief summary with <strong>bold text</strong> and <br> for line breaks",
  "detailed_analysis": [
    {
      "question": "What is my overall wealth potential according to my birth chart?",
      "answer": "Detailed answer with <strong>bold</strong>, <br> for line breaks, and <p> for paragraphs"
    },
    {
      "question": "Will I be wealthy or face financial struggles in life?", 
      "answer": "Detailed answer with HTML markup"
    },
    {
      "question": "Should I do business or job for better financial success?",
      "answer": "Detailed answer with HTML markup"
    },
    {
      "question": "What are my best sources of income and earning methods?",
      "answer": "Detailed answer with HTML markup"
    },
    {
      "question": "Can I do stock trading and speculation successfully?",
      "answer": "Detailed answer with HTML markup"
    },
    {
      "question": "When will I see significant financial growth in my life?",
      "answer": "Detailed answer with HTML markup"
    },
    {
      "question": "At what age will I achieve financial stability?",
      "answer": "Detailed answer with HTML markup"
    },
    {
      "question": "What types of investments and financial strategies suit me best?",
      "answer": "Detailed answer with HTML markup"
    },
    {
      "question": "Should I invest in property, stocks, or other assets?",
      "answer": "Detailed answer with HTML markup"
    }
  ],
  "final_thoughts": "Summary with <strong>bold</strong> and <br> line breaks",
  "follow_up_questions": [
    "📅 When will this happen?",
    "🔮 What remedies can help?",
    "💼 How to maximize success?",
    "🌟 What should I focus on?"
  ]
}

MANDATORY RULES:
1. Response must start with { and end with }
2. All strings must be properly escaped
3. No markdown code blocks (```)
4. No additional text outside JSON
5. Validate JSON syntax before responding

HTML markup for content formatting:
- <strong>text</strong> for bold
- <br> for line breaks  
- <p>text</p> for paragraphs
- <em>text</em> for emphasis

Provide detailed astrological analysis using the birth chart data and planetary periods.
"""
            
            # Use chat analyzer (async)
            try:
                print(f"🤖 Initializing Gemini analyzer...")
                gemini_analyzer = GeminiChatAnalyzer()
                print(f"✅ Gemini analyzer initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini analyzer: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Prepare context as dictionary for GeminiChatAnalyzer
            if isinstance(full_context, str):
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
                context_dict = full_context if full_context else {
                    'astrological_data': 'No astrological context available',
                    'birth_details': {
                        'name': birth_data['name'],
                        'date': birth_data['date'],
                        'time': birth_data['time'],
                        'place': birth_data['place']
                    }
                }
            
            # Retry logic for API timeouts
            max_retries = 3
            retry_delay = 10  # seconds
            ai_result = None
            
            for attempt in range(max_retries):
                try:
                    print(f"🔄 Attempt {attempt + 1}/{max_retries} - Calling Gemini API...")
                    ai_result = await gemini_analyzer.generate_chat_response(
                        wealth_question, context_dict, [], 'english', 'detailed'
                    )
                    print(f"📝 GEMINI API RESPONSE RECEIVED:")
                    print(f"   Success: {ai_result.get('success') if ai_result else 'None'}")
                    
                    if ai_result and ai_result.get('success'):
                        # HTML decode the response to fix encoded characters
                        import html
                        raw_response = ai_result.get('response', '')
                        decoded_response = html.unescape(raw_response)
                        ai_result['response'] = decoded_response
                        print(f"   Response decoded from HTML entities")
                    
                    break  # Success, exit retry loop
                    
                except Exception as api_error:
                    error_msg = str(api_error)
                    print(f"⚠️ API attempt {attempt + 1} failed: {error_msg}")
                    
                    # Check if it's a timeout/deadline error
                    if ("timeout" in error_msg.lower() or 
                        "deadline" in error_msg.lower() or 
                        "504" in error_msg or
                        "DeadlineExceeded" in error_msg):
                        
                        if attempt < max_retries - 1:  # Not the last attempt
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            print(f"⏳ Timeout detected, retrying in {wait_time} seconds...")
                            yield f"data: {json.dumps({'status': 'processing', 'message': f'API timeout, retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})'})}\n\n"
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ All retry attempts exhausted for timeout")
                            ai_result = {'success': False, 'error': f'API timeout after {max_retries} attempts'}
                            break
                    else:
                        # Non-timeout error, don't retry
                        print(f"❌ Non-timeout error, not retrying: {error_msg}")
                        ai_result = {'success': False, 'error': error_msg}
                        break
            
            if ai_result and ai_result.get('success'):
                # Parse AI response
                try:
                    ai_response_text = ai_result.get('response', '')
                    print(f"📄 PARSING RESPONSE:")
                    print(f"   Length: {len(ai_response_text)} chars")
                    print(f"   First 200 chars: {ai_response_text[:200]}...")
                    
                    # Extract JSON from markdown code blocks first
                    import html
                    import re
                    
                    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                        print(f"✅ EXTRACTED JSON FROM MARKDOWN")
                    else:
                        # Try to find JSON object in raw text
                        json_match = re.search(r'({.*})', ai_response_text, re.DOTALL)
                        if json_match:
                            json_text = json_match.group(1)
                            print(f"✅ EXTRACTED JSON FROM RAW TEXT")
                        else:
                            json_text = ai_response_text
                            print(f"⚠️ NO JSON FOUND, using raw response")
                    
                    # Now decode HTML entities in the extracted JSON
                    decoded_json = json_text
                    
                    # Multiple rounds of HTML decoding
                    for _ in range(5):
                        new_decoded = html.unescape(decoded_json)
                        if new_decoded == decoded_json:
                            break
                        decoded_json = new_decoded
                    
                    # Manual replacements for stubborn entities (multiple passes)
                    for _ in range(3):
                        decoded_json = decoded_json.replace('&quot;', '"')
                        decoded_json = decoded_json.replace('&amp;', '&')
                        decoded_json = decoded_json.replace('&lt;', '<')
                        decoded_json = decoded_json.replace('&gt;', '>')
                        decoded_json = decoded_json.replace('&#39;', "'")
                        decoded_json = decoded_json.replace('&apos;', "'")
                    
                    # Additional cleanup for common JSON issues
                    decoded_json = decoded_json.replace('\\"', '"')  # Fix escaped quotes
                    decoded_json = decoded_json.replace('\\\\\\"', '"')  # Fix double-escaped quotes
                    
                    json_text = decoded_json
                    
                    # Debug: Print first 500 chars of cleaned JSON
                    print(f"🔍 CLEANED JSON (first 500 chars): {json_text[:500]}...")
                    
                    try:
                        parsed_response = json.loads(json_text)
                    except json.JSONDecodeError as json_error:
                        print(f"⚠️ JSON parsing failed, trying fallback parsing...")
                        # Fallback: Try to parse with more aggressive cleaning
                        fallback_json = json_text
                        # Remove any remaining HTML-like content in strings
                        fallback_json = re.sub(r'&[a-zA-Z0-9#]+;', '', fallback_json)
                        try:
                            parsed_response = json.loads(fallback_json)
                            print(f"✅ FALLBACK JSON PARSING SUCCEEDED")
                        except:
                            # Last resort: create a basic response structure
                            print(f"❌ All JSON parsing failed, creating fallback response")
                            parsed_response = {
                                "quick_answer": "Wealth analysis completed but response formatting failed. Please try again.",
                                "detailed_analysis": [],
                                "final_thoughts": "Please regenerate the analysis.",
                                "follow_up_questions": []
                            }
                    print(f"✅ JSON PARSED SUCCESSFULLY")
                    print(f"   Keys: {list(parsed_response.keys())}")
                    print(f"   Questions count: {len(parsed_response.get('detailed_analysis', []))}")
                    
                    # Deduct credits for successful analysis
                    success = credit_service.spend_credits(current_user.userid, wealth_cost, 'wealth_analysis', f"Wealth analysis for {request.birth_date}")
                    if success:
                        print(f"💳 Credits deducted successfully")
                    else:
                        print(f"❌ Credit deduction failed")
                    
                    # Store in cache
                    _store_ai_insights(birth_hash, parsed_response)
                    print(f"💾 Response cached successfully")
                    
                    # Send complete response in expected format
                    enhanced_insights = {
                        'wealth_analysis': {
                            'json_response': parsed_response,
                            'summary': 'Comprehensive wealth analysis based on Vedic astrology principles.'
                        },
                        'enhanced_context': True,
                        'questions_covered': len(parsed_response.get('detailed_analysis', [])),
                        'context_type': 'chat_context_builder',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    final_response = {'status': 'complete', 'data': enhanced_insights, 'cached': False}
                    response_json = json.dumps(final_response)
                    print(f"🚀 SENDING FINAL RESPONSE: {len(response_json)} chars")
                    yield f"data: {response_json}\n\n"
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON PARSING FAILED: {e}")
                    print(f"   Extracted JSON (first 1000 chars): {json_text[:1000] if 'json_text' in locals() else 'N/A'}...")
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse AI response'})}\n\n"
            else:
                error_response = {
                    'wealth_analysis': 'AI analysis failed. Please try again.',
                    'enhanced_context': False,
                    'error': ai_result.get('error', 'Unknown error') if ai_result else 'No response from AI'
                }
                yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\n\n"
                
        except Exception as e:
            print(f"❌ ENHANCED WEALTH ANALYSIS ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            full_traceback = traceback.format_exc()
            print(f"Full traceback:\n{full_traceback}")
            
            error_response = {
                'wealth_analysis': f'Analysis error: {str(e)}. Please try again.',
                'enhanced_context': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            yield f"data: {json.dumps({'status': 'error', 'error': str(e), 'error_type': type(e).__name__})}\n\n"
    
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
async def get_astrological_context(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Get complete astrological context for admin users"""
    try:
        # Check if user is admin
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import chat context builder
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from chat.chat_context_builder import ChatContextBuilder
        
        # Prepare birth data
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
        full_context = context_builder.build_complete_context(birth_data)
        
        return {
            "success": True,
            "context": full_context,
            "context_length": len(str(full_context))
        }
        
    except Exception as e:
        print(f"❌ Context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))