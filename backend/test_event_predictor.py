#!/usr/bin/env python3
"""
Test EventPredictor with birth details:
Date: 2nd April 1980
Time: 2:55 PM
Place: Hisar, Haryana, India
"""

import sys
import json
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

# Birth details for Hisar, Haryana
birth_data = {
    'date': '1980-04-02',
    'time': '14:55:00',  # 2:55 PM
    'latitude': 29.1492,  # Hisar coordinates
    'longitude': 75.7217,
    'name': 'Test User'
}

print("=" * 80)
print("TESTING EVENT PREDICTOR")
print("=" * 80)
print(f"Birth Date: 2nd April 1980")
print(f"Birth Time: 2:55 PM")
print(f"Birth Place: Hisar, Haryana, India")
print(f"Coordinates: {birth_data['latitude']}°N, {birth_data['longitude']}°E")
print("=" * 80)

# Initialize calculators
print("\n📊 Initializing calculators...")
birth_obj = SimpleNamespace(**birth_data)

chart_calc = ChartCalculator({})
chart_data = chart_calc.calculate_chart(birth_obj)

print(f"✓ Chart calculated")
print(f"  Ascendant: {chart_data['ascendant']:.2f}° ({['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][int(chart_data['ascendant'] / 30)]})")

transit_calc = RealTransitCalculator()
dasha_calc = DashaCalculator()
shadbala_calc = ShadbalaCalculator(chart_data)

# Real dignities calculator
dignities_calc = PlanetaryDignitiesCalculator(chart_data)

# Real functional benefics calculator (wrapper for dignities)
class FunctionalBeneficsCalculator:
    def __init__(self, dignities_calc):
        self.dignities_calc = dignities_calc
    
    def calculate_functional_benefics(self):
        dignities = self.dignities_calc.calculate_planetary_dignities()
        benefics = [p for p, d in dignities.items() if d.get('functional_nature') == 'benefic']
        malefics = [p for p, d in dignities.items() if d.get('functional_nature') == 'malefic']
        return {'benefics': benefics, 'malefics': malefics}

func_benefics_calc = FunctionalBeneficsCalculator(dignities_calc)

def ashtakavarga_calc_factory(bd, cd):
    return AshtakavargaCalculator(bd, cd)

print("✓ All calculators initialized")

# Initialize predictor
print("\n🔮 Initializing Triple-Lock Event Predictor...")
predictor = ParashariEventPredictor(
    chart_calc, transit_calc, dasha_calc, shadbala_calc,
    ashtakavarga_calc_factory, dignities_calc, func_benefics_calc
)
print("✓ Predictor initialized")

# Test 1: Next 6 months prediction
print("\n" + "=" * 80)
print("TEST 1: NEXT 6 MONTHS PREDICTION")
print("=" * 80)

start_date = datetime.now()
end_date = start_date + timedelta(days=180)

print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print("\nPredicting events...")

events = predictor.predict_events(birth_data, start_date, end_date, min_probability=60)

print(f"\n✓ Found {len(events)} events")

# Group by lock status
triple_lock = [e for e in events if e.get('triple_lock')]
double_lock = [e for e in events if e.get('double_lock') and not e.get('triple_lock')]
single_lock = [e for e in events if not e.get('triple_lock') and not e.get('double_lock')]

print(f"\n📊 Event Distribution:")
print(f"  🔒🔒🔒 Triple Lock (90-98% accuracy): {len(triple_lock)} events")
print(f"  🔒🔒 Double Lock (85-95% accuracy): {len(double_lock)} events")
print(f"  🔒 Single Lock (75-85% accuracy): {len(single_lock)} events")

# Show top 5 highest probability events
print(f"\n🎯 TOP 5 HIGHEST PROBABILITY EVENTS:")
print("-" * 80)

sorted_events = sorted(events, key=lambda x: x['probability'], reverse=True)[:5]

