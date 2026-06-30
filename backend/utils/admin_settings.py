from typing import Optional, Any, Set, Dict
from threading import Lock
import os
import time
import asyncio

ADMIN_SETTINGS_CACHE_TTL_SECONDS = int(os.getenv("ADMIN_SETTINGS_CACHE_TTL_SECONDS", "60"))
_ADMIN_SETTINGS_CACHE: Dict[str, tuple[float, Optional[str]]] = {}
_ADMIN_SETTINGS_CACHE_LOCK = Lock()
ADMIN_SETTINGS_VERSION_POLL_SECONDS = int(os.getenv("ADMIN_SETTINGS_VERSION_POLL_SECONDS", "10"))
CREDITS_SETTINGS_VERSION_KEY = "credits_settings_version"
_LAST_CREDITS_SETTINGS_VERSION: Optional[str] = None


def is_credits_setting_key(key: str) -> bool:
    normalized = str(key or "").strip()
    return normalized.startswith("first_purchase_bonus_") or normalized.startswith("purchase_discount_")


def invalidate_setting_cache(key: Optional[str] = None) -> None:
    """Clear one cached admin setting or the entire cache."""
    with _ADMIN_SETTINGS_CACHE_LOCK:
        if key is None:
            _ADMIN_SETTINGS_CACHE.clear()
        else:
            _ADMIN_SETTINGS_CACHE.pop(str(key), None)


def invalidate_credits_settings_cache() -> None:
    with _ADMIN_SETTINGS_CACHE_LOCK:
        for key in list(_ADMIN_SETTINGS_CACHE.keys()):
            if is_credits_setting_key(key):
                _ADMIN_SETTINGS_CACHE.pop(key, None)

# Allowed Gemini model IDs (with models/ prefix for API). Used by admin UI and as fallbacks.
GEMINI_MODEL_OPTIONS = [
    ("models/gemini-3.1-pro-preview", "Gemini 3.1 Pro (New – complex reasoning)"),
    ("models/gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite (GA – high-volume, low-cost)"),
    ("models/gemini-3.5-flash", "Gemini 3.5 Flash (GA – agents & coding)"),
    ("models/gemini-3-flash-preview", "Gemini 3 Flash (Preview)"),
    ("models/gemini-3-pro-preview", "Gemini 3 Pro (Retiring Mar 2026)"),
    ("models/gemini-2.5-pro", "Gemini 2.5 Pro (Stable)"),
    ("models/gemini-2.5-flash", "Gemini 2.5 Flash (Stable)"),
    ("models/gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite (Stable)"),
    ("models/gemini-2.0-flash-001", "Gemini 2.0 Flash (Stable)"),
    ("models/gemini-2.0-flash-lite-001", "Gemini 2.0 Flash Lite (Stable)"),
]

DEFAULT_GEMINI_CHAT_MODEL = "models/gemini-3.1-flash-lite"
DEFAULT_GEMINI_PREMIUM_MODEL = "models/gemini-3.1-pro-preview"
DEFAULT_GEMINI_ANALYSIS_MODEL = "models/gemini-3.1-flash-lite"
DEFAULT_GEMINI_INSTANT_MODEL = "models/gemini-2.5-flash-lite"
DEFAULT_PARALLEL_BRANCH_PLANNER_MODEL = DEFAULT_GEMINI_INSTANT_MODEL
PARALLEL_BRANCH_GEMINI_MODEL_KEYS = {
    "parashari": "parallel_branch_gemini_model_parashari",
    "jaimini": "parallel_branch_gemini_model_jaimini",
    "nadi": "parallel_branch_gemini_model_nadi",
    "nakshatra": "parallel_branch_gemini_model_nakshatra",
    "kp": "parallel_branch_gemini_model_kp",
    "ashtakavarga": "parallel_branch_gemini_model_ashtakavarga",
    "sudarshan": "parallel_branch_gemini_model_sudarshan",
    "merge": "parallel_branch_gemini_model_merge",
}
PARALLEL_BRANCH_WORD_LIMIT_KEYS = {
    "parashari": "parallel_branch_word_limit_parashari",
    "jaimini": "parallel_branch_word_limit_jaimini",
    "nadi": "parallel_branch_word_limit_nadi",
    "nakshatra": "parallel_branch_word_limit_nakshatra",
    "kp": "parallel_branch_word_limit_kp",
    "ashtakavarga": "parallel_branch_word_limit_ashtakavarga",
    "sudarshan": "parallel_branch_word_limit_sudarshan",
    "merge": "parallel_branch_word_limit_merge",
}
DEFAULT_PARALLEL_BRANCH_WORD_LIMITS = {
    "parashari": 650,
    "jaimini": 250,
    "nadi": 220,
    "nakshatra": 220,
    "kp": 220,
    "ashtakavarga": 220,
    "sudarshan": 220,
    "merge": 1200,
}

