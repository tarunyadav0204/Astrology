from typing import Dict, List, Any, Set
from datetime import datetime

class LifeEventScanner:
    """
    Scans a user's past timeline to identify 'Double Transit' years.
    TUNED: Uses 'Age Weighting' to prioritize typical life stages (e.g., Marriage at 25-32).
    """
    
    def __init__(self, chart_calculator, dasha_calculator, real_transit_calculator):
        self.chart_calc = chart_calculator
        self.dasha_calc = dasha_calculator
        self.transit_calc = real_transit_calculator
        self.natal_planets = {}  # Cache for quick lookup
        
    def scan_timeline(self, birth_data: Dict, start_age: int = 18, end_age: int = 60) -> List[Dict]:
        """
        Scans years to find major life events (Marriage, Career).
        """
        try:
            # 1. Calculate Natal Chart ONCE (The "Promise")
            from types import SimpleNamespace
            birth_obj = SimpleNamespace(**birth_data)
            natal_chart = self.chart_calc.calculate_chart(birth_obj)
            
            # Store natal planets for lookup
            self.natal_planets = natal_chart['planets']
            
            # Get key targets (7th Lord, 10th Lord, etc.)
            sig = self._get_significators(natal_chart)
            
            # 2. Iterate Years
            birth_year = datetime.strptime(birth_data['date'], '%Y-%m-%d').year
            current_year = datetime.now().year
            
            # CORRECT LOGIC: Scan up to current year. Events happen today too.
            scan_end = min(birth_year + end_age, current_year)
            
            events = []
            
            for year in range(birth_year + start_age, scan_end + 1):
                age = year - birth_year
                
                # A. Get Transits (Multi-point scan)
                transits = self._get_transit_span(year)
                
                # B. Get Dasha
                check_date = datetime(year, 7, 1)
                dashas = self.dasha_calc.calculate_dashas_for_date(check_date, birth_data)
                
                # C. Check Locks with Age Weighting
                marriage_score = self._check_marriage_lock(sig, dashas, transits, age)
                career_score = self._check_career_lock(sig, dashas, transits, age)
                
                # Thresholds (Higher threshold to reduce noise)
                if marriage_score >= 4.0:
                    events.append({
                        "year": year,
                        "age": age,
                        "type": "relationship",
                        "label": "Relationship Milestone",
                        "confidence": "High",
                        "score": marriage_score,
                        "reason": f"Strong Activation: {dashas['mahadasha']['planet']} Dasha + Jupiter/Saturn Alignment"
                    })
                
                elif career_score >= 4.0:
                    events.append({
                        "year": year,
                        "age": age,
                        "type": "career",
                        "label": "Career Rise / Change",
                        "confidence": "High",
                        "score": career_score,
                        "reason": f"Strong Activation: {dashas['mahadasha']['planet']} Dasha + Saturn Impact"
                    })
            
            # SORT LOGIC: Strictly by Score
            # The Age Weighting inside the score already handles the "Best Year" logic.
            events.sort(key=lambda x: x['score'], reverse=True)
            
            # Filter out current/future years if we have a good past candidate
            past_events = [e for e in events if e['year'] < current_year]
            if past_events:
                return past_events[:2]
                
            return events[:2]
            
        except Exception as e:
            print(f"❌ Scanner Logic Failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_transit_span(self, year: int) -> Dict[str, Set[int]]:
        """
        Checks Saturn/Jupiter positions at 3 points in the year to catch sign changes.
        Returns a Set of signs occupied during the year.
        """
        sat_signs = set()
        jup_signs = set()
        
        # Check Jan, May, Oct to cover all movements
        check_points = [
            datetime(year, 1, 15),
            datetime(year, 5, 15),
            datetime(year, 10, 15)
        ]
        
        for date in check_points:
            try:
                s_pos = self.transit_calc.get_planet_position(date, 'Saturn')
                j_pos = self.transit_calc.get_planet_position(date, 'Jupiter')
                
                if s_pos: sat_signs.add(int(s_pos / 30))
                if j_pos: jup_signs.add(int(j_pos / 30))
            except:
                continue
                
        return {'Saturn': sat_signs, 'Jupiter': jup_signs}

    def _get_significators(self, chart: Dict) -> Dict:
        asc_sign = int(chart['ascendant'] / 30)
        
        house_7_sign = (asc_sign + 6) % 12
        house_10_sign = (asc_sign + 9) % 12
        
        # Identify Occupants (Planets sitting in the house)
        occupants_7 = []
        occupants_10 = []
        
        for planet, data in chart['planets'].items():
            if planet in ['Uranus', 'Neptune', 'Pluto']: continue
            p_sign = int(data['longitude'] / 30)
            
            if p_sign == house_7_sign:
                occupants_7.append(planet)
            elif p_sign == house_10_sign:
                occupants_10.append(planet)

        return {
            "asc_sign": asc_sign,
            "house_7_sign": house_7_sign,
            "lord_7": self._get_lord_of_sign(house_7_sign),
            "occupants_7": occupants_7,
            "house_10_sign": house_10_sign,
            "lord_10": self._get_lord_of_sign(house_10_sign),
            "occupants_10": occupants_10,
            "venus_sign": int(chart['planets']['Venus']['longitude'] / 30)
        }

    def _check_marriage_lock(self, sig: Dict, dashas: Dict, transits: Dict[str, Set[int]], age: int) -> float:
        score = 0.0
        md = dashas['mahadasha']['planet']
        ad = dashas['antardasha']['planet']
        
        # 1. AGE WEIGHTING (The "Golden Window")
        # Prioritize typically marital ages (23-34)
        if 23 <= age <= 34: score += 1.5
        elif 20 <= age <= 40: score += 0.5
        else: score -= 0.5  # Deprioritize very young/old for "First Marriage" calibration
        
        # 2. DASHA CHECK
        valid_dasha_lords = [sig['lord_7'], 'Venus', 'Jupiter', 'Rahu'] + sig['occupants_7']
        
        if md in valid_dasha_lords: score += 2.0  # Mahadasha is stronger
        elif ad in valid_dasha_lords: score += 1.5
        else: return 0  # No Dasha support = No Event
        
        # 3. SATURN CHECK
        sat_hits = False
        for s_sign in transits['Saturn']:
            aspects = self._get_aspects(s_sign, 'Saturn')
            if sig['house_7_sign'] in aspects: sat_hits = True
            if self._get_sign_of_planet(sig['lord_7']) in aspects: sat_hits = True
            
        if sat_hits: score += 1.0
        
        # 4. JUPITER CHECK
        jup_hits = False
        for j_sign in transits['Jupiter']:
            aspects = self._get_aspects(j_sign, 'Jupiter')
            if sig['house_7_sign'] in aspects: jup_hits = True
            if self._get_sign_of_planet(sig['lord_7']) in aspects: jup_hits = True
            
        if jup_hits: score += 1.0
        
        # 5. SPECIAL: Double Transit Bonus
        if sat_hits and jup_hits: score += 1.0
        
        return score

    def _check_career_lock(self, sig: Dict, dashas: Dict, transits: Dict[str, Set[int]], age: int) -> float:
        score = 0.0
        md = dashas['mahadasha']['planet']
        
        # Age Weighting for Career (Peak Ages)
        if 26 <= age <= 45: score += 1.0
        
        # Valid Dasha
        valid_lords = [sig['lord_10'], 'Saturn', 'Sun', 'Mercury'] + sig['occupants_10']
        if md in valid_lords: score += 2.0
        else: return 0
        
        # Transits
        sat_hits = False
        for s_sign in transits['Saturn']:
            aspects = self._get_aspects(s_sign, 'Saturn')
            if sig['house_10_sign'] in aspects: sat_hits = True
        
        if sat_hits: score += 1.0
        
        jup_hits = False
        for j_sign in transits['Jupiter']:
            aspects = self._get_aspects(j_sign, 'Jupiter')
            if sig['house_10_sign'] in aspects: jup_hits = True
            
        if jup_hits: score += 1.0
        if sat_hits and jup_hits: score += 1.0
        
        return score

    def _get_aspects(self, sign: int, planet: str) -> List[int]:
        """Calculates Vedic aspects (Drishti)"""
        aspects = [sign]
        if planet == 'Saturn': aspects.extend([(sign+2)%12, (sign+6)%12, (sign+9)%12])
        elif planet == 'Jupiter': aspects.extend([(sign+4)%12, (sign+6)%12, (sign+8)%12])
        return aspects

    def _get_lord_of_sign(self, sign_idx):
        lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        return lords[sign_idx]

    def _get_sign_of_planet(self, planet_name):
        if planet_name in self.natal_planets:
            return int(self.natal_planets[planet_name]['longitude'] / 30)
        return 0
