from typing import Optional, Any

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

DEFAULT_GEMINI_CHAT_MODEL = "models/gemini-3.1-flash-lite-preview"
DEFAULT_GEMINI_PREMIUM_MODEL = "models/gemini-3.1-pro-preview"
DEFAULT_GEMINI_ANALYSIS_MODEL = "models/gemini-3.1-flash-lite-preview"


def _ensure_admin_settings_table(conn: Any) -> None:
    """Create admin_settings table if it does not exist (works for sqlite + postgres)."""
    from db import execute
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS admin_settings (
            "key" TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )


def get_setting(key: str) -> Optional[str]:
    """Get admin setting value"""
    try:
        from db import get_conn, execute

        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            cursor = execute(conn, 'SELECT value FROM admin_settings WHERE "key" = ?', (key,))
            result = cursor.fetchone()
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


def get_gemini_analysis_model() -> str:
    """Model ID for analysis features (health, wealth, career, karma, physical, etc.). From admin_settings or default."""
    value = get_setting("gemini_analysis_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_GEMINI_ANALYSIS_MODEL


def is_debug_logging_enabled() -> bool:
    """Check if debug logging is enabled"""
    value = get_setting('debug_logging_enabled')
    return value == 'true' if value else False


PODCAST_PROVIDER_TTS = "tts"
PODCAST_PROVIDER_NOTEBOOK_LM = "notebook_lm"


def get_podcast_provider() -> str:
    """Which podcast pipeline to use: 'tts' (Gemini script + Google TTS) or 'notebook_lm' (Discovery Engine Podcast API)."""
    value = get_setting("podcast_provider")
    if value and value.strip() in (PODCAST_PROVIDER_TTS, PODCAST_PROVIDER_NOTEBOOK_LM):
        return value.strip()
    return PODCAST_PROVIDER_TTS
