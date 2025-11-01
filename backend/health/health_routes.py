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
from calculators.health_calculator import HealthCalculator
from ai.gemini_health_analyzer import GeminiHealthAnalyzer

class BirthDetailsRequest(BaseModel):
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM
    birth_place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    force_regenerate: Optional[bool] = False

router = APIRouter(prefix="/health", tags=["health"])

def _create_birth_hash(birth_data):
    """Create unique hash for birth data"""
    birth_string = f"{birth_data.date}_{birth_data.time}_{birth_data.latitude}_{birth_data.longitude}"
    return hashlib.sha256(birth_string.encode()).hexdigest()

def _init_ai_insights_table():
    """Initialize AI insights table if not exists"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_health_insights (
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
    cursor.execute('SELECT insights_data FROM ai_health_insights WHERE birth_hash = ?', (birth_hash,))
    result = cursor.fetchone()
    conn.close()
    return json.loads(result[0]) if result else None

def _store_ai_insights(birth_hash, insights_data):
    """Store AI insights in database"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO ai_health_insights (birth_hash, insights_data, updated_at)
        VALUES (?, ?, ?)
    ''', (birth_hash, json.dumps(insights_data), datetime.now().isoformat()))
    conn.commit()
    conn.close()

@router.post("/overall-assessment")
async def get_overall_health_assessment(request: BirthDetailsRequest):
    """Get complete health assessment without AI insights"""
    try:
        # Create birth data object
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.birth_date,
            time=request.birth_time,
            place=request.birth_place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+5:30'
        )
        
        # Calculate birth chart
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Calculate health analysis
        health_calc = HealthCalculator(chart_data, birth_data)
        health_analysis = health_calc.calculate_overall_health()
        
        return {
            "status": "success",
            "data": health_analysis
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Health calculation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Health calculation error: {str(e)}\n{error_details}")

from fastapi.responses import StreamingResponse
import asyncio

@router.post("/ai-insights")
async def get_ai_health_insights(request: BirthDetailsRequest):
    """Get AI-powered health insights with streaming keep-alive"""
    
    async def generate_streaming_response():
        import json
        
        try:
            # Send initial status
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Initializing analysis...'})}\n\n"
            
            # Create birth data object
            from types import SimpleNamespace
            birth_data = SimpleNamespace(
                date=request.birth_date,
                time=request.birth_time,
                place=request.birth_place,
                latitude=request.latitude or 28.6139,
                longitude=request.longitude or 77.2090,
                timezone=request.timezone or 'UTC+5:30'
            )
            
            # Create unique hash for this birth data
            birth_hash = _create_birth_hash(birth_data)
            
            # Initialize database table
            _init_ai_insights_table()
            
            # Check if we have stored insights (unless force regenerate)
            if not request.force_regenerate:
                stored_insights = _get_stored_ai_insights(birth_hash)
                if stored_insights:
                    yield f"data: {json.dumps({'status': 'complete', 'data': stored_insights, 'cached': True})}\n\n"
                    return
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Calculating birth chart...'})}\n\n"
            
            # Calculate birth chart and health analysis
            chart_calc = ChartCalculator({})
            chart_data = chart_calc.calculate_chart(birth_data)
            
            health_calc = HealthCalculator(chart_data, birth_data)
            health_analysis = health_calc.calculate_overall_health()
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating AI insights...'})}\n\n"
            
            # Generate AI insights
            try:
                gemini_analyzer = GeminiHealthAnalyzer()
                
                # Run AI generation with periodic updates
                import threading
                import time
                result = {}
                exception = {}
                
                def ai_worker():
                    try:
                        result['data'] = gemini_analyzer.generate_health_insights(health_analysis, chart_data)
                    except Exception as e:
                        exception['error'] = e
                
                thread = threading.Thread(target=ai_worker)
                thread.start()
                
                # Send keep-alive messages every 10 seconds
                while thread.is_alive():
                    yield f"data: {json.dumps({'status': 'processing', 'message': 'AI analysis in progress...'})}\n\n"
                    await asyncio.sleep(10)
                
                thread.join()
                
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
                        'health_overview': '',
                        'constitutional_analysis': '',
                        'key_health_areas': [],
                        'lifestyle_recommendations': [],
                        'preventive_measures': [],
                        'positive_indicators': ''
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
