# Birth Chart Creation API Flow

## Frontend (Web)

**File:** `frontend/src/components/BirthForm/BirthForm.js`

**API Calls:**
1. `apiService.calculateChart(birthData)` - Full chart with storage
2. `apiService.calculateChartOnly(birthData)` - Chart without storage

**Implementation:** `frontend/src/services/apiService.js`
```javascript
calculateChart: async (birthData, nodeType = 'mean') => {
  // Remove timezone field to let backend calculate it from coordinates
  const { timezone, ...birthDataWithoutTimezone } = birthData;
  const response = await apiClient.post(
    `${getEndpoint('/calculate-chart')}?node_type=${nodeType}`, 
    birthDataWithoutTimezone
  );
  return response.data;
}
```

**Endpoint:** `POST /api/calculate-chart`

**Request Format:**
```json
{
  "name": "Test User",
  "date": "1990-01-01",
  "time": "12:00",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "place": "New Delhi, India"
}
```

**Note:** Timezone is explicitly REMOVED before sending

---

## Mobile (React Native)

**File:** `astroroshni_mobile/src/components/BirthForm/BirthFormScreen.js`

**API Calls:**
1. `chartAPI.calculateChart(birthData)` - Full chart
2. `chartAPI.calculateChartOnly(birthData)` - Chart only

**Implementation:** `astroroshni_mobile/src/services/api.js`
```javascript
calculateChart: (birthData) => {
  return api.post(getEndpoint('/calculate-chart'), birthData)
}
```

**Endpoint:** `POST /api/calculate-chart`

**Request Format:** Same as web (no timezone field)

---

## Backend

**File:** `backend/charts/routes.py`

**Endpoints:**

### 1. Calculate Chart Only (`/calculate-chart-only`)
```python
@router.post("/calculate-chart-only")
async def calculate_chart_only(request: dict, current_user: User = Depends(get_current_user))
```

**Purpose:** Calculate chart WITHOUT saving to database

**What it does:**
- ✅ Calculates chart (ascendant, planets, houses)
- ✅ Auto-detects timezone from coordinates
- ❌ Does NOT save birth details to database
- ❌ Does NOT return chart_id

**Use case:** Preview/temporary calculations

**Returns:** Chart data only (no database record)

---

### 2. Calculate Chart (`/calculate-chart`)
```python
@router.post("/calculate-chart")
async def calculate_chart_with_db_save(birth_data: BirthData, current_user: User = Depends(get_current_user))
```

**Purpose:** Calculate chart AND save birth details to database

**What it does:**
- ✅ Validates all input data (coordinates, date, time)
- ✅ Encrypts sensitive data (name, date, time, location)
- ✅ Saves birth details to `birth_charts` table
- ✅ Calculates chart (ascendant, planets, houses)
- ✅ Calculates divisional charts (D3, D9, D10)
- ✅ Returns chart_id for future reference

**Use case:** Permanent chart storage (user's saved charts)

**Returns:** Chart data + chart_id

---

## Key Differences

| Feature | calculate-chart-only | calculate-chart |
|---------|---------------------|----------------|
| **Calculates Chart** | ✅ Yes | ✅ Yes |
| **Saves to Database** | ❌ No | ✅ Yes |
| **Encrypts Data** | ❌ No | ✅ Yes |
| **Returns chart_id** | ❌ No | ✅ Yes |
| **Divisional Charts** | ❌ No | ✅ Yes (D3, D9, D10) |
| **Validation** | Basic | Strict |
| **Use Case** | Preview/Temp | Permanent Storage |

---

## Key Points for Testing

1. **No timezone in request** - Both web and mobile remove timezone before sending
2. **Backend calculates timezone** - From latitude/longitude using timezone_service.py
3. **Two endpoints** - One saves to DB, one doesn't
4. **Flexible request format** - Accepts data at root or in `birth_data` wrapper
5. **Authentication required** - Both endpoints need valid user token

---

## Test Scenarios

### Critical Tests:
1. ✅ Chart calculation without timezone field
2. ✅ Same coordinates produce same chart
3. ✅ Different coordinates produce different charts
4. ✅ Invalid data returns proper error
5. ✅ Chart data has all required fields (ascendant, planets, houses)

### Regression Tests:
1. ✅ Delhi coordinates → Correct ascendant
2. ✅ New York coordinates → Different ascendant than Delhi
3. ✅ Chart calculation is deterministic

### API Contract Tests:
1. ✅ Request without timezone succeeds
2. ✅ Response has expected structure
3. ✅ Authentication is enforced
