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

# Simple cache for timezone lookups to avoid repeated expensive operations
_timezone_cache = {}

# Reusable TimezoneFinder instance (expensive to create, should be singleton)
_timezone_finder = None

def _get_timezone_finder():
    """Get or create singleton TimezoneFinder instance"""
    global _timezone_finder
    if _timezone_finder is None:
        _timezone_finder = TimezoneFinder()
    return _timezone_finder

def get_timezone_from_coordinates(lat: float, lon: float) -> str:
    """
    Professional timezone detection from coordinates using timezonefinder + pytz
    Uses caching to avoid repeated expensive lookups
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
    
    Returns:
        str: UTC offset format (e.g., 'UTC+5:30', 'UTC-8:00')
    """
    if not HAS_TIMEZONE_LIBS:
        raise ImportError("Required libraries not installed: pip install timezonefinder pytz")
    
    # Create cache key (round to 2 decimal places for reasonable caching)
    cache_key = (round(lat, 2), round(lon, 2))
    
    # Check cache first
    if cache_key in _timezone_cache:
        return _timezone_cache[cache_key]
    
    try:
        # Get IANA timezone name from coordinates using singleton instance
        tf = _get_timezone_finder()
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
            result = f"UTC{sign}{hours}"
        else:
            result = f"UTC{sign}{hours}:{minutes:02d}"
        
        # Cache the result
        _timezone_cache[cache_key] = result
        
        return result
            
    except Exception as e:
        raise RuntimeError(f"Timezone detection failed for ({lat}, {lon}): {e}")


def parse_timezone_offset(timezone_str, latitude: float = None, longitude: float = None) -> float:
    """
    Parse timezone string to UTC offset in hours (as float)
    Uses coordinate-based detection if timezone_str is empty or invalid
    
    Args:
        timezone_str: Timezone string (e.g., 'UTC+5:30', 'UTC-8') or float
        latitude: Optional latitude for coordinate-based detection
        longitude: Optional longitude for coordinate-based detection
    
    Returns:
        float: UTC offset in hours (e.g., 5.5 for UTC+5:30, -8.0 for UTC-8)
    """
    # Handle float input (already parsed offset)
    if isinstance(timezone_str, (int, float)):
        return float(timezone_str)
    
    # Handle None input
    if timezone_str is None:
        timezone_str = ''
    
    # Convert to string if needed
    timezone_str = str(timezone_str)
    
    # Handle direct numeric string (e.g., '5.5')
    try:
        result = float(timezone_str)
        return result
    except (ValueError, TypeError):
        pass
    
    # If timezone is 'UTC+0', 'UTC', or empty, try coordinate-based detection
    if (not timezone_str or 
        timezone_str in ['UTC', 'UTC+0', 'UTC-0', 'UTC0'] or
        timezone_str.strip() == ''):
        if latitude is not None and longitude is not None:
            try:
                detected_tz = get_timezone_from_coordinates(latitude, longitude)
                timezone_str = detected_tz
                # Removed log - already logged in main.py
            except Exception as e:
                print(f"⚠️ TIMEZONE: Failed to detect from coordinates: {e}")
                return 0.0  # Fall back to UTC
        else:
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
                return result
            else:
                # Format: UTC+5 or UTC-8
                result = float(tz_str)
                return result
    
    return 0.0