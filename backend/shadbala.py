from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
import math

router = APIRouter()

class ShadbalaRequest(BaseModel):
    birth_data: Dict[str, Any]
    chart_data: Dict[str, Any]

# Natural strengths (Naisargika Bala) in points
NATURAL_STRENGTHS = {
    'Sun': 60.0,
    'Moon': 51.43,
    'Mars': 17.14,
    'Mercury': 25.71,
    'Jupiter': 34.29,
    'Venus': 42.86,
    'Saturn': 8.57
}

# Directional strength houses (Dig Bala)
DIRECTIONAL_HOUSES = {
    'Sun': 10, 'Moon': 4, 'Mars': 10, 'Mercury': 1,
    'Jupiter': 1, 'Venus': 4, 'Saturn': 7
}

# Exaltation degrees
EXALTATION_DATA = {
    'Sun': {'sign': 1, 'degree': 10},    # Aries 10°
    'Moon': {'sign': 2, 'degree': 3},    # Taurus 3°
    'Mars': {'sign': 10, 'degree': 28},  # Capricorn 28°
    'Mercury': {'sign': 6, 'degree': 15}, # Virgo 15°
    'Jupiter': {'sign': 4, 'degree': 5}, # Cancer 5°
    'Venus': {'sign': 12, 'degree': 27}, # Pisces 27°
    'Saturn': {'sign': 7, 'degree': 20}  # Libra 20°
}

def calculate_shadbala(birth_data: Dict, chart_data: Dict) -> Dict:
    """Calculate complete Shadbala for all planets"""
    try:
        planets = chart_data.get('planets', {})
        results = {}
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Rahu', 'Ketu']:
                continue
                
            shadbala = calculate_planet_shadbala(planet_name, planet_data, planets, birth_data)
            results[planet_name] = shadbala
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shadbala calculation failed: {str(e)}")

def calculate_planet_shadbala(planet: str, planet_data: Dict, all_planets: Dict, birth_data: Dict) -> Dict:
    """Calculate six-fold strength for a planet"""
    
    # 1. Sthana Bala (Positional Strength)
    sthana_bala = calculate_sthana_bala(planet, planet_data)
    
    # 2. Dig Bala (Directional Strength)  
    dig_bala = calculate_dig_bala(planet, planet_data)
    
    # 3. Kala Bala (Temporal Strength)
    kala_bala = calculate_kala_bala(planet, planet_data, birth_data)
    
    # 4. Chesta Bala (Motional Strength)
    chesta_bala = calculate_chesta_bala(planet, planet_data, all_planets)
    
    # 5. Naisargika Bala (Natural Strength)
    naisargika_bala = NATURAL_STRENGTHS.get(planet, 0)
    
    # 6. Drik Bala (Aspectual Strength)
    drik_bala = calculate_drik_bala(planet, planet_data, all_planets)
    
    # Total Shadbala
    total_points = sthana_bala + dig_bala + kala_bala + chesta_bala + naisargika_bala + drik_bala
    total_rupas = total_points / 60.0
    
    # Strength grade (adjusted for more realistic Vedic standards)
    if total_rupas >= 6:
        grade = "Excellent"
    elif total_rupas >= 4.5:
        grade = "Good"
    elif total_rupas >= 3:
        grade = "Average"
    else:
        grade = "Weak"
    
    return {
        'total_points': round(total_points, 2),
        'total_rupas': round(total_rupas, 2),
        'grade': grade,
        'components': {
            'sthana_bala': round(sthana_bala, 2),
            'dig_bala': round(dig_bala, 2),
            'kala_bala': round(kala_bala, 2),
            'chesta_bala': round(chesta_bala, 2),
            'naisargika_bala': round(naisargika_bala, 2),
            'drik_bala': round(drik_bala, 2)
        }
    }

def calculate_sthana_bala(planet: str, planet_data: Dict) -> float:
    """Calculate positional strength"""
    uccha_bala = calculate_uccha_bala(planet, planet_data)
    kendra_bala = calculate_kendra_bala(planet_data)
    
    # Add Saptavargaja Bala (simplified - own sign bonus)
    own_sign_bonus = 0
    current_sign = planet_data.get('sign', 0)
    
    # Own sign rulerships (0-indexed)
    own_signs = {
        'Sun': [4],      # Leo
        'Moon': [3],     # Cancer  
        'Mars': [0, 7],  # Aries, Scorpio
        'Mercury': [2, 5], # Gemini, Virgo
        'Jupiter': [8, 11], # Sagittarius, Pisces
        'Venus': [1, 6],   # Taurus, Libra
        'Saturn': [9, 10]  # Capricorn, Aquarius
    }
    
    if planet in own_signs and current_sign in own_signs[planet]:
        own_sign_bonus = 30
    
    return uccha_bala + kendra_bala + own_sign_bonus

def calculate_uccha_bala(planet: str, planet_data: Dict) -> float:
    """Calculate exaltation strength (0-60 points)"""
    if planet not in EXALTATION_DATA:
        return 30  # Neutral strength for planets without exaltation
        
    current_longitude = planet_data.get('longitude', 0)
    
    exalt_data = EXALTATION_DATA[planet]
    exalt_longitude = (exalt_data['sign'] - 1) * 30 + exalt_data['degree']
    
    # Calculate angular distance from exaltation point
    diff = abs(current_longitude - exalt_longitude)
    if diff > 180:
        diff = 360 - diff
    
    # Vedic formula: Maximum 60 at exaltation, 0 at debilitation (180° away)
    strength = 60 * (1 - diff / 180)
    return max(0, strength)

