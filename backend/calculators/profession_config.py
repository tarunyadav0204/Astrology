# Career Analysis Configuration
# All constants and mappings for profession analysis

# Nature of Work Categories
WORK_NATURE_CATEGORIES = {
    'leadership': 'Managing people and organizations',
    'creative': 'Artistic, design, innovation work', 
    'technical': 'Engineering, analysis, problem-solving',
    'administrative': 'Systems, processes, compliance',
    'service': 'Helping, healing, supporting others',
    'spiritual': 'Teaching, counseling, research',
    'trade': 'Business, sales, commerce'
}

# Planetary Work Nature Mapping
PLANETARY_WORK_NATURE = {
    'Sun': ['leadership'],
    'Moon': ['service'],
    'Mars': ['technical'],
    'Mercury': ['administrative'],
    'Jupiter': ['spiritual'],
    'Venus': ['creative'],
    'Saturn': ['administrative'],
    'Rahu': ['technical', 'creative', 'trade'],
    'Ketu': ['spiritual', 'technical'],
    'Gulika': ['administrative', 'service']
}

# Modern Profession Domains
PLANETARY_DOMAINS = {
    'Sun': {
        'traditional': ['Government', 'Politics', 'Administration', 'Leadership roles', 'Public service'],
        'modern': ['Executive leadership', 'Government tech', 'Public policy', 'Corporate governance']
    },
    'Moon': {
        'traditional': ['Healthcare', 'Hospitality', 'Food industry', 'Public relations', 'Nursing'],
        'modern': ['Healthcare tech', 'User experience', 'Social media', 'Customer service', 'Wellness apps']
    },
    'Mars': {
        'traditional': ['Military', 'Police', 'Engineering', 'Sports', 'Surgery', 'Real estate'],
        'modern': ['Cybersecurity', 'Gaming', 'Robotics', 'Competitive programming', 'Hardware engineering']
    },
    'Mercury': {
        'traditional': ['Writing', 'Teaching', 'Accounting', 'Trade', 'Communication'],
        'modern': ['Programming', 'Data science', 'Digital marketing', 'Content creation', 'Analytics', 'Algorithms']
    },
    'Jupiter': {
        'traditional': ['Teaching', 'Law', 'Finance', 'Consulting', 'Religious work', 'Philosophy'],
        'modern': ['Tech leadership', 'AI ethics', 'Educational technology', 'Fintech', 'Legal tech']
    },
    'Venus': {
        'traditional': ['Arts', 'Design', 'Fashion', 'Beauty', 'Entertainment', 'Luxury goods'],
        'modern': ['UI/UX design', 'Creative coding', 'Digital arts', 'Game design', 'Brand design']
    },
    'Saturn': {
        'traditional': ['Construction', 'Mining', 'Agriculture', 'Manufacturing', 'Quality control'],
        'modern': ['System administration', 'Database management', 'Infrastructure', 'DevOps', 'Quality assurance']
    },
    'Rahu': {
        'traditional': ['Foreign trade', 'Aviation', 'Media', 'Unconventional fields'],
        'modern': ['Artificial Intelligence', 'Machine Learning', 'Blockchain', 'Quantum computing', 'Innovation']
    },
    'Ketu': {
        'traditional': ['Research', 'Spirituality', 'Occult sciences', 'Psychology', 'Investigation'],
        'modern': ['Research & Development', 'Algorithm research', 'Data mining', 'Academic research']
    },
    'Gulika': {
        'traditional': ['Toxicology', 'Waste management', 'Security', 'Crisis management'],
        'modern': ['Cybersecurity', 'Risk management', 'Information security', 'Crisis tech']
    }
}

# AI/CS Specific Combinations
AI_CS_COMBINATIONS = {
    ('Mercury', 'Rahu'): {
        'fields': ['Artificial Intelligence', 'Machine Learning', 'Data Science', 'Algorithm Development'],
        'domains': ['Technology', 'Research'],
        'nature': 'technical',
        'description': 'Perfect for AI/ML - combines analytical thinking with innovative technology'
    },
    ('Mercury', 'Saturn'): {
        'fields': ['Systems Programming', 'Database Management', 'Infrastructure', 'Backend Development'],
        'domains': ['Technology', 'Administration'],
        'nature': 'technical',
        'description': 'Structured analytical work in computing systems'
    },
    ('Mercury', 'Ketu'): {
        'fields': ['Research in CS', 'Algorithm Research', 'Academic Computing', 'Deep Learning Research'],
        'domains': ['Research', 'Education'],
        'nature': 'technical',
        'description': 'Deep analytical research in computer science'
    },
    ('Mercury', 'Jupiter'): {
        'fields': ['AI Ethics', 'Educational Technology', 'Tech Leadership', 'Knowledge Systems'],
        'domains': ['Education', 'Technology'],
        'nature': 'leadership',
        'description': 'Wisdom applied to technology and computing'
    },
    ('Mercury', 'Mars'): {
        'fields': ['Cybersecurity', 'Competitive Programming', 'Gaming', 'Real-time Systems'],
        'domains': ['Technology', 'Defense'],
        'nature': 'technical',
        'description': 'Aggressive problem-solving in computing'
    },
    ('Mercury', 'Venus'): {
        'fields': ['UI/UX Design', 'Creative Coding', 'Game Development', 'Digital Arts'],
        'domains': ['Arts', 'Technology'],
        'nature': 'creative',
        'description': 'Creative application of computing and design'
    }
}

