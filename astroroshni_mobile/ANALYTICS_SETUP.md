# Google Analytics Setup for Mobile App

## Current Website Implementation

**Location:** `frontend/public/index.html` + `frontend/src/utils/analytics.js`

**Measurement ID:** G-M0C9B8LGMR

**Features:**
- Auto page view tracking on route changes
- Custom event tracking (chart_generated, horoscope_viewed, etc.)
- User engagement tracking (login, signup)

**Usage Example:**
```javascript
import { useAnalytics } from '../../hooks/useAnalytics';

const { trackEvent } = useAnalytics();
trackEvent('horoscope_period_changed', 'astrology', period);
```

---

## Mobile App Implementation

### Option 1: Firebase Analytics (Recommended)

**Step 1: Install Dependencies**
```bash
cd astroroshni_mobile
npx expo install expo-firebase-analytics
npx expo install expo-firebase-core
```

**Step 2: Configure Firebase**

Create `google-services.json` (Android) and `GoogleService-Info.plist` (iOS) from Firebase Console:
1. Go to https://console.firebase.google.com
2. Create/select project
3. Add Android app (package: com.astroroshni.mobile)
4. Add iOS app (bundle ID: com.astroroshni.mobile)
5. Download config files

Place files:
- `google-services.json` → `android/app/`
- `GoogleService-Info.plist` → `ios/AstroRoshni/`

**Step 3: Update app.json**
```json
{
  "expo": {
    "android": {
      "googleServicesFile": "./google-services.json"
    },
    "ios": {
      "googleServicesFile": "./GoogleService-Info.plist"
    },
    "plugins": [
      "@react-native-firebase/app",
      "@react-native-firebase/analytics"
    ]
  }
}
```

**Step 4: Usage in Components**
```javascript
import { useAnalytics } from '../hooks/useAnalytics';
import { trackAstrologyEvent } from '../utils/analytics';

// In component
const MyScreen = () => {
  const { trackEvent } = useAnalytics('HomeScreen');
  
  const handleChartGenerate = () => {
    trackAstrologyEvent.chartGenerated('lagna');
  };
  
  return <View>...</View>;
};
```

---

### Option 2: React Native Firebase (Alternative)

**Step 1: Install**
```bash
npm install @react-native-firebase/app @react-native-firebase/analytics
```

**Step 2: Update analytics.js**
```javascript
import analytics from '@react-native-firebase/analytics';

export const trackScreenView = async (screenName) => {
  await analytics().logScreenView({
    screen_name: screenName,
    screen_class: screenName,
  });
};

export const trackEvent = async (eventName, params = {}) => {
  await analytics().logEvent(eventName, params);
};
```

---

### Option 3: Expo Analytics (Simplest for Expo)

**Already Created Files:**
- ✅ `src/utils/analytics.js` - Analytics utility functions
- ✅ `src/hooks/useAnalytics.js` - React hook for screen tracking

**Step 1: Install**
```bash
npx expo install expo-firebase-analytics expo-firebase-core
```

**Step 2: Add to package.json**
```json
{
  "dependencies": {
    "expo-firebase-analytics": "~8.0.0",
    "expo-firebase-core": "~7.0.0"
  }
}
```

**Step 3: Configure app.json**
```json
{
  "expo": {
    "android": {
      "googleServicesFile": "./google-services.json",
      "package": "com.astroroshni.mobile"
    },
    "ios": {
      "googleServicesFile": "./GoogleService-Info.plist",
      "bundleIdentifier": "com.astroroshni.mobile"
    }
  }
}
```

---

## Usage Examples

### Track Screen Views
```javascript
import { useAnalytics } from '../hooks/useAnalytics';

const ChartScreen = () => {
  useAnalytics('ChartScreen'); // Auto-tracks on mount
  return <View>...</View>;
};
```

### Track Custom Events
```javascript
import { trackAstrologyEvent } from '../utils/analytics';

// Chart generated
trackAstrologyEvent.chartGenerated('navamsa');

// Horoscope viewed
trackAstrologyEvent.horoscopeViewed('aries', 'daily');

// Chat message sent
trackAstrologyEvent.chatMessageSent('career_question');

// Credit purchased
trackAstrologyEvent.creditPurchased(100);
```

### Track User Properties
```javascript
import { setUserId, setUserProperties } from '../utils/analytics';

// After login
await setUserId(user.id);
await setUserProperties({
  zodiac_sign: 'aries',
  subscription_tier: 'premium',
  language: 'en'
});
```

---

## Events Already Defined

### Astrology Events
- `chart_generated` - Chart type (lagna, navamsa, etc.)
- `horoscope_viewed` - Zodiac sign + period
- `dasha_viewed` - Dasha type
- `transit_viewed` - Date
- `analysis_requested` - Analysis type
- `panchang_viewed` - Date

### User Events
- `sign_up` - User registration
- `login` - User login
- `credit_purchased` - Amount + currency

### Engagement Events
- `chat_message_sent` - Message type
- `pdf_generated` - Report type

---

## Next Steps

1. **Choose Option 3 (Expo Analytics)** - Best for your Expo setup
2. **Get Firebase config files** from Firebase Console
3. **Install dependencies**: `npx expo install expo-firebase-analytics expo-firebase-core`
4. **Add config files** to project
5. **Update app.json** with googleServicesFile paths
6. **Rebuild app**: `npm run android` or `npm run ios`
7. **Test events** in Firebase Console (DebugView)

---

## Testing

Enable debug mode:
```bash
# Android
adb shell setprop debug.firebase.analytics.app com.astroroshni.mobile

# iOS (in Xcode scheme)
-FIRAnalyticsDebugEnabled
```

View events in Firebase Console → Analytics → DebugView

---

## Comparison: Website vs Mobile

| Feature | Website | Mobile |
|---------|---------|--------|
| Library | gtag.js | Firebase Analytics |
| Setup | Script tag in HTML | Native config files |
| Tracking | window.gtag() | expo-firebase-analytics |
| Events | Same event names | Same event names |
| Dashboard | Google Analytics 4 | Firebase Console |
| Auto-tracking | Page views | Screen views |