for i, event in enumerate(sorted_events, 1):
    lock_status = "🔒🔒🔒" if event.get('triple_lock') else "🔒🔒" if event.get('double_lock') else "🔒"
    quality_emoji = "✨" if event['quality'] in ['success', 'positive'] else "⚠️"
    
    print(f"\n{i}. {lock_status} {quality_emoji} {event['event_type'].upper()}")
    print(f"   House: {event['house']} | Probability: {event['probability']}% | Quality: {event['quality']}")
    print(f"   Period: {event['start_date']} to {event['end_date']}")
    print(f"   Peak: {event['peak_date']}")
    
    if event.get('authorization'):
        auth = event['authorization']
        print(f"   Authorization: {auth.get('dasha_lord', 'N/A')} dasha activating house {auth.get('activated_houses', [])}")
    
    if event.get('trigger'):
        trigger = event['trigger']
        print(f"   Trigger: {trigger.get('planet', 'N/A')} transit in house {trigger.get('house', 'N/A')}")

# Test 2: Check specific date (today)
print("\n" + "=" * 80)
print("TEST 2: CHECK TODAY'S DATE")
print("=" * 80)

today = datetime.now()
print(f"Checking date: {today.strftime('%Y-%m-%d')}")

# Check ±7 days around today
check_start = today - timedelta(days=7)
check_end = today + timedelta(days=7)

check_events = predictor.predict_events(birth_data, check_start, check_end, min_probability=50)

# Filter events overlapping with today
today_events = []
for event in check_events:
    event_start = datetime.strptime(event['start_date'], '%Y-%m-%d')
    event_end = datetime.strptime(event['end_date'], '%Y-%m-%d')
    if event_start <= today <= event_end:
        today_events.append(event)

print(f"\n✓ Found {len(today_events)} events active today")

if today_events:
    success_count = sum(1 for e in today_events if e['quality'] in ['success', 'positive'])
    struggle_count = sum(1 for e in today_events if e['quality'] in ['struggle', 'challenging'])
    
    if success_count > struggle_count:
        print(f"🌟 Today is AUSPICIOUS with {success_count} positive influences")
    elif struggle_count > success_count:
        print(f"⚠️ Today is CHALLENGING with {struggle_count} difficult influences")
    else:
        print(f"⚖️ Today has MIXED influences")
    
    print("\nActive events today:")
    for event in today_events:
        quality_emoji = "✨" if event['quality'] in ['success', 'positive'] else "⚠️"
        print(f"  {quality_emoji} {event['event_type']} (House {event['house']}) - {event['probability']}%")
else:
    print("📅 No significant planetary influences detected for today")

# Test 3: Career timeline (House 10)
print("\n" + "=" * 80)
print("TEST 3: CAREER TIMELINE (HOUSE 10) - NEXT 1 YEAR")
print("=" * 80)

career_start = datetime.now()
career_end = career_start + timedelta(days=365)

print(f"Period: {career_start.strftime('%Y-%m-%d')} to {career_end.strftime('%Y-%m-%d')}")

career_events = predictor.predict_events(birth_data, career_start, career_end, min_probability=60)
house_10_events = [e for e in career_events if e['house'] == 10]

print(f"\n✓ Found {len(house_10_events)} career-related events")

if house_10_events:
    triple_lock_career = len([e for e in house_10_events if e.get('triple_lock')])
    success_career = len([e for e in house_10_events if e['quality'] in ['success', 'positive']])
    
    print(f"\n📊 Career Summary:")
    print(f"  🔒🔒🔒 High-certainty events: {triple_lock_career}")
    print(f"  ✨ Positive events: {success_career}")
    print(f"  ⚠️ Challenging events: {len(house_10_events) - success_career}")
    
    print("\n🎯 Key Career Events:")
    for event in sorted(house_10_events, key=lambda x: x['probability'], reverse=True)[:3]:
        lock_status = "🔒🔒🔒" if event.get('triple_lock') else "🔒🔒" if event.get('double_lock') else "🔒"
        quality_emoji = "✨" if event['quality'] in ['success', 'positive'] else "⚠️"
        print(f"\n  {lock_status} {quality_emoji} {event['event_type']}")
        print(f"  Probability: {event['probability']}% | Period: {event['start_date']} to {event['end_date']}")
else:
    print("📅 No significant career events predicted in this period")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
