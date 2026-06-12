from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, List, Any, Tuple
import os
from datetime import datetime
from collections import defaultdict, OrderedDict
from calculators.annual_nakshatra_calculator import AnnualNakshatraCalculator
from db import get_conn, execute

router = APIRouter()

# In-memory cache for nakshatra year calendar (slow to compute). Key -> response dict. Max 100 entries.
# Bump NAKSHATRA_YEAR_RESPONSE_VERSION when dedupe/response shape changes so old cache entries are not reused.
NAKSHATRA_YEAR_RESPONSE_VERSION = 3
NAKSHATRA_YEAR_CACHE: OrderedDict = OrderedDict()
NAKSHATRA_YEAR_CACHE_MAX = 100


def _normalize_nakshatra_name(raw_name: str, valid_names: List[str]) -> str:
    """Accept canonical names and SEO slugs such as purva-phalguni."""
    normalized = " ".join(str(raw_name or "").strip().replace("-", " ").replace("_", " ").split())
    lookup = {name.lower(): name for name in valid_names}
    canonical = lookup.get(normalized.lower())
    if not canonical:
        raise HTTPException(status_code=404, detail=f"Nakshatra '{raw_name}' not found")
    return canonical


def _nakshatra_slug(name: str) -> str:
    return str(name or "").strip().lower().replace(" ", "-")


def _nakshatra_year_cache_key(year: int, latitude: float, longitude: float, ayanamsa_correction: float) -> Tuple:
    return (NAKSHATRA_YEAR_RESPONSE_VERSION, year, round(float(latitude), 4), round(float(longitude), 4), round(float(ayanamsa_correction), 4))


def _build_nakshatra_year_response(year: int, latitude: float, longitude: float, ayanamsa_correction: float) -> Dict[str, Any]:
    """Compute nakshatra year by month. Uses a single pass so each boundary is used once:
    end of one nakshatra = start of next (no overlaps or gaps)."""
    calculator = AnnualNakshatraCalculator()
    months: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    ayan_corr = float(ayanamsa_correction)
    all_periods = calculator.calculate_annual_nakshatra_periods_all_continuous(
        year, latitude, longitude, ayanamsa_correction_degrees=ayan_corr
    )
    # Build list of period dicts per month, then dedupe by (nakshatra, start_date): keep only the first by start_time (removes duplicate rows from calculator artifacts)
    for period in all_periods:
        start_dt = period["start_datetime"]
        month_key = str(start_dt.month)
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = period["end_datetime"].strftime("%Y-%m-%d")
        start_time = period.get("start_time", start_dt.strftime("%I:%M %p"))
        nakshatra = period["nakshatra"]
        months[month_key].append({
            "nakshatra": nakshatra,
            "start_date": start_date,
            "end_date": end_date,
            "start_time": start_time,
            "end_time": period.get("end_time", period["end_datetime"].strftime("%I:%M %p")),
        })
    for month_key in months:
        months[month_key].sort(key=lambda p: (p["start_date"], p.get("start_time", "")))
        # One row per (nakshatra, start_date): keep first when sorted by (start_date, start_time)
        seen_key: set = set()
        deduped = []
        for p in months[month_key]:
            key = (p["nakshatra"], p["start_date"])
            if key in seen_key:
                continue
            seen_key.add(key)
            deduped.append(p)
        months[month_key] = deduped
    return {
        "success": True,
        "year": year,
        "months": dict(months),
        "location": {"latitude": latitude, "longitude": longitude},
    }


def get_db_connection():
    """Get database connection (Postgres) via shared db utility."""
    # Kept for backward compatibility with existing call sites
    return get_conn()


