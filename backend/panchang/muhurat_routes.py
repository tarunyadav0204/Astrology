from fastapi import APIRouter, HTTPException
from .muhurat_calculator import MuhuratCalculator

router = APIRouter()
calculator = MuhuratCalculator()

@router.get("/vivah-muhurat")
async def get_vivah_muhurat(date: str, latitude: float, longitude: float):
    """Get marriage muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = calculator.calculate_vivah_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/property-muhurat")
async def get_property_muhurat(date: str, latitude: float, longitude: float):
    """Get property purchase muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = calculator.calculate_property_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vehicle-muhurat")
async def get_vehicle_muhurat(date: str, latitude: float, longitude: float):
    """Get vehicle purchase muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = calculator.calculate_vehicle_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/griha-pravesh-muhurat")
async def get_griha_pravesh_muhurat(date: str, latitude: float, longitude: float):
    """Get house warming muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = calculator.calculate_griha_pravesh_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))