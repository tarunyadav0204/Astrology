import swisseph as swe
from datetime import datetime, timedelta
from .base_calculator import BaseCalculator
from utils.timezone_service import parse_timezone_offset

class PanchangCalculator(BaseCalculator):
    """Extract panchang calculation logic"""
    
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        self.TITHI_NAMES = [
            'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami', 'Ashtami',
            'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima', 'Amavasya'
        ]
        
        self.VARA_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        self.NAKSHATRA_NAMES = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya',
            'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
            'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
            'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        self.YOGA_NAMES = [
            'Vishkumbha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda', 'Sukarma', 'Dhriti',
            'Shula', 'Ganda', 'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra', 'Siddhi',
            'Vyatipata', 'Variyan', 'Parigha', 'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla',
            'Brahma', 'Indra', 'Vaidhriti'
        ]
        
        self.KARANA_MOVABLE = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija', 'Vishti']

    def _parse_timezone(self, tz_str):
        """Helper to parse timezone string like 'UTC+0' into float offset"""
        offset = 0.0 # Default UTC
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
    
    def calculate_panchang(self, date_str, time_str="12:00:00", latitude=0.0, longitude=0.0, timezone=None):
        # Auto-detect timezone if not provided using centralized service
        if timezone is None and latitude != 0.0 and longitude != 0.0:
            tz_offset = parse_timezone_offset('', latitude, longitude)
            # Convert offset back to UTC format
            if tz_offset >= 0:
                timezone = f"UTC+{tz_offset}"
            else:
                timezone = f"UTC{tz_offset}"
        elif timezone is None:
            timezone = "UTC+0"  # Default fallback
        # Parse Date
        try:
            if 'T' in str(date_str): date_str = str(date_str).split('T')[0]
            year, month, day = map(int, str(date_str).split('-'))
        except:
            if hasattr(date_str, 'year'):
                year, month, day = date_str.year, date_str.month, date_str.day
            else:
                raise ValueError("Invalid date format")
        
        # Parse Time
        if isinstance(time_str, str):
            time_parts = time_str.split(':')
            h = int(time_parts[0])
            m = int(time_parts[1])
            s = int(time_parts[2]) if len(time_parts) > 2 else 0
            local_hour = h + (m / 60.0) + (s / 3600.0)
        else:
            local_hour = 12.0

        # Parse timezone
        tz_offset = self._parse_timezone(timezone)
        utc_hour = local_hour - tz_offset
        
        # Calculate Julian Day
        jd = swe.julday(year, month, day, utc_hour)
        
        # Get Positions
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        
        # Calculations
        tithi_deg = (moon_pos - sun_pos) % 360
        tithi_num = int(tithi_deg / 12) + 1
        
        paksha = "Shukla" if tithi_num <= 15 else "Krishna"
        if tithi_num == 15: tithi_name = "Purnima"
        elif tithi_num == 30: tithi_name = "Amavasya"
        else:
            idx = (tithi_num - 1) % 15
            tithi_name = self.TITHI_NAMES[idx]
        
        vara_index = int((jd + 1.5) % 7)
        
        nak_slice = 360 / 27
        nakshatra_index = int(moon_pos / nak_slice)
        nak_deg_remaining = (moon_pos % nak_slice)
        
        yoga_deg = (sun_pos + moon_pos) % 360
        yoga_index = int(yoga_deg / nak_slice)
        
        k_num = int(tithi_deg / 6) + 1
        if k_num == 1: karana_name = "Kimstughna"
        elif k_num >= 58:
            fixed_map = {58: "Shakuni", 59: "Chatushpada", 60: "Naga"}
            karana_name = fixed_map.get(k_num, "Naga")
        else:
            movable_idx = (k_num - 2) % 7
            karana_name = self.KARANA_MOVABLE[movable_idx]
        
        return {
            "tithi": {"number": tithi_num, "name": tithi_name, "paksha": paksha, "degrees_traversed": round(tithi_deg % 12, 2)},
            "vara": {"number": vara_index + 1, "name": self.VARA_NAMES[vara_index]},
            "nakshatra": {"number": nakshatra_index + 1, "name": self.NAKSHATRA_NAMES[nakshatra_index], "degrees_traversed": round(nak_deg_remaining, 2)},
            "yoga": {"number": yoga_index + 1, "name": self.YOGA_NAMES[yoga_index % 27], "degrees_traversed": round(yoga_deg % nak_slice, 2)},
            "karana": {"number": k_num, "name": karana_name}
        }
    
    def calculate_birth_panchang(self, birth_data):
        date_str = getattr(birth_data, 'date', None) or birth_data.get('date')
        time_str = getattr(birth_data, 'time', "12:00:00") or birth_data.get('time', "12:00:00")
        if hasattr(date_str, 'strftime'): date_str = date_str.strftime("%Y-%m-%d")
        
        lat = getattr(birth_data, 'latitude', 0.0) or birth_data.get('latitude', 0.0)
        lon = getattr(birth_data, 'longitude', 0.0) or birth_data.get('longitude', 0.0)
        tz = getattr(birth_data, 'timezone', "UTC+0") or birth_data.get('timezone', "UTC+0")

        return self.calculate_panchang(date_str, time_str, float(lat), float(lon), tz)
    
    def calculate_choghadiya(self, date_str, lat, lon, timezone="UTC+0"):
        """Calculate daily Choghadiya segments with dynamic timezone"""
        if 'T' in str(date_str): date_str = str(date_str).split('T')[0]
        year, month, day = map(int, str(date_str).split('-'))
        
        # Calculate Sunrise/Sunset (Geocentric, Noon UTC)
        jd = swe.julday(year, month, day, 12.0)
        
        geopos = (float(lon), float(lat), 0.0)
        rise = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)[1][0]
        setting = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)[1][0]
        
        # Use dynamic timezone parsing
        tz_offset = self._parse_timezone(timezone)
        
        rise_local = ((rise + 0.5 - int(rise + 0.5)) * 24.0 + tz_offset) % 24
        set_local = ((setting + 0.5 - int(setting + 0.5)) * 24.0 + tz_offset) % 24
        
        day_duration = set_local - rise_local
        if day_duration < 0: day_duration += 24
        
        night_duration = 24 - day_duration
        day_chunk = day_duration / 8
        night_chunk = night_duration / 8
        
        CHOG_NAMES = ["Udvega", "Amrita", "Roga", "Labha", "Shubha", "Chara", "Kala"]
        CHOG_QUALITIES = ["Bad", "Good", "Bad", "Gain", "Good", "Movable", "Bad"]
        weekday = int((jd + 1.5) % 7)  # 0=Sun
        
        # Day Slots
        day_slots = []
        curr = rise_local
        for i in range(8):
            end = curr + day_chunk
            idx = (weekday + i) % 7
            day_slots.append({
                "name": CHOG_NAMES[idx],
                "quality": CHOG_QUALITIES[idx],
                "start_time": f"{int(curr):02d}:{int((curr%1)*60):02d}",
                "end_time": f"{int(end):02d}:{int((end%1)*60):02d}"
            })
            curr = end
            
        # Night Slots
        night_slots = []
        night_start_idx = (weekday + 4) % 7
        
        curr = set_local
        for i in range(8):
            end = (curr + night_chunk) % 24
            idx = (night_start_idx + i) % 7
            night_slots.append({
                "name": CHOG_NAMES[idx],
                "quality": CHOG_QUALITIES[idx],
                "start_time": f"{int(curr):02d}:{int((curr%1)*60):02d}",
                "end_time": f"{int(end):02d}:{int((end%1)*60):02d}"
            })
            curr = end
            
        return {"day_choghadiya": day_slots, "night_choghadiya": night_slots}
    
    def get_local_sunrise_sunset(self, date_str, latitude, longitude, timezone="UTC+0"):
        """Professional sunrise/sunset using Swiss Ephemeris with atmospheric refraction"""
        if 'T' in str(date_str): date_str = str(date_str).split('T')[0]
        year, month, day = map(int, str(date_str).split('-'))
        
        jd = swe.julday(year, month, day, 0.0)
        geopos = [float(longitude), float(latitude), 0.0]
        
        # Use Swiss Ephemeris rise_trans for accurate calculations
        sunrise_result = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)
        sunset_result = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)
        moonrise_result = swe.rise_trans(jd, swe.MOON, swe.CALC_RISE, geopos)
        moonset_result = swe.rise_trans(jd, swe.MOON, swe.CALC_SET, geopos)
        
        tz_offset = self._parse_timezone(timezone)
        
        def jd_to_local_time(jd_val):
            if not jd_val: return None
            # Swiss Ephemeris returns JD in UTC
            # Convert JD directly to local time by adding timezone offset to JD
            local_jd = jd_val + (tz_offset / 24.0)  # Convert hours to days
            year, month, day, hour, minute, second = swe.jdut1_to_utc(local_jd, 1)
            dt_local = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            return dt_local
        
        sunrise_time = jd_to_local_time(sunrise_result[1][0]) if sunrise_result[0] == 0 else None
        sunset_time = jd_to_local_time(sunset_result[1][0]) if sunset_result[0] == 0 else None
        moonrise_time = jd_to_local_time(moonrise_result[1][0]) if moonrise_result[0] == 0 else None
        moonset_time = jd_to_local_time(moonset_result[1][0]) if moonset_result[0] == 0 else None
        
        # Calculate day duration using Swiss Ephemeris precision
        day_duration = (sunset_time - sunrise_time).total_seconds() / 3600 if sunrise_time and sunset_time else 12
        
        # Calculate dynamic muhurtas (1/15th of day duration)
        muhurta_duration = day_duration / 15
        
        # Calculate twilight times (approximate)
        civil_twilight_begin = sunrise_time - timedelta(minutes=30) if sunrise_time else None
        civil_twilight_end = sunset_time + timedelta(minutes=30) if sunset_time else None
        nautical_twilight_begin = sunrise_time - timedelta(hours=1) if sunrise_time else None
        nautical_twilight_end = sunset_time + timedelta(hours=1) if sunset_time else None
        astronomical_twilight_begin = sunrise_time - timedelta(hours=1.5) if sunrise_time else None
        astronomical_twilight_end = sunset_time + timedelta(hours=1.5) if sunset_time else None
        
        # Calculate special muhurtas
        brahma_start = sunrise_time - timedelta(hours=1.5) if sunrise_time else None
        brahma_end = sunrise_time - timedelta(minutes=48) if sunrise_time else None
        
        abhijit_start = sunrise_time + timedelta(hours=day_duration/2 - muhurta_duration/2) if sunrise_time else None
        abhijit_end = abhijit_start + timedelta(hours=muhurta_duration) if abhijit_start else None
        
        godhuli_start = sunset_time - timedelta(minutes=24) if sunset_time else None
        godhuli_end = sunset_time + timedelta(minutes=24) if sunset_time else None
        
        # Calculate moon phase and illumination
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        phase_angle = (moon_pos - sun_pos) % 360
        illumination = round((1 - abs(phase_angle - 180) / 180) * 100, 1)
        
        phase_names = ['New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous',
                      'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent']
        phase_index = int((phase_angle + 22.5) / 45) % 8
        moon_phase = phase_names[phase_index]
        
        return {
            'sunrise': sunrise_time.isoformat() if sunrise_time else None,
            'sunset': sunset_time.isoformat() if sunset_time else None,
            'moonrise': moonrise_time.isoformat() if moonrise_time else None,
            'moonset': moonset_time.isoformat() if moonset_time else None,
            'day_duration': day_duration,
            'night_duration': 24 - day_duration,
            'muhurta_duration': muhurta_duration,
            'civil_twilight_begin': civil_twilight_begin.isoformat() if civil_twilight_begin else None,
            'civil_twilight_end': civil_twilight_end.isoformat() if civil_twilight_end else None,
            'nautical_twilight_begin': nautical_twilight_begin.isoformat() if nautical_twilight_begin else None,
            'nautical_twilight_end': nautical_twilight_end.isoformat() if nautical_twilight_end else None,
            'astronomical_twilight_begin': astronomical_twilight_begin.isoformat() if astronomical_twilight_begin else None,
            'astronomical_twilight_end': astronomical_twilight_end.isoformat() if astronomical_twilight_end else None,
            'brahma_muhurta_start': brahma_start.isoformat() if brahma_start else None,
            'brahma_muhurta_end': brahma_end.isoformat() if brahma_end else None,
            'abhijit_muhurta_start': abhijit_start.isoformat() if abhijit_start else None,
            'abhijit_muhurta_end': abhijit_end.isoformat() if abhijit_end else None,
            'godhuli_muhurta_start': godhuli_start.isoformat() if godhuli_start else None,
            'godhuli_muhurta_end': godhuli_end.isoformat() if godhuli_end else None,
            'moon_phase': moon_phase,
            'moon_illumination': illumination
        }
    
    def _find_tithi_moment(self, start_jd, target_tithi):
        """Binary search to find exact moment of tithi transition"""
        jd = start_jd
        for _ in range(50):  # Max 50 iterations for precision
            sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            tithi_deg = (moon_pos - sun_pos) % 360
            current_tithi = int(tithi_deg / 12) + 1
            
            if abs(current_tithi - target_tithi) < 0.001:
                return jd
            
            # Adjust search direction
            if current_tithi < target_tithi:
                jd += 0.5 / 1440  # Add 30 seconds
            else:
                jd -= 0.5 / 1440  # Subtract 30 seconds
        
        return jd
    
    def calculate_hora(self, date_str, latitude, longitude, timezone="UTC+0"):
        """Calculate planetary hours (Hora) for the day"""
        if 'T' in str(date_str): date_str = str(date_str).split('T')[0]
        year, month, day = map(int, str(date_str).split('-'))
        
        jd = swe.julday(year, month, day, 0.0)
        geopos = [float(longitude), float(latitude), 0.0]
        
        sunrise_result = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)
        sunset_result = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)
        
        if sunrise_result[0] != 0 or sunset_result[0] != 0:
            return {"error": "Could not calculate sunrise/sunset"}
        
        tz_offset = self._parse_timezone(timezone)
        
        def jd_to_local_time(jd_val):
            year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
            dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            return dt_utc + timedelta(hours=tz_offset)
        
        sunrise_time = jd_to_local_time(sunrise_result[1][0])
        sunset_time = jd_to_local_time(sunset_result[1][0])
        
        day_duration = (sunset_time - sunrise_time).total_seconds() / 3600
        night_duration = 24 - day_duration
        hora_duration_day = day_duration / 12
        hora_duration_night = night_duration / 12
        
        # Planetary sequence starting from day lord
        planets = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']
        weekday = int((jd + 1.5) % 7)
        
        # Day horas
        day_horas = []
        current_time = sunrise_time
        
        for i in range(12):
            planet_index = (weekday + i) % 7
            end_time = current_time + timedelta(hours=hora_duration_day)
            
            day_horas.append({
                'hora_number': i + 1,
                'planet': planets[planet_index],
                'start_time': current_time.isoformat(),
                'end_time': end_time.isoformat()
            })
            current_time = end_time
        
        # Night horas (start from sunset)
        night_horas = []
        current_time = sunset_time
        
        for i in range(12):
            planet_index = (weekday + 12 + i) % 7  # Continue sequence from day
            end_time = current_time + timedelta(hours=hora_duration_night)
            
            night_horas.append({
                'hora_number': i + 1,
                'planet': planets[planet_index],
                'start_time': current_time.isoformat(),
                'end_time': end_time.isoformat()
            })
            current_time = end_time
        
        return {'day_horas': day_horas, 'night_horas': night_horas}
    
    def calculate_special_muhurtas(self, date_str, latitude, longitude, timezone="UTC+0"):
        """Calculate special muhurtas like Abhijit, Brahma Muhurta"""
        sunrise_sunset = self.get_local_sunrise_sunset(date_str, latitude, longitude, timezone)
        
        if not sunrise_sunset['sunrise'] or not sunrise_sunset['sunset']:
            return {"error": "Could not calculate sunrise/sunset"}
        
        sunrise_time = datetime.fromisoformat(sunrise_sunset['sunrise'])
        sunset_time = datetime.fromisoformat(sunrise_sunset['sunset'])
        
        # Brahma Muhurta: 1.5 hours before sunrise
        brahma_start = sunrise_time - timedelta(hours=1.5)
        brahma_end = sunrise_time - timedelta(minutes=48)
        
        # Abhijit Muhurta: Middle 1/15th of the day
        day_duration = sunrise_sunset['day_duration']
        muhurta_duration = day_duration / 15
        abhijit_start = sunrise_time + timedelta(hours=day_duration/2 - muhurta_duration/2)
        abhijit_end = abhijit_start + timedelta(hours=muhurta_duration)
        
        return {
            'brahma_muhurta': {
                'start_time': brahma_start.isoformat(),
                'end_time': brahma_end.isoformat(),
                'description': 'Most auspicious time for spiritual practices'
            },
            'abhijit_muhurta': {
                'start_time': abhijit_start.isoformat(),
                'end_time': abhijit_end.isoformat(),
                'description': 'Victory time, good for important tasks'
            }
        }