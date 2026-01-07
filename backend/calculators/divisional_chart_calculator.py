"""Divisional chart calculator extracted from main.py"""

from .base_calculator import BaseCalculator

class DivisionalChartCalculator(BaseCalculator):
    """Calculate divisional charts using proper Vedic formulas"""
    
    def calculate_divisional_chart(self, division_number=9):
        """Calculate divisional chart - extracted from main.py"""
        
        print(f"\n🔮 [BACKEND] Starting divisional chart calculation for D{division_number}")
        print(f"📍 [BACKEND] Input ascendant: {self.chart_data.get('ascendant')}")
        
        def get_divisional_sign(sign, degree_in_sign, division):
            """Calculate divisional sign using proper Vedic formulas with boundary buffer"""
            EPS = 1e-9  # Prevent 10.0 becoming 9.999
            part = int((degree_in_sign + EPS) / (30.0/division))
            
            # --- MISSING CHARTS ADDED ---
            
            if division == 2:  # Hora (D2) - Parashara Hora
                # Odd Signs: 0-15 Sun(Leo), 15-30 Moon(Cancer)
                # Even Signs: 0-15 Moon(Cancer), 15-30 Sun(Leo)
                is_first_half = degree_in_sign < 15
                if sign % 2 == 0:  # Odd Sign (Aries=0)
                    return 4 if is_first_half else 3  # Leo(4) else Cancer(3)
                else:  # Even Sign
                    return 3 if is_first_half else 4  # Cancer(3) else Leo(4)

            elif division == 3:  # Drekkana (D3) - Parashara
                # 0-10: Self, 10-20: 5th, 20-30: 9th
                if part == 0: return sign
                elif part == 1: return (sign + 4) % 12
                else: return (sign + 8) % 12

            elif division == 4:  # Chaturthamsa (D4)
                # 1st part: Self, 2nd: 4th, 3rd: 7th, 4th: 10th
                return (sign + (part * 3)) % 12

            # --- EXISTING CHARTS ---

            elif division == 7:  # Saptamsa (D7) - CORRECTED
                # Traditional rule: Odd signs start from same sign, Even signs start from 7th sign
                # But the issue might be in how we determine odd/even or calculate parts
                if sign % 2 == 0:  # Aries(0), Gemini(2), Leo(4) etc - Odd signs in astrology
                    start_sign = sign
                else:  # Taurus(1), Cancer(3), Virgo(5) etc - Even signs in astrology  
                    start_sign = (sign + 6) % 12  # 7th sign from current
                return (start_sign + part) % 12

            elif division == 9:  # Navamsa (D9)
                if sign in [0, 3, 6, 9]: start = sign            # Movable: Self
                elif sign in [1, 4, 7, 10]: start = (sign + 8)   # Fixed: 9th
                else: start = (sign + 4)                         # Dual: 5th
                return (start + part) % 12

            elif division == 10:  # Dasamsa (D10)
                if sign % 2 == 0: return (sign + part) % 12      # Odd: Self
                else: return ((sign + 8) + part) % 12            # Even: 9th

            elif division == 12:  # Dwadasamsa (D12)
                return (sign + part) % 12                        # Start from self

            elif division == 16:  # Shodasamsa (D16)
                if sign in [0, 3, 6, 9]: start = 0               # Movable: Aries
                elif sign in [1, 4, 7, 10]: start = 4            # Fixed: Leo
                else: start = 8                                  # Dual: Sag
                return (start + part) % 12

            elif division == 20:  # Vimsamsa (D20)
                if sign in [0, 3, 6, 9]: start = 0               # Movable: Aries
                elif sign in [1, 4, 7, 10]: start = 8            # Fixed: Sag
                else: start = 4                                  # Dual: Leo
                return (start + part) % 12

            elif division == 24:  # Chaturvimsamsa (D24)
                start = 4 if sign % 2 == 0 else 3                # Odd: Leo, Even: Cancer
                return (start + part) % 12

            elif division == 27:  # Saptavimsamsa (D27)
                if sign in [0, 4, 8]: start = 0      # Fire: Aries
                elif sign in [1, 5, 9]: start = 3    # Earth: Cancer
                elif sign in [2, 6, 10]: start = 6   # Air: Libra
                else: start = 9                      # Water: Capricorn
                return (start + part) % 12

            elif division == 30:  # Trimsamsa (D30)
                # Use degree_in_sign directly for unequal parts
                if sign % 2 == 0:  # Odd
                    if degree_in_sign < 5: return 0
                    elif degree_in_sign < 10: return 10
                    elif degree_in_sign < 18: return 8
                    elif degree_in_sign < 25: return 2
                    else: return 6
                else:  # Even
                    if degree_in_sign < 5: return 1
                    elif degree_in_sign < 12: return 5
                    elif degree_in_sign < 20: return 11
                    elif degree_in_sign < 25: return 9
                    else: return 7

            # --- CORRECTIONS ---

            elif division == 40:  # Khavedamsa (D40)
                # RULE: Odd Signs start from Aries(0), Even Signs start from Libra(6)
                if sign % 2 == 0: start = 0  # Odd Sign (Aries is 0)
                else: start = 6              # Even Sign
                return (start + part) % 12

            elif division == 45:  # Akshavedamsa (D45)
                if sign in [0, 3, 6, 9]: start = 0      # Movable: Aries
                elif sign in [1, 4, 7, 10]: start = 4   # Fixed: Leo
                else: start = 8                         # Dual: Sag
                return (start + part) % 12

            elif division == 60:  # Shashtyamsa (D60)
                # RULE: Start from the sign itself (Standard/BPHS Chart Calculation)
                # Note: D60 deities are ignored here, this is for chart placement only
                return (sign + part) % 12

            else:
                # Default for D5, D6, D8, D11 etc if ever passed
                return (sign + part) % 12
        
        # Calculate divisional chart
        divisional_data = {
            'planets': {},
            'houses': [],
            'ayanamsa': self.chart_data.get('ayanamsa', 0)
        }
        
        # Calculate divisional ascendant with proper scaling
        asc_sign = int(self.chart_data['ascendant'] / 30)
        asc_degree = self.chart_data['ascendant'] % 30
        divisional_asc_sign = get_divisional_sign(asc_sign, asc_degree, division_number)
        
        print(f"⚙️ [BACKEND] D1 Ascendant: sign={asc_sign}, degree={asc_degree:.2f}")
        print(f"✅ [BACKEND] D{division_number} Ascendant sign: {divisional_asc_sign}")
        
        # Scaled degree calculation with epsilon buffer
        EPS = 1e-9
        part_size = 30.0 / division_number
        scaled_asc_degree = ((asc_degree + EPS) % part_size) * division_number
        divisional_data['ascendant'] = (divisional_asc_sign * 30) + scaled_asc_degree
        
        # Calculate divisional houses with house numbers
        for i in range(12):
            house_sign = (divisional_asc_sign + i) % 12
            divisional_data['houses'].append({
                'longitude': house_sign * 30,
                'sign': house_sign,
                'house_number': i + 1
            })
        
        # Calculate divisional positions for planets
        planets_to_process = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for planet in planets_to_process:
            if planet in self.chart_data['planets']:
                planet_data = self.chart_data['planets'][planet]
                
                # Regular planetary divisional calculation
                planet_sign = int(planet_data['longitude'] / 30)
                planet_degree = planet_data['longitude'] % 30
                
                divisional_sign = get_divisional_sign(planet_sign, planet_degree, division_number)
                
                # Calculate the actual degree within the divisional sign with proper scaling
                EPS = 1e-9
                part_size = 30.0 / division_number
                part_index = int((planet_degree + EPS) / part_size)  # Buffer here
                degree_within_part = (planet_degree + EPS) % part_size  # Buffer here
                # Scale the degree within part to full sign (0-30 degrees)
                actual_degree = (degree_within_part / part_size) * 30.0
                
                divisional_longitude = divisional_sign * 30 + actual_degree
                
                # Calculate house position relative to divisional ascendant
                house_number = ((divisional_sign - divisional_asc_sign) % 12) + 1
                
                # Calculate dignity for divisional chart
                dignity_info = self._calculate_divisional_dignity(planet, divisional_sign, divisional_asc_sign)
                
                # Add sign name to prevent indexing confusion
                sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
                
                divisional_data['planets'][planet] = {
                    'longitude': divisional_longitude,
                    'sign': divisional_sign,
                    'sign_name': sign_names[divisional_sign],
                    'degree': actual_degree,
                    'retrograde': planet_data.get('retrograde', False),
                    'house': house_number,
                    **dignity_info
                }
        
        print(f"📊 [BACKEND] D{division_number} Result:")
        print(f"  - Ascendant: {divisional_data['ascendant']:.2f} (sign {divisional_asc_sign})")
        print(f"  - Houses: {[{'house': h['house_number'], 'sign': h['sign']} for h in divisional_data['houses'][:3]]}...")
        
        return {
            'divisional_chart': divisional_data,
            'division_number': division_number,
            'chart_name': f'D{division_number}'
        }
    
    def get_chart_name(self, division_number):
        """Get traditional name for divisional chart"""
        chart_names = {
            1: 'Rasi (D1)', 2: 'Hora (D2)', 3: 'Drekkana (D3)', 4: 'Chaturthamsa (D4)',
            7: 'Saptamsa (D7)', 9: 'Navamsa (D9)', 10: 'Dasamsa (D10)',
            12: 'Dwadasamsa (D12)', 16: 'Shodasamsa (D16)', 20: 'Vimsamsa (D20)',
            24: 'Chaturvimsamsa (D24)', 27: 'Saptavimsamsa (D27)', 30: 'Trimsamsa (D30)',
            40: 'Khavedamsa (D40)', 45: 'Akshavedamsa (D45)', 60: 'Shashtyamsa (D60)'
        }
        return chart_names.get(division_number, f'D{division_number}')
    
    def get_chart_significance(self, division_number):
        """Get significance of divisional chart"""
        significances = {
            1: 'Overall life, personality, general indications',
            2: 'Wealth, family, material resources',
            3: 'Siblings, happiness, courage, short journeys',
            4: 'Destiny, assets, residence, property',
            7: 'Children, progeny, creativity, grandchildren',
            9: 'Marriage, dharma, fortune, spiritual inclinations',
            10: 'Career, profession, status, reputation',
            12: 'Parents, ancestry, past life karma',
            16: 'Vehicles, luxuries, happiness, comforts',
            20: 'Spiritual practices, religious activities',
            24: 'Education, learning, knowledge acquisition',
            27: 'Strengths, weaknesses, inherent nature',
            30: 'Evils, misfortunes, diseases, troubles',
            40: 'Maternal relatives, mother\'s family',
            45: 'Paternal relatives, father\'s family',
            60: 'Past life, karmic influences, subtle effects'
        }
        return significances.get(division_number, 'Specific life area analysis')
    
    def _calculate_divisional_dignity(self, planet, sign, divisional_asc_sign=None):
        """Calculate planetary dignity in divisional charts"""
        # Planetary rulerships and dignities
        EXALTATION_SIGNS = {
            'Sun': 0,      # Aries
            'Moon': 1,     # Taurus
            'Mars': 9,     # Capricorn
            'Mercury': 5,  # Virgo
            'Jupiter': 3,  # Cancer
            'Venus': 11,   # Pisces
            'Saturn': 6    # Libra
        }
        
        DEBILITATION_SIGNS = {
            'Sun': 6,      # Libra
            'Moon': 7,     # Scorpio
            'Mars': 3,     # Cancer
            'Mercury': 11, # Pisces
            'Jupiter': 9,  # Capricorn
            'Venus': 5,    # Virgo
            'Saturn': 0    # Aries
        }
        
        OWN_SIGNS = {
            'Sun': [4],           # Leo
            'Moon': [3],          # Cancer
            'Mars': [0, 7],       # Aries, Scorpio
            'Mercury': [2, 5],    # Gemini, Virgo
            'Jupiter': [8, 11],   # Sagittarius, Pisces
            'Venus': [1, 6],      # Taurus, Libra
            'Saturn': [9, 10]     # Capricorn, Aquarius
        }
        
        MOOLATRIKONA_SIGNS = {
            'Sun': 4,      # Leo
            'Moon': 1,     # Taurus
            'Mars': 0,     # Aries
            'Mercury': 5,  # Virgo
            'Jupiter': 8,  # Sagittarius
            'Venus': 6,    # Libra
            'Saturn': 10   # Aquarius
        }
        
        # Rahu and Ketu don't have traditional dignities
        if planet in ['Rahu', 'Ketu']:
            return {
                'dignity': 'neutral',
                'functional_nature': 'neutral',
                'strength_multiplier': 1.0
            }
        
        # Check dignity
        if sign == EXALTATION_SIGNS.get(planet):
            dignity = 'exalted'
            strength_multiplier = 2.0
        elif sign == DEBILITATION_SIGNS.get(planet):
            dignity = 'debilitated'
            strength_multiplier = 0.25
        elif sign == MOOLATRIKONA_SIGNS.get(planet):
            dignity = 'moolatrikona'
            strength_multiplier = 1.5
        elif sign in OWN_SIGNS.get(planet, []):
            dignity = 'own_sign'
            strength_multiplier = 1.25
        else:
            dignity = 'neutral'
            strength_multiplier = 1.0
        
        # Determine functional nature based on divisional ascendant if provided
        if divisional_asc_sign is not None:
            functional_nature = self._get_functional_nature_for_ascendant(planet, divisional_asc_sign)
        else:
            # Fallback to dignity-based functional nature
            if dignity in ['exalted', 'moolatrikona', 'own_sign']:
                functional_nature = 'benefic'
            elif dignity == 'debilitated':
                functional_nature = 'malefic'
            else:
                functional_nature = 'neutral'
        
        return {
            'dignity': dignity,
            'functional_nature': functional_nature,
            'strength_multiplier': strength_multiplier
        }
    
    def _get_functional_nature_for_ascendant(self, planet, ascendant_sign):
        """Get functional benefic/malefic nature based on ascendant sign"""
        # Simplified functional benefic/malefic system for divisional charts
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