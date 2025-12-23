import swisseph as swe
from typing import Dict, Any, List
from datetime import datetime, timedelta

class LunationCalculator:
    """Calculates exact New Moons and Full Moons for monthly trend forecasting"""
    
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def calculate_lunations(self, start_date: datetime, end_date: datetime, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """Calculate all lunations (New Moon and Full Moon) in date range"""
        print(f"\n🌙 Calculating lunations from {start_date.date()} to {end_date.date()}")
        lunations = []
        current_date = start_date
        
        while current_date < end_date:
            # Find next New Moon
            new_moon = self._find_next_syzygy(current_date, 0, latitude, longitude)
            if new_moon:
                nm_dt = datetime.fromisoformat(new_moon['datetime'])
                if nm_dt < end_date and not any(l['datetime'] == new_moon['datetime'] for l in lunations):
                    print(f"  ✅ Found New Moon: {new_moon['datetime']}")
                    lunations.append(new_moon)
                    # Move past this lunation
                    current_date = nm_dt + timedelta(days=1)
                    continue
            
            # Find next Full Moon
            full_moon = self._find_next_syzygy(current_date, 180, latitude, longitude)
            if full_moon:
                fm_dt = datetime.fromisoformat(full_moon['datetime'])
                if fm_dt < end_date and not any(l['datetime'] == full_moon['datetime'] for l in lunations):
                    print(f"  ✅ Found Full Moon: {full_moon['datetime']}")
                    lunations.append(full_moon)
                    # Move past this lunation
                    current_date = fm_dt + timedelta(days=1)
                    continue
            
            # If nothing found, move forward 14 days
            current_date += timedelta(days=14)
        
        print(f"  📊 Total lunations found: {len(lunations)}")
        return sorted(lunations, key=lambda x: x['datetime'])
    
    def _find_next_syzygy(self, start_date: datetime, target_diff: float, latitude: float, longitude: float) -> Dict[str, Any]:
        """Find next syzygy with high precision (Newton-Raphson convergence)"""
        
        # 1. Initial Estimate (Move forward to get close)
        jd = swe.julday(start_date.year, start_date.month, start_date.day, start_date.hour + start_date.minute/60.0)
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        
        # Calculate current separation
        current_diff = (moon_pos - sun_pos + 360) % 360
        
        # Calculate degrees to target (Forward only)
        degrees_to_go = (target_diff - current_diff + 360) % 360
        
        # If we are practically ON the target (< 1 degree), assume we want the NEXT one
        if degrees_to_go < 1:
            degrees_to_go += 360
            
        # Moon moves ~12.19 degrees/day relative to Sun
        days_to_add = degrees_to_go / 12.19
        search_date = start_date + timedelta(days=days_to_add)
        
        # 2. Refine with Iteration
        for _ in range(20):
            jd = swe.julday(search_date.year, search_date.month, search_date.day,
                           search_date.hour + search_date.minute/60.0)
            
            sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            
            # Calculate error (Target - Current)
            current_diff = (moon_pos - sun_pos + 360) % 360
            error = (target_diff - current_diff + 180) % 360 - 180
            
            # Check precision (0.001 degrees = ~7 seconds of time)
            if abs(error) < 0.001:
                lunation_type = 'New Moon' if target_diff == 0 else 'Full Moon'
                chart = self._calculate_lunation_chart(search_date, latitude, longitude)
                
                return {
                    'type': lunation_type,
                    'datetime': search_date.isoformat(),
                    'sun_longitude': round(sun_pos, 4),
                    'moon_longitude': round(moon_pos, 4),
                    'nakshatra': self._get_nakshatra(moon_pos),
                    'chart': chart,
                    'paksha': 'Shukla' if lunation_type == 'New Moon' else 'Krishna',
                    'valid_until': (search_date + timedelta(days=14)).isoformat()
                }
            
            # Adjust time: Error / Relative Speed
            search_date += timedelta(days=error / 12.19)
            
        return None
    
    def _calculate_lunation_chart(self, dt: datetime, latitude: float, longitude: float) -> Dict[str, Any]:
        """Calculate chart for lunation moment"""
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
        
        asc_data = swe.houses_ex(jd, latitude, longitude, b'P')
        ascendant = asc_data[0][0]
        
        planets = {}
        planet_ids = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS,
            'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE
        }
        
        for name, planet_id in planet_ids.items():
            pos = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)[0]
            planets[name] = {
                'longitude': round(pos[0], 4),
                'sign': int(pos[0] / 30),
                'house': self._calculate_house(pos[0], ascendant)
            }
        
        planets['Ketu'] = {
            'longitude': round((planets['Rahu']['longitude'] + 180) % 360, 4),
            'sign': int(((planets['Rahu']['longitude'] + 180) % 360) / 30),
            'house': self._calculate_house((planets['Rahu']['longitude'] + 180) % 360, ascendant)
        }
        
        return {
            'ascendant': round(ascendant, 4),
            'planets': planets
        }
    
    def _calculate_house(self, planet_long: float, ascendant: float) -> int:
        asc_sign = int(ascendant / 30)
        planet_sign = int(planet_long / 30)
        return ((planet_sign - asc_sign) % 12) + 1
    
    def _get_nakshatra(self, longitude: float) -> Dict[str, Any]:
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        
        nakshatra_span = 360 / 27
        nak_index = int(longitude / nakshatra_span)
        pada = int((longitude % nakshatra_span) / (nakshatra_span / 4)) + 1
        
        return {
            'name': nakshatras[nak_index % 27],
            'pada': pada
        }