# Deprecated May 2026 — replaced by GA id in DB + code.
_DEPRECATED_GEMINI_31_FLASH_LITE_PREVIEW = "models/gemini-3.1-flash-lite-preview"
_GEMINI_31_FLASH_LITE_GA = "models/gemini-3.1-flash-lite"

# Chat: which vendor handles `GeminiChatAnalyzer.generate_chat_response`.
# Non-chat analysis & event timelines use `analysis_llm_vendor` / `timeline_llm_vendor` (Gemini or DeepSeek).
CHAT_LLM_GEMINI = "gemini"
CHAT_LLM_OPENAI = "openai"
CHAT_LLM_DEEPSEEK = "deepseek"
CHAT_LLM_GEMMA = "gemma"

# Self-hosted Gemma (or compatible) HTTP POST /generate-analysis — override via admin or GEMMA_CHAT_GENERATE_URL.
DEFAULT_GEMMA_CHAT_GENERATE_URL = "http://8.231.104.209:8000/generate-analysis"

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
DEFAULT_DEEPSEEK_ANALYSIS_MODEL = "deepseek-chat"
DEFAULT_DEEPSEEK_TIMELINE_MODEL = "deepseek-reasoner"


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


def migrate_deprecated_gemini_model_ids_on_startup() -> None:
    """
    Rewrite admin_settings values that still use the retired preview id
    `models/gemini-3.1-flash-lite-preview` to the GA id `models/gemini-3.1-flash-lite`.
    Idempotent; safe to run every process start.
    """
    import logging

    logger = logging.getLogger(__name__)
    try:
        from db import get_conn, execute

        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            cur = execute(
                conn,
                """
                UPDATE admin_settings
                SET value = REPLACE(value, ?, ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE value LIKE ?
                """,
                (
                    _DEPRECATED_GEMINI_31_FLASH_LITE_PREVIEW,
                    _GEMINI_31_FLASH_LITE_GA,
                    f"%{_DEPRECATED_GEMINI_31_FLASH_LITE_PREVIEW}%",
                ),
            )
            n = cur.rowcount if cur is not None else 0
            conn.commit()
            if n and n > 0:
                logger.warning(
                    "admin_settings: migrated %s row(s) from %s to %s",
                    n,
                    _DEPRECATED_GEMINI_31_FLASH_LITE_PREVIEW,
                    _GEMINI_31_FLASH_LITE_GA,
                )
    except Exception as e:
        logger.warning("admin_settings Gemini preview→GA migration skipped: %s", e, exc_info=True)


def get_setting(key: str) -> Optional[str]:
    """Get admin setting value"""
    normalized_key = str(key)
    now = time.monotonic()
    with _ADMIN_SETTINGS_CACHE_LOCK:
        if normalized_key in _ADMIN_SETTINGS_CACHE:
            expires_at, cached_value = _ADMIN_SETTINGS_CACHE[normalized_key]
            if expires_at > now:
                return cached_value
            _ADMIN_SETTINGS_CACHE.pop(normalized_key, None)
    try:
        from db import get_conn, execute

        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            cursor = execute(conn, 'SELECT value FROM admin_settings WHERE "key" = ?', (key,))
            result = cursor.fetchone()
            value = result[0] if result else None
            with _ADMIN_SETTINGS_CACHE_LOCK:
                _ADMIN_SETTINGS_CACHE[normalized_key] = (
                    now + max(1, ADMIN_SETTINGS_CACHE_TTL_SECONDS),
                    value,
                )
            return value
    except Exception:
        return None


