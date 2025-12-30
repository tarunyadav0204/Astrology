from fastapi import APIRouter, HTTPException
from .muhurat_calculator import MuhuratCalculator

router = APIRouter()
calculator = MuhuratCalculator()

@router.get("/vivah-muhurat")
async def get_vivah_muhurat(date: str, latitude: float, longitude: float, timezone: str = "Asia/Kolkata"):
    """Get marriage muhurat for given date and location"""
    try:
        result = calculator.calculate_vivah_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/property-muhurat")
async def get_property_muhurat(date: str, latitude: float, longitude: float, timezone: str = "Asia/Kolkata"):
    """Get property purchase muhurat for given date and location"""
    try:
        result = calculator.calculate_property_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vehicle-muhurat")
async def get_vehicle_muhurat(date: str, latitude: float, longitude: float, timezone: str = "Asia/Kolkata"):
    """Get vehicle purchase muhurat for given date and location"""
    try:
        result = calculator.calculate_vehicle_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/griha-pravesh-muhurat")
async def get_griha_pravesh_muhurat(date: str, latitude: float, longitude: float, timezone: str = "Asia/Kolkata"):
    """Get house warming muhurat for given date and location"""
    try:
        result = calculator.calculate_griha_pravesh_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))