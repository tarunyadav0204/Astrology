"""Chart calculation routes"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import traceback
import time
from pydantic import BaseModel
from auth import get_current_user, User
from calculators.chart_calculator import ChartCalculator
from calculators.vedic_graha_drishti import attach_graha_drishti_to_chart
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.sniper_points_calculator import SniperPointsCalculator
from calculators.pushkara_calculator import PushkaraCalculator
from calculators.gandanta_calculator import GandantaCalculator
from calculators.yogi_calculator import YogiCalculator
from calculators.indu_lagna_calculator import InduLagnaCalculator
from calculators.jaimini_chart_calculator import JaiminiChartCalculator
from charts.house_insight_service import build_house_insight
from birth_charts.schema import (
    ensure_birth_chart_family_columns,
    normalize_chart_relation,
    relation_defaults,
)
from encryption_utils import EncryptionManager
from db import get_conn, execute

try:
    encryptor = EncryptionManager()
except ValueError as e:
    print(f"WARNING: Encryption not configured: {e}")
    encryptor = None

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    place: str = ""
    gender: str = ""
    relation: str = "other"
    relation_order: Optional[int] = None
    relation_side: str = ""
    relation_label: str = ""
    is_family_member: Optional[bool] = None
    
    @property
    def timezone(self):
        """Auto-detect timezone from coordinates and return as offset string"""
        try:
            from utils.timezone_service import get_timezone_from_coordinates
            return get_timezone_from_coordinates(self.latitude, self.longitude)
        except Exception as e:
            print(f"Timezone detection failed: {e}")
            return "UTC+0"  # UTC default instead of IST


def persist_birth_chart_for_user(userid: int, birth_data: BirthData) -> Tuple[Optional[int], Optional[str]]:
    """
    Insert or reuse a birth_charts row using the same encryption, dedupe, and INSERT logic as
    POST /charts/calculate-chart (without running chart math).

    Stored ``timezone`` always comes from ``birth_data.timezone``, which is derived from
    latitude/longitude on the BirthData model — callers must not rely on a client-supplied timezone.
    """
    if not birth_data.latitude or not birth_data.longitude:
        return None, "Valid coordinates required. Please select location from suggestions."

    try:
        datetime.strptime(birth_data.date, "%Y-%m-%d")
    except ValueError:
        return None, f"Invalid date format. Expected YYYY-MM-DD, got: {birth_data.date}"

    try:
        time_parts = birth_data.time.split(":")
        if len(time_parts) not in [2, 3]:
            raise ValueError("Time must be in HH:MM or HH:MM:SS format")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            raise ValueError("Invalid hour or minute values")
    except (ValueError, IndexError) as e:
        return None, f"Invalid time format. Expected HH:MM or HH:MM:SS, got: {birth_data.time}. ({e})"

    tz_value = birth_data.timezone
    if not tz_value:
        return None, "Could not determine timezone from birth coordinates."

    if encryptor:
        enc_name = encryptor.encrypt(birth_data.name)
        enc_date = encryptor.encrypt(birth_data.date)
        enc_time = encryptor.encrypt(birth_data.time)
        enc_lat = encryptor.encrypt(str(birth_data.latitude))
        enc_lon = encryptor.encrypt(str(birth_data.longitude))
        enc_place = encryptor.encrypt(birth_data.place)
    else:
        enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
        enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place

    from utils.birth_hash import birth_hash_from_parts

    explicit_relation_fields = set(getattr(birth_data, "model_fields_set", None) or getattr(birth_data, "__fields_set__", set()) or set())
    has_explicit_family_metadata = bool(
        explicit_relation_fields.intersection(
            {"relation", "relation_order", "relation_side", "relation_label", "is_family_member"}
        )
    )

    relation, is_family_member = relation_defaults(
        normalize_chart_relation(birth_data.relation),
        birth_data.is_family_member,
    )
    relation_side = str(birth_data.relation_side or "").strip().lower() or None
    relation_label = str(birth_data.relation_label or "").strip() or None

    chart_birth_hash = birth_hash_from_parts(
        birth_data.date, birth_data.time, birth_data.latitude, birth_data.longitude
    )

    new_chart_id: Optional[int] = None
    try:
        with get_conn() as conn:
            ensure_birth_chart_family_columns(conn)
            cur = execute(
                conn,
                """
                SELECT id
                FROM birth_charts
                WHERE userid = %s AND name = %s AND date = %s AND time = %s AND place = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (userid, enc_name, enc_date, enc_time, enc_place),
            )
            dup = cur.fetchone()
            if dup:
                new_chart_id = dup[0]
                if has_explicit_family_metadata:
                    if relation == "self":
                        execute(
                            conn,
                            "UPDATE birth_charts SET relation = 'other', is_family_member = FALSE WHERE userid = %s AND relation = 'self' AND id != %s",
                            (userid, new_chart_id),
                        )
                    execute(
                        conn,
                        """
                        UPDATE birth_charts
                        SET relation=%s, relation_order=%s, relation_side=%s, relation_label=%s, is_family_member=%s
                        WHERE id = %s
                        """,
                        (
                            relation,
                            birth_data.relation_order,
                            relation_side,
                            relation_label,
                            is_family_member,
                            new_chart_id,
                        ),
                    )
                if chart_birth_hash:
                    execute(
                        conn,
                        "UPDATE birth_charts SET birth_hash = COALESCE(birth_hash, %s) WHERE id = %s",
                        (chart_birth_hash, new_chart_id),
                    )
                    conn.commit()
                print(f"🔍 [CHART_DEBUG] Dedupe: returning existing chart id={new_chart_id} (exact native match)")
            else:
                print(f"🔍 [CHART_DEBUG] About to insert chart for user {userid}:")
                print(f"🔍 [CHART_DEBUG] - Name: {birth_data.name}")
                print(f"🔍 [CHART_DEBUG] - Relation: {relation}")
                if relation == "self":
                    execute(
                        conn,
                        "UPDATE birth_charts SET relation = 'other', is_family_member = FALSE WHERE userid = %s AND relation = 'self'",
                        (userid,),
                    )

                cur = execute(
                    conn,
                    """
                    INSERT INTO birth_charts
                        (userid, name, date, time, latitude, longitude, timezone, place, gender, relation, birth_hash,
                         relation_order, relation_side, relation_label, is_family_member)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        userid,
                        enc_name,
                        enc_date,
                        enc_time,
                        enc_lat,
                        enc_lon,
                        tz_value,
                        enc_place,
                        birth_data.gender,
                        relation,
                        chart_birth_hash,
                        birth_data.relation_order,
                        relation_side,
                        relation_label,
                        is_family_member,
                    ),
                )
                row = cur.fetchone()
                new_chart_id = row[0] if row else None
                print(f"📝 [CHART_DEBUG] Inserted new chart with id: {new_chart_id}")
                conn.commit()

            if new_chart_id is not None:
                cur = execute(
                    conn,
                    "SELECT relation FROM birth_charts WHERE id = %s",
                    (new_chart_id,),
                )
                rel_row = cur.fetchone()
                actual_relation = rel_row[0] if rel_row else None
                print(f"✅ [CHART_DEBUG] Verified inserted relation: {actual_relation}")
    except Exception as dedupe_err:
        print(f"🔍 [CHART_DEBUG] Dedupe/insert check failed: {dedupe_err}")
        return None, f"Failed to save birth chart: {dedupe_err}"

    return new_chart_id, None


router = APIRouter()


class HouseInsightRequest(BaseModel):
    birth_data: Dict[str, Any]
    house_num: int
    chart_id: str = "lagna"
    transit_date: Optional[str] = None

def get_divisional_sign(sign, degree_in_sign, division):
    """Calculate divisional sign using proper Vedic formulas with boundary buffer"""
    EPS = 1e-9  # Prevent 10.0 becoming 9.999
    part = int((degree_in_sign + EPS) / (30.0/division))
    
    if division == 2:  # Hora (D2) - Parashara Hora
        # Odd Signs: 0-15 Sun(Leo), 15-30 Moon(Cancer)
        # Even Signs: 0-15 Moon(Cancer), 15-30 Sun(Leo)
        is_first_half = degree_in_sign < 15
        if sign % 2 == 0:  # Odd Sign (Aries=0)
            return 4 if is_first_half else 3  # Leo(4) else Cancer(3)
        else:  # Even Sign
            return 3 if is_first_half else 4  # Cancer(3) else Leo(4)
    
    elif division == 3:  # Drekkana (D3) - Parashara
        # 0-10: Self, 10-20: 5th, 20-30: 9th
        if part == 0: return sign
        elif part == 1: return (sign + 4) % 12
        else: return (sign + 8) % 12
    
    elif division == 4:  # Chaturthamsa (D4)
        # 1st part: Self, 2nd: 4th, 3rd: 7th, 4th: 10th
        return (sign + (part * 3)) % 12
    
    elif division == 7:  # Saptamsa (D7)
        return (sign + part) % 12 if sign % 2 == 0 else ((sign + 6) + part) % 12
    
    elif division == 9:  # Navamsa (D9)
        # Movable signs (0,3,6,9): Start from same sign
        # Fixed signs (1,4,7,10): Start from 9th sign
        # Dual signs (2,5,8,11): Start from 5th sign
        if sign in [0, 3, 6, 9]:  # Movable signs
            navamsa_start = sign
        elif sign in [1, 4, 7, 10]:  # Fixed signs
            navamsa_start = (sign + 8) % 12  # 9th from sign
        else:  # Dual signs [2, 5, 8, 11]
            navamsa_start = (sign + 4) % 12  # 5th from sign
        return (navamsa_start + part) % 12
    
    elif division == 10:  # Dasamsa (D10)
        return (sign + part) % 12 if sign % 2 == 0 else ((sign + 8) + part) % 12
    
    elif division == 12:  # Dwadasamsa (D12)
        return (sign + part) % 12
    
    elif division == 16:  # Shodasamsa (D16)
        if sign in [0, 3, 6, 9]:  # Movable signs
            d16_start = 0  # Aries
        elif sign in [1, 4, 7, 10]:  # Fixed signs
            d16_start = 4  # Leo
        else:  # Dual signs
            d16_start = 8  # Sagittarius
        return (d16_start + part) % 12
    
    elif division == 20:  # Vimsamsa (D20)
        if sign in [0, 3, 6, 9]:  # Movable signs
            d20_start = 0  # Aries
        elif sign in [1, 4, 7, 10]:  # Fixed signs
            d20_start = 8  # Sagittarius
        else:  # Dual signs
            d20_start = 4  # Leo
        return (d20_start + part) % 12
    
    elif division == 24:  # Chaturvimsamsa (D24)
        start = 4 if sign % 2 == 0 else 3  # Odd: Leo, Even: Cancer
        return (start + part) % 12
    
    elif division == 27:  # Saptavimsamsa (D27)
        if sign in [0, 4, 8]:  # Fire signs
            d27_start = 0  # Aries
        elif sign in [1, 5, 9]:  # Earth signs
            d27_start = 3  # Cancer
        elif sign in [2, 6, 10]:  # Air signs
            d27_start = 6  # Libra
        else:  # Water signs [3, 7, 11]
            d27_start = 9  # Capricorn
        return (d27_start + part) % 12
    
    elif division == 30:  # Trimsamsa (D30)
        # Use degree_in_sign directly for unequal parts
        if sign % 2 == 0:  # Odd signs (Aries=0 is odd)
            if degree_in_sign < 5: return 0    # Aries
            elif degree_in_sign < 10: return 10  # Aquarius
            elif degree_in_sign < 18: return 8   # Sagittarius
            elif degree_in_sign < 25: return 2   # Gemini
            else: return 6                       # Libra
        else:  # Even signs
            if degree_in_sign < 5: return 1      # Taurus
            elif degree_in_sign < 12: return 5   # Virgo
            elif degree_in_sign < 20: return 11  # Pisces
            elif degree_in_sign < 25: return 9   # Capricorn
            else: return 7                       # Scorpio
    
    elif division == 40:  # Khavedamsa (D40)
        # Odd Signs start from Aries(0), Even Signs start from Libra(6)
        start = 0 if sign % 2 == 0 else 6
        return (start + part) % 12
    
    elif division == 45:  # Akshavedamsa (D45)
        if sign in [0, 3, 6, 9]:  # Movable signs
            d45_start = 0  # Aries
        elif sign in [1, 4, 7, 10]:  # Fixed signs
            d45_start = 4  # Leo
        else:  # Dual signs
            d45_start = 8  # Sagittarius
        return (d45_start + part) % 12
    
    elif division == 60:  # Shashtyamsa (D60)
        # Start from the sign itself
        return (sign + part) % 12
    
    else:
        # Default calculation for other divisions
        return (sign + part) % 12

@router.post("/calculate-chart-only")
async def calculate_chart_only(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate basic chart data only"""
    try:
        # Mobile app sends data directly, not wrapped in birth_data
        if 'birth_data' in request:
            birth_data = request.get('birth_data', {})
        else:
            birth_data = request  # Data is at root level

        # Create birth data object - simple class like in main.py backup
        class BirthDataSimple:
            def __init__(self, data):
                self.name = data.get('name', 'Unknown')
                self.date = data.get('date')
                self.time = data.get('time')
                self.latitude = float(data.get('latitude', 0))
                self.longitude = float(data.get('longitude', 0))
                self.timezone = data.get('timezone', '')  # Empty string, not UTC+0
                self.place = data.get('place', '')
                self.gender = data.get('gender', '')
                self.relation = data.get('relation', 'other')
                
            @property
            def timezone_offset(self):
                """Auto-detect timezone from coordinates and return as offset string"""
                try:
                    from utils.timezone_service import get_timezone_from_coordinates
                    return get_timezone_from_coordinates(self.latitude, self.longitude)
                except Exception as e:
                    logger.warning("timezone detection failed in calculate-chart-only: %s", e)
                    return "UTC+0"  # UTC default instead of IST

        birth_obj = BirthDataSimple(birth_data)

        # Calculate chart
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_obj)

        # Return chart data directly (not wrapped in success/chart_data)
        return chart_data

    except Exception as e:
        logger.exception(
            "calculate-chart-only failed for user_id=%s",
            getattr(current_user, "userid", None),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chart-house-insight")
async def chart_house_insight(request: HouseInsightRequest, current_user: User = Depends(get_current_user)):
    """Build a calculator-backed insight payload for a selected house."""
    try:
        if request.house_num < 1 or request.house_num > 12:
            raise HTTPException(status_code=400, detail="house_num must be between 1 and 12")

        return build_house_insight(
            birth_data=request.birth_data,
            house_num=request.house_num,
            chart_id=request.chart_id,
            transit_date=request.transit_date,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ chart_house_insight failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-all-charts")
async def calculate_all_charts(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate all charts including divisional charts"""
    try:
        birth_data = request.get('birth_data', {})
        
        # Create birth data object - simple class like in main.py backup
        class BirthDataSimple:
            def __init__(self, data):
                self.name = data.get('name', 'Unknown')
                self.date = data.get('date')
                self.time = data.get('time')
                self.latitude = float(data.get('latitude', 0))
                self.longitude = float(data.get('longitude', 0))
                self.timezone = data.get('timezone', 'UTC+0')
                self.place = data.get('place', '')
                self.gender = data.get('gender', '')
                self.relation = data.get('relation', 'other')
        
        birth_obj = BirthDataSimple(birth_data)
        
        # Calculate main chart
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_obj)
        
        # Calculate all divisional charts
        divisional_charts = {}
        
        for division in [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
            try:
                div_result = await calculate_divisional_chart({
                    'birth_data': birth_data,
                    'division': division  # Use 'division' not 'division_number'
                }, current_user)
                divisional_charts[f'd{division}'] = div_result['divisional_chart']
            except Exception as e:
                print(f"Error calculating D{division}: {e}")
        
        # Calculate transit chart
        try:
            from datetime import datetime
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%H:%M')
            
            transit_birth_data = birth_data.copy()
            transit_birth_data['date'] = current_date
            transit_birth_data['time'] = current_time
            
            transit_obj = BirthDataSimple(transit_birth_data)
            transit_chart = calculator.calculate_chart(transit_obj)
            divisional_charts['transit'] = transit_chart
        except Exception as e:
            print(f"Error calculating transit chart: {e}")
        
        return {
            "success": True,
            "chart_data": chart_data,
            "divisional_charts": divisional_charts,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/calculate-divisional-chart")
async def calculate_divisional_chart(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate accurate divisional charts using proper Vedic formulas"""
    def get_divisional_sign(sign, degree_in_sign, division):
        """Calculate divisional sign using proper Vedic formulas with boundary buffer"""
        EPS = 1e-9  # Prevent 10.0 becoming 9.999
        part = int((degree_in_sign + EPS) / (30.0/division))
        
        if division == 2:  # Hora (D2) - Parashara Hora
            # Odd Signs: 0-15 Sun(Leo), 15-30 Moon(Cancer)
            # Even Signs: 0-15 Moon(Cancer), 15-30 Sun(Leo)
            is_first_half = degree_in_sign < 15
            if sign % 2 == 0:  # Odd Sign (Aries=0)
                return 4 if is_first_half else 3  # Leo(4) else Cancer(3)
            else:  # Even Sign
                return 3 if is_first_half else 4  # Cancer(3) else Leo(4)
        
        elif division == 3:  # Drekkana (D3) - Parashara
            # 0-10: Self, 10-20: 5th, 20-30: 9th
            if part == 0: return sign
            elif part == 1: return (sign + 4) % 12
            else: return (sign + 8) % 12
        
        elif division == 4:  # Chaturthamsa (D4)
            # 1st part: Self, 2nd: 4th, 3rd: 7th, 4th: 10th
            return (sign + (part * 3)) % 12
        
        elif division == 7:  # Saptamsa (D7) - CORRECTED
            # Traditional rule: Odd signs start from same sign, Even signs start from 7th sign
            if sign % 2 == 0:  # Aries(0), Gemini(2), Leo(4) etc - Odd signs in astrology
                start_sign = sign
            else:  # Taurus(1), Cancer(3), Virgo(5) etc - Even signs in astrology  
                start_sign = (sign + 6) % 12  # 7th sign from current
            return (start_sign + part) % 12
        
        elif division == 9:  # Navamsa (D9)
            # Movable signs (0,3,6,9): Start from same sign
            # Fixed signs (1,4,7,10): Start from 9th sign
            # Dual signs (2,5,8,11): Start from 5th sign
            if sign in [0, 3, 6, 9]:  # Movable signs
                navamsa_start = sign
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                navamsa_start = (sign + 8) % 12  # 9th from sign
            else:  # Dual signs [2, 5, 8, 11]
                navamsa_start = (sign + 4) % 12  # 5th from sign
            return (navamsa_start + part) % 12
        
        elif division == 10:  # Dasamsa (D10)
            return (sign + part) % 12 if sign % 2 == 0 else ((sign + 8) + part) % 12
        
        elif division == 12:  # Dwadasamsa (D12)
            return (sign + part) % 12
        
        elif division == 16:  # Shodasamsa (D16)
            # For movable signs: start from Aries
            # For fixed signs: start from Leo  
            # For dual signs: start from Sagittarius
            if sign in [0, 3, 6, 9]:  # Movable signs (Aries, Cancer, Libra, Capricorn)
                d16_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs (Taurus, Leo, Scorpio, Aquarius)
                d16_start = 4  # Leo
            else:  # Dual signs (Gemini, Virgo, Sagittarius, Pisces)
                d16_start = 8  # Sagittarius
            return (d16_start + part) % 12
        
        elif division == 20:  # Vimsamsa (D20)
            # For movable signs: start from Aries
            # For fixed signs: start from Sagittarius
            # For dual signs: start from Leo
            if sign in [0, 3, 6, 9]:  # Movable signs
                d20_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                d20_start = 8  # Sagittarius
            else:  # Dual signs
                d20_start = 4  # Leo
            return (d20_start + part) % 12
        
        elif division == 24:  # Chaturvimsamsa (D24)
            # Odd: Leo, Even: Cancer
            start = 4 if sign % 2 == 0 else 3
            return (start + part) % 12
        
        elif division == 27:  # Saptavimsamsa (D27)
            # Fire signs (Aries, Leo, Sagittarius): start from Aries
            # Earth signs (Taurus, Virgo, Capricorn): start from Cancer  
            # Air signs (Gemini, Libra, Aquarius): start from Libra
            # Water signs (Cancer, Scorpio, Pisces): start from Capricorn
            if sign in [0, 4, 8]:  # Fire signs
                d27_start = 0  # Aries
            elif sign in [1, 5, 9]:  # Earth signs
                d27_start = 3  # Cancer
            elif sign in [2, 6, 10]:  # Air signs
                d27_start = 6  # Libra
            else:  # Water signs [3, 7, 11]
                d27_start = 9  # Capricorn
            return (d27_start + part) % 12
        
        elif division == 30:  # Trimsamsa (D30)
            # Use degree_in_sign directly for unequal parts
            if sign % 2 == 0:  # Odd signs (Aries=0 is odd)
                if degree_in_sign < 5: return 0    # Aries
                elif degree_in_sign < 10: return 10  # Aquarius
                elif degree_in_sign < 18: return 8   # Sagittarius
                elif degree_in_sign < 25: return 2   # Gemini
                else: return 6                       # Libra
            else:  # Even signs
                if degree_in_sign < 5: return 1      # Taurus
                elif degree_in_sign < 12: return 5   # Virgo
                elif degree_in_sign < 20: return 11  # Pisces
                elif degree_in_sign < 25: return 9   # Capricorn
                else: return 7                       # Scorpio
        
        elif division == 40:  # Khavedamsa (D40)
            # Odd Signs start from Aries(0), Even Signs start from Libra(6)
            start = 0 if sign % 2 == 0 else 6
            return (start + part) % 12
        
        elif division == 45:  # Akshavedamsa (D45)
            # For movable signs: start from Aries
            # For fixed signs: start from Leo
            # For dual signs: start from Sagittarius
            if sign in [0, 3, 6, 9]:  # Movable signs
                d45_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                d45_start = 4  # Leo
            else:  # Dual signs
                d45_start = 8  # Sagittarius
            return (d45_start + part) % 12
        
        elif division == 60:  # Shashtyamsa (D60)
            # Start from the sign itself
            return (sign + part) % 12
        
        else:
            # Default calculation for other divisions
            return (sign + part) % 12
    
    try:
        birth_data = request.get('birth_data', {})
        # Support both 'division' and 'division_number' for backward compatibility
        division_number = request.get('division', request.get('division_number', 9))

        # Create birth data object - simple class like in main.py backup
        class BirthDataSimple:
            def __init__(self, data):
                self.name = data.get('name', 'Unknown')
                self.date = data.get('date')
                self.time = data.get('time')
                self.latitude = float(data.get('latitude', 0))
                self.longitude = float(data.get('longitude', 0))
                self.timezone = data.get('timezone', 'UTC+0')
                self.place = data.get('place', '')
                self.gender = data.get('gender', '')
                self.relation = data.get('relation', 'other')
        
        birth_obj = BirthDataSimple(birth_data)
        
        # Calculate main chart first
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_obj)

        # Calculate divisional chart
        divisional_data = {
            'planets': {},
            'houses': [],
            'ayanamsa': chart_data.get('ayanamsa', 0)
        }
        
        # Calculate divisional ascendant
        asc_sign = int(chart_data['ascendant'] / 30)
        asc_degree = chart_data['ascendant'] % 30
        divisional_asc_sign = get_divisional_sign(asc_sign, asc_degree, division_number)
        
        # Calculate degree within divisional sign - USE RATIO METHOD FOR ALL DIVISIONS
        EPS = 1e-9
        part_size = 30.0 / division_number
        part_index = int((asc_degree + EPS) / part_size)
        degree_within_part = (asc_degree + EPS) - (part_index * part_size)
        scaled_asc_degree = (degree_within_part / part_size) * 30.0
        divisional_data['ascendant'] = divisional_asc_sign * 30 + scaled_asc_degree

        # Calculate divisional houses
        for i in range(12):
            house_sign = (divisional_asc_sign + i) % 12
            divisional_data['houses'].append({
                'longitude': house_sign * 30,
                'sign': house_sign
            })
        
        # Calculate divisional positions for planets
        planets_to_process = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for planet in planets_to_process:
            if planet in chart_data['planets']:
                planet_data = chart_data['planets'][planet]
                
                # For Gulika and Mandi, keep original positions (don't apply divisional transformation)
                if planet in ['Gulika', 'Mandi']:
                    divisional_data['planets'][planet] = {
                        'longitude': planet_data['longitude'],
                        'sign': planet_data['sign'],
                        'degree': planet_data['degree'],
                        'retrograde': planet_data.get('retrograde', False)
                    }
                else:
                    # Regular planetary divisional calculation
                    planet_sign = int(planet_data['longitude'] / 30)
                    planet_degree = planet_data['longitude'] % 30
                    
                    divisional_sign = get_divisional_sign(planet_sign, planet_degree, division_number)
                    
                    # Calculate the actual degree within the divisional sign - USE RATIO METHOD
                    EPS = 1e-9
                    part_size = 30.0 / division_number
                    part_index = int((planet_degree + EPS) / part_size)
                    degree_within_part = (planet_degree + EPS) - (part_index * part_size)
                    actual_degree = (degree_within_part / part_size) * 30.0

                    divisional_longitude = divisional_sign * 30 + actual_degree
                    
                    divisional_data['planets'][planet] = {
                        'longitude': divisional_longitude,
                        'sign': divisional_sign,
                        'degree': actual_degree,
                        'retrograde': planet_data.get('retrograde', False)
                    }

        attach_graha_drishti_to_chart(divisional_data)

        return {
            'divisional_chart': divisional_data,
            'division_number': division_number,
            'chart_name': f'D{division_number}'
        }
        
    except Exception as e:
        logger.exception(
            "divisional chart calculation failed for user_id=%s division=%s",
            getattr(current_user, "userid", None),
            request.get('division', request.get('division_number', 9)) if isinstance(request, dict) else None,
        )
        return {"success": False, "error": str(e)}

@router.post("/calculate-chart")
async def calculate_chart_with_db_save(birth_data: BirthData, node_type: str = 'mean', current_user: User = Depends(get_current_user)):
    try:
        new_chart_id, persist_err = persist_birth_chart_for_user(current_user.userid, birth_data)
        if persist_err or new_chart_id is None:
            detail = persist_err or "Could not save birth chart."
            low = detail.lower()
            if any(
                x in low
                for x in (
                    "invalid",
                    "format",
                    "required",
                    "coordinates",
                    "timezone",
                    "time format",
                    "date format",
                )
            ):
                raise HTTPException(status_code=422, detail=detail)
            raise HTTPException(status_code=500, detail=detail)

        # Calculate and return chart data using new calculators
        from calculators.chart_calculator import ChartCalculator
        from calculators.divisional_chart_calculator import DivisionalChartCalculator
        
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_data, node_type)
        
        # Add divisional charts
        div_calculator = DivisionalChartCalculator(chart_data)
        chart_data['d3_chart'] = div_calculator.calculate_divisional_chart(3)
        chart_data['d9_chart'] = div_calculator.calculate_divisional_chart(9)
        chart_data['d10_chart'] = div_calculator.calculate_divisional_chart(10)
        
        # Add birth_chart_id to response (may be None if insert failed)
        chart_data['birth_chart_id'] = new_chart_id

        return chart_data
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.exception(
            "calculate-chart failed for user_id=%s birth_name=%s",
            getattr(current_user, "userid", None),
            getattr(birth_data, "name", None),
        )
        raise HTTPException(status_code=500, detail=f"Chart calculation failed: {str(e)}")

@router.post("/jaimini-special-lagnas")
async def calculate_jaimini_special_lagnas(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate all Jaimini special lagnas (AL, UL, KL, Swamsa, HL, GL, A7)"""
    try:
        chart_data = request.get('chart_data', {})
        d9_chart = request.get('d9_chart', {})
        atmakaraka = request.get('atmakaraka')
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        if not atmakaraka:
            raise HTTPException(status_code=400, detail="Atmakaraka planet required")
        
        if isinstance(atmakaraka, dict):
            atmakaraka = atmakaraka['planet']
        
        if not d9_chart or not d9_chart.get('planets'):
            from calculators.divisional_chart_calculator import DivisionalChartCalculator
            div_calc = DivisionalChartCalculator(chart_data)
            d9_chart = div_calc.calculate_divisional_chart(9)
        
        calculator = JaiminiPointCalculator(chart_data, d9_chart, atmakaraka)
        jaimini_points = calculator.calculate_jaimini_points()
        
        return {
            "success": True,
            "jaimini_lagnas": jaimini_points
        }
    except Exception as e:
        logger.exception("error calculating jaimini lagnas")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sniper-points")
async def calculate_sniper_points(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate sniper points (Bhrigu Bindu, Kharesh, 64th Navamsa, Mrityu Bhaga)"""
    try:
        d1_chart = request.get('chart_data', {})
        d3_chart = request.get('d3_chart', {})
        d9_chart = request.get('d9_chart', {})
        
        if not d1_chart or not d1_chart.get('planets'):
            raise HTTPException(status_code=400, detail="D1 chart data required")
        
        from calculators.divisional_chart_calculator import DivisionalChartCalculator
        div_calc = DivisionalChartCalculator(d1_chart)
        
        if not d3_chart or not d3_chart.get('planets'):
            d3_chart = div_calc.calculate_divisional_chart(3)
        
        if not d9_chart or not d9_chart.get('planets'):
            d9_chart = div_calc.calculate_divisional_chart(9)
        
        calculator = SniperPointsCalculator(d1_chart, d3_chart, d9_chart)
        sniper_points = calculator.get_all_sniper_points()
        
        return {
            "success": True,
            "sniper_points": sniper_points
        }
    except Exception as e:
        print(f"Error calculating sniper points: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pushkara-analysis")
async def calculate_pushkara_analysis(request: dict, current_user: User = Depends(get_current_user)):
    """Analyze planets for Pushkara Navamsa and Pushkara Bhaga status"""
    try:
        chart_data = request.get('chart_data', {})
        ascendant = chart_data.get('ascendant', 0)
        ascendant_sign = int(ascendant / 30)
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        calculator = PushkaraCalculator()
        pushkara_analysis = calculator.analyze_chart(chart_data, ascendant_sign)
        
        return {
            "success": True,
            "pushkara_analysis": pushkara_analysis
        }
    except Exception as e:
        print(f"Error calculating Pushkara analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gandanta-analysis")
async def calculate_gandanta_analysis(request: dict, current_user: User = Depends(get_current_user)):
    """Analyze chart for Gandanta positions (planets and lagna)"""
    try:
        chart_data = request.get('chart_data', {})
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        calculator = GandantaCalculator(chart_data)
        gandanta_analysis = calculator.calculate_gandanta_analysis()
        
        return {
            "success": True,
            "gandanta_analysis": gandanta_analysis
        }
    except Exception as e:
        print(f"Error calculating Gandanta analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/yogi-points")
async def calculate_yogi_points(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate Yogi, Avayogi, Dagdha Rashi, and Tithi Shunya Rashi points"""
    try:
        birth_data = request.get('birth_data', {})
        
        if not birth_data:
            raise HTTPException(status_code=400, detail="Birth data required")
        
        calculator = YogiCalculator({})
        yogi_points = calculator.calculate_yogi_points(birth_data)
        
        return {
            "success": True,
            "yogi_points": yogi_points
        }
    except HTTPException:
        raise
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid birth date or time: {e}")
    except Exception as e:
        print(f"Error calculating Yogi points: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to calculate Yogi points")

@router.post("/indu-lagna")
async def calculate_indu_lagna(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate Indu Lagna (wealth indicator)"""
    try:
        chart_data = request.get('chart_data', {})
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        calculator = InduLagnaCalculator(chart_data)
        indu_lagna_data = calculator.get_indu_lagna_data()
        
        return {
            "success": True,
            "indu_lagna": indu_lagna_data
        }
    except Exception as e:
        print(f"Error calculating Indu Lagna: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/karkamsa-chart")
async def calculate_karkamsa_chart(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate Karkamsa chart (D9 recast with Atmakaraka's D9 sign as ascendant)"""
    try:
        chart_data = request.get('chart_data', {})
        atmakaraka = request.get('atmakaraka')
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        if not atmakaraka:
            raise HTTPException(status_code=400, detail="Atmakaraka planet required")
        
        if isinstance(atmakaraka, dict):
            atmakaraka = atmakaraka.get('planet')
        
        calculator = JaiminiChartCalculator(chart_data, atmakaraka)
        karkamsa_result = calculator.calculate_karkamsa_chart()
        karkamsa_interpretation = calculator.get_karkamsa_interpretation(karkamsa_result['karkamsa_sign'])
        
        return {
            "success": True,
            "karkamsa": {
                **karkamsa_result,
                "interpretation": karkamsa_interpretation
            }
        }
    except Exception as e:
        print(f"Error calculating Karkamsa chart: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/swamsa-chart")
async def calculate_swamsa_chart(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate Swamsa chart (D12 recast with Atmakaraka's D12 sign as ascendant)"""
    try:
        chart_data = request.get('chart_data', {})
        atmakaraka = request.get('atmakaraka')
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        if not atmakaraka:
            raise HTTPException(status_code=400, detail="Atmakaraka planet required")
        
        if isinstance(atmakaraka, dict):
            atmakaraka = atmakaraka.get('planet')
        
        calculator = JaiminiChartCalculator(chart_data, atmakaraka)
        swamsa_result = calculator.calculate_swamsa_chart()
        swamsa_interpretation = calculator.get_swamsa_interpretation(swamsa_result['swamsa_sign'])
        
        return {
            "success": True,
            "swamsa": {
                **swamsa_result,
                "interpretation": swamsa_interpretation
            }
        }
    except Exception as e:
        print(f"Error calculating Swamsa chart: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
