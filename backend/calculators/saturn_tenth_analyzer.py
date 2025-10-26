from .planet_analyzer import PlanetAnalyzer
from .house_strength_calculator import HouseStrengthCalculator
from .aspect_calculator import AspectCalculator
from .strength_calculator import StrengthCalculator

class SaturnTenthAnalyzer:
    """Analyzer for 10th house from Saturn's position"""
    
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.planet_analyzer = PlanetAnalyzer(chart_data)
        self.house_strength_calc = HouseStrengthCalculator(chart_data)
        self.aspect_calc = AspectCalculator(chart_data)
        self.strength_calc = StrengthCalculator(chart_data)
    
    def analyze_saturn_tenth_house(self):
        """Complete analysis of 10th house from Saturn"""
        # Get Saturn's house position
        saturn_data = self.chart_data.get('planets', {}).get('Saturn', {})
        saturn_house = saturn_data.get('house', 1)
        
        # Calculate 10th house from Saturn
        saturn_tenth_house = ((saturn_house - 1 + 9) % 12) + 1
        
        # Get house sign and lord
        house_info = self._get_house_info(saturn_tenth_house)
        
        return {
            'saturn_info': {
                'saturn_house': saturn_house,
                'saturn_sign': self._get_sign_name(saturn_data.get('sign', 0))
            },
            'saturn_tenth_house_info': {
                'house_number': saturn_tenth_house,
                'house_sign': house_info['sign'],
                'house_lord': house_info['lord']
            },
            'sign_analysis': self._analyze_house_sign(saturn_tenth_house, house_info),
            'planets_in_house': self._analyze_planets_in_house(saturn_tenth_house),
            'aspects_on_house': self._analyze_aspects_on_house(saturn_tenth_house),
            'house_strength': self.house_strength_calc.calculate_house_strength(saturn_tenth_house),
            'ashtakavarga_points': self._get_ashtakavarga_points(saturn_tenth_house),
            'overall_assessment': self._get_overall_assessment(saturn_tenth_house, house_info)
        }
    
    def _get_house_info(self, house_number):
        """Get house sign and lord information"""
        # Get ascendant sign
        ascendant_longitude = self.chart_data.get('ascendant', 0)
        ascendant_sign = int(ascendant_longitude / 30)
        
        # Calculate house sign
        house_sign_num = (ascendant_sign + house_number - 1) % 12
        house_sign = self._get_sign_name(house_sign_num)
        house_lord = self._get_sign_lord(house_sign_num)
        
        return {
            'sign': house_sign,
            'lord': house_lord,
            'sign_number': house_sign_num
        }
    
    def _analyze_house_sign(self, house_number, house_info):
        """Analyze the sign in the house"""
        sign = house_info['sign']
        sign_lord = house_info['lord']
        
        # Get sign characteristics
        sign_data = self._get_sign_characteristics(house_info['sign_number'])
        
        return {
            'sign': sign,
            'sign_lord': sign_lord,
            'sign_element': sign_data['element'],
            'sign_quality': sign_data['quality'],
            'career_nature': self._get_career_nature_from_saturn_tenth(sign, sign_data),
            'career_approach': self._get_career_approach_from_saturn_tenth(sign, sign_data)
        }
    
    def _analyze_planets_in_house(self, house_number):
        """Analyze planets in the Saturn's 10th house"""
        planets_in_house = []
        
        for planet, data in self.chart_data.get('planets', {}).items():
            if data.get('house') == house_number:
                planet_analysis = self.planet_analyzer.analyze_planet(planet)
                planets_in_house.append({
                    'planet': planet,
                    'dignity': planet_analysis['dignity_analysis']['dignity'],
                    'shadbala_rupas': planet_analysis['strength_analysis']['shadbala_rupas'],
                    'career_significance': self._get_saturn_tenth_career_significance(planet),
                    'overall_effect': self._assess_planet_effect_in_saturn_tenth(planet_analysis)
                })
        
        # Calculate overall influence
        overall_influence = self._calculate_overall_planetary_influence(planets_in_house)
        strongest_planet = max(planets_in_house, key=lambda p: p['shadbala_rupas']) if planets_in_house else None
        
        return {
            'planet_count': len(planets_in_house),
            'planets': planets_in_house,
            'overall_planetary_influence': overall_influence,
            'strongest_planet': strongest_planet
        }
    
    def _analyze_aspects_on_house(self, house_number):
        """Analyze aspects on Saturn's 10th house"""
        aspects = []
        
        for planet, data in self.chart_data.get('planets', {}).items():
            planet_house = data.get('house', 1)
            aspected_houses = self.planet_analyzer._get_aspect_houses(planet, planet_house)
            
            if house_number in aspected_houses:
                # Get basic aspect effect score
                effect_score = self._calculate_basic_aspect_effect(planet)
                aspects.append({
                    'aspecting_planet': planet,
                    'aspect_type': self.planet_analyzer._get_aspect_type(planet_house, house_number),
                    'effect': self._categorize_aspect_effect(effect_score),
                    'effect_score': effect_score,
                    'calculation_details': [f"{planet} aspects house {house_number} with {effect_score:+.1f} effect"]
                })
        
        # Separate benefic and malefic aspects
        benefic_aspects = [a for a in aspects if a['effect_score'] > 0]
        malefic_aspects = [a for a in aspects if a['effect_score'] < 0]
        
        # Calculate net aspect score
        net_score = sum(a['effect_score'] for a in aspects)
        
        return {
            'aspect_count': len(aspects),
            'aspects': aspects,
            'benefic_aspects': benefic_aspects,
            'malefic_aspects': malefic_aspects,
            'net_aspect_score': net_score,
            'overall_aspect_effect': self._get_overall_aspect_effect(net_score)
        }
    
    def _calculate_house_strength(self, house_number, house_info):
        """Calculate strength of Saturn's 10th house"""
        # Get house lord analysis
        house_lord = house_info['lord']
        lord_analysis = self.planet_analyzer.analyze_planet(house_lord)
        
        # Components of house strength
        sign_lord_strength = min(lord_analysis['overall_assessment']['overall_strength_score'], 100)
        
        # Planets in house strength
        planets_data = self._analyze_planets_in_house(house_number)
        planets_strength = self._calculate_planets_strength(planets_data['planets'])
        
        # Aspects strength
        aspects_data = self._analyze_aspects_on_house(house_number)
        aspects_strength = max(0, min(100, 50 + aspects_data['net_aspect_score'] * 5))
        
        # Ashtakavarga strength
        ashtakavarga_data = self._get_ashtakavarga_points(house_number)
        ashtakavarga_strength = min(100, ashtakavarga_data['total_points'] * 3.33)
        
        # Calculate total score (weighted average)
        total_score = (
            sign_lord_strength * 0.3 +
            planets_strength * 0.3 +
            aspects_strength * 0.2 +
            ashtakavarga_strength * 0.2
        )
        
        return {
            'total_score': round(total_score, 1),
            'grade': self._get_strength_grade(total_score),
            'components': {
                'sign_lord_strength': round(sign_lord_strength, 1),
                'planets_strength': round(planets_strength, 1),
                'aspects_strength': round(aspects_strength, 1),
                'ashtakavarga_strength': round(ashtakavarga_strength, 1)
            },
            'interpretation': self._interpret_saturn_tenth_strength(total_score)
        }
    
    def _get_ashtakavarga_points(self, house_number):
        """Get Ashtakavarga points for the house (simplified)"""
        # Simplified Ashtakavarga calculation
        base_points = 28  # Average points per house
        
        # Adjust based on house number and planetary positions
        adjustment = 0
        for planet, data in self.chart_data.get('planets', {}).items():
            if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                planet_house = data.get('house', 1)
                if abs(planet_house - house_number) <= 2:
                    adjustment += 2
        
        total_points = min(40, max(15, base_points + adjustment))
        
        return {
            'total_points': total_points,
            'strength_level': 'Strong' if total_points >= 30 else 'Moderate' if total_points >= 25 else 'Weak',
            'interpretation': self._interpret_ashtakavarga_points(total_points)
        }
    
    def _get_overall_assessment(self, house_number, house_info):
        """Get overall assessment of Saturn's 10th house"""
        house_strength = self._calculate_house_strength(house_number, house_info)
        planets_data = self._analyze_planets_in_house(house_number)
        aspects_data = self._analyze_aspects_on_house(house_number)
        
        overall_score = house_strength['total_score']
        overall_grade = house_strength['grade']
        
        # Determine career potential from Saturn's perspective
        career_potential = self._assess_saturn_tenth_career_potential(overall_score, planets_data, aspects_data)
        
        # Key strengths and challenges
        key_strengths = self._identify_saturn_tenth_strengths(house_info, planets_data, aspects_data)
        key_challenges = self._identify_saturn_tenth_challenges(house_info, planets_data, aspects_data)
        
        # Recommendations
        recommendations = self._get_saturn_tenth_recommendations(overall_score, key_challenges)
        
        return {
            'overall_strength_score': round(overall_score, 1),
            'overall_grade': overall_grade,
            'career_potential': career_potential,
            'key_strengths': key_strengths,
            'key_challenges': key_challenges,
            'recommendations': recommendations
        }
    
    # Helper methods
    def _get_sign_name(self, sign_number):
        """Get sign name from number"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_number % 12]
    
    def _get_sign_lord(self, sign_number):
        """Get sign lord"""
        lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
                'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        return lords[sign_number % 12]
    
    def _get_sign_characteristics(self, sign_number):
        """Get sign characteristics"""
        elements = ['Fire', 'Earth', 'Air', 'Water', 'Fire', 'Earth',
                   'Air', 'Water', 'Fire', 'Earth', 'Air', 'Water']
        qualities = ['Cardinal', 'Fixed', 'Mutable', 'Cardinal', 'Fixed', 'Mutable',
                    'Cardinal', 'Fixed', 'Mutable', 'Cardinal', 'Fixed', 'Mutable']
        
        return {
            'element': elements[sign_number % 12],
            'quality': qualities[sign_number % 12]
        }
    
    def _get_career_nature_from_saturn_tenth(self, sign, sign_data):
        """Get career nature from Saturn's 10th house sign"""
        career_natures = {
            'Aries': 'Leadership roles requiring discipline and initiative',
            'Taurus': 'Stable careers in finance, agriculture, or luxury goods',
            'Gemini': 'Communication-based careers requiring methodical approach',
            'Cancer': 'Nurturing professions with long-term security focus',
            'Leo': 'Authority positions requiring sustained effort',
            'Virgo': 'Service-oriented careers with attention to detail',
            'Libra': 'Partnership-based careers requiring patience',
            'Scorpio': 'Research or transformation-based careers',
            'Sagittarius': 'Teaching or philosophical careers with discipline',
            'Capricorn': 'Traditional authority roles and administration',
            'Aquarius': 'Innovative careers serving collective good',
            'Pisces': 'Spiritual or service careers requiring sacrifice'
        }
        return career_natures.get(sign, 'Professional work requiring discipline')
    
    def _get_career_approach_from_saturn_tenth(self, sign, sign_data):
        """Get career approach from Saturn's 10th house"""
        approaches = {
            'Fire': 'Disciplined action and sustained leadership',
            'Earth': 'Practical, methodical, and security-focused approach',
            'Air': 'Systematic communication and networking',
            'Water': 'Intuitive service with emotional intelligence'
        }
        return approaches.get(sign_data['element'], 'Balanced professional approach')
    
    def _get_saturn_tenth_career_significance(self, planet):
        """Get career significance of planet in Saturn's 10th house"""
        significances = {
            'Sun': 'Authority and leadership from Saturn\'s perspective',
            'Moon': 'Public service and emotional intelligence in career',
            'Mars': 'Disciplined action and structured energy',
            'Mercury': 'Methodical communication and systematic thinking',
            'Jupiter': 'Wisdom-based leadership with patience',
            'Venus': 'Harmonious relationships in structured environment',
            'Saturn': 'Double emphasis on discipline and responsibility',
            'Rahu': 'Unconventional career paths requiring discipline',
            'Ketu': 'Spiritual or research-oriented career detachment'
        }
        return significances.get(planet, 'General career influence')
    
    def _assess_planet_effect_in_saturn_tenth(self, planet_analysis):
        """Assess planet effect in Saturn's 10th house"""
        dignity = planet_analysis['dignity_analysis']['dignity']
        strength = planet_analysis['strength_analysis']['shadbala_rupas']
        
        if dignity in ['exalted', 'own_sign'] and strength >= 5:
            return 'Highly beneficial'
        elif dignity in ['exalted', 'own_sign'] or strength >= 4:
            return 'Beneficial'
        elif dignity == 'debilitated' or strength < 2:
            return 'Challenging'
        else:
            return 'Moderate'
    
    def _calculate_overall_planetary_influence(self, planets):
        """Calculate overall planetary influence"""
        if not planets:
            return 'No planetary influence'
        
        beneficial_count = sum(1 for p in planets if p['overall_effect'] in ['Highly beneficial', 'Beneficial'])
        challenging_count = sum(1 for p in planets if p['overall_effect'] == 'Challenging')
        
        if beneficial_count > challenging_count:
            return 'Predominantly positive'
        elif challenging_count > beneficial_count:
            return 'Requires careful handling'
        else:
            return 'Mixed influences'
    
    def _calculate_basic_aspect_effect(self, planet):
        """Calculate basic aspect effect score"""
        # Natural benefic/malefic nature
        natural_benefics = ['Jupiter', 'Venus']
        natural_malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
        
        if planet in natural_benefics:
            return 2.0
        elif planet in natural_malefics:
            return -2.0
        else:  # Mercury, Moon
            return 1.0
    
    def _categorize_aspect_effect(self, effect_score):
        """Categorize aspect effect"""
        if effect_score >= 3:
            return 'Highly beneficial'
        elif effect_score >= 1:
            return 'Beneficial'
        elif effect_score <= -3:
            return 'Highly challenging'
        elif effect_score <= -1:
            return 'Challenging'
        else:
            return 'Neutral'
    
    def _get_overall_aspect_effect(self, net_score):
        """Get overall aspect effect"""
        if net_score >= 5:
            return 'Strongly supportive'
        elif net_score >= 2:
            return 'Supportive'
        elif net_score <= -5:
            return 'Highly challenging'
        elif net_score <= -2:
            return 'Challenging'
        else:
            return 'Balanced'
    
    def _calculate_planets_strength(self, planets):
        """Calculate strength from planets in house"""
        if not planets:
            return 50  # Neutral
        
        total_strength = sum(p['shadbala_rupas'] for p in planets)
        avg_strength = total_strength / len(planets)
        
        return min(100, max(0, avg_strength * 15))
    
    def _get_strength_grade(self, score):
        """Get strength grade"""
        if score >= 80:
            return 'Excellent'
        elif score >= 70:
            return 'Very Good'
        elif score >= 60:
            return 'Good'
        elif score >= 50:
            return 'Average'
        elif score >= 40:
            return 'Below Average'
        else:
            return 'Weak'
    
    def _interpret_saturn_tenth_strength(self, score):
        """Interpret Saturn's 10th house strength"""
        if score >= 70:
            return 'Strong foundation for disciplined career growth from Saturn\'s perspective'
        elif score >= 50:
            return 'Moderate career potential requiring consistent effort and patience'
        else:
            return 'Career challenges from Saturn\'s viewpoint need structured approach'
    
    def _interpret_ashtakavarga_points(self, points):
        """Interpret Ashtakavarga points"""
        if points >= 30:
            return 'Strong supportive energy for career from Saturn\'s angle'
        elif points >= 25:
            return 'Moderate support requiring additional effort'
        else:
            return 'Weak support, needs strengthening through remedies'
    
    def _assess_saturn_tenth_career_potential(self, score, planets_data, aspects_data):
        """Assess career potential from Saturn's 10th house"""
        if score >= 70 and planets_data['planet_count'] > 0:
            return 'High potential for structured career success'
        elif score >= 50:
            return 'Good potential with disciplined approach'
        else:
            return 'Requires patience and systematic development'
    
    def _identify_saturn_tenth_strengths(self, house_info, planets_data, aspects_data):
        """Identify strengths of Saturn's 10th house"""
        strengths = []
        
        if planets_data['planet_count'] > 0:
            strengths.append(f"Planetary support from {planets_data['planet_count']} planet(s)")
        
        if aspects_data['net_aspect_score'] > 2:
            strengths.append('Positive aspectual support')
        
        if house_info['lord'] in ['Saturn', 'Mars', 'Sun']:
            strengths.append('Strong natural ruler for disciplined career')
        
        return strengths if strengths else ['Natural Saturn influence provides structure']
    
    def _identify_saturn_tenth_challenges(self, house_info, planets_data, aspects_data):
        """Identify challenges of Saturn's 10th house"""
        challenges = []
        
        if planets_data['planet_count'] == 0:
            challenges.append('No direct planetary support in the house')
        
        if aspects_data['net_aspect_score'] < -2:
            challenges.append('Challenging aspectual influences')
        
        challenging_planets = [p for p in planets_data['planets'] if p['overall_effect'] == 'Challenging']
        if challenging_planets:
            challenges.append(f'Challenging influence from {len(challenging_planets)} planet(s)')
        
        return challenges if challenges else ['Minor adjustments needed for optimal results']
    
    def _get_saturn_tenth_recommendations(self, score, challenges):
        """Get recommendations for Saturn's 10th house"""
        recommendations = []
        
        if score < 50:
            recommendations.extend([
                'Focus on building career through disciplined, consistent effort',
                'Strengthen Saturn through regular spiritual practices',
                'Avoid shortcuts and build career foundation slowly'
            ])
        
        if 'No direct planetary support' in str(challenges):
            recommendations.append('Consider strengthening the house lord through appropriate remedies')
        
        if 'Challenging aspectual influences' in str(challenges):
            recommendations.append('Practice patience and persistence during challenging periods')
        
        recommendations.extend([
            'Align career goals with Saturn\'s timing and natural discipline',
            'Focus on long-term career building rather than quick gains',
            'Develop expertise through sustained effort and learning'
        ])
        
        return recommendations