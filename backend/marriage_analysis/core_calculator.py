"""
Core Marriage Analysis Calculator
Handles Rasi chart analysis for marriage indicators
"""
import swisseph as swe
from typing import Dict, List, Tuple, Any

class MarriageCoreCalculator:
    def __init__(self, chart_data: Dict):
        self.chart_data = chart_data
        self.planets = chart_data.get('planets', {})
        self.houses = chart_data.get('houses', {})
        
    def analyze_seventh_house(self) -> Dict[str, Any]:
        """Analyze 7th house and its lord"""
        # Houses is a list, 7th house is at index 6
        seventh_house = self.houses[6] if len(self.houses) > 6 else {}
        seventh_lord = self._get_house_lord(7)
        
        # Planets in 7th house
        planets_in_7th = self._get_planets_in_house(7)
        
        # Aspects to 7th house
        aspects_to_7th = self._get_aspects_to_house(7)
        
        return {
            'house_sign': seventh_house.get('sign'),
            'house_lord': seventh_lord,
            'lord_placement': self._get_planet_house_placement(seventh_lord),
            'planets_in_house': planets_in_7th,
            'aspects': aspects_to_7th,
            'strength_score': self._calculate_house_strength(7)
        }
    
    def analyze_marriage_karakas(self) -> Dict[str, Any]:
        """Analyze Venus and Jupiter as marriage significators"""
        venus_data = self.planets.get('Venus', {})
        jupiter_data = self.planets.get('Jupiter', {})
        
        return {
            'venus': {
                'sign': venus_data.get('sign'),
                'house': venus_data.get('house'),
                'dignity': self._get_planet_dignity('Venus'),
                'strength': self._calculate_planet_strength('Venus'),
                'aspects': self._get_planet_aspects('Venus')
            },
            'jupiter': {
                'sign': jupiter_data.get('sign'),
                'house': jupiter_data.get('house'),
                'dignity': self._get_planet_dignity('Jupiter'),
                'strength': self._calculate_planet_strength('Jupiter'),
                'aspects': self._get_planet_aspects('Jupiter')
            }
        }
    
    def check_manglik_dosha(self) -> Dict[str, Any]:
        """Check for Mangal/Kuja Dosha (Mars in 7th, 8th houses only)"""
        mars_data = self.planets.get('Mars', {})
        mars_house = mars_data.get('house')
        
        is_manglik = mars_house in [7, 8]
        
        # Check cancellation conditions
        cancellation = self._check_manglik_cancellation() if is_manglik else None
        
        return {
            'is_manglik': is_manglik,
            'mars_house': mars_house,
            'mars_sign': mars_data.get('sign'),
            'cancellation': cancellation,
            'severity': self._get_manglik_severity(mars_house) if is_manglik else None
        }
    
    def _get_house_lord(self, house_num: int) -> str:
        """Get the lord of a house"""
        # Houses is a list, get house at index (house_num - 1)
        house_data = self.houses[house_num - 1] if len(self.houses) >= house_num else {}
        sign = house_data.get('sign')
        
        # Sign to lord mapping
        sign_lords = {
            'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury',
            'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury',
            'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter',
            'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
        }
        
        return sign_lords.get(sign, 'Unknown')
    
    def _get_planets_in_house(self, house_num: int) -> List[str]:
        """Get planets placed in a specific house"""
        planets_in_house = []
        for planet, data in self.planets.items():
            if data.get('house') == house_num:
                planets_in_house.append(planet)
        return planets_in_house
    
    def _get_planet_house_placement(self, planet: str) -> int:
        """Get house placement of a planet"""
        return self.planets.get(planet, {}).get('house', 0)
    
    def _get_aspects_to_house(self, house_num: int) -> List[str]:
        """Get planets aspecting a house (simplified)"""
        # Simplified aspect calculation
        aspects = []
        for planet, data in self.planets.items():
            planet_house = data.get('house', 0)
            if self._has_aspect(planet_house, house_num, planet):
                aspects.append(planet)
        return aspects
    
    def _has_aspect(self, from_house: int, to_house: int, planet: str) -> bool:
        """Check if planet has aspect to house (simplified)"""
        # Basic aspects: 7th house aspect for all planets
        if (from_house + 6) % 12 + 1 == to_house:
            return True
        
        # Mars special aspects: 4th and 8th
        if planet == 'Mars':
            if (from_house + 3) % 12 + 1 == to_house or (from_house + 7) % 12 + 1 == to_house:
                return True
        
        # Jupiter special aspects: 5th and 9th
        if planet == 'Jupiter':
            if (from_house + 4) % 12 + 1 == to_house or (from_house + 8) % 12 + 1 == to_house:
                return True
        
        # Saturn special aspects: 3rd and 10th
        if planet == 'Saturn':
            if (from_house + 2) % 12 + 1 == to_house or (from_house + 9) % 12 + 1 == to_house:
                return True
        
        return False
    
    def _calculate_house_strength(self, house_num: int) -> int:
        """Calculate house strength (0-10 scale)"""
        strength = 5  # Base strength
        
        try:
            # House lord placement
            lord = self._get_house_lord(house_num)
            lord_house = self._get_planet_house_placement(lord)
            
            # Kendra/Trikona placement bonus
            if lord_house in [1, 4, 7, 10]:  # Kendra
                strength += 2
            elif lord_house in [5, 9]:  # Trikona
                strength += 3
            
            # Benefic planets in house
            planets_in_house = self._get_planets_in_house(house_num)
            benefics = ['Venus', 'Jupiter', 'Mercury', 'Moon']
            for planet in planets_in_house:
                if planet in benefics:
                    strength += 1
                else:
                    strength -= 1
        except (IndexError, KeyError, TypeError):
            # If there's any error, return base strength
            pass
        
        return max(0, min(10, strength))
    
    def _calculate_planet_strength(self, planet: str) -> int:
        """Calculate planet strength (0-10 scale)"""
        planet_data = self.planets.get(planet, {})
        strength = 5  # Base strength
        
        # House placement
        house = planet_data.get('house', 0)
        if house in [1, 4, 7, 10]:  # Kendra
            strength += 1
        elif house in [5, 9]:  # Trikona
            strength += 2
        
        # Dignity bonus
        dignity = self._get_planet_dignity(planet)
        if dignity == 'Exalted':
            strength += 3
        elif dignity == 'Own':
            strength += 2
        elif dignity == 'Friend':
            strength += 1
        elif dignity == 'Debilitated':
            strength -= 3
        elif dignity == 'Enemy':
            strength -= 1
        
        return max(0, min(10, strength))
    
    def _get_planet_dignity(self, planet: str) -> str:
        """Get planet dignity in current sign"""
        planet_data = self.planets.get(planet, {})
        sign = planet_data.get('sign', '')
        
        # Simplified dignity calculation
        exaltation = {
            'Sun': 'Aries', 'Moon': 'Taurus', 'Mars': 'Capricorn',
            'Mercury': 'Virgo', 'Jupiter': 'Cancer', 'Venus': 'Pisces',
            'Saturn': 'Libra'
        }
        
        debilitation = {
            'Sun': 'Libra', 'Moon': 'Scorpio', 'Mars': 'Cancer',
            'Mercury': 'Pisces', 'Jupiter': 'Capricorn', 'Venus': 'Virgo',
            'Saturn': 'Aries'
        }
        
        own_signs = {
            'Sun': ['Leo'], 'Moon': ['Cancer'], 'Mars': ['Aries', 'Scorpio'],
            'Mercury': ['Gemini', 'Virgo'], 'Jupiter': ['Sagittarius', 'Pisces'],
            'Venus': ['Taurus', 'Libra'], 'Saturn': ['Capricorn', 'Aquarius']
        }
        
        if sign == exaltation.get(planet):
            return 'Exalted'
        elif sign == debilitation.get(planet):
            return 'Debilitated'
        elif sign in own_signs.get(planet, []):
            return 'Own'
        else:
            return 'Neutral'
    
    def _get_planet_aspects(self, planet: str) -> List[str]:
        """Get planets aspected by given planet"""
        planet_data = self.planets.get(planet, {})
        planet_house = planet_data.get('house', 0)
        
        aspected = []
        for other_planet, data in self.planets.items():
            if other_planet != planet:
                other_house = data.get('house', 0)
                if self._has_aspect(planet_house, other_house, planet):
                    aspected.append(other_planet)
        
        return aspected
    
    def _check_manglik_cancellation(self) -> Dict[str, Any]:
        """Check for Manglik dosha cancellation"""
        mars_data = self.planets.get('Mars', {})
        mars_house = mars_data.get('house')
        
        cancellation_factors = []
        
        # Check if Mars is aspected by benefics
        mars_aspects = self._get_planet_aspects('Mars')
        benefics = ['Venus', 'Jupiter']
        
        for benefic in benefics:
            if benefic in mars_aspects:
                cancellation_factors.append(f"Mars aspected by {benefic}")
        
        # Check if Mars is conjunct with benefics
        planets_in_mars_house = self._get_planets_in_house(mars_house)
        for planet in planets_in_mars_house:
            if planet in benefics:
                cancellation_factors.append(f"Mars conjunct with {planet}")
        
        return {
            'has_cancellation': len(cancellation_factors) > 0,
            'factors': cancellation_factors
        }
    
    def _get_manglik_severity(self, mars_house: int) -> str:
        """Get Manglik dosha severity"""
        if mars_house == 7:
            return 'High'  # Direct impact on marriage house
        elif mars_house == 8:
            return 'Medium'  # Longevity and obstacles
        return 'Low'