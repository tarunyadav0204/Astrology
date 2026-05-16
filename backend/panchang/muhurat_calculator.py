import swisseph as swe
from datetime import datetime, timedelta
import pytz
import math
from utils.timezone_service import parse_timezone_offset

class MuhuratCalculator:
    def __init__(self):
        # Set Lahiri Ayanamsa for Drik-level accuracy
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def _sunrise_sunset_jd(self, date_str: str, latitude: float, longitude: float):
        """
        Sunrise and sunset Julian days for the local calendar date.
        rise_trans must use a UT reference where SET follows RISE (fixes India/eastern longitudes).
        """
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        geopos = [float(longitude), float(latitude), 0.0]
        jd_ut = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.5)

        rise_res = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_RISE, geopos)
        set_res = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_SET, geopos)
        if rise_res[0] != 0 or set_res[0] != 0:
            raise ValueError("Could not calculate sunrise/sunset for given location")

        sunrise_jd = rise_res[1][0]
        sunset_jd = set_res[1][0]

        if sunset_jd <= sunrise_jd:
            rise_res = swe.rise_trans(jd_ut - 1.0, swe.SUN, swe.CALC_RISE, geopos)
            if rise_res[0] != 0:
                raise ValueError("Could not calculate sunrise for given location")
            sunrise_jd = rise_res[1][0]

        if sunset_jd <= sunrise_jd:
            raise ValueError("Invalid sunrise/sunset calculation for this date and location")

        day_duration = (sunset_jd - sunrise_jd) * 24
        return sunrise_jd, sunset_jd, day_duration

    def _build_day_muhurtas(
        self,
        sunrise_jd,
        day_duration,
        auspicious_muhurtas,
        suitability,
        timezone,
        latitude,
        longitude,
    ):
        muhurta_duration = day_duration / 15
        muhurtas = []
        for muhurta_num in sorted(auspicious_muhurtas):
            start_jd = sunrise_jd + ((muhurta_num - 1) * muhurta_duration / 24)
            end_jd = sunrise_jd + (muhurta_num * muhurta_duration / 24)
            if end_jd <= start_jd:
                end_jd = start_jd + (muhurta_duration / 24)
            muhurtas.append({
                'muhurta': muhurta_num,
                'name': f'Muhurta {muhurta_num}',
                'start_time': self._jd_to_local_iso(start_jd, timezone, latitude, longitude),
                'end_time': self._jd_to_local_iso(end_jd, timezone, latitude, longitude),
                'duration_minutes': int(muhurta_duration * 60),
                'suitability': suitability,
            })
        return muhurtas, muhurta_duration

    def _jd_to_local_iso(self, jd_val, timezone_name=None, latitude=None, longitude=None):
        """
        Julian Day (UT) -> local ISO string.
        Supports IANA names (Asia/Kolkata) and UTC offset strings (UTC+5:30).
        """
        if not jd_val:
            return None

        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
        dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))

        if timezone_name and str(timezone_name).startswith('UTC'):
            offset_hours = parse_timezone_offset(timezone_name, latitude, longitude)
            return (dt_utc + timedelta(hours=offset_hours)).isoformat()

        if timezone_name:
            try:
                local_zone = pytz.timezone(timezone_name)
                dt_utc_aware = pytz.utc.localize(dt_utc)
                return dt_utc_aware.astimezone(local_zone).isoformat()
            except Exception:
                pass

        offset_hours = parse_timezone_offset(timezone_name or 'UTC+0', latitude, longitude)
        return (dt_utc + timedelta(hours=offset_hours)).isoformat()
    
    def calculate_vivah_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate marriage muhurat for given date localized to user's city"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")

        try:
            sunrise_jd, sunset_jd, day_duration = self._sunrise_sunset_jd(date_str, latitude, longitude)
            muhurtas, muhurta_duration = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [2, 3, 5, 7, 10, 11, 13],
                'Excellent for marriage ceremonies',
                timezone,
                latitude,
                longitude,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'sunrise': self._jd_to_local_iso(sunrise_jd, timezone, latitude, longitude),
                'sunset': self._jd_to_local_iso(sunset_jd, timezone, latitude, longitude),
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
                'muhurta_duration_minutes': int(muhurta_duration * 60),
            }
        except Exception as e:
            raise ValueError(f"Error calculating Vivah Muhurat: {str(e)}")
    
    def calculate_property_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate property purchase muhurat localized to user's city"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")

        try:
            sunrise_jd, sunset_jd, day_duration = self._sunrise_sunset_jd(date_str, latitude, longitude)
            muhurtas, _ = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [1, 3, 6, 10, 11, 13],
                'Favorable for property transactions',
                timezone,
                latitude,
                longitude,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
            }
        except Exception as e:
            raise ValueError(f"Error calculating Property Muhurat: {str(e)}")
    
    def calculate_vehicle_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate vehicle purchase muhurat localized to user's city"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")

        try:
            sunrise_jd, sunset_jd, day_duration = self._sunrise_sunset_jd(date_str, latitude, longitude)
            muhurtas, _ = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [2, 5, 7, 10, 11],
                'Auspicious for vehicle purchase',
                timezone,
                latitude,
                longitude,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
            }
        except Exception as e:
            raise ValueError(f"Error calculating Vehicle Muhurat: {str(e)}")
    
    def calculate_griha_pravesh_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate house warming muhurat localized to user's city"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")

        try:
            sunrise_jd, sunset_jd, day_duration = self._sunrise_sunset_jd(date_str, latitude, longitude)
            muhurtas, _ = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [1, 3, 5, 10, 11, 13],
                'Perfect for house warming ceremony',
                timezone,
                latitude,
                longitude,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
            }
        except Exception as e:
            raise ValueError(f"Error calculating Griha Pravesh Muhurat: {str(e)}")
