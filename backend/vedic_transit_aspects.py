from fastapi import APIRouter, Request, Depends
from typing import Dict, List
from datetime import datetime, timedelta
import swisseph as swe
from pydantic import BaseModel

router = APIRouter()

class VedicTransitAspectCalculator:
    """Calculate traditional Vedic planetary aspects for transits"""
    
    def __init__(self):
        # Traditional Vedic aspects for each planet (including conjunction)
        self.vedic_aspects = {
            'Sun': [1, 7],           # Conjunction, 7th house aspect
            'Moon': [1, 7],          # Conjunction, 7th house aspect
            'Mars': [1, 4, 7, 8],    # Conjunction, 4th, 7th, 8th house aspects
            'Mercury': [1, 7],       # Conjunction, 7th house aspect
            'Jupiter': [1, 5, 7, 9], # Conjunction, 5th, 7th, 9th house aspects
            'Venus': [1, 7],         # Conjunction, 7th house aspect
            'Saturn': [1, 3, 7, 10], # Conjunction, 3rd, 7th, 10th house aspects
            'Rahu': [1, 5, 7, 9],    # Conjunction, 5th, 7th, 9th house aspects
            'Ketu': [1, 5, 7, 9]     # Conjunction, 5th, 7th, 9th house aspects
        }
        
        # Focus on slow-moving planets for meaningful transits
        self.transit_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
        self.natal_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    def calculate_vedic_aspects(self, natal_planets: Dict) -> List[Dict]:
        """Calculate valid Vedic transit aspects - only show aspects that exist in natal chart"""
        aspects = []
        
        # First, find all natal aspects
        natal_aspects = self._find_natal_aspects(natal_planets)
        
        print(f"\n=== CREATING TRANSIT ASPECTS ===")
        # Only show transit aspects for planets that aspect each other in natal chart
        for natal_aspect in natal_aspects:
            transit_planet = natal_aspect['planet1']
            natal_planet = natal_aspect['planet2']
            aspect_type = natal_aspect['aspect_type']
            
            if transit_planet in self.transit_planets and natal_planet in self.natal_planets:
                natal_data = natal_planets[natal_planet]
                
                aspect_entry = {
                    'planet1': transit_planet,  # Transiting planet
                    'planet2': natal_planet,    # Natal planet
                    'aspect_type': aspect_type,
                    'natal_longitude': natal_data['longitude'],
                    'natal_house': natal_data.get('house', 1),
                    'aspect_house': int(aspect_type.replace('th_house', '')),
                    'description': f'Transit {transit_planet} re-activating natal {aspect_type} to {natal_planet}'
                }
                
                aspects.append(aspect_entry)
                print(f"Added transit aspect: {transit_planet} -> {natal_planet} ({aspect_type})")
        
        print(f"Total transit aspects created: {len(aspects)}")
        return aspects
    
    def _find_natal_aspects(self, natal_planets: Dict) -> List[Dict]:
        """Find all aspects that exist in the natal chart"""
        natal_aspects = []
        
        print(f"\n=== FINDING NATAL ASPECTS ===")
        print(f"Available planets: {list(natal_planets.keys())}")
        
        for planet1_name, planet1_data in natal_planets.items():
            if planet1_name not in self.transit_planets or not isinstance(planet1_data, dict):
                continue
                
            planet1_house = planet1_data.get('house', 1)
            print(f"\nChecking {planet1_name} in house {planet1_house}:")
            
            for planet2_name, planet2_data in natal_planets.items():
                if (planet2_name not in self.natal_planets or 
                    not isinstance(planet2_data, dict) or 
                    planet1_name == planet2_name):
                    continue
                
                planet2_house = planet2_data.get('house', 1)
                
                # Calculate which house planet2 is FROM planet1's perspective
                house_diff = (planet2_house - planet1_house) % 12
                if house_diff == 0:
                    aspect_number = 1  # Same house = conjunction
                else:
                    aspect_number = house_diff + 1  # House position from aspecting planet
                
                print(f"  -> {planet2_name} (house {planet2_house}): {aspect_number}th position from {planet1_name}")
                
                # Check if planet1 can actually make this aspect
                if planet1_name in self.vedic_aspects:
                    available_aspects = self.vedic_aspects[planet1_name]
                    print(f"     {planet1_name} can make aspects: {available_aspects}")
                    
                    if aspect_number in available_aspects:
                        natal_aspects.append({
                            'planet1': planet1_name,
                            'planet2': planet2_name,
                            'aspect_type': f'{aspect_number}th_house',
                            'house_difference': aspect_number
                        })
                        print(f"     ✓ VALID ASPECT: {planet1_name} {aspect_number}th aspect to {planet2_name}")
                    else:
                        print(f"     ✗ Invalid aspect: {planet1_name} cannot make {aspect_number}th aspect (only has {available_aspects})")
        
        print(f"\nTotal natal aspects found: {len(natal_aspects)}")
        return natal_aspects
    
    def calculate_aspect_timeline(self, natal_longitude: float, aspect_house: int, 
                                transit_planet: str, start_year: int, year_range: int, 
                                required_transit_house: int = None, natal_house: int = None, 
                                ascendant_sign: int = None, natal_planets: Dict = None) -> List[Dict]:
        """Calculate when transiting planet aspects natal planet - validates actual aspects during transit"""
        timeline = []
        
        if natal_house is None or ascendant_sign is None:
            return []  # Can't calculate without house information
        
        print(f"\n=== CALCULATING TIMELINE FOR {transit_planet} {aspect_house}th ASPECT TO {natal_house} ===")
        print(f"Natal target planet in house {natal_house}, need {aspect_house}th aspect from transit {transit_planet}")
        print(f"Ascendant sign: {ascendant_sign}")
        
        # Date range for calculation
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(start_year + year_range, 12, 31)
        current_date = start_date
        
        # Use smaller step for debugging
        step_days = 7  # Weekly steps for better debugging
        
        in_aspect = False
        aspect_start_date = None
        
        while current_date <= end_date:
            transit_position = self._get_planet_position(current_date, transit_planet)
            
            if transit_position is not None:
                # Calculate transit planet's house
                transit_sign = int(transit_position / 30)
                transit_house = ((transit_sign - ascendant_sign) % 12) + 1
                
                # Calculate what aspect transit planet makes to natal planet
                actual_house_diff = (natal_house - transit_house) % 12
                actual_aspect = 1 if actual_house_diff == 0 else actual_house_diff + 1
                
                # STRICT VALIDATION: Only valid if ALL conditions met
                available_aspects = self.vedic_aspects.get(transit_planet, [])
                can_make_this_aspect = actual_aspect in available_aspects
                matches_required = actual_aspect == aspect_house
                
                # Check if this is a valid aspect
                is_valid_aspect = (actual_aspect in available_aspects and actual_aspect == aspect_house)
                
                # Test specific problematic period
                if (transit_planet == 'Mars' and current_date.month == 6 and current_date.year == 2025):
                    print(f"TESTING: {current_date.strftime('%Y-%m-%d')}")
                    print(f"  Transit Mars longitude: {transit_position:.2f}° (sign {transit_sign}, house {transit_house})")
                    print(f"  Natal Sun house: {natal_house}")
                    print(f"  Actual aspect: {actual_aspect}, Required: {aspect_house}, Valid: {is_valid_aspect}")
                    if not is_valid_aspect:
                        print(f"  SHOULD BE REJECTED: Mars can't make {actual_aspect}th aspect (only {available_aspects})")
                
                if is_valid_aspect:
                    if not in_aspect:
                        # Start new aspect period
                        in_aspect = True
                        aspect_start_date = current_date
                else:
                    if in_aspect:
                        # End current aspect period
                        in_aspect = False
                        if aspect_start_date:
                            timeline.append({
                                'start_date': aspect_start_date.strftime('%Y-%m-%d'),
                                'end_date': current_date.strftime('%Y-%m-%d'),
                                'peak_date': aspect_start_date.strftime('%Y-%m-%d')
                            })
                            aspect_start_date = None
            else:
                # No planet position, end any current aspect
                if in_aspect:
                    in_aspect = False
                    if aspect_start_date:
                        timeline.append({
                            'start_date': aspect_start_date.strftime('%Y-%m-%d'),
                            'end_date': current_date.strftime('%Y-%m-%d'),
                            'peak_date': aspect_start_date.strftime('%Y-%m-%d')
                        })
                        aspect_start_date = None
            
            current_date += timedelta(days=step_days)
        
        # Handle case where aspect continues to end of period
        if in_aspect and aspect_start_date:
            timeline.append({
                'start_date': aspect_start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'peak_date': aspect_start_date.strftime('%Y-%m-%d')
            })
        
        # Final check: if Mars timeline has any periods, verify they're all valid
        if transit_planet == 'Mars' and len(timeline) > 0:
            print(f"WARNING: Mars timeline has {len(timeline)} periods - these should all be valid 8th aspects only")
            for period in timeline:
                print(f"  Period: {period['start_date']} to {period['end_date']}")
        
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
    
    # Get natal planet information
    natal_planets = await _calculate_natal_positions(birth_data)
    natal_planet_data = natal_planets.get(planet2, {})
    natal_longitude = natal_planet_data.get('longitude', 0)
    natal_house = natal_planet_data.get('house', 1)
    ascendant_sign = natal_planets.get('ascendant_sign', 0)
    
    # Get the required transit house from the aspect data if available
    required_transit_house = request_data.get('required_transit_house')
    
    print(f"\n=== API REQUEST DEBUG ===")
    print(f"Requested: Transit {planet1} -> Natal {planet2} ({aspect_type})")
    print(f"Natal {planet1} in house: {natal_planets.get(planet1, {}).get('house', 'unknown')}")
    print(f"Natal {planet2} in house: {natal_house}")
    print(f"Aspect house number: {aspect_house}")
    
    timeline = vedic_calculator.calculate_aspect_timeline(
        natal_longitude, aspect_house, planet1, start_year, year_range, 
        required_transit_house, natal_house, ascendant_sign, natal_planets
    )
    
    print(f"Returning timeline with {len(timeline)} periods for {planet1} -> {planet2}")
    
    return {
        'timeline': timeline,
        'start_year': start_year,
        'year_range': year_range
    }

