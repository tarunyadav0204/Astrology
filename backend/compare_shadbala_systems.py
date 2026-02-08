#!/usr/bin/env python3
"""
Compare different Shadbala systems and scales
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SHADBALA SYSTEMS COMPARISON                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

There are MULTIPLE Shadbala calculation systems. Different software may use
different methods, leading to different values.

┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. PARASHARA SHADBALA (BPHS) - What We Implement                            │
└──────────────────────────────────────────────────────────────────────────────┘

Scale: 0-10 rupas (1 rupa = 60 points)
Components: 6 (Sthana, Dig, Kala, Chesta, Naisargika, Drik)
Source: Brihat Parashara Hora Shastra Chapters 27-28

Example Sun values:
  Strong Sun: 6-8 rupas
  Average Sun: 4-6 rupas  
  Weak Sun: 2-4 rupas

┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. PERCENTAGE SCALE (Some Modern Software)                                  │
└──────────────────────────────────────────────────────────────────────────────┘

Scale: 0-100%
Conversion: (rupas / 10) × 100

Example:
  Our 6.9 rupas = 69%
  If they show "2" = 20% = 2 rupas in our system ✅

This might be your case!

┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. VIMSOPAKA BALA (Divisional Chart Strength)                               │
└──────────────────────────────────────────────────────────────────────────────┘

Scale: 0-20 shashtiamsas
Different calculation: Based on divisional chart placements only
NOT the same as Shadbala!

Some software labels this as "Shadbala" incorrectly.

┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. SIMPLIFIED SHADBALA (Some Apps)                                          │
└──────────────────────────────────────────────────────────────────────────────┘

Scale: 0-5 or 0-10 (simplified)
Components: Fewer than 6, simplified calculations
Used by: Some mobile apps, simplified calculators

Example:
  Only uses: Exaltation + House position + Aspects
  Ignores: Kala Bala, Chesta Bala complexity

┌──────────────────────────────────────────────────────────────────────────────┐
│ 5. DIFFERENT AYANAMSA                                                        │
└──────────────────────────────────────────────────────────────────────────────┘

We use: Lahiri Ayanamsa (Indian Government standard)
Others might use:
  - Raman Ayanamsa
  - KP Ayanamsa  
  - Tropical (Western)

Different Ayanamsa = Different planetary positions = Different Shadbala

Difference: Can be 0.5-2 rupas different!

┌──────────────────────────────────────────────────────────────────────────────┐
│ HOW TO IDENTIFY WHICH SYSTEM THEY USE                                       │
└──────────────────────────────────────────────────────────────────────────────┘

Check their software for:

1. Scale indicator:
   - "0-10 rupas" → Same as us
   - "0-100%" → Divide their value by 10 to compare
   - "0-20 shashtiamsas" → Different system (Vimsopaka)

2. Component count:
   - Shows 6 components → Parashara Shadbala (same as us)
   - Shows fewer → Simplified system
   - Shows divisional charts → Vimsopaka Bala

3. Ayanamsa setting:
   - Check if they use Lahiri (same as us)
   - If using different Ayanamsa, values will differ

┌──────────────────────────────────────────────────────────────────────────────┐
│ CONVERSION TABLE                                                             │
└──────────────────────────────────────────────────────────────────────────────┘

If they show "2" and we show "6.9":

Possibility 1: They use 0-10 scale (Parashara)
  → Their Sun is WEAK (2 rupas)
  → Our Sun is STRONG (6.9 rupas)
  → DIFFERENT CALCULATIONS or DIFFERENT CHART DATA

Possibility 2: They use percentage scale
  → Their 2% = 0.2 rupas (extremely weak)
  → Our 6.9 rupas = 69%
  → They might be showing a DIFFERENT metric

Possibility 3: They use 0-5 simplified scale
  → Their 2/5 = 40% = 4 rupas equivalent
  → Our 6.9 rupas = 69%
  → Still different, but closer

┌──────────────────────────────────────────────────────────────────────────────┐
│ DEBUGGING STEPS                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

1. Check their software name and version
2. Look for "Shadbala" vs "Vimsopaka" vs "Strength"
3. Check if they show 6 components or fewer
4. Verify they use same Ayanamsa (Lahiri)
5. Compare planetary POSITIONS first (longitude, sign)
   - If positions differ → Different Ayanamsa
   - If positions same → Different calculation method

6. Check their scale:
   - Look for "rupas", "%", "points", "shashtiamsas"

┌──────────────────────────────────────────────────────────────────────────────┐
│ MOST LIKELY CAUSE                                                            │
└──────────────────────────────────────────────────────────────────────────────┘

If reputable software (Jagannatha Hora, Parashara's Light) shows 2 rupas
and we show 6.9 rupas for the SAME chart:

→ They might be showing VIMSOPAKA BALA (divisional strength)
→ Or using DIFFERENT AYANAMSA
→ Or showing a DIFFERENT planet's Shadbala

NEXT STEP: Share your birth details and the software name so we can verify!

╚══════════════════════════════════════════════════════════════════════════════╝
""")
