#!/usr/bin/env python3

# Test the backend logic directly
class TestVedicAspects:
    def __init__(self):
        self.vedic_aspects = {
            'Mars': [1, 4, 7, 8],
        }
    
    def test_timeline_validation(self):
        print("Testing timeline validation logic...")
        
        # Test case: Mars in 2nd house, Sun in 11th house (should be INVALID)
        transit_planet = 'Mars'
        transit_house = 2
        natal_house = 11
        aspect_house = 8  # Required aspect from natal chart
        
        # Calculate actual aspect
        actual_house_diff = (natal_house - transit_house) % 12
        actual_aspect = 1 if actual_house_diff == 0 else actual_house_diff + 1
        
        print(f"\nTest Case: {transit_planet} in house {transit_house} to natal house {natal_house}")
        print(f"Actual house diff: ({natal_house} - {transit_house}) % 12 = {actual_house_diff}")
        print(f"Actual aspect: {actual_aspect}")
        print(f"Required aspect: {aspect_house}")
        
        # Validation logic
        available_aspects = self.vedic_aspects.get(transit_planet, [])
        can_make_this_aspect = actual_aspect in available_aspects
        matches_required = actual_aspect == aspect_house
        
        can_make_aspect = (transit_planet in self.vedic_aspects and 
                         can_make_this_aspect and 
                         matches_required)
        
        print(f"Available aspects for {transit_planet}: {available_aspects}")
        print(f"Can make {actual_aspect}th aspect? {can_make_this_aspect}")
        print(f"Matches required {aspect_house}th? {matches_required}")
        print(f"Final validation: {can_make_aspect}")
        
        if can_make_aspect:
            print("❌ ERROR: This should be INVALID but passed validation!")
        else:
            print("✅ CORRECT: This is properly rejected")
        
        return can_make_aspect

# Run test
test = TestVedicAspects()
result = test.test_timeline_validation()

print(f"\nResult: {'INVALID PERIOD INCORRECTLY ACCEPTED' if result else 'INVALID PERIOD CORRECTLY REJECTED'}")