from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from copy import deepcopy
from calculators.planetary_dignities_calculator import (
    PlanetaryDignitiesCalculator,
    SIGN_LORDS,
    SIGN_NAMES,
)
# Retrograde status is already available in chart data

router = APIRouter()

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: str

@router.post("/planetary-dignities")
async def calculate_planetary_dignities(request: Dict[str, Any]):
    """Calculate comprehensive planetary dignities and states"""
    try:
        chart_data = request.get('chart_data', {})
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")

        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        calculator = PlanetaryDignitiesCalculator(chart_data)
        dignities = calculator.calculate_planetary_dignities()
        positions = calculator.calculate_position_tables(
            request.get('condition_chart_data') or chart_data,
            dignities=dignities,
            birth_data=request.get('birth_data'),
        )
        _attach_professional_strength(positions, chart_data, request.get('birth_data'))
        return {
            "dignities": dignities,
            "positions": positions,
            "ascendant_sign": ascendant_sign,
            "summary": _generate_summary(dignities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate dignities: {str(e)}")


def _attach_professional_strength(positions, chart_data, birth_data):
    """Attach established strength worksheets without changing old fields.

    Failures are explicit in ``calculation_status``.  The client never creates
    a substitute value locally.
    """
    rows = {row.get('name'): row for row in positions.get('planets', [])}
    try:
        from calculators.divisional_chart_calculator import DivisionalChartCalculator
        working = deepcopy(chart_data)
        div_calc = DivisionalChartCalculator(working)
        divisions = div_calc.calculate_all_divisional_charts()
        working['divisions'] = divisions
        d9_result = div_calc.calculate_divisional_chart(9)
        d9_planets = (d9_result.get('divisional_chart') or {}).get('planets', {})
        calc = PlanetaryDignitiesCalculator(working)
        shodashavarga_weights = {
            'D1': 3.5, 'D2': 1.0, 'D3': 1.0, 'D4': 0.5,
            'D7': 0.5, 'D9': 3.0, 'D10': 0.5, 'D12': 0.5,
            'D16': 2.0, 'D20': 0.5, 'D24': 0.5, 'D27': 0.5,
            'D30': 1.0, 'D40': 0.5, 'D45': 0.5, 'D60': 4.0,
        }
        panchadha_points = {
            'greatFriend': 18.0, 'friend': 15.0, 'neutral': 10.0,
            'enemy': 7.0, 'greatEnemy': 5.0,
        }
        natal_signs = {
            planet: int(data.get('sign', 0)) % 12
            for planet, data in (chart_data.get('planets') or {}).items()
            if isinstance(data, dict)
        }

        def varga_dignity(planet, sign):
            """Varga sign dignity; D1 degree-bounded Moolatrikona is separate."""
            if sign == (calc.EXALTATION_DATA.get(planet) or {}).get('sign'):
                return 'exalted'
            if sign == (calc.DEBILITATION_DATA.get(planet) or {}).get('sign'):
                return 'debilitated'
            if sign in calc.OWN_SIGNS.get(planet, []):
                return 'own_sign'
            return 'neutral'

        def vimshopaka_for(planet):
            total = 0.0
            details = []
            for code, weight in shodashavarga_weights.items():
                pdata = (divisions.get(code) or {}).get(planet)
                if not isinstance(pdata, dict):
                    continue
                sign = int(pdata.get('sign', 0)) % 12
                dignity = varga_dignity(planet, sign)
                lord = SIGN_LORDS[sign]
                if dignity in {'exalted', 'moolatrikona', 'own_sign'}:
                    relation_key, happiness = 'ownOrHigher', 20.0
                elif planet in natal_signs and lord in natal_signs:
                    natural = calc._natural_relationship(planet, lord)
                    temporary = calc._temporary_relationship(natal_signs[planet], natal_signs[lord])
                    compound = calc._compound_relationship(natural, temporary)
                    relation_key = compound['key']
                    happiness = panchadha_points.get(relation_key, 10.0)
                else:
                    relation_key, happiness = 'notGraded', 10.0
                contribution = weight * happiness / 20.0
                total += contribution
                details.append({'varga': code, 'weight': weight, 'sign': sign,
                                'relation': relation_key, 'contribution': round(contribution, 4)})
            return {'score': round(total, 4), 'maximum': 20.0,
                    'scheme': 'shodashavarga', 'details': details,
                    'reference': 'Brihat Parashara Hora Shastra, Shodashavarga chapter, Vimsopaka Bala verses'}
        for name, row in rows.items():
            if name not in {'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'}:
                continue
            repeated = {'exalted': [], 'own_sign': [], 'debilitated': []}
            for code, planets in divisions.items():
                pdata = planets.get(name) if isinstance(planets, dict) else None
                if not isinstance(pdata, dict):
                    continue
                sign = int(pdata.get('sign', 0)) % 12
                dignity = varga_dignity(name, sign)
                if dignity in repeated:
                    repeated[dignity].append(code)
            d9 = d9_planets.get(name) or {}
            d9_sign = d9.get('sign')
            row['varga_strength'] = {
                'd9_sign': d9_sign,
                'd9_sign_name': SIGN_NAMES[d9_sign] if isinstance(d9_sign, int) else None,
                'd9_dignity': calc._dignity_display(name, varga_dignity(name, d9_sign)) if isinstance(d9_sign, int) else None,
                'vargottama': bool(isinstance(d9_sign, int) and d9_sign == row.get('sign')),
                'repetitions': repeated,
                'charts_checked': list(divisions.keys()),
                'vimshopaka_bala': vimshopaka_for(name),
                'vimshopaka_status': 'calculated',
                'method_note': 'Shodashavarga Vimsopaka uses the classical 20-point weights and Panchadha Maitri from D1.',
            }
    except Exception as exc:
        positions['varga_strength_status'] = {'status': 'unavailable', 'reason': str(exc)}

    if not birth_data:
        positions['shadbala_status'] = {'status': 'unavailable', 'reason': 'birthDataRequired'}
        return
    try:
        from calculators.classical_shadbala import calculate_classical_shadbala
        working = deepcopy(chart_data)
        if not working.get('divisions'):
            from calculators.divisional_chart_calculator import DivisionalChartCalculator
            working['divisions'] = DivisionalChartCalculator(working).calculate_all_divisional_charts()
        strength = calculate_classical_shadbala(birth_data, working)
        for name, result in strength.items():
            row = rows.get(name)
            if not row:
                continue
            components = result.get('components') or {}
            strongest = max(components.items(), key=lambda item: item[1]) if components else None
            weakest = min(components.items(), key=lambda item: item[1]) if components else None
            row['shadbala'] = {
                'total_rupas': result.get('total_rupas'),
                'minimum_required_rupas': result.get('minimum_required_rupas'),
                'required_percent': result.get('required_percent'),
                'meets_minimum': result.get('meets_minimum'),
                'strongest_component': {'key': strongest[0], 'virupas': strongest[1]} if strongest else None,
                'weakest_component': {'key': weakest[0], 'virupas': weakest[1]} if weakest else None,
                'method': 'BPHS Shadbala worksheet',
            }
            row['ishta_kashta'] = {
                'ishta_phala': result.get('ishta_phala'),
                'kashta_phala': result.get('kashta_phala'),
                'tendency': result.get('result_tendency'),
                'method': 'Classical Ishta/Kashta Phala from Uccha and Chesta Bala',
            }
        for row in rows.values():
            for dispositor in (row.get('dispositors') or {}).values():
                target = rows.get(dispositor.get('planet')) if isinstance(dispositor, dict) else None
                if not target:
                    continue
                dispositor['shadbala'] = target.get('shadbala')
                dispositor['aspects_received'] = (target.get('aspects') or {}).get('received', [])
        positions['shadbala_status'] = {'status': 'calculated'}
    except Exception as exc:
        positions['shadbala_status'] = {'status': 'unavailable', 'reason': str(exc)}

def _generate_summary(dignities):
    """Generate summary of dignities"""
    summary = {
        'strongest_planets': [],
        'weakest_planets': [],
        'exalted_planets': [],
        'debilitated_planets': [],
        'combust_planets': [],
        'retrograde_planets': []
    }
    
    # Sort planets by strength
    sorted_planets = sorted(dignities.items(), key=lambda x: x[1]['strength_multiplier'], reverse=True)
    
    # Get strongest and weakest
    summary['strongest_planets'] = [p[0] for p in sorted_planets[:3]]
    summary['weakest_planets'] = [p[0] for p in sorted_planets[-3:]]
    
    # Categorize planets
    for planet, info in dignities.items():
        if info['dignity'] == 'exalted':
            summary['exalted_planets'].append(planet)
        elif info['dignity'] == 'debilitated':
            summary['debilitated_planets'].append(planet)
        
        if info['combustion_status'] == 'combust':
            summary['combust_planets'].append(planet)
        
        if info['retrograde']:
            summary['retrograde_planets'].append(planet)
    
    return summary
