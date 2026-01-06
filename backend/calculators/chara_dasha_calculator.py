from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Any
import pytz

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
        """Generates the Chara Dasha sequence and timing with antardashas."""
        dasha_order = self._get_dasha_sequence(self.ascendant_sign, is_mahadasha=True)
        dasha_periods = []
        start_date = dob_dt
        
        # FIX: Get 'now' in the SAME timezone as dob_dt
        current_time = self._get_current_datetime(dob_dt)
        
        for sign_idx in dasha_order:
            years = self._calculate_dasha_length(sign_idx)
            end_date = start_date + relativedelta(years=years)
            
            is_current = start_date <= current_time < end_date
            
            # Calculate antardashas for current mahadasha
            antardashas = []
            if is_current:
                antardashas = self._calculate_antardashas(sign_idx, years, start_date, current_time)
            
            dasha_periods.append({
                "sign_id": sign_idx,
                "sign_name": self._get_sign_name(sign_idx),
                "duration_years": years,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "is_current": is_current,
                "antardashas": antardashas
            })
            start_date = end_date
            
        return {
            "system": "Jaimini Chara Dasha (K.N. Rao)",
            "periods": dasha_periods
        }

    # --- INTERNAL LOGIC (Safe & Isolated) ---
    
    def _get_dasha_sequence(self, start_sign: int, is_mahadasha: bool = True) -> List[int]:
        """
        K.N. Rao Sequence Logic:
        - For MD: Direction depends on the ASCENDANT.
        - For AD: Direction depends on the Mahadasha sign (start_sign).
        """
        direct_signs = {0, 4, 5, 6, 10, 11}  # Ar, Le, Vi, Li, Aq, Pi
        
        # FIX: Dynamically determine direction based on context
        target_for_direction = self.ascendant_sign if is_mahadasha else start_sign
        is_direct = target_for_direction in direct_signs
        
        sequence = []
        current = start_sign
        
        if is_mahadasha:
            sequence.append(current)
            iterations = 11
        else:
            # For ADs, we skip the starting sign and move immediately to the next/prev
            iterations = 12
            
        for _ in range(iterations):
            if is_direct:
                current = (current + 1) % 12
            else:
                current = (current - 1 + 12) % 12
            sequence.append(current)
            
        return sequence

    def _calculate_dasha_length(self, sign_idx: int) -> int:
        """Calculates years by counting from Sign to Lord."""
        lord_sign = self._get_lord_sign(sign_idx)
        
        # K.N. Rao Method: Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius are Odd-footed (Forward)
        forward_counting_signs = {0, 1, 2, 6, 7, 8}
        is_forward_counting = sign_idx in forward_counting_signs

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
        K.N. Rao Rules:
        1. Exception: If one lord is in the sign itself, REJECT it. Use the other.
        2. Association: More planets conjoined > Stronger.
        3. Exaltation: Exalted planet > Non-exalted.
        4. Degrees: Higher longitude > Stronger.
        """
        p1_sign = self._get_planet_sign(p1_name)
        p2_sign = self._get_planet_sign(p2_name)
        
        # RULE 1: The "Lord in Sign" Exception (K.N. Rao)
        target_sign = 7 if p1_name == 'Mars' else 10
        
        if p1_sign == target_sign and p2_sign != target_sign:
            return p2_sign
        if p2_sign == target_sign and p1_sign != target_sign:
            return p1_sign
        
        # RULE 2: Association Count (Crowd Rule)
        p1_count = self._count_planets_in_sign(p1_sign)
        p2_count = self._count_planets_in_sign(p2_sign)
        
        if p1_count > p2_count: return p1_sign
        if p2_count > p1_count: return p2_sign
        
        # RULE 3: Exaltation Check
        p1_exalted = self._is_exalted(p1_name, p1_sign)
        p2_exalted = self._is_exalted(p2_name, p2_sign)
        
        if p1_exalted and not p2_exalted: return p1_sign
        if p2_exalted and not p1_exalted: return p2_sign
        
        # RULE 4: Degrees (Tie-breaker)
        p1_deg = self._normalize_degree(self.planets.get(p1_name, {}).get('degree', 0))
        p2_deg = self._normalize_degree(self.planets.get(p2_name, {}).get('degree', 0))
        
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
    
    def _is_exalted(self, planet: str, sign: int) -> bool:
        """Check if planet is exalted in given sign."""
        exaltations = {
            'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
            'Jupiter': 3, 'Venus': 11, 'Saturn': 6, 'Rahu': 1, 'Ketu': 7
        }
        return exaltations.get(planet) == sign
    
    def _normalize_degree(self, degree: float) -> float:
        """Normalize degree to 0-30 range for sign-based calculations."""
        return degree % 30
    
    def _get_current_datetime(self, reference_dt: datetime) -> datetime:
        """Get current datetime matching the timezone of the reference."""
        now = datetime.now()
        if reference_dt.tzinfo:
            # If input has timezone, convert 'now' to that timezone
            return datetime.now(reference_dt.tzinfo)
        else:
            # If input is naive, ensure 'now' is naive
            return now.replace(tzinfo=None)

    
    def _calculate_antardashas(self, maha_sign_id: int, total_years: int, start_date: datetime, current_time: datetime) -> List[Dict]:
        """
        Calculates 12 equal antardasha sub-periods for a mahadasha.
        In Jaimini, each AD is exactly 1/12th of the MD.
        """
        antardashas = []
        
        # Get the sequence starting from the NEXT sign after maha (not maha itself)
        sequence = self._get_dasha_sequence(maha_sign_id, is_mahadasha=False)
        
        # Each antardasha is exactly 1/12th of the mahadasha
        # Duration in months = total_years (e.g., 9-year MD = 9-month ADs)
        ad_months = total_years
        
        current_period_start = start_date
        
        for sign_id in sequence:
            end_date = current_period_start + relativedelta(months=ad_months)
            
            antardashas.append({
                "sign_id": sign_id,
                "sign_name": self._get_sign_name(sign_id),
                "start_date": current_period_start.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "months": ad_months,
                "years": round(ad_months / 12, 2),
                "is_current": current_period_start <= current_time < end_date
            })
            
            current_period_start = end_date
        
        return antardashas
