# Comprehensive Nakshatra data for Vedic astrology predictions

# 27 Nakshatras with their lords, characteristics, and pada details
NAKSHATRA_DATA = {
    1: {
        'name': 'Ashwini',
        'lord': 'Ketu',
        'deity': 'Ashwini Kumaras',
        'nature': 'Swift, healing, pioneering',
        'element': 'Earth',
        'guna': 'Rajas',
        'animal': 'Horse',
        'symbol': 'Horse head',
        'characteristics': ['Quick action', 'Healing abilities', 'Initiative', 'Restlessness'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    2: {
        'name': 'Bharani',
        'lord': 'Venus',
        'deity': 'Yama',
        'nature': 'Transformative, creative, nurturing',
        'element': 'Earth',
        'guna': 'Rajas',
        'animal': 'Elephant',
        'symbol': 'Yoni',
        'characteristics': ['Creativity', 'Transformation', 'Nurturing', 'Responsibility'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    3: {
        'name': 'Krittika',
        'lord': 'Sun',
        'deity': 'Agni',
        'nature': 'Sharp, cutting, purifying',
        'element': 'Fire',
        'guna': 'Rajas',
        'animal': 'Goat',
        'symbol': 'Razor/Flame',
        'characteristics': ['Sharp intellect', 'Purification', 'Leadership', 'Critical nature'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    4: {
        'name': 'Rohini',
        'lord': 'Moon',
        'deity': 'Brahma',
        'nature': 'Growing, beautiful, material',
        'element': 'Earth',
        'guna': 'Rajas',
        'animal': 'Serpent',
        'symbol': 'Cart/Chariot',
        'characteristics': ['Beauty', 'Growth', 'Material success', 'Attraction'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    5: {
        'name': 'Mrigashira',
        'lord': 'Mars',
        'deity': 'Soma',
        'nature': 'Searching, gentle, curious',
        'element': 'Earth',
        'guna': 'Tamas',
        'animal': 'Deer',
        'symbol': 'Deer head',
        'characteristics': ['Searching nature', 'Gentleness', 'Curiosity', 'Restlessness'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    6: {
        'name': 'Ardra',
        'lord': 'Rahu',
        'deity': 'Rudra',
        'nature': 'Stormy, emotional, transformative',
        'element': 'Water',
        'guna': 'Tamas',
        'animal': 'Dog',
        'symbol': 'Teardrop',
        'characteristics': ['Emotional intensity', 'Transformation', 'Destruction-creation', 'Mental activity'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    7: {
        'name': 'Punarvasu',
        'lord': 'Jupiter',
        'deity': 'Aditi',
        'nature': 'Renewal, return, nurturing',
        'element': 'Water',
        'guna': 'Rajas',
        'animal': 'Cat',
        'symbol': 'Bow and quiver',
        'characteristics': ['Renewal', 'Optimism', 'Nurturing', 'Repetition'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    8: {
        'name': 'Pushya',
        'lord': 'Saturn',
        'deity': 'Brihaspati',
        'nature': 'Nourishing, spiritual, protective',
        'element': 'Water',
        'guna': 'Tamas',
        'animal': 'Goat',
        'symbol': 'Udder of cow',
        'characteristics': ['Nourishment', 'Spirituality', 'Protection', 'Discipline'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    9: {
        'name': 'Ashlesha',
        'lord': 'Mercury',
        'deity': 'Nagas',
        'nature': 'Clinging, mysterious, hypnotic',
        'element': 'Water',
        'guna': 'Tamas',
        'animal': 'Cat',
        'symbol': 'Serpent',
        'characteristics': ['Mystery', 'Hypnotic power', 'Clinging nature', 'Wisdom'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    10: {
        'name': 'Magha',
        'lord': 'Ketu',
        'deity': 'Pitrs',
        'nature': 'Royal, ancestral, authoritative',
        'element': 'Water',
        'guna': 'Tamas',
        'animal': 'Rat',
        'symbol': 'Throne',
        'characteristics': ['Royal nature', 'Ancestral connection', 'Authority', 'Tradition'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    11: {
        'name': 'Purva Phalguni',
        'lord': 'Venus',
        'deity': 'Bhaga',
        'nature': 'Creative, pleasure-loving, artistic',
        'element': 'Water',
        'guna': 'Rajas',
        'animal': 'Rat',
        'symbol': 'Hammock',
        'characteristics': ['Creativity', 'Pleasure', 'Artistic nature', 'Relaxation'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    12: {
        'name': 'Uttara Phalguni',
        'lord': 'Sun',
        'deity': 'Aryaman',
        'nature': 'Generous, helpful, organized',
        'element': 'Fire',
        'guna': 'Rajas',
        'animal': 'Bull',
        'symbol': 'Bed',
        'characteristics': ['Generosity', 'Organization', 'Helpfulness', 'Leadership'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    13: {
        'name': 'Hasta',
        'lord': 'Moon',
        'deity': 'Savitar',
        'nature': 'Skillful, clever, dexterous',
        'element': 'Fire',
        'guna': 'Rajas',
        'animal': 'Buffalo',
        'symbol': 'Hand',
        'characteristics': ['Skill', 'Cleverness', 'Dexterity', 'Craftsmanship'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    14: {
        'name': 'Chitra',
        'lord': 'Mars',
        'deity': 'Vishvakarma',
        'nature': 'Bright, beautiful, creative',
        'element': 'Fire',
        'guna': 'Tamas',
        'animal': 'Tiger',
        'symbol': 'Pearl',
        'characteristics': ['Beauty', 'Creativity', 'Craftsmanship', 'Illusion'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    15: {
        'name': 'Swati',
        'lord': 'Rahu',
        'deity': 'Vayu',
        'nature': 'Independent, flexible, moving',
        'element': 'Fire',
        'guna': 'Tamas',
        'animal': 'Buffalo',
        'symbol': 'Coral',
        'characteristics': ['Independence', 'Flexibility', 'Movement', 'Trade'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    16: {
        'name': 'Vishakha',
        'lord': 'Jupiter',
        'deity': 'Indra-Agni',
        'nature': 'Determined, goal-oriented, ambitious',
        'element': 'Fire',
        'guna': 'Rajas',
        'animal': 'Tiger',
        'symbol': 'Triumphal arch',
        'characteristics': ['Determination', 'Ambition', 'Goal-oriented', 'Achievement'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    17: {
        'name': 'Anuradha',
        'lord': 'Saturn',
        'deity': 'Mitra',
        'nature': 'Friendly, devoted, balanced',
        'element': 'Fire',
        'guna': 'Tamas',
        'animal': 'Deer',
        'symbol': 'Lotus',
        'characteristics': ['Friendship', 'Devotion', 'Balance', 'Cooperation'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    18: {
        'name': 'Jyeshtha',
        'lord': 'Mercury',
        'deity': 'Indra',
        'nature': 'Senior, protective, responsible',
        'element': 'Air',
        'guna': 'Tamas',
        'animal': 'Deer',
        'symbol': 'Earring',
        'characteristics': ['Seniority', 'Protection', 'Responsibility', 'Authority'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    19: {
        'name': 'Mula',
        'lord': 'Ketu',
        'deity': 'Nirriti',
        'nature': 'Root, foundation, investigative',
        'element': 'Air',
        'guna': 'Tamas',
        'animal': 'Dog',
        'symbol': 'Bunch of roots',
        'characteristics': ['Investigation', 'Foundation', 'Destruction', 'Research'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    20: {
        'name': 'Purva Ashadha',
        'lord': 'Venus',
        'deity': 'Apas',
        'nature': 'Invincible, purifying, proud',
        'element': 'Air',
        'guna': 'Rajas',
        'animal': 'Monkey',
        'symbol': 'Fan',
        'characteristics': ['Invincibility', 'Purification', 'Pride', 'Victory'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    21: {
        'name': 'Uttara Ashadha',
        'lord': 'Sun',
        'deity': 'Vishvedevas',
        'nature': 'Final victory, leadership, universal',
        'element': 'Air',
        'guna': 'Rajas',
        'animal': 'Mongoose',
        'symbol': 'Elephant tusk',
        'characteristics': ['Final victory', 'Leadership', 'Universal approach', 'Righteousness'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    22: {
        'name': 'Shravana',
        'lord': 'Moon',
        'deity': 'Vishnu',
        'nature': 'Listening, learning, connecting',
        'element': 'Air',
        'guna': 'Rajas',
        'animal': 'Monkey',
        'symbol': 'Ear',
        'characteristics': ['Listening', 'Learning', 'Connection', 'Knowledge'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    23: {
        'name': 'Dhanishtha',
        'lord': 'Mars',
        'deity': 'Vasus',
        'nature': 'Wealthy, musical, rhythmic',
        'element': 'Ether',
        'guna': 'Tamas',
        'animal': 'Lion',
        'symbol': 'Drum',
        'characteristics': ['Wealth', 'Music', 'Rhythm', 'Fame'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    24: {
        'name': 'Shatabhisha',
        'lord': 'Rahu',
        'deity': 'Varuna',
        'nature': 'Healing, mysterious, independent',
        'element': 'Ether',
        'guna': 'Tamas',
        'animal': 'Horse',
        'symbol': 'Empty circle',
        'characteristics': ['Healing', 'Mystery', 'Independence', 'Research'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    },
    25: {
        'name': 'Purva Bhadrapada',
        'lord': 'Jupiter',
        'deity': 'Aja Ekapada',
        'nature': 'Passionate, transformative, spiritual',
        'element': 'Ether',
        'guna': 'Rajas',
        'animal': 'Lion',
        'symbol': 'Sword',
        'characteristics': ['Passion', 'Transformation', 'Spirituality', 'Intensity'],
        'pada_lords': ['Mars', 'Venus', 'Mercury', 'Moon']
    },
    26: {
        'name': 'Uttara Bhadrapada',
        'lord': 'Saturn',
        'deity': 'Ahir Budhnya',
        'nature': 'Deep, mystical, stable',
        'element': 'Ether',
        'guna': 'Tamas',
        'animal': 'Cow',
        'symbol': 'Snake',
        'characteristics': ['Depth', 'Mysticism', 'Stability', 'Wisdom'],
        'pada_lords': ['Sun', 'Mercury', 'Venus', 'Mars']
    },
    27: {
        'name': 'Revati',
        'lord': 'Mercury',
        'deity': 'Pushan',
        'nature': 'Nourishing, protective, guiding',
        'element': 'Ether',
        'guna': 'Tamas',
        'animal': 'Elephant',
        'symbol': 'Fish',
        'characteristics': ['Nourishment', 'Protection', 'Guidance', 'Completion'],
        'pada_lords': ['Jupiter', 'Saturn', 'Saturn', 'Jupiter']
    }
}

# Nakshatra compatibility matrix (1=excellent, 0.75=good, 0.5=neutral, 0.25=difficult, 0=incompatible)
NAKSHATRA_COMPATIBILITY = {
    # Simplified compatibility based on traditional Vedic principles
    'same_lord': 0.75,      # Same nakshatra lord
    'friendly_lords': 0.75,  # Friendly nakshatra lords
    'neutral_lords': 0.5,    # Neutral nakshatra lords
    'enemy_lords': 0.25,     # Enemy nakshatra lords
    'same_nakshatra': 1.0,   # Same nakshatra
    'trine_nakshatras': 0.75, # 5th and 9th from each other
    'opposite_nakshatras': 0.25 # 7th from each other (can be challenging)
}

# Planetary friendships for nakshatra lord compatibility
PLANETARY_RELATIONSHIPS = {
    'Sun': {'friends': ['Moon', 'Mars', 'Jupiter'], 'enemies': ['Venus', 'Saturn'], 'neutral': ['Mercury']},
    'Moon': {'friends': ['Sun', 'Mercury'], 'enemies': [], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn']},
    'Mars': {'friends': ['Sun', 'Moon', 'Jupiter'], 'enemies': ['Mercury'], 'neutral': ['Venus', 'Saturn']},
    'Mercury': {'friends': ['Sun', 'Venus'], 'enemies': ['Moon'], 'neutral': ['Mars', 'Jupiter', 'Saturn']},
    'Jupiter': {'friends': ['Sun', 'Moon', 'Mars'], 'enemies': ['Mercury', 'Venus'], 'neutral': ['Saturn']},
    'Venus': {'friends': ['Mercury', 'Saturn'], 'enemies': ['Sun', 'Moon'], 'neutral': ['Mars', 'Jupiter']},
    'Saturn': {'friends': ['Mercury', 'Venus'], 'enemies': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
    'Rahu': {'friends': ['Venus', 'Saturn'], 'enemies': ['Sun', 'Moon', 'Mars'], 'neutral': ['Mercury', 'Jupiter']},
    'Ketu': {'friends': ['Mars', 'Jupiter'], 'enemies': ['Sun', 'Moon'], 'neutral': ['Mercury', 'Venus', 'Saturn']}
}

# Nakshatra pada characteristics and timing
PADA_CHARACTERISTICS = {
    1: {'element': 'Fire', 'nature': 'Initiative, beginning, action'},
    2: {'element': 'Earth', 'nature': 'Stability, material, practical'},
    3: {'element': 'Air', 'nature': 'Communication, movement, flexibility'},
    4: {'element': 'Water', 'nature': 'Emotion, intuition, completion'}
}