from .base_calculator import BaseCalculator
from .aspect_calculator import AspectCalculator

class YogaCalculator(BaseCalculator):
    """Calculate various Vedic yogas and combinations"""
    
    def __init__(self, birth_data=None, chart_data=None):
        super().__init__(chart_data)
        
        self.SIGN_LORDS = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        # Initialize ascendant sign for dosha calculations
        self.ascendant_sign = int(chart_data.get('ascendant', 0) / 30) if chart_data else 0
        
        # Initialize aspect calculator
        self.aspect_calc = AspectCalculator(chart_data)
    
    def calculate_raj_yogas(self):
        """Calculate Raj Yogas (royal combinations)"""
        planets = self.chart_data.get('planets', {})
        raj_yogas = []
        
        # Kendra-Trikona Raj Yoga: Lords of Kendra and Trikona houses connected
        kendra_houses = [1, 4, 7, 10]
        trikona_houses = [1, 5, 9]
        processed_pairs = set()
        
        for kendra_house in kendra_houses:
            kendra_lord = self._get_house_lord(kendra_house)
            if not kendra_lord or kendra_lord not in planets:
                continue
                
            for trikona_house in trikona_houses:
                if kendra_house == trikona_house:  # Skip same house
                    continue
                    
                trikona_lord = self._get_house_lord(trikona_house)
                if not trikona_lord or trikona_lord not in planets:
                    continue
                
                if kendra_lord == trikona_lord:  # Same planet can't form yoga with itself
                    continue
                
                # Prevent duplicate pairs
                pair = tuple(sorted([kendra_lord, trikona_lord]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                
                # Check if lords are connected
                kendra_lord_data = planets[kendra_lord].copy()
                kendra_lord_data['name'] = kendra_lord
                trikona_lord_data = planets[trikona_lord].copy()
                trikona_lord_data['name'] = trikona_lord
                
                if self._are_planets_connected(kendra_lord_data, trikona_lord_data):
                    raj_yogas.append({
                        'name': 'Kendra-Trikona Raj Yoga',
                        'planets': [kendra_lord, trikona_lord],
                        'houses': [planets[kendra_lord].get('house', 1), planets[trikona_lord].get('house', 1)],
                        'strength': 'High',
                        'description': f'{kendra_house}th lord {kendra_lord} and {trikona_house}th lord {trikona_lord} connected'
                    })
        
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
            'Mars': {'name': 'Ruchaka Yoga', 'houses': [1, 4, 7, 10], 'signs': [0, 7, 9]},  # Aries, Scorpio, Capricorn(exalt)
            'Mercury': {'name': 'Bhadra Yoga', 'houses': [1, 4, 7, 10], 'signs': [2, 5]},  # Gemini, Virgo(own+exalt)
            'Jupiter': {'name': 'Hamsa Yoga', 'houses': [1, 4, 7, 10], 'signs': [8, 11, 3]},  # Sagittarius, Pisces, Cancer(exalt)
            'Venus': {'name': 'Malavya Yoga', 'houses': [1, 4, 7, 10], 'signs': [1, 6, 11]},  # Taurus, Libra, Pisces(exalt)
            'Saturn': {'name': 'Sasha Yoga', 'houses': [1, 4, 7, 10], 'signs': [9, 10, 6]}  # Capricorn, Aquarius, Libra(exalt)
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
            'education_yogas': self.calculate_education_yogas(),
            'marriage_yogas': self.calculate_marriage_yogas(),
            'major_doshas': self.calculate_major_doshas()
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
        """Check if planets are in mutual aspect using AspectCalculator"""
        if len(planet_names) < 2:
            return False
        
        # Check if any two planets aspect each other using proper aspect calculation
        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                planet1 = planet_names[i]
                planet2 = planet_names[j]
                
                if planet1 not in planets or planet2 not in planets:
                    continue
                
                planet1_data = planets[planet1].copy()
                planet1_data['name'] = planet1
                planet2_data = planets[planet2].copy()
                planet2_data['name'] = planet2
                
                if self._are_planets_connected(planet1_data, planet2_data):
                    return True
        return False
    
    def _are_planets_connected(self, planet1_data, planet2_data):
        """Check if two planets are connected by conjunction or aspect using AspectCalculator"""
        house1 = planet1_data.get('house', 1)
        house2 = planet2_data.get('house', 1)
        planet1_name = planet1_data.get('name', '')
        planet2_name = planet2_data.get('name', '')
        
        # 1. Conjunction (same house)
        if house1 == house2:
            return True
        
        # 2. Use AspectCalculator to check if planet1 aspects house2
        aspecting_planets_house2 = self.aspect_calc.get_aspecting_planets(house2)
        if planet1_name in aspecting_planets_house2:
            return True
        
        # 3. Use AspectCalculator to check if planet2 aspects house1
        aspecting_planets_house1 = self.aspect_calc.get_aspecting_planets(house1)
        if planet2_name in aspecting_planets_house1:
            return True
        
        return False
    
    def _get_house_lord(self, house_number):
        """Get the lord of a house"""
        houses = self.chart_data.get('houses', [])
        if house_number <= len(houses):
            house_sign = houses[house_number - 1].get('sign', 0)
            return self.SIGN_LORDS.get(house_sign)

    
    def get_marriage_yogas_only(self):
        """Get only marriage-related yogas from all yogas"""
        all_yogas = self.calculate_all_yogas()
        marriage_yogas = []
        
        # Add specific marriage yogas
        marriage_yogas.extend(all_yogas.get('marriage_yogas', []))
        
        # Filter other yogas for marriage relevance
        marriage_keywords = ['kalatra', 'marriage', 'spouse', 'venus', 'shukra', 'seventh', 'saptama', 'mangal', 'guru']
        
        for category_yogas in all_yogas.values():
            if isinstance(category_yogas, list):
                for yoga in category_yogas:
                    yoga_name = yoga.get('name', '').lower()
                    if any(keyword in yoga_name for keyword in marriage_keywords):
                        if yoga not in marriage_yogas:
                            marriage_yogas.append(yoga)
        
        return marriage_yogas
    
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
    
    def calculate_marriage_yogas(self):
        """Calculate marriage-specific yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Mangal Dosha (Kuja Dosha)
        yogas.extend(self._calculate_mangal_dosha())
        
        # Kalatra Yogas (marriage combinations)
        yogas.extend(self._calculate_kalatra_yogas())
        
        # Venus-Jupiter marriage yogas
        yogas.extend(self._calculate_venus_jupiter_yogas())
        
        # 7th house marriage yogas
        yogas.extend(self._calculate_seventh_house_yogas())
        
        return yogas
    
    def _calculate_mangal_dosha(self):
        """Calculate Mangal Dosha (Mars affliction in marriage houses)"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        if 'Mars' not in planets:
            return yogas
        
        mars_house = planets['Mars'].get('house', 1)
        mangal_dosha_houses = [1, 2, 4, 7, 8, 12]
        
        if mars_house in mangal_dosha_houses:
            severity = 'High' if mars_house in [1, 7, 8] else 'Medium'
            yogas.append({
                'name': 'Mangal Dosha',
                'planet': 'Mars',
                'house': mars_house,
                'strength': severity,
                'type': 'affliction',
                'description': f'Mars in {mars_house}th house - marriage delays and conflicts'
            })
        
        return yogas
    
    def _calculate_kalatra_yogas(self):
        """Calculate Kalatra (marriage) yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # 7th lord in Kendra
        seventh_lord = self._get_house_lord(7)
        if seventh_lord and seventh_lord in planets:
            seventh_lord_house = planets[seventh_lord].get('house', 1)
            if seventh_lord_house in [1, 4, 7, 10]:
                yogas.append({
                    'name': 'Kalatra Yoga',
                    'planet': seventh_lord,
                    'house': seventh_lord_house,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': f'7th lord {seventh_lord} in Kendra - strong marriage'
                })
        
        # Venus in 7th house
        if 'Venus' in planets:
            venus_house = planets['Venus'].get('house', 1)
            if venus_house == 7:
                yogas.append({
                    'name': 'Shukra Kalatra Yoga',
                    'planet': 'Venus',
                    'house': 7,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': 'Venus in 7th house - beautiful spouse, happy marriage'
                })
        
        return yogas
    
    def _calculate_venus_jupiter_yogas(self):
        """Calculate Venus-Jupiter marriage combinations"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        if 'Venus' not in planets or 'Jupiter' not in planets:
            return yogas
        
        venus_house = planets['Venus'].get('house', 1)
        jupiter_house = planets['Jupiter'].get('house', 1)
        
        # Venus-Jupiter conjunction
        if venus_house == jupiter_house:
            yogas.append({
                'name': 'Guru-Shukra Yoga',
                'planets': ['Venus', 'Jupiter'],
                'houses': [venus_house],
                'strength': 'High',
                'type': 'beneficial',
                'description': 'Venus-Jupiter conjunction - harmonious marriage, spiritual spouse'
            })
        
        # Venus-Jupiter mutual aspect
        elif self._are_planets_connected(planets['Venus'], planets['Jupiter']):
            yogas.append({
                'name': 'Guru-Shukra Drishti Yoga',
                'planets': ['Venus', 'Jupiter'],
                'houses': [venus_house, jupiter_house],
                'strength': 'Medium',
                'type': 'beneficial',
                'description': 'Venus-Jupiter aspect - balanced marriage, good values'
            })
        
        return yogas
    
    def _calculate_seventh_house_yogas(self):
        """Calculate 7th house specific marriage yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Benefics in 7th house
        benefics_in_seventh = []
        for planet in ['Jupiter', 'Venus', 'Mercury']:
            if planet in planets and planets[planet].get('house', 1) == 7:
                benefics_in_seventh.append(planet)
        
        if benefics_in_seventh:
            yogas.append({
                'name': 'Saptama Shubha Yoga',
                'planets': benefics_in_seventh,
                'houses': [7],
                'strength': 'High',
                'type': 'beneficial',
                'description': f'Benefic planets {", ".join(benefics_in_seventh)} in 7th house - good marriage'
            })
        
        # Malefics in 7th house
        malefics_in_seventh = []
        for planet in ['Mars', 'Saturn', 'Rahu', 'Ketu']:
            if planet in planets and planets[planet].get('house', 1) == 7:
                malefics_in_seventh.append(planet)
        
        if malefics_in_seventh:
            yogas.append({
                'name': 'Saptama Krura Yoga',
                'planets': malefics_in_seventh,
                'houses': [7],
                'strength': 'High',
                'type': 'affliction',
                'description': f'Malefic planets {", ".join(malefics_in_seventh)} in 7th house - marriage challenges'
            })
        
        return yogas
    
    def calculate_major_doshas(self):
        """Calculate major negative yogas (Doshas)"""
        return {
            "mangal_dosha": self._check_mangal_dosha(),
            "kaal_sarp_dosha": self._check_kaal_sarp(),
            "pitra_dosha": self._check_pitra_dosha()
        }
    
    def _check_mangal_dosha(self):
        """Mars in 1, 2, 4, 7, 8, 12 from Lagna or Moon"""
        planets = self.chart_data.get('planets', {})
        if 'Mars' not in planets or 'Moon' not in planets:
            return {"present": False, "note": "Missing planetary data"}
        
        mars_sign = planets['Mars']['sign']
        moon_sign = planets['Moon']['sign']
        
        dosha_houses = [1, 2, 4, 7, 8, 12]
        
        # Check from Lagna
        mars_house_lagna = ((mars_sign - self.ascendant_sign) % 12) + 1
        is_manglik_lagna = mars_house_lagna in dosha_houses
        
        # Check from Moon
        mars_house_moon = ((mars_sign - moon_sign) % 12) + 1
        is_manglik_moon = mars_house_moon in dosha_houses
        
        return {
            "present": is_manglik_lagna or is_manglik_moon,
            "type": "High" if (is_manglik_lagna and is_manglik_moon) else "Low",
            "from_lagna": is_manglik_lagna,
            "from_moon": is_manglik_moon,
            "mars_house_lagna": mars_house_lagna,
            "mars_house_moon": mars_house_moon
        }
    
    def _check_kaal_sarp(self):
        """All planets hemmed between Rahu and Ketu"""
        planets = self.chart_data.get('planets', {})
        if 'Rahu' not in planets or 'Ketu' not in planets:
            return {"present": False, "note": "Missing node data"}
        
        rahu_long = planets['Rahu']['longitude']
        ketu_long = planets['Ketu']['longitude']
        
        # Get other planets
        others = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        planet_longitudes = []
        
        for p in others:
            if p in planets:
                planet_longitudes.append(planets[p]['longitude'])
        
        if len(planet_longitudes) < 7:
            return {"present": False, "note": "Incomplete planetary data"}
        
        # Simple check: all planets in one hemisphere
        # Calculate arc between Rahu and Ketu
        if rahu_long < ketu_long:
            arc1_start, arc1_end = rahu_long, ketu_long
        else:
            arc1_start, arc1_end = ketu_long, rahu_long
        
        planets_in_arc = 0
        for p_long in planet_longitudes:
            if arc1_start <= p_long <= arc1_end:
                planets_in_arc += 1
        
        # KSY if all 7 planets are in one arc (simplified)
        ksy_present = planets_in_arc == 7 or planets_in_arc == 0
        
        return {
            "present": ksy_present,
            "planets_in_rahu_ketu_arc": planets_in_arc,
            "note": "Simplified calculation - all planets in one hemisphere"
        }
    
    def _check_pitra_dosha(self):
        """Sun or Moon afflicted by Nodes or Saturn in 9th"""
        planets = self.chart_data.get('planets', {})
        
        # Check 9th house occupants
        ninth_house_planets = []
        for planet, data in planets.items():
            if data.get('house') == 9:
                ninth_house_planets.append(planet)
        
        # Check Sun/Moon conjunctions with malefics
        sun_afflicted = False
        moon_afflicted = False
        
        if 'Sun' in planets and 'Saturn' in planets:
            if planets['Sun'].get('house') == planets['Saturn'].get('house'):
                sun_afflicted = True
        
        if 'Moon' in planets and 'Rahu' in planets:
            if planets['Moon'].get('house') == planets['Rahu'].get('house'):
                moon_afflicted = True
        
        pitra_present = ('Rahu' in ninth_house_planets or 'Ketu' in ninth_house_planets or 
                        'Saturn' in ninth_house_planets or sun_afflicted or moon_afflicted)
        
        return {
            "present": pitra_present,
            "ninth_house_malefics": [p for p in ninth_house_planets if p in ['Rahu', 'Ketu', 'Saturn']],
            "sun_afflicted": sun_afflicted,
            "moon_afflicted": moon_afflicted,
            "note": "Requires detailed conjunction analysis for complete assessment"
        }