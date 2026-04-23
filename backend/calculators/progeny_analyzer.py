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
        fertility_sphuta = self._calculate_sphuta()
        d1_fifth_house = self._analyze_d1_fifth_house()
        d7_analysis = self._analyze_d7_chart()
        jupiter_status = self._analyze_jupiter()
        timing_indicators = self._get_timing_indicators()

        return {
            "fertility_sphuta": fertility_sphuta,
            "d1_fifth_house": d1_fifth_house,
            "d7_analysis": d7_analysis,
            "jupiter_status": jupiter_status,
            "timing_indicators": timing_indicators,
            "progeny_evidence": self._build_progeny_evidence(
                fertility_sphuta,
                d1_fifth_house,
                d7_analysis,
                jupiter_status,
                timing_indicators,
            ),
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
            confidence = "supportive"
        else:
            strength = "Moderate (Neutral)"
            desc = "The fertility point is in a neutral sign polarity."
            confidence = "mixed"
            
        return {
            "type": name,
            "longitude": total_lon,
            "sign": self.get_sign_name(sign_index),
            "is_odd_sign": is_odd_sign,
            "strength": strength,
            "confidence": confidence,
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
        ninth_sign = (asc_sign + 8) % 12
        ninth_lord = self.SIGN_LORDS[ninth_sign]
        second_sign = (asc_sign + 1) % 12
        second_lord = self.SIGN_LORDS[second_sign]
        
        # 3. Planets in D7 5th House
        planets_in_5th = []
        planets_in_2nd = []
        planets_in_9th = []
        for p, data in self.d7_chart['planets'].items():
            p_sign = data['sign']
            if p_sign == fifth_sign:
                planets_in_5th.append(p)
            if p_sign == second_sign:
                planets_in_2nd.append(p)
            if p_sign == ninth_sign:
                planets_in_9th.append(p)

        supportive_planets = [p for p in planets_in_5th + planets_in_2nd + planets_in_9th if p in ['Jupiter', 'Venus', 'Moon', 'Mercury']]
        challenging_planets = [p for p in planets_in_5th if p in ['Saturn', 'Rahu', 'Ketu', 'Mars']]
                
        return {
            "d7_ascendant": self.get_sign_name(asc_sign),
            "d7_lagna_lord": lagna_lord,
            "d7_fifth_house_sign": self.get_sign_name(fifth_sign),
            "d7_fifth_lord": fifth_lord,
            "d7_ninth_house_sign": self.get_sign_name(ninth_sign),
            "d7_ninth_lord": ninth_lord,
            "d7_second_house_sign": self.get_sign_name(second_sign),
            "d7_second_lord": second_lord,
            "planets_in_d7_5th": planets_in_5th,
            "planets_in_d7_2nd": planets_in_2nd,
            "planets_in_d7_9th": planets_in_9th,
            "supportive_planets": supportive_planets,
            "challenging_planets": challenging_planets,
            "support_level": self._calculate_d7_support_level(planets_in_5th, supportive_planets, challenging_planets),
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
            "strength": "Strong" if not jup.get('retrograde') else "Mixed (Retrograde)",
            "status": "Supportive" if jup.get('house', 1) in [1, 4, 5, 7, 9, 10] and not jup.get('retrograde') else "Mixed"
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

    def _calculate_d7_support_level(self, planets_in_5th: List[str], supportive_planets: List[str], challenging_planets: List[str]) -> str:
        if supportive_planets and not challenging_planets:
            return "Strong"
        if challenging_planets and not supportive_planets:
            return "Delayed"
        if planets_in_5th or supportive_planets or challenging_planets:
            return "Mixed"
        return "Neutral"

    def _calculate_promise_strength(self, fertility_sphuta: Dict[str, Any], d1_fifth_house: Dict[str, Any], d7_analysis: Dict[str, Any], jupiter_status: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        notes: List[str] = []

        if fertility_sphuta.get("confidence") == "supportive":
            score += 1
            notes.append("Fertility point is in favorable polarity.")
        else:
            notes.append("Fertility point is mixed and should be read with context.")

        if d1_fifth_house.get("planets"):
            score += 1
            notes.append("D1 5th house is activated.")
        if d1_fifth_house.get("has_malefics"):
            score -= 1
            notes.append("D1 5th house has malefic pressure.")

        if d7_analysis.get("support_level") == "Strong":
            score += 2
            notes.append("D7 shows strong child-supportive signatures.")
        elif d7_analysis.get("support_level") == "Delayed":
            score -= 1
            notes.append("D7 shows delay or effort signatures.")
        elif d7_analysis.get("support_level") == "Mixed":
            score += 0
            notes.append("D7 is mixed and needs timing support.")

        if jupiter_status.get("status") == "Supportive":
            score += 1
            notes.append("Jupiter is supportive.")
        elif jupiter_status.get("strength") == "Mixed (Retrograde)":
            notes.append("Jupiter is mixed due to retrograde motion.")

        if score >= 4:
            rating = "Strong"
        elif score >= 2:
            rating = "Moderate"
        else:
            rating = "Sensitive"

        return {
            "score": score,
            "rating": rating,
            "notes": notes,
        }

    def _build_progeny_evidence(
        self,
        fertility_sphuta: Dict[str, Any],
        d1_fifth_house: Dict[str, Any],
        d7_analysis: Dict[str, Any],
        jupiter_status: Dict[str, Any],
        timing_indicators: List[str],
    ) -> Dict[str, Any]:
        return {
            "promise": self._calculate_promise_strength(fertility_sphuta, d1_fifth_house, d7_analysis, jupiter_status),
            "static_promise": {
                "d1_5th": d1_fifth_house,
                "d7": d7_analysis,
                "jupiter": jupiter_status,
                "fertility_sphuta": fertility_sphuta,
            },
            "timing_indicators": timing_indicators,
            "focus_guidance": {
                "first_child": "Read for core child promise and favorable conception windows.",
                "next_child": "Read for next-child timing only; avoid re-framing as first-child potential.",
                "parenting": "Read for parenting style, child relationship themes, and support periods; do not predict conception timing.",
            },
            "safety_rules": [
                "Supportive guidance only, not medical diagnosis.",
                "Do not present conception timing as certainty.",
                "If existing children are present, separate parenting guidance from conception timing.",
            ],
        }

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
