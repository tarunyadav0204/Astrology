"""Navatara (Tara Bala) Calculator - 9-fold Nakshatra compatibility system"""

class NavataraCalculator:
    """Calculate Navatara (Tara Bala) for transit analysis"""
    
    TARA_NAMES = [
        "Janma",      # 1st - Birth star (Neutral)
        "Sampat",     # 2nd - Wealth (Good)
        "Vipat",      # 3rd - Danger (Bad)
        "Kshema",     # 4th - Well-being (Good)
        "Pratyak",    # 5th - Obstacle (Bad)
        "Sadhana",    # 6th - Achievement (Good)
        "Naidhana",   # 7th - Death/Endings (Bad)
        "Mitra",      # 8th - Friend (Good)
        "Parama Mitra" # 9th - Best Friend (Excellent)
    ]
    
    TARA_EFFECTS = {
        0: {"name": "Janma", "effect": "neutral", "description": "Birth star - Mixed results"},
        1: {"name": "Sampat", "effect": "good", "description": "Wealth and prosperity"},
        2: {"name": "Vipat", "effect": "bad", "description": "Danger and obstacles"},
        3: {"name": "Kshema", "effect": "good", "description": "Well-being and safety"},
        4: {"name": "Pratyak", "effect": "bad", "description": "Obstacles and delays"},
        5: {"name": "Sadhana", "effect": "good", "description": "Achievement and success"},
        6: {"name": "Naidhana", "effect": "bad", "description": "Endings and losses"},
        7: {"name": "Mitra", "effect": "good", "description": "Friendship and support"},
        8: {"name": "Parama Mitra", "effect": "excellent", "description": "Best outcomes"}
    }
    
    def __init__(self, birth_moon_nakshatra):
        """
        Initialize with birth Moon nakshatra (0-26)
        """
        self.birth_nakshatra = birth_moon_nakshatra
    
    def calculate_tara(self, transit_nakshatra):
        """
        Calculate which Tara the transit nakshatra falls in
        Returns: dict with tara info
        """
        # Calculate distance from birth nakshatra
        distance = (transit_nakshatra - self.birth_nakshatra) % 27
        
        # Map to 9 Taras (each Tara covers 3 nakshatras)
        tara_index = distance % 9
        
        tara_info = self.TARA_EFFECTS[tara_index].copy()
        tara_info['number'] = tara_index + 1  # Add 'number' field for consistency
        tara_info['distance'] = distance
        
        return tara_info
    
    def is_malefic_tara(self, transit_nakshatra):
        """
        Check if transit is in malefic Tara (Vipat, Pratyak, Naidhana)
        """
        tara = self.calculate_tara(transit_nakshatra)
        return tara['effect'] == 'bad'
    
    def get_transit_tara_analysis(self, transit_planets_nakshatras):
        """
        Analyze all transit planets for Tara Bala
        
        Args:
            transit_planets_nakshatras: dict like {'Jupiter': 15, 'Saturn': 22, ...}
        
        Returns:
            dict with tara analysis for each planet
        """
        analysis = {}
        
        for planet, nakshatra in transit_planets_nakshatras.items():
            tara_info = self.calculate_tara(nakshatra)
            
            analysis[planet] = {
                'nakshatra': nakshatra,
                'tara': tara_info['name'],
                'tara_number': tara_info['tara_number'],
                'effect': tara_info['effect'],
                'description': tara_info['description'],
                'is_malefic': tara_info['effect'] == 'bad',
                'warning': self._get_warning(planet, tara_info)
            }
        
        return analysis
    
    def _get_warning(self, planet, tara_info):
        """Generate warning message for malefic Taras"""
        if tara_info['effect'] == 'bad':
            return f"{planet} in {tara_info['name']} Tara - {tara_info['description']}. Exercise caution."
        return None
