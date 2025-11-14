"""
Shared Dasha Calculator
Used by both main.py and classical engine to ensure consistent calculations
"""

import swisseph as swe
from datetime import datetime, timedelta
from typing import Dict, Any, List

class DashaCalculator:
    def __init__(self):
        # Dasha periods in years
        self.DASHA_PERIODS = {
            'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7,
            'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17
        }
        
        # Nakshatra lords
        self.NAKSHATRA_LORDS = [
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
            'Saturn', 'Mercury', 'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
            'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus',
            'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
        ]
        
        # Planet order for dasha sequence
        self.PLANET_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
    
    def calculate_current_dashas(self, birth_data: Dict, current_date: datetime = None) -> Dict[str, Any]:
        """Calculate current dasha periods using accurate Vimshottari method"""
        if current_date is None:
            current_date = datetime.now()
            
        try:
            # Calculate birth Julian Day
            time_parts = birth_data['time'].split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60
            
            # Handle timezone
            if 6.0 <= birth_data['latitude'] <= 37.0 and 68.0 <= birth_data['longitude'] <= 97.0:
                tz_offset = 5.5
            else:
                tz_offset = 0
                if birth_data.get('timezone', '').startswith('UTC'):
                    tz_str = birth_data['timezone'][3:]
                    if tz_str and ':' in tz_str:
                        sign = 1 if tz_str[0] == '+' else -1
                        parts = tz_str[1:].split(':')
                        tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
            
            utc_hour = hour - tz_offset
            jd = swe.julday(
                int(birth_data['date'].split('-')[0]),
                int(birth_data['date'].split('-')[1]),
                int(birth_data['date'].split('-')[2]),
                utc_hour
            )
            
            # Get Moon position
            moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
            
            # Calculate nakshatra and lord
            nakshatra_index = int(moon_pos / 13.333333333333334)
            moon_lord = self.NAKSHATRA_LORDS[nakshatra_index]
            
            # Calculate balance of first dasha
            nakshatra_start = nakshatra_index * 13.333333333333334
            elapsed_degrees = moon_pos - nakshatra_start
            balance_fraction = 1 - (elapsed_degrees / 13.333333333333334)
            
            birth_datetime = datetime.strptime(f"{birth_data['date']} {birth_data['time']}", "%Y-%m-%d %H:%M")
            
            # Calculate all mahadashas
            maha_dashas = []
            current_maha_date = birth_datetime
            start_index = self.PLANET_ORDER.index(moon_lord)
            
            for i in range(9):
                planet = self.PLANET_ORDER[(start_index + i) % 9]
                
                if i == 0:
                    # Balance of first dasha
                    years = self.DASHA_PERIODS[planet] * balance_fraction
                else:
                    years = self.DASHA_PERIODS[planet]
                
                days = years * 365.25
                end_date = current_maha_date + timedelta(days=days)
                
                maha_dashas.append({
                    'planet': planet,
                    'start': current_maha_date,
                    'end': end_date - timedelta(seconds=1),
                    'years': round(years, 2)
                })
                
                current_maha_date = end_date
            
            # Find current mahadasha
            current_maha = None
            for maha in maha_dashas:
                if maha['start'] <= current_date <= maha['end']:
                    current_maha = maha
                    break
            
            if not current_maha:
                # Default to first dasha if none found
                current_maha = maha_dashas[0] if maha_dashas else {'planet': moon_lord, 'start': birth_datetime, 'end': birth_datetime}
            
            # Calculate current antardasha
            current_antar = self._calculate_antardasha(current_maha, current_date)
            
            # Calculate current pratyantardasha
            current_pratyantar = self._calculate_pratyantardasha(current_maha, current_antar, current_date)
            
            # Calculate current sookshma
            current_sookshma = self._calculate_sookshma(current_maha, current_antar, current_pratyantar, current_date)
            
            # Calculate current prana
            current_prana = self._calculate_prana(current_maha, current_antar, current_pratyantar, current_sookshma, current_date)
            
            return {
                'mahadasha': {'planet': current_maha['planet']},
                'antardasha': {'planet': current_antar['planet']},
                'pratyantardasha': {'planet': current_pratyantar['planet']},
                'sookshma': {'planet': current_sookshma['planet']},
                'prana': {'planet': current_prana['planet']},
                'maha_dashas': maha_dashas,
                'moon_nakshatra': nakshatra_index + 1,
                'moon_lord': moon_lord
            }
            
        except Exception as e:
            # print(f"Error calculating dashas: {e}")
            return {
                'mahadasha': {'planet': 'Sun'},
                'antardasha': {'planet': 'Moon'},
                'pratyantardasha': {'planet': 'Mars'},
                'sookshma': {'planet': 'Mercury'},
                'prana': {'planet': 'Jupiter'}
            }
    
    def _calculate_antardasha(self, maha_dasha: Dict, current_date: datetime) -> Dict:
        """Calculate current antardasha within mahadasha"""
        maha_planet = maha_dasha['planet']
        maha_start = maha_dasha['start']
        maha_end = maha_dasha['end']
        
        start_index = self.PLANET_ORDER.index(maha_planet)
        current_antar_date = maha_start
        
        for i in range(9):
            antar_planet = self.PLANET_ORDER[(start_index + i) % 9]
            antar_period = (self.DASHA_PERIODS[maha_planet] * self.DASHA_PERIODS[antar_planet]) / 120
            antar_days = antar_period * 365.25
            antar_end = current_antar_date + timedelta(days=antar_days)
            
            if current_antar_date <= current_date <= antar_end:
                return {
                    'planet': antar_planet,
                    'start': current_antar_date,
                    'end': antar_end
                }
            
            current_antar_date = antar_end
        
        # Default to first antardasha
        return {'planet': maha_planet, 'start': maha_start, 'end': maha_end}
    
    def _calculate_pratyantardasha(self, maha_dasha: Dict, antar_dasha: Dict, current_date: datetime) -> Dict:
        """Calculate current pratyantardasha within antardasha"""
        maha_planet = maha_dasha['planet']
        antar_planet = antar_dasha['planet']
        antar_start = antar_dasha['start']
        antar_end = antar_dasha['end']
        
        start_index = self.PLANET_ORDER.index(antar_planet)
        current_pratyantar_date = antar_start
        
        antar_period = (self.DASHA_PERIODS[maha_planet] * self.DASHA_PERIODS[antar_planet]) / 120
        
        for i in range(9):
            pratyantar_planet = self.PLANET_ORDER[(start_index + i) % 9]
            pratyantar_period = (antar_period * self.DASHA_PERIODS[pratyantar_planet]) / 120
            pratyantar_days = pratyantar_period * 365.25
            pratyantar_end = current_pratyantar_date + timedelta(days=pratyantar_days)
            
            if current_pratyantar_date <= current_date <= pratyantar_end:
                return {
                    'planet': pratyantar_planet,
                    'start': current_pratyantar_date,
                    'end': pratyantar_end
                }
            
            current_pratyantar_date = pratyantar_end
        
        return {'planet': antar_planet, 'start': antar_start, 'end': antar_end}
    
    def _calculate_sookshma(self, maha_dasha: Dict, antar_dasha: Dict, pratyantar_dasha: Dict, current_date: datetime) -> Dict:
        """Calculate current sookshma within pratyantardasha"""
        maha_planet = maha_dasha['planet']
        antar_planet = antar_dasha['planet']
        pratyantar_planet = pratyantar_dasha['planet']
        pratyantar_start = pratyantar_dasha['start']
        pratyantar_end = pratyantar_dasha['end']
        
        start_index = self.PLANET_ORDER.index(pratyantar_planet)
        current_sookshma_date = pratyantar_start
        
        antar_period = (self.DASHA_PERIODS[maha_planet] * self.DASHA_PERIODS[antar_planet]) / 120
        pratyantar_period = (antar_period * self.DASHA_PERIODS[pratyantar_planet]) / 120
        
        for i in range(9):
            sookshma_planet = self.PLANET_ORDER[(start_index + i) % 9]
            sookshma_period = (pratyantar_period * self.DASHA_PERIODS[sookshma_planet]) / 120
            sookshma_days = sookshma_period * 365.25
            sookshma_end = current_sookshma_date + timedelta(days=sookshma_days)
            
            if current_sookshma_date <= current_date <= sookshma_end:
                return {
                    'planet': sookshma_planet,
                    'start': current_sookshma_date,
                    'end': sookshma_end
                }
            
            current_sookshma_date = sookshma_end
        
        return {'planet': pratyantar_planet, 'start': pratyantar_start, 'end': pratyantar_end}
    
    def _calculate_prana(self, maha_dasha: Dict, antar_dasha: Dict, pratyantar_dasha: Dict, sookshma_dasha: Dict, current_date: datetime) -> Dict:
        """Calculate current prana within sookshma"""
        maha_planet = maha_dasha['planet']
        antar_planet = antar_dasha['planet']
        pratyantar_planet = pratyantar_dasha['planet']
        sookshma_planet = sookshma_dasha['planet']
        sookshma_start = sookshma_dasha['start']
        sookshma_end = sookshma_dasha['end']
        
        start_index = self.PLANET_ORDER.index(sookshma_planet)
        current_prana_date = sookshma_start
        
        antar_period = (self.DASHA_PERIODS[maha_planet] * self.DASHA_PERIODS[antar_planet]) / 120
        pratyantar_period = (antar_period * self.DASHA_PERIODS[pratyantar_planet]) / 120
        sookshma_period = (pratyantar_period * self.DASHA_PERIODS[sookshma_planet]) / 120
        
        for i in range(9):
            prana_planet = self.PLANET_ORDER[(start_index + i) % 9]
            prana_period = (sookshma_period * self.DASHA_PERIODS[prana_planet]) / 120
            prana_days = prana_period * 365.25
            prana_end = current_prana_date + timedelta(days=prana_days)
            
            if current_prana_date <= current_date <= prana_end:
                return {
                    'planet': prana_planet,
                    'start': current_prana_date,
                    'end': prana_end
                }
            
            current_prana_date = prana_end
        
        return {'planet': sookshma_planet, 'start': sookshma_start, 'end': sookshma_end}
    
    def calculate_dashas_for_date(self, target_date: datetime, birth_data: Dict) -> Dict[str, Any]:
        """Calculate dashas for a specific date"""
        return self.calculate_current_dashas(birth_data, target_date)
    
    def get_dasha_periods_for_range(self, birth_data: Dict, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all dasha period changes within a date range"""
        # print(f"           Getting dasha periods from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        periods = []
        current_date = start_date
        
        while current_date <= end_date:
            dashas = self.calculate_current_dashas(birth_data, current_date)
            # print(f"           {current_date.strftime('%Y-%m-%d')}: {dashas['mahadasha']['planet']}-{dashas['antardasha']['planet']}-{dashas['pratyantardasha']['planet']}")
            
            # Find when current pratyantardasha ends
            next_change = self._find_next_dasha_change(birth_data, current_date)
            period_end = min(next_change, end_date)
            
            # print(f"           Period: {current_date.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}")
            
            periods.append({
                'start_date': current_date.strftime('%Y-%m-%d'),
                'end_date': period_end.strftime('%Y-%m-%d'),
                'mahadasha': dashas['mahadasha']['planet'],
                'antardasha': dashas['antardasha']['planet'],
                'pratyantardasha': dashas['pratyantardasha']['planet'],
                'sookshma': dashas['sookshma']['planet'],
                'prana': dashas['prana']['planet']
            })
            
            current_date = period_end + timedelta(days=1)
            
            # Prevent infinite loop
            if len(periods) > 100:
                # print(f"           WARNING: Breaking loop after 100 periods to prevent infinite loop")
                break
        
        # print(f"           Total dasha periods found: {len(periods)}")
        return periods
    
    def _find_next_dasha_change(self, birth_data: Dict, current_date: datetime) -> datetime:
        """Find the next dasha change date"""
        # Check every day for the next 30 days to find change
        current_dashas = self.calculate_current_dashas(birth_data, current_date)
        current_pratyantar = current_dashas['pratyantardasha']['planet']
        
        for days_ahead in range(1, 31):
            test_date = current_date + timedelta(days=days_ahead)
            test_dashas = self.calculate_current_dashas(birth_data, test_date)
            
            if test_dashas['pratyantardasha']['planet'] != current_pratyantar:
                return test_date
        
        # Default to 30 days ahead if no change found
        return current_date + timedelta(days=30)