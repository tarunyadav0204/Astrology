"""
Education Analysis API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user
from calculators.chart_calculator import ChartCalculator
from .education_analyzer import EducationAnalyzer

router = APIRouter(prefix="/education", tags=["education"])

@router.post("/analyze")
async def analyze_education(
    birth_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze education prospects using classical Vedic astrology
    """
    try:
        # Calculate chart - convert dict to object-like structure
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Perform education analysis
        analyzer = EducationAnalyzer(birth_data, chart_data)
        analysis = analyzer.analyze_education()
        
        return {
            "success": True,
            "analysis": analysis,
            "birth_data": birth_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/constants")
async def get_education_constants():
    """
    Get education analysis constants and explanations
    """
    from .constants import EDUCATION_HOUSES, EDUCATION_PLANETS, SUBJECT_RECOMMENDATIONS
    
    return {
        "houses": EDUCATION_HOUSES,
        "planets": EDUCATION_PLANETS,
        "subjects": SUBJECT_RECOMMENDATIONS
    }