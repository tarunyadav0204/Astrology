from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ..engines.badhaka_maraka_analyzer import BadhakaMarakaAnalyzer

router = APIRouter()

class BadhakaMarakaRequest(BaseModel):
    natal_chart: Dict[str, Any]
    planet: Optional[str] = None  # If provided, analyze specific planet

@router.post("/badhaka-maraka-analysis")
async def analyze_badhaka_maraka(request: BadhakaMarakaRequest):
    """
    Analyze Badhaka and Maraka planets for a natal chart
    
    Returns:
    - Complete chart analysis if no planet specified
    - Specific planet analysis if planet provided
    """
    try:
        analyzer = BadhakaMarakaAnalyzer()
        
        if request.planet:
            # Analyze specific planet
            result = analyzer.analyze_planet_badhaka_maraka(
                request.planet, 
                request.natal_chart
            )
            return {
                "success": True,
                "planet": request.planet,
                "analysis": result
            }
        else:
            # Get complete chart summary
            result = analyzer.get_chart_badhaka_maraka_summary(request.natal_chart)
            return {
                "success": True,
                "chart_analysis": result
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/badhaka-maraka-info/{ascendant_sign}")
async def get_badhaka_maraka_info(ascendant_sign: int):
    """
    Get Badhaka and Maraka information for a specific ascendant sign
    
    Args:
        ascendant_sign: Ascendant sign number (0-11)
    """
    try:
        if not 0 <= ascendant_sign <= 11:
            raise HTTPException(status_code=400, detail="Ascendant sign must be between 0-11")
        
        analyzer = BadhakaMarakaAnalyzer()
        
        # Create minimal chart for analysis
        natal_chart = {"ascendant": ascendant_sign * 30}
        result = analyzer.get_chart_badhaka_maraka_summary(natal_chart)
        
        return {
            "success": True,
            "ascendant_sign": ascendant_sign,
            "info": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Info retrieval failed: {str(e)}")