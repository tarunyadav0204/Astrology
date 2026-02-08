#!/usr/bin/env python3
"""
Quick verification script to check Shadbala values match between backend and mobile app.
Run this to get expected values for your birth chart.
"""

from calculators.classical_shadbala import calculate_classical_shadbala

# Test birth data (same as integration test)
birth_data = {
    'date': '1990-01-15',
    'time': '10:30',
    'timezone': 'UTC+5.5',
    'latitude': 28.6139,
    'longitude': 77.2090
}

# Test chart data
chart_data = {
    'planets': {
        'Sun': {'longitude': 285.5, 'sign': 9, 'degree': 15.5, 'house': 10},
        'Moon': {'longitude': 45.2, 'sign': 1, 'degree': 15.2, 'house': 2},
        'Mars': {'longitude': 315.8, 'sign': 10, 'degree': 15.8, 'house': 11},
        'Mercury': {'longitude': 275.3, 'sign': 9, 'degree': 5.3, 'house': 10},
        'Jupiter': {'longitude': 95.7, 'sign': 3, 'degree': 5.7, 'house': 4},
        'Venus': {'longitude': 255.4, 'sign': 8, 'degree': 15.4, 'house': 9},
        'Saturn': {'longitude': 285.9, 'sign': 9, 'degree': 15.9, 'house': 10}
    },
    'ascendant': 30.0
}

print("\n" + "="*80)
print("SHADBALA VERIFICATION - Expected Values")
print("="*80)

results = calculate_classical_shadbala(birth_data, chart_data)

print("\n📊 PLANET STRENGTHS (sorted by strength):\n")
sorted_planets = sorted(results.items(), key=lambda x: x[1]['total_rupas'], reverse=True)

for planet, data in sorted_planets:
    print(f"  {planet:8} → {data['total_rupas']:5.2f} rupas | {data['total_points']:6.1f} points | {data['grade']}")

print("\n" + "="*80)
print("DETAILED BREAKDOWN FOR SUN:")
print("="*80)

sun_data = results['Sun']
print(f"\n🌟 Total Strength: {sun_data['total_rupas']:.2f} rupas ({sun_data['total_points']:.1f} points)")
print(f"   Grade: {sun_data['grade']}\n")

print("📋 Six Components:")
for component, value in sun_data['components'].items():
    print(f"   • {component:20} : {value:6.2f}")

if 'detailed_breakdown' in sun_data:
    print("\n🔍 Sthana Bala Details:")
    for key, value in sun_data['detailed_breakdown']['sthana_components'].items():
        print(f"   • {key:25} : {value:6.2f}")
    
    print("\n⏰ Kala Bala Details:")
    for key, value in sun_data['detailed_breakdown']['kala_components'].items():
        print(f"   • {key:25} : {value:6.2f}")

print("\n" + "="*80)
print("HOW TO VERIFY IN MOBILE APP:")
print("="*80)
print("""
1. Open AstroRoshni mobile app
2. Navigate to: Home → Menu → Shadbala
3. Check if the values match above
4. Verify all 7 planets appear (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn)
5. Verify NO other points appear (no Rahu, Ketu, Indu Lagna, etc.)

✅ If values match → Integration is correct
❌ If values differ → Check API response or calculation
""")

print("="*80)
print("\n💡 TIP: To test with YOUR birth data, edit this script and replace")
print("   birth_data and chart_data with your actual values.\n")
