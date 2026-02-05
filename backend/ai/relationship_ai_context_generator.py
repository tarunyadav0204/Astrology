import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.base_ai_context_generator import BaseAIContextGenerator

class RelationshipAIContextGenerator(BaseAIContextGenerator):
    """Relationship-specific AI context generator for bhavam bhavesh analysis"""
    
    # Relationship System Instruction
    RELATIONSHIP_SYSTEM_INSTRUCTION = """
You are analyzing a RELATIONSHIP QUERY using Bhavam Bhavesh (house-based) analysis from the native's birth chart ONLY.

🚨 CRITICAL RULE: NEVER ask for birth details of relatives (son, daughter, mother, father, spouse, siblings, etc.)

METHOD: Use the native's chart to analyze relatives through:
1. **Primary House**: The house representing the relative (5th for children, 4th for mother, 9th for father, 7th for spouse, 3rd for siblings)
2. **House Lord**: Strength, position, and aspects of the house lord
3. **Karaka Planet**: Natural significator for the relative (Jupiter for children, Moon for mother, Sun for father, Venus/Jupiter for spouse, Mars for siblings)
4. **Planets in House**: Any planets occupying the relative's house
5. **Aspects to House**: Planetary influences on the relative's house

RESPONSE APPROACH:
- Analyze the relative's nature, health, career, and life events through their representative house
- Use house significations to predict the relative's circumstances
- Consider dasha periods of house lord and karaka for timing
- Provide specific insights about the relative without needing their birth chart

EXAMPLE: "How will be my son?" → Analyze 5th house, 5th lord, Jupiter (Putrakaraka), planets in 5th house, aspects to 5th house

NEVER ask: "Could you provide your son's birth details?" - This violates the Bhavam Bhavesh principle.
"""
    
    def build_relationship_context(self, birth_data: Dict, relationship_type: str, user_question: str = "") -> Dict[str, Any]:
        """Build context for relationship analysis using bhavam bhavesh"""
        
        # Get base context first
        base_context = self.build_base_context(birth_data)
        
        # Add relationship-specific context
        relationship_context = self._build_relationship_specific_context(birth_data, relationship_type, user_question)
        
        # Combine contexts
        return {
            **base_context,
            **relationship_context
        }
    
    def _build_relationship_specific_context(self, birth_data: Dict, relationship_type: str, user_question: str) -> Dict[str, Any]:
        """Build relationship-specific context components"""
        
        # Get chart data from base context
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        
        # Define relationship house mappings
        relationship_houses = {
            'son': {'primary': 5, 'karaka': 'Jupiter', 'description': '5th house (Putra Bhava)'},
            'daughter': {'primary': 5, 'karaka': 'Jupiter', 'description': '5th house (Putra Bhava)'},
            'children': {'primary': 5, 'karaka': 'Jupiter', 'description': '5th house (Putra Bhava)'},
            'mother': {'primary': 4, 'karaka': 'Moon', 'description': '4th house (Matru Bhava)'},
            'father': {'primary': 9, 'karaka': 'Sun', 'description': '9th house (Pitru Bhava)'},
            'spouse': {'primary': 7, 'karaka': 'Venus', 'description': '7th house (Kalatra Bhava)'},
            'husband': {'primary': 7, 'karaka': 'Jupiter', 'description': '7th house (Kalatra Bhava)'},
            'wife': {'primary': 7, 'karaka': 'Venus', 'description': '7th house (Kalatra Bhava)'},
            'siblings': {'primary': 3, 'karaka': 'Mars', 'description': '3rd house (Sahaja Bhava)'},
            'brother': {'primary': 3, 'karaka': 'Mars', 'description': '3rd house (Sahaja Bhava)'},
            'sister': {'primary': 3, 'karaka': 'Mars', 'description': '3rd house (Sahaja Bhava)'}
        }
        
        rel_info = relationship_houses.get(relationship_type.lower(), {
            'primary': 1, 'karaka': 'Sun', 'description': 'General analysis'
        })
        
        context = {
            # System instruction for relationship analysis
            "system_instruction": self.RELATIONSHIP_SYSTEM_INSTRUCTION,
            
            # Relationship analysis type
            "analysis_type": "relationship_bhavam_bhavesh",
            "relationship_type": relationship_type,
            "primary_house": rel_info['primary'],
            "karaka_planet": rel_info['karaka'],
            "house_description": rel_info['description'],
            
            # House analysis
            "relationship_house_analysis": self._analyze_relationship_house(rel_info['primary'], chart_data),
            
            # Karaka analysis
            "karaka_analysis": self._analyze_karaka_planet(rel_info['karaka'], chart_data),
            
            # Bhavam Bhavesh instruction
            "bhavam_bhavesh_instruction": {
                "method": f"Analyze {relationship_type} using {rel_info['description']} and {rel_info['karaka']} as karaka",
                "focus": f"Examine house lord, planets in house, aspects to house, and {rel_info['karaka']} strength",
                "avoid": "Do NOT ask for birth details of the relative - use native's chart only"
            }
        }
        
        return context
    
    def _analyze_relationship_house(self, house_num: int, chart_data: Dict) -> Dict[str, Any]:
        """Analyze the specific house for relationship"""
        planets = chart_data.get('planets', {})
        houses = chart_data.get('houses', [])
        
        if house_num > len(houses):
            return {}
        
        house_sign = houses[house_num - 1].get('sign', 0)
        house_lord = self.SIGN_LORDS.get(house_sign, 'Unknown')
        
        # Find planets in this house
        planets_in_house = []
        for planet, data in planets.items():
            if data.get('house', 1) == house_num:
                planets_in_house.append(planet)
        
        # Get lord's position
        lord_position = {}
        if house_lord in planets:
            lord_data = planets[house_lord]
            lord_position = {
                'house': lord_data.get('house', 1),
                'sign': lord_data.get('sign', 0),
                'longitude': lord_data.get('longitude', 0)
            }
        
        return {
            'house_number': house_num,
            'sign': house_sign,
            'lord': house_lord,
            'lord_position': lord_position,
            'planets_in_house': planets_in_house,
            'planet_count': len(planets_in_house)
        }
    
    def _analyze_karaka_planet(self, karaka: str, chart_data: Dict) -> Dict[str, Any]:
        """Analyze the karaka planet for relationship"""
        planets = chart_data.get('planets', {})
        
        if karaka not in planets:
            return {}
        
        karaka_data = planets[karaka]
        
        return {
            'planet': karaka,
            'house': karaka_data.get('house', 1),
            'sign': karaka_data.get('sign', 0),
            'longitude': karaka_data.get('longitude', 0),
            'strength': self._get_planet_strength(karaka_data),
            'aspects': self._get_planet_aspects(karaka, chart_data)
        }
    
    def _get_planet_strength(self, planet_data: Dict) -> str:
        """Get basic planet strength"""
        sign = planet_data.get('sign', 0)
        house = planet_data.get('house', 1)
        
        if house in [1, 4, 7, 10]:  # Kendra
            return 'Strong'
        elif house in [1, 5, 9]:  # Trikona
            return 'Strong'
        elif house in [6, 8, 12]:  # Dusthana
            return 'Weak'
        else:
            return 'Medium'
    
    def _get_planet_aspects(self, planet_name: str, chart_data: Dict) -> list:
        """Get houses aspected by planet"""
        try:
            from calculators.aspect_calculator import AspectCalculator
            aspect_calc = AspectCalculator(chart_data)
            
            aspected_houses = []
            for house_num in range(1, 13):
                aspecting_planets = aspect_calc.get_aspecting_planets(house_num)
                if planet_name in aspecting_planets:
                    aspected_houses.append(house_num)
            
            return aspected_houses
        except:
            return []
    
    @property
    def SIGN_LORDS(self):
        """Sign lordships"""
        return {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }