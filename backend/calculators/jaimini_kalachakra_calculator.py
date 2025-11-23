# Authentic Jaimini Kalchakra Dasha Calculator
import swisseph as swe
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from .base_calculator import BaseCalculator
from .jaimini_rashi_strength import JaiminiRashiStrength

class JaiminiKalachakraCalculator(BaseCalculator):
    """
    Authentic Jaimini Kalchakra Dasha Calculator
    Based on classical Jaimini principles - rashi-based only
    """

    def __init__(self, chart_data: Dict[str, Any]):
        super().__init__(chart_data)
        
        # Classical fixed-year durations (1-12 indexing)
        self.CLASSICAL_YEARS = {
            1: 6, 2: 7, 3: 8, 4: 9,
            5: 7, 6: 6, 7: 8, 8: 9,
            9: 10, 10: 7, 11: 6, 12: 7
        }
        
        # Ensure Swiss Ephemeris is initialized
        try:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        except:
            pass

    def calculate_jaimini_kalachakra_dasha(self, birth_data: Dict[str, Any] = None, current_date: datetime = None) -> Dict[str, Any]:
        """Main entry point for Jaimini Kalchakra Dasha calculation"""
        
        if current_date is None:
            current_date = datetime.utcnow().replace(tzinfo=timezone.utc)
        elif current_date.tzinfo is None:
            current_date = current_date.replace(tzinfo=timezone.utc)

        try:
            # Step 1: Get Moon's Rashi (Janma Rashi) - convert to 1-12
            moon_data = self.chart_data['planets']['Moon']
            janma_rashi = moon_data['sign'] + 1  # Convert 0-11 to 1-12
            
            # Step 2: Determine initial direction
            direction1 = self._get_initial_direction(janma_rashi)
            
            # Step 3: Determine chakras and sequences
            chakra1_signs, chakra2_signs = self._determine_chakras(janma_rashi, direction1)
            
            # Step 4: Calculate direction for chakra 2
            direction2 = not direction1
            
            # Step 5: Build complete dasha sequence
            if birth_data:
                birth_jd = self._parse_birth_jd(birth_data)
            else:
                # Use chart data birth time if available
                birth_jd = self.chart_data.get('birth_jd', swe.julday(2000, 1, 1, 12.0))
            mahadashas, skipped_rashis = self._build_mahadasha_sequence(
                chakra1_signs, chakra2_signs, direction1, direction2, birth_jd
            )
            
            # Step 6: Find current periods
            jd_now = self._current_jd(current_date)
            current_maha = self._find_current_mahadasha(mahadashas, jd_now)
            
            # Build actual working dasha sequence used in mahadashas (cycle 1 only)
            working_seq = [p["sign"] + 1 for p in mahadashas if p["cycle"] == 1]
            current_antar = self._calculate_antardasha(current_maha, working_seq, jd_now)
            
            return {
                'system': 'Jaimini Kalchakra',
                'janma_rashi': janma_rashi - 1,  # Convert back to 0-11 for display
                'janma_rashi_name': self.SIGN_NAMES[janma_rashi - 1],
                'chakra1_direction': 'Forward' if direction1 else 'Backward',
                'chakra2_direction': 'Forward' if direction2 else 'Backward',
                'chakra1_signs': [self.SIGN_NAMES[s - 1] for s in chakra1_signs],
                'chakra2_signs': [self.SIGN_NAMES[s - 1] for s in chakra2_signs],
                'mahadashas': mahadashas,
                'skipped_rashis': skipped_rashis,
                'current_mahadasha': current_maha,
                'current_antardasha': current_antar
            }

        except Exception as ex:
            return {'system': 'Jaimini Kalchakra', 'error': str(ex)}

    def _inc_sign(self, sign: int) -> int:
        """Increment sign with proper 1-12 wrapping"""
        sign += 1
        if sign > 12:
            sign = 1
        return sign
    
    def _dec_sign(self, sign: int) -> int:
        """Decrement sign with proper 1-12 wrapping"""
        sign -= 1
        if sign < 1:
            sign = 12
        return sign

    def _get_initial_direction(self, janma_rashi: int) -> bool:
        """Determine initial direction based on odd/even rashi"""
        return janma_rashi % 2 == 1  # Odd = Forward, Even = Backward

    def _determine_chakras(self, janma_rashi: int, direction1: bool) -> Tuple[List[int], List[int]]:
        """Classical Jaimini: Chakra1 = 8 consecutive signs; Chakra2 = remaining 4."""
        
        # Chakra 1 — 8 signs
        chakra1 = []
        s = janma_rashi
        for _ in range(8):
            chakra1.append(s)
            s = self._inc_sign(s) if direction1 else self._dec_sign(s)

        # Chakra 2 — remaining 4 signs, start from first unused after last chakra1 sign
        last = chakra1[-1]
        start = self._inc_sign(last)
        while start in chakra1:
            start = self._inc_sign(start)

        direction2 = not direction1
        chakra2 = []
        s = start

        while len(chakra2) < 4:
            if s not in chakra1 and s not in chakra2:
                chakra2.append(s)
            s = self._inc_sign(s) if direction2 else self._dec_sign(s)

        return chakra1, chakra2

    def _build_mahadasha_sequence(self, chakra1, chakra2, direction1, direction2, birth_jd, max_years=120):
        """Jaimini Kalchakra with proper rashi skipping based on planetary strength"""
        
        mahadashas = []
        skipped_rashis = []
        current_jd = birth_jd
        cycle_num = 1
        forward = direction1
        
        # Start from janma rashi
        janma_rashi = chakra1[0]  # First sign in chakra1
        current_sign = janma_rashi
        
        while current_jd < birth_jd + (max_years * 365.2425):
            # Check if current sign should be skipped based on planetary strength
            skip_sign = self._should_skip_rashi(current_sign, cycle_num)
            
            if skip_sign:
                # Track skipped rashi with reasons
                strength_calc = JaiminiRashiStrength(self.chart_data)
                skip_reasons = strength_calc.get_skip_reasons(current_sign - 1)
                
                print(f"DEBUG: Skipping {self.SIGN_NAMES[current_sign - 1]} in cycle {cycle_num} (strength: {skip_reasons.get('total_strength', 0)})")
                
                skipped_rashis.append({
                    "sign": current_sign - 1,
                    "sign_name": self.SIGN_NAMES[current_sign - 1],
                    "cycle": cycle_num,
                    "chakra": 1 if current_sign in chakra1 else 2,
                    "skip_reasons": skip_reasons
                })
            else:
                years = self.CLASSICAL_YEARS[current_sign]
                days = years * 365.2425
                end_jd = current_jd + days
                
                mahadashas.append({
                    "sign": current_sign - 1,  # Convert to 0-11 for display
                    "sign_name": self.SIGN_NAMES[current_sign - 1],
                    "years": years,
                    "start_jd": current_jd,
                    "end_jd": end_jd,
                    "start_iso": self._jd_to_iso_utc(current_jd),
                    "end_iso": self._jd_to_iso_utc(end_jd - 1/86400.0),
                    "chakra": 1 if current_sign in chakra1 else 2,
                    "direction": "Forward" if forward else "Backward",
                    "cycle": cycle_num,
                    "current": False
                })
                
                current_jd = end_jd
            
            # Move to next sign
            if forward:
                current_sign = self._inc_sign(current_sign)
            else:
                current_sign = self._dec_sign(current_sign)
            
            # Check if we completed a cycle (back to janma rashi)
            if current_sign == janma_rashi:
                cycle_num += 1
                forward = not forward  # Reverse direction for next cycle
        
        print(f"DEBUG: Total skipped rashis: {len(skipped_rashis)}")
        return mahadashas, skipped_rashis
    
    def _should_skip_rashi(self, sign: int, cycle_num: int) -> bool:
        """Determine if a rashi should be skipped based on comprehensive strength analysis"""
        if cycle_num == 1:
            return False  # Never skip in first cycle
        
        # Convert to 0-11 for chart lookup
        sign_index = sign - 1
        
        # Use comprehensive rashi strength calculator
        strength_calc = JaiminiRashiStrength(self.chart_data)
        return strength_calc.is_weak_rashi(sign_index, threshold=25.0)

    def _calculate_antardasha(self, maha, full_seq, jd_now):
        """Classical proportional antardasha."""

        if not maha:
            return {}

        maha_sign = maha["sign"] + 1  # Convert to 1-12

        # antar order = maha_sign rotated sequence
        start_idx = full_seq.index(maha_sign)
        antar_seq = full_seq[start_idx:] + full_seq[:start_idx]

        total_years = sum(self.CLASSICAL_YEARS[s] for s in antar_seq)
        maha_days = maha["end_jd"] - maha["start_jd"]

        cursor = maha["start_jd"]

        for sign in antar_seq:
            proportion = self.CLASSICAL_YEARS[sign] / total_years
            days = maha_days * proportion

            if cursor <= jd_now < cursor + days:
                return {
                    "sign": sign - 1,  # Convert to 0-11 for display
                    "sign_name": self.SIGN_NAMES[sign - 1],
                    "start_date": self._jd_to_iso_utc(cursor),
                    "end_date": self._jd_to_iso_utc(cursor + days - 1/86400.0)
                }

            cursor += days

        # fallback last antar
        return {
            "sign": antar_seq[-1] - 1,
            "sign_name": self.SIGN_NAMES[antar_seq[-1] - 1]
        }
    
    def _parse_birth_jd(self, birth_data: Dict[str, Any]) -> float:
        """Convert birth data to Julian Day"""
        try:
            # Handle different birth data formats
            if 'date' in birth_data and 'time' in birth_data:
                # Format: {'date': '1980-05-15', 'time': '14:30'}
                date_str = birth_data['date']
                time_str = birth_data['time']
                
                # Parse date
                year, month, day = map(int, date_str.split('-'))
                
                # Parse time
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                second = int(time_parts[2]) if len(time_parts) > 2 else 0
            else:
                # Legacy format: {'year': 1980, 'month': 5, 'day': 15, 'hour': 14}
                year = birth_data['year']
                month = birth_data['month']
                day = birth_data['day']
                hour = birth_data.get('hour', 0)
                minute = birth_data.get('minute', 0)
                second = birth_data.get('second', 0)
            
            # Convert to decimal hours
            decimal_hour = hour + minute/60.0 + second/3600.0
            
            # Calculate Julian Day
            jd = swe.julday(year, month, day, decimal_hour)
            return jd
        except Exception as e:
            print(f"Birth JD parsing error: {e}, birth_data: {birth_data}")
            # Fallback to current date if parsing fails
            now = datetime.utcnow()
            return swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
    
    def _current_jd(self, current_date: datetime) -> float:
        """Convert current datetime to Julian Day"""
        return swe.julday(
            current_date.year, 
            current_date.month, 
            current_date.day,
            current_date.hour + current_date.minute/60.0 + current_date.second/3600.0
        )
    
    def _jd_to_iso_utc(self, jd: float) -> str:
        """Convert Julian Day to ISO UTC string"""
        try:
            year, month, day, hour = swe.revjul(jd)
            # Convert decimal hour to hour, minute, second
            h = int(hour)
            m = int((hour - h) * 60)
            s = int(((hour - h) * 60 - m) * 60)
            
            dt = datetime(year, month, day, h, m, s, tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    
    def _find_current_mahadasha(self, mahadashas: List[Dict], jd_now: float) -> Dict:
        """Find current mahadasha period"""
        for maha in mahadashas:
            if maha['start_jd'] <= jd_now < maha['end_jd']:
                maha['current'] = True
                return maha
        
        # If not found, return the last period
        if mahadashas:
            return mahadashas[-1]
        
        return {}
    
    def get_antardasha_details(self, maha_sign: int, antar_sign: int) -> Dict[str, Any]:
        """Get detailed information for a specific antardasha period"""
        return {
            "sign": antar_sign,
            "sign_name": self.SIGN_NAMES[antar_sign],
            "strength_score": self._calculate_strength_score(antar_sign),
            "keywords": self._get_sign_keywords(antar_sign),
            "house_impact": self._get_house_impact(antar_sign),
            "events_likely": self._get_likely_events(antar_sign)
        }
    
    def get_all_antardashas_for_maha(self, maha_sign: int, maha_start_jd: float, maha_end_jd: float) -> List[Dict]:
        """Get all antardasha periods for a given mahadasha"""
        # Convert to 1-12 for internal calculations
        maha_sign_internal = maha_sign + 1
        
        # Get working sequence (cycle 1)
        working_seq = list(range(1, 13))  # Simplified - should use actual sequence
        
        # Rotate sequence starting from maha sign
        start_idx = working_seq.index(maha_sign_internal)
        antar_seq = working_seq[start_idx:] + working_seq[:start_idx]
        
        total_years = sum(self.CLASSICAL_YEARS[s] for s in antar_seq)
        maha_days = maha_end_jd - maha_start_jd
        
        antardashas = []
        cursor = maha_start_jd
        
        for sign in antar_seq:
            proportion = self.CLASSICAL_YEARS[sign] / total_years
            days = maha_days * proportion
            
            antardashas.append({
                "sign": sign - 1,  # Convert to 0-11
                "sign_name": self.SIGN_NAMES[sign - 1],
                "start_jd": cursor,
                "end_jd": cursor + days,
                "start_date": self._jd_to_iso_utc(cursor),
                "end_date": self._jd_to_iso_utc(cursor + days - 1/86400.0),
                "duration_days": days,
                "current": False  # Will be set by frontend
            })
            
            cursor += days
        
        return antardashas
    
    def _calculate_strength_score(self, sign: int) -> int:
        """Calculate strength score (0-100) for a sign"""
        # Basic strength calculation based on sign characteristics
        base_scores = {
            0: 75, 1: 65, 2: 80, 3: 70,  # Aries, Taurus, Gemini, Cancer
            4: 85, 5: 60, 6: 70, 7: 75,  # Leo, Virgo, Libra, Scorpio
            8: 80, 9: 65, 10: 75, 11: 70  # Sagittarius, Capricorn, Aquarius, Pisces
        }
        
        base_score = base_scores.get(sign, 70)
        
        # Modify based on planets in the sign
        if 'planets' in self.chart_data:
            planets_in_sign = [p for p, data in self.chart_data['planets'].items() 
                             if data['sign'] == sign]
            
            # Add points for benefic planets, subtract for malefics
            for planet in planets_in_sign:
                if planet in ['Jupiter', 'Venus', 'Moon']:
                    base_score += 10
                elif planet in ['Mars', 'Saturn']:
                    base_score -= 5
        
        return min(100, max(0, base_score))
    
    def _get_sign_keywords(self, sign: int) -> List[str]:
        """Get keywords for a sign"""
        keywords_map = {
            0: ["Leadership", "Initiative", "Energy", "New Beginnings"],
            1: ["Stability", "Resources", "Comfort", "Material Growth"],
            2: ["Communication", "Learning", "Adaptability", "Networking"],
            3: ["Emotions", "Home", "Family", "Nurturing"],
            4: ["Creativity", "Recognition", "Authority", "Self-Expression"],
            5: ["Service", "Health", "Details", "Improvement"],
            6: ["Relationships", "Balance", "Partnerships", "Harmony"],
            7: ["Transformation", "Intensity", "Research", "Hidden Matters"],
            8: ["Philosophy", "Travel", "Higher Learning", "Expansion"],
            9: ["Career", "Discipline", "Structure", "Achievement"],
            10: ["Innovation", "Friendship", "Groups", "Humanitarian"],
            11: ["Spirituality", "Intuition", "Compassion", "Sacrifice"]
        }
        return keywords_map.get(sign, ["Growth", "Change", "Experience"])
    
    def _get_house_impact(self, sign: int) -> Dict[str, str]:
        """Get house impact from Lagna and Moon"""
        lagna_sign = self.chart_data.get('ascendant', {}).get('sign', 0)
        moon_sign = self.chart_data['planets']['Moon']['sign']
        
        # Calculate house positions
        lagna_house = (sign - lagna_sign) % 12 + 1
        moon_house = (sign - moon_sign) % 12 + 1
        
        house_meanings = {
            1: "Self, Personality", 2: "Wealth, Family", 3: "Siblings, Courage",
            4: "Home, Mother", 5: "Children, Creativity", 6: "Health, Service",
            7: "Partnership, Marriage", 8: "Transformation, Occult", 9: "Fortune, Dharma",
            10: "Career, Status", 11: "Gains, Friends", 12: "Loss, Spirituality"
        }
        
        return {
            "from_lagna": f"{lagna_house}H - {house_meanings.get(lagna_house, 'Unknown')}",
            "from_moon": f"{moon_house}H - {house_meanings.get(moon_house, 'Unknown')}"
        }
    
    def _get_likely_events(self, sign: int) -> List[str]:
        """Get likely events for a sign period"""
        events_map = {
            0: ["Career advancement", "New projects", "Leadership roles"],
            1: ["Financial growth", "Property matters", "Comfort increase"],
            2: ["Communication success", "Learning opportunities", "Short travels"],
            3: ["Family events", "Home changes", "Emotional developments"],
            4: ["Recognition", "Creative projects", "Authority positions"],
            5: ["Health focus", "Service opportunities", "Skill development"],
            6: ["Relationship changes", "Partnerships", "Legal matters"],
            7: ["Major transformations", "Research success", "Hidden revelations"],
            8: ["Long travels", "Higher education", "Philosophical growth"],
            9: ["Career peaks", "Structural changes", "Responsibility increase"],
            10: ["Social expansion", "Group activities", "Innovative projects"],
            11: ["Spiritual growth", "Charitable activities", "Inner development"]
        }
        return events_map.get(sign, ["Personal growth", "Life changes", "New experiences"])