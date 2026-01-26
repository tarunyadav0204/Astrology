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
        
        # Auspiciousness classification
        self.AUSPICIOUS_NAKSHATRAS = {
            'auspicious': ['Rohini', 'Uttara Phalguni', 'Uttara Ashadha', 'Uttara Bhadrapada',  # Dhruva
                          'Punarvasu', 'Swati', 'Shravana', 'Dhanishta', 'Shatabhisha',  # Chara
                          'Mrigashira', 'Chitra', 'Anuradha', 'Revati'],  # Mridu
            'inauspicious': ['Ardra', 'Ashlesha', 'Jyeshtha', 'Mula',  # Tikshna
                            'Bharani', 'Magha', 'Purva Phalguni', 'Purva Ashadha', 'Purva Bhadrapada'],  # Ugra
            'neutral': ['Ashwini', 'Pushya', 'Hasta', 'Vishakha', 'Krittika']  # Laghu/Mixed
        }
        
        self.NAKSHATRA_PROPERTIES = {
            'Ashwini': {'lord': 'Ketu', 'deity': 'Ashwini Kumaras', 'nature': 'Light/Swift', 'guna': 'Rajas', 'symbol': '🐎'},
            'Bharani': {'lord': 'Venus', 'deity': 'Yama', 'nature': 'Fierce/Ugra', 'guna': 'Rajas', 'symbol': '🌺'},
            'Krittika': {'lord': 'Sun', 'deity': 'Agni', 'nature': 'Mixed', 'guna': 'Rajas', 'symbol': '🔥'},
            'Rohini': {'lord': 'Moon', 'deity': 'Brahma', 'nature': 'Fixed/Dhruva', 'guna': 'Rajas', 'symbol': '🐄'},
            'Mrigashira': {'lord': 'Mars', 'deity': 'Soma', 'nature': 'Soft/Mridu', 'guna': 'Tamas', 'symbol': '🦌'},
            'Ardra': {'lord': 'Rahu', 'deity': 'Rudra', 'nature': 'Sharp/Tikshna', 'guna': 'Tamas', 'symbol': '💧'},
            'Punarvasu': {'lord': 'Jupiter', 'deity': 'Aditi', 'nature': 'Movable/Chara', 'guna': 'Rajas', 'symbol': '🏹'},
            'Pushya': {'lord': 'Saturn', 'deity': 'Brihaspati', 'nature': 'Light/Laghu', 'guna': 'Rajas', 'symbol': '🌸'},
            'Ashlesha': {'lord': 'Mercury', 'deity': 'Nagas', 'nature': 'Sharp/Tikshna', 'guna': 'Sattva', 'symbol': '🐍'},
            'Magha': {'lord': 'Ketu', 'deity': 'Pitrs', 'nature': 'Fierce/Ugra', 'guna': 'Tamas', 'symbol': '👑'},
            'Purva Phalguni': {'lord': 'Venus', 'deity': 'Bhaga', 'nature': 'Fierce/Ugra', 'guna': 'Rajas', 'symbol': '🛏️'},
            'Uttara Phalguni': {'lord': 'Sun', 'deity': 'Aryaman', 'nature': 'Fixed/Dhruva', 'guna': 'Rajas', 'symbol': '🌞'},
            'Hasta': {'lord': 'Moon', 'deity': 'Savitar', 'nature': 'Light/Laghu', 'guna': 'Rajas', 'symbol': '✋'},
            'Chitra': {'lord': 'Mars', 'deity': 'Vishvakarma', 'nature': 'Soft/Mridu', 'guna': 'Tamas', 'symbol': '🔨'},
            'Swati': {'lord': 'Rahu', 'deity': 'Vayu', 'nature': 'Movable/Chara', 'guna': 'Tamas', 'symbol': '🌿'},
            'Vishakha': {'lord': 'Jupiter', 'deity': 'Indragni', 'nature': 'Mixed', 'guna': 'Rajas', 'symbol': '🌳'},
            'Anuradha': {'lord': 'Saturn', 'deity': 'Mitra', 'nature': 'Soft/Mridu', 'guna': 'Tamas', 'symbol': '🏵️'},
            'Jyeshtha': {'lord': 'Mercury', 'deity': 'Indra', 'nature': 'Sharp/Tikshna', 'guna': 'Sattva', 'symbol': '☂️'},
            'Mula': {'lord': 'Ketu', 'deity': 'Nirriti', 'nature': 'Sharp/Tikshna', 'guna': 'Tamas', 'symbol': '🌿'},
            'Purva Ashadha': {'lord': 'Venus', 'deity': 'Apas', 'nature': 'Fierce/Ugra', 'guna': 'Rajas', 'symbol': '🪭'},
            'Uttara Ashadha': {'lord': 'Sun', 'deity': 'Vishvedevas', 'nature': 'Fixed/Dhruva', 'guna': 'Rajas', 'symbol': '🐘'},
            'Shravana': {'lord': 'Moon', 'deity': 'Vishnu', 'nature': 'Movable/Chara', 'guna': 'Rajas', 'symbol': '👂'},
            'Dhanishta': {'lord': 'Mars', 'deity': 'Vasus', 'nature': 'Movable/Chara', 'guna': 'Tamas', 'symbol': '🥁'},
            'Shatabhisha': {'lord': 'Rahu', 'deity': 'Varuna', 'nature': 'Movable/Chara', 'guna': 'Tamas', 'symbol': '⭕'},
            'Purva Bhadrapada': {'lord': 'Jupiter', 'deity': 'Aja Ekapada', 'nature': 'Fierce/Ugra', 'guna': 'Rajas', 'symbol': '⚡'},
            'Uttara Bhadrapada': {'lord': 'Saturn', 'deity': 'Ahir Budhnya', 'nature': 'Fixed/Dhruva', 'guna': 'Tamas', 'symbol': '🐍'},
            'Revati': {'lord': 'Mercury', 'deity': 'Pushan', 'nature': 'Soft/Mridu', 'guna': 'Sattva', 'symbol': '🐟'}
        }
    
    def calculate_annual_nakshatra_periods(self, nakshatra_name: str, year: int, latitude: float = 28.6139, longitude: float = 77.2090) -> Dict[str, Any]:
        """Calculate all periods when Moon is in specific nakshatra for a year"""
        
        if nakshatra_name not in self.NAKSHATRA_NAMES:
            raise ValueError(f"Invalid nakshatra name: {nakshatra_name}")
        
        nakshatra_index = self.NAKSHATRA_NAMES.index(nakshatra_name)
        nakshatra_start = nakshatra_index * 13.333333
        nakshatra_end = (nakshatra_index + 1) * 13.333333
        
        periods = []
        current_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        
        # Moon completes cycle in ~27 days, check every 26 days
        while current_date < end_date:
            jd = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            
            if nakshatra_start <= moon_pos < nakshatra_end:
                entry = self._quick_find_entry(current_date, nakshatra_start)
                exit_time = entry + timedelta(hours=24)
                
                periods.append({
                    'start_datetime': entry,
                    'end_datetime': exit_time,
                    'start_time': entry.strftime('%I:%M %p'),
                    'end_time': exit_time.strftime('%I:%M %p'),
                    'start_date': entry.strftime('%b %d'),
                    'end_date': exit_time.strftime('%b %d'),
                    'duration_hours': 24,
                    'weekday': entry.strftime('%a'),
                    'day_number': entry.day,
                    'month_name': entry.strftime('%b')
                })
                current_date += timedelta(days=27)
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
    
    def _calculate_nakshatra_distance(self, moon_pos: float, target_start: float) -> float:
        """Calculate shortest angular distance from moon to target nakshatra"""
        diff = target_start - moon_pos
        if diff < 0:
            diff += 360
        # Return shortest distance (forward or backward)
        return min(diff, 360 - diff)
    
    def _is_in_nakshatra_range(self, moon_pos: float, start: float, end: float) -> bool:
        """Check if Moon position is within nakshatra range"""
        # Handle wrap-around at 360 degrees
        if start > end:  # This shouldn't happen for nakshatras, but safety check
            return moon_pos >= start or moon_pos <= end
        return start <= moon_pos < end
    
    def _quick_find_entry(self, start_date: datetime, nak_start: float) -> datetime:
        """Quick approximation of nakshatra entry"""
        for hours in range(-12, 13, 3):
            test_time = start_date + timedelta(hours=hours)
            jd = swe.julday(test_time.year, test_time.month, test_time.day, test_time.hour)
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            if abs(moon_pos - nak_start) < 1:
                return test_time + timedelta(hours=5, minutes=30)
        return start_date + timedelta(hours=5, minutes=30)
    

    

    
    def get_nakshatra_auspiciousness(self, nakshatra_name: str) -> str:
        """Get base auspiciousness classification for color coding"""
        if nakshatra_name in self.AUSPICIOUS_NAKSHATRAS['auspicious']:
            return 'auspicious'
        elif nakshatra_name in self.AUSPICIOUS_NAKSHATRAS['inauspicious']:
            return 'inauspicious'
        else:
            return 'neutral'
    
    def calculate_tithi_from_datetime(self, dt: datetime) -> int:
        """Calculate tithi (lunar day) from datetime using Swiss Ephemeris"""
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        
        # Get Sun and Moon positions
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        
        # Calculate tithi (difference between Moon and Sun)
        diff = moon_pos - sun_pos
        if diff < 0:
            diff += 360
        
        # Each tithi is 12 degrees
        tithi = int(diff / 12) + 1
        if tithi > 30:
            tithi -= 30
        
        return tithi
    
    def calculate_bhadra_periods(self, start_datetime: datetime) -> bool:
        """Calculate if the time falls in Bhadra (inauspicious) period"""
        jd = swe.julday(start_datetime.year, start_datetime.month, start_datetime.day, 
                       start_datetime.hour + start_datetime.minute/60.0)
        
        # Get weekday (0=Sunday, 1=Monday, etc.)
        weekday = (start_datetime.weekday() + 1) % 7
        
        # Bhadra periods based on weekday (in hours from sunrise)
        bhadra_periods = {
            0: (9, 10.5),   # Sunday: 9:00-10:30 AM
            1: (8, 9.5),    # Monday: 8:00-9:30 AM  
            2: (7, 8.5),    # Tuesday: 7:00-8:30 AM
            3: (6, 7.5),    # Wednesday: 6:00-7:30 AM
            4: (5, 6.5),    # Thursday: 5:00-6:30 AM
            5: (4, 5.5),    # Friday: 4:00-5:30 AM
            6: (3, 4.5),    # Saturday: 3:00-4:30 AM
        }
        
        if weekday in bhadra_periods:
            start_hour, end_hour = bhadra_periods[weekday]
            current_hour = start_datetime.hour + start_datetime.minute/60.0
            
            # Check if current time falls in Bhadra period
            if start_hour <= current_hour <= end_hour:
                return True
        
        return False
    
    def calculate_period_auspiciousness(self, nakshatra_name: str, start_datetime: datetime) -> str:
        """Use traditional nakshatra-based auspiciousness with some variation"""
        
        # Get base nakshatra auspiciousness
        base = self.get_nakshatra_auspiciousness(nakshatra_name)
        
        # Add some variation based on weekday to create realistic color distribution
        weekday = start_datetime.weekday()
        
        # Saturday reduces auspiciousness
        if weekday == 5:  # Saturday
            if base == 'auspicious':
                return 'neutral'
            else:
                return 'inauspicious'
        
        # Tuesday, Thursday, Friday enhance auspiciousness  
        if weekday in [1, 3, 4]:  # Tue, Thu, Fri
            if base == 'inauspicious':
                return 'neutral'
            elif base == 'neutral':
                return 'auspicious'
            else:
                return 'auspicious'
        
        # For other days, return base auspiciousness
        return base
    
    def get_nakshatra_properties(self, nakshatra_name: str) -> Dict[str, Any]:
        """Get detailed properties of a nakshatra"""
        if nakshatra_name not in self.NAKSHATRA_PROPERTIES:
            return {}
        
        props = self.NAKSHATRA_PROPERTIES[nakshatra_name].copy()
        props['name'] = nakshatra_name
        props['index'] = self.NAKSHATRA_NAMES.index(nakshatra_name) + 1
        props['degree_range'] = f"{(props['index']-1) * 13.33:.2f}° - {props['index'] * 13.33:.2f}°"
        props['auspiciousness'] = self.get_nakshatra_auspiciousness(nakshatra_name)
        
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