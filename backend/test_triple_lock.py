"""
Test Triple-Lock Event Prediction System
Birth Chart: 2nd April 1980, 2:55 PM, Hisar, Haryana, India
"""

import sys
from datetime import datetime, timedelta
from types import SimpleNamespace

# Add backend to path
sys.path.insert(0, '/Users/tarunydv/Desktop/Code/AstrologyApp/backend')

from calculators.chart_calculator import ChartCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator
from calculators.shadbala_calculator import ShadbalaCalculator
from calculators.ashtakavarga import AshtakavargaCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.event_predictor.parashari_predictor import ParashariEventPredictor

# Birth data
birth_data = {
    'date': '1980-04-02',
    'time': '14:55:00',
    'latitude': 29.1492,
    'longitude': 75.7217,
    'name': 'Test Chart'
}

print("=" * 80)
print("TRIPLE-LOCK EVENT PREDICTION TEST")
print("=" * 80)
print(f"\nBirth Details:")
print(f"  Date: {birth_data['date']}")
print(f"  Time: {birth_data['time']}")
print(f"  Place: Hisar, Haryana, India")
print(f"  Coordinates: {birth_data['latitude']}°N, {birth_data['longitude']}°E")

# Initialize calculators
print("\n" + "=" * 80)
print("INITIALIZING CALCULATORS...")
print("=" * 80)

birth_obj = SimpleNamespace(**birth_data)
chart_calc = ChartCalculator({})
chart_data = chart_calc.calculate_chart(birth_obj)

print("\n✓ Chart Calculator initialized")
print(f"  Ascendant: {chart_data['ascendant']:.2f}°")

# Display planetary positions
print("\n  Planetary Positions:")
for planet, data in chart_data['planets'].items():
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_name = sign_names[data['sign']]
    print(f"    {planet:10s}: {data['longitude']:6.2f}° in {sign_name:12s} (Sign {data['sign']})")

# Initialize other calculators
transit_calc = RealTransitCalculator()
dasha_calc = DashaCalculator()
shadbala_calc = ShadbalaCalculator(chart_data)

# Create dignities calculator
class SimpleDignities:
    def __init__(self, chart_data):
        self.chart_data = chart_data
    def calculate_dignities(self):
        return {p: {'dignity': 'neutral'} for p in self.chart_data['planets'].keys()}

dignities_calc = SimpleDignities(chart_data)

# Create simple functional benefics calculator
class SimpleFunctionalBenefics:
    def __init__(self, chart_data):
        self.chart_data = chart_data
    
    def calculate_functional_benefics(self):
        asc_sign = int(self.chart_data.get('ascendant', 0) / 30)
        benefics_map = {
            0: ['Sun', 'Mars', 'Jupiter'], 1: ['Mercury', 'Venus', 'Saturn'],
            2: ['Mercury', 'Venus'], 3: ['Moon', 'Mars'], 4: ['Sun', 'Mars'],
            5: ['Mercury', 'Venus'], 6: ['Venus', 'Saturn'], 7: ['Moon', 'Jupiter'],
            8: ['Sun', 'Mars', 'Jupiter'], 9: ['Venus', 'Saturn'], 10: ['Venus', 'Saturn'],
            11: ['Sun', 'Mars', 'Jupiter']
        }
        return {'benefics': benefics_map.get(asc_sign, []), 'malefics': []}

func_benefics_calc = SimpleFunctionalBenefics(chart_data)

def ashtakavarga_calc_factory(bd, cd):
    return AshtakavargaCalculator(bd, cd)

print("✓ All calculators initialized")

# Initialize event predictor
predictor = ParashariEventPredictor(
    chart_calc,
    transit_calc,
    dasha_calc,
    shadbala_calc,
    ashtakavarga_calc_factory,
    dignities_calc,
    func_benefics_calc
)

print("✓ Triple-Lock Event Predictor initialized")

# Test prediction for next 6 months
print("\n" + "=" * 80)
print("PREDICTING EVENTS (Next 6 Months)")
print("=" * 80)

start_date = datetime.now()
end_date = start_date + timedelta(days=180)

