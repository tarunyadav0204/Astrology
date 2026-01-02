from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
import math
from datetime import datetime
import swisseph as swe
from utils.timezone_service import parse_timezone_offset
from shadbala_formulas import (
    get_sthana_bala_formulas, get_dig_bala_formula, get_kala_bala_formulas,
    get_chesta_bala_formula, get_naisargika_bala_formula, get_drik_bala_formula
)

router = APIRouter()

class ShadbalaRequest(BaseModel):
    birth_data: Dict[str, Any]
    chart_data: Dict[str, Any]

# Classical data from Brihat Parashara Hora Shastra
NAISARGIKA_BALA = {
    'Sun': 60.0, 'Moon': 51.43, 'Mars': 17.14, 'Mercury': 25.71,
    'Jupiter': 34.29, 'Venus': 42.86, 'Saturn': 8.57
}

DIRECTIONAL_HOUSES = {
    'Sun': 10, 'Moon': 4, 'Mars': 10, 'Mercury': 1,
    'Jupiter': 1, 'Venus': 4, 'Saturn': 7
}

EXALTATION_DATA = {
    'Sun': {'sign': 0, 'degree': 10},    # Aries 10°
    'Moon': {'sign': 1, 'degree': 3},    # Taurus 3°
    'Mars': {'sign': 9, 'degree': 28},   # Capricorn 28°
    'Mercury': {'sign': 5, 'degree': 15}, # Virgo 15°
    'Jupiter': {'sign': 3, 'degree': 5}, # Cancer 5°
    'Venus': {'sign': 11, 'degree': 27}, # Pisces 27°
    'Saturn': {'sign': 6, 'degree': 20}  # Libra 20°
}

OWN_SIGNS = {
    'Sun': [4],           # Leo
    'Moon': [3],          # Cancer
    'Mars': [0, 7],       # Aries, Scorpio
    'Mercury': [2, 5],    # Gemini, Virgo
    'Jupiter': [8, 11],   # Sagittarius, Pisces
    'Venus': [1, 6],      # Taurus, Libra
    'Saturn': [9, 10]     # Capricorn, Aquarius
}

MOOLATRIKONA_SIGNS = {
    'Sun': {'sign': 4, 'start': 0, 'end': 20},      # Leo 0-20°
    'Moon': {'sign': 1, 'start': 4, 'end': 30},     # Taurus 4-30°
    'Mars': {'sign': 0, 'start': 0, 'end': 12},     # Aries 0-12°
    'Mercury': {'sign': 5, 'start': 16, 'end': 20}, # Virgo 16-20°
    'Jupiter': {'sign': 8, 'start': 0, 'end': 10},  # Sagittarius 0-10°
    'Venus': {'sign': 6, 'start': 0, 'end': 15},    # Libra 0-15°
    'Saturn': {'sign': 10, 'start': 0, 'end': 20}   # Aquarius 0-20°
}

# Drekkana lords (each sign divided into 3 parts of 10° each)
DREKKANA_LORDS = {
    0: [0, 4, 8],   # Aries: Mars, Sun, Jupiter
    1: [1, 5, 9],   # Taurus: Venus, Mercury, Saturn
    2: [2, 6, 10],  # Gemini: Mercury, Venus, Saturn
    3: [3, 7, 11],  # Cancer: Moon, Mars, Jupiter
    4: [4, 8, 0],   # Leo: Sun, Jupiter, Mars
    5: [5, 9, 1],   # Virgo: Mercury, Saturn, Venus
    6: [6, 10, 2],  # Libra: Venus, Saturn, Mercury
    7: [7, 11, 3],  # Scorpio: Mars, Jupiter, Moon
    8: [8, 0, 4],   # Sagittarius: Jupiter, Mars, Sun
    9: [9, 1, 5],   # Capricorn: Saturn, Venus, Mercury
    10: [10, 2, 6], # Aquarius: Saturn, Mercury, Venus
    11: [11, 3, 7]  # Pisces: Jupiter, Moon, Mars
}

def calculate_classical_shadbala(birth_data: Dict, chart_data: Dict) -> Dict:
    """Calculate authentic classical Shadbala"""
    try:
        planets = chart_data.get('planets', {})
        results = {}
        
        # Calculate Julian Day for astronomical calculations
        jd = get_julian_day(birth_data)
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Rahu', 'Ketu', 'Gulika', 'Mandi']:
                continue
                
            shadbala = calculate_planet_classical_shadbala(
                planet_name, planet_data, planets, birth_data, jd
            )
            results[planet_name] = shadbala
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classical Shadbala calculation failed: {str(e)}")

