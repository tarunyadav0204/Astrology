"""
Kalchakra Dasha Calculator
Implements the Kalchakra (Time-Wheel) dasha system based on Moon's nakshatra and pada
"""

import swisseph as swe
from datetime import datetime, timedelta
from typing import Dict, Any, List
from utils.timezone_service import parse_timezone_offset

class KalachakraDashaCalculator:
    """Calculate Kalchakra Dasha periods"""
    
    def __init__(self, chart_data=None):
        self.chart_data = chart_data
        
        # BPHS Nakshatra Lords (correct classical mapping)
        self.NAKSHATRA_LORDS = {
            1: 'Ketu', 2: 'Venus', 3: 'Sun', 4: 'Moon', 5: 'Mars', 6: 'Rahu', 7: 'Jupiter', 8: 'Saturn', 9: 'Mercury',
            10: 'Ketu', 11: 'Venus', 12: 'Sun', 13: 'Moon', 14: 'Mars', 15: 'Rahu', 16: 'Jupiter', 17: 'Saturn', 18: 'Mercury',
            19: 'Ketu', 20: 'Venus', 21: 'Sun', 22: 'Moon', 23: 'Mars', 24: 'Rahu', 25: 'Jupiter', 26: 'Saturn', 27: 'Mercury'
        }
        
        # Simplified pada mapping for quick reference
        self.PADA_TO_PLANET = {
            # Ashwini (1)
            (1, 1): 'Sun', (1, 2): 'Moon', (1, 3): 'Mars', (1, 4): 'Mercury',
            # Bharani (2)
            (2, 1): 'Jupiter', (2, 2): 'Venus', (2, 3): 'Saturn', (2, 4): 'Rahu',
            # Krittika (3)
            (3, 1): 'Ketu', (3, 2): 'Sun', (3, 3): 'Moon', (3, 4): 'Mars',
            # Rohini (4)
            (4, 1): 'Mercury', (4, 2): 'Jupiter', (4, 3): 'Venus', (4, 4): 'Saturn',
            # Mrigashira (5)
            (5, 1): 'Rahu', (5, 2): 'Ketu', (5, 3): 'Sun', (5, 4): 'Moon',
            # Ardra (6)
            (6, 1): 'Mars', (6, 2): 'Mercury', (6, 3): 'Jupiter', (6, 4): 'Venus',
            # Punarvasu (7)
            (7, 1): 'Saturn', (7, 2): 'Rahu', (7, 3): 'Ketu', (7, 4): 'Sun',
            # Pushya (8)
            (8, 1): 'Moon', (8, 2): 'Mars', (8, 3): 'Mercury', (8, 4): 'Jupiter',
            # Ashlesha (9)
            (9, 1): 'Venus', (9, 2): 'Saturn', (9, 3): 'Rahu', (9, 4): 'Ketu',
            # Magha (10)
            (10, 1): 'Sun', (10, 2): 'Moon', (10, 3): 'Mars', (10, 4): 'Mercury',
            # Purva Phalguni (11)
            (11, 1): 'Jupiter', (11, 2): 'Venus', (11, 3): 'Saturn', (11, 4): 'Rahu',
            # Uttara Phalguni (12)
            (12, 1): 'Ketu', (12, 2): 'Sun', (12, 3): 'Moon', (12, 4): 'Mars',
            # Hasta (13)
            (13, 1): 'Mercury', (13, 2): 'Jupiter', (13, 3): 'Venus', (13, 4): 'Saturn',
            # Chitra (14)
            (14, 1): 'Rahu', (14, 2): 'Ketu', (14, 3): 'Sun', (14, 4): 'Moon',
            # Swati (15)
            (15, 1): 'Mars', (15, 2): 'Mercury', (15, 3): 'Jupiter', (15, 4): 'Venus',
            # Vishakha (16)
            (16, 1): 'Saturn', (16, 2): 'Rahu', (16, 3): 'Ketu', (16, 4): 'Sun',
            # Anuradha (17)
            (17, 1): 'Moon', (17, 2): 'Mars', (17, 3): 'Mercury', (17, 4): 'Jupiter',
            # Jyeshtha (18)
            (18, 1): 'Venus', (18, 2): 'Saturn', (18, 3): 'Rahu', (18, 4): 'Ketu',
            # Mula (19)
            (19, 1): 'Ketu', (19, 2): 'Venus', (19, 3): 'Saturn', (19, 4): 'Rahu',
            # Purva Ashadha (20)
            (20, 1): 'Jupiter', (20, 2): 'Mercury', (20, 3): 'Mars', (20, 4): 'Moon',
            # Uttara Ashadha (21)
            (21, 1): 'Sun', (21, 2): 'Ketu', (21, 3): 'Venus', (21, 4): 'Saturn',
            # Shravana (22)
            (22, 1): 'Rahu', (22, 2): 'Jupiter', (22, 3): 'Mercury', (22, 4): 'Mars',
            # Dhanishta (23)
            (23, 1): 'Moon', (23, 2): 'Sun', (23, 3): 'Ketu', (23, 4): 'Venus',
            # Shatabhisha (24)
            (24, 1): 'Saturn', (24, 2): 'Rahu', (24, 3): 'Jupiter', (24, 4): 'Mercury',
            # Purva Bhadrapada (25)
            (25, 1): 'Mars', (25, 2): 'Moon', (25, 3): 'Sun', (25, 4): 'Ketu',
            # Uttara Bhadrapada (26)
            (26, 1): 'Venus', (26, 2): 'Saturn', (26, 3): 'Rahu', (26, 4): 'Jupiter',
            # Revati (27)
            (27, 1): 'Mercury', (27, 2): 'Mars', (27, 3): 'Moon', (27, 4): 'Sun'
        }
        
        # Kalchakra dasha years (different from Vimshottari)
        self.KALCHAKRA_YEARS = {
            'Sun': 6, 'Moon': 10, 'Mars': 7, 'Mercury': 17,
            'Jupiter': 16, 'Venus': 20, 'Saturn': 19, 'Rahu': 18, 'Ketu': 7
        }
        
        # Nakshatra deity classification (BPHS)
        self.NAKSHATRA_DEITIES = {
            1: 'Deva', 2: 'Manushya', 3: 'Rakshasa', 4: 'Manushya', 5: 'Deva', 6: 'Manushya', 7: 'Deva', 8: 'Rakshasa', 9: 'Rakshasa',
            10: 'Rakshasa', 11: 'Manushya', 12: 'Manushya', 13: 'Deva', 14: 'Rakshasa', 15: 'Deva', 16: 'Rakshasa', 17: 'Deva', 18: 'Rakshasa',
            19: 'Rakshasa', 20: 'Manushya', 21: 'Manushya', 22: 'Deva', 23: 'Rakshasa', 24: 'Rakshasa', 25: 'Manushya', 26: 'Manushya', 27: 'Deva'
        }
        
        # Planet sequences
        self.FORWARD_SEQUENCE = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        self.BACKWARD_SEQUENCE = ['Ketu', 'Rahu', 'Saturn', 'Venus', 'Jupiter', 'Mercury', 'Mars', 'Moon', 'Sun']
    
    def calculate_kalchakra_dasha(self, birth_data: Dict, current_date: datetime = None) -> Dict[str, Any]:
        """Calculate current Kalchakra dasha periods"""
        if current_date is None:
            current_date = datetime.now()
        
        try:
            # Get Moon position
            moon_longitude = self._get_moon_position(birth_data)
            
            # Get nakshatra and pada
            nakshatra_info = self._get_nakshatra_info(moon_longitude)
            nakshatra_num = nakshatra_info['number']
            pada = nakshatra_info['pada']
            
            # Get starting planet using BPHS method (nakshatra lord)
            nakshatra_lord = self.NAKSHATRA_LORDS.get(nakshatra_num, 'Ketu')
            starting_planet = nakshatra_lord  # BPHS uses nakshatra lord as starting point
            
            # Determine sequence direction based on pada + deity (classical method)
            deity = self.NAKSHATRA_DEITIES.get(nakshatra_num, 'Deva')
            is_forward = self._get_classical_direction(pada, deity)
            sequence = self.FORWARD_SEQUENCE if is_forward else self.BACKWARD_SEQUENCE
            
            # Calculate elapsed portion in birth nakshatra
            elapsed_fraction = self._calculate_elapsed_fraction(moon_longitude, nakshatra_info)
            
            # Calculate all mahadashas
            birth_datetime = datetime.strptime(f"{birth_data['date']} {birth_data['time']}", "%Y-%m-%d %H:%M")
            maha_dashas = self._calculate_maha_dashas(starting_planet, sequence, elapsed_fraction, birth_datetime)
            
            # Find current mahadasha
            current_maha = self._find_current_period(maha_dashas, current_date)
            
            # Calculate current antardasha
            current_antar = self._calculate_antardasha(current_maha, sequence, current_date)
            
            return {
                'system': 'Kalchakra',
                'mahadasha': {'planet': current_maha['planet']},
                'antardasha': {'planet': current_antar['planet']},
                'moon_nakshatra': nakshatra_num,
                'moon_pada': pada,
                'starting_planet': starting_planet,
                'sequence_direction': 'Forward' if is_forward else 'Backward',
                'maha_dashas': maha_dashas,
                'cycle_length': sum(self.KALCHAKRA_YEARS.values())
            }
            
        except Exception as e:
            return {
                'system': 'Kalchakra',
                'mahadasha': {'planet': 'Sun'},
                'antardasha': {'planet': 'Moon'},
                'error': str(e)
            }
    
    def _get_moon_position(self, birth_data: Dict) -> float:
        """Get Moon's longitude using Swiss Ephemeris"""
        try:
            time_parts = birth_data['time'].split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60
            
            # Get timezone offset using centralized utility
            tz_offset = parse_timezone_offset(
                birth_data.get('timezone', ''),
                birth_data.get('latitude'),
                birth_data.get('longitude')
            )
            
            utc_hour = hour - tz_offset
            jd = swe.julday(
                int(birth_data['date'].split('-')[0]),
                int(birth_data['date'].split('-')[1]),
                int(birth_data['date'].split('-')[2]),
                utc_hour
            )
            
            # Set Lahiri Ayanamsa for accurate Vedic calculations

            
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            
            return swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
            
        except Exception:
            return 0.0
    
    def _get_nakshatra_info(self, longitude: float) -> Dict:
        """Get nakshatra information from longitude"""
        nakshatra_span = 360 / 27  # 13.333333°
        nakshatra_index = int(longitude / nakshatra_span)
        nakshatra_index = min(nakshatra_index, 26)
        
        degrees_in_nakshatra = longitude % nakshatra_span
        pada_span = nakshatra_span / 4
        pada = int(degrees_in_nakshatra / pada_span) + 1
        
        return {
            'number': nakshatra_index + 1,
            'pada': pada,
            'degrees_in_nakshatra': degrees_in_nakshatra,
            'nakshatra_span': nakshatra_span
        }
    
    def _calculate_elapsed_fraction(self, moon_longitude: float, nakshatra_info: Dict) -> float:
        """Calculate elapsed fraction in birth nakshatra"""
        degrees_in_nakshatra = nakshatra_info['degrees_in_nakshatra']
        nakshatra_span = nakshatra_info['nakshatra_span']
        return degrees_in_nakshatra / nakshatra_span
    
    def _calculate_maha_dashas(self, starting_planet: str, sequence: List[str], elapsed_fraction: float, birth_datetime: datetime) -> List[Dict]:
        """Calculate all mahadasha periods"""
        maha_dashas = []
        current_date = birth_datetime
        start_index = sequence.index(starting_planet)
        
        for i in range(9):
            planet = sequence[(start_index + i) % 9]
            
            if i == 0:
                # Balance of first dasha
                years = self.KALCHAKRA_YEARS[planet] * (1 - elapsed_fraction)
            else:
                years = self.KALCHAKRA_YEARS[planet]
            
            days = years * 365.25
            end_date = current_date + timedelta(days=days)
            
            maha_dashas.append({
                'planet': planet,
                'start': current_date,
                'end': end_date - timedelta(seconds=1),
                'years': round(years, 2)
            })
            
            current_date = end_date
        
        return maha_dashas
    
    def _find_current_period(self, periods: List[Dict], current_date: datetime) -> Dict:
        """Find current period from list"""
        for period in periods:
            if period['start'] <= current_date <= period['end']:
                return period
        return periods[0] if periods else {'planet': 'Sun', 'start': current_date, 'end': current_date}
    
    def _calculate_antardasha(self, maha_dasha: Dict, sequence: List[str], current_date: datetime) -> Dict:
        """Calculate current antardasha within mahadasha"""
        maha_planet = maha_dasha['planet']
        maha_start = maha_dasha['start']
        maha_duration = (maha_dasha['end'] - maha_dasha['start']).total_seconds() / (365.25 * 24 * 3600)
        
        start_index = sequence.index(maha_planet)
        current_antar_date = maha_start
        
        for i in range(9):
            antar_planet = sequence[(start_index + i) % 9]
            antar_years = (maha_duration * self.KALCHAKRA_YEARS[antar_planet]) / sum(self.KALCHAKRA_YEARS.values())
            antar_days = antar_years * 365.25
            antar_end = current_antar_date + timedelta(days=antar_days)
            
            if current_antar_date <= current_date <= antar_end:
                return {
                    'planet': antar_planet,
                    'start': current_antar_date,
                    'end': antar_end
                }
            
            current_antar_date = antar_end
        
        return {'planet': maha_planet, 'start': maha_start, 'end': maha_dasha['end']}
    
    def _get_classical_direction(self, pada: int, deity: str) -> bool:
        """Get direction based on classical BPHS rules"""
        # Classical rule: Deva = forward, Rakshasa = backward, Manushya = based on pada
        if deity == 'Deva':
            return True  # Forward
        elif deity == 'Rakshasa':
            return False  # Backward
        else:  # Manushya
            return pada in [1, 2]  # Forward for pada 1,2; Backward for pada 3,4
    
    def get_kalchakra_summary(self) -> Dict[str, Any]:
        """Get summary of Kalchakra dasha system"""
        return {
            'system_name': 'Kalchakra Dasha (Classical BPHS)',
            'total_combinations': 108,
            'cycle_length_years': sum(self.KALCHAKRA_YEARS.values()),
            'based_on': 'Moon nakshatra, pada, and deity classification',
            'direction_rule': 'Deva=Forward, Rakshasa=Backward, Manushya=Pada-based',
            'specialty': 'Jaimini karmic timing and spiritual evolution',
            'sub_periods': 'Has Antardasha and sub-sub-periods (classical)'
        }