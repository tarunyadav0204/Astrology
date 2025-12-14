"""
Test script for Life Event Scanner calibration feature
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from calculators.life_event_scanner import LifeEventScanner
from calculators.chart_calculator import ChartCalculator
from shared.dasha_calculator import DashaCalculator
from calculators.real_transit_calculator import RealTransitCalculator

# Test birth data
test_birth_data = {
    'name': 'Test Person',
    'date': '1990-05-15',
    'time': '14:30',
    'latitude': 28.6139,
    'longitude': 77.2090,
    'timezone': 'Asia/Kolkata',
    'place': 'New Delhi',
    'gender': 'male'
}

print("🔮 Testing Life Event Scanner...")
print(f"Birth Data: {test_birth_data['name']}, {test_birth_data['date']}")
print("-" * 60)

try:
    # Initialize scanner
    scanner = LifeEventScanner(
        ChartCalculator({}),
        DashaCalculator(),
        RealTransitCalculator()
    )
    
    # Scan timeline
    events = scanner.scan_timeline(test_birth_data, start_age=18)
    
    print(f"\n✅ Scanner completed successfully!")
    print(f"Found {len(events)} potential life events\n")
    
    # Display results
    if events:
        print("📅 High-Probability Events:")
        print("-" * 60)
        for event in events:
            print(f"\n{event['year']} (Age {event['age']})")
            print(f"  Type: {event['type']}")
            print(f"  Label: {event['label']}")
            print(f"  Confidence: {event['confidence']}")
            print(f"  Reason: {event['reason']}")
    else:
        print("No high-probability events detected in the scanned period.")
    
    # Test high-confidence filter
    high_confidence = [e for e in events if e['confidence'] == 'High']
    print(f"\n🎯 High Confidence Events: {len(high_confidence)}")
    
    if high_confidence:
        top_event = high_confidence[0]
        print(f"\nTop Event for Calibration:")
        print(f"  Year: {top_event['year']}")
        print(f"  Type: {top_event['type']}")
        print(f"  Label: {top_event['label']}")
        print(f"  Reason: {top_event['reason']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed!")
