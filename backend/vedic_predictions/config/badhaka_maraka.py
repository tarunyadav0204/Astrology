# Badhaka and Maraka Configuration

# Rasi types classification
CHARA_RASIS = [0, 3, 6, 9]      # Aries, Cancer, Libra, Capricorn (Movable)
STHIRA_RASIS = [1, 4, 7, 10]    # Taurus, Leo, Scorpio, Aquarius (Fixed)
DWISWABHAVA_RASIS = [2, 5, 8, 11]  # Gemini, Virgo, Sagittarius, Pisces (Dual)

# Badhaka house calculation by rasi type
BADHAKA_HOUSES = {
    'chara': 11,        # 11th house for movable signs
    'sthira': 9,        # 9th house for fixed signs
    'dwiswabhava': 7    # 7th house for dual signs
}

# Maraka houses (universal for all rasi types)
PRIMARY_MARAKA_HOUSES = [2, 7]      # 2nd and 7th houses
SECONDARY_MARAKA_HOUSES = [12]      # 12th house (sometimes 8th)

# Effect multipliers
BADHAKA_MULTIPLIER = 0.7    # Creates obstacles and delays
MARAKA_MULTIPLIER = 0.5     # Life-threatening, major endings

# Badhaka effects by rasi type
BADHAKA_EFFECTS = {
    'chara': {
        'nature': 'adaptable obstacles',
        'description': 'Obstacles that can be overcome through movement and change',
        'remedies': ['travel', 'change of location', 'dynamic action']
    },
    'sthira': {
        'nature': 'persistent obstacles', 
        'description': 'Stubborn obstacles requiring steady persistent effort',
        'remedies': ['patience', 'consistent effort', 'structural changes']
    },
    'dwiswabhava': {
        'nature': 'fluctuating obstacles',
        'description': 'Variable obstacles requiring flexible approaches',
        'remedies': ['adaptability', 'multiple strategies', 'timing awareness']
    }
}

# Maraka effects (universal)
MARAKA_EFFECTS = {
    'primary': {
        'houses': [2, 7],
        'description': 'Life-threatening, major endings, health risks',
        'remedies': ['life protection mantras', 'health precautions', 'avoid risks']
    },
    'secondary': {
        'houses': [12],
        'description': 'Loss, separation, spiritual transformation',
        'remedies': ['spiritual practices', 'charity', 'letting go']
    }
}