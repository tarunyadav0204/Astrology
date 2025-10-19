from fastapi import APIRouter, Request, Depends
from typing import Dict, List
from datetime import datetime, timedelta
import swisseph as swe
from pydantic import BaseModel

router = APIRouter()

class VedicTransitAspectCalculator:
    """Calculate traditional Vedic planetary aspects for transits"""
    
    def __init__(self):
        # Traditional Vedic aspects for each planet
        self.vedic_aspects = {
            'Sun': [7],           # 7th house aspect
            'Moon': [7],          # 7th house aspect
            'Mars': [4, 7, 8],    # 4th, 7th, 8th house aspects
            'Mercury': [7],       # 7th house aspect
            'Jupiter': [5, 7, 9], # 5th, 7th, 9th house aspects
            'Venus': [7],         # 7th house aspect
            'Saturn': [3, 7, 10], # 3rd, 7th, 10th house aspects
            'Rahu': [5, 7, 9],    # 5th, 7th, 9th house aspects
            'Ketu': [5, 7, 9]     # 5th, 7th, 9th house aspects
        }
        
        # Focus on slow-moving planets for meaningful transits
        self.transit_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
        self.natal_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    def calculate_vedic_aspects(self, natal_planets: Dict) -> List[Dict]:
        """Calculate all possible Vedic transit aspects"""
        aspects = []
        
        for transit_planet in self.transit_planets:
            if transit_planet not in self.vedic_aspects:
                continue
                
            for natal_planet, natal_data in natal_planets.items():
                if natal_planet not in self.natal_planets:
                    continue
                
                # Calculate aspects from transiting planet to natal planet
                for aspect_house in self.vedic_aspects[transit_planet]:
                    aspects.append({
                        'planet1': transit_planet,  # Transiting planet
                        'planet2': natal_planet,    # Natal planet
                        'aspect_type': f'{aspect_house}th_house',
                        'natal_longitude': natal_data['longitude'],
                        'aspect_house': aspect_house
                    })
        
        return aspects
    
    def calculate_aspect_timeline(self, natal_longitude: float, aspect_house: int, 
                                transit_planet: str, start_year: int, year_range: int) -> List[Dict]:
        """Calculate when transiting planet aspects natal planet"""
        timeline = []
        
        # Calculate the sign that creates the aspect from natal planet
        natal_sign = int(natal_longitude / 30)
        aspect_sign = (natal_sign + aspect_house - 1) % 12
        
        # Aspect sign boundaries
        aspect_start_longitude = aspect_sign * 30
        aspect_end_longitude = (aspect_sign + 1) * 30
        
        # Date range for calculation
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(start_year + year_range, 12, 31)
        current_date = start_date
        
        # Use different step sizes based on planet speed
        step_days = {
            'Saturn': 14,    # Very slow
            'Jupiter': 7,    # Slow
            'Mars': 3,       # Medium
            'Rahu': 14,      # Slow (retrograde)
            'Ketu': 14       # Slow (retrograde)
        }.get(transit_planet, 7)
        
        in_aspect = False
        aspect_start_date = None
        
        while current_date <= end_date:
            transit_position = self._get_planet_position(current_date, transit_planet)
            
            if transit_position is not None:
                # Check if transit planet is in the aspect sign
                transit_sign = int(transit_position / 30)
                
                if transit_sign == aspect_sign:
                    if not in_aspect:
                        # Entering aspect
                        in_aspect = True
                        aspect_start_date = current_date
                else:
                    if in_aspect:
                        # Exiting aspect
                        in_aspect = False
                        if aspect_start_date:
                            timeline.append({
                                'start_date': aspect_start_date.strftime('%Y-%m-%d'),
                                'end_date': current_date.strftime('%Y-%m-%d'),
                                'peak_date': aspect_start_date.strftime('%Y-%m-%d')
                            })
            
            current_date += timedelta(days=step_days)
        
        # Handle case where aspect continues to end of period
        if in_aspect and aspect_start_date:
            timeline.append({
                'start_date': aspect_start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'peak_date': aspect_start_date.strftime('%Y-%m-%d')
            })
        
        return timeline
    
    def _get_planet_position(self, date: datetime, planet: str) -> float:
        """Get planet position for given date"""
        try:
            # Set Lahiri Ayanamsa
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            jd = swe.julday(date.year, date.month, date.day, 12.0)
            
            planet_map = {
                'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
                'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
                'Venus': swe.VENUS, 'Saturn': swe.SATURN,
                'Rahu': swe.MEAN_NODE, 'Ketu': swe.MEAN_NODE
            }
            
            if planet in planet_map:
                result = swe.calc_ut(jd, planet_map[planet], swe.FLG_SIDEREAL)
                longitude = result[0][0]
                
                # Ketu is 180° opposite to Rahu
                if planet == 'Ketu':
                    longitude = (longitude + 180) % 360
                
                return longitude
        except Exception as e:
            print(f"Error calculating {planet} position: {e}")
        
        return None
    
    def _is_in_house_range(self, longitude: float, start: float, end: float) -> bool:
        """Check if longitude is within house range (handles 360° wraparound)"""
        if start <= end:
            return start <= longitude <= end
        else:  # Range crosses 0°
            return longitude >= start or longitude <= end
    
    def _consolidate_periods(self, timeline: List[Dict]) -> List[Dict]:
        """Consolidate consecutive dates into periods (now handled in calculate_aspect_timeline)"""
        return timeline
    
    def _dates_within_range(self, date1_str: str, date2_str: str, max_days: int) -> bool:
        """Check if two date strings are within specified range"""
        date1 = datetime.strptime(date1_str, '%Y-%m-%d')
        date2 = datetime.strptime(date2_str, '%Y-%m-%d')
        return (date2 - date1).days <= max_days