def calculate_kendra_bala(planet_data: Dict) -> float:
    """Calculate angular house strength"""
    house = planet_data.get('house', 1)
    if house in [1, 4, 7, 10]:  # Kendra (Angular) houses
        return 60
    elif house in [2, 5, 8, 11]:  # Panapara (Succedent) houses  
        return 30
    else:  # Apoklima (Cadent) houses [3, 6, 9, 12]
        return 15

def calculate_dig_bala(planet: str, planet_data: Dict) -> float:
    """Calculate directional strength"""
    if planet not in DIRECTIONAL_HOUSES:
        return 30  # Neutral strength
        
    current_house = planet_data.get('house', 1)
    directional_house = DIRECTIONAL_HOUSES[planet]
    
    if current_house == directional_house:
        return 60  # Full strength in own direction
    elif current_house == ((directional_house + 6 - 1) % 12 + 1):  # Opposite house (7th from)
        return 0   # No strength in opposite direction
    else:
        # Gradual decrease based on house distance
        distance = min(abs(current_house - directional_house), 12 - abs(current_house - directional_house))
        return max(15, 60 * (1 - distance / 6))  # Minimum 15 points

def calculate_kala_bala(planet: str, planet_data: Dict, birth_data: Dict) -> float:
    """Calculate temporal strength"""
    total_kala_bala = 0
    
    # Natonnata Bala (Day/Night strength)
    birth_time = birth_data.get('time', '12:00')
    hour = int(birth_time.split(':')[0])
    is_day = 6 <= hour <= 18
    
    day_planets = ['Sun', 'Jupiter', 'Venus']
    night_planets = ['Moon', 'Mars', 'Saturn']
    
    if (planet in day_planets and is_day) or (planet in night_planets and not is_day):
        total_kala_bala += 60
    else:
        total_kala_bala += 0
    
    # Paksha Bala (for Moon only - waxing/waning strength)
    if planet == 'Moon':
        # This is a simplified version - full calculation needs lunar phase
        total_kala_bala += 30  # Average strength
    
    # Tribhaga Bala (Day/Night period strength)
    if is_day:
        if hour < 10:  # Morning
            morning_planets = ['Sun', 'Jupiter']
            if planet in morning_planets:
                total_kala_bala += 20
        elif hour < 14:  # Noon
            noon_planets = ['Sun', 'Mars']
            if planet in noon_planets:
                total_kala_bala += 20
        else:  # Afternoon
            afternoon_planets = ['Venus', 'Mercury']
            if planet in afternoon_planets:
                total_kala_bala += 20
    else:  # Night
        night_strength_planets = ['Moon', 'Saturn']
        if planet in night_strength_planets:
            total_kala_bala += 20
    
    return min(total_kala_bala, 60)  # Cap at 60

def calculate_chesta_bala(planet: str, planet_data: Dict, all_planets: Dict) -> float:
    """Calculate motional strength"""
    if planet == 'Sun':
        return 60  # Sun always gets full Chesta Bala
    elif planet == 'Moon':
        # Moon's strength based on distance from Sun (Paksha Bala component)
        sun_data = all_planets.get('Sun', {})
        moon_longitude = planet_data.get('longitude', 0)
        sun_longitude = sun_data.get('longitude', 0)
        
        distance = abs(moon_longitude - sun_longitude)
        if distance > 180:
            distance = 360 - distance
            
        # Maximum at Full Moon (180°), minimum at New Moon (0°)
        return 60 * (distance / 180)
    else:
        # For other planets, retrograde planets get maximum strength
        is_retrograde = planet_data.get('retrograde', False)
        return 60 if is_retrograde else 15  # Lower base for direct motion

def calculate_drik_bala(planet: str, planet_data: Dict, all_planets: Dict) -> float:
    """Calculate aspectual strength (simplified)"""
    # This is a simplified version - full calculation requires complex aspect analysis
    house = planet_data.get('house', 1)
    strength = 0
    
    # Check for benefic/malefic influences (simplified)
    benefics = ['Jupiter', 'Venus', 'Mercury']
    malefics = ['Mars', 'Saturn', 'Sun']
    
    for other_planet, other_data in all_planets.items():
        if other_planet == planet:
            continue
            
        other_house = other_data.get('house', 1)
        
        # Simple aspect check (7th house opposition)
        if abs(house - other_house) == 6 or (house + other_house) == 13:
            if other_planet in benefics:
                strength += 10
            elif other_planet in malefics:
                strength -= 10
                
    return max(-30, min(30, strength))

@router.post("/calculate-shadbala")
async def calculate_shadbala_endpoint(request: ShadbalaRequest):
    """Calculate Shadbala for all planets"""
    try:
        results = calculate_shadbala(request.birth_data, request.chart_data)
        
        # Sort by total strength
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['total_rupas'], reverse=True))
        
        return {
            "shadbala": sorted_results,
            "summary": {
                "strongest": max(results.items(), key=lambda x: x[1]['total_rupas']),
                "weakest": min(results.items(), key=lambda x: x[1]['total_rupas'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shadbala calculation failed: {str(e)}")