import swisseph as swe
from datetime import datetime, timedelta
from .panchang_calculator import PanchangCalculator

class MuhuratCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.panchang_calc = PanchangCalculator()
        
        # Auspicious Nakshatras for Childbirth
        self.CHILDBIRTH_NAKSHATRAS = [4, 5, 7, 8, 12, 13, 14, 15, 17, 21, 22, 23, 24, 26, 27]
        
        # Inauspicious Tithis
        self.AVOID_TITHIS = [4, 9, 14, 30]
        
        # Inauspicious Yogas
        self.AVOID_YOGAS = [1, 6, 9, 10, 13, 15, 17, 19, 27]

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
            
            # Day checks
            panchang = self.panchang_calc.calculate_panchang(date_str, "12:00:00")
            
            # Tithi check
            if panchang['tithi']['number'] in self.AVOID_TITHIS:
                current_date += timedelta(days=1)
                days_scanned += 1
                continue
                
            # Yoga check
            if panchang['yoga']['number'] in self.AVOID_YOGAS:
                current_date += timedelta(days=1)
                days_scanned += 1
                continue
                
            # Nakshatra check
            daily_nak = panchang['nakshatra']['number']
            if daily_nak not in self.CHILDBIRTH_NAKSHATRAS:
                current_date += timedelta(days=1)
                days_scanned += 1
                continue
                
            # Tara Bala check
            dist = (daily_nak - mother_nakshatra) 
            if dist < 0: 
                dist += 27
            tara_score = (dist + 1) % 9
            if tara_score == 0: 
                tara_score = 9
            
            if tara_score in [1, 3, 5, 7]:
                current_date += timedelta(days=1)
                days_scanned += 1
                continue

            # Time checks
            day_slots = self._find_auspicious_lagnas(current_date, latitude, longitude, timezone_str)
            
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
            "period": f"{start_date_str} to {end_date_str}",
            "dates_found": len(valid_slots),
            "recommendations": valid_slots
        }

    def _find_auspicious_lagnas(self, date_obj, lat, lon, tz_str):
        # Parse timezone
        tz_offset = 5.5
        if 'UTC' in tz_str:
            try:
                parts = tz_str.replace('UTC', '').split(':')
                sign = -1 if '-' in tz_str else 1
                tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
            except: 
                pass

        slots = []
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Scan 8 AM to 6 PM
        current_time = date_obj.replace(hour=8, minute=0, second=0)
        end_time = date_obj.replace(hour=18, minute=0, second=0)
        
        while current_time < end_time:
            local_hour = current_time.hour + current_time.minute/60.0
            utc_hour = local_hour - tz_offset
            jd = swe.julday(current_time.year, current_time.month, current_time.day, utc_hour)
            
            # Calculate Ascendant
            houses = swe.houses(jd, lat, lon, b'P')
            asc_deg = (houses[1][0] - swe.get_ayanamsa_ut(jd)) % 360
            asc_sign = int(asc_deg / 30)
            
            # Good lagnas: Taurus, Gemini, Cancer, Leo, Virgo, Libra, Sagittarius, Pisces
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