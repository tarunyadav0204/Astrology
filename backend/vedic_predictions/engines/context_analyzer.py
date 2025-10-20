from .base_predictor import BasePredictionEngine
from .nakshatra_analyzer import NakshatraAnalyzer
from .badhaka_maraka_analyzer import BadhakaMarakaAnalyzer

class ContextAnalyzer(BasePredictionEngine):
    def __init__(self):
        super().__init__()
        self.nakshatra_analyzer = NakshatraAnalyzer()
        self.badhaka_maraka_analyzer = BadhakaMarakaAnalyzer()
    
    def analyze_natal_context(self, natal_chart, natal_planet, transiting_planet):
        """Analyze natal chart context for the aspected planet"""
        context = {
            'natal_house': None,
            'natal_sign': None,
            'dignity': 'neutral',
            'house_lordships': [],
            'transiting_house': None,
            'transiting_lordships': []
        }
        
        # Find natal planet position
        planets = natal_chart.get('planets', {})
        if natal_planet in planets:
            planet_data = planets[natal_planet]
            context['natal_house'] = planet_data.get('house')
            context['natal_sign'] = planet_data.get('sign')
            context['dignity'] = self._calculate_dignity(natal_planet, planet_data.get('sign'), planet_data.get('degree'))
        
        # Find transiting planet position and lordships
        if transiting_planet in planets:
            planet_data = planets[transiting_planet]
            context['transiting_house'] = planet_data.get('house')
            context['transiting_lordships'] = self._get_house_lordships(transiting_planet, natal_chart)
        
        return context
    
    def _calculate_dignity(self, planet, sign, degree=None):
        """Enhanced dignity calculation with degree precision"""
        from ..config.planetary_dignity import (
            EXALTATION_DATA, DEBILITATION_DATA, OWN_SIGNS, 
            MOOLATRIKONA_DATA, NATURAL_FRIENDS, NATURAL_ENEMIES
        )
        
        # Check exaltation with degree precision if available
        if planet in EXALTATION_DATA:
            exalt_data = EXALTATION_DATA[planet]
            if sign == exalt_data['sign']:
                if degree is not None:
                    # Within 5 degrees of exact exaltation degree
                    if abs(degree - exalt_data['degree']) <= 5:
                        return 'exalted'
                else:
                    return 'exalted'
        
        # Check debilitation with degree precision
        if planet in DEBILITATION_DATA:
            debil_data = DEBILITATION_DATA[planet]
            if sign == debil_data['sign']:
                if degree is not None:
                    if abs(degree - debil_data['degree']) <= 5:
                        return 'debilitated'
                else:
                    return 'debilitated'
        
        # Check Moolatrikona
        if planet in MOOLATRIKONA_DATA:
            moola_data = MOOLATRIKONA_DATA[planet]
            if sign == moola_data['sign']:
                if degree is not None:
                    if moola_data['start_degree'] <= degree <= moola_data['end_degree']:
                        return 'moolatrikona'
                else:
                    return 'moolatrikona'
        
        # Check own sign
        if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
            return 'own_sign'
        
        # Check friendship based on sign lord
        sign_lords = {0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
                     6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'}
        
        sign_lord = sign_lords.get(sign)
        if sign_lord:
            if planet in NATURAL_FRIENDS and sign_lord in NATURAL_FRIENDS[planet]:
                return 'friend_sign'
            elif planet in NATURAL_ENEMIES and sign_lord in NATURAL_ENEMIES[planet]:
                return 'enemy_sign'
        
        return 'neutral_sign'
    
    def _check_combustion(self, planet, planet_longitude, sun_longitude):
        """Check if planet is combust or cazimi"""
        from ..config.combustion import COMBUSTION_THRESHOLDS, CAZIMI_THRESHOLD, CAZIMI_CAPABLE
        
        if planet == 'Sun' or planet not in COMBUSTION_THRESHOLDS:
            return 'normal'
        
        # Calculate angular distance
        distance = abs(planet_longitude - sun_longitude)
        if distance > 180:
            distance = 360 - distance
        
        # Check cazimi first (within 1 degree for Mercury/Venus)
        if distance <= CAZIMI_THRESHOLD and planet in CAZIMI_CAPABLE:
            return 'cazimi'
        
        # Check combustion
        threshold = COMBUSTION_THRESHOLDS[planet]
        if distance <= threshold:
            return 'combust'
        
        return 'normal'
    
    def _check_retrograde_status(self, planet, planet_data):
        """Check retrograde status and motion type"""
        from ..config.retrograde import RETROGRADE_CAPABLE, NEVER_RETROGRADE, STATIONARY_ORB
        
        # Sun and Moon never go retrograde
        if planet in NEVER_RETROGRADE:
            return 'direct'
        
        if planet not in RETROGRADE_CAPABLE:
            return 'direct'
        
        # Check if planet data has retrograde flag
        is_retrograde = planet_data.get('retrograde', False)
        speed = abs(planet_data.get('speed', 1.0))  # Daily motion in degrees
        
        # Check if stationary (very slow motion)
        if speed <= STATIONARY_ORB:
            return 'stationary'
        
        return 'retrograde' if is_retrograde else 'direct'
    
    def get_affected_life_areas(self, natal_house, transiting_house):
        """Get life areas affected by the transit"""
        areas = []
        
        if natal_house:
            natal_meanings = self.house_meanings.get(natal_house, {})
            areas.extend(natal_meanings.get('primary', []))
        
        if transiting_house:
            transit_meanings = self.house_meanings.get(transiting_house, {})
            areas.extend(transit_meanings.get('primary', []))
        
        return list(set(areas))
    
    def _get_house_lordships(self, planet, natal_chart):
        """Get house lordships for a planet based on ascendant"""
        from event_prediction.house_significations import SIGN_LORDS
        
        # Get ascendant sign from chart
        ascendant_sign = int(natal_chart.get('ascendant', 0) / 30)
        
        lordships = []
        for house_num in range(1, 13):
            house_sign = (ascendant_sign + house_num - 1) % 12
            house_lord = SIGN_LORDS.get(house_sign)
            if house_lord == planet:
                lordships.append(house_num)
        
        return lordships
    
    def get_comprehensive_life_areas(self, natal_context, transiting_context):
        """Get comprehensive life areas including lordships"""
        areas = []
        
        # Natal planet's house
        if natal_context.get('natal_house'):
            natal_meanings = self.house_meanings.get(natal_context['natal_house'], {})
            areas.extend(natal_meanings.get('primary', []))
        
        # Transiting planet's natal house
        if transiting_context.get('transiting_house'):
            transit_meanings = self.house_meanings.get(transiting_context['transiting_house'], {})
            areas.extend(transit_meanings.get('primary', []))
        
        # Transiting planet's lordships
        for lordship in transiting_context.get('transiting_lordships', []):
            lord_meanings = self.house_meanings.get(lordship, {})
            areas.extend(lord_meanings.get('primary', []))
        
        return list(set(areas))
    
    def _get_natural_nature(self, planet):
        """Determine natural benefic/malefic nature"""
        from ..config.natural_benefic_malefic import NATURAL_BENEFICS, NATURAL_MALEFICS, NATURAL_NEUTRALS
        
        if planet in NATURAL_BENEFICS:
            return 'benefic'
        elif planet in NATURAL_MALEFICS:
            return 'malefic'
        elif planet in NATURAL_NEUTRALS:
            return 'neutral'
        else:
            return 'neutral'
    
    def _get_functional_nature(self, planet, natal_chart):
        """Determine functional benefic/malefic nature based on ascendant"""
        from ..config.functional_nature import FUNCTIONAL_BENEFICS, FUNCTIONAL_MALEFICS, FUNCTIONAL_NEUTRALS
        
        if not natal_chart or 'ascendant' not in natal_chart:
            return 'neutral'
        
        # Get ascendant sign (0-11)
        ascendant_sign = int(natal_chart['ascendant'] / 30) % 12
        
        if planet in FUNCTIONAL_BENEFICS.get(ascendant_sign, []):
            return 'benefic'
        elif planet in FUNCTIONAL_MALEFICS.get(ascendant_sign, []):
            return 'malefic'
        elif planet in FUNCTIONAL_NEUTRALS.get(ascendant_sign, []):
            return 'neutral'
        else:
            return 'neutral'
    
    def _get_temporal_nature(self, planet, dasha_data):
        """Determine temporal benefic/malefic based on current dasha lord"""
        if not dasha_data:
            return 'neutral'
        
        # Check if planet is current dasha lord at any level
        current_dashas = []
        if 'mahadasha' in dasha_data:
            current_dashas.append(dasha_data['mahadasha'].get('planet'))
        if 'antardasha' in dasha_data:
            current_dashas.append(dasha_data['antardasha'].get('planet'))
        if 'pratyantardasha' in dasha_data:
            current_dashas.append(dasha_data['pratyantardasha'].get('planet'))
        
        # Planet becomes temporally benefic if it's running its dasha
        if planet in current_dashas:
            return 'benefic'
        
        return 'neutral'
    
    def _get_comprehensive_benefic_analysis(self, planet, natal_chart, dasha_data=None):
        """Get comprehensive benefic/malefic analysis combining all three types"""
        natural = self._get_natural_nature(planet)
        functional = self._get_functional_nature(planet, natal_chart)
        temporal = self._get_temporal_nature(planet, dasha_data)
        
        # Determine final nature based on priority
        final_nature = functional  # Functional takes precedence
        
        # Temporal benefic status overrides if planet is dasha lord
        if temporal == 'benefic':
            final_nature = 'benefic'
        
        return {
            'natural': natural,
            'functional': functional, 
            'temporal': temporal,
            'final': final_nature
        }
    
    def enhance_prediction_with_context(self, base_prediction, natal_context, transiting_context, natal_chart=None):
        """Enhance base prediction with comprehensive natal chart context"""
        print(f"[PLANETARY_DEBUG] enhance_prediction_with_context called")
        print(f"[PLANETARY_DEBUG] natal_context: {bool(natal_context)}")
        print(f"[PLANETARY_DEBUG] transiting_context: {bool(transiting_context)}")
        
        enhanced = base_prediction.copy()
        
        # Only enhance if we have context data
        if not natal_context and not transiting_context:
            print(f"[PLANETARY_DEBUG] No context data, returning early")
            enhanced['intensity_modifier'] = 1.0
            return enhanced
        
        # Modify based on dignity using config multipliers
        from ..config.planetary_dignity import DIGNITY_MULTIPLIERS
        
        dignity = natal_context.get('dignity', 'neutral_sign')
        enhanced['intensity_modifier'] = DIGNITY_MULTIPLIERS.get(dignity, 1.0)
        
        dignity_descriptions = {
            'exalted': 'exalted',
            'moolatrikona': 'in Moolatrikona',
            'own_sign': 'in own sign',
            'friend_sign': 'in friendly sign',
            'enemy_sign': 'in enemy sign',
            'debilitated': 'debilitated'
        }
        
        # Get comprehensive benefic/malefic analysis
        natal_benefic_analysis = self._get_comprehensive_benefic_analysis(
            enhanced['natal_planet'], natal_chart, base_prediction.get('dasha_data')
        )
        natal_functional_nature = natal_benefic_analysis['final']
        
        # Get badhaka/maraka analysis
        natal_badhaka_maraka = self.badhaka_maraka_analyzer.analyze_planet_badhaka_maraka(
            enhanced['natal_planet'], natal_chart
        )
        
        # Initialize variables
        transiting_dignity = 'neutral_sign'
        transiting_functional_nature = 'neutral'
        transiting_combustion = 'normal'
        natal_combustion = 'normal'
        transiting_retrograde = 'direct'
        natal_retrograde = 'direct'
        
        if transiting_context.get('transiting_house'):
            # Get transiting planet's natal position for dignity calculation
            planets = natal_chart.get('planets', {})
            if enhanced['transiting_planet'] in planets:
                trans_data = planets[enhanced['transiting_planet']]
                transiting_dignity = self._calculate_dignity(
                    enhanced['transiting_planet'], 
                    trans_data.get('sign'), 
                    trans_data.get('degree')
                )
                
                # Check combustion for transiting planet
                if 'Sun' in planets:
                    sun_longitude = planets['Sun'].get('longitude', 0)
                    trans_longitude = trans_data.get('longitude', 0)
                    transiting_combustion = self._check_combustion(
                        enhanced['transiting_planet'], trans_longitude, sun_longitude
                    )
                
                # Check retrograde status for transiting planet
                transiting_retrograde = self._check_retrograde_status(
                    enhanced['transiting_planet'], trans_data
                )
            
            transiting_benefic_analysis = self._get_comprehensive_benefic_analysis(
                enhanced['transiting_planet'], natal_chart, base_prediction.get('dasha_data')
            )
            transiting_functional_nature = transiting_benefic_analysis['final']
            
            # Get badhaka/maraka analysis for transiting planet
            transiting_badhaka_maraka = self.badhaka_maraka_analyzer.analyze_planet_badhaka_maraka(
                enhanced['transiting_planet'], natal_chart
            )
        
        # Check combustion and retrograde for natal planet
        if natal_context.get('natal_house'):
            planets = natal_chart.get('planets', {})
            if enhanced['natal_planet'] in planets and 'Sun' in planets:
                natal_data = planets[enhanced['natal_planet']]
                sun_longitude = planets['Sun'].get('longitude', 0)
                natal_longitude = natal_data.get('longitude', 0)
                natal_combustion = self._check_combustion(
                    enhanced['natal_planet'], natal_longitude, sun_longitude
                )
                
                # Check retrograde status for natal planet
                natal_retrograde = self._check_retrograde_status(
                    enhanced['natal_planet'], natal_data
                )
        
        # Apply combustion and retrograde modifiers
        from ..config.combustion import COMBUSTION_MULTIPLIERS
        from ..config.retrograde import RETROGRADE_MULTIPLIERS
        
        natal_combustion_modifier = COMBUSTION_MULTIPLIERS.get(natal_combustion, 1.0)
        transiting_combustion_modifier = COMBUSTION_MULTIPLIERS.get(transiting_combustion, 1.0)
        natal_retrograde_modifier = RETROGRADE_MULTIPLIERS.get(natal_retrograde, 1.0)
        transiting_retrograde_modifier = RETROGRADE_MULTIPLIERS.get(transiting_retrograde, 1.0)
        
        enhanced['intensity_modifier'] *= (natal_combustion_modifier * transiting_combustion_modifier * 
                                          natal_retrograde_modifier * transiting_retrograde_modifier)
        
        # Apply functional, temporal, badhaka, and maraka modifiers
        from ..config.functional_nature import FUNCTIONAL_MULTIPLIERS
        from ..config.natural_benefic_malefic import TEMPORAL_BENEFIC_MULTIPLIER, TEMPORAL_NEUTRAL_MULTIPLIER
        from ..config.badhaka_maraka import BADHAKA_MULTIPLIER, MARAKA_MULTIPLIER
        
        functional_modifier = FUNCTIONAL_MULTIPLIERS.get(natal_functional_nature, 1.0)
        
        # Apply temporal modifier if planet is dasha lord
        temporal_modifier = 1.0
        if natal_benefic_analysis['temporal'] == 'benefic':
            temporal_modifier = TEMPORAL_BENEFIC_MULTIPLIER
        
        transiting_temporal_modifier = 1.0
        if 'transiting_benefic_analysis' in locals() and transiting_benefic_analysis['temporal'] == 'benefic':
            transiting_temporal_modifier = TEMPORAL_BENEFIC_MULTIPLIER
        
        # Apply badhaka/maraka modifiers
        natal_badhaka_modifier = BADHAKA_MULTIPLIER if natal_badhaka_maraka['is_badhaka'] else 1.0
        natal_maraka_modifier = MARAKA_MULTIPLIER if natal_badhaka_maraka['is_maraka'] else 1.0
        
        transiting_badhaka_modifier = 1.0
        transiting_maraka_modifier = 1.0
        if 'transiting_badhaka_maraka' in locals():
            transiting_badhaka_modifier = BADHAKA_MULTIPLIER if transiting_badhaka_maraka['is_badhaka'] else 1.0
            transiting_maraka_modifier = MARAKA_MULTIPLIER if transiting_badhaka_maraka['is_maraka'] else 1.0
        
        enhanced['intensity_modifier'] *= (functional_modifier * temporal_modifier * transiting_temporal_modifier * 
                                          natal_badhaka_modifier * natal_maraka_modifier * 
                                          transiting_badhaka_modifier * transiting_maraka_modifier)
        
        # Build context note with dignity, functional nature, combustion, and retrograde
        context_parts = []
        if dignity != 'neutral_sign':
            context_parts.append(f"{enhanced['natal_planet']} is {dignity_descriptions.get(dignity, dignity)}")
        if natal_functional_nature != 'neutral':
            context_parts.append(f"functional {natal_functional_nature} for this ascendant")
        if natal_combustion == 'combust':
            context_parts.append(f"{enhanced['natal_planet']} is combust (weakened by Sun)")
        elif natal_combustion == 'cazimi':
            context_parts.append(f"{enhanced['natal_planet']} is cazimi (empowered by Sun)")
        if natal_retrograde == 'retrograde':
            context_parts.append(f"{enhanced['natal_planet']} is retrograde (Vakri Gati)")
        elif natal_retrograde == 'stationary':
            context_parts.append(f"{enhanced['natal_planet']} is stationary (maximum intensity)")
        if transiting_combustion == 'combust':
            context_parts.append(f"{enhanced['transiting_planet']} is combust")
        elif transiting_combustion == 'cazimi':
            context_parts.append(f"{enhanced['transiting_planet']} is cazimi")
        if transiting_retrograde == 'retrograde':
            context_parts.append(f"{enhanced['transiting_planet']} is retrograde")
        elif transiting_retrograde == 'stationary':
            context_parts.append(f"{enhanced['transiting_planet']} is stationary")
        
        if context_parts:
            enhanced['context_note'] = '; '.join(context_parts)
        
        # Add comprehensive planetary analysis with all factors
        enhanced['planetary_analysis'] = {
            'natal_planet': {
                'name': enhanced['natal_planet'],
                'dignity': dignity,
                'benefic_analysis': natal_benefic_analysis,
                'functional_nature': natal_functional_nature,
                'combustion_status': natal_combustion,
                'retrograde_status': natal_retrograde,
                'badhaka_status': natal_badhaka_maraka['is_badhaka'],
                'maraka_status': natal_badhaka_maraka['is_maraka'],
                'dignity_modifier': DIGNITY_MULTIPLIERS.get(dignity, 1.0),
                'functional_modifier': functional_modifier,
                'temporal_modifier': temporal_modifier,
                'combustion_modifier': natal_combustion_modifier,
                'retrograde_modifier': natal_retrograde_modifier,
                'combined_strength': DIGNITY_MULTIPLIERS.get(dignity, 1.0) * functional_modifier * temporal_modifier * natal_combustion_modifier * natal_retrograde_modifier
            },
            'transiting_planet': {
                'name': enhanced['transiting_planet'],
                'dignity': transiting_dignity,
                'benefic_analysis': transiting_benefic_analysis if 'transiting_benefic_analysis' in locals() else {'natural': 'neutral', 'functional': 'neutral', 'temporal': 'neutral', 'final': 'neutral'},
                'functional_nature': transiting_functional_nature,
                'combustion_status': transiting_combustion,
                'retrograde_status': transiting_retrograde,
                'badhaka_status': transiting_badhaka_maraka['is_badhaka'] if 'transiting_badhaka_maraka' in locals() else False,
                'maraka_status': transiting_badhaka_maraka['is_maraka'] if 'transiting_badhaka_maraka' in locals() else False,
                'dignity_modifier': DIGNITY_MULTIPLIERS.get(transiting_dignity, 1.0),
                'functional_modifier': FUNCTIONAL_MULTIPLIERS.get(transiting_functional_nature, 1.0),
                'temporal_modifier': transiting_temporal_modifier,
                'combustion_modifier': transiting_combustion_modifier,
                'retrograde_modifier': transiting_retrograde_modifier,
                'combined_strength': DIGNITY_MULTIPLIERS.get(transiting_dignity, 1.0) * FUNCTIONAL_MULTIPLIERS.get(transiting_functional_nature, 1.0) * transiting_temporal_modifier * transiting_combustion_modifier * transiting_retrograde_modifier
            }
        }
        
        # Add retrograde significations if applicable
        from ..config.retrograde import RETROGRADE_SIGNIFICATIONS
        retrograde_effects = {}
        
        if natal_retrograde == 'retrograde' and enhanced['natal_planet'] in RETROGRADE_SIGNIFICATIONS:
            retrograde_effects['natal_planet'] = RETROGRADE_SIGNIFICATIONS[enhanced['natal_planet']]
        
        if transiting_retrograde == 'retrograde' and enhanced['transiting_planet'] in RETROGRADE_SIGNIFICATIONS:
            retrograde_effects['transiting_planet'] = RETROGRADE_SIGNIFICATIONS[enhanced['transiting_planet']]
        
        if retrograde_effects:
            enhanced['retrograde_effects'] = retrograde_effects
        
        # Add Nakshatra-level analysis if we have planetary positions
        if natal_context.get('natal_house') and transiting_context.get('transiting_house'):
            planets = natal_chart.get('planets', {})
            if enhanced['natal_planet'] in planets and enhanced['transiting_planet'] in planets:
                natal_longitude = planets[enhanced['natal_planet']].get('longitude', 0)
                transiting_longitude = planets[enhanced['transiting_planet']].get('longitude', 0)
                
                nakshatra_analysis = self.nakshatra_analyzer.analyze_nakshatra_influence(
                    enhanced['transiting_planet'],
                    enhanced['natal_planet'],
                    transiting_longitude,
                    natal_longitude
                )
                
                enhanced['nakshatra_analysis'] = nakshatra_analysis
                
                # Apply nakshatra compatibility modifier to intensity
                nakshatra_modifier = nakshatra_analysis['compatibility_score']
                enhanced['intensity_modifier'] *= nakshatra_modifier
                
                print(f"[NAKSHATRA_DEBUG] Added nakshatra analysis with compatibility: {nakshatra_modifier}")
        
        print(f"[PLANETARY_DEBUG] Enhanced planetary_analysis: {enhanced['planetary_analysis']}")
        print(f"[PLANETARY_DEBUG] Final enhanced keys: {list(enhanced.keys())}")
        
        # Keep backward compatibility
        enhanced['planetary_dignity'] = {
            'natal_planet_dignity': dignity,
            'functional_nature': natal_functional_nature,
            'dignity_modifier': DIGNITY_MULTIPLIERS.get(dignity, 1.0),
            'functional_modifier': functional_modifier,
            'combined_modifier': enhanced['intensity_modifier']
        }
        enhanced['affected_areas'] = self.get_comprehensive_life_areas(natal_context, transiting_context)
        
        # Add lordship context
        lordships = transiting_context.get('transiting_lordships', [])
        if lordships:
            lordship_text = f"{enhanced['transiting_planet']} as lord of {', '.join([f'{h}th' for h in lordships])} house{'s' if len(lordships) > 1 else ''}"
            if enhanced.get('context_note'):
                enhanced['context_note'] += f". {lordship_text}"
            else:
                enhanced['context_note'] = lordship_text
        
        # Add body parts from natal house
        natal_house = natal_context.get('natal_house')
        if natal_house:
            house_info = self.get_house_context(natal_house)
            enhanced['body_parts'] = house_info.get('body_parts', [])
        
        return enhanced