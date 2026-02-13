# Timeline Calibration - Complete Flow Diagram

## Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER OPENS CHAT SCREEN                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: useEffect triggers on birthData.id change            │
│  → fetchCalibrationEvent()                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  API Call: GET /api/chat/scan-timeline?birth_chart_id=123      │
│  Headers: Authorization: Bearer {token}                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: chat_routes.py → scan_timeline()                      │
│  1. Fetch birth data from database                              │
│  2. Decrypt if encrypted                                        │
│  3. Initialize LifeEventScanner                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LifeEventScanner: scan_timeline()                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ FOR each year from age 18 to current age:                │ │
│  │   1. Get transits for that year (Saturn, Jupiter)        │ │
│  │   2. Calculate dashas for mid-year                        │ │
│  │   3. Check Marriage Lock:                                 │ │
│  │      - Dasha lord connected to 7th/Venus/Rahu? +1.5      │ │
│  │      - Saturn aspecting 7th house? +1.0                   │ │
│  │      - Jupiter aspecting 7th house? +1.0                  │ │
│  │   4. Check Career Lock:                                   │ │
│  │      - Dasha lord connected to 10th/Saturn/Sun? +1.5     │ │
│  │      - Saturn aspecting 10th house? +1.0                  │ │
│  │      - Jupiter aspecting 10th house? +1.0                 │ │
│  │   5. If score >= 3.0, add to events list                 │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: Filter & Return                                       │
│  1. Filter for HIGH confidence only (score >= 4.0)              │
│  2. Return top 1 event                                          │
│  Response: {"events": [{year, age, type, label, ...}]}         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: Receive Response                                     │
│  if (data.events.length > 0) {                                  │
│    setCalibrationEvent(data.events[0])                          │
│  }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  UI: Render CalibrationCard                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  🔮 TIMELINE CALIBRATION                                  │ │
│  │  ─────────────────────────────────────────────────────────│ │
│  │                                                            │ │
│  │  📅 2012 (Age 28)                                         │ │
│  │  💍 Major Relationship Milestone                          │ │
│  │  ⭐ Confidence: High                                       │ │
│  │                                                            │ │
│  │  Activated by Venus Dasha and Double Transit on 7th House │ │
│  │                                                            │ │
│  │  ┌─────────┐  ┌─────────┐                                │ │
│  │  │ ✓ YES   │  │ ✗ NO    │                                │ │
│  │  └─────────┘  └─────────┘                                │ │
│  │                                                            │ │
│  │  Did you experience this event that year?                 │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ┌────┴────┐
                    │         │
              ┌─────▼─────┐ ┌─▼──────┐
              │  YES      │ │  NO    │
              └─────┬─────┘ └─┬──────┘
                    │         │
                    ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│  API Call: POST /api/chat/verify-calibration                   │
│  Body: {                                                        │
│    birth_chart_id: 123,                                         │
│    event_year: 2012,                                            │
│    verified: true/false                                         │
│  }                                                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: Update Database                                       │
│  UPDATE birth_charts                                            │
│  SET is_rectified = 1, calibration_year = 2012                 │
│  WHERE id = 123                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: Update UI                                            │
│  if (verified) {                                                │
│    - Show success alert: "✅ Chart calibrated!"                │
│    - Mark event as verified                                     │
│    - Hide card with animation                                   │
│  } else {                                                        │
│    - Hide card immediately                                      │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Example

### Request
```http
GET /api/chat/scan-timeline?birth_chart_id=123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response
```json
{
  "events": [
    {
      "year": 2012,
      "age": 28,
      "type": "relationship",
      "label": "Major Relationship Milestone",
      "confidence": "High",
      "reason": "Activated by Venus Dasha and Double Transit on 7th House"
    }
  ]
}
```

### Verification Request
```http
POST /api/chat/verify-calibration
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "birth_chart_id": 123,
  "event_year": 2012,
  "verified": true
}
```

### Verification Response
```json
{
  "success": true
}
```

---

## State Management

### Frontend State
```javascript
// Initial state
calibrationEvent: null

// After fetch
calibrationEvent: {
  year: 2012,
  age: 28,
  type: "relationship",
  label: "Major Relationship Milestone",
  confidence: "High",
  reason: "Activated by Venus Dasha and Double Transit on 7th House"
}

// After verification
calibrationEvent: {
  ...previous,
  verified: true  // Card hidden
}
```

### Database State
```sql
-- Before verification
birth_charts:
  id: 123
  name: "John Doe"
  is_rectified: 0
  calibration_year: NULL

-- After verification
birth_charts:
  id: 123
  name: "John Doe"
  is_rectified: 1
  calibration_year: 2012
```

---

## Error Handling

### No Events Found
```json
{
  "events": []
}
```
→ Frontend: Don't show card, continue normally

### API Error
```javascript
catch (error) {
  console.log('No calibration event available');
  // Silent failure - don't interrupt user experience
}
```

### Database Error
```python
except Exception as e:
    print(f"❌ Timeline scan error: {e}")
    return {"events": []}
```

---

## Performance Metrics

### Backend Processing Time
- Database query: ~10ms
- Chart calculation: ~50ms
- Dasha calculation per year: ~20ms
- Total for 30 years: ~600-800ms

### Frontend Rendering
- API call: ~800ms
- Card render: <16ms (single frame)
- Total user-perceived delay: <1 second

### Cost Analysis
- **Gemini tokens**: 0 (no LLM used)
- **Database queries**: 2 (fetch + update)
- **Computation**: Pure Python (free)
- **Total cost per user**: $0.00

---

## Success Metrics

### User Engagement
- **Card Display Rate**: % of users who see the card
- **Verification Rate**: % of users who click YES
- **Rejection Rate**: % of users who click NO
- **Ignore Rate**: % of users who dismiss without action

### Accuracy Metrics
- **True Positive**: User confirms event happened
- **False Positive**: User rejects event
- **Confidence Calibration**: High confidence events should have >70% verification rate

### Business Impact
- **Credibility Boost**: Users who verify are more likely to trust future predictions
- **Engagement Increase**: Verified users ask more questions
- **Retention**: Verified users have higher 7-day retention

---

## A/B Testing Ideas

### Variant A: Silent Scan (Current)
- Card appears automatically on chat load
- No user action required to trigger

### Variant B: Explicit Trigger
- Show "Verify Chart Accuracy" button
- User clicks to see calibration event

### Variant C: Onboarding Flow
- Show during first-time user setup
- Before first chat question

### Metrics to Compare
- Verification rate
- User engagement
- Time to first question
- 7-day retention
