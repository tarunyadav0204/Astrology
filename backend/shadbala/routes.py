from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from calculators.classical_shadbala import calculate_classical_shadbala

router = APIRouter()

class ShadbalaRequest(BaseModel):
    birth_data: Dict[str, Any]
    chart_data: Dict[str, Any]

def _compute_bhav_bala(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute Bhav Bala (house strength) for all 12 houses. Returns dict keyed by house number '1'..'12'."""
    bhav_bala = {}
    if not chart_data or not isinstance(chart_data.get("houses"), list) or len(chart_data.get("houses", [])) != 12:
        return bhav_bala
    if not chart_data.get("planets"):
        return bhav_bala
    try:
        from calculators.house_strength_calculator import HouseStrengthCalculator
        calc = HouseStrengthCalculator(chart_data)
        for house_num in range(1, 13):
            data = calc.calculate_house_strength(house_num)
            bhav_bala[str(house_num)] = {
                "total_strength": data["total_strength"],
                "grade": data["grade"],
                "interpretation": data["interpretation"],
                "factors": data.get("factors", {}),
            }
    except Exception as e:
        print(f"Bhav Bala calculation skipped: {e}")
    return bhav_bala

@router.post("/calculate-classical-shadbala")
async def calculate_classical_shadbala_endpoint(request: ShadbalaRequest):
    """Calculate authentic classical Shadbala"""
    try:
        # Calculate divisional charts if not present
        chart_data = request.chart_data
        if 'divisions' not in chart_data:
            from calculators.divisional_chart_calculator import DivisionalChartCalculator
            div_calc = DivisionalChartCalculator(chart_data)
            chart_data['divisions'] = div_calc.calculate_all_divisional_charts()
            print(f"\n✅ chart_data['divisions'] populated with {len(chart_data['divisions'])} vargas")
        
        results = calculate_classical_shadbala(request.birth_data, chart_data)
        
        if not results:
            raise HTTPException(status_code=400, detail="No valid planets found for calculation")
        
        # Sort by total strength
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['total_rupas'], reverse=True))
        
        # Bhav Bala (house strength) for all 12 houses
        bhav_bala = _compute_bhav_bala(chart_data)
        
        response = {
            "shadbala": sorted_results,
            "summary": {
                "strongest": max(results.items(), key=lambda x: x[1]['total_rupas']),
                "weakest": min(results.items(), key=lambda x: x[1]['total_rupas'])
            },
            "calculation_method": "Classical Brihat Parashara Hora Shastra",
            "authenticity": "Complete 6-fold calculation with all sub-components"
        }
        if bhav_bala:
            response["bhav_bala"] = bhav_bala
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classical Shadbala calculation failed: {str(e)}")
