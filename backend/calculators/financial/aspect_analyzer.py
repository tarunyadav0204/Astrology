# calculators/financial/aspect_analyzer.py

class AspectAnalyzer:
    """Calculates planet-to-planet aspects for financial analysis"""
    
    ASPECT_TYPES = {
        "conjunction": (0, 10),
        "sextile": (60, 6),
        "square": (90, 8),
        "trine": (120, 8),
        "opposition": (180, 10)
    }
    
    def calculate_aspect(self, long1, long2):
        """
        Returns aspect type and strength between two planets
        Returns: (aspect_type, strength) or (None, 0)
        """
        diff = abs(long1 - long2)
        if diff > 180:
            diff = 360 - diff
        
        for aspect_name, (angle, orb) in self.ASPECT_TYPES.items():
            if abs(diff - angle) <= orb:
                strength = 1 - (abs(diff - angle) / orb)  # 0-1 scale
                return aspect_name, strength
        
        return None, 0
    
    def get_all_aspects(self, planets):
        """
        Get all significant aspects between planets
        planets: dict with planet names as keys, each having 'longitude'
        Returns: list of aspect dicts
        """
        aspects = []
        planet_names = list(planets.keys())
        
        for i, p1 in enumerate(planet_names):
            for p2 in planet_names[i+1:]:
                long1 = planets[p1]['longitude']
                long2 = planets[p2]['longitude']
                
                aspect_type, strength = self.calculate_aspect(long1, long2)
                
                if aspect_type:
                    aspects.append({
                        'planet1': p1,
                        'planet2': p2,
                        'type': aspect_type,
                        'strength': round(strength, 2),
                        'angle': round(abs(long1 - long2) if abs(long1 - long2) <= 180 else 360 - abs(long1 - long2), 2)
                    })
        
        return aspects
    
    def check_specific_aspect(self, planets, p1_name, p2_name, aspect_types=None):
        """
        Check if specific planets have certain aspects
        aspect_types: list like ['square', 'opposition'] or None for any
        Returns: aspect dict or None
        """
        if p1_name not in planets or p2_name not in planets:
            return None
        
        long1 = planets[p1_name]['longitude']
        long2 = planets[p2_name]['longitude']
        
        aspect_type, strength = self.calculate_aspect(long1, long2)
        
        if aspect_type and (aspect_types is None or aspect_type in aspect_types):
            return {
                'planet1': p1_name,
                'planet2': p2_name,
                'type': aspect_type,
                'strength': round(strength, 2)
            }
        
        return None
