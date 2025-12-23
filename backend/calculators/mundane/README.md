# Mundane Astrology Module

Self-contained module for analyzing macro events: Stock Markets, Nations, Politics, Weather, and Economic trends.

## Conceptual Shift

- **Target**: Countries, Corporations, Time Periods (not individuals)
- **Scope**: Multi-century eras (not 120-year lifespans)
- **Planets**: Includes Uranus, Neptune, Pluto for generational shifts

## Core Calculators

### 1. OuterPlanetCalculator
**Purpose**: Calculate positions of Uranus, Neptune, and Pluto (Era Markers)

**Usage**:
```python
from calculators.mundane.outer_planet_calculator import OuterPlanetCalculator
from datetime import datetime

calc = OuterPlanetCalculator()
planets = calc.calculate_outer_planets(datetime.now(), 28.6139, 77.2090)
# Returns: {Uranus: {...}, Neptune: {...}, Pluto: {...}}
```

### 2. IngressCalculator
**Purpose**: Calculate exact moments Sun enters Cardinal Signs (Aries, Cancer, Libra, Capricorn)

**Key Chart**: Aries Ingress = "Birth Chart of the World" for that year

**Usage**:
```python
from calculators.mundane.ingress_calculator import IngressCalculator

calc = IngressCalculator()
ingresses = calc.calculate_yearly_ingresses(2025, 28.6139, 77.2090)
# Returns: Aries, Cancer, Libra, Capricorn ingress moments + Aries chart
```

### 3. LunationCalculator
**Purpose**: Calculate exact New Moons and Full Moons for monthly forecasting

**Logic**: Syzygy search for Moon-Sun conjunction (0°) or opposition (180°)

**Usage**:
```python
from calculators.mundane.lunation_calculator import LunationCalculator
from datetime import datetime

calc = LunationCalculator()
lunations = calc.calculate_lunations(
    datetime(2025, 1, 1), 
    datetime(2025, 12, 31),
    28.6139, 77.2090
)
# Returns: List of New Moon and Full Moon charts with validity periods
```

### 4. GeodeticCalculator
**Purpose**: Map Zodiacal degrees to terrestrial locations (Koorma Chakra)

**Concept**: 27 Nakshatras mapped to geographic directions

**Usage**:
```python
from calculators.mundane.geodetic_calculator import GeodeticCalculator

calc = GeodeticCalculator()
impact = calc.analyze_planetary_impact(
    {'name': 'Saturn', 'nakshatra': {'name': 'Rohini'}},
    country='India'
)
# Returns: Affected regions and impact type
```

### 5. MundaneYogaCalculator
**Purpose**: Detect specialized yogas for war, famine, inflation, revolution

**Key Yogas**:
- **Sanghatta Yoga**: Mars-Saturn conjunction → War/Conflict
- **Durbhiksha Yoga**: Afflicted Moon-Jupiter → Famine/Scarcity
- **Mahargha Yoga**: Venus-Rahu in 2nd/11th → Inflation
- **Parivartan Yoga**: Uranus-Pluto hard aspect → Revolution

**Usage**:
```python
from calculators.mundane.mundane_yoga_calculator import MundaneYogaCalculator

calc = MundaneYogaCalculator()
analysis = calc.analyze_chart(chart_data)
# Returns: Detected yogas, commodity impacts, overall assessment
```

## Integration Logic

**Example Query**: "Will the market crash in October?"

**Step 1**: Check Yearly Aries Ingress chart → Is it malefic?
**Step 2**: Cast October New Moon chart → Does Mars/Saturn afflict 2nd House (Wealth)?
**Step 3**: Check Sarvatobhadra Chakra → Are malefics piercing financial nakshatras?

## Data Flow

```
User Query → Intent Router → Mundane Context Builder
    ↓
1. Calculate Aries Ingress (Yearly baseline)
2. Calculate relevant Lunations (Monthly triggers)
3. Add Outer Planets (Era context)
4. Check Mundane Yogas (Event indicators)
5. Map to Geography (Regional impact)
    ↓
Gemini Analysis → Specific Predictions
```

## Future Enhancements

- Eclipse calculator (Solar/Lunar)
- Planetary cycles (Jupiter-Saturn conjunctions)
- Ashtakavarga for nations
- Historical event correlation database
