import swisseph as swe
from .base_calculator import BaseCalculator

class PanchangCalculator(BaseCalculator):
    """Extract panchang calculation logic from main.py"""
    
    def __init__(self):
        # Set Ayanamsa to Lahiri (CRITICAL FOR VEDIC ASTROLOGY)
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
        
        # Split movable and fixed for easier logic handling
        self.KARANA_MOVABLE = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija', 'Vishti']
        self.KARANA_FIXED = ['Shakuni', 'Chatushpada', 'Naga', 'Kimstughna']
    
    def calculate_panchang(self, date_str, time_str="12:00:00"):
        """Calculate panchang for given date and time"""
        # Parse Date
        year, month, day = map(int, date_str.split('-'))
        
        # Parse Time to decimal hour (handle HH:MM or HH:MM:SS)
        time_parts = time_str.split(':')
        h = int(time_parts[0])
        m = int(time_parts[1])
        s = int(time_parts[2]) if len(time_parts) > 2 else 0
        hour_decimal = h + (m / 60.0) + (s / 3600.0)
        
        # Calculate Julian Day with actual time
        jd = swe.julday(year, month, day, hour_decimal)
        
        # Get Positions (Flag: Sidereal with Lahiri ayanamsa)
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        
        # --- 1. Tithi Calculation (1-30 range) ---
        tithi_deg = (moon_pos - sun_pos) % 360
        tithi_num = int(tithi_deg / 12) + 1
        
        # Determine Paksha and Name
        paksha = "Shukla" if tithi_num <= 15 else "Krishna"
        if tithi_num == 15:
            tithi_name = "Purnima"
        elif tithi_num == 30:
            tithi_name = "Amavasya"
        else:
            # Map 16-29 back to 1-14 names
            idx = (tithi_num - 1) % 15
            tithi_name = self.TITHI_NAMES[idx]
        
        # --- 2. Vara (Weekday) ---
        vara_index = int((jd + 1.5) % 7)
        
        # --- 3. Nakshatra (Using 360/27 for better precision) ---
        nak_slice = 360 / 27
        nakshatra_index = int(moon_pos / nak_slice)
        nak_deg_remaining = (moon_pos % nak_slice)
        
        # --- 4. Yoga ---
        yoga_deg = (sun_pos + moon_pos) % 360
        yoga_index = int(yoga_deg / nak_slice)
        
        # --- 5. Karana (60 half-tithis in a month) ---
        k_num = int(tithi_deg / 6) + 1  # 1 to 60
        
        if k_num == 1:
            karana_name = "Kimstughna"
        elif k_num >= 58:
            # 58=Shakuni, 59=Chatushpada, 60=Naga
            fixed_map = {58: "Shakuni", 59: "Chatushpada", 60: "Naga"}
            karana_name = fixed_map[k_num]
        else:
            # Cycle through the 7 movable karanas
            movable_idx = (k_num - 2) % 7
            karana_name = self.KARANA_MOVABLE[movable_idx]
        
        return {
            "tithi": {
                "number": tithi_num,
                "name": tithi_name,
                "paksha": paksha,
                "degrees_traversed": round(tithi_deg % 12, 2)
            },
            "vara": {
                "number": vara_index + 1,
                "name": self.VARA_NAMES[vara_index]
            },
            "nakshatra": {
                "number": nakshatra_index + 1,
                "name": self.NAKSHATRA_NAMES[nakshatra_index],
                "degrees_traversed": round(nak_deg_remaining, 2)
            },
            "yoga": {
                "number": yoga_index + 1,
                "name": self.YOGA_NAMES[yoga_index % 27],
                "degrees_traversed": round(yoga_deg % nak_slice, 2)
            },
            "karana": {
                "number": k_num,
                "name": karana_name
            }
        }
    
    def calculate_birth_panchang(self, birth_data):
        """Calculate panchang for birth date AND time"""
        date_str = ""
        time_str = "12:00:00"
        
        if isinstance(birth_data, dict):
            date_str = birth_data.get('date')
            time_str = birth_data.get('time', "12:00:00")
        else:
            # Assuming object access
            date_str = getattr(birth_data, 'date', None)
            time_str = getattr(birth_data, 'time', "12:00:00")
            
            # If date is datetime object
            if hasattr(date_str, 'strftime'):
                time_str = date_str.strftime("%H:%M:%S")
                date_str = date_str.strftime("%Y-%m-%d")
        
        return self.calculate_panchang(date_str, time_str)