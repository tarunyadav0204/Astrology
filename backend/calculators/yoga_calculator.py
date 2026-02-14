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
                        'description': f'{self._ordinal(kendra_house)} lord {kendra_lord} and {self._ordinal(trikona_house)} lord {trikona_lord} connected'
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
        exaltation_signs = {
            'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
            'Jupiter': 3, 'Venus': 11, 'Saturn': 6
        }

        for planet_name, debil_sign in debilitation_signs.items():
            if planet_name in planets:
                planet_data = planets[planet_name]
                current_sign = planet_data.get('sign', 0)
                
                if current_sign == debil_sign:
                    cancellation_reasons = []
                    
                    # Rule 1: Lord of the debilitation sign is in a Kendra from Lagna or Moon.
                    debil_lord = self.SIGN_LORDS[debil_sign]
                    if debil_lord in planets:
                        debil_lord_house = planets[debil_lord].get('house', 1)
                        moon_house = planets['Moon'].get('house', 1)
                        debil_lord_house_from_moon = (debil_lord_house - moon_house + 12) % 12 + 1
                        if debil_lord_house in [1, 4, 7, 10] or debil_lord_house_from_moon in [1, 4, 7, 10]:
                            cancellation_reasons.append(f"Lord of debilitation sign, {debil_lord}, is in a Kendra from Lagna or Moon.")

                    # Rule 2: Lord of the exaltation sign of the debilitated planet is in a Kendra from Lagna or Moon.
                    exalt_sign = exaltation_signs[planet_name]
                    exalt_lord = self.SIGN_LORDS[exalt_sign]
                    if exalt_lord in planets:
                        exalt_lord_house = planets[exalt_lord].get('house', 1)
                        moon_house = planets['Moon'].get('house', 1)
                        exalt_lord_house_from_moon = (exalt_lord_house - moon_house + 12) % 12 + 1
                        if exalt_lord_house in [1, 4, 7, 10] or exalt_lord_house_from_moon in [1, 4, 7, 10]:
                            cancellation_reasons.append(f"Lord of exaltation sign, {exalt_lord}, is in a Kendra from Lagna or Moon.")
                    
                    # Rule 3: The debilitated planet is aspected by its exaltation lord.
                    exalt_lord_aspects = self.aspect_calc.get_aspecting_planets(planet_data.get('house'))
                    if exalt_lord in exalt_lord_aspects:
                        cancellation_reasons.append(f"Debilitated planet is aspected by its exaltation lord, {exalt_lord}.")

                    # Rule 4: The debilitated planet is in conjunction with its exaltation lord.
                    if exalt_lord in planets and planets[exalt_lord].get('house') == planet_data.get('house'):
                         cancellation_reasons.append(f"Debilitated planet is conjunct with its exaltation lord, {exalt_lord}.")
                    
                    # Rule 5: The debilitated planet is aspected by the lord of the sign it is in.
                    debil_lord_aspects = self.aspect_calc.get_aspecting_planets(planet_data.get('house'))
                    if debil_lord in debil_lord_aspects:
                        cancellation_reasons.append(f"Debilitated planet is aspected by the lord of its sign, {debil_lord}.")

                    # Rule 6: Two debilitated planets aspecting each other.
                    for other_planet, other_debil_sign in debilitation_signs.items():
                        if other_planet != planet_name and other_planet in planets and planets[other_planet].get('sign') == other_debil_sign:
                            other_planet_data = planets[other_planet]
                            # Check for mutual aspect
                            if self._are_planets_connected(planet_data, other_planet_data):
                                cancellation_reasons.append(f"Debilitated planet is in mutual aspect with another debilitated planet, {other_planet}.")

                    if cancellation_reasons:
                        neecha_bhanga_yogas.append({
                            'name': 'Neecha Bhanga Raja Yoga',
                            'planet': planet_name,
                            'reason': " ".join(cancellation_reasons),
                            'strength': 'Medium',
                            'description': f'{planet_name} debilitation cancelled.'
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
    
    def calculate_nabhasa_yogas(self):
        """Calculate Nabhasa Yogas"""
        yogas = {}
        sankhya_yogas = self._calculate_sankhya_yogas()
        if sankhya_yogas:
            yogas['sankhya_yogas'] = sankhya_yogas
        akriti_yogas = self._calculate_akriti_yogas()
        if akriti_yogas:
            yogas['akriti_yogas'] = akriti_yogas
        ashraya_yogas = self._calculate_ashraya_yogas()
        if ashraya_yogas:
            yogas['ashraya_yogas'] = ashraya_yogas
        return yogas

    def _calculate_ashraya_yogas(self):
        """Calculate Ashraya Yogas (dependency-based)"""
        planets = self.chart_data.get('planets', {})
        classical_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        movable_signs = [0, 3, 6, 9]  # Aries, Cancer, Libra, Capricorn
        fixed_signs = [1, 4, 7, 10]  # Taurus, Leo, Scorpio, Aquarius
        dual_signs = [2, 5, 8, 11]  # Gemini, Virgo, Sagittarius, Pisces
        
        planet_signs = []
        for planet_name in classical_planets:
            if planet_name in planets:
                planet_signs.append(planets[planet_name].get('sign'))

        yogas = []
        
        if len(planet_signs) == 7:
            if all(s in movable_signs for s in planet_signs):
                yogas.append({
                    'name': 'Rajju Yoga',
                    'strength': 'Low',
                    'description': 'All planets in movable signs. Indicates a person who is fond of traveling and is of a jealous disposition.'
                })
            elif all(s in fixed_signs for s in planet_signs):
                yogas.append({
                    'name': 'Musala Yoga',
                    'strength': 'Medium',
                    'description': 'All planets in fixed signs. Indicates a person who is proud, wealthy, and attached to their homeland.'
                })
            elif all(s in dual_signs for s in planet_signs):
                yogas.append({
                    'name': 'Nalika Yoga',
                    'strength': 'Medium',
                    'description': 'All planets in dual signs. Indicates a person who is intelligent, wealthy, and has a fluctuating mind.'
                })
                
        return yogas


    def _calculate_akriti_yogas(self):
        """Calculate Akriti Yogas (shape-based)"""
        planets = self.chart_data.get('planets', {})
        classical_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        occupied_houses = set()
        for planet_name in classical_planets:
            if planet_name in planets:
                occupied_houses.add(planets[planet_name].get('house'))

        yogas = []

        # 1. Gada Yoga: All planets in two adjacent kendras.
        if len(occupied_houses) > 1 and all(h in [1,4] for h in occupied_houses) or \
           all(h in [4,7] for h in occupied_houses) or \
           all(h in [7,10] for h in occupied_houses) or \
           all(h in [10,1] for h in occupied_houses):
            yogas.append({
                'name': 'Gada Yoga',
                'strength': 'Medium',
                'description': 'All planets in two adjacent kendras. Indicates wealth and property.'
            })

        # 2. Sakata Yoga: All planets in the 1st and 7th houses.
        if len(occupied_houses) > 1 and all(h in [1, 7] for h in occupied_houses):
            yogas.append({
                'name': 'Sakata Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 1st and 7th houses. Indicates a life of struggle with occasional bursts of fortune.'
            })

        # 3. Vihaga Yoga: All planets in the 4th and 10th houses.
        if len(occupied_houses) > 1 and all(h in [4, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Vihaga Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 4th and 10th houses. Indicates a person who is a wanderer.'
            })

        # 4. Shringataka Yoga: All planets in the 1st, 5th, and 9th houses.
        if len(occupied_houses) > 1 and all(h in [1, 5, 9] for h in occupied_houses):
            yogas.append({
                'name': 'Shringataka Yoga',
                'strength': 'High',
                'description': 'All planets in trikonas. Indicates a life of ease and comfort.'
            })

        # 5. Hala Yoga: All planets in the 2nd, 6th, and 10th; or 3rd, 7th, and 11th; or 4th, 8th, and 12th.
        if len(occupied_houses) > 1 and all(h in [2, 6, 10] for h in occupied_houses) or \
           all(h in [3, 7, 11] for h in occupied_houses) or \
           all(h in [4, 8, 12] for h in occupied_houses):
            yogas.append({
                'name': 'Hala Yoga',
                'strength': 'Medium',
                'description': 'All planets in 2nd, 6th, 10th or 3rd, 7th, 11th or 4th, 8th, 12th. Indicates a person who is a farmer or works with the land.'
            })
            
        # 6. Vajra Yoga: Benefics in the 1st and 7th, malefics in the 4th and 10th.
        benefics = ['Venus', 'Jupiter', 'Mercury', 'Moon']
        malefics = ['Saturn', 'Mars', 'Sun']
        
        benefic_houses = set()
        malefic_houses = set()
        
        for planet in benefics:
            if planet in planets:
                benefic_houses.add(planets[planet].get('house'))
        
        for planet in malefics:
            if planet in planets:
                malefic_houses.add(planets[planet].get('house'))
                
        if all(h in [1, 7] for h in benefic_houses) and all(h in [4, 10] for h in malefic_houses):
            yogas.append({
                'name': 'Vajra Yoga',
                'strength': 'High',
                'description': 'Benefics in 1st and 7th, malefics in 4th and 10th. Indicates a powerful and influential person.'
            })
            
        # 7. Yava Yoga: Benefics in the 4th and 10th, malefics in the 1st and 7th.
        if all(h in [4, 10] for h in benefic_houses) and all(h in [1, 7] for h in malefic_houses):
            yogas.append({
                'name': 'Yava Yoga',
                'strength': 'High',
                'description': 'Benefics in 4th and 10th, malefics in 1st and 7th. Indicates a person with a difficult early life but success later.'
            })
            
        # 8. Kamala Yoga: All planets in the 1st, 4th, 7th, and 10th houses.
        if len(occupied_houses) > 1 and all(h in [1, 4, 7, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Kamala Yoga',
                'strength': 'High',
                'description': 'All planets in kendras. Indicates a person who is famous and wealthy.'
            })

        # 9. Vapi Yoga: All planets in Panapara houses (2, 5, 8, 11) or Apoklima houses (3, 6, 9, 12).
        if len(occupied_houses) > 1 and all(h in [2, 5, 8, 11] for h in occupied_houses) or \
           all(h in [3, 6, 9, 12] for h in occupied_houses):
            yogas.append({
                'name': 'Vapi Yoga',
                'strength': 'Medium',
                'description': 'All planets in Panapara or Apoklima houses. Indicates a person who is secretive and may have hidden wealth.'
            })
            
        # 10. Yoopa Yoga: All planets in the 1st, 2nd, 3rd, and 4th houses.
        if len(occupied_houses) > 1 and all(h in [1, 2, 3, 4] for h in occupied_houses):
            yogas.append({
                'name': 'Yoopa Yoga',
                'strength': 'Medium',
                'description': 'All planets in the first four houses. Indicates a person who is religious and performs sacrifices.'
            })

        # 11. Sara Yoga: All planets in the 4th, 5th, 6th, and 7th houses.
        if len(occupied_houses) > 1 and all(h in [4, 5, 6, 7] for h in occupied_houses):
            yogas.append({
                'name': 'Sara Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 4th, 5th, 6th, and 7th houses. Indicates a person who is strong and powerful.'
            })

        # 12. Sakti Yoga: All planets in the 7th, 8th, 9th, and 10th houses.
        if len(occupied_houses) > 1 and all(h in [7, 8, 9, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Sakti Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7th, 8th, 9th, and 10th houses. Indicates a person who is lazy and unhappy.'
            })
            
        # 13. Danda Yoga: All planets in the 10th, 11th, 12th, and 1st houses.
        if len(occupied_houses) > 1 and all(h in [10, 11, 12, 1] for h in occupied_houses):
            yogas.append({
                'name': 'Danda Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 10th, 11th, 12th, and 1st houses. Indicates a person who is poor and unfortunate.'
            })

        # 14. Nauka Yoga: All planets in the 7 houses from the 1st to the 7th.
        if len(occupied_houses) > 1 and all(h in [1, 2, 3, 4, 5, 6, 7] for h in occupied_houses):
            yogas.append({
                'name': 'Nauka Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 1st to the 7th. Indicates a person who is famous and wealthy.'
            })
            
        # 15. Koota Yoga: All planets in the 7 houses from the 4th to the 10th.
        if len(occupied_houses) > 1 and all(h in [4, 5, 6, 7, 8, 9, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Koota Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 4th to the 10th. Indicates a person who is a liar and a cheat.'
            })
            
        # 16. Chatra Yoga: All planets in the 7 houses from the 7th to the 1st.
        if len(occupied_houses) > 1 and all(h in [7, 8, 9, 10, 11, 12, 1] for h in occupied_houses):
            yogas.append({
                'name': 'Chatra Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 7th to the 1st. Indicates a person who is a king or a minister.'
            })
            
        # 17. Chapa Yoga: All planets in the 7 houses from the 10th to the 4th.
        if len(occupied_houses) > 1 and all(h in [10, 11, 12, 1, 2, 3, 4] for h in occupied_houses):
            yogas.append({
                'name': 'Chapa Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 10th to the 4th. Indicates a person who is a hunter or a warrior.'
            })
            
        # 18. Ardha Chandra Yoga: All planets in the 7 houses starting from a house other than a Kendra.
        panapara_start = [2, 5, 8, 11]
        apoklima_start = [3, 6, 9, 12]
        
        for start_house in panapara_start + apoklima_start:
            house_range = [(start_house + i -1) % 12 + 1 for i in range(7)]
            if len(occupied_houses) > 1 and all(h in house_range for h in occupied_houses):
                 yogas.append({
                    'name': 'Ardha Chandra Yoga',
                    'strength': 'Medium',
                    'description': 'All planets in 7 consecutive houses starting from a non-kendra house. Indicates a person who is a commander or a leader.'
                })
                 break

        # 19. Samudra Yoga: All planets in the even houses (2, 4, 6, 8, 10, 12).
        if len(occupied_houses) > 1 and all(h in [2, 4, 6, 8, 10, 12] for h in occupied_houses):
            yogas.append({
                'name': 'Samudra Yoga',
                'strength': 'High',
                'description': 'All planets in even houses. Indicates a person who is wealthy and prosperous.'
            })

        # 20. Chakra Yoga: All planets in the odd houses (1, 3, 5, 7, 9, 11).
        if len(occupied_houses) > 1 and all(h in [1, 3, 5, 7, 9, 11] for h in occupied_houses):
            yogas.append({
                'name': 'Chakra Yoga',
                'strength': 'High',
                'description': 'All planets in odd houses. Indicates a person who is a king or a ruler.'
            })

        return yogas


    def _calculate_sankhya_yogas(self):
        """Calculate Sankhya Yogas (number-based)"""
        planets = self.chart_data.get('planets', {})
        classical_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        occupied_signs = set()
        for planet_name in classical_planets:
            if planet_name in planets:
                occupied_signs.add(planets[planet_name].get('sign'))
                
        num_occupied_signs = len(occupied_signs)
        sankhya_yoga_name = ""
        description = ""
        
        if num_occupied_signs == 1:
            sankhya_yoga_name = "Gola Yoga"
            description = "All planets in one sign - focused, but can be narrow-minded."
        elif num_occupied_signs == 2:
            sankhya_yoga_name = "Yuga Yoga"
            description = "All planets in two signs - can be pulled in two directions."
        elif num_occupied_signs == 3:
            sankhya_yoga_name = "Shula Yoga"
            description = "All planets in three signs - can indicate sharp or painful experiences."
        elif num_occupied_signs == 4:
            sankhya_yoga_name = "Kedara Yoga"
            description = "All planets in four signs - resourceful and helpful."
        elif num_occupied_signs == 5:
            sankhya_yoga_name = "Pasha Yoga"
            description = "All planets in five signs - can be bound by obligations."
        elif num_occupied_signs == 6:
            sankhya_yoga_name = "Dama Yoga"
            description = "All planets in six signs - generous and skillful."
        elif num_occupied_signs == 7:
            sankhya_yoga_name = "Veena Yoga"
            description = "All planets in seven signs - talented, enjoys arts and music."
            
        if sankhya_yoga_name:
            return [{
                'name': sankhya_yoga_name,
                'strength': 'Medium',
                'description': description
            }]
        return []
    
    def calculate_all_yogas(self):
        """Calculate all major yogas"""
        parivartana_yogas = self.calculate_parivartana_yogas()
        # Separate parivartana yogas into their respective categories
        maha_yogas = [y for y in parivartana_yogas if y['name'] == 'Maha Yoga']
        dainya_yogas = [y for y in parivartana_yogas if y['name'] == 'Dainya Yoga']
        khala_yogas = [y for y in parivartana_yogas if y['name'] == 'Khala Yoga']
        other_parivartana_yogas = [y for y in parivartana_yogas if y['name'] == 'Parivartana Yoga']
        
        return {
            'raj_yogas': self.calculate_raj_yogas() + maha_yogas,
            'dhana_yogas': self.calculate_dhana_yogas(),
            'mahapurusha_yogas': self.calculate_panch_mahapurusha_yogas(),
            'neecha_bhanga_yogas': self.calculate_neecha_bhanga_yogas(),
            'gaja_kesari_yogas': self.calculate_gaja_kesari_yoga(),
            'amala_yogas': self.calculate_amala_yoga(),
            'viparita_raja_yogas': self.calculate_viparita_raja_yogas(),
            'dharma_karma_yogas': self.calculate_dharma_karma_yogas(),
            'nabhasa_yogas': self.calculate_nabhasa_yogas(),
            'chandra_yogas': self.calculate_chandra_yogas(),
            'surya_yogas': self.calculate_surya_yogas(),
            'parivartana_yogas': {
                'maha_yogas': maha_yogas,
                'dainya_yogas': dainya_yogas,
                'khala_yogas': khala_yogas,
                'other_parivartana_yogas': other_parivartana_yogas
            },
            'career_specific_yogas': self.calculate_career_specific_yogas(),
            'health_yogas': self.calculate_health_yogas(),
            'education_yogas': self.calculate_education_yogas(),
            'marriage_yogas': self.calculate_marriage_yogas(),
            'major_doshas': self.calculate_major_doshas()
        }

    def calculate_other_yogas(self):
        """Calculate Lakshmi, Sakata, Shubha/Papa Kartari and Chamara Yogas"""
        planets = self.chart_data.get('planets', {})
        if not planets:
            return []

        yogas = []

        # Lakshmi Yoga
        ninth_lord = self._get_house_lord(9)
        lagna_lord = self._get_house_lord(1)
        if ninth_lord and lagna_lord and ninth_lord in planets and lagna_lord in planets:
            ninth_lord_house = planets[ninth_lord].get('house')
            # A simplified check for strong lagna lord.
            if ninth_lord_house in [1, 4, 5, 7, 9, 10] and planets[lagna_lord].get('strength') == 'High':
                yogas.append({
                    'name': 'Lakshmi Yoga',
                    'strength': 'High',
                    'description': 'Lord of the 9th house is in a Kendra or Trikona and the Lagna lord is strong. Indicates wealth and prosperity.'
                })

        # Sakata Yoga
        if 'Jupiter' in planets and 'Moon' in planets:
            jupiter_house = planets['Jupiter'].get('house')
            moon_house = planets['Moon'].get('house')
            
            house_diff = (jupiter_house - moon_house + 12) % 12
            if house_diff == 5 or house_diff == 7: # 6th or 8th from Moon
                yogas.append({
                    'name': 'Sakata Yoga',
                    'strength': 'Low',
                    'description': 'Jupiter in the 6th or 8th house from the Moon. Indicates a life of struggle with occasional bursts of fortune.'
                })

        # Shubha/Papa Kartari Yoga
        benefics = ['Venus', 'Jupiter', 'Mercury']
        malefics = ['Saturn', 'Mars', 'Rahu', 'Ketu']
        
        # Shubha Kartari Yoga
        planets_in_second = [p for p,d in planets.items() if d.get('house') == 2]
        planets_in_twelfth = [p for p,d in planets.items() if d.get('house') == 12]
        
        if any(p in benefics for p in planets_in_second) and any(p in benefics for p in planets_in_twelfth):
            yogas.append({
                'name': 'Shubha Kartari Yoga',
                'strength': 'Medium',
                'description': 'Benefic planets in the 2nd and 12th houses from the Lagna. Indicates a protected and easy life.'
            })
        # Papa Kartari Yoga
        if any(p in malefics for p in planets_in_second) and any(p in malefics for p in planets_in_twelfth):
            yogas.append({
                'name': 'Papa Kartari Yoga',
                'strength': 'Low',
                'description': 'Malefic planets in the 2nd and 12th houses from the Lagna. Indicates a life of struggle and hardship.'
            })
            
        # Chamara Yoga
        lagna_lord = self._get_house_lord(1)
        if lagna_lord and lagna_lord in planets:
            lagna_lord_data = planets[lagna_lord]
            # Lagna lord exalted and aspected by Jupiter
            if 'is_exalted' in lagna_lord_data and lagna_lord_data.get('is_exalted') and 'Jupiter' in self.aspect_calc.get_aspecting_planets(lagna_lord_data.get('house')):
                yogas.append({
                    'name': 'Chamara Yoga',
                    'strength': 'High',
                    'description': 'Lagna lord is exalted and aspected by Jupiter. Indicates a long, prosperous, and reputable life.'
                })
        
        # Two benefics in Lagna, 7th, 9th, or 10th
        for h in [1, 7, 9, 10]:
            benefics_in_house = [p for p in benefics if p in planets and planets[p].get('house') == h]
            if len(benefics_in_house) >= 2:
                yogas.append({
                    'name': 'Chamara Yoga',
                    'strength': 'High',
                    'description': f'Two or more benefic planets in the {h}th house. Indicates a long, prosperous, and reputable life.'
                })

        return yogas
        
    def calculate_parivartana_yogas(self):
        """Calculate Parivartana Yogas (exchange of house lords)"""
        planets = self.chart_data.get('planets', {})
        if not planets:
            return []

        yogas = []
        house_lords = {i: self._get_house_lord(i) for i in range(1, 13)}
        
        # Get planet positions
        planet_houses = {p: d.get('house') for p, d in planets.items()}

        # Check for exchanges
        exchanged_lords = set()
        for h1 in range(1, 13):
            for h2 in range(h1 + 1, 13):
                l1 = house_lords.get(h1)
                l2 = house_lords.get(h2)

                if l1 and l2 and l1 != l2 and l1 in planet_houses and l2 in planet_houses:
                    # Check if l1 is in h2 and l2 is in h1
                    if planet_houses.get(l1) == h2 and planet_houses.get(l2) == h1:
                        
                        # Avoid duplicates
                        pair = tuple(sorted((l1, l2)))
                        if pair in exchanged_lords:
                            continue
                        exchanged_lords.add(pair)

                        # Classify the yoga
                        yoga_type = ''
                        description = ''
                        strength = 'Medium'
                        
                        dusthana_houses = [6, 8, 12]
                        trikona_houses = [1, 5, 9]
                        kendra_houses = [1, 4, 7, 10]
                        
                        is_h1_dusthana = h1 in dusthana_houses
                        is_h2_dusthana = h2 in dusthana_houses
                        
                        is_h1_trikona = h1 in trikona_houses
                        is_h2_trikona = h2 in trikona_houses
                        
                        is_h1_kendra = h1 in kendra_houses
                        is_h2_kendra = h2 in kendra_houses

                        if is_h1_dusthana or is_h2_dusthana:
                            yoga_type = 'Dainya Yoga'
                            description = f"Exchange between lord of {h1} and {h2}. Indicates struggles and challenges."
                            strength = 'Low'
                        elif h1 == 3 or h2 == 3:
                            yoga_type = 'Khala Yoga'
                            description = f"Exchange between lord of {h1} and {h2}. Indicates a person who is clever and cunning."
                        elif (is_h1_kendra and is_h2_trikona) or (is_h1_trikona and is_h2_kendra):
                            yoga_type = 'Maha Yoga'
                            description = f"Exchange between lord of {h1} and {h2}. A powerful Raj Yoga, indicating success and high status."
                            strength = 'High'
                        else:
                            yoga_type = 'Parivartana Yoga'
                            description = f"Exchange between lord of {h1} and {h2}."

                        yogas.append({
                            'name': yoga_type,
                            'planets': [l1, l2],
                            'houses': [h1, h2],
                            'strength': strength,
                            'description': description
                        })

        return yogas

    def calculate_surya_yogas(self):
        """Calculate Surya Yogas (Sun-based)"""
        planets = self.chart_data.get('planets', {})
        if 'Sun' not in planets:
            return []

        yogas = []
        sun_house = planets['Sun'].get('house')
        
        planets_in_second_from_sun = []
        planets_in_twelfth_from_sun = []
        
        second_from_sun = (sun_house % 12) + 1
        twelfth_from_sun = (sun_house - 2 + 12) % 12 + 1

        for planet, data in planets.items():
            if planet not in ['Sun', 'Rahu', 'Ketu', 'Moon']:
                if data.get('house') == second_from_sun:
                    planets_in_second_from_sun.append(planet)
                if data.get('house') == twelfth_from_sun:
                    planets_in_twelfth_from_sun.append(planet)

        if planets_in_second_from_sun and not planets_in_twelfth_from_sun:
            yogas.append({
                'name': 'Vesi Yoga',
                'strength': 'Medium',
                'description': 'Planets in the 2nd house from the Sun. Makes the person truthful, and skillful.'
            })
        elif not planets_in_second_from_sun and planets_in_twelfth_from_sun:
            yogas.append({
                'name': 'Vasi Yoga',
                'strength': 'Medium',
                'description': 'Planets in the 12th house from the Sun. Makes the person charitable, and famous.'
            })
        elif planets_in_second_from_sun and planets_in_twelfth_from_sun:
            yogas.append({
                'name': 'Ubhayachari Yoga',
                'strength': 'High',
                'description': 'Planets in both the 2nd and 12th houses from the Sun. Makes the person a king or a ruler.'
            })
            
        return yogas
    
    def calculate_chandra_yogas(self):
        """Calculate Chandra Yogas (Moon-based)"""
        planets = self.chart_data.get('planets', {})
        if 'Moon' not in planets:
            return []

        yogas = []
        moon_house = planets['Moon'].get('house')
        
        planets_in_second_from_moon = []
        planets_in_twelfth_from_moon = []
        
        second_from_moon = (moon_house % 12) + 1
        twelfth_from_moon = (moon_house - 2 + 12) % 12 + 1

        for planet, data in planets.items():
            if planet not in ['Sun', 'Rahu', 'Ketu', 'Moon']:
                if data.get('house') == second_from_moon:
                    planets_in_second_from_moon.append(planet)
                if data.get('house') == twelfth_from_moon:
                    planets_in_twelfth_from_moon.append(planet)

        if planets_in_second_from_moon and not planets_in_twelfth_from_moon:
            yogas.append({
                'name': 'Sunapha Yoga',
                'strength': 'Medium',
                'description': 'Planets in the 2nd house from the Moon. Indicates self-earned wealth and intelligence.'
            })
        elif not planets_in_second_from_moon and planets_in_twelfth_from_moon:
            yogas.append({
                'name': 'Anapha Yoga',
                'strength': 'Medium',
                'description': 'Planets in the 12th house from the Moon. Indicates good health, and an attractive personality.'
            })
        elif planets_in_second_from_moon and planets_in_twelfth_from_moon:
            yogas.append({
                'name': 'Durudhura Yoga',
                'strength': 'High',
                'description': 'Planets in both the 2nd and 12th houses from the Moon. Indicates a person who enjoys a luxurious life.'
            })
        else:
            # Kemadruma Yoga check
            # No planets in 2nd or 12th from Moon.
            # Also check for cancellation: No planets in kendra from Moon
            kendra_from_moon = [(moon_house + i - 1) % 12 + 1 for i in [1, 4, 7, 10]]
            planets_in_kendra_from_moon = False
            for planet, data in planets.items():
                if planet != 'Moon' and data.get('house') in kendra_from_moon:
                    planets_in_kendra_from_moon = True
                    break
            if not planets_in_kendra_from_moon:
                 yogas.append({
                    'name': 'Kemadruma Yoga',
                    'strength': 'Low',
                    'description': 'No planets in the 2nd or 12th from the Moon, and no planets in a kendra from the Moon. Indicates poverty, struggle, and loneliness.'
                })


        # Adhi Yoga
        benefics = ['Mercury', 'Venus', 'Jupiter']
        benefics_in_6_7_8 = {'6': [], '7': [], '8': []}
        
        sixth_from_moon = (moon_house + 5 - 1) % 12 + 1
        seventh_from_moon = (moon_house + 6 - 1) % 12 + 1
        eighth_from_moon = (moon_house + 7 - 1) % 12 + 1

        for planet in benefics:
            if planet in planets:
                p_house = planets[planet].get('house')
                if p_house == sixth_from_moon:
                    benefics_in_6_7_8['6'].append(planet)
                if p_house == seventh_from_moon:
                    benefics_in_6_7_8['7'].append(planet)
                if p_house == eighth_from_moon:
                    benefics_in_6_7_8['8'].append(planet)
                    
        if benefics_in_6_7_8['6'] or benefics_in_6_7_8['7'] or benefics_in_6_7_8['8']:
            yogas.append({
                'name': 'Adhi Yoga',
                'strength': 'High',
                'description': 'Benefics in the 6th, 7th, or 8th from the Moon. Indicates leadership, wealth, and a happy life.'
            })
            
        return yogas
    
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
                house_significance = self._get_saraswati_house_significance(mercury_house)
                yogas.append({
                    'name': 'Saraswati Yoga',
                    'planets': ['Mercury', 'Jupiter', 'Venus'],
                    'houses': [mercury_house],
                    'strength': 'High',
                    'description': f'Mercury, Jupiter, Venus conjunction in {mercury_house}th house - {house_significance}'
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
                house_significance = self._get_budh_aditya_house_significance(sun_house)
                strength = 'High' if sun_house in [1, 4, 5, 9, 10] else 'Medium'
                yogas.append({
                    'name': 'Budh-Aditya Yoga',
                    'planets': ['Sun', 'Mercury'],
                    'houses': [sun_house],
                    'strength': strength,
                    'description': f'Sun-Mercury conjunction in {sun_house}th house - {house_significance}'
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
    
    def _get_saraswati_house_significance(self, house: int) -> str:
        """Get house-specific significance for Saraswati Yoga"""
        significances = {
            1: "exceptional learning ability and academic leadership",
            2: "wealth through education and eloquent speech", 
            3: "creative writing and communication skills",
            4: "strong foundation in traditional learning",
            5: "brilliant intelligence and academic excellence",
            6: "victory in competitive exams and debates",
            7: "success in collaborative learning and partnerships",
            8: "deep research abilities and occult knowledge",
            9: "higher education success and teaching abilities",
            10: "career success through education and reputation",
            11: "gains and recognition through academic achievements",
            12: "foreign education and spiritual learning"
        }
        return significances.get(house, "general learning enhancement")
    
    def _get_budh_aditya_house_significance(self, house: int) -> str:
        """Get house-specific significance for Budh-Aditya Yoga"""
        significances = {
            1: "sharp analytical mind and leadership in academics",
            2: "intelligent speech and financial acumen",
            3: "excellent communication and writing skills", 
            4: "strong logical foundation and practical learning",
            5: "brilliant intelligence and academic success",
            6: "analytical problem-solving in competitive fields",
            7: "diplomatic intelligence and partnership success",
            8: "research excellence but challenges in formal education",
            9: "philosophical intelligence and higher learning",
            10: "career success through intellectual abilities",
            11: "networking skills and gains through intelligence",
            12: "intuitive intelligence but may face educational obstacles"
        }
        return significances.get(house, "enhanced intellectual abilities")
    
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
    
    def _ordinal(self, n):
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    
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

        rahu_house = planets['Rahu'].get('house')
        ketu_house = planets['Ketu'].get('house')
        
        # All other planets
        other_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        # Check if all other planets are between Rahu and Ketu
        is_kal_sarp = True
        for planet in other_planets:
            if planet in planets:
                p_house = planets[planet].get('house')
                # This is a simplified check, a more accurate one would be to check the longitude
                if not (rahu_house < p_house < ketu_house or (ketu_house < rahu_house and (p_house > rahu_house or p_house < ketu_house))):
                     is_kal_sarp = False
                     break
        
        if not is_kal_sarp:
            # Check the other way around
            is_kal_sarp = True
            for planet in other_planets:
                if planet in planets:
                    p_house = planets[planet].get('house')
                    if not (ketu_house < p_house < rahu_house or (rahu_house < ketu_house and (p_house > ketu_house or p_house < rahu_house))):
                        is_kal_sarp = False
                        break

        if not is_kal_sarp:
            return {"present": False}

        # Determine the type of Kaal Sarp Yoga
        kaal_sarp_type = ""
        if rahu_house == 1:
            kaal_sarp_type = "Anant"
        elif rahu_house == 2:
            kaal_sarp_type = "Kulik"
        elif rahu_house == 3:
            kaal_sarp_type = "Vasuki"
        elif rahu_house == 4:
            kaal_sarp_type = "Shankhpal"
        elif rahu_house == 5:
            kaal_sarp_type = "Padma"
        elif rahu_house == 6:
            kaal_sarp_type = "Mahapadma"
        elif rahu_house == 7:
            kaal_sarp_type = "Takshak"
        elif rahu_house == 8:
            kaal_sarp_type = "Karkotak"
        elif rahu_house == 9:
            kaal_sarp_type = "Shankhachood"
        elif rahu_house == 10:
            kaal_sarp_type = "Ghatak"
        elif rahu_house == 11:
            kaal_sarp_type = "Vishdhar"
        elif rahu_house == 12:
            kaal_sarp_type = "Sheshnag"

        # Check for cancellations
        cancellation_reasons = []
        # 1. If Lagna lord is strong
        lagna_lord = self._get_house_lord(1)
        if lagna_lord and lagna_lord in planets:
            # This is a simplified check for strength. A more detailed check would be needed for a world-class calculator.
            if planets[lagna_lord].get('strength', 'Medium') == 'High':
                cancellation_reasons.append("Lagna lord is strong.")
                
        # 2. If there is a strong Raja Yoga
        if self.calculate_raj_yogas():
            cancellation_reasons.append("A strong Raja Yoga is present.")

        return {
            "present": True,
            "type": kaal_sarp_type,
            "cancellation": bool(cancellation_reasons),
            "cancellation_reason": " ".join(cancellation_reasons)
        }
    
    def _check_pitra_dosha(self):
        """Sun or Moon afflicted by Nodes or Saturn in 9th"""
        planets = self.chart_data.get('planets', {})
        if not planets:
            return {"present": False, "note": "Missing planetary data"}

        pitra_dosha_reasons = []

        # 1. Check afflictions to the 9th house from Lagna, Sun, and Moon
        for ref_point in ['ascendant', 'Sun', 'Moon']:
            if ref_point == 'ascendant':
                ref_house = 1
            elif ref_point in planets:
                ref_house = planets[ref_point].get('house')
            else:
                continue
                
            ninth_house = (ref_house + 8 - 1) % 12 + 1
            
            for malefic in ['Rahu', 'Ketu', 'Saturn']:
                if malefic in planets and planets[malefic].get('house') == ninth_house:
                    pitra_dosha_reasons.append(f"{malefic} in the 9th house from {ref_point}.")

        # 2. Check afflictions to the 9th lord
        ninth_lord = self._get_house_lord(9)
        if ninth_lord and ninth_lord in planets:
            ninth_lord_house = planets[ninth_lord].get('house')
            # Affliction by conjunction
            for malefic in ['Rahu', 'Ketu', 'Saturn']:
                if malefic in planets and planets[malefic].get('house') == ninth_lord_house:
                    pitra_dosha_reasons.append(f"9th lord {ninth_lord} is conjunct with {malefic}.")
            # Affliction by aspect
            aspecting_planets = self.aspect_calc.get_aspecting_planets(ninth_lord_house)
            for malefic in ['Rahu', 'Ketu', 'Saturn']:
                if malefic in aspecting_planets:
                    pitra_dosha_reasons.append(f"9th lord {ninth_lord} is aspected by {malefic}.")

        # 3. Check afflictions to Sun and Moon
        for luminary in ['Sun', 'Moon']:
            if luminary in planets:
                luminary_house = planets[luminary].get('house')
                for malefic in ['Rahu', 'Ketu', 'Saturn']:
                    if malefic in planets and planets[malefic].get('house') == luminary_house:
                        pitra_dosha_reasons.append(f"{luminary} is conjunct with {malefic}.")
                    aspecting_planets = self.aspect_calc.get_aspecting_planets(luminary_house)
                    if malefic in aspecting_planets:
                        pitra_dosha_reasons.append(f"{luminary} is aspected by {malefic}.")

        if pitra_dosha_reasons:
            return {
                "present": True,
                "reasons": list(set(pitra_dosha_reasons)) # remove duplicates
            }

        return {"present": False}