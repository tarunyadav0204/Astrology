#!/usr/bin/env python3
"""Test timezone detection performance with cache misses"""
import time
import sys
sys.path.insert(0, '.')

from utils.timezone_service import get_timezone_from_coordinates, _timezone_cache

print("Testing Timezone Detection Performance")
print("=" * 60)

# Test coordinates (different locations to force cache misses)
test_locations = [
    (28.6139, 77.2090, "New Delhi, India"),
    (40.7128, -74.0060, "New York, USA"),
    (51.5074, -0.1278, "London, UK"),
    (35.6762, 139.6503, "Tokyo, Japan"),
    (-33.8688, 151.2093, "Sydney, Australia"),
    (19.0760, 72.8777, "Mumbai, India"),
    (13.0827, 80.2707, "Chennai, India"),
    (22.5726, 88.3639, "Kolkata, India"),
    (12.9716, 77.5946, "Bangalore, India"),
    (17.3850, 78.4867, "Hyderabad, India"),
]

print(f"\nInitial cache size: {len(_timezone_cache)}")
print("\nTesting with CACHE MISSES (first call for each location):")
print("-" * 60)

times_uncached = []
for lat, lon, name in test_locations:
    # Clear cache for this location to force miss
    cache_key = (round(lat, 2), round(lon, 2))
    if cache_key in _timezone_cache:
        del _timezone_cache[cache_key]
    
    start = time.time()
    result = get_timezone_from_coordinates(lat, lon)
    elapsed = time.time() - start
    times_uncached.append(elapsed)
    print(f"  {name:25s}: {elapsed*1000:6.2f}ms -> {result}")

print(f"\nCache size after first calls: {len(_timezone_cache)}")

print("\n" + "=" * 60)
print("UNCACHED (Cache Miss) Performance:")
print(f"  Average: {sum(times_uncached)/len(times_uncached)*1000:.2f}ms")
print(f"  Min:     {min(times_uncached)*1000:.2f}ms")
print(f"  Max:     {max(times_uncached)*1000:.2f}ms")

print("\n" + "=" * 60)
print("\nTesting with CACHE HITS (second call for same locations):")
print("-" * 60)

times_cached = []
for lat, lon, name in test_locations:
    start = time.time()
    result = get_timezone_from_coordinates(lat, lon)
    elapsed = time.time() - start
    times_cached.append(elapsed)
    print(f"  {name:25s}: {elapsed*1000:6.2f}ms -> {result}")

print("\n" + "=" * 60)
print("CACHED (Cache Hit) Performance:")
print(f"  Average: {sum(times_cached)/len(times_cached)*1000:.2f}ms")
print(f"  Min:     {min(times_cached)*1000:.2f}ms")
print(f"  Max:     {max(times_cached)*1000:.2f}ms")

print("\n" + "=" * 60)
print("SPEEDUP from caching:")
avg_uncached = sum(times_uncached)/len(times_uncached)*1000
avg_cached = sum(times_cached)/len(times_cached)*1000
speedup = avg_uncached / avg_cached
print(f"  {speedup:.1f}x faster with cache")
print(f"  Saves {avg_uncached - avg_cached:.2f}ms per lookup")