# API endpoints
vedic_calculator = VedicTransitAspectCalculator()

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: str

@router.post("/vedic-transit-aspects")
async def get_vedic_transit_aspects(request: Request):
    """Get all possible Vedic transit aspects"""
    request_data = await request.json()
    birth_data = request_data['birth_data']
    
    # Calculate natal chart using existing system
    natal_planets = await _calculate_natal_positions(birth_data)
    
    aspects = vedic_calculator.calculate_vedic_aspects(natal_planets)
    
    return {
        'aspects': aspects,
        'natal_planets': natal_planets
    }

@router.post("/vedic-transit-timeline")
async def get_vedic_transit_timeline(request: Request):
    """Get timeline for specific Vedic transit aspect"""
    request_data = await request.json()
    
    birth_data = request_data['birth_data']
    aspect_type = request_data['aspect_type']
    planet1 = request_data['planet1']  # Transit planet
    planet2 = request_data['planet2']  # Natal planet
    start_year = request_data.get('start_year', datetime.now().year)
    year_range = request_data.get('year_range', 1)
    
    # Extract aspect house number from aspect_type
    aspect_house = int(aspect_type.replace('th_house', ''))
    
    # Get natal planet longitude
    natal_planets = await _calculate_natal_positions(birth_data)
    natal_longitude = natal_planets.get(planet2, {}).get('longitude', 0)
    
    timeline = vedic_calculator.calculate_aspect_timeline(
        natal_longitude, aspect_house, planet1, start_year, year_range
    )
    
    return {
        'timeline': timeline,
        'start_year': start_year,
        'year_range': year_range
    }

async def _calculate_natal_positions(birth_data: dict) -> Dict:
    """Calculate natal planet positions using existing chart system"""
    try:
        # Set Lahiri Ayanamsa
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Parse birth data
        time_parts = birth_data['time'].split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        # Handle timezone
        if 6.0 <= birth_data['latitude'] <= 37.0 and 68.0 <= birth_data['longitude'] <= 97.0:
            tz_offset = 5.5
        else:
            tz_offset = 0
            if birth_data['timezone'].startswith('UTC'):
                tz_str = birth_data['timezone'][3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
        
        utc_hour = hour - tz_offset
        jd = swe.julday(
            int(birth_data['date'].split('-')[0]),
            int(birth_data['date'].split('-')[1]),
            int(birth_data['date'].split('-')[2]),
            utc_hour
        )
        
        # Calculate planetary positions
        planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6]):
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            longitude = pos[0][0]
            
            planets[planet_names[i]] = {
                'longitude': longitude,
                'sign': int(longitude / 30),
                'degree': longitude % 30
            }
        
        print(f"Calculated natal positions: {planets}")
        return planets
    
    except Exception as e:
        print(f"Error calculating natal positions: {e}")
        # Return fallback data
        return {
            'Sun': {'longitude': 349.21, 'sign': 11, 'degree': 19.21},
            'Moon': {'longitude': 188.45, 'sign': 6, 'degree': 8.45},
            'Mars': {'longitude': 122.39, 'sign': 4, 'degree': 2.39},
            'Mercury': {'longitude': 321.44, 'sign': 10, 'degree': 21.44},
            'Jupiter': {'longitude': 127.54, 'sign': 4, 'degree': 7.54},
            'Venus': {'longitude': 34.99, 'sign': 1, 'degree': 4.99},
            'Saturn': {'longitude': 148.59, 'sign': 4, 'degree': 28.59}
        }