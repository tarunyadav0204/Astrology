"""
Core Classical Analysis Modules
Implements the user's sophisticated 7-step prediction technique with comprehensive debugging
"""

from datetime import datetime
import swisseph as swe
from typing import Dict, List, Any, Tuple
import json

class CoreClassicalAnalyzer:
    def __init__(self, birth_data: Dict, current_date: datetime = None):
        self.birth_data = birth_data
        self.current_date = current_date or datetime.now()
        self.debug_info = {}
        
    def analyze_dasha_foundation(self) -> Dict[str, Any]:
        """Step 1: Check all 5 dashas to identify planets in action"""
        debug = {
            "step": "1. Identify Active Dasha Planets",
            "description": "Analyzing all 5 dasha levels: Maha, Antar, Pratyantar, Sookshma, Prana",
            "calculations": []
        }
        
        # Get all 5 dasha levels
        dasha_data = self._get_current_dashas()
        active_planets = []
        
        for level in ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma', 'prana']:
            planet = dasha_data.get(level, {}).get('planet')
            if planet and planet not in active_planets:
                active_planets.append(planet)
                debug["calculations"].append(f"{level.title()}: {planet}")
        
        result = {
            "active_dasha_planets": active_planets,
            "dasha_details": dasha_data
        }
        
        self.debug_info["dasha_foundation"] = debug
        return result
    
    def analyze_transit_activations(self, active_dasha_planets: List[str]) -> Dict[str, Any]:
        """Step 2: Find dasha planets activated by transits + natal planets aspecting each other also making transit relations"""
        debug = {
            "step": "2. Transit-Dasha Planet Activation",
            "description": "Finding dasha planets activated by transits + natal aspect relationships also active in transit",
            "calculations": []
        }
        
        natal_positions = self._get_natal_planet_positions()
        transit_positions = self._get_current_transits()
        activated_planets = []
        
        # Part 1: Check dasha planets activated by transits
        for dasha_planet in active_dasha_planets:
            if dasha_planet not in natal_positions:
                continue
                
            natal_pos = natal_positions[dasha_planet]
            activations = []
            
            # Check if any transiting planet aspects or conjuncts this dasha planet
            # BUT only if there was already a natal relationship between them
            natal_aspects = self._get_natal_aspects()
            
            for transit_planet, transit_pos in transit_positions.items():
                if transit_planet == dasha_planet:
                    continue  # Skip self-transit (handled separately)
                    
                # Check if there was a natal relationship between these planets
                has_natal_relationship = False
                for aspect in natal_aspects:
                    if (aspect['planet1'] == transit_planet and aspect['planet2'] == dasha_planet) or \
                       (aspect['planet1'] == dasha_planet and aspect['planet2'] == transit_planet):
                        has_natal_relationship = True
                        break
                
                # Only check transit aspect if there was a natal relationship
                if has_natal_relationship:
                    aspect_type = self._check_classical_aspect(transit_pos['longitude'], natal_pos['longitude'], transit_planet)
                    
                    if aspect_type:
                        activations.append({
                            'transit_planet': transit_planet,
                            'aspect_type': aspect_type,
                            'natal_planet': dasha_planet,
                            'activation_reason': f'{transit_planet}_{aspect_type}_natal_{dasha_planet}_repeat_natal_relation'
                        })
                        debug["calculations"].append(f"{transit_planet} {aspect_type} natal {dasha_planet} (repeating natal relationship)")
            
            # Check if dasha planet is transiting over its own natal position
            if dasha_planet in transit_positions:
                transit_pos = transit_positions[dasha_planet]
                diff = abs(transit_pos['longitude'] - natal_pos['longitude'])
                if diff > 180:
                    diff = 360 - diff
                    
                if diff <= 3:  # 3° orb for conjunction
                    activations.append({
                        'transit_planet': dasha_planet,
                        'aspect_type': 'conjunction',
                        'natal_planet': dasha_planet,
                        'activation_reason': f'{dasha_planet}_return'
                    })
                    debug["calculations"].append(f"{dasha_planet} returning to natal position")
            
            # Only add if there are actual activations
            if activations:
                activated_planets.append({
                    'planet': dasha_planet,
                    'activations': activations
                })
        
        # Part 2: Check natal planets aspecting each other + also making transit relations
        # This is already handled in Part 1 above, so we can remove this duplicate logic
        
        # Debug: Show which planets were NOT activated
        not_activated = [p for p in active_dasha_planets if not any(ap['planet'] == p for ap in activated_planets)]
        if not_activated:
            debug["calculations"].append(f"Dasha planets NOT activated by transits: {', '.join(not_activated)}")
        
        result = {"activated_dasha_planets": activated_planets}
        self.debug_info["transit_activations"] = debug
        return result
    
    def analyze_house_activations(self, activated_planets: List[Dict]) -> Dict[str, Any]:
        """Step 3: Identify houses activated by the transit-activated dasha planets"""
        debug = {
            "step": "3. House Activation Analysis",
            "description": "Finding houses activated by transit-activated dasha planets",
            "calculations": []
        }
        
        activated_houses = set()
        house_details = []
        natal_positions = self._get_natal_planet_positions()
        
        for planet_data in activated_planets:
            planet = planet_data['planet']
            if planet not in natal_positions:
                continue
                
            # 1. Planet placement house
            placement_house = natal_positions[planet]['house']
            activated_houses.add(placement_house)
            house_details.append({
                'house': placement_house,
                'activation_type': 'placement',
                'planet': planet,
                'description': f"{planet} placed in house {placement_house}"
            })
            debug["calculations"].append(f"{planet} placement activates House {placement_house}")
            
            # 2. Planet lordship houses
            lordship_houses = self._get_planet_lordships(planet)
            for lord_house in lordship_houses:
                activated_houses.add(lord_house)
                house_details.append({
                    'house': lord_house,
                    'activation_type': 'lordship',
                    'planet': planet,
                    'description': f"{planet} rules house {lord_house}"
                })
                debug["calculations"].append(f"{planet} lordship activates House {lord_house}")
            
            # 3. Houses aspected by planet
            aspected_houses = self._get_classical_aspects_to_houses(planet, placement_house)
            for asp_house in aspected_houses:
                activated_houses.add(asp_house)
                house_details.append({
                    'house': asp_house,
                    'activation_type': 'aspect',
                    'planet': planet,
                    'description': f"{planet} aspects house {asp_house}"
                })
                debug["calculations"].append(f"{planet} aspects activate House {asp_house}")
        
        result = {
            "activated_houses": sorted(list(activated_houses)),
            "house_details": house_details,
            "total_houses_activated": len(activated_houses)
        }
        
        self.debug_info["house_activations"] = debug
        return result
    

    
    def generate_complete_prediction(self) -> Dict[str, Any]:
        """Execute complete 7-step classical prediction technique"""
        # Step 1: Get active dasha planets
        dasha_analysis = self.analyze_dasha_foundation()
        active_planets = dasha_analysis["active_dasha_planets"]
        
        # Step 2: Find transit-activated dasha planets
        transit_analysis = self.analyze_transit_activations(active_planets)
        activated_planets = transit_analysis["activated_dasha_planets"]
        
        # Step 3: Get activated houses
        house_analysis = self.analyze_house_activations(activated_planets)
        activated_houses = house_analysis["activated_houses"]
        
        # Step 4: Analyze planet results (good/bad)
        planet_results = self.analyze_planet_results(activated_planets)
        
        # Step 5: Generate prediction from house significations
        prediction = self.generate_house_based_prediction(activated_houses, planet_results)
        
        return {
            "step1_dasha_planets": active_planets,
            "step1_dasha_details": dasha_analysis["dasha_details"],
            "step2_activated_planets": [p['planet'] for p in activated_planets],
            "step2_activation_reasons": {p['planet']: [a['activation_reason'] for a in p['activations']] for p in activated_planets},
            "step3_activated_houses": activated_houses,
            "step3_house_details": {str(h['house']): {'score': 1, 'factors': [f"{h['planet']} {h['activation_type']}"]} for h in house_analysis["house_details"]},
            "step4_planet_results": planet_results,
            "step5_prediction": prediction,
            "step5_house_predictions": prediction.get("house_predictions", {}),
            "debug_info": self.debug_info
        }
    
    def analyze_planet_results(self, activated_planets: List[Dict]) -> Dict[str, Any]:
        """Step 4-5: Comprehensive planet result analysis with all classical factors"""
        debug = {
            "step": "4-5. Planet Result Analysis",
            "description": "Analyzing if activated planets give positive or negative results with all factors",
            "calculations": []
        }
        
        planet_results = {}
        natal_positions = self._get_natal_planet_positions()
        
        # Get special points for negative lordship checks
        tithi_shunya_sign = self._get_tithi_shunya_rashi()
        avayogi_sign = self._get_avayogi_sign()
        maraka_houses = self._get_maraka_houses()
        
        for planet_data in activated_planets:
            planet = planet_data['planet']
            if planet not in natal_positions:
                continue
                
            result_score = 0
            factors = []
            planet_pos = natal_positions[planet]
            
            # 1. Natural benefic/malefic
            if planet in ['Jupiter', 'Venus', 'Moon']:
                result_score += 2
                factors.append("Natural benefic (+2)")
            elif planet in ['Saturn', 'Mars', 'Sun', 'Rahu', 'Ketu']:
                result_score -= 2
                factors.append("Natural malefic (-2)")
            
            # 2. Lordship analysis (comprehensive)
            lordships = self._get_planet_lordships(planet)
            for house in lordships:
                # Negative houses
                if house in [6, 8, 12]:
                    result_score -= 2
                    factors.append(f"Lord of {house}th house (-2)")
                # Positive houses
                elif house in [1, 4, 5, 7, 9, 10]:
                    result_score += 1
                    factors.append(f"Lord of {house}th house (+1)")
                
                # Special negative lordships
                if house == tithi_shunya_sign:
                    result_score -= 1
                    factors.append(f"Lord of Tithi Shunya Rashi (-1)")
                
                if house == avayogi_sign:
                    result_score -= 1
                    factors.append(f"Lord of Avayogi sign (-1)")
                
                if house in maraka_houses:
                    result_score -= 1
                    factors.append(f"Maraka lord for house {house} (-1)")
            
            # 3. Exaltation/Debilitation
            dignity = self._calculate_dignity(planet, planet_pos['sign'])
            if dignity == "exalted":
                result_score += 3
                factors.append("Exalted (+3)")
            elif dignity == "debilitated":
                result_score -= 3
                factors.append("Debilitated (-3)")
            elif dignity == "own_sign":
                result_score += 2
                factors.append("Own sign (+2)")
            
            # 4. Tenancy - 5-fold friendship
            house_lord = self._get_house_lord(planet_pos['house'])
            if house_lord:
                friendship = self._get_5_fold_friendship(planet, house_lord)
                if friendship == "friend":
                    result_score += 1
                    factors.append(f"In friend's house (+1)")
                elif friendship == "enemy":
                    result_score -= 1
                    factors.append(f"In enemy's house (-1)")
            
            # 5. Nakshatra friendship
            nakshatra_lord = self._get_nakshatra_lord(planet_pos['longitude'])
            if nakshatra_lord:
                nak_friendship = self._get_5_fold_friendship(planet, nakshatra_lord)
                if nak_friendship == "friend":
                    result_score += 1
                    factors.append(f"In friend's nakshatra (+1)")
                elif nak_friendship == "enemy":
                    result_score -= 1
                    factors.append(f"In enemy's nakshatra (-1)")
            
            # Final result
            if result_score > 0:
                final_result = "positive"
            elif result_score < 0:
                final_result = "negative"
            else:
                final_result = "neutral"
            
            planet_results[planet] = {
                "result": final_result,
                "score": result_score,
                "factors": factors
            }
            
            debug["calculations"].append(f"{planet}: {final_result} (score: {result_score}) - {', '.join(factors)}")
        
        self.debug_info["planet_results"] = debug
        return planet_results
    
    def generate_house_based_prediction(self, activated_houses: List[int], planet_results: Dict) -> Dict[str, Any]:
        """Step 6-7: Generate specific predictions using house combinations"""
        debug = {
            "step": "6-7. House Combination Predictions",
            "description": "Generating specific predictions from house combinations",
            "calculations": []
        }
        
        # Get house combinations from database
        from house_combinations import get_active_house_combinations
        combinations = get_active_house_combinations()
        
        # Find and score matching combinations
        scored_combinations = []
        
        for combo in combinations:
            combo_houses = combo['houses']
            if all(house in activated_houses for house in combo_houses):
                # Score this combination based on multiple factors
                score = self._score_combination(combo_houses, activated_houses, planet_results)
                
                # Determine if this combination should be positive or negative
                affecting_planets = self._get_planets_affecting_houses(combo_houses, planet_results)
                
                positive_count = sum(1 for p in affecting_planets if p['result'] == 'positive')
                negative_count = sum(1 for p in affecting_planets if p['result'] == 'negative')
                
                if positive_count > negative_count:
                    prediction_text = combo['positive_prediction']
                    tendency = "positive"
                elif negative_count > positive_count:
                    prediction_text = combo['negative_prediction']
                    tendency = "negative"
                else:
                    # Mixed - include both
                    prediction_text = f"Mixed results: {combo['positive_prediction']} However, {combo['negative_prediction'].lower()}"
                    tendency = "mixed"
                
                scored_combinations.append({
                    "combination_name": combo['combination_name'],
                    "houses": combo_houses,
                    "prediction": prediction_text,
                    "tendency": tendency,
                    "affecting_planets": [p['planet'] for p in affecting_planets],
                    "score": score,
                    "planet_scores": {p['planet']: p['score'] for p in affecting_planets}
                })
        
        # Sort by score (highest first) and select top combinations
        scored_combinations.sort(key=lambda x: x['score'], reverse=True)
        specific_predictions = scored_combinations[:5]  # Top 5 most relevant
        
        # Log selected combinations
        used_houses = set()
        for pred in specific_predictions:
            used_houses.update(pred['houses'])
            debug["calculations"].append(f"Score {pred['score']:.1f}: {pred['combination_name']} (Houses {pred['houses']}) - {pred['tendency']}")
        
        # Generate individual house predictions for unused houses
        house_predictions = {}
        for house in activated_houses:
            if house not in used_houses:
                themes = self._get_house_themes(house)
                affecting_planets = self._get_planets_affecting_houses([house], planet_results)
                
                positive_count = sum(1 for p in affecting_planets if p['result'] == 'positive')
                negative_count = sum(1 for p in affecting_planets if p['result'] == 'negative')
                
                if positive_count > negative_count:
                    tendency = "positive"
                    prediction = f"Favorable results in {', '.join(themes)}."
                elif negative_count > positive_count:
                    tendency = "negative"
                    prediction = f"Challenges in {', '.join(themes)}."
                else:
                    tendency = "mixed"
                    prediction = f"Mixed results in {', '.join(themes)}."
                
                house_predictions[house] = {
                    "prediction": prediction,
                    "tendency": tendency,
                    "themes": themes,
                    "factors": [f"{p['planet']} ({p['result']})" for p in affecting_planets]
                }
        
        # Generate overall prediction text
        if specific_predictions:
            main_predictions = [pred['prediction'] for pred in specific_predictions[:3]]  # Top 3
            prediction_text = " ".join(main_predictions)
        else:
            prediction_text = "Current period shows general activation in multiple life areas."
        
        # Determine overall tendency
        positive_count = sum(1 for pred in specific_predictions if pred['tendency'] == 'positive')
        negative_count = sum(1 for pred in specific_predictions if pred['tendency'] == 'negative')
        
        if positive_count > negative_count:
            overall_tendency = "favorable"
        elif negative_count > positive_count:
            overall_tendency = "challenging"
        else:
            overall_tendency = "mixed"
        
        # Get dominant themes from combinations
        all_themes = []
        for pred in specific_predictions:
            for house in pred['houses']:
                all_themes.extend(self._get_house_themes(house))
        
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        dominant_themes = [theme for theme, _ in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
        
        result = {
            "prediction_text": prediction_text,
            "overall_tendency": overall_tendency,
            "dominant_themes": dominant_themes,
            "specific_predictions": specific_predictions,
            "house_predictions": house_predictions,
            "activated_houses": activated_houses,
            "selection_method": "intelligent_scoring"
        }
        
        debug["calculations"].append(f"Final prediction: {prediction_text}")
        debug["calculations"].append(f"Selected {len(specific_predictions)} combinations from {len(scored_combinations)} matches")
        self.debug_info["house_prediction"] = debug
        return result
    
    def _score_combination(self, combo_houses: List[int], activated_houses: List[int], planet_results: Dict) -> float:
        """Score combination based on relevance and planet strength"""
        score = 0.0
        
        # 1. Base score for number of houses in combination
        score += len(combo_houses) * 2.0
        
        # 2. Bonus for houses that appear in multiple activations
        house_activation_count = {}
        natal_positions = self._get_natal_planet_positions()
        
        for planet, result in planet_results.items():
            if planet in natal_positions:
                planet_house = natal_positions[planet]['house']
                lordships = self._get_planet_lordships(planet)
                aspects = self._get_classical_aspects_to_houses(planet, planet_house)
                
                # Count how many times each house is activated
                for house in combo_houses:
                    if house == planet_house:
                        house_activation_count[house] = house_activation_count.get(house, 0) + 1
                    if house in lordships:
                        house_activation_count[house] = house_activation_count.get(house, 0) + 1
                    if house in aspects:
                        house_activation_count[house] = house_activation_count.get(house, 0) + 1
        
        # Bonus for multiply-activated houses
        for house, count in house_activation_count.items():
            if count > 1:
                score += count * 1.5
        
        # 3. Planet strength bonus
        affecting_planets = self._get_planets_affecting_houses(combo_houses, planet_results)
        for planet_data in affecting_planets:
            planet_score = abs(planet_data['score'])
            if planet_data['result'] == 'positive':
                score += planet_score * 1.0  # Positive planets boost score
            else:
                score += planet_score * 0.5  # Negative planets still add some relevance
        
        # 4. Bonus for important house combinations
        important_combos = {
            frozenset([1, 10]): 3.0,  # Personality + Career
            frozenset([2, 11]): 3.0,  # Wealth + Gains
            frozenset([5, 9]): 2.5,   # Creativity + Luck
            frozenset([1, 5]): 2.5,   # Self + Creativity
            frozenset([9, 10]): 2.5,  # Luck + Career
            frozenset([2, 8]): 2.0,   # Wealth + Transformation
        }
        
        combo_set = frozenset(combo_houses)
        for important_combo, bonus in important_combos.items():
            if important_combo.issubset(combo_set):
                score += bonus
        
        return score
    
    def _get_planets_affecting_houses(self, houses: List[int], planet_results: Dict) -> List[Dict]:
        """Get planets affecting given houses with their results"""
        affecting_planets = []
        natal_positions = self._get_natal_planet_positions()
        
        for planet, result in planet_results.items():
            if planet in natal_positions:
                planet_house = natal_positions[planet]['house']
                lordships = self._get_planet_lordships(planet)
                aspects = self._get_classical_aspects_to_houses(planet, planet_house)
                
                # Check if planet affects any of the given houses
                if any(planet_house == house or house in lordships or house in aspects for house in houses):
                    affecting_planets.append({
                        'planet': planet,
                        'result': result['result'],
                        'score': result['score']
                    })
        
        return affecting_planets
    
    # Helper methods
    def _get_current_dashas(self) -> Dict:
        """Get current dasha periods using shared calculator"""
        try:
            from shared.dasha_calculator import DashaCalculator
            
            calculator = DashaCalculator()
            dasha_data = calculator.calculate_current_dashas(self.birth_data, self.current_date)
            
            return {
                "mahadasha": dasha_data.get('mahadasha', {}),
                "antardasha": dasha_data.get('antardasha', {}),
                "pratyantardasha": dasha_data.get('pratyantardasha', {}),
                "sookshma": dasha_data.get('sookshma', {}),
                "prana": dasha_data.get('prana', {})
            }
            
        except Exception as e:
            print(f"Error getting current dashas: {e}")
            return {"mahadasha": {}, "antardasha": {}, "pratyantardasha": {}, "sookshma": {}, "prana": {}}
    
    def _get_current_transits(self) -> Dict:
        """Get current transit positions using direct calculation"""
        from event_prediction.config import SIGN_NAMES
        import swisseph as swe
        
        try:
            # Calculate directly without API call
            jd = swe.julday(
                self.current_date.year,
                self.current_date.month,
                self.current_date.day,
                12.0
            )
            
            # Calculate birth ascendant once using same method as main chart
            time_parts = self.birth_data['time'].split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60
            
            if 6.0 <= self.birth_data['latitude'] <= 37.0 and 68.0 <= self.birth_data['longitude'] <= 97.0:
                tz_offset = 5.5
            else:
                tz_offset = 0
            
            utc_hour = hour - tz_offset
            birth_jd = swe.julday(
                int(self.birth_data['date'].split('-')[0]),
                int(self.birth_data['date'].split('-')[1]),
                int(self.birth_data['date'].split('-')[2]),
                utc_hour
            )
            birth_houses_data = swe.houses(birth_jd, self.birth_data['latitude'], self.birth_data['longitude'], b'P')
            birth_ayanamsa = swe.get_ayanamsa_ut(birth_jd)
            birth_ascendant_tropical = birth_houses_data[1][0]
            birth_ascendant_sidereal = (birth_ascendant_tropical - birth_ayanamsa) % 360
            ascendant_sign = int(birth_ascendant_sidereal / 30)
            
            result = {}
            planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
            
            for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6]):
                pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
                longitude = pos[0]
                sign_num = int(longitude / 30)
                house_num = ((sign_num - ascendant_sign) % 12) + 1
                
                result[planet_names[i]] = {
                    "house": house_num,
                    "sign": sign_num,
                    "degree": longitude % 30,
                    "longitude": longitude
                }
            
            return result
            
        except Exception as e:
            print(f"Error getting current transits: {e}")
            return {}
    

    

    
    def _get_house_themes(self, house: int) -> List[str]:
        """Get themes for house"""
        themes = {
            1: ["personality", "health", "appearance"],
            2: ["wealth", "family", "speech"],
            3: ["communication", "siblings", "short travels"],
            4: ["home", "mother", "property"],
            5: ["creativity", "children", "education"],
            6: ["health", "service", "enemies"],
            7: ["marriage", "partnerships", "business"],
            8: ["transformation", "occult", "longevity"],
            9: ["luck", "spirituality", "higher learning"],
            10: ["career", "reputation", "authority"],
            11: ["gains", "friends", "aspirations"],
            12: ["losses", "spirituality", "foreign lands"]
        }
        return themes.get(house, ["unknown"])
    

    
    def _get_natal_planet_positions(self) -> Dict:
        """Get natal planet positions using direct calculation"""
        import swisseph as swe
        
        try:
            # Calculate natal positions
            time_parts = self.birth_data['time'].split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60
            
            if 6.0 <= self.birth_data['latitude'] <= 37.0 and 68.0 <= self.birth_data['longitude'] <= 97.0:
                tz_offset = 5.5
            else:
                tz_offset = 0
            
            utc_hour = hour - tz_offset
            jd = swe.julday(
                int(self.birth_data['date'].split('-')[0]),
                int(self.birth_data['date'].split('-')[1]),
                int(self.birth_data['date'].split('-')[2]),
                utc_hour
            )
            
            # Calculate ascendant using same method as main chart
            houses_data = swe.houses(jd, self.birth_data['latitude'], self.birth_data['longitude'], b'P')
            ayanamsa = swe.get_ayanamsa_ut(jd)
            
            # Get sidereal ascendant (houses_data[1][0] is the ascendant)
            ascendant_tropical = houses_data[1][0]  # Tropical ascendant
            ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
            ascendant_sign = int(ascendant_sidereal / 30)
            
            # Check ayanamsa
            ayanamsa = swe.get_ayanamsa_ut(jd)
            print(f"DEBUG: Using ayanamsa: {ayanamsa:.2f}° (Lahiri)")
            print(f"DEBUG: Tropical ascendant: {ascendant_tropical:.2f}°")
            print(f"DEBUG: Sidereal ascendant: {ascendant_sidereal:.2f}°, sign: {ascendant_sign} ({['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'][ascendant_sign]})")
            print(f"DEBUG: Birth data - lat: {self.birth_data['latitude']}, lon: {self.birth_data['longitude']}, date: {self.birth_data['date']}, time: {self.birth_data['time']}")
            
            # Try with slightly earlier time to see if ascendant changes to Cancer
            test_jd = swe.julday(
                int(self.birth_data['date'].split('-')[0]),
                int(self.birth_data['date'].split('-')[1]),
                int(self.birth_data['date'].split('-')[2]),
                utc_hour - 0.5  # 30 minutes earlier
            )
            test_houses_data = swe.houses(test_jd, self.birth_data['latitude'], self.birth_data['longitude'], b'P')
            test_asc_tropical = test_houses_data[1][0]
            test_asc_sidereal = (test_asc_tropical - ayanamsa) % 360
            test_asc_sign = int(test_asc_sidereal / 30)
            print(f"DEBUG: With 30min earlier time - sidereal ascendant: {test_asc_sidereal:.2f}, sign: {test_asc_sign} ({['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'][test_asc_sign]})")
            
            result = {}
            planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
            
            for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
                if planet <= 6:
                    pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
                else:
                    pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0]
                    if planet == 12:  # Ketu
                        pos = list(pos)
                        pos[0] = (pos[0] + 180) % 360
                
                longitude = pos[0]
                sign_num = int(longitude / 30)
                house_num = ((sign_num - ascendant_sign) % 12) + 1
                
                if planet_names[i] in ['Saturn', 'Rahu']:
                    print(f"DEBUG: {planet_names[i]} - longitude: {longitude:.2f}, sign: {sign_num} ({['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'][sign_num]}), house: {house_num}")
                
                result[planet_names[i]] = {
                    "longitude": longitude,
                    "house": house_num,
                    "sign": sign_num
                }
            
            return result
            
        except Exception as e:
            print(f"Error getting natal positions: {e}")
            return {}
    
    def _check_classical_aspect(self, transit_house: int, natal_house: int, transit_planet: str) -> str:
        """Check classical Vedic aspects using house-based system"""
        if transit_house == natal_house:
            return "conjunction"
        
        # Calculate house difference
        house_diff = (natal_house - transit_house) % 12
        if house_diff == 0:
            house_diff = 12
        
        # Planet-specific house aspects
        if transit_planet == 'Mars':
            # Mars aspects 4th, 7th, 8th houses from its position
            if house_diff in [4, 7, 8]:
                return f"{house_diff}th_aspect"
        elif transit_planet == 'Jupiter':
            # Jupiter aspects 5th, 7th, 9th houses from its position
            if house_diff in [5, 7, 9]:
                return f"{house_diff}th_aspect"
        elif transit_planet == 'Saturn':
            # Saturn aspects 3rd, 7th, 10th houses from its position
            if house_diff in [3, 7, 10]:
                return f"{house_diff}th_aspect"
        elif transit_planet in ['Rahu', 'Ketu']:
            # Rahu/Ketu aspect 5th, 9th houses from their position
            if house_diff in [5, 9]:
                return f"{house_diff}th_aspect"
        else:
            # Sun, Moon, Mercury, Venus only have 7th aspect
            if house_diff == 7:
                return "7th_aspect"
        
        return None
    
    def _get_planet_lordships(self, planet: str) -> List[int]:
        """Get houses ruled by planet based on actual chart ascendant"""
        try:
            natal_positions = self._get_natal_planet_positions()
            # Get ascendant sign from any planet's house calculation
            asc_sign = None
            for p, pos in natal_positions.items():
                if 'sign' in pos and 'house' in pos:
                    # Reverse calculate ascendant sign
                    asc_sign = (pos['sign'] - pos['house'] + 1) % 12
                    break
            
            if asc_sign is None:
                return []
            
            # Planet sign lordships (fixed)
            sign_lordships = {
                "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
                "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]
            }
            
            planet_signs = sign_lordships.get(planet, [])
            house_lordships = []
            
            # Convert signs to houses based on ascendant
            for sign in planet_signs:
                house = ((sign - asc_sign) % 12) + 1
                house_lordships.append(house)
            
            return house_lordships
            
        except Exception as e:
            print(f"Error calculating lordships for {planet}: {e}")
            return []
    
    def _get_classical_aspects_to_houses(self, planet: str, from_house: int) -> List[int]:
        """Get houses aspected by planet from its placement house"""
        if planet in ['Rahu', 'Ketu']:
            # Rahu/Ketu only aspect 3rd and 11th houses from their position
            return [((from_house + 2 - 1) % 12) + 1, ((from_house + 10 - 1) % 12) + 1]
        elif planet == 'Mars':
            # Mars aspects 4th, 7th, 8th houses from its position
            return [((from_house + 3 - 1) % 12) + 1, ((from_house + 6 - 1) % 12) + 1, ((from_house + 7 - 1) % 12) + 1]
        elif planet == 'Jupiter':
            # Jupiter aspects 5th, 7th, 9th houses from its position
            return [((from_house + 4 - 1) % 12) + 1, ((from_house + 6 - 1) % 12) + 1, ((from_house + 8 - 1) % 12) + 1]
        elif planet == 'Saturn':
            # Saturn aspects 3rd, 7th, 10th houses from its position
            return [((from_house + 2 - 1) % 12) + 1, ((from_house + 6 - 1) % 12) + 1, ((from_house + 9 - 1) % 12) + 1]
        else:
            # Sun, Moon, Mercury, Venus only aspect 7th house from their position
            return [((from_house + 6 - 1) % 12) + 1]
    
    def _get_natal_aspects(self) -> List[Dict]:
        """Get natal planet aspects between all planets using house-based system"""
        natal_positions = self._get_natal_planet_positions()
        aspects = []
        
        planet_names = list(natal_positions.keys())
        for i, planet1 in enumerate(planet_names):
            for planet2 in planet_names[i+1:]:
                aspect_type = self._check_classical_aspect(
                    natal_positions[planet1]['house'],
                    natal_positions[planet2]['house'],
                    planet1
                )
                
                if aspect_type:
                    aspects.append({
                        'planet1': planet1,
                        'planet2': planet2,
                        'aspect_type': aspect_type
                    })
        
        return aspects
    
    def _get_tithi_shunya_rashi(self) -> int:
        """Calculate Tithi Shunya Rashi"""
        try:
            natal_positions = self._get_natal_planet_positions()
            sun_long = natal_positions['Sun']['longitude']
            moon_long = natal_positions['Moon']['longitude']
            
            tithi_deg = (moon_long - sun_long) % 360
            tithi_num = int(tithi_deg / 12) + 1
            
            tithi_shunya_signs = {
                1: 11, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11,
                9: 0, 10: 1, 11: 2, 12: 3, 13: 4, 14: 5, 15: 6
            }
            
            return tithi_shunya_signs.get(tithi_num, 0)
        except:
            return 0
    
    def _get_avayogi_sign(self) -> int:
        """Calculate Avayogi sign"""
        try:
            natal_positions = self._get_natal_planet_positions()
            sun_long = natal_positions['Sun']['longitude']
            moon_long = natal_positions['Moon']['longitude']
            
            yogi_point = (sun_long + moon_long) % 360
            avayogi_point = (yogi_point + 186.666667) % 360
            
            return int(avayogi_point / 30)
        except:
            return 0
    
    def _get_maraka_houses(self) -> List[int]:
        """Get Maraka houses (2nd and 7th from ascendant)"""
        return [2, 7]
    
    def _get_house_lord(self, house_num: int) -> str:
        """Get lord of house based on ascendant sign"""
        try:
            natal_positions = self._get_natal_planet_positions()
            # Get ascendant sign from any planet's house calculation
            asc_sign = None
            for planet, pos in natal_positions.items():
                if 'sign' in pos and 'house' in pos:
                    # Reverse calculate ascendant sign
                    asc_sign = (pos['sign'] - pos['house'] + 1) % 12
                    break
            
            if asc_sign is None:
                return None
            
            # Calculate house sign
            house_sign = (asc_sign + house_num - 1) % 12
            
            # Get house lord (sign rulers)
            house_lords = {
                0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
                6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"
            }
            
            return house_lords.get(house_sign)
        except:
            return None
    
    def _get_5_fold_friendship(self, planet1: str, planet2: str) -> str:
        """Calculate 5-fold friendship between planets"""
        if not planet1 or not planet2 or planet1 == planet2:
            return "neutral"
        
        # Natural friendship
        natural_friends = {
            "Sun": ["Moon", "Mars", "Jupiter"],
            "Moon": ["Sun", "Mercury"],
            "Mars": ["Sun", "Moon", "Jupiter"],
            "Mercury": ["Sun", "Venus"],
            "Jupiter": ["Sun", "Moon", "Mars"],
            "Venus": ["Mercury", "Saturn"],
            "Saturn": ["Mercury", "Venus"]
        }
        
        natural_enemies = {
            "Sun": ["Venus", "Saturn"],
            "Moon": ["None"],
            "Mars": ["Mercury"],
            "Mercury": ["Moon"],
            "Jupiter": ["Mercury", "Venus"],
            "Venus": ["Sun", "Moon"],
            "Saturn": ["Sun", "Moon", "Mars"]
        }
        
        if planet2 in natural_friends.get(planet1, []):
            return "friend"
        elif planet2 in natural_enemies.get(planet1, []):
            return "enemy"
        else:
            return "neutral"
    
    def _get_nakshatra_lord(self, longitude: float) -> str:
        """Get nakshatra lord for given longitude"""
        nakshatra_lords = [
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
            "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars",
            "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
            "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
        ]
        
        nakshatra_index = int(longitude / 13.333333333333334)
        return nakshatra_lords[nakshatra_index % 27]
    
    def _calculate_dignity(self, planet: str, sign_num: int) -> str:
        """Calculate planet's dignity in sign"""
        exaltations = {
            "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, 
            "Jupiter": 3, "Venus": 11, "Saturn": 6
        }
        debilitations = {
            "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
            "Jupiter": 9, "Venus": 5, "Saturn": 0
        }
        own_signs = {
            "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
            "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]
        }
        
        if planet in exaltations and exaltations[planet] == sign_num:
            return "exalted"
        elif planet in debilitations and debilitations[planet] == sign_num:
            return "debilitated"
        elif planet in own_signs and sign_num in own_signs[planet]:
            return "own_sign"
        else:
            return "neutral_sign"