# Sign Influence on Work Nature
SIGN_WORK_INFLUENCE = {
    'Aries': {'adds': 'leadership', 'modifies': 'pioneering approach'},
    'Taurus': {'adds': 'administrative', 'modifies': 'steady persistence'},
    'Gemini': {'adds': 'trade', 'modifies': 'versatile communication'},
    'Cancer': {'adds': 'service', 'modifies': 'protective nurturing'},
    'Leo': {'adds': 'leadership', 'modifies': 'creative authority'},
    'Virgo': {'adds': 'administrative', 'modifies': 'analytical perfection'},
    'Libra': {'adds': 'creative', 'modifies': 'diplomatic balance'},
    'Scorpio': {'adds': 'technical', 'modifies': 'transformative intensity'},
    'Sagittarius': {'adds': 'spiritual', 'modifies': 'philosophical expansion'},
    'Capricorn': {'adds': 'administrative', 'modifies': 'structured achievement'},
    'Aquarius': {'adds': 'technical', 'modifies': 'innovative service'},
    'Pisces': {'adds': 'spiritual', 'modifies': 'intuitive compassion'}
}

# House Influence on Work Nature
HOUSE_WORK_INFLUENCE = {
    1: {'nature': 'leadership', 'context': 'personal identity through work'},
    2: {'nature': 'administrative', 'context': 'wealth building focus'},
    3: {'nature': 'creative', 'context': 'communication and skills'},
    4: {'nature': 'spiritual', 'context': 'emotional security through work'},
    5: {'nature': 'leadership', 'context': 'self-expression and creativity'},
    6: {'nature': 'administrative', 'context': 'service and problem-solving'},
    7: {'nature': 'creative', 'context': 'partnerships and public relations'},
    8: {'nature': 'spiritual', 'context': 'research and transformation'},
    9: {'nature': 'leadership', 'context': 'higher learning and philosophy'},
    10: {'nature': 'administrative', 'context': 'public recognition and authority'},
    11: {'nature': 'creative', 'context': 'networks and aspirations'},
    12: {'nature': 'spiritual', 'context': 'foreign lands and letting go'}
}

# Conjunction Effects on Work Nature
CONJUNCTION_WORK_EFFECTS = {
    'Jupiter': {'adds': 'spiritual', 'effect': 'brings wisdom and ethics'},
    'Venus': {'adds': 'creative', 'effect': 'adds artistic and aesthetic elements'},
    'Saturn': {'adds': 'administrative', 'effect': 'brings structure and discipline'},
    'Mars': {'adds': 'technical', 'effect': 'adds energy and problem-solving'},
    'Ketu': {'adds': 'spiritual', 'effect': 'brings research and detachment'},
    'Rahu': {'adds': 'technical', 'effect': 'brings innovation and unconventional approaches'},
    'Mercury': {'adds': 'administrative', 'effect': 'enhances analytical abilities'},
    'Sun': {'adds': 'leadership', 'effect': 'brings authority and recognition'},
    'Moon': {'adds': 'service', 'effect': 'adds emotional connection and public appeal'},
    'Gulika': {'adds': 'administrative', 'effect': 'brings challenges requiring systematic solutions'}
}

# Nakshatra Work Nature (sample - can be expanded)
NAKSHATRA_WORK_NATURE = {
    'Ashwini': 'technical',
    'Bharani': 'creative', 
    'Krittika': 'technical',
    'Rohini': 'creative',
    'Mrigashira': 'technical',
    'Ardra': 'technical',
    'Punarvasu': 'spiritual',
    'Pushya': 'service',
    'Ashlesha': 'administrative',
    'Magha': 'leadership',
    'Purva Phalguni': 'creative',
    'Uttara Phalguni': 'service',
    'Hasta': 'technical',
    'Chitra': 'creative',
    'Swati': 'trade',
    'Vishakha': 'leadership',
    'Anuradha': 'spiritual',
    'Jyeshtha': 'leadership',
    'Mula': 'spiritual',
    'Purva Ashadha': 'creative',
    'Uttara Ashadha': 'leadership',
    'Shravana': 'service',
    'Dhanishta': 'technical',
    'Shatabhisha': 'technical',
    'Purva Bhadrapada': 'spiritual',
    'Uttara Bhadrapada': 'spiritual',
    'Revati': 'service'
}

# House Multipliers
HOUSE_MULTIPLIERS = {
    'kendra': 1.2,    # 1,4,7,10 - Angular houses
    'trikona': 1.15,  # 1,5,9 - Trinal houses  
    'upachaya': 1.1,  # 3,6,10,11 - Growth houses
    'dusthana': 0.85  # 6,8,12 - Difficult houses
}

# Sign Elements
SIGN_ELEMENTS = {
    'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
    'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
    'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
    'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
}

# Element Work Natures
ELEMENT_WORK_NATURES = {
    'fire': 'leadership',
    'earth': 'administrative',
    'air': 'creative',
    'water': 'service'
}

# Nakshatra Rulers
NAKSHATRA_RULERS = {
    'Ashwini': 'Ketu', 'Bharani': 'Venus', 'Krittika': 'Sun', 'Rohini': 'Moon',
    'Mrigashira': 'Mars', 'Ardra': 'Rahu', 'Punarvasu': 'Jupiter', 'Pushya': 'Saturn',
    'Ashlesha': 'Mercury', 'Magha': 'Ketu', 'Purva Phalguni': 'Venus', 'Uttara Phalguni': 'Sun',
    'Hasta': 'Moon', 'Chitra': 'Mars', 'Swati': 'Rahu', 'Vishakha': 'Jupiter',
    'Anuradha': 'Saturn', 'Jyeshtha': 'Mercury', 'Mula': 'Ketu', 'Purva Ashadha': 'Venus',
    'Uttara Ashadha': 'Sun', 'Shravana': 'Moon', 'Dhanishta': 'Mars', 'Shatabhisha': 'Rahu',
    'Purva Bhadrapada': 'Jupiter', 'Uttara Bhadrapada': 'Saturn', 'Revati': 'Mercury'
}