from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Any

class CharaDashaCalculator:
    """
    STANDALONE CALCULATOR for Jaimini Chara Dasha.
    Does NOT modify existing chart data.
    Implements its own internal logic for Dual Lordship checks.
    """

    def __init__(self, chart_data: Dict[str, Any]):
        # We only READ the chart data. We do not modify it.
        self.chart = chart_data
        self.planets = chart_data.get('planets', {})
        self.ascendant_sign = int(chart_data.get('ascendant', 0) / 30)

    def calculate_dasha(self, dob_dt: datetime) -> Dict[str, Any]:
        """Generates the Chara Dasha sequence and timing."""
        dasha_order = self._get_dasha_sequence(self.ascendant_sign)
        dasha_periods = []
        start_date = dob_dt
        
        for sign_idx in dasha_order:
            years = self._calculate_dasha_length(sign_idx)
            end_date = start_date + relativedelta(years=years)
            
            dasha_periods.append({
                "sign_id": sign_idx,
                "sign_name": self._get_sign_name(sign_idx),
                "duration_years": years,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "is_current": start_date <= datetime.now() < end_date
            })
            start_date = end_date
            
        return {
            "system": "Jaimini Chara Dasha (K.N. Rao)",
            "periods": dasha_periods
        }

    # --- INTERNAL LOGIC (Safe & Isolated) ---
    
    def _get_dasha_sequence(self, asc_sign: int) -> List[int]:
        """
        K.N. Rao Sequence: 
        Aries, Leo, Virgo, Libra, Aquarius, Pisces run DIRECT.
        Taurus, Gemini, Cancer, Scorpio, Sagittarius, Capricorn run REVERSE.
        """
        direct_signs = {0, 4, 5, 6, 10, 11} 
        is_direct = asc_sign in direct_signs
        
        sequence = []
        current = asc_sign
        for _ in range(12):
            sequence.append(current)
            if is_direct:
                current = (current + 1) % 12
            else:
                current = (current - 1 + 12) % 12
        return sequence

    def _calculate_dasha_length(self, sign_idx: int) -> int:
        """Calculates years by counting from Sign to Lord."""
        lord_sign = self._get_lord_sign(sign_idx)
        
        # Counting Rule: Odd signs Forward, Even signs Backward
        # Note: sign_idx 0 (Aries) is Odd-footed. sign_idx 1 (Taurus) is Even-footed.
        is_forward_counting = (sign_idx % 2 == 0)

        count = 0
        if is_forward_counting:
            if lord_sign >= sign_idx: 
                count = lord_sign - sign_idx
            else: 
                count = (12 - sign_idx) + lord_sign
        else:
            if sign_idx >= lord_sign: 
                count = sign_idx - lord_sign
            else: 
                count = sign_idx + (12 - lord_sign)
            
        # FIX: 'count' here is already the number of years (Steps).
        # We only apply the 12-year rule if count is 0 (Lord in own sign).
        years = count
        if years == 0: 
            years = 12
        
        return years

    def _get_lord_sign(self, sign_idx: int) -> int:
        """Finds where the lord is sitting."""
        # Standard Lords mapping
        lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
            4: 'Sun', 5: 'Mercury', 6: 'Venus', 
            7: ['Mars', 'Ketu'], # Scorpio
            8: 'Jupiter', 9: 'Saturn', 
            10: ['Saturn', 'Rahu'], # Aquarius
            11: 'Jupiter'
        }
        
        lord_data = lords[sign_idx]
        
        if isinstance(lord_data, str):
            return self._get_planet_sign(lord_data)
            
        # DUAL LORDSHIP LOGIC (Internal)
        return self._resolve_dual_lordship(lord_data[0], lord_data[1])

    def _resolve_dual_lordship(self, p1_name: str, p2_name: str) -> int:
        """
        Decides stronger lord for Scorpio/Aquarius.
        Logic: More Planets > Exalted > Higher Degree
        """
        p1_sign = self._get_planet_sign(p1_name)
        p2_sign = self._get_planet_sign(p2_name)
        
        # 1. Association Count
        p1_count = self._count_planets_in_sign(p1_sign)
        p2_count = self._count_planets_in_sign(p2_sign)
        
        if p1_count > p2_count: return p1_sign
        if p2_count > p1_count: return p2_sign
        
        # 2. Degrees (Tie-breaker)
        p1_deg = self.planets.get(p1_name, {}).get('degree', 0)
        p2_deg = self.planets.get(p2_name, {}).get('degree', 0)
        
        return p1_sign if p1_deg >= p2_deg else p2_sign

    # --- HELPERS ---
    def _get_planet_sign(self, pname: str) -> int:
        return self.planets.get(pname, {}).get('sign', 0)
        
    def _count_planets_in_sign(self, sign_idx: int) -> int:
        count = 0
        for p in self.planets.values():
            if p.get('sign') == sign_idx: count += 1
        return count

    def _get_sign_name(self, idx: int) -> str:
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[idx]
