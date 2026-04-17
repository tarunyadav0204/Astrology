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

# Chat only: which vendor handles `GeminiChatAnalyzer.generate_chat_response` (analysis stays on Gemini).
CHAT_LLM_GEMINI = "gemini"
CHAT_LLM_OPENAI = "openai"
CHAT_LLM_DEEPSEEK = "deepseek"

# OpenAI model IDs for Chat Completions API (no `models/` prefix).
OPENAI_CHAT_MODEL_OPTIONS = [
    ("gpt-5.4-pro", "OpenAI GPT-5.4 Pro (large context / premium)"),
    ("gpt-4o-mini", "OpenAI GPT-4o mini (fast, low cost)"),
    ("gpt-4o", "OpenAI GPT-4o (balanced)"),
    ("gpt-4-turbo", "OpenAI GPT-4 Turbo"),
    ("o4-mini", "OpenAI o4-mini (reasoning)"),
]

DEFAULT_OPENAI_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_PREMIUM_MODEL = "gpt-4o"

DEEPSEEK_CHAT_MODEL_OPTIONS = [
    ("deepseek-chat-3.2", "DeepSeek Chat 3.2"),
    ("deepseek-reasoner", "DeepSeek Reasoner"),
]
DEFAULT_DEEPSEEK_CHAT_MODEL = "deepseek-chat-3.2"
DEFAULT_DEEPSEEK_PREMIUM_MODEL = "deepseek-reasoner"


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


def get_chat_llm_provider() -> str:
    """Which LLM vendor runs astrological chat: 'gemini', 'openai', or 'deepseek'."""
    value = (get_setting("chat_llm_provider") or "").strip().lower()
    if value == CHAT_LLM_DEEPSEEK:
        return CHAT_LLM_DEEPSEEK
    if value == CHAT_LLM_OPENAI:
        return CHAT_LLM_OPENAI
    return CHAT_LLM_GEMINI


def get_openai_chat_model() -> str:
    value = get_setting("openai_chat_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_OPENAI_CHAT_MODEL


def get_openai_premium_model() -> str:
    value = get_setting("openai_premium_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_OPENAI_PREMIUM_MODEL


def get_deepseek_chat_model() -> str:
    value = get_setting("deepseek_chat_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_DEEPSEEK_CHAT_MODEL


def get_deepseek_premium_model() -> str:
    value = get_setting("deepseek_premium_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_DEEPSEEK_PREMIUM_MODEL


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
