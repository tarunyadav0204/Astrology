"""Evidence-driven orchestration for Instant Chat.

This package deliberately contains no natural-language keyword routing.  The
query plan is derived from the LLM intent router; everything after that point
is typed, deterministic and auditable.
"""

from .orchestrator import build_instant_v2_packet, finalize_instant_v2_packet

__all__ = ["build_instant_v2_packet", "finalize_instant_v2_packet"]
