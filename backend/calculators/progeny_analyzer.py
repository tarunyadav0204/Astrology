from typing import Dict, Any, List
from .base_calculator import BaseCalculator
from .divisional_chart_calculator import DivisionalChartCalculator

class ProgenyAnalyzer(BaseCalculator):
    """
    Specialized analyzer for Children & Progeny (Santana).
    Combines D1, D7 (Saptamsa), and Fertility Sphutas.
    """
    
    def __init__(self, chart_data: Dict, birth_data: Dict):
        super().__init__(chart_data)
        self.gender = birth_data.get('gender', 'female').lower()
        self.d7_chart = self._get_d7_chart()
        
    def _get_d7_chart(self):
        """Calculate D7 chart using the validated calculator"""
        calc = DivisionalChartCalculator(self.chart_data)
        return calc.calculate_divisional_chart(7)['divisional_chart']

    def analyze_progeny(self) -> Dict[str, Any]:
        return {
            "fertility_sphuta": self._calculate_sphuta(),
            "d1_fifth_house": self._analyze_d1_fifth_house(),
            "d7_analysis": self._analyze_d7_chart(),
            "jupiter_status": self._analyze_jupiter(),
            "timing_indicators": self._get_timing_indicators()
        }

    def _calculate_sphuta(self) -> Dict[str, Any]:
        """
        Calculates Beeja Sphuta (Seed) for Men or Kshetra Sphuta (Field) for Women.
        Rule: Sum of longitudes of specific planets.
        """
        planets = self.chart_data['planets']
        
        def get_lon(p): return planets.get(p, {}).get('longitude', 0)
        
        if self.gender == 'male':
            # Beeja Sphuta = Sun + Venus + Jupiter
            total_lon = (get_lon('Sun') + get_lon('Venus') + get_lon('Jupiter')) % 360
            name = "Beeja Sphuta (Seed)"
            target_odd = True # Men need Odd signs (Yang/Active)
        else:
            # Kshetra Sphuta = Mars + Moon + Jupiter
            total_lon = (get_lon('Mars') + get_lon('Moon') + get_lon('Jupiter')) % 360
            name = "Kshetra Sphuta (Field)"
            target_odd = False # Women need Even signs (Yin/Receptive)
            
        sign_index = int(total_lon / 30)
        is_odd_sign = (sign_index % 2 == 0) # 0=Aries(Odd), 1=Taurus(Even)
        
        # Determine Strength
        if is_odd_sign == target_odd:
            strength = "Strong (Favorable)"
            desc = "The fertility point is in a favorable sign polarity."
        else:
            strength = "Moderate (Neutral)"
            desc = "The fertility point is in a neutral sign polarity."
            
        return {
            "type": name,
            "longitude": total_lon,
            "sign": self.get_sign_name(sign_index),
            "is_odd_sign": is_odd_sign,
            "strength": strength,
            "description": desc
        }

    def _analyze_d7_chart(self) -> Dict[str, Any]:
        """Deep analysis of Saptamsa (D7)"""
        asc_sign = int(self.d7_chart['ascendant'] / 30)
        
        # 1. D7 Lagna Lord
        lagna_lord = self.SIGN_LORDS[asc_sign]
        
        # 2. D7 5th House (Children)
        fifth_sign = (asc_sign + 4) % 12
        fifth_lord = self.SIGN_LORDS[fifth_sign]
        
        # 3. Planets in D7 5th House
        planets_in_5th = []
        for p, data in self.d7_chart['planets'].items():
            p_sign = data['sign']
            if p_sign == fifth_sign:
                planets_in_5th.append(p)
                
        return {
            "d7_ascendant": self.get_sign_name(asc_sign),
            "d7_lagna_lord": lagna_lord,
            "d7_fifth_house_sign": self.get_sign_name(fifth_sign),
            "d7_fifth_lord": fifth_lord,
            "planets_in_d7_5th": planets_in_5th,
            "summary": self._interpret_d7(planets_in_5th, fifth_lord)
        }

    def _analyze_d1_fifth_house(self) -> Dict[str, Any]:
        """Analyze root promise in Birth Chart"""
        asc_sign = int(self.chart_data['ascendant'] / 30)
        fifth_sign = (asc_sign + 4) % 12
        fifth_lord = self.SIGN_LORDS[fifth_sign]
        
        planets_in_5th = []
        for p, data in self.chart_data['planets'].items():
            if data.get('house') == 5:
                planets_in_5th.append(p)
                
        return {
            "sign": self.get_sign_name(fifth_sign),
            "lord": fifth_lord,
            "planets": planets_in_5th,
            "has_malefics": any(p in ['Saturn', 'Rahu', 'Ketu', 'Mars'] for p in planets_in_5th)
        }

    def _analyze_jupiter(self) -> Dict[str, Any]:
        """Analyze Jupiter (Putra Karaka)"""
        jup = self.chart_data['planets'].get('Jupiter', {})
        return {
            "sign": self.get_sign_name(jup.get('sign', 0)),
            "house": jup.get('house', 1),
            "retrograde": jup.get('retrograde', False),
            "strength": "Strong" if not jup.get('retrograde') else "Mixed (Retrograde)"
        }

    def _get_timing_indicators(self) -> List[str]:
        """Get planets that can give children during their dasha"""
        indicators = ["Jupiter"] # Natural Karaka
        
        # Add 5th Lord D1
        d1_asc = int(self.chart_data['ascendant'] / 30)
        indicators.append(self.SIGN_LORDS[(d1_asc + 4) % 12])
        
        # Add 5th Lord D7
        d7_asc = int(self.d7_chart['ascendant'] / 30)
        indicators.append(self.SIGN_LORDS[(d7_asc + 4) % 12])
        
        return list(set(indicators)) # Remove duplicates

    def _interpret_d7(self, planets_in_5th: List[str], fifth_lord: str) -> str:
        if not planets_in_5th:
            return f"5th House is empty. Outcome depends on lord {fifth_lord}."
        
        if 'Jupiter' in planets_in_5th or 'Venus' in planets_in_5th:
            return "Benefics in D7 5th house indicate happiness from children."
        elif 'Rahu' in planets_in_5th or 'Ketu' in planets_in_5th:
            return "Nodes in D7 5th house indicate unconventional birth (IVF/Surrogacy) or strong karmic bond."
        elif 'Saturn' in planets_in_5th:
            return "Saturn in D7 5th house may indicate delay but dutiful children."
        return "Mixed influences on progeny."