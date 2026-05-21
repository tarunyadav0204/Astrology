"""Google Places API proxy. Keeps API key on server; exposes autocomplete and place details."""

import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from utils.google_places_client import place_details as gp_place_details
from utils.google_places_client import places_autocomplete_suggestions

router = APIRouter(prefix="/places", tags=["places"])


def _get_api_key() -> str:
    if not (os.environ.get("GOOGLE_PLACES_API_KEY") or "").strip():
        raise HTTPException(
            status_code=503,
            detail="Places API is not configured (missing GOOGLE_PLACES_API_KEY)",
        )
    return (os.environ.get("GOOGLE_PLACES_API_KEY") or "").strip()


@router.get("/autocomplete")
def places_autocomplete(
    q: str = Query(..., min_length=1, max_length=200),
    language: Optional[str] = Query("en", alias="languageCode"),
) -> dict:
    """
    Proxy to Google Places Autocomplete (New). Returns a list of suggestions with
    place_id and description for use in location search.
    """
    _get_api_key()
    try:
        results = places_autocomplete_suggestions(q.strip(), language=language or "en", limit=10)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Places autocomplete request failed: {str(e)}",
        ) from e
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
    _get_api_key()
    try:
        return gp_place_details(place_id, language=language or "en")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Place details request failed: {str(e)}",
        ) from e
