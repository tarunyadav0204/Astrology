"""
Planetary Placement Validator
Validates AI-generated career analysis against actual chart data
"""

import re
from typing import Dict, List, Tuple

class PlanetaryPlacementValidator:
    """Validates planetary placements mentioned in AI analysis"""
    
    PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    HOUSES = list(range(1, 13))
    SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    def __init__(self, context: Dict):
        """Initialize with career context data"""
        self.context = context
        self.d1_planets = context.get('d1_chart', {}).get('planets', {})
        self.d10_planets = context.get('d10_detailed', {}).get('planets', {})
        
    def validate_analysis(self, analysis_text: str, chart_type: str = 'd1') -> Tuple[bool, List[str]]:
        """
        Validate planetary placements mentioned in analysis text
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        planets_data = self.d1_planets if chart_type == 'd1' else self.d10_planets
        
        # Extract planetary placement claims from text
        claims = self._extract_placement_claims(analysis_text)
        
        for claim in claims:
            planet = claim['planet']
            claimed_house = claim.get('house')
            claimed_sign = claim.get('sign')
            
            if planet not in planets_data:
                errors.append(f"❌ {planet} not found in chart data")
                continue
            
            actual_data = planets_data[planet]
            actual_house = actual_data.get('house')
            actual_sign_name = actual_data.get('sign_name')
            
            # Validate house
            if claimed_house and claimed_house != actual_house:
                errors.append(
                    f"❌ {planet} house mismatch: AI claims {claimed_house}th house, "
                    f"actual is {actual_house}th house"
                )
            
            # Validate sign
            if claimed_sign and claimed_sign != actual_sign_name:
                errors.append(
                    f"❌ {planet} sign mismatch: AI claims {claimed_sign}, "
                    f"actual is {actual_sign_name}"
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _extract_placement_claims(self, text: str) -> List[Dict]:
        """Extract planetary placement claims from text"""
        claims = []
        
        # Pattern: "Mars in 7th house"
        house_pattern = r'(\w+)\s+(?:is\s+)?in\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)\s+house'
        for match in re.finditer(house_pattern, text, re.IGNORECASE):
            planet = match.group(1)
            house = int(match.group(2))
            if planet in self.PLANETS and house in self.HOUSES:
                claims.append({'planet': planet, 'house': house})
        
        # Pattern: "Mars in Libra"
        sign_pattern = r'(\w+)\s+(?:is\s+)?in\s+(\w+)\s+sign'
        for match in re.finditer(sign_pattern, text, re.IGNORECASE):
            planet = match.group(1)
            sign = match.group(2)
            if planet in self.PLANETS and sign in self.SIGNS:
                claims.append({'planet': planet, 'sign': sign})
        
        # Pattern: "Mars in 7th house in Libra"
        combined_pattern = r'(\w+)\s+(?:is\s+)?in\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)\s+house\s+in\s+(\w+)'
        for match in re.finditer(combined_pattern, text, re.IGNORECASE):
            planet = match.group(1)
            house = int(match.group(2))
            sign = match.group(3)
            if planet in self.PLANETS and house in self.HOUSES and sign in self.SIGNS:
                claims.append({'planet': planet, 'house': house, 'sign': sign})
        
        return claims
    
    def generate_correction_prompt(self, errors: List[str]) -> str:
        """Generate a correction prompt for AI if errors found"""
        if not errors:
            return ""
        
        correction = "⚠️ CRITICAL ERRORS DETECTED IN PLANETARY PLACEMENTS:\n\n"
        correction += "\n".join(errors)
        correction += "\n\n📊 CORRECT PLANETARY POSITIONS:\n"
        
        for planet, data in self.d1_planets.items():
            correction += f"  {planet}: {data.get('house')}th house, {data.get('sign_name')} sign\n"
        
        correction += "\n🔄 Please regenerate the analysis using ONLY these correct positions."
        
        return correction
    
    def validate_and_log(self, analysis_text: str, chart_type: str = 'd1') -> bool:
        """Validate and log results"""
        is_valid, errors = self.validate_analysis(analysis_text, chart_type)
        
        if is_valid:
            print("✅ Planetary placement validation PASSED")
            return True
        else:
            print("❌ Planetary placement validation FAILED")
            print("\n" + "="*80)
            print("VALIDATION ERRORS:")
            print("="*80)
            for error in errors:
                print(error)
            print("="*80)
            print(self.generate_correction_prompt(errors))
            return False


# Example usage
if __name__ == "__main__":
    # Mock context for testing
    mock_context = {
        'd1_chart': {
            'planets': {
                'Mars': {'house': 7, 'sign': 6, 'sign_name': 'Libra'},
                'Sun': {'house': 10, 'sign': 9, 'sign_name': 'Capricorn'},
                'Mercury': {'house': 10, 'sign': 9, 'sign_name': 'Capricorn'}
            }
        }
    }
    
    # Test with correct analysis
    correct_analysis = "Mars is in the 7th house in Libra sign, indicating partnership-oriented career."
    
    # Test with incorrect analysis
    incorrect_analysis = "Mars is in the 3rd house in Aries sign, showing communication skills."
    
    validator = PlanetaryPlacementValidator(mock_context)
    
    print("Testing CORRECT analysis:")
    validator.validate_and_log(correct_analysis)
    
    print("\n" + "="*80 + "\n")
    
    print("Testing INCORRECT analysis:")
    validator.validate_and_log(incorrect_analysis)
