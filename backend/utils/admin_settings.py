import sqlite3
from typing import Optional

# Allowed Gemini model IDs (with models/ prefix for API). Used by admin UI and as fallbacks.
GEMINI_MODEL_OPTIONS = [
    ("models/gemini-3.1-pro-preview", "Gemini 3.1 Pro (New – complex reasoning)"),
    ("models/gemini-3.1-flash-lite-preview", "Gemini 3.1 Flash Lite (New – high-volume, low-cost)"),
    ("models/gemini-3-flash-preview", "Gemini 3 Flash (Preview)"),
    ("models/gemini-3-pro-preview", "Gemini 3 Pro (Retiring Mar 2026)"),
    ("models/gemini-2.5-pro", "Gemini 2.5 Pro (Stable)"),
    ("models/gemini-2.5-flash", "Gemini 2.5 Flash (Stable)"),
    ("models/gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite (Stable)"),
    ("models/gemini-2.0-flash-001", "Gemini 2.0 Flash (Stable)"),
    ("models/gemini-2.0-flash-lite-001", "Gemini 2.0 Flash Lite (Stable)"),
]

DEFAULT_GEMINI_CHAT_MODEL = "models/gemini-2.5-flash"
DEFAULT_GEMINI_PREMIUM_MODEL = "models/gemini-3-flash-preview"


def _ensure_admin_settings_table(conn: sqlite3.Connection) -> None:
    """Create admin_settings table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def get_setting(key: str) -> Optional[str]:
    """Get admin setting value"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        _ensure_admin_settings_table(conn)
        cursor.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception:
        return None


def get_gemini_chat_model() -> str:
    """Model ID for standard chat (e.g. models/gemini-2.5-flash). From admin_settings or default."""
    value = get_setting("gemini_chat_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_GEMINI_CHAT_MODEL


def get_gemini_premium_model() -> str:
    """Model ID for premium chat. From admin_settings or default."""
    value = get_setting("gemini_premium_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_GEMINI_PREMIUM_MODEL


def is_debug_logging_enabled() -> bool:
    """Check if debug logging is enabled"""
    value = get_setting('debug_logging_enabled')
    return value == 'true' if value else False