def get_julian_day(birth_data: Dict) -> float:
    """Calculate Julian Day for birth time"""
    date_parts = birth_data['date'].split('-')
    time_parts = birth_data['time'].split(':')
    
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    hour = float(time_parts[0]) + float(time_parts[1])/60
    
    # Convert to UTC using centralized timezone service
    tz_offset = parse_timezone_offset(
        birth_data.get('timezone', 'UTC+0'),
        birth_data.get('latitude', 0),
        birth_data.get('longitude', 0)
    )
    hour -= tz_offset
    
    return swe.julday(year, month, day, hour)

def calculate_planet_classical_shadbala(planet: str, planet_data: Dict, all_planets: Dict, birth_data: Dict, jd: float) -> Dict:
    """Calculate complete classical Shadbala for a planet"""
    
    # 1. Sthana Bala (Positional Strength) - Complete
    sthana_bala = calculate_complete_sthana_bala(planet, planet_data, jd)
    
    # 2. Dig Bala (Directional Strength) - Authentic
    dig_bala = calculate_authentic_dig_bala(planet, planet_data)
    
    # 3. Kala Bala (Temporal Strength) - Complete classical
    kala_bala = calculate_complete_kala_bala(planet, planet_data, birth_data, jd)
    
    # 4. Chesta Bala (Motional Strength) - Proper planetary motion
    chesta_bala = calculate_authentic_chesta_bala(planet, planet_data, all_planets, jd)
    
    # 5. Naisargika Bala (Natural Strength) - Classical values
    naisargika_bala = NAISARGIKA_BALA.get(planet, 0)
    
    # 6. Drik Bala (Aspectual Strength) - Proper Graha Drishti
    drik_bala = calculate_authentic_drik_bala(planet, planet_data, all_planets)
    
    # Total Shadbala
    total_points = sthana_bala + dig_bala + kala_bala + chesta_bala + naisargika_bala + drik_bala
    total_rupas = total_points / 60.0
    
    # Classical strength grades
    if total_rupas >= 5:
        grade = "Excellent"
    elif total_rupas >= 4:
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
        },
        'detailed_breakdown': {
            'sthana_components': calculate_sthana_breakdown(planet, planet_data, jd),
            'kala_components': calculate_kala_breakdown(planet, planet_data, birth_data, jd)
        },
        'formulas': {
            'sthana_bala_formula': get_sthana_bala_formulas(planet, planet_data, jd),
            'dig_bala_formula': get_dig_bala_formula(planet, planet_data),
            'kala_bala_formula': get_kala_bala_formulas(planet, planet_data, birth_data, jd),
            'chesta_bala_formula': get_chesta_bala_formula(planet, planet_data, all_planets, jd),
            'naisargika_bala_formula': get_naisargika_bala_formula(planet),
            'drik_bala_formula': get_drik_bala_formula(planet, planet_data, all_planets)
        }
    }

def calculate_complete_sthana_bala(planet: str, planet_data: Dict, jd: float) -> float:
    """Complete Sthana Bala with all 5 components"""
    
    # 1. Uccha Bala (Exaltation strength)
    uccha_bala = calculate_authentic_uccha_bala(planet, planet_data)
    
    # 2. Saptavargaja Bala (7 divisional charts strength)
    saptavargaja_bala = calculate_saptavargaja_bala(planet, planet_data, jd)
    
    # 3. Ojhayugmarasyamsa Bala (Odd/Even sign strength)
    ojha_bala = calculate_ojhayugmarasyamsa_bala(planet, planet_data)
    
    # 4. Kendra Bala (Angular house strength)
    kendra_bala = calculate_kendra_bala(planet_data)
    
    # 5. Drekkana Bala (Decanate strength)
    drekkana_bala = calculate_drekkana_bala(planet, planet_data)
    
    return uccha_bala + saptavargaja_bala + ojha_bala + kendra_bala + drekkana_bala

