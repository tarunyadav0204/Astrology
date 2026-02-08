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
            
            # Start with D1 from chart_data itself
            divisions = {'D1': {p: {'sign': d.get('sign', 0), 'house': d.get('house', 1)} 
                               for p, d in chart_data.get('planets', {}).items()}}
            
            print(f"\n🔍 SHADBALA ROUTES: Calculating divisional charts...")
            # Add other divisional charts
            for div_num, div_code in [(2, 'D2'), (3, 'D3'), (7, 'D7'), (9, 'D9'), (12, 'D12'), (30, 'D30')]:
                try:
                    div_chart = div_calc.calculate_divisional_chart(div_num)
                    planets_data = div_chart.get('divisional_chart', {}).get('planets', div_chart.get('planets', {}))
                    divisions[div_code] = {p: {'sign': d.get('sign', 0), 'house': d.get('house', 1)} 
                                          for p, d in planets_data.items()}
                    print(f"   ✅ {div_code}: {len(divisions[div_code])} planets")
                    if div_code == 'D9':
                        print(f"   🔍 D9 data: {divisions[div_code]}")
                except Exception as e:
                    print(f"   ❌ {div_code} failed: {e}")
            
            chart_data['divisions'] = divisions
            print(f"\n✅ chart_data['divisions'] populated with {len(divisions)} vargas")
        
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
