from .base_calculator import BaseCalculator

class PlanetaryDignitiesCalculator(BaseCalculator):
    """Extract planetary dignities calculation from planetary_dignities.py"""
    
    def __init__(self, chart_data=None):
        super().__init__(chart_data or {})
        
        self.EXALTATION_DATA = {
            'Sun': {'sign': 0, 'degree': 10}, 'Moon': {'sign': 1, 'degree': 3},
            'Mars': {'sign': 9, 'degree': 28}, 'Mercury': {'sign': 5, 'degree': 15},
            'Jupiter': {'sign': 3, 'degree': 5}, 'Venus': {'sign': 11, 'degree': 27},
            'Saturn': {'sign': 6, 'degree': 20}
        }
        
        self.DEBILITATION_DATA = {
            'Sun': {'sign': 6, 'degree': 10}, 'Moon': {'sign': 7, 'degree': 3},
            'Mars': {'sign': 3, 'degree': 28}, 'Mercury': {'sign': 11, 'degree': 15},
            'Jupiter': {'sign': 9, 'degree': 5}, 'Venus': {'sign': 5, 'degree': 27},
            'Saturn': {'sign': 0, 'degree': 20}
        }
        
        self.OWN_SIGNS = {
            'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
            'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
        }
        
        self.MOOLATRIKONA_DATA = {
            'Sun': {'sign': 4, 'start_degree': 0, 'end_degree': 20},
            'Moon': {'sign': 1, 'start_degree': 4, 'end_degree': 30},
            'Mars': {'sign': 0, 'start_degree': 0, 'end_degree': 12},
            'Mercury': {'sign': 5, 'start_degree': 16, 'end_degree': 20},
            'Jupiter': {'sign': 8, 'start_degree': 0, 'end_degree': 10},
            'Venus': {'sign': 6, 'start_degree': 0, 'end_degree': 15},
            'Saturn': {'sign': 10, 'start_degree': 0, 'end_degree': 20}
        }
        
        self.COMBUSTION_THRESHOLDS = {
            'Moon': 12, 'Mars': 17, 'Mercury': 14, 'Jupiter': 11, 'Venus': 10, 'Saturn': 15
        }
    
    def calculate_planetary_dignities(self):
        """Calculate comprehensive planetary dignities"""
        planets = self.chart_data.get('planets', {})
        ascendant_sign = int(self.chart_data.get('ascendant', 0) / 30)
        dignities = {}
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Gulika', 'Mandi']:
                continue
            
            planet_sign = planet_data.get('sign', 0)
            planet_degree = planet_data.get('degree', 0)
            planet_longitude = planet_data.get('longitude', 0)
            is_retrograde = planet_data.get('retrograde', False)
            
            dignity_info = {
                'planet': planet_name,
                'sign': planet_sign,
                'degree': round(planet_degree, 2),
                'dignity': self._calculate_dignity(planet_name, planet_sign, planet_degree),
                'functional_nature': self._calculate_functional_nature(planet_name, ascendant_sign),
                'combustion_status': 'normal',
                'retrograde': is_retrograde,
                'strength_multiplier': 1.0,
                'states': []
            }
            
            # Calculate combustion
            if planet_name != 'Sun' and 'Sun' in planets:
                sun_longitude = planets['Sun'].get('longitude', 0)
                dignity_info['combustion_status'] = self._calculate_combustion(planet_name, planet_longitude, sun_longitude)
            
            # Calculate strength multiplier
            dignity_info['strength_multiplier'] = self._calculate_strength_multiplier(dignity_info)
            dignity_info['states'] = self._compile_states(dignity_info)
            
            dignities[planet_name] = dignity_info
        
        return dignities
    
    def _calculate_dignity(self, planet, sign, degree=None):
        """Calculate planetary dignity"""
        if planet in ['Rahu', 'Ketu']:
            return self._calculate_rahu_ketu_dignity(planet, sign)
        
        # Check exaltation
        if planet in self.EXALTATION_DATA:
            exalt_data = self.EXALTATION_DATA[planet]
            if sign == exalt_data['sign']:
                return 'exalted'
        
        # Check debilitation
        if planet in self.DEBILITATION_DATA:
            debil_data = self.DEBILITATION_DATA[planet]
            if sign == debil_data['sign']:
                return 'debilitated'
        
        # Check moolatrikona
        if planet in self.MOOLATRIKONA_DATA:
            mool_data = self.MOOLATRIKONA_DATA[planet]
            if sign == mool_data['sign']:
                if degree is not None:
                    if mool_data['start_degree'] <= degree <= mool_data['end_degree']:
                        return 'moolatrikona'
                else:
                    return 'moolatrikona'
        
        # Check own sign
        if planet in self.OWN_SIGNS:
            if sign in self.OWN_SIGNS[planet]:
                return 'own_sign'
        
        return 'neutral'
    
    def _calculate_rahu_ketu_dignity(self, planet, sign):
        """Calculate dignity for Rahu/Ketu"""
        if planet == 'Rahu':
            if sign in [2, 5, 6, 8, 11]:  # Gemini, Virgo, Libra, Sagittarius, Pisces
                return 'favorable'
            elif sign in [3, 4, 7]:  # Cancer, Leo, Scorpio
                return 'unfavorable'
        elif planet == 'Ketu':
            if sign in [8, 11, 7]:  # Sagittarius, Pisces, Scorpio
                return 'favorable'
            elif sign in [2, 5, 6]:  # Gemini, Virgo, Libra
                return 'unfavorable'
        return 'neutral'
    
    def _calculate_functional_nature(self, planet, ascendant_sign):
        """Calculate functional benefic/malefic nature"""
        # Simplified functional nature based on ascendant
        functional_benefics = {
            0: ['Sun', 'Mars', 'Jupiter'], 1: ['Mercury', 'Venus', 'Saturn'],
            2: ['Mercury', 'Venus'], 3: ['Moon', 'Mars'], 4: ['Sun', 'Mars'],
            5: ['Mercury', 'Venus'], 6: ['Venus', 'Saturn'], 7: ['Moon', 'Jupiter'],
            8: ['Sun', 'Mars', 'Jupiter'], 9: ['Venus', 'Saturn'], 10: ['Venus', 'Saturn'],
            11: ['Sun', 'Mars', 'Jupiter']
        }
        
        if planet in functional_benefics.get(ascendant_sign, []):
            return 'benefic'
        return 'neutral'
    
    def _calculate_combustion(self, planet, planet_longitude, sun_longitude):
        """Calculate combustion status"""
        if planet not in self.COMBUSTION_THRESHOLDS:
            return 'normal'
        
        angular_distance = abs(planet_longitude - sun_longitude)
        if angular_distance > 180:
            angular_distance = 360 - angular_distance
        
        threshold = self.COMBUSTION_THRESHOLDS[planet]
        
        if angular_distance <= 1:  # Cazimi
            return 'cazimi'
        elif angular_distance <= threshold:
            return 'combust'
        
        return 'normal'
    
    def _calculate_strength_multiplier(self, dignity_info):
        """Calculate overall strength multiplier"""
        multiplier = 1.0
        
        dignity_multipliers = {
            'exalted': 1.5, 'moolatrikona': 1.3, 'own_sign': 1.2,
            'favorable': 1.2, 'unfavorable': 0.8, 'debilitated': 0.6
        }
        multiplier *= dignity_multipliers.get(dignity_info['dignity'], 1.0)
        
        if dignity_info['functional_nature'] == 'benefic':
            multiplier *= 1.2
        
        combustion_multipliers = {'cazimi': 1.8, 'combust': 0.3}
        multiplier *= combustion_multipliers.get(dignity_info['combustion_status'], 1.0)
        
        if dignity_info['retrograde'] and dignity_info['planet'] not in ['Jupiter', 'Venus']:
            multiplier *= 0.9
        
        return round(multiplier, 2)
    
    def _compile_states(self, dignity_info):
        """Compile all planetary states"""
        states = []
        
        if dignity_info['dignity'] != 'neutral':
            states.append(dignity_info['dignity'].title())
        
        if dignity_info['functional_nature'] == 'benefic':
            states.append('Functional Benefic')
        
        if dignity_info['combustion_status'] == 'combust':
            states.append('Combust')
        elif dignity_info['combustion_status'] == 'cazimi':
            states.append('Cazimi')
        
        if dignity_info['retrograde']:
            states.append('Retrograde')
        
        return states