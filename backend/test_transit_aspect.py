#!/usr/bin/env python3

# Test the aspect calculation logic
def test_aspect_calculation():
    print("Testing Mars aspect calculation:")
    print("Mars aspects: [1, 4, 7, 8]")
    print()
    
    # Test case 1: Mars in 2nd house, Sun in 11th house
    mars_house = 2
    sun_house = 11
    
    house_diff = (sun_house - mars_house) % 12
    aspect_number = 1 if house_diff == 0 else house_diff + 1
    
    print(f"Mars in house {mars_house}, Sun in house {sun_house}")
    print(f"House difference: ({sun_house} - {mars_house}) % 12 = {house_diff}")
    print(f"Aspect number: {aspect_number}")
    print(f"Can Mars make {aspect_number}th aspect? {aspect_number in [1, 4, 7, 8]}")
    print()
    
    # Test case 2: Mars in 1st house, Sun in 6th house  
    mars_house = 1
    sun_house = 6
    
    house_diff = (sun_house - mars_house) % 12
    aspect_number = 1 if house_diff == 0 else house_diff + 1
    
    print(f"Mars in house {mars_house}, Sun in house {sun_house}")
    print(f"House difference: ({sun_house} - {mars_house}) % 12 = {house_diff}")
    print(f"Aspect number: {aspect_number}")
    print(f"Can Mars make {aspect_number}th aspect? {aspect_number in [1, 4, 7, 8]}")
    print()
    
    # Test case 3: Valid case - Mars in 1st house, Sun in 8th house
    mars_house = 1
    sun_house = 8
    
    house_diff = (sun_house - mars_house) % 12
    aspect_number = 1 if house_diff == 0 else house_diff + 1
    
    print(f"Mars in house {mars_house}, Sun in house {sun_house}")
    print(f"House difference: ({sun_house} - {mars_house}) % 12 = {house_diff}")
    print(f"Aspect number: {aspect_number}")
    print(f"Can Mars make {aspect_number}th aspect? {aspect_number in [1, 4, 7, 8]}")

if __name__ == "__main__":
    test_aspect_calculation()