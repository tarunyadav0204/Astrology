import swisseph as swe
from .base_calculator import BaseCalculator
from utils.timezone_service import parse_timezone_offset, get_timezone_from_coordinates

class FriendshipCalculator(BaseCalculator):
    """Extract friendship calculation logic from main.py"""
    
    def __init__(self):
        # Don't call super().__init__() since we don't need chart_data
        self.NATURAL_FRIENDS = {
            'Sun': ['Moon', 'Mars', 'Jupiter'],
            'Moon': ['Sun', 'Mercury'],
            'Mars': ['Sun', 'Moon', 'Jupiter'],
            'Mercury': ['Sun', 'Venus'],
            'Jupiter': ['Sun', 'Moon', 'Mars'],
            'Venus': ['Mercury', 'Saturn'],
            'Saturn': ['Mercury', 'Venus'],
            'Rahu': [],
            'Ketu': []
        }
        
        self.NATURAL_ENEMIES = {
            'Sun': ['Venus', 'Saturn'],
            'Moon': ['None'],
            'Mars': ['Mercury'],
            'Mercury': ['Moon'],
            'Jupiter': ['Mercury', 'Venus'],
            'Venus': ['Sun', 'Moon'],
            'Saturn': ['Sun', 'Moon', 'Mars'],
            'Rahu': ['Sun', 'Moon', 'Mars'],
            'Ketu': ['Sun', 'Moon', 'Mars']
        }
    
    def calculate_compound_relation(self, p1: str, p2: str, p1_house: int, p2_house: int) -> str:
        """Calculates the 5-fold (Panchadha) relationship for Shadbala Sthana Bala."""
        
        # 1. Determine Natural Relation
        natural = 'neutral'
        if p2 in self.NATURAL_FRIENDS.get(p1, []):
            natural = 'friend'
        elif p2 in self.NATURAL_ENEMIES.get(p1, []):
            natural = 'enemy'
            
        # 2. Determine Temporal Relation (Tatkalika)
        # Rule: 2, 3, 4, 10, 11, 12 houses from planet are friends.
        diff = (p2_house - p1_house) % 12
        temporal = 'friend' if diff in [1, 2, 3, 9, 10, 11] else 'enemy'
        
        # 3. Compound Logic (Panchadha)
        if natural == 'friend':
            return 'great_friend' if temporal == 'friend' else 'neutral'
        elif natural == 'enemy':
            return 'neutral' if temporal == 'friend' else 'great_enemy'
        else:  # natural is neutral
            return 'friend' if temporal == 'friend' else 'enemy'
    
    def calculate_friendship(self, birth_data):
        """Calculate planetary friendship matrix"""
        # Handle both dict and object input
        if isinstance(birth_data, dict):
            time_str = birth_data.get('time', '12:00')
            date_str = birth_data.get('date', '2000-01-01')
            latitude = birth_data.get('latitude', 0.0)
            longitude = birth_data.get('longitude', 0.0)
            timezone = birth_data.get('timezone', 'UTC+05:30')
        else:
            time_str = birth_data.time
            date_str = birth_data.date
            latitude = birth_data.latitude
            longitude = birth_data.longitude
            # Calculate timezone from coordinates if not provided
            if hasattr(birth_data, 'timezone'):
                timezone = birth_data.timezone
            else:
                timezone = get_timezone_from_coordinates(latitude, longitude)
        
        # Calculate planetary positions
        time_parts = time_str.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        # Get timezone offset using centralized service
        tz_offset = parse_timezone_offset(
            timezone,
            latitude,
            longitude
        )
        
        utc_hour = hour - tz_offset
        jd = swe.julday(
            int(date_str.split('-')[0]),
            int(date_str.split('-')[1]),
            int(date_str.split('-')[2]),
            utc_hour
        )
        
        # Get planetary positions
        planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
            if planet <= 6:
                # Set Lahiri Ayanamsa for accurate Vedic calculations

                swe.set_sid_mode(swe.SIDM_LAHIRI)

                pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
            else:
                pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0]
                if planet == 12:
                    pos = list(pos)
                    pos[0] = (pos[0] + 180) % 360
            
            planets[planet_names[i]] = {
                'sign': int(pos[0] / 30),
                'longitude': pos[0]
            }
        
        # Calculate compound friendship
        friendship_matrix = {}
        
        for planet1 in planet_names:
            friendship_matrix[planet1] = {}
            
            for planet2 in planet_names:
                if planet1 == planet2:
                    friendship_matrix[planet1][planet2] = 'self'
                    continue
                
                # Natural friendship
                if planet2 in self.NATURAL_FRIENDS.get(planet1, []):
                    natural = 'friend'
                elif planet2 in self.NATURAL_ENEMIES.get(planet1, []):
                    natural = 'enemy'
                else:
                    natural = 'neutral'
                
                # Temporal friendship (based on house distance)
                house_diff = abs(planets[planet1]['sign'] - planets[planet2]['sign'])
                if house_diff > 6:
                    house_diff = 12 - house_diff
                
                if house_diff in [1, 3, 5, 9, 11]:
                    temporal = 'friend'
                elif house_diff in [2, 4, 6, 8, 10, 12]:
                    temporal = 'enemy'
                else:
                    temporal = 'neutral'
                
                # Compound relationship
                if natural == 'friend' and temporal == 'friend':
                    compound = 'great_friend'
                elif natural == 'friend' and temporal == 'neutral':
                    compound = 'friend'
                elif natural == 'friend' and temporal == 'enemy':
                    compound = 'neutral'
                elif natural == 'neutral' and temporal == 'friend':
                    compound = 'friend'
                elif natural == 'neutral' and temporal == 'neutral':
                    compound = 'neutral'
                elif natural == 'neutral' and temporal == 'enemy':
                    compound = 'enemy'
                elif natural == 'enemy' and temporal == 'friend':
                    compound = 'neutral'
                elif natural == 'enemy' and temporal == 'neutral':
                    compound = 'enemy'
                else:
                    compound = 'great_enemy'
                
                friendship_matrix[planet1][planet2] = compound
        
        # Calculate aspects
        aspects_matrix = {}
        
        for planet1 in planet_names:
            aspects_matrix[planet1] = {}
            
            for planet2 in planet_names:
                if planet1 == planet2:
                    aspects_matrix[planet1][planet2] = 'self'
                    continue
                
                # Calculate angular difference
                angle_diff = abs(planets[planet1]['longitude'] - planets[planet2]['longitude'])
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                # Vedic aspects with orbs
                aspect_type = 'none'
                if 0 <= angle_diff <= 10:  # Conjunction
                    aspect_type = 'conjunction'
                elif 50 <= angle_diff <= 70:  # Sextile (60°)
                    aspect_type = 'sextile'
                elif 80 <= angle_diff <= 100:  # Square (90°)
                    aspect_type = 'square'
                elif 110 <= angle_diff <= 130:  # Trine (120°)
                    aspect_type = 'trine'
                elif 170 <= angle_diff <= 180:  # Opposition (180°)
                    aspect_type = 'opposition'
                
                aspects_matrix[planet1][planet2] = {
                    'type': aspect_type,
                    'angle': round(angle_diff, 1)
                }
        
        return {
            "friendship_matrix": friendship_matrix, 
            "aspects_matrix": aspects_matrix,
            "planet_positions": planets
        }