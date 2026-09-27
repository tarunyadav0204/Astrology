from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from vedic_predictions.config.planetary_dignity import (
    EXALTATION_DATA, DEBILITATION_DATA, OWN_SIGNS, MOOLATRIKONA_DATA
)
from vedic_predictions.config.functional_nature import (
    FUNCTIONAL_BENEFICS, FUNCTIONAL_MALEFICS, FUNCTIONAL_NEUTRALS
)
from calculators.classical_combustion import calculate_planet_combustion
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
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
        dignities = PlanetaryDignitiesCalculator(chart_data).calculate_planetary_dignities()
        return {
            "dignities": dignities,
            "ascendant_sign": ascendant_sign,
            "summary": _generate_summary(dignities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate dignities: {str(e)}")

def _calculate_dignity(planet, sign, degree=None):
    """Calculate planetary dignity"""
    # Rahu and Ketu don't have traditional dignities
    if planet in ['Rahu', 'Ketu']:
        return _calculate_rahu_ketu_dignity(planet, sign)
    
    # Check exaltation
    if planet in EXALTATION_DATA:
        exalt_data = EXALTATION_DATA[planet]
        if sign == exalt_data['sign']:
            if degree is not None and abs(degree - exalt_data['degree']) <= 5:
                return 'exalted'
            return 'exalted'
    
    # Check debilitation
    if planet in DEBILITATION_DATA:
        debil_data = DEBILITATION_DATA[planet]
        if sign == debil_data['sign']:
            if degree is not None and abs(degree - debil_data['degree']) <= 5:
                return 'debilitated'
            return 'debilitated'
    
    # Check moolatrikona
    if planet in MOOLATRIKONA_DATA:
        mool_data = MOOLATRIKONA_DATA[planet]
        if sign == mool_data['sign']:
            if degree is not None:
                if mool_data['start_degree'] <= degree <= mool_data['end_degree']:
                    return 'moolatrikona'
            else:
                return 'moolatrikona'
    
    # Check own sign
    if planet in OWN_SIGNS:
        if sign in OWN_SIGNS[planet]:
            return 'own_sign'
    
    return 'neutral'

def _calculate_rahu_ketu_dignity(planet, sign):
    """Calculate dignity for Rahu/Ketu based on sign preferences"""
    # Rahu is considered strong in: Gemini, Virgo, Libra, Sagittarius, Pisces
    # Ketu is considered strong in: Sagittarius, Pisces, Scorpio
    
    if planet == 'Rahu':
        if sign in [2, 5, 6, 8, 11]:  # Gemini, Virgo, Libra, Sagittarius, Pisces
            return 'favorable'
        elif sign in [3, 4, 7]:  # Cancer, Leo, Scorpio
            return 'unfavorable'
    elif planet == 'Ketu':
        if sign in [8, 11, 7]:  # Sagittarius, Pisces, Scorpio
            return 'favorable'
        elif sign in [2, 5, 6]:  # Gemini, Virgo, Libra
            return 'unfavorable'
    
    return 'neutral'

def _calculate_functional_nature(planet, ascendant_sign):
    """Calculate functional benefic/malefic nature"""
    if planet in FUNCTIONAL_BENEFICS.get(ascendant_sign, []):
        return 'benefic'
    elif planet in FUNCTIONAL_MALEFICS.get(ascendant_sign, []):
        return 'malefic'
    elif planet in FUNCTIONAL_NEUTRALS.get(ascendant_sign, []):
        return 'neutral'
    else:
        return 'neutral'

def _calculate_combustion(planet, planet_longitude, sun_longitude, retrograde=False):
    """Calculate combustion status"""
    row = calculate_planet_combustion(
        planet,
        {"longitude": planet_longitude, "retrograde": retrograde},
        {"longitude": sun_longitude},
    )
    return "combust" if row["is_combust"] else "normal"

def _calculate_strength_multiplier(dignity_info):
    """Calculate overall strength multiplier (legacy function)"""
    result = _calculate_strength_multiplier_with_breakdown(dignity_info)
    return result['final_multiplier']

def _calculate_strength_multiplier_with_breakdown(dignity_info):
    """Calculate overall strength multiplier with detailed breakdown"""
    breakdown = []
    multiplier = 1.0
    
    # Dignity multiplier
    dignity_multipliers = {
        'exalted': 1.5,
        'moolatrikona': 1.3,
        'own_sign': 1.2,
        'favorable': 1.2,  # For Rahu/Ketu
        'unfavorable': 0.8,  # For Rahu/Ketu
        'debilitated': 0.6
    }
    dignity_mult = dignity_multipliers.get(dignity_info['dignity'], 1.0)
    if dignity_mult != 1.0:
        breakdown.append(f"Dignity ({dignity_info['dignity'].title()}): {dignity_mult}x")
    multiplier *= dignity_mult
    
    # Functional nature multiplier
    functional_multipliers = {
        'benefic': 1.2,
        'malefic': 0.8
    }
    functional_mult = functional_multipliers.get(dignity_info['functional_nature'], 1.0)
    if functional_mult != 1.0:
        breakdown.append(f"Functional ({dignity_info['functional_nature'].title()}): {functional_mult}x")
    multiplier *= functional_mult
    
    # Combustion multiplier
    combustion_multipliers = {}
    combustion_mult = combustion_multipliers.get(dignity_info['combustion_status'], 1.0)
    if combustion_mult != 1.0:
        breakdown.append(f"Combustion ({dignity_info['combustion_status'].title()}): {combustion_mult}x")
    multiplier *= combustion_mult
    
    # Retrograde effect (slight reduction for most planets)
    if dignity_info['retrograde'] and dignity_info['planet'] not in ['Jupiter', 'Venus']:
        breakdown.append(f"Retrograde: 0.9x")
        multiplier *= 0.9
    
    # If no factors, show base
    if not breakdown:
        breakdown.append("Base strength: 1.0x")
    
    return {
        'final_multiplier': round(multiplier, 2),
        'breakdown': breakdown,
        'calculation': ' × '.join([str(dignity_mult), str(functional_mult), str(combustion_mult)] + (['0.9'] if dignity_info['retrograde'] and dignity_info['planet'] not in ['Jupiter', 'Venus'] else []))
    }

def _compile_states(dignity_info):
    """Compile all planetary states"""
    states = []
    
    # Add dignity state
    if dignity_info['dignity'] != 'neutral':
        states.append(dignity_info['dignity'].title())
    
    # Add functional nature
    if dignity_info['functional_nature'] != 'neutral':
        states.append(f"Functional {dignity_info['functional_nature'].title()}")
    
    # Add combustion state
    if dignity_info['combustion_status'] == 'combust':
        states.append('Combust')
    elif dignity_info['combustion_status'] == 'cazimi':
        states.append('Cazimi')
    
    # Add retrograde state
    if dignity_info['retrograde']:
        states.append('Retrograde')
    
    return states

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
