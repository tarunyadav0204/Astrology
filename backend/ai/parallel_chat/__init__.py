"""Parallel multi-branch chat pipelines (opt-in via env flags)."""

from ai.parallel_chat.config import (
    parallel_chat_enabled,
    parallel_chat_user_allowlist,
    parallel_relational_chat_enabled,
    should_use_parallel_chat,
    should_use_parallel_relational_chat,
)

__all__ = [
    "parallel_chat_enabled",
    "parallel_chat_user_allowlist",
    "parallel_relational_chat_enabled",
    "should_use_parallel_chat",
    "should_use_parallel_relational_chat",
]