@router.get("/nakshatra/year/{year}")
async def get_nakshatra_year_by_month(
    year: int,
    latitude: Optional[float] = Query(28.6139, description="Latitude for location"),
    longitude: Optional[float] = Query(77.2090, description="Longitude for location"),
    ayanamsa_correction: Optional[float] = Query(0.0, description="Ayanamsa correction in degrees (e.g. -0.2 for Drik Panchang alignment)"),
):
    """Get all nakshatra periods for a year, grouped by month (1-12). Cached on server."""
    try:
        current_year = datetime.now().year
        if year < 1900 or year > current_year + 10:
            raise HTTPException(status_code=400, detail="Year must be between 1900 and 10 years from now")

        lat = float(latitude) if latitude is not None else 28.6139
        lon = float(longitude) if longitude is not None else 77.2090
        ayan_corr = float(ayanamsa_correction) if ayanamsa_correction is not None else 0.0
        cache_key = _nakshatra_year_cache_key(year, lat, lon, ayan_corr)

        if cache_key in NAKSHATRA_YEAR_CACHE:
            NAKSHATRA_YEAR_CACHE.move_to_end(cache_key)
            return NAKSHATRA_YEAR_CACHE[cache_key]

        result = _build_nakshatra_year_response(year, lat, lon, ayan_corr)
        NAKSHATRA_YEAR_CACHE[cache_key] = result
        NAKSHATRA_YEAR_CACHE.move_to_end(cache_key)
        if len(NAKSHATRA_YEAR_CACHE) > NAKSHATRA_YEAR_CACHE_MAX:
            NAKSHATRA_YEAR_CACHE.popitem(last=False)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building nakshatra year calendar: {str(e)}")


