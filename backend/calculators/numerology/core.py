import re

class NumerologyCore:
    """
    The Core Engine for Numerology Calculations.
    Handles mapping systems (Chaldean/Pythagorean) and number reduction logic.
    """

    # ---------------------------------------------------------
    # 1. MAPPING CONSTANTS
    # ---------------------------------------------------------
    
    # Chaldean System (Ancient, Mystic)
    # Note: No letter is assigned to 9. The number 9 is considered sacred.
    CHALDEAN_MAP = {
        1: ['A', 'I', 'J', 'Q', 'Y'],
        2: ['B', 'K', 'R'],
        3: ['C', 'G', 'L', 'S'],
        4: ['D', 'M', 'T'],
        5: ['E', 'H', 'N', 'X'],
        6: ['U', 'V', 'W'],
        7: ['O', 'Z'],
        8: ['F', 'P']
    }

    # Pythagorean System (Modern, Sequential)
    # A=1, B=2... I=9, J=1...
    PYTHAGOREAN_MAP = {
        1: ['A', 'J', 'S'],
        2: ['B', 'K', 'T'],
        3: ['C', 'L', 'U'],
        4: ['D', 'M', 'V'],
        5: ['E', 'N', 'W'],
        6: ['F', 'O', 'X'],
        7: ['G', 'P', 'Y'],
        8: ['H', 'Q', 'Z'],
        9: ['I', 'R']
    }

    # Master Numbers - These are often not reduced in advanced numerology
    MASTER_NUMBERS = {11, 22, 33}

    def __init__(self):
        # Flatten maps for O(1) lookup: {'A': 1, 'B': 2 ...}
        self.chaldean_lookup = self._create_lookup(self.CHALDEAN_MAP)
        self.pythagorean_lookup = self._create_lookup(self.PYTHAGOREAN_MAP)

    def _create_lookup(self, mapping_dict):
        """Helper to invert the map for fast character lookups."""
        lookup = {}
        for number, letters in mapping_dict.items():
            for char in letters:
                lookup[char] = number
        return lookup

    # ---------------------------------------------------------
    # 2. CORE UTILITIES
    # ---------------------------------------------------------

    def reduce_to_single(self, number: int, keep_master: bool = True) -> int:
        """
        Reduces a multi-digit number to a single digit (1-9).
        Example: 23 -> 5.
        
        Args:
            number: The number to reduce.
            keep_master: If True, preserves 11, 22, 33 without reducing.
        """
        # Handle Master Numbers immediately if flag is set
        if keep_master and number in self.MASTER_NUMBERS:
            return number

        # Recursive Reduction
        while number > 9:
            # Check for master number during intermediate steps (e.g., 29 -> 11)
            if keep_master and number in self.MASTER_NUMBERS:
                return number
            
            # Sum digits: 23 -> 2 + 3 = 5
            number = sum(int(digit) for digit in str(number))
            
        return number

    def get_compound_sum(self, text: str, system: str = 'chaldean') -> int:
        """
        Calculates the raw sum of a name WITHOUT reducing.
        Example: "TARUN" -> 4+1+2+6+5 = 18.
        The '18' is the Compound Number (very important in Chaldean).
        """
        text = self._clean_text(text)
        total = 0
        lookup = self.chaldean_lookup if system == 'chaldean' else self.pythagorean_lookup
        
        for char in text:
            total += lookup.get(char, 0)
            
        return total

    def calculate_name_number(self, text: str, system: str = 'chaldean') -> dict:
        """
        Returns full analysis: The Compound Number AND the Reduced Number.
        """
        compound = self.get_compound_sum(text, system)
        reduced = self.reduce_to_single(compound, keep_master=True)
        
        return {
            "name": text,
            "system": system,
            "compound_number": compound,  # The "Mystic" number (e.g. 18)
            "single_number": reduced,     # The "Identity" number (e.g. 9)
            "is_master": reduced in self.MASTER_NUMBERS
        }

    def _clean_text(self, text: str) -> str:
        """Strips non-alpha characters and converts to uppercase."""
        return re.sub(r'[^A-Z]', '', text.upper())

    # ---------------------------------------------------------
    # 3. DATE UTILITIES
    # ---------------------------------------------------------

    def calculate_life_path(self, dob_str: str) -> dict:
        """
        Calculates Life Path from YYYY-MM-DD.
        Method: Horizontal Addition (Day + Month + Year).
        """
        # Expected format: YYYY-MM-DD
        year, month, day = map(int, dob_str.split('-'))

        # Reduce each component first (Standard Method)
        r_day = self.reduce_to_single(day)
        r_month = self.reduce_to_single(month)
        r_year = self.reduce_to_single(year)

        # Sum them up
        final_sum = r_day + r_month + r_year
        life_path = self.reduce_to_single(final_sum)

        return {
            "dob": dob_str,
            "day_number": day, # Birth Day number is also significant
            "life_path_number": life_path,
            "is_master": life_path in self.MASTER_NUMBERS
        }