"""Google Places API proxy. Keeps API key on server; exposes autocomplete and place details."""

import os
import re
from typing import List, Optional

import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/places", tags=["places"])

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
AUTOCOMPLETE_URL = "https://places.googleapis.com/v1/places:autocomplete"
PLACE_DETAILS_URL_TEMPLATE = "https://places.googleapis.com/v1/places/{}"


def _get_api_key() -> str:
    if not GOOGLE_PLACES_API_KEY or not GOOGLE_PLACES_API_KEY.strip():
        raise HTTPException(
            status_code=503,
            detail="Places API is not configured (missing GOOGLE_PLACES_API_KEY)",
        )
    return GOOGLE_PLACES_API_KEY.strip()


def _place_id_from_resource(name: str) -> str:
    """Extract raw place ID from 'places/ChIJ...' format."""
    if not name:
        return ""
    return name.replace("places/", "", 1) if name.startswith("places/") else name


@router.get("/autocomplete")
def places_autocomplete(
    q: str = Query(..., min_length=1, max_length=200),
    language: Optional[str] = Query("en", alias="languageCode"),
) -> dict:
    """
    Proxy to Google Places Autocomplete (New). Returns a list of suggestions with
    place_id and description for use in location search.
    """
    api_key = _get_api_key()
    payload = {
        "input": q.strip(),
        "languageCode": language or "en",
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
    }
    try:
        r = requests.post(
            AUTOCOMPLETE_URL,
            json=payload,
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Places autocomplete request failed: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid response from Places API: {str(e)}",
        )

    suggestions = data.get("suggestions") or []
    results: List[dict] = []
    for s in suggestions:
        pp = s.get("placePrediction")
        if not pp:
            continue
        place_id = pp.get("placeId") or _place_id_from_resource(pp.get("place") or "")
        text_obj = pp.get("text") or {}
        description = (text_obj.get("text") or "").strip()
        if place_id and description:
            results.append({"place_id": place_id, "description": description})
    return {"suggestions": results}


@router.get("/details")
def place_details(
    place_id: str = Query(..., min_length=1),
    language: Optional[str] = Query("en", alias="languageCode"),
) -> dict:
    """
    Proxy to Google Place Details (New). Returns id, displayName, formattedAddress,
    and location (lat/lng) for the given place_id.
    """
    api_key = _get_api_key()
    # Ensure place_id does not include path prefix
    raw_id = _place_id_from_resource(place_id)
    if not re.match(r"^[A-Za-z0-9_-]+$", raw_id):
        raise HTTPException(status_code=400, detail="Invalid place_id")
    url = PLACE_DETAILS_URL_TEMPLATE.format(raw_id)
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,displayName,formattedAddress,location",
    }
    params = {}
    if language:
        params["languageCode"] = language
    try:
        r = requests.get(url, headers=headers, params=params or None, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Place details request failed: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Invalid response from Places API: {str(e)}",
        )

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
        raise HTTPException(
            status_code=502,
            detail="Place details did not return coordinates",
        )
    return {
        "place_id": data.get("id") or raw_id,
        "name": name,
        "formattedAddress": formatted_address,
        "latitude": float(latitude),
        "longitude": float(longitude),
    }
