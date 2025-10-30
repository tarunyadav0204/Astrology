import swisseph as swe
from datetime import datetime, timedelta
import math

class MuhuratCalculator:
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def calculate_vivah_muhurat(self, date_str: str, latitude: float, longitude: float) -> dict:
        """Calculate marriage muhurat for given date"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.0)
            
            # Calculate sunrise and sunset
            geopos = [float(longitude), float(latitude), 0.0]
            sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
            
            if sunrise_result[0] != 0 or sunset_result[0] != 0:
                raise ValueError("Could not calculate sunrise/sunset for given location")
                
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]
            
            # Validate sunrise/sunset order
            if sunset_jd <= sunrise_jd:
                raise ValueError("Invalid sunrise/sunset calculation")
                
            # Day duration in hours
            day_duration = (sunset_jd - sunrise_jd) * 24
            muhurta_duration = day_duration / 15  # Each muhurta duration in hours
            
            # Marriage muhurtas (typically 2nd, 3rd, 5th, 7th, 10th, 11th, 13th)
            # Sort in chronological order (1st muhurta is earliest)
            auspicious_muhurtas = [2, 3, 5, 7, 10, 11, 13]
            
            muhurtas = []
            for muhurta_num in sorted(auspicious_muhurtas):
                # Calculate start and end times correctly
                start_jd = sunrise_jd + ((muhurta_num - 1) * muhurta_duration / 24)
                end_jd = sunrise_jd + (muhurta_num * muhurta_duration / 24)
                
                # Ensure proper time ordering
                if end_jd <= start_jd:
                    end_jd = start_jd + (muhurta_duration / 24)
                
                muhurtas.append({
                    'muhurta': muhurta_num,
                    'name': f'Muhurta {muhurta_num}',
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Excellent for marriage ceremonies'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude},
                'sunrise': self._jd_to_iso(sunrise_jd),
                'sunset': self._jd_to_iso(sunset_jd),
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
                'muhurta_duration_minutes': int(muhurta_duration * 60)
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Vivah Muhurat: {str(e)}")
    
    def calculate_property_muhurat(self, date_str: str, latitude: float, longitude: float) -> dict:
        """Calculate property purchase muhurat"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.0)
            
            # Calculate sunrise and sunset
            geopos = [float(longitude), float(latitude), 0.0]
            sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
            
            if sunrise_result[0] != 0 or sunset_result[0] != 0:
                raise ValueError("Could not calculate sunrise/sunset for given location")
                
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]
            
            # Validate sunrise/sunset order
            if sunset_jd <= sunrise_jd:
                raise ValueError("Invalid sunrise/sunset calculation")
                
            # Day duration in hours
            day_duration = (sunset_jd - sunrise_jd) * 24
            muhurta_duration = day_duration / 15
            
            # Property muhurtas (typically 1st, 3rd, 6th, 10th, 11th, 13th)
            auspicious_muhurtas = [1, 3, 6, 10, 11, 13]
            
            muhurtas = []
            for muhurta_num in sorted(auspicious_muhurtas):
                start_jd = sunrise_jd + ((muhurta_num - 1) * muhurta_duration / 24)
                end_jd = sunrise_jd + (muhurta_num * muhurta_duration / 24)
                
                muhurtas.append({
                    'muhurta': muhurta_num,
                    'name': f'Muhurta {muhurta_num}',
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Favorable for property transactions'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude},
                'muhurtas': muhurtas,
                'day_duration_hours': day_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Property Muhurat: {str(e)}")
    
    def calculate_vehicle_muhurat(self, date_str: str, latitude: float, longitude: float) -> dict:
        """Calculate vehicle purchase muhurat"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.0)
            
            # Calculate sunrise and sunset
            geopos = [float(longitude), float(latitude), 0.0]
            sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
            
            if sunrise_result[0] != 0 or sunset_result[0] != 0:
                raise ValueError("Could not calculate sunrise/sunset for given location")
                
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]
            
            # Validate sunrise/sunset order
            if sunset_jd <= sunrise_jd:
                raise ValueError("Invalid sunrise/sunset calculation")
                
            # Day duration in hours
            day_duration = (sunset_jd - sunrise_jd) * 24
            muhurta_duration = day_duration / 15
            
            # Vehicle muhurtas (typically 2nd, 5th, 7th, 10th, 11th)
            auspicious_muhurtas = [2, 5, 7, 10, 11]
            
            muhurtas = []
            for muhurta_num in sorted(auspicious_muhurtas):
                start_jd = sunrise_jd + ((muhurta_num - 1) * muhurta_duration / 24)
                end_jd = sunrise_jd + (muhurta_num * muhurta_duration / 24)
                
                muhurtas.append({
                    'muhurta': muhurta_num,
                    'name': f'Muhurta {muhurta_num}',
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Auspicious for vehicle purchase'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude},
                'muhurtas': muhurtas,
                'day_duration_hours': day_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Vehicle Muhurat: {str(e)}")
    
    def calculate_griha_pravesh_muhurat(self, date_str: str, latitude: float, longitude: float) -> dict:
        """Calculate house warming muhurat"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.0)
            
            # Calculate sunrise and sunset
            geopos = [float(longitude), float(latitude), 0.0]
            sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
            
            if sunrise_result[0] != 0 or sunset_result[0] != 0:
                raise ValueError("Could not calculate sunrise/sunset for given location")
                
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]
            
            # Validate sunrise/sunset order
            if sunset_jd <= sunrise_jd:
                raise ValueError("Invalid sunrise/sunset calculation")
                
            # Day duration in hours
            day_duration = (sunset_jd - sunrise_jd) * 24
            muhurta_duration = day_duration / 15
            
            # Griha Pravesh muhurtas (typically 1st, 3rd, 5th, 10th, 11th, 13th)
            auspicious_muhurtas = [1, 3, 5, 10, 11, 13]
            
            muhurtas = []
            for muhurta_num in sorted(auspicious_muhurtas):
                start_jd = sunrise_jd + ((muhurta_num - 1) * muhurta_duration / 24)
                end_jd = sunrise_jd + (muhurta_num * muhurta_duration / 24)
                
                muhurtas.append({
                    'muhurta': muhurta_num,
                    'name': f'Muhurta {muhurta_num}',
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Perfect for house warming ceremony'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude},
                'muhurtas': muhurtas,
                'day_duration_hours': day_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Griha Pravesh Muhurat: {str(e)}")
    
    def _jd_to_iso(self, jd):
        """Convert Julian Day to ISO format datetime string"""
        try:
            # Use proper UTC conversion
            year, month, day, hour, minute, second = swe.jdut1_to_utc(jd, 1)
            dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            return dt.isoformat()
        except Exception as e:
            # Fallback method
            import math
            jd_frac = jd - math.floor(jd)
            hours = jd_frac * 24
            hour = int(hours)
            minutes = (hours - hour) * 60
            minute = int(minutes)
            second = int((minutes - minute) * 60)
            
            # Get date from JD
            year, month, day = swe.revjul(int(jd))
            dt = datetime(int(year), int(month), int(day), hour, minute, second)
            return dt.isoformat()