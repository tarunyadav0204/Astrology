# calculators/financial/vedha_calculator.py

class VedhaCalculator:
    """
    Calculates Nakshatra Vedha (Piercing) based on the Sarvatobhadra Chakra (SBC).
    Includes all 28 Nakshatras (Ashwini to Revati + Abhijit).
    """
    
    def __init__(self):
        self.vedha_map = self._get_full_sbc_map()

    def check_vedha(self, planet_long: float, planet_speed: float, target_nakshatra_name: str) -> str:
        """
        Checks if a planet is piercing the target Nakshatra.
        Returns: 'Front', 'Left', 'Right' (Retrograde), or None.
        """
        p_nak_idx = self._get_sbc_nakshatra_index(planet_long)
        t_nak_idx = self._get_nakshatra_index_by_name(target_nakshatra_name)
        
        if not p_nak_idx or not t_nak_idx:
            return None

        targets = self.vedha_map.get(p_nak_idx, {})
        is_retrograde = planet_speed < 0
        
        # Debug logging
        # print(f"  [Vedha] Planet at idx {p_nak_idx} ({planet_long:.2f}°), Target: {target_nakshatra_name} (idx {t_nak_idx})")
        # print(f"  [Vedha] Targets: Front={targets.get('front')}, Left={targets.get('left')}, Right={targets.get('right')}")
        # print(f"  [Vedha] Retrograde: {is_retrograde}")
        
        # FRONT VEDHA: Always active (Direct or Retrograde)
        if targets.get('front') == t_nak_idx:
            return "Front Vedha (Direct Hit)"
            
        # DIRECTIONAL VEDHA (Depends on Motion)
        if is_retrograde:
            if targets.get('right') == t_nak_idx:
                return "Right Vedha (Retrograde Hit)"
        else:
            if targets.get('left') == t_nak_idx:
                return "Left Vedha (Direct Hit)"
                
        return None

    def _get_full_sbc_map(self):
        """
        Returns the Complete 28-Star Lookup Table.
        Index 1 = Ashwini, ..., 22 = Abhijit, ..., 28 = Revati.
        """
        return {
            # --- EASTERN SIDE ---
            1:  {'front': 28, 'left': 22, 'right': 15}, # Ashwini (Corner)
            2:  {'front': 27, 'left': 23, 'right': 14}, # Bharani
            3:  {'front': 26, 'left': 24, 'right': 13}, # Krittika
            4:  {'front': 25, 'left': 25, 'right': 12}, # Rohini (Center)
            5:  {'front': 24, 'left': 26, 'right': 11}, # Mrigashira
            6:  {'front': 23, 'left': 27, 'right': 10}, # Ardra
            7:  {'front': 22, 'left': 28, 'right': 9},  # Punarvasu (Corner)

            # --- SOUTHERN SIDE ---
            8:  {'front': 21, 'left': 1, 'right': 22},  # Pushya (Corner)
            9:  {'front': 20, 'left': 2, 'right': 23},  # Ashlesha
            10: {'front': 19, 'left': 3, 'right': 24},  # Magha
            11: {'front': 18, 'left': 4, 'right': 25},  # P.Phalguni (Center)
            12: {'front': 17, 'left': 5, 'right': 26},  # U.Phalguni
            13: {'front': 16, 'left': 6, 'right': 27},  # Hasta
            14: {'front': 15, 'left': 7, 'right': 28},  # Chitra (Corner)

            # --- WESTERN SIDE ---
            15: {'front': 14, 'left': 8, 'right': 1},   # Swati (Corner)
            16: {'front': 13, 'left': 9, 'right': 2},   # Vishakha
            17: {'front': 12, 'left': 10, 'right': 3},  # Anuradha
            18: {'front': 11, 'left': 11, 'right': 4},  # Jyeshtha (Center)
            19: {'front': 10, 'left': 12, 'right': 5},  # Mula
            20: {'front': 9,  'left': 13, 'right': 6},  # P.Ashadha
            21: {'front': 8,  'left': 14, 'right': 7},  # U.Ashadha (Corner)

            # --- NORTHERN SIDE ---
            22: {'front': 7,  'left': 15, 'right': 8},  # Abhijit (Corner)
            23: {'front': 6,  'left': 16, 'right': 9},  # Shravana
            24: {'front': 5,  'left': 17, 'right': 10}, # Dhanishta
            25: {'front': 4,  'left': 18, 'right': 11}, # Shatabhisha (Center)
            26: {'front': 3,  'left': 19, 'right': 12}, # P.Bhadrapada
            27: {'front': 2,  'left': 20, 'right': 13}, # U.Bhadrapada
            28: {'front': 1,  'left': 21, 'right': 14}, # Revati (Corner)
        }

    def _get_sbc_nakshatra_index(self, longitude: float) -> int:
        """
        Maps 360 degrees to 28 SBC Nakshatras.
        Abhijit (22) is inserted between U.Ashadha (21) and Shravana (23).
        """
        idx = int(longitude / (360/28)) + 1
        return idx

    def _get_nakshatra_index_by_name(self, name: str) -> int:
        ordered_naks = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
            "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
            "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
            "Uttara Ashadha", "Abhijit", "Shravana", "Dhanishta", "Shatabhisha", 
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        try:
            return ordered_naks.index(name) + 1
        except ValueError:
            return None
