"""Utility routes - health checks, tests, debug"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Astrology API is running"}

@router.get("/health")
async def health():
    return {"status": "healthy"}

@router.get("/healthz")
async def healthz():
    return {"status": "ok"}

@router.get("/readiness")
async def readiness():
    return {"status": "ready"}

@router.get("/api/test")
async def test():
    return {"message": "Test endpoint working"}

@router.get("/api/test-gemini")
async def test_gemini():
    try:
        import google.generativeai as genai
        return {"status": "Gemini AI available", "version": genai.__version__}
    except ImportError:
        return {"status": "Gemini AI not available"}

@router.get("/api/test-blank-chart-predictor")
async def test_blank_chart_predictor():
    try:
        from event_prediction.blank_chart_predictor import BlankChartPredictor
        predictor = BlankChartPredictor()
        test_result = predictor.test_connection()
        return {"status": "BlankChartPredictor working", "test": test_result}
    except Exception as e:
        return {"status": "BlankChartPredictor error", "error": str(e)}

@router.get("/api/debug-environment")
async def debug_environment():
    import os
    import sys
    return {
        "python_version": sys.version,
        "python_path": sys.path[:3],
        "environment_vars": {
            "DATABASE_URL": os.getenv("DATABASE_URL", "Not set"),
            "JWT_SECRET_KEY": "***" if os.getenv("JWT_SECRET_KEY") else "Not set",
            "GEMINI_API_KEY": "***" if os.getenv("GEMINI_API_KEY") else "Not set"
        },
        "working_directory": os.getcwd()
    }

@router.get("/api/status")
async def api_status():
    return {
        "api_status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/api/login", "/api/register", "/api/health"]
    }