import swisseph as swe

# Birth details
jd = 2444331.892361111

# Astrosage targets
targets = {
    'Sun': 349 + 18/60 + 44/3600,
    'Moon': 188 + 32/60 + 30/3600,
    'Mars': 122 + 28/60 + 54/3600,
    'Mercury': 321 + 32/60 + 22/3600,
    'Jupiter': 127 + 35/60 + 21/3600,
    'Venus': 35 + 5/60 + 14/3600,
    'Saturn': 148 + 40/60 + 59/3600,
    'Rahu': 123 + 30/60 + 40/3600,
}

# Get tropical positions
planets = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 
           'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE}

tropical = {}
for name, pid in planets.items():
    tropical[name] = swe.calc_ut(jd, pid)[0][0]

# Test ayanamsa offsets around KP value
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
base_ayanamsa = swe.get_ayanamsa_ut(jd)

print(f"Base KP Ayanamsa: {base_ayanamsa:.6f}°\n")
print("Testing offsets (in arc seconds):")
print("="*80)

best_offset = 0
best_error = float('inf')

for offset_arcsec in range(-60, 61, 1):
    offset_deg = offset_arcsec / 3600.0
    test_ayanamsa = base_ayanamsa + offset_deg
    
    total_error = 0
    for name, trop_pos in tropical.items():
        sid_pos = (trop_pos - test_ayanamsa) % 360
        target = targets[name]
        error = abs(sid_pos - target)
        if error > 180:
            error = 360 - error
        total_error += error
    
    avg_error_arcsec = (total_error / 8) * 3600
    
    if total_error < best_error:
        best_error = total_error
        best_offset = offset_arcsec
        
    if offset_arcsec % 10 == 0:
        print(f"Offset: {offset_arcsec:+4d}\" | Ayanamsa: {test_ayanamsa:.6f}° | Avg Error: {avg_error_arcsec:.2f}\"")

print("\n" + "="*80)
print(f"BEST OFFSET: {best_offset}\" ({best_offset/3600:.6f}°)")
print(f"BEST AYANAMSA: {base_ayanamsa + best_offset/3600:.6f}°")
print(f"Average error: {(best_error / 8) * 3600:.2f} arc seconds")
print("="*80)

# Show final positions with best offset
print("\nFinal positions with best offset:")
test_ayanamsa = base_ayanamsa + best_offset/3600
for name, trop_pos in tropical.items():
    sid_pos = (trop_pos - test_ayanamsa) % 360
    target = targets[name]
    
    deg = int(sid_pos)
    min = int((sid_pos - deg) * 60)
    sec = int(((sid_pos - deg) * 60 - min) * 60)
    
    t_deg = int(target)
    t_min = int((target - t_deg) * 60)
    t_sec = int(((target - t_deg) * 60 - t_min) * 60)
    
    diff = abs(sid_pos - target) * 3600
    print(f"  {name:8s}: {deg:3d}° {min:2d}' {sec:2d}\" | Target: {t_deg:3d}° {t_min:2d}' {t_sec:2d}\" | Diff: {diff:.1f}\"")
