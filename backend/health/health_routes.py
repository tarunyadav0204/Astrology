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

@router.post("/ai-insights")
async def get_ai_health_insights(request: BirthDetailsRequest):
    """Get AI-powered health insights with database caching"""
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
        
        # Create unique hash for this birth data
        birth_hash = _create_birth_hash(birth_data)
        
        # Initialize database table
        _init_ai_insights_table()
        
        # Check if we have stored insights (unless force regenerate)
        if not request.force_regenerate:
            stored_insights = _get_stored_ai_insights(birth_hash)
            if stored_insights:
                return {
                    "status": "success",
                    "data": stored_insights,
                    "cached": True
                }
        
        # Calculate birth chart and health analysis
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        health_calc = HealthCalculator(chart_data, birth_data)
        health_analysis = health_calc.calculate_overall_health()
        
        # Generate AI insights
        try:
            print("Initializing Gemini analyzer...")
            gemini_analyzer = GeminiHealthAnalyzer()
            print("Gemini analyzer initialized successfully")
            
            print("Calling Gemini API...")
            ai_insights = gemini_analyzer.generate_health_insights(health_analysis, chart_data)
            print(f"Gemini API response: {ai_insights}")
            
            # Store insights in database
            _store_ai_insights(birth_hash, ai_insights)
            
        except ValueError as ve:
            print(f"Gemini configuration error: {ve}")
            # Return error response with empty insights
            ai_insights = {
                'success': False,
                'insights': {
                    'health_overview': '',
                    'constitutional_analysis': '',
                    'key_health_areas': [],
                    'lifestyle_recommendations': [],
                    'preventive_measures': [],
                    'positive_indicators': ''
                },
                'error': f'Gemini API configuration error: {str(ve)}'
            }
        except Exception as ge:
            print(f"Gemini API error: {ge}")
            import traceback
            traceback.print_exc()
            # Return error response with empty insights
            ai_insights = {
                'success': False,
                'insights': {
                    'health_overview': '',
                    'constitutional_analysis': '',
                    'key_health_areas': [],
                    'lifestyle_recommendations': [],
                    'preventive_measures': [],
                    'positive_indicators': ''
                },
                'error': f'Gemini API error: {str(ge)}'
            }
        
        return {
            "status": "success",
            "data": ai_insights,
            "cached": False
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"AI insights error: {error_details}")
        raise HTTPException(status_code=500, detail=f"AI insights error: {str(e)}\n{error_details}")