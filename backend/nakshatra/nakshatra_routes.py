from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3
import os
from datetime import datetime
from calculators.annual_nakshatra_calculator import AnnualNakshatraCalculator

router = APIRouter()

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'astrology.db')
    return sqlite3.connect(db_path)

@router.get("/nakshatra/{nakshatra_name}/{year}")
async def get_nakshatra_year_data(
    nakshatra_name: str,
    year: int,
    latitude: Optional[float] = Query(28.6139, description="Latitude for location"),
    longitude: Optional[float] = Query(77.2090, description="Longitude for location"),
    location_name: Optional[str] = Query("New Delhi, India", description="Location name")
):
    """Get nakshatra periods for specific year and location"""
    
    try:
        calculator = AnnualNakshatraCalculator()
        
        # Validate nakshatra name
        if nakshatra_name.title() not in calculator.NAKSHATRA_NAMES:
            raise HTTPException(status_code=404, detail=f"Nakshatra '{nakshatra_name}' not found")
        
        # Validate year
        current_year = datetime.now().year
        if year < 1900 or year > current_year + 10:
            raise HTTPException(status_code=400, detail="Year must be between 1900 and 10 years from now")
        
        # Calculate annual periods
        nakshatra_data = calculator.calculate_annual_nakshatra_periods(
            nakshatra_name.title(), year, latitude, longitude
        )
        
        # Get detailed nakshatra info from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, lord, deity, nature, guna, description, characteristics, 
                   positive_traits, negative_traits, careers, compatibility
            FROM nakshatras WHERE LOWER(name) = LOWER(?)
        """, (nakshatra_name.title(),))
        
        db_result = cursor.fetchone()
        conn.close()
        
        if db_result:
            detailed_info = {
                'name': db_result[0],
                'lord': db_result[1],
                'deity': db_result[2],
                'nature': db_result[3],
                'guna': db_result[4],
                'description': db_result[5],
                'characteristics': db_result[6],
                'positive_traits': db_result[7],
                'negative_traits': db_result[8],
                'careers': db_result[9],
                'compatibility': db_result[10]
            }
        else:
            detailed_info = nakshatra_data['properties']
        
        # Get navigation info (previous/next nakshatras)
        current_index = calculator.NAKSHATRA_NAMES.index(nakshatra_name.title())
        prev_nakshatra = calculator.NAKSHATRA_NAMES[current_index - 1] if current_index > 0 else calculator.NAKSHATRA_NAMES[-1]
        next_nakshatra = calculator.NAKSHATRA_NAMES[current_index + 1] if current_index < 26 else calculator.NAKSHATRA_NAMES[0]
        
        return {
            'success': True,
            'nakshatra': nakshatra_name.title(),
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
                'next': next_nakshatra
            },
            'seo': {
                'title': f"{nakshatra_name.title()} Nakshatra {year} - Timings and Dates",
                'description': f"Complete {nakshatra_name.title()} nakshatra calendar for {year}. Find all {nakshatra_name.title()} nakshatra dates, timings, and astrological significance.",
                'keywords': f"{nakshatra_name.lower()} nakshatra, {year}, vedic astrology, nakshatra calendar, moon phases"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating nakshatra data: {str(e)}")

@router.get("/nakshatras/list")
async def get_all_nakshatras():
    """Get list of all 27 nakshatras with basic info"""
    
    try:
        calculator = AnnualNakshatraCalculator()
        nakshatras_list = calculator.get_all_nakshatras_list()
        
        # Get additional info from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, lord, deity, nature, guna, description
            FROM nakshatras ORDER BY id
        """)
        
        db_results = cursor.fetchall()
        conn.close()
        
        # Merge calculator data with database data
        enhanced_list = []
        for i, calc_nak in enumerate(nakshatras_list):
            enhanced_nak = calc_nak.copy()
            
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
        
        if nakshatra_name.title() not in calculator.NAKSHATRA_NAMES:
            raise HTTPException(status_code=404, detail=f"Nakshatra '{nakshatra_name}' not found")
        
        # Get from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, lord, deity, nature, guna, description, characteristics,
                   positive_traits, negative_traits, careers, compatibility
            FROM nakshatras WHERE name = ?
        """, (nakshatra_name.title(),))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Detailed info for '{nakshatra_name}' not found")
        
        # Get navigation info
        current_index = calculator.NAKSHATRA_NAMES.index(nakshatra_name.title())
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
                'next': next_nakshatra
            },
            'seo': {
                'title': f"{nakshatra_name.title()} Nakshatra - Meaning, Characteristics & Significance",
                'description': f"Learn about {nakshatra_name.title()} nakshatra in Vedic astrology. Discover its lord, deity, characteristics, career options, and compatibility.",
                'keywords': f"{nakshatra_name.lower()} nakshatra, vedic astrology, {result[1].lower()}, {result[2].lower()}, nakshatra meaning"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching nakshatra info: {str(e)}")