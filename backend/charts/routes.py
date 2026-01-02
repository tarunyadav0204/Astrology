"""Chart calculation routes"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime
import sqlite3
import traceback
from pydantic import BaseModel
from auth import get_current_user, User
from calculators.chart_calculator import ChartCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from encryption_utils import EncryptionManager

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
    
    @property
    def timezone(self):
        """Auto-detect timezone from coordinates and return as offset string"""
        try:
            from utils.timezone_service import get_timezone_from_coordinates
            return get_timezone_from_coordinates(self.latitude, self.longitude)
        except Exception as e:
            print(f"Timezone detection failed: {e}")
            return "UTC+0"  # UTC default instead of IST

router = APIRouter()

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
        print(f"🔍 Raw request: {request}")
        
        # Mobile app sends data directly, not wrapped in birth_data
        if 'birth_data' in request:
            birth_data = request.get('birth_data', {})
        else:
            birth_data = request  # Data is at root level
        
        print(f"📊 Birth data received: {birth_data}")
        
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
                    detected_tz = get_timezone_from_coordinates(self.latitude, self.longitude)
                    print(f"🌍 Timezone auto-detected for {self.latitude}, {self.longitude}: {detected_tz}")
                    return detected_tz
                except Exception as e:
                    print(f"❌ Timezone detection failed: {e}")
                    return "UTC+0"  # UTC default instead of IST
        
        birth_obj = BirthDataSimple(birth_data)
        print(f"📋 Birth object created - Date: {birth_obj.date}, Time: {birth_obj.time}")
        print(f"🌍 Using timezone: {birth_obj.timezone_offset} for coordinates: {birth_obj.latitude}, {birth_obj.longitude}")
        
        # Calculate chart
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_obj)
        
        # print(f"📊 Chart calculated - Ascendant: {chart_data.get('ascendant', 'N/A')}°")
        if 'houses' in chart_data and len(chart_data['houses']) > 0:
            asc_sign = chart_data['houses'][0].get('sign', 'N/A')
            print(f"📊 Ascendant sign: {asc_sign}")
        
        # Return chart data directly (not wrapped in success/chart_data)
        return chart_data
        
    except Exception as e:
        print(f"❌ Chart calculation error: {str(e)}")
        import traceback
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
        divisional_data['ascendant'] = divisional_asc_sign * 30 + 15  # Middle of sign
        
        print(f"DEBUG D{division_number}: Original ASC={chart_data['ascendant']:.2f} (Sign {asc_sign}, {asc_degree:.2f}°) -> Divisional ASC Sign={divisional_asc_sign}")
        
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
                    
                    # Calculate the actual degree within the divisional sign
                    EPS = 1e-9
                    part_size = 30.0 / division_number
                    part_index = int((planet_degree + EPS) / part_size)
                    degree_within_part = (planet_degree + EPS) % part_size
                    actual_degree = (degree_within_part / part_size) * 30.0
                    
                    divisional_longitude = divisional_sign * 30 + actual_degree
                    
                    divisional_data['planets'][planet] = {
                        'longitude': divisional_longitude,
                        'sign': divisional_sign,
                        'degree': actual_degree,
                        'retrograde': planet_data.get('retrograde', False)
                    }
        
        return {
            'divisional_chart': divisional_data,
            'division_number': division_number,
            'chart_name': f'D{division_number}'
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/calculate-chart")
async def calculate_chart_with_db_save(birth_data: BirthData, node_type: str = 'mean', current_user: User = Depends(get_current_user)):
    try:
        print(f"🔍 Chart calculation request for: {birth_data.name}")
        print(f"📊 Birth data: {birth_data.model_dump()}")
        
        # CRITICAL: Validate coordinates before saving
        if not birth_data.latitude or not birth_data.longitude:
            print(f"❌ Invalid coordinates: lat={birth_data.latitude}, lon={birth_data.longitude}")
            raise HTTPException(status_code=422, detail="Valid coordinates required. Please select location from suggestions.")
        
        # Validate date format
        try:
            datetime.strptime(birth_data.date, '%Y-%m-%d')
        except ValueError as e:
            print(f"❌ Invalid date format: {birth_data.date}, error: {e}")
            raise HTTPException(status_code=422, detail=f"Invalid date format. Expected YYYY-MM-DD, got: {birth_data.date}")
        
        # Validate time format
        try:
            time_parts = birth_data.time.split(':')
            if len(time_parts) not in [2, 3]:
                raise ValueError("Time must be in HH:MM or HH:MM:SS format")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError("Invalid hour or minute values")
        except (ValueError, IndexError) as e:
            print(f"❌ Invalid time format: {birth_data.time}, error: {e}")
            raise HTTPException(status_code=422, detail=f"Invalid time format. Expected HH:MM or HH:MM:SS, got: {birth_data.time}")
        
        # Validate timezone
        if not birth_data.timezone:
            print(f"❌ Missing timezone")
            raise HTTPException(status_code=422, detail="Timezone is required")
        
        print(f"✅ Validation passed, proceeding with chart calculation")
        
        # Store birth data in database (update if exists for current user only)
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
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

        # Always insert new chart (allow duplicates)
        cursor.execute('''
            INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user.userid, enc_name, enc_date, enc_time, enc_lat, enc_lon, 
            birth_data.timezone, enc_place, birth_data.gender, birth_data.relation or 'other'))
        print(f"📝 Inserted new chart with id: {cursor.lastrowid}")

        conn.commit()
        conn.close()
        
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
        
        print(f"✅ Chart calculation completed successfully using new calculators")
        return chart_data
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        import traceback
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'birth_data': birth_data.model_dump() if birth_data else None
        }
        print(f"❌ Chart calculation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Chart calculation failed: {str(e)}")