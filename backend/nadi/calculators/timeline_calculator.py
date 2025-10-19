from datetime import datetime, timedelta
from typing import Dict, List
import swisseph as swe
from ..config.nadi_config import NADI_CONFIG

class NadiTimelineCalculator:
    """Calculate when aspects occur in time"""
    
    def __init__(self):
        self.time_range = NADI_CONFIG['TIME_RANGE']
        self.step_days = NADI_CONFIG['TRANSIT_SETTINGS']['CALCULATION_STEP_DAYS']
    
    def calculate_aspect_timeline(self, natal_planets: Dict, aspect_type: str, planet1: str, planet2: str) -> List[Dict]:
        """Calculate when specific aspect occurs between two planets (full range)"""
        return self.calculate_aspect_timeline_range(natal_planets, aspect_type, planet1, planet2, 
                                                   datetime.now().year - self.time_range['PAST_YEARS'], 
                                                   self.time_range['PAST_YEARS'] + self.time_range['FUTURE_YEARS'])
    
    def calculate_aspect_timeline_range(self, natal_planets: Dict, aspect_type: str, planet1: str, planet2: str, 
                                       start_year: int, year_range: int) -> List[Dict]:
        """Calculate timeline for Nadi degree-range aspects"""
        print(f"Timeline calc: aspect_type={aspect_type}, planet1={planet1}, planet2={planet2}, year={start_year}")
        
        timeline = []
        
        # Calculate date range for specific years only
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(start_year + year_range, 12, 31)
        
        current_date = start_date
        
        # Get the aspectual range for this Nadi aspect
        aspect_range = self._get_nadi_aspect_range(natal_planets[planet1]['longitude'], aspect_type)
        if not aspect_range:
            print(f"No aspect range found for {aspect_type}")
            return []
        
        print(f"Aspect range: {aspect_range['start_longitude']:.1f}° to {aspect_range['end_longitude']:.1f}°")
        
        # Use weekly steps for faster calculation
        step_days = 7  # Weekly instead of daily
        
        while current_date <= end_date:
            # Get transit positions for this date
            transit_positions = self._get_transit_positions(current_date)
            
            if planet2 in transit_positions:
                transit_long = transit_positions[planet2]
                
                # Check if transit planet is within the aspectual range
                if self._is_in_aspect_range(transit_long, aspect_range):
                    # Calculate orb from center of range
                    center_long = aspect_range['center_longitude']
                    orb_diff = min(abs(transit_long - center_long), 360 - abs(transit_long - center_long))
                    
                    timeline.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'orb': orb_diff,
                        'exact': orb_diff <= 1,
                        'strength': self._get_strength_from_orb(orb_diff)
                    })
                    print(f"Found aspect on {current_date.strftime('%Y-%m-%d')}: transit at {transit_long:.1f}°, orb={orb_diff:.1f}°")
            
            current_date += timedelta(days=step_days)
        
        consolidated = self._consolidate_periods(timeline)
        print(f"Timeline calculation complete: {len(timeline)} entries -> {len(consolidated)} periods")
        return consolidated
    
    def _get_nadi_aspect_range(self, planet_long: float, aspect_type: str) -> Dict:
        """Get the aspectual range for a Nadi aspect"""
        aspect_offsets = {
            '1st_ASPECT': 0,
            '2nd_ASPECT': 30,
            '5th_ASPECT': 120,
            '6th_ASPECT': 150,
            '7th_ASPECT': 180,
            '9th_ASPECT': 240
        }
        
        if aspect_type not in aspect_offsets:
            return None
            
        offset = aspect_offsets[aspect_type]
        start_long = (planet_long + offset) % 360
        end_long = (start_long + 30) % 360
        center_long = (start_long + 15) % 360
        
        return {
            'start_longitude': start_long,
            'end_longitude': end_long,
            'center_longitude': center_long
        }
    
    def _is_in_aspect_range(self, longitude: float, aspect_range: Dict) -> bool:
        """Check if longitude is within aspectual range"""
        start = aspect_range['start_longitude']
        end = aspect_range['end_longitude']
        
        if start <= end:
            return start <= longitude <= end
        else:  # Range crosses 0°
            return longitude >= start or longitude <= end
    
    def _get_transit_positions(self, date: datetime) -> Dict[str, float]:
        """Get planetary positions for given date"""
        positions = {}
        jd = swe.julday(date.year, date.month, date.day, 12.0)
        
        planet_map = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN
        }
        
        for planet_name, planet_id in planet_map.items():
            try:
                result = swe.calc_ut(jd, planet_id)
                positions[planet_name] = result[0][0]
            except:
                continue
        
        return positions
    
    def _get_strength_from_orb(self, orb: float) -> str:
        """Get strength category from orb"""
        if orb <= NADI_CONFIG['ASPECT_ORBS']['TIGHT']:
            return 'VERY_STRONG'
        elif orb <= NADI_CONFIG['ASPECT_ORBS']['MEDIUM']:
            return 'STRONG'
        else:
            return 'MODERATE'
    
    def _consolidate_periods(self, timeline: List[Dict]) -> List[Dict]:
        """Consolidate consecutive dates into periods"""
        if not timeline:
            return []
        
        # Sort timeline by date
        timeline.sort(key=lambda x: x['date'])
        
        periods = []
        current_period = {
            'start_date': timeline[0]['date'],
            'end_date': timeline[0]['date'],
            'peak_date': timeline[0]['date'],
            'min_orb': timeline[0]['orb']
        }
        
        for entry in timeline[1:]:
            # Check if dates are within 10 days (allowing for weekly gaps)
            if self._dates_within_range(current_period['end_date'], entry['date'], 10):
                current_period['end_date'] = entry['date']
                if entry['orb'] < current_period['min_orb']:
                    current_period['peak_date'] = entry['date']
                    current_period['min_orb'] = entry['orb']
            else:
                # Gap too large, start new period
                periods.append(current_period)
                current_period = {
                    'start_date': entry['date'],
                    'end_date': entry['date'],
                    'peak_date': entry['date'],
                    'min_orb': entry['orb']
                }
        
        periods.append(current_period)
        return periods
    
    def _dates_within_range(self, date1_str: str, date2_str: str, max_days: int) -> bool:
        """Check if two date strings are within specified range"""
        date1 = datetime.strptime(date1_str, '%Y-%m-%d')
        date2 = datetime.strptime(date2_str, '%Y-%m-%d')
        return (date2 - date1).days <= max_days