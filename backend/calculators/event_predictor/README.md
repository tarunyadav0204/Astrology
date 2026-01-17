# Parashari Event Predictor

**World-class event prediction engine with zero ghost predictions.**

## Overview

The Parashari Event Predictor implements a revolutionary **3-Layer Gate System** that eliminates false predictions by ensuring every predicted event has proper astrological authorization.

### The Problem with Traditional Predictors

Traditional transit-based predictors suffer from "ghost predictions":
- Transit looks good (Jupiter aspects 7th house)
- Dasha is running (Jupiter Mahadasha)
- **BUT**: Jupiter rules 3rd/6th houses, NOT 7th house
- **Result**: False marriage prediction (ghost)

### Our Solution: The Gate System

```
Layer 1: DASHA GATE (Authorization)
   ↓
   Does dasha authorize this house?
   - House lord in dasha?
   - Planets in house in dasha?
   - Planets aspecting house in dasha?
   - Natural karaka in dasha?
   ↓
   Gate Opens: Score ≥ 40 points
   ↓
Layer 2: TRANSIT TRIGGER (Activation)
   ↓
   Does transit activate authorized house?
   - Conjunction or aspect to house
   - Transit planet strength check
   - Ashtakavarga validation
   - Nakshatra Return (Nadi technique)
   ↓
Layer 3: STRENGTH VALIDATION (Quality)
   ↓
   Calculate probability (0-100%)
   - Shadbala strength
   - Planetary dignity
   - Functional benefic status
   - Age appropriateness
   - Natal promise validation
   ↓
   EVENT PREDICTED ✅
```

## Architecture

```
event_predictor/
├── __init__.py                    # Module exports
├── gate_validator.py              # Layer 1: Dasha-House Gate
├── parashari_predictor.py         # Main prediction engine
├── demo.py                        # Usage examples
└── config/
    └── event_rules.py             # Event types & house significations
```

## Key Components

### 1. DashaHouseGate (gate_validator.py)

**Purpose**: Validates if dasha authorizes house activation

**Authorization Paths**:
1. Planet is house lord
2. Planet sits in house
3. Planet aspects house
4. Planet is natural karaka
5. Planet is dispositor of house lord

**Scoring** (3 levels only - birth time accuracy):
- Mahadasha: 100 points
- Antardasha: 70 points
- Pratyantardasha: 40 points

**Note**: Sookshma and Prana excluded due to birth time sensitivity

**Gate Opens**: Score ≥ 40 (minimum PD level)

```python
from calculators.event_predictor import DashaHouseGate

gate = DashaHouseGate(chart_data)
result = gate.check_authorization(house=7, dasha_stack=current_dasha)

if result['authorized']:
    print(f"House 7 authorized with score {result['score']}")
    print(f"Reasons: {result['reasons']}")
```

### 2. ParashariEventPredictor (parashari_predictor.py)

**Purpose**: Main prediction engine orchestrating all 3 layers

**Features**:
- No ghost predictions (gate-validated)
- Probability scoring (0-100%)
- Age-aware predictions (Desha Kala Patra)
- Natal promise validation
- Multi-factor strength assessment

```python
from calculators.event_predictor import ParashariEventPredictor

predictor = ParashariEventPredictor(
    chart_calculator=chart_calc,
    transit_calculator=transit_calc,
    dasha_calculator=dasha_calc,
    shadbala_calculator=shadbala_calc,
    ashtakavarga_calculator=ashtakavarga_calc,
    dignities_calculator=dignities_calc,
    functional_benefics_calculator=func_benefics_calc
)

events = predictor.predict_events(
    birth_data=birth_data,
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=730),
    min_probability=60
)
```

### 3. Event Rules Configuration (config/event_rules.py)

**Defines**:
- House significations
- Event type mappings
- Age-based priorities (Desha Kala Patra)

**Event Types**:
- Marriage, Childbirth, Career Promotion, Job Change
- Property Acquisition, Wealth Gain, Education Success
- Foreign Travel, Health Issues, Litigation
- Spiritual Awakening, Business Success

## Usage

### Basic Usage

```python
from datetime import datetime, timedelta
from calculators.event_predictor import ParashariEventPredictor

# Initialize with all calculators
predictor = ParashariEventPredictor(...)

# Predict events
events = predictor.predict_events(
    birth_data={
        'date': '1990-05-15',
        'time': '14:30',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'timezone': '+05:30'
    },
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=730),
    min_probability=60
)

# Process results
for event in events:
    print(f"{event['event_type']}: {event['probability']}%")
    print(f"Date: {event['start_date']} to {event['end_date']}")
    print(f"Authorization: {event['authorization']['dasha']}")
```

