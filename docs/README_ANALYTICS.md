# Google Analytics 4 Setup Guide

## 1. Get Your Google Analytics Measurement ID

1. Go to [Google Analytics](https://analytics.google.com/)
2. Create a new property for your website
3. Copy your Measurement ID (format: G-XXXXXXXXXX)

## 2. Configure Environment Variables

Create a `.env` file in the frontend directory:

```bash
# Google Analytics Configuration
REACT_APP_GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Replace G-XXXXXXXXXX with your actual Measurement ID
```

## 3. Verify Setup

1. Start your development server: `npm start`
2. Open browser developer tools → Network tab
3. Look for requests to `googletagmanager.com`
4. Check Google Analytics Real-time reports

## 4. Events Being Tracked

### Automatic Events
- **Page Views**: All route changes
- **User Login/Logout**: Authentication events

### Astrology-Specific Events
- **Horoscope Views**: Zodiac sign and period selection
- **Chart Generation**: Birth chart creation
- **Muhurat Searches**: Auspicious time searches
- **Panchang Views**: Daily calendar views
- **Analysis Requests**: Marriage, career, health analysis

### Custom Events
- **Consultation Requests**: Astrologer consultation clicks
- **User Registration**: New user signups
- **Service Usage**: Premium service interactions

## 5. Analytics Dashboard

Monitor these key metrics in Google Analytics:
- **Popular Pages**: Most visited astrology services
- **User Flow**: How users navigate through services
- **Conversion Events**: Consultation requests, registrations
- **Demographics**: User location and device data
- **Real-time Activity**: Current active users

## 6. Privacy Compliance

- Analytics respects user privacy
- No personal data is collected without consent
- IP addresses are anonymized
- Users can opt-out via browser settings