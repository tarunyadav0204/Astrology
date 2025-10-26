import swisseph as swe
from .base_calculator import BaseCalculator

class PanchangCalculator(BaseCalculator):
    """Extract panchang calculation logic from main.py"""
    
    def __init__(self):
        super().__init__()
        self.TITHI_NAMES = [
            'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami', 'Ashtami',
            'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima/Amavasya'
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
        
        self.KARANA_NAMES = [
            'Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija', 'Vishti', 'Shakuni',
            'Chatushpada', 'Naga', 'Kimstughna'
        ]
    
    def calculate_panchang(self, transit_date):
        """Calculate panchang for given date"""
        jd = swe.julday(
            int(transit_date.split('-')[0]),
            int(transit_date.split('-')[1]),
            int(transit_date.split('-')[2]),
            12.0
        )
        
        sun_pos = swe.calc_ut(jd, 0, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        
        # Tithi (Lunar day) - difference between Moon and Sun
        tithi_deg = (moon_pos - sun_pos) % 360
        tithi_num = int(tithi_deg / 12) + 1
        
        # Vara (Weekday)
        vara_index = int((jd + 1.5) % 7)
        
        # Nakshatra
        nakshatra_index = int(moon_pos / 13.333333)
        
        # Yoga - sum of Sun and Moon longitudes
        yoga_deg = (sun_pos + moon_pos) % 360
        yoga_index = int(yoga_deg / 13.333333)
        
        # Karana - half of Tithi
        karana_index = int(tithi_deg / 6) % 11
        
        return {
            "tithi": {
                "number": tithi_num,
                "name": self.TITHI_NAMES[min(tithi_num - 1, 14)],
                "degrees": round(tithi_deg, 2)
            },
            "vara": {
                "number": vara_index + 1,
                "name": self.VARA_NAMES[vara_index]
            },
            "nakshatra": {
                "number": nakshatra_index + 1,
                "name": self.NAKSHATRA_NAMES[nakshatra_index],
                "degrees": round(moon_pos % 13.333333, 2)
            },
            "yoga": {
                "number": yoga_index + 1,
                "name": self.YOGA_NAMES[min(yoga_index, 26)],
                "degrees": round(yoga_deg, 2)
            },
            "karana": {
                "number": karana_index + 1,
                "name": self.KARANA_NAMES[karana_index]
            }
        }
    
    def calculate_birth_panchang(self, birth_data):
        """Calculate panchang for birth date"""
        return self.calculate_panchang(birth_data.date)