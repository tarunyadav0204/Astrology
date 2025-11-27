from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base_calculator import BaseCalculator

class ShoolaDashaCalculator(BaseCalculator):
    """
    Calculates Jaimini Shoola Dasha (Niryana Shoola Dasha).
    Used specifically for longevity and death timing.
    """
    
    def __init__(self, chart_data: Dict):
        self.chart_data = chart_data
        self.ascendant_sign = int(chart_data['ascendant'] / 30)
        self.planets = chart_data['planets']
        
        self.sign_names = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        # Sign Lords (0=Mars, 1=Venus...) - Uses traditional single lordship
        # Note: Scorpio(7)=Mars, Aquarius(10)=Saturn (no Rahu/Ketu co-lordship for MVP)
        self.sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        # Exaltation Signs for Strength Check
        self.exaltation_signs = {
            'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6
        }

    def calculate_shoola_dasha(self, birth_details: Dict, relative_house_idx: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate Shoola Dasha.
        :param relative_house_idx: If provided (e.g., 3 for Mother's 4th house), 
                                   calculates Shoola for that relative.
                                   Default is None (Native's Lagna).
        """
        
        # 1. Determine Reference Sign (Lagna or Relative's House)
        if relative_house_idx is not None:
            base_sign = (self.ascendant_sign + relative_house_idx) % 12
        else:
            base_sign = self.ascendant_sign
            
        # 2. Determine Start Sign (Stronger of Base vs 7th from Base)
        start_sign_idx = self._determine_stronger_sign(base_sign, (base_sign + 6) % 12)
        
        # 3. Determine Direction (Odd = Forward, Even = Backward)
        is_forward = (start_sign_idx + 1) % 2 != 0
        
        # 4. Generate Periods
        birth_date = datetime.strptime(birth_details['date'], "%Y-%m-%d")
        current_date = datetime.now()
        
        periods = []
        start_time = birth_date
        current_period_info = None
        
        # 108 Years Cycle
        for i in range(12):
            if is_forward:
                current_sign_idx = (start_sign_idx + i) % 12
            else:
                current_sign_idx = (start_sign_idx - i + 12) % 12
                
            end_time = start_time + timedelta(days=9*365.25)
            
            dasha_entry = {
                "sign_id": current_sign_idx,
                "sign_name": self.sign_names[current_sign_idx],
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d"),
                "order": i + 1
            }
            
            periods.append(dasha_entry)
            
            if start_time <= current_date < end_time:
                current_period_info = dasha_entry
                
            start_time = end_time

        return {
            "type": "Matri Shoola" if relative_house_idx == 3 else "Shoola Dasha",
            "start_sign": self.sign_names[start_sign_idx],
            "direction": "Forward" if is_forward else "Backward",
            "current_period": current_period_info,
            "all_periods": periods
        }

    def _determine_stronger_sign(self, sign1_idx: int, sign2_idx: int) -> int:
        """
        Jaimini Strength Rules (Prakanti):
        1. More Planets.
        2. Status of Lord (Exalted/Moolatrikona).
        3. Natural Zodiac Strength (Dual > Fixed > Movable).
        """
        # Rule 1: Planet Count
        count1 = self._count_planets_in_sign(sign1_idx)
        count2 = self._count_planets_in_sign(sign2_idx)
        
        if count1 > count2: return sign1_idx
        if count2 > count1: return sign2_idx
        
        # Rule 2: Lord Strength (Simplified Exaltation Check)
        lord1 = self.sign_lords[sign1_idx]
        lord2 = self.sign_lords[sign2_idx]
        
        score1 = self._get_lord_strength_score(lord1, sign1_idx)
        score2 = self._get_lord_strength_score(lord2, sign2_idx)
        
        if score1 > score2: return sign1_idx
        if score2 > score1: return sign2_idx
        
        # Rule 3: Natural Zodiac Strength (Dual > Fixed > Movable)
        # Verified: Aries(0)%3=0(Movable), Taurus(1)%3=1(Fixed), Gemini(2)%3=2(Dual)
        type1 = sign1_idx % 3
        type2 = sign2_idx % 3
        if type1 > type2: return sign1_idx  # Dual(2) > Fixed(1) > Movable(0)
        if type2 > type1: return sign2_idx
        
        # Fallback
        return sign1_idx

    def _count_planets_in_sign(self, sign_idx: int) -> int:
        count = 0
        for planet, data in self.planets.items():
            if planet in ['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna']:
                continue
            if data['sign'] == sign_idx:
                count += 1
        return count

    def _get_lord_strength_score(self, planet_name: str, sign_idx: int) -> int:
        """Helper to check basic dignity of a sign's lord"""
        if planet_name not in self.planets: return 0
        
        p_data = self.planets[planet_name]
        p_sign = p_data['sign']
        
        score = 0
        if p_sign == sign_idx: score += 5  # Own Sign
        if p_sign == self.exaltation_signs.get(planet_name): score += 4  # Exalted
        
        return score