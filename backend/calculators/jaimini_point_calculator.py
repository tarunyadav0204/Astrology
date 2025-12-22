from typing import Dict, Any, List

class JaiminiPointCalculator:
    """
    Calculates Special Jaimini Lagnas:
    1. Arudha Lagna (AL) - Image/Status (in D1)
    2. Upapada Lagna (UL) - Relationships (in D1)
    3. Karkamsa Lagna (KL) - Atmakaraka's sign in Navamsa (D9)
    4. Swamsa Lagna - The Ascendant of the Navamsa (D9)
    """

    def __init__(self, d1_chart: Dict[str, Any], d9_chart: Dict[str, Any], atmakaraka_planet: str):
        self.d1_chart = d1_chart
        self.d9_chart = d9_chart
        self.atmakaraka = atmakaraka_planet
        self.planets_d1 = d1_chart.get('planets', {})
        self.planets_d9 = d9_chart.get('planets', {}) if 'planets' in d9_chart else d9_chart.get('divisional_chart', {}).get('planets', {})
        
        # Determine Ascendant Sign (0-11) for D1
        self.asc_degree_d1 = d1_chart.get('ascendant', 0)
        self.asc_sign_d1 = int(self.asc_degree_d1 / 30)

    def calculate_jaimini_points(self) -> Dict[str, Any]:
        """Returns the calculated Jaimini points."""
        
        # 1. Arudha Lagna (AL) - Arudha of the 1st House (D1)
        al_sign = self._calculate_arudha_pada(house_num=1)
        
        # 2. Upapada Lagna (UL) - Arudha of the 12th House (D1)
        ul_sign = self._calculate_arudha_pada(house_num=12)
        
        # 3. Karkamsa Lagna (KL) - Sign of Atmakaraka in D9
        kl_sign = self._calculate_karkamsa()
        
        # 4. Swamsa Lagna - Ascendant of D9
        # Note: Often Swamsa and Karkamsa are used interchangeably, 
        # but here we treat Swamsa as the 'Lagnamsa' (D9 Ascendant) for yoga analysis.
        swamsa_degree = self.d9_chart.get('ascendant', 0)
        swamsa_sign = int(swamsa_degree / 30)
        
        return {
            "arudha_lagna": {
                "sign_id": al_sign,
                "sign_name": self._get_sign_name(al_sign),
                "description": "How the world sees you (Status/Image)."
            },
            "upapada_lagna": {
                "sign_id": ul_sign,
                "sign_name": self._get_sign_name(ul_sign),
                "description": "Marriage and relationships."
            },
            "karkamsa_lagna": {
                "sign_id": kl_sign,
                "sign_name": self._get_sign_name(kl_sign),
                "description": "Soul's desire and professional talent (AK in D9)."
            },
            "swamsa_lagna": {
                "sign_id": swamsa_sign,
                "sign_name": self._get_sign_name(swamsa_sign),
                "description": "The Ascendant of the Navamsa (Soul's Path)."
            }
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
