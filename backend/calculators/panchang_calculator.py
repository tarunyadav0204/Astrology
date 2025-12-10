import swisseph as swe
from datetime import datetime
from .base_calculator import BaseCalculator

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
        """Helper to parse timezone string like 'UTC+5:30' into float offset"""
        offset = 5.5 # Default IST
        if isinstance(tz_str, (int, float)):
            return float(tz_str)
        if isinstance(tz_str, str) and 'UTC' in tz_str:
            try:
                parts = tz_str.replace('UTC', '').split(':')
                sign = -1 if '-' in tz_str else 1
                if len(parts) > 1:
                    offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    offset = float(parts[0])
            except: pass
        return offset
    
    def calculate_panchang(self, date_str, time_str="12:00:00", latitude=0.0, longitude=0.0, timezone="UTC+5:30"):
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
        tz = getattr(birth_data, 'timezone', "UTC+5:30") or birth_data.get('timezone', "UTC+5:30")

        return self.calculate_panchang(date_str, time_str, float(lat), float(lon), tz)
    
    def calculate_choghadiya(self, date_str, lat, lon, timezone="UTC+5:30"):
        """Calculate daily Choghadiya segments with dynamic timezone"""
        if 'T' in str(date_str): date_str = str(date_str).split('T')[0]
        year, month, day = map(int, str(date_str).split('-'))
        
        # Calculate Sunrise/Sunset (Geocentric, Noon UTC)
        jd = swe.julday(year, month, day, 12.0)
        
        geopos = (float(lon), float(lat), 0.0)
        rise = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)[1][0]
        setting = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)[1][0]
        
        # --- FIX: Use dynamic timezone instead of +5.5 ---
        tz_offset = self._parse_timezone(timezone)
        
        rise_local = ((rise + 0.5 - int(rise + 0.5)) * 24.0 + tz_offset) % 24
        set_local = ((setting + 0.5 - int(setting + 0.5)) * 24.0 + tz_offset) % 24
        
        day_duration = set_local - rise_local
        if day_duration < 0: day_duration += 24
        
        night_duration = 24 - day_duration
        day_chunk = day_duration / 8
        night_chunk = night_duration / 8
        
        CHOG_NAMES = ["Udvega", "Amrita", "Roga", "Labha", "Shubha", "Chara", "Kala"]
        weekday = int((jd + 1.5) % 7)  # 0=Sun
        
        # Day Slots
        day_slots = []
        curr = rise_local
        for i in range(8):
            end = curr + day_chunk
            idx = (weekday + i) % 7
            day_slots.append({
                "name": CHOG_NAMES[idx],
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
                "start_time": f"{int(curr):02d}:{int((curr%1)*60):02d}",
                "end_time": f"{int(end):02d}:{int((end%1)*60):02d}"
            })
            curr = end
            
        return {"day_choghadiya": day_slots, "night_choghadiya": night_slots}