"""
Jaimini Chart Calculator - Karkamsa and Swamsa Charts

These are derivative charts used in Jaimini astrology that recast 
divisional charts with Atmakaraka's position as the ascendant.

Classical References:
- Jaimini Sutras by Maharishi Jaimini
- Jaimini Upadesa Sutras
"""

from .base_calculator import BaseCalculator
from .divisional_chart_calculator import DivisionalChartCalculator


class JaiminiChartCalculator(BaseCalculator):
    """Calculate Jaimini-specific derivative charts"""
    
    def __init__(self, chart_data, atmakaraka_planet):
        """
        Initialize with chart data and Atmakaraka planet
        
        Args:
            chart_data: D1 chart data with planetary positions
            atmakaraka_planet: Name of Atmakaraka planet (e.g., 'Saturn')
        """
        super().__init__(chart_data)
        self.atmakaraka_planet = atmakaraka_planet
        self.divisional_calc = DivisionalChartCalculator(chart_data)
    
    def calculate_karkamsa_chart(self):
        """
        Calculate Karkamsa Chart - PHYSICAL/MATERIAL dimension
        
        Lagna: Atmakaraka's sign in D9
        Planets: D1 (Rashi) positions mapped to houses from Karkamsa lagna
        
        Returns:
            dict: Karkamsa chart with D1 planets relative to D9 AK sign
        """
        # Step 1: Find Atmakaraka's D9 sign (this becomes the lagna)
        d9_result = self.divisional_calc.calculate_divisional_chart(9)
        d9_chart = d9_result['divisional_chart']
        
        if self.atmakaraka_planet not in d9_chart['planets']:
            raise ValueError(f"Atmakaraka {self.atmakaraka_planet} not found in D9")
        
        karkamsa_sign = d9_chart['planets'][self.atmakaraka_planet]['sign']
        
        print(f"[KARKAMSA] AK {self.atmakaraka_planet} in D9 sign {karkamsa_sign}")
        print(f"[KARKAMSA] Using D1 planet positions:")
        
        # Step 2: Map D1 planets to houses relative to Karkamsa lagna
        karkamsa_chart = self._recast_with_d1_planets(karkamsa_sign)
        
        return {
            'karkamsa_chart': karkamsa_chart,
            'karkamsa_sign': karkamsa_sign,
            'atmakaraka': self.atmakaraka_planet,
            'atmakaraka_degree_in_d9': d9_chart['planets'][self.atmakaraka_planet]['degree'],
            'significance': 'Physical reality and worldly achievements'
        }
    
    def calculate_swamsa_chart(self):
        """
        Calculate Swamsa Chart - SOUL/SPIRITUAL dimension
        
        Lagna: Atmakaraka's sign in D9
        Planets: D9 (Navamsa) positions mapped to houses from Swamsa lagna
        
        Returns:
            dict: Swamsa chart with D9 planets relative to D9 AK sign
        """
        # Step 1: Find Atmakaraka's D9 sign (this becomes the lagna)
        d9_result = self.divisional_calc.calculate_divisional_chart(9)
        d9_chart = d9_result['divisional_chart']
        
        if self.atmakaraka_planet not in d9_chart['planets']:
            raise ValueError(f"Atmakaraka {self.atmakaraka_planet} not found in D9")
        
        swamsa_sign = d9_chart['planets'][self.atmakaraka_planet]['sign']
        
        print(f"[SWAMSA] AK {self.atmakaraka_planet} in D9 sign {swamsa_sign}")
        print(f"[SWAMSA] Using D9 planet positions:")
        
        # Step 2: Map D9 planets to houses relative to Swamsa lagna
        swamsa_chart = self._recast_with_d9_planets(d9_chart, swamsa_sign)
        
        return {
            'swamsa_chart': swamsa_chart,
            'swamsa_sign': swamsa_sign,
            'atmakaraka': self.atmakaraka_planet,
            'atmakaraka_degree_in_d9': d9_chart['planets'][self.atmakaraka_planet]['degree'],
            'significance': "Soul's desire and spiritual evolution"
        }
    
    def _recast_with_d1_planets(self, karkamsa_sign):
        """Map D1 planets to houses from Karkamsa lagna"""
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        chart = {
            'ascendant_sign': karkamsa_sign,
            'ascendant': karkamsa_sign * 30,
            'chart_type': 'Karkamsa',
            'planets': {},
            'houses': [{'house_number': i+1, 'sign': (karkamsa_sign+i)%12} for i in range(12)],
            'ayanamsa': self.chart_data.get('ayanamsa', 0)
        }
        
        for planet, data in self.chart_data['planets'].items():
            planet_sign = data['sign']
            house = ((planet_sign - karkamsa_sign) % 12) + 1
            chart['planets'][planet] = {
                'sign': planet_sign,
                'sign_name': sign_names[planet_sign],
                'degree': data['degree'],
                'longitude': data['longitude'],
                'house': house,
                'retrograde': data.get('retrograde', False)
            }
            print(f"  {planet}: D1 sign {planet_sign} → House {house}")
        
        return chart
    
    def _recast_with_d9_planets(self, d9_chart, swamsa_sign):
        """Map D9 planets to houses from Swamsa lagna"""
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        chart = {
            'ascendant_sign': swamsa_sign,
            'ascendant': swamsa_sign * 30,
            'chart_type': 'Swamsa',
            'planets': {},
            'houses': [{'house_number': i+1, 'sign': (swamsa_sign+i)%12} for i in range(12)],
            'ayanamsa': d9_chart.get('ayanamsa', 0)
        }
        
        for planet, data in d9_chart['planets'].items():
            planet_sign = data['sign']
            house = ((planet_sign - swamsa_sign) % 12) + 1
            chart['planets'][planet] = {
                'sign': planet_sign,
                'sign_name': sign_names[planet_sign],
                'degree': data['degree'],
                'longitude': data['longitude'],
                'house': house,
                'retrograde': data.get('retrograde', False)
            }
            print(f"  {planet}: D9 sign {planet_sign} → House {house}")
        
        return chart
    
    def get_karkamsa_interpretation(self, karkamsa_sign):
        """
        Get classical interpretation of Karkamsa sign
        
        Args:
            karkamsa_sign: Sign number (0-11)
            
        Returns:
            str: Classical interpretation
        """
        interpretations = {
            0: "Aries Karkamsa: Spiritual warrior, dharma through action, leadership in spiritual matters",
            1: "Taurus Karkamsa: Material dharma, wealth through righteous means, stable spiritual path",
            2: "Gemini Karkamsa: Intellectual dharma, teaching, communication of wisdom",
            3: "Cancer Karkamsa: Emotional dharma, nurturing others, devotional path",
            4: "Leo Karkamsa: Royal dharma, leadership in spiritual/religious matters, authority",
            5: "Virgo Karkamsa: Service-oriented dharma, healing, analytical spiritual approach",
            6: "Libra Karkamsa: Balanced dharma, justice, partnership in spiritual growth",
            7: "Scorpio Karkamsa: Transformative dharma, occult knowledge, deep spiritual research",
            8: "Sagittarius Karkamsa: Philosophical dharma, teaching higher wisdom, pilgrimage",
            9: "Capricorn Karkamsa: Disciplined dharma, traditional spiritual practices, renunciation",
            10: "Aquarius Karkamsa: Humanitarian dharma, unconventional spiritual path, service to masses",
            11: "Pisces Karkamsa: Mystical dharma, meditation, liberation-oriented path"
        }
        return interpretations.get(karkamsa_sign, "Unknown Karkamsa sign")
    
    def get_swamsa_interpretation(self, swamsa_sign):
        """
        Get classical interpretation of Swamsa sign
        
        Args:
            swamsa_sign: Sign number (0-11)
            
        Returns:
            str: Classical interpretation
        """
        interpretations = {
            0: "Aries Swamsa: Warrior lineage, independent ancestors, pioneering family karma",
            1: "Taurus Swamsa: Wealthy lineage, stable family traditions, material inheritance",
            2: "Gemini Swamsa: Intellectual lineage, communicative ancestors, versatile family",
            3: "Cancer Swamsa: Nurturing lineage, emotional family bonds, protective ancestors",
            4: "Leo Swamsa: Royal lineage, authoritative ancestors, leadership inheritance",
            5: "Virgo Swamsa: Service-oriented lineage, analytical family, healing traditions",
            6: "Libra Swamsa: Balanced lineage, diplomatic ancestors, partnership-focused family",
            7: "Scorpio Swamsa: Transformative lineage, secretive family, occult inheritance",
            8: "Sagittarius Swamsa: Philosophical lineage, religious ancestors, wisdom tradition",
            9: "Capricorn Swamsa: Disciplined lineage, traditional family, structured inheritance",
            10: "Aquarius Swamsa: Humanitarian lineage, unconventional ancestors, progressive family",
            11: "Pisces Swamsa: Mystical lineage, spiritual ancestors, compassionate family karma"
        }
        return interpretations.get(swamsa_sign, "Unknown Swamsa sign")
