import swisseph as swe
from datetime import datetime, timedelta
from .house_significations import SIGN_LORDS
from .config import DASHA_PERIODS, NAKSHATRA_LORDS, PLANET_ORDER
from utils.timezone_service import parse_timezone_offset

class DashaIntegration:
    """Integrates Vimshottari Dasha system with event predictions"""
    
    def __init__(self, birth_data):
        self.birth_data = birth_data
        self.dasha_periods = DASHA_PERIODS
        self.nakshatra_lords = NAKSHATRA_LORDS
        
    def calculate_dasha_periods(self):
        """Calculate Maha and Antar Dasha periods"""
        # Calculate Julian Day
        time_parts = self.birth_data.time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        tz_offset = parse_timezone_offset(
            self.birth_data.timezone,
            self.birth_data.latitude,
            self.birth_data.longitude
        )
        
        utc_hour = hour - tz_offset
        jd = swe.julday(
            int(self.birth_data.date.split('-')[0]),
            int(self.birth_data.date.split('-')[1]),
            int(self.birth_data.date.split('-')[2]),
            utc_hour
        )
        
        # Get Moon position
        # Set Lahiri Ayanamsa for accurate Vedic calculations

        swe.set_sid_mode(swe.SIDM_LAHIRI)

        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        
        # Find Moon's nakshatra
        nakshatra_index = int(moon_pos / 13.333333)
        moon_lord = self.nakshatra_lords[nakshatra_index]
        
        # Calculate elapsed portion in current nakshatra
        nakshatra_start = nakshatra_index * 13.333333
        elapsed_degrees = moon_pos - nakshatra_start
        elapsed_fraction = elapsed_degrees / 13.333333
        
        # Calculate birth date
        birth_datetime = datetime.strptime(f"{self.birth_data.date} {self.birth_data.time}", "%Y-%m-%d %H:%M")
        
        # Calculate Maha Dasha periods
        maha_dashas = []
        current_date = birth_datetime
        
        start_index = PLANET_ORDER.index(moon_lord)
        
        # Calculate remaining period for first dasha
        remaining_years = self.dasha_periods[moon_lord] * (1 - elapsed_fraction)
        
        for i in range(9):
            planet = PLANET_ORDER[(start_index + i) % 9]
            period_years = remaining_years if i == 0 else self.dasha_periods[planet]
            
            # Calculate end date more precisely
            total_days = period_years * 365.25
            end_date = current_date + timedelta(days=total_days)
            
            # Adjust to start of day for cleaner dates
            if i > 0:  # Don't adjust birth date
                current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calculate Antar Dashas for this Maha Dasha
            antar_dashas = self._calculate_antar_dashas(planet, current_date, end_date, period_years)
            
            maha_dashas.append({
                'planet': planet,
                'start': current_date,
                'end': end_date,
                'years': round(period_years, 2),
                'antar_dashas': antar_dashas
            })
            
            current_date = end_date
            remaining_years = 0
        
        return maha_dashas
    
    def _calculate_antar_dashas(self, maha_lord, start_date, end_date, total_years):
        """Calculate Antar Dasha periods within a Maha Dasha"""
        antar_dashas = []
        # Start with Maha Dasha lord
        start_index = PLANET_ORDER.index(maha_lord)
        current_date = start_date
        
        for i in range(9):
            antar_lord = PLANET_ORDER[(start_index + i) % 9]
            
            # Antar Dasha duration = (Maha lord years * Antar lord years) / 120
            antar_years = (self.dasha_periods[maha_lord] * self.dasha_periods[antar_lord]) / 120
            antar_days = antar_years * 365.25
            antar_end = current_date + timedelta(days=antar_days)
            
            # Don't exceed Maha Dasha end date
            if antar_end > end_date:
                antar_end = end_date
            
            antar_dashas.append({
                'planet': antar_lord,
                'start': current_date,
                'end': antar_end,
                'years': round(antar_years, 3)
            })
            
            current_date = antar_end
            if current_date >= end_date:
                break
        
        return antar_dashas
    
    def find_relevant_dasha_periods(self, relevant_planets, start_year=None, end_year=None):
        """Find dasha periods when relevant planets are active"""
        if not start_year:
            start_year = datetime.now().year
        if not end_year:
            end_year = start_year + 10
        
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        dasha_periods = self.calculate_dasha_periods()
        relevant_periods = []
        
        for maha_dasha in dasha_periods:
            # Check if Maha Dasha overlaps with our time range
            if maha_dasha['end'] < start_date or maha_dasha['start'] > end_date:
                continue
            
            # Check if Maha Dasha lord is relevant
            if maha_dasha['planet'] in relevant_planets:
                overlap_start = max(maha_dasha['start'], start_date)
                overlap_end = min(maha_dasha['end'], end_date)
                
                relevant_periods.append({
                    'type': 'maha',
                    'planet': maha_dasha['planet'],
                    'start': overlap_start,
                    'end': overlap_end,
                    'strength': 'high'  # Maha Dasha has high influence
                })
            
            # Check Antar Dashas
            for antar_dasha in maha_dasha['antar_dashas']:
                if antar_dasha['end'] < start_date or antar_dasha['start'] > end_date:
                    continue
                
                if antar_dasha['planet'] in relevant_planets:
                    overlap_start = max(antar_dasha['start'], start_date)
                    overlap_end = min(antar_dasha['end'], end_date)
                    
                    # Higher strength if both Maha and Antar lords are relevant
                    strength = 'very_high' if maha_dasha['planet'] in relevant_planets else 'medium'
                    
                    relevant_periods.append({
                        'type': 'antar',
                        'maha_lord': maha_dasha['planet'],
                        'antar_lord': antar_dasha['planet'],
                        'planet': antar_dasha['planet'],
                        'start': overlap_start,
                        'end': overlap_end,
                        'strength': strength
                    })
        
        return sorted(relevant_periods, key=lambda x: x['start'])
    
    def get_current_dasha(self, date=None):
        """Get current running Maha and Antar Dasha for a given date"""
        if not date:
            date = datetime.now()
        
        dasha_periods = self.calculate_dasha_periods()
        
        for maha_dasha in dasha_periods:
            if maha_dasha['start'] <= date <= maha_dasha['end']:
                # Find current Antar Dasha
                for antar_dasha in maha_dasha['antar_dashas']:
                    if antar_dasha['start'] <= date <= antar_dasha['end']:
                        return {
                            'maha_lord': maha_dasha['planet'],
                            'antar_lord': antar_dasha['planet'],
                            'maha_start': maha_dasha['start'],
                            'maha_end': maha_dasha['end'],
                            'antar_start': antar_dasha['start'],
                            'antar_end': antar_dasha['end']
                        }
        
        return None