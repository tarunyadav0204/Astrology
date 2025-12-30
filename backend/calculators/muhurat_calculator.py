import swisseph as swe
from datetime import datetime, timedelta
import pytz
from .panchang_calculator import PanchangCalculator
from utils.timezone_service import get_timezone_from_coordinates

class MuhuratCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.panchang_calc = PanchangCalculator()
        
        self.CHILDBIRTH_NAKSHATRAS = [4, 5, 7, 8, 12, 13, 14, 15, 17, 21, 22, 23, 24, 26, 27]
        self.VEHICLE_NAKSHATRAS = [1, 4, 5, 7, 8, 13, 14, 15, 17, 22, 23, 24, 27]
        self.HOME_NAKSHATRAS = [4, 5, 12, 14, 17, 21, 26, 27]
        self.GOLD_NAKSHATRAS = [1, 4, 7, 8, 12, 13, 14, 15, 17, 21, 22, 23, 27]
        self.BUSINESS_NAKSHATRAS = [1, 4, 5, 8, 12, 13, 14, 17, 21, 26, 27]

        self.AVOID_TITHIS = [4, 9, 14, 30]
        self.AVOID_YOGAS = [1, 6, 9, 10, 13, 15, 17, 19, 27]
        
        self.GOOD_CHOGHADIYA = ['Amrita', 'Shubh', 'Labh', 'Char']
    
    def _parse_timezone(self, tz_str):
        """Helper to parse timezone string like 'UTC+5:30' into float offset"""
        offset = 5.5 # Default IST
        if isinstance(tz_str, (int, float)):
            return float(tz_str)
        if isinstance(tz_str, str) and 'UTC' in tz_str:
            try:
                tz_part = tz_str.replace('UTC', '')
                sign = -1 if '-' in tz_part else 1
                tz_part = tz_part.replace('+', '').replace('-', '')
                
                if ':' in tz_part:
                    hours, minutes = tz_part.split(':')
                    offset = sign * (float(hours) + float(minutes)/60.0)
                else:
                    offset = sign * float(tz_part)
            except: pass
        return offset

    def _jd_to_local_time(self, jd_val, timezone_str):
        """Convert Julian Day to local time with proper timezone handling"""
        if not jd_val: return None
        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
        dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=pytz.UTC)
        
        # Parse timezone
        if timezone_str.startswith('UTC'):
            tz_offset = self._parse_timezone(timezone_str)
            dt_local = dt_utc + timedelta(hours=tz_offset)
        else:
            try:
                tz = pytz.timezone(timezone_str)
                dt_local = dt_utc.astimezone(tz)
            except:
                tz_offset = self._parse_timezone(timezone_str)
                dt_local = dt_utc + timedelta(hours=tz_offset)
        
        return dt_local.strftime('%I:%M %p')

    def calculate_childbirth_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz = get_timezone_from_coordinates(lat, lon)
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.CHILDBIRTH_NAKSHATRAS, [1, 2, 3, 4, 5, 6, 8, 11], [], "Childbirth")

    def calculate_vehicle_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        # Auto-detect timezone if not provided
        if tz is None:
            tz = get_timezone_from_coordinates(lat, lon)
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.VEHICLE_NAKSHATRAS, [0, 3, 6, 9], [1], "Vehicle Purchase",
            check_4th_house=True, karaka_planet=swe.VENUS)

    def calculate_griha_pravesh_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz = get_timezone_from_coordinates(lat, lon)
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.HOME_NAKSHATRAS, [1, 4, 7, 10], [1, 6], "Griha Pravesh",
            check_4th_house=True, karaka_planet=swe.MARS)

    def calculate_gold_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz = get_timezone_from_coordinates(lat, lon)
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.GOLD_NAKSHATRAS, [1, 2, 3, 4, 5, 6, 8, 11], [1], "Gold Purchase")

    def calculate_business_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz = get_timezone_from_coordinates(lat, lon)
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.BUSINESS_NAKSHATRAS, [1, 4, 7, 10], [1, 6], "Business Opening",
            check_4th_house=True)

    def _generic_muhurat_search(self, start_str, end_str, lat, lon, user_nak, tz_str, 
                              good_nakshatras, good_lagnas, avoid_weekdays, category,
                              check_4th_house=False, karaka_planet=None):
        try:
            if 'T' in start_str: start_str = start_str.split('T')[0]
            if 'T' in end_str: end_str = end_str.split('T')[0]
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
        except ValueError:
            return {"error": "Invalid date format"}

        valid_slots = []
        current_date = start_date
        days_scanned = 0
        
        # Use timezone string directly for proper DST handling
        timezone_str = tz_str

        while current_date <= end_date and days_scanned < 60:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if current_date.weekday() in avoid_weekdays:
                current_date += timedelta(days=1); days_scanned += 1; continue

            try:
                # 2. Panchang Check (Pass all args)
                panchang = self.panchang_calc.calculate_panchang(
                    date_str, 
                    "12:00:00", 
                    float(lat), 
                    float(lon), 
                    tz_str
                )
            except Exception as e:
                print(f"Panchang Error for {date_str}: {e}")
                current_date += timedelta(days=1); days_scanned += 1; continue

            if panchang['tithi']['number'] in self.AVOID_TITHIS:
                current_date += timedelta(days=1); days_scanned += 1; continue
            
            if panchang['yoga']['number'] in self.AVOID_YOGAS:
                current_date += timedelta(days=1); days_scanned += 1; continue
            
            if panchang.get('karana', {}).get('name') == 'Vishti':
                current_date += timedelta(days=1); days_scanned += 1; continue

            daily_nak = panchang['nakshatra']['number']
            if daily_nak not in good_nakshatras:
                current_date += timedelta(days=1); days_scanned += 1; continue
                
            dist = (daily_nak - user_nak) 
            if dist < 0: dist += 27
            tara_score = (dist + 1) % 9
            if tara_score == 0: tara_score = 9
            if tara_score in [1, 3, 5, 7]:
                current_date += timedelta(days=1); days_scanned += 1; continue

            # 4. Planetary Positions
            planet_positions = {}
            if check_4th_house or karaka_planet:
                # Calculate JD for noon in UTC (no timezone offset needed for planetary positions)
                jd_noon = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
                
                if karaka_planet:
                    karaka_pos = swe.calc_ut(jd_noon, karaka_planet, swe.FLG_SIDEREAL)[0][0]
                    sun_pos = swe.calc_ut(jd_noon, swe.SUN, swe.FLG_SIDEREAL)[0][0]
                    if abs(sun_pos - karaka_pos) < 6:
                         current_date += timedelta(days=1); days_scanned += 1; continue

                malefics = [0, 4, 6, 11, 12]
                occupied_signs = set()
                for p in malefics:
                    pos = swe.calc_ut(jd_noon, p, swe.FLG_SIDEREAL)[0][0]
                    sign = int(pos / 30)
                    occupied_signs.add(sign)
                planet_positions['malefics_in'] = occupied_signs

            # 5. Choghadiya (Pass TZ)
            try:
                choghadiya_data = self.panchang_calc.calculate_choghadiya(date_str, lat, lon, timezone=tz_str)
            except:
                choghadiya_data = None

            # 6. Fine-Grained Search with timezone
            day_slots = self._find_lagnas_detailed(
                current_date, float(lat), float(lon), timezone_str, 
                good_lagnas, planet_positions if check_4th_house else None,
                choghadiya_data
            )
            
            if day_slots:
                valid_slots.append({
                    'date': date_str,
                    'weekday': panchang['vara']['name'],
                    'nakshatra': panchang['nakshatra']['name'],
                    'tara_quality': 'Excellent' if tara_score in [2,4,6,8,9] else 'Average',
                    'slots': day_slots
                })
            
            current_date += timedelta(days=1)
            days_scanned += 1
            
        return {
            "category": category,
            "period": f"{start_str} to {end_str}",
            "dates_found": len(valid_slots),
            "recommendations": valid_slots
        }

    def _find_lagnas_detailed(self, date_obj, lat, lon, timezone_str, good_lagnas, planet_positions, choghadiya_data):
        jd = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 12.0)
        geopos = (float(lon), float(lat), 0.0)
        
        rise = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)[1][0]
        setting = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)[1][0]
        
        sunrise_hour = self._jd_to_local_hour(rise, timezone_str)
        sunset_hour = self._jd_to_local_hour(setting, timezone_str)
        
        day_duration = sunset_hour - sunrise_hour
        if day_duration < 0: day_duration += 24 
        
        weekday = date_obj.weekday()
        rahu_map = {0: 1, 1: 6, 2: 4, 3: 5, 4: 3, 5: 2, 6: 7} 
        yama_map = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 5, 6: 6}
        gulika_map = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

        def get_window(idx, is_day=True):
            duration = day_duration if is_day else (24-day_duration)
            start_base = sunrise_hour if is_day else sunset_hour
            one_part = duration / 8
            s = start_base + (idx * one_part)
            return (s, s + one_part)

        rahu = get_window(rahu_map[weekday])
        yama = get_window(yama_map[weekday])
        gulika = get_window(gulika_map[weekday])

        def is_forbidden(t):
            # Check range considering day wrap
            def in_range(val, r): return r[0] <= val < r[1]
            return in_range(t, rahu) or in_range(t, yama) or in_range(t, gulika)
        
        # Find good time slots
        slots = []
        for hour in range(int(sunrise_hour), int(sunset_hour) + 1):
            if is_forbidden(hour): continue
            
            # Calculate lagna for this hour
            tz_offset = self._parse_timezone(timezone_str)
            jd_hour = swe.julday(date_obj.year, date_obj.month, date_obj.day, hour - tz_offset)
            asc = swe.houses(jd_hour, lat, lon, b'P')[1][0]  # Placidus houses
            lagna_sign = int(asc / 30)
            
            if lagna_sign not in good_lagnas: continue
            
            # Check 4th house if required
            if planet_positions and 3 in planet_positions.get('malefics_in', set()):
                continue
            
            # Check choghadiya if available
            if choghadiya_data:
                hour_str = f"{hour:02d}:00"
                is_good_chog = any(
                    slot['name'] in self.GOOD_CHOGHADIYA and 
                    slot['start_time'] <= hour_str < slot['end_time']
                    for slot in choghadiya_data.get('day_choghadiya', [])
                )
                if not is_good_chog: continue
            
            slots.append({
                'time': self._jd_to_local_time(jd_hour + tz_offset/24, timezone_str),
                'lagna': ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][lagna_sign],
                'quality': 'Excellent'
            })
        
        return slots
    
    def _jd_to_local_hour(self, jd_val, timezone_str):
        """Convert JD to local hour with timezone handling"""
        if not jd_val: return 0
        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
        dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=pytz.UTC)
        
        if timezone_str.startswith('UTC'):
            tz_offset = self._parse_timezone(timezone_str)
            dt_local = dt_utc + timedelta(hours=tz_offset)
        else:
            try:
                tz = pytz.timezone(timezone_str)
                dt_local = dt_utc.astimezone(tz)
            except:
                tz_offset = self._parse_timezone(timezone_str)
                dt_local = dt_utc + timedelta(hours=tz_offset)
        
        return dt_local.hour + dt_local.minute/60.0