from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import swisseph as swe
import math
from .panchang_calculator import PanchangCalculator
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
        birth_data = request.birth_data
        panchang_data = panchang_calc.calculate_panchang(
            request.transit_date,
            birth_data['latitude'],
            birth_data['longitude'],
            birth_data['timezone']
        )
        return panchang_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-sunrise-sunset")
async def calculate_sunrise_sunset(request: SunriseSunsetRequest):
    try:
        date_obj = datetime.strptime(request.date, '%Y-%m-%d')
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 0.0)
        
        # Calculate sunrise and sunset using calc_ut instead of rise_trans
        sun_data = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
        
        # Approximate sunrise/sunset calculation
        import math
        lat_rad = math.radians(request.latitude)
        sun_decl = math.radians(23.45 * math.sin(math.radians(360 * (284 + date_obj.timetuple().tm_yday) / 365)))
        hour_angle = math.acos(-math.tan(lat_rad) * math.tan(sun_decl))
        sunrise_hour = 12 - hour_angle * 12 / math.pi
        sunset_hour = 12 + hour_angle * 12 / math.pi
        
        sunrise_time = datetime.combine(date_obj.date(), datetime.min.time()) + timedelta(hours=sunrise_hour)
        sunset_time = datetime.combine(date_obj.date(), datetime.min.time()) + timedelta(hours=sunset_hour)
        
        # Moon calculations
        moon_data = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        moonrise_time = sunrise_time + timedelta(hours=1)  # Approximate
        moonset_time = sunset_time + timedelta(hours=1)    # Approximate
        
        if not sunrise_time or not sunset_time:
            raise HTTPException(status_code=500, detail="Could not calculate sunrise/sunset for this location and date")
        
        # Calculate day duration
        day_duration = (sunset_time - sunrise_time).total_seconds() / 3600
        night_duration = 24 - day_duration
        
        # Calculate twilight times (approximate)
        civil_twilight_begin = sunrise_time - timedelta(minutes=30)
        civil_twilight_end = sunset_time + timedelta(minutes=30)
        nautical_twilight_begin = sunrise_time - timedelta(minutes=60)
        nautical_twilight_end = sunset_time + timedelta(minutes=60)
        astronomical_twilight_begin = sunrise_time - timedelta(minutes=90)
        astronomical_twilight_end = sunset_time + timedelta(minutes=90)
        
        # Calculate special muhurtas
        brahma_muhurta_start = sunrise_time - timedelta(hours=2, minutes=24)
        brahma_muhurta_end = sunrise_time - timedelta(minutes=48)
        
        # Abhijit muhurta (midday)
        midday = sunrise_time + timedelta(hours=day_duration/2)
        abhijit_muhurta_start = midday - timedelta(minutes=24)
        abhijit_muhurta_end = midday + timedelta(minutes=24)
        
        # Godhuli muhurta (evening)
        godhuli_muhurta_start = sunset_time - timedelta(minutes=24)
        godhuli_muhurta_end = sunset_time + timedelta(minutes=24)
        
        # Calculate moon phase
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        phase_angle = (moon_pos - sun_pos) % 360
        illumination = (1 - math.cos(math.radians(phase_angle))) / 2 * 100
        
        phase_names = ['New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous',
                      'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent']
        phase_index = int((phase_angle + 22.5) / 45) % 8
        
        return {
            'sunrise': sunrise_time.isoformat() if sunrise_time else None,
            'sunset': sunset_time.isoformat() if sunset_time else None,
            'moonrise': moonrise_time.isoformat() if moonrise_time else None,
            'moonset': moonset_time.isoformat() if moonset_time else None,
            'day_duration': day_duration,
            'night_duration': night_duration,
            'civil_twilight_begin': civil_twilight_begin.isoformat(),
            'civil_twilight_end': civil_twilight_end.isoformat(),
            'nautical_twilight_begin': nautical_twilight_begin.isoformat(),
            'nautical_twilight_end': nautical_twilight_end.isoformat(),
            'astronomical_twilight_begin': astronomical_twilight_begin.isoformat(),
            'astronomical_twilight_end': astronomical_twilight_end.isoformat(),
            'brahma_muhurta_start': brahma_muhurta_start.isoformat(),
            'brahma_muhurta_end': brahma_muhurta_end.isoformat(),
            'abhijit_muhurta_start': abhijit_muhurta_start.isoformat(),
            'abhijit_muhurta_end': abhijit_muhurta_end.isoformat(),
            'godhuli_muhurta_start': godhuli_muhurta_start.isoformat(),
            'godhuli_muhurta_end': godhuli_muhurta_end.isoformat(),
            'moon_phase': phase_names[phase_index],
            'moon_illumination': round(illumination, 1)
        }
        
    except Exception as e:
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
        date_obj = datetime.strptime(request.date, '%Y-%m-%d')
        weekday = date_obj.weekday()  # 0 = Monday, 6 = Sunday
        
        # Convert to Sunday = 0 format
        sunday_weekday = (weekday + 1) % 7
        
        # Calculate sunrise for the location (simplified)
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 0.0)
        # Calculate sunrise using approximate method
        import math
        lat_rad = math.radians(request.latitude)
        sun_decl = math.radians(23.45 * math.sin(math.radians(360 * (284 + date_obj.timetuple().tm_yday) / 365)))
        hour_angle = math.acos(-math.tan(lat_rad) * math.tan(sun_decl))
        sunrise_hour = 12 - hour_angle * 12 / math.pi
        
        sunrise_time = datetime.combine(date_obj.date(), datetime.min.time()) + timedelta(hours=sunrise_hour)
        
        # Dur Muhurta periods (simplified - there are specific calculations for these)
        dur_muhurta = []
        
        if not sunrise_time:
            raise HTTPException(status_code=500, detail="Could not calculate sunrise for this location and date")
            
        # Add some sample dur muhurta periods
        dur_muhurta.append({
            'start_time': (sunrise_time + timedelta(hours=3)).isoformat(),
            'end_time': (sunrise_time + timedelta(hours=3, minutes=48)).isoformat(),
            'avoid_activities': ['Important meetings', 'New ventures', 'Travel']
        })
        
        # Varjyam periods (simplified)
        varjyam = []
        varjyam.append({
            'start_time': (sunrise_time + timedelta(hours=8)).isoformat(),
            'end_time': (sunrise_time + timedelta(hours=8, minutes=24)).isoformat(),
            'specific_activities': ['Marriage ceremonies', 'House warming', 'Vehicle purchase']
        })
        
        return {
            'dur_muhurta': dur_muhurta,
            'varjyam': varjyam,
            'sunrise_time': sunrise_time.isoformat(),
            'weekday': sunday_weekday
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-rahu-kaal")
async def calculate_rahu_kaal(request: SunriseSunsetRequest):
    try:
        date_obj = datetime.strptime(request.date, '%Y-%m-%d')
        weekday = date_obj.weekday()
        
        # Calculate approximate sunrise
        lat_rad = math.radians(request.latitude)
        sun_decl = math.radians(23.45 * math.sin(math.radians(360 * (284 + date_obj.timetuple().tm_yday) / 365)))
        hour_angle = math.acos(-math.tan(lat_rad) * math.tan(sun_decl))
        sunrise_hour = 12 - hour_angle * 12 / math.pi
        sunset_hour = 12 + hour_angle * 12 / math.pi
        
        day_duration = sunset_hour - sunrise_hour
        rahu_duration = day_duration / 8
        
        # Rahu Kaal timing based on weekday
        rahu_periods = [7.5, 1, 6, 4.5, 3, 6, 4.5]  # Sunday to Saturday (in 8th parts)
        rahu_start_period = rahu_periods[weekday]
        
        sunrise_time = datetime.combine(date_obj.date(), datetime.min.time()) + timedelta(hours=sunrise_hour)
        rahu_start = sunrise_time + timedelta(hours=rahu_start_period * rahu_duration)
        rahu_end = rahu_start + timedelta(hours=rahu_duration)
        
        return {
            'rahu_kaal_start': rahu_start.isoformat(),
            'rahu_kaal_end': rahu_end.isoformat(),
            'duration_minutes': int(rahu_duration * 60),
            'avoid_activities': ['New ventures', 'Important meetings', 'Travel', 'Ceremonies']
        }
        
    except Exception as e:
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
    longitude: float
):
    """Get Choghadiya periods using Swiss Ephemeris calculations"""
    try:
        result = panchang_calc.calculate_choghadiya(date, float(latitude), float(longitude))
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hora")
async def get_hora(
    date: str,
    latitude: float,
    longitude: float
):
    """Get Hora (planetary hours) using Swiss Ephemeris calculations"""
    try:
        result = panchang_calc.calculate_hora(date, float(latitude), float(longitude))
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/special-muhurtas")
async def get_special_muhurtas(
    date: str,
    latitude: float,
    longitude: float
):
    """Get special muhurtas like Abhijit, Brahma Muhurta using Swiss Ephemeris calculations"""
    try:
        result = panchang_calc.calculate_special_muhurtas(date, float(latitude), float(longitude))
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/monthly")
async def get_monthly_panchang(
    year: int,
    month: int,
    latitude: float,
    longitude: float
):
    """Get complete monthly panchang with daily details"""
    try:
        result = monthly_panchang_calc.calculate_monthly_panchang(
            year, month, float(latitude), float(longitude)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/daily-detailed")
async def get_daily_detailed_panchang(
    date: str,
    latitude: float,
    longitude: float
):
    """Get detailed panchang for a single day with all elements"""
    try:
        result = monthly_panchang_calc.calculate_daily_panchang(
            date, float(latitude), float(longitude)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))