from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..engines.base_predictor import BasePredictionEngine
from ..engines.context_analyzer import ContextAnalyzer
from ..engines.timing_analyzer import TimingAnalyzer
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
        
        if not base_prediction:
            raise HTTPException(status_code=404, detail="Prediction template not found")
        
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
            remedies = base_engine.get_remedies(aspect['planet1'], affected_houses)
        
        # Get activated planets and houses with reasons
        activated_planets = [aspect['planet1'], aspect['planet2']]
        formatted_activations = []
        
        try:
            house_activations = {}
            
            # Transiting planet tenancy (where it's located in natal chart)
            if transiting_context.get('transiting_house'):
                house = transiting_context['transiting_house']
                if house not in house_activations:
                    house_activations[house] = []
                house_activations[house].append(f"{aspect['planet1']} tenancy")
            
            # Transiting planet lordships
            for lordship in transiting_context.get('transiting_lordships', []):
                if lordship not in house_activations:
                    house_activations[lordship] = []
                house_activations[lordship].append(f"{aspect['planet1']} lordship")
            
            # Natal planet tenancy (where it's located)
            if natal_context.get('natal_house'):
                house = natal_context['natal_house']
                if house not in house_activations:
                    house_activations[house] = []
                house_activations[house].append(f"{aspect['planet2']} tenancy")
            
            # Natal planet lordships - need to calculate these too
            natal_planet_lordships = context_analyzer._get_house_lordships(aspect['planet2'], natal_chart) if natal_chart else []
            for lordship in natal_planet_lordships:
                if lordship not in house_activations:
                    house_activations[lordship] = []
                house_activations[lordship].append(f"{aspect['planet2']} lordship")
            
            # Convert to formatted list
            for house, reasons in house_activations.items():
                formatted_activations.append({
                    'house': house,
                    'reasons': reasons
                })
            
            # Sort by house number
            formatted_activations.sort(key=lambda x: x['house'])
            
        except Exception as house_error:
            print(f"[PREDICTION_ERROR] House activation error: {house_error}")
            formatted_activations = []
        
        print(f"[PREDICTION_DEBUG] Final house activations: {formatted_activations}")
        
        # Get house-wise life areas after formatted_activations is ready
        house_wise_areas = {}
        for activation in formatted_activations:
            house = activation['house']
            house_meanings = context_analyzer.house_meanings.get(house, {})
            if house_meanings.get('primary'):
                house_wise_areas[house] = house_meanings['primary']
        
        affected_areas = enhanced_prediction.get('affected_areas', [])
        
        # Compile final prediction
        aspect_name = aspect['aspect_type'].replace('_house', '').replace('th', 'th')
        prediction = {
            'aspect_summary': f"{aspect['planet1']} {aspect['aspect_type'].replace('_house', '')} aspect to natal {aspect['planet2']}",
            'theme': enhanced_prediction['theme'],
            'timing': timing_analyzer.get_timing_description(timing_info, period),
            'intensity': round(final_intensity, 2),
            'effects': {
                'positive': enhanced_prediction.get('positive', ''),
                'negative': enhanced_prediction.get('negative', ''),
                'neutral': enhanced_prediction.get('neutral', '')
            },
            'affected_areas': affected_areas,
            'house_wise_areas': house_wise_areas,
            'activated_planets': activated_planets,
            'house_activations': formatted_activations,
            'lordship_context': f"{aspect['planet1']} lords: {', '.join([f'{h}th' for h in transiting_context.get('transiting_lordships', [])])}" if transiting_context.get('transiting_lordships') else '',
            'context_notes': enhanced_prediction.get('context_note', ''),
            'body_parts': enhanced_prediction.get('body_parts', []),
            'planetary_dignity': enhanced_prediction.get('planetary_dignity', {}),
            'planetary_analysis': enhanced_prediction.get('planetary_analysis', {}),
            'nakshatra_analysis': enhanced_prediction.get('nakshatra_analysis', {}),
            'remedies': remedies,
            'period_info': {
                'start_date': period['start_date'],
                'end_date': period['end_date'],
                'peak_date': period.get('peak_date'),
                'duration_days': timing_info['duration_days']
            },
            'dasha_relevance': bool(dasha_relevance),
            'dasha_hierarchy': {k: v for k, v in {
                'mahadasha': dasha_relevance.get('mahadasha'),
                'antardasha': dasha_relevance.get('antardasha'), 
                'pratyantardasha': dasha_relevance.get('pratyantardasha'),
                'sookshma': dasha_relevance.get('sookshma'),
                'prana': dasha_relevance.get('prana')
            }.items() if v is not None} if dasha_relevance else None
        }
        
        return {"prediction": prediction}
        
    except Exception as e:
        import traceback
        print(f"[PREDICTION_ERROR] Full traceback: {traceback.format_exc()}")
        print(f"[PREDICTION_ERROR] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction generation failed: {str(e)}")