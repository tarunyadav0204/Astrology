from .base_calculator import BaseCalculator

class InduLagnaCalculator(BaseCalculator):
    """Calculate InduLagna using classical Parashari method of planetary rays (Kalas)"""
    
    def __init__(self, chart_data):
        super().__init__(chart_data)
        
        # Sign lords mapping (1=Aries, 2=Taurus, etc.)
        self.sign_lords = {
            1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 
            5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars", 
            9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
        }
        
        # Planetary rays (Kalas) as per BPHS
        self.planetary_rays = {
            "Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8,
            "Jupiter": 10, "Venus": 12, "Saturn": 1
        }
    
    def calculate_indu_lagna(self):
        """
        Calculate InduLagna using Parashara's Method of Rays
        Returns InduLagna sign number (1-12)
        """
        # Get ascendant and moon signs from chart data
        ascendant_sign = self._get_ascendant_sign()
        moon_sign = self._get_moon_sign()
        
        # Find 9th house from ascendant
        ninth_from_lagna_sign = (ascendant_sign + 8) % 12
        if ninth_from_lagna_sign == 0:
            ninth_from_lagna_sign = 12
        
        # Find 9th house from moon
        ninth_from_moon_sign = (moon_sign + 8) % 12
        if ninth_from_moon_sign == 0:
            ninth_from_moon_sign = 12
        
        # Get lords of 9th houses
        lord_of_ninth_lagna = self.sign_lords[ninth_from_lagna_sign]
        lord_of_ninth_moon = self.sign_lords[ninth_from_moon_sign]
        
        # Sum rays
        total_rays = self.planetary_rays[lord_of_ninth_lagna] + self.planetary_rays[lord_of_ninth_moon]
        
        # Get remainder (offset)
        offset = total_rays % 12
        if offset == 0:
            offset = 12
        
        # Calculate InduLagna sign
        indu_lagna_sign = (moon_sign + offset - 1) % 12
        if indu_lagna_sign == 0:
            indu_lagna_sign = 12
        
        return indu_lagna_sign
    
    def get_indu_lagna_data(self):
        """
        Get complete InduLagna data for integration with chart
        Returns data in format compatible with existing planet structure
        """
        indu_sign = self.calculate_indu_lagna()
        
        # Calculate approximate longitude (middle of sign)
        indu_longitude = (indu_sign - 1) * 30 + 15
        
        # Calculate house position in D1 chart
        ascendant_sign = self._get_ascendant_sign()
        indu_house = ((indu_sign - ascendant_sign) % 12) + 1
        
        return {
            'longitude': indu_longitude,
            'sign': indu_sign - 1,  # Convert to 0-based for consistency
            'degree': 15.0,  # Middle of sign
            'house': indu_house,
            'type': 'special_point',
            'name': 'InduLagna'
        }
    
    def _get_ascendant_sign(self):
        """Get ascendant sign from chart data (1-based)"""
        if 'ascendant' in self.chart_data:
            ascendant_longitude = self.chart_data['ascendant']
            return int(ascendant_longitude / 30) + 1
        return 1  # Default fallback
    
    def get_indu_lagna_analysis(self):
        """Get complete InduLagna analysis for chat context"""
        indu_sign = self.calculate_indu_lagna()
        ascendant_sign = self._get_ascendant_sign()
        
        # Sign names mapping
        sign_names = {
            1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
            5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
            9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
        }
        
        # Calculate house position
        house_number = ((indu_sign - ascendant_sign) % 12) + 1
        
        # Get occupying and aspecting planets
        occupying_planets = self._get_planets_in_sign(indu_sign)
        aspecting_planets = self._get_aspecting_planets(indu_sign)
        
        return {
            "special_lagnas": {
                "indu_lagna": {
                    "sign_name": sign_names[indu_sign],
                    "house_number": house_number,
                    "ruler": self.sign_lords[indu_sign],
                    "occupying_planets": occupying_planets,
                    "aspecting_planets": aspecting_planets
                }
            }
        }
    
    def _get_planets_in_sign(self, sign_number):
        """Get planets occupying the given sign (1-based)"""
        occupying = []
        if 'planets' in self.chart_data:
            for planet, data in self.chart_data['planets'].items():
                planet_sign = data['sign'] + 1  # Convert to 1-based
                if planet_sign == sign_number:
                    occupying.append(planet)
        return occupying
    
    def _get_aspecting_planets(self, sign_number):
        """Get planets aspecting the given sign (only physical planets can cast aspects)"""
        aspecting = []
        # Only physical planets can cast aspects in Parashari astrology
        physical_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        if 'planets' in self.chart_data:
            for planet, data in self.chart_data['planets'].items():
                if planet not in physical_planets:
                    continue  # Skip Upagrahas like Gulika
                    
                planet_sign = data['sign'] + 1  # Convert to 1-based
                
                # Check for aspects (7th, 4th/8th for Mars, 5th/9th for Jupiter, etc.)
                if self._has_aspect(planet, planet_sign, sign_number):
                    aspecting.append(planet)
        return aspecting
    
    def _has_aspect(self, planet, from_sign, to_sign):
        """Check if planet aspects the target sign"""
        # Calculate sign difference
        diff = (to_sign - from_sign) % 12
        if diff == 0:
            return False  # Same sign, not an aspect
        
        # All planets aspect 7th house
        if diff == 7:
            return True
        
        # Mars aspects 4th and 8th
        if planet == "Mars" and diff in [4, 8]:
            return True
        
        # Jupiter aspects 5th and 9th
        if planet == "Jupiter" and diff in [5, 9]:
            return True
        
        # Saturn aspects 3rd and 10th
        if planet == "Saturn" and diff in [3, 10]:
            return True
        
        return False
    
    def _get_ascendant_sign(self):
        """Get ascendant sign from chart data (1-based)"""
        if 'ascendant' in self.chart_data:
            ascendant_longitude = self.chart_data['ascendant']
            return int(ascendant_longitude / 30) + 1
        return 1  # Default fallback
    
    def _get_moon_sign(self):
        """Get moon sign from chart data (1-based)"""
        if 'planets' in self.chart_data and 'Moon' in self.chart_data['planets']:
            moon_sign = self.chart_data['planets']['Moon']['sign']
            return moon_sign + 1  # Convert from 0-based to 1-based
        return 1  # Default fallback