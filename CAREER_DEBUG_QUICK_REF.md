# Career Analysis Debug - Quick Reference

## 🚀 Quick Start

### 1. Test Ground Truth (30 seconds)
```bash
cd /Users/tarunydv/Desktop/Code/AstrologyApp/backend
python test_career_placements.py
```
**Shows**: Actual planetary positions from calculations

### 2. Trigger Analysis (2 minutes)
1. Open mobile app
2. Go to Career Analysis
3. Click "Start Analysis"
4. Watch backend terminal

### 3. Check Validation (10 seconds)
Look for in backend logs:
- ✅ `Planetary placement validation PASSED` = Good!
- ❌ `Planetary placement validation FAILED` = AI hallucinating

## 🔍 What to Look For

### Backend Terminal Output

**Good Output**:
```
🔍 [CAREER DEBUG] PLANETARY PLACEMENTS IN CONTEXT
📊 D1 CHART PLANETS:
  Mars: House 7, Sign 6 (Libra)
  
🔍 VALIDATING PLANETARY PLACEMENTS
✅ Planetary placement validation PASSED
```

**Bad Output (Hallucination Detected)**:
```
❌ Planetary placement validation FAILED
❌ Mars house mismatch: AI claims 3rd house, actual is 7th house
```

## 🛠️ Quick Fixes

### If Validation Fails
**Problem**: AI is hallucinating placements

**Fix**: Edit `/backend/career_analysis/career_ai_router.py`

Find the `career_question` variable and add at the top:
```python
career_question = """
CRITICAL: You MUST use ONLY the planetary positions in the context.
DO NOT invent placements. Verify every planet reference.

[Rest of existing prompt...]
"""
```

### If Context is Wrong
**Problem**: Wrong data being sent to AI

**Fix**: Check `/backend/ai/career_ai_context_generator.py`

### If Mobile Shows Nothing
**Problem**: Parsing issue

**Fix**: Check `/astroroshni_mobile/src/components/Analysis/AnalysisDetailScreen.js`

## 📊 Log Locations

- **Backend**: Terminal where `python main.py` is running
- **Mobile**: React Native debugger console
- **Test Script**: Terminal output

## 🎯 Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Mars in 3rd" but should be 7th | AI hallucination | Strengthen prompt |
| No planets shown | Context not built | Check context generator |
| Wrong signs | Sign name vs number | Use sign_name field |
| D1/D10 confusion | Not labeled clearly | Separate D1 and D10 in context |

## 📝 Files to Check

1. **Backend Router**: `/backend/career_analysis/career_ai_router.py`
2. **Context Generator**: `/backend/ai/career_ai_context_generator.py`
3. **Validator**: `/backend/ai/planetary_placement_validator.py`
4. **Mobile Screen**: `/astroroshni_mobile/src/components/Analysis/AnalysisDetailScreen.js`
5. **Test Script**: `/backend/test_career_placements.py`

## 🔄 Debug Workflow

```
1. Run test_career_placements.py
   ↓
2. Note actual planetary positions
   ↓
3. Trigger analysis in mobile
   ↓
4. Check backend validation logs
   ↓
5. If FAILED → Strengthen AI prompt
   ↓
6. If PASSED → Issue is elsewhere
```

## 💡 Pro Tips

1. **Always run test script first** - establishes ground truth
2. **Check validation logs** - catches hallucinations automatically
3. **Compare three sources**: Test script, Backend logs, Mobile display
4. **Strengthen prompt gradually** - add one rule at a time
5. **Test with known data** - use birth data you can verify

## 🆘 Emergency Commands

```bash
# See all backend logs
cd /Users/tarunydv/Desktop/Code/AstrologyApp/backend
python main.py | tee career_debug.log

# Test validator standalone
cd /Users/tarunydv/Desktop/Code/AstrologyApp/backend
python ai/planetary_placement_validator.py

# Check if Swiss Ephemeris working
cd /Users/tarunydv/Desktop/Code/AstrologyApp/backend
python -c "import swisseph as swe; print(swe.version)"
```

## ✅ Success Criteria

- [ ] Test script shows planetary positions
- [ ] Backend logs match test script
- [ ] Validation passes (✅ not ❌)
- [ ] Mobile displays correct placements
- [ ] No hallucinated positions

## 📞 Need More Help?

See detailed guide: `/backend/CAREER_DEBUG_GUIDE.md`
See full summary: `/CAREER_ANALYSIS_DEBUG_SUMMARY.md`
