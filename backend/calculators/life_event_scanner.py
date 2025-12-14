from typing import Dict, List, Any, Set
from datetime import datetime
from calculators.divisional_chart_calculator import DivisionalChartCalculator

class LifeEventScanner:
    """
    Scans a user's past timeline to identify 'Double Transit' years.
    PROFESSIONAL GRADE: Uses D1 (Birth) + D9 (Navamsa) + Moon Chart for high-precision timing.
    """
    
    def __init__(self, chart_calculator, dasha_calculator, real_transit_calculator):
        self.chart_calc = chart_calculator
        self.dasha_calc = dasha_calculator
        self.transit_calc = real_transit_calculator
        self.natal_planets = {} 
        self.d9_planets = {}
        
    def scan_timeline(self, birth_data: Dict, start_age: int = 18, end_age: int = 60) -> List[Dict]:
        try:
            # 1. Calculate D1 Natal Chart (The Body)
            from types import SimpleNamespace
            birth_obj = SimpleNamespace(**birth_data)
            natal_chart = self.chart_calc.calculate_chart(birth_obj)
            self.natal_planets = natal_chart['planets']
            
            # 2. Calculate D9 Navamsa Chart (The Soul/Marriage Specific)
            # We initialize the calculator with the D1 chart data
            div_calc = DivisionalChartCalculator(natal_chart)
            d9_data = div_calc.calculate_divisional_chart(9)
            self.d9_planets = d9_data['divisional_chart']['planets']
            
            # 3. Get Comprehensive Significators (D1 + D9 + Moon)
            sig = self._get_significators(natal_chart, d9_data['divisional_chart'])
            
            # 4. Iterate Years
            # Handle both ISO format and simple date format
            date_str = birth_data['date']
            if 'T' in date_str:
                birth_year = datetime.fromisoformat(date_str.replace('Z', '+00:00')).year
            else:
                birth_year = datetime.strptime(date_str, '%Y-%m-%d').year
            current_year = datetime.now().year
            
            # Allow scanning up to current year
            scan_end = min(birth_year + end_age, current_year)
            
            events = []
            
            for year in range(birth_year + start_age, scan_end + 1):
                age = year - birth_year
                
                # A. Get Transits (Multi-point scan)
                transits = self._get_transit_span(year)
                
                # B. Get Dasha
                check_date = datetime(year, 7, 1)
                dashas = self.dasha_calc.calculate_dashas_for_date(check_date, birth_data)
                
                # C. Check Locks (Deep Analysis)
                marriage_score = self._check_marriage_lock(sig, dashas, transits, age)
                
                # Only adding Marriage logic for now as it's the priority
                # Threshold: Needs 3.0+ score (Verification by D9 required for high score)
                if marriage_score >= 3.0:
                    confidence = "High" if marriage_score >= 5.0 else "Medium"
                    
                    # Construct specific reason based on what triggered it
                    reason = self._generate_reason(sig, dashas, marriage_score)
                    
                    events.append({
                        "year": year,
                        "age": age,
                        "type": "relationship",
                        "label": "Marriage / Serious Relationship",
                        "confidence": confidence,
                        "score": marriage_score,
                        "reason": reason
                    })
            
            # 5. SORTING ALGORITHM
            # Priority 1: High Score (Astrological Certainty)
            # Priority 2: Year Ascending (Earliest occurrence is usually the Wedding)
            events.sort(key=lambda x: (-x['score'], x['year']))
            
            # Filter duplicates (e.g. 2012 and 2013 picking up same event)
            unique_events = []
            seen_years = set()
            for e in events:
                # Group years close together (e.g. 2012/2013) into the stronger one
                is_duplicate = False
                for existing_year in seen_years:
                    if abs(e['year'] - existing_year) <= 1:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_events.append(e)
                    seen_years.add(e['year'])
            
            return unique_events[:1] # Return ONLY the single strongest match for calibration
            
        except Exception as e:
            print(f"❌ Scanner Logic Failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _generate_reason(self, sig: Dict, dashas: Dict, score: float) -> str:
        """Generates a human-readable astrological reason"""
        md = dashas['mahadasha']['planet']
        reason = f"Active Period: {md}"
        
        # Check if D9 triggered it
        if md == sig['d9_lord_7'] or md in sig['d9_occupants_7']:
            reason += " (Navamsa 7th Lord)"
        elif md == sig['d1_lord_7']:
            reason += " (7th House Lord)"
        elif md == 'Venus' or md == 'Jupiter':
            reason += " (Natural Karaka)"
            
        return reason + " + Double Transit Activation"

    def _get_transit_span(self, year: int) -> Dict[str, Set[int]]:
        """Checks Saturn/Jupiter positions at 3 points in the year"""
        t_data = {'Saturn': set(), 'Jupiter': set(), 'Rahu': set(), 'Ketu': set()}
        
        check_points = [
            datetime(year, 1, 15),
            datetime(year, 6, 15),
            datetime(year, 11, 15)
        ]
        
        for date in check_points:
            try:
                for planet in ['Saturn', 'Jupiter', 'Rahu', 'Ketu']:
                    pos = self.transit_calc.get_planet_position(date, planet)
                    if pos is not None:
                        t_data[planet].add(int(pos / 30))
            except:
                continue
        return t_data

    def _get_significators(self, d1_chart: Dict, d9_chart: Dict) -> Dict:
        """
        Extracts Marriage Significators from:
        1. D1 (Lagna Chart)
        2. Moon Chart (Chandra Lagna)
        3. D9 (Navamsa Chart)
        """
        # D1 Setup
        asc_sign = int(d1_chart['ascendant'] / 30)
        moon_sign = int(d1_chart['planets']['Moon']['longitude'] / 30)
        
        d1_7th_sign = (asc_sign + 6) % 12
        moon_7th_sign = (moon_sign + 6) % 12
        
        # D9 Setup
        d9_asc_sign = int(d9_chart['ascendant'] / 30)
        d9_7th_sign = (d9_asc_sign + 6) % 12
        
        # Helper to find occupants
        def get_occupants(chart, target_sign):
            occupants = []
            for planet, data in chart['planets'].items():
                if planet in ['Uranus', 'Neptune', 'Pluto', 'Gulika', 'Mandi']: continue
                if data['sign'] == target_sign:
                    occupants.append(planet)
            return occupants

        return {
            # D1 (Lagna)
            "d1_asc": asc_sign,
            "d1_7th": d1_7th_sign,
            "d1_lord_7": self._get_lord_of_sign(d1_7th_sign),
            "d1_occupants_7": get_occupants(d1_chart, d1_7th_sign),
            
            # Moon Chart
            "moon_sign": moon_sign,
            "moon_7th": moon_7th_sign,
            "moon_lord_7": self._get_lord_of_sign(moon_7th_sign),
            
            # D9 (Navamsa) - THE KEY
            "d9_asc": d9_asc_sign,
            "d9_7th": d9_7th_sign,
            "d9_lord_7": self._get_lord_of_sign(d9_7th_sign), # The "Soul" Marriage Giver
            "d9_occupants_7": get_occupants(d9_chart, d9_7th_sign),
            
            "venus_sign": d1_chart['planets']['Venus']['sign']
        }

    def _check_marriage_lock(self, sig: Dict, dashas: Dict, transits: Dict[str, Set[int]], age: int) -> float:
        score = 0.0
        md = dashas['mahadasha']['planet']
        ad = dashas['antardasha']['planet']
        
        # ---------------------------------------------------------
        # 1. AGE WEIGHTING (Bell Curve)
        # ---------------------------------------------------------
        if 23 <= age <= 33: score += 1.5
        elif 20 <= age <= 40: score += 0.5
        else: score -= 1.0 # Significant penalty for unlikely ages
        
        # ---------------------------------------------------------
        # 2. DASHA CHECK (The Promise)
        # ---------------------------------------------------------
        # We classify Dasha Lords by strength
        
        # Tier S: Navamsa 7th Lord OR Planet in Navamsa 7th (Strongest)
        tier_s = [sig['d9_lord_7']] + sig['d9_occupants_7']
        
        # Tier A: D1 7th Lord OR Occupant of D1 7th
        tier_a = [sig['d1_lord_7']] + sig['d1_occupants_7'] + ['Venus', 'Jupiter', 'Rahu']
        
        # Tier B: Moon Chart 7th Lord
        tier_b = [sig['moon_lord_7']]
        
        if md in tier_s: score += 3.0      # Massive boost for D9
        elif md in tier_a: score += 2.0
        elif md in tier_b: score += 1.5
        
        # Antardasha Support
        if ad in tier_s: score += 1.5
        elif ad in tier_a: score += 1.0
        
        # If Dasha score is low (< 1.5), transits usually don't matter.
        if score < 2.0: return 0 
        
        # ---------------------------------------------------------
        # 3. TRANSIT CHECK (The Trigger)
        # ---------------------------------------------------------
        
        # Jupiter Blessing (Aspects 1/5/7/9)
        jup_hits = False
        for j_sign in transits['Jupiter']:
            aspects = self._get_aspects(j_sign, 'Jupiter')
            # Does it touch D1 7th House or D1 7th Lord?
            if sig['d1_7th'] in aspects: jup_hits = True
            if self._get_planet_sign(sig['d1_lord_7']) in aspects: jup_hits = True
            # Does it touch D9 7th House? (Subtle but powerful)
            if sig['d9_7th'] in aspects: jup_hits = True
            
        if jup_hits: score += 1.5
        
        # Saturn Sanction (Aspects 1/3/7/10)
        sat_hits = False
        for s_sign in transits['Saturn']:
            aspects = self._get_aspects(s_sign, 'Saturn')
            if sig['d1_7th'] in aspects: sat_hits = True
            if sig['d9_7th'] in aspects: sat_hits = True # Saturn impacting Navamsa marriage house
            
        if sat_hits: score += 1.0
        
        # Double Transit Bonus (The Gold Standard)
        if jup_hits and sat_hits: score += 1.5
        
        return score

    def _get_aspects(self, sign: int, planet: str) -> List[int]:
        aspects = [sign]
        if planet == 'Saturn': aspects.extend([(sign+2)%12, (sign+6)%12, (sign+9)%12])
        elif planet == 'Jupiter': aspects.extend([(sign+4)%12, (sign+6)%12, (sign+8)%12])
        return aspects

    def _get_lord_of_sign(self, sign_idx):
        lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        return lords[sign_idx]
        
    def _get_planet_sign(self, planet_name):
        # Helper to find current natal sign of any lord (from D1 cache)
        if planet_name in self.natal_planets:
            return self.natal_planets[planet_name]['sign']
        return -1