print(f"\nPrediction Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print("\nAnalyzing... (This may take 30-60 seconds)")

try:
    events = predictor.predict_events(birth_data, start_date, end_date, min_probability=60)
    
    print(f"\n✓ Analysis complete! Found {len(events)} significant events.")
    
    if not events:
        print("\n⚠️  No high-probability events detected in this period.")
        print("    This could mean:")
        print("    - Current dasha period is not authorizing major events")
        print("    - Transit triggers are weak")
        print("    - Try extending the prediction period")
    else:
        print("\n" + "=" * 80)
        print("EVENT PREDICTIONS")
        print("=" * 80)
        
        for i, event in enumerate(events, 1):
            print(f"\n{'─' * 80}")
            print(f"EVENT #{i}: {event['event_type'].upper().replace('_', ' ')}")
            print(f"{'─' * 80}")
            
            # Basic info
            print(f"\n📅 Timing:")
            print(f"   Period: {event['start_date']} to {event['end_date']}")
            print(f"   Peak: {event['peak_date']}")
            print(f"   Precision: {event['trigger'].get('precision', 'N/A')}")
            
            # Probability and accuracy
            print(f"\n📊 Confidence:")
            print(f"   Probability: {event['probability']}%")
            print(f"   Accuracy Range: {event.get('accuracy_range', 'N/A')}")
            print(f"   Certainty: {event.get('certainty', 'N/A')}")
            print(f"   Quality: {event['quality']}")
            
            # Lock status
            locks = []
            if event.get('triple_lock'):
                locks.append("🔒🔒🔒 TRIPLE-LOCK")
            elif event.get('double_lock'):
                locks.append("🔒🔒 DOUBLE-LOCK")
            else:
                locks.append("🔒 SINGLE-LOCK")
            print(f"   Status: {' '.join(locks)}")
            
            # Authorization
            print(f"\n🎯 Authorization (Parashari):")
            auth = event['authorization']
            print(f"   Dasha: {auth['dasha']}")
            print(f"   Score: {auth['score']}")
            print(f"   Capacity: {auth['capacity']}")
            print(f"   House: {event['house']}")
            
            # Jaimini validation
            if 'jaimini_validation' in event and event['jaimini_validation'].get('validated'):
                jaimini = event['jaimini_validation']
                print(f"\n✓ Jaimini Validation:")
                print(f"   Score: {jaimini['jaimini_score']}")
                print(f"   Confidence: {jaimini['confidence_level']}")
                print(f"   Adjustment: {jaimini['adjustment']:+d}%")
                if jaimini.get('chara_dasha_support'):
                    print(f"   ✓ Chara Dasha Support")
                if jaimini.get('karaka_support'):
                    print(f"   ✓ Karaka Support")
                if jaimini.get('argala_support'):
                    print(f"   ✓ Argala Support")
            
            # Nadi validation
            if 'nadi_validation' in event and event['nadi_validation'].get('validated'):
                nadi = event['nadi_validation']
                print(f"\n🎯 Nadi Validation (Sniper Layer):")
                print(f"   Confidence: {nadi['confidence']}")
                print(f"   Adjustment: {nadi['adjustment']:+d}%")
                print(f"   Bonus Points: {nadi['bonus_points']}")
                print(f"   Exact Day: {nadi['exact_day']}")
                
                if nadi.get('linkages'):
                    print(f"\n   Linkages Detected:")
                    for link in nadi['linkages']:
                        link_type = link.get('type', 'unknown')
                        transit_p = link.get('transit_planet', 'N/A')
                        natal_p = link.get('natal_planet', 'N/A')
                        precision = link.get('precision', 0)
                        bonus = link.get('bonus', 0)
                        retro = " [Retrograde Shadow]" if link.get('retrograde_shadow') else ""
                        
                        print(f"     • {link_type.upper()}: {transit_p} ↔ {natal_p}")
                        print(f"       Precision: ±{precision:.2f}° | Bonus: +{bonus}{retro}")
                
                if nadi.get('explanation'):
                    print(f"\n   Explanation:")
                    print(f"   {nadi['explanation']}")
            
            # Trigger details
            print(f"\n⚡ Transit Trigger:")
            trigger = event['trigger']
            print(f"   Planet: {trigger['planet']}")
            print(f"   Type: {trigger['type']}")
            print(f"   House: {trigger['house']}")
            if trigger.get('double_transit'):
                print(f"   🌟 DOUBLE TRANSIT (Jupiter + Saturn)")
            if trigger.get('kakshya_active'):
                print(f"   🎯 KAKSHYA ACTIVE (3-4 day precision)")
            
            # Timing precision
            timing = event.get('timing_precision', 'N/A')
            timing_map = {
                'exact_day': '24-48 hours',
                'very_precise': '3-5 days',
                'precise': '1-2 weeks',
                'moderate': '2-4 weeks'
            }
            print(f"   Timing Window: {timing_map.get(timing, timing)}")

except Exception as e:
    print(f"\n❌ Error during prediction: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
