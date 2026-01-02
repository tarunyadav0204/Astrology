import swisseph as swe
from datetime import datetime, timedelta
import calendar
from typing import Dict, List, Any
import pytz
from utils.timezone_service import parse_timezone_offset
from .panchang_calculator import PanchangCalculator

class MonthlyPanchangCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.panchang_calc = PanchangCalculator()
    
    def _parse_timezone(self, tz_str):
        """Helper to parse timezone string like 'UTC+5:30' into float offset"""
        # Use centralized timezone service
        return parse_timezone_offset(tz_str, 0, 0)  # Default coordinates for parsing
    
    def calculate_monthly_panchang(self, year: int, month: int, latitude: float, longitude: float, timezone: str = None) -> Dict[str, Any]:
        """Calculate complete panchang for entire month with timezone parameter"""
        
        # Get number of days in month
        days_in_month = calendar.monthrange(year, month)[1]
        
        monthly_data = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'days': [],
            'location': {'latitude': latitude, 'longitude': longitude},
            'timezone': timezone
        }
        
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            # CRITICAL: Pass timezone parameter to daily calculation
            daily_data = self.calculate_daily_panchang(date_str, latitude, longitude, timezone)
            monthly_data['days'].append(daily_data)
        
        return monthly_data
    
    def calculate_daily_panchang(self, date_str: str, latitude: float, longitude: float, timezone: str = None) -> Dict[str, Any]:
        """Calculate detailed panchang for a single day with dynamic timezone"""
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 12.0)
        
        # Basic panchang elements with timezone
        basic_panchang = self.panchang_calc.calculate_panchang(date_str, latitude, longitude, timezone)
        
        # Calculate sunrise/sunset with timezone
        sunrise_sunset = self._calculate_sunrise_sunset(date_str, latitude, longitude, timezone)
        
        # Calculate special times with timezone
        special_times = self._calculate_special_times(date_str, latitude, longitude, sunrise_sunset, timezone)
        
        # Calculate samvats and calendar info
        calendar_info = self._calculate_calendar_info(date_obj, jd)
        
        # Calculate moon info
        moon_info = self._calculate_moon_info(jd)
        
        # Calculate planetary positions for signs
        planetary_signs = self._calculate_planetary_signs(jd)
        
        return {
            'date': date_str,
            'day': date_obj.day,
            'weekday': date_obj.strftime('%A'),
            'weekday_short': date_obj.strftime('%a'),
            'basic_panchang': basic_panchang,
            'sunrise_sunset': sunrise_sunset,
            'special_times': special_times,
            'calendar_info': calendar_info,
            'moon_info': moon_info,
            'planetary_signs': planetary_signs,
            'timezone': timezone
        }
    
    def _calculate_sunrise_sunset(self, date_str: str, latitude: float, longitude: float, timezone: str = None) -> Dict[str, Any]:
        """Calculate sunrise, sunset, moonrise, moonset with proper timezone handling using pytz"""
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 0.0)
        
        geopos = [longitude, latitude, 0.0]
        
        # Parse timezone - support both IANA names and UTC offsets
        if timezone.startswith('UTC'):
            # Handle UTC offset format
            tz_offset = self._parse_timezone(timezone)
        else:
            # Handle IANA timezone names with pytz
            try:
                local_tz = pytz.timezone(timezone)
                # Get offset for this specific date (handles DST)
                dt_naive = datetime(date_obj.year, date_obj.month, date_obj.day, 12, 0, 0)
                dt_localized = local_tz.localize(dt_naive)
                tz_offset = dt_localized.utcoffset().total_seconds() / 3600
            except:
                tz_offset = 0.0  # Fallback to UTC
        
        try:
            # Calculate sunrise/sunset
            sunrise_result = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)
            moonrise_result = swe.rise_trans(jd, swe.MOON, swe.CALC_RISE, geopos)
            moonset_result = swe.rise_trans(jd, swe.MOON, swe.CALC_SET, geopos)
            
            sunrise_jd = sunrise_result[1][0] if sunrise_result[0] == 0 else None
            sunset_jd = sunset_result[1][0] if sunset_result[0] == 0 else None
            moonrise_jd = moonrise_result[1][0] if moonrise_result[0] == 0 else None
            moonset_jd = moonset_result[1][0] if moonset_result[0] == 0 else None
            
            def jd_to_local_time(jd_val):
                if not jd_val: return None
                year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
                dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                
                if timezone.startswith('UTC'):
                    # Simple offset calculation
                    dt_local = dt_utc + timedelta(hours=tz_offset)
                else:
                    # Use pytz for proper DST handling
                    try:
                        local_tz = pytz.timezone(timezone)
                        dt_utc_aware = pytz.utc.localize(dt_utc)
                        dt_local = dt_utc_aware.astimezone(local_tz)
                    except:
                        dt_local = dt_utc + timedelta(hours=tz_offset)
                
                return dt_local.strftime('%I:%M %p')
            
            return {
                'sunrise': jd_to_local_time(sunrise_jd),
                'sunset': jd_to_local_time(sunset_jd),
                'moonrise': jd_to_local_time(moonrise_jd),
                'moonset': jd_to_local_time(moonset_jd),
                'day_duration': (sunset_jd - sunrise_jd) * 24 if sunrise_jd and sunset_jd else None
            }
            
        except Exception:
            return {
                'sunrise': None,
                'sunset': None,
                'moonrise': None,
                'moonset': None,
                'day_duration': None
            }
    
    def _calculate_special_times(self, date_str: str, latitude: float, longitude: float, sunrise_sunset: Dict, timezone: str = None) -> Dict[str, Any]:
        """Calculate Rahu Kaal, Gulikai Kalam, Yamaganda with dynamic muhurta windows"""
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
        
        if not sunrise_sunset['sunrise'] or not sunrise_sunset['sunset']:
            return {}
        
        # Parse sunrise time
        sunrise_time = datetime.strptime(f"{date_str} {sunrise_sunset['sunrise']}", '%Y-%m-%d %I:%M %p')
        day_duration = sunrise_sunset['day_duration']
        
        if not day_duration:
            return {}
        
        # Dynamic muhurta calculation (1/15th of actual day duration)
        muhurta_duration = day_duration / 15
        
        # Each Rahu Kaal period is 1/8 of day duration (Drik standard)
        period_duration = day_duration / 8
        
        # Rahu Kaal periods (0=Sunday, 1=Monday, etc.)
        rahu_periods = {0: 7, 1: 0, 2: 5, 3: 3, 4: 2, 5: 4, 6: 1}  # Sunday to Saturday
        gulikai_periods = {0: 6, 1: 4, 2: 2, 3: 0, 4: 6, 5: 2, 6: 4}
        yamaganda_periods = {0: 4, 1: 2, 2: 0, 3: 6, 4: 4, 5: 0, 6: 2}
        
        # Convert weekday (Monday=0) to (Sunday=0)
        sunday_weekday = (weekday + 1) % 7
        
        def calculate_period_time(period_num):
            start_time = sunrise_time + timedelta(hours=period_num * period_duration)
            end_time = start_time + timedelta(hours=period_duration)
            return {
                'start': start_time.strftime('%I:%M %p'),
                'end': end_time.strftime('%I:%M %p')
            }
        
        # Calculate Abhijit Muhurta (8th muhurta - middle of day)
        abhijit_start = sunrise_time + timedelta(hours=7 * muhurta_duration)
        abhijit_end = abhijit_start + timedelta(hours=muhurta_duration)
        
        # Calculate Dur Muhurtam (inauspicious periods - 1/15th each)
        dur_muhurta_1_start = sunrise_time + timedelta(hours=2 * muhurta_duration)
        dur_muhurta_1_end = dur_muhurta_1_start + timedelta(hours=muhurta_duration)
        
        dur_muhurta_2_start = sunrise_time + timedelta(hours=13 * muhurta_duration)
        dur_muhurta_2_end = dur_muhurta_2_start + timedelta(hours=muhurta_duration)
        
        # Calculate Amrit Kalam (auspicious periods - 1/15th each)
        amrit_1_start = sunrise_time + timedelta(hours=4 * muhurta_duration)
        amrit_1_end = amrit_1_start + timedelta(hours=muhurta_duration)
        
        # Calculate Varjyam (avoid specific activities - 1/15th)
        varjyam_start = sunrise_time + timedelta(hours=11 * muhurta_duration)
        varjyam_end = varjyam_start + timedelta(hours=muhurta_duration)
        
        return {
            'rahu_kalam': calculate_period_time(rahu_periods[sunday_weekday]),
            'gulikai_kalam': calculate_period_time(gulikai_periods[sunday_weekday]),
            'yamaganda': calculate_period_time(yamaganda_periods[sunday_weekday]),
            'abhijit': {
                'start': abhijit_start.strftime('%I:%M %p'),
                'end': abhijit_end.strftime('%I:%M %p')
            },
            'dur_muhurtam': [
                {
                    'start': dur_muhurta_1_start.strftime('%I:%M %p'),
                    'end': dur_muhurta_1_end.strftime('%I:%M %p')
                },
                {
                    'start': dur_muhurta_2_start.strftime('%I:%M %p'),
                    'end': dur_muhurta_2_end.strftime('%I:%M %p')
                }
            ],
            'amrit_kalam': [
                {
                    'start': amrit_1_start.strftime('%I:%M %p'),
                    'end': amrit_1_end.strftime('%I:%M %p')
                }
            ],
            'varjyam': {
                'start': varjyam_start.strftime('%I:%M %p'),
                'end': varjyam_end.strftime('%I:%M %p')
            },
            'muhurta_duration_hours': muhurta_duration
        }
    
    def _calculate_calendar_info(self, date_obj: datetime, jd: float) -> Dict[str, Any]:
        """Calculate Samvats and calendar information with Adhika Maas detection"""
        
        # Shaka Samvat (starts from 78 CE)
        shaka_year = date_obj.year - 78
        
        # Vikram Samvat (starts from 57 BCE)
        vikram_year = date_obj.year + 57
        
        # Gujarati Samvat (similar to Vikram but different new year)
        gujarati_year = date_obj.year + 56
        
        # Calculate lunar month names using New Moon detection (like festival_calculator.py)
        lunar_months_amanta = [
            'Chaitra', 'Vaisakha', 'Jyeshtha', 'Ashadha', 'Shravana', 'Bhadrapada',
            'Ashwina', 'Kartika', 'Margashirsha', 'Pausha', 'Magha', 'Phalguna'
        ]
        
        # Find the New Moon (Amavasya) for this month
        amanta_month, is_adhika = self._get_lunar_month_from_new_moon(jd)
        purnimanta_month = amanta_month  # Simplified for now
        
        # Calculate Paksha (lunar fortnight)
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        tithi_deg = (moon_pos - sun_pos) % 360
        
        paksha = 'Shukla Paksha' if tithi_deg < 180 else 'Krishna Paksha'
        
        # Year names (simplified cycle)
        year_names = [
            'Prabhava', 'Vibhava', 'Shukla', 'Pramodoota', 'Prajotpatti', 'Angirasa',
            'Shrimukha', 'Bhava', 'Yuva', 'Dhatr', 'Ishvara', 'Bahudhanya',
            'Pramathi', 'Vikrama', 'Vrisha', 'Chitrabhanu', 'Subhanu', 'Tarana',
            'Parthiva', 'Vyaya', 'Sarvajit', 'Sarvadharin', 'Virodhin', 'Vikrita',
            'Khara', 'Nandana', 'Vijaya', 'Jaya', 'Manmatha', 'Durmukhi',
            'Hemalamba', 'Vilamba', 'Vikarin', 'Sharvari', 'Plava', 'Shubhakrit',
            'Sobhakrit', 'Krodhin', 'Vishvavasu', 'Parabhava', 'Plavanga', 'Kilaka',
            'Saumya', 'Sadharana', 'Virodhikrit', 'Paridhavi', 'Pramadin', 'Ananda',
            'Rakshasa', 'Nala', 'Pingala', 'Kalayukta', 'Siddharthi', 'Raudra',
            'Durmati', 'Dundubhi', 'Rudhirodgarin', 'Raktakshi', 'Krodhana', 'Akshaya'
        ]
        
        shaka_year_name = year_names[(shaka_year - 1) % 60]
        vikram_year_name = year_names[(vikram_year - 1) % 60]
        
        # Add Adhika prefix if leap month
        month_display = f"Adhika {lunar_months_amanta[amanta_month]}" if is_adhika else lunar_months_amanta[amanta_month]
        
        return {
            'shaka_samvat': f"{shaka_year} {shaka_year_name}",
            'vikram_samvat': f"{vikram_year} {vikram_year_name}",
            'gujarati_samvat': f"{gujarati_year} Nala",
            'amanta_month': month_display,
            'purnimanta_month': month_display,
            'paksha': paksha,
            'is_adhika_month': is_adhika
        }
    
    def _get_lunar_month_from_new_moon(self, jd: float) -> tuple:
        """Determine lunar month by finding New Moon and checking Sun's sign (prevents 2026 disaster)"""
        # Find the most recent New Moon
        search_jd = jd
        for _ in range(35):  # Search up to 35 days back
            sun_pos = swe.calc_ut(search_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            moon_pos = swe.calc_ut(search_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            tithi_deg = (moon_pos - sun_pos) % 360
            
            # Check if this is New Moon (tithi near 0 or 360)
            if tithi_deg < 6 or tithi_deg > 354:
                # Found New Moon - check Sun's sign
                sun_sign = int(sun_pos / 30)
                
                # Check for Adhika Maas (Sun in same sign for two consecutive New Moons)
                prev_new_moon_jd = search_jd - 29.5  # Approximate previous New Moon
                prev_sun_pos = swe.calc_ut(prev_new_moon_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
                prev_sun_sign = int(prev_sun_pos / 30)
                
                is_adhika = (sun_sign == prev_sun_sign)
                
                return sun_sign, is_adhika
            
            search_jd -= 1  # Go back one day
        
        # Fallback to solar month if New Moon not found
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        return int(sun_pos / 30), False
    
    def _calculate_moon_info(self, jd: float) -> Dict[str, Any]:
        """Calculate moon sign and other lunar information"""
        
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        
        # Moon sign
        moon_sign_num = int(moon_pos / 30)
        moon_signs = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
                     'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena']
        
        # Sun sign
        sun_sign_num = int(sun_pos / 30)
        
        return {
            'moon_sign': moon_signs[moon_sign_num],
            'sun_sign': moon_signs[sun_sign_num]
        }
    
    def _calculate_planetary_signs(self, jd: float) -> Dict[str, Any]:
        """Calculate current signs of all planets with degrees, retrograde and combustion status"""
        
        signs = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
                'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena']
        
        planets = {
            'Sun': swe.SUN,
            'Moon': swe.MOON,
            'Mars': swe.MARS,
            'Mercury': swe.MERCURY,
            'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS,
            'Saturn': swe.SATURN
        }
        
        planetary_data = {}
        sun_longitude = None
        
        for planet_name, planet_id in planets.items():
            try:
                # Get position with speed for retrograde detection
                planet_data = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
                planet_pos = planet_data[0][0]
                planet_speed = planet_data[0][3]  # Daily motion in degrees
                
                sign_num = int(planet_pos / 30)
                degree_in_sign = planet_pos % 30
                
                # Store Sun's position for combustion calculations
                if planet_name == 'Sun':
                    sun_longitude = planet_pos
                
                # Check if retrograde (negative speed)
                is_retrograde = planet_speed < 0
                
                # Check combustion (within 8 degrees of Sun, except Moon)
                is_combust = False
                if sun_longitude is not None and planet_name != 'Sun' and planet_name != 'Moon':
                    angular_distance = abs(planet_pos - sun_longitude)
                    if angular_distance > 180:
                        angular_distance = 360 - angular_distance
                    is_combust = angular_distance < 8
                
                planetary_data[planet_name] = {
                    'sign': signs[sign_num],
                    'sign_number': sign_num,
                    'degree': round(degree_in_sign, 2),
                    'longitude': round(planet_pos, 2),
                    'speed': round(planet_speed, 4),
                    'is_retrograde': is_retrograde,
                    'is_combust': is_combust
                }
                
            except Exception as e:
                planetary_data[planet_name] = {
                    'sign': 'Unknown',
                    'sign_number': 0,
                    'degree': 0,
                    'longitude': 0,
                    'speed': 0,
                    'is_retrograde': False,
                    'is_combust': False
                }
        
        # Second pass to calculate combustion for all planets now that we have Sun's position
        if sun_longitude is not None:
            for planet_name in planetary_data:
                if planet_name != 'Sun' and planet_name != 'Moon':
                    planet_pos = planetary_data[planet_name]['longitude']
                    angular_distance = abs(planet_pos - sun_longitude)
                    if angular_distance > 180:
                        angular_distance = 360 - angular_distance
                    planetary_data[planet_name]['is_combust'] = angular_distance < 8
        
        return planetary_data
    
    def _jd_to_time_string(self, jd: float, timezone: str = None) -> str:
        """Convert Julian Day to time string with proper timezone handling using pytz"""
        if not jd:
            return None
            
        try:
            # Convert to UTC
            year, month, day, hour, minute, second = swe.jdut1_to_utc(jd, 1)
            dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            
            # Handle timezone conversion
            if timezone.startswith('UTC'):
                # Simple offset calculation
                tz_offset = self._parse_timezone(timezone)
                dt_local = dt_utc + timedelta(hours=tz_offset)
            else:
                # Use pytz for proper DST handling
                try:
                    local_tz = pytz.timezone(timezone)
                    dt_utc_aware = pytz.utc.localize(dt_utc)
                    dt_local = dt_utc_aware.astimezone(local_tz)
                except:
                    dt_local = dt_utc + timedelta(hours=0.0)  # Fallback to UTC
            
            return dt_local.strftime('%I:%M %p')
        except:
            return None