#!/usr/bin/env python3
"""Test chart calculation performance"""
import time
import sys
sys.path.insert(0, '.')

from calculators.chart_calculator import ChartCalculator

class MockBirthData:
    def __init__(self):
        self.name = 'Test User'
        self.date = '1979-08-17'
        self.time = '01:40:00'
        self.latitude = 28.6138954
        self.longitude = 77.2090057
        self.place = 'New Delhi'
        self.timezone = 5.5

print("Testing Chart Calculation Performance")
print("=" * 60)

# Import time
start = time.time()
birth_data = MockBirthData()
print(f"Setup time: {(time.time()-start)*1000:.2f}ms\n")

# Create calculator (no chart_data needed for calculate_chart method)
calc = ChartCalculator.__new__(ChartCalculator)

# Warm up call
print("Warming up...")
calc.calculate_chart(birth_data)

# Test 10 times
print("\nRunning 10 test calculations:")
times = []
for i in range(10):
    start = time.time()
    result = calc.calculate_chart(birth_data)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"  Run {i+1:2d}: {elapsed*1000:6.2f}ms")

print("\n" + "=" * 60)
print(f"Average: {sum(times)/len(times)*1000:.2f}ms")
print(f"Min:     {min(times)*1000:.2f}ms")
print(f"Max:     {max(times)*1000:.2f}ms")
print(f"Median:  {sorted(times)[len(times)//2]*1000:.2f}ms")
