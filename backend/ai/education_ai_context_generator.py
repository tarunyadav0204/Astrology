import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.base_ai_context_generator import BaseAIContextGenerator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from vedic_predictions.config.functional_nature import FUNCTIONAL_BENEFICS, FUNCTIONAL_MALEFICS

class EducationAIContextGenerator(BaseAIContextGenerator):
    """Education-specific AI context generator inheriting from base"""
    
    def build_education_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build complete education analysis context"""
        
        # Get base context first
        base_context = self.build_base_context(birth_data)
        
        # Add education-specific context
        education_context = self._build_education_specific_context(birth_data)
        
        # Combine contexts
        return {
            **base_context,
            **education_context
        }
    
    def _build_education_specific_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build education-specific context components"""
        
        # Get chart data from base context
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        
        # Initialize education-specific calculators
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        
        divisional_calc = DivisionalChartCalculator(chart_data)
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        planet_analyzer = PlanetAnalyzer(chart_data, birth_data)
        
        # Get ascendant sign
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        
        # Calculate D-24 (Chaturvimshamsa - Education chart)
        d24_chart = divisional_calc.calculate_divisional_chart(24)
        
        context = {
            # Education charts with analysis
            "education_charts": {
                "d24_chaturvimshamsa": d24_chart,
                "d24_analysis": self._analyze_d24_chart(d24_chart, chart_data, ascendant_sign)
            },
            
            # Education house analysis
            "education_houses": self._analyze_education_houses(chart_data),
            
            # Learning capacity indicators
            "learning_capacity": self._analyze_learning_capacity(chart_data),
            
            # Subject recommendations
            "subject_analysis": self._analyze_subject_suitability(chart_data),
            
            # Academic timing
            "education_timing": self._analyze_education_timing(birth_data, chart_data),
            
            # Intelligence indicators
            "intelligence_analysis": self._analyze_intelligence(chart_data),
            
            # Memory and concentration
            "memory_analysis": self._analyze_memory_concentration(chart_data),
            
            # Technical aptitude analysis
            "technical_aptitude": self._determine_technical_aptitude(chart_data),
            
            # Functional nature for education
            "functional_nature": self._analyze_functional_nature(chart_data, ascendant_sign),
            
            # Education analysis instructions
            "education_analysis_instructions": {
                "critical_note": "Focus on learning potential, suitable subjects, and optimal study methods.",
                "disclaimer": "This is astrological guidance for educational planning, not academic counseling.",
                "system_instruction": self.VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION
            }
        }
        
        return context
    
    def _analyze_education_houses(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze education-related houses"""
        
        education_houses = {
            "1st_house": self._analyze_house(1, chart_data),  # Intelligence, personality
            "4th_house": self._analyze_house(4, chart_data),  # Foundation education, schooling
            "5th_house": self._analyze_house(5, chart_data),  # Intelligence, creativity, learning
            "9th_house": self._analyze_house(9, chart_data),  # Higher education, wisdom
            "10th_house": self._analyze_house(10, chart_data), # Career-oriented education
            "11th_house": self._analyze_house(11, chart_data), # Gains from education
        }
        
        return education_houses
    
    def _analyze_house(self, house_num: int, chart_data: Dict) -> Dict[str, Any]:
        """Analyze a specific house for education"""
        planets = chart_data.get('planets', {})
        houses = chart_data.get('houses', [])
        
        if house_num > len(houses):
            return {}
        
        house_sign = houses[house_num - 1].get('sign', 0)
        house_lord = self.SIGN_LORDS.get(house_sign, 'Unknown')
        
        # Find planets in this house
        planets_in_house = []
        for planet, data in planets.items():
            if data.get('house', 1) == house_num:
                planets_in_house.append(planet)
        
        # Get lord's position
        lord_position = {}
        if house_lord in planets:
            lord_data = planets[house_lord]
            lord_position = {
                'house': lord_data.get('house', 1),
                'sign': lord_data.get('sign', 0),
                'longitude': lord_data.get('longitude', 0)
            }
        
        return {
            'sign': house_sign,
            'lord': house_lord,
            'lord_position': lord_position,
            'planets_in_house': planets_in_house,
            'planet_count': len(planets_in_house),
            'education_significance': self._get_house_education_significance(house_num)
        }
    
    def _get_house_education_significance(self, house_num: int) -> str:
        """Get education significance of each house"""
        significance = {
            1: "Overall intelligence, learning capacity, and academic personality",
            4: "Foundation education, schooling, basic learning, graduation",
            5: "Intelligence, creativity, academic performance, competitive exams",
            9: "Higher education, university studies, research, foreign education",
            10: "Career-oriented education, professional courses, reputation through learning",
            11: "Gains from education, scholarships, educational achievements"
        }
        return significance.get(house_num, "General influence on education")
    
    def _analyze_learning_capacity(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze overall learning capacity and style"""
        planets = chart_data.get('planets', {})
        
        # Mercury (learning, communication)
        mercury_analysis = {}
        if 'Mercury' in planets:
            mercury_data = planets['Mercury']
            mercury_analysis = {
                'house': mercury_data.get('house', 1),
                'sign': mercury_data.get('sign', 0),
                'strength': self._get_planet_strength(mercury_data),
                'learning_style': self._determine_mercury_learning_style(mercury_data)
            }
        
        # Jupiter (wisdom, higher learning)
        jupiter_analysis = {}
        if 'Jupiter' in planets:
            jupiter_data = planets['Jupiter']
            jupiter_analysis = {
                'house': jupiter_data.get('house', 1),
                'sign': jupiter_data.get('sign', 0),
                'strength': self._get_planet_strength(jupiter_data),
                'wisdom_type': self._determine_jupiter_wisdom_type(jupiter_data)
            }
        
        # Moon (memory, retention)
        moon_analysis = {}
        if 'Moon' in planets:
            moon_data = planets['Moon']
            moon_analysis = {
                'house': moon_data.get('house', 1),
                'sign': moon_data.get('sign', 0),
                'strength': self._get_planet_strength(moon_data),
                'memory_type': self._determine_moon_memory_type(moon_data)
            }
        
        return {
            'mercury_analysis': mercury_analysis,
            'jupiter_analysis': jupiter_analysis,
            'moon_analysis': moon_analysis,
            'overall_learning_capacity': self._calculate_overall_learning_capacity(mercury_analysis, jupiter_analysis, moon_analysis)
        }
    
    def _determine_mercury_learning_style(self, mercury_data: Dict) -> str:
        """Determine learning style based on Mercury position"""
        sign = mercury_data.get('sign', 0)
        
        fire_signs = [0, 4, 8]  # Aries, Leo, Sagittarius
        earth_signs = [1, 5, 9]  # Taurus, Virgo, Capricorn
        air_signs = [2, 6, 10]  # Gemini, Libra, Aquarius
        water_signs = [3, 7, 11]  # Cancer, Scorpio, Pisces
        
        if sign in fire_signs:
            return "Quick, enthusiastic learner; prefers active, hands-on learning"
        elif sign in earth_signs:
            return "Methodical, practical learner; prefers structured, step-by-step approach"
        elif sign in air_signs:
            return "Intellectual, communicative learner; prefers discussion and conceptual learning"
        elif sign in water_signs:
            return "Intuitive, emotional learner; prefers creative and experiential learning"
        else:
            return "Balanced learning approach"
    
    def _determine_jupiter_wisdom_type(self, jupiter_data: Dict) -> str:
        """Determine wisdom and higher learning type based on Jupiter"""
        house = jupiter_data.get('house', 1)
        
        if house in [1, 5, 9]:
            return "Natural wisdom, philosophical learning, teaching ability"
        elif house in [4, 10]:
            return "Practical wisdom, career-oriented higher education"
        elif house in [2, 11]:
            return "Wealth-generating education, business-oriented learning"
        else:
            return "Specialized wisdom in specific areas"
    
    def _determine_moon_memory_type(self, moon_data: Dict) -> str:
        """Determine memory and retention type based on Moon"""
        sign = moon_data.get('sign', 0)
        
        if sign in [1, 5, 9]:  # Taurus, Virgo, Capricorn
            return "Excellent long-term memory, methodical retention"
        elif sign in [2, 6, 10]:  # Gemini, Libra, Aquarius
            return "Quick memory, good with facts and figures"
        elif sign in [3, 7, 11]:  # Cancer, Scorpio, Pisces
            return "Emotional memory, remembers through associations"
        else:
            return "Balanced memory capabilities"
    
    def _analyze_subject_suitability(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze suitability for different subjects"""
        planets = chart_data.get('planets', {})
        
        subject_analysis = {}
        
        # Subject mapping based on planetary strengths
        planet_subjects = {
            'Mercury': ['Mathematics', 'Commerce', 'Communication', 'Computer Science', 'Languages'],
            'Jupiter': ['Philosophy', 'Law', 'Teaching', 'Religion', 'Management'],
            'Mars': ['Engineering', 'Sports', 'Military Science', 'Surgery', 'Technology'],
            'Venus': ['Arts', 'Music', 'Fashion', 'Design', 'Hospitality'],
            'Saturn': ['Research', 'History', 'Archaeology', 'Mining', 'Agriculture'],
            'Sun': ['Government Studies', 'Political Science', 'Administration', 'Leadership'],
            'Moon': ['Psychology', 'Nursing', 'Hospitality', 'Public Relations', 'Counseling']
        }
        
        for planet, subjects in planet_subjects.items():
            if planet in planets:
                planet_data = planets[planet]
                strength = self._get_planet_strength(planet_data)
                
                subject_analysis[planet] = {
                    'subjects': subjects,
                    'strength': strength,
                    'house': planet_data.get('house', 1),
                    'sign': planet_data.get('sign', 0),
                    'suitability_score': self._calculate_subject_suitability_score(planet_data)
                }
        
        return subject_analysis
    
    def _calculate_subject_suitability_score(self, planet_data: Dict) -> int:
        """Calculate suitability score for subjects ruled by a planet"""
        house = planet_data.get('house', 1)
        
        # Education houses get higher scores
        if house in [1, 4, 5, 9, 10]:
            base_score = 80
        elif house in [2, 3, 11]:
            base_score = 60
        else:
            base_score = 40
        
        # Adjust based on strength
        strength = self._get_planet_strength(planet_data)
        if strength == 'Strong':
            base_score += 15
        elif strength == 'Weak':
            base_score -= 15
        
        return min(100, max(20, base_score))
    
    def _analyze_education_timing(self, birth_data: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze timing for educational events"""
        
        # Get current dashas
        from shared.dasha_calculator import DashaCalculator
        dasha_calc = DashaCalculator()
        current_dashas = dasha_calc.calculate_current_dashas(birth_data)
        
        timing_factors = {
            'current_dashas': current_dashas,
            'favorable_periods': self._get_education_favorable_periods(current_dashas, chart_data),
            'jupiter_transit_info': self._get_jupiter_transit_info(),
            'current_period_analysis': self._analyze_current_period_for_education(current_dashas, chart_data)
        }
        
        return timing_factors
    
    def _get_education_favorable_periods(self, current_dashas: Dict, chart_data: Dict) -> list:
        """Get favorable periods for education"""
        if not current_dashas:
            return []
        
        mahadasha = current_dashas.get('mahadasha', 'Unknown')
        
        # Education-favorable planets
        favorable_planets = ['Mercury', 'Jupiter', 'Moon', 'Sun']
        
        favorable = []
        if mahadasha in favorable_planets:
            favorable.append(f"Current {mahadasha} Mahadasha is favorable for education")
        
        return favorable
    
    def _get_jupiter_transit_info(self) -> Dict[str, Any]:
        """Get current Jupiter position for education timing"""
        from calculators.real_transit_calculator import RealTransitCalculator
        from datetime import datetime
        
        try:
            transit_calc = RealTransitCalculator()
            current_date = datetime.now()
            
            jupiter_longitude = transit_calc.get_planet_position(current_date, 'Jupiter')
            current_jupiter_sign = int(jupiter_longitude / 30) if jupiter_longitude else 0
            
            sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
            
            return {
                'current_jupiter_sign': sign_names[current_jupiter_sign],
                'jupiter_longitude': jupiter_longitude,
                'education_note': 'Jupiter transits can indicate favorable periods for higher education'
            }
        except Exception as e:
            return {
                'error': f'Transit position error: {e}',
                'education_note': 'Jupiter transits can indicate favorable periods for higher education'
            }
    
    def _analyze_current_period_for_education(self, current_dashas: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze current dasha period for education"""
        if not current_dashas:
            return {'analysis': 'No current dasha data available'}
        
        mahadasha = current_dashas.get('mahadasha', 'Unknown')
        antardasha = current_dashas.get('antardasha', 'Unknown')
        
        # Education-favorable planets
        favorable_planets = ['Mercury', 'Jupiter', 'Moon', 'Sun']
        
        education_status = 'Neutral'
        if mahadasha in favorable_planets or antardasha in favorable_planets:
            education_status = 'Favorable'
        
        analysis = {
            'current_mahadasha': mahadasha,
            'current_antardasha': antardasha,
            'education_status': education_status,
            'recommendation': f'Current {mahadasha}-{antardasha} period education guidance'
        }
        
        return analysis
    
    def _analyze_intelligence(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze intelligence indicators"""
        planets = chart_data.get('planets', {})
        
        # 5th house analysis (intelligence)
        fifth_house = self._analyze_house(5, chart_data)
        
        # Mercury (analytical intelligence)
        mercury_intelligence = {}
        if 'Mercury' in planets:
            mercury_data = planets['Mercury']
            mercury_intelligence = {
                'house': mercury_data.get('house', 1),
                'sign': mercury_data.get('sign', 0),
                'strength': self._get_planet_strength(mercury_data),
                'intelligence_type': 'Analytical, logical, communicative intelligence'
            }
        
        # Jupiter (wisdom intelligence)
        jupiter_intelligence = {}
        if 'Jupiter' in planets:
            jupiter_data = planets['Jupiter']
            jupiter_intelligence = {
                'house': jupiter_data.get('house', 1),
                'sign': jupiter_data.get('sign', 0),
                'strength': self._get_planet_strength(jupiter_data),
                'intelligence_type': 'Wisdom, philosophical, teaching intelligence'
            }
        
        return {
            'fifth_house_analysis': fifth_house,
            'mercury_intelligence': mercury_intelligence,
            'jupiter_intelligence': jupiter_intelligence,
            'overall_intelligence': self._calculate_overall_intelligence(mercury_intelligence, jupiter_intelligence)
        }
    
    def _analyze_memory_concentration(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze memory and concentration abilities"""
        planets = chart_data.get('planets', {})
        
        # Moon (memory)
        moon_memory = {}
        if 'Moon' in planets:
            moon_data = planets['Moon']
            moon_memory = {
                'house': moon_data.get('house', 1),
                'sign': moon_data.get('sign', 0),
                'strength': self._get_planet_strength(moon_data),
                'memory_quality': self._assess_moon_memory_quality(moon_data)
            }
        
        # Mercury (concentration)
        mercury_concentration = {}
        if 'Mercury' in planets:
            mercury_data = planets['Mercury']
            mercury_concentration = {
                'house': mercury_data.get('house', 1),
                'sign': mercury_data.get('sign', 0),
                'strength': self._get_planet_strength(mercury_data),
                'concentration_quality': self._assess_mercury_concentration_quality(mercury_data)
            }
        
        return {
            'moon_memory': moon_memory,
            'mercury_concentration': mercury_concentration,
            'overall_assessment': self._calculate_memory_concentration_overall(moon_memory, mercury_concentration)
        }
    
    def _assess_moon_memory_quality(self, moon_data: Dict) -> str:
        """Assess Moon's influence on memory quality"""
        house = moon_data.get('house', 1)
        
        if house in [1, 4, 5]:
            return 'Excellent memory, good retention and recall'
        elif house in [6, 8, 12]:
            return 'Memory needs strengthening, may have gaps'
        else:
            return 'Good memory with some fluctuations'
    
    def _assess_mercury_concentration_quality(self, mercury_data: Dict) -> str:
        """Assess Mercury's influence on concentration quality"""
        house = mercury_data.get('house', 1)
        
        if house in [1, 5, 9]:
            return 'Excellent concentration, sharp focus'
        elif house in [6, 8, 12]:
            return 'Concentration needs improvement, easily distracted'
        else:
            return 'Good concentration with occasional lapses'
    
    def _analyze_d24_chart(self, d24_chart: Dict, d1_chart: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze D-24 (Chaturvimshamsa) for education"""
        if not d24_chart or 'divisional_chart' not in d24_chart:
            return {'analysis': 'D-24 chart not available'}
        
        d24_data = d24_chart['divisional_chart']
        d24_planets = d24_data.get('planets', {})
        
        # Get D-24 Lagna Lord (Critical for academic distinction)
        d24_asc_sign = int(d24_data.get('ascendant', 0) / 30)
        d24_lagna_lord = self.SIGN_LORDS.get(d24_asc_sign, 'Unknown')
        
        # Analyze D-24 Lagna Lord position
        d24_lagna_lord_analysis = {}
        if d24_lagna_lord in d24_planets:
            d24_lord_house = self._get_planet_house_in_d24(d24_lagna_lord, d24_planets, d24_asc_sign)
            strength = "Strong" if d24_lord_house in [1, 4, 5, 7, 9, 10] else "Weak"
            d24_lagna_lord_analysis = {
                'planet': d24_lagna_lord,
                'house': d24_lord_house,
                'status': strength,
                'implication': 'High Academic Distinction (Ph.D., Gold Medal)' if strength == 'Strong' else 'Obstacles in higher education, average performance'
            }
        
        # Get 4th and 5th lords from D-1
        fourth_sign = (ascendant_sign + 3) % 12
        fifth_sign = (ascendant_sign + 4) % 12
        fourth_lord = self.SIGN_LORDS.get(fourth_sign, 'Unknown')
        fifth_lord = self.SIGN_LORDS.get(fifth_sign, 'Unknown')
        
        # Analyze education lords in D-24
        fourth_lord_d24_analysis = {}
        if fourth_lord in d24_planets:
            d24_house = self._get_planet_house_in_d24(fourth_lord, d24_planets, d24_asc_sign)
            fourth_lord_d24_analysis = {
                'planet': fourth_lord,
                'd24_house': d24_house,
                'education_impact': self._interpret_d24_house_position(d24_house, 'foundation education')
            }
        
        fifth_lord_d24_analysis = {}
        if fifth_lord in d24_planets:
            d24_house = self._get_planet_house_in_d24(fifth_lord, d24_planets, d24_asc_sign)
            fifth_lord_d24_analysis = {
                'planet': fifth_lord,
                'd24_house': d24_house,
                'education_impact': self._interpret_d24_house_position(d24_house, 'intelligence and learning')
            }
        
        return {
            'd24_lagna_lord': d24_lagna_lord_analysis,
            'fourth_lord_analysis': fourth_lord_d24_analysis,
            'fifth_lord_analysis': fifth_lord_d24_analysis,
            'overall_d24_assessment': self._assess_d24_overall_enhanced(d24_lagna_lord_analysis, fourth_lord_d24_analysis, fifth_lord_d24_analysis)
        }
    
    def _interpret_d24_house_position(self, house: int, education_type: str) -> str:
        """Interpret D-24 house position for education"""
        if house in [1, 4, 5, 9, 10]:
            return f"Excellent potential for {education_type}"
        elif house in [2, 3, 11]:
            return f"Good opportunities in {education_type}"
        elif house in [6, 8, 12]:
            return f"Challenges in {education_type}, needs extra effort"
        else:
            return f"Moderate potential for {education_type}"
    
    def _assess_d24_overall(self, fourth_analysis: Dict, fifth_analysis: Dict) -> str:
        """Assess overall D-24 education indication"""
        if not fourth_analysis or not fifth_analysis:
            return 'Insufficient D-24 data for comprehensive assessment'
        
        fourth_impact = fourth_analysis.get('education_impact', '')
        fifth_impact = fifth_analysis.get('education_impact', '')
        
        if 'Excellent' in fourth_impact and 'Excellent' in fifth_impact:
            return 'Outstanding educational potential with strong foundation and intelligence'
        elif 'Excellent' in fourth_impact or 'Excellent' in fifth_impact:
            return 'Very good educational prospects with particular strength in one area'
        elif 'Good' in fourth_impact and 'Good' in fifth_impact:
            return 'Solid educational foundation with steady progress expected'
        else:
            return 'Educational success requires focused effort and proper guidance'
    
    def _analyze_functional_nature(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze functional benefic/malefic nature for education"""
        planets = chart_data.get('planets', {})
        
        functional_benefics = FUNCTIONAL_BENEFICS.get(ascendant_sign, [])
        functional_malefics = FUNCTIONAL_MALEFICS.get(ascendant_sign, [])
        
        education_benefics = []
        education_malefics = []
        
        for planet_name in planets.keys():
            if planet_name in ['Rahu', 'Ketu']:
                continue
            
            planet_data = planets[planet_name]
            house = planet_data.get('house', 1)
            
            if planet_name in functional_benefics:
                education_benefics.append({
                    'planet': planet_name,
                    'house': house,
                    'education_impact': 'Positive - supports educational success'
                })
            elif planet_name in functional_malefics:
                # Functional malefic in education houses needs attention
                if house in [1, 4, 5, 9]:
                    education_malefics.append({
                        'planet': planet_name,
                        'house': house,
                        'education_impact': f'Challenging - functional malefic in {house}th house may create educational obstacles'
                    })
        
        return {
            'ascendant_sign': ascendant_sign,
            'functional_benefics': education_benefics,
            'functional_malefics': education_malefics,
            'education_assessment': self._assess_functional_education(education_benefics, education_malefics)
        }
    
    def _assess_functional_education(self, benefics: list, malefics: list) -> str:
        """Assess overall functional education status"""
        if len(malefics) > len(benefics):
            return 'Functional malefics create challenges - requires remedial measures for educational success'
        elif len(benefics) > len(malefics):
            return 'Functional benefics support education - natural aptitude for learning'
        else:
            return 'Balanced functional nature - steady educational progress with effort'
    
    def _get_planet_strength(self, planet_data: Dict) -> str:
        """Get basic planet strength"""
        house = planet_data.get('house', 1)
        
        if house in [1, 4, 7, 10]:  # Kendra
            return 'Strong'
        elif house in [1, 5, 9]:  # Trikona
            return 'Strong'
        elif house in [6, 8, 12]:  # Dusthana
            return 'Weak'
        else:
            return 'Medium'
    
    def _calculate_overall_learning_capacity(self, mercury: Dict, jupiter: Dict, moon: Dict) -> str:
        """Calculate overall learning capacity"""
        if not mercury or not jupiter or not moon:
            return 'Moderate'
        
        mercury_strength = mercury.get('strength', 'Medium')
        jupiter_strength = jupiter.get('strength', 'Medium')
        moon_strength = moon.get('strength', 'Medium')
        
        strong_count = sum(1 for strength in [mercury_strength, jupiter_strength, moon_strength] if strength == 'Strong')
        
        if strong_count >= 2:
            return 'Excellent learning capacity with multiple strengths'
        elif strong_count == 1:
            return 'Good learning capacity with specific strengths'
        else:
            return 'Moderate learning capacity - can be improved with effort'
    
    def _calculate_overall_intelligence(self, mercury: Dict, jupiter: Dict) -> str:
        """Calculate overall intelligence assessment"""
        if not mercury or not jupiter:
            return 'Balanced'
        
        mercury_strength = mercury.get('strength', 'Medium')
        jupiter_strength = jupiter.get('strength', 'Medium')
        
        if mercury_strength == 'Strong' and jupiter_strength == 'Strong':
            return 'Exceptional intelligence - both analytical and wisdom-based'
        elif mercury_strength == 'Strong':
            return 'Strong analytical and logical intelligence'
        elif jupiter_strength == 'Strong':
            return 'Strong wisdom and philosophical intelligence'
        else:
            return 'Balanced intelligence with room for development'
    
    def _calculate_memory_concentration_overall(self, moon: Dict, mercury: Dict) -> str:
        """Calculate overall memory and concentration assessment"""
        if not moon or not mercury:
            return 'Moderate'
        
        moon_strength = moon.get('strength', 'Medium')
        mercury_strength = mercury.get('strength', 'Medium')
        
        if moon_strength == 'Strong' and mercury_strength == 'Strong':
            return 'Excellent memory and concentration abilities'
        elif moon_strength == 'Strong':
            return 'Strong memory with good retention'
        elif mercury_strength == 'Strong':
            return 'Excellent concentration and focus'
        else:
            return 'Moderate memory and concentration - can be enhanced'
    
    def _determine_technical_aptitude(self, chart_data: Dict) -> Dict[str, Any]:
        """Determine aptitude for technical/STEM fields"""
        planets = chart_data.get('planets', {})
        fifth_house = self._analyze_house(5, chart_data)
        fifth_house_planets = fifth_house.get('planets_in_house', [])
        
        technical_indicators = []
        score = 0
        
        # Mars influence (Engineering/Logic)
        if 'Mars' in fifth_house_planets:
            score += 20
            technical_indicators.append("Mars in 5th house (Technical Logic)")
        
        # Rahu/Ketu influence (Coding/Research)
        if 'Rahu' in fifth_house_planets or 'Ketu' in fifth_house_planets:
            score += 20
            technical_indicators.append("Nodes in 5th house (Advanced/Abstract Tech)")
        
        # Mars + Saturn connection (Engineering)
        if 'Mars' in planets and 'Saturn' in planets:
            mars_house = planets['Mars'].get('house', 1)
            saturn_house = planets['Saturn'].get('house', 1)
            if mars_house == saturn_house:
                score += 25
                technical_indicators.append("Mars-Saturn conjunction (Engineering/Machinery)")
        
        # Mars + Rahu connection (Technology)
        if 'Mars' in planets and 'Rahu' in planets:
            mars_house = planets['Mars'].get('house', 1)
            rahu_house = planets['Rahu'].get('house', 1)
            if mars_house == rahu_house:
                score += 20
                technical_indicators.append("Mars-Rahu conjunction (Coding/Technology)")
        
        # Sun + Rahu connection (Physics/Technology)
        if 'Sun' in planets and 'Rahu' in planets:
            sun_house = planets['Sun'].get('house', 1)
            rahu_house = planets['Rahu'].get('house', 1)
            if sun_house == rahu_house:
                score += 15
                technical_indicators.append("Sun-Rahu conjunction (Physics/Technology)")
        
        # Ketu in 9th house (Deep research)
        if 'Ketu' in planets:
            ketu_house = planets['Ketu'].get('house', 1)
            if ketu_house == 9:
                score += 15
                technical_indicators.append("Ketu in 9th house (Deep Research/Micro-sciences)")
        
        is_technical = score >= 20
        return {
            "is_technical_leaning": is_technical,
            "technical_score": score,
            "indicators": technical_indicators,
            "recommendation": "STEM fields, Engineering, Technology" if is_technical else "Liberal Arts, Humanities, Commerce"
        }
    
    def _get_planet_house_in_d24(self, planet_name: str, d24_planets: Dict, d24_asc_sign: int) -> int:
        """Calculate house position of planet in D-24 chart"""
        if planet_name not in d24_planets:
            return 1
        
        planet_sign = d24_planets[planet_name].get('sign', 0)
        # Calculate house from D-24 ascendant
        house = ((planet_sign - d24_asc_sign) % 12) + 1
        return house
    
    def _assess_d24_overall_enhanced(self, lagna_analysis: Dict, fourth_analysis: Dict, fifth_analysis: Dict) -> str:
        """Enhanced D-24 assessment including Lagna Lord"""
        if not lagna_analysis:
            return 'Insufficient D-24 Lagna Lord data'
        
        lagna_status = lagna_analysis.get('status', 'Unknown')
        
        if lagna_status == 'Strong':
            return 'Exceptional educational potential with high academic distinction (Ph.D., Gold Medal, Research Excellence)'
        else:
            fourth_impact = fourth_analysis.get('education_impact', '') if fourth_analysis else ''
            fifth_impact = fifth_analysis.get('education_impact', '') if fifth_analysis else ''
            
            if 'Excellent' in fourth_impact or 'Excellent' in fifth_impact:
                return 'Good educational prospects despite D-24 Lagna Lord challenges - focus on specific strengths'
            else:
                return 'Educational success requires extra effort and proper guidance - average to moderate achievements expected'
    
    @property
    def SIGN_LORDS(self):
        """Sign lordships"""
        return {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }