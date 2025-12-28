"""
Planetary Transit API Routes
"""
from fastapi import APIRouter
from datetime import datetime, timedelta
import swisseph as swe

router = APIRouter(prefix="/transits", tags=["transits"])

@router.get("/monthly/{year}/{month}")
async def get_monthly_transits(year: int, month: int):
    """Get planetary transits for a specific month"""
    transits = []
    
    # Initialize Swiss Ephemeris
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Planet data with symbols
    planets = {
        swe.SUN: {"name": "Sun", "symbol": "☉"},
        swe.MARS: {"name": "Mars", "symbol": "♂"},
        swe.MERCURY: {"name": "Mercury", "symbol": "☿"},
        swe.JUPITER: {"name": "Jupiter", "symbol": "♃"},
        swe.VENUS: {"name": "Venus", "symbol": "♀"},
        swe.SATURN: {"name": "Saturn", "symbol": "♄"}
    }
    
    # Zodiac signs
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # Check each day of the month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    current_date = start_date
    while current_date < end_date:
        jd = swe.julday(current_date.year, current_date.month, current_date.day, 12)
        
        for planet_id, planet_info in planets.items():
            try:
                # Get planet position
                planet_pos = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)[0][0]
                current_sign = int(planet_pos / 30)
                
                # Check previous day position
                prev_jd = jd - 1
                prev_pos = swe.calc_ut(prev_jd, planet_id, swe.FLG_SIDEREAL)[0][0]
                prev_sign = int(prev_pos / 30)
                
                # If sign changed, record transit
                if current_sign != prev_sign:
                    transits.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "planet": planet_info["name"],
                        "symbol": planet_info["symbol"],
                        "sign": signs[current_sign],
                        "time": "12:00",
                        "type": "transit"
                    })
            except:
                continue
        
        current_date += timedelta(days=1)
    
    return {"transits": transits}