from __future__ import annotations

from typing import Any, Dict


def build_timing_context(engine_result: Dict[str, Any]) -> Dict[str, Any]:
    timing = engine_result.get("timing_overlay", {}) or {}
    shared = timing.get("shared", {}) or {}
    return {
        "joint_readiness_score": shared.get("joint_readiness_score"),
        "current_window": shared.get("current_window", {}),
        "next_favorable_windows": shared.get("next_favorable_windows", []),
        "next_challenging_windows": shared.get("next_challenging_windows", []),
    }

