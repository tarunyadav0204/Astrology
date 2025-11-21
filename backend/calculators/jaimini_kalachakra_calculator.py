# Authentic Jaimini Kalchakra Dasha Calculator
import swisseph as swe
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple
from .base_calculator import BaseCalculator
from .divisional_chart_calculator import DivisionalChartCalculator
from .shadbala_calculator import ShadbalaCalculator
from .aspect_calculator import AspectCalculator

class JaiminiKalachakraCalculator(BaseCalculator):
    """
    Authentic Jaimini Kalchakra Dasha Calculator
    Based on classical Jaimini principles with proper reversals and jumps
    """

    def __init__(self, chart_data: Dict[str, Any]):
        super().__init__(chart_data)
        self.divisional_calc = DivisionalChartCalculator(chart_data)
        self.shadbala_calc = ShadbalaCalculator(chart_data)
        self.aspect_calc = AspectCalculator(chart_data)
        
        # Ensure Swiss Ephemeris is initialized
        try:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        except:
            pass

    def calculate_jaimini_kalachakra_dasha(self, birth_data: Dict[str, Any], current_date: datetime = None) -> Dict[str, Any]:
        """Main entry point for Jaimini Kalchakra Dasha calculation"""
        
        if current_date is None:
            current_date = datetime.utcnow().replace(tzinfo=timezone.utc)
        elif current_date.tzinfo is None:
            current_date = current_date.replace(tzinfo=timezone.utc)

        try:
            # Step 1: Get Moon's Rashi (Janma Rashi)
            moon_data = self.chart_data['planets']['Moon']
            janma_rashi = moon_data['sign']
            
            # Step 2: Determine initial direction
            direction1 = self._get_initial_direction(janma_rashi)
            
            # Step 3: Calculate Navamsa chart for duration calculation
            navamsa_chart = self.divisional_calc.calculate_divisional_chart(9)
            
            # Step 4: Determine chakras and sequences
            chakra1_signs, chakra2_signs = self._determine_chakras(janma_rashi, direction1)
            
            # Step 5: Calculate direction for chakra 2 (with reversal logic)
            direction2 = self._calculate_chakra2_direction(chakra1_signs, direction1)
            
            # Step 6: Calculate sign durations based on navamsa occupation
            sign_durations = self._calculate_sign_durations(navamsa_chart)
            
            # Step 7: Apply jump logic for weak/empty signs
            processed_chakra1, processed_chakra2 = self._apply_jump_logic(
                chakra1_signs, chakra2_signs, sign_durations, navamsa_chart
            )
            
            # Step 8: Build complete dasha sequence
            birth_jd = self._parse_birth_jd(birth_data)
            mahadashas = self._build_mahadasha_sequence(
                processed_chakra1, processed_chakra2, 
                direction1, direction2, sign_durations, birth_jd
            )
            
            # Step 9: Find current periods
            jd_now = self._current_jd(current_date)
            current_maha = self._find_current_mahadasha(mahadashas, jd_now)
            current_antar = self._calculate_antardasha(current_maha, processed_chakra1 + processed_chakra2, jd_now)
            
            # Step 10: Calculate prediction insights
            prediction_insights = self._calculate_prediction_insights(mahadashas, current_date)
            
            # Step 11: Get comprehensive predictions
            comprehensive_predictions = self._get_comprehensive_predictions(mahadashas, current_date, self.chart_data)
            
            # Step 12: Get card data for multi-card layout
            card_data = {}
            if current_maha:
                card_data = self._get_card_data(current_maha, mahadashas, jd_now, self.chart_data)
            
            return {
                'system': 'Jaimini Kalchakra',
                'janma_rashi': janma_rashi,
                'janma_rashi_name': self.SIGN_NAMES[janma_rashi],
                'chakra1_direction': 'Forward' if direction1 else 'Backward',
                'chakra2_direction': 'Forward' if direction2 else 'Backward',
                'chakra1_signs': [self.SIGN_NAMES[s] for s in processed_chakra1],
                'chakra2_signs': [self.SIGN_NAMES[s] for s in processed_chakra2],
                'mahadashas': mahadashas,
                'current_mahadasha': current_maha,
                'current_antardasha': current_antar,
                'total_cycle_years': sum(sign_durations.values()),
                'reversals': self._detect_reversals(processed_chakra1, processed_chakra2, direction1, direction2),
                'jumps': self._detect_jumps(chakra1_signs + chakra2_signs, processed_chakra1 + processed_chakra2),
                'predictions': prediction_insights,
                'interpretations': comprehensive_predictions,
                'cards': card_data
            }

        except Exception as ex:
            return {'system': 'Jaimini Kalchakra', 'error': str(ex)}

    def _get_initial_direction(self, janma_rashi: int) -> bool:
        """Determine initial direction based on odd/even rashi"""
        return janma_rashi % 2 == 0  # Odd rashi (1,3,5...) = True (Forward), Even = False (Backward)

    def _determine_chakras(self, janma_rashi: int, direction1: bool) -> Tuple[List[int], List[int]]:
        """Determine 8-sign inner chakra and 4-sign outer chakra"""
        
        # Generate 8 consecutive signs for Chakra 1
        chakra1_signs = []
        current_sign = janma_rashi
        
        for i in range(8):
            chakra1_signs.append(current_sign)
            if direction1:  # Forward
                current_sign = (current_sign + 1) % 12
            else:  # Backward
                current_sign = (current_sign - 1) % 12
        
        # Remaining 4 signs for Chakra 2
        all_signs = set(range(12))
        used_signs = set(chakra1_signs)
        chakra2_signs = list(all_signs - used_signs)
        
        return chakra1_signs, chakra2_signs

    def _calculate_chakra2_direction(self, chakra1_signs: List[int], direction1: bool) -> bool:
        """Calculate direction for Chakra 2 - typically reversed from Chakra 1"""
        # Standard Jaimini rule: Direction flips between chakras
        return not direction1

    def _calculate_sign_durations(self, navamsa_chart: Dict[str, Any]) -> Dict[int, float]:
        """Calculate duration for each sign based on navamsa occupation by its lord"""
        
        sign_durations = {}
        navamsa_planets = navamsa_chart['divisional_chart']['planets']
        
        for sign_num in range(12):
            sign_lord = self.SIGN_LORDS[sign_num]
            
            # Count navamsas occupied by sign lord
            navamsa_count = 0
            
            # Check if sign lord is in navamsa chart
            if sign_lord in navamsa_planets:
                lord_data = navamsa_planets[sign_lord]
                lord_navamsa_sign = lord_data['sign']
                
                # Count planets in same navamsa sign as lord
                for planet, planet_data in navamsa_planets.items():
                    if planet_data['sign'] == lord_navamsa_sign:
                        navamsa_count += 1
            
            # Minimum 1 year, maximum based on strength
            base_years = max(1, navamsa_count)
            
            # Apply strength modifiers
            strength_modifier = self._get_sign_strength_modifier(sign_num, sign_lord)
            final_years = base_years * strength_modifier
            
            sign_durations[sign_num] = round(final_years, 2)
        
        return sign_durations

    def _get_sign_strength_modifier(self, sign_num: int, sign_lord: str) -> float:
        """Get strength modifier for sign based on lord's condition"""
        
        if sign_lord not in self.chart_data['planets']:
            return 1.0
        
        lord_data = self.chart_data['planets'][sign_lord]
        modifier = 1.0
        
        # Dignity-based modifiers
        dignity = self.get_planet_dignity(sign_lord, lord_data['sign'])
        if dignity == 'Exalted':
            modifier *= 1.5
        elif dignity == 'Own Sign':
            modifier *= 1.25
        elif dignity == 'Debilitated':
            modifier *= 0.5
        
        # Retrograde modifier
        if lord_data.get('retrograde', False):
            modifier *= 1.2
        
        # House position modifier
        house = lord_data.get('house', 1)
        if house in [1, 4, 7, 10]:  # Kendra houses
            modifier *= 1.1
        elif house in [5, 9]:  # Trikona houses
            modifier *= 1.15
        elif house in [6, 8, 12]:  # Dusthana houses
            modifier *= 0.8
        
        return modifier

    def _apply_jump_logic(self, chakra1_signs: List[int], chakra2_signs: List[int], 
                         sign_durations: Dict[int, float], navamsa_chart: Dict[str, Any]) -> Tuple[List[int], List[int]]:
        """Apply jump logic for weak or empty signs"""
        
        def should_jump_sign(sign_num: int) -> bool:
            """Determine if a sign should be jumped"""
            
            # Check if sign is empty (no planets)
            planets_in_sign = []
            for planet, planet_data in self.chart_data['planets'].items():
                if planet_data['sign'] == sign_num:
                    planets_in_sign.append(planet)
            
            # Jump if completely empty
            if not planets_in_sign:
                return True
            
            # Check sign lord strength
            sign_lord = self.SIGN_LORDS[sign_num]
            if sign_lord in self.chart_data['planets']:
                lord_data = self.chart_data['planets'][sign_lord]
                
                # Jump if lord is severely afflicted
                dignity = self.get_planet_dignity(sign_lord, lord_data['sign'])
                if dignity == 'Debilitated':
                    # Check for neecha bhanga (cancellation)
                    if not self._has_neecha_bhanga(sign_lord, lord_data):
                        return True
                
                # Jump if lord is combust
                if self._is_combust(sign_lord, lord_data):
                    return True
            
            # Jump if duration is too short (less than 6 months)
            if sign_durations.get(sign_num, 1) < 0.5:
                return True
            
            return False
        
        # Process Chakra 1
        processed_chakra1 = []
        for sign in chakra1_signs:
            if not should_jump_sign(sign):
                processed_chakra1.append(sign)
        
        # Process Chakra 2
        processed_chakra2 = []
        for sign in chakra2_signs:
            if not should_jump_sign(sign):
                processed_chakra2.append(sign)
        
        # Ensure minimum signs in each chakra
        if len(processed_chakra1) < 4:
            processed_chakra1 = chakra1_signs[:6]  # Keep at least 6 signs
        
        if len(processed_chakra2) < 2:
            processed_chakra2 = chakra2_signs  # Keep all if too few
        
        return processed_chakra1, processed_chakra2

    def _has_neecha_bhanga(self, planet: str, planet_data: Dict[str, Any]) -> bool:
        """Check for neecha bhanga (debilitation cancellation)"""
        
        planet_sign = planet_data['sign']
        debil_sign = self.DEBILITATION_SIGNS.get(planet)
        
        if planet_sign != debil_sign:
            return False
        
        # Check various neecha bhanga conditions
        # 1. Lord of debilitation sign in kendra from Moon/Lagna
        debil_lord = self.SIGN_LORDS[debil_sign]
        if debil_lord in self.chart_data['planets']:
            debil_lord_house = self.chart_data['planets'][debil_lord]['house']
            if debil_lord_house in [1, 4, 7, 10]:
                return True
        
        # 2. Exaltation lord in kendra
        exalt_sign = self.EXALTATION_SIGNS.get(planet)
        if exalt_sign is not None:
            exalt_lord = self.SIGN_LORDS[exalt_sign]
            if exalt_lord in self.chart_data['planets']:
                exalt_lord_house = self.chart_data['planets'][exalt_lord]['house']
                if exalt_lord_house in [1, 4, 7, 10]:
                    return True
        
        return False

    def _is_combust(self, planet: str, planet_data: Dict[str, Any]) -> bool:
        """Check if planet is combust (too close to Sun)"""
        
        if planet == 'Sun' or 'Sun' not in self.chart_data['planets']:
            return False
        
        sun_longitude = self.chart_data['planets']['Sun']['longitude']
        planet_longitude = planet_data['longitude']
        
        distance = abs(sun_longitude - planet_longitude)
        if distance > 180:
            distance = 360 - distance
        
        # Combustion distances
        combustion_distances = {
            'Moon': 12, 'Mars': 17, 'Mercury': 14,
            'Jupiter': 11, 'Venus': 10, 'Saturn': 15
        }
        
        return distance <= combustion_distances.get(planet, 8)

    def _build_mahadasha_sequence(self, chakra1_signs: List[int], chakra2_signs: List[int],
                                 direction1: bool, direction2: bool, sign_durations: Dict[int, float],
                                 birth_jd: float) -> List[Dict[str, Any]]:
        """Build complete mahadasha sequence with repeating cycles for full lifespan"""
        
        # Build one complete cycle first
        single_cycle = []
        cursor_jd = birth_jd
        
        # Process Chakra 1
        sequence1 = chakra1_signs if direction1 else list(reversed(chakra1_signs))
        for sign_num in sequence1:
            years = sign_durations.get(sign_num, 1.0)
            days = years * 365.2425
            
            single_cycle.append({
                'sign': sign_num,
                'sign_name': self.SIGN_NAMES[sign_num],
                'chakra': 1,
                'start_jd': cursor_jd,
                'end_jd': cursor_jd + days,
                'years': years,
                'direction': 'Forward' if direction1 else 'Backward'
            })
            cursor_jd += days
        
        # Process Chakra 2
        sequence2 = chakra2_signs if direction2 else list(reversed(chakra2_signs))
        for sign_num in sequence2:
            years = sign_durations.get(sign_num, 1.0)
            days = years * 365.2425
            
            single_cycle.append({
                'sign': sign_num,
                'sign_name': self.SIGN_NAMES[sign_num],
                'chakra': 2,
                'start_jd': cursor_jd,
                'end_jd': cursor_jd + days,
                'years': years,
                'direction': 'Forward' if direction2 else 'Backward'
            })
            cursor_jd += days
        
        # Calculate cycle length
        cycle_length_days = cursor_jd - birth_jd
        cycle_length_years = cycle_length_days / 365.2425
        
        # Generate cycles for 120 years lifespan
        mahadashas = []
        lifespan_days = 120 * 365.2425
        cycle_number = 0
        
        while birth_jd + (cycle_number * cycle_length_days) < birth_jd + lifespan_days:
            cycle_start_jd = birth_jd + (cycle_number * cycle_length_days)
            
            for period in single_cycle:
                # Calculate offset from original cycle
                offset_from_birth = period['start_jd'] - birth_jd
                new_start_jd = cycle_start_jd + offset_from_birth
                new_end_jd = new_start_jd + (period['end_jd'] - period['start_jd'])
                
                mahadashas.append({
                    'sign': period['sign'],
                    'sign_name': period['sign_name'],
                    'chakra': period['chakra'],
                    'start_jd': new_start_jd,
                    'end_jd': new_end_jd,
                    'start_iso': self._jd_to_iso_utc(new_start_jd),
                    'end_iso': self._jd_to_iso_utc(new_end_jd - 1/86400.0),
                    'years': period['years'],
                    'direction': period['direction'],
                    'cycle_number': cycle_number + 1
                })
            
            cycle_number += 1
        
        return mahadashas

    def _find_current_mahadasha(self, mahadashas: List[Dict[str, Any]], jd_now: float) -> Dict[str, Any]:
        """Find current mahadasha for given JD"""
        
        if not mahadashas:
            return {}
        
        if jd_now < mahadashas[0]['start_jd']:
            return mahadashas[0]
        
        for maha in mahadashas:
            if maha['start_jd'] <= jd_now < maha['end_jd']:
                return maha
        
        return mahadashas[-1]

    def _calculate_antardasha(self, maha: Dict[str, Any], full_sequence: List[int], jd_now: float) -> Dict[str, Any]:
        """Calculate current antardasha within mahadasha"""
        
        if not maha or not full_sequence:
            return {}
        
        maha_sign = maha['sign']
        
        # Antardasha sequence starts from mahadasha sign
        try:
            start_idx = full_sequence.index(maha_sign)
        except ValueError:
            start_idx = 0
        
        antar_sequence = []
        for i in range(len(full_sequence)):
            antar_sequence.append(full_sequence[(start_idx + i) % len(full_sequence)])
        
        # Calculate proportional antardashas based on sign durations
        maha_total_days = maha['end_jd'] - maha['start_jd']
        
        # Get sign durations (recalculate if needed)
        navamsa_chart = self.divisional_calc.calculate_divisional_chart(9)
        sign_durations = self._calculate_sign_durations(navamsa_chart)
        
        # Calculate total duration for proportion
        total_duration = sum(sign_durations.get(sign, 1.0) for sign in antar_sequence)
        
        cursor = maha['start_jd']
        for sign_num in antar_sequence:
            sign_duration = sign_durations.get(sign_num, 1.0)
            proportion = sign_duration / total_duration if total_duration > 0 else 1.0 / len(antar_sequence)
            days = maha_total_days * proportion
            
            if cursor <= jd_now < cursor + days:
                return {
                    'sign': sign_num,
                    'sign_name': self.SIGN_NAMES[sign_num],
                    'start_date': self._jd_to_iso_utc(cursor),
                    'end_date': self._jd_to_iso_utc(cursor + days - 1/86400.0)
                }
            cursor += days
        
        return {'sign': antar_sequence[-1], 'sign_name': self.SIGN_NAMES[antar_sequence[-1]]}

    def _detect_reversals(self, chakra1: List[int], chakra2: List[int], dir1: bool, dir2: bool) -> List[Dict[str, Any]]:
        """Detect and document direction reversals"""
        
        reversals = []
        
        # Primary chakra transition reversal
        if dir1 != dir2:
            reversals.append({
                'type': 'Chakra Transition',
                'from_direction': 'Forward' if dir1 else 'Backward',
                'to_direction': 'Forward' if dir2 else 'Backward',
                'at_sign': self.SIGN_NAMES[chakra1[-1]] if chakra1 else 'Unknown',
                'significance': 'Major life phase change - inner to outer focus'
            })
        
        # Always show cycle behavior
        reversals.append({
            'type': 'Cycle Repetition',
            'from_direction': f"Chakra 1: {'Forward' if dir1 else 'Backward'}",
            'to_direction': f"Chakra 2: {'Forward' if dir2 else 'Backward'}",
            'at_sign': f"After {self.SIGN_NAMES[chakra1[-1]] if chakra1 else 'Chakra1'}",
            'significance': 'Each 120-year cycle alternates direction pattern'
        })
        
        return reversals

    def _detect_jumps(self, original_sequence: List[int], processed_sequence: List[int]) -> List[Dict[str, Any]]:
        """Detect and document sign jumps"""
        
        jumps = []
        skipped_signs = set(original_sequence) - set(processed_sequence)
        
        for sign_num in skipped_signs:
            jumps.append({
                'type': 'Sign Jump',
                'skipped_sign': self.SIGN_NAMES[sign_num],
                'reason': 'Weak/Empty sign or severely afflicted lord',
                'significance': 'Accelerated karma or bypassed life area'
            })
        
        return jumps

    def _calculate_prediction_insights(self, mahadashas: List[Dict[str, Any]], current_date: datetime) -> Dict[str, Any]:
        """Calculate upcoming events and prediction insights"""
        
        current_jd = self._current_jd(current_date)
        insights = {
            'next_reversal': None,
            'next_cycle_reset': None,
            'upcoming_events': [],
            'cycle_progress': 0
        }
        
        if not mahadashas:
            return insights
        
        # Find current position and cycle info
        current_maha = None
        for maha in mahadashas:
            if maha['start_jd'] <= current_jd < maha['end_jd']:
                current_maha = maha
                break
        
        if not current_maha:
            return insights
        
        # Calculate cycle progress
        cycle_start_jd = None
        cycle_end_jd = None
        for maha in mahadashas:
            if maha['cycle_number'] == current_maha['cycle_number']:
                if cycle_start_jd is None or maha['start_jd'] < cycle_start_jd:
                    cycle_start_jd = maha['start_jd']
                if cycle_end_jd is None or maha['end_jd'] > cycle_end_jd:
                    cycle_end_jd = maha['end_jd']
        
        if cycle_start_jd and cycle_end_jd:
            cycle_progress = ((current_jd - cycle_start_jd) / (cycle_end_jd - cycle_start_jd)) * 100
            insights['cycle_progress'] = round(cycle_progress, 1)
        
        # Find next reversal (chakra transition)
        next_reversal_jd = None
        for maha in mahadashas:
            if maha['start_jd'] > current_jd and maha['cycle_number'] == current_maha['cycle_number']:
                # Check if this is a chakra transition
                prev_maha = None
                for prev in mahadashas:
                    if prev['end_jd'] == maha['start_jd'] and prev['cycle_number'] == maha['cycle_number']:
                        prev_maha = prev
                        break
                
                if prev_maha and prev_maha['chakra'] != maha['chakra']:
                    next_reversal_jd = maha['start_jd']
                    years_until = (next_reversal_jd - current_jd) / 365.2425
                    insights['next_reversal'] = {
                        'date': self._jd_to_iso_utc(next_reversal_jd),
                        'years_until': round(years_until, 1),
                        'from_chakra': prev_maha['chakra'],
                        'to_chakra': maha['chakra'],
                        'significance': 'Inner to outer focus shift' if maha['chakra'] == 2 else 'Outer to inner focus shift'
                    }
                    break
        
        # Find next cycle reset
        next_cycle_jd = None
        for maha in mahadashas:
            if maha['start_jd'] > current_jd and maha['cycle_number'] > current_maha['cycle_number']:
                next_cycle_jd = maha['start_jd']
                years_until = (next_cycle_jd - current_jd) / 365.2425
                insights['next_cycle_reset'] = {
                    'date': self._jd_to_iso_utc(next_cycle_jd),
                    'years_until': round(years_until, 1),
                    'cycle_number': maha['cycle_number']
                }
                break
        
        # Find upcoming events in next 2 years
        two_years_jd = current_jd + (2 * 365.2425)
        for maha in mahadashas:
            if current_jd < maha['start_jd'] <= two_years_jd:
                years_until = (maha['start_jd'] - current_jd) / 365.2425
                event_type = 'Chakra Transition' if any(p['end_jd'] == maha['start_jd'] and p['chakra'] != maha['chakra'] for p in mahadashas) else 'Sign Change'
                
                insights['upcoming_events'].append({
                    'date': self._jd_to_iso_utc(maha['start_jd']),
                    'years_until': round(years_until, 1),
                    'sign': maha['sign_name'],
                    'chakra': maha['chakra'],
                    'direction': maha['direction'],
                    'type': event_type,
                    'duration_years': maha['years']
                })
        
        return insights

    def _get_comprehensive_predictions(self, mahadashas: List[Dict[str, Any]], current_date: datetime, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive prediction interpretations"""
        
        try:
            current_jd = self._current_jd(current_date)
            current_maha = None
            
            # Find current mahadasha
            for maha in mahadashas:
                if maha['start_jd'] <= current_jd < maha['end_jd']:
                    current_maha = maha
                    break
            
            if not current_maha:
                return {}
            
            current_sign = current_maha['sign']
            current_sign_name = current_maha['sign_name']
            
            # 1. Current Focus of Life
            focus = self._get_life_focus(current_maha, chart_data)
            
            # 2. Thematic Keywords
            keywords = self._get_sign_keywords(current_sign)
            
            # 3. Predicted Events (0-2 years)
            events = self._get_predicted_events(current_maha, chart_data)
            
            # 4. Karmic Shifts from Jumps
            karmic_shifts = self._get_karmic_shifts(current_sign, chart_data)
            
            # 5. Strength Scores
            strength = self._get_sign_strength_score(current_sign, chart_data)
            next_strength = self._get_next_sign_strength(mahadashas, current_jd, chart_data)
            
            # 6. Duration + Energy Style
            energy_style = self._get_energy_style(current_maha)
            
            # 7. House Impact Summary
            house_impacts = self._get_house_impacts(current_sign, chart_data)
            
            return {
                'current_focus': focus,
                'theme_keywords': keywords,
                'predicted_events': events,
                'karmic_shifts': karmic_shifts,
                'current_strength': strength,
                'next_strength': next_strength,
                'energy_style': energy_style,
                'house_impacts': house_impacts
            }
        except Exception as e:
            print(f"Error in comprehensive predictions: {e}")
            return {}
    
    def _get_card_data(self, current_maha: Dict[str, Any], mahadashas: List[Dict[str, Any]], current_jd: float, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured data for multi-card layout"""
        
        strength_score = self._get_sign_strength_score(current_maha['sign'], chart_data)
        energy_style = self._get_energy_style(current_maha)
        house_impacts = self._get_house_impacts(current_maha['sign'], chart_data)
        next_sign = self._get_next_sign_strength(mahadashas, current_jd, chart_data)
        
        # Calculate progress
        total_duration = current_maha['end_jd'] - current_maha['start_jd']
        elapsed = current_jd - current_maha['start_jd']
        progress_percent = min(100, max(0, (elapsed / total_duration) * 100))
        
        return {
            'status_card': {
                'sign_name': current_maha['sign_name'],
                'progress_percent': round(progress_percent, 1),
                'time_remaining': self._format_time_remaining(current_maha['end_jd'] - current_jd),
                'chakra': current_maha['chakra'],
                'direction': current_maha['direction'],
                'strength_score': strength_score
            },
            'focus_card': {
                'theme': self._get_life_focus(current_maha, chart_data),
                'energy_style': energy_style['style'],
                'key_areas': f"{house_impacts['lagna_meaning']} ({house_impacts['lagna_house']}H), {house_impacts['moon_meaning']} ({house_impacts['moon_house']}H)",
                'keywords': self._get_sign_keywords(current_maha['sign'])[:3]
            },
            'timeline_card': {
                'current_period': {
                    'name': current_maha['sign_name'],
                    'start': current_maha.get('start_iso', ''),
                    'end': current_maha.get('end_iso', ''),
                    'progress': progress_percent
                },
                'next_events': self._get_timeline_events(mahadashas, current_jd),
                'reversals': current_maha.get('reversals', [])
            },
            'predictions_card': {
                'next_6_months': self._get_predicted_events(current_maha, chart_data)[:2],
                'next_2_years': self._get_sign_keywords(current_maha['sign'])[:2],
                'jump_effects': self._get_karmic_shifts(current_maha['sign'], chart_data)[:1]
            },
            'strength_card': {
                'current_strength': strength_score,
                'next_strength': next_sign['strength'],
                'comparison': self._get_strength_comparison(strength_score, next_sign['strength']),
                'next_sign_name': next_sign['sign'],
                'guidance': self._get_preparation_guidance(strength_score, next_sign['strength'])
            }
        }
    
    def _format_time_remaining(self, days_remaining: float) -> str:
        """Format remaining time in human readable format"""
        if days_remaining < 30:
            return f"{int(days_remaining)} days"
        elif days_remaining < 365:
            months = int(days_remaining / 30)
            return f"{months} months"
        else:
            years = int(days_remaining / 365)
            months = int((days_remaining % 365) / 30)
            if months > 0:
                return f"{years}y {months}m"
            return f"{years} years"
    
    def _get_timeline_events(self, mahadashas: List[Dict[str, Any]], current_jd: float) -> List[Dict[str, Any]]:
        """Get next 2-3 major events for timeline"""
        events = []
        count = 0
        
        for maha in mahadashas:
            if maha['start_jd'] > current_jd and count < 3:
                events.append({
                    'name': f"{maha['sign_name']} begins",
                    'date': maha.get('start_iso', ''),
                    'type': 'period_start'
                })
                count += 1
        
        return events
    
    def _get_strength_comparison(self, current: int, next_strength: int) -> str:
        """Compare current vs next period strength"""
        diff = next_strength - current
        if diff > 15:
            return "significant_increase"
        elif diff > 5:
            return "moderate_increase"
        elif diff < -15:
            return "significant_decrease"
        elif diff < -5:
            return "moderate_decrease"
        else:
            return "similar"
    
    def _get_preparation_guidance(self, current: int, next_strength: int) -> str:
        """Get guidance for upcoming period"""
        comparison = self._get_strength_comparison(current, next_strength)
        
        guidance_map = {
            'significant_increase': "Prepare for accelerated growth and new opportunities",
            'moderate_increase': "Build momentum for upcoming positive changes",
            'similar': "Maintain current strategies and steady progress",
            'moderate_decrease': "Consolidate gains and prepare for challenges",
            'significant_decrease': "Focus on stability and careful planning"
        }
        
        return guidance_map.get(comparison, "Stay adaptable and focused")
    
    def _get_life_focus(self, current_maha: Dict[str, Any], chart_data: Dict[str, Any]) -> str:
        """Determine current life focus based on chakra and sign"""
        
        chakra = current_maha['chakra']
        direction = current_maha['direction']
        sign = current_maha['sign']
        
        # Base focus from chakra
        if chakra == 1:
            base_focus = "Inner development, personal growth, self-discovery"
        else:
            base_focus = "Outer manifestation, public karma, worldly expansion"
        
        # Modify based on direction
        if direction == 'Backward':
            modifier = "introspective phase, past karma resolution"
        else:
            modifier = "progressive phase, future-oriented actions"
        
        # Add sign-specific focus
        sign_focus = {
            0: "identity formation, leadership development",  # Aries
            1: "material stability, resource building",      # Taurus
            2: "communication, learning, networking",       # Gemini
            3: "emotional security, home, nurturing",       # Cancer
            4: "creative expression, recognition, authority", # Leo
            5: "service, health, practical skills",         # Virgo
            6: "relationships, partnerships, balance",      # Libra
            7: "transformation, hidden knowledge, depth",   # Scorpio
            8: "higher learning, dharma, expansion",        # Sagittarius
            9: "career achievement, responsibility, status", # Capricorn
            10: "innovation, humanitarian goals, networks",  # Aquarius
            11: "spiritual surrender, completion, release"   # Pisces
        }.get(sign, "personal development")
        
        return f"{base_focus} with {modifier}. Focus on {sign_focus}."
    
    def _get_sign_keywords(self, sign: int) -> List[str]:
        """Get thematic keywords for current dasha sign"""
        
        keywords_map = {
            0: ["Leadership", "Initiative", "Courage", "Independence", "Action", "Competition", "Pioneering"],
            1: ["Stability", "Resources", "Comfort", "Persistence", "Beauty", "Material growth", "Patience"],
            2: ["Communication", "Learning", "Versatility", "Networking", "Curiosity", "Adaptability", "Information"],
            3: ["Nurturing", "Emotions", "Home", "Security", "Intuition", "Care", "Protection"],
            4: ["Creativity", "Recognition", "Authority", "Drama", "Confidence", "Performance", "Leadership"],
            5: ["Service", "Health", "Analysis", "Perfection", "Practical skills", "Organization", "Healing"],
            6: ["Relationships", "Balance", "Harmony", "Justice", "Partnerships", "Diplomacy", "Beauty"],
            7: ["Transformation", "Depth", "Mystery", "Power", "Regeneration", "Research", "Intensity"],
            8: ["Dharma", "Higher learning", "Travel", "Teachers", "Fortune", "Risk-taking", "Expansion"],
            9: ["Achievement", "Responsibility", "Status", "Discipline", "Authority", "Structure", "Ambition"],
            10: ["Innovation", "Humanitarian goals", "Networks", "Technology", "Freedom", "Uniqueness", "Reform"],
            11: ["Spirituality", "Surrender", "Compassion", "Imagination", "Sacrifice", "Completion", "Transcendence"]
        }
        
        return keywords_map.get(sign, ["Growth", "Development", "Learning"])
    
    def _get_predicted_events(self, current_maha: Dict[str, Any], chart_data: Dict[str, Any]) -> List[str]:
        """Predict likely events based on sign nature and chart factors"""
        
        sign = current_maha['sign']
        chakra = current_maha['chakra']
        
        events_map = {
            0: ["Leadership opportunities", "New initiatives", "Competitive situations", "Independence themes"],
            1: ["Financial growth", "Property matters", "Comfort improvements", "Resource accumulation"],
            2: ["Communication projects", "Learning opportunities", "Travel", "Networking expansion"],
            3: ["Home changes", "Family focus", "Emotional healing", "Nurturing roles"],
            4: ["Creative projects", "Recognition", "Authority positions", "Performance opportunities"],
            5: ["Health improvements", "Service roles", "Skill development", "Organizational changes"],
            6: ["Relationship developments", "Partnership opportunities", "Legal matters", "Balance seeking"],
            7: ["Major transformations", "Hidden knowledge", "Power shifts", "Deep research"],
            8: ["Higher education", "Long-distance travel", "Mentor relationships", "Dharmic opportunities"],
            9: ["Career advancement", "Increased responsibilities", "Status changes", "Structural reforms"],
            10: ["Innovative projects", "Group activities", "Technology adoption", "Social reforms"],
            11: ["Spiritual experiences", "Charitable activities", "Completion of cycles", "Surrender themes"]
        }
        
        base_events = events_map.get(sign, ["Personal growth", "New experiences"])
        
        # Modify based on chakra
        if chakra == 1:
            return [f"Internal {event.lower()}" for event in base_events[:3]]
        else:
            return [f"External {event.lower()}" for event in base_events[:3]]
    
    def _get_karmic_shifts(self, current_sign: int, chart_data: Dict[str, Any]) -> List[str]:
        """Analyze karmic shifts from jumped signs"""
        
        # This would need the jumped signs info - simplified for now
        shifts = [
            "Accelerated karma in current sign themes",
            "Bypassed lessons create quantum leap effects",
            "Focus intensifies on active sign areas"
        ]
        
        return shifts
    
    def _get_sign_strength_score(self, sign: int, chart_data: Dict[str, Any]) -> int:
        """Calculate sign strength score 0-100"""
        
        score = 50  # Base score
        
        # Check sign lord strength
        sign_lord = self.SIGN_LORDS[sign]
        if sign_lord in chart_data['planets']:
            lord_data = chart_data['planets'][sign_lord]
            
            # Dignity bonus
            dignity = self.get_planet_dignity(sign_lord, lord_data['sign'])
            if dignity == 'Exalted':
                score += 25
            elif dignity == 'Own Sign':
                score += 15
            elif dignity == 'Debilitated':
                score -= 25
            
            # House position bonus
            house = lord_data.get('house', 1)
            if house in [1, 4, 7, 10]:  # Kendra
                score += 10
            elif house in [5, 9]:  # Trikona
                score += 15
            elif house in [6, 8, 12]:  # Dusthana
                score -= 15
        
        # Check planets in sign
        planets_in_sign = 0
        for planet, planet_data in chart_data['planets'].items():
            if planet_data['sign'] == sign:
                planets_in_sign += 1
                if planet in ['Jupiter', 'Venus']:  # Benefics
                    score += 5
                elif planet in ['Mars', 'Saturn']:  # Malefics
                    score -= 3
        
        return max(0, min(100, score))
    
    def _get_next_sign_strength(self, mahadashas: List[Dict[str, Any]], current_jd: float, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get next sign strength info"""
        
        next_maha = None
        for maha in mahadashas:
            if maha['start_jd'] > current_jd:
                next_maha = maha
                break
        
        if not next_maha:
            return {'sign': 'Unknown', 'strength': 50}
        
        strength = self._get_sign_strength_score(next_maha['sign'], chart_data)
        
        return {
            'sign': next_maha['sign_name'],
            'strength': strength
        }
    
    def _get_energy_style(self, current_maha: Dict[str, Any]) -> Dict[str, Any]:
        """Get energy style and duration info"""
        
        sign = current_maha['sign']
        years = current_maha['years']
        
        # Energy styles by sign
        styles = {
            0: "Dynamic, fast-moving, action-oriented",
            1: "Steady, persistent, comfort-seeking",
            2: "Versatile, communicative, adaptable",
            3: "Nurturing, emotional, protective",
            4: "Creative, dramatic, confidence-building",
            5: "Analytical, service-oriented, perfectionist",
            6: "Harmonious, relationship-focused, balanced",
            7: "Intense, transformative, depth-seeking",
            8: "Expansive, philosophical, adventure-seeking",
            9: "Disciplined, ambitious, structure-building",
            10: "Innovative, humanitarian, freedom-loving",
            11: "Intuitive, compassionate, surrender-oriented"
        }
        
        return {
            'style': styles.get(sign, "Developmental"),
            'duration_years': years
        }
    
    def _get_house_impacts(self, current_sign: int, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get house impact summary"""
        
        # Get Lagna sign - handle both dict and direct value
        ascendant_data = chart_data.get('ascendant', {})
        if isinstance(ascendant_data, dict):
            lagna_sign = ascendant_data.get('sign', 0)
        else:
            # If ascendant is a direct value (float/int)
            lagna_sign = int(ascendant_data) if ascendant_data else 0
        
        # Calculate house from Lagna
        house_from_lagna = ((current_sign - lagna_sign) % 12) + 1
        
        # Get Moon sign
        moon_sign = chart_data['planets']['Moon']['sign']
        house_from_moon = ((current_sign - moon_sign) % 12) + 1
        
        # House meanings
        house_meanings = {
            1: "Self, identity, appearance",
            2: "Wealth, family, speech",
            3: "Courage, siblings, efforts",
            4: "Home, mother, peace",
            5: "Children, creativity, intelligence",
            6: "Health, service, enemies",
            7: "Partnerships, marriage, business",
            8: "Transformation, occult, longevity",
            9: "Dharma, fortune, higher learning",
            10: "Career, reputation, authority",
            11: "Gains, friends, aspirations",
            12: "Loss, spirituality, foreign lands"
        }
        
        return {
            'lagna_house': house_from_lagna,
            'lagna_meaning': house_meanings.get(house_from_lagna, "Development"),
            'moon_house': house_from_moon,
            'moon_meaning': house_meanings.get(house_from_moon, "Growth")
        }

    # Utility methods
    def _parse_birth_jd(self, birth_data: Dict) -> float:
        """Convert birth data to Julian Day UT"""
        tz = float(birth_data.get('timezone_offset', 0.0))
        Y, M, D = [int(x) for x in birth_data['date'].split('-')]
        hh, mm = [int(x) for x in birth_data['time'].split(':')]
        ut_hour = hh - tz
        return swe.julday(Y, M, D, ut_hour + mm/60.0)

    def _current_jd(self, current_date: datetime) -> float:
        """Convert current date to Julian Day"""
        return swe.julday(current_date.year, current_date.month, current_date.day,
                         current_date.hour + current_date.minute/60.0 + current_date.second/3600.0)

    def _jd_to_iso_utc(self, jd: float) -> str:
        """Convert JD UT to ISO8601 UTC string"""
        try:
            y, m, d, hour = swe.revjul(jd)
            h = int(hour)
            rem = (hour - h) * 60.0
            minute = int(rem)
            second = int((rem - minute) * 60.0)
            dt = datetime(int(y), int(m), int(d), h, minute, second, tzinfo=timezone.utc)
            return dt.isoformat().replace('+00:00', 'Z')
        except Exception:
            dt = datetime(2000,1,1, tzinfo=timezone.utc) + timedelta(days=jd - 2451545.0)
            return dt.isoformat().replace('+00:00', 'Z')