from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..engines.base_predictor import BasePredictionEngine
from ..engines.context_analyzer import ContextAnalyzer
from ..engines.timing_analyzer import TimingAnalyzer
from ..engines.yoga_analyzer import YogaAnalyzer
from shared.dasha_calculator import DashaCalculator

router = APIRouter()

class PredictionRequest(BaseModel):
    birth_data: Dict[str, Any]
    aspect_data: Dict[str, Any]
    period_data: Dict[str, Any]
    natal_chart: Optional[Dict[str, Any]] = None
    dasha_data: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"

@router.post("/api/vedic-transit-prediction")
async def get_transit_prediction(request: PredictionRequest):
    """Generate comprehensive prediction for transit aspect period"""
    try:
        print(f"[PREDICTION_DEBUG] Received request data: {request.model_dump()}")
        # Initialize engines
        base_engine = BasePredictionEngine()
        context_analyzer = ContextAnalyzer()
        timing_analyzer = TimingAnalyzer()
        yoga_analyzer = YogaAnalyzer()
        
        # Extract data
        aspect = request.aspect_data
        period = request.period_data
        natal_chart = request.natal_chart or {}
        
        print(f"[PREDICTION_DEBUG] Aspect: {aspect}")
        print(f"[PREDICTION_DEBUG] Period: {period}")
        
        # Get base prediction template
        print(f"[PREDICTION_DEBUG] Getting base prediction for {aspect['planet1']} {aspect['aspect_type']} {aspect['planet2']}")
        base_prediction = base_engine.get_base_prediction(
            aspect['planet1'],
            aspect['aspect_type'],
            aspect['planet2']
        )
        print(f"[PREDICTION_DEBUG] Base prediction: {base_prediction}")
        print(f"[PREDICTION_DEBUG] Enhancement type: {aspect.get('enhancement_type')}")
        print(f"[PREDICTION_DEBUG] Aspect type: {aspect.get('aspect_type')}")
        
        # Handle Gandanta aspects - show explanation only, no prediction
        if aspect.get('enhancement_type') == 'gandanta':
            print(f"[PREDICTION_DEBUG] Gandanta aspect detected - returning explanation only")
            gandanta_explanation = {
                'title': 'Gandanta Point Activation',
                'description': 'A critical karmic junction between water and fire signs representing intense transformation and spiritual evolution.',
                'significance': 'Gandanta points mark the transition between emotional (water) and action-oriented (fire) energies, creating periods of vulnerability and breakthrough potential.',
                'effects': [
                    'Intense emotional and spiritual transformation',
                    'Release of deep karmic patterns',
                    'Potential for breakthrough or breakdown',
                    'Heightened intuition and psychic sensitivity',
                    'Need for spiritual practices and grounding'
                ],
                'advice': 'Use this period for meditation, spiritual practices, and releasing old patterns. Avoid major decisions during peak intensity.'
            }
            return {
                "prediction": {
                    'aspect_summary': f"{aspect['planet1']} activates Gandanta point affecting natal {aspect['planet2']}",
                    'gandanta_explanation': gandanta_explanation,
                    'period_info': {
                        'start_date': period['start_date'],
                        'end_date': period['end_date'],
                        'peak_date': period.get('peak_date')
                    },
                    'is_gandanta_only': True
                }
            }
        
        # Handle nakshatra connections - provide full analysis
        if not base_prediction and aspect.get('aspect_type') == 'nakshatra_connection':
            print(f"[PREDICTION_DEBUG] Nakshatra connection detected - providing full analysis")
            base_prediction = {
                'theme': f"Karmic nakshatra activation between {aspect['planet1']} and {aspect['planet2']}",
                'positive': 'Enhanced spiritual connection and karmic understanding through nakshatra resonance',
                'negative': 'Karmic patterns requiring conscious resolution and spiritual growth',
                'neutral': 'Deep soul-level activation through nakshatra connection and star lord influence',
                'transiting_planet': aspect['planet1'],
                'natal_planet': aspect['planet2']
            }
        
        # Generic fallback for regular house aspects
        if not base_prediction:
            print(f"[PREDICTION_DEBUG] Using generic fallback for {aspect['planet1']} {aspect['aspect_type']} {aspect['planet2']}")
            aspect_house = aspect['aspect_type'].replace('th_house', '').replace('st_house', '').replace('nd_house', '').replace('rd_house', '').replace('_house', '')
            base_prediction = {
                'theme': f"{aspect['planet1']} activating {aspect['planet2']} through {aspect_house} house connection",
                'positive': f"Harmonious activation of {aspect['planet2']} qualities through {aspect['planet1']} energy",
                'negative': f"Challenging activation requiring conscious integration of {aspect['planet1']}-{aspect['planet2']} energies",
                'neutral': f"{aspect['planet1']} brings dynamic change to {aspect['planet2']} significations",
                'transiting_planet': aspect['planet1'],
                'natal_planet': aspect['planet2']
            }
        
        # Analyze natal context (skip if no natal chart)
        natal_context = {}
        transiting_context = {}
        if natal_chart and isinstance(natal_chart, dict) and 'planets' in natal_chart:
            natal_context = context_analyzer.analyze_natal_context(
                natal_chart,
                aspect['planet2'],  # natal planet being aspected
                aspect['planet1']   # transiting planet
            )
            transiting_context = {
                'transiting_house': natal_context.get('transiting_house'),
                'transiting_lordships': natal_context.get('transiting_lordships', [])
            }
        
        print(f"[PREDICTION_DEBUG] Natal chart type: {type(natal_chart)}")
        if isinstance(natal_chart, dict):
            print(f"[PREDICTION_DEBUG] Natal chart keys: {list(natal_chart.keys())}")
            if 'planets' in natal_chart:
                print(f"[PREDICTION_DEBUG] Planets structure: {type(natal_chart['planets'])}")
        print(f"[PREDICTION_DEBUG] Natal context: {natal_context}")
        print(f"[PREDICTION_DEBUG] Transiting context: {transiting_context}")
        
        # Enhance with context including natal chart for functional nature
        enhanced_prediction = context_analyzer.enhance_prediction_with_context(
            base_prediction,
            natal_context,
            transiting_context,
            natal_chart
        )
        
        # Analyze timing
        print(f"[PREDICTION_DEBUG] Analyzing timing for period: {period}")
        timing_info = timing_analyzer.analyze_period_timing(period)
        print(f"[PREDICTION_DEBUG] Timing info: {timing_info}")
        
        # Calculate complete dasha hierarchy for the period
        dasha_calculator = DashaCalculator()
        period_date = datetime.strptime(period['start_date'], '%Y-%m-%d')
        complete_dashas = dasha_calculator.calculate_dashas_for_date(period_date, request.birth_data)
        
        # Use complete dashas or fallback to provided dasha_data
        dasha_relevance = complete_dashas if complete_dashas else request.dasha_data
        transiting_planet = aspect['planet1']
        aspected_planet = aspect['planet2']
        print(f"[PREDICTION_DEBUG] Complete dashas calculated: {complete_dashas}")
        print(f"[PREDICTION_DEBUG] Using dasha data: {dasha_relevance}")
        print(f"[PREDICTION_DEBUG] Calculating intensity with dasha: {dasha_relevance}, phase: {timing_info['phase']}")
        final_intensity = base_engine.calculate_intensity(
            dasha_relevance,
            timing_info['phase']
        )
        print(f"[PREDICTION_DEBUG] Final intensity: {final_intensity}")
        
        # Get remedies if challenging
        remedies = None
        if 'negative' in enhanced_prediction and final_intensity > 1.0:
            affected_houses = [natal_context.get('natal_house'), aspect.get('required_transit_house')]
            affected_houses = [h for h in affected_houses if h is not None]
            remedies = base_engine.get_remedies(aspect['planet1'], affected_houses) if hasattr(base_engine, 'get_remedies') else None
        
        # Get activated planets and houses with reasons
        activated_planets = [aspect['planet1'], aspect['planet2']]
        
        # Calculate house activations with hierarchy
        house_activations = {
            'primary': [],
            'secondary': [],
            'tertiary': []
        }
        
        try:
            # Primary: Direct tenancy and lordship
            if natal_context.get('natal_house'):
                house_activations['primary'].append({
                    'house': natal_context['natal_house'],
                    'reasons': [f"{aspect['planet2']} tenancy"]
                })
            
            if transiting_context.get('transiting_house'):
                house_activations['primary'].append({
                    'house': transiting_context['transiting_house'],
                    'reasons': [f"{aspect['planet1']} tenancy"]
                })
            
            # Add transiting planet lordships
            for lordship in transiting_context.get('transiting_lordships', []):
                house_activations['primary'].append({
                    'house': lordship,
                    'reasons': [f"{aspect['planet1']} lordship"]
                })
            
            # Add natal planet lordships
            if natal_chart:
                natal_planet_lordships = context_analyzer._get_house_lordships(aspect['planet2'], natal_chart)
                for lordship in natal_planet_lordships:
                    house_activations['primary'].append({
                        'house': lordship,
                        'reasons': [f"{aspect['planet2']} lordship"]
                    })
            
            # Secondary: Conjunctions within orb (3-5 degrees)
            if natal_chart and 'planets' in natal_chart:
                transiting_house = transiting_context.get('transiting_house')
                if transiting_house:
                    # Find planets in same house as transiting planet
                    for planet_name, planet_data in natal_chart['planets'].items():
                        if isinstance(planet_data, dict) and planet_data.get('house') == transiting_house:
                            if planet_name != aspect['planet2']:  # Don't duplicate natal planet
                                # Get conjunct planet's lordships
                                conjunct_lordships = context_analyzer._get_house_lordships(planet_name, natal_chart)
                                for lordship in conjunct_lordships:
                                    house_activations['secondary'].append({
                                        'house': lordship,
                                        'reasons': [f"{planet_name} conjunction"]
                                    })
            
            # Tertiary: Dasha lord houses
            if dasha_relevance:
                for level, dasha_info in dasha_relevance.items():
                    if isinstance(dasha_info, dict) and 'planet' in dasha_info:
                        dasha_planet = dasha_info['planet']
                        # Get dasha planet's lordships (simplified)
                        if dasha_planet in ['Jupiter', 'Venus', 'Mercury', 'Mars', 'Saturn', 'Sun', 'Moon']:
                            house_activations['tertiary'].append({
                                'house': 1,  # Simplified - would need proper lordship calculation
                                'reasons': [f"{dasha_planet} dasha lord"]
                            })
            
            # Remove duplicates and empty lists
            for level in house_activations:
                seen_houses = set()
                unique_activations = []
                for activation in house_activations[level]:
                    if activation['house'] not in seen_houses:
                        seen_houses.add(activation['house'])
                        unique_activations.append(activation)
                house_activations[level] = unique_activations
        
        except Exception as e:
            print(f"[HOUSE_DEBUG] Error calculating house activations: {e}")
            house_activations = {'primary': [], 'secondary': [], 'tertiary': []}
        
        # Analyze activated yogas
        activated_yogas = []
        try:
            activated_yogas = yoga_analyzer.analyze_activated_yogas(house_activations)
            print(f"[YOGA_DEBUG] Activated yogas: {activated_yogas}")
        except Exception as e:
            print(f"[YOGA_DEBUG] Error analyzing yogas: {e}")
        
        # Compile final prediction
        prediction = {
            'aspect_summary': f"{aspect['planet1']} {aspect['aspect_type'].replace('_house', '')} aspect to natal {aspect['planet2']}",
            'theme': enhanced_prediction['theme'],
            'intensity': round(final_intensity, 2),
            'effects': {
                'positive': enhanced_prediction.get('positive', ''),
                'negative': enhanced_prediction.get('negative', ''),
                'neutral': enhanced_prediction.get('neutral', '')
            },
            'activated_planets': activated_planets,
            'house_activations': house_activations,
            'activated_yogas': activated_yogas,
            'planetary_analysis': enhanced_prediction.get('planetary_analysis', {}),
            'nakshatra_analysis': enhanced_prediction.get('nakshatra_analysis', {}),
            'remedies': remedies,
            'period_info': {
                'start_date': period['start_date'],
                'end_date': period['end_date'],
                'peak_date': period.get('peak_date')
            },
            'dasha_hierarchy': {
                'mahadasha': dasha_relevance.get('mahadasha', {}).get('planet') if dasha_relevance and isinstance(dasha_relevance.get('mahadasha'), dict) else dasha_relevance.get('mahadasha') if dasha_relevance else None,
                'antardasha': dasha_relevance.get('antardasha', {}).get('planet') if dasha_relevance and isinstance(dasha_relevance.get('antardasha'), dict) else dasha_relevance.get('antardasha') if dasha_relevance else None,
                'pratyantardasha': dasha_relevance.get('pratyantardasha', {}).get('planet') if dasha_relevance and isinstance(dasha_relevance.get('pratyantardasha'), dict) else dasha_relevance.get('pratyantardasha') if dasha_relevance else None,
                'sookshma': dasha_relevance.get('sookshma', {}).get('planet') if dasha_relevance and isinstance(dasha_relevance.get('sookshma'), dict) else dasha_relevance.get('sookshma') if dasha_relevance else None,
                'prana': dasha_relevance.get('prana', {}).get('planet') if dasha_relevance and isinstance(dasha_relevance.get('prana'), dict) else dasha_relevance.get('prana') if dasha_relevance else None
            } if dasha_relevance else None
        }
        
        return {"prediction": prediction}
        
    except Exception as e:
        import traceback
        print(f"[PREDICTION_ERROR] Full traceback: {traceback.format_exc()}")
        print(f"[PREDICTION_ERROR] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction generation failed: {str(e)}")