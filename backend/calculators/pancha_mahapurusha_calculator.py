"""
Pancha Mahapurusha Yoga Calculator
Five great person yogas formed by Mars, Mercury, Jupiter, Venus, Saturn
Based on classical Vedic astrology from Brihat Parashara Hora Shastra
"""

class PanchaMahapurushaCalculator:
    """Calculate Pancha Mahapurusha Yogas - five great person combinations"""
    
    def __init__(self, chart_data):
        self.chart_data = chart_data
        
        # Yoga definitions with exact conditions
        self.yoga_definitions = {
            'Ruchaka': {
                'planet': 'Mars',
                'conditions': 'Mars in own sign (Aries/Scorpio) or exaltation (Capricorn) in Kendra (1,4,7,10)',
                'own_signs': [0, 7],      # Aries, Scorpio
                'exaltation_signs': [9],   # Capricorn
                'effects': 'Courageous, strong, victorious, leader, commander-like qualities'
            },
            'Bhadra': {
                'planet': 'Mercury',
                'conditions': 'Mercury in own sign (Gemini/Virgo) or exaltation (Virgo) in Kendra (1,4,7,10)',
                'own_signs': [2, 5],      # Gemini, Virgo
                'exaltation_signs': [5],   # Virgo (same as own sign)
                'effects': 'Intelligent, learned, eloquent, skilled in arts and sciences'
            },
            'Hamsa': {
                'planet': 'Jupiter',
                'conditions': 'Jupiter in own sign (Sagittarius/Pisces) or exaltation (Cancer) in Kendra (1,4,7,10)',
                'own_signs': [8, 11],     # Sagittarius, Pisces
                'exaltation_signs': [3],   # Cancer
                'effects': 'Wise, virtuous, wealthy, respected, spiritual inclination'
            },
            'Malavya': {
                'planet': 'Venus',
                'conditions': 'Venus in own sign (Taurus/Libra) or exaltation (Pisces) in Kendra (1,4,7,10)',
                'own_signs': [1, 6],      # Taurus, Libra
                'exaltation_signs': [11],  # Pisces
                'effects': 'Beautiful, artistic, wealthy, luxurious lifestyle, attractive personality'
            },
            'Sasa': {
                'planet': 'Saturn',
                'conditions': 'Saturn in own sign (Capricorn/Aquarius) or exaltation (Libra) in Kendra (1,4,7,10)',
                'own_signs': [9, 10],     # Capricorn, Aquarius
                'exaltation_signs': [6],   # Libra
                'effects': 'Disciplined, hardworking, authoritative, gains through perseverance'
            }
        }
    
    def calculate_pancha_mahapurusha_yogas(self):
        """Calculate all Pancha Mahapurusha Yogas"""
        results = {}
        
        for yoga_name, yoga_info in self.yoga_definitions.items():
            planet = yoga_info['planet']
            yoga_result = self._check_yoga_formation(yoga_name, planet, yoga_info)
            
            if yoga_result['is_formed']:
                results[yoga_name] = yoga_result
        
        return results
    
    def _check_yoga_formation(self, yoga_name, planet, yoga_info):
        """Check if specific Pancha Mahapurusha Yoga is formed"""
        # Get planet data from correct structure
        planets = self.chart_data.get('planets', {})
        if planet not in planets:
            return self._get_no_yoga_result(yoga_name, planet, yoga_info)
        
        planet_data = planets[planet]
        planet_sign = planet_data.get('sign', 0)
        planet_house = planet_data.get('house', 1) - 1  # Convert to 0-based
        
        # Check if planet is in Kendra (houses 1, 4, 7, 10)
        kendra_houses = [0, 3, 6, 9]  # 0-indexed (1st, 4th, 7th, 10th)
        is_in_kendra = planet_house in kendra_houses
        
        # Check if planet is in own sign or exaltation
        valid_signs = yoga_info['own_signs'] + yoga_info['exaltation_signs']
        is_in_valid_sign = planet_sign in valid_signs
        
        # Determine sign type
        sign_type = None
        if planet_sign in yoga_info['own_signs']:
            sign_type = 'Own Sign'
        elif planet_sign in yoga_info['exaltation_signs']:
            sign_type = 'Exaltation'
        
        # Yoga is formed if both conditions are met
        is_formed = is_in_kendra and is_in_valid_sign
        
        # Calculate yoga strength
        planet_longitude = planet_data.get('longitude', 0)
        yoga_strength = self._calculate_yoga_strength(planet, planet_longitude, sign_type, planet_house)
        
        return {
            'yoga_name': yoga_name,
            'planet': planet,
            'is_formed': is_formed,
            'planet_sign': self._get_sign_name(planet_sign),
            'planet_house': planet_house + 1,  # Convert to 1-12
            'sign_type': sign_type,
            'is_in_kendra': is_in_kendra,
            'is_in_valid_sign': is_in_valid_sign,
            'yoga_strength': yoga_strength,
            'conditions': yoga_info['conditions'],
            'effects': yoga_info['effects'],
            'detailed_analysis': self._get_detailed_analysis(yoga_name, planet, is_formed, yoga_strength)
        }
    
    def _calculate_yoga_strength(self, planet, planet_position, sign_type, house_position):
        """Calculate strength of the Pancha Mahapurusha Yoga"""
        if not sign_type:
            return 'Not Formed'
        
        strength_factors = []
        base_strength = 0
        
        # Base strength from sign type
        if sign_type == 'Exaltation':
            base_strength += 4
            strength_factors.append('Exalted planet (+4)')
        elif sign_type == 'Own Sign':
            base_strength += 3
            strength_factors.append('Own sign placement (+3)')
        
        # House strength (Kendra strength varies)
        house_strengths = {0: 4, 3: 3, 6: 3, 9: 2}  # 1st=4, 4th=3, 7th=3, 10th=2
        house_strength = house_strengths.get(house_position, 0)
        base_strength += house_strength
        strength_factors.append(f'Kendra house strength (+{house_strength})')
        
        # Check for additional strengthening factors
        additional_strength = self._check_additional_strength_factors(planet, planet_position)
        base_strength += additional_strength['total']
        strength_factors.extend(additional_strength['factors'])
        
        # Determine overall strength category
        if base_strength >= 10:
            return 'Exceptional'
        elif base_strength >= 8:
            return 'Very Strong'
        elif base_strength >= 6:
            return 'Strong'
        elif base_strength >= 4:
            return 'Moderate'
        else:
            return 'Weak'
    
    def _check_additional_strength_factors(self, planet, planet_position):
        """Check additional factors that strengthen the yoga"""
        factors = []
        total_strength = 0
        
        # Check if planet is Vargottama (same sign in D1 and D9)
        # This would require D9 chart data - placeholder for now
        
        # Check if planet is in favorable nakshatra
        # This would require nakshatra calculation - placeholder for now
        
        # Check if planet is not combust (too close to Sun)
        planets = self.chart_data.get('planets', {})
        sun_data = planets.get('Sun', {})
        sun_position = sun_data.get('longitude', 0)
        distance_from_sun = abs(planet_position - sun_position)
        if distance_from_sun > 180:
            distance_from_sun = 360 - distance_from_sun
        
        if distance_from_sun > 8:  # Not combust
            factors.append('Not combust (+1)')
            total_strength += 1
        
        # Check if planet is not retrograde (would need retrograde data)
        
        return {
            'total': total_strength,
            'factors': factors
        }
    
    def _get_detailed_analysis(self, yoga_name, planet, is_formed, strength):
        """Get detailed analysis of the yoga"""
        if not is_formed:
            return f"{yoga_name} Yoga is not formed. {planet} needs to be in own sign/exaltation and in Kendra house."
        
        strength_descriptions = {
            'Exceptional': 'This is an exceptionally powerful yoga that will dominate the chart',
            'Very Strong': 'This is a very strong yoga with significant positive effects',
            'Strong': 'This is a well-formed yoga with good positive effects',
            'Moderate': 'This yoga is present but with moderate strength',
            'Weak': 'This yoga is technically present but with limited effects'
        }
        
        return f"{yoga_name} Yoga is formed with {strength} strength. {strength_descriptions.get(strength, 'Effects will be moderate.')}"
    
    def _get_sign_name(self, sign_num):
        """Get sign name from number"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num]
    
    def get_pancha_mahapurusha_summary(self):
        """Get summary of all Pancha Mahapurusha Yogas"""
        yogas = self.calculate_pancha_mahapurusha_yogas()
        
        if not yogas:
            return {
                'total_yogas': 0,
                'formed_yogas': [],
                'summary': 'No Pancha Mahapurusha Yogas are formed in this chart'
            }
        
        # Sort yogas by strength
        strength_order = {'Exceptional': 5, 'Very Strong': 4, 'Strong': 3, 'Moderate': 2, 'Weak': 1}
        sorted_yogas = sorted(yogas.items(), 
                            key=lambda x: strength_order.get(x[1]['yoga_strength'], 0), 
                            reverse=True)
        
        formed_yogas = []
        for yoga_name, yoga_data in sorted_yogas:
            formed_yogas.append({
                'yoga_name': yoga_name,
                'planet': yoga_data['planet'],
                'strength': yoga_data['yoga_strength'],
                'house': yoga_data['planet_house'],
                'sign': yoga_data['planet_sign'],
                'sign_type': yoga_data['sign_type']
            })
        
        return {
            'total_yogas': len(yogas),
            'formed_yogas': formed_yogas,
            'detailed_results': yogas,
            'summary': f"{len(yogas)} Pancha Mahapurusha Yoga(s) formed - these create exceptional personality traits"
        }
    
    def get_strongest_yoga(self):
        """Get the strongest Pancha Mahapurusha Yoga"""
        summary = self.get_pancha_mahapurusha_summary()
        
        if summary['formed_yogas']:
            strongest = summary['formed_yogas'][0]
            return {
                'yoga_name': strongest['yoga_name'],
                'planet': strongest['planet'],
                'strength': strongest['strength'],
                'significance': f"Strongest Pancha Mahapurusha Yoga with {strongest['strength']} power"
            }
        
        return None
    
    def _get_no_yoga_result(self, yoga_name, planet, yoga_info):
        """Return result when yoga is not formed due to missing planet data"""
        return {
            'yoga_name': yoga_name,
            'planet': planet,
            'is_formed': False,
            'planet_sign': 'Unknown',
            'planet_house': 0,
            'sign_type': None,
            'is_in_kendra': False,
            'is_in_valid_sign': False,
            'yoga_strength': 'Not Formed',
            'conditions': yoga_info['conditions'],
            'effects': yoga_info['effects'],
            'detailed_analysis': f"{yoga_name} Yoga is not formed. {planet} data not available."
        }