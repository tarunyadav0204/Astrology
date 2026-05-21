"""
Business logic for WhatsApp Flow data channel (ping, INIT, place search exchange).

Screen ids / field names can be aligned with your Flow JSON via env vars below.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from utils.google_places_client import place_details as gp_place_details
from utils.google_places_client import places_autocomplete_suggestions

logger = logging.getLogger(__name__)


def _env(name: str, default: str) -> str:
    return (os.environ.get(name) or default).strip()


def build_flow_data_response(decrypted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build plaintext JSON object for encrypt_flow_response.
    """
    action = str(decrypted.get("action") or "").strip().lower()
    screen = str(decrypted.get("screen") or "")
    data = decrypted.get("data")
    if not isinstance(data, dict):
        data = {}

    # Health check (no screen required)
    if action == "ping":
        return {"data": {"status": "active"}}

    init_screen = _env("WHATSAPP_FLOW_DATA_INIT_SCREEN", "create_birth_chart")
    search_screen = _env("WHATSAPP_FLOW_DATA_SCREEN_SEARCH", "place_search")
    pick_screen = _env("WHATSAPP_FLOW_DATA_SCREEN_PICK", "place_pick")
    after_place_screen = _env("WHATSAPP_FLOW_DATA_SCREEN_AFTER_PLACE", "birth_place_gender")
    query_field = _env("WHATSAPP_FLOW_DATA_FIELD_PLACE_QUERY", "place_query")
    pick_field = _env("WHATSAPP_FLOW_DATA_FIELD_SELECTED_PLACE", "selected_place")

    if action == "INIT":
        return {"screen": init_screen, "data": {}}

    if action == "BACK":
        # Minimal: echo empty data; override with refresh_on_back logic if needed.
        return {"screen": screen or init_screen, "data": {}}

    if action == "data_exchange" and screen == search_screen:
        q = str(data.get(query_field) or "").strip()
        if len(q) < 2:
            return {
                "screen": search_screen,
                "data": {
                    "error_message": "Type at least 2 characters to search.",
                    "place_options": [],
                },
            }
        try:
            rows = places_autocomplete_suggestions(q, limit=8)
        except Exception as e:
            logger.warning("flow data_exchange autocomplete failed: %s", e)
            return {
                "screen": search_screen,
                "data": {
                    "error_message": "Could not search places. Try again.",
                    "place_options": [],
                },
            }
        place_options = [{"id": r["place_id"], "title": (r["description"] or "")[:80]} for r in rows]
        if not place_options:
            return {
                "screen": search_screen,
                "data": {
                    "error_message": "No matches. Try a different city or add country.",
                    "place_options": [],
                },
            }
        return {"screen": pick_screen, "data": {"place_options": place_options}}

    if action == "data_exchange" and screen == pick_screen:
        pid = str(data.get(pick_field) or data.get("place_id") or "").strip()
        if not pid:
            return {
                "screen": pick_screen,
                "data": {"error_message": "Please choose a place from the list."},
            }
        try:
            details = gp_place_details(pid)
        except Exception as e:
            logger.warning("flow data_exchange place details failed: %s", e)
            return {
                "screen": pick_screen,
                "data": {"error_message": "Could not load that place. Pick another."},
            }
        return {
            "screen": after_place_screen,
            "data": {
                "selected_latitude": details["latitude"],
                "selected_longitude": details["longitude"],
                "selected_formatted_address": details["formattedAddress"],
                "selected_place_id": details["place_id"],
            },
        }

    logger.info(
        "flow data: unhandled action=%r screen=%r keys=%s",
        action,
        screen,
        list(data.keys())[:20],
    )
    if action == "data_exchange" and screen:
        return {
            "screen": screen,
            "data": {"error_message": "This step is not supported on the server yet."},
        }
    return {"screen": init_screen, "data": {}}
