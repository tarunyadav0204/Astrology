# Google Analytics Setup for Mobile App

## Partner UA (AppsFlyer + GA4)

Paid user-acquisition partners (for example Appvestor) should use **standard tools**, not a custom SDK:

1. **AppsFlyer** is the campaign source of truth (installs, `af_purchase`, registration, subscribe).
2. **Firebase Analytics / GA4** (`G-M0C9B8LGMR`) is the Google Ads / Play reporting stream.
3. **First-party** `app_installations` stores AppsFlyer conversion data so we can audit attributed revenue independently.

Set these in `astroroshni_mobile/.env` then **rebuild native** (`expo run:android` / `expo run:ios`):

```
EXPO_PUBLIC_APPSFLYER_DEV_KEY=
EXPO_PUBLIC_APPSFLYER_IOS_APP_ID=
EXPO_PUBLIC_APPSFLYER_ONELINK_HOST=
```

Give the partner **AppsFlyer Agency** access and **GA4 Viewer**. Do not give Firebase Owner, Play Console owner, or AstroRoshni admin.

All partner campaign URLs must use an AppsFlyer OneLink. Naming: `media_source=appvestor`, `campaign={campaign_id}`.

Do **not** enable AppsFlyer → Meta event forwarding while native Facebook `Purchase` events are on, or Ads Manager will double-count.

### Partner access (Appvestor)

Do this in the consoles before any spend. Code cannot invite them for you.

**Give**
- AppsFlyer: **Agency** (or Team member with only this app). They need installs, in-app events, revenue, and retention by campaign.
- Google Analytics 4 property `G-M0C9B8LGMR`: **Viewer**. Mark `sign_up`, `purchase`, and `subscribe` as key events.
- Optional: Google Play Console **view** financials if the insertion order requires it.

**Refuse unless a signed IO forces it**
- Appvestor Billing Stats SDK, ad units, or call-screen overlays
- Firebase **Owner**
- AstroRoshni admin panel or production database
- Play Console **owner** credentials

**Written confirmation to request**
> We will attribute Appvestor campaigns exclusively through AppsFlyer OneLinks (`pid`/`media_source=appvestor`) and GA4. We will not integrate the Appvestor Billing Stats SDK. Revenue share applies only to AppsFlyer Non-organic users from Appvestor media source.

**Campaign rules**
- Every Appvestor URL is a OneLink, never a raw Play Store link.
- Naming: `media_source=appvestor` (or `pid=appvestor`), `c={campaign_id}`, plus `af_adset` / `af_ad` when available.
- Optimize to **first purchase** (`af_purchase`), not cheap installs.
- Android-first unless iOS is agreed separately.
- Do not run the same geos/networks as Appvestor without a written split.

The privacy policy at `/policy` discloses AppsFlyer, GA4, and Meta.

---

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

Native events go through `astroroshni_mobile/src/utils/analytics.js`:

- Firebase Analytics when the native module is present after a rebuild
- GA4 Measurement Protocol fallback until that rebuild ships
- Meta App Events for Facebook/Instagram ads
- AppsFlyer `af_*` conversion events when a Dev Key is configured

### Firebase Analytics (native GA4)

Packages: `@react-native-firebase/app` and `@react-native-firebase/analytics` (v25, old architecture). Config files already exist:

- `google-services.json` → Android
- `GoogleService-Info.plist` → iOS

Enable Analytics in the Firebase console for project `astroroshni-7c7ba` if it is still off, then ship a native build.

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

1. Create the AppsFlyer app and OneLink; put the Dev Key in `.env`
2. Enable Firebase Analytics in the console for `astroroshni-7c7ba`
3. Rebuild native (`npm run android` / `npm run ios`)
4. Invite Appvestor as AppsFlyer Agency + GA4 Viewer
5. Confirm in writing they will use AppsFlyer/GA4 instead of their SDK
6. Test `af_purchase` and `sign_up` in AppsFlyer and GA4 DebugView

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
