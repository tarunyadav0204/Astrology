import swisseph as swe
from datetime import datetime, timedelta
from .panchang_calculator import PanchangCalculator

class MuhuratCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.panchang_calc = PanchangCalculator()
        
        # 1. Auspicious Nakshatras (Growth & Stability)
        self.CHILDBIRTH_NAKSHATRAS = [4, 5, 7, 8, 12, 13, 14, 15, 17, 21, 22, 23, 24, 26, 27]
        
        # 2. Inauspicious Tithis (Rikta & Amavasya)
        self.AVOID_TITHIS = [4, 9, 14, 30]
        
        # 3. Inauspicious Yogas
        self.AVOID_YOGAS = [1, 6, 9, 10, 13, 15, 17, 19, 27]
    
    @staticmethod
    def _jd_to_local_hour(jd_val, tz_offset):
        """Convert Julian Day to local hour with timezone offset"""
        utc = (jd_val + 0.5 - int(jd_val + 0.5)) * 24.0
        return (utc + tz_offset) % 24

    def calculate_childbirth_muhurat(self, start_date_str: str, end_date_str: str, 
                                   latitude: float, longitude: float, 
                                   mother_nakshatra: int, timezone_str: str = 'UTC+5:30') -> dict:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        valid_slots = []
        current_date = start_date
        days_scanned = 0
        
        while current_date <= end_date and days_scanned < 30:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                # --- PHASE 1: PANCHANG PURITY (Day Level) ---
                panchang = self.panchang_calc.calculate_panchang(date_str, "12:00:00")
                
                # A. Tithi Check
                if panchang['tithi']['number'] in self.AVOID_TITHIS:
                    current_date += timedelta(days=1); days_scanned += 1; continue
                    
                # B. Yoga Check
                if panchang['yoga']['number'] in self.AVOID_YOGAS:
                    current_date += timedelta(days=1); days_scanned += 1; continue
                
                # C. Karana Check (Vishti/Bhadra is hazardous)
                if panchang['karana']['name'] == 'Vishti':
                    current_date += timedelta(days=1); days_scanned += 1; continue

                # D. Nakshatra Check
                daily_nak = panchang['nakshatra']['number']
                if daily_nak not in self.CHILDBIRTH_NAKSHATRAS:
                    current_date += timedelta(days=1); days_scanned += 1; continue
                    
                # E. Tara Bala Check (Mother Compatibility)
                dist = (daily_nak - mother_nakshatra) 
                if dist < 0: dist += 27
                tara_score = (dist + 1) % 9
                if tara_score == 0: tara_score = 9
                
                if tara_score in [1, 3, 5, 7]: # Reject Janma, Vipat, Pratyak, Naidhana
                    current_date += timedelta(days=1); days_scanned += 1; continue

                # --- PHASE 2: TIME PURITY (Hour Level) ---
                day_slots = self._find_auspicious_lagnas(current_date, latitude, longitude, timezone_str)
                
                if day_slots:
                    valid_slots.append({
                        'date': date_str,
                        'weekday': panchang['vara']['name'],
                        'nakshatra': panchang['nakshatra']['name'],
                        'tara_quality': 'Excellent' if tara_score in [2,4,6,8,9] else 'Average',
                        'slots': day_slots
                    })
            except Exception as e:
                print(f"❌ [MUHURAT ERROR] Error processing {date_str}: {e}")
            
            current_date += timedelta(days=1)
            days_scanned += 1
            
        return {
            "period": f"{start_date_str} to {end_date_str}",
            "dates_found": len(valid_slots),
            "recommendations": valid_slots
        }

    def _find_auspicious_lagnas(self, date_obj, lat, lon, tz_str):
        """Scan 08:00 to 18:00 avoiding Rahu, Yamaganda, and Gulika"""
        
        # 1. Parse Timezone
        tz_offset = 5.5
        if 'UTC' in tz_str:
            try:
                parts = tz_str.replace('UTC', '').split(':')
                sign = -1 if '-' in tz_str else 1
                tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
            except: pass

        # 2. Calculate Forbidden Windows (Rahu, Yama, Gulika)
        jd = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 12.0)
        
        # Pass geopos as a tuple (lon, lat, height)
        geopos = (float(lon), float(lat), 0.0)
        rise_result = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)
        setting_result = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)
        
        rise = rise_result[1][0]
        setting = setting_result[1][0]
        
        sunrise_hour = self._jd_to_local_hour(rise, tz_offset)
        sunset_hour = self._jd_to_local_hour(setting, tz_offset)
        
        day_duration = sunset_hour - sunrise_hour
        if day_duration < 0: day_duration += 24 
        
        one_part = day_duration / 8
        weekday = date_obj.weekday() # 0=Mon, 6=Sun

        # Rahu/Yama/Gulika segments
        rahu_map = {0: 1, 1: 6, 2: 4, 3: 5, 4: 3, 5: 2, 6: 7} 
        yama_map = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 5, 6: 6}
        gulika_map = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

        def get_window(segment_index):
            start = sunrise_hour + (segment_index * one_part)
            return (start, start + one_part)

        rahu_window = get_window(rahu_map[weekday])
        yama_window = get_window(yama_map[weekday])
        gulika_window = get_window(gulika_map[weekday])

        def is_forbidden(time_dec):
            in_rahu = rahu_window[0] <= time_dec < rahu_window[1]
            in_yama = yama_window[0] <= time_dec < yama_window[1]
            in_gulika = gulika_window[0] <= time_dec < gulika_window[1]
            return in_rahu or in_yama or in_gulika

        # 3. Scan Time Slots
        slots = []
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        start_hour = 8
        end_hour = 18
        current_time = date_obj.replace(hour=start_hour, minute=0, second=0)
        end_time = date_obj.replace(hour=end_hour, minute=0, second=0)
        
        while current_time < end_time:
            curr_hour_dec = current_time.hour + current_time.minute/60.0
            
            # Skip forbidden times
            if is_forbidden(curr_hour_dec):
                current_time += timedelta(minutes=15)
                continue

            # Calculate Ascendant
            local_hour = current_time.hour + current_time.minute/60.0
            utc_hour = local_hour - tz_offset
            
            jd_now = swe.julday(int(current_time.year), int(current_time.month), int(current_time.day), float(utc_hour))
            
            houses = swe.houses(jd_now, float(lat), float(lon), b'P')
            asc_deg = (houses[1][0] - swe.get_ayanamsa_ut(jd_now)) % 360
            asc_sign = int(asc_deg / 30)
            
            # Filter Good Lagnas (Benefic Signs)
            if asc_sign in [1, 2, 3, 4, 5, 6, 8, 11]:
                slots.append({
                    "time": current_time.strftime("%H:%M"),
                    "lagna": sign_names[asc_sign],
                    "quality": "High"
                })
                current_time += timedelta(minutes=60)
            else:
                current_time += timedelta(minutes=15)
                
        return slots