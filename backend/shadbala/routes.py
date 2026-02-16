from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from calculators.classical_shadbala import calculate_classical_shadbala

router = APIRouter()

class ShadbalaRequest(BaseModel):
    birth_data: Dict[str, Any]
    chart_data: Dict[str, Any]

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
        
        return {
            "shadbala": sorted_results,
            "summary": {
                "strongest": max(results.items(), key=lambda x: x[1]['total_rupas']),
                "weakest": min(results.items(), key=lambda x: x[1]['total_rupas'])
            },
            "calculation_method": "Classical Brihat Parashara Hora Shastra",
            "authenticity": "Complete 6-fold calculation with all sub-components"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classical Shadbala calculation failed: {str(e)}")
