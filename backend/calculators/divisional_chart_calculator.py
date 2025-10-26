"""Divisional chart calculator extracted from main.py"""

from .base_calculator import BaseCalculator

class DivisionalChartCalculator(BaseCalculator):
    """Calculate divisional charts using proper Vedic formulas"""
    
    def calculate_divisional_chart(self, division_number=9):
        """Calculate divisional chart - extracted from main.py"""
        
        def get_divisional_sign(sign, degree_in_sign, division):
            """Calculate divisional sign using proper Vedic formulas - extracted from main.py"""
            part = int(degree_in_sign / (30/division))
            
            if division == 9:  # Navamsa (D9)
                # Movable signs (0,3,6,9): Start from same sign
                # Fixed signs (1,4,7,10): Start from 9th sign
                # Dual signs (2,5,8,11): Start from 5th sign
                if sign in [0, 3, 6, 9]:  # Movable signs
                    navamsa_start = sign
                elif sign in [1, 4, 7, 10]:  # Fixed signs
                    navamsa_start = (sign + 8) % 12  # 9th from sign
                else:  # Dual signs [2, 5, 8, 11]
                    navamsa_start = (sign + 4) % 12  # 5th from sign
                return (navamsa_start + part) % 12
            
            elif division == 10:  # Dasamsa (D10)
                return (sign + part) % 12 if sign % 2 == 0 else ((sign + 8) + part) % 12
            
            elif division == 12:  # Dwadasamsa (D12)
                return (sign + part) % 12
            
            elif division == 16:  # Shodasamsa (D16)
                if sign in [0, 3, 6, 9]:  # Movable signs
                    d16_start = 0  # Aries
                elif sign in [1, 4, 7, 10]:  # Fixed signs
                    d16_start = 4  # Leo
                else:  # Dual signs
                    d16_start = 8  # Sagittarius
                return (d16_start + part) % 12
            
            elif division == 20:  # Vimsamsa (D20)
                if sign in [0, 3, 6, 9]:  # Movable signs
                    d20_start = 0  # Aries
                elif sign in [1, 4, 7, 10]:  # Fixed signs
                    d20_start = 8  # Sagittarius
                else:  # Dual signs
                    d20_start = 4  # Leo
                return (d20_start + part) % 12
            
            elif division == 24:  # Chaturvimsamsa (D24)
                return (3 + part) % 12  # Cancer
            
            elif division == 27:  # Saptavimsamsa (D27)
                if sign in [0, 4, 8]:  # Fire signs
                    d27_start = 0  # Aries
                elif sign in [1, 5, 9]:  # Earth signs
                    d27_start = 3  # Cancer
                elif sign in [2, 6, 10]:  # Air signs
                    d27_start = 6  # Libra
                else:  # Water signs [3, 7, 11]
                    d27_start = 9  # Capricorn
                return (d27_start + part) % 12
            
            elif division == 30:  # Trimsamsa (D30)
                if sign % 2 == 1:  # Odd signs
                    if part < 5: return 3  # Mars (0-5 degrees)
                    elif part < 10: return 6  # Saturn (5-10 degrees)
                    elif part < 18: return 4  # Jupiter (10-18 degrees)
                    elif part < 25: return 1  # Mercury (18-25 degrees)
                    else: return 2  # Venus (25-30 degrees)
                else:  # Even signs
                    if part < 5: return 2  # Venus (0-5 degrees)
                    elif part < 12: return 1  # Mercury (5-12 degrees)
                    elif part < 20: return 4  # Jupiter (12-20 degrees)
                    elif part < 25: return 6  # Saturn (20-25 degrees)
                    else: return 3  # Mars (25-30 degrees)
            
            elif division == 40:  # Khavedamsa (D40)
                if sign in [0, 3, 6, 9]:  # Movable signs
                    d40_start = 0  # Aries
                elif sign in [1, 4, 7, 10]:  # Fixed signs
                    d40_start = 4  # Leo
                else:  # Dual signs
                    d40_start = 8  # Sagittarius
                return (d40_start + part) % 12
            
            elif division == 60:  # Shashtyamsa (D60)
                if sign in [0, 3, 6, 9]:  # Movable signs
                    d60_start = 0  # Aries
                elif sign in [1, 4, 7, 10]:  # Fixed signs
                    d60_start = 4  # Leo
                else:  # Dual signs
                    d60_start = 8  # Sagittarius
                return (d60_start + part) % 12
            
            else:
                # Default calculation for other divisions
                return (sign + part) % 12
        
        # Calculate divisional chart
        divisional_data = {
            'planets': {},
            'houses': [],
            'ayanamsa': self.chart_data.get('ayanamsa', 0)
        }
        
        # Calculate divisional ascendant
        asc_sign = int(self.chart_data['ascendant'] / 30)
        asc_degree = self.chart_data['ascendant'] % 30
        divisional_asc_sign = get_divisional_sign(asc_sign, asc_degree, division_number)
        divisional_data['ascendant'] = divisional_asc_sign * 30 + 15  # Middle of sign
        
        # Calculate divisional houses
        for i in range(12):
            house_sign = (divisional_asc_sign + i) % 12
            divisional_data['houses'].append({
                'longitude': house_sign * 30,
                'sign': house_sign
            })
        
        # Calculate divisional positions for planets
        planets_to_process = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for planet in planets_to_process:
            if planet in self.chart_data['planets']:
                planet_data = self.chart_data['planets'][planet]
                
                # Regular planetary divisional calculation
                planet_sign = int(planet_data['longitude'] / 30)
                planet_degree = planet_data['longitude'] % 30
                
                divisional_sign = get_divisional_sign(planet_sign, planet_degree, division_number)
                
                # Calculate the actual degree within the divisional sign
                part_size = 30.0 / division_number
                part_index = int(planet_degree / part_size)
                degree_within_part = planet_degree % part_size
                # Scale the degree within part to full sign (0-30 degrees)
                actual_degree = (degree_within_part / part_size) * 30.0
                
                divisional_longitude = divisional_sign * 30 + actual_degree
                
                divisional_data['planets'][planet] = {
                    'longitude': divisional_longitude,
                    'sign': divisional_sign,
                    'degree': actual_degree,
                    'retrograde': planet_data.get('retrograde', False)
                }
        
        return {
            'divisional_chart': divisional_data,
            'division_number': division_number,
            'chart_name': f'D{division_number}'
        }
    
    def get_chart_name(self, division_number):
        """Get traditional name for divisional chart"""
        chart_names = {
            1: 'Rasi (D1)', 9: 'Navamsa (D9)', 10: 'Dasamsa (D10)',
            12: 'Dwadasamsa (D12)', 16: 'Shodasamsa (D16)', 20: 'Vimsamsa (D20)',
            24: 'Chaturvimsamsa (D24)', 27: 'Saptavimsamsa (D27)', 30: 'Trimsamsa (D30)',
            40: 'Khavedamsa (D40)', 45: 'Akshavedamsa (D45)', 60: 'Shashtyamsa (D60)'
        }
        return chart_names.get(division_number, f'D{division_number}')
    
    def get_chart_significance(self, division_number):
        """Get significance of divisional chart"""
        significances = {
            1: 'Overall life, personality, general indications',
            9: 'Marriage, dharma, fortune, spiritual inclinations',
            10: 'Career, profession, status, reputation',
            12: 'Parents, ancestry, past life karma',
            16: 'Vehicles, luxuries, happiness, comforts',
            20: 'Spiritual practices, religious activities',
            24: 'Education, learning, knowledge acquisition',
            27: 'Strengths, weaknesses, inherent nature',
            30: 'Evils, misfortunes, diseases, troubles',
            40: 'Maternal relatives, mother\'s family',
            45: 'Paternal relatives, father\'s family',
            60: 'Past life, karmic influences, subtle effects'
        }
        return significances.get(division_number, 'Specific life area analysis')