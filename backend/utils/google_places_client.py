"""
Server-side Google Places (New) — autocomplete + place details.
Used by /api/places/* and WhatsApp Flow data endpoint.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import requests

AUTOCOMPLETE_URL = "https://places.googleapis.com/v1/places:autocomplete"
PLACE_DETAILS_URL_TEMPLATE = "https://places.googleapis.com/v1/places/{}"


def _api_key() -> Optional[str]:
    k = (os.environ.get("GOOGLE_PLACES_API_KEY") or "").strip()
    return k or None


def _place_id_from_resource(name: str) -> str:
    if not name:
        return ""
    return name.replace("places/", "", 1) if name.startswith("places/") else name


def places_autocomplete_suggestions(
    q: str,
    *,
    language: str = "en",
    limit: int = 8,
) -> List[Dict[str, str]]:
    """
    Returns [{"place_id": "...", "description": "..."}, ...] for non-empty query.
    Raises RuntimeError if API is not configured or request fails.
    """
    api_key = _api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is not set")
    q = (q or "").strip()
    if not q:
        return []

    payload = {"input": q, "languageCode": language or "en"}
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
    }
    r = requests.post(AUTOCOMPLETE_URL, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    suggestions = data.get("suggestions") or []
    results: List[Dict[str, str]] = []
    for s in suggestions:
        pp = s.get("placePrediction")
        if not pp:
            continue
        place_id = pp.get("placeId") or _place_id_from_resource(pp.get("place") or "")
        text_obj = pp.get("text") or {}
        description = (text_obj.get("text") or "").strip()
        if place_id and description:
            results.append({"place_id": place_id, "description": description})
        if len(results) >= limit:
            break
    return results


def place_details(place_id: str, *, language: str = "en") -> Dict[str, Any]:
    """
    Returns place_id, name, formattedAddress, latitude, longitude.
    Raises RuntimeError / ValueError on failure.
    """
    api_key = _api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is not set")
    raw_id = _place_id_from_resource(place_id)
    if not re.match(r"^[A-Za-z0-9_-]+$", raw_id):
        raise ValueError("Invalid place_id")
    url = PLACE_DETAILS_URL_TEMPLATE.format(raw_id)
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,displayName,formattedAddress,location",
    }
    params = {"languageCode": language} if language else None
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    display_name = ""
    dn = data.get("displayName")
    if isinstance(dn, dict) and dn.get("text"):
        display_name = dn["text"]
    formatted_address = data.get("formattedAddress") or display_name
    name = display_name or formatted_address
    location = data.get("location") or {}
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude is None or longitude is None:
        raise RuntimeError("Place details did not return coordinates")
    return {
        "place_id": data.get("id") or raw_id,
        "name": name,
        "formattedAddress": formatted_address,
        "latitude": float(latitude),
        "longitude": float(longitude),
    }