### Check Authorized Houses

```python
from calculators.event_predictor import DashaHouseGate

gate = DashaHouseGate(chart_data)
authorized = gate.get_authorized_houses(dasha_stack, min_score=40)

for auth in authorized:
    print(f"House {auth['house']}: Score {auth['score']}")
    print(f"Reasons: {auth['reasons']}")
```

## Output Format

```python
{
    'event_type': 'career_promotion',
    'house': 10,
    'probability': 85,
    'nature': 'positive',
    'start_date': '2025-03-15',
    'end_date': '2025-04-10',
    'peak_date': datetime(2025, 3, 28),
    'authorization': {
        'dasha': 'Jupiter MD - Venus AD',
        'score': 170,
        'reasons': [
            'Jupiter is lord of H10 (MAHADASHA)',
            'Venus aspects H10 (ANTARDASHA)'
        ]
    },
    'trigger': {
        'planet': 'Saturn',
        'type': 'conjunction',
        'house': 10
    },
    'strength_factors': {
        'shadbala': 20,
        'ashtakavarga': 15,
        'dignity': 10,
        'functional': 10,
        'age_appropriate': 10,
        'natal_promise': 15
    }
}
```

## Probability Scoring

**Total Score = 100 points maximum**

| Factor | Points | Description |
|--------|--------|-------------|
| Dasha Authorization | 40 | Gate score (capped at 40) |
| Shadbala Strength | 20 | Planetary strength |
| Ashtakavarga | 15 | House strength |
| Planetary Dignity | 10 | Exaltation/debilitation |
| Functional Status | 10 | Benefic/malefic |
| Age Appropriateness | 10 | Desha Kala Patra |
| Natal Promise | 15 | Chart supports event |

**Interpretation**:
- 80-100%: Highly likely
- 60-79%: Probable
- 40-59%: Possible
- <40%: Filtered out

## Age-Based Priorities (Desha Kala Patra)

### Student (Age 0-22)
- **Priority**: Education, exams, skills
- **Emphasis**: Houses 4, 5, 9, 11
- **Suppressed**: Marriage, childbirth, career

### Young Professional (Age 23-35)
- **Priority**: Career, marriage, property
- **Emphasis**: Houses 7, 10, 11, 4
- **Suppressed**: None

### Established (Age 36-55)
- **Priority**: Wealth, business, children
- **Emphasis**: Houses 2, 5, 10, 11
- **Suppressed**: Education

### Senior (Age 56+)
- **Priority**: Spirituality, health, travel
- **Emphasis**: Houses 9, 12, 1, 8
- **Suppressed**: Childbirth, education, career

## Integration with Existing Calculators

**Required Calculators**:
1. `ChartCalculator` - Birth chart
2. `RealTransitCalculator` - Current transits
3. `DashaCalculator` - Vimshottari dasha
4. `ShadbalaCalculator` - Planetary strength
5. `AshtakavargaCalculator` - House strength
6. `PlanetaryDignitiesCalculator` - Dignity status
7. `FunctionalBeneficsCalculator` - Benefic/malefic

All calculators already exist in the codebase.

## Future Enhancements

### Phase 2: Jaimini System
- Chara dasha integration
- Jaimini aspects
- Karakamsa analysis

### Phase 3: Nadi System
- Nakshatra-based timing
- Sub-lord analysis
- KP system integration

## Testing

Run the demo:
```bash
cd backend/calculators/event_predictor
python demo.py
```

## Key Innovations

1. **Zero Ghost Predictions**: Gate system ensures authorization
2. **Multi-Factor Scoring**: 7 different strength indicators
3. **Age-Aware**: Desha Kala Patra logic
4. **Natal Promise Validation**: Only predicts what chart supports
5. **Exact Timing**: Day-level precision with transit tracking
6. **Nakshatra Return Detection**: Nadi technique for powerful triggers

## Comparison with Old System

| Feature | Old System | Parashari Predictor |
|---------|-----------|---------------------|
| Ghost Predictions | ✗ Yes | ✅ No |
| Dasha Authorization | ✗ Weak | ✅ Strong (Gate) |
| Probability Scoring | ✗ Binary | ✅ 0-100% |
| Age Awareness | ✗ No | ✅ Yes |
| Strength Validation | ✗ Partial | ✅ Comprehensive |
| Natal Promise Check | ✗ No | ✅ Yes |

---

**Built with classical Parashari principles and modern engineering.**
