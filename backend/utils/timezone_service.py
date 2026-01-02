"""
Professional timezone detection service using coordinates
Returns UTC offset format for astrology calculations
"""
try:
    from timezonefinder import TimezoneFinder
    import pytz
    from datetime import datetime
    HAS_TIMEZONE_LIBS = True
except ImportError:
    HAS_TIMEZONE_LIBS = False


def get_timezone_from_coordinates(lat: float, lon: float) -> str:
    """
    Professional timezone detection from coordinates using timezonefinder + pytz
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
    
    Returns:
        str: UTC offset format (e.g., 'UTC+5:30', 'UTC-8:00')
    """
    if not HAS_TIMEZONE_LIBS:
        raise ImportError("Required libraries not installed: pip install timezonefinder pytz")
    
    try:
        # Get IANA timezone name from coordinates
        tf = TimezoneFinder()
        iana_timezone = tf.timezone_at(lat=lat, lng=lon)
        
        if not iana_timezone:
            raise ValueError(f"No timezone found for coordinates ({lat}, {lon})")
        
        # Get current UTC offset using pytz
        tz = pytz.timezone(iana_timezone)
        now = datetime.now(tz)
        offset_seconds = now.utcoffset().total_seconds()
        offset_hours = offset_seconds / 3600
        
        # Format as UTC±HH:MM
        hours = int(abs(offset_hours))
        minutes = int((abs(offset_hours) - hours) * 60)
        sign = '+' if offset_hours >= 0 else '-'
        
        if minutes == 0:
            return f"UTC{sign}{hours}"
        else:
            return f"UTC{sign}{hours}:{minutes:02d}"
            
    except Exception as e:
        raise RuntimeError(f"Timezone detection failed for ({lat}, {lon}): {e}")


def parse_timezone_offset(timezone_str, latitude: float = None, longitude: float = None) -> float:
    """
    Parse timezone string to UTC offset in hours (as float)
    Uses coordinate-based detection if timezone_str is empty
    
    Args:
        timezone_str: Timezone string (e.g., 'UTC+5:30', 'UTC-8') or float
        latitude: Optional latitude for coordinate-based detection
        longitude: Optional longitude for coordinate-based detection
    
    Returns:
        float: UTC offset in hours (e.g., 5.5 for UTC+5:30, -8.0 for UTC-8)
    """
    print(f"🌍 TIMEZONE SERVICE: Input timezone_str='{timezone_str}', lat={latitude}, lon={longitude}")
    
    # Handle float input (already parsed offset)
    if isinstance(timezone_str, (int, float)):
        print(f"🌍 TIMEZONE SERVICE: Float input detected, returning {float(timezone_str)}")
        return float(timezone_str)
    
    # Handle None input
    if timezone_str is None:
        timezone_str = ''
    
    # Convert to string if needed
    timezone_str = str(timezone_str)
    
    # Handle direct numeric string (e.g., '5.5')
    try:
        result = float(timezone_str)
        print(f"🌍 TIMEZONE SERVICE: Numeric string '{timezone_str}' parsed to {result}")
        return result
    except (ValueError, TypeError):
        pass
    
    # If no timezone string provided, try coordinate-based detection
    if not timezone_str and latitude is not None and longitude is not None:
        print(f"🌍 TIMEZONE SERVICE: No timezone string, using coordinates ({latitude}, {longitude})")
        try:
            detected_tz = get_timezone_from_coordinates(latitude, longitude)
            print(f"🌍 TIMEZONE SERVICE: Detected timezone: {detected_tz}")
            timezone_str = detected_tz
        except Exception as e:
            print(f"❌ TIMEZONE SERVICE: Coordinate detection failed: {e}")
            pass  # Fall through to default
    
    if not timezone_str:
        print(f"🌍 TIMEZONE SERVICE: No timezone available, defaulting to UTC (0.0)")
        return 0.0  # UTC default
    
    # Parse UTC format
    if timezone_str.startswith('UTC'):
        tz_str = timezone_str[3:]  # Remove 'UTC' prefix
        if tz_str:
            if ':' in tz_str:
                # Format: UTC+5:30 or UTC-8:00
                sign = 1 if tz_str[0] == '+' else -1
                parts = tz_str[1:].split(':')
                result = sign * (float(parts[0]) + float(parts[1])/60)
                print(f"🌍 TIMEZONE SERVICE: Parsed '{timezone_str}' to {result}")
                return result
            else:
                # Format: UTC+5 or UTC-8
                result = float(tz_str)
                print(f"🌍 TIMEZONE SERVICE: Parsed '{timezone_str}' to {result}")
                return result
    
    print(f"🌍 TIMEZONE SERVICE: Could not parse '{timezone_str}', defaulting to UTC (0.0)")
    return 0.0