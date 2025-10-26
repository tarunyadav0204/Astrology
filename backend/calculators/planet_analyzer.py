from .base_calculator import BaseCalculator

class PlanetAnalyzer(BaseCalculator):
    """Comprehensive planet analyzer - reusable for any planet analysis"""
    
    def __init__(self, chart_data=None):
        super().__init__(chart_data or {})
        
        # Initialize existing calculators
        from .shadbala_calculator import ShadbalaCalculator
        from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
        
        self.shadbala_calc = ShadbalaCalculator(chart_data)
        self.dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        
        # Get calculated data
        self.shadbala_data = self.shadbala_calc.calculate_shadbala()
        self.dignities_data = self.dignities_calc.calculate_planetary_dignities()
        
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
        
        # Nakshatra data for friendship analysis
        self.NAKSHATRA_LORDS = {
            1: 'Ketu', 2: 'Venus', 3: 'Sun', 4: 'Moon', 5: 'Mars', 6: 'Rahu', 7: 'Jupiter',
            8: 'Saturn', 9: 'Mercury', 10: 'Ketu', 11: 'Venus', 12: 'Sun', 13: 'Moon',
            14: 'Mars', 15: 'Rahu', 16: 'Jupiter', 17: 'Saturn', 18: 'Mercury', 19: 'Ketu',
            20: 'Venus', 21: 'Sun', 22: 'Moon', 23: 'Mars', 24: 'Rahu', 25: 'Jupiter',
            26: 'Saturn', 27: 'Mercury'
        }
    
    def analyze_planet(self, planet_name):
        """Complete analysis of any planet"""
        if planet_name not in self.chart_data.get('planets', {}):
            return {'error': f'Planet {planet_name} not found in chart'}
        
        planet_data = self.chart_data['planets'][planet_name]
        
        analysis = {
            'basic_info': self._get_basic_info(planet_name, planet_data),
            'dignity_analysis': self._get_dignity_analysis(planet_name),
            'strength_analysis': self._get_strength_analysis(planet_name),
            'house_position_analysis': self._get_house_position_analysis(planet_data),
            'friendship_analysis': self._get_friendship_analysis(planet_name, planet_data),
            'special_lordships': self._get_special_lordships(planet_name),
            'conjunctions': self._get_conjunctions(planet_name, planet_data),
            'combustion_status': self._get_combustion_status(planet_name),
            'retrograde_analysis': self._get_retrograde_analysis(planet_name, planet_data),
            'aspects_received': self._get_aspects_received(planet_name, planet_data),
            'overall_assessment': {}
        }
        
        # Calculate overall assessment
        analysis['overall_assessment'] = self._calculate_overall_assessment(analysis)
        
        return analysis
    
    def _get_basic_info(self, planet_name, planet_data):
        """Basic planet information"""
        return {
            'planet': planet_name,
            'sign': planet_data.get('sign', 0),
            'sign_name': self.get_sign_name(planet_data.get('sign', 0)),
            'house': planet_data.get('house', 1),
            'degree': round(planet_data.get('degree', 0), 2),
            'longitude': round(planet_data.get('longitude', 0), 2),
            'nakshatra': self._get_nakshatra(planet_data.get('longitude', 0))
        }
    
    def _get_dignity_analysis(self, planet_name):
        """Planetary dignity analysis"""
        dignity_data = self.dignities_data.get(planet_name, {})
        
        return {
            'dignity': dignity_data.get('dignity', 'neutral'),
            'functional_nature': dignity_data.get('functional_nature', 'neutral'),
            'strength_multiplier': dignity_data.get('strength_multiplier', 1.0),
            'states': dignity_data.get('states', []),
            'dignity_description': self._get_dignity_description(dignity_data.get('dignity', 'neutral'))
        }
    
    def _get_strength_analysis(self, planet_name):
        """Shadbala strength analysis"""
        shadbala_data = self.shadbala_data.get(planet_name, {})
        
        return {
            'shadbala_rupas': shadbala_data.get('total_rupas', 0),
            'shadbala_points': shadbala_data.get('total_points', 0),
            'shadbala_grade': shadbala_data.get('grade', 'Average'),
            'strength_components': shadbala_data.get('components', {}),
            'strength_interpretation': self._interpret_shadbala_strength(shadbala_data.get('total_rupas', 0))
        }
    
    def _get_house_position_analysis(self, planet_data):
        """House position analysis"""
        house = planet_data.get('house', 1)
        
        house_types = []
        if house in self.HOUSE_TYPES['kendra']:
            house_types.append('Kendra')
        if house in self.HOUSE_TYPES['trikona']:
            house_types.append('Trikona')
        if house in self.HOUSE_TYPES['upachaya']:
            house_types.append('Upachaya')
        if house in self.HOUSE_TYPES['dusthana']:
            house_types.append('Dusthana')
        if house in self.HOUSE_TYPES['maraka']:
            house_types.append('Maraka')
        
        return {
            'house_number': house,
            'house_types': house_types,
            'house_strength': self._calculate_house_strength(house),
            'house_significance': self._get_house_significance(house)
        }
    
    def _get_friendship_analysis(self, planet_name, planet_data):
        """5-fold friendship analysis"""
        sign = planet_data.get('sign', 0)
        longitude = planet_data.get('longitude', 0)
        nakshatra_num = self._get_nakshatra_number(longitude)
        nakshatra_lord = self.NAKSHATRA_LORDS.get(nakshatra_num, 'Unknown')
        
        # Get sign lord
        sign_lord = self.get_sign_lord(sign)
        
        # Simplified friendship calculation for now
        # friendship_data = self.friendship_calc.calculate_friendship({'planets': {planet_name: planet_data}})
        
        return {
            'sign_lord': sign_lord,
            'sign_friendship': self._get_friendship_level(planet_name, sign_lord),
            'nakshatra_number': nakshatra_num,
            'nakshatra_lord': nakshatra_lord,
            'nakshatra_friendship': self._get_friendship_level(planet_name, nakshatra_lord),
            'overall_friendship_status': self._calculate_overall_friendship(planet_name, sign_lord, nakshatra_lord)
        }
    
    def _get_special_lordships(self, planet_name):
        """Special lordship analysis (Yogi, Badhaka, etc.)"""
        # This would integrate with YogiCalculator and BadhakaCalculator
        # For now, returning basic structure
        return {
            'is_yogi_lord': False,
            'is_avayogi_lord': False,
            'is_dagdha_lord': False,
            'is_tithi_shunya_lord': False,
            'is_badhaka_lord': False,
            'special_roles': []
        }
    
    def _get_conjunctions(self, planet_name, planet_data):
        """Conjunction analysis"""
        house = planet_data.get('house', 1)
        conjunctions = []
        
        planets = self.chart_data.get('planets', {})
        for other_planet, other_data in planets.items():
            if other_planet != planet_name and other_data.get('house') == house:
                conjunction_type = self._classify_conjunction(planet_name, other_planet)
                conjunctions.append({
                    'planet': other_planet,
                    'type': conjunction_type,
                    'orb': self._calculate_orb(planet_data.get('longitude', 0), other_data.get('longitude', 0)),
                    'effect': self._get_conjunction_effect(planet_name, other_planet, conjunction_type)
                })
        
        return {
            'has_conjunctions': len(conjunctions) > 0,
            'conjunction_count': len(conjunctions),
            'conjunctions': conjunctions,
            'overall_conjunction_effect': self._assess_overall_conjunction_effect(conjunctions)
        }
    
    def _get_combustion_status(self, planet_name):
        """Combustion analysis"""
        if planet_name == 'Sun':
            return {
                'is_combust': False, 
                'is_cazimi': False,
                'status': 'Not applicable - Sun cannot be combust',
                'effect': 'Sun cannot be combust'
            }
        
        dignity_data = self.dignities_data.get(planet_name, {})
        combustion_status = dignity_data.get('combustion_status', 'normal')
        
        return {
            'is_combust': combustion_status == 'combust',
            'is_cazimi': combustion_status == 'cazimi',
            'status': combustion_status,
            'effect': self._get_combustion_effect(combustion_status)
        }
    
    def _get_retrograde_analysis(self, planet_name, planet_data):
        """Retrograde analysis"""
        is_retrograde = planet_data.get('retrograde', False)
        
        return {
            'is_retrograde': is_retrograde,
            'effect': self._get_retrograde_effect(planet_name, is_retrograde) if is_retrograde else 'Normal motion'
        }
    
    def _get_aspects_received(self, planet_name, planet_data):
        """Aspects received by the planet"""
        house = planet_data.get('house', 1)
        aspects = []
        
        planets = self.chart_data.get('planets', {})
        for other_planet, other_data in planets.items():
            if other_planet != planet_name:
                aspect_houses = self._get_aspect_houses(other_planet, other_data.get('house', 1))
                if house in aspect_houses:
                    aspect_effect_data = self._get_aspect_effect(other_planet, planet_name)
                    aspects.append({
                        'aspecting_planet': other_planet,
                        'aspect_type': self._get_aspect_type(other_data.get('house', 1), house),
                        'aspect_strength': self._calculate_aspect_strength(other_planet, other_data.get('house', 1), house),
                        'effect': aspect_effect_data['effect'],
                        'effect_score': aspect_effect_data['score'],
                        'calculation_details': aspect_effect_data['calculation_details']
                    })
        
        return {
            'has_aspects': len(aspects) > 0,
            'aspect_count': len(aspects),
            'aspects': aspects,
            'benefic_aspects': [a for a in aspects if self._is_benefic_aspect(a)],
            'malefic_aspects': [a for a in aspects if not self._is_benefic_aspect(a)]
        }
    
    def _calculate_overall_assessment(self, analysis):
        """Calculate overall planet assessment"""
        strength_score = 0
        
        # Dignity contribution
        dignity = analysis['dignity_analysis']['dignity']
        if dignity == 'exalted':
            strength_score += 30
        elif dignity == 'own_sign':
            strength_score += 20
        elif dignity == 'moolatrikona':
            strength_score += 25
        elif dignity == 'debilitated':
            strength_score -= 25
        
        # Shadbala contribution
        shadbala_rupas = analysis['strength_analysis']['shadbala_rupas']
        strength_score += min(shadbala_rupas * 5, 30)
        
        # House position contribution
        house_types = analysis['house_position_analysis']['house_types']
        if 'Kendra' in house_types:
            strength_score += 15
        if 'Trikona' in house_types:
            strength_score += 20
        if 'Dusthana' in house_types:
            strength_score -= 10
        
        # Combustion penalty
        if analysis['combustion_status']['is_combust']:
            strength_score -= 20
        elif analysis['combustion_status']['is_cazimi']:
            strength_score += 15
        
        # Conjunction effects
        conjunction_effect = analysis['conjunctions']['overall_conjunction_effect']
        if conjunction_effect == 'beneficial':
            strength_score += 10
        elif conjunction_effect == 'harmful':
            strength_score -= 10
        
        # Normalize score
        strength_score = max(0, min(100, strength_score))
        
        return {
            'overall_strength_score': strength_score,
            'overall_grade': self._get_overall_grade(strength_score),
            'key_strengths': self._identify_key_strengths(analysis),
            'key_weaknesses': self._identify_key_weaknesses(analysis),
            'recommendations': self._get_recommendations(analysis)
        }
    
    # Helper methods
    def _get_nakshatra(self, longitude):
        """Get nakshatra from longitude"""
        nakshatra_num = int(longitude / 13.333333) + 1
        nakshatra_names = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        return nakshatra_names[min(nakshatra_num - 1, 26)]
    
    def _get_nakshatra_number(self, longitude):
        """Get nakshatra number from longitude"""
        return int(longitude / 13.333333) + 1
    
    def _get_dignity_description(self, dignity):
        """Get dignity description"""
        descriptions = {
            'exalted': 'Planet is in highest dignity, maximum positive results',
            'own_sign': 'Planet is comfortable and strong in own sign',
            'moolatrikona': 'Planet is in root trine, very favorable',
            'debilitated': 'Planet is weakened, challenges expected',
            'neutral': 'Planet is in neutral dignity'
        }
        return descriptions.get(dignity, 'Unknown dignity')
    
    def _interpret_shadbala_strength(self, rupas):
        """Interpret Shadbala strength"""
        if rupas >= 6:
            return 'Excellent strength, highly capable of giving results'
        elif rupas >= 4.5:
            return 'Good strength, capable of positive results'
        elif rupas >= 3:
            return 'Average strength, moderate results expected'
        else:
            return 'Weak strength, may struggle to give results'
    
    def _calculate_house_strength(self, house):
        """Calculate house strength (simplified)"""
        if house in [1, 4, 7, 10]:
            return 'Strong (Kendra)'
        elif house in [1, 5, 9]:
            return 'Excellent (Trikona)'
        elif house in [3, 6, 10, 11]:
            return 'Growing (Upachaya)'
        else:
            return 'Moderate'
    
    def _get_house_significance(self, house):
        """Get house significance"""
        significances = {
            1: 'Self, personality, health, appearance',
            2: 'Wealth, family, speech, values',
            3: 'Siblings, courage, communication, short travels',
            4: 'Home, mother, education, property',
            5: 'Children, creativity, intelligence, romance',
            6: 'Health, enemies, service, daily work',
            7: 'Marriage, partnerships, business',
            8: 'Transformation, occult, longevity, inheritance',
            9: 'Fortune, dharma, higher learning, father',
            10: 'Career, reputation, authority, public image',
            11: 'Gains, friends, aspirations, elder siblings',
            12: 'Losses, spirituality, foreign lands, expenses'
        }
        return significances.get(house, 'Unknown house')
    
    def _get_friendship_level(self, planet1, planet2):
        """Get friendship level between planets"""
        # Simplified friendship matrix
        friendships = {
            'Sun': {'friends': ['Moon', 'Mars', 'Jupiter'], 'enemies': ['Venus', 'Saturn']},
            'Moon': {'friends': ['Sun', 'Mercury'], 'enemies': []},
            'Mars': {'friends': ['Sun', 'Moon', 'Jupiter'], 'enemies': ['Mercury']},
            'Mercury': {'friends': ['Sun', 'Venus'], 'enemies': ['Moon']},
            'Jupiter': {'friends': ['Sun', 'Moon', 'Mars'], 'enemies': ['Mercury', 'Venus']},
            'Venus': {'friends': ['Mercury', 'Saturn'], 'enemies': ['Sun', 'Moon']},
            'Saturn': {'friends': ['Mercury', 'Venus'], 'enemies': ['Sun', 'Moon', 'Mars']}
        }
        
        if planet2 in friendships.get(planet1, {}).get('friends', []):
            return 'friend'
        elif planet2 in friendships.get(planet1, {}).get('enemies', []):
            return 'enemy'
        else:
            return 'neutral'
    
    def _calculate_overall_friendship(self, planet, sign_lord, nakshatra_lord):
        """Calculate overall friendship status"""
        sign_friendship = self._get_friendship_level(planet, sign_lord)
        nakshatra_friendship = self._get_friendship_level(planet, nakshatra_lord)
        
        if sign_friendship == 'friend' and nakshatra_friendship == 'friend':
            return 'Very Favorable'
        elif sign_friendship == 'enemy' and nakshatra_friendship == 'enemy':
            return 'Very Unfavorable'
        elif sign_friendship == 'friend' or nakshatra_friendship == 'friend':
            return 'Favorable'
        elif sign_friendship == 'enemy' or nakshatra_friendship == 'enemy':
            return 'Unfavorable'
        else:
            return 'Neutral'
    
    def _classify_conjunction(self, planet1, planet2):
        """Classify conjunction as benefic or malefic"""
        benefics = ['Jupiter', 'Venus', 'Mercury', 'Moon']
        malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
        
        if planet1 in benefics and planet2 in benefics:
            return 'benefic'
        elif planet1 in malefics and planet2 in malefics:
            return 'malefic'
        else:
            return 'mixed'
    
    def _calculate_orb(self, long1, long2):
        """Calculate orb between two planets"""
        diff = abs(long1 - long2)
        return min(diff, 360 - diff)
    
    def _get_conjunction_effect(self, planet1, planet2, conjunction_type):
        """Get conjunction effect"""
        if conjunction_type == 'benefic':
            return 'Mutually supportive, enhances positive qualities'
        elif conjunction_type == 'malefic':
            return 'May create challenges, requires careful handling'
        else:
            return 'Mixed results, depends on overall chart strength'
    
    def _assess_overall_conjunction_effect(self, conjunctions):
        """Assess overall conjunction effect"""
        if not conjunctions:
            return 'none'
        
        benefic_count = sum(1 for c in conjunctions if c['type'] == 'benefic')
        malefic_count = sum(1 for c in conjunctions if c['type'] == 'malefic')
        
        if benefic_count > malefic_count:
            return 'beneficial'
        elif malefic_count > benefic_count:
            return 'harmful'
        else:
            return 'mixed'
    
    def _get_combustion_effect(self, status):
        """Get combustion effect"""
        effects = {
            'combust': 'Planet is weakened by Sun, may struggle to express qualities',
            'cazimi': 'Planet is empowered by Sun, enhanced expression of qualities',
            'normal': 'No combustion effects'
        }
        return effects.get(status, 'Unknown status')
    
    def _get_retrograde_effect(self, planet, is_retrograde):
        """Get retrograde effect"""
        if not is_retrograde:
            return 'Normal motion'
        
        effects = {
            'Mercury': 'Communication and thinking may be introspective',
            'Venus': 'Relationships and values may need review',
            'Mars': 'Energy and action may be redirected inward',
            'Jupiter': 'Wisdom and expansion may be internalized',
            'Saturn': 'Discipline and structure may be reconsidered'
        }
        return effects.get(planet, 'Retrograde motion affects planet expression')
    
    def _get_aspect_houses(self, planet, from_house):
        """Get houses aspected by planet using proper Vedic aspects"""
        aspected_houses = []
        
        # Rahu and Ketu have special aspects only (3rd and 11th)
        if planet in ['Rahu', 'Ketu']:
            # Rahu and Ketu aspect 3rd and 11th houses from their position
            third_house = (from_house + 2) % 12
            if third_house == 0:
                third_house = 12
            eleventh_house = (from_house + 10) % 12
            if eleventh_house == 0:
                eleventh_house = 12
            aspected_houses.extend([third_house, eleventh_house])
        else:
            # All other planets aspect 7th house from their position
            seventh_house = (from_house + 6) % 12
            if seventh_house == 0:
                seventh_house = 12
            aspected_houses.append(seventh_house)
            
            # Special aspects for specific planets
            if planet == 'Mars':
                # Mars aspects 4th and 8th houses from its position
                fourth_house = (from_house + 3) % 12
                if fourth_house == 0:
                    fourth_house = 12
                eighth_house = (from_house + 7) % 12
                if eighth_house == 0:
                    eighth_house = 12
                aspected_houses.extend([fourth_house, eighth_house])
                
            elif planet == 'Jupiter':
                # Jupiter aspects 5th and 9th houses from its position
                fifth_house = (from_house + 4) % 12
                if fifth_house == 0:
                    fifth_house = 12
                ninth_house = (from_house + 8) % 12
                if ninth_house == 0:
                    ninth_house = 12
                aspected_houses.extend([fifth_house, ninth_house])
                
            elif planet == 'Saturn':
                # Saturn aspects 3rd and 10th houses from its position
                third_house = (from_house + 2) % 12
                if third_house == 0:
                    third_house = 12
                tenth_house = (from_house + 9) % 12
                if tenth_house == 0:
                    tenth_house = 12
                aspected_houses.extend([third_house, tenth_house])
        
        return aspected_houses
    
    def _get_aspect_type(self, from_house, to_house):
        """Get aspect type based on house difference"""
        # Calculate the aspect number correctly
        if to_house >= from_house:
            aspect_number = to_house - from_house + 1
        else:
            aspect_number = (12 - from_house) + to_house + 1
        
        if aspect_number > 12:
            aspect_number = aspect_number - 12
        
        aspect_names = {
            3: '3rd aspect',
            4: '4th aspect',
            5: '5th aspect', 
            7: '7th aspect',
            8: '8th aspect',
            9: '9th aspect',
            10: '10th aspect',
            11: '11th aspect'
        }
        
        return aspect_names.get(aspect_number, f'{aspect_number}th aspect')
    
    def _calculate_aspect_strength(self, planet, from_house, to_house):
        """Calculate aspect strength"""
        # Simplified aspect strength
        return 'Medium'
    
    def _get_aspect_effect(self, aspecting_planet, aspected_planet):
        """Get comprehensive aspect effect with detailed calculation breakdown"""
        aspecting_data = self.chart_data.get('planets', {}).get(aspecting_planet, {})
        aspecting_house = aspecting_data.get('house', 1)
        
        # Get ascendant for functional benefic/malefic calculation
        ascendant_sign = int(self.chart_data.get('ascendant', 0) / 30)
        ascendant_name = self.get_sign_name(ascendant_sign)
        
        effect_score = 0
        calculation_details = []
        
        # 1. Natural benefic/malefic nature
        natural_benefics = ['Jupiter', 'Venus']
        natural_malefics = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
        conditional_benefics = ['Mercury', 'Moon']
        
        if aspecting_planet in natural_benefics:
            effect_score += 2
            calculation_details.append(f"Natural benefic ({aspecting_planet}): +2 points")
        elif aspecting_planet in natural_malefics:
            effect_score -= 2
            calculation_details.append(f"Natural malefic ({aspecting_planet}): -2 points")
        elif aspecting_planet in conditional_benefics:
            effect_score += 1
            calculation_details.append(f"Conditional benefic ({aspecting_planet}): +1 point")
        
        # 2. Functional benefic/malefic based on ascendant
        functional_nature = self._get_functional_nature(aspecting_planet, ascendant_sign)
        if functional_nature == 'benefic':
            effect_score += 2
            calculation_details.append(f"Functional benefic for {ascendant_name} ascendant: +2 points")
        elif functional_nature == 'malefic':
            effect_score -= 2
            calculation_details.append(f"Functional malefic for {ascendant_name} ascendant: -2 points")
        else:
            calculation_details.append(f"Neutral functional nature for {ascendant_name} ascendant: 0 points")
        
        # 3. House placement of aspecting planet
        house_effect = self._get_house_effect(aspecting_house)
        effect_score += house_effect['score']
        calculation_details.append(f"House {aspecting_house} placement ({house_effect['description']}): {house_effect['score']:+d} points")
        
        # 4. Dignity of aspecting planet
        dignity_data = self.dignities_data.get(aspecting_planet, {})
        dignity = dignity_data.get('dignity', 'neutral')
        
        if dignity == 'exalted':
            effect_score += 3
            calculation_details.append(f"Exalted dignity: +3 points")
        elif dignity == 'own_sign':
            effect_score += 2
            calculation_details.append(f"Own sign dignity: +2 points")
        elif dignity == 'moolatrikona':
            effect_score += 2
            calculation_details.append(f"Moolatrikona dignity: +2 points")
        elif dignity == 'debilitated':
            effect_score -= 3
            calculation_details.append(f"Debilitated dignity: -3 points")
        else:
            calculation_details.append(f"Neutral dignity: 0 points")
        
        # 5. Combustion status
        combustion_status = dignity_data.get('combustion_status', 'normal')
        if combustion_status == 'combust':
            effect_score -= 2
            calculation_details.append(f"Planet is combust: -2 points")
        elif combustion_status == 'cazimi':
            effect_score += 2
            calculation_details.append(f"Planet is cazimi: +2 points")
        else:
            calculation_details.append(f"No combustion effects: 0 points")
        
        # 6. Shadbala strength
        shadbala_data = self.shadbala_data.get(aspecting_planet, {})
        shadbala_rupas = shadbala_data.get('total_rupas', 0)
        
        if shadbala_rupas >= 6:
            effect_score += 2
            calculation_details.append(f"Strong Shadbala ({shadbala_rupas:.2f} rupas): +2 points")
        elif shadbala_rupas >= 4:
            effect_score += 1
            calculation_details.append(f"Good Shadbala ({shadbala_rupas:.2f} rupas): +1 point")
        elif shadbala_rupas < 3:
            effect_score -= 1
            calculation_details.append(f"Weak Shadbala ({shadbala_rupas:.2f} rupas): -1 point")
        else:
            calculation_details.append(f"Average Shadbala ({shadbala_rupas:.2f} rupas): 0 points")
        
        # 7. Retrograde status (for applicable planets)
        if aspecting_data.get('retrograde', False) and aspecting_planet not in ['Sun', 'Moon', 'Rahu', 'Ketu']:
            if aspecting_planet in ['Jupiter', 'Venus']:
                effect_score += 1
                calculation_details.append(f"Retrograde motion (beneficial for {aspecting_planet}): +1 point")
            else:
                effect_score -= 1
                calculation_details.append(f"Retrograde motion (challenging for {aspecting_planet}): -1 point")
        else:
            calculation_details.append(f"Direct motion: 0 points")
        
        # Add total score
        calculation_details.append(f"\nTotal Score: {effect_score}")
        
        # Determine overall effect
        if effect_score >= 3:
            overall_effect = 'Highly Beneficial'
            calculation_details.append("Result: Highly Beneficial (Score ≥ 3)")
        elif effect_score >= 1:
            overall_effect = 'Beneficial'
            calculation_details.append("Result: Beneficial (Score 1-2)")
        elif effect_score <= -3:
            overall_effect = 'Highly Malefic'
            calculation_details.append("Result: Highly Malefic (Score ≤ -3)")
        elif effect_score <= -1:
            overall_effect = 'Malefic'
            calculation_details.append("Result: Malefic (Score -1 to -2)")
        else:
            overall_effect = 'Neutral'
            calculation_details.append("Result: Neutral (Score -0.9 to 0.9)")
        
        return {
            'effect': overall_effect,
            'score': round(effect_score, 1),
            'calculation_details': calculation_details
        }
    
    def _get_functional_nature(self, planet, ascendant_sign):
        """Get functional benefic/malefic nature based on ascendant"""
        # Simplified functional benefic/malefic system
        functional_benefics = {
            0: ['Sun', 'Mars', 'Jupiter'],  # Aries
            1: ['Mercury', 'Venus', 'Saturn'],  # Taurus
            2: ['Mercury', 'Venus'],  # Gemini
            3: ['Moon', 'Mars'],  # Cancer
            4: ['Sun', 'Mars'],  # Leo
            5: ['Mercury', 'Venus'],  # Virgo
            6: ['Venus', 'Saturn'],  # Libra
            7: ['Moon', 'Jupiter'],  # Scorpio
            8: ['Sun', 'Mars', 'Jupiter'],  # Sagittarius
            9: ['Venus', 'Saturn'],  # Capricorn
            10: ['Venus', 'Saturn'],  # Aquarius
            11: ['Sun', 'Mars', 'Jupiter']  # Pisces
        }
        
        functional_malefics = {
            0: ['Mercury', 'Venus', 'Saturn'],
            1: ['Sun', 'Mars', 'Jupiter'],
            2: ['Mars', 'Jupiter'],
            3: ['Sun', 'Venus', 'Saturn'],
            4: ['Mercury', 'Venus', 'Saturn'],
            5: ['Sun', 'Mars', 'Jupiter'],
            6: ['Sun', 'Mars', 'Jupiter'],
            7: ['Sun', 'Venus', 'Saturn'],
            8: ['Mercury', 'Venus', 'Saturn'],
            9: ['Sun', 'Mars', 'Jupiter'],
            10: ['Sun', 'Mars', 'Jupiter'],
            11: ['Mercury', 'Venus', 'Saturn']
        }
        
        if planet in functional_benefics.get(ascendant_sign, []):
            return 'benefic'
        elif planet in functional_malefics.get(ascendant_sign, []):
            return 'malefic'
        else:
            return 'neutral'
    
    def _get_house_effect(self, house):
        """Get effect of planet's house placement"""
        if house in [1, 4, 7, 10]:  # Kendra
            return {'score': 2, 'description': 'Kendra house'}
        elif house in [1, 5, 9]:  # Trikona
            return {'score': 3, 'description': 'Trikona house'}
        elif house in [3, 6, 10, 11]:  # Upachaya
            return {'score': 1, 'description': 'Upachaya house'}
        elif house in [6, 8, 12]:  # Dusthana
            return {'score': -2, 'description': 'Dusthana house'}
        elif house in [2, 7]:  # Maraka
            return {'score': -1, 'description': 'Maraka house'}
        else:
            return {'score': 0, 'description': 'Neutral house'}
    
    def _is_benefic_aspect(self, aspect):
        """Check if aspect is benefic based on comprehensive analysis"""
        effect = aspect['effect']
        return 'beneficial' in effect.lower() or aspect.get('effect_score', 0) > 0
    
    def _get_overall_grade(self, score):
        """Get overall grade from score"""
        if score >= 80:
            return 'Excellent'
        elif score >= 65:
            return 'Very Good'
        elif score >= 50:
            return 'Good'
        elif score >= 35:
            return 'Average'
        else:
            return 'Weak'
    
    def _identify_key_strengths(self, analysis):
        """Identify key strengths"""
        strengths = []
        
        if analysis['dignity_analysis']['dignity'] in ['exalted', 'own_sign', 'moolatrikona']:
            strengths.append(f"Strong dignity: {analysis['dignity_analysis']['dignity']}")
        
        if analysis['strength_analysis']['shadbala_rupas'] >= 5:
            strengths.append(f"Good Shadbala strength: {analysis['strength_analysis']['shadbala_rupas']:.1f} rupas")
        
        house_types = analysis['house_position_analysis']['house_types']
        if 'Kendra' in house_types or 'Trikona' in house_types:
            strengths.append(f"Favorable house position: {', '.join(house_types)}")
        
        if analysis['combustion_status']['is_cazimi']:
            strengths.append("Cazimi status enhances planet")
        
        return strengths
    
    def _identify_key_weaknesses(self, analysis):
        """Identify key weaknesses"""
        weaknesses = []
        
        if analysis['dignity_analysis']['dignity'] == 'debilitated':
            weaknesses.append("Debilitated dignity")
        
        if analysis['strength_analysis']['shadbala_rupas'] < 3:
            weaknesses.append(f"Weak Shadbala strength: {analysis['strength_analysis']['shadbala_rupas']:.1f} rupas")
        
        if 'Dusthana' in analysis['house_position_analysis']['house_types']:
            weaknesses.append("Placed in Dusthana house")
        
        if analysis['combustion_status']['is_combust']:
            weaknesses.append("Combust by Sun")
        
        return weaknesses
    
    def _get_recommendations(self, analysis):
        """Get recommendations for planet strengthening"""
        recommendations = []
        
        if analysis['dignity_analysis']['dignity'] == 'debilitated':
            recommendations.append("Consider remedies for debilitated planet")
        
        if analysis['strength_analysis']['shadbala_rupas'] < 4:
            recommendations.append("Strengthen planet through appropriate remedies")
        
        if analysis['combustion_status']['is_combust']:
            recommendations.append("Wait for planet to move away from Sun for better results")
        
        if not recommendations:
            recommendations.append("Planet is well-placed, maintain positive practices")
        
        return recommendations