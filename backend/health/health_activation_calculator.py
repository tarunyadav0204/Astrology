from datetime import datetime, timedelta
from typing import Dict, List, Optional
from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator

class HealthActivationCalculator:
    """Calculate health-specific planetary activations using real astronomical data"""
    
    def __init__(self):
        self.real_calculator = RealTransitCalculator()
        self.dasha_calculator = DashaCalculator()
        
        # Health-significant planets and houses
        self.health_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        self.health_houses = [1, 6, 8, 12]  # Body, disease, chronic illness, hospitalization
        
        # Vedic aspects for each planet
        self.vedic_aspects = {
            'Sun': [1, 7], 'Moon': [1, 7], 'Mars': [1, 4, 7, 8],
            'Mercury': [1, 7], 'Jupiter': [1, 5, 7, 9], 'Venus': [1, 7],
            'Saturn': [1, 3, 7, 10], 'Rahu': [1, 5, 7, 9], 'Ketu': [1, 5, 7, 9]
        }
        
        # Planet-health system mapping
        self.planet_health_systems = {
            'Sun': ['heart', 'circulation', 'vitality', 'bones', 'spine'],
            'Moon': ['mind', 'emotions', 'fluids', 'stomach', 'reproductive'],
            'Mars': ['blood', 'muscles', 'accidents', 'surgery', 'inflammation'],
            'Mercury': ['nervous_system', 'communication', 'respiratory', 'skin'],
            'Jupiter': ['liver', 'fat', 'growth', 'immunity', 'wisdom'],
            'Venus': ['kidneys', 'reproductive', 'beauty', 'harmony', 'diabetes'],
            'Saturn': ['bones', 'joints', 'chronic_disease', 'aging', 'discipline'],
            'Rahu': ['sudden_events', 'poison', 'mental_disorders', 'epidemics'],
            'Ketu': ['spiritual_health', 'detachment', 'mysterious_illness', 'moksha']
        }
    
    def calculate_health_activations(self, birth_data: Dict, years_ahead: int = 2) -> List[Dict]:
        """Calculate health activations using classical dasha-first approach"""
        activations = []
        
        # Step 1: Get all dasha change windows for Jul-Sep 2025 only
        start_date = datetime(2025, 7, 1)
        end_date = datetime(2025, 9, 30)
        
        dasha_windows = self._get_all_dasha_windows(birth_data, start_date, end_date)
        print(f"Found {len(dasha_windows)} dasha windows")
        
        # Step 2: For each dasha window, check transit activations
        for window in dasha_windows:
            window_activations = self._find_transit_activations_in_window(birth_data, window)
            activations.extend(window_activations)
        
        # Sort by date
        activations.sort(key=lambda x: x['activation_date'])
        
        print(f"\nTotal health activations: {len(activations)}")
        return activations
    
    def _get_all_dasha_windows(self, birth_data: Dict, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all dasha change windows in the time period"""
        windows = []
        current_date = start_date
        
        while current_date <= end_date:
            current_dasha = self.dasha_calculator.calculate_dashas_for_date(current_date, birth_data)
            
            if current_dasha:
                # Find window boundaries for this dasha combination
                window_start, window_end = self._find_dasha_window_boundaries(birth_data, current_date, current_dasha)
                
                dasha_key = f"{current_dasha.get('mahadasha', {}).get('planet')}-{current_dasha.get('antardasha', {}).get('planet')}-{current_dasha.get('pratyantardasha', {}).get('planet')}"
                
                # Avoid duplicates
                if not any(w.get('dasha_key') == dasha_key and w.get('start_date') == window_start.strftime('%Y-%m-%d') for w in windows):
                    windows.append({
                        'start_date': window_start.strftime('%Y-%m-%d'),
                        'end_date': window_end.strftime('%Y-%m-%d'),
                        'dasha_key': dasha_key,
                        'active_planets': [
                            current_dasha.get('mahadasha', {}).get('planet'),
                            current_dasha.get('antardasha', {}).get('planet'),
                            current_dasha.get('pratyantardasha', {}).get('planet')
                        ]
                    })
            
            current_date += timedelta(days=30)  # Check monthly
        
        return windows
    
    def _find_transit_activations_in_window(self, birth_data: Dict, window: Dict) -> List[Dict]:
        """Find transit activations within a dasha window"""
        activations = []
        
        # Get natal positions
        natal_positions = self.real_calculator._calculate_natal_positions(birth_data)
        if not natal_positions:
            return []
        
        # Check each active planet in the dasha
        for active_planet in window['active_planets']:
            if not active_planet or active_planet == 'Unknown':
                continue
                
            # Find natal planets this active planet was related to
            natal_relationships = self._find_natal_relationships(active_planet, natal_positions)
            
            # For each natal relationship, check if transit forms aspect during this window
            for natal_planet, natal_house in natal_relationships:
                transit_periods = self._find_transit_aspects_in_period(
                    birth_data, active_planet, natal_planet, 
                    window['start_date'], window['end_date']
                )
                
                for period in transit_periods:
                    activation = self._create_health_activation_from_window(
                        active_planet, natal_planet, natal_house, period, window
                    )
                    if activation:
                        activations.append(activation)
        
        return activations
    
    def _find_dasha_window_boundaries(self, birth_data: Dict, reference_date: datetime, current_dasha: Dict) -> tuple:
        """Find start and end dates for current dasha window"""
        # Search backwards for start
        start_date = reference_date
        test_date = reference_date - timedelta(days=1)
        while test_date >= reference_date - timedelta(days=90):
            test_dasha = self.dasha_calculator.calculate_dashas_for_date(test_date, birth_data)
            if not test_dasha or not self._dasha_matches_3_levels(current_dasha, test_dasha):
                break
            start_date = test_date
            test_date -= timedelta(days=1)
        
        # Search forwards for end
        end_date = reference_date
        test_date = reference_date + timedelta(days=1)
        while test_date <= reference_date + timedelta(days=90):
            test_dasha = self.dasha_calculator.calculate_dashas_for_date(test_date, birth_data)
            if not test_dasha or not self._dasha_matches_3_levels(current_dasha, test_dasha):
                break
            end_date = test_date
            test_date += timedelta(days=1)
        
        return start_date, end_date
    
    def _find_natal_relationships(self, active_planet: str, natal_positions: Dict) -> List[tuple]:
        """Find natal planets that active planet was related to"""
        relationships = []
        
        if active_planet not in natal_positions:
            return relationships
            
        ascendant_longitude = natal_positions.get('ascendant_longitude', 0)
        active_house = self.real_calculator.calculate_house_from_longitude(
            natal_positions[active_planet]['longitude'], ascendant_longitude
        )
        
        # Check aspects to all other planets
        for natal_planet, pos_data in natal_positions.items():
            if natal_planet == active_planet or natal_planet == 'ascendant_longitude':
                continue
                
            natal_house = self.real_calculator.calculate_house_from_longitude(
                pos_data['longitude'], ascendant_longitude
            )
            
            # Check if active planet aspects this natal planet
            available_aspects = self.vedic_aspects.get(active_planet, [])
            for aspect_num in available_aspects:
                if self._natal_aspect_exists(active_planet, natal_planet, aspect_num, natal_positions):
                    relationships.append((natal_planet, natal_house))
                    break
        
        return relationships
    
    def _find_transit_aspects_in_period(self, birth_data: Dict, transit_planet: str, natal_planet: str, start_date: str, end_date: str) -> List[Dict]:
        """Find when transit planet aspects natal planet during period"""
        # For now, return a simple period if planets are health-relevant
        if (transit_planet in self.health_planets and natal_planet in self.health_planets):
            return [{
                'start_date': start_date,
                'end_date': end_date,
                'aspect_type': '7th_house'  # Default aspect
            }]
        return []
    
    def _create_health_activation_from_window(self, transit_planet: str, natal_planet: str, natal_house: int, period: Dict, window: Dict) -> Optional[Dict]:
        """Create activation from window data"""
        try:
            # Calculate strength
            strength = 60  # Base strength
            if transit_planet in ['Saturn', 'Jupiter']:
                strength += 20
            if natal_house in [1, 6, 8, 12]:
                strength += 15
                
            return {
                'activation_date': period['start_date'],
                'end_date': period['end_date'],
                'transit_planet': transit_planet,
                'natal_planet': natal_planet,
                'aspect_type': period['aspect_type'],
                'natal_house': natal_house,
                'activation_strength': min(strength, 100),
                'health_systems': self._get_affected_health_systems(transit_planet, natal_planet),
                'description': f'Transit {transit_planet} aspects natal {natal_planet} in {natal_house}th house',
                'active_dasha': window['dasha_key']
            }
        except:
            return None
    
    def _dasha_matches_3_levels(self, dasha1: Dict, dasha2: Dict) -> bool:
        """Check if two dashas match at first 3 levels (maha, antar, pratyantar)"""
        return (
            dasha1.get('mahadasha', {}).get('planet') == dasha2.get('mahadasha', {}).get('planet') and
            dasha1.get('antardasha', {}).get('planet') == dasha2.get('antardasha', {}).get('planet') and
            dasha1.get('pratyantardasha', {}).get('planet') == dasha2.get('pratyantardasha', {}).get('planet')
        )
    
    def _dasha_matches(self, dasha1: Dict, dasha2: Dict) -> bool:
        """Check if two dasha combinations match at all 5 levels"""
        return (
            dasha1.get('mahadasha', {}).get('planet') == dasha2.get('mahadasha', {}).get('planet') and
            dasha1.get('antardasha', {}).get('planet') == dasha2.get('antardasha', {}).get('planet') and
            dasha1.get('pratyantardasha', {}).get('planet') == dasha2.get('pratyantardasha', {}).get('planet') and
            dasha1.get('sookshma', {}).get('planet') == dasha2.get('sookshma', {}).get('planet') and
            dasha1.get('prana', {}).get('planet') == dasha2.get('prana', {}).get('planet')
        )
    
    def _calculate_period_intersection(self, transit_period: Dict, dasha_period: Dict) -> Optional[Dict]:
        """Calculate intersection between transit period and dasha period"""
        transit_start = datetime.strptime(transit_period['start_date'], '%Y-%m-%d')
        transit_end = datetime.strptime(transit_period['end_date'], '%Y-%m-%d')
        dasha_start = datetime.strptime(dasha_period['start_date'], '%Y-%m-%d')
        dasha_end = datetime.strptime(dasha_period['end_date'], '%Y-%m-%d')
        
        # Calculate intersection
        intersection_start = max(transit_start, dasha_start)
        intersection_end = min(transit_end, dasha_end)
        
        if intersection_start <= intersection_end:
            return {
                'start_date': intersection_start.strftime('%Y-%m-%d'),
                'end_date': intersection_end.strftime('%Y-%m-%d'),
                'peak_date': intersection_start.strftime('%Y-%m-%d'),
                'aspect_type': transit_period.get('aspect_type'),
                'transit_house': transit_period.get('transit_house'),
                'natal_house': transit_period.get('natal_house')
            }
        
        return None
    
    def _create_health_activation(self, aspect: Dict, period: Dict, dasha_info: str = None) -> Optional[Dict]:
        """Create health activation from aspect and timeline period"""
        try:
            transit_planet = aspect['transit_planet']
            natal_planet = aspect['natal_planet']
            aspect_number = aspect['aspect_number']
            natal_house = aspect['natal_house']
            
            # Calculate activation strength based on planets and houses involved
            strength = self._calculate_activation_strength(aspect)
            
            # Determine health significance
            health_systems = self._get_affected_health_systems(transit_planet, natal_planet)
            
            # Create activation entry
            activation = {
                'activation_date': period['start_date'],
                'end_date': period['end_date'],
                'transit_planet': transit_planet,
                'natal_planet': natal_planet,
                'aspect_type': f'{aspect_number}th_house',
                'natal_house': natal_house,
                'activation_strength': strength,
                'health_systems': health_systems,
                'description': f'Transit {transit_planet} {aspect_number}th house aspect to natal {natal_planet} in {natal_house}th house',
                'health_significance': self._determine_health_significance(aspect, strength)
            }
            
            if dasha_info:
                activation['active_dasha'] = dasha_info
            
            return activation
            
        except Exception as e:
            pass
            return None
    
    def _calculate_activation_strength(self, aspect: Dict) -> int:
        """Calculate activation strength based on classical Vedic principles"""
        base_strength = 50
        
        transit_planet = aspect['transit_planet']
        natal_planet = aspect['natal_planet']
        aspect_number = aspect['aspect_number']
        natal_house = aspect['natal_house']
        
        # Slow-moving planets create stronger activations
        if transit_planet in ['Jupiter', 'Saturn']:
            base_strength += 20
        elif transit_planet in ['Rahu', 'Ketu']:
            base_strength += 15
        elif transit_planet == 'Mars':
            base_strength += 10
        
        # Certain aspects are more powerful
        if aspect_number in [1, 7]:  # Conjunction and opposition
            base_strength += 15
        elif aspect_number in [4, 8, 10]:  # Mars/Saturn special aspects
            base_strength += 10
        elif aspect_number in [5, 9]:  # Jupiter special aspects
            base_strength += 8
        
        # Health houses increase significance
        if natal_house in [1, 6, 8, 12]:
            base_strength += 15
        
        # Luminaries (Sun/Moon) involvement
        if natal_planet in ['Sun', 'Moon']:
            base_strength += 10
        
        return min(base_strength, 100)  # Cap at 100
    
    def _get_affected_health_systems(self, transit_planet: str, natal_planet: str) -> List[str]:
        """Get health systems affected by planetary combination"""
        systems = set()
        
        # Add systems from both planets
        systems.update(self.planet_health_systems.get(transit_planet, []))
        systems.update(self.planet_health_systems.get(natal_planet, []))
        
        return list(systems)
    
    def _natal_aspect_exists(self, planet1: str, planet2: str, aspect_number: int, natal_positions: Dict) -> bool:
        """Check if aspect existed in natal chart"""
        if planet1 not in natal_positions or planet2 not in natal_positions:
            return False
        
        # Get natal house positions
        ascendant_longitude = natal_positions.get('ascendant_longitude', 0)
        
        planet1_house = self.real_calculator.calculate_house_from_longitude(
            natal_positions[planet1]['longitude'], ascendant_longitude
        )
        planet2_house = self.real_calculator.calculate_house_from_longitude(
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
                # Calculate target house for this aspect
                target_house = ((planet1_house + test_aspect - 2) % 12) + 1
                if target_house == planet2_house and aspect_number == test_aspect:
                    return True
        
        return False
    
    def _determine_health_significance(self, aspect: Dict, strength: int) -> str:
        """Determine health significance level"""
        if strength >= 80:
            return 'high'
        elif strength >= 60:
            return 'medium'
        else:
            return 'low'