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
        
        # Nakshatra lordship mapping
        self.nakshatra_lords = {
            'Ashwini': 'Ketu', 'Bharani': 'Venus', 'Krittika': 'Sun',
            'Rohini': 'Moon', 'Mrigashira': 'Mars', 'Ardra': 'Rahu',
            'Punarvasu': 'Jupiter', 'Pushya': 'Saturn', 'Ashlesha': 'Mercury',
            'Magha': 'Ketu', 'Purva Phalguni': 'Venus', 'Uttara Phalguni': 'Sun',
            'Hasta': 'Moon', 'Chitra': 'Mars', 'Swati': 'Rahu',
            'Vishakha': 'Jupiter', 'Anuradha': 'Saturn', 'Jyeshtha': 'Mercury',
            'Mula': 'Ketu', 'Purva Ashadha': 'Venus', 'Uttara Ashadha': 'Sun',
            'Shravana': 'Moon', 'Dhanishta': 'Mars', 'Shatabhisha': 'Rahu',
            'Purva Bhadrapada': 'Jupiter', 'Uttara Bhadrapada': 'Saturn', 'Revati': 'Mercury'
        }
        
        # Focus on slow-moving planets for meaningful transits
        self.transit_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
        self.natal_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        # Gandanta points - critical junction degrees between water and fire signs
        self.gandanta_points = [
            {'name': 'Pisces-Aries', 'water_end': 360.0, 'fire_start': 0.0, 'range': 3.0},  # 27° Pisces to 3° Aries
            {'name': 'Cancer-Leo', 'water_end': 120.0, 'fire_start': 120.0, 'range': 3.0},   # 27° Cancer to 3° Leo  
            {'name': 'Scorpio-Sagittarius', 'water_end': 240.0, 'fire_start': 240.0, 'range': 3.0}  # 27° Scorpio to 3° Sagittarius
        ]
    
    def calculate_vedic_aspects(self, natal_planets: Dict) -> List[Dict]:
        """Calculate enhanced Vedic transit aspects including nakshatra connections"""
        aspects = []
        
        # First, find all natal aspects
        natal_aspects = self._find_natal_aspects(natal_planets)
        
        print(f"\n=== CREATING ENHANCED TRANSIT ASPECTS ===")
        
        # 1. Traditional aspects (existing logic)
        for natal_aspect in natal_aspects:
            transit_planet = natal_aspect['planet1']
            natal_planet = natal_aspect['planet2']
            aspect_type = natal_aspect['aspect_type']
            
            if transit_planet in self.transit_planets and natal_planet in self.natal_planets:
                natal_data = natal_planets[natal_planet]
                
                aspect_entry = {
                    'planet1': transit_planet,
                    'planet2': natal_planet,
                    'aspect_type': aspect_type,
                    'natal_longitude': natal_data['longitude'],
                    'natal_house': natal_data.get('house', 1),
                    'aspect_house': int(aspect_type.replace('th_house', '')),
                    'description': f'Transit {transit_planet} re-activating natal {aspect_type} to {natal_planet}',
                    'enhancement_type': 'regular'
                }
                
                aspects.append(aspect_entry)
                print(f"Added regular aspect: {transit_planet} -> {natal_planet} ({aspect_type})")
        
        # 2. Nakshatra-enhanced aspects (new logic)
        aspects.extend(self._find_nakshatra_enhanced_aspects(natal_planets))
        
        # 3. Gandanta point aspects (critical junction transits)
        aspects.extend(self._find_gandanta_aspects(natal_planets))
        
        print(f"Total enhanced transit aspects created: {len(aspects)}")
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
    
    def calculate_nakshatra_timeline(self, transit_planet: str, natal_planet: str, 
                                   start_year: int, year_range: int, natal_planets: Dict, 
                                   request_data: Dict) -> List[Dict]:
        """Calculate when transiting planet enters natal planet's nakshatra for activation"""
        timeline = []
        
        # Get the target nakshatra to transit through
        natal_data = natal_planets.get(natal_planet, {})
        if not natal_data:
            print(f"[NAKSHATRA_DEBUG] No natal data found for {natal_planet}")
            return []
            
        target_nakshatra = self._get_nakshatra_from_longitude(natal_data['longitude'])
        enhancement_type = request_data.get('enhancement_type', 'natal_nakshatra')
        
        print(f"[NAKSHATRA_DEBUG] Natal {natal_planet} longitude: {natal_data['longitude']:.2f}°")
        print(f"[NAKSHATRA_DEBUG] Natal {natal_planet} nakshatra: {target_nakshatra}")
        print(f"[NAKSHATRA_DEBUG] Looking for {transit_planet} transits through {target_nakshatra}")
        
        print(f"[NAKSHATRA_DEBUG] === CALCULATING NAKSHATRA TIMELINE ===")
        print(f"[NAKSHATRA_DEBUG] Transit {transit_planet} entering {natal_planet}'s nakshatra ({target_nakshatra})")
        print(f"[NAKSHATRA_DEBUG] Enhancement type: {enhancement_type}")
        
        # Calculate nakshatra boundaries (each nakshatra = 13°20' = 13.333°)
        nakshatra_names = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
            'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
            'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
            'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        try:
            nakshatra_index = nakshatra_names.index(target_nakshatra)
            nakshatra_start = nakshatra_index * 13.333333
            nakshatra_end = (nakshatra_index + 1) * 13.333333
            
            print(f"[NAKSHATRA_DEBUG] Target nakshatra {target_nakshatra} spans {nakshatra_start:.2f}° to {nakshatra_end:.2f}°")
            
            # Date range for calculation
            start_date = datetime(start_year, 1, 1)
            end_date = datetime(start_year + year_range, 12, 31)
            current_date = start_date
            
            step_days = 30  # Monthly steps for faster calculation
            in_nakshatra = False
            period_start_date = None
            
            while current_date <= end_date:
                transit_position = self._get_planet_position(current_date, transit_planet)
                
                if transit_position is not None:
                    # Check if transit planet is in target nakshatra
                    is_in_target_nakshatra = self._is_in_nakshatra_range(
                        transit_position, nakshatra_start, nakshatra_end
                    )
                    
                    if is_in_target_nakshatra:
                        if not in_nakshatra:
                            # Start new nakshatra period
                            in_nakshatra = True
                            period_start_date = current_date
                            print(f"[NAKSHATRA_DEBUG] Started nakshatra period: {current_date.strftime('%Y-%m-%d')}")
                            print(f"[NAKSHATRA_DEBUG] Transit {transit_planet} at {transit_position:.1f}° on {current_date.strftime('%Y-%m-%d')}")
                    else:
                        if in_nakshatra:
                            # End current nakshatra period
                            in_nakshatra = False
                            if period_start_date:
                                timeline.append({
                                    'start_date': period_start_date.strftime('%Y-%m-%d'),
                                    'end_date': current_date.strftime('%Y-%m-%d'),
                                    'peak_date': period_start_date.strftime('%Y-%m-%d')
                                })
                                print(f"[NAKSHATRA_DEBUG] Ended nakshatra period: {period_start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
                                print(f"[NAKSHATRA_DEBUG] Transit {transit_planet} at {transit_position:.1f}° on {current_date.strftime('%Y-%m-%d')}")
                                period_start_date = None
                else:
                    # No planet position, end any current period
                    if in_nakshatra:
                        in_nakshatra = False
                        if period_start_date:
                            timeline.append({
                                'start_date': period_start_date.strftime('%Y-%m-%d'),
                                'end_date': current_date.strftime('%Y-%m-%d'),
                                'peak_date': period_start_date.strftime('%Y-%m-%d')
                            })
                            period_start_date = None
                
                current_date += timedelta(days=step_days)
            
            # Handle case where nakshatra period continues to end of range
            if in_nakshatra and period_start_date:
                timeline.append({
                    'start_date': period_start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'peak_date': period_start_date.strftime('%Y-%m-%d')
                })
            
            print(f"[NAKSHATRA_DEBUG] Found {len(timeline)} nakshatra activation periods")
            for period in timeline:
                print(f"[NAKSHATRA_DEBUG] Period: {period['start_date']} to {period['end_date']}")
            if len(timeline) == 0:
                print(f"[NAKSHATRA_DEBUG] No periods found for {transit_planet} transiting through {target_nakshatra}")
                print(f"[NAKSHATRA_DEBUG] This could mean {transit_planet} doesn't transit through this nakshatra in {start_year}")
                
                # Show Jupiter's position at start and end of year for context
                start_pos = self._get_planet_position(start_date, transit_planet)
                end_pos = self._get_planet_position(end_date, transit_planet)
                if start_pos and end_pos:
                    start_nak = self._get_nakshatra_from_longitude(start_pos)
                    end_nak = self._get_nakshatra_from_longitude(end_pos)
                    print(f"[NAKSHATRA_DEBUG] {transit_planet} position: {start_pos:.1f}° ({start_nak}) to {end_pos:.1f}° ({end_nak}) in {start_year}")
                    print(f"[NAKSHATRA_DEBUG] Target range: {nakshatra_start:.1f}° to {nakshatra_end:.1f}° ({target_nakshatra})")
                    
                    # Calculate approximate years when Jupiter was/will be in target nakshatra
                    if transit_planet == 'Jupiter':
                        current_pos = (start_pos + end_pos) / 2
                        target_pos = (nakshatra_start + nakshatra_end) / 2
                        
                        # Handle 360° wraparound
                        if target_pos < current_pos:
                            target_pos += 360
                        
                        degrees_to_travel = target_pos - current_pos
                        years_to_target = degrees_to_travel / 30  # Jupiter moves ~30°/year
                        target_year = start_year + int(years_to_target)
                        
                        # Also calculate when it was last there (12 years ago)
                        last_year = target_year - 12
                        
                        print(f"[NAKSHATRA_DEBUG] Jupiter was last in {target_nakshatra}: ~{last_year}")
                        print(f"[NAKSHATRA_DEBUG] Jupiter will next be in {target_nakshatra}: ~{target_year}")
            return timeline
            
        except ValueError:
            print(f"[NAKSHATRA_DEBUG] Unknown nakshatra: {target_nakshatra}")
            return []
        except Exception as e:
            print(f"[NAKSHATRA_DEBUG] Error calculating nakshatra timeline: {e}")
            return []
    
    def calculate_gandanta_timeline(self, transit_planet: str, natal_planet: str,
                                  start_year: int, year_range: int, natal_planets: Dict,
                                  request_data: Dict) -> List[Dict]:
        """Calculate when transiting planet crosses Gandanta points to activate natal planet"""
        timeline = []
        
        # Get natal planet's Gandanta point
        natal_data = natal_planets.get(natal_planet, {})
        if not natal_data:
            print(f"[GANDANTA_DEBUG] No natal data found for {natal_planet}")
            return []
        
        natal_longitude = natal_data['longitude']
        gandanta_info = self._is_at_gandanta_point(natal_longitude)
        
        if not gandanta_info:
            print(f"[GANDANTA_DEBUG] {natal_planet} is not at a Gandanta point")
            return []
        
        print(f"[GANDANTA_DEBUG] === CALCULATING GANDANTA TIMELINE ===")
        print(f"[GANDANTA_DEBUG] Natal {natal_planet} at {gandanta_info['name']} Gandanta ({natal_longitude:.2f}°)")
        print(f"[GANDANTA_DEBUG] Looking for {transit_planet} transits through {gandanta_info['name']} junction")
        
        # Define Gandanta ranges for transit calculation
        gandanta_ranges = {
            'Pisces-Aries': [(357.0, 360.0), (0.0, 3.0)],  # Split range due to 360° wraparound
            'Cancer-Leo': [(117.0, 123.0)],
            'Scorpio-Sagittarius': [(237.0, 243.0)]
        }
        
        target_ranges = gandanta_ranges.get(gandanta_info['name'], [])
        print(f"[GANDANTA_DEBUG] Target Gandanta ranges: {target_ranges}")
        
        try:
            # Date range for calculation
            start_date = datetime(start_year, 1, 1)
            end_date = datetime(start_year + year_range, 12, 31)
            current_date = start_date
            
            step_days = 7  # Weekly steps
            in_gandanta = False
            period_start_date = None
            
            while current_date <= end_date:
                transit_position = self._get_planet_position(current_date, transit_planet)
                
                if transit_position is not None:
                    # Check if transit planet is in any of the target Gandanta ranges
                    is_in_gandanta = False
                    for range_start, range_end in target_ranges:
                        if self._is_in_gandanta_range(transit_position, range_start, range_end):
                            is_in_gandanta = True
                            break
                    
                    if is_in_gandanta:
                        if not in_gandanta:
                            # Start new Gandanta period
                            in_gandanta = True
                            period_start_date = current_date
                            print(f"[GANDANTA_DEBUG] Started Gandanta period: {current_date.strftime('%Y-%m-%d')}")
                            print(f"[GANDANTA_DEBUG] Transit {transit_planet} at {transit_position:.1f}°")
                    else:
                        if in_gandanta:
                            # End current Gandanta period
                            in_gandanta = False
                            if period_start_date:
                                timeline.append({
                                    'start_date': period_start_date.strftime('%Y-%m-%d'),
                                    'end_date': current_date.strftime('%Y-%m-%d'),
                                    'peak_date': period_start_date.strftime('%Y-%m-%d')
                                })
                                print(f"[GANDANTA_DEBUG] Ended Gandanta period: {period_start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
                                period_start_date = None
                else:
                    # No planet position, end any current period
                    if in_gandanta:
                        in_gandanta = False
                        if period_start_date:
                            timeline.append({
                                'start_date': period_start_date.strftime('%Y-%m-%d'),
                                'end_date': current_date.strftime('%Y-%m-%d'),
                                'peak_date': period_start_date.strftime('%Y-%m-%d')
                            })
                            period_start_date = None
                
                current_date += timedelta(days=step_days)
            
            # Handle case where Gandanta period continues to end of range
            if in_gandanta and period_start_date:
                timeline.append({
                    'start_date': period_start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'peak_date': period_start_date.strftime('%Y-%m-%d')
                })
            
            print(f"[GANDANTA_DEBUG] Found {len(timeline)} Gandanta activation periods")
            for period in timeline:
                print(f"[GANDANTA_DEBUG] Period: {period['start_date']} to {period['end_date']}")
            
            return timeline
            
        except Exception as e:
            print(f"[GANDANTA_DEBUG] Error calculating Gandanta timeline: {e}")
            return []
    
    def _is_in_gandanta_range(self, longitude: float, range_start: float, range_end: float) -> bool:
        """Check if longitude is within Gandanta range (handles 360° wraparound)"""
        longitude = longitude % 360
        
        if range_start <= range_end:
            return range_start <= longitude <= range_end
        else:  # Range crosses 0° (Pisces-Aries case)
            return longitude >= range_start or longitude <= range_end
    
    def _is_in_nakshatra_range(self, longitude: float, start: float, end: float) -> bool:
        """Check if longitude is within nakshatra range (handles 360° wraparound)"""
        # Normalize longitude to 0-360
        longitude = longitude % 360
        
        if start <= end:
            return start <= longitude <= end
        else:  # Range crosses 0° (e.g., Revati to Ashwini)
            return longitude >= start or longitude <= end
    
    def _get_nakshatra_from_longitude(self, longitude: float) -> str:
        """Get nakshatra name from longitude"""
        nakshatra_names = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
            'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
            'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
            'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        nakshatra_index = int(longitude / 13.333333)  # Each nakshatra is 13°20'
        return nakshatra_names[nakshatra_index % 27]
    
    def _find_nakshatra_enhanced_aspects(self, natal_planets: Dict) -> List[Dict]:
        """Find aspects enhanced by nakshatra connections"""
        enhanced_aspects = []
        
        print(f"\n=== FINDING NAKSHATRA ENHANCED ASPECTS ===")
        
        for transit_planet in self.transit_planets:
            if transit_planet not in natal_planets:
                continue
                
            transit_data = natal_planets[transit_planet]
            transit_nakshatra = self._get_nakshatra_from_longitude(transit_data['longitude'])
            transit_nakshatra_lord = self.nakshatra_lords.get(transit_nakshatra)
            
            for natal_planet in self.natal_planets:
                if natal_planet not in natal_planets or transit_planet == natal_planet:
                    continue
                    
                natal_data = natal_planets[natal_planet]
                natal_nakshatra = self._get_nakshatra_from_longitude(natal_data['longitude'])
                natal_nakshatra_lord = self.nakshatra_lords.get(natal_nakshatra)
                
                # Check for nakshatra connections
                enhancement_type = None
                description_suffix = ""
                
                # Case 1: Transit planet is natal planet's nakshatra lord
                if transit_planet == natal_nakshatra_lord:
                    enhancement_type = 'star_lord'
                    description_suffix = f" (Star Lord: {natal_planet} in {natal_nakshatra})"
                
                # Case 2: Natal planet is in transit planet's nakshatra
                elif natal_nakshatra_lord == transit_planet:
                    enhancement_type = 'natal_nakshatra'
                    description_suffix = f" (Natal Connection: {natal_planet} in {transit_planet}'s {natal_nakshatra})"
                
                # If there's a nakshatra connection, create a single nakshatra-only aspect
                if enhancement_type:
                    aspect_entry = {
                        'planet1': transit_planet,
                        'planet2': natal_planet,
                        'aspect_type': 'nakshatra_connection',
                        'natal_longitude': natal_data['longitude'],
                        'natal_house': natal_data.get('house', 1),
                        'aspect_house': None,  # No geometric aspect
                        'description': f'Transit {transit_planet} nakshatra connection to {natal_planet}{description_suffix}',
                        'enhancement_type': enhancement_type,
                        'natal_nakshatra': natal_nakshatra,
                        'natal_nakshatra_lord': natal_nakshatra_lord,
                        'is_nakshatra_only': True
                    }
                    
                    enhanced_aspects.append(aspect_entry)
                    print(f"Added {enhancement_type} connection: {transit_planet} -> {natal_planet} (nakshatra only)")
        
        print(f"Total nakshatra enhanced aspects: {len(enhanced_aspects)}")
        return enhanced_aspects
    
    def _find_gandanta_aspects(self, natal_planets: Dict) -> List[Dict]:
        """Find aspects for planets at or transiting through Gandanta points"""
        gandanta_aspects = []
        
        print(f"\n=== FINDING GANDANTA ASPECTS ===")
        
        for transit_planet in self.transit_planets:
            if transit_planet not in natal_planets:
                continue
                
            for natal_planet in self.natal_planets:
                if natal_planet not in natal_planets:
                    continue
                    
                natal_data = natal_planets[natal_planet]
                natal_longitude = natal_data['longitude']
                
                # Check if natal planet is at a Gandanta point
                gandanta_info = self._is_at_gandanta_point(natal_longitude)
                if gandanta_info:
                    aspect_entry = {
                        'planet1': transit_planet,
                        'planet2': natal_planet,
                        'aspect_type': 'gandanta_transit',
                        'natal_longitude': natal_longitude,
                        'natal_house': natal_data.get('house', 1),
                        'aspect_house': None,
                        'description': f'Transit {transit_planet} activating {natal_planet} at Gandanta point ({gandanta_info["name"]})',
                        'enhancement_type': 'gandanta',
                        'gandanta_point': gandanta_info['name'],
                        'gandanta_degree': natal_longitude % 30,
                        'is_gandanta': True
                    }
                    
                    gandanta_aspects.append(aspect_entry)
                    print(f"Added Gandanta aspect: {transit_planet} -> {natal_planet} at {gandanta_info['name']} ({natal_longitude:.2f}°)")
        
        print(f"Total Gandanta aspects: {len(gandanta_aspects)}")
        return gandanta_aspects
    
    def _is_at_gandanta_point(self, longitude: float) -> Dict:
        """Check if longitude is at a Gandanta point (within 3° of water-fire junction)"""
        longitude = longitude % 360
        
        for gandanta in self.gandanta_points:
            # Check Pisces-Aries junction (357° to 3°)
            if gandanta['name'] == 'Pisces-Aries':
                if longitude >= 357.0 or longitude <= 3.0:
                    return gandanta
            
            # Check Cancer-Leo junction (117° to 123°)
            elif gandanta['name'] == 'Cancer-Leo':
                if 117.0 <= longitude <= 123.0:
                    return gandanta
            
            # Check Scorpio-Sagittarius junction (237° to 243°)
            elif gandanta['name'] == 'Scorpio-Sagittarius':
                if 237.0 <= longitude <= 243.0:
                    return gandanta
        
        return None

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
    
    # Get natal planet information
    natal_planets = await _calculate_natal_positions(birth_data)
    
    # Handle nakshatra-only connections
    if aspect_type == 'nakshatra_connection':
        timeline = vedic_calculator.calculate_nakshatra_timeline(
            planet1, planet2, start_year, year_range, natal_planets, request_data
        )
        return {
            'timeline': timeline,
            'start_year': start_year,
            'year_range': year_range
        }
    
    # Handle Gandanta transit connections
    if aspect_type == 'gandanta_transit':
        timeline = vedic_calculator.calculate_gandanta_timeline(
            planet1, planet2, start_year, year_range, natal_planets, request_data
        )
        return {
            'timeline': timeline,
            'start_year': start_year,
            'year_range': year_range
        }
    
    # Extract aspect house number from aspect_type
    aspect_house = int(aspect_type.replace('th_house', ''))
    
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