# Career Analysis Planetary Placement Debugging Guide

## Issue
Career analysis in mobile app (AnalysisDetailScreen) is showing wrong planetary placements.

## Root Cause Analysis

The issue could be at three levels:

### 1. **Data Generation Level** (Backend Context)
- Career context generator calculates planetary positions
- Uses Swiss Ephemeris for accurate calculations
- Generates D1 and D10 chart data

### 2. **AI Interpretation Level** (Gemini API)
- AI receives correct planetary data in context
- AI may misinterpret or hallucinate placements
- AI generates text-based analysis with planetary references

### 3. **Display Level** (Mobile App)
- Mobile app receives AI-generated text
- Displays the analysis as-is
- No validation of planetary claims

## Debugging Steps Added

### Backend Logging (career_ai_router.py)
Added comprehensive logging before sending context to AI:
```python
# Logs D1 planets with house, sign, longitude
# Logs D10 planets with house, sign
# Logs 10th house analysis
# Logs Chara Karakas including Amatyakaraka
```

### Mobile Logging (AnalysisDetailScreen.js)
Added logging to capture received analysis:
```javascript
// Logs complete parsed.data structure
// Logs planetary references in detailed_analysis answers
```

### Test Script (test_career_placements.py)
Created standalone test to verify context generation:
```bash
cd backend
python test_career_placements.py
```

## How to Debug

### Step 1: Run Test Script
```bash
cd /Users/tarunydv/Desktop/Code/AstrologyApp/backend
python test_career_placements.py
```

This will show you the ACTUAL planetary positions being calculated.

### Step 2: Trigger Career Analysis in Mobile
1. Open mobile app
2. Navigate to Career Analysis
3. Start analysis
4. Check backend logs for planetary data being sent to AI
5. Check mobile logs for analysis received

### Step 3: Compare Data
Compare three sources:
1. **Test script output** - Ground truth from calculations
2. **Backend logs** - Data sent to AI
3. **Mobile display** - What AI generated

### Step 4: Identify Discrepancy Level

#### If Test Script ≠ Backend Logs
- Issue in context generation
- Check `career_ai_context_generator.py`
- Verify chart calculations

#### If Backend Logs = Test Script, but Mobile Display ≠ Backend Logs
- Issue is AI hallucination/misinterpretation
- AI is receiving correct data but generating wrong analysis
- Solution: Improve AI prompt with stricter instructions

#### If Mobile Display shows different format
- Issue in response parsing
- Check `AnalysisDetailScreen.js` parsing logic

## Common Issues & Solutions

### Issue: AI Hallucinating Placements
**Symptom**: Backend sends "Mars in 10th house" but AI says "Mars in 3rd house"

**Solution**: Strengthen AI prompt with:
```
CRITICAL: You MUST use ONLY the planetary positions provided in the context.
DO NOT invent or assume planetary placements.
For each planet mentioned, cite the exact house and sign from the input data.
```

### Issue: Sign Names vs Numbers Confusion
**Symptom**: AI confuses sign 0 (Aries) with sign 1

**Solution**: Ensure context includes both:
- `sign`: 0 (numeric)
- `sign_name`: "Aries" (text)

AI should reference sign_name only.

### Issue: D1 vs D10 Confusion
**Symptom**: AI uses D1 placements when discussing D10 career specialization

**Solution**: Clearly label in context:
```json
{
  "d1_chart": { "planets": {...} },
  "d10_detailed": { "planets": {...} }
}
```

Prompt should specify: "For career specialization, use D10 planets, not D1"

## Verification Checklist

- [ ] Test script runs without errors
- [ ] Backend logs show correct planetary positions
- [ ] Backend logs match test script output
- [ ] Mobile receives complete analysis data
- [ ] AI-generated text references correct houses
- [ ] AI-generated text references correct signs
- [ ] AI-generated text references correct nakshatras
- [ ] No hallucinated planetary positions

## Next Steps

1. **Run test script** to establish ground truth
2. **Trigger analysis** in mobile app
3. **Collect logs** from both backend and mobile
4. **Compare** all three data sources
5. **Identify** which level has the discrepancy
6. **Fix** at the appropriate level:
   - Context generation → Fix calculator
   - AI interpretation → Fix prompt
   - Display → Fix parsing

## Files Modified

1. `/backend/career_analysis/career_ai_router.py` - Added planetary placement logging
2. `/astroroshni_mobile/src/components/Analysis/AnalysisDetailScreen.js` - Added received data logging
3. `/backend/test_career_placements.py` - Created test script

## Expected Output Format

### Backend Log Example:
```
================================================================================
🔍 [CAREER DEBUG] PLANETARY PLACEMENTS IN CONTEXT
================================================================================

📊 D1 CHART PLANETS:
  Sun: House 10, Sign 9 (Capricorn), Long 294.56°
  Moon: House 3, Sign 2 (Gemini), Long 74.23°
  Mars: House 7, Sign 6 (Libra), Long 194.12°
  ...

📊 D10 CHART PLANETS:
  Sun: House 4, Sign 3 (Cancer)
  Moon: House 11, Sign 10 (Aquarius)
  ...

🏠 10TH HOUSE ANALYSIS:
  Sign: Capricorn
  Lord: Saturn
  Planets in 10th: ['Sun', 'Mercury']

👑 CHARA KARAKAS:
  Amatyakaraka: Mars
  ...
```

### Mobile Log Example:
```
📱 [MOBILE DEBUG] CAREER ANALYSIS PLANETARY DATA
================================================================================

📊 Question 1: What is my true professional purpose?
   Answer snippet: Your Amatyakaraka Mars is placed in the 7th house in Libra sign...

📊 Question 3: What specific industry is best for me?
   Answer snippet: With 10th lord Saturn in 4th house and Sun in 10th house...
```

## Conclusion

The debugging infrastructure is now in place. Run the test script and compare outputs to identify where the planetary placement discrepancy occurs. The most likely cause is AI hallucination, which can be fixed by strengthening the prompt instructions.