@router.get("/nakshatra/{nakshatra_name}/{year}")
async def get_nakshatra_year_data(
    nakshatra_name: str,
    year: int,
    latitude: Optional[float] = Query(28.6139, description="Latitude for location"),
    longitude: Optional[float] = Query(77.2090, description="Longitude for location"),
    location_name: Optional[str] = Query("New Delhi, India", description="Location name"),
    ayanamsa_correction: Optional[float] = Query(0.0, description="Ayanamsa correction in degrees"),
):
    """Get nakshatra periods for specific year and location"""
    
    try:
        calculator = AnnualNakshatraCalculator()
        canonical_nakshatra = _normalize_nakshatra_name(nakshatra_name, calculator.NAKSHATRA_NAMES)
        
        # Validate year
        current_year = datetime.now().year
        if year < 1900 or year > current_year + 10:
            raise HTTPException(status_code=400, detail="Year must be between 1900 and 10 years from now")

        ayan_corr = float(ayanamsa_correction) if ayanamsa_correction is not None else 0.0
        
        # Calculate annual periods
        nakshatra_data = calculator.calculate_annual_nakshatra_periods(
            canonical_nakshatra, year, latitude, longitude, ayanamsa_correction_degrees=ayan_corr
        )
        
        # Add dynamic auspiciousness to each period based on multiple factors
        for period in nakshatra_data['periods']:
            period['auspiciousness'] = calculator.calculate_period_auspiciousness(
                canonical_nakshatra, period['start_datetime']
            )
        
        # Get detailed nakshatra info from database
        with get_db_connection() as conn:
            cur = execute(
                conn,
                """
                SELECT name, lord, deity, nature, guna, description, characteristics,
                       positive_traits, negative_traits, careers, compatibility
                FROM nakshatras
                WHERE LOWER(name) = LOWER(%s)
                """,
                (canonical_nakshatra,),
            )
            db_result = cur.fetchone()
        
        # Start with calculator properties (includes symbol)
        detailed_info = nakshatra_data['properties'].copy()
        
        # Merge with database data if available
        if db_result:
            detailed_info.update({
                'description': db_result[5],
                'characteristics': db_result[6],
                'positive_traits': db_result[7],
                'negative_traits': db_result[8],
                'careers': db_result[9],
                'compatibility': db_result[10]
            })
        
        # Get navigation info (previous/next nakshatras)
        current_index = calculator.NAKSHATRA_NAMES.index(canonical_nakshatra)
        prev_nakshatra = calculator.NAKSHATRA_NAMES[current_index - 1] if current_index > 0 else calculator.NAKSHATRA_NAMES[-1]
        next_nakshatra = calculator.NAKSHATRA_NAMES[current_index + 1] if current_index < 26 else calculator.NAKSHATRA_NAMES[0]
        
        return {
            'success': True,
            'nakshatra': canonical_nakshatra,
            'slug': _nakshatra_slug(canonical_nakshatra),
            'year': year,
            'location': {
                'name': location_name,
                'latitude': latitude,
                'longitude': longitude
            },
            'properties': detailed_info,
            'periods': nakshatra_data['periods'],
            'total_periods': nakshatra_data['total_periods'],
            'navigation': {
                'previous': prev_nakshatra,
                'previous_slug': _nakshatra_slug(prev_nakshatra),
                'next': next_nakshatra,
                'next_slug': _nakshatra_slug(next_nakshatra)
            },
            'seo': {
                'title': f"{canonical_nakshatra} Nakshatra {year} - Timings and Dates",
                'description': f"Complete {canonical_nakshatra} nakshatra calendar for {year}. Find all {canonical_nakshatra} nakshatra dates, timings, and astrological significance.",
                'keywords': f"{canonical_nakshatra.lower()} nakshatra, {year}, vedic astrology, nakshatra calendar, moon phases"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating nakshatra data: {str(e)}")


@router.get("/nakshatras/list")
async def get_all_nakshatras():
    """Get list of all 27 nakshatras with basic info"""
    
    try:
        calculator = AnnualNakshatraCalculator()
        nakshatras_list = calculator.get_all_nakshatras_list()
        
        # Get additional info from database
        with get_db_connection() as conn:
            cur = execute(
                conn,
                """
                SELECT name, lord, deity, nature, guna, description
                FROM nakshatras
                ORDER BY id
                """,
            )
            db_results = cur.fetchall()
        
        # Merge calculator data with database data
        enhanced_list = []
        for i, calc_nak in enumerate(nakshatras_list):
            enhanced_nak = calc_nak.copy()
            
            # Add symbol from calculator properties
            calculator_props = calculator.NAKSHATRA_PROPERTIES.get(calc_nak['name'], {})
            if 'symbol' in calculator_props:
                enhanced_nak['symbol'] = calculator_props['symbol']
            
            # Find matching database entry
            for db_nak in db_results:
                if db_nak[0] == calc_nak['name']:
                    enhanced_nak.update({
                        'description': db_nak[5],
                        'detailed_available': True
                    })
                    break
            
            enhanced_list.append(enhanced_nak)
        
        return {
            'success': True,
            'nakshatras': enhanced_list,
            'total': len(enhanced_list),
            'seo': {
                'title': "27 Nakshatras - Complete Vedic Astrology Guide",
                'description': "Explore all 27 nakshatras in Vedic astrology. Learn about nakshatra lords, deities, characteristics, and their significance in your horoscope.",
                'keywords': "nakshatras, vedic astrology, moon signs, nakshatra list, astrology guide"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nakshatras: {str(e)}")

@router.get("/nakshatra/{nakshatra_name}/info")
async def get_nakshatra_info(nakshatra_name: str):
    """Get detailed information about a specific nakshatra"""
    
    try:
        calculator = AnnualNakshatraCalculator()
        canonical_nakshatra = _normalize_nakshatra_name(nakshatra_name, calculator.NAKSHATRA_NAMES)
        
        # Get from database
        with get_db_connection() as conn:
            cur = execute(
                conn,
                """
                SELECT name, lord, deity, nature, guna, description, characteristics,
                       positive_traits, negative_traits, careers, compatibility
                FROM nakshatras
                WHERE name = %s
                """,
                (canonical_nakshatra,),
            )
            result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Detailed info for '{nakshatra_name}' not found")
        
        # Get navigation info
        current_index = calculator.NAKSHATRA_NAMES.index(canonical_nakshatra)
        prev_nakshatra = calculator.NAKSHATRA_NAMES[current_index - 1] if current_index > 0 else calculator.NAKSHATRA_NAMES[-1]
        next_nakshatra = calculator.NAKSHATRA_NAMES[current_index + 1] if current_index < 26 else calculator.NAKSHATRA_NAMES[0]
        
        nakshatra_info = {
            'name': result[0],
            'lord': result[1],
            'deity': result[2],
            'nature': result[3],
            'guna': result[4],
            'description': result[5],
            'characteristics': result[6],
            'positive_traits': result[7],
            'negative_traits': result[8],
            'careers': result[9],
            'compatibility': result[10],
            'index': current_index + 1,
            'degree_range': f"{current_index * 13.33:.1f}° - {(current_index + 1) * 13.33:.1f}°"
        }
        
        return {
            'success': True,
            'nakshatra': nakshatra_info,
            'navigation': {
                'previous': prev_nakshatra,
                'previous_slug': _nakshatra_slug(prev_nakshatra),
                'next': next_nakshatra,
                'next_slug': _nakshatra_slug(next_nakshatra)
            },
            'seo': {
                'title': f"{canonical_nakshatra} Nakshatra - Meaning, Characteristics & Significance",
                'description': f"Learn about {canonical_nakshatra} nakshatra in Vedic astrology. Discover its lord, deity, characteristics, career options, and compatibility.",
                'keywords': f"{nakshatra_name.lower()} nakshatra, vedic astrology, {result[1].lower()}, {result[2].lower()}, nakshatra meaning"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nakshatra info: {str(e)}")
