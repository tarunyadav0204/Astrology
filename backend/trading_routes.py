from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os
import json
import asyncio
import re
from datetime import datetime
from auth import get_current_user, User
from credits.credit_service import CreditService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.trading_ai_context_generator import TradingAIContextGenerator
from ai.gemini_chat_analyzer import GeminiChatAnalyzer
from calculators.trading_calendar_service import TradingCalendarService

class TradingRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: str = 'male'
    target_date: Optional[str] = None
    language: Optional[str] = 'english'
    response_style: Optional[str] = 'concise'
    premium_analysis: Optional[bool] = False
    force_regenerate: Optional[bool] = False

router = APIRouter(prefix="/trading", tags=["trading"])
context_gen = TradingAIContextGenerator()
credit_service = CreditService()

@router.post("/daily-forecast")
async def get_daily_forecast(request: TradingRequest, current_user: User = Depends(get_current_user)):
    if request.premium_analysis:
        base_cost = credit_service.get_credit_setting('trading_daily_cost')
        multiplier = credit_service.get_credit_setting('premium_chat_cost')
        cost = base_cost * multiplier
    else:
        cost = credit_service.get_credit_setting('trading_daily_cost')
    
    # Check cache first
    import sqlite3
    import hashlib
    
    target_date = request.target_date or datetime.now().strftime('%Y-%m-%d')
    cache_key = hashlib.md5(f"{current_user.userid}_{target_date}_{request.date}_{request.time}_{request.place}".encode()).hexdigest()
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_daily_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE,
                user_id INTEGER,
                target_date TEXT,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Skip cache if force_regenerate is True
        if not request.force_regenerate:
            cursor.execute("""
                SELECT analysis_data FROM trading_daily_cache 
                WHERE cache_key = ? AND DATE(created_at) = DATE('now')
            """, (cache_key,))
            
            cached_result = cursor.fetchone()
            
            if cached_result:
                conn.close()
                cached_data = json.loads(cached_result[0])
                cached_data['cached'] = True
                return cached_data
        
        conn.close()
            
    except Exception as cache_error:
        print(f"Cache check failed: {cache_error}")
    
    # If not cached, check credits and proceed
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {cost} credits.")

    try:
        target_dt = datetime.strptime(request.target_date, "%Y-%m-%d") if request.target_date else datetime.now()
        birth_data = request.dict()
        
        context = await asyncio.get_event_loop().run_in_executor(
            None, context_gen.build_trading_context, birth_data, target_dt
        )
        forecast = context['trading_forecast']
        
        birth_hash = context_gen._create_birth_hash(birth_data)
        if birth_hash not in context_gen.static_cache:
            context_gen.build_base_context(birth_data)
            
        natal_chart = context_gen.static_cache[birth_hash]['d1_chart']
        calendar_service = TradingCalendarService(natal_chart, birth_data)
        timings = calendar_service.get_intraday_timings(target_dt)
        
        tara_bala = forecast.get('details', {}).get('tara_bala', {})
        tara_type = tara_bala.get('type', 'Unknown')
        tara_quality = tara_bala.get('quality', 'Unknown')
        chandra_bala = forecast.get('details', {}).get('chandra_bala', {})
        risk_list = [r['name'] for r in forecast.get('risk_factors', [])]
        risk_str = ", ".join(risk_list) if risk_list else "None"
        
        prompt = f"""
You are an expert Financial Astrologer acting as a Trading Coach. 
Your goal is to explain the "Why" behind the prediction using Vedic principles.

DATA:
- User Signal: {forecast['signal']} ({forecast['action']})
- Luck Score: {forecast['luck_score']}/100
- Transit Nakshatra: {forecast['market_mood']['nature']} Nature (Strategy: {forecast['market_mood']['strategy']})
- Tara Bala (Personal): {tara_type} ({tara_quality})
- Chandra Bala (Personal): {chandra_bala.get('quality', 'Unknown')} ({chandra_bala.get('transit_house_from_natal', 'Unknown')}th House from Natal Moon)
- Risk Factors: {risk_str}

JSON OUTPUT ONLY (Must be valid JSON):
{{
  "verdict": "{forecast['action']}",
  "confidence": "{forecast['luck_score']}%",
  "summary": "A sharp, executive summary combining the market atmosphere with the user's personal luck.",
  "detailed_report": [
    {{
      "title": "💫 Your Personal Alignment (Tara Bala)",
      "content": "Explain the specific Tara ({tara_type}). Why is this star {tara_quality} for the user? (e.g., 'As your Vipat Tara, it brings sudden obstacles...')"
    }},
    {{
      "title": "⚡ Day's Trading Atmosphere (Moon Nature)",
      "content": "Analyze the Transit Nakshatra's nature ({forecast['market_mood']['nature']}). Mention its Ruling Planet or Symbol to explain WHY the crowd psychology is 'Swift', 'Cruel', or 'Fixed' today. Clarify this affects volatility, not direction."
    }},
    {{
      "title": "🧠 Your Psychological State (Chandra Bala)",
      "content": "The Moon is in the {chandra_bala.get('transit_house_from_natal', 'Unknown')}th house from your birth moon. Explain how this specific house affects decision-making (e.g., 8th house = anxiety, 9th = luck/intuition, 12th = bad judgment)."
    }},
    {{
      "title": "🛡️ Strategic Advice",
      "content": "Synthesize the Score ({forecast['luck_score']}) into a money management plan. If Risk Factors exist ({risk_str}), explain exactly what 'Badhaka' or 'Gandanta' means for a trader (e.g., 'Gandanta = unexpected reversals')."
    }}
  ],
  "risk_warning": "Mention any risk factors like Gandanta or Badhaka if present, otherwise say 'None'."
}}
"""
        
        gemini = GeminiChatAnalyzer()
        ai_result = await gemini.generate_chat_response(prompt, context, [], request.language, "detailed", None, request.premium_analysis)
        
        if ai_result['success']:
            ai_response_text = ai_result.get('response', '')
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', ai_response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', ai_response_text, re.DOTALL)
                json_text = json_match.group(1) if json_match else ai_response_text

            try:
                parsed = json.loads(json_text)
                
                response_data = {
                    "status": "success",
                    "ai_analysis": parsed,
                    "intraday_timings": timings,
                    "raw_forecast": forecast,
                    "cached": False
                }
                
                # Cache the result
                try:
                    conn = sqlite3.connect('astrology.db')
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO trading_daily_cache 
                        (cache_key, user_id, target_date, analysis_data)
                        VALUES (?, ?, ?, ?)
                    """, (cache_key, current_user.userid, target_date, json.dumps(response_data)))
                    
                    conn.commit()
                    conn.close()
                except Exception as cache_error:
                    print(f"Failed to cache result: {cache_error}")
                
                # Only spend credits after successful caching
                credit_service.spend_credits(current_user.userid, cost, 'trading_daily', f"Trading {target_dt.strftime('%Y-%m-%d')}")
                
                return response_data
            except json.JSONDecodeError:
                return {"status": "error", "message": "Failed to parse AI response", "raw_response": ai_response_text}
        else:
            return {"status": "error", "message": "AI Generation Failed", "ai_result": ai_result}
            
    except Exception as e:
        return {"status": "error", "message": str(e), "error_type": type(e).__name__}

@router.post("/monthly-calendar")
async def get_monthly_calendar(request: TradingRequest, year: int, month: int, current_user: User = Depends(get_current_user)):
    if request.premium_analysis:
        base_cost = credit_service.get_credit_setting('trading_monthly_cost')
        multiplier = credit_service.get_credit_setting('premium_chat_cost')
        cost = base_cost * multiplier
    else:
        cost = credit_service.get_credit_setting('trading_monthly_cost')
    
    # Check cache first
    import sqlite3
    import hashlib
    
    cache_key = hashlib.md5(f"{current_user.userid}_{year}_{month}_{request.date}_{request.time}_{request.place}".encode()).hexdigest()
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_monthly_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE,
                user_id INTEGER,
                year INTEGER,
                month INTEGER,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            SELECT analysis_data FROM trading_monthly_cache 
            WHERE cache_key = ?
        """, (cache_key,))
        
        cached_result = cursor.fetchone()
        conn.close()
        
        if cached_result:
            cached_data = json.loads(cached_result[0])
            
            async def return_cached():
                yield f"data: {json.dumps({'status': 'complete', 'data': cached_data, 'cached': True})}\n\n"
            
            return StreamingResponse(return_cached(), media_type="text/plain")
            
    except Exception as cache_error:
        print(f"Cache check failed: {cache_error}")
    
    # If not cached, check credits and proceed
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {cost} credits.")
    
    async def generate():
        try:
            birth_data = request.dict()
            # FORCE TIMEZONE SAFETY - ensure consistency with daily forecast
            if not birth_data.get('timezone'):
                birth_data['timezone'] = 'UTC+5:30'
            
            # Ensure Base Context is built for cache
            context_gen.build_base_context(birth_data)
            birth_hash = context_gen._create_birth_hash(birth_data)
            natal_chart = context_gen.static_cache[birth_hash]['d1_chart']
            
            service = TradingCalendarService(natal_chart, birth_data)
            calendar = await asyncio.get_event_loop().run_in_executor(
                None, service.get_monthly_forecast, year, month
            )
            
            # Cache the result
            try:
                conn = sqlite3.connect('astrology.db')
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO trading_monthly_cache 
                    (cache_key, user_id, year, month, analysis_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (cache_key, current_user.userid, year, month, json.dumps(calendar)))
                
                conn.commit()
                conn.close()
            except Exception as cache_error:
                print(f"Failed to cache result: {cache_error}")
            
            # Only spend credits after successful caching
            credit_service.spend_credits(current_user.userid, cost, 'trading_calendar', f"Calendar {month}/{year}")
            yield f"data: {json.dumps({'status': 'complete', 'data': calendar, 'cached': False})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/plain")