# Planetary Dignity Configuration for Enhanced Vedic Analysis

# Exaltation signs and degrees
EXALTATION_DATA = {
    'Sun': {'sign': 0, 'degree': 10},      # Aries 10°
    'Moon': {'sign': 1, 'degree': 3},      # Taurus 3°
    'Mars': {'sign': 9, 'degree': 28},     # Capricorn 28°
    'Mercury': {'sign': 5, 'degree': 15},  # Virgo 15°
    'Jupiter': {'sign': 3, 'degree': 5},   # Cancer 5°
    'Venus': {'sign': 11, 'degree': 27},   # Pisces 27°
    'Saturn': {'sign': 6, 'degree': 20},   # Libra 20°
    'Rahu': {'sign': 2, 'degree': 20},     # Gemini 20°
    'Ketu': {'sign': 8, 'degree': 20}      # Sagittarius 20°
}

# Debilitation signs and degrees (opposite of exaltation)
DEBILITATION_DATA = {
    'Sun': {'sign': 6, 'degree': 10},      # Libra 10°
    'Moon': {'sign': 7, 'degree': 3},      # Scorpio 3°
    'Mars': {'sign': 3, 'degree': 28},     # Cancer 28°
    'Mercury': {'sign': 11, 'degree': 15}, # Pisces 15°
    'Jupiter': {'sign': 9, 'degree': 5},   # Capricorn 5°
    'Venus': {'sign': 5, 'degree': 27},    # Virgo 27°
    'Saturn': {'sign': 0, 'degree': 20},   # Aries 20°
    'Rahu': {'sign': 8, 'degree': 20},     # Sagittarius 20°
    'Ketu': {'sign': 2, 'degree': 20}      # Gemini 20°
}

# Own signs (Swakshetra)
OWN_SIGNS = {
    'Sun': [4],           # Leo
    'Moon': [3],          # Cancer
    'Mars': [0, 7],       # Aries, Scorpio
    'Mercury': [2, 5],    # Gemini, Virgo
    'Jupiter': [8, 11],   # Sagittarius, Pisces
    'Venus': [1, 6],      # Taurus, Libra
    'Saturn': [9, 10]     # Capricorn, Aquarius
}

# Moolatrikona signs and degree ranges
MOOLATRIKONA_DATA = {
    'Sun': {'sign': 4, 'start_degree': 0, 'end_degree': 20},    # Leo 0-20°
    'Moon': {'sign': 1, 'start_degree': 4, 'end_degree': 30},   # Taurus 4-30°
    'Mars': {'sign': 0, 'start_degree': 0, 'end_degree': 12},   # Aries 0-12°
    'Mercury': {'sign': 5, 'start_degree': 16, 'end_degree': 20}, # Virgo 16-20°
    'Jupiter': {'sign': 8, 'start_degree': 0, 'end_degree': 10}, # Sagittarius 0-10°
    'Venus': {'sign': 6, 'start_degree': 0, 'end_degree': 15},   # Libra 0-15°
    'Saturn': {'sign': 10, 'start_degree': 0, 'end_degree': 20}  # Aquarius 0-20°
}

# Planetary friendships (Natural relationships)
NATURAL_FRIENDS = {
    'Sun': ['Moon', 'Mars', 'Jupiter'],
    'Moon': ['Sun', 'Mercury'],
    'Mars': ['Sun', 'Moon', 'Jupiter'],
    'Mercury': ['Sun', 'Venus'],
    'Jupiter': ['Sun', 'Moon', 'Mars'],
    'Venus': ['Mercury', 'Saturn'],
    'Saturn': ['Mercury', 'Venus']
}

NATURAL_ENEMIES = {
    'Sun': ['Venus', 'Saturn'],
    'Moon': ['None'],
    'Mars': ['Mercury'],
    'Mercury': ['Moon'],
    'Jupiter': ['Mercury', 'Venus'],
    'Venus': ['Sun', 'Moon'],
    'Saturn': ['Sun', 'Moon', 'Mars']
}

# Dignity strength multipliers for intensity calculation
DIGNITY_MULTIPLIERS = {
    'exalted': 1.5,
    'moolatrikona': 1.3,
    'own_sign': 1.2,
    'friend_sign': 1.1,
    'neutral_sign': 1.0,
    'enemy_sign': 0.9,
    'debilitated': 0.6
}