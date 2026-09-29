"""Resolve non-astrological portrait direction from saved birth-chart facts."""

from __future__ import annotations

import os
import threading
from typing import Any

import httpx


_COUNTRY_CACHE: dict[tuple[float, float], dict[str, str]] = {}
_CACHE_LOCK = threading.Lock()

SOUTH_ASIA = {"AF", "BD", "BT", "IN", "MV", "NP", "PK", "LK"}
EAST_SOUTHEAST_ASIA = {
    "BN", "KH", "CN", "HK", "ID", "JP", "KP", "KR", "LA", "MO", "MY", "MM", "MN", "PH", "SG", "TH",
    "TL", "TW", "VN",
}
MIDDLE_EAST_NORTH_AFRICA = {
    "DZ", "BH", "EG", "EH", "IR", "IQ", "IL", "JO", "KW", "LB", "LY", "MA", "OM", "PS", "QA", "SA",
    "SD", "SY", "TN", "TR", "AE", "YE",
}
SUB_SAHARAN_AFRICA = {
    "AO", "BJ", "BW", "BF", "BI", "CV", "CM", "CF", "TD", "KM", "CG", "CD", "CI", "DJ", "GQ", "ER",
    "SZ", "ET", "GA", "GM", "GH", "GN", "GW", "KE", "LS", "LR", "MG", "MW", "ML", "MR", "MU", "MZ",
    "NA", "NE", "NG", "RW", "ST", "SN", "SC", "SL", "SO", "ZA", "SS", "TZ", "TG", "UG", "ZM", "ZW",
}
EUROPE = {
    "AL", "AD", "AT", "BY", "BE", "BA", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IS", "IE", "IT", "XK", "LV", "LI", "LT", "LU", "MT", "MD", "MC", "ME", "NL", "MK", "NO",
    "PL", "PT", "RO", "RU", "SM", "RS", "SK", "SI", "ES", "SE", "CH", "UA", "GB", "VA",
}
LATIN_AMERICA = {
    "AR", "BO", "BR", "CL", "CO", "CR", "CU", "DO", "EC", "SV", "GF", "GT", "HT", "HN", "MX", "NI",
    "PA", "PY", "PE", "PR", "UY", "VE",
}
NORTH_AMERICA = {"US", "CA", "BM", "GL", "PM"}
CENTRAL_ASIA = {"AM", "AZ", "GE", "KZ", "KG", "TJ", "TM", "UZ"}
OCEANIA = {
    "AS", "AU", "CK", "FJ", "PF", "GU", "KI", "MH", "FM", "NR", "NC", "NZ", "NU", "MP", "PW", "PG",
    "PN", "WS", "SB", "TK", "TO", "TV", "VU", "WF",
}


def partner_presentation(native_gender: str) -> str:
    normalized = (native_gender or "").strip().lower().replace("_", " ")
    if normalized in {"male", "man", "m", "boy"}:
        return "feminine"
    if normalized in {"female", "woman", "f", "girl"}:
        return "masculine"
    raise ValueError("The selected chart must have Male or Female saved before a partner portrait can be created")


def visual_context_for_country(country_code: str) -> str:
    code = (country_code or "").strip().upper()
    groups = (
        (SOUTH_ASIA, "south_asian"),
        (EAST_SOUTHEAST_ASIA, "east_southeast_asian"),
        (MIDDLE_EAST_NORTH_AFRICA, "middle_eastern_north_african"),
        (SUB_SAHARAN_AFRICA, "sub_saharan_african"),
        (EUROPE, "european"),
        (LATIN_AMERICA, "latin_american"),
        (NORTH_AMERICA, "north_american"),
        (CENTRAL_ASIA, "central_asian"),
        (OCEANIA, "oceania"),
    )
    for countries, context in groups:
        if code in countries:
            return context
    return "global_mixed"


async def country_from_coordinates(latitude: float, longitude: float) -> dict[str, str]:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("The selected chart has invalid birth coordinates")
    key = (round(float(latitude), 4), round(float(longitude), 4))
    with _CACHE_LOCK:
        cached = _COUNTRY_CACHE.get(key)
    if cached:
        return dict(cached)

    base_url = os.getenv("PARTNER_PORTRAIT_GEOCODER_URL", "https://nominatim.openstreetmap.org/reverse").strip()
    user_agent = os.getenv("PARTNER_PORTRAIT_GEOCODER_USER_AGENT", "AstroRoshni/1.0").strip()
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(
                base_url,
                params={
                    "format": "jsonv2", "lat": latitude, "lon": longitude, "zoom": 3, "addressdetails": 1,
                },
                headers={"User-Agent": user_agent, "Accept-Language": "en"},
            )
        response.raise_for_status()
        address = (response.json() or {}).get("address") or {}
        country_name = str(address.get("country") or "").strip()
        country_code = str(address.get("country_code") or "").strip().upper()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise RuntimeError("Birth country could not be resolved from the saved coordinates") from exc
    if not country_name or len(country_code) != 2:
        raise RuntimeError("Birth country could not be resolved from the saved coordinates")

    resolved = {"country_name": country_name, "country_code": country_code}
    with _CACHE_LOCK:
        _COUNTRY_CACHE[key] = resolved
    return dict(resolved)


async def derive_art_direction(birth: dict[str, Any]) -> dict[str, str]:
    presentation = partner_presentation(str(birth.get("gender") or ""))
    country = await country_from_coordinates(float(birth["latitude"]), float(birth["longitude"]))
    return {
        "presentation": presentation,
        "visual_context": visual_context_for_country(country["country_code"]),
        **country,
        "source": "birth_chart_gender_and_coordinates",
    }
