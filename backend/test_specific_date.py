#!/usr/bin/env python3

from datetime import datetime

# Test the specific case: Jun 9 - Jul 30 '25
# Mars in 2nd house, Sun in 11th house during this period

def test_specific_transit():
    # Simulate the calculation for June 15, 2025
    test_date = datetime(2025, 6, 15)
    
    # Given: Mars in 2nd house, Sun in 11th house during transit
    mars_transit_house = 2
    sun_natal_house = 11
    
    # Calculate what aspect Mars makes to Sun
    house_diff = (sun_natal_house - mars_transit_house) % 12
    actual_aspect = 1 if house_diff == 0 else house_diff + 1
    
    # Mars aspects
    mars_aspects = [1, 4, 7, 8]
    
    print(f"Date: {test_date.strftime('%Y-%m-%d')}")
    print(f"Transit Mars in house: {mars_transit_house}")
    print(f"Natal Sun in house: {sun_natal_house}")
    print(f"House difference: ({sun_natal_house} - {mars_transit_house}) % 12 = {house_diff}")
    print(f"Actual aspect Mars makes: {actual_aspect}th")
    print(f"Mars can make aspects: {mars_aspects}")
    print(f"Can Mars make {actual_aspect}th aspect? {actual_aspect in mars_aspects}")
    print()
    
    if actual_aspect in mars_aspects:
        print("✓ This should be a VALID period")
    else:
        print("✗ This should be INVALID - Mars cannot make this aspect")
        print("The system should NOT show this period in timeline")

if __name__ == "__main__":
    test_specific_transit()