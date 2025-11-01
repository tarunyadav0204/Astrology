import swisseph as swe
from .base_calculator import BaseCalculator

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
    
    def calculate_friendship(self, birth_data):
        """Calculate planetary friendship matrix"""
        # Calculate planetary positions
        time_parts = birth_data.time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
            tz_offset = 5.5
        else:
            tz_offset = 0
            if birth_data.timezone.startswith('UTC'):
                tz_str = birth_data.timezone[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
        
        utc_hour = hour - tz_offset
        jd = swe.julday(
            int(birth_data.date.split('-')[0]),
            int(birth_data.date.split('-')[1]),
            int(birth_data.date.split('-')[2]),
            utc_hour
        )
        
        # Get planetary positions
        planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
            if planet <= 6:
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