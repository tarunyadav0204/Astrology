from .base_calculator import BaseCalculator

class ArgalaCalculator(BaseCalculator):
    """Calculate Argala (planetary interventions) using real Vedic calculations"""
    
    def __init__(self, birth_data=None, chart_data=None):
        super().__init__(birth_data, chart_data)
        
        # Initialize Shadbala calculator for real strength calculations
        from .shadbala_calculator import ShadbalaCalculator
        from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
        
        self.shadbala_calc = ShadbalaCalculator(birth_data, chart_data)
        self.dignities_calc = PlanetaryDignitiesCalculator(birth_data, chart_data)
        
        # Get real planetary strengths
        self.shadbala_data = self.shadbala_calc.calculate_shadbala()
        self.dignities_data = self.dignities_calc.calculate_planetary_dignities()
    
    def calculate_argala_analysis(self):
        """Calculate complete Argala analysis using real planetary strengths"""
        planets = self.chart_data.get('planets', {})
        argala_analysis = {}
        
        for house_num in range(1, 13):
            house_analysis = {
                'house_number': house_num,
                'argala_planets': self._get_argala_planets(house_num, planets),
                'virodha_argala_planets': self._get_virodha_argala_planets(house_num, planets),
                'net_argala_strength': 0,
                'argala_grade': 'Neutral'
            }
            
            # Calculate net argala using real strengths
            argala_strength = sum(p['real_strength'] for p in house_analysis['argala_planets'])
            virodha_strength = sum(p['real_strength'] for p in house_analysis['virodha_argala_planets'])
            house_analysis['net_argala_strength'] = round(argala_strength - virodha_strength, 2)
            house_analysis['argala_grade'] = self._get_argala_grade(house_analysis['net_argala_strength'])
            
            argala_analysis[house_num] = house_analysis
        
        return argala_analysis
    
    def _get_argala_planets(self, target_house, planets):
        """Get planets creating Argala using real planetary strengths"""
        argala_planets = []
        
        # Authentic Jaimini Argala: 2nd, 4th, 11th from target house
        argala_house_offsets = [1, 3, 10]  # 2nd, 4th, 11th (0-indexed)
        
        for offset in argala_house_offsets:
            argala_house = ((target_house - 1 + offset) % 12) + 1
            
            for planet_name, planet_data in planets.items():
                if planet_name in ['Gulika', 'Mandi']:
                    continue
                    
                planet_house = planet_data.get('house', 1)
                
                if planet_house == argala_house:
                    # Use real Shadbala strength
                    real_strength = self._get_real_planet_strength(planet_name)
                    argala_planets.append({
                        'planet': planet_name,
                        'house': argala_house,
                        'argala_type': self._get_argala_type(offset),
                        'real_strength': real_strength,
                        'shadbala_rupas': self.shadbala_data.get(planet_name, {}).get('total_rupas', 0),
                        'dignity': self.dignities_data.get(planet_name, {}).get('dignity', 'neutral')
                    })
        
        return argala_planets
    
    def _get_virodha_argala_planets(self, target_house, planets):
        """Get planets creating Virodha Argala using real strengths"""
        virodha_planets = []
        
        # Authentic Virodha Argala: 12th, 10th, 3rd from Argala houses
        virodha_offsets = [11, 9, 2]  # 12th, 10th, 3rd (0-indexed)
        
        for i, offset in enumerate(virodha_offsets):
            virodha_house = ((target_house - 1 + offset) % 12) + 1
            
            for planet_name, planet_data in planets.items():
                if planet_name in ['Gulika', 'Mandi']:
                    continue
                    
                planet_house = planet_data.get('house', 1)
                
                if planet_house == virodha_house:
                    # Use real Shadbala strength
                    real_strength = self._get_real_planet_strength(planet_name)
                    virodha_planets.append({
                        'planet': planet_name,
                        'house': virodha_house,
                        'virodha_type': self._get_virodha_type(i),
                        'real_strength': real_strength,
                        'shadbala_rupas': self.shadbala_data.get(planet_name, {}).get('total_rupas', 0),
                        'dignity': self.dignities_data.get(planet_name, {}).get('dignity', 'neutral')
                    })
        
        return virodha_planets
    
    def _get_real_planet_strength(self, planet_name):
        """Get real planetary strength from Shadbala and dignities"""
        # Base strength from Shadbala (in rupas)
        shadbala_rupas = self.shadbala_data.get(planet_name, {}).get('total_rupas', 0)
        
        # Dignity multiplier from real calculations
        dignity_multiplier = self.dignities_data.get(planet_name, {}).get('strength_multiplier', 1.0)
        
        # Convert to Argala strength scale (0-100)
        # Shadbala average is ~5 rupas, excellent is 6+
        argala_strength = (shadbala_rupas * 10) * dignity_multiplier
        
        return round(min(100, max(0, argala_strength)), 2)
    
    def _get_argala_type(self, offset):
        """Get authentic Argala type"""
        argala_types = {1: '2nd House Argala', 3: '4th House Argala', 10: '11th House Argala'}
        return argala_types.get(offset, 'Unknown Argala')
    
    def _get_virodha_type(self, index):
        """Get authentic Virodha Argala type"""
        virodha_types = {0: '12th House Virodha', 1: '10th House Virodha', 2: '3rd House Virodha'}
        return virodha_types.get(index, 'Unknown Virodha')
    
    def _get_argala_grade(self, net_strength):
        """Get Argala grade based on real strength thresholds"""
        if net_strength >= 50:
            return 'Very Strong Support'
        elif net_strength >= 25:
            return 'Strong Support'
        elif net_strength >= 10:
            return 'Good Support'
        elif net_strength >= -10:
            return 'Neutral'
        elif net_strength >= -25:
            return 'Mild Obstruction'
        elif net_strength >= -50:
            return 'Strong Obstruction'
        else:
            return 'Very Strong Obstruction'
    
    def get_career_argala_analysis(self):
        """Get Argala analysis for career houses using real calculations"""
        full_analysis = self.calculate_argala_analysis()
        career_houses = [10, 2, 6, 11]  # Career, wealth, service, gains
        
        career_argala = {}
        for house in career_houses:
            career_argala[house] = full_analysis[house]
        
        return career_argala
    

    
    def get_career_argala_analysis(self):
        """Get Argala analysis specifically for career houses (10th, 2nd, 6th, 11th)"""
        full_analysis = self.calculate_argala_analysis()
        career_houses = [10, 2, 6, 11]
        
        career_argala = {}
        for house in career_houses:
            career_argala[house] = full_analysis[house]
        
        return career_argala