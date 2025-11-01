from .base_calculator import BaseCalculator

class HouseAnalyzer(BaseCalculator):
    """Comprehensive house analyzer - reusable for any house analysis"""
    
    def __init__(self, chart_data=None, birth_data=None):
        super().__init__(chart_data or {})
        self.birth_data = birth_data
        
        # Initialize existing calculators
        from .planet_analyzer import PlanetAnalyzer
        from .house_strength_calculator import HouseStrengthCalculator
        from .yogi_calculator import YogiCalculator
        from .badhaka_calculator import BadhakaCalculator
        from .aspect_calculator import AspectCalculator
        from .gandanta_calculator import GandantaCalculator
        
        self.planet_analyzer = PlanetAnalyzer(chart_data, birth_data)
        self.house_strength_calc = HouseStrengthCalculator(chart_data)
        self.yogi_calc = YogiCalculator(chart_data)
        self.badhaka_calc = BadhakaCalculator(chart_data)
        self.aspect_calc = AspectCalculator(chart_data)
        self.gandanta_calc = GandantaCalculator(chart_data)
        
        # Get calculated data
        self.yogi_data = self.yogi_calc.calculate_yogi_points(birth_data)
        ascendant_sign = chart_data.get('houses', [{}])[0].get('sign', 1)
        self.badhaka_data = {'badhaka_lord': self.badhaka_calc.get_badhaka_lord(ascendant_sign)}
        self.gandanta_data = self.gandanta_calc.calculate_gandanta_analysis()
        
        # House classifications
        self.HOUSE_TYPES = {
            'kendra': [1, 4, 7, 10],
            'trikona': [1, 5, 9], 
            'upachaya': [3, 6, 10, 11],
            'dusthana': [6, 8, 12],
            'maraka': [2, 7],
            'badhaka_houses': {
                'movable': [11], 'fixed': [9], 'dual': [7]
            }
        }
        
        # House significances
        self.HOUSE_SIGNIFICANCES = {
            1: "Self, personality, health, appearance, vitality",
            2: "Wealth, family, speech, values, maraka",
            3: "Siblings, courage, communication, short travels",
            4: "Home, mother, education, property, happiness",
            5: "Children, creativity, intelligence, romance, dharma",
            6: "Health, enemies, service, daily work, diseases",
            7: "Marriage, partnerships, business, maraka",
            8: "Transformation, occult, longevity, inheritance, chronic illness",
            9: "Fortune, dharma, higher learning, father, luck",
            10: "Career, reputation, authority, public image",
            11: "Gains, friends, aspirations, elder siblings",
            12: "Losses, spirituality, foreign lands, expenses, hospitalization"
        }
    
    def analyze_house(self, house_number):
        """Complete analysis of any house"""
        if house_number < 1 or house_number > 12:
            raise ValueError(f'House number must be between 1 and 12, got {house_number}')
        
        if 'houses' not in self.chart_data:
            raise KeyError('Chart data missing houses information')
        
        if len(self.chart_data['houses']) < house_number:
            raise IndexError(f'House {house_number} not found in chart data')
        
        analysis = {
            'basic_info': self._get_basic_house_info(house_number),
            'house_lord_analysis': self._get_house_lord_analysis(house_number),
            'resident_planets': self._get_resident_planets_analysis(house_number),
            'aspects_received': self._get_aspects_received_analysis(house_number),
            'special_house_analysis': self._get_special_house_analysis(house_number),
            'house_strength': self._get_house_strength_analysis(house_number),
            'gandanta_analysis': self._get_house_gandanta_analysis(house_number),
            'overall_house_assessment': {}
        }
        
        # Calculate overall assessment
        analysis['overall_house_assessment'] = self._calculate_overall_house_assessment(analysis)
        
        return analysis
    
    def _get_basic_house_info(self, house_number):
        """Basic house information"""
        house_data = self.chart_data['houses'][house_number - 1]
        house_sign = house_data['sign']
        house_lord = self.get_sign_lord(house_sign)
        
        house_types = []
        if house_number in self.HOUSE_TYPES['kendra']:
            house_types.append('Kendra')
        if house_number in self.HOUSE_TYPES['trikona']:
            house_types.append('Trikona')
        if house_number in self.HOUSE_TYPES['upachaya']:
            house_types.append('Upachaya')
        if house_number in self.HOUSE_TYPES['dusthana']:
            house_types.append('Dusthana')
        if house_number in self.HOUSE_TYPES['maraka']:
            house_types.append('Maraka')
        
        return {
            'house_number': house_number,
            'house_sign': house_sign,
            'house_sign_name': self.get_sign_name(house_sign),
            'house_lord': house_lord,
            'significance': self.HOUSE_SIGNIFICANCES[house_number],
            'house_types': house_types
        }
    
    def _get_house_lord_analysis(self, house_number):
        """Complete analysis of house lord using PlanetAnalyzer"""
        house_data = self.chart_data['houses'][house_number - 1]
        house_sign = house_data['sign']
        house_lord = self.get_sign_lord(house_sign)
        
        if house_lord not in self.chart_data['planets']:
            raise KeyError(f'House lord {house_lord} not found in planets data')
        
        lord_analysis = self.planet_analyzer.analyze_planet(house_lord)
        
        # Add house-specific interpretation
        lord_analysis['house_lordship_impact'] = self._get_house_lordship_impact(house_lord, house_number, lord_analysis)
        
        return lord_analysis
    
    def _get_resident_planets_analysis(self, house_number):
        """Analysis of all planets residing in the house"""
        residents = []
        
        for planet_name, planet_data in self.chart_data['planets'].items():
            if planet_data['house'] == house_number:
                planet_analysis = self.planet_analyzer.analyze_planet(planet_name)
                planet_analysis['house_specific_impact'] = self._get_planet_house_impact(planet_name, house_number, planet_analysis)
                residents.append({
                    'planet': planet_name,
                    'analysis': planet_analysis
                })
        
        return residents
    
    def _get_aspects_received_analysis(self, house_number):
        """Analysis of aspects received by the house"""
        aspecting_planets = self.aspect_calc.get_aspecting_planets(house_number)
        aspects = []
        
        for planet_name in aspecting_planets:
            planet_data = self.chart_data['planets'][planet_name]
            planet_analysis = self.planet_analyzer.analyze_planet(planet_name)
            aspect_type = self._get_aspect_type_for_house(planet_data['house'], house_number)
            aspect_strength = self._calculate_aspect_strength_for_house(planet_name, planet_data['house'], house_number)
            
            aspects.append({
                'aspecting_planet': planet_name,
                'aspecting_from_house': planet_data['house'],
                'aspect_type': aspect_type,
                'aspect_strength': aspect_strength,
                'planet_analysis': planet_analysis,
                'house_specific_effect': self._get_aspect_house_effect(planet_name, house_number, planet_analysis)
            })
        
        return aspects
    
    def _get_special_house_analysis(self, house_number):
        """Special house analysis (Yogi, Badhaka, etc.)"""
        yogi_houses = self.yogi_data.get('yogi_houses', [])
        badhaka_houses = self.badhaka_data.get('badhaka_houses', [])
        
        # Check for dusthana cancellation
        dusthana_cancellation = None
        if house_number in [6, 8, 12]:
            house_lord = self._get_basic_house_info(house_number)['house_lord']
            lord_house = self.chart_data['planets'][house_lord]['house']
            if lord_house in [6, 8, 12]:
                dusthana_cancellation = f"Viparita Raja Yoga - {house_number}th lord in {lord_house}th house"
        
        return {
            'is_yogi_house': house_number in yogi_houses,
            'is_badhaka_house': house_number in badhaka_houses,
            'dusthana_cancellation': dusthana_cancellation,
            'special_combinations': self._get_special_house_combinations(house_number)
        }
    
    def _get_house_strength_analysis(self, house_number):
        """House strength analysis using HouseStrengthCalculator"""
        return self.house_strength_calc.calculate_house_strength(house_number)
    
    def _calculate_overall_house_assessment(self, analysis):
        """Calculate overall house assessment"""
        # Start with base house strength from HouseStrengthCalculator
        base_strength = analysis['house_strength']['total_strength']
        strength_score = base_strength
        
        # House lord dignity bonus/penalty
        lord_dignity = analysis['house_lord_analysis']['dignity_analysis']['dignity']
        if lord_dignity == 'exalted':
            strength_score += 15
        elif lord_dignity == 'own_sign':
            strength_score += 10
        elif lord_dignity == 'debilitated':
            strength_score -= 15
        elif lord_dignity == 'enemy_sign':
            strength_score -= 10
        
        # Resident planets contribution
        if analysis['resident_planets']:
            for resident in analysis['resident_planets']:
                planet_dignity = resident['analysis']['dignity_analysis']['dignity']
                if planet_dignity == 'exalted':
                    strength_score += 8
                elif planet_dignity == 'own_sign':
                    strength_score += 5
                elif planet_dignity == 'debilitated':
                    strength_score -= 8
        
        # Aspects contribution (more balanced)
        if analysis['aspects_received']:
            benefic_aspects = sum(1 for a in analysis['aspects_received'] 
                                if self._is_benefic_aspect_for_house(a))
            malefic_aspects = len(analysis['aspects_received']) - benefic_aspects
            aspect_score = (benefic_aspects * 5) - (malefic_aspects * 3)
            strength_score += aspect_score
        
        # Special combinations
        if analysis['special_house_analysis']['dusthana_cancellation']:
            strength_score += 20
        if analysis['special_house_analysis']['is_yogi_house']:
            strength_score += 15
        if analysis['special_house_analysis']['is_badhaka_house']:
            strength_score -= 8
        
        # Ensure minimum reasonable score
        strength_score = max(25, min(100, strength_score))
        
        return {
            'overall_strength_score': round(strength_score, 2),
            'overall_grade': self._get_house_grade(strength_score),
            'key_strengths': self._identify_house_strengths(analysis),
            'key_weaknesses': self._identify_house_weaknesses(analysis),
            'recommendations': self._get_house_recommendations(analysis)
        }
    
    def _get_house_lordship_impact(self, house_lord, house_number, lord_analysis):
        """Get impact of planet being lord of specific house"""
        dignity = lord_analysis['dignity_analysis']['dignity']
        house_position = lord_analysis['basic_info']['house']
        
        impact_factors = []
        
        if dignity in ['exalted', 'own_sign']:
            impact_factors.append(f"Strong {house_lord} as {house_number}th lord enhances house significations")
        elif dignity == 'debilitated':
            impact_factors.append(f"Debilitated {house_lord} as {house_number}th lord weakens house results")
        
        if house_position in self.HOUSE_TYPES['kendra']:
            impact_factors.append(f"{house_number}th lord in Kendra strengthens house")
        elif house_position in self.HOUSE_TYPES['dusthana']:
            impact_factors.append(f"{house_number}th lord in Dusthana creates challenges")
        
        return impact_factors
    
    def _get_planet_house_impact(self, planet_name, house_number, planet_analysis):
        """Get impact of planet residing in specific house"""
        dignity = planet_analysis['dignity_analysis']['dignity']
        natural_nature = self._get_natural_nature(planet_name)
        
        impact_factors = []
        
        if natural_nature == 'benefic' and house_number in [1, 4, 5, 7, 9, 10, 11]:
            impact_factors.append(f"Benefic {planet_name} in {house_number}th house brings positive results")
        elif natural_nature == 'malefic' and house_number in [3, 6, 10, 11]:
            impact_factors.append(f"Malefic {planet_name} in upachaya house {house_number} gives good results")
        elif natural_nature == 'malefic' and house_number in [1, 4, 5, 7, 8, 9, 12]:
            impact_factors.append(f"Malefic {planet_name} in {house_number}th house may create challenges")
        
        if dignity == 'exalted':
            impact_factors.append(f"Exalted {planet_name} significantly enhances {house_number}th house")
        elif dignity == 'debilitated':
            impact_factors.append(f"Debilitated {planet_name} weakens {house_number}th house significations")
        
        return impact_factors
    
    def _get_aspect_type_for_house(self, from_house, to_house):
        """Get aspect type for house"""
        if to_house >= from_house:
            aspect_number = to_house - from_house + 1
        else:
            aspect_number = (12 - from_house) + to_house + 1
        
        if aspect_number > 12:
            aspect_number = aspect_number - 12
        
        aspect_names = {
            3: '3rd aspect', 4: '4th aspect', 5: '5th aspect', 
            7: '7th aspect', 8: '8th aspect', 9: '9th aspect',
            10: '10th aspect', 11: '11th aspect'
        }
        
        return aspect_names.get(aspect_number, f'{aspect_number}th aspect')
    
    def _calculate_aspect_strength_for_house(self, planet_name, from_house, to_house):
        """Calculate aspect strength for house"""
        planet_analysis = self.planet_analyzer.analyze_planet(planet_name)
        planet_strength = planet_analysis['strength_analysis']['shadbala_rupas']
        
        if planet_strength >= 5:
            return 'Strong'
        elif planet_strength >= 3:
            return 'Medium'
        else:
            return 'Weak'
    
    def _get_aspect_house_effect(self, planet_name, house_number, planet_analysis):
        """Get effect of planet's aspect on house"""
        natural_nature = self._get_natural_nature(planet_name)
        dignity = planet_analysis['dignity_analysis']['dignity']
        
        if natural_nature == 'benefic' and dignity in ['exalted', 'own_sign']:
            return f"Highly beneficial aspect enhances {house_number}th house significations"
        elif natural_nature == 'malefic' and dignity == 'debilitated':
            return f"Weak malefic aspect has reduced negative impact on {house_number}th house"
        elif natural_nature == 'benefic':
            return f"Beneficial aspect supports {house_number}th house matters"
        else:
            return f"Malefic aspect may create challenges for {house_number}th house"
    
    def _get_special_house_combinations(self, house_number):
        """Get special combinations for house"""
        combinations = []
        
        # Check for specific yogas based on house
        if house_number == 1:
            combinations.extend(self._check_lagna_yogas())
        elif house_number == 6:
            combinations.extend(self._check_sixth_house_yogas())
        elif house_number == 8:
            combinations.extend(self._check_eighth_house_yogas())
        elif house_number == 12:
            combinations.extend(self._check_twelfth_house_yogas())
        
        return combinations
    
    def _check_lagna_yogas(self):
        """Check for Lagna-specific yogas"""
        yogas = []
        lagna_lord = self._get_basic_house_info(1)['house_lord']
        lagna_lord_house = self.chart_data['planets'][lagna_lord]['house']
        
        if lagna_lord_house in [1, 4, 7, 10]:
            yogas.append("Lagna lord in Kendra - Strong personality and health")
        elif lagna_lord_house in [5, 9]:
            yogas.append("Lagna lord in Trikona - Dharmic and fortunate life")
        
        return yogas
    
    def _check_sixth_house_yogas(self):
        """Check for 6th house specific yogas"""
        yogas = []
        sixth_lord = self._get_basic_house_info(6)['house_lord']
        sixth_lord_house = self.chart_data['planets'][sixth_lord]['house']
        
        if sixth_lord_house in [6, 8, 12]:
            yogas.append("Viparita Raja Yoga - 6th lord in dusthana gives victory over enemies")
        
        return yogas
    
    def _check_eighth_house_yogas(self):
        """Check for 8th house specific yogas"""
        yogas = []
        eighth_lord = self._get_basic_house_info(8)['house_lord']
        eighth_lord_house = self.chart_data['planets'][eighth_lord]['house']
        
        if eighth_lord_house in [6, 8, 12]:
            yogas.append("Viparita Raja Yoga - 8th lord in dusthana reduces chronic health issues")
        
        return yogas
    
    def _check_twelfth_house_yogas(self):
        """Check for 12th house specific yogas"""
        yogas = []
        twelfth_lord = self._get_basic_house_info(12)['house_lord']
        twelfth_lord_house = self.chart_data['planets'][twelfth_lord]['house']
        
        if twelfth_lord_house in [6, 8, 12]:
            yogas.append("Viparita Raja Yoga - 12th lord in dusthana reduces losses and expenses")
        
        return yogas
    
    def _get_natural_nature(self, planet_name):
        """Get natural benefic/malefic nature"""
        benefics = ['Jupiter', 'Venus', 'Mercury', 'Moon']
        malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
        
        if planet_name in benefics:
            return 'benefic'
        elif planet_name in malefics:
            return 'malefic'
        else:
            return 'neutral'
    
    def _is_benefic_aspect_for_house(self, aspect):
        """Check if aspect is benefic for house"""
        planet_name = aspect['aspecting_planet']
        natural_nature = self._get_natural_nature(planet_name)
        dignity = aspect['planet_analysis']['dignity_analysis']['dignity']
        
        if natural_nature == 'benefic' and dignity in ['exalted', 'own_sign']:
            return True
        elif natural_nature == 'malefic' and dignity == 'debilitated':
            return True
        elif natural_nature == 'benefic':
            return True
        else:
            return False
    
    def _get_house_grade(self, score):
        """Get house grade from score"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        elif score >= 30:
            return 'D'
        else:
            return 'F'
    
    def _identify_house_strengths(self, analysis):
        """Identify key house strengths"""
        strengths = []
        
        lord_analysis = analysis['house_lord_analysis']
        if lord_analysis['overall_assessment']['overall_strength_score'] >= 70:
            strengths.append(f"Strong house lord: {lord_analysis['basic_info']['planet']}")
        
        if analysis['special_house_analysis']['dusthana_cancellation']:
            strengths.append("Viparita Raja Yoga present")
        
        if analysis['special_house_analysis']['is_yogi_house']:
            strengths.append("Yogi house - spiritually beneficial")
        
        benefic_aspects = [a for a in analysis['aspects_received'] if self._is_benefic_aspect_for_house(a)]
        if len(benefic_aspects) > len(analysis['aspects_received']) / 2:
            strengths.append("Predominantly benefic aspects")
        
        return strengths
    
    def _identify_house_weaknesses(self, analysis):
        """Identify key house weaknesses"""
        weaknesses = []
        
        lord_analysis = analysis['house_lord_analysis']
        if lord_analysis['overall_assessment']['overall_strength_score'] < 40:
            weaknesses.append(f"Weak house lord: {lord_analysis['basic_info']['planet']}")
        
        if analysis['special_house_analysis']['is_badhaka_house']:
            weaknesses.append("Badhaka house - potential obstacles")
        
        malefic_aspects = [a for a in analysis['aspects_received'] if not self._is_benefic_aspect_for_house(a)]
        if len(malefic_aspects) > len(analysis['aspects_received']) / 2:
            weaknesses.append("Predominantly malefic aspects")
        
        return weaknesses
    
    def _get_house_recommendations(self, analysis):
        """Get recommendations for house strengthening"""
        recommendations = []
        
        lord_analysis = analysis['house_lord_analysis']
        house_lord = lord_analysis['basic_info']['planet']
        
        if lord_analysis['overall_assessment']['overall_strength_score'] < 50:
            recommendations.append(f"Strengthen house lord {house_lord} through appropriate remedies")
        
        if analysis['special_house_analysis']['is_badhaka_house']:
            recommendations.append("Perform remedies to mitigate Badhaka effects")
        
        if not recommendations:
            recommendations.append("House is well-placed, maintain positive practices")
        
        return recommendations
    
    def _get_house_gandanta_analysis(self, house_number):
        """Get Gandanta analysis for house cusp and occupants"""
        analysis = {
            'house_cusp_gandanta': self._check_house_cusp_gandanta(house_number),
            'resident_planets_gandanta': [],
            'house_lord_gandanta': self._check_house_lord_gandanta(house_number),
            'overall_house_gandanta_impact': 'None'
        }
        
        # Check resident planets for Gandanta
        for planet_name, planet_data in self.chart_data['planets'].items():
            if planet_data['house'] == house_number:
                gandanta_info = self.gandanta_calc._check_planet_gandanta(planet_name, planet_data['longitude'])
                if gandanta_info['is_gandanta']:
                    analysis['resident_planets_gandanta'].append({
                        'planet': planet_name,
                        'gandanta_info': gandanta_info
                    })
        
        # Determine overall impact
        impact_factors = []
        if analysis['house_cusp_gandanta']['is_gandanta']:
            impact_factors.append('House cusp in Gandanta')
        if analysis['house_lord_gandanta']['is_gandanta']:
            impact_factors.append('House lord in Gandanta')
        if analysis['resident_planets_gandanta']:
            impact_factors.append(f"{len(analysis['resident_planets_gandanta'])} resident planets in Gandanta")
        
        if len(impact_factors) >= 2:
            analysis['overall_house_gandanta_impact'] = 'High'
        elif len(impact_factors) == 1:
            analysis['overall_house_gandanta_impact'] = 'Medium'
        else:
            analysis['overall_house_gandanta_impact'] = 'None'
        
        analysis['impact_summary'] = impact_factors
        
        return analysis
    
    def _check_house_cusp_gandanta(self, house_number):
        """Check if house cusp is in Gandanta"""
        house_data = self.chart_data['houses'][house_number - 1]
        cusp_longitude = house_data.get('cusp_longitude')
        
        if cusp_longitude is not None:
            gandanta_info = self.gandanta_calc._check_planet_gandanta(f'{house_number}th House Cusp', cusp_longitude)
            if gandanta_info['is_gandanta']:
                return {
                    'is_gandanta': True,
                    'gandanta_info': gandanta_info
                }
        
        return {'is_gandanta': False}
    
    def _check_house_lord_gandanta(self, house_number):
        """Check if house lord is in Gandanta"""
        house_lord = self._get_basic_house_info(house_number)['house_lord']
        lord_longitude = self.chart_data['planets'][house_lord]['longitude']
        
        gandanta_info = self.gandanta_calc._check_planet_gandanta(house_lord, lord_longitude)
        if gandanta_info['is_gandanta']:
            return {
                'is_gandanta': True,
                'planet': house_lord,
                'gandanta_info': gandanta_info
            }
        
        return {'is_gandanta': False}
    
