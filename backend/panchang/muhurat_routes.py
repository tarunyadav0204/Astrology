from fastapi import APIRouter, HTTPException, Query
from .muhurat_calculator import MuhuratCalculator
from calculators.muhurat_calculator import MuhuratCalculator as PersonalisedMuhuratCalculator
import swisseph as swe
from datetime import datetime, timedelta
from utils.timezone_service import parse_timezone_offset

router = APIRouter()
calculator = MuhuratCalculator()
personalised_calculator = PersonalisedMuhuratCalculator()


def _janma_nakshatra(date_value, time_value, latitude, longitude, timezone):
    """Return the birth Moon Nakshatra used by the mobile Muhurat algorithm."""
    if not date_value or not time_value:
        return None
    try:
        parts = str(time_value).split(':')
        local_hour = float(parts[0]) + float(parts[1] if len(parts) > 1 else 0) / 60
        offset = parse_timezone_offset(timezone, latitude, longitude)
        date_obj = datetime.strptime(str(date_value).split('T')[0], '%Y-%m-%d')
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, local_hour - offset)
        moon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360
        return int(moon / (360 / 27)) + 1
    except Exception:
        return None


def _rich_vehicle_response(date, latitude, longitude, timezone, birth_date=None,
                           birth_time=None, birth_latitude=None, birth_longitude=None,
                           birth_timezone=None):
    """Run the same rule engine as the mobile vehicle planner.

    The public finder has historically returned ``muhurtas`` for one day. Keep
    that response contract while converting the richer engine's Lagna slots.
    """
    user_nak = _janma_nakshatra(
        birth_date, birth_time, birth_latitude if birth_latitude is not None else latitude,
        birth_longitude if birth_longitude is not None else longitude, birth_timezone or timezone,
    )
    birth_context = None
    if birth_date and birth_time:
        birth_context = {
            'date': birth_date,
            'time': birth_time,
            'latitude': birth_latitude if birth_latitude is not None else latitude,
            'longitude': birth_longitude if birth_longitude is not None else longitude,
            'timezone': birth_timezone or timezone,
        }
    selected_day = datetime.strptime(date, '%Y-%m-%d')
    search_start = (selected_day - timedelta(days=30)).strftime('%Y-%m-%d')
    search_end = (selected_day + timedelta(days=30)).strftime('%Y-%m-%d')
    result = personalised_calculator.calculate_vehicle_muhurat(
        search_start, search_end, latitude, longitude, user_nak, timezone, birth_data=birth_context
    )
    # Keep the strict result authoritative.  The relaxed pass is only a
    # labelled fallback for users who must act within the selected period;
    # Panchak remains a hard exclusion in both passes.
    fallback_result = personalised_calculator.calculate_vehicle_muhurat(
        search_start, search_end, latitude, longitude, user_nak, timezone,
        birth_data=birth_context, allow_caution_dates=True,
    )
    all_recommendations = result.get('recommendations', [])
    recommendations = [item for item in all_recommendations if item.get('date') == date]
    nearest_recommendations = sorted(
        [item for item in all_recommendations if item.get('date') != date],
        key=lambda item: abs((datetime.strptime(item['date'], '%Y-%m-%d') - selected_day).days),
    )[:5]
    fallback_recommendations = [item for item in fallback_result.get('recommendations', [])
                                if item.get('fallback') and item.get('date') != date]
    fallback_recommendations = sorted(
        fallback_recommendations,
        key=lambda item: (len(item.get('date_warnings') or []),
                          abs((datetime.strptime(item['date'], '%Y-%m-%d') - selected_day).days)),
    )[:5]
    fallback_selected = next(
        (item for item in fallback_result.get('recommendations', [])
         if item.get('date') == date and item.get('fallback')),
        None,
    )
    selected_rejections = [item for item in result.get('rejected_dates', []) if item.get('date') == date]
    def _slot_cards(recommendation, include_fallback=False):
        cards = []
        for index, slot in enumerate(recommendation.get('slots', []), start=1):
            start_label = slot.get('time')
            try:
                start = datetime.strptime(f'{date} {start_label}', '%Y-%m-%d %I:%M %p')
                end = start + timedelta(hours=1)
                start_time, end_time = start.isoformat(), end.isoformat()
            except Exception:
                start_time = end_time = start_label
            cards.append({
                'muhurta': index,
                'name': f"{slot.get('lagna', 'Auspicious')} Lagna",
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': 60,
                'suitability': 'Usable with caution' if (include_fallback or recommendation.get('fallback')) else 'Auspicious for vehicle purchase',
                'panchak': bool(slot.get('panchak', recommendation.get('panchak', {}).get('is_panchak'))),
                'panchak_warning': slot.get('panchak_warning') or ('Panchak is active during this window; confirm with a qualified priest before using it.' if recommendation.get('panchak', {}).get('is_panchak') else None),
                'panchak_intervals': slot.get('panchak_intervals', recommendation.get('panchak', {}).get('intervals', [])),
                'lagna': slot.get('lagna'),
                'quality': slot.get('quality'),
                'score': slot.get('score'),
                'reasons': slot.get('reasons', []),
                'positives': slot.get('positives', []),
                'cautions': slot.get('cautions', []),
                'score_breakdown': slot.get('score_breakdown', []),
                'rationale': slot.get('rationale'),
                'fallback': include_fallback or bool(recommendation.get('fallback')),
                'date_warnings': recommendation.get('date_warnings', []),
            })
        return cards

    muhurtas = []
    for recommendation in recommendations:
        muhurtas.extend(_slot_cards(recommendation))
    best_available_muhurtas = _slot_cards(fallback_selected, include_fallback=True) if fallback_selected else []
    return {
        'date': date,
        'location': {'latitude': latitude, 'longitude': longitude, 'timezone': timezone},
        'muhurtas': muhurtas,
        'recommendations': recommendations,
        'nearest_recommendations': nearest_recommendations,
        'best_available_recommendations': fallback_recommendations,
        'best_available_selected': fallback_selected,
        'best_available_muhurtas': best_available_muhurtas,
        'best_available_notice': 'These dates have one or more cautions and are shown only for situations where you must proceed. They are not strict recommendations.',
        'rejections': selected_rejections[0].get('reasons', []) if selected_rejections else [],
        'personalised_tara_bala': bool(user_nak),
        'panchak': (recommendations[0].get('panchak') if recommendations else personalised_calculator._panchak_status(date, latitude, longitude, timezone)),
    }

@router.get("/vivah-muhurat")
async def get_vivah_muhurat(date: str, latitude: float, longitude: float):
    """Get marriage muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = calculator.calculate_vivah_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/property-muhurat")
async def get_property_muhurat(date: str, latitude: float, longitude: float):
    """Get property purchase muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = calculator.calculate_property_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vehicle-muhurat")
async def get_vehicle_muhurat(
    date: str, latitude: float, longitude: float,
    birth_date: str | None = Query(default=None), birth_time: str | None = Query(default=None),
    birth_latitude: float | None = Query(default=None), birth_longitude: float | None = Query(default=None),
    birth_timezone: str | None = Query(default=None),
):
    """Get vehicle purchase muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = _rich_vehicle_response(
            date, latitude, longitude, timezone, birth_date, birth_time,
            birth_latitude, birth_longitude, birth_timezone,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/griha-pravesh-muhurat")
async def get_griha_pravesh_muhurat(date: str, latitude: float, longitude: float):
    """Get house warming muhurat for given date and location"""
    try:
        from utils.timezone_service import get_timezone_from_coordinates
        timezone = get_timezone_from_coordinates(latitude, longitude)
        result = calculator.calculate_griha_pravesh_muhurat(date, latitude, longitude, timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