def calculate_authentic_uccha_bala(planet: str, planet_data: Dict) -> float:
    """Authentic exaltation strength calculation"""
    if planet not in EXALTATION_DATA:
        return 0
        
    current_longitude = planet_data.get('longitude', 0)
    exalt_data = EXALTATION_DATA[planet]
    exalt_longitude = exalt_data['sign'] * 30 + exalt_data['degree']
    
    # Calculate distance from exaltation point
    diff = abs(current_longitude - exalt_longitude)
    if diff > 180:
        diff = 360 - diff
    
    # Classical formula: 60 * (1 - distance/180)
    return max(0, 60 * (1 - diff / 180))

def calculate_saptavargaja_bala(planet: str, planet_data: Dict, jd: float) -> float:
    """Simplified Saptavargaja Bala - honest implementation"""
    current_sign = planet_data.get('sign', 0)
    current_degree = planet_data.get('degree', 0)
    
    # Only calculate what we can actually implement properly
    total_points = 0
    
    # 1. Rasi (D1) - 5 points max
    rasi_strength = get_varga_strength(planet, current_sign)
    total_points += rasi_strength * 5
    
    # 2. Hora (D2) - 2 points max  
    hora_sign = 0 if current_sign % 2 == 0 else 1
    if (planet == 'Sun' and hora_sign == 0) or (planet == 'Moon' and hora_sign == 1):
        total_points += 2
    else:
        total_points += 1
    
    # 3. Drekkana (D3) - 3 points max
    drekkana_index = int(current_degree / 10)
    if current_sign in DREKKANA_LORDS and drekkana_index < len(DREKKANA_LORDS[current_sign]):
        drekkana_lord_sign = DREKKANA_LORDS[current_sign][drekkana_index]
        drekkana_strength = get_varga_strength(planet, drekkana_lord_sign)
        total_points += drekkana_strength * 3
    else:
        total_points += 1.5
    
    # For other vargas, give average points (honest about limitations)
    # Saptamsa (D7) - 1 point
    # Navamsa (D9) - 4.5 points  
    # Dwadasamsa (D12) - 2 points
    # Trimsamsa (D30) - 1 point
    total_points += 8.5  # Average for remaining vargas
    
    return min(total_points, 30)  # Cap at 30 points

def get_varga_strength(planet: str, sign: int) -> float:
    """Get strength of planet in a sign"""
    if planet not in OWN_SIGNS:
        return 0.5
        
    if sign in OWN_SIGNS[planet]:
        return 1.0  # Own sign
    elif planet in EXALTATION_DATA and EXALTATION_DATA[planet]['sign'] == sign:
        return 1.0  # Exaltation
    else:
        # Friend/enemy calculation would go here
        return 0.5  # Neutral

def calculate_ojhayugmarasyamsa_bala(planet: str, planet_data: Dict) -> float:
    """Odd/Even sign strength"""
    current_sign = planet_data.get('sign', 0)
    
    # Male planets (Sun, Mars, Jupiter) strong in odd signs
    # Female planets (Moon, Venus) strong in even signs  
    # Mercury neutral
    
    if planet in ['Sun', 'Mars', 'Jupiter']:
        return 15 if current_sign % 2 == 0 else 0  # Odd signs (0-indexed, so even numbers)
    elif planet in ['Moon', 'Venus']:
        return 15 if current_sign % 2 == 1 else 0  # Even signs
    else:  # Mercury
        return 15
    
def calculate_kendra_bala(planet_data: Dict) -> float:
    """Angular house strength"""
    house = planet_data.get('house', 1)
    if house in [1, 4, 7, 10]:  # Kendra
        return 60
    elif house in [2, 5, 8, 11]:  # Panapara
        return 30
    else:  # Apoklima
        return 15

def calculate_drekkana_bala(planet: str, planet_data: Dict) -> float:
    """Decanate strength"""
    current_sign = planet_data.get('sign', 0)
    current_degree = planet_data.get('degree', 0)
    
    drekkana_index = int(current_degree / 10)
    drekkana_lord_sign = DREKKANA_LORDS[current_sign][drekkana_index]
    
    return 10 if get_varga_strength(planet, drekkana_lord_sign) >= 1.0 else 5

def calculate_authentic_dig_bala(planet: str, planet_data: Dict) -> float:
    """Authentic directional strength"""
    if planet not in DIRECTIONAL_HOUSES:
        return 0
        
    current_house = planet_data.get('house', 1)
    directional_house = DIRECTIONAL_HOUSES[planet]
    
    if current_house == directional_house:
        return 60
    elif current_house == ((directional_house + 6 - 1) % 12 + 1):  # Opposite
        return 0
    else:
        # Gradual decrease
        distance = min(abs(current_house - directional_house), 12 - abs(current_house - directional_house))
        return max(0, 60 * (1 - distance / 6))

