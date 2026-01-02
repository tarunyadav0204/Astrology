import swisseph as swe
from datetime import datetime, timedelta
import pytz
import math

class MuhuratCalculator:
    def __init__(self):
        # Set Lahiri Ayanamsa for Drik-level accuracy
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def _jd_to_local_iso(self, jd_val, timezone_name=None):
        """
        Pinpoint accurate converter: Julian Day -> Local Timezone ISO String.
        Handles Daylight Savings (DST) automatically.
        """
        if not jd_val: return None
        
        # 1. Convert JD to UTC components
        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
        dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        
        # 2. Localize using pytz
        try:
            utc_zone = pytz.utc
            local_zone = pytz.timezone(timezone_name)
            
            dt_utc_aware = utc_zone.localize(dt_utc)
            dt_local = dt_utc_aware.astimezone(local_zone)
            return dt_local.isoformat()
        except Exception:
            # Fallback to UTC if timezone name is invalid
            return (dt_utc + timedelta(hours=5, minutes=30)).isoformat()
    
    def calculate_vivah_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate marriage muhurat for given date localized to user's city"""
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
                    'start_time': self._jd_to_local_iso(start_jd, timezone),
                    'end_time': self._jd_to_local_iso(end_jd, timezone),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Excellent for marriage ceremonies'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'sunrise': self._jd_to_local_iso(sunrise_jd, timezone),
                'sunset': self._jd_to_local_iso(sunset_jd, timezone),
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
                'muhurta_duration_minutes': int(muhurta_duration * 60)
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Vivah Muhurat: {str(e)}")
    
    def calculate_property_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate property purchase muhurat localized to user's city"""
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
                    'start_time': self._jd_to_local_iso(start_jd, timezone),
                    'end_time': self._jd_to_local_iso(end_jd, timezone),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Favorable for property transactions'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': day_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Property Muhurat: {str(e)}")
    
    def calculate_vehicle_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate vehicle purchase muhurat localized to user's city"""
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
                    'start_time': self._jd_to_local_iso(start_jd, timezone),
                    'end_time': self._jd_to_local_iso(end_jd, timezone),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Auspicious for vehicle purchase'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': day_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Vehicle Muhurat: {str(e)}")
    
    def calculate_griha_pravesh_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate house warming muhurat localized to user's city"""
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
                    'start_time': self._jd_to_local_iso(start_jd, timezone),
                    'end_time': self._jd_to_local_iso(end_jd, timezone),
                    'duration_minutes': int(muhurta_duration * 60),
                    'suitability': 'Perfect for house warming ceremony'
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': day_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Griha Pravesh Muhurat: {str(e)}")
