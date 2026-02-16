import swisseph as swe
from datetime import datetime

# Birth details
birth_date = "1980-04-02"
birth_time = "14:55"  # 2:55 PM
latitude = 29.1492
longitude = 75.7217
timezone_offset = 5.5  # IST

# Astrosage target values (in decimal degrees)
astrosage_targets = {
    'Sun': 349 + 18/60 + 44/3600,
    'Moon': 188 + 32/60 + 30/3600,
    'Mars': 122 + 28/60 + 54/3600,
    'Mercury': 321 + 32/60 + 22/3600,
    'Jupiter': 127 + 35/60 + 21/3600,
    'Venus': 35 + 5/60 + 14/3600,
    'Saturn': 148 + 40/60 + 59/3600,
    'Rahu': 123 + 30/60 + 40/3600,
}

# Calculate JD
year, month, day = 1980, 4, 2
hour = 14 + 55/60.0
utc_hour = hour - timezone_offset
jd = swe.julday(year, month, day, utc_hour)

# Test different ayanamsa values
print(f"Testing for birth: {birth_date} {birth_time} IST")
print(f"JD: {jd}\n")

# Get tropical positions first
planets = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
    'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS,
    'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE
}

tropical_positions = {}
for name, planet_id in planets.items():
    pos = swe.calc_ut(jd, planet_id)[0]
    tropical_positions[name] = pos[0]

print("Tropical positions:")
for name, pos in tropical_positions.items():
    deg = int(pos)
    min = int((pos - deg) * 60)
    sec = int(((pos - deg) * 60 - min) * 60)
    print(f"  {name}: {deg}° {min}' {sec}\"")

# Test different ayanamsa systems
ayanamsa_systems = [
    (swe.SIDM_LAHIRI, "Lahiri"),
    (swe.SIDM_KRISHNAMURTI, "KP (Krishnamurti)"),
    (swe.SIDM_RAMAN, "Raman"),
    (swe.SIDM_YUKTESHWAR, "Yukteshwar"),
]

print("\n" + "="*80)
print("Testing different Ayanamsa systems:")
print("="*80)

best_match = None
best_error = float('inf')

for sid_mode, name in ayanamsa_systems:
    swe.set_sid_mode(sid_mode)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    
    print(f"\n{name} Ayanamsa: {ayanamsa:.6f}°")
    
    total_error = 0
    for planet_name, tropical_pos in tropical_positions.items():
        if planet_name == 'Ketu':
            continue
        sidereal_pos = (tropical_pos - ayanamsa) % 360
        target = astrosage_targets[planet_name]
        error = abs(sidereal_pos - target)
        if error > 180:
            error = 360 - error
        total_error += error
        
        deg = int(sidereal_pos)
        min = int((sidereal_pos - deg) * 60)
        sec = int(((sidereal_pos - deg) * 60 - min) * 60)
        
        target_deg = int(target)
        target_min = int((target - target_deg) * 60)
        target_sec = int(((target - target_deg) * 60 - target_min) * 60)
        
        diff_arcmin = error * 60
        print(f"  {planet_name:8s}: {deg:3d}° {min:2d}' {sec:2d}\" | Target: {target_deg:3d}° {target_min:2d}' {target_sec:2d}\" | Diff: {diff_arcmin:.2f}'")
    
    avg_error = total_error / len([p for p in tropical_positions.keys() if p != 'Ketu'])
    print(f"  Average error: {avg_error * 60:.2f} arc minutes")
    
    if total_error < best_error:
        best_error = total_error
        best_match = (name, ayanamsa, sid_mode)

print("\n" + "="*80)
print(f"BEST MATCH: {best_match[0]} with ayanamsa {best_match[1]:.6f}°")
print(f"Average error: {best_error / 8 * 60:.2f} arc minutes")
print("="*80)
