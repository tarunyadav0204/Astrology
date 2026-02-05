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
        """Analyze malefic and benefic positions in fortress sections"""
        malefics = ['Saturn', 'Mars', 'Rahu', 'Ketu']
        benefics = ['Jupiter', 'Venus']
        siege_data = {'Stambha': [], 'Madhya': [], 'Prakaara': [], 'Bahya': []}
        
        # Check all planets (malefics and benefics)
        all_planets = malefics + benefics
        for planet_name in all_planets:
            if planet_name in self.chart_data['planets']:
                planet_data = self.chart_data['planets'][planet_name]
                planet_nak = self._get_nakshatra_from_longitude(planet_data.get('longitude', 0))
                planet_nak_name = self.NAKSHATRAS[planet_nak]
                is_retrograde = planet_data.get('is_retrograde', False)
                is_benefic = planet_name in benefics
                
                # Determine motion direction
                motion = 'entering' if is_retrograde else 'exiting'
                
                # Find which section this nakshatra is in
                for section, nakshatras in fortress_map.items():
                    if planet_nak_name in nakshatras:
                        siege_data[section].append({
                            'planet': planet_name,
                            'nakshatra': planet_nak_name,
                            'motion': motion,
                            'retrograde': is_retrograde,
                            'is_benefic': is_benefic
                        })
                        break
        
        return siege_data
    
    def _calculate_protection_score(self, malefic_siege: Dict[str, Any], kota_swami: str, kota_paala: str) -> Dict[str, Any]:
        """Calculate vulnerability with benefic shielding and zone significations"""
        stambha_planets = malefic_siege['Stambha']
        madhya_planets = malefic_siege['Madhya']
        prakaara_planets = malefic_siege['Prakaara']
        
        # Separate malefics and benefics in Stambha
        stambha_malefics = [p for p in stambha_planets if not p.get('is_benefic', False)]
        stambha_benefics = [p for p in stambha_planets if p.get('is_benefic', False)]
        madhya_malefics = [p for p in madhya_planets if not p.get('is_benefic', False)]
        
        # Classical rule: Any malefic in Stambha creates vulnerability
        stambha_occupied = len(stambha_malefics) > 0
        
        # Benefic shielding: Jupiter/Venus in Stambha acts as guardian
        benefic_shield = len(stambha_benefics) > 0
        
        # Check Kota Swami strength
        swami_data = self.chart_data['planets'].get(kota_swami, {})
        swami_strong = swami_data.get('dignity', '') in ['Exalted', 'Own Sign', 'Moolatrikona']
        
        # Check if Kota Paala is free
        paala_data = self.chart_data['planets'].get(kota_paala, {})
        paala_nak = self._get_nakshatra_from_longitude(paala_data.get('longitude', 0))
        paala_nak_name = self.NAKSHATRAS[paala_nak]
        
        paala_free = True
        for section in ['Stambha', 'Madhya']:
            if any(m['nakshatra'] == paala_nak_name for m in malefic_siege.get(section, []) if isinstance(m, dict) and not m.get('is_benefic', False)):
                paala_free = False
                break
        
        # Enhanced vulnerability calculation
        vulnerability = 0
        zone_effects = []
        
        if stambha_occupied:
            vulnerability += 4  # Base siege
            zone_effects.append("Self/Core survival under attack")
            
            if benefic_shield:
                vulnerability -= 2  # Benefic protection
                zone_effects.append("Guardian benefic provides shield")
            
            if swami_strong and paala_free:
                vulnerability -= 1  # Additional protection
                zone_effects.append("Strong fortress guardians")
        
        if len(madhya_malefics) > 0:
            if not stambha_occupied:
                vulnerability = 1
                zone_effects.append("Resources/Family under mild pressure")
        
        if len(prakaara_planets) > 0 and vulnerability == 0:
            zone_effects.append("Social image/reputation effects")
        
        # Status determination
        if vulnerability >= 3:
            status = "Under Siege"
        elif vulnerability == 2:
            status = "Siege with Protection"
        elif vulnerability == 1:
            status = "Caution Advised"
        else:
            status = "Fortress Protected"
        
        return {
            'status': status,
            'vulnerability_score': vulnerability,
            'kota_swami_strong': swami_strong,
            'kota_paala_guarding': paala_free,
            'stambha_occupied': stambha_occupied,
            'benefic_shield': benefic_shield,
            'zone_effects': zone_effects
        }
    
    def _generate_interpretation(self, malefic_siege: Dict[str, Any], protection_score: Dict[str, Any]) -> str:
        """Generate synthesis interpretation with zone significations"""
        status = protection_score['status']
        zone_effects = protection_score.get('zone_effects', [])
        benefic_shield = protection_score.get('benefic_shield', False)
        
        stambha_malefics = [p['planet'] for p in malefic_siege['Stambha'] if not p.get('is_benefic', False)]
        stambha_benefics = [p['planet'] for p in malefic_siege['Stambha'] if p.get('is_benefic', False)]
        
        interpretation = ""
        
        if status == "Under Siege":
            interpretation = f"Stambha Siege: {', '.join(stambha_malefics)} attacking core self. "
            if benefic_shield:
                interpretation += f"Guardian {', '.join(stambha_benefics)} provides partial shield. "
        elif status == "Siege with Protection":
            interpretation = f"Protected Siege: {', '.join(stambha_malefics)} in Stambha but guardians defend. "
        elif status == "Caution Advised":
            interpretation = "Madhya pressure on resources/family. Moderate vigilance needed. "
        else:
            interpretation = "Fortress secure. Favorable for health, legal matters, and new ventures. "
        
        if zone_effects:
            interpretation += " ".join(zone_effects)
        
    def get_planet_details(self, planet_name: str, kota_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextual details for a specific planet in the fortress"""
        if planet_name not in self.chart_data['planets']:
            return {"error": f"Planet {planet_name} not found"}
        
        planet_data = self.chart_data['planets'][planet_name]
        planet_nak = self._get_nakshatra_from_longitude(planet_data.get('longitude', 0))
        planet_nak_name = self.NAKSHATRAS[planet_nak]
        
        # Determine fortress role
        kota_swami = kota_result.get('kota_swami')
        kota_paala = kota_result.get('kota_paala')
        
        if planet_name == kota_swami:
            role = "Kota Swami (Fortress Lord)"
            role_icon = "🛡"
        elif planet_name == kota_paala:
            role = "Kota Paala (Fortress Guard)"
            role_icon = "👮"
        elif planet_name in ['Saturn', 'Mars', 'Rahu', 'Ketu']:
            role = "Malefic Attacker"
            role_icon = "🔴"
        elif planet_name in ['Jupiter', 'Venus']:
            role = "Benefic Protector"
            role_icon = "🔵"
        else:
            role = "Neutral Planet"
            role_icon = "⚪"
        
        # Find fortress location
        fortress_location = "Unknown"
        fortress_map = kota_result.get('fortress_map', {})
        for section, nakshatras in fortress_map.items():
            if planet_nak_name in nakshatras:
                fortress_location = section
                break
        
        # Get current effect based on role and location
        effect = self._get_planet_effect(planet_name, role, fortress_location, planet_data)
        
        # Get guidance based on role
        guidance = self._get_planet_guidance(planet_name, role, fortress_location, kota_result)
        
        # Get sign name from longitude
        sign_num = int(planet_data.get('longitude', 0) // 30)
        sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign_name = sign_names[sign_num] if 0 <= sign_num < 12 else "Unknown"
        
        return {
            "planet": planet_name,
            "role": role,
            "role_icon": role_icon,
            "position": f"{sign_name} {planet_data.get('longitude', 0):.1f}°",
            "nakshatra": planet_nak_name,
            "fortress_location": fortress_location,
            "motion": "Retrograde" if planet_data.get('is_retrograde', False) else "Direct",
            "effect": effect
        }
    
    def _get_planet_effect(self, planet: str, role: str, location: str, planet_data: Dict) -> str:
        """Get specific effect based on planet role and location"""
        if "Fortress Lord" in role:
            if planet_data.get('dignity', '') in ['Exalted', 'Own Sign', 'Moolatrikona']:
                return f"Strong lord providing royal protection to fortress"
            else:
                return f"Weak lord - fortress defenses compromised"
        elif "Fortress Guard" in role:
            if location in ['Stambha', 'Madhya']:
                return f"Guard compromised - unable to protect effectively"
            else:
                return f"Guard positioned well - actively protecting fortress"
        elif "Malefic Attacker" in role:
            if location == 'Stambha':
                return f"Direct siege on core self - health/legal vulnerabilities"
            elif location == 'Madhya':
                return f"Attacking resources and family stability"
            elif location == 'Prakaara':
                return f"Threatening social image and reputation"
            else:
                return f"External pressure from distant sources"
        elif "Benefic Protector" in role:
            if location == 'Stambha':
                return f"Guardian angel providing divine shield to core self"
            elif location == 'Madhya':
                return f"Blessing resources and family prosperity"
            else:
                return f"Providing protective influence from {location.lower()} zone"
        else:
            return f"Neutral influence from {location.lower()} position"
    
    def _get_planet_guidance(self, planet: str, role: str, location: str, kota_result: Dict) -> str:
        """Get actionable guidance based on planet's fortress role"""
        if "Fortress Lord" in role:
            strong = kota_result.get('protection_score', {}).get('kota_swami_strong', False)
            if strong:
                return f"Your fortress lord is strong - excellent time for important ventures and major decisions"
            else:
                return f"Strengthen your lord with {planet} remedies - wear appropriate gemstone, perform {planet} worship"
        elif "Fortress Guard" in role:
            guarding = kota_result.get('protection_score', {}).get('kota_paala_guarding', False)
            if guarding:
                return f"Your guard is active - favorable period for overcoming enemies and obstacles"
            else:
                return f"Guard needs strengthening - perform {planet} mantras and remedies to enhance protection"
        elif "Malefic Attacker" in role:
            if location == 'Stambha':
                return f"Critical period - avoid major health decisions, legal matters, and risky ventures"
            elif location == 'Madhya':
                return f"Exercise caution in financial matters and family decisions"
            else:
                return f"General vigilance needed - perform {planet} remedies to reduce negative influence"
        elif "Benefic Protector" in role:
            return f"Auspicious influence active - enhance with {planet} worship for maximum benefit"
        else:
            return f"Neutral period - standard precautions apply"
