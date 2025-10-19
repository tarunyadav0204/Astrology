# Nadi Astrology Configuration
# All configurable variables for easy maintenance

NADI_CONFIG = {
    # Aspect orb tolerances in degrees
    'ASPECT_ORBS': {
        'TIGHT': 3,      # ±3° very strong influence
        'MEDIUM': 8,     # ±8° strong influence  
        'WIDE': 15       # ±15° moderate influence
    },
    
    # Time range for aspect timeline calculation
    'TIME_RANGE': {
        'PAST_YEARS': 5,     # Look back 5 years
        'FUTURE_YEARS': 10   # Look ahead 10 years
    },
    
    # Vedic planetary aspects (degrees from natal position)
    'VEDIC_ASPECTS': {
        'Sun': [30, 120, 150],  # 2nd, 5th, 6th houses
        'Moon': [30, 60, 90, 120, 150, 180],  # All aspects
        'Mars': [120, 210, 240],  # 4th, 8th, 9th houses  
        'Mercury': [30, 60, 90, 120, 150, 180],  # All aspects
        'Jupiter': [150, 180, 240],  # 5th, 7th, 9th houses
        'Venus': [30, 60, 90, 120, 150, 180],  # All aspects
        'Saturn': [90, 210, 240],  # 3rd, 7th, 10th houses
        'Rahu': [150, 180, 240],  # 5th, 7th, 9th houses
        'Ketu': [150, 180, 240]   # 5th, 7th, 9th houses
    },
    
    # Aspect strength scoring
    'ASPECT_STRENGTH': {
        'VERY_STRONG': {'min_score': 8, 'color': '#00ff00'},
        'STRONG': {'min_score': 6, 'color': '#90ee90'},
        'MODERATE': {'min_score': 4, 'color': '#ffff00'},
        'WEAK': {'min_score': 2, 'color': '#ffa500'},
        'VERY_WEAK': {'min_score': 0, 'color': '#ff0000'}
    },
    
    # Planets to include in Nadi analysis
    'NADI_PLANETS': [
        'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 
        'Venus', 'Saturn', 'Rahu', 'Ketu'
    ],
    
    # Transit calculation settings
    'TRANSIT_SETTINGS': {
        'CALCULATION_STEP_DAYS': 1,  # Check every day
        'MIN_DURATION_DAYS': 3       # Minimum aspect duration
    }
}