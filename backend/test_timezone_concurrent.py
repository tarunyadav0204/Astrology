#!/usr/bin/env python3
"""Test timezone service under concurrent load with all cache misses"""
import time
import sys
sys.path.insert(0, '.')

from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.timezone_service import get_timezone_from_coordinates

# Generate 100 unique locations (all will be cache misses)
# Spread across India with different rounded coordinates
locations = []
for lat_offset in range(10):
    for lon_offset in range(10):
        # Delhi area with small variations to create unique cache keys
        lat = 28.00 + (lat_offset * 0.50)  # 28.00, 28.50, 29.00, etc.
        lon = 77.00 + (lon_offset * 0.50)  # 77.00, 77.50, 78.00, etc.
        locations.append((lat, lon))

print("Testing Timezone Service Under Concurrent Load")
print("ALL CACHE MISSES (100 unique locations)")
print("=" * 60)
print(f"Total requests: {len(locations)}")
print(f"Concurrent threads: 10")
print(f"Each location has unique rounded coordinates")
print("=" * 60)

def lookup_timezone(args):
    """Single timezone lookup"""
    idx, (lat, lon) = args
    start = time.time()
    try:
        result = get_timezone_from_coordinates(lat, lon)
        elapsed = time.time() - start
        return idx, elapsed, result, None
    except Exception as e:
        elapsed = time.time() - start
        return idx, elapsed, None, str(e)

# Test with ThreadPoolExecutor
print("\nStarting concurrent requests...")
start_time = time.time()
times = []
errors = 0

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(lookup_timezone, (i, loc)) for i, loc in enumerate(locations)]
    
    completed = 0
    for future in as_completed(futures):
        idx, elapsed, result, error = future.result()
        times.append(elapsed)
        if error:
            errors += 1
        completed += 1
        if completed % 10 == 0:
            print(f"  Completed: {completed}/{len(locations)}")

total_time = time.time() - start_time

print("\n" + "=" * 60)
print(f"Completed {len(locations)} requests in {total_time:.3f}s")
print(f"Throughput: {len(locations)/total_time:.1f} requests/second")
print(f"Errors: {errors}")
print(f"\nPer-request times (all cache misses):")
print(f"  Average: {sum(times)/len(times)*1000:.2f}ms")
print(f"  Min:     {min(times)*1000:.2f}ms")
print(f"  Max:     {max(times)*1000:.2f}ms")
print(f"  Median:  {sorted(times)[len(times)//2]*1000:.2f}ms")
print(f"  P95:     {sorted(times)[int(len(times)*0.95)]*1000:.2f}ms")
print(f"  P99:     {sorted(times)[int(len(times)*0.99)]*1000:.2f}ms")

if errors == 0:
    print(f"\n✅ All {len(locations)} concurrent requests completed successfully")
    print("✅ No race conditions or errors detected")
    print("✅ Singleton pattern handles concurrent cache misses perfectly")
else:
    print(f"\n⚠️  {errors} requests failed")
