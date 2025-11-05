"""
Planetary War Calculator - Graha Yuddha
Based on classical Vedic astrology principles from Brihat Parashara Hora Shastra
"""

class PlanetaryWarCalculator:
    """Calculate planetary wars (Graha Yuddha) when planets are within 1 degree"""
    
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.war_planets = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']  # Exclude Sun, Moon, Rahu, Ketu
        
    def calculate_planetary_wars(self):
        """Calculate all planetary wars in the chart"""
        wars = []
        
        for i, planet1 in enumerate(self.war_planets):
            for planet2 in self.war_planets[i+1:]:
                war_result = self._check_planetary_war(planet1, planet2)
                if war_result:
                    wars.append(war_result)
        
        return wars
    
    def _check_planetary_war(self, planet1, planet2):
        """Check if two planets are in war (within 1 degree)"""
        pos1 = self.chart_data.get(planet1, 0)
        pos2 = self.chart_data.get(planet2, 0)
        
        # Calculate angular distance
        diff = abs(pos1 - pos2)
        if diff > 180:
            diff = 360 - diff
        
        # War occurs when planets are within 1 degree
        if diff <= 1.0:
            winner, loser = self._determine_winner(planet1, planet2, pos1, pos2)
            return {
                'planet1': planet1,
                'planet2': planet2,
                'planet1_degree': pos1,
                'planet2_degree': pos2,
                'angular_distance': diff,
                'winner': winner,
                'loser': loser,
                'war_type': self._get_war_type(diff),
                'effects': self._get_war_effects(winner, loser)
            }
        
        return None
    
    def _determine_winner(self, planet1, planet2, pos1, pos2):
        """Determine winner based on classical rules"""
        
        # Rule 1: Planet with higher longitude wins (more advanced in degree)
        if pos1 > pos2:
            primary_winner, primary_loser = planet1, planet2
        else:
            primary_winner, primary_loser = planet2, planet1
        
        # Rule 2: Size-based exceptions (larger planet wins)
        size_order = {
            'Jupiter': 5,    # Largest
            'Saturn': 4,
            'Mars': 3,
            'Venus': 2,
            'Mercury': 1     # Smallest
        }
        
        planet1_size = size_order.get(planet1, 0)
        planet2_size = size_order.get(planet2, 0)
        
        # If size difference is significant, larger planet wins
        if abs(planet1_size - planet2_size) >= 2:
            if planet1_size > planet2_size:
                return planet1, planet2
            else:
                return planet2, planet1
        
        # Rule 3: Brightness-based (Venus is brightest, then Jupiter, Mars, Saturn, Mercury)
        brightness_order = {
            'Venus': 5,
            'Jupiter': 4,
            'Mars': 3,
            'Saturn': 2,
            'Mercury': 1
        }
        
        planet1_brightness = brightness_order.get(planet1, 0)
        planet2_brightness = brightness_order.get(planet2, 0)
        
        if planet1_brightness > planet2_brightness:
            return planet1, planet2
        elif planet2_brightness > planet1_brightness:
            return planet2, planet1
        
        # Default to longitude rule
        return primary_winner, primary_loser
    
    def _get_war_type(self, angular_distance):
        """Classify war intensity based on distance"""
        if angular_distance <= 0.25:
            return 'Intense War'
        elif angular_distance <= 0.5:
            return 'Moderate War'
        else:
            return 'Mild War'
    
    def _get_war_effects(self, winner, loser):
        """Get effects of planetary war"""
        return {
            'winner_effects': f"{winner} gains strength and prominence in significations",
            'loser_effects': f"{loser} loses strength and may give adverse results",
            'general_effects': "Conflict in areas ruled by both planets, eventual victory for winner's significations",
            'timing_note': "Effects most prominent during dashas/transits of involved planets"
        }
    
    def get_war_summary(self):
        """Get summary of all planetary wars"""
        wars = self.calculate_planetary_wars()
        
        if not wars:
            return {
                'total_wars': 0,
                'wars': [],
                'summary': 'No planetary wars detected in this chart'
            }
        
        return {
            'total_wars': len(wars),
            'wars': wars,
            'summary': f"{len(wars)} planetary war(s) detected - check individual war details for specific effects"
        }