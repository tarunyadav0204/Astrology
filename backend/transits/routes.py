"""
Planetary Transit API Routes
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import swisseph as swe

from auth import get_current_user, User
from utils.timezone_service import parse_timezone_offset

router = APIRouter(prefix="/transits", tags=["transits"])


# Request models for Sade Sati (kept here to avoid importing from main)
class _BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    place: str = ""
    gender: str = ""
    relation: Optional[str] = "other"


class _TransitRequest(BaseModel):
    birth_data: _BirthData
    transit_date: str


def _saturn_sign_on_date(year: int, month: int, day: int) -> int:
    """Saturn's sidereal sign (0-11) on the given date at noon UT."""
    jd = swe.julday(year, month, day, 12.0)
    saturn_pos = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)[0][0]
    return int(saturn_pos / 30) % 12


def _first_day_saturn_in_signs(year: int, month: int, signs: tuple) -> Optional[datetime]:
    """First day in this month when Saturn is in any of the given signs. Returns date or None."""
    for day in range(1, 32):
        try:
            if _saturn_sign_on_date(year, month, day) in signs:
                return datetime(year, month, day).date()
        except Exception:
            pass
    return None


def _last_day_saturn_in_signs(year: int, month: int, signs: tuple) -> Optional[datetime]:
    """Last day in this month when Saturn is in any of the given signs. Returns date or None."""
    for day in range(31, 0, -1):
        try:
            if _saturn_sign_on_date(year, month, day) in signs:
                return datetime(year, month, day).date()
        except Exception:
            pass
    return None


def _get_sade_sati_periods(birth_data: _BirthData) -> list:
    """Compute all Sade Sati periods (Saturn in 12th, 1st, 2nd from Moon) for ~100 years.
    Uses actual transit dates: period starts when Saturn enters the 12th sign from Moon,
    ends when Saturn leaves the 2nd sign from Moon (not month boundaries)."""
    time_parts = birth_data.time.split(':')
    hour = float(time_parts[0]) + float(time_parts[1]) / 60
    tz_offset = parse_timezone_offset('', birth_data.latitude, birth_data.longitude)
    utc_hour = hour - tz_offset
    birth_jd = swe.julday(
        int(birth_data.date.split('-')[0]),
        int(birth_data.date.split('-')[1]),
        int(birth_data.date.split('-')[2]),
        utc_hour
    )
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    moon_pos = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    moon_sign = int(moon_pos / 30)  # 0-11
    sade_sati_signs = ((moon_sign - 1) % 12, moon_sign, (moon_sign + 1) % 12)

    birth_year = int(birth_data.date.split('-')[0])
    birth_date = datetime(
        int(birth_data.date.split('-')[0]),
        int(birth_data.date.split('-')[1]),
        int(birth_data.date.split('-')[2]),
    ).date()
    start_year = birth_year - 25
    end_year = birth_year + 75
    today = datetime.now().date()

    periods = []
    in_period = False
    period_start = None

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            try:
                jd = swe.julday(year, month, 15, 12.0)
                saturn_pos = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)[0][0]
                saturn_sign = int(saturn_pos / 30)
            except Exception:
                continue
            in_sade_sati = saturn_sign in sade_sati_signs
            if in_sade_sati and not in_period:
                in_period = True
                # Actual date Saturn entered: check this month first, then previous month (16th onward)
                period_start = _first_day_saturn_in_signs(year, month, sade_sati_signs)
                if month == 1:
                    prev_year, prev_month = year - 1, 12
                else:
                    prev_year, prev_month = year, month - 1
                for d in range(16, 32):
                    try:
                        if _saturn_sign_on_date(prev_year, prev_month, d) in sade_sati_signs:
                            earlier = datetime(prev_year, prev_month, d).date()
                            if period_start is None or earlier < period_start:
                                period_start = earlier
                            break
                    except Exception:
                        pass
                if period_start is None:
                    period_start = datetime(year, month, 1).date()
            elif not in_sade_sati and in_period:
                in_period = False
                # Last day Saturn was still in Sade Sati: check from 15th backward (this month and prev)
                end_date = None
                for d in range(15, 0, -1):
                    try:
                        if _saturn_sign_on_date(year, month, d) in sade_sati_signs:
                            end_date = datetime(year, month, d).date()
                            break
                    except Exception:
                        pass
                if end_date is None and month > 1:
                    prev_month = month - 1
                    prev_year = year
                    end_date = _last_day_saturn_in_signs(prev_year, prev_month, sade_sati_signs)
                if end_date is None:
                    end_date = (datetime(year, month, 1) - timedelta(days=1)).date()
                if period_start and end_date >= birth_date:
                    is_current = period_start <= today <= end_date
                    periods.append({
                        "start_date": period_start.isoformat(),
                        "end_date": end_date.isoformat(),
                        "is_current": is_current
                    })
                period_start = None
    if in_period and period_start:
        end_date = datetime(end_year, 12, 31).date()
        if end_date >= birth_date:
            periods.append({
                "start_date": period_start.isoformat(),
                "end_date": end_date.isoformat(),
                "is_current": period_start <= today <= end_date
            })
    return periods

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


@router.post("/sade-sati-periods")
async def sade_sati_periods(
    request: _TransitRequest,
    current_user: User = Depends(get_current_user),
):
    """Return all Sade Sati periods for the native (past and future, ~100 years)."""
    periods = _get_sade_sati_periods(request.birth_data)
    return {"periods": periods}