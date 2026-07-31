import swisseph as swe
from datetime import datetime, timedelta
import pytz
import math
from utils.timezone_service import parse_timezone_offset

class MuhuratCalculator:
    # Panchak begins at Dhanishta pada 3 (sidereal 20° Aquarius 00').
    PANCHAK_START_DEG = 300.0  # Dhanishta pada 3 begins at 20° Aquarius
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

    def _is_panchak(self, jd_ut):
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        longitude = float(swe.calc_ut(jd_ut, swe.MOON, flags)[0][0]) % 360.0
        return longitude >= self.PANCHAK_START_DEG

    def _panchak_intervals(self, sunrise_jd, sunset_jd):
        """Return UTC Julian-day intervals in which the Moon is in Panchak."""
        step = 30.0 / 1440.0
        start = sunrise_jd - 1.5
        end = sunset_jd + 1.5
        cursor = start
        previous = self._is_panchak(cursor)
        active_start = cursor if previous else None
        intervals = []
        while cursor < end:
            nxt = min(cursor + step, end)
            current = self._is_panchak(nxt)
            if current != previous:
                lo, hi = cursor, nxt
                for _ in range(32):
                    mid = (lo + hi) / 2.0
                    if self._is_panchak(mid) == previous:
                        lo = mid
                    else:
                        hi = mid
                boundary = (lo + hi) / 2.0
                if current:
                    active_start = boundary
                elif active_start is not None:
                    intervals.append((active_start, boundary))
                    active_start = None
            previous = current
            cursor = nxt
        if active_start is not None:
            intervals.append((active_start, end))
        return intervals

    def _panchak_for_day(self, sunrise_jd, sunset_jd, timezone, latitude, longitude):
        intervals = self._panchak_intervals(sunrise_jd, sunset_jd)
        clipped = []
        for start, end in intervals:
            start, end = max(start, sunrise_jd), min(end, sunset_jd)
            if end > start:
                clipped.append({
                    'start': self._jd_to_local_iso(start, timezone, latitude, longitude),
                    'end': self._jd_to_local_iso(end, timezone, latitude, longitude),
                })
        return {
            'is_panchak': bool(clipped),
            'name': 'Panchak',
            'reason': 'Moon is transiting Dhanishta pada 3/4, Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada or Revati.',
            'intervals': clipped,
        }

    @staticmethod
    def _overlaps_panchak(start_jd, end_jd, intervals):
        return any(start_jd < end and end_jd > start for start, end in intervals)

    def _build_day_muhurtas(
        self,
        sunrise_jd,
        day_duration,
        auspicious_muhurtas,
        suitability,
        timezone,
        latitude,
        longitude,
        panchak_intervals=(),
    ):
        muhurta_duration = day_duration / 15
        muhurtas = []
        for muhurta_num in sorted(auspicious_muhurtas):
            start_jd = sunrise_jd + ((muhurta_num - 1) * muhurta_duration / 24)
            end_jd = sunrise_jd + (muhurta_num * muhurta_duration / 24)
            if end_jd <= start_jd:
                end_jd = start_jd + (muhurta_duration / 24)
            is_panchak = self._overlaps_panchak(start_jd, end_jd, panchak_intervals)
            muhurtas.append({
                'muhurta': muhurta_num,
                'name': f'Muhurta {muhurta_num}',
                'start_time': self._jd_to_local_iso(start_jd, timezone, latitude, longitude),
                'end_time': self._jd_to_local_iso(end_jd, timezone, latitude, longitude),
                'duration_minutes': int(muhurta_duration * 60),
                'suitability': suitability,
                'panchak': is_panchak,
                'panchak_warning': 'Panchak is active during this window; confirm with a qualified priest before using it.' if is_panchak else None,
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
            panchak = self._panchak_for_day(sunrise_jd, sunset_jd, timezone, latitude, longitude)
            panchak_intervals = self._panchak_intervals(sunrise_jd, sunset_jd)
            muhurtas, muhurta_duration = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [2, 3, 5, 7, 10, 11, 13],
                'Excellent for marriage ceremonies',
                timezone,
                latitude,
                longitude,
                panchak_intervals,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'sunrise': self._jd_to_local_iso(sunrise_jd, timezone, latitude, longitude),
                'sunset': self._jd_to_local_iso(sunset_jd, timezone, latitude, longitude),
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
                'muhurta_duration_minutes': int(muhurta_duration * 60),
                'panchak': panchak,
            }
        except Exception as e:
            raise ValueError(f"Error calculating Vivah Muhurat: {str(e)}")
    
    def calculate_property_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate property purchase muhurat localized to user's city"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")

        try:
            sunrise_jd, sunset_jd, day_duration = self._sunrise_sunset_jd(date_str, latitude, longitude)
            panchak = self._panchak_for_day(sunrise_jd, sunset_jd, timezone, latitude, longitude)
            panchak_intervals = self._panchak_intervals(sunrise_jd, sunset_jd)
            muhurtas, _ = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [1, 3, 6, 10, 11, 13],
                'Favorable for property transactions',
                timezone,
                latitude,
                longitude,
                panchak_intervals,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
                'panchak': panchak,
            }
        except Exception as e:
            raise ValueError(f"Error calculating Property Muhurat: {str(e)}")
    
    def calculate_vehicle_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate vehicle purchase muhurat localized to user's city"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")

        try:
            sunrise_jd, sunset_jd, day_duration = self._sunrise_sunset_jd(date_str, latitude, longitude)
            panchak = self._panchak_for_day(sunrise_jd, sunset_jd, timezone, latitude, longitude)
            panchak_intervals = self._panchak_intervals(sunrise_jd, sunset_jd)
            muhurtas, _ = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [2, 5, 7, 10, 11],
                'Auspicious for vehicle purchase',
                timezone,
                latitude,
                longitude,
                panchak_intervals,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
                'panchak': panchak,
            }
        except Exception as e:
            raise ValueError(f"Error calculating Vehicle Muhurat: {str(e)}")
    
    def calculate_griha_pravesh_muhurat(self, date_str: str, latitude: float, longitude: float, timezone=None) -> dict:
        """Calculate house warming muhurat localized to user's city"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")

        try:
            sunrise_jd, sunset_jd, day_duration = self._sunrise_sunset_jd(date_str, latitude, longitude)
            panchak = self._panchak_for_day(sunrise_jd, sunset_jd, timezone, latitude, longitude)
            panchak_intervals = self._panchak_intervals(sunrise_jd, sunset_jd)
            muhurtas, _ = self._build_day_muhurtas(
                sunrise_jd,
                day_duration,
                [1, 3, 5, 10, 11, 13],
                'Perfect for house warming ceremony',
                timezone,
                latitude,
                longitude,
                panchak_intervals,
            )
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
                'muhurtas': muhurtas,
                'day_duration_hours': round(day_duration, 2),
                'panchak': panchak,
            }
        except Exception as e:
            raise ValueError(f"Error calculating Griha Pravesh Muhurat: {str(e)}")
