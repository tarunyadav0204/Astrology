"""
Ashtakoot Guna Milan Calculator
Implements 8 koots for compatibility scoring (36 points total)
"""
from typing import Dict, List, Tuple, Any

class GunaMilanCalculator:
    def __init__(self):
        self.nakshatra_data = self._initialize_nakshatra_data()
    
    def calculate_ashtakoot(self, boy_moon_nakshatra: str, girl_moon_nakshatra: str) -> Dict[str, Any]:
        """Calculate complete Ashtakoot compatibility"""
        boy_nak_num = self._get_nakshatra_number(boy_moon_nakshatra)
        girl_nak_num = self._get_nakshatra_number(girl_moon_nakshatra)
        
        boy_rashi = self._get_rashi_from_nakshatra(boy_nak_num)
        girl_rashi = self._get_rashi_from_nakshatra(girl_nak_num)
        
        koots = {
            'varna': self._calculate_varna(boy_rashi, girl_rashi),
            'vashya': self._calculate_vashya(boy_rashi, girl_rashi),
            'tara': self._calculate_tara(boy_nak_num, girl_nak_num),
            'yoni': self._calculate_yoni(boy_nak_num, girl_nak_num),
            'graha_maitri': self._calculate_graha_maitri(boy_rashi, girl_rashi),
            'gana': self._calculate_gana(boy_nak_num, girl_nak_num),
            'bhakoot': self._calculate_bhakoot(boy_rashi, girl_rashi),
            'nadi': self._calculate_nadi(boy_nak_num, girl_nak_num)
        }
        
        total_score = sum(koot['score'] for koot in koots.values())
        
        return {
            'total_score': total_score,
            'max_score': 36,
            'percentage': round((total_score / 36) * 100, 1),
            'compatibility_level': self._get_compatibility_level(total_score),
            'koots': koots,
            'critical_issues': self._check_critical_issues(koots)
        }
    
    def _calculate_varna(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        """Varna Koot - 1 point"""
        varna_map = {
            1: 'Brahmin', 2: 'Kshatriya', 3: 'Brahmin', 4: 'Brahmin',
            5: 'Kshatriya', 6: 'Vaishya', 7: 'Vaishya', 8: 'Brahmin',
            9: 'Kshatriya', 10: 'Vaishya', 11: 'Shudra', 12: 'Brahmin'
        }
        
        boy_varna = varna_map[boy_rashi]
        girl_varna = varna_map[girl_rashi]
        
        # Boy's varna should be equal or higher
        varna_order = {'Brahmin': 4, 'Kshatriya': 3, 'Vaishya': 2, 'Shudra': 1}
        
        score = 1 if varna_order[boy_varna] >= varna_order[girl_varna] else 0
        
        return {
            'score': score,
            'max_score': 1,
            'boy_varna': boy_varna,
            'girl_varna': girl_varna,
            'description': f"Boy: {boy_varna}, Girl: {girl_varna}"
        }
    
    def _calculate_vashya(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        """Vashya Koot - 2 points"""
        vashya_map = {
            1: 'Quadruped', 2: 'Quadruped', 3: 'Human', 4: 'Water',
            5: 'Quadruped', 6: 'Human', 7: 'Human', 8: 'Insect',
            9: 'Human', 10: 'Quadruped', 11: 'Human', 12: 'Water'
        }
        
        boy_vashya = vashya_map[boy_rashi]
        girl_vashya = vashya_map[girl_rashi]
        
        # Compatibility matrix
        compatibility = {
            ('Human', 'Human'): 2,
            ('Quadruped', 'Quadruped'): 2,
            ('Water', 'Water'): 2,
            ('Human', 'Water'): 1,
            ('Water', 'Human'): 1,
            ('Quadruped', 'Human'): 1,
            ('Human', 'Quadruped'): 1
        }
        
        score = compatibility.get((boy_vashya, girl_vashya), 0)
        
        return {
            'score': score,
            'max_score': 2,
            'boy_vashya': boy_vashya,
            'girl_vashya': girl_vashya,
            'description': f"Boy: {boy_vashya}, Girl: {girl_vashya}"
        }
    
    def _calculate_tara(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        """Tara Koot - 3 points"""
        # Count from girl's nakshatra to boy's
        distance = (boy_nak - girl_nak) % 27
        if distance == 0:
            distance = 27
        
        tara_num = ((distance - 1) % 9) + 1
        
        # Favorable taras: 1, 3, 4, 5, 7
        favorable_taras = [1, 3, 4, 5, 7]
        
        if tara_num in favorable_taras:
            score = 3
        elif tara_num in [2, 6]:
            score = 1
        else:
            score = 0
        
        return {
            'score': score,
            'max_score': 3,
            'tara_number': tara_num,
            'description': f"Tara: {tara_num} ({'Favorable' if score == 3 else 'Unfavorable' if score == 0 else 'Neutral'})"
        }
    
    def _calculate_yoni(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        """Yoni Koot - 4 points"""
        yoni_map = {
            1: 'Horse', 2: 'Elephant', 3: 'Goat', 4: 'Serpent', 5: 'Dog',
            6: 'Cat', 7: 'Rat', 8: 'Cow', 9: 'Buffalo', 10: 'Tiger',
            11: 'Deer', 12: 'Monkey', 13: 'Lion', 14: 'Mongoose',
            15: 'Horse', 16: 'Elephant', 17: 'Goat', 18: 'Serpent',
            19: 'Dog', 20: 'Cat', 21: 'Rat', 22: 'Cow', 23: 'Buffalo',
            24: 'Tiger', 25: 'Deer', 26: 'Monkey', 27: 'Lion'
        }
        
        boy_yoni = yoni_map[boy_nak]
        girl_yoni = yoni_map[girl_nak]
        
        # Yoni compatibility matrix
        yoni_compatibility = {
            ('Horse', 'Horse'): 4, ('Elephant', 'Elephant'): 4,
            ('Goat', 'Goat'): 4, ('Serpent', 'Serpent'): 4,
            ('Dog', 'Dog'): 4, ('Cat', 'Cat'): 4,
            ('Rat', 'Rat'): 4, ('Cow', 'Cow'): 4,
            ('Buffalo', 'Buffalo'): 4, ('Tiger', 'Tiger'): 4,
            ('Deer', 'Deer'): 4, ('Monkey', 'Monkey'): 4,
            ('Lion', 'Lion'): 4, ('Mongoose', 'Mongoose'): 4,
            
            # Friendly combinations
            ('Horse', 'Elephant'): 3, ('Elephant', 'Horse'): 3,
            ('Cow', 'Buffalo'): 3, ('Buffalo', 'Cow'): 3,
            
            # Enemy combinations
            ('Cat', 'Rat'): 0, ('Rat', 'Cat'): 0,
            ('Dog', 'Cat'): 0, ('Cat', 'Dog'): 0,
            ('Tiger', 'Deer'): 0, ('Deer', 'Tiger'): 0,
            ('Lion', 'Elephant'): 0, ('Elephant', 'Lion'): 0,
            ('Mongoose', 'Serpent'): 0, ('Serpent', 'Mongoose'): 0
        }
        
        score = yoni_compatibility.get((boy_yoni, girl_yoni), 2)  # Default neutral
        
        return {
            'score': score,
            'max_score': 4,
            'boy_yoni': boy_yoni,
            'girl_yoni': girl_yoni,
            'description': f"Boy: {boy_yoni}, Girl: {girl_yoni}"
        }
    
    def _calculate_graha_maitri(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        """Graha Maitri Koot - 5 points"""
        rashi_lords = {
            1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon',
            5: 'Sun', 6: 'Mercury', 7: 'Venus', 8: 'Mars',
            9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter'
        }
        
        boy_lord = rashi_lords[boy_rashi]
        girl_lord = rashi_lords[girl_rashi]
        
        # Planet friendship matrix
        friendship = {
            'Sun': {'friends': ['Moon', 'Mars', 'Jupiter'], 'enemies': ['Venus', 'Saturn']},
            'Moon': {'friends': ['Sun', 'Mercury'], 'enemies': []},
            'Mars': {'friends': ['Sun', 'Moon', 'Jupiter'], 'enemies': ['Mercury']},
            'Mercury': {'friends': ['Sun', 'Venus'], 'enemies': ['Moon']},
            'Jupiter': {'friends': ['Sun', 'Moon', 'Mars'], 'enemies': ['Mercury', 'Venus']},
            'Venus': {'friends': ['Mercury', 'Saturn'], 'enemies': ['Sun', 'Moon']},
            'Saturn': {'friends': ['Mercury', 'Venus'], 'enemies': ['Sun', 'Moon', 'Mars']}
        }
        
        if boy_lord == girl_lord:
            score = 5
            relation = 'Same'
        elif girl_lord in friendship[boy_lord]['friends']:
            score = 4
            relation = 'Friend'
        elif girl_lord in friendship[boy_lord]['enemies']:
            score = 0
            relation = 'Enemy'
        else:
            score = 3
            relation = 'Neutral'
        
        return {
            'score': score,
            'max_score': 5,
            'boy_lord': boy_lord,
            'girl_lord': girl_lord,
            'relation': relation,
            'description': f"Boy: {boy_lord}, Girl: {girl_lord} ({relation})"
        }
    
    def _calculate_gana(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        """Gana Koot - 6 points"""
        gana_map = {
            1: 'Deva', 2: 'Manushya', 3: 'Manushya', 4: 'Rakshasa', 5: 'Manushya',
            6: 'Rakshasa', 7: 'Rakshasa', 8: 'Deva', 9: 'Rakshasa', 10: 'Deva',
            11: 'Deva', 12: 'Manushya', 13: 'Rakshasa', 14: 'Rakshasa',
            15: 'Deva', 16: 'Manushya', 17: 'Manushya', 18: 'Rakshasa',
            19: 'Manushya', 20: 'Rakshasa', 21: 'Rakshasa', 22: 'Deva',
            23: 'Rakshasa', 24: 'Deva', 25: 'Deva', 26: 'Manushya', 27: 'Rakshasa'
        }
        
        boy_gana = gana_map[boy_nak]
        girl_gana = gana_map[girl_nak]
        
        # Gana compatibility
        gana_compatibility = {
            ('Deva', 'Deva'): 6,
            ('Manushya', 'Manushya'): 6,
            ('Rakshasa', 'Rakshasa'): 6,
            ('Deva', 'Manushya'): 6,
            ('Manushya', 'Deva'): 6,
            ('Manushya', 'Rakshasa'): 0,
            ('Rakshasa', 'Manushya'): 0,
            ('Deva', 'Rakshasa'): 0,
            ('Rakshasa', 'Deva'): 0
        }
        
        score = gana_compatibility.get((boy_gana, girl_gana), 0)
        
        return {
            'score': score,
            'max_score': 6,
            'boy_gana': boy_gana,
            'girl_gana': girl_gana,
            'description': f"Boy: {boy_gana}, Girl: {girl_gana}"
        }
    
    def _calculate_bhakoot(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        """Bhakoot Koot - 7 points"""
        distance = abs(boy_rashi - girl_rashi)
        
        # Unfavorable distances: 6, 8 (6/8 positions)
        if distance in [6, 8] or (12 - distance) in [6, 8]:
            score = 0
        else:
            score = 7
        
        return {
            'score': score,
            'max_score': 7,
            'distance': distance,
            'description': f"Rashi distance: {distance} ({'Favorable' if score == 7 else 'Unfavorable'})"
        }
    
    def _calculate_nadi(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        """Nadi Koot - 8 points (most critical)"""
        nadi_map = {
            1: 'Adya', 2: 'Madhya', 3: 'Antya', 4: 'Adya', 5: 'Madhya',
            6: 'Antya', 7: 'Adya', 8: 'Madhya', 9: 'Antya', 10: 'Adya',
            11: 'Madhya', 12: 'Antya', 13: 'Adya', 14: 'Madhya',
            15: 'Antya', 16: 'Adya', 17: 'Madhya', 18: 'Antya',
            19: 'Adya', 20: 'Madhya', 21: 'Antya', 22: 'Adya',
            23: 'Madhya', 24: 'Antya', 25: 'Adya', 26: 'Madhya', 27: 'Antya'
        }
        
        boy_nadi = nadi_map[boy_nak]
        girl_nadi = nadi_map[girl_nak]
        
        score = 8 if boy_nadi != girl_nadi else 0
        
        return {
            'score': score,
            'max_score': 8,
            'boy_nadi': boy_nadi,
            'girl_nadi': girl_nadi,
            'description': f"Boy: {boy_nadi}, Girl: {girl_nadi}",
            'critical': score == 0
        }
    
    def _get_nakshatra_number(self, nakshatra_name: str) -> int:
        """Get nakshatra number (1-27)"""
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
            'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
            'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
            'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        try:
            return nakshatras.index(nakshatra_name) + 1
        except ValueError:
            return 1  # Default to Ashwini
    
    def _get_rashi_from_nakshatra(self, nak_num: int) -> int:
        """Get rashi number from nakshatra"""
        # Each rashi has 2.25 nakshatras
        return ((nak_num - 1) // 2.25) + 1
    
    def _get_compatibility_level(self, score: int) -> str:
        """Get compatibility level based on total score"""
        if score >= 31:
            return 'Excellent'
        elif score >= 21:
            return 'Good'
        elif score >= 18:
            return 'Average'
        else:
            return 'Poor'
    
    def _check_critical_issues(self, koots: Dict) -> List[str]:
        """Check for critical compatibility issues"""
        issues = []
        
        # Nadi dosha
        if koots['nadi']['score'] == 0:
            issues.append("Nadi Dosha - Same Nadi (Critical)")
        
        # Bhakoot dosha
        if koots['bhakoot']['score'] == 0:
            issues.append("Bhakoot Dosha - 6/8 position")
        
        # Gana mismatch
        if koots['gana']['score'] == 0:
            issues.append("Gana Dosha - Incompatible temperaments")
        
        return issues
    
    def _initialize_nakshatra_data(self) -> Dict:
        """Initialize nakshatra reference data"""
        return {
            'names': [
                'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
                'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
                'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
                'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
                'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
            ]
        }