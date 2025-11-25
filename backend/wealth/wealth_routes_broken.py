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
                print(f"🏗️ Building context for birth data: {birth_data['date']} {birth_data['time']}")
                context_builder = ChatContextBuilder()
                full_context = await asyncio.get_event_loop().run_in_executor(
                    None, context_builder.build_complete_context, birth_data
                )
                print(f"✅ Context built successfully")
            except Exception as e:
                print(f"❌ Context building failed: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating AI insights with enhanced context...'})}\n\n"
            
            # Create comprehensive wealth question with strict JSON format requirement
            wealth_question = """
As an expert Vedic astrologer, provide a comprehensive wealth analysis using the complete astrological context provided.

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
                    
                    break
                except Exception as e:
                    print(f"❌ Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            
            if not ai_result or not ai_result.get('success'):
                error_msg = ai_result.get('error', 'Unknown error') if ai_result else 'No response from AI'
                print(f"❌ AI analysis failed: {error_msg}")
                yield f"data: {json.dumps({'status': 'error', 'message': f'AI analysis failed: {error_msg}'})}

"
                return
            
            print(f"✅ AI analysis completed successfully")
            
            # Parse the AI response
            try:
                ai_response_text = ai_result.get('response', '')
                print(f"📄 Raw AI response length: {len(ai_response_text)}")
                print(f"📄 First 500 chars: {ai_response_text[:500]}...")
                
                # Parse JSON response
                parsed_response = json.loads(ai_response_text)
                print(f"✅ JSON parsed successfully")
                print(f"📊 Response keys: {list(parsed_response.keys())}")
                
                # Validate required structure
                if not all(key in parsed_response for key in ['quick_answer', 'detailed_analysis', 'final_thoughts']):
                    print(f"❌ Missing required keys in response")
                    raise ValueError("Response missing required structure")
                
                if not isinstance(parsed_response.get('detailed_analysis'), list):
                    print(f"❌ detailed_analysis is not a list")
                    raise ValueError("detailed_analysis must be a list")
                
                if len(parsed_response.get('detailed_analysis', [])) != 9:
                    print(f"❌ Expected 9 questions, got {len(parsed_response.get('detailed_analysis', []))}")
                    # Don't fail, just log the issue
                
                print(f"✅ Response structure validated")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"📄 Problematic response: {ai_response_text[:1000]}...")
                yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse AI response'})}

"
                return
            except Exception as e:
                print(f"❌ Response validation failed: {e}")
                yield f"data: {json.dumps({'status': 'error', 'message': f'Response validation failed: {str(e)}'})}

"
                return
            
            # Deduct credits after successful analysis
            try:
                credit_service.deduct_credits(current_user.userid, wealth_cost, 'wealth_analysis')
                print(f"💳 Deducted {wealth_cost} credits from user {current_user.userid}")
            except Exception as e:
                print(f"❌ Credit deduction failed: {e}")
                # Continue anyway since analysis was successful
            
            # Store in cache
            try:
                _store_ai_insights(birth_hash, parsed_response)
                print(f"💾 Insights cached successfully")
            except Exception as e:
                print(f"❌ Failed to cache insights: {e}")
                # Continue anyway
            
            # Return final result
            yield f"data: {json.dumps({'status': 'complete', 'data': parsed_response, 'cached': False})}

"
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR in wealth analysis: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'status': 'error', 'message': f'Analysis failed: {str(e)}'})}

"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )