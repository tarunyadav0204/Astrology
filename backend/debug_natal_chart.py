#!/usr/bin/env python3

# Debug the natal chart to see what aspects actually exist
def debug_natal_aspects():
    print("Debugging natal chart aspects...")
    
    # Sample natal chart (you can replace with actual values)
    # Let's assume this is what the system calculated
    natal_planets = {
        'Sun': {'house': 9},      # Example: Sun in 9th house
        'Mars': {'house': 2},     # Example: Mars in 2nd house
        'Jupiter': {'house': 5},
        'Saturn': {'house': 8}
    }
    
    vedic_aspects = {
        'Mars': [1, 4, 7, 8],
        'Jupiter': [1, 5, 7, 9],
        'Saturn': [1, 3, 7, 10]
    }
    
    transit_planets = ['Mars', 'Jupiter', 'Saturn']
    natal_planets_list = ['Sun', 'Mars', 'Jupiter', 'Saturn']
    
    print(f"Natal chart houses: {natal_planets}")
    print()
    
    # Check what aspects exist in natal chart
    for planet1_name, planet1_data in natal_planets.items():
        if planet1_name not in transit_planets:
            continue
            
        planet1_house = planet1_data['house']
        print(f"Checking {planet1_name} in house {planet1_house}:")
        
        for planet2_name, planet2_data in natal_planets.items():
            if planet2_name not in natal_planets_list or planet1_name == planet2_name:
                continue
            
            planet2_house = planet2_data['house']
            
            # Calculate aspect
            house_diff = (planet2_house - planet1_house) % 12
            aspect_number = 1 if house_diff == 0 else house_diff + 1
            
            # Check if valid
            available_aspects = vedic_aspects.get(planet1_name, [])
            is_valid = aspect_number in available_aspects
            
            status = "✓ VALID" if is_valid else "✗ INVALID"
            print(f"  -> {planet2_name} (house {planet2_house}): {aspect_number}th aspect - {status}")
    
    print("\n" + "="*50)
    print("KEY QUESTION: Does Mars actually make 8th aspect to Sun in natal chart?")
    
    mars_house = natal_planets['Mars']['house']
    sun_house = natal_planets['Sun']['house']
    
    house_diff = (sun_house - mars_house) % 12
    aspect_number = 1 if house_diff == 0 else house_diff + 1
    
    print(f"Mars house {mars_house} -> Sun house {sun_house} = {aspect_number}th aspect")
    print(f"Mars can make: {vedic_aspects['Mars']}")
    print(f"Is {aspect_number}th aspect valid for Mars? {aspect_number in vedic_aspects['Mars']}")
    
    if aspect_number in vedic_aspects['Mars']:
        print("✅ Mars DOES make valid aspect to Sun in natal chart")
        print("   So 'Mars → Sun (8th)' should appear in transit list")
    else:
        print("❌ Mars does NOT make valid aspect to Sun in natal chart")
        print("   So 'Mars → Sun (8th)' should NOT appear in transit list")

if __name__ == "__main__":
    debug_natal_aspects()