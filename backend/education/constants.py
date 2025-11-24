"""
Education Analysis Constants
Classical Vedic Astrology Rules and Weights
"""

# House significance for education
EDUCATION_HOUSES = {
    4: {
        'name': 'Foundation Education',
        'description': 'Primary education, schooling, basic learning foundation, graduation',
        'weight': 0.35
    },
    5: {
        'name': 'Intelligence & Performance', 
        'description': 'Learning ability, creativity, academic performance, competitive exams',
        'weight': 0.40
    },
    9: {
        'name': 'Higher Education',
        'description': 'University studies, advanced degrees, research, foreign education',
        'weight': 0.25
    }
}

# Key planets for education
EDUCATION_PLANETS = {
    'Mercury': {
        'significance': 'Learning capacity, communication, analytical thinking',
        'weight': 0.30
    },
    'Jupiter': {
        'significance': 'Wisdom, higher knowledge, teaching ability, academic success',
        'weight': 0.25
    },
    'Moon': {
        'significance': 'Memory, retention, emotional intelligence',
        'weight': 0.15
    },
    'Sun': {
        'significance': 'Confidence, leadership in academics, government education',
        'weight': 0.10
    }
}

# Educational yoga strength mapping (now handled by yoga_calculator)
EDUCATION_YOGA_STRENGTHS = {
    'saraswati yoga': 85,
    'budh-aditya yoga': 75,
    'education lord yoga': 80,
    'guru-mangal yoga': 70,
    'gaja kesari yoga': 75
}

# Strength calculation weights
STRENGTH_WEIGHTS = {
    'house_strength': 0.40,
    'planetary_dignities': 0.30,
    'yogas': 0.20,
    'ashtakavarga': 0.10
}

# House strength sub-weights
HOUSE_STRENGTH_WEIGHTS = {
    4: 0.35,  # Foundation education
    5: 0.40,  # Intelligence
    9: 0.25   # Higher education
}

# Planetary dignity scores
DIGNITY_SCORES = {
    'exalted': 100,
    'moolatrikona': 85,
    'own_sign': 80,
    'favorable': 75,
    'neutral': 50,
    'unfavorable': 35,
    'debilitated': 20
}

# Functional nature multipliers
FUNCTIONAL_MULTIPLIERS = {
    'benefic': 1.2,
    'neutral': 1.0,
    'malefic': 0.8
}

# Combustion effects
COMBUSTION_EFFECTS = {
    'cazimi': 1.5,
    'normal': 1.0,
    'combust': 0.4
}

# Ashtakavarga thresholds
ASHTAKAVARGA_THRESHOLDS = {
    'excellent': 30,
    'good': 28,
    'average': 25,
    'weak': 22
}

# Grade mapping
GRADE_MAPPING = {
    90: 'A+',
    80: 'A',
    70: 'B+',
    60: 'B',
    50: 'C+',
    40: 'C',
    30: 'D',
    0: 'F'
}

# Subject recommendations based on planetary strengths
SUBJECT_RECOMMENDATIONS = {
    'Mercury': ['Mathematics', 'Commerce', 'Communication', 'Computer Science', 'Accounting'],
    'Jupiter': ['Philosophy', 'Law', 'Teaching', 'Theology', 'Management'],
    'Mars': ['Engineering', 'Military Science', 'Sports', 'Surgery', 'Technology'],
    'Venus': ['Arts', 'Music', 'Fashion', 'Interior Design', 'Hospitality'],
    'Saturn': ['Research', 'History', 'Archaeology', 'Mining', 'Agriculture'],
    'Sun': ['Government Studies', 'Political Science', 'Administration', 'Leadership'],
    'Moon': ['Psychology', 'Nursing', 'Hospitality', 'Public Relations', 'Counseling']
}

# Timing indicators
TIMING_FACTORS = {
    'mahadasha': 'Primary period of house lord or education planets',
    'antardasha': 'Sub-period activation',
    'transit': 'Jupiter/Saturn transits through education houses',
    'annual': 'Favorable planetary returns and aspects'
}