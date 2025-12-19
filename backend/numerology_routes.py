from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from calculators.numerology.numerology_manager import NumerologyManager
from auth import get_current_user

router = APIRouter()

class NumerologyRequest(BaseModel):
    name: str
    dob: str  # YYYY-MM-DD format
    gender: Optional[str] = None

class NameOptimizationRequest(BaseModel):
    name: str
    system: Optional[str] = 'chaldean'

class ForecastRequest(BaseModel):
    dob: str  # YYYY-MM-DD format
    target_date: Optional[str] = None

@router.post("/numerology/full-report")
async def get_full_numerology_report(request: NumerologyRequest, current_user=Depends(get_current_user)):
    """Get complete numerology analysis including identity, grid, and forecast"""
    try:
        manager = NumerologyManager()
        report = manager.get_full_report(request.name, request.dob)
        return {"success": True, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating numerology report: {str(e)}")

@router.post("/numerology/identity")
async def get_identity_report(request: NumerologyRequest, current_user=Depends(get_current_user)):
    """Get core identity analysis - Life Path, Expression, Soul Urge, Lo Shu Grid"""
    try:
        manager = NumerologyManager()
        report = manager.get_identity_report(request.name, request.dob, request.gender)
        return {"success": True, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating identity report: {str(e)}")

@router.post("/numerology/forecast")
async def get_forecast_report(request: ForecastRequest, current_user=Depends(get_current_user)):
    """Get timing analysis - Personal Year/Month/Day cycles and Life Pinnacles"""
    try:
        manager = NumerologyManager()
        report = manager.get_forecast_report(request.dob, request.target_date)
        return {"success": True, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast report: {str(e)}")

@router.post("/numerology/optimize-name")
async def optimize_name(request: NameOptimizationRequest, current_user=Depends(get_current_user)):
    """Check name compatibility and get lucky name suggestions"""
    try:
        manager = NumerologyManager()
        analysis = manager.check_name_compatibility(request.name, request.system)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing name: {str(e)}")

@router.get("/numerology/demo")
async def get_demo_report():
    """Demo endpoint for non-authenticated users"""
    try:
        manager = NumerologyManager()
        demo_report = manager.get_identity_report("John Doe", "1990-01-01")
        return {"success": True, "data": demo_report, "demo": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating demo report: {str(e)}")