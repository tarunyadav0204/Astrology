import swisseph as swe
from typing import Dict, List, Any

class JaiminiRashiStrength:
    """Classical Jaimini rashi strength calculator for determining weak rashis in Kalchakra"""
    
    RASHI_LORDS = {
        0: 4,   # Aries -> Mars
        1: 6,   # Taurus -> Venus  
        2: 3,   # Gemini -> Mercury
        3: 2,   # Cancer -> Moon
        4: 1,   # Leo -> Sun
        5: 3,   # Virgo -> Mercury
        6: 6,   # Libra -> Venus
        7: 4,   # Scorpio -> Mars
        8: 5,   # Sagittarius -> Jupiter
        9: 7,   # Capricorn -> Saturn
        10: 7,  # Aquarius -> Saturn
        11: 5   # Pisces -> Jupiter
    }
    
    def __init__(self, chart_data: Dict[str, Any]):
        self.chart_data = chart_data
        self.planets = chart_data.get('planets', {})
        
        # Initialize existing calculators for enhanced accuracy
        from .friendship_calculator import FriendshipCalculator
        from .chara_karaka_calculator import CharaKarakaCalculator
        from .argala_calculator import ArgalaCalculator
        
        self.friendship_calc = FriendshipCalculator()
        self.karaka_calc = CharaKarakaCalculator(chart_data)
        self.argala_calc = ArgalaCalculator(chart_data)
        
        # Get pre-calculated data
        self.karakas = self.karaka_calc.calculate_chara_karakas()['chara_karakas']
        self.argala_data = self.argala_calc.calculate_argala_analysis()
        
    def calculate_rashi_strength(self, rashi_index: int) -> float:
        """Calculate overall strength of a rashi (0-100 scale)"""
        
        # 1. Planetary strength in rashi
        planetary_strength = self._calculate_planetary_strength(rashi_index)
        
        # 2. Aspects to the rashi
        aspect_strength = self._calculate_aspect_strength(rashi_index)
        
        # 3. Rashi lord strength
        lord_strength = self._calculate_rashi_lord_strength(rashi_index)
        
        # 4. Special combinations
        special_strength = self._calculate_special_combinations(rashi_index)
        
        # Weighted combination
        total_strength = (
            planetary_strength * 0.4 +
            aspect_strength * 0.25 +
            lord_strength * 0.25 +
            special_strength * 0.1
        )
        
        return min(100, max(0, total_strength))
    
    def is_weak_rashi(self, rashi_index: int, threshold: float = 25.0) -> bool:
        """Determine if rashi is weak enough to skip in Kalchakra cycles"""
        strength = self.calculate_rashi_strength(rashi_index)
        return strength < threshold
    
    def get_skip_reasons(self, rashi_index: int, threshold: float = 25.0) -> Dict[str, Any]:
        """Get detailed reasons why a rashi is skipped"""
        planetary_strength = self._calculate_planetary_strength(rashi_index)
        aspect_strength = self._calculate_aspect_strength(rashi_index)
        lord_strength = self._calculate_rashi_lord_strength(rashi_index)
        special_strength = self._calculate_special_combinations(rashi_index)
        
        total_strength = (
            planetary_strength * 0.4 +
            aspect_strength * 0.25 +
            lord_strength * 0.25 +
            special_strength * 0.1
        )
        
        return {
            "total_strength": round(total_strength, 1),
            "threshold": threshold,
            "is_skipped": total_strength < threshold,
            "components": {
                "planetary": {
                    "score": round(planetary_strength, 1),
                    "weight": "40%",
                    "details": self._get_planetary_details(rashi_index)
                },
                "aspects": {
                    "score": round(aspect_strength, 1),
                    "weight": "25%",
                    "details": self._get_aspect_details(rashi_index)
                },
                "lord": {
                    "score": round(lord_strength, 1),
                    "weight": "25%",
                    "details": self._get_lord_details(rashi_index)
                },
                "special": {
                    "score": round(special_strength, 1),
                    "weight": "10%",
                    "details": self._get_special_details(rashi_index)
                }
            }
        }
    
    def _calculate_planetary_strength(self, rashi_index: int) -> float:
        """Calculate strength based on planets in rashi"""
        strength = 0.0
        
        for planet_name, planet_data in self.planets.items():
            if planet_data['sign'] == rashi_index:
                # Base strength for planet presence
                planet_strength = 20.0
                
                # Exaltation/debilitation adjustments
                if self._is_exalted(planet_name, rashi_index):
                    planet_strength += 30.0
                elif self._is_debilitated(planet_name, rashi_index):
                    planet_strength -= 15.0
                elif self._is_own_sign(planet_name, rashi_index):
                    planet_strength += 20.0
                elif self._is_friendly_sign(planet_name, rashi_index):
                    planet_strength += 10.0
                elif self._is_enemy_sign(planet_name, rashi_index):
                    planet_strength -= 10.0
                
                strength += planet_strength
        
        return min(60, strength)  # Cap at 60 for planetary component
    
    def _calculate_aspect_strength(self, rashi_index: int) -> float:
        """Calculate strength from Jaimini aspects to the rashi"""
        strength = 0.0
        
        for planet_name, planet_data in self.planets.items():
            planet_sign = planet_data['sign']
            
            # Jaimini aspects: Fixed signs aspect other fixed, cardinal aspect other cardinal, etc.
            if self._has_jaimini_aspect(planet_sign, rashi_index):
                aspect_strength = 15.0
                
                # Benefic vs malefic aspects
                if self._is_benefic(planet_name):
                    aspect_strength += 5.0
                else:
                    aspect_strength -= 2.0
                
                strength += aspect_strength
        
        return min(40, strength)  # Cap at 40 for aspect component
    
    def _calculate_rashi_lord_strength(self, rashi_index: int) -> float:
        """Calculate strength based on rashi lord's position and condition"""
        lord_planet_num = self.RASHI_LORDS[rashi_index]
        lord_name = self._get_planet_name_by_number(lord_planet_num)
        
        if not lord_name or lord_name not in self.planets:
            return 10.0  # Default minimal strength
        
        lord_data = self.planets[lord_name]
        lord_sign = lord_data['sign']
        
        strength = 25.0  # Base strength
        
        # Lord's dignity
        if self._is_exalted(lord_name, lord_sign):
            strength += 20.0
        elif self._is_debilitated(lord_name, lord_sign):
            strength -= 15.0
        elif self._is_own_sign(lord_name, lord_sign):
            strength += 15.0
        
        # Lord in kendra/trikona from own rashi
        house_diff = (lord_sign - rashi_index) % 12
        if house_diff in [0, 3, 6, 9]:  # Kendra
            strength += 10.0
        elif house_diff in [4, 7]:  # Trikona
            strength += 8.0
        
        return min(50, strength)  # Cap at 50 for lord component
    
    def _calculate_special_combinations(self, rashi_index: int) -> float:
        """Calculate strength from special Jaimini combinations using real calculators"""
        strength = 0.0
        
        # Use real Argala calculator for accurate strength
        rashi_house = rashi_index + 1  # Convert to 1-12
        if rashi_house in self.argala_data:
            house_argala = self.argala_data[rashi_house]
            net_argala = house_argala.get('net_argala_strength', 0)
            # Scale argala strength to our 0-20 range
            strength += net_argala * 0.2
        
        # Enhanced Karaka connections (all 7 karakas)
        karaka_connections = 0
        for karaka_name, karaka_data in self.karakas.items():
            karaka_sign = karaka_data.get('sign', -1)
            if karaka_sign == rashi_index:
                # Different weights for different karakas
                if karaka_name == 'Atmakaraka':
                    karaka_connections += 10.0
                elif karaka_name in ['Amatyakaraka', 'Darakaraka']:
                    karaka_connections += 6.0
                else:
                    karaka_connections += 4.0
            elif self._has_jaimini_aspect(karaka_sign, rashi_index):
                # Aspect connection (weaker)
                if karaka_name == 'Atmakaraka':
                    karaka_connections += 5.0
                else:
                    karaka_connections += 2.0
        
        strength += min(15.0, karaka_connections)  # Cap karaka influence
        
        return strength
    
    def _has_jaimini_aspect(self, from_sign: int, to_sign: int) -> bool:
        """Check if there's a Jaimini aspect between signs"""
        # Fixed signs (1,4,7,10) aspect each other
        fixed_signs = [0, 3, 6, 9]  # Aries, Cancer, Libra, Capricorn
        if from_sign in fixed_signs and to_sign in fixed_signs and from_sign != to_sign:
            return True
        
        # Cardinal signs (2,5,8,11) aspect each other  
        cardinal_signs = [1, 4, 7, 10]  # Taurus, Leo, Scorpio, Aquarius
        if from_sign in cardinal_signs and to_sign in cardinal_signs and from_sign != to_sign:
            return True
        
        # Mutable signs (3,6,9,12) aspect each other
        mutable_signs = [2, 5, 8, 11]  # Gemini, Virgo, Sagittarius, Pisces
        if from_sign in mutable_signs and to_sign in mutable_signs and from_sign != to_sign:
            return True
        
        return False
    
    def _is_exalted(self, planet_name: str, sign: int) -> bool:
        """Check if planet is exalted in sign"""
        exaltations = {
            'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
            'Jupiter': 3, 'Venus': 11, 'Saturn': 6
        }
        return exaltations.get(planet_name) == sign
    
    def _is_debilitated(self, planet_name: str, sign: int) -> bool:
        """Check if planet is debilitated in sign"""
        debilitations = {
            'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11,
            'Jupiter': 9, 'Venus': 5, 'Saturn': 0
        }
        return debilitations.get(planet_name) == sign
    
    def _is_own_sign(self, planet_name: str, sign: int) -> bool:
        """Check if planet is in own sign"""
        own_signs = {
            'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
            'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
        }
        return sign in own_signs.get(planet_name, [])
    
    def _is_friendly_sign(self, planet_name: str, sign: int) -> bool:
        """Check if planet is in friendly sign using real friendship calculator"""
        # Use existing friendship calculator for accurate results
        try:
            friendship_data = self.friendship_calc.calculate_friendship(type('obj', (object,), {
                'date': '2000-01-01', 'time': '12:00', 'latitude': 0, 'longitude': 0, 'timezone': 'UTC+0:00'
            })())
            
            # Get sign lord and check friendship
            sign_lord = self._get_planet_name_by_number(self.RASHI_LORDS[sign])
            if sign_lord and planet_name in friendship_data['friendship_matrix']:
                relationship = friendship_data['friendship_matrix'][planet_name].get(sign_lord, 'neutral')
                return relationship in ['friend', 'great_friend']
        except:
            pass
        
        # Fallback to basic friendship
        friendly_signs = {
            'Sun': [0, 8], 'Moon': [1, 3], 'Mars': [4, 8], 'Mercury': [1, 5],
            'Jupiter': [0, 4], 'Venus': [2, 11], 'Saturn': [2, 6]
        }
        return sign in friendly_signs.get(planet_name, [])
    
    def _is_enemy_sign(self, planet_name: str, sign: int) -> bool:
        """Check if planet is in enemy sign"""
        enemy_signs = {
            'Sun': [6, 10], 'Moon': [7, 9], 'Mars': [2, 5], 'Mercury': [8, 11],
            'Jupiter': [6, 7], 'Venus': [0, 4], 'Saturn': [0, 4]
        }
        return sign in enemy_signs.get(planet_name, [])
    
    def _is_benefic(self, planet_name: str) -> bool:
        """Check if planet is natural benefic"""
        return planet_name in ['Jupiter', 'Venus', 'Mercury', 'Moon']
    
    def _get_planetary_details(self, rashi_index: int) -> List[str]:
        """Get detailed planetary strength breakdown"""
        details = []
        planets_in_sign = []
        
        for planet_name, planet_data in self.planets.items():
            if planet_data['sign'] == rashi_index:
                planets_in_sign.append(planet_name)
                status = []
                if self._is_exalted(planet_name, rashi_index):
                    status.append("exalted")
                elif self._is_debilitated(planet_name, rashi_index):
                    status.append("debilitated")
                elif self._is_own_sign(planet_name, rashi_index):
                    status.append("own sign")
                elif self._is_friendly_sign(planet_name, rashi_index):
                    status.append("friendly")
                elif self._is_enemy_sign(planet_name, rashi_index):
                    status.append("enemy")
                
                status_str = f" ({', '.join(status)})" if status else ""
                details.append(f"{planet_name}{status_str}")
        
        if not planets_in_sign:
            details.append("No planets in this rashi")
        
        return details
    
    def _get_aspect_details(self, rashi_index: int) -> List[str]:
        """Get detailed aspect strength breakdown"""
        details = []
        aspecting_planets = []
        
        for planet_name, planet_data in self.planets.items():
            planet_sign = planet_data['sign']
            if self._has_jaimini_aspect(planet_sign, rashi_index):
                benefic_str = " (benefic)" if self._is_benefic(planet_name) else " (malefic)"
                aspecting_planets.append(f"{planet_name}{benefic_str}")
        
        if aspecting_planets:
            details.extend(aspecting_planets)
        else:
            details.append("No Jaimini aspects to this rashi")
        
        return details
    
    def _get_lord_details(self, rashi_index: int) -> List[str]:
        """Get detailed rashi lord strength breakdown"""
        details = []
        lord_planet_num = self.RASHI_LORDS[rashi_index]
        lord_name = self._get_planet_name_by_number(lord_planet_num)
        
        if lord_name and lord_name in self.planets:
            lord_data = self.planets[lord_name]
            lord_sign = lord_data['sign']
            
            # Lord's dignity
            if self._is_exalted(lord_name, lord_sign):
                details.append(f"{lord_name} is exalted")
            elif self._is_debilitated(lord_name, lord_sign):
                details.append(f"{lord_name} is debilitated")
            elif self._is_own_sign(lord_name, lord_sign):
                details.append(f"{lord_name} is in own sign")
            else:
                details.append(f"{lord_name} is in neutral position")
            
            # Position from own rashi
            house_diff = (lord_sign - rashi_index) % 12
            if house_diff in [0, 3, 6, 9]:
                details.append(f"Lord in kendra from own rashi")
            elif house_diff in [4, 7]:
                details.append(f"Lord in trikona from own rashi")
            else:
                details.append(f"Lord in {house_diff + 1}H from own rashi")
        else:
            details.append(f"Lord {lord_name or 'unknown'} not found")
        
        return details
    
    def _get_special_details(self, rashi_index: int) -> List[str]:
        """Get detailed special combinations breakdown using real calculators"""
        details = []
        
        # Real Argala analysis
        rashi_house = rashi_index + 1
        if rashi_house in self.argala_data:
            house_argala = self.argala_data[rashi_house]
            net_strength = house_argala.get('net_argala_strength', 0)
            grade = house_argala.get('argala_grade', 'Neutral')
            
            argala_planets = house_argala.get('argala_planets', [])
            virodha_planets = house_argala.get('virodha_argala_planets', [])
            
            if argala_planets:
                planet_names = [p['planet'] for p in argala_planets]
                details.append(f"Argala from {', '.join(planet_names)} ({grade})")
            
            if virodha_planets:
                planet_names = [p['planet'] for p in virodha_planets]
                details.append(f"Virodha from {', '.join(planet_names)}")
        
        # Karaka connections
        connected_karakas = []
        for karaka_name, karaka_data in self.karakas.items():
            karaka_sign = karaka_data.get('sign', -1)
            if karaka_sign == rashi_index:
                connected_karakas.append(f"{karaka_name} placed")
            elif self._has_jaimini_aspect(karaka_sign, rashi_index):
                connected_karakas.append(f"{karaka_name} aspects")
        
        if connected_karakas:
            details.extend(connected_karakas)
        
        if not details:
            details.append("No special combinations")
        
        return details
    
    def _get_planet_name_by_number(self, planet_num: int) -> str:
        """Convert planet number to name"""
        planet_map = {1: 'Sun', 2: 'Moon', 3: 'Mercury', 4: 'Mars', 
                     5: 'Jupiter', 6: 'Venus', 7: 'Saturn'}
        return planet_map.get(planet_num, '')
    
    def _has_planets_in_sign(self, sign: int) -> bool:
        """Check if any planets are in the given sign"""
        for planet_data in self.planets.values():
            if planet_data['sign'] == sign:
                return True
        return False
    
    def _is_atmakaraka_connected(self, rashi_index: int) -> bool:
        """Check if rashi has connection to Atmakaraka using real calculator"""
        atmakaraka_data = self.karakas.get('Atmakaraka')
        if atmakaraka_data:
            ak_sign = atmakaraka_data.get('sign', -1)
            # Connection if AK is in this rashi or aspects it
            return ak_sign == rashi_index or self._has_jaimini_aspect(ak_sign, rashi_index)
        return False