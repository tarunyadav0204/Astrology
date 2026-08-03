"""Build compact locational recommendation pack for chat context."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _resolve_location_scope(intent: Dict[str, Any]) -> Optional[str]:
    from calculators.locational_calculator import normalize_location_scope

    extracted = intent.get("extracted_context") if isinstance(intent.get("extracted_context"), dict) else {}
    for key in ("location_scope", "locationScope", "place_scope"):
        scope = normalize_location_scope(extracted.get(key) if extracted else None)
        if scope:
            return scope
    return normalize_location_scope(intent.get("location_scope"))


def build_locational_recommendation_pack(
    birth_data: Dict[str, Any],
    *,
    intent_result: Optional[Dict[str, Any]] = None,
    natal_chart: Optional[Dict[str, Any]] = None,
    current_dashas: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return a cite-only locational pack when mode is RECOMMEND_LOCATION.

    Safe to call for other modes: returns None unless mode matches.
    Requires location_scope (india | abroad | both) from intent.
    """
    intent = intent_result if isinstance(intent_result, dict) else {}
    mode = str(intent.get("mode") or "").strip().upper()
    if mode != "RECOMMEND_LOCATION":
        return None

    if not isinstance(birth_data, dict):
        return None
    if birth_data.get("latitude") is None or birth_data.get("longitude") is None:
        logger.warning("locational_pack_skipped missing_coordinates")
        return None

    location_scope = _resolve_location_scope(intent)
    if not location_scope:
        logger.info("locational_pack_skipped missing_location_scope")
        return None

    category = str(intent.get("category") or "general")
    try:
        from calculators.locational_calculator import LocationalCalculator

        calc = LocationalCalculator()
        pack = calc.analyze(
            birth_data,
            category=category,
            location_scope=location_scope,
            natal_chart=natal_chart,
            current_dashas=current_dashas,
            top_n=5 if location_scope != "both" else 6,
        )
        pack["intent_category"] = category
        return pack
    except Exception:
        logger.exception("locational_recommendation_pack_failed")
        return None
