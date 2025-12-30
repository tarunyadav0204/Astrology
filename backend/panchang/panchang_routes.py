from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import swisseph as swe
import math
from calculators.panchang_calculator import PanchangCalculator
from .monthly_panchang_calculator import MonthlyPanchangCalculator

router = APIRouter()
panchang_calc = PanchangCalculator()
monthly_panchang_calc = MonthlyPanchangCalculator()

class PanchangRequest(BaseModel):
    transit_date: str
    birth_data: dict

class SunriseSunsetRequest(BaseModel):
    date: str
    latitude: float
    longitude: float

class MoonPhaseRequest(BaseModel):
    date: str

class InauspiciousTimesRequest(BaseModel):
    date: str
    latitude: float
    longitude: float

@router.post("/calculate-panchang")
async def calculate_panchang(request: PanchangRequest):
    try:
        print(f"[DEBUG] Panchang request: transit_date={request.transit_date}, birth_data={request.birth_data}")
        
        birth_data = request.birth_data
        
        # Handle different request formats
        if isinstance(birth_data, dict):
            latitude = birth_data.get('latitude')
            longitude = birth_data.get('longitude')
            timezone = birth_data.get('timezone', 'UTC+5:30')
        else:
            # Fallback for other formats
            latitude = getattr(birth_data, 'latitude', None)
            longitude = getattr(birth_data, 'longitude', None)
            timezone = getattr(birth_data, 'timezone', 'UTC+5:30')
        
        print(f"[DEBUG] Extracted: lat={latitude}, lon={longitude}, tz={timezone}")
        
        # Convert numeric timezone to string format
        if isinstance(timezone, (int, float)):
            if timezone >= 0:
                hours = int(timezone)
                minutes = int((timezone - hours) * 60)
                timezone = f'UTC+{hours}:{minutes:02d}'
            else:
                hours = int(abs(timezone))
                minutes = int((abs(timezone) - hours) * 60)
                timezone = f'UTC-{hours}:{minutes:02d}'
        
        if latitude is None or longitude is None:
            raise HTTPException(status_code=422, detail="Missing latitude or longitude in birth_data")
        
        # Ensure timezone is a string
        if not isinstance(timezone, str):
            timezone = 'UTC+5:30'  # Default fallback
        
        # Calculate basic panchang data
        basic_panchang = panchang_calc.calculate_panchang(
            request.transit_date,
            "12:00:00",
            float(latitude),
            float(longitude),
            str(timezone)
        )
        
        # Get sunrise/sunset data
        sunrise_sunset_data = panchang_calc.get_local_sunrise_sunset(
            request.transit_date,
            float(latitude),
            float(longitude),
            str(timezone)
        )
        
        # Transform to frontend-expected format
        panchang_data = {
            'tithi': {
                'number': basic_panchang['tithi']['number'],
                'name': basic_panchang['tithi']['name'],
                'paksha': basic_panchang['tithi']['paksha'],
                'lord': 'Moon',  # Tithi lord is always Moon
                'start_time': sunrise_sunset_data.get('sunrise'),
                'end_time': sunrise_sunset_data.get('sunset'),
                'elapsed': basic_panchang['tithi']['degrees_traversed'],
                'duration': 12.0  # Tithi duration in degrees
            },
            'vara': {
                'number': basic_panchang['vara']['number'],
                'name': basic_panchang['vara']['name'],
                'deity': 'Surya',  # Default deity
                'favorable_activities': ['General activities'],
                'lucky_color': '#FFD700'  # Default golden color
            },
            'nakshatra': {
                'number': basic_panchang['nakshatra']['number'],
                'name': basic_panchang['nakshatra']['name'],
                'lord': 'Various',  # Simplified
                'deity': 'Various',
                'nature': 'Balanced',
                'pada': 1,  # Simplified
                'career_focus': 'General',
                'symbol': '⭐',
                'guna': 'Sattva',
                'compatible_nakshatras': [],
                'start_time': sunrise_sunset_data.get('sunrise'),
                'end_time': sunrise_sunset_data.get('sunset')
            },
            'yoga': {
                'number': basic_panchang['yoga']['number'],
                'name': basic_panchang['yoga']['name'],
                'effect': 'Balanced',
                'quality': 'Good',
                'recommended_activities': ['Spiritual practices'],
                'spiritual_practice': 'Meditation',
                'start_time': sunrise_sunset_data.get('sunrise'),
                'end_time': sunrise_sunset_data.get('sunset')
            },
            'karana': {
                'number': basic_panchang['karana']['number'],
                'name': basic_panchang['karana']['name'],
                'nature': 'Balanced',
                'effect': 'Neutral',
                'duration': 6.0,  # Karana duration in hours
                'suitable_activities': ['General work'],
                'business_suitable': True
            }
        }
        
        # Merge with sunrise/sunset data
        result = {**panchang_data, **sunrise_sunset_data}
        
        print(f"[DEBUG] Final panchang result keys: {list(result.keys())}")
        
        return result
        
    except ValueError as e:
        print(f"[ERROR] ValueError in panchang calculation: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid data format: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Exception in panchang calculation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-sunrise-sunset")
