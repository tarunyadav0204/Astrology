from typing import Dict, List, Any, Optional
import math

class PrashnaCalculator:
    """
    God-Tier Horary (Prashna) Calculator based on Tajik Neelakanthi.
    Determines Binary Outcomes (Yes/No) using Ithasala Yoga logic.
    """
    
    # Tajik Orbs (Deeptamsa) - The range of influence for each planet
    ORBS = {
        'Sun': 15, 'Moon': 12, 'Mars': 8, 'Mercury': 7, 
        'Jupiter': 9, 'Venus': 7, 'Saturn': 9, 'Rahu': 0, 'Ketu': 0
    }
    
    # Question Categories -> House Mapping
    TOPIC_MAP = {
        'job': 10, 'career': 10, 'promotion': 10, 'business': 10, 'fame': 10,
        'love': 7, 'relationship': 7, 'marriage': 7, 'partner': 7, 'contract': 7,
        'wealth': 2, 'money': 2, 'finance': 2, 'lost_item': 2, 'family': 2,
        'health': 6, 'disease': 6, 'court_case': 6, 'enemy': 6, 'competition': 6,
        'property': 4, 'home': 4, 'vehicle': 4, 'mother': 4,
        'child': 5, 'pregnancy': 5, 'education': 5, 'speculation': 5,
        'travel': 9, 'visa': 9, 'foreign': 9, 'higher_study': 9,
        'gain': 11, 'friend': 11, 'wish': 11,
        'loss': 12, 'hospital': 12, 'foreign_settlement': 12
    }

    def __init__(self, chart_data: Dict[str, Any]):
        """
        Initialize with a calculated chart (Planets + House Cusps).
        """
        self.chart = chart_data
        self.planets = chart_data.get('planets', {})
        self.ascendant = chart_data.get('ascendant', 0.0)
        self.houses = chart_data.get('houses', [])
        
        # Determine Lagna Lord (Querent)
        asc_sign_idx = int(self.ascendant / 30)
        self.lagna_lord_name = self._get_lord_of_sign(asc_sign_idx)
        self.lagna_lord = self.planets.get(self.lagna_lord_name)

    def analyze_question(self, question_category: str = 'job') -> Dict[str, Any]:
        """
        Main entry point. Returns the Verdict and Analysis.
        """
        # 1. Identify the Objective (Karyesha)
        target_house_num = self.TOPIC_MAP.get(question_category.lower(), 10)
        karyesha_name = self._get_house_lord(target_house_num)
        karyesha = self.planets.get(karyesha_name)
        
        moon = self.planets.get('Moon')
        
        # 2. Calculate the Connection (The Yoga)
        connection = self._check_tajik_connection(self.lagna_lord, karyesha)
        
        # 3. Check Moon's Role (The Flow)
        moon_connection = self._check_tajik_connection(moon, karyesha)
        
        # 4. Formulate Verdict
        verdict = "NO"
        confidence = "Low"
        summary = ""
        
        if connection['type'] == 'Ithasala':
            verdict = "YES"
            confidence = "High" if connection['strength'] == 'Strong' else "Medium"
            summary = f"The Lagna Lord ({self.lagna_lord_name}) is moving towards the Goal Lord ({karyesha_name}) creating a successful Ithasala Yoga."
        
        elif connection['type'] == 'Easarpha':
            verdict = "NO"
            summary = f"The opportunity has passed or is separating. The Lagna Lord ({self.lagna_lord_name}) is moving away from the Goal Lord ({karyesha_name})."
            
        elif connection['type'] == 'None' and moon_connection['type'] == 'Ithasala':
            verdict = "YES"
            confidence = "Medium"
            summary = f"Direct connection is weak, but the Moon is transferring the light (Nakta Yoga) to bring success."
            
        else:
            verdict = "NO"
            summary = f"There is no geometric connection between you ({self.lagna_lord_name}) and the goal ({karyesha_name}) at this moment."

        # 5. Determine Timing (Degrees Difference)
        timing_val = abs(self.lagna_lord['longitude'] - karyesha['longitude']) % 360
        if timing_val > 180: timing_val = 360 - timing_val
        timing_unit = "Weeks" 
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "summary": summary,
            "analysis": {
                "querent": {
                    "planet": self.lagna_lord_name,
                    "position": f"{self.lagna_lord.get('sign_name', 'Unknown')} {self.lagna_lord.get('degree', 0):.2f}°",
                    "house": self.lagna_lord.get('house', 0)
                },
                "objective": {
                    "planet": karyesha_name,
                    "significator": f"Lord of {target_house_num}th House",
                    "position": f"{karyesha.get('sign_name', 'Unknown')} {karyesha.get('degree', 0):.2f}°"
                },
                "yoga": {
                    "name": connection['type'],
                    "aspect": connection['aspect'],
                    "orb_gap": f"{connection['gap']:.2f}°",
                    "description": connection['desc']
                },
                "moon_flow": {
                    "status": moon_connection['type'],
                    "description": "Moon is applying to the goal" if moon_connection['type'] == 'Ithasala' else "Moon is void or separating"
                }
            },
            "timing": {
                "value": round(timing_val, 1),
                "unit": timing_unit,
                "prediction": f"Within {round(timing_val, 1)} {timing_unit}"
            }
        }

    def _check_tajik_connection(self, planet_a, planet_b) -> Dict:
        """
        The Core Physics of Prashna.
        Checks if Planet A and Planet B are forming an Ithasala (Applying) Yoga.
        """
        if not planet_a or not planet_b:
            return {'type': 'None', 'aspect': 'None', 'gap': 0, 'desc': 'Invalid data', 'strength': 'None'}
            
        # 1. Identify Faster vs Slower planet
        speed_order = ['Moon', 'Mercury', 'Venus', 'Sun', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu']
        
        try:
            p1_idx = speed_order.index(planet_a.get('name', ''))
            p2_idx = speed_order.index(planet_b.get('name', ''))
            
            if p1_idx < p2_idx:
                fast, slow = planet_a, planet_b
            else:
                fast, slow = planet_b, planet_a
        except:
            fast, slow = planet_a, planet_b
            
        # 2. Calculate Effective Orb
        orb_limit = (self.ORBS.get(fast.get('name', ''), 8) + self.ORBS.get(slow.get('name', ''), 8)) / 2
        
        # 3. Check Aspect
        pos_fast = fast.get('longitude', 0)
        pos_slow = slow.get('longitude', 0)
        
        diff = abs(pos_fast - pos_slow) % 360
        if diff > 180: diff = 360 - diff
        
        aspect_type = "None"
        
        # Tajik Aspects
        if 0 <= diff <= 10: aspect_type = "Conjunction"
        elif 50 <= diff <= 70: aspect_type = "Sextile"
        elif 80 <= diff <= 100: aspect_type = "Square"
        elif 110 <= diff <= 130: aspect_type = "Trine"
        elif 170 <= diff <= 190: aspect_type = "Opposition"
        
        if aspect_type == "None":
            return {'type': 'None', 'aspect': 'None', 'gap': diff, 'desc': 'No aspect formed', 'strength': 'None'}
            
        # 4. Check Ithasala (Applying) vs Easarpha (Separating)
        deg_fast = fast.get('degree', 0)
        deg_slow = slow.get('degree', 0)
        
        gap = abs(deg_fast - deg_slow)
        
        if gap > orb_limit:
             return {'type': 'None', 'aspect': aspect_type, 'gap': gap, 'desc': 'Out of orb', 'strength': 'None'}
        
        # ITASALA (Applying): Fast < Slow
        if deg_fast < deg_slow:
            desc = "Applying Aspect (Future Event)"
            strength = "Strong"
            return {'type': 'Ithasala', 'strength': strength, 'aspect': aspect_type, 'gap': gap, 'desc': desc}
            
        # EASARPHA (Separating): Fast > Slow
        else:
            return {'type': 'Easarpha', 'strength': 'Weak', 'aspect': aspect_type, 'gap': gap, 'desc': 'Separating Aspect (Past Event)'}

    def _get_house_lord(self, house_num: int) -> str:
        """Returns the planet ruling a specific house number in the chart."""
        try:
            # Houses list is 0-indexed, so house 1 is at index 0
            house_data = self.houses[house_num - 1]
            sign_num = house_data.get('sign', 1)
            return self._get_lord_of_sign(sign_num - 1)
        except:
            return 'Saturn'

    def _get_lord_of_sign(self, sign_index: int) -> str:
        """Returns planet ruling the sign index (0=Aries, 11=Pisces)"""
        lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        return lords[sign_index % 12]
