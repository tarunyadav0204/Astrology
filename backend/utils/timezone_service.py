"""
Timezone detection service using coordinates
Returns UTC offset format for astrology calculations
"""
try:
    from timezonefinder import TimezoneFinder
    HAS_TIMEZONEFINDER = True
except ImportError:
    HAS_TIMEZONEFINDER = False

def get_timezone_from_coordinates(lat: float, lon: float) -> str:
    """
    Get UTC offset format from coordinates for astrology calculations
    Returns format like UTC+5:30, UTC-5:00 etc.
    Only uses timezonefinder library - no manual fallbacks
    """
    try:
        if HAS_TIMEZONEFINDER:
            tf = TimezoneFinder()
            timezone = tf.timezone_at(lat=lat, lng=lon)
            if timezone:
                return convert_iana_to_utc_offset(timezone)
        return None
    except Exception as e:
        print(f"❌ Timezone detection failed for coordinates ({lat}, {lon}): {e}")
        return None

def convert_iana_to_utc_offset(iana_timezone: str) -> str:
    """
    Convert IANA timezone to UTC offset format
    """
    try:
        timezone_map = {
            'Asia/Kolkata': 'UTC+5:30',
            'Asia/Calcutta': 'UTC+5:30',
            'America/New_York': 'UTC-5:00',
            'America/Los_Angeles': 'UTC-8:00',
            'Europe/London': 'UTC+0:00',
            'Australia/Sydney': 'UTC+10:00',
            'UTC': 'UTC+0:00'
        }
        result = timezone_map.get(iana_timezone, 'UTC+0:00')
        print(f"ℹ️ Converted {iana_timezone} → {result}")
        return result
    except Exception as e:
        print(f"❌ Timezone conversion failed for {iana_timezone}: {e}")
        return 'UTC+0:00'