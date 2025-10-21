from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from vedic_predictions.config.planetary_dignity import (
    EXALTATION_DATA, DEBILITATION_DATA, OWN_SIGNS, MOOLATRIKONA_DATA
)
from vedic_predictions.config.functional_nature import (
    FUNCTIONAL_BENEFICS, FUNCTIONAL_MALEFICS, FUNCTIONAL_NEUTRALS
)
from vedic_predictions.config.combustion import COMBUSTION_THRESHOLDS, CAZIMI_THRESHOLD, CAZIMI_CAPABLE
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
        birth_data = request.get('birth_data', {})
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        planets = chart_data['planets']
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        
        dignities = {}
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Gulika', 'Mandi']:
                continue
                
            planet_sign = planet_data.get('sign', 0)
            planet_degree = planet_data.get('degree', 0)
            planet_longitude = planet_data.get('longitude', 0)
            is_retrograde = planet_data.get('retrograde', False)
            
            dignity_info = {
                'planet': planet_name,
                'sign': planet_sign,
                'degree': round(planet_degree, 2),
                'dignity': 'neutral',
                'functional_nature': 'neutral',
                'combustion_status': 'normal',
                'retrograde': is_retrograde,
                'strength_multiplier': 1.0,
                'states': []
            }
            
            # Calculate dignity
            dignity_info['dignity'] = _calculate_dignity(planet_name, planet_sign, planet_degree)
            
            # Calculate functional nature based on ascendant
            dignity_info['functional_nature'] = _calculate_functional_nature(planet_name, ascendant_sign)
            
            # Calculate combustion status
            if planet_name != 'Sun' and 'Sun' in planets:
                sun_longitude = planets['Sun'].get('longitude', 0)
                dignity_info['combustion_status'] = _calculate_combustion(planet_name, planet_longitude, sun_longitude)
            
            # Calculate strength multiplier with breakdown
            strength_result = _calculate_strength_multiplier_with_breakdown(dignity_info)
            dignity_info['strength_multiplier'] = strength_result['final_multiplier']
            dignity_info['strength_breakdown'] = strength_result['breakdown']
            
            # Compile states
            dignity_info['states'] = _compile_states(dignity_info)
            
            dignities[planet_name] = dignity_info
        
        return {
            "dignities": dignities,
            "ascendant_sign": ascendant_sign,
            "summary": _generate_summary(dignities)
        }
        
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

def _calculate_combustion(planet, planet_longitude, sun_longitude):
    """Calculate combustion status"""
    if planet not in COMBUSTION_THRESHOLDS:
        return 'normal'
    
    # Calculate angular distance
    angular_distance = abs(planet_longitude - sun_longitude)
    if angular_distance > 180:
        angular_distance = 360 - angular_distance
    
    threshold = COMBUSTION_THRESHOLDS[planet]
    
    # Check cazimi (heart of Sun)
    if planet in CAZIMI_CAPABLE and angular_distance <= CAZIMI_THRESHOLD:
        return 'cazimi'
    
    # Check combustion
    if angular_distance <= threshold:
        return 'combust'
    
    return 'normal'

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
    combustion_multipliers = {
        'cazimi': 1.8,
        'combust': 0.3
    }
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