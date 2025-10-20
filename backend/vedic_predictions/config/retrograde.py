# Retrograde Motion Configuration for Vedic Astrology

# Retrograde effects on planetary strength
RETROGRADE_MULTIPLIERS = {
    'retrograde': 1.2,      # Enhanced introspective power
    'stationary': 1.5,      # Maximum intensity at direction change
    'direct': 1.0           # Normal motion
}

# Planets that can go retrograde (excluding Sun and Moon)
RETROGRADE_CAPABLE = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

# Planets that never go retrograde
NEVER_RETROGRADE = ['Sun', 'Moon']

# Vakri Gati (retrograde) significations - different meanings when retrograde
RETROGRADE_SIGNIFICATIONS = {
    'Mars': {
        'enhanced': ['past karma resolution', 'inner strength', 'strategic thinking'],
        'modified': ['delayed action', 'internal conflicts', 'revisiting battles']
    },
    'Mercury': {
        'enhanced': ['deep analysis', 'research abilities', 'introspection'],
        'modified': ['communication delays', 'technology issues', 'contract revisions']
    },
    'Jupiter': {
        'enhanced': ['spiritual wisdom', 'inner guidance', 'philosophical depth'],
        'modified': ['delayed blessings', 'questioning beliefs', 'teacher-student role reversal']
    },
    'Venus': {
        'enhanced': ['artistic refinement', 'relationship healing', 'value reassessment'],
        'modified': ['relationship reviews', 'financial reconsiderations', 'beauty standards shift']
    },
    'Saturn': {
        'enhanced': ['karmic lessons', 'structural rebuilding', 'patience development'],
        'modified': ['delayed results', 'authority challenges', 'responsibility reviews']
    },
    'Rahu': {
        'enhanced': ['past-life insights', 'unconventional wisdom', 'breaking patterns'],
        'modified': ['confusion amplified', 'illusion deepening', 'obsession intensified']
    },
    'Ketu': {
        'enhanced': ['spiritual detachment', 'moksha pursuit', 'past mastery'],
        'modified': ['isolation tendencies', 'material disinterest', 'completion focus']
    }
}

# Stationary periods - when planets are changing direction (most powerful)
STATIONARY_ORB = 1.0  # Degrees of apparent motion per day to consider stationary