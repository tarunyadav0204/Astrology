"""
Neecha Bhanga Calculator
Cancellation of debilitation based on classical Vedic astrology rules
From Brihat Parashara Hora Shastra and other classical texts
"""

class NeechaBhangaCalculator:
    """Calculate Neecha Bhanga (cancellation of debilitation) conditions"""
    
    def __init__(self, chart_data, divisional_charts=None):
        self.chart_data = chart_data
        self.divisional_charts = divisional_charts or {}
        
        # Debilitation signs for each planet
        self.debilitation_signs = {
            'Sun': 6,      # Libra (180°-210°)
            'Moon': 7,     # Scorpio (210°-240°)
            'Mars': 3,     # Cancer (90°-120°)
            'Mercury': 5,  # Pisces (330°-360°/0°-30°)
            'Jupiter': 9,  # Capricorn (270°-300°)
            'Venus': 1,    # Virgo (150°-180°)
            'Saturn': 0    # Aries (0°-30°)
        }
        
        # Exaltation signs (opposite of debilitation)
        self.exaltation_signs = {
            'Sun': 0,      # Aries
            'Moon': 1,     # Taurus  
            'Mars': 9,     # Capricorn
            'Mercury': 1,  # Virgo
            'Jupiter': 3,  # Cancer
            'Venus': 5,    # Pisces
            'Saturn': 6    # Libra
        }
        
        # Lords of signs
        self.sign_lords = {
            0: 'Mars',     # Aries
            1: 'Venus',    # Taurus
            2: 'Mercury',  # Gemini
            3: 'Moon',     # Cancer
            4: 'Sun',      # Leo
            5: 'Mercury',  # Virgo
            6: 'Venus',    # Libra
            7: 'Mars',     # Scorpio
            8: 'Jupiter',  # Sagittarius
            9: 'Saturn',   # Capricorn
            10: 'Saturn',  # Aquarius
            11: 'Jupiter'  # Pisces
        }
    
    def calculate_neecha_bhanga(self):
        """Calculate Neecha Bhanga for all debilitated planets"""
        results = {}
        
        for planet in self.debilitation_signs.keys():
            planet_position = self.chart_data.get(planet, 0)
            planet_sign = int(planet_position / 30)
            
            # Check if planet is debilitated
            if planet_sign == self.debilitation_signs[planet]:
                neecha_bhanga_result = self._check_neecha_bhanga_conditions(planet, planet_position)
                results[planet] = neecha_bhanga_result
        
        return results
    
    def _check_neecha_bhanga_conditions(self, planet, planet_position):
        """Check all classical Neecha Bhanga conditions"""
        planet_sign = int(planet_position / 30)
        conditions_met = []
        
        # Condition 1: Lord of debilitation sign in kendra from lagna or moon
        debil_lord = self.sign_lords[planet_sign]
        if self._check_kendra_position(debil_lord):
            conditions_met.append({
                'condition': 'Lord of debilitation sign in Kendra',
                'description': f"{debil_lord} (lord of {self._get_sign_name(planet_sign)}) is in Kendra from Lagna/Moon",
                'strength': 'Strong'
            })
        
        # Condition 2: Lord of exaltation sign in kendra from lagna or moon
        exalt_sign = self.exaltation_signs[planet]
        exalt_lord = self.sign_lords[exalt_sign]
        if self._check_kendra_position(exalt_lord):
            conditions_met.append({
                'condition': 'Lord of exaltation sign in Kendra',
                'description': f"{exalt_lord} (lord of {self._get_sign_name(exalt_sign)}) is in Kendra from Lagna/Moon",
                'strength': 'Strong'
            })
        
        # Condition 3: Debilitated planet aspected by its own lord
        planet_lord = self.sign_lords[planet_sign]
        if self._check_aspect_by_lord(planet, planet_lord):
            conditions_met.append({
                'condition': 'Debilitated planet aspected by own lord',
                'description': f"{planet} is aspected by its sign lord {planet_lord}",
                'strength': 'Moderate'
            })
        
        # Condition 4: Debilitated planet in exaltation in Navamsa
        if self._check_navamsa_exaltation(planet):
            conditions_met.append({
                'condition': 'Exalted in Navamsa',
                'description': f"{planet} is exalted in Navamsa (D9) chart",
                'strength': 'Very Strong'
            })
        
        # Condition 5: Debilitated planet conjunct with exalted planet
        exalted_conjunction = self._check_exalted_conjunction(planet)
        if exalted_conjunction:
            conditions_met.append({
                'condition': 'Conjunction with exalted planet',
                'description': f"{planet} is conjunct with exalted {exalted_conjunction}",
                'strength': 'Strong'
            })
        
        # Condition 6: Debilitated planet in own sign in Navamsa
        if self._check_navamsa_own_sign(planet):
            conditions_met.append({
                'condition': 'Own sign in Navamsa',
                'description': f"{planet} is in own sign in Navamsa (D9) chart",
                'strength': 'Moderate'
            })
        
        # Calculate overall Neecha Bhanga strength
        overall_strength = self._calculate_overall_strength(conditions_met)
        
        return {
            'planet': planet,
            'is_debilitated': True,
            'debilitation_sign': self._get_sign_name(planet_sign),
            'neecha_bhanga_present': len(conditions_met) > 0,
            'conditions_met': conditions_met,
            'total_conditions': len(conditions_met),
            'overall_strength': overall_strength,
            'effects': self._get_neecha_bhanga_effects(planet, overall_strength, len(conditions_met))
        }
    
    def _check_kendra_position(self, planet):
        """Check if planet is in Kendra (1,4,7,10) from Lagna or Moon"""
        planet_pos = self.chart_data.get(planet, 0)
        planet_house = int(planet_pos / 30)
        
        lagna_house = int(self.chart_data.get('ascendant', 0) / 30)
        moon_house = int(self.chart_data.get('Moon', 0) / 30)
        
        # Kendra houses from Lagna
        lagna_kendras = [(lagna_house + i) % 12 for i in [0, 3, 6, 9]]
        
        # Kendra houses from Moon
        moon_kendras = [(moon_house + i) % 12 for i in [0, 3, 6, 9]]
        
        return planet_house in lagna_kendras or planet_house in moon_kendras
    
    def _check_aspect_by_lord(self, planet, lord):
        """Check if debilitated planet is aspected by its lord"""
        planet_pos = self.chart_data.get(planet, 0)
        lord_pos = self.chart_data.get(lord, 0)
        
        if not lord_pos:
            return False
        
        # Calculate houses
        planet_house = (int(planet_pos / 30) + 1)  # 1-12
        lord_house = (int(lord_pos / 30) + 1)      # 1-12
        
        # Check various aspects
        return self._check_planetary_aspect(lord, lord_house, planet_house)
    
    def _check_planetary_aspect(self, aspecting_planet, from_house, to_house):
        """Check if planet aspects another house"""
        house_diff = (to_house - from_house) % 12
        
        # All planets aspect 7th house
        if house_diff == 6:  # 7th house (0-indexed becomes 6)
            return True
        
        # Special aspects
        if aspecting_planet == 'Mars' and house_diff in [3, 7]:  # 4th and 8th
            return True
        elif aspecting_planet == 'Jupiter' and house_diff in [4, 8]:  # 5th and 9th
            return True
        elif aspecting_planet == 'Saturn' and house_diff in [2, 9]:  # 3rd and 10th
            return True
        
        return False
    
    def _check_navamsa_exaltation(self, planet):
        """Check if planet is exalted in Navamsa"""
        if 'd9_navamsa' not in self.divisional_charts:
            return False
        
        d9_chart = self.divisional_charts['d9_navamsa']
        if planet not in d9_chart:
            return False
        
        d9_position = d9_chart[planet]
        d9_sign = int(d9_position / 30)
        
        return d9_sign == self.exaltation_signs[planet]
    
    def _check_navamsa_own_sign(self, planet):
        """Check if planet is in own sign in Navamsa"""
        if 'd9_navamsa' not in self.divisional_charts:
            return False
        
        d9_chart = self.divisional_charts['d9_navamsa']
        if planet not in d9_chart:
            return False
        
        d9_position = d9_chart[planet]
        d9_sign = int(d9_position / 30)
        
        # Check if planet owns this sign
        return self.sign_lords[d9_sign] == planet
    
    def _check_exalted_conjunction(self, planet):
        """Check if debilitated planet is conjunct with any exalted planet"""
        planet_pos = self.chart_data.get(planet, 0)
        planet_sign = int(planet_pos / 30)
        
        for other_planet, exalt_sign in self.exaltation_signs.items():
            if other_planet == planet:
                continue
            
            other_pos = self.chart_data.get(other_planet, 0)
            other_sign = int(other_pos / 30)
            
            # Check if other planet is exalted and in same sign
            if other_sign == exalt_sign and other_sign == planet_sign:
                return other_planet
        
        return None
    
    def _calculate_overall_strength(self, conditions_met):
        """Calculate overall Neecha Bhanga strength"""
        if not conditions_met:
            return 'None'
        
        strength_scores = {
            'Very Strong': 4,
            'Strong': 3,
            'Moderate': 2,
            'Weak': 1
        }
        
        total_score = sum(strength_scores.get(condition['strength'], 1) for condition in conditions_met)
        
        if total_score >= 8:
            return 'Complete Cancellation'
        elif total_score >= 6:
            return 'Strong Cancellation'
        elif total_score >= 4:
            return 'Moderate Cancellation'
        elif total_score >= 2:
            return 'Partial Cancellation'
        else:
            return 'Weak Cancellation'
    
    def _get_neecha_bhanga_effects(self, planet, strength, condition_count):
        """Get effects of Neecha Bhanga"""
        effects = {
            'Complete Cancellation': f"{planet} acts like an exalted planet, exceptional results",
            'Strong Cancellation': f"{planet} gives very good results, debilitation largely neutralized",
            'Moderate Cancellation': f"{planet} gives mixed to good results, significant improvement",
            'Partial Cancellation': f"{planet} gives some positive results, partial improvement",
            'Weak Cancellation': f"{planet} shows slight improvement, mostly debilitated effects remain",
            'None': f"{planet} remains fully debilitated"
        }
        
        return {
            'primary_effect': effects.get(strength, 'Debilitated effects remain'),
            'condition_count_note': f"{condition_count} Neecha Bhanga condition(s) present",
            'timing_note': f"Effects most prominent during {planet}'s dasha/antardasha periods"
        }
    
    def _get_sign_name(self, sign_num):
        """Get sign name from number"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num]
    
    def get_neecha_bhanga_summary(self):
        """Get summary of all Neecha Bhanga results"""
        results = self.calculate_neecha_bhanga()
        
        if not results:
            return {
                'total_debilitated_planets': 0,
                'neecha_bhanga_planets': [],
                'summary': 'No debilitated planets found in this chart'
            }
        
        neecha_bhanga_planets = []
        for planet, result in results.items():
            if result['neecha_bhanga_present']:
                neecha_bhanga_planets.append({
                    'planet': planet,
                    'strength': result['overall_strength'],
                    'conditions': result['total_conditions']
                })
        
        return {
            'total_debilitated_planets': len(results),
            'neecha_bhanga_planets': neecha_bhanga_planets,
            'detailed_results': results,
            'summary': f"{len(neecha_bhanga_planets)} out of {len(results)} debilitated planet(s) have Neecha Bhanga"
        }