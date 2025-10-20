# Combustion Configuration for Vedic Astrology

# Combustion thresholds (degrees from Sun)
COMBUSTION_THRESHOLDS = {
    'Moon': 12,      # Within 12 degrees
    'Mars': 17,      # Within 17 degrees  
    'Mercury': 14,   # Within 14 degrees (but can be cazimi)
    'Jupiter': 11,   # Within 11 degrees
    'Venus': 10,     # Within 10 degrees (but can be cazimi)
    'Saturn': 15,    # Within 15 degrees
    'Rahu': 5,       # Within 5 degrees
    'Ketu': 5        # Within 5 degrees
}

# Cazimi (heart of Sun) - exact conjunction within 1 degree
CAZIMI_THRESHOLD = 1

# Combustion effects on planetary strength
COMBUSTION_MULTIPLIERS = {
    'combust': 0.3,     # Severely weakened
    'cazimi': 1.8,      # Empowered by Sun
    'normal': 1.0       # No combustion effect
}

# Planets that can be cazimi (empowered when very close to Sun)
CAZIMI_CAPABLE = ['Mercury', 'Venus']