@router.post("/dasha-timeline")
async def get_dasha_timeline(request: Request):
    """Get pre-computed dasha timeline for efficient filtering"""
    request_data = await request.json()
    birth_data = request_data['birth_data']
    start_year = request_data.get('start_year', 2020)
    end_year = request_data.get('end_year', 2030)
    
    try:
        dasha_timeline = []
        
        # Calculate dashas every 3 days for better granularity
        current_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        while current_date <= end_date:
            date = current_date
            
            # Use existing dasha calculation
            from shared.dasha_calculator import DashaCalculator
            calculator = DashaCalculator()
            
            # Convert birth_data to expected format
            birth_dict = {
                'name': birth_data['name'],
                'date': birth_data['date'],
                'time': birth_data['time'],
                'latitude': birth_data['latitude'],
                'longitude': birth_data['longitude'],
                'timezone': birth_data['timezone']
            }
            
            dasha_data = calculator.calculate_dashas_for_date(date, birth_dict)
            
            dasha_timeline.append({
                'date': date.isoformat(),
                'mahadasha': dasha_data.get('mahadasha', {}).get('planet', ''),
                'antardasha': dasha_data.get('antardasha', {}).get('planet', ''),
                'pratyantardasha': dasha_data.get('pratyantardasha', {}).get('planet', ''),
                'sookshmadasha': dasha_data.get('sookshma', {}).get('planet', ''),
                'pranadasha': dasha_data.get('prana', {}).get('planet', '')
            })
            
            current_date += timedelta(days=3)
        
        return {
            'dasha_timeline': dasha_timeline,
            'start_year': start_year,
            'end_year': end_year
        }
    
    except Exception as e:
        print(f"Error calculating dasha timeline: {e}")
        return {'dasha_timeline': [], 'error': str(e)}

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
        
        # Calculate ascendant first
        houses_data = swe.houses(jd, birth_data['latitude'], birth_data['longitude'], b'P')
        ayanamsa = swe.get_ayanamsa_ut(jd)
        ascendant_tropical = houses_data[1][0]
        ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
        ascendant_sign = int(ascendant_sidereal / 30)
        
        # Calculate planetary positions
        planets = {
            'ascendant_sign': ascendant_sign,
            'ascendant_longitude': ascendant_sidereal
        }
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6]):
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            longitude = pos[0][0]
            planet_sign = int(longitude / 30)
            house_number = ((planet_sign - ascendant_sign) % 12) + 1
            
            planets[planet_names[i]] = {
                'longitude': longitude,
                'sign': planet_sign,
                'degree': longitude % 30,
                'house': house_number
            }
        
        print(f"Calculated natal positions with houses: {planets}")
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