async def calculate_sunrise_sunset(request: SunriseSunsetRequest):
    try:
        print(f"[DEBUG] Sunrise/Sunset request: date={request.date}, lat={request.latitude}, lon={request.longitude}")
        
        # Use professional PanchangCalculator instead of amateur math
        result = panchang_calc.get_local_sunrise_sunset(
            request.date, 
            request.latitude, 
            request.longitude
        )
        
        print(f"[DEBUG] Sunrise/Sunset result: {result}")
        return result
        
    except Exception as e:
        print(f"[ERROR] Sunrise/Sunset calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-moon-phase")
async def calculate_moon_phase(request: MoonPhaseRequest):
    try:
        date_obj = datetime.strptime(request.date, '%Y-%m-%d')
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 12.0)
        
        # Calculate Moon position and phase
        moon_data = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        sun_data = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
        
        moon_pos = moon_data[0][0]
        sun_pos = sun_data[0][0]
        
        # Calculate phase
        phase_angle = (moon_pos - sun_pos) % 360
        illumination_percentage = (1 - math.cos(math.radians(phase_angle))) / 2 * 100
        
        # Moon age in days
        moon_age = phase_angle / 12.2  # Approximate
        
        # Phase name
        phase_names = ['New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous',
                      'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent']
        phase_index = int((phase_angle + 22.5) / 45) % 8
        phase_name = phase_names[phase_index]
        
        # Moon sign
        moon_sign = int(moon_pos / 30)
        moon_degree = moon_pos % 30
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        sign_lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
                     'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        
        elements = ['Fire', 'Earth', 'Air', 'Water', 'Fire', 'Earth',
                   'Air', 'Water', 'Fire', 'Earth', 'Air', 'Water']
        
        qualities = ['Cardinal', 'Fixed', 'Mutable', 'Cardinal', 'Fixed', 'Mutable',
                    'Cardinal', 'Fixed', 'Mutable', 'Cardinal', 'Fixed', 'Mutable']
        
        # Moon distance (approximate)
        distance_km = 384400  # Average distance
        
        # Lunar month name (simplified)
        lunar_months = ['Chaitra', 'Vaisakha', 'Jyeshtha', 'Ashadha', 'Shravana', 'Bhadrapada',
                       'Ashwin', 'Kartik', 'Margashirsha', 'Pausha', 'Magha', 'Phalguna']
        lunar_month_name = lunar_months[date_obj.month - 1]
        
        # Paksha significance
        paksha_significance = 'Waxing Moon - growth and increase' if phase_angle < 180 else 'Waning Moon - release and decrease'
        
        # Moon sign characteristics
        moon_sign_characteristics = {
            0: 'Independent, pioneering, energetic',
            1: 'Stable, practical, sensual',
            2: 'Communicative, versatile, curious',
            3: 'Emotional, nurturing, protective',
            4: 'Creative, confident, dramatic',
            5: 'Analytical, perfectionist, helpful',
            6: 'Harmonious, diplomatic, aesthetic',
            7: 'Intense, transformative, mysterious',
            8: 'Adventurous, philosophical, optimistic',
            9: 'Ambitious, disciplined, responsible',
            10: 'Innovative, humanitarian, independent',
            11: 'Intuitive, compassionate, dreamy'
        }
        
        # Lunar yogas (simplified)
        lunar_yogas = []
        if illumination_percentage > 95:
            lunar_yogas.append({
                'name': 'Purnima Yoga',
                'description': 'Full Moon energy',
                'effect': 'Heightened emotions and spiritual energy'
            })
        elif illumination_percentage < 5:
            lunar_yogas.append({
                'name': 'Amavasya Yoga',
                'description': 'New Moon energy',
                'effect': 'New beginnings and introspection'
            })
        
        return {
            'phase_name': phase_name,
            'illumination_percentage': round(illumination_percentage, 1),
            'moon_age': round(moon_age, 1),
            'distance_km': distance_km,
            'moon_sign': moon_sign,
            'moon_degree': round(moon_degree, 2),
            'sign_symbol': sign_names[moon_sign],
            'sign_lord': sign_lords[moon_sign],
            'element': elements[moon_sign],
            'quality': qualities[moon_sign],
            'lunar_month_name': lunar_month_name,
            'paksha_significance': paksha_significance,
            'moon_sign_characteristics': moon_sign_characteristics[moon_sign],
            'sign_strength': 'Strong' if moon_sign in [1, 3] else 'Medium',
            'nakshatra_strength': 'Medium',
            'strength_effects': 'Balanced emotional state',
            'lunar_yogas': lunar_yogas
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-inauspicious-times")
async def calculate_inauspicious_times(request: InauspiciousTimesRequest):
    try:
        # Use professional MonthlyPanchangCalculator instead of amateur calculations
        daily_panchang = monthly_panchang_calc.calculate_daily_panchang(
            request.date,
            request.latitude,
            request.longitude,
            "UTC+5:30"  # Default timezone for inauspicious times
        )
        
        special_times = daily_panchang.get('special_times', {})
        
        # Convert format to match frontend expectations
        dur_muhurta = []
        for dm in special_times.get('dur_muhurtam', []):
            if dm.get('start') and dm.get('end'):
                # Convert 12-hour format to ISO datetime for frontend
                start_dt = datetime.strptime(f"{request.date} {dm.get('start')}", '%Y-%m-%d %I:%M %p')
                end_dt = datetime.strptime(f"{request.date} {dm.get('end')}", '%Y-%m-%d %I:%M %p')
                dur_muhurta.append({
                    'start_time': start_dt.isoformat(),
                    'end_time': end_dt.isoformat(),
                    'avoid_activities': ['General activities', 'New ventures', 'Important decisions']
                })
        
        varjyam = []
        varjyam_data = special_times.get('varjyam', {})
        if varjyam_data.get('start') and varjyam_data.get('end'):
            start_dt = datetime.strptime(f"{request.date} {varjyam_data.get('start')}", '%Y-%m-%d %I:%M %p')
            end_dt = datetime.strptime(f"{request.date} {varjyam_data.get('end')}", '%Y-%m-%d %I:%M %p')
            varjyam.append({
                'start_time': start_dt.isoformat(),
                'end_time': end_dt.isoformat(),
                'specific_activities': ['Specific ceremonies', 'Religious activities', 'Auspicious events']
            })
        
        return {
            'dur_muhurta': dur_muhurta,
            'varjyam': varjyam,
            'sunrise_time': daily_panchang['sunrise_sunset']['sunrise'],
            'weekday': datetime.strptime(request.date, '%Y-%m-%d').weekday()
        }
        
    except Exception as e:
        print(f"[ERROR] Inauspicious times calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-rahu-kaal")
async def calculate_rahu_kaal(request: SunriseSunsetRequest):
    try:
        # Use professional MonthlyPanchangCalculator instead of amateur math
        daily_panchang = monthly_panchang_calc.calculate_daily_panchang(
            request.date,
            request.latitude,
            request.longitude,
            "UTC+5:30"  # Default timezone for Rahu Kaal
        )
        
        special_times = daily_panchang.get('special_times', {})
        rahu_kalam = special_times.get('rahu_kalam', {})
        
        return {
            'rahu_kaal_start': rahu_kalam.get('start'),
            'rahu_kaal_end': rahu_kalam.get('end'),
            'duration_minutes': int(daily_panchang['sunrise_sunset']['day_duration'] * 60 / 8) if daily_panchang['sunrise_sunset']['day_duration'] else 90,
            'avoid_activities': ['New ventures', 'Important meetings', 'Travel', 'Ceremonies']
        }
        
    except Exception as e:
        print(f"[ERROR] Rahu Kaal calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/festivals/{date}")
async def get_festivals(date: str):
    try:
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/choghadiya")
async def get_choghadiya(
    date: str,
    latitude: float,
    longitude: float,
    timezone: str
):
    """Get Choghadiya periods using Swiss Ephemeris calculations"""
    try:
        print(f"[DEBUG] Choghadiya request: date={date}, lat={latitude}, lon={longitude}, tz={timezone}")
        result = panchang_calc.calculate_choghadiya(date, float(latitude), float(longitude), timezone)
        print(f"[DEBUG] Choghadiya result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] Choghadiya calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hora")
async def get_hora(
    date: str,
    latitude: float,
    longitude: float,
    timezone: str
):
    """Get Hora (planetary hours) using Swiss Ephemeris calculations"""
    try:
        print(f"[DEBUG] Hora request: date={date}, lat={latitude}, lon={longitude}, tz={timezone}")
        result = panchang_calc.calculate_hora(date, float(latitude), float(longitude), timezone)
        print(f"[DEBUG] Hora result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        if isinstance(result, dict) and 'error' in result:
            print(f"[ERROR] Hora calculation returned error: {result['error']}")
        return result
    except Exception as e:
        print(f"[ERROR] Hora calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/special-muhurtas")
async def get_special_muhurtas(
    date: str,
    latitude: float,
    longitude: float,
    timezone: str
):
    """Get special muhurtas like Abhijit, Brahma Muhurta using Swiss Ephemeris calculations"""
    try:
        print(f"[DEBUG] Special muhurtas request: date={date}, lat={latitude}, lon={longitude}, tz={timezone}")
        result = panchang_calc.calculate_special_muhurtas(date, float(latitude), float(longitude), timezone)
        print(f"[DEBUG] Special muhurtas raw result: {result}")
        
        # Format the result to match frontend expectations
        if 'error' not in result:
            muhurtas = []
            if 'brahma_muhurta' in result:
                muhurtas.append({
                    'name': 'Brahma Muhurta',
                    'start_time': result['brahma_muhurta']['start_time'],
                    'end_time': result['brahma_muhurta']['end_time'],
                    'purpose': result['brahma_muhurta']['description']
                })
            if 'abhijit_muhurta' in result:
                muhurtas.append({
                    'name': 'Abhijit Muhurta',
                    'start_time': result['abhijit_muhurta']['start_time'],
                    'end_time': result['abhijit_muhurta']['end_time'],
                    'purpose': result['abhijit_muhurta']['description']
                })
            
            formatted_result = {'muhurtas': muhurtas}
            print(f"[DEBUG] Special muhurtas formatted result: {formatted_result}")
            return formatted_result
        
        return result
    except Exception as e:
        print(f"[ERROR] Special muhurtas calculation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/monthly")
async def get_monthly_panchang(
    year: int,
    month: int,
    latitude: float,
    longitude: float,
    timezone: str = "Asia/Kolkata"
):
    """Get complete monthly panchang with daily details"""
    try:
        result = monthly_panchang_calc.calculate_monthly_panchang(
            year, month, float(latitude), float(longitude), timezone
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/daily-detailed")
async def get_daily_detailed_panchang(
    date: str,
    latitude: float,
    longitude: float,
    timezone: str
):
    """Get detailed panchang for a single day with all elements and timezone support"""
    try:
        result = monthly_panchang_calc.calculate_daily_panchang(
            date, float(latitude), float(longitude), timezone
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))