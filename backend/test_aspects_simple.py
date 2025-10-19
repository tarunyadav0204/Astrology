#!/usr/bin/env python3

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

# Test with sample data based on your example
# Mars in house 1, Sun in house 6 (your example that was showing invalid 6th aspect)
natal_planets = {
    'Sun': {'house': 6},
    'Moon': {'house': 3},
    'Mars': {'house': 1},  # Mars in 1st house
    'Mercury': {'house': 5},
    'Jupiter': {'house': 8},
    'Venus': {'house': 7},
    'Saturn': {'house': 2}
}

print("Testing aspect calculation with your example:")
print("Mars in house 1, Sun in house 6")

calculator = VedicTransitAspectCalculator()
natal_aspects = calculator._find_natal_aspects(natal_planets)

print(f'\nValid natal aspects found: {len(natal_aspects)}')
for aspect in natal_aspects:
    print(f'{aspect["planet1"]} -> {aspect["planet2"]} ({aspect["aspect_type"]})')

print("\n" + "="*50)
print("EXPECTED: Mars in house 1 to Sun in house 6 should NOT be valid")
print("because Mars (1st house) to Sun (6th house) = 6th aspect")
print("but Mars only has 1st, 4th, 7th, 8th aspects")