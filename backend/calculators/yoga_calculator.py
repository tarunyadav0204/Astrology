from .base_calculator import BaseCalculator

class YogaCalculator(BaseCalculator):
    """Calculate various Vedic yogas and combinations"""
    
    def __init__(self, birth_data=None, chart_data=None):
        super().__init__(chart_data)
        
        self.SIGN_LORDS = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
    
    def calculate_raj_yogas(self):
        """Calculate Raj Yogas (royal combinations)"""
        planets = self.chart_data.get('planets', {})
        raj_yogas = []
        
        # Only consider actual planets, not calculated points
        valid_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        # Get valid planet data only
        valid_planet_data = {name: data for name, data in planets.items() if name in valid_planets}
        
        # Debug logging
        print(f"DEBUG: Valid planets in chart: {list(valid_planet_data.keys())}")
        for name, data in valid_planet_data.items():
            print(f"DEBUG: {name} - House: {data.get('house', 'MISSING')}, Sign: {data.get('sign', 'MISSING')}")
        
        # Check if all planets are in same house (indicates data issue)
        houses = [data.get('house', 1) for data in valid_planet_data.values()]
        unique_houses = set(houses)
        print(f"DEBUG: Houses occupied: {unique_houses}")
        
        if len(unique_houses) == 1 and len(houses) > 1:
            print(f"DEBUG: All planets in same house {list(unique_houses)[0]} - data corruption detected")
            return []
        
        # Kendra-Trikona Raj Yoga requires planets in different houses
        kendra_houses = [1, 4, 7, 10]
        trikona_houses = [1, 5, 9]
        processed_pairs = set()
        
        for planet1_name, planet1_data in valid_planet_data.items():
            house1 = planet1_data.get('house', 1)
            
            for planet2_name, planet2_data in valid_planet_data.items():
                if planet1_name == planet2_name:
                    continue
                
                # Prevent duplicate pairs
                pair = tuple(sorted([planet1_name, planet2_name]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                    
                house2 = planet2_data.get('house', 1)
                
                # Skip if same house (conjunction doesn't form Kendra-Trikona)
                if house1 == house2:
                    continue
                
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
        
        print(f"DEBUG: Found {len(raj_yogas)} Raj Yogas")
        return raj_yogas
    
    def calculate_dhana_yogas(self):
        """Calculate Dhana Yogas (wealth combinations)"""
        planets = self.chart_data.get('planets', {})
        dhana_yogas = []
        valid_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        # 2nd and 11th house lords in conjunction/mutual aspect
        house_2_lord = self._get_house_lord(2)
        house_11_lord = self._get_house_lord(11)
        
        if (house_2_lord and house_11_lord and house_2_lord != house_11_lord and
            house_2_lord in valid_planets and house_11_lord in valid_planets):
            planet1_data = planets.get(house_2_lord, {})
            planet2_data = planets.get(house_11_lord, {})
            
            if self._are_planets_connected(planet1_data, planet2_data):
                dhana_yogas.append({
                    'name': 'Dhana Yoga',
                    'planets': [house_2_lord, house_11_lord],
                    'houses': [planet1_data.get('house', 1), planet2_data.get('house', 1)],
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
                        'houses': [house],  # Add for consistency
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
    
    def calculate_gaja_kesari_yoga(self):
        """Calculate Gaja Kesari Yoga (Moon-Jupiter)"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        if 'Moon' in planets and 'Jupiter' in planets:
            moon_house = planets['Moon'].get('house', 1)
            jupiter_house = planets['Jupiter'].get('house', 1)
            
            # Check if Moon and Jupiter are in Kendra from each other
            house_diff = abs(moon_house - jupiter_house)
            if house_diff in [0, 3, 6, 9] or (moon_house + jupiter_house) == 13:
                yogas.append({
                    'name': 'Gaja Kesari Yoga',
                    'planets': ['Moon', 'Jupiter'],
                    'houses': [moon_house, jupiter_house],
                    'strength': 'High',
                    'description': 'Moon and Jupiter in mutual Kendra - wisdom and prosperity'
                })
        return yogas
    
    def calculate_amala_yoga(self):
        """Calculate Amala Yoga (Benefic in 10th from Moon/Ascendant)"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        moon_house = planets.get('Moon', {}).get('house', 1)
        tenth_from_moon = ((moon_house - 1 + 9) % 12) + 1
        
        benefics_in_tenth = []
        for planet in ['Jupiter', 'Venus', 'Mercury']:
            if planet in planets:
                planet_house = planets[planet].get('house', 1)
                if planet_house == 10 or planet_house == tenth_from_moon:
                    benefics_in_tenth.append(planet)
        
        if benefics_in_tenth:
            yogas.append({
                'name': 'Amala Yoga',
                'planets': benefics_in_tenth,
                'strength': 'High',
                'description': f'Benefic planets {", ".join(benefics_in_tenth)} in 10th house - spotless reputation'
            })
        return yogas
    
    def calculate_viparita_raja_yogas(self):
        """Calculate Viparita Raja Yogas (6th/8th/12th lords in dusthanas)"""
        yogas = []
        dusthana_lords = [self._get_house_lord(h) for h in [6, 8, 12]]
        planets = self.chart_data.get('planets', {})
        
        for lord in dusthana_lords:
            if lord and lord in planets:
                lord_house = planets[lord].get('house', 1)
                if lord_house in [6, 8, 12]:
                    yogas.append({
                        'name': 'Viparita Raja Yoga',
                        'planet': lord,
                        'house': lord_house,
                        'strength': 'Medium',
                        'description': f'Dusthana lord {lord} in dusthana house {lord_house}'
                    })
        return yogas
    
    def calculate_dharma_karma_yogas(self):
        """Calculate 9th-10th lord relationships"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        ninth_lord = self._get_house_lord(9)
        tenth_lord = self._get_house_lord(10)
        
        valid_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        if (ninth_lord and tenth_lord and ninth_lord != tenth_lord and 
            ninth_lord in valid_planets and tenth_lord in valid_planets):
            planet1_data = planets.get(ninth_lord, {})
            planet2_data = planets.get(tenth_lord, {})
            
            if self._are_planets_connected(planet1_data, planet2_data):
                yogas.append({
                    'name': 'Dharma-Karma Yoga',
                    'planets': [ninth_lord, tenth_lord],
                    'strength': 'High',
                    'description': f'{ninth_lord} and {tenth_lord} create dharmic career success'
                })
        return yogas
    
    def calculate_all_yogas(self):
        """Calculate all major yogas"""
        return {
            'raj_yogas': self.calculate_raj_yogas(),
            'dhana_yogas': self.calculate_dhana_yogas(),
            'mahapurusha_yogas': self.calculate_panch_mahapurusha_yogas(),
            'neecha_bhanga_yogas': self.calculate_neecha_bhanga_yogas(),
            'gaja_kesari_yogas': self.calculate_gaja_kesari_yoga(),
            'amala_yogas': self.calculate_amala_yoga(),
            'viparita_raja_yogas': self.calculate_viparita_raja_yogas(),
            'dharma_karma_yogas': self.calculate_dharma_karma_yogas(),
            'career_specific_yogas': self.calculate_career_specific_yogas()
        }
    
    def calculate_career_specific_yogas(self):
        """Calculate career-specific yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Get 9th and 10th house lords
        ninth_lord = self._get_house_lord(9)
        tenth_lord = self._get_house_lord(10)
        
        if not ninth_lord or not tenth_lord:
            return yogas
        
        # 10th lord in Lagna (1st house)
        if tenth_lord in planets:
            tenth_lord_house = planets[tenth_lord].get('house', 1)
            if tenth_lord_house == 1:
                yogas.append({
                    'name': 'Daśama-pati Lagna Yoga',
                    'planet': tenth_lord,
                    'house': 1,
                    'strength': 'High',
                    'description': f'10th lord {tenth_lord} in Lagna - career-centric personality, leadership',
                    'classical_reference': 'Phaladīpikā Ch. 6 § 14',
                    'sanskrit_verse': 'Daśama-patiḥ lagnage karmavān'
                })
        
        # 9th lord in 10th house (Bhagya-Karma Yoga)
        if ninth_lord in planets:
            ninth_lord_house = planets[ninth_lord].get('house', 1)
            if ninth_lord_house == 10:
                yogas.append({
                    'name': 'Bhāgya-Karma Yoga',
                    'planet': ninth_lord,
                    'house': 10,
                    'strength': 'High',
                    'description': f'9th lord {ninth_lord} in 10th house - fortune supports profession',
                    'classical_reference': 'BPHS Ch. 14 on 9th-lord results',
                    'sanskrit_verse': 'Navama-patiḥ daśame kīrti-vān'
                })
        
        # 10th lord with Saturn (Career Discipline Yoga)
        if tenth_lord in planets and 'Saturn' in planets:
            tenth_lord_house = planets[tenth_lord].get('house', 1)
            saturn_house = planets['Saturn'].get('house', 1)
            
            if tenth_lord_house == saturn_house and tenth_lord != 'Saturn':
                yogas.append({
                    'name': 'Śani-Karma Yoga',
                    'planets': [tenth_lord, 'Saturn'],
                    'houses': [tenth_lord_house, saturn_house],
                    'strength': 'High',
                    'description': f'10th lord {tenth_lord} with Saturn - structured, responsible work style',
                    'classical_reference': 'Phaladīpikā 6.16; Hora Sara 10.2',
                    'sanskrit_verse': 'Daśama-patiḥ śanisaṃyuktaḥ karma-niṣṭhaḥ'
                })
        
        return yogas
    
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