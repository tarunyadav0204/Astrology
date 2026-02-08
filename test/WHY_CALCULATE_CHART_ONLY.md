# Why These Files Call `calculateChartOnly` Instead of `calculateChart`

## Summary
All these files are calling `calculateChartOnly` because they are **loading existing saved charts from storage**, not creating new ones. They need chart calculations for display purposes only, not for permanent database storage.

## File Analysis

### 1. `HomeScreen.js` - Dashboard Display
**Why `calculateChartOnly`:**
- Loads birth data from **existing storage** (`storage.getBirthDetails()` or profiles)
- Displays dashboard with current chart essence (Sun, Moon, Ascendant signs)
- Shows current running dashas
- **Purpose:** Real-time display of chart information for dashboard

**Code Evidence:**
```javascript
// Gets EXISTING birth data from storage
let currentBirthData = await storage.getBirthDetails();
if (!currentBirthData) {
  const profiles = await storage.getBirthProfiles();
  currentBirthData = profiles.find(p => p.relation === 'self') || profiles[0];
}

// Only needs chart calculation for display, not storage
const response = await chartAPI.calculateChartOnly(formattedBirthData);
```

### 2. `ChatScreen.js` - Chat Interface Display
**Why `calculateChartOnly`:**
- Loads birth data from **existing storage** for chat context
- Displays "Big 3" signs (Sun, Moon, Ascendant) in chat header
- Shows current running dashas as chips
- **Purpose:** Contextual chart display during conversations

**Code Evidence:**
```javascript
const loadChartData = async (birth) => {
  // Loading existing birth data for chat display context
  const response = await chartAPI.calculateChartOnly(formattedData);
  setChartData(response.data);
};
```

### 3. `ChartScreen.js` - Chart Viewer (2 calls)
**Why `calculateChartOnly`:**

**Call #1 - Loading existing chart:**
```javascript
// Gets fresh data from storage - EXISTING saved chart
const data = await storage.getBirthDetails();
if (data && data.name) {
  setBirthData(data);
  // Calculate fresh chart for display from EXISTING birth data
  const response = await chartAPI.calculateChartOnly(formattedData);
}
```

**Call #2 - Fallback calculation:**
```javascript
// Fallback when preloader fails - still using EXISTING birth data
try {
  const response = await chartAPI.calculateChartOnly(formattedData);
  setChartData(response.data);
} catch (fallbackError) {
  console.error('ChartScreen - Fallback calculation failed:', fallbackError);
}
```

**Purpose:** Display various divisional charts (D1, D9, D10, etc.) from existing birth data

### 4. `ChartWidget.js` - Chart Component
**Why `calculateChartOnly`:**
- Renders individual chart widgets within other screens
- Loads divisional charts and transit charts for display
- Uses **existing birth data** passed as props
- **Purpose:** Chart visualization component, not chart creation

**Code Evidence:**
```javascript
// If not in cache, calculate it from EXISTING birth data
if (!d1ChartData) {
  const response = await chartAPI.calculateChartOnly(formattedData);
  d1ChartData = response.data;
  // Cache it for performance
  setChartDataCache(prev => ({ ...prev, lagna: d1ChartData }));
}
```

### 5. `ProfileScreen.js` - User Profile Display
**Why `calculateChartOnly`:**
- Loads user's **existing self birth chart** from API
- Displays profile with chart essence (Sun, Moon, Ascendant)
- Shows current running dashas in profile
- **Purpose:** Profile display with astrological information

**Code Evidence:**
```javascript
// Fetch user's EXISTING self birth chart from API
const response = await authAPI.getSelfBirthChart();
if (response.data.has_self_chart) {
  setBirthData(birthDataWithId);
  loadChartData(birthDataWithId); // Uses calculateChartOnly
}
```

## Key Distinction

### `calculateChart` (Saves to Database)
- **Used for:** Creating NEW birth charts
- **Files:** `BirthFormScreen.js`, `SelectNative.js`
- **Purpose:** Permanent storage of birth details
- **Returns:** Chart data + `chart_id`

### `calculateChartOnly` (Display Only)
- **Used for:** Loading EXISTING birth charts for display
- **Files:** All the files you mentioned
- **Purpose:** Temporary calculations for UI display
- **Returns:** Chart data only (no database storage)

## Why This Makes Sense

1. **Performance:** No unnecessary database writes for display purposes
2. **Data Integrity:** Existing charts remain unchanged
3. **Separation of Concerns:** Chart creation vs chart display are separate operations
4. **Caching:** Display calculations can be cached without affecting stored data
5. **User Experience:** Fast chart rendering without database overhead

## Conclusion

These files use `calculateChartOnly` because they are **consuming existing birth data** for display purposes, not creating new charts. The birth details already exist in storage/database, and these screens just need the calculated chart positions for visualization and dashboard display.

The pattern is:
- **Create once** with `calculateChart` (in BirthForm)
- **Display many times** with `calculateChartOnly` (in all other screens)