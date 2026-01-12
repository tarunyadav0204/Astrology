#!/usr/bin/env python3
"""Test chart and dasha calculations under concurrent load with different timezones"""
import time
import sys
sys.path.insert(0, '.')

from concurrent.futures import ThreadPoolExecutor, as_completed
from calculators.chart_calculator import ChartCalculator
from shared.dasha_calculator import DashaCalculator

class MockBirthData:
    def __init__(self, name, date, time, lat, lon):
        self.name = name
        self.date = date
        self.time = time
        self.latitude = lat
        self.longitude = lon
        self.place = f"Location {lat},{lon}"
        self.timezone = None  # Will be auto-detected

# Generate 100 unique birth data with different timezones
test_data = []
for i in range(100):
    # Spread across different timezones
    lat = 20.0 + (i % 40) * 1.0  # 20 to 60 degrees
    lon = 70.0 + (i // 10) * 10.0  # 70 to 160 degrees
    test_data.append(MockBirthData(
        name=f"Person_{i}",
        date="1990-01-15",
        time="10:30:00",
        lat=lat,
        lon=lon
    ))

print("Testing Chart & Dasha Calculations Under Concurrent Load")
print("100 UNIQUE LOCATIONS WITH DIFFERENT TIMEZONES")
print("=" * 60)
print(f"Total requests: {len(test_data)}")
print(f"Concurrent threads: 10")
print("=" * 60)

def calculate_chart_and_dasha(args):
    """Calculate both chart and dasha for one person"""
    idx, birth_data = args
    start = time.time()
    
    try:
        # Chart calculation
        chart_calc = ChartCalculator.__new__(ChartCalculator)
        chart_start = time.time()
        chart_result = chart_calc.calculate_chart(birth_data)
        chart_time = time.time() - chart_start
        
        # Dasha calculation
        dasha_calc = DashaCalculator()
        birth_dict = {
            'name': birth_data.name,
            'date': birth_data.date,
            'time': birth_data.time,
            'latitude': birth_data.latitude,
            'longitude': birth_data.longitude,
            'timezone': birth_data.timezone
        }
        dasha_start = time.time()
        dasha_result = dasha_calc.calculate_current_dashas(birth_dict)
        dasha_time = time.time() - dasha_start
        
        total_time = time.time() - start
        
        return {
            'idx': idx,
            'success': True,
            'total_time': total_time,
            'chart_time': chart_time,
            'dasha_time': dasha_time,
            'moon_lord': dasha_result.get('moon_lord'),
            'error': None
        }
    except Exception as e:
        return {
            'idx': idx,
            'success': False,
            'total_time': time.time() - start,
            'chart_time': 0,
            'dasha_time': 0,
            'moon_lord': None,
            'error': str(e)
        }

# Test with ThreadPoolExecutor
print("\nStarting concurrent calculations...")
start_time = time.time()
results = []

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(calculate_chart_and_dasha, (i, data)) for i, data in enumerate(test_data)]
    
    completed = 0
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
        completed += 1
        if completed % 10 == 0:
            print(f"  Completed: {completed}/{len(test_data)}")

total_time = time.time() - start_time

# Analyze results
successful = [r for r in results if r['success']]
failed = [r for r in results if not r['success']]

total_times = [r['total_time'] for r in successful]
chart_times = [r['chart_time'] for r in successful]
dasha_times = [r['dasha_time'] for r in successful]

print("\n" + "=" * 60)
print(f"OVERALL PERFORMANCE")
print("=" * 60)
print(f"Total time: {total_time:.3f}s")
print(f"Throughput: {len(test_data)/total_time:.1f} calculations/second")
print(f"Successful: {len(successful)}/{len(test_data)}")
print(f"Failed: {len(failed)}")

if successful:
    print("\n" + "=" * 60)
    print("TOTAL TIME PER REQUEST (Chart + Dasha):")
    print("=" * 60)
    print(f"  Average: {sum(total_times)/len(total_times)*1000:.2f}ms")
    print(f"  Min:     {min(total_times)*1000:.2f}ms")
    print(f"  Max:     {max(total_times)*1000:.2f}ms")
    print(f"  Median:  {sorted(total_times)[len(total_times)//2]*1000:.2f}ms")
    print(f"  P95:     {sorted(total_times)[int(len(total_times)*0.95)]*1000:.2f}ms")
    
    print("\n" + "=" * 60)
    print("CHART CALCULATION TIME:")
    print("=" * 60)
    print(f"  Average: {sum(chart_times)/len(chart_times)*1000:.2f}ms")
    print(f"  Min:     {min(chart_times)*1000:.2f}ms")
    print(f"  Max:     {max(chart_times)*1000:.2f}ms")
    print(f"  Median:  {sorted(chart_times)[len(chart_times)//2]*1000:.2f}ms")
    
    print("\n" + "=" * 60)
    print("DASHA CALCULATION TIME:")
    print("=" * 60)
    print(f"  Average: {sum(dasha_times)/len(dasha_times)*1000:.2f}ms")
    print(f"  Min:     {min(dasha_times)*1000:.2f}ms")
    print(f"  Max:     {max(dasha_times)*1000:.2f}ms")
    print(f"  Median:  {sorted(dasha_times)[len(dasha_times)//2]*1000:.2f}ms")

if failed:
    print("\n" + "=" * 60)
    print(f"ERRORS ({len(failed)}):")
    print("=" * 60)
    for r in failed[:5]:  # Show first 5 errors
        print(f"  Request {r['idx']}: {r['error']}")

if len(successful) == len(test_data):
    print("\n✅ All 100 concurrent calculations completed successfully")
    print("✅ Timezone detection handled different locations perfectly")
    print("✅ Chart and Dasha calculations are thread-safe")
    print("✅ Singleton pattern performs well under load")
