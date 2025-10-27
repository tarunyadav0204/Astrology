from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import swisseph as swe

class NakshatraCareerAnalyzer:
    """Analyzes career aspects based on key nakshatras"""
    
    NAKSHATRA_CONFIG = {
        'Ashwini': {
            'lord': 'Ketu',
            'career_nature': 'Pioneer and Initiator',
            'work_style': 'Quick action, healing professions',
            'suitable_fields': ['Medicine', 'Emergency services', 'Sports', 'Transportation', 'Veterinary'],
            'leadership_style': 'Pioneering leader',
            'work_environment': 'Fast-paced, dynamic'
        },
        'Bharani': {
            'lord': 'Venus',
            'career_nature': 'Creative and Transformative',
            'work_style': 'Artistic, nurturing, transformational',
            'suitable_fields': ['Arts', 'Entertainment', 'Fashion', 'Beauty', 'Psychology', 'Counseling'],
            'leadership_style': 'Nurturing guide',
            'work_environment': 'Creative, supportive'
        },
        'Krittika': {
            'lord': 'Sun',
            'career_nature': 'Sharp and Decisive',
            'work_style': 'Cutting-edge, precise, authoritative',
            'suitable_fields': ['Engineering', 'Surgery', 'Military', 'Law enforcement', 'Criticism', 'Research'],
            'leadership_style': 'Authoritative commander',
            'work_environment': 'Structured, disciplined'
        },
        'Rohini': {
            'lord': 'Moon',
            'career_nature': 'Creative and Attractive',
            'work_style': 'Artistic, beautiful, growth-oriented',
            'suitable_fields': ['Arts', 'Agriculture', 'Fashion', 'Beauty', 'Real estate', 'Banking'],
            'leadership_style': 'Inspiring motivator',
            'work_environment': 'Beautiful, harmonious'
        },
        'Mrigashira': {
            'lord': 'Mars',
            'career_nature': 'Seeker and Explorer',
            'work_style': 'Research-oriented, curious, traveling',
            'suitable_fields': ['Research', 'Travel', 'Exploration', 'Investigation', 'Journalism', 'Teaching'],
            'leadership_style': 'Curious explorer',
            'work_environment': 'Varied, exploratory'
        },
        'Ardra': {
            'lord': 'Rahu',
            'career_nature': 'Transformer and Innovator',
            'work_style': 'Destructive-creative, innovative, intense',
            'suitable_fields': ['Technology', 'Research', 'Psychology', 'Occult sciences', 'Weather forecasting'],
            'leadership_style': 'Revolutionary change agent',
            'work_environment': 'Intense, transformative'
        },
        'Punarvasu': {
            'lord': 'Jupiter',
            'career_nature': 'Restorer and Teacher',
            'work_style': 'Repetitive excellence, teaching, nurturing',
            'suitable_fields': ['Education', 'Publishing', 'Real estate', 'Import-export', 'Hospitality'],
            'leadership_style': 'Wise mentor',
            'work_environment': 'Educational, nurturing'
        },
        'Pushya': {
            'lord': 'Saturn',
            'career_nature': 'Nurturer and Provider',
            'work_style': 'Service-oriented, disciplined, caring',
            'suitable_fields': ['Healthcare', 'Social work', 'Government', 'Agriculture', 'Dairy', 'Nutrition'],
            'leadership_style': 'Caring provider',
            'work_environment': 'Service-oriented, stable'
        },
        'Ashlesha': {
            'lord': 'Mercury',
            'career_nature': 'Mystical and Strategic',
            'work_style': 'Secretive, strategic, psychological',
            'suitable_fields': ['Psychology', 'Occult', 'Intelligence', 'Medicine', 'Toxicology', 'Research'],
            'leadership_style': 'Strategic manipulator',
            'work_environment': 'Private, secretive'
        },
        'Magha': {
            'lord': 'Ketu',
            'career_nature': 'Royal and Authoritative',
            'work_style': 'Regal, traditional, ancestral',
            'suitable_fields': ['Government', 'Politics', 'Archaeology', 'History', 'Genealogy', 'Museums'],
            'leadership_style': 'Royal commander',
            'work_environment': 'Traditional, prestigious'
        },
        'Purva Phalguni': {
            'lord': 'Venus',
            'career_nature': 'Creative and Luxurious',
            'work_style': 'Artistic, luxurious, relaxed',
            'suitable_fields': ['Arts', 'Entertainment', 'Luxury goods', 'Hotels', 'Recreation', 'Music'],
            'leadership_style': 'Charismatic entertainer',
            'work_environment': 'Luxurious, creative'
        },
        'Uttara Phalguni': {
            'lord': 'Sun',
            'career_nature': 'Generous and Organized',
            'work_style': 'Organized, helpful, systematic',
            'suitable_fields': ['Management', 'Organization', 'Social work', 'Banking', 'Administration'],
            'leadership_style': 'Organized administrator',
            'work_environment': 'Well-organized, helpful'
        },
        'Hasta': {
            'lord': 'Moon',
            'career_nature': 'Skillful and Crafty',
            'work_style': 'Hands-on, skillful, detailed',
            'suitable_fields': ['Handicrafts', 'Healing', 'Massage', 'Pottery', 'Sculpture', 'Manual arts'],
            'leadership_style': 'Skillful craftsperson',
            'work_environment': 'Hands-on, detailed'
        },
        'Chitra': {
            'lord': 'Mars',
            'career_nature': 'Artistic and Architectural',
            'work_style': 'Creative, architectural, beautiful',
            'suitable_fields': ['Architecture', 'Design', 'Fashion', 'Jewelry', 'Photography', 'Engineering'],
            'leadership_style': 'Creative architect',
            'work_environment': 'Artistic, beautiful'
        },
        'Swati': {
            'lord': 'Rahu',
            'career_nature': 'Independent and Flexible',
            'work_style': 'Independent, flexible, business-minded',
            'suitable_fields': ['Business', 'Trade', 'Diplomacy', 'Consulting', 'Freelancing', 'Aviation'],
            'leadership_style': 'Independent entrepreneur',
            'work_environment': 'Flexible, independent'
        },
        'Vishakha': {
            'lord': 'Jupiter',
            'career_nature': 'Goal-oriented and Ambitious',
            'work_style': 'Ambitious, goal-focused, competitive',
            'suitable_fields': ['Politics', 'Law', 'Competition', 'Sports', 'Sales', 'Achievement-based roles'],
            'leadership_style': 'Ambitious achiever',
            'work_environment': 'Competitive, goal-oriented'
        },
        'Anuradha': {
            'lord': 'Saturn',
            'career_nature': 'Devoted and Organized',
            'work_style': 'Devoted, organized, group-oriented',
            'suitable_fields': ['Organization', 'Group work', 'Religion', 'Social causes', 'Mathematics', 'Science'],
            'leadership_style': 'Devoted organizer',
            'work_environment': 'Group-oriented, organized'
        },
        'Jyeshtha': {
            'lord': 'Mercury',
            'career_nature': 'Senior and Protective',
            'work_style': 'Protective, senior, responsible',
            'suitable_fields': ['Security', 'Protection', 'Senior management', 'Occult', 'Investigation', 'Military'],
            'leadership_style': 'Protective elder',
            'work_environment': 'Responsible, protective'
        },
        'Mula': {
            'lord': 'Ketu',
            'career_nature': 'Root-level and Investigative',
            'work_style': 'Deep investigation, root causes, research',
            'suitable_fields': ['Research', 'Investigation', 'Medicine', 'Pharmacy', 'Occult', 'Spirituality'],
            'leadership_style': 'Deep investigator',
            'work_environment': 'Research-oriented, deep'
        },
        'Purva Ashadha': {
            'lord': 'Venus',
            'career_nature': 'Invincible and Artistic',
            'work_style': 'Invincible spirit, artistic, water-related',
            'suitable_fields': ['Arts', 'Water sports', 'Navy', 'Shipping', 'Liquids', 'Purification'],
            'leadership_style': 'Invincible warrior',
            'work_environment': 'Artistic, water-related'
        },
        'Uttara Ashadha': {
            'lord': 'Sun',
            'career_nature': 'Final Victory and Leadership',
            'work_style': 'Ultimate victory, leadership, permanent',
            'suitable_fields': ['Leadership', 'Government', 'Law', 'Administration', 'Permanent positions'],
            'leadership_style': 'Ultimate leader',
            'work_environment': 'Leadership-focused, permanent'
        },
        'Shravana': {
            'lord': 'Moon',
            'career_nature': 'Learning and Communication',
            'work_style': 'Learning, listening, communication',
            'suitable_fields': ['Education', 'Media', 'Communication', 'Music', 'Languages', 'Information'],
            'leadership_style': 'Wise communicator',
            'work_environment': 'Communication-rich, learning'
        },
        'Dhanishtha': {
            'lord': 'Mars',
            'career_nature': 'Wealthy and Musical',
            'work_style': 'Wealth creation, musical, rhythmic',
            'suitable_fields': ['Music', 'Dance', 'Finance', 'Real estate', 'Percussion', 'Rhythm-based work'],
            'leadership_style': 'Wealthy performer',
            'work_environment': 'Musical, wealth-oriented'
        },
        'Shatabhisha': {
            'lord': 'Rahu',
            'career_nature': 'Healing and Mystical',
            'work_style': 'Healing, mystical, secretive',
            'suitable_fields': ['Medicine', 'Healing', 'Research', 'Astronomy', 'Astrology', 'Alternative medicine'],
            'leadership_style': 'Mystical healer',
            'work_environment': 'Healing-oriented, mystical'
        },
        'Purva Bhadrapada': {
            'lord': 'Jupiter',
            'career_nature': 'Transformative and Spiritual',
            'work_style': 'Transformative, spiritual, intense',
            'suitable_fields': ['Spirituality', 'Occult', 'Transformation', 'Psychology', 'Funeral services', 'Research'],
            'leadership_style': 'Transformative guide',
            'work_environment': 'Spiritual, transformative'
        },
        'Uttara Bhadrapada': {
            'lord': 'Saturn',
            'career_nature': 'Deep and Mystical',
            'work_style': 'Deep wisdom, mystical, patient',
            'suitable_fields': ['Spirituality', 'Deep research', 'Mysticism', 'Meditation', 'Philosophy', 'Counseling'],
            'leadership_style': 'Wise mystic',
            'work_environment': 'Deep, mystical'
        },
        'Revati': {
            'lord': 'Mercury',
            'career_nature': 'Nourishing and Protective',
            'work_style': 'Nourishing, protective, guiding',
            'suitable_fields': ['Guidance', 'Protection', 'Travel', 'Transportation', 'Hospitality', 'Care services'],
            'leadership_style': 'Protective guide',
            'work_environment': 'Nurturing, protective'
        }
    }
    
    DASHA_PERIODS = {
        'Ketu': 7,
        'Venus': 20,
        'Sun': 6,
        'Moon': 10,
        'Mars': 7,
        'Rahu': 18,
        'Jupiter': 16,
        'Saturn': 19,
        'Mercury': 17
    }
    
    def __init__(self, chart_data: Dict[str, Any]):
        self.chart_data = chart_data
        self.planets = chart_data.get('planets', {})
        
    def get_nakshatra_from_longitude(self, longitude: float) -> str:
        """Get nakshatra name from longitude"""
        nakshatra_names = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        
        # Each nakshatra is 13°20' (800 minutes)
        nakshatra_index = int(longitude * 60 / 800)
        return nakshatra_names[nakshatra_index % 27]
    
    def get_key_career_nakshatras(self) -> Dict[str, Dict[str, Any]]:
        """Get key nakshatras for career analysis"""
        key_nakshatras = {}
        
        # Get ascendant longitude first
        ascendant_longitude = self.chart_data.get('ascendant', 0)
        if isinstance(ascendant_longitude, dict):
            ascendant_longitude = ascendant_longitude.get('longitude', 0)
        
        # Janma Nakshatra (Moon)
        if 'Moon' in self.planets:
            moon_nakshatra = self.get_nakshatra_from_longitude(self.planets['Moon']['longitude'])
            key_nakshatras['JANMA'] = {
                'planet': 'Moon',
                'nakshatra': moon_nakshatra
            }
        
        # 10th Lord Nakshatra - calculate from ascendant
        ascendant_sign = int(ascendant_longitude / 30)
        tenth_house_sign = (ascendant_sign + 9) % 12
        tenth_lord = self._get_sign_lord(tenth_house_sign)
        if tenth_lord and tenth_lord in self.planets:
            tenth_lord_nakshatra = self.get_nakshatra_from_longitude(self.planets[tenth_lord]['longitude'])
            key_nakshatras['TENTH_LORD'] = {
                'planet': tenth_lord,
                'nakshatra': tenth_lord_nakshatra
            }
        
        # Atmakaraka Nakshatra
        atmakaraka = self.get_atmakaraka()
        if atmakaraka and atmakaraka in self.planets:
            atk_nakshatra = self.get_nakshatra_from_longitude(self.planets[atmakaraka]['longitude'])
            key_nakshatras['ATMAKARAKA'] = {
                'planet': atmakaraka,
                'nakshatra': atk_nakshatra
            }
        
        # Amatyakaraka Nakshatra
        amatyakaraka = self.get_amatyakaraka()
        if amatyakaraka and amatyakaraka in self.planets:
            amk_nakshatra = self.get_nakshatra_from_longitude(self.planets[amatyakaraka]['longitude'])
            key_nakshatras['AMATYAKARAKA'] = {
                'planet': amatyakaraka,
                'nakshatra': amk_nakshatra
            }
        
        # Saturn Nakshatra (Karma Karaka)
        if 'Saturn' in self.planets:
            saturn_nakshatra = self.get_nakshatra_from_longitude(self.planets['Saturn']['longitude'])
            key_nakshatras['SATURN'] = {
                'planet': 'Saturn',
                'nakshatra': saturn_nakshatra
            }
        
        # Lagna Nakshatra
        lagna_nakshatra = self.get_nakshatra_from_longitude(ascendant_longitude)
        key_nakshatras['LAGNA'] = {
            'planet': 'Ascendant',
            'nakshatra': lagna_nakshatra
        }
        
        return key_nakshatras
    
    def get_atmakaraka(self) -> Optional[str]:
        """Get Atmakaraka (planet with highest degree within sign)"""
        max_degree = -1
        atmakaraka = None
        
        for planet, data in self.planets.items():
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                longitude = data.get('longitude', 0)
                degree_in_sign = longitude % 30  # Get degree within sign
                if degree_in_sign > max_degree:
                    max_degree = degree_in_sign
                    atmakaraka = planet
        
        return atmakaraka
    
    def get_amatyakaraka(self) -> Optional[str]:
        """Get Amatyakaraka (planet with second highest degree within sign)"""
        degrees = []
        
        for planet, data in self.planets.items():
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                longitude = data.get('longitude', 0)
                degree_in_sign = longitude % 30  # Get degree within sign
                degrees.append((degree_in_sign, planet))
        
        degrees.sort(reverse=True)
        return degrees[1][1] if len(degrees) > 1 else None
    
    def _get_sign_lord(self, sign_num: int) -> str:
        """Get the lord of a zodiac sign"""
        lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        return lords.get(sign_num, 'Sun')
    
    def get_current_dasha_info(self) -> Optional[Dict[str, Any]]:
        """Get current dasha information from chart data"""
        dasha_data = self.chart_data.get('current_dasha')
        if not dasha_data:
            return None
            
        current_planet = dasha_data.get('mahadasha', {}).get('planet')
        if not current_planet:
            return None
            
        return {
            'planet': current_planet,
            'start': dasha_data.get('mahadasha', {}).get('start_date', ''),
            'end': dasha_data.get('mahadasha', {}).get('end_date', ''),
            'career_impact': self._get_dasha_career_impact(current_planet),
            'recommendations': self._get_dasha_recommendations(current_planet)
        }
    
    def get_upcoming_favorable_periods(self) -> List[Dict[str, Any]]:
        """Get upcoming favorable dasha periods from chart data"""
        dasha_sequence = self.chart_data.get('dasha_sequence', [])
        if not dasha_sequence:
            return []
            
        favorable_periods = []
        for dasha in dasha_sequence[:3]:  # Next 3 periods
            planet = dasha.get('planet')
            if planet and self._is_career_favorable_planet(planet):
                favorable_periods.append({
                    'planet': planet,
                    'start': dasha.get('start_date', ''),
                    'end': dasha.get('end_date', ''),
                    'career_opportunities': self._get_career_opportunities(planet)
                })
                
        return favorable_periods
    
    def analyze_career_nakshatras(self) -> Dict[str, Any]:
        """Complete nakshatra career analysis"""
        key_nakshatras = self.get_key_career_nakshatras()
        current_dasha = self.get_current_dasha_info()
        upcoming_periods = self.get_upcoming_favorable_periods()
        
        return {
            'key_nakshatras': key_nakshatras,
            'current_dasha': current_dasha,
            'upcoming_periods': upcoming_periods,
            'analysis_summary': {
                'primary_career_nature': self._get_primary_career_nature(key_nakshatras),
                'work_style_combination': self._get_work_style_combination(key_nakshatras),
                'leadership_approach': self._get_leadership_approach(key_nakshatras),
                'recommended_environment': self._get_recommended_environment(key_nakshatras)
            }
        }
    
    def _get_primary_career_nature(self, key_nakshatras: Dict) -> str:
        """Determine primary career nature from key nakshatras"""
        if 'JANMA' in key_nakshatras:
            janma_nakshatra = key_nakshatras['JANMA']['nakshatra']
            if janma_nakshatra in self.NAKSHATRA_CONFIG:
                return self.NAKSHATRA_CONFIG[janma_nakshatra]['career_nature']
        return "Balanced professional approach"
    
    def _get_work_style_combination(self, key_nakshatras: Dict) -> str:
        """Get combined work style from multiple nakshatras"""
        styles = []
        for role, data in key_nakshatras.items():
            nakshatra = data['nakshatra']
            if nakshatra in self.NAKSHATRA_CONFIG:
                style = self.NAKSHATRA_CONFIG[nakshatra]['work_style']
                styles.append(style.split(',')[0].strip())  # Take first style
        
        return ', '.join(styles[:3]) if styles else "Adaptable work style"
    
    def _get_leadership_approach(self, key_nakshatras: Dict) -> str:
        """Get leadership approach from Atmakaraka nakshatra"""
        if 'ATMAKARAKA' in key_nakshatras:
            atk_nakshatra = key_nakshatras['ATMAKARAKA']['nakshatra']
            if atk_nakshatra in self.NAKSHATRA_CONFIG:
                return self.NAKSHATRA_CONFIG[atk_nakshatra]['leadership_style']
        return "Balanced leadership style"
    
    def _get_recommended_environment(self, key_nakshatras: Dict) -> str:
        """Get recommended work environment"""
        if 'AMATYAKARAKA' in key_nakshatras:
            amk_nakshatra = key_nakshatras['AMATYAKARAKA']['nakshatra']
            if amk_nakshatra in self.NAKSHATRA_CONFIG:
                return self.NAKSHATRA_CONFIG[amk_nakshatra]['work_environment']
        return "Flexible work environment"
    
    def _get_dasha_career_impact(self, planet: str) -> str:
        """Get career impact for dasha planet"""
        impacts = {
            'Sun': 'Leadership roles, government positions, authority-based careers',
            'Moon': 'Public relations, healthcare, hospitality, nurturing professions', 
            'Mars': 'Engineering, military, sports, real estate, technical fields',
            'Mercury': 'Business, communication, writing, IT, media, trading',
            'Jupiter': 'Teaching, law, finance, spirituality, consulting, advisory roles',
            'Venus': 'Arts, entertainment, beauty, luxury goods, creative fields',
            'Saturn': 'Service sector, manufacturing, discipline-based careers, steady progress',
            'Rahu': 'Technology, foreign connections, unconventional careers',
            'Ketu': 'Spirituality, research, occult sciences, detachment from material success'
        }
        return impacts.get(planet, 'Mixed career influences')
    
    def _get_dasha_recommendations(self, planet: str) -> List[str]:
        """Get career recommendations for dasha planet"""
        recommendations = {
            'Sun': ['Focus on leadership roles', 'Consider government positions', 'Build authority and reputation'],
            'Moon': ['Develop emotional intelligence', 'Consider public-facing roles', 'Focus on nurturing professions'],
            'Mars': ['Leverage technical skills', 'Consider competitive fields', 'Focus on action-oriented careers'],
            'Mercury': ['Enhance communication skills', 'Consider business ventures', 'Focus on intellectual pursuits'],
            'Jupiter': ['Develop teaching abilities', 'Consider advisory roles', 'Focus on knowledge-based careers'],
            'Venus': ['Develop creative abilities', 'Consider artistic fields', 'Focus on beauty and luxury sectors'],
            'Saturn': ['Focus on long-term planning', 'Consider service-oriented roles', 'Build through steady effort'],
            'Rahu': ['Explore unconventional paths', 'Consider technology fields', 'Focus on innovation'],
            'Ketu': ['Consider research roles', 'Focus on spiritual pursuits', 'Develop specialized expertise']
        }
        return recommendations.get(planet, ['Focus on planetary strengths'])
    
    def _is_career_favorable_planet(self, planet: str) -> bool:
        """Check if planet is generally favorable for career"""
        favorable_planets = ['Sun', 'Mercury', 'Jupiter', 'Venus', 'Mars']
        return planet in favorable_planets
    
    def _get_career_opportunities(self, planet: str) -> str:
        """Get career opportunities for planet period"""
        opportunities = {
            'Sun': 'Leadership roles, government positions, and authoritative careers',
            'Mercury': 'Business ventures, communication roles, and intellectual pursuits',
            'Jupiter': 'Teaching, advisory roles, and knowledge-based professions',
            'Venus': 'Creative fields, arts, luxury goods, and beauty industry',
            'Mars': 'Technical fields, engineering, sports, and competitive careers'
        }
        return opportunities.get(planet, 'General career advancement opportunities')