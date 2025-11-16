import swisseph as swe
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class RealTransitCalculator:
    """Real astronomical transit calculations using Swiss Ephemeris"""
    
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Traditional Vedic aspects for each planet
        self.vedic_aspects = {
            'Sun': [1, 7],
            'Moon': [1, 7],
            'Mars': [1, 4, 7, 8],
            'Mercury': [1, 7],
            'Jupiter': [1, 5, 7, 9],
            'Venus': [1, 7],
            'Saturn': [1, 3, 7, 10],
            'Rahu': [1, 5, 7, 9],
            'Ketu': [1, 5, 7, 9]
        }
        
        self.planet_numbers = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN,
            'Rahu': swe.MEAN_NODE, 'Ketu': swe.MEAN_NODE
        }
    
    def get_planet_position(self, date: datetime, planet: str) -> Optional[float]:
        """Get real planet position for specific date"""
        try:
            jd = swe.julday(date.year, date.month, date.day, 12.0)
            planet_num = self.planet_numbers.get(planet)
            
            if planet_num is None:
                return None
                
            result = swe.calc_ut(jd, planet_num, swe.FLG_SIDEREAL)
            longitude = result[0][0]
            
            if planet == 'Ketu':
                longitude = (longitude + 180) % 360
                
            return longitude
        except:
            return None
    
    def calculate_house_from_longitude(self, longitude: float, ascendant_longitude: float) -> int:
        """Calculate house number from longitude using whole sign houses"""
        planet_sign = int(longitude / 30)
        ascendant_sign = int(ascendant_longitude / 30)
        house = ((planet_sign - ascendant_sign) % 12) + 1
        

        
        return house
    
    def find_real_aspects(self, birth_data: Dict) -> List[Dict]:
        """Find real aspects that can occur between transit and natal planets"""
        aspects = []
        
        # Calculate natal positions
        natal_positions = self._calculate_natal_positions(birth_data)
        if not natal_positions:
            return []
        
        ascendant_longitude = natal_positions.get('ascendant_longitude', 0)
        
        # Transit planets that create meaningful aspects
        transit_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
        natal_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for transit_planet in transit_planets:
            if transit_planet not in self.vedic_aspects:
                continue
                
            available_aspects = self.vedic_aspects[transit_planet]
            
            for natal_planet in natal_planets:
                if natal_planet not in natal_positions:
                    continue
                    
                natal_data = natal_positions[natal_planet]
                natal_house = self.calculate_house_from_longitude(
                    natal_data['longitude'], ascendant_longitude
                )
                
                # Check if any natal relationship existed between these planets
                had_natal_relationship = False
                for test_aspect in available_aspects:
                    if self._natal_aspect_existed(transit_planet, natal_planet, test_aspect, natal_positions, ascendant_longitude):
                        had_natal_relationship = True
                        break
                
                # If planets had any natal relationship, include ALL possible transit aspects
                if had_natal_relationship:
                    for aspect_num in available_aspects:
                        aspects.append({
                            'transit_planet': transit_planet,
                            'natal_planet': natal_planet,
                            'aspect_number': aspect_num,
                            'natal_longitude': natal_data['longitude'],
                            'natal_house': natal_house,
                            'ascendant_longitude': ascendant_longitude
                        })
        
        return aspects
    
    def calculate_aspect_timeline(self, aspect_data: Dict, start_year: int, year_range: int, birth_data: Dict = None) -> List[Dict]:
        """Calculate when specific aspect occurs using real ephemeris"""
        timeline = []
        
        transit_planet = aspect_data['transit_planet']
        natal_planet = aspect_data['natal_planet']
        aspect_number = aspect_data['aspect_number']
        natal_house = aspect_data['natal_house']
        ascendant_longitude = aspect_data['ascendant_longitude']
        
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(start_year + year_range, 12, 31)
        current_date = start_date
        
        # Adjust sampling frequency based on year range
        if year_range <= 2:
            step_days = 3  # Every 3 days for short periods
        elif year_range <= 5:
            step_days = 7  # Weekly for medium periods
        else:
            step_days = 15  # Bi-weekly for long periods
        
        # print(f"   Calculating {transit_planet}->{natal_planet} aspect {aspect_number} from {start_year} to {start_year + year_range} (step: {step_days} days)")
        
        # Check if aspect is already active at start of period
        initial_longitude = self.get_planet_position(start_date, transit_planet)
        in_aspect = False
        aspect_start = None
        
        if initial_longitude is not None:
            initial_house = self.calculate_house_from_longitude(initial_longitude, ascendant_longitude)
            
            # Check if initial aspect is active
            if aspect_number == 1:
                # For conjunction, transit planet must be in same house as natal planet
                initial_aspecting = (initial_house == natal_house)
            else:
                # Calculate which house transit planet aspects from its initial position
                initial_aspected_house = ((initial_house + aspect_number - 2) % 12) + 1
                initial_aspecting = (initial_aspected_house == natal_house)
            
            if initial_aspecting:
                in_aspect = True
                aspect_start = start_date
                aspect_start_house = initial_house  # Capture initial house
        
        # Check every 3 days for aspect formation
        while current_date <= end_date:
            transit_longitude = self.get_planet_position(current_date, transit_planet)
            
            if transit_longitude is not None:
                transit_house = self.calculate_house_from_longitude(
                    transit_longitude, ascendant_longitude
                )
                
                # Check if transit planet is aspecting natal planet
                if aspect_number == 1:
                    # For conjunction, transit planet must be in same house as natal planet
                    is_aspecting = (transit_house == natal_house)
                else:
                    # Calculate which house transit planet aspects from its current position
                    aspected_house = ((transit_house + aspect_number - 2) % 12) + 1
                    is_aspecting = (aspected_house == natal_house)
                    

                
                if is_aspecting and not in_aspect:
                    # Start of aspect period
                    in_aspect = True
                    aspect_start = current_date
                    aspect_start_house = transit_house  # Capture house when aspect starts
                elif not is_aspecting and in_aspect:
                    # End of aspect period
                    in_aspect = False
                    if aspect_start:
                        # Get natal positions from birth data
                        natal_positions = self._calculate_natal_positions(birth_data) if birth_data else {}
                        
                        # Get comprehensive transit data for this period using start house
                        start_house = aspect_start_house if 'aspect_start_house' in locals() else transit_house
                        transit_data = self._get_comprehensive_transit_data(
                            transit_planet, start_house, aspect_start, current_date, 
                            natal_positions, ascendant_longitude
                        )
                        
                        timeline.append({
                            'start_date': aspect_start.strftime('%Y-%m-%d'),
                            'end_date': current_date.strftime('%Y-%m-%d'),
                            'peak_date': aspect_start.strftime('%Y-%m-%d'),
                            'aspect_type': f'{aspect_number}{"st" if aspect_number == 1 else "th"}_house',
                            'transit_house': start_house,  # Use house from when aspect started
                            'natal_house': natal_house,
                            'conjunct_natal_planets': transit_data['conjunct_planets'],
                            'all_aspects_cast': transit_data['all_aspects']
                        })
            
            current_date += timedelta(days=step_days)
        
        # Handle ongoing aspect at end of period
        if in_aspect and aspect_start:
            # Get natal positions for ongoing aspect
            natal_positions = self._calculate_natal_positions(birth_data) if birth_data else {}
            
            # Use house from when aspect started
            ongoing_house = aspect_start_house if 'aspect_start_house' in locals() else (transit_house if 'transit_house' in locals() else natal_house)
            transit_data = self._get_comprehensive_transit_data(
                transit_planet, ongoing_house, aspect_start, end_date,
                natal_positions, ascendant_longitude
            )
            
            timeline.append({
                'start_date': aspect_start.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'peak_date': aspect_start.strftime('%Y-%m-%d'),
                'aspect_type': f'{aspect_number}{"st" if aspect_number == 1 else "th"}_house',
                'transit_house': ongoing_house,  # Use house from when aspect started
                'natal_house': natal_house,
                'conjunct_natal_planets': transit_data['conjunct_planets'],
                'all_aspects_cast': transit_data['all_aspects']
            })
        
        return timeline
    
    def _calculate_natal_positions(self, birth_data: Dict) -> Dict:
        """Calculate natal planetary positions"""
        try:
            # print(f"     Calculating natal positions for: {birth_data.get('date')} {birth_data.get('time')}")
            
            # Parse birth data
            time_parts = birth_data['time'].split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60
            # print(f"     Parsed time: {hour} hours")
            
            # Handle timezone
            if 6.0 <= birth_data['latitude'] <= 37.0 and 68.0 <= birth_data['longitude'] <= 97.0:
                tz_offset = 5.5
            else:
                tz_offset = 0
                timezone_str = birth_data.get('timezone', '')
                if timezone_str.startswith('UTC'):
                    tz_str = timezone_str[3:]
                    if tz_str and ':' in tz_str:
                        sign = 1 if tz_str[0] == '+' else -1
                        parts = tz_str[1:].split(':')
                        tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
            
            # print(f"     Timezone offset: {tz_offset} hours")

            
            utc_hour = hour - tz_offset
            jd = swe.julday(
                int(birth_data['date'].split('-')[0]),
                int(birth_data['date'].split('-')[1]),
                int(birth_data['date'].split('-')[2]),
                utc_hour
            )
            
            # Calculate ascendant
            houses_data = swe.houses(jd, birth_data['latitude'], birth_data['longitude'], b'P')
            ayanamsa = swe.get_ayanamsa_ut(jd)
            ascendant_tropical = houses_data[1][0]
            ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
            
            positions = {
                'ascendant_longitude': ascendant_sidereal
            }
            
            # Calculate planetary positions
            planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
            
            for planet_name in planet_names:
                planet_num = self.planet_numbers[planet_name]
                pos = swe.calc_ut(jd, planet_num, swe.FLG_SIDEREAL)
                longitude = pos[0][0]
                
                positions[planet_name] = {
                    'longitude': longitude,
                    'sign': int(longitude / 30),
                    'degree': longitude % 30
                }
            
            # print(f"     Successfully calculated {len(positions)} positions")
            return positions
            
        except Exception as e:
            # print(f"     ❌ Error calculating natal positions: {e}")
            # import traceback
            # traceback.print_exc()
            pass
            return {}
    
    def _natal_aspect_existed(self, planet1: str, planet2: str, aspect_number: int, natal_positions: Dict, ascendant_longitude: float) -> bool:
        """Check if aspect existed between planets in natal chart"""
        if planet1 not in natal_positions or planet2 not in natal_positions:
            return False
        
        # Get natal house positions
        planet1_house = self.calculate_house_from_longitude(
            natal_positions[planet1]['longitude'], ascendant_longitude
        )
        planet2_house = self.calculate_house_from_longitude(
            natal_positions[planet2]['longitude'], ascendant_longitude
        )
        
        # Check if planet1 could aspect planet2 in natal chart
        available_aspects = self.vedic_aspects.get(planet1, [])
        
        for test_aspect in available_aspects:
            if test_aspect == 1:
                # Conjunction - same house
                if planet1_house == planet2_house and aspect_number == 1:
                    return True
            else:
                # Calculate which house planet1 aspects from its natal position
                aspected_house = ((planet1_house + test_aspect - 2) % 12) + 1
                if aspected_house == planet2_house and aspect_number == test_aspect:
                    return True
        
        return False
    
    def _get_comprehensive_transit_data(self, transit_planet: str, transit_house: int, 
                                       start_date: datetime, end_date: datetime,
                                       natal_positions: Dict, ascendant_longitude: float) -> Dict:
        """Get comprehensive transit data including conjunctions and all aspects"""
        # print(f"         Getting comprehensive data for {transit_planet} in house {transit_house}")
        
        # Find all natal planets in the same house as transit planet (conjunctions)
        conjunct_planets = []
        # print(f"         Checking for conjunctions in house {transit_house}:")
        
        for planet_name, planet_data in natal_positions.items():
            if planet_name == 'ascendant_longitude':
                continue
            
            planet_house = self.calculate_house_from_longitude(
                planet_data['longitude'], ascendant_longitude
            )
            
            # print(f"           {planet_name} in house {planet_house}")
            
            if planet_house == transit_house:
                conjunct_planets.append(planet_name)
                # print(f"           -> CONJUNCTION with {planet_name}")
        
        # print(f"         Total conjunctions: {len(conjunct_planets)} - {conjunct_planets}")
        
        # Calculate all aspects cast by transit planet
        available_aspects = self.vedic_aspects.get(transit_planet, [1, 7])
        # print(f"         {transit_planet} can cast aspects: {available_aspects}")
        
        all_aspects = []
        
        for aspect_num in available_aspects:
            if aspect_num == 1:
                # Conjunction - already handled above
                if conjunct_planets:
                    all_aspects.append({
                        'aspect_type': 'conjunction',
                        'aspect_number': 1,
                        'target_house': transit_house,
                        'target_planets': conjunct_planets
                    })
                    # print(f"           Added conjunction aspect to house {transit_house}")
            else:
                # Calculate which house this aspect targets
                target_house = ((transit_house + aspect_num - 2) % 12) + 1
                # print(f"           {aspect_num}th aspect from house {transit_house} targets house {target_house}")
                
                # Find natal planets in target house
                target_planets = []
                for planet_name, planet_data in natal_positions.items():
                    if planet_name == 'ascendant_longitude':
                        continue
                    
                    planet_house = self.calculate_house_from_longitude(
                        planet_data['longitude'], ascendant_longitude
                    )
                    
                    if planet_house == target_house:
                        target_planets.append(planet_name)
                        # print(f"             -> Aspects {planet_name} in house {target_house}")
                
                all_aspects.append({
                    'aspect_type': f'{aspect_num}th_aspect',
                    'aspect_number': aspect_num,
                    'target_house': target_house,
                    'target_planets': target_planets
                })
        
        # print(f"         Total aspects cast: {len(all_aspects)}")
        
        return {
            'conjunct_planets': conjunct_planets,
            'all_aspects': all_aspects
        }