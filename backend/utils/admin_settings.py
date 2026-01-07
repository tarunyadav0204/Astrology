import sqlite3
from typing import Optional

def get_setting(key: str) -> Optional[str]:
    """Get admin setting value"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except:
        return None

def is_debug_logging_enabled() -> bool:
    """Check if debug logging is enabled"""
    value = get_setting('debug_logging_enabled')
    return value == 'true' if value else False
