import swisseph as swe
from typing import Dict, List, Any
from .models import EventAnalysis, AnalysisFactor
from .rules_config import DEFAULT_RULES

class EventAnalyzer:
    def __init__(self):
        self.rules = DEFAULT_RULES
    
    def analyze_event(self, birth_chart: Dict, event_date: str, event_type: str) -> EventAnalysis:
        rule = self.get_rule(event_type)
        if not rule:
            return self._create_empty_analysis(event_type, event_date)
        
        # Calculate event chart data
        event_chart_data = self._calculate_event_chart(birth_chart, event_date)
        
        # Layer 1: Karaka & House Analysis
        karaka_factors = self._analyze_karaka_house(birth_chart, rule)
        
        # Layer 2: Dasha Activation
        dasha_factors = self._analyze_dasha_activation(birth_chart, event_date, rule)
        
        # Layer 3: Transit Confirmation
        transit_factors = self._analyze_transit_confirmation(birth_chart, event_date, dasha_factors, rule)
        
        return self._compile_analysis(event_type, event_date, karaka_factors, dasha_factors, transit_factors, rule)
    
    def get_rule(self, event_type: str):
        return self.rules.get(event_type)
    
    def _calculate_event_chart(self, birth_chart: Dict, event_date: str) -> Dict:
        # Calculate planetary positions for event date
        year, month, day = map(int, event_date.split('-'))
        jd = swe.julday(year, month, day, 12.0)  # Noon time
        
        event_positions = {}
        planet_ids = [0, 1, 4, 2, 5, 3, 6, 11, 12]  # Sun to Ketu
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for i, planet_id in enumerate(planet_ids):
            if planet_id <= 6:
                # Set Lahiri Ayanamsa for accurate Vedic calculations

                swe.set_sid_mode(swe.SIDM_LAHIRI)

                pos = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)[0]
            else:
                pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0]
                if planet_id == 12:  # Ketu
                    pos = list(pos)
                    pos[0] = (pos[0] + 180) % 360
            
            event_positions[planet_names[i]] = {
                'longitude': pos[0],
                'sign': int(pos[0] / 30)
            }
        
        return event_positions
    
    def _analyze_karaka_house(self, birth_chart: Dict, rule) -> List[AnalysisFactor]:
        factors = []
        
        # Check primary karaka
        karaka = rule['primary_karaka']
        karaka_data = birth_chart['planets'].get(karaka, {})
        
        for house_num in rule['house_significations']:
            # Check if karaka is in the house
            if karaka_data.get('sign') == (house_num - 1):  # Convert to 0-based
                factors.append(AnalysisFactor(
                    factor_type="karaka",
                    description=f"{karaka} placed in {house_num}th house",
                    weight=40,
                    confidence=85,
                    explanation=f"{karaka} as karaka placed in house of signification"
                ))
        
        return factors
    
    def _analyze_dasha_activation(self, birth_chart: Dict, event_date: str, rule) -> List[AnalysisFactor]:
        factors = []
        
        # Calculate dashas for event date
        dashas = self._calculate_dashas(birth_chart, event_date)
        
        for dasha_level, planet in dashas.items():
            if not planet:
                continue
                
            # Check activation methods
            activations = self._check_house_activation(planet, rule['house_significations'], birth_chart)
            
            for activation in activations:
                weight = self._get_dasha_weight(dasha_level)
                factors.append(AnalysisFactor(
                    factor_type="dasha",
                    description=f"{dasha_level.title()} dasha {planet}: {activation}",
                    weight=weight,
                    confidence=75,
                    explanation=f"Dasha planet {planet} activating relevant house"
                ))
        
        return factors
    
    def _analyze_transit_confirmation(self, birth_chart: Dict, event_date: str, dasha_factors: List, rule) -> List[AnalysisFactor]:
        factors = []
        event_positions = self._calculate_event_chart(birth_chart, event_date)
        
        # Check transits for dasha planets
        dasha_planets = [factor.description.split()[2].rstrip(':') for factor in dasha_factors]
        
        for planet in dasha_planets:
            if planet not in event_positions:
                continue
                
            triggers = self._check_transit_triggers(planet, birth_chart, event_positions, rule)
            
            for trigger in triggers:
                factors.append(AnalysisFactor(
                    factor_type="transit",
                    description=trigger,
                    weight=25,
                    confidence=70,
                    explanation=f"Transit confirmation for dasha planet {planet}"
                ))
        
        return factors
    
    def _check_house_activation(self, planet: str, house_numbers: List[int], birth_chart: Dict) -> List[str]:
        activations = []
        planet_data = birth_chart['planets'].get(planet, {})
        
        for house_num in house_numbers:
            planet_sign = planet_data.get('sign', -1)
            planet_house = planet_sign + 1
            
            # Direct placement
            if planet_sign == (house_num - 1):
                activations.append(f"placed in {house_num}th house")
            
            # Ownership check
            house_lord = self._get_house_lord(house_num, birth_chart)
            if planet == house_lord:
                activations.append(f"owns {house_num}th house")
            
            # Aspect check (7th house aspect for all planets)
            if (planet_house + 6) % 12 + 1 == house_num:
                activations.append(f"aspects {house_num}th house")
            
            # Special aspects for outer planets
            if planet == 'Mars':
                if (planet_house + 3) % 12 + 1 == house_num or (planet_house + 7) % 12 + 1 == house_num:
                    activations.append(f"Mars aspects {house_num}th house")
            elif planet == 'Jupiter':
                if (planet_house + 4) % 12 + 1 == house_num or (planet_house + 8) % 12 + 1 == house_num:
                    activations.append(f"Jupiter aspects {house_num}th house")
            elif planet == 'Saturn':
                if (planet_house + 2) % 12 + 1 == house_num or (planet_house + 9) % 12 + 1 == house_num:
                    activations.append(f"Saturn aspects {house_num}th house")
        
        return activations
    
    def _check_transit_triggers(self, planet: str, birth_chart: Dict, event_positions: Dict, rule) -> List[str]:
        triggers = []
        
        natal_pos = birth_chart['planets'].get(planet, {}).get('longitude', 0)
        transit_pos = event_positions.get(planet, {}).get('longitude', 0)
        
        # Check conjunction (within orb)
        orb = rule.get('orb_settings', {}).get('conjunction', 3.0)
        if abs(natal_pos - transit_pos) <= orb or abs(natal_pos - transit_pos) >= (360 - orb):
            triggers.append(f"Transit {planet} conjunct natal {planet}")
        
        return triggers
    
    def _calculate_dashas(self, birth_chart: Dict, event_date: str) -> Dict[str, str]:
        # Simplified dasha calculation - would need full implementation
        return {
            "maha": "Saturn",
            "antar": "Mars", 
            "pratyantar": "Jupiter",
            "sookshma": None,
            "prana": None
        }
    
    def _get_dasha_weight(self, dasha_level: str) -> int:
        weights = {
            "maha": 30,
            "antar": 25, 
            "pratyantar": 20,
            "sookshma": 15,
            "prana": 10
        }
        return weights.get(dasha_level, 10)
    
    def _compile_analysis(self, event_type: str, event_date: str, karaka_factors: List, 
                         dasha_factors: List, transit_factors: List, rule) -> EventAnalysis:
        
        total_weight = sum(f.weight for f in karaka_factors + dasha_factors + transit_factors)
        confidence = min(95, max(30, total_weight))
        
        classical_ref = rule.get('classical_references', ['Classical principles support this analysis'])[0]
        
        explanation = self._generate_explanation(karaka_factors, dasha_factors, transit_factors)
        
        return EventAnalysis(
            event_type=event_type,
            event_date=event_date,
            primary_factors=karaka_factors,
            dasha_activations=dasha_factors,
            transit_confirmations=transit_factors,
            total_confidence=confidence,
            classical_support=classical_ref,
            detailed_explanation=explanation
        )
    
    def _generate_explanation(self, karaka_factors: List, dasha_factors: List, transit_factors: List) -> str:
        explanation_parts = []
        
        if karaka_factors:
            explanation_parts.append("Primary astrological factors: " + 
                                   ", ".join(f.description for f in karaka_factors))
        
        if dasha_factors:
            explanation_parts.append("Dasha activation: " + 
                                   ", ".join(f.description for f in dasha_factors))
        
        if transit_factors:
            explanation_parts.append("Transit confirmation: " + 
                                   ", ".join(f.description for f in transit_factors))
        
        return ". ".join(explanation_parts) + "."
    
    def _get_house_lord(self, house_num: int, birth_chart: Dict) -> str:
        """Get the lord of a house based on its sign"""
        house_sign = (int(birth_chart['ascendant'] / 30) + house_num - 1) % 12
        
        # Sign lordships
        lords = {
            0: 'Mars',    # Aries
            1: 'Venus',   # Taurus  
            2: 'Mercury', # Gemini
            3: 'Moon',    # Cancer
            4: 'Sun',     # Leo
            5: 'Mercury', # Virgo
            6: 'Venus',   # Libra
            7: 'Mars',    # Scorpio
            8: 'Jupiter', # Sagittarius
            9: 'Saturn',  # Capricorn
            10: 'Saturn', # Aquarius
            11: 'Jupiter' # Pisces
        }
        
        return lords.get(house_sign, 'Unknown')
    
    def _create_empty_analysis(self, event_type: str, event_date: str) -> EventAnalysis:
        return EventAnalysis(
            event_type=event_type,
            event_date=event_date,
            primary_factors=[],
            dasha_activations=[],
            transit_confirmations=[],
            total_confidence=0,
            classical_support="No rule found for this event type",
            detailed_explanation="Analysis not available for this event type"
        )