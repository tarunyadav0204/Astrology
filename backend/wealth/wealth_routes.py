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
    language: Optional[str] = 'english'

class WealthAnalysisRequest(BaseModel):
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

router = APIRouter(prefix="/wealth", tags=["wealth"])
credit_service = CreditService()

@router.post("/analyze")
async def analyze_wealth(request: WealthAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Analyze wealth prospects with AI - mobile app compatible endpoint"""
    print(f"📱 MOBILE WEALTH ANALYSIS REQUEST:")
    print(f"   Date: {request.date}")
    print(f"   Time: {request.time}")
    print(f"   Force regenerate from request: {request.force_regenerate}")
    print(f"   Request object type: {type(request)}")
    print(f"   Request dict: {request.dict()}")
    
    # Convert mobile request format to web format
    birth_request = BirthDetailsRequest(
        birth_date=request.date,
        birth_time=request.time,
        birth_place=request.place,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
        force_regenerate=request.force_regenerate,
        language=request.language
    )
    print(f"🔄 Birth request force_regenerate: {birth_request.force_regenerate}")
    # Call the existing enhanced insights endpoint
    return await get_enhanced_wealth_insights(birth_request, current_user)

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
            timezone=request.timezone or 'UTC+0'
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
                from ai.structured_analyzer import StructuredAnalysisAnalyzer
                print(f"✅ StructuredAnalysisAnalyzer imported successfully")
            except Exception as e:
                print(f"❌ Failed to import StructuredAnalysisAnalyzer: {e}")
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
                'timezone': request.timezone or 'UTC+0'
            }
            
            # Create birth data object
            from types import SimpleNamespace
            birth_obj = SimpleNamespace(**birth_data)
            birth_hash = _create_birth_hash(birth_obj)
            
            # Initialize database table
            _init_ai_insights_table()
            
            # Check cache first
            force_regen = request.force_regenerate
            print(f"🔍 Cache check - force_regenerate: {force_regen}")
            stored_insights = _get_stored_ai_insights(birth_hash)
            print(f"💾 Cached insights found: {stored_insights is not None}")
            
            if stored_insights and not force_regen:
                print(f"💾 Using cached insights (force_regenerate={force_regen})")
                # Format cached response for mobile compatibility
                cached_response = {
                    'analysis': stored_insights,
                    'terms': stored_insights.get('terms', []),
                    'glossary': stored_insights.get('glossary', {}),
                    'enhanced_context': True,
                    'questions_covered': len(stored_insights.get('detailed_analysis', [])),
                    'context_type': 'cached_analysis',
                    'generated_at': datetime.now().isoformat()
                }
                yield f"data: {json.dumps({'status': 'complete', 'data': cached_response, 'cached': True})}\n\n"
                return
            elif stored_insights and force_regen:
                print(f"🔄 Cache found but force_regenerate=True, generating fresh analysis")
            
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
            
            # Create comprehensive wealth question with JSON structure
            wealth_question = """
{
  "summary": "Brief wealth overview with key insights",
  "detailed_analysis": [
    {
      "title": "Wealth Houses Analysis",
      "content": "Analysis of 2nd, 11th, and 9th houses for wealth indicators"
    },
    {
      "title": "Planetary Wealth Indicators", 
      "content": "Jupiter, Venus, and other wealth-giving planets analysis"
    },
    {
      "title": "Dhana Yogas",
      "content": "Wealth combinations and yogas in the chart"
    },
    {
      "title": "Dasha Periods for Wealth",
      "content": "Current and upcoming periods for financial gains"
    },
    {
      "title": "Investment & Business Guidance",
      "content": "Recommendations for investments and business ventures"
    }
  ],
  "final_thoughts": "Concluding summary with key takeaways and overall wealth outlook",
  "glossary": {
    "term_id": "Simple explanation of the term"
  }
}

Analyze the wealth potential focusing on:
- 2nd House (Wealth accumulation)
- 11th House (Gains and income)
- 9th House (Fortune and luck) 
- Jupiter and Venus placements
- Dhana Yogas and wealth combinations
- Current and upcoming dasha periods
- Investment recommendations
- Business vs job suitability

IMPORTANT: Include meaningful final_thoughts with overall assessment and key advice.
"""
            
            # Use structured analyzer (async)
            try:
                print(f"🤖 Initializing Structured analyzer...")
                analyzer = StructuredAnalysisAnalyzer()
                print(f"✅ Structured analyzer initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Structured analyzer: {e}")
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
                    print(f"🔄 Attempt {attempt + 1}/{max_retries} - Calling Structured API...")
                    ai_result = await analyzer.generate_structured_report(
                        wealth_question, context_dict, request.language
                    )
                    print(f"📝 STRUCTURED API RESPONSE RECEIVED:")
                    print(f"   Success: {ai_result.get('success') if ai_result else 'None'}")
                    print(f"   AI Result keys: {list(ai_result.keys()) if ai_result else 'None'}")
                    print(f"   AI Result type: {type(ai_result)}")
                    if ai_result:
                        print(f"   Error (if any): {ai_result.get('error', 'No error')}")
                        print(f"   Is raw: {ai_result.get('is_raw', False)}")
                        if ai_result.get('data'):
                            print(f"   Data keys: {list(ai_result['data'].keys())}")
                        if ai_result.get('response'):
                            print(f"   Response length: {len(str(ai_result['response']))} chars")
                    
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
                try:
                    # Handle structured analyzer response format
                    if ai_result.get('is_raw'):
                        # Raw response format (fallback)
                        parsed_response = {
                            "raw_response": ai_result.get('response', ''),
                            "quick_answer": "Analysis provided below.",
                            "detailed_analysis": [],
                            "final_thoughts": "View the detailed report below.",
                            "follow_up_questions": []
                        }
                        print(f"📄 Using raw response format")
                    else:
                        # JSON data format (preferred) - map to mobile expected format
                        raw_data = ai_result.get('data', {})
                        
                        # Map detailed_analysis fields to mobile expected format
                        detailed_analysis = []
                        for item in raw_data.get('detailed_analysis', []):
                            detailed_analysis.append({
                                "question": item.get('title', ''),
                                "answer": item.get('content', '')
                            })
                        
                        parsed_response = {
                            "quick_answer": raw_data.get('summary', 'Analysis completed successfully.'),
                            "detailed_analysis": detailed_analysis,
                            "final_thoughts": raw_data.get('final_thoughts', ''),
                            "follow_up_questions": raw_data.get('follow_up_questions', []),
                            "terms": ai_result.get('terms', []),
                            "glossary": ai_result.get('glossary', {})
                        }
                        print(f"📄 Using structured JSON format with field mapping")
                    
                    print(f"✅ RESPONSE PROCESSED SUCCESSFULLY")
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
                    
                    # Build the final insights object - send data in mobile-expected format
                    enhanced_insights = {
                        # Send the parsed data directly as 'analysis' for mobile compatibility
                        'analysis': parsed_response,
                        'terms': ai_result.get('terms', []),
                        'glossary': ai_result.get('glossary', {}),
                        'enhanced_context': True,
                        'questions_covered': len(parsed_response.get('detailed_analysis', [])),
                        'context_type': 'structured_analyzer',
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    final_response = {'status': 'complete', 'data': enhanced_insights, 'cached': False}
                    response_json = json.dumps(final_response)
                    print(f"🚀 SENDING FINAL RESPONSE: {len(response_json)} chars")
                    print(f"📝 FINAL RESPONSE PREVIEW: {response_json[:200]}...")
                    yield f"data: {response_json}\n\n"
                    print(f"✅ FINAL RESPONSE SENT SUCCESSFULLY")
                    
                except Exception as parse_error:
                    print(f"❌ Response processing failed: {parse_error}")
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to process AI response'})}\n\n"
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

@router.post("/check-cache")
async def check_cached_insights(request: BirthDetailsRequest, current_user: User = Depends(get_current_user)):
    """Check if cached insights exist without generating new ones"""
    try:
        # Create birth data object
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.birth_date,
            time=request.birth_time,
            place=request.birth_place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+0'
        )
        
        birth_hash = _create_birth_hash(birth_data)
        _init_ai_insights_table()
        
        stored_insights = _get_stored_ai_insights(birth_hash)
        
        if stored_insights:
            # Format cached response for mobile compatibility
            cached_response = {
                'analysis': stored_insights,
                'terms': stored_insights.get('terms', []),
                'glossary': stored_insights.get('glossary', {}),
                'enhanced_context': True,
                'questions_covered': len(stored_insights.get('detailed_analysis', [])),
                'context_type': 'cached_analysis',
                'generated_at': datetime.now().isoformat()
            }
            return {"success": True, "data": cached_response, "cached": True}
        else:
            return {"success": False, "message": "No cached data found"}
            
    except Exception as e:
        print(f"❌ Cache check error: {e}")
        return {"success": False, "message": str(e)}

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
            'timezone': request.timezone or 'UTC+0'
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