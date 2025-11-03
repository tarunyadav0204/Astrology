from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os
import hashlib
import json
import sqlite3
from datetime import datetime

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

router = APIRouter(prefix="/wealth", tags=["wealth"])

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
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Initializing wealth analysis...'})}\\n\\n"
            
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
                    yield f"data: {json.dumps({'status': 'complete', 'data': stored_insights, 'cached': True})}\\n\\n"
                    return
            else:
                print(f"Debug - Skipping cache due to force regenerate")
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Calculating birth chart...'})}\\n\\n"
            
            # Calculate birth chart and wealth analysis
            chart_calc = ChartCalculator({})
            chart_data = chart_calc.calculate_chart(birth_data)
            
            wealth_calc = WealthCalculator(chart_data, birth_data)
            wealth_analysis = wealth_calc.calculate_overall_wealth()
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating AI insights...'})}\\n\\n"
            
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
                    yield f"data: {json.dumps({'status': 'processing', 'message': 'AI wealth analysis in progress...'})}\\n\\n"
                    await asyncio.sleep(5)
                    count += 1
                
                if thread.is_alive():
                    yield f"data: {json.dumps({'status': 'error', 'error': 'AI analysis timed out'})}\\n\\n"
                    return
                
                thread.join(timeout=1)
                
                if 'error' in exception:
                    raise exception['error']
                
                ai_insights = result['data']
                
                # Store insights in database
                _store_ai_insights(birth_hash, ai_insights)
                
                # Send final result
                yield f"data: {json.dumps({'status': 'complete', 'data': ai_insights, 'cached': False})}\\n\\n"
                
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
                yield f"data: {json.dumps({'status': 'complete', 'data': error_response, 'cached': False})}\\n\\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\\n\\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )