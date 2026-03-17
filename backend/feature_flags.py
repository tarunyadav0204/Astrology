"""
A/B testing and feature flags: control which users see new backend features.

Configuration is stored in admin_settings (key = "feature_<name>") or in env
(FEATURE_<NAME>, e.g. FEATURE_GROK_4_1=rollout:10).

Value format:
  - "on" / "true" / "1"     → enabled for everyone
  - "off" / "false" / "0"  → disabled for everyone
  - "rollout:25"           → 25% of users (deterministic by userid % 100)
  - "users:1,2,3"          → only these userids (comma-separated)
  - "rollout:25;users:1,2" → enabled if in rollout bucket OR in allow-list

Usage in a route:

  from auth import get_current_user, User
  from feature_flags import is_feature_enabled

  @router.post("/ask")
  async def ask(request: ChatRequest, current_user: User = Depends(get_current_user)):
      if is_feature_enabled(current_user, "grok_4_1"):
          response = await grok_analyzer.generate(...)
      else:
          response = await gemini_analyzer.generate_chat_response(...)
      return response

To set flags: insert into admin_settings (key, value), e.g.:
  ("feature_grok_4_1", "rollout:10")   -- 10% of users
  ("feature_grok_4_1", "users:101,202") -- only userids 101 and 202
  ("feature_grok_4_1", "on")            -- everyone
"""

import os
import re
from typing import Optional

from utils.admin_settings import get_setting


def _get_feature_value(feature_name: str) -> Optional[str]:
    """Feature config from admin_settings or env. Normalized key: feature_<name> / FEATURE_<NAME>."""
    key = f"feature_{feature_name}".lower().replace("-", "_")
    value = get_setting(key)
    if value is not None and value.strip():
        return value.strip()
    env_key = "FEATURE_" + feature_name.upper().replace("-", "_")
    return os.environ.get(env_key, "").strip() or None


def is_feature_enabled(user, feature_name: str) -> bool:
    """
    Return True if the feature is enabled for this user (for A/B testing).

    :param user: Object with .userid (int), e.g. from get_current_user()
    :param feature_name: e.g. "grok_4_1", "new_chat_ui"
    """
    if user is None:
        return False
    userid = getattr(user, "userid", None)
    if userid is None:
        return False

    raw = _get_feature_value(feature_name)
    if not raw:
        return False

    raw_lower = raw.lower()
    if raw_lower in ("on", "true", "1"):
        return True
    if raw_lower in ("off", "false", "0"):
        return False

    # rollout:25  →  userid % 100 < 25  (deterministic per user)
    rollout_match = re.match(r"rollout\s*:\s*(\d+)", raw_lower)
    if rollout_match:
        pct = min(100, int(rollout_match.group(1)))
        if pct <= 0:
            return False
        if pct >= 100:
            return True
        if (userid % 100) < pct:
            return True
        # Only rollout, no "users:" part
        if ";" not in raw_lower:
            return False

    # users:1,2,3  (allow-list)
    users_match = re.search(r"users\s*:\s*([\d,\s]+)", raw_lower)
    if users_match:
        allowed = [int(x.strip()) for x in users_match.group(1).split(",") if x.strip().isdigit()]
        if userid in allowed:
            return True

    # "rollout:25;users:1,2"  (rollout OR allow-list)
    if ";" in raw:
        parts = [p.strip() for p in raw.split(";")]
        for part in parts:
            if not part:
                continue
            part_lower = part.lower()
            if part_lower in ("on", "true", "1"):
                return True
            if part_lower in ("off", "false", "0"):
                return False
            if re.match(r"rollout\s*:\s*\d+", part_lower):
                m = re.match(r"rollout\s*:\s*(\d+)", part_lower)
                if m:
                    pct = int(m.group(1))
                    if pct >= 100:
                        return True
                    if pct > 0 and (userid % 100) < pct:
                        return True
            if part_lower.startswith("users:"):
                rest = part_lower[6:].strip()
                allowed = [int(x.strip()) for x in rest.split(",") if x.strip().isdigit()]
                if userid in allowed:
                    return True

    return False
