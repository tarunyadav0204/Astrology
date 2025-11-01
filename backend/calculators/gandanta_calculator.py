from .base_calculator import BaseCalculator

class GandantaCalculator(BaseCalculator):
    """Calculate Gandanta positions - generic for all analysis types"""
    
    def __init__(self, chart_data=None):
        super().__init__(chart_data or {})
        
        # Gandanta ranges in degrees (traditional 3°20' each side)
        self.GANDANTA_RANGES = {
            'pisces_aries': {
                'start': 356.666667,  # 26°40' Pisces (356°40')
                'end': 3.333333,      # 3°20' Aries
                'name': 'Revati-Ashwini Gandanta'
            },
            'cancer_leo': {
                'start': 116.666667,  # 26°40' Cancer
                'end': 123.333333,    # 3°20' Leo
                'name': 'Ashlesha-Magha Gandanta'
            },
            'scorpio_sagittarius': {
                'start': 236.666667,  # 26°40' Scorpio
                'end': 243.333333,    # 3°20' Sagittarius
                'name': 'Jyeshtha-Mula Gandanta'
            }
        }
    
    def calculate_gandanta_analysis(self):
        """Calculate complete Gandanta analysis for chart"""
        if 'planets' not in self.chart_data:
            raise KeyError('Chart data missing planets information')
        
        analysis = {
            'planets_in_gandanta': [],
            'lagna_gandanta': self._check_lagna_gandanta(),
            'moon_gandanta': self._check_moon_gandanta()
        }
        
        # Check each planet for Gandanta
        for planet_name, planet_data in self.chart_data['planets'].items():
            gandanta_info = self._check_planet_gandanta(planet_name, planet_data['longitude'])
            if gandanta_info['is_gandanta']:
                analysis['planets_in_gandanta'].append({
                    'planet': planet_name,
                    'gandanta_info': gandanta_info
                })
        
        return analysis
    
    def _check_planet_gandanta(self, planet_name, longitude):
        """Check if planet is in Gandanta"""
        for gandanta_type, gandanta_range in self.GANDANTA_RANGES.items():
            if self._is_in_gandanta_range(longitude, gandanta_range):
                return {
                    'is_gandanta': True,
                    'gandanta_type': gandanta_type,
                    'gandanta_name': gandanta_range['name'],
                    'longitude': longitude,
                    'distance_from_junction': self._calculate_distance_from_junction(longitude, gandanta_range),
                    'intensity': self._calculate_gandanta_intensity(longitude, gandanta_range)
                }
        
        return {'is_gandanta': False}
    
    def _is_in_gandanta_range(self, longitude, gandanta_range):
        """Check if longitude is within Gandanta range"""
        start = gandanta_range['start']
        end = gandanta_range['end']
        
        # Handle wrap-around for Pisces-Aries
        if start > end:  # Crosses 0 degrees
            return longitude >= start or longitude <= end
        else:
            return start <= longitude <= end
    
    def _calculate_distance_from_junction(self, longitude, gandanta_range):
        """Calculate distance from exact junction point"""
        if gandanta_range['start'] > gandanta_range['end']:  # Pisces-Aries
            junction_point = 0.0  # 0° Aries
            if longitude >= 356:
                distance = 360 - longitude
            else:
                distance = longitude
        else:
            junction_point = gandanta_range['start'] + 4  # 30° of previous sign
            distance = abs(longitude - junction_point)
        
        return round(distance, 2)
    
    def _calculate_gandanta_intensity(self, longitude, gandanta_range):
        """Calculate Gandanta intensity (closer to junction = higher intensity)"""
        distance = self._calculate_distance_from_junction(longitude, gandanta_range)
        
        if distance <= 1.0:
            return 'Extreme'
        elif distance <= 2.0:
            return 'High'
        elif distance <= 3.0:
            return 'Medium'
        else:
            return 'Low'
    
    def _check_lagna_gandanta(self):
        """Check if Lagna (Ascendant) is in Gandanta"""
        if 'ascendant' not in self.chart_data:
            raise KeyError('Chart data missing ascendant information')
        
        ascendant_longitude = self.chart_data['ascendant']
        gandanta_info = self._check_planet_gandanta('Lagna', ascendant_longitude)
        
        if gandanta_info['is_gandanta']:
            return {
                'is_gandanta': True,
                'gandanta_info': gandanta_info
            }
        
        return {'is_gandanta': False}
    
    def _check_moon_gandanta(self):
        """Check if Moon is in Gandanta"""
        if 'Moon' not in self.chart_data['planets']:
            raise KeyError('Moon not found in planets data')
        
        moon_longitude = self.chart_data['planets']['Moon']['longitude']
        gandanta_info = self._check_planet_gandanta('Moon', moon_longitude)
        
        if gandanta_info['is_gandanta']:
            return {
                'is_gandanta': True,
                'gandanta_info': gandanta_info
            }
        
        return {'is_gandanta': False}
    