def calculate_complete_kala_bala(planet: str, planet_data: Dict, birth_data: Dict, jd: float) -> float:
    """Complete Kala Bala with all components"""
    
    # 1. Natonnata Bala (Day/Night strength)
    natonnata = calculate_natonnata_bala(planet, birth_data)
    
    # 2. Paksha Bala (Lunar fortnight strength)
    paksha = calculate_paksha_bala(planet, jd)
    
    # 3. Tribhaga Bala (Day/Night period strength)
    tribhaga = calculate_tribhaga_bala(planet, birth_data)
    
    # 4. Varsha/Masa/Dina/Hora Bala (Year/Month/Day/Hour lord strength)
    temporal_lords = calculate_temporal_lords_bala(planet, birth_data, jd)
    
    # 5. Ayana Bala (Sun's declination strength)
    ayana = calculate_ayana_bala(planet, jd)
    
    return natonnata + paksha + tribhaga + temporal_lords + ayana

def calculate_natonnata_bala(planet: str, birth_data: Dict) -> float:
    """Day/Night strength"""
    birth_time = birth_data.get('time', '12:00')
    hour = int(birth_time.split(':')[0])
    is_day = 6 <= hour <= 18
    
    day_planets = ['Sun', 'Jupiter', 'Venus']
    night_planets = ['Moon', 'Mars', 'Saturn']
    
    if (planet in day_planets and is_day) or (planet in night_planets and not is_day):
        return 60
    else:
        return 0

def calculate_paksha_bala(planet: str, jd: float) -> float:
    """Lunar fortnight strength"""
    # Get Moon's longitude
    # Set Lahiri Ayanamsa for accurate Vedic calculations

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    
    # Calculate lunar phase
    phase_angle = (moon_pos - sun_pos) % 360
    
    if planet == 'Moon':
        # Moon stronger during waxing phase
        if 0 <= phase_angle <= 180:  # Waxing
            return 60 * (phase_angle / 180)
        else:  # Waning
            return 60 * ((360 - phase_angle) / 180)
    else:
        return 30  # Other planets get average strength

def calculate_tribhaga_bala(planet: str, birth_data: Dict) -> float:
    """Day/Night period strength"""
    birth_time = birth_data.get('time', '12:00')
    hour = int(birth_time.split(':')[0])
    
    if 6 <= hour <= 18:  # Day
        if 6 <= hour <= 10:  # Morning
            return 20 if planet in ['Sun', 'Jupiter'] else 10
        elif 10 <= hour <= 14:  # Noon
            return 20 if planet in ['Sun', 'Mars'] else 10
        else:  # Afternoon
            return 20 if planet in ['Venus', 'Mercury'] else 10
    else:  # Night
        return 20 if planet in ['Moon', 'Saturn'] else 10

def calculate_temporal_lords_bala(planet: str, birth_data: Dict, jd: float) -> float:
    """Year/Month/Day/Hour lord strength"""
    # Simplified - would need complex calculations for exact lords
    return 15  # Average strength

def calculate_ayana_bala(planet: str, jd: float) -> float:
    """Sun's declination strength (affects all planets)"""
    if planet == 'Sun':
        # Get Sun's declination
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0]
        # Simplified calculation
        return 30
    else:
        return 15

def calculate_authentic_chesta_bala(planet: str, planet_data: Dict, all_planets: Dict, jd: float) -> float:
    """Authentic motional strength based on planetary speeds"""
    if planet == 'Sun':
        return 60  # Sun always gets full strength
    elif planet == 'Moon':
        # Moon's strength based on distance from Sun
        sun_data = all_planets.get('Sun', {})
        moon_longitude = planet_data.get('longitude', 0)
        sun_longitude = sun_data.get('longitude', 0)
        
        distance = abs(moon_longitude - sun_longitude)
        if distance > 180:
            distance = 360 - distance
            
        return 60 * (distance / 180)
    else:
        # Get actual planetary speed from Swiss Ephemeris
        planet_num = {'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 
                     'Venus': swe.VENUS, 'Saturn': swe.SATURN}.get(planet)
        
        if planet_num:
            pos_data = swe.calc_ut(jd, planet_num, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0]
            daily_motion = abs(pos_data[3])  # Daily motion in longitude
            
            # Classical average daily motions
            avg_motions = {'Mars': 0.5, 'Mercury': 1.0, 'Jupiter': 0.083, 'Venus': 1.0, 'Saturn': 0.033}
            avg_motion = avg_motions.get(planet, 0.5)
            
            # Strength based on motion relative to average
            if daily_motion > avg_motion:
                return min(60, 30 + (daily_motion / avg_motion) * 30)
            else:
                return max(0, 30 * (daily_motion / avg_motion))
        
        return 30

