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
        
        # Basic panchang elements at local sunrise (Hindu day)
        basic_panchang = self.panchang_calc.calculate_panchang(
            date_str, latitude, longitude, timezone, reference="sunrise"
        )

        # Calculate sunrise/sunset with timezone
        sunrise_sunset = self._calculate_sunrise_sunset(date_str, latitude, longitude, timezone)

        # Calculate special times with timezone (needs nakshatra window for Varjyam/Amrit)
        special_times = self._calculate_special_times(
            date_str, latitude, longitude, sunrise_sunset, timezone, basic_panchang=basic_panchang
        )
        
        # Calculate samvats and calendar info
        calendar_info = self._calculate_calendar_info(date_obj, jd)
        
        # Calculate moon info
        moon_info = self._calculate_moon_info(jd)
        
        # Calculate planetary positions for signs
        planetary_signs = self._calculate_planetary_signs(jd)

        # Ritu / Ayana / Chandra Balam (day-level polish; Tara needs birth nakshatra)
        day_context = self._calculate_day_context(jd, basic_panchang)
        
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
            'day_context': day_context,
            'timezone': timezone
        }
    
    def _calculate_sunrise_sunset(self, date_str: str, latitude: float, longitude: float, timezone: str = None) -> Dict[str, Any]:
        """Delegate sun/moon rise-set to shared Swiss Ephemeris calculator (Drik-aligned moon day)."""
        from calculators.panchang_calculator import PanchangCalculator as RiseCalc

        try:
            raw = RiseCalc().get_local_sunrise_sunset(
                date_str, latitude, longitude, timezone or "UTC+0"
            )

            def fmt_clock(iso_val):
                if not iso_val:
                    return None
                return datetime.fromisoformat(str(iso_val)).strftime('%I:%M %p')

            return {
                'sunrise': fmt_clock(raw.get('sunrise')),
                'sunset': fmt_clock(raw.get('sunset')),
                'moonrise': fmt_clock(raw.get('moonrise')),
                'moonset': fmt_clock(raw.get('moonset')),
                'moonrise_iso': raw.get('moonrise'),
                'moonset_iso': raw.get('moonset'),
                'day_duration': raw.get('day_duration'),
            }
        except Exception:
            return {
                'sunrise': None,
                'sunset': None,
                'moonrise': None,
                'moonset': None,
                'day_duration': None,
            }
    
    def _calculate_special_times(self, date_str: str, latitude: float, longitude: float, sunrise_sunset: Dict, timezone: str = None, basic_panchang: Dict = None) -> Dict[str, Any]:
        """Calculate Rahu Kaal, Gulikai, Yamaganda, Dur Muhurta, Varjyam, Amrit Kalam."""

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date_obj.weekday()  # 0=Monday, 6=Sunday

        if not sunrise_sunset.get('sunrise') or not sunrise_sunset.get('sunset'):
            return {}

        sunrise_time = datetime.strptime(f"{date_str} {sunrise_sunset['sunrise']}", '%Y-%m-%d %I:%M %p')
        day_duration = sunrise_sunset.get('day_duration')
        if not day_duration:
            return {}

        muhurta_duration = day_duration / 15.0
        period_duration = day_duration / 8.0

        # Daylight eighths from local sunrise; Sunday=0 maps.
        rahu_periods = {0: 7, 1: 1, 2: 6, 3: 4, 4: 5, 5: 3, 6: 2}
        gulikai_periods = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0}
        yamaganda_periods = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 6, 6: 5}
        sunday_weekday = (weekday + 1) % 7

        def calculate_period_time(period_num):
            start_time = sunrise_time + timedelta(hours=period_num * period_duration)
            end_time = start_time + timedelta(hours=period_duration)
            return {
                'start': start_time.strftime('%I:%M %p'),
                'end': end_time.strftime('%I:%M %p')
            }

        # Abhijit = 8th daytime muhurta (middle of day)
        abhijit_start = sunrise_time + timedelta(hours=7 * muhurta_duration)
        abhijit_end = abhijit_start + timedelta(hours=muhurta_duration)

        # Classical Dur Muhurta by weekday (BV Raman / Muhurta Chintamani), 1-based muhurtas from sunrise.
        # Sunday: 14; Monday: 8,12; Tuesday: 4,11; Wednesday: 8 (Abhijit); Thursday: 12,13; Friday: 4,8; Saturday: 1,2
        # Drik / common practice: when muhurta 8 is listed but Abhijit is auspicious (not Wed),
        # shift that Dur window to muhurta 9 (immediately after Abhijit).
        dur_by_weekday_sun0 = {
            0: [14],
            1: [8, 12],
            2: [4, 11],
            3: [8],
            4: [12, 13],
            5: [4, 8],
            6: [1, 2],
        }
        dur_nums = list(dur_by_weekday_sun0.get(sunday_weekday, []))
        if 8 in dur_nums and sunday_weekday != 3:
            dur_nums = [9 if n == 8 else n for n in dur_nums]
        dur_muhurtam = []
        for muhurta_num in dur_nums:
            start = sunrise_time + timedelta(hours=(muhurta_num - 1) * muhurta_duration)
            end = start + timedelta(hours=muhurta_duration)
            dur_muhurtam.append({
                'start': start.strftime('%I:%M %p'),
                'end': end.strftime('%I:%M %p'),
                'muhurta': muhurta_num,
            })

        # Classical Tyajya / Varjyam: 4 ghatis from nakshatra start (ghati table).
        # Source: Muhurta texts (Ashwini=50 … Revati=30); duration = 4 ghatis.
        varjyam_start_ghati = [
            50, 4, 30, 40, 14, 21, 30, 20, 32, 30,
            20, 1, 21, 20, 14, 14, 10, 14, 20, 20,
            20, 10, 10, 18, 16, 30, 30,
        ]
        # Prashnamarga / common Amrita ghatika starts (4 ghatis).
        amrit_start_ghati = [
            42, 48, 54, 52, 38, 35, 54, 44, 56, 54,
            44, 43, 45, 44, 38, 38, 34, 38, 40, 42,
            42, 40, 40, 36, 38, 42, 42,
        ]

        hindu_day_end = sunrise_time + timedelta(hours=24)
        sunset_time = datetime.strptime(f"{date_str} {sunrise_sunset['sunset']}", '%Y-%m-%d %I:%M %p')
        if sunset_time <= sunrise_time:
            sunset_time += timedelta(days=1)

        def _parse_nak_window(nak: Dict) -> tuple:
            nak_num = int(nak.get('number') or 0)
            start_iso = nak.get('start_time')
            end_iso = nak.get('end_time')
            if not nak_num or not start_iso or not end_iso:
                return None
            try:
                nak_start = datetime.fromisoformat(start_iso)
                nak_end = datetime.fromisoformat(end_iso)
            except ValueError:
                return None
            if nak_end <= nak_start:
                nak_end += timedelta(days=1)
            return nak_num, nak_start, nak_end

        # Nakshatras active across the Hindu day (sunrise → next sunrise), not only sunrise star.
        # Drik's daytime Amrit/Varjyam often belong to the post-sunrise nakshatra (e.g. Ardra).
        nak_windows = []
        first = _parse_nak_window((basic_panchang or {}).get('nakshatra') or {})
        if first:
            nak_windows.append(first)
            cursor_end = first[2]
            while cursor_end < hindu_day_end and len(nak_windows) < 3:
                sample = cursor_end + timedelta(minutes=2)
                sample_date = sample.strftime('%Y-%m-%d')
                sample_time = sample.strftime('%H:%M:%S')
                try:
                    next_bp = self.panchang_calc.calculate_panchang(
                        sample_date, latitude, longitude, timezone or "UTC+0", time_str=sample_time
                    )
                    nxt = _parse_nak_window((next_bp or {}).get('nakshatra') or {})
                except Exception:
                    nxt = None
                if not nxt or nxt[0] == nak_windows[-1][0]:
                    break
                nak_windows.append(nxt)
                cursor_end = nxt[2]

        def periods_from_nakshatra_ghati(start_ghati_table):
            periods = []
            for nak_num, nak_start, nak_end in nak_windows:
                duration = nak_end - nak_start
                ghati = start_ghati_table[(nak_num - 1) % 27]
                start = nak_start + duration * (ghati / 60.0)
                end = start + duration * (4.0 / 60.0)
                # Keep windows that fall on this Hindu day.
                if end <= sunrise_time or start >= hindu_day_end:
                    continue
                periods.append({
                    'start': start.strftime('%I:%M %p'),
                    'end': end.strftime('%I:%M %p'),
                    'start_dt': start,
                    'end_dt': end,
                    'nakshatra_number': nak_num,
                })
            return periods

        def prefer_daytime(periods):
            if not periods:
                return []
            daytime = [
                p for p in periods
                if p['start_dt'] < sunset_time and p['end_dt'] > sunrise_time
            ]
            chosen = daytime or periods
            chosen = sorted(chosen, key=lambda p: p['start_dt'])
            return [{k: v for k, v in p.items() if k not in ('start_dt', 'end_dt')} for p in chosen]

        varjyam_periods = prefer_daytime(periods_from_nakshatra_ghati(varjyam_start_ghati))
        amrit_periods = prefer_daytime(periods_from_nakshatra_ghati(amrit_start_ghati))

        # Preserve prior response shape: varjyam as single object when one window.
        if varjyam_periods:
            varjyam = {k: v for k, v in varjyam_periods[0].items() if k != 'nakshatra_number'}
        else:
            # Fallback only if nakshatra timings missing
            fallback_start = sunrise_time + timedelta(hours=10 * muhurta_duration)
            varjyam = {
                'start': fallback_start.strftime('%I:%M %p'),
                'end': (fallback_start + timedelta(hours=muhurta_duration)).strftime('%I:%M %p'),
            }

        if not amrit_periods:
            amrit_fallback = sunrise_time + timedelta(hours=6 * muhurta_duration)
            amrit_periods = [{
                'start': amrit_fallback.strftime('%I:%M %p'),
                'end': (amrit_fallback + timedelta(hours=muhurta_duration)).strftime('%I:%M %p'),
            }]
        else:
            amrit_periods = [
                {k: v for k, v in p.items() if k != 'nakshatra_number'} for p in amrit_periods
            ]

        return {
            'rahu_kalam': calculate_period_time(rahu_periods[sunday_weekday]),
            'gulikai_kalam': calculate_period_time(gulikai_periods[sunday_weekday]),
            'yamaganda': calculate_period_time(yamaganda_periods[sunday_weekday]),
            'abhijit': {
                'start': abhijit_start.strftime('%I:%M %p'),
                'end': abhijit_end.strftime('%I:%M %p')
            },
            'dur_muhurtam': dur_muhurtam,
            'amrit_kalam': amrit_periods,
            'varjyam': varjyam,
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

    def _calculate_day_context(self, jd: float, basic_panchang: Dict) -> Dict[str, Any]:
        """Ritu, Ayana, and day-level Chandra Balam (Tara Balam needs birth nakshatra)."""
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        tithi_deg = (moon_pos - sun_pos) % 360

        # Sidereal solar months → classical 6 ritus (approx by sun sign)
        sun_sign = int(sun_pos / 30) % 12
        ritu_by_sign = [
            'Vasanta', 'Vasanta', 'Grishma', 'Grishma', 'Varsha', 'Varsha',
            'Sharad', 'Sharad', 'Hemanta', 'Hemanta', 'Shishira', 'Shishira',
        ]
        # Ayana: Uttarayana when Sun in Capricorn–Gemini (signs 9–2), else Dakshinayana
        ayana = 'Uttarayana' if sun_sign in (9, 10, 11, 0, 1, 2) else 'Dakshinayana'

        # Chandra Balam proxy without birth chart: strong in Shukla, weak near Amavasya
        if tithi_deg < 180:
            chandra_balam = {'status': 'Strong', 'paksha': 'Shukla', 'note': 'Waxing Moon supports growth-oriented work'}
        elif tithi_deg < 348:
            chandra_balam = {'status': 'Moderate', 'paksha': 'Krishna', 'note': 'Waning Moon favors completion and release'}
        else:
            chandra_balam = {'status': 'Weak', 'paksha': 'Krishna', 'note': 'Near Amavasya — prefer quiet / remedial work'}

        nak_num = int(((basic_panchang or {}).get('nakshatra') or {}).get('number') or 0)
        # Tara Balam requires janma nakshatra; expose scaffold for clients that pass birth later.
        tara_balam = {
            'available': False,
            'day_nakshatra_number': nak_num or None,
            'note': 'Provide birth nakshatra to compute Tara Balam (1–9 count from janma star)',
        }

        return {
            'ritu': ritu_by_sign[sun_sign],
            'ayana': ayana,
            'sun_sign_index': sun_sign,
            'chandra_balam': chandra_balam,
            'tara_balam': tara_balam,
        }
    
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
