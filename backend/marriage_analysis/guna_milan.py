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
            1: 'Kshatriya', 2: 'Vaishya', 3: 'Vaishya', 4: 'Brahmin',
            5: 'Kshatriya', 6: 'Vaishya', 7: 'Vaishya', 8: 'Kshatriya',
            9: 'Kshatriya', 10: 'Vaishya', 11: 'Shudra', 12: 'Brahmin'
        }
        
        boy_varna = varna_map[boy_rashi]
        girl_varna = varna_map[girl_rashi]
        
        # Traditional rule: Boy's varna must be strictly higher than girl's for compatibility
        varna_order = {'Brahmin': 4, 'Kshatriya': 3, 'Vaishya': 2, 'Shudra': 1}
        
        # Score 1 only if boy's varna is strictly higher than girl's
        # Same varna or lower varna for boy = 0 points (stricter traditional rule)
        if varna_order[boy_varna] > varna_order[girl_varna]:
            score = 1
        else:
            score = 0
        
        interpretation = self._get_varna_interpretation(score, boy_varna, girl_varna)
        
        return {
            'score': score,
            'max_score': 1,
            'boy_varna': boy_varna,
            'girl_varna': girl_varna,
            'description': f"Boy: {boy_varna}, Girl: {girl_varna}",
            'interpretation': interpretation
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
        
        interpretation = self._get_vashya_interpretation(score, boy_vashya, girl_vashya)
        
        return {
            'score': score,
            'max_score': 2,
            'boy_vashya': boy_vashya,
            'girl_vashya': girl_vashya,
            'description': f"Boy: {boy_vashya}, Girl: {girl_vashya}",
            'interpretation': interpretation
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
        
        interpretation = self._get_tara_interpretation(score, tara_num)
        
        return {
            'score': score,
            'max_score': 3,
            'tara_number': tara_num,
            'description': f"Tara: {tara_num} ({'Favorable' if score == 3 else 'Unfavorable' if score == 0 else 'Neutral'})",
            'interpretation': interpretation
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
        
        # Yoni compatibility matrix - Traditional scoring
        yoni_compatibility = {
            # Same yoni - maximum compatibility
            ('Horse', 'Horse'): 4, ('Elephant', 'Elephant'): 4,
            ('Goat', 'Goat'): 4, ('Serpent', 'Serpent'): 4,
            ('Dog', 'Dog'): 4, ('Cat', 'Cat'): 4,
            ('Rat', 'Rat'): 4, ('Cow', 'Cow'): 4,
            ('Buffalo', 'Buffalo'): 4, ('Tiger', 'Tiger'): 4,
            ('Deer', 'Deer'): 4, ('Monkey', 'Monkey'): 4,
            ('Lion', 'Lion'): 4, ('Mongoose', 'Mongoose'): 4,
            
            # Friendly combinations - 3 points
            ('Horse', 'Elephant'): 3, ('Elephant', 'Horse'): 3,
            ('Cow', 'Buffalo'): 3, ('Buffalo', 'Cow'): 3,
            ('Goat', 'Monkey'): 3, ('Monkey', 'Goat'): 3,
            
            # Neutral combinations - 2 points  
            ('Horse', 'Goat'): 2, ('Goat', 'Horse'): 2,
            ('Elephant', 'Serpent'): 2, ('Serpent', 'Elephant'): 2,
            ('Dog', 'Buffalo'): 2, ('Buffalo', 'Dog'): 2,
            
            # Unfriendly combinations - 1 point
            ('Horse', 'Tiger'): 1, ('Tiger', 'Horse'): 1,
            ('Elephant', 'Tiger'): 1, ('Tiger', 'Elephant'): 1,
            ('Cow', 'Tiger'): 1, ('Tiger', 'Cow'): 1,
            
            # Enemy combinations - 0 points
            ('Cat', 'Rat'): 0, ('Rat', 'Cat'): 0,
            ('Dog', 'Cat'): 0, ('Cat', 'Dog'): 0,
            ('Tiger', 'Deer'): 0, ('Deer', 'Tiger'): 0,
            ('Lion', 'Elephant'): 0, ('Elephant', 'Lion'): 0,
            ('Mongoose', 'Serpent'): 0, ('Serpent', 'Mongoose'): 0,
            ('Horse', 'Buffalo'): 0, ('Buffalo', 'Horse'): 0
        }
        
        score = yoni_compatibility.get((boy_yoni, girl_yoni), 1)  # Default unfriendly
        
        interpretation = self._get_yoni_interpretation(score, boy_yoni, girl_yoni)
        
        return {
            'score': score,
            'max_score': 4,
            'boy_yoni': boy_yoni,
            'girl_yoni': girl_yoni,
            'description': f"Boy: {boy_yoni}, Girl: {girl_yoni}",
            'interpretation': interpretation
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
        
        interpretation = self._get_graha_maitri_interpretation(score, boy_lord, girl_lord, relation)
        
        return {
            'score': score,
            'max_score': 5,
            'boy_lord': boy_lord,
            'girl_lord': girl_lord,
            'relation': relation,
            'description': f"Boy: {boy_lord}, Girl: {girl_lord} ({relation})",
            'interpretation': interpretation
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
        
        interpretation = self._get_gana_interpretation(score, boy_gana, girl_gana)
        
        return {
            'score': score,
            'max_score': 6,
            'boy_gana': boy_gana,
            'girl_gana': girl_gana,
            'description': f"Boy: {boy_gana}, Girl: {girl_gana}",
            'interpretation': interpretation
        }
    
    def _calculate_bhakoot(self, boy_rashi: int, girl_rashi: int) -> Dict[str, Any]:
        """Bhakoot Koot - 7 points"""
        # Calculate distance from boy's rashi to girl's rashi
        distance = (girl_rashi - boy_rashi) % 12
        if distance == 0:
            distance = 12
        
        # Traditional Bhakoot rules - very strict
        # 0 points for: 6th and 8th positions (6/8 dosha)
        # Also 0 points for: 2nd and 12th positions in many traditions
        unfavorable_positions = [2, 6, 8, 12]
        
        if distance in unfavorable_positions:
            score = 0
        else:
            score = 7
        
        interpretation = self._get_bhakoot_interpretation(score, distance)
        
        return {
            'score': score,
            'max_score': 7,
            'distance': distance,
            'description': f"Girl's rashi is {distance} positions from boy's ({'Favorable' if score == 7 else 'Unfavorable'})",
            'interpretation': interpretation
        }
    
    def _calculate_nadi(self, boy_nak: int, girl_nak: int) -> Dict[str, Any]:
        """Nadi Koot - 8 points (most critical)"""
        # Standard Nadi mapping used by most Vedic astrology applications
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
        
        interpretation = self._get_nadi_interpretation(score, boy_nadi, girl_nadi)
        
        return {
            'score': score,
            'max_score': 8,
            'boy_nadi': boy_nadi,
            'girl_nadi': girl_nadi,
            'description': f"Boy: {boy_nadi}, Girl: {girl_nadi}",
            'critical': score == 0,
            'interpretation': interpretation
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
        # Correct nakshatra to rashi mapping
        nakshatra_to_rashi = {
            1: 1, 2: 1, 3: 1, 4: 2,  # Ashwini, Bharani, Krittika(1st pada), Krittika(2-4 pada) -> Aries, Aries, Aries, Taurus
            5: 2, 6: 3, 7: 3, 8: 4,  # Rohini, Mrigashira(1-2 pada), Mrigashira(3-4 pada), Ardra -> Taurus, Gemini, Gemini, Gemini  
            9: 4, 10: 5, 11: 5, 12: 6, # Punarvasu(1-3 pada), Punarvasu(4th pada), Pushya, Ashlesha -> Cancer, Cancer, Leo, Leo
            13: 6, 14: 6, 15: 7, 16: 7, # Magha, Purva Phalguni, Uttara Phalguni(1st pada), Uttara Phalguni(2-4 pada) -> Leo, Leo, Virgo, Virgo
            17: 7, 18: 8, 19: 8, 20: 9, # Hasta, Chitra(1-2 pada), Chitra(3-4 pada), Swati -> Virgo, Libra, Libra, Libra
            21: 9, 22: 10, 23: 10, 24: 11, # Vishakha(1-3 pada), Vishakha(4th pada), Anuradha, Jyeshtha -> Scorpio, Scorpio, Sagittarius, Sagittarius
            25: 11, 26: 12, 27: 12  # Mula, Purva Ashadha(1-3 pada), Purva Ashadha(4th pada) -> Sagittarius, Capricorn, Capricorn
        }
        
        # Correct mapping based on traditional Vedic astrology
        rashi_mapping = [
            1, 1, 1, 2,  # Ashwini, Bharani, Krittika, Rohini
            2, 3, 3, 4,  # Mrigashira, Ardra, Punarvasu, Pushya  
            4, 5, 5, 6,  # Ashlesha, Magha, Purva Phalguni, Uttara Phalguni
            6, 7, 7, 8,  # Hasta, Chitra, Swati, Vishakha
            8, 9, 9, 10, # Anuradha, Jyeshtha, Mula, Purva Ashadha
            10, 11, 11, 12, # Uttara Ashadha, Shravana, Dhanishta, Shatabhisha
            12, 12, 1    # Purva Bhadrapada, Uttara Bhadrapada, Revati
        ]
        
        if 1 <= nak_num <= 27:
            return rashi_mapping[nak_num - 1]
        return 1
    
    def _get_compatibility_level(self, score: int) -> str:
        """Get compatibility level based on total score"""
        if score >= 30:
            return '💖 Excellent - A deeply harmonious match with strong love, understanding, and shared life goals.'
        elif score >= 25:
            return '💞 Very Good - You complement each other well. Small differences only add flavor to your bond.'
        elif score >= 18:
            return '🌿 Moderate - The relationship may need patience and emotional awareness, but it can be fulfilling with effort.'
        else:
            return '⚡ Challenging - Differences are more noticeable — extra care, timing, and remedies are advised.'
    
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
    
    def _get_varna_interpretation(self, score: int, boy_varna: str, girl_varna: str) -> str:
        """Get detailed interpretation for Varna compatibility"""
        general = "🕉️ **Varna – Spiritual and Mental Compatibility**\n\nThis guna shows how similar your inner natures are. It reveals whether you both share the same level of emotional maturity, values, and approach to life. When Varna matches well, you naturally understand each other's feelings and respect each other's individuality."
        
        if score == 1:
            specific = f"✨ **Your Score: {score}/1 - Excellent**\n\nYour spiritual energies align beautifully. The boy's {boy_varna} nature complements the girl's {girl_varna} nature perfectly, creating natural harmony and mutual respect in your relationship."
        else:
            specific = f"💫 **Your Score: {score}/1 - Growth Opportunity**\n\nYour spiritual paths may differ slightly, but this creates a beautiful opportunity to grow together with patience and love. One may seem more spiritually inclined, but this balance can deepen your bond through understanding."
        
        return f"{general}\n\n{specific}"
    
    def _get_vashya_interpretation(self, score: int, boy_vashya: str, girl_vashya: str) -> str:
        """Get detailed interpretation for Vashya compatibility"""
        general = "💞 **Vashya – Attraction and Influence**\n\nVashya speaks about the invisible pull between you — the magnetic energy that draws two souls together. It shows who tends to take the lead and how well the other follows with trust and comfort."
        
        if score == 2:
            specific = f"✨ **Your Score: {score}/2 - Perfect Harmony**\n\nYour attraction is beautifully balanced: neither controlling nor distant, but naturally affectionate. Both belonging to {boy_vashya} nature, you understand each other's needs intuitively."
        elif score == 1:
            specific = f"💫 **Your Score: {score}/2 - Gentle Balance**\n\nYour {boy_vashya}-{girl_vashya} combination creates interesting dynamics. You must communicate more openly and learn to respect each other's space and individuality, which will strengthen your magnetic pull."
        else:
            specific = f"🌱 **Your Score: {score}/2 - Learning Together**\n\nYour attraction patterns differ, but this simply means you express love differently. Learning each other's love language will create the harmony that transcends any astrological limitation."
        
        return f"{general}\n\n{specific}"
    
    def _get_tara_interpretation(self, score: int, tara_num: int) -> str:
        """Get detailed interpretation for Tara compatibility"""
        general = "🌠 **Tara – Luck, Support, and Destiny Harmony**\n\nTara tells how lucky you are for each other — how your energies combine to bring happiness, success, and peace into each other's lives. When the stars of both partners support one another, life flows smoothly and opportunities seem to appear effortlessly."
        
        tara_meanings = {
            1: "Janma (Birth) - Same nature, excellent understanding",
            2: "Sampat (Wealth) - Material prosperity with gentle challenges", 
            3: "Vipat (Danger) - Strength through overcoming obstacles together",
            4: "Kshema (Welfare) - Mutual welfare and happiness",
            5: "Pratyak (Obstacle) - Beautiful spiritual growth together",
            6: "Sadhana (Achievement) - Success through loving effort",
            7: "Naidhana (Death) - Transformation and renewal of love",
            8: "Mitra (Friend) - Deep friendship foundation",
            9: "Ati-Mitra (Great Friend) - Profound soul connection"
        }
        
        meaning = tara_meanings.get(tara_num, "Unknown")
        
        if score == 3:
            specific = f"✨ **Your Score: {score}/3 - Destined Harmony**\n\nYour Tara {tara_num} ({meaning}) brings beautiful fortune to your union. Life flows smoothly and opportunities appear effortlessly when you're together."
        elif score == 1:
            specific = f"💫 **Your Score: {score}/3 - Gentle Timing**\n\nYour Tara {tara_num} ({meaning}) suggests you may face small ups and downs in timing, but with care and optimism, you can easily overcome them together."
        else:
            specific = f"🌱 **Your Score: {score}/3 - Patient Growth**\n\nYour Tara {tara_num} ({meaning}) calls for extra patience and understanding, but true love can transform any challenge into deeper connection."
        
        return f"{general}\n\n{specific}"
    
    def _get_yoni_interpretation(self, score: int, boy_yoni: str, girl_yoni: str) -> str:
        """Get detailed interpretation for Yoni compatibility"""
        general = "💋 **Yoni – Emotional and Physical Chemistry**\n\nYoni describes your natural chemistry — how your hearts and bodies connect on an instinctive level. It reveals how affectionate, expressive, and comfortable you feel together."
        
        if score == 4:
            specific = f"✨ **Your Score: {score}/4 - Perfect Chemistry**\n\nBoth sharing the {boy_yoni} nature, there is warmth, tenderness, and a deep sense of belonging. Your hearts beat in perfect rhythm together."
        elif score == 3:
            specific = f"💫 **Your Score: {score}/4 - Beautiful Harmony**\n\nYour {boy_yoni}-{girl_yoni} combination creates strong attraction and tender connection. Minor adjustments only add sweetness to your bond."
        elif score == 2:
            specific = f"🌸 **Your Score: {score}/4 - Growing Love**\n\nYour {boy_yoni}-{girl_yoni} combination shows gentle chemistry that grows stronger with understanding and patience."
        elif score == 1:
            specific = f"🌱 **Your Score: {score}/4 - Learning Love**\n\nYour {boy_yoni}-{girl_yoni} combination means you express love differently. Learning each other's love language will strengthen your bond beautifully."
        else:
            specific = f"💝 **Your Score: {score}/4 - Transforming Love**\n\nYour {boy_yoni}-{girl_yoni} combination challenges you to love beyond the physical, creating a deeper spiritual connection that transcends all limitations."
        
        return f"{general}\n\n{specific}"
    
    def _get_graha_maitri_interpretation(self, score: int, boy_lord: str, girl_lord: str, relation: str) -> str:
        """Get detailed interpretation for Graha Maitri compatibility"""
        general = "🌿 **Graha Maitri – Friendship and Understanding**\n\nGraha Maitri shows the level of friendship in your relationship. It reflects how easily you share ideas, emotions, and decisions with each other. When this guna is strong, you think alike, listen with patience, and truly enjoy each other's company."
        
        if score == 5:
            specific = f"✨ **Your Score: {score}/5 - Soul Twins**\n\nBoth ruled by {boy_lord}, you share identical thinking patterns and interests. You truly enjoy each other's company and understand each other's minds perfectly."
        elif score == 4:
            specific = f"💫 **Your Score: {score}/5 - Beautiful Friendship**\n\nYour ruling planets {boy_lord} and {girl_lord} are friends, creating natural understanding, mutual respect, and harmonious conversations."
        elif score == 3:
            specific = f"🌸 **Your Score: {score}/5 - Balanced Minds**\n\nYour ruling planets {boy_lord} and {girl_lord} are neutral. Your thought processes may differ, but that contrast can bring beautiful balance with empathy."
        else:
            specific = f"🌱 **Your Score: {score}/5 - Growing Understanding**\n\nYour ruling planets {boy_lord} and {girl_lord} think differently — one logical, the other emotional — but this can create profound growth through patient communication."
        
        return f"{general}\n\n{specific}"
    
    def _get_gana_interpretation(self, score: int, boy_gana: str, girl_gana: str) -> str:
        """Get detailed interpretation for Gana compatibility"""
        general = "🔥 **Gana – Temperament and Emotional Nature**\n\nGana represents your emotional nature and everyday behavior. It shows how you both react to life — calm and gentle, practical and social, or passionate and bold. When your Ganas align, you feel understood and accepted just as you are."
        
        if score == 6:
            if boy_gana == girl_gana:
                specific = f"✨ **Your Score: {score}/6 - Perfect Understanding**\n\nBoth belonging to {boy_gana} nature, you feel completely understood and accepted just as you are. Your emotional rhythms flow in beautiful harmony."
            else:
                specific = f"✨ **Your Score: {score}/6 - Complementary Souls**\n\nYour {boy_gana}-{girl_gana} combination creates beautiful harmony where differences become strengths that support each other."
        else:
            specific = f"🌱 **Your Score: {score}/6 - Learning Patience**\n\nYour {boy_gana}-{girl_gana} combination means one may be more expressive while the other prefers peace. Recognizing these differences helps you respond with kindness, turning contrasts into deep emotional growth."
        
        return f"{general}\n\n{specific}"
    
    def _get_bhakoot_interpretation(self, score: int, distance: int) -> str:
        """Get detailed interpretation for Bhakoot compatibility"""
        general = "💫 **Bhakoot – Emotional Bond and Life Progress**\n\nBhakoot reveals the emotional rhythm of your relationship — how your hearts beat together over time. It shows whether you support each other's goals, finances, and family life. A strong Bhakoot match means you grow together in harmony, sharing dreams and responsibilities with ease."
        
        if score == 7:
            specific = f"✨ **Your Score: {score}/7 - Growing Together**\n\nYour {distance}-position relationship creates beautiful harmony in health, prosperity, and life progress. You support each other's dreams naturally."
        else:
            specific = f"🌱 **Your Score: {score}/7 - Patient Building**\n\nYour {distance}-position relationship means your life patterns may differ, but open-hearted communication and shared values can still create a lasting and fulfilling bond."
        
        return f"{general}\n\n{specific}"
    
    def _get_nadi_interpretation(self, score: int, boy_nadi: str, girl_nadi: str) -> str:
        """Get detailed interpretation for Nadi compatibility"""
        general = "💓 **Nadi – Health, Energy, and Soul Connection**\n\nNadi is the pulse of your relationship — the flow of energy that connects two souls at the deepest level. It reflects health, vitality, and emotional resonance."
        
        if score == 8:
            specific = f"✨ **Your Score: {score}/8 - Complementary Energies**\n\nYour different nadis ({boy_nadi} and {girl_nadi}) bring complementary strengths to the relationship, ensuring healthy vitality and beautiful energy flow."
        else:
            specific = f"🌱 **Your Score: {score}/8 - Mindful Harmony**\n\nYou share the same nadi ({boy_nadi}), meaning very similar energies. This calls for awareness, healthy habits, and deep compassion toward each other to maintain beautiful balance."
        
        return f"{general}\n\n{specific}"