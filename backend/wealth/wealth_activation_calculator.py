from datetime import datetime, timedelta
from typing import Dict, List, Optional
from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator

class WealthActivationCalculator:
    """Calculate wealth-specific planetary activations using real astronomical data"""
    
    def __init__(self):
        self.real_calculator = RealTransitCalculator()
        self.dasha_calculator = DashaCalculator()
        
        # Wealth-significant planets and houses
        self.wealth_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        self.wealth_houses = [2, 5, 9, 11]  # Primary wealth houses
        self.supporting_wealth_houses = [1, 4, 7, 10]  # Supporting wealth houses
        
        # Vedic aspects for each planet
        self.vedic_aspects = {
            'Sun': [1, 7], 'Moon': [1, 7], 'Mars': [1, 4, 7, 8],
            'Mercury': [1, 7], 'Jupiter': [1, 5, 7, 9], 'Venus': [1, 7],
            'Saturn': [1, 3, 7, 10], 'Rahu': [1, 5, 7, 9], 'Ketu': [1, 5, 7, 9]
        }
        
        # Planet-wealth system mapping
        self.planet_wealth_systems = {
            'Sun': ['authority_wealth', 'government_income', 'leadership_positions'],
            'Moon': ['public_wealth', 'liquid_assets', 'real_estate'],
            'Mars': ['property_wealth', 'sports_income', 'engineering_business'],
            'Mercury': ['business_wealth', 'communication_income', 'trade_commerce'],
            'Jupiter': ['wisdom_wealth', 'teaching_income', 'dharmic_gains'],
            'Venus': ['luxury_wealth', 'arts_income', 'beauty_business'],
            'Saturn': ['slow_wealth', 'hard_work_income', 'mining_labor'],
            'Rahu': ['foreign_wealth', 'technology_income', 'sudden_gains'],
            'Ketu': ['spiritual_wealth', 'research_income', 'hidden_assets']
        }
    
    def calculate_wealth_activations(self, birth_data: Dict, years_ahead: int = 2) -> List[Dict]:
        """Calculate wealth activations using classical dasha-first approach"""
        activations = []
        
        # Step 1: Get all dasha change windows for next 2 years
        start_date = datetime.now()
        end_date = start_date + timedelta(days=365 * years_ahead)
        
        dasha_windows = self._get_all_dasha_windows(birth_data, start_date, end_date)
        print(f"Found {len(dasha_windows)} wealth dasha windows")
        
        # Step 2: For each dasha window, check transit activations
        for window in dasha_windows:
            window_activations = self._find_wealth_transit_activations_in_window(birth_data, window)
            activations.extend(window_activations)
        
        # Sort by date
        activations.sort(key=lambda x: x['activation_date'])
        
        print(f"Total wealth activations: {len(activations)}")
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
    
    def _find_wealth_transit_activations_in_window(self, birth_data: Dict, window: Dict) -> List[Dict]:
        """Find wealth transit activations within a dasha window"""
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
            natal_relationships = self._find_wealth_natal_relationships(active_planet, natal_positions)
            
            # For each natal relationship, check if transit forms aspect during this window
            for natal_planet, natal_house in natal_relationships:
                transit_periods = self._find_wealth_transit_aspects_in_period(
                    birth_data, active_planet, natal_planet, 
                    window['start_date'], window['end_date']
                )
                
                for period in transit_periods:
                    activation = self._create_wealth_activation_from_window(
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
    
    def _find_wealth_natal_relationships(self, active_planet: str, natal_positions: Dict) -> List[tuple]:
        """Find natal planets that active planet was related to for wealth"""
        relationships = []
        
        if active_planet not in natal_positions:
            return relationships
            
        ascendant_longitude = natal_positions.get('ascendant_longitude', 0)
        active_house = self.real_calculator.calculate_house_from_longitude(
            natal_positions[active_planet]['longitude'], ascendant_longitude
        )
        
        # Check aspects to all other planets, prioritizing wealth planets
        for natal_planet, pos_data in natal_positions.items():
            if natal_planet == active_planet or natal_planet == 'ascendant_longitude':
                continue
                
            natal_house = self.real_calculator.calculate_house_from_longitude(
                pos_data['longitude'], ascendant_longitude
            )
            
            # Prioritize wealth houses and wealth planets
            is_wealth_relevant = (
                natal_house in self.wealth_houses or 
                natal_house in self.supporting_wealth_houses or
                natal_planet in ['Jupiter', 'Venus', 'Mercury', 'Sun']
            )
            
            if is_wealth_relevant:
                # Check if active planet aspects this natal planet
                available_aspects = self.vedic_aspects.get(active_planet, [])
                for aspect_num in available_aspects:
                    if self._natal_aspect_exists(active_planet, natal_planet, aspect_num, natal_positions):
                        relationships.append((natal_planet, natal_house))
                        break
        
        return relationships
    
    def _find_wealth_transit_aspects_in_period(self, birth_data: Dict, transit_planet: str, natal_planet: str, start_date: str, end_date: str) -> List[Dict]:
        """Find when transit planet aspects natal planet during period for wealth"""
        # For wealth analysis, focus on major wealth planets
        wealth_relevant_planets = ['Jupiter', 'Venus', 'Mercury', 'Sun', 'Saturn']
        
        if (transit_planet in wealth_relevant_planets and natal_planet in self.wealth_planets):
            return [{
                'start_date': start_date,
                'end_date': end_date,
                'aspect_type': '7th_house'  # Default aspect
            }]
        return []
    
    def _create_wealth_activation_from_window(self, transit_planet: str, natal_planet: str, natal_house: int, period: Dict, window: Dict) -> Optional[Dict]:
        """Create wealth activation from window data"""
        try:
            # Calculate strength based on wealth significance
            strength = 50  # Base strength
            
            # Wealth planets get higher strength
            if transit_planet in ['Jupiter', 'Venus']:
                strength += 25
            elif transit_planet in ['Mercury', 'Sun']:
                strength += 20
            elif transit_planet == 'Saturn':
                strength += 15
                
            # Wealth houses increase significance
            if natal_house in self.wealth_houses:
                strength += 20
            elif natal_house in self.supporting_wealth_houses:
                strength += 10
                
            # Wealth planet combinations
            if natal_planet in ['Jupiter', 'Venus', 'Mercury']:
                strength += 15
                
            return {
                'activation_date': period['start_date'],
                'end_date': period['end_date'],
                'transit_planet': transit_planet,
                'natal_planet': natal_planet,
                'aspect_type': period['aspect_type'],
                'natal_house': natal_house,
                'activation_strength': min(strength, 100),
                'wealth_systems': self._get_affected_wealth_systems(transit_planet, natal_planet),
                'description': f'Transit {transit_planet} aspects natal {natal_planet} in {natal_house}th house for wealth',
                'active_dasha': window['dasha_key']
            }
        except:
            return None
    
    def _dasha_matches_3_levels(self, dasha1: Dict, dasha2: Dict) -> bool:
        """Check if two dashas match at first 3 levels"""
        return (
            dasha1.get('mahadasha', {}).get('planet') == dasha2.get('mahadasha', {}).get('planet') and
            dasha1.get('antardasha', {}).get('planet') == dasha2.get('antardasha', {}).get('planet') and
            dasha1.get('pratyantardasha', {}).get('planet') == dasha2.get('pratyantardasha', {}).get('planet')
        )
    
    def _get_affected_wealth_systems(self, transit_planet: str, natal_planet: str) -> List[str]:
        """Get wealth systems affected by planetary combination"""
        systems = set()
        
        # Add systems from both planets
        systems.update(self.planet_wealth_systems.get(transit_planet, []))
        systems.update(self.planet_wealth_systems.get(natal_planet, []))
        
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