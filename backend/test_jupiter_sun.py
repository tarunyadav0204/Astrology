#!/usr/bin/env python3

def test_jupiter_sun_aspect():
    print("Testing Jupiter → Sun aspect:")
    print("=" * 40)
    
    # Jupiter aspects: [1, 5, 7, 9]
    jupiter_aspects = [1, 5, 7, 9]
    jupiter_house = 11
    sun_house = 12
    
    print(f"Jupiter in {jupiter_house}th house")
    print(f"Sun in {sun_house}th house")
    print(f"Jupiter's available aspects: {jupiter_aspects}")
    print()
    
    # Show what Jupiter in 11th house can aspect
    print("Jupiter in 11th house can aspect:")
    for aspect in jupiter_aspects:
        if aspect == 1:
            target_house = jupiter_house  # Conjunction
        else:
            target_house = ((jupiter_house + aspect - 2) % 12) + 1
        print(f"  {aspect}th aspect → {target_house}th house")
    
    print()
    
    # Check if Jupiter can aspect Sun
    can_aspect = False
    aspect_type = None
    
    for test_aspect in jupiter_aspects:
        if test_aspect == 1:
            # Conjunction - same house
            if jupiter_house == sun_house:
                can_aspect = True
                aspect_type = 1
                break
        else:
            # Calculate target house for this aspect
            target_house = ((jupiter_house + test_aspect - 2) % 12) + 1
            if target_house == sun_house:
                can_aspect = True
                aspect_type = test_aspect
                break
    
    print(f"Can Jupiter (11th) aspect Sun (12th)? {can_aspect}")
    if can_aspect:
        print(f"Aspect type: {aspect_type}th aspect")
    else:
        print("No valid aspect exists")
    
    print()
    print("Conclusion:")
    if can_aspect:
        print(f"✓ Jupiter in 11th house DOES aspect Sun in 12th house via {aspect_type}th aspect")
    else:
        print("✗ Jupiter in 11th house does NOT aspect Sun in 12th house")

if __name__ == "__main__":
    test_jupiter_sun_aspect()