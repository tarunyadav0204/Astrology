import swisseph as swe
from datetime import datetime, timedelta
import calendar
from typing import Dict, List, Any
from .panchang_calculator import PanchangCalculator

class MonthlyPanchangCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.panchang_calc = PanchangCalculator()
    
    def calculate_monthly_panchang(self, year: int, month: int, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate complete panchang for entire month"""
        
        # Get number of days in month
        days_in_month = calendar.monthrange(year, month)[1]
        
        monthly_data = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'days': [],
            'location': {'latitude': latitude, 'longitude': longitude}
        }
        
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            daily_data = self.calculate_daily_panchang(date_str, latitude, longitude)
            monthly_data['days'].append(daily_data)
        
        return monthly_data
    
    def calculate_daily_panchang(self, date_str: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate detailed panchang for a single day"""
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 12.0)
        
        # Basic panchang elements
        basic_panchang = self.panchang_calc.calculate_panchang(date_str, latitude, longitude, 5.5)
        
        # Calculate sunrise/sunset
        sunrise_sunset = self._calculate_sunrise_sunset(date_str, latitude, longitude)
        
        # Calculate special times
        special_times = self._calculate_special_times(date_str, latitude, longitude, sunrise_sunset)
        
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
            'planetary_signs': planetary_signs
        }
    
    def _calculate_sunrise_sunset(self, date_str: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate sunrise, sunset, moonrise, moonset"""
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 0.0)
        
        geopos = [longitude, latitude, 0.0]
        
        try:
            # Calculate sunrise
            sunrise_result = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)
            
            # Calculate moonrise/moonset
            moonrise_result = swe.rise_trans(jd, swe.MOON, swe.CALC_RISE, geopos)
            moonset_result = swe.rise_trans(jd, swe.MOON, swe.CALC_SET, geopos)
            
            sunrise_jd = sunrise_result[1][0] if sunrise_result[0] == 0 else None
            sunset_jd = sunset_result[1][0] if sunset_result[0] == 0 else None
            moonrise_jd = moonrise_result[1][0] if moonrise_result[0] == 0 else None
            moonset_jd = moonset_result[1][0] if moonset_result[0] == 0 else None
            
            return {
                'sunrise': self._jd_to_time_string(sunrise_jd) if sunrise_jd else None,
                'sunset': self._jd_to_time_string(sunset_jd) if sunset_jd else None,
                'moonrise': self._jd_to_time_string(moonrise_jd) if moonrise_jd else None,
                'moonset': self._jd_to_time_string(moonset_jd) if moonset_jd else None,
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
    
    def _calculate_special_times(self, date_str: str, latitude: float, longitude: float, sunrise_sunset: Dict) -> Dict[str, Any]:
        """Calculate Rahu Kaal, Gulikai Kalam, Yamaganda, etc."""
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
        
        if not sunrise_sunset['sunrise'] or not sunrise_sunset['sunset']:
            return {}
        
        # Parse sunrise time
        sunrise_time = datetime.strptime(f"{date_str} {sunrise_sunset['sunrise']}", '%Y-%m-%d %I:%M %p')
        day_duration = sunrise_sunset['day_duration']
        
        if not day_duration:
            return {}
        
        # Each period is 1/8 of day duration
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
        
        # Calculate Abhijit Muhurta (middle 1/15th of day)
        muhurta_duration = day_duration / 15
        abhijit_start = sunrise_time + timedelta(hours=7 * muhurta_duration)  # 8th muhurta
        abhijit_end = abhijit_start + timedelta(hours=muhurta_duration)
        
        # Calculate Dur Muhurtam (simplified - 2 periods per day)
        dur_muhurta_1_start = sunrise_time + timedelta(hours=2.5 * period_duration)
        dur_muhurta_1_end = dur_muhurta_1_start + timedelta(hours=period_duration * 0.6)
        
        dur_muhurta_2_start = sunrise_time + timedelta(hours=22)  # Late night
        dur_muhurta_2_end = dur_muhurta_2_start + timedelta(hours=0.8)
        
        # Calculate Amrit Kalam (auspicious periods)
        amrit_1_start = sunrise_time + timedelta(hours=3.2 * period_duration)
        amrit_1_end = amrit_1_start + timedelta(hours=1.5)
        
        # Calculate Varjyam (inauspicious for specific activities)
        varjyam_start = sunrise_time + timedelta(hours=13.5)
        varjyam_end = varjyam_start + timedelta(hours=1.6)
        
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
            }
        }
    
    def _calculate_calendar_info(self, date_obj: datetime, jd: float) -> Dict[str, Any]:
        """Calculate Samvats and calendar information"""
        
        # Shaka Samvat (starts from 78 CE)
        shaka_year = date_obj.year - 78
        
        # Vikram Samvat (starts from 57 BCE)
        vikram_year = date_obj.year + 57
        
        # Gujarati Samvat (similar to Vikram but different new year)
        gujarati_year = date_obj.year + 56
        
        # Calculate lunar month names
        lunar_months_amanta = [
            'Chaitra', 'Vaisakha', 'Jyeshtha', 'Ashadha', 'Shravana', 'Bhadrapada',
            'Ashwina', 'Kartika', 'Margashirsha', 'Pausha', 'Magha', 'Phalguna'
        ]
        
        lunar_months_purnimanta = [
            'Chaitra', 'Vaisakha', 'Jyeshtha', 'Ashadha', 'Shravana', 'Bhadrapada',
            'Ashwina', 'Kartika', 'Margashirsha', 'Pausha', 'Magha', 'Phalguna'
        ]
        
        # Simplified lunar month calculation
        amanta_month = lunar_months_amanta[(date_obj.month - 1) % 12]
        purnimanta_month = lunar_months_purnimanta[(date_obj.month - 1) % 12]
        
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
        
        return {
            'shaka_samvat': f"{shaka_year} {shaka_year_name}",
            'vikram_samvat': f"{vikram_year} {vikram_year_name}",
            'gujarati_samvat': f"{gujarati_year} Nala",
            'amanta_month': amanta_month,
            'purnimanta_month': purnimanta_month,
            'paksha': paksha
        }
    
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
    
    def _calculate_planetary_signs(self, jd: float) -> Dict[str, str]:
        """Calculate current signs of all planets"""
        
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
        
        planetary_signs = {}
        
        for planet_name, planet_id in planets.items():
            try:
                planet_pos = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)[0][0]
                sign_num = int(planet_pos / 30)
                planetary_signs[planet_name] = signs[sign_num]
            except:
                planetary_signs[planet_name] = 'Unknown'
        
        return planetary_signs
    
    def _jd_to_time_string(self, jd: float) -> str:
        """Convert Julian Day to time string in IST"""
        if not jd:
            return None
            
        try:
            # Convert to UTC
            year, month, day, hour, minute, second = swe.jdut1_to_utc(jd, 1)
            dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            
            # Convert to IST (UTC+5:30)
            dt_ist = dt_utc + timedelta(hours=5, minutes=30)
            
            return dt_ist.strftime('%I:%M %p')
        except:
            return None