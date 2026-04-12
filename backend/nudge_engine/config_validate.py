"""Validate merged JSON config for configurable nudge triggers."""
from __future__ import annotations

from typing import Any, Dict, List

from .trigger_defaults import ALLOWED_PLANET_NAMES, get_spec


class ConfigValidationError(ValueError):
    pass


def _as_int(x: Any, key: str, lo: int, hi: int) -> int:
    try:
        v = int(x)
    except (TypeError, ValueError) as e:
        raise ConfigValidationError(f"{key} must be an integer") from e
    if v < lo or v > hi:
        raise ConfigValidationError(f"{key} must be between {lo} and {hi}")
    return v


def _as_float(x: Any, key: str, lo: float, hi: float) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError) as e:
        raise ConfigValidationError(f"{key} must be a number") from e
    if v < lo or v > hi:
        raise ConfigValidationError(f"{key} must be between {lo} and {hi}")
    return v


def _as_planet_list(x: Any, key: str) -> List[str]:
    if x is None:
        raise ConfigValidationError(f"{key} is required")
    if not isinstance(x, list):
        raise ConfigValidationError(f"{key} must be a list of planet names")
    out: List[str] = []
    seen = set()
    for item in x:
        s = str(item).strip()
        if s not in ALLOWED_PLANET_NAMES:
            raise ConfigValidationError(f"Unknown planet in {key}: {s}")
        if s not in seen:
            seen.add(s)
            out.append(s)
    if not out:
        raise ConfigValidationError(f"{key} must not be empty")
    return out


def validate_and_normalize_config(trigger_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a normalized config dict for persistence and runtime.
    Raises ConfigValidationError on invalid input.
    """
    spec = get_spec(trigger_key)
    if not spec:
        raise ConfigValidationError(f"Unknown trigger_key: {trigger_key}")

    merged = dict(spec.default_config)
    merged.update(config or {})
    if "planets" in spec.default_config and merged.get("planets") is None:
        merged["planets"] = list(spec.default_config["planets"])

    if trigger_key == "natal_planet_return":
        merged["orb_deg"] = _as_float(merged.get("orb_deg"), "orb_deg", 0.25, 5.0)
        merged["advance_notice_days"] = _as_int(
            merged.get("advance_notice_days"), "advance_notice_days", 1, 90
        )
        merged["horizon_days"] = _as_int(
            merged.get("horizon_days"), "horizon_days", 30, 2500
        )
        merged["planets"] = _as_planet_list(merged.get("planets"), "planets")
        return merged

    if trigger_key == "natal_whole_sign_return":
        merged["advance_notice_days"] = _as_int(
            merged.get("advance_notice_days"), "advance_notice_days", 1, 90
        )
        merged["horizon_days"] = _as_int(
            merged.get("horizon_days"), "horizon_days", 30, 2500
        )
        merged["planets"] = _as_planet_list(merged.get("planets"), "planets")
        return merged

    if trigger_key == "vimshottari_dasha_change":
        merged["md_lead_days"] = _as_int(
            merged.get("md_lead_days"), "md_lead_days", 1, 120
        )
        merged["ad_lead_days"] = _as_int(
            merged.get("ad_lead_days"), "ad_lead_days", 1, 90
        )
        merged["pd_lead_days"] = _as_int(
            merged.get("pd_lead_days"), "pd_lead_days", 1, 14
        )
        return merged

    raise ConfigValidationError(f"No validator for trigger_key: {trigger_key}")
