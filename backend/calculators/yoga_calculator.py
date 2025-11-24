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
            'career_specific_yogas': self.calculate_career_specific_yogas(),
            'health_yogas': self.calculate_health_yogas(),
            'education_yogas': self.calculate_education_yogas()
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
    
    def calculate_health_yogas(self):
        """Calculate health-related yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Aristha Yogas (health affliction yogas)
        yogas.extend(self._calculate_aristha_yogas())
        
        # Ayur Yogas (longevity yogas)
        yogas.extend(self._calculate_ayur_yogas())
        
        # Healing yogas
        yogas.extend(self._calculate_healing_yogas())
        
        return yogas
    
    def _calculate_aristha_yogas(self):
        """Calculate Aristha (health affliction) yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Lagna lord in 6th/8th/12th house
        lagna_lord = self._get_house_lord(1)
        if lagna_lord and lagna_lord in planets:
            lagna_lord_house = planets[lagna_lord].get('house', 1)
            if lagna_lord_house in [6, 8, 12]:
                yogas.append({
                    'name': 'Lagna Lord Aristha Yoga',
                    'planet': lagna_lord,
                    'house': lagna_lord_house,
                    'strength': 'High',
                    'type': 'affliction',
                    'description': f'Lagna lord {lagna_lord} in {lagna_lord_house}th house - health challenges'
                })
        
        # 6th lord in Lagna
        sixth_lord = self._get_house_lord(6)
        if sixth_lord and sixth_lord in planets:
            sixth_lord_house = planets[sixth_lord].get('house', 1)
            if sixth_lord_house == 1:
                yogas.append({
                    'name': 'Sixth Lord in Lagna',
                    'planet': sixth_lord,
                    'house': 1,
                    'strength': 'Medium',
                    'type': 'affliction',
                    'description': f'6th lord {sixth_lord} in Lagna - disease proneness'
                })
        
        # 8th lord in Lagna
        eighth_lord = self._get_house_lord(8)
        if eighth_lord and eighth_lord in planets:
            eighth_lord_house = planets[eighth_lord].get('house', 1)
            if eighth_lord_house == 1:
                yogas.append({
                    'name': 'Eighth Lord in Lagna',
                    'planet': eighth_lord,
                    'house': 1,
                    'strength': 'High',
                    'type': 'affliction',
                    'description': f'8th lord {eighth_lord} in Lagna - chronic health issues'
                })
        
        # Health-specific Viparita Raja Yogas (dusthana cancellation for health)
        yogas.extend(self._calculate_health_viparita_yogas())
        
        return yogas
    
    def _calculate_ayur_yogas(self):
        """Calculate Ayur (longevity) yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Lagna lord in Kendra/Trikona
        lagna_lord = self._get_house_lord(1)
        if lagna_lord and lagna_lord in planets:
            lagna_lord_house = planets[lagna_lord].get('house', 1)
            if lagna_lord_house in [1, 4, 5, 7, 9, 10]:
                yogas.append({
                    'name': 'Ayur Yoga',
                    'planet': lagna_lord,
                    'house': lagna_lord_house,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': f'Lagna lord {lagna_lord} in favorable house - good longevity'
                })
        
        # Jupiter in Lagna (natural healing)
        if 'Jupiter' in planets:
            jupiter_house = planets['Jupiter'].get('house', 1)
            if jupiter_house == 1:
                yogas.append({
                    'name': 'Guru Lagna Yoga',
                    'planet': 'Jupiter',
                    'house': 1,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': 'Jupiter in Lagna - natural healing ability, strong immunity'
                })
        
        return yogas
    
    def _calculate_healing_yogas(self):
        """Calculate healing and recovery yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Sun in 10th house (vitality)
        if 'Sun' in planets:
            sun_house = planets['Sun'].get('house', 1)
            if sun_house == 10:
                yogas.append({
                    'name': 'Surya Karma Yoga',
                    'planet': 'Sun',
                    'house': 10,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': 'Sun in 10th house - strong vitality and leadership in health'
                })
        
        # Moon in 4th house (emotional stability)
        if 'Moon' in planets:
            moon_house = planets['Moon'].get('house', 1)
            if moon_house == 4:
                yogas.append({
                    'name': 'Chandra Sukha Yoga',
                    'planet': 'Moon',
                    'house': 4,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': 'Moon in 4th house - emotional stability, good digestive health'
                })
        
        # Venus in 7th house (hormonal balance)
        if 'Venus' in planets:
            venus_house = planets['Venus'].get('house', 1)
            if venus_house == 7:
                yogas.append({
                    'name': 'Shukra Kalatra Yoga',
                    'planet': 'Venus',
                    'house': 7,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': 'Venus in 7th house - hormonal balance, reproductive health'
                })
        
        return yogas
    
    def _calculate_health_viparita_yogas(self):
        """Calculate health-specific Viparita Raja Yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # 6th lord in 8th/12th house (disease lord in other dusthana)
        sixth_lord = self._get_house_lord(6)
        if sixth_lord and sixth_lord in planets:
            sixth_lord_house = planets[sixth_lord].get('house', 1)
            if sixth_lord_house in [8, 12]:
                yogas.append({
                    'name': 'Sarala Yoga (Health)',
                    'planet': sixth_lord,
                    'house': sixth_lord_house,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': f'6th lord {sixth_lord} in {sixth_lord_house}th house - victory over diseases'
                })
        
        # 8th lord in 6th/12th house (chronic illness lord in other dusthana)
        eighth_lord = self._get_house_lord(8)
        if eighth_lord and eighth_lord in planets:
            eighth_lord_house = planets[eighth_lord].get('house', 1)
            if eighth_lord_house in [6, 12]:
                yogas.append({
                    'name': 'Vimala Yoga (Health)',
                    'planet': eighth_lord,
                    'house': eighth_lord_house,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': f'8th lord {eighth_lord} in {eighth_lord_house}th house - reduces chronic health issues'
                })
        
        # 12th lord in 6th/8th house (hospitalization lord in other dusthana)
        twelfth_lord = self._get_house_lord(12)
        if twelfth_lord and twelfth_lord in planets:
            twelfth_lord_house = planets[twelfth_lord].get('house', 1)
            if twelfth_lord_house in [6, 8]:
                yogas.append({
                    'name': 'Vipareeta Raja Yoga (Health)',
                    'planet': twelfth_lord,
                    'house': twelfth_lord_house,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': f'12th lord {twelfth_lord} in {twelfth_lord_house}th house - reduces hospitalization and mental health issues'
                })
        
        return yogas
    
    def calculate_education_yogas(self):
        """Calculate education-specific yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Saraswati Yoga - Mercury, Jupiter, Venus in conjunction/mutual aspect
        if all(p in planets for p in ['Mercury', 'Jupiter', 'Venus']):
            mercury_house = planets['Mercury'].get('house', 1)
            jupiter_house = planets['Jupiter'].get('house', 1)
            venus_house = planets['Venus'].get('house', 1)
            
            # Check for conjunction (same house)
            if mercury_house == jupiter_house == venus_house:
                yogas.append({
                    'name': 'Saraswati Yoga',
                    'planets': ['Mercury', 'Jupiter', 'Venus'],
                    'houses': [mercury_house],
                    'strength': 'High',
                    'description': 'Mercury, Jupiter, Venus conjunction - excellent learning ability and academic success'
                })
            # Check for mutual aspects
            elif self._planets_in_mutual_aspect(['Mercury', 'Jupiter', 'Venus'], planets):
                yogas.append({
                    'name': 'Saraswati Yoga (Aspect)',
                    'planets': ['Mercury', 'Jupiter', 'Venus'],
                    'houses': [mercury_house, jupiter_house, venus_house],
                    'strength': 'Medium',
                    'description': 'Mercury, Jupiter, Venus in mutual aspect - good learning ability'
                })
        
        # Budh-Aditya Yoga - Sun-Mercury conjunction
        if 'Sun' in planets and 'Mercury' in planets:
            sun_house = planets['Sun'].get('house', 1)
            mercury_house = planets['Mercury'].get('house', 1)
            
            if sun_house == mercury_house:
                yogas.append({
                    'name': 'Budh-Aditya Yoga',
                    'planets': ['Sun', 'Mercury'],
                    'houses': [sun_house],
                    'strength': 'High',
                    'description': 'Sun-Mercury conjunction - sharp intelligence and analytical abilities'
                })
        
        # Guru-Mangal Yoga - Jupiter-Mars conjunction/aspect
        if 'Jupiter' in planets and 'Mars' in planets:
            jupiter_house = planets['Jupiter'].get('house', 1)
            mars_house = planets['Mars'].get('house', 1)
            
            if jupiter_house == mars_house or self._are_planets_connected(planets['Jupiter'], planets['Mars']):
                yogas.append({
                    'name': 'Guru-Mangal Yoga',
                    'planets': ['Jupiter', 'Mars'],
                    'houses': [jupiter_house, mars_house],
                    'strength': 'Medium',
                    'description': 'Jupiter-Mars connection - technical and scientific education aptitude'
                })
        
        # Education Lord Yoga - 4th, 5th, 9th lords connected
        fourth_lord = self._get_house_lord(4)
        fifth_lord = self._get_house_lord(5)
        ninth_lord = self._get_house_lord(9)
        
        if fourth_lord and fifth_lord and ninth_lord:
            connected_lords = []
            if fourth_lord in planets and fifth_lord in planets:
                if self._are_planets_connected(planets[fourth_lord], planets[fifth_lord]):
                    connected_lords.extend([fourth_lord, fifth_lord])
            
            if fifth_lord in planets and ninth_lord in planets:
                if self._are_planets_connected(planets[fifth_lord], planets[ninth_lord]):
                    if ninth_lord not in connected_lords:
                        connected_lords.append(ninth_lord)
            
            if len(connected_lords) >= 2:
                yogas.append({
                    'name': 'Education Lord Yoga',
                    'planets': connected_lords,
                    'strength': 'High',
                    'description': f'Education house lords {" and ".join(connected_lords)} connected - strong educational foundation'
                })
        
        return yogas
    
    def _planets_in_mutual_aspect(self, planet_names, planets):
        """Check if planets are in mutual aspect"""
        houses = [planets[p].get('house', 1) for p in planet_names if p in planets]
        if len(houses) < 2:
            return False
        
        # Check if any two planets aspect each other
        for i in range(len(houses)):
            for j in range(i + 1, len(houses)):
                house_diff = abs(houses[i] - houses[j])
                if house_diff in [3, 6, 9] or (houses[i] + houses[j]) == 13:
                    return True
        return False
    
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

    
    def get_education_yogas_only(self):
        """Get only education-related yogas from all yogas"""
        all_yogas = self.calculate_all_yogas()
        education_yogas = []
        
        # Add specific education yogas
        education_yogas.extend(all_yogas.get('education_yogas', []))
        
        # Add relevant yogas from other categories
        for yoga in all_yogas.get('gaja_kesari_yogas', []):
            education_yogas.append(yoga)
        
        # Filter other yogas for education relevance
        education_keywords = ['saraswati', 'budh', 'mercury', 'jupiter', 'guru', 'education', 'learning', 'gaja', 'kesari']
        
        for category_yogas in all_yogas.values():
            if isinstance(category_yogas, list):
                for yoga in category_yogas:
                    yoga_name = yoga.get('name', '').lower()
                    if any(keyword in yoga_name for keyword in education_keywords):
                        if yoga not in education_yogas:
                            education_yogas.append(yoga)
        
        return education_yogas