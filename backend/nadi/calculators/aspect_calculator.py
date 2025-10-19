from typing import Dict, List, Tuple
from ..config.nadi_config import NADI_CONFIG

class NadiAspectCalculator:
    """Calculate degree-based aspects for Nadi astrology"""
    
    def __init__(self):
        self.orbs = NADI_CONFIG['ASPECT_ORBS']
    
    def calculate_aspects(self, natal_planets: Dict, transit_planets: Dict = None) -> List[Dict]:
        """Calculate all Nadi aspects between planets"""
        aspects = []
        planets = transit_planets if transit_planets else natal_planets
        
        # Debug: Print available planets
        print(f"Available natal planets: {list(natal_planets.keys())}")
        print(f"Nadi planets config: {NADI_CONFIG['NADI_PLANETS']}")
        
        for planet1, data1 in natal_planets.items():
            if planet1 not in NADI_CONFIG['NADI_PLANETS']:
                continue
                
            for planet2, data2 in planets.items():
                if planet2 not in NADI_CONFIG['NADI_PLANETS'] or planet1 == planet2:
                    continue
                
                if planet1 == 'Sun' or planet2 == 'Sun':
                    print(f"Checking aspect: {planet1} ({data1['longitude']:.1f}°) -> {planet2} ({data2['longitude']:.1f}°)")
                
                # Check if planet1 aspects planet2
                aspect = self._calculate_single_aspect(
                    planet1, data1['longitude'], 
                    planet2, data2['longitude']
                )
                
                if aspect:
                    aspects.append(aspect)
                    if planet1 == 'Sun' or planet2 == 'Sun':
                        print(f"Found aspect: {aspect}")
                elif planet1 == 'Sun' or planet2 == 'Sun':
                    print(f"No aspect found: {planet1} -> {planet2}")
        
        print(f"Calculated {len(aspects)} aspects")
        return aspects
    
    def _calculate_single_aspect(self, planet1: str, long1: float, planet2: str, long2: float) -> Dict:
        """Calculate Nadi degree-range aspects (Bhrigu Nadi tradition)"""
        deg1 = long1 % 30  # Degree within sign for planet1
        
        if planet1 == 'Sun' or planet2 == 'Sun':
            print(f"  Checking {planet1} at {long1:.1f}° -> {planet2} at {long2:.1f}°")
        
        # Get all aspectual ranges for this planet
        aspect_ranges = self._get_nadi_aspect_ranges(long1, planet1)
        
        for aspect_info in aspect_ranges:
            start_long = aspect_info['start_longitude']
            end_long = aspect_info['end_longitude']
            aspect_type = aspect_info['aspect_type']
            
            # Check if planet2 falls within this aspectual range
            if self._is_in_range(long2, start_long, end_long):
                # Calculate orb from the center of the range
                center_long = (start_long + end_long) / 2
                if end_long < start_long:  # Range crosses 0°
                    center_long = ((start_long + end_long + 360) / 2) % 360
                
                orb = min(abs(long2 - center_long), 360 - abs(long2 - center_long))
                strength = self._get_aspect_strength(orb)
                
                if planet1 == 'Sun' or planet2 == 'Sun':
                    print(f"  Found {aspect_type}: planet2 at {long2:.1f}° in range {start_long:.1f}°-{end_long:.1f}°, orb={orb:.1f}°")
                
                return {
                    'planet1': planet1,
                    'planet2': planet2,
                    'aspect_type': aspect_type,
                    'exact_degree': center_long,
                    'actual_degree': long2,
                    'orb': orb,
                    'strength': strength,
                    'is_applying': True
                }
        
        return None
    
    def _get_nadi_aspect_ranges(self, planet_long: float, planet_name: str) -> List[Dict]:
        """Get all aspectual ranges for a planet (Nadi tradition)"""
        deg = planet_long % 30  # Degree within sign
        ranges = []
        
        # All planets aspect these ranges from their degree
        aspect_offsets = {
            '1st': 0,    # Same sign to next sign (30° range)
            '5th': 120,  # 5th house (trine)
            '7th': 180,  # 7th house (opposition) 
            '9th': 240   # 9th house (trine)
        }
        
        for aspect_name, offset in aspect_offsets.items():
            # Start of range: planet's degree in the aspect sign
            start_long = (planet_long + offset) % 360
            # End of range: same degree in next sign (30° later)
            end_long = (start_long + 30) % 360
            
            ranges.append({
                'aspect_type': f'{aspect_name}_ASPECT',
                'start_longitude': start_long,
                'end_longitude': end_long
            })
        
        return ranges
    
    def _is_in_range(self, longitude: float, start: float, end: float) -> bool:
        """Check if longitude is within range (handles 360° wraparound)"""
        if start <= end:
            return start <= longitude <= end
        else:  # Range crosses 0°
            return longitude >= start or longitude <= end
    

    

    
    def _get_aspect_strength(self, orb: float) -> str:
        """Determine aspect strength based on orb"""
        if orb <= self.orbs['TIGHT']:
            return 'VERY_STRONG'
        elif orb <= self.orbs['MEDIUM']:
            return 'STRONG'
        else:
            return 'MODERATE'
    
    def _is_applying(self, long1: float, long2: float, aspect_degree: float) -> bool:
        """Check if aspect is applying or separating"""
        # Simplified - in real implementation would need planet speeds
        return True