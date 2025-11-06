"""
Festival Date Calculator using Swiss Ephemeris
"""
import swisseph as swe
from datetime import datetime, timedelta
from .festival_data import HINDU_FESTIVALS, MONTHLY_VRATS

class FestivalCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def get_lunar_day(self, jd):
        """Get lunar day (tithi) for given Julian day with precise calculation"""
        sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
        moon_lon = swe.calc_ut(jd, swe.MOON)[0][0]
        
        # Calculate elongation (moon - sun)
        elongation = moon_lon - sun_lon
        if elongation < 0:
            elongation += 360
        
        # Each tithi is 12 degrees
        tithi = int(elongation / 12) + 1
        
        # Handle special cases
        if tithi > 30:
            tithi = 30  # Amavasya
        elif tithi == 16:
            tithi = 1   # New cycle starts
        
        return tithi
    
    def get_lunar_month(self, jd):
        """Get lunar month for given Julian day"""
        sun_lon = swe.calc_ut(jd, swe.SUN)[0][0]
        # Simplified lunar month calculation
        month_names = [
            "chaitra", "vaisakha", "jyeshtha", "ashadha",
            "sravana", "bhadrapada", "ashwin", "kartik", 
            "margashirsha", "pausha", "magha", "phalguna"
        ]
        month_index = int((sun_lon + 15) / 30) % 12
        return month_names[month_index]
    
    def find_festival_dates(self, year, month=None):
        """Find festival dates for given year/month"""
        festivals = []
        start_date = datetime(year, month or 1, 1)
        if month:
            # Get last day of the month properly
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year + 1, 1, 1)
        
        current_date = start_date
        while current_date < end_date:
            jd = swe.julday(current_date.year, current_date.month, current_date.day)
            lunar_day = self.get_lunar_day(jd)
            lunar_month = self.get_lunar_month(jd)
            
            # Check for festivals
            for festival_id, festival in HINDU_FESTIVALS.items():
                if self._matches_festival(festival, lunar_day, lunar_month, current_date):
                    festivals.append({
                        "id": festival_id,
                        "name": festival["name"],
                        "date": current_date.strftime("%Y-%m-%d"),
                        "type": festival["type"],
                        "description": festival["description"],
                        "significance": festival["significance"],
                        "rituals": festival["rituals"]
                    })
            
            current_date += timedelta(days=1)
        
        return sorted(festivals, key=lambda x: x["date"])
    
    def _matches_festival(self, festival, lunar_day, lunar_month, date):
        """Check if date matches festival criteria"""
        if "lunar_day" in festival:
            day_map = {
                "pratipada": 1, "dvitiya": 2, "tritiya": 3, "chaturthi": 4,
                "panchami": 5, "shashthi": 6, "saptami": 7, "ashtami": 8,
                "navami": 9, "dashami": 10, "ekadashi": 11, "dvadashi": 12,
                "trayodashi": 13, "chaturdashi": 14, "purnima": 15, "amavasya": 30
            }
            
            required_day = day_map.get(festival["lunar_day"])
            if required_day and lunar_day == required_day:
                if festival.get("month") == "all" or festival.get("month") == lunar_month:
                    return True
        
        # Solar festivals
        if "solar_date" in festival:
            if festival["solar_date"] == "january_14" and date.month == 1 and date.day == 14:
                return True
            if festival["solar_date"] == "april_13" and date.month == 4 and date.day == 13:
                return True
        
        return False
    
    def get_monthly_vrats(self, year, month):
        """Get monthly vrat dates"""
        vrats = []
        start_date = datetime(year, month, 1)
        
        # Calculate days in month properly
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        current_date = start_date
        while current_date < end_date:
            jd = swe.julday(current_date.year, current_date.month, current_date.day)
            lunar_day = self.get_lunar_day(jd)
            
            # Check for monthly vrats (avoid duplicates)
            date_str = current_date.strftime("%Y-%m-%d")
            existing_names = [v["name"].lower() for v in vrats]
            
            for vrat_id, vrat in MONTHLY_VRATS.items():
                vrat_name_lower = vrat["name"].lower()
                # Skip if similar vrat already exists
                if not any("pradosh" in existing and "pradosh" in vrat_name_lower for existing in existing_names):
                    if lunar_day == 11 and vrat_id == "ekadashi":
                        vrats.append({
                            "name": "Shukla " + vrat["name"],
                            "date": date_str,
                            "deity": vrat["deity"],
                            "benefits": vrat["benefits"]
                        })
                    elif lunar_day == 26 and vrat_id == "ekadashi":
                        vrats.append({
                            "name": "Krishna " + vrat["name"],
                            "date": date_str,
                            "deity": vrat["deity"],
                            "benefits": vrat["benefits"]
                        })
                    elif lunar_day == 13 and vrat_id == "pradosh":
                        vrats.append({
                            "name": "Shukla " + vrat["name"],
                            "date": date_str,
                            "deity": vrat["deity"],
                            "benefits": vrat["benefits"]
                        })
                    elif lunar_day == 28 and vrat_id == "pradosh":
                        vrats.append({
                            "name": "Krishna " + vrat["name"],
                            "date": date_str,
                            "deity": vrat["deity"],
                            "benefits": vrat["benefits"]
                        })
            
            current_date += timedelta(days=1)
        
        return sorted(vrats, key=lambda x: x["date"])