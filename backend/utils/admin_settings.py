from typing import Optional, Any, Set

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
DEFAULT_GEMINI_INSTANT_MODEL = "models/gemini-2.5-flash-lite"

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

# DeepSeek API model IDs (OpenAI-compatible). Confirm current ids with GET https://api.deepseek.com/v1/models when upgrading.
# V3.2 is the version named on DeepSeek pricing docs for deepseek-chat / deepseek-reasoner; V4 ids appear when the platform exposes them.
DEEPSEEK_CHAT_MODEL_OPTIONS = [
    ("deepseek-chat", "DeepSeek Chat (V3.2)"),
    ("deepseek-reasoner", "DeepSeek Reasoner (V3.2 thinking)"),
    ("deepseek-v4", "DeepSeek V4 (chat)"),
    ("deepseek-v4-reasoner", "DeepSeek V4 (thinking)"),
]
DEFAULT_DEEPSEEK_CHAT_MODEL = "deepseek-chat"
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


def _parse_bool_setting(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


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


def get_gemini_instant_model() -> str:
    """Model ID for instant chat. From admin_settings or default."""
    value = get_setting("gemini_instant_chat_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_GEMINI_INSTANT_MODEL


def get_event_timeline_model() -> str:
    """Model ID for event timeline generation. Falls back to premium Gemini model when unset."""
    value = get_setting("event_timeline_model")
    if value and value.strip():
        return value.strip()
    return get_gemini_premium_model()


def get_chat_llm_provider() -> str:
    """Which LLM vendor runs standard (non-premium) astrological chat: 'gemini', 'openai', or 'deepseek'."""
    value = (get_setting("chat_llm_provider") or "").strip().lower()
    if value == CHAT_LLM_DEEPSEEK:
        return CHAT_LLM_DEEPSEEK
    if value == CHAT_LLM_OPENAI:
        return CHAT_LLM_OPENAI
    return CHAT_LLM_GEMINI


def get_chat_llm_provider_premium() -> str:
    """Vendor for premium chat. When unset or invalid, matches standard chat vendor."""
    value = (get_setting("chat_llm_provider_premium") or "").strip().lower()
    if value == CHAT_LLM_DEEPSEEK:
        return CHAT_LLM_DEEPSEEK
    if value == CHAT_LLM_OPENAI:
        return CHAT_LLM_OPENAI
    if value == CHAT_LLM_GEMINI:
        return CHAT_LLM_GEMINI
    return get_chat_llm_provider()


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


def _normalize_deepseek_model_id(model_id: str) -> str:
    """Map legacy/wrong ids to DeepSeek API names."""
    m = (model_id or "").strip()
    if m == "deepseek-chat-3.2":
        return "deepseek-chat"
    return m


def get_deepseek_chat_model() -> str:
    value = get_setting("deepseek_chat_model")
    if value and value.strip():
        return _normalize_deepseek_model_id(value.strip())
    return DEFAULT_DEEPSEEK_CHAT_MODEL


def get_deepseek_premium_model() -> str:
    value = get_setting("deepseek_premium_model")
    if value and value.strip():
        return _normalize_deepseek_model_id(value.strip())
    return DEFAULT_DEEPSEEK_PREMIUM_MODEL


def is_debug_logging_enabled() -> bool:
    """Check if debug logging is enabled"""
    value = get_setting('debug_logging_enabled')
    return value == 'true' if value else False


def is_instant_chat_enabled() -> bool:
    """Global feature flag for the instant chat prototype."""
    return _parse_bool_setting(get_setting("instant_chat_enabled"), default=False)


def get_instant_chat_user_allowlist() -> Set[int]:
    """Optional CSV/whitespace-separated user id allowlist. Empty set means all users."""
    raw = (get_setting("instant_chat_user_allowlist") or "").strip()
    if not raw:
        return set()
    user_ids: Set[int] = set()
    for token in raw.replace("\n", ",").replace("\t", ",").replace(" ", ",").split(","):
        cleaned = token.strip()
        if not cleaned:
            continue
        try:
            user_ids.add(int(cleaned))
        except (TypeError, ValueError):
            continue
    return user_ids


def instant_chat_enabled_for_user(user_id: Optional[int]) -> bool:
    """
    Global OFF disables instant chat for everyone.
    Global ON + empty allowlist enables for all users.
    Global ON + allowlist enables only listed users.
    """
    if not is_instant_chat_enabled():
        return False
    allowlist = get_instant_chat_user_allowlist()
    if not allowlist:
        return True
    try:
        return int(user_id) in allowlist
    except (TypeError, ValueError):
        return False


def is_speech_chat_enabled() -> bool:
    """Global feature flag for mobile speech input (mic) + /api/speech/transcribe."""
    return _parse_bool_setting(get_setting("speech_chat_enabled"), default=False)


def get_speech_chat_user_allowlist() -> Set[int]:
    """Optional CSV user id allowlist for speech chat. Empty set means all users when speech is enabled."""
    raw = (get_setting("speech_chat_user_allowlist") or "").strip()
    if not raw:
        return set()
    user_ids: Set[int] = set()
    for token in raw.replace("\n", ",").replace("\t", ",").replace(" ", ",").split(","):
        cleaned = token.strip()
        if not cleaned:
            continue
        try:
            user_ids.add(int(cleaned))
        except (TypeError, ValueError):
            continue
    return user_ids


def speech_chat_enabled_for_user(user_id: Optional[int]) -> bool:
    """
    Global OFF disables speech for everyone.
    Global ON + empty allowlist enables for all users.
    Global ON + allowlist enables only listed users.
    """
    if not is_speech_chat_enabled():
        return False
    allowlist = get_speech_chat_user_allowlist()
    if not allowlist:
        return True
    try:
        return int(user_id) in allowlist
    except (TypeError, ValueError):
        return False


def get_chat_static_suggestions() -> list[str]:
    """Admin-defined static suggestion chips for mobile chat."""
    raw = (get_setting("chat_static_suggestions") or "").strip()
    if not raw:
        return []

    try:
        import json
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [
                str(item).strip()
                for item in parsed
                if str(item or "").strip()
            ][:20]
    except Exception:
        pass

    return [
        line.strip()
        for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if line.strip()
    ][:20]


PODCAST_PROVIDER_TTS = "tts"
PODCAST_PROVIDER_NOTEBOOK_LM = "notebook_lm"

SPEECH_TTS_PROVIDER_LOCAL = "local"
SPEECH_TTS_PROVIDER_GOOGLE = "google"


def get_podcast_provider() -> str:
    """Which podcast pipeline to use: 'tts' (Gemini script + Google TTS) or 'notebook_lm' (Discovery Engine Podcast API)."""
    value = get_setting("podcast_provider")
    if value and value.strip() in (PODCAST_PROVIDER_TTS, PODCAST_PROVIDER_NOTEBOOK_LM):
        return value.strip()
    return PODCAST_PROVIDER_TTS


def get_speech_tts_provider() -> str:
    """
    Which TTS provider should speech chat use:
    - 'local' => device-native TTS
    - 'google' => backend Google Cloud TTS audio
    """
    value = (get_setting("speech_tts_provider") or "").strip().lower()
    if value == SPEECH_TTS_PROVIDER_GOOGLE:
        return SPEECH_TTS_PROVIDER_GOOGLE
    return SPEECH_TTS_PROVIDER_LOCAL
