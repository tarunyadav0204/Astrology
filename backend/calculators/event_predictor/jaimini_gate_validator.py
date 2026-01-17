"""
Jaimini Gate Validator - Cross-Validation Layer
Verifies Parashari predictions using Jaimini system for "Double-Lock" accuracy
"""

from typing import Dict, List, Tuple
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.chara_dasha_calculator import CharaDashaCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.argala_calculator import ArgalaCalculator
from calculators.jaimini_full_analyzer import JaiminiFullAnalyzer
from calculators.jaimini_point_calculator import JaiminiPointCalculator


class JaiminiGateValidator:
    """
    Jaimini Cross-Validation Layer for Parashari predictions.
    
    Double-Lock Logic:
    - Parashari predicts event → Jaimini validates
    - Both agree → 85-95% probability (CERTAIN)
    - One agrees → 55-70% probability (POSSIBLE)
    - Both disagree → 40% probability (STRUGGLE)
    
    Scoring:
    - Chara Dasha MD sign aspects house: +50 points
    - Chara Dasha AD sign aspects house: +30 points
    - Relevant Karaka connection: +40 points
    - Argala support (>25): +20 points
    - Argala obstruction (<-25): -20 points
    """
    
    # Karaka-to-House mappings
    HOUSE_KARAKAS = {
        1: ['Atmakaraka'],  # Self
        2: ['Putrakaraka'],  # Wealth (children = prosperity)
        3: ['Bhratrukaraka'],  # Siblings, courage
        4: ['Matrukaraka'],  # Mother, home
        5: ['Putrakaraka'],  # Children, creativity
        6: ['Gnatikaraka'],  # Enemies, obstacles
        7: ['Darakaraka'],  # Spouse, partnership
        8: ['Gnatikaraka'],  # Longevity, transformation
        9: ['Atmakaraka'],  # Dharma, fortune
        10: ['Amatyakaraka'],  # Career, profession
        11: ['Putrakaraka'],  # Gains, fulfillment
        12: ['Gnatikaraka']  # Loss, moksha
    }
    
    def __init__(self, chart_data: Dict, birth_data: Dict, d9_chart: Dict, atmakaraka_planet: str):
        """
        Initialize Jaimini validators.
        
        Args:
            chart_data: D1 chart with planets, ascendant
            birth_data: Birth details with date, time, location
            d9_chart: D9 Navamsa chart
            atmakaraka_planet: Atmakaraka planet name
        """
        self.chart_data = chart_data
        self.birth_data = birth_data
        
        # Initialize Jaimini calculators
        self.chara_dasha_calc = CharaDashaCalculator(chart_data)
        self.karaka_calc = CharaKarakaCalculator(chart_data)
        self.argala_calc = ArgalaCalculator(chart_data)
        self.point_calc = JaiminiPointCalculator(chart_data, d9_chart, atmakaraka_planet)
        
        # Pre-calculate Jaimini data
        self.karakas = self.karaka_calc.calculate_chara_karakas()['chara_karakas']
        self.argala_data = self.argala_calc.calculate_argala_analysis()
        self.points = self.point_calc.calculate_jaimini_points()
        
        # Calculate Chara Dasha
        from datetime import datetime as dt
        dob_str = birth_data.get('date', '1990-01-01')
        time_str = birth_data.get('time', '12:00:00')
        # Handle both HH:MM and HH:MM:SS formats
        if time_str.count(':') == 2:
            dob_dt = dt.strptime(f"{dob_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        else:
            dob_dt = dt.strptime(f"{dob_str} {time_str}", "%Y-%m-%d %H:%M")
        self.chara_dasha = self.chara_dasha_calc.calculate_dasha(dob_dt)
        
        # Initialize Jaimini analyzer
        self.jaimini_analyzer = JaiminiFullAnalyzer(
            chart_data, 
            {'chara_karakas': self.karakas},
            self.points,
            self.chara_dasha
        )
        
        # Get Rashi Drishti (sign aspects)
        self.rashi_drishti = self.jaimini_analyzer._calculate_all_aspects()
    
    def validate_house(self, house: int, current_date: datetime) -> Dict:
        """
        Validate if Jaimini system confirms house activation.
        
        Args:
            house: House number (1-12)
            current_date: Current date for dasha check
        
        Returns:
            {
                'validated': bool,
                'jaimini_score': int,
                'confidence_level': str,
                'reasons': List[str],
                'chara_dasha_support': bool,
                'karaka_support': bool,
                'argala_support': bool
            }
        """
        score = 0
        reasons = []
        
        # Get current Chara Dasha periods
        current_md_sign, current_ad_sign = self._get_current_dasha_signs(current_date)
        
        print(f"   Chara Dasha: MD={self._get_sign_name(current_md_sign) if current_md_sign is not None else 'None'}, AD={self._get_sign_name(current_ad_sign) if current_ad_sign is not None else 'None'}")
        
        # Layer 1: Chara Dasha Sign Aspects House
        md_score, md_reasons = self._check_dasha_sign_aspects(
            current_md_sign, house, 'Mahadasha', 50
        )
        score += md_score
        reasons.extend(md_reasons)
        
        ad_score, ad_reasons = self._check_dasha_sign_aspects(
            current_ad_sign, house, 'Antardasha', 30
        )
        score += ad_score
        reasons.extend(ad_reasons)
        
        chara_dasha_support = (md_score > 0 or ad_score > 0)
        
        # Layer 2: Karaka Verification
        karaka_score, karaka_reasons = self._check_karaka_connection(house)
        score += karaka_score
        reasons.extend(karaka_reasons)
        
        karaka_support = karaka_score > 0
        
        # Layer 3: Argala Validation
        argala_score, argala_reasons = self._check_argala_strength(house)
        score += argala_score
        reasons.extend(argala_reasons)
        
        argala_support = argala_score > 0
        
        # Determine validation status
        validated = score >= 30  # Minimum threshold
        confidence_level = self._get_confidence_level(score)
        
        return {
            'validated': validated,
            'jaimini_score': score,
            'confidence_level': confidence_level,
            'reasons': reasons,
            'chara_dasha_support': chara_dasha_support,
            'karaka_support': karaka_support,
            'argala_support': argala_support,
            'house': house,
            'current_md_sign': current_md_sign,
            'current_ad_sign': current_ad_sign
        }
    
    def _get_current_dasha_signs(self, current_date: datetime) -> Tuple[int, int]:
        """Get current Chara Dasha MD and AD signs"""
        periods = self.chara_dasha.get('periods', [])
        
        # Find current MD
        current_md = next((p for p in periods if p.get('is_current')), None)
        if not current_md:
            return None, None
        
        md_sign = current_md.get('sign_id')
        
        # Find current AD
        antardashas = current_md.get('antardashas', [])
        current_ad = next((a for a in antardashas if a.get('is_current')), None)
        ad_sign = current_ad.get('sign_id') if current_ad else None
        
        return md_sign, ad_sign
    
    def _check_dasha_sign_aspects(self, dasha_sign: int, target_house: int,
                                   level_name: str, weight: int) -> Tuple[int, List[str]]:
        """
        Check if Chara Dasha sign aspects target house.
        
        Uses Rashi Drishti (sign-based aspects).
        """
        if dasha_sign is None:
            return 0, []
        
        score = 0
        reasons = []
        
        # Convert house to sign
        asc_sign = int(self.chart_data['ascendant'] / 30)
        target_sign = (asc_sign + target_house - 1) % 12
        
        # Check if dasha sign IS the target sign (conjunction)
        if dasha_sign == target_sign:
            score = weight
            reasons.append(f"Chara {level_name} sign IS H{target_house} ({self._get_sign_name(dasha_sign)})")
        
        # Check if dasha sign aspects target sign (Rashi Drishti)
        elif target_sign in self.rashi_drishti.get(dasha_sign, []):
            score = weight
            reasons.append(f"Chara {level_name} sign aspects H{target_house} (Rashi Drishti)")
        
        return score, reasons
    
    def _check_karaka_connection(self, house: int) -> Tuple[int, List[str]]:
        """
        Check if relevant Karaka is connected to house.
        
        Connection = Karaka planet in house OR Karaka sign aspects house.
        """
        score = 0
        reasons = []
        
        # Get relevant karakas for this house
        relevant_karakas = self.HOUSE_KARAKAS.get(house, [])
        
        for karaka_name in relevant_karakas:
            karaka_data = self.karakas.get(karaka_name)
            if not karaka_data:
                continue
            
            karaka_planet = karaka_data['planet']
            karaka_sign = karaka_data['sign']
            karaka_house = karaka_data['house']
            
            # Check if karaka planet is IN the target house
            if karaka_house == house:
                score = 40
                reasons.append(f"{karaka_name} ({karaka_planet}) sits in H{house}")
                break
            
            # Check if karaka sign aspects target house
            asc_sign = int(self.chart_data['ascendant'] / 30)
            target_sign = (asc_sign + house - 1) % 12
            
            if target_sign in self.rashi_drishti.get(karaka_sign, []):
                score = 40
                reasons.append(f"{karaka_name} ({karaka_planet}) sign aspects H{house}")
                break
        
        return score, reasons
    
    def _check_argala_strength(self, house: int) -> Tuple[int, List[str]]:
        """
        Check Argala (intervention) strength for house.
        
        Argala > 25: Strong support (+20)
        Argala < -25: Strong obstruction (-20)
        """
        score = 0
        reasons = []
        
        house_argala = self.argala_data.get(house, {})
        net_argala = house_argala.get('net_argala_strength', 0)
        argala_grade = house_argala.get('argala_grade', 'Neutral')
        
        if net_argala > 25:
            score = 20
            reasons.append(f"Strong Argala support for H{house} ({argala_grade})")
        elif net_argala < -25:
            score = -20
            reasons.append(f"⚠️ Strong Virodha Argala obstruction for H{house} ({argala_grade})")
        elif net_argala > 10:
            score = 10
            reasons.append(f"Moderate Argala support for H{house}")
        elif net_argala < -10:
            score = -10
            reasons.append(f"⚠️ Moderate obstruction for H{house}")
        
        return score, reasons
    
    def _get_confidence_level(self, score: int) -> str:
        """Get confidence level based on Jaimini score"""
        if score >= 80:
            return 'very_high'  # Both systems strongly agree
        elif score >= 50:
            return 'high'  # Strong Jaimini confirmation
        elif score >= 30:
            return 'moderate'  # Partial confirmation
        elif score >= 0:
            return 'low'  # Weak confirmation
        else:
            return 'conflicting'  # Jaimini disagrees (obstruction)
    
    def _get_sign_name(self, idx: int) -> str:
        """Get sign name from index"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[idx] if 0 <= idx < 12 else 'Unknown'
    
    def get_special_lagna_activation(self, house: int) -> Dict:
        """
        Check if special lagnas (AL, UL, KL) activate the house.
        
        Returns additional insights for specific life areas.
        """
        activations = []
        
        # Arudha Lagna (AL) - Wealth activation
        if house in [2, 11]:  # Wealth houses
            al_sign = self.points['arudha_lagna']['sign_id']
            asc_sign = int(self.chart_data['ascendant'] / 30)
            target_sign = (asc_sign + house - 1) % 12
            
            # Check 2nd/11th from AL
            second_from_al = (al_sign + 1) % 12
            eleventh_from_al = (al_sign + 10) % 12
            
            if target_sign in [second_from_al, eleventh_from_al]:
                activations.append({
                    'lagna': 'Arudha Lagna (AL)',
                    'significance': 'Wealth flow activation',
                    'strength': 'high'
                })
        
        # Upapada Lagna (UL) - Marriage activation
        if house == 7:  # Marriage house
            ul_sign = self.points['upapada_lagna']['sign_id']
            asc_sign = int(self.chart_data['ascendant'] / 30)
            target_sign = (asc_sign + house - 1) % 12
            
            # Check 2nd from UL (marriage longevity)
            second_from_ul = (ul_sign + 1) % 12
            
            if target_sign == second_from_ul:
                activations.append({
                    'lagna': 'Upapada Lagna (UL)',
                    'significance': 'Marriage timing activation',
                    'strength': 'very_high'
                })
        
        # Karakamsa Lagna (KL) - Career/Skills activation
        if house == 10:  # Career house
            kl_sign = self.points['karakamsa_lagna']['sign_id']
            asc_sign = int(self.chart_data['ascendant'] / 30)
            target_sign = (asc_sign + house - 1) % 12
            
            if kl_sign == target_sign:
                activations.append({
                    'lagna': 'Karakamsa Lagna (KL)',
                    'significance': 'Career destiny activation',
                    'strength': 'very_high'
                })
        
        return {
            'special_lagna_activations': activations,
            'count': len(activations)
        }
