#!/usr/bin/env python3

import swisseph as swe
from datetime import datetime

class VedicTransitAspectCalculator:
    def __init__(self):
        # Traditional Vedic aspects for each planet (including conjunction)
        self.vedic_aspects = {
            'Sun': [1, 7],           # Conjunction, 7th house aspect
            'Moon': [1, 7],          # Conjunction, 7th house aspect
            'Mars': [1, 4, 7, 8],    # Conjunction, 4th, 7th, 8th house aspects
            'Mercury': [1, 7],       # Conjunction, 7th house aspect
            'Jupiter': [1, 5, 7, 9], # Conjunction, 5th, 7th, 9th house aspects
            'Venus': [1, 7],         # Conjunction, 7th house aspect
            'Saturn': [1, 3, 7, 10], # Conjunction, 3rd, 7th, 10th house aspects
            'Rahu': [1, 5, 7, 9],    # Conjunction, 5th, 7th, 9th house aspects
            'Ketu': [1, 5, 7, 9]     # Conjunction, 5th, 7th, 9th house aspects
        }
        
        self.transit_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
        self.natal_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    def _find_natal_aspects(self, natal_planets):
        """Find all aspects that exist in the natal chart"""
        natal_aspects = []
        
        print(f"\n=== FINDING NATAL ASPECTS ===")
        print(f"Available planets: {list(natal_planets.keys())}")
        
        for planet1_name, planet1_data in natal_planets.items():
            if planet1_name not in self.transit_planets or not isinstance(planet1_data, dict):
                continue
                
            planet1_house = planet1_data.get('house', 1)
            print(f"\nChecking {planet1_name} in house {planet1_house}:")
            
            for planet2_name, planet2_data in natal_planets.items():
                if (planet2_name not in self.natal_planets or 
                    not isinstance(planet2_data, dict) or 
                    planet1_name == planet2_name):
                    continue
                
                planet2_house = planet2_data.get('house', 1)
                
                # Calculate which house planet2 is FROM planet1's perspective
                house_diff = (planet2_house - planet1_house) % 12
                if house_diff == 0:
                    aspect_number = 1  # Same house = conjunction
                else:
                    aspect_number = house_diff + 1  # House position from aspecting planet
                
                print(f"  -> {planet2_name} (house {planet2_house}): {aspect_number}th position from {planet1_name}")
                
                # Check if planet1 can actually make this aspect
                if planet1_name in self.vedic_aspects:
                    available_aspects = self.vedic_aspects[planet1_name]
                    print(f"     {planet1_name} can make aspects: {available_aspects}")
                    
                    if aspect_number in available_aspects:
                        natal_aspects.append({
                            'planet1': planet1_name,
                            'planet2': planet2_name,
                            'aspect_type': f'{aspect_number}th_house',
                            'house_difference': aspect_number
                        })
                        print(f"     ✓ VALID ASPECT: {planet1_name} {aspect_number}th aspect to {planet2_name}")
                    else:
                        print(f"     ✗ Invalid aspect: {planet1_name} cannot make {aspect_number}th aspect (only has {available_aspects})")
        
        print(f"\nTotal natal aspects found: {len(natal_aspects)}")
        return natal_aspects

def calculate_natal_positions(birth_data):
    """Calculate natal planet positions"""
    try:
        # Set Lahiri Ayanamsa
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Parse birth data
        time_parts = birth_data['time'].split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        # Handle timezone (simplified)
        tz_offset = 5.5  # IST
        utc_hour = hour - tz_offset
        
        jd = swe.julday(
            int(birth_data['date'].split('-')[0]),
            int(birth_data['date'].split('-')[1]),
            int(birth_data['date'].split('-')[2]),
            utc_hour
        )
        
        # Calculate ascendant first
        houses_data = swe.houses(jd, birth_data['latitude'], birth_data['longitude'], b'P')
        ayanamsa = swe.get_ayanamsa_ut(jd)
        ascendant_tropical = houses_data[1][0]
        ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
        ascendant_sign = int(ascendant_sidereal / 30)
        
        # Calculate planetary positions
        planets = {
            'ascendant_sign': ascendant_sign,
            'ascendant_longitude': ascendant_sidereal
        }
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6]):
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            longitude = pos[0][0]
            planet_sign = int(longitude / 30)
            house_number = ((planet_sign - ascendant_sign) % 12) + 1
            
            planets[planet_names[i]] = {
                'longitude': longitude,
                'sign': planet_sign,
                'degree': longitude % 30,
                'house': house_number
            }
        
        return planets
    
    except Exception as e:
        print(f"Error calculating natal positions: {e}")
        return {}

# Test with your birth data
birth_data = {
    'name': 'Test',
    'date': '1990-01-01',
    'time': '12:00',
    'latitude': 28.6139,
    'longitude': 77.2090,
    'timezone': 'UTC+05:30'
}

print("Testing aspect calculation...")
natal_planets = calculate_natal_positions(birth_data)

print('\nNatal planets with houses:')
for planet, data in natal_planets.items():
    if isinstance(data, dict) and 'house' in data:
        print(f'{planet}: House {data["house"]}')

calculator = VedicTransitAspectCalculator()
natal_aspects = calculator._find_natal_aspects(natal_planets)

print(f'\nValid natal aspects found: {len(natal_aspects)}')
for aspect in natal_aspects:
    print(f'{aspect["planet1"]} -> {aspect["planet2"]} ({aspect["aspect_type"]})')