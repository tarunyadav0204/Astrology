"""
Kota Chakra API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sqlite3
import traceback
from auth import get_current_user
from calculators.kota_chakra_calculator import KotaChakraCalculator
from calculators.chart_calculator import ChartCalculator
from encryption_utils import EncryptionManager

try:
    encryptor = EncryptionManager()
except ValueError as e:
    print(f"WARNING: Encryption not configured: {e}")
    encryptor = None

router = APIRouter(prefix="/kota-chakra", tags=["kota_chakra"])

class KotaChakraRequest(BaseModel):
    birth_chart_id: int
    date: Optional[str] = None

class PlanetDetailsRequest(BaseModel):
    birth_chart_id: int
    planet: str
    date: Optional[str] = None

@router.post("/calculate")
async def calculate_kota_chakra(request: KotaChakraRequest, current_user = Depends(get_current_user)):
    conn = None
    try:
        # Validate request
        if not request.birth_chart_id:
            raise HTTPException(status_code=400, detail="Birth chart ID is required")
        
        # Database connection
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, date, time, place, 
                   latitude, longitude, timezone, gender
            FROM birth_charts 
            WHERE id = ? AND userid = ?
        """, (request.birth_chart_id, current_user.userid))
        
        chart_row = cursor.fetchone()
        
        if not chart_row:
            raise HTTPException(status_code=404, detail="Birth chart not found or access denied")
        
        # Validate birth data
        if not all([chart_row[1], chart_row[2], chart_row[4], chart_row[5]]):
            raise HTTPException(status_code=400, detail="Incomplete birth data")
        
        # Decrypt birth data if encryption is enabled
        if encryptor:
            birth_data = {
                'date': encryptor.decrypt(chart_row[1]),
                'time': encryptor.decrypt(chart_row[2]),
                'latitude': float(encryptor.decrypt(str(chart_row[4]))),
                'longitude': float(encryptor.decrypt(str(chart_row[5]))),
                'timezone': chart_row[6] or 'UTC'
            }
        else:
            birth_data = {
                'date': chart_row[1],
                'time': chart_row[2],
                'latitude': float(chart_row[4]),
                'longitude': float(chart_row[5]),
                'timezone': chart_row[6] or 'UTC'
            }
        
        # Calculate chart using proper pattern from main.py
        from calculators.chart_calculator import ChartCalculator
        
        # Create a temporary birth data object
        class BirthData:
            def __init__(self, date, time, latitude, longitude, timezone):
                self.date = date
                self.time = time
                self.latitude = latitude
                self.longitude = longitude
                self.timezone = timezone
        
        # Calculate birth chart
        birth_obj = BirthData(
            birth_data['date'], birth_data['time'],
            birth_data['latitude'], birth_data['longitude'],
            birth_data['timezone']
        )
        
        chart_calc = ChartCalculator({})
        birth_chart = chart_calc.calculate_chart(birth_obj)
        
        if not birth_chart:
            raise HTTPException(status_code=500, detail="Failed to calculate birth chart")
        
        # If date is provided, combine with transits for that date
        if request.date:
            try:
                # Calculate transits for selected date
                transit_obj = BirthData(
                    request.date, '12:00',  # Use noon for transit
                    birth_data['latitude'], birth_data['longitude'],
                    birth_data['timezone']
                )
                
                transit_chart = chart_calc.calculate_chart(transit_obj)
                
                if transit_chart and 'planets' in transit_chart:
                    # Combine birth chart with current transits
                    combined_chart = birth_chart.copy()
                    for planet in ['Saturn', 'Mars', 'Rahu', 'Ketu', 'Jupiter', 'Venus']:
                        if planet in transit_chart['planets']:
                            combined_chart['planets'][planet] = transit_chart['planets'][planet]
                    chart_data = combined_chart
                else:
                    chart_data = birth_chart
            except Exception as transit_error:
                print(f"Transit calculation error: {transit_error}")
                chart_data = birth_chart
        else:
            chart_data = birth_chart
        
        # Calculate Kota Chakra
        kota_calc = KotaChakraCalculator(chart_data)
        kota_result = kota_calc.calculate()
        
        if not kota_result:
            raise HTTPException(status_code=500, detail="Failed to calculate Kota Chakra")
        
        return {
            "success": True,
            "kota_chakra": kota_result
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        print(f"ValueError in kota-chakra/calculate: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except sqlite3.Error as e:
        print(f"Database error in kota-chakra/calculate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in kota-chakra/calculate: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.post("/periods")
async def get_yearly_periods(request: KotaChakraRequest, current_user = Depends(get_current_user)):
    conn = None
    try:
        # Validate request
        if not request.birth_chart_id:
            raise HTTPException(status_code=400, detail="Birth chart ID is required")
        
        # Database connection
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT date, time, latitude, longitude, timezone
            FROM birth_charts 
            WHERE id = ? AND userid = ?
        """, (request.birth_chart_id, current_user.userid))
        
        chart_row = cursor.fetchone()
        
        if not chart_row:
            raise HTTPException(status_code=404, detail="Birth chart not found or access denied")
        
        # Validate birth data
        if not all([chart_row[0], chart_row[1], chart_row[2], chart_row[3]]):
            raise HTTPException(status_code=400, detail="Incomplete birth data")
        
        # Decrypt birth data if encryption is enabled
        if encryptor:
            birth_data = {
                'date': encryptor.decrypt(chart_row[0]),
                'time': encryptor.decrypt(chart_row[1]),
                'latitude': float(encryptor.decrypt(str(chart_row[2]))),
                'longitude': float(encryptor.decrypt(str(chart_row[3]))),
                'timezone': chart_row[4] or 'UTC'
            }
        else:
            birth_data = {
                'date': chart_row[0],
                'time': chart_row[1],
                'latitude': float(chart_row[2]),
                'longitude': float(chart_row[3]),
                'timezone': chart_row[4] or 'UTC'
            }
        
        # Validate and parse date
        try:
            year = datetime.strptime(request.date, "%Y-%m-%d").year if request.date else datetime.now().year
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        good_periods = []
        vulnerable_periods = []
        
        for month in range(1, 13):
            try:
                # Calculate transits for the 15th of each month
                from datetime import date
                transit_date = date(year, month, 15)
                
                # Create birth data object for chart calculation
                class BirthData:
                    def __init__(self, date, time, latitude, longitude, timezone):
                        self.date = date
                        self.time = time
                        self.latitude = latitude
                        self.longitude = longitude
                        self.timezone = timezone
                
                birth_obj = BirthData(
                    birth_data['date'], birth_data['time'],
                    birth_data['latitude'], birth_data['longitude'],
                    birth_data['timezone']
                )
                
                # Calculate birth chart
                chart_calc = ChartCalculator({})
                birth_chart = chart_calc.calculate_chart(birth_obj)
                
                if not birth_chart:
                    continue
                
                # Calculate transits for this month using ChartCalculator
                # Create a temporary date for transit calculation
                transit_birth_obj = BirthData(
                    transit_date.strftime('%Y-%m-%d'), '12:00',  # Use noon for transit
                    birth_data['latitude'], birth_data['longitude'],
                    birth_data['timezone']
                )
                
                # Calculate transit chart
                transit_chart_calc = ChartCalculator({})
                transit_chart = transit_chart_calc.calculate_chart(transit_birth_obj)
                
                # Combine birth chart with transit positions for Kota Chakra analysis
                combined_chart = birth_chart.copy()
                if transit_chart and 'planets' in transit_chart:
                    # Update malefic positions with current transits
                    for planet in ['Saturn', 'Mars', 'Rahu', 'Ketu']:
                        if planet in transit_chart['planets']:
                            combined_chart['planets'][planet] = transit_chart['planets'][planet]
                
                kota_calc = KotaChakraCalculator(combined_chart)
                kota_result = kota_calc.calculate()
                
                if not kota_result:
                    continue
                
                vulnerability_score = kota_result.get('protection_score', {}).get('vulnerability_score', 0)
                
                period_data = {
                    "month": month,
                    "month_name": datetime(year, month, 1).strftime("%B"),
                    "vulnerability_score": vulnerability_score,
                    "interpretation": kota_result.get('interpretation', '')
                }
                
                if vulnerability_score >= 2:
                    vulnerable_periods.append(period_data)
                elif vulnerability_score == 0:
                    good_periods.append(period_data)
                elif vulnerability_score == 1:
                    # Add caution periods for score 1
                    period_data['period_type'] = 'caution'
                    good_periods.append(period_data)  # Include in good periods with caution flag
                    
            except Exception as calc_error:
                print(f"Error calculating month {month}: {calc_error}")
                continue
        
        return {
            "success": True,
            "year": year,
            "good_periods": good_periods,
            "vulnerable_periods": vulnerable_periods
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in kota-chakra/periods: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
    finally:
        if conn:
            conn.close()

@router.post("/planet-details")
async def get_planet_details(request: PlanetDetailsRequest, current_user = Depends(get_current_user)):
    conn = None
    try:
        if not request.birth_chart_id or not request.planet:
            raise HTTPException(status_code=400, detail="Birth chart ID and planet are required")
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, date, time, place, 
                   latitude, longitude, timezone, gender
            FROM birth_charts 
            WHERE id = ? AND userid = ?
        """, (request.birth_chart_id, current_user.userid))
        
        chart_row = cursor.fetchone()
        
        if not chart_row:
            raise HTTPException(status_code=404, detail="Birth chart not found or access denied")
        
        if not all([chart_row[1], chart_row[2], chart_row[4], chart_row[5]]):
            raise HTTPException(status_code=400, detail="Incomplete birth data")
        
        # Decrypt birth data
        if encryptor:
            birth_data = {
                'date': encryptor.decrypt(chart_row[1]),
                'time': encryptor.decrypt(chart_row[2]),
                'latitude': float(encryptor.decrypt(str(chart_row[4]))),
                'longitude': float(encryptor.decrypt(str(chart_row[5]))),
                'timezone': chart_row[6] or 'UTC'
            }
        else:
            birth_data = {
                'date': chart_row[1],
                'time': chart_row[2],
                'latitude': float(chart_row[4]),
                'longitude': float(chart_row[5]),
                'timezone': chart_row[6] or 'UTC'
            }
        
        class BirthData:
            def __init__(self, date, time, latitude, longitude, timezone):
                self.date = date
                self.time = time
                self.latitude = latitude
                self.longitude = longitude
                self.timezone = timezone
        
        birth_obj = BirthData(
            birth_data['date'], birth_data['time'],
            birth_data['latitude'], birth_data['longitude'],
            birth_data['timezone']
        )
        
        chart_calc = ChartCalculator({})
        birth_chart = chart_calc.calculate_chart(birth_obj)
        
        if not birth_chart:
            raise HTTPException(status_code=500, detail="Failed to calculate birth chart")
        
        if request.date:
            try:
                transit_obj = BirthData(
                    request.date, '12:00',
                    birth_data['latitude'], birth_data['longitude'],
                    birth_data['timezone']
                )
                
                transit_chart = chart_calc.calculate_chart(transit_obj)
                
                if transit_chart and 'planets' in transit_chart:
                    combined_chart = birth_chart.copy()
                    for planet in ['Saturn', 'Mars', 'Rahu', 'Ketu', 'Jupiter', 'Venus']:
                        if planet in transit_chart['planets']:
                            combined_chart['planets'][planet] = transit_chart['planets'][planet]
                    chart_data = combined_chart
                else:
                    chart_data = birth_chart
            except Exception:
                chart_data = birth_chart
        else:
            chart_data = birth_chart
        
        kota_calc = KotaChakraCalculator(chart_data)
        kota_result = kota_calc.calculate()
        
        if not kota_result:
            raise HTTPException(status_code=500, detail="Failed to calculate Kota Chakra")
        
        planet_details = kota_calc.get_planet_details(request.planet, kota_result)
        
        return {
            "success": True,
            "planet_details": planet_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in planet-details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
    finally:
        if conn:
            conn.close()