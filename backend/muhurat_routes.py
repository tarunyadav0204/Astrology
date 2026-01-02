from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from calculators.muhurat_calculator import MuhuratCalculator
from auth import get_current_user, User
from credits.credit_service import CreditService
from utils.timezone_service import parse_timezone_offset
import swisseph as swe

router = APIRouter(prefix="/muhurat", tags=["muhurat"])
calculator = MuhuratCalculator()
credit_service = CreditService()

# --- REQUEST MODELS ---
class ChildbirthMuhuratRequest(BaseModel):
    start_date: str
    end_date: str
    delivery_latitude: float
    delivery_longitude: float
    delivery_timezone: Optional[str] = None
    mother_dob: str
    mother_time: str
    mother_lat: float
    mother_lon: float
    mother_timezone: Optional[str] = None

class GeneralMuhuratRequest(BaseModel):
    start_date: str
    end_date: str
    latitude: float
    longitude: float
    timezone: Optional[str] = None
    user_dob: str
    user_time: str
    user_lat: float
    user_lon: float
    user_timezone: Optional[str] = None

# --- HELPER ---
async def _process_muhurat(request, current_user, feature_name, calc_method):
    # 1. Get cost from settings and check credits
    cost = credit_service.get_credit_setting(f'{feature_name}_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    if user_balance < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {cost}.")

    try:
        # 2. Calc User Nakshatra
        # Supports both "user_..." and "mother_..." field names via getattr logic if needed,
        # but here we standardize on the request object structure.
        
        # Determine dob/time fields based on request type
        if hasattr(request, 'mother_dob'):
            dob, time = request.mother_dob, request.mother_time
        else:
            dob, time = request.user_dob, request.user_time

        time_parts = time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        # Get timezone offset using centralized service
        if hasattr(request, 'mother_lat'):
            lat, lon = request.mother_lat, request.mother_lon
            tz = getattr(request, 'mother_timezone', None)
        else:
            lat, lon = request.user_lat, request.user_lon
            tz = getattr(request, 'user_timezone', None)
        
        tz_offset = parse_timezone_offset(tz, lat, lon)
        utc_hour = hour - tz_offset
        
        jd = swe.julday(int(dob.split('-')[0]), int(dob.split('-')[1]), int(dob.split('-')[2]), utc_hour)
        # Set Lahiri Ayanamsa for accurate Vedic calculations
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        user_nak_id = int(moon_pos / (360/27)) + 1

        # 3. Run Calculation
        # Map location fields
        lat = getattr(request, 'delivery_latitude', getattr(request, 'latitude', 0.0))
        lon = getattr(request, 'delivery_longitude', getattr(request, 'longitude', 0.0))
        tz = getattr(request, 'delivery_timezone', getattr(request, 'timezone', None))

        result = calc_method(
            request.start_date,
            request.end_date,
            lat, lon,
            user_nak_id,
            tz
        )
        
        # 4. Only deduct credits if recommendations found
        if result and result.get('recommendations') and len(result['recommendations']) > 0:
            credit_service.spend_credits(current_user.userid, cost, feature_name, f"Planned {request.start_date}")
        
        return {
            "status": "success",
            "user_nakshatra": user_nak_id,
            "data": result,
            "credits_deducted": result and result.get('recommendations') and len(result['recommendations']) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINTS ---

@router.post("/childbirth-planner")
async def get_childbirth_muhurat(request: ChildbirthMuhuratRequest, current_user: User = Depends(get_current_user)):
    return await _process_muhurat(request, current_user, "childbirth_planner", calculator.calculate_childbirth_muhurat)

@router.post("/vehicle-purchase")
async def get_vehicle_muhurat(request: GeneralMuhuratRequest, current_user: User = Depends(get_current_user)):
    return await _process_muhurat(request, current_user, "vehicle_purchase", calculator.calculate_vehicle_muhurat)

@router.post("/griha-pravesh")
async def get_property_muhurat(request: GeneralMuhuratRequest, current_user: User = Depends(get_current_user)):
    return await _process_muhurat(request, current_user, "griha_pravesh", calculator.calculate_griha_pravesh_muhurat)

@router.post("/gold-purchase")
async def get_gold_muhurat(request: GeneralMuhuratRequest, current_user: User = Depends(get_current_user)):
    return await _process_muhurat(request, current_user, "gold_purchase", calculator.calculate_gold_muhurat)

@router.post("/business-opening")
async def get_business_muhurat(request: GeneralMuhuratRequest, current_user: User = Depends(get_current_user)):
    return await _process_muhurat(request, current_user, "business_opening", calculator.calculate_business_muhurat)

