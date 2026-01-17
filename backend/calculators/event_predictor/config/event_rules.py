"""
Event Rules Configuration
Maps houses to life events and defines event types
"""

# House-to-Life-Area Mappings
HOUSE_SIGNIFICATIONS = {
    1: {
        'primary': ['health', 'vitality', 'personality', 'appearance'],
        'events': ['health_improvement', 'personality_change', 'new_beginning', 'self_realization']
    },
    2: {
        'primary': ['wealth', 'family', 'speech', 'food', 'savings'],
        'events': ['wealth_gain', 'family_expansion', 'financial_windfall', 'asset_acquisition']
    },
    3: {
        'primary': ['siblings', 'courage', 'short_travel', 'communication', 'skills'],
        'events': ['sibling_event', 'skill_development', 'short_journey', 'communication_success']
    },
    4: {
        'primary': ['mother', 'home', 'property', 'education', 'vehicles', 'happiness'],
        'events': ['property_acquisition', 'vehicle_purchase', 'home_change', 'mother_related', 'education_completion']
    },
    5: {
        'primary': ['children', 'intelligence', 'creativity', 'romance', 'speculation', 'education'],
        'events': ['childbirth', 'romance', 'creative_success', 'speculation_gain', 'exam_success', 'pregnancy']
    },
    6: {
        'primary': ['enemies', 'disease', 'debts', 'competition', 'service', 'obstacles'],
        'events': ['disease', 'enemy_defeat', 'debt_clearance', 'competition_victory', 'litigation', 'job_service']
    },
    7: {
        'primary': ['marriage', 'partnership', 'spouse', 'business', 'travel'],
        'events': ['marriage', 'engagement', 'partnership', 'business_deal', 'foreign_travel', 'relationship']
    },
    8: {
        'primary': ['longevity', 'transformation', 'occult', 'inheritance', 'accidents', 'research'],
        'events': ['inheritance', 'transformation', 'occult_knowledge', 'accident', 'surgery', 'research_breakthrough']
    },
    9: {
        'primary': ['father', 'fortune', 'dharma', 'higher_education', 'long_travel', 'spirituality'],
        'events': ['father_related', 'fortune_change', 'pilgrimage', 'higher_education', 'spiritual_awakening', 'foreign_settlement']
    },
    10: {
        'primary': ['career', 'profession', 'status', 'authority', 'government', 'reputation'],
        'events': ['promotion', 'job_change', 'career_success', 'recognition', 'government_favor', 'business_growth']
    },
    11: {
        'primary': ['gains', 'income', 'fulfillment', 'friends', 'elder_sibling', 'achievements'],
        'events': ['income_increase', 'goal_achievement', 'friendship', 'elder_sibling_event', 'wish_fulfillment']
    },
    12: {
        'primary': ['loss', 'expenses', 'foreign', 'moksha', 'isolation', 'hospitalization'],
        'events': ['foreign_travel', 'spiritual_retreat', 'hospitalization', 'loss', 'expense', 'isolation', 'moksha']
    }
}

# Event Type Definitions with Required Houses
EVENT_TYPES = {
    'marriage': {
        'primary_houses': [7],
        'supporting_houses': [2, 11],  # 2nd for family, 11th for fulfillment
        'blocking_houses': [6, 8, 12],  # Dusthanas
        'required_planets': ['Venus'],
        'description': 'Marriage or committed partnership'
    },
    'childbirth': {
        'primary_houses': [5],
        'supporting_houses': [1, 9],  # 1st for self, 9th for fortune
        'blocking_houses': [6, 8],
        'required_planets': ['Jupiter'],
        'description': 'Birth of child'
    },
    'career_promotion': {
        'primary_houses': [10],
        'supporting_houses': [1, 6, 11],  # 1st for self, 6th for service, 11th for gains
        'blocking_houses': [8, 12],
        'required_planets': ['Sun', 'Saturn', 'Jupiter'],
        'description': 'Career advancement or promotion'
    },
    'job_change': {
        'primary_houses': [10],
        'supporting_houses': [1, 3, 6],  # 1st for self, 3rd for change, 6th for service
        'blocking_houses': [],
        'required_planets': ['Sun', 'Saturn'],
        'description': 'Change in employment'
    },
    'property_acquisition': {
        'primary_houses': [4],
        'supporting_houses': [2, 11],  # 2nd for wealth, 11th for gains
        'blocking_houses': [6, 8, 12],
        'required_planets': ['Mars', 'Venus'],
        'description': 'Purchase of property or vehicle'
    },
    'wealth_gain': {
        'primary_houses': [2, 11],
        'supporting_houses': [9],  # 9th for fortune
        'blocking_houses': [6, 8, 12],
        'required_planets': ['Jupiter', 'Venus'],
        'description': 'Significant financial gain'
    },
    'education_success': {
        'primary_houses': [4, 5],
        'supporting_houses': [9, 11],  # 9th for higher education, 11th for achievement
        'blocking_houses': [6, 8],
        'required_planets': ['Mercury', 'Jupiter'],
        'description': 'Academic achievement or admission'
    },
    'foreign_travel': {
        'primary_houses': [9, 12],
        'supporting_houses': [3, 7],  # 3rd for travel, 7th for foreign
        'blocking_houses': [],
        'required_planets': ['Rahu', 'Moon'],
        'description': 'Travel abroad or foreign settlement'
    },
    'health_issue': {
        'primary_houses': [6, 8],
        'supporting_houses': [1, 12],  # 1st for body, 12th for hospitalization
        'blocking_houses': [],
        'required_planets': ['Mars', 'Saturn'],
        'description': 'Health problem or disease',
        'negative': True
    },
    'litigation': {
        'primary_houses': [6],
        'supporting_houses': [8, 12],
        'blocking_houses': [],
        'required_planets': ['Mars', 'Saturn'],
        'description': 'Legal disputes or court cases',
        'negative': True
    },
    'spiritual_awakening': {
        'primary_houses': [9, 12],
        'supporting_houses': [5, 8],  # 5th for intelligence, 8th for occult
        'blocking_houses': [],
        'required_planets': ['Jupiter', 'Ketu'],
        'description': 'Spiritual growth or religious activity'
    },
    'business_success': {
        'primary_houses': [7, 10],
        'supporting_houses': [2, 11],
        'blocking_houses': [6, 8, 12],
        'required_planets': ['Mercury', 'Jupiter'],
        'description': 'Business growth or partnership success'
    }
}

# Age-Based Event Priorities (Desha Kala Patra)
AGE_PRIORITIES = {
    'student': {  # Age < 23
        'age_range': (0, 22),
        'priority_events': ['education_success', 'skill_development', 'exam_success'],
        'house_emphasis': [4, 5, 9, 11],  # Education houses
        'suppressed_events': ['marriage', 'childbirth', 'career_promotion']
    },
    'young_professional': {  # Age 23-35
        'age_range': (23, 35),
        'priority_events': ['career_promotion', 'job_change', 'marriage', 'property_acquisition'],
        'house_emphasis': [7, 10, 11, 4],
        'suppressed_events': []
    },
    'established': {  # Age 36-55
        'age_range': (36, 55),
        'priority_events': ['wealth_gain', 'business_success', 'childbirth', 'property_acquisition'],
        'house_emphasis': [2, 5, 10, 11],
        'suppressed_events': ['education_success']
    },
    'senior': {  # Age 56+
        'age_range': (56, 100),
        'priority_events': ['spiritual_awakening', 'health_issue', 'foreign_travel'],
        'house_emphasis': [9, 12, 1, 8],
        'suppressed_events': ['childbirth', 'education_success', 'career_promotion']
    }
}