def get_raw_setting_no_cache(key: str) -> Optional[str]:
    try:
        from db import get_conn, execute

        with get_conn() as conn:
            _ensure_admin_settings_table(conn)
            cursor = execute(conn, 'SELECT value FROM admin_settings WHERE "key" = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception:
        return None


def bump_credits_settings_version() -> None:
    from db import get_conn, execute

    with get_conn() as conn:
        _ensure_admin_settings_table(conn)
        execute(
            conn,
            """
            INSERT INTO admin_settings (key, value, description, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT ("key") DO UPDATE SET
                value = CAST(COALESCE(NULLIF(admin_settings.value, ''), '0') AS BIGINT)::text,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                CREDITS_SETTINGS_VERSION_KEY,
                "0",
                "Monotonic version for cross-worker invalidation of cached credit bonus settings",
            ),
        )
        execute(
            conn,
            """
            UPDATE admin_settings
            SET value = (CAST(COALESCE(NULLIF(value, ''), '0') AS BIGINT) + 1)::text,
                updated_at = CURRENT_TIMESTAMP
            WHERE key = %s
            """,
            (CREDITS_SETTINGS_VERSION_KEY,),
        )
        conn.commit()


async def poll_credits_settings_version_forever() -> None:
    global _LAST_CREDITS_SETTINGS_VERSION
    while True:
        try:
            current = get_raw_setting_no_cache(CREDITS_SETTINGS_VERSION_KEY) or "0"
            if _LAST_CREDITS_SETTINGS_VERSION is None:
                _LAST_CREDITS_SETTINGS_VERSION = current
            elif current != _LAST_CREDITS_SETTINGS_VERSION:
                invalidate_credits_settings_cache()
                _LAST_CREDITS_SETTINGS_VERSION = current
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        await asyncio.sleep(max(1, ADMIN_SETTINGS_VERSION_POLL_SECONDS))


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


def get_parallel_branch_gemini_model(branch_label: str, fallback_model: Optional[str] = None) -> str:
    """Gemini model override for a parallel chat branch.

    When no explicit admin override is present, fall back to the caller-provided lane
    model so standard chats stay on the standard lane and premium chats can opt into
    the premium lane deliberately.
    """
    normalized = str(branch_label or "").strip().lower()
    key = PARALLEL_BRANCH_GEMINI_MODEL_KEYS.get(normalized)
    if key:
        value = get_setting(key)
        if value and value.strip():
            return value.strip()
    if fallback_model and str(fallback_model).strip():
        return str(fallback_model).strip()
    return get_gemini_chat_model()


def get_parallel_branch_word_limit(branch_label: str) -> int:
    """Word-budget hint for a parallel branch or merge lane, with safe defaults."""
    normalized = str(branch_label or "").strip().lower()
    default = int(DEFAULT_PARALLEL_BRANCH_WORD_LIMITS.get(normalized, 250))
    key = PARALLEL_BRANCH_WORD_LIMIT_KEYS.get(normalized)
    if not key:
        return default
    value = get_setting(key)
    if value is None:
        return default
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return max(80, min(4000, parsed))


def is_parallel_branch_planner_enabled() -> bool:
    return _parse_bool_setting(get_setting("parallel_branch_planner_enabled"), False)


def get_parallel_branch_planner_model() -> str:
    value = get_setting("parallel_branch_planner_model")
    if value and value.strip():
        return value.strip()
    return DEFAULT_PARALLEL_BRANCH_PLANNER_MODEL


def get_analysis_llm_vendor() -> str:
    """Vendor for non-chat analysis (health, wealth, karma, structured reports, etc.): gemini or deepseek."""
    value = (get_setting("analysis_llm_vendor") or "").strip().lower()
    if value == CHAT_LLM_DEEPSEEK:
        return CHAT_LLM_DEEPSEEK
    return CHAT_LLM_GEMINI


def get_timeline_llm_vendor() -> str:
    """Vendor for yearly/monthly event timeline generation: gemini or deepseek."""
    value = (get_setting("timeline_llm_vendor") or "").strip().lower()
    if value == CHAT_LLM_DEEPSEEK:
        return CHAT_LLM_DEEPSEEK
    return CHAT_LLM_GEMINI


def get_deepseek_analysis_model() -> str:
    value = get_setting("deepseek_analysis_model")
    if value and value.strip():
        return _normalize_deepseek_model_id(value.strip())
    return DEFAULT_DEEPSEEK_ANALYSIS_MODEL


def get_deepseek_timeline_model() -> str:
    value = get_setting("deepseek_timeline_model")
    if value and value.strip():
        return _normalize_deepseek_model_id(value.strip())
    return DEFAULT_DEEPSEEK_TIMELINE_MODEL


def get_chat_llm_provider() -> str:
    """Which LLM vendor runs standard (non-premium) astrological chat: 'gemini', 'openai', 'deepseek', or 'gemma'."""
    value = (get_setting("chat_llm_provider") or "").strip().lower()
    if value == CHAT_LLM_DEEPSEEK:
        return CHAT_LLM_DEEPSEEK
    if value == CHAT_LLM_OPENAI:
        return CHAT_LLM_OPENAI
    if value == CHAT_LLM_GEMMA:
        return CHAT_LLM_GEMMA
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
    if value == CHAT_LLM_GEMMA:
        return CHAT_LLM_GEMMA
    return get_chat_llm_provider()


def get_gemma_chat_generate_url() -> str:
    """Full URL for POST /generate-analysis (Gemma GPU service). Env wins for quick ops tests."""
    import os

    env_url = (os.getenv("GEMMA_CHAT_GENERATE_URL") or "").strip()
    if env_url:
        return env_url
    db_url = (get_setting("gemma_chat_generate_url") or "").strip()
    if db_url:
        return db_url
    return DEFAULT_GEMMA_CHAT_GENERATE_URL


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


def is_chat_subject_gate_enabled() -> bool:
    """Global feature flag for the pre-question subject/profile gate."""
    return _parse_bool_setting(get_setting("chat_subject_gate_enabled"), default=False)


def get_chat_subject_gate_user_allowlist() -> Set[int]:
    """Optional CSV/whitespace-separated user id allowlist. Empty set means all users."""
    raw = (get_setting("chat_subject_gate_user_allowlist") or "").strip()
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


def chat_subject_gate_enabled_for_user(user_id: Optional[int]) -> bool:
    """Global ON + empty allowlist enables for all users; otherwise only listed users."""
    if not is_chat_subject_gate_enabled():
        return False
    allowlist = get_chat_subject_gate_user_allowlist()
    if not allowlist:
        return True
    try:
        return int(user_id) in allowlist
    except (TypeError, ValueError):
        return False


def _parse_int_setting(value: Optional[str], default: int, minimum: Optional[int] = None, maximum: Optional[int] = None) -> int:
    try:
        parsed = int(float(str(value).strip()))
    except (TypeError, ValueError):
        parsed = int(default)
    if minimum is not None:
        parsed = max(int(minimum), parsed)
    if maximum is not None:
        parsed = min(int(maximum), parsed)
    return parsed


def is_first_purchase_bonus_enabled() -> bool:
    """Global feature flag for the post-free-question first credit purchase bonus."""
    return _parse_bool_setting(get_setting("first_purchase_bonus_enabled"), default=False)


def get_first_purchase_bonus_user_allowlist() -> Set[int]:
    """Optional CSV/whitespace-separated user id allowlist. Empty set means all users."""
    raw = (get_setting("first_purchase_bonus_user_allowlist") or "").strip()
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


def first_purchase_bonus_enabled_for_user(user_id: Optional[int]) -> bool:
    """Global ON + empty allowlist enables for all users; otherwise only listed users."""
    if not is_first_purchase_bonus_enabled():
        return False
    allowlist = get_first_purchase_bonus_user_allowlist()
    if not allowlist:
        return True
    try:
        return int(user_id) in allowlist
    except (TypeError, ValueError):
        return False


def get_first_purchase_bonus_config() -> Dict[str, Any]:
    """Admin-controlled values for the post-free-question first credit purchase bonus."""
    import json

    percent = _parse_int_setting(get_setting("first_purchase_bonus_percent"), default=20, minimum=0, maximum=500)
    fixed = _parse_int_setting(get_setting("first_purchase_bonus_fixed_credits"), default=0, minimum=0, maximum=100000)
    max_bonus = _parse_int_setting(get_setting("first_purchase_bonus_max_bonus_credits"), default=1000, minimum=0, maximum=100000)
    window_minutes = _parse_int_setting(get_setting("first_purchase_bonus_window_minutes"), default=30, minimum=1, maximum=10080)
    raw_pack_overrides = (get_setting("first_purchase_bonus_pack_overrides") or "").strip()
    # The first-purchase offer is intentionally one mode at a time.
    # If legacy/admin data has both set, fixed credits wins because it is the explicit amount.
    bonus_type = "fixed" if fixed > 0 else ("percent" if percent > 0 else "none")
    pack_overrides: Dict[str, Dict[str, Any]] = {}
    if raw_pack_overrides:
        try:
            decoded = json.loads(raw_pack_overrides)
            if isinstance(decoded, dict):
                for key, value in decoded.items():
                    product_id = str(key or "").strip()
                    if not product_id or not isinstance(value, dict):
                        continue
                    override_percent = max(0, min(500, int(value.get("percent") or 0)))
                    override_fixed = max(0, min(100000, int(value.get("fixed_credits") or 0)))
                    override_cap = max(0, min(100000, int(value.get("max_bonus_credits") or 0)))
                    override_type = str(value.get("bonus_type") or "").strip().lower()
                    if override_type not in {"percent", "fixed", "none"}:
                        override_type = "fixed" if override_fixed > 0 else ("percent" if override_percent > 0 else "none")
                    pack_overrides[product_id] = {
                        "percent": override_percent,
                        "fixed_credits": override_fixed,
                        "max_bonus_credits": override_cap,
                        "bonus_type": override_type,
                    }
        except Exception:
            pack_overrides = {}
    return {
        "percent": percent,
        "fixed_credits": fixed,
        "max_bonus_credits": max_bonus,
        "window_minutes": window_minutes,
        "bonus_type": bonus_type,
        "pack_overrides": pack_overrides,
    }


def is_purchase_discount_enabled() -> bool:
    """Global feature flag for extra credits on any eligible credit purchase."""
    return _parse_bool_setting(get_setting("purchase_discount_enabled"), default=False)


def get_purchase_discount_user_allowlist() -> Set[int]:
    """Optional CSV/whitespace-separated user id allowlist. Empty set means all users."""
    raw = (get_setting("purchase_discount_user_allowlist") or "").strip()
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


def purchase_discount_enabled_for_user(user_id: Optional[int]) -> bool:
    """Global ON + empty allowlist enables for all users; otherwise only listed users."""
    if not is_purchase_discount_enabled():
        return False
    allowlist = get_purchase_discount_user_allowlist()
    if not allowlist:
        return True
    try:
        return int(user_id) in allowlist
    except (TypeError, ValueError):
        return False


def get_purchase_discount_window_started_at():
    """Campaign start timestamp for the purchase discount window."""
    from datetime import datetime, timezone

    raw = (get_setting("purchase_discount_window_started_at") or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def get_purchase_discount_config() -> Dict[str, Any]:
    """Admin-controlled values for the open purchase discount campaign."""
    import json

    percent = _parse_int_setting(get_setting("purchase_discount_percent"), default=0, minimum=0, maximum=500)
    fixed = _parse_int_setting(get_setting("purchase_discount_fixed_credits"), default=0, minimum=0, maximum=100000)
    max_bonus = _parse_int_setting(get_setting("purchase_discount_max_bonus_credits"), default=0, minimum=0, maximum=100000)
    window_minutes = _parse_int_setting(get_setting("purchase_discount_window_minutes"), default=0, minimum=0, maximum=10080)
    raw_pack_overrides = (get_setting("purchase_discount_pack_overrides") or "").strip()
    bonus_type = "fixed" if fixed > 0 else ("percent" if percent > 0 else "none")
    pack_overrides: Dict[str, Dict[str, Any]] = {}
    if raw_pack_overrides:
        try:
            decoded = json.loads(raw_pack_overrides)
            if isinstance(decoded, dict):
                for key, value in decoded.items():
                    product_id = str(key or "").strip()
                    if not product_id or not isinstance(value, dict):
                        continue
                    override_percent = max(0, min(500, int(value.get("percent") or 0)))
                    override_fixed = max(0, min(100000, int(value.get("fixed_credits") or 0)))
                    override_cap = max(0, min(100000, int(value.get("max_bonus_credits") or 0)))
                    override_type = str(value.get("bonus_type") or "").strip().lower()
                    if override_type not in {"percent", "fixed", "none"}:
                        override_type = "fixed" if override_fixed > 0 else ("percent" if override_percent > 0 else "none")
                    pack_overrides[product_id] = {
                        "percent": override_percent,
                        "fixed_credits": override_fixed,
                        "max_bonus_credits": override_cap,
                        "bonus_type": override_type,
                    }
        except Exception:
            pack_overrides = {}
    return {
        "percent": percent,
        "fixed_credits": fixed,
        "max_bonus_credits": max_bonus,
        "window_minutes": window_minutes,
        "bonus_type": bonus_type,
        "pack_overrides": pack_overrides,
        "window_started_at": (
            get_purchase_discount_window_started_at().isoformat()
            if get_purchase_discount_window_started_at()
            else None
        ),
    }


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


def is_play_payment_service_enabled() -> bool:
    """Global feature flag for routing Play purchase verification through the payment service."""
    return _parse_bool_setting(get_setting("play_payment_service_enabled"), default=False)


def get_play_payment_service_user_allowlist() -> Set[int]:
    """Optional CSV user id allowlist for the Play payment service. Empty set means all users when enabled."""
    raw = (get_setting("play_payment_service_user_allowlist") or "").strip()
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


def play_payment_service_enabled_for_user(user_id: Optional[int]) -> bool:
    """
    Global OFF disables the payment service for everyone.
    Global ON + empty allowlist enables for all users.
    Global ON + allowlist enables only listed users.
    """
    if not is_play_payment_service_enabled():
        return False
    allowlist = get_play_payment_service_user_allowlist()
    if not allowlist:
        return True
    try:
        return int(user_id) in allowlist
    except (TypeError, ValueError):
        return False


def is_chat_worker_mode_enabled() -> bool:
    """Global feature flag for routing chat-v2 processing through the dedicated worker path."""
    return _parse_bool_setting(get_setting("chat_worker_mode_enabled"), default=False)


def get_chat_worker_user_allowlist() -> Set[int]:
    """Optional CSV user id allowlist for chat worker mode. Empty set means all users when enabled."""
    raw = (get_setting("chat_worker_user_allowlist") or "").strip()
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


def chat_worker_mode_enabled_for_user(user_id: Optional[int]) -> bool:
    """
    Global OFF disables worker mode for everyone.
    Global ON + empty allowlist enables for all users.
    Global ON + allowlist enables only listed users.
    """
    if not is_chat_worker_mode_enabled():
        return False
    allowlist = get_chat_worker_user_allowlist()
    if not allowlist:
        return True
    try:
        return int(user_id) in allowlist
    except (TypeError, ValueError):
        return False


def is_free_question_parashari_only_enabled() -> bool:
    """Global feature flag for answering free chat questions through a Parashari-only final lane."""
    return _parse_bool_setting(get_setting("free_question_parashari_only_enabled"), default=False)


def get_play_payment_service_base_url() -> Optional[str]:
    """Base URL for the Play payment service Cloud Run app."""
    value = (get_setting("play_payment_service_base_url") or os.getenv("PLAY_PAYMENT_SERVICE_BASE_URL") or "").strip()
    return value.rstrip("/") if value else None


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


def get_chart_guide_video_url() -> str:
    """Public guide video URL shown on the chart screen."""
    return (get_setting("chart_guide_video_url") or "").strip()


PODCAST_PROVIDER_TTS = "tts"
PODCAST_PROVIDER_NOTEBOOK_LM = "notebook_lm"

SPEECH_TTS_PROVIDER_LOCAL = "local"
SPEECH_TTS_PROVIDER_GOOGLE = "google"
DEFAULT_SPEECH_TTS_VOICE_EN = "en-IN-Neural2-A"
DEFAULT_SPEECH_TTS_VOICE_HI = "hi-IN-Neural2-A"


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


def get_speech_tts_voice(lang: str = "en") -> str:
    """
    Default Google TTS voice for speech chat by language.
    English uses `speech_tts_voice_en`, Hindi uses `speech_tts_voice_hi`.
    """
    normalized_lang = (lang or "en").strip().lower()
    if normalized_lang.startswith("hi"):
        value = (get_setting("speech_tts_voice_hi") or "").strip()
        return value or DEFAULT_SPEECH_TTS_VOICE_HI
    value = (get_setting("speech_tts_voice_en") or "").strip()
    return value or DEFAULT_SPEECH_TTS_VOICE_EN
