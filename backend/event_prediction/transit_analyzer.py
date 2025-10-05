import swisseph as swe
from datetime import datetime, timedelta
from .house_significations import SIGN_LORDS
from .config import PLANET_SPEEDS, PLANET_NUMBERS, TRANSIT_PLANETS, CONJUNCTION_STRENGTHS, OPPOSITION_STRENGTHS, SPECIAL_ASPECT_STRENGTHS

class TransitAnalyzer:
    """Analyzes transit activations for event timing"""
    
    def __init__(self, birth_data, chart_data):
        self.birth_data = birth_data
        self.chart_data = chart_data
        
    def find_transit_activations(self, relevant_planets, start_year, end_year):
        """Find when transiting planets activate natal positions"""
        activations = []
        
        for year in range(start_year, end_year + 1):
            # Check all planet transits
            for transit_planet in TRANSIT_PLANETS:
                planet_activations = self._find_planet_transits(transit_planet, relevant_planets, year)
                activations.extend(planet_activations)
        
        return sorted(activations, key=lambda x: x['date'])
    
    def _find_planet_transits(self, transit_planet, relevant_planets, year):
        """Find transits for any planet over relevant planets"""
        activations = []
        
        # Check frequency based on speed
        check_months = 12 if PLANET_SPEEDS[transit_planet] >= 1 else 1
        
        for month in range(1, 13, max(1, 12 // check_months)):
            jd = swe.julday(year, month, 15, 12.0)
            
            # Get transit planet position
            if transit_planet in PLANET_NUMBERS:
                planet_num = PLANET_NUMBERS[transit_planet]
                transit_pos = swe.calc_ut(jd, planet_num, swe.FLG_SIDEREAL)[0][0]
            else:  # Rahu/Ketu
                node_pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
                transit_pos = node_pos if transit_planet == 'Rahu' else (node_pos + 180) % 360
            
            transit_sign = int(transit_pos / 30)
            
            # Check aspects to relevant planets
            for natal_planet in relevant_planets:
                if natal_planet in self.chart_data['planets']:
                    natal_sign = self.chart_data['planets'][natal_planet]['sign']
                    aspects = self._get_planet_aspects(transit_planet, transit_sign, natal_sign)
                    
                    for aspect in aspects:
                        activations.append({
                            'date': datetime(year, month, 15),
                            'type': f'{transit_planet.lower()}_{aspect["type"]}',
                            'planet': natal_planet,
                            'strength': aspect['strength'],
                            'description': f'{transit_planet} {aspect["type"]} natal {natal_planet}'
                        })
        
        return activations
    
    def _get_planet_aspects(self, planet, transit_sign, natal_sign):
        """Get aspects for a planet with proper strengths"""
        aspects = []
        
        # Conjunction (same sign)
        if transit_sign == natal_sign:
            strength = CONJUNCTION_STRENGTHS[planet]
            aspects.append({'type': 'conjunction', 'strength': strength})
        
        # 7th aspect (opposition) - all planets
        elif (transit_sign + 6) % 12 == natal_sign:
            strength = OPPOSITION_STRENGTHS[planet]
            aspects.append({'type': 'opposition', 'strength': strength})
        
        # Special aspects
        if planet in SPECIAL_ASPECT_STRENGTHS:
            planet_aspects = SPECIAL_ASPECT_STRENGTHS[planet]
            
            if planet == 'Mars':
                if (transit_sign + 3) % 12 == natal_sign:
                    aspects.append({'type': '4th_aspect', 'strength': planet_aspects['4th_aspect']})
                elif (transit_sign + 7) % 12 == natal_sign:
                    aspects.append({'type': '8th_aspect', 'strength': planet_aspects['8th_aspect']})
            
            elif planet == 'Jupiter':
                if (transit_sign + 4) % 12 == natal_sign:
                    aspects.append({'type': '5th_aspect', 'strength': planet_aspects['5th_aspect']})
                elif (transit_sign + 8) % 12 == natal_sign:
                    aspects.append({'type': '9th_aspect', 'strength': planet_aspects['9th_aspect']})
            
            elif planet == 'Saturn':
                if (transit_sign + 2) % 12 == natal_sign:
                    aspects.append({'type': '3rd_aspect', 'strength': planet_aspects['3rd_aspect']})
                elif (transit_sign + 9) % 12 == natal_sign:
                    aspects.append({'type': '10th_aspect', 'strength': planet_aspects['10th_aspect']})
            
            elif planet in ['Rahu', 'Ketu']:
                if (transit_sign + 2) % 12 == natal_sign:
                    aspects.append({'type': '3rd_aspect', 'strength': planet_aspects['3rd_aspect']})
                elif (transit_sign + 10) % 12 == natal_sign:
                    aspects.append({'type': '11th_aspect', 'strength': planet_aspects['11th_aspect']})
        
        return aspects
    
