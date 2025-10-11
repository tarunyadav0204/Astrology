import swisseph as swe
from datetime import datetime, timedelta
from .house_significations import HOUSE_SIGNIFICATIONS, SIGN_LORDS, NATURAL_BENEFICS, NATURAL_MALEFICS, EXALTATION_SIGNS, DEBILITATION_SIGNS

class UniversalHouseAnalyzer:
    """Universal House Analyzer for all 12 houses with comprehensive analysis"""
    
    def __init__(self, birth_data, chart_data):
        self.birth_data = birth_data
        self.chart_data = chart_data
        
    def analyze_all_houses(self):
        """Analyze all 12 houses comprehensively"""
        house_analyses = {}
        
        for house_num in range(1, 13):
            house_analyses[house_num] = self.analyze_house(house_num)
            
        return house_analyses
    
    def analyze_house(self, house_num):
        """Comprehensive analysis of a specific house"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        house_lord = SIGN_LORDS[house_sign]
        
        analysis = {
            'house_number': house_num,
            'house_name': HOUSE_SIGNIFICATIONS[house_num]['name'],
            'house_sign': house_sign,
            'house_lord': house_lord,
            'significations': HOUSE_SIGNIFICATIONS[house_num],
            'strength_analysis': self._calculate_house_strength(house_num),
            'resident_planets': self._get_planets_in_house(house_num),
            'aspecting_planets': self._get_aspecting_planets(house_num),
            'lord_analysis': self._analyze_house_lord(house_num),
            'predictions': self._generate_house_predictions(house_num),
            'remedies': self._suggest_remedies(house_num)
        }
        
        return analysis
    
    def _calculate_house_strength(self, house_num):
        """Calculate comprehensive house strength"""
        strength_factors = {
            'lord_strength': self._calculate_lord_strength(house_num),
            'resident_planets_strength': self._calculate_resident_planets_strength(house_num),
            'aspects_strength': self._calculate_aspects_strength(house_num),
            'sign_strength': self._calculate_sign_strength(house_num),
            'positional_strength': self._calculate_positional_strength(house_num)
        }
        
        # Weighted calculation
        total_strength = (
            strength_factors['lord_strength'] * 0.35 +
            strength_factors['resident_planets_strength'] * 0.25 +
            strength_factors['aspects_strength'] * 0.20 +
            strength_factors['sign_strength'] * 0.10 +
            strength_factors['positional_strength'] * 0.10
        )
        
        return {
            'total_strength': round(total_strength, 2),
            'factors': strength_factors,
            'interpretation': self._interpret_strength(total_strength),
            'grade': self._get_strength_grade(total_strength)
        }
    
    def _calculate_lord_strength(self, house_num):
        """Calculate house lord strength"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        lord_planet = SIGN_LORDS[house_sign]
        
        if lord_planet not in self.chart_data['planets']:
            return 50
            
        lord_data = self.chart_data['planets'][lord_planet]
        strength = 50  # Base strength
        
        # Exaltation/Debilitation
        if lord_data['sign'] == EXALTATION_SIGNS.get(lord_planet):
            strength += 30
        elif lord_data['sign'] == DEBILITATION_SIGNS.get(lord_planet):
            strength -= 30
        
        # Own sign strength
        if lord_data['sign'] in [s for s, l in SIGN_LORDS.items() if l == lord_planet]:
            strength += 25
        
        # House position strength
        lord_house = lord_data.get('house', 1)
        if lord_house in [1, 4, 7, 10]:  # Kendra houses
            strength += 20
        elif lord_house in [1, 5, 9]:  # Trikona houses
            strength += 25
        elif lord_house in [6, 8, 12]:  # Dusthana houses
            strength -= 20
        
        # Retrograde consideration
        if lord_data.get('retrograde', False):
            strength += 5  # Retrograde can be beneficial in some cases
            
        return max(0, min(100, strength))
    
    def _calculate_resident_planets_strength(self, house_num):
        """Calculate strength of planets residing in the house"""
        resident_planets = self._get_planets_in_house(house_num)
        
        if not resident_planets:
            return 60  # Neutral if empty
        
        total_strength = 0
        for planet in resident_planets:
            planet_data = self.chart_data['planets'][planet]
            planet_strength = 50
            
            # Natural benefic/malefic
            if planet in NATURAL_BENEFICS:
                planet_strength += 15
            elif planet in NATURAL_MALEFICS:
                planet_strength -= 5
            
            # Exaltation/Debilitation
            if planet_data['sign'] == EXALTATION_SIGNS.get(planet):
                planet_strength += 25
            elif planet_data['sign'] == DEBILITATION_SIGNS.get(planet):
                planet_strength -= 25
            
            # Own sign
            if planet_data['sign'] in [s for s, l in SIGN_LORDS.items() if l == planet]:
                planet_strength += 20
            
            # House-specific planet effects
            planet_strength += self._get_planet_house_compatibility(planet, house_num)
            
            total_strength += planet_strength
        
        return max(0, min(100, total_strength / len(resident_planets)))
    
    def _calculate_aspects_strength(self, house_num):
        """Calculate strength of aspects on the house"""
        aspecting_planets = self._get_aspecting_planets(house_num)
        
        if not aspecting_planets:
            return 50
        
        total_strength = 0
        for planet in aspecting_planets:
            aspect_strength = 50
            
            if planet in NATURAL_BENEFICS:
                aspect_strength += 15
            elif planet in NATURAL_MALEFICS:
                aspect_strength -= 10
            
            # Special aspects
            if planet == 'Jupiter':
                aspect_strength += 20  # Jupiter's aspect is always beneficial
            elif planet == 'Saturn':
                aspect_strength -= 5   # Saturn's aspect can be restrictive
            
            total_strength += aspect_strength
        
        return max(0, min(100, total_strength / len(aspecting_planets)))
    
    def _calculate_sign_strength(self, house_num):
        """Calculate strength based on the sign in the house"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        # Sign compatibility with house significations
        sign_strength = 50
        
        # Some signs are naturally better for certain houses
        house_sign_compatibility = {
            1: [0, 4, 8],      # Aries, Leo, Sagittarius good for 1st house
            2: [1, 5, 9],      # Taurus, Virgo, Capricorn good for 2nd house
            3: [2, 6, 10],     # Gemini, Libra, Aquarius good for 3rd house
            4: [3, 7, 11],     # Cancer, Scorpio, Pisces good for 4th house
            5: [0, 4, 8],      # Fire signs good for 5th house
            6: [5, 9],         # Earth signs good for 6th house
            7: [6, 1],         # Libra, Taurus good for 7th house
            8: [7, 3, 11],     # Water signs good for 8th house
            9: [8, 0, 4],      # Fire signs good for 9th house
            10: [9, 5, 1],     # Earth signs good for 10th house
            11: [10, 2, 6],    # Air signs good for 11th house
            12: [11, 3, 7]     # Water signs good for 12th house
        }
        
        if house_sign in house_sign_compatibility.get(house_num, []):
            sign_strength += 15
        
        return sign_strength
    
    def _calculate_positional_strength(self, house_num):
        """Calculate strength based on house position (Kendra, Trikona, etc.)"""
        if house_num in [1, 4, 7, 10]:  # Kendra houses
            return 75
        elif house_num in [1, 5, 9]:    # Trikona houses
            return 80
        elif house_num in [3, 6, 11]:   # Upachaya houses
            return 65
        elif house_num in [6, 8, 12]:   # Dusthana houses
            return 35
        else:
            return 50
    
    def _get_planets_in_house(self, house_num):
        """Get planets residing in the specified house"""
        planets_in_house = []
        
        for planet, data in self.chart_data['planets'].items():
            if data.get('house') == house_num:
                planets_in_house.append(planet)
        
        return planets_in_house
    
    def _get_aspecting_planets(self, house_num):
        """Get planets aspecting the specified house"""
        aspecting = []
        target_house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        for planet, data in self.chart_data['planets'].items():
            planet_sign = data['sign']
            
            # 7th aspect (all planets)
            if (planet_sign + 6) % 12 == target_house_sign:
                aspecting.append(planet)
            
            # Special aspects
            if planet == 'Mars':
                # Mars aspects 4th and 8th houses from its position
                if (planet_sign + 3) % 12 == target_house_sign or (planet_sign + 7) % 12 == target_house_sign:
                    aspecting.append(planet)
            elif planet == 'Jupiter':
                # Jupiter aspects 5th and 9th houses from its position
                if (planet_sign + 4) % 12 == target_house_sign or (planet_sign + 8) % 12 == target_house_sign:
                    aspecting.append(planet)
            elif planet == 'Saturn':
                # Saturn aspects 3rd and 10th houses from its position
                if (planet_sign + 2) % 12 == target_house_sign or (planet_sign + 9) % 12 == target_house_sign:
                    aspecting.append(planet)
        
        return list(set(aspecting))  # Remove duplicates
    
    def _analyze_house_lord(self, house_num):
        """Detailed analysis of house lord"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        lord_planet = SIGN_LORDS[house_sign]
        
        if lord_planet not in self.chart_data['planets']:
            return {'status': 'Lord not found in chart'}
        
        lord_data = self.chart_data['planets'][lord_planet]
        lord_house = lord_data.get('house', 1)
        
        analysis = {
            'planet': lord_planet,
            'position_sign': lord_data['sign'],
            'position_house': lord_house,
            'degree': lord_data.get('degree', 0),
            'retrograde': lord_data.get('retrograde', False),
            'strength': self._calculate_lord_strength(house_num),
            'dignity': self._get_planet_dignity(lord_planet, lord_data['sign']),
            'house_relationship': self._get_house_relationship(house_num, lord_house)
        }
        
        return analysis
    
    def _get_planet_dignity(self, planet, sign):
        """Get planet's dignity in the sign"""
        if sign == EXALTATION_SIGNS.get(planet):
            return 'Exalted'
        elif sign == DEBILITATION_SIGNS.get(planet):
            return 'Debilitated'
        elif sign in [s for s, l in SIGN_LORDS.items() if l == planet]:
            return 'Own Sign'
        else:
            return 'Neutral'
    
    def _get_house_relationship(self, house_num, lord_house):
        """Analyze relationship between house and its lord's position"""
        if lord_house == house_num:
            return 'Lord in own house - Very strong'
        elif lord_house in [1, 4, 7, 10]:
            return 'Lord in Kendra - Strong'
        elif lord_house in [1, 5, 9]:
            return 'Lord in Trikona - Excellent'
        elif lord_house in [6, 8, 12]:
            return 'Lord in Dusthana - Challenging'
        else:
            return 'Neutral position'
    
    def _get_planet_house_compatibility(self, planet, house_num):
        """Get compatibility score between planet and house"""
        compatibility_matrix = {
            'Sun': {1: 20, 5: 15, 9: 15, 10: 20},
            'Moon': {1: 10, 4: 20, 11: 10},
            'Mars': {1: 15, 3: 15, 6: 20, 10: 15, 11: 10},
            'Mercury': {1: 10, 3: 15, 6: 10, 10: 15},
            'Jupiter': {1: 15, 2: 10, 5: 20, 9: 20, 11: 15},
            'Venus': {2: 15, 4: 10, 7: 20, 12: 10},
            'Saturn': {3: 10, 6: 15, 8: 10, 10: 15, 11: 20},
            'Rahu': {3: 10, 6: 15, 11: 15},
            'Ketu': {8: 10, 12: 15}
        }
        
        return compatibility_matrix.get(planet, {}).get(house_num, 0)
    
    def _generate_house_predictions(self, house_num):
        """Generate predictions for the house"""
        strength = self._calculate_house_strength(house_num)['total_strength']
        significations = HOUSE_SIGNIFICATIONS[house_num]
        
        predictions = {
            'general_outlook': self._get_general_outlook(strength),
            'key_areas': significations['primary'],
            'likely_events': self._predict_likely_events(house_num, strength),
            'timing_indicators': self._get_timing_indicators(house_num),
            'favorable_periods': self._get_favorable_periods(house_num)
        }
        
        return predictions
    
    def _get_general_outlook(self, strength):
        """Get general outlook based on strength"""
        if strength >= 80:
            return "Excellent prospects with strong positive results"
        elif strength >= 65:
            return "Good outcomes with favorable conditions"
        elif strength >= 50:
            return "Mixed results, timing and effort important"
        elif strength >= 35:
            return "Challenges present, remedies recommended"
        else:
            return "Significant obstacles, strong remedial measures needed"
    
    def _predict_likely_events(self, house_num, strength):
        """Predict likely events for the house"""
        base_events = HOUSE_SIGNIFICATIONS[house_num]['events']
        
        if strength >= 70:
            return [f"Positive {event}" for event in base_events[:3]]
        elif strength >= 50:
            return [f"Mixed results in {event}" for event in base_events[:2]]
        else:
            return [f"Challenges in {event}" for event in base_events[:2]]
    
    def _get_timing_indicators(self, house_num):
        """Get timing indicators for house events"""
        house_lord = SIGN_LORDS[self.chart_data['houses'][house_num - 1]['sign']]
        
        return {
            'primary_dasha': f"{house_lord} Mahadasha/Antardasha periods",
            'transit_triggers': f"When benefics transit through house {house_num} or aspect it",
            'annual_indicators': f"During {house_lord}'s favorable transit periods"
        }
    
    def _get_favorable_periods(self, house_num):
        """Get favorable periods for house matters"""
        house_lord = SIGN_LORDS[self.chart_data['houses'][house_num - 1]['sign']]
        
        return [
            f"{house_lord} Mahadasha",
            f"Jupiter transit through house {house_num}",
            f"Benefic planets transiting house {house_num}"
        ]
    
    def _suggest_remedies(self, house_num):
        """Suggest remedies for house improvement"""
        strength = self._calculate_house_strength(house_num)['total_strength']
        house_lord = SIGN_LORDS[self.chart_data['houses'][house_num - 1]['sign']]
        
        if strength >= 70:
            return ["Continue positive practices", "Express gratitude for blessings"]
        
        remedies = []
        
        # General remedies based on house lord
        lord_remedies = {
            'Sun': ["Offer water to Sun at sunrise", "Donate wheat on Sundays", "Wear ruby (if suitable)"],
            'Moon': ["Offer milk to Shiva", "Donate white items on Mondays", "Wear pearl (if suitable)"],
            'Mars': ["Recite Hanuman Chalisa", "Donate red items on Tuesdays", "Wear red coral (if suitable)"],
            'Mercury': ["Donate green items on Wednesdays", "Feed green grass to cows", "Wear emerald (if suitable)"],
            'Jupiter': ["Donate yellow items on Thursdays", "Respect teachers and elders", "Wear yellow sapphire (if suitable)"],
            'Venus': ["Donate white items on Fridays", "Respect women", "Wear diamond (if suitable)"],
            'Saturn': ["Donate black items on Saturdays", "Serve the poor", "Wear blue sapphire (if suitable)"]
        }
        
        remedies.extend(lord_remedies.get(house_lord, ["Consult an astrologer for specific remedies"]))
        
        # House-specific remedies
        house_remedies = {
            1: ["Maintain good health habits", "Practice meditation"],
            2: ["Save money regularly", "Speak truthfully"],
            3: ["Maintain good relationships with siblings", "Develop communication skills"],
            4: ["Respect mother and elders", "Keep home clean and peaceful"],
            5: ["Spend time with children", "Engage in creative activities"],
            6: ["Maintain good health", "Serve others selflessly"],
            7: ["Respect spouse and partners", "Maintain harmony in relationships"],
            8: ["Practice spiritual disciplines", "Study occult sciences carefully"],
            9: ["Respect father and teachers", "Follow dharmic principles"],
            10: ["Work with dedication", "Maintain good reputation"],
            11: ["Help friends in need", "Work towards goals systematically"],
            12: ["Practice charity", "Engage in spiritual practices"]
        }
        
        remedies.extend(house_remedies.get(house_num, []))
        
        return remedies[:5]  # Return top 5 remedies
    
    def _interpret_strength(self, strength):
        """Interpret numerical strength"""
        if strength >= 80:
            return "Excellent strength - Very favorable results expected"
        elif strength >= 65:
            return "Good strength - Favorable outcomes likely"
        elif strength >= 50:
            return "Average strength - Mixed results, effort needed"
        elif strength >= 35:
            return "Below average - Challenges present, remedies helpful"
        else:
            return "Weak - Significant challenges, strong remedies required"
    
    def _get_strength_grade(self, strength):
        """Get letter grade for strength"""
        if strength >= 90:
            return 'A+'
        elif strength >= 80:
            return 'A'
        elif strength >= 70:
            return 'B+'
        elif strength >= 60:
            return 'B'
        elif strength >= 50:
            return 'C+'
        elif strength >= 40:
            return 'C'
        elif strength >= 30:
            return 'D'
        else:
            return 'F'