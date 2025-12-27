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
        print(f"🚀 Blank chart prediction request received")
        print(f"📊 Request data: {request.date}, {request.time}, {request.latitude}, {request.longitude}")
        
        birth_data = {
            'date': request.date,
            'time': request.time,
            'latitude': request.latitude,
            'longitude': request.longitude,
            'timezone': request.timezone
        }
        
        # Build astrological context
        print(f"🔧 Building astrological context...")
        builder = BlankChartContextBuilder()
        context = builder.build_context(birth_data)
        
        if 'error' in context:
            print(f"❌ Context building failed: {context['error']}")
            raise HTTPException(status_code=500, detail=context['error'])
        
        print(f"✅ Context built successfully with keys: {list(context.keys())}")
        
        # Generate AI prediction using Gemini
        print(f"🤖 Initializing Gemini predictor...")
        predictor = BlankChartGeminiPredictor()
        
        print(f"🎯 Generating AI prediction...")
        ai_result = predictor.generate_prediction(context)
        
        print(f"📤 AI result: success={ai_result.get('success')}, has_prediction={bool(ai_result.get('prediction'))}, has_fallback={bool(ai_result.get('fallback_prediction'))}")
        
        return {
            "success": ai_result.get('success', True),
            "ai_prediction": ai_result.get('prediction', ai_result.get('fallback_prediction')),
            "confidence": ai_result.get('confidence', 'High'),
            "astrological_context": context,
            "error": ai_result.get('error') if not ai_result.get('success') else None,
            "debug_info": {
                "context_keys": list(context.keys()),
                "ai_result_keys": list(ai_result.keys()),
                "timestamp": ai_result.get('timestamp')
            }
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Blank chart prediction failed: {str(e)}")
        print(f"❌ Stack trace: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick-insight")
async def get_quick_insight(request: BlankChartRequest):
    """Generate quick AI insight using Gemini"""
    try:
        print(f"🚀 Quick insight request received")
        
        birth_data = {
            'date': request.date,
            'time': request.time,
            'latitude': request.latitude,
            'longitude': request.longitude,
            'timezone': request.timezone
        }
        
        # Build astrological context
        print(f"🔧 Building context for quick insight...")
        builder = BlankChartContextBuilder()
        context = builder.build_context(birth_data)
        
        if 'error' in context:
            print(f"❌ Context building failed: {context['error']}")
            raise HTTPException(status_code=500, detail=context['error'])
        
        # Generate AI insight using Gemini
        print(f"🤖 Generating quick insight...")
        predictor = BlankChartGeminiPredictor()
        ai_result = predictor.generate_quick_insight(context)
        
        print(f"📤 Quick insight result: success={ai_result.get('success')}, has_insight={bool(ai_result.get('insight'))}")
        
        return {
            "success": ai_result.get('success', True),
            "insight": ai_result.get('insight'),
            "confidence": ai_result.get('confidence', '99%'),
            "error": ai_result.get('error') if not ai_result.get('success') else None,
            "debug_info": {
                "timestamp": ai_result.get('timestamp')
            }
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Quick insight failed: {str(e)}")
        print(f"❌ Stack trace: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-predictor")
async def test_blank_chart_predictor():
    """Test blank chart predictor initialization and connection"""
    try:
        print(f"🧪 Testing blank chart predictor...")
        
        # Test predictor initialization
        predictor = BlankChartGeminiPredictor()
        
        # Test connection
        connection_test = predictor.test_gemini_connection()
        
        return {
            "predictor_initialized": True,
            "connection_test": connection_test
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Blank chart predictor test failed: {str(e)}")
        print(f"❌ Stack trace: {error_trace}")
        
        return {
            "predictor_initialized": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "stack_trace": error_trace
        }