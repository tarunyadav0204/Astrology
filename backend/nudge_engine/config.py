"""Configuration for the nudge engine."""
import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BACKEND_DIR, "astrology.db")
_env_path = os.environ.get("NUDGE_DB_PATH")
if _env_path:
    DB_PATH = _env_path

MAX_NUDGES_PER_USER_PER_DAY = 1
DEFAULT_CTA_DEEP_LINK = "astroroshni://chat"
