"""
Professional Festival Date Calculator using Swiss Ephemeris
Geographic-Moment approach for Drik Panchang level accuracy
"""
import swisseph as swe
from datetime import datetime, timedelta
import pytz
from .festival_data import HINDU_FESTIVALS, MONTHLY_VRATS

class FestivalCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def get_tithi_at_moment(self, jd):
        """Calculate exact Tithi (1-30) and Paksha at specific Julian Day"""
        sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
        moon_lon = swe.calc_ut(jd, swe.MOON)[0][0]
        
        elongation = (moon_lon - sun_lon) % 360
        tithi_float = elongation / 12
        full_tithi = int(tithi_float) + 1  # 1 to 30
        
        paksha = "shukla" if full_tithi <= 15 else "krishna"
        lunar_day = full_tithi if full_tithi <= 15 else full_tithi - 15
        
        return full_tithi, lunar_day, paksha
    
    def get_local_sunrise(self, jd, lat, lon):
        """Calculate local sunrise for Udaya Tithi determination"""
        try:
            res = swe.rise_trans(jd, swe.SUN, lat, lon, 0, 0, 0, 1)
            return res[1][0] if res[0] == 0 else jd + 0.25  # Fallback to 6 AM
        except:
            return jd + 0.25  # Fallback to 6 AM local
    
    def get_moonrise_time(self, jd, lat, lon, timezone_name="Asia/Kolkata"):
        """Calculate moonrise time for Karwa Chauth and Sankashti Chaturthi"""
        try:
            res = swe.rise_trans(jd, swe.MOON, lat, lon, 0, 0, 0, 1)
            if res[0] == 0:  # Success
                moonrise_jd = res[1][0]
                year, month, day, hour_utc, minute, second = swe.jdut1_to_utc(moonrise_jd, 1)
                utc_dt = datetime(year, month, day, hour_utc, minute, int(second), tzinfo=pytz.UTC)
                
                try:
                    tz = pytz.timezone(timezone_name)
                    local_dt = utc_dt.astimezone(tz)
                    return f"{local_dt.hour:02d}:{local_dt.minute:02d}"
                except:
                    # Fallback to offset calculation
                    offset_hours = 5.5 if "Asia" in timezone_name else 0
                    local_jd = moonrise_jd + (offset_hours / 24.0)
                    year, month, day, hour, minute, second = swe.jdut1_to_utc(local_jd, 1)
                    return f"{hour:02d}:{minute:02d}"
            else:
                return "Not visible"
        except:
            return "Not available"
    
    def get_local_sunset(self, jd, lat, lon):
        """Calculate local sunset for Pradosh calculations"""
        try:
            res = swe.rise_trans(jd, swe.SUN, lat, lon, 0, 0, 0, 2)
            return res[1][0] if res[0] == 0 else jd + 0.75  # Fallback to 6 PM
        except:
            return jd + 0.75  # Fallback to 6 PM local
    
    def get_tithi_end_time(self, jd_start, target_tithi, lat, lon, timezone_name="Asia/Kolkata"):
        """Calculate exact moment when tithi ends in proper timezone"""
        jd = jd_start
        max_search_hours = 48
        
        for hour in range(int(max_search_hours * 60)):
            jd_test = jd + (hour / (24 * 60))
            
            sun_lon = swe.calc_ut(jd_test, swe.SUN)[0][0]
            moon_lon = swe.calc_ut(jd_test, swe.MOON)[0][0]
            elongation = (moon_lon - sun_lon) % 360
            current_tithi = int(elongation / 12) + 1
            
            if current_tithi != target_tithi:
                # Convert to proper timezone
                year, month, day, hour_utc, minute, second = swe.jdut1_to_utc(jd_test, 1)
                utc_dt = datetime(year, month, day, hour_utc, minute, int(second), tzinfo=pytz.UTC)
                
                try:
                    tz = pytz.timezone(timezone_name)
                    local_dt = utc_dt.astimezone(tz)
                    return f"{local_dt.hour:02d}:{local_dt.minute:02d}"
                except:
                    # Fallback to offset calculation
                    offset_hours = 5.5 if "Asia" in timezone_name else 0
                    local_jd = jd_test + (offset_hours / 24.0)
                    year, month, day, hour, minute, second = swe.jdut1_to_utc(local_jd, 1)
                    return f"{hour:02d}:{minute:02d}"
        
        return "Next Day"
    
    def calculate_parana_time(self, jd_ekadashi, lat, lon, timezone_name="Asia/Kolkata"):
        """Calculate proper Ekadashi Parana time avoiding Hari Vasara"""
        jd_next_day = jd_ekadashi + 1
        jd_next_sunrise = self.get_local_sunrise(jd_next_day, lat, lon)
        
        full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd_next_sunrise)
        
        if lunar_day == 12:  # Dwadashi present at sunrise
            # Find when first 25% of Dwadashi ends (avoid Hari Vasara)
            dwadashi_start = jd_next_sunrise
            
            # Find when Dwadashi completely ends
            dwadashi_end_jd = None
            for hour in range(48 * 60):  # Search in minutes
                test_jd = dwadashi_start + (hour / (24 * 60))
                test_tithi, test_lunar_day, test_paksha = self.get_tithi_at_moment(test_jd)
                if test_lunar_day != 12:  # Dwadashi ended
                    dwadashi_end_jd = test_jd
                    break
            
            if dwadashi_end_jd:
                # Calculate 25% point of Dwadashi duration
                dwadashi_duration = dwadashi_end_jd - dwadashi_start
                hari_vasara_end = dwadashi_start + (dwadashi_duration * 0.25)
                
                # Convert to proper timezone
                year, month, day, hour_utc, minute, second = swe.jdut1_to_utc(hari_vasara_end, 1)
                utc_dt = datetime(year, month, day, hour_utc, minute, int(second), tzinfo=pytz.UTC)
                
                try:
                    tz = pytz.timezone(timezone_name)
                    local_dt = utc_dt.astimezone(tz)
                    return f"After {local_dt.hour:02d}:{local_dt.minute:02d} (avoiding Hari Vasara)"
                except:
                    # Fallback to offset calculation
                    offset_hours = 5.5 if "Asia" in timezone_name else 0
                    local_jd = hari_vasara_end + (offset_hours / 24.0)
                    year, month, day, hour, minute, second = swe.jdut1_to_utc(local_jd, 1)
                    return f"After {hour:02d}:{minute:02d} (avoiding Hari Vasara)"
        
        # Dwadashi already ended, can break fast after sunrise
        year, month, day, hour_utc, minute, second = swe.jdut1_to_utc(jd_next_sunrise, 1)
        utc_dt = datetime(year, month, day, hour_utc, minute, int(second), tzinfo=pytz.UTC)
        
        try:
            tz = pytz.timezone(timezone_name)
            local_dt = utc_dt.astimezone(tz)
            return f"After {local_dt.hour:02d}:{local_dt.minute:02d}"
        except:
            # Fallback to offset calculation
            offset_hours = 5.5 if "Asia" in timezone_name else 0
            local_jd = jd_next_sunrise + (offset_hours / 24.0)
            year, month, day, hour, minute, second = swe.jdut1_to_utc(local_jd, 1)
            return f"After {hour:02d}:{minute:02d}"
    
    def get_lunar_month_with_adhika(self, jd, calendar_system="amanta"):
        """Get lunar month with proper Adhika Maas detection"""
        # Find the New Moon (Amavasya) for this lunar month
        # Search backwards up to 35 days to find the New Moon that started this month
        amavasya_jd = None
        for days_back in range(35):
            test_jd = jd - days_back
            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(test_jd)
            if lunar_day == 15 and paksha == "krishna":  # Amavasya
                amavasya_jd = test_jd
                break
        
        if not amavasya_jd:
            # Fallback to old method if no Amavasya found
            return self.get_lunar_month_simple(jd, calendar_system), False
        
        # Get Sun's position at this Amavasya
        sun_lon_amavasya = swe.calc_ut(amavasya_jd, swe.SUN)[0][0]
        
        # Find next Amavasya
        next_amavasya_jd = None
        for days_forward in range(25, 35):  # Lunar month is ~29.5 days
            test_jd = amavasya_jd + days_forward
            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(test_jd)
            if lunar_day == 15 and paksha == "krishna":  # Next Amavasya
                next_amavasya_jd = test_jd
                break
        
        is_adhika = False
        if next_amavasya_jd:
            # Get Sun's position at next Amavasya
            sun_lon_next = swe.calc_ut(next_amavasya_jd, swe.SUN)[0][0]
            
            # Check if Sun is in same zodiac sign (Adhika month condition)
            current_sign = int(sun_lon_amavasya / 30)
            next_sign = int(sun_lon_next / 30)
            
            if current_sign == next_sign:
                is_adhika = True
        
        # Get month name based on Sun's position
        month_names = [
            "chaitra", "vaisakha", "jyeshtha", "ashadha",
            "sravana", "bhadrapada", "ashwin", "kartik", 
            "margashirsha", "pausha", "magha", "phalguna"
        ]
        
        # Month is determined by Sun's sign at Amavasya
        sign_index = int(sun_lon_amavasya / 30)
        # Adjust for month naming convention (Chaitra starts when Sun enters Pisces)
        month_index = (sign_index + 1) % 12
        
        # Adjust for Purnimanta system
        if calendar_system == "purnimanta":
            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd)
            if paksha == "krishna":
                month_index = (month_index + 1) % 12
        
        month_name = month_names[month_index]
        if is_adhika:
            month_name = f"adhika_{month_name}"
        
        return month_name, is_adhika
    
    def get_lunar_month_simple(self, jd, calendar_system="amanta"):
        """Get lunar month with Purnimanta/Amanta system support"""
        sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
        month_names = [
            "chaitra", "vaisakha", "jyeshtha", "ashadha",
            "sravana", "bhadrapada", "ashwin", "kartik", 
            "margashirsha", "pausha", "magha", "phalguna"
        ]
        month_index = int((sun_lon + 15) / 30) % 12
        
        # Adjust for Purnimanta system (North India)
        if calendar_system == "purnimanta":
            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd)
            if paksha == "krishna":
                month_index = (month_index + 1) % 12
        
        return month_names[month_index]
    
    def find_festival_dates(self, year, month=None, lat=28.6139, lon=77.2090, calendar_system="amanta", timezone_name="Asia/Kolkata"):
        """Find festivals with geographic precision and Adhika Maas support"""
        festivals = []
        start_date = datetime(year, month or 1, 1)
        
        if month:
            end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        else:
            end_date = datetime(year + 1, 1, 1)
        
        current_date = start_date
        while current_date < end_date:
            jd_midnight = swe.julday(current_date.year, current_date.month, current_date.day, 0)
            jd_sunrise = self.get_local_sunrise(jd_midnight, lat, lon)
            
            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd_sunrise)
            lunar_month, is_adhika = self.get_lunar_month_with_adhika(jd_sunrise, calendar_system)
            
            # Calculate tithi end time with timezone
            tithi_end_time = self.get_tithi_end_time(jd_sunrise, full_tithi, lat, lon, timezone_name)
            
            for festival_id, festival in HINDU_FESTIVALS.items():
                # Skip generic ekadashi entries to avoid duplicates with dynamic vrats
                if festival_id in ["shukla_ekadashi", "krishna_ekadashi", "sankashti_chaturthi"]:
                    continue
                    
                if self._matches_pro_logic(festival, festival_id, full_tithi, lunar_day, paksha, 
                                         lunar_month, current_date, jd_sunrise, lat, lon):
                    festivals.append({
                        "id": festival_id,
                        "name": festival["name"],
                        "date": current_date.strftime("%Y-%m-%d"),
                        "tithi_at_sunrise": full_tithi,
                        "tithi_end_time": tithi_end_time,
                        "paksha": paksha,
                        "lunar_month": lunar_month,
                        "is_adhika_month": is_adhika,
                        "type": festival["type"],
                        "description": festival["description"],
                        "significance": festival["significance"],
                        "rituals": festival["rituals"]
                    })
            
            current_date += timedelta(days=1)
        
        return sorted(festivals, key=lambda x: x["date"])
    
    def _matches_pro_logic(self, festival, festival_id, full_tithi, lunar_day, paksha, 
                          lunar_month, date, jd_sunrise, lat, lon):
        """Professional matching with Udaya Tithi and time-window logic"""
        # Solar festivals
        if "solar_date" in festival:
            if festival["solar_date"] == "january_14" and date.month == 1 and date.day == 14:
                return True
            if festival["solar_date"] == "april_13" and date.month == 4 and date.day == 13:
                return True
        
        # Lunar festivals
        if "lunar_day" in festival:
            day_map = {
                "pratipada": 1, "dvitiya": 2, "tritiya": 3, "chaturthi": 4, "panchami": 5,
                "shashthi": 6, "saptami": 7, "ashtami": 8, "navami": 9, "dashami": 10,
                "ekadashi": 11, "dvadashi": 12, "trayodashi": 13, "chaturdashi": 14,
                "purnima": 15, "amavasya": 15
            }
            
            target_lunar_day = day_map.get(festival["lunar_day"])
            if not target_lunar_day:
                return False
            
            # Month check
            if festival.get("month") != "all" and festival.get("month") != lunar_month:
                return False
            
            # Paksha check
            if festival.get("paksha") and festival["paksha"] != paksha:
                return False
            
            # Standard Udaya Tithi rule
            if target_lunar_day == lunar_day:
                # Special window checks for major festivals
                if festival_id == "diwali":
                    # Amavasya must prevail during Pradosh (sunset + 2.4 hours)
                    jd_sunset = self.get_local_sunset(jd_sunrise, lat, lon)
                    jd_pradosh = jd_sunset + (2.4 / 24.0)  # 2.4 hours after sunset
                    _, pradosh_lunar_day, pradosh_paksha = self.get_tithi_at_moment(jd_pradosh)
                    return pradosh_lunar_day == 15 and pradosh_paksha == "krishna"
                
                elif festival_id == "janmashtami":
                    # Ashtami must prevail during Nishita (midnight)
                    jd_midnight = jd_sunrise + 0.5  # Midnight of same day
                    _, midnight_lunar_day, midnight_paksha = self.get_tithi_at_moment(jd_midnight)
                    return midnight_lunar_day == 8 and midnight_paksha == "krishna"
                
                return True
        
        return False
    
    def get_monthly_vrats(self, year, month, lat=28.6139, lon=77.2090, calendar_system="amanta", timezone_name="Asia/Kolkata"):
        """Get monthly vrats with dynamic generation, timezone and Adhika support"""
        vrats = []
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        
        # Vrat definitions
        vrat_types = {
            11: {
                "shukla": {"name": "Shukla Ekadashi", "id": "shukla_ekadashi", "has_parana": True},
                "krishna": {"name": "Krishna Ekadashi", "id": "krishna_ekadashi", "has_parana": True}
            },
            13: {
                "shukla": {"name": "Shukla Pradosh Vrat", "id": "shukla_pradosh"},
                "krishna": {"name": "Krishna Pradosh Vrat", "id": "krishna_pradosh"}
            },
            4: {
                "krishna": {"name": "Sankashti Chaturthi", "id": "sankashti_chaturthi", "has_moonrise": True}
            },
            14: {
                "krishna": {"name": "Masik Shivaratri", "id": "masik_shivaratri"}
            }
        }
        
        found_dates = set()
        found_vrat_types = set()  # Track vrat types per lunar month
        current_lunar_month = None
        current_date = start_date
        
        while current_date < end_date:
            jd_midnight = swe.julday(current_date.year, current_date.month, current_date.day, 0)
            jd_sunrise = self.get_local_sunrise(jd_midnight, lat, lon)
            
            full_tithi, lunar_day, paksha = self.get_tithi_at_moment(jd_sunrise)
            lunar_month, _ = self.get_lunar_month_with_adhika(jd_sunrise, calendar_system)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Reset vrat tracking when lunar month changes
            if current_lunar_month != lunar_month:
                current_lunar_month = lunar_month
                found_vrat_types = set()
            
            # Check if this lunar_day has vrat definitions
            if lunar_day in vrat_types:
                paksha_vrats = vrat_types[lunar_day]
                if paksha in paksha_vrats:
                    vrat_def = paksha_vrats[paksha]
                    vrat_type_key = f"{lunar_month}_{vrat_def['id']}"
                    
                    if vrat_type_key not in found_vrat_types:
                        found_vrat_types.add(vrat_type_key)
                        
                        tithi_end_time = self.get_tithi_end_time(jd_sunrise, full_tithi, lat, lon, timezone_name)
                        
                        vrat_data = {
                            "id": vrat_def["id"],
                            "name": vrat_def["name"],
                            "date": date_str,
                            "type": "vrat",
                            "tithi_at_sunrise": full_tithi,
                            "tithi_end_time": tithi_end_time,
                            "paksha": paksha
                        }
                        
                        # Add parana time for Ekadashi
                        if vrat_def.get("has_parana"):
                            vrat_data["parana_time"] = self.calculate_parana_time(jd_sunrise, lat, lon, timezone_name)
                        
                        # Add moonrise time for Sankashti
                        if vrat_def.get("has_moonrise"):
                            vrat_data["moonrise_time"] = self.get_moonrise_time(jd_sunrise, lat, lon, timezone_name)
                        
                        vrats.append(vrat_data)
            
            current_date += timedelta(days=1)
        
        return sorted(vrats, key=lambda x: x["date"])