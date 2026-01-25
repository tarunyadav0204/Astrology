"""
Kota Chakra Calculator - Uttara Kalamrita System
Static fortress grid for analyzing malefic siege and protection at specific moments
"""

from typing import Dict, Any, List
from calculators.base_calculator import BaseCalculator

class KotaChakraCalculator(BaseCalculator):
    
    # 28 Nakshatras with Abhijit (degree boundaries)
    NAKSHATRA_28_BOUNDARIES = [
        (0.0, 13.333333, "Ashwini"), (13.333333, 26.666667, "Bharani"), (26.666667, 40.0, "Krittika"),
        (40.0, 53.333333, "Rohini"), (53.333333, 66.666667, "Mrigashira"), (66.666667, 80.0, "Ardra"),
        (80.0, 93.333333, "Punarvasu"), (93.333333, 106.666667, "Pushya"), (106.666667, 120.0, "Ashlesha"),
        (120.0, 133.333333, "Magha"), (133.333333, 146.666667, "Purva Phalguni"), (146.666667, 160.0, "Uttara Phalguni"),
        (160.0, 173.333333, "Hasta"), (173.333333, 186.666667, "Chitra"), (186.666667, 200.0, "Swati"),
        (200.0, 213.333333, "Vishakha"), (213.333333, 226.666667, "Anuradha"), (226.666667, 240.0, "Jyeshtha"),
        (240.0, 253.333333, "Mula"), (253.333333, 266.666667, "Purva Ashadha"),
        (266.666667, 276.666667, "Uttara Ashadha"),  # Shortened for Abhijit
        (276.666667, 280.888889, "Abhijit"),  # 06°40' to 10°53'20" Capricorn (276.666667° to 280.888889°)
        (280.888889, 293.333333, "Shravana"),  # Starts after Abhijit
        (293.333333, 306.666667, "Dhanishta"), (306.666667, 320.0, "Shatabhisha"),
        (320.0, 333.333333, "Purva Bhadrapada"), (333.333333, 346.666667, "Uttara Bhadrapada"),
        (346.666667, 360.0, "Revati")
    ]
    
    NAKSHATRAS = [name for _, _, name in NAKSHATRA_28_BOUNDARIES]
    
    # Fortress sections (7 nakshatras each)
    FORTRESS_SECTIONS = {
        'Stambha': [0, 1, 2, 3, 4, 5, 6],      # Inner Pillar (Critical)
        'Madhya': [7, 8, 9, 10, 11, 12, 13],   # Middle Fort
        'Prakaara': [14, 15, 16, 17, 18, 19, 20], # Boundary Wall
        'Bahya': [21, 22, 23, 24, 25, 26, 27]  # Outer Zone
    }
    
    def __init__(self, chart_data):
        super().__init__(chart_data)
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate Kota Chakra fortress grid and malefic siege analysis"""
        try:
            # Get Janma Nakshatra (Birth Star)
            moon_data = self.chart_data['planets'].get('Moon', {})
            janma_nakshatra = self._get_nakshatra_from_longitude(moon_data.get('longitude', 0))
            
            # Map fortress from Janma Nakshatra
            fortress_map = self._build_fortress_map(janma_nakshatra)
            
            # Get Kota Swami (Lord of Moon's Rashi)
            kota_swami = self._get_kota_swami(moon_data.get('sign', 0))
            
            # Get Kota Paala (Nakshatra Lord)
            kota_paala = self._get_nakshatra_lord(janma_nakshatra)
            
            # Analyze malefic positions in fortress
            malefic_siege = self._analyze_malefic_siege(fortress_map)
            
            # Calculate protection/vulnerability score
            protection_score = self._calculate_protection_score(malefic_siege, kota_swami, kota_paala)
            
            return {
                'janma_nakshatra': self.NAKSHATRAS[janma_nakshatra],
                'janma_nakshatra_num': janma_nakshatra,
                'kota_swami': kota_swami,
                'kota_paala': kota_paala,
                'fortress_map': fortress_map,
                'malefic_siege': malefic_siege,
                'protection_score': protection_score,
                'interpretation': self._generate_interpretation(malefic_siege, protection_score)
            }
            
        except Exception as e:
            return {"error": f"Kota Chakra calculation failed: {str(e)}"}
    
    def _get_nakshatra_from_longitude(self, longitude: float) -> int:
        """Convert longitude to nakshatra number (0-27) using 28-nakshatra system with Abhijit"""
        longitude = longitude % 360
        
        for idx, (start, end, name) in enumerate(self.NAKSHATRA_28_BOUNDARIES):
            if start <= longitude < end:
                return idx
        
        return 27  # Revati fallback
    
    def _build_fortress_map(self, janma_nakshatra: int) -> Dict[str, List[str]]:
        """Build fortress sections starting from Janma Nakshatra"""
        fortress = {}
        
        for section, offsets in self.FORTRESS_SECTIONS.items():
            nakshatras = []
            for offset in offsets:
                nak_index = (janma_nakshatra + offset) % 28
                if nak_index < len(self.NAKSHATRAS):
                    nakshatras.append(self.NAKSHATRAS[nak_index])
            fortress[section] = nakshatras
        
        return fortress
    
    def _get_kota_swami(self, moon_sign: int) -> str:
        """Get lord of Moon's rashi"""
        lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        return lords[moon_sign]
    
    def _get_nakshatra_lord(self, nakshatra_num: int) -> str:
        """Get Vimshottari lord of nakshatra"""
        lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
                "Saturn", "Mercury"] * 3
        return lords[nakshatra_num % 27]
    
    def _analyze_malefic_siege(self, fortress_map: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze malefic planet positions in fortress sections with motion direction"""
        malefics = ['Saturn', 'Mars', 'Rahu', 'Ketu']
        siege_data = {'Stambha': [], 'Madhya': [], 'Prakaara': [], 'Bahya': []}
        
        for planet_name in malefics:
            if planet_name in self.chart_data['planets']:
                planet_data = self.chart_data['planets'][planet_name]
                planet_nak = self._get_nakshatra_from_longitude(planet_data.get('longitude', 0))
                planet_nak_name = self.NAKSHATRAS[planet_nak]
                is_retrograde = planet_data.get('is_retrograde', False)
                
                # Determine motion direction
                motion = 'entering' if is_retrograde else 'exiting'
                
                # Find which section this nakshatra is in
                for section, nakshatras in fortress_map.items():
                    if planet_nak_name in nakshatras:
                        siege_data[section].append({
                            'planet': planet_name,
                            'nakshatra': planet_nak_name,
                            'motion': motion,
                            'retrograde': is_retrograde
                        })
                        break
        
        return siege_data
    
    def _calculate_protection_score(self, malefic_siege: Dict[str, Any], kota_swami: str, kota_paala: str) -> Dict[str, Any]:
        """Calculate vulnerability score based on malefic positions and guard status"""
        stambha_count = len(malefic_siege['Stambha'])
        madhya_count = len(malefic_siege['Madhya'])
        
        # Check if Kota Swami is strong
        swami_data = self.chart_data['planets'].get(kota_swami, {})
        swami_strong = swami_data.get('dignity', '') in ['Exalted', 'Own Sign', 'Moolatrikona']
        
        # Check if Kota Paala (Guard) is inside the fortress
        paala_data = self.chart_data['planets'].get(kota_paala, {})
        paala_nak = self._get_nakshatra_from_longitude(paala_data.get('longitude', 0))
        paala_nak_name = self.NAKSHATRAS[paala_nak]
        
        paala_guarding = False
        for section in ['Stambha', 'Madhya']:
            if any(m['nakshatra'] == paala_nak_name for m in malefic_siege.get(section, []) if isinstance(m, dict)):
                paala_guarding = True
                break
        
        # Calculate vulnerability
        vulnerability = stambha_count * 3 + madhya_count * 2
        if not swami_strong:
            vulnerability += 2
        if paala_guarding:
            vulnerability -= 2  # Guard is protecting
        
        # Check for entering malefics (more dangerous)
        entering_stambha = sum(1 for m in malefic_siege['Stambha'] if isinstance(m, dict) and m['motion'] == 'entering')
        if entering_stambha > 0:
            vulnerability += entering_stambha
        
        if vulnerability >= 6:
            status = "High Vulnerability"
        elif vulnerability >= 3:
            status = "Moderate Caution"
        else:
            status = "Protected"
        
        return {
            'status': status,
            'vulnerability_score': vulnerability,
            'kota_swami_strong': swami_strong,
            'kota_paala_guarding': paala_guarding
        }
    
    def _generate_interpretation(self, malefic_siege: Dict[str, Any], protection_score: Dict[str, Any]) -> str:
        """Generate interpretation text"""
        stambha = malefic_siege['Stambha']
        status = protection_score['status']
        
        if status == "High Vulnerability":
            planets = [m['planet'] for m in stambha if isinstance(m, dict)]
            entering = [m['planet'] for m in stambha if isinstance(m, dict) and m['motion'] == 'entering']
            if entering:
                return f"Critical Alert: {', '.join(planets)} in Stambha with {', '.join(entering)} entering. Immediate health/legal caution needed."
            return f"Critical Alert: {', '.join(planets)} in Stambha (Inner Pillar) creates siege. Health/legal caution needed."
        elif status == "Moderate Caution":
            return "Moderate pressure from malefics. Maintain vigilance in health and legal matters."
        else:
            return "Fortress is protected. No major malefic siege detected."
