# House Calculation Test Checklist

## What to Test in the UI

### 1. **Lord Positional Strength Logic**
**Test Case**: Find a house where the lord is in a Trikona (1st, 5th, 9th) or Kendra (1st, 4th, 7th, 10th)
- **Expected**: Should show "Uttama" grade even if dignity is neutral
- **Before Fix**: Would show "Madhyama" 
- **Look For**: "Sun is neutral (dignity: Madhyama) and placed in 9th house (position: Uttama)" → Grade should be **Uttama**

### 2. **Rahu/Ketu Handling**
**Test Case**: Find houses with Rahu or Ketu as residents
- **Expected**: Should show dignity + house assessment, not "0.0 rupas"
- **Before Fix**: "Rahu (weak: 0.0 rupas)"
- **After Fix**: "Rahu (strong: neutral in 6th house)" or similar
- **Look For**: No more "0.0 rupas" for shadow planets

### 3. **House Type Classification**
**Test Case**: Check 2nd and 7th houses (Maraka houses)
- **Expected**: Should show "Maraka house - death-dealing, requires caution"
- **Before Fix**: "Regular house" despite being Maraka
- **Look For**: Proper primary type identification

### 4. **Aspectual Strength for Shadow Planets**
**Test Case**: Find aspects from Rahu/Ketu
- **Expected**: "Rahu (malefic shadow planet)" instead of "Rahu (weak, 0.0 rupas)"
- **Look For**: Shadow planets treated as strong aspecters

## Quick Test Method

1. **Open Health Analysis Tab**
2. **Expand "House Health Analysis" section**
3. **Click on any house strength score (the number with 🔍)**
4. **Check the detailed breakdown for these patterns:**

### ✅ Good Signs:
- Lord in Trikona/Kendra shows "Uttama" grade
- Rahu/Ketu show dignity+house assessment (no 0.0 rupas)
- Maraka houses properly identified
- Shadow planet aspects show as "shadow planet" not "0.0 rupas"

### ❌ Issues to Report:
- Strong lord in good house still shows "Madhyama"
- Any "0.0 rupas" for Rahu/Ketu
- "Regular house" for 2nd/7th houses
- Inconsistent reasoning vs grade

## Sample Good Output:
```
Lord Positional Strength: Uttama
Reasoning: Sun is neutral (dignity: Madhyama) and placed in 9th house (position: Uttama)

Resident Planets Strength: Adhama  
Reasoning: Resident planets: Mars (weak: 2.5 rupas), Rahu (moderate: neutral in 6th house). Strong: 0, Weak: 1

House Type Strength: Madhyama
Reasoning: Maraka house - death-dealing, requires caution. Primary type: Maraka
```

## What to Share:
If you see issues, share:
1. Which house number
2. The specific factor that looks wrong
3. The reasoning text shown
4. What you expected vs what you got