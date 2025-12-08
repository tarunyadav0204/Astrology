from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from calculators.muhurat_calculator import MuhuratCalculator
from auth import get_current_user
from credits.credit_service import CreditService

router = APIRouter(prefix="/muhurat", tags=["muhurat"])
calculator = MuhuratCalculator()
credit_service = CreditService()

class ChildbirthMuhuratRequest(BaseModel):
    # Delivery params
    start_date: str
    end_date: str
    delivery_latitude: float
    delivery_longitude: float
    delivery_timezone: Optional[str] = "UTC+5:30"
    
    # Mother params
    mother_dob: str
    mother_time: str
    mother_lat: float
    mother_lon: float
    mother_timezone: Optional[str] = "UTC+5:30"

@router.get("/childbirth-planner/cost")
async def get_childbirth_planner_cost(current_user = Depends(get_current_user)):
    """Get credit cost for childbirth planner"""
    cost = credit_service.get_credit_setting('childbirth_planner_cost')
    current_credits = credit_service.get_user_credits(current_user.userid)
    
    return {
        "cost": cost,
        "current_credits": current_credits,
        "can_afford": current_credits >= cost
    }

@router.post("/childbirth-planner")
async def get_childbirth_muhurat(request: ChildbirthMuhuratRequest, current_user = Depends(get_current_user)):
    try:
        print(f"🔍 [DEBUG] Childbirth Planner Request:")
        print(f"  Current User: {current_user.userid}")
        print(f"  Mother DOB: {request.mother_dob}")
        print(f"  Mother Time: {request.mother_time}")
        print(f"  Mother Location: {request.mother_lat}, {request.mother_lon}")
        print(f"  Delivery Location: {request.delivery_latitude}, {request.delivery_longitude}")
        print(f"  Date Range: {request.start_date} to {request.end_date}")
        print(f"  Request Object: {request.dict()}")
        print("="*50)
        # Check credits
        cost = credit_service.get_credit_setting('childbirth_planner_cost')
        current_credits = credit_service.get_user_credits(current_user.userid)
        
        if current_credits < cost:
            raise HTTPException(
                status_code=402, 
                detail={
                    "error": "insufficient_credits",
                    "message": f"Insufficient credits. Need {cost} credits, you have {current_credits}.",
                    "required": cost,
                    "available": current_credits
                }
            )
        # Calculate mother's chart to get Moon nakshatra
        import swisseph as swe
        
        # Parse mother's birth data
        time_parts = request.mother_time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        # Handle timezone
        tz_offset = 5.5
        if request.mother_timezone.startswith('UTC'):
            tz_str = request.mother_timezone[3:]
            if tz_str and ':' in tz_str:
                sign = 1 if tz_str[0] == '+' else -1
                parts = tz_str[1:].split(':')
                tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
        
        utc_hour = hour - tz_offset
        jd = swe.julday(
            int(request.mother_dob.split('-')[0]),
            int(request.mother_dob.split('-')[1]),
            int(request.mother_dob.split('-')[2]),
            utc_hour
        )
        
        # Get Moon position
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        mother_nak_id = int(moon_pos / (360/27)) + 1
        
        # Calculate muhurat
        result = calculator.calculate_childbirth_muhurat(
            request.start_date,
            request.end_date,
            request.delivery_latitude,
            request.delivery_longitude,
            mother_nak_id,
            request.delivery_timezone
        )
        
        # Deduct credits after successful calculation
        credit_service.spend_credits(
            current_user.userid, 
            cost, 
            'childbirth_planner',
            f"Childbirth muhurat planning for {request.start_date} to {request.end_date}"
        )
        
        return {
            "status": "success",
            "mother_nakshatra": mother_nak_id,
            "credits_used": cost,
            "remaining_credits": credit_service.get_user_credits(current_user.userid),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))