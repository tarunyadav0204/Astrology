from typing import Dict, List
from datetime import datetime

def format_degree(longitude: float) -> str:
    """Format longitude to degrees, minutes, seconds"""
    degrees = int(longitude)
    minutes = int((longitude - degrees) * 60)
    seconds = int(((longitude - degrees) * 60 - minutes) * 60)
    return f"{degrees}°{minutes:02d}'{seconds:02d}\""

def get_sign_name(longitude: float) -> str:
    """Get zodiac sign name from longitude"""
    signs = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]
    sign_index = int(longitude / 30)
    return signs[sign_index % 12]

def format_planet_position(planet_name: str, longitude: float) -> str:
    """Format planet position for display"""
    degree_in_sign = longitude % 30
    sign = get_sign_name(longitude)
    formatted_degree = format_degree(degree_in_sign)
    return f"{formatted_degree} {sign}"

def calculate_aspect_strength_score(orb: float, aspect_type: str) -> int:
    """Calculate numerical strength score for aspect"""
    base_scores = {
        'CONJUNCTION': 10,
        'OPPOSITION': 8,
        'TRINE': 9,
        'SQUARE': 7,
        'SEXTILE': 6
    }
    
    base_score = base_scores.get(aspect_type, 5)
    
    # Reduce score based on orb
    if orb <= 1:
        return base_score
    elif orb <= 2:
        return base_score - 1
    elif orb <= 4:
        return base_score - 2
    else:
        return base_score - 3

def is_date_in_past(date_str: str) -> bool:
    """Check if date string is in the past"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    return date < datetime.now()

def format_timeline_period(period: Dict) -> str:
    """Format timeline period for display"""
    start = period['start_date']
    end = period['end_date']
    
    if start == end:
        return start
    else:
        return f"{start} to {end}"