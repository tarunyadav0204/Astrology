# House significations with expanded traditional meanings

HOUSE_SIGNIFICATIONS = {
    1: {
        'name': 'Ascendant/Self',
        'primary': ['self', 'personality', 'health', 'appearance', 'vitality'],
        'body_parts': ['head', 'brain', 'face', 'overall_constitution'],
        'events': ['birth', 'major_life_changes', 'health_issues', 'personality_development']
    },
    2: {
        'name': 'Wealth/Family',
        'primary': ['wealth', 'family', 'speech', 'food', 'savings'],
        'body_parts': ['face', 'eyes', 'ears', 'nose', 'teeth', 'tongue', 'throat'],
        'events': ['financial_gains', 'family_events', 'speech_issues', 'eye_problems', 'dental_issues']
    },
    3: {
        'name': 'Siblings/Courage',
        'primary': ['siblings', 'courage', 'communication', 'short_journeys', 'skills'],
        'body_parts': ['arms', 'hands', 'shoulders', 'chest', 'lungs'],
        'events': ['sibling_relationships', 'communication_opportunities', 'skill_development', 'short_travels']
    },
    4: {
        'name': 'Mother/Home',
        'primary': ['mother', 'home', 'property', 'education', 'happiness', 'vehicles'],
        'body_parts': ['heart', 'chest', 'lungs', 'breasts'],
        'events': ['property_acquisition', 'home_changes', 'mother_health', 'education_completion', 'vehicle_purchase']
    },
    5: {
        'name': 'Children/Creativity',
        'primary': ['children', 'creativity', 'speculation', 'romance', 'intelligence'],
        'body_parts': ['stomach', 'upper_abdomen', 'heart'],
        'events': ['childbirth', 'pregnancy', 'creative_projects', 'romantic_relationships', 'speculation_gains']
    },
    6: {
        'name': 'Enemies/Health',
        'primary': ['enemies', 'diseases', 'service', 'debts', 'obstacles'],
        'body_parts': ['intestines', 'kidney', 'stomach'],
        'events': ['health_recovery', 'job_changes', 'legal_victories', 'debt_clearance', 'enemy_defeat']
    },
    7: {
        'name': 'Marriage/Partnerships',
        'primary': ['marriage', 'spouse', 'partnerships', 'business', 'public_relations'],
        'body_parts': ['reproductive_organs', 'lower_abdomen', 'kidneys'],
        'events': ['marriage', 'engagement', 'business_partnerships', 'spouse_health', 'relationship_changes']
    },
    8: {
        'name': 'Longevity/Transformation',
        'primary': ['longevity', 'occult', 'inheritance', 'transformation', 'research'],
        'body_parts': ['reproductive_organs', 'anus', 'external_genitalia'],
        'events': ['inheritance_gains', 'occult_experiences', 'major_transformations', 'research_breakthroughs']
    },
    9: {
        'name': 'Father/Dharma',
        'primary': ['father', 'dharma', 'higher_learning', 'spirituality', 'long_journeys'],
        'body_parts': ['hips', 'thighs'],
        'events': ['spiritual_awakening', 'higher_education', 'father_health', 'pilgrimage', 'dharmic_activities']
    },
    10: {
        'name': 'Career/Reputation',
        'primary': ['career', 'reputation', 'authority', 'government', 'status'],
        'body_parts': ['knees', 'joints', 'bones'],
        'events': ['career_advancement', 'promotion', 'reputation_changes', 'government_recognition', 'authority_positions']
    },
    11: {
        'name': 'Gains/Friends',
        'primary': ['gains', 'friends', 'elder_siblings', 'hopes', 'aspirations'],
        'body_parts': ['calves', 'ankles', 'left_ear'],
        'events': ['financial_gains', 'friendship_formation', 'goal_achievement', 'elder_sibling_events']
    },
    12: {
        'name': 'Losses/Moksha',
        'primary': ['losses', 'expenses', 'foreign_lands', 'moksha', 'isolation'],
        'body_parts': ['feet', 'left_eye', 'lymphatic_system'],
        'events': ['foreign_travel', 'spiritual_liberation', 'hospital_visits', 'charitable_activities', 'losses']
    }
}

# Planet lordships for signs
SIGN_LORDS = {
    0: 'Mars',      # Aries
    1: 'Venus',     # Taurus  
    2: 'Mercury',   # Gemini
    3: 'Moon',      # Cancer
    4: 'Sun',       # Leo
    5: 'Mercury',   # Virgo
    6: 'Venus',     # Libra
    7: 'Mars',      # Scorpio
    8: 'Jupiter',   # Sagittarius
    9: 'Saturn',    # Capricorn
    10: 'Saturn',   # Aquarius
    11: 'Jupiter'   # Pisces
}

# Natural benefics and malefics
NATURAL_BENEFICS = ['Jupiter', 'Venus', 'Mercury', 'Moon']
NATURAL_MALEFICS = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']

# Exaltation and debilitation signs
EXALTATION_SIGNS = {
    'Sun': 0,       # Aries
    'Moon': 1,      # Taurus
    'Mars': 9,      # Capricorn
    'Mercury': 5,   # Virgo
    'Jupiter': 3,   # Cancer
    'Venus': 11,    # Pisces
    'Saturn': 6     # Libra
}

DEBILITATION_SIGNS = {
    'Sun': 6,       # Libra
    'Moon': 7,      # Scorpio
    'Mars': 3,      # Cancer
    'Mercury': 11,  # Pisces
    'Jupiter': 9,   # Capricorn
    'Venus': 5,     # Virgo
    'Saturn': 0     # Aries
}