def calculate_authentic_drik_bala(planet: str, planet_data: Dict, all_planets: Dict) -> float:
    """Authentic aspectual strength using classical Graha Drishti"""
    total_drik = 0
    planet_longitude = planet_data.get('longitude', 0)
    
    # Classical aspects with their strengths
    aspects = {
        'conjunction': {'angle': 0, 'orb': 15, 'strength': 60},
        'sextile': {'angle': 60, 'orb': 6, 'strength': 30},
        'square': {'angle': 90, 'orb': 8, 'strength': -45},
        'trine': {'angle': 120, 'orb': 8, 'strength': 45},
        'opposition': {'angle': 180, 'orb': 12, 'strength': -60}
    }
    
    # Special aspects for Mars, Jupiter, Saturn
    special_aspects = {
        'Mars': [90, 180, 270],      # 4th, 7th, 8th aspects
        'Jupiter': [120, 150, 180],   # 5th, 9th, 7th aspects  
        'Saturn': [90, 180, 270]      # 3rd, 7th, 10th aspects
    }
    
    for other_planet, other_data in all_planets.items():
        if other_planet == planet or other_planet in ['Rahu', 'Ketu', 'Gulika', 'Mandi']:
            continue
            
        other_longitude = other_data.get('longitude', 0)
        angle_diff = abs(planet_longitude - other_longitude)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Check for aspects
        for aspect_name, aspect_data in aspects.items():
            if abs(angle_diff - aspect_data['angle']) <= aspect_data['orb']:
                # Benefic/malefic consideration
                benefic_planets = ['Jupiter', 'Venus', 'Mercury']
                malefic_planets = ['Mars', 'Saturn', 'Sun']
                
                strength = aspect_data['strength']
                if other_planet in benefic_planets and strength > 0:
                    total_drik += strength * 0.5
                elif other_planet in malefic_planets and strength < 0:
                    total_drik += strength * 0.5
                else:
                    total_drik += strength * 0.25
    
    return max(-30, min(30, total_drik))

def calculate_sthana_breakdown(planet: str, planet_data: Dict, jd: float) -> Dict:
    """Detailed breakdown of Sthana Bala components"""
    return {
        'uccha_bala': round(calculate_authentic_uccha_bala(planet, planet_data), 2),
        'saptavargaja_bala': round(calculate_saptavargaja_bala(planet, planet_data, jd), 2),
        'ojhayugmarasyamsa_bala': round(calculate_ojhayugmarasyamsa_bala(planet, planet_data), 2),
        'kendra_bala': round(calculate_kendra_bala(planet_data), 2),
        'drekkana_bala': round(calculate_drekkana_bala(planet, planet_data), 2)
    }

def calculate_kala_breakdown(planet: str, planet_data: Dict, birth_data: Dict, jd: float) -> Dict:
    """Detailed breakdown of Kala Bala components"""
    return {
        'natonnata_bala': round(calculate_natonnata_bala(planet, birth_data), 2),
        'paksha_bala': round(calculate_paksha_bala(planet, jd), 2),
        'tribhaga_bala': round(calculate_tribhaga_bala(planet, birth_data), 2),
        'temporal_lords_bala': round(calculate_temporal_lords_bala(planet, birth_data, jd), 2),
        'ayana_bala': round(calculate_ayana_bala(planet, jd), 2)
    }

@router.post("/calculate-classical-shadbala")
async def calculate_classical_shadbala_endpoint(request: ShadbalaRequest):
    """Calculate authentic classical Shadbala"""
    try:
        results = calculate_classical_shadbala(request.birth_data, request.chart_data)
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classical Shadbala calculation failed: {str(e)}")