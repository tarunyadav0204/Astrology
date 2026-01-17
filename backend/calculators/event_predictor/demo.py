"""
Demo: How to use the Parashari Event Predictor

This shows the integration with existing calculators and usage patterns.
"""

from datetime import datetime, timedelta
from calculators.event_predictor import ParashariEventPredictor, DashaHouseGate
from calculators.chart_calculator import ChartCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator
from calculators.shadbala_calculator import ShadbalaCalculator
from calculators.ashtakavarga_calculator import AshtakavargaCalculator
from calculators.planetary_dignities import PlanetaryDignitiesCalculator
from calculators.functional_benefics_calculator import FunctionalBeneficsCalculator


def demo_parashari_predictor():
    """
    Demo: Predict events for next 2 years
    """
    
    # Sample birth data
    birth_data = {
        'date': '1990-05-15',
        'time': '14:30',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'timezone': '+05:30'
    }
    
    # Initialize calculators
    chart_calc = ChartCalculator()
    transit_calc = RealTransitCalculator()
    dasha_calc = DashaCalculator()
    
    # Calculate chart first for other calculators
    from types import SimpleNamespace
    birth_obj = SimpleNamespace(**birth_data)
    chart_data = chart_calc.calculate_chart(birth_obj)
    
    # Initialize strength calculators
    shadbala_calc = ShadbalaCalculator(chart_data)
    ashtakavarga_calc = AshtakavargaCalculator
    dignities_calc = PlanetaryDignitiesCalculator(chart_data)
    func_benefics_calc = FunctionalBeneficsCalculator(chart_data)
    
    # Initialize Parashari Predictor
    predictor = ParashariEventPredictor(
        chart_calculator=chart_calc,
        transit_calculator=transit_calc,
        dasha_calculator=dasha_calc,
        shadbala_calculator=shadbala_calc,
        ashtakavarga_calculator=ashtakavarga_calc,
        dignities_calculator=dignities_calc,
        functional_benefics_calculator=func_benefics_calc
    )
    
    # Predict events for next 2 years
    start_date = datetime.now()
    end_date = start_date + timedelta(days=730)  # 2 years
    
    print("🔮 Parashari Event Prediction")
    print("=" * 80)
    print(f"Birth Date: {birth_data['date']}")
    print(f"Prediction Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 80)
    
    events = predictor.predict_events(
        birth_data=birth_data,
        start_date=start_date,
        end_date=end_date,
        min_probability=60  # Only show events with 60%+ probability
    )
    
    print(f"\n✅ Found {len(events)} authorized events:\n")
    
    for i, event in enumerate(events, 1):
        print(f"{i}. {event['event_type'].upper().replace('_', ' ')}")
        print(f"   House: {event['house']}")
        print(f"   Probability: {event['probability']}%")
        print(f"   Nature: {event['nature']}")
        print(f"   Date Range: {event['start_date']} to {event['end_date']}")
        print(f"   Peak: {event['peak_date'].strftime('%Y-%m-%d')}")
        print(f"   Authorization: {event['authorization']['dasha']} (Score: {event['authorization']['score']})")
        print(f"   Trigger: {event['trigger']['planet']} {event['trigger']['type']}")
        print(f"   Reasons: {', '.join(event['authorization']['reasons'][:2])}")
        print()


def demo_gate_validator():
    """
    Demo: Check which houses are authorized by current dasha
    """
    
    birth_data = {
        'date': '1990-05-15',
        'time': '14:30',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'timezone': '+05:30'
    }
    
    # Calculate chart
    chart_calc = ChartCalculator()
    from types import SimpleNamespace
    birth_obj = SimpleNamespace(**birth_data)
    chart_data = chart_calc.calculate_chart(birth_obj)
    
    # Initialize Gate Validator
    gate = DashaHouseGate(chart_data)
    
    # Get current dasha
    dasha_calc = DashaCalculator()
    current_dasha = dasha_calc.calculate_current_dashas(birth_data, datetime.now())
    
    print("🚪 Dasha-House Gate Validator")
    print("=" * 80)
    print(f"Current Dasha: {current_dasha['mahadasha']['planet']} MD - {current_dasha['antardasha']['planet']} AD")
    print("=" * 80)
    
    # Get all authorized houses
    authorized = gate.get_authorized_houses(current_dasha, min_score=40)
    
    print(f"\n✅ {len(authorized)} houses authorized for activation:\n")
    
    for auth in authorized:
        print(f"House {auth['house']}: Score {auth['score']}")
        print(f"  Reasons: {', '.join(auth['reasons'][:3])}")
        print()


if __name__ == '__main__':
    print("\n" + "="*80)
    print("PARASHARI EVENT PREDICTOR - DEMO")
    print("="*80 + "\n")
    
    # Demo 1: Gate Validator
    demo_gate_validator()
    
    print("\n" + "="*80 + "\n")
    
    # Demo 2: Full Event Prediction
    demo_parashari_predictor()
