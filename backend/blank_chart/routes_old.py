from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.blank_chart_context_builder import BlankChartContextBuilder
from calculators.blank_chart_gemini_predictor import BlankChartGeminiPredictor

router = APIRouter(prefix="/blank-chart", tags=["Blank Chart Predictions"])

class BlankChartRequest(BaseModel):
    date: str  # YYYY-MM-DD format
    time: str  # HH:MM format
    latitude: float
    longitude: float
    timezone: str

@router.post("/stunning-prediction")
async def get_stunning_prediction(request: BlankChartRequest):
    """Generate stunning AI predictions using Gemini"""
    try:
        birth_data = {
            'date': request.date,
            'time': request.time,
            'latitude': request.latitude,
            'longitude': request.longitude,
            'timezone': request.timezone
        }
        
        # Build astrological context
        builder = BlankChartContextBuilder()
        context = builder.build_context(birth_data)
        
        if 'error' in context:
            raise HTTPException(status_code=500, detail=context['error'])
        
        # Generate AI prediction using Gemini
        predictor = BlankChartGeminiPredictor()
        ai_result = predictor.generate_prediction(context)
        
        return {
            "success": ai_result.get('success', True),
            "ai_prediction": ai_result.get('prediction', ai_result.get('fallback_prediction')),
            "confidence": ai_result.get('confidence', 'High'),
            "astrological_context": context,
            "error": ai_result.get('error') if not ai_result.get('success') else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _create_stunning_summary(context: Dict) -> Dict:
    """Create immediately impactful summary"""
    pillars = context.get('pillars', {})
    age = context.get('metadata', {}).get('target_age', 25)
    
    summary = {
        "age_revelation": f"You are currently {age} years old",
        "life_phase": "",
        "major_themes": [],
        "immediate_insights": [],
        "karmic_patterns": [],
        "timing_alerts": []
    }
    
    # BCP Life Phase
    bcp = pillars.get('bcp_activation', {})
    active_house = bcp.get('activated_house')
    
    if active_house:
        house_meaning = bcp.get('house_meaning', '')
        summary["life_phase"] = f"You're in a {house_meaning.lower()} focused period"
        
        if bcp.get('house_occupants'):
            planets = ', '.join(bcp.get('house_occupants', []))
            summary["immediate_insights"].append(f"Planetary energies of {planets} are highly active")
    
    # Nakshatra Triggers
    nak_triggers = pillars.get('nakshatra_triggers', {})
    if nak_triggers.get('is_fated_period'):
        birth_star = nak_triggers.get('birth_star', 'Unknown')
        summary["timing_alerts"].append(f"FATED PERIOD according to {birth_star} - major events destined")
    
    # Lal Kitab Debts
    debts = pillars.get('lal_kitab_layer', {}).get('ancestral_debts', [])
    if debts:
        summary["karmic_patterns"] = debts
    
    # Jaimini Insights
    jaimini = pillars.get('jaimini_markers', {})
    atmakaraka = jaimini.get('atmakaraka')
    if atmakaraka:
        summary["immediate_insights"].append(f"Soul planet {atmakaraka} guides your life purpose")
    
    return summary

@router.post("/quick-insight")
async def get_quick_insight(request: BlankChartRequest):
    """Generate quick AI insight using Gemini"""
    try:
        birth_data = {
            'date': request.date,
            'time': request.time,
            'latitude': request.latitude,
            'longitude': request.longitude,
            'timezone': request.timezone
        }
        
        # Build astrological context
        builder = BlankChartContextBuilder()
        context = builder.build_context(birth_data)
        
        if 'error' in context:
            raise HTTPException(status_code=500, detail=context['error'])
        
        # Generate AI insight using Gemini
        predictor = BlankChartGeminiPredictor()
        ai_result = predictor.generate_quick_insight(context)
        
        return {
            "success": ai_result.get('success', True),
            "insight": ai_result.get('insight'),
            "confidence": ai_result.get('confidence', '99%'),
            "error": ai_result.get('error') if not ai_result.get('success') else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_most_stunning_insight(context: Dict) -> str:
    """Extract single most impactful insight"""
    pillars = context.get('pillars', {})
    age = context.get('metadata', {}).get('target_age', 25)
    
    # Priority 1: Fated period
    nak_triggers = pillars.get('nakshatra_triggers', {})
    if nak_triggers.get('is_fated_period'):
        birth_star = nak_triggers.get('birth_star', 'your birth star')
        return f"According to {birth_star}, you are in a FATED PERIOD. Major life events are destined now."
    
    # Priority 2: Major house activation
    bcp = pillars.get('bcp_activation', {})
    active_house = bcp.get('activated_house')
    if active_house == 1:
        return f"At age {age}, your identity is undergoing complete transformation. This is your rebirth year."
    elif active_house == 7:
        return f"Your relationship sector is cosmically activated at age {age}. Major partnership changes destined."
    elif active_house == 10:
        return f"Career breakthrough period at age {age}. Professional destiny unfolds now."
    
    # Priority 3: Ancestral karma
    debts = pillars.get('lal_kitab_layer', {}).get('ancestral_debts', [])
    if debts:
        return f"Ancestral karma active: {debts[0]}"
    
    # Default
    return f"At age {age}, you're in a significant life cycle reshaping your destiny."