import swisseph as swe
from datetime import datetime, timedelta
import math
from typing import Dict, List, Any

class AnnualNakshatraCalculator:
    """Calculate annual nakshatra periods for specific nakshatras"""
    
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        self.NAKSHATRA_NAMES = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya',
            'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
            'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
            'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        self.NAKSHATRA_PROPERTIES = {
            'Ashwini': {'lord': 'Ketu', 'deity': 'Ashwini Kumaras', 'nature': 'Light/Swift', 'guna': 'Rajas'},
            'Bharani': {'lord': 'Venus', 'deity': 'Yama', 'nature': 'Fierce/Ugra', 'guna': 'Rajas'},
            'Krittika': {'lord': 'Sun', 'deity': 'Agni', 'nature': 'Mixed', 'guna': 'Rajas'},
            'Rohini': {'lord': 'Moon', 'deity': 'Brahma', 'nature': 'Fixed/Dhruva', 'guna': 'Rajas'},
            'Mrigashira': {'lord': 'Mars', 'deity': 'Soma', 'nature': 'Soft/Mridu', 'guna': 'Tamas'},
            'Ardra': {'lord': 'Rahu', 'deity': 'Rudra', 'nature': 'Sharp/Tikshna', 'guna': 'Tamas'},
            'Punarvasu': {'lord': 'Jupiter', 'deity': 'Aditi', 'nature': 'Movable/Chara', 'guna': 'Rajas'},
            'Pushya': {'lord': 'Saturn', 'deity': 'Brihaspati', 'nature': 'Light/Laghu', 'guna': 'Rajas'},
            'Ashlesha': {'lord': 'Mercury', 'deity': 'Nagas', 'nature': 'Sharp/Tikshna', 'guna': 'Sattva'},
            'Magha': {'lord': 'Ketu', 'deity': 'Pitrs', 'nature': 'Fierce/Ugra', 'guna': 'Tamas'},
            'Purva Phalguni': {'lord': 'Venus', 'deity': 'Bhaga', 'nature': 'Fierce/Ugra', 'guna': 'Rajas'},
            'Uttara Phalguni': {'lord': 'Sun', 'deity': 'Aryaman', 'nature': 'Fixed/Dhruva', 'guna': 'Rajas'},
            'Hasta': {'lord': 'Moon', 'deity': 'Savitar', 'nature': 'Light/Laghu', 'guna': 'Rajas'},
            'Chitra': {'lord': 'Mars', 'deity': 'Vishvakarma', 'nature': 'Soft/Mridu', 'guna': 'Tamas'},
            'Swati': {'lord': 'Rahu', 'deity': 'Vayu', 'nature': 'Movable/Chara', 'guna': 'Tamas'},
            'Vishakha': {'lord': 'Jupiter', 'deity': 'Indragni', 'nature': 'Mixed', 'guna': 'Rajas'},
            'Anuradha': {'lord': 'Saturn', 'deity': 'Mitra', 'nature': 'Soft/Mridu', 'guna': 'Tamas'},
            'Jyeshtha': {'lord': 'Mercury', 'deity': 'Indra', 'nature': 'Sharp/Tikshna', 'guna': 'Sattva'},
            'Mula': {'lord': 'Ketu', 'deity': 'Nirriti', 'nature': 'Sharp/Tikshna', 'guna': 'Tamas'},
            'Purva Ashadha': {'lord': 'Venus', 'deity': 'Apas', 'nature': 'Fierce/Ugra', 'guna': 'Rajas'},
            'Uttara Ashadha': {'lord': 'Sun', 'deity': 'Vishvedevas', 'nature': 'Fixed/Dhruva', 'guna': 'Rajas'},
            'Shravana': {'lord': 'Moon', 'deity': 'Vishnu', 'nature': 'Movable/Chara', 'guna': 'Rajas'},
            'Dhanishta': {'lord': 'Mars', 'deity': 'Vasus', 'nature': 'Movable/Chara', 'guna': 'Tamas'},
            'Shatabhisha': {'lord': 'Rahu', 'deity': 'Varuna', 'nature': 'Movable/Chara', 'guna': 'Tamas'},
            'Purva Bhadrapada': {'lord': 'Jupiter', 'deity': 'Aja Ekapada', 'nature': 'Fierce/Ugra', 'guna': 'Rajas'},
            'Uttara Bhadrapada': {'lord': 'Saturn', 'deity': 'Ahir Budhnya', 'nature': 'Fixed/Dhruva', 'guna': 'Tamas'},
            'Revati': {'lord': 'Mercury', 'deity': 'Pushan', 'nature': 'Soft/Mridu', 'guna': 'Sattva'}
        }
    
    def calculate_annual_nakshatra_periods(self, nakshatra_name: str, year: int, latitude: float = 28.6139, longitude: float = 77.2090) -> Dict[str, Any]:
        """Calculate all periods when Moon is in specific nakshatra for a year"""
        
        if nakshatra_name not in self.NAKSHATRA_NAMES:
            raise ValueError(f"Invalid nakshatra name: {nakshatra_name}")
        
        nakshatra_index = self.NAKSHATRA_NAMES.index(nakshatra_name)
        nakshatra_start = nakshatra_index * 13.333333
        nakshatra_end = (nakshatra_index + 1) * 13.333333
        
        periods = []
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        
        current_date = start_date
        
        while current_date < end_date:
            jd = swe.julday(current_date.year, current_date.month, current_date.day, 0.0)
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            
            # Check if Moon is in target nakshatra
            if self._is_in_nakshatra_range(moon_pos, nakshatra_start, nakshatra_end):
                period = self._find_nakshatra_period(current_date, nakshatra_start, nakshatra_end, latitude, longitude)
                if period:
                    periods.append(period)
                    # Skip to end of this period to avoid duplicates
                    current_date = period['end_datetime'] + timedelta(days=1)
                else:
                    current_date += timedelta(days=1)
            else:
                current_date += timedelta(days=1)
        
        return {
            'nakshatra': nakshatra_name,
            'year': year,
            'properties': self.NAKSHATRA_PROPERTIES[nakshatra_name],
            'periods': periods,
            'total_periods': len(periods),
            'location': {'latitude': latitude, 'longitude': longitude}
        }
    
    def _is_in_nakshatra_range(self, moon_pos: float, start: float, end: float) -> bool:
        """Check if Moon position is within nakshatra range"""
        # Handle wrap-around at 360 degrees
        if start > end:  # This shouldn't happen for nakshatras, but safety check
            return moon_pos >= start or moon_pos <= end
        return start <= moon_pos < end
    
    def _find_nakshatra_period(self, start_date: datetime, nak_start: float, nak_end: float, lat: float, lon: float) -> Dict[str, Any]:
        """Find exact start and end times for nakshatra period"""
        
        # Find when Moon enters nakshatra
        entry_time = self._find_nakshatra_entry(start_date, nak_start, backwards=True)
        if not entry_time:
            return None
        
        # Find when Moon exits nakshatra
        exit_time = self._find_nakshatra_exit(entry_time, nak_end)
        if not exit_time:
            return None
        
        # Convert to local time (IST)
        entry_local = entry_time + timedelta(hours=5, minutes=30)
        exit_local = exit_time + timedelta(hours=5, minutes=30)
        
        return {
            'start_datetime': entry_local,
            'end_datetime': exit_local,
            'start_time': entry_local.strftime('%I:%M %p'),
            'end_time': exit_local.strftime('%I:%M %p'),
            'start_date': entry_local.strftime('%b %d'),
            'end_date': exit_local.strftime('%b %d'),
            'duration_hours': (exit_time - entry_time).total_seconds() / 3600,
            'weekday': entry_local.strftime('%a'),
            'day_number': entry_local.day,
            'month_name': entry_local.strftime('%b')
        }
    
    def _find_nakshatra_entry(self, start_date: datetime, nak_start: float, backwards: bool = False) -> datetime:
        """Find when Moon enters nakshatra"""
        
        current_time = start_date
        step = timedelta(hours=-1) if backwards else timedelta(hours=1)
        
        for _ in range(72):  # Max 3 days search
            jd = swe.julday(current_time.year, current_time.month, current_time.day, 
                           current_time.hour + current_time.minute/60.0)
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            
            if backwards:
                if moon_pos < nak_start or moon_pos >= nak_start + 13.333333:
                    # Found entry point
                    return current_time + timedelta(hours=1)
            else:
                if nak_start <= moon_pos < nak_start + 13.333333:
                    return current_time
            
            current_time += step
        
        return start_date  # Fallback
    
    def _find_nakshatra_exit(self, entry_time: datetime, nak_end: float) -> datetime:
        """Find when Moon exits nakshatra"""
        
        current_time = entry_time
        
        for _ in range(72):  # Max 3 days search
            jd = swe.julday(current_time.year, current_time.month, current_time.day,
                           current_time.hour + current_time.minute/60.0)
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            
            if moon_pos >= nak_end or moon_pos < nak_end - 13.333333:
                return current_time
            
            current_time += timedelta(hours=1)
        
        return entry_time + timedelta(days=1)  # Fallback
    
    def get_nakshatra_properties(self, nakshatra_name: str) -> Dict[str, Any]:
        """Get detailed properties of a nakshatra"""
        if nakshatra_name not in self.NAKSHATRA_PROPERTIES:
            return {}
        
        props = self.NAKSHATRA_PROPERTIES[nakshatra_name].copy()
        props['name'] = nakshatra_name
        props['index'] = self.NAKSHATRA_NAMES.index(nakshatra_name) + 1
        props['degree_range'] = f"{(props['index']-1) * 13.33:.2f}° - {props['index'] * 13.33:.2f}°"
        
        return props
    
    def get_all_nakshatras_list(self) -> List[Dict[str, Any]]:
        """Get list of all nakshatras with basic properties"""
        nakshatras = []
        
        for i, name in enumerate(self.NAKSHATRA_NAMES):
            props = self.NAKSHATRA_PROPERTIES[name].copy()
            props['name'] = name
            props['index'] = i + 1
            props['degree_range'] = f"{i * 13.33:.1f}° - {(i + 1) * 13.33:.1f}°"
            nakshatras.append(props)
        
        return nakshatras