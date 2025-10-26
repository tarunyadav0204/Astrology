from .base_calculator import BaseCalculator

class YogaCalculator(BaseCalculator):
    """Calculate various Vedic yogas and combinations"""
    
    def __init__(self, birth_data=None, chart_data=None):
        super().__init__(birth_data, chart_data)
        
        self.SIGN_LORDS = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
    
    def calculate_raj_yogas(self):
        """Calculate Raj Yogas (royal combinations)"""
        planets = self.chart_data.get('planets', {})
        raj_yogas = []
        
        # Kendra-Trikona Raj Yoga
        kendra_houses = [1, 4, 7, 10]
        trikona_houses = [1, 5, 9]
        
        for planet1_name, planet1_data in planets.items():
            if planet1_name in ['Rahu', 'Ketu']:
                continue
                
            house1 = planet1_data.get('house', 1)
            
            for planet2_name, planet2_data in planets.items():
                if planet2_name in ['Rahu', 'Ketu'] or planet1_name == planet2_name:
                    continue
                    
                house2 = planet2_data.get('house', 1)
                
                # Check if planets are in conjunction or mutual aspect
                if self._are_planets_connected(planet1_data, planet2_data):
                    # Check Kendra-Trikona combination
                    if ((house1 in kendra_houses and house2 in trikona_houses) or 
                        (house1 in trikona_houses and house2 in kendra_houses)):
                        raj_yogas.append({
                            'name': 'Kendra-Trikona Raj Yoga',
                            'planets': [planet1_name, planet2_name],
                            'houses': [house1, house2],
                            'strength': 'High',
                            'description': f'{planet1_name} and {planet2_name} form Raj Yoga'
                        })
        
        return raj_yogas
    
    def calculate_dhana_yogas(self):
        """Calculate Dhana Yogas (wealth combinations)"""
        planets = self.chart_data.get('planets', {})
        dhana_yogas = []
        
        # 2nd and 11th house lords in conjunction/mutual aspect
        house_2_lord = self._get_house_lord(2)
        house_11_lord = self._get_house_lord(11)
        
        if house_2_lord and house_11_lord and house_2_lord != house_11_lord:
            planet1_data = planets.get(house_2_lord, {})
            planet2_data = planets.get(house_11_lord, {})
            
            if self._are_planets_connected(planet1_data, planet2_data):
                dhana_yogas.append({
                    'name': 'Dhana Yoga',
                    'planets': [house_2_lord, house_11_lord],
                    'description': '2nd and 11th house lords connected - wealth yoga',
                    'strength': 'Medium'
                })
        
        return dhana_yogas
    
    def calculate_panch_mahapurusha_yogas(self):
        """Calculate Panch Mahapurusha Yogas"""
        planets = self.chart_data.get('planets', {})
        mahapurusha_yogas = []
        
        yoga_definitions = {
            'Mars': {'name': 'Ruchaka Yoga', 'houses': [1, 4, 7, 10], 'signs': [0, 7]},
            'Mercury': {'name': 'Bhadra Yoga', 'houses': [1, 4, 7, 10], 'signs': [2, 5]},
            'Jupiter': {'name': 'Hamsa Yoga', 'houses': [1, 4, 7, 10], 'signs': [8, 11]},
            'Venus': {'name': 'Malavya Yoga', 'houses': [1, 4, 7, 10], 'signs': [1, 6]},
            'Saturn': {'name': 'Sasha Yoga', 'houses': [1, 4, 7, 10], 'signs': [9, 10]}
        }
        
        for planet_name, yoga_data in yoga_definitions.items():
            if planet_name in planets:
                planet_data = planets[planet_name]
                house = planet_data.get('house', 1)
                sign = planet_data.get('sign', 0)
                
                # Check if planet is in Kendra and own/exaltation sign
                if house in yoga_data['houses'] and sign in yoga_data['signs']:
                    mahapurusha_yogas.append({
                        'name': yoga_data['name'],
                        'planet': planet_name,
                        'house': house,
                        'sign': sign,
                        'strength': 'High',
                        'description': f'{planet_name} in Kendra in own/exaltation sign'
                    })
        
        return mahapurusha_yogas
    
    def calculate_neecha_bhanga_yogas(self):
        """Calculate Neecha Bhanga Yogas (debilitation cancellation)"""
        planets = self.chart_data.get('planets', {})
        neecha_bhanga_yogas = []
        
        debilitation_signs = {
            'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11,
            'Jupiter': 9, 'Venus': 5, 'Saturn': 0
        }
        
        for planet_name, debil_sign in debilitation_signs.items():
            if planet_name in planets:
                planet_data = planets[planet_name]
                current_sign = planet_data.get('sign', 0)
                
                if current_sign == debil_sign:
                    # Check for cancellation conditions
                    cancellation_found = False
                    cancellation_reason = ""
                    
                    # Rule 1: Debilitation lord in Kendra from Moon/Ascendant
                    debil_lord = self.SIGN_LORDS[debil_sign]
                    if debil_lord in planets:
                        debil_lord_house = planets[debil_lord].get('house', 1)
                        if debil_lord_house in [1, 4, 7, 10]:
                            cancellation_found = True
                            cancellation_reason = f"Debilitation lord {debil_lord} in Kendra"
                    
                    if cancellation_found:
                        neecha_bhanga_yogas.append({
                            'name': 'Neecha Bhanga Yoga',
                            'planet': planet_name,
                            'reason': cancellation_reason,
                            'strength': 'Medium',
                            'description': f'{planet_name} debilitation cancelled'
                        })
        
        return neecha_bhanga_yogas
    
    def calculate_all_yogas(self):
        """Calculate all major yogas"""
        return {
            'raj_yogas': self.calculate_raj_yogas(),
            'dhana_yogas': self.calculate_dhana_yogas(),
            'mahapurusha_yogas': self.calculate_panch_mahapurusha_yogas(),
            'neecha_bhanga_yogas': self.calculate_neecha_bhanga_yogas()
        }
    
    def _are_planets_connected(self, planet1_data, planet2_data):
        """Check if two planets are connected by conjunction or aspect"""
        house1 = planet1_data.get('house', 1)
        house2 = planet2_data.get('house', 1)
        
        # Conjunction (same house)
        if house1 == house2:
            return True
        
        # 7th house aspect (opposition)
        if abs(house1 - house2) == 6 or (house1 + house2) == 13:
            return True
        
        return False
    
    def _get_house_lord(self, house_number):
        """Get the lord of a house"""
        houses = self.chart_data.get('houses', [])
        if house_number <= len(houses):
            house_sign = houses[house_number - 1].get('sign', 0)
            return self.SIGN_LORDS.get(house_sign)
        return None