from typing import Dict, Any, List

class JaiminiPointCalculator:
    """
    Calculates Special Jaimini Lagnas:
    1. Arudha Lagna (AL) - Image/Status (in D1)
    2. Upapada Lagna (UL) - Relationships (in D1)
    3. Karkamsa Lagna (KL) - Atmakaraka's sign in Navamsa (D9)
    4. Swamsa Lagna - The Ascendant of the Navamsa (D9)
    """

    def __init__(self, d1_chart: Dict[str, Any], d9_chart: Dict[str, Any], atmakaraka_planet: str, birth_data=None, ayanamsha: str = 'lahiri'):
        self.d1_chart = d1_chart
        self.d9_chart = d9_chart
        self.atmakaraka = atmakaraka_planet
        self.birth_data = birth_data
        self.ayanamsha = ayanamsha
        self.planets_d1 = d1_chart.get('planets', {})
        self.planets_d9 = d9_chart.get('planets', {}) if 'planets' in d9_chart else d9_chart.get('divisional_chart', {}).get('planets', {})
        
        # Determine Ascendant Sign (0-11) for D1
        self.asc_degree_d1 = d1_chart.get('ascendant', 0)
        self.asc_sign_d1 = int(self.asc_degree_d1 / 30)

    def calculate_jaimini_points(self) -> Dict[str, Any]:
        """Returns the calculated Jaimini points."""
        
        # 1. Arudha Lagna (AL) - Arudha of the 1st House (D1)
        al_sign = self._calculate_arudha_pada(house_num=1)
        
        # 2. Darapada (A7) - Arudha of the 7th House (Business/Physical Partnerships)
        a7_sign = self._calculate_arudha_pada(house_num=7)
        
        # 3. Upapada Lagna (UL) - Arudha of the 12th House (Legal Marriage)
        ul_sign = self._calculate_arudha_pada(house_num=12)
        
        # 4. Karkamsa Lagna (KL) - Sign of Atmakaraka in D9
        kl_sign = self._calculate_karkamsa()
        
        # 5. Swamsa reference - selected convention: AK's Navamsa sign.
        # The legacy implementation incorrectly returned the D9 ascendant here,
        # while the dedicated Swamsa chart was already recast from the AK's D9 sign.
        swamsa_sign = kl_sign
        
        # BPHS Chapter 5 requires sunrise and birth-place inputs for these two
        # points.  Never substitute the former Sun/Moon/Ascendant shortcuts.
        time_lagnas = self._calculate_time_lagnas()
        hora_lagna = time_lagnas.get('hora_lagna') or self._unavailable_time_lagna('Hora Lagna')
        ghatika_lagna = time_lagnas.get('ghatika_lagna') or self._unavailable_time_lagna('Ghatika Lagna')
        
        return {
            "arudha_lagna": {
                "sign_id": al_sign,
                "sign_name": self._get_sign_name(al_sign),
                "description": "Public Status & Image (AL)"
            },
            "darapada": {
                "sign_id": a7_sign,
                "sign_name": self._get_sign_name(a7_sign),
                "description": "Business & Physical Partnerships (A7)"
            },
            "upapada_lagna": {
                "sign_id": ul_sign,
                "sign_name": self._get_sign_name(ul_sign),
                "description": "Legal Marriage & Spouse (UL)"
            },
            "karkamsa_lagna": {
                "sign_id": kl_sign,
                "sign_name": self._get_sign_name(kl_sign),
                "description": "Soul's Skill/Talent (KL)"
            },
            "swamsa_lagna": {
                "sign_id": swamsa_sign,
                "sign_name": self._get_sign_name(swamsa_sign),
                "description": "D9 reference from the Atmakaraka's Navamsa sign",
                "terminology_note": "Commentarial usage of Swamsha and Karakamsha varies."
            },
            "hora_lagna": hora_lagna,
            "ghatika_lagna": ghatika_lagna,
        }

    def calculate_house_arudha(self, house_num: int) -> Dict[str, Any]:
        """Calculate the Arudha Pada (A1-A12) for one D1 house."""
        house = int(house_num)
        if house < 1 or house > 12:
            raise ValueError("house_num must be between 1 and 12")
        sign = self._calculate_arudha_pada(house_num=house)
        return {
            "house": house,
            "name": f"A{house}",
            "sign_id": sign,
            "sign_name": self._get_sign_name(sign),
            "calculation_rule": (
                "Count from the house sign to its lord and repeat the distance, "
                "using the standard same-sign and seventh-sign exceptions."
            ),
        }

    # -------------------------------------------------------------------------
    # CORE LOGIC: Arudha Calculation
    # -------------------------------------------------------------------------
    def _calculate_arudha_pada(self, house_num: int) -> int:
        """
        Calculates the Arudha (Image) of a house.
        Rule: Count from House to Lord. Count same distance again.
        Exceptions (K.N. Rao / Standard Jaimini):
        - If Lord is in the House itself -> Arudha is 10th from House.
        - If Lord is in 7th from House -> Arudha is 4th from House.
        """
        # 1. Identify the Sign of the House (in D1)
        house_sign_idx = (self.asc_sign_d1 + (house_num - 1)) % 12
        
        # 2. Find the Lord of that Sign
        lord_planet = self._get_lord_planet(house_sign_idx)
        
        # 3. Find where the Lord is sitting (in D1)
        if isinstance(lord_planet, list):
             lord_pos_sign = self._resolve_dual_lord_simple(lord_planet)
        else:
            lord_pos_sign = self.planets_d1.get(lord_planet, {}).get('sign', 0)
            
        # 4. Count from House Sign to Lord Sign
        # Always count FORWARD in Zodiac for Arudha calculation
        if lord_pos_sign >= house_sign_idx:
            dist = lord_pos_sign - house_sign_idx
        else:
            dist = (12 - house_sign_idx) + lord_pos_sign
            
        # 5. Apply Exceptions
        if dist == 0:
            final_arudha = (house_sign_idx + 9) % 12 # 10th house
            return final_arudha
            
        if dist == 6:
            final_arudha = (house_sign_idx + 3) % 12 # 4th house
            return final_arudha
            
        # 6. Normal Calculation: Count 'dist' again from Lord
        final_arudha = (lord_pos_sign + dist) % 12
        
        return final_arudha

    def _calculate_karkamsa(self) -> int:
        """Finds the sign of the Atmakaraka in the D9 (Navamsa) Chart."""
        if not self.atmakaraka:
            return 0
        
        ak_data = self.planets_d9.get(self.atmakaraka, {})
        return ak_data.get('sign', 0)
    
    @staticmethod
    def _unavailable_time_lagna(name: str) -> Dict[str, Any]:
        return {
            'available': False,
            'name': name,
            'reason': 'Birth date, time, latitude, longitude and timezone are required for the BPHS sunrise calculation.',
            'fallback_used': False,
        }

    def _calculate_time_lagnas(self) -> Dict[str, Any]:
        """Use the canonical BPHS sunrise calculator when birth data is present."""
        if not self.birth_data:
            return {}
        from .classical_special_points import ClassicalSpecialPointsCalculator
        worksheet = ClassicalSpecialPointsCalculator(
            self.d1_chart,
            self.birth_data,
            self.d9_chart,
            ayanamsha=self.ayanamsha,
        ).special_lagnas()
        result = {}
        for row in worksheet.get('points') or []:
            if row.get('key') not in {'hora_lagna', 'ghatika_lagna'}:
                continue
            result[row['key']] = {
                'available': True,
                'sign_id': row['sign'],
                'sign_name': row['sign_name'],
                'longitude': row['longitude'],
                'degree': row['degree'],
                'description': row['name'],
                'calculation_basis': row['calculation_basis'],
            }
        return result

    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------
    def _get_lord_planet(self, sign_idx: int):
        """Returns lord of the sign (names)."""
        lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
            4: 'Sun', 5: 'Mercury', 6: 'Venus', 
            7: ['Mars', 'Ketu'], # Scorpio
            8: 'Jupiter', 9: 'Saturn', 
            10: ['Saturn', 'Rahu'], # Aquarius
            11: 'Jupiter'
        }
        return lords[sign_idx]

    def _resolve_dual_lord_simple(self, lords: List[str]) -> int:
        """
        Simplified Dual Lord check for Arudha.
        Returns the sign of the stronger lord (based on Association).
        """
        p1, p2 = lords[0], lords[1]
        p1_sign = self.planets_d1.get(p1, {}).get('sign', 0)
        p2_sign = self.planets_d1.get(p2, {}).get('sign', 0)
        
        p1_count = self._count_planets_in_sign(p1_sign)
        p2_count = self._count_planets_in_sign(p2_sign)
        
        if p1_count >= p2_count: return p1_sign
        return p2_sign

    def _count_planets_in_sign(self, sign_idx: int) -> int:
        c = 0
        for p in self.planets_d1.values():
            if p.get('sign') == sign_idx: c += 1
        return c

    def _get_sign_name(self, idx: int) -> str:
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[idx]
