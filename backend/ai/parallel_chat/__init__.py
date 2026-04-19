"""Parallel multi-branch chat pipeline (opt-in via ASTRO_PARALLEL_CHAT)."""

from ai.parallel_chat.config import (
    parallel_chat_enabled,
    parallel_chat_user_allowlist,
    should_use_parallel_chat,
)

__all__ = [
    "parallel_chat_enabled",
    "parallel_chat_user_allowlist",
    "should_use_parallel_chat",
]
