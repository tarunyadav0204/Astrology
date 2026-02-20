import swisseph as swe
from datetime import datetime, timedelta
import math
from typing import Dict, List, Any, Optional

try:
    from utils.timezone_service import parse_timezone_offset
except ImportError:
    parse_timezone_offset = None


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
    
    def _moon_sidereal_lon(self, jd: float, ayanamsa_correction_degrees: float = 0.0) -> float:
        """Moon's sidereal longitude in [0, 360). Uses Lahiri + optional correction to align with Drik Panchang."""
        if ayanamsa_correction_degrees == 0.0:
            lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            return lon % 360.0
        # Apply custom correction: sidereal = tropical - ayanamsa + correction (positive = crossing earlier)
        trop = swe.calc_ut(jd, swe.MOON, 0)[0][0]
        ayan = swe.get_ayanamsa_ut(jd)
        return (trop - ayan + ayanamsa_correction_degrees) % 360.0

    def _find_moon_longitude_crossing(
        self,
        jd_start: float,
        target_lon: float,
        max_days: float = 2.0,
        ayanamsa_correction_degrees: float = 0.0,
    ) -> Optional[float]:
        """
        Find the next UT JD after jd_start when Moon's sidereal longitude crosses target_lon (0-360).
        Moon moves forward ~13°/day. Returns None if no crossing in max_days.
        Precision: ~1 minute (1/1440 day).
        """
        target_lon = target_lon % 360.0
        step = 1.0 / 24.0  # 1 hour
        jd = jd_start
        end_jd = jd_start + max_days
        prev_lon = self._moon_sidereal_lon(jd, ayanamsa_correction_degrees)
        
        while jd < end_jd:
            jd += step
            curr_lon = self._moon_sidereal_lon(jd, ayanamsa_correction_degrees)
            # Detect crossing: Moon moves forward; handle wrap at 360
            crossed = False
            if prev_lon < curr_lon:
                if prev_lon < target_lon <= curr_lon:
                    crossed = True
            else:
                # wrap: prev_lon > curr_lon (e.g. 350 -> 10)
                if prev_lon < target_lon or target_lon <= curr_lon:
                    crossed = True
            if crossed:
                # Binary search in [jd - step, jd] for precision (~1 min)
                lo, hi = jd - step, jd
                for _ in range(30):
                    mid = (lo + hi) / 2.0
                    mid_lon = self._moon_sidereal_lon(mid, ayanamsa_correction_degrees)
                    # Moon moves forward; "before" target = need to go forward in time (lo = mid)
                    diff = (target_lon - mid_lon + 360.0) % 360.0
                    if diff > 180.0:
                        lo = mid
                    else:
                        hi = mid
                    if hi - lo < 1.0 / 1440.0:
                        return (lo + hi) / 2.0
                return (lo + hi) / 2.0
            prev_lon = curr_lon
        return None
    
    def _jd_ut_to_local_datetime(self, jd_ut: float, tz_offset_hours: float) -> datetime:
        """Convert UT Julian Day to local datetime (date + time) using timezone offset."""
        local_jd = jd_ut + (tz_offset_hours / 24.0)
        y, m, d, h, mi, s = swe.jdut1_to_utc(local_jd, 1)
        sec = min(59, int(round(s)))  # datetime allows 0..59 only
        return datetime(int(y), int(m), int(d), int(h), int(mi), sec)
    
    def calculate_annual_nakshatra_periods_all_continuous(
        self,
        year: int,
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        ayanamsa_correction_degrees: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Compute all nakshatra periods for the year so that each boundary is used exactly once:
        end of nakshatra N = start of nakshatra N+1 (no gaps or overlaps).
        Returns a flat list of periods, each with nakshatra_name, start_datetime, end_datetime, etc.
        """
        nak_slice = 360.0 / 27.0
        tz_offset = 5.5
        if parse_timezone_offset:
            try:
                tz_offset = parse_timezone_offset('', latitude, longitude)
            except Exception:
                pass
        jd_year_start = swe.julday(year, 1, 1, 0.0)
        jd_year_end = swe.julday(year + 1, 1, 1, 0.0)

        # Build ordered list of (jd, into_nakshatra_index) for every boundary crossing in the year.
        # Each (jd, nak) means: at jd we enter nakshatra nak (so the previous nakshatra ends at jd).
        crossings = []  # (jd, into_nakshatra_index)
        cursor_jd = jd_year_start
        min_jd_step = 1.0 / 24.0  # 1 hour: skip duplicate crossing if same nakshatra within this
        min_forward_jd = 1.0 / 1440.0  # crossing must be at least 1 min after previous (avoid past/wrong boundary)
        while cursor_jd < jd_year_end:
            lon = self._moon_sidereal_lon(cursor_jd, ayanamsa_correction_degrees)
            current_nak = int(lon / nak_slice) % 27
            next_boundary = ((current_nak + 1) * nak_slice) % 360.0
            if next_boundary == 0:
                next_boundary = 360.0
            exit_jd = self._find_moon_longitude_crossing(
                cursor_jd + 1.0 / 1440.0, next_boundary, max_days=32.0, ayanamsa_correction_degrees=ayanamsa_correction_degrees
            )
            if exit_jd is None or exit_jd >= jd_year_end:
                break
            next_nak = (current_nak + 1) % 27
            last_jd = crossings[-1][0] if crossings else jd_year_start
            expected_next = (crossings[-1][1] + 1) % 27 if crossings else None
            # Enforce strict order: must be next nakshatra in cycle (fixes Ashlesha reappearing after Magha)
            if expected_next is not None and next_nak != expected_next:
                cursor_jd = cursor_jd + min_jd_step
                continue
            # Skip if this crossing is in the past or same as last (wrong boundary)
            if exit_jd <= last_jd + min_forward_jd:
                cursor_jd = cursor_jd + min_jd_step
                continue
            # Skip duplicate: same nakshatra entered within 1 hour of previous (numerical artifact)
            if crossings and crossings[-1][1] == next_nak and (exit_jd - crossings[-1][0]) < min_jd_step:
                cursor_jd = exit_jd + 1.0 / 1440.0
                continue
            crossings.append((exit_jd, next_nak))
            cursor_jd = exit_jd + 1.0 / 1440.0

        # Build periods: use each boundary exactly once. First period starts at year_start.
        result = []
        # First period: nakshatra at year start, from year_start to first crossing
        if crossings:
            entry_jd = jd_year_start
            exit_jd = crossings[0][0]
            lon0 = self._moon_sidereal_lon(jd_year_start, ayanamsa_correction_degrees)
            first_nak = int(lon0 / nak_slice) % 27
            entry_local = self._jd_ut_to_local_datetime(entry_jd, tz_offset)
            exit_local = self._jd_ut_to_local_datetime(exit_jd, tz_offset)
            result.append({
                'nakshatra': self.NAKSHATRA_NAMES[first_nak],
                'start_datetime': entry_local,
                'end_datetime': exit_local,
                'start_time': entry_local.strftime('%I:%M %p'),
                'end_time': exit_local.strftime('%I:%M %p'),
                'start_date': entry_local.strftime('%b %d'),
                'end_date': exit_local.strftime('%b %d'),
            })
        for k in range(len(crossings)):
            entry_jd, nak_idx = crossings[k]
            exit_jd = crossings[k + 1][0] if k + 1 < len(crossings) else jd_year_end
            if exit_jd > jd_year_end:
                exit_jd = jd_year_end
            entry_local = self._jd_ut_to_local_datetime(entry_jd, tz_offset)
            exit_local = self._jd_ut_to_local_datetime(exit_jd, tz_offset)
            result.append({
                'nakshatra': self.NAKSHATRA_NAMES[nak_idx],
                'start_datetime': entry_local,
                'end_datetime': exit_local,
                'start_time': entry_local.strftime('%I:%M %p'),
                'end_time': exit_local.strftime('%I:%M %p'),
                'start_date': entry_local.strftime('%b %d'),
                'end_date': exit_local.strftime('%b %d'),
            })
        # Remove duplicates: same nakshatra and same start_datetime (can occur from crossing list edge cases)
        seen = set()
        deduped = []
        for p in result:
            key = (p["nakshatra"], p["start_datetime"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(p)
        return deduped

    def calculate_annual_nakshatra_periods(
        self,
        nakshatra_name: str,
        year: int,
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        ayanamsa_correction_degrees: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate all periods when Moon is in this nakshatra for the year.
        Uses exact Moon longitude crossing (Lahiri sidereal) and converts to local time.
        Optional ayanamsa_correction_degrees: add to sidereal longitude (positive = crossings earlier).
        Use a small value (e.g. -0.2 to +0.2) to align with Drik Panchang if needed.
        """
        if nakshatra_name not in self.NAKSHATRA_NAMES:
            raise ValueError(f"Invalid nakshatra name: {nakshatra_name}")
        
        tz_offset = 5.5  # IST fallback
        if parse_timezone_offset:
            try:
                tz_offset = parse_timezone_offset('', latitude, longitude)
            except Exception:
                pass
        
        nakshatra_index = self.NAKSHATRA_NAMES.index(nakshatra_name)
        nak_slice = 360.0 / 27.0
        nakshatra_start = (nakshatra_index * nak_slice) % 360.0
        nakshatra_end = ((nakshatra_index + 1) * nak_slice) % 360.0
        if nakshatra_end == 0:
            nakshatra_end = 360.0
        
        jd_year_start = swe.julday(year, 1, 1, 0.0)
        jd_year_end = swe.julday(year + 1, 1, 1, 0.0)
        
        periods = []
        cursor_jd = jd_year_start
        
        while cursor_jd < jd_year_end:
            entry_jd = self._find_moon_longitude_crossing(
                cursor_jd, nakshatra_start, max_days=30.0, ayanamsa_correction_degrees=ayanamsa_correction_degrees
            )
            if entry_jd is None or entry_jd >= jd_year_end:
                break
            exit_jd = self._find_moon_longitude_crossing(
                entry_jd + 1.0 / 1440.0, nakshatra_end, max_days=2.0, ayanamsa_correction_degrees=ayanamsa_correction_degrees
            )
            if exit_jd is None:
                exit_jd = entry_jd + 1.0  # fallback ~1 day
            if exit_jd > jd_year_end:
                exit_jd = jd_year_end
            
            entry_local = self._jd_ut_to_local_datetime(entry_jd, tz_offset)
            exit_local = self._jd_ut_to_local_datetime(exit_jd, tz_offset)
            duration_hours = (exit_jd - entry_jd) * 24.0
            
            periods.append({
                'start_datetime': entry_local,
                'end_datetime': exit_local,
                'start_time': entry_local.strftime('%I:%M %p'),
                'end_time': exit_local.strftime('%I:%M %p'),
                'start_date': entry_local.strftime('%b %d'),
                'end_date': exit_local.strftime('%b %d'),
                'duration_hours': round(duration_hours, 2),
                'weekday': entry_local.strftime('%a'),
                'day_number': entry_local.day,
                'month_name': entry_local.strftime('%b')
            })
            cursor_jd = exit_jd + 0.01
        
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