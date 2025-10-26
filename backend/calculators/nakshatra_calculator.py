from .base_calculator import BaseCalculator

class NakshatraCalculator(BaseCalculator):
    """Calculate Nakshatra positions, lords, and padas"""
    
    def __init__(self, birth_data=None, chart_data=None):
        super().__init__(birth_data, chart_data)
        
        self.NAKSHATRA_NAMES = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya',
            'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
            'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
            'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        self.NAKSHATRA_LORDS = [
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
            'Saturn', 'Mercury', 'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
            'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus',
            'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
        ]
        
        self.NAKSHATRA_DEITIES = [
            'Ashwini Kumaras', 'Yama', 'Agni', 'Brahma', 'Soma', 'Rudra', 'Aditi', 'Brihaspati',
            'Nagas', 'Pitrs', 'Bhaga', 'Aryaman', 'Savitar', 'Tvashtar', 'Vayu',
            'Indra-Agni', 'Mitra', 'Indra', 'Nirrti', 'Apas', 'Vishve Devas', 'Vishnu',
            'Vasus', 'Varuna', 'Aja Ekapada', 'Ahir Budhnya', 'Pushan'
        ]
        
        self.NAKSHATRA_QUALITIES = [
            'Swift', 'Creative', 'Sharp', 'Growing', 'Soft', 'Sharp', 'Movable', 'Swift',
            'Sharp', 'Fierce', 'Fierce', 'Fixed', 'Swift', 'Soft', 'Movable',
            'Mixed', 'Soft', 'Sharp', 'Sharp', 'Fierce', 'Fixed', 'Movable',
            'Movable', 'Movable', 'Fierce', 'Fixed', 'Swift'
        ]
    
    def calculate_nakshatra_positions(self):
        """Calculate nakshatra positions for all planets"""
        planets = self.chart_data.get('planets', {})
        nakshatra_positions = {}
        
        for planet_name, planet_data in planets.items():
            longitude = planet_data.get('longitude', 0)
            nakshatra_info = self._get_nakshatra_info(longitude)
            
            nakshatra_positions[planet_name] = {
                'longitude': longitude,
                'nakshatra_number': nakshatra_info['number'],
                'nakshatra_name': nakshatra_info['name'],
                'nakshatra_lord': nakshatra_info['lord'],
                'nakshatra_deity': nakshatra_info['deity'],
                'nakshatra_quality': nakshatra_info['quality'],
                'pada': nakshatra_info['pada'],
                'degrees_in_nakshatra': nakshatra_info['degrees_in_nakshatra']
            }
        
        return nakshatra_positions
    
    def _get_nakshatra_info(self, longitude):
        """Get nakshatra information for given longitude"""
        # Each nakshatra is 13°20' (13.333333°)
        nakshatra_span = 360 / 27
        nakshatra_index = int(longitude / nakshatra_span)
        
        # Ensure index is within bounds
        nakshatra_index = min(nakshatra_index, 26)
        
        # Calculate degrees within nakshatra
        degrees_in_nakshatra = longitude % nakshatra_span
        
        # Calculate pada (each nakshatra has 4 padas of 3°20' each)
        pada_span = nakshatra_span / 4
        pada = int(degrees_in_nakshatra / pada_span) + 1
        
        return {
            'number': nakshatra_index + 1,
            'name': self.NAKSHATRA_NAMES[nakshatra_index],
            'lord': self.NAKSHATRA_LORDS[nakshatra_index],
            'deity': self.NAKSHATRA_DEITIES[nakshatra_index],
            'quality': self.NAKSHATRA_QUALITIES[nakshatra_index],
            'pada': pada,
            'degrees_in_nakshatra': round(degrees_in_nakshatra, 2)
        }
    
    def get_moon_nakshatra(self):
        """Get Moon's nakshatra (birth star)"""
        positions = self.calculate_nakshatra_positions()
        return positions.get('Moon', {})
    
    def get_ascendant_nakshatra(self):
        """Get Ascendant's nakshatra"""
        ascendant_longitude = self.chart_data.get('ascendant', 0)
        return self._get_nakshatra_info(ascendant_longitude)
    
    def get_nakshatra_compatibility(self, nakshatra1, nakshatra2):
        """Calculate basic nakshatra compatibility"""
        # Simplified compatibility based on nakshatra numbers
        diff = abs(nakshatra1 - nakshatra2)
        
        # Vedic compatibility rules (simplified)
        if diff in [0]:  # Same nakshatra
            return {'score': 50, 'type': 'Neutral'}
        elif diff in [1, 26]:  # Adjacent nakshatras
            return {'score': 60, 'type': 'Good'}
        elif diff in [9, 18]:  # Trine nakshatras
            return {'score': 80, 'type': 'Excellent'}
        elif diff in [13, 14]:  # Opposition nakshatras
            return {'score': 30, 'type': 'Challenging'}
        else:
            return {'score': 55, 'type': 'Average'}
    
    def analyze_nakshatra_yogas(self):
        """Analyze special nakshatra combinations"""
        positions = self.calculate_nakshatra_positions()
        yogas = []
        
        moon_nak = positions.get('Moon', {}).get('nakshatra_number', 0)
        sun_nak = positions.get('Sun', {}).get('nakshatra_number', 0)
        
        # Ganda Mool Nakshatras
        ganda_mool = [1, 2, 9, 18, 19, 27]  # Ashwini, Bharani, Ashlesha, Jyeshtha, Mula, Revati
        
        if moon_nak in ganda_mool:
            yogas.append({
                'name': 'Ganda Mool',
                'description': 'Moon in Ganda Mool nakshatra - requires special remedies',
                'planet': 'Moon',
                'nakshatra': positions['Moon']['nakshatra_name']
            })
        
        # Abhijit Nakshatra (special 28th nakshatra)
        if 276.67 <= positions.get('Moon', {}).get('longitude', 0) <= 280:
            yogas.append({
                'name': 'Abhijit',
                'description': 'Moon in Abhijit nakshatra - highly auspicious',
                'planet': 'Moon',
                'nakshatra': 'Abhijit'
            })
        
        return yogas