# Financial Markets Astrology - Mobile UI

## 📱 Components Created

1. **FinancialDashboard.js** - Main dashboard with sector cards and hot opportunities
2. **SectorDetailScreen.js** - Detailed view of individual sector with timeline
3. **AllOpportunitiesScreen.js** - List of all high-intensity opportunities with filters

## 🚀 Integration Steps

### 1. Add Routes to Navigation

In your navigation file (e.g., `src/navigation/AppNavigator.js`), add:

```javascript
import { 
  FinancialDashboard, 
  SectorDetailScreen, 
  AllOpportunitiesScreen 
} from '../components/Financial';

// Inside your Stack.Navigator:
<Stack.Screen 
  name="FinancialDashboard" 
  component={FinancialDashboard}
  options={{ headerShown: false }}
/>
<Stack.Screen 
  name="SectorDetail" 
  component={SectorDetailScreen}
  options={{ headerShown: false }}
/>
<Stack.Screen 
  name="AllOpportunities" 
  component={AllOpportunitiesScreen}
  options={{ headerShown: false }}
/>
```

### 2. Add Menu Item

In your main menu/home screen, add a button to navigate:

```javascript
<TouchableOpacity 
  onPress={() => navigation.navigate('FinancialDashboard')}
  style={styles.menuItem}
>
  <Ionicons name="trending-up" size={24} color="#10b981" />
  <Text style={styles.menuText}>Market Astrology</Text>
</TouchableOpacity>
```

### 3. Ensure API_BASE_URL is Set

In `src/utils/constants.js`, make sure you have:

```javascript
export const API_BASE_URL = 'https://your-backend-url.com';
// or for local development:
// export const API_BASE_URL = 'http://localhost:8001';
```

## 📊 Features

### FinancialDashboard
- Shows current trends for all 8 sectors
- Displays top 5 hot opportunities
- Color-coded sector cards (Green=Bullish, Red=Bearish, Yellow=Neutral)
- Tap any sector to view details

### SectorDetailScreen
- Complete 5-year forecast timeline
- Visual timeline bar showing all periods
- Detailed period cards with:
  - Start/End dates
  - Trend (Bullish/Bearish/Neutral)
  - Intensity (High/Medium/Low)
  - Astrological reason
  - Duration in days

### AllOpportunitiesScreen
- Filter by intensity (High/Medium/Low)
- Shows all bullish periods across sectors
- Sortable and searchable
- Quick navigation to sector details

## 🎨 Design Features

- Dark gradient background (#0f0c29 → #302b63)
- Color-coded trends:
  - 🟢 Bullish: Green (#10b981)
  - 🔴 Bearish: Red (#ef4444)
  - 🟡 Neutral: Yellow (#f59e0b)
- Smooth animations and transitions
- Responsive cards and layouts
- Icon-based navigation

## 🔐 Authentication

All API calls require authentication token from AsyncStorage:
```javascript
const token = await AsyncStorage.getItem('authToken');
```

Make sure users are logged in before accessing these screens.

## 📱 Screen Flow

```
Home/Menu
    ↓
FinancialDashboard
    ↓
    ├─→ SectorDetailScreen (tap sector card)
    └─→ AllOpportunitiesScreen (tap "View All")
```

## 🎯 API Endpoints Used

1. `GET /api/financial/current-trends` - Current status of all sectors
2. `GET /api/financial/hot-opportunities?intensity=High` - Hot opportunities
3. `GET /api/financial/forecast/all` - Complete forecast data
4. `GET /api/financial/forecast/{sector}` - Specific sector details

## 🐛 Troubleshooting

**Issue: "Market forecast data not available"**
- Solution: Admin needs to run `POST /api/financial/admin/regenerate` first

**Issue: 401 Unauthorized**
- Solution: Check if authToken is valid in AsyncStorage

**Issue: Sectors not loading**
- Solution: Verify API_BASE_URL is correct and backend is running

## 📝 Notes

- Data is pre-generated and cached in database
- No real-time calculations on mobile
- Fast loading (<50ms after initial fetch)
- Works offline after first load (cached in state)

## 🎨 Customization

To change colors, edit the gradient arrays in each component:
```javascript
colors={['#0f0c29', '#302b63', '#24243e']} // Background
colors={['#10b981', '#34d399']} // Bullish
colors={['#ef4444', '#f87171']} // Bearish
```

To change sector icons, edit `SECTOR_ICONS` object in `FinancialDashboard.js`.
