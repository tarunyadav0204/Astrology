from typing import Dict, Any
from calculators.base_calculator import BaseCalculator

class SniperPointsCalculator(BaseCalculator):
    """Calculator for Sniper Points - critical degrees that trigger sudden events"""
    
    # Classical Mrityu Bhaga - ONE universal degree per sign (BPHS/Phaladeepika)
    MRITYU_BHAGA_DEGREES = {
        0: 19, 1: 9, 2: 13, 3: 26, 4: 24, 5: 11,
        6: 6, 7: 14, 8: 13, 9: 25, 10: 4, 11: 12
    }
    
    def __init__(self, d1_chart: Dict, d3_chart: Dict, d9_chart: Dict):
        self.d1_chart = d1_chart
        self.d3_chart = d3_chart
        self.d9_chart = d9_chart
        
        self.sign_names = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        self.sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
    
    def calculate_kharesh_point(self) -> Dict[str, Any]:
        """Calculate 22nd Drekkana (Kharesh) - 8th sign from D3 ascendant"""
        try:
            # Handle different D3 chart structures
            d3_asc_long = None
            if 'ascendant' in self.d3_chart:
                d3_asc_long = self.d3_chart['ascendant']
            elif 'divisional_chart' in self.d3_chart and 'ascendant' in self.d3_chart['divisional_chart']:
                d3_asc_long = self.d3_chart['divisional_chart']['ascendant']
            
            if d3_asc_long is None:
                return {'error': 'Kharesh calculation failed: D3 ascendant not found'}
            
            d3_asc_sign = int(d3_asc_long / 30)
            drekkana_22_sign_idx = (d3_asc_sign + 7) % 12
            kharesh_lord = self.sign_lords[drekkana_22_sign_idx]
            
            # Get D1 planets
            if 'planets' not in self.d1_chart:
                return {'error': 'Kharesh calculation failed: D1 chart structure invalid'}
            
            lord_in_d1 = self.d1_chart['planets'].get(kharesh_lord, {})
            
            return {
                'point_name': '22nd Drekkana (Kharesh)',
                'danger_sign': self.sign_names[drekkana_22_sign_idx],
                'kharesh_lord': kharesh_lord,
                'lord_location_d1': f"{self.sign_names[lord_in_d1.get('sign', 0)]} ({lord_in_d1.get('house', 0)}th House)",
                'significance': 'Sensitive point for health and sudden events.',
                'transit_watch': f"Watch when Saturn/Rahu transits {self.sign_names[drekkana_22_sign_idx]} or crosses {kharesh_lord}."
            }
        except Exception as e:
            return {'error': f'Kharesh calculation failed: {e}'}
    
    def calculate_64th_navamsa(self) -> Dict[str, Any]:
        """Calculate 64th Navamsa - 4th sign from Moon in D9 chart"""
        try:
            # Handle different D9 chart structures
            d9_planets = None
            if 'planets' in self.d9_chart:
                d9_planets = self.d9_chart['planets']
            elif 'divisional_chart' in self.d9_chart and 'planets' in self.d9_chart['divisional_chart']:
                d9_planets = self.d9_chart['divisional_chart']['planets']
            
            if not d9_planets or 'Moon' not in d9_planets:
                return {'error': '64th Navamsa calculation failed: Moon not found in D9 chart'}
            
            moon_d9 = d9_planets['Moon']
            moon_d9_sign = moon_d9.get('sign')
            
            if moon_d9_sign is None:
                moon_d9_sign = int(moon_d9.get('longitude', 0) / 30)
            
            navamsa_64_sign_idx = (moon_d9_sign + 3) % 12
            navamsa_lord = self.sign_lords[navamsa_64_sign_idx]
            
            return {
                'point_name': '64th Navamsa',
                'danger_sign': self.sign_names[navamsa_64_sign_idx],
                'danger_lord': navamsa_lord,
                'significance': 'Critical point for mental stress and transformation.',
                'transit_watch': f"Watch when Saturn/Rahu transits {self.sign_names[navamsa_64_sign_idx]}."
            }
        except Exception as e:
            return {'error': f'64th Navamsa calculation failed: {e}'}
    
    def calculate_bhrigu_bindu(self) -> Dict[str, Any]:
        """Calculate Bhrigu Bindu - midpoint between Moon and Rahu"""
        try:
            if 'planets' not in self.d1_chart:
                return {'error': 'Bhrigu Bindu calculation failed: D1 chart structure invalid'}
            
            planets = self.d1_chart['planets']
            
            if 'Moon' not in planets or 'Rahu' not in planets:
                return {'error': 'Bhrigu Bindu calculation failed: Moon or Rahu not found'}
            
            moon_long = planets['Moon']['longitude']
            rahu_long = planets['Rahu']['longitude']
            
            # Calculate midpoint (Bhrigu Bindu)
            # Handle the circular nature of zodiac (0-360 degrees)
            diff = abs(rahu_long - moon_long)
            
            if diff > 180:
                # Shorter arc goes the other way
                if moon_long < rahu_long:
                    bhrigu_bindu = (moon_long + (360 - diff) / 2) % 360
                else:
                    bhrigu_bindu = (rahu_long + (360 - diff) / 2) % 360
            else:
                # Direct midpoint
                bhrigu_bindu = (moon_long + rahu_long) / 2
            
            # Normalize to 0-360
            bhrigu_bindu = bhrigu_bindu % 360
            
            bb_sign = int(bhrigu_bindu / 30)
            bb_degree = bhrigu_bindu % 30
            bb_lord = self.sign_lords[bb_sign]
            
            # Get house placement
            ascendant = self.d1_chart.get('ascendant', 0)
            bb_house = int((bhrigu_bindu - ascendant) / 30) % 12 + 1
            
            # Calculate when slow-moving planets will transit this point
            transit_timing = self._calculate_bhrigu_bindu_transits(bhrigu_bindu, bb_sign)
            
            return {
                'point_name': 'Bhrigu Bindu',
                'longitude': round(bhrigu_bindu, 2),
                'sign': self.sign_names[bb_sign],
                'degree': round(bb_degree, 2),
                'house': bb_house,
                'lord': bb_lord,
                'significance': 'Sensitive point for destiny and karmic events. Represents the soul\'s journey.',
                'transit_watch': f"Watch when slow-moving planets (Saturn/Jupiter/Rahu) transit {self.sign_names[bb_sign]} near {bb_degree:.1f}°.",
                'formatted': f"{self.sign_names[bb_sign]} {bb_degree:.2f}° (House {bb_house})",
                'upcoming_transits': transit_timing
            }
        except Exception as e:
            return {'error': f'Bhrigu Bindu calculation failed: {e}'}
    
    def _calculate_bhrigu_bindu_transits(self, bb_longitude: float, bb_sign: int) -> Dict[str, Any]:
        """Calculate when slow-moving planets will transit Bhrigu Bindu (within 3° orb) - accounts for retrograde"""
        try:
            import swisseph as swe
            from datetime import datetime, timedelta
            
            # Initialize Swiss Ephemeris
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            current_date = datetime.now()
            jd_now = swe.julday(current_date.year, current_date.month, current_date.day)
            
            transits = {}
            
            # Planets to check: Saturn, Jupiter, Rahu (True Node for precision)
            planets_to_check = {
                'Saturn': swe.SATURN,
                'Jupiter': swe.JUPITER,
                'Rahu': swe.TRUE_NODE
            }
            
            for planet_name, planet_id in planets_to_check.items():
                # Get current position
                current_pos = swe.calc_ut(jd_now, planet_id, swe.FLG_SIDEREAL)[0][0]
                
                # Calculate if currently within orb
                orb = abs(current_pos - bb_longitude)
                if orb > 180:
                    orb = 360 - orb
                
                is_current = orb <= 3.0
                intensity_score = max(0, 100 - (orb * 10)) if is_current else 0
                
                # Find exact transit date using binary search (accounts for retrograde)
                transit_info = self._find_exact_transit_date(
                    planet_id, bb_longitude, jd_now, planet_name
                )
                
                transits[planet_name] = {
                    'current_longitude': round(current_pos, 2),
                    'current_sign': self.sign_names[int(current_pos / 30)],
                    'is_currently_transiting': is_current,
                    'current_orb': round(orb, 2) if is_current else None,
                    'intensity_score': int(intensity_score),
                    **transit_info
                }
            
            return transits
            
        except Exception as e:
            return {'error': f'Transit calculation failed: {e}'}
    
    def _find_exact_transit_date(self, planet_id: int, target_longitude: float, jd_start: float, planet_name: str) -> Dict[str, Any]:
        """Find exact date when planet crosses target longitude using iterative search"""
        import swisseph as swe
        from datetime import datetime, timedelta
        
        try:
            # Search forward up to 10 years (3650 days)
            max_days = 3650
            step_days = 30  # Check every 30 days initially
            
            # Get starting position
            start_pos = swe.calc_ut(jd_start, planet_id, swe.FLG_SIDEREAL)[0][0]
            
            # Determine direction (forward or backward for Rahu)
            is_retrograde_planet = planet_name == 'Rahu'
            
            # Calculate target distance
            if is_retrograde_planet:
                target_distance = (start_pos - target_longitude) % 360
            else:
                target_distance = (target_longitude - start_pos) % 360
            
            # Check if planet just passed (within last 30 days)
            jd_past = jd_start - 30
            past_pos = swe.calc_ut(jd_past, planet_id, swe.FLG_SIDEREAL)[0][0]
            past_distance = abs(past_pos - target_longitude)
            if past_distance > 180:
                past_distance = 360 - past_distance
            
            current_distance = abs(start_pos - target_longitude)
            if current_distance > 180:
                current_distance = 360 - current_distance
            
            is_next_cycle = past_distance < current_distance and current_distance > 10
            
            # Search for crossing point
            found_crossing = False
            crossing_jd = None
            
            for day in range(0, max_days, step_days):
                jd_check = jd_start + day
                pos = swe.calc_ut(jd_check, planet_id, swe.FLG_SIDEREAL)[0][0]
                
                # Calculate distance
                if is_retrograde_planet:
                    distance = (start_pos - pos) % 360
                else:
                    distance = (pos - start_pos) % 360
                
                # Check if we've crossed or are very close
                orb = abs(pos - target_longitude)
                if orb > 180:
                    orb = 360 - orb
                
                if orb <= 0.5:  # Within 0.5° - close enough
                    # Refine with daily steps
                    for refine_day in range(max(0, day - step_days), day + step_days):
                        jd_refine = jd_start + refine_day
                        refine_pos = swe.calc_ut(jd_refine, planet_id, swe.FLG_SIDEREAL)[0][0]
                        refine_orb = abs(refine_pos - target_longitude)
                        if refine_orb > 180:
                            refine_orb = 360 - refine_orb
                        
                        if refine_orb <= 0.1:  # Within 0.1° - exact enough
                            crossing_jd = jd_refine
                            found_crossing = True
                            break
                    
                    if found_crossing:
                        break
            
            if found_crossing and crossing_jd:
                # Convert JD to date
                year, month, day, hour = swe.revjul(crossing_jd)
                transit_date = datetime(year, month, day)
                days_until = int(crossing_jd - jd_start)
                
                return {
                    'exact_transit_date': transit_date.strftime('%Y-%m-%d'),
                    'days_until_transit': days_until if days_until > 0 else None,
                    'years_until_transit': round(days_until / 365.25, 1) if days_until > 0 else None,
                    'is_next_cycle': is_next_cycle,
                    'calculation_method': 'exact_search',
                    'retrograde_accounted': True
                }
            else:
                # No crossing found within 10 years
                return {
                    'exact_transit_date': 'Beyond 10 years',
                    'days_until_transit': None,
                    'years_until_transit': None,
                    'is_next_cycle': is_next_cycle,
                    'calculation_method': 'not_found',
                    'retrograde_accounted': True
                }
                
        except Exception as e:
            # Fallback to linear estimate if search fails
            return {
                'exact_transit_date': 'Calculation error',
                'days_until_transit': None,
                'years_until_transit': None,
                'is_next_cycle': False,
                'calculation_method': 'error',
                'error': str(e)
            }
    
    def calculate_mrityu_bhaga(self) -> Dict[str, Any]:
        """Check if planets or Lagna fall on Death Degree (Mrityu Bhaga)"""
        try:
            afflicted_points = []
            
            # Check Ascendant
            asc_long = self.d1_chart.get('ascendant', 0)
            asc_sign = int(asc_long / 30)
            asc_deg = asc_long % 30
            mb_deg = self.MRITYU_BHAGA_DEGREES[asc_sign]
            orb = abs(asc_deg - mb_deg)
            
            if orb <= 1.0:
                afflicted_points.append({
                    'point': 'Ascendant',
                    'degree': round(asc_deg, 2),
                    'mb_degree': mb_deg,
                    'orb': round(orb, 2),
                    'intensity': 'Critical' if orb <= 0.25 else 'High',
                    'impact': 'Structural vulnerability in vitality and self-protection'
                })
            
            # Check Planets
            for planet, data in self.d1_chart.get('planets', {}).items():
                p_sign = data.get('sign')
                p_long = data.get('longitude', 0)
                p_deg = p_long % 30
                mb_deg = self.MRITYU_BHAGA_DEGREES[p_sign]
                orb = abs(p_deg - mb_deg)
                
                if orb <= 1.0:
                    afflicted_points.append({
                        'planet': planet,
                        'house': data.get('house'),
                        'degree': round(p_deg, 2),
                        'mb_degree': mb_deg,
                        'orb': round(orb, 2),
                        'intensity': 'Critical' if orb <= 0.25 else 'Strong',
                        'impact': 'Planet wounded - cannot protect house significations'
                    })
            
            return {
                'point_name': 'Mrityu Bhaga (Death Degree)',
                'has_affliction': len(afflicted_points) > 0,
                'afflicted_points': afflicted_points,
                'source': 'BPHS/Phaladeepika'
            }
        except Exception as e:
            return {'error': f'Mrityu Bhaga calculation failed: {e}'}
    
    def get_all_sniper_points(self) -> Dict[str, Any]:
        """Get all sniper points"""
        return {
            'kharesh': self.calculate_kharesh_point(),
            'navamsa_64th': self.calculate_64th_navamsa(),
            'bhrigu_bindu': self.calculate_bhrigu_bindu(),
            'mrityu_bhaga': self.calculate_mrityu_bhaga()
        }