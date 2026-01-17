"""
Dasha-House Gate Validator
Core innovation: Only allows events that have dasha authorization for specific life areas
Eliminates "ghost predictions" where transit looks good but dasha is silent
"""

from typing import Dict, List, Tuple
from calculators.aspect_calculator import AspectCalculator


class DashaHouseGate:
    """
    Validates if current dasha stack authorizes a specific house/life area to activate.
    
    Authorization Hierarchy (Only 3 levels for birth time accuracy):
    - Mahadasha (MD): 100 points
    - Antardasha (AD): 70 points
    - Pratyantardasha (PD): 40 points
    
    Note: Sookshma and Prana excluded due to birth time sensitivity
    Gate Opens: Score >= 40 (minimum PD level)
    """
    
    # Natural Karakas for houses
    HOUSE_KARAKAS = {
        1: ['Sun', 'Mars'],           # Self, vitality
        2: ['Jupiter', 'Mercury'],    # Wealth, speech
        3: ['Mars', 'Mercury'],       # Courage, communication
        4: ['Moon', 'Venus', 'Mercury'],  # Mother, home, education
        5: ['Jupiter'],               # Children, intelligence
        6: ['Mars', 'Saturn'],        # Enemies, disease
        7: ['Venus'],                 # Marriage, partnership
        8: ['Saturn'],                # Longevity, occult
        9: ['Jupiter', 'Sun'],        # Father, fortune, dharma
        10: ['Sun', 'Mercury', 'Jupiter', 'Saturn'],  # Career, status
        11: ['Jupiter'],              # Gains, fulfillment
        12: ['Saturn', 'Ketu']        # Loss, moksha
    }
    
    def __init__(self, chart_data: Dict):
        """
        Initialize with natal chart data
        
        Args:
            chart_data: D1 chart with planets, houses, ascendant
        """
        self.chart_data = chart_data
        self.aspects_calc = AspectCalculator(chart_data)
        
        # Sign lords
        self.SIGN_LORDS = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        # Pre-calculate house lords
        self.house_lords = {}
        for house in range(1, 13):
            self.house_lords[house] = self._get_house_lord(house)
        
        # Pre-calculate planets in houses
        self.planets_in_houses = self._map_planets_to_houses()
        
        # Pre-calculate aspects to houses
        self.aspects_to_houses = self._calculate_house_aspects()
    
    def check_authorization(self, house: int, dasha_stack: Dict, 
                           shadbala_data: Dict = None, 
                           ashtakavarga_data: Dict = None) -> Dict:
        """
        Check if dasha authorizes house activation WITH strength validation.
        
        Args:
            house: House number (1-12)
            dasha_stack: Dict with mahadasha, antardasha, pratyantardasha
            shadbala_data: Planetary strength data (optional)
            ashtakavarga_data: Ashtakavarga scores (optional)
        
        Returns:
            {
                'authorized': bool,
                'score': int,
                'reasons': List[str],
                'dasha_connections': List[Dict],
                'strength_validated': bool,
                'capacity': str  # 'strong', 'moderate', 'weak'
            }
        """
        score = 0
        reasons = []
        connections = []
        
        # Dasha weights (only 3 levels for reliability)
        dasha_levels = [
            ('mahadasha', 100),
            ('antardasha', 70),
            ('pratyantardasha', 40)
            # Sookshma and Prana excluded - too sensitive to birth time errors
        ]
        
        for level_name, weight in dasha_levels:
            if level_name not in dasha_stack:
                continue
            
            dasha_planet = dasha_stack[level_name].get('planet')
            if not dasha_planet:
                continue
            
            # Check all authorization paths
            auth_score, auth_reasons = self._check_planet_authorizes_house(
                dasha_planet, house, level_name, weight
            )
            
            if auth_score > 0:
                score += auth_score
                reasons.extend(auth_reasons)
                connections.append({
                    'level': level_name,
                    'planet': dasha_planet,
                    'score': auth_score,
                    'reasons': auth_reasons
                })
        
        # Gate opens if score >= 40 (at least PD level)
        authorized = score >= 40
        
        # Strength validation (Portfolio + Capacity check)
        strength_validated = True
        capacity = 'strong'
        
        if authorized and (shadbala_data or ashtakavarga_data):
            # Check if dasha planets have CAPACITY to deliver
            weak_planets = []
            
            for conn in connections:
                planet = conn['planet']
                
                # Shadbala check (< 4 rupas = weak)
                if shadbala_data:
                    planet_strength = shadbala_data.get(planet, {}).get('total_strength', 5)
                    if planet_strength < 4:
                        weak_planets.append(f"{planet} (Shadbala: {planet_strength:.1f})")
                
                # Ashtakavarga check for house (< 25 bindus = weak)
                if ashtakavarga_data:
                    house_score = ashtakavarga_data.get(house, 28)
                    if house_score < 25:
                        weak_planets.append(f"H{house} (AV: {house_score})")
            
            if weak_planets:
                capacity = 'weak' if len(weak_planets) > 1 else 'moderate'
                strength_validated = False
                reasons.append(f"⚠️ Weak capacity: {', '.join(weak_planets)}")
        
        return {
            'authorized': authorized,
            'score': score,
            'reasons': reasons,
            'dasha_connections': connections,
            'house': house,
            'strength_validated': strength_validated,
            'capacity': capacity
        }
    
    def _check_planet_authorizes_house(self, planet: str, house: int, 
                                       level_name: str, weight: int) -> Tuple[int, List[str]]:
        """
        Check if planet authorizes house through multiple paths.
        
        Authorization Paths:
        1. Planet is house lord
        2. Planet sits in house
        3. Planet aspects house
        4. Planet is natural karaka
        5. Planet is dispositor of house lord
        """
        score = 0
        reasons = []
        
        # Path 1: House Lord
        if self.house_lords.get(house) == planet:
            score = weight
            reasons.append(f"{planet} is lord of H{house} ({level_name.upper()})")
        
        # Path 2: Planet in House
        if planet in self.planets_in_houses.get(house, []):
            score = weight
            reasons.append(f"{planet} sits in H{house} ({level_name.upper()})")
        
        # Path 3: Planet Aspects House
        if planet in self.aspects_to_houses.get(house, []):
            score = weight
            reasons.append(f"{planet} aspects H{house} ({level_name.upper()})")
        
        # Path 4: Natural Karaka (REDUCED WEIGHT - not full)
        if planet in self.HOUSE_KARAKAS.get(house, []):
            # Karaka authorization is supportive but not primary
            if score == 0:  # Only if no other authorization
                karaka_score = weight // 2  # Half weight for karaka alone
                score = karaka_score
                reasons.append(f"{planet} is natural karaka for H{house} ({level_name.upper()}) [Karaka only]")
        
        # Path 5: Dispositor Chain (only for MD/AD)
        if level_name in ['mahadasha', 'antardasha']:
            house_lord = self.house_lords.get(house)
            if house_lord and self._is_dispositor(planet, house_lord):
                dispositor_score = weight // 3
                score = max(score, dispositor_score)
                reasons.append(f"{planet} is dispositor of H{house} lord {house_lord} ({level_name.upper()})")
        
        return score, reasons
    
    def _get_house_lord(self, house: int) -> str:
        """Get lord of house"""
        asc_sign = int(self.chart_data['ascendant'] / 30)
        house_sign = (asc_sign + house - 1) % 12
        return self.SIGN_LORDS.get(house_sign, 'Sun')
    
    def _get_sign_lord(self, sign: int) -> str:
        """Get lord of sign"""
        return self.SIGN_LORDS.get(sign, 'Sun')
    
    def _map_planets_to_houses(self) -> Dict[int, List[str]]:
        """Map which planets are in which houses"""
        planets_in_houses = {}
        asc_sign = int(self.chart_data['ascendant'] / 30)
        
        for planet, data in self.chart_data['planets'].items():
            planet_sign = data['sign']
            house = ((planet_sign - asc_sign) % 12) + 1
            
            if house not in planets_in_houses:
                planets_in_houses[house] = []
            planets_in_houses[house].append(planet)
        
        return planets_in_houses
    
    def _calculate_house_aspects(self) -> Dict[int, List[str]]:
        """Calculate which planets aspect which houses"""
        aspects_to_houses = {}
        asc_sign = int(self.chart_data['ascendant'] / 30)
        
        # Vedic aspects
        vedic_aspects = {
            'Sun': [7], 'Moon': [7], 'Mars': [4, 7, 8], 'Mercury': [7],
            'Jupiter': [5, 7, 9], 'Venus': [7], 'Saturn': [3, 7, 10],
            'Rahu': [5, 7, 9], 'Ketu': [5, 7, 9]
        }
        
        for planet, data in self.chart_data['planets'].items():
            if planet not in vedic_aspects:
                continue
            
            planet_sign = data['sign']
            planet_house = ((planet_sign - asc_sign) % 12) + 1
            
            for aspect_num in vedic_aspects[planet]:
                if aspect_num == 1:
                    continue  # Skip conjunction
                
                # Calculate target house
                target_house = ((planet_house + aspect_num - 2) % 12) + 1
                
                if target_house not in aspects_to_houses:
                    aspects_to_houses[target_house] = []
                aspects_to_houses[target_house].append(planet)
        
        return aspects_to_houses
    
    def _is_dispositor(self, planet: str, target_planet: str) -> bool:
        """Check if planet is dispositor of target_planet"""
        if target_planet not in self.chart_data['planets']:
            return False
        
        target_sign = self.chart_data['planets'][target_planet]['sign']
        sign_lord = self._get_sign_lord(target_sign)
        
        return sign_lord == planet
    
    def get_authorized_houses(self, dasha_stack: Dict, min_score: int = 40,
                             shadbala_data: Dict = None, 
                             ashtakavarga_data: Dict = None) -> List[Dict]:
        """
        Get all houses authorized by current dasha stack WITH strength validation.
        
        Args:
            dasha_stack: Current dasha configuration
            min_score: Minimum score for authorization (default 40)
            shadbala_data: Planetary strength data
            ashtakavarga_data: House-based Ashtakavarga scores
        
        Returns:
            List of authorized houses with scores, reasons, and capacity
        """
        authorized_houses = []
        
        for house in range(1, 13):
            result = self.check_authorization(
                house, dasha_stack, shadbala_data, ashtakavarga_data
            )
            if result['score'] >= min_score:
                authorized_houses.append(result)
        
        # Sort by score descending
        authorized_houses.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit to top 6 houses to avoid over-prediction
        return authorized_houses[:6]
