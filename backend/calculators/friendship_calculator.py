import swisseph as swe
from .base_calculator import BaseCalculator
from utils.timezone_service import parse_timezone_offset, get_timezone_from_coordinates

class FriendshipCalculator(BaseCalculator):
    """
    Calculates Planetary Friendship (Panchadha Maitri) and Vedic Aspects (Drishti).
    Follows standard Parashari principles.
    """
    
    def __init__(self):
        # Natural Friendship (Naisargika Maitri)
        # Based on Brihat Parashara Hora Shastra
        self.NATURAL_FRIENDS = {
            'Sun': ['Moon', 'Mars', 'Jupiter'],
            'Moon': ['Sun', 'Mercury'],
            'Mars': ['Sun', 'Moon', 'Jupiter'],
            'Mercury': ['Sun', 'Venus'],
            'Jupiter': ['Sun', 'Moon', 'Mars'],
            'Venus': ['Mercury', 'Saturn'],
            'Saturn': ['Mercury', 'Venus'],
            'Rahu': ['Venus', 'Saturn', 'Mercury'],
            'Ketu': ['Mars', 'Sun', 'Moon']
        }
        
        self.NATURAL_ENEMIES = {
            'Sun': ['Venus', 'Saturn'],
            'Moon': [], # Moon has no natural enemies
            'Mars': ['Mercury'],
            'Mercury': ['Moon'],
            'Jupiter': ['Mercury', 'Venus'],
            'Venus': ['Sun', 'Moon'],
            'Saturn': ['Sun', 'Moon', 'Mars'],
            'Rahu': ['Sun', 'Moon', 'Mars'],
            'Ketu': ['Sun', 'Moon', 'Venus']
        }
    
    def calculate_compound_relation(self, p1: str, p2: str, p1_sign: int, p2_sign: int) -> str:
        """
        Calculates the 5-fold (Panchadha) relationship.
        1. Natural + Temporal = Compound
        """
        # 1. Determine Natural Relation
        natural = 'neutral'
        if p2 in self.NATURAL_FRIENDS.get(p1, []):
            natural = 'friend'
        elif p2 in self.NATURAL_ENEMIES.get(p1, []):
            natural = 'enemy'
            
        # 2. Determine Temporal Relation (Tatkalika)
        # Rule: Planets in 2, 3, 4, 10, 11, 12 houses from the planet are friends.
        # house_diff is 0-indexed distance (1 to 11)
        diff = (p2_sign - p1_sign) % 12
        # diff 1=2nd house, 2=3rd, 3=4th, 9=10th, 10=11th, 11=12th
        temporal = 'friend' if diff in [1, 2, 3, 9, 10, 11] else 'enemy'
        
        # 3. Compound Logic (Panchadha)
        if natural == 'friend':
            return 'great_friend' if temporal == 'friend' else 'neutral'
        elif natural == 'enemy':
            return 'neutral' if temporal == 'friend' else 'great_enemy'
        else:  # natural is neutral
            return 'friend' if temporal == 'friend' else 'enemy'
    
    def get_vedic_aspects(self, p1: str, p1_long: float, p2_long: float):
        """
        Calculates Vedic Drishti (Aspect) strength.
        Returns a dictionary with type and strength (0 to 1).
        """
        # House-based difference (1-indexed)
        p1_house = int(p1_long / 30) + 1
        p2_house = int(p2_long / 30) + 1
        house_diff = (p2_house - p1_house) % 12 + 1
        
        strength = 0
        aspect_type = 'none'
        
        # All planets have 7th house aspect (100% strength)
        if house_diff == 7:
            strength = 1.0
            aspect_type = 'full'
            
        # Special Aspects
        if p1 == 'Mars' and house_diff in [4, 8]:
            strength = 1.0
            aspect_type = 'special'
        elif p1 == 'Jupiter' and house_diff in [5, 9]:
            strength = 1.0
            aspect_type = 'special'
        elif p1 == 'Saturn' and house_diff in [3, 10]:
            strength = 1.0
            aspect_type = 'special'
        elif p1 in ['Rahu', 'Ketu'] and house_diff in [5, 9]:
            # Rahu/Ketu are often given Jupiter-like aspects in many traditions
            strength = 1.0
            aspect_type = 'special'
            
        # Partial aspects (optional, but good for completeness)
        # 3, 10 (except Saturn) = 25%
        # 5, 9 (except Jupiter/Nodes) = 50%
        # 4, 8 (except Mars) = 75%
        if strength == 0:
            if house_diff in [3, 10]: strength = 0.25
            elif house_diff in [5, 9]: strength = 0.50
            elif house_diff in [4, 8]: strength = 0.75
            
            if strength > 0:
                aspect_type = 'partial'

        return aspect_type, strength

    def calculate_friendship(self, birth_data):
        """Calculate planetary friendship matrix and Vedic aspects"""
        if isinstance(birth_data, dict):
            time_str = birth_data.get('time', '12:00')
            date_str = birth_data.get('date', '2000-01-01')
            latitude = birth_data.get('latitude', 0.0)
            longitude = birth_data.get('longitude', 0.0)
            timezone = birth_data.get('timezone', '')
        else:
            time_str = birth_data.time
            date_str = birth_data.date
            latitude = birth_data.latitude
            longitude = birth_data.longitude
            timezone = getattr(birth_data, 'timezone', '')
        
        # Centralized Timezone Handling
        tz_offset = parse_timezone_offset(timezone, latitude, longitude)
        
        time_parts = time_str.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        utc_hour = hour - tz_offset
        
        jd = swe.julday(
            int(date_str.split('-')[0]),
            int(date_str.split('-')[1]),
            int(date_str.split('-')[2]),
            utc_hour
        )
        
        # Planet mapping for Swiss Ephemeris
        # Sun=0, Moon=1, Mars=4, Merc=2, Jup=5, Ven=3, Sat=6, Rahu=11
        planet_map = {
            'Sun': 0, 'Moon': 1, 'Mars': 4, 'Mercury': 2, 
            'Jupiter': 5, 'Venus': 3, 'Saturn': 6, 'Rahu': swe.TRUE_NODE
        }
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        planets = {}
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        for name in planet_names:
            if name == 'Ketu':
                # Ketu is always 180 degrees from Rahu
                rahu_long = planets['Rahu']['longitude']
                long = (rahu_long + 180) % 360
            else:
                swe_id = planet_map[name]
                res = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL)
                long = res[0][0] if isinstance(res[0], (list, tuple)) else res[0]
            
            planets[name] = {
                'sign': int(long / 30),
                'longitude': long
            }
        
        # 1. Calculate Friendship Matrix
        friendship_matrix = {}
        for p1 in planet_names:
            friendship_matrix[p1] = {}
            for p2 in planet_names:
                if p1 == p2:
                    friendship_matrix[p1][p2] = 'self'
                else:
                    friendship_matrix[p1][p2] = self.calculate_compound_relation(
                        p1, p2, planets[p1]['sign'], planets[p2]['sign']
                    )
        
        # 2. Calculate Vedic Aspects Matrix
        aspects_matrix = {}
        for p1 in planet_names:
            aspects_matrix[p1] = {}
            for p2 in planet_names:
                if p1 == p2:
                    aspects_matrix[p1][p2] = 'self'
                else:
                    asp_type, strength = self.get_vedic_aspects(
                        p1, planets[p1]['longitude'], planets[p2]['longitude']
                    )
                    aspects_matrix[p1][p2] = {
                        'type': asp_type,
                        'strength': strength,
                        'angle': round(abs(planets[p1]['longitude'] - planets[p2]['longitude']) % 360, 2)
                    }
        
        return {
            "friendship_matrix": friendship_matrix, 
            "aspects_matrix": aspects_matrix,
            "planet_positions": planets
        }
