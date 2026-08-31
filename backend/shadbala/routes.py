from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
from calculators.classical_shadbala import calculate_classical_shadbala
from calculators.classical_bhava_bala import calculate_classical_bhava_bala

router = APIRouter()

class ShadbalaRequest(BaseModel):
    birth_data: Dict[str, Any]
    chart_data: Dict[str, Any]

def _compute_supplementary_house_strength(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return the app's general house score.

    This weighted diagnostic is intentionally not called classical Bhava Bala:
    Parashara's worksheet uses Bhavadhipati, Bhava Dig and Bhava Drishti Bala,
    which are a different calculation.
    """
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
        bhava_bala = calculate_classical_bhava_bala(request.birth_data, chart_data, results)
        
        if not results:
            raise HTTPException(status_code=400, detail="No valid planets found for calculation")
        
        # Sort by total strength
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['relative_rank']))
        
        supplementary_house_strength = _compute_supplementary_house_strength(chart_data)
        
        response = {
            "shadbala": sorted_results,
            "bhava_bala": bhava_bala,
            "summary": {
                "strongest": min(results.items(), key=lambda x: x[1]['relative_rank']),
                "weakest": max(results.items(), key=lambda x: x[1]['relative_rank'])
            },
            "calculation_method": "BPHS Ch. 26–27 with Sripati/Kedarnath-Dutt conventions",
            "bhava_bala_method": "BPHS Ch. 27.26–31: lord, direction, aspect, occupation and day/twilight/night",
            "validation": {
                "reference": "Parashara's Light 7.0.3 public Chennai sample",
                "exact_rows": ["Sthana Bala", "Dig Bala", "Drik Bala"],
                "bounded_rows": ["Kala Bala"],
                "convention_dependent_rows": ["Chesta Bala", "Ishta/Kashta Phala"],
                "note": (
                    "Totals include the selected classical Chesta mean-longitude convention. "
                    "Do not treat Shadbala as a health, lifespan, or event-probability score."
                ),
                "bhava_bala_note": (
                    "Bhava Bala is a house-strength worksheet, not an outcome probability. "
                    "The BPHS twilight adjustment uses a disclosed one-ghati Sandhya convention."
                ),
            },
        }
        if supplementary_house_strength:
            response["supplementary_house_strength"] = supplementary_house_strength
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classical Shadbala calculation failed: {str(e)}")
